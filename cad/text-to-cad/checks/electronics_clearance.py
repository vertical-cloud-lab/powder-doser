"""Do the tilting parts clear the electronics through the tilt range?

checks/interference.py sweeps the doser's own parts. This adds the
POWDER_DOSER_V2 board on its printed holder (placed by
lib.electronics_place.ELECTRONICS_POSE) against every placed part: the
ones that tilt (auger and cap, stepper, brackets, tap collar, solenoid,
mounting plate) and the ones that don't (baseplate, servos, pinions).
Each electronics solid whose box touches a part gets an OCC boolean, and
the smallest gap to the tilting parts is reported.

    PYTHONPATH=src python3 checks/electronics_clearance.py [--tilts 0 5 ... 45]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "checks")]

import parts_index  # noqa: E402
from interference import _common_volume  # noqa: E402
from lib import frames as F  # noqa: E402
from lib.electronics_place import ELECTRONICS_POSE  # noqa: E402


def electronics_solids(variant: str) -> list:
    from build123d import import_step
    shp = import_step(str(ROOT / "STEP" / "electronics" / "pcb_holder_assembly.step"))
    loc = F.to_location(ELECTRONICS_POSE[variant])
    return [s.moved(loc) for s in shp.solids()]


def _box(shape):
    bb = shape.bounding_box()
    return (bb.min.X, bb.min.Y, bb.min.Z), (bb.max.X, bb.max.Y, bb.max.Z)


def _boxes_touch(a, b) -> bool:
    return all(a[0][k] <= b[1][k] and b[0][k] <= a[1][k] for k in range(3))


def min_gap(parts: dict, elec: list) -> dict:
    """Smallest gap between a tilting part's bounding box and the
    electronics' bounding box: boxes enclose the shapes, so this is a lower
    bound on the true gap (exact distances on the threaded auger take
    minutes per pair)."""
    from lib.doser import TILTING
    lo = [min(getattr(e.bounding_box().min, a) for e in elec) for a in "XYZ"]
    hi = [max(getattr(e.bounding_box().max, a) for e in elec) for a in "XYZ"]
    best = {"mm": float("inf"), "part": None}
    for name, p in parts.items():
        if name.split(" [")[0] not in TILTING:
            continue
        bb = p.bounding_box()
        d = [max(lo[k] - getattr(bb.max, a), getattr(bb.min, a) - hi[k], 0.0)
             for k, a in enumerate("XYZ")]
        g = sum(v * v for v in d) ** 0.5
        if g < best["mm"]:
            best = {"mm": round(g, 2), "part": name}
    return best


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tilts", type=float, nargs="+", default=[0, 5, 10, 15, 20, 25, 30, 35, 40, 45])
    a = ap.parse_args()
    out = {"tilts": a.tilts, "hits": []}
    for variant in ("below", "above"):
        elec = electronics_solids(variant)
        eboxes = [_box(e) for e in elec]
        for tilt in a.tilts:
            parts = parts_index.assembly(tilt, variant, "recreated", board=False)
            n = 0
            for name, p in parts.items():
                pb = _box(p)
                for i, e in enumerate(elec):
                    if not _boxes_touch(pb, eboxes[i]):
                        continue
                    v = _common_volume(p, e)
                    if v > 0.05:
                        n += 1
                        out["hits"].append({"variant": variant, "tilt": tilt, "part": name,
                                            "electronics_solid": i, "mm3": round(v, 2)})
                        print(variant, tilt, name, "x electronics solid", i, round(v, 2), flush=True)
            gap = min_gap(parts, elec)
            out.setdefault("min_gap_mm", []).append({"variant": variant, "tilt": tilt, **gap})
            print(variant, tilt, "hits", n, "min gap", gap, flush=True)
    p = ROOT / "checks" / "results" / "electronics_clearance.json"
    p.write_text(json.dumps(out, indent=1) + "\n")
    print("wrote", p)


if __name__ == "__main__":
    main()
