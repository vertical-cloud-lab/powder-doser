"""Where every part goes: the chain solution, the 12 carriages, the station
and the assembly steps.

The chain is solved exactly for 96 links on two 19T sprockets: with the
drive sprocket's pin at 90 deg (top) and C = 38.5 pitches, both free spans
are 38 links and each sprocket carries 10 (the polygon effect tilts each
span by 0.39 mm over 362 mm). The loop runs counter-clockwise seen from
above: top span drive -> idler, around the idler, bottom (front) span back.

Carriage 1 sits at the station, on the front span near x = 0. Every 8th link
is an A-1 attachment connecting link; carriage k bolts to the k-th of them.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

import cadquery as cq
import numpy as np

from params import *  # noqa: F401,F403
import parts as PT

HERE = Path(__file__).resolve().parent
REF = HERE / "reference"            # Sam's Onshape export, the lab auger

C = 38.5 * P                         # centre distance that closes 96 links exactly
X_DRIVE, X_IDLER = C / 2, -C / 2
R = PD / 2
ALPHA = 2 * math.pi / N_TEETH
CARRIAGE_LINK0 = 66                  # carriage 1's A-1 link (front span, near x = 0)


def chain_pins() -> np.ndarray:
    """96 pin centres (x, y), in loop order, starting at the drive's top pin."""
    ha = ALPHA / 2
    A = np.array([X_DRIVE, R])
    B = np.array([X_IDLER + P / 2, R * math.cos(ha)])
    D = np.array([X_IDLER, -R])
    E = np.array([X_DRIVE - P / 2, -R * math.cos(ha)])
    pts = [A + (B - A) * i / 38 for i in range(38)]
    a0 = math.pi / 2 - ha
    pts += [np.array([X_IDLER + R * math.cos(a0 + k * ALPHA), R * math.sin(a0 + k * ALPHA)]) for k in range(10)]
    pts += [D + (E - D) * i / 38 for i in range(38)]
    a1 = -math.pi / 2 - ha
    pts += [np.array([X_DRIVE + R * math.cos(a1 + k * ALPHA), R * math.sin(a1 + k * ALPHA)]) for k in range(10)]
    pts = np.array(pts)
    gaps = np.linalg.norm(np.roll(pts, -1, axis=0) - pts, axis=1)
    assert len(pts) == N_LINKS and np.allclose(gaps, P, atol=2e-3), (len(pts), gaps.min(), gaps.max())
    return pts


def T(R3=None, t=(0.0, 0.0, 0.0)) -> np.ndarray:
    M = np.eye(4)
    if R3 is not None:
        M[:3, :3] = R3
    M[:3, 3] = t
    return M


def Rz(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])


def Rx(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[1, 0, 0], [0, c, -s], [0, s, c]])


def Ry(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])


def link_frame(i: int, z: float = CHAIN_Z) -> np.ndarray:
    """Frame of link i: origin mid-way between pins i and i+1, y outward
    (right of travel: the loop runs counter-clockwise), z up, so x points
    against the travel."""
    p = chain_pins()
    a, b = p[i], p[(i + 1) % N_LINKS]
    t = (b - a) / np.linalg.norm(b - a)
    return T(Rz(math.atan2(t[1], t[0]) + math.pi), ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2, z))


def carriage_links() -> list[int]:
    return [(CARRIAGE_LINK0 + MODULE_LINKS * k) % N_LINKS for k in range(N_MODULES)]


def station_frame() -> np.ndarray:
    """Carriage 1's frame (z = 0 on the deck): the dispense station."""
    return link_frame(CARRIAGE_LINK0, 0.0)


def to_world(M: np.ndarray, xyz) -> np.ndarray:
    return (M @ np.r_[np.asarray(xyz, float), 1.0])[:3]


