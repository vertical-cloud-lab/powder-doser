# Mock editorial panel and independent manuscript audit

**Manuscript:** *Per-powder Bayesian calibration of an auger doser for alloy feedstock preparation, and dosing records as a probe of powder flow*  
**Target:** *Additive Manufacturing*, full-length research article  
**Audit date:** 27 November 2026

## Executive assessment

**My decision now is reject in its present full-length research-article form, with encouragement to resubmit a narrower, substantially validated paper.** This is not a decision based on the orange text or illustrative synthetic panels. I treat those as the authors' intended scope and ask whether the specified work would support it.

The strongest existing result is real: the eight-dose `bo-005` block is much faster than the four hand-tuned doses, and its absolute errors are smaller. I reproduce time medians of **78.40 versus 245.15 s**, a **3.127-fold** ratio, and an exact two-sided Mann–Whitney **p = 0.004040**. However, that establishes a comparison between these settings in these sessions, not that Bayesian optimization (BO) is superior to simpler calibration strategies. Afterflow constant, day, powder state, and validation-block order are not all controlled. The proposed response-as-feedstock-measurement contribution is promising but has not yet crossed the validation threshold for an AM research article.

**The most consequential audit findings are:**

1. **Figure 7b contradicts Section 3.6:** the actual panel says moisture/error **ρ = 0.35, n = 12**; the text says **ρ = 0.87, n = 9** and points to that panel. SI Table S9 contains 12 moisture entries, but the SI does not supply the per-powder errors or the nine-powder inclusion rule. Neither version can be independently reconstructed from the supplied SI.
2. **“No effect” of hand-over margin is not established.** The 35 and 0 mg margins were tested on different days with drifting powder. The seven jointly successful corners give the stated p = 0.578125, but that is a selected subset, not an equivalence test or an unconfounded margin experiment.
3. **The 55 mg lower useful-dose threshold is an extrapolation, not a measured boundary.** The 50 mg trial missed by 2.56 mg, or 5.12%; there is no 55 mg trial, and the six range doses include a post-dose firmware fault.
4. **Two “ok” entries are outside their displayed final stopping bands:** Table S2 index 20, −9.5 mg at δ = 9 mg; Table S4 index 5, −3.1 mg at δ = 3 mg. The former cannot be dismissed as one-decimal-place rounding. Explain controller-stop versus settled-score classification.
5. **The two papers share substantive results, not just hardware:** the AlSi10Mg 8 g/7.993 g dose, Al 4047 obstruction/recovery observations, and the fixed-setting records used in Fig. 7. The companion also reports **about 25 mg/s** after manual clearing where the present paper/Table S5 report **30.7/~31 mg/s** for the apparently same 1.10 g dose. Different windows might explain this, but neither paper makes that reconciliation.
6. **OUTLINE §4 is a useful development plan, not yet a sufficient confirmatory design.** One session per powder, one unsieved opening fingerprint, and a surrogate replay do not by themselves validate batch discrimination, generalization across days, or multi-task sample-efficiency gains. E8 is salt-only; it cannot establish a cross-powder correlation between inferred cohesion and shear-cell results.

**My recommended smallest defensible AM research package** is a narrowed version of E0–E3 + E5–E6, with replicated split-batch/fill/day checks and one quantitative AM-facing outcome. I would omit E4, E7–E8 and the broad property-inference claim unless they become the main paper. If the paper is explicitly restricted to 0.5 g calibration, dropping the two eight-dose range blocks from each of E1–E3 reduces the planned executor count from **222 to 174**, without weakening that restricted calibration claim. This is a conservative operational package, not a statistically proven minimum. A small, controlled subset of E9 is one way to provide the AM-facing outcome; charge-composition tolerance in an actual alloy-preparation workflow is another. I would not require a printed part merely for its own sake.

The current contribution is closer to the journal's **new Methods-paper category**, but changing the article type is not a waiver of validation or reproducibility. *Powder Technology* is the strongest alternative for a feeder-response/metrology paper; *Digital Discovery* is plausible for a genuinely benchmarked autonomous-calibration paper. I would avoid turning this into a second hardware-description article while the companion is in preparation.

## Audit basis and limits

I read both PDFs, the companion LaTeX source, OUTLINE.md, SUBMISSION.md, and all three scouting notes. I independently reconstructed **all 60 Table S2 rows and all 43 Table S4 rows** from the SI, inspected the actual extracted figures, and reran the calculations below in Python/SciPy. I checked the live journal guide and Elsevier publishing-ethics page [W1–W2]; full BibTeX and source snapshots are in the audit bundle. The figure supplied with this report shows the validation times and all 16 paired corners; the exact values are also tabulated below and in CSV files.

I did **not** have the underlying balance telemetry, the source analysis scripts, powder-response tables behind Fig. 7, DEM run files, or the companion's `\input` tables and figure assets. A statement that is not checkable from the supplied files is labelled **not independently auditable**, not automatically false. For overlap I can compare the displayed main figures with the companion's source paths/captions and text, but cannot establish image identity by comparing unavailable companion image files.

The following panel voices are **my simulated reports, inspired by the named experts' subject areas in the supplied scouting notes**. They are not reports, quotations, or opinions from those people. I use A. T. Clare as the requested handling-editor persona, not the scouting note's unverified Wicker officeholder designation. I make no independent claim about present editorial appointments.

# 1. Handling-editor report — A. T. Clare–inspired lens

### Scope, novelty and significance

I see a legitimate **upstream AM** problem: preparing compositionally accurate alloy-feedstock charges and detecting a troublesome atomized batch. I do not yet see a demonstrated powder-bed-fusion or directed-energy-deposition process advance. Almost all optimization evidence is on table salt at 0.5 g; the metal evidence is one AlSi10Mg dose and an operational blockage case (Sections 3.1–3.3, Figs. 2–4, Tables S2–S5). This distinction matters more than adding AM terminology to the introduction.

The work's defensible novelty is **integration and experimental validation**, not a new BO algorithm, not a new gravimetric feeder, and not the first inference of contact parameters from screw-dosing records. Section 1 correctly acknowledges the closest auger/DEM calibration precedent [manuscript refs. 58–60; independently verified bibliographic metadata for El Kassem et al., DOI 10.14356/kona.2021010, and Imole et al., DOI 10.1016/j.powtec.2015.07.051]. The companion already establishes the open instrument and multi-powder response. The present paper must add a persuasive calibration decision or validated feedstock-quality decision that a reader could not obtain from that companion.

The title's dual proposition is reasonable, but the present narrative tries to carry five papers' worth of promises: single-task calibration, state drift, task transfer, inverse DEM, and flow-property/spreading prediction. The 42-dose case and transparent negative result in campaign 2 are useful; neither is a demonstration of general property inference or an independently validated benefit of multi-task BO.

### Article type and decision

**Now: reject/rebuild for the requested full research type.** If this had already entered review, I would require major revision approaching a new submission. I would not accept “the placeholders will be replaced” as the scientific response: the issue is whether the new design answers the confounding and validation questions.

**Methods route:** the live guide explicitly welcomes significant, transferable calibration/validation procedures, uncertainty evaluation, repeatability, reproducibility, common pitfalls, and tutorial-style implementation [W1, “Methods Papers”]. The current calibration/drift story fits that remit better than it establishes a new physical finding. A successful Methods submission should teach the complete workflow: hardware-state qualification, the actual controller and BO configuration, reference measurements, failure handling, stopping rules, decision-making and independent validation on an AM powder. It should be much less a research prospectus. Salt alone plus an anecdotal metal transfer would still leave breadth to the AM community weak.

**After the proposed work:** I would send a focused full article for review if E0–E3 and E5–E6 produce repeatable, uncertainty-qualified decisions on actual feedstocks, with matched baselines and a meaningful within-alloy/AM use case. I would consider acceptance only after those results and their controls are examined. Completing every row E0–E9 is neither necessary nor sufficient: no amount of salt-only DEM makes a four-powder correlation valid, and an emulator replay cannot replace measured optimizer comparisons. If only the calibration method becomes robust, Methods is the more honest category. If the physical finding is feeder-specific, *Powder Technology* is a better scope match. If the principal advance is demonstrable autonomous learning efficiency, consider *Digital Discovery*.

I would request both companion drafts and a data/result overlap statement at submission. The guide prohibits part papers but allows a self-contained paper; “stand-alone” is a scientific condition, not an assertion satisfied merely by repeating the doser construction (Section 2.1). Citation and disclosure must make the reused alloy-charge and fixed-setting records unmistakable.

# 2. Reviewer 1 — Laura Cordova–inspired AM feedstock/flowability report

**Recommendation: major revision; not acceptable as a full AM research article yet.**

### Major comments

**R1.1 — Establish the AM decision, not a generic ordering of unrelated powders.** Sections 2.2, 3.6 and 4; Fig. 7; Table S9. Twelve class-level estimates spanning biopolymers, salts and metals cannot validate a quality-control test for batches of one AM alloy. Seven angles of repose are engineering estimates, and none of the properties was measured on the dosed lots. E5–E6 are essential if the property-probe claim is retained, but a correlation across three or four new materials will also be too fragile for general prediction. Use a paired split of an Al 4047 batch before/after a defined sieve treatment, document the retained fraction and PSD, and ask whether the dosing measurement reliably resolves that treatment.

