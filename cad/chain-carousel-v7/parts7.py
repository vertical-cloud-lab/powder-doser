"""v7 parts (Sam, PR #185, 2026-11-10, his second note). parts.py is v2's, parts3-6 v3-v6's, all unchanged.

Sam's notes, and the part each one became:
1. "raise the kinematic couplings on the mounting plate up so that the electronics carriage can be as short as possible, i.e.
   they interface on the scale side of the auger" -> plate_additions_v7: three posts printed on the plate reach past the
   auger (tips 16.4 mm past its axis) with v6's printed domes at A and B and a flat tip at C, a magnet in each post under its
   tip. ec_additions_v7: Sam's carriage turned over, with no arms: the cone, the vee and ball C sit on three ears at its rim.
2. "The linear actuator on the back doesn't work. I like it the way it was before, underneath ... Try to keep it one
   actuator" -> one P16-150 again, pinned to a tail on the EC's back end (under the 44T gear) and to a clevis on a cross bar
   behind the balance; the tail's two shoes run in guide_v7's slots, which keep v6's funnel mouths and cone/vee seats.
3. "I think your model for the scale is wrong ... the draft cage is the main feature, plus the bottom scale" -> balance_v7.
4. The latch is v6's, with its spring pocket made long enough (the profile view found v6's spring would go solid at the
   cam's 4.5 mm and the carrier hit the housing's back wall at 6 mm, short of the 10 mm hand release v6 described).
Frames: Sam's studio frame for the module (x along the auger from the hinge axis, y along it, z away from the plate on the
auger's side, plate underside z -18); the EC "as drawn" (Sam's Oct 13 carriage mirrored z -> -z: docked it sits DOCK_RISE_V4
(-0.9) from that); the carriage frame (u, w, x); world for the station's fixed parts.
"""
from __future__ import annotations

import math

import cadquery as cq

from params import *  # noqa: F401,F403
import parts as PT
import parts3 as P3
import parts6 as P6
from parts3 import _box, _cyl
from parts6 import _cyl_x

DR4 = DOCK_RISE_V4


# ---------------------------------------------------------------- 1. mounting plate v7: v6's, the dock on posts
def plate_additions_v7() -> tuple[cq.Workplane, cq.Workplane]:
    """(added, cut) for mounting plate v7, Sam's frame, on his Oct 13 plate: v6's extension to the cap (slab, clip 2, cap
    saddle, keeper at the back) without v6's domes on the plate's face, and three posts beside the tube (8 x 8, |y| 15.5-23.5)
    from the plate's face (z -13) out to z KC7_TIP past the auger: domes (the 1/4 in balls' exposed caps, 3.75 proud) on A and
    B, a flat tip on C. A D42-N52 sits in each post 1.8 mm under its tip, dropped in at a print pause (the plate prints flat,
    the posts upright)."""
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
    for name, (x, y) in (("A", KC7_A), ("B", KC7_B), ("C", KC7_C)):
        post = _box(x - px / 2, x + px / 2, y - py / 2, y + py / 2, -13.2, KC7_TIP).edges("|Z").fillet(1.0)
        add = add.union(post)
        if name != "C":
            dome = cq.Workplane("XY").sphere(r).translate((x, y, KC7_BALL_Z)).intersect(_box(x - 4, x + 4, y - 4, y + 4, KC7_TIP - 0.01, KC7_TIP + 5))
            add = add.union(dome)
        zm = KC7_TIP - KC7_MAG_DEPTH - KC6_MAG[1]
        cut = cut.union(_cyl(KC6_MAG[0] / 2 + 0.05, KC6_MAG[1] + 0.01, x, y, zm))
    for sy in (-1, 1):
        cut = cut.union(_cyl(1.6, 4.0, 18.5, sy * 13.7, -17.0))
    return add, cut


def plate7_magnet_bases() -> list:
    """(x, y, z) of the three post magnets' lower faces, Sam's frame (each runs +z KC6_MAG[1])."""
    zm = KC7_TIP - KC7_MAG_DEPTH - KC6_MAG[1]
    return [(x, y, zm) for (x, y) in (KC7_A, KC7_B, KC7_C)]


