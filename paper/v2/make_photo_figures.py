#!/usr/bin/env python3
"""Figs. 1, 4 and 5 (v2): the doser, how a dose runs, and how it is used.

Review of 11 Nov 2026 (paper/review_2026-11-11/NOTES.md): Figs. 1 and 5 are
written as one PDF per panel, without panel letters, and assembled as LaTeX
subfigures in figures.tex; Fig. 4 (how a dose runs) stays one image.

From the 27 Oct whiteboard (sources/brainstorm-whiteboard-2026-10-27.png):

    Fig. 1  schematic + real doser image with callouts; assembled + exploded;
            callout to the auger section view; powder in the beaker (23:09).
    Fig. 3  dosing stages as keyframes, beside the feedback schematic and the
            Claude ping that starts a dose ("dose 8 g").
    Fig. 4  loading powder, fitting and swapping augers, with the augers
            lined up and a callout of what is inside each one.

Photographs and video frames are in assets/photos/ (SOURCES.json: comment URL,
author, date).  CAD renders come from PR #170 and paper/figures/assets/.  The
dose trace is read from the raw serial log in git by
paper/figures/data/build_dose_traces.py.  Per-powder numbers come from the
same loaders as the results figures.

Usage:  python3 make_photo_figures.py
"""

from __future__ import annotations

import json
import sys
import textwrap
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import ConnectionPatch, FancyArrowPatch, FancyBboxPatch, Rectangle
from PIL import Image, ImageOps

HERE = Path(__file__).resolve().parent
PHOTOS = HERE / "assets" / "photos"
OLD = HERE.parent / "figures"
FIGS, PREVIEW = HERE / "figures", HERE / "preview"
sys.path.insert(0, str(OLD))
sys.path.insert(0, str(OLD / "data"))

import make_figures as mf  # noqa: E402  (auger cut-away with its anchors)
import make_data_figures as m  # noqa: E402

INK, INK2, MUTED = "#0b0b0b", "#52514e", "#b8b6ae"
W_IN = 17.1 / 2.54
CALL = "#c0392b"          # callout colour
PHASE = {"bulk": "#cfcabd", "fine": "#e2ddd0", "tap": "#efece4"}
plt.rcParams.update({"font.size": 6.0, "font.family": "sans-serif",
                     "savefig.dpi": 600})


def photo(name: str, box: tuple[int, int, int, int] | None = None,
          rotate: float = 0.0) -> np.ndarray:
    im = ImageOps.exif_transpose(Image.open(PHOTOS / name)).convert("RGB")
    if rotate:
        im = im.rotate(rotate, expand=True, resample=Image.BICUBIC,
                       fillcolor=(255, 255, 255))
    if box:
        im = im.crop(box)
    return np.asarray(im)


def bare(ax):
    ax.set_xticks([]), ax.set_yticks([])
    for s in ax.spines.values():
        s.set_visible(False)


def label(ax, letter, x=0.0, y=1.0, color=INK, inside=False):
    ax.text(x, y, f"({letter})", transform=ax.transAxes, fontsize=7.5,
            fontweight="bold", ha="left", va="top" if inside else "bottom",
            color=color, zorder=20,
            bbox=dict(fc="white", ec="none", alpha=0.75, pad=0.8) if inside else None)


def save(fig, stem):
    """PDF at print size; figures.tex places it at its natural size."""
    fig.savefig(FIGS / f"{stem}.pdf")
    plt.close(fig)
    print("wrote", stem)


def image_panel(w_in: float, h_in: float):
    fig = plt.figure(figsize=(w_in, h_in))
    ax = fig.add_axes([0, 0, 1, 1])
    bare(ax)
    return fig, ax


# ----------------------------------------------------------------------------
# Fig. 1  the doser
# ----------------------------------------------------------------------------
# Panel sizes (inches, print size) for the LaTeX layout in figures.tex:
# (a) on the left; (b) above (c) and (d) on the right.
DOSER_A_W = 3.45
DOSER_R_W = W_IN - DOSER_A_W - 0.10
DOSER_LOW_H = 1.95


