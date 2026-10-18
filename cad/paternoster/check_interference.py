"""Pairwise interference checks for the paternoster carousel (OCC booleans).

    python check_interference.py            # home pose, every pair
    python check_interference.py --sweep    # chain indexed one module (10 pitches) in half-link steps:
                                            #   all 12 gondolas together cover every point of the loop
    python check_interference.py --tilt     # station: approach (actuator 0 -> docked) and tilt 0-90 deg
    python check_interference.py --swap     # loading position: module lifted and slid out of its gondola

A pair is reported when the two solids share more than 0.5 mm^3. Pairs that
touch by design (pin in its bore, bearing on its shaft, gear mesh, thread
in a nut) are skipped by part key in SKIP. Results go to checks/*.json.
"""
from __future__ import annotations

import itertools
import json
import math
import sys
import time
from pathlib import Path

import numpy as np

import kinematics as K
import layout as L
from params import MODULE_LINKS, N_MODULES

OUT = Path(__file__).resolve().parent / "checks"

SKIP = {("auger", "auger_cap"), ("auger", "sam_mounting_plate"), ("auger", "pinion"),
        ("shoulder_screw", "nut_m3"), ("shoulder_screw", "sleeve_bearing"), ("shoulder_screw", "thrust_washer"),
        ("shoulder_screw", "chain_sa1"), ("gondola", "sleeve_bearing"), ("gondola", "insert_m5"), ("insert_m5", "thumb_screw"), ("gondola", "thumb_screw"),
        ("nema11", "sam_electronics_carriage"), ("solenoid", "sam_electronics_carriage"), ("pinion", "sam_electronics_carriage"),
        ("nema11", "pinion"), ("actuator_body", "actuator_rod"), ("actuator_body", "clevis_bracket"), ("actuator_rod", "uyoke_base"),
        ("uyoke_arm", "uyoke_base"), ("uyoke_arm", "yoke_stop"), ("uyoke_arm", "yoke_stop_m"), ("stub_pin", "uyoke_arm"), ("stub_pin", "sam_electronics_carriage"),
        ("stub_pin", "pin_boss"), ("pin_boss", "sam_electronics_carriage"), ("stub_pin", "pin_boss_m"), ("pin_boss_m", "sam_electronics_carriage"), ("eclip", "stub_pin"), ("magnet_bracket", "sam_electronics_carriage"),
        ("dock_magnet", "magnet_bracket"), ("loc_pin", "sam_electronics_carriage"), ("armature_tab", "sam_mounting_plate"),
        ("shaft_idle", "sprocket_32"), ("shaft_drive", "sprocket_32"), ("shaft_idle", "flange_bearing"), ("shaft_drive", "flange_bearing"),
        ("idler_axle", "bearing_6202"), ("bearing_6202", "sprocket_32_idler"), ("idler_axle", "side_plate_front"),
        ("idler_axle", "side_plate_back"), ("idler_axle", "nut_m10"), ("coupling", "shaft_drive"), ("coupling", "nema34"),
        ("foot", "ext_x"), ("flange_bearing", "side_plate_front"), ("flange_bearing", "side_plate_back"),
        ("vial", "vial_funnel")}
SKIP = {tuple(sorted(k)) for k in SKIP}
CHAIN = ("chain_inner", "chain_outer", "chain_sa1")


def _skip(ka: str, kb: str) -> bool:
    if ka in CHAIN and kb in CHAIN:
        return True                      # links share pins and plates by design
    return tuple(sorted((ka, kb))) in SKIP


def overlaps(objs: list, pairs=None, min_vol: float = 0.5) -> list:
    boxes = [s.BoundingBox() for _, _, s in objs]
    hits = []
    it = pairs if pairs is not None else itertools.combinations(range(len(objs)), 2)
    for i, j in it:
        (ka, na, sa), (kb, nb, sb) = objs[i], objs[j]
        a, b = boxes[i], boxes[j]
        if a.xmax < b.xmin or b.xmax < a.xmin or a.ymax < b.ymin or b.ymax < a.ymin or a.zmax < b.zmin or b.zmax < a.zmin:
            continue
        if _skip(ka, kb):
            continue
        v = sa.intersect(sb).Volume()
        if v > min_vol:
            hits.append((na, nb, round(v, 2)))
    return hits


def objects(pl) -> list:
    return [(p.key, p.name, L.moved(p.key, p.M)) for p in pl]


def _report(tag: str, hits: list, extra: dict | None = None) -> None:
    OUT.mkdir(exist_ok=True)
    rec = {"check": tag, "clashes": [{"a": a, "b": b, "mm3": v} for a, b, v in hits], **(extra or {})}
    (OUT / f"{tag}.json").write_text(json.dumps(rec, indent=1) + "\n")
    print(f"{tag}: {len(hits)} clash(es) over 0.5 mm^3")
    for a, b, v in sorted(hits, key=lambda h: -h[2])[:40]:
        print(f"  {v:9.2f} mm^3  {a}  x  {b}")


def home() -> list:
    pl = L.placements()
    t0 = time.time()
    hits = overlaps(objects(pl))
    _report("home", hits, {"instances": len(pl), "seconds": round(time.time() - t0)})
    return hits


