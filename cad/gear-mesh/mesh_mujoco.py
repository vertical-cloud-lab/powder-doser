"""MuJoCo model of the docked station drive with real tooth contact (both carousel designs).

The NEMA 11's 20T pinion and the auger's 44T gear are convex tooth prisms (the 44T teeth are
the lab STEP's own outline, the 20T a standard involute) that collide in MuJoCo, so the mesh
can do whatever the forces make it do: run, rattle, lift the module, or jump a tooth.

Bodies (Sam's studio frame, SI units inside, gravity turned for the station tilt):
  module   = Sam's plate + steel tab, hinged at the origin (the gondola lugs or the v2 carriage pins)
    auger  = tube + flights + cap + powder, turning on its axis, with the 44T teeth
  actuator = Actuonix P16 pinned to the frame at its base, a position-held rod (LAC), 50 N limit
    carriage = Sam's electronics carriage pinned to the rod end: rim pads and the magnet face
               press on the plate; optional locating pins in sockets in the plate
      pinion = 20T on the NEMA 11, with the rotor inertia, driven by a stepper torque-angle model
The dock electromagnet is a gap-dependent pull between its face and the steel tab.

    python mesh_mujoco.py calib                   # mesh stiffness against the FEA, static checks
    python mesh_mujoco.py run --tilt 30 --rpm 60 --config proposed --record
    python mesh_mujoco.py sweep                   # tilt x speed x config, nominal load
    python mesh_mujoco.py stall                   # load ramp to stall or tooth jump, tilt x config
"""
from __future__ import annotations

import argparse
import json
import math
import time
from pathlib import Path

import mujoco
import numpy as np

import common as C

HERE = Path(__file__).resolve().parent
OUT = C.OUT / "mujoco"
OUT.mkdir(parents=True, exist_ok=True)
MM = 1e-3
DT = 2.0e-5

GEAR_FACE = (78.73, 88.73)          # auger STEP z 78.33-88.33 + 0.4 (Sam's x)
PINION_FACE = (78.3, 88.3)          # pinion on the NEMA 11 shaft (paternoster layout)
PINION_Z = -C.A_DOCK                # pinion axis 32.1 mm under the auger axis when docked
MAG_X = 99.5                        # electromagnet centre (Sam's x)
MAG_GAP = 0.15                      # designed gap to the steel tab when docked (mm)
F0_MAG, G0_MAG = 20.0, 0.4          # F = F0/(1+g/g0)^2 (N, mm); fitted to the P20/15 later by magnet.py

CONFIGS = {
    # name: magnet, pinion material, tooth friction, rod-end pin (Sam x, z), locating pins
    "as drawn": dict(magnet=False, pinion="PETG (printed)", mu=0.30, pin=(40.0, -72.0), locpins=False),
    "magnet": dict(magnet=True, pinion="PETG (printed)", mu=0.30, pin=(40.0, -72.0), locpins=False),
    "magnet + steel pinion": dict(magnet=True, pinion="steel", mu=0.10, pin=(40.0, -72.0), locpins=False),
    "mesh-line pin": dict(magnet=True, pinion="steel", mu=0.10, pin=(83.5, -50.0), locpins=True),
    "proposed": dict(magnet=True, pinion="steel", mu=0.10, pin=(45.0, -34.0), locpins=True, a_dock=32.25),
    "proposed at 32.1 mm": dict(magnet=True, pinion="steel", mu=0.10, pin=(45.0, -34.0), locpins=True, a_dock=32.1),
    # as built in both designs: stub pins through the carriage's solid side posts (x 29-37)
    "final": dict(magnet=True, pinion="steel", mu=0.10, pin=(32.0, -34.0), locpins=True, a_dock=32.25),
}


# ---------------------------------------------------------------- teeth
def _hull(pts):
    from scipy.spatial import ConvexHull
    h = ConvexHull(pts)
    return pts[h.vertices]


def tooth_polygons():
    """(gear tooth polygon, pinion tooth polygon) in (y, z) of their own gear frame, tooth on +z (towards the mesh for
    the pinion, away for the gear: we rotate later). Convex hull of the tooth above its root circle."""
    cache = OUT / "tooth_polys.npz"
    if cache.exists():
        z = np.load(cache)
        return z["g"], z["p"]
    import fea_tooth as FT
    gg = json.loads((C.OUT / "gear_geometry.json").read_text())
    outs = []
    for outline, zt in ((FT.gear_outline_from_step(sum(gg["face_z_mm"]) / 2), C.Z2), (FT.pinion_outline(), C.Z1)):
        coords, lo, hi, n = FT.sector(outline, zt, r_in=5.0)
        arc = coords[:n]
        r = np.hypot(arc[:, 0], arc[:, 1])
        th = np.arctan2(arc[:, 1], arc[:, 0])
        rf = r.min()
        k = (np.abs(th - math.pi / 2) < math.pi / zt) & (r > rf + 0.12)
        P = arc[k]
        # add points on the root circle under the tooth so the prism has a base
        a0 = np.arctan2(P[:, 1], P[:, 0])
        base = np.array([[(rf - 0.3) * math.cos(a), (rf - 0.3) * math.sin(a)] for a in (a0.min(), a0.max())])
        outs.append(_hull(np.vstack([P, base])))
    np.savez(cache, g=outs[0], p=outs[1])
    return outs[0], outs[1]


