#!/usr/bin/env python3
"""SI Fig. S1 (v2): the generative-CAD comparison, as images.

From the 27 Oct whiteboard ("Generative CAD comparisons: tap collar, Zoo
comparison, CADSmith, mounting plate gap", blue = SI) and the meeting (15:50-
17:05): the tool comparison is text in the main paper, and its images go in the
SI.  Rows:

    (a-c) one prompt, three tools: the issue #104 prompt (22 Jun 2026) given to
          the GitHub Copilot coding agent (PR #107), CADSmith (fork
          vertical-cloud-lab/CADSmith PR #6) and the Zoo Text-to-CAD API
          (PR #110); all three rendered from the same viewpoint (az 090).
    (d-f) the tap collar: the coding agent's first collar, its collar after
          review, and the Zoo Design Studio collar (Zookeeper, third
          iteration; STL attached to issue #104).
    (g-l) plates: CADSmith's mounting plate and baseplate, and the coding
          agent's four mounting-plate iterations (the gap case, PR #57).

Sources: assets/cadcompare/SOURCES.json, assets/timeline/SOURCES.json.

Usage:  python3 make_si_cad_comparison.py
"""

from __future__ import annotations

import re
import zipfile
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from PIL import Image

HERE = Path(__file__).resolve().parent
CMP = HERE / "assets" / "cadcompare"
TL = HERE / "assets" / "timeline"
OLD = HERE.parent / "figures" / "assets"
FIGS, PREVIEW = HERE / "figures", HERE / "preview"
INK, INK2 = "#0b0b0b", "#52514e"
EDGE = {"copilot": "#4a3aa7", "cadsmith": "#c98500", "zoo": "#0f8fb8"}
W_IN = 17.1 / 2.54
plt.rcParams.update({"font.size": 6.0, "font.family": "sans-serif", "savefig.dpi": 600})

STL_ZIP = Path("/tmp/zoo_tc/tc3.zip")   # issue #104 attachment, see SOURCES.json


