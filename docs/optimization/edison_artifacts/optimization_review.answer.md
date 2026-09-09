Question: We are building an open-source benchtop powder doser for self-driving
laboratories (target application: high-throughput metal-AM alloy discovery,
but validated first on surrogate powders such as xanthan gum). The dispensing
head is an auger/screw conveyor driven by a NEMA-11 stepper (continuously
variable RPM), mounted on a servo that sets the dispensing tilt angle, with a
solenoid tapper (variable tap frequency) and an ERM vibration motor to combat
bridging/ratholing. Mass feedback comes from a laboratory balance under the
receiving vessel; the noisy balance signal is filtered with a Kalman filter
whose process-noise covariance Q and measurement-noise covariance R are
currently hand-set.

The controller is a two-phase gravimetric strategy, analogous to coarse/fine
or bulk/trickle dosing: (1) a "bang-bang" bulk phase runs the auger at a fixed
speed/tilt/tap setting until the filtered mass estimate crosses a cutoff near
the setpoint, then shuts off; (2) a "trim" phase closes the remaining error
either with a PI controller (gains KP, KI) modulating the auger, or with
discrete solenoid taps ("tap trim") that each shake loose a small increment of
powder. Note dispensing is irreversible: overshoot cannot be removed, only a
failed dose discarded.

A team member has brainstormed which user-defined parameters should be tuned
by an optimization campaign and what the objectives should be. Their verbatim
notes:

---
In creating the bang-bang controller followed by a trim method, we have
multiple parameters that are user-defined. Some of these parameters change
with the optimal control algorithm, while some don't. We have some parameters
that are influenced by collected test data and some that are just used because
they seem to make sense. This issue is to explore what can be optimized and
what are our objectives?

Possible optimization objectives:
Bang-bang
- fastest dispensing orientation
- minimize error
PI trim control
- minimize error
Tap trim control
- minimize error

Parameters:
Bang-bang (for speed)
- tilt
- auger rpms
- tap frequency
Bang-bang (for accuracy)
- Q (process noise covariance matrix)
- R (measurement noise matrix)
PI trim control
- KP
- KI

There are many other parameters we could potentially try to optimize, but this
is what I was thinking about for now. I was also thinking of making the
bang-bang a two-step optimization. We could first optimize the control
parameters (tilt, rpm, tapping) for the fastest possible dispensing and then
optimize to minimize the error of this already established configuration. We
have to be wary of including certain parameters in an optimization. For
example, including tilt and RPM's in the optimization to minimize error of the
bang-bang solution would most likely make the system way too slow.

---

Please write a literature-grounded review that answers, with citations to
peer-reviewed work (and authoritative vendor/application literature where
peer-reviewed sources are thin):

1. **Objectives.** In published work on gravimetric powder dosing —
   loss-in-weight feeding, pharmaceutical micro-dosing (e.g. Mettler-Toledo
   Quantos, Capsugel Xcelodose, tapping/vibratory capillary dosers), catch
   weighers, and self-driving-lab solid dispensers — what objective functions
   are used to characterize and optimize performance? Cover dosing time /
   throughput, mean absolute or relative error, repeatability (CV/RSD),
   overshoot rate, and minimum dispensable increment. How do published
   systems combine speed and accuracy: weighted scalarization, epsilon-
   constraint ("as fast as possible subject to error < tolerance"), or true
   multi-objective Pareto fronts? Given that overshoot is irreversible in
   powder dispensing, is an asymmetric penalty (penalizing overshoot more
   than undershoot, or deliberately undershooting the bulk phase and trimming
   up) the established practice?

2. **Two-stage vs. joint optimization.** Critique the proposed two-step
   scheme (first optimize tilt / auger RPM / tap frequency for fastest
   dispensing, then freeze those and optimize the accuracy-oriented
   parameters). When does sequential/greedy optimization of coupled
   controller parameters fail? In coarse-to-fine dosing specifically, the
   bulk-phase flow rate at cutoff determines the in-flight mass and
   spillover, so speed parameters directly bound achievable accuracy — how
   does the literature handle this coupling (e.g. optimizing the switchover
   threshold jointly with feed rate, flow-rate-dependent cutoff prediction,
   feedforward of estimated in-flight mass)? Is a constrained formulation
   ("minimize dose time s.t. |error| ≤ tol with x% confidence") preferable
   to two sequential single-objective problems?

3. **Which parameters belong in a black-box optimization at all?** For each
   parameter class, what does the literature recommend:
   (a) Kalman filter Q and R — should these be tuned by black-box
   optimization against dosing error, or identified from data (innovation-
   based/adaptive filtering, autocovariance least squares, offline noise
   characterization of the balance)? What is standard for mass-flow
   estimation in loss-in-weight feeders, where filter lag vs. noise directly
   trades off cutoff timing?
   (b) PI trim gains KP, KI — classical tuning (relay autotuning, IMC,
   Ziegler-Nichols variants) vs. data-driven/Bayesian tuning; what's known
   about controller tuning when the plant is an integrating, stochastic,
   quantized process (powder arrives in discrete avalanches)?
   (c) Mechanical/recipe parameters (tilt, auger RPM, tap frequency) — these
   shape the flow-rate regime; evidence on how auger speed, inclination
   angle, and vibration/tapping parameters affect mean flow rate AND
   flow-rate variability (pulsation, avalanching) for cohesive vs.
   free-flowing powders.
   (d) Structural parameters often forgotten: bulk→trim switchover
   threshold, trim tolerance band, balance settling wait — are these more
   impactful than the listed ones?

4. **Optimization algorithms for hardware-in-the-loop tuning.** Survey
   Bayesian optimization of controller parameters on physical systems where
   each evaluation is an expensive, stochastic real experiment: multi-
   objective BO (e.g. qNEHVI/EHVI) for speed-accuracy trade-offs, constrained
   and safe BO (e.g. SafeOpt) to avoid spills/jams, handling heteroscedastic
   noise and replication, typical evaluation budgets, and contextual /
   transfer approaches so a campaign tuned on one powder transfers to another
   (powder properties as context variables). Include examples from
   self-driving labs tuning their own hardware.

5. **Powder-physics limits.** What does the literature say about the floor
   on achievable dosing error — minimum stable increment from tapping or
   slow auger rotation (avalanche size statistics), balance noise and
   settling, electrostatics/cohesion effects — and how the optimal
   parameters shift with powder flowability (Hausner ratio, FFC)? This
   bounds what any optimizer can deliver and informs tolerance selection.

