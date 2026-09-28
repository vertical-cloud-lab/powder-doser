# Verdict

The compartment idea is good, but the current implementation is **not yet a defensible scientific benchmark for ranking these five controllers**. It is a useful behavioral test fixture. The main problems are:

1. Hopper powder moves to the lip instantaneously when the screw turns. There is no screw hold-up or rotation-dependent transport delay.
2. Controllers can access an idealized true landing-rate signal that the hardware does not measure.
3. Balance samples are generated on demand rather than on the balance’s clock. Repeated reads at the same simulation time produce independent noise and consume the same random-number stream used by the physical process.
4. The 10% conveying noise is applied every 50 ms, making its effective variance depend on timestep and RPM.
5. Nearly all material-property coefficients are uncalibrated scalar scores. Several have internal magnitude or normalization inconsistencies.
6. Variability is mostly independent from one substep to the next, whereas real screw feeding has run-level, low-frequency, screw-periodic, and arch-state correlations.

Those issues directly favor feedback, filtering, model-predictive control (MPC), and dual-filter methods in different ways. I would not use controller rankings from the current model as evidence about hardware performance.

# 1. Minimum model structure

## Add powder residing in the screw

Yes. For this rig, a screw-transport state is required.

The current transition is:

$$
\Delta m_{h\rightarrow lip}=F(h,\theta,C,p)\,\Delta N,
$$

so powder withdrawn from the hopper appears at the lip in the same 50 ms substep. That is physically equivalent to a zero-length screw.

Loss-in-weight feeder models commonly use at least a nonlinear steady feed relation plus dynamic lag and transport delay. Bascone et al. modeled twin-screw feeders as

$$
\tau\frac{d\dot m}{dt}+\dot m=\dot m_{\mathrm{level}},
\qquad
\dot m_{\mathrm{out}}(t)=\dot m(t-\vartheta).
$$

