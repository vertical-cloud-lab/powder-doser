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

Review of 17 Nov 2026 (paper/review_2026-11-17/NOTES.md, points 2.1-3.3): the
bracket drawing sits in the AI row beside the bracket made from it, with a short
red arrow that stays above the axis; the engineers' items are tagged in green
(who, then the tool); "First auger" shows the 24 Apr OpenSCAD design in section;
both Claude Code bars share a row in (b); Fig. 3 (a) ends with Ethan's solenoid
bracket, (b) starts with the first auger printed and tested, and (c) runs from
the drawing to today's flexible C-clip.

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
    "people": "#3b7d23",        # the engineers: same green as their tags in (a)
}
ENG_TAG = "#3b7d23"             # engineer tags (review of 17 Nov, point 2.2): a
                                # leaf green, distinct from Claude's teal
W_IN = 17.1 / 2.54

plt.rcParams.update({
    "font.size": 6.0, "font.family": "sans-serif", "axes.linewidth": 0.6,
    "savefig.dpi": 600,
})


def D(s: str) -> float:
    return mdates.date2num(dt.date.fromisoformat(s))


def prep(name: str, crop: tuple[float, float, float, float] | None = None) -> np.ndarray:
    """Load an asset, invert black-background wireframes, trim the margins."""
    im = Image.open(ASSETS / name)
    if im.mode in ("RGBA", "LA"):               # Onshape exports: transparent
        white = Image.new("RGBA", im.size, (255, 255, 255, 255))   # background
        im = Image.alpha_composite(white, im.convert("RGBA"))
    im = im.convert("RGB")
    if crop:                                    # fractional (l, t, r, b)
        w, h = im.size
        im = im.crop((int(crop[0] * w), int(crop[1] * h),
                      int(crop[2] * w), int(crop[3] * h)))
    a = np.asarray(im).astype(float) / 255
    is_photo = name.lower().endswith((".jpg", ".jpeg"))
    if a.mean() < 0.35 and not is_photo:        # wireframe on black; never invert a
        a = 1 - a                               # photo (17 Nov: a dark mat would trip it)
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
# Review of 17 Nov 2026 (paper/review_2026-11-17/NOTES.md):
#   2.1  the bracket drawing sits in the top row, directly beside the bracket the
#        agent modelled from it, so the red arrow between them never crosses the
#        axis;
#   2.2  the engineers' items carry a tag like the agents' (who, in green, then
#        the tool, in grey); photographs are tagged as photographs;
#   #74 item 4: "First auger" (24 Apr, Claude Code, Sonnet 4.6) now shows that
#        design: Devora's v2 OpenSCAD auger of 24 Apr, in section, rendered from
#        commit f3e8aa4 (it was Copilot's hollow tube of 15 May).
# (date on the axis, image, crop, title, who, tool, kind); kind "ai" = modelled by
# an AI agent (who = agent, tool = model); "eng" = the engineers' own work.
TOP_ITEMS = [
    ("2026-04-24", "ai_excavator.png", None, "Powder\nexcavator", "Copilot", "Opus 4.7", "ai"),
    ("2026-04-24", "ai_first_auger_v2_xsec_2026-04-24.png", None, "First auger", "Claude Code", "Sonnet 4.6", "ai"),
    ("2026-05-13", "ai_whole_module_iso.png", None, "Whole module,\none request", "Copilot", "Opus 4.7", "ai"),
    ("2026-05-14", "eng_bracket_drawing.png", None, "Drawing given\nto the agent", "Sam", "hand drawing", "eng"),
    ("2026-05-14", "ai_bracket_pr47_2026-05-14.png", None, "Bracket from\nthe drawing", "Copilot", "Opus 4.7", "ai"),
    ("2026-05-15", "ai_tap_collar_v1.png", None, "First tap collar", "Copilot", "Opus 4.7", "ai"),
    ("2026-06-10", "ai_tap_collar_revised.png", None, "Tap collar,\nafter review", "Copilot", "Opus 4.7,\nFable 5", "ai"),
    ("2026-06-16", "ai_storage_auger_xsec.png", None, "Storage auger,\nscrew cap", "Copilot", "Opus 4.8", "ai"),
    ("2026-06-22", "ai_zoo_t2c_doser.png", (0.1, 0.18, 0.92, 0.82), "Whole doser,\n11 parts", "Zoo Text-to-CAD", "'kcl' model", "ai"),
    ("2026-10-01", "ai_onshape_assembly.png", None, "Team's parts,\nassembled", "Claude Code", "Opus 5.5,\nOnshape API", "ai"),
]
DRAWING, FROM_DRAWING = 3, 4            # indices in TOP_ITEMS: the red arrow
# (date, image, crop, title, who, tool); who None for a photograph
ENG_ITEMS = [
    ("2026-04-22", "eng_hackathon_sketch.jpg", None, "Hackathon sketch", "Sterling", "hand drawing"),
    ("2026-04-24", "eng_pose_tube.png", (0.0, 0.0, 0.5, 0.42), "First auger,\nprinted and tested", None, "photo"),
    ("2026-07-17", "eng_fusion_auger.png", None, "Auger, cap,\n44-tooth gear", "Sam", "Fusion 360"),
    ("2026-07-24", "eng_glovebox_first_dose.jpg", (0.05, 0.0, 0.95, 1.0), "First dose in\na glove box", "Sam, at U of U", "photo"),
    ("2026-08-19", "eng_multidoser_sketch.png", None, "Multi-doser\ncarriage", "Sam", "hand drawing"),
    ("2026-08-19", "eng_multidoser_onshape.png", None, "Multi-doser\ncarriages", "Sam", "Onshape"),
    ("2026-09-11", "eng_rig_2026-09-11.jpg", None, "Doser as tested", None, "photo, 11 Sep"),
]
# Agent + model band: (row, tool, colour key, start, end, models).  Review of
# 17 Nov, point 2.3: both Claude Code bars share a row, each with its own label.
BAND = [
    (0, "GitHub Copilot coding agent", "copilot", "2026-04-23", "2026-06-30",
     "Claude Opus 4.7 → Opus 4.8"),
    (1, "Claude Code, local", "claude", "2026-04-23", "2026-04-25", "Claude Sonnet 4.6"),
    (1, "Claude Code, GitHub Actions", "claude", "2026-06-30", "2026-11-10",
     "Opus 4.8, Fable 5, Opus 5, Opus 5.5: rig, data, Onshape assembly (Oct)"),
    (2, "CADSmith, run by the agent", "cadsmith", "2026-05-12", "2026-06-22",
     "Claude Sonnet 4.5 / Opus 4.5"),
    (3, "Zoo Text-to-CAD API", "zoo", "2026-05-12", "2026-06-30", "'kcl' model"),
    (4, "Zoo Design Studio", "zoo", "2026-05-18", "2026-07-17", "Zookeeper agent"),
    (5, "Engineers, conventional CAD", "people", "2026-07-02", "2026-11-10",
     "Fusion 360 from 2 Jul (#120); Onshape from Aug"),
]
EVENTS = [("2026-04-22", "2026-04-24", "Hackathon"),
          ("2026-08-04", "2026-09-15", "Tests: 13 powders")]

