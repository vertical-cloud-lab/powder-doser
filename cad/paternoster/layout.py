"""Placements for the paternoster carousel: every instance as (part key, 4x4 world matrix).

`placements(state)` places the whole rig for a machine state: the chain's
shift (links travelled), which gondolas hold a module, the station's
actuator extension and tilt, and an optional module part-way out at the
loading position. Everything comes from params.py and the exact chain
kinematics in kinematics.py, so the CAD, the clearance checks, the renders
and the MuJoCo sim all agree.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

import cadquery as cq
import numpy as np

import kinematics as K
import parts as PT
from params import *  # noqa: F401,F403
from step_io import read_step_parts

HERE = Path(__file__).resolve().parent
REF = HERE / "reference"


# ---------------------------------------------------------------- transforms
def T(R3=None, t=(0.0, 0.0, 0.0)) -> np.ndarray:
    M = np.eye(4)
    if R3 is not None:
        M[:3, :3] = R3
    M[:3, 3] = t
    return M


def Rx(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[1, 0, 0], [0, c, -s], [0, s, c]])


def Ry(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])


def Rz(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])


def cols(*vs) -> np.ndarray:
    return np.array(vs, float).T


def rot(x_axis, z_axis) -> np.ndarray:
    """Proper rotation (det +1) with the part's x and z axes along the given world vectors."""
    x, z = np.asarray(x_axis, float), np.asarray(z_axis, float)
    return cols(x, np.cross(z, x), z)


def chain_frame(mid, ang: float, back: bool) -> np.ndarray:
    """Link frame -> world. Link frame: travel along x, +y into the loop, pins along z.
    Front chain: link z -> world +x. Back chain: turned 180 deg about the link's y (tab toward -x)."""
    t = (0.0, math.cos(ang), math.sin(ang))
    n_in = (0.0, -math.sin(ang), math.cos(ang))
    if not back:
        return T(cols(t, n_in, (1, 0, 0)), (0.0, mid[0], mid[1]))
    return T(cols(tuple(-v for v in t), n_in, (-1, 0, 0)), (CHAIN_L, mid[0], mid[1]))


def sprocket_frame(centre, phi: float, back: bool) -> np.ndarray:
    """Sprocket frame -> world: ring in the frame's XY, hub toward -z (out of the loop)."""
    xl = (0.0, math.cos(phi), math.sin(phi))
    if not back:
        return T(cols(xl, (0.0, -math.sin(phi), math.cos(phi)), (1, 0, 0)), (0.0, centre[0], centre[1]))
    return T(cols(xl, (0.0, math.sin(phi), -math.cos(phi)), (-1, 0, 0)), (CHAIN_L, centre[0], centre[1]))




# ---------------------------------------------------------------- reference parts
@lru_cache(None)
def reference_parts() -> dict[str, cq.Workplane]:
    """Sam's latest (Oct 13) mounting plate and electronics carriage from his Onshape
    Part Studio, and the lab's threaded-storage auger + cap (PR #170). Sam's parts are
    in his studio frame (hinge axis = his y at x = z = 0); the auger runs along +z."""
    sam = read_step_parts(REF / "sam-oct13-mounting-plate-and-carriage.step")
    aug = read_step_parts(REF / "auger-threaded-storage.step")
    cap = read_step_parts(REF / "auger-cap-threaded.step")
    plate = cq.Workplane("XY").add(sam["Mounting Plate"])
    (x1, y1), (x2, y2) = LOCPIN_XY
    depth = 3.5
    plate = plate.cut(cq.Workplane("XY").center(x1, y1).circle(LOCPIN_HOLE / 2).extrude(depth).translate((0, 0, -18.0)))
    plate = plate.cut(cq.Workplane("XY").center(x2, y2).slot2D(LOCPIN_SLOT, LOCPIN_HOLE, 0).extrude(depth).translate((0, 0, -18.0)))
    for (x, y) in ARMATURE_SCREWS:                    # M3 heat-set inserts for the steel tab
        plate = plate.cut(cq.Workplane("XY").center(x, y).circle(2.0).extrude(4.0).translate((0, 0, -18.0)))
    return {"sam_mounting_plate": plate,
            "sam_electronics_carriage": cq.Workplane("XY").add(sam["Carriage"]),
            "auger": cq.Workplane("XY").add(next(iter(aug.values()))),
            "auger_cap": cq.Workplane("XY").add(next(iter(cap.values())))}


def sam_in_gondola(tilt_deg: float = 0.0) -> np.ndarray:
    """Sam's studio frame in a gondola's frame (the module is never turned; tilt lifts the cap end)."""
    return T(None, (HINGE_X, 0.0, HINGE_Z)) @ T(Ry(-math.radians(tilt_deg)))