def prism_vertices(poly, x0, x1):
    """Polygon in the gear plane (u = gear-frame 'x' of the 2D outline, v = its 'y') -> 3D prism along Sam's x.
    2D outline coords (a, b) map to Sam (y, z) = (a, b) in the gear's own body frame."""
    v = []
    for x in (x0, x1):
        for a, b in poly:
            v.append((x * MM, a * MM, b * MM))
    return " ".join(f"{c:.7f}" for p in v for c in p)


# ---------------------------------------------------------------- model
def gravity_sam(tilt_deg):
    a = math.radians(tilt_deg)
    return (-C.G * math.sin(a), 0.0, -C.G * math.cos(a))


def base_pin_sam(tilt_deg, pin):
    """Actuator base pin in Sam's frame at a station tilt: fixed in the world, directly below the docked rod-end pin."""
    a = math.radians(tilt_deg)
    xw, zw = pin[0], pin[1] - (197.4 + 20.0)          # P16-150 retracted length + the 20 mm dock stroke
    return (xw * math.cos(a) + zw * math.sin(a), -xw * math.sin(a) + zw * math.cos(a))


def build(tilt=30.0, config="proposed", powder=0.0, ecc=0.0, pitch_err=0.0, seed=0, mesh_tc=4.0e-4, a_dock=None):
    cfg = CONFIGS[config]
    a_dock = a_dock if a_dock is not None else cfg.get("a_dock", C.A_DOCK)
    pinion_z = -a_dock
    gpoly, ppoly = tooth_polygons()
    rng = np.random.default_rng(seed)
    perr = rng.normal(0.0, pitch_err, C.Z2) if pitch_err > 0 else np.zeros(C.Z2)
    mu = cfg["mu"]
    gx, gy, gz = gravity_sam(tilt)
    bx, bz = base_pin_sam(tilt, cfg["pin"])
    px, pz = cfg["pin"]
    d = np.array([px - bx, pz - bz])
    L = float(np.linalg.norm(d))
    d /= L
    m_pin = 0.020 if cfg["pinion"] == "steel" else 0.004
    j_pin = 0.5 * m_pin * (0.0105) ** 2 + C.J_ROTOR
    # module body = plate (CAD) + steel tab + screws/inserts; the auger + cap + powder is a child body
    mp = json.loads((C.OUT / "mass_props.json").read_text())
    m_plate, c_plate = mp["plate"]["mass_g"] / 1000, mp["plate"]["com_mm"]
    m_tab, c_tab = 0.0097, (100.0, 0.0, -19.0)                 # 2 mm low-carbon steel, 22 x 28 mm
    m_scr, c_scr = 0.002, (94.0, 0.0, -16.0)
    m_mod = m_plate + m_tab + m_scr
    xc = (m_plate * c_plate[0] + m_tab * c_tab[0] + m_scr * c_scr[0]) / m_mod * MM
    zc = (m_plate * c_plate[2] + m_tab * c_tab[2] + m_scr * c_scr[2]) / m_mod * MM
    iyy = mp["plate"]["Iy_hinge_gmm2"] * 1e-9 - m_plate * ((c_plate[0] * MM) ** 2 + (c_plate[2] * MM) ** 2) + 2e-6
    m_aug = C.M_AUG + powder
    x_aug = (mp["auger"]["mass_g"] * mp["auger"]["com_mm"][0] + mp["cap"]["mass_g"] * mp["cap"]["com_mm"][0]
             + powder * 1000 * C.POWDER_TILT_X) / (m_aug * 1000)
    iyy_aug = (mp["auger"]["Iy_hinge_gmm2"] + mp["cap"]["Iy_hinge_gmm2"]) * 1e-9 + powder * (C.POWDER_TILT_X * MM) ** 2 - m_aug * (x_aug * MM) ** 2
    j_aug = C.J_AUG + 0.5 * powder * (0.0105 ** 2) * 0.5
    car_parts = [(0.0177, 37.05, -41.57), (0.180, 50.8, -33.0), (0.030, 12.0, -35.0), (0.010, 40.0, -45.0)]
    if cfg["magnet"]:
        car_parts.append((0.027, MAG_X, -28.0))
    m_car = sum(p[0] for p in car_parts)
    cx_car = sum(p[0] * p[1] for p in car_parts) / m_car
    cz_car = sum(p[0] * p[2] for p in car_parts) / m_car
    sol_tooth = f'solref="{mesh_tc:.2e} 1.0" solimp="0.98 0.995 0.0002 0.5 2"'
    sol_dock = 'solref="0.001 1.0" solimp="0.95 0.99 0.0005 0.5 2"'
    X = []
    X.append(f"""<mujoco model="station-mesh">
  <compiler angle="radian" autolimits="true"/>
  <option timestep="{DT}" gravity="{gx:.5f} {gy:.5f} {gz:.5f}" integrator="implicitfast" cone="elliptic" impratio="1"
          noslip_iterations="0" iterations="60" tolerance="1e-10"/>
  <size memory="50M"/>
  <visual><global offwidth="1280" offheight="720"/><quality shadowsize="2048" offsamples="8"/>
    <headlight ambient="0.4 0.4 0.4" diffuse="0.6 0.6 0.6"/><map znear="0.001" zfar="5"/></visual>
  <asset>
    <mesh name="gtooth" vertex="{prism_vertices(gpoly, *GEAR_FACE)}"/>
    <mesh name="ptooth" vertex="{prism_vertices(ppoly, *PINION_FACE)}"/>
    <material name="plate" rgba="0.10 0.25 0.85 1"/><material name="steel" rgba="0.60 0.62 0.66 1"/>
    <material name="auger" rgba="0.90 0.90 0.86 1"/><material name="carr" rgba="0.20 0.70 0.40 1"/>
    <material name="pinion" rgba="0.95 0.45 0.05 1"/><material name="act" rgba="0.2 0.2 0.22 1"/>
    <material name="gear" rgba="0.85 0.85 0.80 1"/><material name="mag" rgba="0.75 0.15 0.15 1"/>
  </asset>
  <default>
    <geom contype="0" conaffinity="0" condim="3" friction="0.3 0.005 0.0001"/>
    <default class="tooth"><geom condim="3" friction="{mu} 0.0 0.0" {sol_tooth} margin="0" gap="0"/></default>
    <default class="dock"><geom condim="3" friction="0.4 0.0 0.0" {sol_dock}/></default>
  </default>
  <worldbody>
    <light pos="0.05 -0.3 0.3" dir="0 1 -1" diffuse="0.6 0.6 0.6"/>
    <camera name="mesh" pos="{0.150:.4f} {-0.020:.4f} {-0.016:.4f}" xyaxes="0 1 0 0 0 1" fovy="22"/>
    <camera name="side" pos="0.06 -0.32 -0.03" xyaxes="1 0 0 0 0 1" fovy="40"/>
    <body name="module" pos="0 0 0">
      <joint name="lift" type="hinge" axis="0 -1 0" damping="0.0005" range="{-0.6 / 100.0:.5f} 1.6" limited="true"/>
      <inertial pos="{xc:.5f} 0 {zc:.5f}" mass="{m_mod:.5f}" diaginertia="{iyy * 0.15:.3e} {iyy:.3e} {iyy:.3e}"/>
      <geom name="plate" class="dock" type="box" pos="{61.9 * MM:.5f} 0 {-15.5 * MM:.5f}" size="{36.9 * MM:.5f} {25 * MM:.5f} {2.5 * MM:.5f}"
            contype="16" conaffinity="8" material="plate"/>
      <geom name="tab" class="dock" type="box" pos="{100.0 * MM:.5f} 0 {-19.0 * MM:.5f}" size="{11.0 * MM:.5f} {14 * MM:.5f} {1.0 * MM:.5f}"
            contype="16" conaffinity="8" material="steel"/>
      <geom type="box" pos="{2 * MM:.5f} 0 {-6 * MM:.5f}" size="{4 * MM:.5f} {25 * MM:.5f} {6 * MM:.5f}" material="plate"/>""")
    if cfg["locpins"]:
        for (sx, sy) in ((30.0, 16.0), (70.0, -16.0)):
            for dx, dy, hx, hy in ((2.6, 0, 0.5, 3.1), (-2.6, 0, 0.5, 3.1), (0, 2.6, 3.1, 0.5), (0, -2.6, 3.1, 0.5)):
                X.append(f'      <geom class="dock" type="box" pos="{(sx + dx) * MM:.5f} {(sy + dy) * MM:.5f} {-15.0 * MM:.5f}" '
                         f'size="{hx * MM:.5f} {hy * MM:.5f} {2.0 * MM:.5f}" contype="64" conaffinity="32" rgba="0.1 0.2 0.7 0.4"/>')
    X.append(f"""      <body name="auger" pos="0 0 0">
        <joint name="spin" type="hinge" axis="1 0 0" damping="1e-5"/>
        <inertial pos="{x_aug * MM:.5f} 0 0" mass="{m_aug:.5f}" diaginertia="{j_aug:.3e} {iyy_aug:.3e} {iyy_aug:.3e}"/>
        <geom type="cylinder" fromto="{0.4 * MM:.5f} 0 0 {250.4 * MM:.5f} 0 0" size="{12.5 * MM:.5f}" material="auger" rgba="0.9 0.9 0.86 0.35"/>
        <geom type="cylinder" fromto="{GEAR_FACE[0] * MM:.5f} 0 0 {GEAR_FACE[1] * MM:.5f} 0 0" size="{20.8 * MM:.5f}" material="gear"/>""")
    for k in range(C.Z2):
        a = 2 * math.pi * k / C.Z2 + perr[k]
        # tooth polygon is centred on the 2D +y axis; Sam (y, z) = (a2d, b2d): rotate about x by angle a
        q = (math.cos(a / 2), math.sin(a / 2), 0, 0)
        X.append(f'        <geom class="tooth" type="mesh" mesh="gtooth" pos="0 {ecc * MM * math.cos(0):.6f} 0" quat="{q[0]:.7f} {q[1]:.7f} 0 0" '
                 f'contype="2" conaffinity="4" material="gear"/>')
    X.append("      </body>\n    </body>")
    # actuator + carriage
    ang = math.atan2(d[0], d[1])
    X.append(f"""    <body name="act" pos="{bx * MM:.5f} 0 {bz * MM:.5f}">
      <joint name="act_pivot" type="hinge" axis="0 1 0" damping="0.002"/>
      <geom type="box" pos="{d[0] * 0.09:.5f} 0 {d[1] * 0.09:.5f}" size="0.0105 0.0105 0.085" euler="0 {ang:.5f} 0" mass="0.06" material="act"/>
      <body name="rod" pos="0 0 0">
        <joint name="act_slide" type="slide" axis="{d[0]:.6f} 0 {d[1]:.6f}" damping="5"/>
        <geom type="capsule" fromto="{d[0] * 0.12:.5f} 0 {d[1] * 0.12:.5f} {d[0] * L * MM:.5f} 0 {d[1] * L * MM:.5f}" size="0.004" mass="0.02" material="steel"/>
        <body name="carriage" pos="{(px - bx) * MM:.5f} 0 {(pz - bz) * MM:.5f}">
          <joint name="car_pin" type="hinge" axis="0 1 0" damping="0.0005"/>
          <inertial pos="{(cx_car - px) * MM:.5f} 0 {(cz_car - pz) * MM:.5f}" mass="{m_car:.4f}" diaginertia="1.2e-4 2.0e-4 1.2e-4"/>
          <geom type="box" pos="{(37.8 - px) * MM:.5f} 0 {(-39.4 - pz) * MM:.5f}" size="{35.5 * MM:.5f} {18 * MM:.5f} {21.0 * MM:.5f}" material="carr" rgba="0.2 0.7 0.4 0.35"/>""")
    for (x0, x1) in ((25.0, 29.0), (69.3, 73.3)):
        for sy in (-1, 1):
            X.append(f'          <geom class="dock" type="box" pos="{((x0 + x1) / 2 - px) * MM:.5f} {sy * 16 * MM:.5f} {(-19.0 - pz) * MM:.5f}" '
                     f'size="{(x1 - x0) / 2 * MM:.5f} {2 * MM:.5f} {1.0 * MM:.5f}" contype="8" conaffinity="16" material="carr"/>')
    if cfg["magnet"]:
        X.append(f'          <geom name="magface" class="dock" type="cylinder" pos="{(MAG_X - px) * MM:.5f} 0 {(-20.15 - 0.5 - pz) * MM:.5f}" '
                 f'size="{10 * MM:.5f} {0.5 * MM:.5f}" contype="8" conaffinity="16" material="mag"/>')
        X.append(f'          <geom type="cylinder" pos="{(MAG_X - px) * MM:.5f} 0 {(-28.15 - pz) * MM:.5f}" size="{10 * MM:.5f} {7.5 * MM:.5f}" material="mag" rgba="0.6 0.1 0.1 0.5"/>')
    if cfg["locpins"]:
        for (sx, sy) in ((30.0, 16.0), (70.0, -16.0)):
            X.append(f'          <geom class="dock" type="capsule" fromto="{(sx - px) * MM:.5f} {sy * MM:.5f} {(-19.0 - pz) * MM:.5f} {(sx - px) * MM:.5f} {sy * MM:.5f} {(-14.5 - pz) * MM:.5f}" '
                     f'size="{2.0 * MM:.5f}" contype="32" conaffinity="64" material="steel"/>')
    X.append(f"""          <body name="pinion" pos="{(GEAR_FACE[0] + GEAR_FACE[1]) / 2 * MM - px * MM:.5f} 0 {(pinion_z - pz) * MM:.5f}">
            <joint name="motor" type="hinge" axis="1 0 0" damping="0"/>
            <inertial pos="0 0 0" mass="{m_pin:.4f}" diaginertia="{j_pin:.3e} {0.6 * j_pin:.3e} {0.6 * j_pin:.3e}"/>
            <geom type="cylinder" fromto="{(PINION_FACE[0] - 83.73) * MM:.5f} 0 0 {(PINION_FACE[1] - 83.73) * MM:.5f} 0 0" size="{8.8 * MM:.5f}" material="pinion"/>""")
    for k in range(C.Z1):
        a = 2 * math.pi * k / C.Z1 + math.pi / C.Z1          # pinion tooth half-phase so a gear tooth sits in a pinion space
        q = (math.cos(a / 2), math.sin(a / 2), 0, 0)
        X.append(f'            <geom class="tooth" type="mesh" mesh="ptooth" pos="{-83.73 * MM:.5f} 0 0" quat="{q[0]:.7f} {q[1]:.7f} 0 0" '
                 f'contype="4" conaffinity="2" material="pinion"/>')
    X.append("""          </body>
        </body>
      </body>
    </body>
  </worldbody>
  <actuator>""")
    X.append(f'    <general name="lac" joint="act_slide" gainprm="1" biastype="affine" biasprm="0 -2.0e5 -400" forcelimited="true" forcerange="-50 50"/>')
    X.append("  </actuator>\n</mujoco>")
    xml = "\n".join(X)
    info = dict(tilt=tilt, config=config, a_dock_mm=a_dock, L_act_mm=L, carriage_com_mm=(round(cx_car, 2), round(cz_car, 2)), m_carriage=m_car, base_sam_mm=(bx, bz), pin_sam_mm=(px, pz), powder=powder,
                j_pin=j_pin, j_aug=j_aug, m_mod=m_mod)
    return xml, info


