"""Figures for new_scale.py and crank_drive.py (issue #204, 23 Nov).

    renders/newscale_dims.png     the HR-100A (what the earlier checks used) next to the new balance, dimensioned
    renders/newscale_plans.png    plan of each layout with the new balance at its best orientation and its door zones
    renders/newscale_options.png  renders of the three layouts that keep a linear actuator and free a side door
    renders/crank_drive.png       L6's crank and P16-50 at 0, 45 and 90 deg
"""
from __future__ import annotations

import math
from pathlib import Path

import numpy as np

import doserlib as D
import base as B
import components as K
import leg_room as LR
import scale_room as SR
import stands as ST
import crank_drive as CD
import new_scale as NS

OUT = NS.OUT
NB = NS.NB
GLASS = (0.74, 0.86, 0.93)
BAL = (0.86, 0.86, 0.84)


# --------------------------------------------------------------------------- #
# 1. the two balances, dimensioned
# --------------------------------------------------------------------------- #
def _dim(ax, p0, p1, txt, off=(0, 0), fs=9.5, col="#222", rot=0):
    ax.annotate("", xy=p1, xytext=p0, arrowprops=dict(arrowstyle="<->", color=col, lw=1.0, shrinkA=0, shrinkB=0))
    ax.text((p0[0] + p1[0]) / 2 + off[0], (p0[1] + p1[1]) / 2 + off[1], txt, ha="center", va="center", fontsize=fs,
            color=col, rotation=rot, bbox=dict(fc="white", ec="none", pad=0.6))


