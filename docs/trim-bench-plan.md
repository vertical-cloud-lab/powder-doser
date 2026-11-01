# Bench test plan: real data for the trim-phase methods

*Written for the request on [PR #154](https://github.com/vertical-cloud-lab/powder-doser/pull/154)
for real (hardware) data on trickle-tap PI performance and on the
chance-constrained increment method proposed in
[`trim-dispensing.md`](trim-dispensing.md). Every test below runs on the
existing doser rig (Pico W + Tic T500 auger, tap solenoid, tilt servos,
A&D HR-100A) and is sized so its result can actually change a decision.*

---

## 0. What real closed-loop data exists today, and why it is not enough

Two things have to be said precisely, because they define the work:

1. **No PI controller has ever run on the hardware.** Every real dose to date
   was produced by `main_three_phase.py`'s fixed-increment scheme (bulk 360°
   cycles → fine ~30–45° cycles → 2-tap cycles, each followed by settle and
   read). The KF + rate-PI trickle with the predictive cutoff — the thing the
   sim studies call the "deployed" `trickle_tap` controller — exists only in
   the twin (`optimization/benchmarks/bangbang.py` on the PR #124 branch).
   Getting "real data on PI performance" therefore starts with a port (§4).

2. **The real dose sample is n = 12.** Across all 23 battery runs, the usable
   closed-loop doses on a conveying powder are the two salt Block G triplets
   (2026-08-06, 2026-08-12, 1 g target) and the six salt Block H doses
   (2026-09-03, 50/200 mg targets, recovered in commit `81bbe75`):

   | | n | ended over target | strict >+5 mg | within ±5 mg | E[max(E,0)] | median E | worst over |
   |---|---:|---:|---:|---:|---:|---:|---:|
   | pooled salt doses | 12 | 4 (33 %) | 3 (25 %) | 9/12 | 2.9 mg | −1.3 mg | +13.3 mg |

   The Wilson 95 % CI on that 33 % is **[14 %, 61 %]**. The simulation's headline
   comparison is 30.4 % (rate-PI) vs 8.8 % (chance-constrained); n = 12 cannot
   distinguish those, and n = 12 spread over three targets and two firmware
   read paths barely constrains either one alone. That is the gap this plan
   closes.

   For what it is worth, the real pooled numbers (33 % over, E[max(E,0)]
   2.9 mg) sit right on top of the sim's deployed-controller row (30.4 %,
   3.4 mg) — but from a *different* controller at *different* targets, so treat
   the agreement as encouraging, not confirming.

Characterization data that already exists and gets reused here: per-run
rotation/tap/refeed yield trials in `data/battery/*/trials_*.csv` (medians per
tilt, but too few reps per condition to give p95s), pre-move balance drop
captures, and the 2026-09-03 new-hood environment survey (0.077 mg quiet
jitter, zero shocks in 240 s, −3.6…+2.6 mg/min thermal drift).

## 1. Ground rules for every test

**Prerequisites (from the 2026-09-03 block-H handoff):**

- Calibrate the HR-100A with a 100 g class E2/F1 weight — it has not been
  calibrated since the fume-hood move. Log the cal in the run record.
- Empty the collection beaker (~1.8 g of salt left in it).
- Record the environment survey line before each session; read its gate
  against the planned dose duration (the stock verdict is calibrated for
  multi-minute Block G doses).
- The `battery_runs` collection has a duplicate document for the 17:04
  2026-09-03 run — exclude one copy in any analysis that counts runs.

**Statistics.** Hardware doses cannot be seed-paired the way the sim's are, so
McNemar-style paired inference is unavailable and every comparison is
unpaired: Wilson CIs on rates, two-proportion tests between arms, Wilcoxon on
the signed error, plus a logistic regression of overshoot on method with
session, run-order index, and hopper-fill covariates. Interleave arms within a
session in ABBA blocks so drift and fill level cannot masquerade as a method
effect. Score everything with the one-sided scorecard from the trim study:
P(E>0), P(E>+5 mg), E[max(E,0)], yield in [−5, 0] mg, median E, max positive
excess, dose time.

**Logging upgrade (P0, code-only, do before any campaign).** The run JSON
records per-dose aggregates but not per-cycle state; per-cycle detail exists
only in the raw serial log. Extend the dose runner to emit one structured
record per cycle: phase, commanded action (auger deg + rpm, taps), settled
mass before/after, settle wait actually used, stable-frame fraction during the
read, timestamps. Two reasons: (i) every future dose then doubles as
calibration data — each (commanded, delivered) pair updates the increment
method's yield model and scores the KF's innovations for free; (ii) overshoot
post-mortems become attributable to a specific action instead of a dose-level
guess. Keep retaining the raw serial + poll traces alongside.

## 2. Tier A — characterization (no controller changes)

These are the three bench measurements `trim-dispensing.md` §7 asked for, plus
two cheap ones the new hood makes possible. They feed *both* methods: the KF's
plant model and the increment method's yield model come from the same numbers.

