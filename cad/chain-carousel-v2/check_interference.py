"""Pairwise interference check of the assembled rig v2 (OCC booleans).

    python check_interference.py           # home pose: every pair overlapping by more than 0.5 mm^3
    python check_interference.py --sweep   # index the chain 8 pitches (one module) round all four corners
    python check_interference.py --tilt    # module 1 tilted 0-90 deg at the station, against everything

Pairs that touch by design (screw in its hole, carriage on its A-1 tab,
chain links on their pins) share faces but no volume, so they don't show
up; anything listed is a real clash. Threads are modelled as plain
cylinders, so a screw in a tapped hole, insert or T-nut overlaps by design
and those pairs are skipped.
"""
from __future__ import annotations

import itertools
import math
import time

import numpy as np

import layout as L

SKIP = {("chain_inner", "chain_outer"), ("chain_a1", "chain_inner"), ("auger", "auger_cap"), ("auger_blank", "auger_cap"),
        ("carriage", "insert_m25"), ("insert_m25", "m25x6_bhcs"), ("carriage", "m25x6_bhcs"),
        ("m5x10_fhcs", "sam_mounting_plate"),                       # hinge pin in Sam's knuckle
        ("m5x12_bhcs", "tnut_m5"), ("ext_post", "tnut_m5"), ("ext_x", "tnut_m5"), ("ext_post", "m5x12_bhcs"),
        ("bolt_m10x30", "nut_m10"), ("coupling", "nema34"), ("m5x12_shcs", "standoff"), ("m5x20_shcs", "standoff"),
        ("m5x30_shcs", "nut_m5"), ("m5x10_shcs", "side_plate_front"), ("m5x10_shcs", "side_plate_back"),
        ("hold_down", "insert_m5"), ("insert_m5", "m5x16_shcs"), ("foot", "tnut_m5"), ("ext_x", "foot")}
SKIP = {tuple(sorted(k)) for k in SKIP}

MOVING = ("carriage", "sam_mounting_plate", "auger", "auger_blank", "auger_cap", "m5x10_fhcs", "m25x6_bhcs", "insert_m25",
          "magnet", "sam_electronics_carriage")


def _overlaps(objs: list, pairs=None, min_vol: float = 0.5) -> list:
    boxes = [s.BoundingBox() for _, _, s in objs]
    hits = []
    it = pairs if pairs is not None else itertools.combinations(range(len(objs)), 2)
    for i, j in it:
        (ka, na, sa), (kb, nb, sb) = objs[i], objs[j]
        a, b = boxes[i], boxes[j]
        if a.xmax < b.xmin or b.xmax < a.xmin or a.ymax < b.ymin or b.ymax < a.ymin or a.zmax < b.zmin or b.zmax < a.zmin:
            continue
        if tuple(sorted((ka, kb))) in SKIP:
            continue
        v = sa.intersect(sb).Volume()
        if v > min_vol:
            hits.append((na, nb, round(v, 1)))
    return hits


def main(min_vol: float = 0.5) -> list:
    pl = L.placements()
    objs = [(p.key, p.name, L.moved(p.key, p.M)) for p in pl]
    t0 = time.time()
    hits = _overlaps(objs, min_vol=min_vol)
    print(f"home pose: {len(pl)} instances, {time.time() - t0:.0f} s; {len(hits)} clash(es) over {min_vol} mm^3")
    for h in sorted(hits, key=lambda h: -h[2]):
        print(f"  {h[2]:9.1f} mm^3  {h[0]}  x  {h[1]}")
    return hits


def _static(base) -> list:
    """Everything that doesn't move with the chain."""
    return [(p.key, p.name, L.moved(p.key, p.M)) for p in base if p.key not in MOVING and not p.key.startswith("chain")]


def sweep(steps: int = 8) -> list:
    """Index the chain 0..steps-1 pitches past home. Every carriage and its
    module is checked against the other carriages and modules and against
    everything static (shafts, sprockets, bearings, plates, frame,
    hold-downs, motor). One module pitch takes each module a quarter of the
    way round, so 8 steps cover every corner position."""
    base = L.placements()
    static = _static(base)
    hits = []
    for k in range(steps):
        movers = []
        for ci, li in enumerate(L.carriage_links()):
            D = L.carriage_frame(li + k) @ np.linalg.inv(L.carriage_frame(li))
            for p in base:
                if p.key in MOVING and p.name.split()[-1] == str(ci + 1) and p.key != "sam_electronics_carriage":
                    movers.append((p.key, f"{p.name} [c{ci + 1}]", L.moved(p.key, D @ p.M)))
                elif ci == 0 and p.name in ("Home magnet", "Auger, threaded storage (lab) 1"):
                    movers.append((p.key, f"{p.name} [c1]", L.moved(p.key, D @ p.M)))
        objs = movers + static
        n = len(movers)
        pairs = [(i, j) for i in range(n) for j in range(i + 1, len(objs))
                 if not (j < n and movers[i][1].split(" [")[1] == movers[j][1].split(" [")[1])]
        h = _overlaps(objs, pairs)
        hits += [(k, *x) for x in h]
        print(f"  step {k}: {len(movers)} moving parts, {len(h)} clash(es)", flush=True)
    print(f"sweep over {steps} pitch steps: {len(hits)} clash(es)")
    for h in hits:
        print(f"  step {h[0]}: {h[3]} mm^3  {h[1]}  x  {h[2]}")
    return hits


def tilt(angles=(15, 30, 45, 60, 75, 90)) -> list:
    """Module 1 (Sam's plate, auger, cap) tilted about its hinge at the
    station, against every other part in the rig. The snap hooks are what
    the plate pushes past, so carriage 1 itself is left out."""
    hits = []
    base = L.placements()
    others = [(p.key, p.name, L.moved(p.key, p.M)) for p in base
              if not (p.step == 10 and p.name.endswith(" 1")) and p.name != "Carriage 1"
              and p.key != "sam_electronics_carriage"]
    for a in angles:
        Ms = L.sam_frame(L.station_frame(), a)
        Ma = Ms @ L.T(L.Ry(math.pi / 2), (L.AUGER_Z0_XS, 0, 0))
        mod = [("sam_mounting_plate", f"Mounting plate 1 @{a}", L.moved("sam_mounting_plate", Ms)),
               ("auger", f"Auger 1 @{a}", L.moved("auger", Ma)),
               ("auger_cap", f"Cap 1 @{a}", L.moved("auger_cap", Ma @ L.T(None, (0, 0, L.AUGER_LEN))))]
        objs = mod + others
        pairs = [(i, j) for i in range(len(mod)) for j in range(len(mod), len(objs))]
        h = _overlaps(objs, pairs)
        hits += h
        print(f"  tilt {a:2d} deg: {len(h)} clash(es)", flush=True)
    print(f"tilt sweep: {len(hits)} clash(es)")
    for h in hits:
        print(f"  {h[2]} mm^3  {h[0]}  x  {h[1]}")
    return hits


if __name__ == "__main__":
    import sys
    if "--sweep" in sys.argv:
        sweep()
    elif "--tilt" in sys.argv:
        tilt()
    else:
        main()
