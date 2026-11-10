#!/usr/bin/env python3
"""Fig. 2 (v2): how the design moved between the AI agents and the engineers.

Laid out as drawn on the 27 Oct whiteboard (sources/brainstorm-whiteboard-
2026-10-27.png): a timeline from April to November 2026 with the key AI-modelled
designs above the axis, the engineers' work (hand drawings, conventional CAD,
the built doser) below it, and the agents and models along the bottom.  Panel
(b) puts original AI parts beside what replaced them.

Every image is a committed render or photograph, copied with its provenance into
assets/timeline/ (SOURCES.json lists branch, path and commit).  Dates are those
of the design-log entries and pull requests (paper/figures/data/design_log_cad.csv,
ai_tools_timeline.csv).

Usage:  python3 make_fig2_timeline.py
"""

from __future__ import annotations

import datetime as dt
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyArrowPatch
from PIL import Image

HERE = Path(__file__).resolve().parent
ASSETS = HERE / "assets" / "timeline"
FIGS, PREVIEW = HERE / "figures", HERE / "preview"

INK, INK2, MUTED, FAINT = "#0b0b0b", "#52514e", "#b8b6ae", "#e8e6e0"
AI_EDGE, ENG_EDGE = "#4a3aa7", "#52514e"
TOOL_COLOUR = {
    "copilot": "#4a3aa7",       # same hue as SI agent-activity figure
    "claude": "#1baf7a",
    "cadsmith": "#c98500",
    "zoo": "#0f8fb8",
    "people": "#8a8984",
}
W_IN = 17.1 / 2.54

plt.rcParams.update({
    "font.size": 6.0, "font.family": "sans-serif", "axes.linewidth": 0.6,
    "savefig.dpi": 600,
})


def D(s: str) -> float:
    return mdates.date2num(dt.date.fromisoformat(s))


def prep(name: str, crop: tuple[float, float, float, float] | None = None) -> np.ndarray:
    """Load an asset, invert black-background wireframes, trim the margins."""
    im = Image.open(ASSETS / name).convert("RGB")
    if crop:                                    # fractional (l, t, r, b)
        w, h = im.size
        im = im.crop((int(crop[0] * w), int(crop[1] * h),
                      int(crop[2] * w), int(crop[3] * h)))
    a = np.asarray(im).astype(float) / 255
    if a.mean() < 0.35:                         # wireframe on black
        a = 1 - a
    bg = a[0, 0]
    mask = np.abs(a - bg).sum(axis=2) > 0.08
    if mask.any():
        ys, xs = np.where(mask)
        pad = 6
        a = a[max(ys.min() - pad, 0):ys.max() + pad,
              max(xs.min() - pad, 0):xs.max() + pad]
    return a


# ----------------------------------------------------------------------------
# Content
# ----------------------------------------------------------------------------
# (date on the axis, image, crop, title, tool, model)
AI_ITEMS = [
    ("2026-04-24", "ai_excavator.png", None, "Powder excavator", "Copilot", "Opus 4.7"),
    ("2026-04-24", "ai_first_auger.png", None, "First auger", "Claude Code", "Sonnet 4.6"),
    ("2026-05-13", "ai_whole_module.png", (0.0, 0.0, 0.62, 1.0), "Whole module,\none request", "Copilot", "Opus 4.7"),
    ("2026-05-14", "ai_bracket.png", None, "Bracket from\nthe drawing", "Copilot", "Opus 4.7"),
    ("2026-05-15", "ai_tap_collar_v1.png", None, "First tap collar", "Copilot", "Opus 4.7"),
    ("2026-06-10", "ai_tap_collar_revised.png", None, "Tap collar,\nafter review", "Copilot", "Opus 4.7, Fable 5"),
    ("2026-06-16", "ai_storage_auger_xsec.png", None, "Storage auger,\nscrew cap", "Copilot", "Opus 4.8"),
    ("2026-06-22", "ai_zoo_t2c_doser.png", (0.1, 0.18, 0.92, 0.82), "Whole doser,\n11 parts", "Zoo Text-to-CAD", "'kcl' model"),
    ("2026-10-01", "ai_onshape_assembly.png", None, "Team's parts,\nassembled", "Claude Code", "Opus 5.5, Onshape API"),
]
ENG_ITEMS = [
    ("2026-04-22", "eng_hackathon_sketch.jpg", None, "Hackathon sketch", "hand drawing"),
    ("2026-04-24", "eng_pose_tube.png", (0.0, 0.0, 0.5, 0.42), "First auger,\nprinted and tested", "photo"),
    ("2026-05-14", "eng_bracket_drawing.png", None, "Bracket drawing\nfor the agent", "hand drawing"),
    ("2026-07-17", "eng_fusion_auger.png", None, "Auger, cap,\n44-tooth gear", "Fusion 360"),
    ("2026-07-24", "eng_glovebox_first_dose.jpg", (0.05, 0.0, 0.95, 1.0), "First dose in\na glove box", "photo"),
    ("2026-08-19", "eng_multidoser_sketch.png", None, "Multi-doser\ncarriage", "hand drawing"),
    ("2026-08-19", "eng_multidoser_onshape.png", None, "Multi-doser\ncarriages", "Onshape"),
    ("2026-09-11", "eng_rig_2026-09-11.jpg", None, "Doser as tested", "photo, 11 Sep"),
]
# Agent + model band: (tool, colour key, start, end, models)
BAND = [
    ("GitHub Copilot coding agent", "copilot", "2026-04-23", "2026-06-30",
     "Claude Opus 4.7 → Opus 4.8"),
    ("Claude Code, local", "claude", "2026-04-23", "2026-04-25", "Claude Sonnet 4.6"),
    ("CADSmith, run by the agent", "cadsmith", "2026-05-12", "2026-06-22",
     "Claude Sonnet 4.5 / Opus 4.5"),
    ("Zoo Text-to-CAD API", "zoo", "2026-05-12", "2026-06-30", "'kcl' model"),
    ("Zoo Design Studio", "zoo", "2026-05-18", "2026-07-17", "Zookeeper agent"),
    ("Claude Code, GitHub Actions", "claude", "2026-06-30", "2026-11-10",
     "Opus 4.8, Fable 5, Opus 5, Opus 5.5: rig, data, Onshape assembly (Oct)"),
    ("Engineers, conventional CAD", "people", "2026-07-02", "2026-11-10",
     "Fusion 360 from 2 Jul (#120); Onshape from Aug"),
]
EVENTS = [("2026-04-22", "2026-04-24", "Hackathon"),
          ("2026-08-04", "2026-09-15", "Tests: 13 powders")]

