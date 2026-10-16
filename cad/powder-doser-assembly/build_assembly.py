#!/usr/bin/env python3
"""Assemble every zoo.dev-generated Powder Doser part into one model + render.

This takes the per-part outputs produced by ``generate.py`` (``exports/<part>/``)
and positions them into the full Powder Doser assembly on a single datum:

  * the auger long axis runs along **+Y** (dispensing tip at +Y),
  * **+Z is up**, the mounting-plate top surface is at ``Z = 0``,
  * the auger bore centreline sits at ``Z = Z_AUG = 29.25 mm`` above it.

Two artefacts are emitted into ``assembly/``:

  1. ``full_assembly.step`` / ``full_assembly.glb`` — every part imported from
     its native ``output.step`` B-rep, positioned and coloured, written back as
     a single combined CAD assembly (this is the "everything put together"
     model).
  2. ``assembly_iso_az090.png`` and ``assembly_iso_az090_hires.png`` — a
     coloured isometric render at the same ``az = 90`` iso perspective as
     ``cad/mounting-plate-assembly/assembly/assembly_iso_az090_hires.png``.
     The render loads each part's high-resolution ``output.obj`` mesh so curved
     surfaces (the auger tube) stay smooth instead of faceting into a polygon.

Run headless (VTK needs an X server)::

    xvfb-run -a python3 build_assembly.py

Colours mirror the linked reference render's scheme so the two assemblies read
the same at a glance.
"""
from __future__ import annotations

import math
from pathlib import Path

HERE = Path(__file__).resolve().parent
EXPORTS = HERE / "exports"
ASM = HERE / "assembly"
ASM.mkdir(exist_ok=True)

# --------------------------------------------------------------------------- #
# Assembly datum (all millimetres) — derived from the part prompts/spec.
# --------------------------------------------------------------------------- #
Z_AUG = 29.25                 # auger bore axis above the mounting-plate top
Y_DISP = 125.0                # auger dispensing tip (front, +Y)
PLATE_TOP_LOCAL = 6.0         # mounting-plate slab top in its own native frame
GEAR_BAND_FROM_DISP = 83.33   # 48T band centre, measured from the dispense end
Y_GEAR_BAND = Y_DISP - GEAR_BAND_FROM_DISP        # +41.67
X_MOTOR = 32.0                # pinion/stepper centre distance from the auger
Y_TAP = 56.67                 # tap-collar Y station (just behind the gear band)
Y_BRK_FRONT = 72.67           # front auger bracket
Y_BRK_REAR = -2.0             # rear auger bracket
X_SERVO = 45.0                # servo pinion stations (one per side)
Y_SERVO = Y_DISP              # servo pinions sit by the front hinge line
Z_SERVO = 2.0                 # servo spline axis, 10 mm above the baseplate top

# --------------------------------------------------------------------------- #
# Colours — mirror cad/mounting-plate-assembly/render_assembly.py so the two
# assemblies share one palette.
# --------------------------------------------------------------------------- #
COL_PLATE = (0.80, 0.82, 0.86)
COL_BASE = (0.62, 0.66, 0.72)
COL_AUGER = (0.90, 0.76, 0.45)
COL_BRACKET = (0.55, 0.72, 0.85)
COL_TAP_COLLAR = (0.70, 0.45, 0.85)
COL_TAP_MOUNT = (0.55, 0.40, 0.70)
COL_PINION = (0.45, 0.70, 0.55)
COL_SERVO_PINION = (0.50, 0.85, 0.55)
COL_MOTOR = (0.30, 0.30, 0.35)
COL_SERVO_BODY = (0.20, 0.20, 0.22)

