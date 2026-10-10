#!/usr/bin/env python3
"""Generate all manuscript figures for the powder-doser base paper.

Real CAD renders and photographs are pulled from paper/figures/assets/
(extracted from the design branches of this repository; the as-built photo
comes from issue #165, and the current-design annotated render, the exploded
view and the build-step stills from PR #170).
Fig. 1c is assets/auger_cutaway.png, a shaded 3-D cut-away of the tested
Fusion 360 auger and cap rendered by data/render_auger_cutaway.py.  The
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

    The hinge axis (x, out of the page) runs just behind the outlet: 11.6 mm
    behind it in the PR #170 assembly of the current parts, where the
    44-tooth gear meets the stepper pinion.  The tube swings about that axis,
    so over 0-45 deg the outlet (red) moves only about 3 mm horizontally and
    8 mm down, and the dose lands in nearly the same place.  The three poses
    are the tilts used in the tests: 0 deg (horizontal park), 22.5 deg and
    45 deg, the steepest tilt tested (not the mechanism's limit: the servos
    can turn further).  The firmware's "vertical" preset reaches 45 deg
    because the tilt plate is geared 2:1.  The hinge offset is to scale for
    the 250 mm tube; the tube's width is not (length : diameter = 10 : 1).
    """
    L, w = 1.0, 0.1
    d = 11.6 / 250.0                             # hinge behind the outlet
    hx, hy = -d, 0.0                             # hinge axis (pivot)
    poses = [(0.0, "#e9d3a6", "0° (horizontal park)"),
             (22.5, "#d4ad62", "22.5°"),
             (45.0, "#b6862c", "45° (steepest tested)")]
    outlets = []
    for theta, fc, label in poses:
        t = np.deg2rad(theta)
        ux, uy = -np.cos(t), np.sin(t)          # outlet -> back end
        nx, ny = -uy, ux                         # tube-width direction
        px, py = hx + d * np.cos(t), hy - d * np.sin(t)   # outlet position
        outlets.append((px, py))
        corners = [
            (px + nx * w / 2, py + ny * w / 2),
            (px + ux * L + nx * w / 2, py + uy * L + ny * w / 2),
            (px + ux * L - nx * w / 2, py + uy * L - ny * w / 2),
            (px - nx * w / 2, py - ny * w / 2),
        ]
        ax.add_patch(patches.Polygon(corners, closed=True, fc=fc, ec="0.35",
                                     lw=0.6, alpha=0.95, zorder=2))
        if theta == 0.0:
            ax.text(-L / 2, -0.11, label, fontsize=5.4, ha="center",
                    va="top", color="0.2")
        else:
            ax.text(px + ux * (L + 0.06), py + uy * (L + 0.06), label,
                    fontsize=5.4, ha="right", va="bottom", color="0.2")
    # angle arc measured from the horizontal park position, about the hinge
    arc = np.deg2rad(np.linspace(0, 45, 40))
    ax.plot(hx - 0.46 * np.cos(arc), hy + 0.46 * np.sin(arc), color="0.35",
            lw=0.6, zorder=3)
    ax.text(hx - 0.38 * np.cos(np.deg2rad(11)),
            hy + 0.38 * np.sin(np.deg2rad(11)),
            r"$\theta$", fontsize=7, ha="center", va="center", zorder=4)
    # hinge axis (out of the page), outlet at each tilt, and falling dose
    ax.add_patch(patches.Circle((hx, hy), 0.021, fc="white", ec="0.15",
                                lw=0.5, zorder=6))
    ax.plot(hx, hy, ".", ms=1.2, color="0.15", zorder=7)
    for px, py in outlets:
        ax.plot(px, py, "o", ms=2.6, color="#d03b3b", zorder=5)
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


