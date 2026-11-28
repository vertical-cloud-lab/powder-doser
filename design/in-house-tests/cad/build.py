"""Build every printed part: STEP and STL in the use frame, an STL turned onto the bed, and checks.

    python build.py [name ...]      # default: all parts

Writes out/step/<name>.step, out/stl/<name>.stl (use frame), out/print/<name>.stl (on the bed,
centred, z >= 0) and out/parts.json (volume, mass at 100 % infill, bounding box, bed footprint,
watertightness, printer fit).
"""
from __future__ import annotations

import json
import math
import sys
import time
from pathlib import Path

import cadquery as cq
import numpy as np
import trimesh

from parts import PARTS

HERE = Path(__file__).resolve().parent
OUT = HERE / "out"
PLA = 1.24  # g/cm3
BEDS = {"A1M": (180.0, 180.0, 180.0), "H2D": (325.0, 320.0, 325.0)}


def to_mesh(wp: cq.Workplane, tol=0.02, ang=0.2) -> trimesh.Trimesh:
    shape = wp.val() if len(wp.vals()) == 1 else cq.Compound.makeCompound([v for v in wp.vals()])
    verts, tris = shape.tessellate(tol, ang)
    v = np.array([(p.x, p.y, p.z) for p in verts])
    return trimesh.Trimesh(v, np.array(tris), process=True)


def build(name: str) -> dict:
    p = PARTS[name]
    t0 = time.time()
    wp = p.fn()
    solid = wp.val() if len(wp.vals()) == 1 else wp.combine().val()
    (OUT / "step").mkdir(parents=True, exist_ok=True)
    (OUT / "stl").mkdir(parents=True, exist_ok=True)
    (OUT / "print").mkdir(parents=True, exist_ok=True)
    cq.exporters.export(wp, str(OUT / "step" / f"{name}.step"))
    mesh = to_mesh(wp)
    mesh.export(OUT / "stl" / f"{name}.stl")
    m = mesh.copy()
    rx, ry, rz = p.bed_rot
    for ang, ax in ((rx, [1, 0, 0]), (ry, [0, 1, 0]), (rz, [0, 0, 1])):
        if ang:
            m.apply_transform(trimesh.transformations.rotation_matrix(math.radians(ang), ax))
    lo, hi = m.bounds
    m.apply_translation([-(lo[0] + hi[0]) / 2, -(lo[1] + hi[1]) / 2, -lo[2]])
    m.export(OUT / "print" / f"{name}.stl")
    ext = (m.bounds[1] - m.bounds[0]).tolist()
    bed = BEDS[p.printer]
    vol = float(solid.Volume())
    # contact area on the bed (faces within 0.05 mm of z = 0 facing down)
    fz = m.triangles_center[:, 2]
    down = (m.face_normals[:, 2] < -0.99) & (fz < 0.05)
    bed_area = float(m.area_faces[down].sum())
    rec = {
        "name": name, "test": p.test, "qty": p.qty, "printer": p.printer, "infill_pct": p.infill,
        "note": p.note, "volume_mm3": round(vol, 1), "mass_g_solid": round(vol * PLA / 1000, 2),
        "bbox_use_mm": [round(x, 2) for x in (mesh.bounds[1] - mesh.bounds[0]).tolist()],
        "bed_extent_mm": [round(x, 2) for x in ext], "bed_rot_deg": list(p.bed_rot),
        "bed_contact_mm2": round(bed_area, 1), "watertight": bool(mesh.is_watertight),
        "fits_printer": all(e <= b - 4 for e, b in zip(ext, bed)), "faces": int(len(mesh.faces)),
        "build_s": round(time.time() - t0, 1),
    }
    return rec


def main(names):
    OUT.mkdir(exist_ok=True)
    db_path = OUT / "parts.json"
    db = json.loads(db_path.read_text()) if db_path.exists() else {}
    for n in names:
        try:
            rec = build(n)
            db[n] = rec
            print(f"{n:28s} {rec['volume_mm3']:>10.0f} mm3 {rec['mass_g_solid']:>7.1f} g  "
                  f"bed {rec['bed_extent_mm']}  wt={rec['watertight']} fit={rec['fits_printer']} "
                  f"({rec['build_s']} s)", flush=True)
        except Exception as exc:  # noqa: BLE001
            print(f"{n:28s} FAILED: {type(exc).__name__}: {exc}", flush=True)
            db[n] = {"name": n, "error": f"{type(exc).__name__}: {exc}"}
    db_path.write_text(json.dumps(dict(sorted(db.items())), indent=1) + "\n")


if __name__ == "__main__":
    main(sys.argv[1:] or list(PARTS))
