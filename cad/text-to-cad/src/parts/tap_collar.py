"""Tap collar: a split clamp ring on the auger tube with a solenoid plate (3D printed).

Recreates the team's Fusion 360 part ``tapcollar_v1`` (PR #170
``components/fusion-step/tap-collar.step``) in the SAME frame:

* the clamp bore axis is the Y axis (X = 0, Z = 0);
* the collar is extruded along +Y from Y = 0 to Y = DEPTH;
* +Z is up: the block and the thin mounting plate rise above the ring, the
  split clamp ear points to -X and a pocketed tab points to +X.

Construction: one XZ profile (ring + block + clamp ear + tab, minus the bore
and the clamp split) extruded along +Y, plus the thin plate on the +Y face,
then the holes: the vertical tap hole from the block top into the bore, the
M3 clamp hole through the ear (along Z), two M3 holes through the plate
(along Y), and the keyhole pocket in the +X face of the tab.
"""
from __future__ import annotations

from cadgen import build123d as bd
from cadgen import step, stl

# ---- dimensions (mm), measured from tap-collar.step -----------------------
DEPTH = 17.0                # extrusion depth along +Y
MID_Y = DEPTH / 2           # mid-plane of all Y-centred holes
BORE_D = 25.5               # clamp bore (auger tube clearance)
RING_OD = 33.5              # clamp ring outside diameter
BLOCK_WIDTH = 25.4          # block above the ring (X)
BLOCK_TOP_Z = 24.5
PLATE_THICKNESS = 1.2       # thin plate flush with the +Y face
PLATE_TOP_Z = 53.35
EAR_X_MIN = -26.0           # split clamp ear, towards -X
EAR_HEIGHT = 13.8           # Z extent of the ear, centred on Z = 0
SPLIT_WIDTH = 2.2           # clamp split, centred on Z = 0, ear end to bore
CLAMP_HOLE_D = 3.4          # M3 clearance through the ear, along Z
CLAMP_HOLE_X = -20.2
TAB_X_MAX = 19.95           # pocketed tab, towards +X
TAB_HEIGHT = 10.8           # Z extent of the tab, centred on Z = 0
POCKET_DEPTH = 2.5          # keyhole pocket in the tab's +X face
POCKET_D = 10.5             # round part of the pocket, centred (Y, Z) = (MID_Y, 0)
POCKET_SLOT_WIDTH = 4.0     # slot part of the pocket (Y), through the tab's Z extent
TAP_HOLE_D = 6.9            # vertical hole from the block top into the bore
PLATE_HOLE_D = 3.2          # two M3 holes through the plate, along Y
PLATE_HOLES_XZ = ((9.1, 49.0), (-9.1, 33.0))


def _profile() -> bd.Face:
    """The XZ profile, built in local XY with (x, y) = (X, Z)."""
    ring = bd.Circle(RING_OD / 2)
    block = bd.Rectangle(BLOCK_WIDTH, BLOCK_TOP_Z, align=(bd.Align.CENTER, bd.Align.MIN))
    # ear and tab start on the bore axis; the bore cut trims their inner ends
    ear = bd.Pos(EAR_X_MIN, 0) * bd.Rectangle(-EAR_X_MIN, EAR_HEIGHT,
                                              align=(bd.Align.MIN, bd.Align.CENTER))
    tab = bd.Rectangle(TAB_X_MAX, TAB_HEIGHT, align=(bd.Align.MIN, bd.Align.CENTER))
    bore = bd.Circle(BORE_D / 2)
    split = bd.Pos(EAR_X_MIN - 1, 0) * bd.Rectangle(-EAR_X_MIN + 1, SPLIT_WIDTH,
                                                    align=(bd.Align.MIN, bd.Align.CENTER))
    faces = (ring + block + ear + tab - bore - split).faces()
    assert len(faces) == 1, faces
    return faces[0]


def _pocket() -> bd.Part:
    """Keyhole pocket cut into the tab's +X face: a round seat plus a slot."""
    seat = bd.Pos(MID_Y, 0) * bd.Circle(POCKET_D / 2)
    slot = bd.Pos(MID_Y, 0) * bd.Rectangle(POCKET_SLOT_WIDTH, TAB_HEIGHT + 2)
    floor = bd.Plane.YZ.offset(TAB_X_MAX - POCKET_DEPTH)   # local (x, y) = (Y, Z)
    return bd.extrude(floor * (seat + slot), amount=POCKET_DEPTH + 1)


def make_tap_collar() -> bd.Part:
    body = bd.extrude(bd.Plane.XZ * _profile(), amount=DEPTH, dir=(0, 1, 0))
    plate = bd.Pos(0, DEPTH - PLATE_THICKNESS, BLOCK_TOP_Z) * bd.Box(
        BLOCK_WIDTH, PLATE_THICKNESS, PLATE_TOP_Z - BLOCK_TOP_Z,
        align=(bd.Align.CENTER, bd.Align.MIN, bd.Align.MIN))
    body = body + plate

    tap_hole = bd.Pos(0, MID_Y, 0) * bd.Cylinder(
        TAP_HOLE_D / 2, BLOCK_TOP_Z + 1, align=(bd.Align.CENTER, bd.Align.CENTER, bd.Align.MIN))
    clamp_hole = bd.Pos(CLAMP_HOLE_X, MID_Y, 0) * bd.Cylinder(CLAMP_HOLE_D / 2, EAR_HEIGHT + 2)
    plate_holes = [bd.Pos(x, DEPTH - PLATE_THICKNESS / 2, z) * bd.Rot(90, 0, 0)
                   * bd.Cylinder(PLATE_HOLE_D / 2, PLATE_THICKNESS + 2)
                   for x, z in PLATE_HOLES_XZ]
    return body - tap_hole - clamp_hole - plate_holes - _pocket()


@step(out="../../STEP/parts/tap_collar.step")
@stl(out="../../STL/parts/tap_collar.stl")
def tap_collar():
    part = make_tap_collar()
    part.label = "tap_collar"
    return part


if __name__ == "__main__":
    tap_collar()
