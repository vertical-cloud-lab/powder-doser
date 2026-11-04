"""v3 station in MuJoCo: the EC rising in its guide cradle, capturing the plate's balls in its cone and vee, seating,
tilting with the module, and undocking back onto its cradle seat. Contacts only (no welds).

    python sim/station_mj.py capture            # carriage 0, 1, 2, 3 mm off its index along the run: rise and seat
    python sim/station_mj.py cycle --off 1      # rise, seat, tilt to 30 deg, dose, back, undock (and the video data)
    xvfb-run -a python sim/station_mj.py video  # MP4 + GIF of the cycle (MUJOCO_GL=glfw)

Model (Sam's frame at the station, metres inside; z up, hinge axis along y through the origin; ../params.py):
* Carriage: slides along the run (y) and up (z) on the chain, 2 x 2.8 N/mm each way (two A-1 tabs, 80 N pretension),
  rest position off its index by --off mm along the run; the hold-downs stop it 2 mm up and 4 mm down.
* Module (plate, armature, auger, powder 50 g) on its hinge, resting on its pads (the latch is open at the station).
  The plate's balls A and B are spheres; the armature is a box. The outlet door is a slide on the module with its spring
  (0.06 N/mm, 0.27 N shut) and its push strip down to z -22.
* EC v3 (0.311 kg): its dock cone (8 printed facets, 45 deg), its vee (two 1/8 in dowels), ball C, the coil's face, the
  door finger, its lower body and three base balls. It hangs on the P16's rod end through a pin in 2 mm slots (a slide
  along its z limited to +-1 mm, and a hinge), with +-1 mm along y so the cradle's side walls take the side loads.
* P16: pinned at its base, a position servo on the rod (30 N/mm, limited to 50 N).
* Cradle: side walls 0.3 mm off the EC's body, front wall 0.3 mm ahead of it (with the notch for the ears), the seat's
  cone, dowel vee and flat for the base balls.
* Magnets: the seat magnets' pull on balls A and B against gap from dock_statics.py (results/magnet_curve_cache.json,
  scaled to K&J's case 1); the coil F = 20 / (1 + g / 0.4)^2 N on the armature while it is on.
* Friction: 0.25 steel on printed PETG, 0.15 steel on steel; contacts soft to about 0.01 mm.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys
from pathlib import Path

import mujoco
import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))
import kelvin as K  # noqa: E402
from params import *  # noqa: E402,F401,F403

OUT = HERE / "results"
MM = 1e-3
DT = 1e-4
G = 9.81
M_EC, COM_EC = 0.3111, np.array([51.9, -0.1, -34.2])          # dock_statics.py (docked, Sam frame)
M_MOD0, COM_MOD0 = 0.1271, np.array([90.1, 0.0, -5.1])
PIN_D = np.array([EC_PIN[0], 0.0, EC_PIN[1] + DOCK_RISE_V3])   # clevis pin, docked
B_PIN0 = np.array([EC_PIN[0], 0.0, PIN_D[2] - PARK_DROP - ACT_RETRACTED])   # P16 base pin (layout.actuator_pins)
B_PIN = B_PIN0.copy()
SWING = dict(preload=0.0, k=3.0)
FINGER_X = [-3.6, -0.6]               # as drawn; proposed: [-3.6, 0.0] with a 1.5 mm foot on the strip (overlap 0.8 -> 2.9 mm)
STRIP_FOOT = [0.0]
EY_FREE = [0.0]                       # proposed: the EC free to shift this far along the run (side walls this far out, base clevis slotted)       # proposed fix: N*m holding the P16 on a stop at vertical (0: as drawn, free to swing)


def set_base_dx(dx):
    """Proposed fix: move the P16's base pin dx mm back (+x), so its rod leans forward and its thrust presses the EC on the
    cradle's front wall while it rises (as drawn, dx = 0, the rod is vertical and nothing holds the EC's bottom back)."""
    B_PIN[:] = B_PIN0 + np.array([dx, 0.0, -(math.sqrt(ACT_RETRACTED ** 2 - dx ** 2) - ACT_RETRACTED) if dx else 0.0])
ZB = KC_BALL_Z
H_VEE = math.sqrt((KC_BALL_D / 2 + VEE_DOWEL_D / 2) ** 2 - (VEE_SPACING / 2) ** 2)
R_B = KC_BALL_D / 2
K_RUN = 2 * 2800.0                                              # N/m along the run, two tabs
K_UP = 2 * 2800.0
MU_PETG, MU_STEEL = 0.25, 0.15
CURVE = json.loads((OUT / "magnet_curve_cache.json").read_text())
_CG = np.array([c["gap_mm"] for c in CURVE])
_CF = np.array([c["pull_kj_scaled_N"] for c in CURVE])


def seat_pull(gap_mm):
    if gap_mm > 6.0:
        return 0.0
    return float(np.interp(max(gap_mm, 0.0), _CG, _CF))


def _f(*v):
    return " ".join(f"{x:.6g}" for x in v)


def box(name, x0, x1, y0, y1, z0, z1, rgba, ct, ca, rel=np.zeros(3), fr=MU_PETG, group=0):
    c = (np.array([(x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2]) - rel) * MM
    h = np.array([(x1 - x0) / 2, (y1 - y0) / 2, (z1 - z0) / 2]) * MM
    return (f'<geom name="{name}" type="box" pos="{_f(*c)}" size="{_f(*h)}" rgba="{rgba}" contype="{ct}" conaffinity="{ca}" '
            f'friction="{fr} 0.005 0.0001" group="{group}"/>')


def cone_facets(name, cx, cy, apex_z, s0, s1, rgba, ct, ca, rel=np.zeros(3), n=8, th=0.6, fr=MU_PETG):
    """A 90 deg seat cone opening upward (+z) as n planar facets (boxes whose top faces lie on the cone)."""
    out = []
    sm = 0.5 * (s0 + s1)
    L = (s1 - s0) * math.sqrt(2)
    w = 2 * s1 * math.tan(math.pi / n) + 0.4
    for k in range(n):
        ph = 2 * math.pi * k / n
        c, s = math.cos(ph), math.sin(ph)
        nrm = np.array([-c, -s, 1.0]) / math.sqrt(2)
        xl = np.array([c, s, 1.0]) / math.sqrt(2)
        yl = np.array([-s, c, 0.0])
        p = np.array([cx + sm * c, cy + sm * s, apex_z + sm]) - nrm * th / 2
        p = (p - rel) * MM
        out.append(f'<geom name="{name}{k}" type="box" pos="{_f(*p)}" size="{_f(L / 2 * MM, w / 2 * MM, th / 2 * MM)}" '
                   f'xyaxes="{_f(*xl, *yl)}" rgba="{rgba}" contype="{ct}" conaffinity="{ca}" friction="{fr} 0.005 0.0001"/>')
    return "\n".join(out)


def build(off_mm=0.0, powder_g=50.0):
    global ROD_BACK
    u = (PIN_D - np.array([0, 0, PARK_DROP]) - B_PIN)
    u /= np.linalg.norm(u)
    # the EC's frame inside the tilted p16 body: rotate back to upright (zaxis of the world z expressed in the p16 frame)
    zx = np.array([0, 0, 1.0])
    ang = math.atan2(u[0], u[2])
    ROD_BACK = np.array([-math.sin(ang), 0.0, math.cos(ang)])
    m_mod = M_MOD0 + powder_g / 1000
    com_mod = (COM_MOD0 * M_MOD0 + np.array([125.0, 0, -4.0]) * powder_g / 1000) / m_mod
    rel = PIN_D                                   # EC geoms relative to its pin (docked coordinates)
    park = np.array([0, 0, -PARK_DROP])           # cradle = docked coordinates shifted down
    ec = []
    # dock cone A (EC), opening up; contact circle for the seated ball
    c_contact = ZB - R_B * math.cos(math.radians(45))
    apex = c_contact - R_B * math.sin(math.radians(45))
    top = KC_SEAT_TOP
    r_mouth = top - apex
    ec.append(cone_facets("econe", KC_A[0], KC_A[1], apex, 0.4, r_mouth, "0.95 0.6 0.15 1", 1, 2, rel))
    ax, ay = KC_A
    ec += [box("eA_l", ax - 6, ax - r_mouth, 14.6, 22.8, top - 1, top, "0.2 0.45 0.95 1", 1, 2, rel),
           box("eA_r", ax + r_mouth, ax + 6, 14.6, 22.8, top - 1, top, "0.2 0.45 0.95 1", 1, 2, rel),
           box("eA_f", ax - r_mouth, ax + r_mouth, 14.6, ay - r_mouth, top - 1, top, "0.2 0.45 0.95 1", 1, 2, rel),
           box("eA_b", ax - r_mouth, ax + r_mouth, ay + r_mouth, 22.8, top - 1, top, "0.2 0.45 0.95 1", 1, 2, rel)]
    bx, by = KC_B
    zd = ZB - H_VEE
    for j, sx in enumerate((-1, 1)):
        p0 = (np.array([bx + sx * VEE_SPACING / 2, by - 4.0, zd]) - rel) * MM
        p1 = (np.array([bx + sx * VEE_SPACING / 2, by + 4.0, zd]) - rel) * MM
        ec.append(f'<geom name="edowel{j}" type="capsule" fromto="{_f(*p0, *p1)}" size="{VEE_DOWEL_D / 2 * MM}" rgba="0.7 0.7 0.72 1" '
                  f'contype="1" conaffinity="2" friction="{MU_STEEL} 0.005 0.0001"/>')
    ec += [box("eB_l", bx - 6, bx - VEE_SPACING / 2 + 0.2, -22.8, -14.6, top - 1, top - 0.8, "0.2 0.45 0.95 1", 1, 2, rel),
           box("eB_r", bx + VEE_SPACING / 2 - 0.2, bx + 6, -22.8, -14.6, top - 1, top - 0.8, "0.2 0.45 0.95 1", 1, 2, rel)]
    cb = (np.array([KC_C[0], KC_C[1], -20.0 - R_B]) - rel) * MM
    ec.append(f'<geom name="eballC" type="sphere" pos="{_f(*cb)}" size="{R_B * MM}" rgba="0.75 0.75 0.78 1" contype="1" conaffinity="2" '
              f'friction="{MU_STEEL} 0.005 0.0001"/>')
    ec.append(box("ecoil", 90, 110, -10, 10, -21.15, -20.15, "0.75 0.15 0.12 1", 1, 2, rel, fr=MU_STEEL))
    ec.append(box("efinger", FINGER_X[0], FINGER_X[1], DOOR_ROD_Y - 2, DOOR_ROD_Y + 2, -25.1, DOOR_ROD_BOTTOM + DOOR_TRAVEL, "0.95 0.6 0.15 1", 1, 2, rel))
    # body in the guide and its base balls
    ec.append(box("ebody", 2.3, 73.3, -15.0, 15.0, EC_BASE_Z - EC_BASE_T + DOCK_RISE_V3, -21.6, "0.2 0.45 0.95 0.9", 4, 8, rel))
    zbb = EC_BASE_Z - EC_BASE_T + 2.6 - R_B + DOCK_RISE_V3
    for j, (x, y) in enumerate(EC_BALLS):
        p = (np.array([x, y, zbb]) - rel) * MM
        ec.append(f'<geom name="ebase{j}" type="sphere" pos="{_f(*p)}" size="{R_B * MM}" rgba="0.75 0.75 0.78 1" contype="4" conaffinity="8" '
                  f'friction="{MU_STEEL} 0.005 0.0001"/>')
    # visual only: NEMA 11, pinion, solenoid
    ec.append(box("v_nema", 40, 73, -14, 14, -48, -22, "0.15 0.15 0.17 1", 0, 0, rel, group=1))
    ec.append(box("v_bracket", 76, 119, -12, 12, -38, -21.5, "0.2 0.45 0.95 1", 0, 0, rel, group=1))
    pc = (np.array([GEAR_X + 5.0, 0, -32.25]) - rel) * MM
    ec.append(f'<geom name="v_pinion" type="cylinder" pos="{_f(*pc)}" size="{10 * MM} {3 * MM}" zaxis="1 0 0" rgba="0.7 0.7 0.72 1" contype="0" conaffinity="0" group="1"/>')
    ec_xml = "\n          ".join(ec)

    cr = []
    zf = -48.6 + 0.0                                # walls' tops, docked coordinates shifted with the park
    wt = -29.5 + DOCK_RISE_V3 - PARK_DROP           # = -48.6
    fl = EC_BASE_Z - EC_BASE_T + 2.6 - R_B - 1.0 - 6.0 + DOCK_RISE_V3 - PARK_DROP
    xf = 2.3 - GUIDE_CLEAR
    yw = 15.0 + GUIDE_CLEAR + EY_FREE[0]
    for sy in (-1, 1):
        y0, y1 = (yw, yw + GUIDE_WALL_T) if sy > 0 else (-yw - GUIDE_WALL_T, -yw)
        cr.append(box(f"wall{sy}a", xf - GUIDE_WALL_T, 23.5, y0, y1, fl, wt, "0.95 0.6 0.15 0.45", 8, 4))
        cr.append(box(f"wall{sy}b", 39.4, 74.3, y0, y1, fl, wt, "0.95 0.6 0.15 0.45", 8, 4))
    cr.append(box("wallf", xf - GUIDE_WALL_T, xf, -yw - GUIDE_WALL_T, yw + GUIDE_WALL_T, fl, wt, "0.95 0.6 0.15 0.45", 8, 4))
    zball_p = zbb - PARK_DROP
    ap = zball_p - KC_BALL_D * math.cos(math.radians(45))
    (x1, y1), (x2, y2), (x3, y3) = EC_BALLS
    cr.append(cone_facets("scone", x1, y1, ap, 0.3, 4.0, "0.95 0.6 0.15 1", 8, 4))
    for j, sx in enumerate((-1, 1)):
        p0 = np.array([x2 + sx * VEE_SPACING / 2, y2 - 4.0, zball_p - H_VEE]) * MM
        p1 = np.array([x2 + sx * VEE_SPACING / 2, y2 + 4.0, zball_p - H_VEE]) * MM
        cr.append(f'<geom name="sdowel{j}" type="capsule" fromto="{_f(*p0, *p1)}" size="{VEE_DOWEL_D / 2 * MM}" rgba="0.7 0.7 0.72 1" '
                  f'contype="8" conaffinity="4" friction="{MU_STEEL} 0.005 0.0001"/>')
    cr.append(box("sflat", x3 - 4, x3 + 4, y3 - 4, y3 + 4, zball_p - R_B - 1.0, zball_p - R_B, "0.7 0.7 0.72 1", 8, 4, fr=MU_STEEL))
    cr.append(box("floor", xf - GUIDE_WALL_T, 77.3, -yw - GUIDE_WALL_T, yw + GUIDE_WALL_T, fl - 0.1, fl, "0.95 0.6 0.15 0.45", 0, 0))
    cradle_xml = "\n    ".join(cr)

    # module geoms (Sam frame, the module body's frame = Sam's)
    mod = [f'<geom name="ballA" type="sphere" pos="{_f(KC_A[0] * MM, KC_A[1] * MM, ZB * MM)}" size="{R_B * MM}" rgba="0.8 0.8 0.82 1" contype="2" conaffinity="1" friction="{MU_STEEL} 0.005 0.0001"/>',
           f'<geom name="ballB" type="sphere" pos="{_f(KC_B[0] * MM, KC_B[1] * MM, ZB * MM)}" size="{R_B * MM}" rgba="0.8 0.8 0.82 1" contype="2" conaffinity="1" friction="{MU_STEEL} 0.005 0.0001"/>',
           box("armature", ARMATURE_X3[0], ARMATURE_X3[1], -ARMATURE_HW3, ARMATURE_HW3, -20.0, -18.0, "0.6 0.6 0.62 1", 2, 1, fr=MU_STEEL),
           box("plate", 3.0, 122.0, -25.0, 25.0, -18.0, -13.0, "0.1 0.25 0.85 0.55", 0, 0),
           f'<geom name="v_tube" type="cylinder" fromto="{_f(0.4 * MM, 0, 0, 225 * MM, 0, 0)}" size="{6.35 * MM}" rgba="0.85 0.85 0.8 0.9" contype="0" conaffinity="0" group="1"/>',
           f'<geom name="v_gear" type="cylinder" fromto="{_f(75.4 * MM, 0, 0, 81.4 * MM, 0, 0)}" size="{23 * MM}" rgba="0.95 0.95 0.95 0.9" contype="0" conaffinity="0" group="1"/>',
           f'<geom name="v_cap" type="cylinder" fromto="{_f(225 * MM, 0, 0, 252 * MM, 0, 0)}" size="{14.5 * MM}" rgba="0.3 0.3 0.32 1" contype="0" conaffinity="0" group="1"/>']
    mod_xml = "\n        ".join(mod)
    door_xml = "\n          ".join([
        box("shutter", -1.4, 0.1, -5.0, 9.0, DOOR_CLOSED_Z[0], DOOR_CLOSED_Z[1], "0.95 0.85 0.2 1", 0, 0),
        box("strip", -1.4 - STRIP_FOOT[0], 0.1, DOOR_ROD_Y - DOOR_ROD_D / 2, DOOR_ROD_Y + DOOR_ROD_D / 2, DOOR_ROD_BOTTOM, DOOR_ROD_BOTTOM + 3.0, "0.95 0.85 0.2 1", 2, 1),
        box("strip_up", -1.4, 0.1, DOOR_ROD_Y - DOOR_ROD_D / 2, DOOR_ROD_Y + DOOR_ROD_D / 2, DOOR_ROD_BOTTOM + 3.0, DOOR_CLOSED_Z[0], "0.95 0.85 0.2 1", 0, 0)])
    car_xml = "\n      ".join([
        box("car_f", -33, -6, -33, 33, -23, -18, "0.55 0.55 0.6 0.5", 0, 0),
        box("car_b", WIN_BACK_V3, 272, -33, 33, -23, -18, "0.55 0.55 0.6 0.5", 0, 0),
        box("car_l", -6, WIN_BACK_V3, 27, 33, -23, -18, "0.55 0.55 0.6 0.5", 0, 0),
        box("car_r", -6, WIN_BACK_V3, -33, -27, -23, -18, "0.55 0.55 0.6 0.5", 0, 0)])
    if SWING["preload"] > 0:
        SWING_XML = (f'range="0 60" limited="true" solreflimit="0.0005 1" stiffness="{SWING["k"]}" '
                     f'springref="{-math.degrees(SWING["preload"] / SWING["k"])}"')
    else:
        SWING_XML = ""
    I_ec = (M_EC / 12 * (0.036 ** 2 + 0.045 ** 2), M_EC / 12 * (0.07 ** 2 + 0.045 ** 2), M_EC / 12 * (0.07 ** 2 + 0.036 ** 2))
    W0 = (0.1 + m_mod) * G
    xml = f"""<mujoco model="v3 station">
  <compiler angle="degree"/>
  <option timestep="{DT}" integrator="implicitfast" gravity="0 0 -{G}" cone="elliptic" impratio="3">
    <flag filterparent="disable"/>
  </option>
  <visual><global offwidth="1280" offheight="960"/><quality shadowsize="2048"/><map znear="0.01"/></visual>
  <default>
    <geom condim="3" solref="0.0004 1" solimp="0.95 0.99 0.00002"/>
  </default>
  <asset>
    <texture name="grid" type="2d" builtin="checker" rgb1="0.92 0.92 0.92" rgb2="0.85 0.85 0.85" width="256" height="256"/>
    <material name="grid" texture="grid" texrepeat="8 8"/>
  </asset>
  <worldbody>
    <light pos="0.1 -0.4 0.3" dir="-0.2 1 -0.6" diffuse="0.8 0.8 0.8"/>
    <light pos="-0.2 0.3 0.4" dir="0.4 -0.6 -0.8" diffuse="0.4 0.4 0.4"/>
    <geom name="bench" type="plane" pos="0 0 {-0.300}" size="0.4 0.4 0.01" material="grid" contype="0" conaffinity="0"/>
    {cradle_xml}
    <body name="car" pos="0 0 0">
      <joint name="car_y" type="slide" axis="0 1 0" stiffness="{K_RUN}" springref="{off_mm * MM}" damping="8"/>
      <joint name="car_z" type="slide" axis="0 0 1" stiffness="{K_UP}" springref="{W0 / K_UP}" damping="8" range="-0.004 0.002" limited="true" solreflimit="0.0005 1"/>
      <inertial pos="0.12 0 -0.02" mass="0.1" diaginertia="0.0009 0.0003 0.0009"/>
      {car_xml}
      <body name="mod" pos="0 0 0">
        <joint name="tilt" type="hinge" axis="0 -1 0" range="0 100" limited="true" damping="0.002" solreflimit="0.0005 1"/>
        <inertial pos="{_f(*(com_mod * MM))}" mass="{m_mod}" diaginertia="{_f(m_mod * 0.0125 ** 2 / 2 + 2e-5, m_mod * 0.25 ** 2 / 12 + 4e-5, m_mod * 0.25 ** 2 / 12 + 4e-5)}"/>
        {mod_xml}
        <body name="door" pos="0 0 0">
          <joint name="door" type="slide" axis="0 0 1" range="0 {DOOR_TRAVEL * MM + 0.0005}" limited="true" solreflimit="0.0005 1" stiffness="{DOOR_SPRING[2] * 1000}" springref="{-(DOOR_SPRING[1] - DOOR_SPRING_SHUT) * MM}" damping="0.05"/>
          <inertial pos="0 {DOOR_ROD_Y * MM} {-0.006}" mass="0.002" diaginertia="1e-7 1e-7 1e-7"/>
          {door_xml}
        </body>
      </body>
    </body>
    <body name="p16" pos="{_f(*(B_PIN * MM))}" zaxis="{_f(*((PIN_D - np.array([0, 0, PARK_DROP]) - B_PIN) / np.linalg.norm(PIN_D - np.array([0, 0, PARK_DROP]) - B_PIN)))}">
      <joint name="swing" type="hinge" axis="0 1 0" damping="0.0005" {SWING_XML}/>
      <inertial pos="0 0 0.09" mass="0.1" diaginertia="0.0003 0.0003 0.00001"/>
      <geom name="v_p16" type="box" pos="0 0 {0.09}" size="0.011 0.012 0.09" rgba="0.25 0.25 0.28 1" contype="0" conaffinity="0" group="1"/>
      <body name="rod" pos="0 0 0">
        <joint name="ext" type="slide" axis="0 0 1" range="-0.002 {ACT_STROKE * MM}" limited="true" solreflimit="0.0005 1" damping="30"/>
        <inertial pos="0 0 0.15" mass="0.02" diaginertia="1e-5 1e-5 1e-7"/>
        <geom name="v_rod" type="cylinder" fromto="0 0 0.17 0 0 {ACT_RETRACTED * MM}" size="0.003" rgba="0.75 0.75 0.78 1" contype="0" conaffinity="0" group="1"/>
        <body name="ec" pos="0 0 {ACT_RETRACTED * MM}" zaxis="{_f(*ROD_BACK)}">
          <joint name="slot" type="slide" axis="0 0 1" range="-0.001 0.001" limited="true" solreflimit="0.0005 1" damping="0.5"/>
          <joint name="ey" type="slide" axis="0 1 0" range="{-(1.0 + EY_FREE[0]) * MM} {(1.0 + EY_FREE[0]) * MM}" limited="true" solreflimit="0.0005 1" damping="0.5"/>
          <joint name="pitch" type="hinge" axis="0 1 0" damping="0.0005"/>
          <inertial pos="{_f(*((COM_EC - PIN_D) * MM))}" mass="{M_EC}" diaginertia="{_f(*I_ec)}"/>
          {ec_xml}
        </body>
      </body>
    </body>
  </worldbody>
  <actuator>
    <general name="p16" joint="ext" gainprm="30000" biastype="affine" biasprm="0 -30000 -300" forcelimited="true" forcerange="-50 50"/>
  </actuator>
