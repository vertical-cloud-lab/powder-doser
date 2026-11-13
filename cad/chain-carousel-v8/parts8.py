"""v8 parts (Sam, PR #185, 2026-11-12). parts.py is v2's, parts3-7 v3-v7's, all unchanged.

Sam's notes, and the part each one became:
1. "design a new electronics carriage more similar to the first design. Flip the solenoid around so it faces the front, not
   the back, and move the solenoid to just in front of the gear" -> ec_v8: his Aug 27 layout (a flat base with the parts
   standing on it), all of it behind the 44T gear's front face but the solenoid: the NEMA 11 now sits BEHIND the gear on a
   motor plate with its shaft forward (v7: in front of the gear, shaft back), the pinion under the gear as before, and the
   solenoid in a cradle just in front of the gear, plunger up under the tube, its frame screwed through the cradle's front
   wall (it faces the front).
2. "You'll also have to move the kinematic couplings, guides, etc." -> plate_additions_v8: v7's three posts moved from in
   front of the gear (x 46.5-64) to behind it (x 104-140), over the EC's base; guide_v8: v7's guides at the EC's back end.
   The outlet door's push strip now carries on back under the tube as a bar (door_shutter_v8), so the EC's finger meets it
   behind the balance instead of at the outlet.
3. "Keep the linear actuator attachment point as close to the front as possible ... the bigger priority is to shorten the z
   distance between the auger and the beaker" -> the P16's pin under the solenoid's cradle (90.6 mm from the hinge; v7: 95).
4. "This should allow the augers to get closer to the scale and the electronics carriage to sit mostly or totally behind
   the scale" -> riser_v8 and balance_v8: the pan's centre 38 mm in front of the exit, the beaker on an offset cup, so the
   cage ends 3 mm in front of the EC; the lid's collar is left off.
Frames: Sam's frame of the station module, DOCKED (x along the auger from the hinge axis, y along it, z away from the plate on
the auger's side: down at the station; auger axis z = 0, plate underside z -18); world for the station's fixed parts.
"""
from __future__ import annotations

import math

import cadquery as cq

from params import *  # noqa: F401,F403
import parts3 as P3
import parts4 as P4
import parts7 as P7
from parts3 import _box, _cyl
from parts6 import _cyl_x


# ---------------------------------------------------------------- 1. mounting plate v8: v7's, the posts behind the gear
def plate_additions_v8() -> tuple[cq.Workplane, cq.Workplane]:
    """(added, cut) for mounting plate v8, Sam's frame, on his Oct 13 plate: v7's extension to the cap (slab, clip 2, cap
    saddle, keeper) with the three dock posts moved behind the gear (x 100-108 and 136-144, |y| 15.5-23.5), and a guide lug
    under clip 1 that the door's bar slides through."""
    x0, x1 = 98.0, PLATE6_X1
    hw = PLATE6_HW
    slab = _box(x0, x1, -hw, hw, -18.0, -13.0).edges("|Z and >X").fillet(4.0)
    c0, c1 = CLIP2_X
    ring = _cyl_x(CLIP_R_OUT, c0, c1).cut(_cyl_x(CLIP_R_IN, c0 - 1, c1 + 1)).cut(_box(c0 - 1, c1 + 1, -20, 20, CLIP_TOP, 20))
    foot = _box(c0, c1, -CLIP_R_OUT, CLIP_R_OUT, -13.5, -9.0).cut(_cyl_x(CLIP_R_IN, c0 - 1, c1 + 1))
    clip = ring.union(foot).edges("|X and >Z").chamfer(0.8)
    a0, a1 = CAP_CRADLE_X
    cradle = _box(a0, a1, -17.0, 17.0, -13.5, -5.0).cut(_cyl_x(14.7, a0 - 1, a1 + 1))
    k0, k1 = KEEPER6_X
    keeper = _box(k0, k1, LATCH_Y6 - 5.0, LATCH_Y6 + 5.0, -18.0, -8.0).edges("|X and >Z").fillet(1.0)
    add = slab.union(clip).union(cradle).union(keeper)
    px, py = KC7_POST
    r = KC_BALL_D / 2
    cut = _cyl_x(LATCH6_PIN[0] / 2 + 0.1, k1 - LATCH6_ENGAGE - 0.5, k1 + 0.1, LATCH_Y6, LATCH6_PIN[2])
    for name, (x, y) in (("A", KC8_A), ("B", KC8_B), ("C", KC8_C)):
        post = _box(x - px / 2, x + px / 2, y - py / 2, y + py / 2, -13.2, KC7_TIP).edges("|Z").fillet(1.0)
        add = add.union(post)
        if name != "C":
            dome = cq.Workplane("XY").sphere(r).translate((x, y, KC7_BALL_Z)).intersect(_box(x - 4, x + 4, y - 4, y + 4, KC7_TIP - 0.01, KC7_TIP + 5))
            add = add.union(dome)
        zm = KC7_TIP - KC7_MAG_DEPTH - KC6_MAG[1]
        cut = cut.union(_cyl(KC6_MAG[0] / 2 + 0.05, KC6_MAG[1] + 0.01, x, y, zm))
    # the door bar's guide lug, hanging from the plate's face beside the tube near the bar's end (it slides 6 mm along z in the slot)
    g0, g1 = DOOR8_LUG_X
    yb = door8_bar_y()
    h0, h1 = DOOR8_HIGH
    lug = _box(g0, g1, yb[0] - 1.5, yb[1] + 2.0, -13.2, h1 + 2.0)
    add = add.union(lug)
    cut = cut.union(_box(g0 - 0.1, g1 + 0.1, yb[0] - 0.25, yb[1] + 0.25, h0 - DOOR_TRAVEL - 2.0, h1 + 0.25))
    for sy in (-1, 1):
        cut = cut.union(_cyl(1.6, 4.0, 18.5, sy * 13.7, -17.0))
    return add, cut