# ---------------------------------------------------------------- 2. EC v7: Sam's carriage turned over, ears, a tail
def _ec7_levels() -> dict:
    """As-drawn z of the dock's features (docked = as drawn + DR4)."""
    zt = KC7_SEAT - DR4                                   # 18.9: seat faces of the cone and the vee (the carriage's rim)
    zb = KC7_BALL_Z - DR4                                 # 17.9: the domes' centres
    c_face = (KC7_TIP - DR4) + (KC_BALL_D - 2.6)          # ball C's pocket face: the ball's tip on post C's flat
    return dict(zt=zt, zb=zb, c_face=c_face)


EC7_EAR_TOP = 31.0


def ec_additions_v7() -> tuple[cq.Workplane, cq.Workplane]:
    """(added, cut) for EC v7, as drawn (Sam's Oct 13 carriage mirrored z -> -z, its rim at z 18.9 facing the plate). No arms,
    no base, no hooks: three ears on the rim carry the dock's EC half (the cone at A and the dowel vee at B, |y| 14-25 outside
    the walls; ball C's ear sits 2.2 mm lower so the ball's tip meets post C's flat), a D44-N52 behind each. At the front,
    v4's door finger. At the back, a tail under the 44T gear: a web (|y| <= 10.5, between the guides' cheeks), a clevis
    for the P16's rod end (pin at EC7_PIN, a 2 mm lost-motion slot along z as v3-v5) and two guide shoes on necks with v6's
    conical noses."""
    lv = _ec7_levels()
    zt, zb, c_face = lv["zt"], lv["zb"], lv["c_face"]
    add = None
    for (x, y), z0 in ((KC7_A, zt), (KC7_B, zt), (KC7_C, c_face)):
        ys = 1 if y > 0 else -1
        ear = _box(x - 5.5, x + 5.5, *sorted((ys * 14.0, ys * 25.0)), z0, EC7_EAR_TOP).edges("|Z").fillet(1.5)
        add = ear if add is None else add.union(ear)
    # door finger (v4's): under the push strip's end, holding it DOOR_TRAVEL in when docked
    fy = DOOR_ROD_Y
    f_top = -(DOOR_ROD_BOTTOM + DOOR_TRAVEL) - DR4
    add = add.union(_box(-3.6, -0.6, fy - 2.0, fy + 2.0, f_top, 26.0)).union(_box(-3.6, 2.4, fy - 2.0, fy + 2.0, 22.0, 26.0))
    # tail
    tx0, tx1 = EC7_TAIL_X
    tz0, tz1 = EC7_TAIL_Z
    web = _box(tx0 - 0.5, tx1, -10.5, 10.5, tz0, tz1)
    px, pz = EC7_PIN
    c0, c1 = EC_CHEEK_Y
    for sy in (-1, 1):                                    # clevis cheeks: rounded R5 about the pin (the P16's tube end is 6 mm past it)
        ya, yb = sorted((sy * c0, sy * c1))
        web = web.union(_box(tx0 - 0.5, px + 5.0, ya, yb, tz0, pz)).union(_cyl(5.0, yb - ya, px, ya, pz, axis="Y"))   # _cyl "Y" runs +y from y
    sx0, sx1 = EC7_SHOE_X
    sy0, sy1 = EC7_SHOE_Y
    sz0, sz1 = EC7_SHOE_Z
    nd, nh = SHOE6_NOSE
    for sy in (-1, 1):
        shoe = _box(sx0, sx1, *sorted((sy * sy0, sy * sy1)), sz0, sz1)
        neck = _box(sx0, sx1, *sorted((sy * 10.0, sy * (sy0 + 0.5))), tz0, tz1)
        nose = cq.Workplane("XY").add(cq.Solid.makeCone(nd / 2, 0.6, nh, cq.Vector((sx0 + sx1) / 2, sy * (sy0 + sy1) / 2, sz1 - 0.01), cq.Vector(0, 0, 1)))
        web = web.union(shoe).union(neck).union(nose)
    add = add.union(web)

    # ---- cuts: v4's cone, vee and ball-C geometry at the new levels
    r = KC_BALL_D / 2
    axx, ayy = KC7_A
    c_contact = zb + r * math.cos(math.radians(KC_CONE_HALF))
    r_contact = r * math.sin(math.radians(KC_CONE_HALF))
    apex = c_contact + r_contact / math.tan(math.radians(KC_CONE_HALF))
    mag_face = zb + r + KC_MAG_GAP
    r_top = (apex - zt) * math.tan(math.radians(KC_CONE_HALF))
    r_mag = (apex - mag_face) * math.tan(math.radians(KC_CONE_HALF))
    cone = cq.Workplane("XY").add(cq.Solid.makeCone(r_top + 0.3, r_mag, mag_face - (zt - 0.3), cq.Vector(axx, ayy, zt - 0.3), cq.Vector(0, 0, 1)))
    cut = cone.union(_cyl(KC_MAG_D / 2 + 0.1, KC_MAG_H + 0.2, axx, ayy, mag_face))
    bxx, byy = KC7_B
    h = math.sqrt((r + VEE_DOWEL_D / 2) ** 2 - (VEE_SPACING / 2) ** 2)
    zd = zb + h
    for sx in (-1, 1):
        # centred on the vee (v4-v6 started this hole at byy + 4.01, but _cyl's "Y" runs +y, so their holes sat 8 mm inboard of the dowels)
        cut = cut.union(_cyl(VEE_DOWEL_D / 2 - 0.02, 8.02, bxx + sx * VEE_SPACING / 2, byy - 4.01, zd, axis="Y"))
    cut = cut.union(_box(bxx - VEE_SPACING / 2 + 0.2, bxx + VEE_SPACING / 2 - 0.2, byy - 4.5, byy + 4.5, zt - 0.5, zd))
    cut = cut.union(_cyl(KC_MAG_D / 2 + 0.1, KC_MAG_H + 0.2, bxx, byy, zd + VEE_DOWEL_D / 2 + 0.4))
    cx, cy = KC7_C
    cut = cut.union(_cyl(3.125, 2.6, cx, cy, c_face - 0.01))
    cut = cut.union(_cyl(KC_MAG_D / 2 + 0.1, min(KC_MAG_H + 0.2, EC7_EAR_TOP - 0.6 - (c_face + 2.6 + 0.4)), cx, cy, c_face + 2.6 + 0.4))
    # the rod end's tab between the cheeks, and the pin's slot
    cut = cut.union(_box(px - 7.0, px + 7.0, -c0 + 0.05, c0 - 0.05, tz0 - 1.0, pz + 6.0))   # room for the 6 mm tab and a 0.8 PTFE washer each side
    cut = cut.union(cq.Workplane("XZ").center(px, pz).slot2D(4.1 + EC_SLOT, 4.1, 90).extrude(12.0, both=True))
    return add, cut


