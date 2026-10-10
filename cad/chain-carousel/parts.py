"""Part models for the chain-carousel test rig (CadQuery).

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
    spring clip on the top plate."""
    z0 = OUTER_GAP / 2
    top = _plate(PLATE_T, PIN_D).translate((0, 0, z0))
    bot = _plate(PLATE_T, PIN_D).translate((0, 0, -z0 - PLATE_T))
    pins = (cq.Workplane("XY").pushPoints([(-P / 2, 0), (P / 2, 0)]).circle(PIN_D / 2)
            .extrude(PIN_LEN).translate((0, 0, -PIN_LEN / 2)))
    link = top.union(bot).union(pins)
    if clip:
        c = (cq.Workplane("XY").rect(P + 2.6, 5.2).extrude(0.5)
             .faces(">Z").workplane().pushPoints([(-P / 2, 0), (P / 2, 0)]).hole(PIN_D)
             .translate((0, 0, z0 + PLATE_T)))
        link = link.union(c)
    return link


def chain_a1_link() -> cq.Workplane:
    """#35 A-1 attachment connecting link: an outer link whose top plate
    carries a tab bent up 90 deg on the outer side (+y) with one M3 hole.
    With the chain lying flat the tab stands vertical, hole axis radial."""
    link = chain_outer_link(clip=True)
    z_top = OUTER_GAP / 2 + PLATE_T
    web = (cq.Workplane("XY").center(0, (PLATE_H / 2 + A1_C) / 2)
           .rect(A1_TAB_L, A1_C - PLATE_H / 2 + PLATE_T).extrude(PLATE_T)
           .translate((0, PLATE_T / 2, z_top - PLATE_T)))
    tab = (cq.Workplane("XZ").center(0, z_top + (A1_H - PLATE_T) / 2 - 0.0)
           .rect(A1_TAB_L, A1_H + PLATE_T).extrude(-PLATE_T)
           .translate((0, A1_C, -PLATE_T / 2)))
    hole = (cq.Workplane("XZ").center(0, z_top + A1_HOLE_Z).circle(A1_HOLE_D / 2)
            .extrude(-10).translate((0, A1_C - 3, 0)))
    return link.union(web).union(tab).cut(hole)


# ---------------------------------------------------------------- sprockets
def _tooth_disc(t: float) -> cq.Workplane:
    """19T ANSI 35 tooth ring: OD disc minus N seating gaps with straight
    flanks opening to the tip. Gap 0 is centred on +x."""
    R = PD / 2
    disc = cq.Workplane("XY").circle(OD / 2).extrude(t)
    rs = SEAT_D / 2
    half = math.radians(17.0)                    # flank half-opening
    pts = [(R - rs * math.cos(a), rs * math.sin(a)) for a in (math.radians(x) for x in range(-90, 91, 15))]
    # flank lines from the seating circle tangents out past the tip
    ext = OD / 2 + 3 - R
    gap = (cq.Workplane("XY").moveTo(R - 0.2, -rs).lineTo(R + ext, -rs - ext * math.tan(half))
           .lineTo(R + ext, rs + ext * math.tan(half)).lineTo(R - 0.2, rs).close().extrude(t)
           .union(cq.Workplane("XY").center(R, 0).circle(rs).extrude(t)))
    del pts
    for k in range(N_TEETH):
        disc = disc.cut(gap.rotate((0, 0, 0), (0, 0, 1), k * 360.0 / N_TEETH))
    return disc


def sprocket_drive() -> cq.Workplane:
    """35B19 (19T, B hub) bored 14 mm with a 5 mm keyway for the NEMA 34.
    Tooth ring centred on z = 0, hub below it (hub-down, into the deck)."""
    ring = _tooth_disc(TOOTH_W).translate((0, 0, -TOOTH_W / 2))
    hub = cq.Workplane("XY").circle(HUB_D / 2).extrude(LTB - TOOTH_W).translate((0, 0, -LTB + TOOTH_W / 2))
    s = ring.union(hub)
    bore = cq.Workplane("XY").circle(DRIVE_BORE / 2).extrude(60).translate((0, 0, -30))
    key = cq.Workplane("XY").center(DRIVE_BORE / 2, 0).rect(4.6, M34_KEY_W).extrude(60).translate((0, 0, -30))
    setscrews = (cq.Workplane("YZ").center(0, -LTB + TOOTH_W / 2 + 8).circle(3.0).extrude(30)
                 .union(cq.Workplane("XZ").center(0, -LTB + TOOTH_W / 2 + 8).circle(3.0).extrude(-30)))
    return s.cut(bore).cut(key).cut(setscrews)