def fig_dims(fn):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Polygon as MPoly, Circle, Rectangle
    HR = SR.HR
    fig, axs = plt.subplots(2, 2, figsize=(16.5, 15.5), dpi=105, gridspec_kw=dict(height_ratios=[1.05, 1]))
    # --- plans (rear up, display at the bottom)
    ax = axs[0, 0]
    ax.set_aspect("equal")
    for poly in SR.plan_outline_station(90.0, lid=True):
        ax.add_patch(MPoly(poly, closed=True, fc=(0.55, 0.55, 0.55, 0.18), ec="#333", lw=1.0))
    ax.add_patch(Circle((0, 0), HR["bb_r"], fill=False, ec="#1f77b4", lw=1.6))
    ax.add_patch(Circle((0, 0), HR["inside_d"] / 2, fill=False, ec="#1f77b4", lw=0.8, ls="--"))
    ax.add_patch(Circle((0, 0), HR["pan_d"] / 2, fc="#e8e8e8", ec="#555", lw=0.8))
    ax.plot([0], [0], "k+", ms=12)
    w = HR["W"] / 2
    _dim(ax, (-w, -205), (w, -205), "198 wide")
    _dim(ax, (125, HR["front_tip"]), (125, HR["rear"]), "294 deep", off=(12, 0), rot=90)
    _dim(ax, (-118, HR["front_tip"]), (-118, 0), "167", off=(-11, 0), rot=90)
    _dim(ax, (-118, 0), (-118, HR["rear"]), "127", off=(-11, 0), rot=90)
    _dim(ax, (-HR["bb_r"], 30), (HR["bb_r"], 30), "Ø186 across the door frames (Ø156 inside)", fs=8.5, col="#1f77b4")
    ax.text(0, -12, "pan Ø90", ha="center", fontsize=8.5)
    ax.text(0, 105, "rear column\n(full height)", ha="center", fontsize=8.5)
    ax.text(0, -140, "sloped display", ha="center", fontsize=8.5)
    ax.set_xlim(-175, 175)
    ax.set_ylim(-235, 175)
    ax.axis("off")
    ax.set_title("A&D HR-100A: what the 10-21 Nov checks used\n(A&D's drawing, manual section 22; plan, display at the bottom)",
                 loc="left", fontsize=12, fontweight="bold")
    ax = axs[0, 1]
    ax.set_aspect("equal")
    _, e = NS.balance_prims(NB["F"])
    ax.add_patch(Rectangle((-e["wb"], -e["x1"] + 0 if False else e["xb0"]), 2 * e["wb"], e["x1"] - e["xb0"],
                           fc=(0.55, 0.55, 0.55, 0.15), ec="#333", lw=1.0))
    ax.add_patch(Rectangle((-e["w"], e["x0"]), 2 * e["w"], e["x1"] - e["x0"], fc=GLASS + (0.45,), ec="#1f77b4", lw=1.6))
    for sx in (-1, 1):
        ax.plot([sx * e["w"], sx * e["w"]], [e["x0"] + 12, e["x1"] - 12], color="#2ca02c", lw=4.0, solid_capstyle="butt")
    ax.add_patch(Circle((0, 0), 45, fc="#e8e8e8", ec="#555", lw=0.8, ls="--"))
    ax.plot([0], [0], "k+", ms=12)
    _dim(ax, (-e["wb"], e["xb0"] - 18), (e["wb"], e["xb0"] - 18), "base 190 wide")
    _dim(ax, (-e["w"], e["x1"] + 16), (e["w"], e["x1"] + 16), "enclosure 183 wide", col="#1f77b4")
    _dim(ax, (e["wb"] + 22, e["xb0"]), (e["wb"] + 22, e["x1"]), "base 260 long", off=(12, 0), rot=90)
    _dim(ax, (-e["wb"] - 22, e["x0"]), (-e["wb"] - 22, e["x1"]), "enclosure 240 long", off=(-12, 0), rot=90, col="#1f77b4")
    _dim(ax, (40, e["x0"]), (40, 0), f"{NB['F']:.0f}?", off=(10, 0), rot=90, col="#c0392b")
    ax.text(0, 14, "pan: position not known;\ncentred assumed", ha="center", fontsize=8.5, color="#c0392b")
    ax.text(e["w"] + 6, 60, "side door", fontsize=8.5, color="#2ca02c", rotation=90, va="center")
    ax.text(-e["w"] - 6, 60, "side door", fontsize=8.5, color="#2ca02c", rotation=90, va="center", ha="right")
    ax.text(0, e["xb0"] + 9, "display (assumed on the base's front)", ha="center", fontsize=8.5)
    ax.set_xlim(-175, 175)
    ax.set_ylim(-235, 175)
    ax.axis("off")
    ax.set_title("The new balance: your rough numbers, as two boxes\n(plan, display at the bottom; green: sliding side doors)",
                 loc="left", fontsize=12, fontweight="bold")
    # --- side elevations
    ax = axs[1, 0]
    ax.set_aspect("equal")
    for pr in SR.hr_prims(True):
        if pr[0] == "cyl":
            _, cx, cy, r, z0, z1 = pr
            ax.add_patch(Rectangle((cx - r, z0), 2 * r, z1 - z0, fc=(0.55, 0.55, 0.55, 0.14), ec="#333", lw=0.8))
        elif pr[0] == "xy":
            xs = [q[0] for q in pr[1]]
            ax.add_patch(Rectangle((min(xs), pr[2]), max(xs) - min(xs), pr[3] - pr[2], fc=(0.55, 0.55, 0.55, 0.14),
                                   ec="#333", lw=0.8))
        else:
            ax.add_patch(MPoly(pr[1], closed=True, fc=(0.55, 0.55, 0.55, 0.14), ec="#333", lw=0.8))
    ax.plot([-HR["pan_d"] / 2, HR["pan_d"] / 2], [HR["pan_z"], HR["pan_z"]], color="k", lw=2.5)
    ax.axhline(0, color="#888", lw=1.0)
    _dim(ax, (150, 0), (150, HR["H"]), "315 (lid on)", off=(12, 0), rot=90)
    _dim(ax, (-195, 0), (-195, HR["rim_top"]), "290 lid off", off=(-12, 0), rot=90)
    _dim(ax, (-60, 0), (-60, HR["pan_z"]), "pan 86.5", off=(-14, 0), rot=90, fs=8.5)
    _dim(ax, (HR["front_tip"], -22), (HR["rear"], -22), "294")
    ax.text(0, 180, "breeze break", ha="center", fontsize=8.5)
    ax.set_xlim(-215, 185)
    ax.set_ylim(-45, 345)
    ax.set_xlabel("mm, front (left) to back (right)")
    ax.set_title("HR-100A, side", loc="left", fontsize=12, fontweight="bold")
    ax = axs[1, 1]
    ax.set_aspect("equal")
    ax.add_patch(Rectangle((e["xb0"], 0), e["x1"] - e["xb0"], NB["h_base"], fc=(0.55, 0.55, 0.55, 0.14), ec="#333", lw=0.8))
    ax.add_patch(Rectangle((e["x0"], NB["h_base"]), e["x1"] - e["x0"], NB["top"] - NB["h_base"], fc=GLASS + (0.45,),
                           ec="#1f77b4", lw=1.4))
    ax.axhline(0, color="#888", lw=1.0)
    ax.axhline(NS.S_STD, color="#c46a1c", lw=2.0)
    ax.text(-200, NS.S_STD + 6, f"shelf underside at {NS.S_STD:.0f} (S2 can be set there)", color="#c46a1c", fontsize=9)
    _dim(ax, (150, 0), (150, NB["top"]), "320", off=(12, 0), rot=90)
    _dim(ax, (-170, 0), (-170, NB["h_base"]), f"{NB['h_base']:.0f}?", off=(-12, 0), rot=90, col="#c0392b")
    _dim(ax, (e["xb0"], -22), (e["x1"], -22), "260")
    _dim(ax, (e["x0"], NB["top"] + 4), (e["x1"], NB["top"] + 4), "240", fs=8.5)
    ax.text(0, 205, "enclosure", ha="center", fontsize=8.5)
    ax.text(-150, 260, "red: assumed", fontsize=9, color="#c0392b")
    ax.set_xlim(-215, 185)
    ax.set_ylim(-45, 365)
    ax.set_xlabel("mm, front (left) to back (right)")
    ax.set_title("New balance, side", loc="left", fontsize=12, fontweight="bold")
    fig.tight_layout()
    fig.savefig(fn)
    plt.close(fig)
    return fn


