"""Install / rotation / powder-flow diagrams for the mounting-plate assembly.

Produces matplotlib SVGs + PNGs in ``diagrams/``:

- ``install_mounting_plate.{svg,png}`` — top view of the mounting plate
  with every M3/M5 hole labelled and grouped by the part it carries
  (bracket #1, bracket #2, tap collar, NEMA-17, hinge, actuator tab).
- ``install_baseplate.{svg,png}`` — top view of the baseplate showing
  the hinge pillars, linear-actuator clevis, leg footprint, and
  discharge cut-out, all labelled.
- ``rotation_0_45_90.{svg,png}`` — three side-elevation diagrams of the
  assembly tilted to 0°, 45°, and 90° about the hinge axis, with the
  driving linear actuator drawn at the length each angle requires.
- ``powder_flow.{svg,png}`` — schematic of powder travelling down the
  auger, through the discharge bore, past the discharge notch and
  baseplate cut-out, and into the cup on top of the scale.

All dimensions come from ``cad_model``, so updating the CadQuery
constants automatically updates the diagrams.
"""

from __future__ import annotations

import math
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.patches as mp
import matplotlib.pyplot as plt

import cad_model as cm  # noqa: E402  (sibling module, run via `python -m`)

HERE = Path(__file__).parent
OUT = HERE / "diagrams"
OUT.mkdir(exist_ok=True)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _save(fig, stem: str) -> None:
    fig.savefig(OUT / f"{stem}.svg", bbox_inches="tight")
    fig.savefig(OUT / f"{stem}.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def _label_hole(ax, x, y, name, dx=4, dy=4, ha="left"):
    ax.plot(x, y, "ko", markersize=2.5)
    ax.annotate(name, xy=(x, y), xytext=(x + dx, y + dy),
                fontsize=7, ha=ha,
                arrowprops=dict(arrowstyle="-", lw=0.4, color="0.4"))


# ---------------------------------------------------------------------------
# Mounting plate install diagram
# ---------------------------------------------------------------------------

def diagram_mounting_plate() -> None:
    fig, ax = plt.subplots(figsize=(11, 5))
    ax.set_aspect("equal")

    # Plate outline (top view, X right, Y up). Discharge end at X=0, motor
    # end at X=MP_LEN.
    ax.add_patch(mp.FancyBboxPatch(
        (0, -cm.MP_WIDTH / 2.0), cm.MP_LEN, cm.MP_WIDTH,
        boxstyle="round,pad=0,rounding_size=6",
        linewidth=1.0, edgecolor="black", facecolor="#eef2fa"))

    # Discharge notch.
    ax.add_patch(mp.Rectangle(
        (0, -cm.DISCHARGE_NOTCH_W / 2.0),
        cm.DISCHARGE_NOTCH_X, cm.DISCHARGE_NOTCH_W,
        edgecolor="black", facecolor="white", linewidth=0.8))
    ax.annotate("Discharge notch\n(powder falls through)",
                xy=(cm.DISCHARGE_NOTCH_X / 2.0, 0),
                xytext=(2, -cm.MP_WIDTH / 2.0 - 16),
                fontsize=7, ha="left",
                arrowprops=dict(arrowstyle="->", lw=0.4))

    # Hinge axis annotation (a dashed line at X = HINGE_X).
    ax.plot([cm.HINGE_X, cm.HINGE_X],
            [-cm.MP_WIDTH / 2.0 - 8, cm.MP_WIDTH / 2.0 + 8],
            "--", color="#c0392b", lw=0.8)
    ax.text(cm.HINGE_X, cm.MP_WIDTH / 2.0 + 10,
            "HINGE AXIS  (also auger discharge axis)",
            color="#c0392b", fontsize=7, ha="center")

    # Hinge pillar footprints (rectangles peeking out the bottom).
    for y_sign in (-1.0, +1.0):
        yc = y_sign * cm.HINGE_PILLAR_Y
        ax.add_patch(mp.Rectangle(
            (cm.HINGE_X - cm.HINGE_PILLAR_W / 2.0,
             yc - cm.HINGE_PILLAR_T / 2.0),
            cm.HINGE_PILLAR_W, cm.HINGE_PILLAR_T,
            edgecolor="#c0392b", facecolor="#fadbd8", linewidth=0.6))
        _label_hole(ax, cm.HINGE_X, yc, "M5 hinge pin",
                    dx=8, dy=4 * y_sign)

    # Hole groups.
    def add_group(x_centre, dx_pat, dy_pat, hole_d, label, short, colour):
        for i, (sx, sy) in enumerate([(-1, -1), (-1, 1), (1, -1), (1, 1)]):
            x = x_centre + sx * dx_pat / 2.0
            y = sy * dy_pat / 2.0
            ax.add_patch(mp.Circle((x, y), hole_d / 2.0, edgecolor="black",
                                   facecolor="white", linewidth=0.6))
            ax.text(x, y - 4, f"{short}{i + 1}",
                    fontsize=6, ha="center", color=colour)
        # Outline the part footprint lightly.
        ax.add_patch(mp.Rectangle(
            (x_centre - cm.BRACKET_FLANGE_D / 2.0,
             -cm.BRACKET_FLANGE_W / 2.0),
            cm.BRACKET_FLANGE_D, cm.BRACKET_FLANGE_W,
            edgecolor=colour, facecolor="none",
            linewidth=0.4, linestyle=":"))
        ax.text(x_centre, cm.BRACKET_FLANGE_W / 2.0 + 1.0,
                label, fontsize=8, ha="center",
                color=colour, fontweight="bold")

    add_group(cm.X_BRACKET_DISCHARGE,
              cm.BRACKET_HOLE_DX, cm.BRACKET_HOLE_DY,
              cm.BRACKET_HOLE_D,
              "BRK-D (M3, bracket #1)", "D", "#1f6f3f")
    add_group(cm.X_TAP_COLLAR,
              cm.TAP_HOLE_DX, cm.TAP_HOLE_DY,
              cm.TAP_HOLE_D,
              "TAP (M3, tap-collar mount)", "T", "#7e3f8b")
    add_group(cm.X_BRACKET_MOTOR,
              cm.BRACKET_HOLE_DX, cm.BRACKET_HOLE_DY,
              cm.BRACKET_HOLE_D,
              "BRK-M (M3, bracket #2)", "M", "#1f6f3f")

    # NEMA-17: 4 bolts on 31 mm pattern + pilot.
    half = cm.NEMA17_BOLT_PITCH / 2.0
    for i, (sx, sy) in enumerate([(-1, -1), (-1, 1), (1, -1), (1, 1)]):
        x = cm.X_NEMA17 + sx * half
        y = sy * half
        ax.add_patch(mp.Circle((x, y), cm.NEMA17_HOLE_D / 2.0,
                               edgecolor="black", facecolor="white",
                               linewidth=0.6))
        ax.text(x, y - 4, f"NEMA-{i + 1}", fontsize=6, ha="center",
                color="#0b3d8a")
    ax.add_patch(mp.Circle((cm.X_NEMA17, 0), cm.NEMA17_PILOT / 2.0,
                           edgecolor="#0b3d8a", facecolor="white",
                           linewidth=0.6, linestyle="--"))
    ax.text(cm.X_NEMA17, 0, "Ø22 pilot", fontsize=6, ha="center",
            color="#0b3d8a")
    ax.add_patch(mp.Rectangle(
        (cm.X_NEMA17 - cm.NEMA17_BODY / 2.0,
         -cm.NEMA17_BODY / 2.0),
        cm.NEMA17_BODY, cm.NEMA17_BODY,
        edgecolor="#0b3d8a", facecolor="none",
        linewidth=0.4, linestyle=":"))
    ax.text(cm.X_NEMA17, cm.NEMA17_BODY / 2.0 + 1.0,
            "NEMA-17 (M3, motor)", fontsize=8, ha="center",
            color="#0b3d8a", fontweight="bold")

    # Linear-actuator tab footprint indicator (under the plate, near hinge).
    tab_x = cm.HINGE_X + 55.0
    ax.text(tab_x, -cm.MP_WIDTH / 2.0 - 6,
            "LA tab (underside, M5 clevis)",
            fontsize=7, ha="center", color="#a04000")
    ax.add_patch(mp.Circle((tab_x, 0), 1.5,
                           edgecolor="#a04000", facecolor="#a04000"))

    # Axes / labels / title.
    ax.set_xlim(-12, cm.MP_LEN + 12)
    ax.set_ylim(-cm.MP_WIDTH / 2.0 - 28, cm.MP_WIDTH / 2.0 + 22)
    ax.set_xlabel("X — auger long axis (mm)")
    ax.set_ylabel("Y (mm)")
    ax.set_title(f"Mounting-plate install diagram  "
                 f"(top view, plate {cm.MP_LEN}×{cm.MP_WIDTH}×{cm.MP_THK} mm)")
    ax.grid(True, ls=":", lw=0.3, alpha=0.5)
    _save(fig, "install_mounting_plate")
    print("wrote diagrams/install_mounting_plate.{svg,png}")


# ---------------------------------------------------------------------------
# Baseplate install diagram
# ---------------------------------------------------------------------------

def diagram_baseplate() -> None:
    fig, ax = plt.subplots(figsize=(11, 7))
    ax.set_aspect("equal")

    # Baseplate outline.
    ax.add_patch(mp.FancyBboxPatch(
        (cm.BP_X_OFFSET, -cm.BP_WIDTH / 2.0),
        cm.BP_LEN, cm.BP_WIDTH,
        boxstyle="round,pad=0,rounding_size=8",
        linewidth=1.0, edgecolor="black", facecolor="#f0f0e8"))

    # Discharge cut-out.
    ax.add_patch(mp.Rectangle(
        (cm.HINGE_X - cm.DISCHARGE_OPENING_D / 2.0,
         -cm.DISCHARGE_OPENING_W / 2.0),
        cm.DISCHARGE_OPENING_D, cm.DISCHARGE_OPENING_W,
        edgecolor="black", facecolor="white", linewidth=0.8))
    ax.text(cm.HINGE_X, 0, "Discharge\ncut-out",
            ha="center", va="center", fontsize=7)

    # Hinge pillars (top-view rectangles at the hinge end).
    for y_sign in (-1.0, +1.0):
        yc = y_sign * (cm.HINGE_PILLAR_Y + cm.HINGE_PILLAR_T + 1.0)
        ax.add_patch(mp.Rectangle(
            (cm.HINGE_X - cm.HINGE_PILLAR_W / 2.0,
             yc - cm.HINGE_PILLAR_T / 2.0),
            cm.HINGE_PILLAR_W, cm.HINGE_PILLAR_T,
            edgecolor="#c0392b", facecolor="#fadbd8", linewidth=0.6))
        _label_hole(ax, cm.HINGE_X, yc, "M5 hinge pin (mating)",
                    dx=10, dy=4 * y_sign)

    # Linear-actuator clevis lugs.
    for y_sign in (-1.0, +1.0):
        yc = y_sign * 8.0
        ax.add_patch(mp.Rectangle(
            (cm.LA_BASE_PIVOT_X - 7, yc - 2),
            14, 4,
            edgecolor="#a04000", facecolor="#fdebd0", linewidth=0.6))
        _label_hole(ax, cm.LA_BASE_PIVOT_X, yc, "M5 LA pivot",
                    dx=8, dy=6 * y_sign)

    # Legs (as outlined squares at corners).
    bp_x0 = cm.BP_X_OFFSET
    bp_x1 = cm.BP_X_OFFSET + cm.BP_LEN
    bp_y0 = -cm.BP_WIDTH / 2.0
    bp_y1 = +cm.BP_WIDTH / 2.0
    inset = cm.LEG_SECTION / 2.0 + 4.0
    leg_pts = [
        (bp_x0 + inset, bp_y0 + inset),
        (bp_x0 + inset, bp_y1 - inset),
        (bp_x1 - inset, bp_y0 + inset),
        (bp_x1 - inset, bp_y1 - inset),
    ]
    for i, (lx, ly) in enumerate(leg_pts):
        ax.add_patch(mp.Rectangle(
            (lx - cm.LEG_SECTION / 2.0, ly - cm.LEG_SECTION / 2.0),
            cm.LEG_SECTION, cm.LEG_SECTION,
            edgecolor="#7d6608", facecolor="#fcf3cf", linewidth=0.6))
        ax.text(lx, ly, f"LEG-{i + 1}\n{cm.LEG_H} mm",
                ha="center", va="center", fontsize=6,
                color="#7d6608")

    # Cup + scale shadow under the discharge.
    ax.add_patch(mp.Rectangle(
        (cm.HINGE_X - cm.SCALE_W / 2.0, -cm.SCALE_D / 2.0),
        cm.SCALE_W, cm.SCALE_D,
        edgecolor="0.4", facecolor="none",
        linewidth=0.4, linestyle="--"))
    ax.text(cm.HINGE_X, -cm.SCALE_D / 2.0 - 4,
            f"Scale envelope ({cm.SCALE_W}×{cm.SCALE_D}×{cm.SCALE_H} mm) "
            f"under baseplate",
            ha="center", va="top", fontsize=7, color="0.3")

    ax.set_xlim(bp_x0 - 12, bp_x1 + 12)
    ax.set_ylim(bp_y0 - 22, bp_y1 + 18)
    ax.set_xlabel("X (mm)")
    ax.set_ylabel("Y (mm)")
    ax.set_title(f"Baseplate install diagram (top view, plate "
                 f"{cm.BP_LEN}×{cm.BP_WIDTH}×{cm.BP_THK} mm "
                 f"on four {cm.LEG_H} mm legs)")
    ax.grid(True, ls=":", lw=0.3, alpha=0.5)
    _save(fig, "install_baseplate")
    print("wrote diagrams/install_baseplate.{svg,png}")


# ---------------------------------------------------------------------------
# Rotation diagram
# ---------------------------------------------------------------------------

def diagram_rotation() -> None:
    fig, axes = plt.subplots(1, 3, figsize=(15, 5), sharey=True)

    pin_world_z = cm.LEG_H + cm.BP_THK + 50.0 - 4.0
    la_lower_x = cm.LA_BASE_PIVOT_X
    la_lower_z = cm.LEG_H + cm.BP_THK + 12.0
    mp_z_lift = cm.AUGER_OD / 2.0 + cm.BRACKET_FLANGE_T

    # Tab attach point (in MP local frame): underside, X = HINGE_X+55, Y=0,
    # z = -17 (hangs 17 mm below the plate underside).
    tab_local = (cm.HINGE_X + 55.0, -17.0)

    for ax, tilt_deg in zip(axes, (0, 45, 90)):
        ax.set_aspect("equal")
        # Floor.
        ax.axhline(0, color="0.5", lw=0.4)
        ax.text(-40, -4, "floor", fontsize=7, color="0.5")

        # Baseplate (side view rectangle).
        ax.add_patch(mp.Rectangle(
            (cm.BP_X_OFFSET, cm.LEG_H), cm.BP_LEN, cm.BP_THK,
            edgecolor="black", facecolor="#f0f0e8", lw=0.6))
        # Legs.
        for lx in (cm.BP_X_OFFSET + 13, cm.BP_X_OFFSET + cm.BP_LEN - 13):
            ax.add_patch(mp.Rectangle(
                (lx - cm.LEG_SECTION / 2.0, 0),
                cm.LEG_SECTION, cm.LEG_H,
                edgecolor="#7d6608", facecolor="#fcf3cf", lw=0.6))
        # Base hinge pillar.
        ax.add_patch(mp.Rectangle(
            (cm.HINGE_X - cm.HINGE_PILLAR_W / 2.0,
             cm.LEG_H + cm.BP_THK),
            cm.HINGE_PILLAR_W, 50.0,
            edgecolor="#c0392b", facecolor="#fadbd8", lw=0.6))
        # LA base clevis.
        ax.add_patch(mp.Rectangle(
            (cm.LA_BASE_PIVOT_X - 7, cm.LEG_H + cm.BP_THK),
            14, 25, edgecolor="#a04000", facecolor="#fdebd0", lw=0.6))

        # Cup + scale.
        ax.add_patch(mp.Rectangle(
            (cm.HINGE_X - cm.SCALE_W / 2.0, 0),
            cm.SCALE_W, cm.SCALE_H,
            edgecolor="0.4", facecolor="0.85", lw=0.5))
        ax.add_patch(mp.Rectangle(
            (cm.HINGE_X - cm.CUP_OD / 2.0, cm.SCALE_H),
            cm.CUP_OD, cm.CUP_H,
            edgecolor="#7d6608", facecolor="#fcf3cf", lw=0.5))

        # Hinge marker.
        ax.plot(cm.HINGE_X, pin_world_z, "o",
                markerfacecolor="white", markeredgecolor="#c0392b",
                markersize=6)
        ax.text(cm.HINGE_X - 3, pin_world_z + 6, "hinge",
                color="#c0392b", fontsize=7, ha="right")

        # Rotate the upper assembly by tilt_deg about (HINGE_X, pin_world_z),
        # using -Y axis (right-hand-rule) so the motor end swings UP, not
        # DOWN — matches cad_model.build_assembly().
        ang = math.radians(tilt_deg)
        cos_a, sin_a = math.cos(ang), math.sin(ang)

        def rot(pt):
            x, z = pt
            dx, dz = x - cm.HINGE_X, z - pin_world_z
            xr = cm.HINGE_X + cos_a * dx - sin_a * dz
            zr = pin_world_z + sin_a * dx + cos_a * dz
            return xr, zr

        # Mounting plate as a rectangle in side view: spans X 0..MP_LEN,
        # Z = (mp_z_lift) .. (mp_z_lift + MP_THK) above the hinge pin.
        plate_corners_local = [
            (0, mp_z_lift),
            (cm.MP_LEN, mp_z_lift),
            (cm.MP_LEN, mp_z_lift + cm.MP_THK),
            (0, mp_z_lift + cm.MP_THK),
        ]
        # Convert local-MP to world (pre-rotation): add pin_world_z to z.
        plate_world = [(x, z + pin_world_z) for (x, z) in plate_corners_local]
        plate_rot = [rot(p) for p in plate_world]
        ax.add_patch(mp.Polygon(plate_rot, closed=True,
                                edgecolor="black", facecolor="#eef2fa",
                                lw=0.7))

        # Auger as a thick line from X=0..AUGER_LEN at z=pin_world_z.
        a0 = rot((0.0, pin_world_z))
        a1 = rot((cm.AUGER_LEN, pin_world_z))
        ax.plot([a0[0], a1[0]], [a0[1], a1[1]],
                color="#7d4f1f", lw=cm.AUGER_OD * 0.6,
                solid_capstyle="butt")
        # Discharge bore mark.
        bore = rot((cm.AUGER_DISCHARGE_X, pin_world_z))
        ax.plot(bore[0], bore[1], "o", markerfacecolor="white",
                markeredgecolor="black", markersize=4)

        # NEMA-17 box on top of plate at X = X_NEMA17.
        nema_local = [
            (cm.X_NEMA17 - 21, mp_z_lift + cm.MP_THK),
            (cm.X_NEMA17 + 21, mp_z_lift + cm.MP_THK),
            (cm.X_NEMA17 + 21, mp_z_lift + cm.MP_THK + cm.NEMA17_LEN),
            (cm.X_NEMA17 - 21, mp_z_lift + cm.MP_THK + cm.NEMA17_LEN),
        ]
        nema_world = [(x, z + pin_world_z) for (x, z) in nema_local]
        nema_rot = [rot(p) for p in nema_world]
        ax.add_patch(mp.Polygon(nema_rot, closed=True,
                                edgecolor="black", facecolor="#3d3d40",
                                lw=0.5))

        # LA: line from base clevis (la_lower_x, la_lower_z) to the rotated
        # tab attach point.
        tab_world = (tab_local[0], tab_local[1] + pin_world_z)
        tab_rot = rot(tab_world)
        la_len = math.hypot(tab_rot[0] - la_lower_x,
                            tab_rot[1] - la_lower_z)
        ax.plot([la_lower_x, tab_rot[0]],
                [la_lower_z, tab_rot[1]],
                color="#1f4f8a", lw=4, solid_capstyle="round")
        ax.plot([la_lower_x, tab_rot[0]],
                [la_lower_z, tab_rot[1]],
                color="#3d6fb8", lw=2, solid_capstyle="round")
        ax.text(0.5 * (la_lower_x + tab_rot[0]) + 6,
                0.5 * (la_lower_z + tab_rot[1]),
                f"LA = {la_len:.0f} mm", fontsize=7, color="#1f4f8a")

        # Powder-flow arrow at 0° only (always falls straight down).
        if tilt_deg == 0:
            ax.annotate("", xy=(cm.HINGE_X, cm.SCALE_H + cm.CUP_H - 2),
                        xytext=(cm.HINGE_X, pin_world_z - 14),
                        arrowprops=dict(arrowstyle="->", color="#1f6f3f",
                                        lw=1.0))

        ax.set_title(f"Tilt = {tilt_deg}°")
        ax.set_xlim(cm.BP_X_OFFSET - 30, cm.BP_X_OFFSET + cm.BP_LEN + 30)
        ax.set_ylim(-15, 380)
        ax.set_xlabel("X (mm)")
        ax.grid(True, ls=":", lw=0.3, alpha=0.4)

    axes[0].set_ylabel("Z (mm, floor at 0)")
    fig.suptitle("Tilt 0° → 45° → 90° about the hinge axis "
                 "(driven by the linear actuator)",
                 fontsize=11)
    fig.tight_layout()
    _save(fig, "rotation_0_45_90")
    print("wrote diagrams/rotation_0_45_90.{svg,png}")


# ---------------------------------------------------------------------------
# Powder flow diagram
# ---------------------------------------------------------------------------

def diagram_powder_flow() -> None:
    fig, ax = plt.subplots(figsize=(10, 7))
    ax.set_aspect("equal")
    pin_world_z = cm.LEG_H + cm.BP_THK + 50.0 - 4.0
    mp_z_lift = cm.AUGER_OD / 2.0 + cm.BRACKET_FLANGE_T

    # Floor + scale + cup.
    ax.axhline(0, color="0.5", lw=0.4)
    ax.add_patch(mp.Rectangle(
        (cm.HINGE_X - cm.SCALE_W / 2.0, 0),
        cm.SCALE_W, cm.SCALE_H,
        edgecolor="0.4", facecolor="0.85", lw=0.6))
    ax.text(cm.HINGE_X + cm.SCALE_W / 2.0 + 4, cm.SCALE_H / 2.0,
            "scale (placeholder)", fontsize=8, va="center")
    ax.add_patch(mp.Rectangle(
        (cm.HINGE_X - cm.CUP_OD / 2.0, cm.SCALE_H),
        cm.CUP_OD, cm.CUP_H,
        edgecolor="#7d6608", facecolor="#fcf3cf", lw=0.6))
    ax.text(cm.HINGE_X + cm.CUP_OD / 2.0 + 4, cm.SCALE_H + cm.CUP_H / 2.0,
            "cup (placeholder)", fontsize=8, va="center")

    # Baseplate + cut-out.
    ax.add_patch(mp.Rectangle(
        (cm.BP_X_OFFSET, cm.LEG_H), cm.BP_LEN, cm.BP_THK,
        edgecolor="black", facecolor="#f0f0e8", lw=0.6))
    ax.add_patch(mp.Rectangle(
        (cm.HINGE_X - cm.DISCHARGE_OPENING_D / 2.0, cm.LEG_H),
        cm.DISCHARGE_OPENING_D, cm.BP_THK,
        edgecolor="black", facecolor="white", lw=0.6))
    ax.text(cm.HINGE_X + cm.DISCHARGE_OPENING_D / 2.0 + 4,
            cm.LEG_H + cm.BP_THK / 2.0,
            "baseplate cut-out", fontsize=8, va="center")

    # Mounting plate at 0° tilt.
    ax.add_patch(mp.Rectangle(
        (0, pin_world_z + mp_z_lift),
        cm.MP_LEN, cm.MP_THK,
        edgecolor="black", facecolor="#eef2fa", lw=0.7))
    # Discharge notch in the plate.
    ax.add_patch(mp.Rectangle(
        (0, pin_world_z + mp_z_lift),
        cm.DISCHARGE_NOTCH_X, cm.MP_THK,
        edgecolor="black", facecolor="white", lw=0.6))
    # Discharge notch label moved to top so it doesn't sit over the bore.
    ax.text(cm.DISCHARGE_NOTCH_X / 2.0,
            pin_world_z + mp_z_lift + cm.MP_THK + 4,
            "mounting-plate notch", fontsize=8, ha="center")

    # Auger (side view) with discharge bore.
    ax.add_patch(mp.Rectangle(
        (0, pin_world_z - cm.AUGER_OD / 2.0),
        cm.AUGER_LEN, cm.AUGER_OD,
        edgecolor="#5a3a17", facecolor="#a37a48", lw=0.6))
    ax.add_patch(mp.Rectangle(
        (cm.AUGER_DISCHARGE_X - cm.AUGER_DISCHARGE_BORE / 2.0,
         pin_world_z - cm.AUGER_OD / 2.0),
        cm.AUGER_DISCHARGE_BORE, cm.AUGER_OD,
        edgecolor="black", facecolor="white", lw=0.5))
    ax.annotate(f"Ø{cm.AUGER_DISCHARGE_BORE:.0f} discharge bore",
                xy=(cm.AUGER_DISCHARGE_X,
                    pin_world_z + cm.AUGER_OD / 2.0),
                xytext=(cm.AUGER_DISCHARGE_X - 50,
                        pin_world_z + 50),
                fontsize=8, ha="left",
                arrowprops=dict(arrowstyle="->", lw=0.5, color="0.4"))

    # Hinge marker.
    ax.plot(cm.HINGE_X, pin_world_z, "o",
            markerfacecolor="white", markeredgecolor="#c0392b",
            markersize=8)
    ax.annotate("hinge axis = discharge axis",
                xy=(cm.HINGE_X, pin_world_z),
                xytext=(cm.HINGE_X + 40, pin_world_z + 80),
                color="#c0392b", fontsize=8,
                arrowprops=dict(arrowstyle="->", color="#c0392b", lw=0.5))

    # Powder-flow arrows: along the auger toward the bore, then down through
    # the bore, the plate notch, the baseplate cut-out, into the cup.
    ax.annotate("", xy=(cm.AUGER_DISCHARGE_X + 3, pin_world_z),
                xytext=(cm.AUGER_LEN - 6, pin_world_z),
                arrowprops=dict(arrowstyle="->", color="#1f6f3f", lw=1.5))
    ax.text((cm.AUGER_LEN + cm.AUGER_DISCHARGE_X) / 2.0,
            pin_world_z - 14,
            "powder driven along auger by NEMA-17",
            ha="center", fontsize=8, color="#1f6f3f")

    # Vertical arrow through bore → notch → cut-out → cup.
    ax.annotate("", xy=(cm.HINGE_X, cm.SCALE_H + cm.CUP_H - 4),
                xytext=(cm.HINGE_X,
                        pin_world_z - cm.AUGER_OD / 2.0 - 2),
                arrowprops=dict(arrowstyle="->", color="#1f6f3f", lw=1.8))
    ax.text(cm.HINGE_X - 6,
            (pin_world_z + cm.SCALE_H + cm.CUP_H) / 2.0,
            "powder falls through:\n discharge bore →\n plate notch →\n"
            " baseplate cut-out →\n cup",
            fontsize=8, ha="right", color="#1f6f3f")

    ax.set_xlim(cm.BP_X_OFFSET - 30, cm.BP_X_OFFSET + cm.BP_LEN + 30)
    ax.set_ylim(-15, 320)
    ax.set_xlabel("X (mm)")
    ax.set_ylabel("Z (mm)")
    ax.set_title("Powder flow path: auger → discharge bore → cup on scale")
    ax.grid(True, ls=":", lw=0.3, alpha=0.4)
    _save(fig, "powder_flow")
    print("wrote diagrams/powder_flow.{svg,png}")


def main() -> None:
    diagram_mounting_plate()
    diagram_baseplate()
    diagram_rotation()
    diagram_powder_flow()


if __name__ == "__main__":
    main()