def plate8_magnet_bases() -> list:
    zm = KC7_TIP - KC7_MAG_DEPTH - KC6_MAG[1]
    return [(x, y, zm) for (x, y) in (KC8_A, KC8_B, KC8_C)]


def door8_bar_y() -> tuple[float, float]:
    """The bar's y span beside the tube, outside clip 1 (R16.5) and the tube."""
    return (18.0, 18.0 + DOOR8_BAR[0])


DOOR8_LOW = (20.0, 22.0)             # the low run (z, closed): under the knuckles, from the strip's end to x 15
DOOR8_HIGH = (8.0, 10.0)             # the high run (z, closed) beside the tube from x 15 to the EC: it crosses the draft cage's back
                                     # frame (Sam x 38-51) 10 mm higher than the low run would, and open (6 mm up) it is still 2 mm off
                                     # the plate's lug slot's top
DOOR8_STEP_X = 15.0
DOOR8_LUG_X = (46.0, 52.0)           # the bar's guide lug, hanging from the plate between clip 1 (x 26-42) and the gear housing (66)


def door8_bar_z() -> tuple[float, float]:
    """The high run's z span, closed (the EC's finger meets its end)."""
    return DOOR8_HIGH


def door_shutter_v8() -> cq.Workplane:
    """v4's shutter (closed, Sam's frame) with its push strip carried on back to the EC as a bar: from the strip's end (y 6-9,
    z 20-22) a jog out to y 18-21 under the knuckles, a low run to x 15, a riser, and a high run (z 8-10) beside the tube back to
    x 58, over the EC's finger. 3 x 2 mm, printed in one piece with the shutter (PETG)."""
    s = P4.door_shutter_v4()
    y0, y1 = door8_bar_y()
    l0, l1 = DOOR8_LOW
    h0, h1 = DOOR8_HIGH
    jog = _box(P3.DOOR_XF, 3.0, DOOR_ROD_Y - DOOR_ROD_D / 2, y1, l0, l1)
    low = _box(0.0, DOOR8_STEP_X + DOOR8_BAR[0], y0, y1, l0, l1)
    riser = _box(DOOR8_STEP_X, DOOR8_STEP_X + DOOR8_BAR[0], y0, y1, h0, l1)
    high = _box(DOOR8_STEP_X, DOOR8_BAR_X1, y0, y1, h0, h1)
    return s.union(jog).union(low).union(riser).union(high)