# --------------------------------------------------------------------------- #
# 2. plans: the balance at its best orientation in each layout
# --------------------------------------------------------------------------- #
def _to_station(xy, phi):
    c, s = math.cos(math.radians(phi)), math.sin(math.radians(phi))
    xy = np.asarray(xy, float)
    return np.c_[c * xy[:, 0] - s * xy[:, 1], s * xy[:, 0] + c * xy[:, 1]]


def fig_plans(res, samples, fn, keys=("L0", "L2", "L4", "L4r", "T0", "L6")):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Polygon as MPoly
    face = B.shelf_outline_sketch()._faces.Faces()[0]
    ol = B._wire_xy(face.outerWire())
    fig, axs = plt.subplots(2, 3, figsize=(20.5, 15.2), dpi=100)
    for ax, key in zip(axs.ravel(), keys):
        r = res["layouts"][key]
        b = pick(r)
        P, T, Kd, S = samples[key]
        zb = NS.BOT - S
        ax.set_aspect("equal")
        ax.fill(ol[:, 0], ol[:, 1], color="#fbe3c8", zorder=1)
        ax.plot(ol[:, 0], ol[:, 1], color="#c46a1c", lw=1.0, zorder=2)
        hz = P[:, 2] - zb                                  # height above the bench
        low = hz < NB["top"] + 10.0
        act = Kd == 0
        if (act & ~low).any():
            m = act & ~low & ((T == 0) | (T == 90) | (T < 0))
            ax.scatter(P[m, 0], P[m, 1], s=0.25, color="#bbbbbb", zorder=3)
        for t, col in ((0, "#5b8bd9"), (90, "#c0392b")):
            m = act & low & (T == t)
            ax.scatter(P[m, 0], P[m, 1], s=0.3, color=col, zorder=5)
        m = act & low & (T < 0)
        ax.scatter(P[m, 0], P[m, 1], s=0.3, color="#7f7f7f", zorder=5)
        m = Kd == 1
        ax.scatter(P[m, 0], P[m, 1], s=0.3, color="#16a085", zorder=4)
        phi, F = b["phi"], 120.0
        _, e = NS.balance_prims(F)
        base = [(e["xb0"], -e["wb"]), (e["x1"], -e["wb"]), (e["x1"], e["wb"]), (e["xb0"], e["wb"])]
        enc = [(e["x0"], -e["w"]), (e["x1"], -e["w"]), (e["x1"], e["w"]), (e["x0"], e["w"])]
        ax.add_patch(MPoly(_to_station(base, phi), closed=True, fc=(0.5, 0.5, 0.5, 0.15), ec="#555", lw=0.8, zorder=6))
        ax.add_patch(MPoly(_to_station(enc, phi), closed=True, fc=GLASS + (0.55,), ec="#1f77b4", lw=1.4, zorder=6))
        # display arrow
        fr = _to_station([(e["xb0"] - 4, 0), (e["xb0"] - 40, 0)], phi)
        ax.annotate("", xy=fr[1], xytext=fr[0], arrowprops=dict(arrowstyle="-|>", color="#333", lw=1.4), zorder=8)
        # door zones on both sides: green if clear, red if not
        A = NB["access"]
        for side, sg in (("left", 1.0), ("right", -1.0)):
            reach, slide = b[f"door_{side}"], b[f"slide_{side}"]
            zone = [(e["x0"], sg * e["w"]), (e["x1"], sg * e["w"]), (e["x1"], sg * (e["w"] + A)), (e["x0"], sg * (e["w"] + A))]
            ok = reach >= A
            ax.add_patch(MPoly(_to_station(zone, phi), closed=True, fc=("#2ca02c" if ok else "#d62728"), alpha=0.16,
                               ec=("#2ca02c" if ok else "#d62728"), lw=1.0, zorder=7))
            strip = [(e["x1"], sg * (e["w"] - 5)), (e["x1"] + NB["slide_len"], sg * (e["w"] - 5)),
                     (e["x1"] + NB["slide_len"], sg * (e["w"] + NB["slide_strip"])), (e["x1"], sg * (e["w"] + NB["slide_strip"]))]
            ok2 = slide >= NB["slide_len"]
            ax.add_patch(MPoly(_to_station(strip, phi), closed=True, fc="none", ec=("#2ca02c" if ok2 else "#d62728"),
                               lw=1.2, ls="--", zorder=7))
        ax.annotate("gap", xy=(0, -322), ha="center", fontsize=9, color="#777")
        ax.set_xlim(-345, 345)
        ax.set_ylim(-345, 345)
        ax.axis("off")
        s = b.get("door_side")
        rd = lambda v: "clear" if v >= 999 else f"{v:.0f}"
        door = (f"{s} door: reach-in {rd(b[f'door_{s}'])}, slide-back {rd(b[f'slide_{s}'])}" if s else
                f"no door with {NB['access']:.0f} mm beside it (best {max(min(b['door_left'], 999), min(b['door_right'], 999)):.0f})")
        if b["fit"] < NS.GAP:
            tail = f"the balance runs {-b['fit']:.0f} mm into the actuators\n(its best orientation, pan centred)"
        else:
            tail = f"balance {b['fit']:.0f} mm clear (pan centred),\n{door}; top door {rd(b['top_slide'])}"
        ax.set_title(f"{key}  {r['title']}\nshelf {S:.0f} mm up; {tail}", fontsize=10.5, loc="left")
    fig.text(0.01, 0.006,
             "Blue / red: actuator parts at 0° / 90° tilt that are lower than the balance's top (grey: higher up, clear of it); teal: legs; "
             "orange: the base.  Blue box: the enclosure, grey: the balance's base, arrow: its display.  Shaded: 100 mm reach-in zone "
             "beside each side door, dashed: a 200 mm strip for a sliding door (green clear, red blocked).",
             fontsize=10.5, color="#333", wrap=True)
    fig.tight_layout(rect=(0, 0.025, 1, 1))
    fig.savefig(fn)
    plt.close(fig)
    return fn


