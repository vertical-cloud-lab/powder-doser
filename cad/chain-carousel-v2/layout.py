"""Where every part goes: the chain solution, the 12 carriages, the frame,
the station and the assembly steps (v2, vertical twin-chain loop).

Each chain is solved exactly for 104 links on four 32T sprockets on a
114.3 x 228.6 mm rectangle of centres: with 32 teeth a 90-degree wrap is
exactly 8 links, so the pins at every tangent point sit in a tooth gap and
the straights are whole pitches (bottom 12, sides 24, top 12). The two chains
are identical, 305 mm apart in x, and every carriage bolts to the same link
number on both, so a carriage only ever moves in the y-z plane.

The loop runs counter-clockwise seen from the back (+x looking toward -x):
along the bottom toward +y, up the +y side, back along the top, down the -y
side. Carriage 1 sits at the station on the bottom straight.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import cadquery as cq
import numpy as np

from params import *  # noqa: F401,F403
import parts as PT

HERE = Path(__file__).resolve().parent
REF = HERE / "reference"            # Sam's Onshape export, the lab auger

ALPHA = 2 * math.pi / N_TEETH
CORNERS = {"B+": (LOOP_Y, Z_BOT), "T+": (LOOP_Y, Z_TOP), "T-": (-LOOP_Y, Z_TOP), "B-": (-LOOP_Y, Z_BOT)}
DRIVE = "B+"                         # NEMA 34 on this shaft, at the back
CARRIAGE_LINK0 = 6                   # carriage 1's A-1 link: on the bottom straight (links 0-11)


@lru_cache(None)
def chain_pins() -> np.ndarray:
    """104 pin centres (y, z), in loop order, starting at the bottom run's
    tangent point under the B- sprocket."""
    b, a = LOOP_B, LOOP_A
    pts = []
    y0, z0 = -b / 2, Z_BOT - R
    pts += [(y0 + k * P, z0) for k in range(LOOP_M)]                                  # bottom straight
    pts += [(b / 2 + R * math.cos(-math.pi / 2 + j * ALPHA), Z_BOT + R * math.sin(-math.pi / 2 + j * ALPHA))
            for j in range(8)]                                                         # round B+
    pts += [(b / 2 + R, Z_BOT + k * P) for k in range(LOOP_N)]                        # up the +y side
    pts += [(b / 2 + R * math.cos(j * ALPHA), Z_TOP + R * math.sin(j * ALPHA)) for j in range(8)]   # round T+
    pts += [(b / 2 - k * P, Z_TOP + R) for k in range(LOOP_M)]                        # top straight
    pts += [(-b / 2 + R * math.cos(math.pi / 2 + j * ALPHA), Z_TOP + R * math.sin(math.pi / 2 + j * ALPHA))
            for j in range(8)]                                                         # round T-
    pts += [(-b / 2 - R, Z_TOP - k * P) for k in range(LOOP_N)]                       # down the -y side
    pts += [(-b / 2 + R * math.cos(math.pi + j * ALPHA), Z_BOT + R * math.sin(math.pi + j * ALPHA))
            for j in range(8)]                                                         # round B-
    pts = np.array(pts)
    gaps = np.linalg.norm(np.roll(pts, -1, axis=0) - pts, axis=1)
    assert len(pts) == N_LINKS and np.allclose(gaps, P, atol=1e-6), (len(pts), gaps.min(), gaps.max())
    return pts


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


def carriage_frame(i: int) -> np.ndarray:
    """Carriage frame on link i: u along the travel, w inward (into the
    loop), x front -> back; origin on the front chain's pitch line mid-way
    between the link's pins."""
    p = chain_pins()
    a, b = p[i % N_LINKS], p[(i + 1) % N_LINKS]
    ty, tz = (b - a) / P
    u, w = (0.0, ty, tz), (0.0, -tz, ty)
    return T(cols(u, w, (1.0, 0.0, 0.0)), (0.0, (a[0] + b[0]) / 2, (a[1] + b[1]) / 2))


def link_frame(i: int, back: bool) -> np.ndarray:
    """Frame of link i in parts.py's link coordinates (x along the chain, y
    radially outward, z along the pins). The A-1 tab is on +z, so z points
    from each chain toward the modules: +x on the front chain, -x on the back."""
    C = carriage_frame(i)
    u, w = C[:3, 0], C[:3, 1]
    if back:
        return T(cols(u, -w, (-1.0, 0.0, 0.0)), C[:3, 3] + (CHAIN_L, 0.0, 0.0))
    return T(cols(-u, -w, (1.0, 0.0, 0.0)), C[:3, 3])


def carriage_links() -> list[int]:
    return [(CARRIAGE_LINK0 + MODULE_LINKS * k) % N_LINKS for k in range(N_MODULES)]


def station_frame() -> np.ndarray:
    """Carriage 1's frame at home: the dispense station."""
    return carriage_frame(CARRIAGE_LINK0)


