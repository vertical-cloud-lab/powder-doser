# Literature-Backed Critique of the Rapid-Dispense Stop-Response Characterization

## Summary

The stop-response experiment is a sensible first attempt to characterize the post-halt dynamics of an Archimedean-auger powder doser. Several of the qualitative conclusions are directionally sound—particularly that afterflow dominates over threshold quantization and that settling is relatively rapid. However, the experiment has significant statistical, physical, and protocol weaknesses that prevent the claimed tau constant from being regarded as a validated plant parameter. Below is a structured critique organized by the five requested areas.

The following table summarizes all major findings:

| Critique Area | Specific Concern | Literature Finding | Recommendation/Implication |
|---|---|---|---|
| Validity | Treating \(\tau = \text{afterflow}/\text{flow}\) as a physical constant from the same noisy balance trace may be an errors-in-variables artifact. | Measurement error in explanatory variables and correlations causes attenuation and can distort inferred relationships; with noisy numerator and denominator estimates, apparent collapse can be partly statistical rather than physical. LIW/feeder studies typically characterize feed behavior with repeated calibration/verification runs and external catch-scale data rather than ratios from a single noisy derivative estimate (gillen2019experimentingwithmeasurement pages 26-29, gillen2019experimentingwithmeasurement pages 22-26, kelly2007someaspectsof pages 3-5, gillen2019experimentingwithmeasurement pages 1-5, gillen2019experimentingwithmeasurement pages 5-8, fathollahi2024improvingcontinuouslossinweight pages 2-4, bostijn2019amultivariateapproach pages 10-14). | Do not claim a physical constant from 10 trials and derived ratios alone. Estimate stop-response with a model that separates trigger overshoot, transport inventory, and measurement noise; report uncertainty from replicate runs and, ideally, use an external calibration of dynamic weighing and/or independent flow estimation. |
| Validity | Claiming “no tilt trend” with n=2 per angle and tilt-blocked order. | Screw/feeder performance depends on inclination, rotational speed, and fill level; fill level and conditioning can shift feed factor materially, while blockwise runs risk aliasing session drift onto angle. Feeder literature commonly emphasizes repeated characterization, calibration runs, and variability metrics (RSD/RE), often over minutes-long runs or multiple cycles, not 2 replicates per condition (owen2009predictionofscrew pages 8-10, owen2009predictionofscrew pages 10-11, bostijn2019amultivariateapproach pages 14-18, fathollahi2024improvingcontinuouslossinweight pages 6-7, fathollahi2024improvingcontinuouslossinweight pages 4-6, bostijn2019amultivariateapproach pages 10-14, li2020predictiveperformanceof pages 36-40). | Reframe as “no obvious trend in this pilot dataset.” Randomize or Latin-square angle order, increase replicates substantially, and include fill level/session as blocking factors or covariates. |
| Physics | Interpreting post-stop mass gain as only “in-flight transport delay/inventory.” | Auger literature explicitly notes that feed does not stop immediately when rotation ceases and that accuracy deteriorates with larger augers; coarse/fine concentric auger concepts exist precisely because screw stoppage overruns the target. DEM and feeder studies also show strong dependence of conveying behavior on speed, fill level, inclination, and flow regime (yang2007meteringanddispensing pages 6-7, owen2009predictionofscrew pages 8-10, owen2009predictionofscrew pages 10-11, owen2009predictionofscrew pages 14-15, owen2009predictionofscrew pages 15-15). | Interpret afterflow as a composite of at least: powder already airborne, screw-tip/tube holdup, lip avalanche, and mechanically induced release. A single \(\tau\) may be a useful local heuristic, but not yet a validated plant invariant. |
| Physics | Possible confounding by the balance’s own dynamic response and vibration sensitivity. | Dynamic weighing literature and feeder setups often require smoothing/filtering or dedicated compensation because fast acquisition plus vibration can make raw mass signals nonrepresentative of true instantaneous flow. Your own setup’s unstable post-tare oscillation and much higher in-process sigma are consistent with this concern (fathollahi2021developmentofa pages 2-4, gyurkes2023residencetimedistributionbased pages 2-4). | Independently characterize the balance+mount dynamics with known mass steps and with non-dispensing vibration/tap injections. Deconvolve or at least bound instrument settling before assigning 0.7–1.5 s entirely to powder settling. |
| Physics | Hard stop may not be the best endpoint actuation profile. | Literature on powder dosing frequently uses dual-stage or feed-forward approaches: high-rate bulk delivery, then reduced-rate precise delivery near target; this is partly because immediate cessation of screw delivery is imperfect and because fine control near target improves accuracy (pu2019acceleratingsamplepreparation pages 5-7, pu2019acceleratingsamplepreparation pages 2-5, fathollahi2021developmentofa pages 1-2, fathollahi2021developmentofa pages 4-5, fathollahi2021developmentofa pages 13-14, fathollahi2021developmentofa pages 12-13). | Test ramp-down or phase-switched stop profiles explicitly: hard stop vs decel vs stop-auger/keep-tap vs stop-tap/keep-auger. Measure whether controlled deceleration reduces overrun or merely redistributes it. |
| Protocol Improvements | Fixed 0.5 g threshold probes only one operating point and one part of the run. | Feed factor and discharge behavior vary with hopper fill level and with process progression due to densification/conditioning; single-threshold stop tests cannot separate early-run vs late-run inventory effects (bostijn2019amultivariateapproach pages 14-18, fathollahi2024improvingcontinuouslossinweight pages 6-7, bostijn2019amultivariateapproach pages 10-14, li2020predictiveperformanceof pages 36-40, fathollahi2020performanceevaluationof pages 4-5, fathollahi2021developmentofa pages 4-5). | Restore the original plan to randomize halt times/masses across the ramp. This is critical for identifying whether afterflow is state-dependent (mass already in tube, fill level, conditioning) rather than a universal delay. |
| Protocol Improvements | Tap and auger are fully confounded. | Vibration strongly affects powder flow and packing; literature notes screw-feeder variability can be strongly influenced by hopper vibration, and vibration can both initiate flow and alter apparent density/packing (yang2007meteringanddispensing pages 6-7, yang2007meteringanddispensing pages 7-9). | Run factorial stop-response tests: auger-only, tap-only, combined, and varied tap phase relative to auger position. Without this, the inferred \(\tau\) is for a combined actuator pattern, not for the auger plant alone. |
| Protocol Improvements | Fill level was uncontrolled/unmeasured despite literature showing major effects. | LIW and micro-feeder studies repeatedly show feed factor is highest at high fill and drifts as hopper empties; refill amount and solids stress alter densification and overfeeding (bostijn2019amultivariateapproach pages 14-18, fathollahi2024improvingcontinuouslossinweight pages 6-7, bostijn2019amultivariateapproach pages 10-14, li2020predictiveperformanceof pages 36-40, fathollahi2024improvingcontinuouslossinweight pages 1-2). | Add a way to track total feeder inventory or a surrogate fill metric each trial (pre/post weighing off-line, separate support scale, image-based level, or calibrated geometric estimate). Treat fill level as a primary experimental factor. |
| Controller Implications | “Halt at target − flow×\tau” may be usable but is likely too simplistic as a general law. | Better-performing feeder controls in the literature use feed-forward/state-dependent compensation based on material-specific profiles or dead-time models, not a single static offset. RTD/Smith-predictor concepts are used when dead time matters; feed-forward displacement/feed-factor profiles compensate known state dependence (fathollahi2021developmentofa pages 1-2, fathollahi2021developmentofa pages 4-5, fathollahi2021developmentofa pages 13-14, fathollahi2021developmentofa pages 12-13, gyurkes2023residencetimedistributionbased pages 2-4). | Use the present \(\tau\) only as an initial heuristic. Move toward a state-based anticipator/observer whose inventory estimate depends on flow, angle, fill level, and actuation mode; verify with settle-and-correct trim. |
| Controller Implications | Full-speed bulk flow appears incompatible with mg-class endpoint tolerance if stop lag is ~1 s. | Your own inferred overshoot scale (flow × lag) aligns with general coarse/fine dosing practice: bulk/high-rate phase until a switchover band, then reduced-rate precise phase. Published gravimetric powder systems likewise use fast and precise stages with smaller feed parameters near target (pu2019acceleratingsamplepreparation pages 5-7, pu2019acceleratingsamplepreparation pages 2-5, yang2007meteringanddispensing pages 6-7). | Quantitatively cap bulk-phase flow so worst-case lag + slug variability leaves enough remaining mass for trim. With ~1 s lag, full-speed operation should stop well before final tolerance band; the last tens of mg should be dispensed at much lower rate and/or discrete trim actuation. |
| Other | The observed tilt-move release event suggests reconfiguration itself is a dispensing mode. | Powder systems are sensitive to vibration, stress redistribution, and geometry changes; fill/stress changes can release material unexpectedly (fathollahi2024improvingcontinuouslossinweight pages 6-7, fathollahi2024improvingcontinuouslossinweight pages 1-2, yang2007meteringanddispensing pages 7-9). | Treat tilt changes as an actuator with its own transfer function and interlock them away from final approach unless explicitly modeled. Include “motion-only blank” trials in every characterization session. |
| Other | “Settling is fast and clean; waiting >2 s buys nothing” may overstate what this dataset shows. | Fast apparent convergence can reflect both true process settling and instrument filtering/averaging. Micro-feeder and GIW/LIW studies often rely on post-processing windows because raw signals are noisy and dynamically distorted (fathollahi2021developmentofa pages 2-4, gyurkes2023residencetimedistributionbased pages 2-4). | Report this more narrowly: in this setup, stable weight at +5 s agreed closely with ~2 s estimates for these 10 trials. Confirm across more powders, fill levels, and induced vibration states before hard-coding the wait time. |