# ---------------------------------------------------------------- deck
def deck_holes() -> list[tuple[str, tuple, tuple]]:
    """(kind, centre, size) for every opening in the deck, world x/y."""
    S = station_frame()
    holes = [("circle", (X_DRIVE, 0.0), (80.0,)),                      # drive sprocket hub
             ("slot", (X_IDLER - 3.0, 0.0), (22.0, 22.0 + TENSION_TRAVEL))]
    for sx in (-1, 1):                                                  # motor plate, countersunk
        for sy in (-1, 1):
            holes.append(("csk", (X_DRIVE + sx * (MOTOR_PLATE / 2 - 10), sy * (MOTOR_PLATE / 2 - 10)), (5.5,)))
    for sy in (-1, 1):                                                  # idler slider clamps
        holes.append(("csk", (X_IDLER - 22.0, sy * 18.0), (5.5,)))
    # station reach-through, in the carriage frame -> world
    c = to_world(S, (0, (CUT_Y[0] + CUT_Y[1]) / 2, 0))
    holes.append(("rect", (c[0], c[1]), (2 * CUT_X + 6, CUT_Y[1] - CUT_Y[0] + 6)))
    for x in (-25.0, 25.0):                                             # hall sensors (home -X, index +X)
        h = to_world(S, (x, CAR_Y0 + 40, 0))
        holes.append(("circle", (h[0], h[1]), (11.8,)))
    for x in (-43.0, -19.0, 19.0, 43.0):                                # hold-down blocks
        h = to_world(S, (x, CAR_Y0 + CAR_L - 1 + HD_HOLE_DY, 0))
        holes.append(("circle", (h[0], h[1]), (4.5,)))
    for y in (-9.0, 9.0):                                               # tensioner block, from above
        holes.append(("csk4", (X_IDLER + 42.0, y), (4.5,)))
    # deck to frame: M5 countersunk into T-nuts along both long rails and the cross members
    for x in (-450.0, -280.0, -130.0, 80.0, 183.0, 300.0, 450.0):
        for sy in (-1, 1):
            holes.append(("csk", (float(x), sy * RAIL_Y), (5.5,)))
    for cx in cross_x():
        if abs(cx - X_DRIVE) < 100:
            continue                                    # motor-box members sit under the motor plate's edges
        for y in (-150.0, 150.0) if abs(cx - DECK_SEAM_X) > 15 else (-250.0, -100.0, 100.0, 250.0):
            holes.append(("csk", (cx, y), (5.5,)))
    return holes


def cross_x() -> list[float]:
    nones = [i for i, x in enumerate(CROSS_X) if x is None]
    return [x if x is not None else (X_DRIVE - 80.0 if i == nones[0] else X_DRIVE + 80.0)
            for i, x in enumerate(CROSS_X)]


@lru_cache(None)
def deck_part() -> cq.Workplane:
    d = PT.deck()
    for kind, (x, y), size in deck_holes():
        if kind == "circle":
            d = d.cut(cq.Workplane("XY").center(x, y).circle(size[0] / 2).extrude(-DECK_T - 2).translate((0, 0, 1)))
        elif kind == "csk4":
            d = d.cut(cq.Workplane("XY").center(x, y).circle(size[0] / 2).extrude(-DECK_T - 2).translate((0, 0, 1)))
            d = d.cut(cq.Workplane("XY").center(x, y).circle(4.2).workplane(offset=-2.6).circle(1.8).loft())
        elif kind == "csk":
            d = d.cut(cq.Workplane("XY").center(x, y).circle(size[0] / 2).extrude(-DECK_T - 2).translate((0, 0, 1)))
            d = d.cut(cq.Workplane("XY").center(x, y).circle(5.5).workplane(offset=-3.0).circle(2.75)
                      .loft().translate((0, 0, 0.0)))
        elif kind == "slot":
            d = d.cut(cq.Workplane("XY").center(x, y).slot2D(size[1], size[0]).extrude(-DECK_T - 2).translate((0, 0, 1)))
        elif kind == "rect":
            S = station_frame()
            ang = math.atan2(S[1, 0], S[0, 0])
            cut = (cq.Workplane("XY").rect(size[0], size[1]).extrude(-DECK_T - 2).translate((0, 0, 1))
                   .rotate((0, 0, 0), (0, 0, 1), math.degrees(ang)).translate((x, y, 0)))
            d = d.cut(cut)
    return d


def deck_half(side: int) -> cq.Workplane:
    """The deck is two 24 x 48 in sheets butted on the cross member at DECK_SEAM_X."""
    box = cq.Workplane("XY").center((DECK_SEAM_X - DECK_L / 2 if side < 0 else DECK_SEAM_X + DECK_L / 2) / 2, 0) \
        .rect(DECK_L / 2 + (DECK_SEAM_X if side < 0 else -DECK_SEAM_X), DECK_W + 2).extrude(-DECK_T - 4).translate((0, 0, 2))
    return deck_part().intersect(box)


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