def to_world(M: np.ndarray, xyz) -> np.ndarray:
    return (M @ np.r_[np.asarray(xyz, float), 1.0])[:3]


STATION_Y = float(station_frame()[1, 3])                 # 4.76: carriage 1's centre on the bottom run


# ---------------------------------------------------------------- side plates
def side_holes(back: bool) -> list[tuple]:
    """(kind, (y, z), size) for every opening in a side plate, world y/z.
    kinds: circle (d), slot (d, length; vertical), tap (M5 tapped)."""
    out = []
    j = BRG["J"] / 2
    lo, hi = TENSION_TRAVEL
    for name, (y, z) in CORNERS.items():
        if name.startswith("B"):
            out.append(("circle", (y, z), (BRG["HOLE"],)))                          # the bearing's rear dome
            for dy in (-j, j):                                                      # bolt line horizontal
                out.append(("circle", (y + dy, z), (BRG["BOLT_D"] + 0.8,)))
        else:                                                                       # top: vertical slots to tension
            zm = z + (lo + hi) / 2
            out.append(("slot", (y, zm), (BRG["HOLE"], BRG["HOLE"] + hi - lo)))
            for dy in (-j, j):
                out.append(("slot", (y + dy, zm), (BRG["BOLT_D"] + 0.8, BRG["BOLT_D"] + 0.8 + hi - lo)))
            for dy in (-10.0, 10.0):                                                # tensioner block screws
                out.append(("tap", (y + dy, z - BRG["DOME_D"] / 2 - 6.0 - 12.0), (5.0,)))
    zs = (90.0, 140.0, 200.0, 320.0, 440.0, 540.0) if back else (200.0, 320.0, 440.0, 540.0)
    for sy in (-1, 1):                                                              # to the posts' slots
        for z in zs:
            out.append(("circle", (sy * POST_Y, z), (5.5,)))
    for dy in (-12.0, 12.0):                                                        # hold-down, into its inserts:
        out.append(("slot", (STATION_Y + dy, Z_RUN + CAR_W0 - CAR_T - 2.0 - 11.0), (5.5, 9.5)))   # +-2 mm to set the lip gap
    if back:                                                                        # NEMA 34, slotted to tension the drive chain
        out.append(("slot", (LOOP_Y, Z_MOTOR), (M34_PILOT_D + 0.5, M34_PILOT_D + 0.5 + 2 * DRIVE_TRAVEL)))
        for dy in (-1, 1):
            for dz in (-1, 1):
                out.append(("slot", (LOOP_Y + dy * M34_BOLT_SQ / 2, Z_MOTOR + dz * M34_BOLT_SQ / 2),
                            (M34_HOLE_D, M34_HOLE_D + 2 * DRIVE_TRAVEL)))
    return out


@lru_cache(None)
def side_plate_part(back: bool) -> cq.Workplane:
    """Side plate in its own frame: x = world y, y = world z, z = world x
    measured from the plate's inner face (front plate: z in [-6.35, 0];
    back plate: z in [0, 6.35])."""
    t = PLATE_T_SIDE
    z0 = 0.0 if back else -t
    p = PT.side_plate(back).translate((0, 0, z0))
    for kind, (y, z), size in side_holes(back):
        if kind in ("circle", "tap"):
            d = size[0] if kind == "circle" else 4.2
            p = p.cut(cq.Workplane("XY").center(y, z).circle(d / 2).extrude(t + 2).translate((0, 0, z0 - 1)))
        elif kind == "slot":
            p = p.cut(cq.Workplane("XY").center(y, z).slot2D(size[1], size[0], angle=90).extrude(t + 2)
                      .translate((0, 0, z0 - 1)))
    return p


# ---------------------------------------------------------------- reference parts
def _read_step_parts(path: Path) -> dict[str, cq.Shape]:
    """Named solids of a STEP assembly, in its world frame."""
    from OCP.IFSelect import IFSelect_RetDone
    from OCP.STEPCAFControl import STEPCAFControl_Reader
    from OCP.TCollection import TCollection_ExtendedString
    from OCP.TDataStd import TDataStd_Name
    from OCP.TDF import TDF_Label, TDF_LabelSequence
    from OCP.TDocStd import TDocStd_Document
    from OCP.TopLoc import TopLoc_Location
    from OCP.XCAFDoc import XCAFDoc_DocumentTool, XCAFDoc_ShapeTool

    doc = TDocStd_Document(TCollection_ExtendedString("d"))
    rd = STEPCAFControl_Reader()
    rd.SetNameMode(True)
    assert rd.ReadFile(str(path)) == IFSelect_RetDone, path
    rd.Transfer(doc)
    st = XCAFDoc_DocumentTool.ShapeTool_s(doc.Main())
    out: dict[str, cq.Shape] = {}

    def name(lab):
        n = TDataStd_Name()
        return n.Get().ToExtString() if lab.FindAttribute(TDataStd_Name.GetID_s(), n) else "part"

    def walk(lab, loc):
        if XCAFDoc_ShapeTool.IsAssembly_s(lab):
            comps = TDF_LabelSequence()
            XCAFDoc_ShapeTool.GetComponents_s(lab, comps)
            for i in range(1, comps.Length() + 1):
                c, ref = comps.Value(i), TDF_Label()
                XCAFDoc_ShapeTool.GetReferredShape_s(c, ref)
                walk(ref, loc.Multiplied(XCAFDoc_ShapeTool.GetLocation_s(c)))
        else:
            out[name(lab)] = cq.Shape.cast(XCAFDoc_ShapeTool.GetShape_s(lab).Moved(loc))

    roots = TDF_LabelSequence()
    st.GetFreeShapes(roots)
    for i in range(1, roots.Length() + 1):
        walk(roots.Value(i), TopLoc_Location())
    return out