def fig_doser_panels() -> None:
    """Fig. 1 as four subfigures (review of 11 Nov 2026: LaTeX subfigures;
    (d) replaced by the fixed livestream camera's view of the cup)."""
    # (a) photograph with callouts; asset is 1500 x 2000 (3024 x 4032 / 2.016)
    k = 1500 / 3024
    img = photo("rig_2026-09-11.jpg")
    x0, x1, y0, y1 = 120 * k, 2950 * k, 230 * k, 4032 * k
    fig, ax = image_panel(DOSER_A_W, DOSER_A_W * (y1 - y0) / (x1 - x0))
    ax.imshow(img)
    ax.set_xlim(x0, x1), ax.set_ylim(y1, y0)
    callouts = [
        ("Screw-on cap over\nthe fill opening", (885, 545), (180, 470), "left"),
        ("Stepper motor", (760, 690), (180, 820), "left"),
        ("20:44 gear pair\n(auger drive)", (1120, 690), (180, 1110), "left"),
        ("Tilt servo (one of two)\nand 2:1 tilt gears", (640, 1440), (180, 1880), "left"),
        ("Tap collar with\n12 V solenoid", (1480, 430), (2900, 330), "right"),
        ("Electronics", (1830, 820), (2900, 700), "right"),
        # review of 17 Nov, point 1.1: no dashed box; the callout points to (c)
        ("Auger tube: the powder\nreservoir, filled from\nthe capped end\n(section view in (c))",
         (1300, 930), (2900, 1200), "right"),
        ("Outlet, Ø 3 mm", (1470, 1085), (2900, 1650), "right"),
        ("Hinged mounting\nplate", (1350, 1390), (2900, 2050), "right"),
        ("Collection beaker", (1480, 2330), (2900, 2700), "right"),
        ("Analytical balance,\n0.1 mg readability", (1250, 3550), (2900, 3450), "right"),
    ]
    for text, (px, py), (tx, ty), side in callouts:
        ax.annotate(text, xy=(px * k, py * k), xytext=(tx * k, ty * k),
                    fontsize=5.6, color=INK, ha="left" if side == "left" else "right",
                    va="center", linespacing=1.1, multialignment="left",
                    bbox=dict(fc="white", ec="none", alpha=0.85, pad=1.2),
                    arrowprops=dict(arrowstyle="-", lw=0.6, color=CALL,
                                    shrinkA=0, shrinkB=1.5), zorder=5)
        ax.plot(px * k, py * k, "o", ms=2.2, color=CALL, zorder=6)
    save(fig, "doser_a_photo")

    # (b) exploded view: review of 17 Nov, point 1.2.  PR #170's exploded start
    # re-rendered without balloons (render_exploded_view.py), with balloons for
    # the 13 main parts only, each beside its part (make_exploded_view.py).  The
    # print size is that of the PR #170 crop it replaces (870 x 680 px).
    import make_exploded_view as mev
    mev.main_panel(DOSER_R_W, DOSER_R_W * 680 / 870)

    # (c) auger section, larger than in the composite
    fig = plt.figure(figsize=(1.52, DOSER_LOW_H))
    axc = fig.add_axes([0.0, 0.0, 1.0, 1.0])
    mf.auger_cutaway(axc)
    save(fig, "doser_c_auger")

    # (d) the fixed livestream camera, after a 0.5 g NaCl dose (15 Sep 2026)
    cam = photo("salt_demo_after_2026-09-15.jpg")         # 720 x 1280
    cam = cam[640:1150, 170:600]
    fig, ax = image_panel(DOSER_LOW_H * cam.shape[1] / cam.shape[0], DOSER_LOW_H)
    ax.imshow(cam, interpolation="lanczos")
    ax.annotate("0.496 g of NaCl", xy=(215, 250), xytext=(215, 470),
                fontsize=5.6, color=INK, ha="center", va="center",
                bbox=dict(fc="white", ec="none", alpha=0.85, pad=1.2),
                arrowprops=dict(arrowstyle="-", lw=0.6, color=CALL, shrinkA=0,
                                shrinkB=1.5), zorder=5)
    ax.plot(215, 250, "o", ms=2.2, color=CALL, zorder=6)
    save(fig, "doser_d_cam")


