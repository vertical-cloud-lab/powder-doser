Question: We are designing a Model Predictive Controller for an open-source, low-cost gravimetric
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

Question: We are designing a Model Predictive Controller for an open-source, low-cost gravimetric
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

# MPC Design and System Identification for an Open-Source Gravimetric Powder Doser

## 1. MODEL STRUCTURE FOR MPC OF SCREW/AUGER POWDER FEEDING

### 1.1 Feed-Factor Models

The foundational model for screw-based powder feeding is the **feed factor** — the mass of powder dispensed per screw revolution (g/rev). In the loss-in-weight (LIW) feeder literature, the feed factor is defined as the ratio of measured feed rate to screw speed and serves as the core calibration parameter linking motor commands to delivered mass (bostijn2019amultivariateapproach pages 10-14). The instantaneous mass flow rate is then:

$$\dot{m}(t) = \mathrm{ff}(\cdot) \cdot \omega(t)$$

where ω is screw speed and ff(·) captures the dependence on operating conditions. This is structurally a **Hammerstein model**: a static nonlinearity (the feed-factor map) followed by an integrating linear dynamic (accumulated mass = integral of flow rate).

Critically, the feed factor is **not constant**. It depends on:

- **Hopper fill level**: Feed factor is maximal at full hopper and decays as the hopper empties. Bostijn et al. introduced the "feed factor profile" concept, characterizing FFmax (maximum feed factor at full hopper) and FFdecay (the fill percentage at which feed factor drops to 90% of maximum), finding that highly compressible powders show steeper decay (bostijn2019amultivariateapproach pages 22-26, bostijn2019amultivariateapproach pages 10-14, bostijn2019amultivariateapproach pages 14-18). Fathollahi et al. showed that hopper stress profiles directly influence bulk density at the screw interface, and that hopper design can homogenize these stresses to reduce fill-level sensitivity (fathollahi2024improvingcontinuouslossinweight pages 2-4).

- **Powder identity**: Across 15 pharmaceutical powders, PLS regression models using 25 material property descriptors (density, compressibility, flow properties) explained 81–97% of FFmax variance, demonstrating that feed factor is fundamentally powder-dependent (bostijn2019amultivariateapproach pages 22-26, bostijn2019amultivariateapproach pages 1-6).

- **Screw speed**: The dependence is weak (~−7% anti-correlation with FFmax) but measurable, suggesting mild shear-thinning or aerodynamic effects at higher speeds (bostijn2019amultivariateapproach pages 22-26).

- **Tilt angle** (specific to this doser): Your empirical data show tilt strongly modulates both continuous and tap yields (57 mg per fine cycle at 22.5° vs. ~5 mg at 0°), so tilt must enter as a scheduling variable in ff(tilt, fill, ω).

### 1.2 Cyclostationary Pulsation Model

Your observed alternating yields (0.048 g then 0.006 g on successive half-rev increments) are consistent with the auger flight fill/dump cycle. This is a **rotation-angle-dependent (cyclostationary) pattern**, not white noise. The appropriate model is a periodic lookup table or low-order Fourier expansion:

$$\mathrm{ff}(\theta) = \bar{\mathrm{ff}} + \sum_{k=1}^{K} a_k \cos(k\theta) + b_k \sin(k\theta)$$

indexed by auger angle θ (mod 2π). For your system, K=1–2 harmonics likely suffice. This argues strongly for **event-based (rotation-based) sampling** rather than purely time-based discretization.

### 1.3 Transport Delay and In-Flight Inventory

Your measurement of +162 mg landing during 0.8 s after auger halt is a combined transport delay and in-flight inventory effect. Three modeling options exist:

1. **Pure time delay**: m_measured(t) = m_dispensed(t − τ_d). Simple but cannot capture the exponential tail of powder settling.

2. **Dead time + first-order lag**: A transfer function e^{−τ_d s} / (1+τ_lag s) between dispensed and measured mass. This is the standard approach in pharmaceutical RTD modeling, where tank-in-series (TIS) models with dead time parameters (t_D, N tanks, mean residence time τ_TIS) are used to characterize continuous powder processes (gyurkes2023residencetimedistributionbased pages 1-2, gyurkes2023residencetimedistributionbased pages 4-6, gyurkes2023residencetimedistributionbased pages 6-7).

3. **Explicit in-flight inventory state**: An additional state variable x_flight representing powder that has left the auger but not yet reached the balance, with dynamics dx_flight/dt = ṁ_auger − ṁ_land. This is the most natural model for your system given the tilt-dependent fall trajectory and is analogous to the RTD-based process models used in continuous manufacturing where transfer functions capture interconnected CSTR-like mixing and plug-flow delay elements (rehrl2018controlofthree pages 1-4, rehrl2018controlofthree pages 4-8).

For your system, option 3 is recommended: the in-flight state scales with tilt angle and flow rate, is directly observable through stop-response tests, and provides the `anticipation_g` margin needed for overshoot-free stopping.

### 1.4 Discrete Impulsive Actuators (Taps)

Taps are fundamentally different from continuous screw feeding — they deliver impulsive mass packets by dislodging powder from the tube lip. The appropriate model is:

- **Impulse response with depletion state**: Define a lip inventory state x_lip that taps drain and auger rotations refill. Each tap removes Δm_tap = g_tap(tilt, x_lip) from the lip, where g_tap decreases as x_lip depletes (successive taps without re-feed yield diminishing returns). Each screw rotation adds Δx_lip_refill = f_refill(tilt, ff) to the lip inventory. This captures your observation that "taps deplete the tube lip unless the auger re-feeds it between taps."

### 1.5 Stochastic Flow Noise

For cohesive powders, flow is inherently stochastic due to avalanching, bridging, and stick-slip behavior. Cohesive forces cause particles to form structures (arches, bridges) in the hopper that resist displacement; when these collapse, they produce intermittent flow surges (jonessalkey2023reviewingtheimpact pages 4-6). The flow function coefficient (FFC) from shear cell testing quantifies this: FFC < 2 is very cohesive, 2–4 cohesive, 4–10 easy flowing, >10 free flowing (pouliquen2025powdersandcohesive pages 9-12). Powders with FFC > 3 achieve sub-1% flow rate variability, while low-FFC powders exhibit large feed factor variations suggesting processing instability (jonessalkey2023reviewingtheimpact pages 8-10). The noise model should therefore be powder-class-dependent: a variance term σ²_flow(FFC, tilt, ω) that is identified per powder from the spread in per-packet yield measurements.

## 2. MPC FORMULATION

### 2.1 Shrinking-Horizon Batch MPC

Your dosing problem is fundamentally a **batch/endpoint control** problem: deliver a target mass M_target into a cup, then stop. This naturally maps to a **shrinking-horizon MPC** where the prediction horizon contracts as dispensed mass approaches the target. The state is accumulated mass m(k), the integrating dynamics are m(k+1) = m(k) + ff(·)·Δθ(k) + g_tap(·)·n_tap(k) (in event-based sampling), and the terminal constraint is m(N) = M_target.

The **asymmetric hard constraint** (no overshoot — powder cannot be removed) is the defining feature. This is a one-sided output constraint m(k) ≤ M_target ∀k. In robust MPC terms, this constraint must hold despite flow stochasticity, requiring a **back-off** from the target.

