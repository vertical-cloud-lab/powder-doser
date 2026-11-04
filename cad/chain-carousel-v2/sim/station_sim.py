"""Docking and tilt at the v2 station (MuJoCo), with the dock electromagnet and the gear-mesh reaction.

    python sim/station_sim.py cycle               # approach, magnet on, tilt to the dose angle, dose (mesh torque + taps),
                                                  #   stall pulse, tilt back into the snap hooks, magnet off, retract
    python sim/station_sim.py cycle --no-magnet   # the same with gravity alone holding the module on the carriage
    python sim/station_sim.py threshold           # at 0-90 deg: ramp the gear's separating force until the dock opens
    python sim/station_sim.py all                 # both, with and without the magnet; plots and results.json

What is modelled (SI units inside; geometry from params.py / layout.py, frame coordinates):

* The station's chain carriage on its two A-1 tabs. The chains are vertical springs at the tabs,
  k = T (1/a + 1/b) per chain for a carriage a and b from the bottom run's two sprockets (80 N
  pretension: 2.8 N/mm per tab), with the hold-down lips 2 mm above the tongues and the feet 4 mm below.
* The module (Sam's plate, the steel armature tab, the auger, cap and powder) on its hinge on the carriage.
  The snap hooks are a detent: they hold the plate down with up to HOOK_N until it has lifted past their
  0.8 mm overlap, and take PUSH_N to press back in.
* Sam's electronics carriage on the P16's rod end (pinned), the P16 pinned to the station rail: a position
  servo on the rod limited to 50 N (the P16-150-22's rating). The yoke's tongue rides the approach fork until
  the carriage docks. The carriage's rim is a contact against the plate's underside: it sets the centre distance.
* The dock electromagnet (Adafruit 3872 P20/15) as a gap-dependent pull between its face and the armature tab:
  F = F0 / (1 + g / g0)^2, F0 = 20 N, g0 = 0.4 mm (10.6 N at the design gap of 0.15 mm, 1.6 N at 1 mm).
* The gear mesh as a force pair: on the module at the 44T gear's pitch point, on the carriage at the pinion's,
  a separating part along the line of centres and a tangential part (Ft = T_pinion / 10 mm).
  Nominal dosing: 0.03 N*m at the auger. Stall pulse: the NEMA 11's 0.10 N*m holding torque with the steel pinion
  on the printed gear, dry PTFE lube (separating ratio 0.55, against tan 20 deg = 0.36 frictionless and 0.75 for
  PETG on PETG).
* Solenoid taps: 4 N for 10 ms between the carriage and the module near the outlet.

Once docked, the carriage and the module are welded and the weld's wrench is read back as the force the dock
interface has to carry. The dock holds while that contact force is compressive and its centre of pressure stays
inside the support: the rim (Sam x 25-73.3) and the magnet face (x 89.5-109.5) under the steel tab. The face sits
0.15 mm under the tab, so a 0.3 deg tip closes the gap and the face becomes the second support whether the coil is
on or off. Contact-only docking (no weld) tipped the carriage about the rim's
back edge in MuJoCo and was not used for the loads.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

import mujoco
import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import layout as L  # noqa: E402
from params import *  # noqa: E402,F401,F403

OUT = HERE / "results" / "station"
MM = 1e-3
G = 9.81
DT = 2e-4

# masses (kg) and centres (Sam's frame, mm)
M_CAR = 0.098                     # chain carriage, PETG (80 cm^3 at about 80 % fill) + screws, nuts, magnets
M_MOD_DRY = 0.0345 + 0.0092 + 0.0035 + 0.0662 + 0.0054    # plate, steel tab, pins/e-clips/screws, auger, cap
COM_MOD_DRY = np.array([(0.0345 * 52.4 + 0.0092 * 100.0 + 0.0035 * 40.0 + 0.0662 * 103.4 + 0.0054 * 241.4) / M_MOD_DRY, 0.0,
                        (0.0345 * -11.3 + 0.0092 * -19.0) / M_MOD_DRY])
M_ECAR = 0.285                    # Sam's carriage 17.7 g + NEMA 11 180 g + solenoid 30 g + magnet and bracket 27 g + wiring 10 g
COM_ECAR = np.array([52.0, 0.0, -33.6])   # + steel pinion 20 g at (83.7, -32.1); main session's estimate
HOOK_N, PUSH_N = 8.0, 6.0         # snap hooks: release and press-in force, both hooks together
HOOK_ARM = (SNAP_X - HINGE_X) * MM
HOOK_DEG = math.degrees(math.atan2(SNAP_LAP, SNAP_X - HINGE_X))
F0_MAG, G0_MAG = 20.0, 0.4        # N, mm
K_TAB = CHAIN_TENSION_N * (1 / ((L.STATION_Y + LOOP_Y) * MM) + 1 / ((LOOP_Y - L.STATION_Y) * MM))   # N/m per chain
T_NOMINAL_AUGER = 0.03            # N*m at the auger while dosing
T_HOLD_PINION = 0.10              # N*m, NEMA 11 11HS18-0674S holding torque
SEP_FRICTION = SEP_RATIO_STEEL    # separating / tangential force: steel pinion, dry PTFE lube (0.55); PETG on PETG 0.75; frictionless 0.364
GEAR_PT = np.array([GEAR_X + 5.0, 0.0, -22.0])     # 44T pitch point under the auger axis (Sam's frame)


YOKE = [YOKE_X, YOKE_Z]           # rod-end pin under the electronics carriage, Sam's frame (override for variants)
TONGUE = [TONGUE_X, TONGUE_Y, L.TONGUE_Z0]          # guide tongue under the U-yoke: x, y and bottom z (Sam's frame, docked)
FORK = [L.HINGE_STATION[0] + TONGUE_X, L.STATION_Y + TONGUE_Y, L.FORK_Z, L.FORK_TOP]


def _f(*v):
    return " ".join(f"{x:.6f}" for x in v)


FORK_L = [UFORK_L]                # rod end -> carriage pin along the actuator axis (U-yoke), mm


def act_pins(tilt_frame: float, ext_mm: float):
    """(base pin, carriage pin) in frame mm for the current YOKE (as layout.actuator_pins); the actuator's rod end is
    FORK_L short of the carriage pin on the same axis."""
    def pin(tf, ex):
        E = L.electronics_frame(tf, ex)
        return L.to_world(E, (YOKE[0], 0.0, YOKE[1]))
    pd = pin(0.0, DOCK_EXT)
    B = pd - np.array([0.0, 0.0, ACT_RETRACTED + DOCK_EXT + FORK_L[0]])
    return B, pin(tilt_frame, ext_mm)


def build(powder_g: float = 50.0):
    """MJCF of the station (frame coordinates in metres)."""
    S = L.station_frame()
    H = L.HINGE_STATION * MM
    car_o = S[:3, 3] * MM                                   # carriage frame origin (front chain's pitch line)
    zc = (Z_RUN + CAR_W0 - CAR_T / 2) * MM                  # carriage plate's mid-plane
    m_mod = M_MOD_DRY + powder_g / 1000
    com_mod = (COM_MOD_DRY * M_MOD_DRY + np.array([125.0, 0.0, -4.0]) * powder_g / 1000) / m_mod
    B, P0 = act_pins(0.0, 0.0)                              # retracted
    B, P0 = B * MM, P0 * MM
    axis = (P0 - B) / np.linalg.norm(P0 - B)
    E0 = L.electronics_frame(0.0, 0.0)                      # Sam's frame of the electronics carriage, retracted
    e_org = E0[:3, 3] * MM
    pin_rel = np.array([YOKE[0], 0, YOKE[1]]) * MM          # rod-end pin in the electronics carriage's frame
    fork_c = np.array([FORK[0], FORK[1], (FORK[2] + FORK[3]) / 2]) * MM
    fh = FORK_H * MM / 2
    lip_z = (Z_RUN + CAR_W0 + HOLD_DOWN_GAP) * MM           # lip underside
    foot_z = (Z_RUN + CAR_W0 - CAR_T - HOLD_DOWN_FOOT_GAP) * MM   # foot top
    sy = L.STATION_Y * MM
    # locating pins on the carriage rim (capsules: rounded tips centre them) and the plate's hole and slot as walls
    sk, lp = [], []
    r_h, w = LOCPIN_HOLE / 2, 1.0
    for j, (px, py) in enumerate(LOCPIN_XY):
        lp.append(f'          <geom name="locpin{j}" type="capsule" fromto="{_f(*((np.array([px, py, -18.9 - 1.0]) * MM) - pin_rel), *((np.array([px, py, -18.9 + LOCPIN_PROUD - LOCPIN_D / 2]) * MM) - pin_rel))}" size="{LOCPIN_D / 2 * MM}" contype="8" conaffinity="8" rgba="0.7 0.7 0.7 1"/>')
        half_x = r_h if j == 0 else LOCPIN_SLOT / 2
        for sgn in (-1, 1):                                       # walls across y (both features)
            sk.append(f'        <geom name="sock{j}y{sgn}" type="box" pos="{_f(px * MM, (py + sgn * (r_h + w / 2)) * MM, -16.0 * MM)}" size="{_f((half_x + w) * MM, w / 2 * MM, 2.0 * MM)}" contype="8" conaffinity="8" rgba="0.3 0.3 0.8 0.5"/>')
            sk.append(f'        <geom name="sock{j}x{sgn}" type="box" pos="{_f((px + sgn * (half_x + w / 2)) * MM, py * MM, -16.0 * MM)}" size="{_f(w / 2 * MM, (r_h + w) * MM, 2.0 * MM)}" contype="8" conaffinity="8" rgba="0.3 0.3 0.8 0.5"/>')
    sockets, locpins = "\n".join(sk), "\n".join(lp)
    xml = f"""<mujoco model="v2 station">
  <compiler angle="degree"/>
  <option timestep="{DT}" integrator="implicitfast" gravity="0 0 -{G}" cone="elliptic" impratio="5">
    <flag filterparent="disable"/>
  </option>
  <default>
    <geom contype="1" conaffinity="1" condim="3" friction="0.3 0.005 0.0001" solref="0.001 1" solimp="0.95 0.99 0.0002"/>
  </default>
  <worldbody>
    <geom name="lip_f" type="box" pos="{_f(-15.5 * MM, sy, lip_z + 0.0045)}" size="{_f(0.0085, 0.020, 0.0045)}" rgba="0.95 0.55 0.1 1"/>
    <geom name="lip_b" type="box" pos="{_f((CHAIN_L + 15.5) * MM, sy, lip_z + 0.0045)}" size="{_f(0.0085, 0.020, 0.0045)}" rgba="0.95 0.55 0.1 1"/>
    <geom name="foot_f" type="box" pos="{_f(-15.5 * MM, sy, foot_z - 0.005)}" size="{_f(0.0085, 0.020, 0.005)}" rgba="0.95 0.55 0.1 1"/>
    <geom name="foot_b" type="box" pos="{_f((CHAIN_L + 15.5) * MM, sy, foot_z - 0.005)}" size="{_f(0.0085, 0.020, 0.005)}" rgba="0.95 0.55 0.1 1"/>
    <geom name="fork_yl" type="box" pos="{_f(fork_c[0], fork_c[1] - (3.3 + 2.0) * MM, fork_c[2])}" size="{_f(0.025, 0.002, fh)}" rgba="0.9 0.5 0.1 1"/>
    <geom name="fork_yr" type="box" pos="{_f(fork_c[0], fork_c[1] + (3.3 + 2.0) * MM, fork_c[2])}" size="{_f(0.025, 0.002, fh)}" rgba="0.9 0.5 0.1 1"/>
    <geom name="fork_xa" type="box" pos="{_f(fork_c[0] - (15.5 + 2.0) * MM, fork_c[1], fork_c[2])}" size="{_f(0.002, 0.0033, fh)}" rgba="0.9 0.5 0.1 1"/>
    <geom name="fork_xb" type="box" pos="{_f(fork_c[0] + (15.5 + 2.0) * MM, fork_c[1], fork_c[2])}" size="{_f(0.002, 0.0033, fh)}" rgba="0.9 0.5 0.1 1"/>
    <body name="car" pos="{_f(CHAIN_L / 2 * MM, sy, zc)}">
      <joint name="car_z" type="slide" axis="0 0 1" damping="2"/>
      <joint name="car_p" type="hinge" axis="0 1 0" damping="0.05"/>
      <inertial pos="0 0 0" mass="{M_CAR}" diaginertia="0.00003 0.0009 0.00088"/>
      <geom name="car_plate_a" type="box" pos="{_f((-8 - CHAIN_L / 2 + (WIN_X[0] + 8) / 2) * MM, 0, 0)}" size="{_f((WIN_X[0] + 8) / 2 * MM, CAR_W / 2 * MM, CAR_T / 2 * MM)}" contype="2" conaffinity="2"/>
      <geom name="tongue_f" type="box" pos="{_f((CAR_X0 + 7.5 - CHAIN_L / 2) * MM, 0, 0)}" size="{_f(0.0075, 0.020, CAR_T / 2 * MM)}" contype="1" conaffinity="1"/>
      <geom name="tongue_b" type="box" pos="{_f((CAR_X1 - 7.5 - CHAIN_L / 2) * MM, 0, 0)}" size="{_f(0.0075, 0.020, CAR_T / 2 * MM)}" contype="1" conaffinity="1"/>
      <body name="mod" pos="{_f(*(H - np.array([CHAIN_L / 2 * MM, sy, zc])))}">
        <joint name="tilt" type="hinge" axis="0 -1 0" range="0 100" limited="true" damping="0.002" solreflimit="0.002 1"/>
        <inertial pos="{_f(*(com_mod * MM))}" mass="{m_mod}" diaginertia="{_f(0.5 * m_mod * 0.0125 ** 2 + 2e-5, m_mod * 0.25 ** 2 / 12 + 4e-5, m_mod * 0.25 ** 2 / 12 + 4e-5)}"/>
        <geom name="plate_under" type="box" pos="{_f(61.9 * MM, 0, -15.5 * MM)}" size="{_f(36.9 * MM, 25.0 * MM, 2.5 * MM)}" contype="4" conaffinity="4" rgba="0.1 0.25 0.85 1"/>
{sockets}
        <site name="armature" pos="{_f(100.0 * MM, 0, -20.0 * MM)}"/>
        <geom name="armature_g" type="box" pos="{_f(100.0 * MM, 0, -19.0 * MM)}" size="{_f(11.0 * MM, 14.0 * MM, 1.0 * MM)}" contype="4" conaffinity="4" rgba="0.6 0.6 0.6 1"/>
        <site name="gear" pos="{_f(*(GEAR_PT * MM))}"/>
        <site name="tap_mod" pos="{_f(12.0 * MM, 0, -12.5 * MM)}"/>
      </body>
    </body>
    <body name="act" pos="{_f(*B)}">
      <joint name="act_pin" type="hinge" axis="0 1 0" damping="0.0005"/>
      <inertial pos="{_f(*(axis * 0.06))}" mass="0.10" diaginertia="0.0003 0.0003 0.00001"/>
      <body name="rod" pos="0 0 0">
        <joint name="act_slide" type="slide" axis="{_f(*axis)}" range="0 {ACT_STROKE * MM}" limited="true" damping="30"/>
        <inertial pos="{_f(*(axis * 0.15))}" mass="0.02" diaginertia="1e-5 1e-5 1e-7"/>
        <geom name="tongue" type="box" pos="{_f(*(P0 - B + (np.array([TONGUE[0] - YOKE[0], TONGUE[1], TONGUE[2] - YOKE[1] + 12.5]) * MM)))}" size="{_f(15.0 * MM, 3.0 * MM, 12.5 * MM)}" contype="1" conaffinity="1" rgba="0.95 0.55 0.1 1"/>
        <geom name="ystop" type="box" pos="{_f(*(P0 - B + (np.array([14.0, 0, YOKE_STOP_Z + 2.0]) * MM)))}" size="{_f(3.0 * MM, 19.5 * MM, 2.0 * MM)}" contype="16" conaffinity="16" rgba="0.95 0.55 0.1 1"/>
        <body name="ecar" pos="{_f(*(P0 - B))}">
          <joint name="ecar_pin" type="hinge" axis="0 1 0" damping="0.0002"/>
          <inertial pos="{_f(*((COM_ECAR * MM) - pin_rel))}" mass="{M_ECAR}" diaginertia="0.00008 0.00015 0.00012"/>
          <geom name="rim" type="box" pos="{_f(*((np.array([40.55, 0, -19.9]) * MM) - pin_rel))}" size="{_f(32.75 * MM, 18.0 * MM, 1.0 * MM)}" contype="4" conaffinity="4" rgba="0.2 0.45 0.95 1"/>
          <geom name="tail" type="box" pos="{_f(14.0 * MM, 0, -9.5 * MM)}" size="{_f(3.0 * MM, 19.5 * MM, 1.5 * MM)}" contype="16" conaffinity="16" rgba="0.95 0.55 0.1 1"/>
{locpins}
          <site name="magnet" pos="{_f(*((np.array([DOCK_MAG_XY[0], 0, DOCK_MAG_FACE_Z]) * MM) - pin_rel))}"/>
          <geom name="magnet_g" type="box" pos="{_f(*((np.array([DOCK_MAG_XY[0], 0, DOCK_MAG_FACE_Z - 1.0]) * MM) - pin_rel))}" size="{_f(9.0 * MM, 9.0 * MM, 1.0 * MM)}" contype="4" conaffinity="4" rgba="0.75 0.15 0.12 1"/>
          <site name="pinion" pos="{_f(*((np.array([GEAR_X + 5.0, 0, NEMA11_Z + 10.0]) * MM) - pin_rel))}"/>
          <site name="tap_car" pos="{_f(*((np.array([SOL_X, 0, SOL_Z]) * MM) - pin_rel))}"/>
        </body>
      </body>
    </body>
  </worldbody>
  <actuator>
    <general name="act_drive" joint="act_slide" gainprm="1" biastype="affine" biasprm="0 -30000 -300" forcelimited="true" forcerange="-50 50"/>
  </actuator>
  <equality>
    <weld name="dock" body1="mod" body2="ecar" active="false" solref="0.002 1" torquescale="1"/>
  </equality>
