"""Build a real powder-excavator trough using rhino3dm and write a .3dm file.
Demonstrates pure-Python NURBS authoring on a fresh Linux runner —
no Rhino installation, no license, no GUI required.

Run from anywhere:
    python rhino3dm_demo.py
The output .3dm is written next to this script, in ./build/."""
import rhino3dm as r3
from math import pi, sin, cos
import os, pathlib

trough_radius = 12.0
trough_length = 40.0
wall_thickness = 1.6

model = r3.File3dm()

# Build half-circle profile curves as NURBS curves and extrude.
def half_arc_nurbs(radius, n=33):
    pts = [r3.Point3d(radius*cos(pi + t*pi/(n-1)), 0, radius*sin(pi + t*pi/(n-1)))
           for t in range(n)]
    nc = r3.NurbsCurve.Create(False, 3, pts)
    return nc

outer_curve = half_arc_nurbs(trough_radius)
inner_curve = half_arc_nurbs(trough_radius - wall_thickness)

ext_outer = r3.Extrusion.Create(outer_curve, trough_length, False)
ext_inner = r3.Extrusion.Create(inner_curve, trough_length, False)

model.Objects.AddExtrusion(ext_outer)
model.Objects.AddExtrusion(ext_inner)

# Pivot pin axis as reference line
pin = r3.LineCurve(
    r3.Point3d(0, -2, trough_radius + 4),
    r3.Point3d(0, trough_length + 2, trough_radius + 4),
)
model.Objects.AddCurve(pin)

model.Objects.AddTextDot(
    f"trough_radius={trough_radius} length={trough_length} wall={wall_thickness}",
    r3.Point3d(0, trough_length/2, -trough_radius - 5),
)

out_dir = pathlib.Path(__file__).parent / "build"
out_dir.mkdir(exist_ok=True)
out = str(out_dir / "trough.3dm")
ok = model.Write(out, 7)
print(f"Wrote {out}: ok={ok}, size={os.path.getsize(out)} bytes")

m2 = r3.File3dm.Read(out)
print(f"Re-read ok, objects={len(m2.Objects)}")
for obj in m2.Objects:
    g = obj.Geometry
    try:
        bbox = g.GetBoundingBox()
        print(f"  - {type(g).__name__:14s}  bbox min={bbox.Min}  max={bbox.Max}")
    except Exception:
        print(f"  - {type(g).__name__}")