def sam_frame(carriage_M: np.ndarray, tilt_deg: float = 0.0) -> np.ndarray:
    """Sam's studio frame on a carriage: his +x (hinge -> gear) points back
    toward the chain (-Y), his y is the carriage X, his z is up; hinge at
    (0, HINGE_Y, HINGE_Z). Positive tilt lifts the gear end (outlet down)."""
    Rs = np.array([[0, 1, 0], [-1, 0, 0], [0, 0, 1]], float)   # sam x->-Y, y->X, z->Z
    M = T(Rs, (0.0, HINGE_Y, HINGE_Z))
    return carriage_M @ M @ T(Ry(-math.radians(tilt_deg)))


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
HDPE = (0.95, 0.95, 0.92)
PETG = (0.16, 0.36, 0.78)
ORANGE = (0.95, 0.55, 0.12)
SAM = (0.10, 0.25, 0.85)
WHITE = (0.97, 0.97, 0.97)
BRASS = (0.80, 0.65, 0.25)
GREEN = (0.10, 0.50, 0.25)
RED = (0.85, 0.12, 0.10)

STEPS = {
    1: "Frame: long rails, cross members, corner brackets",
    2: "Legs and leveling feet",
    3: "NEMA 34 on its motor plate",
    4: "Deck onto the frame; motor plate up into the deck",
    5: "Idler: slider, stud, spacer, idler sprocket, tensioner",
    6: "Drive sprocket on the motor shaft",
    7: "Hall sensors (index, home) into the deck",
    8: "Chain: 12 A-1 attachment links every 8 pitches, close the loop, tension",
    9: "Carriages: inserts and magnets, then bolt each to its A-1 tab",
    10: "Station hold-down blocks",
    11: "Module 1: Sam's mounting plate, auger and cap on carriage 1",
    12: "Electronics board: supply, driver, Pi, interface board, e-stop",
}


