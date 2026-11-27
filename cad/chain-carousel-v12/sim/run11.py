"""Run the v11 mesh studies in parallel (mesh11.py) and save every result to out/*.json.

    python run11.py entry       # sideways entry: as drawn and spring-loaded, phases x tolerance x clevis stiffness x pinion mode
    python run11.py exit        # the next index pulls the gear out
    python run11.py cycle       # tilt 30, dose, 90, dose, back, reverse at rest; and stall ramps at 0/30/60/90 deg
    python run11.py all
"""
from __future__ import annotations

import json
import multiprocessing as mp
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import mesh11 as M  # noqa: E402

KEYS = ("phase", "mode", "a_err", "spring", "k_roll", "drag_mNm", "jam", "meshed", "stubbed", "meshed_after_seek", "outcome", "cd_at_stop",
        "cd_after_seek", "cd_end", "tooth_force_max_N", "tooth_force_2ms_max_N", "chain_force_max_N",
        "chain_lag_max_mm", "pinion_turn_deg", "auger_turn_deg", "ec_roll_max_deg", "module_lift_max_deg", "end_tooth_force_N", "end_seat_N")
NPH = 12


def _entry(args):
    kw, ph, mode = args
    r, _ = M.entry(M.Cfg(**kw), ph, mode=mode)
    out = {k: r[k] for k in KEYS}
    if kw.get("spring"):
        c = M.Cfg(**kw)
        out["f_spring"], out["stop_deep"] = c.f_spring, c.stop_deep
    return out


def _exit(args):
    kw, mode = args
    r, _ = M.exit_run(M.Cfg(**kw), mode=mode)
    r.update(kw)
    r["mode"] = mode
    return r


def _cycle(args):
    kw, stall_at = args
    out, A = M.cycle(M.Cfg(**kw), tilts=(30.0, 90.0) if stall_at is None else (stall_at,), ramp_stall_at=stall_at)
    res = dict(cfg=kw, stall_at=stall_at, steps=out["steps"], tooth_jumps=out["tooth_jumps"], phases=M.summarize_cycle(out, A))
    return res


def pool_map(fn, jobs, n=2):
    n = int(__import__("os").environ.get("RUN11_PROCS", n))
    with mp.get_context("fork").Pool(n) as P:
        return P.map(fn, jobs)


def entry_study():
    jobs = []
    # 1. as drawn: tolerance stack (pinion farther + / nearer -) x clevis roll stiffness, pinion free (the Pi driver's default)
    for kr in (3.0, 10.0, 100.0):
        for e in (-0.3, -0.15, 0.0, 0.25, 0.5):
            jobs += [(dict(a_err=e, k_roll=kr), k / NPH, "free") for k in range(NPH)]
    # 2. as drawn: pinion held (driver on) and seeking (--seek), and with packed powder's drag
    jobs += [(dict(), k / NPH, "held") for k in range(NPH)]
    jobs += [(dict(), k / NPH, "seek") for k in range(NPH)]
    jobs += [(dict(drag=0.03), k / NPH, "free") for k in range(NPH)]
    # 3. spring-loaded pinion (v12 candidate): the same tolerance sweep, wider, two clevis stiffnesses; 6 N with the stop 0.4 mm deep,
    #    and the lighter 4 N with the stop 0.2 mm deep
    for kr in (3.0, 100.0):
        for e in (-0.5, -0.3, 0.0, 0.25, 0.5, 1.0):
            jobs += [(dict(a_err=e, k_roll=kr, spring=True), k / NPH, "free") for k in range(NPH)]
    for e in (-0.5, -0.3, 0.0, 0.25, 0.5, 1.0):
        jobs += [(dict(a_err=e, spring=True, f_spring=4.0, stop_deep=0.2), k / NPH, "free") for k in range(NPH)]
    t = time.time()
    rs = pool_map(_entry, jobs, 3)
    (M.OUT / "entry.json").write_text(json.dumps(dict(n=len(rs), wall_s=round(time.time() - t), runs=rs), indent=0))
    print(f"entry: {len(rs)} runs in {time.time() - t:.0f}s", flush=True)
    return rs


def exit_study():
    jobs = [(dict(a_err=e, k_roll=kr), mode) for e in (-0.3, 0.0, 0.5) for kr in (3.0, 100.0) for mode in ("free", "held")]
    jobs += [(dict(a_err=e, spring=True), "free") for e in (-0.3, 0.0, 0.5)]
    t = time.time()
    rs = pool_map(_exit, jobs, 3)
    (M.OUT / "exit.json").write_text(json.dumps(dict(n=len(rs), runs=rs), indent=0))
    print(f"exit: {len(rs)} runs in {time.time() - t:.0f}s", flush=True)
    return rs


def cycle_study():
    jobs = [(dict(), None), (dict(k_roll=3.0), None), (dict(k_roll=100.0), None), (dict(a_err=0.5), None), (dict(a_err=-0.3), None),
            (dict(spring=True), None), (dict(spring=True, a_err=0.5), None), (dict(spring=True, f_spring=4.0, stop_deep=0.2), None)]
    # stall ramps: at rest (0), 30, 60, 90 deg; as drawn and spring-loaded
    for sp in (False, True):
        for a in (0.0, 30.0, 60.0, 90.0):
            jobs.append((dict(spring=sp), a))
        jobs.append((dict(spring=sp, a_err=0.5), 30.0))
    for a in (0.0, 30.0, 90.0):
        jobs.append((dict(spring=True, f_spring=4.0, stop_deep=0.2), a))
    t = time.time()
    rs = pool_map(_cycle, jobs, 3)
    (M.OUT / "cycle.json").write_text(json.dumps(dict(n=len(rs), runs=rs), indent=0))
    print(f"cycle: {len(rs)} runs in {time.time() - t:.0f}s", flush=True)
    return rs


