"""Render iso / front / top / side PNGs for each generated part.

Reads STEPs from ./step/ and writes PNGs to ./views/.
Run with xvfb-run because VTK needs a DISPLAY::

    xvfb-run -a python3 render_views.py
"""

from __future__ import annotations

from pathlib import Path

import cadquery as cq
import vtk


HERE = Path(__file__).resolve().parent
STEP_DIR = HERE / "step"
VIEWS_DIR = HERE / "views"
VIEWS_DIR.mkdir(exist_ok=True)

# Camera direction unit vectors for each view (looking AT origin).
VIEW_DIRS = {
    "iso":   (1.0, -1.0, 0.8),
    "front": (0.0, -1.0, 0.0),
    "top":   (0.0, 0.0, 1.0),
    "side":  (1.0, 0.0, 0.0),
}


def _shape_to_actor(shape: cq.Shape) -> vtk.vtkActor:
    poly = shape.toVtkPolyData(tolerance=0.02, angularTolerance=0.1)
    mapper = vtk.vtkPolyDataMapper()
    mapper.SetInputData(poly)
    actor = vtk.vtkActor()
    actor.SetMapper(mapper)
    actor.GetProperty().SetColor(0.78, 0.83, 0.92)
    actor.GetProperty().SetEdgeVisibility(True)
    actor.GetProperty().SetEdgeColor(0.15, 0.18, 0.22)
    actor.GetProperty().SetLineWidth(0.6)
    return actor


def _render(actor: vtk.vtkActor, direction: tuple[float, float, float],
            out_path: Path, size: tuple[int, int] = (900, 700)) -> None:
    renderer = vtk.vtkRenderer()
    renderer.SetBackground(1.0, 1.0, 1.0)
    renderer.AddActor(actor)

    bounds = actor.GetBounds()
    cx = 0.5 * (bounds[0] + bounds[1])
    cy = 0.5 * (bounds[2] + bounds[3])
    cz = 0.5 * (bounds[4] + bounds[5])
    diag = ((bounds[1] - bounds[0]) ** 2
            + (bounds[3] - bounds[2]) ** 2
            + (bounds[5] - bounds[4]) ** 2) ** 0.5
    dist = max(diag * 1.4, 50.0)
    dvec = direction
    dnorm = (dvec[0] ** 2 + dvec[1] ** 2 + dvec[2] ** 2) ** 0.5
    cam = renderer.GetActiveCamera()
    cam.SetFocalPoint(cx, cy, cz)
    cam.SetPosition(cx + dist * dvec[0] / dnorm,
                    cy + dist * dvec[1] / dnorm,
                    cz + dist * dvec[2] / dnorm)
    cam.SetViewUp(0, 0, 1) if direction[2] < 0.99 else cam.SetViewUp(0, 1, 0)
    renderer.ResetCameraClippingRange()

    win = vtk.vtkRenderWindow()
    win.SetOffScreenRendering(1)
    win.AddRenderer(renderer)
    win.SetSize(*size)
    win.Render()

    w2i = vtk.vtkWindowToImageFilter()
    w2i.SetInput(win)
    w2i.Update()
    writer = vtk.vtkPNGWriter()
    writer.SetFileName(str(out_path))
    writer.SetInputConnection(w2i.GetOutputPort())
    writer.Write()


def main() -> None:
    for step_path in sorted(STEP_DIR.glob("*.step")):
        name = step_path.stem
        shape = cq.importers.importStep(str(step_path)).val()
        actor = _shape_to_actor(shape)
        for view_name, direction in VIEW_DIRS.items():
            out = VIEWS_DIR / f"{name}_{view_name}.png"
            _render(actor, direction, out)
            print(f"  {out.relative_to(HERE)}")
            # vtkActor can only be in one renderer at a time → rebuild it
            actor = _shape_to_actor(shape)


if __name__ == "__main__":
    main()
