"""Tooth-gap and toothless-sector sketches for the mounting plate's 28T tilt gears (0 Onshape calls).

Used by parts/mounting_plate_servos_above.fs. The gears are text-to-cad's ``lib/gears.py`` spur gear
(PR #176), which matches the lab's Fusion 360 SpurGear add-in: module 1.298 (= OD 38.94 / 30), 28 teeth,
20 deg pressure angle, addendum 1.0 m, dedendum 1.157 m, 0.5 mm root fillets, zero backlash, tooth 0
centred on MP +X. For 28 teeth the base circle (r 17.076) lies above the root circle (r 16.670); the
flank below the base circle would be a radial line, but the 0.5 mm root fillet reaches past the base
circle (it touches the involute at r 17.125), so, as in gears.py, no radial run is left. ``_flank``
below is gears.py's and keeps the radial run for gears that have one.

    python gear_gap_mounting_plate.py                # print both blocks for the .fs
    python gear_gap_mounting_plate.py --check        # fail if the .fs holds other numbers
    python gear_gap_mounting_plate.py --turn 0       # both blocks for another sector turn (0: the Fusion part)

Tooth gap: the gap between tooth 0 (on +X) and tooth 1, cut once and patterned 28 times in Onshape.
fsgen sketches have no splines, so each involute flank is FLANK_ARCS 3-point arcs through involute
points (equal steps in roll angle), within 1 um of the involute (checked below on 200 points per arc).
The flanks run OVERCUT past the tip circle, where a straight line closes the gap.

Toothless sector: the lab's plate has teeth only from TOOTH_SECTOR_START_DEG counter-clockwise through
0 deg to TOOTH_SECTOR_END_DEG (both edges in a tooth gap). The servos-above plate turns that sector by
SECTOR_TURN_DEG = 180 about the hinge (MP +Z); elsewhere the rim is turned down to r = SECTOR_CUT_R, just
under the root circle. As in mounting_plate.py the teeth turn with the sector: the gap is drawn turned by
the turn modulo the tooth pitch, which is 0 for 180 deg (14 pitches), so its block is the same as for 0.
The cut region runs from SECTOR_CUT_R out to a polyline at SECTOR_OUTER_R, which stays clear of the floor
(r >= 33.5 from the hinge axis); the .fs cuts it, like the tooth gaps, through all before the knuckles and
arms exist, so it only touches the gears. The arms, added afterwards, fill the arm band, which keeps the
teeth there that the lab's Fusion sketch left uncut (for 180 deg the band lies inside the toothed sector).

Arcs about the hinge axis: fsgen pins every sketch point within 1 nm of the origin to it and also
dimensions both ends of every arc, so an arc centred exactly on the hinge axis is over-defined (Onshape:
WARNING; fsgen then re-sends the sketch without any dimensions). The sector's turned-down arc is
therefore drawn with its centre HUB_OFFSET (0.1 um) off the axis, on the bisector of its ends so that
both ends stay on r = SECTOR_CUT_R. Each root land (0.41 mm long) is a straight line: 1.3 um from the
root circle at most.
"""
from __future__ import annotations

import math
import re
import sys
from pathlib import Path

TEETH, PRESSURE_ANGLE = 28, 20.0
MODULE = 38.94 / (TEETH + 2)          # 1.298: addendum 1 m, outside diameter 38.94
ADDENDUM, DEDENDUM, ROOT_FILLET = 1.0, 1.157, 0.5
FLANK_ARCS = 3                        # arcs per involute flank
OVERCUT = 0.5                         # flanks run this far past the tip circle
TOOTH_SECTOR_START_DEG = 250.563      # lab plate: teeth CCW from here ...
TOOTH_SECTOR_END_DEG = 97.076         # ... through 0 deg to here
SECTOR_TURN_DEG = 180.0               # servos above the hinge
SECTOR_CUT_R = 16.6355                # toothless rim (root circle r = 16.670)
SECTOR_OUTER_R = 24.0                 # outer polyline of the sector cut
HUB_OFFSET = 1e-4                     # mm, centre of the turned-down arc off the hinge axis (see above)
FS = Path(__file__).resolve().parent / "parts" / "mounting_plate_servos_above.fs"


