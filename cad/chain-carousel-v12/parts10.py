"""v10 parts (Sam, PR #185, 2026-11-19). parts.py is v2's, parts3-9 v3-v9's, all unchanged; v10 is a variation on v9 (and v7).

Sam's note, and the part each piece became:
1. "instead of a linear actuator on the bottom pushing the augers up, what if it was inside, defaulting to fully extending, and then
   pulling it up to dose?" -> ec_v10: a new electronics carriage (EC) inside the loop, on the plate's side of the module, so nothing
   of the station is under the auger. One Actuonix P16-100 inside the loop beside the module (p16_100, its base on
   p16_bracket_v10 on the front side plate) is fully extended between doses and retracts to pull the EC and the module up about the
   hinge.
2. "None of the wires can cross the carousel boundary, so they would have to come out the front ... some cuts in the front metal
   panel" -> the EC's and the P16's leads run along the arm and the P16 to a grommet in the front side plate (layout.cable_paths_v10).
3. "a keyed rail ... each mounting plate would have some kind of T or L bracket that would slot into the electronics carriage every
   time an auger passed the dosing station. Give the entrance and exit a ramp" -> t_bracket_v10 on every plate; rail_cavity_v10 is the
   T-slot along the travel under the EC, flared at both ends. Its lips' ramps lift each arriving module TAU0 about its hinge, which
   brings its 44T gear up into mesh with the pinion; no magnets, no kinematic coupling.
4. "give the electronics carriage some guides so it's not flopping around in between augers" -> the EC rests on its guide shoe in a
   funnel seat (guide_hanger_v10, on a 2020 beam inside the loop) and hangs from the P16's pin: between modules it can't swing.
5. "if you see any other places that would need support, adjust for them" -> the outlet door is opened by a ramp on the EC (the
   pull wire and tab, door_shutter_v10); the carriage's stiffening ribs move to its outer face (carriage_v10), so the EC and its
   pinion clear the passing carriages; the latch cam's flat is longer (params.LATCH_RAIL_FLAT); a stepped deck and a dose hole.
Frames: Sam's studio frame for the module and for the EC (the EC is drawn at the coupled pose: it is fixed to the station module's
Sam frame tilted TAU0 and more); the carriage frame (u, w, x); world for the beam, the bracket and the chamber.
"""
from __future__ import annotations

import math

import cadquery as cq

from params import *  # noqa: F401,F403
import parts as PT
import parts3 as P3
import parts4 as P4
import parts6 as P6
import parts7 as P7
from parts3 import _box, _cyl
from parts6 import _cyl_x


def _arrive(x: float, z: float, tau: float = 0.0) -> tuple[float, float]:
    """A point of a module at tilt tau (Sam x, z) in the EC's frame (the station module's Sam frame at TAU0)."""
    d = math.radians(tau - TAU0)
    return x * math.cos(d) + z * math.sin(d), -x * math.sin(d) + z * math.cos(d)


# ---------------------------------------------------------------- 1. the keyed rail: the T-bracket and the slot
def t_bracket_v10() -> cq.Workplane:
    """Printed T-bracket, Sam's frame: a foot on the plate's underside (two M3 x 6 into heat-set inserts, beyond the head's wings so a
    hex key reaches them), a 6 mm stem through
    the carriage's opening, and a 16 x 16 head 10 mm past the plate's underside. Its ends are chamfered so it finds the rail."""
    x0, x1, hy, t = T10_FOOT
    foot = _box(x0, x1, -hy, hy, -18.0 - t, -18.0).edges("|Z").fillet(2.0)
    s0, s1 = T10_STEM_X
    h0, h1 = T10_HEAD_X
    zu, zt = T10_HEAD_Z
    stem = _box(s0, s1, -T10_HY, T10_HY, zu, -18.0 - t + 0.01)
    head = _box(h0, h1, -T10_HY, T10_HY, zt, zu).edges("|X").chamfer(1.0).edges("|Z").chamfer(1.5)
    b = foot.union(stem).union(head)
    for x in T10_SCREW_X:
        b = b.cut(_cyl(1.7, t + 0.2, x, 0.0, -18.0 - t - 0.1)).cut(_cyl(3.0, 1.0, x, 0.0, -18.0 - t - 0.1))
    return b