def sprocket_idler() -> cq.Workplane:
    """19T #35 idler with a pressed-in ball bearing (35BB19H style),
    3/8" bore. Tooth ring centred on z = 0, bearing hub both sides."""
    ring = _tooth_disc(TOOTH_W).translate((0, 0, -TOOTH_W / 2))
    hub = cq.Workplane("XY").circle(IDLER_HUB_D / 2).extrude(IDLER_W).translate((0, 0, -IDLER_W / 2))
    race = cq.Workplane("XY").circle(IDLER_HUB_D / 2 - 2).circle(IDLER_HUB_D / 2 - 3).extrude(IDLER_W + 0.01).translate((0, 0, -IDLER_W / 2))
    bore = cq.Workplane("XY").circle(IDLER_BORE / 2).extrude(40).translate((0, 0, -20))
    return ring.union(hub).cut(race).cut(bore)


# ---------------------------------------------------------------- drive
def nema34() -> cq.Workplane:
    """34HS59-6004D-E1000: 86 mm flange, 69.58 mm bolt square, 73 mm pilot,
    14 mm keyed shaft. Mounting face at z = 0, shaft up (+z), body down."""
    f = M34_FLANGE
    cap = (cq.Workplane("XY").rect(f, f).extrude(-12).edges("|Z").chamfer(6)
           .faces(">Z").workplane().rect(M34_BOLT_SQ, M34_BOLT_SQ, forConstruction=True)
           .vertices().hole(M34_HOLE_D))
    body = (cq.Workplane("XY").rect(f - 1, f - 1).extrude(-(M34_BODY_L - 24)).edges("|Z").chamfer(11)
            .translate((0, 0, -12)))
    rear = cq.Workplane("XY").rect(f, f).extrude(-12).edges("|Z").chamfer(6).translate((0, 0, -(M34_BODY_L - 12)))
    enc = cq.Workplane("XY").rect(f - 6, f - 6).extrude(-M34_ENC_L).edges("|Z").fillet(4).translate((0, 0, -M34_BODY_L))
    gland = cq.Workplane("YZ").center(0, -M34_BODY_L - M34_ENC_L / 2).circle(5).extrude(12).translate((f / 2 - 3, 0, 0))
    pilot = cq.Workplane("XY").circle(M34_PILOT_D / 2).extrude(M34_PILOT_H)
    shaft = cq.Workplane("XY").circle(M34_SHAFT_D / 2).extrude(M34_SHAFT_L)
    key = cq.Workplane("XY").center(M34_SHAFT_D / 2 - 1.0, 0).rect(5.0, M34_KEY_W).extrude(25).translate((0, 0, M34_SHAFT_L - 27))
    return cap.union(body).union(rear).union(enc).union(gland).union(pilot).union(shaft).union(key)


def motor_plate() -> cq.Workplane:
    """1/4" 6061 plate under the deck: pilot bore, motor holes, 4 M5
    countersunk holes up into the deck and 4 for the cross-member brackets."""
    s = MOTOR_PLATE
    p = (cq.Workplane("XY").rect(s, s).extrude(MOTOR_PLATE_T).edges("|Z").fillet(6)
         .faces(">Z").workplane().hole(M34_PILOT_D + 0.5)
         .faces(">Z").workplane().rect(M34_BOLT_SQ, M34_BOLT_SQ, forConstruction=True).vertices().hole(M34_HOLE_D)
         .faces(">Z").workplane().rect(s - 20, s - 20, forConstruction=True).vertices().hole(5.5))
    return p


def key_5x5() -> cq.Workplane:
    return cq.Workplane("XY").rect(25, 5).extrude(5).edges("|Z").fillet(2.49)


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
    prof = prof.cut(cq.Workplane("XY").circle(4.2 / 2).extrude(length))
    return prof.edges("|Z").fillet(0.4) if False else prof


def corner_bracket() -> cq.Workplane:
    """Cast 2020 corner bracket, 20 x 20 x 20, two M5 slots. Legs along
    +x and +z, back faces on the x = 0 and z = 0 planes."""
    t = 3.5
    b = (cq.Workplane("XZ").polyline([(0, 0), (20, 0), (20, t), (t, 20), (0, 20)]).close().extrude(-18)
         .translate((0, 9, 0)))
    b = b.union(cq.Workplane("XZ").polyline([(t, t), (16, t), (t, 16)]).close().extrude(-2).translate((0, 1, 0)))
    holes = (cq.Workplane("XY").center(12, 0).circle(2.75).extrude(t + 1)
             .union(cq.Workplane("YZ").center(0, 12).circle(2.75).extrude(t + 1)))
    return b.cut(holes)