**R1.2 — Give the Al 4047 diagnosis a causal control.** Section 3.3 and Fig. 4a–b; Table S5. The recovery after manual clearing is compelling operational evidence of an obstruction; it does not uniquely identify particle-size oversize, an agglomerate, caking, a changing fill, or a geometry difference. E3's single opening fingerprint on unsieved powder is not an adequately replicated sieved/unsieved comparison. Split a well-mixed source batch into paired aliquots, preserve geometry and fill, vary sieve treatment deliberately, and inspect/measure retained particles. Include the sieve cut and its relevance both to the 3 mm doser outlet and to the intended AM powder size window. Report this as evidence of obstruction unless that control confirms the cause.

**R1.3 — Match the independent flow test to the intended application.** Sections 2.10 and 3.6; Fig. 1c and planned Fig. 7c. Hall/Carney time, angle of repose, shear-cell flow function and thin-layer spreading measure different stress and motion regimes. A funnel no-flow outcome is a valid result, not proof that the dosing assay is more physically informative. For a claim of feedstock spreading/packing prediction, carry out E9 with fixed blade gap, speed, substrate, layer length, atmosphere, powder history, independent aliquots and repeated layers, then quantify coverage and areal mass. Otherwise restrict the claim to handling/dosing and quantify an alloy-charge preparation benefit. A full printed build is not obligatory.

**R1.4 — Resolve the property result that the reader actually sees.** Section 3.6 versus Fig. 7b and Table S9. The plot says ρ = 0.35 for 12 powders, not 0.87 for nine. Specify whether the response is signed mean error, mean absolute error or absolute mean error, show all powders, and explain exclusions before attributing an effect to moisture. Literature equilibrium moisture is not the measured water content during dosing. The sentence that particle size “decides” flow within silicon compares two grades with potentially different morphology/history and cannot establish size as the sole cause.

**R1.5 — Do not export salt DEM parameters to metal spreading without validation.** Sections 2.9, 3.5 and 4; Fig. 6a. The exact agreement at one condition coexists with ~18–35% residuals elsewhere, uncertain 30→60 rpm scaling, and extreme outlet-gap sensitivity. E8 on salt is a proof of concept at most. If contact inference remains, measured geometry, PSD, packing replicates, stiffness/discrepancy sensitivity and out-of-condition predictions are prerequisites. Coarse-graining that preserves a cohesive/gravitational ratio need not preserve a narrow outlet's particle-to-gap ratio or bridging. Shear-cell `ffc` is not a direct measurement of a unique DEM cohesion parameter.

### Minor comments

**R1.6 —** Table 1/Section 2.2 should give supplier/product, atomization route, size fraction, storage/conditioning and lot identifiers where recoverable; mark old unknowns explicitly rather than assigning new-lot measurements to old data.

**R1.7 —** Section 2.7/Fig. 7a should name the powder excluded from the correlation cohort drawn from the 13-powder battery. Comparing Table S9 with the companion roster identifies **fumed silica** as absent. Explain why, and distinguish no measurable delivery from a precisely measured small positive mean.

**R1.8 —** Fig. 1a's solid-border “measured (13 powders)” feed-factor box includes “before and after humid air.” The supplied hardware battery does not establish a controlled humid-air before/after experiment. Separate the measured tilt response from the proposed humidity protocol. This is a status/claim error in a non-placeholder measurement box, not an objection to planned figures.

**R1.9 —** Section 3.6's “not redundant” interpretation of two descriptors at ρ = −0.66 needs incremental predictive value with uncertainty, not just a correlation less than one. The volumetric index also inherits uncertainty from literature bulk density and the chosen AlSi10Mg normalization.

# 3. Reviewer 2 — Keith A. Brown–inspired BO/autonomous-experimentation report

**Recommendation: major revision, with the central algorithmic claim narrowed unless a fair benchmark is added.**

### Major comments

**R2.1 — Demonstrate what the optimizer adds over a good design and simple recommendation.** Sections 2.4, 3.1 and 4; Fig. 2a; Tables S2, S6–S8. All three observed Pareto points inside the stated reference box are pre-BO (`corner-05`, `corner-09`, `recenter-02`); the 14 suggestions did not grow observed hypervolume. Validation shows `bo-005` is a good setting, not that SAASBO is necessary or best. Compare equally budgeted Sobol/random, the screening-derived rule and a linear-model recommendation; report optimization overhead and human interventions. The paper already admits linear models predict as well or better. I regard that candour as a strength, but the conclusion must honor it.

**R2.2 — Use a fair objective and a fixed acceptance definition.** Sections 2.3–2.5; Table 2; Fig. 2a and Table S1. The optimized δ is also used to define “ok,” so success is not a common tolerance across candidates. A fast overdose is unusable even if it has a short measured time. The current symmetric |error|, reference-point thresholds and failure penalties are not the same as a one-sided overshoot-risk constraint. Separate controller termination, engineering feasibility and statistical failure; predefine the externally required tolerance, report time conditional on acceptable delivery alongside the failure rate, and implement the planned one-sided objective with sensitivity analyses rather than quietly changing the historical objective.

**R2.3 — Treat nonstationarity as part of the design.** Sections 2.4–2.5, 3.1–3.2; Figs. 2b and 3. The baseline is partly at a different afterflow constant and on a different date from validation; the BO block precedes the corner block. Campaign 2 changes both margin and date/powder state. Interleave/randomize matched comparisons after fixing balance lag, record fill/T/RH/elapsed time and use opening/closing references. E1–E3 are still one session per task; task identity and day remain confounded for learning task correlations. Add a repeated anchor powder/setting across sessions or a small crossed repeat-session design.

**R2.4 — A held-out-powder emulator is a benchmark of emulators, not a prospective laboratory win.** Section 2.8; Fig. 5 design; OUTLINE §4.B3/E4. A surrogate trained on all doses of the supposedly held-out task contains information about that task's full response surface. It may be a simulation testbed if explicitly quarantined as such, but its uncertainty, misspecification and extrapolation must be audited independently of the model being ranked. Ten random seeds do not create ten independent real campaigns. Use paired seeds, equal initial observations, the same objective/reference, and a prespecified attainable target; do not use test-task outcomes to choose kernels, normalization, task similarity or acquisition settings. E4's one multi-task trajectory with carry-over baseline does not by itself compare online dose counts against single-task BO. At minimum distinguish simulated efficiency, prospective recommendation quality and measured sample efficiency.

**R2.5 — The probability/range objective is much more demanding than the plan.** Sections 2.8 and 3.4; Table S3. Eight validation doses give only a 0.688 one-sided lower success bound, conditional on independent stable trials. Eight at each of two range endpoints cannot establish the minimum target achieving 95% reliability. Delete that threshold claim or design a target-mass/reliability study with substantially more validation, a defined interpolation model and uncertainty. The good 59-success calculation must not be used as proof that all future powder states are covered.

**R2.6 — Predictive coverage is not yet evidence that uncertainty caused a better decision.** Section 3.1; Tables S6–S8 and Fig. S1. Coverage of 40/42 for time and 39/42 for error, using broad intervals, is imprecisely estimated; the constant baseline's coverage is 100%/93%. Calibration, sharpness, scoring rules and dependence matter. Raw-time SAAS standardized residuals fail the reported Shapiro test (p = 0.030); Gaussian absolute-error predictions can go negative. Compare log-time and appropriate error/failure models using nested or session-held-out checks, not simply the best transform selected on the same leave-one-out results. LOO on adaptively selected points is not a generalization estimate for a new powder/day.

### Minor comments

**R2.7 —** Section 2.4 distinguishes 14 suggestions, two Sobol and 12 model-selected. Use that distinction consistently in claims about “the optimizer”; provide the exact Ax/BoTorch campaign environment, priors, noise model, rounding, acquisition and recommendation-choice rules. Ax 0.4.3 and diagnostic BoTorch 0.18 are different analysis environments, not evidence of exact model identity.

**R2.8 —** Sections 2.11 and 3.6 disagree about multiplicity: one says p-values are uncorrected leads, the other reports Bonferroni adjustment. Supply the full 42-pair family and a clear primary/exploratory distinction.

**R2.9 —** Table S6 should not report p = 0.000; use a bound or more digits. Relevance weights in Table S7 are posterior summaries of an encoded, adaptively sampled response, not causal physical effects.

# 4. Reviewer 3 — Johannes G. Khinast–inspired feeding/dosing metrology report

**Recommendation: major revision; the instrument can support a valuable metrology method after qualification.**

### Major comments

**R3.1 — Qualify the measurement chain independently of controller repeatability.** Sections 2.1 and 3.1; Fig. 2c; Tables S2–S3. A 0.1 mg balance readability and 0.56 mg dose SD do not establish accuracy or uncertainty. Check calibrated weights, blank/actuation disturbance, tare drift, eccentric loading, serial latency, settling, powder loss and electrostatics; reconcile the 0.7 versus 0.16 s lag before new campaigns. A final reading from the same balance controlling the dose is not an independent accuracy validation. A subset independently reweighed after controlled settling is enough to test gross bias. E0's calibration weight is necessary but not a complete measurement-system analysis.

**R3.2 — Define a reproducible powder/feeder state and test it.** Sections 2.1–2.3 and 3.2; Fig. 3; Table 1. Unknown tube identity, uncertain exit dimensions, unknown fill and uncontrolled storage mean repeatability cannot yet be assigned to powder alone. Measure as-built outlet/core clearance, record auger ID, load mass, fill procedure and cumulative drawdown; use at least repeated fills/days and, if making an operator-independent claim, a second operator. The stated one-session-per-jar plan does not explicitly allocate this crossed repeatability work. Do not infer those controls from the phrase “drift check.”

