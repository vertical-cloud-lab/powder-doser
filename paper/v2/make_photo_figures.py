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
        ("Auger tube: the powder\nreservoir, filled from\nthe capped end", (1300, 930), (2900, 1210), "right"),
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
    # dashed box: the part drawn in section in (c)
    ax.add_patch(Rectangle((1020 * k, 760 * k), 520 * k, 380 * k, fill=False,
                           lw=0.9, ec=CALL, ls=(0, (3, 1.5)), zorder=7))
    ax.text(1020 * k, 750 * k, "section in (c)", fontsize=5.0, color=CALL,
            ha="left", va="bottom", style="italic", zorder=7,
            bbox=dict(fc="white", ec="none", alpha=0.8, pad=0.6))
    save(fig, "doser_a_photo")

    # (b) exploded view (PR #170, the drawing only, BOM table cropped off)
    ex = np.asarray(Image.open(OLD / "assets" / "assembly_exploded_bom.png").convert("RGB"))
    h, w = ex.shape[:2]
    ex = ex[:, : int(0.635 * w)]
    fig, ax = image_panel(DOSER_R_W, DOSER_R_W * ex.shape[0] / ex.shape[1])
    ax.imshow(ex, interpolation="lanczos")
    save(fig, "doser_b_exploded")

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


def card(ax, x, y, w, h, who, when, text, colour):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.008,rounding_size=0.02",
                                fc="white", ec=colour, lw=0.8, transform=ax.transAxes))
    ax.text(x + 0.02, y + h - 0.03, who, transform=ax.transAxes, fontsize=5.6,
            fontweight="bold", color=colour, va="top")
    ax.text(x + w - 0.02, y + h - 0.03, when, transform=ax.transAxes, fontsize=5.0,
            color=INK2, va="top", ha="right")
    ax.text(x + 0.02, y + h - 0.13, textwrap.fill(text, 46), transform=ax.transAxes,
            fontsize=5.2, color=INK, va="top", linespacing=1.2)


def box(ax, xy, text, w=0.27, h=0.15, fc="#eef1f7", ec="#7a8296"):
    x, y = xy
    ax.add_patch(FancyBboxPatch((x - w / 2, y - h / 2), w, h,
                                boxstyle="round,pad=0.01,rounding_size=0.02",
                                fc=fc, ec=ec, lw=0.7, transform=ax.transAxes))
    ax.text(x, y, text, transform=ax.transAxes, ha="center", va="center",
            fontsize=5.3, linespacing=1.15)


def arrow(ax, a, b, rad=0.0, text=None):
    ax.add_patch(FancyArrowPatch(a, b, transform=ax.transAxes, arrowstyle="-|>",
                                 mutation_scale=6, lw=0.8, color=INK2,
                                 connectionstyle=f"arc3,rad={rad}"))
    if text:
        ax.text((a[0] + b[0]) / 2, (a[1] + b[1]) / 2, text, transform=ax.transAxes,
                fontsize=4.9, color=INK2, ha="center", va="center", style="italic",
                bbox=dict(fc="white", ec="none", pad=0.5))


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


