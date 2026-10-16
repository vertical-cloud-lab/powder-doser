# Edison query: feedback on the rapid-dispense stop-response characterization (2026-08-07)

Job: `job-futurehouse-paperqa3-high` (LITERATURE_HIGH)
Submitted: 2026-08-07 (PR #131; the report under review is
https://github.com/vertical-cloud-lab/powder-doser/pull/131#issuecomment-5221180886,
data/analysis committed at 2c98f59 in `data/stop-response/2026-08-07_salt/`)

## Question

We just ran a stop-response characterization on our open-source gravimetric powder doser
and want a HIGH-EFFORT, citation-backed CRITIQUE of the experiment and its
interpretation. Act as a skeptical reviewer from the powder-handling / loss-in-weight
(LIW) feeding / gravimetric dosing literature: tell us (a) whether our analysis and
conclusions are sound, (b) what confounds or alternative explanations we missed, (c) how
the protocol should be improved or extended, and (d) what the results imply for the
controller design. Do NOT re-survey control paradigms (a previous review already selected
a phase-switched MPC-style architecture); focus on THIS experiment.

THE PLANT (context). An Archimedean auger tube conveys powder (currently coarse
granulated NaCl, ~53-63 g load) from a rotating hollow tube hopper; a stepper drives the
auger (0-55 RPM); a solenoid tapper gives discrete ~60 ms impulsive taps at the tube lip;
a servo tilts the dispense tube 0-90 deg ("plate degrees"; steeper = closer to vertical);
powder falls into a cup on an A&D HR-100A balance (0.1 mg display quantum, ~10.4 Hz raw
serial stream including unstable-flagged frames). The balance is the only process
sensor. Goal accuracy for dosing: +/-2 mg today, +/-1 mg target, on 0.25-2 g doses.

THE EXPERIMENT UNDER REVIEW ("rapid-dispense stop-response", n = 10 trials, 25/40/50/60/70
plate deg x 2 replicates, randomized-ish order, single session, one tare per trial):

Protocol per trial: tilt to angle -> settled tare -> start "rapid pace" actuation
(continuous auger at 55 RPM + one solenoid tap every 3rd poll, i.e. tapping while
rotating) -> poll the raw ~10.4 Hz stream -> the FIRST sample reading >= 0.500 g triggers
an immediate halt of all actuation in the same loop iteration (ms-scale command latency)
-> record a 15 s raw settling tail -> stable weigh -> +5 s confirmation weigh.

One-time scale-noise baseline (60 s static raw stream): sd 0.59 mg over the window,
dominated by a slow -1.5 mg/min drift (post-tare relaxation); sample-to-sample sigma
0.012 mg. Caveat observed: the first ~14 s after a tare showed a decaying +/-20-45 mg
oscillation (unstable-flagged) of unidentified mechanical origin before going quiet.
During dispensing, high-frequency sigma is ~1.8 mg/sample (~150x the static floor), which
inseparably mixes vibration noise with real quantized slug arrivals.

RESULTS (trigger read = first sample >= 0.5 g; afterflow = settled - trigger read):

| tilt | rep | trigger read (g) | dispense time (s) | settled (g) | afterflow (mg) | total past 0.5 g (mg) | settle time (s) |
|---|---|---|---|---|---|---|---|
| 25 | 1/2 | 0.5137 / 0.5016 | 4.7 / 5.0 | 0.6439 / 0.5922 | +130 / +91 | +144 / +92 | 1.4 / 1.2 |
| 40 | 1/2 | 0.5145 / 0.5139 | 4.0 / 4.3 | 0.6809 / 0.6175 | +166 / +104 | +181 / +118 | 1.0 / 0.8 |
| 50 | 1/2 | 0.5058 / 0.5174 | 3.5 / 4.4 | 0.6731 / 0.6331 | +167 / +116 | +173 / +133 | 1.2 / 1.3 |
| 60 | 1/2 | 0.5084 / 0.5099 | 3.4 / 5.7 | 0.6217 / 0.6137 | +113 / +104 | +122 / +114 | 1.1 / 1.4 |
| 70 | 1/2 | 0.5079 / 0.5060 | 6.3 / 7.1 | 0.5858 / 0.6079 | +78 / +102 | +86 / +108 | 0.7 / 1.5 |

OUR INTERPRETATION (this is what we want critiqued):