# --------------------------------------------------------------------------- #
# 3. renders
# --------------------------------------------------------------------------- #
def balance_parts(phi, F, S):
    zb = NS.BOT - S
    _, e = NS.balance_prims(F)
    M = SR.M_balance(phi, zb)
    base = D.Part("new balance base", D.box(e["xb0"], e["x1"], -e["wb"], e["wb"], 0.0, NB["h_base"]), M, BAL, "balance")
    enc = D.Part("new balance enclosure", D.box(e["x0"], e["x1"], -e["w"], e["w"], NB["h_base"], NB["top"]), M, GLASS, "balance")
    out = [base, enc]
    for p in out:
        p.kind = "balance"
    return out


def layout_parts(key, S, tilts=(30, 60, 0)):
    src = NS.LAYOUTS[key]["src"]
    parts = []
    mod_src = {"L5w": "L5", "L6": "L5", "T0": "L0"}.get(src, src)
    for i, th in enumerate(LR.BEARINGS):
        M = D.place(th, LR.SP, 0.0)
        u = "ABC"[i]
        parts += LR.module_parts(mod_src, tilts[i], M, u)
        if src == "L6":
            parts += CD.drive_parts(tilts[i], M, u)
        if src == "T0":
            h = D.Part(f"{u}:hanger", K.hanger(), M, LR.LEG, u, False)
            h.kind = "new"
            parts.append(h)
    for p in parts:
        if getattr(p, "colour", None) is None:
            p.colour = K.STATUS["reuse"][2]
    parts.append(LR.part("base", LR.base_for(mod_src), np.eye(4), K.STATUS["new"][2]))
    if src in ("L5w", "L6", "T0"):
        _, sh = NS.outrigger_posts(S)
        for i, th in enumerate(LR.BEARINGS):
            parts.append(LR.part(f"{'ABC'[i]}:leg", sh, D.place(th, LR.SP, 0.0), LR.LEG))
    else:
        NS.set_height(S)
        parts += LR.fixed_parts(src)
    return parts


