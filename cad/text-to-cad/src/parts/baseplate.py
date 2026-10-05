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
  turned 180 deg about the hinge axis, so each servo sits in an open-top
  cradle whose ear holes are exactly where the old posts' holes go under
  that turn.  The
  front arms, the legs and the gussets go, leaving nothing below or in
  front of the nozzle.  With nothing hanging below it, the plate can
  overhang the board: it runs from the towers' feet (y = 55.4) back to
  y = 170, the board's edge moves to y = 100, and four #10 screws go into
  the board at y = 115 and 155.  A slot between the towers runs back past
  the board's edge, so in front of the board the plate is a fork and a
  cup up to about 58 mm across can rise past it to the tube.  Nothing is
  below z = 0, so it prints flat on the bed (registration lips were tried
  and dropped: they put supports under the whole plate).

  The doser also sits ``ABOVE_DROP`` = 5 mm lower than PR #170's
  (``lib.frames.DROP``): the towers and cradles are 5 mm shorter.  At rest
  the mounting plate's floor would then be 3 mm under the plate top, so
  the plate is relieved under it down to a 2 mm skin (1 mm clear of the
  floor), the slot widens to the towers' inner faces and runs on to
  y = 111, and the rear bracket screws' button heads get notches.  The
  towers' feet keep the full 6 mm.
