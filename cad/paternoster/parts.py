"""Part models for the paternoster carousel (CadQuery).

Purchased parts are modelled from vendor dimension tables (BOM.md cites
them) at the detail that matters for fit: envelopes, bores, hole patterns,
the chain's plates/pins/bushings and the sprockets' tooth gaps. The NEMA 34
is StepperOnline's own STEP (PR #115). Printed parts are the design. Every
builder returns a solid in the part's own frame; layout.py places them.
"""
from __future__ import annotations

import math
from functools import lru_cache
from pathlib import Path

import cadquery as cq

from params import *  # noqa: F401,F403

HERE = Path(__file__).resolve().parent
REF = HERE / "reference"


# ---------------------------------------------------------------- chain (link frame: pins along z at x = +-P/2, travel along x, +y into the loop)
def _plate(t: float, hole_d: float) -> cq.Workplane:
    r = PLATE_H / 2
    body = (cq.Workplane("XY").rect(P, PLATE_H).extrude(t)
            .union(cq.Workplane("XY").pushPoints([(-P / 2, 0), (P / 2, 0)]).circle(r).extrude(t)))
    waist = 4.2
    cut = (cq.Workplane("XY").pushPoints([(0, r + waist - 0.55), (0, -(r + waist - 0.55))])
           .circle(waist).extrude(t))
    return body.cut(cut).faces(">Z").workplane().pushPoints([(-P / 2, 0), (P / 2, 0)]).hole(hole_d)


def chain_inner_link() -> cq.Workplane:
    z0 = W_IN / 2
    top = _plate(PLATE_T, BUSH_D).translate((0, 0, z0))
    bot = _plate(PLATE_T, BUSH_D).translate((0, 0, -z0 - PLATE_T))
    bush = (cq.Workplane("XY").pushPoints([(-P / 2, 0), (P / 2, 0)]).circle(BUSH_D / 2)
            .circle(PIN_D / 2 + 0.01).extrude(INNER_W).translate((0, 0, -INNER_W / 2)))
    return top.union(bot).union(bush)


def chain_outer_link(clip: bool = False) -> cq.Workplane:
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


def chain_sa1_link() -> cq.Workplane:
    """#35 SA-1 attachment connecting link: the +z outer plate runs on past
    its edge as a straight tab (toward -y, out of the loop), one hole at C1
    from the pitch line, opened to 3.4 mm for the pivot screw's M3 thread."""
    link = chain_outer_link(clip=True)
    z0 = OUTER_GAP / 2
    tab = (cq.Workplane("XY").center(0, -(SA1_XS + PLATE_H / 2 - 1) / 2).rect(SA1_N, SA1_XS - PLATE_H / 2 + 1)
           .extrude(PLATE_T).translate((0, 0, z0)))
    tab = tab.union(cq.Workplane("XY").center(0, -SA1_C).circle(SA1_N / 2).extrude(PLATE_T).translate((0, 0, z0)))
    hole = cq.Workplane("XY").center(0, -SA1_C).circle(SA1_HOLE_DRILLED / 2).extrude(10).translate((0, 0, -5))
    return link.union(tab).cut(hole)


# ---------------------------------------------------------------- sprockets
def _tooth_disc(t: float, n: int = N_TEETH) -> cq.Workplane:
    pd = P / math.sin(math.pi / n)
    od = P * (0.6 + 1 / math.tan(math.pi / n))
    r = pd / 2
    disc = cq.Workplane("XY").circle(od / 2).extrude(t)
    rs = SEAT_D / 2
    half = math.radians(17.0)
    ext = od / 2 + 3 - r
    gap = (cq.Workplane("XY").moveTo(r - 0.2, -rs).lineTo(r + ext, -rs - ext * math.tan(half))
           .lineTo(r + ext, rs + ext * math.tan(half)).lineTo(r - 0.2, rs).close().extrude(t)
           .union(cq.Workplane("XY").center(r, 0).circle(rs).extrude(t)))
    gaps = gap
    for k in range(1, n):
        gaps = gaps.union(gap.rotate((0, 0, 0), (0, 0, 1), k * 360.0 / n))
    return disc.cut(gaps)