# ---------------------------------------------------------------- 2. EC v8: Sam's Aug 27 layout, behind the balance
def _dock_levels() -> dict:
    zt = KC7_SEAT                                          # 18: the cone's and vee's seat faces, docked
    zb = KC7_BALL_Z                                        # 17: the domes' centres
    c_face = KC7_TIP + (KC_BALL_D - 2.6)                   # ball C's pocket face: its tip on post C's flat
    return dict(zt=zt, zb=zb, c_face=c_face)


def ec_v8() -> cq.Workplane:
    """Electronics carriage v8, printed PETG, Sam's frame, DOCKED. Sam's Aug 27 layout: a flat base (x 58-150, |y| <= 25, z
    47-51) with the parts standing on it, on the scale side of the auger. From the front: the door finger (x 54-58) under the
    door bar's end; the solenoid's cradle (x 57.5-73.5), the solenoid standing in it plunger up, screwed through the cradle's
    front wall; the pinion under the gear (on the motor's shaft, not part of this solid); the motor plate (x 88.8-93.8) with
    the NEMA 11 behind it, its body over the base; three ears beside the motor with the dock's EC half (the cone at A and the
    dowel vee at B at x 104, ball C at x 140, a D44-N52 behind each); at the back two guide shoes with conical noses. Under
    the cradle, the clevis for the P16's rod end (pin at EC8_PIN, a 2 mm lost-motion slot along z as v3-v7)."""
    lv = _dock_levels()
    zt, zb, c_face = lv["zt"], lv["zb"], lv["c_face"]
    hw = EC8_HW
    zb0, zb1 = EC8_BASE_Z
    base = _box(56.0, 136.0, -hw, hw, zb0, zb1).edges("|Z").fillet(4.0)          # ends before the guides' cheeks (Sam x 138+)
    base = base.union(_box(130.0, EC8_BACK, -10.5, 10.5, zb0, zb1))                  # a neck between the guides back to the shoes
    # the solenoid's cradle: front wall, side walls and floor round the frame (x 59-73, |y| 8.5), open at the back (the shaft
    # ends at x 78.3) and at the top (the plunger)
    fx, fy, fz = SOL8_FRAME
    sx0, sx1 = SOL8_X - fx / 2, SOL8_X + fx / 2
    zs1 = SOL8_TOP + fz                                    # 53.7: the frame's bottom
    cradle = _box(56.0, sx1 + 0.5, -fy / 2 - 2.0, fy / 2 + 2.0, SOL8_TOP + 6.0, EC8_CRADLE_Z1)
    cradle = cradle.cut(_box(sx0 - 0.2, sx1 + 1.0, -fy / 2 - 0.2, fy / 2 + 0.2, SOL8_TOP - 1.0, zs1 + 0.2))
    for dy in (-5.0, 5.0):                                 # two M3 through the front wall into the solenoid's frame (it faces the front)
        cradle = cradle.cut(_cyl(1.7, 4.0, 55.5, dy, 38.0, axis="X"))
    body = base.union(cradle)
    # the door finger, at the front, under the bar's end (pushes it 6 mm up in the dock's last 6 mm)
    y0, y1 = door8_bar_y()
    f_top = door8_bar_z()[1] - DOOR_TRAVEL                 # 4: the high run's underside when open
    body = body.union(_box(FINGER8_X[0], FINGER8_X[1], y0 - 0.5, y1 + 0.5, f_top, SOL8_TOP + 10.0))
    body = body.union(_box(FINGER8_X[0], 58.0, fy / 2 + 1.0, y1 + 0.5, SOL8_TOP + 4.0, SOL8_TOP + 10.0))
    # the motor plate: a 22.4 pilot hole for the boss, the 23 mm square of M2.5 clearance holes
    m0, m1 = MOTOR8_PLATE_X
    mp = _box(m0, m1, -14.5, 14.5, 17.5, zb1).cut(cq.Workplane("YZ").center(0, MOTOR8_Z).circle(11.2).extrude(m1 - m0 + 2).translate((m0 - 1, 0, 0)))
    for dy in (-11.5, 11.5):
        for dz in (-11.5, 11.5):
            mp = mp.cut(cq.Workplane("YZ").center(dy, MOTOR8_Z + dz).circle(1.4).extrude(m1 - m0 + 2).translate((m0 - 1, 0, 0)))
    body = body.union(mp)
    # ears for the dock, beside the motor (|y| 15-25), from the seat faces down to the base
    for (x, y), z0 in ((KC8_A, zt), (KC8_B, zt), (KC8_C, c_face)):
        ys = 1 if y > 0 else -1
        ear = _box(x - 5.5, x + 5.5, *sorted((ys * 15.0, ys * 25.0)), z0, zb1).edges("|Z").fillet(1.5)
        body = body.union(ear)
    # the clevis for the P16's rod end, under the cradle: two cheeks 9.6 apart, rounded R5 about the pin
    px, pz = EC8_PIN
    c0, c1 = EC_CHEEK_Y
    for sy in (-1, 1):
        ya, yb = sorted((sy * c0, sy * c1))
        body = body.union(_box(px - 5.0, px + 5.0, ya, yb, EC8_CRADLE_Z1 - 0.5, pz)).union(_cyl(5.0, yb - ya, px, ya, pz, axis="Y"))
    # the shoes at the back end, on necks off the base, conical noses down (+z) into the guides' seats
    sx0_, sx1_ = EC8_SHOE_X
    sy0, sy1 = EC8_SHOE_Y
    sz0, sz1 = EC8_SHOE_Z
    nd, nh = SHOE6_NOSE
    for sy in (-1, 1):
        shoe = _box(sx0_, sx1_, *sorted((sy * sy0, sy * sy1)), sz0, sz1)
        nose = cq.Workplane("XY").add(cq.Solid.makeCone(nd / 2, 0.6, nh, cq.Vector((sx0_ + sx1_) / 2, sy * (sy0 + sy1) / 2, sz1 - 0.01), cq.Vector(0, 0, 1)))
        body = body.union(shoe).union(nose)
    body = body.union(_box(sx0_, EC8_BACK, -sy1, sy1, zb0, zb1))
    # ---- cuts: v7's cone, vee and ball-C pockets at A, B, C
    r = KC_BALL_D / 2
    cut = None
    axx, ayy = KC8_A
    c_contact = zb + r * math.cos(math.radians(KC_CONE_HALF))
    r_contact = r * math.sin(math.radians(KC_CONE_HALF))
    apex = c_contact + r_contact / math.tan(math.radians(KC_CONE_HALF))
    mag_face = zb + r + KC_MAG_GAP
    r_top = (apex - zt) * math.tan(math.radians(KC_CONE_HALF))
    r_mag = (apex - mag_face) * math.tan(math.radians(KC_CONE_HALF))
    cone = cq.Workplane("XY").add(cq.Solid.makeCone(r_top + 0.3, r_mag, mag_face - (zt - 0.3), cq.Vector(axx, ayy, zt - 0.3), cq.Vector(0, 0, 1)))
    cut = cone.union(_cyl(KC_MAG_D / 2 + 0.1, KC_MAG_H + 0.2, axx, ayy, mag_face))
    bxx, byy = KC8_B
    h = math.sqrt((r + VEE_DOWEL_D / 2) ** 2 - (VEE_SPACING / 2) ** 2)
    zd = zb + h
    for s_ in (-1, 1):
        cut = cut.union(_cyl(VEE_DOWEL_D / 2 - 0.02, 8.02, bxx + s_ * VEE_SPACING / 2, byy - 4.01, zd, axis="Y"))
    cut = cut.union(_box(bxx - VEE_SPACING / 2 + 0.2, bxx + VEE_SPACING / 2 - 0.2, byy - 4.5, byy + 4.5, zt - 0.5, zd))
    cut = cut.union(_cyl(KC_MAG_D / 2 + 0.1, KC_MAG_H + 0.2, bxx, byy, zd + VEE_DOWEL_D / 2 + 0.4))
    cx, cy = KC8_C
    cut = cut.union(_cyl(3.125, 2.6, cx, cy, c_face - 0.01))
    cut = cut.union(_cyl(KC_MAG_D / 2 + 0.1, KC_MAG_H + 0.2, cx, cy, c_face + 2.6 + 0.4))
    # the rod end's tab between the cheeks, and the pin's slot
    cut = cut.union(_box(px - 7.0, px + 7.0, -c0 + 0.05, c0 - 0.05, EC8_CRADLE_Z1 - 1.0, pz + 6.0))
    cut = cut.union(cq.Workplane("XZ").center(px, pz).slot2D(4.1 + EC_SLOT, 4.1, 90).extrude(12.0, both=True))
    return body.cut(cut)