def leveling_foot() -> cq.Workplane:
    stud = cq.Workplane("XY").circle(4).extrude(20)
    pad = cq.Workplane("XY").circle(15).extrude(-8).union(cq.Workplane("XY").polygon(6, 14).extrude(5))
    return pad.union(stud)


def deck(cut_station: bool = True) -> cq.Workplane:
    """1/2" HDPE deck, top face at z = 0. Holes are added by layout.py
    (deck_holes) because they depend on the chain solution."""
    return cq.Workplane("XY").rect(DECK_L, DECK_W).extrude(-DECK_T).edges("|Z").fillet(10)


# ---------------------------------------------------------------- idler
def idler_stud() -> cq.Workplane:
    """3/8"-16 x 2-1/2" hex bolt, head down (under the deck)."""
    head = cq.Workplane("XY").polygon(6, 14.3 / math.cos(math.pi / 6)).extrude(6.0)
    shank = cq.Workplane("XY").circle(9.525 / 2).extrude(63.5).translate((0, 0, 6.0))
    return head.union(shank)


def nut_38() -> cq.Workplane:
    return cq.Workplane("XY").polygon(6, 14.3 / math.cos(math.pi / 6)).extrude(8.3).faces(">Z").workplane().hole(9.525)


def washer(od: float, id_: float, t: float) -> cq.Workplane:
    return cq.Workplane("XY").circle(od / 2).circle(id_ / 2).extrude(t)


def idler_slider() -> cq.Workplane:
    """Printed (PETG) slider: sits in the deck's idler slot, carries the
    3/8" stud and sets the idler's tooth ring at the chain centre plane.
    Its tail takes the M5 jack screw from the tensioner block."""
    h = CHAIN_Z - IDLER_W / 2           # top of the boss, under the bearing's inner race
    base = cq.Workplane("XY").rect(40, 30).extrude(3.0).edges("|Z").fillet(4)
    boss = cq.Workplane("XY").circle(9.0).extrude(h)
    tail = cq.Workplane("XY").center(-26, 0).rect(16, 14).extrude(10).edges("|Z").fillet(2)
    s = base.union(boss).union(tail)
    s = s.cut(cq.Workplane("XY").circle(9.7 / 2).extrude(30).translate((0, 0, -5)))
    nut_pocket = cq.Workplane("YZ").center(0, 5).polygon(6, 9.2).extrude(4).translate((-32, 0, 0))
    return s.cut(nut_pocket).cut(cq.Workplane("YZ").center(0, 5).circle(2.7).extrude(20).translate((-40, 0, 0)))


def tensioner_block() -> cq.Workplane:
    """Printed block screwed to the deck; an M5 jack screw through it pushes
    the idler slider outward (-x) to tension the chain."""
    b = cq.Workplane("XY").rect(16, 30).extrude(16).edges("|Z").fillet(2)
    b = b.cut(cq.Workplane("YZ").center(0, 5).circle(2.75).extrude(30).translate((-15, 0, 0)))
    for y in (-9, 9):
        b = b.cut(cq.Workplane("XY").center(0, y).circle(2.0).extrude(30).translate((0, 0, -5)))
        b = b.cut(cq.Workplane("XY").center(0, y).circle(3.2).extrude(3).translate((0, 0, 13)))
    return b