*Table: This table summarizes the main reviewer-style critiques of the stop-response experiment across validity, physics, protocol, controller implications, and other issues. It condenses the literature-backed concerns and the most actionable recommendations for redesigning the experiment and interpreting its results.*

---

## 1. VALIDITY: Is tau = afterflow/flow ~ 1 s a sound reduction?

### 1.1. Ratio-of-estimates bias (errors-in-variables concern)

The tau computation divides afterflow (settled mass minus trigger-read mass) by the instantaneous flow rate estimated from the last ~1 s of the same noisy mass ramp. Both quantities are derived from the same ~10.4 Hz balance signal with in-process sigma ~1.8 mg/sample. This is a classic errors-in-variables situation. When both the numerator and denominator of a ratio contain measurement error, the resulting ratio can exhibit spuriously low variance and apparent constancy even when the underlying true relationship is more complex. Measurement error in regression attenuates slope estimates toward zero, and when measurement error is present in both variables used to compute a correlation or ratio, the distortion compounds (gillen2019experimentingwithmeasurement pages 26-29, kelly2007someaspectsof pages 3-5). Gillen et al. (2019) demonstrated that with measurement error accounting for 30-40% of variance—a range comparable to what is plausible in a 10-point ~1.8 mg sigma environment—estimated correlations and regression coefficients can be severely distorted relative to the true underlying relationships (gillen2019experimentingwithmeasurement pages 5-8). Even with N=1000 observations, measurement error causes persistent bias that cannot be eliminated by increasing sample size alone (gillen2019experimentingwithmeasurement pages 1-5).

