#!/usr/bin/env python3
"""Figs. 1, 3 and 4 (v2): the doser, how a dose runs, and how it is used.

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
    fig.savefig(FIGS / f"{stem}.pdf")
    fig.savefig(PREVIEW / f"{stem}.png", dpi=220, facecolor="white")
    plt.close(fig)
    print("wrote", stem)


# ----------------------------------------------------------------------------
# Fig. 1  the doser
# ----------------------------------------------------------------------------
def fig1_doser() -> None:
    fig = plt.figure(figsize=(W_IN, 4.55))

    # (a) photograph with callouts; asset is 1500 x 2000 (3024 x 4032 / 2.016)
    k = 1500 / 3024
    img = photo("rig_2026-09-11.jpg")
    ax = fig.add_axes([0.0, 0.0, 0.50, 1.0])
    ax.imshow(img)
    x0, x1, y0, y1 = 120 * k, 2950 * k, 230 * k, 4032 * k
    ax.set_xlim(x0, x1), ax.set_ylim(y1, y0)
    bare(ax)
    # (part, point on the photo in original pixels, label position in original pixels)
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
                    fontsize=5.4, color=INK, ha="left" if side == "left" else "right",
                    va="center", linespacing=1.1,
                    bbox=dict(fc="white", ec="none", alpha=0.85, pad=1.2),
                    arrowprops=dict(arrowstyle="-", lw=0.6, color=CALL,
                                    shrinkA=0, shrinkB=1.5), zorder=5)
        ax.plot(px * k, py * k, "o", ms=2.2, color=CALL, zorder=6)
    # callout box around the auger, linked to the section view
    auger_box = Rectangle((1020 * k, 760 * k), 520 * k, 380 * k, fill=False,
                          lw=0.9, ec=CALL, ls=(0, (3, 1.5)), zorder=7)
    ax.add_patch(auger_box)
    label(ax, "a", x=0.01, y=0.99, inside=True)

    # (b) exploded view (PR #170, the drawing only, BOM table cropped off)
    axb = fig.add_axes([0.505, 0.47, 0.495, 0.53])
    ex = np.asarray(Image.open(OLD / "assets" / "assembly_exploded_bom.png").convert("RGB"))
    h, w = ex.shape[:2]
    axb.imshow(ex[:, : int(0.635 * w)])
    bare(axb)
    label(axb, "b", x=0.0, y=0.98, inside=True)

    # (c) auger section view (callout from the photo)
    axc = fig.add_axes([0.53, 0.0, 0.25, 0.47])
    mf.auger_cutaway(axc)
    label(axc, "c", x=0.0, y=0.98, inside=True)
    con = ConnectionPatch(xyA=(1540 * k, 950 * k), coordsA=ax.transData,
                          xyB=(0.12, 0.62), coordsB=axc.transAxes,
                          arrowstyle="-", lw=0.8, color=CALL, ls=(0, (3, 1.5)),
                          zorder=8)
    fig.add_artist(con)

    # (d) powder in the beaker after a dose
    axd = fig.add_axes([0.80, 0.03, 0.195, 0.41])
    pb = photo("powder_in_beaker_2026-09-10.jpg")
    H, W = pb.shape[:2]
    axd.imshow(pb[int(0.36 * H):int(0.78 * H), int(0.12 * W):int(0.84 * W)])
    bare(axd)
    label(axd, "d", x=0.02, y=0.98, inside=True)
    save(fig, "fig1_doser")


# ----------------------------------------------------------------------------
# Fig. 3  how a dose runs
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


def fig3_dosing() -> None:
    import build_dose_traces as bt
    fig = plt.figure(figsize=(W_IN, 5.0))

    # (a) the request and the reply (PR #166, 29 Sep 2026)
    ax = fig.add_axes([0.0, 0.60, 0.37, 0.40])
    bare(ax)
    ax.set_xlim(0, 1), ax.set_ylim(0, 1)
    card(ax, 0.02, 0.53, 0.94, 0.40, "sgbaird", "29 Sep 2026, 22:36 UTC", REQUEST, "#4a3aa7")
    card(ax, 0.02, 0.04, 0.94, 0.40, "claude[bot]", "22:37 UTC", REPLY, "#1baf7a")
    arrow(ax, (0.5, 0.53), (0.5, 0.445))
    label(ax, "a", x=0.0, y=0.955)

    # phone screen: Claude's checklist for the 30 Sep Al 4047 dose (slide video)
    axp = fig.add_axes([0.375, 0.66, 0.175, 0.30])
    ph = photo("video_claude_checklist_t20p5.jpg")
    H, W = ph.shape[:2]
    axp.imshow(ph[int(0.0 * H):int(0.46 * H), int(0.05 * W):int(0.78 * W)])
    bare(axp)
    for sp in axp.spines.values():
        sp.set_visible(True), sp.set_color(MUTED), sp.set_linewidth(0.6)
    axp.text(0.5, -0.02, "Phone, 30 Sep: the agent's\nchecklist for an 8 g dose",
             transform=axp.transAxes, ha="center", va="top", fontsize=4.9, color=INK2)

    # (b) the feedback loop
    axb = fig.add_axes([0.56, 0.60, 0.44, 0.40])
    bare(axb)
    axb.set_xlim(0, 1), axb.set_ylim(0, 1)
    box(axb, (0.2, 0.78), "Dose request\n(target mass)", w=0.3)
    box(axb, (0.2, 0.36), "Three-phase\ncontroller\n(microcontroller)", w=0.3, h=0.22)
    box(axb, (0.75, 0.36), "Auger rotation,\nsolenoid taps,\ntilt servos", w=0.34, h=0.22)
    box(axb, (0.75, 0.78), "Analytical\nbalance", w=0.3)
    arrow(axb, (0.2, 0.705), (0.2, 0.475))
    arrow(axb, (0.355, 0.36), (0.575, 0.36))
    arrow(axb, (0.75, 0.475), (0.75, 0.705), text="powder")
    arrow(axb, (0.595, 0.76), (0.36, 0.44), text="measured mass")
    axb.text(0.2, 0.93, "agent or person", ha="center", fontsize=4.9,
             color=INK2, style="italic", transform=axb.transAxes)
    label(axb, "b", x=0.0, y=0.955)

    # (c) one dose, phase by phase
    dose = nacl_trace()
    axt = fig.add_axes([0.075, 0.07, 0.905, 0.25])
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
        axk.text(0.5, 1.02, text, transform=axk.transAxes, ha="center",
                 va="bottom", fontsize=4.8, color=INK, linespacing=1.1)
        # leader to the matching stretch of the trace
        if ph_:
            a, b = spans[ph_]
            tx = (a + b) / 2
        else:
            tx = tmark
        con = ConnectionPatch(xyA=(0.5, 0.0), coordsA=axk.transAxes,
                              xyB=(tx, 1120), coordsB=axt.transData,
                              arrowstyle="-|>", mutation_scale=5, lw=0.6,
                              color=INK2)
        fig.add_artist(con)
    save(fig, "fig3_dosing")


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


def fig4_use() -> None:
    FH = 2.8
    fig = plt.figure(figsize=(W_IN, FH))
    steps = [
        ("auger_filled_salt_2026-07-29.jpg", (0.05, 0.25, 0.60, 1.0), "Fill the tube through\nits open end, then cap it"),
        ("video_fit_auger_t10.jpg", (0.12, 0.0, 0.45, 1.0), "Fit the filled auger\nto the doser"),
        ("video_loaded_t17.jpg", (0.60, 0.0, 0.93, 1.0), "Ready over the cup"),
    ]
    hgt, y0 = 0.70, 0.22
    k = hgt * FH / W_IN
    x = 0.0
    for i, (name, crop, cap) in enumerate(steps):
        img = photo(name)
        H, W = img.shape[:2]
        l, t, r, b = crop
        img = img[int(t * H):int(b * H), int(l * W):int(r * W)]
        w = k * img.shape[1] / img.shape[0]
        axs = fig.add_axes([x, y0, w, hgt])
        axs.imshow(img)
        bare(axs)
        axs.text(0.5, -0.03, cap, transform=axs.transAxes, ha="center", va="top",
                 fontsize=5.3, linespacing=1.1)
        label(axs, "abc"[i], x=0.03, y=0.97, inside=True)
        if i:
            fig.text(x - 0.007, y0 + hgt / 2, "→", fontsize=10, ha="center",
                     va="center", color=INK2)
        x += w + 0.014

    # (d) one auger per powder, stored filled; callouts from the data
    img = photo("augers_lineup_2026-09-10.jpg", rotate=-27)
    H, W = img.shape[:2]
    img = img[int(0.06 * H):int(0.86 * H), int(0.20 * W):int(0.80 * W)]
    img = img[380 + 280:380 + 1300, 450:]
    hd = 0.84
    wd = hd * FH / W_IN * img.shape[1] / img.shape[0]
    axl = fig.add_axes([x + 0.005, 0.02, wd, hd])
    axl.imshow(img)
    bare(axl)
    label(axl, "d", x=0.02, y=0.98, inside=True)
    xt = x + 0.005 + wd + 0.012
    ys = np.linspace(0.84, 0.10, len(LINEUP))
    for (_, pid), name, (px, py), yy in zip(LINEUP, LINEUP_NAME, LINEUP_XY, ys):
        if pid in m.DID_NOT_CONVEY:
            val = "none measurable"
        else:
            val = f"{m.per_turn(m.REP_RUN[pid], 45.0)[0]:.0f} mg per rev."
        fig.text(xt, yy, f"{name}\n{val}", fontsize=5.1, color=m.colour(pid),
                 va="center", linespacing=1.1)
        con = ConnectionPatch(xyA=(px, py), coordsA=axl.transData,
                              xyB=(xt - 0.004, yy), coordsB=fig.transFigure,
                              arrowstyle="-", lw=0.5, color=CALL)
        fig.add_artist(con)
        axl.plot(px, py, "o", ms=2.2, color=CALL)
    fig.text(xt, 0.985, "Label, and delivery\nper revolution at 22.5°",
             fontsize=4.9, color=INK2, va="top", style="italic")
    save(fig, "fig4_use")


if __name__ == "__main__":
    FIGS.mkdir(exist_ok=True), PREVIEW.mkdir(exist_ok=True)
    fig1_doser()
    fig3_dosing()
    fig4_use()