# ---------------------------------------------------------------- helpers
class Station:
    def __init__(self, tilt=30.0, config="proposed", powder=0.0, ecc=0.0, pitch_err=0.0, seed=0, mesh_tc=4.0e-4,
                 v_supply=24.0, i_set=0.95, a_dock=None):
        self.xml, self.info = build(tilt, config, powder, ecc, pitch_err, seed, mesh_tc, a_dock)
        self.m = mujoco.MjModel.from_xml_string(self.xml)
        self.d = mujoco.MjData(self.m)
        self.cfg = CONFIGS[config]
        self.v_supply, self.i_set = v_supply, i_set
        m = self.m
        self.j = {n: m.joint(n).id for n in ("lift", "spin", "act_pivot", "act_slide", "car_pin", "motor")}
        self.qa = {n: m.jnt_qposadr[i] for n, i in self.j.items()}
        self.va = {n: m.jnt_dofadr[i] for n, i in self.j.items()}
        self.b = {n: m.body(n).id for n in ("module", "auger", "carriage", "pinion")}
        self.theta_cmd = 0.0
        self.w_cmd = 0.0
        self.t_load = 0.0
        self.magnet_on = self.cfg["magnet"]
        self.f_mag = 0.0
        self.gap = 0.0

    # --- geometry probes (mm)
    def point(self, body, p_local_mm):
        R = self.d.xmat[self.b[body]].reshape(3, 3)
        return (self.d.xpos[self.b[body]] + R @ (np.asarray(p_local_mm) * MM)) / MM

    def centre_distance(self):
        g = self.point("auger", (83.73, 0, 0))
        p = self.d.xpos[self.b["pinion"]] / MM
        return float(np.hypot(g[1] - p[1], g[2] - p[2]))

    def mag_gap(self):
        """Gap between the magnet face and the tab's underside, along the module's z (mm)."""
        Rm = self.d.xmat[self.b["module"]].reshape(3, 3)
        tab = self.point("module", (MAG_X, 0, -20.0))
        face = self.point("carriage", (MAG_X - self.info["pin_sam_mm"][0], 0, -20.15 - self.info["pin_sam_mm"][1]))
        return float((tab - face) @ Rm[:, 2])

    def rim_gaps(self):
        Rm = self.d.xmat[self.b["module"]].reshape(3, 3)
        px, pz = self.info["pin_sam_mm"]
        out = []
        for x in (27.0, 71.3):
            pl = self.point("module", (x, 0, -18.0))
            ri = self.point("carriage", (x - px, 0, -18.0 - pz))
            out.append(float((pl - ri) @ Rm[:, 2]))
        return out

    def mesh_phase(self):
        """Gear angle + (z1/z2) * pinion angle, in gear tooth pitches (constant while meshed)."""
        return (self.d.qpos[self.qa["spin"]] + C.Z1 / C.Z2 * self.d.qpos[self.qa["motor"]]) / (2 * math.pi / C.Z2)

    # --- forces
    def motor_torque(self):
        import shigley as S
        w = self.d.qvel[self.va["motor"]]
        tmax = float(S.motor_torque(abs(w) / (2 * math.pi), self.v_supply, self.i_set))
        e = C.N_ROTOR * (self.theta_cmd - self.d.qpos[self.qa["motor"]])
        return tmax * math.sin(e) - 2.0e-4 * (w - self.w_cmd), e

    def apply(self):
        d = self.d
        d.qfrc_applied[:] = 0.0
        tm, _ = self.motor_torque()
        d.qfrc_applied[self.va["motor"]] += tm
        wg = d.qvel[self.va["spin"]]
        d.qfrc_applied[self.va["spin"]] += -self.t_load * math.tanh(wg / 0.05) if self.t_load > 0 else 0.0
        if self.magnet_on:
            g = self.mag_gap()
            self.gap = g
            f = F0_MAG / (1.0 + max(g, 0.0) / G0_MAG) ** 2
            self.f_mag = f
            Rm = d.xmat[self.b["module"]].reshape(3, 3)
            nz = Rm[:, 2]
            p_tab = self.point("module", (MAG_X, 0, -20.0)) * MM
            mujoco.mj_applyFT(self.m, d, -f * nz, np.zeros(3), p_tab, self.b["module"], d.qfrc_applied)
            mujoco.mj_applyFT(self.m, d, f * nz, np.zeros(3), p_tab, self.b["carriage"], d.qfrc_applied)

    def step(self, n=1):
        for _ in range(n):
            self.theta_cmd += self.w_cmd * DT
            self.apply()
            mujoco.mj_step(self.m, self.d)

    def settle(self, t=0.15):
        """Hold the LAC at the docked length (keeps the plate on the rim), let contacts and the magnet settle."""
        d, m = self.d, self.m
        d.ctrl[0] = 0.0
        # the rod's slide joint starts at 0 = docked length; the position servo holds it (biasprm: -kp*q)
        self.step(int(t / DT))


