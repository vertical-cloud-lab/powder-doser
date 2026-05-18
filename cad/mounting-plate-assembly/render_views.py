"""Render iso/front/top/side PNGs for each new part in this package.

Renders only the three parts authored here (mounting_plate, baseplate,
hinge_pin); the imported parts (auger / bracket / tap-collar / pinion)
already ship with their own renders in the upstream PRs and are not
re-rendered here.

Run from the package directory (xvfb required for headless VTK)::

    xvfb-run -a python3 render_views.py
"""
from __future__ import annotations

from pathlib import Path

import cadquery as cq
import vtk

VIEWS = {
    "iso":   ((1.0,  1.0,  0.7),  (0, 0, 1)),
    "front": ((0.0, -1.0,  0.0),  (0, 0, 1)),
    "top":   ((0.0,  0.0,  1.0),  (0, 1, 0)),
    "side":  ((1.0,  0.0,  0.0),  (0, 0, 1)),
}

IMG_W, IMG_H = 900, 700


def _shape_to_actor(shape: cq.Shape, colour=(0.70, 0.75, 0.82)) -> vtk.vtkActor:
    """Convert a CadQuery shape to a VTK actor via Shape.toVtkPolyData."""
    pd = shape.toVtkPolyData(0.1, 0.5)
    mapper = vtk.vtkPolyDataMapper()
    mapper.SetInputData(pd)
    actor = vtk.vtkActor()
    actor.SetMapper(mapper)
    actor.GetProperty().SetColor(*colour)
    actor.GetProperty().SetSpecular(0.35)
    actor.GetProperty().SetSpecularPower(20)
    return actor


def _render(actor: vtk.vtkActor, out_path: Path, direction, up) -> None:
    ren = vtk.vtkRenderer()
    ren.SetBackground(0.97, 0.97, 0.98)
    ren.AddActor(actor)
    win = vtk.vtkRenderWindow()
    win.SetOffScreenRendering(1)
    win.SetSize(IMG_W, IMG_H)
    win.AddRenderer(ren)

    cam = ren.GetActiveCamera()
    # Centre on the actor bounds
    b = actor.GetBounds()
    cx = (b[0] + b[1]) / 2
    cy = (b[2] + b[3]) / 2
    cz = (b[4] + b[5]) / 2
    diag = max(b[1] - b[0], b[3] - b[2], b[5] - b[4], 1.0)
    cam.SetFocalPoint(cx, cy, cz)
    cam.SetPosition(cx + direction[0] * diag * 2,
                    cy + direction[1] * diag * 2,
                    cz + direction[2] * diag * 2)
    cam.SetViewUp(*up)
    ren.ResetCamera()

    win.Render()
    w2i = vtk.vtkWindowToImageFilter()
    w2i.SetInput(win)
    w2i.SetScale(1)
    w2i.SetInputBufferTypeToRGBA()
    w2i.ReadFrontBufferOff()
    w2i.Update()
    writer = vtk.vtkPNGWriter()
    writer.SetFileName(str(out_path))
    writer.SetInputConnection(w2i.GetOutputPort())
    writer.Write()


def main() -> None:
    here = Path(__file__).resolve().parent
    out_dir = here / "views"
    out_dir.mkdir(exist_ok=True)

    # Build each part fresh (faster than re-importing the STEP).
    from cad_model import build_mounting_plate, build_baseplate, build_hinge_pin

    parts = {
        "mounting_plate": build_mounting_plate(),
        "baseplate": build_baseplate(),
        "hinge_pin": build_hinge_pin(),
    }
    for name, wp in parts.items():
        shape = wp.val()
        for view, (dir_, up) in VIEWS.items():
            actor = _shape_to_actor(shape)
            out = out_dir / f"{name}_{view}.png"
            _render(actor, out, dir_, up)
            print(f"  → {out.relative_to(here)}")


if __name__ == "__main__":
    main()