6. **Recommended protocol.** Synthesize into a concrete recommendation for
   this system: which parameters to optimize with which objective(s), which
   to identify/tune by other means, which to fix; whether to run screening
   (DOE/sensitivity analysis) before BO; how many replicates per condition
   given stochastic powder flow; and what to log so later campaigns can
   reuse the data. State the single most defensible formulation of the
   optimization problem for this doser.

Structure the answer with the section numbering above.



# Literature-Grounded Review: Optimization of an Open-Source Benchtop Powder Doser for Self-Driving Laboratories

## 1. Objectives

### 1.1 Performance Metrics in Published Gravimetric Dosing Systems

Published work on gravimetric powder dosing—spanning loss-in-weight (LIW) feeders, pharmaceutical micro-dosers, and self-driving laboratory solid dispensers—employs several well-established performance metrics. For continuous LIW feeders used in pharmaceutical manufacturing, the two principal metrics are **relative standard deviation (RSD)** of the feed rate, measuring variability, and **relative error (RE)** of the mean feed rate versus the setpoint (bostijn2019amultivariateapproach pages 1-6). Feed-rate consistency, feeding accuracy, and the relationship between achievable mass flow and motor command are the central performance concepts, with the "feed factor" (mass dispensed per screw revolution) serving as a material- and tooling-specific calibration quantity (li2020predictiveperformanceof pages 36-40). For micro-dosing systems, RMSEP (root mean square error of prediction) and TOST (two one-sided t-test) equivalence testing have been used to compare dosing methods against analytical balances (madarasz2023applicationofimage pages 37-41).

In self-driving laboratory contexts, dispensing percentage error across diverse solid materials and target masses is the primary reported metric. Comparative studies of the Mettler-Toledo Quantos, Chemspeed, and biomimetic dual-arm robotic dispensers report per-material errors for target masses from 20 mg to 1000 mg, with failure rates (complete non-delivery) of 23–27% across thirteen tested solids (jiang2023autonomousbiomimeticsolid pages 10-11, jiang2023autonomousbiomimeticsolid pages 10-10). Accurate and precise dosing is identified as particularly difficult below approximately 20 mg (seifrid2022autonomouschemicalexperiments pages 8-9).

For LIW feeders undergoing hopper refill, **maximum deviation**, **deviation time**, and **total deviation percentage** are used as response variables in predictive models (li2020predictiveperformanceof pages 30-36). Throughput (dosing time) is implicitly addressed through feed-rate setpoints and operating ranges, but most pharmaceutical LIW literature treats throughput as an input constraint rather than an explicit optimization objective.

### 1.2 Combining Speed and Accuracy

The literature does not commonly report formal multi-objective Pareto fronts for speed vs. accuracy in powder dosing. Instead, the dominant paradigm is an **epsilon-constraint** or threshold approach: the feed rate (speed) is specified as a setpoint, and the controller's task is to minimize deviation from that setpoint. This is functionally equivalent to "as fast as possible subject to error < tolerance." In micro-feeding, when screw speed falls below a usable threshold (~15% of rated speed), a temporal modulation strategy (rapid on/off cycling within 500 ms windows) is used rather than simply reducing RPM, representing a practical speed-accuracy tradeoff (madarasz2023applicationofimage pages 37-41). Weighted scalarization is used implicitly when PID controllers minimize a single error metric, but explicit Pareto-front construction for dosing speed vs. accuracy appears absent from the powder-dosing literature proper.

### 1.3 Overshoot Handling and Asymmetric Penalties

The irreversibility of powder dispensing is well recognized. The biomimetic robotic dispenser explicitly addresses this: if the target mass is exceeded, the system can restart dispensing, returning excess material to the hopper—an option available only because of the spatula-based design (jiang2023autonomousbiomimeticsolid pages 2-3, jiang2023autonomousbiomimeticsolid pages 1-2). For auger/screw-based systems where overshoot cannot be reversed, the established practice is to **deliberately undershoot in the bulk phase** and use a trim/fine phase to approach the target from below. Although no published powder-dosing system explicitly formulates an asymmetric loss function in mathematical terms, the two-phase (coarse/fine or bulk/trickle) architecture itself constitutes an asymmetric strategy: the cutoff is set conservatively below the target, accepting longer trim times to avoid irreversible overshoot. The Quantos system's "self-adaptive algorithm" similarly learns from previous dispenses to improve subsequent accuracy, implicitly penalizing overshoot more than undershoot (jiang2023autonomousbiomimeticsolid pages 2-3).

## 2. Two-Stage vs. Joint Optimization

### 2.1 Critique of Sequential Optimization

The proposed two-step scheme—first optimizing tilt/auger RPM/tap frequency for maximum speed, then freezing those and optimizing accuracy parameters—is a **greedy sequential decomposition** of a coupled problem. This approach fails when the parameters optimized in the first stage directly constrain the achievable performance in the second stage. In gravimetric dosing, this coupling is fundamental: the bulk-phase flow rate at the moment of cutoff determines the **in-flight mass** (powder that has left the auger but not yet reached the balance), and this spillover directly bounds achievable accuracy. Higher RPM and steeper tilt produce faster dispensing but also larger in-flight mass and greater post-shutoff variability.

The LIW feeder literature documents this coupling extensively. When a feeder transitions from gravimetric to volumetric mode during hopper refill, the screw speed is held at the last gravimetric value; when gravimetric control resumes, a sudden speed correction may be needed because powder density has changed, producing accuracy errors whose magnitude depends on the material and the flow rate at transition (jordaan2012thedevelopmentof pages 47-51, jordaan2012thedevelopmentof pages 8-12). Analogously, freezing speed parameters at their throughput-optimal values and then trying to minimize dosing error will likely find that the accuracy floor is set by physics (in-flight mass, pulsation amplitude) rather than by the remaining tunable parameters.

### 2.2 Literature Approaches to Coupling

In LIW feeding, the switchover between operating modes is handled through **feed-factor profiles**: the feed factor (mass per revolution) is characterized as a function of hopper fill level, and the refill point is triggered when the feed factor decays to 90% of its maximum (bostijn2019amultivariateapproach pages 10-14). This is analogous to a flow-rate-dependent cutoff rather than a fixed mass threshold. The gravimetric-to-volumetric transition uses previously calibrated volumetric characteristics to maintain feed rate during the "blind" period (jordaan2012thedevelopmentof pages 47-51). These approaches jointly consider speed and accuracy by making the transition strategy depend on the current flow regime.

### 2.3 Recommended Formulation

A **constrained single-stage optimization** is preferable to two sequential single-objective problems. The formulation "minimize dose time subject to |error| ≤ tolerance with p% confidence" naturally captures the speed-accuracy coupling by allowing the optimizer to explore the full joint parameter space while respecting accuracy requirements. This avoids the suboptimality of freezing speed parameters at values that may preclude the required accuracy.

