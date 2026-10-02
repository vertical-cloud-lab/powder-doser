"""Render the full assembly (mounting plate + baseplate + upstream parts).

Imports the per-part STEPs we generate in ``cad_model.py`` and adds
placeholder geometry for the upstream auger / bracket / tap-collar /
motor (sized from PR #49 / #51 / #55 published dimensions; we don't
import the upstream STLs here since those PRs are not merged yet).

The mounting-plate sub-assembly (mounting plate + brackets + auger +
tap-collar + motor + pinion) is rotated as a rigid group about the
hinge axis (the world X-axis at (HINGE_Y, HINGE_Z)) to render the
0°, 45°, and 90° tilt poses.

Run::

    xvfb-run -a python3 render_assembly.py
"""

from __future__ import annotations

import math
from pathlib import Path

import cadquery as cq
import vtk

import cad_model as M


HERE = Path(__file__).resolve().parent
ASM_DIR = HERE / "assembly"
ASM_DIR.mkdir(exist_ok=True)


# --------------------------------------------------------------------- #
# Placeholder upstream-part geometry (sized from PRs #49, #51, #55)
# --------------------------------------------------------------------- #
def _auger() -> cq.Workplane:
    """PR #49 auger placeholder: Ø25 × 250 mm tube + gear band + pinion."""
    body = (
        cq.Workplane("XZ")
        .circle(M.AUGER_OD / 2)
        .extrude(M.AUGER_LEN)
        .translate((0, -M.AUGER_LEN / 2, 0))
    )
    gear_band = (
        cq.Workplane("XZ")
        .circle(M.GEAR_BAND_TIP_DIA / 2)
        .extrude(M.GEAR_BAND_FACE_W)
        .translate((0, M.Y_GEAR_BAND - M.GEAR_BAND_FACE_W / 2, 0))
    )
    return body.union(gear_band).translate((0, 0, M.Z_AUG))


def _pinion() -> cq.Workplane:
    """PR #49 pinion placeholder: Ø18 short disc on the motor shaft."""
    return (
        cq.Workplane("XZ")
        .circle(M.PINION_TIP_DIA / 2)
        .extrude(M.GEAR_BAND_FACE_W + 4)
        .translate((M.X_MOTOR, M.Y_GEAR_BAND - (M.GEAR_BAND_FACE_W + 4) / 2,
                    M.Z_MOTOR))
    )


def _motor() -> cq.Workplane:
    """NEMA 11 placeholder: 28.2 × 28.2 × 32 mm body, face at MOTOR_FACE_Y."""
    body = (
        cq.Workplane("XY")
        .box(M.NEMA11_BODY_W, M.NEMA11_BODY_L, M.NEMA11_BODY_W,
             centered=(True, False, True))
        .translate((M.X_MOTOR, M.MOTOR_FACE_Y - M.NEMA11_BODY_L, M.Z_MOTOR))
    )
    # Stub shaft poking through the motor face into the boss.
    shaft = (
        cq.Workplane("XZ")
        .circle(2.5)                                # Ø5 shaft
        .extrude(6.0)
        .translate((M.X_MOTOR, M.MOTOR_FACE_Y - 1, M.Z_MOTOR))
    )
    return body.union(shaft)


def _bracket(y: float) -> cq.Workplane:
    """PR #55 bracket placeholder: 60 × 25 × 10 flange + Ø35.4 ring."""
    flange = (
        cq.Workplane("XY")
        .box(M.BRK_FLANGE_W, M.BRK_FLANGE_D, M.BRK_FLANGE_T,
             centered=(True, True, False))
    )
    # Ring centred at z = BRK_FLANGE_T + ring_or * 0.55 above flange bottom.
    ring_or = M.BRK_RING_OD / 2
    ring_z = M.BRK_FLANGE_T + ring_or * 0.55
    ring = (
        cq.Workplane("XY")
        .workplane(offset=ring_z)
        .circle(ring_or)
        .extrude(M.BRK_FLANGE_D, both=True)
        .translate((0, 0, 0))
    )
    # Approximation: just show the ring as a torus-ish disc.  Subtract
    # the auger bore through the centre.
    bore = (
        cq.Workplane("XZ")
        .workplane(offset=-M.BRK_FLANGE_D / 2 - 1)
        .center(0, ring_z)
        .circle(M.AUGER_OD / 2)
        .extrude(M.BRK_FLANGE_D + 2)
    )
    # The simple union of flange + offset ring gives us a chunky bracket
    # silhouette that's close enough for an assembly diagram.
    bracket = flange.union(
        cq.Workplane("XZ")
        .workplane(offset=-M.BRK_FLANGE_D / 2)
        .center(0, ring_z)
        .circle(ring_or)
        .extrude(M.BRK_FLANGE_D)
    ).cut(bore)
    return bracket.translate((0, y, 0))


