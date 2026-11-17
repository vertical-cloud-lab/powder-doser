"""Interference sweep: every pair of parts, over the tilt range, both layouts.

Parts are placed by lib.frames (the servo pinions turn -2x the tilt, as the
28T:14T mesh drives them).  Each pair whose bounding boxes touch gets an OCC
boolean; overlaps above ``--min`` mm^3 are reported.  Fasteners are checked
separately against the parts they pass through (``--fasteners``): a screw in
a clearance hole should show nothing, and threads cut into a tapped part
(motor, servo shaft, solenoid) are flagged as expected.

    python3 checks/interference.py [--tilts 0 15 30 45] [--fasteners] [--variants above]

With ``--variants`` only those layouts are swept; the others are kept from
the previous results.
"""
from __future__ import annotations

import argparse
import itertools
import json
import time
from pathlib import Path

import parts_index
from lib import hardware_placements as H
from lib.frames import to_location

ROOT = Path(__file__).resolve().parents[1]

# threads into these are meant to overlap (the screw cuts or meets a thread)
TAPPED = {("shcs_m2p5x8", "Stepper (NEMA 11)"), ("shcs_m3x10", "Servo MG996R (+X)"),
          ("shcs_m3x10", "Servo MG996R (-X)"), ("shcs_m3x5", "Solenoid (Adafruit 412)"),
          ("wood_10x1p25", "Mounting board")}


def _common_volume(a, b) -> float:
    from OCP.BRepAlgoAPI import BRepAlgoAPI_Common
    from OCP.BRepGProp import BRepGProp
    from OCP.GProp import GProp_GProps
    op = BRepAlgoAPI_Common(a.wrapped, b.wrapped)
    if not op.IsDone():
        return float("nan")
    p = GProp_GProps()
    BRepGProp.VolumeProperties_s(op.Shape(), p)
    return p.Mass()


def _touch(a, b, pad=0.0) -> bool:
    ba, bb = a.bounding_box(), b.bounding_box()
    return all(lo1 - pad <= hi2 and lo2 - pad <= hi1
               for lo1, hi1, lo2, hi2 in zip(ba.min, ba.max, bb.min, bb.max))


def sweep(variant: str, tilts, min_vol: float, fasteners: bool) -> dict:
    out = {"variant": variant, "tilts": list(tilts), "pairs": [], "fasteners": []}
    for tilt in tilts:
        parts = parts_index.assembly(tilt, variant, "recreated")
        for (na, a), (nb, b) in itertools.combinations(parts.items(), 2):
            if not _touch(a, b):
                continue
            v = _common_volume(a, b)
            if v > min_vol or v != v:
                out["pairs"].append({"tilt": tilt, "a": na, "b": nb, "mm3": round(v, 3)})
                print(variant, tilt, na, "x", nb, round(v, 3), flush=True)
        if fasteners:
            from lib.fasteners import fastener
            geo = {}
            for name, key, joint, carrier, M in H.fastener_placements(tilt, variant):
                if key not in geo:
                    geo[key] = fastener(key)
                f = geo[key].moved(to_location(M))
                for pn, p in parts.items():
                    if not _touch(f, p):
                        continue
                    v = _common_volume(f, p)
                    if v > min_vol:
                        expected = (key, pn.split(" [")[0]) in TAPPED
                        out["fasteners"].append({"tilt": tilt, "fastener": name, "kind": key,
                                                 "part": pn, "mm3": round(v, 3),
                                                 "expected": expected})
                        print(variant, tilt, name, "x", pn, round(v, 3),
                              "(expected)" if expected else "", flush=True)
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tilts", type=float, nargs="+", default=[0.0, 15.0, 30.0, 45.0])
    ap.add_argument("--min", type=float, default=0.05, help="mm^3 to report")
    ap.add_argument("--fasteners", action="store_true")
    ap.add_argument("--variants", nargs="+", default=["below", "above"], choices=["below", "above"])
    a = ap.parse_args()
    t0 = time.time()
    out = ROOT / "checks" / "results" / "interference.json"
    res = json.loads(out.read_text()) if out.exists() else {}
    res.update({v: sweep(v, a.tilts, a.min, a.fasteners) for v in a.variants})
    res["seconds"] = round(time.time() - t0, 1)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(res, indent=1) + "\n")
    print("wrote", out, res["seconds"], "s")


if __name__ == "__main__":
    main()
