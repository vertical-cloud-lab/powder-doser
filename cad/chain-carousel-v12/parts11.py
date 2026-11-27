"""v11 parts (Sam, PR #185, 2026-11-25). parts.py is v2's, parts3-10 v3-v10's, all unchanged; v11 is v10 with Sam's notes:

1. 90 deg: the carriages are 40 mm longer (params.CHAIN_L 345, HINGE_X 73), so the EC has room to swing forward past the front
   chain; the P16 is a P16-150 again, its base OUTSIDE the front side plate on p16_bracket_v11, through a slot in the plate
   ("punch a hole through the metal plate so the linear actuator has some more room").
2. The keyed rail no longer lifts: t_bracket_v11 rides straight through rail_cavity_v11, whose ends only flare (in x and z) to
   steer an arriving T to the right place. The hinge sits 5 mm nearer the carriage plate (params.HINGE_RAISE11), so the 44T gear
   reaches the pinion at rest; the pinion is 24T so the NEMA 11's body clears the passing plates.
3. The door: no cable. A stainless rod on each shutter runs up its spring's axis and out of the housing's cap to a printed head;
   the EC reaches forward over the outlet, and a ramp slot there catches the head and draws it 6 mm toward the loop.
4. The solenoid moves to the auger's first third: over clip 1, 32 mm behind the exit (v10: over clip 2, 156 mm).
5. The balance with its tall draft cage stands on the bench (balance_v11, v7's base and cage 4 mm taller, to the HR-100A's 315
   mm), a dosing lid set into its top frame, the beaker on a cylindrical pillar (pillar_v11).
6. The front acrylic panel gets an open doorway for the balance (no bay window, no weighing chamber); the wires aren't drawn.
Frames: Sam's studio frame for the module and the EC (the EC is fixed to the station module's Sam frame at max(0, tilt)); the
carriage frame (u, w, x); world for the beam, the brackets and the balance (origin under the pan's centre for the balance).
"""
from __future__ import annotations

import math

import cadquery as cq

from params import *  # noqa: F401,F403
import parts as PT
import parts3 as P3
import parts4 as P4
import parts7 as P7
import parts10 as P10
from parts3 import _box, _cyl
from parts6 import _cyl_x


# ---------------------------------------------------------------- 1. the keyed rail: straight, flared ends
def t_bracket_v11() -> cq.Workplane:
    """Printed T-bracket, Sam's frame: a foot on the plate's underside (two M3 x 6 into heat-set inserts), a 6 mm stem and a 16 x 16
    head 6 mm past the plate's underside. Its ends are chamfered so it finds the rail's flared mouth."""
    x0, x1, hy, t = T11_FOOT
    foot = _box(x0, x1, -hy, hy, -18.0 - t, -18.0).edges("|Z").fillet(2.0)
    s0, s1 = T11_STEM_X
    h0, h1 = T11_HEAD_X
    zu, zt = T11_HEAD_Z
    stem = _box(s0, s1, -T11_HY, T11_HY, zu - 0.01, -18.0 - t + 0.01)   # 2026-11-27: zu - 0.01 (was + 0.01: the head a separate solid)
    head = _box(h0, h1, -T11_HY, T11_HY, zt, zu).edges("|X").chamfer(0.8).edges("|Z").chamfer(1.5)
    b = foot.union(stem).union(head)
    for x in T11_SCREW_X:
        b = b.cut(_cyl(1.7, t + 0.2, x, 0.0, -18.0 - t - 0.1)).cut(_cyl(3.0, 1.0, x, 0.0, -18.0 - t - 0.1))
    return b


