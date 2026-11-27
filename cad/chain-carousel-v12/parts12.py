"""v12 parts (Sterling, PR #185, 2026-11-27): v11 with the spring-loaded pinion the v11 gear study proposed. parts.py ... parts11.py are
v2-v11's, unchanged. What v12 adds or changes:

1. cradle_v12: the NEMA 11 and its 24T pinion on a printed cradle. The cradle's motor plate is v11's EC motor plate (the motor's face
   bolts to it); a pivot tube runs along the motor's -y side on two 3 x 12 mm dowels (along x, level with the pinion's axis, 18.5 mm to
   the side the gears arrive from); a top bar over the motor carries the spring's seat; a lug on the motor's +y side carries the stop's
   set screw and the hall switch.
2. The spring (1 N/mm, 6 N at the stop) between the top bar and the EC's roof, on the pinion's line (18.5 mm from the pivot, like the
   pinion), so its rate and force are the pinion's. The stop: an M3 cup-point set screw down through the lug onto the arm's top, 0.4 mm
   past tight mesh. The hall switch (US5881) on the lug's +y face; its magnet in a post on the EC beside it.
3. ec_v12: EC v11 with its motor plate, cheeks and strap replaced by the cradle's pivot bosses, an outer -y rail and a cross bar behind
   the motor, a roof over the spring with an up-stop pad, the switch's magnet post, and a second guide shoe on the far (-y) side.
4. guide_hanger_v12: the second shoe's seat on a hanger from a second station beam (world y +56, the first beam's mirror).
Frames: Sam's studio frame for the EC and the cradle (the cradle drawn in tight mesh, layout.cradle12_M turns it about its pivot);
world for the hanger.
"""
from __future__ import annotations

import math

import cadquery as cq

from params import *  # noqa: F401,F403
import parts as PT
import parts3 as P3
import parts10 as P10
import parts11 as P11
from parts3 import _box, _cyl
from parts6 import _cyl_x

PY, PZ = CRADLE12_PIV
NEMA11_SCREWS = [(dy, PINION12_Z + dz) for dy in (-11.5, 11.5) for dz in (-11.5, 11.5)]   # M2.5 on the NEMA 11's 23 mm square