# ----------------------------------------------------------------------------
# ----------------------------------------------------------------------------
# Fig. 4 (was 3)  how a dose runs
# ----------------------------------------------------------------------------
REQUEST = ("@claude dispense 8 grams of the AlSi10Mg that we just loaded. You can use the "
           "most recent optimized parameters. It flows pretty well, maybe not quite as good "
           "as salt, but still pretty decent.")
REPLY = ("Dispensed 8 g of AlSi10Mg: 7.993 g delivered in 315 s. 7.9928 g against an "
         "8.000 g target, 7.2 mg short (−0.09 %). The firmware reported ok.")


def inch_axes(fig, rect):
    """Bare axes whose data coordinates are inches from its lower-left corner,
    so boxes, padding and rounded corners keep their shape at any size."""
    ax = fig.add_axes(rect)
    bare(ax)
    w_in, h_in = fig.get_size_inches()
    ax.set_xlim(0, rect[2] * w_in), ax.set_ylim(0, rect[3] * h_in)
    return ax, rect[2] * w_in, rect[3] * h_in


PT = 1 / 72                     # one point, in inches


def card(ax, x, top, w, who, when, text, colour, wrap):
    """A comment card (inch axes) hanging from `top`, text wrapped at `wrap`
    characters; returns the card's bottom edge.  Review of 17 Nov, point 4.1:
    short, wide cards with long lines."""
    body = textwrap.fill(text, wrap)
    n = body.count("\n") + 1
    h = (3.0 + 6.4 + 2.0 + n * 6.6 + 2.0) * PT
    y = top - h
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.0,rounding_size=0.04",
                                fc="white", ec=colour, lw=0.8))
    ax.text(x + 0.06, top - 3.0 * PT, who, fontsize=5.6, fontweight="bold",
            color=colour, va="top")
    ax.text(x + w - 0.06, top - 3.0 * PT, when, fontsize=5.0, color=INK2, va="top",
            ha="right")
    ax.text(x + 0.06, top - (3.0 + 6.4 + 2.0) * PT, body, fontsize=5.2, color=INK,
            va="top", linespacing=1.27)
    return y


def box(ax, x0, yc, w, h, text, fc="#eef1f7", ec="#7a8296"):
    """A block of the control loop (inch axes): left edge x0, centre height yc."""
    ax.add_patch(FancyBboxPatch((x0, yc - h / 2), w, h,
                                boxstyle="round,pad=0.0,rounding_size=0.05",
                                fc=fc, ec=ec, lw=0.7))
    ax.text(x0 + w / 2, yc, text, ha="center", va="center", fontsize=5.3,
            linespacing=1.15)


def arrow(ax, a, b):
    ax.add_patch(FancyArrowPatch(a, b, arrowstyle="-|>", mutation_scale=6, lw=0.8,
                                 color=INK2, shrinkA=0, shrinkB=0))


def brace(fig, x0, x1, y0, rx, ry, colour=INK2, lw=0.7):
    """A horizontal curly brace from x0 to x1 (figure fraction) with its feet
    on y0 and its tip pointing up; rx, ry: the curl radius in figure fraction.
    Returns the tip.  Review of 17 Nov, point 4.3: a brace spans a phase, where
    a leader line read as one moment."""
    from matplotlib.path import Path
    from matplotlib.patches import PathPatch
    xm = (x0 + x1) / 2
    rx = min(rx, (x1 - x0) / 4)
    C = Path.CURVE3
    verts = [(x0, y0), (x0, y0 + ry), (x0 + rx, y0 + ry), (xm - rx, y0 + ry),
             (xm, y0 + ry), (xm, y0 + 2 * ry), (xm, y0 + ry), (xm + rx, y0 + ry),
             (x1 - rx, y0 + ry), (x1, y0 + ry), (x1, y0)]
    codes = [Path.MOVETO, C, C, Path.LINETO, C, C, C, C, Path.LINETO, C, C]
    fig.add_artist(PathPatch(Path(verts, codes), fill=False, ec=colour, lw=lw,
                             transform=fig.transFigure, capstyle="round",
                             joinstyle="round"))
    return xm, y0 + 2 * ry