</mujoco>"""
    info = dict(B=B, axis=axis, e_org=e_org, m_mod=m_mod, com_mod=com_mod, k_tab=K_TAB,
                tab_x=np.array([A1_HOLE_C, CHAIN_L - A1_HOLE_C]) * MM, car_c=np.array([CHAIN_L / 2 * MM, sy, zc]))
    return xml, info


def ext_for_tilt(tilt_frame: float) -> float:
    """Actuator extension (m, from fully retracted) that puts the module at this hinge angle."""
    B, Pp = act_pins(tilt_frame, DOCK_EXT)
    return (np.linalg.norm(Pp - B) - ACT_RETRACTED - FORK_L[0]) * MM


class Station:
    def __init__(self, magnet=True, powder_g=50.0, hook_n=HOOK_N):
        xml, self.info = build(powder_g)
        self.m = mujoco.MjModel.from_xml_string(xml)
        self.d = mujoco.MjData(self.m)
        self.magnet = magnet
        self.mag_on = False
        self.hook_n = hook_n
        self.latched = True
        self.welded = False
        m = self.m
        self.b_car, self.b_mod, self.b_ecar = m.body("car").id, m.body("mod").id, m.body("ecar").id
        self.j_tilt = m.joint("tilt").qposadr[0]
        self.d_tilt = m.joint("tilt").dofadr[0]
        self.j_slide = m.joint("act_slide").qposadr[0]
        self.d_slide = m.joint("act_slide").dofadr[0]
        self.j_carz, self.j_carp = m.joint("car_z").qposadr[0], m.joint("car_p").qposadr[0]
        self.d_carz, self.d_carp = m.joint("car_z").dofadr[0], m.joint("car_p").dofadr[0]
        self.s = {n: m.site(n).id for n in ("armature", "gear", "tap_mod", "magnet", "pinion", "tap_car")}
        self.g = {n: m.geom(n).id for n in ("lip_f", "lip_b", "foot_f", "foot_b", "rim", "plate_under", "armature_g", "magnet_g")}
        self.F_sep, self.F_tan, self.F_tap = 0.0, 0.0, 0.0
        mujoco.mj_forward(m, self.d)
        # static chain preload: the springs carry the carriage + module weight at the nominal height
        W = (M_CAR + self.info["m_mod"]) * G
        self.tab_pre = np.array([W / 2, W / 2])

    # ---- helpers
    def tilt_deg(self):
        return math.degrees(self.d.qpos[self.j_tilt])

    def tab_dz(self):
        """Vertical displacement of the two tab points from nominal (m)."""
        z, p = self.d.qpos[self.j_carz], self.d.qpos[self.j_carp]
        xr = self.info["tab_x"] - self.info["car_c"][0]
        return z - xr * math.sin(p)          # hinge about +y: +p lowers +x

    def mag_gap(self):
        a, mg = self.d.site_xpos[self.s["armature"]], self.d.site_xpos[self.s["magnet"]]
        n = self.d.xmat[self.b_ecar].reshape(3, 3)[:, 2]
        return float((a - mg) @ n), n

    def rim_gap(self):
        """Gap between the carriage's rim and the plate's underside at the rim's front and back ends (mm)."""
        R_e = self.d.xmat[self.b_ecar].reshape(3, 3)
        R_m = self.d.xmat[self.b_mod].reshape(3, 3)
        n_m = -R_m[:, 2]                                        # plate underside normal (down, module frame)
        p_m = self.d.xpos[self.b_mod] + R_m @ np.array([0, 0, -18.0 * MM])
        out = []
        for x in (25.0, 73.3):
            p = self.d.xpos[self.b_ecar] + R_e @ ((np.array([x, 0, -18.9]) * MM) - np.array([YOKE[0], 0, YOKE[1]]) * MM)
            out.append(float((p_m - p) @ n_m * -1) / MM)        # positive: rim below the plate (open)
        return out

    def apply_forces(self):
        d = self.d
        d.xfrc_applied[:] = 0.0
        # chain springs at the tabs
        dz = self.tab_dz()
        dzd = d.qvel[self.d_carz] - (self.info["tab_x"] - self.info["car_c"][0]) * d.qvel[self.d_carp]
        f_tab = self.tab_pre - K_TAB * dz - 3.0 * dzd
        self.f_tab = f_tab
        xr = self.info["tab_x"] - self.info["car_c"][0]
        d.qfrc_applied[:] = 0.0
        d.qfrc_applied[self.d_carz] = f_tab.sum()
        d.qfrc_applied[self.d_carp] = -(f_tab * xr).sum()
        # snap hooks: hold the plate's free end down until it has lifted past the overlap, then push-in force
        th = self.tilt_deg()
        tau = 0.0
        if self.latched:
            if th > HOOK_DEG:
                self.latched = False
            else:
                tau = -self.hook_n * HOOK_ARM * min(1.0, th / (0.25 * HOOK_DEG) if HOOK_DEG > 0 else 1.0) if th > 0 else 0.0
        else:
            if th < HOOK_DEG + 0.5:
                tau = PUSH_N * HOOK_ARM
            if th < 0.3:                                    # past the hooks' lip: snapped in
                self.latched = True
        d.qfrc_applied[self.d_tilt] += tau
        self.tau_hook = tau
        # magnet
        g, n = self.mag_gap()
        Fm = 0.0
        if self.magnet and self.mag_on:
            gm = max(g / MM, 0.0)
            Fm = F0_MAG / (1 + gm / G0_MAG) ** 2
            self._force(self.b_mod, self.s["armature"], -Fm * n)
            self._force(self.b_ecar, self.s["magnet"], Fm * n)
        self.F_mag, self.g_mag = Fm, g / MM
        # gear mesh: separating along the carriage's z (line of centres), tangential along y
        if self.F_sep or self.F_tan:
            f = self.F_sep * n + self.F_tan * np.array([0, 1.0, 0])
            self._force(self.b_mod, self.s["gear"], f)
            self._force(self.b_ecar, self.s["pinion"], -f)
        if self.F_tap:
            self._force(self.b_mod, self.s["tap_mod"], self.F_tap * n)
            self._force(self.b_ecar, self.s["tap_car"], -self.F_tap * n)

    def _force(self, body, site, f):
        p = self.d.site_xpos[site]
        c = self.d.xipos[body]
        self.d.xfrc_applied[body, :3] += f
        self.d.xfrc_applied[body, 3:] += np.cross(p - c, f)

    def contact_force(self, gname):
        tot = 0.0
        gid = self.g[gname]
        f6 = np.zeros(6)
        for i in range(self.d.ncon):
            c = self.d.contact[i]
            if c.geom1 == gid or c.geom2 == gid:
                mujoco.mj_contactForce(self.m, self.d, i, f6)
                tot += abs(f6[0])
        return tot

    def hinge_reaction(self):
        mujoco.mj_rnePostConstraint(self.m, self.d)
        f = self.d.cfrc_int[self.b_mod][3:]
        return f

    def weld(self, on: bool):
        """Weld the electronics carriage to the module where they are now (docked) and stop their contacts."""
        m, d = self.m, self.d
        eq = m.equality("dock").id
        if on:
            Rm, pm = d.xmat[self.b_mod].reshape(3, 3), d.xpos[self.b_mod]
            Re, pe = d.xmat[self.b_ecar].reshape(3, 3), d.xpos[self.b_ecar]
            rel_p = Rm.T @ (pe - pm)
            q = np.zeros(4)
            mujoco.mju_mat2Quat(q, (Rm.T @ Re).ravel())
            m.eq_data[eq, 0:3] = 0.0                  # anchor at the carriage's origin (the rod-end pin)
            m.eq_data[eq, 3:6] = rel_p
            m.eq_data[eq, 6:10] = q
            m.eq_data[eq, 10] = 1.0
        d.eq_active[eq] = 1 if on else 0
        for g in ("rim", "plate_under", "armature_g", "magnet_g"):
            m.geom_contype[self.g[g]] = 0 if on else 4
            m.geom_conaffinity[self.g[g]] = 0 if on else 4
        for g in ("tail", "ystop"):
            m.geom_contype[m.geom(g).id] = 0 if on else 16
            m.geom_conaffinity[m.geom(g).id] = 0 if on else 16
        self.welded = on

    def dock_wrench(self):
        """Contact force/moment the module puts on the carriage through the dock (carriage frame, N and N*mm about
        the rod-end pin), and whether a compressive contact inside the support can carry it."""
        d = self.d
        eq = self.m.equality("dock").id
        rows = [i for i in range(d.nefc) if d.efc_type[i] == mujoco.mjtConstraint.mjCNSTR_EQUALITY and d.efc_id[i] == eq]
        if len(rows) < 6:
            return None
        f = -d.efc_force[rows[0:3]]
        tq = -0.5 * d.efc_force[rows[3:6]]
        Re = d.xmat[self.b_ecar].reshape(3, 3)
        F, M = Re.T @ f, Re.T @ tq * 1e3                  # carriage frame; torque in N*mm
        N = -F[2]                                         # compression (module pushing the carriage away)
        x_cp = M[1] / N + YOKE[0] if N > 1e-6 else float("nan")  # Sam x of the centre of pressure
        lo, hi = 25.0, DOCK_MAG_XY[0] + DOCK_MAG_D / 2      # rim front ... magnet face's back edge (a contact surface, coil on or off)
        margin = min(x_cp - lo, hi - x_cp) if N > 0 else -1.0
        slide = abs(F[0]) / (0.3 * N) if N > 1e-6 else float("inf")
        return dict(N=float(N), x_cp=float(x_cp), cp_margin=float(margin), Ft=float(F[0]), slide_ratio=float(slide),
                    holds=bool(N > 0 and margin > 0))

    def step(self, ext_cmd):
        self.d.ctrl[0] = 30000 * ext_cmd       # affine bias: force = 3e4 * (cmd - q) - 300 qdot
        self.apply_forces()
        mujoco.mj_step(self.m, self.d)


