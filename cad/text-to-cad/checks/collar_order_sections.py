"""Side sections before and after the front bracket / tap collar swap.

PR #170 (and this recreation until f489826) had the tap collar and its base
in front of the front bracket.  The collar rides loose on the turning tube,
so as the doser tilts outlet down nothing stopped it sliding forward off its
base.  The lab's doser has them the other way round: the front bracket on
the floor's front M3 row, then the collar on its base, then the auger's 44T
gear, so the collar is held between the bracket and the gear.

"Before" puts the parts back where they were: the old rows, the auger and
the stepper pinion 1.6 mm further forward, and the servos-above board edge
at y = 100.  Top: the current layout just beside the auger axis (x = 2.5, through the
front bracket's clamp ear).
Bottom: the servos-above layout through the tap-collar base's tower-side
screw (x = -24), where its M3 x 30 ends flush with the plate's underside.

    PYTHONPATH=src python3 checks/collar_order_sections.py

Writes renders/checks/collar_order_sections.png.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "checks")]

import parts_index  # noqa: E402
from lib import frames as F  # noqa: E402
from lib import hardware_placements as H  # noqa: E402

SHOW = {"Baseplate": "#8c9198", "Mounting board": "#d8c39a", "Mounting plate": "#b9bcc2",
        "Auger": "#cca140", "Bracket (front)": "#7fa6c4", "Bracket (rear)": "#7fa6c4",
        "Tap collar base": "#5d8db3", "Tap collar": "#8c59b3",
        "Solenoid (Adafruit 412)": "#55585e", "Stepper pinion": "#5aa36f"}
HW = ("Bracket screw (front", "Bracket nut (front", "Tap base")
# (layout, cut x, title)
CUTS = [("below", 2.5, "current layout, x = 2.5 (through the auger, the bracket's +X clamp ear)"),
        ("above", -24.0, "servos above, x = -24 (through the tap-collar base's flat-head screw)")]
# labels on the "after" panels: (row, text, arrow tip (y, z), text at (y, z))
NOTES = [(0, "front bracket", (87.7, 62.0), (60.0, 84.0)),
         (0, "tap collar on its base", (103.7, 70.0), (100.0, 92.0)),
         (0, "44T gear", (118.7, 62.0), (138.0, 80.0)),
         (0, "1.5 mm to the bracket and 1.5 mm to the gear", (94.5, 28.5), (24.0, 8.0)),
         (0, "", (113.0, 28.5), (24.0, 8.0)),
         (1, "M3 x 30 ends flush with the plate's underside", (103.7, 0.3), (40.0, -8.0)),
         (1, "board edge moved to y = 108", (108.0, -3.0), (125.0, -9.0))]
NOTES_BEFORE = [(0, "tap collar: nothing in front of it", (79.2, 70.0), (30.0, 92.0)),
                (0, "front bracket", (103.7, 62.0), (118.0, 88.0)),
                (1, "board edge at y = 100", (100.0, -3.0), (120.0, -9.0))]


def section_polys(shape, x: float):
    """Closed (y, z) polylines of shape cut by the plane x = const: the
    planar faces a thin slab leaves on its +X side (curved faces' centres
    can lie outside the slab, so they are not sorted by centre)."""
    from build123d import Align, Box, GeomType, Location
    cut = shape.intersect(Box(0.02, 600, 600, align=(Align.CENTER,) * 3).moved(Location((x, 100, 0))))
    out = []
    if not cut:
        return out
    for face in cut.faces():
        if face.geom_type != GeomType.PLANE or abs(face.normal_at().X) < 0.99 or face.center().X < x:
            continue
        for w in face.wires():
            pts = []
            for e in w.order_edges():
                n = 2 if e.geom_type == GeomType.LINE else 24
                pts += [(p.Y, p.Z) for p in (e.position_at(i / n) for i in range(n))]
            if pts:
                out.append(pts + [pts[0]])
    return out


def _set_layout(swapped: bool) -> None:
    """Put the frames back to the old order (swapped=False) or the new one."""
    T, rot = F.T, F.rot_about
    if swapped:
        rows, tap_row, pinion_front, board_y = (-124.0, -42.33), -58.33, F.PINION_FRONT_X, 108.0
    else:
        rows, tap_row, pinion_front, board_y = (-124.0, -58.33), -42.33, -66.73, 100.0
    F.MP_ROWS_BRACKET, F.MP_ROW_TAP_BASE = rows, tap_row
    F.COLLAR_IN_MP = T([F.NZ, F.NX, F.Y], (tap_row + 8.5, 0.0, F.MP_MID_Z))
    F.TAP_BASE_IN_MP = T([F.Z, F.X, F.Y], (tap_row, F.MP_FLOOR_Y, F.MP_MID_Z))
    F.PINION_IN_MP = T([F.Z, F.Y, F.NX], (pinion_front, 0.0, F.MP_STEPPER_Z)) @ rot(F.Z, F.PINION_PHASE_DEG)
    outlet_x = pinion_front - F.PINION_TEETH_W / 2 + F.AUGER_GEAR_FROM_OUTLET
    F.AUGER_IN_MP = T([F.Z, F.Y, F.NX], (outlet_x, 0.0, F.MP_MID_Z))
    F.BOARD_FRONT_Y["above"] = board_y


def scene(variant: str, swapped: bool) -> dict:
    from lib.fasteners import fastener
    _set_layout(swapped)
    parts = parts_index.assembly(0.0, variant, "recreated", board=True)
    shapes = {k: parts[k] for k in SHOW if k in parts}
    for name, key, joint, carrier, M in H.fastener_placements(0.0, variant, with_board=False):
        if name.startswith(HW):
            shapes[name] = fastener(key).moved(F.to_location(M))
    return shapes


def main() -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Polygon

    cols = [("before: collar in front of the bracket (PR #170)", False),
            ("after: collar between the front bracket and the 44T gear", True)]
    fig, axes = plt.subplots(len(CUTS), 2, figsize=(15, 9.8), sharex=True)
    for r, (variant, x, cut_name) in enumerate(CUTS):
        for c, (title, swapped) in enumerate(cols):
            ax = axes[r][c]
            for name, shp in scene(variant, swapped).items():
                color = SHOW.get(name, "#c9a227")
                for poly in section_polys(shp, x):
                    ax.add_patch(Polygon(poly, closed=True, fc=color, ec="k", lw=0.4,
                                         alpha=0.95, zorder=1 if name == "Mounting board" else 2))
            for nr, text, tip, at in (NOTES if swapped else NOTES_BEFORE):
                if nr == r:
                    ax.annotate(text, tip, at, fontsize=8.5, zorder=4,
                                arrowprops=dict(arrowstyle="->", lw=0.8, color="#333"))
            ax.set_title(f"{title}\n{cut_name}", fontsize=10)
            ax.set_aspect("equal")
            ax.grid(alpha=0.25)
            ax.set_ylim(-12, 100) if r == 0 else ax.set_ylim(-12, 70)
        axes[r][0].set_ylabel("z (mm), board top at 0")
    _set_layout(True)
    axes[0][0].set_xlim(15, 175)
    for c in range(2):
        axes[-1][c].set_xlabel("y (mm), outlet end to the left")
    fig.suptitle("The tap collar rides loose on the tube: with the front bracket in front of it and "
                 "the auger's 44T gear behind, it cannot slide off its base when the doser tilts "
                 "outlet down", fontsize=10.5)
    fig.tight_layout()
    out = ROOT / "renders" / "checks" / "collar_order_sections.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=110)
    print("wrote", out)


if __name__ == "__main__":
    main()
