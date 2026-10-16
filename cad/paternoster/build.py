"""Build the paternoster carousel's CAD outputs from params.py.

    python build.py

* step/paternoster_carousel.step: the whole rig at home (module 1 at the
  station, docked, tilt 0), one product per assembly step, every instance
  named; parts shared between instances are written once.
* step/components/<part>.step: each unique part in its own frame.
* stl/: the printed parts (gondola, station parts, hold-down brackets).
* dxf/: cutting templates for the two side plates and the motor plate.
* placements.json: every instance's name, part and 4x4 matrix (renders, sim).
"""
from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

import cadquery as cq
import numpy as np

import layout as L

HERE = Path(__file__).resolve().parent
PRINTED = ("gondola", "station_yoke", "fork", "fork_arm", "clevis_bracket", "vial_cup", "vial_funnel", "hold_bracket")
SKIP_COMPONENT = ("auger", "auger_cap", "sam_mounting_plate", "sam_electronics_carriage", "nema34")   # already in reference/


def loc(M: np.ndarray) -> cq.Location:
    from OCP.gp import gp_Trsf
    tr = gp_Trsf()
    tr.SetValues(*[float(M[i, j]) for i in range(3) for j in range(4)])
    return cq.Location(tr)


def main() -> None:
    pl = L.placements()
    (HERE / "step" / "components").mkdir(parents=True, exist_ok=True)
    (HERE / "stl").mkdir(exist_ok=True)
    (HERE / "dxf").mkdir(exist_ok=True)

    shapes = {k: cq.Workplane("XY").add(L.shape(k)) for k in sorted({p.key for p in pl})}
    top = cq.Assembly(name="paternoster_carousel")
    groups = defaultdict(list)
    for p in pl:
        groups[p.step].append(p)
    for s in sorted(groups):
        sub = cq.Assembly(name=f"{s:02d} {L.STEP_TITLES[s].split(':')[0]}")
        for p in groups[s]:
            sub.add(shapes[p.key], name=p.name, loc=loc(p.M), color=cq.Color(*p.color))
        top.add(sub, name=f"{s:02d} {L.STEP_TITLES[s].split(':')[0]}")
    out = HERE / "step" / "paternoster_carousel.step"
    top.save(str(out))
    print(f"  {out.relative_to(HERE)}: {len(pl)} instances, {len(shapes)} parts, {out.stat().st_size / 1e6:.1f} MB")

    for k, w in shapes.items():
        if k in SKIP_COMPONENT:
            continue
        cq.exporters.export(w, str(HERE / "step" / "components" / f"{k}.step"))
    for k in PRINTED:
        cq.exporters.export(shapes[k], str(HERE / "stl" / f"{k}.stl"), tolerance=0.05, angularTolerance=0.15)
    print(f"  components: {len([k for k in shapes if k not in SKIP_COMPONENT])} STEP, {len(PRINTED)} STL")

    for k in ("side_plate_front", "side_plate_back", "motor_plate"):
        s = L.shape(k)
        bb = s.BoundingBox()
        face = cq.Workplane("YZ").add(s).faces("<X").val()
        sec = cq.Workplane("YZ").add(face)
        cq.exporters.export(sec, str(HERE / "dxf" / f"{k}.dxf"), cq.exporters.ExportTypes.DXF)
        print(f"  dxf/{k}.dxf  ({bb.ylen:.1f} x {bb.zlen:.1f} mm, 1/4 in 6061)")

    rec = [{"name": p.name, "key": p.key, "step": p.step, "module": p.module, "M": np.round(p.M, 5).tolist()} for p in pl]
    (HERE / "placements.json").write_text(json.dumps(rec) + "\n")
    print(f"  placements.json: {len(rec)} instances")


if __name__ == "__main__":
    main()
