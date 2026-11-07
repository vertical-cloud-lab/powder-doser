"""Mounting plate: the tilting cradle that carries the auger (3D printed).

Recreates the team's Fusion 360 part ``mountingplate_v2`` (PR #170
``components/fusion-step/mounting-plate.step``) in the SAME frame, the "MP
frame" of PR #170's ``onshape/layout.py``, so its placement applies as is:

* the hinge axis is MP Z through the origin.  The origin lies in the inner
  face of the world -X tilt gear, so the part spans z = -95.9 .. 12.3 and
  its mid-plane (world x = 0) is z = MID_Z = -41.8;
* the floor is a 6 mm plate parallel to XZ with its top at y = -29.25, so
  the auger axis (MP X through (y, z) = (0, MID_Z)) is level with the hinge
  once the brackets (bores 29.25 mm above their bases) stand on it;
* the stepper side is MP +z (world -X): the NEMA 11 plate is crosswise
  (normal X) at x = -89.333 .. -83.333, its pilot 32 mm from the auger axis.

Five bodies, like the reference STEP (which also overlaps them):

  plate                 floor with the M3 rows, two hinge knuckles, stepper plate
  gear_pos, gear_neg    28T tilt gears, world +X / -X side
                        (MP z = -95.9 .. -83.6 / 0 .. 12.3)
  block_pos, block_neg  arm-shaped blocks tying each gear to the floor

Each knuckle and block is the same "arm" profile (XY): a 7.5 mm wide band
from the floor top up to the Ø15 hinge boss, its outer side tangent to the
boss and through the arm foot (x = -25 on the floor top), its inner side
parallel through the hinge axis.  Where an arm meets the floor, the floor
runs forward as a tongue to the arm's inner side, its bottom edge rounded
with R = floor thickness; between the tongues the floor front is x = -37.

The 28T gears (module 1.298 = OD 38.94 / 30, 20 deg, Fusion SpurGear
add-in profile from ``lib.gears``, tooth 0 on +X) are partial: teeth only on
the sector TOOTH_SECTOR_START_DEG -> TOOTH_SECTOR_END_DEG (counter-clockwise
about MP +Z, both edges in a tooth gap).  Elsewhere the rim is turned down to
r = SECTOR_CUT_R, just under the root circle, except inside the arm band,
where the Fusion sketch left the block's footprint out of the cut, so a few
teeth remain there (one whole, two partial).  ``make_mounting_plate`` can
turn the toothed sector about the hinge (e.g. 180 deg for servos above the
hinge); nothing else moves.
"""
from __future__ import annotations

import math

from cadgen import build123d as bd
from cadgen import step, stl

from lib.gears import spur_gear

# ---- layout along the hinge axis (MP z), symmetric about MID_Z -------------
KNUCKLE_GAP = 32.2          # between the two knuckles' inner faces
KNUCKLE_W = 12.5            # each hinge knuckle
TOWER_W = 12.3              # baseplate hinge tower that sits beside each knuckle
KNUCKLE_TOWER_GAP = 0.3     # knuckle -> tower
TOWER_GEAR_GAP = 0.6        # tower -> 28T gear
GEAR_W = 12.3               # 28T gear (and block) width
# distances from the mid-plane
KNUCKLE_IN = KNUCKLE_GAP / 2                                       # 16.1
KNUCKLE_OUT = KNUCKLE_IN + KNUCKLE_W                               # 28.6
GEAR_IN = KNUCKLE_OUT + KNUCKLE_TOWER_GAP + TOWER_W + TOWER_GEAR_GAP   # 41.8
GEAR_OUT = GEAR_IN + GEAR_W                                        # 54.1
MID_Z = -GEAR_IN            # -41.8: origin on the world -X gear's inner face

# ---- hinge ------------------------------------------------------------------
HINGE_HOLE_D = 5.7          # M5 shank clearance (knuckles and gears)
BOSS_R = 7.5                # knuckle boss around the hinge axis
ARM_FOOT_X = -25.0          # arm's outer side meets the floor top here

# ---- floor (a plate parallel to XZ) ------------------------------------------
FLOOR_TOP_Y = -29.25        # auger axis (y = 0) 29.25 above it
FLOOR_T = 6.0
FLOOR_BACK_X = -130.0
FLOOR_FRONT_X = -37.0       # front edge between the knuckle / gear tongues
FLOOR_REAR_HALF_W = 34.0    # |z - MID_Z| of the narrow rear section
# the rear section widens to the full width (GEAR_OUT) with a 45 deg chamfer
# that ends at these x (the Fusion sketch is not symmetric here)
FLOOR_STEP_X_ZPOS = -36.197553   # MP +z side (stepper / world -X)
FLOOR_STEP_X_ZNEG = -37.0        # MP -z side
TONGUE_ROUND_R = FLOOR_T    # full round on each tongue's bottom front edge
# M3 rows: brackets at x = -124 / -58.333, tap-collar base at -42.333
FLOOR_HOLE_D = 3.4
FLOOR_HOLE_XS = (-124.0, -58.333, -42.333)
FLOOR_HOLE_HALF_PITCH = 24.0     # rows 48 mm apart across the auger

