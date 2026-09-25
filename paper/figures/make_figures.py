#!/usr/bin/env python3
"""Generate all manuscript figures for the powder-doser base paper.

Real CAD renders and photographs are pulled from paper/figures/assets/
(extracted from the design branches of this repository; the as-built photo and
the annotated render come from issue #165).  The measured-data figures
(Figs. 3-5) are drawn by make_data_figures.py.

Usage:  python3 make_figures.py        (writes PDFs next to this script,
                                        PNG previews in preview/)
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


def _save(fig, stem: str) -> None:
    """Write the PDF used by LaTeX plus a PNG preview for review comments."""
    fig.savefig(HERE / f"{stem}.pdf", bbox_inches="tight")
    (HERE / "preview").mkdir(exist_ok=True)
    fig.savefig(HERE / "preview" / f"{stem}.png", dpi=220, bbox_inches="tight",
                facecolor="white")


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
def tilt_diagram(ax) -> None:
    """Side view of the tilt sweep, drawn natively with its coordinate frame.

    The hinge axis (x, out of the page) passes through the dispense point, so
    the tube swings about the nozzle tip and the dose lands in the same place
    at every angle.  Geometry is schematic (tube length : diameter = 10 : 1).
    """
    L, w = 1.0, 0.1
    shades = {0: "#e9d3a6", 45: "#d4ad62", 90: "#b6862c"}
    for theta, fc in shades.items():
        t = np.deg2rad(theta)
        ux, uy = -np.cos(t), np.sin(t)          # tip -> back end
        nx, ny = -uy, ux                         # tube-width direction
        corners = [
            (0 + nx * w / 2, 0 + ny * w / 2),
            (ux * L + nx * w / 2, uy * L + ny * w / 2),
            (ux * L - nx * w / 2, uy * L - ny * w / 2),
            (0 - nx * w / 2, 0 - ny * w / 2),
        ]
        ax.add_patch(patches.Polygon(corners, closed=True, fc=fc, ec="0.35",
                                     lw=0.6, alpha=0.95, zorder=2))
        ax.text(ux * (L + 0.07), uy * (L + 0.07), f"{theta}°",
                fontsize=5.6, ha="center", va="center", color="0.2")
    # angle arc measured from the horizontal park position
    arc = np.deg2rad(np.linspace(0, 45, 40))
    ax.plot(-0.46 * np.cos(arc), 0.46 * np.sin(arc), color="0.35", lw=0.6,
            zorder=3)
    ax.text(-0.36 * np.cos(np.deg2rad(22)), 0.36 * np.sin(np.deg2rad(22)),
            r"$\theta$", fontsize=7, ha="center", va="center", zorder=4)
    # fixed dispense point and falling dose
    ax.plot(0, 0, "o", ms=4.2, color="#d03b3b", zorder=5)
    for dy in (-0.10, -0.18, -0.26):
        ax.plot(0, dy, ".", ms=1.8, color="#b6862c", zorder=4)
    ax.add_patch(patches.Rectangle((-0.12, -0.42), 0.24, 0.1, fc="#fbf3df",
                                   ec="0.35", lw=0.6, zorder=3))
    # coordinate frame (hinge axis x points out of the page)
    ox, oy = 0.3, 0.62
    kw = dict(arrowstyle="-|>", lw=0.7, color="0.15", mutation_scale=5)
    ax.annotate("", xy=(ox + 0.22, oy), xytext=(ox, oy), arrowprops=kw)
    ax.annotate("", xy=(ox, oy + 0.22), xytext=(ox, oy), arrowprops=kw)
    ax.text(ox + 0.25, oy, "y", fontsize=6, style="italic", va="center")
    ax.text(ox, oy + 0.26, "z", fontsize=6, style="italic", ha="center")
    ax.add_patch(patches.Circle((ox, oy), 0.028, fc="white", ec="0.15",
                                lw=0.6, zorder=5))
    ax.plot(ox, oy, ".", ms=1.6, color="0.15", zorder=6)
    ax.text(ox - 0.04, oy - 0.07, "x = hinge axis\n(out of page)",
            fontsize=5.0, style="italic", ha="left", va="top")
    ax.set_xlim(-1.2, 0.72)
    ax.set_ylim(-0.48, 1.16)
    ax.set_aspect("equal")
    ax.set_axis_off()


def fig1() -> None:
    fig = plt.figure(figsize=(DOUBLE_COL_IN, 4.75))
    outer = fig.add_gridspec(2, 1, height_ratios=[1.12, 1.0], hspace=0.06)
    top = outer[0].subgridspec(1, 2, wspace=0.04)
    bottom = outer[1].subgridspec(1, 3, width_ratios=[0.95, 1.05, 1.0],
                                  wspace=0.12)

    # (a) annotated CAD render and (b) the as-built module, same viewpoint
    #     (issue #165; photo: frame at t = 65 s of the first automated dispense)
    ax = fig.add_subplot(top[0, 0])
    show(ax, "cad_render_annotated.png")
    panel_label(ax, "a")
    ax = fig.add_subplot(top[0, 1])
    show(ax, "as_built_first_dispense.jpg", crop_white=False)
    panel_label(ax, "b")

    # (c) powder path through the module, drawn to the no-hopper design: the
    #     auger tube itself is the reservoir, loaded through slots; the dose
    #     lands in a cup on the analytical balance.
    ax = fig.add_subplot(bottom[0, 0])
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10)
    ax.set_axis_off()
    panel_label(ax, "c")
    tube_x0, tube_x1 = 3.2, 5.2
    tube_y0, tube_y1 = 2.6, 9.4
    ax.add_patch(patches.Rectangle((tube_x0, tube_y0), tube_x1 - tube_x0,
                                   tube_y1 - tube_y0, fc="#f3e6c8", ec="0.3",
                                   lw=0.8))
    ax.add_patch(patches.Rectangle((4.0, tube_y0 + 0.2), 0.4,
                                   tube_y1 - tube_y0 - 0.4, fc="#e0c79a",
                                   ec="0.45", lw=0.4))
    ty = np.linspace(tube_y0 + 0.3, tube_y1 - 0.3, 240)
    tx = 4.2 + 0.8 * np.sin((ty - tube_y0) * 3.0)
    ax.plot(tx, ty, color="#b6862c", lw=0.9)
    for sy in (tube_y1 - 0.7, tube_y1 - 1.3):
        ax.add_patch(patches.Rectangle((tube_x0 - 0.02, sy), 0.45, 0.2,
                                       fc="white", ec="0.3", lw=0.6))
    ax.add_patch(patches.Polygon([(3.75, tube_y0), (4.65, tube_y0),
                                  (4.4, tube_y0 - 0.7), (4.0, tube_y0 - 0.7)],
                                 closed=True, fc="#f3e6c8", ec="0.3", lw=0.7))
    for dy in np.linspace(tube_y0 - 0.9, 1.45, 5):
        ax.plot(4.2, dy, ".", ms=2.0, color="#b6862c")
    ax.add_patch(patches.Polygon([(3.1, 1.3), (5.3, 1.3), (5.0, 0.4),
                                  (3.4, 0.4)], closed=True, fc="#fbf3df",
                                 ec="0.3", lw=0.7))
    ax.add_patch(patches.Rectangle((2.4, 0.05), 3.6, 0.3, fc="#dfe6ef",
                                   ec="0.3", lw=0.7))
    callouts_c = [
        ("loading slots\n(tube = reservoir)", (4.9, tube_y1 - 1.0), (5.7, tube_y1 - 0.5)),
        ("single-start flight,\n10 mm pitch", (4.95, 6.3), (5.7, 6.6)),
        ("Ø 8 mm core,\nØ 21 mm bore", (4.35, 4.6), (5.7, 4.5)),
        ("exit nozzle", (4.45, tube_y0 - 0.4), (5.7, tube_y0 - 0.2)),
        ("cup on balance", (5.2, 0.8), (5.7, 1.05)),
    ]
    for text, (xt, yt), (xl, yl) in callouts_c:
        ax.annotate(text, xy=(xt, yt), xytext=(xl, yl), fontsize=5.0,
                    ha="left", va="center",
                    arrowprops=dict(arrowstyle="-", lw=0.5, color="0.35"))

    # (d) tilt sweep about the fixed dispense point, with its coordinate frame
    ax = fig.add_subplot(bottom[0, 1])
    tilt_diagram(ax)
    panel_label(ax, "d")

    # (e) closed-loop gravimetric dosing: the target mass enters the
    #     controller, which drives the actuators; the balance feeds the
    #     measured mass back to the controller.
    ax = fig.add_subplot(bottom[0, 2])
    ax.set_xlim(-1.4, 10.4)
    ax.set_ylim(0, 11.9)
    ax.set_axis_off()
    panel_label(ax, "e")
    bw = 4.4
    boxes = [
        (0.0, 8.0, "Dose request\n(target mass)"),
        (0.0, 4.6, "Three-phase\ncontroller (bulk\n→ fine → tap)"),
        (5.8, 4.6, "Auger rotation,\nsolenoid taps,\ntilt servo"),
        (5.8, 0.9, "Analytical\nbalance (A&D\nHR-100A)"),
    ]
    for x, y, label in boxes:
        ax.add_patch(patches.FancyBboxPatch((x, y), bw, 2.3,
                                            boxstyle="round,pad=0.12",
                                            fc="#eef3fb", ec="0.3", lw=0.7))
        ax.text(x + bw / 2, y + 1.15, label, ha="center", va="center",
                fontsize=4.9)
    arrow = dict(arrowstyle="->", lw=0.8, color="0.2")
    ax.annotate("", xy=(bw / 2, 7.0), xytext=(bw / 2, 8.0), arrowprops=arrow)
    ax.annotate("", xy=(5.8, 5.75), xytext=(bw + 0.1, 5.75), arrowprops=arrow)
    ax.annotate("", xy=(5.8 + bw / 2, 3.3), xytext=(5.8 + bw / 2, 4.6),
                arrowprops=arrow)
    ax.annotate("", xy=(2.9, 4.6), xytext=(5.8, 2.0), arrowprops=arrow)
    ax.text(2.4, 2.6, "measured\nmass", fontsize=4.8, ha="center",
            color="0.3")

    _save(fig, "fig1_overview")
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
    ax.set_title("Whole-assembly attempt\n(single prompt)", fontsize=5.5)

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
    _save(fig, "fig2_genai")
    plt.close(fig)


# ----------------------------------------------------------------------------
# Figure 6 — future work: multi-doser array
# ----------------------------------------------------------------------------
def fig6() -> None:
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
    ax.set_title("8-channel radial array\n(concept)", fontsize=6)

    # (b) inward-tilting collection-cup render
    ax = fig.add_subplot(gs[0, 1])
    show(ax, "inward_collection_cup_iso.png")
    panel_label(ax, "b")
    ax.set_title("Inward-tilting channels\nover shared cup\n(preliminary CAD)", fontsize=6)

    _save(fig, "fig6_future")
    plt.close(fig)


# ----------------------------------------------------------------------------
# Figure S1 — exit-nozzle variants
# ----------------------------------------------------------------------------
def figs1() -> None:
    fig = plt.figure(figsize=(DOUBLE_COL_IN, 2.6))
    gs = fig.add_gridspec(1, 5, width_ratios=[0.7, 1, 1, 1, 1], wspace=0.12)
    ax = fig.add_subplot(gs[0, 0])
    show(ax, "auger_geared_cross_section.png")
    panel_label(ax, "a")
    for k in range(1, 5):
        ax = fig.add_subplot(gs[0, k])
        show(ax, f"nozzle_type{k}_cross_section.png")
        panel_label(ax, "abcde"[k])
    _save(fig, "figS1_nozzles")
    plt.close(fig)


if __name__ == "__main__":
    for fn in (fig1, fig2, fig6, figs1):
        fn()
        print(f"wrote {fn.__name__}")
