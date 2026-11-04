"""Generate dimensioned 2D engineering drawing for the mounting plate
and baseplate.  Output is ``drawing/engineering_drawing.png`` /
``.pdf`` / ``.svg``.

Run::

    python3 engineering_drawing.py
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import Circle, FancyArrowPatch, Polygon, Rectangle

import cad_model as M


HERE = Path(__file__).resolve().parent
DRW_DIR = HERE / "drawing"
DRW_DIR.mkdir(exist_ok=True)


# Drawing style.
LINE_K = dict(linewidth=1.2, edgecolor="#222", facecolor="none")
HOLE_K = dict(linewidth=0.9, edgecolor="#222", facecolor="#fff")
DIM_K  = dict(linewidth=0.6, color="#444")
TXT_K  = dict(fontsize=8)


# --------------------------------------------------------------------- #
# Dimension primitives
# --------------------------------------------------------------------- #
def _hdim(ax, x0: float, x1: float, y: float, text: str,
          *, tick: float = 2.0, offset: float = 5.0) -> None:
    """Horizontal dimension line from x0 to x1 at height y, labelled."""
    yo = y + offset
    ax.add_patch(FancyArrowPatch((x0, yo), (x1, yo),
                                 arrowstyle="<|-|>", mutation_scale=8,
                                 shrinkA=0, shrinkB=0, **DIM_K))
    ax.plot([x0, x0], [y, yo + 1], **DIM_K)
    ax.plot([x1, x1], [y, yo + 1], **DIM_K)
    ax.text((x0 + x1) / 2, yo + 1.5, text, ha="center", va="bottom", **TXT_K)


def _vdim(ax, y0: float, y1: float, x: float, text: str,
          *, offset: float = 5.0) -> None:
    """Vertical dimension line from y0 to y1 at x, labelled."""
    xo = x + offset
    ax.add_patch(FancyArrowPatch((xo, y0), (xo, y1),
                                 arrowstyle="<|-|>", mutation_scale=8,
                                 shrinkA=0, shrinkB=0, **DIM_K))
    ax.plot([x, xo + 1], [y0, y0], **DIM_K)
    ax.plot([x, xo + 1], [y1, y1], **DIM_K)
    ax.text(xo + 2, (y0 + y1) / 2, text, ha="left", va="center",
            rotation=90, **TXT_K)


def _hole(ax, x: float, y: float, dia: float, label: str | None = None,
          *, label_off: tuple[float, float] = (4, 4)) -> None:
    ax.add_patch(Circle((x, y), dia / 2, **HOLE_K))
    # Crosshair tick.
    r = dia / 2 + 1.5
    ax.plot([x - r, x + r], [y, y], **DIM_K)
    ax.plot([x, x], [y - r, y + r], **DIM_K)
    if label:
        ax.text(x + label_off[0], y + label_off[1], label, **TXT_K)


# --------------------------------------------------------------------- #
# Drawing
# --------------------------------------------------------------------- #
def _draw_mounting_plate_top(ax) -> None:
    """Top view: outline + all bolt holes + slot + boss outline + knuckles."""
    # Plate outline.
    ax.add_patch(Rectangle((-M.PLATE_W / 2, -M.PLATE_L / 2),
                           M.PLATE_W, M.PLATE_L, **LINE_K))

    # Bracket holes (×4: 2 brackets × 2 holes each)
    brk_hx = M.BRK_FLANGE_W / 2 - M.BRK_MOUNT_HOLE_INSET_X
    for cy, lbl in ((M.Y_BRK_FRONT, "Bracket FRONT"),
                    (M.Y_BRK_REAR, "Bracket REAR")):
        # Flange footprint (dashed).
        ax.add_patch(Rectangle((-M.BRK_FLANGE_W / 2, cy - M.BRK_FLANGE_D / 2),
                               M.BRK_FLANGE_W, M.BRK_FLANGE_D,
                               linewidth=0.6, edgecolor="#888",
                               facecolor="none", linestyle="--"))
        for sx in (+brk_hx, -brk_hx):
            _hole(ax, sx, cy, M.M3_CLEAR)
        ax.text(M.BRK_FLANGE_W / 2 + 3, cy, lbl, va="center", **TXT_K)

    # Tap-collar holes (2).
    tap_hx = M.TAP_PLATE_W / 2 - M.TAP_MOUNT_HOLE_INSET_X
    ax.add_patch(Rectangle((-M.TAP_PLATE_W / 2, M.Y_TAP - M.TAP_PLATE_D / 2),
                           M.TAP_PLATE_W, M.TAP_PLATE_D,
                           linewidth=0.6, edgecolor="#888",
                           facecolor="none", linestyle="--"))
    for sx in (+tap_hx, -tap_hx):
        _hole(ax, sx, M.Y_TAP, M.M3_CLEAR)
    ax.text(M.TAP_PLATE_W / 2 + 3, M.Y_TAP, "Tap-collar mount", va="center", **TXT_K)

    # Motor-boss footprint + 4 face holes + Ø22 pilot.
    ax.add_patch(Rectangle((M.X_MOTOR - M.BOSS_W / 2,
                            M.MOTOR_FACE_Y),
                           M.BOSS_W, M.BOSS_T,
                           linewidth=0.6, edgecolor="#888",
                           facecolor="none", linestyle="--"))
    for sx in (+M.NEMA11_FACE_HOLE_PITCH / 2, -M.NEMA11_FACE_HOLE_PITCH / 2):
        _hole(ax, M.X_MOTOR + sx, M.MOTOR_FACE_Y + M.BOSS_T / 2, M.M3_CLEAR)
    # Pilot (note: pilot is along +Y direction through the boss, not a
    # circle in the top view; we annotate it with text instead).
    ax.text(M.X_MOTOR, M.MOTOR_FACE_Y + M.BOSS_T + 3,
            "NEMA-11 boss\n(Ø22 pilot + 4×M3 @ 23 pitch)",
            ha="center", va="bottom", **TXT_K)

    # Gear-band clearance slot.
    gb_x_min = -(M.GEAR_BAND_TIP_DIA / 2) - 2.0
    gb_x_max = (M.X_MOTOR + M.PINION_TIP_DIA / 2) + 2.0
    ax.add_patch(Rectangle((gb_x_min, M.Y_GEAR_BAND - (M.GEAR_BAND_FACE_W + 8) / 2),
                           gb_x_max - gb_x_min, M.GEAR_BAND_FACE_W + 8,
                           **LINE_K))
    ax.text(gb_x_min - 3, M.Y_GEAR_BAND - 12, "Gear-band\nclearance slot",
            ha="right", va="center", **TXT_K)

    # Hinge knuckles (top-view footprint).
    for side in (+1, -1):
        cx = side * M.HINGE_X_OFFSET
        ax.add_patch(Rectangle((cx - M.HINGE_EYE_WIDTH / 2,
                                M.HINGE_Y),
                               M.HINGE_EYE_WIDTH, M.HINGE_DROP,
                               linewidth=0.6, edgecolor="#cc4400",
                               facecolor="none", linestyle=":"))
    ax.text(0, M.HINGE_Y + 2, "Hinge knuckles (×2)  — drop below plate",
            ha="center", va="bottom", color="#cc4400", **TXT_K)

    # --- Dimensions --------------------------------------------------------
    _hdim(ax, -M.PLATE_W / 2, M.PLATE_W / 2, M.PLATE_L / 2,
          f"{M.PLATE_W:g} (plate W)", offset=8)
    _vdim(ax, -M.PLATE_L / 2, M.PLATE_L / 2, M.PLATE_W / 2,
          f"{M.PLATE_L:g} (plate L)", offset=12)
    # Bracket Y spacing.
    _vdim(ax, M.Y_BRK_REAR, M.Y_BRK_FRONT, -M.PLATE_W / 2,
          f"{M.Y_BRK_FRONT - M.Y_BRK_REAR:g} (bracket Y pitch)",
          offset=-18)
    # Bracket X hole spacing.
    _hdim(ax, -brk_hx, +brk_hx, M.Y_BRK_FRONT - M.BRK_FLANGE_D / 2,
          f"{2 * brk_hx:g} (M3 hole pitch)", offset=-12)
    # Tap-collar centre.
    _vdim(ax, 0, M.Y_TAP, M.PLATE_W / 2 + 18,
          f"{M.Y_TAP:g} (tap-collar Y)", offset=8)
    # Hinge centre.
    _vdim(ax, 0, M.HINGE_Y, M.PLATE_W / 2 + 30,
          f"{M.HINGE_Y:g} (hinge edge Y)", offset=8)
    # Hinge knuckle X spacing.
    _hdim(ax, -M.HINGE_X_OFFSET, +M.HINGE_X_OFFSET, M.HINGE_Y + M.HINGE_DROP + 2,
          f"{2 * M.HINGE_X_OFFSET:g} (knuckle X pitch)", offset=4)

    ax.set_aspect("equal")
    ax.set_xlim(-M.PLATE_W / 2 - 50, M.PLATE_W / 2 + 70)
    ax.set_ylim(-M.PLATE_L / 2 - 30, M.PLATE_L / 2 + 40)
    ax.set_title("Mounting plate — TOP view (Z up out of page)",
                 fontsize=10, pad=10)
    ax.axis("off")


def _draw_mounting_plate_side(ax) -> None:
    """Side view (looking along +X): shows boss height, knuckle, hinge axis."""
    # Plate cross-section.
    ax.add_patch(Rectangle((-M.PLATE_L / 2, -M.PLATE_T),
                           M.PLATE_L, M.PLATE_T, **LINE_K))

    # Motor boss (rises above plate top).
    ax.add_patch(Rectangle((M.MOTOR_FACE_Y, 0),
                           M.BOSS_T, M.BOSS_H, **LINE_K))
    ax.plot([M.MOTOR_FACE_Y - M.NEMA11_BODY_L, M.MOTOR_FACE_Y],
            [M.Z_MOTOR + M.NEMA11_BODY_W / 2,
             M.Z_MOTOR + M.NEMA11_BODY_W / 2], **DIM_K)
    ax.plot([M.MOTOR_FACE_Y - M.NEMA11_BODY_L, M.MOTOR_FACE_Y],
            [M.Z_MOTOR - M.NEMA11_BODY_W / 2,
             M.Z_MOTOR - M.NEMA11_BODY_W / 2], **DIM_K)
    ax.plot([M.MOTOR_FACE_Y - M.NEMA11_BODY_L, M.MOTOR_FACE_Y - M.NEMA11_BODY_L],
            [M.Z_MOTOR - M.NEMA11_BODY_W / 2,
             M.Z_MOTOR + M.NEMA11_BODY_W / 2], **DIM_K)
    ax.text(M.MOTOR_FACE_Y - M.NEMA11_BODY_L / 2, M.Z_MOTOR + M.NEMA11_BODY_W / 2 + 2,
            "NEMA-11 body", ha="center", va="bottom", **TXT_K)

    # Auger circle (cross-section at Z_AUG, just a centre-line tick).
    ax.plot([-M.PLATE_L / 2 - 10, M.PLATE_L / 2 + 30], [M.Z_AUG, M.Z_AUG],
            color="#cc4400", linewidth=0.5, linestyle="-.")
    ax.text(-M.PLATE_L / 2 - 10, M.Z_AUG + 2, "Auger centreline",
            color="#cc4400", **TXT_K)

    # Hinge knuckle (side view): triangle gusset + eye.
    knuckle = Polygon([
        (M.HINGE_Y,                 -M.PLATE_T),
        (M.HINGE_Y - M.HINGE_DROP,  -M.PLATE_T),   # gusset toe (into plate)
        (M.HINGE_Y,                  M.HINGE_Z),    # eye centre
    ], **LINE_K)
    ax.add_patch(knuckle)
    ax.add_patch(Circle((M.HINGE_Y, M.HINGE_Z), M.HINGE_EYE_OD / 2, **LINE_K))
    ax.add_patch(Circle((M.HINGE_Y, M.HINGE_Z), M.HINGE_EYE_ID / 2,
                        linewidth=0.6, edgecolor="#222",
                        facecolor="#fff"))
    ax.plot(M.HINGE_Y, M.HINGE_Z, "+", color="#cc4400", markersize=8,
            markeredgewidth=1.2)
    ax.text(M.HINGE_Y + 4, M.HINGE_Z, "Hinge axis", **TXT_K, color="#cc4400")

    # Dimensions.
    _hdim(ax, -M.PLATE_L / 2, M.PLATE_L / 2, -M.PLATE_T - 18,
          f"{M.PLATE_L:g} (plate length, Y)", offset=-6)
    _vdim(ax, -M.PLATE_T, 0, -M.PLATE_L / 2 - 6,
          f"{M.PLATE_T:g} (plate thickness)", offset=-12)
    _vdim(ax, 0, M.Z_AUG, M.PLATE_L / 2 + 30,
          f"{M.Z_AUG:.1f} (auger ↑ from plate top)", offset=8)
    _vdim(ax, M.HINGE_Z, -M.PLATE_T, M.HINGE_Y + 18,
          f"{M.HINGE_DROP:g} (hinge drop)", offset=4)
    ax.text(M.HINGE_Y + 5, M.HINGE_Z - 12,
            f"Eye Ø{M.HINGE_EYE_OD:g} / bore Ø{M.HINGE_EYE_ID:g} (M5)",
            **TXT_K)

    ax.set_aspect("equal")
    ax.set_xlim(-M.PLATE_L / 2 - 40, M.PLATE_L / 2 + 60)
    ax.set_ylim(M.HINGE_Z - 20, M.BOSS_H + 10)
    ax.set_title("Mounting plate — SIDE view (looking along +X, Y →, Z ↑)",
                 fontsize=10, pad=10)
    ax.axis("off")


def _draw_baseplate_top(ax) -> None:
    """Top view of the baseplate."""
    ax.add_patch(Rectangle((-M.BASE_W / 2, M.BASE_Y_CENTRE - M.BASE_L / 2),
                           M.BASE_W, M.BASE_L, **LINE_K))

    # Corner bolt holes.
    bx = M.BASE_W / 2 - M.BASE_BOLT_INSET
    for sx in (+bx, -bx):
        for sy in (M.BASE_Y_CENTRE + (M.BASE_L / 2 - M.BASE_BOLT_INSET),
                   M.BASE_Y_CENTRE - (M.BASE_L / 2 - M.BASE_BOLT_INSET)):
            _hole(ax, sx, sy, M.BASE_BOLT_DIA)
    ax.text(bx + 3, M.BASE_Y_CENTRE + (M.BASE_L / 2 - M.BASE_BOLT_INSET),
            "Ø5.4 (M5) ×4", **TXT_K)

    # Powder window.
    ax.add_patch(Rectangle((-M.WINDOW_W / 2, M.WINDOW_Y - M.WINDOW_L / 2),
                           M.WINDOW_W, M.WINDOW_L, **LINE_K))
    ax.text(0, M.WINDOW_Y, f"Powder window\n{M.WINDOW_W:g} × {M.WINDOW_L:g}",
            ha="center", va="center", **TXT_K)

    # Hinge posts (top-view footprint).
    for side in (+1, -1):
        cx = side * M.HINGE_X_OFFSET
        post_x_offset = side * (M.HINGE_EYE_WIDTH / 2 + 1.0 + M.POST_W / 2)
        post_cx = cx + post_x_offset
        ax.add_patch(Rectangle((post_cx - M.POST_W / 2,
                                M.POST_Y - M.POST_W / 2),
                               M.POST_W, M.POST_W,
                               linewidth=0.8, edgecolor="#cc4400",
                               facecolor="none"))
    ax.plot([-M.BASE_W / 2 - 4, M.BASE_W / 2 + 4],
            [M.HINGE_Y, M.HINGE_Y],
            color="#cc4400", linewidth=0.5, linestyle="-.")
    ax.text(M.BASE_W / 2 + 5, M.HINGE_Y, "Hinge axis (= mounting-plate edge)",
            color="#cc4400", va="center", **TXT_K)

    # Dimensions.
    _hdim(ax, -M.BASE_W / 2, M.BASE_W / 2, M.BASE_Y_CENTRE + M.BASE_L / 2,
          f"{M.BASE_W:g} (base W)", offset=8)
    _vdim(ax, M.BASE_Y_CENTRE - M.BASE_L / 2, M.BASE_Y_CENTRE + M.BASE_L / 2,
          M.BASE_W / 2, f"{M.BASE_L:g} (base L)", offset=14)
    # Window Y position from hinge.
    _vdim(ax, M.HINGE_Y, M.WINDOW_Y, -M.BASE_W / 2 - 5,
          f"{M.WINDOW_Y - M.HINGE_Y:.2f} (hinge → window)", offset=-22)

    ax.set_aspect("equal")
    ax.set_xlim(-M.BASE_W / 2 - 60, M.BASE_W / 2 + 110)
    ax.set_ylim(M.BASE_Y_CENTRE - M.BASE_L / 2 - 25,
                M.BASE_Y_CENTRE + M.BASE_L / 2 + 25)
    ax.set_title("Baseplate — TOP view (Z up out of page)",
                 fontsize=10, pad=10)
    ax.axis("off")


def _draw_hinge_detail(ax) -> None:
    """Side-view detail of the hinge joint (X out of page)."""
    # Mounting plate cross-section (just the rear bit).
    ax.add_patch(Rectangle((M.HINGE_Y - 25, -M.PLATE_T),
                           25, M.PLATE_T, **LINE_K))
    # Triangle knuckle gusset.
    knuckle = Polygon([
        (M.HINGE_Y,                 -M.PLATE_T),
        (M.HINGE_Y - M.HINGE_DROP,  -M.PLATE_T),
        (M.HINGE_Y,                  M.HINGE_Z),
    ], **LINE_K)
    ax.add_patch(knuckle)
    # Knuckle eye.
    ax.add_patch(Circle((M.HINGE_Y, M.HINGE_Z), M.HINGE_EYE_OD / 2, **LINE_K))
    ax.add_patch(Circle((M.HINGE_Y, M.HINGE_Z), M.HINGE_EYE_ID / 2, **HOLE_K))

    # Baseplate cross-section (top face at Z_BASE_TOP).
    ax.add_patch(Rectangle((M.HINGE_Y - 25, M.Z_BASE_TOP - M.BASE_T),
                           60, M.BASE_T, **LINE_K))
    # Post + eye.
    ax.add_patch(Rectangle((M.POST_Y - M.POST_W / 2, M.Z_BASE_TOP),
                           M.POST_W, M.POST_H, **LINE_K))
    ax.add_patch(Circle((M.POST_Y, M.HINGE_Z), M.HINGE_EYE_OD / 2, **LINE_K))
    ax.add_patch(Circle((M.POST_Y, M.HINGE_Z), M.HINGE_EYE_ID / 2, **HOLE_K))

    # Hinge pin (single dot indicating axis out of page).
    ax.plot(M.HINGE_Y, M.HINGE_Z, "x", color="#cc4400", markersize=8,
            markeredgewidth=1.5)
    ax.plot(M.POST_Y, M.HINGE_Z, "x", color="#cc4400", markersize=8,
            markeredgewidth=1.5)
    ax.text(M.HINGE_Y - 10, M.HINGE_Z + 8,
            f"M5 pin (Ø{M.M5_PIN_DIA:g})\nbore Ø{M.HINGE_EYE_ID:g}",
            color="#cc4400", **TXT_K)

    # Dimensions.
    _vdim(ax, M.Z_BASE_TOP, M.HINGE_Z, M.POST_Y + 10,
          f"{M.POST_H:g} (post H)", offset=4)
    _vdim(ax, M.HINGE_Z, -M.PLATE_T, M.HINGE_Y + 15,
          f"{M.HINGE_DROP:g} (knuckle drop)", offset=4)
    _hdim(ax, M.HINGE_Y, M.POST_Y, M.HINGE_Z + M.HINGE_EYE_OD / 2 + 4,
          f"{M.POST_Y - M.HINGE_Y:g}", offset=4)

    ax.set_aspect("equal")
    ax.set_xlim(M.HINGE_Y - 30, M.HINGE_Y + 55)
    ax.set_ylim(M.Z_BASE_TOP - M.BASE_T - 8, M.HINGE_Z + 20)
    ax.set_title("Hinge detail — SIDE view (X out of page)",
                 fontsize=10, pad=10)
    ax.axis("off")


def main() -> None:
    fig = plt.figure(figsize=(16, 22), dpi=120)
    gs = fig.add_gridspec(3, 2, hspace=0.18, wspace=0.10,
                          height_ratios=[1.6, 1.0, 1.0])
    ax_mp_top  = fig.add_subplot(gs[0, :])
    ax_mp_side = fig.add_subplot(gs[1, :])
    ax_bp_top  = fig.add_subplot(gs[2, 0])
    ax_hinge   = fig.add_subplot(gs[2, 1])

    _draw_mounting_plate_top(ax_mp_top)
    _draw_mounting_plate_side(ax_mp_side)
    _draw_baseplate_top(ax_bp_top)
    _draw_hinge_detail(ax_hinge)

    fig.suptitle(
        "Powder-doser mounting plate + baseplate — engineering drawing  "
        f"(all dimensions mm; PLA, 100 % infill recommended; "
        f"plate T={M.PLATE_T:g}, base T={M.BASE_T:g})",
        fontsize=11, y=0.995,
    )
    fig.text(0.5, 0.005,
             "M3 hole = Ø3.4 clearance, M5 hole = Ø5.4 clearance, "
             "M5 pin = Ø5.0; bracket / tap-collar hole patterns mirror "
             "the upstream PR #55 / PR #51 footprints; NEMA-11 face holes "
             "match the PR #49 motor block.",
             ha="center", va="bottom", fontsize=8, color="#555")

    for fmt in ("png", "pdf", "svg"):
        out = DRW_DIR / f"engineering_drawing.{fmt}"
        fig.savefig(out, bbox_inches="tight", facecolor="white")
        print(f"  {out.relative_to(HERE)}")


if __name__ == "__main__":
    main()