@lru_cache(None)
def _ring32():
    return _tooth_disc(TOOTH_W, N_TEETH).translate((0, 0, -TOOTH_W / 2))


def sprocket_32(bore: float = SPROCKET_BORE, keyed: bool = True) -> cq.Workplane:
    """35BS32: 32T, 2 in hub toward -z (out of the loop), 7/8 in through the bore.
    Tooth ring centred on z = 0; the ring's inner face (+z) is the flush face."""
    hub = cq.Workplane("XY").circle(HUB_D / 2).extrude(LTB - TOOTH_W).translate((0, 0, -LTB + TOOTH_W / 2))
    s = _ring32().union(hub)
    s = s.cut(cq.Workplane("XY").circle(bore / 2).extrude(60).translate((0, 0, -30)))
    if keyed:
        s = s.cut(cq.Workplane("XY").center(0, bore / 2).rect(KEYWAY[0], 2 * KEYWAY[1]).extrude(60).translate((0, 0, -30)))
    zs = -LTB + TOOTH_W / 2 + (LTB - TOOTH_W) / 2
    return s.cut(cq.Workplane("XZ").center(0, zs).circle(3.0).extrude(-40))


def sprocket_32_idler() -> cq.Workplane:
    """35BS32 re-bored to 35 mm for two 6202-2RS bearings (22 mm, the hub's 7/8 in)."""
    return sprocket_32(bore=IDLER_BORE, keyed=False)


# ---------------------------------------------------------------- shafts, bearings, axles, coupling
def shaft(length: float, d: float = SHAFT_D) -> cq.Workplane:
    return cq.Workplane("XY").circle(d / 2).extrude(length).edges().chamfer(0.5)


def flange_bearing() -> cq.Workplane:
    """SBSFL202-10 2-bolt stamped-steel flange unit. Mounting plane z = 0,
    insert toward +z, rear dome toward -z (into the plate's 49 mm hole), bolt line along y."""
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


def bearing_6202() -> cq.Workplane:
    """6202-2RS deep-groove ball bearing, 15 x 35 x 11, centred on z = 0."""
    return (cq.Workplane("XY").circle(35 / 2).circle(15 / 2).extrude(11).translate((0, 0, -5.5))
            .faces(">Z or <Z").edges().chamfer(0.5))


def idler_axle() -> cq.Workplane:
    """Fixed axle for a top idler: 15 mm shaft (h6) with an M10 threaded stem
    through the side plate's slot. Shoulder face (on the plate's inner face) at z = 0,
    bearing seat along +z, stem along -z."""
    seat = cq.Workplane("XY").circle(7.5).extrude(IDLER_AXLE_L).edges(">Z").chamfer(0.6)
    shoulder = cq.Workplane("XY").circle(11.0).extrude(4.0)
    stem = cq.Workplane("XY").circle(5.0).extrude(-(PLATE_T_SIDE + 12.0))
    return seat.union(shoulder).union(stem)


def jaw_coupling() -> cq.Workplane:
    """Jaw coupling (two hubs + spider), axis along z from z = 0 to CPL_L."""
    h = (CPL_L - 2.0) / 2
    hub = cq.Workplane("XY").circle(CPL_OD / 2).extrude(h)
    spider = cq.Workplane("XY").polygon(6, CPL_OD * 0.85).extrude(2.0).translate((0, 0, h))
    c = hub.union(spider).union(hub.translate((0, 0, h + 2.0)))
    return c.cut(cq.Workplane("XY").circle(SHAFT_D / 2).extrude(CPL_L + 2).translate((0, 0, -1)))