@lru_cache(None)
def reference_parts() -> dict[str, cq.Workplane]:
    """Sam's Oct 8 mounting plate and electronics carriage (his Onshape Part
    Studio), and the lab's threaded-storage auger + cap (PR #170). Each in its
    own frame: Sam's parts in his studio frame (hinge axis = his y axis at
    x = z = 0), auger along +z from its outlet end."""
    out = {}
    sam = _read_step_parts(REF / "sam-oct8-mounting-plate-and-carriage.step")
    out["sam_mounting_plate"] = cq.Workplane("XY").add(sam["Mounting Plate"])
    out["sam_electronics_carriage"] = cq.Workplane("XY").add(sam["Carriage"])
    aug = _read_step_parts(REF / "auger-threaded-storage.step")
    out["auger"] = cq.Workplane("XY").add(next(iter(aug.values())))
    cap = _read_step_parts(REF / "auger-cap-threaded.step")
    out["auger_cap"] = cq.Workplane("XY").add(next(iter(cap.values())))
    return out


SAM_IN_CARRIAGE = T(cols((0, 0, 1), (1, 0, 0), (0, 1, 0)), (0.0, HINGE_W, HINGE_X))   # his x -> x, y -> u, z -> w


def sam_frame(carriage_M: np.ndarray, tilt_deg: float = 0.0) -> np.ndarray:
    """Sam's studio frame on a carriage. Positive tilt lifts the cap end
    into the loop (outlet down), about the hinge."""
    return carriage_M @ SAM_IN_CARRIAGE @ T(Ry(-math.radians(tilt_deg)))


# ---------------------------------------------------------------- placements
@dataclass
class Placement:
    key: str
    name: str
    M: np.ndarray
    step: int
    color: tuple = (0.6, 0.6, 0.6)
    group: str = ""
    explode: tuple = (0.0, 0.0, 0.0)      # world offset used by the step renders


STEEL = (0.62, 0.64, 0.67)
DARK = (0.18, 0.18, 0.2)
ALU = (0.80, 0.82, 0.85)
PLATE_ALU = (0.70, 0.72, 0.76)
PETG = (0.16, 0.36, 0.78)
ORANGE = (0.95, 0.55, 0.12)
SAM = (0.10, 0.25, 0.85)
WHITE = (0.97, 0.97, 0.97)
BLANK = (0.88, 0.88, 0.84)
BRASS = (0.80, 0.65, 0.25)
GREEN = (0.10, 0.50, 0.25)
RED = (0.85, 0.12, 0.10)
CAST = (0.42, 0.44, 0.47)

STEPS = {
    1: "Base frame: rails, corner brackets, leveling feet",
    2: "Posts and top frame",
    3: "Side plates onto the posts",
    4: "Flange bearings and top-shaft tensioners on the side plates",
    5: "Corner shafts with their sprockets (set screws loose)",
    6: "NEMA 34 on the back plate, 15T sprockets, drive chain",
    7: "Chains: 12 A-1 links per chain, close both loops",
    8: "Carriages across both chains; phase and tension",
    9: "Station: hold-downs and hall switches",
    10: "Modules: Sam's plate, auger and cap on every carriage",
    11: "Electronics board: supply, driver, Pi, interface board, e-stop",
}

X_FRONT_OUT = -SIDE_GAP - PLATE_T_SIDE          # front plate's outer face
X_BACK_OUT = CHAIN_L + SIDE_GAP + PLATE_T_SIDE  # back plate's outer face
X_POST = (X_FRONT_OUT - EXT / 2, X_BACK_OUT + EXT / 2)
RAIL_X0, RAIL_X1 = X_FRONT_OUT - EXT, X_BACK_OUT + EXT
SHAFT_X0 = X_FRONT_OUT - BRG["OUT"]
SHAFT_L = X_BACK_OUT + BRG["OUT"] - SHAFT_X0      # 404.7: flush with both bearings' inserts
X_DRV = X_BACK_OUT + BRG["OUT"] + 7.5            # drive chain's centre plane, 2 mm clear of the bearing
DRIVE_EXTRA = X_DRV + LTB15 - TOOTH_W / 2 - (X_BACK_OUT + BRG["OUT"])   # B+ shaft's stub for the 15T


