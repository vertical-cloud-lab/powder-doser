"""Tap-collar base: the hard-stop plate under the tap collar (3D printed).

Recreates PR #170's ``components/ai-step/tap-collar-base.step`` (the
AI-generated ``mount_plate.step`` from PR #51 that the rig still uses) in the
SAME frame:

* underside on Z = 0, centred on X = 0 and on Y = 0;
* the profile is extruded along Y, symmetric about Y = 0 (+/- DEPTH / 2);
* the cradle (a cylindrical saddle for the collar ring) is coaxial with the
  auger tube at X = 0, Z = CRADLE_Z, axis parallel to Y.

Construction: one XZ profile (block with the cradle cut into its top, plus
the hard-stop tower with concave root fillets) extruded along Y, then two
vertical M3 clearance holes, the one through the tower countersunk at the
top for a 90 degree flat-head screw.
"""
from __future__ import annotations

import math

from cadgen import build123d as bd
from cadgen import step, stl

# ---- dimensions (mm), measured from tap-collar-base.step ------------------
LENGTH = 60.0               # X
DEPTH = 18.0                # Y, symmetric about Y = 0
BLOCK_HEIGHT = 14.0         # top of the block (Z)
CRADLE_D = 34.0             # cylindrical saddle for the collar ring
CRADLE_Z = 29.25            # saddle axis height (= the auger tube axis)
TOWER_X_MIN = 17.25         # hard-stop tower on the +X end
TOWER_X_MAX = 27.2
TOWER_TOP_Z = 21.0
TOWER_FILLET_R = 1.5        # concave fillets at the tower root, both sides
HOLE_D = 3.4                # M3 clearance, vertical
HOLE_X = 24.0               # holes at X = -HOLE_X (plain) and +HOLE_X (through the tower)
CSK_D = 6.0                 # countersink diameter at the tower top
CSK_ANGLE = 90.0            # included angle

_EPS = 1e-3


def _profile() -> bd.Face:
    """The XZ profile, built in local XY with (x, y) = (X, Z)."""
    block = bd.Rectangle(LENGTH, BLOCK_HEIGHT, align=(bd.Align.CENTER, bd.Align.MIN))
    tower = bd.Pos(TOWER_X_MIN, 0) * bd.Rectangle(
        TOWER_X_MAX - TOWER_X_MIN, TOWER_TOP_Z, align=(bd.Align.MIN, bd.Align.MIN))
    cradle = bd.Pos(0, CRADLE_Z) * bd.Circle(CRADLE_D / 2)
    face = (block + tower - cradle).faces()[0]
    roots = [v for v in face.vertices() if abs(v.Y - BLOCK_HEIGHT) < _EPS
             and min(abs(v.X - TOWER_X_MIN), abs(v.X - TOWER_X_MAX)) < _EPS]
    assert len(roots) == 2, roots
    return face.fillet_2d(TOWER_FILLET_R, roots)


def make_tap_collar_base() -> bd.Part:
    body = bd.extrude(bd.Plane.XZ * _profile(), amount=DEPTH / 2, both=True)
    up = (bd.Align.CENTER, bd.Align.CENTER, bd.Align.MIN)   # from Z = -1 upwards
    plain = bd.Pos(-HOLE_X, 0, -1) * bd.Cylinder(HOLE_D / 2, BLOCK_HEIGHT + 2, align=up)
    tower_hole = bd.Pos(HOLE_X, 0, -1) * bd.Cylinder(HOLE_D / 2, TOWER_TOP_Z + 2, align=up)
    # countersink: a cone from CSK_D at the tower top down to the hole diameter
    half = math.radians(CSK_ANGLE / 2)
    csk_depth = (CSK_D - HOLE_D) / 2 / math.tan(half)
    over = 1.0   # the cone continues past the top face so the cut is clean
    countersink = bd.Pos(HOLE_X, 0, TOWER_TOP_Z - csk_depth) * bd.Cone(
        HOLE_D / 2, CSK_D / 2 + over * math.tan(half), csk_depth + over,
        align=(bd.Align.CENTER, bd.Align.CENTER, bd.Align.MIN))
    return body - plain - tower_hole - countersink


@step(out="../../STEP/parts/tap_collar_base.step")
@stl(out="../../STL/parts/tap_collar_base.stl")
def tap_collar_base():
    part = make_tap_collar_base()
    part.label = "tap_collar_base"
    return part


if __name__ == "__main__":
    tap_collar_base()
