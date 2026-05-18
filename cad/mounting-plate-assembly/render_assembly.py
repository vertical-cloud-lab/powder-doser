"""Render full-assembly views + installation/rotation/powder-flow diagrams.

Loads the IMPORTED STLs from upstream PRs (#49, #51, #55) via
``vtkSTLReader`` (cadquery 2.7.0 has no ``importStl`` helper — see repo
memory) and positions them on top of the freshly-generated mounting
plate + baseplate + hinge pin from this package.

Per issue #62's hand drawing, every component sits on the TOP of the
mounting plate; the auger lies horizontal at Z=+19.74 mm directly above
the plate, supported by two PR#55 brackets bolted flange-DOWN.

Run from the package directory (xvfb required for headless VTK)::

    xvfb-run -a python3 render_assembly.py
"""
from __future__ import annotations

import math
from pathlib import Path

import cadquery as cq
import matplotlib
matplotlib.use("Agg")
import matplotlib.patches as patches
import matplotlib.pyplot as plt
import numpy as np
import vtk

from cad_model import (
    AUGER_LEN, AUGER_OD, BASE_T, BRK_FLANGE_T, BRK_FLANGE_W, BRK_FLANGE_D,
    BRK_MOUNT_HOLE_INSET_X, BRK_RING_CENTRE_LOCAL_Z, GEAR_BAND_FACE_W,
    GEAR_BAND_TIP_DIA, GEAR_CENTRE_DISTANCE, MOTOR_FACE_Y, NEMA11_BODY_L,
    NEMA11_BODY_W, NEMA11_FACE_HOLE_PITCH, NEMA11_PILOT_DIA, PINION_LEN,
    PINION_TIP_DIA, PLATE_L, PLATE_T, PLATE_W, PLATE_X_CENTRE, PLATE_X_MIN,
    PLATE_X_MAX, PLATE_Y_BACK, PLATE_Y_CENTRE, PLATE_Y_FRONT, TAP_PLATE_D,
    TAP_PLATE_T, TAP_PLATE_W, TAP_MOUNT_HOLE_INSET_X, WINDOW_L, WINDOW_W,
    WINDOW_Y, X_MOTOR, Y_BRK_FRONT, Y_BRK_REAR, Y_DISP, Y_GEAR_BAND, Y_REAR,
    Y_TAP, Z_AUG, Z_BASE_TOP, Z_MOTOR, YOKE_WEDGE_GAP, YOKE_WEDGE_THK,
    YOKE_WEDGE_TOP_Z, YOKE_WEDGE_Y_BACK, YOKE_EYE_OD, YOKE_X_INNER,
    build_baseplate, build_hinge_pin, build_mounting_plate,
)

HERE = Path(__file__).resolve().parent
ASM = HERE / "assembly"
ASM.mkdir(exist_ok=True)

IMG_W, IMG_H = 1400, 1000

# ----- colours --------------------------------------------------------------
COL_PLATE = (0.80, 0.82, 0.86)
COL_BASE = (0.62, 0.66, 0.72)
COL_AUGER = (0.90, 0.76, 0.45)
COL_BRACKET = (0.55, 0.72, 0.85)
COL_TAP_COLLAR = (0.70, 0.45, 0.85)
COL_TAP_MOUNT = (0.55, 0.40, 0.70)
COL_PINION = (0.45, 0.70, 0.55)
COL_MOTOR = (0.30, 0.30, 0.35)
COL_PIN = (0.85, 0.55, 0.20)


def _stl_actor(stl_path: Path, colour) -> vtk.vtkActor:
    r = vtk.vtkSTLReader()
    r.SetFileName(str(stl_path))
    r.Update()
    m = vtk.vtkPolyDataMapper()
    m.SetInputConnection(r.GetOutputPort())
    a = vtk.vtkActor()
    a.SetMapper(m)
    a.GetProperty().SetColor(*colour)
    a.GetProperty().SetSpecular(0.3)
    a.GetProperty().SetSpecularPower(15)
    return a