# ---------------------------------------------------------------- motor (OEM STEP)
@lru_cache(None)
def nema34() -> cq.Workplane:
    """StepperOnline's own 34HS59-6004D-E1000 STEP (from PR #115): mounting face
    at z = 0, shaft up (+z), body down, cable exit toward -y."""
    from step_io import read_step_parts
    parts = read_step_parts(REF / "34HS59-6004D-E1000.step")
    return cq.Workplane("XY").add(next(iter(parts.values())))


def nema11_envelope() -> cq.Workplane:
    """11HS18-0674S on Sam's electronics carriage: 28 mm square, 45 mm body, 5 mm shaft.
    Mounting face at z = 0, shaft +z."""
    body = cq.Workplane("XY").rect(28, 28).extrude(-45.0).edges("|Z").chamfer(2.5)
    boss = cq.Workplane("XY").circle(11).extrude(1.5)
    sh = cq.Workplane("XY").circle(2.5).extrude(18)
    return body.union(boss).union(sh)


def pinion_20t() -> cq.Workplane:
    """Printed 20T module-1 pinion (stepper side of the 20:44 auger drive), 21 OD, 10 wide."""
    return cq.Workplane("XY").polygon(20, 21.0).extrude(10.0).cut(cq.Workplane("XY").circle(2.55).extrude(10))


def solenoid_412() -> cq.Workplane:
    """Adafruit 412 12 V push-pull solenoid, envelope 32 x 15 x 12 frame + 4.5 mm plunger, plunger along +z."""
    frame = cq.Workplane("XY").rect(15.0, 12.0).extrude(-32.0)
    plunger = cq.Workplane("XY").circle(2.25).extrude(8.0)
    return frame.union(plunger)


# ---------------------------------------------------------------- frame
def extrusion_2020(length: float) -> cq.Workplane:
    s = 20.0
    prof = cq.Workplane("XY").rect(s, s).extrude(length)
    slot_open, lip, cav_w, cav_d = 6.2, 1.8, 11.0, 6.1
    for ang in (0, 90, 180, 270):
        slot = (cq.Workplane("XY").center(s / 2 - lip / 2, 0).rect(lip + 0.02, slot_open).extrude(length)
                .union(cq.Workplane("XY").center(s / 2 - lip - (cav_d - lip) / 2, 0).rect(cav_d - lip, cav_w).extrude(length)))
        prof = prof.cut(slot.rotate((0, 0, 0), (0, 0, 1), ang))
    return prof.cut(cq.Workplane("XY").circle(4.2 / 2).extrude(length))


def corner_bracket() -> cq.Workplane:
    t = 3.5
    b = cq.Workplane("XZ").polyline([(0, 0), (20, 0), (20, t), (t, 20), (0, 20)]).close().extrude(9, both=True)
    b = b.union(cq.Workplane("XZ").polyline([(t, t), (16, t), (t, 16)]).close().extrude(1, both=True))
    holes = (cq.Workplane("XY").center(12, 0).circle(2.75).extrude(t + 1)
             .union(cq.Workplane("YZ").center(0, 12).circle(2.75).extrude(t + 1)))
    return b.cut(holes)


def leveling_foot() -> cq.Workplane:
    stud = cq.Workplane("XY").circle(2.5).extrude(FOOT_H + 6)
    pad = cq.Workplane("XY").circle(15).extrude(6).union(cq.Workplane("XY").polygon(6, 9.2).extrude(FOOT_H - 1))
    return pad.union(stud)


