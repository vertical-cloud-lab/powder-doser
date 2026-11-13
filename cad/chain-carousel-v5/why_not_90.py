"""Why v5 stops short of 90 deg (Sam, PR #185, 2026-11-10: "For a 90 degree tilt, make a gif that shows exactly where and why
it didn't work for v5"). Run from this directory, so it uses v5's own layout, parts and renderer unchanged.

    python why_not_90.py analyze            # -> ../chain-carousel-v7/checks/v5_why_not_90.json
    xvfb-run -a python why_not_90.py clip    # -> ../chain-carousel-v7/renders/v7/v5_why_not_90.{gif,mp4,png}

analyze: v5's station tilted 0 -> 90 deg with its two P16s, lift bar, end blocks, EC and module 1 moving, everything else
fixed (the balance's top door open, as v5's --tilt check). Every moving part against every other part (OCC booleans, as
check_interference.py: over 0.5 mm^3 counts, the by-design pairs in its SKIP are skipped): a coarse pass every 3 deg, then
each pair's first contact bisected to 0.25 deg. The P16 extension (|rod pin - base pin| - 197.4 mm) against its 150 mm
stroke, and the lift bar's height over the hinge axis, every 0.5 deg. The module + EC on their own (no bar, no P16s) are
the subset of pairs between module 1 / the EC and the rest.
"""
from __future__ import annotations

import json
import math
import sys
import time
from pathlib import Path

import numpy as np

import check_interference as CI
import layout as L
from params import ACT_RETRACTED, PARK_DROP

HERE = Path(__file__).resolve().parent
V7 = HERE.parent / "chain-carousel-v7"
JSON = Path(__import__("os").environ.get("WHY90_JSON", V7 / "checks" / "v5_why_not_90.json"))
CLIP_OUT = Path(__import__("os").environ.get("WHY90_OUT", V7 / "renders" / "v7"))
STROKE = 150.0
TOP_OPEN = CI.TOP_OPEN
MOVING_GROUPS = CI.MOVING_GROUPS
K_ST = L.carriage_at(L.CARRIAGE_LINK0, 0.0)
BAR_PARTS = ("lift_bar", "bar_end", "actuator_body", "actuator_rod")     # plus the rod ends' screws/nuts (group station_ec, on the bar ends)


def state(a: float) -> L.State:
    return L.State(tilt=float(a), top_door=TOP_OPEN) if a > 0 else L.State(ext=PARK_DROP, top_door=TOP_OPEN)


def movers(pl):
    return [p for p in pl if p.group in MOVING_GROUPS or (p.group == "modules" and p.module == K_ST)]


def is_bar(p) -> bool:
    """The parts v5 added to carry the EC: the bar, its end blocks, the P16s and the rod ends' shoulder screws and nuts."""
    if p.key in BAR_PARTS:
        return True
    return p.key in ("clevis_screw", "nut_m3_clevis") and "rod end" in p.name


def p16_ext(a: float) -> float:
    B, Pp = L.p16_pins(float(a), PARK_DROP, 1)
    return float(np.linalg.norm(Pp - B) - ACT_RETRACTED)


def bar_rel(a: float) -> tuple[float, float]:
    _, P0 = L.actuator_pins(float(a), PARK_DROP)
    return float(P0[0] - L.HINGE_STATION[0]), float(P0[2] - L.HINGE_STATION[2])


def _bb(s):
    return s.BoundingBox()


def _hit(ba, bb_, pad=0.0) -> bool:
    return not (ba.xmax + pad < bb_.xmin or bb_.xmax + pad < ba.xmin or ba.ymax + pad < bb_.ymin or bb_.ymax + pad < ba.ymin
                or ba.zmax + pad < bb_.zmin or bb_.zmax + pad < ba.zmin)