### 2.2 Tube-Based Robust MPC for Back-Off

Tube-based robust MPC provides the principled framework for determining how far to back off from the overshoot constraint. The approach maintains a nominal trajectory with "tightened" constraints, where the tightening set accounts for the worst-case (or probabilistic) disturbance realization (oshin2308differentiablerobustmodel pages 2-3, dey2603adaptivetubempc pages 2-3, dey2603adaptivetubempc pages 1-2). For your system:

- The disturbance bound is the flow noise variance σ²_flow, propagated through the remaining horizon
- The constraint tightening gives m_nominal_target = M_target − Δ_backoff, where Δ_backoff ∝ σ_flow · √(N_remaining)
- As the horizon shrinks and you switch to finer actuators, σ_flow decreases (taps have lower variance than bulk auger), so the back-off naturally decreases

Adaptive tube MPC further reduces conservatism by updating the uncertainty set online as the feed factor estimate converges during the dose, shrinking the tube cross-section and allowing the controller to approach the target more aggressively (dey2603adaptivetubempc pages 10-11, dey2603adaptivetubempc pages 9-10).

### 2.3 Hybrid/Phase-Switched MPC

Given the heterogeneous actuator set (continuous auger, discrete taps, tilt, vibration), a **phase-switched architecture** is most practical:

- **Phase 1 (Bulk)**: Continuous MPC on auger speed, with tilt set high for fast flow. Horizon is time-based with ~1 s steps matching balance settling. Stop criterion: m > M_target − M_fine_margin.
- **Phase 2 (Fine)**: Event-based MPC on discrete rotation increments (half-rev, quarter-rev). Shorter effective horizon. Stop criterion: m > M_target − M_tap_margin.
- **Phase 3 (Trim)**: Tap-only policy, possibly a simple greedy rule or single-step optimization. Each tap is evaluated against remaining error minus expected in-flight inventory.

This avoids the computational complexity of full mixed-integer MPC while naturally matching the actuator capabilities to the error regime. Full MI-MPC combining continuous speed and integer tap counts would require solving a Mixed-Integer Nonlinear Program at each step; while this is tractable for small problems (herkenrath2026addressingmixedintegernonlinear pages 1-2), the phase-switched approach is far simpler to implement and tune on embedded hardware.

### 2.4 Frugal MPC for Embedded Implementation

The "Frugal MPC" paradigm is directly applicable to your Pi Zero/RP2040 platform. This approach uses a simplified **integrator-chain model** (mass is the integral of flow rate, which is the integral of acceleration) combined with an **Extended State Observer (ESO)** that estimates and compensates for the total disturbance (model mismatch, powder variability, unmodeled dynamics) as a lumped term (vasquezcruz2025frugalmodelpredictive pages 1-2, vasquezcruz2025frugalmodelpredictive pages 2-3). The key advantages are:

- The QP matrices H, A_ineq, etc. are computed **offline once**; only the state/disturbance vectors are updated at runtime (vasquezcruz2025frugalmodelpredictive pages 5-6)
- Control parameterization can reduce decision variables to as few as 2 over a horizon of N=10 (vasquezcruz2025frugalmodelpredictive pages 2-3)
- The ESO provides adaptive disturbance rejection without requiring an accurate plant model, making it robust to powder-to-powder variation (vasquezcruz2025frugalmodelpredictive pages 11-13)

### 2.5 Sampling and Discretization

Given the 0.8 s balance settling time, the natural MPC sample period for bulk-phase control is T_s ≈ 1 s (time-based). However, for fine-phase control, **event-based (rotation-based) sampling** is more appropriate: each MPC step corresponds to one rotation increment, with the balance read taken after settling. This naturally handles the cyclostationary pulsation and avoids aliasing the per-rev yield pattern into noise.

## 3. STATE ESTIMATION

### 3.1 Kalman Filtering of Mass and Flow Rate

The estimation problem closely parallels LIW feeder operation during refill, where the balance signal becomes unreliable and the system must estimate flow from a combination of volumetric (model-predicted) and gravimetric (measured) information (fathollahi2024improvingcontinuouslossinweight pages 7-10, fathollahi2024improvingcontinuouslossinweight pages 2-4, fathollahi2024improvingcontinuouslossinweight pages 1-2). For your system:

**State vector**: x = [m_cup, ṁ_flow, x_flight, x_lip, ff]ᵀ — accumulated cup mass, instantaneous flow rate, in-flight inventory, lip inventory, and current feed factor.

**Measurement**: y = m_balance (slow, quantized, noisy).

A Kalman filter or Extended Kalman Filter (EKF) propagates the state forward using the process model (auger commands → predicted flow → predicted mass) and corrects with each balance reading. The measurement noise covariance R should be set based on your balance noise baseline (~1 mg resolution), and the process noise Q captures feed-factor uncertainty and flow stochasticity.

### 3.2 Handling Quantization and Settling

Two strategies exist for the slow, quantized balance:

1. **Wait for stable readings**: Use only settled readings with known noise characteristics. This limits update rate to ~1.2 Hz but gives clean measurements.
2. **Use non-stable readings with a noise model**: Treat the raw serial stream as measurements with time-varying noise covariance R(t) that is large during settling and small after. This allows faster state updates but requires characterizing the balance's transient response.

Strategy 2 is theoretically superior and is supported by the balance noise baseline experiment. In practice, start with strategy 1 and upgrade if the control bandwidth proves insufficient.

### 3.3 Online Feed-Factor Estimation

The feed factor should be estimated online using **Recursive Least Squares (RLS) with forgetting factor** or an EKF with ff as an augmented state. The forgetting factor (λ ≈ 0.95–0.99) allows adaptation to slow drifts (fill-level changes, powder conditioning) while filtering fast noise. Your existing "per-rev estimator that converged fine" is essentially this approach. For MPC integration, the updated ff estimate directly modifies the prediction model at each step — this is **indirect adaptive MPC**.

### 3.4 Regime Change / Fault Detection

Bridging, empty hopper, and caking manifest as sudden feed-factor drops or anomalous flow patterns. Detection approaches include:

- **CUSUM or EWMA on ff residuals**: A sustained deviation of estimated ff from the running mean signals a regime change
- **FFC-based classification**: Powders with FFC < 2 (very cohesive) are flagged for higher bridging risk; the controller should monitor for zero-flow periods and trigger vibration or tapping as remediation (jonessalkey2023reviewingtheimpact pages 4-6, jonessalkey2023reviewingtheimpact pages 1-3)
- **Soft sensors using feeder data**: RTD-based soft sensors demonstrated in continuous manufacturing predict process state from feeder mass flow data alone, without additional sensors (rehrl2018controlofthree pages 1-4, rehrl2018controlofthree pages 18-22)

## 4. DATA COLLECTION / SYSTEM IDENTIFICATION — THE CORE DELIVERABLE

### 4.1 Experiment Battery

The following table specifies the complete experiment program, mapped to model parameters:

