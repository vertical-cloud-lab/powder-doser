#!/usr/bin/env python3
"""Submit the Whitehead / single-run calibration Edison query (PR #124, submit-only).

sgbaird asked (PR #124, 2026-10-07), following XZaitzeff's conversation with
Jared Whitehead (BYU Math) about data assimilation: fit the in-flight mass term
and the feed factor for a new powder from a single run, using autodiff (e.g.
JAX) with a prior that keeps the estimates near a reasonable starting guess;
store the per-powder values and reuse them, which would also simplify a
"calibrate a new powder" procedure for other labs. Gotcha raised in the same
comment: #140 found the feed factor drifting ~1.8x over two days for the same
powder, so a stored value may work better as a prior than as a constant.

"Run an Edison search related to Jared Whitehead's research and how it could
apply here."  Writes query_out/whitehead_da.task.json.  Fetch with
fetch_whitehead_da_result.py (high-effort; allow ~20-40 min)."""
import json
import os
from pathlib import Path

from edison_client import EdisonClient, JobNames
from edison_client.models.app import TaskRequest

HERE = Path(__file__).parent
OUT = HERE / "query_out"
OUT.mkdir(exist_ok=True)
NAME = "whitehead_da"


def _api_key() -> str:
    key = os.environ.get("EDISON_API_KEY") or os.environ.get("EDISON_PLATFORM_API_KEY")
    if not key:
        raise SystemExit(
            "Edison API key is not set (EDISON_API_KEY / EDISON_PLATFORM_API_KEY)."
        )
    return key


RIG_CONTEXT = """Context: we are building an open-source, low-cost powder doser for \
gravimetric dosing of dry powders (salt as the development surrogate; ultimately \
metal additive-manufacturing feedstocks such as AlSi10Mg, plus food/pharma powders) \
inside a self-driving-lab loop. Hardware: an Archimedean auger in a tube driven by a \
stepper motor (44:20 gear), a solenoid tapper that strikes the tube, and a servo that \
tilts the whole assembly (0-70 degrees), dispensing into a cup on an A&D HR-100A \
analytical balance (102 g capacity, 0.1 mg readability). The balance is mechanically \
isolated from the doser; at its factory response setting it emits a new datum only \
every ~197 ms (5.1 Hz), and drop-weight step tests show a first-order response with \
time constant tau_bal ~ 0.16 s (R^2 > 0.995, independent of mass and drop height).

Current controller ("bang-bang" bulk + trim): dispense at full rate while a 3-state \
Kalman filter (true cup mass m, deposition rate r, lagged balance reading b; the \
balance observes b) runs on the balance stream; halt the auger when the predicted \
settled mass m_hat + AF0 + tau_af * r_hat (+ k * sigma) reaches target minus a guard; \
then a slow increment/tap trim closes the remaining tens of mg on settled readings. \
Two per-powder quantities dominate this predictor:

(1) FEED FACTOR phi (g per auger revolution, i.e. the volumetric-feeder "feed factor"). \
For salt it is ~0.14-0.23 g/rev at working tilts; across 8 powders (salt, calcium \
lactate, AlSi10Mg, xanthan gum, rice flours, sodium alginate, CMC) it spans <0.03 to \
~0.23 g/rev. It is NOT stable: flow fell 3.6x within one session as the hopper drew \
down; identical interleaved 1-rev flow-check probes within one session ranged \
0.033-0.105 g/rev (excluding an empty first probe); and replaying recorded doses \
through our state-space model, ONE fitted feed-factor scale cut the trajectory RMS \
error from 366 mg to 22 mg - but for the same rig and same salt the fitted scale was \
~1.65-1.83x the value characterized two days earlier. Hopper fill level is not \
measured (the loaded tube exceeds the \
balance range), so fill level and powder re-packing/consolidation are confounded and \
are our prime suspects for that drift.

(2) IN-FLIGHT / AFTERFLOW MASS: powder already committed when the auger halts (in the \
screw, on the tube lip, in free fall) that lands after the halt. A stop-response \
sweep at 15-75 rpm gave post-halt arrival A ~ AF0 + tau_af * flow with AF0 ~ 14.7 mg \
and tau_af ~ 0.30 s (R^2 = 0.90 on the four per-rpm means but only 0.18 per trial). \
In closed-loop doses at one nominal condition, A ranged 30-159 mg (sd 34 mg); flow at \
halt explained 18% of its variance and adding run duration raised that to 43% \
(shorter runs afterflow more - a lip/screw inventory or history effect). Fitting the \
same law to different datasets gave tau_af = 0.28 s, 1.02 s, ~1.07 s, and ~0 (with \
AF0 ~ 7 mg), so (AF0, tau_af) are not stable constants either.

Prior work in this project: an earlier literature review of data assimilation for \
this rig recommended a within-dose dual unscented Kalman filter estimating at most \
1-2 parameters (feed factor first), dose-to-dose batch MLE/MAP refits of the model \
from dose logs, interacting-multiple-model filtering for jump/arching regimes, and \
deferring "DA-estimated latent context for Bayesian optimization" until the estimates \
prove stable. A digital twin (compartment model: hopper -> screw hold-up -> lip \
reservoir -> free fall -> cup -> first-order balance) is available for testing \
estimators against ground truth."""