def mesh_tc_for(pinion):
    """Contact time constant giving the FEA single-pair stiffness (calibrated with `calib`)."""
    return 4.0e-4


def run(tilt=30.0, rpm=60.0, config="proposed", powder=0.0, t_run=0.6, load=0.03, ecc=0.05, pitch_err=0.0006,
        seed=0, record=False, v_supply=24.0, ramp_load=None, tag=None, a_dock=None, i_set=0.95):
    S = Station(tilt, config, powder, ecc=ecc, pitch_err=pitch_err, seed=seed,
                mesh_tc=mesh_tc_for(CONFIGS[config]["pinion"]), v_supply=v_supply, a_dock=a_dock, i_set=i_set)
    t0 = time.time()
    S.settle(0.12)
    ph0 = S.mesh_phase()
    w_motor = -rpm / 60 * 2 * math.pi * C.Z2 / C.Z1          # pinion turns opposite to the auger
    log = []
    frames = []
    n_ramp = int(0.08 / DT)
    n_run = int(t_run / DT)
    skip_t = None
    stall_t = None
    every = max(1, int(1e-4 / DT))
    for i in range(n_ramp + n_run):
        S.w_cmd = w_motor * min(1.0, i / n_ramp)
        if ramp_load is not None:
            S.t_load = ramp_load * max(0.0, (i - n_ramp) / n_run)
        else:
            S.t_load = load * (1.0 + 0.5 * math.sin(S.d.qpos[S.qa["spin"]]))   # one slug per revolution
        S.step()
        if i % every == 0:
            ph = S.mesh_phase() - ph0
            _, e = S.motor_torque()
            cd = S.centre_distance()
            rg = S.rim_gaps()
            g = S.mag_gap() if S.cfg["magnet"] else float("nan")
            log.append((S.d.time, S.d.qpos[S.qa["spin"]], S.d.qvel[S.qa["spin"]] if False else S.d.qvel[S.va["spin"]],
                        ph, e, cd, rg[0], rg[1], g, S.f_mag, S.t_load, S.d.qpos[S.qa["lift"]], S.d.actuator_force[0]))
            if skip_t is None and abs(ph) > 0.5:
                skip_t = S.d.time
            if stall_t is None and abs(e) > math.pi:
                stall_t = S.d.time
            if record and i % int(1 / 240 / DT) == 0:
                frames.append(S.d.qpos.copy())
        if ramp_load is not None and (skip_t is not None or stall_t is not None) and S.d.time > (skip_t or stall_t or 0) + 0.05:
            break
    A = np.array(log)
    k = A[:, 0] > A[0, 0] + 0.08 + 0.05 if ramp_load is None else np.ones(len(A), bool)
    res = dict(tilt=tilt, rpm=rpm, config=config, a_dock_mm=S.info["a_dock_mm"], i_set_A=i_set, powder_g=powder * 1000,
               load_Nm=load if ramp_load is None else None,
               ecc_mm=ecc, pitch_err_rad=pitch_err, v_supply=v_supply,
               tooth_jumps=int(round(abs(A[-1, 3]))) if abs(A[-1, 3]) > 0.5 else 0, first_jump_s=skip_t, stall_s=stall_t,
               centre_distance_mm=dict(mean=float(A[k, 5].mean()), max=float(A[k, 5].max()), min=float(A[k, 5].min())),
               rim_gap_front_mm_max=float(A[k, 6].max()), rim_gap_back_mm_max=float(A[k, 7].max()),
               mag_gap_mm_max=float(np.nanmax(A[k, 8])) if S.cfg["magnet"] else None,
               lift_deg_max=float(np.degrees(A[k, 11].max() - A[0, 11])),
               actuator_N=dict(min=float(A[k, 12].min()), max=float(A[k, 12].max())),
               wall_s=round(time.time() - t0, 1), sim_s=float(S.d.time))
    if ramp_load is not None:
        tj = skip_t or stall_t
        res["mode"] = "tooth jump" if (skip_t is not None and (stall_t is None or skip_t <= stall_t)) else ("motor stall" if stall_t else "held")
        res["load_at_failure_Nm"] = float(np.interp(tj, A[:, 0], A[:, 10])) if tj else None
    tag = tag or f"{config.replace(' ', '_').replace('+', '')}_t{tilt:g}_r{rpm:g}" + ("_ramp" if ramp_load else "")
    np.savez_compressed(OUT / f"{tag}.npz", log=A, frames=np.array(frames) if frames else np.zeros(0))
    (OUT / f"{tag}.json").write_text(json.dumps(res, indent=1))
    return res, S