# ---------------------------------------------------------------- fasteners
def shoulder_screw() -> cq.Workplane:
    """M3 thread, 4 mm x 8 mm shoulder (ISO 7379 style). Head face (under the head) at z = 0,
    shoulder along -z, thread beyond it."""
    head = cq.Workplane("XY").circle(SHOULDER_HEAD_D / 2).extrude(SHOULDER_HEAD_H)
    head = head.cut(cq.Workplane("XY").polygon(6, 2.5 / math.cos(math.pi / 6)).extrude(2.0).translate((0, 0, SHOULDER_HEAD_H - 2.0)))
    sh = cq.Workplane("XY").circle(SHOULDER_D / 2).extrude(-SHOULDER_L)
    th = cq.Workplane("XY").circle(1.5).extrude(-5.5).translate((0, 0, -SHOULDER_L))
    return head.union(sh).union(th)


def locknut(m: float = 3.0) -> cq.Workplane:
    """Nylon-insert locknut (DIN 985), bearing face at z = 0, crown toward +z."""
    af, h = {3.0: (5.5, 4.0), 5.0: (8.0, 5.0), 6.35: (11.1, 7.1), 10.0: (16.0, 10.0)}[m]
    nut = cq.Workplane("XY").polygon(6, af / math.cos(math.pi / 6)).extrude(h * 0.7)
    crown = cq.Workplane("XY").circle(af / 2 * 0.95).extrude(h * 0.3).translate((0, 0, h * 0.7))
    return nut.union(crown).cut(cq.Workplane("XY").circle(m / 2).extrude(h + 1))


def thrust_washer() -> cq.Workplane:
    """McMaster 95630A630 PTFE washer, 4.3 x 9 x 0.8."""
    return cq.Workplane("XY").circle(4.5).circle(2.15).extrude(WASHER_T)


def sleeve_bearing() -> cq.Workplane:
    """McMaster 6659K65 flanged bronze bushing, 4 ID x 7.02 OD x 6, flange 10 x 1.5:
    flange's outer face at z = +1.5 ... seat face at z = 0, sleeve along -z."""
    fl = cq.Workplane("XY").circle(5.0).circle(2.0).extrude(1.5)
    sl = cq.Workplane("XY").circle(3.51).circle(2.0).extrude(-4.5)
    return fl.union(sl)


def thumb_screw() -> cq.Workplane:
    """M5 x 16 knurled-head thumb screw: underside of the head at z = 0, shank along -z.
    Its tip is the module's hinge pin in Sam's knuckle."""
    head = cq.Workplane("XY").polygon(24, THUMB_HEAD[0]).extrude(THUMB_HEAD[1])
    return head.union(cq.Workplane("XY").circle(HINGE_PIN_D / 2).extrude(-THUMB_L).edges("<Z").chamfer(0.5))


def heat_set_insert_m5() -> cq.Workplane:
    """M5 brass heat-set insert, short (5.8 mm), 6.4 OD; top face at z = 0, body along -z."""
    return cq.Workplane("XY").circle(INSERT_D / 2).circle(2.5).extrude(-5.5)


def screw(d: float, length: float, head_d: float, head_h: float) -> cq.Workplane:
    """Generic socket/button head screw: underside of the head at z = 0, shank along -z."""
    return cq.Workplane("XY").circle(head_d / 2).extrude(head_h).union(cq.Workplane("XY").circle(d / 2).extrude(-length))


def magnet() -> cq.Workplane:
    return cq.Workplane("XY").circle(MAGNET_D / 2).extrude(MAGNET_H)


def hall_switch() -> cq.Workplane:
    """A3144-style hall switch on a small printed holder (envelope)."""
    return cq.Workplane("XY").rect(12.0, 16.0).extrude(6.0).union(cq.Workplane("XY").rect(4.0, 3.0).extrude(7.5))


