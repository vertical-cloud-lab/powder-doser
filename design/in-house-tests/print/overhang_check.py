import json, sys
from pathlib import Path
import numpy as np, trimesh
d = Path(sys.argv[1]); out = {}
for f in sorted(d.glob("*.stl")):
    m = trimesh.load(f, force="mesh")
    n = m.face_normals; c = m.triangles_center; a = m.area_faces
    down = n[:, 2] < -np.cos(np.radians(45))          # steeper than 45 deg from vertical, facing down
    off_bed = c[:, 2] > 0.25
    sup = a[down & off_bed].sum()
    # horizontal-facing-down areas = bridges or overhang ceilings
    flat_down = (n[:, 2] < -0.99) & off_bed
    out[f.stem] = {"overhang_mm2": round(float(sup), 1), "flat_ceiling_mm2": round(float(a[flat_down].sum()), 1),
                   "height_mm": round(float(m.bounds[1][2]), 1),
                   "bed_contact_mm2": round(float(a[(n[:, 2] < -0.99) & (c[:, 2] < 0.05)].sum()), 1)}
for k, v in out.items():
    flag = "  <-- check" if v["overhang_mm2"] > 150 else ""
    print(f"{k:28s} overhang {v['overhang_mm2']:8.1f}  ceilings {v['flat_ceiling_mm2']:8.1f}  h {v['height_mm']:6.1f}  bed {v['bed_contact_mm2']:8.1f}{flag}")
json.dump(out, open(sys.argv[2], "w"), indent=1)
