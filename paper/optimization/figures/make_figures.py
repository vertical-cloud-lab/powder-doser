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


def synthetic(ax, text: str = "SYNTHETIC DATA", top: bool = False) -> None:
    """Diagonal, light watermark: readable, but out of the way of the marks.
    top=True draws it above filled plots (contours, images), where it would be hidden."""
    ax.text(0.5, 0.5, text, transform=ax.transAxes, rotation=28, ha="center", va="center",
            fontsize=15, fontweight="bold", color="#c0392b" if not top else "white",
            alpha=0.16 if not top else 0.55, zorder=10 if top else 0)


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
    save(fig, "fig2_salt_campaign")


# --------------------------------------------- second salt campaign (margin)
RES = ROOT / "analysis" / "results"
SNAP = DATA / "opt_trials" / "opt_trials_20260929-20261020.jsonl"
ST_STYLE = {"ok": (BLUE, "o", True), "overshoot": (ORANGE, "^", True), "cycle-budget": (INK, "X", True),
            "stalled": (INK, "X", True), "timeout": (INK, "X", True), "fw-error": (MUTED, "o", False),
            "not-tared": (MUTED, "s", False)}


def _status_marker(ax, x, y, status, s=22, z=3):
    col, mk, filled = ST_STYLE.get(status, (MUTED, "o", False))
    ax.scatter([x], [y], s=s, marker=mk, c=col if filled else "white", edgecolors=col if not filled else "white",
               linewidths=0.7 if not filled else 0.5, zorder=z)


def snap_docs() -> dict:
    return {d["trial_uuid"]: d for d in (json.loads(l) for l in open(SNAP))}


def snap_trace(doc: dict):
    tel = doc["telemetry"]
    cols = tel["header"].split(",")
    rows = [dict(zip(cols, r.split(","))) for r in tel["rows"]]
    t = np.array([float(r["t_s"]) for r in rows])
    m = np.array([float(r["z_g"]) if r["z_g"] not in ("", None) else np.nan for r in rows])
    ph = [r["phase"] for r in rows]
    i0 = next(i for i, p in enumerate(ph) if p == "bulk")
    return t[i0:] - t[i0], m[i0:] - (m[i0] if np.isfinite(m[i0]) else 0.0)


