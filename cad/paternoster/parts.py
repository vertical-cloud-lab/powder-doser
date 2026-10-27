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

import sys as _sys
_sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "vendor"))
import actuonix  # noqa: E402  (Actuonix's STEP, shared with the other carousel)
import mcmaster  # noqa: E402  (McMaster's own STEPs, placed in these builders' frames)

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
    pl = PIN_LEN if clip else PIN_LEN_RC35          # SA-1 connecting link (McMaster STEP) / plain riveted link (Nitro L)
    pins = (cq.Workplane("XY").pushPoints([(-P / 2, 0), (P / 2, 0)]).circle(PIN_D / 2)
            .extrude(pl).translate((0, 0, -pl / 2)))
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
    from the pitch line, opened to 3.4 mm for the pivot screw's M3 thread.
    McMaster 7321K31's own STEP when it is on disk (cad/vendor/mcmaster.py)."""
    real = mcmaster.mcm("7321K31")
    if real is not None:
        return real
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
    Tooth ring centred on z = 0; the ring's inner face (+z) is the flush face. Martin 35BS32 5/8 (catalog data, the
    maker's table that distributors quote): 4.032 in OD, 3.826 in PD, 2 in hub, 7/8 in LTB, 3/16 x 3/32 keyway,
    two set screws, one over the keyway and one at 90 deg (was one)."""
    hub = cq.Workplane("XY").circle(HUB_D / 2).extrude(LTB - TOOTH_W).translate((0, 0, -LTB + TOOTH_W / 2))
    s = _ring32().union(hub)
    s = s.cut(cq.Workplane("XY").circle(bore / 2).extrude(60).translate((0, 0, -30)))
    if keyed:
        s = s.cut(cq.Workplane("XY").center(0, bore / 2).rect(KEYWAY[0], 2 * KEYWAY[1]).extrude(60).translate((0, 0, -30)))
    zs = -LTB + TOOTH_W / 2 + (LTB - TOOTH_W) / 2
    return s.cut(cq.Workplane("XZ").center(0, zs).circle(3.0).extrude(-40)
                 .union(cq.Workplane("YZ").center(0, zs).circle(3.0).extrude(40)))


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
    lobe_r = (b["L"] - b["J"]) / 2               # 8.75: 81 long over the lobes (was 9.0)
    lobes = cq.Workplane("XY").pushPoints([(0, -b["J"] / 2), (0, b["J"] / 2)]).circle(lobe_r).extrude(b["T"])
    hull = (cq.Workplane("XY").polyline([(-lobe_r, -b["J"] / 2), (-b["W"] / 2, -6), (-b["W"] / 2, 6), (-lobe_r, b["J"] / 2),
                                         (lobe_r, b["J"] / 2), (b["W"] / 2, 6), (b["W"] / 2, -6), (lobe_r, -b["J"] / 2)])
            .close().extrude(b["T"]))
    flange = lobes.union(hull).union(cq.Workplane("XY").circle(b["W"] / 2 - 4).extrude(b["T"]))
    front = cq.Workplane("XY").circle(b["DOME_D"] / 2).extrude(b["DOME_OUT"]).edges(">Z").chamfer(4)
    rear = cq.Workplane("XY").circle(b["DOME_D"] / 2).extrude(-b["DOME_IN"]).edges("<Z").chamfer(4)
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
    bearing seat along +z to the inner bearing's face, with the circlip's groove at its end,
    stem along -z (3 mm past the nylock and its washer, chamfered)."""
    seat = cq.Workplane("XY").circle(7.5).extrude(IDLER_AXLE_L + IDLER_CIRCLIP[1]).edges(">Z").chamfer(0.5)
    groove = (cq.Workplane("XY").circle(7.6).circle(IDLER_CIRCLIP[0] / 2).extrude(IDLER_CIRCLIP[1] + 0.1)
              .translate((0, 0, IDLER_AXLE_L)))
    shoulder = cq.Workplane("XY").circle(11.0).extrude(4.0)
    stem = cq.Workplane("XY").circle(5.0).extrude(-(PLATE_T_SIDE + 15.0)).faces("<Z").chamfer(0.8)
    return seat.cut(groove).union(shoulder).union(stem)


def idler_spacer() -> cq.Workplane:
    """Aluminium spacer between the axle's washer shoulder and the outer 6202's inner ring (shop: cut from 3/4 in
    tube and bored to 15.2): z 0 .. length, on the axle."""
    i, o, l = IDLER_SPACER
    return cq.Workplane("XY").circle(o / 2).circle(i / 2).extrude(l)


