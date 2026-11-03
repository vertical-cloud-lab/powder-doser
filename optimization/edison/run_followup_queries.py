#!/usr/bin/env python3
"""Submit the three follow-up Edison queries for issue #123 / PR #124 (submit-only).

1. mpc_followup (LITERATURE_HIGH): MPC / smooth continuous control as an
   alternative or complement to the phase-switched Layer 1 policy, with explicit
   treatment of parameter interactions (tilt x tap coupling, rotate-then-tap
   local depletion) and PID on instantaneous dose rate to cut dispense time.
2. physics_engines (LITERATURE): open-source physics/game/animation engines
   usable as a "digital twin" for powder flowing through an auger.
3. particle_methods (LITERATURE): numerical methods (DEM, SPH, MPM, ...) for
   simulating particle behavior in screw/auger feeders.

Writes query_out/<name>.task.json for each. Fetch later with
fetch_followup_results.py (wait ~15 min for the high-effort query, ~10 min for
the standard ones)."""
import json
import os
from pathlib import Path

from edison_client import EdisonClient, JobNames
from edison_client.models.app import TaskRequest

HERE = Path(__file__).parent
OUT = HERE / "query_out"
OUT.mkdir(exist_ok=True)


def _api_key() -> str:
    key = os.environ.get("EDISON_API_KEY") or os.environ.get("EDISON_PLATFORM_API_KEY")
    if not key:
        raise SystemExit(
            "Edison API key is not set (EDISON_API_KEY / EDISON_PLATFORM_API_KEY)."
        )
    return key


RIG_CONTEXT = """Context: we are building an open-source, low-cost powder doser for \
gravimetric metering of dry powders (ultimately metal additive-manufacturing \
feedstocks such as AlSi10Mg, silicon, stainless steel; salt and similar surrogates \
during development) inside an autonomous self-driving-lab alloy-discovery loop. The \
rig is an Archimedean auger in a tilted tube driven by a stepper motor (44:20 gear), \
a solenoid tapper that strikes the tube, and a servo-controlled tilt of the whole \
assembly (0-45 degrees from horizontal), dispensing into a vial on an analytical \
balance (A&D HR-100A, ~1 mg readability, ~1 s settling; readings during actuation \
are vibration-corrupted). Current controller: a deterministic three-phase policy \
(bulk feed at steep tilt -> fine incremental rotations -> tap-until-tolerance at \
shallow tilt), with per-phase parameters (tilt angle, rotation increment/speed, taps \
per cycle, settle time, gram-based phase-switch thresholds) intended to be tuned by \
contextual multi-objective Bayesian optimization. Objectives: absolute mass error \
(target +/- 1 mg, stretch +/- 0.1 mg) and dose time, with no-overshoot as a hard \
asymmetric constraint (powder cannot be removed). Context variables: hopper fill \
level, powder humidity-exposure history, ambient temperature. Empirically observed \
interactions: (a) tapping or rotating at steeper tilt dispenses far more per action \
than at shallow tilt; (b) a tap immediately after an auger rotation dispenses more \
than repeated taps alone, because taps deplete the loose powder near the tube lip \
while rotation replenishes it - i.e., the state includes an unobserved "lip \
reservoir" that actuators couple through."""