X0, X1 = D("2026-04-12"), D("2026-11-15")
AX_L, AX_R = 0.05, 0.985


def thumb(fig, rect, img, edge, lines, above):
    ax = fig.add_axes(rect)
    ax.imshow(img, interpolation="lanczos")
    ax.set_xticks([]), ax.set_yticks([])
    ax.set_aspect("equal")
    for sp in ax.spines.values():
        sp.set_edgecolor(edge)
        sp.set_linewidth(0.7)
    x, y, w, h = rect
    if above:
        fig.text(x + w / 2, y + h + 0.006, lines, ha="center", va="bottom",
                 fontsize=4.8, color=INK, linespacing=1.12)
    else:
        fig.text(x + w / 2, y - 0.006, lines, ha="center", va="top",
                 fontsize=4.8, color=INK, linespacing=1.12)
    return ax


def slots(n, x0, x1, w):
    centres = np.linspace(x0 + w / 2, x1 - w / 2, n)
    return [c - w / 2 for c in centres]


def ax_x(date: float) -> float:
    return AX_L + (date - X0) / (X1 - X0) * (AX_R - AX_L)


def fig2_timeline() -> None:
    fig = plt.figure(figsize=(W_IN, 5.3))
    y_axis = 0.585
    ax_axis = fig.add_axes([AX_L, y_axis, AX_R - AX_L, 0.001])
    ax_axis.set_xlim(X0, X1)
    ax_axis.set_yticks([])
    for sp in ("left", "right", "top"):
        ax_axis.spines[sp].set_visible(False)
    ax_axis.spines["bottom"].set_color(INK)
    ax_axis.spines["bottom"].set_linewidth(1.0)
    ax_axis.xaxis.set_major_locator(mdates.MonthLocator())
    ax_axis.xaxis.set_major_formatter(mdates.DateFormatter("%b 2026"))
    ax_axis.tick_params(axis="x", labelsize=5.8, colors=INK, length=3, pad=1.5)

    over = fig.add_axes([0, 0, 1, 1], zorder=-1)
    over.set_xlim(0, 1), over.set_ylim(0, 1), over.axis("off")
    for a, b, label in EVENTS:
        xa, xb = ax_x(D(a)), ax_x(D(b))
        over.add_patch(plt.Rectangle((xa, y_axis - 0.007), max(xb - xa, 0.005),
                                     0.014, color="#f1e6c8", zorder=0))
        over.text((xa + xb) / 2 if xb - xa > 0.05 else xa, y_axis + 0.012,
                  label, fontsize=4.9, color="#8a6300",
                  ha="center" if xb - xa > 0.05 else "left", va="bottom")

    # AI row, above the axis
    w, h, y_ai = 0.088, 0.17, 0.705
    xs = slots(len(AI_ITEMS), AX_L, AX_R, w)
    for (date, name, crop, title, tool, model), x in zip(AI_ITEMS, xs):
        thumb(fig, [x, y_ai, w, h], prep(name, crop), AI_EDGE,
              f"{title}\n{tool}\n{model}", above=True)
        over.plot([x + w / 2, ax_x(D(date))], [y_ai - 0.004, y_axis + 0.003],
                  color=AI_EDGE, lw=0.5, alpha=0.65)
        over.plot(ax_x(D(date)), y_axis, "o", ms=2.3, color=AI_EDGE, zorder=5)

    # Engineer row, below the axis
    w2, h2, y_eng = 0.098, 0.17, 0.335
    n_eng = len(ENG_ITEMS) + 1                  # last slot: final photo
    xs = slots(n_eng, AX_L, AX_R, w2)
    for (date, name, crop, title, tool), x in zip(ENG_ITEMS, xs):
        thumb(fig, [x, y_eng, w2, h2], prep(name, crop), ENG_EDGE,
              f"{title}\n{tool}", above=False)
        over.plot([x + w2 / 2, ax_x(D(date))], [y_eng + h2 + 0.004, y_axis - 0.003],
                  color=ENG_EDGE, lw=0.5, alpha=0.65)
        over.plot(ax_x(D(date)), y_axis, "s", ms=2.1, color=ENG_EDGE, zorder=5)
    xp = xs[-1]
    over.add_patch(plt.Rectangle((xp, y_eng), w2, h2, fill=False,
                                 ls=(0, (2, 2)), lw=0.7, edgecolor=ENG_EDGE))
    over.text(xp + w2 / 2, y_eng + h2 / 2, "Final doser\n(photo to\nbe taken)",
              ha="center", va="center", fontsize=4.9, color=INK2, style="italic")
    over.text(xp + w2 / 2, y_eng - 0.006, "Final version\nphoto",
              ha="center", va="top", fontsize=4.8, color=INK, linespacing=1.12)
    over.plot([xp + w2 / 2, ax_x(D("2026-11-05"))], [y_eng + h2 + 0.004, y_axis - 0.003],
              color=ENG_EDGE, lw=0.5, alpha=0.65, ls=(0, (2, 2)))

    # drawing -> AI model (Sam, 23:37): the bracket drawing went to the agent
    xd = slots(n_eng, AX_L, AX_R, w2)[2]
    xa = slots(len(AI_ITEMS), AX_L, AX_R, w)[3]
    over.add_patch(FancyArrowPatch(
        (xd + w2 * 0.75, y_eng + h2 + 0.004), (xa + w * 0.35, y_ai - 0.004),
        connectionstyle="arc3,rad=0.18", arrowstyle="-|>", mutation_scale=6,
        lw=0.9, color="#c0392b", zorder=6))
    over.text(xd + w2 * 0.75 + 0.012, y_eng + h2 + 0.022, "drawing given to the agent",
              fontsize=4.8, color="#c0392b", ha="left", va="center",
              style="italic", bbox=dict(fc="white", ec="none", pad=0.4))

    # row labels (rotated, as on the whiteboard)
    fig.text(0.012, y_ai + h / 2, "AI", rotation=90, fontsize=7, fontweight="bold",
             color=AI_EDGE, ha="center", va="center")
    fig.text(0.012, y_eng + h2 / 2, "Engineers", rotation=90, fontsize=7,
             fontweight="bold", color=ENG_EDGE, ha="center", va="center")

    # Agent + model band, on the same date axis
    axb = fig.add_axes([AX_L, 0.02, AX_R - AX_L, 0.165])
    axb.set_xlim(X0, X1)
    axb.set_ylim(len(BAND) - 0.45, -0.55)
    for i, (tool, key, a, b, models) in enumerate(BAND):
        c = TOOL_COLOUR[key]
        span = D(b) - D(a)
        axb.barh(i, span, left=D(a), height=0.66, color=c,
                 alpha=0.92 if key != "people" else 0.6, zorder=3)
        label = f"{tool}: {models}"
        inside = span > 100 or (span > 60 and len(label) < 52)
        if inside:
            axb.text(D(a) + 1.5, i, label, va="center", ha="left", fontsize=4.8,
                     color="white", zorder=4)
        else:
            axb.text(D(b) + 1.5, i, label, va="center", ha="left", fontsize=4.8,
                     color=c if key != "people" else INK2, zorder=4)
    axb.set_yticks([])
    axb.xaxis.set_major_locator(mdates.MonthLocator())
    axb.xaxis.set_major_formatter(mdates.DateFormatter("%b"))
    axb.tick_params(axis="x", labelsize=5.2, colors=INK2, length=2, pad=1)
    axb.grid(axis="x", color=FAINT, lw=0.5, zorder=0)
    for sp in ("top", "right", "left"):
        axb.spines[sp].set_visible(False)
    axb.spines["bottom"].set_color(MUTED)
    fig.text(0.012, 0.02 + 0.165 / 2, "Agents and models", rotation=90,
             fontsize=6.0, fontweight="bold", color=INK, ha="center",
             va="center")
    fig.text(0.0, 0.995, "(a)", fontsize=7.5, fontweight="bold", va="top")

    FIGS.mkdir(exist_ok=True), PREVIEW.mkdir(exist_ok=True)
    fig.savefig(FIGS / "fig2a_timeline.pdf")
    fig.savefig(PREVIEW / "fig2a_timeline.png", dpi=220, facecolor="white")
    plt.close(fig)
    print("wrote fig2a_timeline")


