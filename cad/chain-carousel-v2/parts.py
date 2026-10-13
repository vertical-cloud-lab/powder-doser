"""Part models for the chain-carousel test rig v2 (CadQuery).

Purchased parts are modelled from the vendor's dimension tables (BOM.md
cites them) at the level of detail that matters for fit: envelopes, bores,
hole patterns, the chain's plates/pins/bushings and the sprocket's tooth
gaps. Printed parts are the design itself. Every builder returns a solid in
the part's own frame; layout.py places them.
"""
from __future__ import annotations

import math

import cadquery as cq

from params import *  # noqa: F401,F403  (one dimension table for the whole rig)


# ---------------------------------------------------------------- chain
def _plate(t: float, hole_d: float) -> cq.Workplane:
    """Figure-8 link plate in the XY plane, pins at x = +-P/2, z in [0, t]."""
    r = PLATE_H / 2
    body = (cq.Workplane("XY").rect(P, PLATE_H).extrude(t)
            .union(cq.Workplane("XY").pushPoints([(-P / 2, 0), (P / 2, 0)]).circle(r).extrude(t)))
    waist = 4.2
    cut = (cq.Workplane("XY").pushPoints([(0, r + waist - 0.55), (0, -(r + waist - 0.55))])
           .circle(waist).extrude(t))
    return body.cut(cut).faces(">Z").workplane().pushPoints([(-P / 2, 0), (P / 2, 0)]).hole(hole_d)


def chain_inner_link() -> cq.Workplane:
    """Two inner plates on two bushings (no rollers on #35). Centred on the
    chain centre plane, pins along z."""
    z0 = W_IN / 2
    top = _plate(PLATE_T, BUSH_D).translate((0, 0, z0))
    bot = _plate(PLATE_T, BUSH_D).translate((0, 0, -z0 - PLATE_T))
    bush = (cq.Workplane("XY").pushPoints([(-P / 2, 0), (P / 2, 0)]).circle(BUSH_D / 2)
            .circle(PIN_D / 2 + 0.01).extrude(INNER_W).translate((0, 0, -INNER_W / 2)))
    return top.union(bot).union(bush)


def chain_outer_link(clip: bool = False) -> cq.Workplane:
    """Two outer plates and two pins. clip=True adds a connecting link's
    spring clip on the -z plate (the A-1 tab is on the +z plate)."""
    z0 = OUTER_GAP / 2
    top = _plate(PLATE_T, PIN_D).translate((0, 0, z0))
    bot = _plate(PLATE_T, PIN_D).translate((0, 0, -z0 - PLATE_T))
    pins = (cq.Workplane("XY").pushPoints([(-P / 2, 0), (P / 2, 0)]).circle(PIN_D / 2)
            .extrude(PIN_LEN).translate((0, 0, -PIN_LEN / 2)))
    link = top.union(bot).union(pins)
    if clip:
        c = (cq.Workplane("XY").rect(P + 2.6, 5.2).extrude(0.5)
             .faces(">Z").workplane().pushPoints([(-P / 2, 0), (P / 2, 0)]).hole(PIN_D)
             .translate((0, 0, -z0 - PLATE_T - 0.5)))
        link = link.union(c)
    return link


def chain_a1_link() -> cq.Workplane:
    """#35 A-1 attachment connecting link: an outer link whose +z plate runs
    out past its outer edge (+y) and bends 90 deg into a tab along the pins,
    one hole (Tsubaki RS35 A-1: S, C, X, N in params.py). On the vertical
    loop the tab lies on the outside of the loop with its hole radial."""
    link = chain_outer_link(clip=True)
    z_top = OUTER_GAP / 2 + PLATE_T                       # outer face of the +z plate
    web = (cq.Workplane("XY").center(0, (PLATE_H / 2 - 1 + A1_C) / 2)
           .rect(A1_TAB_L, A1_C - PLATE_H / 2 + 1).extrude(PLATE_T).translate((0, 0, z_top - PLATE_T)))
    tab = (cq.Workplane("XY").center(0, A1_C - PLATE_T / 2).rect(A1_TAB_L, PLATE_T)
           .extrude(A1_X - (z_top - PLATE_T)).translate((0, 0, z_top - PLATE_T)))
    tab = tab.edges("|Y and >Z").fillet(A1_TAB_L / 2 - 0.01)
    hole = (cq.Workplane("XZ").center(0, A1_HOLE_C).circle(A1_HOLE_D / 2).extrude(-10).translate((0, A1_C - 5, 0)))
    return link.union(web).union(tab).cut(hole)


