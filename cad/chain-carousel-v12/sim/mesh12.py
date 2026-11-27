"""v12 station dynamics with real tooth contact (MuJoCo): the spring-loaded pinion v12 is built round.

Sterling (PR #185, 2026-11-27): "Go with the spring-loaded pinion. Make v12 from v11 with what your last report proposed: the NEMA 11
and its pinion on a cradle that pivots in the EC, with a spring pressing the pinion into the gear (about 1 N/mm and 6 N preload) and a
set-screw stop; a hall switch on the cradle ...; the slow seek after each index (turn the pinion slowly, reversing once), with a second
try when the switch still reads 'lifted'; a second seat for the EC on the far side of the module ... Then redo every check for v12: the
MuJoCo entry, hold, exit and robustness runs, against the same tolerance stack; the stall torque with the preloaded mesh, against what
the auger needs".

This is v11's model (mesh11.py, kept in ../../chain-carousel-v11/sim) with the pinion on v12's cradle instead of v11's rigid mount or
its proposed slide:
  cradle  the NEMA 11, the 24T pinion and the printed cradle (224 g), hinged in the EC about x on the pivot dowels, 18.5 mm to the side
          the gears arrive from (Sam -y) at the pinion's level; a torsional spring equal to v12's 1 N/mm spring at the pinion, 6 N at
          the set screw's stop 0.4 mm past tight mesh (the joint's upper limit); the roof's pad 3.2 mm over tight mesh (its lower limit)
  hall    the switch on the cradle reads "lifted" when the pinion is more than 0.8 mm over the pivot's level (tight mesh as drawn)
  seats   the EC's two guide shoes in two 90 deg seats, one each side of the module (v11: one)
and the driver's v12 seek after every index: the pinion turned 0.25 rev/s forward for 0.2 s and back for 0.2 s with the driver on; if the
switch still reads "lifted", a second try the other way round. The tolerance stack a_err places the EC (its pivot and stop) a_err mm
farther from the gear than drawn (the set screw is set once, on module 1): at +0.4 or more the cradle rests on its stop in mesh.

Everything is in the station module's Sam frame at rest (layout.sam_frame(station_frame(), 0)): x along the auger from its exit (the
hinge is the y axis through the origin), z out of the loop (world DOWN at the station), so gravity is +z here. The machine runs the
bottom run toward Sam +y, so the next module arrives from Sam -y. SI units inside MuJoCo, mm in the code's constants.

    python mesh12.py entry [--a-err 0] [--phases 12] [--k-roll 10] [--leading]
    python mesh12.py cycle [--a-err 0]
    python mesh12.py info
"""
from __future__ import annotations

import argparse
import json
import math
import sys
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path

import mujoco
import numpy as np

HERE = Path(__file__).resolve().parent
V12 = HERE.parent
V11 = V12
GM = V11.parent / "gear-mesh"
OUT = HERE / "out"
OUT.mkdir(parents=True, exist_ok=True)
sys.path.insert(0, str(GM))
import common as GC  # noqa: E402  gear-mesh study: the 44T's measured geometry, the NEMA 11, the module's mass properties
import shigley as GS  # noqa: E402  motor_torque(rev/s, V, A)

MM = 1e-3
DT = 2.0e-5
G = 9.81

# ---------------------------------------------------------------- geometry (mm, Sam frame at rest; `python mesh11.py geom` prints it)
GEO = dict(
    p16_base=(-135.0, 35.7625, -269.85),     # layout.P16_11_BASE in the station Sam frame
    p16_pin=(96.0, 35.7625, -25.0),          # params.P16_11_PIN on the EC's arm (Sam y = layout.SY_P16_11)
    p16_ext_rest=139.22,                     # layout.p16_11_ext(0): 10.8 mm short of full extension
    act_retracted=197.4,
    shoe_tip=(139.0, 36.0, -24.5),           # layout.SHOE11_TIP: the 90 deg nose's tip; the seat's apex is 0.5 further (+z). 2026-11-27: behind
                                             # the arm on its bracket (was (115, 35.76, -31), where the guide's seat block sat inside the arm)
    seat_gap=0.5,                            # params.GUIDE11_SEAT_GAP
    pinion_axis_z=-34.25,                    # params.PINION11_Z: centre distance 34.25 (44T + 24T at module 1 is 34.0)
    pinion_face=(78.3, 88.3),                # params.PINION11_X0 + 10
    gear_face=(78.4, 88.4),                  # the auger's 44T (lab STEP z 78.33-88.33 + the 0.4 mm outlet offset ... v11 draws 78.4-88.4)
    t_head_x=(52.0, 68.0), t_head_z=(-24.0, -27.0), t_stem_x=(57.0, 63.0), t_hy=8.0,
    lip_gap=0.2, slot_clear=0.3, ceiling_gap=0.5,  # params.RAIL11_LIP_GAP, RAIL11_CLEAR; parts11._t_profile11's ceiling 0.5 over the head
    rail_y=12.0,                             # RAIL11_FLAT + RAIL11_FUNNEL_L: the lips' length each side of the station
    lip_bottom=-21.0,                        # params.RAIL11_BOTTOM
    ec_bottom=-19.0, plate_top=-18.0,        # the EC's underside 1 mm over the plate's inner face
    sol_x=32.0,
    pivot=(-18.5, -34.0),                    # v12: params.CRADLE12_PIV (y, z): the cradle's dowels, level with the pinion in tight mesh
    shoe_tip2=(139.0, -32.0, -24.5),         # v12: the second shoe's nose tip (params.SHOE12_Y2), its seat 0.5 further (+z)
    lift_max=3.2,                            # v12: the roof's pad (params.CRADLE12_LIFT)
)
Z1, Z2 = 24, GC.Z2                           # pinion, gear teeth
R1, R2 = 12.0, 22.0
A0 = R1 + R2                                 # 34.0: zero-backlash centre distance for standard teeth

# masses (g, mm): printed PETG at 1.27 g/cm3 x a solid fraction, STL volumes from stl/*.stl (trimesh)
EC_PARTS_V11 = [  # (g, x, y, z)
    (45.07 * 1.27 * 0.80, 83.0, 8.0, -32.7),  # EC v11's CAD, 45.07 cm3, its centroid (2026-11-27, after the spine, bars and shoe bracket fixes)
    (180.0, 115.0, 0.0, -34.25),             # NEMA 11 11HS18-0674S (0.18 kg, SPECS.md), body x 93.5-137 on the pinion's axis
    (34.0, 83.3, 0.0, -34.25),               # 24T steel pinion, OD 26 x 10, 5 mm bore
    (35.0, 32.0, 0.0, -40.0),                # solenoid over clip 1 (Adafruit 412 class)
    (10.0, 90.0, 20.0, -30.0),               # screws, rod-end shoulder screw, nut
]
EC_PARTS = [  # v12: the EC without the cradle (g, x, y, z)
    (48.06 * 1.27 * 0.80, 88.0, 6.7, -37.4),  # EC v12's CAD, 48.06 cm3, its centroid
    (35.0, 32.0, 0.0, -40.0),                # solenoid over clip 1
    (10.0, 90.0, 20.0, -30.0),               # screws, rod-end shoulder screw, nut
    (1.5, 102.0, 30.0, -39.5),               # the hall switch's magnet, the two dowels
]
CRADLE_PARTS = [  # v12: what turns on the cradle (g, x, y, z)
    (7.71 * 1.27 * 0.80, 105.0, 0.3, -39.1),  # cradle v12's CAD, 7.71 cm3
    (180.0, 116.0, 0.0, -34.0),               # NEMA 11 11HS18-0674S, body x 93.5-138.5 on the pinion's axis
    (34.0, 83.3, 0.0, -34.0),                 # 24T steel pinion and its sleeve
    (2.0, 106.0, 22.0, -36.0),                # the stop's insert and set screw, the hall switch
]
MOD_PARTS = [  # the module without the turning auger (the plate, T, door, screws)
    (70.35 * 1.27 * 0.80, 128.2, 0.1, -13.3),   # mounting_plate_v11.stl 70.35 cm3 (Sam z = -18 + z_stl)
    (2.07 * 1.27 * 0.9, 60.0, 0.0, -23.0),      # T-bracket
    (2.5, 0.5, 0.0, -10.0),                     # outlet door: housing, shutter, rod, head
    (5.0, 100.0, 0.0, -15.0),                   # screws, inserts, hinge pins' share
]
_MP = json.loads((GM / "out" / "mass_props.json").read_text())
AUG_M = _MP["auger_rotating"]["mass_g"] / 1000            # 0.0728 kg: tube + flights + cap turn together
AUG_J = _MP["auger_rotating"]["Ix_axis_gmm2"] * 1e-9       # about its axis
AUG_X = (_MP["auger"]["mass_g"] * _MP["auger"]["com_mm"][0] + _MP["cap"]["mass_g"] * _MP["cap"]["com_mm"][0]) / (
    _MP["auger"]["mass_g"] + _MP["cap"]["mass_g"])