def nacl_trace():
    """The 12 Aug 1 g NaCl dose (protocol G, dose 0): all three phases ran."""
    import build_dose_traces as bt
    import pandas as pd
    doses = pd.read_csv(OLD / "data" / "doses_all.csv")
    keyed, _ = bt.load_all(str(HERE.parent.parent), bt.DEFAULT_REF, doses)
    return keyed[("20260812T215154Z_salt", "G", 0)]


PHASE_TEXT = {
    "bulk": "Bulk: 45° tilt, 55 rpm,\nto 0.5 g short",
    "fine": "Fine: 22.5° tilt, 45° steps,\nto 50 mg short",
    "tap": "Tap: horizontal, 2 taps\nper cycle, to ±5 mg",
}


DOSING_H = 4.75                 # inches


def fig_dosing() -> None:
    """Fig. 4 (was 3): request and reply, the control loop, one dose by phase.

    Review of 11 Nov 2026: the phone-screen snippet is gone, the loop is drawn
    as one row with a single loop back, and the keyframe leaders are lines.
    Review of 17 Nov 2026 (points 4.1-4.3): short, wide cards in (a), giving
    the height to (c); "powder" clear of the blocks and the loop back drawn as
    one path in (b); braces over the phases, and "Before" moved to the left
    edge, in (c).  Kept as one image (not subfigures): the braces' leaders
    cross between panels."""
    from matplotlib.path import Path
    import build_dose_traces as bt
    H = DOSING_H
    fig = plt.figure(figsize=(W_IN, H))
    top_y, top_h = 0.776, 0.196                 # the row of (a) and (b)

    # (a) the request and the reply (PR #166, 29 Sep 2026): short, wide cards
    ax, wa, ha = inch_axes(fig, [0.0, top_y, 0.452, top_h])
    y = card(ax, 0.02, ha - 0.01, wa - 0.04, "sgbaird", "29 Sep 2026, 22:36 UTC",
             REQUEST, "#4a3aa7", wrap=78)
    y2 = y - 0.075
    arrow(ax, (wa / 2, y - 0.008), (wa / 2, y2 + 0.01))
    card(ax, 0.02, y2, wa - 0.04, "claude[bot]", "22:37 UTC", REPLY, "#1baf7a", wrap=78)
    label(ax, "a", x=0.0, y=1.0)

    # (b) the control loop, left to right, with the measurement looping back
    axb, wb, hb = inch_axes(fig, [0.468, top_y, 0.532, top_h])
    texts = ["Dose request\n(target mass)", "Three-phase\ncontroller\n(microcontroller)",
             "Auger rotation,\nsolenoid taps,\ntilt servos", "Analytical\nbalance"]
    widths = [0.66, 0.80, 0.72, 0.56]           # inches
    gaps = [0.19, 0.19, 0.38]                   # the last one carries "powder"
    bh, yb = 0.40, hb - 0.29
    x0s = [0.04]
    for w_, g_ in zip(widths[:-1], gaps):
        x0s.append(x0s[-1] + w_ + g_)
    for x0_, w_, t_ in zip(x0s, widths, texts):
        box(axb, x0_, yb, w_, bh, t_)
    for i in range(3):
        arrow(axb, (x0s[i] + widths[i] + 0.012, yb), (x0s[i + 1] - 0.012, yb))
    xg = x0s[2] + widths[2] + gaps[2] / 2       # "powder", above its arrow, in the gap
    axb.text(xg, yb + 0.035, "powder", fontsize=4.9, color=INK2, ha="center",
             va="bottom", style="italic")
    # the measurement loops back as one path with one arrowhead (point 4.2)
    xc2, xc4 = x0s[1] + widths[1] / 2, x0s[3] + widths[3] / 2
    yl = yb - bh / 2 - 0.17
    loop = Path([(xc4, yb - bh / 2 - 0.01), (xc4, yl), (xc2, yl), (xc2, yb - bh / 2 - 0.012)],
                [Path.MOVETO, Path.LINETO, Path.LINETO, Path.LINETO])
    axb.add_patch(FancyArrowPatch(path=loop, arrowstyle="-|>", mutation_scale=6, lw=0.8,
                                  color=INK2, joinstyle="miter", capstyle="butt"))
    axb.text((xc2 + xc4) / 2, yl - 0.04, "measured mass, read after every step",
             fontsize=4.9, color=INK2, ha="center", va="top", style="italic")
    axb.text(x0s[0] + widths[0] / 2, yb - bh / 2 - 0.04, "from an agent\nor a person",
             ha="center", va="top", fontsize=4.9, color=INK2, style="italic",
             linespacing=1.1)
    label(axb, "b", x=0.0, y=1.0)

    # (c) one dose, phase by phase: the trace, with braces up to the keyframes
    dose = nacl_trace()
    axt = fig.add_axes([0.075, 0.075, 0.905, 0.34])
    tt, mm = bt.trace_xy(dose)
    prev, spans = 0.0, {}
    for ph_ in dose["order"]:
        end_ = dose["phases"][ph_]["end_s"]
        axt.axvspan(prev, end_, color=PHASE[ph_], lw=0, zorder=0)
        spans[ph_] = (prev, end_)
        prev = end_
    axt.axhspan(950, 1050, color="#e6f4e6", zorder=1)
    axt.axhline(1000, color=INK2, lw=0.6, ls="--", zorder=2)
    axt.step(tt, mm, where="post", color=m.SURROGATE, lw=1.1, zorder=3)
    axt.plot(tt[-1], mm[-1], "o", ms=3.5, color=m.SURROGATE, zorder=4)
    axt.text(tt[-1] - 2, mm[-1] - 120, f"{mm[-1]:.0f} mg", ha="right", fontsize=5.4,
             color=INK)
    axt.set_xlim(0, tt[-1] + 4)
    axt.set_ylim(-30, 1120)
    axt.set_xlabel("Time since the dose started (s)", labelpad=1)
    axt.set_ylabel("Mass in the cup (mg)")
    for sp in ("top", "right"):
        axt.spines[sp].set_visible(False)
    fig.text(0.0, 0.739, "(c)", fontsize=7.5, fontweight="bold", ha="left", va="bottom",
             color=INK)

    # keyframes above the trace: before (at the left edge), the tube in each
    # phase, after (at the right edge); each phase image sits over a brace that
    # spans that phase on the time axis
    frames = [
        ("salt_demo_before_2026-09-15.jpg", "photo", "Before: empty cup", None),
        ("cad_tilt45.png", "cad", PHASE_TEXT["bulk"], "bulk"),
        ("cad_tilt22p5.png", "cad", PHASE_TEXT["fine"], "fine"),
        ("cad_tilt00.png", "cad", PHASE_TEXT["tap"], "tap"),
        ("salt_demo_after_2026-09-15.jpg", "photo", "After: the dose in the cup", None),
    ]
    fy, fh = 0.486, 0.215                       # keyframe row (figure fraction)
    imgs = []
    for name, kind, _, _ in frames:
        img = photo(name)
        Hh, Ww = img.shape[:2]
        if kind == "photo":
            img = img[int(0.30 * Hh):int(0.78 * Hh), int(0.05 * Ww):int(0.95 * Ww)]
        else:
            # one crop for all three tilts (the union of the parts, plus a margin),
            # so the doser is drawn at the same scale in each
            img = img[int(0.12 * Hh):int(0.93 * Hh), int(0.29 * Ww):int(0.86 * Ww)]
        imgs.append(img)
    fws = [fh * H * im.shape[1] / im.shape[0] / W_IN for im in imgs]   # exact widths
    x_end = 0.98
    gap = (x_end - sum(fws)) / (len(fws) - 1)
    xs, x = [], 0.0
    for fw_ in fws:
        xs.append(x)
        x += fw_ + gap
    # brace geometry: feet just above the axes, tips under the keyframes
    ax_pos = axt.get_position()
    t_to_fig = lambda t: ax_pos.x0 + ax_pos.width * t / (tt[-1] + 4)  # noqa: E731
    y_feet = ax_pos.y1 + 0.03 / H
    r_in = 0.045
    for (name, kind, text, ph_), img, fw_, x in zip(frames, imgs, fws, xs):
        axk = fig.add_axes([x, fy, fw_, fh])
        axk.imshow(img, interpolation="lanczos")
        bare(axk)
        for sp in axk.spines.values():
            sp.set_visible(True), sp.set_color(MUTED), sp.set_linewidth(0.6)
        axk.text(0.0, 1.03, text, transform=axk.transAxes, ha="left",
                 va="bottom", fontsize=4.8, color=INK, linespacing=1.1)
        if ph_:
            a_, b_ = spans[ph_]
            xm, ytip = brace(fig, t_to_fig(a_) + 0.0015, t_to_fig(b_) - 0.0015, y_feet,
                             r_in / W_IN, r_in / H)
            # up from the tip to the nearest point of the frame's lower edge
            xk = min(max(xm, x + 0.2 * fw_), x + 0.8 * fw_)
            fig.add_artist(plt.Line2D([xm, xk], [ytip + 0.004, fy - 0.004],
                                      transform=fig.transFigure, lw=0.6, color=INK2))
    save(fig, "dosing")