## 3. Which Parameters Belong in Black-Box Optimization?

### 3(a) Kalman Filter Q and R

The noise covariances Q and R should **not** be tuned by black-box optimization against dosing error. The literature on Kalman filter noise identification provides well-established data-driven methods that are more principled and transferable:

- **Innovation-based methods**: The innovation sequence of a properly tuned Kalman filter should be white (uncorrelated). Mehra's output-correlation method and its variants estimate the steady-state Kalman gain from lagged innovation autocovariances, then recover Q and R (zhang2020ontheidentification pages 2-4, zhang2020ontheidentification pages 6-7).
- **Autocovariance least squares (ALS)**: Constructs multistep autocovariances of measurements and solves a linear least-squares problem for Q and R, with structural constraints ensuring symmetry and positive definiteness (zhang2020ontheidentification pages 4-5, zhang2020ontheidentification pages 25-25).
- **Maximum likelihood and expectation-maximization**: Tune covariances by maximizing the probability density of measurement residuals (zhang2020ontheidentification pages 1-2).
- **Post-fit residual methods**: R can be estimated from post-fit residuals using formulas involving the Kalman gain and innovation covariance (zhang2020ontheidentification pages 11-13).

A six-step successive-approximation procedure has been demonstrated across multiple test cases, producing estimates that contained true values within 95% probability intervals even in ill-conditioned systems (zhang2020ontheidentification pages 19-21). For this doser, R can be characterized offline from stationary balance readings, and Q can be identified from dispensing time-series data using innovation whiteness tests. Optimizing Q and R directly against dose error risks exploiting filter lag to produce artificially smooth (but delayed) estimates, yielding non-physical and non-transferable values.

### 3(b) PI Trim Gains KP, KI

PI gains are legitimate candidates for data-driven tuning, but the plant characteristics pose challenges for classical methods. The powder-dispensing process during trim is an **integrating process** (accumulated mass only increases) with **stochastic, quantized disturbances** (powder arrives in discrete avalanches). Classical Ziegler-Nichols or relay autotuning assumes continuous, approximately linear plant dynamics, which is violated here.

Multi-objective Bayesian optimization of PI controller parameters directly on physical hardware has been demonstrated for industrial drives, where gains Kp and Ki were tuned as integer-valued parameters with objectives including IAE, ITAE, overshoot, and oscillation. Useful Pareto-optimal solutions were found within 15–100 physical trials (petrovic2605towardsautonomouscommissioning pages 4-5, petrovic2605towardsautonomouscommissioning pages 1-2, petrovic2605towardsautonomouscommissioning pages 2-3). Guided BO with digital twins reduced hardware experiments by 46–57% compared to standard BO (nobar2024guidedbayesianoptimization pages 1-2). Safe BO (SafeOpt) provides theoretical guarantees against unsafe parameter evaluations during tuning (berkenkamp2023bayesianoptimizationwith pages 1-3, fiedler2501safetyinsafe pages 1-3).

The recommended approach is to obtain conservative initial gains from a simple integrating-process model (e.g., IMC tuning with the measured mass-per-revolution as the plant gain), then refine them with constrained BO that includes anti-windup limits and the switchover threshold.

### 3(c) Mechanical/Recipe Parameters (Tilt, Auger RPM, Tap Frequency)

These parameters shape the flow-rate regime and interact strongly with powder properties:

- **Tilt/inclination**: Nozzle inclination was found to be the strongest predictor of mass flow rate in vibration powder dispensing, converting all-or-nothing discharge into a controllable regime (greeley2023vibrationpowderdispensing pages 70-73, greeley2023vibrationpowderdispensing pages 39-45).
- **Vibration/tapping**: Effects are highly powder- and geometry-specific. A critical vibration threshold must be exceeded to initiate flow; above it, flow may increase, plateau, or decrease depending on frequency, amplitude, and orientation. Vibration parallel to the capillary axis achieved RSD as low as 5%, compared to 10% for perpendicular vibration. Increasing amplitude increased dose-mass variability (greeley2023vibrationpowderdispensing pages 17-20, greeley2023vibrationpowderdispensing pages 20-24).
- **Auger RPM**: Screw speed governs throughput but also pulsation. LIW feeders operate in an effective range of 20–90% of drive command; outside this range, flow becomes erratic (li2020predictiveperformanceof pages 36-40). The feed factor varies with material properties, and conditioned bulk density correlates with the maximum achievable feed factor.

These parameters should be screened via a fractional factorial DOE to identify dominant effects and interactions, then included as bounded variables in the joint BO campaign.

### 3(d) Structural Parameters Often Forgotten

The **bulk-to-trim switchover threshold** is arguably the single most impactful parameter not listed in the team's notes. It directly controls the transition from high-flow to precision mode and is strongly coupled to every other parameter. In LIW feeders, the analogous transition (gravimetric to volumetric during refill) is a primary source of dosing error, with maximum deviation, deviation time, and total deviation percentage serving as key response variables (li2020predictiveperformanceof pages 30-36, jordaan2012thedevelopmentof pages 47-51). The **trim tolerance band** determines when a dose is accepted; if set narrower than the minimum stable increment or balance noise, it causes futile cycling. The **balance settling wait** trades throughput against measurement reliability and should be identified from balance step-response testing rather than optimized purely against dose error.

The recommended parameter classification is summarized below:

