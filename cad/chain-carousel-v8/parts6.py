"""v6 parts (Sam, PR #185, 2026-11-10). parts.py is v2's, parts3.py v3's, parts4.py v4's and parts5.py v5's, all unchanged.

Sam's notes, and the part each one became:
1. "extend the mounting plate so it supports more of the auger. Add another clip about halfway between the gear and the cap"
   -> plate_additions_v6: his Oct 13 plate's front (knuckles, clip 1, gear housing) kept and extended to the cap's end, with
   clip 2 at x 150-162 and a saddle under the cap.
2. "the pin that keeps the mounting plate pinned to the carriage can be moved to the back" and "this mounting plate can rest
   on the base carriage" -> the keeper on the plate's back end; latch_bolt_v6 carries the pin and a rest shelf, so a module
   whose latch the station has opened rests on its own carriage (v5 rested it on a tube rest on the station).
3. "for the kinematic couplings ... integrate them (no need to use a washer, just add it to the 3D printed part" -> printed
   domes at A and B and the plate's own face at C; magnets pressed in under them for the EC's magnets to pull on.
4. "Can the auger go all the way to 90 degrees? If not, adjust the carriage until it can." -> carriage_v6's opening starts
   5 mm further forward; the station gets a separate tilt actuator (ec_additions_v6's tilt arm), see layout.py.
5. "crossbars like a rung of a ladder" -> rungs (layout.py), lift_shelf_v6, guide_block_v6 on them.
6. "a small funnel-type kinematic coupling to the linear actuators guides" -> lift_end_v6's shoes have conical noses that
   seat in a cone (one side) and a vee (the other) at the bottom of guide_block_v6's slots; the slots' mouths are funnels.
Frames are as in parts4/parts5: Sam's studio frame for the module (x along the auger from the hinge axis, y along it, z away
from the plate on the auger's side, plate underside z -18), the carriage frame (u, w, x) for the carriage, EC "as drawn".
"""
from __future__ import annotations

import math

import cadquery as cq

from params import *  # noqa: F401,F403
import parts as PT
import parts3 as P3
import parts4 as P4
import parts5 as P5
from parts3 import _box, _cyl

DR4 = DOCK_RISE_V4


# ---------------------------------------------------------------- 1-3. mounting plate v6
def _cyl_x(r: float, x0: float, x1: float, y: float = 0.0, z: float = 0.0) -> cq.Workplane:
    return cq.Workplane("YZ").center(y, z).circle(r).extrude(x1 - x0).translate((x0, 0, 0))