def idler_circlip() -> cq.Workplane:
    """DIN 471 external retaining ring for a 15 mm shaft, 1.0 thick, in the seat's groove: face on the bearing at
    z = 0, along +z (simplified: a split ring with two lug holes)."""
    r = cq.Workplane("XY").circle(10.4).circle(IDLER_CIRCLIP[0] / 2).extrude(IDLER_CIRCLIP[1])
    return r.cut(cq.Workplane("XY").center(0, 9.0).rect(3.0, 4.0).extrude(3).translate((0, 0, -1)))


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
    """11HS18-0674S on Sam's electronics carriage: 28 mm square, 45 mm body, 22 mm boss, 5 mm x 20 mm shaft.
    Mounting face at z = 0, shaft +z. On the inner face of the carriage's back wall, the shaft ends at the pinion's
    back face."""
    body = cq.Workplane("XY").rect(28, 28).extrude(-45.0).edges("|Z").chamfer(2.5)
    boss = cq.Workplane("XY").circle(11).extrude(1.5)
    # StepperOnline 11HS18-0674S spec (product page, 2026-10-27): 28 x 28, body 45, shaft 5 x 20, D-cut 15 long (added,
    # 0.5 deep on +x); its drawing PDF and STEP need the page's own download (403 to a plain request, STEP needs a login)
    sh = cq.Workplane("XY").circle(2.5).extrude(20.0).cut(cq.Workplane("XY").center(2.5, 0).rect(1.0, 6.0).extrude(15.0)
                                                         .translate((0, 0, 5.0)))
    return body.union(boss).union(sh)


def _spur_outline(z: int, m: float, alpha_deg: float = 20.0, n_inv: int = 7) -> list[tuple[float, float]]:
    """Standard full-depth involute spur gear outline (addendum m, dedendum 1.25 m, zero shift) as a closed polyline,
    a tooth centred on +x. The flank runs radially below the base circle (no undercut detail)."""
    a = math.radians(alpha_deg)
    r, ra, rf = m * z / 2, m * z / 2 + m, m * z / 2 - 1.25 * m
    rb = r * math.cos(a)
    inv = lambda t: math.tan(t) - t  # noqa: E731
    half = math.pi / (2 * z) + inv(a)               # tooth half-angle at the base circle
    rs = [max(rb, rf) + (ra - max(rb, rf)) * i / n_inv for i in range(n_inv + 1)]
    flank = [(rr, half - inv(math.acos(min(1.0, rb / rr)))) for rr in rs]   # (radius, half-angle) up one flank
    pts: list[tuple[float, float]] = []
    for k in range(z):
        c = 2 * math.pi * k / z
        tooth = [(rf, c - half - 0.6 * (math.pi / z - half))] + [(rr, c - th) for rr, th in flank]
        tooth += [(rr, c + th) for rr, th in reversed(flank)] + [(rf, c + half + 0.6 * (math.pi / z - half))]
        pts += [(rr * math.cos(t), rr * math.sin(t)) for rr, t in tooth]
    return pts


def pinion_20t() -> cq.Workplane:
    """Steel 20T module-1 pinion: KHK SS1-20A (S45C, 5 mm H7 bore, 10 mm face) with its 10 mm hub faced off so it
    fits in front of the dock magnet's bracket; bonded to the shaft (Loctite 638). 22 OD, 10 wide. A printed pinion
    is softer and rubs at about mu 0.3, which raises the separating force (cad/gear-mesh). KHK catalog (SS1-20A,
    2026-10-27): bore 5, hub 16 x 10 (faced off here), PD 20, OD 22, face 10, standard full depth, 20 deg: now an
    involute tooth form (was a 20-gon of 21.6 mm). Face toward the motor at z = 0, a tooth on +x."""
    return (cq.Workplane("XY").polyline(_spur_outline(20, 1.0)).close().extrude(10.0)
            .cut(cq.Workplane("XY").circle(2.5).extrude(10)))


def solenoid_412() -> cq.Workplane:
    """Adafruit 412 12 V push-pull solenoid, plunger along +z. Adafruit's drawing (product-files/412/412_C514-B_diagram.PDF,
    TAU0730TM, 2026-10-27): U-frame 17 x 14 across, 29.7 long, plunger 5 mm (brass tip 5 x 10), 51.9 overall, 4.9 mm
    stroke, push end 15.4 out of the frame when energised (20.3 at rest). Was a 15 x 12 x 32 frame and a 4.5 mm plunger.
    The plunger is still drawn 8 mm out (where the layout's SOL_Z puts its tip under the auger tube): the real one
    stands 7.4 mm further out energised, see cad/vendor/AUDIT_other.md."""
    frame = cq.Workplane("XY").rect(17.0, 14.0).extrude(-29.7)
    plunger = cq.Workplane("XY").circle(2.5).extrude(8.0)
    return frame.union(plunger)