# ---------------------------------------------------------------- sprockets
def _tooth_disc(t: float, n: int = N_TEETH) -> cq.Workplane:
    """ANSI 35 tooth ring: OD disc minus n seating gaps with straight flanks
    opening to the tip. Gap 0 is centred on +x."""
    pd = P / math.sin(math.pi / n)
    od = P * (0.6 + 1 / math.tan(math.pi / n))
    r = pd / 2
    disc = cq.Workplane("XY").circle(od / 2).extrude(t)
    rs = SEAT_D / 2
    half = math.radians(17.0)                    # flank half-opening
    ext = od / 2 + 3 - r
    gap = (cq.Workplane("XY").moveTo(r - 0.2, -rs).lineTo(r + ext, -rs - ext * math.tan(half))
           .lineTo(r + ext, rs + ext * math.tan(half)).lineTo(r - 0.2, rs).close().extrude(t)
           .union(cq.Workplane("XY").center(r, 0).circle(rs).extrude(t)))
    gaps = gap
    for k in range(1, n):
        gaps = gaps.union(gap.rotate((0, 0, 0), (0, 0, 1), k * 360.0 / n))
    return disc.cut(gaps)


def sprocket(n: int, bore: float, hub_d: float, ltb: float, key: tuple) -> cq.Workplane:
    """Type B (hub one side) #35 sprocket with a finished bore, keyway and
    two set screws (one over the keyway, one at 90 deg). Tooth ring centred
    on z = 0, hub toward -z."""
    ring = _tooth_disc(TOOTH_W, n).translate((0, 0, -TOOTH_W / 2))
    hub = cq.Workplane("XY").circle(hub_d / 2).extrude(ltb - TOOTH_W).translate((0, 0, -ltb + TOOTH_W / 2))
    s = ring.union(hub)
    bore_ = cq.Workplane("XY").circle(bore / 2).extrude(60).translate((0, 0, -30))
    kw = cq.Workplane("XY").center(0, bore / 2).rect(key[0], 2 * key[1]).extrude(60).translate((0, 0, -30))
    zs = -ltb + TOOTH_W / 2 + (ltb - TOOTH_W) / 2
    setscrews = (cq.Workplane("XZ").center(0, zs).circle(3.0).extrude(-40)
                 .union(cq.Workplane("YZ").center(0, zs).circle(3.0).extrude(40)))
    return s.cut(bore_).cut(kw).cut(setscrews)


def sprocket_32() -> cq.Workplane:
    """35BS32-5/8: 32T, 2 in hub, 7/8 in through the bore, 5/8 in bore."""
    return sprocket(N_TEETH, SPROCKET_BORE, HUB_D, LTB, KEYWAY)


def sprocket_15_shaft() -> cq.Workplane:
    """35BS15H-5/8 on the B+ shaft's stub."""
    return sprocket(N15, SPROCKET_BORE, HUB15_D, LTB15, KEYWAY)


def sprocket_15_motor() -> cq.Workplane:
    """35BS15H-1/2 re-bored to 14 mm with a 5 mm keyway, on the NEMA 34."""
    return sprocket(N15, M34_SHAFT_D, HUB15_D, LTB15, (5.0, 2.3))


# ---------------------------------------------------------------- shafts, bearings, drive
def shaft(length: float, d: float = SHAFT_D) -> cq.Workplane:
    """Round shaft along +z from z = 0, with a set-screw flat (cosmetic)."""
    s = cq.Workplane("XY").circle(d / 2).extrude(length)
    return s.edges().chamfer(0.5)