def _t_profile(dx: float, dz: float, widen: float, rise: float) -> list[tuple[float, float]]:
    """The slot's cross-section (x, z) round the T at an offset (dx, dz), widened by `widen` in x and `rise` toward the loop."""
    c = RAIL10_CLEAR
    m0, m1 = T10_STEM_X[0] - c - widen + dx, T10_STEM_X[1] + c + widen + dx
    h0, h1 = T10_HEAD_X[0] - c - widen + dx, T10_HEAD_X[1] + c + widen + dx
    zl = T10_HEAD_Z[0] + dz                                   # the lips' top: the T's underside (contact when coupled)
    zc = T10_HEAD_Z[1] - 0.5 - rise + dz                      # the ceiling
    zb = RAIL10_BOTTOM + 3.0                                  # open toward the plate
    return [(m0, zb), (m0, zl), (h0, zl), (h0, zc), (h1, zc), (h1, zl), (m1, zl), (m1, zb)]


def _loft_xz(p0: list, y0: float, p1: list, y1: float) -> cq.Workplane:
    """A solid lofted between two (x, z) polygons in the planes y = y0 and y = y1."""
    w0 = cq.Wire.makePolygon([cq.Vector(x, y0, z) for x, z in p0], close=True)
    w1 = cq.Wire.makePolygon([cq.Vector(x, y1, z) for x, z in p1], close=True)
    return cq.Workplane("XY").add(cq.Solid.makeLoft([w0, w1], True))


ARRIVE_T = _arrive((T10_HEAD_X[0] + T10_HEAD_X[1]) / 2, T10_HEAD_Z[0])     # the arriving T's underside, EC frame
T_DX = ARRIVE_T[0] - (T10_HEAD_X[0] + T10_HEAD_X[1]) / 2                   # +1.9: it arrives further back ...
T_DZ = ARRIVE_T[1] - T10_HEAD_Z[0]                                         # +4.26: ... and nearer the plate


def rail_cavity_v10() -> cq.Workplane:
    """The T-slot cut through the rail block, EC frame: straight over the lips' flat (|y| <= RAIL10_FLAT), then lofted to each end
    (|y| = RAIL10_FLAT + RAIL10_RAMP), where it is shifted to where an arriving T is (T_DX back, T_DZ + 0.5 nearer the plate) and
    flared RAIL10_FUNNEL. The lips' tops are the ramps that lift the T (and the module) as it slides in."""
    fl, rp = RAIL10_FLAT, RAIL10_RAMP
    flat = _t_profile(0.0, 0.0, 0.0, 0.0)
    ent = _t_profile(T_DX, T_DZ + 0.5, RAIL10_FUNNEL, RAIL10_FUNNEL)
    mid = _loft_xz(flat, -fl, flat, fl)
    out = mid
    for s in (-1, 1):
        y0, y1 = s * fl, s * (fl + rp + 0.01)
        out = out.union(_loft_xz(flat, y0, ent, y1) if s > 0 else _loft_xz(ent, y1, flat, y0))
    return out


def lip_top(s: float) -> float:
    """The lips' top (EC frame, Sam z) at |y| = s along the rail: -28 on the flat, rising toward the plate along the ramps."""
    fl, rp = RAIL10_FLAT, RAIL10_RAMP
    z_flat, z_end = T10_HEAD_Z[0], T10_HEAD_Z[0] + T_DZ + 0.5
    if s <= fl:
        return z_flat
    if s >= fl + rp:
        return z_end
    return z_flat + (s - fl) / rp * (z_end - z_flat)