def auger_cutaway(ax) -> None:
    """Fig. 1c: shaded 3-D cut-away of the tested auger and its screw-on cap.

    The render (assets/auger_cutaway.png, made by
    data/render_auger_cutaway.py) shows the Fusion 360 parts that ran every
    test, cut in half through the tube axis and drawn upright with the
    outlet at the bottom.  The PNG's "anchors" text chunk gives the image
    positions of the labelled features and the projection from the part
    frame (mm; outlet at z = 0, cut face y = 0) to image pixels, so the
    leader and dimension lines follow the render.  Axes units are pixels.
    """
    with Image.open(ASSETS / "auger_cutaway.png") as im:
        meta = json.loads(im.text["anchors"])
        img = np.asarray(im.convert("RGBA"))
    anchor = meta["anchors"]
    A = np.asarray(meta["projection"]["A"])
    b = np.asarray(meta["projection"]["b"])

    def px(x: float, z: float) -> np.ndarray:      # point on the cut face
        return A @ (x, 0.0, z) + b

    s = float(np.hypot(*A[:, 2]))                  # px per mm along the axis
    ax.imshow(img, zorder=1)
    xt = px(0, 0)[0] + 32 * s                      # label column
    callouts = [                                   # text, anchor, label height
        ("screw-on cap", "cap", 254),
        ("threaded fill\nopening", "thread", 224),
        ("plain reservoir:\nØ 25 mm tube,\nØ 21 mm bore", "reservoir", 165),
        ("44-tooth gear\n(driven by stepper)", "gear", 104),
        ("Ø 8 mm core", "core", 70),
        ("single-start flight,\n10.4 mm pitch", "flight", 45),
        ("tapered outlet,\nØ 3 mm exit hole", "outlet", 10),
    ]
    for text, key, z_label in callouts:
        ax.annotate(text, xy=anchor[key], xytext=(xt, px(0, z_label)[1]),
                    fontsize=4.9, ha="left", va="center", zorder=3,
                    arrowprops=dict(arrowstyle="-", lw=0.45, color="0.3",
                                    shrinkA=1.5, shrinkB=0))
        ax.plot(*anchor[key], "o", ms=1.0, color="0.15", zorder=4)
    # dimension lines in the cut plane: the whole tube and the flighted end
    for z1, xd, text in ((250.0, -40.0, "250 mm"), (83.3, -28.0, "83 mm")):
        p0, p1 = px(xd, 0.0), px(xd, z1)
        ax.annotate("", xy=p1, xytext=p0,
                    arrowprops=dict(arrowstyle="<|-|>", lw=0.5, color="0.2",
                                    mutation_scale=4, shrinkA=0, shrinkB=0))
        ax.text(*(0.5 * (p0 + p1) - (1.2 * s, 0)), text, rotation=90,
                fontsize=4.8, ha="right", va="center")
        for z in (0.0, z1):                        # extension lines
            ax.plot(*np.c_[px(-12.5, z), px(xd - 2.5, z)], color="0.55",
                    lw=0.3, zorder=0)
    x0, y0 = px(0, 0)
    ax.set_xlim(x0 - 68 * s, x0 + 100 * s)
    ax.set_ylim(y0 + 10 * s, y0 - 292 * s)
    ax.set_aspect("equal")
    ax.set_axis_off()


def fig1() -> None:
    fig = plt.figure(figsize=(DOUBLE_COL_IN, 4.75))
    outer = fig.add_gridspec(2, 1, height_ratios=[1.12, 1.0], hspace=0.06)
    top = outer[0].subgridspec(1, 2, wspace=0.04)
    bottom = outer[1].subgridspec(1, 3, width_ratios=[0.95, 1.05, 1.0],
                                  wspace=0.12)

    # (a) annotated CAD render of the current design (PR #170, commit
    #     ce256c3: same camera as the June render in issue #165, with every
    #     printed part from the team's Fusion 360 files except the AI-modelled
    #     tap-collar base) and (b) the as-built module (issue #165; frame at
    #     t = 65 s of the first automated dispense, in the University of Utah
    #     glove box, issue #117)
    ax = fig.add_subplot(top[0, 0])
    show(ax, "cad_render_current_annotated.png")
    panel_label(ax, "a")
    ax = fig.add_subplot(top[0, 1])
    show(ax, "as_built_first_dispense.jpg", crop_white=False)
    panel_label(ax, "b")

    # (c) 3-D cut-away of the tested auger and cap: the tube is its own
    #     reservoir, filled through the capped end; the flight occupies only
    #     the outlet third, and the 44-tooth gear sits on the outside.
    ax = fig.add_subplot(bottom[0, 0])
    auger_cutaway(ax)
    panel_label(ax, "c")

    # (d) tilt range (0-45 deg) about the hinge just behind the outlet
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
        (5.8, 0.9, "Analytical\nbalance"),
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