def flange_bearing() -> cq.Workplane:
    """SBSFL202-10 2-bolt stamped-steel flange unit (envelope). Mounting
    plane z = 0 (on the plate's outer face), front dome and insert toward +z,
    rear dome toward -z (into the plate's 49 mm hole), bolt line along y."""
    b = BRG
    lobe_r = 9.0
    lobes = cq.Workplane("XY").pushPoints([(0, -b["J"] / 2), (0, b["J"] / 2)]).circle(lobe_r).extrude(b["T"])
    hull = (cq.Workplane("XY").polyline([(-lobe_r, -b["J"] / 2), (-b["W"] / 2, -6), (-b["W"] / 2, 6), (-lobe_r, b["J"] / 2),
                                         (lobe_r, b["J"] / 2), (b["W"] / 2, 6), (b["W"] / 2, -6), (lobe_r, -b["J"] / 2)])
            .close().extrude(b["T"]))
    flange = lobes.union(hull).union(cq.Workplane("XY").circle(b["W"] / 2 - 4).extrude(b["T"]))
    front = cq.Workplane("XY").circle(b["DOME_D"] / 2).extrude(b["OUT"] - 2.0).edges(">Z").chamfer(4)
    rear = cq.Workplane("XY").circle(b["DOME_D"] / 2).extrude(-(b["IN"] - 1.0)).edges("<Z").chamfer(4)
    ring = cq.Workplane("XY").circle(b["RING_D"] / 2).extrude(b["OUT"] + b["IN"]).translate((0, 0, -b["IN"]))
    body = flange.union(front).union(rear).union(ring)
    body = body.cut(cq.Workplane("XY").pushPoints([(0, -b["J"] / 2), (0, b["J"] / 2)]).circle(b["BOLT_D"] / 2 + 0.4)
                    .extrude(b["T"] + 2).translate((0, 0, -1)))
    return body.cut(cq.Workplane("XY").circle(SHAFT_D / 2).extrude(b["OUT"] + b["IN"] + 2).translate((0, 0, -b["IN"] - 1)))


def nema34() -> cq.Workplane:
    """34HS59-6004D-E1000: 86 mm flange, 69.58 mm bolt square, 73 mm pilot,
    14 mm keyed shaft. Mounting face at z = 0, shaft up (+z), body down."""
    f = M34_FLANGE
    cap = (cq.Workplane("XY").rect(f, f).extrude(-12).edges("|Z").chamfer(6)
           .faces(">Z").workplane().rect(M34_BOLT_SQ, M34_BOLT_SQ, forConstruction=True)
           .vertices().hole(M34_HOLE_D))
    body = (cq.Workplane("XY").rect(f - 1, f - 1).extrude(-(M34_BODY_L - 24)).edges("|Z").chamfer(21)
            .translate((0, 0, -12)))
    rear = cq.Workplane("XY").rect(f, f).extrude(-12).edges("|Z").chamfer(6).translate((0, 0, -(M34_BODY_L - 12)))
    enc = cq.Workplane("XY").rect(f - 6, f - 6).extrude(-M34_ENC_L).edges("|Z").fillet(4).translate((0, 0, -M34_BODY_L))
    gland = cq.Workplane("YZ").center(0, -M34_BODY_L - M34_ENC_L / 2).circle(5).extrude(12).translate((f / 2 - 3, 0, 0))
    pilot = cq.Workplane("XY").circle(M34_PILOT_D / 2).extrude(M34_PILOT_H)
    shaft_ = cq.Workplane("XY").circle(M34_SHAFT_D / 2).extrude(M34_SHAFT_L)
    key = cq.Workplane("XY").center(M34_SHAFT_D / 2 - 1.0, 0).rect(5.0, M34_KEY_W).extrude(25).translate((0, 0, M34_SHAFT_L - 27))
    return cap.union(body).union(rear).union(enc).union(gland).union(pilot).union(shaft_).union(key)


# ---------------------------------------------------------------- frame
def extrusion_2020(length: float) -> cq.Workplane:
    """2020 B-type slot 6 profile (Misumi HFS5-2020 dims) along +z."""
    s = 20.0
    prof = cq.Workplane("XY").rect(s, s).extrude(length)
    slot_open, lip, cav_w, cav_d = 6.2, 1.8, 11.0, 6.1
    for ang in (0, 90, 180, 270):
        slot = (cq.Workplane("XY").center(s / 2 - lip / 2, 0).rect(lip + 0.02, slot_open).extrude(length)
                .union(cq.Workplane("XY").center(s / 2 - lip - (cav_d - lip) / 2, 0)
                       .rect(cav_d - lip, cav_w).extrude(length)))
        prof = prof.cut(slot.rotate((0, 0, 0), (0, 0, 1), ang))
    return prof.cut(cq.Workplane("XY").circle(4.2 / 2).extrude(length))


