#!/usr/bin/env python3
"""Build every figure of the optimization manuscript.

Real data come from ``paper/optimization/data/`` (copied from the branches
named in ``data/README.md``).  Panels that wait on experiments not yet run are
drawn from clearly synthetic numbers and carry a diagonal "SYNTHETIC DATA"
mark; their captions start with "[Placeholder: synthetic data.]".

Usage:  python3 figures/make_figures.py        (from paper/optimization/)
Writes figures/<name>.pdf and figures/<name>.png.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Rectangle  # noqa: E402

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
DATA = ROOT / "data"
SALT = DATA / "salt-20260929T014732Z"

# Palette: the companion paper's (blue = optimizer, orange = hand tuning /
# research powders, grey = context).  Validated with the dataviz checker:
# all-pairs CVD dE >= 9.2 for the three hues below.
INK, INK2, MUTED = "#0b0b0b", "#52514e", "#8a8983"
GRID, BAND = "#e8e6e0", "#f0efec"
BLUE, ORANGE, AQUA = "#2a78d6", "#eb6834", "#1baf7a"
BLUE_L, ORANGE_L = "#cde2fb", "#fbd9c9"

SINGLE, ONEHALF, DOUBLE = 3.54, 5.51, 7.48  # Elsevier column widths, inches

plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["DejaVu Sans"],
    "font.size": 8,
    "axes.titlesize": 8,
    "axes.labelsize": 8,
    "xtick.labelsize": 7,
    "ytick.labelsize": 7,
    "legend.fontsize": 7,
    "axes.edgecolor": MUTED,
    "axes.labelcolor": INK,
    "axes.linewidth": 0.6,
    "xtick.color": INK2,
    "ytick.color": INK2,
    "xtick.major.width": 0.6,
    "ytick.major.width": 0.6,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "savefig.dpi": 300,
    "pdf.fonttype": 42,
})


# ----------------------------------------------------------------- helpers
def save(fig, name: str) -> None:
    for ext in ("pdf", "png"):
        fig.savefig(HERE / f"{name}.{ext}", bbox_inches="tight", pad_inches=0.02)
    plt.close(fig)
    print("wrote", name)


def synthetic(ax, text: str = "SYNTHETIC DATA") -> None:
    """Diagonal, light watermark: readable, but out of the way of the marks."""
    ax.text(0.5, 0.5, text, transform=ax.transAxes, rotation=28, ha="center", va="center",
            fontsize=15, fontweight="bold", color="#c0392b", alpha=0.16, zorder=0)


def panel(ax, letter: str, x: float = -0.16, y: float = 1.04) -> None:
    ax.text(x, y, f"({letter})", transform=ax.transAxes, fontweight="bold", fontsize=9,
            va="bottom", ha="left", color=INK)


def ylabel_top(ax, text: str) -> None:
    """Horizontal y label above the axis (the repo's figure convention)."""
    ax.set_ylabel("")
    ax.text(0.0, 1.02, text, transform=ax.transAxes, ha="left", va="bottom", color=INK, fontsize=8)


# ------------------------------------------------------------ salt campaign
HAND = ("baseline-00", "baseline-01", "rebaseline-00", "rebaseline-01")
RECOMMENDED = "bo-005"
REF_T, REF_E = 180.0, 20.0  # the campaign's reference point (s, mg)
PRE_RESTART = (42, 43)      # validation doses before the restart (validation_20261006.md)


def salt_doses() -> pd.DataFrame:
    rows = []
    for line in open(SALT / "campaign_records.jsonl"):
        r = json.loads(line)
        s = r["summary"]
        lab = r["label"]
        if r["mode"] == "validation":
            if r["trial_index"] in PRE_RESTART:
                continue  # ran before the rig restart; counted in no validation block
            grp = "val-bo" if "bo-005" in lab else "val-corner"
        else:
            grp = ("hand" if lab in HAND else "screen" if lab.startswith(("corner", "center"))
                   else "anchor" if lab.startswith("recenter") else "bo")
        rows.append(dict(i=r["trial_index"], label=lab, group=grp, status=s["status"],
                         t=s["t_total_s"], err=s["error_mg"], abs=s["abs_error_mg"],
                         uuid=r["trial_uuid"], **r["params"]))
    return pd.DataFrame(rows).sort_values("i").reset_index(drop=True)


def hv2d(points: list[tuple[float, float]], ref=(REF_T, REF_E)) -> float:
    """Dominated hypervolume of 2-D minimization points inside the reference box."""
    pts = sorted((t, e) for t, e in points if t < ref[0] and e < ref[1])
    hv, best_e = 0.0, ref[1]
    front = []
    for t, e in pts:
        if e < best_e:
            front.append((t, e))
            best_e = e
    for k, (t, e) in enumerate(front):
        t_next = front[k + 1][0] if k + 1 < len(front) else ref[0]
        hv += (t_next - t) * (ref[1] - e)
    return hv


def pareto_mask(t: np.ndarray, e: np.ndarray) -> np.ndarray:
    keep = np.ones(len(t), bool)
    for k in range(len(t)):
        dom = (t <= t[k]) & (e <= e[k]) & ((t < t[k]) | (e < e[k]))
        keep[k] = not dom.any()
    return keep


def trace(uuid: str) -> dict:
    d = json.load(open(SALT / "zero" / f"trial_{uuid}.json"))
    cols = d["telemetry"]["header"].split(",")
    rows = [dict(zip(cols, r.split(","))) for r in d["telemetry"]["rows"]]
    t = np.array([float(r["t_s"]) for r in rows])
    m = np.array([float(r["z_g"]) for r in rows])
    ph = [r["phase"] for r in rows]
    t0 = next(tt for tt, p in zip(t, ph) if p == "bulk") - 0.4
    o = d["outcomes"]
    stage = {}
    for p in ("bulk", "trickle", "tap"):
        ts = [tt for tt, q in zip(t, ph) if q.startswith(p)]
        if ts:
            stage[p] = (min(ts) - t0, max(ts) - t0)
    return dict(t=np.r_[0.0, t - t0, o["t_total_s"]], m=np.r_[0.0, m, o["settled_final_g"]] * 1e3,
                stage=stage, outcomes=o)


def fig_salt_campaign() -> None:
    allv = salt_doses()
    df = allv[~allv.group.str.startswith("val")].reset_index(drop=True)
    val = allv[allv.group.str.startswith("val")]
    fig = plt.figure(figsize=(DOUBLE, 5.3))
    gs = fig.add_gridspec(2, 3, width_ratios=[1.0, 0.62, 0.95], hspace=0.62, wspace=0.55)
    a = fig.add_subplot(gs[0, 0:2])
    b = fig.add_subplot(gs[0, 2])
    gs2 = fig.add_gridspec(2, 3, width_ratios=[0.95, 0.75, 0.95], hspace=0.62, wspace=0.12)
    c = fig.add_subplot(gs2[1, 0])
    d = fig.add_subplot(gs2[1, 2])

    # (a) every campaign dose in objective space, plus the two validation blocks
    style = {"hand": (ORANGE, "o", "hand-tuned settings"), "screen": (MUTED, "o", "screening corners"),
             "anchor": (MUTED, "D", "centre-point repeats"), "bo": (BLUE, "o", "chosen by the optimizer")}
    over = df["err"] > 20  # overshoots beyond the error limit, drawn along the top edge
    for g, (col, mk, lab) in style.items():
        s_ = df[(df.group == g) & ~over]
        a.scatter(s_.t, s_["abs"], s=22, c=col, marker=mk, edgecolors="white", linewidths=0.6,
                  zorder=3, label=lab)
        so = df[(df.group == g) & over]
        a.scatter(so.t, np.full(len(so), 27.5), s=24, c=col, marker="^", edgecolors="white",
                  linewidths=0.6, zorder=3)
    vb = val[val.group == "val-bo"]
    vc = val[val.group == "val-corner"]
    a.scatter(vb.t, vb["abs"], s=18, facecolors="none", edgecolors=BLUE, linewidths=0.8, zorder=4,
              label="bo-005 repeated, 8 doses")
    a.scatter(vc.t, vc["abs"], s=16, facecolors="none", edgecolors=INK2, marker="D", linewidths=0.7,
              zorder=4, label="corner-09 repeated, 8 doses")
    a.axhline(REF_E, color=INK2, lw=0.6, ls=(0, (3, 2)))
    a.axvline(REF_T, color=INK2, lw=0.6, ls=(0, (3, 2)))
    a.text(REF_T + 4, 21.0, "limits: 180 s, 20 mg", color=INK2, fontsize=6.5, va="bottom")
    a.text(30, 27.5, "overshoots, 21–83 mg over", color=INK2, fontsize=6.5, va="center", ha="left")
    ok = df[(df.t < REF_T) & (df["abs"] < REF_E)]
    pm = pareto_mask(ok.t.values, ok["abs"].values)
    fr = ok[pm].sort_values("t")
    a.step(np.r_[fr.t.values, REF_T], np.r_[fr["abs"].values, fr["abs"].values[-1]], where="post",
           color=INK2, lw=0.8, zorder=2)
    a.set_xlim(0, 410)
    a.set_ylim(0, 30)
    a.set_yticks([0, 5, 10, 15, 20])
    a.set_xlabel("time per 0.5 g dose (s)  ← better")
    a.set_ylabel("|error| (mg)  ↓ better")
    a.legend(loc="lower left", bbox_to_anchor=(0.0, 1.02), ncol=3, frameon=False, handletextpad=0.2,
             columnspacing=0.9, borderaxespad=0.0, fontsize=6.5)
    a.text(-0.09, 1.30, "(a)", transform=a.transAxes, fontweight="bold", fontsize=9, va="bottom")

    # (b) repeatability of three settings: time per dose
    groups = [("hand-tuned", df[df.group == "hand"], ORANGE),
              ("corner-09", vc, MUTED), ("bo-005", vb, BLUE)]
    for k, (lab, g, col) in enumerate(groups):
        xs = np.full(len(g), k) + np.linspace(-0.12, 0.12, len(g))
        b.scatter(xs, g.t, s=14, c=col, edgecolors="white", linewidths=0.5, zorder=3)
        med = np.median(g.t)
        b.plot([k - 0.25, k + 0.25], [med, med], color=INK, lw=1.0, zorder=4)
        b.text(k, 405, f"{np.median(g['abs']):.1f} mg", ha="center", va="bottom", fontsize=6.3, color=INK2)
    b.text(1, 432, "median |error|", ha="center", va="bottom", fontsize=6.3, color=INK2)
    b.set_xticks(range(3), ["hand-\ntuned", "corner-\n09", "bo-005"], rotation=0, fontsize=6.5)
    b.set_xlim(-0.6, 2.6)
    b.set_ylim(0, 400)
    b.set_ylabel("time per dose (s)")
    b.text(-0.42, 1.30, "(b)", transform=b.transAxes, fontweight="bold", fontsize=9, va="bottom")

    # (c) cup mass over time: hand-tuned vs recommended
    for lab, col, name, xy, ha in (("rebaseline-01", ORANGE, "hand-tuned", (245, 455), "right"),
                                   (RECOMMENDED, BLUE, "recommended", (104, 528), "left")):
        u = df[df.label == lab].uuid.iloc[0]
        tr = trace(u)
        c.plot(tr["t"], tr["m"], color=col, lw=1.1, drawstyle="steps-post")
        c.text(xy[0], xy[1], f"{name}, {tr['t'][-1]:.0f} s", color=INK, fontsize=6.5, va="top", ha=ha)
    c.axhline(500, color=INK2, lw=0.6, ls=(0, (3, 2)))
    c.set_xlim(0, 250)
    c.set_ylim(0, 560)
    c.set_xlabel("time since the dose started (s)")
    c.set_ylabel("powder in the cup (mg)")
    c.text(-0.3, 1.06, "(c)", transform=c.transAxes, fontweight="bold", fontsize=9, va="bottom")

    # (d) what the optimizer changed, each setting on its own search range
    camp = json.load(open(SALT / "campaign.json"))
    base = camp["baseline_params"]
    recp = df[df.label == RECOMMENDED].iloc[0]
    names = [("bulk_tilt_deg", "bulk tilt (°)"), ("bulk_rpm", "bulk speed (rpm)"),
             ("trickle_start_remaining_g", "switch to trickle (g to go)"),
             ("trickle_tilt_deg", "trickle tilt (°)"), ("tap_tilt_deg", "tap tilt (°)"),
             ("tolerance_g", "stop within (mg)")]
    bounds = {p["name"]: p["bounds"] for p in camp["search_space"] if p["type"] == "range"}
    for k, (key, lab) in enumerate(names):
        lo, hi = bounds[key]
        y = len(names) - 1 - k
        d.plot([0, 1], [y, y], color=GRID, lw=3, solid_capstyle="round", zorder=0)
        b0, r0 = (base[key] - lo) / (hi - lo), (recp[key] - lo) / (hi - lo)
        d.plot([b0, r0], [y, y], color=MUTED, lw=0.8, zorder=1)
        d.scatter([b0], [y], s=26, c=ORANGE, zorder=3, edgecolors="white", linewidths=0.6)
        d.scatter([r0], [y], s=26, c=BLUE, zorder=3, edgecolors="white", linewidths=0.6)
        scale = 1000 if key == "tolerance_g" else 1
        d.text(-0.04, y, lab, ha="right", va="center", fontsize=6.8, color=INK)
        d.text(1.04, y, f"{lo*scale:g}–{hi*scale:g}", ha="left", va="center", fontsize=6.3, color=MUTED)
    d.text(0.0, len(names) - 0.35, "hand-tuned", color=ORANGE, fontsize=6.8, ha="left", va="bottom")
    d.text(1.0, len(names) - 0.35, "recommended (bo-005)", color=BLUE, fontsize=6.8, ha="right", va="bottom")
    d.set_xlim(-0.02, 1.02)
    d.set_ylim(-0.6, len(names) + 0.1)
    d.set_xticks([0, 1], ["low end of range", "high end of range"], fontsize=6.5)
    d.set_yticks([])
    d.spines["left"].set_visible(False)
    d.text(-0.78, 1.06, "(d)", transform=d.transAxes, fontweight="bold", fontsize=9, va="bottom")
    save(fig, "fig3_salt_campaign")


# ---------------------------------------------------------- powders, real
def fig_powders() -> None:
    df = pd.read_csv(DATA / "powders" / "versatility_data.csv")
    flows = df[df.flows].sort_values("mg_per_turn")
    nof = df[~df.flows]
    order = list(nof.name) + list(flows.name)
    y = {n: k for k, n in enumerate(order)}
    fig, (a, b) = plt.subplots(1, 2, figsize=(DOUBLE, 3.1), sharey=True,
                               gridspec_kw=dict(wspace=0.08, width_ratios=[1.15, 1]))
    col = {"research": ORANGE, "surrogate": BLUE}
    mk = {"research": "s", "surrogate": "o"}
    a.axhspan(-0.6, len(nof) - 0.4, color=BAND, lw=0, zorder=0)
    a.text(12, len(nof) / 2 - 0.5, "no measurable flow", color=INK2, fontsize=7, va="center", style="italic")
    for _, r in flows.iterrows():
        a.errorbar(r.mg_per_turn, y[r["name"]], xerr=r.se_mg, fmt=mk[r.track], ms=5, color=col[r.track],
                   ecolor=INK2, elinewidth=0.6, capsize=1.5, markeredgecolor="white", markeredgewidth=0.6,
                   zorder=3)
    a.set_xscale("log")
    a.set_xlim(6, 400)
    a.set_xticks([10, 30, 100, 300], ["10", "30", "100", "300"])
    a.set_yticks(range(len(order)), order)
    a.set_xlabel("powder delivered per auger revolution (mg/rev)\n30 rpm, 22.5° tilt, fixed settings")
    a.grid(axis="x", color=GRID, lw=0.6, zorder=0)
    a.annotate("", xy=(231, len(order) - 0.2), xytext=(9.6, len(order) - 0.2),
               arrowprops=dict(arrowstyle="<|-|>", color=INK2, lw=0.7, shrinkA=0, shrinkB=0))
    a.text(47, len(order) + 0.05, "24-fold range", ha="center", va="bottom", fontsize=7, color=INK)
    a.set_ylim(-0.6, len(order) + 0.6)
    a.text(0.99, 0.02, "research-relevant", color=ORANGE, transform=a.transAxes, ha="right", fontsize=7)
    a.text(0.99, 0.09, "food-safe stand-in", color=BLUE, transform=a.transAxes, ha="right", fontsize=7)
    panel(a, "a", x=-0.47)

    b.axvspan(0.95, 1.05, color="#e6f4e6", lw=0, zorder=0)
    b.axvline(1.0, color=INK2, lw=0.6)
    for _, r in df.iterrows():
        yy = y[r["name"]]
        if r.doses_1g == 0 or pd.isna(r.min_delivered_g):
            b.text(0.52, yy, "not dosed at 1 g", va="center", fontsize=6.5, color=MUTED, style="italic")
            continue
        lo, hi = r.min_delivered_g, r.max_delivered_g
        inside = r.within_5pct_1g == r.doses_1g
        b.plot([lo, hi], [yy, yy], color=col[r.track], lw=2.2, solid_capstyle="round", zorder=3)
        b.plot([lo, hi], [yy, yy], mk[r.track], ms=4, color=col[r.track] if inside else "white",
               markeredgecolor=col[r.track], markeredgewidth=0.8, zorder=4)
        b.text(1.12, yy, f"{r.within_5pct_1g}/{r.doses_1g}", va="center", fontsize=6.5, color=INK2)
    b.text(1.12, len(order) + 0.05, "within ±5%", va="bottom", fontsize=6.5, color=INK2)
    b.set_xlim(0.5, 1.22)
    b.set_xlabel("delivered mass for a 1 g request (g)\nclosed loop; band = ±5%")
    b.grid(axis="x", color=GRID, lw=0.6, zorder=0)
    b.tick_params(axis="y", length=0)
    panel(b, "b", x=-0.04)
    save(fig, "fig2_powders")


# ------------------------------------------------- multi-task, synthetic
def fig_multitask_placeholder() -> None:
    rng = np.random.default_rng(179)
    n = np.arange(1, 41)
    fig, (a, b) = plt.subplots(1, 2, figsize=(DOUBLE, 2.7), gridspec_kw=dict(wspace=0.35))
    curves = {"single-task (this work, salt)": (MUTED, 22.0), "multi-task, 3 earlier powders": (BLUE, 11.0),
              "multi-task, 8 earlier powders": (AQUA, 6.0)}
    for lab, (colr, tau) in curves.items():
        reps = np.array([0.82 * (1 - np.exp(-n / (tau * rng.uniform(0.8, 1.2)))) + rng.normal(0, 0.02, n.size)
                         for _ in range(10)])
        reps = np.maximum.accumulate(np.clip(reps, 0, 1), axis=1)
        mu, sd = reps.mean(0), reps.std(0)
        a.fill_between(n, mu - sd, mu + sd, color=colr, alpha=0.18, lw=0)
        a.plot(n, mu, color=colr, lw=1.2)
        a.text(n[-1] + 0.6, mu[-1], lab, color=INK, fontsize=6.5, va="center")
    a.axhline(0.7, color=INK2, lw=0.6, ls=(0, (3, 2)))
    a.text(1, 0.72, "target: 70% of the best known hypervolume", fontsize=6.5, color=INK2)
    a.set_xlim(0, 62)
    a.set_ylim(0, 1)
    a.set_xlabel("doses on the new powder")
    ylabel_top(a, "hypervolume, fraction of best known")
    synthetic(a)
    panel(a, "a")

    names = ["NaCl", "Na$_2$SO$_4$", "CaLac", "AlSi10Mg", "Si 75–150", "316L", "Ti", "Al 4047"]
    k = len(names)
    z = rng.normal(size=(k, 2))
    z[[3, 5, 6, 7]] += [2.0, 0.6]
    z[[0, 1, 2]] += [-1.0, -0.4]
    dist = np.sqrt(((z[:, None, :] - z[None, :, :]) ** 2).sum(-1))
    corr = np.exp(-dist ** 2 / 3.0)
    im = b.imshow(corr, cmap="Blues", vmin=0, vmax=1)
    b.set_xticks(range(k), names, rotation=45, ha="right", fontsize=6.5)
    b.set_yticks(range(k), names, fontsize=6.5)
    b.spines[:].set_visible(False)
    cb = fig.colorbar(im, ax=b, fraction=0.046, pad=0.04)
    cb.set_label("learned task correlation", fontsize=7)
    cb.outline.set_visible(False)
    synthetic(b)
    panel(b, "b", x=-0.42)
    save(fig, "fig4_multitask_placeholder")


# --------------------------------------------------------- DEM, mixed
def fig_dem() -> None:
    fig, axs = plt.subplots(1, 3, figsize=(DOUBLE, 2.6), gridspec_kw=dict(wspace=0.45))
    a, b, c = axs
    # (a) real: PR #180 rig validation, 29k salt grains, no calibration
    tilt = np.array([0.0, 22.5, 27.5, 45.0])
    sim = np.array([33, 71, 105, 153])
    meas = np.array([28, 108, 105, 195])
    meas_lo = np.array([28, 106, 94, 195])
    meas_hi = np.array([28, 110, 116, 195])
    a.vlines(tilt, meas_lo, meas_hi, color=ORANGE, lw=1.2)
    a.scatter(tilt, meas, s=26, c=ORANGE, marker="s", edgecolors="white", linewidths=0.6, zorder=3)
    a.scatter(tilt, sim, s=26, c=BLUE, marker="o", edgecolors="white", linewidths=0.6, zorder=3)
    a.text(46.5, 195, "measured", color=ORANGE, fontsize=6.5, va="center")
    a.text(46.5, 150, "DEM", color=BLUE, fontsize=6.5, va="center")
    a.set_xlim(-3, 56)
    a.set_ylim(0, 220)
    a.set_xticks([0, 22.5, 27.5, 45], ["0", "22.5", "27.5", "45"])
    a.set_xlabel("auger tilt (°)")
    ylabel_top(a, "salt delivered (mg/rev)")
    panel(a, "a", x=-0.3)

    # (b) synthetic: delivery surface over cohesion and friction
    ced = np.linspace(0, 1.0, 60)     # cohesion energy density (normalised)
    mu = np.linspace(0.2, 0.8, 60)    # sliding friction coefficient
    C, M = np.meshgrid(ced, mu)
    Q = 160 * np.exp(-1.6 * C) * (1.25 - 0.6 * M)
    cs = b.contourf(C, M, Q, levels=10, cmap="Blues_r")
    b.contour(C, M, Q, levels=[60, 105, 150], colors=INK2, linewidths=0.6)
    b.set_xlabel("cohesion energy density (norm.)")
    ylabel_top(b, "sliding friction coefficient")
    cb = fig.colorbar(cs, ax=b, fraction=0.05, pad=0.03)
    cb.set_label("mg/rev", fontsize=7)
    cb.outline.set_visible(False)
    synthetic(b)
    panel(b, "b", x=-0.3)

    # (c) synthetic: posterior for one powder given tilt-sweep data
    rng = np.random.default_rng(7)
    samp = rng.multivariate_normal([0.35, 0.52], [[0.004, -0.0025], [-0.0025, 0.0036]], 1500)
    c.scatter(samp[:, 0], samp[:, 1], s=2, c=BLUE, alpha=0.25, edgecolors="none")
    c.scatter([0.35], [0.52], s=30, c=INK, marker="+", zorder=3)
    c.set_xlim(0, 1)
    c.set_ylim(0.2, 0.8)
    c.set_xlabel("cohesion energy density (norm.)")
    ylabel_top(c, "sliding friction coefficient")
    c.text(0.52, 0.72, "posterior for one\npowder from its\ntilt sweep", fontsize=6.5, color=INK2)
    synthetic(c)
    panel(c, "c", x=-0.3)
    save(fig, "fig5_dem")


# ------------------------------- property links: (a, b) real, (c) synthetic
SHORT = {"salt": "NaCl", "white-rice-flour": "white rice flour", "brown-rice-flour": "brown rice flour",
         "sodium-alginate": "Na alginate", "calcium-lactate": "Ca lactate", "carboxymethyl-cellulose": "CMC",
         "xanthan-gum": "xanthan", "sodium-sulfate": "Na$_2$SO$_4$", "silicon-110-200": "Si 75–150 µm",
         "silicon-325": "Si <44 µm", "alsi10mg": "AlSi10Mg", "barium-chloride": "BaCl$_2$"}


def fig_properties() -> None:
    from scipy.stats import spearmanr

    resp = pd.read_csv(DATA / "powders" / "battery_responses.csv")
    lit = pd.read_csv(DATA / "powders" / "literature_powder_properties.csv")
    df = resp.merge(lit, on="powder_id")
    aor_col = next(c for c in lit.columns if "repose" in c.lower() or c.lower().startswith("aor"))
    fig, axs = plt.subplots(1, 3, figsize=(DOUBLE, 2.55), gridspec_kw=dict(wspace=0.5))
    a, b, c = axs

    # (a) literature angle of repose vs delivery at 45 deg tube tilt (servo 90 deg)
    ff = df.ff90_mg_per_rev.clip(lower=0.1)
    metal = df.batch.str.startswith("metal")
    for m, colr, mk in ((~metal, BLUE, "o"), (metal, ORANGE, "s")):
        a.scatter(df.loc[m, aor_col], ff[m], s=22, c=colr, marker=mk, edgecolors="white", linewidths=0.6,
                  zorder=3)
    rho, p = spearmanr(df[aor_col], np.log10(ff))
    for _, r in df.iterrows():
        if r.powder_id in ("alsi10mg", "silicon-325", "sodium-alginate", "salt", "brown-rice-flour"):
            a.annotate(SHORT[r.powder_id], (r[aor_col], max(r.ff90_mg_per_rev, 0.1)), xytext=(4, 2),
                       textcoords="offset points", fontsize=6.3, color=INK2)
    a.set_yscale("log")
    a.set_ylim(0.08, 800)
    a.set_xlim(27, 50)
    a.set_xlabel("angle of repose, literature value (°)")
    ylabel_top(a, "delivered at 45° tilt (mg/rev)")
    a.text(0.97, 0.97, f"Spearman ρ = {rho:.2f}\nn = {len(df)}", transform=a.transAxes, ha="right", va="top",
           fontsize=6.5, color=INK)
    panel(a, "a", x=-0.32)

    # (b) tilt response of each conveying powder: the "fingerprint"
    tilts = np.array([0.0, 22.5, 45.0])
    hi = {"alsi10mg": ORANGE, "salt": BLUE, "carboxymethyl-cellulose": AQUA}
    for _, r in df[df.conveys].iterrows():
        yv = np.array([r.ff0_mg_per_rev, r.ff45_mg_per_rev, r.ff90_mg_per_rev]).clip(min=0.1)
        colr = hi.get(r.powder_id, "#c9c7c1")
        b.plot(tilts, yv, "-o", ms=2.5, color=colr, lw=1.0 if r.powder_id in hi else 0.7,
               zorder=3 if r.powder_id in hi else 2)
        if r.powder_id in hi:
            b.text(46.5, yv[-1], SHORT[r.powder_id], color=INK, fontsize=6.3, va="center")
    b.set_yscale("log")
    b.set_ylim(0.3, 800)
    b.set_xlim(-2, 62)
    b.set_xticks([0, 22.5, 45], ["0", "22.5", "45"])
    b.set_xlabel("auger tilt (°), 30 rpm")
    ylabel_top(b, "delivered (mg/rev)")
    panel(b, "b", x=-0.32)

    # (c) synthetic: what the paper will test
    rng = np.random.default_rng(42)
    k = 10
    coh = np.sort(rng.uniform(0.05, 0.95, k))
    ffc = 12 * np.exp(-2.2 * coh) + rng.normal(0, 0.5, k)
    c.scatter(coh, ffc, s=22, c=BLUE, edgecolors="white", linewidths=0.6, zorder=3)
    c.set_xlabel("cohesion inferred from dosing (norm.)")
    ylabel_top(c, "shear-cell flow function $ff_c$")
    synthetic(c)
    panel(c, "c", x=-0.32)
    save(fig, "fig6_properties")


# ------------------------------------------------- overview schematic
def box(ax, xy, w, h, text, fc, ec=MUTED, fs=7, bold=False):
    ax.add_patch(FancyBboxPatch(xy, w, h, boxstyle="round,pad=0.012,rounding_size=0.02", fc=fc, ec=ec,
                                lw=0.7, transform=ax.transAxes))
    ax.text(xy[0] + w / 2, xy[1] + h / 2, text, ha="center", va="center", fontsize=fs, color=INK,
            transform=ax.transAxes, fontweight="bold" if bold else "normal", linespacing=1.25)


def arrow(ax, p, q, col=INK2, dashed=False):
    ax.add_patch(FancyArrowPatch(p, q, transform=ax.transAxes, arrowstyle="-|>", mutation_scale=8,
                                 color=col, lw=0.8, ls=(0, (3, 2)) if dashed else "-"))


def fig_overview() -> None:
    df = salt_doses()
    tr = trace(df[df.label == RECOMMENDED].uuid.iloc[0])
    fig = plt.figure(figsize=(DOUBLE, 3.5))
    a = fig.add_axes([0.06, 0.16, 0.36, 0.70])
    stage_col = {"bulk": "#dbe8fa", "trickle": "#eef4fd", "tap": "#f6f5f1"}
    for p, (t0, t1) in tr["stage"].items():
        a.axvspan(t0, t1, color=stage_col[p], lw=0, zorder=0)
        a.text((t0 + t1) / 2, 545, p, ha="center", va="bottom", fontsize=6.5, color=INK2)
    a.plot(tr["t"], tr["m"], color=BLUE, lw=1.1, drawstyle="steps-post", zorder=3)
    a.axhline(500, color=INK2, lw=0.6, ls=(0, (3, 2)))
    a.set_xlim(0, tr["t"][-1] + 2)
    a.set_ylim(0, 600)
    a.set_xlabel("time (s)")
    ylabel_top(a, "powder in the cup (mg)")
    a.text(0.98, 0.30, "tilt, speed and\ntap settings per stage\nare the search space",
           transform=a.transAxes, ha="right", fontsize=6.5, color=INK2)
    panel(a, "a", x=-0.14, y=1.07)

    s = fig.add_axes([0.47, 0.02, 0.53, 0.94])
    s.axis("off")
    box(s, (0.00, 0.70), 0.27, 0.20, "auger doser\non a 0.1 mg\nbalance", BLUE_L, bold=True)
    box(s, (0.36, 0.70), 0.28, 0.20, "dose record\ntime, error,\ntaps, mg/rev", "#ffffff")
    box(s, (0.72, 0.70), 0.28, 0.20, "multi-objective\nBO per powder\n(Sec. 3.2)", BLUE_L)
    box(s, (0.72, 0.38), 0.28, 0.20, "multi-task BO\nacross powders\n(Sec. 3.3)", "#ffffff", ec=ORANGE)
    box(s, (0.36, 0.38), 0.28, 0.20, "DEM twin with\nmeasured PSD\n(Sec. 3.4)", BLUE_L)
    box(s, (0.00, 0.38), 0.27, 0.20, "effective cohesion\nand friction", "#ffffff", ec=ORANGE)
    box(s, (0.00, 0.06), 0.27, 0.20, "Hall flow,\nshear cell", "#ffffff", ec=ORANGE)
    box(s, (0.36, 0.06), 0.64, 0.20, "spreading and packing in AM\n(Sec. 3.5, outlook)", "#ffffff", ec=ORANGE)
    arrow(s, (0.27, 0.80), (0.36, 0.80))
    arrow(s, (0.64, 0.80), (0.72, 0.80))
    arrow(s, (0.86, 0.70), (0.86, 0.58), dashed=True)
    arrow(s, (0.50, 0.70), (0.50, 0.58))
    arrow(s, (0.36, 0.48), (0.27, 0.48))
    arrow(s, (0.135, 0.38), (0.135, 0.26), dashed=True)
    arrow(s, (0.27, 0.16), (0.36, 0.16), dashed=True)
    s.text(0.86, 0.94, "", transform=s.transAxes)
    s.text(0.0, 0.97, "(b)", fontweight="bold", fontsize=9, transform=s.transAxes, va="bottom")
    s.text(1.0, 0.985, "solid: done   dashed / orange outline: in progress",
           ha="right", va="bottom", fontsize=6.5, color=INK2, transform=s.transAxes)
    s.set_xlim(0, 1)
    s.set_ylim(0, 1)
    save(fig, "fig1_overview")


def fig_graphical_abstract() -> None:
    fig = plt.figure(figsize=(5.31, 2.17))  # 531 x 1328 px at 250 dpi wide format
    s = fig.add_axes([0, 0, 1, 1])
    s.axis("off")
    box(s, (0.02, 0.30), 0.20, 0.40, "auger doser\n+ balance", BLUE_L, bold=True, fs=8)
    box(s, (0.28, 0.55), 0.22, 0.30, "Bayesian\ncalibration", "#ffffff", fs=8)
    box(s, (0.28, 0.15), 0.22, 0.30, "DEM twin", "#ffffff", fs=8)
    box(s, (0.56, 0.30), 0.20, 0.40, "cohesion,\nfriction", "#ffffff", ec=ORANGE, fs=8)
    box(s, (0.82, 0.30), 0.16, 0.40, "AM\nfeedstock\nbehaviour", "#ffffff", ec=ORANGE, fs=8)
    arrow(s, (0.22, 0.55), (0.28, 0.68))
    arrow(s, (0.22, 0.45), (0.28, 0.32))
    arrow(s, (0.50, 0.68), (0.56, 0.55))
    arrow(s, (0.50, 0.32), (0.56, 0.45))
    arrow(s, (0.76, 0.50), (0.82, 0.50), dashed=True)
    s.text(0.5, 0.94, "Every calibration of a powder doser is also a measurement of the powder",
           ha="center", va="center", fontsize=8.5, color=INK)
    save(fig, "graphical_abstract")


if __name__ == "__main__":
    fig_overview()
    fig_powders()
    fig_salt_campaign()
    fig_multitask_placeholder()
    fig_dem()
    fig_properties()
    fig_graphical_abstract()