def _inv(a: float) -> float:
    return math.tan(a) - a


def _flank(module, teeth, alpha, backlash, addendum, dedendum, root_fillet):
    """gears.py's flank of a tooth centred on +X (the +Y side): (rr, ra, fillet, line, pt, r0) where
    ``fillet`` is (root point, mid, flank point) or None, ``line`` the radial run (low, high) or None,
    ``pt(r)`` the flank point at radius r and ``r0`` where the involute part starts."""
    rp = module * teeth / 2.0
    rb = rp * math.cos(alpha)
    ra = rp + addendum * module
    rr = rp - dedendum * module
    psi_b = math.pi / (2 * teeth) - backlash / (4.0 * rp) + _inv(alpha)

    def psi(r: float) -> float:
        return psi_b - _inv(math.acos(min(1.0, rb / r)))

    def pt(r: float) -> tuple[float, float]:
        a = psi_b if r <= rb else psi(r)
        return (r * math.cos(a), r * math.sin(a))

    r_low = max(rb, rr)
    fillet = None
    if root_fillet > 0.0:
        rho, rc = root_fillet, rr + root_fillet

        def centre(r: float) -> tuple[float, float]:
            h = 1e-6
            (x0, y0), (x1, y1) = pt(max(rr, r - h) if r > rb else r), pt(r + h)
            tx, ty = x1 - x0, y1 - y0
            n = math.hypot(tx, ty)
            x, y = pt(r)
            return (x - rho * ty / n, y + rho * tx / n)

        r_t = math.sqrt(rc * rc - rho * rho)
        if r_t > rb or rb <= rr:
            lo, hi = r_low, ra
            for _ in range(80):
                mid = 0.5 * (lo + hi)
                if math.hypot(*centre(mid)) < rc:
                    lo = mid
                else:
                    hi = mid
            r_t = 0.5 * (lo + hi)
        cx, cy = centre(r_t)
        t = pt(r_t)
        k = rr / math.hypot(cx, cy)
        root = (cx * k, cy * k)
        bx, by = (t[0] - cx) + (root[0] - cx), (t[1] - cy) + (root[1] - cy)
        nb = math.hypot(bx, by)
        fillet = (root, (cx + rho * bx / nb, cy + rho * by / nb), t)
        r_low = r_t
    line = (pt(r_low), pt(rb)) if rb > rr and r_low < rb - 1e-9 else None
    return rr, ra, rb, fillet, line, pt, max(r_low, rb)


def _circle(a, b, c):
    (ax, ay), (bx, by), (cx, cy) = a, b, c
    d = 2 * (ax * (by - cy) + bx * (cy - ay) + cx * (ay - by))
    ux = ((ax * ax + ay * ay) * (by - cy) + (bx * bx + by * by) * (cy - ay) + (cx * cx + cy * cy) * (ay - by)) / d
    uy = ((ax * ax + ay * ay) * (cx - bx) + (bx * bx + by * by) * (ax - cx) + (cx * cx + cy * cy) * (bx - ax)) / d
    return ux, uy, math.hypot(ax - ux, ay - uy)