def calib():
    """Mesh stiffness: hold the pinion, apply a torque to the auger, read the extra rotation -> N/um along the line of action."""
    out = {}
    for tc in (2.0e-4, 4.0e-4, 8.0e-4):
        S = Station(0.0, "proposed", 0.0, mesh_tc=tc)
        S.settle(0.1)
        th0 = S.d.qpos[S.qa["spin"]]
        S.t_load = 0.0
        res = []
        for T in (0.05, 0.10, 0.20):
            # constant torque on the auger against the held pinion (motor holds theta_cmd = 0)
            for _ in range(int(0.06 / DT)):
                S.theta_cmd = 0.0
                S.apply()
                S.d.qfrc_applied[S.va["spin"]] += -T
                mujoco.mj_step(S.m, S.d)
            dth = S.d.qpos[S.qa["spin"]] - th0
            dm = S.d.qpos[S.qa["motor"]]
            # line-of-action deflection = r_b2 * (gear rotation relative to the pinion's)
            rel = (dth + C.Z1 / C.Z2 * dm)
            Wn = T / (C.RB2 * MM)
            res.append(dict(T=T, rel_urad=rel * 1e6, defl_um=abs(rel) * C.RB2 * 1000, Wn=Wn,
                            k_N_per_um=Wn / max(abs(rel) * C.RB2 * 1000, 1e-9)))
        out[f"{tc:.1e}"] = res
        print(tc, res)
    (OUT / "calib.json").write_text(json.dumps(out, indent=1))
    return out


