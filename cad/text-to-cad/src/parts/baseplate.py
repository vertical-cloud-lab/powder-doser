"""Baseplate: the fixed part that carries the hinge towers and both servos.

Recreated from the lab's Fusion 360 file (PR #170,
``components/fusion-step/baseplate.step``), in its frame: Z up, underside on
z = 0, hinge axis along X through (y, z) = (45.4, 43.25), outlet end of the
auger towards -Y.

``make_baseplate(servos=...)`` builds both layouts:

* ``"below"`` (the current design, ``baseplate.py``): the servos lie on the
  two front arms, on four posts, with their pinions meshing the 28T gears
  27.26 mm below the hinge; two legs with gussets hang over the board's
  front edge.
* ``"above"`` (``baseplate_servos_above.py``, issue #172): the servo side is
  turned 180 deg about the hinge axis, so each servo hangs in a frame whose
  ear holes sit exactly where the old posts' holes go under that turn.  The
  front arms, the legs and the gussets go, leaving nothing below or in
  front of the nozzle.  The plate keeps its rear 59.6 mm, its four corner
  holes and the hinge towers; two short lips register its front edge on
  the board's front edge.
"""
from __future__ import annotations

import math

from cadgen import build123d as bd
from cadgen import step, stl

# plate
PLATE_T = 6.0
PLATE_HALF_W = 95.0
PLATE_DEPTH = 115.0
REAR_CHAMFER = 24.0            # 45 deg corners: (95, 91) -> (71, 115)
CUTOUT_HALF_W = 59.0           # U-cutout under the outlet
BOARD_EDGE_Y = 55.4            # board front edge = back of the cutout = legs' back faces
CORNER_HOLES = [(sx * 80.0, y) for sx in (1, -1) for y in (65.4, 95.4)]
CORNER_HOLE_D = 5.5            # #10 wood screws

# hinge towers (profile in the y-z plane, extruded along x)
HINGE_Y, HINGE_Z = 45.4, 43.25
TOWER_X = (28.9, 41.2)
KNUCKLE_R = 9.0
HINGE_HOLE_D = 5.3             # M5 x 45 button head
TOWER_TOP_Z = HINGE_Z + KNUCKLE_R              # 52.25
TOWER_REAR_ROUND_R = 10.0
TOWER_REAR_ROUND_C = (58.33, 42.25)
TOWER_BACK_FOOT_Y = 81.77

# servo posts (current design)
POST_X = (67.1, 72.1)
POST_YS = ((7.5, 15.5), (55.5, 63.5))
POST_Z = (6.0, 26.0)
POST_HOLE_D = 4.0
POST_HOLE_YS = (11.5, 59.54)
POST_HOLE_ZS = (11.48, 20.52)

# legs over the board's front edge (current design)
LEG_Y = (50.4, 55.4)
LEG_DEPTH = 40.0
GUSSET_X = (59.0, 64.0)
LEG_HOLE_D = 5.5
LEG_HOLE_X, LEG_HOLE_Z = 70.0, -19.0

# servos-above frame: the posts turned 180 deg about the hinge axis
FLIP_Y, FLIP_Z = 2 * HINGE_Y, 2 * HINGE_Z      # (y, z) -> (FLIP_Y - y, FLIP_Z - z)
SERVO_CASE_Y = (34.93, 75.63)   # MG996R case once flipped (layout: spline at y 45.4)
SERVO_CASE_Z = (60.66, 80.36)
CASE_CLEARANCE = 0.5
FRAME_TOP_RAIL = 4.0
FRAME_FOOT_REAR_Y = 101.0
FRAME_FRONT_POST_Y = 27.3       # FLIP_Y - 63.5
FRAME_FRONT_POST_FOOT_Z = 58.0
LIP_DEPTH = 12.0                # front-edge registration lips, below the plate
LIP_X = (64.0, 95.0)


def _yz_prism(points, x0: float, x1: float) -> bd.Part:
    """Extrude a closed y-z polygon along +x from x0 to x1."""
    pts = [(x0, y, z) for y, z in points]
    face = bd.Face(bd.Wire.make_polygon([bd.Vector(*p) for p in pts], close=True))
    return bd.extrude(face, amount=x1 - x0, dir=(1, 0, 0))


