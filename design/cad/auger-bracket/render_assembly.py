"""Render an assembly diagram showing how two auger brackets support an auger.

Builds the bracket from cad_model.py, places two of them along an auger
shaft (a simple cylinder + helical flighting proxy), and renders an
isometric PNG that demonstrates the intended use.

Run with::

    xvfb-run -a python render_assembly.py
"""
from __future__ import annotations

from pathlib import Path

import cadquery as cq
import vtk

from cad_model import AUGER_OD, COLLAR_CENTRE_Z, build

HERE = Path(__file__).parent
OUT = HERE / "renders"
OUT.mkdir(parents=True, exist_ok=True)

# Bracket spacing (mm)
BRACKET_SPACING = 180.0  # along the auger axis (Y); auger total height 250 mm
AUGER_LENGTH = 250.0     # PR #16 auger total_height
AUGER_SHAFT_OD = AUGER_OD

# --- Build solids -----------------------------------------------------------
bracket = build()

bracket_a = bracket.translate((0, -BRACKET_SPACING / 2, 0))
bracket_b = bracket.translate((0, +BRACKET_SPACING / 2, 0))

shaft = (
    cq.Workplane("XZ")
    .workplane(offset=-AUGER_LENGTH / 2)
    .center(0, COLLAR_CENTRE_Z)
    .circle(AUGER_SHAFT_OD / 2)
    .extrude(AUGER_LENGTH)
)

# --- VTK render ------------------------------------------------------------
def add_actor(renderer, shape, color, opacity=1.0):
    poly = shape.val().toVtkPolyData(tolerance=0.05, normals=True)
    mapper = vtk.vtkPolyDataMapper()
    mapper.SetInputData(poly)
    actor = vtk.vtkActor()
    actor.SetMapper(mapper)
    actor.GetProperty().SetColor(*color)
    actor.GetProperty().SetOpacity(opacity)
    actor.GetProperty().SetAmbient(0.25)
    actor.GetProperty().SetDiffuse(0.7)
    actor.GetProperty().SetSpecular(0.2)
    renderer.AddActor(actor)
    return actor


renderer = vtk.vtkRenderer()
renderer.SetBackground(1.0, 1.0, 1.0)
add_actor(renderer, bracket_a, (0.78, 0.78, 0.85))
add_actor(renderer, bracket_b, (0.78, 0.78, 0.85))
add_actor(renderer, shaft, (0.55, 0.45, 0.30))

light = vtk.vtkLight()
light.SetPosition(120, -120, 140)
light.SetFocalPoint(0, 0, 10)
renderer.AddLight(light)

window = vtk.vtkRenderWindow()
window.SetOffScreenRendering(1)
window.SetSize(1200, 800)
window.AddRenderer(renderer)

cam = renderer.GetActiveCamera()
cam.SetFocalPoint(0, 0, COLLAR_CENTRE_Z)
cam.SetPosition(120, -160, 90)
cam.SetViewUp(0, 0, 1)
renderer.ResetCamera()
cam.Zoom(1.25)

window.Render()
w2i = vtk.vtkWindowToImageFilter()
w2i.SetInput(window)
w2i.Update()
writer = vtk.vtkPNGWriter()
writer.SetFileName(str(OUT / "assembly_diagram.png"))
writer.SetInputConnection(w2i.GetOutputPort())
writer.Write()
print(f"wrote {OUT / 'assembly_diagram.png'}")