def _t_profile11(w: float) -> list[tuple[float, float]]:
    """The slot's cross-section (x, z) round the T, widened by w in x and opened by w in z both ways (the lips' top toward the plate,
    the ceiling toward the loop). w = 0 on the straight part: the lips sit RAIL11_LIP_GAP under the head's underside at rest."""
    c = RAIL11_CLEAR
    m0, m1 = T11_STEM_X[0] - c - w, T11_STEM_X[1] + c + w
    h0, h1 = T11_HEAD_X[0] - c - w, T11_HEAD_X[1] + c + w
    zl = T11_HEAD_Z[0] + RAIL11_LIP_GAP + w * RAIL11_FUNNEL_DOWN / RAIL11_FUNNEL   # the lips' top (toward the plate is +z)
    zc = T11_HEAD_Z[1] - 0.5 - w                                  # the ceiling
    zb = RAIL11_BOTTOM + 3.0                                      # open toward the plate
    return [(m0, zb), (m0, zl), (h0, zl), (h0, zc), (h1, zc), (h1, zl), (m1, zl), (m1, zb)]


def rail_cavity_v11() -> cq.Workplane:
    """The T-slot through the rail block (EC frame): straight over |y| <= RAIL11_FLAT, then each end flares RAIL11_FUNNEL over
    RAIL11_FUNNEL_L, the same amount up and down, so a T arriving off line is steered to the middle without the module being lifted."""
    fl, fn = RAIL11_FLAT, RAIL11_FUNNEL_L
    flat, mouth = _t_profile11(0.0), _t_profile11(RAIL11_FUNNEL)
    out = P10._loft_xz(flat, -fl, flat, fl)
    out = out.union(P10._loft_xz(flat, fl - 0.01, mouth, fl + fn + 0.01))
    out = out.union(P10._loft_xz(mouth, -(fl + fn + 0.01), flat, -(fl - 0.01)))
    return out


def rail_lip_top(s: float) -> float:
    """The lips' top (Sam z) at |y| = s: level over the straight part, opening toward the plate along each flared end."""
    fl, fn = RAIL11_FLAT, RAIL11_FUNNEL_L
    z = T11_HEAD_Z[0] + RAIL11_LIP_GAP
    return z if s <= fl else z + min(1.0, (s - fl) / fn) * RAIL11_FUNNEL_DOWN


def module_lift(offset: float) -> float:
    """v11: the rail never lifts a module."""
    return 0.0


# ---------------------------------------------------------------- 2. the outlet door, opened directly by the EC
DOOR11_ROD_X = P3.DOOR_SPRING_X                                   # the rod runs up the spring's axis (x -2.85, y 0)
DOOR11_ROD_Z0 = -4.0                                              # pressed into the shutter's boss (z -5..-3)


def door_rod_v11() -> cq.Workplane:
    """1.5 mm stainless rod, Sam's frame, door shut: from the shutter's boss up through the spring and the housing's cap (its 1.8 mm
    hole) to the head."""
    z1 = DOOR11_HEAD_Z0 - DOOR11_HEAD[2]
    return _cyl(DOOR11_ROD_D / 2, DOOR11_ROD_Z0 - z1, DOOR11_ROD_X, 0.0, z1)


def door_head_v11() -> cq.Workplane:
    """The printed head pressed on the rod's end, door shut: 6 x 6 x 2.5 mm, its underside DOOR11_HEAD_Z0."""
    hx, hy, hz = DOOR11_HEAD
    z0 = DOOR11_HEAD_Z0
    return _box(DOOR11_ROD_X - hx / 2, DOOR11_ROD_X + hx / 2, -hy / 2, hy / 2, z0 - hz, z0).edges("|Z").fillet(0.8).cut(
        _cyl(DOOR11_ROD_D / 2, hz + 1, DOOR11_ROD_X, 0.0, z0 - hz - 0.5))


def door_lip_face(s: float) -> float:
    """The door ramp's lips' face toward the loop (Sam z) at |y| = s: 0.5 under the shut head at the ends, 6.5 further at the flat,
    so the head (and the shutter) is drawn DOOR_TRAVEL toward the loop."""
    z_end = DOOR11_HEAD_Z0 + 0.5
    z_open = DOOR11_HEAD_Z0 - DOOR_TRAVEL
    fl, rp = DOOR11_RAMP_FLAT, DOOR11_RAMP
    if s <= fl:
        return z_open
    if s >= fl + rp:
        return z_end
    return z_open + (s - fl) / rp * (z_end - z_open)