class Scene:
    """Static parts built once (only those within reach of the moving set over 0-90 deg); movers rebuilt per angle."""

    def __init__(self):
        pl = L.placements(state(0.0))
        mv = movers(pl)
        ids = {id(p) for p in mv}
        # the movers' reach: their boxes at a few angles, padded
        boxes = []
        for a in (0.0, 15.0, 30.0, 45.0, 60.0, 75.0, 90.0):
            for p in movers(L.placements(state(a))):
                boxes.append(_bb(L.moved(p.key, p.M)))
        self.reach = boxes
        st_pl = [p for p in pl if id(p) not in ids]
        self.static = []
        for p in st_pl:
            s = L.moved(p.key, p.M)
            b = _bb(s)
            if any(_hit(b, r, 6.0) for r in boxes):
                self.static.append((p, s, b))
        print(f"static parts within reach: {len(self.static)} of {len(st_pl)}", flush=True)

    def pose(self, a: float):
        pl = L.placements(state(a))
        out = []
        for p in movers(pl):
            s = L.moved(p.key, p.M)
            out.append((p, s, _bb(s)))
        return out

    def pairs(self, a: float):
        """(mover placement, other placement, mover shape, other shape) for every bbox-overlapping, non-skipped pair."""
        mo = self.pose(a)
        res = []
        for i, (p, s, b) in enumerate(mo):
            for (q, t, c) in self.static:
                if _hit(b, c) and not CI._skip(p.key, q.key):
                    res.append((p, q, s, t))
            for (q, t, c) in mo[i + 1:]:
                if _hit(b, c) and not CI._skip(p.key, q.key):
                    res.append((p, q, s, t))
        return res


def pair_id(p, q) -> str:
    a, b = sorted((p.name, q.name))
    return f"{a}  x  {b}"


def vol(s, t) -> float:
    try:
        return float(s.intersect(t).Volume())
    except Exception as e:  # noqa: BLE001
        print("   boolean failed:", e, flush=True)
        return -1.0


def analyze(step: float = 3.0, tol: float = 0.25) -> dict:
    t0 = time.time()
    sc = Scene()
    angles = [round(i * step, 3) for i in range(int(round(90.0 / step)) + 1)]
    first: dict[str, dict] = {}
    table: dict[str, dict] = {}
    prev_seen: dict[str, float] = {}
    for a in angles:
        t1 = time.time()
        n_new = 0
        for p, q, s, t in sc.pairs(a):
            pid = pair_id(p, q)
            v = vol(s, t)
            row = table.setdefault(pid, {})
            row[a] = max(row.get(a, 0.0), round(v, 2))
            if v > 0.5 and pid not in first:
                first[pid] = {"coarse_deg": a, "mm3_at_coarse": round(v, 2), "a": p.name, "b": q.name, "a_key": p.key, "b_key": q.key,
                              "mover_is_bar": is_bar(p) or is_bar(q)}
                n_new += 1
        print(f"  tilt {a:5.1f}: {len(first)} pairs over 0.5 mm^3 so far (+{n_new}), {time.time() - t1:.0f} s", flush=True)
    # bisect each pair's first contact between the previous coarse angle and its first coarse hit
    for pid, rec in first.items():
        hi = rec["coarse_deg"]
        lo = max(0.0, hi - step)
        while hi - lo > tol:
            mid = (lo + hi) / 2
            v = _pair_vol(sc, mid, rec)
            if v > 0.5:
                hi = mid
            else:
                lo = mid
        rec["first_deg"] = round(hi, 2)
        rec["mm3_at_first"] = round(_pair_vol(sc, hi, rec), 2)
        print(f"  {pid}: first over 0.5 mm^3 at {hi:.2f} deg ({rec['mm3_at_first']} mm^3)", flush=True)
    for pid, rec in first.items():
        rec["mm3_by_deg"] = table[pid]
    # the stroke and the bar
    fine = [round(0.5 * i, 2) for i in range(181)]
    ext = {a: round(p16_ext(a), 2) for a in fine}
    out_deg = next(a for a in fine if ext[a] > STROKE)
    lo, hi = out_deg - 0.5, out_deg
    while hi - lo > 0.01:
        mid = (lo + hi) / 2
        if p16_ext(mid) > STROKE:
            hi = mid
        else:
            lo = mid
    bar = {a: [round(v, 1) for v in bar_rel(a)] for a in fine[::4]}
    res = {
        "what": "v5's station tilted 0-90 deg by its own kinematics (layout.State(tilt=a), top door open); OCC booleans of every moving part "
                "(two P16s, lift bar, end blocks, EC, module 1) against every other part and each other; over 0.5 mm^3 counts; "
                "check_interference.SKIP pairs skipped",
        "coarse_step_deg": step, "bisect_tol_deg": tol, "seconds": round(time.time() - t0),
        "p16": {"stroke_mm": STROKE, "retracted_mm": ACT_RETRACTED, "ext_docked_mm": ext[0.0], "ext_at_90_mm": ext[90.0],
                "runs_out_at_deg": round(hi, 2), "ext_by_deg": {str(k): v for k, v in ext.items() if (k * 2) % 4 == 0}},
        "lift_bar_axis_rel_hinge_xz_mm": {str(k): v for k, v in bar.items()},
        "first_contacts": sorted(first.values(), key=lambda r: r["first_deg"]),
    }
    JSON.parent.mkdir(parents=True, exist_ok=True)
    JSON.write_text(json.dumps(res, indent=1) + "\n")
    print(f"-> {JSON} ({res['seconds']} s)")
    return res


