"""Checks for the POWDER_DOSER_V2 electronics models (src/electronics/).

    python3 checks/pcb_checks.py        # from cad/text-to-cad, after building

Writes checks/results/pcb_checks.json.  What is measured (mm):
  1. bare board (STEP/electronics/pcb.step, body "fr4"): envelope vs the GKO
     outline (101.6 x 76.2 x 1.6), and every Gerber drill (137: PTH, vias,
     NPTH, 3 slots) matched to a cylindrical hole face of the right radius
     at the right centre (tolerance 0.01 mm);
  2. module registration (STEP/electronics/pcb_assembly.step): every pin of
     every module footprint in FlyingProbeTesting.json lands on a hole of the
     module placed over it (nearest hole centre within 0.05 mm);
  3. holder (STEP/electronics/pcb_holder_assembly.step): footprint inside the
     requested envelope x = -110..110, y = 0..70 and nothing at y < 0 above
     the wood (z > 0); holder solid valid with positive volume; no overlap
     (> 0.01 mm^3) between the holder and any populated-board body.
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src" / "electronics"))

import pcb_gerber as G  # noqa: E402
from pcb_layout import BOARD_H, BOARD_T, BOARD_W, GERBER_TO_BOARD  # noqa: E402

OUT = ROOT / "checks" / "results" / "pcb_checks.json"

FOOTPRINT_TO_MODULE = {
    "pico_l": "U2_pico_w", "pico_r": "U2_pico_w",
    "waveshareleft": "U6_pico_2ch_rs232", "waveshareright": "U6_pico_2ch_rs232",
    "ticpower": "U5_tic_t500", "stepperpins": "U5_tic_t500", "tic": "U5_tic_t500",
    "solenoiddriver": "U4_drv8871_solenoid",
    "hapticdriver": "U3_drv2605l_haptic",
    "5v_reg": "U1_d24v22f5_5v",
    "Shunt": "SR1_shunt_33v",
}


def hole_circles(shape, rmin: float, rmax: float):
    """Centres of circular edges (radius in [rmin, rmax]) of a shape."""
    out = []
    for e in shape.edges():
        if e.geom_type.name != "CIRCLE":
            continue
        r = e.radius
        if rmin <= r <= rmax:
            c = e.arc_center
            out.append((c.X, c.Y, c.Z, r))
    return out


def check_board(results: dict) -> bool:
    from cadgen import read_scene
    scene = read_scene(str(ROOT / "STEP" / "electronics" / "pcb.step"))
    fr4 = scene.resolve("#fr4").shape()
    bb = fr4.bounding_box()
    size = (bb.size.X, bb.size.Y, bb.size.Z)
    env_ok = (abs(bb.min.X) < 1e-3 and abs(bb.min.Y) < 1e-3 and abs(bb.min.Z) < 1e-3
              and abs(size[0] - BOARD_W) < 0.01 and abs(size[1] - BOARD_H) < 0.01
              and abs(size[2] - BOARD_T) < 0.01)

    cyl_faces = []
    for f in fr4.faces():
        if f.geom_type.name == "CYLINDER":
            for e in f.edges():
                if e.geom_type.name == "CIRCLE" or e.geom_type.name == "ELLIPSE":
                    c = e.arc_center
                    cyl_faces.append((c.X, c.Y, e.radius))
                    break
    ox, oy = GERBER_TO_BOARD
    misses = []
    drills = G.drills()
    for d in drills:
        if d.is_slot:
            pts = [(d.x + ox, d.y + oy), (d.x2 + ox, d.y2 + oy)]   # slot end arcs
        else:
            pts = [(d.x + ox, d.y + oy)]
        for x, y in pts:
            if not any(math.hypot(x - cx, y - cy) < 0.01 and abs(r - d.dia / 2) < 0.01
                       for cx, cy, r in cyl_faces):
                misses.append({"x": round(x, 3), "y": round(y, 3), "dia": d.dia,
                               "slot": d.is_slot})
    results["board"] = {
        "fr4_bbox_min": [round(v, 4) for v in (bb.min.X, bb.min.Y, bb.min.Z)],
        "fr4_size": [round(v, 4) for v in size],
        "expected_size": [BOARD_W, BOARD_H, BOARD_T],
        "envelope_ok": env_ok,
        "gerber_drills": len(drills),
        "drill_breakdown": {
            "pth": sum(1 for d in drills if d.plated and not d.via),
            "via": sum(1 for d in drills if d.via),
            "npth": sum(1 for d in drills if not d.plated),
            "slots": sum(1 for d in drills if d.is_slot)},
        "unmatched_drills": misses,
        "tolerance_mm": 0.01,
    }
    return env_ok and not misses


def check_registration(results: dict) -> bool:
    from cadgen import read_scene
    scene = read_scene(str(ROOT / "STEP" / "electronics" / "pcb_assembly.step"))
    _comps, pins = G.probe_data()
    ox, oy = GERBER_TO_BOARD
    holes_by_module: dict[str, list] = {}
    worst = {}
    ok = True
    for pin in pins:
        mod = FOOTPRINT_TO_MODULE.get(pin["component"])
        if mod is None:
            continue
        if mod not in holes_by_module:
            shape = scene.resolve(f"#{mod}").shape()
            holes_by_module[mod] = hole_circles(shape, 0.45, 0.52)
        x, y = pin["x"] + ox, pin["y"] + oy
        d = min(math.hypot(x - hx, y - hy) for hx, hy, _hz, _r in holes_by_module[mod])
        key = f"{pin['component']}->{mod}"
        worst[key] = max(worst.get(key, 0.0), d)
        if d > 0.05:
            ok = False
    results["registration"] = {
        "max_pin_to_hole_mm": {k: round(v, 4) for k, v in worst.items()},
        "tolerance_mm": 0.05,
        "pins_checked": sum(1 for p in pins if p["component"] in FOOTPRINT_TO_MODULE),
        "ok": ok,
    }
    return ok


def check_holder(results: dict) -> bool:
    from cadgen import read_scene
    from cadgen.geometry import overlap_volume
    scene = read_scene(str(ROOT / "STEP" / "electronics" / "pcb_holder_assembly.step"))
    holder = scene.resolve("#pcb_holder").shape()
    hb = holder.bounding_box()
    solids = holder.solids()
    vol = sum(s.volume for s in solids)
    from cadgen import read_step
    allshape = read_step(str(ROOT / "STEP" / "electronics" / "pcb_holder_assembly.step"))
    ab = allshape.bounding_box()
    above = [s for s in allshape.solids() if s.bounding_box(optimal=False).max.Z > 0.0]
    min_y_above_wood = min(s.bounding_box().min.Y for s in above)

    pcb = scene.resolve("#pcb_assembly").shape()
    hb_fast = holder.bounding_box(optimal=False)
    overlaps, tested = [], 0
    for s in pcb.solids():
        sb = s.bounding_box(optimal=False)
        if (sb.max.X < hb_fast.min.X or sb.min.X > hb_fast.max.X or sb.max.Y < hb_fast.min.Y
                or sb.min.Y > hb_fast.max.Y or sb.max.Z < hb_fast.min.Z or sb.min.Z > hb_fast.max.Z):
            continue
        for h in solids:
            tested += 1
            v = overlap_volume(h, s)
            if v > 0.01:
                overlaps.append(round(v, 4))
    foot_ok = hb.min.X >= -110 and hb.max.X <= 110 and hb.min.Y >= -1e-6 and hb.max.Y <= 70 + 1e-6
    results["holder"] = {
        "holder_bbox": [[round(v, 3) for v in (hb.min.X, hb.min.Y, hb.min.Z)],
                        [round(v, 3) for v in (hb.max.X, hb.max.Y, hb.max.Z)]],
        "assembly_bbox": [[round(v, 3) for v in (ab.min.X, ab.min.Y, ab.min.Z)],
                          [round(v, 3) for v in (ab.max.X, ab.max.Y, ab.max.Z)]],
        "min_y_of_parts_above_wood": round(min_y_above_wood, 3),
        "holder_solids": len(solids),
        "holder_valid": all(s.is_valid for s in solids),
        "holder_volume_mm3": round(vol, 1),
        "holder_mass_g_pla_100pct": round(vol * 1.24e-3, 1),
        "footprint_ok": foot_ok,
        "pcb_vs_holder_pairs_tested": tested,
        "pcb_vs_holder_overlaps_mm3": overlaps,
        "note": "wood screws extend to z < 0 on purpose (into the 38.1 mm board)",
    }
    return (foot_ok and min_y_above_wood >= -1e-6 and len(solids) == 1
            and all(s.is_valid for s in solids) and vol > 0 and not overlaps)


def main() -> int:
    results: dict = {}
    verdict = {}
    for name, fn in (("board", check_board), ("registration", check_registration),
                     ("holder", check_holder)):
        try:
            verdict[name] = bool(fn(results))
        except Exception as exc:          # a failed computation is not a pass
            verdict[name] = False
            results[f"{name}_error"] = repr(exc)
    results["verdict"] = verdict
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(results, indent=2))
    print(json.dumps(results, indent=2))
    return 0 if all(verdict.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