def corner_bracket() -> cq.Workplane:
    """Cast 2020 corner bracket, 20 x 20 x 18, two M5 holes. Legs along
    +x and +z, back faces on the x = 0 and z = 0 planes, centred on y = 0."""
    t = 3.5
    b = (cq.Workplane("XZ").polyline([(0, 0), (20, 0), (20, t), (t, 20), (0, 20)]).close().extrude(9, both=True))
    b = b.union(cq.Workplane("XZ").polyline([(t, t), (16, t), (t, 16)]).close().extrude(1, both=True))
    holes = (cq.Workplane("XY").center(12, 0).circle(2.75).extrude(t + 1)
             .union(cq.Workplane("YZ").center(0, 12).circle(2.75).extrude(t + 1)))
    return b.cut(holes)


def leveling_foot() -> cq.Workplane:
    """M5 leveling foot, pad on z = 0, stud up."""
    stud = cq.Workplane("XY").circle(2.5).extrude(FOOT_H + 6)
    pad = cq.Workplane("XY").circle(15).extrude(6).union(cq.Workplane("XY").polygon(6, 9.2).extrude(FOOT_H - 1))
    return pad.union(stud)


def side_plate(back: bool) -> cq.Workplane:
    """1/4 in 6061 side plate in its own frame: x across the loop (world y),
    y up (world z), plate from z = 0 (inner face) to z = +PLATE_T_SIDE
    (outer face). Holes are added by layout.py (they follow the chain
    solution); this is the blank."""
    w, (z0, z1) = SIDE_W, (SIDE_Z_BACK if back else SIDE_Z)
    p = (cq.Workplane("XY").center(0, (z0 + z1) / 2).rect(w, z1 - z0).extrude(PLATE_T_SIDE)
         .edges("|Z").fillet(6))
    return p


def tensioner_block() -> cq.Workplane:
    """Printed (PETG) jack block under a top bearing, on the side plate's
    outer face: two M5 screws into the plate, an M5 jack screw (nut trapped)
    pushing up on the underside of the bearing's front dome. Frame: x across
    (world y), y up, back face on z = 0."""
    b = cq.Workplane("XY").center(0, -9).rect(30, 18).extrude(14).edges("|Z").fillet(2)
    b = b.cut(cq.Workplane("XZ").center(0, 7).circle(2.75).extrude(30))                            # jack screw, along y
    b = b.cut(cq.Workplane("XY").center(0, -6.2).rect(9.6, 4.4).extrude(12.6).translate((0, 0, 1.5)))  # nut slot, open to the front
    for x in (-10, 10):
        b = b.cut(cq.Workplane("XY").center(x, -12).circle(2.75).extrude(30).translate((0, 0, -1)))
        b = b.cut(cq.Workplane("XY").center(x, -12).circle(4.8).extrude(10.01).translate((0, 0, 4)))
    return b


