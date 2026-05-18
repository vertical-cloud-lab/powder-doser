"""Render the tap collar parts (and an assembled pair) from four viewpoints.

Headless VTK render via cadquery's ``toVtkPolyData``.  Run with::

    xvfb-run -a python render_views.py
"""
from __future__ import annotations

from pathlib import Path

import cadquery as cq
import vtk

HERE = Path(__file__).parent
OUT = HERE / "renders"
OUT.mkdir(parents=True, exist_ok=True)

# (name, list-of-(step-path, color)) — color is RGB 0-1.
TARGETS = {
    "mount_plate": [(HERE / "mount_plate.step", (0.78, 0.78, 0.85))],
    "tap_collar":  [(HERE / "tap_collar.step",  (0.78, 0.78, 0.85))],
    "assembly":    [
        (HERE / "mount_plate.step", (0.80, 0.82, 0.90)),
        (HERE / "tap_collar.step",  (0.95, 0.78, 0.55)),
    ],
}

VIEWS = {
    # name: (azimuth_deg, elevation_deg)
    "iso":   (45, 30),
    "front": (0, 0),
    "side":  (90, 0),
    "top":   (0, 90),
}


def _build_renderer(parts):
    renderer = vtk.vtkRenderer()
    renderer.SetBackground(1.0, 1.0, 1.0)
    for step_path, color in parts:
        solid = cq.importers.importStep(str(step_path)).val()
        poly = solid.toVtkPolyData(tolerance=0.03, normals=True)

        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputData(poly)

        actor = vtk.vtkActor()
        actor.SetMapper(mapper)
        actor.GetProperty().SetColor(*color)
        actor.GetProperty().SetAmbient(0.25)
        actor.GetProperty().SetDiffuse(0.7)
        actor.GetProperty().SetSpecular(0.2)
        renderer.AddActor(actor)

    light = vtk.vtkLight()
    light.SetPosition(60, -60, 80)
    light.SetFocalPoint(0, 0, 20)
    renderer.AddLight(light)
    return renderer


def _set_camera(renderer, az_el, focal_z):
    cam = renderer.GetActiveCamera()
    cam.SetFocalPoint(0, 0, focal_z)
    cam.SetPosition(0, -120, focal_z)
    cam.SetViewUp(0, 0, 1)
    cam.Azimuth(az_el[0])
    cam.Elevation(az_el[1])
    renderer.ResetCamera()
    cam.Zoom(1.3)


def render_target(name: str, parts):
    renderer = _build_renderer(parts)
    window = vtk.vtkRenderWindow()
    window.SetOffScreenRendering(1)
    window.SetSize(900, 700)
    window.AddRenderer(renderer)

    # Focus roughly on the collar centre height when the collar is in scene.
    focal_z = 30.0 if name != "mount_plate" else 22.0
    for view_name, az_el in VIEWS.items():
        _set_camera(renderer, az_el, focal_z)
        window.Render()
        w2i = vtk.vtkWindowToImageFilter()
        w2i.SetInput(window)
        w2i.Update()
        writer = vtk.vtkPNGWriter()
        out_path = OUT / f"{name}_{view_name}.png"
        writer.SetFileName(str(out_path))
        writer.SetInputConnection(w2i.GetOutputPort())
        writer.Write()
        print(f"wrote {out_path}")


if __name__ == "__main__":
    for name, parts in TARGETS.items():
        render_target(name, parts)
