"""Slice every 3D-printed part of both carousel designs with the Bambu Studio CLI, in PETG.

    python export_printed.py                                  # STLs of the printed parts, from the CAD
    python slice.py --bambu /tmp/bambu/squashfs-root          # all plates of both designs
    python slice.py --bambu ... --design paternoster --parts  # also slice each part alone (audit)
    python previews.py                                        # toolpath previews and plates.png

Bambu Studio's own Linux AppImage (v02.08.02.61, `--appimage-extract`), no login. Presets are Bambu's
system presets, flattened by flatten_bambu_profiles.py (this repo's script, from the
copilot/programmatic-access-bambu-h2d branch):

* H2D: "Bambu Lab H2D 0.4 nozzle", "0.20mm Standard @BBL H2D", "Bambu PETG Basic @BBL H2D 0.4 nozzle",
  loaded once per tool with `--filament-map-mode Manual --filament-map 1,2 --slice 1` (the H2D recipe
  from a1_mini_slice_and_send.py). Every part is on filament 1, the left nozzle, whose printable area
  is x 0-325, y 0-320 (the right nozzle's is x 25-350), so plates are laid out in 325 x 320.
* A1 mini: "Bambu Lab A1 mini 0.4 nozzle", "0.20mm Standard @BBL A1M", "Bambu PETG Basic @BBL A1M 0.4 nozzle",
  180 x 180 bed.

On top of the stock process: 3 walls and 25 % sparse infill (functional parts, as byu-vcl's slices),
Textured PEI plate (65-70 C for PETG), supports off unless a plate's SUPPORT entry turns them on.
Each part is turned into its print orientation (ORIENT, with the reason), and each plate is
sliced in its own run, so every plate gets its own .gcode.3mf. Writes, per design,
<design>/plates/<plate>.gcode.3mf (when < 20 MB), <design>/plates/<plate>.png (Studio's own plate
render, when an OpenGL context is available), <design>/slice_report.json and <design>/audit.json.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import re
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

import numpy as np
import trimesh

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import audit as A  # noqa: E402
import flatten_bambu_profiles as F  # noqa: E402

PRINTERS = {
    "h2d": {"label": "Bambu Lab H2D (left nozzle)", "bed": (325.0, 320.0), "height": 320.0, "idex": True,
            "machine": "Bambu Lab H2D 0.4 nozzle", "process": "0.20mm Standard @BBL H2D",
            "filament": "Bambu PETG Basic @BBL H2D 0.4 nozzle"},
    "a1m": {"label": "Bambu Lab A1 mini", "bed": (180.0, 180.0), "height": 180.0, "idex": False,
            "machine": "Bambu Lab A1 mini 0.4 nozzle", "process": "0.20mm Standard @BBL A1M",
            "filament": "Bambu PETG Basic @BBL A1M 0.4 nozzle"},
}
PROCESS = {"wall_loops": "3", "sparse_infill_density": "25%", "enable_support": "0"}
SUPPORT = {"enable_support": "1", "support_type": "tree(auto)", "support_on_build_plate_only": "1"}
BRIM = {"brim_type": "outer_only", "brim_width": "3"}   # station plates: yoke stops (24 mm2), pin plates, funnel rim; Studio's auto brim adds none
BED_TYPE = "Textured PEI Plate"
FILAMENT_COLOUR = "#F28C28"
GAP = 8.0                     # mm between parts on a plate
MAX_3MF = 20e6

# Print orientation per part: rotations about the part's own axes (applied in order), and why.
X, Y, Z = "x", "y", "z"
ORIENT = {
    "gondola": ([], "as it hangs: end plates, rails, ribs, lugs and saddle all stand on the bed; pivot and insert holes horizontal (small)"),
    "carriage": ([(X, 90)], "plate's outer face on the bed, ribs, lugs, hooks and snap arms up; on the H2D bed's diagonal (351 mm > 325)"),
    "uyoke_base": ([(X, 180)], "crossbar's top face on the bed, guide tongue up: socket opens upward, no support in it"),
    "yoke_stop": ([(X, 90)], "flat, 6 x 4 mm on the bed, 1.3 mm tall"),
    "yoke_stop_m": ([(X, 90)], "flat, 6 x 4 mm on the bed, 1.3 mm tall"),
    "pin_boss": ([(X, 90)], "flat: the 1.5 mm plate on the bed, pin hole vertical"),
    "pin_boss_m": ([(X, 90)], "flat: the 1.5 mm plate on the bed, pin hole vertical"),
    "magnet_bracket": ([], "as drawn: foot, arms and cup floor on the bed, magnet pocket opens upward"),
    "fork": ([], "as drawn: slot and lead-in vertical, no overhangs"),
    "fork_arm": ([(X, 90)], "flat, largest face on the bed"),
    "clevis_bracket": ([], "foot on the bed, cheeks up; pin hole horizontal (5 mm, prints without support)"),
    "vial_cup": ([], "as drawn: cup floor and arm on the bed"),
    "vial_funnel": ([(X, 180)], "mouth on the bed: cone narrows upward (24 deg from vertical), largest first layer"),
    "hold_bracket": ([], "as drawn, 28 x 12 on the bed"),
    "hold_down": ([], "side-plate face on the bed: foot, web and lip stack without overhang; insert holes vertical"),
    "tensioner_block": ([], "back face on the bed: screw holes and nut slot vertical, jack-screw hole horizontal"),
    "level_wedge": ([], "flat"),
    "sam_mounting_plate": ([], "as drawn (Sam's part): base on the bed"),
}

# Where a design's part differs from its namesake in the other design
ORIENT_DESIGN = {
    ("chain-carousel-v2", "fork_arm"): ([], "the 6 mm plate flat on the bed, M6 clearance and insert holes vertical"),
}


def orient(design: str, key: str):
    return ORIENT_DESIGN.get((design, key), ORIENT[key])


# Plates: (name, printer, [(part, count)], support?).  Filled per design by plates().
QTY_NOTE = "quantities from layout.placements() (the BoM's counts)"


def plates(design: str, qty: dict) -> list[dict]:
    station_common = ["uyoke_base", "yoke_stop", "yoke_stop_m", "pin_boss", "pin_boss_m", "magnet_bracket", "fork",
                      "fork_arm", "clevis_bracket", "vial_cup", "vial_funnel"]
    out = []
    if design == "paternoster":
        n = qty["gondola"]
        per = 4
        for i in range(math.ceil(n / per)):
            out.append({"name": f"gondolas_{i + 1}", "printer": "h2d", "parts": [("gondola", min(per, n - i * per))]})
        out.append({"name": "station", "printer": "a1m", "brim": True,
                    "parts": [(k, qty[k]) for k in station_common + ["hold_bracket"]]})
        m = qty["sam_mounting_plate"]
        per = 6
        for i in range(math.ceil(m / per)):
            out.append({"name": f"mounting_plates_{i + 1}", "printer": "h2d", "parts": [("sam_mounting_plate", min(per, m - i * per))]})
    else:
        for i in range(qty["carriage"]):
            out.append({"name": f"carriage_{i + 1:02d}", "printer": "h2d", "parts": [("carriage", 1)], "diagonal": True})
        out.append({"name": "station", "printer": "a1m", "brim": True, "parts": [(k, qty[k]) for k in station_common + ["level_wedge"]]})
        out.append({"name": "hold_downs_tensioners", "printer": "a1m", "parts": [("hold_down", qty["hold_down"]),
                                                                                 ("tensioner_block", qty["tensioner_block"])]})
        m = qty["sam_mounting_plate"]
        per = 6
        for i in range(math.ceil(m / per)):
            out.append({"name": f"mounting_plates_{i + 1}", "printer": "h2d", "parts": [("sam_mounting_plate", min(per, m - i * per))]})
    return out


# ---------------------------------------------------------------- presets
def write_presets(bambu: Path, build: Path) -> dict[str, dict[str, Path]]:
    by_name = F.index_presets(str(bambu / "resources" / "profiles"))
    out = {}
    for key, pr in PRINTERS.items():
        d = {}
        for role in ("machine", "process", "filament"):
            path = build / f"{key}_{role}.json"
            F.write_flat(role, pr[role], by_name, str(path), machine_name=pr["machine"])
            cfg = json.loads(path.read_text())
            if role == "filament":
                cfg["filament_colour"] = [FILAMENT_COLOUR]
            if role == "process":
                cfg.update(PROCESS)
            path.write_text(json.dumps(cfg, indent=1))
            d[role] = path
        for tag, extra in (("support", SUPPORT), ("brim", BRIM)):
            cfg = json.loads(d["process"].read_text())
            cfg.update(extra)
            d[f"process_{tag}"] = build / f"{key}_process_{tag}.json"
            d[f"process_{tag}"].write_text(json.dumps(cfg, indent=1))
        out[key] = d
    return out


# ---------------------------------------------------------------- orientation and layout
def oriented(design: str, key: str, diagonal: bool = False) -> trimesh.Trimesh:
    mesh = trimesh.load(HERE / design / "stl" / f"{key}.stl")
    m = A.place(mesh, orient(design, key)[0])
    if diagonal:
        m = diag(m)
    return m


def diag(m: trimesh.Trimesh) -> trimesh.Trimesh:
    """Turn a long part about z so its footprint lies on the bed's diagonal (325 x 320)."""
    m = m.copy()
    ang = math.atan2(PRINTERS["h2d"]["bed"][1], PRINTERS["h2d"]["bed"][0])
    if m.extents[1] > m.extents[0]:
        m.apply_transform(trimesh.transformations.rotation_matrix(-math.pi / 2, [0, 0, 1]))
    m.apply_transform(trimesh.transformations.rotation_matrix(ang, [0, 0, 1]))
    lo, hi = m.bounds
    m.apply_translation([-(lo[0] + hi[0]) / 2, -(lo[1] + hi[1]) / 2, -lo[2]])
    return m