| Experiment Name | Purpose/Model Parameter Targeted | Excitation Signal | Key Settings to Vary | Sampling Strategy | Minimum Repeats | Notes |
|---|---|---|---|---|---|---|
| Static feed-factor map by tilt and speed | Identify mean feed factor (g/rev or g/step), local input nonlinearity between commanded screw motion and delivered mass, and baseline gravimetric variance for each powder; this is the core calibration used in LIW feeders and low-dose feeders (bostijn2019amultivariateapproach pages 10-14, fathollahi2024improvingcontinuouslossinweight pages 2-4, fathollahi2020performanceevaluationof pages 1-2) | Staircase of constant-speed runs and fixed-rotation packet doses; include both continuous RPM plateaus and discrete half-rev or quarter-rev packets | Tilt angle, screw speed, vibration on or off or level, packet size, auger direction if reversible, hopper fill band | Log raw balance stream continuously, not only stable values; also compute settled delta-mass per packet and average slope over longer windows; use run lengths long enough to average several settling intervals at each plateau | 10 runs per powder-tilt-speed in coarse map; 20 packet doses per point for fine-dose region | Map separately for bulk and fine regimes; literature shows feed factor changes with fill level and density-stress state, so this map is only the first layer, not the full model (bostijn2019amultivariateapproach pages 22-26, bostijn2019amultivariateapproach pages 14-18) |
| Per-revolution periodicity and screw pulsation map | Identify cyclostationary angle-dependent yield pattern, harmonic content, and whether the system should be modeled in event or angle domain rather than only time domain | Repeated single-increment doses synchronized to motor angle: quarter-rev, half-rev, and full-rev sequences starting from many initial angles; also low-speed continuous rotation with angle-resolved binning | Initial auger phase, increment size, tilt, vibration state, low versus medium RPM, hopper fill band | Event-based logging keyed by commanded and actual step count; estimate delivered mass only after batching enough identical events to overcome 1 mg quantization; aggregate by angle modulo 1 rev | 30 identical packets per phase bin; target 8 to 16 phase bins per rev | This experiment is essential because observed alternating yields are structured, not white noise; identify a periodic basis such as a lookup table or first few Fourier terms to embed in the prediction model |
| Continuous-speed dynamic test | Identify dynamic relation between screw-speed changes and delivered flow or inventory under continuous operation; estimate whether a first-order lag is needed in addition to pure transport delay | Speed steps, staircases, and bounded PRBS or ternary sequence on RPM during long runs | Tilt, nominal RPM, vibration state, fill band | Sample raw balance as fast as available; estimate mass-flow soft sensor offline from smoothed derivative or state estimator; fit dead-time plus low-order dynamic model on longer windows than 0.8 s settling | 5 long runs per operating region; each run should contain 10 to 20 informative transitions | Because the balance is slow, dynamic identification should rely on long-enough blocks and soft-sensed flow rather than packet deltas alone; this mirrors RTD and dead-time identification logic used in continuous powder processes (gyurkes2023residencetimedistributionbased pages 1-2, rehrl2018controlofthree pages 4-8, gyurkes2023residencetimedistributionbased pages 4-6) |
| Stop-response and in-flight inventory test | Identify transport delay, falling-column inventory, and anticipation mass needed to stop without overshoot | Run at steady flow, then command abrupt stop at randomized times or phases | Tilt, RPM, vibration state, fill band, stop phase within screw rotation | Record raw mass before stop and through full post-stop settling; compute extra landed mass after stop, apparent delay to first continued rise, and decay shape | 20 stops per operating point | Use results to choose between pure dead time, dead time plus first-order lag, or explicit in-flight inventory state; if extra landed mass scales linearly with pre-stop flow, an inventory state is natural |
| Start-up transient and preconditioning test | Identify initial compaction, lag, and transient densification before steady feeding | From rest, execute standardized start sequences: immediate continuous run, ramped start, and pre-spin or conditioning routines | Powder loading method, dwell time after loading, tilt, RPM, vibration, fill level | Log full transient from motor start until apparent steady state; compare first delivered mass and time-to-steady behavior | 10 starts per condition | Low-dose feeder literature shows distinct start, densification, stable, and end phases; these data decide whether MPC needs a startup mode or simply a disturbance state (fathollahi2020performanceevaluationof pages 3-4, fathollahi2020performanceevaluationof pages 2-3) |
| Fill-level drawdown experiment | Identify feed-factor dependence on hopper fill level and refill threshold policy; estimate ff(fill) profile and decay point | Long volumetric or pseudo-gravimetric emptying runs from full to near-empty | Initial fill mass, speed, tilt, vibration, refill strategy disabled during characterization | Continuously log hopper or catch mass, cumulative rotations, and inferred feed factor versus remaining fill; bin by fill fraction | 3 full drawdowns per operating condition; 5 for powders expected to cake or bridge | This directly matches LIW literature practice: extract FFmax and decay-threshold descriptors and determine at what fill level performance degrades sharply (bostijn2019amultivariateapproach pages 10-14, bostijn2019amultivariateapproach pages 14-18) |
| Refill disturbance test | Identify how adding powder perturbs density or feed factor and how long recovery takes; useful if future system will refill during long campaigns | Controlled refill pulses during operation with fixed added mass or volume | Refill level trigger, refill amount, refill rate, speed, tilt, vibration | Time-align refill event with raw mass and rotation logs; estimate transient change in feed factor before, during, and after refill | 10 refills per policy | LIW feeders switch effectively to volumetric behavior during refill and show densification-driven overfeed; even if current batch doses are short, this test is needed for library building and future long runs (fathollahi2024improvingcontinuouslossinweight pages 7-10, fathollahi2024improvingcontinuouslossinweight pages 2-4, fathollahi2024improvingcontinuouslossinweight pages 6-7) |
| Tap-only impulse-response map | Identify tap burst yield distribution, dead time from tap to landed mass, and baseline stochasticity of impulse actuation | Isolated tap bursts with no screw motion between bursts | Tap count, on-time, off-time, duty cycle, burst spacing, tilt, vibration state | Event-based logging of each burst timestamp plus raw balance trace; compute settled mass per burst and post-burst landing tail | 30 bursts per tap configuration in fine-dose region | Because yields are only a few mg, high repeat count is needed to estimate both mean and variance under quantization; use randomized burst order to avoid drift confounding |
| Tap depletion and re-feed dynamics | Identify lip inventory state drained by taps and replenished by auger motion; needed for hybrid model with depletion state | Sequences such as tap-tap-tap, tap plus wait, tap plus half-rev plus tap, tap plus multiple revs plus tap | Number of taps since last re-feed, inter-tap interval, re-feed rotation amount, tilt, vibration | Log each event with event index; estimate marginal yield of each successive tap and recovery as function of intervening rotations or time | 20 sequences per pattern | If successive taps decay strongly without re-feed, include explicit lip-inventory state in model; if recovery depends mainly on added rotation, use a refill gain from auger motion |
| Auger-tap interaction matrix | Identify interaction term between continuous screw feed and discrete taps, especially when taps act on already mobile powder at higher tilt | Factorial or space-filling sequences mixing short screw packets and tap bursts | Tilt, screw packet size, RPM, tap config, vibration | Use event-level response decomposition: predicted screw-only mass plus tap-only mass versus actual combined mass | 15 replicates per selected interaction point | Full factorial over all settings is expensive; use a coarse screening design first, then concentrate repeats where interaction non-additivity is largest |
| Tilt sensitivity map | Identify tilt as a scheduling variable affecting feed factor, tap gain, dead time, and stop inventory | Repeat key auger, stop, and tap tests on a tilt grid | Tilt across full used range such as 0 to 25 degrees, speed bands, tap settings | Treat tilt as a slow scheduling coordinate; collect enough data at each node to interpolate | 5 runs per node for coarse map; 10 near operating regions of interest | Existing observations show tilt strongly changes both continuous and tap yields, so model scheduling on tilt is mandatory |
| Vibration sensitivity map | Identify whether vibration mainly shifts mean feed factor, reduces variance or bridging, changes tap depletion, or changes dead time | On-off tests, level steps, and optional PRBS on vibration amplitude if controllable | Vibration amplitude or duty, powder, fill band, tilt, speed | Compare matched runs with and without vibration; log current draw if possible as proxy for actual agitation state | 10 paired runs per condition | For cohesive powders, vibration may reduce bridging and variance more than it changes mean; capture both effects for controller and fault logic |
| Cross-actuator optimal design campaign | Identify low-order interaction model over tilt, speed, tap config, and vibration while spending runs where MPC benefits most | Screening DOE followed by focused D-optimal or space-filling refinement | Tilt, RPM, vibration, tap count and on-off, packet size; optionally fill band as blocking factor | Start with fractional factorial or Latin hypercube to screen; fit sparse interaction model; then allocate more runs where Fisher information for critical parameters is low | Screening: 1 to 2 runs per point over 20 to 40 points; refinement: add 20 to 40 targeted runs | Identification-for-control principle: spend runs near intended operating envelope and near constraint boundary where stop accuracy matters, not uniformly everywhere |
| Balance noise and quantization baseline | Identify measurement noise, settling-time distribution, quantization effects, drift, and whether non-stable readings are usable in estimation | No-actuation idle records; known calibration micro-steps; gentle cup disturbances if safe | Ambient vibration conditions, serial polling rate, filtering mode, cup mass, tare state | Record raw serial stream continuously for long idle periods and during known reference mass additions | 10 long idle records plus 20 known-step trials | Needed to tune Kalman or observer measurement covariance and to decide whether to use all raw readings rather than only stable values |
| Environmental and context drift study | Quantify between-run shifts due to humidity, temperature, and exposure history; support powder library indexing and adaptation | Repeated standard characterization runs at different ambient and exposure conditions | Relative humidity, temperature, elapsed exposure time after opening, storage condition, hopper residence time | Log environment continuously if possible and store run-level metadata; repeat a standard reference test at start and end of day | Daily reference runs; 5 exposure states per powder if feasible | Literature and powder practice indicate moisture and temperature alter cohesion and flowability; even if not controlled, they should be logged as covariates (stavrou2020assessingpowderflowability pages 255-258, jonessalkey2023reviewingtheimpact pages 1-3) |
| Powder transfer and library-building campaign | Determine what must be re-identified per powder versus adapted online from prior library models | Run a reduced transfer set for new powders after a full characterization of a few anchor powders | Powder identity, particle size distribution if available, bulk and tapped density, FFC or cohesion metrics, humidity history | For each new powder, collect a small standard packet: baseline feed-factor map, stop test, tap map, and balance noise check; compare against prior powders using normalized descriptors | Full campaign for 3 to 5 anchor powders; reduced transfer set for every new powder | Use literature descriptors such as bulk density, tapped density, compressibility, and FFC to index transferability, but still re-measure the parameters that most affect overshoot risk: feed factor, stop inventory, and tap gain (bostijn2019amultivariateapproach pages 22-26, jonessalkey2023reviewingtheimpact pages 4-6, jonessalkey2023reviewingtheimpact pages 8-10) |
| Environmental logging and metadata standard | Ensure same dataset supports identification, MPC validation, and later Bayesian optimization | No excitation; mandatory logging standard attached to every run | powder_id, batch or lot, operator, storage history, time since opening, humidity, temperature, hopper fill, tilt, vibration setting, commanded and actual rotations, tap event details, raw mass stream | Log every event with timestamped commanded and actual actuator state plus all raw balance readings including unstable samples | Every run | Required schema should include run-level metadata, sample-level balance data, event-level actuation records, and derived labels; this mirrors continuous manufacturing practice where feeder data and contextual metadata are central to soft sensing and control (rehrl2018controlofthree pages 18-22, fathollahi2024improvingcontinuouslossinweight pages 2-4) |


