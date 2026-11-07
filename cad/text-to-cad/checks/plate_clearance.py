"""Does the lowered servos-above doser clear its baseplate and the board?

frames.DROP lowers everything but the baseplate's plate by 5 mm, so the
only pairs that change are the moving parts and their screws against the
baseplate and the board; every other pair moves rigidly together and is
covered by interference.py.  The mounting plate's floor swings back as it
rises and clears the plate top only at about 4.5 deg, inside the default
sweep's first 15 deg step, so this sweeps 0-10 deg in 0.5 deg steps and
then on to 45.  It also reports the rest-position gaps of the lowest parts
and screws to the plate and to the board.

    PYTHONPATH=src python3 checks/plate_clearance.py [--variant above]

Writes checks/results/plate_clearance.json.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "checks")]

import parts_index  # noqa: E402
from interference import _common_volume, _touch  # noqa: E402
from lib import frames as F  # noqa: E402
from lib import hardware_placements as H  # noqa: E402

TILTS = [i * 0.5 for i in range(21)] + [12.5, 15.0, 22.5, 30.0, 37.5, 45.0]
FIXED = ("Baseplate", "Mounting board")
# With PR #170's order (tap-collar base on the floor's front row) the base
# rested on the towers' backs at 0 deg (0.135 mm^3), a de facto hard stop.
# On the middle row, behind the front bracket, it clears them by 6.3 mm and
# the front bracket by 2.6 mm, so nothing should touch.
HARD_STOP = ("Tap collar base", "Baseplate")
LOW = ("Mounting plate", "Stepper (NEMA 11)", "Bracket (front)", "Bracket (rear)", "Tap collar base")


def movers(tilt: float, variant: str, geo: dict) -> tuple[dict, dict]:
    from lib.fasteners import fastener
    parts = parts_index.assembly(tilt, variant, "recreated", board=True)
    fixed = {k: parts.pop(k) for k in FIXED}
    # without the board screws, every fastener moves with the doser
    for name, key, joint, carrier, M in H.fastener_placements(tilt, variant, with_board=False):
        if key not in geo:
            geo[key] = fastener(key)
        parts[name] = geo[key].moved(F.to_location(M))
    return parts, fixed


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--variant", default="above", choices=["below", "above"])
    ap.add_argument("--min", type=float, default=0.01, help="mm^3 to report")
    a = ap.parse_args()
    t0, geo = time.time(), {}
    res = {"variant": a.variant, "drop_mm": F.DROP[a.variant], "tilts": TILTS, "hits": [],
           "rest_gaps_mm": []}
    for tilt in TILTS:
        parts, fixed = movers(tilt, a.variant, geo)
        for fn, f in fixed.items():
            for mn, m in parts.items():
                if not _touch(m, f):
                    continue
                v = _common_volume(m, f)
                if v > a.min:
                    res["hits"].append({"tilt": tilt, "part": mn, "fixed": fn, "mm3": round(v, 3),
                                        "expected": (mn, fn) == HARD_STOP})
                    print(tilt, mn, "x", fn, round(v, 3), flush=True)
    parts, fixed = movers(0.0, a.variant, geo)
    for name, shp in parts.items():
        if name in LOW or "Bracket screw" in name or "Tap base" in name:
            row = {"part": name, "z_min": round(shp.bounding_box().min.Z, 2),
                   "to_plate": round(shp.distance_to(fixed["Baseplate"]), 2),
                   "to_board": round(shp.distance_to(fixed["Mounting board"]), 2)}
            res["rest_gaps_mm"].append(row)
            print(row, flush=True)
    res["seconds"] = round(time.time() - t0, 1)
    out = ROOT / "checks" / "results" / "plate_clearance.json"
    out.write_text(json.dumps(res, indent=1) + "\n")
    print("wrote", out, res["seconds"], "s")


if __name__ == "__main__":
    main()