FAIL_CONFIGS = ["as drawn", "magnet", "magnet + steel pinion", "pin (48,-58)", "proposed"]
CONFIGS["pin (48,-58)"] = dict(magnet=True, pinion="steel", mu=0.10, pin=(48.0, -58.0), locpins=True)


def stall_sweep(tilts=(0, 15, 30, 45, 60, 75, 90), configs=FAIL_CONFIGS, name="stall_sweep"):
    """Ramp the auger's load torque at 30 rpm until a tooth jumps or the motor stalls."""
    rows = []
    for cfg in configs:
        for t in tilts:
            r, _ = run(tilt=float(t), rpm=30.0, config=cfg, t_run=1.2, ramp_load=0.45, ecc=0.0, pitch_err=0.0,
                       tag=f"stall_{cfg.replace(' ', '_').replace('+', '').replace('(', '').replace(')', '').replace(',', '_')}_t{t}")
            rows.append(r)
            print(cfg, t, r["mode"], r["load_at_failure_Nm"], r["centre_distance_mm"]["max"], flush=True)
    (OUT / f"{name}.json").write_text(json.dumps(rows, indent=1))
    return rows


def runout_sweep(eccs=(0.0, 0.025, 0.05, 0.075, 0.1), configs=("proposed at 32.1 mm", "proposed"), tilt=30.0, rpm=60.0,
                 name="runout_sweep"):
    """How much gear runout each dock centre distance tolerates (nominal load, 1.2 revolutions)."""
    rows = []
    for cfg in configs:
        for e in eccs:
            r, _ = run(tilt=tilt, rpm=rpm, config=cfg, t_run=1.2, load=0.03, ecc=e, pitch_err=0.0006,
                       tag=f"runout_{cfg.replace(' ', '_').replace('.', 'p')}_e{e:g}")
            rows.append(r)
            print(cfg, e, "jumps", r["tooth_jumps"], "stall", r["stall_s"], "cd", round(r["centre_distance_mm"]["min"], 3),
                  round(r["centre_distance_mm"]["max"], 3), flush=True)
    (OUT / f"{name}.json").write_text(json.dumps(rows, indent=1))
    return rows