# ---------------------------------------------------------------- frame
def extrusion_2020(length: float) -> cq.Workplane:
    """80/20 20-2020 along +z, from 80/20's profile drawing (8020.net/20-2020, gallery image 2, 2026-10-27): 20.00
    square, slot opening 5.26, lips 1.50, slot 11.99 wide under the lips, narrowing at 45 deg to the 7.32 core
    (6.34 from a face), 4.19 bore through. Was a Misumi-style slot-6 profile (6.2 opening, 1.8 lips, 11.0 x 6.1 slot,
    4.2 bore). Note 80/20's 5.26 opening is narrower than a generic 2020 slot 6 (cad/vendor/AUDIT_other.md)."""
    s, op, lip, w, depth, web, bore = 20.0, 5.26, 1.50, 11.99, 6.34, 1.50, 4.19
    h, g = s / 2, web / math.sqrt(2)            # cavity walls run parallel to the 45 deg corner webs, a web apart
    pts = [(h + 0.01, op / 2), (h - lip, op / 2), (h - lip, w / 2), (w / 2 + g, w / 2), (h - depth, h - depth - g),
           (h - depth, -(h - depth - g)), (w / 2 + g, -w / 2), (h - lip, -w / 2), (h - lip, -op / 2), (h + 0.01, -op / 2)]
    slot = cq.Workplane("XY").polyline(pts).close().extrude(length)
    prof = cq.Workplane("XY").rect(s, s).extrude(length)
    for ang in (0, 90, 180, 270):
        prof = prof.cut(slot.rotate((0, 0, 0), (0, 0, 1), ang))
    return prof.cut(cq.Workplane("XY").circle(bore / 2).extrude(length))


def corner_bracket() -> cq.Workplane:
    """80/20 14059, 2-hole 18 mm slotted inside corner bracket with dual support (8020.net/14059 table, 2026-10-27):
    A = B = K = 18 (legs and width), F 3.0 legs, H 2.0 side walls, slots J 5.3 wide x G 7.0 long centred D 10.5 from
    the corner. Legs along +x and +z, back faces on x = 0 and z = 0, centred on y. Was a solid 20 x 20 x 18 wedge, 3.5
    legs, 5.5 holes 12 from the corner."""
    a, t, w, sw = 18.0, 3.0, 18.0, 2.0
    b = cq.Workplane("XZ").polyline([(0, 0), (a, 0), (a, t), (t, a), (0, a)]).close().extrude(w / 2, both=True)
    b = b.cut(cq.Workplane("XY").box(a, w - 2 * sw, a, centered=(False, True, False)).translate((t, 0, t)))
    slot_x = cq.Workplane("XY").center(10.5, 0).slot2D(7.0, 5.3, 0).extrude(t + 2).translate((0, 0, -1))
    slot_z = cq.Workplane("YZ").center(0, 10.5).slot2D(7.0, 5.3, 90).extrude(t + 2).translate((-1, 0, 0))
    return b.cut(slot_x).cut(slot_z)


def leveling_foot() -> cq.Workplane:
    """TNUTZ LF-020-A: M6 x 40 stud on a dia 10 ball end in a dia 20 black nylon base, with a hex nut (TNUTZ product page,
    2026-10-27; the base's 9 mm height and taper are read off its photo, cad/vendor/AUDIT_other.md). Pad on z = 0, stud
    up through a jam nut under the rail into the rail's T-nut: the 40 mm stud is cut to FOOT_H + 6 (a 2020 slot is
    about 6 mm deep). Was an M5 stud on a dia 30 pad."""
    pad = cq.Workplane("XY").add(cq.Solid.makeCone(10.0, 7.5, 9.0))
    ball = cq.Workplane("XY").sphere(5.0).translate((0, 0, 9.0))
    stud = cq.Workplane("XY").circle(3.0).extrude(FOOT_H + 6)
    nut = cq.Workplane("XY").polygon(6, 10.0 / math.cos(math.pi / 6)).extrude(5.0).translate((0, 0, FOOT_H - 5.2))
    return pad.union(ball).union(stud).union(nut)