| Parameter | Recommended Tuning Method | Rationale |
|---|---|---|
| Kalman Q and R | Identify from balance and dispensing time-series data. Estimate R from stationary-balance or residual data and Q from innovations, autocovariance least squares, maximum likelihood, or expectation maximization. Validate using innovation whiteness and consistency tests. Exclude raw covariance entries from the primary dosing BO. | Q and R represent stochastic dynamics and measurement noise rather than recipe controls. Data-based methods estimate them while enforcing covariance structure and positive definiteness. Direct optimization against dose error could exploit filter lag and produce nonphysical, nontransferable values (zhang2020ontheidentification pages 2-4, zhang2020ontheidentification pages 1-2, zhang2020ontheidentification pages 4-5, zhang2020ontheidentification pages 19-21). |
| PI gains KP and KI | Obtain conservative initial gains from an identified local plant model, IMC or integrating-process tuning, or relay tests. Refine them jointly with actuator limits, anti-windup, switchover, and trim settings using constrained or safe BO. | PI gains are valid controller-design variables, but the integrating, delayed, stochastic, and intermittent plant challenges conventional smooth-response tuning. Hardware studies show that BO can tune coupled PI gains with tens of trials and multiple response metrics, while safe BO restricts trials to certified operating regions (berkenkamp2023bayesianoptimizationwith pages 1-3, petrovic2605towardsautonomouscommissioning pages 4-5, petrovic2605towardsautonomouscommissioning pages 1-2, petrovic2605towardsautonomouscommissioning pages 2-3). |
| Tilt angle | Screen by DOE for each powder class, then include as a bounded recipe variable in joint constrained BO. Fix it only if sensitivity is negligible or angle changes impose excessive operational cost. | Inclination can dominate mean flow and can transform all-or-nothing discharge into a controllable regime. Its effect interacts with geometry, loading, and powder properties, so independently maximizing flow may increase variability or spillover (greeley2023vibrationpowderdispensing pages 70-73, greeley2023vibrationpowderdispensing pages 39-45). |
| Auger RPM | Calibrate mean flow and variability versus RPM first. Optimize bulk RPM jointly with cutoff prediction, while treating trim RPM or pulse duration as a separate bounded variable. | Screw speed governs throughput, pulsation, and powder remaining in motion after shutdown. LIW systems adjust speed to track mass flow, and usable ranges depend on tooling and powder properties; RPM therefore should not be frozen after speed-only optimization (bostijn2019amultivariateapproach pages 1-6, li2020predictiveperformanceof pages 36-40, bostijn2019amultivariateapproach pages 10-14). |
| Tap frequency | Screen frequency together with tap impulse, duration, and tilt. Retain it in BO only where it materially reduces bridging or increment variability. For tap trim, model the full mass-per-tap distribution. | Vibration responses are powder- and geometry-specific: flow may rise, fall, peak, or remain insensitive. Stronger excitation can increase dose variability, while excitation orientation and lower intensity have sometimes improved RSD (greeley2023vibrationpowderdispensing pages 17-20, greeley2023vibrationpowderdispensing pages 20-24, hou2024developmentofa pages 44-47). |
| Bulk-to-trim switchover threshold | Treat as a primary jointly optimized control variable. Prefer a flow-rate-dependent prediction of in-flight mass over a fixed mass offset. | The threshold controls bulk duration and post-shutoff spillover. It is strongly coupled to RPM, tilt, tapping, filtering delay, and shutdown dynamics; analogous gravimetric transitions exhibit accuracy errors when operating state or powder density changes (jordaan2012thedevelopmentof pages 47-51, bostijn2019amultivariateapproach pages 10-14, jordaan2012thedevelopmentof pages 8-12). |
| Trim tolerance band | Initialize from balance uncertainty and the empirical minimum stable increment. Then optimize or validate under a chance constraint, using separate lower and upper bounds when overshoot is costlier. | A band narrower than balance noise or a single tap or pulse increment causes futile cycling and extra delay, whereas a wide band sacrifices accuracy. Performance depends strongly on material and target mass, especially below approximately 20 mg (jiang2023autonomousbiomimeticsolid pages 10-11, jiang2023autonomousbiomimeticsolid pages 10-10, seifrid2022autonomouschemicalexperiments pages 8-9). |
| Balance settling wait | Identify using balance step-response and stability testing under motor, tapper, and vibration disturbances. Prefer adaptive stability detection; optimize only any remaining bounded timing parameter jointly with cycle time. | Settling time trades throughput against biased or noisy terminal-mass readings. Gravimetric dispensing requires reliable delivered-mass measurements, and enclosed, stable weighing improves consistency, so the wait should follow a statistical stability criterion rather than dose-error BO alone (jiang2023autonomousbiomimeticsolid pages 3-4, jiang2023autonomousbiomimeticsolid pages 1-2, tom2024selfdrivinglaboratoriesfor pages 4-5). |


*Table: The table classifies parameters for statistical identification, classical initialization, experimental screening, or joint constrained optimization. It highlights coupling among mechanical settings, switchover logic, trim resolution, and balance dynamics.*

## 4. Optimization Algorithms for Hardware-in-the-Loop Tuning

### 4.1 Bayesian Optimization for Physical Systems

Bayesian optimization (BO) is the method of choice for tuning controller parameters on physical systems where each evaluation is an expensive, stochastic real experiment. BO uses a probabilistic surrogate model (typically a Gaussian process) to approximate the objective landscape from limited data, and an acquisition function to select the next experiment by balancing exploration and exploitation (lee2026towardselfdrivinglaboratory pages 4-5).

### 4.2 Multi-Objective BO for Speed-Accuracy Tradeoffs

For the speed-accuracy tradeoff in powder dosing, **multi-objective BO** using Expected Hypervolume Improvement (EHVI) or its noisy parallel variant **qNEHVI** is directly applicable. EHVI selects experiments expected to increase the hypervolume dominated by the current approximate Pareto frontier, thereby producing well-distributed Pareto-optimal solutions (daulton2021parallelbayesianoptimization pages 1-2, daulton2021parallelbayesianoptimization pages 2-4). qNEHVI extends this to noisy observations by integrating over uncertainty in both the Pareto frontier and pending evaluations, and supports batch/parallel experiment selection with complexity polynomial in batch size (daulton2021parallelbayesianoptimization pages 4-6, daulton2021parallelbayesianoptimization pages 9-10). Performance has been validated with noise levels of 1–30% of objective range.

For the doser, the two objectives would be: (1) minimize dose time, (2) minimize |dose error| or maximize dose accuracy. The Pareto front reveals the fundamental speed-accuracy tradeoff, allowing the user to select an operating point appropriate for their application.

### 4.3 Constrained and Safe BO

**SafeOpt** and its variants provide safety guarantees during optimization by maintaining a certified safe set and only evaluating parameters predicted to satisfy safety constraints with high probability (berkenkamp2023bayesianoptimizationwith pages 1-3, fiedler2024onsafetyin pages 7-9). For the doser, safety constraints include: no powder spills (mass dispensed < vessel capacity), no auger jams (torque within limits), and no catastrophic overshoot. SafeOpt uses Gaussian process models of both the objective and constraint functions, starting from an initial safe parameter set and progressively expanding it through statistically justified exploration (blasco2025collaborativesafebayesian pages 13-16). Recent work (LoSBO) relaxes the RKHS norm assumption to require only a known Lipschitz bound, improving practical applicability (fiedler2501safetyinsafe pages 6-8, fiedler2501safetyinsafe pages 1-3). Constrained BO with particle swarms has also been demonstrated for safe adaptive controller tuning on physical systems.

### 4.4 Evaluation Budgets and Replication