# ---------------------------------------------------------------- 1. the cradle
def cradle_v12() -> cq.Workplane:
    """Printed cradle (PETG), Sam's frame in tight mesh (pinion axis at z PINION12_Z):
    - the motor plate x 89.9-93.5 (the NEMA 11's face on its back, its boss in a 22.4 mm bore, four M2.5 x 6 from the front);
    - the pivot tube, 7 x 7 round the dowels' axis (y -18.5, z -34), from the plate back along the motor's -y side to x 136.5;
    - the top bar over the motor (0.3 mm off it), the spring's seat (a 1 mm counterbore and a 3 mm peg) on its far face;
    - the lug on the motor's +y side, 2 mm over the EC's arm: an M3 heat-set insert for the stop's set screw, the hall switch's pocket
      on its +y face."""
    p0, p1 = CRADLE12_PLATE_X
    zc = PINION12_Z
    # the plate: the motor's square from the pivot boss's side to y 14.5, from the top bar's far face (z -51.5) down to z -20.0; above
    # z -32 it runs on out to the lug. 2026-11-27 (Bambu Studio, v12's first slice): the plate stopped at z -49 and y 14, so the top bar
    # hung on a 0.7 mm strip of it and two counterbores broke out of its edges
    tx0_, tx1_, hw_, zn_, zf_ = CRADLE12_TOP
    plate = _box(p0, p1, -16.0, 14.5, zf_, zc + 14.0)                   # -y edge at -16 over the tube: lifted, it swings toward the EC's rail
    plate = plate.union(_box(p0, p1, 13.9, CRADLE12_LUG[3], CRADLE12_LUG[5], CRADLE12_LUG[4]))
    plate = plate.cut(_cyl_x(11.2, p0 - 1.0, p1 + 1.0, 0.0, zc))                     # the motor's 22 mm boss
    for (y, z) in NEMA11_SCREWS:
        plate = plate.cut(_cyl_x(1.45, p0 - 1.0, p1 + 1.0, y, z))                   # M2.5 clearance
        if z > zc:   # the two lower heads counterbored 1.5 mm, so they stay 0.5 mm behind the passing 44T gears' back face (x 88.4)
            plate = plate.cut(_cyl_x(2.3, p0 - 1.0, p0 + 1.5, y, z))
    t0, t1 = CRADLE12_TUBE
    tube = _box(t0, t1, PY - 3.5, PY + 3.5, PZ - 3.5, PZ + 3.5).edges("|X").fillet(1.5)
    # the tube is solid only at its two bosses (where the dowels run), hollow-free between them: a 7 x 7 bar
    tx0, tx1, hw, zn, zf = CRADLE12_TOP
    top = _box(tx0, tx1, -hw, hw, zf, zn)
    lx0, lx1, ly0, ly1, lzn, lzf = CRADLE12_LUG
    lug = _box(lx0, lx1, ly0, ly1, lzf, lzn)
    # the top bar's two cheeks down the motor's sides to the tube (-y) and the lug (+y) at the plate's back, x 93.5-97.5
    web_m = _box(p1 - 0.01, p1 + 4.0, -16.0, -14.3, zf, PZ + 3.5)
    web_p = _box(p1 - 0.01, p1 + 4.0, 14.3, 16.0, zf, lzn)                 # 2026-11-27: was 0.31 mm thick (y 14.3-14.61)
    c = plate.union(tube).union(top).union(lug).union(web_m).union(web_p)
    # back: a ring of the top bar's far end down the -y side to the tube's back boss (stiffens the tube)
    c = c.union(_box(tx1 - 4.0, tx1, -16.0, -14.3, zf, PZ + 3.5))
    # the dowels' bores (3.1, free) at both ends of the tube
    c = c.cut(_cyl_x(1.55, t0 - 1.0, t1 + 1.0, PY, PZ))
    # the spring's seat: counterbore 1 mm deep, a 3 mm peg 2 mm tall inside the spring
    sx = SPRING12_X
    c = c.cut(_cyl(SPRING12_OD / 2 + 0.3, 1.0, sx, 0.0, zf - 0.01).translate((0, 0, 0))).union(_cyl(1.5, 2.0 + 1.0, sx, 0.0, zf - 2.0))
    # the stop's set screw: an M3 heat-set insert (4.0 hole) through the lug, along z
    ssx, ssy = SETSCREW12_XY
    c = c.cut(_cyl(2.0, lzn - lzf + 2.0, ssx, ssy, lzf - 1.0))
    # the hall switch's pocket in the lug's +y face: the US5881's 4.1 x 3.0 x 1.5 body, branded face out, leads up into a 3 mm slot
    hx, hy, hz = HALL12_XYZ
    c = c.cut(_box(hx - 2.1, hx + 2.1, ly1 - 1.55, ly1 + 0.1, hz - 1.55, hz + 1.55))
    c = c.cut(_box(hx - 1.5, hx + 1.5, ly1 - 1.0, ly1 + 0.1, lzf - 0.1, hz))
    return c.clean()


def pivot_dowel_v12() -> cq.Workplane:
    """3 x 12 mm 18-8 stainless dowel along +x from x = 0, centred on the y/z origin (layout puts it on the pivot axis)."""
    d, L = PIN12
    return _cyl_x(d / 2, 0.0, L).edges().chamfer(0.25)


def spring_v12(length: float) -> cq.Workplane:
    """The cradle's compression spring at a given length, along -z from z = 0 (its seat on the top bar's far face), Sam's frame offsets
    applied by layout."""
    return P3.spring(SPRING12_OD, length, 0.56, 9).mirror("XY")


def set_screw_m3x6() -> cq.Workplane:
    """M3 x 6 flat-point set screw (McMaster 92605A100), its tip at z = 0, body along -z (screwed down through the lug from the loop's
    side): flat, so it doesn't dent the printed arm it stops on. A 1.5 mm hex socket in its top."""
    s = _cyl(1.5, 6.0, 0, 0, -6.0).faces(">Z").chamfer(0.3)
    return s.cut(cq.Workplane("XY").polygon(6, 1.5 / math.cos(math.pi / 6)).extrude(1.6).translate((0, 0, -6.05)))