# ----------------------------------------------------------------------------
# (b) the original AI part beside what replaced it
# ----------------------------------------------------------------------------
PAIRS = [
    ("Tap collar", [
        ("ai_tap_collar_v1.png", None, "AI, 15 May\nCopilot, Opus 4.7", AI_EDGE),
        ("ai_tap_collar_revised.png", None, "AI, after review\nCopilot, by 10 Jun", AI_EDGE),
        ("eng_tapcollar_rig_2026-09-11.jpg", None, "On the rig in the\ntests (photo, 11 Sep)", ENG_EDGE),
        ("eng_tapcollar_new_2026-10-08.jpg", None, "Team's new block\n(photo, 8 Oct)", ENG_EDGE),
    ], None),
    ("Auger", [
        ("ai_storage_auger_xsec.png", None, "AI, 16 Jun\nCopilot, Opus 4.8\n16:48 gears", AI_EDGE),
        ("eng_fusion_auger.png", None, "Team, 17 Jul\nFusion 360\n20:44 gears (tested)", ENG_EDGE),
    ], None),
    ("Bracket", [
        ("eng_bracket_drawing.png", None, "Team drawing,\n14 May", ENG_EDGE),
        ("ai_bracket.png", None, "AI model, 14 May\nCopilot, Opus 4.7", AI_EDGE),
    ], None),
]