**R3.3 — Reconcile outcome labels and all abort limits.** Sections 2.1, 2.3–2.5; Tables S2–S5. Table S2 index 20 and Table S4 index 5 are outside their displayed settled-score bands despite “ok.” Table S5 contains an 802.7 s cycle-budget metal record despite the general 600 s timeout wording. Table S3's 10 g dose has 178 taps despite a stated 120 tap-cycle allowance. These may reflect version/mode/total-versus-consecutive limits; publish those definitions by firmware and distinguish a successful controller stop from a final score inside the band. Equipment faults with recoverable mass data should not become silent successes in one section and exclusions in another.

**R3.4 — Specify the feed-rate estimator before interpreting material differences.** Sections 2.6 and 3.3; Fig. 4a–b; Table S5. A first-to-last balance gain over the bulk window is affected by startup and lag, and a six-second trailing slope is affected by pulsed flow. Short 0.5 g bulk stages and a long 8 g dose are not matched throughput tests. The caption acknowledges this but the 2.4-fold salt/metal ratio still reads like an intrinsic property. Use equal commanded turns/windows after a defined startup, verified actual speed/turn count and common fill, with uncertainty. The companion's protocol-D timing error is particularly important for the interruption fraction and DEM speed scaling.

**R3.5 — A no-flow measurement needs a limit of detection and a diagnostic rule.** Sections 2.7 and 3.6; Fig. 7. “Share of balance increments showing no flow” is not a reproducible definition without increment length, threshold, filtering, negative readings, lag correction and noise-floor handling. The hardware paper reports powder-group/bench-noise confounding and noisy nonconveying powders. Reanalyse those traces with a noise-aware threshold and sensitivity analysis before calling the interruption fraction a cohesion analogue. Empty tube, plugged outlet and genuinely cohesive powder can all produce zero increments.

**R3.6 — Preserve the negative campaign rather than retrospectively cleaning it away.** Section 3.2; Fig. 3; OUTLINE §4.A decision D6. Starvation/caking was not observed directly. Retain all original records and model-available information; mark suspected state failures with the evidence and show analyses with/without them. “Void its starved doses” should mean transparent prospective data-quality handling and retrospective sensitivity, not deleting inconvenient optimizer failures. Reliability and unattended operation are system-level properties, so equipment faults still count in total runtime and operational yield even when excluded from the response model.

### Minor comments

**R3.7 —** Section 3.1's Mann–Whitney time calculations reproduce, but interpret them as distribution/rank comparisons unless a common-shape shift model is justified. Corner-09 has a much larger dispersion than `bo-005`.

**R3.8 —** Section 3.1/Table 1 omit two pre-restart recommendation doses from the table's campaign-1 count. List them explicitly, explain the exclusion rule and show a sensitivity analysis including them. They are not independent evidence of a new campaign.

**R3.9 —** Sections 2.6/3.3 and Fig. 4 should identify the exact dose IDs behind each charge or segment. “An 8 g charge” is not the same as a single 8 g executor request: the 11.1 mg/s Al 4047 row in Table S5 has a 4.5095 g request within that charge-filling sequence.

**R3.10 —** Section 3.5/Fig. 6 should report simulator CPU model, geometry/mesh version, outlet counting plane, mass balance/leak checks, steady-state definition and independent packing replicates. These are necessary for reproducibility even if inverse DEM is removed.

# 5. Independent statistics audit

## 5.1 Recomputed validation summaries

I use Table S2 indices **0, 21, 22, 27** for the hand-tuned baseline, **44–51** for `bo-005`, and **52–59** for `corner-09`, following the manuscript's explicit block definitions. Errors below are absolute errors unless labelled signed. SI values are rounded observations, not the unrounded database values.

| Group | n | Time median, s | Time range, s | Mean time, s | Time SD, s | Median absolute error, mg | Absolute-error range, mg |
|---|---:|---:|---:|---:|---:|---:|---:|
| Hand-tuned | 4 | 245.15 | 179.8–342.8 | 253.225 | 67.407 | 4.55 | 3.6–4.8 |
| `bo-005` block | 8 | 78.40 | 60.5–114.4 | 84.650 | 20.112 | 1.85 | 0.8–2.6 |
| `corner-09` block | 8 | 201.95 | 47.1–385.0 | 215.388 | 138.515 | 2.60 | 2.0–2.8 |

The `bo-005` delivered-mass sample SD is **0.5643 mg**, agreeing with 0.56 mg. Its signed errors are all negative. The ratio of hand-tuned to `bo-005` time medians is **3.1269**. Restricting the baseline to indices 22 and 27, at the fitted afterflow constant, gives **209.20 s** and a ratio of **2.6684**, agreeing with the stated 2.7. With only two matched-constant baseline doses, it is descriptive, not a strong causal control.

To remove Monte Carlo variation I enumerated the empirical bootstrap distribution for each small sample rather than sampling 20,000 resamples. The resulting percentile 95% intervals are:

| Quantity | Exact empirical-bootstrap percentile interval |
|---|---:|
| `bo-005` median time | 68.5–109.6 s |
| `bo-005` median absolute error | 1.3–2.3 mg |
| `corner-09` median time | 99.2–355.9 s |
| `corner-09` median absolute error | 2.3–2.8 mg |
| Hand-tuned median time | 179.8–342.8 s |
| Ratio of time medians, hand-tuned/`bo-005` | 2.0738–4.3724 |

These agree with the manuscript's rounded 69–110 s, 99–356 s and 2.1–4.4. The table-derived 1.85 mg versus printed 1.8 mg is **not a demonstrated substantive error**: both one-decimal rounding conventions and unrounded source measurements can explain it. Use sufficient digits and one rounding rule.

## 5.2 Recomputed between-group tests and shifts

All time observations in each comparison are distinct, so the ordinary exact rank-sum distribution applies. Negative shifts mean the first group is faster/more accurate. Hodges–Lehmann shifts are medians of all cross-group differences, not differences of sample medians.

| Comparison | Response | U for first group | Two-sided exact p | Hodges–Lehmann shift |
|---|---|---:|---:|---:|
| `bo-005` vs hand-tuned | Time | 0 | 0.0040404 | −165.80 s |
| `bo-005` vs `corner-09` | Time | 14 | 0.0649573 | −114.50 s |
| `corner-09` vs hand-tuned | Time | 14 | 0.8080808 | −59.35 s |
| `bo-005` vs hand-tuned | Absolute error | 0 | 0.0040404 | −2.65 mg |
| `bo-005` vs `corner-09` | Absolute error | 6 | **0.0048174**, tied-rank permutation | −0.70 mg |
| `corner-09` vs hand-tuned | Absolute error | 0 | 0.0040404, tied-rank permutation | −2.00 mg |

The manuscript's principal p-values **0.004, 0.065, 0.81 and 0.005 reproduce to their stated precision**. For `bo-005`/`corner-09` absolute error there are tied observations, including cross-group ties. A naïve `mannwhitneyu(method="exact")` uses the untied null distribution and returns 0.0046620. I instead enumerate all **12,870** assignments of eight labels among 16 observations and obtain **0.0048174**, using twice the smaller inclusive permutation tail as the two-sided convention. Both round to 0.005, so this is a specification issue, not evidence that the conclusion changes. Exact inference should state how ties were handled.

Inverting the exact untied rank-sum tests gives time-shift confidence intervals:

- `bo-005` minus hand-tuned: **−261.8 to −104.0 s** (discrete confidence ~95.15%).
- `bo-005` minus `corner-09`: **−268.0 to +3.3 s** (~95.01%).

These agree with the printed −262 to −104 and −268 to +3 s. The second interval's inclusion of zero is not proof that the settings have equal performance. Conversely, **p = 0.81 does not establish that corner-09 is “no faster” than hand tuning**; the data are highly dispersed and inconclusive about that contrast. The observed difference of medians is −43.20 s, distinct from its −59.35 s Hodges–Lehmann shift.

## 5.3 Recomputed paired corners

I match the 16 `corner-00` through `corner-15` labels across Tables S2 and S4, discard only the two untared non-dispenses in S4, and keep all actual corner attempts for the all-corner summaries.

| Quantity | Recomputed result | Assessment |
|---|---|---|
| Successful corners, campaign 1 / campaign 2 | 9 / 9 | Confirmed |
| Successful in both | 7 | Confirmed |
| Time change, second minus first, jointly successful seven | Median **−11.9 s**; mean **−56.16 s** | Median agrees with −12 s |
| Exact Wilcoxon signed-rank on those seven time changes | W = 10, **p = 0.578125** | Agrees with 0.58 |
| Absolute-error change, same seven | Mean **+0.2143 mg**; median +0.4 mg | Agrees with mean 0.2 mg; state that it is absolute error |
| Overshooting corners, first / second | 6 / 5 | Confirmed |
| Overshoot discordances | 2 ceased overshooting, 1 began | Exact McNemar **p = 1.0** |
| Time rank correlation, all 16 corners | **ρ = 0.44412, p = 0.08482** | Agrees with 0.44/~0.08 |
| Absolute-error rank correlation, all 16 | **ρ = 0.46392, p = 0.07028** | Agrees with 0.47/~0.07 |
| Signed-error rank correlation, all 16 | **ρ = 0.20324, p = 0.45028** | Does not agree with 0.47 if “error” means signed error |
| Time change, all 16 | Median **0.0 s**; mean +24.65 s | Descriptive only: mixes fast overshoots and long failures |

For completeness, an exact sign-randomization signed-rank calculation on all 16 time differences, allowing the tied absolute differences, gives p = **0.87018**. This is not a superior causal margin test: mixing success/failure times changes the estimand. The seven-corner result is correctly calculated but conditional on post-treatment success at both settings. It cannot support an all-corner effect or “no effect” statement.

## 5.4 Screening arithmetic, outcomes and model checks

