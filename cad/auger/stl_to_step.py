"""
Convert binary STL -> STEP (.stp) via FreeCAD's OCCT bindings.

Why this is OK for our workflow:
  The Archimedes auger source of truth is the parametric OpenSCAD file
  (`archimedes-auger.scad`). OpenSCAD has no native STEP exporter
  (its kernel is mesh-based), so we go SCAD -> STL -> STEP.
  The resulting STEP is a faceted shell (one face per STL triangle),
  not a NURBS B-rep, so it loses the helix's analytic surface — but
  every CAM/slicer/CAD tool that "requires STEP" (FreeCAD Path,
  Fusion 360, SolidWorks import, Cura via plugin, etc.) accepts it.

Run:
  freecadcmd cad/auger/stl_to_step.py
Inputs/outputs are positional in the script for reproducibility.
"""
import os
import sys

import Mesh        # noqa: E402  (FreeCAD provides this at runtime)
import Part        # noqa: E402

HERE   = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else os.getcwd()
STL_IN = os.path.join(HERE, "archimedes-auger.stl")
STP_OUT = os.path.join(HERE, "archimedes-auger.stp")


def stl_to_step(stl_path: str, step_path: str) -> None:
    if not os.path.isfile(stl_path):
        raise SystemExit(f"STL not found: {stl_path}")

    print(f"[stl_to_step] reading mesh: {stl_path}")
    mesh = Mesh.Mesh(stl_path)
    print(f"[stl_to_step] mesh facets:   {mesh.CountFacets}")
    print(f"[stl_to_step] mesh points:   {mesh.CountPoints}")
    print(f"[stl_to_step] manifold:      {mesh.isSolid()}")

    # Build a B-rep shell from the mesh (one planar face per triangle),
    # then sew into a single solid so downstream STEP consumers see one
    # connected body rather than 11k loose faces.
    shape = Part.Shape()
    shape.makeShapeFromMesh(mesh.Topology, 0.05, False)
    solid = Part.Solid(Part.Shell(shape.Faces))
    print(f"[stl_to_step] solid volume:  {solid.Volume:.2f} mm^3")
    print(f"[stl_to_step] solid faces:   {len(solid.Faces)}")

    solid.exportStep(step_path)
    print(f"[stl_to_step] wrote STEP:    {step_path}"
          f" ({os.path.getsize(step_path) / 1024:.1f} KiB)")


def _main():
    import sys as _sys
    # freecadcmd: argv = ['freecadcmd', 'stl_to_step.py', stl?, stp?]
    # python:     argv = ['stl_to_step.py', stl?, stp?]
    args = [a for a in _sys.argv if a not in ("freecadcmd",)
            and not a.endswith("stl_to_step.py")]
    stl = args[0] if len(args) > 0 else STL_IN
    stp = args[1] if len(args) > 1 else STP_OUT
    stl_to_step(stl, stp)


# freecadcmd doesn't set __name__ == "__main__", so always run on import.
_main()