def plate_additions_v6() -> tuple[cq.Workplane, cq.Workplane]:
    """(added, cut) for mounting plate v6, Sam's frame, applied to his Oct 13 plate (its knuckles, clip 1 at x 26-42 and the
    gear housing at x 66-102 stay as he drew them). Added: the plate carried on from x 98 to the cap's end (252), clip 2 (a C
    round the tube, open toward +z so the auger still pulls straight off), a saddle under the cap, the keeper on the back end,
    and the dock's two domes. Cut: the keeper's pin hole, the three magnet pockets from the underside, the door housing's two
    M2 insert holes (v3's)."""
    x0, x1 = 98.0, PLATE6_X1
    hw = PLATE6_HW
    slab = _box(x0, x1, -hw, hw, -18.0, -13.0).edges("|Z and >X").fillet(4.0)
    # clip 2: a C round the tube, from the plate's face up past the axis
    c0, c1 = CLIP2_X
    ring = _cyl_x(CLIP_R_OUT, c0, c1).cut(_cyl_x(CLIP_R_IN, c0 - 1, c1 + 1)).cut(_box(c0 - 1, c1 + 1, -20, 20, CLIP_TOP, 20))
    foot = _box(c0, c1, -CLIP_R_OUT, CLIP_R_OUT, -13.5, -9.0).cut(_cyl_x(CLIP_R_IN, c0 - 1, c1 + 1))
    clip = ring.union(foot).edges("|X and >Z").chamfer(0.8)
    # a saddle under the cap (R 14.5)
    a0, a1 = CAP_CRADLE_X
    cradle = _box(a0, a1, -17.0, 17.0, -13.5, -5.0).cut(_cyl_x(14.7, a0 - 1, a1 + 1))
    # keeper beside the cap on the back end: y 16-26, up to z -8
    k0, k1 = KEEPER6_X
    keeper = _box(k0, k1, LATCH_Y6 - 5.0, LATCH_Y6 + 5.0, -18.0, -8.0).edges("|X and >Z").fillet(1.0)
    add = slab.union(clip).union(cradle).union(keeper)
    # the dock's plate half, printed: v4's balls' exposed caps (centre z KC4_BALL_Z, R 3.175) at A and B
    r = KC_BALL_D / 2
    for (x, y) in (KC4_A, KC4_B):
        dome = cq.Workplane("XY").sphere(r).translate((x, y, KC4_BALL_Z)).intersect(_box(x - 4, x + 4, y - 4, y + 4, -13.2, 0.0))
        add = add.union(dome)
    d, l, zp = LATCH6_PIN
    cut = _cyl_x(d / 2 + 0.1, k1 - LATCH6_ENGAGE - 0.5, k1 + 0.1, LATCH_Y6, zp)
    for (x, y) in (KC4_A, KC4_B, KC4_C):                      # magnets from the underside: 1.8 mm of plastic left under the face
        cut = cut.union(_cyl(KC6_MAG[0] / 2 + 0.05, KC6_MAG[1] + 0.01, x, y, -18.01))
    for sy in (-1, 1):
        cut = cut.union(_cyl(1.6, 4.0, 18.5, sy * 13.7, -17.0))
    return add, cut


def kc6_magnet() -> cq.Workplane:
    """K&J D42-N52, 1/4 x 1/8 in, from z 0 up."""
    return cq.Workplane("XY").circle(KC6_MAG[0] / 2).extrude(KC6_MAG[1])


# ---------------------------------------------------------------- 2. latch v6: pin + rest shelf on one bolt, at the back
LATCH6_CARRIER = (LATCH6_HOUSING_X[0] + 2.2 + 0.3, 270.0)   # the bolt's printed carrier (x, closed)


def latch_bolt_v6() -> cq.Workplane:
    """Latch bolt v6, Sam's frame, CLOSED: a 4 x 10 mm dowel along x with its tip LATCH6_ENGAGE into the keeper's hole, and a
    printed rest shelf that reaches SHELF6[0] over the keeper's outer face (z -8), both on one printed carrier that slides in
    the housing. The station's cam draws it back LATCH_TRAVEL (4.5): the pin leaves the hole but the shelf is still 3.5 mm
    over the keeper, so the module rests on its own carriage. By hand it goes back LATCH6_MANUAL (10): both clear."""
    k0, k1 = KEEPER6_X
    d, l, zp = LATCH6_PIN
    tip = k1 - LATCH6_ENGAGE
    pin = _cyl_x(d / 2, tip, tip + l, LATCH_Y6, zp).edges("<X").chamfer(0.5)
    c0, c1 = LATCH6_CARRIER
    carrier = _box(c0, c1, LATCH_Y6 - 4.0, LATCH_Y6 + 4.0, zp - 2.8, -4.2)
    sx0 = k1 - SHELF6[0]
    shelf = _box(sx0, c0 + 0.01, LATCH_Y6 - 4.0, LATCH_Y6 + 4.0, -8.0 + 0.2, -8.0 + 0.2 + SHELF6[1]).edges("<X and >Z").chamfer(0.8)
    blk = carrier.union(shelf).cut(_cyl(1.5, 20.0, LATCH6_FOLLOW_X, LATCH_Y6, zp - 5.0))
    return pin.union(blk)