def hall_magnet_v12() -> cq.Workplane:
    """K&J D42-N52 (1/4 x 1/8 in) along +y from y = 0: the hall switch's magnet, its face toward the switch at y = 0."""
    return P3.disc_magnet(MAGNET_D, MAGNET_H).rotate((0, 0, 0), (1, 0, 0), 90)


# ---------------------------------------------------------------- 2. EC v12
def ec_v12(sy_p16: float) -> cq.Workplane:
    """Electronics carriage v12 (printed PETG), Sam's frame at rest. v11's front half unchanged (the door ramp over the outlet, the spine,
    the solenoid's collar over clip 1, the straight rail); behind the pinion:
    - the -y bar ends in the front pivot boss (the front dowel pressed in); an outer -y rail runs from it, outside the cradle's tube, to
      a cross bar behind the motor that carries the back pivot boss;
    - the +y bar drops onto the arm through a bridge outside the cradle's lug; the arm (v11's, its inner edge 3 mm further out) carries
      the P16's clevis, the stop's landing and the first guide shoe;
    - a roof over the spring on two posts (the outer rail and the arm), with an up-stop pad over the top bar and the switch's magnet post;
    - the second guide shoe on the far (-y) side, on a bracket off the cross bar."""
    x0 = EC11_FRONT
    hw = EC11_HW
    zn, zf = EC11_SPINE_Z
    body = _box(x0, 71.5, -hw, hw, zf, zn)
    body = body.union(_box(69.5, 71.5, -19.5, 19.5, zf, zn))
    bx1 = EC12_BOSS_F[1]
    for s_ in (-1, 1):
        body = body.union(_box(69.5, bx1, *sorted((s_ * 15.5, s_ * 19.5)), zf, zn))
    body = body.union(P11.door_ramp_v11())
    sx = SOL11_X
    zs0 = SOL11_TIP - 8.0
    collar = _box(sx - 7.0 - 2.4, sx + 7.0 + 2.4, -8.5 - 2.4, 8.5 + 2.4, zs0 - 22.0, zs0 - 2.0)
    collar = collar.cut(_box(sx - 7.2, sx + 7.2, -8.7, 8.7, zs0 - 23.0, zs0 + 1.0))
    body = body.cut(_box(sx - 7.2, sx + 7.2, -8.7, 8.7, zs0 - 40.0, zs0 + 1.0)).union(collar)
    r0, r1 = RAIL11_X
    ry = RAIL11_FLAT + RAIL11_FUNNEL_L
    rail = _box(r0, r1, -ry, ry, zn - 0.01, RAIL11_BOTTOM).cut(P11.rail_cavity_v11())
    body = body.union(rail)
    # ---- the pivot's front boss on the -y bar, the outer -y rail, the cross bar behind the motor with the back boss
    f0, f1 = EC12_BOSS_F
    body = body.union(_box(f0, f1, PY - 3.5, -15.5, PZ - 3.5, PZ + 3.5))
    my0, my1, mzf, mzn = EC12_RAIL_M
    body = body.union(_box(f0, f1, my0, PY - 3.4, mzf, mzn))                                  # the boss out to the rail
    body = body.union(_box(f0, EC12_CROSS[1], my0, my1, mzf, mzn))                             # the outer rail
    cx0, cx1, cy0, cy1, czf, czn = EC12_CROSS
    body = body.union(_box(cx0, cx1, cy0, 27.5, czf, czn))                                     # the cross bar
    b0, b1 = EC12_BOSS_B
    body = body.union(_box(b0, cx0 + 0.01, PY - 3.5, PY + 3.5, PZ - 3.5, PZ + 3.5))            # the back boss, in front of the cross bar
    # ---- the arm (inner edge out to EC12_ARM_Y0), the P16's clevis, the bridge from the +y bar
    a0, a1, _, ay1, azn, azf = EC11_ARM
    ay0 = EC12_ARM_Y0
    body = body.union(_box(a0, a1, ay0, ay1, azf, azn))
    yk = 27.5                                                                                  # the first guide's seat block starts at Sam y 28.5
    body = body.union(_box(cx0, cx1, ay0, yk, czf, azn))                                      # the cross bar's +y end down to the arm's near face
    body = body.union(_box(a1 - 0.01, cx0 + 0.01, ay0, yk, azf, azn))                          # the arm carried back to the cross bar
    body = body.union(_box(f0, f1, 15.5, 31.0, zf, zn))                                        # the +y bar widened outside the lug
    body = body.union(_box(f0, a0 + 0.5, CRADLE12_LUG[3] + 0.5, 31.0, zf, -24.0))              # the bridge down to the arm, over the gears' tips
    px, pz = P16_11_PIN
    for s in (-1, 1):
        ya, yb = sorted((sy_p16 + s * 3.9, sy_p16 + s * 7.4))
        cheek = _box(px - 6.0, px + 6.0, ya, yb, azf + 0.01, pz).union(_cyl(6.0, yb - ya, px, ya, pz, axis="Y"))
        body = body.union(cheek)
    body = body.cut(cq.Workplane("XZ").center(px, pz).circle(2.05).extrude(30.0, both=True).translate((0, sy_p16, 0)))
    # 2026-11-27 (v12): v11's arm was solid between its clevis cheeks, so the P16's 6 mm rod-end tab had no slot to sit in (the actuator's
    # STEP stops short of the eye, and the check skipped the pin's nut and screw against the arm): a slot through the arm between the
    # cheeks round the pin (the tab swings 47-148 deg about the pin, always on the loop's side), and pockets for the nut and the head
    body = body.cut(_box(px - 6.5, px + 6.5, sy_p16 - 3.9, sy_p16 + 3.9, azf - 1.0, azn + 0.1))
    body = body.cut(_cyl(3.7, sy_p16 - 3.9 - 18.0 + 0.01, px, 18.0, pz, axis="Y"))
    body = body.cut(_cyl(3.9, ay1 + 1.0 - (sy_p16 + 7.4), px, sy_p16 + 7.4 - 0.01, pz, axis="Y"))
    # ---- the roof over the spring, on two posts; the up-stop pad; the switch's magnet post
    rx0, rx1, rzn, rzf = EC12_ROOF
    roof = _box(rx0, rx1, my0, 31.0, rzf, rzn)
    post_m = _box(rx0, rx1, my0, my1, rzf + 0.01, mzf + 0.01)
    post_p = _box(rx0, rx1, 27.0, 31.0, rzf + 0.01, azf + 0.01)
    body = body.union(roof).union(post_m).union(post_p)
    body = body.cut(_cyl(SPRING12_OD / 2 + 0.3, 2.0, SPRING12_X, 0.0, rzn - 2.0))            # the spring's pocket in the roof
    # up-stop: a pad under the roof over the top bar's +y half, CRADLE12_LIFT at the pinion before it touches (the bar rises 26.5/18.5 as much)
    tzf = CRADLE12_TOP[4]
    lift_y8 = 3.2 * (8.0 - PY) / (0.0 - PY)       # the pad as first drawn (for 3.2 mm at y 8); with the top bar widened to +-16 its corner
                                                 # meets the pad at 3.0 mm of lift at the pinion (CRADLE12_LIFT, measured by bisection)
    body = body.union(_box(rx1 - 6.0, rx1, 4.0, 9.0, rzn - 0.01, tzf - lift_y8 - 0.2))   # 2026-11-27: rzn + 0.01 left it 0.01 mm off the roof (a second solid)
    # the switch's magnet post: a block off the +y post, the magnet's 6.4 mm hole along y, its face MAGNET12_GAP off the lug's +y face
    hx, hy, hz = HALL12_XYZ
    mz = hz + MAGNET12_DZ
    my = CRADLE12_LUG[3] + MAGNET12_GAP
    mpost = _box(hx - 5.5, hx + 5.5, my, 31.0, mz - 6.0, mz + 4.5)
    mpost = mpost.union(_box(hx - 5.5, hx + 5.5, 27.0, 31.0, rzn, mz - 5.99))                 # up to the roof's +y post line
    body = body.union(mpost).cut(_cyl(MAGNET_D / 2 + 0.1, MAGNET_H + 0.2, hx, my - 0.01, mz, axis="Y").translate((0, 0, 0)))
    # ---- the first guide shoe (v11's) and the second, mirrored on the far side
    sx0, sx1, tip, top = SHOE11
    nd, nh = SHOE10_NOSE
    bxa, bxb, bz0, bz1 = SHOE11_BRACKET
    for sy_, root_y in ((SHOE11_Y, ay1), (SHOE12_Y2, my0)):
        bracket = _box(bxa, bxb, sy_ - 5.0, sy_ + 5.0, bz0, bz1)
        if sy_ > 0:
            riser = _box(bxa, a1, sy_ - 5.0, sy_ + 5.0, bz1 - 0.1, azf + 0.01)
        else:                                       # the far shoe's bracket off the outer rail and the cross bar
            riser = _box(bxa, min(bxb, cx1), sy_ + 4.9, my0 + 2.0, bz0, bz1)          # overlaps the outer rail's outer face
        shoe = _box(sx0, sx1, sy_ - 5.0, sy_ + 5.0, top, tip - nh)
        nose = cq.Workplane("XY").add(cq.Solid.makeCone(nd / 2, nd / 2 - nh, nh, cq.Vector((sx0 + sx1) / 2, sy_, tip - nh), cq.Vector(0, 0, 1)))
        body = body.union(bracket).union(riser).union(shoe).union(nose)
    # ---- the dowels' holes: 2.95 in the EC's bosses (pressed)
    body = body.cut(_cyl_x(1.475, f0 - 1.0, f1 + 0.01, PY, PZ)).cut(_cyl_x(1.475, b0 - 0.01, cx1 + 1.0, PY, PZ))
    return body.clean()


