"""Export the chain-carousel test rig v2.

    python build.py

* step/chain_carousel_rig_v2.step  the whole rig as one STEP assembly: named,
  coloured instances that share their part definitions (the two chains'
  182 plain links are 2 parts, not 182), so Onshape imports it as one
  assembly plus one Part Studio per unique part.
* step/components/<key>.step     every unique part on its own (reference parts: reference/).
* stl/<part>.stl                 the printed parts, print-ready orientation.
* dxf/side_plate_front.dxf, dxf/side_plate_back.dxf  cutting/drilling templates (1:1).
* placements.json                every instance: key, name, step, 4x4 transform.
"""
from __future__ import annotations

import json
from pathlib import Path

import cadquery as cq
import numpy as np

import layout as L

HERE = Path(__file__).resolve().parent
PRINTED = ("carriage", "hold_down", "tensioner_block", "uyoke_base", "magnet_bracket", "clevis_bracket", "fork", "fork_arm",
           "vial_cup", "vial_funnel", "level_wedge", "pin_boss", "yoke_stop")
LASER = ("armature_tab", "uyoke_arm")         # 2 mm low-carbon steel, laser cut (SendCutSend): DXF outlines
STEP_FILE = "chain_carousel_rig_v2.step"


def loc(M: np.ndarray) -> cq.Location:
    from OCP.gp import gp_Trsf
    tr = gp_Trsf()
    tr.SetValues(*[float(v) for v in M[:3, :].ravel()])
    return cq.Location(tr)


def assembly(tilt_deg: float = 0.0) -> cq.Assembly:
    """Root -> one sub-assembly per assembly step ("05 Idler ...") -> parts,
    so the Onshape assembly's tree reads like the build instructions."""
    asm = cq.Assembly(name="Chain carousel test rig v2")
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
        if k == "carriage":                         # outer face down on the bed
            s = s.rotate((0, 0, 0), (1, 0, 0), 90)
        bb = s.BoundingBox()
        s = s.translate((0, 0, -bb.zmin))
        cq.exporters.export(cq.Workplane("XY").add(s), str(HERE / "stl" / f"{k}.stl"), tolerance=0.02, angularTolerance=0.1)
    # 1:1 drilling templates for the two side plates (outer-face view, world y across, z up)
    for k, z in (("side_plate_front", -PLATE_T_SIDE / 2), ("side_plate_back", PLATE_T_SIDE / 2)):
        sec = cq.Workplane("XY").add(L.shape(k)).section(z)
        cq.exporters.export(sec, str(HERE / "dxf" / f"{k}.dxf"))
    # laser-cut steel parts: outlines in their own plane
    tab = cq.Workplane("XY").add(L.shape("armature_tab")).section(-18.0 - 1.0)          # tab: plane z = -19 (Sam's frame)
    cq.exporters.export(tab, str(HERE / "dxf" / "armature_tab.dxf"))
    arm = cq.Workplane("XY").add(L.shape("uyoke_arm").rotate((0, 0, 0), (1, 0, 0), -90)).section(1.0)   # arm: x-z plane
    cq.exporters.export(arm, str(HERE / "dxf" / "uyoke_arm.dxf"))
    asm = assembly()
    asm.save(str(HERE / "step" / STEP_FILE), exportType="STEP")
    pl = [dict(key=p.key, name=p.name, step=p.step, M=np.round(p.M, 6).tolist()) for p in L.placements()]
    (HERE / "placements.json").write_text(json.dumps(pl, indent=0))
    print("exported", len(keys), "unique parts,", len(pl), "instances")


PLATE_T_SIDE = L.PLATE_T_SIDE

if __name__ == "__main__":
    main()
