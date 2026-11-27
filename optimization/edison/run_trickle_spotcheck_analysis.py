#!/usr/bin/env python3
"""Submit an Edison ANALYSIS task: spot-check of the 2026-08-21 write-up on why
the Kalman filter is used inside `trickle_tap` and what actually prevents
overshoot (issue #123 / PR #124, comment 5374457558).

Uploads the claim list (spotcheck_claims.md), the bang-bang controllers and the
shared endgame, the diagnostic that produced the numbers plus its raw output,
and the digital twin whose lip/balance physics the conclusions lean on. Writes
query_out/trickle_spotcheck.task.json; fetch with
    fetch_analysis_result.py trickle_spotcheck [wait]
"""
import json
import os
from pathlib import Path

from edison_client import EdisonClient, JobNames
from edison_client.models.app import TaskRequest

HERE = Path(__file__).parent
ROOT = HERE.parent
OUT = HERE / "query_out"
OUT.mkdir(exist_ok=True)

NAME = "trickle_spotcheck"

FILES = [
    HERE / "spotcheck_claims.md",
    ROOT / "benchmarks" / "bangbang.py",
    ROOT / "benchmarks" / "controllers.py",
    ROOT / "benchmarks" / "diag_trickle_stages.py",
    ROOT / "benchmarks" / "results" / "diag_trickle_stages.txt",
    ROOT / "simulation" / "powder_sim.py",
]


def _api_key() -> str:
    key = os.environ.get("EDISON_API_KEY") or os.environ.get("EDISON_PLATFORM_API_KEY")
    if not key:
        raise SystemExit(
            "Edison API key is not set (EDISON_API_KEY / EDISON_PLATFORM_API_KEY)."
        )
    return key


QUERY = """Spot-check an engineering analysis of a benchtop gravimetric powder \
doser (auger feeder + solenoid tapper + tilt servo + A&D HR-100A balance at \
~10.4 Hz; dose targets 0.3-2.0 g; tolerance +/-5 mg; overshoot is a HARD \
ASYMMETRIC constraint because powder cannot be removed from the vial).

The uploaded spotcheck_claims.md states twelve numbered claims (C1-C12) from a \
write-up answering the question "why is a Kalman filter used during the low-rate \
trim stage, and how does that avoid overshoot despite the rate estimate being \
noisy at small flows?". The other uploads are the artifacts those claims are \
based on:

* bangbang.py - the 3-state Kalman filter (MassRateLagKF: state [true mass, \
rate, balance internal reading], H = [0,0,1] so the balance frame measures the \
LAGGED state and the estimate of true mass is lag-free; R switched between \
0.5 mg quiet and 8 mg while actuating, keyed to the controller's own actuation \
state; predict every 0.2 s tick, update only on a fresh balance frame) and the \
bang-bang controllers, including trickle_tap() whose cutoff rule is \
m_hat + r_hat*tau + k_sigma*sigma_pred >= target - margin.
* controllers.py - the shared at-rest tap endgame (tap -> settle -> STABLE \
reading -> repeat) and the grey-box committed-lookahead helper.
* diag_trickle_stages.py + diag_trickle_stages.txt - the instrumented \
diagnostic and its raw output: stage-by-stage mass at each handoff, the \
decomposition of the cutoff decision into its three terms, and an ablation grid \
(remove k*sigma, remove the fixed margin, replace the filtered rate with a \
rectified finite difference, remove the Kalman filter entirely).
* powder_sim.py - the digital twin the numbers come from (compartment model: \
hopper -> revolution-domain screw transport -> lip reservoir with a smooth \
tilt-dependent drain plus a marked avalanche point process -> jittered free \
fall -> vial, with a sample-and-hold balance model, regime-switching vibration \
noise, feed-factor drift, and three-state flowing/starved/blocked hazards). \
Feed factors and tilt gains are fitted to real dosing runs; the lip drain law, \
afterflow and balance lag are PROVISIONAL.

Please work through C1-C12 in order and, for each: state whether the claim is \
SUPPORTED, PARTIALLY SUPPORTED, or WRONG given the uploaded code and numbers; \
give the specific technical reason; and give the concrete correction (name the \
file/function/line and the change). Pay particular attention to:

1. Whether attributing safety to "term magnitude in a threshold rule" (C1) is \
sound, and whether the ablations supply a valid counterfactual given that the \
rate estimate feeds BOTH the stopping statistic and the rate-PI feedback loop \
(C5) - i.e. is this a confounded ablation, and what is the right design \
(counterfactual replay on fixed trajectories, common random numbers, paired \
statistics)?
2. The claim that the k*sigma term is "self-correcting" with observed data \
quality (C3). For a linear Kalman filter the covariance follows a deterministic \
Riccati recursion independent of the realized innovations, so we believe this is \
wrong as stated; please confirm/refute, say what sigma_pred actually adapts to \
in this implementation, and say what an innovation-adaptive scheme (adaptive \
Kalman filtering / covariance matching / NIS-based consistency monitoring) would \
have to look like to deliver the claimed behaviour.
3. Whether a rate-based continuum description is defensible at the measured \
cutoff flow of 0.042 g/s given bench evidence that discharge is a marked point \
process (salt, 45 degree auger increments: mean 6.4 mg, sd 15.9 mg, n = 64), and \
whether there is a principled criterion for where "rate" stops being meaningful \
(C4).
4. Estimator correctness (C11): post-update clamping of a state to be \
non-negative and its effect on the covariance and hence on sigma_pred; near-zero \
process noise on the balance-lag state and numerical conditioning; whether \
3-state lag deconvolution is the standard way to invert a known instrument time \
constant or whether a better-conditioned formulation exists; and the sensitivity \
of every conclusion to tau_bal (twin uses 0.7 s, our bench drop-weight tests \
suggest ~0.16 s).
5. Whether the causal story survives if the twin's provisional passive lip drain \
(median +26 mg during a 1.2 s post-cutoff settle at 20 deg tilt) is wrong - our \
own bench data shows settling complete in 0.7-1.5 s with no creep past ~2 s \
after a halt (C6). Name the minimal discriminating experiment, and cite any \
published evidence on post-halt discharge from an inclined auger/tube outlet.
6. Whether the recommended fixes are the right priorities (C8) and what is \
missing, in light of the gravimetric filling / loss-in-weight feeder / \
pharmaceutical continuous-manufacturing literature: standard practice for \
bulk-to-dribble handover, cutoff (in-flight/"free fall") compensation in \
checkweighing and gravimetric filling, and the standard metrics for a \
one-sided-constrained dosing problem (C7).

Finish with C12: is the headline answer to the project member correct, partially \
correct, or misleading, and what is the single most important correction? Then \
give a ranked list of the 3-5 changes that would most improve the controller and \
the analysis, separating (a) changes justified by the uploaded evidence from \
(b) changes that need a bench measurement first, naming the measurement."""


def main() -> None:
    client = EdisonClient(api_key=_api_key())
    file_ids = []
    for path in FILES:
        fid = client.upload_file(path, name=path.name,
                                 description=f"powder-doser trickle spot-check: {path.name}")
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
