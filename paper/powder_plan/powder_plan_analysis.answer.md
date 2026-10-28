## Bottom line

The revised draft is close to a coherent prospective validation story, but it is not internally closed yet. The central narrative is consistent in the abstract, Section 2.4, and Section 3.4: ten named powders, a three-phase bulk–fine–tap controller, fixed manually selected per-powder settings, and algorithmic optimization deferred. The main problems are one surviving two-phase label in Fig. 1, an incomplete acceptance rule at 50 mg, a serious mismatch between the ±5 mg stopping tolerance and the 20 mg accuracy criterion, ambiguity over whether silicon–glidant blends are additional test materials, and promises of several auxiliary studies that are not operationally specified.

The four-mass by ten-powder design gives at least 400 primary doses. That is defensible as a broad hardware validation campaign, but `n = 10` is only an ISO-style minimum. It is adequate for estimating mean bias, much weaker for coefficient of variation (CV), and too small for a useful overshoot-rate claim unless overshoot is common. The protocol also needs independent reload/day blocks, an uncertainty budget, powder characterization methods, and environmental controls.

## 1. Internal-consistency audit

### Definite contradictions or mismatches

1. **A two-phase label remains in Fig. 1d.** The controller box says **“coarse → trickle”**, while the abstract, Section 2.1, Section 2.4, Section 3.4, and Fig. 4 caption describe **bulk–fine–tap**. Replace the box text with “three-phase controller: bulk → fine → tap-to-target.” This is the clearest dangling reference to the older algorithm.

2. **The figure number in the request and compiled manuscript do not match.** In the supplied `main.pdf`, Fig. 3 is the generative-CAD outcomes figure; dispensing performance is **Fig. 4**. If the source draft calls the dispensing plot Fig. 3, labels and cross-references have not been rebuilt consistently. Audit the compiled numbering rather than editing prose by memory.

3. **Fig. 4b uses a ±10% band at every mass, but the text specifies ±5% above 100 mg and ±10% at 20 mg.** The graphic therefore depicts the wrong acceptance region for 500 mg and 5 g. It also says nothing about 50 mg, for which the manuscript currently gives no acceptance limit.

4. **The 50 mg target has no pre-registered accuracy limit.** The stated limits are “±5% above 100 mg” and “±10% at 20 mg.” Fifty milligrams falls into neither category. A reviewer cannot determine whether a 50 mg condition passes.

5. **The default ±5 mg terminal tolerance conflicts with the 20 mg criterion.** At 20 mg, ±5 mg is ±25%, while the proposed acceptance limit is ±10% or ±2 mg. The controller can therefore declare success while the dose fails the validation criterion. The stopping tolerance should be mass-dependent and strictly tighter than the relevant acceptance limit.

6. **The phase logic is incomplete for small targets.** A 0.5 g bulk-exit threshold exceeds the 500, 50, and 20 mg targets; a 50 mg fine-exit threshold equals or exceeds the 50 and 20 mg targets. State explicitly that phases whose entry or exit threshold exceeds the requested mass are skipped. Without this rule, “three phases at all four masses” is not executable as written.

7. **Termination is described in two incompatible ways.** Phase 3 says dosing continues “until the dose is within tolerance,” but the next paragraph says dosing terminates when filtered mass “reaches the target.” For an irreversible addition process, these are not equivalent. Define success, undershoot, and overshoot precisely and use one rule throughout.

8. **“Ten powders” becomes more than ten material conditions if blends are included.** Table 1 has ten rows, but fumed silica is proposed both neat and at **0.5–1 wt%** in fine silicon. A 0.5% blend, a 1% blend, neat fumed silica, and unmodified fine silicon are distinct formulations. Clarify whether:
   - the primary factorial validation is exactly the ten neat powders, with one preselected silicon–glidant blend as a secondary case; or
   - blends are part of the primary campaign, in which case state the exact concentration and the resulting number of formulations.

