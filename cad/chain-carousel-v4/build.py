"""Export the chain-carousel test rig v4 (the augers outside the loop).

    python build.py

* step/chain_carousel_rig_v4.step  the whole rig as one STEP assembly: named,
  coloured instances that share their part definitions (the two chains'
  182 plain links are 2 parts, not 182), so Onshape imports it as one
  assembly plus one Part Studio per unique part.
* step/components/<key>.step     every unique part on its own (reference parts: reference/).
* stl/<part>.stl                 the printed parts, print-ready orientation.
* dxf/side_plate_front.dxf, dxf/side_plate_back.dxf  cutting/drilling templates (1:1); the acrylic
  panels and hatch doors (laser cut from 1/8 in cast acrylic).
* placements.json                every instance: key, name, step, 4x4 transform.
"""
from __future__ import annotations

import json
from pathlib import Path

import cadquery as cq
import numpy as np

import layout as L

HERE = Path(__file__).resolve().parent
PRINTED = ("carriage", "hold_down", "tensioner_block", "clevis_bracket", "cradle", "latch_rail", "latch_bolt", "door_housing", "door_shutter",
           "side_tab", "side_tab_m", "catch")
PRINTED_REF = {"sam_electronics_carriage": "electronics_carriage_v4", "sam_mounting_plate": "mounting_plate_v4"}   # Sam's parts + v4 features
ACRYLIC = ("panel_side", "panel_side_hatch", "panel_front_hatch", "panel_back", "panel_top", "hatch_front", "hatch_side")
STEP_FILE = "chain_carousel_rig_v4.step"


def loc(M: np.ndarray) -> cq.Location:
    from OCP.gp import gp_Trsf
    tr = gp_Trsf()
    tr.SetValues(*[float(v) for v in M[:3, :].ravel()])
    return cq.Location(tr)


def assembly(tilt_deg: float = 0.0) -> cq.Assembly:
    """Root -> one sub-assembly per assembly step ("05 Idler ...") -> parts,
    so the Onshape assembly's tree reads like the build instructions."""
    asm = cq.Assembly(name="Chain carousel test rig v4")
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
    for k in PRINTED + tuple(PRINTED_REF):
        s = L.shape(k)
        if k == "carriage":                         # v4: the lugs and the latch housing stand on the outer face, so it prints
            s = L.P4.carriage_v4(print_web=True).val()  # outer face up, on supports under the plate between the ribs
            s = s.rotate((0, 0, 0), (1, 0, 0), -90)
        if k == "sam_mounting_plate":               # underside down (balls go in after printing)
            pass
        if k == "door_shutter":                     # flat on the bed
            s = s.rotate((0, 0, 0), (0, 1, 0), 90)
        bb = s.BoundingBox()
        s = s.translate((0, 0, -bb.zmin))
        cq.exporters.export(cq.Workplane("XY").add(s), str(HERE / "stl" / f"{PRINTED_REF.get(k, k)}.stl"), tolerance=0.02, angularTolerance=0.1)
    # 1:1 drilling templates for the two side plates (outer-face view, world y across, z up)
    for k, z in (("side_plate_front", -PLATE_T_SIDE / 2), ("side_plate_back", PLATE_T_SIDE / 2)):
        sec = cq.Workplane("XY").add(L.shape(k)).section(z)
        cq.exporters.export(sec, str(HERE / "dxf" / f"{k}.dxf"))
    # acrylic panels and hatch doors: outlines at mid-thickness (their own frame, z 0..3)
    for k in ACRYLIC:
        sec = cq.Workplane("XY").add(L.shape(k)).section(L.ACRYLIC_T / 2)
        cq.exporters.export(sec, str(HERE / "dxf" / f"{k}.dxf"))
    asm = assembly()
    asm.save(str(HERE / "step" / STEP_FILE), exportType="STEP")
    pl = [dict(key=p.key, name=p.name, step=p.step, M=np.round(p.M, 6).tolist()) for p in L.placements()]
    (HERE / "placements.json").write_text(json.dumps(pl, indent=0))
    print("exported", len(keys), "unique parts,", len(pl), "instances")


PLATE_T_SIDE = L.PLATE_T_SIDE  # noqa

if __name__ == "__main__":
    main()