# ---------------------------------------------------------------- printed: gondola
def gondola() -> cq.Workplane:
    """One printed PETG gondola, in its own frame: origin on the pivot axis at the
    front chain's centre plane, x toward the back chain, z up (it always hangs upright).
    Two end plates with pivot bosses, two side rails, a floor round the station window,
    hinge lugs for Sam's plate and a saddle under the auger's cap end."""
    L = CHAIN_L
    zb = GON_Z0 + 2.0                          # -46: printed parts stop 2 mm inside the envelope
    end_poly = [(-GON_W / 2, zb), (GON_W / 2, zb), (GON_W / 2, -24.0), (9.0, -3.0), (-9.0, -3.0), (-GON_W / 2, -24.0)]

    def end_plate(x0: float) -> cq.Workplane:
        p = cq.Workplane("YZ").polyline(end_poly).close().extrude(END_T)
        boss = cq.Workplane("YZ").circle(9.0).extrude(END_T)
        e = p.union(boss).translate((x0, 0, 0))
        return e.cut(cq.Workplane("YZ").circle(BUSHING_OD / 2).extrude(END_T + 2).translate((x0 - 1, 0, 0)))

    g = end_plate(END_X0).union(end_plate(L - END_X1))
    # side rails, outside Sam's plate (|y| <= 27.02)
    rail_y0 = 27.6
    for sgn in (-1, 1):
        rail = cq.Workplane("XY").box(L - 2 * END_X1 + 2.0, GON_W / 2 - rail_y0, -24.0 - zb, centered=False)
        g = g.union(rail.translate((END_X1 - 1.0, rail_y0 if sgn > 0 else -GON_W / 2, zb)))
    # INDEX magnet pocket under the -y rail (the station's hall switch reads it); HOME gets a second one on gondola 1
    g = g.cut(cq.Workplane("XY").center(HALL_X[0], -(GON_W / 2 + rail_y0) / 2).circle(MAGNET_D / 2 + 0.1)
              .extrude(MAGNET_H + 0.2).translate((0, 0, zb - 0.01)))
    # floor under Sam's plate: two strips beside the window and a back strip, open at the front (outlet)
    fz0, fz1 = HINGE_Z - SAM_DROP - FLOOR_T, HINGE_Z - SAM_DROP
    for sgn in (-1, 1):
        strip = cq.Workplane("XY").box(WIN_X[1] + 6.0 - (HINGE_X - 6.0), GON_W / 2 - WIN_Y, FLOOR_T, centered=False)
        g = g.union(strip.translate((HINGE_X - 6.0, WIN_Y if sgn > 0 else -GON_W / 2, fz0)))
    back = cq.Workplane("XY").box(10.0, GON_W, FLOOR_T, centered=False).translate((WIN_X[1], -GON_W / 2, fz0))
    g = g.union(back)
    # under-floor ribs from the floor down to the rails' bottom, beside the window
    for sgn in (-1, 1):
        rib = cq.Workplane("XY").box(WIN_X[1] + 6.0 - (HINGE_X - 6.0), 3.0, fz0 - zb, centered=False)
        g = g.union(rib.translate((HINGE_X - 6.0, (WIN_Y if sgn > 0 else -WIN_Y - 3.0), zb)))
    # hinge lugs (Sam's knuckle spans +-25), hole for the quick-release pin
    for sgn in (-1, 1):
        lug = (cq.Workplane("XZ").center(HINGE_X, HINGE_Z).circle(7.0).extrude(GON_W / 2 - LUG_IN)
               .union(cq.Workplane("XY").box(14.0, GON_W / 2 - LUG_IN, HINGE_Z - zb, centered=False)
                      .translate((HINGE_X - 7.0, 0, zb)).translate((0, -(GON_W / 2 - LUG_IN), 0))))
        lug = lug.translate((0, GON_W / 2, 0)) if sgn > 0 else lug.mirror("XZ").translate((0, -GON_W / 2, 0))
        g = g.union(lug)
    g = g.cut(cq.Workplane("XZ").center(HINGE_X, HINGE_Z).circle(INSERT_D / 2).extrude(GON_W + 2, both=True)
              .cut(cq.Workplane("XY").box(30, 2 * LUG_IN, 30).translate((HINGE_X, 0, HINGE_Z))))
    # saddle under the auger near the cap end: a cross bar with a V seat 0.6 mm below the tube
    sx = HINGE_X + SADDLE_XS
    tube_bot = HINGE_Z - AUGER_R_TUBE
    bar = cq.Workplane("XY").box(10.0, GON_W, tube_bot - 0.6 - zb, centered=False).translate((sx - 5.0, -GON_W / 2, zb))
    vee = (cq.Workplane("YZ").polyline([(-18, tube_bot - 0.6 + 12), (0, tube_bot - 0.6), (18, tube_bot - 0.6 + 12)])
           .close().extrude(10.0).translate((sx - 5.0, 0, 0)))
    g = g.union(bar).union(vee.intersect(cq.Workplane("XY").box(10, GON_W, 40, centered=False).translate((sx - 5.0, -GON_W / 2, tube_bot - 0.6))))
    g = g.cut(cq.Workplane("YZ").center(0, HINGE_Z).circle(AUGER_R_TUBE + 0.6).extrude(12).translate((sx - 6.0, 0, 0)))
    return g