# ---------------------------------------------------------------- fasteners
def shoulder_screw() -> cq.Workplane:
    """McMaster 90265A121: 4 mm x 10 mm shoulder, M3 x 5 thread, 6 x 3 head. Head face (under the head) at z = 0,
    shoulder along -z, thread beyond it. McMaster's STEP when on disk."""
    real = mcmaster.mcm("90265A121")
    if real is not None:
        return real
    head = cq.Workplane("XY").circle(SHOULDER_HEAD_D / 2).extrude(SHOULDER_HEAD_H)
    head = head.cut(cq.Workplane("XY").polygon(6, 2.5 / math.cos(math.pi / 6)).extrude(2.0).translate((0, 0, SHOULDER_HEAD_H - 2.0)))
    sh = cq.Workplane("XY").circle(SHOULDER_D / 2).extrude(-SHOULDER_L)
    th = cq.Workplane("XY").circle(1.5).extrude(-5.5).translate((0, 0, -SHOULDER_L))
    return head.union(sh).union(th)


def locknut(m: float = 3.0) -> cq.Workplane:
    """Nylon-insert locknut (DIN 985), bearing face at z = 0, crown toward +z. McMaster's STEP for the M3 (93625A100),
    M5 (93625A200) and 1/4-20 (95615A120) when on disk."""
    real = mcmaster.mcm({3.0: "93625A100", 5.0: "93625A200", 6.35: "95615A120"}.get(m, ""))
    if real is not None:
        return real
    af, h = {3.0: (5.5, 4.0), 5.0: (8.0, 5.0), 6.35: (11.1, 7.1), 10.0: (16.0, 10.0)}[m]
    nut = cq.Workplane("XY").polygon(6, af / math.cos(math.pi / 6)).extrude(h * 0.7)
    crown = cq.Workplane("XY").circle(af / 2 * 0.95).extrude(h * 0.3).translate((0, 0, h * 0.7))
    return nut.union(crown).cut(cq.Workplane("XY").circle(m / 2).extrude(h + 1))


def thrust_washer() -> cq.Workplane:
    """McMaster 95630A630 PTFE washer, 4.3 x 9 x 0.8 (McMaster's STEP when on disk)."""
    real = mcmaster.mcm("95630A630")
    if real is not None:
        return real
    return cq.Workplane("XY").circle(4.5).circle(2.15).extrude(WASHER_T)


def sleeve_bearing() -> cq.Workplane:
    """McMaster 6659K65 flanged bronze bushing, 4 ID x 7.02 OD x 6, flange 10 x 1.5:
    flange's outer face at z = +1.5 ... seat face at z = 0, sleeve along -z. McMaster's STEP when on disk."""
    real = mcmaster.mcm("6659K65")
    if real is not None:
        return real
    fl = cq.Workplane("XY").circle(5.0).circle(2.0).extrude(1.5)
    sl = cq.Workplane("XY").circle(3.51).circle(2.0).extrude(-4.5)
    return fl.union(sl)


def thumb_screw() -> cq.Workplane:
    """M5 x 16 knurled-head thumb screw: underside of the head at z = 0, shank along -z.
    Its tip is the module's hinge pin in Sam's knuckle. McMaster 92545A179's STEP when on disk."""
    real = mcmaster.mcm("92545A179")
    if real is not None:
        return real
    head = cq.Workplane("XY").polygon(24, THUMB_HEAD[0]).extrude(THUMB_HEAD[1])
    return head.union(cq.Workplane("XY").circle(HINGE_PIN_D / 2).extrude(-THUMB_L).edges("<Z").chamfer(0.5))


def heat_set_insert_m5() -> cq.Workplane:
    """M5 brass heat-set insert, McMaster 94459A774 (5.7 long, 7.1 knurl OD into a 6.4 hole); top face at z = 0, body
    along -z. McMaster's STEP when on disk; the stand-in is the hole it melts into."""
    real = mcmaster.mcm("94459A774")
    if real is not None:
        return real
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
    # saddle under the auger near the cap end: a cross bar with a seat 0.6 mm below the tube. The seat's cheeks
    # (|y| 12-18) stand on the bar: as a V (apex down) they started 8 mm up in mid-air and would not print unsupported
    sx = HINGE_X + SADDLE_XS
    tube_bot = HINGE_Z - AUGER_R_TUBE
    bar = cq.Workplane("XY").box(10.0, GON_W, tube_bot - 0.6 - zb, centered=False).translate((sx - 5.0, -GON_W / 2, zb))
    vee = (cq.Workplane("YZ").polyline([(-18, tube_bot - 0.6 + 12), (-18, tube_bot - 0.6), (18, tube_bot - 0.6), (18, tube_bot - 0.6 + 12)])
           .close().extrude(10.0).translate((sx - 5.0, 0, 0)))
    g = g.union(bar).union(vee.intersect(cq.Workplane("XY").box(10, GON_W, 40, centered=False).translate((sx - 5.0, -GON_W / 2, tube_bot - 0.6))))
    g = g.cut(cq.Workplane("YZ").center(0, HINGE_Z).circle(AUGER_R_TUBE + 0.6).extrude(12).translate((sx - 6.0, 0, 0)))
    return g


