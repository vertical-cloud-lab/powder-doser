"""Pairwise interference checks of the v2 rig (OCC booleans), in frame coordinates.

    python check_interference.py            # home pose (station docked), every pair
    python check_interference.py --sweep    # chain indexed one module (8 pitches) in half-link steps the way it runs;
                                            #   all 13 carriages together pass every point of the loop
    python check_interference.py --tilt     # station: electronics carriage rising (approach), then module +
                                            #   carriage + actuator tilting to the hinge's travel limit
    python check_interference.py --swap     # loading position: a carriage's screws out, slid 10 mm, lifted out

A pair is reported when the two solids share more than 0.5 mm^3. Pairs that touch by design (pin in its bore,
screw in its insert or nut, bearing on its shaft, gear mesh) are skipped by part key in SKIP; anything listed is a
real clash. One by-design contact can't be skipped by key: the mounting plate's edge passing the carriage's snap-hook
lips while the station tilts it; that part of the overlap is logged in checks/tilt.json, not counted (see overlaps). The frame pitch is a rigid rotation of everything (and is 0), so the checks run in frame coordinates.
Results go to checks/*.json.
"""
from __future__ import annotations

import itertools
import json
import sys
import time
from functools import lru_cache
from pathlib import Path

import cadquery as cq

import layout as L
from params import DOCK_EXT, HINGE_W, HOOK_SLIDE, MODULE_LINKS, RUN_DIRECTION, SAM_DROP, SCREW_OUT, SNAP_LAP, SNAP_X, TILT_MAX_FRAME

OUT = Path(__file__).resolve().parent / "checks"

SKIP = {("auger", "auger_cap"), ("auger", "sam_mounting_plate"), ("auger", "pinion"),
        ("clevis_screw", "clevis_bracket"), ("clevis_screw", "actuator_body"), ("clevis_screw", "nut_m3"),
        ("yoke_pin", "uyoke_base"), ("yoke_pin", "actuator_rod"), ("yoke_pin", "uyoke_arm"),
        # the 15T drive sprockets mesh with the drive chain: 0.3-0.7 mm slivers where the simplified tooth form meets a link as
        # it wraps on or off (0.50 mm3 with Nitro's real plate height); only the drive chain reaches these sprockets
        ("sprocket_15_motor", "chain_inner"), ("sprocket_15_motor", "chain_outer"), ("sprocket_15_shaft", "chain_inner"),
        ("sprocket_15_shaft", "chain_outer"),
        ("carriage", "nut_m3"), ("carriage", "m3x12_bhcs"), ("m3x12_bhcs", "nut_m3"), ("chain_a1", "m3x12_bhcs"),
        ("carriage", "clevis_pin"), ("clevis_pin", "sam_mounting_plate"), ("clevis_pin", "eclip"),
        ("armature_tab", "m3x6_fhcs"), ("insert_m3", "m3x6_fhcs"), ("insert_m3", "sam_mounting_plate"), ("m3x6_fhcs", "sam_mounting_plate"),
        ("m5x12_bhcs", "tnut_m5"), ("ext_post", "tnut_m5"), ("ext_x", "tnut_m5"), ("ext_post", "m5x12_bhcs"),
        ("bolt_m6x25", "nut_m6"), ("m5x25_shcs", "nut_m5"), ("nema34", "sprocket_15_motor"),
        ("nema34", "nut_m5"), ("m5x30_shcs", "nut_m5"), ("m5x10_shcs", "side_plate_front"), ("m5x10_shcs", "side_plate_back"),
        ("hold_down", "insert_m5"), ("insert_m5", "m5x16_shcs"), ("foot", "tnut_m5"), ("ext_x", "foot"), ("foot", "riser"),
        ("shaft", "sprocket_32"), ("shaft_drive", "sprocket_32"), ("shaft", "flange_bearing"), ("shaft_drive", "flange_bearing"),
        ("shaft_drive", "sprocket_15_shaft"),
        ("nema11", "sam_electronics_carriage"), ("solenoid", "sam_electronics_carriage"), ("pinion", "sam_electronics_carriage"),
        ("nema11", "pinion"), ("actuator_body", "actuator_rod"), ("actuator_body", "clevis_bracket"), ("actuator_rod", "station_yoke"),
        ("sam_electronics_carriage", "station_yoke"), ("magnet_bracket", "sam_electronics_carriage"), ("dock_magnet", "magnet_bracket"),
        ("magnet_bracket", "nema11"), ("vial", "vial_funnel"), ("vial", "vial_cup"), ("load_cell", "vial_cup"), ("level_wedge", "load_cell"),
        ("ext_vial_post", "level_wedge"), ("ext_vial_post", "ext_x"), ("ext_fork_post", "ext_y"), ("fork", "fork_arm"), ("ext_fork_post", "fork_arm"),
        ("clevis_bracket", "ext_y"), ("corner_bracket", "ext_y"), ("corner_bracket", "ext_x"), ("corner_bracket", "ext_post"),
        ("loc_pin", "sam_electronics_carriage"), ("loc_pin", "sam_mounting_plate"),
        ("sam_electronics_carriage", "stub_pin"), ("pin_boss", "stub_pin"), ("eclip_stub", "stub_pin"), ("actuator_rod", "uyoke_base"),
        ("uyoke_arm", "uyoke_base"), ("uyoke_arm", "yoke_stop"), ("pin_boss", "sam_electronics_carriage"),
        ("uyoke_arm", "yoke_stop_m"), ("pin_boss_m", "stub_pin"), ("pin_boss_m", "sam_electronics_carriage")}
