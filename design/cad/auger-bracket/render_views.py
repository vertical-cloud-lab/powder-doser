"""Render the auger bracket STEP from four viewpoints to PNG.

Headless VTK render via cadquery's toVtkPolyData.  Run with::

    xvfb-run -a python render_views.py
"""
from __future__ import annotations

from pathlib import Path

import cadquery as cq
import vtk

HERE = Path(__file__).parent
STEP = HERE / "auger_bracket.step"
OUT = HERE / "renders"
OUT.mkdir(parents=True, exist_ok=True)

# Load STEP
solid = cq.importers.importStep(str(STEP)).val()
poly = solid.toVtkPolyData(tolerance=0.03, normals=True)

mapper = vtk.vtkPolyDataMapper()
mapper.SetInputData(poly)

actor = vtk.vtkActor()
actor.SetMapper(mapper)
actor.GetProperty().SetColor(0.78, 0.78, 0.85)
actor.GetProperty().SetAmbient(0.25)
actor.GetProperty().SetDiffuse(0.7)
actor.GetProperty().SetSpecular(0.2)

# Edge overlay for clarity
edge_actor = vtk.vtkActor()
edge_actor.SetMapper(mapper)
edge_actor.GetProperty().SetRepresentationToWireframe()
edge_actor.GetProperty().SetColor(0.1, 0.1, 0.1)
edge_actor.GetProperty().SetLineWidth(0.5)
edge_actor.GetProperty().EdgeVisibilityOn()

renderer = vtk.vtkRenderer()
renderer.AddActor(actor)
renderer.SetBackground(1.0, 1.0, 1.0)

light = vtk.vtkLight()
light.SetPosition(60, -60, 80)
light.SetFocalPoint(0, 0, 8)
renderer.AddLight(light)

window = vtk.vtkRenderWindow()
window.SetOffScreenRendering(1)
window.SetSize(900, 700)
window.AddRenderer(renderer)

VIEWS = {
    # name: (azimuth_deg, elevation_deg)
    "iso":   (45, 30),
    "front": (0, 0),
    "side":  (90, 0),
    "top":   (0, 90),
}


def set_camera(az_el):
    cam = renderer.GetActiveCamera()
    cam.SetFocalPoint(0, 0, 10)
    cam.SetPosition(0, -80, 10)
    cam.SetViewUp(0, 0, 1)
    cam.Azimuth(az_el[0])
    cam.Elevation(az_el[1])
    renderer.ResetCamera()
    cam.Zoom(1.3)


for name, az_el in VIEWS.items():
    set_camera(az_el)
    window.Render()
    w2i = vtk.vtkWindowToImageFilter()
    w2i.SetInput(window)
    w2i.Update()
    writer = vtk.vtkPNGWriter()
    writer.SetFileName(str(OUT / f"auger_bracket_{name}.png"))
    writer.SetInputConnection(w2i.GetOutputPort())
    writer.Write()
    print(f"wrote {OUT / f'auger_bracket_{name}.png'}")