def module_lift(offset: float) -> float:
    """The tilt (deg, about the hinge) the rail gives a module whose centre is `offset` mm along the run from the station: the T
    (16 mm long) rests on the highest point of the lips under it."""
    s = max(0.0, abs(offset) - T10_HY)
    if s >= RAIL10_FLAT + RAIL10_RAMP:
        return 0.0
    z = lip_top(s)                                            # the T's underside there (EC frame)
    # the T's underside centre sits at z: find the tilt that puts it there (it moves T_DZ over TAU0, near enough linearly)
    frac = (T10_HEAD_Z[0] + T_DZ - z) / T_DZ
    return max(0.0, min(1.0, frac)) * TAU0


# ---------------------------------------------------------------- 2. the outlet door: pulled open by a ramp on the EC
def door_housing_v10() -> cq.Workplane:
    """v4's door housing without its push-strip bush under the exit (z > 5 cut off), and a 1.8 mm hole through its cap for the pull
    wire on the spring's axis."""
    h = P4.door_housing_v4().cut(_box(-10.0, 25.0, -20.0, 20.0, 5.0, 30.0))
    return h.cut(_cyl(0.9, 6.0, P3.DOOR_SPRING_X, 0.0, -DOOR_TOP - 1.0))


def door_cable_points() -> list[tuple[float, float, float]]:
    """The door cable's centreline, Sam frame: from the shutter's boss up through the spring and the housing's cap, round a bend in the
    guide just over the cap, back along the plate's underside (inside the carriage's opening) to a second bend under the tab, and up
    to the tab. It slides in a PTFE sleeve; the path itself never moves, only the tab does (6 mm toward the loop to open)."""
    xs = P3.DOOR_SPRING_X
    zc = -DOOR_TOP - 1.2                                      # just over the cap
    xb = (DOOR10_TAB_X[0] + DOOR10_TAB_X[1]) / 2              # under the tab
    return [(xs, 0.0, -4.0), (xs, 0.0, zc), (xs + 2.0, 0.0, zc - 0.6), (xb - 2.0, 0.0, zc - 0.6), (xb, 0.0, zc - 2.0), (xb, 0.0, DOOR10_TAB_Z[0])]


def _polyline_tube(pts, r: float) -> cq.Workplane:
    out = None
    for a, b in zip(pts[:-1], pts[1:]):
        L = math.dist(a, b)
        if L < 0.05:
            continue
        d = cq.Vector(*[(bb - aa) / L for aa, bb in zip(a, b)])
        seg = cq.Workplane("XY").add(cq.Solid.makeCylinder(r, L, cq.Vector(*a), d)).union(cq.Workplane("XY").add(cq.Solid.makeSphere(r, cq.Vector(*b))))
        out = seg if out is None else out.union(seg)
    return out


def door_shutter_v10() -> cq.Workplane:
    """v4's shutter with its push strip cut off: nothing of the door hangs under the exit any more. The cable is crimped into its boss."""
    return P4.door_shutter_v4().cut(_box(-10.0, 10.0, -20.0, 20.0, 6.5, 30.0))


def door_guide_v10() -> cq.Workplane:
    """The door cable's guide (printed), Sam frame, fixed to the module: a 3 mm strip clipped over the housing's cap that runs back
    along the plate's underside (x 15 on, two M2 into the plate) to a boss under the tab, with the cable in its PTFE sleeve (drawn
    with it: 0.6 mm stainless wire rope in a 1.6 mm OD sleeve). It sits 3.5 mm into the carriage's opening, 22 mm or less from the
    hinge axis in front of the plate, so the module still tilts past 60 deg."""
    xs = P3.DOOR_SPRING_X
    x1 = (DOOR10_TAB_X[0] + DOOR10_TAB_X[1]) / 2
    zc = -DOOR_TOP
    strip = _box(xs - 2.0, x1 + 1.5, -2.5, 2.5, zc - 2.5, zc).union(_box(15.0, x1 + 1.5, -2.5, 2.5, -21.5, -18.0))
    boss = _box(x1 - 1.5, x1 + 1.5, -2.5, 2.5, -22.0, -18.0)            # between the door ramp's two rails (their underside at -23)
    g = strip.union(boss)
    g = g.cut(_polyline_tube(door_cable_points()[1:], 0.85))
    sleeve = _polyline_tube(door_cable_points()[1:-1], 0.8)
    return g.union(sleeve)


