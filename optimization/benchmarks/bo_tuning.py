#!/usr/bin/env python3
"""Bayesian optimization of the three-phase policy parameters (Ax/BoTorch).

Implements the "Layer 2" recommendation from the Edison control-theory review:
policy-parameter BO over the deterministic three-phase controller, with the
scalarized objective |mass error| + time + wear and overshoot as a penalty
(the pragmatic SafeOpt stand-in: conservative bounds + a known-safe seed
point).  One small campaign per powder on the nominal context; tuned
parameters are written to results/bo_params.json for benchmark.py to evaluate
(including on held-out stressed contexts the optimizer never saw).

Usage:  python bo_tuning.py [--trials 24] [--reps 2]
"""
from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path

from ax.service.ax_client import AxClient, ObjectiveProperties

from rig import Context, POWDERS, PowderDoserSim, Rig
from controllers import ThreePhase, TOL_G

HERE = Path(__file__).parent
POWDER_SET = ["salt", "lactose", "AlSi10Mg"]
TARGETS_G = [2.0, 0.3]

SPACE = [
    {"name": "t1_g", "type": "range", "bounds": [0.2, 1.0]},
    {"name": "t2_g", "type": "range", "bounds": [0.02, 0.20]},
    {"name": "bulk_tilt", "type": "range", "bounds": [20.0, 45.0]},
    {"name": "bulk_rpm", "type": "range", "bounds": [15.0, 100.0]},
    {"name": "fine_tilt", "type": "range", "bounds": [0.0, 35.0]},
    {"name": "fine_rot_deg", "type": "range", "bounds": [15.0, 180.0]},
    {"name": "fine_rpm", "type": "range", "bounds": [10.0, 60.0]},
    {"name": "taps_per_cycle", "type": "range", "bounds": [1, 4]},
    {"name": "tap_tilt", "type": "range", "bounds": [0.0, 20.0]},
]

#: firmware defaults = the known-safe seed point (SafeOpt-lite)
SEED_POINT = {"t1_g": 0.5, "t2_g": 0.05, "bulk_tilt": 45.0, "bulk_rpm": 55.0,
              "fine_tilt": 22.5, "fine_rot_deg": 30.0, "fine_rpm": 30.0,
              "taps_per_cycle": 2, "tap_tilt": 0.0}


def dose_cost(params: dict, powder: str, seed: int, target_g: float) -> float:
    """Scalarized cost: |error| (mg) + 0.25*time (s) + 0.05*taps (wear) +
    a large asymmetric penalty for violating the no-overshoot constraint."""
    sim = PowderDoserSim(POWDERS[powder], Context(), seed=seed)
    rig = Rig(sim)
    ctrl = ThreePhase(**params)
    try:
        ctrl.run(rig, target_g)
    except Exception:
        sim.set_auger_rpm(0.0)
    t = rig.t
    err_mg = (rig.true_dispensed_g() - target_g) * 1000.0
    cost = abs(err_mg) + 0.25 * t + 0.05 * rig.taps_used
    if err_mg > TOL_G * 1000.0:
        cost += 150.0 + 2.0 * err_mg      # asymmetric overshoot penalty
    return cost


def eval_params(params: dict, powder: str, reps: int) -> float:
    costs = [dose_cost(params, powder, seed=100 + r, target_g=tg)
             for r in range(reps) for tg in TARGETS_G]
    return sum(costs) / len(costs)


def tune_powder(powder: str, trials: int, reps: int) -> dict:
    ax = AxClient(random_seed=0, verbose_logging=False)
    ax.create_experiment(
        name=f"three_phase_{powder}",
        parameters=SPACE,
        objectives={"cost": ObjectiveProperties(minimize=True)},
    )
    # seed with the known-safe firmware defaults
    _, idx = ax.attach_trial(parameters=SEED_POINT)
    ax.complete_trial(trial_index=idx,
                      raw_data={"cost": eval_params(SEED_POINT, powder, reps)})
    for _ in range(trials):
        params, idx = ax.get_next_trial()
        ax.complete_trial(trial_index=idx,
                          raw_data={"cost": eval_params(params, powder, reps)})
    best, values = ax.get_best_parameters()
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
