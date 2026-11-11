#!/usr/bin/env python3
"""Figs. 2 and 3 (v2): how the design moved between the AI agents and engineers.

Fig. 2 is laid out as drawn on the 27 Oct whiteboard (sources/brainstorm-
whiteboard-2026-10-27.png): (a) a timeline from April to November 2026 with the
key AI-modelled designs above the axis and the engineers' work (hand drawings,
conventional CAD, the built doser) below it, and (b) the agents and models on
the same date axis.  Fig. 3 (Fig. 2b until the 11 Nov review) puts original AI
parts beside what replaced them: (a) tap collar, (b) auger, (c) bracket.

Review of 11 Nov 2026 (paper/review_2026-11-11/NOTES.md): every panel is its
own PDF, assembled as LaTeX subfigures in figures.tex; labels are left-aligned,
with the model in a lighter colour than the agent; connectors run up, along and
up again into the middle of each frame; the whole-module render is the upright
isometric view.

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
    ("2026-05-13", "ai_whole_module_iso.png", None, "Whole module,\none request", "Copilot", "Opus 4.7"),
    ("2026-05-14", "ai_bracket.png", None, "Bracket from\nthe drawing", "Copilot", "Opus 4.7"),
    ("2026-05-15", "ai_tap_collar_v1.png", None, "First tap collar", "Copilot", "Opus 4.7"),
    ("2026-06-10", "ai_tap_collar_revised.png", None, "Tap collar,\nafter review", "Copilot", "Opus 4.7,\nFable 5"),
    ("2026-06-16", "ai_storage_auger_xsec.png", None, "Storage auger,\nscrew cap", "Copilot", "Opus 4.8"),
    ("2026-06-22", "ai_zoo_t2c_doser.png", (0.1, 0.18, 0.92, 0.82), "Whole doser,\n11 parts", "Zoo Text-to-CAD", "'kcl' model"),
    ("2026-10-01", "ai_onshape_assembly.png", None, "Team's parts,\nassembled", "Claude Code", "Opus 5.5,\nOnshape API"),
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


MODEL_GREY = "#8a8984"


def thumb(fig, rect, img, edge):
    """Image in a frame; returns the frame's final box (figure fraction)."""
    ax = fig.add_axes(rect)
    ax.imshow(img, interpolation="lanczos")
    ax.set_xticks([]), ax.set_yticks([])
    ax.set_aspect("equal")
    for sp in ax.spines.values():
        sp.set_edgecolor(edge)
        sp.set_linewidth(0.7)
    ax.apply_aspect()
    return ax.get_position()


def stack_label(fig, x, y, lines, above, fs=4.8):
    """Left-aligned label block at x; lines = [(text, colour, style)], drawn
    top to bottom.  Above a frame the block sits on y; below, it hangs from y."""
    h_in = fig.get_size_inches()[1]
    dy = 1.18 * fs / 72 / h_in
    n = sum(t.count("\n") + 1 for t, _, _ in lines)
    yy = y + (n * dy if above else 0)
    for text, colour, style in lines:
        k = text.count("\n") + 1
        fig.text(x, yy, text, ha="left", va="top", fontsize=fs, color=colour,
                 style=style, linespacing=1.12)
        yy -= k * dy


def slots(n, x0, x1, w):
    centres = np.linspace(x0 + w / 2, x1 - w / 2, n)
    return [c - w / 2 for c in centres]


def ax_x(date: float) -> float:
    return AX_L + (date - X0) / (X1 - X0) * (AX_R - AX_L)


def route(over, x_date, y_axis, x_frame, y_frame, level, colour, ls="-"):
    """Up (or down) from the date, along at `level`, then into the frame."""
    if abs(x_frame - x_date) < 0.004:
        xs, ys = [x_date, x_date], [y_axis, y_frame]
    else:
        xs = [x_date, x_date, x_frame, x_frame]
        ys = [y_axis, level, level, y_frame]
    over.plot(xs, ys, color=colour, lw=0.55, alpha=0.75, ls=ls,
              solid_joinstyle="miter", zorder=2)