def _shape_actor(shape: cq.Shape, colour) -> vtk.vtkActor:
    pd = shape.toVtkPolyData(0.1, 0.5)
    m = vtk.vtkPolyDataMapper()
    m.SetInputData(pd)
    a = vtk.vtkActor()
    a.SetMapper(m)
    a.GetProperty().SetColor(*colour)
    a.GetProperty().SetSpecular(0.3)
    a.GetProperty().SetSpecularPower(15)
    return a


def _tilt_transform(tilt_deg: float, pre: vtk.vtkTransform | None = None) -> vtk.vtkTransform:
    """Compose: (optional pre) → translate hinge to origin → RotateX → translate back."""
    t = vtk.vtkTransform()
    t.PostMultiply()
    if pre is not None:
        t.Concatenate(pre)
    t.Translate(0, -Y_DISP, -Z_AUG)
    t.RotateX(-tilt_deg)
    t.Translate(0, Y_DISP, Z_AUG)
    return t


def _set_tilt(actor: vtk.vtkActor, tilt_deg: float,
              pre: vtk.vtkTransform | None = None) -> vtk.vtkActor:
    actor.SetUserTransform(_tilt_transform(tilt_deg, pre))
    return actor


# --------------------------------------------------------------------------- #
# Assembly actors.  All but the baseplate rotate about the hinge axis (the
# global X-axis through (Y_DISP, Z_AUG)) by `tilt_deg`.
# --------------------------------------------------------------------------- #
def build_assembly_actors(tilt_deg: float = 0.0) -> list[vtk.vtkActor]:
    actors: list[vtk.vtkActor] = []

    # ---- baseplate (never tilts; sits on the bench) ------------------------
    actors.append(_shape_actor(build_baseplate().val(), COL_BASE))

    # ---- mounting plate ----------------------------------------------------
    actors.append(_set_tilt(_shape_actor(build_mounting_plate().val(), COL_PLATE),
                            tilt_deg))

    # ---- imported AUGER: native frame has axis along +Z with the dispensing
    # end at z=0.  We want it horizontal along +Y with the dispensing end at
    # Y=Y_DISP and centred at X=0, Z=Z_AUG.  Rotation -90° about X maps
    # (X,Y,Z)→(X,Z,-Y) in PostMultiply: so a point at z=L ends up at y=L.
    # After rotation the dispensing end (originally z=0) is at y=0; we then
    # translate by (0, Y_DISP, Z_AUG) so the dispensing end lands at +Y_DISP
    # and the motor end at +Y_DISP-AUGER_LEN = Y_REAR.
    pre_auger = vtk.vtkTransform()
    pre_auger.PostMultiply()
    pre_auger.RotateX(-90)
    pre_auger.Translate(0, Y_DISP, Z_AUG)
    actors.append(_set_tilt(_stl_actor(
        HERE / "imported-parts/auger-geared/archimedes-auger-geared.stl",
        COL_AUGER), tilt_deg, pre_auger))

    # ---- imported BRACKETS (PR #55): native frame has flange-bottom on z=0
    # and the bore at z=BRK_RING_CENTRE_LOCAL_Z (≈19.74).  We bolt the
    # bracket FLANGE-DOWN to the plate TOP (z=0) so the bore lands at
    # z=+19.74 = Z_AUG exactly.  No rotation needed — just translate to
    # (0, cy, 0).
    bracket_stl = HERE / "imported-parts/auger-bracket/auger-bracket.stl"
    for cy in (Y_BRK_FRONT, Y_BRK_REAR):
        pre = vtk.vtkTransform()
        pre.PostMultiply()
        pre.Translate(0, cy, 0)
        actors.append(_set_tilt(_stl_actor(bracket_stl, COL_BRACKET),
                                tilt_deg, pre))

    # ---- imported TAP-COLLAR MOUNT PLATE (PR #51): same mounting style as
    # the brackets — flange-DOWN on plate top.  Translate to (0, Y_TAP, 0).
    pre_tm = vtk.vtkTransform()
    pre_tm.PostMultiply()
    pre_tm.Translate(0, Y_TAP, 0)
    actors.append(_set_tilt(_stl_actor(
        HERE / "imported-parts/tap-collar/mount_plate.stl",
        COL_TAP_MOUNT), tilt_deg, pre_tm))

    # ---- imported TAP COLLAR (PR #51) - wraps the auger at Y_TAP.  Native
    # frame: auger axis along Y, bore centre at z ≈ +30.25 (collar inner
    # tube above its own native base on z=0).  Translate so its bore centre
    # lands on the auger centreline (0, Y_TAP, Z_AUG).
    pre_tc = vtk.vtkTransform()
    pre_tc.PostMultiply()
    pre_tc.Translate(0, Y_TAP, Z_AUG - 30.25)
    actors.append(_set_tilt(_stl_actor(
        HERE / "imported-parts/tap-collar/tap_collar.stl",
        COL_TAP_COLLAR), tilt_deg, pre_tc))

    # ---- imported PINION (PR #49): native frame has axis along +Z, length
    # PINION_LEN.  After RotateX -90 it lies along +Y.  We then translate
    # so the pinion is centred on the gear band at (X_MOTOR, Y_GEAR_BAND,
    # Z_AUG) with the pinion's front face poking out of the motor.
    pre_p = vtk.vtkTransform()
    pre_p.PostMultiply()
    pre_p.RotateX(-90)
    pre_p.Translate(X_MOTOR, Y_GEAR_BAND - PINION_LEN / 2.0, Z_AUG)
    actors.append(_set_tilt(_stl_actor(
        HERE / "imported-parts/auger-geared/stepper-pinion.stl",
        COL_PINION), tilt_deg, pre_p))

    # ---- NEMA 11 motor body (drawn as a box for visualisation; the real
    # part is part of the assembly-preview in PR #49 but we want it sized
    # and located against the integrated boss on our plate top).  Body
    # centred at (X_MOTOR, MOTOR_FACE_Y - NEMA11_BODY_L/2, Z_MOTOR).
    motor_box = (
        cq.Workplane("XY")
        .box(NEMA11_BODY_W, NEMA11_BODY_L, NEMA11_BODY_W, centered=(True, True, True))
        .val()
    )
    pre_m = vtk.vtkTransform()
    pre_m.PostMultiply()
    pre_m.Translate(X_MOTOR, MOTOR_FACE_Y - NEMA11_BODY_L / 2.0, Z_MOTOR)
    actors.append(_set_tilt(_shape_actor(motor_box, COL_MOTOR), tilt_deg, pre_m))

    # ---- HINGE PIN ---------------------------------------------------------
    pre_hp = vtk.vtkTransform()
    pre_hp.PostMultiply()
    pre_hp.Translate(0, Y_DISP, Z_AUG)
    actors.append(_set_tilt(_shape_actor(build_hinge_pin().val(), COL_PIN),
                            tilt_deg, pre_hp))

    return actors


