"""Pack every printed part onto plates and slice them with Bambu Studio's command line.

    python slice_all.py            # all plates -> plates/<plate>.gcode.3mf, plates.json, preview PNGs

- Printer: Bambu Lab A1 mini, 0.4 mm nozzle (read live over LAN before slicing: 0.4 mm stainless,
  2026-11-28 09:01 UTC). The 245 mm drum shaft goes on the H2D's LEFT nozzle (0.4 mm; the right one
  had 0.6 mm in), sliced for 0.4 mm, and the slice is checked to use only that nozzle.
- Process: 0.20mm Standard, 3 walls, 25 % gyroid-free grid infill ("solid" plates 100 %), Bambu PLA
  Basic. Tree supports only on plates that hold a part flagged in SUPPORT.
- Bambu Studio 02.09.02.62 (AppImage, extracted to /tmp/bambu). Its system presets inherit from
  base presets; the CLI does not resolve that, so `flatten()` merges each chain into a full preset.
"""
from __future__ import annotations

import json
import math
import os
import re
import shutil
import subprocess
import sys
import time
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
CAD = HERE.parent / "cad" / "out"
PLATES = HERE / "plates"
BAMBU = Path(os.environ.get("BAMBU_ROOT", "/tmp/bambu/squashfs-root"))
PROFILES = BAMBU / "resources" / "profiles" / "BBL"
WORK = Path("/tmp/slice-work")

SUPPORT = {"tapper_carriage", "drum_shaft", "camera_rod_clamp", "camera_carriage"}
# Structural parts whose surfaces don't touch powder or set a dimension: 0.24 mm Draft, 15 % infill
DRAFT = {"tapper_base", "tilt_base", "micro_base", "micro_column", "ucs_base", "camera_tower", "backlight_foot",
         "tripod_spider", "hc_slurry_tray", "hc_shelf", "hc_sensor_clip", "hc_fan_mount", "spread_bracket",
         "fc_cradle", "fc_pcb_box", "fc_pcb_lid", "fc_insulator_base", "cup_holder", "pan_adapter",
         "stage_motor_block", "stage_end_block"}
SOLID = 100
SPACING = 6.0
BED = {"A1M": (180.0, 180.0), "H2D": (350.0, 320.0)}
MARGIN = 6.0
PRESETS = {
    "A1M": ("Bambu Lab A1 mini 0.4 nozzle", "0.20mm Standard @BBL A1M", "Bambu PLA Basic @BBL A1M"),
    "A1M_draft": ("Bambu Lab A1 mini 0.4 nozzle", "0.24mm Draft @BBL A1M", "Bambu PLA Basic @BBL A1M"),
    "H2D": ("Bambu Lab H2D 0.4 nozzle", "0.20mm Standard @BBL H2D", "Bambu PLA Basic @BBL H2D"),
}


def flatten(cat: str, name: str) -> dict:
    d = json.loads((PROFILES / cat / f"{name}.json").read_text())
    if d.get("inherits"):
        base = flatten(cat, d["inherits"])
        base.update({k: v for k, v in d.items() if k != "inherits"})
        d = base
    d.pop("inherits", None)
    return d


def presets(printer: str, infill: int, support: bool, out: Path, draft: bool = False) -> tuple[Path, Path, Path]:
    m, p, f = PRESETS[printer + ("_draft" if draft else "")]
    mach, proc, fil = flatten("machine", m), flatten("process", p), flatten("filament", f)
    for d in (mach, proc, fil):
        d["from"] = "system"
        d["is_custom_defined"] = "0"
    proc["wall_loops"] = "3"
    proc["sparse_infill_density"] = f"{infill}%"
    if infill >= 100:
        proc["sparse_infill_pattern"] = "zig-zag"   # Bambu rejects grid at 100 %
    proc["enable_support"] = "1" if support else "0"
    proc["support_type"] = "tree(auto)"
    proc["support_on_build_plate_only"] = "0"
    proc["brim_type"] = "auto_brim"
    proc["curr_bed_type"] = "Textured PEI Plate"     # the lab's A1 minis and H2D print PLA on textured PEI
    if printer == "H2D":   # one filament, on the LEFT nozzle only (filament_map 1 = left)
        proc["filament_map_mode"] = "Manual"
        proc["filament_map"] = ["1"]
    out.mkdir(parents=True, exist_ok=True)
    paths = (out / "machine.json", out / "process.json", out / "filament.json")
    for path, d in zip(paths, (mach, proc, fil)):
        path.write_text(json.dumps(d, indent=1))
    return paths