# ---------------------------------------------------------------- station: dock magnet, U-yoke, locating pins
# The same station as chain carousel v2 (cad/chain-carousel-v2/parts.py), all in Sam's studio frame.
def dock_magnet() -> cq.Workplane:
    """Adafruit 3872 holding electromagnet P20/15: face up at z = 0, body along -z. Adafruit's diagram
    (cdn-shop.adafruit.com/product-files/3872/3872_diagram.png, 2026-10-27): 20 dia x 15, an 8 mm centre pole in the
    face, an M4 x 10 tapped hole in the back's centre; leads out of the back beside it. (Was: a ring mark at 8.8-12.8
    and the leads from the centre.)"""
    body = cq.Workplane("XY").circle(DOCK_MAG_D / 2).extrude(-DOCK_MAG_H)
    epoxy = cq.Workplane("XY").circle(8.5).circle(4.0).extrude(-0.3)            # coil's potting between the pole and the shell
    tap = cq.Workplane("XY").circle(3.3 / 2).extrude(10.0).translate((0, 0, -DOCK_MAG_H))   # M4 x 10 (tap drill 3.3)
    leads = cq.Workplane("XY").pushPoints([(-1.5, 6.0), (1.5, 6.0)]).circle(0.6).extrude(-8).translate((0, 0, -DOCK_MAG_H))
    return body.cut(epoxy).cut(tap).union(leads)


def magnet_bracket() -> cq.Workplane:
    """Printed PETG bracket for the dock magnet, Sam's frame (carriage as drawn): a foot on the carriage's back face
    (x 73.33) on the NEMA 11's two upper M2.5 screws, two arms back beside the pinion at |y| 12-18, and a cup round the
    magnet at (x 99.5, y 0), open on the pinion side; the magnet is bonded in."""
    x0, t = 73.33, 3.0
    mx, my = DOCK_MAG_XY
    zfoot = -19.9
    ztop = DOCK_MAG_FACE_Z - 0.3
    zbot = DOCK_MAG_FACE_Z - DOCK_MAG_H - 2.0
    foot = cq.Workplane("XY").box(t, 36.0, zfoot - (-26.5), centered=False).translate((x0, -18.0, -26.5))
    foot = foot.cut(cq.Workplane("YZ").pushPoints([(-11.5, -21.5), (11.5, -21.5)]).circle(1.4).extrude(t + 2).translate((x0 - 1, 0, 0)))
    arms = None
    for s in (-1, 1):
        a = cq.Workplane("XY").box(mx + DOCK_MAG_D / 2 + 2.0 - x0, 6.0, ztop - zbot, centered=False).translate((x0, 12.0 if s > 0 else -18.0, zbot))
        arms = a if arms is None else arms.union(a)
    cup = cq.Workplane("XY").circle(DOCK_MAG_D / 2 + 2.0).extrude(ztop - zbot).translate((mx, my, zbot))
    b = foot.union(arms).union(cup)
    b = b.cut(cq.Workplane("XY").circle(DOCK_MAG_D / 2 + 0.1).extrude(ztop - zbot + 5).translate((mx, my, zbot + 2.0)))
    return b.cut(cq.Workplane("XY").box(89.5 - 76.5, 24.0, 40.0, centered=False).translate((76.5, -12.0, zbot - 5.0)))


def armature_tab() -> cq.Workplane:
    """Low-carbon steel armature, 2 mm, laser cut, Sam's frame: top face on the plate's underside (z -18), x 89-111,
    |y| <= 14; two countersunk M3 holes into heat-set inserts in the plate's back strip."""
    x0, x1 = ARMATURE_X
    t = cq.Workplane("XY").box(x1 - x0, 2 * ARMATURE_HW, ARMATURE_T, centered=False).translate((x0, -ARMATURE_HW, -18.0 - ARMATURE_T))
    t = t.edges("|Z").fillet(2.0)
    for x, y in ARMATURE_SCREWS:
        t = t.cut(cq.Workplane("XY").center(x, y).circle(1.7).extrude(5).translate((0, 0, -21)))
        t = t.cut(cq.Solid.makeCone(3.0, 1.6, 1.4, cq.Vector(x, y, -18.0 - ARMATURE_T), cq.Vector(0, 0, 1)))
    return t