</mujoco>"""
    return xml


class Station:
    def __init__(self, off_mm=0.0, powder_g=50.0):
        self.m = mujoco.MjModel.from_xml_string(build(off_mm, powder_g))
        self.d = mujoco.MjData(self.m)
        m = self.m
        self.b = {n: m.body(n).id for n in ("car", "mod", "door", "ec", "rod", "p16")}
        self.j = {n: m.joint(n).qposadr[0] for n in ("car_y", "car_z", "tilt", "door", "ext", "slot", "ey", "pitch", "swing")}
        self.coil = False
        self.F_sep = self.F_t = 0.0
        self.gid = {m.geom(i).name: i for i in range(m.ngeom)}
        self.groups = {
            "A": {self.gid[f"econe{k}"] for k in range(8)} | {self.gid[n] for n in ("eA_l", "eA_r", "eA_f", "eA_b")},
            "B": {self.gid["edowel0"], self.gid["edowel1"], self.gid["eB_l"], self.gid["eB_r"]},
            "C": {self.gid["eballC"]},
            "coil": {self.gid["ecoil"]},
            "finger": {self.gid["efinger"]},
            "walls": {self.gid[n] for n in ("wall-1a", "wall-1b", "wall1a", "wall1b", "wallf")},
            "seat": {self.gid[f"scone{k}"] for k in range(8)} | {self.gid[n] for n in ("sdowel0", "sdowel1", "sflat")},
        }
        mujoco.mj_forward(m, self.d)
        self.mags = dict(A=0.0, B=0.0, coil=0.0, coil_gap=99.0)

    def pt(self, body, p_local_mm):
        d = self.d
        return d.xpos[self.b[body]] + d.xmat[self.b[body]].reshape(3, 3) @ (np.asarray(p_local_mm) * MM)

    def _force(self, body, p, f):
        d = self.d
        c = d.xipos[self.b[body]]
        d.xfrc_applied[self.b[body], :3] += f
        d.xfrc_applied[self.b[body], 3:] += np.cross(p - c, f)

    def apply(self):
        d = self.d
        d.xfrc_applied[:] = 0
        for name, ball, face in (("A", (KC_A[0], KC_A[1], ZB), (KC_A[0], KC_A[1], ZB - R_B - KC_MAG_GAP)),
                                 ("B", (KC_B[0], KC_B[1], ZB), (KC_B[0], KC_B[1], ZB - H_VEE - VEE_DOWEL_D / 2 - 0.6))):
            pb = self.pt("mod", ball)
            pf = self.pt("ec", np.array(face) - PIN_D)
            v = pf - pb
            dist = np.linalg.norm(v)
            gap = dist / MM - R_B
            F = seat_pull(gap)
            self.mags[name] = F
            if F > 0:
                u = v / dist
                self._force("mod", pb, F * u)
                self._force("ec", pf, -F * u)
        Rm = d.xmat[self.b["mod"]].reshape(3, 3)
        pc = self.pt("ec", np.array([DOCK_MAG_XY3[0], 0, -20.15]) - PIN_D)
        local = Rm.T @ (pc - d.xpos[self.b["mod"]]) / MM
        gap = -20.0 - local[2]
        self.mags["coil_gap"] = gap
        F = K.em_pull(gap) if (self.coil and gap < 8.0) else 0.0
        self.mags["coil"] = F
        if F > 0:
            n = Rm[:, 2]
            self._force("mod", self.pt("mod", (local[0], local[1], -20.0)), -F * n)
            self._force("ec", pc, F * n)
        if self.F_sep or self.F_t:
            pm = self.pt("mod", (GEAR_X + 5.0, 0, -22.0))
            f = -self.F_sep * Rm[:, 2] + self.F_t * Rm[:, 1]
            self._force("ec", pm, f)
            self._force("mod", pm, -f)

    def step(self, ext_mm):
        self.d.ctrl[0] = ext_mm * MM
        self.apply()
        mujoco.mj_step(self.m, self.d)

    def contact_sum(self, group):
        f6 = np.zeros(6)
        tot = np.zeros(3)
        gs = self.groups[group]
        for i in range(self.d.ncon):
            c = self.d.contact[i]
            if c.geom1 in gs or c.geom2 in gs:
                mujoco.mj_contactForce(self.m, self.d, i, f6)
                tot += c.frame.reshape(3, 3).T @ f6[:3]
        return float(np.linalg.norm(tot))

    def dock_error(self):
        """EC pose in the module frame against the seated pose: pin position error (mm) and rotation (deg)."""
        d = self.d
        Rm = d.xmat[self.b["mod"]].reshape(3, 3)
        Re = d.xmat[self.b["ec"]].reshape(3, 3)
        p = Rm.T @ (d.xpos[self.b["ec"]] - d.xpos[self.b["mod"]]) / MM
        Rr = Rm.T @ Re
        ang = math.degrees(math.acos(max(-1.0, min(1.0, (np.trace(Rr) - 1) / 2))))
        return p - PIN_D, ang

    def row(self, t, cmd):
        d, j = self.d, self.j
        e, ang = self.dock_error()
        return dict(t=round(t, 4), cmd=cmd, ext=d.qpos[j["ext"]] / MM, F_act=float(d.actuator_force[0]),
                    car_y=d.qpos[j["car_y"]] / MM, car_z=d.qpos[j["car_z"]] / MM, tilt=math.degrees(d.qpos[j["tilt"]]),
                    door=d.qpos[j["door"]] / MM, slot=d.qpos[j["slot"]] / MM, ey=d.qpos[j["ey"]] / MM,
                    pitch=math.degrees(d.qpos[j["pitch"]]), dx=e[0], dy=e[1], dz=e[2], dang=ang,
                    fA=self.contact_sum("A"), fB=self.contact_sum("B"), fC=self.contact_sum("C"), fcoil=self.contact_sum("coil"),
                    ffinger=self.contact_sum("finger"), fwalls=self.contact_sum("walls"), fseat=self.contact_sum("seat"),
                    magA=self.mags["A"], magB=self.mags["B"], coil=self.mags["coil"], coil_gap=self.mags["coil_gap"])


def ext_for_tilt(tilt):
    th = math.radians(tilt)
    R = np.array([[math.cos(th), 0, -math.sin(th)], [0, 1, 0], [math.sin(th), 0, math.cos(th)]])
    P = R @ PIN_D
    return np.linalg.norm(P - B_PIN) - ACT_RETRACTED


def run(off_mm=0.0, mode="capture", v=18.0, tilt=30.0, record_every=0.01, frames=None, fps=30):
    st = Station(off_mm)
    T = {}
    T["rise0"] = 0.3
    T["rise1"] = T["rise0"] + (PARK_DROP + 1.0) / v
    T["coil"] = T["rise1"] - 3.0 / v
    T["float"] = T["rise1"] + 0.3
    T["seat_end"] = T["float"] + 0.4
    e_t = ext_for_tilt(tilt) + 1.0
    if mode == "capture":
        T["end"] = T["seat_end"]
    else:
        T["tilt0"] = T["seat_end"]
        T["tilt1"] = T["tilt0"] + (e_t - PARK_DROP - 1.0) / v
        T["dose0"] = T["tilt1"] + 0.3
        T["dose1"] = T["dose0"] + 1.0
        T["back0"] = T["dose1"] + 0.2
        T["back1"] = T["back0"] + (e_t - PARK_DROP - 1.0) / v
        T["float2"] = T["back1"] + 0.3
        T["coiloff"] = T["float2"] + 0.2
        T["down0"] = T["coiloff"] + 0.2
        T["down1"] = T["down0"] + (PARK_DROP + 1.0) / v
        T["end"] = T["down1"] + 0.5

    def cmd(t):
        if t < T["rise0"]:
            return 0.0
        if t < T["rise1"]:
            return min(PARK_DROP + 1.0, (t - T["rise0"]) * v)
        if mode == "capture" or t < T.get("tilt0", 1e9):
            return PARK_DROP if t >= T["float"] else PARK_DROP + 1.0
        if t < T["tilt1"]:
            return PARK_DROP + 1.0 + (t - T["tilt0"]) * v
        if t < T["back0"]:
            return e_t
        if t < T["back1"]:
            return max(PARK_DROP + 1.0, e_t - (t - T["back0"]) * v)
        if t < T["down0"]:
            return PARK_DROP
        if t < T["down1"]:
            return max(-1.0, PARK_DROP - (t - T["down0"]) * v)
        return -1.0 if t < T["end"] - 0.2 else 0.0

    rows, imgs = [], []
    n = int(T["end"] / DT)
    every = max(1, int(round(record_every / DT)))
    fevery = max(1, int(round(1.0 / fps / DT)))
    for i in range(n):
        t = i * DT
        st.coil = (T["coil"] <= t < T.get("coiloff", 1e9))
        if mode != "capture" and T["dose0"] <= t < T["dose1"]:
            st.F_t = 0.03 / 0.022
            st.F_sep = st.F_t * SEP_RATIO_STEEL
        else:
            st.F_t = st.F_sep = 0.0
        c = cmd(t)
        st.step(c)
        if i % every == 0:
            rows.append(st.row(t, c))
        if frames is not None and i % fevery == 0:
            frames(st, t)
    return st, rows, T


def summarize(rows, T, off):
    seat = [r for r in rows if T["float"] + 0.2 <= r["t"] < T["seat_end"]]
    rise = [r for r in rows if r["t"] < T["float"]]
    last = seat[-1]
    seated = abs(last["dx"]) < 0.1 and abs(last["dy"]) < 0.1 and abs(last["dz"]) < 0.1 and last["dang"] < 0.2
    return dict(off_mm=off, seated=bool(seated), dock_error_mm=[round(last["dx"], 3), round(last["dy"], 3), round(last["dz"], 3)],
                dock_error_deg=round(last["dang"], 3),
                F_act_peak_N=round(max(abs(r["F_act"]) for r in rise), 2),
                carriage_pulled_back_mm=round(off - last["car_y"], 3), carriage_y_end_mm=round(last["car_y"], 3),
                module_lift_peak_deg=round(max(r["tilt"] for r in rise), 3),
                contact_A_N=round(last["fA"], 2), contact_B_N=round(last["fB"], 2), contact_C_N=round(last["fC"], 2),
                coil_face_N=round(last["fcoil"], 2), seat_pulls_N=[round(last["magA"], 2), round(last["magB"], 2)],
                coil_N=round(last["coil"], 2), coil_gap_mm=round(last["coil_gap"], 3),
                wall_force_peak_N=round(max(r["fwalls"] for r in rise), 2), door_open_mm=round(last["door"], 2),
                finger_force_N=round(last["ffinger"], 3), ec_lean_deg=round(min(r["pitch"] for r in rise), 3))


def plot_capture(results, path, tag=""):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(4, 1, figsize=(9, 10), sharex=True)
    cols = ["#1f5fbf", "#2a9d5c", "#d0661a", "#b00020", "#6b6b6b", "#8e44ad"]
    for (off, rows, T), col in zip(results, cols):
        t = [r["t"] for r in rows]
        ax[0].plot(t, [r["F_act"] for r in rows], color=col, label=f"{off} mm off index")
        ax[1].plot(t, [r["car_y"] for r in rows], color=col)
        ax[2].plot(t, [r["tilt"] for r in rows], color=col)
        ax[3].plot(t, [math.sqrt(r["dx"] ** 2 + r["dy"] ** 2 + r["dz"] ** 2) for r in rows], color=col)
    ax[0].set_ylabel("P16 force (N)")
    ax[1].set_ylabel("carriage along the run (mm)")
    ax[2].set_ylabel("module lifted (deg)")
    ax[3].set_ylabel("EC off its seated pose (mm)")
    ax[3].set_yscale("log")
    ax[3].set_xlabel("s")
    T = results[0][2]
    for a in ax:
        for k in ("coil", "rise1", "float"):
            a.axvline(T[k], color="k", lw=0.6, alpha=0.4)
        a.grid(alpha=0.3)
    ax[0].legend(fontsize=8)
    ax[0].set_title(f"v3 capture ({tag or 'as drawn'}): the EC rises 20 mm in its guide into the plate's balls (coil on for the last 3 mm)", fontsize=9)
    fig.tight_layout()
    fig.savefig(path, dpi=110)
    plt.close(fig)


def plot_cycle(rows, T, path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(4, 1, figsize=(9, 10), sharex=True)
    t = [r["t"] for r in rows]
    ax[0].plot(t, [r["tilt"] for r in rows], label="module tilt (deg)")
    ax[0].plot(t, [r["ext"] for r in rows], label="P16 extension (mm)")
    ax[0].plot(t, [r["door"] * 5 for r in rows], label="door opening x 5 (mm)")
    ax[1].plot(t, [r["F_act"] for r in rows], label="P16 force (N)")
    ax[1].plot(t, [r["fwalls"] for r in rows], label="guide walls (N)")
    ax[2].plot(t, [r["fA"] for r in rows], label="cone A (N)")
    ax[2].plot(t, [r["fB"] for r in rows], label="vee B (N)")
    ax[2].plot(t, [r["fC"] for r in rows], label="flat C (N)")
    ax[2].plot(t, [r["fseat"] for r in rows], label="cradle seat (N)")
    ax[3].plot(t, [math.sqrt(r["dx"] ** 2 + r["dy"] ** 2 + r["dz"] ** 2) for r in rows], label="EC off its seated pose (mm)")
    ax[3].set_yscale("log")
    for a in ax:
        for k in ("rise1", "tilt0", "dose0", "back0", "coiloff", "down0"):
            a.axvline(T[k], color="k", lw=0.6, alpha=0.4)
        a.grid(alpha=0.3)
        a.legend(fontsize=8, loc="upper right")
    ax[3].set_xlabel("s")
    ax[0].set_title("v3 station cycle: rise, seat, tilt to 30 deg, dose, back, coil off, undock (carriage 1 mm off index)", fontsize=10)
    fig.tight_layout()
    fig.savefig(path, dpi=110)
    plt.close(fig)


def video(off=1.0, tilt=30.0):
    import imageio.v2 as imageio
    from PIL import Image, ImageDraw
    W, H = 960, 720
    holder = {}
    frames_out = []

    def grab(st, t):
        if "r" not in holder:
            holder["r"] = mujoco.Renderer(st.m, H, W)
            cam = mujoco.MjvCamera()
            cam.type = mujoco.mjtCamera.mjCAMERA_FREE
            cam.lookat[:] = [0.055, 0.0, -0.045]
            cam.distance = 0.30
            cam.azimuth = -62
            cam.elevation = -12
            holder["cam"] = cam
            opt = mujoco.MjvOption()
            opt.geomgroup[:] = 1
            holder["opt"] = opt
        r = holder["r"]
        r.update_scene(st.d, camera=holder["cam"], scene_option=holder["opt"])
        img = Image.fromarray(r.render())
        dr = ImageDraw.Draw(img)
        rw = st.row(t, 0)
        txt = (f"t {t:4.2f} s   P16 {rw['ext']:5.1f} mm  {rw['F_act']:5.1f} N   tilt {rw['tilt']:4.1f} deg   door {rw['door']:3.1f} mm   "
               f"coil {'on ' if st.coil else 'off'}   carriage {rw['car_y']:+.2f} mm")
        dr.rectangle([0, 0, W, 26], fill=(255, 255, 255))
        dr.text((8, 7), "v3 station (MuJoCo): rise in the guide, capture, seat, tilt, dose, undock.  " + txt, fill=(0, 0, 0))
        frames_out.append(np.asarray(img))

    st, rows, T = run(off, mode="cycle", tilt=tilt, frames=grab, fps=25)
    OUT.mkdir(exist_ok=True)
    mp4 = OUT / "station_v3_cycle.mp4"
    imageio.mimwrite(mp4, frames_out, fps=25, quality=7, macro_block_size=8)
    small = [np.asarray(Image.fromarray(f).resize((640, 480), Image.LANCZOS)) for f in frames_out[::3]]
    imageio.mimwrite(OUT / "station_v3_cycle.gif", small, duration=0.12, loop=0)
    return mp4


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("what", choices=["capture", "cycle", "video"])
    ap.add_argument("--off", type=float, default=1.0)
    ap.add_argument("--offs", type=str, default="0,1,2,3")
    ap.add_argument("--base-dx", type=float, default=0.0)
    ap.add_argument("--tag", type=str, default="")
    ap.add_argument("--swing-preload", type=float, default=0.0)
    ap.add_argument("--finger-fix", action="store_true")
    ap.add_argument("--ey-free", type=float, default=0.0)
    a = ap.parse_args()
    set_base_dx(a.base_dx)
    SWING["preload"] = a.swing_preload
    EY_FREE[0] = a.ey_free
    if a.finger_fix:
        FINGER_X[:] = [-3.6, 0.0]
        STRIP_FOOT[0] = 1.5
    OUT.mkdir(exist_ok=True)
    resf = OUT / f"station_mj{('_' + a.tag) if a.tag else ''}.json"
    res = json.loads(resf.read_text()) if resf.exists() else {}
    if a.what == "capture":
        allr, summ = [], []
        for off in [float(x) for x in a.offs.split(",")]:
            st, rows, T = run(off, mode="capture")
            s = summarize(rows, T, off)
            print(json.dumps(s), flush=True)
            summ.append(s)
            allr.append((off, rows, T))
        res["capture"] = summ
        res["settings"] = dict(base_dx=a.base_dx, swing_preload_Nm=a.swing_preload, finger_fix=a.finger_fix, ey_free_mm=a.ey_free)
        plot_capture(allr, OUT / f"capture{('_' + a.tag) if a.tag else ''}.png", a.tag)
    elif a.what == "cycle":
        st, rows, T = run(a.off, mode="cycle")
        s = summarize(rows, {**T, "seat_end": T["seat_end"]}, a.off)
        dose = [r for r in rows if T["dose0"] <= r["t"] < T["dose1"]]
        undock = [r for r in rows if T["down0"] <= r["t"]]
        s.update(tilt_reached=round(max(r["tilt"] for r in rows), 2),
                 F_act_peak_cycle_N=round(max(abs(r["F_act"]) for r in rows), 2),
                 F_act_pull_off_N=round(min(r["F_act"] for r in undock), 2),
                 dock_error_dose_max_mm=round(max(math.sqrt(r["dx"] ** 2 + r["dy"] ** 2 + r["dz"] ** 2) for r in dose), 4),
                 door_open_during_tilt_min_mm=round(min(r["door"] for r in rows if T["tilt0"] <= r["t"] < T["back1"]), 2),
                 door_shut_at_ext_mm=round(next((r["ext"] for r in undock if r["door"] < 0.05), float("nan")), 2),
                 balls_leave_at_ext_mm=round(next((r["ext"] for r in undock if math.sqrt(r["dx"] ** 2 + r["dy"] ** 2 + r["dz"] ** 2) > 0.2), float("nan")), 2),
                 parked_on_seat_end=bool(rows[-1]["fseat"] > 1.0), seat_force_end_N=round(rows[-1]["fseat"], 2),
                 module_back_down_deg=round(rows[-1]["tilt"], 3))
        print(json.dumps(s), flush=True)
        res["cycle"] = s
        res["cycle_T"] = T
        res["settings"] = dict(base_dx=a.base_dx, swing_preload_Nm=a.swing_preload, finger_fix=a.finger_fix, ey_free_mm=a.ey_free)
        plot_cycle(rows, T, OUT / f"cycle{('_' + a.tag) if a.tag else ''}.png")
    else:
        print(video(a.off))
    resf.write_text(json.dumps(res, indent=1) + "\n")


if __name__ == "__main__":
    main()