# --------------------------------------------------------------------------- #
# Part placement table.  ``ops`` is an ordered list of rigid-body operations
# applied identically to the VTK render actor and the CadQuery STEP shape:
#   ("rotx", deg) | ("roty", deg) | ("rotz", deg) | ("translate", (x, y, z))
# Rotations are about the global origin, then the translation places the part.
# --------------------------------------------------------------------------- #
PARTS = [
    # name, colour, ops
    ("baseplate", COL_BASE, []),
    ("mounting-plate", COL_PLATE, [("translate", (0.0, 0.0, -PLATE_TOP_LOCAL))]),
    ("storage-auger-full", COL_AUGER,
     [("rotx", -90.0), ("translate", (0.0, Y_DISP, Z_AUG))]),
    ("auger-bracket", COL_BRACKET, [("translate", (0.0, Y_BRK_FRONT, 0.0))]),
    ("auger-bracket", COL_BRACKET, [("translate", (0.0, Y_BRK_REAR, 0.0))]),
    ("tap-collar-mount", COL_TAP_MOUNT, [("translate", (0.0, Y_TAP, 0.0))]),
    ("tap-collar", COL_TAP_COLLAR, [("translate", (0.0, Y_TAP, Z_AUG))]),
    # stepper pinion: native +Z axis -> +Y, gear face aligned onto the band.
    ("stepper-pinion", COL_PINION,
     [("rotx", -90.0), ("translate", (X_MOTOR, Y_GEAR_BAND - 5.0, Z_AUG))]),
    # two servo pinions: native +Z axis -> +X, one each side by the hinge line.
    ("servo-pinion", COL_SERVO_PINION,
     [("roty", 90.0), ("translate", (X_SERVO, Y_SERVO, Z_SERVO))]),
    ("servo-pinion", COL_SERVO_PINION,
     [("roty", 90.0), ("translate", (-X_SERVO, Y_SERVO, Z_SERVO))]),
]

# Simplified motor/servo bodies (boxes) so the render reads like the reference.
# (xc, yc, zc, sx, sy, sz, colour)
BOXES = [
    ("nema11_motor", X_MOTOR, Y_GEAR_BAND - 8.0 - 15.0, Z_AUG,
     28.0, 30.0, 28.0, COL_MOTOR),
    ("mg996r_pos_x", X_SERVO + 24.0, Y_SERVO - 10.0, Z_SERVO,
     20.0, 40.0, 36.0, COL_SERVO_BODY),
    ("mg996r_neg_x", -X_SERVO - 24.0, Y_SERVO - 10.0, Z_SERVO,
     20.0, 40.0, 36.0, COL_SERVO_BODY),
]


# --------------------------------------------------------------------------- #
# VTK render
# --------------------------------------------------------------------------- #
IMG_W, IMG_H = 1400, 1000


def _vtk_transform(ops):
    import vtk
    t = vtk.vtkTransform()
    t.PostMultiply()
    for op, val in ops:
        if op == "rotx":
            t.RotateX(val)
        elif op == "roty":
            t.RotateY(val)
        elif op == "rotz":
            t.RotateZ(val)
        elif op == "translate":
            t.Translate(*val)
    return t


def _obj_actor(name, colour, ops):
    import vtk
    obj = EXPORTS / name / "output.obj"
    r = vtk.vtkOBJReader()
    r.SetFileName(str(obj))
    r.Update()
    norms = vtk.vtkPolyDataNormals()
    norms.SetInputConnection(r.GetOutputPort())
    norms.SetFeatureAngle(45)
    norms.SplittingOff()
    m = vtk.vtkPolyDataMapper()
    m.SetInputConnection(norms.GetOutputPort())
    a = vtk.vtkActor()
    a.SetMapper(m)
    a.GetProperty().SetColor(*colour)
    a.GetProperty().SetSpecular(0.3)
    a.GetProperty().SetSpecularPower(15)
    a.SetUserTransform(_vtk_transform(ops))
    return a


def _box_actor(xc, yc, zc, sx, sy, sz, colour):
    import vtk
    src = vtk.vtkCubeSource()
    src.SetXLength(sx)
    src.SetYLength(sy)
    src.SetZLength(sz)
    src.SetCenter(xc, yc, zc)
    m = vtk.vtkPolyDataMapper()
    m.SetInputConnection(src.GetOutputPort())
    a = vtk.vtkActor()
    a.SetMapper(m)
    a.GetProperty().SetColor(*colour)
    a.GetProperty().SetSpecular(0.2)
    return a