QUERIES = {
    "mpc_followup": (
        JobNames.LITERATURE_HIGH,
        RIG_CONTEXT
        + """

This is a follow-up to an earlier review that recommended a phase-switched inner \
policy plus Bayesian optimization of its parameters. We now want a HIGH-EFFORT \
deep-dive on the alternative we are leaning toward: treating the dose as one smooth \
continuous control problem (Model Predictive Control or PID on the instantaneous \
dose rate) instead of, or blended with, discrete phases. Please cover, with \
citations:

1. MPC formulations that fit this rig: hybrid / mixed-integer MPC for systems \
mixing continuous inputs (auger speed, tilt angle) with impulsive discrete events \
(solenoid taps); MPC for integrating processes (dispensed mass only increases); \
asymmetric constraint handling (no overshoot) and reference governors; economic MPC \
trading accuracy against time. What horizon lengths, sampling rates, and model \
orders are realistic when the measurement is a ~1 Hz effective, noisy, \
settling-limited mass signal?

2. Modeling for MPC on cheap hardware: control-oriented model identification for \
powder feeding from tens (not thousands) of doses - low-order ARX/state-space with \
input nonlinearities (Hammerstein), grey-box models with a hidden "lip reservoir" \
state capturing the rotate-then-tap depletion/replenishment interaction, and \
Gaussian-process or learning-based MPC (GP-MPC, learning residual dynamics) where \
the model is powder-dependent. Include state estimation: Kalman/moving-horizon \
estimation of true dispensed mass and in-flight powder from a delayed, \
vibration-corrupted balance signal, and estimating instantaneous dose rate from \
noisy mass differences.

3. PID / cascaded control on dose RATE: pharmaceutical loss-in-weight feeders \
regulate mass FLOW RATE with PI(D) on screw speed - how is that transferred to a \
finite-dose (batch) task with a stopping constraint? Cover rate-based trickle \
control in checkweighers/filling machines, cutoff prediction (stop the actuator \
early by predicted in-flight mass), and whether PID-on-rate genuinely reduces dose \
time versus phase-switched policies in published comparisons.

4. Interaction-aware control: multivariable control where inputs couple through a \
shared depletable buffer (analogies: surge tanks, screw feeders with agitators, \
vibratory bowl feeders + conveyors); RGA-style interaction analysis for our tilt x \
tap x rotation coupling; and whether the literature supports scheduling one \
actuator as a function of another (e.g., tilt as a gain-scheduling variable for tap \
effectiveness) rather than optimizing them independently.

5. Smooth parameterizations of dose profiles: replacing discrete phases with \
continuous decay profiles (e.g., auger speed as an exponential/spline function of \
remaining mass, tap energy proportional to remaining mass), their use in filling \
and dosing machines, and how such profile parameters interact with BO tuning \
compared to phase thresholds.

6. A concrete recommendation: for THIS rig (seconds-scale doses, 1 Hz noisy \
feedback, powder-dependent dynamics, hobby-grade actuators, MicroPython inner loop \
+ Python host), is MPC worth it over the tuned three-phase policy? If yes, specify \
the minimal viable MPC (model form, estimator, horizon, solver that runs on a host \
PC, fallback safety layer). If no, state what evidence would change the answer and \
what intermediate step (e.g., rate-PID trickle phase inside the existing \
three-phase skeleton, or an MPC-like one-step-ahead predictive cutoff) captures \
most of the time savings. Include a comparison table of tuned phase-switched \
policy vs rate-PID vs full MPC on accuracy, time, sample cost to commission per \
powder, robustness to powder change, and implementation complexity.""",
    ),
    "physics_engines": (
        JobNames.LITERATURE,
        RIG_CONTEXT
        + """

Question: what existing physics-based simulation ENGINES could serve as a \
"digital twin" of powder flowing through and out of this tilted auger, so we can \
prototype and pre-tune dosing control policies in simulation before hardware runs? \
We are explicitly interested in video-game and animation-style physics engines \
(real-time or near-real-time, plausible rather than perfectly calibrated), not \
only research-grade codes. Please survey, with citations and links where possible, \
OPEN-SOURCE options in particular:

1. Game/animation-style engines with granular-material support: e.g., NVIDIA \
PhysX/Flex/Warp/Isaac Sim particle systems, Project Chrono (Chrono::Granular / \
Chrono::GPU), Bullet, MuJoCo (and its recent particle/deformable support), Taichi \
(MPM/DEM examples, e.g., taichi_elements), Blender's rigid-body/particle systems \
and Molecular add-on, Houdini-style grain solvers (POP grains / PBD) and \
position-based-dynamics libraries. For each: license, GPU support, particle counts \
achievable in near-real-time, contact model fidelity (friction, cohesion, \
rolling resistance), Python scriptability, and evidence of use for granular flow.

2. Research/engineering DEM codes usable as engines: LIGGGHTS/LAMMPS granular, \
YADE, Kratos DEM, MercuryDPM, MFiX-DEM, esyS-Particle, GranOO - same criteria, \
plus screw-conveyor/auger example cases if published.

3. Reduced/hybrid approaches for speed: continuum granular models, \
material-point method (MPM), position-based dynamics, cellular automata, and \
learned surrogates (graph-network simulators like DeepMind's GNS, NeuralDEM) that \
approximate DEM at a fraction of the cost - can they capture auger conveying and \
tap-induced avalanching well enough for control-policy pretraining?

4. Sim-to-real considerations for granular digital twins: DEM calibration of \
contact parameters against simple bench tests (angle of repose, drained mass flow), \
particle upscaling/coarse-graining (simulating 100-micron powder with mm-scale \
pseudo-particles), how sensitive auger mass-per-revolution and tap-triggered \
discharge are to calibration error, and published examples of tuning or verifying \
feeder/doser control policies in simulation before deployment.

5. Recommendation: a shortlist (2-3) of open-source engines best matched to \
"tilted auger + tube + solenoid taps + vial on balance" at engineering-workstation \
scale, and a suggested workflow coupling the engine to our Python control code \
(step the sim, command auger angle/tilt/tap impulses, read out dispensed mass).""",
    ),
    "particle_methods": (
        JobNames.LITERATURE,
        RIG_CONTEXT
        + """

Question: what are the established METHODS for simulating particle behavior in \
screw/auger feeders and similar powder-handling devices? This is the methods \
companion to a separate tooling survey, so focus on the physics and numerics, with \
citations:

1. Discrete Element Method (DEM) fundamentals for powders: contact models \
(Hertz-Mindlin, linear spring-dashpot), cohesion models for fine/humid powders \
(JKR, simplified JKR, liquid-bridge/capillary models), rolling friction and \
non-spherical particle representations (multi-sphere, superquadric), timestep \
(Rayleigh) limits, and the computational scaling that makes ~100-micron metal \
powder at device scale expensive.

2. DEM of screw conveyors and auger dosing specifically: published studies of \
screw feeders/conveyors (mass flow per revolution vs fill level, inclination \
angle effects, pulsating discharge at low fill), auger dosing of pharmaceutical \
and food powders, and validation against experiments. What did they learn about \
the parameters we care about (feed factor vs fill level and tilt, discharge \
variability near the tube exit)?

3. Vibration- and impact-driven powder dynamics: DEM/experimental studies of \
tapped density and tap-induced compaction/avalanching, vibratory feeders and \
transport regimes vs amplitude/frequency, impulse (hammer/knocker) driven \
discharge of arched or rat-holed powder - the physics behind our solenoid tapper's \
diminishing returns when the tube lip is depleted.

4. Cheaper-than-DEM methods: continuum/constitutive approaches (mu(I) rheology, \
critical-state soil mechanics), material point method (MPM), SPH for granular \
media, kinematic/cellular-automata hopper models, 1D surge/reservoir compartment \
models of feeders (hopper -> screw -> lip discharge chains), and stochastic \
avalanche models - which are adequate for a control-oriented digital twin where we \
need dose-mass trajectories, not grain-scale fidelity?

5. Calibration and validation methodology: standard DEM calibration tests (angle \
of repose, FT4/shear cell, drained flow), inverse calibration with optimization or \
BO, coarse-graining rules, and quantified sim-vs-experiment error for feeder mass \
flow in published work.

6. Recommendation: for predicting dispensed-mass trajectories of this tilted \
auger + tapper rig across powders (salt now; AlSi10Mg, silicon, stainless steel \
later), what simulation-method ladder does the literature support - e.g., \
compartment/reservoir model for control design, coarse-grained DEM for physics \
insight, full DEM only for geometry changes - and roughly what compute each rung \
costs?""",
    ),
}


def main() -> None:
    client = EdisonClient(api_key=_api_key())
    for name, (job, query) in QUERIES.items():
        task = TaskRequest(name=job, query=query)
        tid = client.create_task(task)
        print(f"{name}: trajectory_id {tid} (job {job})", flush=True)
        (OUT / f"{name}.task.json").write_text(
            json.dumps({"trajectory_id": str(tid), "job": str(job), "query": query}, indent=2)
        )


if __name__ == "__main__":
    main()