def ec7_ball_c() -> tuple:
    """Ball C's centre on EC v7, as drawn."""
    c_face = _ec7_levels()["c_face"]
    return (KC7_C[0], KC7_C[1], c_face + 2.6 - KC_BALL_D / 2)


def ec7_vee_dowels() -> list:
    bxx, byy = KC7_B
    h = math.sqrt((KC_BALL_D / 2 + VEE_DOWEL_D / 2) ** 2 - (VEE_SPACING / 2) ** 2)
    zd = _ec7_levels()["zb"] + h
    return [(bxx - VEE_SPACING / 2, byy, zd), (bxx + VEE_SPACING / 2, byy, zd)]


def ec7_magnet_faces() -> list:
    """(x, y, face z) of EC v7's three dock magnets, as drawn; each runs +z from its face."""
    lv = _ec7_levels()
    zb, c_face = lv["zb"], lv["c_face"]
    r = KC_BALL_D / 2
    h = math.sqrt((r + VEE_DOWEL_D / 2) ** 2 - (VEE_SPACING / 2) ** 2)
    return [(KC7_A[0], KC7_A[1], zb + r + KC_MAG_GAP), (KC7_B[0], KC7_B[1], zb + h + VEE_DOWEL_D / 2 + 0.5),
            (KC7_C[0], KC7_C[1], c_face + 2.6 + 0.5)]


