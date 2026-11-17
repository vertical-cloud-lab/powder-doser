"""Export a design's parts and placements for the FEA, from its CadQuery source, without touching the design's folder.

    python export_design.py chain-carousel-v3 [key ...]

Writes $FEA_WORK/designs/<design>/components/<key>.step for every unique part (or the keys named) and
$FEA_WORK/designs/<design>/placements.json (key, name, step, 4x4 world transform per instance), the same files a
design's build.py writes into its own folder. v3 and v4 are still being changed on #185 and their builds are not
committed, so the FEA builds them itself from the commit it is run on (recorded in source.json).
"""
from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import fem  # noqa: E402


def main(design: str, keys: list[str]) -> None:
    src = fem.CAD / design
    sys.path.insert(0, str(src))
    import cadquery as cq
    import layout as L
    out = fem.WORK / "designs" / design
    (out / "components").mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    pl = L.placements()
    rows = [dict(key=p.key, name=p.name, step=p.step, M=np.round(p.M, 6).tolist()) for p in pl]
    (out / "placements.json").write_text(json.dumps(rows, indent=0))
    todo = keys or sorted({p.key for p in pl})
    for k in todo:
        f = out / "components" / f"{k}.step"
        if f.exists():
            continue
        cq.exporters.export(cq.Workplane("XY").add(L.shape(k)), str(f))
    commit = subprocess.run(["git", "rev-parse", "--short=7", "HEAD"], cwd=src, capture_output=True, text=True).stdout.strip()
    (out / "source.json").write_text(json.dumps(dict(design=design, commit=commit, parts=len(todo), instances=len(rows))))
    print(design, len(todo), "parts,", len(rows), "instances", f"{time.time() - t0:.0f} s")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2:])