def fig_margin_campaign() -> None:
    st = json.load(open(RES / "stats.json"))
    pairs = pd.read_csv(RES / "paired_corners_margin.csv")
    mr = pd.read_csv(RES / "doses_margin_20261013.csv")
    feed = pd.read_csv(RES / "feed_40deg_20rpm.csv")
    fig = plt.figure(figsize=(DOUBLE, 2.75))
    gs = fig.add_gridspec(1, 3, width_ratios=[0.8, 0.8, 1.45], wspace=0.55)
    a, b, c = (fig.add_subplot(gs[0, k]) for k in range(3))

    # (a) the same 16 screening corners at a 35 mg margin (29 Sep) and a 0 mg margin (13 Oct)
    for _, r in pairs.iterrows():
        a.plot([0, 1], [r.t_35, r.t_0], color=GRID if not (r.status_35 == r.status_0 == "ok") else "#b9cfee",
               lw=0.8, zorder=1)
        _status_marker(a, 0, r.t_35, r.status_35)
        _status_marker(a, 1, r.t_0, r.status_0)
    P = st["margin"]["pairs"]
    a.set_xticks([0, 1], ["35 mg\n29 Sep", "0 mg\n13 Oct"])
    a.set_xlim(-0.35, 1.35)
    a.set_ylim(0, 520)
    a.set_yticks([0, 100, 200, 300, 400])
    ylabel_top(a, "time per 0.5 g dose (s)")
    a.set_xlabel("hand-over margin")
    a.text(0.5, 0.97, f"{P['n_both_ok']} pairs ok at both:\nmedian {P['dt_median_s']:+.0f} s, "
           f"p = {P['wilcoxon_time']['p']:.2f}", transform=a.transAxes, ha="center", va="top", fontsize=6.0,
           color=INK2)
    panel(a, "a", x=-0.42)

    # (b) bulk feed of salt at 40 deg, 20 rpm, by session (one auger fill since 29 Sep)
    dates = sorted(feed.date.unique())
    lab = {"2026-09-29": "29\nSep", "2026-10-06": "6\nOct", "2026-10-13": "13\nOct", "2026-10-15": "15\nOct"}
    for k, d_ in enumerate(dates):
        v = feed[feed.date == d_].bulk_rate_mgps.values
        xs = k + np.linspace(-0.13, 0.13, len(v))
        col = ORANGE if d_ == "2026-10-15" else BLUE
        b.scatter(xs, v, s=12, c=col, edgecolors="white", linewidths=0.4, zorder=3)
        med = np.median(v)
        b.plot([k - 0.25, k + 0.25], [med, med], color=INK, lw=1.0, zorder=4)
        b.text(k, 61, f"n={len(v)}", ha="center", fontsize=6.0, color=INK2)
    b.set_xticks(range(len(dates)), [lab.get(d_, d_) for d_ in dates], fontsize=6.5)
    b.set_ylim(0, 66)
    b.set_xlim(-0.6, len(dates) - 0.4)
    ylabel_top(b, "salt bulk feed (mg/s)")
    b.set_xlabel("session; 40° tilt, 20 rpm")
    panel(b, "b", x=-0.42)

    # (c) every dose of the margin campaign, in order
    day = mr.date.values
    brk = int(np.argmax(day == "2026-10-15"))
    c.axvspan(brk - 0.5, len(mr) - 0.5, color="#fbeee8", lw=0, zorder=0)
    c.text(brk + 0.3, 500, "15 Oct: feed collapsed", fontsize=6.3, color=ORANGE, va="bottom")
    c.text(0.3, 500, "13 Oct", fontsize=6.3, color=INK2, va="bottom")
    for _, r in mr.iterrows():
        _status_marker(c, r.i, min(r.t, 470), r.status, s=18)
    c.axvline(17.5, color=MUTED, lw=0.6, ls=(0, (3, 2)))
    c.text(8.5, 250, "screening\ncorners", ha="center", fontsize=6.3, color=INK2)
    c.text(18.2, 250, "optimizer", ha="left", fontsize=6.3, color=INK2)
    c.set_xlim(-1, len(mr))
    c.set_ylim(0, 530)
    c.set_yticks([0, 100, 200, 300, 400])
    c.set_xlabel("dose number")
    ylabel_top(c, "time per dose (s)")
    # legend for status markers
    hand = []
    for name, labx in (("ok", "ok"), ("overshoot", "overshoot"), ("stalled", "jam or stall"),
                       ("fw-error", "firmware or tare error")):
        col, mk, filled = ST_STYLE[name]
        hand.append(plt.Line2D([], [], ls="", marker=mk, ms=4.5, mfc=col if filled else "white", mec=col if not filled
                               else "white", mew=0.6, label=labx))
    c.legend(handles=hand, loc="upper left", bbox_to_anchor=(0.0, -0.22), ncol=4, frameon=False, fontsize=6.3,
             handletextpad=0.2, columnspacing=0.8)
    panel(c, "c", x=-0.16)
    save(fig, "fig3_margin_campaign")


# ------------------------------------------------ metal feedstock: flow signal
def _rate_trace(doc: dict, win: float = 6.0):
    """Delivery rate (mg/s) against time: mass gained over a trailing window of `win` s."""
    t, m = snap_trace(doc)
    ok = np.isfinite(m)
    t, m = t[ok], m[ok]
    tt = np.arange(win, t[-1], 1.0)
    r = (np.interp(tt, t, m) - np.interp(tt - win, t, m)) / win * 1e3
    return tt, np.clip(r, 0.05, None)