*Table: This table lays out a control-oriented experiment program for identifying the gravimetric powder doser’s feed, delay, impulsive tap, fill-level, and context-dependent dynamics. It is designed to support MPC model building, estimator tuning, and powder-library transfer with citations to the relevant feeder and powder-flow literature.*

### 4.2 Excitation Signal Design Details

**For the auger**: Steps and staircases are the primary excitation for feed-factor identification. PRBS on screw speed is informative for dynamic identification (lag, dead time) but must be adapted to the slow measurement: use multi-level sequences with hold times ≥ 3× the settling time (≥2.4 s per level) to ensure at least one clean measurement per state. Single-increment dosing pulses (quarter-rev, half-rev) are essential for fine-regime characterization and per-rev periodicity mapping. Given the 1 mg resolution and ~5–50 mg per-packet yields, **30+ repeats per condition** are needed to estimate both mean and standard deviation with useful precision (bostijn2019amultivariateapproach pages 14-18, fathollahi2020performanceevaluationof pages 3-4).

**For taps**: Impulse-response mapping requires burst-size sweeps (1, 2, 3, 4, 5 taps), duty-cycle variation, and critically, depletion sequences (multiple bursts without re-feed). At ~2–5 mg per 2-tap burst, 30 repeats give ~±0.5 mg standard error on the mean, which is sufficient for ±1 mg accuracy targets.

**For fill-level dependence**: Draw-down experiments (run hopper from full to empty, logging mass vs. rotations) directly produce the ff(fill) profile. This exactly follows the methodology established for LIW feeder characterization, where feed-factor profiles are generated by plotting feed factor against hopper fill level at multiple screw speeds (bostijn2019amultivariateapproach pages 10-14, bostijn2019amultivariateapproach pages 14-18).

**For in-flight inventory**: Stop-response tests at multiple speeds and tilts identify the anticipation mass. Run at steady state for ≥30 s, then command an abrupt stop and record the full post-stop mass trace through settling. The extra landed mass Δm_stop directly estimates the in-flight inventory at that operating point.

### 4.3 Cross-Actuator Interaction Design

A full factorial over (tilt: 5 levels) × (speed: 4 levels) × (tap config: 4 levels) × (vibration: 2 levels) = 160 points × 10 repeats = 1600 runs is prohibitive. Instead, use a **two-stage approach**:

1. **Screening**: Latin hypercube or fractional factorial with 30–40 runs to identify which interactions are significant
2. **Refinement**: D-optimal design focused on the identified significant interactions, concentrating runs near the intended MPC operating envelope — this follows the "identification for control" principle that experiment effort should be allocated where the controller operates, not uniformly (rehrl2018controlofthree pages 4-8).

### 4.4 Per-Powder vs. Transferable Parameters