# ---- NEMA 11 stepper plate ---------------------------------------------------
STEPPER_BACK_X = -89.333    # motor side
STEPPER_T = 6.0
STEPPER_OFFSET = 32.0       # pilot axis from the auger axis: (20 + 44) / 2 at module 1
STEPPER_HALF = 18.1         # plate extends this far around the pilot (top, sides)
PILOT_D = 22.0
SCREW_HOLE_D = 3.4          # 4x, for the M2.5 x 8 motor screws
SCREW_HALF_PITCH = 11.5     # NEMA 11: 23 mm square
STEPPER_TAB_MARGIN = 6.0    # floor tab under the plate, past each face
STEPPER_TAB_R = 6.0         # its two outer corners

# ---- 28T tilt gears --------------------------------------------------------
GEAR_TEETH = 28
GEAR_OD = 38.94
GEAR_MODULE = GEAR_OD / (GEAR_TEETH + 2)   # 1.298 (addendum 1 m)
GEAR_PRESSURE_ANGLE = 20.0
GEAR_TOOTH_ANGLE = 0.0      # tooth 0 centred on MP +X
TOOTH_SECTOR_START_DEG = 250.563   # teeth run CCW from here ...
TOOTH_SECTOR_END_DEG = 97.076      # ... through 0 deg to here
SECTOR_CUT_R = 16.6355      # toothless rim (root circle r = 16.670)


def _pt(x: float, y: float) -> bd.Vector:
    return bd.Vector(x, y, 0.0)


def _arm_geometry() -> tuple[bd.Vector, bd.Vector, bd.Vector, float, float]:
    """Arm foot points A (outer) and B (inner) on the floor top, the tangent
    point T on the boss, and the polar angles (deg) of T and of the inner
    side's crossing of the boss circle."""
    a = _pt(ARM_FOOT_X, FLOOR_TOP_Y)
    d = a.length
    phi_a = math.atan2(a.Y, a.X)
    phi_t = phi_a - math.acos(BOSS_R / d)          # the upper tangent point
    t = _pt(BOSS_R * math.cos(phi_t), BOSS_R * math.sin(phi_t))
    u = (t - a).normalized()                       # arm direction, foot -> boss
    b = _pt(FLOOR_TOP_Y * u.X / u.Y, FLOOR_TOP_Y)  # inner side through the axis
    phi_in = math.atan2(-u.Y, -u.X)
    return a, b, t, math.degrees(phi_t), math.degrees(phi_in)


def _arc(r: float, a0: float, a1: float) -> bd.Edge:
    """Arc of radius r about the origin from a0 to a1 (deg, signed sweep)."""
    pts = [_pt(r * math.cos(math.radians(a)), r * math.sin(math.radians(a)))
           for a in (a0, 0.5 * (a0 + a1), a1)]
    return bd.Edge.make_three_point_arc(*pts)


def _arm_polygon() -> bd.Face:
    """The arm band from the floor top to the hinge axis (A, B, axis, T)."""
    a, b, t, _, _ = _arm_geometry()
    return bd.Face(bd.Wire.make_polygon([a, b, _pt(0, 0), t], close=True))


def _knuckle_profile() -> bd.Face:
    """Arm + the boss around the hinge (270 deg of it shows), minus the bore."""
    a, b, t, phi_t, phi_in = _arm_geometry()
    p_in = _pt(BOSS_R * math.cos(math.radians(phi_in)), BOSS_R * math.sin(math.radians(phi_in)))
    outline = bd.Face(bd.Wire([
        bd.Edge.make_line(a, b),
        bd.Edge.make_line(b, p_in),
        _arc(BOSS_R, phi_in, phi_t + 360.0),        # CCW round the far side
        bd.Edge.make_line(t, a),
    ]))
    return outline - bd.Circle(HINGE_HOLE_D / 2)


def _block_profile() -> bd.Face:
    """Arm outside the boss circle: the part of the arm the gear does not cover."""
    a, b, t, phi_t, phi_in = _arm_geometry()
    p_in = _pt(BOSS_R * math.cos(math.radians(phi_in)), BOSS_R * math.sin(math.radians(phi_in)))
    return bd.Face(bd.Wire([
        bd.Edge.make_line(a, b),
        bd.Edge.make_line(b, p_in),
        _arc(BOSS_R, phi_in, phi_t),                 # CW, concave
        bd.Edge.make_line(t, a),
    ]))


