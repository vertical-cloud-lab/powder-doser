#!/usr/bin/env python3
"""Generate all manuscript figures for the powder-doser base paper.

Real CAD renders are pulled from paper/figures/assets/ (extracted from the
design branches of this repository).  Every panel reflects work already
completed; the manuscript reports no synthetic or placeholder data.

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


def check_text_overlaps(fig, name: str, pad: float = 1.0) -> list:
    """Report text that is overlapped or crossed by another artist.

    Computes the rendered window extent (display-pixel bounding box) of every
    visible text artist---panel labels, annotation callouts, axis titles---and
    flags (a) any pair of labels whose boxes intersect and (b) any annotation
    *leader line* that passes through a label other than its own anchor.  The
    second check guarantees that no callout text is obscured by a line running
    through it.  Returns the list of offending pairs (empty when clean).
    """
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    items = []
    annotations = []  # (owner_text, (x0,y0), (x1,y1)) leader segments in display px
    for ax in fig.axes:
        artists = list(ax.texts)
        if ax.get_title():
            artists.append(ax.title)
        for t in artists:
            if not t.get_text().strip():
                continue
            try:
                bb = t.get_window_extent(renderer=renderer)
            except Exception:
                continue
            bb = bb.expanded(1.0 + pad / max(bb.width, 1.0), 1.0 + pad / max(bb.height, 1.0))
            label = t.get_text().replace("\n", " ")
            items.append((label, bb))
            # capture the leader line of annotations (text -> target)
            arrow = getattr(t, "arrow_patch", None)
            if arrow is not None and getattr(t, "xy", None) is not None:
                try:
                    target = ax.transData.transform(t.xy)
                    src = ((bb.x0 + bb.x1) / 2.0, (bb.y0 + bb.y1) / 2.0)
                    annotations.append((label, bb, src, tuple(target)))
                except Exception:
                    pass
    bad = []
    for i in range(len(items)):
        for j in range(i + 1, len(items)):
            if items[i][1].overlaps(items[j][1]):
                bad.append((items[i][0], items[j][0]))
    # leader-line-through-text check: sample each leader and test every other
    # label's box; the segment naturally touches its own box, which is excluded.
    samples = 24  # number of points sampled along each leader line
    for owner, owner_bb, (x0, y0), (x1, y1) in annotations:
        for steps in range(1, samples):
            s = steps / float(samples)
            px, py = x0 + (x1 - x0) * s, y0 + (y1 - y0) * s
            for label, bb in items:
                if label == owner:
                    continue
                if bb.x0 <= px <= bb.x1 and bb.y0 <= py <= bb.y1:
                    pair = (owner, f"leader through {label!r}")
                    if pair not in bad:
                        bad.append(pair)
    for a, b in bad:
        print(f"  [overlap] {name}: {a!r} <-> {b!r}")
    return bad


def save(fig, name: str) -> None:
    overlaps = check_text_overlaps(fig, name)
    fig.savefig(HERE / f"{name}.pdf", bbox_inches="tight")
    plt.close(fig)
    if overlaps:
        raise SystemExit(f"text overlaps detected in {name}; fix label placement")


# ----------------------------------------------------------------------------
# Figure 1 — platform overview
# ----------------------------------------------------------------------------
def fig1() -> None:
    fig = plt.figure(figsize=(DOUBLE_COL_IN, 4.8))
    gs = fig.add_gridspec(2, 3, height_ratios=[1.4, 1.0], hspace=0.32, wspace=0.18)

    # (a) annotated final single-channel assembly render.  The render fills the
    #     whole frame, so a band of white headroom is added above (and a margin
    #     below) the image and every callout label is placed in that clear space
    #     with a leader line pointing into the part---no text sits on top of the
    #     busy render or has a leader line running through it.
    ax = fig.add_subplot(gs[0, :2])
    img = load("assembly_iso_final.png")
    ax.imshow(img)
    ax.set_axis_off()
    h, w = img.shape[:2]
    # Margins are sized to fit the longest label (the two-line stepper callout)
    # in clear space beside the render without overlapping it.
    left = 0.30 * w  # white margin left of the render (for left-hand labels)
    right = 0.46 * w  # white margin right of the render (for right-hand labels)
    ax.set_xlim(-0.5 - left, w - 0.5 + right)
    ax.set_ylim(h - 0.5, -0.5)
    panel_label(ax, "a")
    # Labels live in the white side margins (never on top of the render) and
    # their leader lines run horizontally into the part, so no text is crossed by
    # a leader line or obscured by the model.  Left-hand labels are right-aligned
    # against the render; right-hand labels are left-aligned; they are spread
    # vertically so none collide.
    # (text, part target frac, label anchor frac, ha, va)
    callouts = [
        ("Archimedes auger\n(printed, geared)", (0.16, 0.50), (-0.03, 0.30), "right", "center"),
        ("Baseplate", (0.22, 0.82), (-0.03, 0.86), "right", "center"),
        ("NEMA-11 stepper +\nprinted spur-gear drive", (0.70, 0.42), (1.03, 0.20), "left", "center"),
        ("Auger bracket +\ntap collar", (0.50, 0.50), (1.03, 0.54), "left", "center"),
        ("Hinged plate (servo tilt)", (0.64, 0.64), (1.03, 0.86), "left", "center"),
    ]
    for text, (xt, yt), (xl, yl), ha, va in callouts:
        ax.annotate(
            text,
            xy=(xt * w, yt * h),
            xytext=(xl * w, yl * h),
            fontsize=5.5,
            ha=ha,
            va=va,
            arrowprops=dict(arrowstyle="-", lw=0.6, color="0.25"),
        )

    # (b) powder-flow path through the module (tall panel), drawn to match the
    #     final no-hopper design: the auger tube itself is the reservoir, loaded
    #     through slots; dispensed mass lands in a cup on the analytical balance.
    ax = fig.add_subplot(gs[0, 2])
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10)
    ax.set_aspect("auto")
    ax.set_axis_off()
    panel_label(ax, "b")
    ax.set_title("Powder-flow path (schematic)", fontsize=6)

    tube_x0, tube_x1 = 4.0, 6.0
    tube_y0, tube_y1 = 2.6, 9.0
    # auger tube body = powder reservoir
    ax.add_patch(
        patches.Rectangle(
            (tube_x0, tube_y0),
            tube_x1 - tube_x0,
            tube_y1 - tube_y0,
            fc="#f3e6c8",
            ec="0.3",
            lw=0.8,
        )
    )
    # helical auger flight inside the tube
    ty = np.linspace(tube_y0 + 0.3, tube_y1 - 0.3, 240)
    tx = 5.0 + 0.7 * np.sin((ty - tube_y0) * 3.0)
    ax.plot(tx, ty, color="#b6862c", lw=0.9)
    # loading slots near the top of the tube wall
    for sy in (tube_y1 - 0.6, tube_y1 - 1.2):
        ax.add_patch(patches.Rectangle((tube_x0 - 0.02, sy), 0.5, 0.18, fc="white", ec="0.3", lw=0.6))
        ax.add_patch(patches.Rectangle((tube_x1 - 0.48, sy), 0.5, 0.18, fc="white", ec="0.3", lw=0.6))
    # exit nozzle protruding below the tube
    ax.add_patch(patches.Polygon([(4.55, tube_y0), (5.45, tube_y0), (5.2, tube_y0 - 0.7), (4.8, tube_y0 - 0.7)], closed=True, fc="#f3e6c8", ec="0.3", lw=0.7))
    # falling dose
    for k, dy in enumerate(np.linspace(tube_y0 - 0.9, 1.4, 6)):
        ax.plot(5.0, dy, ".", ms=2.0, color="#b6862c")
    # collection cup on the balance
    ax.add_patch(patches.Polygon([(3.9, 1.3), (6.1, 1.3), (5.8, 0.4), (4.2, 0.4)], closed=True, fc="#fbf3df", ec="0.3", lw=0.7))
    ax.add_patch(patches.Rectangle((3.2, 0.05), 3.6, 0.3, fc="#dfe6ef", ec="0.3", lw=0.7))
    callouts_b = [
        ("auger tube = reservoir\n(loaded through slots,\nno separate hopper)", (5.4, tube_y1 - 0.9), (6.3, tube_y1 - 0.4)),
        ("step-counted\nArchimedes auger", (5.4, 6.0), (6.4, 6.0)),
        ("exit nozzle", (5.2, tube_y0 - 0.45), (6.4, tube_y0 - 0.2)),
        ("cup on balance\n(A&D HR-100A)", (5.6, 0.7), (6.4, 1.0)),
    ]
    for text, (xt, yt), (xl, yl) in callouts_b:
        ax.annotate(
            text,
            xy=(xt, yt),
            xytext=(xl, yl),
            fontsize=4.6,
            ha="left",
            va="center",
            arrowprops=dict(arrowstyle="-", lw=0.5, color="0.35"),
        )

    # (c) tilt sweep about the fixed dispense point
    ax = fig.add_subplot(gs[1, 0])
    img = load("rotation_0_45_90.png")
    img = img[int(img.shape[0] * 0.10):, :]  # trim internal suptitle
    ax.imshow(img)
    ax.set_axis_off()
    panel_label(ax, "c")
    ax.set_title("Tilt sweep about fixed dispense point", fontsize=6)

    # (d) closed-loop dosing concept diagram: the target mass enters the
    #     controller, which drives the actuation; the balance feeds measured
    #     mass back to the controller.
    ax = fig.add_subplot(gs[1, 1])
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 11.2)
    ax.set_axis_off()
    panel_label(ax, "d")
    ax.set_title("Closed-loop gravimetric dosing", fontsize=6)
    boxes = [
        (0.7, 7.7, "Dose request\n(target mass)"),
        (0.7, 4.2, "Controller\n(coarse \u2192 trickle)"),
        (5.9, 4.2, "Auger + tap +\nvibration actuation"),
        (5.9, 0.9, "Balance reading\n(A&D HR-100A, RS-232)"),
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
        ax.text(x + 1.6, y + 0.95, label, ha="center", va="center", fontsize=5.2)
    arrow = dict(arrowstyle="->", lw=0.8, color="0.2")
    # target mass into the controller
    ax.annotate("", xy=(2.3, 6.1), xytext=(2.3, 7.7), arrowprops=arrow)
    # controller commands the actuation
    ax.annotate("", xy=(5.9, 5.15), xytext=(3.9, 5.15), arrowprops=arrow)
    # actuation dispenses onto the balance
    ax.annotate("", xy=(7.5, 2.8), xytext=(7.5, 4.2), arrowprops=arrow)
    # measured mass fed back to the controller
    ax.annotate("", xy=(3.9, 4.3), xytext=(5.9, 1.85), arrowprops=arrow)

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

    save(fig, "fig1_overview")


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
    save(fig, "fig2_genai")


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
    ax.set_title("Tap collar split clamp\n(actuator mount)", fontsize=6)

    save(fig, "fig4_design")


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
    ax.set_title("8-channel radial array\n(concept)", fontsize=6)

    # (b) inward-tilting collection-cup render
    ax = fig.add_subplot(gs[0, 1])
    show(ax, "inward_collection_cup_iso.png")
    panel_label(ax, "b")
    ax.set_title("Inward-tilting channels\nover shared cup\n(preliminary CAD)", fontsize=6)

    save(fig, "fig5_future")


# ----------------------------------------------------------------------------
# Figure S1 — exit-nozzle variants
# ----------------------------------------------------------------------------
def figs1() -> None:
    fig, axs = plt.subplots(1, 4, figsize=(DOUBLE_COL_IN, 2.4))
    for k, ax in enumerate(axs, start=1):
        show(ax, f"nozzle_type{k}_cross_section.png")
        panel_label(ax, "abcd"[k - 1])
        ax.set_title(f"Type {k}", fontsize=7)
    save(fig, "figS1_nozzles")


if __name__ == "__main__":
    for fn in (fig1, fig2, fig4, fig5, figs1):
        fn()
        print(f"wrote {fn.__name__}")