def _pair_vol(sc: Scene, a: float, rec: dict) -> float:
    pl = L.placements(state(a))
    pa = [p for p in pl if p.name == rec["a"]]
    pb = [p for p in pl if p.name == rec["b"]]
    if not pa or not pb:
        return 0.0
    best = 0.0
    for p in pa:
        for q in pb:
            s, t = L.moved(p.key, p.M), L.moved(q.key, q.M)
            if _hit(_bb(s), _bb(t)):
                best = max(best, vol(s, t))
    return best


# ---------------------------------------------------------------- the clip
RED = (1.0, 0.12, 0.12)
HOT = (1.0, 0.80, 0.08)


def _intersection(a: float, name_a: str, name_b: str):
    """The common solid of two placements (by name) at tilt a, frame coordinates (a cq.Workplane), or None."""
    import cadquery as cq
    pl = L.placements(state(a))
    best, out = 0.0, None
    for p in (p for p in pl if p.name == name_a):
        for q in (q for q in pl if q.name == name_b):
            s, t = L.moved(p.key, p.M), L.moved(q.key, q.M)
            if not _hit(_bb(s), _bb(t)):
                continue
            c = s.intersect(t)
            v = c.Volume()
            if v > best:
                best, out = v, c
    if out is None:
        return None, 0.0
    return cq.Workplane("XY").add(out), best