# ---------------------------------------------------------------- carriage
def carriage() -> cq.Workplane:
    """Printed (PETG) carriage base plate, in the carriage frame: X along the
    chain, Y radially outward from the chain pitch line, Z up from the deck.

    * inner wall bolts to the A-1 tab (M3 heat-set insert),
    * 4 skids ride on the HDPE and never cross a deck cut-out,
    * edge ribs stiffen the 290 mm plate,
    * reach-through window for the station (Sam's Oct 8 electronics
      carriage) and the auger's 44T gear,
    * hinge lugs for Sam's Oct 8 mounting plate (M5 pin) and rest posts for
      its free end,
    * outer tongue for the station hold-down,
    * magnet pockets under the inner skids: index (+X) on every carriage,
      home (-X) on carriage 1 only.
    """
    y0, y1 = CAR_Y0, CAR_Y0 + CAR_L
    z0, z1 = CAR_SKID, CAR_SKID + CAR_T
    plate = (cq.Workplane("XY").center(0, (y0 + y1) / 2).rect(CAR_W, CAR_L).extrude(CAR_T)
             .edges("|Z").fillet(4).translate((0, 0, z0)))
    rw, rh = RIB
    for sx in (-1, 1):
        rib = (cq.Workplane("XY").center(sx * (CAR_W / 2 - rw / 2), (y0 + 12 + y1 - 4) / 2)
               .rect(rw, y1 - 4 - y0 - 12).extrude(rh).translate((0, 0, z1)))
        plate = plate.union(rib)
    win = (cq.Workplane("XY").center(0, (CUT_Y[0] + CUT_Y[1]) / 2).rect(2 * CUT_X, CUT_Y[1] - CUT_Y[0])
           .extrude(CAR_T + 2).edges("|Z").fillet(3).translate((0, 0, z0 - 1)))
    lighten = (cq.Workplane("XY").pushPoints([(0, y0 + 75), (0, y0 + 135)]).rect(36, 44)
               .extrude(CAR_T + 2).edges("|Z").fillet(6).translate((0, 0, z0 - 1)))
    plate = plate.cut(win).cut(lighten)
    # inner wall that meets the A-1 tab
    tab_top = CHAIN_Z + OUTER_GAP / 2 + PLATE_T + A1_H
    wall = (cq.Workplane("XY").center(0, y0 + 5).rect(A1_TAB_L + 10, 10).extrude(tab_top - z0)
            .translate((0, 0, z0)))
    insert_z = CHAIN_Z + OUTER_GAP / 2 + PLATE_T + A1_HOLE_Z
    insert = cq.Workplane("XZ").center(0, insert_z).circle(4.0 / 2).extrude(-7).translate((0, y0, 0))
    plate = plate.union(wall).cut(insert)
    # skids: two inner, two outer, all clear of the deck's station cut-out
    skids = (cq.Workplane("XY").pushPoints([(-25, y0 + 27), (25, y0 + 27)]).rect(12, 40).extrude(CAR_SKID)
             .union(cq.Workplane("XY").pushPoints([(-25, y1 - 10), (25, y1 - 10)]).rect(12, 14).extrude(CAR_SKID))
             .edges("|Z").fillet(2))
    plate = plate.union(skids)
    # hinge lugs (merge into the ribs)
    lug_h = HINGE_Z + 7 - z1
    for sx in (-1, 1):
        lug = (cq.Workplane("YZ").center(HINGE_Y, z1 + lug_h / 2).rect(16, lug_h).extrude(LUG_T)
               .edges("|X and >Z").fillet(7.9).translate((sx * LUG_X - LUG_T / 2, 0, 0)))
        plate = plate.union(lug)
    pin = cq.Workplane("YZ").center(HINGE_Y, HINGE_Z).circle(HINGE_D / 2).extrude(80).translate((-40, 0, 0))
    plate = plate.cut(pin)
    # rest posts under the mounting plate's free end (Sam's plate: 98.8 from the hinge, 18 below it)
    y_rest = HINGE_Y - 94.0
    posts = (cq.Workplane("XY").pushPoints([(-20, y_rest), (20, y_rest)]).rect(8, 8)
             .extrude(HINGE_Z - 18.0 - z1).translate((0, 0, z1)))
    plate = plate.union(posts)
    # hold-down tongue
    tw, tt, tl = TONGUE[2], TONGUE[1], TONGUE[0]
    tongue = (cq.Workplane("XY").center(0, y1 + tl / 2 - 1).rect(tw, tl + 2).extrude(tt)
              .edges("|Z and >Y").fillet(3).translate((0, 0, z0)))
    plate = plate.union(tongue)
    # magnet pockets from below
    for (x, y) in ((-25, y0 + 40), (25, y0 + 40)):
        plate = plate.cut(cq.Workplane("XY").center(x, y).circle(MAGNET_D / 2 + 0.1)
                          .extrude(MAGNET_H + 0.3).translate((0, 0, -0.1)))
    return plate