def door_open_at(offset: float) -> float:
    """How far (mm) the door of a module `offset` mm from the station is open: its head (6 mm long) on the lips' highest point."""
    s = max(0.0, abs(offset) - DOOR11_HEAD[1] / 2)
    return max(0.0, min(DOOR_TRAVEL, DOOR11_HEAD_Z0 - door_lip_face(s)))


def door_ramp_v11() -> cq.Workplane:
    """The door ramp at the EC's front (EC frame): two wedge lips either side of the rod's slot, their faces following door_lip_face
    along y; a channel over them for the head, walls and a roof. At the ends the lips run 1.1 mm over the passing doors' caps."""
    fl, rp = DOOR11_RAMP_FLAT, DOOR11_RAMP
    L = fl + rp
    xr = DOOR11_ROD_X
    sl, lw = DOOR11_SLOT, DOOR11_LIP_W
    zb = DOOR11_HEAD_Z0 + 0.5 + DOOR11_LIP_T                      # the lips' underside at the ends: -20.6
    ys = [-L, -fl, fl, L]
    prof = [(ys[0], zb), (ys[0], door_lip_face(L)), (ys[1], door_lip_face(fl)), (ys[2], door_lip_face(fl)), (ys[3], door_lip_face(L)), (ys[3], zb)]
    body = None
    for x0, x1 in ((xr - sl / 2 - lw, xr - sl / 2), (xr + sl / 2, xr + sl / 2 + lw)):
        w = cq.Workplane("YZ").polyline(prof).close().extrude(x1 - x0).translate((x0, 0, 0))
        body = w if body is None else body.union(w)
    hx = DOOR11_HEAD[0]
    c0, c1 = xr - hx / 2 - 0.5, xr + hx / 2 + 0.5                 # the head's channel
    ceil = DOOR11_HEAD_Z0 - DOOR_TRAVEL - DOOR11_HEAD[2] - 1.2   # over the head when it's drawn open
    roof_top = EC11_SPINE_Z[1]
    walls = _box(EC11_FRONT, c0, -L, L, roof_top, zb).union(_box(c1, c1 + 2.0, -L, L, roof_top, zb))
    roof = _box(EC11_FRONT, c1 + 2.0, -L, L, roof_top, ceil)
    body = body.union(walls).union(roof)
    # tie the lips to the walls under the channel's ends (outside the head's path) only: the head runs between them
    return body


# ---------------------------------------------------------------- 3. EC v11
def p16_pin_sam_y(station_y: float) -> float:
    return station_y - P16_11_YW