"""
from __future__ import annotations

import math

from cadgen import build123d as bd
from cadgen import step, stl

from lib.frames import DROP

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
CASE_CLEARANCE = 0.3
CRADLE_HOLE_D = 3.4             # M3 clearance: leaves >= 1.6 mm between hole and case slot
FRAME_FOOT_REAR_Y = 101.0
FRAME_FRONT_POST_Y = 27.3       # FLIP_Y - 63.5
FRAME_FRONT_POST_FOOT_Z = 58.0
# servos-above: nothing hangs below the plate, so it can overhang the board.
# The board edge moves 44.6 mm back (the outlet then overhangs it by 66 mm
# at rest) and the plate grows rearwards to keep four screws in the board.
ABOVE_BOARD_EDGE_Y = 100.0
ABOVE_PLATE_REAR_Y = 170.0
ABOVE_HOLES = [(sx * 80.0, y) for sx in (1, -1) for y in (115.0, 155.0)]
# ...and a slot between the hinge towers, back to the board's edge, so the
# plate is a fork in front of the board and a cup can rise past it
# lowered (frames.DROP), it widens to the towers' inner faces, because the
# mounting plate's knuckle tongues then dip below the plate top beside them,
# and it runs on to y = 111, past where the front bracket's screw heads
# swing as the doser tilts (they clear the plate top at 4.3 deg, y = 109.2)
ABOVE_SLOT_HALF_W = TOWER_X[0]
ABOVE_SLOT_END_Y = 111.0
ABOVE_DROP = DROP["above"]
# relief under the mounting plate's floor, which at rest spans z = 3..9
# once lowered.  The floor's footprint (world frame, +X half, from
# mounting_plate.py): tongues forward to y = 61.8 under the knuckles
# (|x| = 16.1..28.6) and the gear blocks (41.8..54.1), full width 54.1 back
# to y = 82.4, a 45 deg chamfer to 34, then 34 back to y = 175.4, plus the
# stepper plate's tab (34..54.1, y = 122.7..140.7) on the -X side.  The
# relief is that, mirrored, plus ABOVE_RELIEF_MARGIN, less the towers'
# feet; the tongues' rounded fronts reach the plate top at y = 62.6.
ABOVE_RELIEF_Z = 2.0            # skin left under the relief
ABOVE_RELIEF_MARGIN = 1.5
# as the doser tilts, the floor swings back (+y) by up to 2.7 mm before it
# clears the plate top (at 4.5 deg), so walls it swings towards (the
# chamfers, the stepper tab's rear) get this much more
ABOVE_RELIEF_SWING = 1.5
ABOVE_RELIEF_TONGUE_Y = 61.0
ABOVE_RELIEF_BEHIND_TOWER_Y = 82.4 - ABOVE_RELIEF_MARGIN
# the rear bracket's two M3 button heads hang 1.35 mm above the board
ABOVE_HEAD_NOTCH_D = 9.0
ABOVE_REAR_HEADS = [(sx * 24.0, 169.4) for sx in (1, -1)]


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
        d = ABOVE_PLATE_REAR_Y
        outline = [(-w, BOARD_EDGE_Y), (w, BOARD_EDGE_Y), (w, d - c), (w - c, d),
                   (-w + c, d), (-w, d - c)]
    plate = bd.extrude(bd.Face(bd.Wire.make_polygon([bd.Vector(x, y, 0) for x, y in outline],
                                                    close=True)), amount=PLATE_T)
    for x, y in (CORNER_HOLES if servos == "below" else ABOVE_HOLES):
        plate -= bd.Cylinder(CORNER_HOLE_D / 2, 3 * PLATE_T).moved(bd.Location((x, y, 0)))
    if servos == "above":
        hw = ABOVE_SLOT_HALF_W
        plate -= bd.Box(2 * hw, ABOVE_SLOT_END_Y - BOARD_EDGE_Y + 1.0, 3 * PLATE_T,
                        align=(bd.Align.CENTER, bd.Align.MIN, bd.Align.CENTER)).moved(
            bd.Location((0, BOARD_EDGE_Y - 1.0, PLATE_T / 2)))
        plate -= _relief()
        for x, y in ABOVE_REAR_HEADS:
            plate -= bd.Cylinder(ABOVE_HEAD_NOTCH_D / 2, 3 * PLATE_T).moved(bd.Location((x, y, 0)))
    return plate


def _relief() -> bd.Part:
    """Servos-above: the pocket under the mounting plate's floor, from
    ABOVE_RELIEF_Z up through the plate top (see ABOVE_RELIEF_*)."""
    m = ABOVE_RELIEF_MARGIN
    ms = m + ABOVE_RELIEF_SWING
    w_full, w_rear = 54.1 + m, 34.0 + m
    chamfer = 54.1 + 82.4 + ms * math.sqrt(2)         # x + y on the chamfer
    tab_y = (122.73 - m, 140.73 + ms)
    rear_y = 175.4 + 5.0                              # runs out of the plate
    half = [(0.0, ABOVE_RELIEF_BEHIND_TOWER_Y), (w_full, ABOVE_RELIEF_BEHIND_TOWER_Y),
            (w_full, chamfer - w_full), (w_rear, chamfer - w_rear),
            (w_rear, tab_y[0]), (w_full, tab_y[0]), (w_full, tab_y[1]), (w_rear, tab_y[1]),
            (w_rear, rear_y), (0.0, rear_y)]
    outline = half[1:-1] + [(-x, y) for x, y in reversed(half[1:-1])]
    h = PLATE_T + 1.0 - ABOVE_RELIEF_Z
    relief = bd.extrude(bd.Face(bd.Wire.make_polygon(
        [bd.Vector(x, y, ABOVE_RELIEF_Z) for x, y in outline], close=True)), amount=h)
    # forward to the gear blocks' tongues, outside the towers' feet (the
    # knuckles' tongues are inside the slot)
    for sx in (1, -1):
        x0 = TOWER_X[1] if sx > 0 else -w_full
        relief += bd.Box(w_full - TOWER_X[1], ABOVE_RELIEF_BEHIND_TOWER_Y - ABOVE_RELIEF_TONGUE_Y + 1.0, h,
                         align=bd.Align.MIN).moved(
            bd.Location((x0, ABOVE_RELIEF_TONGUE_Y, ABOVE_RELIEF_Z)))
    return relief


def _tower(x0: float, x1: float, drop: float = 0.0) -> bd.Part:
    """Hinge tower: inclined front face up to a knuckle round on the hinge.
    ``drop`` lowers the hinge: the back face keeps its slope (its foot moves
    forward) and the front face still ends on the plate's front edge."""
    hz, top = HINGE_Z - drop, TOWER_TOP_Z - drop
    with bd.BuildSketch(bd.Plane.YZ) as sk:
        with bd.BuildLine():
            cy, cz = TOWER_REAR_ROUND_C[0], TOWER_REAR_ROUND_C[1] - drop
            r = TOWER_REAR_ROUND_R
            # the rear round is tangent to the back face at 19.5 deg
            a0, a1 = math.radians(19.5), math.radians(90.0)
            on_round = lambda a: (cy + r * math.cos(a), cz + r * math.sin(a))
            p_round = on_round(a0)
            back_foot_y = TOWER_BACK_FOOT_Y + (p_round[0] - TOWER_BACK_FOOT_Y) * drop / (
                p_round[1] + drop - PLATE_T)
            bd.Line((BOARD_EDGE_Y, PLATE_T), (back_foot_y, PLATE_T))
            bd.Line((back_foot_y, PLATE_T), p_round)
            bd.ThreePointArc(p_round, on_round((a0 + a1) / 2), (cy, top))
            bd.Line((cy, top), (HINGE_Y, top))
            bd.ThreePointArc((HINGE_Y, top), (HINGE_Y - KNUCKLE_R, hz),
                             (HINGE_Y, hz - KNUCKLE_R))
            bd.Line((HINGE_Y, hz - KNUCKLE_R), (BOARD_EDGE_Y, PLATE_T))
        bd.make_face()
    tower = bd.extrude(sk.sketch, amount=x1 - x0).moved(bd.Location((x0, 0, 0)))
    hole = bd.Cylinder(HINGE_HOLE_D / 2, 200, rotation=(0, 90, 0)).moved(
        bd.Location((0, HINGE_Y, hz)))
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


