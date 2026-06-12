#!/usr/bin/env python3
"""Generate all manuscript figures for the powder-doser base paper.

Real CAD renders are pulled from paper/figures/assets/ (extracted from the
design branches of this repository).  Panels that contain synthetic
(placeholder) data are watermarked with a diagonal "SYNTHETIC DATA" label so
they cannot be mistaken for measurements; they will be replaced with real
bench data before submission.

Usage:  python3 make_figures.py        (writes PDFs next to this script)
"""

from __future__ import annotations

import pathlib

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib import patches
from PIL import Image

HERE = pathlib.Path(__file__).resolve().parent
ASSETS = HERE / "assets"

# RSC column geometry (cm -> inch)
SINGLE_COL_IN = 8.3 / 2.54
DOUBLE_COL_IN = 17.1 / 2.54

RNG = np.random.default_rng(42)

plt.rcParams.update(
    {
        "font.size": 7,
        "font.family": "sans-serif",
        "axes.linewidth": 0.6,
        "lines.linewidth": 1.0,
        "savefig.dpi": 600,
        "figure.dpi": 150,
    }
)


def load(name: str, crop_white: bool = True) -> np.ndarray:
    img = Image.open(ASSETS / name)
    if img.mode in ("RGBA", "LA", "P"):
        img = img.convert("RGBA")
        bg = Image.new("RGBA", img.size, (255, 255, 255, 255))
        img = Image.alpha_composite(bg, img)
    img = img.convert("RGB")
    arr = np.asarray(img)
    if crop_white:
        mask = (arr < 245).any(axis=2)
        rows = np.flatnonzero(mask.any(axis=1))
        cols = np.flatnonzero(mask.any(axis=0))
        if rows.size and cols.size:
            pad = 6
            r0, r1 = max(rows[0] - pad, 0), min(rows[-1] + pad, arr.shape[0])
            c0, c1 = max(cols[0] - pad, 0), min(cols[-1] + pad, arr.shape[1])
            arr = arr[r0:r1, c0:c1]
    return arr


def synthetic_watermark(ax, text: str = "SYNTHETIC DATA") -> None:
    """Non-invasive diagonal watermark marking placeholder data."""
    ax.text(
        0.5,
        0.5,
        text,
        transform=ax.transAxes,
        rotation=30,
        fontsize=11,
        color="0.55",
        alpha=0.38,
        ha="center",
        va="center",
        fontweight="bold",
        zorder=10,
    )


def placeholder_note(ax, text: str) -> None:
    ax.text(
        0.5,
        0.02,
        text,
        transform=ax.transAxes,
        fontsize=4.5,
        color="0.45",
        ha="center",
        va="bottom",
        style="italic",
        zorder=10,
    )


def panel_label(ax, letter: str) -> None:
    ax.text(
        0.02,
        0.98,
        f"({letter})",
        transform=ax.transAxes,
        fontsize=8,
        fontweight="bold",
        ha="left",
        va="top",
        bbox=dict(fc="white", ec="none", alpha=0.7, pad=1.0),
        zorder=11,
    )


def show(ax, name: str, **kw) -> None:
    ax.imshow(load(name, **kw))
    ax.set_axis_off()


