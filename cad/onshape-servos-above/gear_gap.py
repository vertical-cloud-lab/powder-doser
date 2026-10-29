"""Tooth-gap sketch block for a spur gear in an fsgen Part Studio script (0 Onshape calls).

The generalisation of tooth_gap.py (the auger's 44T gear) to any module, tooth count and pressure angle;
used for parts/stepper_pinion.fs (module 1, 20 teeth) and parts/servo_pinion.fs (module 1.298, 14 teeth).
The gear is the one text-to-cad's ``lib/gears.py`` (PR #176) builds to match the lab's Fusion 360 SpurGear
add-in: addendum 1.0 m, dedendum 1.157 m, 0.5 mm root fillets, zero backlash, tooth 0 centred on +X. The
gap between tooth 0 and tooth 1 (centred on 180 / N deg) is cut once and patterned N times.

Below about 42 teeth (at 20 deg) the base circle lies above the root circle. As in gears.py, the flank then
runs on from the base circle as a radial line down to the root fillet, which is tangent to that line (or to
the involute, if the tangent point would lie above the base circle, as on the 44T gear).

fsgen sketches have lines, arcs and circles but no splines, so each involute flank is a chain of 3-point
arcs through points of the involute. The split points are placed so that the arcs share the largest
deviation equally, and the chain has the fewest arcs that stay within --tol (default 3 um). One arc is
10 um off for 20 teeth and 13 um for 14 teeth: the involute's curvature has no bound at the base circle.
Two arcs are within 1.6 um and 2.1 um (checked on 400 points per arc). The outermost arc runs on along its
own circle to --overcut past the tip circle, so the cut crosses the tip circle cleanly.

    python gear_gap.py --module 1 --teeth 20                                # print the block
    python gear_gap.py --module 1 --teeth 20 --check parts/stepper_pinion.fs  # fail if the file differs

Every point is in millimetres in the gear plane (sketch x -> world X, sketch y -> world Y).
"""
from __future__ import annotations

import argparse
import math
import re
import sys
from pathlib import Path

GOLDEN = (math.sqrt(5) - 1) / 2


def inv(a: float) -> float:
    return math.tan(a) - a


def circle3(a, b, c) -> tuple[float, float, float]:
    """Centre and radius of the circle through three points."""
    (ax, ay), (bx, by), (cx, cy) = a, b, c
    d = 2 * (ax * (by - cy) + bx * (cy - ay) + cx * (ay - by))
    ux = ((ax * ax + ay * ay) * (by - cy) + (bx * bx + by * by) * (cy - ay) + (cx * cx + cy * cy) * (ay - by)) / d
    uy = ((ax * ax + ay * ay) * (cx - bx) + (bx * bx + by * by) * (ax - cx) + (cx * cx + cy * cy) * (bx - ax)) / d
    return ux, uy, math.hypot(ax - ux, ay - uy)


def golden_min(f, lo: float, hi: float, iters: int = 60) -> tuple[float, float]:
    """(x, f(x)) minimising a unimodal f on [lo, hi]."""
    a, b = lo, hi
    c, d = b - GOLDEN * (b - a), a + GOLDEN * (b - a)
    fc, fd = f(c), f(d)
    for _ in range(iters):
        if fc < fd:
            b, d, fd = d, c, fc
            c = b - GOLDEN * (b - a)
            fc = f(c)
        else:
            a, c, fc = c, d, fd
            d = a + GOLDEN * (b - a)
            fd = f(d)
    return (c, fc) if fc < fd else (d, fd)