9. **“Fixed manually chosen parameters” is consistent, but “per-powder calibration” needs sharper wording.** Section 3.4 promises a characterization sweep over rotation yield, tap yield, and angle, after which fixed settings are selected manually. This is compatible with optimization being deferred, but it could be read as optimization by another name. Say that the sweep characterizes response and supports a documented manual selection rule; no automated search or post hoc tuning on validation outcomes is allowed.

10. **Fig. 4c risks implying that speed is optimized.** A CV-versus-speed sweep is presented as motivation for three phases, while the paper says settings are hand chosen and formal optimization is future work. This is not necessarily contradictory, but distinguish a predetermined characterization grid from algorithmic optimization and specify that final validation settings are frozen before validation replicates.

### Coherent elements

- The abstract accurately names ten powders, three phases, and an ISO 8655-inspired prospective protocol.
- Section 2.4 and Section 3.4 agree on the four targets and `n ≥ 10`.
- Section 3.4 clearly says parameters are configurable by powder but fixed manually in this paper.
- The Conclusions correctly defer algorithmic and Bayesian optimization.
- Table 1’s qualitative observations distinguish tests made on this platform from prior commercial-trickler experience in its caption.
- The deliberate status of the Fig. 4 data is communicated consistently in the text, figure, and caption. I do not treat that status as a defect.

### SI gaps and dangling commitments

The SI does not contradict the three-phase protocol, but it does not yet support it. It contains the bill of materials, abbreviated construction instructions, nozzle variants, and AI records, but no:

- ten-powder inventory or material identifiers;
- three-phase pseudocode or state diagram;
- parameter table and phase-skipping rules;
- gravimetric protocol, equations, acceptance matrix, or statistical analysis plan;
- environmental and balance-quality-control procedure;
- powder characterization methods;
- randomized run sheet or raw-data schema.

The SI also says all four nozzles will be tested “per nozzle and per powder.” That implies up to 40 nozzle–powder combinations before mass-level replication. Section 3.4 otherwise reads as validation of one production configuration. Define nozzle screening as a separate preliminary experiment on a limited, predeclared powder subset, then freeze one nozzle for the primary campaign.

## 2. Comparison with the digital-pipette precedent

### Point-by-point

| Element | Digital pipette v1 | Digital pipette v2 Commit | Powder-doser plan | Assessment |
|---|---|---|---|---|
| Standards structure | ISO 8655-6 gravimetry; errors compared with ISO 8655-2 limits | Same structure; direct v1 and ISO comparison | ISO-inspired because no powder equivalent exists | Appropriate, but do not imply formal ISO conformity |
| Test ladder | 10, 5, 1 mL: 100%, 50%, 10% of 10 mL nominal | 10, 5, 1 mL for device test; 0.2, 1, 5 mL in human comparison | 5 g, 500 mg, 50 mg, 20 mg | Covers a wider range, but it is not the ISO 100/50/10% ladder |
| Replication | `n = 10` manual; robotic test `n = 100` | Gravimetric test follows v1; human arm has four operators × five replicates per volume | `n ≥ 10` per powder–mass condition | Minimum is precedented; lacks a long-run condition |
| Bias and repeatability | Mean, systematic error, standard deviation/CV | Mean, systematic error, CV | Systematic error and CV | Add absolute SD and confidence intervals, not CV alone |
| External limits | Explicit ISO 8655-2 maximum permissible systematic and random errors | Same | Self-selected percentage limits | Necessary for powders, but rationale and separate bias/precision limits are incomplete |
| Calibration/resolution | Broad and fine pulse-length sweeps; linear regressions; ~0.02 mL actuator resolution | Broad and fine calibration plots; regular calibration recommended | Rotation/tap yield sweep and mass-flow curve are promised | Needs an explicit minimum controllable increment/resolution analysis |
| Comparator | Commercial micropipette under the same manual protocol | v1, ISO limits, and four experienced human operators | None | A manual spatula/hand-weighing arm is the most obvious missing benchmark |
| Property challenge | Sucrose viscosity sweep, four concentrations, `n = 10`, commercial comparator | Not repeated in the Commit | Ten powders spanning qualitative behavior; planned size/density/flow descriptors | The powder campaign is broader and more application-relevant if properties are measured rather than asserted |
| Robotic/operational endurance | Robotic arm, 100 transfers, common calibration, no significant degradation | Robotic operation plus tip attachment/removal functionality | Dose time and wear/fouling observations promised | Add a predeclared repeated-use/endurance sequence and refill/recalibration rule |
| Environment | Water temperature, air pressure, correction factor, balance resolution, taring, room humidity disclosed; acknowledged humidity outside ISO range | Temperature, pressure, correction factor, balance model/readability | Balance model/readability and quiet-window filtering only | Temperature, relative humidity, static control, vibration, draft enclosure, equilibration, and calibration checks are missing |
| Human factors | Experienced graduate operator; experimental chemist double-check | Four experienced operators; variance comparison using Levene’s test | No operator/comparator plan | Manual comparator and operator handling protocol should be added |
| Failure-specific metric | Droplet retention discussed | Tip contamination/attachment function addressed | Overshoot, stalls, timeout, fouling, actuation ablations | Strong powder-specific additions, but definitions are needed |

