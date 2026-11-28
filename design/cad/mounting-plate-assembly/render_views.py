"""Render iso/front/top/side PNGs for each part and the assembly.

Uses CadQuery's VTK polydata helper plus an offscreen VTK render window,
following the same convention as ``cad/meta-tools/render_step.py`` from
earlier work in this repo. Run under ``xvfb-run -a python ...`` because
VTK requires a DISPLAY even for offscreen rendering.
"""

from __future__ import annotations

import math
from pathlib import Path

import cadquery as cq
import vtk

HERE = Path(__file__).parent
STEP_DIR = HERE / "step"
RENDER_DIR = HERE / "renders"
RENDER_DIR.mkdir(exist_ok=True)

# Width x height of every PNG we emit.
SIZE = (900, 700)


def _load(step_path: Path):
    return cq.importers.importStep(str(step_path)).val()


def _shape_to_actor(shape, color=(0.78, 0.82, 0.90)):
    pd = shape.toVtkPolyData(tolerance=0.05, angularTolerance=0.2)
    mapper = vtk.vtkPolyDataMapper()
    mapper.SetInputData(pd)
    actor = vtk.vtkActor()
    actor.SetMapper(mapper)
    p = actor.GetProperty()
    p.SetColor(*color)
    p.SetAmbient(0.25)
    p.SetDiffuse(0.7)
    p.SetSpecular(0.15)
    p.SetEdgeVisibility(False)
    return actor


def _render(actors, png_path: Path, view: str):
    ren = vtk.vtkRenderer()
    ren.SetBackground(1.0, 1.0, 1.0)
    for a in actors:
        ren.AddActor(a)

    # Compute combined bounds.
    bounds = [+1e9, -1e9, +1e9, -1e9, +1e9, -1e9]
    for a in actors:
        b = a.GetBounds()
        bounds[0] = min(bounds[0], b[0]); bounds[1] = max(bounds[1], b[1])
        bounds[2] = min(bounds[2], b[2]); bounds[3] = max(bounds[3], b[3])
        bounds[4] = min(bounds[4], b[4]); bounds[5] = max(bounds[5], b[5])
    cx = 0.5 * (bounds[0] + bounds[1])
    cy = 0.5 * (bounds[2] + bounds[3])
    cz = 0.5 * (bounds[4] + bounds[5])
    diag = math.dist((bounds[0], bounds[2], bounds[4]),
                     (bounds[1], bounds[3], bounds[5])) or 1.0

    cam = ren.GetActiveCamera()
    cam.SetFocalPoint(cx, cy, cz)
    if view == "iso":
        cam.SetPosition(cx + diag, cy - diag, cz + 0.7 * diag)
        cam.SetViewUp(0, 0, 1)
    elif view == "front":
        cam.SetPosition(cx, cy - 2.0 * diag, cz)
        cam.SetViewUp(0, 0, 1)
    elif view == "side":
        cam.SetPosition(cx + 2.0 * diag, cy, cz)
        cam.SetViewUp(0, 0, 1)
    elif view == "top":
        cam.SetPosition(cx, cy, cz + 2.0 * diag)
        cam.SetViewUp(0, 1, 0)
    else:
        raise ValueError(view)
    ren.ResetCamera()
    cam.Zoom(1.05)

    # Lights.
    light = vtk.vtkLight()
    light.SetLightTypeToCameraLight()
    light.SetIntensity(0.9)
    ren.AddLight(light)

    rw = vtk.vtkRenderWindow()
    rw.SetOffScreenRendering(1)
    rw.AddRenderer(ren)
    rw.SetSize(*SIZE)
    rw.Render()

    w2i = vtk.vtkWindowToImageFilter()
    w2i.SetInput(rw)
    w2i.Update()
    writer = vtk.vtkPNGWriter()
    writer.SetFileName(str(png_path))
    writer.SetInputConnection(w2i.GetOutputPort())
    writer.Write()


PART_COLORS = {
    "mounting_plate":          (0.85, 0.85, 0.95),
    "baseplate":               (0.80, 0.80, 0.85),
    "auger_placeholder":       (0.55, 0.40, 0.20),
    "bracket_placeholder":     (0.90, 0.65, 0.20),
    "tap_collar_mount_placeholder": (0.65, 0.30, 0.30),
    "nema17_placeholder":      (0.20, 0.20, 0.22),
    "linear_actuator_placeholder": (0.30, 0.45, 0.70),
    "cup_placeholder":         (0.95, 0.95, 0.65),
    "scale_placeholder":       (0.30, 0.30, 0.30),
}


def render_part(name: str) -> None:
    shape = _load(STEP_DIR / f"{name}.step")
    color = PART_COLORS.get(name, (0.78, 0.82, 0.90))
    for view in ("iso", "front", "side", "top"):
        actor = _shape_to_actor(shape, color=color)
        _render([actor], RENDER_DIR / f"{name}_{view}.png", view)
        print(f"wrote renders/{name}_{view}.png")


def render_assembly(step_name: str, out_prefix: str) -> None:
    """Assembly STEPs come back as a Compound containing many shells —
    walk the children so we can colour each one."""
    cmp_ = _load(STEP_DIR / f"{step_name}.step")
    children = list(cmp_.Solids()) or [cmp_]
    # Colour children deterministically by index.
    palette = [
        (0.85, 0.85, 0.95), (0.55, 0.40, 0.20), (0.90, 0.65, 0.20),
        (0.65, 0.30, 0.30), (0.20, 0.20, 0.22), (0.80, 0.80, 0.85),
        (0.30, 0.45, 0.70), (0.30, 0.30, 0.30), (0.95, 0.95, 0.65),
        (0.90, 0.65, 0.20),
    ]
    for view in ("iso", "front", "side"):
        actors = [
            _shape_to_actor(s, color=palette[i % len(palette)])
            for i, s in enumerate(children)
        ]
        _render(actors, RENDER_DIR / f"{out_prefix}_{view}.png", view)
        print(f"wrote renders/{out_prefix}_{view}.png")


def main() -> None:
    parts = [
        "mounting_plate",
        "baseplate",
        "auger_placeholder",
        "bracket_placeholder",
        "tap_collar_mount_placeholder",
        "nema17_placeholder",
        "linear_actuator_placeholder",
        "cup_placeholder",
        "scale_placeholder",
    ]
    for name in parts:
        render_part(name)
    for tilt in (0, 45, 90):
        render_assembly(f"assembly_{tilt}deg", f"assembly_{tilt}deg")


if __name__ == "__main__":
    main()