AUGER_IN_SAM = T(Ry(math.pi / 2), (AUGER_Z0_XS, 0, 0))


# ---------------------------------------------------------------- side plates
def side_holes(back: bool) -> list[tuple]:
    """Holes in a side plate, in (y, z): bottom bearings (49 mm dome hole + 2 bolts, bolt line vertical),
    top idler axle slots, post bolts, motor standoffs (back plate only)."""
    h = []
    for sy in (-1, 1):
        y = sy * CORNER_Y
        h.append(("round", y, Z_BOT, BRG["HOLE"]))
        for dz in (-BRG["J"] / 2, BRG["J"] / 2):
            h.append(("round", y, Z_BOT + dz, 6.9))
        h.append(("slot", y, Z_TOP + (TENSION_TRAVEL[0] + TENSION_TRAVEL[1]) / 2, 10.5, TENSION_TRAVEL[1] - TENSION_TRAVEL[0]))
        h.append(("round", y, Z_TOP + 30.0, 5.5))           # jack-screw block
        for z in (SIDE_Z[0] + 25, (SIDE_Z[0] + SIDE_Z[1]) / 2, SIDE_Z[1] - 25):
            h.append(("round", sy * POST_Y, z, 5.5))         # M5 into the posts' T-nuts
    if back:
        for dy in (-1, 1):
            for dz in (-1, 1):
                h.append(("round", CORNER_Y + dy * MOTOR_SO[0], Z_BOT + dz * MOTOR_SO[1], 6.6))
    return h


# ---------------------------------------------------------------- placements
@dataclass
class Placement:
    key: str
    name: str
    M: np.ndarray
    step: int
    color: tuple = (0.6, 0.6, 0.6)
    group: str = ""
    explode: tuple = (0.0, 0.0, 0.0)
    module: int = -1          # gondola/module index this instance moves with (-1: fixed or chain)


@dataclass
class State:
    shift: float = K.HOME_SHIFT          # chain travel, links
    loaded: tuple = tuple(range(N_MODULES))
    tilt: float = 0.0                    # station module tilt, deg (module at the station only)
    ext: float = DOCK_EXT                # actuator extension at tilt 0 (0 = retracted, DOCK_EXT = docked)
    out_module: int = -1                 # module being swapped at the loading position
    out_frac: float = 0.0                # 0 = seated, 1 = fully slid out (+y)
    gondola_swing: dict = field(default_factory=dict)   # module -> swing angle (rad) about x, from the sim
    station: bool = True
    tension: float = 0.0                 # top axles' offset (mm)
    thumb_out: dict = field(default_factory=dict)       # module -> thumb screws backed out by (mm)


STEEL = (0.62, 0.64, 0.67)
DARK = (0.18, 0.18, 0.20)
ALU = (0.80, 0.82, 0.85)
BRONZE = (0.72, 0.53, 0.25)
PETG = (0.95, 0.55, 0.10)
SAM = (0.10, 0.25, 0.85)
WHITE = (0.93, 0.93, 0.90)
GREEN = (0.15, 0.6, 0.3)
BLACK = (0.08, 0.08, 0.08)
GLASS = (0.75, 0.88, 0.95)
ORANGE = (0.95, 0.45, 0.05)

STEP_TITLES = {
    1: "Base frame: 2020 base rails, two station cross rails, feet",
    2: "Posts, top rails and cross rails",
    3: "Side plates and the bottom flange bearings",
    4: "Bottom through shafts with their 32T sprockets (front keyed, back set after phasing)",
    5: "Top idlers: axle studs, 6202 bearings, re-bored 32T sprockets",
    6: "Chains: 120 links each, an SA-1 link every 10th pitch on both",
    7: "Drive: jaw coupling, motor plate on standoffs, NEMA 34",
    8: "Gondolas: hang each one on its two SA-1 pivots (shoulder screw, PTFE washer, bushing, locknut)",
    9: "Modules: auger into Sam's mounting plate, then into a gondola at the loading position, pinned",
    10: "Station: actuator on its clevis, U-yoke on the rod, electronics carriage on stub pins (NEMA 11, steel pinion, solenoid, dock magnet), approach fork",
    11: "Dispense: vial on the load cell, hall switches (INDEX, HOME)",
}


def gondola_world(state: State, k: int, pv: np.ndarray) -> np.ndarray:
    """World matrix of gondola k's frame (origin on the front pivot axis)."""
    sw = state.gondola_swing.get(k, 0.0)
    return T(Rx(sw), (0.0, pv[k][0], pv[k][1]))