class Gear:
    def __init__(self, module: float, teeth: int, pressure_angle: float = 20.0, *, addendum: float = 1.0,
                 dedendum: float = 1.157, root_fillet: float = 0.5, backlash: float = 0.0):
        self.module, self.teeth, self.pressure_angle = module, teeth, pressure_angle
        alpha = math.radians(pressure_angle)
        self.rp = module * teeth / 2
        self.rb = self.rp * math.cos(alpha)
        self.ra = self.rp + addendum * module
        self.rr = self.rp - dedendum * module
        self.rho = root_fillet
        if not self.rr < self.rp < self.ra:
            raise ValueError("root < pitch < outside radius violated")
        self.psi_b = math.pi / (2 * teeth) - backlash / (4 * self.rp) + inv(alpha)
        if self.psi_b - inv(math.acos(self.rb / self.ra)) <= 0:
            raise ValueError("pointed teeth")

    def pt(self, r: float) -> tuple[float, float]:
        """Point of the +Y flank of tooth 0 at radius r (radial line below the base circle)."""
        a = self.psi_b if r <= self.rb else self.psi_b - inv(math.acos(self.rb / r))
        return (r * math.cos(a), r * math.sin(a))

    def roll(self, r: float) -> float:
        return math.sqrt(max(0.0, (r / self.rb) ** 2 - 1))

    def at_roll(self, t: float) -> tuple[float, float]:
        return self.pt(self.rb * math.sqrt(1 + t * t))

    def fillet(self):
        """Root fillet as lib/gears.py solves it: (tangent radius, tangent point, mid, root point)."""
        rho, rc, rb, rr = self.rho, self.rr + self.rho, self.rb, self.rr

        def centre(r: float) -> tuple[float, float]:
            # flank point + rho * unit normal towards the gap (+angle side)
            h = 1e-7
            (x0, y0), (x1, y1) = self.pt(r - h if r > rb else r), self.pt(r + h)
            tx, ty = x1 - x0, y1 - y0
            n = math.hypot(tx, ty)
            x, y = self.pt(r)
            return (x - rho * ty / n, y + rho * tx / n)

        r_t = math.sqrt(rc * rc - rho * rho)          # tangent radius on the radial line
        if r_t > rb or rb <= rr:                      # the tangent point is on the involute
            lo, hi = max(rb, rr), self.ra
            if math.hypot(*centre(lo)) > rc:
                raise ValueError("root fillet does not fit")
            for _ in range(100):
                mid = 0.5 * (lo + hi)
                lo, hi = (mid, hi) if math.hypot(*centre(mid)) < rc else (lo, mid)
            r_t = 0.5 * (lo + hi)
        cx, cy = centre(r_t)
        t = self.pt(r_t)
        k = rr / math.hypot(cx, cy)
        root = (cx * k, cy * k)
        bx, by = (t[0] - cx) + (root[0] - cx), (t[1] - cy) + (root[1] - cy)
        nb = math.hypot(bx, by)
        if math.atan2(root[1], root[0]) >= math.pi / self.teeth:
            raise ValueError("root fillets overlap")
        return r_t, t, (cx + rho * bx / nb, cy + rho * by / nb), root

    # ---- involute flank as a chain of arcs
    def _samples(self, t0: float, t1: float, n: int) -> list[tuple[float, float]]:
        return [self.at_roll(t0 + (t1 - t0) * i / (n - 1)) for i in range(n)]

    def best_arc(self, t0: float, t1: float, n: int = 160) -> tuple[float, float]:
        """Arc through the involute points at rolls t0 and t1 and the one at the roll fraction f between them
        that keeps the largest deviation smallest: (f, deviation in mm)."""
        pts = self._samples(t0, t1, n)
        a, b = pts[0], pts[-1]

        def dev(f: float) -> float:
            ux, uy, R = circle3(a, self.at_roll(t0 + f * (t1 - t0)), b)
            return max(abs(math.hypot(x - ux, y - uy) - R) for x, y in pts)
        return golden_min(dev, 0.02, 0.98, 50)

    def flank_chain(self, t_start: float, arcs: int, sweeps: int = 4) -> tuple[list[float], list[float]]:
        """Roll values of the junctions (t_start .. roll(ra)) and the mid fractions of `arcs` arcs, with
        the junctions moved until neighbouring arcs share the largest deviation."""
        ta = self.roll(self.ra)
        ts = [t_start + (ta - t_start) * (i / arcs) ** 0.8 for i in range(arcs + 1)]  # denser near the base
        for _ in range(sweeps if arcs > 1 else 0):
            for j in range(1, arcs):
                lo, hi = ts[j - 1], ts[j + 1]
                pad = 0.02 * (hi - lo)
                ts[j], _ = golden_min(lambda s: max(self.best_arc(lo, s, 80)[1], self.best_arc(s, hi, 80)[1]),
                                      lo + pad, hi - pad, 40)
        return ts, [self.best_arc(ts[i], ts[i + 1])[0] for i in range(arcs)]