def render_assembly_view(out_path: Path, view: str, tilt_deg: float = 0.0) -> None:
    ren = vtk.vtkRenderer()
    ren.SetBackground(0.97, 0.97, 0.98)
    for a in build_assembly_actors(tilt_deg):
        ren.AddActor(a)

    win = vtk.vtkRenderWindow()
    win.SetOffScreenRendering(1)
    win.SetSize(IMG_W, IMG_H)
    win.AddRenderer(ren)

    cam = ren.GetActiveCamera()
    cam.SetFocalPoint(PLATE_X_CENTRE, 0, Z_AUG)
    diag = 380.0
    if view == "iso":
        cam.SetPosition(PLATE_X_CENTRE + diag, -diag * 1.0, Z_AUG + diag * 0.6)
        cam.SetViewUp(0, 0, 1)
    elif view == "front":
        cam.SetPosition(PLATE_X_CENTRE, -diag, Z_AUG)
        cam.SetViewUp(0, 0, 1)
    elif view == "top":
        cam.SetPosition(PLATE_X_CENTRE, 0, diag)
        cam.SetViewUp(0, 1, 0)
    elif view == "side":
        cam.SetPosition(PLATE_X_CENTRE + diag, 0, Z_AUG)
        cam.SetViewUp(0, 0, 1)
    ren.ResetCamera()

    win.Render()
    w2i = vtk.vtkWindowToImageFilter()
    w2i.SetInput(win)
    w2i.SetInputBufferTypeToRGBA()
    w2i.ReadFrontBufferOff()
    w2i.Update()
    writer = vtk.vtkPNGWriter()
    writer.SetFileName(str(out_path))
    writer.SetInputConnection(w2i.GetOutputPort())
    writer.Write()
    print(f"  → {out_path.relative_to(HERE)}")