def fig_dosing() -> None:
    """Fig. 4 (was 3): request and reply, the control loop, one dose by phase.

    Review of 11 Nov 2026: the phone-screen snippet is gone, the loop is drawn
    as one row with a single loop back, and the keyframe leaders are lines.
    Kept as one image (not subfigures): the leaders cross between panels."""
    import build_dose_traces as bt
    fig = plt.figure(figsize=(W_IN, 4.75))

    # (a) the request and the reply (PR #166, 29 Sep 2026)
    ax = fig.add_axes([0.0, 0.615, 0.40, 0.355])
    bare(ax)
    ax.set_xlim(0, 1), ax.set_ylim(0, 1)
    card(ax, 0.02, 0.53, 0.96, 0.43, "sgbaird", "29 Sep 2026, 22:36 UTC", REQUEST, "#4a3aa7")
    card(ax, 0.02, 0.02, 0.96, 0.43, "claude[bot]", "22:37 UTC", REPLY, "#1baf7a")
    arrow(ax, (0.5, 0.53), (0.5, 0.445))
    label(ax, "a", x=0.0, y=1.0)

    # (b) the control loop, left to right, with the measurement looping back
    axb = fig.add_axes([0.425, 0.615, 0.575, 0.355])
    bare(axb)
    axb.set_xlim(0, 1), axb.set_ylim(0, 1)
    yb, bw, bh = 0.60, 0.185, 0.34
    xs_ = [0.10, 0.365, 0.63, 0.895]
    texts = ["Dose request\n(target mass)", "Three-phase\ncontroller\n(microcontroller)",
             "Auger rotation,\nsolenoid taps,\ntilt servos", "Analytical\nbalance"]
    for x_, t_ in zip(xs_, texts):
        box(axb, (x_, yb), t_, w=bw, h=bh)
    for x0_, x1_, t_ in [(xs_[0], xs_[1], None), (xs_[1], xs_[2], None),
                         (xs_[2], xs_[3], "powder")]:
        arrow(axb, (x0_ + bw / 2 + 0.004, yb), (x1_ - bw / 2 - 0.004, yb))
        if t_:
            axb.text((x0_ + x1_) / 2, yb + 0.035, t_, transform=axb.transAxes,
                     fontsize=4.9, color=INK2, ha="center", va="bottom", style="italic")
    yl = 0.17                                   # the loop back, under the row
    axb.plot([xs_[3], xs_[3], xs_[1]], [yb - bh / 2 - 0.01, yl, yl],
             color=INK2, lw=0.8, transform=axb.transAxes, solid_capstyle="butt")
    arrow(axb, (xs_[1], yl), (xs_[1], yb - bh / 2 - 0.006))
    axb.text((xs_[1] + xs_[3]) / 2, yl - 0.035, "measured mass, read after every step",
             transform=axb.transAxes, fontsize=4.9, color=INK2, ha="center",
             va="top", style="italic")
    axb.text(xs_[0], yb + bh / 2 + 0.05, "agent or person", ha="center", fontsize=4.9,
             color=INK2, style="italic", transform=axb.transAxes)
    label(axb, "b", x=0.0, y=1.0)

    # (c) one dose, phase by phase
    dose = nacl_trace()
    axt = fig.add_axes([0.075, 0.075, 0.905, 0.25])
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
    label(axt, "c", x=-0.075, y=1.0)

    # keyframes above the trace: before, the tube at each phase, after
    frames = [
        ("salt_demo_before_2026-09-15.jpg", "photo", "Before: empty cup", 0.0),
        ("cad_tilt45.png", "cad", "", None),
        ("cad_tilt22p5.png", "cad", "", None),
        ("cad_tilt00.png", "cad", "", None),
        ("salt_demo_after_2026-09-15.jpg", "photo", "Done", tt[-1]),
    ]
    phases_for = [None, "bulk", "fine", "tap", None]
    n = len(frames)
    fw, fh, fy = 0.17, 0.215, 0.375
    xs = np.linspace(0.075, 0.98 - fw, n)
    for (name, kind, cap, tmark), ph_, x in zip(frames, phases_for, xs):
        axk = fig.add_axes([x, fy, fw, fh])
        img = photo(name)
        H, W = img.shape[:2]
        if kind == "photo":
            img = img[int(0.30 * H):int(0.78 * H), int(0.05 * W):int(0.95 * W)]
        else:
            img = img[int(0.05 * H):int(0.95 * H), int(0.12 * W):int(0.88 * W)]
        axk.imshow(img)
        bare(axk)
        for sp in axk.spines.values():
            sp.set_visible(True), sp.set_color(MUTED), sp.set_linewidth(0.6)
        text = PHASE_TEXT[ph_] if ph_ else cap
        axk.text(0.0, 1.02, text, transform=axk.transAxes, ha="left",
                 va="bottom", fontsize=4.8, color=INK, linespacing=1.1)
        # leader (a line: it only links the frame to its stretch of the trace)
        if ph_:
            a_, b_ = spans[ph_]
            tx = (a_ + b_) / 2
        else:
            tx = tmark
        con = ConnectionPatch(xyA=(0.5, 0.0), coordsA=axk.transAxes,
                              xyB=(tx, 1120), coordsB=axt.transData,
                              arrowstyle="-", lw=0.6, color=INK2)
        fig.add_artist(con)
    save(fig, "dosing")


