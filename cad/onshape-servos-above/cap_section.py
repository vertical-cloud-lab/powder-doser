"""Section of the auger cap through its axis, with the by-hand recipe's groove sketch (step 6) on top.

    fsgen studio build parts/auger_cap.fs        # writes out/auger_cap/auger_cap.step (0 calls)
    python cap_section.py                         # -> renders/local/auger_cap_section.png

The section is of fsgen's build of parts/auger_cap.fs (its STL, cut with trimesh: OpenCascade's own section of
the helical faces comes back in open pieces), through the Front (XZ) plane. The orange outline is the recipe's
step 6 sketch (recipe_check.py): it sits at the helix start, below the rim, where the sweep begins.
"""
from __future__ import annotations

from pathlib import Path

import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import trimesh  # noqa: E402
from build123d import fillet  # noqa: E402

from recipe_check import CORNERS, FILLET, Z_PLANE, R_OUT, front  # noqa: E402

HERE = Path(__file__).resolve().parent
SURFACE, INK, INK2, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#d9d8d4"
CAP, SKETCH = "#2a78d6", "#eb6834"


def edges_xy(shape, n=60):
    for e in shape.edges():
        pts = [e @ t for t in np.linspace(0, 1, n)]
        yield [p.X for p in pts], [p.Z for p in pts]


def main() -> None:
    mesh = trimesh.load(HERE / "out" / "auger_cap" / "auger_cap.stl")
    loops = mesh.section(plane_origin=[0, 0, 0], plane_normal=[0, 1, 0]).discrete
    if len(loops) != 1:     # the cut is one region (the grooves open into the bore), so one closed loop
        raise SystemExit(f"expected one closed loop in the section, got {len(loops)}")
    fig, ax = plt.subplots(figsize=(8.2, 7.4), dpi=150)
    fig.patch.set_facecolor(SURFACE)
    ax.set_facecolor(SURFACE)
    xz = loops[0][:, [0, 2]]
    ax.fill(xz[:, 0], xz[:, 1], color=CAP, alpha=0.85, lw=0)
    ax.plot(xz[:, 0], xz[:, 1], color=INK, lw=0.8)
    ax.axvline(0, color=INK2, lw=0.8, ls=(0, (8, 3, 2, 3)))
    ax.axhline(Z_PLANE, color=INK2, lw=0.8, ls=(0, (3, 3)))
    ax.text(-14.3, Z_PLANE + 0.35, "thread plane, z = −28.4 (helix start)", color=INK2, fontsize=8.5)
    # recipe step 6: trapezoid A-B-C-D with 1 mm fillets at B and C
    trap = front([CORNERS[k] for k in "ABCD"])
    prof = fillet([v for v in trap.vertices() if abs(v.X - R_OUT) < 1e-6], radius=FILLET)
    for x, z in edges_xy(prof):
        ax.plot(x, z, color=SKETCH, lw=2)
    xs = [CORNERS[k][0] for k in "ABCDA"]
    zs = [CORNERS[k][1] for k in "ABCDA"]
    ax.plot(xs, zs, color=SKETCH, lw=0.8, ls=(0, (2, 2)))
    for k, (x, z) in CORNERS.items():
        ax.plot([x], [z], "o", ms=4.5, color=SKETCH, mec=SURFACE, mew=1)
        dx = -0.25 if k in "AD" else 0.25
        ax.annotate(f"{k} ({x:g}, {z:.4f})", (x, z), xytext=(x + dx, z + (-0.75 if k in "AB" else 0.45)),
                    ha="right" if k in "AD" else "left", fontsize=8.5, color=INK)
    notes = [(0.3, 2.85, "end wall, top z = +2 (45° chamfer)", "left"),
             (0.3, -0.75, "inner end face, z = 0", "left"),
             (-14.6, -25.75, "rim, z = −25", "left"),
             (-6.4, -12.5, "bore Ø23.5\n(thread crest)", "center"),
             (6.4, -12.5, "thread groove: 3.5 mm pitch,\nright-hand; bottom Ø27", "center")]
    for x, z, s, ha in notes:
        ax.text(x, z, s, fontsize=8.5, color=INK2, ha=ha, va="center")
    ax.set_aspect("equal")
    ax.set_xlim(-16, 19.5)
    ax.set_ylim(-31.2, 3.6)
    ax.set_xlabel("x = radius (mm)", color=INK2)
    ax.set_ylabel("z (mm)", color=INK2)
    ax.tick_params(colors=INK2, labelsize=8)
    for s in ax.spines.values():
        s.set_color(GRID)
    ax.grid(color=GRID, lw=0.5)
    ax.set_axisbelow(True)
    ax.set_title("Auger cap, cut through its axis (Front plane), and the groove sketch of recipe step 6",
                 color=INK, fontsize=10.5, loc="left")
    fig.text(0.01, 0.01, "Blue: fsgen's build of parts/auger_cap.fs. Orange: step 6, trapezoid A-B-C-D with 1 mm "
             "fillets at B and C;\nthe sweep carries it up the helix through the cap. 0 Onshape calls.",
             fontsize=8, color=INK2)
    fig.tight_layout(rect=(0, 0.04, 1, 1))
    out = HERE / "renders" / "local" / "auger_cap_section.png"
    fig.savefig(out, facecolor=SURFACE)
    print("->", out.relative_to(HERE))


if __name__ == "__main__":
    main()