**A1. Identify `tau_bal` in the configured response mode** *(~half a session)*
Place and remove small class weights (10, 20, 50 mg, 1 g) with tweezers while
streaming the balance at its maximum rate; ≥20 steps per mass. Fit a
first-order lag + dead time per step; report the distribution, not a point.
Repeat with the auger spinning at trickle rpm and during tap bursts. Also
read out and document the HR-100A's configured response/filter mode — the
datasheet (~0.7 s) and the pre-move drop tests (~0.16 s) disagree by 4.4×,
worth 22.7 mg at trim flow, and the configurable response mode is the likely
explanation. *Gates:* the KF's `tau_bal_belief`, the rate methods' margins,
and whether §4's B4 mode-switch test spans a useful lag range.

**A2. Noise, drift, and the actuation penalty** *(piggybacks on A1's session)*
240 s quiet captures at session start/middle/end (drift model + Allan
deviation), then captures while the auger runs at trickle rpm and while
tapping, with and without powder flowing. Deliverables: the real at-rest vs
actuating noise floor (the study assumes 0.5 vs 8 mg — the 16× at-rest
advantage is a load-bearing input to the increment method's case), the
stable-frame fraction in each state, and a drift-vs-settle-time curve that
sets how long a settled read is actually worth waiting for (the thermal drift
means a longer settle is not automatically a better read).

**A3. Single-action yield distributions — the terminal quantum**
*(~2 h per powder; salt first)*
From rest at the trim tilt, command single actions and record the settled
delta, **including the zeros**: auger increments {2°, 5°, 11°, 22°, 45°, 90°,
180°} and single taps + 2-tap bursts, n ≥ 40 per condition. Alternate lip
state in blocks — "charged" (immediately after a 1-rev prime) vs "depleted"
(after tapping until dry) — because the study's most load-bearing uncertain
parameter is `trigger_risk` (the chance any command dislodges a charged lip,
set to 0.5 in sim by matching p95s, never measured). Deliverables per
condition: mean, CV, P(zero), p95. This directly seeds
`YieldModel` priors, pins `trigger_risk`, and tests two published claims: that
shrinking 45°→5° only halves the p95 (35.6→17.7 mg in sim), and that a tap
delivers ~6.5 mg mean / ~21.7 mg p95. It is also the measurement §6's
"±5 mg needs a ~0.8 mg quantum" spec stands or falls on.

**A4. Post-halt drain, separated from in-flight mass** *(~half a session)*
Trickle at {6, 12, 18} auger rpm, halt, and log the settled mass at +2, +5,
+10 s after halt; n ≥ 20 per rpm. Run a cup-swap variant (swap the collection
cup at the halt instant, weigh both) to split lip drain from powder already in
flight, per the Edison review's protocol. The +26 mg twin drain figure has no
hardware confirmation, and the review notes no published measurement of
post-halt discharge from an inclined auger lip exists — this one is novel.

**A5. Slug statistics during trickle** *(~half a session)*
60–120 s continuous runs at {6, 12, 18} rpm over the streaming balance. With
0.077 mg quiet jitter against ~6 mg slugs, individual arrival events are now
resolvable at low rate: count events and step sizes from the trace
(deconvolving with A1's lag), and compute the variance-to-mean ratio in
windows against the compound-Poisson prediction. This tests the assumption
the whole §1 regime argument rests on — and if real discharge is
*over*-dispersed relative to Poisson, §6's quantum requirements are
understated, which the team should want to know early.

## 3. Tier B — closed-loop campaigns

**B0. Baseline campaign, current firmware untouched** *(n = 40; one session)*
Salt, targets 200 mg and 1 g (20 each), current three-phase parameters, new
bracket read path. Purpose: pin *today's* overshoot rate with a usable CI
(n = 40 at p̂ ≈ 25 % gives roughly [14, 40] %) and anchor the power analysis
for B1/B2. This is also the control arm every later comparison refers back
to, taken after the hood move rather than before it.

**B1. Rate-PI trickle-tap campaign** *(n = 60; interleaved with B2)*
After the §4 port: salt, same targets, the KF + rate-PI trickle with the
`m̂ + r̂τ + kσ ≥ target − margin` cutoff and tap endgame, at the twin's
deployed settings. Instrument the internals per dose: r̂ vs realized rate,
σ, the r̂ ≥ 0 clamp count, and the three cutoff-budget terms — the twin
diagnostic claims the fixed 35 mg margin does the safety work and the
KF terms contribute ~33 %; that claim becomes measurable on hardware.

**B2. Chance-constrained increment campaign** *(n = 60 at α = 0.05;
interleaved with B1 in ABBA blocks)*
The `largest_safe_rev` loop from `optimization/trim/estimators.py`, host-side:
settled read → largest command with P(delivered > budget) ≤ α → command →
repeat; hard interlock at target; tap arm gated the same way. Seed the yield
model from A3, update online from each (commanded, delivered) pair, and log
the model state per decision so miscalibration is visible dose-by-dose
(realized delivery vs predicted p95).

**Power.** For the sim's 30 % vs 9 % gap, a two-proportion test needs ~55
doses per arm at 80 % power (~73 at 90 %); 60/arm is the target, and at
block-H pace (17–64 s per 50–200 mg dose plus handling) an arm is roughly one
2–3 h session. If B0 lands materially below 30 %, re-run the power
calculation before committing to B1/B2 sizes — at 25 % vs 9 % the requirement
grows to ~86/arm. The continuous error distribution carries more information
per dose than the binary rate, so report both; the Wilcoxon comparison will
resolve before the proportion test does.

**B3. The α dial** *(n = 20 per point at α ∈ {0.20, 0.10, 0.02}; one session)*
The proposal's central promise is that α is a *calibrated* knob. Twenty doses
per point cannot pin each rate, but monotonicity and slope are a trend test:
fit realized overshoot vs α by logistic regression across all 120 α-doses
(including B2's 60 at 0.05). If realized overshoot does not track α, the
method loses its main selling point regardless of how B2 scored.

**B4. Physical balance-lag robustness — the cheapest strong falsification**
*(15–20 doses per method per mode; one session)*
The study's strongest claim is that the increment method is flat under
balance-lag mismatch (4–9 % across τ_bal 0.16–1.0 s) while rate feedback
degrades 29 %→54 %. The HR-100A's configurable response mode makes that
testable without touching any model: run both controllers with the balance in
FAST and in SLOW response mode, *without* re-tuning either. Prediction on
record: the rate-PI's overshoot rate moves with the mode switch; the
increment method's does not. This is the highest information-per-dose test in
the plan.

**B5. Second powder** *(stretch; n = 20–30 per arm)*
Repeat B1/B2 on AlSi10Mg once the tilt servo fault is cleared (its one valid
battery run shows ~3× the salt tap quantum, i.e. the hard case for §6), or on
sodium sulfate as a free-flowing contrast. Metal-powder handling rules apply.

## 4. The port (code work, no bench time)

To produce real PI data at all, the twin's `trickle_tap` controller has to
run against the rig. Recommended shape: **host-side on the Pi**, driving the
existing firmware primitives over serial (`r <deg>`, `t`, `w`, `z`, and the
continuous velocity mode with its poll stream) — CPython, easy to iterate,
and the poll plumbing already writes `polls_*.csv`. The increment method needs
only the settled-read/rotate cycle the fine phase already uses, plus the
sizing rule; the PI port needs the KF fed by the instantaneous stream.

Acceptance before any campaign dose: (i) hardware-in-the-loop replay — feed
recorded poll traces through the twin's `MassRateLagKF` and the host port and
require identical outputs; (ii) five smoke doses with the safety interlock
active and a hand on the e-stop; (iii) a pinned-parameter test as in the
block-H work, so campaign arms differ only in the controller.

## 5. Order and effort

| step | bench time | blocked by |
|---|---|---|
| P0 logging upgrade + §4 ports | 0 (1–2 days code) | — |
| A1 + A2 (lag, noise, drift) | 1 session | cal weight |
| B0 baseline campaign | 1 session | P0 |
| A3 + A4 (+A5 if time) quantum/drain | 1–2 sessions | — |
| B1 + B2 interleaved campaigns | 2 sessions | ports, A3 priors |
| B3 α sweep | 1 session | B2 |
| B4 response-mode robustness | 1 session | A1 |

Roughly seven bench sessions for the full plan; A1+A2+B0 alone (two
sessions) already replace the n = 12 baseline and settle the τ_bal question
that both method families depend on.

## 6. What each result would change

- **A1**: τ_bal ≈ 0.16 s → rate methods gain real margin and the sim's 0.7 s
  rows overstate their fragility; τ_bal ≥ 0.4 s → the deployed margins are
  undersized and the increment method's at-rest advantage grows.
- **A3**: if a 2–5° command's p95 is well under 10 mg (sim says it is not),
  a software-only path to ±5 mg reopens and §6's actuator conclusion softens;
  if confirmed, the outlet redesign is the priority and α cannot be chosen
  aggressively.
- **A5**: over-dispersion beyond compound-Poisson → §6's quantum spec tightens
  further; tighten the sim and re-derive.
- **B1 vs B2**: the decision. Adopt the increment method for the trim phase if
  it cuts P(E>0) by ≥ half at ≤ +60 s median dose time; otherwise keep rate-PI
  and take the α machinery as the tap gate only.
- **B3**: no monotone α response → the yield model is miscalibrated on
  hardware; fix the model before drawing any B2 conclusion.
- **B4**: if the increment method also degrades under the mode switch, the
  study's robustness argument is wrong on hardware and the whole proposal
  reverts to "a knob, at a time cost".