# ----------------------------------------------------------------------------
# Fig. 4  using the doser: fill, fit, dose; one auger per powder
# ----------------------------------------------------------------------------
# Sam's photo of 17 Nov 2026 (review of 17 Nov, point 5.4), replacing the 10 Sep one.
# The augers lie horizontally, staggered, caps to the right, so no rotation is needed.
LINEUP_PHOTO = "augers_lineup_2026-11-17.jpg"
LINEUP_BOX = (1450, 230, 3720, 2830)   # pixel crop of the 4032 x 3024 original:
                                       # every label and cap (checked on 18 Nov);
                                       # the outlet ends, left, are cut
LINEUP = [  # handwritten label (top to bottom in the photo), powder id
    ("Brown rice flour (auger 1)", "brown-rice-flour"),
    ("Brown rice flour (auger 2)", "brown-rice-flour"),
    ("White rice flour", "white-rice-flour"),
    ("Sodium alginate", "sodium-alginate"),
    ("Calcium lactate", "calcium-lactate"),
    ("Carboxymethyl cellulose", "carboxymethyl-cellulose"),
    ("Xanthan gum", "xanthan-gum"),
    ("Sodium chloride (table salt)", "salt"),
]


# Callout points: the centre of each auger's cap (the black NaCl tube's end), in
# pixels of the 4032 x 3024 original, same order.  Estimated on 17 Nov without a
# render; checked against the photo on 18 Nov (each point is on its own cap).
LINEUP_XY = [(2524, 484), (2643, 730), (2758, 1012), (2879, 1284), (3008, 1593),
             (3155, 1911), (3302, 2238), (3542, 2601)]