def ec_v11(sy_p16: float) -> cq.Workplane:
    """Electronics carriage v11 (printed PETG), Sam's frame at rest (it turns with the station module once the P16 pulls). All of it
    inside the loop, 1 mm or more over the passing plates and carriages (both at z -18), reaching from over the outlet back past the
    motor:
    - the door ramp at the front (x -8.6..2.9), over the outlet: it draws each arriving door's rod 6 mm toward the loop;
    - the spine back to the motor plate, with a collar for the solenoid over clip 1 (x 32) and the rail block (x 45-75) under it;
    - the motor plate at x 89.9-93.5 and two cheeks beside the NEMA 11 (behind the gear, its shaft forward to the 24T pinion);
    - an arm out to the world -y side with the P16's rod-end clevis (pin at x 96) and the guide shoe."""
    x0 = EC11_FRONT
    hw = EC11_HW
    zn, zf = EC11_SPINE_Z
    # 2026-11-27: the spine used to run to the motor plate (x 93.5) and ended inside its 22.4 mm hole, so the front (ramp, collar, rail)
    # and the back (plate, cheeks, arm) never met, and on the way it ran through the 24T pinion (652 mm3) and the motor's shaft (found by
    # slicing in Bambu Studio; the check skipped those pairs). It now stops at x 71.5, widens there, and two 4 x 4.5 mm bars run beside
    # the pinion (2.5 mm off its tips) to the cheeks.
    body = _box(x0, 71.5, -hw, hw, zf, zn)
    body = body.union(_box(69.5, 71.5, -19.5, 19.5, zf, zn))
    for s_ in (-1, 1):
        body = body.union(_box(69.5, 89.91, *sorted((s_ * 15.5, s_ * 19.5)), zf, zn))
    body = body.union(door_ramp_v11())
    # solenoid collar over clip 1: the frame (14 along x, 17 across) from z SOL11_TIP - 8 to that - 29.7
    sx = SOL11_X
    zs0 = SOL11_TIP - 8.0
    collar = _box(sx - 7.0 - 2.4, sx + 7.0 + 2.4, -8.5 - 2.4, 8.5 + 2.4, zs0 - 22.0, zs0 - 2.0)
    collar = collar.cut(_box(sx - 7.2, sx + 7.2, -8.7, 8.7, zs0 - 23.0, zs0 + 1.0))
    body = body.cut(_box(sx - 7.2, sx + 7.2, -8.7, 8.7, zs0 - 40.0, zs0 + 1.0)).union(collar)
    # rail block
    r0, r1 = RAIL11_X
    ry = RAIL11_FLAT + RAIL11_FUNNEL_L
    rail = _box(r0, r1, -ry, ry, zn - 0.01, RAIL11_BOTTOM).cut(rail_cavity_v11())
    body = body.union(rail)
    # motor plate, cheeks, strap
    xm = NEMA11_11_X
    plate = _box(xm - 3.6, xm, -15.5, 15.5, -50.5, -20.5)
    plate = plate.cut(_cyl_x(11.2, xm - 4.0, xm + 1.0, 0.0, PINION11_Z))
    for dy in (-11.5, 11.5):
        for dz in (-11.5, 11.5):
            plate = plate.cut(_cyl_x(1.4, xm - 4.0, xm + 1.0, dy, PINION11_Z + dz))
    body = body.union(plate)
    c0, c1, cy0, cy1, czn, czf = EC11_CHEEK
    for s in (-1, 1):
        body = body.union(_box(xm - 3.6, c1, *sorted((s * cy0, s * cy1)), czf, czn))
    body = body.union(_box(xm + 2.0, xm + 42.0, -cy1, cy1, czf, PINION11_Z - 14.0 - 0.3))      # strap over the motor's far side
    # the arm, the P16's clevis, the guide shoe
    a0, a1, ay0, ay1, azn, azf = EC11_ARM
    body = body.union(_box(a0, a1, ay0, ay1, azf, azn))
    px, pz = P16_11_PIN
    for s in (-1, 1):
        ya, yb = sorted((sy_p16 + s * 3.9, sy_p16 + s * 7.4))
        cheek = _box(px - 6.0, px + 6.0, ya, yb, azf + 0.01, pz).union(_cyl(6.0, yb - ya, px, ya, pz, axis="Y"))
        body = body.union(cheek)
    body = body.cut(cq.Workplane("XZ").center(px, pz).circle(2.05).extrude(30.0, both=True).translate((0, sy_p16, 0)))
    sx0, sx1, tip, top = SHOE11
    nd, nh = SHOE10_NOSE
    sy = SHOE11_Y
    bx0, bx1, bz0, bz1 = SHOE11_BRACKET
    bracket = _box(bx0, bx1, sy - 5.0, sy + 5.0, bz0, bz1)
    riser = _box(bx0, a1, sy - 5.0, sy + 5.0, bz1 - 0.1, azf + 0.01)        # the bracket onto the arm's far face
    shoe = _box(sx0, sx1, sy - 5.0, sy + 5.0, top, tip - nh)
    # a true 90 deg cone (tip radius nd/2 - nh = 0.5; was 0.8, a 43 deg cone that sank 0.3 mm into the guide's 45 deg seat): with its tip
    # GUIDE10_SEAT_GAP (0.5) over the seat's apex its flanks are 0.35 mm clear of the seat's
    nose = cq.Workplane("XY").add(cq.Solid.makeCone(nd / 2, nd / 2 - nh, nh, cq.Vector((sx0 + sx1) / 2, sy, tip - nh), cq.Vector(0, 0, 1)))
    body = body.union(bracket).union(riser).union(shoe).union(nose)
    return body.clean()