def layout(items: list[tuple[str, trimesh.Trimesh]], bed: tuple[float, float]) -> list[tuple[str, float, float]]:
    """Shelf packing, biggest first, rows along x; the block is then centred on the bed.
    Returns (key, x, y) of each part's bbox centre."""
    order = sorted(range(len(items)), key=lambda i: -items[i][1].extents[1] * 1000 - items[i][1].extents[0])
    rows, cur, x, y, row_h = [], [], 0.0, 0.0, 0.0
    for i in order:
        w, h = items[i][1].extents[:2]
        if cur and x + w > bed[0] - 2 * GAP:
            rows.append((cur, y, row_h))
            y += row_h + GAP
            cur, x, row_h = [], 0.0, 0.0
        cur.append((i, x + w / 2))
        x += w + GAP
        row_h = max(row_h, h)
    rows.append((cur, y, row_h))
    total_h = y + row_h
    pos = [None] * len(items)
    for cur, y0, rh in rows:
        row_w = max(xc for _, xc in cur) + items[cur[-1][0]][1].extents[0] / 2
        for i, xc in cur:
            pos[i] = (items[i][0], bed[0] / 2 - row_w / 2 + xc, bed[1] / 2 - total_h / 2 + y0 + rh / 2)
    if total_h > bed[1] - 2 or any(abs(p[1] - bed[0] / 2) + items[i][1].extents[0] / 2 > bed[0] / 2 for i, p in enumerate(pos)):
        raise SystemExit(f"plate does not fit: {[k for k, _ in items]} on {bed}")
    return pos