LINEUP_NAME = ["Brown rice flour (1)", "Brown rice flour (2)", "White rice flour",
               "Sodium alginate", "Calcium lactate", "CMC", "Xanthan gum",
               "NaCl (table salt)"]


USE_H = 2.05            # inches: every panel of the row has this height


def fig_use_panels() -> None:
    """Fig. 5 (was 4) as four subfigures of one height (review of 11 Nov 2026:
    aligned panels, a callout for the aluminium cup in (c), no "Label, and
    delivery..." header in (d), the tilt in the caption with an asterisk).

    Review of 17 Nov 2026: (a) and (b) re-cropped so the auger is in the
    middle (points 5.1, 5.2; our earlier crops had pushed it to one side), and
    (d) is Sam's photo of 17 Nov with one level callout per auger (point 5.4)."""
    steps = [
        # (a) the auger is at 41-57 % of the photo's width: centre it
        ("use_a_fill", "auger_filled_salt_2026-07-29.jpg", (0.22, 0.25, 0.77, 1.0)),
        # (b) left half of the dose video's side-by-side frame: the whole auger,
        # from its capped end, and the hand that holds it
        ("use_b_fit", "video_fit_auger_t10.jpg", (0.0, 0.0, 0.33, 1.0)),
        ("use_c_ready", "video_loaded_t17.jpg", (0.60, 0.0, 0.93, 1.0)),
    ]
    for stem, name, crop in steps:
        img = photo(name)
        H, W = img.shape[:2]
        l, t, r, b = crop
        img = img[int(t * H):int(b * H), int(l * W):int(r * W)]
        fig, ax = image_panel(USE_H * img.shape[1] / img.shape[0], USE_H)
        ax.imshow(img, interpolation="lanczos")
        if stem == "use_c_ready":
            # the aluminium cup that stands in the glass beaker (review, 03:49)
            ax.annotate("Aluminium cup\n(6063?)", xy=(312, 500), xytext=(600, 760),
                        fontsize=5.6, color=INK, ha="right", va="center",
                        multialignment="left",
                        bbox=dict(fc="white", ec="none", alpha=0.88, pad=1.2),
                        arrowprops=dict(arrowstyle="-", lw=0.6, color=CALL,
                                        shrinkA=0, shrinkB=1.5), zorder=5)
            ax.plot(312, 500, "o", ms=2.2, color=CALL, zorder=6)
        save(fig, stem)

    # (d) one auger per powder, stored filled; callouts from the data, each level
    # with its auger (the augers lie horizontally, one above the other)
    img = photo(LINEUP_PHOTO, box=LINEUP_BOX)
    hp = img.shape[0]
    w_photo = USE_H * img.shape[1] / hp
    w_text = 0.82
    fig = plt.figure(figsize=(w_photo + w_text, USE_H))
    axl = fig.add_axes([0, 0, w_photo / (w_photo + w_text), 1])
    axl.imshow(img, interpolation="lanczos")
    bare(axl)
    xt = (w_photo + 0.05) / (w_photo + w_text)
    star = "*"                  # on the first value only; the caption explains it
    for (_, pid), name, (px, py) in zip(LINEUP, LINEUP_NAME, LINEUP_XY):
        px, py = px - LINEUP_BOX[0], py - LINEUP_BOX[1]
        yy = 1 - py / hp                        # the auger's height, figure fraction
        if pid in m.DID_NOT_CONVEY:
            val = "none measurable"
        else:
            val = f"{m.per_turn(m.REP_RUN[pid], 45.0)[0]:.0f} mg per rev." + star
            star = ""
        fig.text(xt, yy, f"{name}\n{val}", fontsize=5.4, color=m.colour(pid),
                 va="center", linespacing=1.1)
        con = ConnectionPatch(xyA=(px, py), coordsA=axl.transData,
                              xyB=(xt - 0.012, yy), coordsB=fig.transFigure,
                              arrowstyle="-", lw=0.5, color=CALL)
        fig.add_artist(con)
        axl.plot(px, py, "o", ms=2.2, color=CALL)
    save(fig, "use_d_augers")
    print(f"Fig. 5 panel widths (in): (d) {w_photo + w_text:.3f}")


if __name__ == "__main__":
    FIGS.mkdir(exist_ok=True), PREVIEW.mkdir(exist_ok=True)
    fig_doser_panels()
    fig_dosing()
    fig_use_panels()
