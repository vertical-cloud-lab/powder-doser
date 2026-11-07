"""Check the Onshape branch (hinge lowered) against the text-to-cad lowering.

* every solid but the board, the baseplate and the four board screws moved
  by (0, 0, -drop); those six did not move (the baseplate changed shape),
* the Onshape baseplate against text-to-cad's ``STEP/parts/baseplate_servos_above.step``
  (IoU, volume, box),
* a tilt sweep: the tilting solids (the mounting plate and everything on it)
  turned about the lowered hinge axis, and the servo pinions with them, against
  the Onshape baseplate, at 0-5 deg in 0.5 deg steps (where the floor and the
  bracket screw heads swing back over the table) and at 15, 30, 45 deg.

    python3 onshape/compare_hinge.py /tmp/os/onshape_hinge_drop5.step --tag v2
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import numpy as np
from OCP.BRepAlgoAPI import BRepAlgoAPI_Common
from OCP.BRepBuilderAPI import BRepBuilderAPI_Transform
from OCP.gp import gp_Ax1, gp_Dir, gp_Pnt, gp_Trsf

from compare_onshape import BEFORE, iou, is_board, moved, props, read, solids, volume

HERE = Path(__file__).resolve().parent
T2C_BASEPLATE = HERE.parent / "STEP" / "parts" / "baseplate_servos_above.step"
HINGE_Y, HINGE_Z = 45.4, 43.25
TILTS = [i * 0.5 for i in range(11)] + [15.0, 30.0, 45.0]


def tilt_group_flags(sb: list) -> list[bool]:
    """Which solids of the original STEP belong to tilt_group (XCAF tree)."""
    from OCP.STEPCAFControl import STEPCAFControl_Reader
    from OCP.TCollection import TCollection_ExtendedString
    from OCP.TDataStd import TDataStd_Name
    from OCP.TDF import TDF_Label, TDF_LabelSequence
    from OCP.TDocStd import TDocStd_Document
    from OCP.TopLoc import TopLoc_Location
    from OCP.XCAFDoc import XCAFDoc_DocumentTool

    doc = TDocStd_Document(TCollection_ExtendedString("d"))
    r = STEPCAFControl_Reader()
    r.SetNameMode(True)
    r.ReadFile(str(BEFORE))
    r.Transfer(doc)
    st = XCAFDoc_DocumentTool.ShapeTool_s(doc.Main())

    def nm(lab):
        a = TDataStd_Name()
        return a.Get().ToExtString() if lab.FindAttribute(TDataStd_Name.GetID_s(), a) else ""

    tilt_centroids = []

    def walk(lab, top, loc):
        tgt = lab
        if st.IsReference_s(lab):
            ref = TDF_Label()
            st.GetReferredShape_s(lab, ref)
            tgt, loc = ref, loc.Multiplied(st.GetLocation_s(lab))
        if st.IsAssembly_s(tgt):
            kids = TDF_LabelSequence()
            st.GetComponents_s(tgt, kids)
            for i in range(1, kids.Length() + 1):
                walk(kids.Value(i), top or nm(kids.Value(i)), loc)
        elif top == "tilt_group":
            for s in solids(st.GetShape_s(tgt).Moved(loc)):
                tilt_centroids.append(props(s)["centroid"])

    roots = TDF_LabelSequence()
    st.GetFreeShapes(roots)
    walk(roots.Value(1), None, TopLoc_Location())
    tc = np.array(tilt_centroids)
    return [bool(np.min(np.linalg.norm(tc - props(s)["centroid"], axis=1)) < 1e-6) for s in sb]


def rotated(s, deg: float, hz: float):
    t = gp_Trsf()
    t.SetRotation(gp_Ax1(gp_Pnt(0, HINGE_Y, hz), gp_Dir(1, 0, 0)), math.radians(deg))
    return BRepBuilderAPI_Transform(s, t, True).Shape()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("after", type=Path)
    ap.add_argument("--drop", type=float, default=5.0)
    ap.add_argument("--tag", default="v1")
    a = ap.parse_args()
    sb, sa = solids(read(BEFORE)), solids(read(a.after))
    pb, pa = [props(s) for s in sb], [props(s) for s in sa]
    tilting = tilt_group_flags(sb)

    def fixed(p):      # board, baseplate, the four #10 screws into the board
        return is_board(p) or (abs(p["lo"][0] + 95) < 0.01 and abs(p["hi"][1] - 170) < 0.01) or \
            (abs(abs(p["centroid"][0]) - 80) < 0.5 and p["volume"] < 2000)

    base_b = next(i for i, p in enumerate(pb) if abs(p["lo"][0] + 95) < 0.01 and abs(p["hi"][1] - 170) < 0.01)
    base_a = next(j for j, q in enumerate(pa) if abs(q["lo"][0] + 95) < 0.01 and abs(q["hi"][1] - 170) < 0.01)
    used, worst, n_fixed, tilt_after = {base_a}, 0.0, 0, []
    for i, p in enumerate(pb):
        if i == base_b:
            continue
        dz = 0.0 if fixed(p) else -a.drop
        n_fixed += dz == 0.0
        want = p["centroid"] + [0, 0, dz]
        j = min((j for j in range(len(pa)) if j not in used),
                key=lambda j: np.linalg.norm(pa[j]["centroid"] - want))
        used.add(j)
        worst = max(worst, float(np.abs(pa[j]["lo"] - p["lo"] - [0, 0, dz]).max()),
                    float(np.abs(pa[j]["hi"] - p["hi"] - [0, 0, dz]).max()))
        if tilting[i]:
            tilt_after.append(sa[j])
    res = {"tag": a.tag, "drop_mm": a.drop,
           "placements": {"solids": len(sa), "fixed": n_fixed + 1, "moved": len(sa) - n_fixed - 1,
                          "max_bbox_error_mm": worst, "tilting_solids": len(tilt_after)}}

    base = sa[base_a]
    t2c = solids(read(T2C_BASEPLATE))[0]
    pt, po = props(t2c), props(base)
    res["baseplate"] = {"onshape_volume_mm3": po["volume"], "text_to_cad_volume_mm3": pt["volume"],
                        "onshape_bbox_mm": [po["lo"].round(3).tolist(), po["hi"].round(3).tolist()],
                        "text_to_cad_bbox_mm": [pt["lo"].round(3).tolist(), pt["hi"].round(3).tolist()],
                        "iou_onshape_vs_text_to_cad": iou(base, t2c)}

    hz = HINGE_Z - a.drop
    sweep = {}
    for deg in TILTS:
        hits = []
        for s in tilt_after:
            v = volume(BRepAlgoAPI_Common(rotated(s, deg, hz), base).Shape())
            if v > 1e-3:
                c = props(s)["centroid"]
                hits.append({"centroid_mm": c.round(1).tolist(), "overlap_mm3": round(v, 4)})
        sweep[f"{deg:g}"] = hits
    res["tilt_sweep_vs_baseplate"] = sweep
    res["tilt_sweep_clean"] = all(not h for h in sweep.values())
    print(json.dumps(res, indent=1))
    (HERE / "results" / f"compare_hinge_{a.tag}.json").write_text(json.dumps(res, indent=1) + "\n")


if __name__ == "__main__":
    main()