# ---------------------------------------------------------------- printed: station
def station_yoke() -> cq.Workplane:
    """Printed yoke bolted under Sam's electronics carriage: a clevis for the actuator's
    rod end (pin along y) and a guide tongue at y = TONGUE_Y that rides the approach fork.
    Frame: Sam's studio frame (the carriage's underside is at his z = -60.75)."""
    zt = -60.75
    plate = cq.Workplane("XY").box(44.0, 36.0, 5.0, centered=False).translate((YOKE_X - 22.0, -17.0, zt - 5.0))
    cheeks = None
    for y0 in (-10.5, 5.5):
        c = (cq.Workplane("XZ").center(YOKE_X, YOKE_Z).circle(6.0).extrude(-5.0)
             .union(cq.Workplane("XY").box(12.0, 5.0, zt - 5.0 - YOKE_Z, centered=False).translate((YOKE_X - 6.0, 0, YOKE_Z))))
        c = c.translate((0, y0, 0))
        cheeks = c if cheeks is None else cheeks.union(c)
    y = plate.union(cheeks)
    y = y.cut(cq.Workplane("XZ").center(YOKE_X, YOKE_Z).circle(ACT_CLEVIS_D / 2 + 0.1).extrude(40, both=True))
    tongue = cq.Workplane("XY").box(30.0, 6.0, 25.0, centered=False).translate((TONGUE_X - 15.0, TONGUE_Y - 3.0, zt - 25.0))
    return y.union(tongue)


def approach_fork() -> cq.Workplane:
    """Fixed printed fork that keeps the electronics carriage square while the actuator
    lifts it to the module (the first DOCK_EXT of the stroke); the tongue leaves its top
    as the carriage docks, so it is free to tilt. Frame: slot centred on the origin
    (x along the auger, y across), bottom at z = 0. It sits beside the actuator's swing plane."""
    h = FORK_H
    body = cq.Workplane("XY").box(50.0, 19.0, h, centered=False).translate((-25.0, -4.5, 0))
    slot = cq.Workplane("XY").box(31.0, 6.6, h + 2, centered=False).translate((-15.5, -3.3, -1))
    lead = (cq.Workplane("XZ").polyline([(-15.5, h - 6), (-19.0, h + 0.1), (19.0, h + 0.1), (15.5, h - 6)]).close()
            .extrude(3.3, both=True))
    return body.cut(slot).cut(lead)


def vial_funnel() -> cq.Workplane:
    """Printed catch funnel on the vial: 36 mm mouth, 18 mm spout into the vial, mouth cut flat
    at x = FUNNEL x_max (world) so it stays ahead of the docked electronics carriage. Frame:
    vial axis, spout bottom at z = 0."""
    f = FUNNEL
    outer = cq.Solid.makeCone(f["spout_d"] / 2 + 1.6, f["top_d"] / 2 + 1.6, f["h"])
    inner = cq.Solid.makeCone(f["spout_d"] / 2, f["top_d"] / 2, f["h"])
    cone = cq.Workplane("XY").add(outer).cut(cq.Workplane("XY").add(inner))
    clip = cq.Workplane("XY").box(200, 200, 100, centered=(True, True, False)).translate((f["x_max"] - VIAL_X - 100, 0, -1))
    return cone.intersect(clip)