The LIW feeder literature strongly supports that **feed factor is grossly powder-dependent** — your 17× mismatch between default and measured ff confirms this (bostijn2019amultivariateapproach pages 6-10, bostijn2019amultivariateapproach pages 22-26, bostijn2019amultivariateapproach pages 1-6). However, certain model structures transfer:

- **Dead time and in-flight dynamics**: Primarily geometric (tube length, tilt), largely powder-independent
- **Per-rev pulsation pattern**: Primarily mechanical (auger geometry), largely powder-independent
- **Balance noise model**: Completely powder-independent
- **Feed factor magnitude and variance**: Fully powder-dependent, must be re-identified
- **Tap yield and depletion dynamics**: Strongly powder-dependent (cohesion governs lip adhesion)

PLS models using material property descriptors (bulk density, tapped density, compressibility, FFC) can predict FFmax with R² > 0.8 across diverse powders (bostijn2019amultivariateapproach pages 22-26, bostijn2019amultivariateapproach pages 1-6), providing useful **priors** for new powders. The recommended approach: maintain a powder library in MongoDB (keyed by powder_id with material properties), run a reduced "transfer set" for each new powder (baseline ff map + stop test + tap map ≈ 60–90 minutes), and use the library to initialize online estimators.

### 4.5 Environmental Instrumentation

The powder flow literature identifies humidity and temperature as significant factors affecting cohesion and flowability (stavrou2020assessingpowderflowability pages 255-258). At minimum, log:
- Relative humidity (±2% RH sensor, ~$5)
- Temperature (±0.5°C, built into many RH sensors)
- Time since powder container was opened (exposure history proxy)
- Hopper fill mass at start

These are metadata, not controlled variables, but they enable post-hoc analysis of drift and support future adaptive models.

### 4.6 Dataset Schema

Every run should log the following, stored per-run and per-event in MongoDB:

**Run-level metadata**: run_id, powder_id, powder_batch, operator, timestamp, ambient_rh, ambient_temp, powder_exposure_hours, hopper_fill_g, tilt_deg, vibration_setting, target_mass_g, controller_mode, notes.

**Sample-level balance data** (logged at maximum serial rate, ~10 Hz): timestamp_ms, raw_mass_mg, stable_flag, balance_status_byte.

**Event-level actuation records**: timestamp_ms, event_type (rotation/tap/tilt_change/vibration_change/stop), commanded_value (steps/taps/degrees), actual_encoder_value, auger_phase_angle_deg, estimated_ff_g_per_rev, estimated_inflight_mg, estimated_lip_inventory_mg.

**Derived labels** (computed post-run): settled_mass_per_event, cumulative_mass_trace, per_rev_yield, terminal_error_mg, dose_time_s, overshoot_flag, constraint_violation_count.

## 5. VALIDATION, PRACTICALITY, AND PHASED PLAN

### 5.1 Validation Metrics

Following LIW feeder benchmarking practice, the primary metrics are (bostijn2019amultivariateapproach pages 1-6, bostijn2019amultivariateapproach pages 6-10, bostijn2019amultivariateapproach pages 14-18):

- **Terminal error distribution**: Mean and standard deviation of (dispensed − target) across doses; goal: |mean| < 1 mg, σ < 1 mg
- **Time-to-dose**: Total time from start to final settled reading; benchmark against current 21 s for 2 g
- **Overshoot rate**: Fraction of doses exceeding M_target; goal: 0% for ±5 mg tolerance, <5% for ±1 mg
- **RSD of delivered mass**: Relative standard deviation across repeated doses; sub-1% RSD is achievable for FFC > 3 powders (jonessalkey2023reviewingtheimpact pages 8-10)

Both **open-loop** (model prediction error on validation data) and **closed-loop** (actual dosing performance) validation are needed. Open-loop validates the model; closed-loop validates the controller. Use held-out runs from the ID campaign for open-loop, and fresh dosing runs for closed-loop.

### 5.2 Implementable Toolchains

For a Raspberry Pi Zero 2 W (1 GHz quad-core ARM, 512 MB RAM):

- **Frugal MPC with ESO**: The most computationally lightweight option. Precompute QP matrices offline; runtime requires only matrix-vector multiplies and a small gradient-based QP solve. Demonstrated at 1 ms sampling on embedded hardware (vasquezcruz2025frugalmodelpredictive pages 8-9). Easily implementable in Python/NumPy or C on the Pi Zero.

- **acados**: The leading open-source solver for embedded nonlinear MPC, providing fast SQP solvers with automatic C-code generation (lahr2026l4acadoslearningbasedmodels pages 1-2, lahr2026l4acadoslearningbasedmodels pages 3-4). Achieves ~8 ms solve times for GP-MPC on automotive hardware (lahr2026l4acadoslearningbasedmodels pages 8-10). Can run on Pi Zero via C-generated code, though Python interface adds overhead.

- **Explicit MPC / lookup tables**: For the small state space of this problem (mass, flow estimate, in-flight inventory, lip inventory ≈ 4–5 states), multiparametric QP can precompute the optimal control law as a piecewise-affine function of the state, stored as a lookup table. This reduces online computation to a point-location search, feasible even on the RP2040 microcontroller (arango2023neuralnetworksfor pages 54-57).

- **Neural network approximation**: DNNs trained to imitate the MPC achieve 25–200× speedup with probabilistic constraint satisfaction guarantees (arango2023neuralnetworksfor pages 39-42). The DNN can warm-start an active-set solver to preserve all MPC guarantees while reducing computation (arango2023neuralnetworksfor pages 18-21).

- **Python-based tools** (do-mpc, GEKKO, CasADi): Suitable for prototyping and offline optimization on the Pi Zero, but likely too slow for real-time control at >1 Hz with nonlinear models. Use for offline trajectory optimization and run-to-run learning, not for real-time MPC.

### 5.3 Recommended Phased Plan

**Phase 0 — Measurement Infrastructure (1–2 weeks)**
- Implement high-rate raw balance logging (all readings, not just stable)
- Add RH/temperature sensor, log to MongoDB with run metadata
- Implement dataset schema described above
- Run balance noise baseline experiments (idle + known-step)
- *Evidence to proceed*: Characterized balance noise, settling-time distribution, quantization effects

**Phase 1 — Single-Powder Characterization Campaign (2–3 weeks)**
- Choose one well-behaved anchor powder (e.g., salt)
- Execute: feed-factor map, per-rev periodicity, stop-response, tap impulse-response, fill-level drawdown, tilt sensitivity
- Identify: ff(tilt, fill, ω), per-rev harmonics, dead time τ_d, in-flight inventory model, tap gain g_tap(tilt, x_lip), depletion dynamics
- *Evidence to proceed*: Open-loop model prediction error < 5 mg for 2 g doses; identified parameters converge across repeats

**Phase 2 — Frugal MPC Implementation (2–3 weeks)**
- Implement phase-switched controller: bulk MPC (integrator model + ESO) → fine event-based MPC → tap trim
- Use Frugal MPC formulation with precomputed QP matrices
- Implement online RLS feed-factor estimation with forgetting
- Tune back-off from overshoot constraint using identified flow variance
- *Evidence to proceed*: Closed-loop terminal error < 5 mg with 0% overshoot; dose time competitive with current 21 s