All **eight rows of Table S1** reproduce from the 16 corners, including:

- bulk-tap successful-time means **185.45 vs 78.80 s**; failures **2/8 vs 5/8**;
- tap-tilt successful-time means **222.55 vs 91.78 s**;
- switch-threshold absolute-error means **33.8125 vs 10.8500 mg**;
- six screening overshoots and one screening cycle-budget failure.

I also checked the design matrix. It is balanced, all main-effect columns are orthogonal, there are **no length-three defining words**, and length-four defining words are present: the claimed **resolution IV** design is supported. Nevertheless, the reported time “main effects” in S1 are **success-conditioned means with different subset sizes**. Conditioning on success breaks the simple balanced-factorial interpretation; these summaries are useful operational descriptions, not unbiased estimates of the unconditional causal effect of tapping or tilt. Main effects remain aliased with three-factor interactions, and two-factor interactions with one another.

Outcome counts reproduce exactly:

- campaign 1: **31 recorded ok, 8 overshoot, 3 cycle-budget**;
- campaign 2: **19 recorded ok, 5 overshoot, 6 cycle-budget, 5 stalled, 6 fw-error, 2 not-tared**, hence 35 non-equipment-error records;
- seven campaign-2 BO-labelled doses both recorded ok and within 3 mg; the fastest two are **71.7 and 91.9 s**, agreeing with 72–92 s.

The “ok” counts are controller labels, not uniformly verified final-band or engineering-feasibility counts. Specific discrepancies are S2 index 20 (−9.5 mg at ±9) and S4 index 5 (−3.1 mg at ±3). Further, several doses labelled ok exceed the 180 s hypervolume reference; the manuscript also calls such observations “failures.” Explicitly distinguish the reference point, controller outcome, final scored tolerance and system failure.

The three observed nondominated campaign-1 points within the 180 s/20 mg reference are **`corner-05` (65.5 s, 0.6 mg), `corner-09` (51.8 s, 0.7 mg), `recenter-02` (24.0 s, 6.8 mg)**. Thus no BO point improves that observed front, consistent with the text. The 42 recorded execution durations sum to **6,650.4 s = 110.84 min = 1.847 h**. The stated **2.3 h** is not the sum of dose times, but could be elapsed campaign wall time including suggestions/restarts. Without timestamps I cannot call that a contradiction; distinguish the denominators.

I reproduce the S6 constant leave-one-out RMSEs: **133.820 s** for time and **19.522 mg** for absolute error after the stated jam-error encoding. Other fitted-model quantities, including NUTS convergence, predictive intervals, afterflow regression t = 1.1, stage-specific tap rates, bulk-feed correlations, and DEM summaries cannot be recomputed from final per-dose t/e tables. In particular **7% bulk-feed change, its p = 0.03, and ρ = 0.90** require stage telemetry or per-dose stage summaries not supplied in the SI.

## 5.5 Range, reliability and exclusions

Table S3 gives:

| Target | Time, s | Signed error, mg | Absolute relative error |
|---|---:|---:|---:|
| 0.5 g | 114.0 | −2.28 | 0.456% |
| 1.5 g | 125.3 | −2.20 | 0.1467% |
| 0.05 g | 305.0 | −2.56 | **5.12%** |
| 0.005 g | 25.5 | −2.70 | **54.0%** |
| 10 g, firmware error after completion | 242.9 | −2.48 | **0.0248%** |
| 0.5 g | 110.5 | −0.30 | 0.060% |

The 25–305 s and 0.3–2.7 mg ranges in Section 3.1 are reasonable rounded descriptions. However:

- **“Meet ±5% only above about 55 mg” is not an experimentally determined threshold.** A heuristic using 2.7 mg/0.05 gives 54 mg; using the allowed ±3 mg stopping band gives 60 mg. Neither establishes the minimum reliably doseable mass. The measured 50 mg trial is slightly outside ±5%; the next tested distinct larger target is 0.5 g.
- Section 2.11 says equipment-error doses are excluded from comparisons. The 10 g result is nevertheless counted among “all six” range doses. Reporting its recovered mass is reasonable, but state explicitly that this is a physically completed dose with a reporting failure, and distinguish physical yield from end-to-end workflow yield.
- With 8 successes in 8 independent, identically distributed trials, the one-sided 95% Clopper–Pearson lower bound is **0.687656**, and with 0 overshoots in 8 the upper bound is **0.312344**. The stated 0.69/0.31 and **59** zero-failure trials needed for a lower bound of at least 0.95 are correct. They do not apply to uncontrolled changes in day/fill/powder state as though those were sampled adequately.
- Including the two pre-restart S2 doses (42–43) gives **10/10**, time median **78.40 s**, median absolute error **1.70 mg**, and time p = **0.001998** versus the four baseline doses. This sensitivity does not reverse the result. It also does not justify relabelling an originally defined eight-dose block after seeing the data.
- The dose accounting is **60 S2 + 43 S4 + 6 S3 + 16 S5 = 125**. Table 1's campaign-1 row describes only 42 + 8 + 8 = 58 and does not enumerate the two pre-restart doses; the table-described total is therefore 123 unless those are added.

## 5.6 Tests and claims needing repair

1. **Mann–Whitney is suitable for a conditional small-sample distribution comparison, not automatically a median test or a causal algorithm comparison.** Baseline/validation day and block order violate simple exchangeability as an experimental-design assumption. With markedly different shapes, a pure common-location-shift interpretation of the exact Hodges–Lehmann interval is questionable. Keep the interval as a shift-model summary and show the individual data.
2. **Wilcoxon/McNemar calculations do not cure the cross-day margin confound.** Failure to reject does not establish equivalence. A margin-equivalence experiment needs a practical effect bound, randomized/interleaved margins and sufficient power under controlled powder state. The absolute-difference distribution's symmetry is also hard to assess at n = 7.
3. **Bootstrap/binomial intervals assume stable, sufficiently independent sampling.** These are within-block uncertainty summaries, not across-lot, across-day, operator or tube reproducibility. Add grouped uncertainty when there are enough independent sessions; resampling individual doses cannot manufacture independent sessions.
4. **Fig. 7b must be regenerated from a single explicit analysis table.** Provide the 12-powder and nine-powder analyses, response definition, exclusions and source uncertainties. The SI lacks the dosing response vector, so I cannot adjudicate which ρ is correct.
5. **Property multiplicity/provenance need more than a rank test.** Section 2.11 says uncorrected exploratory p-values; Section 3.6 gives a 42-comparison Bonferroni result. The printed p = 0.0006 and adjusted 0.023 are not necessarily an arithmetic error, because the unrounded raw p could differ. Supply exact unrounded values, all 42 pairs, tie-aware/permutation methods and uncertainty/sensitivity to estimated properties. Rank correlation does not remove the uncertainty or possible circularity of engineering estimates and AoR-anchored/assumed Hausner ratios in S9.
6. **Non-correlation is not exclusion of a mechanism.** ρ = 0.26 for class-level median size does not show particle size is irrelevant; “moisture content, not particle size, tracked error” is a descriptive selected-dataset statement, not mechanism isolation. Likewise two silicon grades do not establish a causal size-only relation, and ρ = −0.66 is not evidence of independent added information.
7. **Coverage does not prove the GP's uncertainty is calibrated or useful relative to alternatives.** The S6 95%/93% values are rounded 40/42 and 39/42. Broad intervals can cover well; include sharpness/scoring and uncertainty on coverage. Normality tests on dependent fitted residuals are diagnostic only. Do not claim eight validation points inside very broad intervals demonstrate external calibration.
8. **Do not erase system faults or suspected starvation from efficacy accounting.** They may be excluded from a specified model fit, but should remain in denominator/runtime/reliability reporting. The 10 g reporting fault and metal no-result/manual segments require explicit treatment.

**Bottom line on numerical integrity:** the main salt-block medians, rank-test p-values, shifts, bootstrap intervals, screening arithmetic, outcome counts and binomial bounds are largely correct. The clearest displayed numerical contradiction is **Fig. 7b versus Section 3.6**. The larger problems are estimand/design ambiguity, unverified physical diagnosis, and conclusions stronger than these otherwise mostly correct calculations warrant.

# 6. Duplication and cross-paper consistency audit

## 6.1 Policy judgment and how I classified overlap

Elsevier's policy says authors should not publish manuscripts describing **essentially the same research** in more than one primary journal, and must not submit the same manuscript concurrently [W2, “Multiple, redundant or concurrent publication”]. This is not a prohibition on reusing a transparently identified dataset for a substantially different analysis, nor on describing essential shared equipment. **Citation is necessary but does not by itself make redundant scientific publication acceptable.** Conversely, overlapping authors, identical instruments or a repeated apparatus dimension are not misconduct.

Both supplied papers are drafts; main reference **[64] is explicitly a “manuscript in preparation (2026).”** I cannot conclude that duplicate publication has occurred, or determine copyright permissions from these files. My judgments below concern **submission/publication risk**. Disclose both manuscripts to both editors, supply copies, map shared dose IDs, and explain which result is primary in each. If a figure asset or substantial wording is reproduced after publication, check the applicable licence/permission separately from the scientific-overlap question.

For precision I distinguish **same record/result**, **new analysis of old records**, **shared apparatus/method**, and **shared background**. I do not count a number that appears only in the hardware paper as a duplicate in main.pdf. I also do not treat the two different controllers or two different AlSi10Mg target masses as the same experiment.

The source below is `hardware_paper_main.tex`; line numbers refer to the supplied file. Its included external tables and graphics are not supplied. This is an inventory of all identifiable substantive overlaps in the available main text, tables and displayed panels, not a claim to have compared inaccessible companion image pixels or missing table cells.