def render_zoo_tap_collar() -> None:
    """Shade the Zoo Design Studio tap-collar STL once, into assets/."""
    out = CMP / "zoo_tap_collar.png"
    if out.exists():
        return
    raw = zipfile.ZipFile(STL_ZIP).read("tap collar 3.stl").decode("ascii", "replace")
    v = np.array(re.findall(r"vertex\s+(\S+)\s+(\S+)\s+(\S+)", raw), float)
    tris = v.reshape(-1, 3, 3)
    n = np.cross(tris[:, 1] - tris[:, 0], tris[:, 2] - tris[:, 0])
    n /= np.linalg.norm(n, axis=1, keepdims=True) + 1e-12
    light = np.array([0.4, -0.6, 0.7]) / np.linalg.norm([0.4, -0.6, 0.7])
    shade = 0.35 + 0.65 * np.clip(np.abs(n @ light), 0, 1)
    base = np.array([0.80, 0.66, 0.45])
    fig = plt.figure(figsize=(4, 4))
    ax = fig.add_subplot(projection="3d")
    ax.add_collection3d(Poly3DCollection(tris, facecolors=shade[:, None] * base,
                                         edgecolor="none"))
    lo, hi = tris.min(axis=(0, 1)), tris.max(axis=(0, 1))
    c, r = (lo + hi) / 2, (hi - lo).max() / 2
    ax.set_xlim(c[0] - r, c[0] + r), ax.set_ylim(c[1] - r, c[1] + r)
    ax.set_zlim(c[2] - r, c[2] + r)
    ax.set_box_aspect((1, 1, 1))
    ax.view_init(elev=22, azim=-58)
    ax.set_axis_off()
    fig.savefig(out, dpi=300, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def img(path: Path, frac=None) -> np.ndarray:
    a = np.asarray(Image.open(path).convert("RGB")).astype(float) / 255
    if frac:
        h, w = a.shape[:2]
        a = a[int(frac[1] * h):int(frac[3] * h), int(frac[0] * w):int(frac[2] * w)]
    if a.mean() < 0.35:
        a = 1 - a
    bg = a[0, 0]
    mask = np.abs(a - bg).sum(axis=2) > 0.08
    if mask.any():
        ys, xs = np.where(mask)
        a = a[max(ys.min() - 8, 0):ys.max() + 8, max(xs.min() - 8, 0):xs.max() + 8]
    return a


ROWS = [
    ("One prompt, three tools: the whole doser (issue #104 prompt, 22 Jun 2026)", [
        (CMP / "prompt104_copilot.png", None, "GitHub Copilot coding agent\nClaude Opus 4.8 (PR #107)", "copilot"),
        (CMP / "prompt104_cadsmith.png", None, "CADSmith\nClaude Opus 4.5 (CADSmith PR #6)", "cadsmith"),
        (CMP / "prompt104_zoo.png", (0.1, 0.18, 0.92, 0.82), "Zoo Text-to-CAD API\n'kcl' model (PR #110)", "zoo"),
    ]),
    ("Tap collar", [
        (TL / "ai_tap_collar_v1.png", None, "Coding agent, first collar\n15 May (PR #51)", "copilot"),
        (TL / "ai_tap_collar_revised.png", None, "Coding agent, after review\nby 10 Jun (PR #51)", "copilot"),
        (CMP / "zoo_tap_collar.png", None, "Zoo Design Studio, Zookeeper\nthird iteration, 12 Jun", "zoo"),
    ]),
    ("Mounting plate and baseplate", [
        (CMP / "cadsmith_mounting_plate.png", (0, 0, 0.34, 1), "CADSmith\nmounting plate", "cadsmith"),
        (CMP / "cadsmith_baseplate.png", (0, 0, 0.34, 1), "CADSmith\nbaseplate", "cadsmith"),
        (OLD / "plate_iter1_hole_top.png", None, "Coding agent, iter. 1:\nunexplained hole", "copilot"),
        (OLD / "plate_iter2_platforms_iso.png", None, "Iter. 2: raised\nplatforms", "copilot"),
        (OLD / "plate_iter3_gap_top.png", None, "Iter. 3: gap,\nmotor plate floats", "copilot"),
        (OLD / "plate_iter4_final_top.png", None, "Iter. 4: correct\ninputs, clean plate", "copilot"),
    ]),
]


def figS_cad_comparison() -> None:
    render_zoo_tap_collar()
    fig = plt.figure(figsize=(W_IN, 6.0))
    heights = [0.30, 0.23, 0.21]
    tops = [0.955, 0.60, 0.255]
    letters = iter("abcdefghijkl")
    for (title, items), h, top in zip(ROWS, heights, tops):
        fig.text(0.0, top + 0.03, title, fontsize=6.6, fontweight="bold", va="bottom")
        n = len(items)
        gap = 0.012
        w = (1 - gap * (n - 1)) / n
        for j, (path, frac, cap, tool) in enumerate(items):
            ax = fig.add_axes([j * (w + gap), top - h, w, h])
            ax.imshow(img(path, frac))
            ax.set_xticks([]), ax.set_yticks([])
            for s in ax.spines.values():
                s.set_edgecolor(EDGE[tool]), s.set_linewidth(0.9)
            ax.text(0.5, -0.02, cap, transform=ax.transAxes, ha="center", va="top",
                    fontsize=5.2, color=INK, linespacing=1.12)
            ax.text(0.02, 0.98, f"({next(letters)})", transform=ax.transAxes,
                    fontsize=7, fontweight="bold", va="top",
                    bbox=dict(fc="white", ec="none", alpha=0.8, pad=0.6))
    FIGS.mkdir(exist_ok=True), PREVIEW.mkdir(exist_ok=True)
    fig.savefig(FIGS / "figS_cad_comparison.pdf")
    # the PNG preview is rendered from the compiled LaTeX by build_figures.py
    plt.close(fig)
    print("wrote figS_cad_comparison")


if __name__ == "__main__":
    figS_cad_comparison()