def fig_metal_feedstock() -> None:
    docs = snap_docs()
    met = pd.read_csv(RES / "doses_metal_feedstock.csv")
    sal = pd.read_csv(RES / "doses_salt_20260929.csv")
    prod = pd.read_csv(RES / "doses_production_salt.csv")
    fig = plt.figure(figsize=(DOUBLE, 2.9))
    gs = fig.add_gridspec(1, 3, width_ratios=[1.35, 1.0, 0.85], wspace=0.38)
    a, b, d = (fig.add_subplot(gs[0, k]) for k in range(3))

    # (a) bulk feed at the recommended bulk settings (40 deg, 100 rpm, 2 Hz taps), dose by dose
    items = []
    vb = sal[sal.group == "val-bo"].bulk_rate_mgps.dropna().values
    items.append(("salt\n×8", vb, BLUE, "o"))
    p15 = prod[prod.target_g == 1.5].bulk_rate_mgps.values
    items.append(("salt\n×1", p15, BLUE, "o"))
    al = met[met.powder == "alsi10mg"].bulk_rate_mgps.values
    items.append(("AlSi\n10Mg", al, ORANGE, "s"))
    a47 = met[met.powder.str.startswith("al4047") & (met["mode"] == "production")].dropna(subset=["bulk_rate_mgps"])
    lab47 = {"2026-09-30T21:21": "30\nSep", "2026-10-19T23:24": "19\nOct", "2026-10-20T01:20": "60°\n*",
             "2026-10-20T01:23": "75°\n*", "2026-10-20T21:07": "20 Oct\n#1", "2026-10-20T21:30": "#2",
             "2026-10-20T21:36": "#3", "2026-10-20T22:15": "after\nclear-\ning"}
    for _, r in a47.iterrows():
        if r.utc == "2026-09-30T21:50" or r.bulk_tilt != 40.0:
            continue  # the 0.32 g bulk-only top-up, and the two unclog tries at 60 and 75 deg
        items.append((lab47.get(r.utc, r.utc[5:10]), np.array([r.bulk_rate_mgps]), "#8c5a2b", "D"))
    for k, (lab_, v, col, mk) in enumerate(items):
        xs = k + (np.linspace(-0.15, 0.15, len(v)) if len(v) > 1 else np.zeros(1))
        a.scatter(xs, v, s=14 if len(v) > 1 else 20, c=col, marker=mk, edgecolors="white", linewidths=0.4,
                  zorder=3)
    a.set_yscale("log")
    a.set_ylim(0.08, 500)
    a.set_xticks(range(len(items)), [i[0] for i in items], fontsize=6.0)
    a.set_xlim(-0.6, len(items) - 0.4)
    a.axvspan(2.5, len(items) - 0.4, color="#f6efe8", lw=0, zorder=0)
    a.text(2.75, 280, "Al 4047, lab-atomized, unsieved", fontsize=6.0, color="#8c5a2b", va="center")
    ylabel_top(a, "bulk feed (mg/s)")
    a.set_xlabel("dose; all at 40°, 100 rpm, 2 Hz taps")
    panel(a, "a", x=-0.13)

    # (b) delivery rate within a dose: steady for AlSi10Mg, decaying for Al 4047 until it was cleared
    sets = [("alsi10mg", "AlSi10Mg (8 g request)", ORANGE, "-"),
            ("2026-10-20T21:07", "Al 4047, 20 Oct #1", "#8c5a2b", "-"),
            ("2026-10-20T21:36", "Al 4047, #3", "#c9a27e", "-"),
            ("2026-10-20T22:15", "Al 4047 after clearing", "#8c5a2b", (0, (2.5, 1.2)))]
    for key, lab_, col, ls in sets:
        if key == "alsi10mg":
            doc = next(d_ for d_ in docs.values() if d_["powder_id"] == "alsi10mg")
        else:
            doc = next(d_ for d_ in docs.values() if d_["started_utc"][:16] == key and d_["mode"] == "production")
        tt, rr = _rate_trace(doc)
        keep = tt <= (54 if key == "alsi10mg" else 400)
        b.plot(tt[keep], rr[keep], color=col, lw=1.0, ls=ls, label=lab_)
    b.set_yscale("log")
    b.set_ylim(0.3, 400)
    b.set_xlim(0, 300)
    b.set_xlabel("time since the dose started (s)")
    ylabel_top(b, "delivery rate (mg/s)")
    b.legend(loc="upper right", frameon=False, fontsize=5.8, handlelength=1.6)
    panel(b, "b", x=-0.2)

    # (c) one setting, many targets: salt at bo-005's settings, 5 mg to 10 g (one dose each)
    ps = prod.sort_values("target_g")
    d.scatter(ps.target_g, ps.err_mg.abs(), s=22, c=BLUE, edgecolors="white", linewidths=0.6, zorder=3)
    for _, r in ps.iterrows():
        below = r.target_g < 0.01 or abs(r.err_mg) < 1
        dx = 12 if r.target_g < 0.01 else 0
        d.annotate(f"{r.t_s:.0f} s", (r.target_g, abs(r.err_mg)), xytext=(dx, -10 if below else 5),
                   textcoords="offset points", fontsize=5.8, color=INK2, ha="center")
    d.axhline(3.0, color=INK2, lw=0.6, ls=(0, (3, 2)))
    d.text(19, 3.12, "stopping band ±3 mg", fontsize=5.8, color=INK2, va="bottom", ha="right")
    d.set_xscale("log")
    d.set_xlim(0.003, 20)
    d.set_ylim(0, 4.4)
    d.set_xlabel("target (g); salt, settings bo-005")
    ylabel_top(d, "|error| (mg)")
    panel(d, "c", x=-0.22)
    save(fig, "fig4_metal_feedstock")