def door_tab_v10() -> cq.Workplane:
    """The printed tab crimped on the cable's end, Sam frame, door shut; it moves 6 mm toward the loop (-z) to open the door. A 6 mm
    stub of the cable runs down from it into the guide's boss."""
    x0, x1 = DOOR10_TAB_X
    z0, z1 = DOOR10_TAB_Z
    tab = _box(x0, x1, -DOOR10_TAB_HY, DOOR10_TAB_HY, z1, z0).edges("|Y").chamfer(0.8)
    xb = (x0 + x1) / 2
    return tab.union(_cyl(0.3, 6.0, xb, 0.0, z0 - 0.01))


def door_ramp_profile(s: float) -> float:
    """The door ramp's top (EC frame, Sam z) at |y| = s: it holds the tab DOOR_TRAVEL toward the loop on the flat."""
    ax, az = _arrive((DOOR10_TAB_X[0] + DOOR10_TAB_X[1]) / 2, DOOR10_TAB_Z[0])
    z_open = DOOR10_TAB_Z[0] - DOOR_TRAVEL
    z_end = az + 0.5
    fl, rp = DOOR10_RAMP_FLAT, DOOR10_RAMP
    if s <= fl:
        return z_open
    if s >= fl + rp:
        return z_end
    return z_open + (s - fl) / rp * (z_end - z_open)


def door_open_at(offset: float) -> float:
    """How far (mm) the door of a module `offset` mm from the station is open: the tab (5 mm wide) on the ramp's highest point."""
    s = max(0.0, abs(offset) - DOOR10_TAB_HY)
    z = door_ramp_profile(s)
    _, az = _arrive((DOOR10_TAB_X[0] + DOOR10_TAB_X[1]) / 2, DOOR10_TAB_Z[0], module_lift(offset))
    return max(0.0, min(DOOR_TRAVEL, az - z))


# ---------------------------------------------------------------- 3. EC v10
def p16_pin_sam_y(station_y: float) -> float:
    """Sam y of the P16's plane at the station (his y is the world's -y there)."""
    return station_y - P16_10_YW


