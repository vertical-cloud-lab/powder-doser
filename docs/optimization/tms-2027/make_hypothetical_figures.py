"""Two hypothetical results figures for the TMS 2027 abstract (issue #179).

The abstract ("Auger-Based Powder Dosing as a Mechanistic Probe of Powder Flow
Behavior: Multi-Task Bayesian Calibration and Physics-Based Property
Inference", written in PR #78) makes two claims that need a core figure each:

1. Multi-task Bayesian optimization shares information across powders and
   cuts per-powder calibration effort.
2. Dosing data, read through a discrete element model (DEM), recover effective
   cohesion and friction that agree with shear-cell measurements.

Neither experiment has been run, so both figures are mostly dummy data and are
watermarked as such.  Only these elements are measured:

* Figure 1, black points: the salt campaign of PR #166
  (data/opt/salt-20260929T014732Z/campaign_records.jsonl): the 4 doses at the
  hand-tuned settings and the 8 validation doses of the recommended point
  bo-005, found after 42 campaign doses.
* Figure 2, left panel: the #116 battery's feed factor at 90 deg tilt (QC-valid
  runs) against the literature angle of repose, both as tabulated for #163 on
  branch claude/issue-163-20260918-2102 at e7b7964
  (data/powder-properties/battery_responses.csv and
  literature_powder_properties.csv).  The angles of repose are literature
  values, not measurements of our lots.

Everything else (the learning curves in Figure 1, the ellipses and crosses in
Figure 2) is invented to show what the result would look like.  It is not a
prediction.

Slides are 13.333 x 7.5 in (16:9), so a matplotlib point is a PowerPoint point
when the PNG fills the slide; no text is smaller than 24 pt (the look of the
PR #175 slides: message top left, no titles or legends, series named in their
own colour).

    python docs/optimization/tms-2027/make_hypothetical_figures.py
"""
from __future__ import annotations

import json
import statistics
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib import font_manager  # noqa: E402
from matplotlib.patches import Ellipse  # noqa: E402
from scipy.stats import spearmanr  # noqa: E402

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
CAMPAIGN = REPO / "data/opt/salt-20260929T014732Z"

for f in font_manager.findSystemFonts():
    if "Lato" in f:
        font_manager.fontManager.addfont(f)

FIG_IN = (13.3334, 7.5)
DPI = 144                 # 1920 x 1080

INK = "#0b0b0b"
INK2 = "#52514e"
GREY = "#83827d"
FAINT = "#c9c7c1"
BLUE = "#2a78d6"
BLUE_LIGHT = "#cde2fb"
ORANGE = "#eb6834"
MARK = "#c0392b"          # watermark

FS = 24
FS_TITLE = 32
TITLE_XY = (0.045, 0.935)

plt.rcParams.update({
    "font.family": ["Lato", "DejaVu Sans"],
    "font.size": FS,
    "axes.labelsize": FS,
    "xtick.labelsize": FS,
    "ytick.labelsize": FS,
    "axes.edgecolor": INK2,
    "axes.labelcolor": INK,
    "xtick.color": INK2,
    "ytick.color": INK2,
    "xtick.labelcolor": INK,
    "ytick.labelcolor": INK,
    "axes.linewidth": 1.4,
    "xtick.major.width": 1.4,
    "ytick.major.width": 1.4,
    "xtick.major.size": 7,
    "ytick.major.size": 7,
    "xtick.minor.size": 0,
    "ytick.minor.size": 0,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.grid": False,
    "figure.facecolor": "white",
    "axes.facecolor": "white",
    "savefig.facecolor": "white",
    "lines.solid_capstyle": "round",
})


def slide(message):
    fig = plt.figure(figsize=FIG_IN)
    fig.text(*TITLE_XY, message, fontsize=FS_TITLE, color=INK, ha="left", va="top",
             linespacing=1.15)
    return fig


def style_axes(ax, xlim, ylim, xticks, yticks, xlabels=None, ylabels=None):
    ax.set_xlim(*xlim)
    ax.set_ylim(*ylim)
    ax.set_xticks(xticks)
    ax.set_yticks(yticks)
    if xlabels:
        ax.set_xticklabels(xlabels)
    if ylabels:
        ax.set_yticklabels(ylabels)
    ax.minorticks_off()
    for side in ("left", "bottom"):
        ax.spines[side].set_position(("outward", 14))
    ax.spines["left"].set_bounds(yticks[0], yticks[-1])
    ax.spines["bottom"].set_bounds(xticks[0], xticks[-1])
    ax.tick_params(pad=6)


