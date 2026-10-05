"""Side sections of the servos-above doser at rest, before and after the
5 mm drop (frames.DROP): through a hinge tower (x = 35) and through the
bracket screws (x = 24).  "Before" is the previous baseplate STEP, from git,
with DROP set to 0.

    PYTHONPATH=src python3 checks/lowered_sections.py [--before-ref 9a9a570]

Writes renders/checks/lowered_sections.png.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "checks")]

import parts_index  # noqa: E402
from lib import frames as F  # noqa: E402
from lib import hardware_placements as H  # noqa: E402

CUTS = {35.0: "x = 35 (through the +X hinge tower)", 24.0: "x = 24 (through the +X bracket screws)"}
SHOW = {"Baseplate": "#8c9198", "Mounting board": "#d8c39a", "Mounting plate": "#b9bcc2",
        "Bracket (front)": "#7fa6c4", "Bracket (rear)": "#7fa6c4", "Tap collar base": "#5d8db3",
        "Servo MG996R (+X)": "#202124", "Servo pinion (+X)": "#5aa36f"}
HW = ("Hinge screw (+X)", "Hinge locknut (+X)", "Bracket screw", "Bracket nut", "Tap base")
# labels on the "after" panels: (cut x, text, arrow tip (y, z), text at (y, z))
NOTES = [(35.0, "hinge and towers 5 mm lower", (45.4, 33.0), (75.0, 50.0)),
         (35.0, "floor 1 mm above the 2 mm skin", (95.0, 2.5), (120.0, 24.0)),
         (24.0, "M3 button heads 1.35 mm above the board: the limit", (103.7, 1.3), (112.0, -8.5)),
         (24.0, "slot to y = 111", (110.0, 4.0), (128.0, 30.0))]


def section_polys(shape, x: float):
    """Closed (y, z) polylines of shape cut by the plane x = const."""
    from build123d import Align, Axis, Box, Location
    cut = shape.intersect(Box(0.02, 600, 600, align=(Align.CENTER,) * 3).moved(Location((x, 100, 0))))
    out = []
    if not cut:
        return out
    for s in cut.solids():
        face = s.faces().sort_by(Axis.X)[-1]
        for w in face.wires():
            pts = []
            for e in w.order_edges():
                n = 2 if e.geom_type == "LINE" else 24
                pts += [(p.Y, p.Z) for p in (e.position_at(i / n) for i in range(n))]
            if pts:
                out.append(pts + [pts[0]])
    return out


def scene(variant_drop: float, baseplate_step: Path | None):
    from build123d import import_step
    from lib.fasteners import fastener
    F.DROP["above"] = variant_drop
    parts = parts_index.assembly(0.0, "above", "recreated", board=True)
    if baseplate_step is not None:
        parts["Baseplate"] = import_step(str(baseplate_step)).solids()[0]
    shapes = {k: parts[k] for k in SHOW if k in parts}
    for name, key, joint, carrier, M in H.fastener_placements(0.0, "above", with_board=False):
        if name.startswith(HW):
            shapes[name] = fastener(key).moved(F.to_location(M))
    return shapes


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--before-ref", default="9a9a570", help="commit with the previous baseplate")
    a = ap.parse_args()
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Polygon

    old = ROOT / "tmp" / "baseplate_servos_above_before.step"
    old.parent.mkdir(parents=True, exist_ok=True)
    old.write_bytes(subprocess.run(
        ["git", "show", f"{a.before_ref}:cad/text-to-cad/STEP/parts/baseplate_servos_above.step"],
        check=True, capture_output=True, cwd=ROOT).stdout)
    drop = F.DROP["above"]
    scenes = {f"before (hinge z = {F.HINGE_Z:g})": scene(0.0, old),
              f"after, {drop:g} mm lower (hinge z = {F.HINGE_Z - drop:g})": scene(drop, None)}
    fig, axes = plt.subplots(len(CUTS), 2, figsize=(15, 9.5), sharex=True, sharey=True)
    for r, (x, cut_name) in enumerate(CUTS.items()):
        for c, (title, shapes) in enumerate(scenes.items()):
            ax = axes[r][c]
            for name, shp in shapes.items():
                color = SHOW.get(name, "#c9a227")
                for poly in section_polys(shp, x):
                    ax.add_patch(Polygon(poly, closed=True, fc=color, ec="k", lw=0.4,
                                         alpha=0.95, zorder=1 if name == "Mounting board" else 2))
            ax.axhline(6.0, color="#d62728", lw=0.6, ls="--", zorder=3)
            for nx, text, tip, at in (NOTES if c == 1 else []):
                if nx == x:
                    ax.annotate(text, tip, at, fontsize=8.5, zorder=4,
                                arrowprops=dict(arrowstyle="->", lw=0.8, color="#333"))
            ax.set_title(f"{title}: {cut_name}", fontsize=10)
            ax.set_aspect("equal")
            ax.grid(alpha=0.25)
    ax = axes[0][0]
    ax.set_xlim(20, 185)
    ax.set_ylim(-12, 62)
    for r in range(len(CUTS)):
        axes[r][0].set_ylabel("z (mm), board top at 0")
    for c in range(2):
        axes[-1][c].set_xlabel("y (mm), outlet end to the left")
    fig.suptitle("Servos-above doser at rest: the baseplate is relieved under the mounting plate's "
                 "floor (2 mm skin), so everything above the plate drops 5 mm. "
                 "Dashed: the plate's top, z = 6", fontsize=10.5)
    fig.tight_layout()
    out = ROOT / "renders" / "checks" / "lowered_sections.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=110)
    print("wrote", out)


if __name__ == "__main__":
    main()
