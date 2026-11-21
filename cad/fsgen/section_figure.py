"""Section through the +X hinge tower (x = 35 mm), no Onshape calls.

Left: the STEP Onshape exported from the fsgen tree (blue) over text-to-cad's
``baseplate_servos_above.step`` (orange outline). Right: the thinner-table branch
(plateThickness 3 mm, fsgen's local build, whose volume Onshape confirmed) over the main
workspace. Writes ``renders/section_x35.png``.

    python section_figure.py /path/to/text-to-cad/STEP/parts/baseplate_servos_above.step
"""
from __future__ import annotations

import sys
from pathlib import Path

import build123d as bd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import PathPatch
from matplotlib.path import Path as MPath

HERE = Path(__file__).resolve().parent
X = 35.0


def section_paths(step: Path) -> list[MPath]:
    solid = bd.import_step(str(step)).solids()[0]
    slab = bd.Box(0.002, 600, 600).moved(bd.Location((X, 0, 0)))
    cut = solid & slab
    paths = []
    for f in cut.faces():
        c = f.center()
        if abs(c.X - (X - 0.001)) > 1e-4 or abs(abs(f.normal_at().X) - 1) > 1e-6:
            continue
        verts, codes = [], []
        for w in [f.outer_wire(), *f.inner_wires()]:
            pts = [w.position_at(t / 200) for t in range(201)]
            verts += [(p.Y, p.Z) for p in pts]
            codes += [MPath.MOVETO] + [MPath.LINETO] * (len(pts) - 2) + [MPath.CLOSEPOLY]
        paths.append(MPath(verts, codes))
    return paths


def draw(ax, paths, face, edge, lw, alpha=1.0, z=1):
    for p in paths:
        ax.add_patch(PathPatch(p, facecolor=face, edgecolor=edge, linewidth=lw, alpha=alpha, zorder=z))


if __name__ == "__main__":
    ref = Path(sys.argv[1])
    onshape = section_paths(HERE / "results" / "onshape_export" / "baseplate_servos_above_onshape.step")
    t2c = section_paths(ref)
    thin = section_paths(HERE / "branch_thinner_table" / "out" / "baseplate_thinner_table" / "baseplate_thinner_table.step")
    blue, orange, ink2, surface = "#2a78d6", "#eb6834", "#52514e", "#fcfcfb"
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.6), dpi=200, sharey=True)
    fig.patch.set_facecolor(surface)
    draw(axes[0], onshape, blue, "none", 0, 0.85)
    draw(axes[0], t2c, "none", orange, 1.6, z=2)
    axes[0].set_title("main: Onshape export (blue) vs. text-to-cad (orange line), IoU 1.000000",
                      fontsize=9.5, color=ink2)
    draw(axes[1], onshape, "none", blue, 1.6, z=2)
    draw(axes[1], thin, orange, "none", 0, 0.85)
    axes[1].set_title("branch: thinner table, plateThickness 3 mm (orange) vs. main (blue line)",
                      fontsize=9.5, color=ink2)
    for ax in axes:
        ax.set_facecolor(surface)
        ax.set_aspect("equal")
        ax.set_xlim(25, 175)
        ax.set_ylim(-4, 82)
        ax.set_xlabel("y (mm)", fontsize=9, color=ink2)
        ax.grid(True, color="#e4e3df", linewidth=0.6)
        ax.set_axisbelow(True)
        ax.tick_params(colors=ink2, labelsize=8)
        for s in ("top", "right"):
            ax.spines[s].set_visible(False)
    axes[0].set_ylabel("z (mm)", fontsize=9, color=ink2)
    fig.suptitle(f"Section at x = {X:g} mm through the +X hinge tower (outlet towards -y)", fontsize=11,
                 x=0.02, ha="left", fontweight="bold")
    fig.tight_layout()
    out = HERE / "renders" / "section_x35.png"
    fig.savefig(out, facecolor=surface)
    print("->", out.relative_to(HERE))