1. The threshold trigger itself is nearly blameless: the first reading past 0.5 g
   overshoots the threshold by only 1.6-17.4 mg (sampling quantization of a 0.07-0.15 g/s
   stream at 10.4 Hz); nearly all error is powder already in flight / in the tube.
2. Afterflow collapses onto one constant: tau = afterflow / flow-rate-at-halt =
   1.07 +/- 0.20 s with NO tilt trend. Steeper tilts gave SMALLER overshoot only because
   this salt feeds slower there (feed rate peaks near 40-60 deg and falls at 70 deg,
   consistent with an earlier per-rev characterization). We read tau as an in-flight
   transport-delay/inventory constant, independently confirming the 1.1 s anticipation
   constant a PID controller had converged to.
3. Settling is fast and clean: 0.7-1.5 s to within 2 mg of final, confirmation weigh at
   +5 s agrees to <= 0.3 mg; no slow creep. Waiting longer than ~2 s after halt buys
   nothing.
4. Controller implication: a rapid threshold-stop cannot beat ~flow x 1.07 s of overshoot
   (80-180 mg at full speed), so halt at target - flow x tau; residual is slug
   quantization (+/-10-20 mg), to be closed by a tap/trim endgame. Recommended recipe:
   rapid bulk at 40-60 deg + anticipated early halt + settled verify at ~2 s.
5. Secondary observation: changing tilt 50->60 deg between trials once shook +25.4 mg
   loose (all other tilt moves <= 0.2 mg) — tilt moves can themselves dispense.

ADDITIONAL CONTEXT that may matter to the critique: n is only 2 per angle; all trials in
one session on one powder at one fill level (~120 g total tube mass, above the balance's
102 g capacity so the load could not be weighed); the flow-rate-at-halt used in the tau
computation is estimated from the last ~1 s of the mass ramp before the halt (same
quantized/noisy signal); the tap-while-rotating pattern means taps and auger flights are
confounded within a trial; trial order was tilt-blocked (both reps at one tilt run
together) so drift aliases onto tilt; prior sessions showed feed factor and tap yield are
strongly fill-level dependent, and per-rev delivery is quantized in ~100 mg slugs at
55 RPM on a full tube.

PLEASE PROVIDE, WITH CITATIONS WHERE THE LITERATURE SPEAKS:

1. VALIDITY. Is the tau = afterflow/flow ~ 1 s "constant" a sound reduction, or is it an
   artifact of afterflow and flow estimates sharing the same noisy signal
   (ratio-of-estimates bias, regression dilution)? With n=2 per angle, can "no tilt
   trend" be claimed? What statistical treatment does the LIW / feeder literature use for
   stop-response or dribble-phase characterization, and what n is typical?
2. PHYSICS. What does the literature say the post-halt afterflow actually consists of for
   screw/auger feeders (screw-tip dribble, in-fall column, lip avalanche, conveyor-tube
   holdup)? Is a single flow-proportional time constant the accepted model, or do
   fill-level, screw speed at halt, powder cohesion, or deceleration profile enter?
   Would a controlled ramp-down (vs. hard stop) reduce afterflow, per e.g. fill-head or
   vibratory dosing literature? Is the balance's own step-response/damping time
   (a ~1 s-class instrument transient) confounded with true powder afterflow, and how
   would one separate them (e.g. drop known masses, characterize the balance's dynamic
   response)?
3. PROTOCOL IMPROVEMENTS. Concretely: randomization/blocking across tilt, repeats needed
   for the claimed effects, varying halt-time within the ramp (the earlier data-collection
   plan called for randomized halt times — we used a fixed 0.5 g threshold instead; how
   much does that cost?), separating tap and auger contributions, and controlling/
   measuring fill level given the balance capacity limit.
4. CONTROLLER IMPLICATIONS. Given tau ~ 1 s and slug quantization ~10-20 mg residual: is
   "halt at target - flow x tau" the right anticipation form, or should it be
   state-based (estimated in-flight inventory via an observer) as in LIW refill
   compensation? How do commercial gravimetric fillers handle the coarse/fine handoff
   quantitatively (bulk-to-dribble switchover points, typical dribble-phase flow rates
   relative to target tolerance)? What does the literature suggest as the maximum bulk
   flow rate compatible with a +/-2 mg endpoint given a ~1 s stop lag and ~10 Hz
   single-sensor feedback?
5. Anything else a reviewer from the powder metering / precision dispensing / analytical
   balance dynamics literature would flag about this experiment or its conclusions.
