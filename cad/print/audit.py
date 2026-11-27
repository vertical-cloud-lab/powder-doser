"""Mesh-based printability checks for the printed parts (used by slice.py; runnable on its own).

    python audit.py paternoster gondola            # the 6 axis-aligned orientations of one part
    python audit.py chain-carousel-v2              # every part of a design

For an oriented mesh (bed at z = 0) it reports
* overhang area: downward faces more than OVERHANG_DEG (50) from vertical, not on the bed;
* layer-by-layer (0.2 mm), from cross-sections: islands that start in mid-air (nothing in the layer below
  them: floating regions, which need support or a design change), and area not within the 50 deg
  overhang reach of the layer below (overhangs and bridges together);
* thin walls: cross-section regions narrower than two 0.42 mm lines (0.84 mm);
* first-layer contact area and the bed footprint.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import trimesh
from shapely.geometry import Polygon
from shapely.ops import unary_union

HERE = Path(__file__).resolve().parent
OVERHANG_DEG = 50.0          # from vertical
LAYER = 0.2
LINE = 0.42
AXES = {"x": [1, 0, 0], "y": [0, 1, 0], "z": [0, 0, 1]}
SIX = {"z up (as drawn)": [], "z down": [("x", 180)], "x up": [("y", -90)], "x down": [("y", 90)],
       "y up": [("x", 90)], "y down": [("x", -90)]}


def rot(spec) -> np.ndarray:
    M = np.eye(4)
    for ax, deg in spec:
        M = trimesh.transformations.rotation_matrix(np.radians(deg), AXES[ax]) @ M
    return M


def place(mesh: trimesh.Trimesh, spec) -> trimesh.Trimesh:
    """Rotate by spec, then centre the bounding box on x = y = 0 with its bottom on z = 0."""
    m = mesh.copy()
    m.apply_transform(rot(spec))
    lo, hi = m.bounds
    m.apply_translation([-(lo[0] + hi[0]) / 2, -(lo[1] + hi[1]) / 2, -lo[2]])
    return m


def face_metrics(m: trimesh.Trimesh) -> dict:
    n, a = m.face_normals, m.area_faces
    z = m.triangles[:, :, 2]
    on_bed = z.max(axis=1) < 0.02
    down = n[:, 2] < -np.sin(np.radians(OVERHANG_DEG))
    flat_down = n[:, 2] < -0.999
    return {"overhang_area_mm2": round(float(a[down & ~on_bed].sum()), 1),
            "flat_ceiling_area_mm2": round(float(a[flat_down & ~on_bed].sum()), 1),
            "bed_contact_mm2": round(float(a[flat_down & on_bed].sum()), 1),
            "size_mm": [round(float(v), 1) for v in m.extents]}


def _polys(sec) -> list[Polygon]:
    if sec is None:
        return []
    try:
        return [p for p in sec.polygons_full if p.is_valid and p.area > 1e-4]
    except Exception:
        return []


def layer_metrics(m: trimesh.Trimesh, h: float = LAYER) -> dict:
    zs = np.arange(h / 2, m.bounds[1][2], h)
    secs = m.section_multiplane(plane_origin=[0, 0, 0], plane_normal=[0, 0, 1], heights=zs)
    reach = h * np.tan(np.radians(OVERHANG_DEG))
    prev = None
    islands, unsup, thin = [], [], []
    for z, sec in zip(zs, secs):
        polys = _polys(sec)
        geom = unary_union(polys) if polys else Polygon()
        if prev is not None and not geom.is_empty:
            for p in getattr(geom, "geoms", [geom]):
                if prev.is_empty or not p.intersects(prev.buffer(0.05)):
                    islands.append({"z": round(float(z), 2), "area_mm2": round(p.area, 2),
                                    "xy": [round(p.centroid.x, 1), round(p.centroid.y, 1)]})
            ua = geom.difference(prev.buffer(reach)).area if not prev.is_empty else geom.area
            if ua > 0.5:
                unsup.append((float(z), float(ua)))
        if not geom.is_empty:
            opened = geom.buffer(-LINE).buffer(LINE)
            sl = geom.difference(opened.buffer(0.05))
            big = [g for g in getattr(sl, "geoms", [sl]) if g.area > 1.5]
            if big:
                thin.append((float(z), float(sum(g.area for g in big))))
        prev = geom
    first = unary_union(_polys(secs[0])) if len(secs) else Polygon()
    return {"layers": len(zs),
            "first_layer_mm2": round(first.area, 1),
            "floating_islands": islands[:12], "n_floating_islands": len(islands),
            "unsupported_area_mm2": round(sum(a for _, a in unsup) * 1.0, 1),
            "unsupported_layers": len(unsup),
            "unsupported_z_ranges": _ranges([z for z, _ in unsup]),
            "thin_wall_layers": len(thin), "thin_wall_z_ranges": _ranges([z for z, _ in thin]),
            "thin_wall_max_area_mm2": round(max((a for _, a in thin), default=0.0), 1)}


def _ranges(zs: list[float], gap: float = 0.25) -> list[list[float]]:
    out = []
    for z in zs:
        if out and z - out[-1][1] <= gap + 1e-6:
            out[-1][1] = round(z, 2)
        else:
            out.append([round(z, 2), round(z, 2)])
    return out[:10]


def audit(mesh: trimesh.Trimesh, spec, layers: bool = True) -> dict:
    m = place(mesh, spec)
    r = face_metrics(m)
    if layers:
        r.update(layer_metrics(m))
    return r


if __name__ == "__main__":
    design = sys.argv[1]
    keys = sys.argv[2:] or list(json.loads((HERE / design / "parts.json").read_text()))
    for k in keys:
        mesh = trimesh.load(HERE / design / "stl" / f"{k}.stl")
        print(f"== {design}/{k}  watertight={mesh.is_watertight}")
        for name, spec in SIX.items():
            r = audit(mesh, spec, layers=len(sys.argv) > 2)
            print(f"  {name:16s} {json.dumps(r)}")