def ec_v10(sy_p16: float) -> cq.Workplane:
    """The electronics carriage v10 (printed PETG), Sam's frame at the coupled pose (its frame is the station module's, tilted TAU0
    or more). All of it is on the plate's side, inside the loop, 1 mm or more over the passing carriages' inner faces:
    - a spine over the door ramp and the rail;
    - the door ramp (x 14-23) that lifts each door's tab 6 mm as the module slides in;
    - the rail block (x 45-75) with the T-slot along the travel and its ramps;
    - the motor plate at x 89.4-93 and two cheeks beside the NEMA 11 (behind the gear, its shaft forward to the 20T pinion under
      the 44T gear), a strap over it, and the solenoid's holder over clip 2;
    - an arm out to the world -y side with the P16's rod-end clevis and the guide shoe (its 90 deg conical nose toward the plate).
    sy_p16 is the P16's plane in Sam y."""
    x0, x1, hw, zn, zf = EC10_SPINE
    body = _box(x0, x1, -hw, hw, zf, zn)
    # door ramp: a wedge under the tabs' path, joined to the spine by a back wall (the wires come in from the front)
    fl, rp = DOOR10_RAMP_FLAT, DOOR10_RAMP
    ys = [-(fl + rp), -fl, fl, fl + rp]
    prof = [(ys[0], -23.0), (ys[0], door_ramp_profile(fl + rp)), (ys[1], door_ramp_profile(fl)), (ys[2], door_ramp_profile(fl)),
            (ys[3], door_ramp_profile(fl + rp)), (ys[3], -23.0)]
    for dx0, dx1 in DOOR10_RAMP_X:                               # two rails, the tab's cable between them
        body = body.union(cq.Workplane("YZ").polyline(prof).close().extrude(dx1 - dx0).translate((dx0, 0, 0)))
    (f0, _), (_, b1) = DOOR10_RAMP_X
    for wx0, wx1 in ((f0 - 2.0, f0 + 0.01), (b1 + 1.5, b1 + 3.0)):    # webs up to the spine, outside the tabs' path
        body = body.union(_box(wx0, wx1, -(fl + rp), fl + rp, zn - 0.01, -23.0))
    body = body.union(_box(b1 - 0.01, b1 + 1.51, -(fl + rp), fl + rp, -24.5, -23.0))
    # rail block
    r0, r1 = RAIL10_X
    ry = RAIL10_FLAT + RAIL10_RAMP
    rail = _box(r0, r1, -ry, ry, zn - 0.01, RAIL10_BOTTOM).cut(rail_cavity_v10())
    body = body.union(rail)
    # motor plate, cheeks, strap
    xm = NEMA11_10_X
    plate = _box(xm - 3.6, xm, -15.0, 15.0, -50.0, -18.8)
    plate = plate.cut(_cyl_x(11.2, xm - 4.0, xm + 1.0, 0.0, PINION10_Z))
    for dy in (-11.5, 11.5):
        for dz in (-11.5, 11.5):
            plate = plate.cut(_cyl_x(1.4, xm - 4.0, xm + 1.0, dy, PINION10_Z + dz))
    c0, c1, cy0, cy1, czn, czf = EC10_CHEEK
    body = body.union(plate)
    for s in (-1, 1):
        body = body.union(_box(xm - 3.6, c1, *sorted((s * cy0, s * cy1)), czf, czn))
    body = body.union(_box(xm + 2.0, xm + 42.0, -cy1, cy1, czf, PINION10_Z - 14.0 - 0.3))          # strap over the motor's far side
    body = body.union(_box(SOL10_X - 10.0, SOL10_X + 10.0, -cy1, cy1, czf - 4.0, czf + 0.01))       # solenoid holder plate
    # the arm, the P16's clevis, the guide shoe
    a0, a1, ay0, ay1, azn, azf = EC10_ARM
    arm = _box(a0, a1, ay0, ay1, azf, azn)
    body = body.union(arm)
    px, pz = P16_10_PIN
    for s in (-1, 1):
        ya, yb = sorted((sy_p16 + s * 3.9, sy_p16 + s * 6.9))
        cheek = _box(px - 6.0, px + 6.0, ya, yb, azn - 0.01, pz).union(_cyl(6.0, yb - ya, px, ya, pz, axis="Y"))
        body = body.union(cheek)
    body = body.cut(cq.Workplane("XZ").center(px, pz).circle(2.05).extrude(30.0, both=True).translate((0, sy_p16, 0)))
    sx0, sx1, tip, top = SHOE10
    nd, nh = SHOE10_NOSE
    shoe = _box(sx0, sx1, sy_p16 - 5.0, sy_p16 + 5.0, top, tip - nh)
    nose = cq.Workplane("XY").add(cq.Solid.makeCone(nd / 2, 0.8, nh, cq.Vector((sx0 + sx1) / 2, sy_p16, tip - nh), cq.Vector(0, 0, 1)))
    body = body.union(shoe).union(nose)
    # cable clips: two slots under the arm for the bundle
    return body.clean()