def date_axis(ax, labels=True):
    ax.set_xlim(X0, X1)
    ax.xaxis.set_major_locator(mdates.MonthLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b 2026" if labels else "%b"))


def save_pdf(fig, stem):
    FIGS.mkdir(exist_ok=True)
    fig.savefig(FIGS / f"{stem}.pdf")
    plt.close(fig)
    print("wrote", stem)


def fig2_timeline() -> None:
    """(a): AI designs above the date axis, the engineers' work below."""
    H_IN = 4.45
    fig = plt.figure(figsize=(W_IN, H_IN))
    y_axis = 0.505
    ax_axis = fig.add_axes([AX_L, y_axis, AX_R - AX_L, 0.001])
    date_axis(ax_axis)
    ax_axis.set_yticks([])
    for sp in ("left", "right", "top"):
        ax_axis.spines[sp].set_visible(False)
    ax_axis.spines["bottom"].set_color(INK)
    ax_axis.spines["bottom"].set_linewidth(1.0)
    ax_axis.tick_params(axis="x", labelsize=5.8, colors=INK, length=3, pad=1.5)

    over = fig.add_axes([0, 0, 1, 1], zorder=-1)
    over.set_xlim(0, 1), over.set_ylim(0, 1), over.axis("off")
    for a, b, label in EVENTS:
        xa, xb = ax_x(D(a)), ax_x(D(b))
        over.add_patch(plt.Rectangle((xa, y_axis - 0.008), max(xb - xa, 0.005),
                                     0.016, color="#f1e6c8", zorder=0))
        over.text(xa, y_axis + 0.013, label, fontsize=4.9, color="#8a6300",
                  ha="left", va="bottom")

    # AI row, above the axis
    w, h, y_ai = 0.088, 0.235, 0.655
    xs = slots(len(AI_ITEMS), AX_L, AX_R, w)
    boxes = []
    for (date, name, crop, title, tool, model), x in zip(AI_ITEMS, xs):
        bb = thumb(fig, [x, y_ai, w, h], prep(name, crop), AI_EDGE)
        boxes.append(bb)
        stack_label(fig, bb.x0, y_ai + h + 0.008,
                    [(title, INK, "normal"), (tool, AI_EDGE, "normal"),
                     (model, MODEL_GREY, "italic")], above=True)
    lo, hi = y_axis + 0.045, y_ai - 0.018
    levels = np.linspace(hi, lo, len(AI_ITEMS))     # leftmost runs highest
    for (date, *_), bb, lv in zip(AI_ITEMS, boxes, levels):
        xd = ax_x(D(date))
        route(over, xd, y_axis + 0.004, (bb.x0 + bb.x1) / 2, bb.y0, lv, AI_EDGE)
        over.plot(xd, y_axis, "o", ms=2.3, color=AI_EDGE, zorder=5)

    # Engineer row, below the axis
    w2, h2, y_eng = 0.098, 0.235, 0.085
    n_eng = len(ENG_ITEMS) + 1                  # last slot: final photo
    xs = slots(n_eng, AX_L, AX_R, w2)
    eboxes = []
    for (date, name, crop, title, tool), x in zip(ENG_ITEMS, xs):
        bb = thumb(fig, [x, y_eng, w2, h2], prep(name, crop), ENG_EDGE)
        eboxes.append(bb)
        stack_label(fig, bb.x0, y_eng - 0.008,
                    [(title, INK, "normal"), (tool, MODEL_GREY, "italic")], above=False)
    xp = xs[-1]
    over.add_patch(plt.Rectangle((xp, y_eng), w2, h2, fill=False,
                                 ls=(0, (2, 2)), lw=0.7, edgecolor=ENG_EDGE))
    over.text(xp + w2 / 2, y_eng + h2 / 2, "Final doser\n(photo to\nbe taken)",
              ha="center", va="center", fontsize=4.9, color=INK2, style="italic")
    stack_label(fig, xp, y_eng - 0.008, [("Final version", INK, "normal"),
                                          ("photo", MODEL_GREY, "italic")], above=False)
    lo2, hi2 = y_eng + h2 + 0.018, y_axis - 0.045
    levels = np.linspace(lo2, hi2, n_eng)           # leftmost runs lowest
    for (date, *_), bb, lv in zip(ENG_ITEMS, eboxes, levels):
        xd = ax_x(D(date))
        route(over, xd, y_axis - 0.004, (bb.x0 + bb.x1) / 2, bb.y1, lv, ENG_EDGE)
        over.plot(xd, y_axis, "s", ms=2.1, color=ENG_EDGE, zorder=5)
    xd = ax_x(D("2026-11-05"))
    route(over, xd, y_axis - 0.004, xp + w2 / 2, y_eng + h2, levels[-1], ENG_EDGE,
          ls=(0, (2, 2)))

    # drawing -> AI model (Sam, 23:37): the bracket drawing went to the agent
    bd, ba = eboxes[2], boxes[3]
    over.add_patch(FancyArrowPatch(
        (bd.x0 + 0.75 * (bd.x1 - bd.x0), bd.y1), (ba.x0 + 0.3 * (ba.x1 - ba.x0), ba.y0),
        connectionstyle="arc3,rad=0.18", arrowstyle="-|>", mutation_scale=6,
        lw=0.9, color="#c0392b", zorder=6))
    over.text(bd.x1 + 0.008, bd.y1 + 0.032, "drawing given to the agent",
              fontsize=4.8, color="#c0392b", ha="left", va="center",
              style="italic", bbox=dict(fc="white", ec="none", pad=0.4), zorder=6)

    # row labels (rotated, as on the whiteboard)
    fig.text(0.012, y_ai + h / 2, "AI", rotation=90, fontsize=7, fontweight="bold",
             color=AI_EDGE, ha="center", va="center")
    fig.text(0.012, y_eng + h2 / 2, "Engineers", rotation=90, fontsize=7,
             fontweight="bold", color=ENG_EDGE, ha="center", va="center")
    save_pdf(fig, "timeline_a")


def fig2_band() -> None:
    """(b): agents and models on the same date axis as (a)."""
    fig = plt.figure(figsize=(W_IN, 1.05))
    axb = fig.add_axes([AX_L, 0.17, AX_R - AX_L, 0.80])
    date_axis(axb, labels=False)
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
    axb.tick_params(axis="x", labelsize=5.2, colors=INK2, length=2, pad=1)
    axb.grid(axis="x", color=FAINT, lw=0.5, zorder=0)
    for sp in ("top", "right", "left"):
        axb.spines[sp].set_visible(False)
    axb.spines["bottom"].set_color(MUTED)
    fig.text(0.024, 0.57, "Agents and\nmodels", rotation=90, fontsize=5.8,
             fontweight="bold", color=INK, ha="center", va="center",
             multialignment="center")
    save_pdf(fig, "timeline_b_band")


# ----------------------------------------------------------------------------
# Fig. 3 (was 2b): the original AI part beside what replaced it
# ----------------------------------------------------------------------------
PAIRS = {
    "redesign_a_tapcollar": [
        ("ai_tap_collar_v1.png", None, [("AI, 15 May", INK), ("Copilot", AI_EDGE), ("Opus 4.7", MODEL_GREY)], AI_EDGE),
        ("ai_tap_collar_revised.png", None, [("AI, after review", INK), ("Copilot, by 10 Jun", AI_EDGE), ("Opus 4.7, Fable 5", MODEL_GREY)], AI_EDGE),
        ("eng_tapcollar_rig_2026-09-11.jpg", None, [("On the rig in the tests", INK), ("photo, 11 Sep", MODEL_GREY)], ENG_EDGE),
        ("eng_tapcollar_new_2026-10-08.jpg", None, [("Team's new block", INK), ("photo, 8 Oct", MODEL_GREY)], ENG_EDGE),
    ],
    "redesign_b_auger": [
        ("ai_storage_auger_xsec.png", None, [("AI, 16 Jun", INK), ("Copilot", AI_EDGE), ("Opus 4.8; 16:48 gears", MODEL_GREY)], AI_EDGE),
        ("eng_fusion_auger.png", None, [("Team, 17 Jul", INK), ("Fusion 360", ENG_EDGE), ("20:44 gears; tested", MODEL_GREY)], ENG_EDGE),
    ],
    "redesign_c_bracket": [
        ("eng_bracket_drawing.png", None, [("Team drawing, 14 May", INK), ("hand drawing", MODEL_GREY)], ENG_EDGE),
        ("ai_bracket.png", None, [("AI model, 14 May", INK), ("Copilot", AI_EDGE), ("Opus 4.7", MODEL_GREY)], AI_EDGE),
    ],
}
PAIR_SIZE = {"redesign_a_tapcollar": (W_IN, 1.55),
             "redesign_b_auger": (2.35, 2.0),
             "redesign_c_bracket": (4.15, 2.0)}


def fig3_redesign() -> None:
    for stem, items in PAIRS.items():
        w_in, h_in = PAIR_SIZE[stem]
        fig = plt.figure(figsize=(w_in, h_in))
        n = len(items)
        gap = 0.20 / w_in                       # room for the arrow between frames
        iw = (1 - gap * (n - 1)) / n
        lab_h = 0.36 / h_in                     # label block under each frame
        for j, (img, crop, lines, edge) in enumerate(items):
            x = j * (iw + gap)
            bb = thumb(fig, [x + 0.004, lab_h, iw - 0.008, 1 - lab_h - 0.01],
                       prep(img, crop), edge)
            stack_label(fig, bb.x0, lab_h - 0.03,
                        [(t, c, "italic" if c == MODEL_GREY else "normal") for t, c in lines],
                        above=False, fs=5.2)
            if j:
                fig.text(x - gap / 2, lab_h + (1 - lab_h) / 2, "→", fontsize=10,
                         ha="center", va="center", color=INK2)
        save_pdf(fig, stem)


if __name__ == "__main__":
    fig2_timeline()
    fig2_band()
    fig3_redesign()