def pick(r, F="120"):
    """The configuration to show: the best-ranked one, or the best fit if nothing fits."""
    v = r["any_tilt"][F]
    return v["best"] if v["best"]["level"] > 0 else dict(v["best_fit"], level=0.0, door_side=None)


def render_layout(key, res, fn, title, sub, az=-62.0, el=16.0):
    r = res["layouts"][key]
    S = r["shelf_mm"]
    b = pick(r)
    parts = layout_parts(key, S) + balance_parts(b["phi"], 120.0, S) + [ST.bench(NS.BOT - S, half=400.0)]
    ST.render_concept(f"ns{key}", parts, title, sub, fn, az=az, el=el)
    return fn


def options_sheet(res, fn, keys=("L4r", "T0", "L6")):
    from PIL import Image, ImageDraw
    tiles = []
    for key in keys:
        r = res["layouts"][key]
        b = pick(r)
        s = b.get("door_side")
        rd = lambda v: "clear" if v >= 999 else f"{v:.0f} mm"
        sub = [f"shelf {r['shelf_mm']:.0f} mm up; the balance clears by {b['fit']:.0f} mm",
               f"{s} door: reach-in {rd(b[f'door_{s}'])}, slide-back {rd(b[f'slide_{s}'])}" if s else "no free side door"]
        f = OUT / f"_ns_{key}.png"
        render_layout(key, res, f, f"{key}  {r['title']}", sub)
        tiles.append(f)
    ims = [Image.open(p).convert("RGB") for p in tiles]
    w, h = ims[0].size
    w2, h2 = int(w * 0.7), int(h * 0.7)
    sheet = Image.new("RGB", (len(ims) * w2 + (len(ims) - 1) * 12, h2 + 70), "white")
    for i, im in enumerate(ims):
        sheet.paste(im.resize((w2, h2)), (i * (w2 + 12), 70))
    d = ImageDraw.Draw(sheet)
    d.text((20, 16), "Three ways to keep linear actuators over the new balance (modules at 30, 60 and 0°; pan centred)",
           font=K.font(34, True), fill=(20, 20, 20))
    sheet.save(fn)
    for p in tiles:
        p.unlink()
    return fn