## 6.2 Item-by-item overlap inventory

| ID | Location in main.pdf / repeated item | Companion source | Attribution in main.pdf | Judgment |
|---|---|---|---|---|
| D01 | Title/abstract, Sections 1, 2.1, 4–5: open-source, 3D-printed, low-cost auger doser for alloy-feedstock preparation | Title/abstract; “The doser”; “Cost and accessibility”; Conclusions, lines 181–183, 395, 427 | Explicit hardware provenance [64] in Section 1 and 2.1, not in abstract/title | Legitimate context, but not a new hardware contribution here. Do not sell instrument openness/construction as this paper's novelty. |
| D02 | Section 2.1: one-piece auger is both reservoir and screw; tilt, rotation and solenoid tapping deliver powder into a balance cup | “The doser,” line 181; “How a dose runs,” line 263 | Section opens with [64,65] | Necessary shared apparatus description; low risk if concise. |
| D03 | Section 2.1: PLA, Bambu Lab H2D, 0.2 mm layers | “Fabrication and build files,” line 401 | Covered by Section 2.1 provenance | Same fabrication description; acceptable methods reuse, not a separate result. |
| D04 | Section 2.1: 21 mm bore, 250 mm tube, 0.5 mm flight, 10.4 mm pitch, ~3 mm exit; flight near outlet | Lines 181, 401 | Covered by [64,65] | Shared specifications; acceptable. Flight extent differs: 84 versus 83 mm (see discrepancies). |
| D05 | Section 2.1: NEMA-11, 20:44 stepper gears, two servos and 2:1 tilt gears | Lines 181, 401, 405 | Covered by [64,65] | Shared design, acceptable. Model-number details not present in companion are not numerical duplication. |
| D06 | Section 2.1: 60 ms tapping, A&D HR-100A, 0.1 mg readability, Pico W/MicroPython, Pololu Tic T500 and RS-232 balance | Protocol E table, lines 299–303; lines 401, 405 | Covered by [64,65] | Shared instrumentation; acceptable. 102 g capacity, Pi Zero and maximum 109 rpm are not all repeated in the available companion text. |
| D07 | Sections 2.1/2.7: tube angles and speeds/revolutions mean actual auger quantities, not servo/gear coordinates | Protocol-table caption; electronics/firmware, line 405 | Hardware reference in methods | Same coordinate convention, essential; ensure raw servo angles converted once. |
| D08 | Sections 2.1, 2.7 and discussion: three-stage bulk/fine(or trickle)/tap strategy and final re-feed/nudge | “How a dose runs,” line 263; G/H methods, line 413 | Earlier frozen controller explicitly attributed in Section 2.7; newer controller described separately | Shared architecture, **not identical controller performance data**. Different settings/versions must be mapped, not conflated. |
| D09 | Section 2.6 and AM-workflow discussion: direct delivery into an ultrasonic-atomizer crucible/charge | Hardware Figs. `fgr:v2dosing` (8 g request/reply) and `fgr:v2use`; “Dosing for the alloy workflow,” lines 263–279, 384 | Section 2.6 says charge completion/final masses are in [64]; Fig. 4 caption also points there | Shared use demonstration. Acceptable supporting context only; both papers should not count it as independent application validation. |
| D10 | Abstract; Section 3.3; conclusion: **8 g requested, 7.993 g delivered** for AlSi10Mg | “Dosing for the alloy workflow,” line 384; Conclusions, line 427; request/reply Fig. `fgr:v2dosing` caption line 268 | General boundary stated in Sections 1/2.6, but Section 3.3's result and abstract do not explicitly identify this as the same previously reported charge | Exact same experimental result. This is the clearest redundancy risk because it is a headline in both. Label it “the same charge reported in [64], reanalysed here…” or leave outcome accuracy primary in only one paper. |
| D11 | Section 3.3/abstract/conclusion: **−7.2 mg, −0.09%, within 0.1%**, **315 s**, **144 mg/s, 86 mg/rev** for that charge | Underlying 8 g/7.993 g record above | Same indirect attribution as D10; S5 provides time/rate | Error/percentage are derived restatements of shared mass data; time and feed-rate extraction are additional analyses, not an independent dose. No matching 315/144/86 numbers appear in the supplied hardware text. Properly labelled secondary analysis can add value. |
| D12 | Section 2.6: **8 g, 3.04 g and 6.57 g** Al 4047 charge targets on **30 Sep, 19–20 Oct**; Table 1: **10 executor doses + 5 manual sessions** | “Dosing for the alloy workflow,” line 384: three charge targets **8.0000, 3.0407, 6.5674 g**, ten closed-loop doses; charge sequence SI referred to there | Section 2.6 explicitly assigns charges/final masses to [64] | Shared record inventory, transparently contextual. The five manual sessions and detailed dated bulk records are not numerically enumerated in the supplied companion main text. |
| D13 | Section 2.6/Fig. 4: Al 4047 nominal bulk **40°, 100 rpm, 2 Hz** and salt-fitted afterflow | Atomizer-dose methods, line 417, same nominal settings and **0.83 s** afterflow | Charge source cited in Section 2.6/Fig. 4 | Shared operating conditions. Main campaign-fit **0.834 s** and hardware **0.83 s** are compatible rounding. Hardware's slowdown/recovery logic qualifies “fixed settings”; see discrepancies. |
| D14 | Abstract; Section 3.3; Sections 4–5/Fig. 4 story: Al 4047 unlike AlSi10Mg obstructs the **3 mm outlet**, associated with coarse particles/agglomerates | Hardware abstract, line 384 and Conclusions line 427 | Charge source [64] globally/Section 2.6 and Fig. 4; not locally labelled as a repeated diagnosis in Section 3.3 | Same application observation and much of same scientific claim. New rate-versus-time analysis is useful, but the blockage/quality-control story must not be presented as an independent new demonstration in each. |
| D15 | Section 3.3: steeper **60°/75°**, faster rotation/tapping did not clear obstruction | Line 384 | Same attribution as D14 | Same observation. Keep as attributed background to rate analysis, or consolidate into one primary account. |
| D16 | Section 3.3: **~13 reverse turns at 0°**, followed by **60–80 mg/rev** in either direction | Line 384 | Same attribution as D14 | Exact repeated quantitative recovery result. Cite locally as shared; moderate redundancy risk if repeatedly used to establish novelty. |
| D17 | Section 3.3: manual removal of large particles restored flow; next dose ~**31 mg/s** and completed | Line 384: manual clearing, **1.10 g** at **about 25 mg/s** without stalling | Source of charges is cited, rate appears as current analysis | Same recovery event, with a numerical estimator disagreement. S5 defines the rate as first-to-last bulk-stage gain divided by duration; the companion does not specify that same estimator. Reconcile explicitly. |
| D18 | Section 4: sieve laboratory atomized batches; reverse clearing/local obstruction points to a feedstock problem | “Two lessons carry over…” in line 384; limits/conclusions | Hardware acknowledged generally, no local reanalysis label in discussion | Same operational conclusion, not a distinct discovery. Do not count this twice in the papers' significance claims. |
| D19 | Section 1/Section 2.7/Fig. 1a: fixed-setting response of **13 powders** used as a powder fingerprint | “Open-loop delivery of 13 powders,” lines 282–324; Conclusions/future, lines 427, 432 | Explicitly [64], including Fig. 1a caption | Legitimate summary of companion results, not a new 13-powder study. Controlled humidity response is not established there. |
| D20 | Section 2.7: protocol **C**, **six single revolutions at 30 rpm**, **0/22.5/45°**, settled reading each revolution | Hardware protocol table (`tbl:protocols`), line 298; `fgr:v2openloop` | Explicit [64] at start of Section 2.7 | Same measurement protocol and underlying records. New property association can be publishable secondary analysis. |
| D21 | Section 2.7: protocol **D**, **15/45/90 rpm at 22.5°**, especially 15 rpm trace; Section 3.6 interruption fractions **0.13, 0.26, 0.81, 0.96** | Protocol table line 299; continuous traces in `fgr:v2openloop` and lines 320, 408 | Explicit [64] for records; fraction is introduced as a new descriptor | Same traces, **new statistic**. The listed interruption fractions/correlations do not appear in companion main text. Must inherit timing/noise caveats and identify analysis windows. |
| D22 | Section 2.7: protocol **G**, **three 1 g doses**, same hand-tuned salt settings for all powders; Fig. 7b and text reuse the resulting errors | Protocol table line 302; frozen G/H methods line 413; `fgr:v2closedloop` and included dose tables | Explicit [64] in Section 2.7 and Fig. 7 caption | Same response data, new moisture-association analysis. Acceptable if stated as reuse and not represented as 12 new validation sets. |
| D23 | Section 3.6/Fig. 7a: **45°** delivery versus literature angle; **ρ = −0.84**; selected groups **244–339 / 9–37 mg/rev**; also **22.5° ρ = −0.77** | Underlying protocol-C records used by hardware `fgr:v2openloop`, which displays **22.5°**, **10–231 mg/rev** | Explicit [64] in Section 3.6/Fig. 7 | Reanalysis, not a duplicated published correlation or same plotted panel. Different tilt explains different magnitude ranges; do not call those ranges a contradiction. |
| D24 | Section 3.6: coarse/fine silicon shows strong within-material flow contrast; Fig. 7a fine Si mean near zero | Hardware line 324: coarse **~75–150 µm**, fine **<44 µm**, fine single **7 mg** pulse in six turns at 45°, coarse **211 mg/rev** at 22.5° | Companion cited at paragraph start and named in sentence; Fig. 7 source explicit | Shared qualitative contrast; exact 7/211 numbers are not repeated in main.pdf. New conclusion should not claim a causal size-only test. |
| D25 | Section 3.5/Fig. 6a: **0° and 45°** experimental delivery and **22.5°, 90 rpm** comparator, plus 30→60 rpm scaling | Hardware protocols C/D; uncertain speed exponent discussed line 322 and timing correction line 408 | Section 3.5 explicitly cites [64] for scaled data; Fig. 6a caption names companion's exponent but has no bracketed citation | Reused experimental comparators inside a new DEM plot. Make panel-level provenance explicit, including which points are old. The centre-point **105 ± 11 mg/rev** is from the new salt campaign, not the hardware battery. |
| D26 | Section 3.5/Discussion: speed dependence/scaling is uncertain | Hardware line 322: median exponent **0.78**, one pass per speed, timing error **15–54%** extra turn | [64] for scaling; qualitative uncertainty admitted | Same calibration limitation. Main does **not** re-report 0.78 as a new measured result, but still uses the exponent in Fig. 6a; the outline's “no longer used as a result” should not hide this dependency. |
| D27 | Section 4: salt clung to the auger in a dry glove box; electrostatic charging suspected in CMC | Hardware glove-box trial line 386 (salt sticking); noise/static limitations in hardware | Main's sentence cites **[80]**, a general static-charging source, rather than identifying the shared glove-box observation as from [64] | The salt anecdote is reused project evidence without a local primary-observation attribution. Add [64] and distinguish it from new calibration records made in air. CMC mechanism remains a suspicion, not a second verified measurement. |
| D28 | Sections 3.2/4: response depends on fill, lip state, compaction; unattended dosing still needs fills/recovery; balance noise limits small-dose performance | Hardware “Limits of the current design,” line 391, plus methods line 408 | Hardware provenance global, no explicit repeated-result label in each discussion paragraph | Shared limitations/engineering reasoning. New campaign-2 drift is distinct evidence and can substantively extend it. Do not imply that old noise/fill limitations were controlled in the correlation data. |
| D29 | Sections 1/4: weighing/blending limits autonomous alloy discovery; commercial tools are costly, powders differ, particle cohesion affects flow; accessible open hardware fills a laboratory gap | Hardware Introduction, abstract, cost and future-work sections | Literature citations/hardware reference, variable by sentence | Shared background, not duplicate experimental findings. Write independently, cite primary literature, and keep it short; not an ethics objection on its own. |
| D30 | Sections 1/2.8/4: automatic per-powder BO and a powder-property-linked settings database | Hardware future-work paragraph, line 432 | Companion boundary explicit in main Section 1 | Shared research direction, not duplicated accomplished BO results: the hardware describes these as underway/future. Completing the calibration paper is a legitimate follow-on if it adds sufficient independent evidence. |