The specific pathology here is that the flow-rate denominator is estimated from the same noisy signal that determines the afterflow numerator (since the trigger reading is on the same trace). This creates a mechanical correlation between numerator and denominator errors that can compress the apparent variance of their ratio—a well-known phenomenon in ratio estimators sometimes called "spurious self-correlation" or Pearson's fallacy.

**Recommendation:** Independently estimate the pre-halt flow rate (e.g., from commanded RPM × a separately calibrated per-revolution feed factor), and use that independent estimate to compute tau. Report the uncertainty propagated through the ratio, not just the sample standard deviation of the ratio.

### 1.2. "No tilt trend" with n=2 per angle

With only 2 replicates per tilt angle, the experiment has essentially zero statistical power to detect a trend. The within-angle ranges (e.g., 78–102 mg at 70° vs. 104–166 mg at 40°) substantially overlap with between-angle variability. A regression of tau on tilt with n=10 total and 5 groups of 2 would require very large effect sizes to reach significance. The claim should be "we did not detect a tilt trend, but we had very low power to do so."

Moreover, the tilt-blocked trial order (both replicates at one tilt run consecutively) means any session-level drift—fill level depletion, temperature, operator learning, powder conditioning—is aliased onto the tilt factor. The LIW feeder characterization literature routinely accounts for this by running at multiple fill levels, using catch-scale verification, and performing calibration runs with acceptance criteria (e.g., ±2% variation between consecutive runs) before experimental runs (fathollahi2024improvingcontinuouslossinweight pages 2-4). Feed factor characterization studies typically use 15+ materials with multiple screw speeds and systematic fill-level tracking (bostijn2019amultivariateapproach pages 10-14, li2020predictiveperformanceof pages 36-40).