# ----------------------------------------------------------------------------
# Fig. 4  using the doser: fill, fit, dose; one auger per powder
# ----------------------------------------------------------------------------
LINEUP = [  # handwritten label (top to bottom in the rotated photo), powder id
    ("Sodium chloride (table salt)", "salt"),
    ("Carboxymethyl cellulose", "carboxymethyl-cellulose"),
    ("Sodium alginate", "sodium-alginate"),
    ("Brown rice flour (auger 2)", "brown-rice-flour"),
    ("Brown rice flour (auger 1)", "brown-rice-flour"),
    ("Xanthan gum", "xanthan-gum"),
    ("White rice flour", "white-rice-flour"),
    ("Calcium lactate", "calcium-lactate"),
]


# tape-label positions on the rotated, cropped lineup photo (pixels), same order
LINEUP_XY = [(760, 80), (670, 160), (540, 230), (510, 390), (440, 510),
             (330, 610), (250, 735), (170, 895)]
LINEUP_NAME = ["NaCl (table salt)", "CMC", "Sodium alginate", "Brown rice flour (2)",
               "Brown rice flour (1)", "Xanthan gum", "White rice flour", "Calcium lactate"]


USE_H = 2.15            # inches: every panel of the row has this height


def fig_use_panels() -> None:
    """Fig. 5 (was 4) as four subfigures of one height (review of 11 Nov 2026:
    aligned panels, a callout for the aluminium cup in (c), no "Label, and
    delivery..." header in (d), the tilt in the caption with an asterisk)."""
    steps = [
        ("use_a_fill", "auger_filled_salt_2026-07-29.jpg", (0.05, 0.25, 0.60, 1.0)),
        ("use_b_fit", "video_fit_auger_t10.jpg", (0.12, 0.0, 0.45, 1.0)),
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

    # (d) one auger per powder, stored filled; callouts from the data
    img = photo("augers_lineup_2026-09-10.jpg", rotate=-27)
    H, W = img.shape[:2]
    img = img[int(0.06 * H):int(0.86 * H), int(0.20 * W):int(0.80 * W)]
    img = img[380 + 280:380 + 1300, 450:]
    w_photo = USE_H * img.shape[1] / img.shape[0]
    w_text = 0.86
    fig = plt.figure(figsize=(w_photo + w_text, USE_H))
    axl = fig.add_axes([0, 0, w_photo / (w_photo + w_text), 1])
    axl.imshow(img)
    bare(axl)
    xt = (w_photo + 0.06) / (w_photo + w_text)
    ys = np.linspace(0.93, 0.07, len(LINEUP))
    for i, ((_, pid), name, (px, py), yy) in enumerate(zip(LINEUP, LINEUP_NAME, LINEUP_XY, ys)):
        if pid in m.DID_NOT_CONVEY:
            val = "none measurable"
        else:
            val = f"{m.per_turn(m.REP_RUN[pid], 45.0)[0]:.0f} mg per rev." + ("*" if i == 0 else "")
        fig.text(xt, yy, f"{name}\n{val}", fontsize=5.4, color=m.colour(pid),
                 va="center", linespacing=1.1)
        con = ConnectionPatch(xyA=(px, py), coordsA=axl.transData,
                              xyB=(xt - 0.01, yy), coordsB=fig.transFigure,
                              arrowstyle="-", lw=0.5, color=CALL)
        fig.add_artist(con)
        axl.plot(px, py, "o", ms=2.2, color=CALL)
    save(fig, "use_d_augers")


if __name__ == "__main__":
    FIGS.mkdir(exist_ok=True), PREVIEW.mkdir(exist_ok=True)
    fig_doser_panels()
    fig_dosing()
    fig_use_panels()
