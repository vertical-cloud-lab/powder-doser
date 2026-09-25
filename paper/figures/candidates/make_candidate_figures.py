"""Candidate manuscript figures from the issue #116 round-1 powder battery.

These are *options to choose between*, not the final figure set.  Each function
answers one question about the data; the accompanying README ranks them for the
Digital Discovery manuscript (PR #97).

Every panel is built from the tidy CSVs in ``data/`` (see ``build_dataset.py``),
which are distilled from the per-run artifacts on the ``claude/issue-116-*``
branches.

Usage:
    python make_candidate_figures.py [outdir]
"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.lines import Line2D
from matplotlib.patches import Patch

HERE = Path(__file__).parent
DATA = HERE / "data"

# --- palette -----------------------------------------------------------------
# Categorical slots 1-3 of the validated reference palette (all-pairs safe).
SURROGATE = "#2a78d6"   # slot 1, blue
RESEARCH = "#eb6834"    # slot 2, orange
ACCENT = "#1baf7a"      # slot 3, aqua
# Tilt is an ordered magnitude, so it gets a one-hue ordinal ramp, not hues.
TILT_RAMP = {0.0: "#86b6ef", 45.0: "#2a78d6", 90.0: "#104281"}
# Status palette (fixed, never themed) - always paired with a text label.
GOOD, WARNING, SERIOUS, CRITICAL = "#0ca30c", "#fab219", "#ec835a", "#d03b3b"
STATUS = {"ok": GOOD, "overshoot": WARNING,
          "cycle-budget": SERIOUS, "stalled": CRITICAL}
INK, INK2, MUTED = "#0b0b0b", "#52514e", "#b8b6ae"
SURFACE = "#fcfcfb"

plt.rcParams.update({
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE,
    "savefig.facecolor": SURFACE, "font.size": 9,
    "axes.edgecolor": MUTED, "axes.labelcolor": INK, "axes.titlesize": 10,
    "axes.titleweight": "bold", "axes.titlecolor": INK, "axes.linewidth": 0.8,
    "xtick.color": INK2, "ytick.color": INK2, "text.color": INK,
    "grid.color": "#e8e6e0", "grid.linewidth": 0.7, "legend.frameon": False,
    "axes.spines.top": False, "axes.spines.right": False,
})


def load():
    runs = pd.read_csv(DATA / "runs.csv")
    feed = pd.read_csv(DATA / "feed.csv")
    trials = pd.read_csv(DATA / "trials.csv")
    doses = pd.read_csv(DATA / "doses.csv")
    polls = pd.read_csv(DATA / "polls.csv")
    return runs, feed, trials, doses, polls


RUNS, FEED, TRIALS, DOSES, POLLS = load()
VALID_RUNS = set(RUNS[RUNS.qc_valid].run_id)
DOSES = DOSES[DOSES.run_id.isin(VALID_RUNS)].copy()
DISPLAY = dict(zip(RUNS.powder_id, RUNS.display))
TRACK = dict(zip(RUNS.powder_id, RUNS.track))

# Powders whose feed factor is an upper bound rather than a measurement: the
# battery could not resolve conveyance above its own noise floor.  Reported as
# censored observations, never as small numbers.
BOUNDED = {"brown-rice-flour": 0.3, "silicon-325": 1.2, "fumed-silica": 0.25}


def representative_runs() -> pd.DataFrame:
    """One run per powder: QC-valid, preferring the C/E-consistent, newest.

    Powders whose only runs are QC-excluded *for non-conveyance* are kept, at
    their bound: "this geometry cannot meter this powder" is a result, and
    dropping it would silently truncate the low end of the range.
    """
    ok = RUNS[RUNS.qc_valid | RUNS.powder_id.isin(BOUNDED)].copy()
    ok["rank"] = (~ok.poolable).astype(int)
    ok = ok.sort_values(["powder_id", "rank", "started_utc"],
                        ascending=[True, True, False])
    return ok.groupby("powder_id", as_index=False).first()


REP = representative_runs()


def feed_factor(run_id: str, tilt: float) -> tuple[float, float]:
    """Block C mean mass per 360 deg revolution, in mg, and its RSD."""
    row = FEED[(FEED.run_id == run_id) & (FEED.phase == "rotation")
               & (FEED.tilt_deg == tilt)]
    if row.empty:
        return np.nan, np.nan
    return float(row.mean_g.iloc[0]) * 1000, float(row.rsd_pct.iloc[0])


def order_by_feed(powders, tilt=45.0):
    vals = {}
    for p in powders:
        rid = REP[REP.powder_id == p].run_id.iloc[0]
        vals[p] = BOUNDED.get(p, feed_factor(rid, tilt)[0])
    return sorted(powders, key=lambda p: vals[p] or 0)


def spread(values, gap):
    """Nudge label positions apart in log space, preserving order."""
    order = np.argsort(values)
    out = np.array(values, dtype=float)
    for k in range(1, len(order)):
        i, j = order[k - 1], order[k]
        if out[j] - out[i] < gap:
            out[j] = out[i] + gap
    return out


def place_labels(ax, items, fontsize=7.3, pad=1.5):
    """Greedy non-overlapping direct labels with leader lines.

    ``items`` is a sequence of ``(x, y, text, color)`` in data coordinates.
    Each label tries eight offsets in turn and takes the first that clears
    every label already placed; a leader line is drawn whenever the label
    ends up far enough from its marker to be ambiguous.
    """
    fig = ax.figure
    fig.canvas.draw()
    offsets = [(0, -13), (0, 10), (11, 0), (-11, 0),
               (10, -11), (-10, -11), (10, 10), (-10, 10),
               (0, -24), (0, 21), (20, -20), (-20, -20)]
    placed = []
    for x, y, text, color in items:
        px, py = ax.transData.transform((x, y))
        best = None
        for dx, dy in offsets:
            ha = "center" if dx == 0 else ("left" if dx > 0 else "right")
            va = "top" if dy < 0 else ("bottom" if dy > 0 else "center")
            t = ax.annotate(text, (x, y), xytext=(dx, dy),
                            textcoords="offset points", fontsize=fontsize,
                            ha=ha, va=va, color=INK2)
            fig.canvas.draw()
            bb = t.get_window_extent().expanded(1.0 + pad / 50, 1.0 + pad / 20)
            if not any(bb.overlaps(o) for o in placed):
                best = (t, bb, dx, dy)
                break
            t.remove()
        if best is None:
            dx, dy = 0, -13
            t = ax.annotate(text, (x, y), xytext=(dx, dy),
                            textcoords="offset points", fontsize=fontsize,
                            ha="center", va="top", color=INK2)
            fig.canvas.draw()
            best = (t, t.get_window_extent(), dx, dy)
        t, bb, dx, dy = best
        placed.append(bb)
        if abs(dx) + abs(dy) > 22:
            ax.annotate("", xy=(x, y), xytext=(dx * 0.72, dy * 0.72),
                        textcoords="offset points",
                        arrowprops=dict(arrowstyle="-", color=MUTED, lw=0.7,
                                        shrinkA=0, shrinkB=2))


def track_color(pid):
    return RESEARCH if TRACK[pid] == "research" else SURROGATE


def track_legend(ax, loc="lower right", extra=(), bars=False):
    """Track legend whose swatch matches the mark the chart actually draws."""
    if bars:
        handles = [Patch(facecolor=SURROGATE, label="Surrogate (food-safe)"),
                   Patch(facecolor=RESEARCH, label="Research-relevant")]
    else:
        handles = [
            Line2D([], [], marker="o", ls="", color=SURROGATE,
                   label="Surrogate (food-safe)"),
            Line2D([], [], marker="s", ls="", color=RESEARCH,
                   label="Research-relevant"),
        ]
    ax.legend(handles=[*handles, *extra], loc=loc, fontsize=7.5)


def finish(fig, path, note=None):
    if note:
        # Place the note below everything already drawn.  Rotated tick labels
        # can extend a long way under the axes, so measure the rendered extent
        # rather than guessing a fixed offset.
        fig.canvas.draw()
        bottom = min(
            fig.transFigure.inverted().transform(
                ax.get_tightbbox(fig.canvas.get_renderer()).p0)[1]
            for ax in fig.axes if ax.get_visible())
        fig.text(0.01, bottom - 0.035, note, fontsize=6.4, color=INK2,
                 va="top")
    fig.savefig(path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"  wrote {path.name}")


# =============================================================================
# A - Conveyance: does the auger move this powder at all?
# =============================================================================

def figA1_feed_vs_tilt(out: Path):
    """Feed factor vs tilt, surrogate and research tracks side by side."""
    fig, axes = plt.subplots(1, 2, figsize=(9.6, 4.1), sharey=True)
    for ax, track, title in zip(
            axes, ["surrogate", "research"],
            ["General powder set (food-safe surrogates)",
             "Research-relevant powders (alloy / precursor)"]):
        pids = order_by_feed([p for p in REP.powder_id if TRACK[p] == track])[::-1]
        ends = []
        for pid in pids:
            rid = REP[REP.powder_id == pid].run_id.iloc[0]
            xs, ys = [], []
            for tilt in (0.0, 45.0, 90.0):
                mg, _ = feed_factor(rid, tilt)
                xs.append(tilt)
                ys.append(max(mg, 0.05))
            bounded = pid in BOUNDED
            ax.plot(xs, ys, marker="o" if track == "surrogate" else "s",
                    ms=5, lw=1.8, color=track_color(pid),
                    alpha=0.95 if not bounded else 0.4,
                    ls="-" if not bounded else ":")
            ends.append((pid, ys[-1], bounded))
        labels = spread([np.log10(e[1]) for e in ends], 0.135)
        for (pid, yend, bounded), ylab in zip(ends, labels):
            ax.annotate(DISPLAY[pid] + (" $\\leq$bound" if bounded else ""),
                        (90, 10 ** ylab), xytext=(9, 0),
                        textcoords="offset points", fontsize=7.3,
                        color=INK if not bounded else INK2, va="center")
        ax.set_yscale("log")
        ax.set_xticks([0, 45, 90])
        ax.set_xlabel("Auger tilt (deg;  0 = horizontal, 90 = vertical)")
        ax.set_title(title, fontsize=9)
        ax.grid(axis="y", alpha=0.6)
        ax.set_xlim(-8, 150)
    axes[0].set_ylabel("Feed factor (mg per 360$^\\circ$ revolution)")
    fig.suptitle("A1 · Feed factor spans three orders of magnitude across powders",
                 fontsize=11, fontweight="bold", y=1.0)
    finish(fig, out / "A1_feed_vs_tilt.png",
           "Block C, 6 revolutions at 30 RPM per tilt, one QC-valid run per powder. "
           "Dotted = upper bound (conveyance unresolved above the balance floor).")


def figA2_feed_rank(out: Path):
    """Ranked feed factor at 45 deg, with censored powders drawn as bounds.

    Position-encoded dots rather than bars: bar *length* on a log axis is not
    proportional to the value it encodes, and there is no zero baseline to
    anchor it to.
    """
    pids = order_by_feed(list(REP.powder_id))
    fig, ax = plt.subplots(figsize=(7.4, 4.6))
    left = 0.09
    for i, pid in enumerate(pids):
        rid = REP[REP.powder_id == pid].run_id.iloc[0]
        mg, rsd = feed_factor(rid, 45.0)
        c = track_color(pid)
        if pid in BOUNDED:
            b = BOUNDED[pid]
            ax.plot([left, b], [i, i], color=c, lw=1.1, alpha=0.3, zorder=1)
            ax.annotate("", xy=(b * 0.4, i), xytext=(b, i),
                        arrowprops=dict(arrowstyle="-|>", color=c, lw=1.4,
                                        alpha=0.75))
            ax.scatter([b], [i], s=70, color=c, alpha=0.4, zorder=3,
                       marker="o" if TRACK[pid] == "surrogate" else "s",
                       edgecolor=SURFACE, linewidth=1.0)
            ax.text(b * 2.6, i, f"$\\leq${b:g} mg/rev", va="center",
                    fontsize=7.2, color=INK2)
        else:
            err = mg * (rsd or 0) / 100 / np.sqrt(6)
            ax.plot([left, mg], [i, i], color=c, lw=1.1, alpha=0.35, zorder=1)
            ax.errorbar(mg, i, xerr=err, fmt="o" if TRACK[pid] == "surrogate"
                        else "s", ms=8, color=c, ecolor=INK2, elinewidth=1,
                        capsize=2.5, zorder=3, markeredgecolor=SURFACE,
                        markeredgewidth=1.0)
            ax.text(mg * 1.25, i, f"{mg:.0f}", va="center", fontsize=7.4,
                    color=INK2)
    ax.set_yticks(range(len(pids)))
    ax.set_yticklabels([DISPLAY[p] for p in pids], fontsize=8)
    ax.set_xscale("log")
    ax.set_xlim(left, 1600)
    ax.set_ylim(-0.8, len(pids) - 0.2)
    ax.set_xlabel("Feed factor at 45$^\\circ$ tilt (mg per revolution, log scale)")
    ax.set_title("A2 \u00b7 One auger, one parameter set, 3+ decades of conveyance",
                 fontsize=10.5)
    ax.grid(axis="x", alpha=0.6)
    track_legend(ax, loc="lower right")
    finish(fig, out / "A2_feed_rank.png",
           "Error bars are the standard error of 6 revolutions. Arrows are upper bounds: "
           "the powder conveyed nothing resolvable above the balance noise floor.")


def figA3_tilt_sensitivity(out: Path):
    """How much gravity assist each powder needs: ratio of 90 deg to 0 deg."""
    rows = []
    for pid in REP.powder_id:
        if pid in BOUNDED:
            continue
        rid = REP[REP.powder_id == pid].run_id.iloc[0]
        f0, _ = feed_factor(rid, 0.0)
        f90, _ = feed_factor(rid, 90.0)
        if f0 and f0 > 0.5:
            rows.append((pid, f90 / f0, f0))
    rows.sort(key=lambda r: r[1])
    fig, ax = plt.subplots(figsize=(6.8, 3.9))
    ax.barh(np.arange(len(rows)), [r[1] for r in rows],
            color=[track_color(r[0]) for r in rows], height=0.6)
    ax.set_yticks(np.arange(len(rows)))
    ax.axvline(1, color=INK2, lw=1, ls="--")
    ax.text(1.05, -0.65, "no tilt benefit", fontsize=7, color=INK2)
    ax.set_yticklabels([DISPLAY[r[0]] for r in rows], fontsize=8)
    ax.set_xlabel("Feed factor ratio, 90$^\\circ$ / 0$^\\circ$ tilt")
    ax.set_title("A3 · Gravity dependence separates cohesive from free-flowing",
                 fontsize=10.5)
    ax.grid(axis="x", alpha=0.6)
    for i, r in enumerate(rows):
        ax.text(r[1] + 0.15, i, f"{r[1]:.1f}$\\times$", va="center",
                fontsize=7.4, color=INK2)
    track_legend(ax, loc="lower right", bars=True)
    finish(fig, out / "A3_tilt_sensitivity.png",
           "A large ratio means the powder barely conveys horizontally and needs the tube tipped "
           "toward vertical; a small ratio means the screw meters it under its own action.\n"
           "Powders whose feed factor is an upper bound are omitted (the ratio is undefined).")


# =============================================================================
# B - Precision: how repeatable is a revolution?
# =============================================================================

def figB1_rsd_vs_feed(out: Path):
    """Dose precision is set by how much mass a revolution moves."""
    fig, ax = plt.subplots(figsize=(7.0, 4.6))
    xs, ys = [], []
    for pid in REP.powder_id:
        if pid in BOUNDED:
            continue
        rid = REP[REP.powder_id == pid].run_id.iloc[0]
        for tilt in (0.0, 45.0, 90.0):
            mg, rsd = feed_factor(rid, tilt)
            if not mg or mg <= 0 or not np.isfinite(rsd) or rsd <= 0:
                continue
            xs.append(mg)
            ys.append(rsd)
            ax.scatter(mg, rsd, s=52, color=TILT_RAMP[tilt],
                       marker="o" if TRACK[pid] == "surrogate" else "s",
                       edgecolor=SURFACE, linewidth=0.9, zorder=3)

    # Power-law fit in log-log space, reported with its own r^2 so the strength
    # of the trend is visible rather than asserted.
    lx, ly = np.log10(xs), np.log10(ys)
    slope, icept = np.polyfit(lx, ly, 1)
    r = np.corrcoef(lx, ly)[0, 1]
    grid = np.logspace(np.log10(min(xs)), np.log10(max(xs)), 50)
    ax.plot(grid, 10 ** (icept + slope * np.log10(grid)), color=INK2, lw=1.4,
            ls="--", zorder=2,
            label=f"fit: RSD $\\propto$ feed$^{{{slope:.2f}}}$  ($r^2$ = {r*r:.2f})")
    ax.plot(grid, 10 ** (np.log10(80) - 0.5 * np.log10(grid)), color=ACCENT,
            lw=1.4, ls=":", zorder=2,
            label="slope $-$0.5 (counting-statistics reference)")

    # Label only the ends of the range and the control - a name on every point
    # would bury the trend it is meant to support.
    named = {"salt", "calcium-lactate", "sodium-alginate", "white-rice-flour"}
    items = []
    for pid in named:
        if pid not in set(REP.powder_id):
            continue
        rid = REP[REP.powder_id == pid].run_id.iloc[0]
        mg, rsd = feed_factor(rid, 45.0)
        if mg and np.isfinite(rsd):
            items.append((mg, rsd, DISPLAY[pid], INK2))

    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("Feed factor (mg per revolution)")
    ax.set_ylabel("Revolution-to-revolution RSD (%)")
    ax.set_title("B1 \u00b7 Precision follows flow: more mass per turn, tighter dose",
                 fontsize=10.5)
    ax.grid(alpha=0.6, which="both")
    handles = [Line2D([], [], marker="o", ls="", color=TILT_RAMP[t],
                      label=f"{t:.0f}$^\\circ$ tilt") for t in (0.0, 45.0, 90.0)]
    handles += [Line2D([], [], marker="o", ls="", color=INK2, label="Surrogate"),
                Line2D([], [], marker="s", ls="", color=INK2, label="Research")]
    handles += ax.get_legend_handles_labels()[0][-2:]
    ax.legend(handles=handles, fontsize=7.0, ncol=2, loc="lower left")
    place_labels(ax, items)
    finish(fig, out / "B1_rsd_vs_feed.png",
           "Each point is one powder at one tilt (n = 6 revolutions); 30 points from 10 powders. "
           "Colour encodes tilt (ordered), marker shape encodes powder track.\n"
           "Upper-bound powders are excluded (RSD is undefined when the mean is not resolved).")


def figB2_salt_repeats(out: Path):
    """Between-session vs within-session scatter for the salt control."""
    salt = RUNS[(RUNS.powder_id == "salt") & (RUNS.poolable)]
    tilts = (0.0, 45.0, 90.0)
    fig, ax = plt.subplots(figsize=(6.4, 4.1))
    n_runs = len(salt)
    width = 0.7 / n_runs
    for j, rid in enumerate(salt.run_id):
        date = rid[:8]
        vals = [feed_factor(rid, t)[0] for t in tilts]
        errs = [feed_factor(rid, t)[0] * (feed_factor(rid, t)[1] or 0) / 100
                / np.sqrt(6) for t in tilts]
        ax.bar(np.arange(3) + (j - (n_runs - 1) / 2) * width, vals, width * 0.88,
               yerr=errs, label=f"{date[:4]}-{date[4:6]}-{date[6:]}",
               color=list(TILT_RAMP.values())[j], zorder=3,
               error_kw=dict(ecolor=INK2, lw=1, capsize=2.5))
    for i, t in enumerate(tilts):
        vals = [feed_factor(rid, t)[0] for rid in salt.run_id]
        between = np.std(vals, ddof=1) / np.mean(vals) * 100
        within = np.median([feed_factor(rid, t)[1] for rid in salt.run_id])
        ax.text(i, max(vals) * 1.10,
                f"between-run {between:.0f}%\nwithin-run {within:.0f}%",
                ha="center", fontsize=7, color=INK2)
    ax.set_xticks(range(3))
    ax.set_xticklabels([f"{t:.0f}$^\\circ$" for t in tilts])
    ax.set_xlabel("Auger tilt")
    ax.set_ylabel("Feed factor (mg per revolution)")
    ax.set_ylim(0, 375)
    ax.set_title("B2 · The control repeats: between-run scatter $\\approx$ within-run",
                 fontsize=10.5)
    ax.grid(axis="y", alpha=0.6)
    ax.legend(fontsize=7.5, title="NaCl control session", title_fontsize=7.5)
    finish(fig, out / "B2_salt_repeats.png",
           "Only NaCl runs passing the block C/E consistency gate are pooled; the 2026-08-06 "
           "run is excluded (C/E = 2.68) and 2026-08-20 was an environment stress test.")


# =============================================================================
# C - Speed: what does turning the auger faster buy?
# =============================================================================

# Runs whose own QC notes flag the block D per-speed split as unusable
# (inter-trial carry-over: block D tares once, not between speeds).
BLOCK_D_EXCLUDED = {"barium-chloride"}


def figC1_massrev_vs_rpm(out: Path):
    """Mass per revolution vs auger speed: is the screw fill-limited?"""
    d = TRIALS[(TRIALS.block == "D") & TRIALS.rpm.notna()].copy()
    d["mg_per_rev"] = d.delta_g * 1000 / 3.0     # block D is 3 revolutions
    fig, ax = plt.subplots(figsize=(7.0, 4.4))
    items, dropped = [], []
    for pid in REP.powder_id:
        if pid in BOUNDED or pid in BLOCK_D_EXCLUDED:
            dropped.append(DISPLAY[pid])
            continue
        rid = REP[REP.powder_id == pid].run_id.iloc[0]
        sub = d[d.run_id == rid].groupby("rpm").mg_per_rev.mean()
        # The normalisation divides by the 15 RPM point, so that point must be
        # a real measurement rather than a few mg of balance noise.
        if sub.empty or 15.0 not in sub.index or sub.loc[15.0] < 20:
            dropped.append(DISPLAY[pid])
            continue
        norm = sub / sub.loc[15.0] * 100
        ax.plot(norm.index, norm.values, marker="o" if TRACK[pid] ==
                "surrogate" else "s", ms=5.5, lw=1.7, color=track_color(pid),
                alpha=0.9)
        items.append((norm.index[-1], norm.values[-1], DISPLAY[pid],
                      track_color(pid)))
    ax.axhline(100, color=MUTED, lw=1.2, ls="--")
    ax.text(16, 102, "same mass per revolution at every speed", fontsize=7,
            color=INK2)
    ax.set_xticks([15, 45, 90])
    ax.set_xlabel("Auger speed (RPM)")
    ax.set_ylabel("Mass per revolution, % of the 15 RPM value")
    ax.set_xlim(10, 132)
    ax.set_title("C1 \u00b7 Most powders deliver less per turn as the auger speeds up",
                 fontsize=10.5)
    ax.grid(alpha=0.6)
    track_legend(ax, loc="lower left")
    # Line-end labels, spread vertically so their order matches the lines'.
    ends = spread([it[1] for it in items], 4.6)
    for (x, y, text, color), ylab in zip(items, ends):
        ax.annotate(text, (90, ylab), xytext=(8, 0), textcoords="offset points",
                    fontsize=7.3, color=INK2, va="center")
    finish(fig, out / "C1_massrev_vs_rpm.png",
           "Block D, 3 continuous revolutions per speed at 45 deg tilt - n = 1 per speed per run, "
           "so these are trends, not measured slopes.\n"
           "Normalised within powder so shape, not magnitude, is compared. Excluded (no resolvable "
           "15 RPM reference, or QC-flagged carry-over between speeds): " + ", ".join(dropped) + ".")


def figC2_traces(out: Path):
    """Streaming balance traces: dosing is discrete slugs, not a smooth flow."""
    picks = ["salt", "alsi10mg", "calcium-lactate", "carboxymethyl-cellulose"]
    fig, axes = plt.subplots(2, 2, figsize=(8.6, 5.0), sharex=True)
    for ax, pid in zip(axes.ravel(), picks):
        rid = REP[REP.powder_id == pid].run_id.iloc[0]
        sub = POLLS[(POLLS.run_id == rid) & (POLLS.rpm == 15.0)].copy()
        if sub.empty:
            ax.set_visible(False)
            continue
        t = (sub.t_ms - sub.t_ms.min()) / 1000
        ax.plot(t, (sub.grams - sub.grams.iloc[0]) * 1000, lw=1.6,
                color=track_color(pid))
        ax.set_title(f"{DISPLAY[pid]}", fontsize=9,
                     color=track_color(pid))
        ax.grid(alpha=0.6)
    for ax in axes[1]:
        ax.set_xlabel("Time within the 15 RPM burst (s)")
    for ax in axes[:, 0]:
        ax.set_ylabel("Delivered mass (mg)")
    fig.suptitle("C2 · Mass-vs-time traces reveal per-revolution slugs and stalls",
                 fontsize=11, fontweight="bold")
    fig.tight_layout()
    finish(fig, out / "C2_traces.png",
           "Block D streaming balance polls (~4 Hz) during 3 revolutions at 15 RPM, 45 deg tilt.")


# =============================================================================
# D - Fine actuation: the smallest increment the module can add
# =============================================================================

def resolved_tap(powder_id: str, tilt: float = 45.0):
    """Best resolved tap quantum for a powder, searching all QC-valid runs.

    A tap quantum counts as resolved only when the mean is positive and clears
    twice its own standard error.  Block E is the smallest signal in the
    battery, so most runs on a noisy bench do not resolve it at all - and a
    tap "quantum" that is negative, or smaller than its error bar, is the
    bench moving, not the solenoid.
    """
    best = None
    for rid in RUNS[RUNS.qc_valid & (RUNS.powder_id == powder_id)].run_id:
        row = FEED[(FEED.run_id == rid) & (FEED.phase == "tap")
                   & (FEED.tilt_deg == tilt)]
        if row.empty:
            continue
        mg = float(row.mean_g.iloc[0]) * 1000
        sem = float(row.sem_g.iloc[0] or 0) * 1000
        if mg > 0 and sem > 0 and mg > 2 * sem:
            if best is None or rid > best[0]:
                best = (rid, mg, sem)
    return best


# Documented measurement artifacts that must not be read as a tap quantum.
TAP_ARTIFACTS = {"fumed-silica"}


def figD1_tap_quantum(out: Path):
    """mg per solenoid tap against mg per revolution - the resolution ladder."""
    fig, ax = plt.subplots(figsize=(7.0, 4.5))
    items, unresolved = [], []
    for pid in sorted(REP.powder_id):
        rid = REP[REP.powder_id == pid].run_id.iloc[0]
        mg, _ = feed_factor(rid, 45.0)
        if pid in BOUNDED:
            mg = BOUNDED[pid]
        best = None if pid in TAP_ARTIFACTS else resolved_tap(pid)
        if best is None or not mg:
            unresolved.append(DISPLAY[pid])
            continue
        _, tmg, tsem = best
        ax.errorbar(mg, tmg, yerr=tsem, capsize=3, zorder=3,
                    fmt="o" if TRACK[pid] == "surrogate" else "s", ms=8,
                    color=track_color(pid), markeredgecolor=SURFACE,
                    markeredgewidth=1.0, elinewidth=1.1, ecolor=INK2)
        items.append((mg, tmg, DISPLAY[pid], track_color(pid)))
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.axhline(5, color=CRITICAL, lw=1.2, ls="--", zorder=1)
    ax.text(ax.get_xlim()[0] * 1.1, 5.7,
            "$\\pm$5 mg closed-loop tolerance", fontsize=7.2, color=CRITICAL)
    ax.set_xlim(ax.get_xlim()[0], ax.get_xlim()[1] * 2.4)
    ax.set_xlabel("Feed factor at 45$^\\circ$ (mg per revolution)")
    ax.set_ylabel("Tap quantum at 45$^\\circ$ (mg per solenoid tap)")
    ax.set_title("D1 \u00b7 The tap quantum does not track the feed factor",
                 fontsize=10.5)
    ax.grid(alpha=0.6, which="both")
    track_legend(ax, loc="lower right")
    place_labels(ax, items)
    finish(fig, out / "D1_tap_quantum.png",
           "Block E, 8 single-tap trials at 45 deg, each preceded by a measured re-feed "
           "rotation; error bars are the standard error of those 8 taps.\n"
           "Plotted only where the quantum resolves above its own noise (mean > 2 SE). "
           "Not resolved in any QC-valid run: " + ", ".join(unresolved) + ".")


# =============================================================================
# E - Closed loop: the headline dosing result
# =============================================================================

def figE1_dose_error(out: Path):
    """Error on 1.000 g closed-loop doses, per powder, against the +/-5 mg band."""
    d = DOSES.copy()
    d["mg"] = d.error_g * 1000
    missing = sorted({DISPLAY[p] for p in REP.powder_id} -
                     {DISPLAY[p] for p in d.powder_id})
    order = d.groupby("powder_id").mg.mean().sort_values(ascending=False).index
    fig, ax = plt.subplots(figsize=(7.4, 4.3))
    ax.axhspan(-5, 5, color=GOOD, alpha=0.13, zorder=0)
    ax.axhline(0, color=INK2, lw=1)
    for i, pid in enumerate(order):
        sub = d[d.powder_id == pid]
        for _, r in sub.iterrows():
            ax.scatter(i + np.random.uniform(-.13, .13), np.clip(r.mg, -120, 60),
                       s=54, color=STATUS.get(r.status, MUTED),
                       marker="v" if r.mg < -120 else
                       ("o" if TRACK[pid] == "surrogate" else "s"),
                       edgecolor=SURFACE, linewidth=0.8, zorder=3)
    ax.set_xticks(range(len(order)))
    ax.set_xticklabels([DISPLAY[p] for p in order], rotation=28,
                       ha="right", fontsize=8)
    ax.set_ylim(-128, 62)
    ax.set_ylabel("Dose error (mg) on a 1.000 g target")
    ax.set_title("E1 · Only the control powder lands inside the $\\pm$5 mg band",
                 fontsize=10.5)
    ax.grid(axis="y", alpha=0.6)
    handles = [Patch(facecolor=STATUS[s], label=s) for s in
               ["ok", "overshoot", "cycle-budget", "stalled"]]
    handles.append(Line2D([], [], marker="v", ls="", color=MUTED,
                          label="clipped (< -120 mg)"))
    ax.legend(handles=handles, fontsize=7.2, ncol=2, loc="lower left",
              title="controller termination", title_fontsize=7.2)
    finish(fig, out / "E1_dose_error.png",
           "Block G, 3 doses of 1.000 g per powder, frozen three-phase parameters tuned on NaCl. "
           "Silicon (-325 mesh) doses sit at -1000 mg (no conveyance) and are clipped.\n"
           "No valid block G exists for: " + ", ".join(missing) +
           " - those runs held block G back because the bench environment "
           "exceeded the +/-5 mg dose band.")


def figE2_dose_cost(out: Path):
    """What a 1 g dose costs in wall-clock time, and how it ended."""
    d = DOSES[DOSES.elapsed_s > 0].copy()
    order = d.groupby("powder_id").elapsed_s.median().sort_values().index
    fig, ax = plt.subplots(figsize=(7.4, 4.2))
    for i, pid in enumerate(order):
        sub = d[d.powder_id == pid]
        ax.plot([sub.elapsed_s.min(), sub.elapsed_s.max()], [i, i],
                color=MUTED, lw=1.1, zorder=1)
        for _, r in sub.iterrows():
            ax.scatter(r.elapsed_s, i, s=72, color=STATUS.get(r.status, MUTED),
                       marker="o" if TRACK[pid] == "surrogate" else "s",
                       edgecolor=SURFACE, linewidth=1.0, zorder=3)
        ax.text(sub.elapsed_s.max() * 1.16, i,
                f"{int(sub.taps.mean())} taps", va="center", fontsize=7,
                color=INK2)
    ax.set_yticks(range(len(order)))
    ax.set_yticklabels([DISPLAY[p] for p in order], fontsize=8)
    ax.set_xscale("log")
    ax.set_xlim(4, 3000)
    ax.set_ylim(-0.7, len(order) - 0.3)
    ax.set_xlabel("Time to terminate the dose (s, log scale)")
    ax.set_title("E2 \u00b7 A fast dose is not a good dose: read the outcome, not the clock",
                 fontsize=10.5)
    ax.grid(axis="x", alpha=0.6)
    handles = [Patch(facecolor=STATUS[k], label=k) for k in
               ["ok", "overshoot", "cycle-budget", "stalled"]]
    ax.legend(handles=handles, fontsize=7.2, ncol=2, loc="lower right",
              title="controller termination", title_fontsize=7.2)
    finish(fig, out / "E2_dose_cost.png",
           "Block G, 3 doses of 1.000 g per powder; each marker is one dose, the grey rule spans "
           "the three. Annotation is the mean solenoid taps consumed.\n"
           "Silicon (-325 mesh) and brown rice flour terminate in seconds because they stall "
           "immediately; sodium alginate and white rice flour exhaust the 200-cycle fine budget.")


def figE3_phase_effort(out: Path):
    """Where the controller spends its cycles: bulk, fine, or tapping."""
    rows = []
    for _, r in DOSES.iterrows():
        parts = dict(p.split(":") for p in str(r.phase_cycles).split(";") if ":" in p)
        rows.append({"powder_id": r.powder_id, "status": r.status,
                     **{k: int(v) for k, v in parts.items()}})
    df = pd.DataFrame(rows).fillna(0)
    agg = df.groupby("powder_id")[["bulk", "fine", "tap"]].mean()
    agg = agg.loc[agg.sum(axis=1).sort_values().index]
    fig, ax = plt.subplots(figsize=(7.0, 4.0))
    left = np.zeros(len(agg))
    for phase, color in zip(["bulk", "fine", "tap"], TILT_RAMP.values()):
        ax.barh(range(len(agg)), agg[phase], left=left, height=0.62,
                color=color, label=f"phase {phase}", edgecolor=SURFACE, linewidth=1.4)
        left += agg[phase].values
    ax.set_yticks(range(len(agg)))
    ax.set_yticklabels([DISPLAY[p] for p in agg.index], fontsize=8)
    ax.set_xlabel("Mean controller cycles per 1.000 g dose")
    ax.set_title("E3 · Controller effort splits by phase and by powder",
                 fontsize=10.5)
    ax.grid(axis="x", alpha=0.6)
    ax.legend(fontsize=7.5, ncol=3, loc="lower right")
    finish(fig, out / "E3_phase_effort.png",
           "Block G, mean of 3 doses. A powder that never leaves 'bulk' never reached the "
           "fine-approach phase - it stalled.")


# =============================================================================
# F - Synthesis: the operating map
# =============================================================================

def figF1_operating_map(out: Path):
    """Two measured numbers place a powder on a dose-ability map."""
    fig, ax = plt.subplots(figsize=(7.4, 5.0))
    ax.axvspan(0.08, 10, color=CRITICAL, alpha=0.07)
    ax.axvspan(10, 100, color=WARNING, alpha=0.08)
    ax.axvspan(100, 1400, color=GOOD, alpha=0.08)
    ax.text(0.33, 480, "not\ndoseable", fontsize=7.8, color=CRITICAL,
            ha="center", va="top")
    ax.text(31, 480, "slow /\nfine only", fontsize=7.8, color="#9a6a00",
            ha="center", va="top")
    ax.text(370, 480, "readily\ndoseable", fontsize=7.8, color="#0a7a0a",
            ha="center", va="top")
    items = []
    for pid in REP.powder_id:
        rid = REP[REP.powder_id == pid].run_id.iloc[0]
        mg, rsd = feed_factor(rid, 45.0)
        if pid in BOUNDED:
            mg, rsd = BOUNDED[pid], 200
        if not mg or not np.isfinite(rsd):
            continue
        ax.scatter(mg, rsd, s=120, color=track_color(pid),
                   marker="o" if TRACK[pid] == "surrogate" else "s",
                   edgecolor=SURFACE, linewidth=1.2, zorder=4,
                   alpha=0.45 if pid in BOUNDED else 1.0)
        items.append((mg, rsd, DISPLAY[pid], track_color(pid)))
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlim(0.1, 1400)
    ax.set_ylim(1.2, 700)
    ax.set_xlabel("Feed factor at 45$^\\circ$ (mg per revolution)  $\\rightarrow$  throughput")
    ax.set_ylabel("Revolution RSD (%)  $\\rightarrow$  scatter")
    ax.set_title("F1 · A two-number fingerprint places any new powder on the map",
                 fontsize=10.5)
    ax.grid(alpha=0.5, which="both")
    track_legend(ax, loc="lower left")
    place_labels(ax, items)
    finish(fig, out / "F1_operating_map.png",
           "Both axes come from block C alone (~2 min of bench time). Faded markers are "
           "upper-bound powders, plotted at their bound.")


def figF2_environment(out: Path):
    """The balance environment across the campaign, and what it cost.

    Block A is eight no-actuation reads at the start of every run: it is the
    measurement floor every later number in that run had to be seen through.
    It is flat zero for the whole food-safe batch and becomes the binding
    constraint after the rig moved into the fume hood - which is why the
    research-relevant powders have no closed-loop dose block.
    """
    rows = []
    for _, r in RUNS.iterrows():
        base = TRIALS[(TRIALS.run_id == r.run_id) & (TRIALS.block == "A")]
        if base.empty:
            continue
        rows.append({
            "run_id": r.run_id, "powder_id": r.powder_id, "track": r.track,
            "date": r.run_id[:8], "spread_mg": (base.delta_g.max() -
                                                base.delta_g.min()) * 1000,
            "has_dose": r.run_id in set(DOSES.run_id),
        })
    df = pd.DataFrame(rows).sort_values("run_id").reset_index(drop=True)
    fig, ax = plt.subplots(figsize=(8.4, 4.3))
    x = np.arange(len(df))
    ax.axhspan(0, 10, color=GOOD, alpha=0.12, zorder=0)
    ax.text(0.15, 10.6, "block A spread within the $\\pm$5 mg dose band",
            fontsize=7.2, color="#0a7a0a")
    for i, r in df.iterrows():
        colour = RESEARCH if r.track == "research" else SURROGATE
        ax.bar(i, max(r.spread_mg, 0.18), color=colour, width=0.62,
               alpha=1.0 if r.has_dose else 0.42, zorder=3)
        if not r.has_dose:
            ax.text(i, max(r.spread_mg, 0.18) + 2, "no\nblock G", ha="center",
                    fontsize=6.2, color=INK2)
    # The rig moved into the fume hood between 2026-08-12 and 2026-08-20.
    move = df.index[df.date >= "20260820"].min()
    ax.axvline(move - 0.5, color=INK2, lw=1.2, ls="--")
    ax.text(move - 0.35, ax.get_ylim()[1] * 0.93, "fume-hood move",
            fontsize=7.4, color=INK2)
    ax.set_xticks(x)
    ax.set_xticklabels([f"{r.date[4:6]}-{r.date[6:]}  {DISPLAY[r.powder_id]}"
                        for _, r in df.iterrows()], rotation=52, ha="right",
                       fontsize=6.9)
    ax.set_ylabel("Block A no-actuation spread (mg)")
    ax.set_title("F2 \u00b7 The bench, not the powder, decided which runs could close the loop",
                 fontsize=10.5)
    ax.grid(axis="y", alpha=0.6)
    handles = [Patch(facecolor=SURROGATE, label="Surrogate"),
               Patch(facecolor=RESEARCH, label="Research-relevant"),
               Patch(facecolor=MUTED, alpha=0.5, label="Block G withheld")]
    ax.legend(handles=handles, fontsize=7.4, loc="upper left")
    finish(fig, out / "F2_environment.png",
           "Spread is max - min over the 8 block A trials, which run with no actuation at all. "
           "Bars at the axis floor are runs where all 8 reads were identical.\n"
           "Faded bars are runs whose block G was not attempted, or whose doses failed QC.")


def main(outdir: Path):
    outdir.mkdir(parents=True, exist_ok=True)
    np.random.seed(0)
    print(f"writing candidate figures to {outdir}")
    for fn in (figA1_feed_vs_tilt, figA2_feed_rank, figA3_tilt_sensitivity,
               figB1_rsd_vs_feed, figB2_salt_repeats, figC1_massrev_vs_rpm,
               figC2_traces, figD1_tap_quantum, figE1_dose_error,
               figE2_dose_cost, figE3_phase_effort, figF1_operating_map,
               figF2_environment):
        fn(outdir)


if __name__ == "__main__":
    main(Path(sys.argv[1]) if len(sys.argv) > 1 else HERE / "out")
