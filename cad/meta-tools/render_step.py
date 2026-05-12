"""Render a STEP file to PNG (isometric view) headlessly.

Used to commit "Judge"-style rendered images alongside generated CAD
artefacts (cf. CADSmith workflow referenced in #29) so that PR reviewers
can sanity-check geometry without an external viewer like 3dviewer.net.

Usage:
    xvfb-run -a python render_step.py <input.step> <output.png>

Requires CadQuery + VTK (both pulled in by ``pip install cadquery``)
and an X server (Xvfb works) for VTK's offscreen render path.
"""
import pathlib
import sys

import cadquery as cq
import vtk


def render(inp: pathlib.Path, out: pathlib.Path,
           size: int = 1200, tol: float = 0.03, ang_tol: float = 0.1) -> None:
    shape = cq.importers.importStep(str(inp))
    solids = shape.solids().vals()
    bb = shape.val().BoundingBox()
    print(f"{inp.name}: {len(solids)} solid(s); "
          f"bbox = {bb.xlen:.2f} x {bb.ylen:.2f} x {bb.zlen:.2f} mm")

    ren = vtk.vtkRenderer()
    ren.SetBackground(1.0, 1.0, 1.0)
    for s in solids:
        poly = s.toVtkPolyData(tolerance=tol, angularTolerance=ang_tol, normals=True)
        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputData(poly)
        actor = vtk.vtkActor()
        actor.SetMapper(mapper)
        # tan-ish, similar to 3dviewer.net default
        actor.GetProperty().SetColor(0.78, 0.74, 0.58)
        actor.GetProperty().SetSpecular(0.2)
        actor.GetProperty().SetSpecularPower(20)
        ren.AddActor(actor)

    ren.ResetCamera()
    cam = ren.GetActiveCamera()
    cam.Azimuth(35)
    cam.Elevation(25)
    ren.ResetCameraClippingRange()

    rw = vtk.vtkRenderWindow()
    rw.SetOffScreenRendering(1)
    rw.AddRenderer(ren)
    rw.SetSize(size, size)
    rw.Render()

    w2i = vtk.vtkWindowToImageFilter()
    w2i.SetInput(rw)
    w2i.Update()
    writer = vtk.vtkPNGWriter()
    writer.SetFileName(str(out))
    writer.SetInputConnection(w2i.GetOutputPort())
    writer.Write()
    print(f"wrote {out} ({out.stat().st_size} bytes)")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(__doc__)
        sys.exit(2)
    render(pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2]))