def speed_sweep(tilts=(0, 30, 60, 90), rpms=(30, 60, 120, 240), configs=("as drawn", "magnet + steel pinion", "proposed"),
                ecc=0.0, pitch_err=0.0, name="speed_sweep"):
    """Nominal dosing load (0.03 N*m at the auger, +-50 % once per revolution) with printed-gear errors: 0.05 mm runout,
    13 um rms pitch error. At least 1.2 auger revolutions per run."""
    rows = []
    for cfg in configs:
        for t in tilts:
            for rpm in rpms:
                t_run = max(0.6, 1.2 * 60.0 / rpm)
                r, _ = run(tilt=float(t), rpm=float(rpm), config=cfg, t_run=t_run, load=0.03, ecc=ecc, pitch_err=pitch_err,
                           tag=f"{name}_{cfg.replace(' ', '_').replace('+', '')}_t{t}_r{rpm}")
                rows.append(r)
                print(cfg, t, rpm, "jumps", r["tooth_jumps"], "stall", r["stall_s"], "cd", round(r["centre_distance_mm"]["min"], 3),
                      round(r["centre_distance_mm"]["max"], 3), flush=True)
    (OUT / f"{name}.json").write_text(json.dumps(rows, indent=1))
    return rows


def engage(config="proposed", tilt=0.0, phase=0.5, seek_rps=0.0, approach_mm=3.0, v_mm_s=10.0, drag=0.02, f_push=15.0,
           record=False, tag=None):
    """Docking: the carriage rises the last approach_mm onto the plate with the pinion at a phase offset (fraction of a
    pinion pitch; 0.5 = tooth tip on tooth tip). The pinion is held, or turns slowly (seek) until the plate seats on the
    rim. The auger has its powder/bearing drag. The LAC pushes with at most f_push (its current limit) during the dock.
    The magnet is switched on only after the plate seats."""
    S = Station(tilt, config)
    m = S.m
    m.actuator_forcerange[0] = (-f_push, f_push)
    kp = 2.0e5
    S.magnet_on = False
    S.d.qpos[S.qa["act_slide"]] = -approach_mm * MM
    S.d.qpos[S.qa["motor"]] = phase * 2 * math.pi / C.Z1
    S.theta_cmd = S.d.qpos[S.qa["motor"]]
    mujoco.mj_forward(S.m, S.d)
    log, frames = [], []
    n_app = int(approach_mm / v_mm_s / DT)
    n_max = n_app + int(1.0 / DT)
    seated_t, seat_i, ok_since = None, None, None
    S.t_load = drag
    i = 0
    while i < n_max:
        target = -approach_mm * MM * max(0.0, 1.0 - i / n_app)
        S.d.ctrl[0] = kp * target
        seeking = seek_rps > 0 and seated_t is None
        S.w_cmd = -seek_rps * 2 * math.pi if seeking else 0.0
        S.step()
        if i % int(1e-4 / DT) == 0:
            rg = S.rim_gaps()
            cd = S.centre_distance()
            log.append((S.d.time, S.d.qpos[S.qa["act_slide"]] / MM, cd, rg[0], rg[1], S.d.actuator_force[0],
                        S.d.qpos[S.qa["motor"]], S.d.qpos[S.qa["spin"]]))
            ok = i > n_app * 0.5 and abs(cd - S.info["a_dock_mm"]) < 0.08 and max(rg) < 0.15
            if seated_t is None:
                if ok:
                    ok_since = ok_since if ok_since is not None else S.d.time
                    if S.d.time - ok_since >= 0.02:
                        seated_t, seat_i = ok_since, i
                        S.magnet_on = CONFIGS[config]["magnet"]
                        m.actuator_forcerange[0] = (-50.0, 50.0)
                else:
                    ok_since = None
        if record and i % int(1 / 240 / DT) == 0:
            frames.append(S.d.qpos.copy())
        if seat_i is not None and i > seat_i + int(0.15 / DT):
            break
        i += 1
    A = np.array(log)
    res = dict(config=config, tilt=tilt, phase=phase, seek_rps=seek_rps, drag_Nm=drag, push_N=f_push,
               seated=bool(seated_t is not None), seated_after_s=(seated_t - n_app * DT) if seated_t else None,
               final_centre_distance_mm=float(A[-1, 2]), final_rim_gaps_mm=[float(A[-1, 3]), float(A[-1, 4])],
               peak_actuator_N=float(A[:, 5].max()))
    tag = tag or f"engage_{config.replace(' ', '_')}_p{phase:g}_s{seek_rps:g}"
    np.savez_compressed(OUT / f"{tag}.npz", log=A, frames=np.array(frames) if frames else np.zeros(0))
    (OUT / f"{tag}.json").write_text(json.dumps(res, indent=1))
    return res, S


