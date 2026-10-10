"""Pairwise interference check of the assembled rig (OCC booleans).

    python check_interference.py          # prints every pair overlapping by more than 0.5 mm^3

Pairs that touch by design (screw in its hole, carriage wall on its A-1 tab,
chain links on their pins) share faces but no volume, so they don't show
up; anything listed is a real clash.
"""
from __future__ import annotations

import itertools
import time

import layout as L

# by design: pins in bushings, threads modelled as solid (cap on auger, screws in inserts/T-nuts/tapped
# holes), heat-set inserts melted into plastic
SKIP = {("chain_inner", "chain_outer"), ("chain_a1", "chain_inner"), ("auger", "auger_cap"), ("carriage", "insert_m3"),
        ("insert_m3", "m3x10_bhcs"), ("m5x20_fhcs", "tnut_m5"), ("m4x20_shcs", "tnut_m4"), ("ext_cross", "tnut_m5"),
        ("ext_long", "tnut_m5"), ("ext_long", "tnut_m4"), ("m5x18_shcs", "motor_plate"), ("m5x20_fhcs", "nut_m5"),
        ("m5x40_shcs", "nut_m5"), ("idler_stud", "nut_12"), ("m4x20_fhcs", "tensioner_block")}


def main(min_vol: float = 0.5) -> list:
    pl = L.placements()
    shapes = [(p, L.moved(p.key, p.M)) for p in pl]
    boxes = [s.BoundingBox() for _, s in shapes]
    hits, n = [], 0
    t0 = time.time()
    for (i, (pa, sa)), (j, (pb, sb)) in itertools.combinations(enumerate(shapes), 2):
        a, b = boxes[i], boxes[j]
        if a.xmax < b.xmin or b.xmax < a.xmin or a.ymax < b.ymin or b.ymax < a.ymin or a.zmax < b.zmin or b.zmax < a.zmin:
            continue
        if tuple(sorted((pa.key, pb.key))) in {tuple(sorted(k)) for k in SKIP}:
            continue
        n += 1
        v = sa.intersect(sb).Volume()
        if v > min_vol:
            hits.append((pa.name, pb.name, round(v, 1)))
    print(f"{n} candidate pairs checked in {time.time() - t0:.0f} s; {len(hits)} clash(es) over {min_vol} mm^3")
    for h in sorted(hits, key=lambda h: -h[2]):
        print(f"  {h[2]:9.1f} mm^3  {h[0]}  x  {h[1]}")
    return hits


if __name__ == "__main__":
    main()
