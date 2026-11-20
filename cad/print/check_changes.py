"""Quick clearance check of a printability change against its neighbours at the home pose.

    python check_changes.py paternoster gondola gondola 1c135e0 [key,key,...]
        # design, layout key, builder in parts.py, git ref, and optionally only these neighbour keys (faster)

Builds the part with parts.py as of the git ref (default HEAD; 1c135e0 is before the printability changes) and
with the working copy, takes the material the
change added (exact B-rep difference), and intersects it with every other instance of the design's
layout.placements() whose bounding box comes near it, in each placed copy of the part. Prints the
overlapping instances: none means the change cannot have created an interference at the home pose.
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
WORKER = r"""
import sys, importlib.util
import cadquery as cq
from OCP.gp import gp_Trsf
from OCP.TopLoc import TopLoc_Location
import layout as L
key, fn, head_src = sys.argv[1], sys.argv[2], sys.argv[3]
only = set(sys.argv[4].split(",")) if len(sys.argv) > 4 and sys.argv[4] else None
spec = importlib.util.spec_from_file_location("parts_head", head_src)
head = importlib.util.module_from_spec(spec); spec.loader.exec_module(head)

def solid(w):
    return w.val() if isinstance(w, cq.Workplane) and len(w.vals()) == 1 else (
        cq.Compound.makeCompound([v for v in w.vals() if isinstance(v, cq.Shape)]) if isinstance(w, cq.Workplane) else w)

def moved(s, M):
    tr = gp_Trsf(); tr.SetValues(*[float(M[i, j]) for i in range(3) for j in range(4)])
    return cq.Shape.cast(s.wrapped.Moved(TopLoc_Location(tr)))

new, old = L.shape(key), solid(getattr(head, fn)())
added = new.cut(old)
print(f"{key}: volume now {new.Volume():.1f} mm3, at the git ref {old.Volume():.1f} mm3, added {added.Volume():.1f} mm3", flush=True)
if added.Volume() < 1e-3:
    print("nothing added: no new interference possible"); sys.exit()
pl = L.placements()
hits, n = 0, 0
for h in [p for p in pl if p.key == key]:
    a = moved(added, h.M); ab = a.BoundingBox()
    for p in pl:
        if p is h or (only and p.key not in only):
            continue
        s = moved(L.shape(p.key), p.M); b = s.BoundingBox()
        if b.xmax < ab.xmin - 1 or b.xmin > ab.xmax + 1 or b.ymax < ab.ymin - 1 or b.ymin > ab.ymax + 1 or b.zmax < ab.zmin - 1 or b.zmin > ab.zmax + 1:
            continue
        n += 1
        v = a.intersect(s).Volume()
        if v > 1e-3:
            hits += 1
            print(f"  {h.name}: added material overlaps {p.name} ({p.key}) by {v:.3f} mm3", flush=True)
print(f"{n} neighbour pairs checked; {hits} overlaps")
"""

if __name__ == "__main__":
    design, key, fn = sys.argv[1], sys.argv[2], sys.argv[3]
    ref = sys.argv[4] if len(sys.argv) > 4 else "HEAD"
    only = sys.argv[5] if len(sys.argv) > 5 else ""
    src = subprocess.run(["git", "show", f"{ref}:cad/{design}/parts.py"], cwd=HERE, capture_output=True, text=True, check=True).stdout
    tmp = Path(f"/tmp/parts_head_{design}.py")
    tmp.write_text(src)
    subprocess.run([sys.executable, "-c", WORKER, key, fn, str(tmp), only], cwd=HERE.parent / design, check=True,
                   env={**os.environ, "PYTHONPATH": str(HERE.parent / design)})