def _floor() -> bd.Part:
    """Plan outline (XZ) extruded through the floor thickness, intersected
    with the side profile (XY) that rounds the tongues' bottom front edges."""
    _, b, _, _, _ = _arm_geometry()
    tip = b.X                                        # tongue tip: the arm's inner side
    zp = lambda d: MID_Z + d                         # MP +z side (stepper)
    zn = lambda d: MID_Z - d
    tab0 = STEPPER_BACK_X - STEPPER_TAB_MARGIN
    tab1 = STEPPER_BACK_X + STEPPER_T + STEPPER_TAB_MARGIN
    chamfer = GEAR_OUT - FLOOR_REAR_HALF_W          # 45 deg, rear width -> full width
    plan_pts = [
        (FLOOR_BACK_X, zn(FLOOR_REAR_HALF_W)), (FLOOR_BACK_X, zp(FLOOR_REAR_HALF_W)),
        (tab0, zp(FLOOR_REAR_HALF_W)), (tab0, zp(GEAR_OUT)),          # stepper tab
        (tab1, zp(GEAR_OUT)), (tab1, zp(FLOOR_REAR_HALF_W)),
        (FLOOR_STEP_X_ZPOS - chamfer, zp(FLOOR_REAR_HALF_W)), (FLOOR_STEP_X_ZPOS, zp(GEAR_OUT)),
        (tip, zp(GEAR_OUT)), (tip, zp(GEAR_IN)),                       # gear tongue
        (FLOOR_FRONT_X, zp(GEAR_IN)), (FLOOR_FRONT_X, zp(KNUCKLE_OUT)),
        (tip, zp(KNUCKLE_OUT)), (tip, zp(KNUCKLE_IN)),                 # knuckle tongue
        (FLOOR_FRONT_X, zp(KNUCKLE_IN)), (FLOOR_FRONT_X, zn(KNUCKLE_IN)),
        (tip, zn(KNUCKLE_IN)), (tip, zn(KNUCKLE_OUT)),                 # knuckle tongue
        (FLOOR_FRONT_X, zn(KNUCKLE_OUT)), (FLOOR_FRONT_X, zn(GEAR_IN)),
        (tip, zn(GEAR_IN)), (tip, zn(GEAR_OUT)),                       # gear tongue
        (FLOOR_STEP_X_ZNEG, zn(GEAR_OUT)), (FLOOR_STEP_X_ZNEG - chamfer, zn(FLOOR_REAR_HALF_W)),
    ]
    plan = bd.Face(bd.Wire.make_polygon([_pt(*p) for p in plan_pts], close=True))
    tab_corners = [v for v in plan.vertices()
                   if abs(v.Y - zp(GEAR_OUT)) < 1e-6 and min(abs(v.X - tab0), abs(v.X - tab1)) < 1e-6]
    assert len(tab_corners) == 2, tab_corners
    plan = plan.fillet_2d(STEPPER_TAB_R, tab_corners)
    # local (u, v) -> (X, Z); extruded down (-Y) from the floor top.  Every
    # extrusion here gives its direction: a face's normal follows its winding.
    floor_plane = bd.Plane(origin=(0, FLOOR_TOP_Y, 0), x_dir=(1, 0, 0), z_dir=(0, -1, 0))
    plan_solid = bd.extrude(floor_plane * plan, amount=FLOOR_T, dir=(0, -1, 0))

    r, yt, yb = TONGUE_ROUND_R, FLOOR_TOP_Y, FLOOR_TOP_Y - FLOOR_T
    c = _pt(tip - r, yt)
    side = bd.Face(bd.Wire([
        bd.Edge.make_line(_pt(FLOOR_BACK_X - 1, yb), _pt(tip - r, yb)),
        bd.Edge.make_three_point_arc(_pt(tip - r, yb),
                                     c + _pt(r * math.cos(-math.pi / 4), r * math.sin(-math.pi / 4)),
                                     _pt(tip, yt)),
        bd.Edge.make_line(_pt(tip, yt), _pt(FLOOR_BACK_X - 1, yt)),
        bd.Edge.make_line(_pt(FLOOR_BACK_X - 1, yt), _pt(FLOOR_BACK_X - 1, yb)),
    ]))
    side_solid = bd.extrude(bd.Plane.XY.offset(zn(GEAR_OUT) - 1) * side, amount=2 * GEAR_OUT + 2,
                            dir=(0, 0, 1))
    floor = plan_solid & side_solid

    holes = [bd.Pos(x, yt - FLOOR_T / 2, MID_Z + s * FLOOR_HOLE_HALF_PITCH) * bd.Rot(90, 0, 0)
             * bd.Cylinder(FLOOR_HOLE_D / 2, FLOOR_T + 2)
             for x in FLOOR_HOLE_XS for s in (-1, 1)]
    return floor - holes


