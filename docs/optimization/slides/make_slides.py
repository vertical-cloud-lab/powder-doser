"""Slides for the salt optimization campaign (PR #166), in builds.

    python3 make_slides.py            # every slide, every version
    python3 make_slides.py pareto     # one slide

Each slide is a build: step 1 shows the least, each later step adds one
thing and greys out what came before.  For every slide and version this
writes, under ``<slide>/<version>/``:

- ``step_N.png``: the steps at 1920 x 1080, with the message;
- ``plain/step_N.png``: the same without the message, for a slide that has
  its own title (everything else is in exactly the same place);
- ``print/step_N.png``: the message steps at 300 dpi (4000 x 2250);
- ``build.gif`` (1280 x 720) and ``build.mp4`` (1920 x 1080): the steps in
  order, each held 4 s (the last 6 s), with 0.25 s cross-fades.

The data are the campaign's own files (``campaign_data.py``); every number
printed on a slide is computed from them.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
from matplotlib.patches import Rectangle

import campaign_data as cd
import slide_style as ss
from slide_style import BLUE, FAINT, FS, GREY, INK, INK2, ORANGE

HERE = Path(__file__).resolve().parent
OUT = HERE

# --------------------------------------------------------------------------- #
# Pareto front
# --------------------------------------------------------------------------- #
PARETO_STEPS = [
    "Hand-tuned settings took 3 to 6 minutes\nper 0.5 g dose of salt",
    "The optimizer tried 38 other settings\nin one unattended 2-hour run",
    "The best trade-offs between speed and accuracy\nform the Pareto front",
    "The recommended settings dose 0.5 g in under 2 minutes,\nmore accurately than hand tuning",
]
# version "model": the front is the model's (Ax, SAASBO posterior means), which
# averages over the dose-to-dose noise; the recommended settings are on it
PARETO_STEPS_MODEL = PARETO_STEPS[:2] + [
    "The model's best trade-offs between speed and accuracy\nform the Pareto front",
    PARETO_STEPS[3],
]
PARETO_RECT = [0.105, 0.215, 0.78, 0.475]
OFF_SCALE = 29.0          # linear version: doses above this many mg are drawn at the top


def _pareto_axes(fig, logy):
    ax = fig.add_axes(PARETO_RECT)
    if logy:
        ax.set_yscale("log")
        ss.style_axes(ax, (-0.13, 7.0), (0.42, 120), list(range(8)), [1, 10, 100],
                      yfmt=lambda v: f"{v:g}")
        ax.minorticks_off()
    else:
        ss.style_axes(ax, (-0.13, 7.0), (-0.9, 31.5), list(range(8)), [0, 10, 20, 30])
    ss.ylabel_top(ax, "Error (mg, \u2193 is better)", y=1.07)
    ss.xlabel(ax, "Time per 0.5 g dose (min, \u2190 is better)")
    return ax


def slide_pareto(step: int, version: str = "linear", message: bool = True):
    """version "linear": error axis 0-30 mg, the overshoots (34-83 mg) as
    triangles along the top; "model": the same, but the front is the model's
    (SAASBO posterior means from pareto.json), which averages over the noise
    between repeat doses; "log": log error axis, every dose on scale."""
    logy = version == "log"
    model = version == "model"
    steps = PARETO_STEPS_MODEL if model else PARETO_STEPS
    fig = ss.slide(steps[step - 1] if message else None)
    ax = _pareto_axes(fig, logy)
    D = cd.doses()
    for d in D:
        d["x"] = d["t"] / 60.0
    hand = [d for d in D if d["group"] == "hand"]
    other = [d for d in D if d["group"] != "hand"]
    clean = [d for d in D if d["status"] == "ok"]
    if model:
        mp = json.load(open(cd.CAMPAIGN / "pareto.json"))["model_pareto"]
        lab = {d["ax"]: d["label"] for d in D if d["ax"] is not None}
        front = cd.pareto_front([(p["predicted_means"]["t_total_s"] / 60.0,
                                  p["predicted_means"]["abs_error_mg"], lab[p["trial_index"]])
                                 for p in mp])
        on_front = set()
    else:
        front = cd.pareto_front([(d["x"], d["abs"], d["label"]) for d in clean])
        on_front = {f[2] for f in front}
    rec = [d for d in D if d["label"] in ("bo-003", cd.RECOMMENDED, "bo-006")]

    def y(v):
        return max(v, 0.5) if logy else v

    # every dose that isn't hand tuned: open circles, grey, fainter once the front is in
    if step >= 2:
        col = GREY if step == 2 else FAINT
        keep = [d for d in other if step == 2 or (d["label"] not in on_front
                                                   and not (step == 4 and d in rec))]
        on = [d for d in keep if logy or d["abs"] <= OFF_SCALE]
        offs = [d for d in keep if not logy and d["abs"] > OFF_SCALE]
        ax.scatter([d["x"] for d in on], [y(d["abs"]) for d in on], s=120, facecolor="white",
                   edgecolor=col, linewidth=2.2, zorder=3)
        ax.scatter([d["x"] for d in offs], [31.0] * len(offs), s=150, marker="^",
                   facecolor="white", edgecolor=col, linewidth=2.2, zorder=3, clip_on=False)
        if step == 2:
            ss.callout(ax, "Other settings", (309.3 / 60, y(12.1)), (5.3, y(24.5) if not logy else 45),
                       GREY)
            if offs:
                lo, hi = min(d["abs"] for d in offs), max(d["abs"] for d in offs)
                ax.text(0.7, 31.0, f"off the scale: overshot by {lo:.0f}\u2013{hi:.0f} mg",
                        fontsize=FS, color=GREY, va="center", ha="left")

    # hand tuned, always in orange
    ax.scatter([d["x"] for d in hand], [y(d["abs"]) for d in hand], s=170, color=ORANGE,
               edgecolor="white", linewidth=1.8, zorder=5)
    if step in (1, 4):
        ss.callout(ax, "Hand-tuned", (252 / 60, y(4.7)), (4.37, y(9.6) if not logy else 14), ORANGE)

    if step >= 3:
        fx, fy = [f[0] for f in front], [y(f[1]) for f in front]
        a = 1.0 if step == 3 else 0.35
        ax.plot(fx, fy, color=BLUE, lw=3.2, zorder=4, alpha=a)
        if model:
            # predicted means: hollow, joined
            ax.scatter(fx, fy, s=170, facecolor="white", edgecolor=BLUE, linewidth=2.6, zorder=6,
                       alpha=1.0 if step == 3 else 0.45)
            if step == 3:
                ss.callout(ax, "Pareto front, as the model predicts it", (1.3, y(11.6)),
                           (0.67, y(22.0) if not logy else 40), BLUE)
        else:
            ax.scatter(fx, fy, s=170, color=BLUE, edgecolor="white", linewidth=1.8, zorder=6,
                       alpha=1.0 if step == 3 else 0.45)
            if step == 3:
                mid = ((fx[0] + fx[1]) / 2,
                       (fy[0] + fy[1]) / 2 if not logy else np.sqrt(fy[0] * fy[1]))
                ss.callout(ax, "Pareto front", mid, (1.17, y(17.0) if not logy else 20), BLUE)
    if step == 4:
        ax.scatter([d["x"] for d in rec], [y(d["abs"]) for d in rec], s=170, color=BLUE,
                   edgecolor="white", linewidth=1.8, zorder=6)
        ss.callout(ax, "Recommended settings", (103.5 / 60, y(1.0)),
                   (2.13, y(17.0) if not logy else 30), BLUE)
    return fig


# --------------------------------------------------------------------------- #
# Mass in the cup over time
# --------------------------------------------------------------------------- #
TRACE_RECT = [0.105, 0.215, 0.78, 0.475]
HAND_TRACE = "rebaseline-01"        # hand-tuned, at the same fitted tau as bo-005
TRACE_STEPS = [
    "A hand-tuned dose spent 3\u00bd of its 4 minutes\ntapping out the last 65 mg",
    "The recommended settings finished\nthe same dose in under 2 minutes",
    "Each of its taps moved twice as much powder,\nso the endgame took a third of the time",
]
TRACE_STEPS_ALL = [
    "Hand-tuned doses spent most of their time\ntapping out the last 60 to 80 mg",
    "Doses at the recommended settings finished\nin under 2 minutes",
    "Each of their taps moved about twice as much powder,\nso the endgame was much shorter",
]


def _trace_axes(fig, zoom: float):
    """zoom 0: the whole dose; 1: the last 100 mg (0.40-0.50 g)."""
    ax = fig.add_axes(TRACE_RECT)
    lo = 0.40 * zoom
    if zoom < 0.5:
        yt = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5]
    else:
        yt = [0.40, 0.42, 0.44, 0.46, 0.48, 0.50]
    yt = [v for v in yt if v >= lo - 1e-9]
    ss.style_axes(ax, (-0.1, 6.0), (lo - 0.012 * (1 - 0.75 * zoom), 0.512),
                  [0, 1, 2, 3, 4, 5, 6], yt, yfmt=lambda v: f"{v:.2f}".rstrip("0").rstrip(".")
                  if zoom < 0.5 else f"{v:.2f}")
    ss.ylabel_top(ax, "Powder in the cup (g)", y=1.07)
    ss.xlabel(ax, "Time since the dose started (min)")
    ax.axhline(0.5, color=GREY, lw=1.6, ls=(0, (5, 4)), zorder=1, xmax=0.985)
    ax.text(6.05, 0.5, "target", color=GREY, fontsize=FS, va="center", ha="left")
    return ax


def _tap_rate(tr):
    gain = tr["taps"][-1][1] - tr["m_trickle_end"]
    return gain * 1000 / len(tr["taps"])


def slide_traces(step: float, version: str = "pair", message: bool = True):
    """version "pair": the opening hand-tuned dose against bo-005; "all": the
    four hand-tuned doses against the three doses at the recommended corner
    (bo-003, bo-005, bo-006).  A fractional step between 2 and 3 is the zoom."""
    zoom = float(np.clip(step - 2, 0, 1))
    k = int(np.ceil(step - 1e-9))
    steps = TRACE_STEPS if version == "pair" else TRACE_STEPS_ALL
    fig = ss.slide(steps[min(k, 3) - 1] if message else None)
    ax = _trace_axes(fig, zoom)
    D = {d["label"]: d for d in cd.doses()}
    hands = [HAND_TRACE] if version == "pair" else list(cd.HAND_TUNED)
    recs = [cd.RECOMMENDED] if version == "pair" else ["bo-003", cd.RECOMMENDED, "bo-006"]
    lw = 3.2 if version == "pair" else 2.4
    for lab in hands:
        tr = cd.trace(D[lab]["uuid"])
        ax.plot(np.array(tr["t"]) / 60, tr["m"], color=ORANGE, lw=lw, zorder=4,
                solid_joinstyle="round",
                drawstyle="steps-post" if zoom > 0 else "default")
    if k >= 2:
        for lab in recs:
            tr = cd.trace(D[lab]["uuid"])
            ax.plot(np.array(tr["t"]) / 60, tr["m"], color=BLUE, lw=lw, zorder=5,
                    drawstyle="steps-post" if zoom > 0 else "default")
    h = cd.trace(D[HAND_TRACE]["uuid"])
    r = cd.trace(D[cd.RECOMMENDED]["uuid"])
    if k == 1 and version == "pair":
        tb = h["taps"][0][0] - 1.6
        mins, secs = divmod(round(h["total"] - tb), 60)
        ss.callout(ax, f"bulk and trickle: {h['m_trickle_end']:.2f} g in {tb:.0f} s",
                   (0.23, 0.30), (0.67, 0.17), ORANGE)
        ss.callout(ax, f"taps: last {1000 * (0.5 - h['m_trickle_end']):.0f} mg in "
                   f"{mins} min {secs} s", (2.5, 0.478), (2.3, 0.33), ORANGE)
    if k == 1 and version == "all":
        ss.callout(ax, "hand-tuned, 4 doses", (2.5, 0.47), (2.3, 0.33), ORANGE)
    if k == 2 and zoom == 0:
        if version == "pair":
            ss.callout(ax, "hand-tuned", (3.6, 0.494), (4.0, 0.36), ORANGE)
            ss.callout(ax, "recommended", (1.0, 0.482), (1.47, 0.30), BLUE)
        else:
            ss.callout(ax, "hand-tuned, 4 doses", (3.6, 0.494), (4.0, 0.36), ORANGE)
            ss.callout(ax, "recommended, 3 doses", (1.0, 0.482), (1.47, 0.30), BLUE)
    if k == 3 and zoom == 1:
        if version == "pair":
            ss.callout(ax, f"{_tap_rate(h):.1f} mg per tap", (3.0, 0.4878), (3.4, 0.455), ORANGE)
            ss.callout(ax, f"{_tap_rate(r):.1f} mg per tap", (1.03, 0.4844), (1.58, 0.435), BLUE)
        else:
            hr = [_tap_rate(cd.trace(D[x]["uuid"])) for x in hands]
            rr = [_tap_rate(cd.trace(D[x]["uuid"])) for x in recs]
            ss.callout(ax, f"{min(hr):.1f}\u2013{max(hr):.1f} mg per tap", (3.6, 0.4878),
                       (3.9, 0.455), ORANGE)
            ss.callout(ax, f"{min(rr):.1f}\u2013{max(rr):.1f} mg per tap", (1.03, 0.4844),
                       (1.58, 0.435), BLUE)
    return fig


# --------------------------------------------------------------------------- #
# The eight knobs: hand-tuned against recommended, inside each search range
# --------------------------------------------------------------------------- #
KNOBS = [   # label, key, low, high, unit formatter, stage
    ("Bulk tilt", "bulk_tilt_deg", 15, 40, lambda v: f"{v:g}\u00b0", "bulk"),
    ("Bulk speed", "bulk_rpm", 20, 100, lambda v: f"{v:g} rpm", "bulk"),
    ("Taps during bulk", "bulk_tap", 0, 1, lambda v: ("off", "on")[int(v)], "bulk"),
    ("Switch to trickle at", "trickle_start_remaining_g", 0.05, 0.30,
     lambda v: f"{1000 * v:g} mg to go", "trickle"),
    ("Trickle tilt", "trickle_tilt_deg", 10, 30, lambda v: f"{v:g}\u00b0", "trickle"),
    ("Taps during trickle", "trim_tap", 0, 1, lambda v: ("off", "on")[int(v)], "trickle"),
    ("Tap tilt", "tap_tilt_deg", 0, 15, lambda v: f"{v:g}\u00b0", "taps"),
    ("Stop when within", "tolerance_g", 0.003, 0.015, lambda v: f"{1000 * v:g} mg", "taps"),
]
KNOB_STEPS = [
    "The optimizer searched eight knobs,\nstarting from the hand-tuned values",
    "The recommended settings changed\nseven of the eight",
    "Every number it changed ended at the edge of its range,\nso the next search should widen the ranges",
]


def _knob_value(params, key):
    v = params[key]
    if key in ("bulk_tap", "trim_tap"):
        return 1.0 if v in ("2hz", True, 1) else 0.0
    return float(v)


def slide_knobs(step: int, version: str = "dumbbell", message: bool = True):
    fig = ss.slide(KNOB_STEPS[step - 1] if message else None)
    ax = fig.add_axes([0.40, 0.07, 0.42, 0.66])
    ax.set_xlim(-0.08, 1.08)
    ax.set_ylim(len(KNOBS) - 0.4, -0.75)
    ax.axis("off")
    D = {d["label"]: d for d in cd.doses()}
    hand = D[HAND_TRACE]["params"]
    rec = D[cd.RECOMMENDED]["params"]
    for i, (name, key, lo, hi, fmt, stage) in enumerate(KNOBS):
        h = (_knob_value(hand, key) - lo) / (hi - lo)
        r = (_knob_value(rec, key) - lo) / (hi - lo)
        ax.plot([0, 1], [i, i], color=ss.GHOST, lw=10, solid_capstyle="round", zorder=1)
        edge = step == 3 and abs(r - h) > 1e-9 and (r < 1e-9 or r > 1 - 1e-9)
        lo_col = BLUE if edge and r < 0.5 else GREY
        hi_col = BLUE if edge and r > 0.5 else GREY
        ax.text(-0.06, i, fmt(lo), ha="right", va="center", fontsize=FS, color=lo_col)
        ax.text(1.06, i, fmt(hi), ha="left", va="center", fontsize=FS, color=hi_col)
        fig.text(0.045, 0.0, "")
        ax.annotate(name, xy=(0, i), xycoords=("figure fraction", "data"), xytext=(0.045, i),
                    textcoords=("figure fraction", "data"), ha="left", va="center", fontsize=FS,
                    color=INK)
        ax.scatter([h], [i], s=260, color=ORANGE if step == 1 else ss.ORANGE_LIGHT,
                   edgecolor="white", linewidth=2, zorder=4)
        if step >= 2:
            if abs(r - h) > 1e-9:
                ax.plot([h, r], [i, i], color=BLUE, lw=3, alpha=0.35, zorder=2)
            ax.scatter([r], [i], s=260, color=BLUE, edgecolor="white", linewidth=2, zorder=5)
    if step == 1:
        ss.callout(ax, "hand-tuned", (0.6, 0), (0.7, -0.62), ORANGE)
    if step == 2:
        ss.callout(ax, "recommended", (1.0, 0), (0.62, -0.62), BLUE)
    return fig


# --------------------------------------------------------------------------- #
# The math, part 1: Pareto front and hypervolume (a small worked example)
# --------------------------------------------------------------------------- #
LIMIT_T, LIMIT_E = 3.0, 20.0          # the optimizer's thresholds: 180 s, 20 mg
# Ten made-up doses in the campaign's units, laid out so the front has four
# steps.  Illustration only; the results slides use the real doses.
TOY = [(0.55, 14.0), (0.9, 7.5), (1.6, 4.0), (2.4, 1.6), (1.2, 13.0), (2.0, 9.5),
       (2.7, 5.5), (3.6, 3.0), (4.4, 11.0), (5.2, 6.5)]
TOY_ONE = (2.0, 9.5)                  # the dose step 1 points at
TOY_NEXT = (1.25, 4.3)                # the model's predicted next dose
TOY_NEXT_SD = (0.35, 2.5)
FRONT_STEPS = [
    "Every dose gives two numbers to make small:\nhow long it took, and how far it missed",
    "One dose beats another only if it is\nboth faster and more accurate",
    "The doses that nothing beats\nform the Pareto front",
    "The area the front covers, inside the limits,\nmeasures how good the best trade-offs are",
    "The optimizer doses next where it expects\nthe area to grow the most",
]


def _staircase(front):
    sx, sy = [], []
    for k, (x, e) in enumerate(front):
        if k:
            sx.append(x)
            sy.append(front[k - 1][1])
        sx.append(x)
        sy.append(e)
    return sx, sy


def _hv_patches(ax, front, color, alpha, z=1):
    for k, (x, e) in enumerate(front):
        if x >= LIMIT_T or e >= LIMIT_E:
            continue
        e_top = LIMIT_E if k == 0 else min(LIMIT_E, front[k - 1][1])
        ax.add_patch(Rectangle((x, e), LIMIT_T - x, e_top - e, facecolor=color,
                               edgecolor="none", zorder=z, alpha=alpha))


def slide_front_math(step: int, version: str = "example", message: bool = True):
    fig = ss.slide(FRONT_STEPS[step - 1] if message else None)
    ax = _pareto_axes(fig, False)
    ax.text(7.0, -0.9, "worked example", color=GREY, fontsize=FS, ha="right", va="bottom")
    front = cd.pareto_front(TOY)
    fx, fy = zip(*front)
    if step == 1:
        x, e = TOY_ONE
        ax.scatter([x], [e], s=190, color=INK, zorder=6)
        ax.plot([x, x], [-0.9, e], color=INK2, lw=1.6, ls=(0, (3, 3)))
        ax.plot([-0.13, x], [e, e], color=INK2, lw=1.6, ls=(0, (3, 3)))
        ss.callout(ax, f"one dose: {x:g} min, {e:g} mg off", (x, e), (2.9, 17.0), INK)
        return fig
    col = GREY if step == 2 else FAINT
    rest = [p for p in TOY if not (step >= 3 and p in front)]
    ax.scatter(*zip(*rest), s=130, facecolor="white", edgecolor=col, linewidth=2.2, zorder=3)
    if step == 2:
        x, e = front[2]
        ax.add_patch(Rectangle((x, e), 7.0 - x, 31.5 - e, facecolor=ss.GHOST, edgecolor="none",
                               zorder=0))
        ax.scatter([x], [e], s=190, color=INK, zorder=6)
        ss.callout(ax, "this dose ...", (x, e), (0.35, 1.2), INK)
        ax.text(4.3, 24.0, "... beats every dose\nin the grey area", color=INK, fontsize=FS,
                ha="left", va="center")
        return fig
    if step >= 4:
        _hv_patches(ax, front, ss.BLUE_LIGHT, 1.0 if step == 4 else 0.7)
        ax.plot([LIMIT_T, LIMIT_T], [-0.9, LIMIT_E], color=INK2, lw=1.6, ls=(0, (5, 4)), zorder=2)
        ax.plot([-0.13, LIMIT_T], [LIMIT_E, LIMIT_E], color=INK2, lw=1.6, ls=(0, (5, 4)), zorder=2)
        ax.text(LIMIT_T + 0.08, LIMIT_E, "limits:\n3 min, 20 mg", color=INK2, fontsize=FS,
                ha="left", va="center", linespacing=1.1)
        if step == 4:
            ax.text(2.25, 12.0, "hypervolume", color=BLUE, fontsize=FS, ha="center", va="center")
    sx, sy = _staircase(front)
    ax.plot(sx, sy, color=BLUE, lw=3.0, zorder=4)
    ax.scatter(fx, fy, s=170, color=BLUE, edgecolor="white", linewidth=1.8, zorder=6)
    if step == 3:
        ss.callout(ax, "Pareto front", (0.9, 10.5), (1.6, 19.0), BLUE)
    if step == 5:
        cx, ce = TOY_NEXT
        new_front = cd.pareto_front(list(front) + [TOY_NEXT])
        gain = [(x, e) for x, e in new_front]
        # the extra area if the dose lands where predicted
        k = new_front.index(TOY_NEXT)
        e_top = new_front[k - 1][1]
        x_right = new_front[k + 1][0]
        ax.add_patch(Rectangle((cx, ce), x_right - cx, e_top - ce, facecolor=BLUE, alpha=0.35,
                               edgecolor="none", zorder=2))
        ax.errorbar([cx], [ce], xerr=[[TOY_NEXT_SD[0]], [TOY_NEXT_SD[0]]],
                    yerr=[[TOY_NEXT_SD[1]], [TOY_NEXT_SD[1]]], fmt="none", ecolor=BLUE,
                    alpha=0.45, elinewidth=3, capsize=0, zorder=5)
        ax.scatter([cx], [ce], s=200, facecolor="white", edgecolor=BLUE, linewidth=3.0, zorder=7)
        ss.callout(ax, "predicted next dose,\nwith its uncertainty", (cx - 0.08, ce + 0.5),
                   (0.25, 21.5), BLUE)
        ss.callout(ax, "area it would add", (cx + 0.2, ce + 1.6), (3.6, 9.0), BLUE)
    return fig


# --------------------------------------------------------------------------- #
# The math, part 2: the model and the choice (one knob, made-up numbers)
# --------------------------------------------------------------------------- #
GP_X = np.array([1.0, 4.0, 7.0, 14.0])          # knob setting of the doses so far
GP_Y = np.array([3.4, 2.6, 2.2, 3.1])           # their times (min)
GP_NEW_Y = 1.75                                  # what the new dose gives
MODEL_STEPS = [
    "The model starts from the doses so far,\nshown here for one knob",
    "It draws a best guess through them ...",
    "... with a band for how unsure it is\nbetween them",
    "It doses where a big improvement is most likely:\nlow guess, wide band, or both",
    "Each new dose narrows the band, and the loop repeats,\nfor all eight knobs and both numbers at once",
]


def _gp(xq, X, Y, ell=2.0, sf=0.8, sn=0.08):
    """Posterior mean and sd of a GP with a squared-exponential kernel and a
    constant mean equal to the data mean."""
    k = lambda a, b: sf ** 2 * np.exp(-0.5 * (a[:, None] - b[None, :]) ** 2 / ell ** 2)  # noqa
    m0 = Y.mean()
    K = k(X, X) + sn ** 2 * np.eye(len(X))
    Ks = k(xq, X)
    L = np.linalg.cholesky(K)
    a = np.linalg.solve(L.T, np.linalg.solve(L, Y - m0))
    mu = m0 + Ks @ a
    v = np.linalg.solve(L, Ks.T)
    var = sf ** 2 - (v ** 2).sum(0)
    return mu, np.sqrt(np.maximum(var, 1e-9))


def _ei(mu, sd, best):
    from math import erf, exp, pi, sqrt
    z = (best - mu) / sd
    Phi = np.array([0.5 * (1 + erf(v / sqrt(2))) for v in z])
    phi = np.array([exp(-0.5 * v * v) / sqrt(2 * pi) for v in z])
    return (best - mu) * Phi + sd * phi


def slide_model_math(step: int, version: str = "example", message: bool = True):
    fig = ss.slide(MODEL_STEPS[step - 1] if message else None)
    ax = fig.add_axes([0.105, 0.415, 0.78, 0.275])
    ss.style_axes(ax, (-0.3, 15.3), (0.6, 4.6), [0, 5, 10, 15], [1, 2, 3, 4])
    ss.ylabel_top(ax, "Time per dose (min, \u2193 is better)", y=1.07)
    ax.spines["bottom"].set_visible(False)
    ax.tick_params(axis="x", length=0, labelbottom=False)
    xq = np.linspace(0, 15, 301)
    X, Y = GP_X, GP_Y
    if step == 5:
        mu0, sd0 = _gp(xq, X, Y)
        ei0 = _ei(mu0, sd0, Y.min())
        xn = xq[np.argmax(ei0)]
        yn = GP_NEW_Y
        X2, Y2 = np.append(X, xn), np.append(Y, yn)
        ax.fill_between(xq, mu0 - sd0, mu0 + sd0, color=GHOST_BAND, lw=0, zorder=1)
        mu, sd = _gp(xq, X2, Y2)
        ax.fill_between(xq, mu - sd, mu + sd, color=ss.BLUE_LIGHT, lw=0, zorder=2, alpha=0.9)
        ax.plot(xq, mu, color=BLUE, lw=3, zorder=3)
        ax.scatter(X, Y, s=170, color=INK, zorder=6)
        ax.scatter([xn], [yn], s=200, color=BLUE, edgecolor="white", linewidth=2, zorder=7)
        ss.callout(ax, "new dose", (xn, yn), (xn + 1.6, 1.0), BLUE)
    else:
        mu, sd = _gp(xq, X, Y)
        if step >= 3:
            ax.fill_between(xq, mu - sd, mu + sd, color=ss.BLUE_LIGHT, lw=0, zorder=1,
                            alpha=1.0 if step == 3 else 0.8)
        if step >= 2:
            ax.plot(xq, mu, color=BLUE, lw=3, zorder=3, alpha=1.0 if step <= 3 else 0.8)
        ax.scatter(X, Y, s=170, color=INK, zorder=6)
        if step == 1:
            ss.callout(ax, "doses so far", (4.0, 2.6), (5.2, 4.1), INK)
        if step == 2:
            ss.callout(ax, "best guess", (10.5, float(np.interp(10.5, xq, mu))), (11.0, 4.1), BLUE)
        if step == 3:
            ss.callout(ax, "uncertainty", (10.5, float(np.interp(10.5, xq, mu + sd))),
                       (11.0, 4.3), BLUE)
    # the acquisition, under the model
    ax2 = fig.add_axes([0.105, 0.225, 0.78, 0.13])
    ax2.set_xlim(-0.3, 15.3)
    for sp in ("left", "top", "right"):
        ax2.spines[sp].set_visible(False)
    ax2.spines["bottom"].set_position(("outward", 6))
    ax2.spines["bottom"].set_bounds(0, 15)
    ax2.set_xticks([0, 5, 10, 15])
    ax2.set_yticks([])
    ax2.set_xlabel("One knob's setting", fontsize=FS, loc="left", labelpad=10)
    ax2.set_xticklabels([])
    ax2.tick_params(axis="x", length=6)
    fig.text(0.885, 0.04, "made-up numbers", color=GREY, fontsize=FS, ha="right", va="bottom")
    if step >= 4:
        mu, sd = _gp(xq, X, Y)
        ei = _ei(mu, sd, Y.min())
        ei = ei / ei.max()
        col = BLUE if step == 4 else FAINT
        ax2.fill_between(xq, 0, ei, color=col, alpha=0.25 if step == 4 else 0.4, lw=0)
        ax2.plot(xq, ei, color=col, lw=2.6)
        ax2.set_ylim(0, 1.15)
        xn = xq[np.argmax(ei)]
        if step == 4:
            ax2.plot([xn, xn], [0, 1.0], color=BLUE, lw=2, ls=(0, (3, 3)))
            ax.plot([xn, xn], [0.6, 4.6], color=BLUE, lw=2, ls=(0, (3, 3)), alpha=0.6)
            ax2.text(0.0, 0.62, "expected improvement", color=BLUE, fontsize=FS,
                     ha="left", va="center")
    else:
        ax2.set_ylim(0, 1.15)
    return fig


GHOST_BAND = "#ecebe7"


# --------------------------------------------------------------------------- #
SLIDES = {
    "pareto": (slide_pareto, len(PARETO_STEPS), ("linear", "model", "log")),
    "traces": (slide_traces, len(TRACE_STEPS), ("pair", "all")),
    "knobs": (slide_knobs, len(KNOB_STEPS), ("dumbbell",)),
    "front-math": (slide_front_math, len(FRONT_STEPS), ("example",)),
    "model-math": (slide_model_math, len(MODEL_STEPS), ("example",)),
}


def ss_ease(u):
    return u * u * (3 - 2 * u)


# extra in-between frames: slide -> (after step, list of fractional steps)
TWEENS = {"traces": (2, [2.0001] + [2 + ss_ease(u) for u in np.linspace(0, 1, 16)[1:-1]])}


def build(name):
    fn, n, versions = SLIDES[name]
    for v in versions:
        d = OUT / f"{name}" / v
        frames, holds, fades = [], [], []
        for k in range(1, n + 1):
            fig = fn(k, v, True)
            ss.save(fig, d / f"step_{k}.png")
            frames.append(ss.to_image(fig))
            holds.append(6.0 if k == n else 4.0)
            fades.append(0.0 if name in TWEENS and TWEENS[name][0] == k - 1 else 0.25)
            ss.save(fig, d / "print" / f"step_{k}.png", dpi=ss.DPI_PRINT)
            ss.plt.close(fig)
            fig = fn(k, v, False)
            ss.save(fig, d / "plain" / f"step_{k}.png")
            ss.plt.close(fig)
            if name in TWEENS and TWEENS[name][0] == k:
                # the zoom: the message changes in the usual cross-fade, then the
                # axis glides to the new range; no fade into the step after it
                for j, u in enumerate(TWEENS[name][1]):
                    fig = fn(u, v, True)
                    frames.append(ss.to_image(fig))
                    ss.plt.close(fig)
                    holds.append(0.6 if j == 0 else 1 / 15)
                    fades.append(0.25 if j == 0 else 0.0)
        ss.write_gif(frames, holds, d / "build.gif", fades=fades)
        ss.write_mp4(frames, holds, d / "build.mp4", fades=fades)
        print(f"  {name}/{v}: {n} steps")


def main():
    names = sys.argv[1:] or list(SLIDES)
    for name in names:
        build(name)


if __name__ == "__main__":
    main()
