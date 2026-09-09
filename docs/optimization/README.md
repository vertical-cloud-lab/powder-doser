# What can be optimized in the doser controller, and against what objectives?

Response to [issue #161](https://github.com/vertical-cloud-lab/powder-doser/issues/161),
which brainstorms optimization objectives and tunable parameters for the
two-phase dispensing controller (a **bang-bang bulk phase** that runs the
auger at a fixed tilt / RPM / tap setting until the Kalman-filtered mass
estimate crosses a cutoff, followed by a **trim phase** — PI control of the
auger, or discrete solenoid taps — that closes the remaining error).

This document has three parts: a direct review of the brainstorm, a
proposed problem formulation, and a synthesis of the high-effort Edison
Scientific literature query commissioned for this issue
(artifacts in [`edison_artifacts/`](edison_artifacts/)).

---

## 1. Review of the brainstorm

### 1.1 The objectives are right, but incomplete

"Fastest dispensing" and "minimize error" are the correct axes, but as
stated they hide three things the campaign should measure explicitly:

1. **Overshoot is not just error — it is irreversible error.** Powder
   cannot be un-dispensed; an overshoot beyond tolerance means a discarded
   dose (or a discarded sample downstream). Undershoot, by contrast, is
   recoverable by more trimming at the cost of time. The loss function
   should therefore be **asymmetric**: treat `P(overshoot > tol)` as a
   near-hard constraint, and let undershoot trade off against time. This
   is exactly why commercial gravimetric dispensers (Quantos-style
   bulk/fine dosing) deliberately undershoot the coarse phase and approach
   the setpoint from below.
2. **Repeatability, not single-shot error.** Powder flow is stochastic
   (avalanches, clumps), so a single dispense's error is a noisy draw. The
   quantity worth optimizing is distributional: e.g. `P(|error| ≤ tol)`
   over replicates, or the CV/RSD at a given target mass — this is also
   the number every commercial spec sheet quotes, so it makes the device
   comparable to Quantos / Chemspeed benchmarks already collected in
   [`docs/edison/literature-high-powder-dispensing.md`](../edison/literature-high-powder-dispensing.md).
3. **Total time includes the trim phase and balance settling.** A bulk
   phase tuned "fastest" in isolation can hand the trim phase a large,
   variable remainder that takes longer to trim than was saved. Time must
   be measured end-to-end: bulk + trim + settling waits until the dose is
   *confirmed* in tolerance.

### 1.2 The speed and accuracy parameters are coupled through the cutoff

The brainstorm's instinct to keep tilt / RPM / tapping out of an
error-minimization ("would most likely make the system way too slow") is
sound, but the deeper structure is worth naming. The bulk phase's job is
not accuracy — it is to hand the trim phase a **small, predictable
remainder**. What links the two phases is the **flow rate at cutoff**:

- The mass still in flight (falling powder column, auger discharge after
  stop, filter lag) scales with the bulk-phase flow rate. Higher
  tilt/RPM/tap settings mean a faster bulk phase *and* a larger, more
  variable stopping transient.
- Therefore the **cutoff threshold (undershoot margin)** — how far below
  the setpoint the bang-bang switches off — is the single most important
  parameter *missing* from the brainstorm's list. It must scale with the
  bulk flow rate (a fixed margin is either wasteful at low flow or
  overshoot-prone at high flow). A useful reframe: the margin should be
  roughly `flow_rate × effective_latency + k·σ(stopping transient)`, with
  the latency including filter lag — which is where Q and R actually enter
  the accuracy story (see 1.3).

Two other parameters are implicit today and should be surfaced as
first-class tunables before any campaign: the **trim tolerance band**
(when to declare done — though this is really a requirement set by the
application, not a free parameter) and the **balance settling wait**
between actuation and a trusted reading (dominates trim-phase time when
taps are involved).

### 1.3 Q and R do not belong in a black-box optimization

Putting the Kalman covariances into the same optimizer as tilt/RPM is
appealing but has three problems:

1. **Identifiability.** For a scalar mass estimate with a random-walk (or
   constant-flow) process model, the steady-state Kalman gain depends only
   on the *ratio* Q/R, not on the pair. An optimizer given two knobs that
   move one effective quantity wastes budget exploring a degenerate
   direction.
2. **They are identifiable from data by construction.** R is simply the
   balance noise variance: measure it directly from a static tare trace
   (and it is *not constant* — it inflates during vibration/tapping, which
   argues for a duty-cycled "actuate, pause, read" pattern or a
   time-varying R rather than one fixed matrix). Q encodes flow-rate
   variability: estimate it from logged dispensing traces (innovation
   whitening / autocovariance least-squares), refreshed per powder.
3. **The objective they influence is latency, not error per se.** The
   filter affects dosing error through cutoff timing: too much smoothing →
   lag → late cutoff → overshoot; too little → noise-triggered early or
   jittery cutoff. If you want a knob in the campaign, expose **one**
   parameter — the effective filter bandwidth (equivalently the Q/R ratio,
   or a time constant) — and let the identification set the scale.

The same logic applies in miniature to KP/KI: the trim plant is close to
an integrator driven by quantized stochastic increments, so classical
starting points (relay/IMC-style tuning on the measured trim response)
get you a stable baseline cheaply, and black-box optimization is then a
*refinement* over a two-parameter space with a known-safe center — a much
easier problem than cold-starting. For **tap trim**, the real tunables are
the increment size distribution (tap energy / count per decision) and the
decision rule (how many taps per settled reading); the mean single-tap
increment sets the physical floor on achievable tolerance, so measure it
per powder before promising an accuracy spec.

### 1.4 The two-step idea: right instinct, needs a constraint to be safe

Optimizing speed parameters first and accuracy parameters second is a
reasonable *staging*, but pure sequential optimization of coupled
parameters is greedy and can strand step 2: if step 1 returns "maximum
tilt, maximum RPM, maximum tapping," the stopping transient may be so
large and variable that **no** setting of the accuracy parameters can
recover tolerance — the accuracy campaign then optimizes inside a
hopeless region. Three formulations fix this, in increasing order of
sophistication:

1. **Constrained step 1 (recommended first).** Step 1 is not "fastest
   possible" but "fastest subject to a trim-able handoff": maximize bulk
   flow rate subject to, e.g., `σ(mass delivered past cutoff) ≤ margin
   budget` and no jams/stalls. This keeps the two-step simplicity while
   making step 2 feasible by construction.
2. **Epsilon-constraint single objective.** Minimize end-to-end time
   subject to `P(|error| ≤ tol) ≥ 95%` and `P(overshoot > tol) ≈ 0`,
   optimizing bulk and trim parameters jointly. Most sample-efficient
   when you already know the tolerance you must hit.
3. **Multi-objective BO (qNEHVI / EHVI over time vs. error).** Returns
   the whole Pareto front so the operating point can be chosen per
   application (a 5 mg dose for alloy discovery vs. a 500 mg bulk
   transfer want different trade-offs). Costs more evaluations; worth it
   once the rig is reliable enough to run overnight campaigns.

Practical notes for any of the three: each evaluation is a real dispense,
so (a) replicate 3–5 times per configuration and use a noise-aware
(heteroscedastic) model — flow variability itself depends strongly on the
parameters; (b) run a cheap **screening design first** (factorial or
Latin hypercube over tilt × RPM × tap frequency, logging mean flow rate
and its variance) — it bounds the safe region, provides priors, and often
reveals that one parameter dominates; (c) treat **powder identity as
context**: optimal parameters will shift with flowability (Hausner ratio
/ FFC class), so either re-run a short per-powder calibration or use a
contextual/transfer formulation with powder descriptors as context
variables rather than one global optimum.

### 1.5 Parameter classification (summary table)

| Parameter | Class | Recommendation |
|---|---|---|
| Tilt angle | Bulk recipe | Optimize (screen first; safe bounds from spill/jam limits) |
| Auger RPM | Bulk recipe | Optimize (screen first) |
| Tap frequency (bulk) | Bulk recipe | Optimize; interacts with balance noise — prefer duty-cycled actuate/read |
| **Cutoff margin** | Coupling | **Optimize — highest leverage; scale with measured flow rate** |
| Q, R | Estimation | Identify from data; expose only the Q/R ratio (bandwidth) if optimizing |
| KP, KI | Trim | Classical tuning for baseline, BO refinement after |
| Tap increment / taps-per-reading | Trim | Characterize increment distribution per powder; optimize decision rule |
| Trim tolerance band | Requirement | Fix from application spec, don't optimize |
| Balance settling wait | Timing | Measure step response once; fix |
| Vibration (DRV2605L effect/amplitude) | Bulk recipe (latent) | Hold out of round 1; it corrupts the mass signal most |

---

## 2. Proposed formulation (the single most defensible version)

> **Minimize** expected end-to-end dose time
> **over** {tilt, auger RPM, tap frequency, cutoff margin, trim policy
> (PI gains or tap rule)}
> **subject to** `P(|error| ≤ tol) ≥ 0.95` and `P(overshoot > tol) ≤ 0.01`,
> estimated from 3–5 replicates per configuration,
> **per powder class** (free-flowing vs. cohesive surrogate),
> with Q/R identified from logged traces rather than searched.

Campaign order: (1) instrument + log (raw balance trace, filtered
estimate, actuator commands, per-tap increments — timestamped); (2)
screening sweep for flow-rate mean/variance maps and safe bounds; (3)
identify filter + measure single-tap increment distribution; (4)
constrained BO on the formulation above (Ax/BoTorch and its
[Honegumi](https://github.com/sgbaird/honegumi) templates make the
constrained and multi-objective variants straightforward); (5) hold-out
validation replicates at the chosen operating point, reported as CV at
target mass — directly comparable to the Quantos/Chemspeed numbers in the
existing literature review.

---

## 3. Edison Scientific literature synthesis

A high-effort `LITERATURE_HIGH` query covering objectives, two-stage vs.
joint optimization, parameter classification, hardware-in-the-loop
Bayesian optimization, and powder-physics accuracy floors was run for
this issue (task `0c1829bf-e499-4659-9d61-12a31a845f0b`, success).
Verbatim answer, numbered references, and full task state:
[`edison_artifacts/`](edison_artifacts/) —
[answer](edison_artifacts/optimization_review.answer.md),
[references](edison_artifacts/optimization_review.references.md).

### 3.1 Where the literature confirms the review above

- **Objectives.** Published gravimetric dosing work reports RSD/relative
  error of feed rate (loss-in-weight feeders), per-material percentage
  error and failure rate (SDL dispensers), and treats throughput as a
  constraint, not an objective. Formal Pareto fronts for speed vs.
  accuracy are essentially absent from the dosing literature — the
  dominant paradigm is exactly the **epsilon-constraint** framing
  proposed in §2 ("as fast as possible subject to error < tolerance").
- **Asymmetric overshoot handling** is established practice, embodied
  structurally rather than as an explicit loss function: auger systems
  deliberately undershoot the bulk phase and approach from below
  (Quantos's self-adaptive algorithm implicitly penalizes overshoot;
  only spatula-type systems like Cooper's dual-arm robot can return
  excess to the hopper).
- **The switchover threshold is the key omission.** Edison independently
  flags the bulk→trim switchover threshold as "arguably the single most
  impactful parameter not listed in the team's notes," recommends a
  **flow-rate-dependent prediction of in-flight mass** rather than a
  fixed offset, and documents the analogous gravimetric↔volumetric
  transition as a primary error source in loss-in-weight feeders.
- **Q and R should be identified, not black-box optimized.** Named
  methods: Mehra-style innovation/output-correlation, autocovariance
  least squares (ALS), maximum-likelihood/EM, with innovation-whiteness
  validation. Optimizing Q/R against dose error "risks exploiting filter
  lag to produce artificially smooth (but delayed) estimates, yielding
  non-physical and non-transferable values."
- **Two-stage sequential optimization is a greedy decomposition** of a
  coupled problem; freezing throughput-optimal speed parameters can
  leave the accuracy floor set by physics (in-flight mass, pulsation)
  rather than by the remaining tunables. A constrained joint formulation
  is preferred.

### 3.2 What the literature adds (quantitative anchors)

- **Budgets:** hardware-in-the-loop BO typically converges in 30–100
  physical trials (PI drive tuning: useful Pareto sets in 15–30 trials
  after 10 random initializations); recommended: 10 initialization + 40–90
  BO trials, 3–5 replicates per condition. Digital-twin-guided BO cut
  hardware experiments by 46–57%.
- **Auger operating band:** loss-in-weight feeders are usable in roughly
  20–90% of rated drive command; outside that, flow turns erratic. The
  **feed factor** (mass per screw revolution) as a function of fill level
  is the standard calibration object — worth adopting directly.
- **Tilt** was the strongest single predictor of mass flow rate in
  vibratory powder dispensing, converting all-or-nothing discharge into a
  controllable regime — supporting screening it first rather than
  assuming RPM dominates.
- **Tapping/vibration is powder- and geometry-specific:** above the flow
  threshold, more amplitude *increased* dose-mass variability; excitation
  parallel to the capillary axis halved RSD vs. perpendicular (5% vs.
  10%). So tap frequency belongs in the bulk-speed screen, but tap
  *energy* is what matters for trim increments.
- **Accuracy floors:** dosing below about 20 mg is flagged as hard across
  platforms; best-case vibratory dispensing RSD near 5%; balance noise
  0.1–1 mg. Metal-AM powders (Hausner near 1.0–1.1) should support much
  tighter tolerances than cohesive surrogates like xanthan gum (Hausner
  potentially >1.4) — tolerance bands must be material-dependent.
- **Algorithm pointers:** qNEHVI for noisy multi-objective BO (validated
  at 1–30% objective-range noise, supports batches), SafeOpt/LoSBO for
  certified-safe exploration (no jams/spills), EGBO for constraint-heavy
  Pareto coverage, and contextual GPs with powder descriptors (Hausner,
  d50, bulk density) for cross-powder transfer.

### 3.3 Edison's recommended formulation vs. §2

Edison's single most defensible formulation is bi-objective:

> **Minimize** (dose_time, |dose_error|) **subject to**
> P(overshoot > tolerance) ≤ α, no_jam, no_spill,
> over {tilt, bulk_RPM, trim_RPM, tap_frequency, switchover_threshold,
> trim_tolerance_band, KP, KI}, with Q/R and initial PI gains identified
> from data, and powder descriptors as context variables.

This differs from §2 only in keeping |error| as a second objective
(Pareto) instead of a chance constraint, and in adding `trim_RPM` and
the tolerance band as decision variables. Both formulations are
defensible: use the **epsilon-constraint version of §2 when the
application tolerance is fixed** (most alloy-discovery dosing), and the
**bi-objective version when the doser must serve multiple dose
regimes** and the operating point will be chosen per campaign. Edison's
suggestion to let the optimizer see the tolerance band is best treated
carefully — leave it fixed when it is a downstream requirement, optimize
it only when "futile-cycling time vs. accuracy" is genuinely negotiable.

The protocol ordering in §2 (instrument/log → screen → identify →
constrained BO → hold-out validation) matches Edison's §6
recommendation, including the fractional-factorial screen (16–32 runs
with replicates) before any BO, and the same log schema (raw balance
trace, filtered estimate, phase timestamps, actuator settings, powder
lot and fill level, ambient conditions).