def pack(items: list[tuple[str, float, float]], bed=(180.0, 180.0)) -> list[list[tuple[str, float, float, float, float, bool]]]:
    """Shelf packing. items: (name, w, d). Returns plates of (name, x, y, w, d, rotated)."""
    W, D = bed[0] - 2 * MARGIN, bed[1] - 2 * MARGIN
    todo = sorted(items, key=lambda t: max(t[1], t[2]), reverse=True)
    plates = []
    while todo:
        plate, shelves, left = [], [], []
        y_used = 0.0
        for name, w, d in todo:
            placed = False
            for rot in (False, True):
                ww, dd = (d, w) if rot else (w, d)
                if ww > W or dd > D:
                    continue
                for sh in shelves:     # [y0, height, x_used]
                    if dd <= sh[1] and sh[2] + ww <= W:
                        plate.append((name, sh[2], sh[0], ww, dd, rot))
                        sh[2] += ww + SPACING
                        placed = True
                        break
                if placed:
                    break
                if y_used + dd <= D:
                    shelves.append([y_used, dd, ww + SPACING])
                    plate.append((name, 0.0, y_used, ww, dd, rot))
                    y_used += dd + SPACING
                    placed = True
                    break
            if not placed:
                left.append((name, w, d))
        if not plate:
            raise SystemExit(f"cannot place {left}")
        plates.append(plate)
        todo = left
    return plates


def slice_plate(key: str, printer: str, infill: int, support: bool, files: list[Path], draft: bool = False) -> dict:
    wd = WORK / key
    if wd.exists():
        shutil.rmtree(wd)
    wd.mkdir(parents=True)
    mach, proc, fil = presets(printer, infill, support, wd / "presets", draft)
    out3mf = wd / f"{key}.gcode.3mf"
    cmd = ["xvfb-run", "-a", str(BAMBU / "AppRun"), "--debug", "1", "--slice", "0", "--arrange", "0",
           "--orient", "0", "--load-settings", f"{mach};{proc}", "--load-filaments", str(fil),
           "--export-3mf", out3mf.name, "--outputdir", str(wd)] + [str(f) for f in files]
    t0 = time.time()
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=1800)
    res = json.loads((wd / "result.json").read_text()) if (wd / "result.json").exists() else {}
    rec = {"plate": key, "printer": printer, "infill_pct": infill, "supports": support, "draft_0p24": draft,
           "slice_s": round(time.time() - t0, 1), "return_code": res.get("return_code", r.returncode),
           "error": res.get("error_string", r.stderr[-400:])}
    g = wd / "plate_1.gcode"
    if g.exists():
        head = g.read_text(errors="ignore")[:20000]
        def grab(pat):
            m = re.search(pat, head)
            return m.group(1).strip() if m else None
        rec["time"] = grab(r"total estimated time: ([^\n;]+)")
        rec["model_time"] = grab(r"model printing time: ([^;\n]+)")
        rec["layers"] = grab(r"total layer number: (\d+)")
        rec["filament_m"] = round(float(grab(r"total filament length \[mm\] : ([\d.]+)") or 0) / 1000, 2)
        rec["filament_g"] = float(grab(r"total filament weight \[g\] : ([\d.]+)") or 0)
        rec["max_z_mm"] = float(grab(r"max_z_height: ([\d.]+)") or 0)
        txt = g.read_text(errors="ignore")
        rec["tool_changes"] = sorted(set(re.findall(r"^(T\d+)\s*$", txt, flags=re.M)))
        rec["gcode_md5"] = __import__("hashlib").md5(g.read_bytes()).hexdigest()
    if res.get("sliced_plates"):
        sp = res["sliced_plates"][0]
        rec["predicted_s"] = sp.get("main_predication")
        rec["placed"] = [{"name": o["name"], **{k: round(v, 1) for k, v in o["bbox"].items()}} for o in sp.get("objects", [])]
    if out3mf.exists():
        PLATES.mkdir(parents=True, exist_ok=True)
        shutil.copy(out3mf, PLATES / out3mf.name)
        with zipfile.ZipFile(out3mf) as z:
            names = z.namelist()
            if "Metadata/project_settings.config" in names:
                ps = json.loads(z.read("Metadata/project_settings.config"))
                rec["check"] = {k: ps.get(k) for k in ("printer_model", "nozzle_diameter", "layer_height", "wall_loops",
                                                       "sparse_infill_density", "enable_support", "filament_type",
                                                       "filament_map", "nozzle_temperature", "curr_bed_type")}
    return rec


def gcode_extents(path: Path):
    """Min/max X and Y of every extruding move after the start G-code (purge lines excluded)."""
    if not path.exists():
        return None
    xs, ys = [], []
    x = y = None
    started = False
    for line in path.open(errors="ignore"):
        if not started:
            if line.startswith("; CHANGE_LAYER") or line.startswith(";LAYER_CHANGE"):
                started = True
            continue
        if line.startswith(("G1 ", "G0 ", "G2 ", "G3 ")):
            mx = re.search(r" X(-?[\d.]+)", line)
            my = re.search(r" Y(-?[\d.]+)", line)
            if mx:
                x = float(mx.group(1))
            if my:
                y = float(my.group(1))
            if " E" in line and re.search(r" E(\d*\.?\d+)", line) and x is not None and y is not None:
                xs.append(x)
                ys.append(y)
        elif line.startswith("; MACHINE_END_GCODE_START") or line.startswith("; filament end gcode"):
            break
    if not xs:
        return None
    return {"xmin": round(min(xs), 1), "xmax": round(max(xs), 1), "ymin": round(min(ys), 1), "ymax": round(max(ys), 1)}