def latch_follower_v6() -> cq.Workplane:
    """3 x 25 mm dowel through the carrier, out past the housing to z +10 behind the cap, along z (parts4's was 40 long, to +24)."""
    z0 = LATCH6_PIN[2] - 2.8
    return _cyl(1.5, LATCH6_FOLLOW_TIP - z0, 0, 0, z0).edges().chamfer(0.3)


def latch_housing_v6() -> cq.Workplane:
    """The latch's printed guide on the carriage's outer face (Sam's z -18) behind the opening: a bore for the pin and a slot
    for the shelf through its front wall, the carrier's channel (cam stroke 4.5 + the 10 mm by hand), a spring pocket behind
    it, and a slot in its outer wall for the follower."""
    x0, x1 = LATCH6_HOUSING_X
    d, l, zp = LATCH6_PIN
    y0, y1 = LATCH_Y6 - 6.5, LATCH_Y6 + 6.5
    h = _box(x0, x1, y0, y1, -18.0, -1.5)
    h = h.cut(_cyl_x(d / 2 + 0.15, x0 - 1, x1 + 1, LATCH_Y6, zp))
    h = h.cut(_box(x0 - 0.1, x0 + 2.6, LATCH_Y6 - 4.2, LATCH_Y6 + 4.2, -8.0, -5.5))           # the shelf's slot
    c0, _ = LATCH6_CARRIER
    h = h.cut(_box(c0 - 0.3, x1 - 3.0, LATCH_Y6 - 4.2, LATCH_Y6 + 4.2, zp - 3.0, -4.0))         # carrier channel + spring pocket
    sl = LATCH_TRAVEL + LATCH6_MANUAL
    h = h.cut(cq.Workplane("XY").center(LATCH6_FOLLOW_X + sl / 2, LATCH_Y6).slot2D(sl + 3.4, 3.4, 0).extrude(10.0).translate((0, 0, -6.0)))
    return h


def latch_spring_v6() -> cq.Workplane:
    """The bolt's spring between the carrier's back and the housing's back wall (closed), along x."""
    c0, c1 = LATCH6_CARRIER
    L = LATCH6_HOUSING_X[1] - 3.0 - c1
    return P3.spring(LATCH_SPRING[0], L, 0.3, 5).rotate((0, 0, 0), (0, 1, 0), 90).translate((c1, LATCH_Y6, LATCH6_PIN[2] + 1.0))


def latch_rail_v6(wall_x: float) -> cq.Workplane:
    """The station's latch cam v6, Sam's frame at the station: parts4.latch_rail_v4's profile at the new follower (x 263,
    y 21): its face at the closed follower's -x edge where the 25 deg ramps end and LATCH_TRAVEL further +x on the flat, so
    it pushes each follower (and the pin) back as the carriage arrives. A web outward of the followers' tips (z 25-31) runs
    back to a foot on the back side plate's inner face (Sam x = wall_x), two M5 through the plate."""
    x_closed = LATCH6_FOLLOW_X - 1.5
    xf = x_closed + LATCH_TRAVEL
    z0, z1 = LATCH6_CAM_Z
    zw0, zw1 = LATCH6_FOLLOW_TIP + 0.5, LATCH6_FOLLOW_TIP + 6.5         # the web, outward of the followers' tips
    half = LATCH_RAIL_FLAT
    ramp = LATCH_TRAVEL / math.tan(math.radians(25))
    lead = 1.5 / math.tan(math.radians(25))
    xb = x_closed - 1.5 - 4.0
    pts = [(xf, -half), (xf, half), (x_closed, half + ramp), (x_closed - 1.5, half + ramp + lead), (xb, half + ramp + lead),
           (xb, -half - ramp - lead), (x_closed - 1.5, -half - ramp - lead), (x_closed, -half - ramp)]
    cam = cq.Workplane("XY").polyline(pts).close().extrude(z1 - z0).translate((0, LATCH_Y6, z0))
    yl = half + ramp + lead
    post = _box(xb, x_closed - 2.0, LATCH_Y6 - yl, LATCH_Y6 + yl, z0, zw0 + 0.01)       # the cam's back, behind the followers' path
    web = _box(xb, wall_x - 6.0, LATCH_Y6 - yl, LATCH_Y6 + yl, zw0, zw1)
    foot = _box(wall_x - 6.0, wall_x, LATCH_Y6 - yl, LATCH_Y6 + yl, zw0, LATCH6_FOOT_Z1)
    for dy in (-9.0, 9.0):
        foot = foot.cut(_cyl_x(2.75, wall_x - 7.0, wall_x + 1.0, LATCH_Y6 + dy, LATCH6_FOOT_HOLE_Z))
    return cam.union(post).union(web).union(foot)