AUG_IYY = (_MP["auger"]["Iy_hinge_gmm2"] + _MP["cap"]["Iy_hinge_gmm2"]) * 1e-9 - AUG_M * (AUG_X * MM) ** 2
J_ROTOR = GC.J_ROTOR                                        # 9 g cm^2
J_PINION = 0.5 * 0.034 * (0.012 ** 2 + 0.0025 ** 2)


def _com(parts):
    m = sum(p[0] for p in parts)
    c = [sum(p[0] * p[i] for p in parts) / m for i in (1, 2, 3)]
    return m / 1000, c


# ---------------------------------------------------------------- teeth
def _hull(pts):
    from scipy.spatial import ConvexHull
    return pts[ConvexHull(pts).vertices]


def involute_outline(z: int, m: float = 1.0, phi=math.radians(20.0), x_thin: float = 0.0, rho=0.38) -> np.ndarray:
    """Standard involute spur outline (2D, centred), tooth thinned by x_thin (mm at the pitch circle), root fillet rho*m."""
    from shapely.geometry import Polygon
    rp = m * z / 2
    rb, ra, rf = rp * math.cos(phi), rp + m, rp - 1.25 * m
    inv = lambda a: math.tan(a) - a
    s = math.pi * m / 2 - x_thin
    psi = lambda r: s / (2 * rp) + inv(phi) - inv(math.acos(min(1.0, rb / r)))
    pitch = 2 * math.pi / z
    pts = []
    for k in range(z):
        tc = k * pitch
        r_inv = np.linspace(rb, ra, 50)
        r_rad = np.linspace(rf - 0.3, rb, 8)[:-1]
        right = [(r, tc - psi(rb)) for r in r_rad] + [(r, tc - psi(r)) for r in r_inv]
        left = [(r, tc + psi(r)) for r in r_inv[::-1]] + [(r, tc + psi(rb)) for r in r_rad[::-1]]
        tip = [(ra, a) for a in np.linspace(tc - psi(ra), tc + psi(ra), 6)[1:-1]]
        pts += [(r * math.cos(a), r * math.sin(a)) for r, a in right + tip + left]
        a0, a1 = tc + psi(rb), tc + pitch - psi(rb)
        pts += [(rf * math.cos(a), rf * math.sin(a)) for a in np.linspace(a0, a1, 10)[1:-1]]
    poly = Polygon(pts)
    disc = Polygon([(rf * math.cos(a), rf * math.sin(a)) for a in np.linspace(0, 2 * math.pi, 400)])
    poly = poly.union(disc).buffer(rho * m, join_style=1, quad_segs=16).buffer(-rho * m, join_style=1, quad_segs=16)
    return np.array(poly.exterior.coords)[:-1]


def tooth_polygon(outline: np.ndarray, z: int) -> np.ndarray:
    """Convex hull of the tooth centred on +y (2D), from its root circle up, as a prism section."""
    r = np.hypot(outline[:, 0], outline[:, 1])
    th = np.arctan2(outline[:, 1], outline[:, 0])
    pitch = 2 * math.pi / z
    tip = r > r.max() - 0.03
    c = math.atan2(np.mean(np.sin(np.mod(th[tip], pitch) * z)), np.mean(np.cos(np.mod(th[tip], pitch) * z))) / z
    th2 = np.mod(th + (math.pi / 2 - c) + math.pi, 2 * math.pi) - math.pi
    rf = r.min()
    k = (np.abs(th2 - math.pi / 2) < pitch / 2) & (r > rf + 0.12)
    P = np.c_[r[k] * np.cos(th2[k]), r[k] * np.sin(th2[k])]
    a0 = np.arctan2(P[:, 1], P[:, 0])
    base = np.array([[(rf - 0.3) * math.cos(a), (rf - 0.3) * math.sin(a)] for a in (a0.min(), a0.max())])
    return _hull(np.vstack([P, base]))


def tooth_polys() -> tuple[np.ndarray, np.ndarray]:
    """(44T gear tooth from the lab auger's STEP, 24T pinion tooth), each a convex 2D polygon with the tooth on +y."""
    cache = OUT / "tooth_polys12.npz"
    if cache.exists():
        z = np.load(cache)
        return z["g"], z["p"]
    import fea_tooth as FT                       # gear-mesh: the 44T's outline cut from the auger STEP at its mid-plane
    gg = json.loads((GM / "out" / "gear_geometry.json").read_text())
    g = tooth_polygon(FT.gear_outline_from_step(sum(gg["face_z_mm"]) / 2), Z2)
    p = tooth_polygon(involute_outline(Z1), Z1)
    np.savez(cache, g=g, p=p)
    return g, p


def prism(poly, x0, x1):
    v = [(x * MM, a * MM, b * MM) for x in (x0, x1) for a, b in poly]
    return " ".join(f"{c:.7f}" for p in v for c in p)


# ---------------------------------------------------------------- configuration
@dataclass
class Cfg:
    a_err: float = 0.0          # mm added to the pinion's distance from the gear (+ = farther): the tolerance stack
    mu: float = 0.15            # steel pinion on printed PETG, PTFE dry lube (gear-mesh: 0.10 lubed, 0.20 dry)
    k_roll: float = 10.0        # N*m/rad: the EC's roll (about x) on the P16's clevis and rod (play + bending, lumped)
    k_yaw: float = 10.0         # N*m/rad: its yaw (about z)
    k_lat: float = 1.0e4        # N/m: its sideways (y) give: the P16's rod at 10 N side load moves ~1 mm (assumed)
    detent: float = 3.0e-3      # N*m: the free NEMA 11's detent torque (DRV8825 disabled)
    drag: float = 5.0e-3        # N*m: the auger's static drag (5 mN m empty; 30 mN m with packed powder)
    spring: bool = False        # v11's proposed slide (kept for comparison; v12 is the cradle)
    cradle: bool = True         # v12: the pinion on the spring-loaded cradle (False: v11's rigid mount, as drawn in v11)
    piv_dy: float = -18.5       # v12: the pivot's y from the pinion's axis (-: the side the gears arrive from, a trailing arm; +: leading)
    piv_dz: float = 0.0         # v12: the pivot's z from the pinion's axis (+: toward the gear; +12 puts it level with the pitch point)
    seats: int = 2              # v12: the EC's guide seats (v11: 1)
    hall_lift: float = 0.8      # v12: the hall switch reads 'lifted' above this lift of the pinion over the pivot's level (mm)
    k_spring: float = 1000.0    # N/m (1 N/mm) at the pinion
    f_spring: float = 6.0       # N at the stop
    stop_deep: float = 0.4      # mm the stop lets the pinion go deeper than the zero-backlash centre distance (34.0)
    p16_kp: float = 1.0e5       # N/m: the P16's lead screw held by the LAC
    p16_flim: float = 50.0
    i_set: float = 0.45         # A: the driver current v2-v11 use (0.067 N m stall at the pinion)
    v_supply: float = 12.0
    mesh_tc: float = 4.0e-4     # tooth contact time constant (gear-mesh calibration: FEA single-pair stiffness)
    extra: dict = field(default_factory=dict)


def ec_inertial(cfg: Cfg):
    if cfg.cradle:
        return _com(EC_PARTS)
    parts = EC_PARTS_V11 if not cfg.spring else [p for p in EC_PARTS_V11 if p[0] not in (180.0, 34.0)]
    return _com(parts)