# ------------------------------------------------- multi-task, synthetic
def fig_multitask_placeholder() -> None:
    rng = np.random.default_rng(179)
    n = np.arange(1, 41)
    fig, (a, b) = plt.subplots(1, 2, figsize=(DOUBLE, 2.7), gridspec_kw=dict(wspace=0.35))
    curves = {"single-task": (MUTED, 16.0, 0.30), "multi-task, 3 earlier powders": (BLUE, 7.0, 0.55),
              "multi-task, 8 earlier powders": (AQUA, 3.5, 0.82)}
    for lab, (colr, tau, ylab) in curves.items():
        reps = np.array([0.98 * (1 - np.exp(-n / (tau * rng.uniform(0.8, 1.2)))) + rng.normal(0, 0.015, n.size)
                         for _ in range(10)])
        reps = np.maximum.accumulate(np.clip(reps, 0, 1), axis=1)
        mu, sd = reps.mean(0), reps.std(0)
        a.fill_between(n, mu - sd, mu + sd, color=colr, alpha=0.18, lw=0)
        a.plot(n, mu, color=colr, lw=1.2, label=lab)
    a.axhline(0.9, color=INK2, lw=0.6, ls=(0, (3, 2)))
    a.text(40, 0.88, "target: 90% of best known", fontsize=6.5, color=INK2, ha="right", va="top")
    a.legend(loc="lower right", frameon=False, fontsize=6.5, handlelength=1.5)
    a.set_xlim(0, 41)
    a.set_ylim(0, 1.08)
    a.set_yticks([0, 0.2, 0.4, 0.6, 0.8, 1.0])
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
    save(fig, "fig5_multitask_placeholder")