def _entry_v(args):
    kw, ph, mode, v = args
    r, _ = M.entry(M.Cfg(**kw), ph, mode=mode, v=v)
    out = {k: r[k] for k in KEYS}
    out["v"] = v
    out["cfg"] = kw
    return out


def robust_study():
    """What the jams depend on: the EC's sideways give, tooth friction, the index speed, the free motor's detent."""
    jobs = []
    for kw in (dict(k_lat=1.0e5), dict(k_lat=1.0e6), dict(mu=0.3), dict(detent=1.0e-3), dict(detent=8.0e-3), dict(drag=0.03)):
        jobs += [(kw, k / NPH, "free", 50.0) for k in range(NPH)]
        jobs += [(dict(kw, spring=True), k / NPH, "free", 50.0) for k in range(NPH)]
    jobs += [(dict(), k / NPH, "free", 25.0) for k in range(NPH)] + [(dict(spring=True), k / NPH, "free", 25.0) for k in range(NPH)]
    jobs += [(dict(), k / NPH, "free", 100.0) for k in range(NPH)] + [(dict(spring=True), k / NPH, "free", 100.0) for k in range(NPH)]
    t = time.time()
    rs = pool_map(_entry_v, jobs, 3)
    (M.OUT / "entry_robust.json").write_text(json.dumps(dict(n=len(rs), wall_s=round(time.time() - t), runs=rs), indent=0))
    print(f"robust: {len(rs)} runs in {time.time() - t:.0f}s", flush=True)
    return rs


def _entry_rev(args):
    kw, ph = args
    r, _ = M.entry(M.Cfg(**kw), ph, seek_reverse=True)
    out = {k: r[k] for k in KEYS}
    out["seek"] = "forward 0.2 s, back 0.2 s"
    c = M.Cfg(**kw)
    out["f_spring"], out["stop_deep"] = c.f_spring, c.stop_deep
    return out


def seek2_study():
    """Every spring-loaded case again with the seek reversing halfway (0.2 s each way at 0.25 rev/s)."""
    jobs = [(dict(a_err=e, k_roll=kr, spring=True), k / NPH) for kr in (3.0, 10.0, 100.0) for e in (-0.5, -0.3, 0.0, 0.25, 0.5, 1.0) for k in range(NPH)]
    jobs += [(dict(a_err=e, spring=True, f_spring=4.0, stop_deep=0.2), k / NPH) for e in (-0.5, -0.3, 0.0, 0.25, 0.5, 1.0) for k in range(NPH)]
    t = time.time()
    rs = pool_map(_entry_rev, jobs, 3)
    (M.OUT / "entry_seek2.json").write_text(json.dumps(dict(n=len(rs), wall_s=round(time.time() - t), runs=rs), indent=0))
    print(f"seek2: {len(rs)} runs in {time.time() - t:.0f}s; jams {sum(r['jam'] for r in rs)}, stubs {sum(r['outcome'].startswith('stub') for r in rs)}, "
          f"left stubbed {sum(r['outcome'] == 'stub' for r in rs)}", flush=True)


def stall0_study():
    """The stall ramps at rest (0 deg), which the first cycle run skipped."""
    jobs = [(dict(spring=False), 0.0), (dict(spring=True), 0.0), (dict(spring=True, f_spring=4.0, stop_deep=0.2), 0.0)]
    rs = pool_map(_cycle, jobs, 3)
    p = M.OUT / "cycle.json"
    C = json.loads(p.read_text())
    C["runs"] = [r for r in C["runs"] if r["stall_at"] != 0.0] + rs
    C["n"] = len(C["runs"])
    p.write_text(json.dumps(C, indent=0))
    print("stall at 0 deg:", [(r["cfg"], r["steps"]) for r in rs], flush=True)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "robust":
        robust_study()
    if len(sys.argv) > 1 and sys.argv[1] == "stall0":
        stall0_study()
    if len(sys.argv) > 1 and sys.argv[1] == "seek2":
        seek2_study()
    what = sys.argv[1] if len(sys.argv) > 1 else "all"
    if what in ("entry", "all"):
        entry_study()
    if what in ("exit", "all"):
        exit_study()
    if what in ("cycle", "all"):
        cycle_study()
    if what == "quick":
        jobs = [(dict(), k / NPH, "free") for k in range(NPH)] + [(dict(spring=True), k / NPH, "free") for k in range(NPH)]
        for r in pool_map(_entry, jobs, 3):
            print(json.dumps({k: r[k] for k in ("phase", "spring", "outcome", "cd_at_stop", "cd_after_seek", "tooth_force_max_N", "tooth_force_2ms_max_N", "chain_force_max_N",
                                                "pinion_turn_deg", "auger_turn_deg", "end_tooth_force_N")}), flush=True)