def ec11_shoe_tip(sy_p16: float) -> tuple:
    """The guide shoe's nose tip, Sam's frame at rest (2026-11-27: at SHOE11_Y behind the arm; sy_p16 is no longer used)."""
    sx0, sx1, tip, _ = SHOE11
    return ((sx0 + sx1) / 2, SHOE11_Y, tip)


def pinion_24t() -> cq.Workplane:
    """24T module 1 steel spur gear (KHK SS1-24 class), 10 mm face, hub faced off: involute-ish envelope along +z from z = 0 (its
    front face), bore 5 mm H8 for the NEMA 11's shaft."""
    n, m = PINION11_T, 1.0
    rp, ra, rf = n * m / 2, n * m / 2 + m, n * m / 2 - 1.25 * m
    pts = []
    for i in range(n):
        a = 2 * math.pi * i / n
        for da, r in ((-0.30, rf), (-0.16, ra), (0.16, ra), (0.30, rf)):
            aa = a + da * 2 * math.pi / n * 1.6
            pts.append((r * math.cos(aa), r * math.sin(aa)))
    g = cq.Workplane("XY").polyline(pts).close().extrude(10.0)
    return g.cut(cq.Workplane("XY").circle(2.5).extrude(12.0).translate((0, 0, -1)))


# ---------------------------------------------------------------- 4. the P16-150's base clevis, on a bar across the front posts
def p16_bracket_v11(bx: float, by: float, bz: float, bar_x0: float, bar_x1: float, bar_z0: float) -> cq.Workplane:
    """Printed base clevis for the P16-150 (world): a flange under the front bar (x bar_x0..bar_x1, its underside at bar_z0; two M5 into
    T-nuts in the bar's bottom slot) and two cheeks CLEVIS_GAP apart round the P16's 8 mm rear tab, down to the pin (along y, at (bx, bz)),
    rounded R6 about it so the actuator swings between them."""
    t = (SHOULDER_CLEVIS_L - CLEVIS_GAP - 0.2) / 2
    fl = _box(bar_x0, bar_x1, by - 20.0, by + 20.0, bar_z0 - 5.0, bar_z0)
    out = fl
    for s in (-1, 1):
        ya, yb = sorted((by + s * CLEVIS_GAP / 2, by + s * (CLEVIS_GAP / 2 + t)))
        cheek = _box(bx - 6.0, bx + 6.0, ya, yb, bz, bar_z0 - 4.99).union(_cyl(6.0, yb - ya, bx, ya, bz, axis="Y"))
        out = out.union(cheek)
    out = out.cut(cq.Workplane("XZ").center(bx, bz).circle(ACT_CLEVIS_D / 2 - 0.05).extrude(30.0, both=True).translate((0, by, 0)))
    xc = (bar_x0 + bar_x1) / 2
    for dy in (-14.0, 14.0):
        out = out.cut(_cyl(2.75, 7.0, xc, by + dy, bar_z0 - 6.0))
    return out