def gap(module: float, teeth: int, pressure_angle: float = 20.0, *, addendum: float = 1.0,
        dedendum: float = 1.157, root_fillet: float = 0.5, backlash: float = 0.0, overcut: float = 0.5,
        tol: float = 0.003, arcs: int | None = None) -> dict:
    g = Gear(module, teeth, pressure_angle, addendum=addendum, dedendum=dedendum, root_fillet=root_fillet,
             backlash=backlash)
    r_t, t_pt, fillet_mid, root = g.fillet()
    radial = None
    if g.rb > g.rr and r_t < g.rb - 1e-9:             # radial run from the fillet up to the base circle
        radial = (g.pt(g.rb), t_pt)
    r0 = max(r_t, g.rb)
    t0 = g.roll(r0)

    # fewest arcs within tol, unless the count is given
    for n in ([arcs] if arcs else range(1, 7)):
        ts, fs = g.flank_chain(t0, n)
        circles = [circle3(g.at_roll(ts[i]), g.at_roll(ts[i] + fs[i] * (ts[i + 1] - ts[i])), g.at_roll(ts[i + 1]))
                   for i in range(n)]
        dev = 0.0                                     # check on 400 points per arc, base (or fillet) to tip
        for i, (ux, uy, R) in enumerate(circles):
            for x, y in g._samples(ts[i], ts[i + 1], 400):
                dev = max(dev, abs(math.hypot(x - ux, y - uy) - R))
        if arcs or dev <= tol:
            break
    else:
        raise ValueError(f"no chain of up to 6 arcs is within {tol * 1000:.1f} um")

    # run the outermost arc on along its circle until it is `overcut` outside the tip circle
    ux, uy, R = circles[-1]
    ang = lambda p: math.atan2(p[1] - uy, p[0] - ux)
    on = lambda a: (ux + R * math.cos(a), uy + R * math.sin(a))
    a_prev, a_tip = ang(g.at_roll(ts[-2])), ang(g.at_roll(ts[-1]))
    step = math.copysign(1e-4, math.remainder(a_tip - a_prev, 2 * math.pi))
    lo = a_tip
    while math.hypot(*on(lo + step)) < g.ra + overcut:
        lo += step
        if abs(lo - a_tip) > 1.0:
            raise ValueError("flank arc does not leave the tip circle")
    hi = lo + step
    for _ in range(80):
        mid = 0.5 * (lo + hi)
        lo, hi = (mid, hi) if math.hypot(*on(mid)) < g.ra + overcut else (lo, mid)
    a_top = 0.5 * (lo + hi)
    top = on(a_top)

    # flank arcs of tooth 0, top down to the base circle: (start, mid, end)
    junctions = [g.at_roll(t) for t in ts]
    flank = []
    for i in reversed(range(len(circles))):
        cx, cy, Ri = circles[i]
        a_lo = math.atan2(junctions[i][1] - cy, junctions[i][0] - cx)
        if i == len(circles) - 1:
            start, a_hi = top, a_top
        else:
            start = junctions[i + 1]
            a_hi = math.atan2(start[1] - cy, start[0] - cx)
        a_mid = a_lo + 0.5 * math.remainder(a_hi - a_lo, 2 * math.pi)
        flank.append((start, (cx + Ri * math.cos(a_mid), cy + Ri * math.sin(a_mid)), junctions[i]))

    # mirror about the gap centre line (angle pi / N)
    phi = math.pi / teeth
    c2, s2 = math.cos(2 * phi), math.sin(2 * phi)
    mirror = lambda p: (p[0] * c2 + p[1] * s2, p[0] * s2 - p[1] * c2)
    root_mid = (g.rr * math.cos(phi), g.rr * math.sin(phi))
    # the closing line must stay outside the tip circle, or a sliver of every tip would be left uncut
    m_top = mirror(top)
    chord_r = abs(top[0] * m_top[1] - top[1] * m_top[0]) / math.hypot(top[0] - m_top[0], top[1] - m_top[1])
    if chord_r <= g.ra + 0.05:
        raise ValueError("closing line cuts into the tip circle; increase the overcut")
    return {"gear": g, "flank": flank, "radial": radial, "fillet": (t_pt, fillet_mid, root),
            "root": (root, root_mid, mirror(root)), "mirror": mirror, "deviation_mm": dev, "r_t": r_t,
            "top": top, "chord_r": chord_r}