LATCH6_FOOT_Z1 = 30.0                 # the cam's foot on the back plate, Sam z (world 405.65-425): over the tilt bracket (world z <= 394)
LATCH6_FOOT_HOLE_Z = 22.0             # its two M5 holes


# ---------------------------------------------------------------- 3-4. carriage v6
def carriage_v6(print_web: bool = False) -> cq.Workplane:
    """Printed carriage v6 in the carriage frame (X = u, Y = w into the loop, Z = x front -> back): v4's, with the opening
    starting 5 mm further forward (x 14: the plate's front edge passes it at 90 deg, which v5's x 19 stopped), widened to
    +-27.6 over the keeper (Sam x 238-255) as well as over Sam's gear housing, and v6's latch housing behind the opening."""
    u0 = CAR_W / 2
    w0, w1 = CAR_W0 - CAR_T, CAR_W0
    xa, xb = -8.0, CHAIN_L + 8.0
    plate = (cq.Workplane("XY").rect(CAR_W, CAR_T).extrude(xb - xa).translate((0, (w0 + w1) / 2, xa)).edges("|Y").fillet(3))
    for x0, x1 in ((CAR_X0, xa + 1), (xb - 1, CAR_X1)):
        t = (cq.Workplane("XY").rect(TONGUE_W, CAR_T).extrude(x1 - x0).translate((0, (w0 + w1) / 2, x0)).edges("|Y").fillet(2))
        plate = plate.union(t)
    rw, rh = RIB
    rx0, rx1 = 17.0, CHAIN_L - 17.0
    for su in (-1, 1):
        rib = (cq.Workplane("XY").center(su * (u0 - rw / 2), w1 + rh / 2).rect(rw, rh).extrude(rx1 - rx0).translate((0, 0, rx0)))
        plate = plate.union(rib)
    ox0, ox1 = OPEN_X6
    opening = (cq.Workplane("XY").rect(2 * OPEN_U, CAR_T + 2).extrude(ox1 - ox0).translate((0, (w0 + w1) / 2, ox0)).edges("|Y").fillet(3))
    plate = plate.cut(opening)
    for (bx0, bx1, uu) in ((OPEN_BACK_X[0], OPEN_BACK_X[1], OPEN_U_BACK), (238.0, 255.0, OPEN_U_KEEPER)):
        plate = plate.cut(cq.Workplane("XY").rect(2 * uu, CAR_T + 2).extrude(bx1 - bx0).translate((0, (w0 + w1) / 2, HINGE_X + bx0))
                          .edges("|Y").fillet(1.5))
    lug_out = HINGE_W - 8.0
    for su in (-1, 1):
        lug = (cq.Workplane("YZ").center((w0 + lug_out) / 2, HINGE_X).rect(w0 - lug_out, 16).extrude(LUG_T)
               .translate((LUG_U4 if su > 0 else -LUG_U4 - LUG_T, 0, 0)))
        lug = lug.edges("|X and <Y").fillet(7.9)
        plate = plate.union(lug)
    pin = cq.Workplane("YZ").center(HINGE_W, HINGE_X).circle((PIN_D + 0.15) / 2).extrude(2 * u0 + 2).translate((-u0 - 1, 0, 0))
    plate = plate.cut(pin)
    for su in (-1, 1):
        u_out = LUG_U4 + LUG_T
        cb = cq.Workplane("YZ").center(HINGE_W, HINGE_X).circle(PIN_CBORE[0] / 2).extrude(PIN_CBORE[1] + 0.01)
        plate = plate.cut(cb.translate((u_out - PIN_CBORE[1], 0, 0)) if su > 0 else cb.translate((-u_out - 0.01, 0, 0)))
    for x in (A1_HOLE_C, CHAIN_L - A1_HOLE_C):
        plate = plate.cut(cq.Workplane("XZ").center(0, x).circle(3.4 / 2).extrude(CAR_T + 2).translate((0, w1 + 1, 0)))
        plate = plate.cut(cq.Workplane("XZ").center(0, x).circle(6.4 / 2).extrude(TAB_SCREW_CB).translate((0, w0 + TAB_SCREW_CB, 0)))
        plate = plate.union(PT.tab_hook(x > CHAIN_L / 2, print_web).translate((0, 0, x)))
    pin_end = PIN_LEN / 2
    for z0 in (pin_end - 0.8, CHAIN_L - pin_end - 0.8):
        plate = plate.cut(cq.Workplane("XY").center(4.6, 0.0).rect(23.8, 4.8).extrude(1.6).translate((0, 0, z0)))
    for x in (CAR_X0 + 7.0, CAR_X1 - 7.0):
        plate = plate.cut(cq.Workplane("XZ").center(0, x).circle(MAGNET_D / 2 + 0.15).extrude(MAGNET_H + 0.3).translate((0, w1 + 0.01, 0)))
    h = latch_housing_v6().mirror("XZ").mirror("XY")              # Sam's frame -> carriage frame, as carriage_v4
    h = h.rotate((0, 0, 0), (1, 1, 1), -120)
    plate = plate.union(h.translate((0, HINGE_W, HINGE_X)))
    return plate