**Phase 3 — Robustification and Multi-Powder (3–4 weeks)**
- Run transfer campaigns on 2–3 additional powders (xanthan gum, flour, AlSi10Mg)
- Implement tube-based constraint tightening using per-powder variance estimates
- Build powder library with material-property-indexed priors
- Implement fault detection (bridging, empty hopper) from ff residuals
- *Evidence to proceed*: ±1 mg accuracy across multiple powders; automatic adaptation to new powder within reduced transfer set

**Phase 4 — Advanced MPC and Optimization (4+ weeks)**
- Explore explicit MPC lookup tables for RP2040 deployment
- Implement run-to-run Bayesian optimization for outer-loop tuning (back-off, phase transition thresholds, tap policy parameters)
- Consider GP-based adaptive MPC if powder variability warrants learning-based residual models (lahr2026l4acadoslearningbasedmodels pages 2-3)
- *Evidence to proceed*: Quantitative improvement in dose time or accuracy over Phase 2 controller; ±0.1 mg stretch goal demonstration

This phased approach ensures each step builds on validated evidence from the previous one, with clear quantitative criteria for advancing in complexity. The core principle throughout is that **the model and controller complexity should be justified by the data** — start with the simplest model that captures the dominant dynamics (integrator + feed factor + dead time), and add complexity (cyclostationary terms, lip inventory, GP residuals) only when validated against experimental evidence of inadequacy.


References

1. (bostijn2019amultivariateapproach pages 10-14): N. Bostijn, J. Dhondt, A. Ryckaert, E. Szabó, W. Dhondt, B. V. Snick, B. V. Snick, V. Vanhoorne, C. Vervaet, and T. D. Beer. A multivariate approach to predict the volumetric and gravimetric feeding behavior of a low feed rate feeder based on raw material properties. International Journal of Pharmaceutics, 557:342–353, Feb 2019. URL: https://doi.org/10.1016/j.ijpharm.2018.12.066, doi:10.1016/j.ijpharm.2018.12.066. This article has 89 citations and is from a domain leading peer-reviewed journal.

2. (bostijn2019amultivariateapproach pages 22-26): N. Bostijn, J. Dhondt, A. Ryckaert, E. Szabó, W. Dhondt, B. V. Snick, B. V. Snick, V. Vanhoorne, C. Vervaet, and T. D. Beer. A multivariate approach to predict the volumetric and gravimetric feeding behavior of a low feed rate feeder based on raw material properties. International Journal of Pharmaceutics, 557:342–353, Feb 2019. URL: https://doi.org/10.1016/j.ijpharm.2018.12.066, doi:10.1016/j.ijpharm.2018.12.066. This article has 89 citations and is from a domain leading peer-reviewed journal.

3. (bostijn2019amultivariateapproach pages 14-18): N. Bostijn, J. Dhondt, A. Ryckaert, E. Szabó, W. Dhondt, B. V. Snick, B. V. Snick, V. Vanhoorne, C. Vervaet, and T. D. Beer. A multivariate approach to predict the volumetric and gravimetric feeding behavior of a low feed rate feeder based on raw material properties. International Journal of Pharmaceutics, 557:342–353, Feb 2019. URL: https://doi.org/10.1016/j.ijpharm.2018.12.066, doi:10.1016/j.ijpharm.2018.12.066. This article has 89 citations and is from a domain leading peer-reviewed journal.

4. (fathollahi2024improvingcontinuouslossinweight pages 2-4): Sara Fathollahi, Valjon Demiri, Theresa R. Hörmann-Kincses, Snjezana Maljuric, Julia Massoner, Greg Mehos, and Johannes G. Khinast. Improving continuous loss-in-weight feeding accuracy by a novel hopper design. Journal of Pharmaceutical Innovation, Sep 2024. URL: https://doi.org/10.1007/s12247-024-09858-2, doi:10.1007/s12247-024-09858-2. This article has 2 citations and is from a peer-reviewed journal.

5. (bostijn2019amultivariateapproach pages 1-6): N. Bostijn, J. Dhondt, A. Ryckaert, E. Szabó, W. Dhondt, B. V. Snick, B. V. Snick, V. Vanhoorne, C. Vervaet, and T. D. Beer. A multivariate approach to predict the volumetric and gravimetric feeding behavior of a low feed rate feeder based on raw material properties. International Journal of Pharmaceutics, 557:342–353, Feb 2019. URL: https://doi.org/10.1016/j.ijpharm.2018.12.066, doi:10.1016/j.ijpharm.2018.12.066. This article has 89 citations and is from a domain leading peer-reviewed journal.

6. (gyurkes2023residencetimedistributionbased pages 1-2): Martin Gyürkés, Kornélia Tacsi, Hajnalka Pataki, and Attila Farkas. Residence time distribution-based smith predictor: an advanced feedback control for dead time–dominated continuous powder blending process. Journal of Pharmaceutical Innovation, 18:1381-1394, May 2023. URL: https://doi.org/10.1007/s12247-023-09728-3, doi:10.1007/s12247-023-09728-3. This article has 4 citations and is from a peer-reviewed journal.

7. (gyurkes2023residencetimedistributionbased pages 4-6): Martin Gyürkés, Kornélia Tacsi, Hajnalka Pataki, and Attila Farkas. Residence time distribution-based smith predictor: an advanced feedback control for dead time–dominated continuous powder blending process. Journal of Pharmaceutical Innovation, 18:1381-1394, May 2023. URL: https://doi.org/10.1007/s12247-023-09728-3, doi:10.1007/s12247-023-09728-3. This article has 4 citations and is from a peer-reviewed journal.

8. (gyurkes2023residencetimedistributionbased pages 6-7): Martin Gyürkés, Kornélia Tacsi, Hajnalka Pataki, and Attila Farkas. Residence time distribution-based smith predictor: an advanced feedback control for dead time–dominated continuous powder blending process. Journal of Pharmaceutical Innovation, 18:1381-1394, May 2023. URL: https://doi.org/10.1007/s12247-023-09728-3, doi:10.1007/s12247-023-09728-3. This article has 4 citations and is from a peer-reviewed journal.

9. (rehrl2018controlofthree pages 1-4): Jakob Rehrl, Anssi-Pekka Karttunen, Niels Nicolaï, Theresa Hörmann, Martin Horn, Ossi Korhonen, Ingmar Nopens, Thomas De Beer, and Johannes G. Khinast. Control of three different continuous pharmaceutical manufacturing processes: use of soft sensors. International Journal of Pharmaceutics, 543:60–72, May 2018. URL: https://doi.org/10.1016/j.ijpharm.2018.03.027, doi:10.1016/j.ijpharm.2018.03.027. This article has 85 citations and is from a domain leading peer-reviewed journal.

10. (rehrl2018controlofthree pages 4-8): Jakob Rehrl, Anssi-Pekka Karttunen, Niels Nicolaï, Theresa Hörmann, Martin Horn, Ossi Korhonen, Ingmar Nopens, Thomas De Beer, and Johannes G. Khinast. Control of three different continuous pharmaceutical manufacturing processes: use of soft sensors. International Journal of Pharmaceutics, 543:60–72, May 2018. URL: https://doi.org/10.1016/j.ijpharm.2018.03.027, doi:10.1016/j.ijpharm.2018.03.027. This article has 85 citations and is from a domain leading peer-reviewed journal.