# ---------------------------------------------------------------- Studio CLI
OSMESA = Path("/usr/lib/x86_64-linux-gnu/libOSMesa.so.8")
GL_PRELOAD: str | None = None


def gl_setup(build: Path) -> None:
    """Studio's CLI renders thumbnails and --export-png through GLFW on a Wayland display with an OSMesa context,
    and its GLX-built GLEW then refuses to start; glxshim.c fakes the few GLX calls GLEW makes (byu-vcl's recipe).
    Needs WAYLAND_DISPLAY (a headless Weston is enough, see README) and libOSMesa; without them, no PNGs."""
    global GL_PRELOAD
    if not (os.environ.get("WAYLAND_DISPLAY") and OSMESA.exists() and shutil.which("gcc")):
        print("no Wayland display or libOSMesa: slicing without Studio's plate pictures")
        return
    shim = build / "libglxshim.so"
    subprocess.run(["gcc", "-shared", "-fPIC", "-O2", "-o", str(shim), str(HERE / "glxshim.c"), f"-l:{OSMESA.name}", "-ldl"], check=True)
    GL_PRELOAD = f"{shim}:{OSMESA}"


def gl_env() -> dict:
    env = dict(os.environ)
    if GL_PRELOAD:
        env["LD_PRELOAD"] = GL_PRELOAD
    return env


def export_png(bambu: Path, f3: Path, out: Path) -> Path | None:
    """Studio's own iso picture of the plate (--export-png, camera view 0)."""
    if not GL_PRELOAD:
        return None
    d = out / "png"
    shutil.rmtree(d, ignore_errors=True)
    d.mkdir()
    subprocess.run(["nice", "-n", "10", str(bambu / "AppRun"), "--export-png", "0", "--camera-view", "0", "--outputdir", str(d), str(f3)],
                   capture_output=True, env=gl_env(), timeout=600)
    pngs = sorted(d.glob("*.png"))
    return pngs[0] if pngs else None

