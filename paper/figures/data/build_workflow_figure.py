#!/usr/bin/env python3
"""SI figure figS_workflow: the AI-CAD loop used for the printed parts.

Panel (a) is a real input drawing, saved unchanged as
``assets/example_drawing.png``: the annotated sketch of the auger bracket that
a team member attached to issue #46 on 14 May 2026, the first request of the
part-by-part approach (source:
https://github.com/user-attachments/assets/1a930d05-5ea2-4926-89d7-ec49aea76abb).
The GitHub Copilot coding agent modelled it in CadQuery in PR #47.  The same
image, pixel for pixel, was posted again for the zoo.dev and CADSmith trials
(issues #52 and #54, 15 May 2026).

Panel (b) is drawn here from the repository record:

  1  request as a GitHub issue      issue #46 (sketch), #48, #50, #62, #65
  2  agent writes parametric code   CadQuery or OpenSCAD (PRs #47, #49, #51)
  3  renders, STL/STEP, checks      scripts run in the agent's GitHub Actions
                                    session: one manifold solid (PRs #49, #53,
                                    #55), overlap checks (PR #66), as asked in
                                    issue #65 and the PR #35 review
  4  pull request                   one per part, updated by each session
  5  team review of the renders     e.g. PR #51, #57 and #68 reviews
  6-7 print, fit, bench test        #46 and #72 photos; PR #49 comment
                                    4460165741 ("the gears fit together")
  8  freeze                         e.g. Auger4.stl committed as the main design
                                    (11ed351, after the #48 bench test)
  Zoo Design Studio variant         #92, discussion #39 (12 Jun 2026), servo
                                    pinion transcript (PR #66), tap collar 3
                                    files (#104, PR #105)

Usage:  python3 build_workflow_figure.py
        (writes ../figS_workflow.pdf and ../preview/figS_workflow.png)
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.lines import Line2D
from matplotlib.patches import FancyBboxPatch, Patch
from PIL import Image

HERE = Path(__file__).resolve().parent
FIG_DIR = HERE.parent
DRAWING = FIG_DIR / "assets" / "example_drawing.png"

MM = 1 / 25.4
FIG_W_MM, FIG_H_MM = 166.0, 92.0   # SI text width; about 40% of the text height

INK, INK2 = "#0b0b0b", "#52514e"
EDGE = "#6f6e69"
ARROW = "#3a3936"
AI_FILL = "#dfeafa"     # tint of categorical slot 1 (blue), as in the data figures
TEAM_FILL = "#fde3d6"   # tint of categorical slot 2 (orange)

plt.rcParams.update({
    "font.size": 6.5,
    "font.family": "sans-serif",
    "savefig.dpi": 600,
})

BOX_FS = 6.2
LABEL_FS = 5.7


def load_drawing(path: Path) -> np.ndarray:
    """The sketch on white, cropped to its ink with a small margin."""
    img = Image.open(path).convert("RGBA")
    white = Image.new("RGBA", img.size, (255, 255, 255, 255))
    arr = np.asarray(Image.alpha_composite(white, img).convert("RGB"))
    ink = (arr < 235).any(axis=2)
    rows, cols = np.flatnonzero(ink.any(axis=1)), np.flatnonzero(ink.any(axis=0))
    pad = 14
    r0, r1 = max(rows[0] - pad, 0), min(rows[-1] + pad, arr.shape[0])
    c0, c1 = max(cols[0] - pad, 0), min(cols[-1] + pad, arr.shape[1])
    return arr[r0:r1, c0:c1]


def panel_label(fig, x_mm: float, y_mm: float, letter: str) -> None:
    fig.text(x_mm / FIG_W_MM, y_mm / FIG_H_MM, f"({letter})", fontsize=8,
             fontweight="bold", ha="left", va="top")


def box(ax, x, y, w, h, lines, role, number=None):
    """Rounded step box; text in ink, fill by who did the step."""
    fill = AI_FILL if role == "ai" else TEAM_FILL
    ax.add_patch(FancyBboxPatch((x, y), w, h,
                                boxstyle="round,pad=0,rounding_size=1.3",
                                fc=fill, ec=EDGE, lw=0.6, zorder=2))
    tx = x + 2.0
    if number is not None:
        ax.text(x + 2.0, y + h / 2, str(number), ha="left", va="center",
                fontsize=BOX_FS + 0.6, fontweight="bold", color=INK, zorder=3)
        tx = x + 6.0
    ax.text(tx, y + h / 2, "\n".join(lines), ha="left", va="center",
            fontsize=BOX_FS, color=INK, linespacing=1.3, zorder=3)


def arrow(ax, pts, lw=0.75):
    """Polyline through pts with an arrowhead on the last segment."""
    pts = np.asarray(pts, dtype=float)
    if len(pts) > 2:
        ax.add_line(Line2D(pts[:-1, 0], pts[:-1, 1], lw=lw, color=ARROW,
                           solid_joinstyle="miter", solid_capstyle="butt",
                           zorder=1))
    ax.annotate("", xy=pts[-1], xytext=pts[-2],
                arrowprops=dict(arrowstyle="-|>", lw=lw, color=ARROW,
                                mutation_scale=6.5, shrinkA=0, shrinkB=0),
                zorder=1)


def label(ax, x, y, text, **kw):
    kw.setdefault("ha", "left")
    kw.setdefault("va", "center")
    ax.text(x, y, text, fontsize=LABEL_FS, color=INK2, style="italic", **kw)


def draw_flow(ax) -> None:
    ax.set_xlim(0, 110)
    ax.set_ylim(0, 90)
    ax.set_axis_off()

    # main column: steps 1-8 top to bottom
    x0, w, h, gap, top = 20.0, 54.0, 7.4, 3.5, 86.0
    steps = [
        (["Request in a GitHub issue: written",
          "specification or annotated drawing"], "team"),
        (["Coding agent writes the part as",
          "parametric code (CadQuery, OpenSCAD)"], "ai"),
        (["Agent's scripts render views, export",
          "STL and STEP files, and run checks"], "ai"),
        (["Agent opens or updates the pull request"], "ai"),
        (["Team reviews the renders and files",
          "in the pull request"], "team"),
        (["Team prints the part in PLA"], "team"),
        (["Team fits it to the neighbouring parts",
          "and tests it on the doser"], "team"),
        (["Team freezes the geometry"], "team"),
    ]
    ys = [top - h - i * (h + gap) for i in range(len(steps))]
    for i, ((lines, role), y) in enumerate(zip(steps, ys)):
        box(ax, x0, y, w, h, lines, role, number=i + 1)
    cx = x0 + w / 2
    for i in range(len(steps) - 1):
        arrow(ax, [(cx, ys[i]), (cx, ys[i + 1] + h)])
    label(ax, cx + 1.5, ys[4] - gap / 2, "accept")
    label(ax, cx + 1.5, ys[6] - gap / 2, "fits and works")

    # inner loop: review comment back to the agent (5 -> 2)
    xi = 13.0
    y5, y2 = ys[4] + h / 2, ys[1] + h / 2
    arrow(ax, [(x0, y5), (xi, y5), (xi, y2), (x0, y2)])
    label(ax, xi - 1.0, (y5 + y2) / 2, "revise: comment in the PR",
          rotation=90, ha="right")

    # outer loop: problem at the bench back to a new request (7 -> 1)
    xo = 4.5
    y7, y1 = ys[6] + h / 2, ys[0] + h / 2
    arrow(ax, [(x0, y7), (xo, y7), (xo, y1), (x0, y1)])
    label(ax, xo - 1.0, (y7 + y1) / 2, "problem at the bench: new comment or issue",
          rotation=90, ha="right")

    # Zoo Design Studio variant: 1 -> chat with Zookeeper -> export -> 6
    zx, zw = 79.0, 29.5
    zc = zx + zw / 2
    z1_h, z2_h = 14.5, 11.0
    z1_y = ys[2] + h - z1_h + 1.0
    z2_y = ys[4] - 1.0
    box(ax, zx, z1_y, zw, z1_h, ["Team member chats", "with Zookeeper, which",
                                 "models the part in KCL", "in a live CAD view"], "ai")
    box(ax, zx, z2_y, zw, z2_h, ["Team inspects the", "model and exports",
                                 "STEP or STL files"], "team")
    arrow(ax, [(x0 + w, y1), (zc, y1), (zc, z1_y + z1_h)])
    label(ax, zc, y1 + 1.6, "Zoo Design Studio variant", ha="center", va="bottom")
    arrow(ax, [(zc, z1_y), (zc, z2_y + z2_h)])
    y6 = ys[5] + h / 2
    arrow(ax, [(zc, z2_y), (zc, y6), (x0 + w, y6)])

    # who did each step
    handles = [Patch(fc=TEAM_FILL, ec=EDGE, lw=0.6, label="Team"),
               Patch(fc=AI_FILL, ec=EDGE, lw=0.6, label="AI tool")]
    ax.legend(handles=handles, loc="lower right", bbox_to_anchor=(0.99, 0.0),
              frameon=False, fontsize=BOX_FS, handlelength=1.6, handleheight=1.1,
              borderaxespad=0.2, labelcolor=INK)


def main() -> None:
    fig = plt.figure(figsize=(FIG_W_MM * MM, FIG_H_MM * MM))

    img = load_drawing(DRAWING)
    a_h = 86.0
    a_w = a_h * img.shape[1] / img.shape[0]
    ax_a = fig.add_axes([1.0 / FIG_W_MM, 1.0 / FIG_H_MM,
                         a_w / FIG_W_MM, a_h / FIG_H_MM])
    ax_a.imshow(img, interpolation="antialiased")
    ax_a.set_axis_off()
    # thin frame so the white sketch reads as an inserted image
    ax_a.add_patch(plt.Rectangle((0, 0), 1, 1, transform=ax_a.transAxes,
                                 fill=False, ec=EDGE, lw=0.5))

    b_left = FIG_W_MM - 110.0
    ax_b = fig.add_axes([b_left / FIG_W_MM, 0.0, 110.0 / FIG_W_MM, 90.0 / FIG_H_MM])
    draw_flow(ax_b)

    panel_label(fig, 1.0, FIG_H_MM - 0.5, "a")
    panel_label(fig, b_left, FIG_H_MM - 0.5, "b")

    fig.savefig(FIG_DIR / "figS_workflow.pdf")
    (FIG_DIR / "preview").mkdir(exist_ok=True)
    fig.savefig(FIG_DIR / "preview" / "figS_workflow.png", dpi=220,
                facecolor="white")
    plt.close(fig)
    print(f"panel (a) {a_w:.1f} x {a_h:.1f} mm; wrote figS_workflow.pdf and preview")


if __name__ == "__main__":
    main()