def clip(preview: bool = False) -> None:
    from PIL import ImageDraw

    import explain as E
    import render as R
    import render_balance as RB

    class _FastView(R.View):
        """No multisampling (explain6.py's trick: 4x MSAA is 15 s a frame under llvmpipe, none 1.7 s)."""
        def __init__(self, w=1600, h=1000, bg=(1, 1, 1), samples=0):
            super().__init__(w, h, bg, 0)

    R.View = _FastView
    E.OUT = CLIP_OUT
    E.GIF_W = 880
    res = json.loads(JSON.read_text())
    H = L.HINGE_STATION
    first = res["first_contacts"]
    out_deg = res["p16"]["runs_out_at_deg"]

    def fc(pred) -> list:
        return [r for r in first if pred(r)]

    # ---- readout (tilt, the P16s' extension against their stroke: red past it) and an optional summary box
    OVER: dict = {"summary": None, "png": None}
    orig = E.compose

    def compose(img3, chap, title, text, items, readout, tag):
        img = orig(img3, chap, title, text, items, None, tag)
        d = ImageDraw.Draw(img, "RGBA")
        W = img.width
        if readout:
            f = E.font(21, True)
            rw = max(d.textlength(s, font=f) for s, _ in readout) + 24
            rh = 28 * len(readout) + 10
            d.rounded_rectangle((W - rw - 12, E.TOP + 10, W - 12, E.TOP + 10 + rh), 8, fill=(25, 30, 40, 232))
            for i, (s, col) in enumerate(readout):
                d.text((W - rw, E.TOP + 15 + 28 * i), s, fill=col, font=f)
        if OVER["summary"]:
            f, fb = E.font(19), E.font(20, True)
            lines = OVER["summary"]
            w = max(d.textlength(s, font=fb if i == 0 else f) for i, s in enumerate(lines)) + 30
            h = 27 * len(lines) + 16
            x0, y0 = 16, E.TOP + 12
            d.rounded_rectangle((x0, y0, x0 + w, y0 + h), 9, fill=(255, 255, 255, 238), outline=(150, 20, 20, 255), width=3)
            for i, s in enumerate(lines):
                d.text((x0 + 14, y0 + 8 + 27 * i), s, fill=(140, 10, 10) if i == 0 else (20, 20, 28), font=fb if i == 0 else f)
        if OVER["png"]:
            img.save(OVER["png"])
            OVER["png"] = None
        return img

    E.compose = compose

    def ro(a: float) -> list:
        e = p16_ext(a)
        over = e > STROKE + 1e-6
        bx, bz = bar_rel(a)
        return [(f"tilt {a:4.1f} deg", (150, 255, 150)),
                (f"P16 extension {e:5.1f} / 150 mm", (255, 90, 80) if over else (150, 255, 150)),
                (f"lift bar {bz:+5.1f} mm over the hinge", (255, 210, 120) if bz > -20 else (200, 220, 255))]

    # ---- red clash solids as extra placements
    n_cl = [0]

    def clash(a: float, name_a: str, name_b: str):
        w, v = _intersection(a, name_a, name_b)
        if w is None:
            return None, 0.0, None
        n_cl[0] += 1
        key = f"clash_{n_cl[0]}"
        L.BUILDERS[key] = (lambda ww=w: ww)
        bb = w.val().BoundingBox()
        cen = ((bb.xmin + bb.xmax) / 2, (bb.ymin + bb.ymax) / 2, (bb.zmin + bb.zmax) / 2)
        return L.Placement(key, f"Clash {n_cl[0]}", np.eye(4), 0, RED, "clash"), v, cen

    def S(a: float, extra=(), **kw) -> L.State:
        st = state(a)
        st.extra = list(extra)
        st.enclosure = False
        for k, v in kw.items():
            setattr(st, k, v)
        return st

    def accent_for(names: set):
        def f(p):
            if p.group == "clash":
                return RED
            if p.name in names:
                return HOT
            return None
        return f

    KEEP_SIDE = (0, 1, 12)            # modules/carriages 1, 2 and 13 (k = 0, 1, 12); the rest of the loop is hidden
    KEEP_FRONT = (0, 1, 11, 12)       # ... and carriage 12, on the -y side run

    def _others(p, keep) -> bool:
        return p.group in ("modules", "carriages") and p.module >= 0 and p.module not in keep

    def hide_side(p) -> bool:
        return RB.cut_section(p) or p.group == "elec" or _others(p, KEEP_SIDE)

    def hide_front(p) -> bool:
        """The front view: no enclosure, no front side plate, and nothing on the front chain's plane (its chain, sprockets,
        hold-down) in front of the station; only modules 1, 2, 12 and 13."""
        if p.group == "clash":
            return False
        if RB.cut_front(p) or p.group == "elec" or _others(p, KEEP_FRONT):
            return True
        x = p.M[0, 3]
        if p.group in ("chain", "sprockets") and x < 20.0:
            return True
        if p.key in ("hold_down", "hall_switch", "insert_m5", "m5x16_shcs", "tensioner_block", "m5x10_shcs", "m5x30_shcs", "nut_m5",
                     "flange_bearing", "bolt_m6x25", "nut_m6") and x < 20.0:
            return True
        return False

    def hide_alone(p) -> bool:
        """Module 1, its carriage and the EC (no bar, no P16s), and the clash solids."""
        if p.group == "clash":
            return False
        if p.module == 0 and p.group in ("modules", "carriages"):
            return False
        if p.group == "station_ec" and not is_bar(p):
            return False
        return True

    def see_through(names: set, op: float = 0.30):
        """The clash partners see-through, and every part of a module that one of them belongs to (its auger, door and
        cap stand in front of the red solid in the front view)."""
        import re
        mods = set()
        for n in names:
            m = re.search(r"(\d+)$", n.strip())
            if m and not n.startswith("Carriage"):
                mods.add(int(m.group(1)) - 1)
        return lambda pl: {p.name: op for p in pl if p.name in names or (p.group == "modules" and p.module in mods)}

    bar_names = {p.name for p in L.placements(state(0.0)) if is_bar(p)}
    focus_all = lambda p: True  # noqa: E731
    TAG = "chain carousel v5 · why it stops short of 90 deg · PR #185 · 2026-11-10"
    CAM_SIDE = ((H[0] + 75.0, H[1], H[2] + 20.0), (0.0, 1.0, 0.06), 780)
    CAM_SIDE_LOW = ((H[0] + 75.0, H[1], H[2] - 20.0), (0.0, 1.0, 0.04), 1080)
    CAM_FRONT = ((100.0, 0.0, H[2] + 8.0), (-1.0, -0.06, 0.10), 470)
    CAM_HINGE = ((H[0] - 15.0, H[1], H[2] + 22.0), (-0.45, 1.0, 0.38), 175)

    shared: dict = {}
    plan = EVENTS(res, fc)                        # the limits, in order (built from the JSON)
    c = E.Clip("v5_why_not_90", TAG, len(plan["chapters"]), preview)
    for idx, ch in enumerate(plan["chapters"], 1):
        ch(c, dict(idx=idx, state=shared, hide_alone=hide_alone, see_through=see_through, S=S, ro=ro, clash=clash, accent_for=accent_for, hide_side=hide_side, hide_front=hide_front, CAM_SIDE=CAM_SIDE,
                   CAM_SIDE_LOW=CAM_SIDE_LOW, CAM_FRONT=CAM_FRONT, CAM_HINGE=CAM_HINGE, bar_names=bar_names, OVER=OVER, E=E, R=R,
                   out_deg=out_deg, res=res, focus_all=focus_all))
    c.done()


