"""Export the chain-carousel test rig.

    python build.py

* step/chain_carousel_rig.step  the whole rig as one STEP assembly: named,
  coloured instances that share their part definitions (the chain's 84
  plain links are 2 parts, not 84), so Onshape imports it as one assembly
  plus one Part Studio per unique part.
* step/parts/<key>.step          every unique part on its own.
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
    asm = cq.Assembly(name="Chain carousel test rig")
    names: dict[str, int] = {}
    for p in L.placements(tilt_deg):
        n = names.get(p.name, 0)
        names[p.name] = n + 1
        nm = p.name if n == 0 else f"{p.name} ({n + 1})"
        asm.add(L.shape(p.key), name=nm.replace("/", "-"), loc=loc(p.M), color=cq.Color(*p.color))
    return asm


def main() -> None:
    (HERE / "step" / "parts").mkdir(parents=True, exist_ok=True)
    (HERE / "stl").mkdir(exist_ok=True)
    (HERE / "dxf").mkdir(exist_ok=True)
    keys = sorted({p.key for p in L.placements()})
    for k in keys:
        cq.exporters.export(cq.Workplane("XY").add(L.shape(k)), str(HERE / "step" / "parts" / f"{k}.step"))
    for k in PRINTED:
        s = L.shape(k)
        if k == "idler_slider":                     # printed base-down
            s = s.rotate((0, 0, 0), (1, 0, 0), 0)
        cq.exporters.export(cq.Workplane("XY").add(s), str(HERE / "stl" / f"{k}.stl"), tolerance=0.02, angularTolerance=0.1)
    # 1:1 templates: deck (top view) and motor plate
    deck = cq.Workplane("XY").add(L.shape("deck")).section(-DECK_T_HALF)
    cq.exporters.export(deck, str(HERE / "dxf" / "deck.dxf"))
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