# ---------------------------------------------------------------- model
def build(cfg: Cfg) -> tuple[str, dict]:
    gp, pp = tooth_polys()
    g = GEO
    bx, by, bz = g["p16_base"]
    px, py, pz = g["p16_pin"]
    L0 = g["act_retracted"] + g["p16_ext_rest"]
    d = np.array([px - bx, pz - bz])
    assert abs(np.linalg.norm(d) - L0) < 0.2, (np.linalg.norm(d), L0)
    d /= np.linalg.norm(d)
    m_ec, c_ec = ec_inertial(cfg)
    m_mod, c_mod = _com(MOD_PARTS)
    a_nom = -g["pinion_axis_z"] + cfg.a_err                  # the pinion axis's distance from the gear's, as built
    pin_z = -a_nom
    gx0, gx1 = g["gear_face"]
    qx0, qx1 = g["pinion_face"]
    xm = 0.5 * (qx0 + qx1)
    sol_t = f'solref="{cfg.mesh_tc:.2e} 1.0" solimp="0.98 0.995 0.0002 0.5 2"'
    sol_c = 'solref="0.0005 1.0" solimp="0.95 0.99 0.0002 0.5 2"'     # printed-part contacts: about 1 N/um at the EC's mass
    hx0, hx1 = g["t_head_x"]
    hz0, hz1 = g["t_head_z"]
    sx0, sx1 = g["t_stem_x"]
    c = g["slot_clear"]
    ry = g["rail_y"]
    lip_top = hz0 + g["lip_gap"]
    ceil = hz1 - g["ceiling_gap"]
    tips = [g["shoe_tip"]] + ([g["shoe_tip2"]] if (cfg.cradle and cfg.seats >= 2) else [])
    r_nose = 2.0
    nose_cs = [(t[0] - px, t[1] - py, (t[2] - r_nose * math.sqrt(2)) - pz) for t in tips]   # contact after the 0.5 mm the drawing leaves
    tx, ty, tz = g["shoe_tip"]
    X = [f"""<mujoco model="v12-station">
  <compiler angle="radian" autolimits="true"/>
  <option timestep="{DT}" gravity="0 0 {G}" integrator="implicitfast" cone="elliptic" iterations="80" tolerance="1e-10">
    <flag filterparent="disable"/>
  </option>
  <size memory="80M"/>
  <visual><global offwidth="1280" offheight="720"/></visual>
  <asset>
    <mesh name="gtooth" vertex="{prism(gp, gx0, gx1)}"/>
    <mesh name="ptooth" vertex="{prism(pp, qx0 - xm, qx1 - xm)}"/>
  </asset>
  <default>
    <geom contype="0" conaffinity="0" condim="3" friction="0.3 0.005 0.0001"/>
    <default class="tooth"><geom condim="3" friction="{cfg.mu} 0 0" {sol_t} margin="0" gap="0"/></default>
    <default class="hard"><geom condim="3" friction="0.3 0 0" {sol_c}/></default>
  </default>
  <worldbody>"""]
    # the guides' seats: 90 deg cones (12 flat facets) with their apexes seat_gap under the noses' tips, opening toward -z (world up)
    nf = 12
    for si, (tx, ty, tz) in enumerate(tips):
        apex_z = tz + g["seat_gap"]
        seat = []
        for k in range(nf):
            a = 2 * math.pi * k / nf
            rr = 4.0                                  # facet centre's distance from the axis
            cxw, cyw = tx + rr * math.cos(a), ty + rr * math.sin(a)
            czw = apex_z - rr                        # 45 deg: z rises (toward -z) as r grows
            n = np.array([-math.cos(a), -math.sin(a), -1.0]) / math.sqrt(2)
            t1 = np.array([-math.sin(a), math.cos(a), 0.0])
            t2 = np.cross(n, t1)
            R = np.c_[t1, t2, n]
            q = _quat(R)
            ctr = np.array([cxw, cyw, czw]) - n * 2.5
            seat.append(f'<geom class="hard" type="box" size="{2.4 * MM:.5f} {4.5 * MM:.5f} {2.5 * MM:.5f}" pos="{ctr[0] * MM:.6f} {ctr[1] * MM:.6f} {ctr[2] * MM:.6f}" '
                        f'quat="{q[0]:.6f} {q[1]:.6f} {q[2]:.6f} {q[3]:.6f}" contype="64" conaffinity="32" rgba="0.9 0.5 0.1 0.6"/>')
        X.append(f'    <body name="seat{"" if si == 0 else si + 1}">' + "".join(seat) + "</body>")

    # the carriage (chain) and the module
    imod = 0.30 * m_mod * (0.257 ** 2 / 12)
    X.append(f"""    <body name="carriage">
      <joint name="chain" type="slide" axis="0 1 0" damping="5"/>
      <inertial pos="0 0 0" mass="0.25" diaginertia="1e-3 1e-3 1e-3"/>
      <body name="module">
        <joint name="hinge" type="hinge" axis="0 1 0" range="0 1.7" damping="0.0005" solreflimit="0.0005 1" solimplimit="0.95 0.99 0.0002"/>
        <inertial pos="{c_mod[0] * MM:.5f} {c_mod[1] * MM:.5f} {c_mod[2] * MM:.5f}" mass="{m_mod:.5f}" diaginertia="{0.2 * imod:.3e} {imod:.3e} {imod:.3e}"/>
        <geom name="t_head" class="hard" type="box" pos="{(hx0 + hx1) / 2 * MM:.5f} 0 {(hz0 + hz1) / 2 * MM:.5f}" size="{(hx1 - hx0) / 2 * MM:.5f} {g['t_hy'] * MM:.5f} {abs(hz1 - hz0) / 2 * MM:.5f}" contype="8" conaffinity="16" rgba="0.9 0.6 0.1 1"/>
        <geom name="t_stem" class="hard" type="box" pos="{(sx0 + sx1) / 2 * MM:.5f} 0 {(hz0 - 20.0) / 2 * MM:.5f}" size="{(sx1 - sx0) / 2 * MM:.5f} {g['t_hy'] * MM:.5f} {abs(hz0 + 20.0) / 2 * MM:.5f}" contype="8" conaffinity="16" rgba="0.9 0.6 0.1 1"/>
        <geom name="plate" class="hard" type="box" pos="{0.125:.5f} 0 {(g['plate_top'] + 4.0) * MM:.5f}" size="0.126 0.027 0.004" contype="8" conaffinity="16" rgba="0.1 0.25 0.85 0.5"/>
        <body name="auger">
          <joint name="spin" type="hinge" axis="1 0 0" damping="2e-6"/>
          <inertial pos="{AUG_X * MM:.5f} 0 0" mass="{AUG_M:.5f}" diaginertia="{AUG_J:.3e} {AUG_IYY:.3e} {AUG_IYY:.3e}"/>
          <geom type="cylinder" fromto="0.0004 0 0 0.2504 0 0" size="0.0125" rgba="0.9 0.9 0.86 0.3"/>""")
    for k in range(Z2):
        a = 2 * math.pi * k / Z2
        q = (math.cos(a / 2), math.sin(a / 2), 0, 0)
        X.append(f'          <geom class="tooth" type="mesh" mesh="gtooth" quat="{q[0]:.7f} {q[1]:.7f} 0 0" contype="2" conaffinity="4" rgba="0.85 0.85 0.8 1"/>')
    X.append("        </body>\n      </body>\n    </body>")
    # the P16, the EC on its rod end
    ang = math.atan2(d[0], d[1])
    ec_rel = lambda x, y, z: ((x - px) * MM, (y - py) * MM, (z - pz) * MM)
    cx, cy, cz = ec_rel(*c_ec)
    lip_geoms = []
    for (x0, x1) in ((hx0 - c, sx0 - c), (sx1 + c, hx1 + c)):
        p_ = ec_rel((x0 + x1) / 2, 0.0, (lip_top + g["lip_bottom"]) / 2)
        lip_geoms.append(f'<geom class="hard" type="box" pos="{p_[0]:.6f} {p_[1]:.6f} {p_[2]:.6f}" size="{(x1 - x0) / 2 * MM:.6f} {ry * MM:.6f} {abs(lip_top - g["lip_bottom"]) / 2 * MM:.6f}" contype="16" conaffinity="8" rgba="0.2 0.7 0.4 1"/>')
    p_ = ec_rel((hx0 + hx1) / 2, 0.0, ceil - 1.5)
    lip_geoms.append(f'<geom class="hard" type="box" pos="{p_[0]:.6f} {p_[1]:.6f} {p_[2]:.6f}" size="{(hx1 - hx0 + 2 * c) / 2 * MM:.6f} {ry * MM:.6f} {1.5 * MM:.6f}" contype="16" conaffinity="8" rgba="0.2 0.7 0.4 1"/>')
    for sx in (-1, 1):   # the slot's walls round the head (x)
        xw = (hx0 - c - 1.0) if sx < 0 else (hx1 + c + 1.0)
        p_ = ec_rel(xw, 0.0, (ceil + lip_top) / 2)
        lip_geoms.append(f'<geom class="hard" type="box" pos="{p_[0]:.6f} {p_[1]:.6f} {p_[2]:.6f}" size="{1.0 * MM:.6f} {ry * MM:.6f} {abs(ceil - lip_top) / 2 * MM:.6f}" contype="16" conaffinity="8" rgba="0.2 0.7 0.4 0.5"/>')
    p_ = ec_rel(20.0, 0.0, g["ec_bottom"] - 2.0)       # the EC's underside over the plate (x -8.6..45 is the spine and ramp)
    lip_geoms.append(f'<geom class="hard" type="box" pos="{p_[0]:.6f} {p_[1]:.6f} {p_[2]:.6f}" size="{25.0 * MM:.6f} {9.0 * MM:.6f} {2.0 * MM:.6f}" contype="16" conaffinity="8" rgba="0.2 0.7 0.4 0.4"/>')
    X.append(f"""    <body name="p16" pos="{bx * MM:.5f} {by * MM:.5f} {bz * MM:.5f}">
      <joint name="p16_pivot" type="hinge" axis="0 1 0" damping="0.01"/>
      <geom type="box" pos="{d[0] * 0.10:.5f} 0 {d[1] * 0.10:.5f}" size="0.0105 0.0075 0.09" euler="0 {ang:.5f} 0" mass="0.10" rgba="0.25 0.25 0.28 1"/>
      <body name="rod">
        <joint name="p16_slide" type="slide" axis="{d[0]:.6f} 0 {d[1]:.6f}" damping="50"/>
        <geom type="capsule" fromto="{d[0] * 0.15:.5f} 0 {d[1] * 0.15:.5f} {d[0] * L0 * MM:.5f} 0 {d[1] * L0 * MM:.5f}" size="0.003" mass="0.03" rgba="0.7 0.7 0.72 1"/>
        <body name="ec" pos="{(px - bx) * MM:.5f} 0 {(pz - bz) * MM:.5f}">
          <joint name="ec_lat" type="slide" axis="0 1 0" stiffness="{cfg.k_lat:.4g}" damping="{2 * math.sqrt(cfg.k_lat * m_ec) * 0.3:.4g}"/>
          <joint name="ec_roll" type="hinge" axis="1 0 0" stiffness="{cfg.k_roll:.4g}" damping="{0.02 * cfg.k_roll ** 0.5:.4g}"/>
          <joint name="ec_yaw" type="hinge" axis="0 0 1" stiffness="{cfg.k_yaw:.4g}" damping="{0.02 * cfg.k_yaw ** 0.5:.4g}"/>
          <joint name="ec_pin" type="hinge" axis="0 1 0" damping="0.0005"/>
          <inertial pos="{cx:.6f} {cy:.6f} {cz:.6f}" mass="{m_ec:.5f}" diaginertia="6e-5 6e-4 6e-4"/>
          {''.join(f'<geom type="sphere" pos="{c[0] * MM:.6f} {c[1] * MM:.6f} {c[2] * MM:.6f}" size="{r_nose * MM:.5f}" class="hard" contype="32" conaffinity="64" rgba="0.2 0.7 0.4 1"/>' for c in nose_cs)}
          {''.join(lip_geoms)}""")
    pin_ax = ec_rel(xm, 0.0, pin_z)
    if cfg.cradle:
        # v12: the cradle on its pivot (along x), the pinion level with it at q = 0; q > 0 turns the pinion toward the gear (+z). The pivot and
        # the stop sit a_err farther from the gear than drawn: tight mesh is at sin q = a_err / L, the stop at sin q = stop_deep / L
        L = abs(cfg.piv_dy)
        sg = 1.0 if cfg.piv_dy < 0 else -1.0                # pinion at +L (trailing arm, pivot on -y) or -L (leading) in y from the pivot
        pvz = g["pivot"][1] + cfg.piv_dz - cfg.a_err
        piv = ec_rel(xm, cfg.piv_dy, pvz)
        q_stop = math.asin(cfg.stop_deep / L)
        q_lo = -math.asin(g["lift_max"] / L)
        k_th = cfg.k_spring * (L * MM) ** 2
        ref = q_stop + (cfg.f_spring / cfg.k_spring) / (L * MM)
        mc, cc = _com(CRADLE_PARTS)
        crel = ((cc[0] - xm) * MM, (cc[1] - cfg.piv_dy) * MM, (cc[2] - g["pivot"][1] - cfg.piv_dz) * MM)   # the cradle's centre of mass from the pivot
        icr = 2.4e-5                                        # about its centre of mass (the NEMA 11's 28 mm square body)
        X.append(f"""          <body name="cradle" pos="{piv[0]:.6f} {piv[1]:.6f} {piv[2]:.6f}">
            <joint name="cradle" type="hinge" axis="{sg:.0f} 0 0" range="{q_lo:.6f} {q_stop:.6f}" stiffness="{k_th:.6g}" springref="{ref:.6f}" damping="0.0008" solreflimit="0.0005 1"/>
            <inertial pos="{crel[0]:.6f} {crel[1]:.6f} {crel[2]:.6f}" mass="{mc - 0.034:.5f}" diaginertia="{icr:.3e} {icr:.3e} {icr:.3e}"/>
            <body name="pinion" pos="0 {-cfg.piv_dy * MM:.6f} {-cfg.piv_dz * MM:.6f}">""")
    elif cfg.spring:
        # the NEMA 11 and pinion on a slide toward the gear (+z), pushed by a spring; the stop lets it go stop_deep under 34.0
        q_stop = (a_nom - (A0 - cfg.stop_deep))             # how far (+z, mm) the carrier can move from as-drawn before the stop
        ref = q_stop + cfg.f_spring / cfg.k_spring * 1000.0  # spring's free position, mm
        X.append(f"""          <body name="carrier" pos="{pin_ax[0]:.6f} {pin_ax[1]:.6f} {pin_ax[2]:.6f}">
            <joint name="carrier" type="slide" axis="0 0 1" range="{-2.0 * MM:.5f} {q_stop * MM:.6f}" stiffness="{cfg.k_spring:.4g}" springref="{ref * MM:.6f}" damping="3" solreflimit="0.0005 1"/>
            <inertial pos="{(115.0 - xm) * MM:.5f} 0 0" mass="0.214" diaginertia="2e-5 6e-5 6e-5"/>
            <body name="pinion">""")
    else:
        X.append(f"""          <body name="pinion" pos="{pin_ax[0]:.6f} {pin_ax[1]:.6f} {pin_ax[2]:.6f}">""")
    X.append(f"""              <joint name="motor" type="hinge" axis="1 0 0" damping="0"/>
              <inertial pos="0 0 0" mass="0.034" diaginertia="{J_PINION + J_ROTOR:.3e} {0.6 * (J_PINION + J_ROTOR):.3e} {0.6 * (J_PINION + J_ROTOR):.3e}"/>""")
    for k in range(Z1):
        a = 2 * math.pi * k / Z1 + math.pi + math.pi / Z1        # tooth on -z side faces a gear space at the line of centres
        q = (math.cos(a / 2), math.sin(a / 2), 0, 0)
        X.append(f'              <geom class="tooth" type="mesh" mesh="ptooth" quat="{q[0]:.7f} {q[1]:.7f} 0 0" contype="4" conaffinity="2" rgba="0.95 0.45 0.05 1"/>')
    X.append("            </body>" + ("\n          </body>" if (cfg.spring or cfg.cradle) else ""))
    X.append("""        </body>
      </body>
    </body>
  </worldbody>
""")
    X.append("</mujoco>")
    info = dict(L0=L0, d=d.tolist(), m_ec=m_ec, c_ec=c_ec, m_mod=m_mod, c_mod=c_mod, a_nom=a_nom)
    return "\n".join(X), info