def run_cli(bambu: Path, printer: str, presets: dict, assemble: Path, out: Path, name: str, variant: str) -> tuple[int, str]:
    pr = PRINTERS[printer]
    p = presets[printer]
    cmd = ["xvfb-run", "-a", "-s", "-screen 0 1280x1024x24", str(bambu / "AppRun"), "--debug", "2",
           "--load-settings", f"{p['machine']};{p['process_' + variant] if variant else p['process']}"]
    if pr["idex"]:
        cmd += ["--load-filaments", f"{p['filament']};{p['filament']}", "--filament-map-mode", "Manual", "--filament-map", "1,2"]
    else:
        cmd += ["--load-filaments", str(p["filament"])]
    cmd += ["--load-assemble-list", str(assemble), "--curr-bed-type", BED_TYPE,
            "--slice", "1" if pr["idex"] else "0", "--outputdir", str(out), "--export-3mf", f"{name}.gcode.3mf"]
    proc = subprocess.run(["nice", "-n", "10"] + cmd, capture_output=True, text=True, env=gl_env(), timeout=1800)
    log = proc.stdout + proc.stderr
    (out / f"{name}.cli.log").write_text(log)
    return proc.returncode, log


def parse(out: Path, name: str, log: str) -> dict:
    res = json.loads((out / "result.json").read_text())
    shutil.copy(out / "result.json", out / f"{name}.result.json")
    r = {"return_code": res.get("return_code"), "error": res.get("error_string")}
    f3 = out / f"{name}.gcode.3mf"
    if res.get("return_code") != 0 or not f3.exists():
        return r
    with zipfile.ZipFile(f3) as z:
        info = ET.fromstring(z.read("Metadata/slice_info.config"))
        gname = next(n for n in z.namelist() if re.match(r"Metadata/plate_\d+\.gcode$", n))
        head = z.read(gname)[:6000].decode(errors="replace")
        pngs = [n for n in z.namelist() if n.endswith(".png")]
    pl = info.find("plate")
    meta = {m.get("key"): m.get("value") for m in pl.findall("metadata")}
    fil = pl.find("filament")
    layers = re.search(r"; total layer number: (\d+)", head)
    tot = re.search(r"total estimated time: ([^\n]+)", head)
    sp = res["sliced_plates"][0]
    r.update({
        "print_time_s": int(meta.get("prediction", 0)), "print_time": tot.group(1).strip() if tot else None,
        "filament_g": float(fil.get("used_g")) if fil is not None else None,
        "filament_m": float(fil.get("used_m")) if fil is not None else None,
        "layers": int(layers.group(1)) if layers else None,
        "max_z_mm": float(re.search(r"; max_z_height: ([\d.]+)", head).group(1)) if "max_z_height" in head else None,
        "toolpath_outside_bed": meta.get("outside") == "true", "support_used": meta.get("support_used") == "true",
        "slicer_warnings": sorted(set(re.findall(r"found (?:NON_CRITICAL )?slicing warnings: (.*)", log))),
        "gcode_warnings": [{"msg": w.get("msg"), "level": w.get("level"), "code": w.get("error_code")} for w in pl.findall("warning")],
        "feature_time_s": {k: round(v) for k, v in sorted(sp.get("feature_type_times", {}).items())},
        "pngs_in_3mf": pngs,
    })
    return r