# --------------------------------------------------------------------------- #
# Diagrams (matplotlib)
# --------------------------------------------------------------------------- #
def installation_diagram(out_path: Path) -> None:
    """Top-down annotated map of every mounting hole on the mounting plate.

    Annotations follow the issue #62 layout: hinge at the bottom (the +Y
    end), components on the TOP surface of an asymmetric plate.
    """
    fig, ax = plt.subplots(figsize=(11, 8.5), dpi=140)
    ax.set_aspect("equal")
    ax.set_title("Mounting plate (TOP view, components on TOP surface)\n"
                 "asymmetric: clear side at $-X$, components at $+X$")
    ax.set_xlabel("X (mm)")
    ax.set_ylabel("Y (mm)")

    # Plate outline
    ax.add_patch(patches.Rectangle((PLATE_X_MIN, PLATE_Y_BACK),
                                   PLATE_W, PLATE_L,
                                   facecolor="#e8e8ec", edgecolor="#444", lw=1.5))

    # Yoke wedges (projected as rectangles at the +Y edge, with eyes
    # projecting forward)
    for sx in (+YOKE_X_INNER, -YOKE_X_INNER):
        ax.add_patch(patches.Rectangle((sx - YOKE_WEDGE_THK / 2, YOKE_WEDGE_Y_BACK),
                                       YOKE_WEDGE_THK,
                                       PLATE_Y_FRONT - YOKE_WEDGE_Y_BACK,
                                       facecolor="#d0d0d8", edgecolor="#444", lw=1.2))
        ax.add_patch(patches.Circle((sx, Y_DISP), YOKE_EYE_OD / 2,
                                    facecolor="#bcbcc6",
                                    edgecolor="#444", lw=1.2))
        ax.add_patch(patches.Circle((sx, Y_DISP), 5.4 / 2, facecolor="white",
                                    edgecolor="#444", lw=0.8))

    # Powder-fall slot through plate
    slot_l = 30.0
    slot_y_centre = PLATE_Y_FRONT - slot_l / 2 + 2
    ax.add_patch(patches.Rectangle((-YOKE_WEDGE_GAP / 2, slot_y_centre - slot_l / 2),
                                   YOKE_WEDGE_GAP, slot_l, facecolor="white",
                                   edgecolor="#444", lw=1.0, ls="--"))

    # Gear-band clearance slot
    gb_x_min = -(GEAR_BAND_TIP_DIA / 2.0) - 2.0
    gb_x_max = +X_MOTOR + PINION_TIP_DIA / 2.0 + 2.0
    gb_w = gb_x_max - gb_x_min
    gb_l = GEAR_BAND_FACE_W + 8.0
    ax.add_patch(patches.Rectangle((gb_x_min, Y_GEAR_BAND - gb_l / 2),
                                   gb_w, gb_l, facecolor="white",
                                   edgecolor="#444", lw=1.0, ls="--"))

    # Hole groups
    def add_hole_group(cy, x_spacing, dia, label, colour, label_x=None):
        for sx in (+x_spacing / 2, -x_spacing / 2):
            ax.add_patch(patches.Circle((sx, cy), dia / 2, facecolor=colour,
                                        edgecolor="black", lw=0.8))
        ax.annotate(label, xy=(0, cy),
                    xytext=(PLATE_X_MAX + 12, cy),
                    fontsize=9, va="center", ha="left",
                    arrowprops=dict(arrowstyle="-", color="black", lw=0.6))

    add_hole_group(Y_BRK_FRONT, 48.0, 3.4,
                   "Front bracket (#55) — 2 × M3 @ X=±24", "#3a78b8")
    add_hole_group(Y_TAP,       48.0, 3.4,
                   "Tap-collar mount (#51) — 2 × M3 @ X=±24", "#6a3a8b")
    add_hole_group(Y_BRK_REAR,  48.0, 3.4,
                   "Rear bracket (#55) — 2 × M3 @ X=±24", "#3a78b8")

    # NEMA 11 motor face: 4 × M3 + Ø22 pilot at (X_MOTOR, MOTOR_FACE_Y)
    pitch = NEMA11_FACE_HOLE_PITCH
    # In top view the boss is at +Y of the motor body (at Y=MOTOR_FACE_Y).
    # Project the face holes onto the X-Y plane (they're actually in X-Z).
    # Draw a vertical-face indicator instead.
    ax.add_patch(patches.Rectangle((X_MOTOR - NEMA11_BODY_W / 2 - 4,
                                    MOTOR_FACE_Y - 6),
                                   NEMA11_BODY_W + 8, 6,
                                   facecolor="#88b88f", edgecolor="black",
                                   lw=0.8, alpha=0.6,
                                   label="NEMA 11 mount boss (vertical)"))
    ax.add_patch(patches.Rectangle((X_MOTOR - NEMA11_BODY_W / 2,
                                    MOTOR_FACE_Y - NEMA11_BODY_L),
                                   NEMA11_BODY_W, NEMA11_BODY_L,
                                   facecolor="#888", edgecolor="black",
                                   lw=0.8, alpha=0.4))
    ax.annotate("NEMA 11 (#49) — 4 × M3 @ 23 mm pitch + Ø22 pilot\n"
                "(face holes on the +Y vertical face of the boss)",
                xy=(X_MOTOR, MOTOR_FACE_Y - NEMA11_BODY_L / 2),
                xytext=(PLATE_X_MAX + 12, MOTOR_FACE_Y - NEMA11_BODY_L / 2),
                fontsize=9, va="center", ha="left",
                arrowprops=dict(arrowstyle="-", color="black", lw=0.6))

    # Actuator lug (on UNDERSIDE — dashed)
    ax.add_patch(patches.Rectangle((-6, -60 - 4), 12, 8, facecolor="#b88a3a",
                                   edgecolor="black", lw=0.8, alpha=0.4))
    ax.annotate("Linear-actuator rod-end lug (UNDERSIDE)",
                xy=(0, -60), xytext=(PLATE_X_MAX + 12, -60),
                fontsize=9, va="center", ha="left",
                arrowprops=dict(arrowstyle="-", color="black", lw=0.6))

    # Auger projection
    ax.plot([0, 0], [Y_REAR, Y_DISP], color="#a07020", lw=1.0, ls=":",
            label="Auger centreline (above plate)")
    ax.plot([0], [Y_GEAR_BAND], "o", color="#a07020", ms=8, mfc="none",
            label=f"Gear band (Y={Y_GEAR_BAND:.1f})")
    ax.plot([X_MOTOR], [Y_GEAR_BAND], "x", color="#3a8b48", ms=10,
            label="Pinion centreline")

    # Annotate axis labels
    ax.annotate("HINGE AXIS\n(along X, through dispensing point)",
                xy=(0, Y_DISP + 2),
                xytext=(PLATE_X_MIN - 8, Y_DISP),
                fontsize=8, va="center", ha="right", color="red",
                arrowprops=dict(arrowstyle="->", color="red", lw=0.8))
    ax.annotate("DISPENSING POINT", xy=(0, Y_DISP),
                xytext=(PLATE_X_MIN - 8, Y_DISP - 12),
                fontsize=8, va="center", ha="right", color="red",
                arrowprops=dict(arrowstyle="->", color="red", lw=0.6))

    ax.legend(loc="lower left", fontsize=8)
    ax.set_xlim(PLATE_X_MIN - 70, PLATE_X_MAX + 130)
    ax.set_ylim(PLATE_Y_BACK - 20, Y_DISP + 20)
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(out_path)
    plt.close(fig)
    print(f"  → {out_path.relative_to(HERE)}")