def placements(tilt_deg: float = 0.0) -> list[Placement]:
    out: list[Placement] = []
    add = out.append
    z_rail = -DECK_T - EXT / 2

    # 1. frame
    L_long, L_cross = RAIL_L, 2 * RAIL_Y - EXT
    for sy in (-1, 1):
        add(Placement("ext_long", f"Long rail {'front' if sy < 0 else 'back'}",
                      T(Ry(math.pi / 2), (-L_long / 2, sy * RAIL_Y, z_rail)), 1, ALU, "frame", (0, sy * 60, -40)))
    for i, x in enumerate(cross_x()):
        add(Placement("ext_cross", f"Cross member {i + 1}", T(Rx(-math.pi / 2), (x, -L_cross / 2, z_rail)), 1, ALU,
                      "frame", (0, 0, -80)))
        for sy in (-1, 1):
            sides = CROSS_BRACKET_SIDES.get(x, (-1, 1) if abs(x) < RAIL_L / 2 - 20 else (-int(np.sign(x)),))
            for sx in sides:
                # inside corner between this cross member and a rail: one leg on the
                # rail's inner face, the other on the cross member's side face
                Rb = np.array([[sx, 0, 0], [0, 0, -sy], [0, sx * sy, 0]], float)
                add(Placement("corner_bracket", f"Corner bracket {i + 1}{'FB'[sy > 0]}{'LR'[sx > 0]}",
                              T(Rb, (x + sx * EXT / 2, sy * (RAIL_Y - EXT / 2), z_rail)), 1, ALU, "frame", (0, 0, -120)))
    # 2. legs + feet: each leg hangs under a rail end on two corner brackets,
    # one to the rail's underside, one to the end cross member's underside
    for sx in (-1, 1):
        for sy in (-1, 1):
            x, y = sx * (L_long / 2 - EXT / 2), sy * RAIL_Y
            zt = -DECK_T - EXT
            add(Placement("ext_leg", "Leg", T(None, (x, y, zt - LEG_L)), 2, ALU, "frame", (0, 0, -150)))
            add(Placement("foot", "Leveling foot", T(None, (x, y, zt - LEG_L - 20)), 2, DARK, "frame", (0, 0, -200)))
            Ra = np.array([[-sx, 0, 0], [0, sx, 0], [0, 0, -1]], float)
            add(Placement("corner_bracket", "Leg bracket (rail)", T(Ra, (x - sx * EXT / 2, y, zt)), 2, ALU, "frame",
                          (0, 0, -150)))
            Rc = np.array([[0, -sy, 0], [-sy, 0, 0], [0, 0, -1]], float)
            add(Placement("corner_bracket", "Leg bracket (cross member)", T(Rc, (x, y - sy * EXT / 2, zt)), 2, ALU,
                          "frame", (0, 0, -150)))
    # 3. motor + plate (plate under the deck, motor under the plate)
    z_plate = -DECK_T - MOTOR_PLATE_T
    add(Placement("motor_plate", "Motor plate", T(None, (X_DRIVE, 0, z_plate)), 3, ALU, "drive", (0, 0, -120)))
    add(Placement("nema34", "NEMA 34 34HS59-6004D-E1000", T(None, (X_DRIVE, 0, z_plate)), 3, DARK, "drive", (0, 0, -140)))
    for sx in (-1, 1):
        for sy in (-1, 1):
            add(Placement("m5x18_shcs", "Motor screw M5x18", T(Rx(math.pi), (X_DRIVE + sx * M34_BOLT_SQ / 2, sy * M34_BOLT_SQ / 2,
                                                                          z_plate - 12)), 3, DARK, "drive", (0, 0, -190)))
    # 4. deck (+ the motor plate's countersunk screws)
    add(Placement("deck_left", "Deck, idler half (1/2in HDPE)", T(), 4, HDPE, "deck", (0, 0, 120)))
    add(Placement("deck_right", "Deck, drive half (1/2in HDPE)", T(), 4, HDPE, "deck", (0, 0, 120)))
    for kind, (x, y), size in deck_holes():
        if kind == "csk":
            plate = abs(abs(x - X_DRIVE) - (MOTOR_PLATE / 2 - 10)) < 1 and abs(abs(y) - (MOTOR_PLATE / 2 - 10)) < 1
            clamp = abs(x - (X_IDLER - 22.0)) < 1 and abs(abs(y) - 18.0) < 1
            if clamp:
                continue                                    # placed with the idler (step 5)
            add(Placement("m5x25_fhcs" if plate else "m5x18_fhcs", "Motor plate screw" if plate else "Deck screw",
                          T(None, (x, y, 0)), 4, DARK, "deck", (0, 0, 160)))
            if plate:
                add(Placement("nut_m5", "Motor plate nut", T(None, (x, y, -DECK_T - MOTOR_PLATE_T - 4)), 4, STEEL, "deck",
                              (0, 0, -60)))
            else:
                add(Placement("tnut_m5", "T-nut", T(Rx(math.pi), (x, y, -DECK_T - 2.2)), 4, STEEL, "deck", (0, 0, 100)))
    # 5. idler: slider and jack block under the deck, idler on a spacer above
    xi = X_IDLER
    add(Placement("idler_slider", "Idler slider (printed)", T(None, (xi, 0, -DECK_T)), 5, ORANGE, "idler", (0, 0, -70)))
    add(Placement("idler_stud", "Idler stud 1/2-13 x 2-1/2", T(None, (xi, 0, -DECK_T - 8 - 7.7)), 5, STEEL, "idler", (0, 0, -130)))
    add(Placement("idler_spacer", "Idler spacer (printed)", T(None, (xi, 0, -DECK_T)), 5, ORANGE, "idler", (0, 0, 40)))
    add(Placement("sprocket_idler", "Idler sprocket 19T (bearing)", T(Rz(math.pi / 2 - ALPHA / 2), (xi, 0, CHAIN_Z)),
                  5, STEEL, "idler", (0, 0, 80)))
    add(Placement("washer_12", "Washer 1/2", T(None, (xi, 0, CHAIN_Z + IDLER_W / 2)), 5, STEEL, "idler", (0, 0, 110)))
    add(Placement("nut_12", "Nylon-insert locknut 1/2-13", T(None, (xi, 0, CHAIN_Z + IDLER_W / 2 + 2.4)), 5, STEEL, "idler",
                  (0, 0, 130)))
    for sy in (-1, 1):
        add(Placement("m5x25_fhcs", "Slider clamp screw", T(None, (xi - 22.0, sy * 18.0, 0)), 5, DARK, "idler", (0, 0, 60)))
        add(Placement("nut_m5", "Slider clamp nut", T(None, (xi - 22.0, sy * 18.0, -DECK_T - 8 - 4)), 5, STEEL, "idler",
                      (0, 0, -100)))
    add(Placement("tensioner_block", "Tensioner block (printed)", T(None, (X_IDLER + 42.0, 0, -DECK_T)), 5, ORANGE, "idler",
                  (0, 0, -70)))
    for y in (-9.0, 9.0):
        add(Placement("m4x20_fhcs", "Tensioner block screw", T(None, (X_IDLER + 42.0, y, 0)), 5, DARK, "idler", (0, 0, 60)))
    # jack screw: head outboard, tip on the slider's +x face (32 mm from the stud)
    add(Placement("m5x40_shcs", "Jack screw M5x40", T(Ry(math.pi / 2), (X_IDLER + 72.0, 0, -DECK_T - 5)), 5, DARK, "idler",
                  (40, 0, -70)))
    add(Placement("nut_m5", "Jack screw nut", T(Ry(math.pi / 2), (X_IDLER + 46.2, 0, -DECK_T - 5)), 5, STEEL, "idler",
                  (40, 0, -70)))
    # 6. drive sprocket
    add(Placement("sprocket_drive", "Drive sprocket 35B19, 14 mm bore", T(Rz(math.pi / 2), (X_DRIVE, 0, CHAIN_Z)), 6, STEEL,
                  "drive", (0, 0, 90)))
    # 7. hall sensors
    S = station_frame()
    for x, nm in ((25.0, "index"), (-25.0, "home")):
        p = to_world(S, (x, CAR_Y0 + 40, 0))
        add(Placement("hall_holder", f"Hall holder ({nm})", T(None, tuple(p)), 7, ORANGE, "sensors", (0, 0, -60)))
        add(Placement("a3144", f"A3144 hall sensor ({nm})", T(None, (p[0], p[1], -0.8)), 7, DARK, "sensors", (0, 0, -90)))
    # 8. chain
    cl = set(carriage_links())
    for i in range(N_LINKS):
        M = link_frame(i)
        if i in cl:
            add(Placement("chain_a1", "A-1 attachment connecting link", M, 8, STEEL, "chain", (0, 0, 40)))
        elif i % 2 == 0:
            add(Placement("chain_outer", "Outer link", M, 8, STEEL, "chain", (0, 0, 40)))
        else:
            add(Placement("chain_inner", "Inner link", M, 8, STEEL, "chain", (0, 0, 40)))
    # 9. carriages
    for k, li in enumerate(carriage_links()):
        Mc = link_frame(li, 0.0)
        add(Placement("carriage", f"Carriage {k + 1}", Mc, 9, PETG, "carriages", (0, 0, 70)))
        tab_z = CHAIN_Z + A1_HOLE_C
        add(Placement("m25x8_bhcs", f"Carriage screw {k + 1}", Mc @ T(Rx(math.pi / 2), (0, A1_C - PLATE_T, tab_z)), 9, DARK,
                      "carriages", (0, 0, 70)))
        add(Placement("insert_m25", f"Heat-set insert {k + 1}", Mc @ T(Rx(-math.pi / 2), (0, CAR_Y0, tab_z)), 9, BRASS,
                      "carriages", (0, 0, 70)))
        add(Placement("magnet", f"Index magnet {k + 1}", Mc @ T(None, (25, CAR_Y0 + 40, 0.2)), 9, STEEL, "carriages", (0, 0, 70)))
        if k == 0:
            add(Placement("magnet", "Home magnet", Mc @ T(None, (-25, CAR_Y0 + 40, 0.2)), 9, STEEL, "carriages", (0, 0, 70)))
    # 10. hold-downs
    for x in (-31.0, 31.0):
        add(Placement("hold_down", "Hold-down block (printed)", S @ T(None, (x, 0, 0)), 10, ORANGE, "station", (0, -40, 50)))
        for dx in (-12.0, 12.0):
            p = to_world(S, (x + dx, CAR_Y0 + CAR_L - 1 + HD_HOLE_DY, CAR_SKID + TONGUE[1] + 2.5))
            add(Placement("m4x25_shcs", "Hold-down screw M4x25", T(None, tuple(p)), 10, DARK, "station", (0, -40, 80)))
            add(Placement("tnut_m4", "Hold-down T-nut M4", T(Rx(math.pi), (p[0], p[1], -DECK_T - 2.2)), 10, STEEL, "station",
                          (0, -40, -40)))
    # 11. module 1 on carriage 1
    Ms = sam_frame(link_frame(CARRIAGE_LINK0, 0.0), tilt_deg)
    add(Placement("sam_mounting_plate", "Mounting plate (Sam, Oct 8)", Ms, 11, SAM, "module", (0, 0, 120)))
    Ma = Ms @ T(Ry(math.pi / 2), (AUGER_Z0_XS, 0, 0))                    # auger +z along Sam's +x
    add(Placement("auger", "Auger, threaded storage (lab)", Ma, 11, WHITE, "module", (0, 0, 160)))
    add(Placement("auger_cap", "Auger cap (lab)", Ma @ T(None, (0, 0, 250.0)), 11, WHITE, "module", (0, 0, 160)))
    for sx in (-1, 1):    # one short pin per side: a through pin would cross the auger's outlet end
        Mp = link_frame(CARRIAGE_LINK0, 0.0) @ T(Ry(sx * math.pi / 2), (sx * (LUG_X + LUG_T / 2), HINGE_Y, HINGE_Z))
        add(Placement("m5x18_shcs", "Hinge pin M5x18", Mp, 11, DARK, "module", (sx * 60, 0, 120)))
    # 12. electronics board beside the rig (on the bench, in front of the drive end)
    zb = -DECK_T - EXT - LEG_L - 20 - 8
    bx, by = DECK_L / 2 + 260, -120.0
    add(Placement("board_panel", "Electronics board (1/4in plywood)", T(None, (bx, by, zb)), 12, (0.80, 0.68, 0.48), "elec", (0, -80, 0)))
    add(Placement("lrs350", "Mean Well LRS-350-36", T(None, (bx - 90, by + 70, zb + 6.35)), 12, ALU, "elec", (0, -80, 60)))
    add(Placement("cl86t", "CL86T closed-loop driver", T(None, (bx + 105, by + 55, zb + 6.35)), 12, DARK, "elec", (0, -80, 60)))
    add(Placement("raspberry_pi", "Raspberry Pi", T(None, (bx - 120, by - 85, zb + 6.35 + 6)), 12, GREEN, "elec", (0, -80, 60)))
    add(Placement("perfboard", "Interface board (ULN2803A, pull-ups)", T(None, (bx - 20, by - 85, zb + 6.35 + 6)), 12, GREEN,
                  "elec", (0, -80, 60)))
    add(Placement("estop", "E-stop", T(None, (bx + 150, by - 90, zb + 6.35)), 12, RED, "elec", (0, -80, 60)))
    return out


