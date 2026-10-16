"""Compare two STEP solids: volumes, boxes and IoU (no Onshape calls).

    python compare_step.py candidate.step reference.step [--out result.json] [--dz -3]

``--dz`` moves the reference before comparing (e.g. -3 for the thinner-table edit, where
everything on the table sits 3 mm lower). Used to check fsgen's local build and the STEP
Onshape exports back against text-to-cad's ``baseplate_servos_above.step`` (PR #176).
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import build123d as bd


def load(path: str):
    solids = bd.import_step(path).solids()
    return solids[0] if len(solids) == 1 else bd.Compound(list(solids))


def box(s) -> list[list[float]]:
    b = s.bounding_box()
    return [[round(b.min.X, 3), round(b.min.Y, 3), round(b.min.Z, 3)],
            [round(b.max.X, 3), round(b.max.Y, 3), round(b.max.Z, 3)]]


def compare(cand_path: str, ref_path: str, dz: float = 0.0) -> dict:
    a, b = load(cand_path), load(ref_path)
    if dz:
        b = b.moved(bd.Location((0, 0, dz)))
    inter = (a & b).volume
    union = a.volume + b.volume - inter
    return {"candidate": Path(cand_path).name, "reference": Path(ref_path).name, "reference_dz_mm": dz,
            "candidate_volume_mm3": round(a.volume, 3), "reference_volume_mm3": round(b.volume, 3),
            "volume_diff_pct": round(100 * (a.volume - b.volume) / b.volume, 5),
            "candidate_bbox_mm": box(a), "reference_bbox_mm": box(b),
            "candidate_solids": len(a.solids()), "reference_solids": len(b.solids()),
            "iou": round(inter / union, 6)}


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("candidate")
    ap.add_argument("reference")
    ap.add_argument("--dz", type=float, default=0.0)
    ap.add_argument("--out")
    args = ap.parse_args()
    res = compare(args.candidate, args.reference, args.dz)
    print(json.dumps(res, indent=1))
    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(json.dumps(res, indent=1) + "\n")