def _quat(R):
    """Rotation matrix -> (w, x, y, z)."""
    q = np.empty(4)
    t = np.trace(R)
    if t > 0:
        s = math.sqrt(t + 1.0) * 2
        q[:] = (0.25 * s, (R[2, 1] - R[1, 2]) / s, (R[0, 2] - R[2, 0]) / s, (R[1, 0] - R[0, 1]) / s)
    else:
        i = int(np.argmax(np.diag(R)))
        j, k = (i + 1) % 3, (i + 2) % 3
        s = math.sqrt(1.0 + R[i, i] - R[j, j] - R[k, k]) * 2
        q[0] = (R[k, j] - R[j, k]) / s
        q[1 + i] = 0.25 * s
        q[1 + j] = (R[j, i] + R[i, j]) / s
        q[1 + k] = (R[k, i] + R[i, k]) / s
    return q / np.linalg.norm(q)


# ---------------------------------------------------------------- the simulator
class Station:
    def __init__(self, cfg: Cfg):
        self.cfg = cfg
        self.xml, self.info = build(cfg)
        self.m = mujoco.MjModel.from_xml_string(self.xml)
        self.d = mujoco.MjData(self.m)
        m = self.m
        names = ["chain", "hinge", "spin", "p16_pivot", "p16_slide", "ec_lat", "ec_roll", "ec_yaw", "ec_pin", "motor"] + (
            ["cradle"] if cfg.cradle else (["carrier"] if cfg.spring else []))
        self.qa = {n: m.jnt_qposadr[m.joint(n).id] for n in names}
        self.va = {n: m.jnt_dofadr[m.joint(n).id] for n in names}
        self.bid = {n: m.body(n).id for n in ("module", "auger", "ec", "pinion", "seat", "carriage") + (("cradle",) if cfg.cradle else ())}
        self.seat_ids = [m.body(n).id for n in ("seat", "seat2") if mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_BODY, n) >= 0]
        self.mode = "free"          # free | held | drive
        self.theta_cmd = 0.0
        self.w_cmd = 0.0
        self.t_extra = 0.0          # extra load torque on the auger (N m), signed against its rotation
        self.drag = cfg.drag
        self.taps = []              # (t0, F) solenoid pulses
        self.chain_y = 0.0          # chain target (mm)
        self.chain_v = 0.0          # its velocity (mm/s), fed forward
        self.p16_q = 0.0            # rod target (mm, from rest; negative retracts)
        self.p16_v = 0.0
        self.f_chain = 0.0          # the servo forces (N), logged
        self.f_p16 = 0.0
        self.gid = {}
        for n in ("t_head", "t_stem", "plate"):
            self.gid[n] = m.geom(n).id
        if cfg.cradle:
            # v12: start the cradle where the spring holds it with a module in mesh (tight mesh, or on its stop when the stack puts the stop
            # short of it), so a run that starts with the module already at the station (cycle, exit) doesn't start with the teeth overlapping
            L_ = abs(cfg.piv_dy)
            q0 = math.asin(max(-0.9, min(cfg.stop_deep, cfg.a_err) / L_))
            self.d.qpos[self.qa["cradle"]] = q0
            mujoco.mj_forward(m, self.d)

    # ---- probes (mm)
    def pos(self, body):
        return self.d.xpos[self.bid[body]] / MM

    def R(self, body):
        return self.d.xmat[self.bid[body]].reshape(3, 3)

    def centre_distance(self):
        gc = self.pos("auger")
        pc = self.pos("pinion")
        ax = self.R("auger")[:, 0]
        v = pc - gc
        return float(np.linalg.norm(v - (v @ ax) * ax))

    def tilt_deg(self):
        return math.degrees(self.d.qpos[self.qa["hinge"]])

    def lip_gap(self):
        """The T's head underside over the lips' top, along the EC's z at the head's centre (mm; 0 = on the lips)."""
        Rm, Re = self.R("module"), self.R("ec")
        head = self.pos("module") + Rm @ np.array([60.0, 0.0, GEO["t_head_z"][0]])
        lip = self.pos("ec") + Re @ (np.array([60.0, 0.0, GEO["t_head_z"][0] + GEO["lip_gap"]]) - np.array(GEO["p16_pin"]) + np.array([0, GEO["p16_pin"][1], 0]) * 0)
        lip = self.pos("ec") + Re @ np.array([60.0 - GEO["p16_pin"][0], -GEO["p16_pin"][1], GEO["t_head_z"][0] + GEO["lip_gap"] - GEO["p16_pin"][2]])
        return float((lip - head) @ Re[:, 2]) + GEO["lip_gap"] - GEO["lip_gap"]

    def mesh_phase(self):
        """Gear angle + (z1/z2) x pinion angle, in gear pitches: constant while the teeth stay in step."""
        return (self.d.qpos[self.qa["spin"]] + Z1 / Z2 * self.d.qpos[self.qa["motor"]]) / (2 * math.pi / Z2)

    def tooth_force(self):
        """Sum of the normal forces between pinion and gear teeth (N)."""
        d, m = self.d, self.m
        f = np.zeros(6)
        tot = 0.0
        pb, gb = self.bid["pinion"], self.bid["auger"]
        for i in range(d.ncon):
            c = d.contact[i]
            b1, b2 = m.geom_bodyid[c.geom1], m.geom_bodyid[c.geom2]
            if {b1, b2} == {pb, gb}:
                mujoco.mj_contactForce(m, d, i, f)
                tot += f[0]
        return tot

    def seat_force(self):
        return sum(self.seat_forces())

    def seat_forces(self):
        """Normal force on each guide seat (N): (first, second)."""
        d, m = self.d, self.m
        f = np.zeros(6)
        out = [0.0 for _ in self.seat_ids]
        for i in range(d.ncon):
            c = d.contact[i]
            b1, b2 = m.geom_bodyid[c.geom1], m.geom_bodyid[c.geom2]
            for j, sb in enumerate(self.seat_ids):
                if sb in (b1, b2):
                    mujoco.mj_contactForce(m, d, i, f)
                    out[j] += f[0]
        return out

    def lift(self):
        """v12: the pinion's lift over the pivot's level (mm), what the hall switch on the cradle reads (0 in tight mesh as drawn)."""
        if not self.cfg.cradle:
            return 0.0
        q = self.d.qpos[self.qa["cradle"]]
        sg = 1.0 if self.cfg.piv_dy < 0 else -1.0
        ry, rz = -self.cfg.piv_dy, -self.cfg.piv_dz
        ph = sg * q
        return -(ry * math.sin(ph) + rz * (math.cos(ph) - 1.0))

    def lifted(self):
        return self.lift() > self.cfg.hall_lift

    def t_force(self):
        """Normal force between the T (module) and the EC's lips/ceiling/walls/underside (N)."""
        d, m = self.d, self.m
        f = np.zeros(6)
        tot = 0.0
        mb, eb = self.bid["module"], self.bid["ec"]
        for i in range(d.ncon):
            c = d.contact[i]
            if {m.geom_bodyid[c.geom1], m.geom_bodyid[c.geom2]} == {mb, eb}:
                mujoco.mj_contactForce(m, d, i, f)
                tot += f[0]
        return tot

    # ---- forces
    def motor_torque(self):
        d = self.d
        th = d.qpos[self.qa["motor"]]
        w = d.qvel[self.va["motor"]]
        if self.mode == "free":
            return -self.cfg.detent * math.sin(200.0 * th) - 2e-6 * w, 0.0
        tmax = float(GS.motor_torque(abs(w) / (2 * math.pi), self.cfg.v_supply, self.cfg.i_set))
        e = GC.N_ROTOR * (self.theta_cmd - th)
        return tmax * math.sin(e) - 2.0e-4 * (w - self.w_cmd), e

    def apply(self):
        d = self.d
        d.qfrc_applied[:] = 0.0
        tm, _ = self.motor_torque()
        d.qfrc_applied[self.va["motor"]] += tm
        wg = d.qvel[self.va["spin"]]
        d.qfrc_applied[self.va["spin"]] += -(self.drag + self.t_extra) * math.tanh(wg / 0.02)
        for (t0, F) in self.taps:
            if t0 <= d.time < t0 + 0.012:   # the solenoid pushes the plate over clip 1 (out, +z) and itself back (EC)
                Rm = self.R("module")
                p = (self.pos("module") + Rm @ np.array([GEO["sol_x"], 0.0, -18.0])) * MM
                mujoco.mj_applyFT(self.m, d, F * Rm[:, 2], np.zeros(3), p, self.bid["module"], d.qfrc_applied)
                mujoco.mj_applyFT(self.m, d, -F * Rm[:, 2], np.zeros(3), p, self.bid["ec"], d.qfrc_applied)
        # the chain (NEMA 34 through the chain: stiff) and the P16 (lead screw held by the LAC, 50 N limit) as tracking servos
        qc, vc = d.qpos[self.qa["chain"]], d.qvel[self.va["chain"]]
        self.f_chain = 2.0e6 * (self.chain_y * MM - qc) + 3.0e3 * (self.chain_v * MM - vc)
        d.qfrc_applied[self.va["chain"]] += self.f_chain
        qp, vp = d.qpos[self.qa["p16_slide"]], d.qvel[self.va["p16_slide"]]
        f = self.cfg.p16_kp * (self.p16_q * MM - qp) + 600.0 * (self.p16_v * MM - vp)
        self.f_p16 = max(-self.cfg.p16_flim, min(self.cfg.p16_flim, f))
        d.qfrc_applied[self.va["p16_slide"]] += self.f_p16

    def step(self, n=1):
        for _ in range(n):
            self.theta_cmd += self.w_cmd * DT
            self.apply()
            mujoco.mj_step(self.m, self.d)

    def set_chain(self, y_mm, v_mm_s=0.0):
        """Put the carriage (and its module) at y with velocity v, statically (before a run)."""
        self.d.qpos[self.qa["chain"]] = y_mm * MM
        self.d.qvel[self.va["chain"]] = v_mm_s * MM
        self.chain_y = y_mm
        mujoco.mj_forward(self.m, self.d)

    def settle(self, t=0.1):
        self.step(int(t / DT))


