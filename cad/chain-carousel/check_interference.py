"""Pairwise interference check of the assembled rig (OCC booleans).

    python check_interference.py          # home pose: every pair overlapping by more than 0.5 mm^3
    python check_interference.py --sweep  # index the chain 8 pitches: carriages vs neighbours and the wraps

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
SKIP = {("chain_inner", "chain_outer"), ("chain_a1", "chain_inner"), ("auger", "auger_cap"), ("carriage", "insert_m25"),
        ("insert_m25", "m25x8_bhcs"), ("m5x20_fhcs", "tnut_m5"), ("m4x25_shcs", "tnut_m4"), ("ext_cross", "tnut_m5"),
        ("ext_long", "tnut_m5"), ("ext_long", "tnut_m4"), ("m5x18_shcs", "motor_plate"), ("m5x20_fhcs", "nut_m5"),
        ("m5x40_shcs", "nut_m5"), ("idler_stud", "nut_12"), ("m4x20_fhcs", "tensioner_block"), ("nut_m5", "tensioner_block")}


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


def sweep(steps: int = 8) -> list:
    """Index the chain 0..steps-1 pitches past home and check every carriage
    (and module 1) against its neighbours and the parts at the two wraps."""
    import numpy as np
    static_keys = ("sprocket_drive", "sprocket_idler", "nut_12", "washer_12", "idler_stud", "tensioner_block", "nema34",
                   "hold_down", "m4x25_shcs")
    base = L.placements()
    static = [(p, L.moved(p.key, p.M)) for p in base if p.key in static_keys]
    moving_keys = ("carriage", "sam_mounting_plate", "auger", "auger_cap", "m5x18_shcs", "m25x8_bhcs")
    hits = []
    for k in range(steps):
        movers = []
        for ci, li in enumerate(L.carriage_links()):
            M_home = L.link_frame(li, 0.0)
            M_now = L.link_frame((li + k) % L.N_LINKS, 0.0)
            D = M_now @ np.linalg.inv(M_home)
            for p in base:
                if p.key in moving_keys and (p.name.endswith(f" {ci + 1}") or (ci == 0 and p.step == 11)):
                    movers.append((f"{p.name} [c{ci + 1}]", L.moved(p.key, D @ p.M)))
        objs = movers + [(p.name, s) for p, s in static]
        boxes = [s.BoundingBox() for _, s in objs]
        for (i, (na, sa)), (j, (nb, sb)) in itertools.combinations(enumerate(objs), 2):
            if i >= len(movers) and j >= len(movers):
                continue
            a, b = boxes[i], boxes[j]
            if a.xmax < b.xmin or b.xmax < a.xmin or a.ymax < b.ymin or b.ymax < a.ymin or a.zmax < b.zmin or b.zmax < a.zmin:
                continue
            if na.split(" [")[1:] == nb.split(" [")[1:] and " [" in na:
                continue                                       # same carriage's own parts
            v = sa.intersect(sb).Volume()
            if v > 0.5:
                hits.append((k, na, nb, round(v, 1)))
    print(f"sweep over {steps} pitch steps: {len(hits)} clash(es)")
    for h in hits:
        print(f"  step {h[0]}: {h[3]} mm^3  {h[1]}  x  {h[2]}")
    return hits


if __name__ == "__main__":
    import sys
    sweep() if "--sweep" in sys.argv else main()