def ec8_ball_c() -> tuple:
    c_face = _dock_levels()["c_face"]
    return (KC8_C[0], KC8_C[1], c_face + 2.6 - KC_BALL_D / 2)


def ec8_vee_dowels() -> list:
    bxx, byy = KC8_B
    h = math.sqrt((KC_BALL_D / 2 + VEE_DOWEL_D / 2) ** 2 - (VEE_SPACING / 2) ** 2)
    zd = _dock_levels()["zb"] + h
    return [(bxx - VEE_SPACING / 2, byy, zd), (bxx + VEE_SPACING / 2, byy, zd)]


def ec8_magnet_faces() -> list:
    """(x, y, face z) of EC v8's three dock magnets, docked; each runs +z from its face."""
    lv = _dock_levels()
    zb, c_face = lv["zb"], lv["c_face"]
    r = KC_BALL_D / 2
    h = math.sqrt((r + VEE_DOWEL_D / 2) ** 2 - (VEE_SPACING / 2) ** 2)
    return [(KC8_A[0], KC8_A[1], zb + r + KC_MAG_GAP), (KC8_B[0], KC8_B[1], zb + h + VEE_DOWEL_D / 2 + 0.5),
            (KC8_C[0], KC8_C[1], c_face + 2.6 + 0.5)]