# ---------------------------------------------------------------- 5. EC v6: hooks on the lift bars, a tilt arm
def _hook_mouth(bx: float, bz: float) -> tuple[float, float]:
    """The direction (EC frame, as drawn: x, z) a bar at (bx, bz) leaves its hook in as the EC turns +tilt about the hinge
    axis: minus the tangent of its arc. World (docked, rel. the hinge) x = bx, z = -(bz + DR4); tangent (-z, x) / r; back to
    the EC frame z -> -z."""
    xw, zw = bx, -(bz + DR4)
    r = math.hypot(xw, zw)
    tx, tz = -zw / r, xw / r
    return -tx, tz


def ec_additions_v6() -> tuple[cq.Workplane, cq.Workplane]:
    """(added, cut) for EC v6, as drawn: EC v5 without its lift-bar saddles. Instead two hooks under its base sit on the lift
    frame's two bars (x 10 and 60): each a U whose mouth points the way its bar leaves as the EC turns about the hinge axis,
    so the frame lifts and lowers the EC (both jaws) and lets go of it only by that turn. And a tilt arm on its +y side
    (Sam y 25-31) out to the tilt pin, 60 mm from the hinge axis at -135 deg (in front of and below the outlet), with a
    2 mm lost-motion slot along the tilt actuator; it stays below the carriage at every tilt."""
    add4, cut4 = P4.ec_additions_v4()
    px, pz = EC_PIN[0], -EC_PIN[1]
    c0, c1 = EC_CHEEK_Y
    zb0 = -(EC_BASE_Z - EC_BASE_T)                                       # base's outer face, as drawn (63.8)
    add = add4.cut(_box(px - 5.5, px + 5.5, -c1 - 0.5, c1 + 0.5, zb0 + 0.01, pz + 6.0))   # v4's clevis cheeks off
    cut = cut4.cut(_box(px - 8.0, px + 8.0, -c1 - 5.0, c1 + 5.0, zb0 - 3.0, pz + 20.0))
    for (x, y) in EC_BALLS:
        cut = cut.cut(_cyl(3.3, 3.0, x, y, zb0 - 2.8))
    for bx in LIFT6_BARS_X:
        bz = LIFT6_BAR_Z
        blk = _box(bx - 7.0, bx + 7.0, -12.0, 12.0, zb0 - 0.01, bz + 9.0).edges("|Y").fillet(2.0)
        add = add.union(blk)
        mx, mz = _hook_mouth(bx, bz)
        ang = math.degrees(math.atan2(mz, mx))
        ch = _box(0.0, 24.0, -13.0, 13.0, -HOOK6_W / 2, HOOK6_W / 2).rotate((0, 0, 0), (0, 1, 0), -ang).translate((bx, 0, bz))
        cut = cut.union(ch).union(_cyl(HOOK6_W / 2, 26.0, bx, -13.0, bz, axis="Y"))
    # tilt arm: Q in the EC frame (as drawn)
    qx, qz = tilt_pin_ec()
    y0, y1 = TILT6_ARM_Y
    arm = (cq.Workplane("XZ").polyline([(16.0, 36.0), (16.0, 56.0), (qx + 2.0, qz + 7.0), (qx - 7.0, qz + 7.0), (qx - 7.0, qz - 7.0),
                                        (qx + 2.0, qz - 7.0)]).close().extrude(-(y1 - y0)).translate((0, y0, 0)))
    bridge = _box(2.4, 16.0, 15.0, y1, 36.0, 56.0)
    add = add.union(arm).union(bridge)
    cut = cut.union(cq.Workplane("XZ").center(qx, qz).slot2D(4.1 + TILT6_SLOT, 4.1, 0).extrude(-(y1 - y0 + 2)).translate((0, y0 - 1, 0)))
    return add, cut


