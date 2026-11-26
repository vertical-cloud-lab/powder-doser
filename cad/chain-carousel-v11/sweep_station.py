"""v9 (v7's, with the balance on its block, the beaker on the pan 32 mm under the exit, and the weighing chamber's deck 4.6 mm under the passing modules): the chain sweep restricted to the station: every carriage and module within two modules of the station
(their new dock posts, the gears, the door strips, the latch followers) against the parked station (EC v7 and its tail, the
P16, the two guides and the cross bars, the latch cam, the hold-downs) and the balance, over one module of travel the way the
machine runs, in 1-link steps. The full --sweep (every pair) takes far longer; v7 left everything else as v6 had it.

    python sweep_station.py    -> checks/sweep_station.json
"""
from __future__ import annotations

import json
import time

import numpy as np

import check_interference as CI
import layout as L
from params import MODULE_LINKS, RUN_DIRECTION, P

hits, poses = [], []
t0 = time.time()
import sys
STEPS = [float(v) for v in sys.argv[1].split(",")] if len(sys.argv) > 1 else [float(i) for i in range(MODULE_LINKS + 1)]
for i in STEPS:
    s = RUN_DIRECTION * float(i)
    pl = L.placements(L.State(shift=s, ext=0.0, enclosure=False))
    near = []
    for p in pl:
        if p.module < 0 or p.group not in ("modules", "carriages"):
            continue
        d = ((L.slot_of(p.module, s) - L.CARRIAGE_LINK0 + L.N_LINKS / 2) % L.N_LINKS - L.N_LINKS / 2) * P
        if abs(d) <= 2.2 * MODULE_LINKS * P:
            near.append(p)
    fixed = [p for p in pl if p.group in ("station", "station_ec", "station_act", "cable", "scale", "chamber") or p.key in ("beam10", "rung", "nema34")]
    fixed = [p for p in fixed if p.key != "cable10_outside"]
    mo, fo = CI.objects(near), CI.objects(fixed)
    objs = mo + fo
    pairs = [(a, b) for a in range(len(mo)) for b in range(len(mo), len(objs))]
    h = CI.overlaps(objs, pairs)
    hits += [(f"{a} @{s:+.0f}", b, v) for a, b, v in h]
    poses.append(s)
    print(f"  shift {s:+3.0f} links: {len(h)} clash(es) ({len(near)} moving, {len(fixed)} fixed)", flush=True)
CI._report(sys.argv[2] if len(sys.argv) > 2 else "sweep_station", hits, {"step_links": 1, "poses": len(poses), "direction": RUN_DIRECTION, "seconds": round(time.time() - t0),
                                   "scope": "carriages and modules within 2.2 modules of the station vs the parked station, the balance, its block and the beaker, and the weighing chamber (deck, baffles)"})