def ylabel_top(ax, text, y=1.04):
    ax.text(0.0, y, text, transform=ax.transAxes, ha="left", va="bottom", fontsize=FS,
            color=INK, linespacing=1.2)


def xlabel(ax, text, pad=12):
    ax.set_xlabel(text, fontsize=FS, color=INK, labelpad=pad, loc="left")


def callout(ax, text, xy, xytext, color, ha="left", va="center", alpha=0.45, lw=1.8,
            fs=FS, coords="data"):
    return ax.annotate(text, xy=xy, xytext=xytext, textcoords=coords, fontsize=fs, color=color,
                       ha=ha, va=va, zorder=6, linespacing=1.15,
                       arrowprops=dict(arrowstyle="-", color=color, alpha=alpha, lw=lw,
                                       shrinkA=6, shrinkB=7))


def textrow(fig, x, y, parts, gap="   "):
    """One line of text in several colours: parts = [(text, colour), ...]."""
    r = fig.canvas.get_renderer()
    for i, (text, colour) in enumerate(parts):
        t = fig.text(x, y, text + (gap if i < len(parts) - 1 else ""), fontsize=FS,
                     color=colour, ha="left", va="bottom")
        x = fig.transFigure.inverted().transform(t.get_window_extent(r))[1][0]


def watermark(ax, text="DUMMY DATA", fontsize=86):
    ax.text(0.5, 0.5, text, transform=ax.transAxes, ha="center", va="center", rotation=22,
            fontsize=fontsize, fontweight="bold", color=MARK, alpha=0.12, zorder=10)


# --------------------------------------------------------------------------
# Figure 1: doses needed to calibrate a new powder, single-task vs multi-task
# --------------------------------------------------------------------------

def salt_measured():
    """Hand-tuned doses (dose 0) and the validated recommendation (after 42)."""
    hand, val = [], []
    for line in open(CAMPAIGN / "campaign_records.jsonl"):
        r = json.loads(line)
        s = r["summary"]
        if r["label"] in ("baseline-00", "baseline-01", "rebaseline-00", "rebaseline-01"):
            hand.append(s["t_total_s"])
        # the 2026-10-06 block that wrote the profile: the last 8 bo-005 replicates
        if r["label"].startswith("val-bo-005-"):
            val.append(s["t_total_s"])
    val = val[-8:]
    n_campaign = sum(1 for line in open(CAMPAIGN / "campaign_records.jsonl")
                     if json.loads(line)["mode"] != "validation")
    return hand, val, n_campaign


