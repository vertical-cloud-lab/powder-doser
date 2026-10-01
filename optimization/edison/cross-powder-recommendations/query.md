# Edison query: does a 7-powder characterization dataset change our salt-derived MPC / stop-response recommendations?

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
