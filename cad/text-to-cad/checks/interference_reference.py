"""Which overlaps are inherited from the lab's design?

Recomputes, on PR #170's own STEP files (the lab's Fusion 360 exports and its
purchased-part stand-ins, fetched by checks/fetch_reference.py), the part
pairs that checks/interference.py flags on the recreation, at tilt 0, for the
current (servos-below) layout.  Same placements (lib.frames), same booleans.

    python3 checks/interference_reference.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "checks")]

import parts_index  # noqa: E402
from interference import _common_volume, _touch  # noqa: E402

PAIRS = [("Baseplate", "Servo MG996R (+X)"), ("Baseplate", "Servo MG996R (-X)"),
         ("Mounting plate", "Stepper (NEMA 11)"), ("Bracket (rear)", "Stepper (NEMA 11)"),
         ("Stepper pinion", "Stepper (NEMA 11)"), ("Baseplate", "Tap collar base"),
         ("Auger", "Auger cap")]


def main() -> None:
    out = {}
    for source in ("reference", "recreated"):
        parts = parts_index.assembly(0.0, "below", source)
        rows = []
        for a, b in PAIRS:
            pa, pb = parts[a], parts[b]
            v = _common_volume(pa, pb) if _touch(pa, pb) else 0.0
            rows.append({"a": a, "b": b, "mm3": round(v, 3)})
            print(source, a, "x", b, rows[-1]["mm3"], flush=True)
        out[source] = rows
    p = ROOT / "checks" / "results" / "interference_reference.json"
    p.write_text(json.dumps(out, indent=1) + "\n")
    print("wrote", p)


if __name__ == "__main__":
    main()