# ----------------------------------------------------------------------------
# Figure 1 — platform overview
# ----------------------------------------------------------------------------
def fig1() -> None:
    fig = plt.figure(figsize=(DOUBLE_COL_IN, 4.6))
    gs = fig.add_gridspec(2, 3, height_ratios=[1.25, 1.0], hspace=0.32, wspace=0.18)

    # (a) annotated final single-channel assembly render
    ax = fig.add_subplot(gs[0, :2])
    img = load("assembly_iso_final.png")
    ax.imshow(img)
    ax.set_axis_off()
    panel_label(ax, "a")
    h, w = img.shape[:2]
    callouts = [
        ("Archimedes auger\n(printed, geared)", (0.30, 0.42), (0.10, 0.12)),
        ("Auger bracket +\ntap collar", (0.55, 0.38), (0.48, 0.08)),
        ("NEMA-11 stepper\n+ GT2/gear drive", (0.66, 0.36), (0.72, 0.10)),
        ("Hinged mounting plate\n(servo tilt)", (0.62, 0.62), (0.93, 0.42)),
        ("Baseplate", (0.46, 0.72), (0.16, 0.88)),
    ]
    for text, (xt, yt), (xl, yl) in callouts:
        ax.annotate(
            text,
            xy=(xt * w, yt * h),
            xytext=(xl * w, yl * h),
            fontsize=5.5,
            ha="left",
            va="center",
            arrowprops=dict(arrowstyle="-", lw=0.6, color="0.25"),
        )
    placeholder_note(ax, "CAD render; photograph of the printed platform to be added")

    # (b) powder-flow path through the module (tall panel)
    ax = fig.add_subplot(gs[0, 2])
    img = load("single_channel_module_powder_flow.png")
    img = img[int(img.shape[0] * 0.16):, :]  # trim internal title text
    ax.imshow(img)
    ax.set_axis_off()
    panel_label(ax, "b")
    ax.set_title("Powder-flow path (cross-section)", fontsize=6)

    # (c) tilt sweep about the fixed dispense point
    ax = fig.add_subplot(gs[1, 0])
    img = load("rotation_0_45_90.png")
    img = img[int(img.shape[0] * 0.10):, :]  # trim internal suptitle
    ax.imshow(img)
    ax.set_axis_off()
    panel_label(ax, "c")
    ax.set_title("Tilt sweep about fixed dispense point", fontsize=6)

    # (d) closed-loop dosing concept diagram
    ax = fig.add_subplot(gs[1, 1])
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10)
    ax.set_axis_off()
    panel_label(ax, "d")
    ax.set_title("Closed-loop gravimetric dosing", fontsize=6)
    boxes = [
        (1.0, 7.2, "Dose request\n(target mass)"),
        (1.0, 4.2, "Auger + tap +\nvibration actuation"),
        (1.0, 1.2, "Balance reading\n(A&D HR-100A, RS-232)"),
        (6.1, 4.2, "Controller\n(coarse \u2192 trickle)"),
    ]
    for x, y, label in boxes:
        ax.add_patch(
            patches.FancyBboxPatch(
                (x, y),
                3.2,
                1.9,
                boxstyle="round,pad=0.12",
                fc="#eef3fb",
                ec="0.3",
                lw=0.7,
            )
        )
        ax.text(x + 1.6, y + 0.95, label, ha="center", va="center", fontsize=5.5)
    arrow = dict(arrowstyle="->", lw=0.8, color="0.2")
    ax.annotate("", xy=(2.6, 6.1), xytext=(2.6, 7.2), arrowprops=arrow)
    ax.annotate("", xy=(2.6, 3.1), xytext=(2.6, 4.2), arrowprops=arrow)
    ax.annotate("", xy=(6.1, 5.15), xytext=(4.2, 2.2), arrowprops=arrow)
    ax.annotate("", xy=(4.2, 5.15), xytext=(6.1, 5.15), arrowprops=arrow)

    # (e) project timeline
    ax = fig.add_subplot(gs[1, 2])
    panel_label(ax, "e")
    ax.set_title("Design timeline (2026)", fontsize=6)
    milestones = [
        ("Apr 23", 0, "Scoop/excavator sketch"),
        ("Apr 24", 1, "Auger concept; dosing alternatives"),
        ("May 8", 2, "Modular architecture"),
        ("May 12", 3, "Single-channel module"),
        ("May 14", 4, "Part-by-part redesign"),
        ("May 15", 5, "Bracket, geared auger, tap collar"),
        ("May 19", 6, "Servo-tilt mounting plate"),
        ("Jun 1", 7, "97-entry design log"),
    ]
    ax.set_xlim(0, 10)
    ax.set_ylim(-1.6, len(milestones) - 0.2)
    ax.invert_yaxis()
    ax.set_axis_off()
    ax.plot([1.0, 1.0], [-0.4, len(milestones) - 0.6], color="0.3", lw=1.0)
    for date, i, label in milestones:
        ax.plot(1.0, i, "o", ms=3, color="#2a6db5")
        ax.text(0.85, i, date, ha="right", va="center", fontsize=5)
        ax.text(1.3, i, label, ha="left", va="center", fontsize=5.2)

    fig.savefig(HERE / "fig1_overview.pdf", bbox_inches="tight")
    plt.close(fig)