def block(d: dict, sketch: str = "gapSk") -> str:
    g, m = d["gear"], d["mirror"]
    v = lambda p: f"vector({p[0]:.9f}, {p[1]:.9f}) * mm"
    arc = lambda name, s, mid, e: (f'    skArc({sketch}, "{name}", {{ "start" : {v(s)}, "mid" : {v(mid)}, '
                                   f'"end" : {v(e)} }});')
    line = lambda name, s, e: f'    skLineSegment({sketch}, "{name}", {{ "start" : {v(s)}, "end" : {v(e)} }});'
    n = len(d["flank"])
    names = ["flank"] if n == 1 else [f"flank{n - i}" for i in range(n)]      # numbered from the base up
    t, fm, fr = d["fillet"]
    out = [f"    // ---- generated by gear_gap.py (module {g.module:g}, {g.teeth} teeth, {g.pressure_angle:g} deg); "
           "do not edit by hand ----"]
    out += [arc(nm.replace("flank", "flankA") if n > 1 else "flankA", *a) for nm, a in zip(names, d["flank"])]
    if d["radial"]:
        out.append(line("radialA", *d["radial"]))
    out.append(arc("filletA", t, fm, fr))
    out.append(arc("rootLand", fr, d["root"][1], m(fr)))
    out.append(arc("filletB", m(fr), m(fm), m(t)))
    if d["radial"]:
        out.append(line("radialB", m(d["radial"][1]), m(d["radial"][0])))
    for nm, (s, mid, e) in reversed(list(zip(names, d["flank"]))):
        out.append(arc(nm.replace("flank", "flankB") if n > 1 else "flankB", m(e), m(mid), m(s)))
    out.append(line("outside", m(d["top"]), d["top"]))
    out.append("    // ---- end of generated block ----")
    return "\n".join(out)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--module", type=float, required=True, help="module, mm")
    ap.add_argument("--teeth", type=int, required=True)
    ap.add_argument("--pressure-angle", type=float, default=20.0, help="deg (default 20)")
    ap.add_argument("--addendum", type=float, default=1.0, help="x module (default 1.0)")
    ap.add_argument("--dedendum", type=float, default=1.157, help="x module (default 1.157)")
    ap.add_argument("--root-fillet", type=float, default=0.5, help="mm (default 0.5)")
    ap.add_argument("--backlash", type=float, default=0.0, help="mm on the pitch circle (default 0)")
    ap.add_argument("--overcut", type=float, default=0.5, help="mm the flanks run past the tip circle (default 0.5)")
    ap.add_argument("--tol", type=float, default=0.003, help="largest arc-to-involute deviation, mm (default 0.003)")
    ap.add_argument("--arcs", type=int, help="arcs per flank (default: the fewest within --tol)")
    ap.add_argument("--sketch", default="gapSk", help="sketch variable in the .fs (default gapSk)")
    ap.add_argument("--check", metavar="FS", help="fail unless FS holds this block")
    a = ap.parse_args(argv)
    d = gap(a.module, a.teeth, a.pressure_angle, addendum=a.addendum, dedendum=a.dedendum,
            root_fillet=a.root_fillet, backlash=a.backlash, overcut=a.overcut, tol=a.tol, arcs=a.arcs)
    b = block(d, a.sketch)
    g = d["gear"]
    if a.check:
        src = Path(a.check).read_text()
        found = re.findall(r"    // ---- generated by gear_gap\.py.*?// ---- end of generated block ----", src, re.S)
        if b not in found:
            print(f"{a.check}: tooth-gap block is missing or out of date; run gear_gap.py and paste it in",
                  file=sys.stderr)
            return 1
        print(f"{a.check}: tooth-gap block is current")
    else:
        print(b)
    print(f"// module {g.module:g}, {g.teeth} teeth: {len(d['flank'])} arc(s) per flank, max {d['deviation_mm'] * 1000:.2f} um "
          f"off the involute; root r {g.rr:.4f}, base r {g.rb:.4f}, tip r {g.ra:.4f}; fillet meets the "
          f"{'radial line' if d['radial'] else 'involute'} at r {d['r_t']:.4f}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