def hold_down() -> cq.Workplane:
    """Printed hold-down block at the station: an overhanging lip 0.5 mm
    above the carriage tongue reacts the station's upward push. Frame: X
    along the chain, Y radial (same as the carriage), Z up from the deck."""
    y_t0 = CAR_Y0 + CAR_L - 1          # tongue inner edge
    tz = CAR_SKID + TONGUE[1]
    base = cq.Workplane("XY").center(0, y_t0 + 22).rect(40, 20).extrude(tz + 0.5 + 4)
    lip = (cq.Workplane("XY").center(0, y_t0 + 9).rect(40, 10).extrude(4)
           .translate((0, 0, tz + 0.5)))
    lead = cq.Workplane("YZ").polyline([(y_t0 + 4, tz + 0.5), (y_t0 + 14, tz + 0.5), (y_t0 + 14, tz + 3)]).close().extrude(40).translate((-20, 0, 0))
    b = base.union(lip).cut(lead)
    for x in (-12, 12):
        b = b.cut(cq.Workplane("XY").center(x, y_t0 + 24).circle(2.2).extrude(30).translate((0, 0, -1)))
        b = b.cut(cq.Workplane("XY").center(x, y_t0 + 24).circle(4.2).extrude(4).translate((0, 0, tz + 0.5)))
    return b.edges("|Z").fillet(1.5)


def hall_holder() -> cq.Workplane:
    """Printed plug pressed into a 12 mm deck hole from below; holds an
    A3144 (TO-92) face-up 0.8 mm under the deck surface."""
    plug = cq.Workplane("XY").circle(5.9).extrude(DECK_T - 0.8).translate((0, 0, -DECK_T))
    flange = cq.Workplane("XY").circle(9).extrude(2).translate((0, 0, -DECK_T - 2))
    p = plug.union(flange)
    pocket = cq.Workplane("XY").rect(4.3, 3.3).extrude(5).translate((0, 0, -0.8 - 3.2))
    leads = cq.Workplane("XY").rect(4.3, 1.4).extrude(DECK_T + 4).translate((0, 0, -DECK_T - 3))
    return p.cut(pocket).cut(leads)


def a3144() -> cq.Workplane:
    body = cq.Workplane("XY").rect(4.0, 3.0).extrude(1.5).translate((0, 0, -1.5))
    legs = cq.Workplane("XY").pushPoints([(-1.27, 0), (0, 0), (1.27, 0)]).rect(0.4, 0.4).extrude(14).translate((0, 0, -15.5))
    return body.union(legs)


def magnet() -> cq.Workplane:
    return cq.Workplane("XY").circle(MAGNET_D / 2).extrude(MAGNET_H)


# ---------------------------------------------------------------- fasteners
def shcs(d: float, L: float, head: str = "socket") -> cq.Workplane:
    """Screw with its head's underside at z = 0, shank down (-z)."""
    if head == "button":
        h = cq.Workplane("XY").circle(0.95 * d).extrude(0.55 * d)
    elif head == "flat":
        h = cq.Workplane("XY").circle(d * 0.5).workplane(offset=0.6 * d).circle(d).loft().translate((0, 0, -0.6 * d))
    else:
        h = cq.Workplane("XY").circle(0.75 * d).extrude(d)
    sh = cq.Workplane("XY").circle(d / 2).extrude(-L)
    if head == "flat":
        sh = sh.translate((0, 0, 0))
    return h.union(sh)


def hexnut(d: float) -> cq.Workplane:
    s = {3: 5.5, 5: 8.0}[int(d)]
    return cq.Workplane("XY").polygon(6, s / math.cos(math.pi / 6)).extrude(0.8 * d).faces(">Z").workplane().hole(d)


def tnut_m5() -> cq.Workplane:
    """Drop-in (roll-in) M5 T-nut for 2020 slot 6."""
    b = cq.Workplane("XY").rect(10, 6).extrude(4).edges("|X and <Z").fillet(1.8)
    return b.faces(">Z").workplane().hole(5)


def heat_insert_m3() -> cq.Workplane:
    return cq.Workplane("XY").circle(2.3).circle(1.5).extrude(5.7)


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
    b = b.union(box(23, 6.4, 5, 0).translate((0, 0, 1.6)))   # ULN2803A DIP-18
    b = b.union(box(25, 8, 10, 0).translate((0, 18, 1.6)))   # screw terminals
    return b


def estop() -> cq.Workplane:
    b = box(68, 68, 60, 4)
    return b.union(cq.Workplane("XY").circle(20).extrude(12).translate((0, 0, 60)))


def board_panel() -> cq.Workplane:
    """1/4" plywood electronics board (sits beside the rig)."""
    return box(420, 300, 6.35, 4)


def din_terminal() -> cq.Workplane:
    return box(40, 20, 15, 1)