# ---------------------------------------------------------------- 3. the guides (v7's, at the EC's back end)
GUIDE8_TAB = 12.0


def guide8_screw_y(shoe_yc: float) -> float:
    return shoe_yc + 5.5 + 5.0 + GUIDE8_TAB / 2


def guide_v8(bar_x: float, z_bar_top: float, z_seat: float, z_top: float, shoe_x: float, shoe_yc: float, vee: bool) -> cq.Workplane:
    """v7's guide (a channel round one shoe with v6's 45 deg funnel mouth, a 0.5 mm relief over its bottom 8 mm and a cone or
    vee seat in its floor) on a foot on the guide cross bar at world x bar_x; world-aligned (x, y = world y - STATION_Y, z),
    built for the +y shoe."""
    w = GUIDE_SLOT_W
    xc = shoe_x
    y_in, y_out = shoe_yc - 7.5, shoe_yc + 5.5
    cheek = _box(xc - w / 2 - 5.0, xc + w / 2 + 5.0, y_in, y_out + 5.0, z_bar_top, z_top)
    foot = _box(min(xc - w / 2 - 5.0, bar_x - 10.0), bar_x + 10.0, y_in, y_out + 5.0 + GUIDE8_TAB, z_bar_top, z_bar_top + 6.0)
    body = cheek.union(foot)
    body = body.cut(_box(xc - w / 2, xc + w / 2, y_in - 0.01, y_out, z_seat, z_top + 1))
    body = body.cut(_box(xc - w / 2 - GUIDE7_RELIEF, xc + w / 2 + GUIDE7_RELIEF, y_in - 0.01, y_out, z_seat, z_seat + 8.0))
    f = GUIDE7_FUNNEL
    fun = (cq.Workplane("XZ").polyline([(xc - w / 2, z_top - f), (xc - w / 2 - f, z_top + 0.01), (xc + w / 2 + f, z_top + 0.01), (xc + w / 2, z_top - f)])
           .close().extrude(-(y_out - y_in + 0.02)).translate((0, y_in - 0.01, 0)))
    body = body.cut(fun)
    nd, nh = SHOE6_NOSE
    if vee:
        seat = (cq.Workplane("XZ").polyline([(xc - nd / 2 - 0.3, z_seat + 0.01), (xc, z_seat - nd / 2 - 0.3), (xc + nd / 2 + 0.3, z_seat + 0.01)]).close()
                .extrude(-(y_out - y_in + 0.02)).translate((0, y_in - 0.01, 0)))
    else:
        seat = cq.Workplane("XY").add(cq.Solid.makeCone(nd / 2 + 0.3, 0.0, nd / 2 + 0.3, cq.Vector(xc, shoe_yc, z_seat + 0.01), cq.Vector(0, 0, -1)))
    body = body.cut(seat)
    for dx in (-6.0, 6.0):
        body = body.cut(_cyl(2.75, 8.0, bar_x + dx, guide8_screw_y(shoe_yc), z_bar_top - 1.0))
    return body