def station_module(state: State) -> int:
    """Module whose gondola is at the station for this shift (or -1)."""
    pv = K.pivots(state.shift)
    for k in range(N_MODULES):
        if abs(pv[k][0]) < 0.5 and pv[k][1] < Z_BOT:
            return k
    return -1


def electronics_frame(state: State, k_station: int, pv: np.ndarray) -> np.ndarray:
    """Sam's carriage frame (his studio frame as drawn; docked it rises DOCK_RISE): tilting with the module, or
    lowered by the actuator's remaining approach."""
    hinge = np.array([HINGE_X, 0.0, (pv[k_station][1] if k_station >= 0 else K.pivots(K.HOME_SHIFT)[0][1]) + HINGE_Z])
    if state.tilt > 0:
        return T(None, hinge) @ T(Ry(-math.radians(state.tilt))) @ T(None, (0, 0, DOCK_RISE))
    return T(None, hinge - np.array([0, 0, DOCK_EXT - state.ext - DOCK_RISE]))


def actuator_pose(state: State, k_station: int, pv: np.ndarray) -> tuple[np.ndarray, np.ndarray, float]:
    """(base pin B, stub-pin axis P, base-to-P length) in world for the station state. The P16's rod-end hole is
    UFORK_L short of P on the same axis (the U-yoke is rigid on the rod); B sits directly under the docked P."""
    docked = State(shift=state.shift, tilt=0.0, ext=DOCK_EXT)
    P_dock = (electronics_frame(docked, k_station, pv) @ np.array([YOKE_X, 0.0, YOKE_Z, 1.0]))[:3]
    B = P_dock - np.array([0, 0, ACT_RETRACTED + DOCK_EXT + UFORK_L])
    P_ = (electronics_frame(state, k_station, pv) @ np.array([YOKE_X, 0.0, YOKE_Z, 1.0]))[:3]
    return B, P_, float(np.linalg.norm(P_ - B))


def station_base_z() -> float:
    pv0 = K.pivots(K.HOME_SHIFT)[0][1]
    return pv0 + HINGE_Z + YOKE_Z + DOCK_RISE - ACT_RETRACTED - DOCK_EXT - UFORK_L


