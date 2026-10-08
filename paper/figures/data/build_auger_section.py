#!/usr/bin/env python3
"""Cut the tested auger and its screw-on cap along their axis.

The auger and cap that ran every test are Sam Charles's Fusion 360 parts
("Threaded Auger Final" and "Cap Final", shared as STL in the issue #117 zip
and committed under cad/full-assembly/components/fusion/ in PR #170).  This
script slices both meshes with the plane through the tube axis, keeps the
solid regions (even-odd fill of the section loops), and writes them to
assets/auger_section.json together with the dimensions measured from the
mesh.  Fig. 1c used to be drawn from that file; it is now the shaded 3-D
cut-away made by render_auger_cutaway.py, which reuses _load() and
CAP_SEAT_Z from here.  The cap polygons in the JSON are not phased to the
tube's thread (render_auger_cutaway.py turns the cap 180 deg so the two
threads interleave); the measured dimensions are unaffected, and
build_auger_comparison.py checks them against its own measurements.

Usage:
    python3 build_auger_section.py                      # read the STLs from PR #170's branch
    python3 build_auger_section.py AUGER.stl CAP.stl    # or from local files

Requires trimesh, shapely, networkx and numpy.
"""

from __future__ import annotations

import io
import json
import pathlib
import subprocess
import sys

import numpy as np
import trimesh
from shapely.geometry import LineString, Polygon

HERE = pathlib.Path(__file__).resolve().parent
OUT = HERE.parent / "assets" / "auger_section.json"
BRANCH = "origin/claude/issue-165-20261001-1931"
FUSION_DIR = "cad/full-assembly/components/fusion"
CAP_SEAT_Z = 250.0  # the cap's open end seats at the tube end (z = 250 mm)


def _load(arg: str | None, name: str) -> trimesh.Trimesh:
    if arg:
        return trimesh.load(arg)
    blob = subprocess.run(["git", "show", f"{BRANCH}:{FUSION_DIR}/{name}"],
                          check=True, capture_output=True).stdout
    return trimesh.load(io.BytesIO(blob), file_type="stl")


def _solid(mesh: trimesh.Trimesh, z_shift: float = 0.0):
    """Solid region of the axial section (plane y = 0), as shapely geometry."""
    sec = mesh.section(plane_origin=[0, 0, 0], plane_normal=[0, 1, 0])
    geom = None
    for loop in sec.discrete:
        if len(loop) < 4:
            continue
        poly = Polygon(np.c_[loop[:, 0], loop[:, 2] + z_shift]).buffer(0)
        geom = poly if geom is None else geom.symmetric_difference(poly)
    return geom.simplify(0.02)


def _polys(geom) -> list[dict]:
    parts = geom.geoms if hasattr(geom, "geoms") else [geom]
    return [{"exterior": np.round(np.asarray(p.exterior.coords), 2).tolist(),
             "interiors": [np.round(np.asarray(i.coords), 2).tolist()
                           for i in p.interiors]}
            for p in parts if p.area > 0.05]


def _crossings(geom, x: float) -> list[tuple[float, float]]:
    hit = geom.intersection(LineString([(x, -1.0), (x, 400.0)]))
    segs = hit.geoms if hasattr(hit, "geoms") else [hit]
    return sorted((min(s.coords[0][1], s.coords[-1][1]),
                   max(s.coords[0][1], s.coords[-1][1])) for s in segs)


def main() -> None:
    args = sys.argv[1:] + [None, None]
    auger = _load(args[0], "threaded-auger-final.stl")
    cap = _load(args[1], "cap-final.stl")
    g_auger = _solid(auger)
    g_cap = _solid(cap, CAP_SEAT_Z)

    # flight blades cut at mid-radius (x = 7 mm), ignoring the outlet end wall
    blades = [(a, b) for a, b in _crossings(g_auger, 7.0) if a > 8.0]
    starts = np.array([a for a, _ in blades])
    pitch = float(np.median(np.diff(starts)))
    core = _crossings(g_auger, 0.0)[0]
    ext = auger.extents
    dims = {
        "length_mm": round(float(auger.bounds[1][2] - auger.bounds[0][2]), 2),
        "outer_diameter_mm": 25.0,
        "bore_mm": 21.0,
        "core_diameter_mm": 8.0,
        "core_extent_mm": [round(core[0], 2), round(core[1], 2)],
        "flight_pitch_mm": round(pitch, 2),
        "flight_axial_thickness_mm": round(float(np.median([b - a for a, b in blades])), 2),
        "flight_extent_mm": [round(blades[0][0], 2), round(blades[-1][1], 2)],
        "gear_tip_diameter_mm": round(float(max(ext[0], ext[1])), 2),
        "cap_seat_z_mm": CAP_SEAT_Z,
    }
    out = {
        "source": "Fusion 360 'Threaded Auger Final.stl' and 'Cap Final.stl' "
                  "(issue #117 zip; PR #170 cad/full-assembly/components/fusion/)",
        "frame": "x across the tube, z along the axis; outlet at z = 0, cap end at z = 250 (mm)",
        "dimensions": dims,
        "auger": _polys(g_auger),
        "cap": _polys(g_cap),
    }
    OUT.write_text(json.dumps(out, separators=(",", ":")))
    print(json.dumps(dims, indent=1))
    print(f"wrote {OUT.relative_to(HERE.parent.parent)} ({OUT.stat().st_size // 1024} kB)")


if __name__ == "__main__":
    main()