def tilt_pin_ec() -> tuple[float, float]:
    """The tilt pin's (x, z) in the EC's as-drawn frame (world: TILT6_R from the hinge axis at TILT6_PHI0, untilted)."""
    a = math.radians(TILT6_PHI0)
    xw, zw = TILT6_R * math.cos(a), TILT6_R * math.sin(a)
    return xw, -zw - DR4


# ---------------------------------------------------------------- 5-6. the lift frame and its guides
def lift_end_v6() -> cq.Workplane:
    """Printed end block of the lift frame (its frame: origin at the lift P16's rod-end pin; x along the world's x; y outward,
    away from the machine's centre; z up). Clamps on both bars' ends (x -25 and +25, the bars 12 mm in, M3 pinch screws), two
    cheeks round the rod end's 6 mm tab with 2 mm tall slots for its 4 x 16 shoulder screw (v4/v5's lost motion), a web
    joining them, and the guide shoe outboard (14 x 10 x 20) with a 90 deg conical nose under it that seats in its guide's
    cone or vee when the frame is parked."""
    t = 3.1
    dx = (LIFT6_BARS_X[1] - LIFT6_BARS_X[0]) / 2
    body = None
    for sx in (-1, 1):
        c = _box(sx * dx - 7.0, sx * dx + 7.0, -26.0, -12.0, -7.0, 7.0).cut(_cyl(LIFT_BAR_D / 2 + 0.02, 14.6, sx * dx, -26.3, 0, axis="Y"))
        body = c if body is None else body.union(c)
    web = _box(-dx - 6.0, dx + 6.0, -14.0, -t - 5.0 + 0.01, 1.0, 7.0)
    cheeks = _box(-6.0, 6.0, -t - 5.0, -t, -4.5, 8.0).union(_box(-6.0, 6.0, t, t + 5.0, -4.5, 8.0))
    bridge = _box(-6.0, 6.0, -t - 5.0, t + 5.0, 5.0, 8.0)
    shoe = _box(-SHOE[0] / 2, SHOE[0] / 2, t + 5.0 - 0.01, t + 5.0 + SHOE[1], -SHOE[2] / 2, SHOE[2] / 2)
    yc = t + 5.0 + SHOE[1] / 2
    nd, nh = SHOE6_NOSE
    nose = cq.Workplane("XY").add(cq.Solid.makeCone(nd / 2, 0.6, nh, cq.Vector(0, yc, -SHOE[2] / 2 + 0.01), cq.Vector(0, 0, -1)))
    body = body.union(web).union(cheeks).union(bridge).union(shoe).union(nose)
    slot = cq.Workplane("XZ").slot2D(4.1 + EC_SLOT, 4.1, 90).extrude(t + 6.0, both=True)
    cbore = _cyl(3.3, SHOE[1] + 0.2, 0, t + 5.0 - 0.1, 0, axis="Y")
    return body.cut(slot).cut(cbore)