Typical evaluation budgets for hardware-in-the-loop BO are **30–100 physical trials**. For industrial drive PI tuning, useful Pareto-optimal solutions were found with as few as 15–30 trials after 10 random initialization trials, with total wall times of 1.5–12 minutes (petrovic2605towardsautonomouscommissioning pages 4-5, petrovic2605towardsautonomouscommissioning pages 7-8). Self-driving laboratory optimization campaigns typically use 10²–10³ total experiments due to operating costs, reactant availability, and time constraints (hippalgaonkar2023evolutionguidedbayesianoptimization pages 1-2). For stochastic powder flow, 3–5 replicates per condition are advisable to estimate observation noise and heteroscedasticity, with the GP noise model updated as data accumulate.

### 4.5 Contextual and Transfer Approaches

Contextual BO, where powder properties (e.g., Hausner ratio, particle size distribution, bulk density) serve as context variables in the GP model, enables transfer of tuning campaigns across powders. The SafeOpt framework explicitly supports context variables for safe transfer to new situations and tasks (berkenkamp2023bayesianoptimizationwith pages 1-3, berkenkamp2023bayesianoptimizationwith pages 5-8). Multi-task GPs or multi-output GPs can model correlations among objectives across different powder types, enabling warm-starting of optimization for a new powder using data from previously characterized powders.

Evolution-guided Bayesian optimization (EGBO) augments qNEHVI with evolutionary selection pressure for better Pareto-front coverage and constraint handling, and has been demonstrated in self-driving labs for nanoparticle synthesis with three objectives and complex constraints (hippalgaonkar2023evolutionguidedbayesianoptimization pages 1-2, lee2026towardselfdrivinglaboratory pages 4-5).

## 5. Powder-Physics Limits

### 5.1 Minimum Stable Increment

The floor on achievable dosing error is set by the **minimum stable increment**—the smallest reproducible mass that can be dispensed in a single actuation event. For auger-based systems, this corresponds to the mass delivered by a fraction of a screw revolution, which depends on powder packing density, screw geometry, and flow behavior. For tap/vibration trim, it corresponds to the mass dislodged by a single tap or vibration pulse—essentially an avalanche event. Vibration dispensers have achieved controlled flow with variability (RSD) as low as 5% for the dispensed dose, but the absolute minimum dose depends strongly on powder properties and system geometry (greeley2023vibrationpowderdispensing pages 17-20, greeley2023vibrationpowderdispensing pages 20-24).

### 5.2 Powder Flowability Effects

Powder properties fundamentally determine dosing performance. Cohesive powders (high Hausner ratio, high compressibility index) are prone to bridging, ratholing, irregular bed density, and erratic flow, which narrow the usable operating range and increase dose variability (li2020predictiveperformanceof pages 30-36, hou2024developmentofa pages 44-47). The Hausner ratio and compressibility index quantify densification under tapping: higher values indicate greater cohesiveness and poorer flow, with implications for discharge consistency and dosing repeatability (fernandezUnknownyeardevelopmentandevaluation pages 40-43). Finer particles, higher compressibility, moisture, irregular shape, and electrostatic charging all degrade dosing performance.

For LIW feeders, cohesive powders may show densification during feeding, while coarser powders exhibit both densification and elastic recovery ("powder bed expansion"), each requiring different compensation strategies (fathollahi2020performanceevaluationof pages 1-2). The feed factor (mass per revolution) depends on conditioned bulk density, allowing maximum feed rate and usable operating range to be estimated from material characterization (li2020predictiveperformanceof pages 36-40).

### 5.3 Balance Noise and Settling

Analytical balance noise (typically 0.1–1 mg for laboratory balances) and settling time after disturbances (motor vibration, tapper impulses, ERM motor) set a measurement floor. The Kalman filter's lag-vs-noise tradeoff is directly relevant: aggressive filtering (large Q relative to R) reduces lag but increases noise transmission, while conservative filtering introduces delay that can cause overshoot at cutoff. Balance enclosure and environmental isolation improve weighing consistency (jiang2023autonomousbiomimeticsolid pages 3-4).

### 5.4 Implications for Tolerance Selection

For xanthan gum (a cohesive, compressible powder) and metal-AM powders (typically free-flowing, 15–45 µm spherical particles), the achievable accuracy floor will differ substantially. Metal powders with Hausner ratios near 1.0–1.1 should permit tighter tolerances, while cohesive surrogates like xanthan gum (Hausner ratio potentially >1.4) will require wider tolerance bands, slower trim speeds, and more aggressive anti-bridging measures. Any optimizer must be informed of these material-dependent limits to avoid setting unachievable targets.

## 6. Recommended Protocol

### 6.1 Pre-Optimization Characterization

Before launching a BO campaign:
1. **Characterize the balance**: Measure R (measurement noise covariance) from stationary readings and step-response settling time under motor/tapper disturbances.
2. **Characterize the powder**: Measure Hausner ratio, particle size distribution, bulk/tapped density, and angle of repose. Record these as context variables.
3. **Calibrate the auger**: Map RPM to mean flow rate and flow-rate variability (feed factor profile) across the usable RPM range (li2020predictiveperformanceof pages 36-40, bostijn2019amultivariateapproach pages 10-14).
4. **Identify Kalman filter parameters**: Estimate Q from dispensing time-series using innovation-based or ALS methods; validate with innovation whiteness tests (zhang2020ontheidentification pages 2-4, zhang2020ontheidentification pages 4-5).

### 6.2 Screening DOE

Run a fractional factorial design (e.g., 2^(k-p) with center points) over tilt, RPM, tap frequency, and switchover threshold to identify main effects and two-factor interactions. This requires approximately 16–32 runs with 3–5 replicates each, providing sensitivity information to fix insensitive parameters and bound the BO search space.

### 6.3 Joint Constrained Multi-Objective BO

**The single most defensible optimization formulation** is:

> **Minimize** (dose_time, |dose_error|) **subject to** P(overshoot > tolerance) ≤ α, no_jam, no_spill

with decision variables: {tilt, bulk_RPM, trim_RPM, tap_frequency, switchover_threshold, trim_tolerance_band, KP, KI}.

Use **qNEHVI** as the acquisition function with independent GPs for each objective, incorporating observation noise explicitly (daulton2021parallelbayesianoptimization pages 1-2, daulton2021parallelbayesianoptimization pages 4-6). Add safety constraints via SafeOpt-style certified safe sets or constrained EHVI to prevent spills and jams (berkenkamp2023bayesianoptimizationwith pages 1-3). Include powder properties (Hausner ratio, d50, bulk density) as context variables to enable transfer across powders (berkenkamp2023bayesianoptimizationwith pages 5-8).

### 6.4 Replication and Budget

- **Replicates**: 3–5 per condition to estimate stochastic variability of powder flow.
- **Budget**: 10 random initialization trials + 40–90 BO-guided trials (total 50–100), consistent with hardware-in-the-loop BO practice (petrovic2605towardsautonomouscommissioning pages 4-5, hippalgaonkar2023evolutionguidedbayesianoptimization pages 1-2).
- **Batch size**: q = 1–4 parallel evaluations if multiple dosing stations are available.