# ---------------------------------------------------------------- 5. carriage v11: v10's, its opening longer at the front
def carriage_v11(print_web: bool = False) -> cq.Workplane:
    """carriage_v10 (ribs on the outer face) with its opening run forward to HINGE_X - 40: at 90 deg the EC's spine passes the
    carriage's plane 19-37 mm in front of the hinge ("the holes in the plate can be bigger")."""
    c = P10.carriage_v10(print_web)
    w0, w1 = CAR_W0 - CAR_T, CAR_W0
    return c.cut(_box(-OPEN_U, OPEN_U, w0 - 1.0, w1 + 1.0, HINGE_X - 40.0, HINGE_X - 18.0))   # 40: at 38 the EC passed its edge by 0.5 mm at 90 deg


# ---------------------------------------------------------------- 6. mounting plate v11: v10's additions, no motor relief
def plate_additions_v11() -> tuple[cq.Workplane, cq.Workplane]:
    """(added, cut) for mounting plate v11, Sam's frame, on his Oct 13 plate: v6/v7's extension to the cap (slab, clip 2, cap saddle,
    keeper), the T-bracket's two M3 inserts. No motor relief (the 24T pinion keeps the NEMA 11 2.25 mm off the plate)."""
    add, cut = P10.plate_additions_v10()
    m0, m1, mh, md = MOTOR10_RELIEF
    relief = _box(m0, m1, -mh, mh, -18.1, -18.0 + md)
    cut = cut.cut(relief)
    for x in T11_SCREW_X:
        cut = cut.union(_cyl(2.0, 5.0, x, 0.0, -18.1))
    # 2026-11-27: the channel wall beside the door housing's arms cut back to |y| 16.3 along the arms (x 4.8-22, z -13 to -8; the wall is
    # 10 mm thick there, |y| 15-25, so 8.7 mm stays), so the arms can run to |y| 16.25 round their M2 screws (parts4.door_housing_v4)
    for sy in (-1, 1):
        cut = cut.union(_box(4.8, 22.01, *sorted((sy * 14.9, sy * 16.3)), -13.01, -7.99))
    return add, cut


# ---------------------------------------------------------------- 7. the balance with its tall draft cage, and the pillar
def balance_v11() -> dict[str, cq.Workplane]:
    """v7's balance (a base and a draft cage, nothing behind the cage) with the chamber BAL11_CAGE_H tall over the pan, so the cage's top
    frame is at BAL11_TOP (315, the HR-100A's height); the top door is out and a dosing lid sits in the top frame's opening, flush
    with its top, with a LID11_HOLE hole on the pan's axis. Frame: origin on the bench under the pan's centre (parts5.hr202i's)."""
    W = HR2_W
    g, fr = BAL7_GLASS, BAL7_FRAME
    cw, cd, _ = HR2_CH
    chh = BAL11_CAGE_H
    hw = cw / 2
    cx0 = -86.5
    cx1 = cx0 + cd
    zf = HR2_FLOOR
    ztop = HR2_PAN_TOP + chh
    xb = BAL7_BACK_X
    xs = cx0 - g - fr
    x0 = xs - 73.0
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
    out["bal11_base"] = base.union(_cyl(HR2_PAN_D / 2 + 7, 4.0, 0, 0, zf).cut(_cyl(HR2_PAN_D / 2 + 3, 6.0, 0, 0, zf - 1)))
    out["bal11_frame"] = frame.union(ring).union(sills)
    out["bal11_display"] = (cq.Workplane(cq.Plane(origin=((x0 + 6 + xs) / 2, 0.0, (n0 + 4 + n1 + 4) / 2 + 0.4), xDir=(0, 1, 0),
                                                  normal=(-math.sin(math.atan2(n1 - n0, xs - x0 - 6)), 0, math.cos(math.atan2(n1 - n0, xs - x0 - 6)))))
                            .rect(110.0, 30.0).extrude(0.8))
    out["bal11_glass"] = _box(cx0 - g, cx0, -hw, hw, zf + 6, ztop).union(_box(cx1, cx1 + g, -hw, hw, zf + 6, ztop))
    out["bal11_pan"] = _cyl(HR2_PAN_D / 2, 2.0, 0.0, 0.0, HR2_PAN_TOP - 2.0).union(_cyl(7.0, HR2_PAN_TOP - 2.0 - zf + 0.5, 0.0, 0.0, zf - 0.5))
    zt = ztop + g + fr
    out["bal11_lid"] = _box(cx0 + 2.2, cx1 - 2.2, -hw + 2.2, hw - 2.2, zt - LID11_T, zt).cut(_cyl(LID11_HOLE / 2, LID11_T + 2, 0, 0, zt - LID11_T - 1))
    dh = ztop - zf - 6.0 - 3.0
    for name, sy in (("bal11_door_left", -1), ("bal11_door_right", 1)):
        yy = sy * (hw + fr / 2)
        pane = _box(cx0, cx0 + cd, yy - g / 2, yy + g / 2, zf + 6, zf + 6 + dh)
        ga, gb = sorted((yy + sy * g / 2, yy + sy * (g / 2 + 7)))
        grip = _box(cx0 + 4, cx0 + 16, ga, gb, zf + 60, zf + 200)
        out[name] = pane.union(grip)
    return out