LIFT_END_SHOE_YC = 3.1 + 5.0 + SHOE[1] / 2          # the shoe's (and its nose's) centre along the end block's y


def guide_block_v6(z_rung0: float, z_seat: float, z_top: float, vee: bool) -> cq.Workplane:
    """Printed guide on an upper rung's inner face (its frame: x across, y from the rung's inner face toward the machine's
    centre, z world height). A vertical slot 14.2 wide, open toward the frame, from the seat up: at the top a 45 deg funnel
    GUIDE6_FUNNEL each side, where the shoe leaves it as the EC docks (so in the dock's last 4 mm the cone and vee, not the
    guide, decide where the EC seats) and finds it again on the way down; over the bottom 8 mm it opens GUIDE6_RELIEF each
    side, and the floor has a 90 deg cone (vee=False) or a 90 deg vee along y (vee=True) that the shoe's nose sits in when
    parked: one side fixes the frame's end, the other only its x, so the two P16s park it in the same place every time."""
    w = GUIDE_SLOT_W
    yc_shoe = (STATION_POST_Y - EXT / 2) - (P16_Y + LIFT_END_SHOE_YC)    # the shoe's centre from the rung's inner face (10.9)
    d = yc_shoe + SHOE[1] / 2 + 1.5                                    # 17.4: the lift P16's tube passes 0.6 mm outside it
    blk = _box(-EXT / 2 - 6.0, EXT / 2 + 6.0, 0.0, d, z_rung0, z_top)
    slot = _box(-w / 2, w / 2, 4.0 - 0.01, d + 0.01, z_seat, z_top + 1)
    rel = _box(-w / 2 - GUIDE6_RELIEF, w / 2 + GUIDE6_RELIEF, 4.0 - 0.01, d + 0.01, z_seat, z_seat + 8.0)
    f = GUIDE6_FUNNEL
    fun = (cq.Workplane("XZ").polyline([(-w / 2, z_top - f), (-w / 2 - f, z_top + 0.01), (w / 2 + f, z_top + 0.01), (w / 2, z_top - f)])
           .close().extrude(-(d - 4.0 + 0.02)).translate((0, 4.0 - 0.01, 0)))
    nd, nh = SHOE6_NOSE
    if vee:
        seat = (cq.Workplane("XZ").polyline([(-nd / 2 - 0.3, z_seat + 0.01), (0.0, z_seat - nd / 2 - 0.3), (nd / 2 + 0.3, z_seat + 0.01)]).close()
                .extrude(-(d - 4.0 + 0.02)).translate((0, 4.0 - 0.01, 0)))
    else:
        seat = cq.Workplane("XY").add(cq.Solid.makeCone(nd / 2 + 0.3, 0.0, nd / 2 + 0.3, cq.Vector(0, yc_shoe, z_seat + 0.01), cq.Vector(0, 0, -1)))
    body = blk.cut(slot).cut(rel).cut(fun).cut(seat)
    yh = (STATION_POST_Y - EXT / 2) - P16_Y - 10.5                       # the lift P16's 20 mm housing reaches this close to the rung
    body = body.cut(_box(-30.0, 30.0, yh, d + 1.0, z_rung0 - 1.0, z_seat - nd / 2 - 2.0))   # notch: the housing (top z 309.7) under the seat
    for dx in (-EXT / 2 - 3.0, EXT / 2 + 3.0):                 # two M5 into T-nuts in the rung's inner slot
        body = body.cut(_cyl(2.75, 5.0, dx, -0.5, z_rung0 + EXT / 2, axis="Y"))
    return body