### 6.5 What to Log

For each dispensing trial, record: all actuator settings (RPM, tilt, tap frequency/pattern, ERM state), raw balance time series (pre-filtered), Kalman-filtered mass estimate, timestamps for phase transitions (bulk start, cutoff, trim start/end), final dispensed mass, ambient temperature/humidity, powder lot identifier, and hopper fill level. This enables: (a) offline re-identification of Q/R, (b) post-hoc analysis of in-flight mass and settling dynamics, (c) transfer learning to new powders, and (d) reproducibility of the full campaign.

### 6.6 Parameters to Fix vs. Optimize vs. Identify

- **Fix**: Balance settling wait (set by adaptive stability detection), ERM motor intensity (set to minimum effective anti-bridging level).
- **Identify from data**: Kalman Q, R (innovation/ALS methods); initial PI gains (from identified plant model).
- **Screen then optimize**: Tilt, bulk RPM, tap frequency, switchover threshold, trim tolerance band.
- **Optimize jointly**: Switchover threshold, trim RPM/pulse duration, KP, KI, and (bounded) tilt and bulk RPM.

This protocol separates signal-processing parameters (identified from data), fixed infrastructure parameters (characterized offline), and control/recipe parameters (optimized via constrained multi-objective BO), avoiding the pitfalls of the proposed two-stage sequential decomposition while remaining practical within a budget of ~50–100 hardware trials per powder.


References

1. (bostijn2019amultivariateapproach pages 1-6): N. Bostijn, J. Dhondt, A. Ryckaert, E. Szabó, W. Dhondt, B. V. Snick, B. V. Snick, V. Vanhoorne, C. Vervaet, and T. D. Beer. A multivariate approach to predict the volumetric and gravimetric feeding behavior of a low feed rate feeder based on raw material properties. International Journal of Pharmaceutics, 557:342–353, Feb 2019. URL: https://doi.org/10.1016/j.ijpharm.2018.12.066, doi:10.1016/j.ijpharm.2018.12.066. This article has 90 citations and is from a domain leading peer-reviewed journal.

2. (li2020predictiveperformanceof pages 36-40): Tianyi Li. Predictive performance of loss-in-weight feeders for continuous powder-based manufacturing. ArXiv, Jan 2020. URL: https://doi.org/10.7282/t3-6tgx-8f63, doi:10.7282/t3-6tgx-8f63. This article has 2 citations.

3. (madarasz2023applicationofimage pages 37-41): L Madarász. Application of image analysis for real-time monitoring and control of pharmaceutical processes. Unknown journal, 2023.

4. (jiang2023autonomousbiomimeticsolid pages 10-11): Ying Jiang, Hatem Fakhruldeen, Gabriella Pizzuto, Louis Longley, Ai He, Tianwei Dai, Rob Clowes, Nicola Rankin, and Andrew I. Cooper. Autonomous biomimetic solid dispensing using a dual-arm robotic manipulator. Digital Discovery, 2:1733-1744, Jan 2023. URL: https://doi.org/10.1039/d3dd00075c, doi:10.1039/d3dd00075c. This article has 67 citations and is from a peer-reviewed journal.

5. (jiang2023autonomousbiomimeticsolid pages 10-10): Ying Jiang, Hatem Fakhruldeen, Gabriella Pizzuto, Louis Longley, Ai He, Tianwei Dai, Rob Clowes, Nicola Rankin, and Andrew I. Cooper. Autonomous biomimetic solid dispensing using a dual-arm robotic manipulator. Digital Discovery, 2:1733-1744, Jan 2023. URL: https://doi.org/10.1039/d3dd00075c, doi:10.1039/d3dd00075c. This article has 67 citations and is from a peer-reviewed journal.

6. (seifrid2022autonomouschemicalexperiments pages 8-9): Martin Seifrid, Robert Pollice, Andrés Aguilar-Granda, Zamyla Morgan Chan, Kazuhiro Hotta, Cher Tian Ser, Jenya Vestfrid, Tony C. Wu, and Alán Aspuru-Guzik. Autonomous chemical experiments: challenges and perspectives on establishing a self-driving lab. Accounts of Chemical Research, 55:2454-2466, Aug 2022. URL: https://doi.org/10.1021/acs.accounts.2c00220, doi:10.1021/acs.accounts.2c00220. This article has 379 citations and is from a domain leading peer-reviewed journal.

7. (li2020predictiveperformanceof pages 30-36): Tianyi Li. Predictive performance of loss-in-weight feeders for continuous powder-based manufacturing. ArXiv, Jan 2020. URL: https://doi.org/10.7282/t3-6tgx-8f63, doi:10.7282/t3-6tgx-8f63. This article has 2 citations.

8. (jiang2023autonomousbiomimeticsolid pages 2-3): Ying Jiang, Hatem Fakhruldeen, Gabriella Pizzuto, Louis Longley, Ai He, Tianwei Dai, Rob Clowes, Nicola Rankin, and Andrew I. Cooper. Autonomous biomimetic solid dispensing using a dual-arm robotic manipulator. Digital Discovery, 2:1733-1744, Jan 2023. URL: https://doi.org/10.1039/d3dd00075c, doi:10.1039/d3dd00075c. This article has 67 citations and is from a peer-reviewed journal.

9. (jiang2023autonomousbiomimeticsolid pages 1-2): Ying Jiang, Hatem Fakhruldeen, Gabriella Pizzuto, Louis Longley, Ai He, Tianwei Dai, Rob Clowes, Nicola Rankin, and Andrew I. Cooper. Autonomous biomimetic solid dispensing using a dual-arm robotic manipulator. Digital Discovery, 2:1733-1744, Jan 2023. URL: https://doi.org/10.1039/d3dd00075c, doi:10.1039/d3dd00075c. This article has 67 citations and is from a peer-reviewed journal.

10. (jordaan2012thedevelopmentof pages 47-51): C Jordaan. The development of a control system for gravimetric feeding of a twin screw extruder. Unknown journal, 2012.

11. (jordaan2012thedevelopmentof pages 8-12): C Jordaan. The development of a control system for gravimetric feeding of a twin screw extruder. Unknown journal, 2012.

