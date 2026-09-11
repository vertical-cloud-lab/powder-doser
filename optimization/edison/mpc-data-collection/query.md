# Edison query: MPC for the powder doser + data requirements for controller design

Job: `job-futurehouse-paperqa3-high` (LITERATURE_HIGH)
Submitted: 2026-07-23 (PR #131, follow-up to the multi-objective control review in
`optimization/edison/query_out/query.answer.md` @ f5bf64c, per PR #124 discussion)

## Question

We are designing a Model Predictive Controller for an open-source, low-cost gravimetric
powder doser and need a HIGH-EFFORT, citation-backed treatment of (a) which MPC
formulations fit this system and (b) — most importantly — exactly WHAT DATA we must
collect, and HOW, to identify the models the controller needs. A previous literature
review already covered the general landscape (decentralized PID vs. RGA vs. LQR/H-inf vs.
MPC; multi-objective scalarization; BO for outer-loop tuning), and concluded MPC is the
natural framework; do NOT repeat that survey — go deep and specific on MPC design and
system identification / experiment design for THIS class of plant.

THE PLANT. An Archimedean auger (screw) conveys powder from a hopper through a tube; a
stepper motor drives the auger (0-55 RPM, position-controlled, we command discrete
rotation increments or continuous speed); a solenoid tapper delivers discrete impulsive
taps (configurable pulse trains: on-time, off-time, duty, count) that knock loose powder
from the tube lip; a vibration motor provides continuous agitation; a servo tilts the
dispensing tube/plate (0-25 degrees used so far; steeper = faster flow); everything
dispenses into a cup on a balance read over serial. The balance is the ONLY process
sensor: ~1 mg resolution, needs ~0.8 s settling before a "stable" reading, so mass
feedback is slow, quantized, and noisy relative to a 0.1-5 mg/s flow. The controller runs
on a Raspberry Pi Zero 2 W host and/or an RP2040 (Pico) microcontroller.

EMPIRICAL BEHAVIOR ALREADY OBSERVED (real runs, one cohesive test powder):
- Feed factor is grossly powder-dependent and uncertain a priori: measured ~0.029 g/rev
  against a 0.5 g/rev default guess (17x off). An online per-rev estimator converged fine.
- Strong periodic per-rev yield alternation (e.g. 0.048 g then 0.006 g on successive
  half-rev increments) — consistent with the auger flight fill/dump cycle, i.e. a
  rotation-angle-dependent (cyclostationary) feed rate, not white noise.
- In-flight/falling powder: in a continuous bulk phase at ~0.13 g/s, halting the auger
  still let +162 mg land during the 0.8 s settling window — a transport delay / in-flight
  inventory that any anticipative stop must model (an `anticipation_g` margin knob exists
  but is untuned).
- Discrete tap yields: ~2-5 mg per 2-tap burst at 0 degrees tilt, but ~57 mg per fine
  cycle (half-rev + 2 taps) at 22.5 degrees — actuator effects interact strongly with
  tilt, and taps deplete the tube lip unless the auger "re-feeds" it between taps.
- Two controllers exist today: a two-phase (coarse auger to 95% + tap trim; 1 g in 201 s,
  -2.8 mg error) and a three-phase draft (continuous bulk -> half-rev fine -> tap; 2 g in
  21 s but +26 mg overshoot with untuned parameters). We want MPC to get the 21 s speed
  WITH the few-mg accuracy.
- Overshoot is asymmetric and effectively a hard constraint: powder cannot be removed
  once dispensed. Tolerance today ±5 mg; goal ±1 mg; stretch ±0.1 mg.
- Contexts that shift dynamics but are not controlled: powder identity (salt, xanthan
  gum, flour now; metal AM feedstocks like AlSi10Mg later), hopper fill level, ambient
  humidity/temperature and the powder's exposure history (cohesion, caking, bridging).
- A characterization sweep already runs on-device: at each tilt angle it measures
  per-rotation yield distributions, tap-only yield distributions (with re-feed
  accounting), and balance noise baselines, with repeats; results land in MongoDB keyed
  by powder_id.

PLEASE COVER, WITH CITATIONS:

1. MODEL STRUCTURE for MPC of screw/auger powder feeding. What model classes does the
   literature use for loss-in-weight (LIW) and screw feeders in pharmaceutical continuous
   manufacturing and powder filling machines: integrating (mass = integral of feed rate)
   models with input nonlinearity (Hammerstein), feed-factor models ff(fill level, screw
   speed), transport delay / dead time representations, cyclostationary or
   angle-dependent screw pulsation models, and stochastic flow-noise models for cohesive
   powders (avalanching). How is the in-flight (falling) powder column modeled — pure
   time delay, first-order lag, or explicit in-flight inventory state? How are discrete
   impulsive actuators (taps) modeled alongside a continuous screw — impulse response
   with depletion state (tube-lip inventory that taps drain and rotations refill)?

2. MPC FORMULATION. Given one integrating output, asymmetric hard constraint (no
   overshoot), a terminal target (batch/shrinking-horizon dosing rather than continuous
   regulation), and hybrid inputs (continuous screw speed + integer tap counts): compare
   shrinking-horizon batch MPC / minimum-time formulations, chance-constrained or
   tube-based robust MPC for the stochastic flow (what back-off from target does the
   theory prescribe given flow variance?), hybrid/mixed-integer MPC vs. treating tap
   bursts as quantized inputs vs. phase-switched MPC (bulk MPC then tap-trim policy),
   stochastic MPC with feed-factor uncertainty, and economic MPC trading dose time
   against terminal error. Which is appropriate at our scale, and what horizon /
   discretization (time-based vs. event/rotation-based sampling) does the literature use
   when the measurement itself needs 0.8 s settling?

3. STATE ESTIMATION with only a slow noisy balance: Kalman filtering of mass to estimate
   instantaneous flow rate and in-flight inventory (LIW feeders do exactly this during
   refill); handling measurement quantization (1 mg) and settling (should we use
   non-stable readings with a noise model instead of waiting for stable ones?); online
   feed-factor / g-per-rev estimation (RLS, EKF, observer with forgetting) and its
   interaction with MPC (indirect adaptive MPC); detecting regime changes (bridging,
   empty hopper, caking) as fault detection.

4. DATA COLLECTION / SYSTEM IDENTIFICATION — the core deliverable. Specify the
   experiment battery we should run, mapped to the model parameters above:
   - What excitation signals for the auger (steps, staircases, PRBS/multisine on screw
     speed, single-increment dosing pulses) and what sampling/repeat counts are needed to
     identify feed factor, its fill-level dependence, per-rev periodicity, dead time, and
     flow-noise spectrum, given 1 mg / 0.8 s measurement limits?
   - Impulse-response mapping for taps: burst size/count/duty sweeps, tube-lip depletion
     and re-feed dynamics — how many repeats for usable variance estimates?
   - Fill-level dependence: draw-down experiments (run hopper from full to empty logging
     mass vs. rotations) as done for LIW feed-factor maps?
   - In-flight inventory / stop-response tests: halt-from-steady-flow experiments at
     several speeds and tilts to identify the anticipation mass?
   - Cross-actuator interaction coverage: full factorial vs. D-optimal / space-filling
     designs over (tilt, speed, tap config, vibration) — what does optimal experiment
     design for control (identification for control, "identify what the controller needs")
     say about where to spend runs?
   - Environmental/context logging: what humidity/temperature instrumentation and
     metadata do powder-flow studies show actually matters?
   - How much of this must be re-done per powder vs. transferred/adapted online
     (multi-powder model libraries, transfer learning between powders)?
   - Concretely: recommended dataset schema — signals to log per run and per event
     (timestamps, commanded vs. actual rotation, tap events, mass traces including
     non-stable samples, contexts) so the same data serves ID, MPC validation, and later
     BO.

5. VALIDATION + PRACTICALITY: closed-loop vs. open-loop validation metrics for dosing
   (terminal error distribution, time-to-dose, constraint violation rate); how the LIW
   literature benchmarks feeder controllers; and implementable toolchains at our compute
   scale (explicit MPC lookup tables, offline-optimized profiles with run-to-run update,
   do-mpc / acados / CasADi / GEKKO on a Pi Zero class host). Finish with a recommended
   phased plan: which experiments first, which model first, which MPC variant first, and
   what quantitative evidence would justify each step up in complexity.