def rotation_diagram(out_path: Path) -> None:
    """Side view of the assembly at tilt = 0°, 45°, 90° (Y-Z plane)."""
    fig, axes = plt.subplots(1, 3, figsize=(15, 7), dpi=140)
    fig.suptitle("Rotation about the auger dispensing point — hinge axis is "
                 f"X through (Y={Y_DISP:.0f}, Z={Z_AUG:.1f})\n"
                 "dispensing point literally does not move (red dot)")
    tilts = [0, 45, 90]
    L_act = []

    # Actuator pivots in untilted frame
    rod_y0 = -60.0
    rod_z0 = -PLATE_T - (24.0 - 6)
    base_y = -110.0
    base_z = Z_BASE_TOP + BASE_T + (30.0 - 6)
    hy, hz = Y_DISP, Z_AUG

    for ax, tilt in zip(axes, tilts):
        ax.set_aspect("equal")
        ax.set_title(f"tilt = {tilt}°")

        # Baseplate (side projection)
        ax.add_patch(patches.Rectangle((-160, Z_BASE_TOP), 320, BASE_T,
                                       facecolor="#c0c0c8", edgecolor="#444"))

        c, s = math.cos(math.radians(-tilt)), math.sin(math.radians(-tilt))

        def rot(y, z):
            dy, dz = y - hy, z - hz
            return hy + c * dy - s * dz, hz + s * dy + c * dz

        # Mounting plate
        pts_plate = [(PLATE_Y_BACK, -PLATE_T), (PLATE_Y_FRONT, -PLATE_T),
                     (PLATE_Y_FRONT, 0), (PLATE_Y_BACK, 0)]
        ax.add_patch(patches.Polygon([rot(y, z) for y, z in pts_plate],
                                     facecolor="#d8d8e0", edgecolor="#333"))

        # Auger (above the plate at Z=Z_AUG)
        pts_aug = [(Y_REAR, Z_AUG - AUGER_OD / 2),
                   (Y_DISP, Z_AUG - AUGER_OD / 2),
                   (Y_DISP, Z_AUG + AUGER_OD / 2),
                   (Y_REAR, Z_AUG + AUGER_OD / 2)]
        ax.add_patch(patches.Polygon([rot(y, z) for y, z in pts_aug],
                                     facecolor="#e8c98a", edgecolor="#a07020"))
        # Gear band
        pts_gb = [(Y_GEAR_BAND - GEAR_BAND_FACE_W / 2, Z_AUG - GEAR_BAND_TIP_DIA / 2),
                  (Y_GEAR_BAND + GEAR_BAND_FACE_W / 2, Z_AUG - GEAR_BAND_TIP_DIA / 2),
                  (Y_GEAR_BAND + GEAR_BAND_FACE_W / 2, Z_AUG + GEAR_BAND_TIP_DIA / 2),
                  (Y_GEAR_BAND - GEAR_BAND_FACE_W / 2, Z_AUG + GEAR_BAND_TIP_DIA / 2)]
        ax.add_patch(patches.Polygon([rot(y, z) for y, z in pts_gb],
                                     facecolor="#c8a060", edgecolor="#604020"))

        # Motor body
        mb_y = MOTOR_FACE_Y - NEMA11_BODY_L
        pts_mb = [(mb_y, Z_MOTOR - NEMA11_BODY_W / 2),
                  (MOTOR_FACE_Y, Z_MOTOR - NEMA11_BODY_W / 2),
                  (MOTOR_FACE_Y, Z_MOTOR + NEMA11_BODY_W / 2),
                  (mb_y, Z_MOTOR + NEMA11_BODY_W / 2)]
        ax.add_patch(patches.Polygon([rot(y, z) for y, z in pts_mb],
                                     facecolor="#444", edgecolor="#222"))

        # Yoke wedge (single profile in side view)
        pts_wedge = [(YOKE_WEDGE_Y_BACK, 0), (PLATE_Y_FRONT, 0),
                     (PLATE_Y_FRONT, YOKE_WEDGE_TOP_Z)]
        ax.add_patch(patches.Polygon([rot(y, z) for y, z in pts_wedge],
                                     facecolor="#bcbcc6", edgecolor="#444"))

        # Hinge axis marker (always at the same physical point!)
        ax.plot(*rot(hy, hz), "o", color="red", ms=10, zorder=10)
        # Baseplate tang
        pts_tang = [(Y_DISP - 10, Z_BASE_TOP + BASE_T),
                    (Y_DISP + 10, Z_BASE_TOP + BASE_T),
                    (Y_DISP + 10, Z_AUG + 8),
                    (Y_DISP - 10, Z_AUG + 8)]
        ax.add_patch(patches.Polygon(pts_tang, facecolor="#a8a8b4",
                                     edgecolor="#444"))

        # Actuator line
        rod_y, rod_z = rot(rod_y0, rod_z0)
        ax.plot([base_y, rod_y], [base_z, rod_z], "-", color="#666", lw=2.5)
        L = math.hypot(rod_y - base_y, rod_z - base_z)
        L_act.append(L)
        ax.text((base_y + rod_y) / 2, (base_z + rod_z) / 2 + 8,
                f"actuator L = {L:.1f} mm", ha="center", fontsize=9,
                bbox=dict(boxstyle="round", facecolor="white", edgecolor="#666"))

        ax.set_xlim(-200, 200)
        ax.set_ylim(-130, 280)
        ax.grid(True, alpha=0.3)
        ax.set_xlabel("Y (mm)")
        if ax is axes[0]:
            ax.set_ylabel("Z (mm)")

    fig.tight_layout()
    fig.savefig(out_path)
    plt.close(fig)
    print(f"  → {out_path.relative_to(HERE)}  (actuator lengths: "
          + ", ".join(f"{t}°={L:.1f}mm" for t, L in zip(tilts, L_act)) + ")")