@lru_cache(None)
def drive_chain_pins() -> np.ndarray:
    """44 pin centres (y, z) of the drive chain: two equal 15T sprockets,
    C = 14.5 pitches, solved like v1's loop (14-link spans, 8 links on each
    sprocket). The stub sprocket (B+ shaft) is at the top."""
    r = PD15 / 2
    al = 2 * math.pi / N15
    ha = al / 2
    xd, xi = C_DRIVE / 2, -C_DRIVE / 2           # local x: motor (-) -> stub (+)
    A = np.array([xd, r])
    B = np.array([xi + P / 2, r * math.cos(ha)])
    D = np.array([xi, -r])
    E = np.array([xd - P / 2, -r * math.cos(ha)])
    span = (DRIVE_LINKS - 16) // 2
    pts = [A + (B - A) * i / span for i in range(span)]
    pts += [np.array([xi + r * math.cos(math.pi / 2 - ha + k * al), r * math.sin(math.pi / 2 - ha + k * al)]) for k in range(8)]
    pts += [D + (E - D) * i / span for i in range(span)]
    pts += [np.array([xd + r * math.cos(-math.pi / 2 - ha + k * al), r * math.sin(-math.pi / 2 - ha + k * al)]) for k in range(8)]
    pts = np.array(pts)
    gaps = np.linalg.norm(np.roll(pts, -1, axis=0) - pts, axis=1)
    assert len(pts) == DRIVE_LINKS and np.allclose(gaps, P, atol=2e-3), (len(pts), gaps.min(), gaps.max())
    zc = (Z_BOT + Z_MOTOR) / 2
    return np.column_stack([LOOP_Y + pts[:, 1], zc + pts[:, 0]])


def bracket(corner, n1, n2) -> np.ndarray:
    """Corner bracket: leg on the surface with outward normal n1, the other
    leg against the surface with outward normal n2, at the corner point."""
    n1, n2 = np.asarray(n1, float), np.asarray(n2, float)
    return T(cols(n2, np.cross(n1, n2), n1), corner)