# --------------------------------------------------------- DEM, mixed
def fig_dem() -> None:
    fig, axs = plt.subplots(1, 3, figsize=(DOUBLE, 2.6), gridspec_kw=dict(wspace=0.45))
    a, b, c = axs
    # (a) real: PR #180 rig validation, 29k salt grains, no calibration
    xk = np.arange(4)
    sim = np.array([33, 71, 105, 153])
    meas = np.array([28, 108, 105, 195])
    meas_lo = np.array([28, 106, 94, 195])
    meas_hi = np.array([28, 110, 116, 195])
    a.vlines(xk + 0.08, meas_lo, meas_hi, color=ORANGE, lw=1.2)
    a.scatter(xk + 0.08, meas, s=26, c=ORANGE, marker="s", edgecolors="white", linewidths=0.6, zorder=3)
    a.scatter(xk - 0.08, sim, s=26, c=BLUE, marker="o", edgecolors="white", linewidths=0.6, zorder=3)
    a.text(0.1, 200, "measured", color=ORANGE, fontsize=6.5, va="center")
    a.text(0.1, 182, "DEM, no fitted\nparameters", color=BLUE, fontsize=6.5, va="top")
    a.set_xlim(-0.5, 3.5)
    a.set_ylim(0, 220)
    a.set_xticks(xk, ["0°\n60", "22.5°\n90", "27.5°\n60", "45°\n60"], fontsize=6.5)
    a.set_xlabel("auger tilt and speed (rpm)")
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
    cb.ax.set_title("mg/rev", fontsize=6.5, loc="left")
    cb.outline.set_visible(False)
    synthetic(b, top=True)
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
    save(fig, "fig6_dem")


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
    offs = {"alsi10mg": (-3, 5, "left"), "silicon-325": (5, 0, "left"), "sodium-alginate": (5, 3, "left"),
            "brown-rice-flour": (-5, 5, "right")}
    for _, r in df.iterrows():
        if r.powder_id in offs:
            dx, dy, ha = offs[r.powder_id]
            a.annotate(SHORT[r.powder_id], (r[aor_col], max(r.ff90_mg_per_rev, 0.1)), xytext=(dx, dy),
                       textcoords="offset points", fontsize=6.3, color=INK2, ha=ha)
    a.set_yscale("log")
    a.set_ylim(0.08, 800)
    a.set_xlim(27, 50)
    a.set_xlabel("angle of repose, literature value (°)")
    ylabel_top(a, "delivered at 45° tilt (mg/rev)")
    a.text(0.04, 0.04, f"Spearman ρ = {rho:.2f}, n = {len(df)}", transform=a.transAxes, ha="left", va="bottom",
           fontsize=6.5, color=INK)
    panel(a, "a", x=-0.32)

    # (b) literature moisture content vs error of 1 g closed-loop doses (hand-tuned controller)
    mo = df.dropna(subset=["moisture_pct", "blockG_mean_err_mg"])
    mo = mo[mo.blockG_outcome.astype(str).str.lower().ne("nan")]
    em = mo.blockG_mean_err_mg.abs().clip(lower=0.3)
    mmet = mo.batch.str.startswith("metal")
    for m, colr, mk in ((~mmet, BLUE, "o"), (mmet, ORANGE, "s")):
        b.scatter(mo.loc[m, "moisture_pct"].clip(lower=0.01), em[m], s=22, c=colr, marker=mk,
                  edgecolors="white", linewidths=0.6, zorder=3)
    rho_m, _ = spearmanr(mo.moisture_pct, em)
    for _, r in mo.iterrows():
        if r.powder_id in ("xanthan-gum", "sodium-alginate", "alsi10mg", "salt", "white-rice-flour"):
            b.annotate(SHORT[r.powder_id], (max(r.moisture_pct, 0.01), max(abs(r.blockG_mean_err_mg), 0.3)),
                       xytext=(4, 2), textcoords="offset points", fontsize=6.3, color=INK2)
    b.set_xscale("log")
    b.set_yscale("log")
    b.set_xlim(0.006, 40)
    b.set_ylim(0.2, 800)
    b.set_xlabel("moisture content, literature value (wt%)")
    ylabel_top(b, "|error| of 1 g doses (mg)")
    b.text(0.04, 0.90, f"Spearman ρ = {rho_m:.2f}, n = {len(mo)}", transform=b.transAxes, ha="left",
           va="bottom", fontsize=6.5, color=INK)
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
    save(fig, "fig7_properties")


# ------------------------------------------------- overview schematic
def box(ax, xy, w, h, text, fc, ec=MUTED, fs=7, bold=False):
    ax.add_patch(FancyBboxPatch(xy, w, h, boxstyle="round,pad=0.012,rounding_size=0.02", fc=fc, ec=ec,
                                lw=0.7, transform=ax.transAxes))
    ax.text(xy[0] + w / 2, xy[1] + h / 2, text, ha="center", va="center", fontsize=fs, color=INK,
            transform=ax.transAxes, fontweight="bold" if bold else "normal", linespacing=1.25)


def arrow(ax, p, q, col=INK2, dashed=False):
    ax.add_patch(FancyArrowPatch(p, q, transform=ax.transAxes, arrowstyle="-|>", mutation_scale=8,
                                 color=col, lw=0.8, ls=(0, (3, 2)) if dashed else "-"))