def render_iso(out_path: Path, azimuth_deg: float = 90.0,
               elevation_frac: float = 0.6, scale: int = 1) -> None:
    """Render the coloured assembly at the iso ``azimuth_deg`` perspective.

    The camera math matches cad/mounting-plate-assembly/render_assembly.py so
    the two assemblies share the same viewpoint; ``scale`` super-samples the
    1400x1000 window (``scale=4`` -> 5600x4000 px).
    """
    import vtk
    ren = vtk.vtkRenderer()
    ren.SetBackground(0.97, 0.97, 0.98)
    for name, colour, ops in PARTS:
        ren.AddActor(_obj_actor(name, colour, ops))
    for _, xc, yc, zc, sx, sy, sz, colour in BOXES:
        ren.AddActor(_box_actor(xc, yc, zc, sx, sy, sz, colour))

    kit = vtk.vtkLightKit()
    kit.AddLightsToRenderer(ren)

    win = vtk.vtkRenderWindow()
    win.SetOffScreenRendering(1)
    win.SetSize(IMG_W, IMG_H)
    win.AddRenderer(ren)

    cam = ren.GetActiveCamera()
    cam.SetFocalPoint(0.0, 0.0, Z_AUG)
    diag = 380.0
    ox, oy = diag, -diag
    a = math.radians(azimuth_deg)
    rx = ox * math.cos(a) - oy * math.sin(a)
    ry = ox * math.sin(a) + oy * math.cos(a)
    cam.SetPosition(rx, ry, Z_AUG + diag * elevation_frac)
    cam.SetViewUp(0, 0, 1)
    ren.ResetCamera()

    win.Render()
    w2i = vtk.vtkWindowToImageFilter()
    w2i.SetInput(win)
    if scale > 1:
        w2i.SetScale(scale)
    w2i.SetInputBufferTypeToRGBA()
    w2i.ReadFrontBufferOff()
    w2i.Update()
    writer = vtk.vtkPNGWriter()
    writer.SetFileName(str(out_path))
    writer.SetInputConnection(w2i.GetOutputPort())
    writer.Write()
    print(f"  -> {out_path.relative_to(HERE)}")


# --------------------------------------------------------------------------- #
# Combined CAD assembly (CadQuery, from the native STEP B-reps)
# --------------------------------------------------------------------------- #
def _cq_place(shape, ops):
    for op, val in ops:
        if op == "rotx":
            shape = shape.rotate((0, 0, 0), (1, 0, 0), val)
        elif op == "roty":
            shape = shape.rotate((0, 0, 0), (0, 1, 0), val)
        elif op == "rotz":
            shape = shape.rotate((0, 0, 0), (0, 0, 1), val)
        elif op == "translate":
            shape = shape.translate(val)
    return shape


def build_combined_assembly(out_step: Path, out_glb: Path) -> None:
    import cadquery as cq

    asm = cq.Assembly()
    counts: dict[str, int] = {}
    for name, colour, ops in PARTS:
        step = EXPORTS / name / "output.step"
        shape = cq.importers.importStep(str(step)).val()
        shape = _cq_place(shape, ops)
        counts[name] = counts.get(name, 0) + 1
        inst = f"{name.replace('-', '_')}_{counts[name]}"
        asm.add(shape, name=inst, color=cq.Color(*colour))

    for nm, xc, yc, zc, sx, sy, sz, colour in BOXES:
        box = (cq.Workplane("XY")
               .box(sx, sy, sz, centered=(True, True, True))
               .translate((xc, yc, zc)))
        asm.add(box, name=nm, color=cq.Color(*colour))

    asm.export(str(out_step))
    print(f"  -> {out_step.relative_to(HERE)}")
    try:
        asm.export(str(out_glb))
        print(f"  -> {out_glb.relative_to(HERE)}")
    except Exception as exc:  # noqa: BLE001 - GLTF export is a nice-to-have
        print(f"  ! GLB export skipped: {exc}")


def main() -> None:
    print("Combining native STEP parts into one assembly ...")
    build_combined_assembly(ASM / "full_assembly.step",
                            ASM / "full_assembly.glb")
    print("Rendering coloured iso views ...")
    render_iso(ASM / "assembly_iso_az090.png", azimuth_deg=90.0, scale=1)
    render_iso(ASM / "assembly_iso_az090_hires.png", azimuth_deg=90.0, scale=4)


if __name__ == "__main__":
    main()