def _stepper_plate() -> bd.Part:
    pilot_z = MID_Z + STEPPER_OFFSET
    plate = bd.Pos(STEPPER_BACK_X, FLOOR_TOP_Y, pilot_z - STEPPER_HALF) * bd.Box(
        STEPPER_T, STEPPER_HALF - FLOOR_TOP_Y, 2 * STEPPER_HALF,
        align=(bd.Align.MIN, bd.Align.MIN, bd.Align.MIN))
    x_mid = STEPPER_BACK_X + STEPPER_T / 2
    along_x = bd.Rot(0, 90, 0)
    holes = [bd.Pos(x_mid, 0, pilot_z) * along_x * bd.Cylinder(PILOT_D / 2, STEPPER_T + 2)]
    holes += [bd.Pos(x_mid, sy * SCREW_HALF_PITCH, pilot_z + sz * SCREW_HALF_PITCH) * along_x
              * bd.Cylinder(SCREW_HOLE_D / 2, STEPPER_T + 2)
              for sy in (-1, 1) for sz in (-1, 1)]
    return plate - holes


def _plate() -> bd.Part:
    knuckle = _knuckle_profile()
    knuckles = [bd.extrude(bd.Plane.XY.offset(z0) * knuckle, amount=KNUCKLE_W, dir=(0, 0, 1))
                for z0 in (MID_Z + KNUCKLE_IN, MID_Z - KNUCKLE_OUT)]
    plate = _floor() + knuckles + _stepper_plate()
    return plate.clean()


def _tilt_gear(tooth_sector_rotation_deg: float) -> bd.Part:
    """One 28T gear, z = 0 .. GEAR_W, teeth only on the (rotated) sector."""
    gear = spur_gear(GEAR_MODULE, GEAR_TEETH, GEAR_W, GEAR_PRESSURE_ANGLE,
                     bore=HINGE_HOLE_D, tooth_angle=GEAR_TOOTH_ANGLE + tooth_sector_rotation_deg)
    # toothless sector: CCW from the sector's end round to its start
    a0 = TOOTH_SECTOR_END_DEG + tooth_sector_rotation_deg
    span = (TOOTH_SECTOR_START_DEG - TOOTH_SECTOR_END_DEG) % 360.0
    n = max(2, math.ceil(span / 45.0))
    far = 2.5 * GEAR_OD
    wedge = bd.Face(bd.Wire.make_polygon(
        [_pt(0, 0)] + [_pt(far * math.cos(math.radians(a0 + span * i / n)),
                           far * math.sin(math.radians(a0 + span * i / n))) for i in range(n + 1)],
        close=True))
    rim = (wedge - bd.Circle(SECTOR_CUT_R)) - _arm_polygon()   # the block keeps its teeth
    cut = bd.extrude(bd.Plane.XY.offset(-1) * rim, amount=GEAR_W + 2, dir=(0, 0, 1))
    return gear - cut


def make_mounting_plate(tooth_sector_rotation_deg: float = 0.0) -> bd.Shape:
    """The five bodies as a labelled Compound, in the MP frame.

    ``tooth_sector_rotation_deg`` turns the toothed sector of both 28T gears
    about the hinge axis (MP +Z, counter-clockwise); the hubs, blocks,
    knuckles and everything else stay put.  0 is the Fusion part; 180 meshes
    servo pinions above the hinge (MP +y) instead of below it (MP -y)."""
    plate = _plate()
    plate.label = "plate"
    gear = _tilt_gear(tooth_sector_rotation_deg)
    block = bd.extrude(_block_profile(), amount=GEAR_W, dir=(0, 0, 1))
    z_neg, z_pos = MID_Z + GEAR_IN, MID_Z - GEAR_OUT       # 0 and -95.9
    gear_neg = gear.moved(bd.Location((0, 0, z_neg)))
    gear_neg.label = "gear_neg"
    gear_pos = gear.moved(bd.Location((0, 0, z_pos)))
    gear_pos.label = "gear_pos"
    block_neg = block.moved(bd.Location((0, 0, z_neg)))
    block_neg.label = "block_neg"
    block_pos = block.moved(bd.Location((0, 0, z_pos)))
    block_pos.label = "block_pos"
    return bd.Compound(children=[plate, gear_pos, gear_neg, block_pos, block_neg],
                       label="mounting_plate")


@step(out="../../STEP/parts/mounting_plate.step")
@stl(out="../../STL/parts/mounting_plate.stl")
def mounting_plate():
    return make_mounting_plate(0.0)


if __name__ == "__main__":
    mounting_plate()