def placements(tilt_deg: float = 0.0) -> list[Placement]:
    out: list[Placement] = []
    add = out.append
    zr0, zr1 = Z_BASE, Z_BASE + EXT                       # base rails
    zt0, zt1 = Z_TOP_RAIL, Z_TOP_RAIL + EXT               # top rails
    L_x, L_y = RAIL_X1 - RAIL_X0, 2 * POST_Y - EXT        # rails along x run full length; along y fit between
    L_post = zt0 - zr1

    # 1. base frame
    for sy in (-1, 1):
        add(Placement("ext_x", f"Base rail {'-y' if sy < 0 else '+y'}", T(Ry(math.pi / 2), (RAIL_X0, sy * POST_Y, (zr0 + zr1) / 2)),
                      1, ALU, "frame", (0, sy * 40, -40)))
    for xp in X_POST:
        add(Placement("ext_y", f"Base cross rail {'front' if xp < 0 else 'back'}",
                      T(Rx(-math.pi / 2), (xp, -L_y / 2, (zr0 + zr1) / 2)), 1, ALU, "frame", (0, 0, -60)))
    for sx in (-1, 1):
        for sy in (-1, 1):
            add(Placement("foot", "Leveling foot", T(None, (sx * (L_x / 2 - 15) + (RAIL_X0 + RAIL_X1) / 2, sy * POST_Y, 0.0)),
                          1, DARK, "frame", (0, 0, -80)))
            add(Placement("tnut_m5", "T-nut (foot)", T(Rx(math.pi), (sx * (L_x / 2 - 15) + (RAIL_X0 + RAIL_X1) / 2, sy * POST_Y,
                                                                    zr0 + 2.2)), 1, STEEL, "frame", (0, 0, -80)))
    # 2. posts and top frame
    for xp in X_POST:
        for sy in (-1, 1):
            add(Placement("ext_post", "Post", T(None, (xp, sy * POST_Y, zr1)), 2, ALU, "frame", (0, sy * 30, 0)))
            sx = 1 if xp < 0 else -1           # inner side (toward the loop) along x
            # post foot: one bracket on the long rail's top (inner x side), one on the cross rail's top (inner y side)
            add(Placement("corner_bracket", "Corner bracket (post foot)",
                          bracket((xp + sx * EXT / 2, sy * POST_Y, zr1), (0, 0, 1), (sx, 0, 0)), 2, ALU, "frame", (0, 0, 40)))
            add(Placement("corner_bracket", "Corner bracket (post foot)",
                          bracket((xp, sy * (POST_Y - EXT / 2), zr1), (0, 0, 1), (0, -sy, 0)), 2, ALU, "frame", (0, 0, 40)))
            # post head: the same under the top rails
            add(Placement("corner_bracket", "Corner bracket (post head)",
                          bracket((xp + sx * EXT / 2, sy * POST_Y, zt0), (0, 0, -1), (sx, 0, 0)), 2, ALU, "frame", (0, 0, 60)))
            add(Placement("corner_bracket", "Corner bracket (post head)",
                          bracket((xp, sy * (POST_Y - EXT / 2), zt0), (0, 0, -1), (0, -sy, 0)), 2, ALU, "frame", (0, 0, 60)))
    for sy in (-1, 1):
        add(Placement("ext_x", f"Top rail {'-y' if sy < 0 else '+y'}", T(Ry(math.pi / 2), (RAIL_X0, sy * POST_Y, (zt0 + zt1) / 2)),
                      2, ALU, "frame", (0, sy * 30, 80)))
    for xp in X_POST:
        add(Placement("ext_y", f"Top cross rail {'front' if xp < 0 else 'back'}",
                      T(Rx(-math.pi / 2), (xp, -L_y / 2, (zt0 + zt1) / 2)), 2, ALU, "frame", (0, 0, 80)))
    # 3. side plates (front: inner face at x = -30; back: at x = L + 30), screwed to the posts
    Rside = cols((0, 1, 0), (0, 0, 1), (1, 0, 0))          # plate x -> world y, y -> z, z -> x
    add(Placement("side_plate_front", "Side plate, front (1/4in 6061)", T(Rside, (-SIDE_GAP, 0, 0)), 3, PLATE_ALU, "plates",
                  (-70, 0, 0)))
    add(Placement("side_plate_back", "Side plate, back (1/4in 6061)", T(Rside, (CHAIN_L + SIDE_GAP, 0, 0)), 3, PLATE_ALU,
                  "plates", (70, 0, 0)))
    for back in (False, True):
        xi = CHAIN_L + SIDE_GAP if back else -SIDE_GAP     # inner face
        sgn = 1 if back else -1                            # outward
        for kind, (y, z), size in side_holes(back):
            if kind == "circle" and abs(abs(y) - POST_Y) < 0.1:
                # M5 button head on the plate's inner face, into a T-nut in the post's slot
                add(Placement("m5x12_bhcs", "Side plate screw M5x12", T(Ry(-sgn * math.pi / 2), (xi, y, z)), 3, DARK, "plates",
                              (sgn * 90, 0, 0)))
                add(Placement("tnut_m5", "T-nut (side plate)", T(Ry(sgn * math.pi / 2), (xi + sgn * (PLATE_T_SIDE + 2.2), y, z)),
                              3, STEEL, "plates", (sgn * 110, 0, 0)))
    # 4. bearings (bolt line horizontal) and tensioners under the top ones
    for back in (False, True):
        xo = X_BACK_OUT if back else X_FRONT_OUT
        Rb = cols((0, 0, -1), (0, 1, 0), (1, 0, 0)) if back else cols((0, 0, 1), (0, 1, 0), (-1, 0, 0))
        sgn = 1 if back else -1
        for name, (y, z) in CORNERS.items():
            add(Placement("flange_bearing", f"Flange bearing {name} {'back' if back else 'front'}", T(Rb, (xo, y, z)), 4, CAST,
                          "bearings", (sgn * 60, 0, 0)))
            for dy in (-BRG["J"] / 2, BRG["J"] / 2):
                add(Placement("bolt_m6x25", "Bearing bolt 1/4-20 x 1in", T(Ry(sgn * math.pi / 2), (xo + sgn * BRG["T"], y + dy, z)), 4,
                              DARK, "bearings", (sgn * 90, 0, 0)))
                add(Placement("nut_m6", "Bearing nut 1/4-20 (nylock)", T(Ry(sgn * math.pi / 2), (xo - sgn * (PLATE_T_SIDE + 5.0), y + dy, z)),
                              4, STEEL, "bearings", (-sgn * 40, 0, 0)))
            if name.startswith("T"):
                Rt = cols((0, 1, 0), (0, 0, 1), (1, 0, 0)) if back else cols((0, -1, 0), (0, 0, 1), (-1, 0, 0))
                zb = z - BRG["DOME_D"] / 2 - 6.0                          # block's top: 6 mm under the front dome
                add(Placement("tensioner_block", f"Tensioner block {name} {'back' if back else 'front'} (printed)",
                              T(Rt, (xo, y, zb)), 4, ORANGE, "bearings", (sgn * 40, 0, -20)))
                for dy in (-10.0, 10.0):
                    add(Placement("m5x10_shcs", "Tensioner block screw M5x10", T(Ry(sgn * math.pi / 2), (xo + sgn * 4.0, y + dy, zb - 12)),
                                  4, DARK, "bearings", (sgn * 70, 0, -20)))
                xs = xo + sgn * 7.0
                add(Placement("m5x30_shcs", "Jack screw M5x30", T(cols((0, 1, 0), (1, 0, 0), (0, 0, -1)), (xs, y, z - BRG["DOME_D"] / 2 - 30.0)),
                              4, DARK, "bearings", (sgn * 40, 0, -50)))
                add(Placement("nut_m5", "Jack screw nut", T(None, (xs, y, zb - 8.4)), 4, STEEL, "bearings", (sgn * 40, 0, -20)))
    for name, (y, z) in CORNERS.items():
        key = "shaft_drive" if name == DRIVE else "shaft"
        add(Placement(key, f"Shaft {name} (1/2in)", T(Ry(math.pi / 2), (SHAFT_X0, y, z)), 5, STEEL, "shafts", (-120, 0, 0)))
    # 5. shafts (above) and sprockets: hub outward; any multiple of 11.25 deg puts a tooth gap on every pin
    for name, (y, z) in CORNERS.items():
        add(Placement("sprocket_32", f"Sprocket 35B32 {name} front", T(cols((0, 1, 0), (0, 0, 1), (1, 0, 0)), (0.0, y, z)), 5, STEEL,
                      "sprockets", (60, 0, 0)))
        add(Placement("sprocket_32", f"Sprocket 35B32 {name} back", T(cols((0, 1, 0), (0, 0, -1), (-1, 0, 0)), (CHAIN_L, y, z)), 5,
                      STEEL, "sprockets", (-60, 0, 0)))
    # 6. NEMA 34 inside the frame on the back plate's inner face; #35 drive chain up to the B+ shaft's stub
    Rm = cols((0, 1, 0), (0, 0, 1), (1, 0, 0))              # motor z (shaft) -> +x, through the back plate
    xi_b = CHAIN_L + SIDE_GAP
    add(Placement("nema34", "NEMA 34 34HS59-6004D-E1000", T(Rm, (xi_b, LOOP_Y, Z_MOTOR)), 6, DARK, "drive", (-170, 0, 0)))
    for dy in (-1, 1):
        for dz in (-1, 1):
            p = (LOOP_Y + dy * M34_BOLT_SQ / 2, Z_MOTOR + dz * M34_BOLT_SQ / 2)
            add(Placement("m5x25_shcs", "Motor bolt M5x25", T(Ry(math.pi / 2), (X_BACK_OUT, *p)), 6, DARK, "drive", (80, 0, 0)))
            add(Placement("nut_m5", "Motor nut M5 (nylock)", T(Ry(-math.pi / 2), (xi_b - 12.0, *p)), 6, STEEL, "drive", (-120, 0, 0)))
    Rs15 = cols((0, 1, 0), (0, 0, -1), (-1, 0, 0))          # hub outward (+x)
    add(Placement("sprocket_15_motor", "Drive sprocket 15T on the motor (35BS15H-1/2 bored 14 mm)",
                  T(Rs15 @ Rz(-math.pi / N15), (X_DRV, LOOP_Y, Z_MOTOR)), 6,
                  STEEL, "drive", (60, 0, 0)))
    add(Placement("sprocket_15_shaft", "Drive sprocket 15T on the B+ shaft (35BS15H-5/8)", T(Rs15, (X_DRV, LOOP_Y, Z_BOT)), 6, STEEL,
                  "drive", (80, 0, 0)))
    dp = drive_chain_pins()
    for i in range(DRIVE_LINKS):
        a_, b_ = dp[i], dp[(i + 1) % DRIVE_LINKS]
        ty, tz = (b_ - a_) / P
        Ml = T(cols((0, -ty, -tz), (0, tz, -ty), (1, 0, 0)), (X_DRV, (a_[0] + b_[0]) / 2, (a_[1] + b_[1]) / 2))
        key = "chain_outer" if i % 2 == 0 else "chain_inner"
        add(Placement(key, "Drive chain link", Ml, 6, STEEL, "drive", (80, 0, 0)))
    # 7. chains: every 8th link an A-1 attachment connecting link, same links on both chains
    cl = set(carriage_links())
    for back in (False, True):
        for i in range(N_LINKS):
            M = link_frame(i, back)
            ex = (60 if not back else -60, 0, 0)
            if i in cl:
                add(Placement("chain_a1", f"A-1 attachment connecting link ({'back' if back else 'front'})", M, 7, STEEL, "chain", ex))
            elif i % 2 == 0:
                add(Placement("chain_outer", "Outer link", M, 7, STEEL, "chain", ex))
            else:
                add(Placement("chain_inner", "Inner link", M, 7, STEEL, "chain", ex))
    # 8. carriages
    for k, li in enumerate(carriage_links()):
        C = carriage_frame(li)
        out_dir = tuple(-C[:3, 1] * 60)                    # lift outward, away from the loop
        add(Placement("carriage", f"Carriage {k + 1}", C, 8, PETG, "carriages", out_dir))
        for xa in (A1_HOLE_C, CHAIN_L - A1_HOLE_C):
            add(Placement("m3x6_bhcs", f"Carriage screw M3x6 {k + 1}", C @ T(Rx(-math.pi / 2), (0, CAR_W0 + PLATE_T, xa)), 8, DARK,
                          "carriages", out_dir))
            add(Placement("insert_m3", f"Heat-set insert M3 {k + 1}", C @ T(Rx(math.pi / 2), (0, CAR_W0, xa)), 8, BRASS, "carriages",
                          out_dir))
        mz = CAR_W0 - 0.3 - MAGNET_H
        add(Placement("magnet", f"Index magnet {k + 1}", C @ T(Rx(-math.pi / 2), (0, mz, CAR_X0 + 7.0)), 8, STEEL, "carriages", out_dir))
        if k == 0:
            add(Placement("magnet", "Home magnet", C @ T(Rx(-math.pi / 2), (0, mz, CAR_X1 - 7.0)), 8, STEEL, "carriages", out_dir))
    # 9. station: hold-downs over both tongues, hall switches in their lips
    S = station_frame()
    HDf = T(cols((0, 1, 0), (0, 0, 1), (1, 0, 0)), (-SIDE_GAP, STATION_Y, Z_RUN))
    HDb = T(cols((0, -1, 0), (0, 0, 1), (-1, 0, 0)), (CHAIN_L + SIDE_GAP, STATION_Y, Z_RUN))
    tz = CAR_W0 + HOLD_DOWN_GAP
    zc = SIDE_GAP + CAR_X0 + 7.0
    Rsw = cols((1, 0, 0), (0, 0, -1), (0, 1, 0))
    for HD, nm, sgn in ((HDf, "front, INDEX", -1), (HDb, "back, HOME", 1)):
        add(Placement("hold_down", f"Hold-down ({nm.split(',')[0]}, printed)", HD, 9, ORANGE, "station", (0, 0, 60)))
        add(Placement("hall_switch", f"Hall switch US5881 ({nm.split(', ')[1]})", HD @ T(Rsw, (0, tz + 0.8, zc)), 9, DARK, "station",
                      (0, 0, 90)))
        for dy in (-12.0, 12.0):
            p = to_world(HD, (dy, CAR_W0 - CAR_T - 2.0 - 11.0, 0.0))
            xo = X_BACK_OUT if sgn > 0 else X_FRONT_OUT
            add(Placement("m5x16_shcs", "Hold-down screw M5x16", T(Ry(sgn * math.pi / 2), (xo, p[1], p[2])), 9, DARK, "station",
                          (sgn * 60, 0, 0)))
            add(Placement("insert_m5", "M5 heat-set insert (hold-down)", HD @ T(None, (dy, CAR_W0 - CAR_T - 2.0 - 11.0, 0.0)), 9, BRASS,
                          "station", (0, 0, 60)))
    # 10. modules: module 1 is the lab's (real auger); 2-12 carry a printed auger blank
    for k, li in enumerate(carriage_links()):
        C = carriage_frame(li)
        Ms = sam_frame(C, tilt_deg if k == 0 else 0.0)
        out_dir = tuple(C[:3, 1] * 80)                     # lift inward
        add(Placement("sam_mounting_plate", f"Mounting plate (Sam, Oct 8) {k + 1}", Ms, 10, SAM, "modules", out_dir))
        Ma = Ms @ T(Ry(math.pi / 2), (AUGER_Z0_XS, 0, 0))
        if k == 0:
            add(Placement("auger", "Auger, threaded storage (lab) 1", Ma, 10, WHITE, "modules", out_dir))
        else:
            add(Placement("auger_blank", f"Auger blank (printed) {k + 1}", Ma, 10, BLANK, "modules", out_dir))
        add(Placement("auger_cap", f"Auger cap (lab) {k + 1}", Ma @ T(None, (0, 0, AUGER_LEN)), 10, WHITE, "modules", out_dir))
        for su in (-1, 1):
            add(Placement("m5x10_fhcs", f"Hinge pin M5x10 flat head {k + 1}", C @ T(Ry(su * math.pi / 2), (su * (LUG_U + LUG_T), HINGE_W, HINGE_X)),
                          10, DARK, "modules", out_dir))
        if k == 0:
            add(Placement("sam_electronics_carriage", "Electronics carriage (Sam, Oct 8), docked at the station",
                          sam_frame(C, tilt_deg), 10, (0.20, 0.45, 0.95), "modules", (0, 0, -90)))
    # 11. electronics board beside the rig (on the bench, behind it on the +y side)
    bx, by = CHAIN_L + 330.0, 260.0
    add(Placement("board_panel", "Electronics board (1/4in plywood)", T(None, (bx, by, 0.0)), 11, (0.80, 0.68, 0.48), "elec", (0, 80, 0)))
    add(Placement("lrs350", "Mean Well LRS-350-48", T(None, (bx - 90, by + 70, 6.35)), 11, ALU, "elec", (0, 80, 60)))
    add(Placement("cl86t", "CL86T closed-loop driver", T(None, (bx + 105, by + 55, 6.35)), 11, DARK, "elec", (0, 80, 60)))
    add(Placement("raspberry_pi", "Raspberry Pi", T(None, (bx - 120, by - 85, 6.35 + 6)), 11, GREEN, "elec", (0, 80, 60)))
    add(Placement("perfboard", "Interface board (74AHCT125, pull-ups)", T(None, (bx - 20, by - 85, 6.35 + 6)), 11, GREEN, "elec",
                  (0, 80, 60)))
    add(Placement("estop", "E-stop", T(None, (bx + 150, by - 90, 6.35)), 11, RED, "elec", (0, 80, 60)))
    return out