X0, X1 = D("2026-04-12"), D("2026-11-15")
AX_L, AX_R = 0.05, 0.985


MODEL_GREY = "#8a8984"


def thumb(fig, rect, img, edge, anchor="C"):
    """Image in a frame; returns the frame's final box (figure fraction).
    `anchor` pins the shrunk frame inside its slot: "N" under a label above it,
    "S" over a label below it."""
    ax = fig.add_axes(rect)
    ax.imshow(img, interpolation="lanczos")
    ax.set_xticks([]), ax.set_yticks([])
    ax.set_aspect("equal")
    ax.set_anchor(anchor)
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


def slots(n, x0, x1, w, wide_after=None, extra=0.0):
    """Left edges of n frames of width w spread over [x0, x1]; the gap after
    frame `wide_after` is `extra` wider than the others."""
    gap = (x1 - x0 - n * w - (extra if wide_after is not None else 0)) / (n - 1)
    xs, x = [], x0
    for i in range(n):
        xs.append(x)
        x += w + gap + (extra if i == wide_after else 0)
    return xs


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


def item_label(who, tool, kind):
    """Tag lines under the title: the agent (purple) and model (grey) for an AI
    design; the engineer (green) and tool (grey) for the team's own work; just
    the grey "photo" line for a photograph (review of 17 Nov, point 2.2)."""
    lines = []
    if who:
        lines.append((who, AI_EDGE if kind == "ai" else ENG_TAG, "normal"))
    lines.append((tool, MODEL_GREY, "italic"))
    return lines


