"""MG996R metal-gear servo, simplified (recreation of PR #170's stand-in).

step.parts has no MG996R (searched MG996R, MG996, 996R, MG995, TowerPro,
Tower Pro, servo, rc servo, ...; its closest records are a generic 50 x 20 x 42
"standard RC servo envelope" and the Futaba S3003), so this is PR #170's
simplified model (cad/full-assembly/onshape/purchased_parts.py, ``mg996r()``)
rebuilt parametrically; see checks/results/purchased_step_parts.json.

Frame (as PR #170): output spline axis = +z through the origin, case top on
z = 0, case towards +x, flange (mounting ears) in the XY plane.

Dimensions (PR #170): 40.7 x 19.7 mm case, 37 mm from its bottom to its top,
42.9 mm to the spline tip; 54.5 x 2.5 mm flange whose underside is 26.5 mm
above the case bottom; four Ø4.4 flange holes on the 48.04 x 9.04 mm pattern
of the Fusion baseplate's servo posts (the real servo's ears are slotted),
centred 9.88 mm from the spline axis towards +x; Ø13 x 1.5 boss; 25-sided
Ø5.8 spline (vertex on +x) with a Ø2.5 x 4 horn-screw hole.

Children: ``case`` (case, flange and boss, one solid) and ``output_spline``
(the spline above the boss, which turns with the output).  Their union is the
PR #170 solid; they touch on the boss top and do not overlap.
"""
from __future__ import annotations

import math

from cadgen import build123d as bd
from cadgen import srgb, step

CASE_L, CASE_W = 40.7, 19.7          # along x, along y
CASE_H = 37.0                        # case bottom to case top (z = 0)
TOTAL_H = 42.9                       # case bottom to spline tip
FLANGE_L, FLANGE_T = 54.5, 2.5
FLANGE_Z = 26.5                      # flange underside above the case bottom
HOLES_L, HOLES_W = 48.04, 9.04       # flange-hole pattern
HOLE_D = 4.4
SPLINE_TO_HOLES = 9.88               # spline axis to the hole-pattern centre, +x
BOSS_D, BOSS_H = 13.0, 1.5
SPLINE_D = 5.8                       # circumscribed diameter of the spline
SPLINE_SIDES = 25
SCREW_HOLE_D, SCREW_HOLE_DEPTH = 2.5, 4.0

CASE_COLOR = "#1E1F22"               # black plastic case
SPLINE_COLOR = "#C9CDD2"             # metal output spline

def _base() -> tuple:
    """Centred in x and y, based on z = 0."""
    return (bd.Align.CENTER, bd.Align.CENTER, bd.Align.MIN)


def _case() -> bd.Part:
    cx = SPLINE_TO_HOLES                 # case centred on the hole pattern
    body = bd.Pos(cx, 0, -CASE_H) * bd.Box(CASE_L, CASE_W, CASE_H, align=_base())
    fz = -CASE_H + FLANGE_Z
    flange = bd.Pos(cx, 0, fz) * bd.Box(FLANGE_L, CASE_W, FLANGE_T, align=_base())
    holes = [bd.Pos(cx + sx * HOLES_L / 2, sy * HOLES_W / 2, fz - 1.0)
             * bd.Cylinder(HOLE_D / 2, FLANGE_T + 2.0, align=_base())
             for sx in (-1, 1) for sy in (-1, 1)]
    flange = flange - holes
    boss = bd.Cylinder(BOSS_D / 2, BOSS_H, align=_base())
    return (body + flange + boss).clean()


def _spline() -> bd.Part:
    r = SPLINE_D / 2
    pts = [(r * math.cos(2 * math.pi * i / SPLINE_SIDES),
            r * math.sin(2 * math.pi * i / SPLINE_SIDES), 0.0)
           for i in range(SPLINE_SIDES)]
    height = TOTAL_H - CASE_H - BOSS_H   # the part standing above the boss
    prism = bd.Pos(0, 0, BOSS_H) * bd.extrude(
        bd.Face(bd.Wire.make_polygon(pts, close=True)), height)
    tip = TOTAL_H - CASE_H
    screw_hole = bd.Pos(0, 0, tip - SCREW_HOLE_DEPTH) * bd.Cylinder(
        SCREW_HOLE_D / 2, SCREW_HOLE_DEPTH + 1.0, align=_base())
    return prism - screw_hole


@step(out="../../STEP/purchased/mg996r.step")
def mg996r():
    case = _case()
    case.label = "case"
    case.color = srgb(CASE_COLOR)
    spline = _spline()
    spline.label = "output_spline"
    spline.color = srgb(SPLINE_COLOR)
    return bd.Compound(children=[case, spline], label="mg996r")


if __name__ == "__main__":
    mg996r()
