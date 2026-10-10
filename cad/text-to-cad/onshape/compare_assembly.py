"""The whole Onshape model against the text-to-cad assembly it should equal.

Pairs every solid of an Onshape Part Studio export with the nearest solid
(by centroid) of a text-to-cad assembly STEP and reports the worst
bounding-box and volume differences.  The text-to-cad file has the
electronics too; those are simply left unpaired.

    python3 onshape/compare_assembly.py /tmp/os/onshape_hinge_drop5_v2.step \\
        STEP/assembly_servos_above.step --tag hinge_v2
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from compare_onshape import mesh_volume, props, read, solids

HERE = Path(__file__).resolve().parent


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("onshape", type=Path)
    ap.add_argument("t2c", type=Path)
    ap.add_argument("--tag", default="")
    a = ap.parse_args()
    so, st = solids(read(a.onshape)), solids(read(a.t2c))
    po, pt = [props(s) for s in so], [props(s) for s in st]
    C = np.array([p["centroid"] for p in pt])
    worst_box, worst_v, worst_c, used = 0.0, 0.0, 0.0, set()
    for s, p in zip(so, po):
        d = np.linalg.norm(C - p["centroid"], axis=1)
        d[list(used)] = np.inf
        j = int(np.argmin(d))
        used.add(j)
        q = pt[j]
        worst_c = max(worst_c, float(d[j]))
        worst_box = max(worst_box, float(np.abs(q["lo"] - p["lo"]).max()), float(np.abs(q["hi"] - p["hi"]).max()))
        dv = abs(q["volume"] - p["volume"]) / q["volume"]
        if dv > 1e-3:
            dv = abs(mesh_volume(st[j]) - mesh_volume(s)) / q["volume"]
        worst_v = max(worst_v, dv)
    res = {"onshape": str(a.onshape), "text_to_cad": str(a.t2c), "onshape_solids": len(so),
           "text_to_cad_solids": len(st), "paired": len(so), "max_centroid_distance_mm": worst_c,
           "max_bbox_difference_mm": worst_box, "max_volume_difference_rel": worst_v}
    print(json.dumps(res, indent=1))
    (HERE / "results" / f"compare_assembly_{a.tag}.json").write_text(json.dumps(res, indent=1) + "\n")


if __name__ == "__main__":
    main()