def ec12_shoe_tips() -> tuple:
    """Both guide shoes' nose tips, Sam's frame at rest: (first, second)."""
    sx0, sx1, tip, _ = SHOE11
    return ((sx0 + sx1) / 2, SHOE11_Y, tip), ((sx0 + sx1) / 2, SHOE12_Y2, tip)


# ---------------------------------------------------------------- 3. the second guide, on the second beam
def guide_hanger_v12(xc: float, yc: float, z_tip: float, plate_y: tuple, beam_y0: float, beam_z0: float) -> cq.Workplane:
    """v10's guide hanger for the far shoe, world: its seat block under the shoe (a 90 deg cone GUIDE10_SEAT_GAP under the nose's tip
    and v6's 45 deg funnel mouth), a 4 mm plate at plate_y up to the second beam's underside (inside the B+ shaft), and a flange under
    the beam with two M5 into T-nuts in its bottom slot. The beam is on the +y side here (v10's hanger is for a beam on the -y side)."""
    nd, nh = SHOE10_NOSE
    zs = z_tip - GUIDE10_SEAT_GAP
    ztop = zs + nh + 1.5
    pa, pb = plate_y
    blk = _box(xc - 11.0, xc + 11.0, yc - 7.5, pb, zs - 5.0, ztop)
    plate = _box(xc - 11.0, xc + 11.0, pa, pb, zs - 5.0, beam_z0)
    flange = _box(xc - 11.0, xc + 11.0, pa, beam_y0 + 20.0, beam_z0 - 4.0, beam_z0)
    g = blk.union(plate).union(flange)
    cone = cq.Workplane("XY").add(cq.Solid.makeCone(0.01, ztop - zs + 0.02, ztop - zs + 0.02, cq.Vector(xc, yc, zs), cq.Vector(0, 0, 1)))
    funnel = cq.Workplane("XY").add(cq.Solid.makeCone(nd / 2 + 1.0, nd / 2 + 1.0 + 4.0, 4.0, cq.Vector(xc, yc, ztop - 4.0 + 0.01), cq.Vector(0, 0, 1)))
    g = g.cut(cone).cut(funnel)
    for dx in (-6.0, 6.0):
        g = g.cut(_cyl(2.75, 6.0, xc + dx, beam_y0 + 10.0, beam_z0 - 5.0))
    return g