# ---------------------------------------------------------------- 3. the guides (v6's funnels and seats, at the EC's tail)
def guide_v7(z_bar_top: float, z_seat: float, z_top: float, shoe_x: float, shoe_yc: float, vee: bool) -> cq.Workplane:
    """Printed guide for one of the EC's two shoes, world-aligned (x, y = world y - STATION_Y, z), built for the +y shoe
    (mirror in y for the other). A foot on the guide cross bar's top face (two M5 into T-nuts), and a cheek up to z_top: a
    vertical channel 14.2 wide (x) round the shoe, closed outboard and open toward the EC (its neck runs in the opening). At
    the top v6's 45 deg funnel, GUIDE7_FUNNEL each side, where the shoe leaves it in the dock's last 4 mm (so the dock, not
    the guide, decides where the EC seats) and finds it again on the way down; over the bottom 8 mm the channel opens
    GUIDE7_RELIEF each side, and its floor has a 90 deg cone (vee=False) or a vee along y (vee=True) for the shoe's nose, so
    the parked EC sits in the same place every time."""
    w = GUIDE_SLOT_W
    xc = shoe_x
    y_in, y_out = shoe_yc - 7.5, shoe_yc + 5.5                 # channel: 0.5 mm outside the shoe's outer face; open inboard
    cheek = _box(xc - w / 2 - 5.0, xc + w / 2 + 5.0, y_in, y_out + 5.0, z_bar_top, z_top)
    foot = _box(CROSS7_GUIDE_X - 10.0, CROSS7_GUIDE_X + 10.0, y_in, y_out + 5.0, z_bar_top, z_bar_top + 6.0)
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
    for dx in (-6.0, 6.0):                                     # two M5 down into T-nuts in the bar's top slot
        body = body.cut(_cyl(2.75, 8.0, CROSS7_GUIDE_X + dx, (y_in + y_out + 5.0) / 2, z_bar_top - 1.0))
    return body


