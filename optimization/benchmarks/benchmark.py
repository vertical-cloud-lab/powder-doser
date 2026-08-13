#!/usr/bin/env python3
"""Benchmark harness: every controller x powder x context x target x seed.

Runs each candidate controller against the digital twin through the fair Rig
interface, with repeats (seeds), simulated balance readings and noise, and
scores the objectives/constraints from the PR #124 problem formulation:
|mass error| (primary), dose time (secondary), tap count (wear), and the hard
asymmetric no-overshoot constraint.

Usage:
    python benchmark.py [--quick] [--methods a,b,...] [--out results.jsonl]
"""
from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path

from rig import Context, DoseOutcome, POWDERS, PowderDoserSim, Rig
from controllers import ALL_CONTROLLERS as _BASE_CONTROLLERS, TOL_G
from bangbang import BANGBANG_CONTROLLERS

# base feedback/three-phase methods plus the bang-bang family (PR #124 2026-08)
ALL_CONTROLLERS = {**_BASE_CONTROLLERS, **BANGBANG_CONTROLLERS}

HERE = Path(__file__).parent

CONTEXTS = {
    # nominal bench conditions
    "nominal": Context(temperature_c=22.0, humidity_pct_rh=30.0,
                       exposure_hours=0.0, hopper_fill_frac=0.8),
    # stressed: humid day, powder left out overnight, hopper nearly starved
    "stressed": Context(temperature_c=22.0, humidity_pct_rh=60.0,
                        exposure_hours=24.0, hopper_fill_frac=0.25),
}

POWDER_SET = ["salt", "lactose", "AlSi10Mg"]
TARGETS_G = [2.0, 0.3]
N_SEEDS = 30    # >= ~30 independent seed clusters per the methods-check review


def run_dose(method: str, ctrl, powder: str, ctx_name: str,
             target_g: float, seed: int) -> DoseOutcome:
    sim = PowderDoserSim(POWDERS[powder], CONTEXTS[ctx_name], seed=seed)
    rig = Rig(sim)
    try:
        status = ctrl.run(rig, target_g)
    except Exception as exc:  # a controller crash is a failed dose, not a crash
        status = f"error:{type(exc).__name__}"
        sim.set_auger_rpm(0.0)
    t_done = rig.t
    true_g = rig.true_dispensed_g()
    err_mg = (true_g - target_g) * 1000.0
    return DoseOutcome(
        method=method, powder=powder, context_name=ctx_name, target_g=target_g,
        dispensed_g=round(true_g, 5), error_mg=round(abs(err_mg), 3),
        signed_error_mg=round(err_mg, 3), overshoot=err_mg > 0.0,
        within_tol=abs(err_mg) <= TOL_G * 1000.0, time_s=round(t_done, 1),
        taps=rig.taps_used, auger_rev=round(rig.auger_rev_used, 2),
        status=status, seed=seed)


def make_controller(method: str, tuned_params: dict | None = None):
    if method.startswith("bo_"):
        base = method[3:]
        params = dict(tuned_params or {})
        return ALL_CONTROLLERS[base](**params)
    return ALL_CONTROLLERS[method]()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--quick", action="store_true", help="2 seeds, salt only")
    ap.add_argument("--methods", default=",".join(ALL_CONTROLLERS))
    ap.add_argument("--out", default=str(HERE / "results" / "results.jsonl"))
    ap.add_argument("--bo-params", default=str(HERE / "results" / "bo_params.json"),
                    help="per-powder tuned ThreePhase params; adds bo_three_phase")
    args = ap.parse_args()

    methods = [m for m in args.methods.split(",") if m]
    powders = ["salt"] if args.quick else POWDER_SET
    seeds = range(2) if args.quick else range(N_SEEDS)
    contexts = ["nominal"] if args.quick else list(CONTEXTS)

    bo_params = {}
    bo_path = Path(args.bo_params)
    if bo_path.exists() and not args.quick:
        bo_params = json.loads(bo_path.read_text())
        if "bo_three_phase" not in methods:
            methods = methods + ["bo_three_phase"]

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    results = []
    with out_path.open("w") as fh:
        for powder in powders:
            for ctx_name in contexts:
                for target in TARGETS_G:
                    for method in methods:
                        for seed in seeds:
                            if method == "bo_three_phase":
                                ctrl = make_controller(method,
                                                       bo_params.get(powder))
                            else:
                                ctrl = make_controller(method)
                            o = run_dose(method, ctrl, powder, ctx_name,
                                         target, seed)
                            results.append(o)
                            fh.write(json.dumps(asdict(o)) + "\n")
                            fh.flush()
                    done = [r for r in results
                            if (r.powder, r.context_name, r.target_g)
                            == (powder, ctx_name, target)]
                    print(f"[{powder}/{ctx_name}/{target}g] "
                          + "  ".join(
                              f"{m}: {_cell(done, m)}"
                              for m in methods), flush=True)
    print(f"\nwrote {len(results)} doses -> {out_path}")
    summarize(results)


def _cell(rows, method):
    rows = [r for r in rows if r.method == method]
    if not rows:
        return "-"
    import statistics
    med = statistics.median(r.error_mg for r in rows)
    t = statistics.median(r.time_s for r in rows)
    over = sum(r.overshoot for r in rows)
    return f"{med:.1f}mg/{t:.0f}s/ov{over}"


def summarize(results) -> None:
    import statistics
    print(f"\n{'method':<16}{'n':>4}{'med|e|mg':>10}{'p95|e|mg':>10}"
          f"{'tol%':>7}{'over%':>7}{'med t(s)':>10}{'med taps':>10}{'fail':>6}")
    for method in sorted({r.method for r in results}):
        rows = [r for r in results if r.method == method]
        errs = sorted(r.error_mg for r in rows)
        p95 = errs[min(len(errs) - 1, int(0.95 * len(errs)))]
        print(f"{method:<16}{len(rows):>4}"
              f"{statistics.median(errs):>10.2f}{p95:>10.1f}"
              f"{100 * sum(r.within_tol for r in rows) / len(rows):>6.0f}%"
              f"{100 * sum(r.overshoot for r in rows) / len(rows):>6.0f}%"
              f"{statistics.median(r.time_s for r in rows):>10.1f}"
              f"{statistics.median(r.taps for r in rows):>10.0f}"
              f"{sum(not r.status.startswith('ok') for r in rows):>6}")


if __name__ == "__main__":
    main()