def placements(state: State | None = None) -> list[Placement]:
    st = state or State()
    out: list[Placement] = []

    def add(*a, **kw):
        out.append(Placement(*a, **kw))

    # 1-2. frame -------------------------------------------------------------
    px = (SIDE_IN - PLATE_T_SIDE - EXT / 2, CHAIN_L - SIDE_IN + PLATE_T_SIDE + EXT / 2)   # post centres (x)
    xr0, xr1 = px[0] - EXT / 2, px[1] + EXT / 2
    for sy in (-1, 1):
        add("ext_x", f"Base rail x {'-' if sy < 0 else '+'}y", T(Ry(math.pi / 2), (xr0, sy * POST_Y, BASE_Z + EXT / 2)), 1, ALU, "frame", (0, 0, -60))
        add("ext_x", f"Top rail x {'-' if sy < 0 else '+'}y", T(Ry(math.pi / 2), (xr0, sy * POST_Y, TOP_Z + EXT / 2)), 2, ALU, "frame", (0, 0, 80))
    for xs, nm in ((STATION_RAIL_X[0], "Station rail (vial)"), (STATION_RAIL_X[1], "Station rail (actuator)")):
        add("ext_y", nm, T(Rx(-math.pi / 2), (xs, -POST_Y + EXT / 2, BASE_Z + EXT / 2)), 1, ALU, "frame", (0, 0, -60))
    for i, x in enumerate(px):
        for sy in (-1, 1):
            add("ext_post", f"Post {'front' if i == 0 else 'back'} {'-' if sy < 0 else '+'}y",
                T(None, (x, sy * POST_Y, BASE_Z + EXT)), 2, ALU, "frame", (0, 0, 120))
            add("foot", f"Leveling foot {i}{sy}", T(None, (x, sy * POST_Y, 0.0)), 1, DARK, "frame", (0, 0, -40))
        add("ext_y", f"Bottom cross rail {'front' if i == 0 else 'back'}", T(Rx(-math.pi / 2), (x, -POST_Y + EXT / 2, BASE_Z + 1.5 * EXT)), 2, ALU, "frame", (0, 0, -40))
        add("ext_y", f"Top cross rail {'front' if i == 0 else 'back'}", T(Rx(-math.pi / 2), (x, -POST_Y + EXT / 2, TOP_Z - EXT / 2)), 2, ALU, "frame", (0, 0, 80))
        for sy in (-1, 1):
            for z, up in ((BASE_Z + 2 * EXT, True), (TOP_Z - EXT, False)):
                # cast corner brackets joining the cross rails to the posts (inside corner)
                R3 = rot((0, -sy, 0), (0, 0, 1 if up else -1))
                add("corner_bracket", f"Corner bracket {i}{sy}{'b' if up else 't'}", T(R3, (x, sy * (POST_Y - EXT / 2), z)), 2, DARK, "frame", (0, 0, 0))

    # 3. side plates + bottom bearings ----------------------------------------
    for back in (False, True):
        x0 = SIDE_IN - PLATE_T_SIDE if not back else CHAIN_L - SIDE_IN
        add("side_plate_back" if back else "side_plate_front", f"Side plate {'back' if back else 'front'}", T(None, (x0, 0, 0)), 3, ALU, "plates",
            (( 60 if back else -60), 0, 0))
        xo = (SIDE_IN - PLATE_T_SIDE) if not back else (CHAIN_L - SIDE_IN + PLATE_T_SIDE)
        R3 = rot((0, -1 if not back else 1, 0), (-1 if not back else 1, 0, 0))   # insert outward, bolt line vertical
        for sy in (-1, 1):
            add("flange_bearing", f"Flange bearing bottom {'back' if back else 'front'} {sy:+d}y", T(R3, (xo, sy * CORNER_Y, Z_BOT)), 3, STEEL, "plates",
                ((40 if back else -40), 0, 0))

    # 4. bottom through shafts + sprockets -----------------------------------
    phi = K.sprocket_angle(st.shift)
    sh0 = SIDE_IN - PLATE_T_SIDE - BRG["OUT"] - 3.0
    for sy in (-1, 1):
        drive = sy > 0
        ln = (CHAIN_L - 2 * sh0) + (DRIVE_EXT if drive else 0.0)
        add("shaft_drive" if drive else "shaft_idle", f"Bottom shaft {'B+ (drive)' if drive else 'B-'}",
            T(Ry(math.pi / 2), (sh0, sy * CORNER_Y, Z_BOT)) @ T(Rz(phi)), 4, STEEL, "drivetrain", (0, 0, -50))
        for back in (False, True):
            add("sprocket_32", f"Sprocket 32T bottom {'back' if back else 'front'} {sy:+d}y", sprocket_frame((sy * CORNER_Y, Z_BOT), phi, back), 4, STEEL, "drivetrain",
                ((25 if back else -25), 0, 0))

    # 5. top idlers ------------------------------------------------------------
    for sy in (-1, 1):
        zc = Z_TOP + st.tension
        for back in (False, True):
            xs = SIDE_IN if not back else CHAIN_L - SIDE_IN
            Rz_ = rot((0, 1, 0), (1, 0, 0)) if not back else rot((0, 1, 0), (-1, 0, 0))
            add("idler_axle", f"Idler axle {'back' if back else 'front'} {sy:+d}y", T(Rz_, (xs, sy * CORNER_Y, zc)), 5, STEEL, "idlers", ((40 if back else -40), 0, 0))
            for kb, xb in enumerate((-14.6, -3.6)):
                xw = xb if not back else CHAIN_L - xb
                add("bearing_6202", f"6202-2RS {'back' if back else 'front'} {sy:+d}y {kb}", T(Rz_, (xw, sy * CORNER_Y, zc)), 5, DARK, "idlers", ((30 if back else -30), 0, 0))
            add("sprocket_32_idler", f"Idler 32T {'back' if back else 'front'} {sy:+d}y", sprocket_frame((sy * CORNER_Y, zc), phi, back), 5, STEEL, "idlers",
                ((25 if back else -25), 0, 0))
            xn = (SIDE_IN - PLATE_T_SIDE) if not back else (CHAIN_L - SIDE_IN + PLATE_T_SIDE)
            add("nut_m10", f"Axle locknut {'back' if back else 'front'} {sy:+d}y", T(rot((0, 1, 0), (-1, 0, 0)) if not back else rot((0, 1, 0), (1, 0, 0)), (xn, sy * CORNER_Y, zc)),
                5, STEEL, "idlers", ((40 if back else -40), 0, 0))

    # 6. chains -------------------------------------------------------------
    frames = K.link_frames(st.shift)
    sa1 = {K.module_link(k) for k in range(N_MODULES)}
    for back in (False, True):
        for j, (mid, ang) in enumerate(frames):
            key = "chain_sa1" if j in sa1 else ("chain_outer" if j % 2 == 0 else "chain_inner")
            add(key, f"{'Back' if back else 'Front'} chain link {j}", chain_frame(mid, ang, back), 6, DARK if key != "chain_sa1" else STEEL, "chains",
                ((15 if back else -15), 0, 0))

    # 7. drive ----------------------------------------------------------------
    xb = CHAIN_L - SIDE_IN + PLATE_T_SIDE                  # back plate's outer face
    c0 = xb + BRG["OUT"] + 6.0
    add("coupling", "Jaw coupling (L-075 class)", T(Ry(math.pi / 2), (c0, CORNER_Y, Z_BOT)), 7, (0.85, 0.75, 0.1), "drive", (60, 0, 0))
    xm = c0 + CPL_L - 25.0 + M34_SHAFT_L                   # motor mounting face
    add("motor_plate", "Motor plate (1/4 in 6061)", T(None, (xm - PLATE_T_SIDE, CORNER_Y, Z_BOT)), 7, ALU, "drive", (100, 0, 0))
    for dy in (-1, 1):
        for dz in (-1, 1):
            add("standoff", f"Motor standoff {dy}{dz}", T(Ry(math.pi / 2), (xb, CORNER_Y + dy * MOTOR_SO[0], Z_BOT + dz * MOTOR_SO[1])), 7, ALU, "drive", (80, 0, 0))
    add("nema34", "NEMA 34 34HS59-6004D-E1000 (StepperOnline STEP)", T(rot((0, 1, 0), (-1, 0, 0)), (xm, CORNER_Y, Z_BOT)), 7, DARK, "drive", (140, 0, 0))

    # 8. gondolas + pivots ------------------------------------------------------
    pv = K.pivots(st.shift)
    k_st = station_module(st) if st.station else -1
    for k in range(N_MODULES):
        G = gondola_world(st, k, pv)
        add("gondola", f"Gondola {k + 1}", G, 8, PETG, "gondolas", (0, 0, 60), k)
        for back in (False, True):
            sgn = -1.0 if back else 1.0
            xt = TAB_X1 if not back else CHAIN_L - TAB_X1
            Rp = rot((0, 1, 0), (sgn, 0, 0))                 # part z -> toward the gondola
            Rn = rot((0, 1, 0), (-sgn, 0, 0))                # part z -> away from the gondola
            p0 = np.array([0.0, pv[k][0], pv[k][1]])
            def at(x):
                return np.array([x if not back else CHAIN_L - x, p0[1], p0[2]])
            add("thrust_washer", f"PTFE washer {k + 1}{'b' if back else 'f'}", T(Rp, at(TAB_X1)), 8, WHITE, "gondolas", (0, 0, 60), k)
            add("sleeve_bearing", f"Flanged bronze bushing {k + 1}{'b' if back else 'f'}", T(Rp, at(END_X1)), 8, BRONZE, "gondolas", (0, 0, 60), k)
            add("thrust_washer", f"PTFE washer (head) {k + 1}{'b' if back else 'f'}", T(Rp, at(END_X1 + 1.5)), 8, WHITE, "gondolas", (0, 0, 60), k)
            add("shoulder_screw", f"Shoulder screw M3x4x8 {k + 1}{'b' if back else 'f'}", T(Rp, at(TAB_X1 + SHOULDER_L)), 8, STEEL, "gondolas", (0, 0, 60), k)
            add("nut_m3", f"M3 nylon-insert locknut {k + 1}{'b' if back else 'f'}", T(Rn, at(TAB_X0)), 8, STEEL, "gondolas", (0, 0, 60), k)

    # 9. modules -------------------------------------------------------------
    for k in range(N_MODULES):
        if k not in st.loaded:
            continue
        G = gondola_world(st, k, pv)
        tilt = st.tilt if k == k_st else 0.0
        slide = (T(None, (0, MODULE_SLIDE * max(0.0, (st.out_frac - 0.25) / 0.75), MODULE_LIFT * min(1.0, 4 * st.out_frac)))
                 if k == st.out_module else np.eye(4))
        S = G @ slide @ sam_in_gondola(tilt)
        add("sam_mounting_plate", f"Mounting plate (Sam, Oct 13) {k + 1}", S, 9, SAM, "modules", (0, 0, 80), k)
        A = S @ AUGER_IN_SAM
        add("armature_tab", f"Steel armature tab {k + 1} (2 mm, laser cut)", S, 9, STEEL, "modules", (0, 0, 80), k)
        add("auger", f"Auger, threaded storage {k + 1}", A, 9, WHITE, "modules", (0, 0, 80), k)
        add("auger_cap", f"Auger cap {k + 1}", A @ T(None, (0, 0, AUGER_LEN)), 9, WHITE, "modules", (0, 0, 80), k)
        for sy in (-1, 1):
            add("insert_m5", f"M5 heat-set insert {k + 1}{'+' if sy > 0 else '-'}", G @ T(rot((1, 0, 0), (0, sy, 0)), (HINGE_X, sy * GON_W / 2, HINGE_Z)), 8, BRONZE, "gondolas", (0, 0, 60), k)
            if k == st.out_module and st.out_frac > 0:
                continue                 # thumb screws are out (in the operator's hand) while the module moves
            back_out = st.thumb_out.get(k, 0.0)
            add("thumb_screw", f"M5 x 16 thumb screw (hinge pin) {k + 1}{'+' if sy > 0 else '-'}",
                G @ T(rot((1, 0, 0), (0, sy, 0)), (HINGE_X, sy * (GON_W / 2 + back_out), HINGE_Z)), 9, STEEL, "modules", (0, sy * 40, 0), k)

    if not st.station:
        return out

    # 10. station ---------------------------------------------------------------
    B, Pp, Lact = actuator_pose(st, k_st, pv)
    zdir = (Pp - B) / np.linalg.norm(Pp - B)
    ydir = np.array([0.0, 1.0, 0.0])
    xdir = np.cross(ydir, zdir)
    Ract = cols(xdir, ydir, zdir)
    add("clevis_bracket", "Actuator base clevis", T(None, B), 10, ALU, "station", (0, 0, -40))
    add("actuator_body", "Actuonix P16-P 150 mm (feedback)", T(Ract, B), 10, (0.25, 0.25, 0.28), "station", (0, 0, -40))
    add("actuator_rod", "Actuonix rod", T(Ract, B + zdir * (Lact - UFORK_L - ACT_RETRACTED)), 10, (0.7, 0.7, 0.72), "station", (0, 0, -40))
    Y = T(Ract, Pp)                                   # yoke frame: on the stub-pin axis, z along the actuator
    add("uyoke_base", "U-yoke crossbar with guide tongue (printed)", Y, 10, PETG, "station", (0, 0, -60))
    for sy in (-1, 1):
        Rm = T(None) if sy > 0 else T(Rz(math.pi))   # part's +y outward
        add("uyoke_arm", f"U-yoke arm {'+' if sy > 0 else '-'}y, 2 mm steel (laser cut)", Y @ T(None, (0, sy * UFORK_Y[0], 0)) @ Rm, 10, STEEL, "station", (0, 0, -60))
        add("yoke_stop" if sy > 0 else "yoke_stop_m", f"Yoke stop block {'+' if sy > 0 else '-'}y (printed)", Y @ T(None, (0, sy * UFORK_Y[0], 0)),
            10, PETG, "station", (0, 0, -60))
    C = electronics_frame(st, k_st, pv)
    add("sam_electronics_carriage", "Electronics carriage (Sam, Oct 13)", C, 10, (0.20, 0.45, 0.95), "station", (0, 0, -60))
    for sy in (-1, 1):
        Rq = T(Rz(math.pi)) if sy < 0 else T(None)
        add("pin_boss" if sy > 0 else "pin_boss_m", f"Stub-pin plate with tail {'+' if sy > 0 else '-'}y (printed)", C @ T(None, (YOKE_X, sy * 18.0, YOKE_Z)),
            10, PETG, "station", (0, 0, -60))
        add("stub_pin", f"Stub pin {'+' if sy > 0 else '-'}y, 4 mm steel", C @ T(None, (YOKE_X, sy * 15.3, YOKE_Z)) @ Rq, 10, STEEL, "station", (0, 0, -60))
        add("eclip", f"E-clip DIN 6799 {'+' if sy > 0 else '-'}y", C @ T(None, (YOKE_X, sy * 22.3, YOKE_Z)) @ T(Rx(-sy * math.pi / 2)), 10, DARK, "station", (0, 0, -60))
    add("nema11", "NEMA 11 11HS18-0674S (auger drive)", C @ T(Ry(math.pi / 2), (NEMA11_X, 0, NEMA11_Z)), 10, DARK, "station", (0, 0, -60))
    add("pinion", "20T steel pinion (KHK SS1-20A)", C @ T(Ry(math.pi / 2), (NEMA11_X + 10.0, 0, NEMA11_Z)), 10, ORANGE, "station", (0, 0, -60))
    add("solenoid", "Solenoid (Adafruit 412)", C @ T(None, (SOL_X, 0, SOL_Z)), 10, DARK, "station", (0, 0, -60))
    add("magnet_bracket", "Dock magnet bracket (printed)", C, 10, PETG, "station", (0, 0, -60))
    add("dock_magnet", "Dock electromagnet Adafruit 3872 (P20/15)", C @ T(None, (DOCK_MAG_XY[0], DOCK_MAG_XY[1], DOCK_MAG_FACE_Z)), 10,
        (0.75, 0.15, 0.15), "station", (0, 0, -60))
    for i, (x, y) in enumerate(LOCPIN_XY):
        add("loc_pin", f"Locating pin {i + 1}, 4 mm (carriage rim)", C @ T(None, (x, y, -18.9 - 5.0)), 10, STEEL, "station", (0, 0, -60))
    add("fork", "Approach fork (printed)", T(None, (HINGE_X + TONGUE_X, TONGUE_Y, FORK_Z)), 10, PETG, "station", (0, 0, -40))
    add("ext_station_post", "Station post (fork)", T(None, (STATION_RAIL_X[1], FORK_POST_Y, BASE_Z + EXT)), 10, ALU, "station", (0, 0, -40))
    add("fork_arm", "Fork arm (printed)", T(None, (HINGE_X + TONGUE_X, TONGUE_Y, FORK_Z)), 10, PETG, "station", (0, 0, -40))

    # station chain hold-down strips (front and back chain), from the side plates
    for back in (False, True):
        xc = 0.0 if not back else CHAIN_L
        add("hold_strip", f"Chain hold-down strip {'back' if back else 'front'} (UHMW)", T(None, (xc, 0.0, HOLD_Z0)), 10, WHITE, "station", ((30 if back else -30), 0, 0))
        for sy in (-1, 1):
            if not back:
                M = T(None, (SIDE_IN, sy * HOLD_BRACKET_Y, HOLD_Z0 + HOLD_STRIP[2] - 9.0))
            else:
                M = T(Rz(math.pi), (CHAIN_L - SIDE_IN, sy * HOLD_BRACKET_Y, HOLD_Z0 + HOLD_STRIP[2] - 9.0))
            add("hold_bracket", f"Hold-down bracket {'back' if back else 'front'} {sy:+d}", M, 10, PETG, "station", ((30 if back else -30), 0, 0))

    # 11. dispense + sensors ----------------------------------------------------
    zv = (pv[k_st][1] if k_st >= 0 else K.pivots(K.HOME_SHIFT)[0][1]) + GON_Z0 - VIAL_GAP - VIAL_H
    add("vial", "Vial, 20 mL", T(None, (VIAL_X, 0.0, zv)), 11, GLASS, "dispense", (0, 0, 60))
    add("vial_funnel", "Catch funnel on the vial (printed)", T(None, (VIAL_X, 0.0, zv + VIAL_H - 4.0)), 11, PETG, "dispense", (0, 0, 60))
    add("vial_cup", "Vial cup on the load cell (printed)", T(Rz(math.pi / 2), (VIAL_X, 0.0, zv - 3.0)), 11, PETG, "dispense", (0, 0, 40))
    add("load_cell", "Load cell 100 g", T(Rz(math.pi / 2), (VIAL_X, -125.0, zv - 3.0 - 12.7)), 11, (0.7, 0.7, 0.75), "dispense", (0, -30, 0))
    add("ext_vial_post", "Station post (vial)", T(None, (VIAL_X, VIAL_POST_Y, BASE_Z + EXT)), 11, ALU, "dispense", (0, 0, -40))
    for nm, xh in (("INDEX", HALL_X[0]), ("HOME", HALL_X[1])):
        zh = (pv[k_st][1] if k_st >= 0 else K.pivots(K.HOME_SHIFT)[0][1]) + GON_Z0 - HALL_GAP - 7.5
        add("hall", f"Hall switch {nm}", T(None, (xh, -29.3, zh)), 11, GREEN, "dispense", (0, 0, -40))
    return out


