"""Summarise the sliced plates: tables for README.md and a contact sheet of every plate (plates.png).

    xvfb-run -a python report.py
"""
from __future__ import annotations

import json
import math
import re
from pathlib import Path

import numpy as np
import pyvista as pv
import trimesh

HERE = Path(__file__).resolve().parent
CAD = HERE.parent / "cad" / "out"
pv.OFF_SCREEN = True


def secs(s):
    return sum(int(v) * {"d": 86400, "h": 3600, "m": 60, "s": 1}[u] for v, u in re.findall(r"(\d+)([dhms])", s or ""))


def hm(t):
    return f"{int(t // 3600)} h {int(t % 3600 // 60):02d} min"


def main():
    plates = json.loads((HERE / "plates.json").read_text())
    parts = json.loads((CAD / "parts.json").read_text())
    rows = []
    for p in plates:
        objs = {}
        for o in p["objects"]:
            objs[o] = objs.get(o, 0) + 1
        rows.append((p["plate"], p["printer"], "0.24 Draft" if p.get("draft_0p24") else "0.20 Standard", p["infill_pct"],
                     "tree" if p["supports"] else "none", p.get("time"), p.get("filament_g"),
                     ", ".join(f"{k} x{v}" if v > 1 else k for k, v in objs.items()), p["return_code"]))
    tot_t = sum(secs(r[5]) for r in rows)
    tot_g = sum(r[6] or 0 for r in rows)
    a1 = [r for r in rows if r[1] == "A1M"]
    h2 = [r for r in rows if r[1] == "H2D"]
    lines = ["| Plate | Printer | Layers | Infill | Supports | Time | PLA (g) | Parts |", "|---|---|---|---|---|---|---|---|"]
    for r in rows:
        lines.append(f"| [`{r[0]}`](plates/{r[0]}.gcode.3mf) | {r[1]} | {r[2]} | {r[3]} % | {r[4]} | {r[5]} | {r[6]} | {r[7]} |")
    by_test = {}
    for name, p in parts.items():
        if "error" in p:
            continue
        by_test.setdefault(p["test"], []).append(name)
    summary = {
        "plates": len(rows), "a1m_plates": len(a1), "h2d_plates": len(h2),
        "total_time_h": round(tot_t / 3600, 1), "a1m_time_h": round(sum(secs(r[5]) for r in a1) / 3600, 1),
        "h2d_time_h": round(sum(secs(r[5]) for r in h2) / 3600, 1), "pla_g": round(tot_g),
        "all_return_code_0": all(r[8] == 0 for r in rows),
        "all_on_bed": all(p.get("merged_bbox_ok") for p in plates),
        "unique_parts": len([n for n in parts if "error" not in parts[n]]),
        "printed_items": sum(parts[n]["qty"] for n in parts if "error" not in parts[n]),
    }
    (HERE / "summary.json").write_text(json.dumps(summary, indent=1) + "\n")
    (HERE / "plates_table.md").write_text("\n".join(lines) + "\n")
    print(json.dumps(summary, indent=1))
    # contact sheet: parts laid out as the slicer arranged them
    n = len(plates)
    cols = 6
    rows_ = math.ceil(n / cols)
    pl = pv.Plotter(shape=(rows_, cols), window_size=(cols * 300, rows_ * 300), off_screen=True)
    for k, p in enumerate(plates):
        pl.subplot(k // cols, k % cols)
        bed = (180, 180) if p["printer"] == "A1M" else (350, 320)
        pl.add_mesh(pv.Box((0, bed[0], 0, bed[1], -1, 0)), color="#d8d8d8")
        for o in p.get("packed", []):
            base = o["name"].split("__")[0]
            f = CAD / "print" / f"{base}.stl"
            if not f.exists():
                continue
            m = trimesh.load(f, force="mesh")
            if o["rot"]:
                m.apply_transform(trimesh.transformations.rotation_matrix(math.pi / 2, [0, 0, 1]))
            lo = m.bounds[0]
            m.apply_translation([o["x"] - lo[0], o["y"] - lo[1], -lo[2]])
            pl.add_mesh(pv.wrap(m), color="#2a9d8f" if not p["supports"] else "#e76f51")
        pl.add_text(f"{p['plate']}\n{p.get('time')}, {p.get('filament_g')} g", font_size=8)
        pl.view_isometric()
        pl.camera.zoom(1.25)
        pl.set_background("white")
    pl.screenshot(str(HERE / "plates.png"))


if __name__ == "__main__":
    main()
