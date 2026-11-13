"""Which printer can print each powder-doser part?

Reads STEP files and, for each part, reports its solid volume, its size when
laid on its largest flat face, and whether it fits a Bambu Lab A1 mini
(180 x 180 x 180 mm) or needs the H2D (350 x 320 x 325 mm). A part counts as
fitting if some face-down orientation fits, including turning it on the bed
diagonal.

The part files are the Fusion 360 exports in PR #170
(cad/full-assembly/components/fusion-step/ and .../ai-step/ on branch
claude/issue-165-20261001-1931). Pass their paths:

    pip install cadquery trimesh
    python print_fit.py path/to/*.step
"""

import math
import sys

import cadquery as cq
import numpy as np
import trimesh

PRINTERS = {"A1 mini": (180.0, 180.0, 180.0), "H2D": (350.0, 320.0, 325.0)}


def fits_on_bed(a, b, bed_x, bed_y):
    """Does an a x b footprint fit on the bed, allowing any rotation about z?"""
    for deg in np.linspace(0.0, 90.0, 901):
        t = math.radians(deg)
        w = a * math.cos(t) + b * math.sin(t)
        h = a * math.sin(t) + b * math.cos(t)
        if (w <= bed_x and h <= bed_y) or (h <= bed_x and w <= bed_y):
            return True
    return False


def fits(extents, printer):
    bed_x, bed_y, bed_z = PRINTERS[printer]
    e = sorted(extents)
    # any of the three box axes can point up
    for up in range(3):
        rest = [e[i] for i in range(3) if i != up]
        if e[up] <= bed_z and fits_on_bed(rest[0], rest[1], bed_x, bed_y):
            return True
    return False


def flat_footprint(shape, pts):
    """Size (long x short x height) with the largest planar face down."""
    faces = [f for f in shape.Faces() if f.geomType() == "PLANE"]
    if not faces:
        return None
    n = max(faces, key=lambda f: f.Area()).normalAt()
    n = np.array([n.x, n.y, n.z])
    n /= np.linalg.norm(n)
    a = np.array([1.0, 0.0, 0.0]) if abs(n[0]) < 0.9 else np.array([0.0, 1.0, 0.0])
    u = np.cross(n, a)
    u /= np.linalg.norm(u)
    w = np.cross(n, u)
    p = np.c_[pts @ u, pts @ w]
    best = None
    for deg in range(90):
        t = math.radians(deg)
        r = np.array([[math.cos(t), -math.sin(t)], [math.sin(t), math.cos(t)]])
        ext = np.ptp(p @ r, axis=0)
        if best is None or ext[0] * ext[1] < best[0] * best[1]:
            best = ext
    height = np.ptp(pts @ n)
    return max(best), min(best), height


def main(paths):
    print(f"{'part':28s} {'cm3':>7s}  {'flat size (mm)':>24s}  A1 mini  H2D")
    for path in paths:
        solids = cq.importers.importStep(path).solids().vals()
        comp = cq.Compound.makeCompound(solids)
        vol = sum(s.Volume() for s in solids) / 1000.0
        verts, tris = comp.tessellate(0.2, 0.3)
        mesh = trimesh.Trimesh([(v.x, v.y, v.z) for v in verts], tris)
        _, obb = trimesh.bounds.oriented_bounds(mesh)
        bb = comp.BoundingBox()
        ext = min([sorted(obb), sorted([bb.xlen, bb.ylen, bb.zlen])], key=lambda e: e[2])
        flat = flat_footprint(comp, np.asarray(mesh.vertices))
        size = "%.1f x %.1f x %.1f" % flat if flat else "-"
        name = path.replace("\\", "/").split("/")[-1]
        a1 = "yes" if fits(ext, "A1 mini") else "NO"
        h2d = "yes" if fits(ext, "H2D") else "NO"
        print(f"{name:28s} {vol:7.2f}  {size:>24s}  {a1:7s}  {h2d}")


if __name__ == "__main__":
    main(sys.argv[1:])