def figure_multitask(out: Path):
    hand, val, n_campaign = salt_measured()
    hand_med, val_med = statistics.median(hand), statistics.median(val)

    # Dummy learning curves: median dose time of the best settings found after
    # n doses on a new powder, with the spread over 6 held-out powders.
    # Single-task starts from hand-tuned settings; multi-task starts from what
    # the other powders' doses predict.  Invented, not predicted.
    n = np.linspace(0, 50, 501)
    best = 80.0

    def curve(y0, k):
        return best + (y0 - best) * np.exp(-n / k)

    single = curve(hand_med, 13.0)
    multi = curve(150.0, 6.5)
    single_lo, single_hi = curve(hand_med * 0.8, 10.0) - 8, curve(hand_med * 1.2, 17.0) + 10
    multi_lo, multi_hi = curve(120.0, 5.0) - 7, curve(185.0, 8.5) + 9
    target = best * 1.10
    n_single = float(n[np.argmax(single <= target)])
    n_multi = float(n[np.argmax(multi <= target)])

    fig = slide("Expected: doses from other powders should cut a new\n"
                "powder's calibration from about 40 doses to about 15")
    ax = fig.add_axes([0.1, 0.27, 0.84, 0.43])
    watermark(ax)

    ax.fill_between(n, single_lo, single_hi, color=FAINT, alpha=0.55, lw=0, zorder=1)
    ax.fill_between(n, multi_lo, multi_hi, color=BLUE_LIGHT, alpha=0.75, lw=0, zorder=1)
    ax.plot(n, single, color=GREY, lw=3.2, zorder=3)
    ax.plot(n, multi, color=BLUE, lw=3.2, zorder=3)
    ax.axhline(target, xmin=0.02, color=INK2, lw=1.4, ls=(0, (2, 3)), zorder=2)
    ax.plot([n_multi, n_multi], [0, target], color=BLUE, lw=1.6, alpha=0.55, zorder=2)
    ax.plot([n_single, n_single], [0, target], color=GREY, lw=1.6, alpha=0.75, zorder=2)

    # measured salt points: median and range
    for x, ts in ((0, hand), (n_campaign, val)):
        ax.plot([x, x], [min(ts), max(ts)], color=INK, lw=2.4, zorder=5, solid_capstyle="butt")
        ax.plot(x, statistics.median(ts), "o", ms=13, color=INK, mec="white", mew=2.2, zorder=6)

    style_axes(ax, (-1.2, 51), (0, 400), [0, 10, 20, 30, 40, 50], [0, 100, 200, 300, 400])
    ylabel_top(ax, "Time per 0.5 g dose with the best settings so far (s)")
    xlabel(ax, "Doses on the new powder")

    callout(ax, f"salt, hand-tuned: {hand_med:.0f} s", (0, hand_med), (2.5, 365), INK)
    callout(ax, "one powder at a time", (10, single[np.searchsorted(n, 10)]), (13, 290), GREY)
    callout(ax, f"salt after {n_campaign} doses, validated: {val_med:.0f} s", (n_campaign, val_med),
            (50, 215), INK, ha="right")
    callout(ax, "sharing data across powders", (20, multi[np.searchsorted(n, 20)]), (15.6, 30),
            BLUE)
    callout(ax, "best + 10 %", (45.5, target), (40.4, 30), INK2)

    textrow(fig, 0.1, 0.035, [("Black: measured on salt (PR #166).", INK),
                              ("Lines and bands: dummy data.", MARK)])
    fig.savefig(out, dpi=DPI)
    plt.close(fig)
    return dict(hand_median_s=hand_med, val_median_s=val_med, n_campaign=n_campaign,
                n_single_dummy=n_single, n_multi_dummy=n_multi)


# --------------------------------------------------------------------------
# Figure 2: dosing data as a probe of cohesion and friction
# --------------------------------------------------------------------------

# #116 battery feed factor at 90 deg tilt (mg/rev, QC-valid runs) and the
# literature angle of repose (deg), from #163 (branch
# claude/issue-163-20260918-2102 at e7b7964).
BATTERY = [
    # powder,                   ff90,   AoR, label
    ("salt",                    247.80, 32, "salt"),
    ("white-rice-flour",        37.15,  45, None),
    ("brown-rice-flour",        0.20,   47, "brown rice flour"),
    ("sodium-alginate",         10.87,  42, None),
    ("calcium-lactate",         232.25, 40, None),
    ("carboxymethyl-cellulose", 9.35,   41, None),
    ("xanthan-gum",             186.77, 35, None),
    ("sodium-sulfate",          243.55, 32, None),
    ("silicon-110-200",         302.35, 36, None),
    ("silicon-325",             1.20,   43, "Si, -325 mesh"),
    ("alsi10mg",                338.93, 30, "AlSi10Mg"),
    ("barium-chloride",         200.38, 34, None),
]

# Dummy: internal friction angle (deg) and cohesion (kPa) per powder.  The
# ellipse is the 90 % region inferred from doses through DEM, the cross the
# shear-cell measurement.  Invented, not predicted.
# (name, phi, c, sd phi, sd log10 c, measured phi, measured c, label x, label c, ha)
PROPERTIES = [
    ("316L",       29.0, 0.10, 0.9, 0.08, 29.5, 0.115, 28.6, 0.047, "center"),
    ("AlSi10Mg",   31.2, 0.22, 0.9, 0.08, 31.6, 0.19,  26.0, 0.70,  "left"),
    ("Al 4047",    34.4, 0.45, 1.1, 0.09, 33.9, 0.38,  34.4, 1.25,  "center"),
    ("salt",       35.6, 0.06, 1.0, 0.09, 36.1, 0.07,  38.0, 0.058, "left"),
    ("Si 110/200", 38.6, 0.17, 1.1, 0.09, 39.3, 0.20,  41.2, 0.17,  "left"),
    ("Si −325",    41.0, 1.20, 1.3, 0.11, 40.3, 1.45,  41.0, 2.75,  "center"),
]
LEADER_TO = {"AlSi10Mg": (31.2, 0.31)}