Their fitted industrial-feeder values spanned approximately $\tau=0.2$ to 119 s and $\vartheta=0$ to 210 s across powders, screw speeds, and feeder configurations. Those absolute values should **not** be copied into this much smaller rig, but the study establishes that delay and lag depend strongly on material, speed, and geometry rather than being negligible constants. Bascone also used a hopper-mass-dependent volumetric efficiency, $\eta=\alpha m^\beta$ [Bascone et al., 2019](https://doi.org/10.1016/j.ifacol.2019.12.223).

Hopkins describes the loss-in-weight system as the combination of weighing, screw metering, filtering, and control, not simply a static grams-per-revolution map [Hopkins, 2006](https://doi.org/10.1177/002029400603900801). Feed-factor studies likewise treat powder properties, screw configuration, and operating state as determinants of volumetric efficiency [Tahir et al., 2020](https://doi.org/10.1016/j.powtec.2019.09.071); [Bostijn et al., 2019](https://doi.org/10.1016/j.ijpharm.2018.12.066).

For this intermittent doser, a conventional time-only dead time is not quite right. Powder generally stops progressing when the screw stops. Model transport in **revolutions**, not only seconds.

### Recommended implementation

Add a mass-conserving $n$-cell screw state:

$$
q_{in}=F_{in}\omega,
$$

$$
\dot m_1=q_{in}-k_N\omega m_1,
$$

$$
\dot m_i=k_N\omega(m_{i-1}-m_i),\quad i=2,\ldots,n,
$$

$$
q_{s\rightarrow lip}=k_N\omega m_n.
$$

Here $\omega$ is revolutions per second. When $\omega=0$, transport freezes. The mean transport distance is

$$
N_{tr}=n/k_N\quad\text{revolutions}.
$$

Use `n = 3` initially. Set $N_{tr}$ from screw length divided by pitch and then fit effective slip using a colored-tracer or start-from-empty experiment. Before measurement, run sensitivity cases of 0.5, 1, and 2 effective revolutions rather than declaring one value correct.

Also initialize screw hold-up explicitly. A pre-primed screw and an empty screw are different experimental states.

### Effect on controller ranking

Transport hold-up does not necessarily mean all powder in the screw falls after cutoff. If the motor stops, much of it remains in the flights. The main effects are delayed response to new rotations and delayed evidence of feed-factor changes. This generally:

- worsens aggressive proportional-integral (PI) feedback if delay is ignored;
- increases the value of a correctly specified predictor or MPC;
- hurts MPC more than PI if MPC is given the wrong transport model;
- makes online feed-factor estimation slower and less identifiable near cutoff;
- can make short incremental rotations appear ineffective until their delayed packets reach the lip.

Add a separate coast/slump term only if hardware stop tests show post-stop motion:

$$
q_{coast}(t)=q_{coast,0}e^{-(t-t_{stop})/\tau_c}.
$$

Do not make all screw inventory drain automatically at stop.

# 2. Functional forms and magnitudes

The literature supports the qualitative dependencies, but not the present universal coefficients. Most should be treated as calibration parameters, with hierarchical variation by powder lot.

## Fill-level factor

Current:

$$
G_h=\min(1,h/0.30)^{0.7}.
$$

This is a reasonable smooth placeholder, but the fixed 30% breakpoint has no general physical meaning. Starvation depends on hopper geometry, throat area, screw fill, wall friction, and flow pattern. Bascone’s fitted form $\eta=\alpha m^\beta$ supports a power-law dependence, but its coefficients varied by material and feeder.

Use a fitted saturating form:

$$
G_h(h)=\left(\frac{h}{h+h_{50}}\middle/\frac{1}{1+h_{50}}\right)^\gamma,
$$

which is normalized to one at full hopper. Fit $h_{50}$ and $\gamma$ per powder or partially pool them. Until measured, use $h_{50}\in\{0.05,0.15,0.30\}$ and $\gamma\in\{0.5,1.0,2.0\}$ as sensitivity scenarios, not probability-based priors.

Your present low-fill sinusoid has 60% amplitude and activates discontinuously at 30% fill. Replace the discontinuity with a smooth amplitude:

$$
A_h(h)=A_{max}\,\operatorname{logistic}\!\left(\frac{h_c-h}{w_h}\right),
$$

and fit $A_{max}$ from mass-per-small-angle experiments.

## Tilt gain

Current:

$$
G_\theta=0.50+0.90s,
\qquad s=\frac{\sin\theta}{\sin45^\circ}.
$$

This forces every powder to have exactly a 2.8-fold gain from 0° to 45°. More importantly, it conflicts with the `Powder` documentation: `feed_factor_g_per_rev` is described as the full-fill, 45° value, but the code multiplies it by 1.4 and by cohesion. For example, nominal salt is 0.35 g/rev but the dry simulated value at 45° is about 0.474 g/rev. The corresponding 316L value is about 2.20 g/rev rather than 1.60 g/rev.

Normalize all gains at their reference condition:

$$
G_\theta(s)=g_0+(1-g_0)s^{p_\theta},
$$

so $G_\theta(1)=1$. Fit $g_0$ and $p_\theta$ by powder. A reasonable pre-calibration sensitivity grid is $g_0=0.2,0.5,0.8$ and $p_\theta=0.5,1,2$. Include a tilt-by-powder interaction. Do not impose the same ratio on salt, spherical metal powder, angular silicon, and lactose.

Confirm that `tilt_deg` maps to tube-axis angle relative to gravity. A sine law on mounting-plate degrees is otherwise only a convenient interpolation.

## Cohesion loss

Current:

$$
G_C=1-0.40C.
$$

This allows only a 40% continuous reduction between $C=0$ and $C=1$, followed by a separate hard arch threshold at $C=0.45$. Cohesive feeding usually shows a mixture of continuous loss, intermittent flow, wall adhesion, and complete blockage. One scalar from 0 to 1 is not a powder property with transferable units.

Keep a dimensionless latent flowability score if necessary, but use it explicitly as an empirical index:

$$
G_C=\exp(-\beta_C C),
$$

with $\beta_C$ fitted by powder family, plus a separate state-transition model for blockage. Better still, replace `cohesion` with measured inputs such as flow-function coefficient, conditioned bulk density, compressibility/Hausner ratio, and wall-friction class. Fine powders below roughly 50–100 µm are especially affected by van der Waals, electrostatic, and capillary forces; Fathollahi et al. discuss the resulting agglomeration and feeder-wall adhesion [Fathollahi et al., 2020](https://doi.org/10.1208/s12249-020-01835-5).

## Densification

Current:

$$
G_p=1+0.12p.
$$

A 12% maximum density effect is plausible as a trial value, but it is not established by the cited literature. Fathollahi’s micro-feeder studies show that effective displacement density can vary systematically through a powder charge and that the profile is material-specific; fine compressible powders densify, while some larger-particle powders also dilate or recover elastically [Fathollahi et al., 2021](https://doi.org/10.1208/s12249-021-02104-9).

The bigger problem is state location. One global `packing` variable is increased by a lip tap and then increases hopper-to-screw feed. Split it into:

- `hopper_compaction`, affecting throat filling and arching;
- `screw_fill_density`, affecting grams/revolution;
- `lip_consolidation`, affecting tap release.

If the solenoid strikes only near the exit, its direct effect on hopper compaction may be nearly zero. Fit the sign as well as magnitude. Do not assume tapping always increases subsequent screw feed.

## Tap ejection

Current:

$$
f_{tap}=0.35(0.20+0.80s)(1-0.55C).
$$

For a 0.20 g lip charge, this predicts approximately 13 mg per horizontal salt tap and 67 mg per 45° salt tap. Across the supplied powders it predicts about 49–69 mg at 45°. That conflicts with the README’s claimed rough range of 1–30 mg per tap.

Retain reservoir depletion, but use a hurdle-distribution tap model:

$$
P(\text{release})=\n\operatorname{logistic}(a_0+a_\theta s-a_C C+a_R\log(m_{lip}+\epsilon)),
$$

$$
f_{tap}\mid\text{release}\sim
\operatorname{Beta}(\mu_f\kappa,(1-\mu_f)\kappa),
$$

$$
\operatorname{logit}(\mu_f)=b_0+b_\theta s-b_C C-b_p p_{lip}.
$$

Then $m_{tap}=f_{tap}m_{lip}$, optionally rounded into one or more random agglomerate marks. Fit the entire repeated-tap decay sequence, including zero-yield taps, not only the mean first tap.

As an immediate correction, reduce the prefactor from 0.35 to approximately 0.10 if the 1–30 mg observation is reliable, then recalibrate. At 0.20 g lip mass this gives a dry-salt steep-tap expectation near 19 mg.

## Lip capacity

Current 45° capacities are about 22 mg for AlSi10Mg, 24 mg for 316L, 28 mg for salt, 48 mg for silicon, and 85 mg for lactose. Horizontal capacities are five times larger. These values come entirely from a 0.25 g constant and a linear angle-of-repose multiplier.

Angle of repose alone does not determine arching, retained wedge geometry, or wall adhesion. Bulk shear strength and wall friction are required for a mechanistic hopper calculation. For a control model, use measured retained mass:

$$
C_{lip}(\theta,C)=C_{min}+
\frac{C_{max}(C)-C_{min}}
{1+\exp[(\theta-\theta_{50}(C))/w_\theta]}.
$$

Measure it by overfilling the lip, allowing a fixed settling interval, and weighing retained mass at each tilt. The present 80% linear capacity loss can remain only as an explicitly unvalidated provisional curve.

## Gravity drain and avalanche

Current:

$$
k_d=1.2s^2(1-0.6C),\qquad
\dot m_{lip}=-k_dm_{lip},
$$

plus exponential relaxation of excess mass with a 0.3 s time constant. At 45°, dry salt has a lip half-life of about 0.61 s. This creates a smooth trickle for several seconds after screw cutoff.

Granular micro-discharge is often intermittent and thresholded, especially near jamming. Vibration can both clear arches and alter the discharge regime [Mankoc et al., 2009](https://doi.org/10.1103/physreve.80.011309). Replace the smooth overflow with a state-dependent marked point process:

$$
P(N_{av}>0\text{ in }dt)=1-e^{-\lambda_{av}dt},
$$

$$
\log\lambda_{av}=c_0+c_m(m_{lip}-C_{lip})_+ +c_\theta s-c_C C,
$$

with avalanche masses drawn from a gamma or lognormal distribution and truncated by available lip mass. Preserve an optional smooth component for genuinely free-flowing powders.

## Per-substep conveying noise

Current:

```python
conveyed *= 1 + Normal(0, 0.10)
```

at every 50 ms substep is not timestep invariant. At 60 rpm there are 20 independent draws per revolution, so the integrated per-revolution coefficient of variation is only about $0.10/\sqrt{20}=2.2\%$. At 10 rpm it is about 0.9%. Changing the internal timestep changes the process.

Replace it with three components:

1. run-level feed-factor variation;
2. autocorrelated within-dose drift;
3. screw-phase pulsation.

For example:

$$
z_{t+dt}=e^{-dt/\tau_z}z_t+
\sigma_z\sqrt{1-e^{-2dt/\tau_z}}\epsilon_t,
$$

$$
F_t=\bar F\exp(z_t-\tfrac12\sigma_z^2)
\left[1+A_1\sin(2\pi N+\phi_1)+A_2\sin(4\pi N+\phi_2)\right].
$$

Use $\tau_z=1,5,20$ s and feed-factor coefficients of variation of 3%, 10%, and 20% as benchmark sensitivity levels until spectra from repeated runs are available. Johnson et al. specifically used autoregressive moving-average time-series models for screw-feeder flow, supporting correlated rather than independent fluctuations [Johnson et al., 2022](https://doi.org/10.1016/j.ijpharm.2022.121776).

## Poisson clumps

The current fixed clump mass plus Poisson count imposes

$$
\operatorname{Var}(M)=E[M]m_{clump}.
$$

It is equidispersed, memoryless, and has identical clump sizes. Real cohesive discharge is usually overdispersed and serially clustered. Your nominal clump masses are about 1.0 mg for AlSi10Mg, 3.0 mg for 316L, 4.8 mg for salt, and 6 mg for silicon/lactose. These are unvalidated and, for salt, arise mainly from the large 400 µm particle-size entry.

Use a compound renewal or negative-binomial model:

$$
N\sim\operatorname{NegBin}(\lambda dt,r),
\qquad
m_j\sim\operatorname{Lognormal}(\mu_m,\sigma_m),
$$

and $M=\min(m_{available},\sum_jm_j)$. Make $\lambda$, mark size, and dispersion depend on lip state and actuation. Estimate them from individual landed-mass increments after deconvolving the balance response.

## Arching

The current model has a hard cohesion threshold, an arch rate proportional to RPM, spontaneous exponential clearing with mean 50 s, and 60% clearing probability per tap. It omits outlet-to-particle size ratio, fill stress, consolidation time, hopper geometry, and wall friction. It also treats arching and rat-holing as the same binary state, though rat-holing can permit reduced, intermittent feed rather than zero flow.

Use at least three states: `flowing`, `starved_or_rathole`, and `blocked`. Model transitions per revolution or per unit throat disturbance:

$$
\log\lambda_{F\rightarrow B}=
\beta_0+\beta_C C+\beta_p p_h+
\beta_h h+\beta_d\log(d_p/D_o)-\beta_\omega\log(\omega+\epsilon).
$$

Do not assume the RPM coefficient’s sign. Faster rotation can promote arch creation through compaction or clear it through agitation. Fit both formation and tap-clearing probabilities. Use Weibull dwell times if the clearing hazard changes with blockage age.

## Moisture and temperature

Current moisture increases linearly without an equilibrium:

$$
\dot M=k_h RH,
$$

while RH also adds directly to cohesion. This double-counts humidity, allows unbounded uptake, ignores desorption and hysteresis, and assumes temperature always reduces cohesion by 0.004 per °C. Relative humidity, equilibrium moisture, capillary forces, and electrostatic charge do not have that universal linear relationship.

Use a sorption-relaxation state:

$$
\dot M=\frac{M_{eq}(RH,T)-M}{\tau_M},
$$

with $M_{eq}$ from measured dynamic vapor sorption or a fitted GAB isotherm. Then model capillary cohesion from $M$, not from a second direct RH term. Add a separate electrostatic state because increasing humidity may accelerate charge leakage while high moisture can increase capillary cohesion.

Until sorption data exist, use categorical dry/ambient/conditioned material parameters measured after controlled exposure. That is safer than presenting the current `hygroscopicity` numbers as physical uptake constants.

## Balance

A first-order approximation is acceptable only after a step-response check. With $\tau=0.7$ s, the model reaches 95% in about 2.1 s, close to the HR-100A’s advertised approximately 2 s stabilization time. The manufacturer permits response adjustment and multiple data-output modes, so the exact response depends on configuration [A&D HR-A/HR-AZ manual](https://www.aandd.jp/products/manual/balances/hr-az_hr-a_manual.pdf).

The present observation implementation is not acceptable for a benchmark:

- every `read_balance()` call creates a new independent noise draw;
- unlimited reads at the same time allow arbitrary noise averaging;
- noise is white despite vibration being periodic and correlated;
- the stable flag is an invented 1 mg/0.5 s rule;
- there is no serial sample-and-hold, latency, dropout, drift, or tare uncertainty.

Implement a balance clock at the configured measured rate, for example the actual logged 5 or 10 Hz setting:

```python
if t >= next_balance_update:
    raw = balance_dynamics(true_pan_mass)
    reported = quantize(raw + bias + vibration_error)
    cached_report = reported
    next_balance_update += 1 / fs
return cached_report
```

Use one cached sample between updates. Fit a first- or second-order response from certified-weight step tests. Replace the disturbed 8 mg independent Gaussian with

$$
e_v(t)=A_a(t)\sin(2\pi f_at+\phi)+u_t,
$$

$$
u_{t+dt}=\rho_vu_t+\sigma_v\sqrt{1-\rho_v^2}\epsilon_t,
$$

where amplitude depends on auger, tap, and servo motion. Keep 0.15 mg quiet and 8 mg disturbed only if raw serial logs support those standard deviations. Add a session bias and slow random walk, with magnitudes estimated from repeated tare and reference-weight records.

# 3. Missing physics ranked by ranking impact divided by effort

| Priority | Addition | Ranking impact | Effort | Why it matters |
|---|---|---:|---:|---|
| 1 | Fixed-rate, sample-and-hold balance API; remove true-rate access | Very high | Low | Prevents filters and MPC from receiving impossible information or unlimited independent samples. |
| 2 | Separate random streams for process, sensor, context, and actuators | Very high | Low | Currently a controller’s read frequency changes future physical randomness. |
| 3 | Autocorrelated and run-level feed-factor variation | Very high | Low | Central to comparing fixed policy, Kalman filters, dual UKF, MPC, and Bayesian optimization. |
| 4 | Screw hold-up and revolution-domain delay | Very high | Medium | Changes identifiability, cutoff timing, and short-pulse response. |
| 5 | Empirical balance dynamics, drift, and colored vibration | High | Low–medium | Directly changes predictive cutoff and stable-wait time. |
| 6 | Stochastic lip avalanches and zero-yield taps | High | Medium | Changes overshoot tails and usefulness of tap-until-tolerance. |
| 7 | Three-state starvation/rat-hole/arch process | High for lactose/silicon | Medium | Creates long-tailed completion times and recovery actions. |
| 8 | Servo slew, overshoot, settling vibration, and command latency | Medium–high | Low | Tilt is a dominant actuator and currently nearly deterministic. |
| 9 | Tap-induced flooding/flushing state | Medium–high for fine powders | Medium | A tap may release more than lip inventory by mobilizing aerated powder; this can reverse whether tapping is the safest fine action. |
| 10 | Electrostatic adhesion/charge state | Potentially high for <50 µm metals | Medium–high | AlSi10Mg and 316L entries are in the size regime where tribocharging and wall adhesion can matter. Triboelectric response has been measured directly for AlSi10Mg and SS316L [Galindo et al., 2024](https://doi.org/10.1038/s41598-024-67295-0). |
| 11 | Full sorption kinetics | Medium | Medium–high | Important for transfer across conditioning histories, less important than fixing observation and delay first. |

For flooding, add an `aeration` state only if experiments show it:

$$
\dot a=k_{tap}I_{tap}+k_\omega\omega-k_{deaer}a,
$$

and let high $a$ temporarily increase drain or avalanche hazard. Do not add it solely because it exists in industrial fine-powder handling.

# 4. Stochasticity

The current source categories are sensible, but their families and correlations are not.

Use this hierarchy:

1. **Powder-lot random effects**, fixed for an entire campaign: bulk density, baseline feed factor, cohesion/flowability, electrostatic tendency.
2. **Dose-run random effects**, fixed for one dose: initial screw fill, initial lip mass, tare bias, initial packing.
3. **Within-dose latent drift**, correlated over seconds: feed factor, wall adhesion, balance bias.
4. **Screw-periodic fluctuations**, indexed by screw angle rather than timestep.
5. **Discrete events**: avalanches, clumps, arches, tap releases.
6. **Measurement noise**, generated on the balance clock and conditionally correlated during actuation.

Important omitted correlations include:

- feed factor and packing density;
- arch probability and preceding vibration/tap history;
- lip mass and next tap yield;
- clump size and waiting time;
- balance vibration amplitude and actuator command;
- humidity with electrostatic relaxation and capillary cohesion;
- hopper fill with both average feed and fluctuation amplitude.

A switching-covariance Kalman filter is being evaluated, so the benchmark must contain genuine regime persistence. An independent quiet/disturbed Gaussian switch with perfectly known actuation times is too easy. Include uncertain recovery duration and colored residual vibration after the actuator stops.

# 5. Fairness problems

## Remove privileged telemetry

`dose_rate_g_per_s` is a smoothed **true landed rate**, not a balance-derived estimate. Giving it to the rate-PI, UKF, or MPC controller makes the comparison invalid. All controllers should receive only data available from the same hardware interface:

- timestamped balance value and transmitted status byte;
- commanded and, if actually sensed, acknowledged stepper/servo states;
- environmental measurements actually installed;
- no `lip_g`, `in_flight_g`, `arched`, true feed factor, or true dose rate.

Keep full telemetry only for scoring and diagnostics.

`tap()` currently returns true ejected mass. Controllers must not receive that return value.

## Decouple random-number streams

The same `self.rng` drives balance reads, conveying noise, clumps, and arches. A controller that reads the balance more often consumes extra random numbers and thereby changes future powder physics. Create independent streams, for example:

```python
SeedSequence(seed).spawn(5)
# context_rng, process_rng, event_rng, balance_rng, actuator_rng
```

For common-random-number comparisons, pre-index continuous disturbances by physical time or screw angle. Action-dependent events cannot always be paired perfectly, so report both paired and independent-seed uncertainty.

## Avoid model-class favoritism

- A grey-box Hammerstein MPC will be favored if the simulator uses the same Hammerstein structure and parameters. Generate evaluation plants from a richer structure than the controller model.
- A dual UKF will be favored if feed factor is exactly a Gaussian random walk matching its assumed process model. Include smooth drift, run offsets, and occasional jumps, then test sensitivity.
- Bayesian optimization will be favored if training and test contexts reuse the same fixed powder coefficients. Hold out powder lots or parameter draws, not merely random seeds.
- Perfect actuator execution favors MPC and predictive cutoff. Include measured command latency, missed steps if observed, servo settling, and tap-energy variation.
- Exact knowledge of free-fall and tap timing favors prediction-based methods. Randomize these within measured repeatability and timestamp observations as the real software does.
- Controller-dependent simulation step sizes must not change process variance. Physics should evolve on its own fixed clock or with timestep-invariant stochastic differential equations.

Use identical wall-clock budgets, stopping rules, maximum tap counts, and settling criteria. Score final mass only after all in-flight and delayed balance dynamics have settled. Enforce no-overshoot against **true vial mass** for scoring, but do not expose that mass to controllers.

# 6. Changes I would make before running the comparison

## Required before any ranking claim

1. **Add a three-cell screw compartment.** Use the equations above; start with effective delays of 0.5, 1, and 2 revolutions for sensitivity, then replace them with tracer-test estimates.
2. **Make `feed_factor_g_per_rev` a true reference-condition parameter.** Normalize fill, tilt, cohesion, and packing gains to one at a documented reference condition. Fix the present 45° normalization error.
3. **Delete controller access to true dose rate and white-box telemetry.** Provide one common observation dataclass reflecting the serial and actuator interfaces.
4. **Implement balance sample-and-hold at the actual configured serial rate.** One noise realization per balance update, cached between updates.
5. **Split random-number generators.** Sensor queries must not alter physical trajectories.
6. **Replace 50 ms independent conveying noise.** Use run-level variation plus an Ornstein–Uhlenbeck/log-AR(1) feed-factor drift and screw-angle harmonics.
7. **Add session bias and balance drift.** Fit from empty-vial and reference-weight time series; do not guess final benchmark amplitudes.
8. **Replace deterministic lip overflow with a marked avalanche process.** Include no-release intervals and overdispersion.
9. **Use a hurdle/Beta tap model.** As a provisional magnitude correction, lower the 0.35 prefactor to about 0.10, then fit repeated-tap data.
10. **Replace binary arching with flowing/starved/blocked states.** Fit transition hazards and tap-clearing probability separately by powder and context.

## Required calibration experiments

For each powder and at least two lots where possible:

- 20–50 repeated fixed-angle rotations at each of 3 RPMs, 3 tilts, and 3 fill levels;
- start-from-empty, pre-primed, and stop/restart tests to identify screw hold-up and transport in revolutions;
- repeated tap trains after a controlled priming rotation at 4–5 tilts;
- passive lip-drain records after controlled overfill;
- raw 5–10 Hz balance logs for certified mass steps, auger motion, tap impulses, and servo moves;
- controlled humidity/exposure experiments, recording mass uptake rather than inferring it from time alone;
- outlet videos or acoustic/accelerometer data synchronized with mass to label clumps and arches.

Fit on some action sequences and validate on held-out mixed sequences that resemble controller behavior. Validate distributions, not just the current inequalities: mean error, variance, zero-increment probability, autocorrelation, power spectrum, tap-yield decay, arch dwell-time distribution, and upper-tail overshoot.

## Benchmark design

Run at least three model-fidelity scenarios:

- **Nominal:** posterior median calibrated parameters;
- **uncertain:** parameter draws from calibration uncertainty and new-lot random effects;
- **stress:** longer transport, stronger correlation, higher clump dispersion, and balance drift within observed or explicitly labeled sensitivity ranges.

Report paired controller differences with confidence intervals across contexts and seeds. Treat powder, lot, and context as hierarchical sources of variation. A controller ranking that changes across plausible calibration sets is not a resolved ranking.

# Bottom line

The hopper/screw/lip/free-fall/balance decomposition is appropriate after adding an explicit screw-transport compartment. The lip reservoir is a particularly useful state because it encodes your strongest bench observation. The present model, however, is dominated by hand-set functions and has observation-channel artifacts that can decide the controller comparison before control quality is tested.

Fix sensor realism, random-stream coupling, time-dependent noise, and screw hold-up first. Then calibrate tap and lip event distributions. Electrostatics and moisture deserve later states if the controlled experiments show they alter within-dose behavior. Until those changes and held-out validation are complete, call results a **simulation sensitivity study**, not evidence that one controller is superior on the doser.

### Discretionary analytical decisions

- Treated Bascone et al.’s industrial twin-screw parameter ranges as evidence for model structure, not as transferable parameter values for this small auger.
- Recommended a three-cell revolution-domain transport model rather than a pure time dead time because the rig uses intermittent incremental rotations.
- Chose hurdle/Beta tap release and negative-binomial/lognormal avalanche models as practical overdispersed alternatives; other marked renewal families could also be valid.
- Suggested 0.5, 1, and 2 transport revolutions and several feed-drift levels as sensitivity scenarios, not as empirically established values.
- Used the README’s 1–30 mg tap range to recommend reducing the provisional tap prefactor from 0.35 to about 0.10.
- Prioritized ranking validity and implementability over adding detailed discrete-element physics.
- Recommended hierarchical powder-lot and run-level variation because the intended inference concerns controller performance across powders and contexts, not one fixed nominal plant.
- Did not assign literature-derived numerical values to moisture, electrostatics, disturbed balance noise, or arch hazards where the available sources do not support transfer to this hardware.