# ---------------------------------------------------------------- carriage
def carriage() -> cq.Workplane:
    """Printed (PETG) carriage in the carriage frame: X = u (along the
    travel), Y = w (radially inward, into the loop), Z = x (front -> back).

    * a 5 mm plate outside both chains, sitting on the two A-1 tabs; one
      M3 heat-set insert at each end takes the screw through the tab
      (the holes are radial: vertical at the station),
    * tongues past both chains for the station hold-downs, with the index
      magnet (front, every carriage) and home magnet (back, carriage 1),
    * edge ribs on the inside, hinge lugs for Sam's Oct 8 mounting plate,
      a station window for his electronics carriage and the auger's gear,
    * two snap hooks over the mounting plate's edges, so it stays shut on
      the top run (the station's tilt pulls it past them).
    """
    u0 = CAR_W / 2
    w0, w1 = CAR_W0 - CAR_T, CAR_W0                     # plate outer, inner faces
    xa, xb = -8.0, CHAIN_L + 8.0                         # full-width plate; tongues beyond
    plate = (cq.Workplane("XY").rect(CAR_W, CAR_T).extrude(xb - xa).translate((0, (w0 + w1) / 2, xa))
             .edges("|Y").fillet(3))
    for x0, x1 in ((CAR_X0, xa + 1), (xb - 1, CAR_X1)):
        t = (cq.Workplane("XY").rect(TONGUE_W, CAR_T).extrude(x1 - x0).translate((0, (w0 + w1) / 2, x0))
             .edges("|Y").fillet(2))
        plate = plate.union(t)
    # edge ribs on the inside, from past the front A-1 tab to before the back one
    rw, rh = RIB
    rx0, rx1 = 17.0, CHAIN_L - 17.0
    for su in (-1, 1):
        rib = (cq.Workplane("XY").center(su * (u0 - rw / 2), w1 + rh / 2).rect(rw, rh).extrude(rx1 - rx0)
               .translate((0, 0, rx0)))
        rib = rib.cut(cq.Workplane("XY").center(su * (u0 - rw / 2), w1 + rh / 2).rect(rw + 1, rh + 1)
                      .extrude(16).translate((0, 0, SNAP_X - 8)))           # room for the snap hook to flex
        rib = rib.cut(cq.Workplane("XY").center(su * (u0 - rw / 2), w1 + rh / 2).rect(rw + 1, rh + 1)
                      .extrude(18).translate((0, 0, HINGE_X - 9)))          # the lug takes over here
        plate = plate.union(rib)
    # station window: electronics carriage, gear, outlet's powder path
    win = (cq.Workplane("XY").rect(2 * WIN_U, CAR_T + 2).extrude(WIN_X[1] - WIN_X[0])
           .translate((0, (w0 + w1) / 2, WIN_X[0])).edges("|Y").fillet(3))
    lighten = cq.Workplane("XY")
    for xc in (155.0, 200.0, 245.0):
        lighten = lighten.union(cq.Workplane("XY").rect(36, CAR_T + 2).extrude(34)
                                .translate((0, (w0 + w1) / 2, xc - 17)).edges("|Y").fillet(6))
    plate = plate.cut(win).cut(lighten)
    # hinge lugs (merge into the ribs), M5 holes countersunk on the outside for flush flat-head pins
    lug_top = HINGE_W + 6.0
    for su in (-1, 1):
        lug = (cq.Workplane("YZ").center(w1 + (lug_top - w1) / 2, HINGE_X).rect(lug_top - w1, 16)
               .extrude(LUG_T).translate((LUG_U if su > 0 else -LUG_U - LUG_T, 0, 0)))
        lug = lug.edges("|X and >Y").fillet(7.9)
        # chamfer the outer-top corner to |u| + w <= INNER_CORNER (neighbours on a corner)
        u_out = LUG_U + LUG_T
        cham = (cq.Workplane("XY").polyline([(su * (INNER_CORNER - lug_top - 0.01), lug_top + 0.01),
                                             (su * (u_out + 0.01), lug_top + 0.01),
                                             (su * (u_out + 0.01), INNER_CORNER - u_out)]).close()
                .extrude(30).translate((0, 0, HINGE_X - 15)))
        plate = plate.union(lug.cut(cham))
    pin = cq.Workplane("YZ").center(HINGE_W, HINGE_X).circle(HINGE_D / 2).extrude(2 * u0 + 2).translate((-u0 - 1, 0, 0))
    plate = plate.cut(pin)
    for su in (-1, 1):
        u_out = LUG_U + LUG_T
        csk = cq.Workplane("YZ").center(HINGE_W, HINGE_X).circle(HINGE_D / 2).workplane(offset=2.8).circle(5.1).loft()
        plate = plate.cut(csk.translate((u_out - 2.8, 0, 0)) if su > 0 else
                          csk.mirror("YZ").translate((-u_out + 2.8, 0, 0)))
    # snap hooks over the mounting plate's edges (Sam's plate is +-25 wide here, top face at w = -1.35)
    top_face = HINGE_W - SAM_DROP + 5.0
    for su in (-1, 1):
        arm = (cq.Workplane("XY").center(su * (25.2 + 1.6), (w1 + top_face + 2.4) / 2)
               .rect(3.2, top_face + 2.4 - w1).extrude(12).translate((0, 0, SNAP_X - 6)))
        lip = (cq.Workplane("XY").polyline([(su * 25.2, top_face + 0.2), (su * (25.2 - SNAP_LAP), top_face + 0.9),
                                            (su * (25.2 - SNAP_LAP), top_face + 1.5), (su * 25.2, top_face + 2.4)])
               .close().extrude(12).translate((0, 0, SNAP_X - 6)))
        plate = plate.union(arm).union(lip)
    # A-1 tab screws: M3 heat-set insert holes, radial (along w), from the inner face
    for x in (A1_HOLE_C, CHAIN_L - A1_HOLE_C):
        plate = plate.cut(cq.Workplane("XZ").center(0, x).circle(4.0 / 2).extrude(4.6).translate((0, w1 + 0.01, 0)))
    # magnet pockets from the inner face of the tongues
    for x in (CAR_X0 + 7.0, CAR_X1 - 7.0):
        plate = plate.cut(cq.Workplane("XZ").center(0, x).circle(MAGNET_D / 2 + 0.15).extrude(MAGNET_H + 0.3)
                          .translate((0, w1 + 0.01, 0)))
    return plate