BUILDERS = {
    "ext_long": lambda: PT.extrusion_2020(RAIL_L),
    "ext_cross": lambda: PT.extrusion_2020(2 * RAIL_Y - EXT),
    "ext_leg": lambda: PT.extrusion_2020(LEG_L),
    "corner_bracket": PT.corner_bracket,
    "foot": PT.leveling_foot,
    "motor_plate": PT.motor_plate,
    "nema34": PT.nema34,
    "deck": deck_part,
    "deck_left": lambda: deck_half(-1),
    "deck_right": lambda: deck_half(1),
    "idler_slider": PT.idler_slider,
    "idler_stud": lambda: PT.idler_stud(12.7, 63.5, 19.05),
    "idler_spacer": lambda: PT.washer(20.0, 13.2, DECK_T + CHAIN_Z - IDLER_W / 2),
    "sprocket_idler": PT.sprocket_idler,
    "washer_12": lambda: PT.washer(27.0, 13.5, 2.4),
    "nut_12": lambda: PT.nut_imperial(12.7, 19.05, 15.1),
    "nut_m5": lambda: PT.hexnut(5),
    "m4x20_fhcs": lambda: PT.shcs(4, 20, "flat"),
    "tnut_m4": PT.tnut_m5,
    "tensioner_block": PT.tensioner_block,
    "sprocket_drive": PT.sprocket_drive,
    "hall_holder": PT.hall_holder,
    "a3144": PT.a3144,
    "chain_a1": PT.chain_a1_link,
    "chain_outer": PT.chain_outer_link,
    "chain_inner": PT.chain_inner_link,
    "carriage": PT.carriage,
    "insert_m25": PT.heat_insert_m25,
    "magnet": PT.magnet,
    "hold_down": PT.hold_down,
    "m25x8_bhcs": lambda: PT.shcs(2.5, 8, "button"),
    "m4x25_shcs": lambda: PT.shcs(4, 25),
    "m5x18_shcs": lambda: PT.shcs(5, 18),
    "m5x18_fhcs": lambda: PT.shcs(5, 18, "flat"),
    "m5x25_fhcs": lambda: PT.shcs(5, 25, "flat"),
    "m5x40_shcs": lambda: PT.shcs(5, 40),
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
    print("C =", round(C, 3), "mm; pins:", len(p), "; carriage links:", carriage_links())
    S = station_frame()
    print("station frame origin", np.round(S[:3, 3], 2), "x-axis", np.round(S[:3, 0], 3))
    pl = placements()
    from collections import Counter
    print(len(pl), "placements;", Counter(x.key for x in pl).most_common(12))