**Recommendation:** Randomize or Latin-square the tilt order across the session. Increase to at least n=5–6 per condition (minimum for estimating standard deviation with any reliability). Include fill-level as a covariate.

---

## 2. PHYSICS: What does the post-halt afterflow actually consist of?

### 2.1. Afterflow is not a monolithic "in-flight inventory"

Yang and Evans (2007), in their comprehensive review of powder metering and dispensing, explicitly note a key problem with auger dosing: "the problem of dosing from an auger is that the feed does not stop as rotation ceases and the accuracy deteriorates as the auger diameter increases" (yang2007meteringanddispensing pages 6-7). This means that the afterflow your experiment measures is a composite of at least:

1. **Powder already airborne** between tube lip and cup (true in-flight inventory; transit time scales with fall height).
2. **Screw-tip dribble and tube holdup** — powder residing in the last pitch of the auger and on the tube lip that avalanches or slides out after the motor stops; this component depends on screw geometry, powder angle of repose, and residual kinetic energy.
3. **Tap-induced lip avalanche** — since tapping occurs concurrently with augering, the last tap before halt may loosen a slug that is mid-release at halt.
4. **Mechanical post-halt vibration** — the stepper motor stopping itself generates a mechanical transient that can shake powder loose (your own data shows 1.8 mg/sample in-process sigma vs. 0.012 mg static).

A single flow-proportional time constant (tau = afterflow/flow) lumps all these mechanisms into one number. This is a useful engineering heuristic but not yet a validated physical model. The fact that it "collapses" across tilts may simply reflect that at a single RPM (55), the dominant afterflow mechanism (screw-tip holdup + airborne inventory) scales roughly with flow for this one powder at this fill range—not that the relationship is universal.

### 2.2. Fill-level and densification effects on afterflow

The LIW feeder literature extensively documents how fill level affects feed factor (mass per screw revolution). Fathollahi et al. (2024) showed that higher fill levels cause greater densification at the hopper-screw interface, increasing feed factor deviations and overfeeding because compressive forces on powder particles at the hopper bottom increase (fathollahi2024improvingcontinuouslossinweight pages 6-7). Bostijn et al. (2019) found that feed factor is highest at 100% hopper fill and gradually decreases as the hopper empties, with a metric FFdecay marking the fill percentage where feed factor drops to 90% of its maximum (bostijn2019amultivariateapproach pages 10-14). Li (2020) confirmed that bulk density changes with fill level due to varying compression, which in turn affects the maximum mass flow rate achievable for a given screw speed (li2020predictiveperformanceof pages 36-40).

