"""Render iso/front/top/side PNG views of every part in cad_model.PARTS using
VTK offscreen rendering.  Outputs land in views/<part>_<view>.png.

Requires xvfb-run because VTK needs a DISPLAY.
"""
from __future__ import annotations

import os
from pathlib import Path

import vtk

import cad_model

VIEWS_DIR = Path(__file__).resolve().parent / "views"
VIEWS_DIR.mkdir(parents=True, exist_ok=True)

# Camera positions per view (azimuth, elevation, roll).  Looking AT origin.
VIEW_DIRS = {
    "iso":   (35.0, 25.0),
    "front": (0.0, 0.0),
    "top":   (0.0, 89.9),
    "side":  (90.0, 0.0),
}

def _shape_to_actor(shape):
    """CadQuery Shape -> VTK actor (using Shape.toVtkPolyData)."""
    polydata = shape.toVtkPolyData(tolerance=0.1, angularTolerance=0.3)
    mapper = vtk.vtkPolyDataMapper()
    mapper.SetInputData(polydata)
    actor = vtk.vtkActor()
    actor.SetMapper(mapper)
    actor.GetProperty().SetColor(0.78, 0.81, 0.86)
    actor.GetProperty().SetSpecular(0.3)
    actor.GetProperty().SetSpecularPower(20)
    return actor


def _render_part(name: str, build_fn) -> None:
    print(f"Rendering {name} ...")
    part = build_fn()
    shape = part.val()

    bb = shape.BoundingBox()
    centre = ((bb.xmin + bb.xmax) / 2,
              (bb.ymin + bb.ymax) / 2,
              (bb.zmin + bb.zmax) / 2)
    diag = bb.DiagonalLength

    for view, (az, el) in VIEW_DIRS.items():
        ren = vtk.vtkRenderer()
        ren.SetBackground(1, 1, 1)
        ren.AddActor(_shape_to_actor(shape))

        # Lights.
        for pos in ((1, 1, 1), (-1, 1, 0.5), (0, -1, 1)):
            light = vtk.vtkLight()
            light.SetPosition(centre[0] + pos[0] * diag,
                              centre[1] + pos[1] * diag,
                              centre[2] + pos[2] * diag)
            light.SetFocalPoint(*centre)
            light.SetIntensity(0.5)
            ren.AddLight(light)

        cam = ren.GetActiveCamera()
        cam.SetFocalPoint(*centre)
        # Place camera diag*1.5 away in -Y (front view default).
        cam.SetPosition(centre[0], centre[1] - diag * 1.6, centre[2])
        cam.SetViewUp(0, 0, 1)
        cam.Azimuth(az)
        cam.Elevation(el)
        ren.ResetCameraClippingRange()

        win = vtk.vtkRenderWindow()
        win.SetOffScreenRendering(1)
        win.AddRenderer(ren)
        win.SetSize(800, 600)
        win.Render()

        w2i = vtk.vtkWindowToImageFilter()
        w2i.SetInput(win)
        w2i.Update()

        writer = vtk.vtkPNGWriter()
        out = VIEWS_DIR / f"{name}_{view}.png"
        writer.SetFileName(str(out))
        writer.SetInputConnection(w2i.GetOutputPort())
        writer.Write()
        print(f"  wrote {out.relative_to(VIEWS_DIR.parent)}")


def main() -> None:
    for name, fn in cad_model.PARTS.items():
        _render_part(name, fn)


if __name__ == "__main__":
    main()
