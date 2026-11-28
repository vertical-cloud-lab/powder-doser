"""Write README.md (parts table) and ../ASSEMBLY.md (step lists) from parts.py, assemblies.py and out/parts.json.

    python make_docs.py
"""
from __future__ import annotations

import json
from pathlib import Path

import assemblies as A
from parts import PARTS

HERE = Path(__file__).resolve().parent
DB = json.loads((HERE / "out" / "parts.json").read_text())
TESTS = {"shared": "Shared bench parts", "1": "1. Heap angle of repose", "2": "2. Bulk and tapped density",
         "3": "3. Tilting plate", "4": "4. PSD and shape from images", "5": "5. Orifice cup", "6": "6. Humidity chambers",
         "7": "7. Rotating drum", "8": "8. Unconfined strength", "9": "9. Blade spreading", "10": "10. Faraday cup"}

FITS = [
    ("Ø6 steel guide rods in the tapper base", "Ø6.00 hole, 15 deep", "press fit; printed holes come out about 0.1 mm small"),
    ("Ø6 rods through the tapper carriage", "Ø6.50 bores", "slide fit; wrap the rods in PTFE tape, or ream to 6.2"),
    ("Ø5 hinge pin (tilt table)", "Ø5.20 in the towers, Ø5.10 in the plate lugs", "pin turns in the towers"),
    ("Ø8 shafts in the DIY stage blocks", "Ø8.06, 14 deep", "press fit"),
    ("LM8UU bearings in the stage carriage", "Ø15.10 x 32", "press fit, two per side"),
    ("608 bearing (stage end block)", "Ø22.10 x 7.2", "press fit"),
    ("NEMA 17 pilot / NEMA 11 pilot", "Ø22.6 / Ø22.5", "clearance"),
    ("M3 heat-set inserts (drum shaft flange, drum, stage carriage)", "Ø4.2", "for standard M3 x 4 inserts"),
    ("M3 clearance", "Ø3.2-3.4", ""),
    ("M2.5 self-tapping (IMU, NEMA 11 face)", "Ø2.2-2.7", ""),
    ("Spigot / socket (risers, pedestals)", "Ø9.90 spigot into Ø10.25 socket", "slip fit, no glue: pedestals swap"),
    ("Locating pins on the tripod spider", "Ø3.0 pins, Ø3.5 blind holes", "trays, cradles and the cup holder drop on"),
    ("Coupon pockets", "0.71 deep (tilt plate), 0.91 deep (spreading bed)", "0.91 mm 304 coupons: 0.2 proud / flush"),
    ("Orifice discs", "printed 0.2 mm under size", "drill or ream to 1.0-6.0 mm; check with pin gauges"),
]


def parts_readme():
    lines = ["# Printed parts (CadQuery)", "",
             "**Status: designed and sliced, not printed.** Each part is a function in [`parts.py`](parts.py). "
             "[`build.py`](build.py) writes a STEP and an STL in the use frame, an STL turned onto the bed, and "
             "[`out/parts.json`](out/parts.json) (volume, mass when solid, bounding box, bed footprint, watertightness, "
             "printer fit). [`assemblies.py`](assemblies.py) places the parts with stand-ins for bought parts and renders "
             "each apparatus ([`out/renders/`](out/renders)). Numbers come from [`../SPEC.md`](../SPEC.md).", "",
             "```bash", "python build.py              # all parts (about 3 min)", "xvfb-run -a python assemblies.py   # renders",
             "python make_docs.py         # this README and ../ASSEMBLY.md", "```", "",
             "Slicing is in [`../print/`](../print). Mass below is for a solid part; printed mass is lower (see the plates).", ""]
    for t, title in TESTS.items():
        names = [n for n, p in PARTS.items() if p.test == t]
        if not names:
            continue
        lines += [f"## {title}", "", "| Part | Qty | Printer | Infill | Solid mass (g) | Size in use (mm) | STEP / STL | Note |",
                  "|---|---|---|---|---|---|---|---|"]
        for n in names:
            r = DB.get(n, {})
            if "error" in r or not r:
                continue
            bb = " x ".join(f"{x:.0f}" for x in r["bbox_use_mm"])
            lines.append(f"| `{n}` | {r['qty']} | {r['printer']} | {r['infill_pct']} % | {r['mass_g_solid']} | {bb} | "
                         f"[STEP](out/step/{n}.step) · [STL](out/stl/{n}.stl) · [bed](out/print/{n}.stl) | {r['note']} |")
        lines.append("")
    lines += ["## Fits and hardware holes", "", "| Interface | Printed size | Fit |", "|---|---|---|"]
    lines += [f"| {a} | {b} | {c} |" for a, b, c in FITS]
    lines += ["", "Printed holes shrink by about 0.1-0.2 mm on an A1 mini. Print one `wall_ring` and one "
              "`tapper_cam` first and check the fits before committing to a full plate.", ""]
    (HERE / "README.md").write_text("\n".join(lines))


def assembly_md():
    lines = ["# Assembly, step by step", "",
             "**Status: designed, not built.** These are the steps the assembly videos animate; the renders are from "
             "[`cad/assemblies.py`](cad/assemblies.py). Teal parts are printed (see [`cad/`](cad)), purple ones are "
             "bought (see [`bom/`](bom)), grey is the existing doser and balance. The SOPs that use each apparatus are "
             "in [`software/sop/`](software/sop).", ""]
    for key, fn in A.ASSEMBLIES.items():
        a = fn()
        lines += [f"## {a['title']}", "", f"![{a['title']}](cad/out/renders/{key}.png)", ""]
        for i, s in enumerate(a["steps"]):
            comps = [c.label for c in a["comps"] if c.step == i and c.kind != "context"]
            extra = f" *({'; '.join(comps)})*" if comps else ""
            lines.append(f"{i + 1}. {s}{extra}")
        lines.append("")
    (HERE.parent / "ASSEMBLY.md").write_text("\n".join(lines))


if __name__ == "__main__":
    parts_readme()
    assembly_md()
    print("ok")