SKIP = {tuple(sorted(k)) for k in SKIP}
CHAIN = ("chain_inner", "chain_outer", "chain_a1")


def _skip(ka: str, kb: str) -> bool:
    if ka in CHAIN and kb in CHAIN:
        return True                      # links share pins and plates by design
    return tuple(sorted((ka, kb))) in SKIP


def _moved(shape, M):
    from OCP.gp import gp_Trsf
    from OCP.TopLoc import TopLoc_Location
    tr = gp_Trsf()
    tr.SetValues(*[float(v) for v in M[:3, :].ravel()])
    return cq.Shape.cast(shape.wrapped.Moved(TopLoc_Location(tr)))


@lru_cache(None)
def _snap_lips() -> cq.Shape:
    """The snap hooks' two lips (the 0.8 mm overhang onto the mounting plate's edge), carriage frame (u, w, x)."""
    top = HINGE_W - SAM_DROP + 5.0                      # the plate's top face where the hooks hold it (parts.carriage)
    z = None
    for su in (-1, 1):
        u0, u1 = sorted((su * (25.2 - SNAP_LAP - 0.01), su * 25.2))
        b = cq.Workplane("XY").box(u1 - u0, 2.22, 12.02, centered=False).translate((u0, top + 0.19, SNAP_X - 6.01))
        z = b if z is None else z.union(b)
    return z.val()


SNAP_LOG: list = []      # (pose, plate, carriage, mm^3): the plate passing the snap lips, reported but not a clash


def overlaps(objs: list, pairs=None, min_vol: float = 0.5, tag: str = "") -> list:
    """Pairs of (key, name, shape, M) sharing more than min_vol. The one by-design contact that can't be skipped by key:
    while the station tilts the module (or the actuator pulls it back), the mounting plate's edge passes the carriage's
    two snap-hook lips, which flex 0.8 mm (SNAP_LAP) out of its way. The part of a plate/carriage overlap inside the lips
    is logged in SNAP_LOG; anything outside them (lugs, ribs, hook arms, window) still counts as a clash."""
    boxes = [o[2].BoundingBox() for o in objs]
    hits = []
    it = pairs if pairs is not None else itertools.combinations(range(len(objs)), 2)
    for i, j in it:
        (ka, na, sa, Ma), (kb, nb, sb, Mb) = objs[i], objs[j]
        a, b = boxes[i], boxes[j]
        if a.xmax < b.xmin or b.xmax < a.xmin or a.ymax < b.ymin or b.ymax < a.ymin or a.zmax < b.zmin or b.zmax < a.zmin:
            continue
        if _skip(ka, kb):
            continue
        common = sa.intersect(sb)
        v = common.Volume()
        if v > min_vol and {ka, kb} == {"carriage", "sam_mounting_plate"}:
            lips = _moved(_snap_lips(), Ma if ka == "carriage" else Mb)
            v_lip = common.intersect(lips).Volume()
            if v_lip > 0.01:
                SNAP_LOG.append((tag, na, nb, round(v_lip, 2)))
            v -= v_lip
        if v > min_vol:
            hits.append((na, nb, round(v, 2)))
    return hits


def objects(pl) -> list:
    return [(p.key, p.name, L.moved(p.key, p.M), p.M) for p in pl]


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


ROT = ("sprocket_32", "shaft", "shaft_drive", "sprocket_15_shaft", "sprocket_15_motor")