def uyoke_base() -> cq.Workplane:
    """Printed crossbar of the U-yoke on the P16's rod end, yoke frame: origin on the stub-pin axis, z along the
    actuator (toward the carriage). The P16's rod end (a 9 x 6 tab) goes into a fitted slot and a 4 mm dowel through its hole
    makes it rigid; the steel arms bolt to its sides; the approach-guide tongue hangs under it at y = TONGUE_Y."""
    zr = -UFORK_L
    hw = UFORK_Y[0]
    b = cq.Workplane("XY").box(20.0, 2 * hw, 14.0, centered=(True, True, False)).translate((0, 0, zr - 6.0))
    # socket for the P16's real rod end (datasheet + Actuonix STEP): the dia 8.94 rod tube and the rod end's dia 9 x 1 mm
    # collar sit in a dia 9.3 counterbore (collar face 3 mm below the hole), and the 9 x 6 tab (hole at zr, tip 4 mm
    # above) fits a 9.3 x 6.3 slot, so it can't rock (the old 9.3 mm square socket fitted a 9 x 9 plug the P16 doesn't have)
    b = b.cut(cq.Workplane("XY").circle(4.65).extrude(3.11).translate((0, 0, zr - 6.01)))
    b = b.cut(cq.Workplane("XY").box(9.3, 6.3, 7.2, centered=(True, True, False)).translate((0, 0, zr - 2.9)))
    b = b.cut(cq.Workplane("XZ").center(0, zr).circle(1.98).extrude(30, both=True))   # 4 mm dowel, light press
    for x in (-5.0, 5.0):
        b = b.cut(cq.Workplane("XZ").center(x, zr + 4.0).circle(2.0).extrude(30, both=True))
    tongue = cq.Workplane("XY").box(30.0, 6.0, 25.0, centered=False).translate((-15.0, TONGUE_Y - 3.0, zr - 6.0 - 25.0))
    return b.union(tongue)


def yoke_pin() -> cq.Workplane:
    """McMaster 91595A128: hardened steel dowel pin, 4 mm x 38 mm (m6, read 2026-10-27). Pressed through the U-yoke
    crossbar and the P16 rod end's dia 4.25 hole; the two steel arms cover both ends, so it can't walk out (an M4 bolt
    there had no room for its head or nut: the arms sit flat on the crossbar's sides). Yoke frame: along y, centred
    on the origin. McMaster's STEP when on disk."""
    real = mcmaster.mcm("91595A128")
    if real is not None:
        return real
    return cq.Workplane("XZ").circle(2.0).extrude(19.0, both=True).edges().chamfer(0.4)


def uyoke_arm() -> cq.Workplane:
    """2 mm steel arm of the U-yoke (laser cut), yoke frame, at y in [0, 2] (placed at |y| 19.5-21.5): a 4.1 mm hole
    for the stub pin at the origin, R6 end, two 3.4 mm holes into the crossbar."""
    zr = -UFORK_L
    t = UFORK_Y[1] - UFORK_Y[0]
    prof = cq.Workplane("XZ").moveTo(-6.0, 0).lineTo(-10.0, zr - 4.0).lineTo(10.0, zr - 4.0).lineTo(6.0, 0).close()
    arm = prof.extrude(-t).union(cq.Workplane("XZ").circle(6.0).extrude(-t))
    arm = arm.cut(cq.Workplane("XZ").circle(2.05).extrude(-t - 1))
    for x in (-5.0, 5.0):
        arm = arm.cut(cq.Workplane("XZ").center(x, zr + 4.0).circle(1.7).extrude(-t - 1))
    return arm


def stub_pin() -> cq.Workplane:
    """4 mm stub pin along +y from y = 0 (pressed through the carriage's side post and the printed boss) to 8.0 mm, with a
    DIN 6799-3.2 groove (0.64 wide, dia 3.2) just outside the yoke arm, 0.96 mm from the end. Turned from 4 mm h8 303
    stainless rod: a hardened dowel can't be grooved with HSS, and the old 0.6 mm groove 0.5 mm from the end was
    narrower than DIN 6799 asks and left no wall behind it (cad/shop/README.md)."""
    p = cq.Workplane("XZ").circle(2.0).extrude(-8.0).edges().chamfer(0.3)
    return p.cut(cq.Workplane("XZ").circle(2.1).circle(1.6).extrude(-0.64).translate((0, 6.4, 0)))