def settle(st: Station, ext, t=0.3):
    for _ in range(int(t / DT)):
        st.step(ext)


def cycle(magnet=True, powder_g=50.0, tilt_world=TILT_DOSE_WORLD, v=0.018, record=False) -> dict:
    st = Station(magnet=magnet, powder_g=powder_g)
    dock_ext = DOCK_EXT * MM + 0.0012                      # 1.2 mm past the nominal dock: takes up the carriage's sag
    tilt_frame = L.frame_dose_tilt(tilt_world)
    e_tilt = ext_for_tilt(tilt_frame) + 0.0012
    T = {"dock0": 0.3}
    T["dock1"] = T["dock0"] + dock_ext / v
    T["mag"] = T["dock1"] + 0.2
    T["tilt0"] = T["mag"] + 0.45
    T["tilt1"] = T["tilt0"] + (e_tilt - dock_ext) / v
    T["dose0"] = T["tilt1"] + 0.4
    T["dose1"] = T["dose0"] + 2.0
    T["stall0"] = T["dose1"] + 0.2
    T["stall1"] = T["stall0"] + 0.4
    T["back0"] = T["stall1"] + 0.3
    T["back1"] = T["back0"] + (e_tilt - dock_ext + 0.0015) / v
    T["press1"] = T["back1"] + 0.4
    T["magoff"] = T["press1"] + 0.1
    T["ret0"] = T["magoff"] + 0.3
    T["ret1"] = T["ret0"] + dock_ext / v
    T["end"] = T["ret1"] + 0.4
    taps = [T["dose0"] + 0.25 + 0.5 * i for i in range(4)]
    Ft_nom = T_NOMINAL_AUGER / (22.0 * MM)                 # at the 44T pitch circle (R 22)
    Ft_stall = T_HOLD_PINION / (10.0 * MM)                 # at the pinion's pitch circle (R 10)

    def cmd(t):
        if t < T["dock0"]:
            return 0.0
        if t < T["dock1"]:
            return (t - T["dock0"]) * v
        if t < T["tilt0"]:
            return dock_ext
        if t < T["tilt1"]:
            return dock_ext + (t - T["tilt0"]) * v
        if t < T["back0"]:
            return e_tilt
        if t < T["back1"]:
            return max(dock_ext - 0.0015, e_tilt - (t - T["back0"]) * v)     # 1.5 mm past level: presses the plate into the hooks
        if t < T["ret0"]:
            return dock_ext - 0.0015
        if t < T["ret1"]:
            return max(0.0, dock_ext - 0.0015 - (t - T["ret0"]) * v)
        return 0.0

    rows = []
    n = int(T["end"] / DT)
    for i in range(n):
        t = i * DT
        st.mag_on = magnet and (T["mag"] <= t < T["magoff"])
        if not st.welded and T["mag"] + 0.25 <= t < T["magoff"]:      # the magnet seats the carriage first, then the weld
            st.weld(True)
        elif st.welded and t >= T["magoff"]:
            st.weld(False)
        if T["dose0"] <= t < T["dose1"]:
            st.F_tan, st.F_sep = Ft_nom, Ft_nom * SEP_FRICTION
        elif T["stall0"] <= t < T["stall1"]:
            ramp = min(1.0, (t - T["stall0"]) / 0.15)
            st.F_tan, st.F_sep = ramp * Ft_stall, ramp * Ft_stall * SEP_FRICTION
        else:
            st.F_tan = st.F_sep = 0.0
        st.F_tap = 4.0 if any(tp <= t < tp + 0.010 for tp in taps) else 0.0
        st.step(cmd(t))
        if i % 25 == 0:
            hr = st.hinge_reaction()
            gaps = st.rim_gap()
            rows.append(dict(t=t, cmd_mm=cmd(t) / MM, ext_mm=st.d.qpos[st.j_slide] / MM, F_act=float(st.d.actuator_force[0]),
                             tilt=st.tilt_deg(), gap_front=gaps[0], gap_back=gaps[1], g_mag=st.g_mag, F_mag=st.F_mag,
                             hinge_z=float(hr[2]), hinge_x=float(hr[0]), lip_f=st.contact_force("lip_f"), lip_b=st.contact_force("lip_b"),
                             foot=st.contact_force("foot_f") + st.contact_force("foot_b"),
                             tab_f=float(st.f_tab[0]), tab_b=float(st.f_tab[1]), dz_f=float(st.tab_dz()[0] / MM), dz_b=float(st.tab_dz()[1] / MM),
                             latched=int(st.latched), F_sep=st.F_sep, F_tap=st.F_tap, rim=st.contact_force("rim"),
                             **({f"dock_{k}": v for k, v in (st.dock_wrench() or {}).items()} if st.welded else {})))
    return dict(rows=rows, T=T, magnet=magnet, powder_g=powder_g, tilt_world=tilt_world, tilt_frame=tilt_frame)