def hold_down() -> cq.Workplane:
    """Printed hold-down at the station, on a side plate's inner face. It
    wraps the carriage tongue like a C: a lip 0.5 mm over the tongue reacts
    the station's upward push, a foot 2 mm under it catches a downward pull,
    and a pocket in the lip holds a hall switch over the tongue's magnet.
    Frame: X = u (along the travel), Y = w (inward from the chain's pitch
    line), Z = distance from the side plate's inner face toward the chain.
    Two M5 screws come through the side plate into heat-set inserts."""
    tz = CAR_W0 + HOLD_DOWN_GAP                          # lip underside, 0.5 mm above the tongue
    tongue_end = SIDE_GAP + CAR_X0                       # 7: tongue tip's distance from the plate
    z_lip1 = SIDE_GAP - 7.0                              # lip stops 7 mm short of the chain's centre plane
    w_foot = CAR_W0 - CAR_T - 2.0                        # foot top, 2 mm under the tongue
    lip = cq.Workplane("XY").center(0, tz + 4.5).rect(40, 9).extrude(z_lip1 - tongue_end + 1.5).translate((0, 0, tongue_end - 1.5))
    web = cq.Workplane("XY").center(0, (w_foot + tz + 9) / 2).rect(40, tz + 9 - w_foot).extrude(tongue_end - 1.5)
    foot = cq.Workplane("XY").center(0, (w_foot - 22 + w_foot) / 2).rect(40, 22).extrude(16.0)
    b = lip.union(web).union(foot)
    # lead-in: chamfer the lip's underside and the foot's top at both ends along the travel
    for su in (-1, 1):
        for y0, dy in ((tz, 2.5), (w_foot, -2.5)):
            ramp = (cq.Workplane("XY").polyline([(su * 20.01, y0 - 0.01 * (dy / abs(dy))), (su * 13, y0 - 0.01 * (dy / abs(dy))),
                                                 (su * 20.01, y0 + dy)]).close().extrude(z_lip1 + 1).translate((0, 0, -0.5)))
            b = b.cut(ramp)
    # M5 heat-set inserts for the screws through the side plate
    for x in (-12.0, 12.0):
        b = b.cut(cq.Workplane("XY").center(x, w_foot - 11).circle(3.2).extrude(10.0).translate((0, 0, -0.01)))
    # hall switch pocket over the magnet (face 0.8 mm above the lip's underside) and a lead channel
    zc = SIDE_GAP + CAR_X0 + 7.0                         # magnet centre's distance from the plate
    b = b.cut(cq.Workplane("XY").center(0, tz + 0.8 + 0.9).rect(4.3, 1.8).extrude(3.3).translate((0, 0, zc - 1.65)))
    b = b.cut(cq.Workplane("XY").center(0, tz + 2.6 + 3.3).rect(4.3, 6.6).extrude(1.6).translate((0, 0, zc - 0.8)))
    return b


def hall_switch() -> cq.Workplane:
    """US5881 in TO-92: body face down at z = 0, leads up."""
    body = cq.Workplane("XY").rect(4.0, 3.0).extrude(1.5)
    legs = cq.Workplane("XY").pushPoints([(-1.27, 0), (0, 0), (1.27, 0)]).rect(0.4, 0.4).extrude(6).translate((0, 0, 1.5))
    return body.union(legs)