def _plate(servos: str) -> bd.Part:
    w, d, c = PLATE_HALF_W, PLATE_DEPTH, REAR_CHAMFER
    if servos == "below":
        outline = [(-w, 0), (-CUTOUT_HALF_W, 0), (-CUTOUT_HALF_W, BOARD_EDGE_Y),
                   (CUTOUT_HALF_W, BOARD_EDGE_Y), (CUTOUT_HALF_W, 0), (w, 0),
                   (w, d - c), (w - c, d), (-w + c, d), (-w, d - c)]
    else:
        outline = [(-w, BOARD_EDGE_Y), (w, BOARD_EDGE_Y), (w, d - c), (w - c, d),
                   (-w + c, d), (-w, d - c)]
    plate = bd.extrude(bd.Face(bd.Wire.make_polygon([bd.Vector(x, y, 0) for x, y in outline],
                                                    close=True)), amount=PLATE_T)
    for x, y in CORNER_HOLES:
        plate -= bd.Cylinder(CORNER_HOLE_D / 2, 3 * PLATE_T).moved(bd.Location((x, y, 0)))
    return plate


def _tower(x0: float, x1: float) -> bd.Part:
    """Hinge tower: inclined front face up to a knuckle round on the hinge."""
    with bd.BuildSketch(bd.Plane.YZ) as sk:
        with bd.BuildLine():
            cy, cz = TOWER_REAR_ROUND_C
            r = TOWER_REAR_ROUND_R
            # the rear round is tangent to the back face at 19.5 deg
            a0, a1 = math.radians(19.5), math.radians(90.0)
            on_round = lambda a: (cy + r * math.cos(a), cz + r * math.sin(a))
            p_round = on_round(a0)
            bd.Line((BOARD_EDGE_Y, PLATE_T), (TOWER_BACK_FOOT_Y, PLATE_T))
            bd.Line((TOWER_BACK_FOOT_Y, PLATE_T), p_round)
            bd.ThreePointArc(p_round, on_round((a0 + a1) / 2), (cy, TOWER_TOP_Z))
            bd.Line((cy, TOWER_TOP_Z), (HINGE_Y, TOWER_TOP_Z))
            bd.ThreePointArc((HINGE_Y, TOWER_TOP_Z), (HINGE_Y - KNUCKLE_R, HINGE_Z),
                             (HINGE_Y, HINGE_Z - KNUCKLE_R))
            bd.Line((HINGE_Y, HINGE_Z - KNUCKLE_R), (BOARD_EDGE_Y, PLATE_T))
        bd.make_face()
    tower = bd.extrude(sk.sketch, amount=x1 - x0).moved(bd.Location((x0, 0, 0)))
    hole = bd.Cylinder(HINGE_HOLE_D / 2, 200, rotation=(0, 90, 0)).moved(
        bd.Location((0, HINGE_Y, HINGE_Z)))
    return tower - hole


def _posts_below(sx: int) -> bd.Part:
    x0, x1 = (POST_X if sx > 0 else (-POST_X[1], -POST_X[0]))
    part = None
    for (y0, y1), yh in zip(POST_YS, POST_HOLE_YS):
        post = bd.Box(x1 - x0, y1 - y0, POST_Z[1] - POST_Z[0], align=bd.Align.MIN).moved(
            bd.Location((x0, y0, POST_Z[0])))
        for zh in POST_HOLE_ZS:
            post -= bd.Cylinder(POST_HOLE_D / 2, 30, rotation=(0, 90, 0)).moved(
                bd.Location(((x0 + x1) / 2, yh, zh)))
        part = post if part is None else part + post
    return part