MOVERS = ("gondola", "thrust_washer", "sleeve_bearing", "shoulder_screw", "nut_m3", "sam_mounting_plate", "auger",
          "auger_cap", "thumb_screw", "insert_m5", "armature_tab") + CHAIN


def sweep(step: float = 0.5) -> list:
    """Chain shift HOME .. HOME + 10 links. Movers: gondolas, modules, pivots, chain links.
    The station parts are left out here (the station is retracted while the chain moves;
    --tilt covers it), and so is module 0's station carriage."""
    hits = []
    n = int(round(MODULE_LINKS / step))
    static = None
    for i in range(n + 1):
        s = K.HOME_SHIFT + i * step
        st = L.State(shift=s, ext=0.0)
        pl = L.placements(st)
        if static is None:
            static = [o for o, p in zip(objects([p for p in pl if p.key not in MOVERS and p.group != "station"
                                                   and p.group != "dispense" and p.key not in ("sprocket_32", "sprocket_32_idler", "shaft_drive", "shaft_idle")]),
                                        [p for p in pl if p.key not in MOVERS and p.group != "station" and p.group != "dispense"
                                         and p.key not in ("sprocket_32", "sprocket_32_idler", "shaft_drive", "shaft_idle")])]
        rot = [p for p in pl if p.key in ("sprocket_32", "sprocket_32_idler", "shaft_drive", "shaft_idle")]
        disp = [p for p in pl if p.group in ("station", "dispense")]
        mv = [p for p in pl if p.key in MOVERS]
        mo = objects(mv)
        others = static + objects(rot) + objects(disp)
        objs = mo + others
        nm = len(mo)
        pairs = []
        for a in range(nm):
            for b in range(a + 1, len(objs)):
                if b < nm and mv[a].module == mv[b].module and mv[a].module >= 0:
                    continue             # parts of one gondola move together
                if b < nm and mv[a].key in CHAIN and mv[b].key in CHAIN:
                    continue
                pairs.append((a, b))
        h = overlaps(objs, pairs)
        hits += [(f"{a} @s+{i * step:.1f}", b, v) for a, b, v in h]
        print(f"  shift +{i * step:4.1f} links: {len(h)} clash(es)", flush=True)
    _report("sweep", hits, {"step_links": step, "poses": n + 1})
    return hits


def tilt(angles=(5, 15, 30, 45, 60, 75, 90), exts=(0.0, 5.0, 10.0, 15.0, 19.5)) -> list:
    """Station: the electronics carriage rising (ext 0 -> docked), then module 1 + carriage
    tilting 5-90 deg, against everything else."""
    hits = []
    moving_keys = ("sam_mounting_plate", "auger", "auger_cap", "armature_tab", "sam_electronics_carriage", "nema11",
                   "pinion", "solenoid", "actuator_rod", "actuator_body", "uyoke_base", "uyoke_arm", "yoke_stop", "yoke_stop_m",
                   "stub_pin", "pin_boss", "pin_boss_m", "eclip", "magnet_bracket", "dock_magnet", "loc_pin")
    for kind, vals in (("ext", exts), ("tilt", angles)):
        for v in vals:
            st = L.State(ext=v) if kind == "ext" else L.State(tilt=v)
            pl = L.placements(st)
            mv = [p for p in pl if (p.key in moving_keys and (p.module in (0, -1)))]
            rest = [p for p in pl if p not in mv]
            mo, ro = objects(mv), objects(rest)
            objs = mo + ro
            pairs = [(a, b) for a in range(len(mo)) for b in range(len(mo), len(objs))]
            pairs += [(a, b) for a in range(len(mo)) for b in range(a + 1, len(mo))]
            h = overlaps(objs, pairs)
            hits += [(f"{a} @{kind}{v:g}", b, x) for a, b, x in h]
            print(f"  {kind} {v:5.1f}: {len(h)} clash(es)", flush=True)
    _report("tilt", hits)
    return hits


def swap(fracs=(0.1, 0.25, 0.4, 0.6, 0.8, 1.0)) -> list:
    """Loading position: the module of the gondola there is lifted, then slid out toward +y."""
    hits = []
    k_load = (0 + 3) % N_MODULES          # at home, module 4 (index 3) is at the loading position
    for f in fracs:
        st = L.State(out_module=k_load, out_frac=f)
        pl = L.placements(st)
        mv = [p for p in pl if p.module == k_load and p.key in ("sam_mounting_plate", "auger", "auger_cap", "armature_tab")]
        rest = [p for p in pl if p not in mv]
        mo, ro = objects(mv), objects(rest)
        objs = mo + ro
        pairs = [(a, b) for a in range(len(mo)) for b in range(len(mo), len(objs))]
        h = overlaps(objs, pairs)
        hits += [(f"{a} @out{f:g}", b, x) for a, b, x in h]
        print(f"  out {f:4.2f}: {len(h)} clash(es)", flush=True)
    _report("swap", hits)
    return hits


if __name__ == "__main__":
    if "--sweep" in sys.argv:
        sweep()
    elif "--tilt" in sys.argv:
        tilt()
    elif "--swap" in sys.argv:
        swap()
    else:
        home()