# ---------------------------------------------------------------- 4. the balance: a base and a draft cage
def balance_v7(door_left: float = 0.0, door_right: float = 0.0) -> dict[str, cq.Workplane]:
    """An analytical balance as Sam describes the lab's (2026-11-10): the weighing base and the draft cage on it, nothing
    behind the cage over the base's height. Frame as parts5.hr202i: origin on the bench under the pan's centre, x from the
    display (front, -x) back, y across, z up. The chamber, pan and display are v5's HR-202i numbers (183 x 164.5 inside, 250
    over the pan, pan 90 at z 50, 86.5 behind the front glass), so the beaker and the fall are v5's; 200 wide, 253 deep over
    the base, 311 tall (the HR-100A is 198 x 253 x 315). The top door is replaced by a dosing lid: 3 mm acrylic with a 30 mm
    hole on the pan's axis and a printed collar. Side doors slide back (+x) by the given mm."""
    W = HR2_W
    g, fr = BAL7_GLASS, BAL7_FRAME
    cw, cd, chh = HR2_CH
    hw = cw / 2
    cx0 = -86.5                                       # chamber's front glass, inside face
    cx1 = cx0 + cd                                    # back glass, inside face (78)
    zf = HR2_FLOOR
    ztop = HR2_PAN_TOP + chh                          # chamber ceiling (inside): 300
    xb = BAL7_BACK_X
    xs = cx0 - g - fr                                 # the cage's front frame
    x0 = xs - 73.0                                    # the display section's nose
    out: dict[str, cq.Workplane] = {}
    base = _box(x0 + 2.0, xb, -W / 2, W / 2, 3.0, zf).edges("|Z").fillet(6.0)
    n0, n1 = HR2_NOSE
    nose = (cq.Workplane("XZ").polyline([(x0, 3.0), (xs + 1.0, 3.0), (xs + 1.0, n1 + 4), (x0 + 6, n0 + 4), (x0, n0)]).close()
            .extrude(W / 2 - 0.5, both=True))
    base = base.union(nose)
    for fx in (x0 + 25.0, xb - 20.0):
        for fy in (-75.0, 75.0):
            base = base.union(_cyl(9.0, 3.01, fx, fy, 0.0))
    frame = None
    for (xa, xc_) in ((xs, cx0 - g), (cx1 + g, cx1 + g + fr)):
        for sy in (-1, 1):
            ya, yb = sorted((sy * hw, sy * (hw + fr)))
            p = _box(xa, xc_, ya, yb, zf, ztop + g + fr)
            frame = p if frame is None else frame.union(p)
    ring = _box(xs, cx1 + g + fr, -hw - fr, hw + fr, ztop + g, ztop + g + fr).cut(_box(cx0 + 2, cx1 - 2, -hw + 2, hw - 2, ztop, ztop + g + fr + 1))
    sills = _box(xs, cx1 + g + fr, -hw - fr, hw + fr, zf, zf + 6.0).cut(_box(cx0, cx1, -hw, hw, zf - 1, zf + 7))
    out["bal7_base"] = base.union(_cyl(HR2_PAN_D / 2 + 7, 4.0, 0, 0, zf).cut(_cyl(HR2_PAN_D / 2 + 3, 6.0, 0, 0, zf - 1)))
    out["bal7_frame"] = frame.union(ring).union(sills)
    out["bal7_display"] = (cq.Workplane(cq.Plane(origin=((x0 + 6 + xs) / 2, 0.0, (n0 + 4 + n1 + 4) / 2 + 0.4), xDir=(0, 1, 0),
                                                 normal=(-math.sin(math.atan2(n1 - n0, xs - x0 - 6)), 0, math.cos(math.atan2(n1 - n0, xs - x0 - 6)))))
                           .rect(110.0, 30.0).extrude(0.8))
    out["bal7_glass"] = _box(cx0 - g, cx0, -hw, hw, zf + 6, ztop).union(_box(cx1, cx1 + g, -hw, hw, zf + 6, ztop))
    out["bal7_pan"] = _cyl(HR2_PAN_D / 2, 2.0, 0.0, 0.0, HR2_PAN_TOP - 2.0).union(_cyl(7.0, HR2_PAN_TOP - 2.0 - zf + 0.5, 0.0, 0.0, zf - 0.5))
    lid = _box(cx0 + 1.0, cx1 - 1.0, -hw + 1.0, hw - 1.0, ztop, ztop + 3.0).cut(_cyl(BAL7_LID_HOLE / 2, 5.0, 0, 0, ztop - 1))
    collar = _cyl(BAL7_LID_HOLE / 2 + 4.0, 6.0, 0, 0, ztop + 3.0).cut(_cyl(BAL7_LID_HOLE / 2, 8.0, 0, 0, ztop))
    out["bal7_lid"] = lid.union(collar)
    dh = ztop - zf - 6.0 - 3.0
    for name, sy, slide in (("bal7_door_left", -1, door_left), ("bal7_door_right", 1, door_right)):
        yy = sy * (hw + fr / 2)
        xa = cx0 + slide
        pane = _box(xa, xa + cd, yy - g / 2, yy + g / 2, zf + 6, zf + 6 + dh)
        ga, gb = sorted((yy + sy * g / 2, yy + sy * (g / 2 + 7)))
        grip = _box(xa + 4, xa + 16, ga, gb, zf + 60, zf + 200)
        out[name] = pane.union(grip)
    return out


# ---------------------------------------------------------------- 5. the latch: v6's, with room for its spring
LATCH7_CARRIER = (LATCH6_HOUSING_X[0] + 2.2 + 0.3, LATCH7_CARRIER_X1)