def nema11_v12() -> cq.Workplane:
    """The NEMA 11 (parts.nema11_envelope) with its 5 mm shaft cut to 15 mm, so it ends at the 24T pinion's front face instead of 4.8 mm
    past it, inside the EC's rail block (v11 skipped the EC-motor pair and hid it). Mounting face at z = 0, shaft +z."""
    env = PT.nema11_envelope()
    return env.cut(_cyl(3.0, 10.0, 0, 0, 15.0))


# ---------------------------------------------------------------- 5. the outlet door's shutter: a boss the rod can be pressed into
DOOR12_BOSS_R = 1.6                  # a round boss on the spring's axis (v4-v11: a 3.3 x 3 box that stood only 0.35 mm in front of the axis)
DOOR12_ROD_HOLE_R = 0.775            # 1.55 mm: a press fit for the 1/16 in (1.59 mm) 316 rod, through the boss's 2 mm
DOOR12_ROD_Z0 = -3.1                 # the rod's end, 0.1 mm short of the boss's far face (v11's rod stopped at -4.0, 1 mm into a boss it broke out of)


def door_shutter_v12() -> cq.Workplane:
    """v11's shutter (parts10.door_shutter_v10) with its spring boss made round, 3.2 mm across, on the spring's axis (x -2.85, y 0, z -5
    to -3, door shut), and a 1.55 mm hole through it for the door rod. v11's rectangular boss ran from x -3.2 to the shutter's back face,
    so a hole on the axis (x -2.85) left 0.35 mm in front: it broke out (README v11, "still open"). The round boss overlaps the shutter's
    front face (x -1.4) by 0.15 mm, stays clear of the housing's front lips (|y| > 3.5) and slides 6 mm toward the cap with the door."""
    s = P10.door_shutter_v10()
    xs = P3.DOOR_SPRING_X
    z0, z1 = -5.0, -3.0
    s = s.cut(_box(P3.DOOR_XF - 1.81, P3.DOOR_XF - 0.0, -1.51, 1.51, z0 - 0.01, z1 + 0.01))      # the old boss's part in front of the shutter
    boss = _cyl(DOOR12_BOSS_R, z1 - z0, xs, 0.0, z0)
    s = s.union(boss)
    return s.cut(_cyl(DOOR12_ROD_HOLE_R, z1 - z0 + 0.2, xs, 0.0, z0 - 0.1))


