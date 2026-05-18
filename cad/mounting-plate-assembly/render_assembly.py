"""Render full-assembly views + installation/rotation/powder-flow diagrams.

Loads the IMPORTED STLs from upstream PRs (#49, #51, #55) via
``vtkSTLReader`` (cadquery 2.7.0 has no importStl helper — repo memory)
and places them against the freshly-generated mounting_plate +
baseplate + hinge_pin from this package.

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
    BRK_MOUNT_HOLE_INSET_X, GEAR_BAND_FACE_W, GEAR_BAND_TIP_DIA,
    GEAR_CENTRE_DISTANCE, MOTOR_FACE_Y, NEMA11_BODY_L, NEMA11_BODY_W,
    PINION_LEN, PINION_TIP_DIA, PLATE_L, PLATE_T, PLATE_W, TAP_PLATE_D,
    TAP_PLATE_T, TAP_PLATE_W, TAP_MOUNT_HOLE_INSET_X, WINDOW_L, WINDOW_W,
    WINDOW_Y, X_MOTOR, Y_BRK_FRONT, Y_BRK_REAR, Y_DISP, Y_GEAR_BAND, Y_REAR,
    Y_TAP, Z_AUG, Z_MOTOR, build_baseplate, build_hinge_pin,
    build_mounting_plate,
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


def _xform(actor: vtk.vtkActor, rx=0.0, ry=0.0, rz=0.0,
           tx=0.0, ty=0.0, tz=0.0) -> vtk.vtkActor:
    """Apply rotations then translation. Rotations are intrinsic Y-X-Z order."""
    t = vtk.vtkTransform()
    t.PostMultiply()
    if rx:
        t.RotateX(rx)
    if ry:
        t.RotateY(ry)
    if rz:
        t.RotateZ(rz)
    t.Translate(tx, ty, tz)
    actor.SetUserTransform(t)
    return actor


# --------------------------------------------------------------------------- #
# Build a list of (actor, label) for the full assembly, with the hinge at
# the given tilt angle (deg, 0 = horizontal auger, 90 = auger straight down).
# --------------------------------------------------------------------------- #
def build_assembly_actors(tilt_deg: float = 0.0) -> list[vtk.vtkActor]:
    actors: list[vtk.vtkActor] = []

    # ---- baseplate (never tilts; sits on bench) ----------------------------
    actors.append(_shape_actor(build_baseplate().val(), COL_BASE))

    # ---- everything else rotates about the hinge axis (x-axis) at the
    # dispense point (Y_DISP, Z_AUG) by `tilt_deg`. We build a single
    # transform that we'll apply to every tilting actor.
    def tilted(actor: vtk.vtkActor, extra_pre: vtk.vtkTransform | None = None) -> vtk.vtkActor:
        t = vtk.vtkTransform()
        t.PostMultiply()
        if extra_pre is not None:
            t.Concatenate(extra_pre)
        # Translate so hinge axis is at origin, rotate about X, translate back.
        t.Translate(0, -Y_DISP, -Z_AUG)
        t.RotateX(-tilt_deg)
        t.Translate(0, Y_DISP, Z_AUG)
        actor.SetUserTransform(t)
        return actor

    # ---- mounting plate ----------------------------------------------------
    actors.append(tilted(_shape_actor(build_mounting_plate().val(), COL_PLATE)))

    # ---- imported AUGER: native orientation has axis along Z, dispensing
    # end at Z=0. We need it horizontal along +Y, dispensing end at +Y_DISP,
    # centred at X=0 and Z=Z_AUG. Rotation: rotate -90° about X so the +Z
    # axis maps to +Y. Then translate so the (originally) z=0 end sits at
    # y=Y_DISP and the auger lies at z=Z_AUG.
    auger_stl = HERE / "imported-parts/auger-geared/archimedes-auger-geared.stl"
    a_auger = _stl_actor(auger_stl, COL_AUGER)
    # rotate -90° about X: (X,Y,Z) -> (X, Z, -Y).  Original Z=0..250 becomes
    # Y=0..250 (after the next translate we put the dispensing end at Y_DISP).
    pre_auger = vtk.vtkTransform()
    pre_auger.PostMultiply()
    pre_auger.RotateX(-90)
    # After rotate: dispensing end is at Y=0 — push it to Y_DISP, drop to Z_AUG
    pre_auger.Translate(0, Y_DISP - AUGER_LEN, Z_AUG)
    # Wait: rotation maps z=0 to y=0, z=AUGER_LEN to y=AUGER_LEN. So the
    # dispensing end (originally z=0) ends up at y=0; we want it at +Y_DISP,
    # so translate +Y_DISP. The motor end (originally z=AUGER_LEN) ends up
    # at y=-AUGER_LEN after rotation, so we want it at Y_DISP - AUGER_LEN.
    # Build the right transform:
    pre_auger = vtk.vtkTransform()
    pre_auger.PostMultiply()
    pre_auger.RotateX(-90)
    pre_auger.Translate(0, Y_DISP, Z_AUG)
    a_auger.SetUserTransform(pre_auger)
    actors.append(tilted(a_auger, pre_auger))

    # ---- imported BRACKETS (PR #55): native frame is flange-bottom on z=0
    # plane, bore axis along Y, plate 60×25 along X×Y. We mount flange-UP
    # to plate underside (so flip 180° about X), centre at (0, Y_BRK_*,
    # plate-bottom = -PLATE_T). After flipping, flange-top (originally Z=0)
    # becomes the new bottom; we want flange-bottom mating against plate
    # underside, so place the new top of the flipped bracket at z=-PLATE_T.
    bracket_stl = HERE / "imported-parts/auger-bracket/auger-bracket.stl"
    for cy in (Y_BRK_FRONT, Y_BRK_REAR):
        a = _stl_actor(bracket_stl, COL_BRACKET)
        t = vtk.vtkTransform()
        t.PostMultiply()
        # Flip about X axis so the flange (originally bottom) goes on top
        t.RotateX(180)
        # After flip, the bracket's original z=0 face is now at z=0 facing -Z;
        # we want this face to mate against plate underside at z=-PLATE_T.
        # The original z=0 face is now the TOP face of the flipped bracket.
        # We want it at z=-PLATE_T, so translate by (-PLATE_T).
        t.Translate(0, cy, -PLATE_T)
        a.SetUserTransform(t)
        actors.append(tilted(a, t))

    # ---- imported TAP-COLLAR MOUNT PLATE (PR #51): native plate 60×12×14,
    # plate-bottom on z=0 mating face, with hardstop column rising above.
    # Mount the SAME way as the brackets: flange-UP to plate underside.
    tap_mount_stl = HERE / "imported-parts/tap-collar/mount_plate.stl"
    a_tm = _stl_actor(tap_mount_stl, COL_TAP_MOUNT)
    t_tm = vtk.vtkTransform()
    t_tm.PostMultiply()
    t_tm.RotateX(180)
    t_tm.Translate(0, Y_TAP, -PLATE_T)
    a_tm.SetUserTransform(t_tm)
    actors.append(tilted(a_tm, t_tm))

    # ---- imported TAP COLLAR (PR #51) - wraps around the auger at Y_TAP
    tap_collar_stl = HERE / "imported-parts/tap-collar/tap_collar.stl"
    a_tc = _stl_actor(tap_collar_stl, COL_TAP_COLLAR)
    t_tc = vtk.vtkTransform()
    t_tc.PostMultiply()
    # Native frame: auger axis along Y, bore centred at z = COLLAR_CENTRE_Z
    # (≈30.25 mm above z=0). Flip 180° so the collar sits above its native
    # bottom, then translate so the bore centre lands on the auger centreline
    # (X=0, Y=Y_TAP, Z=Z_AUG). After flipping about X by 180°, the original
    # z=30.25 becomes z=-30.25; we want it at z=Z_AUG. So translate Z by
    # (Z_AUG - (-30.25)) = Z_AUG + 30.25.
    t_tc.RotateX(180)
    t_tc.Translate(0, Y_TAP, Z_AUG + 30.25)
    a_tc.SetUserTransform(t_tc)
    actors.append(tilted(a_tc, t_tc))

    # ---- imported PINION (PR #49): native frame has axis along Z, length
    # 16 mm. Pinion meshes with the auger gear band at Y=Y_GEAR_BAND,
    # X=+GEAR_CENTRE_DISTANCE, Z=Z_AUG (same as auger axis Z). After
    # rotating about X by -90 the pinion lies along +Y axis from y=0 to
    # y=PINION_LEN; we centre it on Y_GEAR_BAND.
    pinion_stl = HERE / "imported-parts/auger-geared/stepper-pinion.stl"
    a_p = _stl_actor(pinion_stl, COL_PINION)
    t_p = vtk.vtkTransform()
    t_p.PostMultiply()
    t_p.RotateX(-90)
    # After rotate -90 about X: original Z range [0, 16] maps to Y range
    # [0, 16] (since RotateX maps (X,Y,Z)→(X,Z,-Y); a point at z=L goes to
    # y=L after post-multiply). Centre pinion axially on the gear band.
    t_p.Translate(X_MOTOR, Y_GEAR_BAND - PINION_LEN / 2, Z_AUG)
    a_p.SetUserTransform(t_p)
    actors.append(tilted(a_p, t_p))

    # ---- NEMA 11 motor body (drawn as a box; PR #49 has it as part of
    # the assembly-preview STL but we want it separately so we can size
    # and locate it precisely against the integrated boss on our plate).
    motor_box = (
        cq.Workplane("XY")
        .box(NEMA11_BODY_W, NEMA11_BODY_L, NEMA11_BODY_W, centered=(True, True, True))
        .val()
    )
    a_m = _shape_actor(motor_box, COL_MOTOR)
    t_m = vtk.vtkTransform()
    t_m.PostMultiply()
    # Motor body centred at (X_MOTOR, MOTOR_FACE_Y - NEMA11_BODY_L/2, Z_MOTOR)
    t_m.Translate(X_MOTOR, MOTOR_FACE_Y - NEMA11_BODY_L / 2, Z_MOTOR)
    a_m.SetUserTransform(t_m)
    actors.append(tilted(a_m, t_m))

    # ---- HINGE PIN -------------------------------------------------------
    a_hp = _shape_actor(build_hinge_pin().val(), COL_PIN)
    t_hp = vtk.vtkTransform()
    t_hp.PostMultiply()
    t_hp.Translate(0, Y_DISP, Z_AUG)
    a_hp.SetUserTransform(t_hp)
    actors.append(tilted(a_hp, t_hp))

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
    cam.SetFocalPoint(0, 0, Z_AUG)
    diag = 350.0
    if view == "iso":
        cam.SetPosition(diag, -diag * 1.0, diag * 0.5)
        cam.SetViewUp(0, 0, 1)
    elif view == "front":
        cam.SetPosition(0, -diag, Z_AUG)
        cam.SetViewUp(0, 0, 1)
    elif view == "top":
        cam.SetPosition(0, 0, diag)
        cam.SetViewUp(0, 1, 0)
    elif view == "side":
        cam.SetPosition(diag, 0, Z_AUG)
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
    """Top-down annotated map of every mounting hole on the mounting plate."""
    fig, ax = plt.subplots(figsize=(11, 8), dpi=140)
    ax.set_aspect("equal")
    ax.set_title("Mounting plate — top-down installation map")
    ax.set_xlabel("X (mm)")
    ax.set_ylabel("Y (mm)")

    # Plate outline
    ax.add_patch(patches.Rectangle((-PLATE_W / 2, -PLATE_L / 2), PLATE_W, PLATE_L,
                                   facecolor="#e8e8ec", edgecolor="#444", lw=1.5))
    # Yoke arms (visual hint)
    eye_offset_x = 14.0 / 2 + 26.0 / 2  # YOKE_EYE_OD/2 + YOKE_EYE_GAP/2 = 20
    for sx in (+eye_offset_x, -eye_offset_x):
        ax.add_patch(patches.Rectangle((sx - 7, PLATE_L / 2),
                                       14, Y_DISP - PLATE_L / 2,
                                       facecolor="#d0d0d8", edgecolor="#444", lw=1.2))
        ax.add_patch(patches.Circle((sx, Y_DISP), 14 / 2, facecolor="#bcbcc6",
                                    edgecolor="#444", lw=1.2))
        ax.add_patch(patches.Circle((sx, Y_DISP), 5.4 / 2, facecolor="white",
                                    edgecolor="#444", lw=0.8))

    # Powder-fall slot (front)
    slot_w, slot_l = 26.0, 50.0
    ax.add_patch(patches.Rectangle((-slot_w / 2, PLATE_L / 2 - slot_l + 2),
                                   slot_w, slot_l, facecolor="white",
                                   edgecolor="#444", lw=1.0, ls="--"))

    # Hole groups
    def add_hole_group(cy, x_spacing, dia, label, colour):
        for sx in (+x_spacing / 2, -x_spacing / 2):
            ax.add_patch(patches.Circle((sx, cy), dia / 2, facecolor=colour,
                                        edgecolor="black", lw=0.8))
        ax.annotate(label, xy=(0, cy), xytext=(PLATE_W / 2 + 8, cy),
                    fontsize=9, va="center", ha="left",
                    arrowprops=dict(arrowstyle="-", color="black", lw=0.6))

    # Brackets (PR #55): 2 × M3 at X = ±24
    add_hole_group(Y_BRK_FRONT, 48.0, 3.4, "Bracket FRONT (#55) — 2 × M3 @ X=±24", "#3a78b8")
    add_hole_group(Y_BRK_REAR,  48.0, 3.4, "Bracket REAR  (#55) — 2 × M3 @ X=±24", "#3a78b8")
    # Tap-collar mount (PR #51): 2 × M3 at X = ±24
    add_hole_group(Y_TAP, 48.0, 3.4, "Tap-collar mount (#51) — 2 × M3 @ X=±24", "#6a3a8b")

    # NEMA 11 motor face holes + pilot (at (X_MOTOR, MOTOR_FACE_Y))
    pitch = 23.0
    for sx in (+pitch / 2, -pitch / 2):
        for sy in (+pitch / 2, -pitch / 2):
            ax.add_patch(patches.Circle((X_MOTOR + sx, MOTOR_FACE_Y + sy),
                                        3.4 / 2, facecolor="#3a8b48",
                                        edgecolor="black", lw=0.8))
    ax.add_patch(patches.Circle((X_MOTOR, MOTOR_FACE_Y), 22 / 2,
                                facecolor="white", edgecolor="black", lw=0.8))
    ax.annotate("NEMA 11 (#49) — 4 × M3 @ 23 mm pitch + Ø22 pilot",
                xy=(X_MOTOR, MOTOR_FACE_Y),
                xytext=(PLATE_W / 2 + 8, MOTOR_FACE_Y),
                fontsize=9, va="center", ha="left",
                arrowprops=dict(arrowstyle="-", color="black", lw=0.6))

    # Actuator lug
    ax.add_patch(patches.Rectangle((-6, -60 - 4), 12, 8, facecolor="#b88a3a",
                                   edgecolor="black", lw=0.8))
    ax.annotate("Linear-actuator rod-end pivot lug (M5)",
                xy=(0, -60), xytext=(PLATE_W / 2 + 8, -60),
                fontsize=9, va="center", ha="left",
                arrowprops=dict(arrowstyle="-", color="black", lw=0.6))

    # Auger projection (light dashed)
    ax.plot([0, 0], [-AUGER_LEN / 2, +AUGER_LEN / 2],
            color="#a07020", lw=1.0, ls=":", label="Auger centreline")
    ax.plot([0], [Y_GEAR_BAND], "o", color="#a07020", ms=8, mfc="none",
            label=f"Gear band (Y={Y_GEAR_BAND:.1f})")
    ax.plot([X_MOTOR], [Y_GEAR_BAND], "x", color="#3a8b48", ms=10,
            label="Pinion centreline")

    ax.legend(loc="lower left", fontsize=8)
    ax.set_xlim(-PLATE_W / 2 - 5, PLATE_W / 2 + 110)
    ax.set_ylim(-PLATE_L / 2 - 20, Y_DISP + 25)
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(out_path)
    plt.close(fig)
    print(f"  → {out_path.relative_to(HERE)}")


def rotation_diagram(out_path: Path) -> None:
    """Side view of the assembly at tilt = 0°, 45°, 90°."""
    fig, axes = plt.subplots(1, 3, figsize=(15, 7), dpi=140)
    fig.suptitle("Rotation about the auger dispense axis (hinge axis = X through Y=+125, Z=Z_AUG)")
    tilts = [0, 45, 90]
    L_act = []  # required actuator length for each tilt

    # Pivots: rod-end on the plate at (X=0, Y=ACT_LUG_Y, Z=-PLATE_T-(ACT_LUG_H-6))
    #         base on the baseplate at (X=0, Y=ACT_BASE_Y, Z=BASE_T+(ACT_BASE_H-6))
    rod_y0, rod_z0 = -60.0, -PLATE_T - (24.0 - 6)
    base_y, base_z = -110.0, 6.0 + (30.0 - 6)
    # Hinge axis at (Y_DISP, Z_AUG)
    hy, hz = Y_DISP, Z_AUG

    for ax, tilt in zip(axes, tilts):
        ax.set_aspect("equal")
        ax.set_title(f"tilt = {tilt}°")
        # Draw baseplate (side projection)
        ax.add_patch(patches.Rectangle((-160, 0), 320, BASE_T, facecolor="#c0c0c8",
                                       edgecolor="#444"))
        # Tilted assembly: rotate every point by -tilt about (hy, hz)
        c, s = math.cos(math.radians(-tilt)), math.sin(math.radians(-tilt))

        def rot(y, z):
            dy, dz = y - hy, z - hz
            return hy + c * dy - s * dz, hz + s * dy + c * dz

        # Mounting plate side projection (y from -PLATE_L/2 to PLATE_L/2,
        # z from -PLATE_T to 0)
        pts_plate = [(-PLATE_L / 2, -PLATE_T), (PLATE_L / 2, -PLATE_T),
                     (PLATE_L / 2, 0), (-PLATE_L / 2, 0)]
        ax.add_patch(patches.Polygon([rot(y, z) for y, z in pts_plate],
                                     facecolor="#d8d8e0", edgecolor="#333"))

        # Auger (a horizontal cylinder in local frame, drawn as rectangle)
        # spanning y = [-AUGER_LEN/2, +AUGER_LEN/2], z = Z_AUG ± AUGER_OD/2
        pts_aug = [(-AUGER_LEN / 2, Z_AUG - AUGER_OD / 2),
                   (+AUGER_LEN / 2, Z_AUG - AUGER_OD / 2),
                   (+AUGER_LEN / 2, Z_AUG + AUGER_OD / 2),
                   (-AUGER_LEN / 2, Z_AUG + AUGER_OD / 2)]
        ax.add_patch(patches.Polygon([rot(y, z) for y, z in pts_aug],
                                     facecolor="#e8c98a", edgecolor="#a07020"))
        # Gear band
        pts_gb = [(Y_GEAR_BAND - GEAR_BAND_FACE_W / 2, Z_AUG - GEAR_BAND_TIP_DIA / 2),
                  (Y_GEAR_BAND + GEAR_BAND_FACE_W / 2, Z_AUG - GEAR_BAND_TIP_DIA / 2),
                  (Y_GEAR_BAND + GEAR_BAND_FACE_W / 2, Z_AUG + GEAR_BAND_TIP_DIA / 2),
                  (Y_GEAR_BAND - GEAR_BAND_FACE_W / 2, Z_AUG + GEAR_BAND_TIP_DIA / 2)]
        ax.add_patch(patches.Polygon([rot(y, z) for y, z in pts_gb],
                                     facecolor="#c8a060", edgecolor="#604020"))

        # Hinge axis marker
        ax.plot(*rot(hy, hz), "o", color="red", ms=8)
        # Actuator line
        rod_y, rod_z = rot(rod_y0, rod_z0)
        ax.plot([base_y, rod_y], [base_z, rod_z], "-", color="#666", lw=2.5)
        L = math.hypot(rod_y - base_y, rod_z - base_z)
        L_act.append(L)
        ax.text((base_y + rod_y) / 2, (base_z + rod_z) / 2 + 8,
                f"actuator L = {L:.1f} mm", ha="center", fontsize=9,
                bbox=dict(boxstyle="round", facecolor="white", edgecolor="#666"))

        ax.set_xlim(-200, 200)
        ax.set_ylim(-180, 200)
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
    ax.set_title("Powder flow (assembly tilted 90° about the auger dispense axis)")

    # Rotate about hinge: tilt = 90°
    tilt = 90
    hy, hz = Y_DISP, Z_AUG
    c, s = math.cos(math.radians(-tilt)), math.sin(math.radians(-tilt))

    def rot(y, z):
        dy, dz = y - hy, z - hz
        return hy + c * dy - s * dz, hz + s * dy + c * dz

    # Baseplate
    ax.add_patch(patches.Rectangle((-160, 0), 320, BASE_T, facecolor="#c0c0c8",
                                   edgecolor="#444"))
    # Powder window (cutout)
    ax.add_patch(patches.Rectangle((WINDOW_Y - WINDOW_L / 2, -1),
                                   WINDOW_L, BASE_T + 2,
                                   facecolor="white", edgecolor="#444", ls="--"))
    # Mounting plate rotated
    pts_plate = [(-PLATE_L / 2, -PLATE_T), (PLATE_L / 2, -PLATE_T),
                 (PLATE_L / 2, 0), (-PLATE_L / 2, 0)]
    ax.add_patch(patches.Polygon([rot(y, z) for y, z in pts_plate],
                                 facecolor="#d8d8e0", edgecolor="#333"))
    # Auger
    pts_aug = [(-AUGER_LEN / 2, Z_AUG - AUGER_OD / 2),
               (+AUGER_LEN / 2, Z_AUG - AUGER_OD / 2),
               (+AUGER_LEN / 2, Z_AUG + AUGER_OD / 2),
               (-AUGER_LEN / 2, Z_AUG + AUGER_OD / 2)]
    ax.add_patch(patches.Polygon([rot(y, z) for y, z in pts_aug],
                                 facecolor="#e8c98a", edgecolor="#a07020"))

    # Cup on a scale below the powder window
    scale_y, scale_z = WINDOW_Y, -65
    ax.add_patch(patches.Rectangle((scale_y - 40, scale_z), 80, 12,
                                   facecolor="#222", edgecolor="black"))
    ax.text(scale_y, scale_z + 6, "scale", color="white", ha="center", va="center", fontsize=8)
    ax.add_patch(patches.Polygon([(scale_y - 22, scale_z + 12),
                                  (scale_y + 22, scale_z + 12),
                                  (scale_y + 18, scale_z + 52),
                                  (scale_y - 18, scale_z + 52)],
                                 closed=True, facecolor="#eedf9c",
                                 edgecolor="#7a5a20", alpha=0.6))

    # Powder path arrow: from auger dispense point (rot of (-AUGER_LEN/2, Z_AUG))
    disp_y, disp_z = rot(Y_DISP, Z_AUG)  # at hinge axis itself
    ax.annotate("", xy=(scale_y, scale_z + 50), xytext=(disp_y, disp_z),
                arrowprops=dict(arrowstyle="->", color="#a07020", lw=3))
    ax.text((disp_y + scale_y) / 2 + 6, (disp_z + scale_z + 50) / 2,
            "powder falls\nstraight down\nthrough window",
            fontsize=10, color="#604020")

    ax.set_xlim(-200, 250)
    ax.set_ylim(-90, 220)
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

    # Combined-STEP export of the new parts only (the imported parts ship
    # their own STEPs upstream; the user can stitch them by importing).
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