## 6.3 Figure/table-by-figure/table disposition

| Main item | Audit disposition |
|---|---|
| Graphical abstract, left | Summary of new salt validation data; no corresponding hardware figure/result found. |
| Graphical abstract, middle | Reuses the same AlSi10Mg/Al 4047 charge-record family as D09–D18, now as derived feed rates. No local source marker; add same-record disclosure in caption or main linkage. |
| Graphical abstract, right | New AoR correlation from old protocol-C records, D20/D23. A summary of reanalysis, not an independent experiment. |
| Fig. 1a–c | Conceptual scheme with apparatus renders/proposed tests; its measured 13-powder component is hardware-derived. No exact companion figure match identifiable from supplied source. Render-asset identity cannot be checked. See humidity-status problem R1.8. |
| Fig. 2a–d | New 0.5 g salt calibration, validation, stage traces and settings comparisons. Hardware's dosing figure uses a **12 August 1 g salt** trace and September camera stills, not this calibration plot. No identifiable same-data panel. |
| Fig. 3a–c | New campaign-2 margin/drift records. No matching hardware result. |
| Fig. 4a–b | New rate summaries/traces from shared alloy charge records (D09–D18), plus new salt comparators. Not a direct copy of hardware `fgr:v2dosing` request/reply or `fgr:v2use` photographs, but substantial underlying data overlap. |
| Fig. 4c | New six-dose salt range records, not hardware 50/200 mg or stepped-tilt records. |
| Fig. 5 | Planned multi-task scope; no existing-data duplication finding. |
| Fig. 6a | New DEM output against a **mixture of old hardware protocol C/D observations and new centre-point salt observations**. New figure does not imply every experimental point is new. |
| Fig. 6b–c | Planned inverse-model scope; no existing-data duplication finding. |
| Fig. 7a–b | New analysis/plots of old protocol C/G response records. The caption explicitly attributes records to [64]. Moisture panel has the separate text/figure numerical inconsistency. |
| Fig. 7c | Planned independent-property validation; no existing-data duplication finding. |
| Table 1 | New inventory, overlapping shared alloy charges and fixed-setting cohort; not a copied hardware table. Missing two pre-restart salt doses in count description. |
| Table 2 | New search space, hand-tuned newer controller and recommended settings. **Not** the hardware G/H fixed-controller settings: 30/15/10° baseline here versus hardware's 45/22.5/0° procedure. |

I find **no demonstrable exact copied data figure or whole table** in the supplied source comparison. That conclusion does **not** mean there is no duplication risk: D10 and D14–D18 are the same experiments and conclusions appearing in both narratives. Conversely, the hardware's 13-powder 10–231 mg/rev range, 24/39 within ±5% at 1 g, small-dose counts, **20 repeated 2 g AlSi10Mg** stepped-tilt doses, 11 within ±1 mg, 116-trial study, cost/AI-design-history figures and tables are **not** new results repeated in main.pdf. I do not count them as duplicates merely because the doser is the same.

## 6.4 Statements about the same system/data that differ

1. **Flight length:** main Section 2.1 says **84 mm/8 turns**; hardware fabrication says **83 mm**. Eight × 10.4 mm = 83.2 mm, so nominal rounding could explain it. Use one drawing/version and distinguish CAD from measured geometry. It is not evidence of falsification.
2. **Cleared Al 4047 feed rate:** main Section 3.3/Table S5 give **30.7/~31 mg/s** for the ~1.10 g successful bulk dose; hardware line 384 says **about 25 mg/s**. The apparently same event needs identical window/lag/startup definitions or an explicit statement that two estimators differ. This is not ordinary rounding.
3. **“Fixed” metal bulk conditions:** main Section 2.6 and Fig. 4 foreground **40°, 100 rpm, 2 Hz** as unchanged settings. Hardware atomizer-dose methods line 417 additionally describe **linear slowdown in the last 100 mg and speed recovery after 3 s without flow**. A nominal bulk setting is not constant instantaneous actuation; include the same mode/ramp definition and exclude/match the endgame when claiming material feed-rate ratios.
4. **Strength of the particle-size diagnosis:** hardware states the powder **contained coarse agglomerates that lodged in the outlet**; main says the evidence **points to oversized particles or agglomerates**, with sieve/micrograph confirmation still needed. Adopt the more cautious common interpretation until direct characterization exists. Abstract/conclusion wording in main is stronger than its own detailed caveat.
5. **Controller procedures and stopping limits:** hardware G/H use bulk 45°/55 rpm, stepped fine motion at 22.5°, tap at 0°, ±5 mg, 200-cycle/900 s limits; main uses the newer continuous PI/Kalman trickle and optimized tilts/band, 120 cycles/20 nudges/600 s wording. This is principally a **version/dataset difference**, not an internal contradiction; state it explicitly because Fig. 7b uses old G errors while Fig. 2 uses the new controller. Do not call the hardware G/H baseline the same hand-tuned setting as Table 2.
6. **Cohort:** hardware tests 13 powders; main correlations use 12, omitting **fumed silica** from S9. The 13/12 numbers are compatible subsets, not an error, but the omission and screening/no-flow rule should be stated. The hardware itself labels fine silicon/brown rice flour as no reliably measurable flow, whereas Fig. 7a plots their unresolved positive means; main acknowledges this in its caption. Sensitivity to censored/no-flow ranks remains necessary.
7. **Existing measurements versus planned work:** the hardware battery did not control humidity/fill and explicitly warns of noise confounded with powder group. Fig. 1a's solid measured box adds “before and after humid air.” That extension is not established by the cited battery. Section 3.6's interpretation also needs the old noise caveats.
8. **Declared paper boundary versus actual text:** OUTLINE says hardware uses “about 8 g” while this paper owns **7.993 g/−0.09%** accuracy. The supplied hardware source actually prints **7.993 g for 8 g** in both its workflow section and conclusion. The boundary plan is therefore not the implemented boundary. Similarly, the present discussion and hardware both use blockage/reversal/sieving as substantive lessons, not merely separate rate and mass reporting.
9. **Companion bibliographic title:** main [64] names *An open-source, 3D-printed auger powder doser designed with generative artificial intelligence*; the supplied source is titled *An open-source powder doser for autonomous alloy discovery, designed by engineers and modelled by AI agents*. This is a reference/version mismatch rather than a data discrepancy. Update the citation, version and public identifier when available.
10. **Completeness of logs:** main Section 2.4 says **every prompt and response is public**; hardware AI-tool methods line 423 say **April–early July action logs expired after 90 days**, with later logs archived. If “every” in main refers only to these September/October calibration campaigns, say so. If it is project-wide, it conflicts with the companion. Do not substitute a universal provenance claim for a scoped archive inventory.