12. (bostijn2019amultivariateapproach pages 10-14): N. Bostijn, J. Dhondt, A. Ryckaert, E. Szabó, W. Dhondt, B. V. Snick, B. V. Snick, V. Vanhoorne, C. Vervaet, and T. D. Beer. A multivariate approach to predict the volumetric and gravimetric feeding behavior of a low feed rate feeder based on raw material properties. International Journal of Pharmaceutics, 557:342–353, Feb 2019. URL: https://doi.org/10.1016/j.ijpharm.2018.12.066, doi:10.1016/j.ijpharm.2018.12.066. This article has 90 citations and is from a domain leading peer-reviewed journal.

13. (zhang2020ontheidentification pages 2-4): Lingyi Zhang, David Sidoti, Adam Bienkowski, Krishna Pattipati, Yaakov Bar-Shalom, and David Kleinman. On the identification of noise covariances and adaptive kalman filtering: a new look at a 50 year-old problem. Jan 2020. URL: https://doi.org/10.36227/techrxiv.11663871.v3, doi:10.36227/techrxiv.11663871.v3. This article has 163 citations.

14. (zhang2020ontheidentification pages 6-7): Lingyi Zhang, David Sidoti, Adam Bienkowski, Krishna Pattipati, Yaakov Bar-Shalom, and David Kleinman. On the identification of noise covariances and adaptive kalman filtering: a new look at a 50 year-old problem. Jan 2020. URL: https://doi.org/10.36227/techrxiv.11663871.v3, doi:10.36227/techrxiv.11663871.v3. This article has 163 citations.

15. (zhang2020ontheidentification pages 4-5): Lingyi Zhang, David Sidoti, Adam Bienkowski, Krishna Pattipati, Yaakov Bar-Shalom, and David Kleinman. On the identification of noise covariances and adaptive kalman filtering: a new look at a 50 year-old problem. Jan 2020. URL: https://doi.org/10.36227/techrxiv.11663871.v3, doi:10.36227/techrxiv.11663871.v3. This article has 163 citations.

16. (zhang2020ontheidentification pages 25-25): Lingyi Zhang, David Sidoti, Adam Bienkowski, Krishna Pattipati, Yaakov Bar-Shalom, and David Kleinman. On the identification of noise covariances and adaptive kalman filtering: a new look at a 50 year-old problem. Jan 2020. URL: https://doi.org/10.36227/techrxiv.11663871.v3, doi:10.36227/techrxiv.11663871.v3. This article has 163 citations.

17. (zhang2020ontheidentification pages 1-2): Lingyi Zhang, David Sidoti, Adam Bienkowski, Krishna Pattipati, Yaakov Bar-Shalom, and David Kleinman. On the identification of noise covariances and adaptive kalman filtering: a new look at a 50 year-old problem. Jan 2020. URL: https://doi.org/10.36227/techrxiv.11663871.v3, doi:10.36227/techrxiv.11663871.v3. This article has 163 citations.

18. (zhang2020ontheidentification pages 11-13): Lingyi Zhang, David Sidoti, Adam Bienkowski, Krishna Pattipati, Yaakov Bar-Shalom, and David Kleinman. On the identification of noise covariances and adaptive kalman filtering: a new look at a 50 year-old problem. Jan 2020. URL: https://doi.org/10.36227/techrxiv.11663871.v3, doi:10.36227/techrxiv.11663871.v3. This article has 163 citations.

19. (zhang2020ontheidentification pages 19-21): Lingyi Zhang, David Sidoti, Adam Bienkowski, Krishna Pattipati, Yaakov Bar-Shalom, and David Kleinman. On the identification of noise covariances and adaptive kalman filtering: a new look at a 50 year-old problem. Jan 2020. URL: https://doi.org/10.36227/techrxiv.11663871.v3, doi:10.36227/techrxiv.11663871.v3. This article has 163 citations.

20. (petrovic2605towardsautonomouscommissioning pages 4-5): David Petrovic, Gian Antonio Susto, and Angelo Cenedese. Towards autonomous commissioning of industrial drives via multi-objective bayesian optimization. ArXiv, May 2605. URL: https://doi.org/10.48550/arxiv.2605.28478, doi:10.48550/arxiv.2605.28478. This article has 0 citations.

21. (petrovic2605towardsautonomouscommissioning pages 1-2): David Petrovic, Gian Antonio Susto, and Angelo Cenedese. Towards autonomous commissioning of industrial drives via multi-objective bayesian optimization. ArXiv, May 2605. URL: https://doi.org/10.48550/arxiv.2605.28478, doi:10.48550/arxiv.2605.28478. This article has 0 citations.

22. (petrovic2605towardsautonomouscommissioning pages 2-3): David Petrovic, Gian Antonio Susto, and Angelo Cenedese. Towards autonomous commissioning of industrial drives via multi-objective bayesian optimization. ArXiv, May 2605. URL: https://doi.org/10.48550/arxiv.2605.28478, doi:10.48550/arxiv.2605.28478. This article has 0 citations.

23. (nobar2024guidedbayesianoptimization pages 1-2): Mahdi Nobar, Jürg Keller, Alisa Rupenyan, Mohammad Khosravi, and John Lygeros. Guided bayesian optimization: data-efficient controller tuning with digital twin. IEEE Transactions on Automation Science and Engineering, 22:11304-11317, Mar 2024. URL: https://doi.org/10.48550/arxiv.2403.16619, doi:10.48550/arxiv.2403.16619. This article has 38 citations and is from a domain leading peer-reviewed journal.

24. (berkenkamp2023bayesianoptimizationwith pages 1-3): Felix Berkenkamp, Andreas Krause, and Angela P. Schoellig. Bayesian optimization with safety constraints: safe and automatic parameter tuning in robotics. Jun 2023. URL: https://doi.org/10.1007/s10994-021-06019-1, doi:10.1007/s10994-021-06019-1. This article has 535 citations and is from a highest quality peer-reviewed journal.

25. (fiedler2501safetyinsafe pages 1-3): Christian Fiedler, Johanna Menn, and Sebastian Trimpe. Safety in safe bayesian optimization and its ramifications for control. ArXiv, Jan 2501. URL: https://doi.org/10.48550/arxiv.2501.13697, doi:10.48550/arxiv.2501.13697. This article has 1 citations.

26. (greeley2023vibrationpowderdispensing pages 70-73): A Greeley. Vibration powder dispensing and gravity-fed powder delivery for directed energy deposition additive manufacturing systems. Unknown journal, 2023.

27. (greeley2023vibrationpowderdispensing pages 39-45): A Greeley. Vibration powder dispensing and gravity-fed powder delivery for directed energy deposition additive manufacturing systems. Unknown journal, 2023.

28. (greeley2023vibrationpowderdispensing pages 17-20): A Greeley. Vibration powder dispensing and gravity-fed powder delivery for directed energy deposition additive manufacturing systems. Unknown journal, 2023.