def door_rod_v12() -> cq.Workplane:
    """The door rod (v11's, 1/16 in 316) 0.9 mm longer, so it runs the boss's full 2 mm: 22.7 mm from the boss to the head's top."""
    z1 = DOOR11_HEAD_Z0 - DOOR11_HEAD[2]
    return _cyl(DOOR11_ROD_D / 2, DOOR12_ROD_Z0 - z1, P11.DOOR11_ROD_X, 0.0, z1)


DOOR12_BORE_R = 1.8                  # the tower's bore round the spring (3.0 OD) and the shutter's new boss (3.2), 0.2 mm clear of the boss


def door_housing_v12() -> cq.Workplane:
    """v11's door housing (parts10.door_housing_v10) with the spring's tower bored out: v4-v11 drew the tower in front of the shutter
    (x -4.6..-3.0, |y| < 4, from the cap down to z -3.5) solid, with the 3 mm spring and the rod's boss inside it (the check skipped
    the spring and the shutter against the housing). v12: a 3.6 mm bore on the spring's axis from the cap's underside (z -16.5) to the
    tower's end, open toward the shutter, and the tower's front carried 0.85 mm further forward so 0.8 mm of wall stays in front of it."""
    h = P10.door_housing_v10()
    xs = P3.DOOR_SPRING_X
    z_cap = -(DOOR_TOP - 3.0)
    h = h.union(_box(xs - DOOR12_BORE_R - 0.8, -4.0, -2.6, 2.6, -DOOR_TOP, -3.5))
    return h.cut(_cyl(DOOR12_BORE_R, -2.9 - z_cap, xs, 0.0, z_cap))
