"""Export the chain-carousel test rig.

    python build.py

* step/chain_carousel_rig.step  the whole rig as one STEP assembly: named,
  coloured instances that share their part definitions (the chain's 84
  plain links are 2 parts, not 84), so Onshape imports it as one assembly
  plus one Part Studio per unique part.
* step/components/<key>.step     every unique part on its own (reference parts: reference/).
* stl/<part>.stl                 the printed parts, print-ready orientation.
* dxf/deck.dxf, dxf/motor_plate.dxf  cutting/drilling templates (1:1).
* placements.json                every instance: key, name, step, 4x4 transform.
"""
from __future__ import annotations

import json
from pathlib import Path

import cadquery as cq
import numpy as np

import layout as L

HERE = Path(__file__).resolve().parent
PRINTED = ("carriage", "idler_slider", "tensioner_block", "idler_spacer", "hold_down", "hall_holder")


def loc(M: np.ndarray) -> cq.Location:
    from OCP.gp import gp_Trsf
    tr = gp_Trsf()
    tr.SetValues(*[float(v) for v in M[:3, :].ravel()])
    return cq.Location(tr)


def assembly(tilt_deg: float = 0.0) -> cq.Assembly:
    """Root -> one sub-assembly per assembly step ("05 Idler ...") -> parts,
    so the Onshape assembly's tree reads like the build instructions."""
    asm = cq.Assembly(name="Chain carousel test rig")
    subs: dict[int, cq.Assembly] = {}
    names: dict[str, int] = {}
    for p in L.placements(tilt_deg):
        if p.step not in subs:
            title = L.STEPS[p.step].split(":")[0]
            subs[p.step] = cq.Assembly(name=f"{p.step:02d} {title}")
        n = names.get(p.name, 0)
        names[p.name] = n + 1
        nm = p.name if n == 0 else f"{p.name} ({n + 1})"
        subs[p.step].add(L.shape(p.key), name=nm.replace("/", "-"), loc=loc(p.M), color=cq.Color(*p.color))
    for s in sorted(subs):
        asm.add(subs[s], name=subs[s].name)
    return asm


def main() -> None:
    import shutil
    shutil.rmtree(HERE / "step" / "components", ignore_errors=True)    # no stale parts
    (HERE / "step" / "components").mkdir(parents=True, exist_ok=True)
    (HERE / "stl").mkdir(exist_ok=True)
    (HERE / "dxf").mkdir(exist_ok=True)
    keys = sorted({p.key for p in L.placements()})
    for k in keys:
        if k in ("auger", "auger_cap") or k.startswith("sam_"):
            continue                                # already in reference/
        cq.exporters.export(cq.Workplane("XY").add(L.shape(k)), str(HERE / "step" / "components" / f"{k}.step"))
    for k in PRINTED:
        s = L.shape(k)
        if k == "idler_slider":                     # printed base-down
            s = s.rotate((0, 0, 0), (1, 0, 0), 0)
        cq.exporters.export(cq.Workplane("XY").add(s), str(HERE / "stl" / f"{k}.stl"), tolerance=0.02, angularTolerance=0.1)
    # 1:1 templates: deck (top view) and motor plate
    for k in ("deck_left", "deck_right"):
        sec = cq.Workplane("XY").add(L.shape(k)).section(-DECK_T_HALF)
        cq.exporters.export(sec, str(HERE / "dxf" / f"{k}.dxf"))
    plate = cq.Workplane("XY").add(L.shape("motor_plate")).section(3.0)
    cq.exporters.export(plate, str(HERE / "dxf" / "motor_plate.dxf"))
    asm = assembly()
    asm.save(str(HERE / "step" / "chain_carousel_rig.step"), exportType="STEP")
    pl = [dict(key=p.key, name=p.name, step=p.step, M=np.round(p.M, 6).tolist()) for p in L.placements()]
    (HERE / "placements.json").write_text(json.dumps(pl, indent=0))
    print("exported", len(keys), "unique parts,", len(pl), "instances")


DECK_T_HALF = 6.35

if __name__ == "__main__":
    main()