def ext_for_tilt(tilt_deg: float) -> float:
    """The P16's slide coordinate (mm from rest) for a module tilt: the pin swings round the hinge (y axis) by the tilt."""
    bx, _, bz = GEO["p16_base"]
    px, _, pz = GEO["p16_pin"]
    a = math.radians(tilt_deg)
    # Ry(a) in Sam's frame: x -> x cos a + z sin a ; z -> -x sin a + z cos a
    qx, qz = px * math.cos(a) + pz * math.sin(a), -px * math.sin(a) + pz * math.cos(a)
    return math.hypot(qx - bx, qz - bz) - (GEO["act_retracted"] + GEO["p16_ext_rest"])


def trapezoid(dist: float, v: float, a: float, t: float) -> tuple[float, float]:
    """Position and velocity along a trapezoidal move of length dist (mm) at time t (s)."""
    ta = v / a
    if dist < v * ta:
        ta = math.sqrt(dist / a)
        v = a * ta
    tc = (dist - v * ta) / v
    if t <= 0:
        return 0.0, 0.0
    if t < ta:
        return 0.5 * a * t * t, a * t
    if t < ta + tc:
        return 0.5 * a * ta * ta + v * (t - ta), v
    if t < 2 * ta + tc:
        tt = t - ta - tc
        return 0.5 * a * ta * ta + v * tc + v * tt - 0.5 * a * tt * tt, v - a * tt
    return dist, 0.0