# ---------------------------------------------------------------- shapes
def _ext(length):
    return lambda: PT.extrusion_2020(length)


def _px():
    return (SIDE_IN - PLATE_T_SIDE - EXT / 2, CHAIN_L - SIDE_IN + PLATE_T_SIDE + EXT / 2)


def _fork_arm() -> cq.Workplane:
    """Printed arm from the fork post (x = STATION_RAIL_X[1], y = FORK_POST_Y) to the fork (frame at the fork's slot centre)."""
    y0, y1 = 14.5, FORK_POST_Y - TONGUE_Y - 10.0
    return cq.Workplane("XY").box(20.0, y1 - y0, 12.0, centered=False).translate((STATION_RAIL_X[1] - (HINGE_X + TONGUE_X) - 10.0, y0, 0.0))


SHAPES = {
    "chain_inner": PT.chain_inner_link,
    "chain_outer": lambda: PT.chain_outer_link(clip=False),
    "chain_sa1": PT.chain_sa1_link,
    "sprocket_32": PT.sprocket_32,
    "sprocket_32_idler": PT.sprocket_32_idler,
    "shaft_idle": lambda: PT.shaft(CHAIN_L - 2 * (SIDE_IN - PLATE_T_SIDE - BRG["OUT"] - 3.0)),
    "shaft_drive": lambda: PT.shaft(CHAIN_L - 2 * (SIDE_IN - PLATE_T_SIDE - BRG["OUT"] - 3.0) + DRIVE_EXT),
    "flange_bearing": PT.flange_bearing,
    "bearing_6202": PT.bearing_6202,
    "idler_axle": PT.idler_axle,
    "coupling": PT.jaw_coupling,
    "nema34": PT.nema34,
    "motor_plate": PT.motor_plate,
    "standoff": lambda: PT.standoff(MOTOR_STANDOFF),
    "ext_x": lambda: PT.extrusion_2020(_px()[1] - _px()[0] + EXT),
    "ext_y": lambda: PT.extrusion_2020(2 * POST_Y - EXT),
    "ext_post": lambda: PT.extrusion_2020(TOP_Z - BASE_Z - EXT),
    "ext_station_post": lambda: PT.extrusion_2020(STATION_POST_H),
    "ext_vial_post": lambda: PT.extrusion_2020(VIAL_POST_H),
    "corner_bracket": PT.corner_bracket,
    "foot": PT.leveling_foot,
    "side_plate_front": lambda: PT.side_plate(False, side_holes(False)),
    "side_plate_back": lambda: PT.side_plate(True, side_holes(True)),
    "gondola": PT.gondola,
    "thrust_washer": PT.thrust_washer,
    "sleeve_bearing": PT.sleeve_bearing,
    "shoulder_screw": PT.shoulder_screw,
    "nut_m3": lambda: PT.locknut(3.0),
    "nut_m10": lambda: PT.locknut(10.0),
    "thumb_screw": PT.thumb_screw,
    "insert_m5": PT.heat_set_insert_m5,
    "sam_mounting_plate": lambda: reference_parts()["sam_mounting_plate"],
    "sam_electronics_carriage": lambda: reference_parts()["sam_electronics_carriage"],
    "auger": lambda: reference_parts()["auger"],
    "auger_cap": lambda: reference_parts()["auger_cap"],
    "clevis_bracket": PT.clevis_bracket,
    "actuator_body": lambda: PT.actuator_p16()[0],
    "actuator_rod": lambda: PT.actuator_p16()[1],
    "uyoke_base": PT.uyoke_base,
    "uyoke_arm": PT.uyoke_arm,
    "yoke_stop": PT.yoke_stop,
    "yoke_stop_m": PT.yoke_stop_m,
    "pin_boss_m": PT.pin_boss_m,
    "stub_pin": PT.stub_pin,
    "pin_boss": PT.pin_boss,
    "eclip": PT.eclip,
    "magnet_bracket": PT.magnet_bracket,
    "dock_magnet": PT.dock_magnet,
    "armature_tab": PT.armature_tab,
    "loc_pin": PT.loc_pin,
    "nema11": PT.nema11_envelope,
    "pinion": PT.pinion_20t,
    "solenoid": PT.solenoid_412,
    "fork": PT.approach_fork,
    "fork_arm": _fork_arm,
    "vial": PT.vial,
    "vial_cup": PT.vial_cup,
    "vial_funnel": PT.vial_funnel,
    "load_cell": PT.load_cell,
    "hall": PT.hall_switch,
    "hold_strip": PT.hold_down_strip,
    "hold_bracket": PT.hold_down_bracket,
}


@lru_cache(None)
def shape(key: str) -> cq.Shape:
    w = SHAPES[key]()
    return w.val() if isinstance(w, cq.Workplane) and len(w.vals()) == 1 else (
        cq.Compound.makeCompound([v for v in w.vals() if isinstance(v, cq.Shape)]) if isinstance(w, cq.Workplane) else w)


def moved(key: str, M: np.ndarray) -> cq.Shape:
    from OCP.gp import gp_Trsf
    from OCP.TopLoc import TopLoc_Location
    tr = gp_Trsf()
    tr.SetValues(*[float(M[i, j]) for i in range(3) for j in range(4)])
    return cq.Shape.cast(shape(key).wrapped.Moved(TopLoc_Location(tr)))
