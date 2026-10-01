#!/usr/bin/env python3
"""Generate all manuscript figures for the powder-doser base paper.

Real CAD renders and photographs are pulled from paper/figures/assets/
(extracted from the design branches of this repository; the as-built photo
comes from issue #165 and the current-design annotated render from PR #170).
Fig. 1c is drawn from assets/auger_section.json, an axial cut through the
tested Fusion 360 auger and cap made by data/build_auger_section.py.  The
measured-data figures (Figs. 3-5) are drawn by make_data_figures.py.

Usage:  python3 make_figures.py        (writes PDFs next to this script,
                                        PNG previews in preview/)
"""

from __future__ import annotations

import json
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
    """Side view of the tilt range, drawn natively with its coordinate frame.

    The hinge axis (x, out of the page) passes through the dispense point, so
    the tube swings about the outlet and the dose lands in the same place at
    every angle.  The three poses are the tilts used in the tests: 0 deg
    (horizontal park), 22.5 deg and 45 deg, the maximum.  The firmware's
    "vertical" preset reaches 45 deg because the tilt plate is geared 2:1.
    Geometry is schematic (tube length : diameter = 10 : 1).
    """
    L, w = 1.0, 0.1
    poses = [(0.0, "#e9d3a6", "0° (horizontal park)"),
             (22.5, "#d4ad62", "22.5°"),
             (45.0, "#b6862c", "45° (maximum)")]
    for theta, fc, label in poses:
        t = np.deg2rad(theta)
        ux, uy = -np.cos(t), np.sin(t)          # outlet -> back end
        nx, ny = -uy, ux                         # tube-width direction
        corners = [
            (0 + nx * w / 2, 0 + ny * w / 2),
            (ux * L + nx * w / 2, uy * L + ny * w / 2),
            (ux * L - nx * w / 2, uy * L - ny * w / 2),
            (0 - nx * w / 2, 0 - ny * w / 2),
        ]
        ax.add_patch(patches.Polygon(corners, closed=True, fc=fc, ec="0.35",
                                     lw=0.6, alpha=0.95, zorder=2))
        if theta == 0.0:
            ax.text(-L / 2, -0.11, label, fontsize=5.4, ha="center",
                    va="top", color="0.2")
        else:
            ax.text(ux * (L + 0.06), uy * (L + 0.06), label, fontsize=5.4,
                    ha="right", va="bottom", color="0.2")
    # angle arc measured from the horizontal park position
    arc = np.deg2rad(np.linspace(0, 45, 40))
    ax.plot(-0.46 * np.cos(arc), 0.46 * np.sin(arc), color="0.35", lw=0.6,
            zorder=3)
    ax.text(-0.38 * np.cos(np.deg2rad(11)), 0.38 * np.sin(np.deg2rad(11)),
            r"$\theta$", fontsize=7, ha="center", va="center", zorder=4)
    # fixed dispense point and falling dose
    ax.plot(0, 0, "o", ms=4.2, color="#d03b3b", zorder=5)
    for dy in (-0.10, -0.18, -0.26):
        ax.plot(0, dy, ".", ms=1.8, color="#b6862c", zorder=4)
    ax.add_patch(patches.Rectangle((-0.12, -0.42), 0.24, 0.1, fc="#fbf3df",
                                   ec="0.35", lw=0.6, zorder=3))
    # coordinate frame (hinge axis x points out of the page)
    ox, oy = 0.22, 0.55
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
    ax.set_ylim(-0.48, 1.22)
    ax.set_aspect("equal")
    ax.set_axis_off()