# ---------------------------------------------------------------- studies
def entry(cfg: Cfg, phase_frac: float, mode="free", y0=-18.0, v=50.0, acc=250.0, record=False, seek_rev_s=0.25, hold=0.12, post_seek=True,
          seek_reverse=True, seek_t=0.2, tries=2, reindex=True, reindex_held=False):
    """One index into the station: the carriage arrives from Sam -y at the Pi driver's 50 mm/s and 250 mm/s^2, the gear slides into
    mesh with the pinion (the NEMA 11's driver off: the pinion free), the carriage stops at the station, everything settles. The pinion
    starts phase_frac of a pinion pitch off the angle that meshes at the station. Then v12's seek: the driver on, the pinion turned
    seek_rev_s forward for seek_t and back for seek_t; if the hall switch still reads 'lifted', a second try, back first. The result
    records the switch's reading after each step and whether it was right."""
    S = Station(cfg)
    d = S.d
    S.mode = "free" if mode == "free" else "drive"
    S.d.qpos[S.qa["motor"]] = phase_frac * 2 * math.pi / Z1
    S.theta_cmd = S.d.qpos[S.qa["motor"]]
    S.w_cmd = (-2 * math.pi * abs(seek_rev_s)) if mode == "seek" else 0.0
    S.set_chain(y0, 0.0)
    S.settle(0.10)                          # the EC settles on its seats and clevis, the module on its shelf, the cradle on its stop
    rest_seats = [round(float(f), 2) for f in S.seat_forces()]
    rest_lift = S.lift()
    t_a = v / acc
    dist = -y0
    t_start = t_a
    x_start = 0.5 * acc * t_a ** 2
    total = dist + x_start
    T = (total - v * t_a) / v + 2 * t_a
    n = int((T - t_start + hold) / DT)
    S.set_chain(y0, v)
    log = []
    frames = []
    every = max(1, int(2e-4 / DT))
    f_chain_max = 0.0
    lift_max = -9.0
    for i in range(n):
        t = t_start + i * DT
        x, vv = trapezoid(total, v, acc, t)
        S.chain_y = y0 + (x - x_start)
        S.chain_v = vv
        S.step()
        if i % every == 0:
            fc = float(S.f_chain)
            if abs(S.chain_y) < 13.0:
                f_chain_max = max(f_chain_max, abs(fc))
            lift_max = max(lift_max, S.lift())
            log.append((d.time, S.chain_y, d.qpos[S.qa["chain"]] / MM, S.centre_distance(), S.tooth_force(), fc,
                        math.degrees(d.qpos[S.qa["motor"]]), math.degrees(d.qpos[S.qa["spin"]]), S.seat_force(),
                        math.degrees(d.qpos[S.qa["ec_roll"]]), S.tilt_deg(), S.t_force(), S.lift()))
        if record and i % int(round(1 / 300 / DT)) == 0:
            frames.append((d.time, d.qpos.copy()))
    cd_stop = S.centre_distance()
    hall = [bool(S.lifted())]
    cds = [cd_stop]
    seek_log = []

    def seek(direction):
        """forward then back (direction +1), or back then forward (-1): the driver on, 0.25 rev/s, seek_t each way, then hold 0.1 s."""
        S.mode = "drive"
        S.theta_cmd = d.qpos[S.qa["motor"]]
        w = -2 * math.pi * abs(seek_rev_s) * direction          # - turns the auger forward (the dose's direction)
        S.w_cmd = w
        nn = int(2 * seek_t / DT)
        for i in range(nn):
            if i == nn // 2:
                S.w_cmd = -w
            S.step()
            if record and i % int(round(1 / 300 / DT)) == 0:
                frames.append((d.time, d.qpos.copy()))
            if i % every == 0:
                seek_log.append((d.time, S.centre_distance(), S.tooth_force(), S.lift()))
        S.w_cmd = 0.0
        for i in range(int(0.1 / DT)):
            S.step()
            if record and i % int(round(1 / 300 / DT)) == 0:
                frames.append((d.time, d.qpos.copy()))

    def reindex_once(back=13.0):
        """v12 driver's fallback when the switch still reads lifted after both seeks: the chain backs off `back` mm (past where the tips
        first touch, 12.9 mm), the pinion turns half a tooth with the driver on, the chain comes back with the NEMA 11 free, then one
        seek (v11's stopgap, which cleared 42 of its 46 jams). With dry teeth, holding the pinion on the way back (reindex_held) left 10 of
        36 on the tips against 6 with it free, so the driver leaves it free."""
        S.mode = "free"
        S.w_cmd = 0.0
        y_a = S.chain_y

        def move(y0, y1, T):
            n2 = int(T / DT)
            for i in range(n2):
                tt = i / (n2 - 1)
                S.chain_y = y0 + (y1 - y0) * (0.5 - 0.5 * math.cos(math.pi * tt))
                S.chain_v = (y1 - y0) * 0.5 * math.pi * math.sin(math.pi * tt) / T
                S.step()
                if record and i % int(round(1 / 300 / DT)) == 0:
                    frames.append((d.time, d.qpos.copy()))
            S.chain_v = 0.0
        move(y_a, y_a - back, 0.5)
        S.mode = "drive"
        S.theta_cmd = d.qpos[S.qa["motor"]]
        S.w_cmd = -2 * math.pi * abs(seek_rev_s)
        for i in range(int((0.5 / Z1) / abs(seek_rev_s) / DT)):      # half a pinion tooth
            S.step()
        S.w_cmd = 0.0
        S.theta_cmd = d.qpos[S.qa["motor"]]
        S.mode = "held" if reindex_held else "free"         # held: the gear comes back to a pinion half a tooth off the phase that stubbed
        move(y_a - back, y_a, 0.5)
        S.mode = "drive"
        for i in range(int(0.1 / DT)):
            S.step()
        seek(+1)

    n_seeks = 0
    reindexed = False
    if post_seek:
        for k in range(tries):
            if k > 0 and not S.lifted():
                break                                           # the second try only when the switch still reads lifted
            seek(+1 if (k % 2 == 0) else -1)
            n_seeks += 1
            hall.append(bool(S.lifted()))
            cds.append(S.centre_distance())
            if not seek_reverse:
                break
        if reindex and S.lifted():
            reindex_once()
            reindexed = True
            n_seeks += 1
            hall.append(bool(S.lifted()))
            cds.append(S.centre_distance())
    A = np.array(log)
    lag = A[:, 1] - A[:, 2]
    near = np.abs(A[:, 2]) < 11.5
    kf = max(1, int(round(2e-3 / (every * DT))))
    f_avg = np.convolve(A[:, 4], np.ones(kf) / kf, mode="same")
    res = dict(phase=phase_frac, mode=mode, a_err=cfg.a_err, spring=cfg.spring, cradle=cfg.cradle, piv_dy=cfg.piv_dy, seats=cfg.seats,
               f_spring=cfg.f_spring, stop_deep=cfg.stop_deep, k_roll=cfg.k_roll, drag_mNm=cfg.drag * 1e3,
               cd_end=round(float(S.centre_distance()), 3),
               tooth_force_max_N=round(float(A[near, 4].max() if near.any() else 0.0), 2),
               tooth_force_2ms_max_N=round(float(f_avg[near].max() if near.any() else 0.0), 2), cd_at_stop=round(cd_stop, 3),
               chain_force_max_N=round(f_chain_max, 2), chain_lag_max_mm=round(float(np.abs(lag).max()), 3),
               pinion_turn_deg=round(float(A[-1, 6] - A[0, 6]), 1), auger_turn_deg=round(float(A[-1, 7] - A[0, 7]), 2),
               ec_roll_max_deg=round(float(np.abs(A[:, 9]).max()), 3), module_lift_max_deg=round(float(A[:, 10].max()), 3),
               end_tooth_force_N=round(float(S.tooth_force()), 2), end_seats_N=[round(float(f), 2) for f in S.seat_forces()],
               end_t_force_N=round(float(S.t_force()), 2), rest_seats_N=rest_seats, rest_lift_mm=round(rest_lift, 3),
               lift_max_mm=round(lift_max, 3), end_lift_mm=round(S.lift(), 3), n_seeks=n_seeks, reindexed=reindexed,
               hall=hall, cds=[round(float(c), 3) for c in cds])
    res["jam"] = bool(res["chain_lag_max_mm"] > 0.25 or res["chain_force_max_N"] > 40.0)
    ok = lambda c: c < A0 + 0.70
    res["meshed"] = bool(ok(cd_stop) and not res["jam"])
    res["stubbed"] = bool(not res["jam"] and not res["meshed"])
    res["meshed_after_seek"] = bool(ok(res["cd_end"]) and not res["jam"])
    # the switch is right when it reads lifted exactly when the pinion isn't in mesh, at every reading
    res["hall_right"] = all(h == (not ok(c)) for h, c in zip(hall, cds))
    if res["jam"]:
        res["outcome"] = "jam"
    elif res["meshed"]:
        res["outcome"] = "meshed"
    elif len(cds) > 1 and ok(cds[1]):
        res["outcome"] = "stub, cleared by the seek"
    elif len(cds) > 2 and ok(cds[2]) and not (reindexed and len(cds) == 3):
        res["outcome"] = "stub, cleared by the second try"
    elif reindexed and ok(cds[-1]):
        res["outcome"] = "stub, cleared by re-indexing"
    else:
        res["outcome"] = "stub left (the switch reads lifted)" if S.lifted() else "stub left, the switch reads seated"
    return (res, A, frames, S) if record else (res, A)


