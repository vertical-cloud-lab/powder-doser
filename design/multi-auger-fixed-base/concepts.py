"""Fixed-base multi-auger concepts (issue #204): sweeps + renders.

    pip install cadquery trimesh python-fcl rtree vtk pillow numpy
    xvfb-run -a python concepts.py            # sweeps + renders (about 5 min)
    xvfb-run -a python concepts.py --no-sweep # renders only, spacings from results.json

Every unit is the current doser from PR #170 (real STEP files, see
doserlib.py).  New parts (shared shelf, towers, servo posts, actuator,
clevis bracket, beaker) are simple placeholders sized from the real parts.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import numpy as np

import doserlib as D

HERE = Path(__file__).resolve().parent
OUT = HERE / "renders"
GAP = 2.0                       # clearance every spacing is sized for (mm)
ROLL_FLANK = -90.0              # tap collar rolled onto the unit's +X flank

TOWER_STD = D.tower(28.9, 41.2)     # the baseplate's tower, |x| 28.9..41.2
TOWER_NARROW = D.tower(28.9, 37.0)  # no gear outboard, so 8 mm is plenty


def mirror_x(M):
    return M @ np.diag([-1.0, 1.0, 1.0, 1.0])


# --------------------------------------------------------------------------- #
# concept builders
# --------------------------------------------------------------------------- #
def towers(spec: D.UnitSpec, M, tag):
    out = []
    for sx in (1, -1):
        plain = spec.drive == "none" or (spec.drive == "single-below" and sx < 0)
        sh = TOWER_NARROW if plain else TOWER_STD
        out.append(D.Part(f"{tag}:tower {'+' if sx > 0 else '-'}X", sh, M if sx > 0 else mirror_x(M), D.COL["base"], tag))
    return out


def servo_posts(spec: D.UnitSpec, M, tag):
    """Two posts per servo, under its flanges (placeholders)."""
    out = []
    sides = {"dual-flip": (1, -1), "single-below": (1,)}.get(spec.drive, ())
    for sx in sides:
        # the flange's two M3 holes are 48.04 apart about the case centre, which
        # sits 9.85 mm from the spline: behind it when flipped, ahead of it now
        c = 9.85 if spec.drive == "dual-flip" else -9.85
        ys = (c - 24.02 - 3.0, c + 24.02 - 3.0)
        for y0 in ys:
            post = D.box(67.1, 73.1, y0, y0 + 6.0, D.BASE_TOP_U, -17.5)   # flange on the inner face, |x| = 67.1 (PR #170)
            out.append(D.Part(f"{tag}:servo post", post, M if sx > 0 else mirror_x(M), D.COL["base"], tag))
    return out


ACT_A, ACT_C = 95.0, 45.0       # rod-end pin: 95 mm behind the hinge, 45 mm below it (P16-150: 0-90 deg)


def actuator(M, tilt, tag):
    """Clevis bracket under the plate floor (tilts with it) + a P16 from a
    base pin straight under it, below the shelf."""
    br = D.Part(f"{tag}:clevis bracket", D.clevis_bracket(ACT_A, ACT_C), M @ D.Rx(tilt), D.COL["new"], tag, True)
    Pu = D.Rx(tilt) @ np.array([0.0, ACT_A, -ACT_C, 1.0])
    Bu = np.array([0.0, ACT_A, -ACT_C - D.P16["closed"] - 5.0, 1.0])
    return [br] + D.p16_parts((M @ Bu)[:3], (M @ Pu)[:3], tag, axis_x=M[:3, 0])


def actuator_length(tilt):
    Pu = D.Rx(tilt) @ np.array([0.0, ACT_A, -ACT_C, 1.0])
    Bu = np.array([0.0, ACT_A, -ACT_C - D.P16["closed"] - 5.0, 1.0])
    return float(np.linalg.norm(Pu - Bu))


def shelf(Ms, window_r, slot=False):
    """One flat shelf under all units (6 mm, top level with the old
    baseplate's top), a round window for the beaker, and a slot per unit for
    its actuator rod."""
    plate = None
    for M in Ms:
        r = D.box(-100.0, 100.0, -25.0, 190.0, D.BASE_BOT_U, D.BASE_TOP_U)
        r = r.transformShape(_mat(M)) if False else r.moved(_loc(M))
        plate = r if plate is None else plate.fuse(r)
    plate = plate.cut(D.cyl(window_r, 20, 0, 0, D.BASE_BOT_U - 5))
    if slot:
        for M in Ms:
            s = D.box(-12.0, 12.0, 35.0, 110.0, D.BASE_BOT_U - 5, D.BASE_TOP_U + 5).moved(_loc(M))
            plate = plate.cut(s)
    return plate.clean()


def _loc(M):
    import cadquery as cq
    from OCP.gp import gp_Trsf
    t = gp_Trsf()
    t.SetValues(*M[0, :4], *M[1, :4], *M[2, :4])
    return cq.Location(t)


def _mat(M):
    return M


BEAKERS = {"100 mL": (50.0, 70.0), "150 mL": (60.0, 80.0)}


def beaker_part(kind, rim_z):
    d, h = BEAKERS[kind]
    return D.Part(f"beaker {kind}", D.beaker(d, h), D.Tt(0, 0, rim_z - h), D.COL["glass"], "fixed", False, 0.45)


CONCEPTS = {
    # name: (unit spec, n units, layout, param)
    "P0": dict(title="Two current doser modules nose-to-nose, each on its own baseplate",
               spec=D.UnitSpec("dual-below", baseplate=True), n=2),
    "A1": dict(title="Idea A1: servos turned end for end (cases point back), shared base",
               spec=D.UnitSpec("dual-flip"), n=2),
    "A2": dict(title="Idea A2: one gear + servo per module, on opposite flanks",
               spec=D.UnitSpec("single-below"), n=2),
    "B1": dict(title="Idea B1: gearless pair, an Actuonix P16 under each plate",
               spec=D.UnitSpec("none"), n=2, act=True),
    "B2": dict(title="Idea B2: gearless tri-star (three at 120 deg), a P16 under each plate",
               spec=D.UnitSpec("none", collar_roll=ROLL_FLANK), n=3, act=True),
    # sweep only: could three servo modules (A1's flipped servos) share a beaker?
    "A1x3": dict(title="Three A1 modules (flipped servos) at 120 deg",
                 spec=D.UnitSpec("dual-flip", collar_roll=ROLL_FLANK), n=3),
}

EXPECTED = (("servo pinion", "28T gear"), ("tower", "Mounting plate"), ("P16 rod", "clevis bracket"),
            ("P16 body", "P16 rod"))


def self_check(key, tilts=range(0, 91, 15)):
    """Within one unit: the parts that stay put (servos, pinions, posts, towers,
    P16 body) against the parts that tilt, over 0..90 deg.  Expected contacts
    (meshing teeth, knuckle in its tower, pinned rod end) are left out."""
    worst = (1e9, None, None, None)
    for t in tilts:
        parts, _ = layout(key, 200.0 if CONCEPTS[key]["n"] == 2 else 150.0, (t,) * CONCEPTS[key]["n"], extras=False)
        parts = [p for p in parts if p.name.startswith("A:")]
        for p in parts:
            p.unit = "moving" if p.moving else "still"
        ok = []
        for p in parts:
            ok.append(p)
        best = (1e9, None, None)
        still = [p for p in ok if p.unit == "still"]
        moving = [p for p in ok if p.unit == "moving"]
        for a in still:
            for b in moving:
                if any((x in a.name and y in b.name) or (y in a.name and x in b.name) for x, y in EXPECTED):
                    continue
                d = D.clearance([a, b])[0]
                if d < best[0]:
                    best = (d, a.name, b.name)
        if best[0] < worst[0]:
            worst = (best[0], best[1], best[2], t)
    return worst


def layout(key, spacing, tilts, extras=True, roll=None):
    """Parts of a concept with hinge spacing (pair: hinge-to-hinge D; star:
    hinge radius R) and per-unit tilts."""
    c = CONCEPTS[key]
    spec = c["spec"] if roll is None else D.UnitSpec(c["spec"].drive, collar_roll=roll, baseplate=c["spec"].baseplate)
    n = c["n"]
    if n == 2:
        Ms = [D.place(90, spacing / 2, 0), D.place(-90, spacing / 2, 0)]
    else:
        Ms = [D.place(90 + i * 120, spacing, 0) for i in range(3)]
    parts = []
    for i, M in enumerate(Ms):
        tag = "ABC"[i]
        parts += D.unit_parts(spec, tilts[i], M, tag)
        if not spec.baseplate:
            parts += towers(spec, M, tag) + servo_posts(spec, M, tag)
        if c.get("act"):
            parts += actuator(M, tilts[i], tag)
    if extras and not spec.baseplate:
        win = {2: 30.0, 3: 34.0}[n]
        parts.append(D.Part("shelf", shelf(Ms, win, slot=c.get("act", False)), np.eye(4), D.COL["base"], "fixed"))
    return parts, Ms


def unit_clear(parts):
    """Clearance between units, ignoring the shelf (it is cut round them)."""
    return D.clearance([p for p in parts if p.unit != "fixed"])


def min_spacing(key, tilts, lo=10.0, hi=150.0, roll=None):
    for _ in range(10):
        mid = (lo + hi) / 2
        if unit_clear(layout(key, mid, tilts, extras=False, roll=roll)[0])[0] >= GAP:
            hi = mid
        else:
            lo = mid
    d, a, b = unit_clear(layout(key, hi, tilts, extras=False, roll=roll)[0])
    return round(hi, 1), a, b


TILT_CASES_2 = [(0, 0), (30, 30), (45, 45), (60, 60), (90, 90), (90, 0)]
TILT_CASES_3 = [(0, 0, 0), (30, 30, 30), (45, 45, 45), (60, 60, 60), (90, 90, 90), (90, 0, 0)]


def sweeps():
    res = {}
    for key, c in CONCEPTS.items():
        cases = TILT_CASES_2 if c["n"] == 2 else TILT_CASES_3
        res[key] = {}
        for t in cases:
            s, a, b = min_spacing(key, t)
            res[key][",".join(map(str, t))] = dict(spacing=s, limit=f"{a} / {b}")
            print(f"{key} tilts {t}: {s} mm  ({a} / {b})", flush=True)
    # the tapper rolled onto the flank, for the 90 deg cases
    res["flank"] = {}
    for key in ("A1", "A2", "B1"):
        s, a, b = min_spacing(key, (90, 90), roll=ROLL_FLANK)
        res["flank"][key] = dict(spacing=s, limit=f"{a} / {b}")
        print(f"{key} 90/90 tapper on the flank: {s} mm  ({a} / {b})", flush=True)
    res["self_check"] = {}
    for key in ("A1", "A2", "B1"):
        d, a, b, t = self_check(key)
        res["self_check"][key] = dict(min_clearance=round(d, 2), between=f"{a} / {b}", at_tilt=t)
        print(f"{key} self check 0..90: {d:.2f} mm ({a} / {b} at {t} deg)", flush=True)
    res["servo_check"] = servo_check()
    # the actuator's stroke over 0..90
    res["p16_stroke"] = {str(t): round(actuator_length(t) - D.P16["closed"], 1) for t in (0, 30, 45, 60, 90)}
    return res


# --------------------------------------------------------------------------- #
# figures
# --------------------------------------------------------------------------- #
def outlet_marks(Ms, tilts, r=2.2):
    out = []
    for M, t in zip(Ms, tilts):
        p = (M @ np.append(D.outlet_point(t), 1.0))[:3]
        out.append(D.Part("outlet", D.cyl(r, 1.0, *p - (0, 0, 0.5)).fuse(D.cyl(0.6, 60, p[0], p[1], p[2] - 60)),
                          np.eye(4), (0.85, 0.1, 0.1), "fixed"))
    return out


FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FONT_B = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


def caption(img, title, lines, width=None):
    """Add a white caption bar (bold title + lines) under a PIL image."""
    from PIL import Image, ImageDraw, ImageFont
    w = width or img.width
    if img.width != w:
        img = img.resize((w, round(img.height * w / img.width)))
    fb, fr = ImageFont.truetype(FONT_B, 30), ImageFont.truetype(FONT, 24)
    bar = 24 + 42 + 34 * len(lines)
    out = Image.new("RGB", (w, img.height + bar), "white")
    out.paste(img.convert("RGB"), (0, 0))
    d = ImageDraw.Draw(out)
    d.text((24, img.height + 12), title, font=fb, fill=(20, 20, 20))
    for i, ln in enumerate(lines):
        d.text((24, img.height + 56 + 34 * i), ln, font=fr, fill=(60, 60, 60))
    return out


def side_by_side(paths, out, title, lines, labels=()):
    from PIL import Image, ImageDraw, ImageFont
    ims = [Image.open(p).convert("RGB") for p in paths]
    h = max(i.height for i in ims)
    ims = [i.resize((round(i.width * h / i.height), h)) for i in ims]
    row = Image.new("RGB", (sum(i.width for i in ims) + 20 * (len(ims) - 1), h), "white")
    x = 0
    f = ImageFont.truetype(FONT_B, 26)
    for k, i in enumerate(ims):
        row.paste(i, (x, 0))
        if k < len(labels):
            ImageDraw.Draw(row).text((x + 16, 12), labels[k], font=f, fill=(40, 40, 40))
        x += i.width + 20
    caption(row, title, lines).save(out)
    for p in paths:
        Path(p).unlink()


def outlet_gap(key, sp, t):
    n = CONCEPTS[key]["n"]
    r = (sp / 2 if n == 2 else sp) - D.OUTLET_AHEAD * math.cos(math.radians(t))
    return 2 * r if n == 2 else 2 * r      # pair: outlet to outlet; star: outlet circle diameter


def figures(res, size=(1500, 1050)):
    OUT.mkdir(exist_ok=True)
    pick = {k: v for k, v in res.items() if k in CONCEPTS}
    # working spacing: clears every case up to 60 deg on all units at once, and one unit at 90
    work = {}
    for key, c in CONCEPTS.items():
        cases = (["0,0", "30,30", "45,45", "60,60", "90,0"] if c["n"] == 2
                 else ["0,0,0", "30,30,30", "45,45,45", "60,60,60", "90,90,90", "90,0,0"])
        work[key] = math.ceil(max(pick[key][k]["spacing"] for k in cases))
    res["working_spacing"] = work
    res["outlets"] = {k: {str(t): round(outlet_gap(k, work[k], t), 1) for t in (0, 45, 90)} for k in CONCEPTS if k != "P0"}

    # the problem: current modules, own baseplates, as close as they go
    sp0 = work["P0"]
    parts, Ms = layout("P0", sp0, (0, 0))
    D.render(parts, OUT / "_p0a.png", az=-50, el=28, size=size, dist=1.55)
    # ... and without baseplates at A1's spacing: what still collides
    cur, _ = layout("P0", work["A1"], (0, 0), extras=False)
    cur = [p for p in cur if "Baseplate" not in p.name]
    hits = D.collisions(cur)
    hl = {h for pair in hits for h in pair}
    res["current_without_baseplates_at_A1_spacing"] = sorted({" / ".join(sorted(h)) for h in hits})
    D.render(cur, OUT / "_p0b.png", az=-50, el=28, size=size, dist=1.55, highlight=hl)
    side_by_side([OUT / "_p0a.png", OUT / "_p0b.png"], OUT / "p0_problem.png",
                 "The problem: two current modules nose-to-nose",
                 [f"Left: each on its own baseplate, the hinges can't come closer than {sp0} mm (the baseplates' front arms hit);"
                  f" outlets {sp0 - 23.2:.0f} mm apart.",
                  f"Right: baseplates removed, hinges {work['A1']} mm apart: the MG996R servos (red) still collide,"
                  " because each case reaches 37 mm in front of its hinge."],
                 labels=("own baseplates, 93 mm", f"no baseplates, {work['A1']} mm: servos hit"))

    shots = {
        "A1": ((30, 30), "Idea A1: turn each servo end for end so its case points back",
               "Gears, pinions and mounting plates unchanged. A new shared base holds the towers and rear-facing servo posts."),
        "A2": ((30, 30), "Idea A2: one gear + one servo per module, on opposite flanks",
               "Each mounting plate drops its -X gear; facing each other, the two drives fall on opposite sides and pass."),
        "B1": ((30, 60), "Idea B1: gearless pair, an Actuonix P16-150 under each plate",
               "No servos, gears or pinions. Rod-end clevis 95 mm behind and 45 mm below the hinge; the P16 hangs under the shelf."),
        "B2": ((30, 60, 0), "Idea B2: gearless tri-star, three modules at 120 deg, a P16 under each",
               "Same unit as B1; the tap collar is rolled onto the flank so all three can sit at 90 deg at once."),
    }
    for key, (tilts, title, line) in shots.items():
        sp = work[key]
        n = CONCEPTS[key]["n"]
        parts, Ms = layout(key, sp, tilts)
        parts.append(beaker_part("100 mL" if n == 2 else "150 mL", -11.6 - 15.0))
        parts += outlet_marks(Ms, tilts)
        D.render(parts, OUT / "_iso.png", az=-50 if n == 2 else -70, el=28, size=size, dist=1.6)
        top, Ms0 = layout(key, sp, (0,) * n)
        top.append(beaker_part("100 mL" if n == 2 else "150 mL", -11.6 - 15.0))
        top += outlet_marks(Ms0, (0,) * n)
        D.render(top, OUT / "_top.png", view="top", size=(560, 1050) if n == 2 else (1050, 1050), parallel=True,
                 dist=290 if n == 2 else 320, focal=(0, 0 if n == 2 else 60, 0))
        D.render(top, OUT / "_zoom.png", view="top", size=(1050, 1050), parallel=True, dist=80 if n == 2 else 95)
        o = res["outlets"][key]
        unit = "hinge to hinge" if n == 2 else "hinge to beaker axis"
        what = "outlets apart" if n == 2 else "outlet circle dia."
        tilt_txt = ", ".join(f"{t}" for t in tilts)
        rng = ("every tilt up to 90 deg on all three at once" if key == "B2"
               else "every tilt up to 60 deg on both at once, or one unit at 90")
        lines = [line,
                 f"{unit}: {sp} mm (2 mm clearance, {rng}).  "
                 f"{what}: {o['0']} mm at 0 deg, {o['45']} at 45, {o['90']} at 90.",
                 f"Left: tilts {tilt_txt} deg. Middle/right: plan at 0 deg, red dots = outlets, blue = "
                 f"{'100 mL (50 mm)' if n == 2 else '150 mL (60 mm)'} beaker, rim 15 mm under the 90 deg outlets."]
        side_by_side([OUT / "_iso.png", OUT / "_top.png", OUT / "_zoom.png"], OUT / f"{key.lower()}_concept.png",
                     title, lines, labels=("", "plan", "plan, centre"))
        print("  ->", f"{key.lower()}_concept.png", flush=True)
    return res


def servo_check(keys=("P0", "A1", "A2"), tilts=range(0, 91, 10)):
    """Closest approach of the servos and their posts to anything that tilts
    (one module, 0..90 deg): turning the servo (A1) must not make it worse."""
    out = {}
    for key in keys:
        worst = (1e9, None, None, None)
        for t in tilts:
            parts, _ = layout(key, 200.0, (t, t), extras=False)
            parts = [p for p in parts if p.name.startswith("A:")]
            still = [p for p in parts if "MG996R" in p.name or "servo post" in p.name]
            for a in still:
                for b in (p for p in parts if p.moving):
                    a.unit, b.unit = "still", "moving"
                    d = D.clearance([a, b])[0]
                    if d < worst[0]:
                        worst = (d, a.name, b.name, t)
        out[key] = dict(min_clearance=round(worst[0], 2), between=f"{worst[1]} / {worst[2]}", at_tilt=worst[3])
        print(f"{key} servo check: {out[key]}", flush=True)
    return out


def actuator_figure(res):
    """One gearless module (B1/B2) in half-section at 0, 45 and 90 deg: the
    clevis under the floor, the rod through the shelf slot, the P16 below."""
    paths = []
    for t in (0, 45, 90):
        M = D.place(90, 0.0, 0.0)
        spec = D.UnitSpec("none")
        parts = D.unit_parts(spec, t, M, "A") + towers(spec, M, "A") + actuator(M, t, "A")
        sh = D.box(-100.0, 100.0, -60.0, 190.0, D.BASE_BOT_U, D.BASE_TOP_U).cut(
            D.box(-12.0, 12.0, 35.0, 110.0, D.BASE_BOT_U - 5, D.BASE_TOP_U + 5))
        parts.append(D.Part("shelf", sh, np.eye(4), D.COL["base"], "fixed"))
        fn = OUT / f"_act{t}.png"
        D.render(parts, fn, view="side", size=(900, 1100), parallel=True, dist=262, focal=(0, 86, -8), clip_x=0.3,
                 fixed=True)
        paths.append(fn)
    st = res["p16_stroke"]
    side_by_side(paths, OUT / "b_actuator_mount.png",
                 "Idea B: the actuator mount, half-section through the module's centreline",
                 [f"Rod-end clevis 95 mm behind and 45 mm below the hinge (under the floor, between the auger brackets);"
                  f" base clevis straight below, under the shelf.",
                  f"Rod out from closed: {st['0']} mm at 0 deg, {st['45']} at 45, {st['90']} at 90 (P16-150: 150 mm stroke)."
                  " The actuator swings at most 8 deg; the load is 4-7 N."],
                 labels=("0 deg", "45 deg", "90 deg"))
    print("  -> b_actuator_mount.png", flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-sweep", action="store_true")
    a = ap.parse_args()
    rpath = HERE / "results.json"
    if a.no_sweep and rpath.exists():
        res = json.loads(rpath.read_text())
    else:
        res = sweeps()
    res = figures(res)
    actuator_figure(res)
    rpath.write_text(json.dumps(res, indent=1) + "\n")
    print(json.dumps(res.get("working_spacing"), indent=1))


if __name__ == "__main__":
    main()