11. (jonessalkey2023reviewingtheimpact pages 4-6): Owen Jones-Salkey, Zoe Chu, Andrew Ingram, and Christopher R. K. Windows-Yule. Reviewing the impact of powder cohesion on continuous direct compression (cdc) performance. Pharmaceutics, 15:1587, May 2023. URL: https://doi.org/10.3390/pharmaceutics15061587, doi:10.3390/pharmaceutics15061587. This article has 36 citations.

12. (pouliquen2025powdersandcohesive pages 9-12): Olivier Pouliquen. Powders and cohesive granular media: a rheological perspective. Rheologica Acta, 64:195-207, Apr 2025. URL: https://doi.org/10.1007/s00397-025-01490-2, doi:10.1007/s00397-025-01490-2. This article has 15 citations and is from a peer-reviewed journal.

13. (jonessalkey2023reviewingtheimpact pages 8-10): Owen Jones-Salkey, Zoe Chu, Andrew Ingram, and Christopher R. K. Windows-Yule. Reviewing the impact of powder cohesion on continuous direct compression (cdc) performance. Pharmaceutics, 15:1587, May 2023. URL: https://doi.org/10.3390/pharmaceutics15061587, doi:10.3390/pharmaceutics15061587. This article has 36 citations.

14. (oshin2308differentiablerobustmodel pages 2-3): Alex Oshin, Hassan Almubarak, and Evangelos A. Theodorou. Differentiable robust model predictive control. ArXiv, Aug 2308. URL: https://doi.org/10.48550/arxiv.2308.08426, doi:10.48550/arxiv.2308.08426. This article has 29 citations.

15. (dey2603adaptivetubempc pages 2-3): Anchita Dey and S. Bhasin. Adaptive tube mpc: beyond a common quadratically stabilizing feedback gain. ArXiv, Mar 2603. URL: https://doi.org/10.48550/arxiv.2603.15912, doi:10.48550/arxiv.2603.15912. This article has 0 citations.

16. (dey2603adaptivetubempc pages 1-2): Anchita Dey and S. Bhasin. Adaptive tube mpc: beyond a common quadratically stabilizing feedback gain. ArXiv, Mar 2603. URL: https://doi.org/10.48550/arxiv.2603.15912, doi:10.48550/arxiv.2603.15912. This article has 0 citations.

17. (dey2603adaptivetubempc pages 10-11): Anchita Dey and S. Bhasin. Adaptive tube mpc: beyond a common quadratically stabilizing feedback gain. ArXiv, Mar 2603. URL: https://doi.org/10.48550/arxiv.2603.15912, doi:10.48550/arxiv.2603.15912. This article has 0 citations.

18. (dey2603adaptivetubempc pages 9-10): Anchita Dey and S. Bhasin. Adaptive tube mpc: beyond a common quadratically stabilizing feedback gain. ArXiv, Mar 2603. URL: https://doi.org/10.48550/arxiv.2603.15912, doi:10.48550/arxiv.2603.15912. This article has 0 citations.

19. (herkenrath2026addressingmixedintegernonlinear pages 1-2): Ferris Herkenrath, Silas Koßler, Marco Günther, and Stefan Pischinger. Addressing mixed-integer nonlinear energy management in hybrid vehicles: comparing genetic algorithm and sequential quadratic programming within model predictive control. Energies, 19:1535, Mar 2026. URL: https://doi.org/10.3390/en19061535, doi:10.3390/en19061535. This article has 1 citations.

20. (vasquezcruz2025frugalmodelpredictive pages 1-2): Rafael Isaac Vásquez-Cruz, Ernesto Castellanos-Velasco, and José Fermi Guerrero-Castellanos. Frugal model predictive control and active disturbance rejection for laser beam steering systems. Control Theory and Technology, 23:513-528, Aug 2025. URL: https://doi.org/10.1007/s11768-025-00281-7, doi:10.1007/s11768-025-00281-7. This article has 3 citations and is from a peer-reviewed journal.

21. (vasquezcruz2025frugalmodelpredictive pages 2-3): Rafael Isaac Vásquez-Cruz, Ernesto Castellanos-Velasco, and José Fermi Guerrero-Castellanos. Frugal model predictive control and active disturbance rejection for laser beam steering systems. Control Theory and Technology, 23:513-528, Aug 2025. URL: https://doi.org/10.1007/s11768-025-00281-7, doi:10.1007/s11768-025-00281-7. This article has 3 citations and is from a peer-reviewed journal.

22. (vasquezcruz2025frugalmodelpredictive pages 5-6): Rafael Isaac Vásquez-Cruz, Ernesto Castellanos-Velasco, and José Fermi Guerrero-Castellanos. Frugal model predictive control and active disturbance rejection for laser beam steering systems. Control Theory and Technology, 23:513-528, Aug 2025. URL: https://doi.org/10.1007/s11768-025-00281-7, doi:10.1007/s11768-025-00281-7. This article has 3 citations and is from a peer-reviewed journal.

23. (vasquezcruz2025frugalmodelpredictive pages 11-13): Rafael Isaac Vásquez-Cruz, Ernesto Castellanos-Velasco, and José Fermi Guerrero-Castellanos. Frugal model predictive control and active disturbance rejection for laser beam steering systems. Control Theory and Technology, 23:513-528, Aug 2025. URL: https://doi.org/10.1007/s11768-025-00281-7, doi:10.1007/s11768-025-00281-7. This article has 3 citations and is from a peer-reviewed journal.

24. (fathollahi2024improvingcontinuouslossinweight pages 7-10): Sara Fathollahi, Valjon Demiri, Theresa R. Hörmann-Kincses, Snjezana Maljuric, Julia Massoner, Greg Mehos, and Johannes G. Khinast. Improving continuous loss-in-weight feeding accuracy by a novel hopper design. Journal of Pharmaceutical Innovation, Sep 2024. URL: https://doi.org/10.1007/s12247-024-09858-2, doi:10.1007/s12247-024-09858-2. This article has 2 citations and is from a peer-reviewed journal.

25. (fathollahi2024improvingcontinuouslossinweight pages 1-2): Sara Fathollahi, Valjon Demiri, Theresa R. Hörmann-Kincses, Snjezana Maljuric, Julia Massoner, Greg Mehos, and Johannes G. Khinast. Improving continuous loss-in-weight feeding accuracy by a novel hopper design. Journal of Pharmaceutical Innovation, Sep 2024. URL: https://doi.org/10.1007/s12247-024-09858-2, doi:10.1007/s12247-024-09858-2. This article has 2 citations and is from a peer-reviewed journal.

26. (jonessalkey2023reviewingtheimpact pages 1-3): Owen Jones-Salkey, Zoe Chu, Andrew Ingram, and Christopher R. K. Windows-Yule. Reviewing the impact of powder cohesion on continuous direct compression (cdc) performance. Pharmaceutics, 15:1587, May 2023. URL: https://doi.org/10.3390/pharmaceutics15061587, doi:10.3390/pharmaceutics15061587. This article has 36 citations.

