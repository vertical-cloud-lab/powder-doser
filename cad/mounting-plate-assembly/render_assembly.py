"""Render full-assembly views + installation/rotation/powder-flow diagrams.

Loads the IMPORTED STLs from upstream PRs (#49, #51, #55) via
``vtkSTLReader`` (cadquery 2.7.0 has no ``importStl`` helper — see repo
memory) and positions them on top of the freshly-generated mounting
plate + baseplate + hinge pins from this package.

Per the issue #62 follow-up:
  * components on TOP of plate
  * auger axis raised on integrated plinths (no through-plate slot)
  * single open U-notch in the +Y plate edge for the auger overhang
  * two SEPARATE side hinges with the rotation axis 10 mm forward of
    the baseplate's front edge
  * full-width front ramps rising up to the hinge axis on each side
    of the auger gap

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
    ARM_BASE_SUPPORT_LEN, AUGER_GAP_W, AUGER_GAP_Y_BACK, AUGER_LEN,
    AUGER_OD, ARM_THK,
    BASE_T, BASE_Y_BACK, BASE_Y_CENTRE, BASE_Y_FRONT, BRK_FLANGE_T,
    BRK_FLANGE_W, BRK_FLANGE_D, BRK_MOUNT_HOLE_INSET_X,
    BRK_RING_CENTRE_LOCAL_Z, GEAR_BAND_FACE_W, GEAR_BAND_TIP_DIA,
    GEAR_CENTRE_DISTANCE,
    GEAR_HINGE_TIP_D, GEAR_HINGE_PCD, GEAR_PINION_TIP_D, GEAR_PINION_PCD,
    GEAR_X_CENTRE, GEAR_X_LO, GEAR_X_HI, GEAR_FACE_W, GEAR_CENTRE_C,
    HINGE_EYE_ID, HINGE_EYE_OD,
    HINGE_LOBE_W, HINGE_X0, HINGE_X1, HINGE_X2, HINGE_X3,
    MG996R_BODY_H, MG996R_BODY_L, MG996R_BODY_T, MG996R_SPLINE_Y_OFFSET,
    MOTOR_FACE_Y, NEMA11_BODY_L, NEMA11_BODY_W,
    NEMA11_FACE_HOLE_PITCH, NEMA11_PILOT_DIA, PINION_LEN, PINION_TIP_DIA,
    PINION_X_LO, PINION_X_HI, PINION_Y, PINION_Z,
    PLATE_L, PLATE_T, PLATE_W, PLATE_X_CENTRE, PLATE_X_MAX, PLATE_X_MIN,
    PLATE_Y_BACK, PLATE_Y_CENTRE, PLATE_Y_FRONT,
    RAMP_TOP_Z, RAMP_Y_BACK,
    SERVO_BODY_X_LO, SERVO_BODY_X_HI, SERVO_WALL_X, SERVO_WALL_T,
    TAP_COLLAR_BORE_LOCAL_Z,
    TAP_PLATE_D, TAP_PLATE_T, TAP_PLATE_W,
    TAP_MOUNT_HOLE_INSET_X, X_MOTOR, Y_BRK_FRONT, Y_BRK_REAR, Y_DISP,
    Y_GEAR_BAND, Y_REAR, Y_TAP, Z_AUG, Z_BASE_TOP, Z_MOTOR,
    build_baseplate, build_hinge_pin, build_mounting_plate,
    build_servo_pinion,
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
COL_SERVO_PINION = (0.50, 0.85, 0.55)
COL_SERVO_BODY = (0.20, 0.20, 0.22)


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
    # Y=Y_DISP and centred at X=0, Z=Z_AUG.
    pre_auger = vtk.vtkTransform()
    pre_auger.PostMultiply()
    pre_auger.RotateX(+90)
    pre_auger.Translate(0, Y_DISP, Z_AUG)
    actors.append(_set_tilt(_stl_actor(
        HERE / "imported-parts/auger-geared/archimedes-auger-geared.stl",
        COL_AUGER), tilt_deg, pre_auger))

    # ---- imported BRACKETS (PR #55): native frame has flange-bottom on z=0
    # and the bore at z=BRK_RING_CENTRE_LOCAL_Z (≈19.74).  We bolt the
    # bracket FLANGE-DOWN to the plate TOP (z=0) so the bore lands
    # exactly at Z_AUG = BRK_RING_CENTRE_LOCAL_Z.  No plinths.
    bracket_stl = HERE / "imported-parts/auger-bracket/auger-bracket.stl"
    for cy in (Y_BRK_FRONT, Y_BRK_REAR):
        pre = vtk.vtkTransform()
        pre.PostMultiply()
        pre.Translate(0, cy, 0)
        actors.append(_set_tilt(_stl_actor(bracket_stl, COL_BRACKET),
                                tilt_deg, pre))

    # ---- imported TAP-COLLAR MOUNT PLATE (PR #51): same mounting style as
    # the brackets but with NO plinth — sits flush on the plate top.
    pre_tm = vtk.vtkTransform()
    pre_tm.PostMultiply()
    pre_tm.Translate(0, Y_TAP, 0)
    actors.append(_set_tilt(_stl_actor(
        HERE / "imported-parts/tap-collar/mount_plate.stl",
        COL_TAP_MOUNT), tilt_deg, pre_tm))

    # ---- imported TAP COLLAR (PR #51): native bore at z=+29.25 above its
    # own z=0 base, so with Z_AUG=29.25 it bolts down flush with no z shift.
    pre_tc = vtk.vtkTransform()
    pre_tc.PostMultiply()
    pre_tc.Translate(0, Y_TAP, Z_AUG - TAP_COLLAR_BORE_LOCAL_Z)
    actors.append(_set_tilt(_stl_actor(
        HERE / "imported-parts/tap-collar/tap_collar.stl",
        COL_TAP_COLLAR), tilt_deg, pre_tc))

    # ---- imported PINION (PR #49): along +Z native, rotated to +Y, centred
    # *on* the gear band at (X_MOTOR, Y_GEAR_BAND, Z_AUG).  Per the fifth
    # review the pinion must be Y-aligned with the gear band (no offset)
    # so the mesh transfers full torque across the gear face.
    pre_p = vtk.vtkTransform()
    pre_p.PostMultiply()
    pre_p.RotateX(+90)
    pre_p.Translate(X_MOTOR, Y_GEAR_BAND, Z_AUG)
    actors.append(_set_tilt(_stl_actor(
        HERE / "imported-parts/auger-geared/stepper-pinion.stl",
        COL_PINION), tilt_deg, pre_p))

    # ---- NEMA 11 motor body (box; +Y face mates with the motor mount block).
    motor_box = (
        cq.Workplane("XY")
        .box(NEMA11_BODY_W, NEMA11_BODY_L, NEMA11_BODY_W, centered=(True, True, True))
        .val()
    )
    pre_m = vtk.vtkTransform()
    pre_m.PostMultiply()
    pre_m.Translate(X_MOTOR, MOTOR_FACE_Y - NEMA11_BODY_L / 2.0, Z_MOTOR)
    actors.append(_set_tilt(_shape_actor(motor_box, COL_MOTOR), tilt_deg, pre_m))

    # ---- HINGE PINS (two pins, one per side; the build_hinge_pin compound
    # is already centred on Y=0,Z=0 in its own frame -> translate to hinge
    # axis (0, Y_DISP, Z_AUG)).  The pins are rigidly attached to the
    # baseplate arms here for visualisation (they could equally be attached
    # to the mounting plate eyes — they sit at the hinge axis either way).
    pre_hp = vtk.vtkTransform()
    pre_hp.PostMultiply()
    pre_hp.Translate(0, Y_DISP, Z_AUG)
    actors.append(_shape_actor(build_hinge_pin().val(), COL_PIN))
    actors[-1].SetUserTransform(pre_hp)

    # ---- SERVO PINION (this package; build_servo_pinion is at origin in
    # its own frame, axis along +X).  Bolted to the MG996R spline on the
    # baseplate, so it does NOT tilt — only spins about its own +X axis.
    pinion_shape = build_servo_pinion().translate(
        (PINION_X_LO, PINION_Y, PINION_Z)
    ).val()
    actors.append(_shape_actor(pinion_shape, COL_SERVO_PINION))

    # ---- MG996R BODY (simplified box for visualisation only — the
    # actual servo is a black plastic body 40 × 20 × 36.8 mm with
    # flange ears, per Will's dimensioned drawing on PR #66).  Body
    # sits outboard of the servo wall in +X; spline pokes -X through
    # the wall onto the pinion.
    body = (
        cq.Workplane("XY")
        .box(MG996R_BODY_H, MG996R_BODY_L, MG996R_BODY_T,
             centered=(False, False, True))
        .translate((SERVO_BODY_X_LO,
                    PINION_Y - MG996R_SPLINE_Y_OFFSET,
                    PINION_Z))
        .val()
    )
    actors.append(_shape_actor(body, COL_SERVO_BODY))

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
    """Top-down annotated map of every mounting hole on the mounting plate."""
    fig, ax = plt.subplots(figsize=(11, 8.5), dpi=140)
    ax.set_aspect("equal")
    ax.set_title("Mounting plate (TOP view, components on TOP surface)\n"
                 "symmetric about $X=0$ — auger overhangs through the central "
                 "+Y notch")
    ax.set_xlabel("X (mm)")
    ax.set_ylabel("Y (mm)")

    # Plate outline (rectangle minus the central +Y notch).
    plate_poly = patches.Polygon([
        (PLATE_X_MIN, PLATE_Y_BACK),
        (PLATE_X_MAX, PLATE_Y_BACK),
        (PLATE_X_MAX, PLATE_Y_FRONT),
        (+AUGER_GAP_W / 2, PLATE_Y_FRONT),
        (+AUGER_GAP_W / 2, AUGER_GAP_Y_BACK),
        (-AUGER_GAP_W / 2, AUGER_GAP_Y_BACK),
        (-AUGER_GAP_W / 2, PLATE_Y_FRONT),
        (PLATE_X_MIN, PLATE_Y_FRONT),
    ], closed=True, facecolor="#e8e8ec", edgecolor="#444", lw=1.5)
    ax.add_patch(plate_poly)

    # Front ramps (shaded regions on either side of the auger gap, top view)
    for x0, x1 in ((+AUGER_GAP_W / 2, PLATE_X_MAX),
                   (PLATE_X_MIN, -AUGER_GAP_W / 2)):
        ax.add_patch(patches.Rectangle((x0, RAMP_Y_BACK),
                                       x1 - x0, PLATE_Y_FRONT - RAMP_Y_BACK,
                                       facecolor="#d0d0d8", edgecolor="#666",
                                       lw=0.6, alpha=0.7))

    # Hinge sandwich — top view of all 3 layers per side at the +Y edge.
    # Inner & outer thirds belong to the mounting plate; middle third
    # belongs to the baseplate (drawn dashed).
    for side in (+1, -1):
        if side > 0:
            mp_spans = ((HINGE_X0, HINGE_X1), (HINGE_X2, HINGE_X3))
            bp_span = (HINGE_X1, HINGE_X2)
        else:
            mp_spans = ((-HINGE_X1, -HINGE_X0), (-HINGE_X3, -HINGE_X2))
            bp_span = (-HINGE_X2, -HINGE_X1)
        for x0, x1 in mp_spans:
            cx = (x0 + x1) / 2
            ax.add_patch(patches.Circle((cx, Y_DISP), HINGE_EYE_OD / 2,
                                        facecolor="#bcbcc6",
                                        edgecolor="#444", lw=1.2))
            ax.add_patch(patches.Circle((cx, Y_DISP), HINGE_EYE_ID / 2,
                                        facecolor="white",
                                        edgecolor="#444", lw=0.8))
        x0, x1 = bp_span
        ax.add_patch(patches.Rectangle((min(x0, x1), BASE_Y_FRONT),
                                       abs(x1 - x0), Y_DISP - BASE_Y_FRONT,
                                       facecolor="#c8c8d0", edgecolor="#444",
                                       lw=0.8, ls="--"))
        cx = (x0 + x1) / 2
        ax.add_patch(patches.Circle((cx, Y_DISP), HINGE_EYE_OD / 2,
                                    facecolor="#a8a8b4",
                                    edgecolor="#444", lw=1.0, ls="--"))

    # Bracket plinths (raised rectangles, top view) at the bracket Ys.
    for cy in (Y_BRK_FRONT, Y_BRK_REAR):
        ax.add_patch(patches.Rectangle((-BRK_FLANGE_W / 2, cy - BRK_FLANGE_D / 2),
                                       BRK_FLANGE_W, BRK_FLANGE_D,
                                       facecolor="#c8d0dc", edgecolor="#446",
                                       lw=1.0))

    # Tap-collar mount footprint (no plinth, flush).
    ax.add_patch(patches.Rectangle((-TAP_PLATE_W / 2, Y_TAP - TAP_PLATE_D / 2),
                                   TAP_PLATE_W, TAP_PLATE_D,
                                   facecolor="#dcd0e4", edgecolor="#646",
                                   lw=1.0))

    # Hole groups
    def add_hole_group(cy, x_spacing, dia, label, colour):
        for sx in (+x_spacing / 2, -x_spacing / 2):
            ax.add_patch(patches.Circle((sx, cy), dia / 2, facecolor=colour,
                                        edgecolor="black", lw=0.8))
        ax.annotate(label, xy=(0, cy),
                    xytext=(PLATE_X_MAX + 12, cy),
                    fontsize=9, va="center", ha="left",
                    arrowprops=dict(arrowstyle="-", color="black", lw=0.6))

    add_hole_group(Y_BRK_FRONT, 48.0, 3.4,
                   "Front bracket (#47 lifted) — 2 × M3 @ X=±24 (flush)", "#3a78b8")
    add_hole_group(Y_TAP,       48.0, 3.4,
                   "Tap-collar mount (#51) — 2 × M3 @ X=±24 (flush)", "#6a3a8b")
    add_hole_group(Y_BRK_REAR,  48.0, 3.4,
                   "Rear bracket (#47 lifted) — 2 × M3 @ X=±24 (flush)", "#3a78b8")

    # NEMA 11 motor face on the vertical mount block.
    ax.add_patch(patches.Rectangle((X_MOTOR - NEMA11_BODY_W / 2 - 4,
                                    MOTOR_FACE_Y - 6),
                                   NEMA11_BODY_W + 8, 6,
                                   facecolor="#88b88f", edgecolor="black",
                                   lw=0.8, alpha=0.6))
    ax.add_patch(patches.Rectangle((X_MOTOR - NEMA11_BODY_W / 2,
                                    MOTOR_FACE_Y - NEMA11_BODY_L),
                                   NEMA11_BODY_W, NEMA11_BODY_L,
                                   facecolor="#888", edgecolor="black",
                                   lw=0.8, alpha=0.4))
    ax.annotate("NEMA 11 (#49) — 4 × M3 @ 23 mm pitch + Ø22 pilot\n"
                "(face holes on +Y vertical face of mount block)",
                xy=(X_MOTOR, MOTOR_FACE_Y - NEMA11_BODY_L / 2),
                xytext=(PLATE_X_MAX + 12, MOTOR_FACE_Y - NEMA11_BODY_L / 2),
                fontsize=9, va="center", ha="left",
                arrowprops=dict(arrowstyle="-", color="black", lw=0.6))

    # (Plate underside is feature-free — no actuator lug.)

    # Auger projection (overhangs through the gap into mid-air at +Y).
    ax.plot([0, 0], [Y_REAR, Y_DISP], color="#a07020", lw=1.5, ls=":",
            label="Auger centreline (above plate, overhangs through gap)")
    ax.plot([0], [Y_GEAR_BAND], "o", color="#a07020", ms=8, mfc="none",
            label=f"Gear band (Y={Y_GEAR_BAND:.1f}, "
                  f"clears plate top by {Z_AUG - GEAR_BAND_TIP_DIA/2:.2f} mm)")
    ax.plot([X_MOTOR], [Y_GEAR_BAND], "x", color="#3a8b48", ms=10,
            label="Pinion centreline (Y-aligned with gear band)")

    # Hinge axis annotation
    ax.annotate("HINGE AXIS\n(X-axis through dispense point;\n"
                "10 mm forward of baseplate front edge)",
                xy=(0, Y_DISP + 2),
                xytext=(PLATE_X_MIN - 8, Y_DISP),
                fontsize=8, va="center", ha="right", color="red",
                arrowprops=dict(arrowstyle="->", color="red", lw=0.8))

    # Auger gap label
    ax.annotate("AUGER GAP\n(open notch in +Y edge)",
                xy=(0, AUGER_GAP_Y_BACK + 8),
                xytext=(PLATE_X_MIN - 8, AUGER_GAP_Y_BACK),
                fontsize=8, va="center", ha="right", color="#a04a20",
                arrowprops=dict(arrowstyle="->", color="#a04a20", lw=0.6))

    ax.legend(loc="lower left", fontsize=8)
    ax.set_xlim(PLATE_X_MIN - 80, PLATE_X_MAX + 150)
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
                 "dispense point literally does not move (red dot); axis "
                 f"sits {Y_DISP - BASE_Y_FRONT:.0f} mm forward of baseplate front edge")
    tilts = [0, 45, 90]
    hy, hz = Y_DISP, Z_AUG
    arm_back_y = BASE_Y_FRONT - ARM_BASE_SUPPORT_LEN

    for ax, tilt in zip(axes, tilts):
        ax.set_aspect("equal")
        ax.set_title(f"tilt = {tilt}°")

        # Baseplate (side projection)
        ax.add_patch(patches.Rectangle((BASE_Y_BACK, Z_BASE_TOP),
                                       BASE_Y_FRONT - BASE_Y_BACK, BASE_T,
                                       facecolor="#c0c0c8", edgecolor="#444"))
        # Baseplate hinge arm side projection — bottom face sits on the
        # baseplate top from arm_back_y forward to the hinge eye, in full
        # contact with the baseplate.
        ax.add_patch(patches.Polygon([
            (arm_back_y, Z_BASE_TOP + BASE_T),
            (Y_DISP + HINGE_EYE_OD / 2, Z_BASE_TOP + BASE_T),
            (Y_DISP + HINGE_EYE_OD / 2, Z_AUG + HINGE_EYE_OD / 2),
            (arm_back_y, Z_AUG + HINGE_EYE_OD / 2),
        ], closed=True, facecolor="#a8a8b4", edgecolor="#444"))

        c, s = math.cos(math.radians(-tilt)), math.sin(math.radians(-tilt))

        def rot(y, z):
            dy, dz = y - hy, z - hz
            return hy + c * dy - s * dz, hz + s * dy + c * dz

        # Mounting plate body (rectangle)
        pts_plate = [(PLATE_Y_BACK, -PLATE_T), (PLATE_Y_FRONT, -PLATE_T),
                     (PLATE_Y_FRONT, 0), (PLATE_Y_BACK, 0)]
        ax.add_patch(patches.Polygon([rot(y, z) for y, z in pts_plate],
                                     facecolor="#d8d8e0", edgecolor="#333"))
        # Front ramp (side projection)
        pts_ramp = [(RAMP_Y_BACK, 0), (PLATE_Y_FRONT, 0),
                    (PLATE_Y_FRONT, RAMP_TOP_Z)]
        ax.add_patch(patches.Polygon([rot(y, z) for y, z in pts_ramp],
                                     facecolor="#c8c8d0", edgecolor="#444"))
        # Eye tab projection (rectangle in YZ)
        pts_tab = [
            (PLATE_Y_FRONT - 1, Z_AUG - HINGE_EYE_OD / 2),
            (Y_DISP + HINGE_EYE_OD / 2, Z_AUG - HINGE_EYE_OD / 2),
            (Y_DISP + HINGE_EYE_OD / 2, Z_AUG + HINGE_EYE_OD / 2),
            (PLATE_Y_FRONT - 1, Z_AUG + HINGE_EYE_OD / 2),
        ]
        ax.add_patch(patches.Polygon([rot(y, z) for y, z in pts_tab],
                                     facecolor="#bcbcc6", edgecolor="#444"))

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

        # Hinge axis marker (always at the same physical point!)
        ax.plot(*rot(hy, hz), "o", color="red", ms=10, zorder=10)

        ax.set_xlim(-200, 200)
        ax.set_ylim(-130, 280)
        ax.grid(True, alpha=0.3)
        ax.set_xlabel("Y (mm)")
        if ax is axes[0]:
            ax.set_ylabel("Z (mm)")

    fig.tight_layout()
    fig.savefig(out_path)
    plt.close(fig)
    print(f"  → {out_path.relative_to(HERE)}")


def powder_flow_diagram(out_path: Path) -> None:
    """Side view at 90° tilt showing the powder path auger → cup."""
    fig, ax = plt.subplots(figsize=(11, 9), dpi=140)
    ax.set_aspect("equal")
    ax.set_title("Powder flow (assembly tilted 90° about the auger dispensing point) — "
                 "powder falls in front of the baseplate")

    tilt = 90
    hy, hz = Y_DISP, Z_AUG
    c, s = math.cos(math.radians(-tilt)), math.sin(math.radians(-tilt))

    def rot(y, z):
        dy, dz = y - hy, z - hz
        return hy + c * dy - s * dz, hz + s * dy + c * dz

    # Baseplate (front edge at BASE_Y_FRONT = +115; hinge axis is +10 mm
    # forward).
    ax.add_patch(patches.Rectangle((BASE_Y_BACK, Z_BASE_TOP),
                                   BASE_Y_FRONT - BASE_Y_BACK, BASE_T,
                                   facecolor="#c0c0c8", edgecolor="#444"))
    # Baseplate forward-and-up arm (side projection) — bottom face sits
    # on the baseplate top, extending back ARM_BASE_SUPPORT_LEN.
    ax.add_patch(patches.Polygon([
        (BASE_Y_FRONT - ARM_BASE_SUPPORT_LEN, Z_BASE_TOP + BASE_T),
        (Y_DISP + HINGE_EYE_OD / 2, Z_BASE_TOP + BASE_T),
        (Y_DISP + HINGE_EYE_OD / 2, Z_AUG + HINGE_EYE_OD / 2),
        (BASE_Y_FRONT - ARM_BASE_SUPPORT_LEN, Z_AUG + HINGE_EYE_OD / 2),
    ], closed=True, facecolor="#a8a8b4", edgecolor="#444"))

    # Mounting plate + ramp (rotated)
    pts_plate = [(PLATE_Y_BACK, -PLATE_T), (PLATE_Y_FRONT, -PLATE_T),
                 (PLATE_Y_FRONT, 0), (PLATE_Y_BACK, 0)]
    ax.add_patch(patches.Polygon([rot(y, z) for y, z in pts_plate],
                                 facecolor="#d8d8e0", edgecolor="#333"))
    pts_ramp = [(RAMP_Y_BACK, 0), (PLATE_Y_FRONT, 0), (PLATE_Y_FRONT, RAMP_TOP_Z)]
    ax.add_patch(patches.Polygon([rot(y, z) for y, z in pts_ramp],
                                 facecolor="#c8c8d0", edgecolor="#444"))
    # Auger rotated
    pts_aug = [(Y_REAR, Z_AUG - AUGER_OD / 2),
               (Y_DISP, Z_AUG - AUGER_OD / 2),
               (Y_DISP, Z_AUG + AUGER_OD / 2),
               (Y_REAR, Z_AUG + AUGER_OD / 2)]
    ax.add_patch(patches.Polygon([rot(y, z) for y, z in pts_aug],
                                 facecolor="#e8c98a", edgecolor="#a07020"))

    # Cup + scale in front of the baseplate (at Y > BASE_Y_FRONT).
    scale_y = Y_DISP                 # under the dispense point
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

    # Powder path arrow: from auger dispensing point straight down.
    disp_y, disp_z = hy, hz
    ax.annotate("", xy=(scale_y, scale_z + 50), xytext=(disp_y, disp_z),
                arrowprops=dict(arrowstyle="->", color="#a07020", lw=3))
    ax.text(disp_y + 8, (disp_z + scale_z + 50) / 2,
            "powder falls in front\nof the baseplate\ninto cup on scale",
            fontsize=10, color="#604020")
    ax.plot([disp_y], [disp_z], "o", color="red", ms=10, zorder=10)
    ax.annotate("dispense point\n(= hinge axis)",
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

    # Combined-STEP export of the NEW parts only.
    asm_step = ASM / "full_assembly.step"
    a = cq.Assembly()
    a.add(build_mounting_plate(), name="mounting_plate", color=cq.Color(*COL_PLATE))
    a.add(build_baseplate(), name="baseplate", color=cq.Color(*COL_BASE))
    a.add(build_hinge_pin().translate((0, Y_DISP, Z_AUG)), name="hinge_pins",
          color=cq.Color(*COL_PIN))
    a.add(build_servo_pinion().translate((PINION_X_LO, PINION_Y, PINION_Z)),
          name="servo_pinion", color=cq.Color(*COL_SERVO_PINION))
    a.save(str(asm_step))
    print(f"  → {asm_step.relative_to(HERE)}")


if __name__ == "__main__":
    main()
