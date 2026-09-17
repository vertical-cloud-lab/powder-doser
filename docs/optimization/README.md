# What can be optimized in the doser controller, and against what objectives?

Response to [issue #161](https://github.com/vertical-cloud-lab/powder-doser/issues/161),
which brainstorms optimization objectives and tunable parameters for the
two-phase dispensing controller (a **bang-bang bulk phase** that runs the
auger at a fixed tilt / RPM / tap setting until the Kalman-filtered mass
estimate crosses a cutoff, followed by a **trim phase** — PI control of the
auger, or discrete solenoid taps — that closes the remaining error).

This document has five parts: a direct review of the brainstorm, a
proposed problem formulation, a synthesis of the high-effort Edison
Scientific literature query commissioned for this issue
(artifacts in [`edison_artifacts/`](edison_artifacts/)),
clarifications raised in the PR #162 review (§4), and a worked
screening-DOE example requested in that review (§5).

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
| Tilt angle (per phase, §4.3) | Bulk/trim recipe | Optimize; screen `tilt_bulk` and `tilt_trim` separately (safe bounds from spill/jam limits) |
| Auger RPM | Bulk recipe | Optimize (screen first) |
| Tap frequency (bulk) | Bulk recipe | Optimize; interacts with balance noise — prefer duty-cycled actuate/read |
| **Cutoff margin** | Coupling | **Optimize — highest leverage; scale with measured flow rate** |
| Q, R | Estimation | Identify from data; expose only the Q/R ratio (bandwidth) if optimizing |
| KP, KI | Trim | IMC/relay baseline from identified plant gain, bounded BO refinement after (§4.3) |
| Trim authority bound (RPM cap/floor, or pulse duration) | Trim | Optimize as bounded variable — this is what "trim RPM" means under PI trim (§4.3) |
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

---

## 4. Clarifications from review (PR #162)

Three questions from review deserve durable answers here. They anchor on
Edison's §6 protocol and §6.3 formulation
([answer](edison_artifacts/optimization_review.answer.md)); that file is
a verbatim record of the Edison output and stays unedited, so the
clarifications live in this document.

### 4.1 What powder characterization contributes to the optimization

The characterization step (Edison §6.1.2: Hausner ratio, particle size
distribution, bulk/tapped density, angle of repose) adds **no decision
variables and never appears in the objective**. It enters the campaign
in four concrete places:

1. **Context variables → cross-powder transfer.** The target
   application is a multi-powder library (8–12 active reservoirs
   against a library of about 30 powders, per
   [`design/brainstorming.md`](../../design/brainstorming.md)), and a
   full BO campaign costs 50–100 dispenses *per powder*. That cost is
   only paid down if campaigns transfer: fit one surrogate
   `f(tilt, RPM, …; Hausner, d50, ρ_bulk)` over parameters *and*
   descriptors, so data from already-characterized powders warm-starts
   each new powder, and conditioning the model on a new powder's
   measured descriptors yields good starting parameters before a single
   dispense. Without recorded descriptors, every powder is a cold
   start.
2. **Feasible tolerance selection.** The accuracy floor (minimum stable
   increment, avalanche statistics) tracks flowability: Hausner near
   1.0–1.1 (metal-AM powders) supports far tighter tolerances than
   Hausner above 1.4 (xanthan gum surrogate). Setting `tol` in
   `P(|error| ≤ tol) ≥ 0.95` below the material's floor hands the
   constrained BO an empty feasible set — the campaign spends its whole
   budget discovering the target was impossible. Characterization sets
   a defensible `tol` per material class *before* hardware time is
   spent.
3. **Bounds and priors that shrink the search.** Conditioned bulk
   density predicts the feed factor (mass per revolution) and hence the
   flow rate at any RPM — which scales the cutoff-margin prior (§1.2)
   and the expected single-tap increment. Cohesion class indicates
   which tilt/RPM regions are bridging- or flooding-prone, i.e. the
   initial safe set that constrained/SafeOpt-style BO requires.
4. **Pooling and drift diagnosis.** Descriptors recorded per lot let
   later campaigns be pooled, and make lot-to-lot drift (humidity
   uptake changing flowability) show up as a shifted context rather
   than unexplained noise.

Cost note: Hausner ratio and bulk/tapped density need only a graduated
cylinder plus the existing tapper; angle of repose is a photograph. PSD
is the expensive one — the vendor's d50 is an acceptable stand-in at
first. If the device were only ever tuned per-powder from scratch,
items 2–3 alone justify the cheap subset; item 1 is what makes the
30-powder ambition tractable.

### 4.2 The screening DOE: what it is and what it feeds

The fractional-factorial screen (Edison §6.2) is neither an optimizer
nor new hardware — it is a scripted, pre-planned block of dispenses run
once per powder class, before BO. Each candidate parameter (tilt, RPM,
tap frequency, cutoff margin) gets two levels spanning its safe range; a
chosen fraction `2^(k−p)` of the full `2^k` grid (e.g. 8 of the 16
corner settings for k = 4, plus center points to detect curvature, with
3–5 replicates each) still estimates every main effect free of
two-factor interactions (the interactions themselves arrive in aliased
pairs — §5.3). At 1–2 min per dispense this is one unattended overnight
run. §5 gives the full worked design for this rig.

What it returns, and where each output lands:

| Screen output | Feeds |
|---|---|
| Main-effect ranking (which parameters actually move flow rate, variability, overshoot) | Fix insensitive parameters → lower-dimensional BO; each dropped dimension saves real dispenses |
| Flow-rate mean/variance map (feed-factor profile) | Cutoff-margin scaling (§1.2); plant gain for the IMC-style PI baseline (§4.3) |
| Onset of bridging, erratic flow, spills/jams | Box bounds and the initial safe set constrained BO starts from |
| Replicate scatter per setting | Heteroscedastic noise model for the GP; replicate count for later evaluations |
| The 16–32 structured runs themselves | BO initialization data (replacing purely random initialization) |

Architecturally it contributes **software and workflow, not mechanism**:
it defines the per-powder calibration routine the doser can run
autonomously, and its logging needs (raw balance trace, filtered
estimate, phase timestamps, actuator commands) are exactly the log
schema of campaign step 1 in §2 — implement the logger once and both
stages use it. Its findings can also re-rank hardware effort: if tilt
dominates (as the vibratory-dispensing literature suggests), tilt
repeatability is worth more engineering than another control knob.

### 4.3 Decision-variable refinements (KP/KI, trim RPM, tolerance, per-phase tilt)

Four refinements to Edison's §6.3 variable list `{tilt, bulk_RPM,
trim_RPM, tap_frequency, switchover_threshold, trim_tolerance_band, KP,
KI}`, consistent with §1.3 and §3.3:

- **KP/KI are IMC-initialized, then BO-refined — not cold-searched.**
  This document (§1.3) and Edison itself (§3(b) and §6.6) both stage it
  this way: derive conservative gains from an integrating-process model
  (IMC-style, with the measured feed factor as the plant gain and the
  closed-loop time constant chosen against balance settling/filter
  lag), then let BO refine only within a bounded region around that
  center (e.g. a factor of 3 either way on a log scale) under safe-BO
  constraints. The gains stay in the *joint* campaign because their
  optimum shifts with the other variables — the cutoff margin sets the
  remainder handed to trim, and the trim authority bound sets how hard
  the loop may push — and because the plant violates IMC's assumptions
  (integrating, stochastic, quantized avalanche arrivals), which makes
  the IMC result a known-safe center rather than an optimum.
- **"trim_RPM" means the trim authority bound, not a competitor to the
  PI output.** Under PI trim the instantaneous auger RPM *is* the
  controller output, so a fixed trim RPM would indeed be redundant. The
  legitimate free parameters are the saturation bounds on that output:
  the RPM cap, and the minimum usable RPM below which auger flow turns
  erratic (loss-in-weight practice puts the usable band above roughly
  15–20% of rated drive; below it, pulsed on/off modulation replaces
  slower rotation). In the tap-trim or pulsed-auger variant there is no
  PI at all and the fixed pulse rate/duration is first-class. The
  cleanest framing is §2's: a discrete **trim mode** (continuous PI vs.
  pulsed auger vs. taps) plus that mode's small parameter set.
- **Spec tolerance ≠ stopping band — only the second is tunable.** The
  application tolerance in `P(|error| ≤ tol)` defines the problem; an
  optimizer allowed to move it will always widen it, since every
  relaxation looks faster. Fix it per application — or, equivalently,
  run the bi-objective variant and let a human choose the operating
  point off the time-vs-error Pareto front. The controller's internal
  **stopping band** (when trim declares done) may legitimately differ
  from the spec — tighter, to leave margin for settling drift, and
  asymmetric, since the approach is from below — and *is* a valid
  bounded decision variable, bounded below by balance noise and the
  single-increment floor. Where policy sets stopping band = spec
  tolerance, drop it from the variable list (§3.3's recommendation).
- **Tilt should be per-phase.** Bulk wants maximum *controllable* flow;
  trim wants the minimum stable increment; the test-rig firmware's
  servo presets (horizontal/tilt/vertical/tip) already anticipate
  distinct poses. So screen `tilt_bulk` and `tilt_trim` as separate
  variables — and note the end-of-dose retract pose is itself an
  actuation against in-flight mass that interacts with the cutoff
  margin. The caveat is the mid-dose transition: the servo move costs
  time and mechanically disturbs the head at the accuracy-critical
  moment, so `tilt_trim` earns a BO slot only if the screen shows the
  trim increment is sensitive to it; otherwise hold tilt constant
  across phases and avoid the transient entirely.

---

## 5. Worked example: the screening DOE for this rig

Requested in review: what the §4.2 screen concretely looks like, and
why tilt, auger RPM, tap frequency, and cutoff margin are the right
four factors. Levels below are in real units but are placeholders
until confirmed against `config.py` on the rig plus a short
range-finding pass; the *rules* for setting each level are part of the
design and are stated alongside.

### 5.1 Why these four factors — and why nothing else

A parameter earns a factorial slot when all five of these hold; the
screened four are the only candidates that pass every test:

1. **Its effect is empirically unknown and powder-specific.** The
   literature cannot predict even the *direction* of some of these
   effects (tap excitation may raise, plateau, or lower flow — §3.2);
   a screen exists to resolve exactly that kind of uncertainty.
   Parameters whose effect is known by construction (a wider stopping
   band is always faster and less accurate) teach a screen nothing.
2. **It acts on the plant, not on the estimator or the measurement
   protocol.** The screen measures flow physics and the bulk→trim
   handover. Q/R shape the *estimate* of that physics — varying them
   in the same factorial would confound filter lag with flow response,
   and §1.3's identification route is cheaper and transferable. The
   balance settling wait is measurement protocol, identified once from
   a step-response test.
3. **It is live in the bulk phase.** The screen freezes the trim
   policy at current defaults, so each run's end-to-end time and error
   are attributable to the screened factors. KP/KI and the trim
   authority bound act only after cutoff, and their sensible starting
   point — the IMC center of §4.3 — *requires the feed factor this
   screen measures*, so they cannot precede it.
4. **It is software-settable, continuous, and safely boundable at two
   levels.** All four change between runs over the serial REPL
   (`a <deg>` for tilt, stepper speed, tap cadence, cutoff parameter);
   no hardware is touched during an unattended block.
5. **Jointly, the four span both objectives.** Tilt, RPM, and tap
   cadence set the bulk flow regime — its mean (speed) and its
   variability/pulsation (the accuracy-relevant part). The cutoff
   margin is the single accuracy-side factor: §1.2's coupling variable
   that converts a flow regime into a terminal error and a trim
   workload. Screening the three mechanical factors without the margin
   would characterize speed only; screening the margin at one flow
   regime would miss the interaction the design exists to measure.

Per factor, the open question the screen answers:

| Factor | Open question |
|---|---|
| `tilt_bulk` | The literature's strongest single flow predictor (§3.2) — is that true on this auger and this powder, and where do no-flow and flooding set in? |
| Auger RPM | Feed factor (mass/rev) and pulsation vs. RPM — the plant gain that margin scaling and the IMC gains are built on; locates the usable band (LIW practice: erratic outside roughly 20–90% of drive) |
| Tap cadence (bulk) | Does background tapping help bulk flow *at all* here, and at what cost in flow variability and balance noise? Direction genuinely unknown (§3.2) |
| Cutoff margin | How much of the flow regime survives cutoff as landed-after-cutoff mass — and does the required margin scale with flow rate (§1.2's claim, tested as the RPM × margin interaction) |

And the excluded parameters, each with its better route (§1.5):

| Excluded | Route | Why not a screen factor |
|---|---|---|
| Q, R | Identify from traces (§1.3) | Estimator, not plant (test 2); degenerate pair — only the ratio matters |
| KP, KI, trim authority bound | IMC center from the screen's feed factor, then bounded BO (§4.3) | Trim-phase only (test 3); their optimum is conditional on the remainder the margin leaves |
| Balance settling wait | One-off step-response test | Measurement protocol (test 2); the dedicated test costs minutes, a factorial cell costs dispenses |
| Stopping band / spec tolerance | Application spec or policy (§4.3) | Effect monotone by construction (test 1) |
| ERM vibration | Held out of round 1 (§1.5) | Corrupts the mass signal most; becomes factor E in the resolution-V variant (§5.4) once duty-cycled reads exist |
| Tap energy / single-tap increment | Per-powder increment-distribution measurement (§1.3) | A distribution to estimate, not an effect to detect; trim-phase resolution floor |

### 5.2 The design: 2^(4−1), resolution IV, 8 corners + 4 centers

Half fraction of the 2^4 grid, generator `D = ABC` (defining relation
`I = ABCD`), plus center points:

| | Factor | − level | + level | Center | Rule for setting the levels |
|---|---|---|---|---|---|
| A | `tilt_bulk` (° from horizontal) | 20 | 50 | 35 | Range-find inside the servo band: − just above sustained-flow onset, + just below flooding/spill |
| B | Auger RPM | 60 | 240 | 150 | About 20% and 80% of the usable band: stall below it, erratic flow or flooding above it |
| C | Tap cadence in bulk (Hz) | 0 (off) | 5 | 2.5 | Cadence = 1000/(`TAP_ON_MS` + `TAP_OFF_MS`); the 0 level tests whether bulk tapping is needed at all (switch − to 1 Hz once presence is established) |
| D | Cutoff margin (mg at a 500 mg target) | 10 | 75 | 42.5 | −: slightly above filter lag × flow rate at the slowest corner; +: covers the largest post-cutoff landed mass observed in range-finding at the fastest corner, plus 3σ |

The eight corners (coded, then in real units):

| Run | A | B | C | D = ABC | tilt (°) | RPM | tap (Hz) | margin (mg) |
|---|---|---|---|---|---|---|---|---|
| 1 | − | − | − | − | 20 | 60 | 0 | 10 |
| 2 | + | − | − | + | 50 | 60 | 0 | 75 |
| 3 | − | + | − | + | 20 | 240 | 0 | 75 |
| 4 | + | + | − | − | 50 | 240 | 0 | 10 |
| 5 | − | − | + | + | 20 | 60 | 5 | 75 |
| 6 | + | − | + | − | 50 | 60 | 5 | 10 |
| 7 | − | + | + | − | 20 | 240 | 5 | 10 |
| 8 | + | + | + | + | 50 | 240 | 5 | 75 |
| C1–C4 | 0 | 0 | 0 | 0 | 35 | 150 | 2.5 | 42.5 |

Three replicates of each corner plus the 4 center points = 28
dispenses per block; at 2–4 min per full dose cycle that is roughly
1–2 hours — one unattended evening, leaving room for the §5.3 foldover
block on a second.

Protocol — the part that makes this a designed experiment rather than
28 dispenses:

- **One powder lot, one target mass** (e.g. 500 mg of the xanthan gum
  surrogate on the existing 0.1 mg-class balance). The screen is per
  powder class × dose regime; the mg-trace and multi-gram regimes get
  their own screens if and when they matter.
- **Trim frozen at current defaults, ERM off, settling wait fixed and
  conservative** — every measured difference then belongs to A–D.
- **Randomized run order**, with the center points pinned near
  positions 1, 10, 19, 28: they estimate curvature *and* monitor
  within-block drift (compaction, humidity uptake).
- **Hopper topped up on a fixed cadence** (the feed factor drifts with
  fill level); log fill level, ambient humidity, and whether powder
  was recycled from earlier runs (recycling changes its state).
- Corners 4 and 7 (high RPM, minimal margin) are deliberately
  aggressive and will sometimes overshoot. On a surrogate-powder test
  rig an overshoot is not a lost sample but a *measurement* of the
  stopping transient — cheaply mapping the failure boundary is exactly
  why the screen precedes BO.

Responses per run, and what consumes each (§4.2's table made
concrete): `t_bulk`, `t_trim`, `t_total`; signed final error and an
overshoot flag; **landed-after-cutoff mass** (settled final mass minus
the estimate at cutoff — the §1.2 stopping transient, whose regression
on B is the first margin-scaling law); bulk flow-rate mean and SD from
the trace (feed factor → IMC plant gain); event flags (stall/bridge,
flood, spill, jam → safe-set boundary); replicate SD per corner
(heteroscedastic GP noise); and the full §2 log schema per run (BO
initialization data).

### 5.3 What is estimable, the alias trade, and the analysis

Resolution IV means the eight corners estimate all four **main effects
free of two-factor interactions** (mains alias only with three-factor
terms, assumed negligible). The six two-factor interactions arrive in
three aliased pairs — a hard constraint of any 4-factor half fraction,
and the complementary-pair structure is fixed no matter which physical
factor takes which letter:

- tilt×RPM + tap×margin
- **tilt×tap + RPM×margin** — contains §1.2's expected coupling
- tilt×margin + RPM×tap

Because RPM×margin is *expected* to be large (in-flight mass scales
with flow rate), a large second alias string is confirmation of §1.2 —
but attributing it strictly requires the **foldover**: a second block
on the complementary eight corners (equivalently, rerun with the
margin column's signs reversed). The two blocks combine into the full
2^4 with every interaction individually estimable, and the block
(night) effect lands on the four-factor interaction — on nothing we
care about. On the cohesive surrogate (xanthan gum), tilt×tap is
plausible too, so plan both nights; on a free-flowing metal surrogate
the first block alone may settle it.

Analysis, in order:

1. Replicated corners give **pure error** (16 df), so effects get real
   t-tests rather than only a half-normal plot; the centers-vs-corners
   contrast tests curvature. Significant curvature is fine — the GP
   models it — it only warns against using the linear fit as the map.
2. Fit the same model to **log s² per corner** (dispersion effects):
   which settings make flow erratic is the accuracy half of the story
   and feeds the heteroscedastic noise model directly.
3. Decision rules: a factor null on both the mean and dispersion
   responses is fixed at its cheap/fast level and dropped from the BO
   (each dropped dimension saves real dispenses). Overshoot flags vs.
   (B, D) give the first empirical margin-scaling curve. Stall/flood
   corners set the BO box bounds and initial safe set. All runs seed
   the GP.

### 5.4 The five-factor variant, for when ERM is promoted

When the ERM vibration amplitude enters (cohesive powders, once
duty-cycled actuate–pause–read protects the balance), do not bolt a
fifth factor onto the 8-run design: a `2^(5−1)` half fraction with
`I = ABCDE` is **resolution V** — 16 corners with every two-factor
interaction clear of every other — for the same two-block hardware
budget as 8 runs plus a foldover. That is the natural round-2 design
on xanthan gum.