In your system, the ~53-63 g NaCl load sits in a tube whose total mass (~120 g) exceeds the balance capacity. Since you cannot weigh the tube to track depletion, you have no way of knowing how much the feed factor drifted across 10 trials. Given that prior sessions already showed fill-level-dependent feed factor and per-rev delivery, this is a first-order uncontrolled confound.

### 2.3. Screw speed, inclination, and mass flow rate nonlinearity

Owen and Cleary (2009) used DEM simulations (validated against experimental data) to demonstrate complex relationships between screw conveyor operating parameters and mass flow rate. Mass flow rate decreases strongly and linearly with increasing inclination until approximately 60°, beyond which it approaches a constant value (owen2009predictionofscrew pages 10-11). This is broadly consistent with your observation that feed rate peaks near 40-60° and falls at 70°. They also found that "no consistent power law scaling could be found to describe the relativity between these three axial particle velocity curves and the rotational speed of the screw" (owen2009predictionofscrew pages 15-15), indicating that mass flow rate does not scale perfectly linearly with RPM—a complication for any simple flow-proportional anticipation law.

Importantly, the DEM work shows that increasing fill level increases mass flow rate linearly at a given speed and angle, since average axial particle speed is nearly invariant to fill level (owen2009predictionofscrew pages 10-11). This means that as your tube empties across 10 trials, flow rate should decrease—but your tau computation uses the local flow estimate, so the ratio may appear more constant than either its numerator or denominator.

### 2.4. Balance dynamics confounding

The A&D HR-100A is an electromagnetic force compensation (EMFC) balance. EMFC balances have internal digital filters with user-selectable response times, typically ranging from ~0.5 s (fast/unstable) to several seconds (slow/stable). The balance's own step response settling time is likely 0.5–2 s depending on the filter setting. Your measured "settle time" of 0.7–1.5 s to within 2 mg of final is thus plausibly confounded with the balance's own dynamic response to a step input. The post-tare oscillation of ±20-45 mg over ~14 s that you observed further suggests the balance+mount system has significant mechanical resonances.

**Recommendation:** Characterize the balance's step response independently by dropping known masses (e.g., steel balls of known weight) from the dispensing height into the cup and recording the raw serial stream. This directly measures the instrument's settling envelope. Any powder afterflow whose timescale is shorter than the balance's step response is invisible to you; what you call "settling" is the convolution of true powder arrival and instrument filtering.

---

## 3. PROTOCOL IMPROVEMENTS

### 3.1. Randomization and blocking

The current tilt-blocked design aliases session drift onto the tilt factor. Since fill level decreases monotonically across trials (each trial dispenses ~0.5-0.7 g, so ~5-7 g total was removed across 10 trials from a ~53-63 g load), there is a systematic fill-level decline confounded with trial order and partially with tilt.

**Recommendation:** Use a fully randomized or balanced incomplete block design. If tilt changes themselves dispense powder (as your own secondary observation confirms), include deliberate "tilt-only blank" runs to quantify and subtract this effect.

### 3.2. Separating tap and auger contributions

The tap-while-rotating protocol means the afterflow tau reflects a combined actuator mode. You cannot attribute any fraction of the 80-180 mg overshoot to the auger alone vs. the tapper alone. The powder dispensing literature recognizes that vibration both initiates and modulates flow; vibratory methods can serve as independent metering mechanisms with different afterflow characteristics than screws (yang2007meteringanddispensing pages 6-7, yang2007meteringanddispensing pages 7-9).

**Recommendation:** Run a factorial design: (a) auger-only stop response, (b) tap-only stop response (from a pre-loaded static bed), (c) combined stop response at multiple relative phases. This is essential for controller design because the MPC-style architecture needs separate models for each actuator's transfer function.

