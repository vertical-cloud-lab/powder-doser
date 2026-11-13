#!/usr/bin/env python3
"""Submit an Edison ANALYSIS task critiquing the powder-doser digital twin
(issue #123 / PR #124, sgbaird 2026-07-25: "first starting with defining a
fairly reasonable 'simulation' function ... Send it to Edison, fetch and apply
feedback").

Uploads optimization/simulation/powder_sim.py (plus its test and README) and
asks for a concrete, implementable critique of the model as a *benchmark
function* for comparing dosing control methods. Writes
query_out/sim_critique.task.json; fetch with
fetch_analysis_result.py sim_critique [wait]."""
import json
import os
from pathlib import Path

from edison_client import EdisonClient, JobNames
from edison_client.models.app import TaskRequest

HERE = Path(__file__).parent
SIM = HERE.parent / "simulation"
OUT = HERE / "query_out"
OUT.mkdir(exist_ok=True)

NAME = "sim_critique"


def _api_key() -> str:
    key = os.environ.get("EDISON_API_KEY") or os.environ.get("EDISON_PLATFORM_API_KEY")
    if not key:
        raise SystemExit(
            "Edison API key is not set (EDISON_API_KEY / EDISON_PLATFORM_API_KEY)."
        )
    return key


QUERY = """We are building an open-source, low-cost powder doser for gravimetric \
metering of dry powders (metal AM feedstocks such as AlSi10Mg, 316L, silicon; salt \
and lactose as surrogates) inside a self-driving-lab alloy-discovery loop. Hardware: \
an Archimedean auger in a tube driven by a stepper (44:20 gear), a solenoid tapper \
striking the tube, servo-controlled tilt of the whole assembly (mounting-plate 0-45 \
deg; 45 = rig "vertical"), dispensing into a vial on an A&D HR-100A balance (0.1 mg \
readability, ~1 s settling; readings during actuation are vibration-corrupted). \
Empirical observations we must reproduce: (a) rotating or tapping at steeper tilt \
dispenses far more per action; (b) a tap immediately after a rotation dispenses more \
than repeated taps alone (an unobserved "lip reservoir" of loose powder near the \
tube exit that rotation replenishes and taps deplete); (c) cohesive powders bridge \
("rat-hole") over the hopper throat and discharge in clumps.

The uploaded file powder_sim.py is our control-oriented stochastic compartment-model \
"digital twin": hopper -> auger conveying (fill-, tilt-, cohesion-, densification- \
dependent feed factor, g/rev) -> lip reservoir (gravity drain + avalanche overflow \
+ tap ejection) -> 0.15 s free-fall -> vial; first-order balance model with \
regime-switching noise and an A&D-style stable flag; context variables (humidity x \
exposure -> moisture -> cohesion; temperature; hopper fill); Poisson clump \
discharge; stochastic arching. test_powder_sim.py contains its behavioral checks \
and README.md the rationale.

PURPOSE: this simulator is about to be used as the common BENCHMARK FUNCTION for an \
exhaustive simulation comparison of candidate dosing controllers - (i) the current \
deterministic three-phase policy (bulk / fine increments / tap-until-tolerance), \
(ii) a rate-PI trickle phase with predictive cutoff driven by a 2-state \
switching-covariance Kalman filter, (iii) a dual UKF additionally estimating the \
feed factor online, (iv) short-horizon constrained MPC on a grey-box Hammerstein \
model, and (v) Bayesian optimization (Ax/BoTorch) of the three-phase policy \
parameters - under repeats, multiple powders, and randomized contexts, with \
objectives |mass error| and dose time, tap-count wear regularization, and \
no-overshoot as a hard asymmetric constraint.

Please CRITIQUE THE SIMULATOR AS A SCIENTIFIC INSTRUMENT for that benchmark, and be \
concrete and implementable (we will directly edit the code from your answer):

1. Structure: is the compartment decomposition (hopper / screw / lip / in-flight / \
balance) adequate for screw-feeder micro-dosing, or is a first-order screw \
transport delay (powder residing IN the flights) a required extra state? What does \
the loss-in-weight feeder and volumetric micro-feeding literature say about minimum \
model structure for control design?

2. Functional forms and magnitudes, item by item: fill-level exponent \
(min(1,fill/0.30)^0.7), tilt gain (0.50+0.90*steepness with steepness = \
sin(tilt)/sin(45)), cohesion loss (1-0.40*coh), densification (1+0.12*packing), \
tap ejection fraction 0.35*(0.20+0.80*steepness)*(1-0.55*coh) of lip mass per tap, \
lip capacity and drain-rate laws, per-substep multiplicative conveying noise (10 % \
sd), Poisson clump size law, arching probability law, moisture-uptake law, balance \
first-order lag + regime-switching Gaussian noise (0.15 mg quiet / 8 mg disturbed). \
Which of these are inconsistent with published screw-feeder / powder-rheology data, \
and what forms or ranges would you substitute?

3. Missing physics that could CHANGE THE RANKING of the five controllers above - \
e.g. screw transport delay / dead volume (would penalize tight feedback less or \
more?), stick-slip or avalanche statistics at the lip, tap-induced flooding/flushing \
of fine powders, electrostatics for <50 um metal powders, balance drift/tare error, \
discrete balance update rate (we currently model continuous first-order settling; \
the real HR-100A streams ~5-10 Hz over RS-232), servo tilt vibration coupling. \
Rank additions by (impact on controller ranking) / (implementation effort).

4. Stochasticity: are the noise sources (multiplicative conveying noise, Poisson \
clumps, arching Bernoulli, balance noise) the right FAMILIES with the right \
regime-dependence for a benchmark, and are any correlations we ignore (e.g. \
autocorrelated feed-factor drift within a dose) important for filter/MPC \
evaluation?

5. Fairness: any modelling choices that would systematically bias the comparison \
toward or against a controller class (e.g. perfectly-known tap impulse timing \
favoring MPC; instantaneous rate telemetry that no real sensor provides)?

6. A prioritized, concrete list of the changes you would actually make before \
trusting benchmark conclusions, each with the specific equation/parameter edit.

Where possible ground recommendations in published loss-in-weight / screw feeder / \
powder micro-dosing models (Fathollahi, Li, Bascone, Hopkins etc.) and powder \
rheology; give numbers, not generalities."""


def main() -> None:
    client = EdisonClient(api_key=_api_key())
    file_ids = []
    for path in (SIM / "powder_sim.py", SIM / "test_powder_sim.py", SIM / "README.md"):
        fid = client.upload_file(path, name=path.name,
                                 description=f"powder-doser digital twin: {path.name}")
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