def fig2_timeline() -> None:
    """(a): AI designs above the date axis, the engineers' work below; the
    drawing the agent was given sits above, beside the bracket made from it."""
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

    # top row: AI designs, and the drawing given to the agent (grey frame)
    w, h, y_ai = 0.0815, 0.235, 0.655
    xs = slots(len(TOP_ITEMS), AX_L, AX_R, w, wide_after=DRAWING, extra=0.012)
    boxes = []
    for (date, name, crop, title, who, tool, kind), x in zip(TOP_ITEMS, xs):
        edge = AI_EDGE if kind == "ai" else ENG_EDGE
        bb = thumb(fig, [x, y_ai, w, h], prep(name, crop), edge, anchor="N")
        boxes.append(bb)
        stack_label(fig, bb.x0 if (bb.x1 - bb.x0) > 0.5 * w else x,
                    y_ai + h + 0.008,
                    [(title, INK, "normal")] + item_label(who, tool, kind), above=True)
    lo, hi = y_axis + 0.045, y_ai - 0.018
    levels = np.linspace(hi, lo, len(TOP_ITEMS))    # leftmost runs highest
    for (date, *_, kind), bb, lv in zip(TOP_ITEMS, boxes, levels):
        xd = ax_x(D(date))
        c = AI_EDGE if kind == "ai" else ENG_EDGE
        route(over, xd, y_axis + 0.004, (bb.x0 + bb.x1) / 2, bb.y0, lv, c)
        over.plot(xd, y_axis, "o" if kind == "ai" else "s",
                  ms=2.3 if kind == "ai" else 2.1, color=c, zorder=5)

    # drawing -> the agent's bracket (Sam, 23:37; review of 17 Nov, 2.1): a short
    # arrow between the two frames, above the axis
    bd, ba = boxes[DRAWING], boxes[FROM_DRAWING]
    ya = (max(bd.y0, ba.y0) + min(bd.y1, ba.y1)) / 2
    over.add_patch(FancyArrowPatch((bd.x1 + 0.002, ya), (ba.x0 - 0.002, ya),
                                   arrowstyle="-|>", mutation_scale=6, lw=0.9,
                                   color="#c0392b", zorder=6, shrinkA=0, shrinkB=0))

    # bottom row: the engineers' work
    w2, h2, y_eng = 0.104, 0.235, 0.085
    n_eng = len(ENG_ITEMS) + 1                  # last slot: final photo
    xs = slots(n_eng, AX_L, AX_R, w2)
    eboxes = []
    for (date, name, crop, title, who, tool), x in zip(ENG_ITEMS, xs):
        bb = thumb(fig, [x, y_eng, w2, h2], prep(name, crop), ENG_EDGE, anchor="S")
        eboxes.append(bb)
        # narrow frames: start the label at the slot edge so it clears the next one
        xl = bb.x0 if (bb.x1 - bb.x0) > 0.5 * w2 else x + 0.004
        stack_label(fig, xl, y_eng - 0.008,
                    [(title, INK, "normal")] + item_label(who, tool, "eng"), above=False)
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

    # row labels (rotated, as on the whiteboard)
    fig.text(0.012, y_ai + h / 2, "AI", rotation=90, fontsize=7, fontweight="bold",
             color=AI_EDGE, ha="center", va="center")
    fig.text(0.012, y_eng + h2 / 2, "Engineers", rotation=90, fontsize=7,
             fontweight="bold", color=ENG_TAG, ha="center", va="center")
    save_pdf(fig, "timeline_a")