### 3.3. Fixed 0.5 g threshold vs. randomized halt times

Using a fixed 0.5 g threshold means all stops occur at approximately the same point in the dispensing trajectory. The afterflow may depend on how long the auger has been running (priming effects, dynamic densification in the screw), how much powder remains in the tube (fill level), and the instantaneous state of the powder bed at the tube lip. The original plan to randomize halt times/masses would have provided much richer information.

**Recommendation:** In the next session, randomize the halt mass across the range of interest (0.1–2.0 g) to test whether tau is truly mass-independent. Also test whether stopping at the same mass from different fill levels yields the same afterflow.

### 3.4. Fill-level tracking

The LIW feeder literature universally monitors fill level as a primary variable. Fathollahi et al. (2024) designed their experiments with explicit refill levels (6-10 kg) and refill portions (2-4 kg) to systematically study fill-level sensitivity (fathollahi2024improvingcontinuouslossinweight pages 4-6). Bostijn et al. (2019) characterized feed factor decay profiles as functions of hopper fill percentage (bostijn2019amultivariateapproach pages 10-14).

**Recommendation:** Even if the tube cannot be weighed on the process balance, weigh it on a separate scale before and after each trial to track cumulative depletion. Alternatively, estimate fill level from dispensed cumulative mass. Treat fill level as an explicit covariate in analysis.

---

## 4. CONTROLLER IMPLICATIONS

### 4.1. "Halt at target − flow × tau" is a reasonable starting heuristic, but the literature supports state-dependent approaches

The simple anticipated-cutoff form (halt at target − flow × tau) is equivalent to a fixed dead-time compensator. The continuous pharmaceutical manufacturing literature uses more sophisticated approaches for analogous problems. Gyürkés et al. (2023) demonstrated that a Smith predictor incorporating the residence time distribution model reduced response time to disturbances by up to 50% compared to classic PID control in a dead-time-dominated blending process (gyurkes2023residencetimedistributionbased pages 2-4). Fathollahi et al. (2021) showed that feed-forward control using material-specific displacement feed factor profiles can reduce mean deviation from set-point from ~10.8% to ~1.0% by dynamically adjusting the actuator based on known state-dependent density variation (fathollahi2021developmentofa pages 12-13). These are not simple constant-offset approaches; they are state-dependent compensators.

**Recommendation:** Use the measured tau ≈ 1 s as a seed for a Smith-predictor or observer-based architecture. The observer should estimate in-flight inventory based on flow rate, time since last halt, fill level, and actuation mode—not just a fixed offset.

### 4.2. Coarse/fine (bulk/dribble) handoff

The dual-speed dosing strategy is well-established in gravimetric powder dispensing. Pu et al. (2019) described a system that explicitly divides each dispensing event into fast and precise feeding stages, with the fast stage using open-loop control at large feed parameters and the precise stage switching to PID feedback with reduced feed rates as the target mass is approached (pu2019acceleratingsamplepreparation pages 5-7, pu2019acceleratingsamplepreparation pages 2-5). Yang and Evans (2007) noted that one solution to the auger overrun problem is "a system of concentric augers in which the larger one provides rapid transfer to a weighing system but shuts off just before the predetermined amount is reached. A smaller concentric auger then provides the exact dose" (yang2007meteringanddispensing pages 6-7).

For your system, the implication is that 55 RPM full-speed augering is appropriate only during the bulk phase. With tau ~ 1 s and flow rates of 0.07-0.15 g/s, full-speed operation should cease when the remaining mass exceeds flow × tau + margin, i.e., ~150-250 mg before target. The last 100-200 mg should be dispensed at much lower auger speed and/or via discrete taps only.

### 4.3. Maximum bulk flow rate for ±2 mg endpoint