def magnet() -> cq.Workplane:
    return cq.Workplane("XY").circle(MAGNET_D / 2).extrude(MAGNET_H)


def auger_blank() -> cq.Workplane:
    """Printable stand-in for the lab auger on carriages 2-12: the same
    outside (25 mm tube, 46 mm 44T-gear disc at z 78.3-88.3, 26 mm threaded
    end), hollow so it can be filled with salt to working mass. Along +z
    from the outlet end."""
    tube = cq.Workplane("XY").circle(12.5).circle(10.9).extrude(220.0)
    gear = cq.Workplane("XY").circle(GEAR_R - 0.6).circle(10.9).extrude(9.6).translate((0, 0, 78.5))    # the gear's teeth, as a disc
    end = cq.Workplane("XY").circle(13.0).circle(10.9).extrude(30.0).translate((0, 0, 220.0))
    floor = cq.Workplane("XY").circle(12.5).extrude(1.6)
    return tube.union(gear).union(end).union(floor)


# ---------------------------------------------------------------- fasteners
def shcs(d: float, L: float, head: str = "socket") -> cq.Workplane:
    """Screw with its head's underside at z = 0, head up (+z), shank down (-z)."""
    if head == "button":
        h = cq.Workplane("XY").circle(0.95 * d).extrude(0.55 * d)
    elif head == "flat":
        h = cq.Workplane("XY").circle(d * 0.5).workplane(offset=0.6 * d).circle(d).loft().translate((0, 0, -0.6 * d))
    else:
        h = cq.Workplane("XY").circle(0.75 * d).extrude(d)
    return h.union(cq.Workplane("XY").circle(d / 2).extrude(-L))


def hexnut(d: float) -> cq.Workplane:
    s = {3: 5.5, 5: 8.0, 6: 10.0, 10: 16.0}[int(d)]
    return cq.Workplane("XY").polygon(6, s / math.cos(math.pi / 6)).extrude(0.8 * d).faces(">Z").workplane().hole(d)


def tnut_m5() -> cq.Workplane:
    """Drop-in (roll-in) M5 T-nut for 2020 slot 6."""
    b = cq.Workplane("XY").rect(10, 6).extrude(4).edges("|X and <Z").fillet(1.8)
    return b.faces(">Z").workplane().hole(5)


def heat_insert_m3() -> cq.Workplane:
    """CNC Kitchen M3 short insert (M3 x 4, 4.6 OD), melted into a 4.0 mm hole."""
    return cq.Workplane("XY").circle(2.3).circle(1.5).extrude(4.0)


# ---------------------------------------------------------------- electronics
def box(x, y, z, fillet=1.0) -> cq.Workplane:
    b = cq.Workplane("XY").rect(x, y).extrude(z)
    return b.edges("|Z").fillet(fillet) if fillet else b


def cl86t() -> cq.Workplane:
    """StepperOnline CL86T closed-loop driver envelope with its mounting
    flanges (151 x 97 x 52, per the vendor drawing)."""
    b = box(118, 97, 52, 2).union(box(151, 97, 4, 2))
    for x in (-68, 68):
        for y in (-38, 38):
            b = b.cut(cq.Workplane("XY").center(x, y).circle(2.25).extrude(10).translate((0, 0, -2)))
    return b


def lrs350() -> cq.Workplane:
    return box(215, 115, 30, 1)


def raspberry_pi() -> cq.Workplane:
    b = box(85, 56, 1.6, 3)
    b = b.union(box(51, 5, 8.5, 0).translate((-1, 22, 1.6)))
    b = b.union(box(21, 16, 13.5, 0).translate((32, 9, 1.6))).union(box(21, 16, 13.5, 0).translate((32, -9, 1.6)))
    return b


def perfboard() -> cq.Workplane:
    b = box(70, 50, 1.6, 1)
    b = b.union(box(23, 6.4, 5, 0).translate((0, 0, 1.6)))
    b = b.union(box(25, 8, 10, 0).translate((0, 18, 1.6)))
    return b


def estop() -> cq.Workplane:
    b = box(68, 68, 60, 4)
    return b.union(cq.Workplane("XY").circle(20).extrude(12).translate((0, 0, 60)))


def board_panel() -> cq.Workplane:
    """1/4 in plywood electronics board (sits beside the rig)."""
    return box(420, 300, 6.35, 4)