BEAKER11_RIM = BAL11_TOP - LID11_T - BEAKER11_UNDER_LID           # 309 above the balance's feet
PILLAR11_TOP = BEAKER11_RIM - BEAKER_H                            # the beaker's floor on the pillar's socket


def pillar_v11() -> cq.Workplane:
    """The beaker's pillar on the pan (printed PETG, vase-mode walls): a 60 mm foot on the pan, a 40 mm tube, and a socket 2 mm deep for
    the 25 mL beaker on top. Frame: the pan's axis, z from the bench (balance frame)."""
    od, wall = PILLAR11
    z0, z1 = HR2_PAN_TOP, PILLAR11_TOP
    foot = _cyl(30.0, 2.0, 0, 0, z0).cut(_cyl(od / 2 - wall, 3.0, 0, 0, z0 - 0.5))
    tube = _cyl(od / 2, z1 - z0, 0, 0, z0).cut(_cyl(od / 2 - wall, z1 - z0 + 2, 0, 0, z0 - 1))
    cap = _cyl(BEAKER_D / 2 + 2.0, 4.0, 0, 0, z1 - 2.0).cut(_cyl(BEAKER_D / 2 + 0.3, 3.0, 0, 0, z1))
    deck = _cyl(od / 2, 2.0, 0, 0, z1 - 2.0)
    return foot.union(tube).union(cap).union(deck)


# ---------------------------------------------------------------- 8. the latch cam, its foot beside the back hold-down
def latch_rail_v11(wall_x: float) -> cq.Workplane:
    """v10's latch cam (parts6.latch_rail_v6 with the +-18 mm flat and 30 deg ramps) with its web and foot cut back to Sam y >=
    LATCH11_FOOT_Y over the last 26 mm to the back plate, where the back hold-down stands (Sam y -20..20); the foot's two M5 move to
    LATCH_Y6 + LATCH11_FOOT_DY. Sam's frame at the station."""
    import parts6 as P6
    r = P6.latch_rail_v6(wall_x)
    r = r.cut(_box(wall_x - 27.0, wall_x + 1.0, -80.0, LATCH11_FOOT_Y, -20.0, 60.0))
    r = r.union(_box(wall_x - 6.0, wall_x, LATCH11_FOOT_Y, LATCH_Y6 + 28.0, P6.LATCH6_FOLLOW_TIP + 0.5 if hasattr(P6, "LATCH6_FOLLOW_TIP") else 10.5,
                     P6.LATCH6_FOOT_Z1))
    for dy in LATCH11_FOOT_DY:
        r = r.cut(_cyl_x(2.75, wall_x - 7.0, wall_x + 1.0, LATCH_Y6 + dy, P6.LATCH6_FOOT_HOLE_Z))
    return r