def auger_section(ax) -> None:
    """Fig. 1c: axial cut through the tested auger and its screw-on cap.

    Drawn from assets/auger_section.json (data/build_auger_section.py), i.e.
    the Fusion 360 parts that ran every test, with the outlet at the bottom
    and the cup on the balance below it.  Units are mm.
    """
    sec = json.loads((ASSETS / "auger_section.json").read_text())
    dims = sec["dimensions"]
    for key, fc in (("auger", "#d4ad62"), ("cap", "#5b7fbf")):
        for poly in sec[key]:
            ext = np.asarray(poly["exterior"])
            path = [ext] + [np.asarray(i) for i in poly["interiors"]]
            verts = np.concatenate(path)
            codes = np.concatenate([
                [matplotlib.path.Path.MOVETO]
                + [matplotlib.path.Path.LINETO] * (len(p) - 2)
                + [matplotlib.path.Path.CLOSEPOLY] for p in path])
            ax.add_patch(patches.PathPatch(matplotlib.path.Path(verts, codes),
                                           fc=fc, ec="0.25", lw=0.25,
                                           zorder=3))
    # powder in the reservoir and in the flight, falling to the cup
    rng = np.random.default_rng(3)
    px = rng.uniform(-9.8, 9.8, 900)
    pz = rng.uniform(12, 150, 900)
    keep = (pz > 84) | (np.abs(px) > 4.6)       # not inside the core
    ax.plot(px[keep], pz[keep], ".", ms=0.6, color="#8a6a2a", alpha=0.35,
            zorder=2)
    for z in np.linspace(-6, -36, 6):
        ax.plot(rng.uniform(-0.6, 0.6), z, ".", ms=1.6, color="#8a6a2a",
                zorder=2)
    ax.add_patch(patches.Polygon([(-16, -40), (16, -40), (12, -58),
                                  (-12, -58)], closed=True, fc="#fbf3df",
                                 ec="0.3", lw=0.6))
    ax.add_patch(patches.Rectangle((-26, -64), 52, 6, fc="#dfe6ef", ec="0.3",
                                   lw=0.6))
    pitch = dims["flight_pitch_mm"]
    callouts = [
        ("screw-on cap\n(fill opening)", (13.5, 240), (30, 246)),
        ("reservoir: plain tube,\nØ 25 mm outside,\nØ 21 mm bore", (11.5, 160),
         (30, 168)),
        ("44-tooth gear\n(driven by stepper)", (23, 83), (30, 103)),
        (f"single-start flight,\n{pitch:.1f} mm pitch,\n"
         "on Ø 8 mm core", (8.5, 42), (30, 52)),
        ("tapered outlet", (6, 4), (30, 8)),
        ("cup on balance", (15, -48), (30, -46)),
    ]
    for text, (xt, yt), (xl, yl) in callouts:
        ax.annotate(text, xy=(xt, yt), xytext=(xl, yl), fontsize=4.9,
                    ha="left", va="center",
                    arrowprops=dict(arrowstyle="-", lw=0.45, color="0.35"))
    # 50 mm scale bar
    ax.plot([-44, -44], [150, 200], color="0.2", lw=0.9)
    ax.text(-47, 175, "50 mm", rotation=90, fontsize=4.8, ha="right",
            va="center")
    ax.set_xlim(-60, 92)
    ax.set_ylim(-68, 262)
    ax.set_aspect("equal")
    ax.set_axis_off()


def fig1() -> None:
    fig = plt.figure(figsize=(DOUBLE_COL_IN, 4.75))
    outer = fig.add_gridspec(2, 1, height_ratios=[1.12, 1.0], hspace=0.06)
    top = outer[0].subgridspec(1, 2, wspace=0.04)
    bottom = outer[1].subgridspec(1, 3, width_ratios=[0.95, 1.05, 1.0],
                                  wspace=0.12)

    # (a) annotated CAD render of the current design (PR #170: same camera as
    #     the June render in issue #165, with the Fusion auger, cap, 20-tooth
    #     pinion, solenoid and tap collar swapped in) and (b) the as-built
    #     module (issue #165; frame at t = 65 s of the first automated dispense)
    ax = fig.add_subplot(top[0, 0])
    show(ax, "cad_render_current_annotated.png")
    panel_label(ax, "a")
    ax = fig.add_subplot(top[0, 1])
    show(ax, "as_built_first_dispense.jpg", crop_white=False)
    panel_label(ax, "b")

    # (c) axial cut through the tested auger and cap: the tube is its own
    #     reservoir, filled through the capped end; the flight occupies only
    #     the outlet third, and the 44-tooth gear sits on the outside.
    ax = fig.add_subplot(bottom[0, 0])
    auger_section(ax)
    panel_label(ax, "c")

    # (d) tilt range (0-45 deg) about the fixed dispense point, with its frame
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
# Figure 6 — future work: roller-chain multi-doser (issue #128)
# ----------------------------------------------------------------------------
def fig6() -> None:
    """Hand sketch and Onshape model of the multi-doser carriages.

    Both images are from issue #128 (2026-08-27 update); the Onshape screenshot
    is cropped to the model, removing the editor's toolbars and view cube.
    """
    fig = plt.figure(figsize=(SINGLE_COL_IN, 1.75))
    gs = fig.add_gridspec(1, 2, width_ratios=[1.45, 1.0], wspace=0.06)

    ax = fig.add_subplot(gs[0, 0])
    show(ax, "multidoser_carriage_sketch.png")
    panel_label(ax, "a")

    ax = fig.add_subplot(gs[0, 1])
    show(ax, "multidoser_carriages_onshape.png")
    panel_label(ax, "b")

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