def _servo_frame(sx: int, drop: float = 0.0) -> bd.Part:
    """Servos-above: an open-top cradle in the old posts' plane.  Its ear
    holes are the old post holes turned 180 deg about the hinge.  The MG996R
    is lowered into it from above, after the mounting plate is on its hinge
    (its spline then passes over the 28T gear's top), with the
    case between the two posts and the ears on their inner faces, as in the
    current design.  A diagonal strut carries the front post from the
    plate's front edge.  ``drop`` lowers everything but the feet."""
    x0, x1 = POST_X
    c = CASE_CLEARANCE
    rear_post_y1 = FLIP_Y - POST_YS[0][0]          # 83.3
    top_z = SERVO_CASE_Z[1] + c - drop              # posts end level with the case
    outline = [(BOARD_EDGE_Y, PLATE_T), (FRAME_FOOT_REAR_Y, PLATE_T),
               (rear_post_y1, top_z), (FRAME_FRONT_POST_Y, top_z),
               (FRAME_FRONT_POST_Y, FRAME_FRONT_POST_FOOT_Z - drop)]
    frame = _yz_prism(outline, x0, x1)
    slot = bd.Box(30, SERVO_CASE_Y[1] - SERVO_CASE_Y[0] + 2 * c, 60, align=bd.Align.MIN).moved(
        bd.Location((x0 - 10, SERVO_CASE_Y[0] - c, SERVO_CASE_Z[0] - c - drop)))
    frame -= slot
    for yh in POST_HOLE_YS:
        for zh in POST_HOLE_ZS:
            frame -= bd.Cylinder(CRADLE_HOLE_D / 2, 30, rotation=(0, 90, 0)).moved(
                bd.Location(((x0 + x1) / 2, FLIP_Y - yh, FLIP_Z - zh - drop)))
    return frame if sx > 0 else frame.mirror(bd.Plane.YZ)


def make_baseplate(servos: str = "below") -> bd.Part:
    if servos not in ("below", "above"):
        raise ValueError(servos)
    drop = ABOVE_DROP if servos == "above" else 0.0
    part = _plate(servos)
    for x0, x1 in (TOWER_X, (-TOWER_X[1], -TOWER_X[0])):
        part += _tower(x0, x1, drop)
    for sx in (1, -1):
        if servos == "below":
            part += _posts_below(sx)
            part += _leg(sx)
        else:
            part += _servo_frame(sx, drop)
    part = part.clean()
    part.label = "baseplate" if servos == "below" else "baseplate_servos_above"
    return part


@step(out="../../STEP/parts/baseplate.step")
@stl(out="../../STL/parts/baseplate.stl")
def baseplate():
    return make_baseplate("below")


if __name__ == "__main__":
    baseplate()