27. (rehrl2018controlofthree pages 18-22): Jakob Rehrl, Anssi-Pekka Karttunen, Niels Nicolaï, Theresa Hörmann, Martin Horn, Ossi Korhonen, Ingmar Nopens, Thomas De Beer, and Johannes G. Khinast. Control of three different continuous pharmaceutical manufacturing processes: use of soft sensors. International Journal of Pharmaceutics, 543:60–72, May 2018. URL: https://doi.org/10.1016/j.ijpharm.2018.03.027, doi:10.1016/j.ijpharm.2018.03.027. This article has 85 citations and is from a domain leading peer-reviewed journal.

28. (fathollahi2020performanceevaluationof pages 1-2): Sara Fathollahi, Stephan Sacher, M. Sebastian Escotet-Espinoza, James DiNunzio, and Johannes G. Khinast. Performance evaluation of a high-precision low-dose powder feeder. AAPS PharmSciTech, Nov 2020. URL: https://doi.org/10.1208/s12249-020-01835-5, doi:10.1208/s12249-020-01835-5. This article has 25 citations and is from a peer-reviewed journal.

29. (fathollahi2020performanceevaluationof pages 3-4): Sara Fathollahi, Stephan Sacher, M. Sebastian Escotet-Espinoza, James DiNunzio, and Johannes G. Khinast. Performance evaluation of a high-precision low-dose powder feeder. AAPS PharmSciTech, Nov 2020. URL: https://doi.org/10.1208/s12249-020-01835-5, doi:10.1208/s12249-020-01835-5. This article has 25 citations and is from a peer-reviewed journal.

30. (fathollahi2020performanceevaluationof pages 2-3): Sara Fathollahi, Stephan Sacher, M. Sebastian Escotet-Espinoza, James DiNunzio, and Johannes G. Khinast. Performance evaluation of a high-precision low-dose powder feeder. AAPS PharmSciTech, Nov 2020. URL: https://doi.org/10.1208/s12249-020-01835-5, doi:10.1208/s12249-020-01835-5. This article has 25 citations and is from a peer-reviewed journal.

31. (fathollahi2024improvingcontinuouslossinweight pages 6-7): Sara Fathollahi, Valjon Demiri, Theresa R. Hörmann-Kincses, Snjezana Maljuric, Julia Massoner, Greg Mehos, and Johannes G. Khinast. Improving continuous loss-in-weight feeding accuracy by a novel hopper design. Journal of Pharmaceutical Innovation, Sep 2024. URL: https://doi.org/10.1007/s12247-024-09858-2, doi:10.1007/s12247-024-09858-2. This article has 2 citations and is from a peer-reviewed journal.

32. (stavrou2020assessingpowderflowability pages 255-258): Alexandros G. Stavrou. Assessing powder flowability at low consolidation stresses. Text, Jan 2020. URL: https://doi.org/10.15126/thesis.00852876, doi:10.15126/thesis.00852876. This article has 2 citations and is from a peer-reviewed journal.

33. (bostijn2019amultivariateapproach pages 6-10): N. Bostijn, J. Dhondt, A. Ryckaert, E. Szabó, W. Dhondt, B. V. Snick, B. V. Snick, V. Vanhoorne, C. Vervaet, and T. D. Beer. A multivariate approach to predict the volumetric and gravimetric feeding behavior of a low feed rate feeder based on raw material properties. International Journal of Pharmaceutics, 557:342–353, Feb 2019. URL: https://doi.org/10.1016/j.ijpharm.2018.12.066, doi:10.1016/j.ijpharm.2018.12.066. This article has 89 citations and is from a domain leading peer-reviewed journal.

34. (vasquezcruz2025frugalmodelpredictive pages 8-9): Rafael Isaac Vásquez-Cruz, Ernesto Castellanos-Velasco, and José Fermi Guerrero-Castellanos. Frugal model predictive control and active disturbance rejection for laser beam steering systems. Control Theory and Technology, 23:513-528, Aug 2025. URL: https://doi.org/10.1007/s11768-025-00281-7, doi:10.1007/s11768-025-00281-7. This article has 3 citations and is from a peer-reviewed journal.

35. (lahr2026l4acadoslearningbasedmodels pages 1-2): Amon Lahr, Joshua Näf, Kim P. Wabersich, Jonathan Frey, Pascal Siehl, Andrea Carron, Moritz Diehl, and Melanie N. Zeilinger. L4acados: learning-based models for acados, applied to gaussian process-based predictive control. ArXiv, Nov 2026. URL: https://doi.org/10.48550/arxiv.2411.19258, doi:10.48550/arxiv.2411.19258. This article has 18 citations.

36. (lahr2026l4acadoslearningbasedmodels pages 3-4): Amon Lahr, Joshua Näf, Kim P. Wabersich, Jonathan Frey, Pascal Siehl, Andrea Carron, Moritz Diehl, and Melanie N. Zeilinger. L4acados: learning-based models for acados, applied to gaussian process-based predictive control. ArXiv, Nov 2026. URL: https://doi.org/10.48550/arxiv.2411.19258, doi:10.48550/arxiv.2411.19258. This article has 18 citations.

37. (lahr2026l4acadoslearningbasedmodels pages 8-10): Amon Lahr, Joshua Näf, Kim P. Wabersich, Jonathan Frey, Pascal Siehl, Andrea Carron, Moritz Diehl, and Melanie N. Zeilinger. L4acados: learning-based models for acados, applied to gaussian process-based predictive control. ArXiv, Nov 2026. URL: https://doi.org/10.48550/arxiv.2411.19258, doi:10.48550/arxiv.2411.19258. This article has 18 citations.

38. (arango2023neuralnetworksfor pages 54-57): Camilo Gonzalez Arango, Houshyar Asadi, L. Kooijman, and Chee Peng Lim. Neural networks for fast optimisation in model predictive control: a review. ArXiv, Sep 2023. URL: https://doi.org/10.48550/arxiv.2309.02668, doi:10.48550/arxiv.2309.02668. This article has 51 citations.

39. (arango2023neuralnetworksfor pages 39-42): Camilo Gonzalez Arango, Houshyar Asadi, L. Kooijman, and Chee Peng Lim. Neural networks for fast optimisation in model predictive control: a review. ArXiv, Sep 2023. URL: https://doi.org/10.48550/arxiv.2309.02668, doi:10.48550/arxiv.2309.02668. This article has 51 citations.

40. (arango2023neuralnetworksfor pages 18-21): Camilo Gonzalez Arango, Houshyar Asadi, L. Kooijman, and Chee Peng Lim. Neural networks for fast optimisation in model predictive control: a review. ArXiv, Sep 2023. URL: https://doi.org/10.48550/arxiv.2309.02668, doi:10.48550/arxiv.2309.02668. This article has 51 citations.

41. (lahr2026l4acadoslearningbasedmodels pages 2-3): Amon Lahr, Joshua Näf, Kim P. Wabersich, Jonathan Frey, Pascal Siehl, Andrea Carron, Moritz Diehl, and Melanie N. Zeilinger. L4acados: learning-based models for acados, applied to gaussian process-based predictive control. ArXiv, Nov 2026. URL: https://doi.org/10.48550/arxiv.2411.19258, doi:10.48550/arxiv.2411.19258. This article has 18 citations.