def ec10_shoe_tip(sy_p16: float) -> tuple:
    sx0, sx1, tip, _ = SHOE10
    return ((sx0 + sx1) / 2, sy_p16, tip)


# ---------------------------------------------------------------- 4. the P16-100, its bracket, the beam's hanger and seat
def p16_100() -> tuple[cq.Workplane, cq.Workplane]:
    """Actuonix P16-100-22-12-P: the -150's envelope (parts.actuator_p16's stand-in) with 50 mm less tube and rod. Rear clevis hole on
    the y axis at the origin, rod along +z. (body, rod at full retraction)."""
    ret = P16_10_RETRACTED
    housing = cq.Workplane("XY").box(36.0, 20.0, 70.0, centered=False).translate((-25.5, -10.0, 4.5))
    tab = (cq.Workplane("XZ").circle(5.0).extrude(4.0, both=True).union(cq.Workplane("XY").box(10.0, 8.0, 4.6, centered=(True, True, False))))
    tube = cq.Workplane("XY").box(12.0, 12.0, ret - 5.0 - 23.4, centered=False).translate((-6.0, -6.0, 23.4))
    body = housing.union(tab).union(tube).cut(cq.Workplane("XZ").circle(ACT_CLEVIS_D / 2).extrude(20, both=True))
    rl = P16_10_STROKE + 15.0
    rod = cq.Workplane("XY").circle(4.47).extrude(rl).translate((0, 0, ret - 4.0 - rl))
    end = (cq.Workplane("XY").box(9.0, 6.0, 4.0, centered=(True, True, False)).translate((0, 0, ret - 4.0))
           .union(cq.Workplane("XZ").center(0, ret).circle(4.5).extrude(3.0, both=True)))
    end = end.intersect(cq.Workplane("XY").box(20, 20, 8.0, centered=(True, True, False)).translate((0, 0, ret - 4.0)))
    rod = rod.union(end).cut(cq.Workplane("XZ").center(0, ret).circle(ACT_CLEVIS_D / 2).extrude(10, both=True))
    return body, rod


def p16_bracket_v10(bx: float, by: float, bz: float, wall_x: float) -> cq.Workplane:
    """Printed base clevis for the P16-100 on the front side plate's inner face (world): a foot on the plate (x wall_x .. +6, two M5
    through the plate into heat-set inserts), two cheeks CLEVIS_GAP apart round the P16's 8 mm rear tab, rounded R6 about the pin
    (along y, at (bx, bz)) so the housing swings over them."""
    t = (SHOULDER_CLEVIS_L - CLEVIS_GAP - 0.2) / 2
    foot = _box(wall_x, wall_x + 6.0, by - 16.0, by + 16.0, bz - 18.0, bz + 10.0)
    out = foot
    for s in (-1, 1):
        ya, yb = sorted((by + s * CLEVIS_GAP / 2, by + s * (CLEVIS_GAP / 2 + t)))
        cheek = _box(wall_x + 5.99, bx, ya, yb, bz - 6.0, bz + 6.0).union(_cyl(6.0, yb - ya, bx, ya, bz, axis="Y"))
        out = out.union(cheek)
    out = out.cut(cq.Workplane("XZ").center(bx, bz).circle(ACT_CLEVIS_D / 2 - 0.05).extrude(30.0, both=True).translate((0, by, 0)))
    for dy in (-11.0, 11.0):
        out = out.cut(_cyl_x(3.2, wall_x - 1.0, wall_x + 7.0, by + dy, bz - 9.0))          # M5 heat-set inserts (6.4 mm holes)
    return out