def threshold(magnet=True, powder_g=0.0, tilts=(0.0, 15.0, 30.0, 45.0, 60.0, 75.0, 90.0), friction=SEP_FRICTION) -> list:
    """Docked and held at each hinge angle: ramp the gear's separating force (with its tangential share) from 0 to
    25 N over 2.5 s. The dock 'opens' when the rim's back end (next to the gear) lifts 0.1 mm off the plate."""
    out = []
    for tf in tilts:
        st = Station(magnet=magnet, powder_g=powder_g)
        e = ext_for_tilt(tf) + 0.0012
        e_dock = DOCK_EXT * MM + 0.0012
        st.d.qpos[st.j_slide] = DOCK_EXT * MM                # start exactly docked and welded (the approach is checked in cycle())
        for gname in ("fork_yl", "fork_yr", "fork_xa", "fork_xb"):     # the fork only guides the approach
            st.m.geom_contype[st.m.geom(gname).id] = 0
            st.m.geom_conaffinity[st.m.geom(gname).id] = 0
        mujoco.mj_forward(st.m, st.d)
        st.mag_on = magnet
        st.weld(True)
        settle(st, e_dock, 0.3)
        steps = int(max(0.2, (e - e_dock) / 0.02) / DT)
        for i in range(steps):
            st.step(e_dock + (e - e_dock) * min(1.0, (i + 1) / steps))
        settle(st, e, 0.4)
        F_open, tilt_at = None, st.tilt_deg()
        for i in range(int(2.5 / DT)):
            Fs = 25.0 * i * DT / 2.5
            st.F_sep, st.F_tan = Fs, Fs / friction
            st.step(e)
            if i % 20 == 0 and i > 0:
                w = st.dock_wrench()
                if F_open is None and w is not None and not w["holds"]:
                    F_open = Fs
                    break
        out.append(dict(tilt_frame=tf, tilt_actual=round(tilt_at, 2), magnet=magnet, powder_g=powder_g,
                        F_sep_open_N=None if F_open is None else round(F_open, 2),
                        F_tan_open_N=None if F_open is None else round(F_open / friction, 2),
                        pinion_torque_open_Nm=None if F_open is None else round(F_open / friction * 0.010, 4)))
        print(json.dumps(out[-1]), flush=True)
    return out