def latch_bolt_v7() -> cq.Workplane:
    """v6's latch bolt (pin + rest shelf on one printed carrier), CLOSED, with the carrier 8 mm long (v6: 12) so the spring
    behind it has room, the shelf reaching SHELF7[0] over the keeper (v6: 8), and the pin a 4 x 12 dowel 2 mm into the carrier."""
    k0, k1 = KEEPER6_X
    d, _, zp = LATCH6_PIN
    tip = k1 - LATCH6_ENGAGE
    c0, c1 = LATCH7_CARRIER
    pin = _cyl_x(d / 2, tip, c0 + 2.0, LATCH_Y6, zp).edges("<X").chamfer(0.5)
    carrier = _box(c0, c1, LATCH_Y6 - 4.0, LATCH_Y6 + 4.0, zp - 2.8, -4.2)
    sx0 = k1 - SHELF7[0]
    shelf = _box(sx0, c0 + 0.01, LATCH_Y6 - 4.0, LATCH_Y6 + 4.0, -8.0 + 0.2, -8.0 + 0.2 + SHELF7[1]).edges("<X and >Z").chamfer(0.8)
    blk = carrier.union(shelf).cut(_cyl(1.5, 20.0, LATCH6_FOLLOW_X, LATCH_Y6, zp - 5.0))
    return pin.union(blk)


def latch_housing_v7() -> cq.Workplane:
    """v6's latch housing with the carrier's channel run back to x LATCH7_CHANNEL_X1 (1.5 mm wall left) and the follower's
    slot long enough for the hand release (LATCH7_MANUAL)."""
    x0, x1 = LATCH6_HOUSING_X
    d, _, zp = LATCH6_PIN
    y0, y1 = LATCH_Y6 - 6.5, LATCH_Y6 + 6.5
    h = _box(x0, x1, y0, y1, -18.0, -1.5)
    h = h.cut(_cyl_x(d / 2 + 0.15, x0 - 1, x1 + 1, LATCH_Y6, zp))
    h = h.cut(_box(x0 - 0.1, x0 + 2.6, LATCH_Y6 - 4.2, LATCH_Y6 + 4.2, -8.0, -5.5))
    c0, _ = LATCH7_CARRIER
    h = h.cut(_box(c0 - 0.3, LATCH7_CHANNEL_X1, LATCH_Y6 - 4.2, LATCH_Y6 + 4.2, zp - 3.0, -4.0))
    sl = LATCH7_MANUAL
    h = h.cut(cq.Workplane("XY").center(LATCH6_FOLLOW_X + sl / 2, LATCH_Y6).slot2D(sl + 3.4, 3.4, 0).extrude(10.0).translate((0, 0, -6.0)))
    return h


def latch_spring_v7(travel: float = 0.0) -> cq.Workplane:
    """The bolt's spring between the carrier's back face and the channel's back wall, compressed by the bolt's travel, along x
    (fixed end at the wall: layout places it without moving it)."""
    L = LATCH7_CHANNEL_X1 - (LATCH7_CARRIER_X1 + travel)
    return P3.spring(LATCH7_SPRING[0], max(L, LATCH7_SPRING[3]), 0.3, 6).rotate((0, 0, 0), (0, 1, 0), 90).translate(
        (LATCH7_CARRIER_X1 + travel, LATCH_Y6, LATCH6_PIN[2] + 1.0))


def carriage_v7(print_web: bool = False) -> cq.Workplane:
    """carriage_v6 with latch_housing_v7 in place of v6's housing (same outline; the channel inside runs 4.5 mm further back)."""
    plate = P6.carriage_v6(print_web)
    c0, _ = LATCH7_CARRIER
    d, _, zp = LATCH6_PIN
    chan = _box(c0 - 0.3, LATCH7_CHANNEL_X1, LATCH_Y6 - 4.2, LATCH_Y6 + 4.2, zp - 3.0, -4.0)
    sl = LATCH7_MANUAL
    slot = cq.Workplane("XY").center(LATCH6_FOLLOW_X + sl / 2, LATCH_Y6).slot2D(sl + 3.4, 3.4, 0).extrude(10.0).translate((0, 0, -6.0))
    extra = chan.union(slot).mirror("XZ").mirror("XY").rotate((0, 0, 0), (1, 1, 1), -120).translate((0, HINGE_W, HINGE_X))
    return plate.cut(extra)