29. (greeley2023vibrationpowderdispensing pages 20-24): A Greeley. Vibration powder dispensing and gravity-fed powder delivery for directed energy deposition additive manufacturing systems. Unknown journal, 2023.

30. (hou2024developmentofa pages 44-47): Development of a micro-feeder for cohesive pharmaceutical powders This article has 2 citations.

31. (jiang2023autonomousbiomimeticsolid pages 3-4): Ying Jiang, Hatem Fakhruldeen, Gabriella Pizzuto, Louis Longley, Ai He, Tianwei Dai, Rob Clowes, Nicola Rankin, and Andrew I. Cooper. Autonomous biomimetic solid dispensing using a dual-arm robotic manipulator. Digital Discovery, 2:1733-1744, Jan 2023. URL: https://doi.org/10.1039/d3dd00075c, doi:10.1039/d3dd00075c. This article has 67 citations and is from a peer-reviewed journal.

32. (tom2024selfdrivinglaboratoriesfor pages 4-5): Gary Tom, Stefan Schmid, Sterling G. Baird, Yang Cao, Kourosh Darvish, Han Hao, Stanley Lo, Sergio Pablo‐García, Ella M. Rajaonson, Marta Skreta, Naruki Yoshikawa, Samantha Corapi, Gun Deniz Akkoc, Felix Strieth-Kalthoff, Martin Seifrid, and Alán Aspuru Guzik. Self-driving laboratories for chemistry and materials science. Chemical Reviews, 124:9633-9732, Aug 2024. URL: https://doi.org/10.1021/acs.chemrev.4c00055, doi:10.1021/acs.chemrev.4c00055. This article has 971 citations and is from a highest quality peer-reviewed journal.

33. (lee2026towardselfdrivinglaboratory pages 4-5): Heeseung Lee, Hyuk Jun Yoo, Hye Su Jang, Byeongho Park, Yang Jeong Park, and Sang Soo Han. Toward self-driving laboratory 2.0 for chemistry and materials discovery. Materials Horizons, 13(10):4712-4739, Jan 2026. URL: https://doi.org/10.1039/d5mh01984b, doi:10.1039/d5mh01984b. This article has 19 citations and is from a domain leading peer-reviewed journal.

34. (daulton2021parallelbayesianoptimization pages 1-2): Samuel Daulton, Maximilian Balandat, and Eytan Bakshy. Parallel bayesian optimization of multiple noisy objectives with expected hypervolume improvement. Jan 2021. URL: https://doi.org/10.48550/arxiv.2105.08195, doi:10.48550/arxiv.2105.08195. This article has 403 citations.

35. (daulton2021parallelbayesianoptimization pages 2-4): Samuel Daulton, Maximilian Balandat, and Eytan Bakshy. Parallel bayesian optimization of multiple noisy objectives with expected hypervolume improvement. Jan 2021. URL: https://doi.org/10.48550/arxiv.2105.08195, doi:10.48550/arxiv.2105.08195. This article has 403 citations.

36. (daulton2021parallelbayesianoptimization pages 4-6): Samuel Daulton, Maximilian Balandat, and Eytan Bakshy. Parallel bayesian optimization of multiple noisy objectives with expected hypervolume improvement. Jan 2021. URL: https://doi.org/10.48550/arxiv.2105.08195, doi:10.48550/arxiv.2105.08195. This article has 403 citations.

37. (daulton2021parallelbayesianoptimization pages 9-10): Samuel Daulton, Maximilian Balandat, and Eytan Bakshy. Parallel bayesian optimization of multiple noisy objectives with expected hypervolume improvement. Jan 2021. URL: https://doi.org/10.48550/arxiv.2105.08195, doi:10.48550/arxiv.2105.08195. This article has 403 citations.

38. (fiedler2024onsafetyin pages 7-9): Christian Fiedler, Johanna Menn, Lukas Kreisköther, and Sebastian Trimpe. On safety in safe bayesian optimization. ArXiv, Mar 2024. URL: https://doi.org/10.48550/arxiv.2403.12948, doi:10.48550/arxiv.2403.12948. This article has 37 citations.

39. (blasco2025collaborativesafebayesian pages 13-16): A Castell Blasco. Collaborative safe bayesian optimisation. Unknown journal, 2025.

40. (fiedler2501safetyinsafe pages 6-8): Christian Fiedler, Johanna Menn, and Sebastian Trimpe. Safety in safe bayesian optimization and its ramifications for control. ArXiv, Jan 2501. URL: https://doi.org/10.48550/arxiv.2501.13697, doi:10.48550/arxiv.2501.13697. This article has 1 citations.

41. (petrovic2605towardsautonomouscommissioning pages 7-8): David Petrovic, Gian Antonio Susto, and Angelo Cenedese. Towards autonomous commissioning of industrial drives via multi-objective bayesian optimization. ArXiv, May 2605. URL: https://doi.org/10.48550/arxiv.2605.28478, doi:10.48550/arxiv.2605.28478. This article has 0 citations.

42. (hippalgaonkar2023evolutionguidedbayesianoptimization pages 1-2): Kedar Hippalgaonkar, Andre Low, Flore Mekki-Berrada, Abhishek Gupta, Aleksandr Ostudin, Jiaxun Xie, Eleonore Vissol-Gaudin, Yee-Fun Lim, Qianxiao Li, Yew Soon Ong, and Saif Khan. Evolution-guided bayesian optimization for constrained multi-objective optimization in self-driving labs. Dec 2023. URL: https://doi.org/10.21203/rs.3.rs-3578558/v1, doi:10.21203/rs.3.rs-3578558/v1.

43. (berkenkamp2023bayesianoptimizationwith pages 5-8): Felix Berkenkamp, Andreas Krause, and Angela P. Schoellig. Bayesian optimization with safety constraints: safe and automatic parameter tuning in robotics. Jun 2023. URL: https://doi.org/10.1007/s10994-021-06019-1, doi:10.1007/s10994-021-06019-1. This article has 535 citations and is from a highest quality peer-reviewed journal.

44. (fernandezUnknownyeardevelopmentandevaluation pages 40-43): DB Fernández. Development and evaluation of a micro-dynamic method for characterising powder flowability at low consolidation stresses using small sample volumes. Unknown journal, Unknown year.

45. (fathollahi2020performanceevaluationof pages 1-2): Sara Fathollahi, Stephan Sacher, M. Sebastian Escotet-Espinoza, James DiNunzio, and Johannes G. Khinast. Performance evaluation of a high-precision low-dose powder feeder. AAPS PharmSciTech, Nov 2020. URL: https://doi.org/10.1208/s12249-020-01835-5, doi:10.1208/s12249-020-01835-5. This article has 25 citations and is from a peer-reviewed journal.