**Editorial remedy:** keep construction and its frozen 13-powder performance in the companion; let this paper own a new controlled calibration/batch-discrimination study. Reanalyse old records openly, give shared IDs and cite the same-event provenance locally. Do not try to solve substantive overlap by removing a citation, changing units, or redrawing the same result.

# 7. Would OUTLINE §4 make the paper acceptable? What is actually necessary?

## 7.1 Experiment-by-experiment verdict

| Plan | What the stated plan really buys | My requirement/decision |
|---|---|---|
| **E0** | Measured hardware state, drawdown/working fill, weight check and T/RH logging; ½ day | **Essential for either article type.** Also verify dynamic weighing and record geometry uncertainty, not just nominal bore. |
| **E1** | Salt session: 22 screen + 20 BO + 8 validation + 8 hand-tuned + 8 small-target + 8 large-target = **74 doses** | **Essential matched calibration study**, but randomize/interleave baseline/validation under the same corrected lag/afterflow configuration. Make opening/closing state references explicit; separate a frozen `bo-005` transfer check from a newly optimized recommendation. |
| **E2** | Same **74 doses** on AlSi10Mg, salt settings as the eight-dose baseline | **Essential AM-powder calibration/transfer evidence** for this full research story. A carried-over baseline tests the value of per-powder calibration relative to transfer, not superiority to a competent manually tuned metal baseline. Label that estimand honestly. |
| **E3** | Same **74 doses** on sieved Al 4047; one unsieved opening fingerprint (~20 min) | **Essential difficult-feedstock case, but insufficient batch-discrimination control as specified.** Add replicated paired aliquots and fill/day checks on both treatments. Characterize retained oversize; control geometry, fill and treatment order. |
| **E4** | 12 multi-task BO + 8 validation + 8 baseline = **28 specified executor doses**, plus fingerprints, rounded to ~30 | **Optional unless multi-task is a principal result.** One prospective task demonstrates a recommendation, not a general or causal sample-efficiency gain against unrun optimizers. Additional comparator design is needed for that claim. |
| **E5** | Same-lot PSD, density, AoR and loss on drying | **Essential for any validated property/batch claim.** Define actual lot roster and replicate method. A few material-class points do not validate a correlation model. SEM number-based PSD, sieve mass fractions and laser volume PSD are not interchangeable without stating weighting/range. Loss on drying is not necessarily selective for water; report its protocol and interpretation. |
| **E6** | Hall/Carney on metal lots, including no-flow | **Useful minimum conventional comparator.** Make paired repeat measurements and uncertainty explicit. Do not infer thin-layer spreadability or unique cohesion from a funnel result. |
| **E7** | Shear-cell `ffc` on 3–4 lots; 2–4 week external turnaround | **Optional for a calibration paper; required external evidence if a cohesion-related physical inference is claimed.** Specify consolidation stress, conditioning and test standard. Three/four lots can provide a pilot comparison, not a strong cross-powder correlation. |
| **E8** | ~30 parameter sets × 3 tilts = **~90 simulator cases**, salt only; 45–90 CPU-h plus 2–3 coding days | **Defer in the minimum paper.** First test recovery/identifiability with known synthetic parameters, geometry/PSD uncertainty, wall friction/adhesion and random packings. Ninety cases are not necessarily 90 independent parameter locations. Salt-only inference cannot substantiate “inferred parameters across powders track shear-cell flow.” |
| **E9** | Layers of 3–4 Al 4047 treatments; 1–2 days | **Conditional, but a compact controlled subset is high value for an AM full article.** Essential if claiming spreading/packing prediction; otherwise substitute a quantitative charge-composition workflow outcome, or move to a calibration Methods/powder-handling paper. Do not claim a universal relation from one source batch. |

**Run arithmetic:** E1–E3 specify **222 executor doses**. E4 adds **28 explicitly counted doses**, so the full set is **250 counted doses**, consistent with the outline's ~250; using the rounded E4 ~30 gives ~252. Opening/closing fingerprints, references, resets, independent weighing and characterization are additional measurements, not all included in those totals. Calling it “four rig days” is an optimistic scheduling estimate rather than a dose-count identity.

## 7.2 Smallest sufficient packages: my choices, not a journal guarantee

### A. Focused full-length AM research article — my recommended route

I would retain only two connected claims: **per-powder calibration improves a measured alloy-preparation decision under controlled conditions**, and **standardized dosing records detect a meaningful within-alloy feedstock-flow change**. For that scope:

1. **E0 and pre-E1 readiness changes:** fix timing/lag, validate logging/retry/limits, measure hardware and define working fill. Preserve the old campaigns with their original classifications.
2. **E1–E3 at the central 0.5 g target:** the specified 22 + 20 + 8 + 8 = **58 executor doses per powder**, **174 total**. Remove the two eight-dose range blocks only if removing the “accessible range/minimum reliable mass” research claim. This keeps the authors' existing screen/BO budgets; I am not claiming they are statistically optimal or the absolute minimum possible.
3. **Add a small crossed repeatability/treatment study, not three more full optimizations.** For example, split one well-mixed Al 4047 source batch into **three independently handled paired aliquots**, apply the defined sieve treatment to one of each pair, and acquire standardized fingerprints in randomized order across repeated fills/days. This is a proposed minimum pilot design, not a completed result or a power-derived guarantee. It supports a within-source-batch treatment claim; broad batch-to-batch quality control would need independent production lots. Include an unchanged reference powder across days to separate task from session effects.
4. **E5–E6 on those exact aliquots/lots**, with replicated physical tests, including the removed fraction. Measure the sensing noise and independently reweigh a subset of final doses. If the doser cannot discriminate the controlled states above its measurement variability, report that negative result and withdraw the quality-control claim.
5. **One quantitative AM-facing validation:** a small subset of E9, for example the same three treatment pairs with two technical layers per aliquot (**12 layers**, analysed with aliquot/pair rather than each image as the independent unit), or a specified alloy-charge composition/preparation-tolerance result. This is my discretionary addition to the outline's minimum: it makes AM relevance more than “the powder is an alloy.” Choose the outcome before seeing which treatment gives a favorable result.

The core count is therefore **174 executor doses plus explicitly budgeted repeat fingerprints/reference measurements and the AM-facing validation**, not “174 doses proves acceptability.” If the range claim remains, use the original **222** and interpret the 16 endpoint trials as exploratory repeatability, not proof of a 95%-reliable minimum target. No new printer, multi-task campaign or inverse DEM is intrinsically required for this focused contribution.

### B. Methods-paper alternative

For an AM Methods paper I would make the tutorial/reproducibility contribution primary, not physical-property inference. A plausible smaller route is E0 + a matched E1 central-target demonstration (**58 doses if its range blocks are omitted**) plus at least a compact matched demonstration on actual AlSi10Mg under the same method. For example, **8 salt-transfer and 8 new-calibration validation doses** add 16, but do not count the acquisition of a new metal recommendation as zero-cost: its calibration budget must also be reported. A salt-only Methods submission with the old single metal dose is not a safe AM-specific fallback. Give code/configuration, worked examples, state checks and uncertainty, with E5 characterization sufficient to specify the materials. This package should drop the general feedstock-property, multi-task and inverse-DEM assertions.

### C. Broader “full scope” paper

If multi-task and contact inference remain central, all their validation work is additional, not an ornament:

- For multi-task, execute E4, retain a genuinely quarantined simulator benchmark if useful, and either run a fair prospective single-task/alternative comparator or restrict the claim to a prospectively validated multi-task recommendation. Use equal budgets, matched initial data, repeated seeds where meaningful and a non-leaking target definition. Learning a task matrix from three/four powders is a highly uncertain pilot, not evidence of learned physical similarity.
- For inverse DEM, E7 plus salt-only E8 supports at most a one-powder calibration case with external checking. A cross-powder association requires inference on those powders, identifiable parameters, independently measured geometry/PSD, multiple packings, discrepancy and withheld-condition prediction. Coarse-graining must pass a narrow-outlet sensitivity test, not only a global dimensionless-force match.
- For spreading transfer, E9 needs an out-of-condition prediction with no refitting to the very layer data used for validation. Merely correlating two quantities estimated from the same limited records does not close that loop.

Thus **the planned work can make a paper acceptable, but not every currently contemplated claim follows even if every row is checked off**. I would rather review the focused package with solid controls than 250 doses plus a fragile inverse-model appendix.

## 7.3 Analyses, run-count power and schedule audit

The strongest elements of OUTLINE §4.B are correcting balance lag, modelling log-time, adding an overshoot-aware decision, paired baseline blocks, covariates and preregistered property links. The omitted essentials are **crossed session/fill replication**, a real paired treatment design and a clear prospective algorithm-comparison estimand. The C1–C9/D1–D7 readiness checklist is referenced but not supplied; I can assess the changes summarized in OUTLINE, not verify the missing checklist or implemented code.

I also checked the outline's power statement under its explicit **independent log-normal times, common natural-log SD = 0.26, two-sided exact Mann–Whitney α = 0.05** model. In **200,000 Monte Carlo trials** with seed 20261127, I obtain:

| Group sizes | True ratio | Simulated power |
|---|---:|---:|
| 8 versus 8 | 2.0 | 0.9973 |
| 8 versus 8 | 1.5 | 0.8035 |
| 4 versus 8 | 2.0 | **0.9575** |

The outline's **0.72 for a twofold contrast at 4 versus 8 does not reproduce under those assumptions**. Its 8-versus-8 ~1.0 is supported; 0.78 for a 1.5-fold contrast is near but not identical to my simulation. Document the original power model/critical rule. More importantly, the log SD in the actual `corner-09` block is **0.790**, much larger than 0.26 (hand-tuned 0.264; `bo-005` 0.234). A power calculation based on the good stable blocks does not protect against the long-tailed or drifting state observed elsewhere. More independent sessions matter more than a nominally powered within-session n.