def main():
    db = json.loads((CAD / "parts.json").read_text())
    groups: dict[tuple, list] = {}
    for name, p in db.items():
        if "error" in p:
            continue
        test = p["test"]
        solid = p["infill_pct"] >= SOLID
        sup = name in SUPPORT
        printer = p["printer"]
        cls = "solid" if solid else ("draft" if name in DRAFT else "std")
        key = (printer, test, cls, sup)
        w, d = p["bed_extent_mm"][0], p["bed_extent_mm"][1]
        for i in range(p["qty"]):
            groups.setdefault(key, []).append((f"{name}__{i}", w, d))
    # merge tiny groups of the same printer/infill/support class across tests to save plates
    merged: dict[tuple, list] = {}
    for (printer, test, cls, sup), items in groups.items():
        area = sum(w * d for _, w, d in items)
        bucket = test if area > 6000 or printer == "H2D" else "misc"
        merged.setdefault((printer, bucket, cls, sup), []).extend(items)
    plan = []
    for (printer, bucket, cls, sup), items in sorted(merged.items(), key=lambda kv: (kv[0][0], str(kv[0][1]).zfill(6), kv[0][2])):
        for i, plate in enumerate(pack(items, BED[printer])):
            key = f"{printer.lower()}_{'t' + bucket.zfill(2) if bucket not in ('shared', 'misc') else bucket}_{cls}{'_sup' if sup else ''}_{i + 1}"
            plan.append((key, printer, SOLID if cls == "solid" else (15 if cls == "draft" else 25), sup, plate, cls == "draft"))
    only = set(sys.argv[1:])
    recs = []
    for key, printer, infill, sup, plate, draft in plan:
        if only and key not in only:
            continue
        stl_dir = WORK / "stl" / key
        stl_dir.mkdir(parents=True, exist_ok=True)
        # Place every object at the packer's position and merge them into one mesh, so the slicer can't
        # push anything off the bed (its own arrange did, on 5 plates, on 2026-11-28).
        import trimesh
        meshes = []
        for name, x, y, w_, d_, rot in plate:
            base = name.split("__")[0]
            m = trimesh.load(CAD / "print" / f"{base}.stl", force="mesh")
            if rot:
                m.apply_transform(trimesh.transformations.rotation_matrix(math.pi / 2, [0, 0, 1]))
            lo = m.bounds[0]
            m.apply_translation([x + MARGIN - lo[0], y + MARGIN - lo[1], -lo[2]])
            meshes.append(m)
        merged = trimesh.util.concatenate(meshes)
        if printer == "H2D":      # centre it: each H2D nozzle can't reach one edge of the bed
            lo, hi = merged.bounds
            merged.apply_translation([BED["H2D"][0] / 2 - (lo[0] + hi[0]) / 2, BED["H2D"][1] / 2 - (lo[1] + hi[1]) / 2, 0])
        dst = stl_dir / f"{key}.stl"
        merged.export(dst)
        files = [dst]
        rec = slice_plate(key, printer, infill, sup, files, draft)
        rec["packed"] = [{"name": n, "x": round(x + MARGIN, 1), "y": round(y + MARGIN, 1), "w": round(w, 1), "d": round(d, 1), "rot": r}
                         for n, x, y, w, d, r in plate]
        rec["objects"] = [n.split("__")[0] for n, *_ in plate]
        rec["n_objects"] = len(plate)
        W_, D_ = BED[printer]
        ext = gcode_extents(WORK / key / "plate_1.gcode")
        rec["extrusion_extents_mm"] = ext
        rec["merged_bbox_ok"] = bool(ext) and ext["xmin"] >= 0 and ext["ymin"] >= 0 and ext["xmax"] <= W_ and ext["ymax"] <= D_
        recs.append(rec)
        print(f"{key:34s} {len(plate):2d} obj  rc={rec['return_code']} bed_ok={rec.get('merged_bbox_ok')} time={rec.get('time')} "
              f"{rec.get('filament_g')} g  tools={rec.get('tool_changes')}  ({rec['slice_s']} s)", flush=True)
    out = HERE / "plates.json"
    old = json.loads(out.read_text()) if out.exists() and only else []
    keep = [r for r in old if r["plate"] not in {x["plate"] for x in recs}]
    out.write_text(json.dumps(keep + recs, indent=1) + "\n")


if __name__ == "__main__":
    main()