def gap() -> dict:
    rr, ra, rb, fillet, line, pt, r0 = _flank(MODULE, TEETH, math.radians(PRESSURE_ANGLE), 0.0,
                                              ADDENDUM, DEDENDUM, ROOT_FILLET)
    roll = lambda r: math.sqrt(max(0.0, (r / rb) ** 2 - 1))
    at_roll = lambda s: rb * math.sqrt(1 + s * s)
    s0, s1 = roll(r0), roll(ra + OVERCUT)
    # flank arcs of tooth 0's +Y flank, from the tip down (the order the gap outline runs)
    arcs, dev = [], 0.0
    for i in reversed(range(FLANK_ARCS)):
        sa, sb = s0 + (s1 - s0) * i / FLANK_ARCS, s0 + (s1 - s0) * (i + 1) / FLANK_ARCS
        lo, hi = at_roll(sa), at_roll(sb)
        p_lo, p_mid, p_hi = pt(lo), pt(at_roll(0.5 * (sa + sb))), pt(hi)
        ux, uy, R = _circle(p_hi, p_mid, p_lo)
        top = min(hi, ra)   # only the part inside the tip circle matters
        if top > lo:
            dev = max(dev, max(abs(math.hypot(x - ux, y - uy) - R)
                               for x, y in (pt(lo + (top - lo) * k / 200) for k in range(201))))
        arcs.append((p_hi, p_mid, p_lo))
    assert dev < 1.5e-3, dev
    # mirror about the gap centre line (angle pi / N): tooth 1's -Y flank
    phi = math.pi / TEETH
    c2, s2 = math.cos(2 * phi), math.sin(2 * phi)
    mirror = lambda p: (p[0] * c2 + p[1] * s2, p[0] * s2 - p[1] * c2)
    root = fillet[0] if fillet else (line[0] if line else pt(r0))
    land_sagitta = rr * (1 - math.cos(phi - math.atan2(root[1], root[0])))
    return {"arcs": arcs, "line": line, "fillet": fillet, "root": root, "mirror": mirror, "deviation_mm": dev,
            "ra": ra, "rr": rr, "rb": rb, "r0": r0, "land_sagitta_mm": land_sagitta}


def sector(turn_deg: float = SECTOR_TURN_DEG) -> dict:
    """Toothless sector, CCW from a0 to a1: its two sides, outer polyline and turned-down arc."""
    a0 = math.radians(TOOTH_SECTOR_END_DEG + turn_deg)
    span = math.radians((TOOTH_SECTOR_START_DEG - TOOTH_SECTOR_END_DEG) % 360.0)
    a1 = a0 + span
    n = max(2, math.ceil(math.degrees(span) / 40.0))
    assert SECTOR_OUTER_R * math.cos(span / n / 2) > (TEETH / 2 + ADDENDUM) * MODULE + OVERCUT + 0.5
    pol = lambda r, a: (r * math.cos(a), r * math.sin(a))
    outer = [pol(SECTOR_OUTER_R, a0 + span * i / n) for i in range(n + 1)]
    am = a0 + span / 2
    hub = pol(HUB_OFFSET, am)                     # on the bisector of the arc's ends
    r_arc = math.hypot(SECTOR_CUT_R * math.cos(a0) - hub[0], SECTOR_CUT_R * math.sin(a0) - hub[1])
    mid = (hub[0] + r_arc * math.cos(am), hub[1] + r_arc * math.sin(am))
    return {"start": pol(SECTOR_CUT_R, a0), "end": pol(SECTOR_CUT_R, a1), "outer": outer, "mid": mid,
            "a0_deg": math.degrees(a0) % 360, "a1_deg": math.degrees(a1) % 360}


def _vec(p) -> str:
    return f"vector({p[0]:.9f}, {p[1]:.9f}) * mm"


_v = _vec


def _phase(turn_deg: float) -> float:
    """The teeth turn with the sector; the gap pattern repeats every pitch, so only this remainder (rad) shows."""
    r = math.remainder(turn_deg, 360.0 / TEETH)
    return 0.0 if abs(r) < 1e-9 else math.radians(r)


