Question: # Edison query: does a 7-powder characterization dataset change our salt-derived MPC / stop-response recommendations?

Job: `job-futurehouse-paperqa3-high` (LITERATURE_HIGH)
Submitted: 2026-08-11 (PR #131). Pulls the issue #116 uniform-powder battery
dataset (7 powders) alongside the salt-only physics characterization done in this
PR, and asks whether the multi-powder evidence revises the recommendations from
two prior Edison reviews (MPC data-collection plan; rapid-dispense stop-response
critique).

## What we want

We have two bodies of experimental data on ONE open-source gravimetric powder
doser and we want a HIGH-EFFORT, citation-backed answer to a specific question:

> **Given cross-powder characterization data, do our earlier salt-only
> recommendations still hold, and specifically — do the "protocol upgrades" and
> the MPC data-collection strategy need to change?**

Act as a skeptical reviewer grounded in the powder-handling / loss-in-weight
(LIW) feeder / gravimetric micro-dosing / DEM-of-screw-conveyor literature.
Please answer, with citations, the numbered questions in the last section. Do
NOT re-derive which control paradigm to use (a prior review already selected a
phase-switched MPC-style architecture); focus on whether the cross-powder
evidence changes *what data to collect* and *what the controller/observer must
model*.

## THE PLANT (context)

An Archimedean auger tube conveys powder from a rotating hollow-tube hopper; a
stepper drives the auger (0–90 RPM); a solenoid tapper gives discrete ~60 ms
impulsive taps at the tube lip; a servo tilts the dispense tube 0–90° ("tilt";
0° = horizontal, 90° = vertical; some drivers speak "plate degrees" = tilt/2).
Powder falls into a cup on an A&D HR-100A analytical balance (0.1 mg display
quantum, ~10.4 Hz raw serial stream including unstable-flagged frames). The
balance is the only process sensor. Dosing goal: ±2 mg today, ±1 mg target, on
0.25–2 g doses. An empty auger tube weighs 56.716 g; full it can exceed the
scale's 102 g capacity, so absolute fill is not always weighable in situ.

## DATASET A — cross-powder "uniform battery" (issue #116, n=1 run/powder)

One FIXED test sequence run identically on 7 powders, with a closed-loop
three-phase controller whose parameters are FROZEN at salt-tuned values for
EVERY powder (this is deliberate: a transfer/robustness test, not per-powder
tuning). Blocks per powder: A baseline noise (8 static reads @45°); B static
hold (15 s @0/45/90°, no actuation); C feed factor (6×360° @30 RPM per tilt
0/45/90°); D speed sweep (3 rev @15/45/90 RPM @45°); E tap (8 single taps @0°
and 45°, each after a 360° re-feed); F vibration (SKIPPED — DRV2605L
unavailable); G three-phase closed-loop 3×1.000 g doses.

Cross-powder summary (feed factor in mg/rev at tilt 0/45/90; tap in mg/tap @45°;
mean 1 g dose error under the frozen salt-tuned controller):

| Powder | feed mg/rev @0/45/90 | best RSD | speed trend 15→90 RPM | tap mg @45 | mean 1 g dose err | dose status |
|---|---|---|---|---|---|---|
| calcium-lactate | 47.3 / 198.3 / 232.2 | 2.2% @45 | 190→129 (−33%) | 20.36 | −26.5 mg | 3× stalled |
| xanthan-gum | 23.7 / 161.2 / 186.8 | 4.0% @90 | 233→106 (−55%) | 13.61 | −32.9 mg | 3× stalled |
| carboxymethyl-cellulose | 2.6 / 26.3 / 9.3 (peaks @45) | 9.1% @45 | 23→29 (+23%) | 0.15 | −43.2 mg | 3× stalled |
| salt | 5.6 / 17.1* / 24.9* | 12.5% @0 | drift-entangled | 3.05 | +0.2 mg | 2 ok, 1 overshoot |
| white-rice-flour | 3.75 / 12.78 / 37.15 | 22% @45 | 19→37 (+94%) | 0.11 | −137.9 mg | 3× cycle-budget |
| sodium-alginate | 0.75 / 9.58 / 10.87 | 8% @45 | 11→13 (+17%) | 0.24 | −291.5 mg | 3× cycle-budget |
| brown-rice-flour | 0.30 / 0.25 / 0.20 (no tilt dep) | below res. | 0/0/2.6 mg | 0.16 | ~−999 mg | 3× stalled |

\* salt block-C feed factor is a LOWER BOUND (intra-run drift; see below).

Key facts from Dataset A (a prior Edison review already softened the wording of
several of these; we report them here as observed):
- Feed factor spans ~3 orders of magnitude (232 → <0.3 mg/rev) on identical
  hardware and identical parameters.
- Speed dependence of mass-per-rev is powder-dependent in SIGN: falls with RPM
  for calcium lactate (−33%) and xanthan (−55%); rises for white rice flour
  (+94%); ~flat for alginate/CMC.
- Tap yield @45° tracks feed factor: 20 mg (Ca-lactate) / 14 mg (xanthan) for
  high-feed powders, but <0.25 mg (not resolved from zero) for low-feed powders.
- CMC feed factor is NON-MONOTONIC in tilt — peaks at 45° (26 mg/rev), falls
  2.8× at vertical; per-rev at 90°: 39.0, 7.4, 4.0, 1.8, 1.4, 2.5 mg (a strong
  first-revolution transient).
- No powder avalanches through a STATIONARY auger even fully vertical (block B =
  0 at all tilts, all powders): flow is auger-gated, not gravity-gated.
- Under the frozen salt-tuned controller, ONLY salt lands on target; dose error
  is NOT monotone in feed factor (Ca-lactate conveys 13× salt yet misses by
  −27 mg; alginate conveys LESS than salt yet misses by −292 mg). Two failure
  modes: `cycle-budget` (bulk halts early on salt's 0.12 g anticipation, fine
  can't close the gap) for slow powders; phase-3 `stalled` (fine oversteps the
  handover, then taps at 0° where the tap quantum collapses) for fast powders.
- Salt control DRIFTS within one 17-min run (dose errors −4.7 → −3.5 → +8.8 mg
  monotone; block C vs block E feed factor at matched tilt/RPM disagree 2.7× for
  salt but agree to within ~10% for the other six powders). Cause unresolved.
- n = 1 battery run per powder (except brown rice flour, 2 augers); within-run
  revolutions/taps/doses are technical replicates, not independent preparations.
- Vibration block (F) never ran; no real metal powders (AlSi10Mg, Si) yet.

## DATASET B — salt-only physics characterization (this PR, deeper, still n small)

On coarse granulated NaCl only, we ran three deeper experiments and two prior
Edison reviews already critiqued them:

1. **Single-tap lip-inventory characterization** (2 sessions). Per trial: tilt →
   1 auger revolution (lip re-feed / reset) → 10 SINGLE taps, weighed one at a
   time. Session 1 (half-drawn tube, 4 tilts 0–25°): successive taps DEPLETE the
   lip — e.g. 25° gave 19.2 → 10.0 → 6.5 → ... → 1.3 mg over 10 taps, well fit by
   yᵢ = y∞ + A·rⁱ⁻¹ (A 1.6–16.6 mg, r 0.38–0.75, small non-depleting floor
   y∞ ≈ 1–3 mg). Tap-1 gain scaled ~7× with tilt (2.9 → 19.2 mg, 0→25°). One
   revolution delivers far more than 10 taps can extract (33% of a revolution's
   mass at 25°). Session 2 (freshly refilled brim-full tube, 8 tilts 0–70°): the
   depletion signature VANISHED — taps flat/slightly rising across the 10, and
   per-tap yield was ~10–20× LOWER than session 1 at matched tilt, WHILE auger
   feed-per-rev went UP. We attribute this to fill level / packing state moving
   the two actuators in OPPOSITE directions, but fill and the act of refilling
   are confounded. Best trim operating point on this salt shifted to 30–50° (2.7
   mg/tap at CV 38% @50°), not the 0–25° every dose recipe had used.

2. **Rapid-dispense stop-response** (n=10; 25/40/50/60/70° × 2; single session).
   Rapid actuation (55 RPM + tap-while-rotating) halted the same loop iteration
   the balance first read ≥ 0.5 g, then a 15 s settling tail. Result: total
   overshoot past 0.5 g was +86 to +181 mg; decomposed, trigger quantization was
   only 1.6–17.4 mg and the rest was afterflow. Afterflow ÷ flow-at-halt =
   τ = 1.07 ± 0.20 s with NO detected tilt trend (steeper gave LESS overshoot
   because this salt feeds slower past ~40°). Settling to within 2 mg took
   0.7–1.5 s; a +5 s re-weigh agreed to ≤ 0.3 mg. A single 50→60° tilt move once
   shook +25.4 mg loose (tilt change is itself a dispensing actuator).

3. **Single continuous PID on auger speed** with a 1.1 s flow-anticipation term:
   hit +1.2 mg on a half-drawn tube (2026-07-29) but +57 mg mean (n=3) on a
   brim-full tube (2026-07-30) at IDENTICAL gains — same fill-level sensitivity,
   auger side. Telemetry shows delivery is QUANTIZED: ~110 mg "slugs", one per
   auger revolution at 45 RPM, up to 27 mg landing in one 100 ms sample, with
   troughs of zero flow between — the per-flight discharge, not a continuous rate.

## PRIOR RECOMMENDATIONS WE WANT RE-EXAMINED

From the MPC data-collection review (salt-anchored): model the plant with an
explicit in-flight-inventory state, a tube-lip-inventory state `x_lip` (taps
drain, rotations refill), and a feed factor ff(tilt, fill, ω) with a
Fourier-in-auger-phase term for pulsation; identify per-powder feed maps + stop
tests + tap maps; run a full campaign on 3–5 anchor powders then a reduced
~60–90 min transfer set per new powder, indexing priors by bulk/tapped density
and flow-function-coefficient (FFC).

From the stop-response critique ("protocol upgrades" for the NEXT session):
(a) randomize tilt order and halt masses (0.1–2.0 g), not a fixed 0.5 g;
(b) deconfound actuators — auger-only vs tap-only vs combined stop-response;
(c) track fill level every trial as a primary factor;
(d) add tilt-only "blank" trials each session and interlock tilt moves away from
final approach; (e) measure the balance's own step response with dropped known
masses to separate instrument settling from powder settling; (f) test 2–3 more
powders before generalizing; treat τ ≈ 1 s as a seed for a state observer /
Smith predictor, not a fixed offset; handoff recipe leave-full-speed at
target − 200 mg, dribble to target − 20 mg, verify at +2 s, then single taps.

## QUESTIONS (please answer each, with citations)

1. **Does Dataset A change the data-collection priorities?** The salt-only plan
   proposed 3–5 "anchor" powders + a reduced transfer set indexed by density/FFC.
   Dataset A shows feed factor spanning 3 orders of magnitude, sign-flipping
   speed dependence, and non-monotonic tilt for CMC. Given that, is a
   density/FFC-indexed transfer-learning approach still defensible, or does the
   sign-flip in speed dependence and the CMC tilt non-monotonicity imply the
   powder space is not smoothly interpolable and each powder needs its own
   identification? What single powder descriptor(s) would the literature expect
   to best predict (i) feed factor magnitude, (ii) the SIGN of the speed
   dependence, (iii) tap efficacy?

2. **Is the τ ≈ 1 s afterflow constant likely powder-invariant or
   powder-specific?** τ was measured on salt only. Dataset A shows the per-flight
   slug mass and feed factor vary 3 orders of magnitude across powders. Does the
   LIW/auger-overrun literature predict the afterflow TIME constant (as opposed
   to the afterflow MASS) to be roughly conserved across powders at fixed
   geometry/RPM, or to vary with cohesion/angle of repose/flow regime? What would
   the minimum cross-powder stop-response design be to settle this?

3. **The "quantized slug" delivery (one ~110 mg discharge per revolution) is the
   binding constraint on a continuous-rpm controller.** Does the literature
   support treating the per-revolution discharge as a modeled discrete event
   (halt on auger PHASE, in a trough) rather than trying to meter a continuous
   rate near the endpoint? Is per-flight discharge mass a stable, identifiable
   quantity across fill level, and how is it best measured?

4. **Fill level moved the auger and the tap in OPPOSITE directions on salt.** A
   single scalar "fill factor" multiplying both actuators is therefore wrong. How
   should fill level enter the model/observer given only a 0.1 mg cup balance and
   no in-hopper sensor (the tube can exceed scale capacity)? Is cumulative
   dispensed mass an adequate fill surrogate, or do refill/repack events reset
   the state discontinuously (our session-1 vs session-2 tap reversal suggests
   they do)?

5. **Do the stop-response "protocol upgrades" still stand, or should any be
   re-prioritized given Dataset A?** In particular: is per-trial fill tracking
   now the single highest-value addition (since fill dominates both actuators)?
   Should the actuator-deconfounding factorial be run per-powder or only on
   anchors? Given salt's INTRA-run drift (feed factor changing 2.7× in 17 min),
   is there a stationarity/conditioning pre-check every session should pass
   before data is trusted?

6. **Controller architecture implications.** The frozen salt-tuned three-phase
   controller failed on all 6 non-salt powders in two distinct modes
   (cycle-budget for slow, phase-3 stall for fast). Beyond "tune per powder,"
   does the cross-powder evidence favor (i) an online feed-factor/ff estimator
   that adapts within a single dose, (ii) a gain-schedule on a measured
   descriptor, or (iii) a short per-powder identification burst before each dose?
   What does the LIW literature show about within-run adaptation vs a-priori
   calibration for materials with this much variability and intra-run drift?

7. **What is now the smallest experimental program** that would let us build and
   validate a controller that hits ±2 mg across this powder range — given finite
   bench time, one balance, and n≈1 per powder so far? Please give a concrete,
   prioritized experiment list and the quantitative gates to advance between
   stages.


# Cross-Powder Characterization and Its Impact on Salt-Derived MPC / Stop-Response Recommendations

## Executive Summary

The seven-powder uniform battery (Dataset A) materially revises several salt-only recommendations while strengthening others. The core MPC architecture (phase-switched, observer-based) remains sound, but the **data-collection plan, model structure, and protocol upgrades all require revision** in light of the 3-order-of-magnitude spread in feed factor, sign-flipping speed dependence, non-monotonic tilt behaviour, and the two distinct failure modes observed across powders. Below, each numbered question is answered with citation-backed reasoning.

| Recommendation area | Original salt-only recommendation | Cross-powder evidence | Verdict (holds/revise/strengthen) | Priority change |
|---|---|---|---|---|
| Per-powder identification vs transfer learning | Run full identification on 3–5 anchor powders, then reduced transfer sets for new powders, indexed by density/FFC | Dataset A shows ~3 orders of magnitude spread in feed factor, sign-flipping speed dependence, and non-monotonic tilt response (CMC peaks at 45°, then drops at 90°), so powder behavior is not smoothly ordered by a single descriptor; literature supports density/conditioned bulk density as a good predictor of feed-factor magnitude, but not a sufficient predictor of all dynamics, while flowability/compressibility help explain variability and hopper-emptying effects (li2020predictiveperformanceof pages 36-40, li2020predictiveperformanceof pages 49-53, bostijn2019amultivariateapproach pages 22-26, jonessalkey2023reviewingtheimpact pages 8-10) | Revise | Increase: reduced transfer sets are still useful for screening/priors, but each new powder now needs at least a short direct identification burst before closed-loop use |
| Feed-factor map contents | Identify per-powder feed maps ff(tilt, fill, ω) with explicit in-flight and lip states | Dataset A strongly supports this: feed factor changes massively by powder and tilt, and speed dependence changes sign by powder; literature also shows hopper level/stress changes effective density and therefore feed factor, and screw-speed effects can be nontrivial and material-dependent (bostijn2019amultivariateapproach pages 10-14, fathollahi2024improvingcontinuouslossinweight pages 1-2, bascone2020hybridmechanisticempiricalapproach pages 11-14, bascone2020hybridmechanisticempiricalapproach pages 25-30) | Strengthen | Increase to top priority |
| Descriptor-based priors | Use bulk/tapped density and FFC to index priors across powders | Cross-powder evidence does not kill descriptor-based priors, but it narrows their role: literature shows conditioned/bulk density predicts feed-factor magnitude well, and FFC/flowability help predict variability/stability; neither is enough to predict sign of speed dependence or tilt non-monotonicity from current evidence (li2020predictiveperformanceof pages 36-40, li2020predictiveperformanceof pages 49-53, bostijn2019amultivariateapproach pages 22-26, jonessalkey2023reviewingtheimpact pages 8-10) | Revise | Keep as medium-priority support layer, not primary model-transfer mechanism |
| Stop-response tests | Measure stop tests and treat τ≈1 s as a seed for observer/Smith-predictor design, not a fixed offset | Dataset A makes powder invariance of τ less plausible because per-rev slug mass and flow regime differ dramatically across powders; literature on feeders emphasizes powder-dependent effective density, fill level, and flow regime changes, while dead-time compensation remains sensible if re-identified per material/condition (bascone2020hybridmechanisticempiricalapproach pages 11-14, fathollahi2021developmentofa pages 4-5, li2020predictiveperformanceof pages 36-40) | Hold, but revise scope | Increase: cross-powder stop-response is now mandatory before assuming a shared τ |
| Protocol upgrade: randomize tilt order and halt masses | Randomize order of tilt and stop mass to reduce drift/confounding | Dataset A salt drift within one run and strong powder-specific tilt effects make fixed-order protocols even less trustworthy; literature shows feeder response changes with hopper stress/fill and operating point, so randomization remains necessary (bostijn2019amultivariateapproach pages 10-14, fathollahi2024improvingcontinuouslossinweight pages 1-2, fathollahi2024improvingcontinuouslossinweight pages 4-6) | Strengthen | Increase |
| Protocol upgrade: deconfound actuators | Separate auger-only, tap-only, and combined stop-response trials | Dataset A shows tap efficacy tracks powder/feed regime and collapses toward zero for some powders, so actuator-separable characterization is even more important; otherwise controller failure modes cannot be attributed correctly (supported mechanistically by distinct screw-fed vs density/state-dependent behaviors in feeder literature) (bascone2020hybridmechanisticempiricalapproach pages 11-14, fathollahi2021developmentofa pages 4-5, fathollahi2021developmentofa pages 12-13) | Strengthen | Increase to top priority |
| Protocol upgrade: track fill level every trial | Track fill level as a primary factor | Dataset B already suggested fill affects auger and tap differently; Dataset A plus literature on feeder densification/refill disturbances makes fill/state tracking the single highest-value protocol addition. Hopper stress and refill perturb density, feed factor, and drift (bostijn2019amultivariateapproach pages 10-14, fathollahi2024improvingcontinuouslossinweight pages 1-2, fathollahi2024improvingcontinuouslossinweight pages 2-4, fathollahi2024improvingcontinuouslossinweight pages 6-7, li2020predictiveperformanceof pages 66-73, bascone2020hybridmechanisticempiricalapproach pages 11-14) | Strengthen | Increase to highest priority |
| Protocol upgrade: tilt-only blanks and avoid tilt moves near endpoint | Add tilt-only blank trials; interlock tilt changes away from final approach | Dataset B found a tilt move can release mass; Dataset A’s strong tilt sensitivity across powders means this remains critical and likely powder-specific (owen2009predictionofscrew pages 11-13, owen2009predictionofscrew pages 10-11) | Hold | No change to high priority |
| Protocol upgrade: measure balance step response | Characterize balance-only settling separately from powder settling | Cross-powder evidence does not weaken this; if powders differ strongly in afterflow/landing dynamics, separating instrument response from powder response becomes even more valuable for observer design | Hold | Slight increase |
| Continuous-rate endpoint control | Use anticipation/observer logic rather than naive continuous-RPM control near endpoint | Dataset A and B reinforce that endpoint control cannot assume a smooth continuous rate; B shows quantized per-revolution delivery and A shows powder-dependent feed maps; DEM/mechanistic literature also describes screw transport as structured by angular position, inclination, fill, and flow regime rather than ideal continuous discharge (owen2009predictionofscrew pages 10-11, owen2009predictionofscrew pages 1-2, owen2009predictionofscrew pages 2-4) | Strengthen | Increase |
| Stationarity/session qualification | Implicitly assume session data are usable after normal setup | Dataset A salt drift and Dataset B fill/repack reversals imply a formal pre-check is needed before trusting a session; literature reports refill/fill-state disturbances and long relaxation of density/stress fields (fathollahi2024improvingcontinuouslossinweight pages 6-7, fathollahi2024improvingcontinuouslossinweight pages 4-6, bascone2020hybridmechanisticempiricalapproach pages 11-14) | Revise | Add new high-priority gate before any characterization run |
| Validation breadth | Test 2–3 more powders before generalizing | Dataset A already supplies multi-powder evidence and shows the need for broader validation, not less; literature likewise emphasizes strong material dependence of feeder performance (bostijn2019amultivariateapproach pages 22-26, jonessalkey2023reviewingtheimpact pages 8-10, owen2009predictionofscrew pages 1-2) | Strengthen | Increase from desirable to essential |
| Controller tuning strategy | Collect data for a phase-switched MPC-style controller with observer states for in-flight and lip inventory | Dataset A supports the architecture choice but shows the observer/model must include powder-specific ff maps, fill/state dependence, and actuator-specific trim efficacy; literature supports material-specific calibration plus adaptive correction rather than one frozen calibration (bascone2020hybridmechanisticempiricalapproach pages 11-14, fathollahi2021developmentofa pages 4-5, fathollahi2021developmentofa pages 12-13, fathollahi2021developmentofa pages 13-14) | Hold, but expand modeled states | Increase |


*Table: This table compares the original salt-only recommendations with what the seven-powder dataset now shows. It highlights which recommendations remain valid, which must be revised, and which become higher priority for building a robust cross-powder dosing controller.*

---

## Question 1: Does Dataset A Change the Data-Collection Priorities?

**Yes — substantially.** The salt-only plan proposed 3–5 anchor powders with a reduced transfer set indexed by bulk/tapped density and FFC. Dataset A shows that powder space is **not smoothly interpolable** by these descriptors alone:

- **Feed factor magnitude** spans ~3 orders of magnitude (232 mg/rev for calcium lactate at 90° down to <0.3 mg/rev for brown rice flour). The literature consistently identifies **conditioned bulk density (cBD)** as the best single predictor of feed-factor magnitude across screw feeders (R² > 0.9 in one 14-material study), with bulk and tapped density positively correlated with the maximum feed factor (li2020predictiveperformanceof pages 49-53, li2020predictiveperformanceof pages 36-40). This is mechanistically expected: a constant-volume screw flight delivers mass proportional to the in-flight packing density.

- **Sign of speed dependence** is not predicted by density or FFC. Dataset A shows calcium lactate and xanthan gum (high feed factor, likely free-flowing in the auger) exhibit **decreasing** mass-per-rev with increasing RPM (−33% and −55%, respectively), while white rice flour shows a **+94% increase**. The literature reports only a "weak negative correlation" between screw speed and FFmax that remains consistent across tested powders in pharmaceutical twin-screw feeders (bostijn2019amultivariateapproach pages 22-26), and no known single descriptor predicts the sign flip. DEM studies show that the balance between recirculatory avalanching flow (dominant at low inclination/low fill) and swirling bed flow (dominant at high inclination) shifts with speed, fill, and particle friction properties (owen2009predictionofscrew pages 11-13, owen2009predictionofscrew pages 10-11), suggesting that the sign of speed dependence is governed by the **flow regime** (flood-fed vs. starve-fed, cohesive arch vs. free avalanche) rather than a simple scalar property.

- **Tap efficacy** tracks feed factor magnitude (20 mg/tap for high-feed powders, <0.25 mg for low-feed powders), which is consistent with tap yield being proportional to the mass of loosely retained lip inventory — itself set by the feed factor at the operating tilt.

- **Tilt non-monotonicity** (CMC peaks at 45°, drops 2.8× at 90°) is unique among the seven powders. DEM studies confirm that inclination changes the flow pattern from a bulldozer-heap regime (low angles) to a uniform-depth swirling bed (high angles), with axial velocity dropping linearly up to ~60° then levelling off (owen2009predictionofscrew pages 11-13, owen2009predictionofscrew pages 10-11). CMC's non-monotonicity likely reflects a cohesive arch or bridging interaction at high tilt that is not captured by a monotonic density/FFC index.

**Recommendation:** A density/FFC-indexed transfer-learning approach is **defensible for initialising priors** on feed-factor magnitude, but **not sufficient** for predicting speed-dependence sign, tilt optima, or tap efficacy. Each new powder requires at minimum a **short direct identification burst** (a few revolutions at 2–3 tilts and 2–3 speeds, plus a tap sequence) before closed-loop dosing. The "reduced ~60–90 min transfer set" should be retained but understood as an identification experiment, not a mere validation of a transferred model. The most predictive descriptors from the literature are: (i) conditioned bulk density for feed-factor magnitude (li2020predictiveperformanceof pages 49-53, bostijn2019amultivariateapproach pages 22-26), (ii) FFC/flowability for feed-rate variability and stability (jonessalkey2023reviewingtheimpact pages 8-10), and (iii) compressibility (Carr Index, C@15kPa) for feed-factor decay with hopper emptying (bostijn2019amultivariateapproach pages 22-26). No established descriptor predicts speed-dependence sign; this must be measured directly.

---

## Question 2: Is τ ≈ 1 s Afterflow Constant Powder-Invariant or Powder-Specific?

**Almost certainly powder-specific.** The afterflow time constant τ was measured only on coarse granulated NaCl. Several lines of reasoning predict powder dependence:

1. **Physical mechanism:** Afterflow comprises (a) material already in the screw flights continuing to discharge after motor stop (inertial rundown), and (b) material draining from the lip/tube exit under gravity. The mass of (a) scales with the per-flight slug mass, which spans 3 orders of magnitude across Dataset A powders. While the *time* for inertial rundown depends primarily on screw/motor deceleration (geometry-dominated), the *draining time* of residual lip material depends on powder cohesion, angle of repose, and packing state — all powder-specific.

2. **Literature evidence:** Hybrid mechanistic-empirical models of screw feeders (Bascone et al.) show that the effective density within the screw is a function of vertical stress and compressibility, and is modelled with powder-specific parameters (ρ₀, κ) (bascone2020hybridmechanisticempiricalapproach pages 11-14). Hopper/feeder dynamics during transients are powder-dependent: materials with better flowability (high permeability, low cohesion) recover faster from disturbances than poorly flowing materials (li2020predictiveperformanceof pages 114-118). This implies that the settling/draining portion of afterflow is cohesion-dependent.

3. **Dataset A implication:** For calcium lactate (232 mg/rev), a single revolution delivers ~20× the mass of salt at matched tilt. The afterflow *mass* will therefore be far larger. Whether the afterflow *time* is conserved depends on whether the drainage rate scales proportionally — an untested assumption.

**Minimum cross-powder stop-response design:** Run at least 3 powders spanning the feed-factor range (e.g., calcium lactate, salt, sodium alginate) × 2 tilts × 2 speeds, with n ≥ 5 stops per condition. This gives ~60 stop trials, achievable in 2–3 hours. Measure afterflow mass and time to within-2-mg settling separately for each. If τ varies by >2× across powders, it must be a per-powder identified parameter in the observer.

---

## Question 3: Quantized Per-Revolution Discharge — Should It Be Treated as a Discrete Event?

**Yes — the literature strongly supports this.** DEM simulations of single-flight screw conveyors show that powder is transported as a structured heap or bed confined between successive screw flights, with the discharge at the outlet occurring as the flight passes the exit plane (owen2009predictionofscrew pages 1-2, owen2009predictionofscrew pages 2-4). Owen and Cleary's DEM study describes the flow as a "bull dozer pushing a circulating heap" at low inclinations, transitioning to a uniform-depth bed at high angles — in both regimes, the material is bounded by the screw pitch geometry and discharges discretely as each flight clears the outlet (owen2009predictionofscrew pages 4-8, owen2009predictionofscrew pages 10-11).

Dataset B confirms this: ~110 mg slugs at one per revolution, with up to 27 mg in a single 100 ms sample and troughs of zero between. This is the **per-flight discharge** phenomenon, not measurement noise. Treating this as a modelled discrete event and halting in a trough (at a known auger phase) is therefore well-motivated by both theory and observation.

**Stability across fill level:** DEM studies show that average axial speed is "almost invariant to changes in volumetric fill level" (owen2009predictionofscrew pages 10-11), but the pharmaceutical feeder literature shows that higher fill levels increase effective density at the screw entrance through powder densification, increasing the mass carried per flight (bostijn2019amultivariateapproach pages 10-14, fathollahi2024improvingcontinuouslossinweight pages 1-2, li2020predictiveperformanceof pages 66-73). Therefore, per-flight discharge mass is **fill-level-dependent** and must be re-identified or estimated online as fill changes.

**Best measurement approach:** Run a set of single-revolution trials (one full revolution from a known phase, weigh the deposit) at multiple fill levels and tilts. A minimum of 5 revolutions × 3 fill levels × 3 tilts = 45 trials per powder. Phase-locked stopping (halting at a known angular position in a trough) will reduce endpoint variability by up to the full slug amplitude (~110 mg for salt, potentially much larger for high-feed powders).

---

## Question 4: Fill Level Moves Auger and Tap in Opposite Directions — How Should Fill Enter the Model?

The observation that higher fill level **increased** auger feed-per-rev but **decreased** tap yield on salt means a single scalar "fill factor" multiplying both actuators is structurally wrong. This is consistent with the literature: higher fill level increases compressive stress at the screw entrance, densifying powder in the flights and increasing mass throughput per revolution (fathollahi2024improvingcontinuouslossinweight pages 1-2, fathollahi2024improvingcontinuouslossinweight pages 6-7, bascone2020hybridmechanisticempiricalapproach pages 11-14). Meanwhile, a brim-full tube likely packs the lip zone more tightly, reducing the loosely retained inventory that taps can dislodge.

**Model recommendation:** Fill level should enter the observer as **two separate gain multipliers**: one for the auger channel (monotonically increasing with fill, modelled via an effective density ρ_eff(σ_v) relationship as in Bascone et al. (bascone2020hybridmechanisticempiricalapproach pages 11-14)), and one for the tap channel (monotonically decreasing with fill, modelled as the available lip inventory x_lip). This requires the observer to maintain **separate state estimates** for in-tube fill and lip inventory.

**Is cumulative dispensed mass an adequate fill surrogate?** Partially. Cumulative dispensed mass gives a monotone-decreasing estimate of remaining tube fill, which is useful between refills. However, **refill/repack events reset the state discontinuously** — the session-1 vs session-2 tap reversal in Dataset B is direct evidence, and the LIW literature extensively documents refill-induced perturbations that change density profiles, require ~300 seconds to stabilize, and cause feed-factor excursions (fathollahi2024improvingcontinuouslossinweight pages 6-7, fathollahi2024improvingcontinuouslossinweight pages 4-6). Therefore, refill events must be treated as **state resets** in the observer, not smooth continuations. After any refill, a short re-identification sequence (e.g., 3–5 single revolutions + a tap sequence at the operating tilt) should re-calibrate the fill-dependent gains before resuming closed-loop dosing.

---

## Question 5: Do the Stop-Response Protocol Upgrades Still Stand?

**All six protocol upgrades stand; several are elevated in priority by Dataset A.**

**(a) Randomize tilt order and halt masses:** Strengthened. Salt's intra-run drift (feed factor changing 2.7× in 17 min, dose errors trending monotonically) makes fixed-order protocols unreliable. The literature confirms that feeder response changes with operating history and stress state (fathollahi2024improvingcontinuouslossinweight pages 6-7, fathollahi2024improvingcontinuouslossinweight pages 4-6).

**(b) Deconfound actuators (auger-only vs tap-only vs combined):** Elevated to **top priority**. Dataset A shows tap efficacy collapses to <0.25 mg for low-feed powders (below balance resolution), meaning the tap actuator is effectively absent for those materials. The controller's phase-3 stall failure mode for fast powders is directly attributable to assuming tap efficacy at 0° tilt that doesn't exist. Actuator deconfounding should be run per-powder, not only on anchors, because the tap/auger balance varies qualitatively across powders.

**(c) Track fill level every trial:** Now the **single highest-value addition**. Fill dominates both actuators in opposite directions (Dataset B), and the LIW literature identifies fill-induced stress/densification as the primary source of feed-factor drift and refill disturbances (bostijn2019amultivariateapproach pages 10-14, fathollahi2024improvingcontinuouslossinweight pages 1-2, fathollahi2024improvingcontinuouslossinweight pages 2-4, bascone2020hybridmechanisticempiricalapproach pages 11-14). A practical protocol: weigh the loaded tube before and after each block (when within scale capacity), or track cumulative dispensed mass with explicit resets at refills.

**(d) Tilt-only blanks and interlock tilt moves:** Retained at high priority. Dataset B showed a single tilt move released +25.4 mg. Dataset A's strong tilt sensitivity across all powders means tilt changes are themselves dispensing events, powder-specifically.

**(e) Balance step response with known masses:** Retained. Separating instrument settling from powder settling becomes more important when afterflow characteristics vary by powder.

**(f) Test 2–3 more powders before generalizing:** Already accomplished by Dataset A (7 powders). However, metal powders (AlSi10Mg, Si) remain untested, and given the extreme variability observed, they should be added before any τ or control parameter is treated as universal.

**Stationarity/conditioning pre-check:** Given salt's 2.7× intra-run drift, every session should begin with a **stationarity gate**: run 3–5 matched single-revolution trials at a reference tilt/speed; if the per-revolution mass changes by more than ±15% across the set, the tube must be re-conditioned (e.g., 10 conditioning revolutions) and the gate repeated before trusting any subsequent data.

---

## Question 6: Controller Architecture Implications

The frozen salt-tuned controller failed on all 6 non-salt powders via two distinct modes: **cycle-budget exhaustion** (slow powders: bulk phase halts too early on salt's anticipation threshold, fine phase can't close the gap) and **phase-3 stall** (fast powders: fine phase oversteps handover, then taps at 0° where tap quantum collapses). This argues strongly against a single frozen calibration.

The literature on feeder control points toward a hybrid of options (i) and (iii):

**(i) Online feed-factor estimator (favored).** The pharmaceutical micro-feeder literature demonstrates successful feed-forward control using a pre-characterized displacement-feed-factor profile, combined with iterative learning control that updates the profile online — achieving <1.5% deviation from setpoint across diverse materials (fathollahi2021developmentofa pages 4-5, fathollahi2021developmentofa pages 12-13, fathollahi2021developmentofa pages 13-14). This architecture is directly analogous to what the open-source doser needs: a per-powder feed-factor profile (ff as a function of tilt, fill, and speed) used as a feed-forward model, with an online estimator that corrects the profile within-dose based on balance observations.

**(iii) Short per-powder identification burst before each dose.** Given the 3-order-of-magnitude feed-factor range, the controller needs at minimum a rough estimate of the powder's feed factor before attempting a dose. A "probe phase" of 2–3 revolutions at the operating tilt would suffice to set the correct gain scale. This is compatible with the phase-switched architecture: insert a "Phase 0" probe before the bulk dispense phase.

**(ii) Gain-schedule on a measured descriptor** is useful as an initialisation prior (density predicts ff magnitude well (li2020predictiveperformanceof pages 49-53, bostijn2019amultivariateapproach pages 22-26)) but cannot replace direct measurement because it does not predict speed-dependence sign or tilt optima.

**Within-run adaptation vs a-priori calibration:** The LIW literature relies on a-priori calibration (feed-factor profiles) for steady-state operation and switches to volumetric (open-loop) mode during transients like refills (li2020predictiveperformanceof pages 36-40). However, the micro-feeder control literature shows that adding iterative/adaptive correction on top of calibration significantly improves performance, especially for materials with high feed-rate fluctuations (fathollahi2021developmentofa pages 12-13, fathollahi2021developmentofa pages 13-14). Given the observed intra-run drift on salt (2.7× in 17 min), **within-dose online adaptation is essential**, not optional. A recursive least-squares or exponentially weighted moving average estimator on ff, updated every revolution, is the minimum viable approach.

---

## Question 7: Minimum Experimental Program for ±2 mg Across This Powder Range

Given one balance, finite bench time, and n ≈ 1 per powder, the following prioritized program is recommended:

**Stage 1: Stationarity and Fill-Level Calibration (salt only, ~2 hours)**
- Establish a stationarity gate protocol (5 matched revolutions, ±15% criterion).
- Characterize fill-level effect on per-rev mass at 3 fill levels × 2 tilts (30 trials).
- Characterize fill-level effect on tap yield at same 3 fills × 2 tilts (30 trials).
- **Gate:** Demonstrate <20% variation in per-rev mass across consecutive matched trials before proceeding.

**Stage 2: Cross-Powder Stop-Response (3 powders, ~3 hours)**
- Select calcium lactate (high feed), salt (medium), sodium alginate (low feed).
- Auger-only stops: 5 stops × 2 tilts × 2 speeds = 20 per powder.
- Tap-only stops (where tap is resolvable): 5 stops × 2 tilts = 10 per powder.
- **Gate:** Determine whether τ varies >2× across powders. If yes, τ must be per-powder identified.

**Stage 3: Per-Powder Identification Burst Protocol (all 7 powders, ~1 hour each)**
- Per powder: 5 revolutions × 3 tilts × 2 speeds = 30 trials (feed-factor map).
- Per powder: 5 taps × 2 tilts = 10 trials (tap map).
- Per powder: 1 tilt-blank trial.
- **Gate:** Feed-factor map RSD <25% at best operating point; tap yield resolvable from zero at ≥1 tilt.

**Stage 4: Adaptive Controller Development and Single-Powder Validation (salt + 1 fast + 1 slow, ~4 hours)**
- Implement Phase 0 probe (2–3 revolutions) + online ff estimator + phase-locked stopping.
- Validate ±2 mg on n = 10 doses of salt.
- Validate on calcium lactate (fast) and sodium alginate or white rice flour (slow).
- **Gate:** ≥8/10 doses within ±2 mg on salt; ≥6/10 on each non-salt powder.

**Stage 5: Cross-Powder Validation (remaining 4 powders, ~4 hours)**
- Run n = 5 doses per powder with the adaptive controller.
- **Gate:** ≥4/5 within ±2 mg for powders with resolvable feed factors; for brown rice flour (below resolution), document minimum achievable dose and accuracy.

**Stage 6: Metal Powder Extension (AlSi10Mg, Si, ~2 hours each)**
- Run Stage 3 identification + Stage 4 validation on each metal powder.
- **Gate:** Same as Stage 4.

**Total estimated bench time:** ~20–25 hours across ~6 sessions. This is aggressive but achievable if each session is well-planned and the stationarity gate is enforced. The key quantitative gates ensure that data quality is verified before advancing, and that the controller is validated on powders spanning the full 3-order-of-magnitude range before being declared general.

---

## Summary of Revisions to Prior Recommendations

The cross-powder evidence **does not invalidate** the MPC architecture or the core data-collection strategy, but it **materially revises** several assumptions:

1. **Density/FFC indexing** is useful for initialising feed-factor magnitude priors but cannot predict speed-dependence sign, tilt optima, or tap efficacy — each powder needs direct identification.
2. **τ ≈ 1 s** should be treated as powder-specific until cross-powder stop-response data prove otherwise.
3. **Per-revolution discrete discharge** is well-supported by DEM literature and Dataset B; phase-locked stopping should be the default endpoint strategy.
4. **Fill level** must enter the model as separate gain multipliers for auger and tap channels, with refills treated as state resets.
5. **Fill tracking** is now the single highest-priority protocol upgrade.
6. **Online feed-factor estimation** (within-dose adaptation) is essential given the observed variability and drift, not merely desirable.
7. A **stationarity pre-check** should gate every session before data are trusted.


References

1. (li2020predictiveperformanceof pages 36-40): Tianyi Li. Predictive performance of loss-in-weight feeders for continuous powder-based manufacturing. ArXiv, Jan 2020. URL: https://doi.org/10.7282/t3-6tgx-8f63, doi:10.7282/t3-6tgx-8f63. This article has 2 citations.

2. (li2020predictiveperformanceof pages 49-53): Tianyi Li. Predictive performance of loss-in-weight feeders for continuous powder-based manufacturing. ArXiv, Jan 2020. URL: https://doi.org/10.7282/t3-6tgx-8f63, doi:10.7282/t3-6tgx-8f63. This article has 2 citations.

3. (bostijn2019amultivariateapproach pages 22-26): N. Bostijn, J. Dhondt, A. Ryckaert, E. Szabó, W. Dhondt, B. V. Snick, B. V. Snick, V. Vanhoorne, C. Vervaet, and T. D. Beer. A multivariate approach to predict the volumetric and gravimetric feeding behavior of a low feed rate feeder based on raw material properties. International Journal of Pharmaceutics, 557:342–353, Feb 2019. URL: https://doi.org/10.1016/j.ijpharm.2018.12.066, doi:10.1016/j.ijpharm.2018.12.066. This article has 89 citations and is from a domain leading peer-reviewed journal.

4. (jonessalkey2023reviewingtheimpact pages 8-10): Owen Jones-Salkey, Zoe Chu, Andrew Ingram, and Christopher R. K. Windows-Yule. Reviewing the impact of powder cohesion on continuous direct compression (cdc) performance. Pharmaceutics, 15:1587, May 2023. URL: https://doi.org/10.3390/pharmaceutics15061587, doi:10.3390/pharmaceutics15061587. This article has 35 citations.

5. (bostijn2019amultivariateapproach pages 10-14): N. Bostijn, J. Dhondt, A. Ryckaert, E. Szabó, W. Dhondt, B. V. Snick, B. V. Snick, V. Vanhoorne, C. Vervaet, and T. D. Beer. A multivariate approach to predict the volumetric and gravimetric feeding behavior of a low feed rate feeder based on raw material properties. International Journal of Pharmaceutics, 557:342–353, Feb 2019. URL: https://doi.org/10.1016/j.ijpharm.2018.12.066, doi:10.1016/j.ijpharm.2018.12.066. This article has 89 citations and is from a domain leading peer-reviewed journal.

6. (fathollahi2024improvingcontinuouslossinweight pages 1-2): Sara Fathollahi, Valjon Demiri, Theresa R. Hörmann-Kincses, Snjezana Maljuric, Julia Massoner, Greg Mehos, and Johannes G. Khinast. Improving continuous loss-in-weight feeding accuracy by a novel hopper design. Journal of Pharmaceutical Innovation, Sep 2024. URL: https://doi.org/10.1007/s12247-024-09858-2, doi:10.1007/s12247-024-09858-2. This article has 2 citations and is from a peer-reviewed journal.

7. (bascone2020hybridmechanisticempiricalapproach pages 11-14): Davide Bascone, Federico Galvanin, Nilay Shah, and Salvador Garcia-Munoz. Hybrid mechanistic-empirical approach to the modeling of twin screw feeders for continuous tablet manufacturing. Industrial & Engineering Chemistry Research, 59:6650-6661, Mar 2020. URL: https://doi.org/10.1021/acs.iecr.0c00420, doi:10.1021/acs.iecr.0c00420. This article has 16 citations and is from a peer-reviewed journal.

8. (bascone2020hybridmechanisticempiricalapproach pages 25-30): Davide Bascone, Federico Galvanin, Nilay Shah, and Salvador Garcia-Munoz. Hybrid mechanistic-empirical approach to the modeling of twin screw feeders for continuous tablet manufacturing. Industrial & Engineering Chemistry Research, 59:6650-6661, Mar 2020. URL: https://doi.org/10.1021/acs.iecr.0c00420, doi:10.1021/acs.iecr.0c00420. This article has 16 citations and is from a peer-reviewed journal.

9. (fathollahi2021developmentofa pages 4-5): Sara Fathollahi, Julia Kruisz, Stephan Sacher, Jakob Rehrl, M. Sebastian Escotet-Espinoza, James DiNunzio, Benjamin J. Glasser, and Johannes G. Khinast. Development of a controlled continuous low-dose feeding process. AAPS PharmSciTech, Oct 2021. URL: https://doi.org/10.1208/s12249-021-02104-9, doi:10.1208/s12249-021-02104-9. This article has 7 citations and is from a peer-reviewed journal.

10. (fathollahi2024improvingcontinuouslossinweight pages 4-6): Sara Fathollahi, Valjon Demiri, Theresa R. Hörmann-Kincses, Snjezana Maljuric, Julia Massoner, Greg Mehos, and Johannes G. Khinast. Improving continuous loss-in-weight feeding accuracy by a novel hopper design. Journal of Pharmaceutical Innovation, Sep 2024. URL: https://doi.org/10.1007/s12247-024-09858-2, doi:10.1007/s12247-024-09858-2. This article has 2 citations and is from a peer-reviewed journal.

11. (fathollahi2021developmentofa pages 12-13): Sara Fathollahi, Julia Kruisz, Stephan Sacher, Jakob Rehrl, M. Sebastian Escotet-Espinoza, James DiNunzio, Benjamin J. Glasser, and Johannes G. Khinast. Development of a controlled continuous low-dose feeding process. AAPS PharmSciTech, Oct 2021. URL: https://doi.org/10.1208/s12249-021-02104-9, doi:10.1208/s12249-021-02104-9. This article has 7 citations and is from a peer-reviewed journal.

12. (fathollahi2024improvingcontinuouslossinweight pages 2-4): Sara Fathollahi, Valjon Demiri, Theresa R. Hörmann-Kincses, Snjezana Maljuric, Julia Massoner, Greg Mehos, and Johannes G. Khinast. Improving continuous loss-in-weight feeding accuracy by a novel hopper design. Journal of Pharmaceutical Innovation, Sep 2024. URL: https://doi.org/10.1007/s12247-024-09858-2, doi:10.1007/s12247-024-09858-2. This article has 2 citations and is from a peer-reviewed journal.

13. (fathollahi2024improvingcontinuouslossinweight pages 6-7): Sara Fathollahi, Valjon Demiri, Theresa R. Hörmann-Kincses, Snjezana Maljuric, Julia Massoner, Greg Mehos, and Johannes G. Khinast. Improving continuous loss-in-weight feeding accuracy by a novel hopper design. Journal of Pharmaceutical Innovation, Sep 2024. URL: https://doi.org/10.1007/s12247-024-09858-2, doi:10.1007/s12247-024-09858-2. This article has 2 citations and is from a peer-reviewed journal.

14. (li2020predictiveperformanceof pages 66-73): Tianyi Li. Predictive performance of loss-in-weight feeders for continuous powder-based manufacturing. ArXiv, Jan 2020. URL: https://doi.org/10.7282/t3-6tgx-8f63, doi:10.7282/t3-6tgx-8f63. This article has 2 citations.

15. (owen2009predictionofscrew pages 11-13): P.J. Owen and P.W. Cleary. Prediction of screw conveyor performance using the discrete element method (dem). Powder Technology, 193:274-288, Aug 2009. URL: https://doi.org/10.1016/j.powtec.2009.03.012, doi:10.1016/j.powtec.2009.03.012. This article has 358 citations and is from a domain leading peer-reviewed journal.

16. (owen2009predictionofscrew pages 10-11): P.J. Owen and P.W. Cleary. Prediction of screw conveyor performance using the discrete element method (dem). Powder Technology, 193:274-288, Aug 2009. URL: https://doi.org/10.1016/j.powtec.2009.03.012, doi:10.1016/j.powtec.2009.03.012. This article has 358 citations and is from a domain leading peer-reviewed journal.

17. (owen2009predictionofscrew pages 1-2): P.J. Owen and P.W. Cleary. Prediction of screw conveyor performance using the discrete element method (dem). Powder Technology, 193:274-288, Aug 2009. URL: https://doi.org/10.1016/j.powtec.2009.03.012, doi:10.1016/j.powtec.2009.03.012. This article has 358 citations and is from a domain leading peer-reviewed journal.

18. (owen2009predictionofscrew pages 2-4): P.J. Owen and P.W. Cleary. Prediction of screw conveyor performance using the discrete element method (dem). Powder Technology, 193:274-288, Aug 2009. URL: https://doi.org/10.1016/j.powtec.2009.03.012, doi:10.1016/j.powtec.2009.03.012. This article has 358 citations and is from a domain leading peer-reviewed journal.

19. (fathollahi2021developmentofa pages 13-14): Sara Fathollahi, Julia Kruisz, Stephan Sacher, Jakob Rehrl, M. Sebastian Escotet-Espinoza, James DiNunzio, Benjamin J. Glasser, and Johannes G. Khinast. Development of a controlled continuous low-dose feeding process. AAPS PharmSciTech, Oct 2021. URL: https://doi.org/10.1208/s12249-021-02104-9, doi:10.1208/s12249-021-02104-9. This article has 7 citations and is from a peer-reviewed journal.

20. (li2020predictiveperformanceof pages 114-118): Tianyi Li. Predictive performance of loss-in-weight feeders for continuous powder-based manufacturing. ArXiv, Jan 2020. URL: https://doi.org/10.7282/t3-6tgx-8f63, doi:10.7282/t3-6tgx-8f63. This article has 2 citations.

21. (owen2009predictionofscrew pages 4-8): P.J. Owen and P.W. Cleary. Prediction of screw conveyor performance using the discrete element method (dem). Powder Technology, 193:274-288, Aug 2009. URL: https://doi.org/10.1016/j.powtec.2009.03.012, doi:10.1016/j.powtec.2009.03.012. This article has 358 citations and is from a domain leading peer-reviewed journal.