Sources: Yoshikawa *et al.*, *Digital Discovery* **2023**, DOI [10.1039/d3dd00115f](https://doi.org/10.1039/d3dd00115f), especially Methods 2.2–2.5 and Results 3.1–3.4; Yoshikawa *et al.*, *Digital Discovery* **2026**, DOI [10.1039/d5dd00336a](https://doi.org/10.1039/d5dd00336a), especially Evaluation and Calibration.

### Elements a reviewer familiar with those papers is likely to expect

1. **A calibration and effective-resolution analogue.** Measure delivered mass versus commanded auger angle/step count and versus tap burst, with repeats, at fixed tilt. Report slope, nonlinearity, heteroscedasticity, minimum reliably nonzero increment, and the distribution of the final increment. A flow-rate plot alone is not resolution.
2. **A matched manual baseline.** Have trained operators weigh the same targets and powders using a spatula or the lab’s normal method. Report accuracy, CV, time, overshoot, and failure/rework rate under the same balance and environmental conditions.
3. **Environmental records and controls.** Temperature, relative humidity, barometric pressure if buoyancy correction is used, draft shielding, vibration isolation, electrostatic mitigation, powder equilibration time, and order/time stamps.
4. **A durability or sequence test.** The v1 paper included 100 robotic deliveries. A reviewer may expect at least one predeclared long sequence for representative free-flowing and cohesive powders, with drift, fouling, refill events, and recalibration tracked.
5. **Explicit calibration governance.** State when calibration occurs, whether validation data can trigger retuning, and what happens after refill, cleaning, nozzle replacement, or a failed dose.
6. **A comparator to prior hardware where feasible.** A commercial trickler comparison for the silicon powders would be useful, but a manual arm is more generally attainable and should be primary.

### Powder-specific strengths absent from the pipette studies

- A ten-material matrix spanning free-flowing, cohesive, bridging, low-density, metallic, and semiconducting powders.
- Irreversible overshoot as a separate asymmetric outcome.
- Stalls, bridging, re-feed, fouling, dribble, and nozzle dependence.
- Auger/tap/vibration ablations.
- Particle-size distribution, bulk/tapped density, and flowability descriptors that can link material properties to performance.
- Static and humidity sensitivity, which are much more central for fines than for the pipette’s liquid tests.
- Safety and containment issues for AlSi10Mg, silicon fines, and fumed silica.

## 3. Adequacy of the metrics and mass ladder

### Is 10 × 4 × at least 10 defensible?

Yes, as a primary breadth study. It produces at least **400 validation doses**, before calibration, ablations, nozzle screening, blends, comparators, or endurance tests. Four targets over 20 mg–5 g test a 250-fold nominal range and are more informative for this hardware than blindly copying a pipette’s three-point volume ladder.

Call it an **operating-envelope mass ladder inspired by ISO’s replicated gravimetric structure**, not an ISO test-volume ladder. With 5 g as a nominal maximum, the points are 100%, 10%, 1%, and 0.4%, not 100%, 50%, and 10%.

### Statistical weaknesses

1. **`n = 10` gives imprecise CV estimates.** Under independent normal errors, the 95% confidence interval for the true standard deviation, and approximately for CV when mean uncertainty is small, is about **0.69–1.83 times the observed value**. Thus an observed 2% CV is compatible with a true CV of roughly 1.4–3.7%. Keep `n = 10` for the full matrix, but use more replicates at the 20 mg lower bound and in selected endurance conditions if precise repeatability claims matter.

2. **`n = 10` is poor for overshoot rates.** Even if zero overshoots occur, the one-sided exact 95% upper confidence bound is about **26%**; the two-sided upper bound is about **31%**. Report exact binomial confidence intervals and avoid claiming a low overshoot rate from ten trials. A larger selected-condition sequence is needed.

3. **Replicates may not be independent.** Ten consecutive doses from one fill are technical replicates within one loading state. Divide them across independent reloads and preferably days, for example randomized blocks with multiple doses per reload. Model reload/day as a block or random effect where enough levels exist.

4. **No uncertainty budget is specified.** Balance readability is 0.1 mg, only 0.5% of 20 mg, but readability is not measurement uncertainty. Actuation vibration, drift, static, air currents, tare repeatability, calibration uncertainty, filter behavior, and powder remaining in flight may dominate. Quantify idle and actuated zero noise, repeatability of a check mass, drift over a run, and uncertainty of mass differences.

5. **CV at 20 mg needs qualification.** If mass noise is comparable to the between-dose standard deviation, subtracting or ignoring it can distort the inferred dosing variability. Report the raw variance and balance-noise baseline; do not “correct” variance unless the measurement model and independence assumptions are justified.

6. **Acceptance is not statistically defined.** “±5% accuracy” could mean individual-dose tolerance, mean systematic error, or a confidence interval for bias. ISO separates systematic and random errors. Pre-register separate limits for:
   - absolute and relative mean bias;
   - SD or CV;
   - individual-dose success;
   - overshoot rate;
   - timeout/stall rate;
   - dose time.

7. **No multiplicity strategy is needed for a pass/fail engineering matrix if every condition must pass**, but the manuscript should not conduct 40 isolated significance tests and celebrate selected `p < 0.05` results. Report estimates and confidence intervals across all conditions. If inferential comparisons or property–performance associations are tested, predeclare the models and control false discovery rate.

### Under-specified physical characterization

“Size distribution, bulk/tapped density, flowability class” is not enough. State methods and replicate counts now:

- supplier, lot, grade, composition, and storage history for each material;
- moisture content or loss-on-drying where relevant;
- particle-size distribution method and reported percentiles, such as D10/D50/D90, with dispersion mode stated;
- loose bulk and tapped density method;
- Hausner ratio and Carr index if derived from those densities;
- angle of repose and/or a defined shear-cell flow function where instrument access permits;
- particle morphology source or imaging method, especially for AlSi10Mg and silicon;
- relative humidity and conditioning duration before testing;
- electrostatic-control procedure.

Do not call qualitative observations a “flowability class” unless the classification rule is defined.

### Other over-promises

- Section 2.4 promises property characterization, three-way actuation ablations, balance-noise studies, wear/fouling observations, four-nozzle testing, ten-powder validation, blends, and the full mass ladder. This can become several papers’ worth of experiments. Mark the 400-dose matrix as primary and identify smaller, predeclared representative subsets for nozzle, ablation, blend, and endurance studies.
- The Conclusions currently state that the doser “can” provide closed-loop dosing in a way that reads as a demonstrated performance conclusion, while the validation campaign is prospective. Until real data exist, restrict claims to construction, operation, and the protocol; accuracy and operating-envelope claims must follow the measurements.
- The rationale that error contributes less than one atomic percent in a “typical five-component blend” is too compressed. Composition error depends on component fraction, molar masses, covariance among doses, and total batch mass. Provide the derivation and scenario, or describe the limits as engineering targets rather than a generally proven composition guarantee.

## 4. Ranked edits that can be made before data collection

### Priority 1: make the protocol executable and internally consistent

1. **Fig. 1d:** Replace “Controller (coarse → trickle)” with “Three-phase controller (bulk → fine → tap-to-target).” If space permits, show the three state transitions and balance feedback.
2. **Section 3.4:** Add phase-entry rules: bulk is skipped when the target is at or below the bulk threshold; fine is skipped when the target is at or below the fine threshold. State the starting phase for all four target masses.
3. **Section 3.4:** Replace the fixed ±5 mg stopping rule with a predeclared target-dependent terminal tolerance that is tighter than the acceptance limit. Define whether stopping occurs below target to accommodate expected in-flight powder.
4. **Sections 2.4 and 3.4:** Add an explicit acceptance matrix for all four masses. Separate bias, CV/SD, individual-dose tolerance, overshoot, timeout/failure, and time. Define whether confidence bounds or point estimates determine passage.
5. **Section 3.4:** Define outcomes mathematically. For dose `i`, report error `e_i = m_i − m_target`; systematic error as mean absolute and relative error; sample SD; CV; overshoot indicator and threshold; dose time start/end; stalls; timeouts; aborted doses; and whether failed doses remain in the denominator.
6. **Fig. 4b and caption:** Replace the uniform ±10% band with the actual piecewise acceptance region, or remove the band until the complete acceptance matrix is fixed.

### Priority 2: freeze the experimental design and prevent post hoc tuning

7. **Section 3.4:** State that calibration and manual parameter selection use a separate training/calibration dataset. Freeze one versioned parameter profile per powder before validation. Validation outcomes must not be used to retune that profile without restarting the affected validation block.
8. **Table 1 and Section 2.4:** Resolve neat powders versus blends. Name the exact glidant concentration, or move blends into a clearly labeled secondary study. Avoid “0.5–1 wt%” as a validation condition.
9. **Section 3.4:** Specify the primary design as 10 powders × 4 targets × a stated replicate count, then list secondary subsets for nozzle comparison, actuation ablation, glidant blend, and endurance. State which nozzle is used in the primary campaign.
10. **Section 3.4/SI:** Add randomized blocking across target masses, independent reloads, run days, cleaning, refill, and recalibration rules. Preserve chronological order in the raw data even if plots are sorted.
11. **Section 3.4/SI:** Add a manual hand-weighing comparator for a manageable representative subset, ideally one free-flowing, one cohesive, fine silicon, and the four target masses. Use the same balance and report time, bias, CV, overshoot, and rework/failure.
12. **Section 3.4/SI:** Add an endurance sequence with substantially more than ten doses for representative easy and difficult powders. Track drift, stalls, deposits, cleaning, and parameter changes.

### Priority 3: add measurement assurance and powder methods

13. **Section 3.4:** Record temperature, relative humidity, draft-shield status, balance leveling/calibration checks, vibration isolation, static-control method, conditioning time, and elapsed time since powder loading. Pressure is needed if an air-buoyancy correction is applied; otherwise explain why it is negligible relative to the acceptance limits.
14. **Section 3.4/SI:** Add a concise uncertainty-budget plan covering balance calibration, repeatability, drift, tare, static, actuation-induced disturbance, filtering, and in-flight settling. Report unfiltered raw balance streams as well as filtered values.
15. **Section 3.4:** Specify particle-size, moisture, bulk/tapped density, flowability, and morphology methods, with replicate counts and supplier/lot metadata.
16. **Section 2.4/SI:** Define the calibration/resolution experiment: commanded rotation or tap burst versus delivered mass, replicate count, regression or nonparametric summary, usable range, minimum nonzero increment, and hysteresis/refill checks.
17. **Experimental safety subsection:** State handling controls for combustible or respirable metal/silicon fines and fumed silica, including containment, respiratory protection as applicable, ignition-source control, grounding/static mitigation, and waste handling.

### Priority 4: align claims and supporting material

18. **Abstract:** Keep “we define … a validation protocol” until results exist. Do not imply validated accuracy or generality. Once data are inserted, replace prospective wording with the measured operating envelope and numerical results.
19. **Section 2.4:** Change “acceptance targets, chosen so that…” to either a documented calculation with assumptions or “pre-registered engineering targets selected for the intended alloy-blending use case.”
20. **Conclusions, first sentence:** Avoid concluding accuracy before the campaign. A safe current version is: “We built and operated a single-channel, 3D-printed auger powder doser with closed-loop gravimetric feedback for under $200, excluding the balance.” Add performance claims only after results.
21. **Conclusions/future work:** Preserve the statement that this paper uses manually chosen fixed profiles and that automated/Bayesian optimization is future work. Add that the validation set remains untouched by any future optimizer.
22. **SI:** Add the protocol, equations, acceptance table, three-phase pseudocode/state diagram, parameter-profile template, powder metadata table, run sheet, data dictionary, exclusion/failure rules, and planned statistical outputs.
23. **SI Section S3:** Replace “per nozzle and per powder” with the exact nozzle-screening design and the rule used to select the production nozzle before primary validation.
24. **Whole manuscript:** Repair broken table references that render as “( 1)” or bare “1,” audit Fig. 3/Fig. 4 numbering, and use one term consistently: **bulk–fine–tap-to-target**.

## Recommended minimum defensible final campaign

- **Primary:** 10 clearly defined powder/formulation rows × 4 target masses × at least 10 validation doses, using frozen profiles and one frozen nozzle.
- **Independence:** distribute replicates across at least three independent reload/day blocks rather than one uninterrupted fill.
- **Lower bound:** increase replication at 20 mg if strong CV or overshoot claims are planned.
- **Comparator:** manual hand weighing for a predeclared representative subset.
- **Resolution:** separate rotation- and tap-increment calibration curves with repeated measurements.
- **Endurance:** one easy and one difficult powder in a longer sequential run.
- **Reporting:** mean bias with 95% confidence interval, SD and CV with uncertainty intervals, individual errors, exact binomial intervals for overshoot/failure rates, median and tail dose times, and all failed or timed-out attempts retained.

This would match the digital-pipette papers’ strongest features while adding a genuinely powder-specific operating-envelope study. It would also prevent the most likely reviewer criticism: a broad list of powders and metrics without enough control over material state, calibration, independence, and uncertainty.

### Discretionary analytical decisions

- Treated the supplied compiled PDFs as the authoritative source for figure numbering and wording.
- Treated the ten-powder × four-mass matrix as the primary validation design and nozzle, ablation, blend, and endurance experiments as secondary studies because this gives the cleanest confirmatory structure.
- Used exact binomial confidence bounds to assess the informativeness of `n = 10` for overshoot and a chi-square interval under normal independent errors to illustrate uncertainty in SD/CV.
- Recommended estimation with confidence intervals rather than condition-by-condition null-hypothesis tests because the task is hardware performance characterization.
- Recommended a manual spatula/hand-weighing comparator rather than requiring a commercial powder doser, since it directly measures the intended automation benefit and is broadly reproducible.
- Recommended frozen calibration profiles and independent reload/day blocks to separate parameter selection from validation and to reduce pseudoreplication.