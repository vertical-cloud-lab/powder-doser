"""Export the chain-carousel test rig v9 (v7 with Sam's 2026-11-17 note: no draft cage, the balance on a granite block, the beaker on the pan 32 mm under the exit, v7's EC cut back where it hung over the beaker, a bay window and a weighing chamber).

    python build.py

* step/chain_carousel_rig_v9.step  the whole rig as one STEP assembly: named,
  coloured instances that share their part definitions (the two chains'
  182 plain links are 2 parts, not 182), so Onshape imports it as one
  assembly plus one Part Studio per unique part.
* step/components/<key>.step     every unique part on its own (reference parts: reference/).
* stl/<part>.stl                 the printed parts, print-ready orientation.
* dxf/side_plate_front.dxf, dxf/side_plate_back.dxf  cutting/drilling templates (1:1); the acrylic
  panels, the bay window's sheets and door, the weighing chamber's baffles and deck (laser cut from 1/8 in cast acrylic).
* placements.json                every instance: key, name, step, 4x4 transform.
"""
from __future__ import annotations

import json
from pathlib import Path

import cadquery as cq
import numpy as np

import layout as L

HERE = Path(__file__).resolve().parent
PRINTED = ("carriage", "hold_down", "tensioner_block", "clevis_bracket", "latch_rail", "latch_bolt", "door_housing", "door_shutter",
           "side_tab", "side_tab_m", "catch", "guide7_cone", "guide7_vee")   # v7: the two guides; the clevis is the P16's base (v9: no riser)
PRINTED_REF = {"sam_electronics_carriage": "electronics_carriage_v9", "sam_mounting_plate": "mounting_plate_v7"}   # Sam's parts + v4-v7 features; v9's EC
ACRYLIC = ("panel_side", "panel_side_hatch", "panel_front_bay", "panel_back", "panel_top", "hatch_side", "bay9_door")
WORLD_ACRYLIC = ("bay9_front", "bay9_top", "bay9_side_p", "bay9_side_m", "baffle9_side_p", "baffle9_side_m", "baffle9_back", "deck9")   # built in place
STEP_FILE = "chain_carousel_rig_v9.step"


def loc(M: np.ndarray) -> cq.Location:
    from OCP.gp import gp_Trsf
    tr = gp_Trsf()
    tr.SetValues(*[float(v) for v in M[:3, :].ravel()])
    return cq.Location(tr)


def assembly(tilt_deg: float = 0.0) -> cq.Assembly:
    """Root -> one sub-assembly per assembly step ("05 Idler ...") -> parts,
    so the Onshape assembly's tree reads like the build instructions."""
    asm = cq.Assembly(name="Chain carousel test rig v9")
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
            s = L.P7.carriage_v7(print_web=True).val()  # outer face up, on supports under the plate between the ribs
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
    # v9: the bay window's sheets and the weighing chamber's baffles and deck are built in place (world): turn each so its thickness
    # runs along z, then cut it at mid-thickness
    for k in WORLD_ACRYLIC:
        sh = L.shape(k)
        bb = sh.BoundingBox()
        ext = {"x": bb.xlen, "y": bb.ylen, "z": bb.zlen}
        thin = min(ext, key=ext.get)
        if thin == "x":
            sh = sh.rotate((0, 0, 0), (0, 1, 0), -90)
        elif thin == "y":
            sh = sh.rotate((0, 0, 0), (1, 0, 0), 90)
        bb = sh.BoundingBox()
        sh = sh.translate((-bb.xmin, -bb.ymin, -bb.zmin))
        sec = cq.Workplane("XY").add(sh).section(L.ACRYLIC_T / 2)
        cq.exporters.export(sec, str(HERE / "dxf" / f"{k}.dxf"))
    asm = assembly()
    asm.save(str(HERE / "step" / STEP_FILE), exportType="STEP")
    pl = [dict(key=p.key, name=p.name, step=p.step, M=np.round(p.M, 6).tolist()) for p in L.placements()]
    (HERE / "placements.json").write_text(json.dumps(pl, indent=0))
    print("exported", len(keys), "unique parts,", len(pl), "instances")


PLATE_T_SIDE = L.PLATE_T_SIDE  # noqa

if __name__ == "__main__":
    main()
