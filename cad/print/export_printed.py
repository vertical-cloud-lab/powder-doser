"""Export every 3D-printed part of the carousel designs as STL, in each part's own CAD frame.

    python export_printed.py                       # every design
    python export_printed.py paternoster           # one design
    python export_printed.py chain-carousel-v11    # v11 (PR #185): carriage, plate, T, door, latch carrier, EC, station, enclosure

Each design's `layout.shape(key)` is the source (the same builder functions build.py uses), so this
does not run either design's build.py. Quantities come from `layout.placements()` (the same count the
BoMs use; Sam's mounting plate in chain-carousel-v2 is one fewer, module 1 exists; v11 prints all 13). Writes
<design>/stl/<key>.stl and <design>/parts.json (quantity, bounding box, volume per part).
The designs all have modules called layout/parts/params, so each runs in its own process.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
CAD = HERE.parent
DESIGNS = {
    "paternoster": ["gondola", "uyoke_base", "yoke_stop", "yoke_stop_m", "pin_boss", "pin_boss_m", "magnet_bracket", "fork",
                    "fork_arm", "clevis_bracket", "vial_cup", "vial_funnel", "hold_bracket", "sam_mounting_plate"],
    "chain-carousel-v2": ["carriage", "hold_down", "tensioner_block", "uyoke_base", "magnet_bracket", "clevis_bracket", "fork",
                          "fork_arm", "vial_cup", "vial_funnel", "level_wedge", "pin_boss", "pin_boss_m", "yoke_stop",
                          "yoke_stop_m", "sam_mounting_plate"],
    # v11 (cad/chain-carousel-v11/bom.py, the "Printed" lines; its own stl/ has the same parts, some turned for printing)
    "chain-carousel-v11": ["carriage", "sam_mounting_plate", "t_bracket", "door_housing", "door_shutter", "door_head11", "latch_bolt",
                           "ec11", "pillar11", "p16_bracket11", "guide11", "latch_rail11", "hold_down", "tensioner_block", "side_tab",
                           "side_tab_m", "catch", "hatch_knob"],
}
QTY_ADJUST = {("chain-carousel-v2", "sam_mounting_plate"): -1}     # BoM line 39: modules 2-13 (module 1 exists)
# Print-only variants: the carriage's break-off webs under the tab-hook fingers (parts.tab_hook) are not in the assembly.
# v11's are in chain-carousel-v11/print_variants.py (V): the carriage with its webs, the latch bolt's printed carrier without the steel
# dowel (as v11's build.py now exports it), and the side hatch's knob (cut off the acrylic door it is bonded to).
PRINT_VARIANT = {("chain-carousel-v2", "carriage"): "PT.carriage(print_web=True)",
                 ("chain-carousel-v11", "carriage"): "V.carriage()",
                 ("chain-carousel-v11", "latch_bolt"): "V.latch_bolt()",
                 ("chain-carousel-v11", "hatch_knob"): "V.hatch_knob()"}
COUNT_AS = {("chain-carousel-v11", "hatch_knob"): "hatch_side"}     # one knob per side-hatch door

WORKER = r"""
import json, sys, collections
from pathlib import Path
import cadquery as cq
import layout as L
import parts as PT
out = Path(sys.argv[1]); keys = sys.argv[2].split(','); adjust = json.loads(sys.argv[3]); variant = json.loads(sys.argv[4])
count_as = json.loads(sys.argv[5]) if len(sys.argv) > 5 else {}
sys.path.insert(0, str(out))
V = __import__('print_variants') if (out / 'print_variants.py').exists() else None
(out / 'stl').mkdir(parents=True, exist_ok=True)
count = collections.Counter(p.key for p in L.placements())
info = {}
for k in keys:
    if k in variant:
        w = eval(variant[k], {'PT': PT, 'L': L, 'V': V})
        s = w if isinstance(w, cq.Shape) else (w.val() if len(w.vals()) == 1 else cq.Compound.makeCompound(w.vals()))
    else:
        s = L.shape(k)
    cq.exporters.export(cq.Workplane('XY').add(s), str(out / 'stl' / f'{k}.stl'), tolerance=0.02, angularTolerance=0.1)
    bb = s.BoundingBox()
    info[k] = {'qty': count[count_as.get(k, k)] + adjust.get(k, 0), 'source': variant.get(k, f'layout.shape({k!r})'), 'bbox_mm': [round(bb.xlen, 2), round(bb.ylen, 2), round(bb.zlen, 2)],
               'volume_mm3': round(s.Volume(), 1)}
    print(k, info[k], flush=True)
(out / 'parts.json').write_text(json.dumps(info, indent=1) + '\n')
"""


def export(design: str) -> None:
    adjust = {k: v for (d, k), v in QTY_ADJUST.items() if d == design}
    variant = {k: v for (d, k), v in PRINT_VARIANT.items() if d == design}
    count_as = {k: v for (d, k), v in COUNT_AS.items() if d == design}
    subprocess.run([sys.executable, "-c", WORKER, str(HERE / design), ",".join(DESIGNS[design]), json.dumps(adjust), json.dumps(variant),
                    json.dumps(count_as)],
                   cwd=CAD / design, check=True, env={**__import__("os").environ, "PYTHONPATH": str(CAD / design)})


if __name__ == "__main__":
    for d in (sys.argv[1:] or DESIGNS):
        export(d)
