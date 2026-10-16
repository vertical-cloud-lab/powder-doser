"""Render the full-system CAD model to judge-style PNGs (iso / front / top / side
+ a cross-section).  Headless via VTK offscreen — invoke under ``xvfb-run -a``.

    xvfb-run -a python design/cad/full-system-direct-drive/render_views.py
"""
from __future__ import annotations

import math
import pathlib
import sys

import cadquery as cq
import vtk

HERE = pathlib.Path(__file__).resolve().parent
RENDER_DIR = HERE / "renders"

sys.path.insert(0, str(HERE))
from cad_model import build, Params  # noqa: E402

# Material colours (R, G, B in 0..1) — visually distinguishable in renders.
PART_COLOURS = {
    "housing": (0.78, 0.74, 0.55),       # tan PLA
    "auger": (0.55, 0.65, 0.78),         # blue PETG
    "coupler_stub": (0.85, 0.85, 0.85),  # aluminium
    "deflector": (0.85, 0.50, 0.40),     # orange ABS
}


def _shape_to_actor(shape: cq.Shape, rgb: tuple[float, float, float]) -> vtk.vtkActor:
    poly = shape.toVtkPolyData(tolerance=0.05, angularTolerance=0.2)
    mapper = vtk.vtkPolyDataMapper()
    mapper.SetInputData(poly)
    actor = vtk.vtkActor()
    actor.SetMapper(mapper)
    actor.GetProperty().SetColor(*rgb)
    actor.GetProperty().SetAmbient(0.18)
    actor.GetProperty().SetDiffuse(0.78)
    actor.GetProperty().SetSpecular(0.10)
    return actor


def _camera_for(view: str, focal: tuple[float, float, float],
                radius: float) -> tuple[tuple[float, float, float],
                                        tuple[float, float, float]]:
    fx, fy, fz = focal
    if view == "iso":
        d = radius * 1.6
        return (fx + d, fy - d, fz + d * 0.7), (0, 0, 1)
    if view == "front":
        return (fx, fy - radius * 2.2, fz), (0, 0, 1)
    if view == "top":
        return (fx, fy, fz + radius * 2.4), (0, 1, 0)
    if view == "side":
        return (fx + radius * 2.2, fy, fz), (0, 0, 1)
    raise ValueError(view)


def render(actors: list[vtk.vtkActor], filename: pathlib.Path, view: str,
           focal: tuple[float, float, float], radius: float,
           size: tuple[int, int] = (1200, 1200),
           clip_plane: tuple | None = None) -> None:
    ren = vtk.vtkRenderer()
    ren.SetBackground(1.0, 1.0, 1.0)
    for a in actors:
        if clip_plane is not None:
            origin, normal = clip_plane
            plane = vtk.vtkPlane()
            plane.SetOrigin(*origin)
            plane.SetNormal(*normal)
            mapper = a.GetMapper()
            mapper.AddClippingPlane(plane)
        ren.AddActor(a)

    cam = ren.GetActiveCamera()
    pos, up = _camera_for(view, focal, radius)
    cam.SetPosition(*pos)
    cam.SetFocalPoint(*focal)
    cam.SetViewUp(*up)
    cam.ParallelProjectionOn()
    cam.SetParallelScale(radius)

    rw = vtk.vtkRenderWindow()
    rw.SetOffScreenRendering(1)
    rw.AddRenderer(ren)
    rw.SetSize(*size)
    rw.Render()

    w2i = vtk.vtkWindowToImageFilter()
    w2i.SetInput(rw)
    w2i.Update()
    writer = vtk.vtkPNGWriter()
    writer.SetFileName(str(filename))
    writer.SetInputConnection(w2i.GetOutputPort())
    writer.Write()
    print(f"Wrote {filename}")


def main() -> int:
    RENDER_DIR.mkdir(parents=True, exist_ok=True)
    parts = build()

    actors: list[vtk.vtkActor] = []
    bbox_xmin = bbox_ymin = bbox_zmin = float("inf")
    bbox_xmax = bbox_ymax = bbox_zmax = float("-inf")
    for name, wp in parts.items():
        rgb = PART_COLOURS.get(name, (0.7, 0.7, 0.7))
        for solid in wp.val().Solids() or [wp.val()]:
            actors.append(_shape_to_actor(solid, rgb))
        bb = wp.val().BoundingBox()
        bbox_xmin = min(bbox_xmin, bb.xmin); bbox_xmax = max(bbox_xmax, bb.xmax)
        bbox_ymin = min(bbox_ymin, bb.ymin); bbox_ymax = max(bbox_ymax, bb.ymax)
        bbox_zmin = min(bbox_zmin, bb.zmin); bbox_zmax = max(bbox_zmax, bb.zmax)

    focal = ((bbox_xmin + bbox_xmax) / 2.0,
             (bbox_ymin + bbox_ymax) / 2.0,
             (bbox_zmin + bbox_zmax) / 2.0)
    radius = max(bbox_xmax - bbox_xmin,
                 bbox_ymax - bbox_ymin,
                 bbox_zmax - bbox_zmin) / 1.7

    for view in ("iso", "front", "top", "side"):
        render(actors, RENDER_DIR / f"full_system_{view}.png", view, focal, radius)

    # Cross-section render: slice through the YZ plane (x=0) so the
    # internal auger flight + embed pockets are visible. Re-build actors
    # so the clip plane only affects this render.
    parts2 = build()
    cs_actors = []
    for name, wp in parts2.items():
        rgb = PART_COLOURS.get(name, (0.7, 0.7, 0.7))
        for solid in wp.val().Solids() or [wp.val()]:
            cs_actors.append(_shape_to_actor(solid, rgb))
    render(cs_actors, RENDER_DIR / "full_system_cross_section.png",
           "side", focal, radius,
           clip_plane=((0, 0, focal[2]), (-1, 0, 0)))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