# ----------------------------------------------------------------------------
# Figures S1 and S2 — exploded view and build steps of the current design
# ----------------------------------------------------------------------------
# Build steps of cad/full-assembly/BOM.md (PR #170); bracketed numbers are the
# item numbers of the exploded view (Fig. S1).
ASSEMBLY_STEPS = [
    "Baseplate onto the board [1, 2]",
    "Screws into the board [3]",
    "Servos into the posts [4]",
    "Servo screws and nuts [5, 6]",
    "Servo pinions [7, 8]",
    "Mounting plate on the hinge [9]",
    "Hinge screws and nuts [10, 11]",
    "Stepper [12, 13]",
    "Stepper pinion [14]",
    "Tap-collar base [6, 15–18]",
    "Auger over the plate [19]",
    "Front bracket on the tube [20]",
    "Tap collar on the tube [21]",
    "Auger onto the plate [19–21]",
    "Rear bracket on the tube [20]",
    "Bracket screws and clamps [5, 6, 22]",
    "Tap-collar clamp [6, 22]",
    "Solenoid [23, 24]",
    "Auger cap [25]",
]


def figs_assembly_exploded() -> None:
    """Exploded view of the current design with every BOM item numbered.

    Rendered by PR #170 (cad/full-assembly/renders/assembly_exploded_bom.png,
    commit ce256c3) from the team's Fusion 360 parts, the AI-modelled
    tap-collar base, datasheet models of the purchased parts and McMaster-Carr
    fasteners; the table on the right is its bill of materials.
    """
    img = load("assembly_exploded_bom.png")
    h, w = img.shape[:2]
    fig = plt.figure(figsize=(DOUBLE_COL_IN, DOUBLE_COL_IN * h / w))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.imshow(img)
    ax.set_axis_off()
    _save(fig, "figS_assembly_exploded")
    plt.close(fig)


def figs_assembly_steps() -> None:
    """The 19 build steps as stills from the PR #170 assembly animation.

    Stills are the end of each step in assembly_walkthrough.gif, extracted by
    data/extract_assembly_steps.py into assets/assembly_steps/.
    """
    ncol, nrow = 4, 5
    aspect = 1.6                       # every still padded to this width/height
    fig, axes = plt.subplots(nrow, ncol, figsize=(DOUBLE_COL_IN, 6.0),
                             gridspec_kw=dict(hspace=0.30, wspace=0.08))
    for k, ax in enumerate(axes.flat):
        ax.set_axis_off()
        if k < len(ASSEMBLY_STEPS):
            img = load(f"assembly_steps/step{k + 1:02d}.png")
            h, w = img.shape[:2]
            H, W = max(h, int(round(w / aspect))), max(w, int(round(h * aspect)))
            canvas = np.full((H, W, 3), 255, dtype=np.uint8)
            r0, c0 = (H - h) // 2, (W - w) // 2
            canvas[r0:r0 + h, c0:c0 + w] = img
            ax.imshow(canvas)
            ax.set_title(f"{k + 1}. {ASSEMBLY_STEPS[k]}", fontsize=5.3,
                         loc="left", pad=2.0)
        else:
            ax.text(0.04, 0.6,
                    "Numbers in brackets are the\n"
                    "item numbers in Fig. S1.",
                    fontsize=5.6, ha="left", va="center", color="0.25",
                    transform=ax.transAxes)
    _save(fig, "figS_assembly_steps")
    plt.close(fig)


if __name__ == "__main__":
    for fn in (fig1, fig2, fig6, figs1, figs_assembly_exploded,
               figs_assembly_steps):
        fn()
        print(f"wrote {fn.__name__}")