def sweep(step: float = 0.5) -> list:
    """Chain travel 0 .. one module (8 links) the way the machine runs (RUN_DIRECTION), in half-link steps.
    Movers: carriages and everything on them, and the chain links (exact polygonal kinematics). The station is
    retracted (actuator at 0) as it is whenever the chain moves."""
    hits = []
    n = int(round(MODULE_LINKS / step))
    static = None
    for i in range(n + 1):
        s = RUN_DIRECTION * i * step
        st = L.State(shift=s, ext=0.0)
        pl = L.placements(st)
        mv = [p for p in pl if p.module >= 0 or p.key in CHAIN and p.group == "chain"]
        mv_ids = {id(p) for p in mv}
        if static is None:
            static_pl = [p for p in pl if id(p) not in mv_ids and p.key not in ROT and p.group != "drive"]
            static = objects(static_pl)
        rot = [p for p in pl if p.key in ROT or p.group == "drive"]
        mo = objects(mv)
        objs = mo + static + objects(rot)
        nm = len(mo)
        pairs = []
        for a in range(nm):
            for b in range(a + 1, len(objs)):
                if b < nm and mv[a].module == mv[b].module and mv[a].module >= 0:
                    continue             # parts of one carriage move together
                if b < nm and mv[a].key in CHAIN and mv[b].key in CHAIN:
                    continue
                pairs.append((a, b))
        h = overlaps(objs, pairs)
        hits += [(f"{a} @{s:+.1f}", b, v) for a, b, v in h]
        print(f"  shift {s:+5.1f} links: {len(h)} clash(es)", flush=True)
    _report("sweep", hits, {"step_links": step, "poses": n + 1, "direction": RUN_DIRECTION})
    return hits


MOVING_STATION = ("sam_mounting_plate", "auger", "auger_cap", "armature_tab", "m3x6_fhcs", "insert_m3",
                  "sam_electronics_carriage", "nema11", "pinion", "solenoid", "magnet_bracket", "dock_magnet",
                  "loc_pin", "stub_pin", "pin_boss", "pin_boss_m", "eclip_stub", "uyoke_base", "uyoke_arm", "yoke_stop", "yoke_stop_m",
                  "actuator_rod", "actuator_body")


def tilt(angles=(5, 15, 25, 30, 38, 45, 60, 75, 90, TILT_MAX_FRAME), exts=(0.0, 5.0, 10.0, 15.0, 19.5, DOCK_EXT)) -> list:
    """Station: the electronics carriage rising (ext 0 -> docked), then module 1 + carriage + actuator tilting about
    the hinge, against everything else (carriage 1 itself included: its window, snap hooks and lugs)."""
    hits = []
    for kind, vals in (("ext", exts), ("tilt", angles)):
        for v in vals:
            st = L.State(ext=v) if kind == "ext" else L.State(tilt=float(v))
            pl = L.placements(st)
            mv = [p for p in pl if p.key in MOVING_STATION and p.module in (0, -1) and (p.group in ("station", "modules"))]
            ids = {id(p) for p in mv}
            rest = [p for p in pl if id(p) not in ids]
            mo, ro = objects(mv), objects(rest)
            objs = mo + ro
            pairs = [(a, b) for a in range(len(mo)) for b in range(len(mo), len(objs))]
            pairs += [(a, b) for a in range(len(mo)) for b in range(a + 1, len(mo))]
            h = overlaps(objs, pairs, tag=f"{kind}{v:g}")
            hits += [(f"{a} @{kind}{v:g}", b, x) for a, b, x in h]
            print(f"  {kind} {v:5.1f}: {len(h)} clash(es)", flush=True)
    _report("tilt", hits, {"snap_lip_contacts_by_design": [{"pose": t, "a": a, "b": b, "mm3": x} for t, a, b, x in SNAP_LOG]})
    return hits


def swap() -> list:
    """Loading position (+y side, carriage 4 at home): screws backed out, the carriage slid HOOK_SLIDE along the
    run to free its hooks, then lifted out sideways (+y) with its module."""
    hits = []
    k = 3
    so = SCREW_OUT                        # screws backed out until their tips clear the tabs (they stay in the plate)
    seq = [(3.0, 0.0, 0.0), (so, 0.0, 0.0), (so, HOOK_SLIDE / 2, 0.0), (so, HOOK_SLIDE, 0.0), (so, HOOK_SLIDE, 2.0),
           (so, HOOK_SLIDE, 10.0), (so, HOOK_SLIDE, 30.0), (so, HOOK_SLIDE, 60.0), (so, HOOK_SLIDE, 100.0), (so, HOOK_SLIDE, 150.0)]
    for so, sl, lf in seq:
        st = L.State(out_carriage=k, screws_out=so, out_slide=sl, out_lift=lf)
        pl = L.placements(st)
        mv = [p for p in pl if p.module == k]
        ids = {id(p) for p in mv}
        rest = [p for p in pl if id(p) not in ids]
        mo, ro = objects(mv), objects(rest)
        objs = mo + ro
        pairs = [(a, b) for a in range(len(mo)) for b in range(len(mo), len(objs))]
        h = overlaps(objs, pairs)
        hits += [(f"{a} @screws{so:g}/slide{sl:g}/lift{lf:g}", b, x) for a, b, x in h]
        print(f"  screws {so:4.1f} slide {sl:4.1f} lift {lf:5.1f}: {len(h)} clash(es)", flush=True)
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