def engage_sweep():
    rows = []
    for phase in (0.0, 0.1, 0.2, 0.3, 0.4, 0.5):
        for seek in (0.0, 0.25):
            r, _ = engage("proposed", 0.0, phase, seek)
            rows.append(r)
            print(r, flush=True)
    (OUT / "engage_sweep.json").write_text(json.dumps(rows, indent=1))
    return rows


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["calib", "run", "xml", "stall", "speed", "engage", "runout", "speed_err", "all"])
    ap.add_argument("--tilt", type=float, default=30.0)
    ap.add_argument("--rpm", type=float, default=60.0)
    ap.add_argument("--config", default="proposed")
    ap.add_argument("--t", type=float, default=0.6)
    ap.add_argument("--load", type=float, default=0.03)
    ap.add_argument("--ramp", type=float, default=None)
    ap.add_argument("--record", action="store_true")
    a = ap.parse_args()
    if a.cmd == "calib":
        calib()
    elif a.cmd == "xml":
        print(build(a.tilt, a.config)[0][:3000])
    elif a.cmd == "stall":
        stall_sweep()
    elif a.cmd == "speed":
        speed_sweep()
    elif a.cmd == "engage":
        engage_sweep()
    elif a.cmd == "runout":
        runout_sweep()
    elif a.cmd == "speed_err":
        speed_sweep(configs=("proposed",), ecc=0.05, pitch_err=0.0006, name="speed_sweep_errors")
    elif a.cmd == "all":
        stall_sweep()
        engage_sweep()
        speed_sweep()
    else:
        r, _ = run(a.tilt, a.rpm, a.config, t_run=a.t, load=a.load, ramp_load=a.ramp, record=a.record)
        print(json.dumps(r, indent=1))
