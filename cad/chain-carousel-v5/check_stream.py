"""v5: is the dose stream's path clear? An 8 mm column under the exit, from 6 mm below it to the beaker's rim, against every part
at 15, 30 and 45 deg (checks/stream.json). Run from this folder: python check_stream.py"""
import sys, json
sys.path.insert(0, ".")
import cadquery as cq
import layout as L
from params import BEAKER_RIM_Z, PARK_DROP
D = L.DOSE_POINT
out = {}
for tilt in (15.0, 30.0, 45.0):
    z0, z1 = BEAKER_RIM_Z + 1.0, float(D[2]) - 6.0
    cyl = cq.Workplane("XY").circle(4.0).extrude(z1 - z0).translate((float(D[0]), float(D[1]), z0)).val()
    cb = cyl.BoundingBox()
    hits = []
    for p in L.placements(L.State(tilt=tilt, top_door=140.0)):
        s = L.moved(p.key, p.M)
        b = s.BoundingBox()
        if b.xmax < cb.xmin or b.xmin > cb.xmax or b.ymax < cb.ymin or b.ymin > cb.ymax or b.zmax < cb.zmin or b.zmin > cb.zmax:
            continue
        v = s.intersect(cyl).Volume()
        if v > 0.01:
            hits.append((p.name, round(v, 2)))
    out[tilt] = hits
    print(f"tilt {tilt}: stream column (8 mm dia., from 6 mm under the exit to the beaker's rim) meets {hits}", flush=True)
json.dump({"check": "stream", "column_d_mm": 8.0, "from_z": "6 mm under the exit", "to_z": BEAKER_RIM_Z + 1.0,
           "hits": {str(k): v for k, v in out.items()}}, open("checks/stream.json", "w"), indent=1)
