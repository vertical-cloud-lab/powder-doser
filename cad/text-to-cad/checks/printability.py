"""Printability (DfAM) of every printed part, with text-to-cad's dfam-check skill.

Runs the skill's ``dfam_tool.py measure`` and ``orientations`` on each
part's STL (FDM, 45 deg self-supporting limit) and compares the facts with
the skill's FDM limits (references/process-limits.md: min supported wall
1.2 mm, unsupported 1.6 mm, min hole 2.0 mm).  The tool only measures; the
verdicts here are this script's.

    python3 checks/printability.py [--tool /path/to/dfam_tool.py] [--parts baseplate_servos_above ...]

With ``--parts`` only those parts are measured again; the other rows are
kept from the previous results.

Writes checks/results/printability.json and printability.md.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOL = Path("/tmp/text-to-cad/skills/dfam-check/scripts/dfam_tool.py")
PRINTED = ["baseplate", "baseplate_servos_above", "mounting_plate", "mounting_plate_servos_above",
           "auger", "auger_cap", "bracket", "tap_collar", "tap_collar_base",
           "stepper_pinion", "servo_pinion"]
EXTRA = {"pcb_mount": ROOT / "STL" / "electronics" / "pcb_mount.stl"}
FDM = {"wall_supported": 1.2, "wall_unsupported": 1.6, "angle": 45.0}


def printable_stl(name: str, stl: Path) -> Path:
    """The STL to measure.  A part modelled as several overlapping bodies (the
    mounting plate's gears overlap its knuckles) is fused first, as a slicer
    would merge it; otherwise the overlap reads as zero-thickness walls."""
    step = ROOT / "STEP" / "parts" / f"{name}.step"
    if not step.exists():
        return stl
    from build123d import export_stl, import_step
    shp = import_step(str(step))
    solids = shp.solids()
    if len(solids) < 2:
        return stl
    fused = solids[0].fuse(*solids[1:]).clean()
    out = ROOT / "tmp" / "printability" / f"{name}_fused.stl"
    out.parent.mkdir(parents=True, exist_ok=True)
    export_stl(fused, str(out), tolerance=0.01, angular_tolerance=0.1)
    return out


def run(tool: Path, cmd: str, stl: Path) -> dict:
    p = subprocess.run([sys.executable, str(tool), cmd, str(stl), "--angle-limit", str(FDM["angle"])],
                       capture_output=True, text=True)
    if p.returncode not in (0, 2):
        return {"error": p.stderr.strip() or p.stdout.strip()}
    return json.loads(p.stdout)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tool", type=Path, default=TOOL)
    ap.add_argument("--parts", nargs="+", default=None)
    a = ap.parse_args()
    parts = {k: ROOT / "STL" / "parts" / f"{k}.stl" for k in PRINTED}
    parts.update(EXTRA)
    out = ROOT / "checks" / "results"
    old_rows, old_raw = {}, {}
    if a.parts:
        old = json.loads((out / "printability.json").read_text())
        old_rows, old_raw = {r["part"]: r for r in old["rows"]}, old["raw"]
    rows, raw = [], {}
    for name, stl in parts.items():
        if a.parts and name not in a.parts:
            if name in old_rows:
                rows.append(old_rows[name])
                raw[name] = old_raw.get(name)
            continue
        if not stl.exists():
            continue
        stl = printable_stl(name, stl)
        m = run(a.tool, "measure", stl)
        o = run(a.tool, "orientations", stl)
        raw[name] = {"measure": m, "orientations": o}
        if "error" in m:
            rows.append({"part": name, "error": m["error"]})
            continue
        wt = m.get("wall_thickness", {})
        cands = o.get("orientations", {}).get("candidates", [])
        best = min(cands, key=lambda c: (c["support_area_mm2"], c["build_height_mm"])) if cands else {}
        rows.append({
            "part": name,
            "watertight": m["mesh"]["watertight"],
            "bodies": m["mesh"]["body_count"],
            "volume_cm3": (round(m["mesh"]["volume_mm3"] / 1000, 1)
                           if m["mesh"].get("volume_mm3") is not None else None),
            "wall_min_mm": wt.get("min_mm"), "wall_p05_mm": wt.get("p05_mm"),
            "best_orientation": best.get("orientation"),
            "support_area_mm2": best.get("support_area_mm2"),
            "support_area_pct": best.get("support_area_pct"),
            "build_height_mm": best.get("build_height_mm"),
            "thin_wall": (wt.get("p05_mm") or 99) < FDM["wall_unsupported"],
        })
        print(rows[-1], flush=True)
    out.mkdir(parents=True, exist_ok=True)
    (out / "printability.json").write_text(json.dumps({"fdm_limits": FDM, "rows": rows,
                                                       "raw": raw}, indent=1) + "\n")
    lines = ["| Part | Watertight | Bodies | Volume (cm³) | Wall min / p05 (mm) | Best orientation "
             "| Support area (mm², % of surface) | Height (mm) |", "|---|---|---|---|---|---|---|---|"]
    for r in rows:
        if "error" in r:
            lines.append(f"| {r['part']} | error: {r['error'][:60]} |||||||")
            continue
        lines.append(f"| {r['part']} | {'yes' if r['watertight'] else '**no**'} | {r['bodies']} | "
                     f"{r['volume_cm3']} | {r['wall_min_mm']} / {r['wall_p05_mm']} | "
                     f"{r['best_orientation']} | {r['support_area_mm2']} ({r['support_area_pct']} %) | "
                     f"{r['build_height_mm']} |")
    (out / "printability.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