def fig2_band() -> None:
    """(b): agents and models on the same date axis as (a)."""
    n_rows = max(r for r, *_ in BAND) + 1
    fig = plt.figure(figsize=(W_IN, 0.92))
    axb = fig.add_axes([AX_L, 0.19, AX_R - AX_L, 0.78])
    date_axis(axb, labels=False)
    axb.set_ylim(n_rows - 0.45, -0.55)
    for i, tool, key, a, b, models in BAND:
        c = TOOL_COLOUR[key]
        span = D(b) - D(a)
        axb.barh(i, span, left=D(a), height=0.66, color=c,
                 alpha=0.92 if key != "people" else 0.85, zorder=3)
        label = f"{tool}: {models}"
        inside = span > 100 or (span > 60 and len(label) < 52)
        if inside:
            axb.text(D(a) + 1.5, i, label, va="center", ha="left", fontsize=4.8,
                     color="white", zorder=4)
        else:
            axb.text(D(b) + 1.5, i, label, va="center", ha="left", fontsize=4.8,
                     color=c, zorder=4)
    axb.set_yticks([])
    axb.tick_params(axis="x", labelsize=5.2, colors=INK2, length=2, pad=1)
    axb.grid(axis="x", color=FAINT, lw=0.5, zorder=0)
    for sp in ("top", "right", "left"):
        axb.spines[sp].set_visible(False)
    axb.spines["bottom"].set_color(MUTED)
    fig.text(0.024, 0.58, "Agents and\nmodels", rotation=90, fontsize=5.8,
             fontweight="bold", color=INK, ha="center", va="center",
             multialignment="center")
    save_pdf(fig, "timeline_b_band")


