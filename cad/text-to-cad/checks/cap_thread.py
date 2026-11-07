"""Does the auger cap's thread groove meet the auger's thread?

Turns the cap about the tube axis in 30 deg steps, seated on the tube end
(cap frame origin at z = AUGER_LEN), and prints the auger & cap overlap.
A right-handed 3.5 mm-pitch thread repeats every turn, so the overlap is a
smooth function of the angle with a zero band where the crest sits in the
groove; lib.frames.CAP_TURN_DEG is the middle of that band.

    python3 checks/cap_thread.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from lib import frames  # noqa: E402


def overlap(a, b) -> float:
    from OCP.BRepAlgoAPI import BRepAlgoAPI_Common
    from OCP.BRepGProp import BRepGProp
    from OCP.GProp import GProp_GProps
    op = BRepAlgoAPI_Common(a.wrapped, b.wrapped)
    p = GProp_GProps()
    BRepGProp.VolumeProperties_s(op.Shape(), p)
    return p.Mass()


def main() -> None:
    from build123d import Location, Rot, import_step
    auger = import_step(str(ROOT / "STEP/parts/auger.step")).solids()[0]
    cap = import_step(str(ROOT / "STEP/parts/auger_cap.step")).solids()[0]
    rows = []
    for ang in range(0, 360, 30):
        placed = cap.moved(Location((0, 0, frames.AUGER_LEN)) * Rot(0, 0, ang))
        rows.append({"cap_turn_deg": ang, "overlap_mm3": round(overlap(auger, placed), 2)})
        print(rows[-1], flush=True)
    out = ROOT / "checks" / "results" / "cap_thread.json"
    out.write_text(json.dumps({"cap_turn_deg_used": frames.CAP_TURN_DEG, "rows": rows}, indent=1) + "\n")
    print("wrote", out)


if __name__ == "__main__":
    main()
