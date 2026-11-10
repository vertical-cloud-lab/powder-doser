"""Pairwise interference checks of the v6 rig (OCC booleans), in frame coordinates.

    python check_interference.py            # home pose (station docked), every pair
    python check_interference.py --sweep    # chain indexed one module (8 pitches) in half-link steps the way it runs;
                                            #   all 13 carriages together pass every point of the loop
    python check_interference.py --tilt     # station: electronics carriage rising (approach), then module +
                                            #   carriage + actuator tilting to the hinge's travel limit
    python check_interference.py --latch    # v5: the station's latch rail against everything while carriages pass it, the EC rises and tilts
    python check_interference.py --swap     # loading position: a carriage's screws out, slid 10 mm, lifted out past the side tabs
    python check_interference.py --scale    # v5: the HR-202i (and, as a second check, the lab's HR-100A) at the dose point, against
                                            #   everything; the station parked, then docked and tilted to 30 and 50 deg

A pair is reported when the two solids share more than 0.5 mm^3. Pairs that touch by design (pin in its bore,
screw in its insert or nut, bearing on its shaft, gear mesh) are skipped by part key in SKIP; anything listed is a
real clash. v3 has no snap hooks (the latch replaced them), so nothing is logged as a by-design flex any more. v5: the HR-202i
stands at the dose point in every check (home, tilt, sweep), its top door open while the station tilts; --scale also tries
the HR-100A there. The frame pitch is 0, so the checks run in frame coordinates.
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
from params import PARK_DROP, HINGE_W, HOOK_SLIDE, MODULE_LINKS, RUN_DIRECTION, SAM_DROP, SCREW_OUT, TILT_MAX_FRAME, HATCH_OPEN_DEG

OUT = Path(__file__).resolve().parent / "checks"

SKIP = {("auger", "auger_cap"), ("auger", "sam_mounting_plate"), ("auger", "pinion"),
        ("clevis_screw", "clevis_bracket"), ("clevis_screw", "actuator_body"), ("clevis_screw", "nut_m3_clevis"),
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
        ("uyoke_arm", "yoke_stop_m"), ("pin_boss_m", "stub_pin"), ("pin_boss_m", "sam_electronics_carriage"),
        # ---- v3: pressed, bonded or seated by design
        ("kc_ball", "sam_mounting_plate"), ("kc_ball", "sam_electronics_carriage"), ("kc_ball", "vee_dowel"), ("kc_ball", "armature_v3"),
        ("kc_ball", "cradle"), ("kc_ball", "flat_pad"), ("vee_dowel", "sam_electronics_carriage"), ("vee_dowel", "cradle"),
        ("flat_pad", "cradle"), ("kc_magnet", "sam_electronics_carriage"), ("dock_magnet", "sam_electronics_carriage"),
        ("armature_v3", "m3x6_fhcs"), ("armature_v3", "sam_mounting_plate"),
        ("door_shutter", "door_housing"), ("door_spring", "door_housing"), ("door_spring", "door_shutter"),
        ("door_spring_open", "door_housing"), ("door_spring_open", "door_shutter"), ("door_shutter", "sam_electronics_carriage"),
        ("m2x8_shcs", "door_housing"), ("m2x8_shcs", "sam_mounting_plate"),
        ("latch_bolt", "carriage"), ("latch_follower", "latch_bolt"), ("latch_follower", "carriage"), ("latch_spring", "carriage"),
        ("latch_spring", "latch_bolt"), ("latch_follower", "latch_rail"),
        ("clevis_screw", "sam_electronics_carriage"), ("clevis_screw", "actuator_rod"), ("nut_m3_clevis", "sam_electronics_carriage"),
        ("ext_cradle_post", "cradle"), ("ext_cradle_post", "ext_y"), ("ext_latch_post", "latch_rail"), ("ext_latch_post", "ext_y"),
        ("side_tab", "insert_m5"), ("side_tab_m", "insert_m5"),
        ("standoff", "ext_post"), ("standoff", "ext_x"), ("standoff", "ext_y"), ("standoff_back", "ext_post"),
        ("standoff", "panel_side"), ("standoff", "panel_side_hatch"), ("standoff", "panel_front_hatch"), ("standoff_back", "panel_back"),
        ("hinge_leaf", "panel_side_hatch"), ("hinge_leaf", "panel_front_hatch"), ("hinge_leaf", "hatch_front"), ("hinge_leaf", "hatch_side"),
        ("catch", "panel_side_hatch"), ("catch", "panel_front_hatch"), ("panel_top", "panel_side"), ("panel_top", "panel_side_hatch"),
        ("panel_top", "panel_front_hatch"), ("panel_top", "panel_back"), ("panel_front_hatch", "panel_side"),
        ("panel_front_hatch", "panel_side_hatch"), ("panel_back", "panel_side"), ("panel_back", "panel_side_hatch"),
        ("hr100a_body", "hr100a_glass"), ("hr100a_body", "hr100a_pan"), ("beaker", "hr100a_pan"), ("hinge_leaf", "hinge_leaf"),
        ("side_tab", "m5x8_shcs"), ("side_tab_m", "m5x8_shcs"), ("m5x8_shcs", "side_plate_front"), ("m5x8_shcs", "side_plate_back"),
        ("flat_pad_v4", "sam_mounting_plate"), ("flat_pad_v4", "kc_ball"),
        ("catch", "hatch_front"), ("catch", "hatch_side"), ("ec_pin_screw", "sam_electronics_carriage"), ("ec_pin_screw", "actuator_rod"),
        ("ec_pin_screw", "nut_m3_clevis"), ("ec_pin_screw", "ptfe_washer"), ("actuator_rod", "ptfe_washer"), ("ptfe_washer", "sam_electronics_carriage"),
        # ---- v5: the lift bar in the EC's saddles and the end blocks' clamps; the rod ends' tabs between the end blocks' cheeks
        # on their shoulder screws; shelves, guides, posts and beams screwed to each other; the balance's own parts; the
        # riser on the pan and the beaker in the riser's cup
        ("lift_bar", "sam_electronics_carriage"), ("bar_end", "lift_bar"), ("bar_end", "clevis_screw"), ("bar_end", "nut_m3_clevis"), ("actuator_rod", "bar_end"),
        ("clevis_bracket", "p16_shelf"), ("ext_station_post", "p16_shelf"), ("ext_station_post", "guide_block"), ("corner_bracket", "ext_station_post"),
        ("corner_bracket", "ext_latch_post5"), ("corner_bracket", "ext_latch_beam"), ("ext_latch_beam", "ext_latch_post5"), ("ext_latch_post5", "ext_x"),
        ("ext_station_post", "ext_x"), ("ext_latch_beam", "latch_rail"),
        ("hr202i_body", "hr202i_display"), ("hr202i_body", "hr202i_front_glass"), ("hr202i_body", "hr202i_pan"), ("hr202i_body", "hr202i_door_left"),
        ("hr202i_body", "hr202i_door_right"), ("hr202i_body", "hr202i_top_door"), ("hr202i_door_left", "hr202i_front_glass"),
        ("hr202i_door_right", "hr202i_front_glass"), ("hr202i_front_glass", "hr202i_top_door"), ("hr202i_door_left", "hr202i_top_door"),
        ("hr202i_door_right", "hr202i_top_door"), ("beaker_riser", "hr202i_pan"), ("beaker", "beaker_riser"), ("beaker", "hr100a_pan"),
        # ---- v6: the lift frame's bars in the end blocks' clamps and the EC's hooks; the rod ends' tabs between the end blocks'
        # cheeks; the shoes' noses on their seats (parked); shelves, guides, rungs and brackets screwed together; the tilt P16
        # on its bracket and its rod end on the EC's tilt arm; magnets pressed into the plate; the latch cam's foot on the back plate
        ("lift_bar", "lift_end"), ("lift_bar", "sam_electronics_carriage"), ("actuator_rod", "lift_end"), ("bar_end", "p16l_rod"), ("p16l_rod", "lift_end"),
        ("clevis_screw", "lift_end"), ("lift_end", "nut_m3_clevis"), ("p16l_body", "p16l_rod"), ("clevis_bracket", "p16l_body"),
        ("clevis_screw", "p16l_body"), ("clevis_screw", "p16l_rod"), ("clevis_bracket", "lift_shelf"), ("lift_shelf", "rung"),
        ("guide_cone", "rung"), ("guide_vee", "rung"), ("corner_bracket", "rung"), ("ext_post", "rung"), ("guide_cone", "lift_end"),
        ("guide_vee", "lift_end"), ("side_plate_back", "tilt_bracket"), ("clevis_screw", "tilt_bracket"), ("actuator_body", "tilt_bracket"),
        ("nut_m3_clevis", "tilt_bracket"), ("kc6_magnet", "sam_mounting_plate"), ("latch_rail", "side_plate_back"), ("latch_rail", "m5x12_bhcs"),
        ("m5x12_bhcs", "side_plate_back"), ("m5x12_bhcs", "tilt_bracket"), ("actuator_rod", "nut_m3_clevis"), ("kc6_magnet", "kc_magnet")}
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
    pl = L.placements(L.State())
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
        st = L.State(shift=s, ext=0.0, enclosure=False)
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


def latch(step: float = 0.25, span: float = 2.5) -> list:
    """v5, 2026-11-10: the station's latch rail, moved to the followers' -x side so that it pushes them open, against every
    other part while a carriage passes it (quarter-link steps over +-span links, station parked), then with the EC rising and
    the module tilting at the station. Also reports how much each follower overlaps the rail's cam, a by-design contact that
    the other checks skip: it should stay a sliver (the round follower on the 25 deg ramp), never a block."""
    hits, contact = [], []
    poses = [(-span + i * step, 0.0, 0.0) for i in range(int(round(2 * span / step)) + 1)]
    poses += [(0.0, e, 0.0) for e in (14.0, PARK_DROP)] + [(0.0, PARK_DROP, a) for a in (10.0, 20.0, 30.0, 40.0)]
    for s, e, a in poses:
        st = L.State(shift=s, ext=e, tilt=a, magnet_on=a > 0, enclosure=False)
        pl = L.placements(st)
        rail = [p for p in pl if p.key == "latch_rail"]
        objs = objects(rail) + objects([p for p in pl if p.key != "latch_rail"])
        h = overlaps(objs, [(0, j) for j in range(1, len(objs))])
        hits += [(f"{x} @shift {s:+.2f}, ext {e:.0f}, tilt {a:.0f}", y, v) for x, y, v in h]
        rb = objs[0][2].BoundingBox()
        for k, nm, sh, M in objs[1:]:
            if k != "latch_follower":
                continue
            b = sh.BoundingBox()
            if b.xmax < rb.xmin or rb.xmax < b.xmin or b.ymax < rb.ymin or rb.ymax < b.ymin or b.zmax < rb.zmin or rb.zmax < b.zmin:
                continue
            v = objs[0][2].intersect(sh).Volume()
            if v > 1e-4:
                contact.append({"shift": s, "follower": nm, "mm3": round(v, 3)})
        print(f"  shift {s:+5.2f}, ext {e:4.1f}, tilt {a:4.1f}: {len(h)} clash(es)", flush=True)
    _report("latch", hits, {"poses": len(poses), "step_links": step, "span_links": span,
                            "follower_on_cam": contact, "follower_on_cam_max_mm3": max((c["mm3"] for c in contact), default=0.0)})
    return hits


MOVING_GROUPS = ("station_ec", "station_act", "station_lift", "station_tilt")   # v6: EC, lift frame, all three P16s; plus the station module
TOP_OPEN = 205.0                                          # v5: the HR-202i's top door slid back while the station doses (A&D's DXF)


def tilt(angles=(5, 10, 20, 30, 40, 50, 60, 70, 80, 90), exts=(0.0, 5.0, 10.0, 15.0, 19.5, 24.0, PARK_DROP), tag: str = "tilt") -> list:
    """Station: the EC rising out of its cradle (ext 0 -> docked; the door opens over the last 8.5 mm), then module 1 + EC
    + actuator tilting about the hinge, against everything else (carriage 1 included: its window, pads, latch, lugs)."""
    hits = []
    for kind, vals in (("ext", exts), ("tilt", angles)):
        for v in vals:
            st = L.State(ext=v, top_door=TOP_OPEN) if kind == "ext" else L.State(tilt=float(v), top_door=TOP_OPEN)
            pl = L.placements(st)
            k_st = L.carriage_at(L.CARRIAGE_LINK0, 0.0)
            mv = [p for p in pl if p.group in MOVING_GROUPS or (p.group == "modules" and p.module == k_st)]
            ids = {id(p) for p in mv}
            rest = [p for p in pl if id(p) not in ids]
            mo, ro = objects(mv), objects(rest)
            objs = mo + ro
            pairs = [(a, b) for a in range(len(mo)) for b in range(len(mo), len(objs))]
            pairs += [(a, b) for a in range(len(mo)) for b in range(a + 1, len(mo))]
            h = overlaps(objs, pairs, tag=f"{kind}{v:g}")
            hits += [(f"{a} @{kind}{v:g}", b, x) for a, b, x in h]
            print(f"  {kind} {v:5.1f}: {len(h)} clash(es)", flush=True)
    _report(tag, hits, {"angles": list(angles), "exts": list(exts)})
    return hits


def swap() -> list:
    """v4: at the loading position (+y side, module 4 at home), the side hatch open, the auger pulled straight off its plate
    (out of the loop, through the hatch) in steps, against everything else; then the carriage's own removal as v3 (screws
    out, slid 10 mm, lifted out) for completeness."""
    hits = []
    k = 3
    for ao in (5.0, 15.0, 30.0, 60.0, 100.0, 140.0):
        st = L.State(out_auger=k, auger_out=ao, hatch_side=HATCH_OPEN_DEG)
        pl = L.placements(st)
        mv = [p for p in pl if p.module == k and p.key in ("auger", "auger_cap")]
        ids = {id(p) for p in mv}
        rest = [p for p in pl if id(p) not in ids]
        mo, ro = objects(mv), objects(rest)
        objs = mo + ro
        pairs = [(a, b) for a in range(len(mo)) for b in range(len(mo), len(objs))]
        h = overlaps(objs, pairs)
        hits += [(f"{a} @auger_out{ao:g}", b, x) for a, b, x in h]
        print(f"  auger out {ao:5.1f}: {len(h)} clash(es)", flush=True)
    so = SCREW_OUT
    for so_, sl, lf in [(so, HOOK_SLIDE, 0.0), (so, HOOK_SLIDE, 30.0), (so, HOOK_SLIDE, 100.0)]:
        st = L.State(out_carriage=k, screws_out=so_, out_slide=sl, out_lift=lf, hatch_side=HATCH_OPEN_DEG)
        pl = L.placements(st)
        mv = [p for p in pl if p.module == k]
        ids = {id(p) for p in mv}
        rest = [p for p in pl if id(p) not in ids]
        mo, ro = objects(mv), objects(rest)
        objs = mo + ro
        pairs = [(a, b) for a in range(len(mo)) for b in range(len(mo), len(objs))]
        h = overlaps(objs, pairs)
        hits += [(f"{a} @carriage slide{sl:g}/lift{lf:g}", b, x) for a, b, x in h]
        print(f"  carriage slide {sl:4.1f} lift {lf:5.1f}: {len(h)} clash(es)", flush=True)
    _report("swap", hits)
    return hits


def scale() -> list:
    """v5: the balance with its pan centre under the dose point, against everything else: the HR-202i with the station
    parked, docked, and tilted to 30 and 50 deg (its top door open), then the lab's HR-100A (stock breeze break) parked and
    at 30 deg. Every hit would be a part in the balance's way; v5 is meant to have none."""
    hits, poses = [], []
    for model, states in (("hr202i", (dict(ext=0.0), dict(ext=PARK_DROP, top_door=TOP_OPEN), dict(tilt=30.0, top_door=TOP_OPEN),
                                       dict(tilt=50.0, top_door=TOP_OPEN))),
                          ("hr100a", (dict(ext=0.0), dict(tilt=30.0)))):
        for kw in states:
            pl = L.placements(L.State(scale_model=model, **kw))
            sc = [p for p in pl if p.group == "scale"]
            rest = [p for p in pl if p.group != "scale"]
            so, ro = objects(sc), objects(rest)
            objs = so + ro
            pairs = [(a, b) for a in range(len(so)) for b in range(len(so), len(objs))]
            h = overlaps(objs, pairs, min_vol=0.0)
            tag = f"{model} {kw}"
            hits += [(f"{a} @{tag}", b, v) for a, b, v in h]
            poses.append(tag)
            print(f"  {tag}: {len(h)} part(s) in the balance's way", flush=True)
    _report("scale", hits, {"pan_centre": [round(float(v), 2) for v in L.scale_pan_target()[:2]], "poses": poses,
                            "note": "v5: the balance at the dose point; any hit is a part in its way (min volume 0)"})
    return hits


if __name__ == "__main__":
    if "--sweep" in sys.argv:
        # --step N: a coarser sweep (N links per pose) when time is short; the JSON records the step and pose count
        sweep(float(sys.argv[sys.argv.index("--step") + 1])) if "--step" in sys.argv else sweep()
    elif "--latch" in sys.argv:
        latch()
    elif "--tilt" in sys.argv:
        # v6: --angles 5,10 --exts 0,5 --tag tilt_a: subsets run as parallel processes, merged by hand into checks/tilt.json
        a = [float(v) for v in sys.argv[sys.argv.index("--angles") + 1].split(",") if v] if "--angles" in sys.argv else None
        e = [float(v) for v in sys.argv[sys.argv.index("--exts") + 1].split(",") if v] if "--exts" in sys.argv else None
        tg = sys.argv[sys.argv.index("--tag") + 1] if "--tag" in sys.argv else "tilt"
        tilt(**{k: v for k, v in (("angles", a), ("exts", e)) if v is not None}, tag=tg)
    elif "--swap" in sys.argv:
        swap()
    elif "--scale" in sys.argv:
        scale()
    else:
        home()
