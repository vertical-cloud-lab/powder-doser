#!/usr/bin/env python3
"""Submit Edison ANALYSIS task #2: accuracy check of the controller
implementations and benchmark results (issue #123 / PR #124).

Uploads the v2 digital twin, the controller implementations, the benchmark
harness/BO tuner, and the results summary, and asks Edison to check the
methods for correctness against the literature and to flag anything that
would invalidate the comparison. Writes query_out/methods_check.task.json;
fetch with fetch_analysis_result.py methods_check [wait]."""
import json
import os
from pathlib import Path

from edison_client import EdisonClient, JobNames
from edison_client.models.app import TaskRequest

HERE = Path(__file__).parent
ROOT = HERE.parent
OUT = HERE / "query_out"
OUT.mkdir(exist_ok=True)

NAME = "methods_check"

FILES = [
    ROOT / "simulation" / "powder_sim.py",
    ROOT / "benchmarks" / "rig.py",
    ROOT / "benchmarks" / "controllers.py",
    ROOT / "benchmarks" / "benchmark.py",
    ROOT / "benchmarks" / "bo_tuning.py",
    ROOT / "benchmarks" / "results" / "summary.md",
]


def _api_key() -> str:
    key = os.environ.get("EDISON_API_KEY") or os.environ.get("EDISON_PLATFORM_API_KEY")
    if not key:
        raise SystemExit(
            "Edison API key is not set (EDISON_API_KEY / EDISON_PLATFORM_API_KEY)."
        )
    return key


QUERY = """Follow-up to a previous analysis in which you critiqued our powder-doser \
digital twin as a benchmark instrument (compartment model: hopper -> 3-cell \
revolution-domain screw transport -> lip reservoir -> jittered free fall -> vial, \
with a sample-and-hold 10 Hz balance model, split RNG streams, OU feed-factor \
drift + screw harmonics, hurdle/Beta tap model, marked avalanche lip discharge, \
three-state flowing/starved/blocked hazards, sorption-equilibrium moisture, \
balance bias/drift and colored actuation vibration). powder_sim.py v2 (uploaded) \
implements your "required before any ranking claim" list; controllers interact \
only through rig.py's sensor surface (balance samples + own commanded state).

We then benchmarked five controller families on this twin (controllers.py, \
benchmark.py, bo_tuning.py, results in summary.md, all uploaded):

1. three_phase - the deterministic firmware baseline (bulk increments / fine \
increments / tap-until-tolerance), firmware-default parameters.
2. three_phase_vel - same with continuous-rotation bulk + anticipation threshold.
3. rate_pi_kf - continuous feed with a rate-PI loop on a 2-state (mass, rate) \
Kalman filter (filterpy) with regime-switching R keyed to the controller's own \
actuation state, input-aware predict (B matrix uses an EWMA feed factor), rate \
setpoint tapered as (remaining - margin)/(2*L(tilt)), and predictive cutoff on \
committed mass m + r*L(tilt), where L(tilt) is a grey-box lip-holdup lookahead \
~ 1/(1.2*steepness^2*0.85) + 0.85 s; then a shared tap-until-tolerance endgame.
4. dual_ukf - unscented KF (filterpy) over [mass, rate, feed_factor] with \
random-walk feed factor (joint state-parameter estimation), feedforward speed \
u = r_sp/ff, same taper/cutoff/endgame.
5. mpc - short-horizon (16 x 0.25 s) constrained linear MPC (cvxpy/OSQP) on \
m+ = m + r dt, r+ = r + a(ff*u - r), with hard constraints m + L*r <= target - \
margin (committed-mass no-overshoot), a future-input volumetric budget \
ff_hi * dt * cumsum(u) <= remaining (arching guard), input slew limits, and a \
planned-rate cap; feed factor from an EWMA of (m + committed correction)/revs; \
same tap endgame.
6. bo_three_phase - Ax/BoTorch (qLogNEI default) tuning of 9 three-phase policy \
parameters per powder on the nominal context (24 trials, firmware defaults as a \
safe seed trial), scalarized cost |err|_mg + 0.25*t_s + 0.05*taps + asymmetric \
overshoot penalty, then evaluated on held-out stressed contexts and seeds.

The benchmark grid: 3 powders (salt, cohesive lactose, free-flowing AlSi10Mg) x \
2 contexts (nominal; stressed = 60 %RH, 24 h exposure, 25 % hopper fill) x 2 \
targets (2.0 g, 0.3 g) x 10 seeds. Objectives: |mass error| after settle \
(tolerance +/-5 mg), dose time, tap count (wear); hard asymmetric no-overshoot \
constraint scored on true vial mass.

Please check the IMPLEMENTATIONS and the ANALYSIS for correctness:

A. Estimator correctness: is the switching-R KF implemented correctly (R keyed \
to self-reported actuation, input-aware predict via B = [0, a*ff]); is the UKF \
process/measurement split sound; are there standard corrections we missed \
(e.g. handling the 10 Hz sample-and-hold - we currently update the filters at \
their own 0.2-0.25 s period; is treating held samples as fresh measurements a \
bias, and should we use the balance tick timestamps instead)?

B. MPC formulation: is the committed-mass constraint m + L r <= target a \
legitimate stand-in for an unmodelled transport/lip state; is the volumetric \
future-input budget sound; known better practice for asymmetric no-overshoot \
(e.g. constraint softening with exact penalty, tube MPC, offset-free MPC with \
disturbance estimation) that would be worth the effort here?

C. BO setup: is a scalarized objective with an asymmetric penalty + safe seed \
trial a reasonable stand-in for constrained BO (qNEHVI / SafeOpt) at 24 trials; \
should the overshoot penalty instead be an Ax outcome constraint; is per-powder \
tuning with stressed-context holdout the right generalization test?

D. Benchmark design: with 10 seeds per cell, what is the right way to report \
paired uncertainty (per your prior advice on paired controller differences and \
common random numbers given our split RNG streams); any obvious statistical \
mistakes in summary.md's aggregation (medians over pooled cells)?

E. Fairness: any remaining channels through which a method class is favored \
(e.g. all-methods-share tap_finish; the grey-box L(tilt) using the same 1.2 \
coefficient family as the plant's drain law; MPC's model matching the plant's \
integrator structure)?

F. Verdict: given summary.md's numbers, which conclusions are supported and \
which are artifacts; what 2-3 changes would most improve the study's validity \
before we report rankings to the project?

Be concrete: name the file/function and the specific change."""


def main() -> None:
    client = EdisonClient(api_key=_api_key())
    file_ids = []
    for path in FILES:
        fid = client.upload_file(path, name=path.name,
                                 description=f"powder-doser benchmark: {path.name}")
        print(f"uploaded {path.name}: {fid}", flush=True)
        file_ids.append(str(fid))
    task = TaskRequest(name=JobNames.ANALYSIS, query=QUERY)
    tid = client.create_task(task, files=file_ids)
    print(f"{NAME}: trajectory_id {tid}", flush=True)
    (OUT / f"{NAME}.task.json").write_text(
        json.dumps(
            {"trajectory_id": str(tid), "job": str(JobNames.ANALYSIS),
             "files": file_ids, "query": QUERY},
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