def lift_shelf_v6(z_top: float, z_rung_top: float) -> cq.Workplane:
    """Printed shelf for a lift P16's base clevis on a lower rung (its frame as guide_block_v6's): it sits on the rung's top
    face (two M5 into T-nuts in the top slot) with a lip down its inner face (two more), and reaches in past the P16's axis."""
    reach = STATION_POST_Y - EXT / 2 - P16_Y + 22.0
    top = _box(-24.0, 24.0, -EXT, reach, z_rung_top, z_top)
    lip = _box(-24.0, 24.0, 0.0, 6.0, z_rung_top - EXT, z_rung_top + 0.01)
    return top.union(lip)


def p16_50() -> tuple[cq.Workplane, cq.Workplane]:
    """Actuonix P16-50-22-12-P, the -150's envelope (parts.actuator_p16's stand-in) with 100 mm less tube and rod: retracted
    hole to hole P16L_RETRACTED. Rear clevis hole on the y axis at the origin, rod along +z. (body, rod at full retraction)."""
    housing = cq.Workplane("XY").box(36.0, 20.0, 70.0, centered=False).translate((-25.5, -10.0, 4.5))
    tab = (cq.Workplane("XZ").circle(5.0).extrude(4.0, both=True).union(cq.Workplane("XY").box(10.0, 8.0, 4.6, centered=(True, True, False))))
    tube_top = P16L_RETRACTED - 5.0
    tube = cq.Workplane("XY").box(12.0, 12.0, tube_top - 23.4, centered=False).translate((-6.0, -6.0, 23.4))
    body = housing.union(tab).union(tube).cut(cq.Workplane("XZ").circle(ACT_CLEVIS_D / 2).extrude(20, both=True))
    rl = P16L_STROKE + 15.0
    rod = cq.Workplane("XY").circle(4.47).extrude(rl).translate((0, 0, P16L_RETRACTED - 4.0 - rl))
    end = (cq.Workplane("XY").box(9.0, 6.0, 4.0, centered=(True, True, False)).translate((0, 0, P16L_RETRACTED - 4.0))
           .union(cq.Workplane("XZ").center(0, P16L_RETRACTED).circle(4.5).extrude(3.0, both=True)))
    end = end.intersect(cq.Workplane("XY").box(20, 20, 8.0, centered=(True, True, False)).translate((0, 0, P16L_RETRACTED - 4.0)))
    rod = rod.union(end).cut(cq.Workplane("XZ").center(0, P16L_RETRACTED).circle(ACT_CLEVIS_D / 2).extrude(10, both=True))
    return body, rod


def tilt_bracket_v6() -> cq.Workplane:
    """The tilt P16's base clevis on the back side plate: parts.clevis_bracket with its foot on the plate's inner face (its
    frame: pin along y at the origin, the foot's underside at z = -(plate x - pin x); layout turns it so z points +x)."""
    return PT.clevis_bracket(LAYOUT_TILT_H)


LAYOUT_TILT_H = 335.0 - TILT6_B[0]          # back plate's inner face (x CHAIN_L + SIDE_GAP) -> the tilt P16's base pin