The dates in §4.D are plausible **targets conditional on access**, not a robust critical path. Pre-E1 readiness, E0 metrology and acceptance of the salt pilot should be go/no-go gates. The stated full scope omits explicit time for repeated fills/operators, a failed pilot, held-out DEM checks/coarse-graining and outside-lab repeat work. Ninety salt simulations at a fraction to several revolutions, additional packings and held-out cases may exceed the quoted CPU budget. With E7 shipped in January, a 2–4 week turnaround need not be the dominant risk; interpretation/rework is.

There is also a concrete scheduling inconsistency: the **minimum-version submission is about 12 February**, but the shared **write-up/figures/author-review window is 16 February–5 March**. Give the minimum route its own analysis and author-approval window before submission. The nominal four rig days also exclude E0's half day and may not cover cup handling every ten doses, references, working-fill resets, and paired treatment/fill repeats. Preserve the winter-break constraint; do not quietly use it as experimental time.

# 8. Consolidated priority-ranked revision list

I rank these by what blocks an interpretable result, not by ease. Tags use the requested categories; conditional items are explicitly marked.

| Priority | Revision | Tag | Completion criterion |
|---:|---|---|---|
| **1** | Freeze the scientific scope and intended article type: calibrated dosing plus validated batch decision, or a tutorial Methods paper. Defer multi-task/inverse DEM unless they are principal contributions. | **writing only** | Title, questions, abstract, figures and conclusion describe one evidence-supported paper; no requirement to run optional work merely to fill an outline. |
| **2** | Qualify hardware and weighing dynamics (E0/readiness): measured outlet/core gap, tube ID, fill/drawdown, balance settling/calibration/actuation blank and subset independent final weighing. | **new experiments** | Traceable measurement uncertainty and a passing pilot under the corrected lag/timing implementation. |
| **3** | Run matched, randomized/interleaved recommendation and baseline blocks under the same firmware/afterflow/state; replicate an anchor across fills/days (E1–E3). | **new experiments** | Separate setting effects from day, order and powder state; report the complete acquisition/validation budget. |
| **4** | Convert E3 into a paired, replicated sieved/unsieved Al 4047 treatment experiment; measure the removed particles and retained PSD/fraction. | **new experiments** | Detectable state change exceeds measurement-system variability, or the negative result is reported; no unverified universal oversize diagnosis. |
| **5** | Measure same-lot/aliquot PSD, density, moisture-related loss and conventional flow response (E5–E6). | **new experiments** | Protocol, weights/fractions, replicates, conditioning, uncertainty and no-flow outcomes supplied; old lots never relabelled with new-lot data. |
| **6** | Add one quantitative AM decision/outcome—compact paired E9 or an alloy-charge composition/tolerance workflow. | **new experiments** | Demonstrated application benefit or explicitly narrowed Methods/powder-handling scope; no requirement for a token printed build. |
| **7** | Rebuild Fig. 7b and its source table; reconcile ρ/n/response definition and show exclusions and the full exploratory test family. | **new analysis of existing data** | One consistent text/figure/SI analysis; sensitivity to estimated properties, noise/no-flow and sample inclusion. |
| **8** | Reconcile controller labels, final tolerance, reference-point penalties and equipment failure by firmware/mode; preserve all 125 records and suspected-starvation flags. | **new analysis of existing data** | Explain S2 #20/S4 #5, 178 taps/120 cycles, 802.7 s/600 s, range fault and the missing two-dose inventory; report both physical and end-to-end yield. |
| **9** | Reframe inferential claims and rerun the specified robust analyses: tie-aware exact permutations, conditional-success time, dispersion, exclusions, multiplicity and stable-state limits. | **new analysis of existing data** | Correct arithmetic retained; “not significant” is not equivalence; binomial bounds conditional on their sampling assumptions. |
| **10** | Analyse common-window, noise-aware feed factors/interruption fractions with actual timing/turns, startup/lag sensitivity and old bench-noise stratification. | **new analysis of existing data** | Feedstock comparisons are not artifacts of short windows, fixed-order speed errors or group-confounded noise. |
| **11** | Establish the calibration-strategy baseline appropriate to the claimed novelty: screening/linear/Sobol versus BO, equal budgets and prespecified recommendation rules. | **new analysis of existing data** | Existing data support only a transparent retrospective comparison; any simulator-based result is labelled as such, not a measured online win. |
| **12** | Implement the one-sided feasibility/risk objective, log-time/state-aware model and clear external acceptance tolerance before new campaigns. | **new analysis of existing data** | Historical objective remains documented; model choice and thresholds are fixed prospectively for new data. |
| **13** | Resolve paper overlap locally and in both cover letters: shared dose IDs, same-event attribution, 7.993 g headline, 25 versus 31 mg/s estimator, flight dimension and companion version. | **writing only** | Both editors receive both manuscripts and an overlap table; primary versus secondary results are unmistakable. |
| **14** | If multi-task is retained, carry out E4 with a leakage-free, equal-budget prospective comparison or narrow the claim to recommendation validation. | **new experiments** | Independent test-task evidence answers the actual claimed efficiency question; ten simulator seeds are not ten laboratory replications. |
| **15** | If inverse DEM is retained, complete recovery/identifiability, geometry/PSD/stiffness/packing/discrepancy and withheld-condition tests before reporting contact parameters. | **new analysis of existing data** | This includes new computational simulations; parameters are identifiable/effective with uncertainty, not fitted artifacts. Salt-only results are labelled salt-only. |
| **16** | If claiming physically meaningful cohesion across powders, extend inference to the E7 lots and obtain matched independent shear tests. | **new experiments** | External property comparison has appropriate stress/conditioning and adequate independent material states; no salt-only-to-multipowder leap. |
| **17** | Supply a frozen reproducibility release: raw stage/telemetry and per-powder response tables, model code/environment, DEM inputs, failure inventory and scoped prompt-log archive; update S8 and dossier. | **writing only** | Repository/DOI claims are verifiable; corrected source table generates every numeric figure annotation; missing old records are acknowledged. |
| **18** | Finish publication hygiene without inflating scope: concise apparatus provenance, true measured/proposed Fig. 1 labels, safety for combustible metal dust/static, current reference/author contributions and compliant word count. | **writing only** | Self-contained Methods/research narrative, not a dependent “part II”; minimum-route analysis/author-review schedule precedes its submission date. |

# 9. Sources and reproducibility

**Supplied primary materials:** main.pdf (Sections 1–5, Figs. 1–7, Tables 1–2); si.pdf (Tables S1–S9, Fig. S1); hardware_paper_main.tex (source labels and line locations given above); OUTLINE.md §4/§4b; SUBMISSION.md; 16-journal-editors.md; 17-suggested-reviewers.md; 08-powder-properties-experts.md. Input SHA-256 hashes are in the audit bundle. I evaluated these versions, not the outline's descriptions of an older review or files absent from the collection.

**[W1] Elsevier.** *Guide for authors — Additive Manufacturing.* Accessed 27 November 2026. https://www.sciencedirect.com/journal/additive-manufacturing/publish/guide-for-authors . I used its Methods-paper criteria, standalone/no-part-paper rule and scope/format requirements; I did not infer them solely from SUBMISSION.md.

**[W2] Elsevier.** *Publishing ethics.* Accessed 27 November 2026. https://www.elsevier.com/about/policies-and-standards/publishing-ethics . I used the multiple/redundant/concurrent-publication policy, not a blanket rule that any shared data are forbidden.

**Prior-work metadata checks:** Bilal El Kassem et al. (2021), *A Semi-Automated DEM Parameter Calibration Technique of Powders Based on Different Bulk Responses Extracted from Auger Dosing Experiments*, KONA 38, 235–250, DOI **10.14356/kona.2021010**; Olukayode I. Imole et al. (2016), *Experiments and discrete element simulation of the dosing of cohesive powders in a simplified geometry*, Powder Technology 287, 108–120, DOI **10.1016/j.powtec.2015.07.051**. These correspond to the manuscript's acknowledged precedents; I verified citation metadata, not a new full-text literature review.

The audit bundle contains the reconstructed per-dose tables, numerical summaries/comparisons, paired-corner table, extracted manuscript/SI text, source hashes, live-policy snapshots, complete BibTeX entries and an executed reproducibility script. The calculations use rounded SI observations, so tiny last-digit differences from unrounded telemetry are expected. No synthetic planned result is used as an observation in this audit.

## Discretionary analytical decisions

- I used three clearly labelled expert-inspired simulated reports rather than claiming to speak for actual researchers.
- I honored the manuscript's explicit eight-dose validation blocks; I separately checked inclusion of the two pre-restart doses rather than silently changing the main analysis.
- I used two-sided exact rank tests for the specified time comparisons, label permutation for tied absolute errors, and exact enumeration of empirical-bootstrap median distributions to remove resampling noise.
- I treated reliability intervals as conditional on independent stable trials and kept controller “ok,” engineering feasibility and system-level completion distinct.
- I classified reused records separately from reused graphics or new derived analyses; I did not infer misconduct from overlap or claim identity of unavailable companion graphics.
- I favored a narrower controlled AM-facing study over mandatory completion of all optional work. My 174-dose proposal removes range claims and adds explicit state/treatment validation; it is not a formal minimum-sample-size proof.
- I required an AM-relevant measured decision/outcome for my preferred research-article route, while allowing either thin-layer validation or a quantitative charge-preparation alternative rather than demanding printing for appearance.
