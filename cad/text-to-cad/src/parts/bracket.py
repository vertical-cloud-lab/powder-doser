"""Auger bracket: a split clamp ring on a footed base (3D printed).

Recreates the team's Fusion 360 part ``Auger_Bracket_Recorded_v1``
(PR #170 ``components/fusion-step/brackets.step``) in the SAME frame:

* base underside on Z = 0, the part centred on X = 0;
* the whole profile is extruded along +Y from Y = 0 to Y = THICKNESS;
* the clamp bore axis is parallel to Y at X = 0, Z = BORE_Z.

Construction: one XZ profile (feet + pedestal + clamp ring + two clamp
ears, minus the bore and the clamp split, with concave fillets where the
pedestal top meets the ring and rounds on the ear tops) extruded along +Y,
then intersected with a YZ rounded block so the ear tops are also rounded
along X (Fusion's cylinder/cylinder corners, no spherical patch), then the
M3 clearance holes: one clamp hole through both ears (along X) and one
mounting hole through each foot (along Z).
"""
from __future__ import annotations

import math

from cadgen import build123d as bd
from cadgen import step, stl

# ---- dimensions (mm), measured from brackets.step -------------------------
THICKNESS = 12.0            # extrusion depth along +Y
BASE_LENGTH = 60.0          # X extent of the footed base
FOOT_HEIGHT = 8.0           # foot (flange) thickness at both ends
PEDESTAL_WIDTH = 36.0       # centre block between the feet
PEDESTAL_HEIGHT = 14.0      # centre block top (Z)
BORE_Z = 29.25              # clamp bore axis height
BORE_D = 25.5               # clamp bore (auger tube clearance)
RING_OD = 33.5              # clamp ring outside diameter
WEB_FILLET_R = 3.0          # concave fillet, pedestal top -> ring
SLOT_WIDTH = 2.0            # clamp split, centred on X = 0, bore to top
EAR_THICKNESS = 3.0         # each clamp ear, along X
EAR_TOP_Z = 51.9615 + 1.0   # ear top (30*sqrt(3) + round radius in Fusion)
EAR_ROUND_R = 1.0           # rounds on all four top edges of each ear
CLAMP_HOLE_D = 3.4          # M3 clearance, clamp screw along X
CLAMP_HOLE_Z = 49.2
MOUNT_HOLE_D = 3.4          # M3 clearance, through each foot along Z
MOUNT_HOLE_X = 24.0         # +/- from centre
HOLE_Y = THICKNESS / 2      # all holes on the mid-plane of the extrusion

_EPS = 1e-3


def _profile() -> bd.Face:
    """The XZ profile, built in local XY with (x, y) = (X, Z)."""
    feet = bd.Rectangle(BASE_LENGTH, FOOT_HEIGHT, align=(bd.Align.CENTER, bd.Align.MIN))
    pedestal = bd.Rectangle(PEDESTAL_WIDTH, PEDESTAL_HEIGHT,
                            align=(bd.Align.CENTER, bd.Align.MIN))
    ring = bd.Pos(0, BORE_Z) * bd.Circle(RING_OD / 2)
    ear_span = SLOT_WIDTH + 2 * EAR_THICKNESS
    ears = bd.Pos(0, BORE_Z) * bd.Rectangle(ear_span, EAR_TOP_Z - BORE_Z,
                                            align=(bd.Align.CENTER, bd.Align.MIN))
    outline = (feet + pedestal + ring + ears).faces()[0]

    # concave web fillets where the pedestal top meets the ring
    x_web = math.sqrt((RING_OD / 2) ** 2 - (BORE_Z - PEDESTAL_HEIGHT) ** 2)
    web = [v for v in outline.vertices()
           if abs(v.Y - PEDESTAL_HEIGHT) < _EPS and abs(abs(v.X) - x_web) < 1e-2]
    assert len(web) == 2, web
    outline = outline.fillet_2d(WEB_FILLET_R, web)

    bore = bd.Pos(0, BORE_Z) * bd.Circle(BORE_D / 2)
    slot = bd.Pos(0, BORE_Z) * bd.Rectangle(SLOT_WIDTH, EAR_TOP_Z - BORE_Z + 1,
                                            align=(bd.Align.CENTER, bd.Align.MIN))
    face = (outline - bore - slot).faces()[0]

    # rounds on the ear tops (the four top corners, two per ear)
    tops = [v for v in face.vertices() if abs(v.Y - EAR_TOP_Z) < _EPS]
    assert len(tops) == 4, tops
    return face.fillet_2d(EAR_ROUND_R, tops)


def _ear_round_block() -> bd.Part:
    """Rounds the ear tops along X: a YZ rounded rectangle extruded along X."""
    rect = bd.Rectangle(THICKNESS, EAR_TOP_Z, align=(bd.Align.MIN, bd.Align.MIN)).faces()[0]
    rect = rect.fillet_2d(EAR_ROUND_R, [v for v in rect.vertices()
                                         if abs(v.Y - EAR_TOP_Z) < _EPS])
    return bd.extrude(bd.Plane.YZ * rect, amount=BASE_LENGTH / 2 + 1, both=True)


def make_bracket() -> bd.Part:
    body = bd.extrude(bd.Plane.XZ * _profile(), amount=THICKNESS, dir=(0, 1, 0))
    body = body & _ear_round_block()

    clamp_len = SLOT_WIDTH + 2 * EAR_THICKNESS + 2
    clamp_hole = (bd.Pos(0, HOLE_Y, CLAMP_HOLE_Z) * bd.Rot(0, 90, 0)
                  * bd.Cylinder(CLAMP_HOLE_D / 2, clamp_len))
    mount_holes = [bd.Pos(x, HOLE_Y, FOOT_HEIGHT / 2)
                   * bd.Cylinder(MOUNT_HOLE_D / 2, FOOT_HEIGHT + 2)
                   for x in (-MOUNT_HOLE_X, MOUNT_HOLE_X)]
    return body - clamp_hole - mount_holes


@step(out="../../STEP/parts/bracket.step")
@stl(out="../../STL/parts/bracket.stl")
def bracket():
    part = make_bracket()
    part.label = "bracket"
    return part


if __name__ == "__main__":
    bracket()