def summarize(res: dict) -> dict:
    R = res["rows"]
    T = res["T"]

    def win(a, b):
        return [r for r in R if T[a] <= r["t"] < T[b]]
    dose, stall = win("dose0", "dose1"), win("stall0", "stall1")
    tilt_ph = win("tilt0", "tilt1")
    back = win("back0", "press1")
    s = dict(magnet=res["magnet"], powder_g=res["powder_g"], tilt_world=res["tilt_world"], tilt_frame=res["tilt_frame"],
             tilt_reached=round(max(r["tilt"] for r in R), 2),
             F_act_peak_N=round(max(abs(r["F_act"]) for r in R), 2),
             F_act_dock_N=round(np.mean([r["F_act"] for r in win("mag", "tilt0")]), 2),
             F_act_dose_N=round(np.mean([r["F_act"] for r in dose]), 2),
             dock_gap_dose_max_mm=round(max(r["gap_back"] for r in dose), 3),
             dock_gap_stall_max_mm=round(max(r["gap_back"] for r in stall), 3),
             magnet_force_dose_N=round(np.mean([r["F_mag"] for r in dose]), 2),
             hinge_up_peak_N=round(max(r["hinge_z"] for r in R), 2),
             hinge_down_peak_N=round(min(r["hinge_z"] for r in R), 2),
             lip_force_peak_N=round(max(r["lip_f"] + r["lip_b"] for r in R), 2),
             foot_force_peak_N=round(max(r["foot"] for r in R), 2),
             tab_lift_peak_mm=round(max(max(r["dz_f"], r["dz_b"]) for r in R), 3),
             tab_drop_peak_mm=round(min(min(r["dz_f"], r["dz_b"]) for r in R), 3),
             relatched=bool(R[-1]["latched"]),
             tilt_end=round(R[-1]["tilt"], 3))
    for nm, rows in (("dose", dose), ("stall", stall), ("tilt", tilt_ph), ("back", back)):
        w = [r for r in rows if "dock_holds" in r]
        if w:
            s[f"dock_holds_{nm}"] = bool(all(r["dock_holds"] for r in w))
            s[f"dock_N_min_{nm}"] = round(min(r["dock_N"] for r in w), 2)
            s[f"dock_cp_margin_min_{nm}_mm"] = round(min(r["dock_cp_margin"] for r in w), 2)
    return s