def _leg(sx: int) -> bd.Part:
    """Gusset under the arm's inner edge plus the leg over the board edge."""
    g0, g1 = GUSSET_X
    gusset = _yz_prism([(0.0, 0.0), (LEG_Y[0], 0.0), (LEG_Y[0], -LEG_DEPTH)], g0, g1)
    # leg: x from 59 to 95 at the top, 59..64 at the bottom (sloped outer face)
    pts = [(g0, 0.0), (PLATE_HALF_W, 0.0), (g1, -LEG_DEPTH), (g0, -LEG_DEPTH)]
    face = bd.Face(bd.Wire.make_polygon([bd.Vector(x, LEG_Y[0], z) for x, z in pts], close=True))
    leg = bd.extrude(face, amount=LEG_Y[1] - LEG_Y[0], dir=(0, 1, 0))
    leg -= bd.Cylinder(LEG_HOLE_D / 2, 30, rotation=(90, 0, 0)).moved(
        bd.Location((LEG_HOLE_X, sum(LEG_Y) / 2, LEG_HOLE_Z)))
    part = gusset + leg
    return part if sx > 0 else part.mirror(bd.Plane.YZ)


def _servo_frame(sx: int) -> bd.Part:
    """Servos-above: a 5 mm frame in the old posts' plane.  Its ear holes are
    the old post holes turned 180 deg about the hinge; the MG996R case passes
    through its window, and a diagonal strut carries the front post from the
    plate's front edge."""
    x0, x1 = POST_X
    rear_post_y1 = FLIP_Y - POST_YS[0][0]          # 83.3
    top_z = SERVO_CASE_Z[1] + CASE_CLEARANCE + FRAME_TOP_RAIL
    outline = [(BOARD_EDGE_Y, PLATE_T), (FRAME_FOOT_REAR_Y, PLATE_T),
               (rear_post_y1, top_z), (FRAME_FRONT_POST_Y, top_z),
               (FRAME_FRONT_POST_Y, FRAME_FRONT_POST_FOOT_Z)]
    frame = _yz_prism(outline, x0, x1)
    c = CASE_CLEARANCE
    win = bd.Box(30, SERVO_CASE_Y[1] - SERVO_CASE_Y[0] + 2 * c,
                 SERVO_CASE_Z[1] - SERVO_CASE_Z[0] + 2 * c, align=bd.Align.MIN).moved(
        bd.Location((x0 - 10, SERVO_CASE_Y[0] - c, SERVO_CASE_Z[0] - c)))
    frame -= win
    for yh in POST_HOLE_YS:
        for zh in POST_HOLE_ZS:
            frame -= bd.Cylinder(POST_HOLE_D / 2, 30, rotation=(0, 90, 0)).moved(
                bd.Location(((x0 + x1) / 2, FLIP_Y - yh, FLIP_Z - zh)))
    return frame if sx > 0 else frame.mirror(bd.Plane.YZ)


def _lip(sx: int) -> bd.Part:
    x0, x1 = LIP_X
    lip = bd.Box(x1 - x0, LEG_Y[1] - LEG_Y[0], LIP_DEPTH, align=bd.Align.MIN).moved(
        bd.Location((x0, LEG_Y[0], -LIP_DEPTH)))
    # the plate starts at the board edge, so the lip hangs from a 5 mm ledge
    ledge = bd.Box(x1 - x0, LEG_Y[1] - LEG_Y[0], PLATE_T, align=bd.Align.MIN).moved(
        bd.Location((x0, LEG_Y[0], 0)))
    part = lip + ledge
    return part if sx > 0 else part.mirror(bd.Plane.YZ)


def make_baseplate(servos: str = "below") -> bd.Part:
    if servos not in ("below", "above"):
        raise ValueError(servos)
    part = _plate(servos)
    for x0, x1 in (TOWER_X, (-TOWER_X[1], -TOWER_X[0])):
        part += _tower(x0, x1)
    for sx in (1, -1):
        if servos == "below":
            part += _posts_below(sx)
            part += _leg(sx)
        else:
            part += _servo_frame(sx)
            part += _lip(sx)
    part = part.clean()
    part.label = "baseplate" if servos == "below" else "baseplate_servos_above"
    return part


@step(out="../../STEP/parts/baseplate.step")
@stl(out="../../STL/parts/baseplate.stl")
def baseplate():
    return make_baseplate("below")


if __name__ == "__main__":
    baseplate()