def actuator_p16() -> tuple[cq.Workplane, cq.Workplane]:
    """Actuonix P16-150-22-12-P, modelled from Actuonix's STEP: rear clevis hole on the
    y axis at the origin, rod along +z. Motor/gear block 36 x 20 x 79 (rod axis 10.5 mm
    from one end of the 36), 12 x 12 tube, 9 mm rod, 9 x 9 rod-end plug.
    Returns (body, rod at full retraction; the layout slides the rod by the extension)."""
    block = cq.Workplane("XY").box(36.0, 20.0, 79.0, centered=False).translate((-25.5, -10.0, -4.5))
    tube = cq.Workplane("XY").box(12.0, 12.0, 167.0, centered=False).translate((-6.0, -6.0, 23.4))
    body = block.union(tube).cut(cq.Workplane("XZ").circle(ACT_CLEVIS_D / 2).extrude(20, both=True))
    rod = cq.Workplane("XY").circle(4.5).extrude(43.4).translate((0, 0, 150.0))
    plug = cq.Workplane("XY").box(9.0, 9.0, 14.0, centered=False).translate((-4.5, -4.5, ACT_RETRACTED - 10.0))
    rod = rod.union(plug).cut(cq.Workplane("XZ").center(0, ACT_RETRACTED).circle(ACT_CLEVIS_D / 2).extrude(10, both=True))
    return body, rod


def clevis_bracket() -> cq.Workplane:
    """Base clevis for the actuator's 20 mm block (printed PETG or the Actuonix bracket):
    two 5 mm cheeks 21 mm apart on a foot, pin along y at the frame origin."""
    foot = cq.Workplane("XY").box(44.0, 40.0, 6.0, centered=(True, True, False)).translate((0, 0, -CLEVIS_H))
    cheeks = None
    for y0 in (-15.5, 10.5):
        c = (cq.Workplane("XZ").circle(7.0).extrude(-5.0)
             .union(cq.Workplane("XY").box(14.0, 5.0, CLEVIS_H, centered=(True, False, False)).translate((0, 0, -CLEVIS_H))))
        c = c.translate((0, y0, 0))
        cheeks = c if cheeks is None else cheeks.union(c)
    b = foot.union(cheeks).cut(cq.Workplane("XZ").circle(ACT_CLEVIS_D / 2 + 0.1).extrude(30, both=True))
    return b.cut(cq.Workplane("XY").pushPoints([(-16, 0), (16, 0)]).circle(2.75).extrude(10).translate((0, 0, -CLEVIS_H - 1)))


def vial() -> cq.Workplane:
    """20 mL glass scintillation vial, 28 mm OD x 61 mm, open (cap off). Base at z = 0."""
    v = cq.Workplane("XY").circle(14.0).extrude(VIAL_H)
    return v.cut(cq.Workplane("XY").circle(12.6).extrude(VIAL_H).translate((0, 0, 1.4)))


def load_cell() -> cq.Workplane:
    """100 g bar load cell (TAL221 class): 47.5 x 6 x 6 mm... envelope of the 80 x 12.7 x 12.7 class.
    Fixed end at x = 0, free end toward +x, bottom at z = 0."""
    return cq.Workplane("XY").box(LC_L, 12.7, 12.7, centered=(False, True, False))