# ----------------------------------------------------------------------------
# Fig. 3 (was 2b): the original AI part beside what replaced it
# ----------------------------------------------------------------------------
# Each item: (image, fractional crop, label lines [(text, colour)], frame colour).
# Label colours: INK title; AI_EDGE agent; ENG_TAG engineer; MODEL_GREY (italic)
# model, tool or note.  Review of 17 Nov 2026: (a) ends with Ethan's solenoid
# bracket (#203), not the 8 Oct electronics block (point 3.1); (b) starts with
# the first auger (point 3.2); (c) continues past the agent's model to the
# brackets the team made after it, ending with today's flexible C-clip (3.3).
PAIRS = {
    "redesign_a_tapcollar": [
        ("ai_tap_collar_v1.png", None, [("AI, 15 May", INK), ("Copilot", AI_EDGE), ("Opus 4.7", MODEL_GREY)], AI_EDGE),
        ("ai_tap_collar_revised.png", None, [("AI, after review", INK), ("Copilot, by 10 Jun", AI_EDGE), ("Opus 4.7, Fable 5", MODEL_GREY)], AI_EDGE),
        ("eng_tapcollar_rig_2026-09-11.jpg", None, [("On the rig in the tests", INK), ("Team, Fusion 360", ENG_TAG), ("photo, 11 Sep", MODEL_GREY)], ENG_EDGE),
        # Sam's photo of 17 Nov; the crop keeps the bracket and solenoid
        ("../photos/solenoid_bracket_2026-11-17.jpg", (0.195, 0.165, 0.745, 0.705),
         [("Solenoid bracket", INK), ("Ethan, Onshape", ENG_TAG), ("photo, 17 Nov", MODEL_GREY)], ENG_EDGE),
    ],
    "redesign_b_auger": [
        # the version printed and run with NaCl on 14 May (#16); the storage auger
        # stays in the middle because the Fusion 360 auger recreates it
        ("ai_first_auger_xsec_2026-05-13.png", None, [("AI, 13 May", INK), ("Copilot", AI_EDGE), ("Opus 4.7", MODEL_GREY), ("tested 14 May", MODEL_GREY)], AI_EDGE),
        ("ai_storage_auger_xsec.png", None, [("AI, 16 Jun", INK), ("Copilot", AI_EDGE), ("Opus 4.8", MODEL_GREY), ("16:48 gears", MODEL_GREY)], AI_EDGE),
        ("eng_fusion_auger.png", None, [("Team, 17 Jul", INK), ("Sam, Fusion 360", ENG_TAG), ("20:44 gears", MODEL_GREY), ("in every test", MODEL_GREY)], ENG_EDGE),
    ],
    "redesign_c_bracket": [
        ("eng_bracket_drawing.png", None, [("Drawing, 14 May", INK), ("Sam", ENG_TAG), ("hand drawing", MODEL_GREY)], ENG_EDGE),
        ("ai_bracket_pr47_2026-05-14.png", None, [("AI model, 14 May", INK), ("Copilot", AI_EDGE), ("Opus 4.7", MODEL_GREY)], AI_EDGE),
        # Sam's #120 recreation, the bolted split clamp (Fusion "Auger Bracket
        # Recorded" v1; render from PR #170's reference sheet)
        ("eng_bracket_split_clamp_fusion.png", None, [("Split clamp, Jul", INK), ("Sam", ENG_TAG), ("Fusion 360", MODEL_GREY)], ENG_EDGE),
        # the open C-clip on the rig behind the 44-tooth gear from Aug, through
        # the tests (PR #170 README; Sam on #117, 31 Jul)
        ("eng_flexible_bracket_original.png", None, [("Flexible C-clip, Aug", INK), ("Sam", ENG_TAG), ("Fusion 360; in the tests", MODEL_GREY)], ENG_EDGE),
        # Ethan's Onshape version, the bracket #193 links (29 Oct)
        ("eng_flexible_bracket_current.png", None, [("C-clip now, Oct", INK), ("Ethan", ENG_TAG), ("Onshape", MODEL_GREY)], ENG_EDGE),
    ],
}
# Print sizes (inches).  (a) full width; (b) and (c) share the row below.
PAIR_SIZE = {"redesign_a_tapcollar": (W_IN, 1.62),
             "redesign_b_auger": (2.2, 2.05),
             "redesign_c_bracket": (4.45, 2.05)}


def fig3_redesign() -> None:
    for stem, items in PAIRS.items():
        w_in, h_in = PAIR_SIZE[stem]
        fig = plt.figure(figsize=(w_in, h_in))
        n = len(items)
        gap = 0.20 / w_in                       # room for the arrow between frames
        iw = (1 - gap * (n - 1)) / n
        n_lines = max(sum(t.count("\n") + 1 for t, _ in lines) for *_, lines, _ in items)
        lab_h = (n_lines * 1.18 * 5.2 / 72 + 0.07) / h_in   # label block under each frame
        for j, (img, crop, lines, edge) in enumerate(items):
            x = j * (iw + gap)
            bb = thumb(fig, [x + 0.004, lab_h, iw - 0.008, 1 - lab_h - 0.01],
                       prep(img, crop), edge, anchor="S")
            stack_label(fig, bb.x0 if (bb.x1 - bb.x0) > 0.6 * iw else x + 0.004,
                        lab_h - 0.03,
                        [(t, c, "italic" if c == MODEL_GREY else "normal") for t, c in lines],
                        above=False, fs=5.2)
            if j:
                fig.text(x - gap / 2, lab_h + 0.42 * (1 - lab_h), "→", fontsize=10,
                         ha="center", va="center", color=INK2)
        save_pdf(fig, stem)


if __name__ == "__main__":
    fig2_timeline()
    fig2_band()
    fig3_redesign()
