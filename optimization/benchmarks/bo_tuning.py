#!/usr/bin/env python3
"""Bayesian optimization of the three-phase policy parameters (Ax/BoTorch).

Implements the "Layer 2" recommendation from the Edison control-theory review:
policy-parameter BO over the deterministic three-phase controller.  Revised
per the Edison methods-check critique (query_out/methods_check.answer.md):

* constrained single-objective BO: scalarized accuracy/time/wear cost with
  STRICT overshoot (worst positive signed error across the trial's scenario
  doses) as an Ax outcome constraint, not a penalty folded into the cost;
* scenario seeds ROTATE per trial (fixed common random numbers over 4 doses
  caused severe overfitting: the tuned policy was worse than defaults
  out-of-sample); benchmark validation seeds (0..N) are never used here;
* timeout/stall/exception penalized explicitly;
* the tap endgame parameters are FROZEN at firmware defaults so BO tunes the
  same upstream policy the other controllers share (fairness);
* the seed trial counts toward the budget (total evaluations == --trials).

One campaign per powder on the nominal context; tuned parameters go to
results/bo_params.json for benchmark.py to evaluate on held-out seeds and the
stressed context.

Usage:  python bo_tuning.py [--trials 24] [--reps 2]
"""
from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path

from ax.service.ax_client import AxClient, ObjectiveProperties

from rig import Context, POWDERS, PowderDoserSim, Rig
from controllers import ThreePhase

HERE = Path(__file__).parent
POWDER_SET = ["salt", "lactose", "AlSi10Mg"]
TARGETS_G = [2.0, 0.3]

#: endgame (tap_tilt, taps_per_cycle, ...) frozen at firmware defaults -
#: every benchmarked controller shares the identical tap_finish policy
SPACE = [
    {"name": "t1_g", "type": "range", "bounds": [0.2, 1.0]},
    {"name": "t2_g", "type": "range", "bounds": [0.02, 0.20]},
    {"name": "bulk_tilt", "type": "range", "bounds": [20.0, 45.0]},
    {"name": "bulk_rpm", "type": "range", "bounds": [15.0, 100.0]},
    {"name": "fine_tilt", "type": "range", "bounds": [0.0, 35.0]},
    {"name": "fine_rot_deg", "type": "range", "bounds": [15.0, 180.0]},
    {"name": "fine_rpm", "type": "range", "bounds": [10.0, 60.0]},
]

#: firmware defaults = the known-safe seed point (SafeOpt-lite)
SEED_POINT = {"t1_g": 0.5, "t2_g": 0.05, "bulk_tilt": 45.0, "bulk_rpm": 55.0,
              "fine_tilt": 22.5, "fine_rot_deg": 30.0, "fine_rpm": 30.0}

FAIL_COST = 200.0          # explicit stall/timeout/exception penalty


def dose_metrics(params: dict, powder: str, seed: int,
                 target_g: float) -> tuple[float, float]:
    """(scalarized cost, signed overshoot mg) for one simulated dose.
    Cost: |error| (mg) + 0.25*time (s) + 0.05*taps (wear) + failure penalty.
    Overshoot is returned separately for the outcome constraint."""
    sim = PowderDoserSim(POWDERS[powder], Context(), seed=seed)
    rig = Rig(sim)
    ctrl = ThreePhase(**params)
    try:
        status = ctrl.run(rig, target_g)
    except Exception:
        status = "error"
        sim.set_auger_rpm(0.0)
    t = rig.t
    err_mg = (rig.true_dispensed_g() - target_g) * 1000.0
    cost = abs(err_mg) + 0.25 * t + 0.05 * rig.taps_used
    if not status.startswith("ok"):
        cost += FAIL_COST
    return cost, err_mg


def eval_params(params: dict, powder: str, reps: int,
                trial_index: int) -> dict:
    """Rotating scenario seeds per trial (never overlapping the benchmark's
    validation seeds); over_mg = WORST signed error across the scenarios,
    strict definition matching benchmark.py."""
    costs, overs = [], []
    for r in range(reps):
        for tg in TARGETS_G:
            seed = 1000 + 37 * trial_index + r
            c, e = dose_metrics(params, powder, seed=seed, target_g=tg)
            costs.append(c)
            overs.append(e)
    return {"cost": sum(costs) / len(costs), "over_mg": max(overs)}


def tune_powder(powder: str, trials: int, reps: int) -> dict:
    ax = AxClient(random_seed=0, verbose_logging=False)
    ax.create_experiment(
        name=f"three_phase_{powder}",
        parameters=SPACE,
        objectives={"cost": ObjectiveProperties(minimize=True)},
        outcome_constraints=["over_mg <= 0.0"],   # strict: true mass <= target
    )
    # seed with the known-safe firmware defaults (counts toward the budget)
    _, idx = ax.attach_trial(parameters=SEED_POINT)
    ax.complete_trial(trial_index=idx,
                      raw_data=eval_params(SEED_POINT, powder, reps, idx))
    for _ in range(trials - 1):
        params, idx = ax.get_next_trial()
        ax.complete_trial(trial_index=idx,
                          raw_data=eval_params(params, powder, reps, idx))
    best_out = ax.get_best_parameters()
    if best_out is None:       # no feasible point -> keep the safe defaults
        print(f"[{powder}] no feasible optimum; keeping firmware defaults",
              flush=True)
        return dict(SEED_POINT)
    best, values = best_out
    print(f"[{powder}] best cost {values[0]['cost']:.1f}: {best}", flush=True)
    return best


def main() -> None:
    logging.getLogger("ax").setLevel(logging.WARNING)
    ap = argparse.ArgumentParser()
    ap.add_argument("--trials", type=int, default=24)
    ap.add_argument("--reps", type=int, default=2)
    args = ap.parse_args()
    out = {}
    for powder in POWDER_SET:
        out[powder] = tune_powder(powder, args.trials, args.reps)
        (HERE / "results").mkdir(exist_ok=True)
        (HERE / "results" / "bo_params.json").write_text(
            json.dumps(out, indent=2))
    print("wrote results/bo_params.json")


if __name__ == "__main__":
    main()
