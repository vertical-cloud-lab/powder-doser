"""Export every 3D-printed part of both carousel designs as STL, in each part's own CAD frame.

    python export_printed.py                 # both designs
    python export_printed.py paternoster     # one design

Each design's `layout.shape(key)` is the source (the same builder functions build.py uses), so this
does not run either design's build.py. Quantities come from `layout.placements()` (the same count the
BoMs use; Sam's mounting plate in chain-carousel-v2 is one fewer, module 1 exists). Writes
<design>/stl/<key>.stl and <design>/parts.json (quantity, bounding box, volume per part).
The two designs both have modules called layout/parts/params, so each runs in its own process.
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
}
QTY_ADJUST = {("chain-carousel-v2", "sam_mounting_plate"): -1}     # BoM line 39: modules 2-13 (module 1 exists)
# Print-only variants: the carriage's break-off webs under the tab-hook fingers (parts.tab_hook) are not in the assembly.
PRINT_VARIANT = {("chain-carousel-v2", "carriage"): "PT.carriage(print_web=True)"}

WORKER = r"""
import json, sys, collections
from pathlib import Path
import cadquery as cq
import layout as L
import parts as PT
out = Path(sys.argv[1]); keys = sys.argv[2].split(','); adjust = json.loads(sys.argv[3]); variant = json.loads(sys.argv[4])
(out / 'stl').mkdir(parents=True, exist_ok=True)
count = collections.Counter(p.key for p in L.placements())
info = {}
for k in keys:
    if k in variant:
        w = eval(variant[k], {'PT': PT})
        s = w.val() if len(w.vals()) == 1 else cq.Compound.makeCompound(w.vals())
    else:
        s = L.shape(k)
    cq.exporters.export(cq.Workplane('XY').add(s), str(out / 'stl' / f'{k}.stl'), tolerance=0.02, angularTolerance=0.1)
    bb = s.BoundingBox()
    info[k] = {'qty': count[k] + adjust.get(k, 0), 'source': variant.get(k, f'layout.shape({k!r})'), 'bbox_mm': [round(bb.xlen, 2), round(bb.ylen, 2), round(bb.zlen, 2)],
               'volume_mm3': round(s.Volume(), 1)}
    print(k, info[k], flush=True)
(out / 'parts.json').write_text(json.dumps(info, indent=1) + '\n')
"""


def export(design: str) -> None:
    adjust = {k: v for (d, k), v in QTY_ADJUST.items() if d == design}
    variant = {k: v for (d, k), v in PRINT_VARIANT.items() if d == design}
    subprocess.run([sys.executable, "-c", WORKER, str(HERE / design), ",".join(DESIGNS[design]), json.dumps(adjust), json.dumps(variant)],
                   cwd=CAD / design, check=True, env={**__import__("os").environ, "PYTHONPATH": str(CAD / design)})


if __name__ == "__main__":
    for d in (sys.argv[1:] or DESIGNS):
        export(d)