BUILDERS = {
    "ext_x": lambda: PT.extrusion_2020(RAIL_X1 - RAIL_X0),
    "ext_y": lambda: PT.extrusion_2020(2 * POST_Y - EXT),
    "ext_post": lambda: PT.extrusion_2020(Z_TOP_RAIL - Z_BASE - EXT),
    "corner_bracket": PT.corner_bracket,
    "foot": PT.leveling_foot,
    "side_plate_front": lambda: side_plate_part(False),
    "side_plate_back": lambda: side_plate_part(True),
    "flange_bearing": PT.flange_bearing,
    "shaft": lambda: PT.shaft(SHAFT_L),
    "shaft_drive": lambda: PT.shaft(SHAFT_L + DRIVE_EXTRA),
    "tensioner_block": PT.tensioner_block,
    "sprocket_32": PT.sprocket_32,
    "sprocket_15_shaft": PT.sprocket_15_shaft,
    "sprocket_15_motor": PT.sprocket_15_motor,
    "nema34": PT.nema34,
    "chain_a1": PT.chain_a1_link,
    "chain_outer": PT.chain_outer_link,
    "chain_inner": PT.chain_inner_link,
    "carriage": PT.carriage,
    "insert_m3": PT.heat_insert_m3,
    "insert_m5": lambda: cq.Workplane("XY").circle(3.5).circle(2.5).extrude(7.0),
    "magnet": PT.magnet,
    "hold_down": PT.hold_down,
    "hall_switch": PT.hall_switch,
    "auger_blank": PT.auger_blank,
    "m3x6_bhcs": lambda: PT.shcs(3, 6, "button"),
    "m5x12_bhcs": lambda: PT.shcs(5, 12, "button"),
    "m5x10_fhcs": lambda: PT.shcs(5, 10, "flat"),
    "m5x16_shcs": lambda: PT.shcs(5, 16),
    "m5x30_shcs": lambda: PT.shcs(5, 30),
    "bolt_m6x25": lambda: PT.shcs(6, 25),
    "nut_m6": lambda: PT.hexnut(6),
    "m5x25_shcs": lambda: PT.shcs(5, 25),
    "m5x10_shcs": lambda: PT.shcs(5, 10),
    "nut_m5": lambda: PT.hexnut(5),
    "tnut_m5": PT.tnut_m5,
    "board_panel": PT.board_panel,
    "lrs350": PT.lrs350,
    "cl86t": PT.cl86t,
    "raspberry_pi": PT.raspberry_pi,
    "perfboard": PT.perfboard,
    "estop": PT.estop,
    "sam_mounting_plate": lambda: reference_parts()["sam_mounting_plate"],
    "sam_electronics_carriage": lambda: reference_parts()["sam_electronics_carriage"],
    "auger": lambda: reference_parts()["auger"],
    "auger_cap": lambda: reference_parts()["auger_cap"],
}


@lru_cache(None)
def shape(key: str) -> cq.Shape:
    w = BUILDERS[key]()
    vals = w.vals()
    return vals[0] if len(vals) == 1 else cq.Compound.makeCompound(vals)


def moved(key: str, M: np.ndarray) -> cq.Shape:
    from OCP.gp import gp_Trsf
    from OCP.TopLoc import TopLoc_Location
    tr = gp_Trsf()
    tr.SetValues(*[float(v) for v in M[:3, :].ravel()])
    return cq.Shape.cast(shape(key).wrapped.Moved(TopLoc_Location(tr)))


if __name__ == "__main__":
    p = chain_pins()
    print("pins:", len(p), "; carriage links:", carriage_links(), "; station y =", round(STATION_Y, 2))
    print("loop pitch-line box: y +-%.1f, z %.1f-%.1f" % (LOOP_Y + R, Z_BOT - R, Z_TOP + R))
    print("shaft clearance to the gear: %.2f mm" % SHAFT_CLEAR)
    pl = placements()
    from collections import Counter
    print(len(pl), "placements;", Counter(x.key for x in pl).most_common(14))