def exit_run(cfg: Cfg, phase_frac: float = 0.0, mode="free", y1=18.0, v=50.0, acc=250.0):
    """The next index: from meshed at the station, the carriage leaves toward Sam +y and the gear slides out of the pinion."""
    S = Station(cfg)
    d = S.d
    S.mode = mode
    S.set_chain(0.0, 0.0)
    S.settle(0.12)
    log = []
    every = max(1, int(2e-4 / DT))
    f_max = 0.0
    T = y1 / v + v / acc
    for i in range(int(T / DT)):
        t = i * DT
        x, vv = trapezoid(y1 + 40.0, v, acc, t)
        S.chain_y = x
        S.chain_v = vv
        S.step()
        if i % every == 0:
            fc = float(S.f_chain)
            f_max = max(f_max, abs(fc))
            log.append((d.time, S.chain_y, d.qpos[S.qa["chain"]] / MM, S.centre_distance(), S.tooth_force(), fc))
    A = np.array(log)
    return dict(phase=phase_frac, a_err=cfg.a_err, spring=cfg.spring, chain_force_max_N=round(f_max, 2),
                tooth_force_max_N=round(float(A[:, 4].max()), 2), chain_lag_max_mm=round(float(np.abs(A[:, 1] - A[:, 2]).max()), 3)), A