def yoke_stop() -> cq.Workplane:
    """Printed stop block on a yoke arm's inner face (yoke frame: origin on the stub-pin axis, arm face at y = 0, block
    toward -y, 1.3 mm thick, outside the carriage's |y| 18). The pin plate's tail rests on it while the carriage hangs
    during the approach (its COM is 20 mm behind the pins); the tilt turns the tail up and away, and nothing on the
    carriage reaches the |y| 18.2-19.5 layer, so the carriage can turn through 92 deg in the yoke."""
    return cq.Workplane("XY").box(6.0, 1.3, 4.0, centered=False).translate((11.0, -1.3, YOKE_STOP_Z))


def pin_boss() -> cq.Workplane:
    """Printed pin plate bonded to the carriage's side post (along +y from y = 0, 1.5 mm thick): a 10 mm boss round the
    stub pin and a tail down and back to (14, -8) from the pin, which rests on the yoke's stop block during the approach."""
    boss = cq.Workplane("XZ").circle(5.0).extrude(-1.5)
    d = (14.0, -8.0)
    ln = math.hypot(*d)
    ang = math.degrees(math.atan2(d[1], d[0]))
    tail = (cq.Workplane("XZ").center(ln / 2, 0).rect(ln, 6.0).extrude(-1.5)
            .union(cq.Workplane("XZ").center(ln, 0).circle(3.0).extrude(-1.5))
            .rotate((0, 0, 0), (0, 1, 0), -ang))
    return boss.union(tail).cut(cq.Workplane("XZ").circle(2.0).extrude(-2.0))


def yoke_stop_m() -> cq.Workplane:
    """The -y arm's stop block: yoke_stop mirrored in y (a turn about z would also swap it to ahead of the pins)."""
    return yoke_stop().mirror("XZ")


def pin_boss_m() -> cq.Workplane:
    """The -y side's pin plate: pin_boss mirrored in y, so its tail also points back and down."""
    return pin_boss().mirror("XZ")


def loc_pin() -> cq.Workplane:
    """Steel dowel locating pin, LOCPIN_D x 8 mm, 1 mm 45 deg cone on top: bottom at z = 0 (5 mm in the rim wall)."""
    real = mcmaster.mcm("91595A150")   # McMaster 4 x 8 mm hardened dowel (52100), both ends rounded
    if real is not None:
        return real
    return cq.Workplane("XY").circle(LOCPIN_D / 2).extrude(5.0 + LOCPIN_PROUD).faces(">Z").chamfer(1.0)


def eclip() -> cq.Workplane:
    """DIN 6799 e-clip on a stub pin's groove: 9 OD, 0.6 thick, open on one side. Face at z = 0, along -z."""
    c = cq.Workplane("XY").circle(ECLIP[0] / 2).circle(1.6).extrude(-ECLIP[1])     # sits in the stub pin's 3.2 mm groove
    return c.cut(cq.Workplane("XY").center(0, -3.5).rect(3.4, 4.0).extrude(-2).translate((0, 0, 0.5)))


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
    """Actuonix P16-150-22-12-P: Actuonix's own STEP (cad/vendor/actuonix.py) when it is on disk, else the same
    envelope from the datasheet drawing. Rear clevis hole on the y axis at the origin, rod along +z: 36 x 20 x 70
    housing from z 4.5 (rod axis 10.5 mm from one end of the 36), rear tab 8 thick, 12 x 12 tube, dia 8.94 rod,
    rod end a 9 x 6 tab (hole 4 mm from its tip). Returns (body, rod at full retraction; the layout slides the rod)."""
    real = actuonix.p16_150()
    return real if real is not None else actuonix.p16_150_standin(ACT_CLEVIS_D, ACT_RETRACTED)