def fig2b_pairs() -> None:
    fig = plt.figure(figsize=(W_IN, 1.75))
    weights = [len(items) + (1 if extra else 0) for _, items, extra in PAIRS]
    unit = 0.97 / sum(weights)
    starts = np.cumsum([0] + weights[:-1]) * unit
    for g, (name, items, extra) in enumerate(PAIRS):
        x0 = starts[g] + 0.02 + 0.012 * g
        k = len(items) + (1 if extra else 0)
        iw = unit - 0.004
        fig.text(x0 + (0.02 if g == 0 else 0), 0.97, name, fontsize=6.6, fontweight="bold", va="top")
        for j, (img, crop, label, edge) in enumerate(items):
            ax = fig.add_axes([x0 + j * iw + 0.005, 0.22, iw - 0.02, 0.62])
            ax.imshow(prep(img, crop), interpolation="lanczos")
            ax.set_aspect("equal"), ax.set_xticks([]), ax.set_yticks([])
            for s in ax.spines.values():
                s.set_edgecolor(edge), s.set_linewidth(0.8)
            fig.text(x0 + j * iw + iw / 2 - 0.005, 0.2, label, ha="center",
                     va="top", fontsize=4.9, color=INK, linespacing=1.15)
            if j:
                fig.text(x0 + j * iw - 0.003, 0.53, "→", fontsize=9,
                         ha="center", va="center", color=INK2)
        if extra:
            j = len(items)
            fig.text(x0 + j * iw - 0.003, 0.53, "→", fontsize=9, ha="center",
                     va="center", color=INK2)
            ax = fig.add_axes([x0 + j * iw + 0.005, 0.22, iw - 0.02, 0.62])
            ax.set_xticks([]), ax.set_yticks([])
            for s in ax.spines.values():
                s.set_edgecolor(ENG_EDGE), s.set_linestyle((0, (2, 2)))
            ax.text(0.5, 0.5, extra, ha="center", va="center", fontsize=4.9,
                    color=INK2, style="italic", transform=ax.transAxes)
    fig.text(0.0, 0.99, "(b)", fontsize=7.5, fontweight="bold", va="top")
    fig.savefig(FIGS / "fig2b_pairs.pdf")
    fig.savefig(PREVIEW / "fig2b_pairs.png", dpi=220, facecolor="white")
    plt.close(fig)
    print("wrote fig2b_pairs")


if __name__ == "__main__":
    fig2_timeline()
    fig2b_pairs()