def crank_render(fn):
    """L6 on module A at 0, 45 and 90 deg, seen from its +X side (the neighbours left out)."""
    from PIL import Image, ImageDraw
    tiles = []
    M = D.place(90.0, LR.SP, 0.0)
    kin = CD.kinematics()
    for t in (0, 45, 90):
        parts = LR.module_parts("L5", t, M, "A") + CD.drive_parts(t, M, "A")
        parts.append(LR.part("base", LR.base_for("L5"), np.eye(4), K.STATUS["new"][2]))
        f = OUT / f"_crank_{t}.png"
        D.render(parts, f, az=20.0, el=12.0, size=(900, 1000), parallel=True, dist=118.0, focal=(62.0, 80.0, 42.0),
                 fixed=True)
        im = Image.open(f).convert("RGB")
        d = ImageDraw.Draw(im)
        d.text((20, 16), f"{t}°: rod out {kin['rod_out'][str(t)]:.1f} mm", font=K.font(34, True), fill=(20, 20, 20))
        im.save(f)
        tiles.append(f)
    ims = [Image.open(p) for p in tiles]
    w, h = ims[0].size
    sheet = Image.new("RGB", (3 * w + 24, h + 150), "white")
    for i, im in enumerate(ims):
        sheet.paste(im, (i * (w + 12), 80))
    d = ImageDraw.Draw(sheet)
    d.text((20, 16), "L6: a P16-50 on a crank at the hinge, above the shelf (one module, from its +X side)",
           font=K.font(36, True), fill=(20, 20, 20))
    d.text((20, h + 92), f"Crank {CD.CR['R']:.0f} mm, 45° down-back at 0° and 45° up-back at 90°. Stroke used "
           f"{kin['stroke_used']:.1f} of {CD.ACT['stroke']:.0f} mm, {kin['mm_per_deg'][0]}-{kin['mm_per_deg'][1]} mm per degree, "
           f"at most {kin['max_force_N']:.0f} N (0.65 N·m).", font=K.font(26), fill=(60, 60, 60))
    ST.legend_row(sheet, [("reused", K.STATUS["reuse"][2]), ("#203 bracket", K.STATUS["t203"][2]),
                          ("new (placeholder)", K.STATUS["new"][2]), ("P16-50 (bought)", K.STATUS["buy"][2])],
                  y=h + 122, sz=24)
    sheet.save(fn)
    for p in tiles:
        p.unlink()
    return fn


def all_figures(res, samples):
    if "act_fit" not in LR.OPTIONS["L0"]:
        LR.prepare()
    print("  ->", fig_dims(OUT / "newscale_dims.png"), flush=True)
    print("  ->", fig_plans(res, samples, OUT / "newscale_plans.png"), flush=True)
    print("  ->", crank_render(OUT / "crank_drive.png"), flush=True)
    print("  ->", options_sheet(res, OUT / "newscale_options.png"), flush=True)