def guide_hanger_v10(xc: float, yc: float, z_tip: float, beam_y0: float, beam_z0: float) -> cq.Workplane:
    """Printed guide for the EC's shoe, world: a flange under the beam (two M5 into T-nuts in its bottom slot), a 4 mm plate down
    beside the beam's inner face, and a seat block under the shoe with a 90 deg cone for its nose (GUIDE10_SEAT_GAP under the tip)
    and v6's 45 deg funnel mouth round it, so a shoe coming down off line is steered in."""
    nd, nh = SHOE10_NOSE
    zs = z_tip - GUIDE10_SEAT_GAP                          # the cone's apex level (the nose tip parks 0.5 over it)
    ztop = zs + nh + 1.5
    blk = _box(xc - 11.0, xc + 11.0, beam_y0, yc + 7.5, zs - 5.0, ztop)
    plate = _box(xc - 11.0, xc + 11.0, beam_y0, beam_y0 + 4.0, zs - 5.0, beam_z0)
    flange = _box(xc - 11.0, xc + 11.0, beam_y0 - 20.0, beam_y0 + 4.0, beam_z0 - 4.0, beam_z0)
    g = blk.union(plate).union(flange)
    cone = cq.Workplane("XY").add(cq.Solid.makeCone(0.01, ztop - zs + 0.02, ztop - zs + 0.02, cq.Vector(xc, yc, zs), cq.Vector(0, 0, 1)))
    funnel = cq.Workplane("XY").add(cq.Solid.makeCone(nd / 2 + 1.0, nd / 2 + 1.0 + 4.0, 4.0, cq.Vector(xc, yc, ztop - 4.0 + 0.01), cq.Vector(0, 0, 1)))
    g = g.cut(cone).cut(funnel)
    for dx in (-6.0, 6.0):
        g = g.cut(_cyl(2.75, 6.0, xc + dx, beam_y0 - 10.0, beam_z0 - 5.0))
    return g


# ---------------------------------------------------------------- 5. carriage v10: the ribs on the outer face
def carriage_v10(print_web: bool = False) -> cq.Workplane:
    """carriage_v7 with its two stiffening ribs (4 x 7, along x 17-288) moved from the inner face to the outer face (|u| 29-33),
    so the inner face under the EC is flat: the pinion clears every passing carriage by 4 mm and the EC's rail and ramps by 1."""
    c = P7.carriage_v7(print_web)
    rw, rh = RIB
    u0 = CAR_W / 2
    w0, w1 = CAR_W0 - CAR_T, CAR_W0
    for su in (-1, 1):
        ua, ub = sorted((su * (u0 - rw), su * u0))
        c = c.cut(_box(ua - 0.01, ub + 0.01, w1 - 0.01, w1 + rh + 0.01, 17.0, CHAIN_L - 17.0))
        c = c.union(_box(ua, ub, w0 - rh, w0 + 0.01, 17.0, CHAIN_L - 17.0))
    return c


# ---------------------------------------------------------------- 6. mounting plate v10: v7's without the posts, with the T's inserts
def plate_additions_v10() -> tuple[cq.Workplane, cq.Workplane]:
    """(added, cut) for mounting plate v10, Sam's frame, on his Oct 13 plate: v6/v7's extension to the cap (slab, clip 2, cap saddle,
    keeper at the back) without v7's three dock posts and their magnets; two M3 heat-set insert holes for the T-bracket, and a 1.5 mm
    relief in the underside over the NEMA 11 (it runs 0.25 mm off the plate's underside when coupled)."""
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
    cut = _cyl_x(LATCH6_PIN[0] / 2 + 0.1, k1 - LATCH6_ENGAGE - 0.5, k1 + 0.1, LATCH_Y6, LATCH6_PIN[2])
    for sy in (-1, 1):
        cut = cut.union(_cyl(1.6, 4.0, 18.5, sy * 14.35, -17.0))   # v11, 2026-11-27: the door housing's M2 inserts at |y| 14.35 (was 13.7)
    for x in T10_SCREW_X:                                       # the T-bracket's inserts
        cut = cut.union(_cyl(2.0, 5.0, x, 0.0, -18.1))
    m0, m1, mh, md = MOTOR10_RELIEF
    cut = cut.union(_box(m0, m1, -mh, mh, -18.1, -18.0 + md))
    return add, cut