def powder_flow_diagram(out_path: Path) -> None:
    """Side view at 90° tilt showing the powder path auger → window → cup."""
    fig, ax = plt.subplots(figsize=(11, 9), dpi=140)
    ax.set_aspect("equal")
    ax.set_title("Powder flow (assembly tilted 90° about the auger dispensing point)")

    tilt = 90
    hy, hz = Y_DISP, Z_AUG
    c, s = math.cos(math.radians(-tilt)), math.sin(math.radians(-tilt))

    def rot(y, z):
        dy, dz = y - hy, z - hz
        return hy + c * dy - s * dz, hz + s * dy + c * dz

    # Baseplate
    ax.add_patch(patches.Rectangle((-160, Z_BASE_TOP), 320, BASE_T,
                                   facecolor="#c0c0c8", edgecolor="#444"))
    # Powder window cutout
    ax.add_patch(patches.Rectangle((WINDOW_Y - WINDOW_L / 2, Z_BASE_TOP - 1),
                                   WINDOW_L, BASE_T + 2,
                                   facecolor="white", edgecolor="#444", ls="--"))
    # Mounting plate rotated
    pts_plate = [(PLATE_Y_BACK, -PLATE_T), (PLATE_Y_FRONT, -PLATE_T),
                 (PLATE_Y_FRONT, 0), (PLATE_Y_BACK, 0)]
    ax.add_patch(patches.Polygon([rot(y, z) for y, z in pts_plate],
                                 facecolor="#d8d8e0", edgecolor="#333"))
    # Auger rotated
    pts_aug = [(Y_REAR, Z_AUG - AUGER_OD / 2),
               (Y_DISP, Z_AUG - AUGER_OD / 2),
               (Y_DISP, Z_AUG + AUGER_OD / 2),
               (Y_REAR, Z_AUG + AUGER_OD / 2)]
    ax.add_patch(patches.Polygon([rot(y, z) for y, z in pts_aug],
                                 facecolor="#e8c98a", edgecolor="#a07020"))

    # Cup + scale below the powder window
    scale_y = WINDOW_Y
    scale_z = Z_BASE_TOP - 65
    ax.add_patch(patches.Rectangle((scale_y - 40, scale_z), 80, 12,
                                   facecolor="#222", edgecolor="black"))
    ax.text(scale_y, scale_z + 6, "scale", color="white",
            ha="center", va="center", fontsize=8)
    ax.add_patch(patches.Polygon([(scale_y - 22, scale_z + 12),
                                  (scale_y + 22, scale_z + 12),
                                  (scale_y + 18, scale_z + 52),
                                  (scale_y - 18, scale_z + 52)],
                                 closed=True, facecolor="#eedf9c",
                                 edgecolor="#7a5a20", alpha=0.6))
    ax.text(scale_y, scale_z + 32, "cup", color="#604020",
            ha="center", va="center", fontsize=10)

    # Powder path arrow: from auger dispensing point (= hinge point) down
    disp_y, disp_z = hy, hz
    ax.annotate("", xy=(scale_y, scale_z + 50), xytext=(disp_y, disp_z),
                arrowprops=dict(arrowstyle="->", color="#a07020", lw=3))
    ax.text(disp_y + 8, (disp_z + scale_z + 50) / 2,
            "powder falls straight\ndown through window\ninto cup on scale",
            fontsize=10, color="#604020")
    ax.plot([disp_y], [disp_z], "o", color="red", ms=10, zorder=10)
    ax.annotate("dispensing point\n(also = hinge axis)",
                xy=(disp_y, disp_z), xytext=(disp_y - 80, disp_z + 30),
                fontsize=9, color="red",
                arrowprops=dict(arrowstyle="->", color="red", lw=0.8))

    ax.set_xlim(-200, 260)
    ax.set_ylim(scale_z - 20, 260)
    ax.set_xlabel("Y (mm)")
    ax.set_ylabel("Z (mm)")
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(out_path)
    plt.close(fig)
    print(f"  → {out_path.relative_to(HERE)}")


