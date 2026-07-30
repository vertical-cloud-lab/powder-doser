"""
Render four views (iso, front, top, side) of the auger bracket STEP
to ``views/*.png``.  Mirrors the convention in
``cad/meta-tools/render_step.py``: CadQuery ``importStep`` →
``toVtkPolyData(0.03)`` → VTK offscreen.

Run with::

    xvfb-run -a python3 cad/auger-bracket/render_views.py
"""

from __future__ import annotations

from pathlib import Path

import cadquery as cq
import vtk


HERE = Path(__file__).resolve().parent
STEP_PATH = HERE / "auger-bracket.step"
VIEWS_DIR = HERE / "views"


def _shape_to_actor(shape: cq.Shape) -> vtk.vtkActor:
    poly = shape.toVtkPolyData(0.03, 0.2)
    mapper = vtk.vtkPolyDataMapper()
    mapper.SetInputData(poly)
    actor = vtk.vtkActor()
    actor.SetMapper(mapper)
    actor.GetProperty().SetColor(0.36, 0.61, 0.84)   # PR #16 "#5B9BD5"
    actor.GetProperty().SetSpecular(0.25)
    actor.GetProperty().SetDiffuse(0.85)
    actor.GetProperty().SetAmbient(0.20)
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
    edge_actor.GetProperty().SetColor(0.10, 0.18, 0.26)
    edge_actor.GetProperty().SetLineWidth(1.3)
    return actor, edge_actor


def _render(actors, camera_position, view_up, out_path: Path, parallel: bool):
    ren = vtk.vtkRenderer()
    for actor in actors:
        ren.AddActor(actor)
    ren.SetBackground(1.0, 1.0, 1.0)

    cam = ren.GetActiveCamera()
    cam.SetParallelProjection(parallel)
    cam.SetPosition(*camera_position)
    cam.SetFocalPoint(0, 0, 20)
    cam.SetViewUp(*view_up)
    ren.ResetCamera()
    if parallel:
        cam.SetParallelScale(35)

    rw = vtk.vtkRenderWindow()
    rw.SetOffScreenRendering(1)
    rw.AddRenderer(ren)
    rw.SetSize(900, 900)
    rw.Render()

    w2i = vtk.vtkWindowToImageFilter()
    w2i.SetInput(rw)
    w2i.Update()
    writer = vtk.vtkPNGWriter()
    writer.SetFileName(str(out_path))
    writer.SetInputConnection(w2i.GetOutputPort())
    writer.Write()
    print(f"wrote {out_path.relative_to(HERE.parent.parent)}")


def main() -> None:
    VIEWS_DIR.mkdir(parents=True, exist_ok=True)
    shape = cq.importers.importStep(str(STEP_PATH)).val()
    actors = _shape_to_actor(shape)

    _render(actors, (120, -120, 90), (0, 0, 1), VIEWS_DIR / "iso.png", parallel=False)
    _render(actors, (0, -200, 20), (0, 0, 1), VIEWS_DIR / "front.png", parallel=True)
    _render(actors, (200, 0, 20), (0, 0, 1), VIEWS_DIR / "side.png", parallel=True)
    _render(actors, (0, 0, 200), (0, 1, 0), VIEWS_DIR / "top.png", parallel=True)


if __name__ == "__main__":
    main()