# ---------------------------------------------------------------- 7. the weighing chamber v10 (world)
def chamber_v10(xf_in: float, sy: float, z_front: float) -> dict[str, cq.Workplane]:
    """v9's weighing chamber with nothing of the station in it: the side baffles and the back baffle (no slot: the P16 is gone from
    under the station), and a stepped deck: in front (to DECK10_FRONT_X1) its top 1.5 mm under the passing tubes, with only a 16 mm
    hole under the exit for the dose; behind, down at v9's 408 under the passing gears; a riser between."""
    t = ACRYLIC_T
    z1 = BAY9_TOP
    xb = DECK9_X1
    xr = DECK10_FRONT_X1
    out = {}
    for s in (-1, 1):
        y0 = sy + s * BAY9_HW - (t if s > 0 else 0.0)
        p = _box(xf_in, xr + t, y0, y0 + t, 0.0, z_front - t).union(_box(xr, xb, y0, y0 + t, 0.0, z1 - t))
        out[f"baffle10_side_{'p' if s > 0 else 'm'}"] = p
    out["baffle10_back"] = _box(xb, xb + t, sy - BAY9_HW, sy + BAY9_HW, 0.0, z1 - t)
    return out


def decks_v10(xf_in: float, sy: float, z_front: float, dose_xy: tuple) -> dict[str, cq.Workplane]:
    t = ACRYLIC_T
    xr = DECK10_FRONT_X1
    xb = DECK9_X1
    front = _box(xf_in, xr + t, sy - BAY9_HW, sy + BAY9_HW, z_front - t, z_front).cut(_cyl(DECK10_HOLE / 2, 2 * t + 2, dose_xy[0], dose_xy[1], z_front - t - 1))
    riser = _box(xr, xr + t, sy - BAY9_HW, sy + BAY9_HW, BAY9_TOP - t, z_front - t)
    back = _box(xr + t, xb + t, sy - BAY9_HW, sy + BAY9_HW, BAY9_TOP - t, BAY9_TOP)
    return {"deck10_front": front, "deck10_riser": riser, "deck10_back": back}


def bay_v10(xf_out: float, sy: float, z_top: float) -> dict[str, cq.Workplane]:
    """v9's bay window with its top at the front deck's level, so the beaker slides in level under both."""
    t = ACRYLIC_T
    xb = xf_out - BAY9_DEPTH
    dw, dh = BAY9_DOOR
    dz1 = z_top - t
    out = {"bay10_front": _box(xb, xb + t, sy - BAY9_HW, sy + BAY9_HW, 0.0, z_top - t)
           .cut(_box(xb - 1, xb + t + 1, sy - dw / 2, sy + dw / 2, dz1 - dh, dz1 + 1.0).edges("|X").fillet(3.0)),
           "bay10_top": _box(xb, xf_out, sy - BAY9_HW, sy + BAY9_HW, z_top - t, z_top)}
    for s in (-1, 1):
        y0 = sy + s * BAY9_HW - (t if s > 0 else 0.0)
        out[f"bay10_side_{'p' if s > 0 else 'm'}"] = _box(xb + t, xf_out, y0, y0 + t, 0.0, z_top - t)
    return out


def grommet_v10() -> cq.Workplane:
    """A rubber grommet for a 20 mm hole in 1/4 in plate (its axis along z, the plate's faces at z 0 and PLATE_T_SIDE)."""
    h, f = GROMMET10
    g = _cyl(f / 2, 2.0, 0, 0, -2.0).union(_cyl(h / 2, PLATE_T_SIDE, 0, 0, 0.0)).union(_cyl(f / 2, 2.0, 0, 0, PLATE_T_SIDE))
    return g.cut(_cyl(CABLE10_D / 2 + 1.5, 20.0, 0, 0, -5.0))