def clevis_bracket() -> cq.Workplane:
    """Printed base clevis for the P16's rear tab (8 mm thick, dia 4.25 hole 4.5 mm behind the housing): two cheeks
    CLEVIS_GAP apart straddle the tab on a foot, pin along y at the frame origin. The cheeks end in R4 round the pin,
    so the 20 mm housing (its face 4.5 mm from the pin) swings over them. A 4 x 16 mm shoulder screw is the pin."""
    t = (SHOULDER_CLEVIS_L - CLEVIS_GAP - 0.2) / 2
    foot = cq.Workplane("XY").box(44.0, 40.0, 6.0, centered=(True, True, False)).translate((0, 0, -CLEVIS_H))
    cheeks = None
    for y0 in (-CLEVIS_GAP / 2 - t, CLEVIS_GAP / 2):
        c = (cq.Workplane("XZ").circle(4.0).extrude(-t)
             .union(cq.Workplane("XY").box(8.0, t, CLEVIS_H, centered=(True, False, False)).translate((0, 0, -CLEVIS_H))))
        c = c.translate((0, y0, 0))
        cheeks = c if cheeks is None else cheeks.union(c)
    web = cq.Workplane("XY").box(8.0, CLEVIS_GAP + 2 * t, CLEVIS_H - 9.0, centered=(True, True, False)).translate((0, 0, -CLEVIS_H))
    b = foot.union(cheeks).union(web).cut(cq.Workplane("XZ").circle(ACT_CLEVIS_D / 2 - 0.05).extrude(30, both=True))
    return b.cut(cq.Workplane("XY").pushPoints([(-16, 0), (16, 0)]).circle(2.75).extrude(10).translate((0, 0, -CLEVIS_H - 1)))


def clevis_shoulder_screw() -> cq.Workplane:
    """McMaster 90265A123: 18-8 shoulder screw, 4 mm x 16 mm shoulder, M3 x 0.5 x 5 mm thread, 6 x 3 mm head (McMaster's
    family table, read 2026-10-27). The P16's base pin through the clevis cheeks and the rear tab. Underside of the head at
    z = 0, shoulder along -z. McMaster's STEP when on disk."""
    real = mcmaster.mcm("90265A123")
    if real is not None:
        return real
    head = cq.Workplane("XY").circle(3.0).extrude(3.0).cut(cq.Workplane("XY").polygon(6, 2.0 / math.cos(math.pi / 6)).extrude(1.5).translate((0, 0, 1.5)))
    sh = cq.Workplane("XY").circle(2.0).extrude(-SHOULDER_CLEVIS_L)
    th = cq.Workplane("XY").circle(1.5).extrude(-5.0).translate((0, 0, -SHOULDER_CLEVIS_L))
    return head.union(sh).union(th)


def vial() -> cq.Workplane:
    """20 mL glass scintillation vial, 28 mm OD x 61 mm, open (cap off). Base at z = 0."""
    v = cq.Workplane("XY").circle(14.0).extrude(VIAL_H)
    return v.cut(cq.Workplane("XY").circle(12.6).extrude(VIAL_H).translate((0, 0, 1.4)))


def load_cell() -> cq.Workplane:
    """SparkFun SEN-14727, TAL221 100 g straight-bar (parallel-beam) load cell, from the TAL221 datasheet (HTC Sensor,
    cdn.sparkfun.com/assets/9/9/a/f/3/TAL221.pdf, 2026-10-27): 47 x 12 x 6 mm (SparkFun: 47 x 12 x 6), two M3 tapped
    holes at the fixed end and two 3.2 mm holes at the free end, 6 mm apart across the bar and 40 mm apart along it,
    and a 20 mm binocular hole through the 12 mm side. Was an 80 x 12.7 x 12.7 block (the TAL220's size). Fixed end at
    x = 0, free end toward +x, bottom at z = 0: the bar sits on a 3.35 mm spacer under its fixed end and carries one on
    its free end, so the stack is still 12.7 tall (the vial cup and post heights) and the beam is clear to bend."""
    L, W, H, sp, e = LC_L, 12.0, 6.0, (12.7 - 6.0) / 2, 3.5
    bar = cq.Workplane("XY").box(L, W, H, centered=(False, True, False)).translate((0, 0, sp))
    bar = bar.cut(cq.Workplane("XZ").pushPoints([(L / 2 - 8.0, sp + H / 2), (L / 2 + 8.0, sp + H / 2)]).circle(2.0)
                  .extrude(W, both=True))
    bar = bar.cut(cq.Workplane("XZ").center(L / 2, sp + H / 2).rect(16.0, 1.6).extrude(W, both=True))
    pads = (cq.Workplane("XY").box(2 * e, W, sp, centered=(False, True, False))
            .union(cq.Workplane("XY").box(2 * e, W, sp, centered=(False, True, False)).translate((L - 2 * e, 0, sp + H))))
    holes = (cq.Workplane("XY").pushPoints([(e, -3.0), (e, 3.0)]).circle(1.25).extrude(20).translate((0, 0, -1))
             .union(cq.Workplane("XY").pushPoints([(L - e, -3.0), (L - e, 3.0)]).circle(1.6).extrude(20).translate((0, 0, -1))))
    return bar.union(pads).cut(holes)


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