# ----------------------------------------------------------------------------
# Figure 2 — generative-AI CAD examples
# ----------------------------------------------------------------------------
def fig2() -> None:
    fig = plt.figure(figsize=(DOUBLE_COL_IN, 3.5))
    gs = fig.add_gridspec(2, 4, hspace=0.42, wspace=0.12)

    ax = fig.add_subplot(gs[0, 0])
    show(ax, "tap_collar_v1_iso.png")
    panel_label(ax, "a")
    ax.set_title("Tap collar, first AI proposal:\ninterferences, bad tolerancing,\nno component clearance", fontsize=5.5)

    ax = fig.add_subplot(gs[0, 1])
    show(ax, "tap_collar_final_iso.png")
    panel_label(ax, "b")
    ax.set_title("Tap collar after review iterations\n(final part redesigned in Zoo)", fontsize=5.5)

    ax = fig.add_subplot(gs[0, 2])
    show(ax, "auger_assembly_iso.png")
    panel_label(ax, "c")
    ax.set_title("Geared auger + pinion\n(part-by-part workflow)", fontsize=5.5)

    ax = fig.add_subplot(gs[0, 3])
    show(ax, "single_channel_module_iso.png")
    panel_label(ax, "d")
    ax.set_title("Whole-assembly attempt\n(single prompt, v1 module)", fontsize=5.5)

    iters = [
        ("plate_iter1_hole_top.png", "Iter. 1: unexplained\nhole under gear"),
        ("plate_iter2_platforms_iso.png", "Iter. 2: raised platforms\ninstead of hole"),
        ("plate_iter3_gap_top.png", "Iter. 3: gap appears;\nmotor plate floats"),
        ("plate_iter4_final_top.png", "Iter. 4: correct inputs\n\u2192 clean plate"),
    ]
    for k, (name, title) in enumerate(iters):
        ax = fig.add_subplot(gs[1, k])
        show(ax, name)
        panel_label(ax, "efgh"[k])
        ax.set_title(title, fontsize=5.5)

    fig.suptitle(
        "",
        fontsize=1,
    )
    fig.savefig(HERE / "fig2_genai.pdf", bbox_inches="tight")
    plt.close(fig)


# ----------------------------------------------------------------------------
# Figure 3 — dispensing characterization (synthetic placeholder data)
# ----------------------------------------------------------------------------
POWDERS = [
    ("Glass beads (70\u2013110 \u00b5m)", "#2a6db5", 1.6),
    ("Al\u2082O\u2083 (50 \u00b5m)", "#c44e52", 1.1),
    ("316L steel (15\u201345 \u00b5m)", "#55a868", 2.3),
    ("Xanthan gum", "#8172b3", 0.45),
]


def fig3() -> None:
    fig, axs = plt.subplots(
        1, 3, figsize=(DOUBLE_COL_IN, 2.1), gridspec_kw=dict(wspace=0.42)
    )

    # (a) cumulative dispensed mass vs time
    ax = axs[0]
    t = np.linspace(0, 30, 200)
    for name, color, rate in POWDERS:
        m = rate * t * (1 + 0.04 * np.sin(2.2 * t) * np.exp(-t / 18))
        m += RNG.normal(0, 0.02 * rate, t.size).cumsum() * 0.15
        ax.plot(t, m, color=color, label=name, lw=0.9)
    ax.set_xlabel("Time (s)")
    ax.set_ylabel("Dispensed mass (g)")
    ax.legend(fontsize=4.2, frameon=False, loc="upper left")
    panel_label(ax, "a")
    synthetic_watermark(ax)

    # (b) requested vs measured parity
    ax = axs[1]
    req = np.logspace(np.log10(0.02), np.log10(5), 14)
    for name, color, _ in POWDERS:
        meas = req * (1 + RNG.normal(0, 0.035, req.size)) + RNG.normal(
            0, 0.004, req.size
        )
        ax.loglog(req, np.clip(meas, 1e-3, None), "o", ms=2.2, color=color, alpha=0.8)
    lims = [0.01, 8]
    ax.loglog(lims, lims, "-", color="0.4", lw=0.7)
    ax.fill_between(
        lims, [l * 0.9 for l in lims], [l * 1.1 for l in lims], color="0.8", alpha=0.4
    )
    ax.set_xlabel("Requested mass (g)")
    ax.set_ylabel("Measured mass (g)")
    panel_label(ax, "b")
    synthetic_watermark(ax)

    # (c) speed vs accuracy trade-off
    ax = axs[2]
    rpm = np.linspace(5, 120, 40)
    for name, color, rate in POWDERS:
        cv = 0.6 + 0.035 * rpm + RNG.normal(0, 0.12, rpm.size)
        cv = np.convolve(np.clip(cv, 0.3, None), np.ones(5) / 5, mode="same")
        ax.plot(rpm[2:-2], cv[2:-2], color=color, lw=0.9)
    ax.set_xlabel("Auger speed (rpm)")
    ax.set_ylabel("Dose CV (%)")
    panel_label(ax, "c")
    synthetic_watermark(ax)

    fig.savefig(HERE / "fig3_dispense.pdf", bbox_inches="tight")
    plt.close(fig)