def plot(results: list, path: Path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(4, 1, figsize=(10, 11), sharex=True)
    for res, ls in zip(results, ("-", "--")):
        R = res["rows"]
        t = [r["t"] for r in R]
        lab = "magnet on while docked" if res["magnet"] else "gravity only"
        ax[0].plot(t, [r["tilt"] for r in R], ls, label=f"tilt ({lab})")
        ax[1].plot(t, [r["F_act"] for r in R], ls, label=f"actuator force ({lab})")
        ax[2].plot(t, [r["gap_back"] for r in R], ls, label=f"dock gap at the gear end ({lab})")
        ax[3].plot(t, [r["hinge_z"] for r in R], ls, label=f"hinge reaction, up + ({lab})")
        ax[3].plot(t, [r["lip_f"] + r["lip_b"] for r in R], ls, label=f"hold-down lips ({lab})", alpha=0.6)
    T = results[0]["T"]
    for a in ax:
        for k, c in (("dose0", "g"), ("stall0", "r"), ("back0", "b"), ("magoff", "k")):
            a.axvline(T[k], color=c, lw=0.6, alpha=0.5)
        a.grid(alpha=0.3)
        a.legend(fontsize=8, loc="upper right")
    ax[0].set_ylabel("deg (frame)")
    ax[1].set_ylabel("N")
    ax[2].set_ylabel("mm")
    ax[2].set_ylim(-0.2, 3.0)
    ax[3].set_ylabel("N")
    ax[3].set_xlabel("s")
    ax[0].set_title("v2 station: dock, tilt to 30 deg, dose (taps), stall pulse, back into the hooks, undock")
    fig.tight_layout()
    fig.savefig(path, dpi=110)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("what", choices=["cycle", "threshold", "all"])
    ap.add_argument("--no-magnet", action="store_true")
    ap.add_argument("--powder", type=float, default=50.0)
    a = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    out = {}
    if a.what in ("cycle", "all"):
        res = [cycle(magnet=True, powder_g=a.powder)] if not a.no_magnet else []
        if a.what == "all" or a.no_magnet:
            res.append(cycle(magnet=False, powder_g=a.powder))
        out["cycle"] = [summarize(r) for r in res]
        for s in out["cycle"]:
            print(json.dumps(s))
        plot(res, OUT / "station_cycle.png")
        np.savez_compressed(OUT / "station_cycle.npz", **{f"{('mag' if r['magnet'] else 'grav')}_{k}": np.array([row[k] for row in r["rows"]])
                                                       for r in res for k in r["rows"][0]})
    if a.what in ("threshold", "all"):
        th = threshold(magnet=True, powder_g=0.0) + threshold(magnet=False, powder_g=0.0)
        out["threshold"] = th
    (OUT / "results.json").write_text(json.dumps(out, indent=1) + "\n")


if __name__ == "__main__":
    main()