def main() -> None:
    # Full-assembly renders at tilt = 0
    for v in ("iso", "front", "top", "side"):
        render_assembly_view(ASM / f"assembly_{v}.png", v, tilt_deg=0.0)
    # Tilted iso at 45° and 90° for completeness
    render_assembly_view(ASM / "assembly_45deg_iso.png", "iso", tilt_deg=45.0)
    render_assembly_view(ASM / "assembly_90deg_iso.png", "iso", tilt_deg=90.0)

    # Diagrams
    installation_diagram(ASM / "installation_diagram.png")
    rotation_diagram(ASM / "rotation_0_45_90.png")
    powder_flow_diagram(ASM / "powder_flow.png")

    # Combined-STEP export of the NEW parts only (the imported parts ship
    # their own STEPs upstream).
    asm_step = ASM / "full_assembly.step"
    a = cq.Assembly()
    a.add(build_mounting_plate(), name="mounting_plate", color=cq.Color(*COL_PLATE))
    a.add(build_baseplate(), name="baseplate", color=cq.Color(*COL_BASE))
    a.add(build_hinge_pin().translate((0, Y_DISP, Z_AUG)), name="hinge_pin",
          color=cq.Color(*COL_PIN))
    a.save(str(asm_step))
    print(f"  → {asm_step.relative_to(HERE)}")


if __name__ == "__main__":
    main()