QUESTION = """
NEW PROPOSAL TO EVALUATE. After a conversation with Prof. Jared P. Whitehead \
(Brigham Young University, Department of Mathematics) about data assimilation, a \
team member proposed: fit the in-flight mass term (AF0, tau_af) and the feed factor \
phi for a NEW powder from a SINGLE calibration run, using automatic differentiation \
(e.g. JAX) through a model of the run, with a prior that keeps the estimates near a \
reasonable starting guess (i.e. a MAP / regularized fit); then store the per-powder \
values and reuse them, which would make "calibrate a new powder" a simple, portable \
procedure that other labs could run. The known gotcha is the ~1.8x two-day drift of \
phi for the same material, suggesting a stored value should act as a PRIOR for the \
next session rather than as a constant.

Please (with citations throughout):

Q1. Whitehead's research and what transfers. Identify and summarize Jared P. \
Whitehead's research relevant to this problem - in particular (a) parameter learning \
with nudging / continuous data assimilation (e.g. the Carlson-Hudson-Larios \
algorithm and its extensions: Carlson, Hudson, Larios, Martinez, Ng & Whitehead on \
dynamically learning parameters of chaotic systems from partial observations; Pachev, \
Whitehead & McQuarrie 2022 on concurrent multi-parameter learning for the \
Kuramoto-Sivashinsky equation; Newey, Whitehead & Carlson 2024 "Model discovery on \
the fly using continuous data assimilation", which recasts CHL as Newton's method and \
finds Levenberg-Marquardt better for multiple parameters; and any comparisons of \
these deterministic nudging-based schemes with stochastic/ensemble parameter recovery) \
and (b) Bayesian inversion \
in small-data, high-uncertainty settings (the historical tsunami / earthquake \
reconstructions with MCMC over expensive forward models and the open-source \
tsunamibayes package) - plus any other of his work on stochastic forcing, model \
error, or identifiability that bears on this. For each line of work: what are its \
assumptions (dissipative dynamics, synchronization of a nudged model, observation \
density, Gaussian errors, well-specified model), and which of them survive \
translation to a LOW-DIMENSIONAL, HYBRID (start/stop, threshold-triggered), \
STOCHASTIC granular-flow system observed through ONE scalar, lagged, 5 Hz sensor?

Q2. Method fit. Is "single-run MAP fit with autodiff and a Gaussian prior" \
equivalent to strong- or weak-constraint 4D-Var with a background term / Tikhonov \
regularization, and when is its Laplace approximation an adequate posterior? \
Compare it, for a single 30-120 s run (~150-600 balance frames, 1-5 halts), against: \
(i) online nudging/CDA-based parameter updates during the run (Whitehead-style); \
(ii) a dual or augmented-state UKF; (iii) full Bayesian posterior sampling (MCMC/HMC, \
as in the tsunami work); (iv) differentiating a Kalman-filter marginal likelihood \
(prediction-error method) instead of a deterministic simulator. Which gives the most \
trustworthy phi and afterflow estimates WITH calibrated uncertainty, given jump noise \
(slug/clump arrivals, occasional arching) and model error?

Q3. Identifiability and experimental design of the single run. phi is observable \
from flow segments, but (AF0, tau_af) only at halts, and our data say afterflow also \
depends on run history (duration, lip inventory). How should ONE calibration run be \
designed (number/spacing of start-stop segments, rate levels, segment durations, \
taps, tilt) so the target parameters are jointly identifiable - Fisher-information or \
Bayesian optimal experimental design, D-optimal input design, sloppiness / profile \
likelihood analysis? How many parameters can realistically be learned concurrently, \
and how do we detect when they are compensating for structural model error (e.g. \
the missing history dependence) rather than measuring something physical?

Q4. Priors, drift and storage. If stored per-powder values become priors, how should \
the prior variance be set and inflated over time - hierarchical Bayesian models \
(population/powder/session levels), random-walk parameter models with variance \
growing with elapsed time or dispensed mass, empirical Bayes across a multi-powder \
database, or priors predicted from measured material properties (bulk/tapped density, \
Hausner ratio, PSD, moisture)? Separately: what does the screw / loss-in-weight \
feeder literature say about why the feed factor of the SAME material drifts by \
1.5-2x over hours to days (hopper fill level / head pressure, consolidation and \
densification, moisture uptake by hygroscopic powders such as NaCl, temperature, \
attrition, electrostatics, refill events), which of these are predictable from \
loggable covariates, and what feed-factor-vs-fill-level calibration practice (e.g. \
the feed-factor decay curves used in pharmaceutical loss-in-weight feeders) we \
should copy so that drift becomes a modelled covariate rather than unexplained \
noise?

Q5. Tooling and a portable protocol. Recommend open-source implementations (JAX: \
optax/optimistix/jaxopt for MAP, numpyro/blackjax for Laplace/HMC, diffrax for \
differentiable ODEs, dynamax for differentiable Kalman filters and parameter \
learning; any published code from Whitehead's group, e.g. tsunamibayes or CDA \
parameter-learning code) and the pitfalls of differentiating through hybrid or \
discontinuous dynamics (halts, threshold-triggered stops, Poisson clump arrivals) \
with standard remedies. Then propose what a minimal, portable "calibrate a new \
powder" procedure and per-powder parameter card should contain (parameters with \
posterior uncertainty, covariates logged, validity range, re-calibration triggers), \
citing precedents for transferable feeder/powder characterization (e.g. \
material-property databases and multivariate models predicting feeder behaviour). \
Finish with a ranked, value-per-effort verdict for THIS rig: what to build first, \
what to defer, and what not to build, grounded in the literature."""


def main() -> None:
    client = EdisonClient(api_key=_api_key())
    query = RIG_CONTEXT + "\n" + QUESTION
    task = TaskRequest(name=JobNames.LITERATURE_HIGH, query=query)
    tid = client.create_task(task)
    print(f"{NAME}: trajectory_id {tid}", flush=True)
    (OUT / f"{NAME}.task.json").write_text(
        json.dumps(
            {"trajectory_id": str(tid), "job": str(JobNames.LITERATURE_HIGH), "query": query},
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