def _who(name: str) -> str:
    """A short label for a part name: 'module 13's plate', 'carriage 12', 'the lift bar' ..."""
    import re
    m = re.search(r"(\d+)$", name.strip())
    n = m.group(1) if m else ""
    low = name.lower()
    if low.startswith("lift bar"):
        return "the lift bar"
    if low.startswith("bar end"):
        return "a lift-bar end block"
    if "actuonix" in low:
        return "a P16"
    if low.startswith("mounting plate"):
        return f"module {n}'s plate"
    if low.startswith("auger cap"):
        return f"module {n}'s cap"
    if low.startswith("auger"):
        return f"module {n}'s auger"
    if low.startswith("door housing screw"):
        return f"module {n}'s door screws"
    if low.startswith("door"):
        return f"module {n}'s outlet door"
    if low.startswith("carriage "):
        return f"carriage {n}"
    if low.startswith("electronics carriage"):
        return "the EC"
    if "shoulder screw" in low or "locknut" in low:
        return "a P16 rod-end screw" if "rod end" in low else "a pin screw"
    return name.split("(")[0].strip()


def EVENTS(res: dict, fc) -> dict:
    """The clip's chapters, from the analysis: the lift bar's first contacts with the corner modules (in order), the P16s'
    stroke, the bar against the side run's carriages, the module + EC on their own against their carriage's opening, and a
    summary. Each chapter is f(clip, kit); kit["idx"] is its number."""
    import explain as E
    first = res["first_contacts"]
    out_deg = res["p16"]["runs_out_at_deg"]
    ext90 = res["p16"]["ext_at_90_mm"]
    bar_side = ("the lift bar", "a lift-bar end block", "a P16", "a P16 rod-end screw")

    def split(r):
        """(bar part name, other part name) for a bar contact."""
        return (r["a"], r["b"]) if _who(r["a"]) in bar_side else (r["b"], r["a"])

    barhits = [r for r in first if r["mover_is_bar"]]
    by_mod: dict = {}
    car_hits = []
    for r in sorted(barhits, key=lambda r: r["first_deg"]):
        mine, other = split(r)
        who = _who(other)
        if who.startswith("module "):
            by_mod.setdefault(who.split("'")[0], []).append(r)
        elif who.startswith("carriage "):
            car_hits.append(r)
    mod_events = sorted(by_mod.items(), key=lambda kv: kv[1][0]["first_deg"])
    mod_only = sorted([r for r in first if not r["mover_is_bar"]], key=lambda r: r["first_deg"])
    chapters = []

    def labels_at(a, rs, clash):
        """Red solids and callouts for the contacts in rs that overlap at tilt a."""
        pls, labs, names, partners = [], [], set(), set()
        for r in rs:
            pa, v, cen = clash(a, r["a"], r["b"])
            names |= {r["a"], r["b"]}
            if pa is None or v < 0.05:
                continue
            pls.append(pa)
            mine, other = split(r) if r["mover_is_bar"] else (r["a"], r["b"])
            partners.add(other)
            labs.append((f"from {r['first_deg']:.1f} deg: {_who(mine)}\nx {_who(other)} ({v:.0f} mm3 here)", E.world(cen)))
        return pls, labs, names, partners

    def ch_intro(c, k):
        S, ro = k["S"], k["ro"]
        a1 = mod_events[0][1][0]["first_deg"] if mod_events else 40.0
        c.chapter(k["idx"], "v5 tilts on its lift bar: fine up to 40 deg")
        c.move(3.5, lambda t, i, n: dict(st=S(40.0 * t), cam=k["CAM_SIDE"], hide=k["hide_side"], readout=ro(40.0 * t),
                                         accent=lambda p: HOT if p.name in k["bar_names"] else None,
                                         labels=[("Lift bar (8 mm), clamped in the EC's base:\nit turns with the module", E.part("lift_bar")),
                                                 ("Hinge axis", E.world(L.HINGE_STATION))] if t > 0.25 else (),
                                         text="Section through v5's station, seen from +y (yellow: the lift bar, its end blocks and the two "
                                              "P16s). The EC hangs on an 8 mm bar that the P16s push; the bar runs through the EC's base 75 mm "
                                              f"under the hinge axis and 58 mm behind it, so it swings up with the module. v5 stops at 40 deg; "
                                              f"the first clash is at {a1:.1f} deg."))
        c.hold(0.6)

    chapters.append(ch_intro)

    def ch_bar(c, k):
        S, ro, clash, R = k["S"], k["ro"], k["clash"], k["R"]
        c.chapter(k["idx"], "The lift bar climbs into the corner modules")
        c.move(1.5, lambda t, i, n: dict(st=S(40.0), cam=R.cam_lerp(k["CAM_SIDE"], k["CAM_FRONT"], t), hide=k["hide_front"],
                                         readout=ro(40.0), accent=lambda p: HOT if p.name in k["bar_names"] else None,
                                         text="From the front (front side plate removed): the bar is 264 mm long along y, so its ends pass "
                                              "under the modules on both bottom corners."))
        a_prev, hit = 40.0, set()
        for mod, rs in mod_events[:2]:
            a = rs[0]["first_deg"]
            af = min(a + 3.0, 89.0)
            c.move(1.0, lambda t, i, n, a0=a_prev, a1=af, hn=set(hit): dict(
                st=S(a0 + (a1 - a0) * t), cam=k["CAM_FRONT"], hide=k["hide_front"], readout=ro(a0 + (a1 - a0) * t),
                accent=k["accent_for"](hn | k["bar_names"]), text=f"Tilting on past {a:.1f} deg."), eased=False)
            pls, labs, names, partners = labels_at(af, [r for r in rs if r["first_deg"] <= af], clash)
            hit |= names
            cen = labs[0][1](None, None) if labs else np.array([100.0, 0.0, 440.0])
            close = (tuple(cen), (-1.0, -0.06, 0.10), 250)
            acc = k["accent_for"]((hit - partners) | k["bar_names"])
            c.move(0.8, lambda t, i, n, cl=close, pp=pls, pt=partners, ac=acc: dict(
                st=S(af, extra=pp), cam=R.cam_lerp(k["CAM_FRONT"], cl, t), hide=k["hide_front"], readout=ro(af), accent=ac,
                opacity=k["see_through"](pt), text=f"Closer: module {mod.split()[-1]}, see-through."))
            c.frame(st=S(af, extra=pls), cam=close, hide=k["hide_front"], readout=ro(af), accent=acc, labels=labs,
                    opacity=k["see_through"](partners),
                    text=f"From {a:.1f} deg the lift bar runs into {mod} (red: the solid the two parts would share, shown at {af:.1f} deg). "
                         "The bar is on the far side of the hinge from the plate, so its ends climb toward the corner modules as the "
                         "module stands up.")
            c.hold(1.8)
            c.move(0.8, lambda t, i, n, cl=close, ac=acc: dict(st=S(af), cam=R.cam_lerp(cl, k["CAM_FRONT"], t), hide=k["hide_front"],
                                                               readout=ro(af), accent=ac, text="Back out."))
            a_prev = af
        k["state"]["a"], k["state"]["hit"] = a_prev, hit

    if mod_events:
        chapters.append(ch_bar)

    def ch_stroke(c, k):
        S, ro, R = k["S"], k["ro"], k["R"]
        a0 = k["state"].get("a", 62.0)
        acc = lambda p: HOT if p.key in ("actuator_rod", "actuator_body") else None  # noqa: E731
        c.chapter(k["idx"], f"The P16s run out of stroke at {out_deg:.1f} deg")
        c.move(1.2, lambda t, i, n: dict(st=S(a0), cam=R.cam_lerp(k["CAM_FRONT"], k["CAM_SIDE_LOW"], t), hide=k["hide_side"], readout=ro(a0),
                                         accent=acc, text="Back to the section. The readout's second line is the P16s' extension."))
        c.move(2.2, lambda t, i, n: dict(st=S(a0 + (out_deg - a0) * t), cam=k["CAM_SIDE_LOW"], hide=k["hide_side"],
                                         readout=ro(a0 + (out_deg - a0) * t), accent=acc,
                                         text="The bar's pin moves on a circle about the hinge axis and the P16s stand under it, so the rod "
                                              f"it takes grows with the tilt: {res['p16']['ext_by_deg'].get('40.0', 85.0):.0f} mm at 40 deg, "
                                              f"{res['p16']['ext_by_deg'].get('60.0', 118.0):.0f} mm at 60 deg (28 of them to dock)."),
               eased=False)
        lab = [(f"{out_deg:.1f} deg: both P16-150s\nat their full 150 mm stroke", E.part("actuator_rod", nth=0))]
        c.frame(st=S(out_deg), cam=k["CAM_SIDE_LOW"], hide=k["hide_side"], readout=ro(out_deg), labels=lab,
                accent=lambda p: RED if p.key == "actuator_rod" else None,
                text=f"{out_deg:.1f} deg: the P16s are fully extended. 90 deg would need {ext90:.1f} mm of rod, {ext90 - 150.0:.1f} mm "
                     "more than a P16-150 has.")
        c.hold(1.8)
        c.move(1.2, lambda t, i, n: dict(st=S(out_deg + (90.0 - out_deg) * t), cam=k["CAM_SIDE_LOW"], hide=k["hide_side"],
                                         readout=ro(out_deg + (90.0 - out_deg) * t), accent=lambda p: RED if p.key == "actuator_rod" else None,
                                         text="Beyond it the rods would have to leave their tubes (drawn only to show the shortfall)." +
                                              (f" At {late_car[0]['first_deg']:.1f} deg the bar's end also reaches {_who(split(late_car[0])[1])}, on the "
                                               "-y side run." if late_car else "")),
               eased=False)
        c.hold(0.8)

    STROKE_CH = ch_stroke

    early_car = [r for r in car_hits if r["first_deg"] < out_deg]
    late_car = [r for r in car_hits if r["first_deg"] >= out_deg]
    if early_car:
        def ch_car(c, k):
            S, ro, clash, R = k["S"], k["ro"], k["clash"], k["R"]
            a0 = k["state"].get("a", 40.0)
            hit = k["state"].get("hit", set())
            a1 = early_car[-1]["first_deg"]
            af = min(a1 + 1.5, out_deg - 0.5)
            whos = [_who(split(r)[1]) for r in early_car]
            c.chapter(k["idx"], f"{early_car[0]['first_deg']:.0f}-{a1:.0f} deg: the bar reaches the carriages")
            c.move(2.0, lambda t, i, n: dict(st=S(a0 + (af - a0) * t), cam=k["CAM_FRONT"], hide=k["hide_front"], readout=ro(a0 + (af - a0) * t),
                                             accent=k["accent_for"](hit | k["bar_names"]),
                                             text="Further on, the bar passes right through both corner modules (yellow: the parts it has hit)."),
                   eased=False)
            pls, labs, names, partners = labels_at(af, early_car, clash)
            c.frame(st=S(af, extra=pls), cam=k["CAM_FRONT"], hide=k["hide_front"], readout=ro(af),
                    accent=k["accent_for"]((hit | names | k["bar_names"]) - partners), opacity=k["see_through"](partners | hit - k["bar_names"]),
                    labels=labs, text=f"By {a1:.1f} deg the bar has reached {', '.join(whos[:-1])} and {whos[-1]}: the corner modules' "
                                      "carriages, then the station module's own carriage, whose latch housing hangs under it (red: the shared "
                                      f"solids at {af:.1f} deg).")
            c.hold(2.0)
            k["state"]["a"] = af
        chapters.append(ch_car)
    chapters.append(STROKE_CH)

    if mod_only:
        def ch_alone(c, k):
            S, ro, clash, R = k["S"], k["ro"], k["clash"], k["R"]
            hide = k["hide_alone"]
            trans = lambda pl: {p.name: 0.30 for p in pl if p.name == "Carriage 1"}  # noqa: E731
            a1 = mod_only[0]["first_deg"]
            af = min(a1 + 1.5, 90.0)
            c.chapter(k["idx"], "Module and EC alone: the plate meets its carriage")
            c.move(1.2, lambda t, i, n: dict(st=S(62.0), cam=R.cam_lerp(k["CAM_FRONT"], k["CAM_HINGE"], t), hide=hide, readout=ro(62.0),
                                             opacity=trans, text="Now only module 1, its carriage (see-through) and the EC: no bar, no P16s. "
                                                                 "A close-up of the hinge and the front end of the carriage's opening, from +y."))
            c.move(1.8, lambda t, i, n: dict(st=S(62.0 + (af - 62.0) * t), cam=k["CAM_HINGE"], hide=hide, opacity=trans,
                                             readout=ro(62.0 + (af - 62.0) * t),
                                             text="As the module stands up, the plate's front end turns down past the hinge axis."), eased=False)
            pls, labs, names, partners = labels_at(af, [r for r in mod_only if r["first_deg"] <= af], clash)
            c.frame(st=S(af, extra=pls), cam=k["CAM_HINGE"], hide=hide, opacity=trans, readout=ro(af), accent=k["accent_for"](names - partners),
                    labels=labs[:3], text=f"From {a1:.1f} deg the plate's underside, 18 mm off the hinge axis, swings past the front end of the "
                                          "carriage's opening, which starts only 14 mm in front of the axis (red)" +
                                          (f"; the door housing's screws follow at {mod_only[1]['first_deg']:.1f} deg" if len(mod_only) > 1 else "") +
                                          ". The cap never reaches the top run: the module is 252 mm long on a hinge 355 mm under it.")
            c.hold(1.8)
            if af < 89.5:
                pls90, labs90, names90, partners90 = labels_at(90.0, mod_only, clash)
                c.move(1.0, lambda t, i, n: dict(st=S(af + (90.0 - af) * t), cam=k["CAM_HINGE"], hide=hide, opacity=trans,
                                                 readout=ro(af + (90.0 - af) * t), accent=k["accent_for"](names - partners), text="On to 90 deg."),
                       eased=False)
                c.frame(st=S(90.0, extra=pls90), cam=k["CAM_HINGE"], hide=hide, opacity=trans, readout=ro(90.0),
                        accent=k["accent_for"](names90 - partners90), labels=labs90[:3], text="90 deg, module and EC alone.")
                c.hold(1.5)
        chapters.append(ch_alone)

    def ch_sum(c, k):
        S, ro = k["S"], k["ro"]
        c.chapter(k["idx"], "Summary: v5's limits on the way to 90 deg, in order")
        rows = []
        for mod, rs in mod_events:
            for r in rs:
                rows.append((r["first_deg"], f"the lift bar reaches {_who(split(r)[1])}"))
        rows.append((out_deg, f"the P16-150s reach full stroke (90 deg needs {ext90:.1f} mm)"))
        for r in car_hits:
            where = " on the side run" if r in late_car else (" (its own)" if _who(split(r)[1]) == "carriage 1" else "")
            rows.append((r["first_deg"], f"the lift bar reaches {_who(split(r)[1])}{where}"))
        for r in mod_only:
            wa = _who(r["a"])
            rows.append((r["first_deg"], f"{wa} {'meet' if wa.endswith('s') else 'meets'} {_who(r['b'])}'s opening (module + EC alone)"))
        rows.sort()
        bz = res["lift_bar_axis_rel_hinge_xz_mm"]["90.0"][1]
        lines = ["Where v5 stops (over 0.5 mm3 of overlap = a clash)"] + [f"{a:5.1f} deg   {s}" for a, s in rows]
        lines.append(f"At 90 deg the bar would be {bz:.0f} mm above the hinge axis")
        k["OVER"]["summary"] = lines
        k["OVER"]["png"] = str(CLIP_OUT / "v5_why_not_90.png")
        a_k = min(mod_events[0][1][0]["first_deg"] + 6.0, 89.0) if mod_events else 46.0
        names = set(k["bar_names"])
        for mod, rs in mod_events:
            names |= {rs[0]["a"], rs[0]["b"]}
        a1 = mod_events[0][1][0]["first_deg"] if mod_events else float("nan")
        c.frame(st=S(a_k), cam=k["CAM_FRONT"], hide=k["hide_front"], readout=ro(a_k), accent=k["accent_for"](names),
                text=f"v5 can't reach 90 deg: its lift bar turns with the module and climbs into the corner modules from {a1:.1f} deg, and "
                     f"its P16-150s run out of stroke at {out_deg:.1f} deg. The module and the EC on their own are clear until the "
                     f"plate meets its carriage's opening at {mod_only[0]['first_deg'] if mod_only else 90.0:.1f} deg.")
        c.hold(4.0)
        k["OVER"]["summary"] = None

    chapters.append(ch_sum)
    return {"chapters": chapters}


def _cen(pa) -> tuple:
    bb = L.shape(pa.key).BoundingBox()
    return ((bb.xmin + bb.xmax) / 2, (bb.ymin + bb.ymax) / 2, (bb.zmin + bb.zmax) / 2)


if __name__ == "__main__":
    if "analyze" in sys.argv:
        st = float(sys.argv[sys.argv.index("--step") + 1]) if "--step" in sys.argv else 3.0
        analyze(st)
    elif "clip" in sys.argv:
        clip(preview="--preview" in sys.argv)
    else:
        print(__doc__)