def vial_cup() -> cq.Workplane:
    """Printed cup on the load cell's free end that holds the vial."""
    cup = cq.Workplane("XY").circle(17.0).extrude(18.0).cut(cq.Workplane("XY").circle(14.3).extrude(18).translate((0, 0, 3)))
    arm = cq.Workplane("XY").box(40.0, 12.7, 3.0, centered=(False, True, False)).translate((-52.0, 0, 0))
    return cup.union(arm)


def side_plate(back: bool, holes: list[tuple]) -> cq.Workplane:
    """1/4 in 6061 side plate in the YZ plane (thickness along +x from x = 0).
    holes: (kind, y, z, d[, length]) -- 'round' or 'slot' (vertical slot)."""
    y0, y1 = -SIDE_HALF_W, SIDE_HALF_W
    z0, z1 = SIDE_Z
    p = cq.Workplane("YZ").center((y0 + y1) / 2, (z0 + z1) / 2).rect(y1 - y0, z1 - z0).extrude(PLATE_T_SIDE)
    p = p.edges("|X").fillet(8.0)
    for h in holes:
        kind, y, z, d = h[:4]
        if kind == "round":
            p = p.cut(cq.Workplane("YZ").center(y, z).circle(d / 2).extrude(PLATE_T_SIDE + 2).translate((-1, 0, 0)))
        else:
            ln = h[4]
            p = p.cut(cq.Workplane("YZ").center(y, z).slot2D(ln + d, d, 90).extrude(PLATE_T_SIDE + 2).translate((-1, 0, 0)))
    return p


def motor_plate() -> cq.Workplane:
    """1/4 in 6061 motor plate, in the YZ plane, thickness along +x: NEMA 34 pilot and
    bolt square at the centre, four standoff holes at the corners."""
    s = MOTOR_PLATE
    p = cq.Workplane("YZ").rect(s, s).extrude(PLATE_T_SIDE).edges("|X").fillet(6.0)
    p = p.cut(cq.Workplane("YZ").circle(M34_PILOT_D / 2 + 0.3).extrude(10).translate((-1, 0, 0)))
    p = p.cut(cq.Workplane("YZ").rect(M34_BOLT_SQ, M34_BOLT_SQ, forConstruction=True).vertices().circle(M34_HOLE_D / 2 + 0.25)
              .extrude(10).translate((-1, 0, 0)))
    return p.cut(cq.Workplane("YZ").rect(2 * MOTOR_SO[0], 2 * MOTOR_SO[1], forConstruction=True).vertices().circle(3.25).extrude(10).translate((-1, 0, 0)))


def standoff(length: float) -> cq.Workplane:
    """Round aluminium standoff, 10 mm OD, M6 both ends, along +z."""
    return cq.Workplane("XY").circle(5.0).extrude(length).cut(cq.Workplane("XY").circle(2.5).extrude(length))


def hold_down_strip() -> cq.Workplane:
    """UHMW-PE bar 10 x 12 x 120 mm over the chain's bottom run (centred on the chain plane,
    underside at z = 0, along y), two M4 holes for the brackets."""
    sx, sy, sz = HOLD_STRIP
    b = cq.Workplane("XY").box(sx, sy, sz, centered=(True, True, False))
    return b.cut(cq.Workplane("XZ").pushPoints([(0, sz / 2)]).circle(2.1).extrude(sy, both=True).translate((0, 0, 0))
                 .intersect(cq.Workplane("XY").box(sx + 2, 2 * HOLD_BRACKET_Y + 8, sz, centered=(True, True, False))
                            .cut(cq.Workplane("XY").box(sx + 4, 2 * HOLD_BRACKET_Y - 8, sz + 2, centered=(True, True, False)))))


def hold_down_bracket() -> cq.Workplane:
    """Printed PETG block from the side plate's inner face (x = 0) to the strip (along +x),
    12 wide (y), 9 tall (z, bottom at 0)."""
    L = -SIDE_IN - HOLD_STRIP[0] / 2
    return cq.Workplane("XY").box(L, 12.0, 9.0, centered=(False, True, False))
