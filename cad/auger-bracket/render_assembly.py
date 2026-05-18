"""
Render an assembly diagram showing the PR #16 Archimedes auger held
by two of these brackets.

Note: the auger STL itself lives in PR #16
(``cad/auger/archimedes-auger.stl``) and is not committed here.  If
the auger STL is available next to the cloned repo (the PR #16
branch), point the script at it via ``--auger-stl``; otherwise it
falls back to a ``/tmp/auger-ref/archimedes-auger.stl`` checkout
created at agent runtime, and if neither is found it draws a plain
Ø25 × 250 mm cylinder as a stand-in.

Run with::

    xvfb-run -a python3 cad/auger-bracket/render_assembly.py
"""

from __future__ import annotations

import argparse
from pathlib import Path

import cadquery as cq
import vtk


HERE = Path(__file__).resolve().parent
STEP_PATH = HERE / "auger-bracket.step"
OUT_PATH = HERE / "views" / "assembly.png"

AUGER_OD = 25.0
AUGER_HEIGHT = 250.0

# The two brackets sit at 1/5 and 4/5 of the auger length, leaving
# the middle clear for the planned solenoid (#25) and coin
# vibration motor (#31).
BRACKET_FRACTIONS = (0.18, 0.82)


def _add_shape(renderer: vtk.vtkRenderer, shape: cq.Shape,
               color, opacity=1.0, edge_color=(0.10, 0.18, 0.26)) -> None:
    poly = shape.toVtkPolyData(0.1, 0.3)
    mapper = vtk.vtkPolyDataMapper()
    mapper.SetInputData(poly)
    actor = vtk.vtkActor()
    actor.SetMapper(mapper)
    actor.GetProperty().SetColor(*color)
    actor.GetProperty().SetOpacity(opacity)
    actor.GetProperty().SetDiffuse(0.85)
    actor.GetProperty().SetAmbient(0.20)
    renderer.AddActor(actor)

    edges = vtk.vtkFeatureEdges()
    edges.SetInputData(poly)
    edges.BoundaryEdgesOn()
    edges.FeatureEdgesOn()
    edges.SetFeatureAngle(30.0)
    edges.NonManifoldEdgesOff()
    edges.ManifoldEdgesOff()
    edge_mapper = vtk.vtkPolyDataMapper()
    edge_mapper.SetInputConnection(edges.GetOutputPort())
    edge_actor = vtk.vtkActor()
    edge_actor.SetMapper(edge_mapper)
    edge_actor.GetProperty().SetColor(*edge_color)
    edge_actor.GetProperty().SetLineWidth(1.0)
    edge_actor.GetProperty().SetOpacity(opacity)
    renderer.AddActor(edge_actor)


def _add_auger(renderer: vtk.vtkRenderer, auger_stl_arg: Path | None) -> None:
    candidates = []
    if auger_stl_arg is not None:
        candidates.append(auger_stl_arg)
    candidates += [
        Path("/tmp/auger-ref/archimedes-auger.stl"),
        HERE.parent / "auger" / "archimedes-auger.stl",
    ]
    poly = None
    for path in candidates:
        if path.is_file():
            print(f"using auger STL: {path}")
            reader = vtk.vtkSTLReader()
            reader.SetFileName(str(path))
            reader.Update()
            poly = reader.GetOutput()
            break
    if poly is None:
        print("auger STL not found — falling back to Ø25 × 250 cylinder stand-in")
        src = vtk.vtkCylinderSource()
        src.SetRadius(AUGER_OD / 2.0)
        src.SetHeight(AUGER_HEIGHT)
        src.SetResolution(64)
        src.Update()
        # vtkCylinderSource axis is +Y; rotate to +Z and lift so base
        # sits at z = 0.
        tf = vtk.vtkTransform()
        tf.Translate(0, 0, AUGER_HEIGHT / 2.0)
        tf.RotateX(90)
        tff = vtk.vtkTransformPolyDataFilter()
        tff.SetInputConnection(src.GetOutputPort())
        tff.SetTransform(tf)
        tff.Update()
        poly = tff.GetOutput()

    mapper = vtk.vtkPolyDataMapper()
    mapper.SetInputData(poly)
    actor = vtk.vtkActor()
    actor.SetMapper(mapper)
    actor.GetProperty().SetColor(0.78, 0.80, 0.82)
    actor.GetProperty().SetOpacity(0.85)
    actor.GetProperty().SetDiffuse(0.85)
    actor.GetProperty().SetAmbient(0.20)
    renderer.AddActor(actor)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--auger-stl", type=Path, default=None,
                        help="path to the PR #16 archimedes-auger.stl")
    args = parser.parse_args()

    bracket = cq.importers.importStep(str(STEP_PATH)).val()
    bracket_aligned = bracket.rotate((0, 0, 0), (1, 0, 0), -90)

    renderer = vtk.vtkRenderer()
    renderer.SetBackground(1.0, 1.0, 1.0)

    _add_auger(renderer, args.auger_stl)

    for frac in BRACKET_FRACTIONS:
        z_target = frac * AUGER_HEIGHT
        # Pre-rotation, ring centre Z in bracket-local coords is at
        # RING_CENTRE_Z (see auger-bracket.py — 19.735 mm).  The
        # -90° X rotation maps (x, y, z) → (x, z, -y), so the bore
        # centre lands at (0, RING_CENTRE_Z, 0).  Shift -Y by
        # RING_CENTRE_Z to put the bore axis on the global Z axis,
        # then translate up to the target height.
        ring_centre_z_orig = 19.735       # mirrors auger-bracket.py
        placed = bracket_aligned.translate((0, -ring_centre_z_orig, z_target))
        _add_shape(renderer, placed, color=(0.36, 0.61, 0.84), opacity=1.0)

    cam = renderer.GetActiveCamera()
    cam.SetPosition(400, 350, AUGER_HEIGHT * 0.55)
    cam.SetFocalPoint(0, 0, AUGER_HEIGHT / 2.0)
    cam.SetViewUp(0, 0, 1)
    cam.SetParallelProjection(True)
    renderer.ResetCamera()
    cam.SetParallelScale(AUGER_HEIGHT * 0.55)

    light = vtk.vtkLight()
    light.SetPosition(300, -300, 400)
    light.SetFocalPoint(0, 0, AUGER_HEIGHT / 2.0)
    light.SetIntensity(0.9)
    renderer.AddLight(light)

    rw = vtk.vtkRenderWindow()
    rw.SetOffScreenRendering(1)
    rw.AddRenderer(renderer)
    rw.SetSize(900, 1200)
    rw.Render()

    w2i = vtk.vtkWindowToImageFilter()
    w2i.SetInput(rw)
    w2i.Update()
    writer = vtk.vtkPNGWriter()
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    writer.SetFileName(str(OUT_PATH))
    writer.SetInputConnection(w2i.GetOutputPort())
    writer.Write()
    print(f"wrote {OUT_PATH.relative_to(HERE.parent.parent)}")


if __name__ == "__main__":
    main()