def _tap_collar() -> cq.Workplane:
    """PR #51 tap-collar mount-plate placeholder: 60 × 12 × 14 mm."""
    plate = (
        cq.Workplane("XY")
        .box(M.TAP_PLATE_W, M.TAP_PLATE_D, M.TAP_PLATE_T,
             centered=(True, True, False))
        .translate((0, M.Y_TAP, 0))
    )
    # Collar wraps the auger.
    collar = (
        cq.Workplane("XZ")
        .workplane(offset=M.Y_TAP - M.TAP_PLATE_D / 2)
        .center(0, M.Z_AUG)
        .circle(M.AUGER_OD / 2 + 3)
        .extrude(M.TAP_PLATE_D)
    )
    bore = (
        cq.Workplane("XZ")
        .workplane(offset=M.Y_TAP - M.TAP_PLATE_D / 2 - 1)
        .center(0, M.Z_AUG)
        .circle(M.AUGER_OD / 2)
        .extrude(M.TAP_PLATE_D + 2)
    )
    return plate.union(collar).cut(bore)


# --------------------------------------------------------------------- #
# Rendering
# --------------------------------------------------------------------- #
def _add_actor(renderer: vtk.vtkRenderer, shape: cq.Shape,
               color: tuple[float, float, float],
               opacity: float = 1.0) -> None:
    poly = shape.toVtkPolyData(tolerance=0.05, angularTolerance=0.2)
    mapper = vtk.vtkPolyDataMapper()
    mapper.SetInputData(poly)
    actor = vtk.vtkActor()
    actor.SetMapper(mapper)
    actor.GetProperty().SetColor(*color)
    actor.GetProperty().SetOpacity(opacity)
    if opacity > 0.99:
        actor.GetProperty().SetEdgeVisibility(True)
        actor.GetProperty().SetEdgeColor(0.15, 0.18, 0.22)
        actor.GetProperty().SetLineWidth(0.4)
    renderer.AddActor(actor)


def _rotate_about_hinge(shape: cq.Workplane, angle_deg: float) -> cq.Workplane:
    """Rotate ``shape`` about the world X-axis through (HINGE_Y, HINGE_Z).

    Positive ``angle_deg`` tilts the plate UP (dispense end swings forward
    past the hinge and downward to the baseplate top).
    """
    return (
        shape
        .translate((0, -M.HINGE_Y, -M.HINGE_Z))
        .rotate((0, 0, 0), (1, 0, 0), -angle_deg)
        .translate((0, M.HINGE_Y, M.HINGE_Z))
    )


def _scene_for_tilt(angle_deg: float) -> vtk.vtkRenderer:
    renderer = vtk.vtkRenderer()
    renderer.SetBackground(1.0, 1.0, 1.0)

    # Static (baseplate).
    base = M.build_baseplate()
    _add_actor(renderer, base.val(), color=(0.78, 0.83, 0.92))

    # Rotating sub-assembly: plate + auger + brackets + tap-collar + motor + pinion.
    plate = M.build_mounting_plate()
    auger = _auger()
    pinion = _pinion()
    motor = _motor()
    bracket_f = _bracket(M.Y_BRK_FRONT).translate((0, 0, 0))   # flange-down on plate top
    bracket_r = _bracket(M.Y_BRK_REAR).translate((0, 0, 0))
    tap = _tap_collar()

    for shape, color in (
        (plate,     (0.78, 0.83, 0.92)),     # plate – light grey
        (auger,     (0.82, 0.68, 0.40)),     # auger – brass
        (pinion,    (0.65, 0.55, 0.30)),     # pinion – darker brass
        (motor,     (0.30, 0.30, 0.32)),     # motor – charcoal
        (bracket_f, (0.55, 0.62, 0.72)),     # bracket – mid-grey
        (bracket_r, (0.55, 0.62, 0.72)),
        (tap,       (0.85, 0.55, 0.50)),     # tap-collar – terracotta
    ):
        rotated = _rotate_about_hinge(shape, angle_deg)
        _add_actor(renderer, rotated.val(), color=color)

    # Hinge pins (one per knuckle/post pair) — rendered in red so visible.
    pin = M.build_hinge_pin()
    for side in (+1, -1):
        knuckle_cx = side * M.HINGE_X_OFFSET
        # Place pin so it spans the eye + post eye along X.
        x_centre = knuckle_cx + side * (M.HINGE_EYE_WIDTH / 2 + 0.5
                                        + M.HINGE_EYE_WIDTH / 2) / 2
        pin_placed = pin.translate((x_centre, M.HINGE_Y, M.HINGE_Z))
        # The pin does NOT rotate with the sub-assembly (it's the pivot).
        _add_actor(renderer, pin_placed.val(), color=(0.75, 0.20, 0.20))

    return renderer