# ----------------------------------------------------------------------------
# Figure 4 — design specifics / cross-sections
# ----------------------------------------------------------------------------
def fig4() -> None:
    fig = plt.figure(figsize=(SINGLE_COL_IN, 3.4))
    gs = fig.add_gridspec(1, 2, width_ratios=[0.62, 1.0], wspace=0.1)

    ax = fig.add_subplot(gs[0, 0])
    show(ax, "auger_geared_cross_section.png")
    panel_label(ax, "a")
    ax.set_title("Auger tube\ncross-section", fontsize=6)

    ax = fig.add_subplot(gs[0, 1])
    show(ax, "tap_collar_final_iso.png")
    panel_label(ax, "b")
    ax.set_title("Tap collar + solenoid\nmount (split clamp)", fontsize=6)

    fig.savefig(HERE / "fig4_design.pdf", bbox_inches="tight")
    plt.close(fig)


# ----------------------------------------------------------------------------
# Figure 5 — future work: multi-doser array
# ----------------------------------------------------------------------------
def fig5() -> None:
    fig = plt.figure(figsize=(SINGLE_COL_IN, 2.2))
    gs = fig.add_gridspec(1, 2, width_ratios=[1.0, 1.0], wspace=0.15)

    # (a) radial array schematic
    ax = fig.add_subplot(gs[0, 0])
    ax.set_aspect("equal")
    ax.set_axis_off()
    panel_label(ax, "a")
    n = 8
    for k in range(n):
        ang = 2 * np.pi * k / n
        x, y = 2.4 * np.cos(ang), 2.4 * np.sin(ang)
        rect = patches.Rectangle(
            (-0.42, -0.7),
            0.84,
            1.4,
            fc="#dbe6f4",
            ec="0.3",
            lw=0.6,
            transform=matplotlib.transforms.Affine2D()
            .rotate(ang + np.pi / 2)
            .translate(x, y)
            + ax.transData,
        )
        ax.add_patch(rect)
    ax.add_patch(patches.Circle((0, 0), 0.9, fc="#f6e8c8", ec="0.3", lw=0.8))
    ax.text(0, 0, "shared\ncup", ha="center", va="center", fontsize=5.5)
    ax.set_xlim(-3.6, 3.6)
    ax.set_ylim(-3.6, 3.6)
    ax.set_title("N-channel radial array\n(concept)", fontsize=6)

    # (b) inward-tilting collection-cup render
    ax = fig.add_subplot(gs[0, 1])
    show(ax, "inward_collection_cup_iso.png")
    panel_label(ax, "b")
    ax.set_title("Inward-tilting channels\nover shared cup (CAD)", fontsize=6)

    fig.savefig(HERE / "fig5_future.pdf", bbox_inches="tight")
    plt.close(fig)


# ----------------------------------------------------------------------------
# Figure S1 — exit-nozzle variants
# ----------------------------------------------------------------------------
def figs1() -> None:
    fig, axs = plt.subplots(1, 4, figsize=(DOUBLE_COL_IN, 2.4))
    for k, ax in enumerate(axs, start=1):
        show(ax, f"nozzle_type{k}_cross_section.png")
        ax.set_title(f"Type {k}", fontsize=7)
    fig.savefig(HERE / "figS1_nozzles.pdf", bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    for fn in (fig1, fig2, fig3, fig4, fig5, figs1):
        fn()
        print(f"wrote {fn.__name__}")