def gap_block(turn_deg: float = SECTOR_TURN_DEG) -> str:
    g = gap()
    phase = _phase(turn_deg)
    cos_ph, sin_ph = math.cos(phase), math.sin(phase)
    _v = lambda p: _vec((p[0] * cos_ph - p[1] * sin_ph, p[0] * sin_ph + p[1] * cos_ph))   # noqa: E731
    m = g["mirror"]
    turned = f", turned {math.degrees(phase):g} deg" if phase else ""
    out = ["    // ---- generated by gear_gap_mounting_plate.py (tooth gap: module 1.298, 28 teeth, 20 deg"
           f"{turned}); do not edit by hand ----"]
    for i, (a, b, c) in enumerate(g["arcs"]):
        out.append(f'    skArc(gapSk, "flankA{i + 1}", {{ "start" : {_v(a)}, "mid" : {_v(b)}, "end" : {_v(c)} }});')
    if g["line"]:
        out.append(f'    skLineSegment(gapSk, "radialA", {{ "start" : {_v(g["line"][1])}, "end" : {_v(g["line"][0])} }});')
    if g["fillet"]:
        t, fm, fr = g["fillet"][2], g["fillet"][1], g["fillet"][0]
        out.append(f'    skArc(gapSk, "filletA", {{ "start" : {_v(t)}, "mid" : {_v(fm)}, "end" : {_v(fr)} }});')
    root = g["root"]
    out.append(f'    skLineSegment(gapSk, "rootLand", {{ "start" : {_v(root)}, "end" : {_v(m(root))} }});')
    if g["fillet"]:
        t, fm, fr = g["fillet"][2], g["fillet"][1], g["fillet"][0]
        out.append(f'    skArc(gapSk, "filletB", {{ "start" : {_v(m(fr))}, "mid" : {_v(m(fm))}, "end" : {_v(m(t))} }});')
    if g["line"]:
        out.append(f'    skLineSegment(gapSk, "radialB", {{ "start" : {_v(m(g["line"][0]))}, "end" : {_v(m(g["line"][1]))} }});')
    for i, (a, b, c) in enumerate(reversed(g["arcs"])):
        out.append(f'    skArc(gapSk, "flankB{i + 1}", {{ "start" : {_v(m(c))}, "mid" : {_v(m(b))}, "end" : {_v(m(a))} }});')
    top = g["arcs"][0][0]
    out.append(f'    skLineSegment(gapSk, "outside", {{ "start" : {_v(m(top))}, "end" : {_v(top)} }});')
    out.append("    // ---- end of generated tooth gap ----")
    return "\n".join(out)


def sector_block(turn_deg: float = SECTOR_TURN_DEG) -> str:
    s = sector(turn_deg)
    pts = ", ".join(_v(p) for p in s["outer"])
    return "\n".join([
        f"    // ---- generated by gear_gap_mounting_plate.py (toothless sector, turned {turn_deg:g} deg: "
        f"{s['a0_deg']:.3f} -> {s['a1_deg']:.3f} deg); do not edit by hand ----",
        f'    skLineSegment(sectorSk, "startSide", {{ "start" : {_v(s["start"])}, "end" : {_v(s["outer"][0])} }});',
        f'    skPolyline(sectorSk, "outside", {{ "points" : [{pts}] }});',
        f'    skLineSegment(sectorSk, "endSide", {{ "start" : {_v(s["outer"][-1])}, "end" : {_v(s["end"])} }});',
        f'    skArc(sectorSk, "turnedRim", {{ "start" : {_v(s["end"])}, "mid" : {_v(s["mid"])}, "end" : {_v(s["start"])} }});',
        "    // ---- end of generated toothless sector ----",
    ])


def _current(src: str, what: str) -> str | None:
    m = re.search(rf"    // ---- generated by gear_gap_mounting_plate\.py \({what}.*?// ---- end of generated {what} ----",
                  src, re.S)
    return m.group(0) if m else None


if __name__ == "__main__":
    turn = SECTOR_TURN_DEG
    if "--turn" in sys.argv:
        turn = float(sys.argv[sys.argv.index("--turn") + 1])
    blocks = {"tooth gap": gap_block(turn), "toothless sector": sector_block(turn)}
    if "--check" in sys.argv:
        src = FS.read_text()
        stale = [k for k, b in blocks.items() if _current(src, k) != b]
        if stale:
            sys.exit(f"{FS.name}: {', '.join(stale)} block(s) out of date; run python {Path(__file__).name} "
                     "and paste them in")
        print(f"{FS.name}: tooth gap and toothless sector blocks are current")
    else:
        print(blocks["tooth gap"])
        print()
        print(blocks["toothless sector"])
    g = gap()
    print(f"// flank arcs vs involute: max {g['deviation_mm'] * 1000:.2f} um ({FLANK_ARCS} arcs per flank); "
          f"root land vs root circle: {g['land_sagitta_mm'] * 1000:.2f} um; root r {g['rr']:.4f}, base r "
          f"{g['rb']:.4f}, tip r {g['ra']:.4f}, involute from r {g['r0']:.4f}"
          + ("" if g["line"] else " (no radial run: the fillet reaches the involute)"), file=sys.stderr)