def _camera_iso(renderer: vtk.vtkRenderer, size_factor: float = 1.4) -> None:
    bounds = [1e9, -1e9, 1e9, -1e9, 1e9, -1e9]
    for actor in renderer.GetActors():
        b = actor.GetBounds()
        for i in range(0, 6, 2):
            bounds[i] = min(bounds[i], b[i])
            bounds[i + 1] = max(bounds[i + 1], b[i + 1])
    cx = 0.5 * (bounds[0] + bounds[1])
    cy = 0.5 * (bounds[2] + bounds[3])
    cz = 0.5 * (bounds[4] + bounds[5])
    diag = ((bounds[1] - bounds[0]) ** 2
            + (bounds[3] - bounds[2]) ** 2
            + (bounds[5] - bounds[4]) ** 2) ** 0.5
    dist = max(diag * size_factor, 100.0)
    direction = (1.0, -1.2, 0.7)
    dn = math.sqrt(sum(d * d for d in direction))
    cam = renderer.GetActiveCamera()
    cam.SetFocalPoint(cx, cy, cz)
    cam.SetPosition(cx + dist * direction[0] / dn,
                    cy + dist * direction[1] / dn,
                    cz + dist * direction[2] / dn)
    cam.SetViewUp(0, 0, 1)
    renderer.ResetCameraClippingRange()


def _render_to_file(renderer: vtk.vtkRenderer, path: Path,
                    size: tuple[int, int] = (1200, 900)) -> None:
    win = vtk.vtkRenderWindow()
    win.SetOffScreenRendering(1)
    win.AddRenderer(renderer)
    win.SetSize(*size)
    win.Render()
    w2i = vtk.vtkWindowToImageFilter()
    w2i.SetInput(win)
    w2i.Update()
    writer = vtk.vtkPNGWriter()
    writer.SetFileName(str(path))
    writer.SetInputConnection(w2i.GetOutputPort())
    writer.Write()


def main() -> None:
    for angle in (0.0, 45.0, 90.0):
        renderer = _scene_for_tilt(angle)
        _camera_iso(renderer)
        out = ASM_DIR / f"assembly_{int(angle):02d}deg_iso.png"
        _render_to_file(renderer, out)
        print(f"  {out.relative_to(HERE)}")

    # Front + side of the 0° pose for clarity.
    for view_name, direction, size in (
        ("front", (0, -1, 0.05), (1200, 700)),
        ("side",  (1, 0, 0.05),  (900, 900)),
        ("top",   (0, 0, 1),     (900, 1200)),
    ):
        renderer = _scene_for_tilt(0.0)
        bounds = [1e9, -1e9, 1e9, -1e9, 1e9, -1e9]
        for actor in renderer.GetActors():
            b = actor.GetBounds()
            for i in range(0, 6, 2):
                bounds[i] = min(bounds[i], b[i])
                bounds[i + 1] = max(bounds[i + 1], b[i + 1])
        cx = 0.5 * (bounds[0] + bounds[1])
        cy = 0.5 * (bounds[2] + bounds[3])
        cz = 0.5 * (bounds[4] + bounds[5])
        diag = ((bounds[1] - bounds[0]) ** 2
                + (bounds[3] - bounds[2]) ** 2
                + (bounds[5] - bounds[4]) ** 2) ** 0.5
        dist = diag * 1.3
        dn = math.sqrt(sum(d * d for d in direction))
        cam = renderer.GetActiveCamera()
        cam.SetFocalPoint(cx, cy, cz)
        cam.SetPosition(cx + dist * direction[0] / dn,
                        cy + dist * direction[1] / dn,
                        cz + dist * direction[2] / dn)
        cam.SetViewUp(0, 0, 1) if direction[2] < 0.99 else cam.SetViewUp(0, 1, 0)
        renderer.ResetCameraClippingRange()
        out = ASM_DIR / f"assembly_{view_name}.png"
        _render_to_file(renderer, out, size)
        print(f"  {out.relative_to(HERE)}")


if __name__ == "__main__":
    main()