def cycle(cfg: Cfg, tilts=(30.0, 90.0), rpm=30.0, load=0.02, record=False, ramp_stall_at=None, taps=True, t_dose=1.0, p16_v=30.0):
    """A station cycle on a module already in mesh: the P16 pulls (30 mm/s), the EC leaves its seat, its lips pick the T up, the module
    tilts to each angle in turn; at each, the auger turns at rpm against a load (a slug per revolution) with solenoid taps; then the
    P16 sets everything back down, the auger reverses one turn at rest. With ramp_stall_at = angle: at that angle the load ramps
    until the motor stalls or the teeth jump instead of dosing."""
    S = Station(cfg)
    d = S.d
    S.mode = "held"
    S.set_chain(0.0, 0.0)
    S.settle(0.15)
    every = max(1, int(5e-4 / DT))
    log = []
    frames = []
    events = []
    ph0 = S.mesh_phase()

    def logit():
        _, e = S.motor_torque()
        log.append((d.time, S.tilt_deg(), S.p16_q, float(S.f_p16), S.centre_distance(), S.tooth_force(), S.seat_force(),
                    S.t_force(), math.degrees(d.qpos[S.qa["ec_roll"]]), d.qpos[S.qa["ec_lat"]] / MM, S.mesh_phase() - ph0, e,
                    S.t_extra + S.drag, d.qvel[S.va["spin"]] * 60 / (2 * math.pi)))

    def run_for(t, fn=None):
        n = int(t / DT)
        for i in range(n):
            if fn:
                fn(i * DT)
            S.step()
            if i % every == 0:
                logit()
            if record and i % int(round(1 / 60 / DT)) == 0:
                frames.append((d.time, d.qpos.copy()))

    def move_p16(target, v=p16_v):
        q0 = S.p16_q
        T = abs(target - q0) / v
        sv = math.copysign(v, target - q0)

        def f(t):
            S.p16_q = q0 + (target - q0) * min(1.0, t / T)
            S.p16_v = sv if t < T else 0.0
        run_for(T, f)
        S.p16_q, S.p16_v = target, 0.0
        run_for(0.25)

    def dose(t):
        w = -rpm / 60 * 2 * math.pi * Z2 / Z1             # the pinion turns opposite to the auger
        S.mode = "drive"
        t0 = d.time
        S.taps = [(t0 + 0.3 + 0.25 * k, 4.0) for k in range(int((t - 0.3) / 0.25))] if taps else []
        S.t_extra = 0.0

        def f(tt):
            S.w_cmd = w * min(1.0, tt / 0.08)
            S.t_extra = load * (1.0 + 0.5 * math.sin(d.qpos[S.qa["spin"]])) - S.drag
        run_for(t, f)
        S.w_cmd = 0.0
        run_for(0.5)                                       # stop, hold 0.5 s (the leakage study)
        S.taps = []
        S.t_extra = 0.0

    def stall_ramp(tmax=0.30, T=1.5):
        w = -rpm / 60 * 2 * math.pi * Z2 / Z1
        S.mode = "drive"
        res = dict(mode=None, load_Nm=None)

        def f(tt):
            S.w_cmd = w * min(1.0, tt / 0.08)
            S.t_extra = tmax * max(0.0, (tt - 0.15) / T)
        n = int((T + 0.3) / DT)
        ph_start = S.mesh_phase()
        for i in range(n):
            f(i * DT)
            S.step()
            if i % every == 0:
                logit()
                _, e = S.motor_torque()
                jump = abs(S.mesh_phase() - ph_start) > 0.5
                if jump or abs(e) > math.pi:
                    res["mode"] = "tooth jump" if jump else "motor stall"
                    res["load_Nm"] = round(S.t_extra + S.drag, 4)
                    res["cd_mm"] = round(S.centre_distance(), 3)
                    break
        S.w_cmd = 0.0
        S.t_extra = 0.0
        S.mode = "held"
        S.theta_cmd = d.qpos[S.qa["motor"]]
        run_for(0.1)
        return res

    out = dict(a_err=cfg.a_err, spring=cfg.spring, k_roll=cfg.k_roll, rpm=rpm, load=load, steps=[])
    for a in tilts:
        tgt = ext_for_tilt(a)
        t0 = d.time
        move_p16(tgt)
        events.append(("tilt", a, t0, d.time))
        st = dict(tilt_cmd=a, tilt=round(S.tilt_deg(), 2))
        if ramp_stall_at is not None and abs(a - ramp_stall_at) < 1e-6:
            st["stall"] = stall_ramp()
        else:
            t1 = d.time
            dose(t_dose)
            events.append(("dose", a, t1, d.time))
            st["dose"] = True
        out["steps"].append(st)
    t0 = d.time
    move_p16(0.0)
    run_for(0.3)
    events.append(("back", 0.0, t0, d.time))
    # reverse one auger turn at rest
    t1 = d.time
    S.mode = "drive"
    w = +30 / 60 * 2 * math.pi * Z2 / Z1
    run_for(2.0 * 60 / 30 * 0 + 2.0, lambda tt: setattr(S, "w_cmd", w if tt < 2.0 - 0.05 else 0.0))
    events.append(("reverse", 0.0, t1, d.time))
    A = np.array(log)
    out["events"] = events
    out["tooth_jumps"] = int(round(abs(A[-1, 10]))) if len(A) else 0
    return (out, A, frames, S) if record else (out, A)


def summarize_cycle(out, A):
    """Numbers per phase of the cycle from the log columns."""
    cols = dict(t=0, tilt=1, p16q=2, p16F=3, cd=4, toothF=5, seatF=6, tF=7, roll=8, lat=9, phase=10, lag=11, load=12, rpm=13)
    res = {}
    for kind, a, t0, t1 in out["events"]:
        k = (A[:, 0] >= t0) & (A[:, 0] <= t1)
        if not k.any():
            continue
        B = A[k]
        key = f"{kind}{'' if kind in ('back', 'reverse') else '_' + format(a, 'g')}"
        res[key] = dict(t=round(t1 - t0, 2), tilt_end=round(float(B[-1, 1]), 2), p16_N=(round(float(B[:, 3].min()), 1), round(float(B[:, 3].max()), 1)),
                        cd_mm=(round(float(B[:, 4].min()), 3), round(float(B[:, 4].max()), 3)), tooth_N_max=round(float(B[:, 5].max()), 2),
                        tooth_N_10ms_max=round(float(np.convolve(B[:, 5], np.ones(20) / 20, mode="same").max()), 2),
                        tooth_N_mean=round(float(B[:, 5].mean()), 2),
                        seat_N_end=round(float(B[-1, 6]), 2), t_contact_N=(round(float(B[:, 7].min()), 2), round(float(B[:, 7].max()), 2)),
                        ec_roll_deg=(round(float(B[:, 8].min()), 3), round(float(B[:, 8].max()), 3)),
                        ec_lat_mm=(round(float(B[:, 9].min()), 3), round(float(B[:, 9].max()), 3)),
                        phase_drift=round(float(B[-1, 10] - B[0, 10]), 3))
    return res


# ---------------------------------------------------------------- geometry check
def geom():
    sys.path.insert(0, str(V11))
    import layout as L
    from params import SHOE10_NOSE, GUIDE11_SEAT_GAP
    M0 = L.sam_frame(L.station_frame(), 0.0)
    Mi = np.linalg.inv(M0)
    sam = lambda p: np.round((Mi @ np.r_[p, 1.0])[:3], 3).tolist()
    print(json.dumps(dict(p16_base=sam(L.P16_11_BASE), p16_pin=sam(L.p16_11_pin(0.0)), p16_ext_rest=round(L.p16_11_ext(0.0), 3),
                          shoe_tip=sam(L.SHOE11_TIP), nose=SHOE10_NOSE, seat_gap=GUIDE11_SEAT_GAP,
                          ext_check={a: (round(L.p16_11_ext(a) - L.p16_11_ext(0.0), 3), round(ext_for_tilt(a), 3)) for a in (30, 60, 90)}), indent=1))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("what", choices=["geom", "entry", "exit", "cycle", "info"])
    ap.add_argument("--a-err", type=float, default=0.0)
    ap.add_argument("--spring", action="store_true")
    ap.add_argument("--mode", default="free")
    ap.add_argument("--phases", type=int, default=4)
    ap.add_argument("--k-roll", type=float, default=10.0)
    ap.add_argument("--drag", type=float, default=5e-3)
    a = ap.parse_args()
    if a.what == "geom":
        geom()
    elif a.what == "info":
        x, info = build(Cfg(spring=a.spring))
        print(json.dumps(info, indent=1))
        m = mujoco.MjModel.from_xml_string(x)
        print("nbody", m.nbody, "ngeom", m.ngeom, "njnt", m.njnt)
    elif a.what == "entry":
        cfg = Cfg(a_err=a.a_err, spring=a.spring, k_roll=a.k_roll, drag=a.drag)
        for k in range(a.phases):
            t = time.time()
            r, _ = entry(cfg, k / a.phases, mode=a.mode)
            print(json.dumps(r), f"{time.time() - t:.1f}s", flush=True)
    elif a.what == "exit":
        r, _ = exit_run(Cfg(a_err=a.a_err, spring=a.spring, k_roll=a.k_roll))
        print(json.dumps(r))
    elif a.what == "cycle":
        cfg = Cfg(a_err=a.a_err, spring=a.spring, k_roll=a.k_roll)
        t = time.time()
        out, A = cycle(cfg)
        print(json.dumps(summarize_cycle(out, A), indent=1), out["tooth_jumps"], f"{time.time() - t:.1f}s")