Given a ~1 s transport lag and ~10-20 mg slug quantization at full speed, the irreducible overshoot at full speed is on the order of 80-180 mg—far exceeding the ±2 mg target. To achieve ±2 mg endpoints, the dribble-phase flow rate must be low enough that flow × response_delay < 2 mg. With a balance response time of ~0.5-1 s, this implies a maximum dribble flow rate of ~2-4 mg/s—roughly 50-100× slower than the 70-150 mg/s bulk rate. The tap actuator (if delivering ~10-20 mg discrete slugs) is close to the right granularity for trim but may itself overshoot by one slug.

**Recommendation:** The recipe of "rapid bulk → anticipated early halt → settled verify → tap trim" is sound in concept. Quantitatively: switch from full-speed bulk to low-speed dribble at target − 200 mg; halt dribble at target − 20 mg (one slug margin); verify at +2 s; if short, deliver single taps with settle verification after each.

---

## 5. ADDITIONAL CONCERNS

### 5.1. Tilt moves as dispensing events

The observation that a 50°→60° tilt change released 25.4 mg is concerning and consistent with the general sensitivity of powder systems to geometry changes and stress redistribution (fathollahi2024improvingcontinuouslossinweight pages 6-7, fathollahi2024improvingcontinuouslossinweight pages 1-2). For a dosing system targeting ±2 mg, an uncontrolled 25 mg release during reconfiguration is catastrophic.

**Recommendation:** Either (a) fix the tilt angle throughout the dosing cycle and only change it between dispense events (after tare), or (b) model tilt changes as an explicit actuator with their own transfer function and interlock them during the final approach. Include systematic "tilt-only" blank trials to characterize the magnitude distribution.

### 5.2. Single powder, single session

All 10 trials used coarse granulated NaCl in a single session. NaCl is free-flowing, non-cohesive, and non-hygroscopic under typical conditions—it is among the easiest powders to dispense. Cohesive, fine, or moisture-sensitive powders will behave very differently: cohesive powders exhibit different flow regimes in screws (owen2009predictionofscrew pages 4-8), greater fill-level sensitivity (fathollahi2024improvingcontinuouslossinweight pages 6-7), and more erratic afterflow. The LIW feeder literature routinely tests 6-15 materials spanning a wide range of particle sizes, densities, and flow properties to establish general performance claims (li2020predictiveperformanceof pages 36-40, fathollahi2020performanceevaluationof pages 4-5).

**Recommendation:** Before generalizing any controller parameters, repeat the characterization with at least 2-3 powders spanning the intended use range (e.g., a fine cohesive API-surrogate and a free-flowing excipient) at multiple fill levels.

### 5.3. Post-tare oscillation of unknown origin

The ~14 s, ±20-45 mg oscillation observed after taring is a major concern for any sub-2 mg endpoint strategy. If the oscillation is mechanical (e.g., a structural resonance of the balance/mount/cup system excited by the tare zero-adjustment), it will recur every time the balance is disturbed—including when powder impacts the cup during dispensing. This could explain part of the in-process sigma inflation (1.8 mg vs. 0.012 mg static).

**Recommendation:** Investigate the post-tare oscillation immediately. Candidates include mechanical resonance of the cup/mount, air currents from the draft shield, or electromagnetic interference. Separate the balance step response from the mechanical transient by applying controlled step loads without powder.

---

## Concluding Assessment

The experiment provides a useful first look at stop-response behavior and correctly identifies afterflow as the dominant error source. However, the reduction to a single constant tau from 10 trials on one powder in one session, with confounded actuators, uncontrolled fill level, tilt-blocked ordering, and uncharacterized balance dynamics, is premature for controller parametrization. The recommended next steps are: (1) characterize the balance step response independently; (2) run a properly randomized, factorialized design with ≥5 replicates per condition, separating tap and auger contributions; (3) track fill level; and (4) test at least 2-3 additional powders. The qualitative finding that a ~1 s anticipation constant and a coarse/fine recipe are needed is well-supported and aligns with the broader powder dosing literature, but the quantitative value should be treated as provisional until these confounds are resolved.