# ---------------------------------------------------------------- 4. the balance: v7's, the lid without its collar; the riser
def balance_v8(door_left: float = 0.0, door_right: float = 0.0) -> dict[str, cq.Workplane]:
    """v7's balance (a base and a draft cage) with the dosing lid's hole moved 38 mm behind the pan's centre (under the exit)
    and no collar round it. Frame: origin on the bench under the pan's centre."""
    out = P7.balance_v7(door_left, door_right)
    cw, cd, chh = HR2_CH
    hw = cw / 2
    cx0 = -86.5
    cx1 = cx0 + cd
    ztop = HR2_PAN_TOP + chh
    lid = _box(cx0 + 1.0, cx1 - 1.0, -hw + 1.0, hw - 1.0, ztop, ztop + 3.0).cut(_cyl(BAL7_LID_HOLE / 2, 5.0, PAN8_AHEAD, 0, ztop - 1))
    out["bal7_lid"] = lid
    return out


def riser_v8() -> cq.Workplane:
    """Printed PETG riser on the pan (frame: origin on the pan's top at its centre): v5's 80 mm foot and 44 mm tube, and at the
    top an arm that carries the beaker's cup RISER8_ARM (38 mm) back, under the exit. The cup's rim height is v5's."""
    h = BEAKER_RISER_H
    foot = _cyl(BRISER_FOOT_D / 2, 3.0, 0, 0, 0)
    tube = _cyl(BRISER_TUBE_D / 2, h - 8.0, 0, 0, 0).cut(_cyl(BRISER_TUBE_D / 2 - BRISER_WALL, h - 11.0, 0, 0, -0.01))
    a = RISER8_ARM
    arm = _box(0.0, a, -12.0, 12.0, h - 14.0, h - 8.0).union(_cyl(BRISER_TUBE_D / 2, 6.0, 0, 0, h - 14.0))
    web = (cq.Workplane("XZ").polyline([(BRISER_TUBE_D / 2 - 2.0, h - 50.0), (a - 8.0, h - 14.0), (BRISER_TUBE_D / 2 - 2.0, h - 14.0)]).close()
           .extrude(3.0, both=True))
    cup = _cyl(BEAKER_D / 2 + 3.0, 8.0, a, 0, h - 8.0).cut(_cyl(BEAKER_D / 2 + 0.4, 9.0, a, 0, h - 5.0))
    return foot.union(tube).union(arm).union(web).union(_cyl(BEAKER_D / 2 + 3.0, 6.0, a, 0, h - 14.0)).union(cup)


# ---------------------------------------------------------------- 5. the front cover: brush strips round the balance's notch
def brush_strip(length: float, along_y: bool = False) -> cq.Workplane:
    """A brush strip (nylon bristles in an aluminium holder): the holder 12 wide x 8 deep, the bristles 9 mm on past it, along
    +z (or +y). Frame: the holder's corner at the origin, x 0-8 (into the frame from the panel), the bristles toward +y (or +z) from
    y 12 (z 12)."""
    if along_y:
        holder = _box(0.0, 8.0, 0.0, length, -12.0, 0.0)
        bristles = _box(2.0, 6.0, 12.0, length - 12.0, -21.0, -12.0)
        return holder.union(bristles).translate((0, 0, 12.0))
    holder = _box(0.0, 8.0, 0.0, 12.0, 0.0, length)
    bristles = _box(2.0, 6.0, 12.0, 21.0, 0.0, length - 12.0)
    return holder.union(bristles)
