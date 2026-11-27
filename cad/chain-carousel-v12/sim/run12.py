"""Run the v12 mesh studies in parallel (mesh12.py) and save every result to out/*.json.

    python run12.py entry       # sideways entry with v12's seek: 6 N cradle over the tolerance stack x clevis stiffness; 4 N; a leading-arm
                                #   pivot; one seat only (v11's)
    python run12.py robust      # what the outcome depends on: the EC's sideways give, tooth friction, detent, drag, index speed, the pinion
                                #   held or seeking during the index
    python run12.py exit        # the next index pulls the gear out
    python run12.py cycle       # tilt 30, dose, 90, dose, back, reverse at rest; and stall ramps at 0/30/60/90 deg
    python run12.py all
RUN12_PROCS sets the number of processes (default 4).
"""
from __future__ import annotations

import json
import multiprocessing as mp
import os
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import mesh12 as M  # noqa: E402

NPH = 12
OFFSETS = (-0.5, -0.3, 0.0, 0.25, 0.5, 1.0)          # the tolerance stack: the EC's pivot and stop this far farther from the gear (mm)


def pool_map(fn, jobs, n=4):
    n = int(os.environ.get("RUN12_PROCS", n))
    with mp.get_context("fork").Pool(n) as P:
        return P.map(fn, jobs, chunksize=1)


def _entry(args):
    kw, ph, mode, v, label = args
    r, _ = M.entry(M.Cfg(**kw), ph, mode=mode, v=v)
    r["cfg"] = kw
    r["v"] = v
    r["label"] = label
    return r


def _save(name, rs, t):
    (M.OUT / f"{name}.json").write_text(json.dumps(dict(n=len(rs), wall_s=round(time.time() - t), runs=rs), indent=0))
    jams = sum(r["jam"] for r in rs)
    left = sum(r["outcome"].startswith("stub left") for r in rs)
    print(f"{name}: {len(rs)} runs in {time.time() - t:.0f}s; jams {jams}, stubs left {left}", flush=True)


def entry_study():
    jobs = []
    for kr in (3.0, 10.0, 100.0):                                       # v12 as drawn: 6 N at the stop, trailing arm, two seats
        for e in OFFSETS:
            jobs += [(dict(a_err=e, k_roll=kr), k / NPH, "free", 50.0, "v12") for k in range(NPH)]
    for e in OFFSETS:                                                   # a 4 N spring
        jobs += [(dict(a_err=e, f_spring=4.0), k / NPH, "free", 50.0, "4 N spring") for k in range(NPH)]
    for e in OFFSETS:                                                   # the pivot on the other side (a leading arm)
        jobs += [(dict(a_err=e, piv_dy=18.5), k / NPH, "free", 50.0, "leading arm") for k in range(NPH)]
    for e in OFFSETS:                                                   # the dowels 10 mm nearer the gear (level with the mesh's push)
        jobs += [(dict(a_err=e, piv_dz=10.0), k / NPH, "free", 50.0, "pivot 10 mm nearer the gear") for k in range(NPH)]
    for e in OFFSETS:                                                   # one seat (v11's), the loosest clevis
        jobs += [(dict(a_err=e, seats=1, k_roll=3.0), k / NPH, "free", 50.0, "one seat") for k in range(NPH)]
    t = time.time()
    _save("entry", pool_map(_entry, jobs), t)


def robust_study():
    jobs = []
    for kw, lbl in ((dict(k_lat=1.0e5), "EC 10x stiffer sideways"), (dict(k_lat=1.0e6), "EC 100x stiffer sideways"), (dict(mu=0.3), "dry teeth (mu 0.3)"),
                    (dict(detent=1.0e-3), "detent 1 mN m"), (dict(detent=8.0e-3), "detent 8 mN m"), (dict(drag=0.03), "packed powder (30 mN m)")):
        jobs += [(kw, k / NPH, "free", 50.0, lbl) for k in range(NPH)]
    jobs += [(dict(), k / NPH, "free", 25.0, "index at 25 mm/s") for k in range(NPH)]
    jobs += [(dict(), k / NPH, "free", 100.0, "index at 100 mm/s") for k in range(NPH)]
    jobs += [(dict(), k / NPH, "held", 50.0, "pinion held during the index") for k in range(NPH)]
    jobs += [(dict(), k / NPH, "seek", 50.0, "pinion seeking during the index") for k in range(NPH)]
    t = time.time()
    _save("entry_robust", pool_map(_entry, jobs), t)


def _exit(args):
    kw, mode = args
    r, _ = M.exit_run(M.Cfg(**kw), mode=mode)
    r.update(kw)
    r["mode"] = mode
    return r


def exit_study():
    jobs = [(dict(a_err=e, k_roll=kr), mode) for e in (-0.3, 0.0, 0.5, 1.0) for kr in (3.0, 100.0) for mode in ("free", "held")]
    t = time.time()
    rs = pool_map(_exit, jobs)
    (M.OUT / "exit.json").write_text(json.dumps(dict(n=len(rs), runs=rs), indent=0))
    print(f"exit: {len(rs)} runs in {time.time() - t:.0f}s; peak chain force {max(r['chain_force_max_N'] for r in rs):.1f} N", flush=True)


def _cycle(args):
    kw, stall_at = args
    out, A = M.cycle(M.Cfg(**kw), tilts=(30.0, 90.0) if stall_at is None else (stall_at,), ramp_stall_at=stall_at)
    return dict(cfg=kw, stall_at=stall_at, steps=out["steps"], tooth_jumps=out["tooth_jumps"], phases=M.summarize_cycle(out, A))


def cycle_study():
    jobs = [(dict(), None), (dict(k_roll=3.0), None), (dict(k_roll=100.0), None), (dict(a_err=0.5), None), (dict(a_err=-0.3), None),
            (dict(a_err=1.0), None), (dict(f_spring=4.0), None), (dict(seats=1, k_roll=3.0), None)]
    for a in (0.0, 30.0, 60.0, 90.0):                                   # stall ramps: v12 at rest and tilted
        jobs.append((dict(), a))
    jobs += [(dict(a_err=0.5), 30.0), (dict(a_err=1.0), 30.0), (dict(a_err=-0.3), 30.0)]
    for a in (0.0, 30.0, 90.0):
        jobs.append((dict(f_spring=4.0), a))
        jobs.append((dict(piv_dz=10.0), a))
        jobs.append((dict(piv_dy=18.5), a))
    for a in (0.0, 30.0):                                               # v11 as drawn (rigid), for comparison on the same code
        jobs.append((dict(cradle=False), a))
    t = time.time()
    rs = pool_map(_cycle, jobs)
    (M.OUT / "cycle.json").write_text(json.dumps(dict(n=len(rs), runs=rs), indent=0))
    print(f"cycle: {len(rs)} runs in {time.time() - t:.0f}s", flush=True)


if __name__ == "__main__":
    what = sys.argv[1] if len(sys.argv) > 1 else "all"
    if what in ("entry", "all"):
        entry_study()
    if what in ("robust", "all"):
        robust_study()
    if what in ("exit", "all"):
        exit_study()
    if what in ("cycle", "all"):
        cycle_study()