def slice_plate(bambu: Path, presets: dict, design: str, plate: dict, build: Path, dest: Path) -> dict:
    name = plate["name"]
    out = build / name
    shutil.rmtree(out, ignore_errors=True)
    out.mkdir(parents=True)
    pr = PRINTERS[plate["printer"]]
    items, files = [], {}
    for key, n in plate["parts"]:
        m = oriented(design, key, plate.get("diagonal", False))
        if m.extents[2] > pr["height"]:
            raise SystemExit(f"{key} is {m.extents[2]:.0f} mm tall")
        files[key] = out / f"{key}.stl"
        m.export(files[key])
        items += [(key, m)] * n
    pos = layout(items, pr["bed"])
    # one entry per copy: with "count" > 1 the H2D run put the copies off the bed ("partly inside", -52)
    objs = [{"path": str(files[key]), "count": 1, "filaments": [1], "pos_x": [round(x, 2)], "pos_y": [round(y, 2)], "pos_z": [0]}
            for key, x, y in pos]
    assemble = out / "assemble.json"
    assemble.write_text(json.dumps({"plates": [{"plate_name": name, "need_arrange": False, "objects": objs}]}, indent=1))
    variant = "support" if plate.get("support") else ("brim" if plate.get("brim") else "")
    code, log = run_cli(bambu, plate["printer"], presets, assemble, out, name, variant)
    r = {"plate": name, "printer": pr["label"], "printer_key": plate["printer"], "bed_mm": list(pr["bed"]),
         "parts": {k: n for k, n in plate["parts"]}, "support": plate.get("support", False), "brim_mm": float(BRIM["brim_width"]) if variant == "brim" else 0.0,
         "positions": [[k, round(x, 1), round(y, 1)] for k, x, y in pos], "cli_exit": code}
    r.update(parse(out, name, log))
    f3 = out / f"{name}.gcode.3mf"
    dest.mkdir(parents=True, exist_ok=True)
    if f3.exists():
        if f3.stat().st_size < MAX_3MF:
            shutil.copy(f3, dest / f3.name)
            r["gcode_3mf"] = f"plates/{f3.name}"
        else:
            r["gcode_3mf"] = None
            r["gcode_3mf_note"] = f"{f3.stat().st_size / 1e6:.0f} MB, not kept (> 20 MB); re-run slice.py"
        r["gcode_3mf_mb"] = round(f3.stat().st_size / 1e6, 2)
        png = export_png(bambu, f3, out)
        if png:
            shutil.copy(png, dest / f"{name}.png")
            r["studio_png"] = f"plates/{name}.png"
    print(f"  {design}/{name}: exit {code}, {r.get('print_time')}, {r.get('filament_g')} g, warnings {r.get('slicer_warnings')}", flush=True)
    return r


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--bambu", type=Path, default=Path("/tmp/bambu/squashfs-root"))
    ap.add_argument("--build", type=Path, default=Path("/tmp/slicebuild"))
    ap.add_argument("--design", choices=["paternoster", "chain-carousel-v2"], action="append")
    ap.add_argument("--parts", action="store_true", help="also slice every part alone, supports off (per-part audit)")
    ap.add_argument("--only", nargs="*", help="slice only these plates")
    args = ap.parse_args()
    args.build.mkdir(parents=True, exist_ok=True)
    presets = write_presets(args.bambu, args.build)
    gl_setup(args.build)
    version = re.search(r"BambuStudio_\S*?-v([\d.]+)", " ".join(os.listdir(args.bambu.parent))) if args.bambu.parent.exists() else None
    for design in args.design or ["paternoster", "chain-carousel-v2"]:
        info = json.loads((HERE / design / "parts.json").read_text())
        qty = {k: v["qty"] for k, v in info.items()}
        dest = HERE / design / "plates"
        rep_path = HERE / design / "slice_report.json"
        old = json.loads(rep_path.read_text()) if rep_path.exists() else {}
        if args.parts:
            audit = {}
            for k in info:
                mesh = trimesh.load(HERE / design / "stl" / f"{k}.stl")
                a = A.audit(mesh, orient(design, k)[0])
                p = {"name": f"part_{k}", "printer": "h2d" if max(A.place(mesh, orient(design, k)[0]).extents[:2]) > 170 else "a1m",
                     "parts": [(k, 1)], "diagonal": k == "carriage"}
                s = slice_plate(args.bambu, presets, design, p, args.build / design / "parts", args.build / design / "parts_out")
                audit[k] = {"qty": qty[k], "orientation": orient(design, k)[0], "why": orient(design, k)[1], "mesh": a,
                            "studio_supports_off": {kk: s.get(kk) for kk in ("print_time", "print_time_s", "filament_g", "layers",
                                                                             "slicer_warnings", "gcode_warnings", "return_code", "error")}}
            (HERE / design / "audit.json").write_text(json.dumps(audit, indent=1) + "\n")
        reps = {p["plate"]: p for p in old.get("plates", [])}
        for p in plates(design, qty):
            if args.only and p["name"] not in args.only:
                continue
            reps[p["name"]] = slice_plate(args.bambu, presets, design, p, args.build / design, dest)
        order = [p["name"] for p in plates(design, qty)]
        pl = [reps[n] for n in order if n in reps]
        rep = {"design": design, "bambu_studio": "02.08.02.61", "bed_type": BED_TYPE,
               "presets": {k: {r: PRINTERS[k][r] for r in ("machine", "process", "filament")} for k in PRINTERS},
               "process_overrides": PROCESS, "support_settings_when_on": SUPPORT, "brim_settings_when_on": BRIM, "quantities": qty, "quantities_note": QTY_NOTE,
               "plates": pl,
               "total_print_time_h": round(sum(p.get("print_time_s", 0) for p in pl) / 3600, 1),
               "total_filament_g": round(sum(p.get("filament_g") or 0 for p in pl), 1)}
        rep_path.write_text(json.dumps(rep, indent=1) + "\n")
        print(f"{design}: {len(pl)} plates, {rep['total_print_time_h']} h, {rep['total_filament_g']} g")


if __name__ == "__main__":
    main()