def fig_graphical_abstract() -> None:
    """Three real results, left to right; at least 1328 x 531 px as Elsevier asks."""
    from scipy.stats import spearmanr
    sal = pd.read_csv(RES / "doses_salt_20260929.csv")
    met = pd.read_csv(RES / "doses_metal_feedstock.csv")
    resp = pd.read_csv(DATA / "powders" / "battery_responses.csv")
    lit = pd.read_csv(DATA / "powders" / "literature_powder_properties.csv")
    fig = plt.figure(figsize=(6.6, 2.64))
    fig.text(0.5, 0.965, "Every calibration of a powder doser is also a measurement of the powder",
             ha="center", va="top", fontsize=9, color=INK, fontweight="bold")
    axs = [fig.add_axes([0.08 + k * 0.32, 0.17, 0.24, 0.52]) for k in range(3)]
    a, b, c = axs
    # 1: calibration by BO beats hand tuning
    hand = sal[sal.group == "hand"].t.values
    bo = sal[sal.group == "val-bo"].t.values
    for k, (v, col) in enumerate(((hand, ORANGE), (bo, BLUE))):
        a.scatter(k + np.linspace(-0.12, 0.12, len(v)), v, s=12, c=col, edgecolors="white", linewidths=0.4, zorder=3)
        a.plot([k - 0.25, k + 0.25], [np.median(v)] * 2, color=INK, lw=1.0)
    a.set_xticks([0, 1], ["hand-\ntuned", "Bayesian\noptimized"], fontsize=6.5)
    a.set_xlim(-0.6, 1.6)
    a.set_ylim(0, 380)
    a.set_title("calibrate each powder", fontsize=7.5, color=INK, pad=16, fontweight="bold")
    ylabel_top(a, "s per 0.5 g dose (salt)")
    # 2: the same settings on three feedstocks
    vb = sal[sal.group == "val-bo"].bulk_rate_mgps.dropna().values
    al = met[met.powder == "alsi10mg"].bulk_rate_mgps.values
    a47 = met[met.powder.str.startswith("al4047") & (met["mode"] == "production") & (met.bulk_tilt == 40.0)]
    a47 = a47.dropna(subset=["bulk_rate_mgps"])
    a47 = a47[a47.utc != "2026-09-30T21:50"].bulk_rate_mgps.values
    for k, (v, col, mk) in enumerate(((vb, BLUE, "o"), (al, ORANGE, "s"), (a47, "#8c5a2b", "D"))):
        b.scatter(k + (np.linspace(-0.15, 0.15, len(v)) if len(v) > 1 else np.zeros(1)), v, s=12, c=col, marker=mk,
                  edgecolors="white", linewidths=0.4, zorder=3)
    b.set_yscale("log")
    b.set_ylim(0.8, 400)
    b.set_xticks([0, 1, 2], ["salt", "AlSi10Mg", "Al 4047\nunsieved"], fontsize=6.5)
    b.set_xlim(-0.6, 2.6)
    b.set_title("same settings, other feedstock", fontsize=7.5, color=INK, pad=16, fontweight="bold")
    ylabel_top(b, "bulk feed (mg/s)")
    # 3: records rank powders like a standard flow measure
    df = resp.merge(lit, on="powder_id")
    ff = df.ff90_mg_per_rev.clip(lower=0.1)
    metal = df.batch.str.startswith("metal")
    for m, col, mk in ((~metal, BLUE, "o"), (metal, ORANGE, "s")):
        c.scatter(df.loc[m, "angle_repose_deg"], ff[m], s=12, c=col, marker=mk, edgecolors="white", linewidths=0.4)
    rho, _ = spearmanr(df.angle_repose_deg, np.log10(ff))
    c.set_yscale("log")
    c.set_ylim(0.08, 800)
    c.set_xlim(27, 50)
    c.set_xlabel("angle of repose (°)", fontsize=6.5)
    c.text(0.04, 0.04, f"ρ = {rho:.2f}, 12 powders", transform=c.transAxes, ha="left", va="bottom", fontsize=6.3)
    c.set_title("records rank powders", fontsize=7.5, color=INK, pad=16, fontweight="bold")
    ylabel_top(c, "mg per revolution")
    for ax in axs:
        ax.tick_params(labelsize=6)
    save(fig, "graphical_abstract")


if __name__ == "__main__":
    fig_salt_campaign()
    fig_margin_campaign()
    fig_metal_feedstock()
    fig_multitask_placeholder()
    fig_dem()
    fig_properties()
    fig_graphical_abstract()