def figure_properties(out: Path):
    ff = np.array([b[1] for b in BATTERY])
    aor = np.array([b[2] for b in BATTERY])
    rho = spearmanr(aor, ff).statistic

    fig = slide("The doser already ranks powders by flow; with DEM, its\n"
                "doses should also give each powder's cohesion and friction")

    # left: measured
    axl = fig.add_axes([0.115, 0.305, 0.33, 0.395])
    axl.scatter(aor, ff, s=150, color=INK, edgecolor="white", linewidth=2.0, zorder=4)
    axl.set_yscale("log")
    style_axes(axl, (29, 48), (0.1, 1000), [30, 35, 40, 45], [0.1, 1, 10, 100, 1000],
               ylabels=["0.1", "1", "10", "100", "1000"])
    ylabel_top(axl, "Powder per auger turn, vertical (mg)")
    xlabel(axl, "Angle of repose (°)")
    lab = {b[3]: (b[2], b[1]) for b in BATTERY if b[3]}
    callout(axl, "AlSi10Mg", lab["AlSi10Mg"], (31.0, 900), INK)
    callout(axl, "salt", lab["salt"], (32.6, 60), INK, ha="center")
    callout(axl, "Si, −325 mesh", lab["Si, -325 mesh"], (41.6, 1.2), INK, ha="right")
    callout(axl, "brown rice flour", lab["brown rice flour"], (46.0, 0.2), INK, ha="right")
    axl.text(48, 420, f"12 powders\nρ = {rho:.2f}".replace("-", "−"), ha="right", va="center",
             fontsize=FS, color=INK, linespacing=1.2)

    # right: dummy
    axr = fig.add_axes([0.6, 0.305, 0.34, 0.395])
    watermark(axr, fontsize=64)
    for name, phi, c, sphi, slc, mphi, mc, lx, lc, ha in PROPERTIES:
        # 90 % region of a 2-D Gaussian: 2.146 sd along each axis
        axr.add_patch(Ellipse((phi, np.log10(c)), 2 * 2.146 * sphi, 2 * 2.146 * slc,
                              facecolor=BLUE_LIGHT, edgecolor=BLUE, lw=2.0, alpha=0.9, zorder=2))
        axr.plot(mphi, np.log10(mc), marker="x", ms=15, mew=3.4, color=INK, zorder=4)
        if name in LEADER_TO:
            tx, tc = LEADER_TO[name]
            callout(axr, name, (tx, np.log10(tc)), (lx, np.log10(lc)), BLUE, ha=ha)
        else:
            axr.text(lx, np.log10(lc), name, fontsize=FS, color=BLUE, ha=ha, va="center",
                     zorder=5)
    style_axes(axr, (25.5, 46.5), np.log10([0.03, 3]), [26, 30, 34, 38, 42, 46],
               np.log10([0.03, 0.1, 0.3, 1, 3]), ylabels=["0.03", "0.1", "0.3", "1", "3"])
    ylabel_top(axr, "Cohesion (kPa)")
    xlabel(axr, "Internal friction angle (°)")
    textrow(fig, 0.115, 0.075, [("Left: measured on the doser (#116); angle of repose from "
                                 "literature (#163).", INK)])
    textrow(fig, 0.115, 0.02, [("Right: dummy data.", MARK),
                               ("Blue: 90 % region from doses via DEM.", BLUE),
                               ("×: shear cell.", INK)])
    fig.savefig(out, dpi=DPI)
    plt.close(fig)
    return dict(spearman_rho_aor_ff90=round(float(rho), 3), n_powders=len(BATTERY))


if __name__ == "__main__":
    s1 = figure_multitask(HERE / "fig1_multitask_calibration.png")
    s2 = figure_properties(HERE / "fig2_property_inference.png")
    print(json.dumps({"fig1": s1, "fig2": s2}, indent=1))
