## Bottom line

The dataset supports an **exploratory hardware-characterization result**: the same auger and fixed control policy produced large, powder-dependent differences in conveyed mass, repeatability, tap response, completion status, and dose error. It does **not yet support stable powder “flow-regime” classification, universal thresholds, or population-level performance claims**, because there is one battery run per powder and the within-run revolutions/doses are technical or sequential observations, not independent powder preparations.

The frozen-controller comparison is fair if presented as a **deliberate transfer or robustness test**: “What happens when one salt-calibrated policy is transferred without retuning?” It becomes a strawman if presented as evidence that a competently tuned universal controller is impossible, or that the hardware cannot dose these powders accurately. The experiment tested one parameter set, one order of operations, one fill state, and one run per powder.

A further limitation is that the supplied `/workspace/main.pdf` is an unfilled RSC template, not the substantive draft. I could therefore assess the proposed framing and figure, but not whether the current manuscript text already states the limitations fairly.

## Review of the eight observations

### 1. Feed factor spans three orders of magnitude

**Supported descriptively, with wording changes.**

The largest block-C mean is 232.25 mg rev⁻¹ for calcium lactate at 90°. Brown-rice-flour means are 0.20–0.30 mg rev⁻¹, giving ratios of 774–1161, or 2.89–3.07 decimal orders. “Approximately three orders of magnitude” is accurate for the observed run.

Do not describe the brown-rice-flour mean itself as below the 0.1 mg display increment: its mean is 0.20–0.30 mg rev⁻¹, created by many zeros and occasional measurable releases. Instead report the **fraction of individual increments recorded as zero/below the display increment** and the distribution of nonzero increments. Also say “observed in this battery,” not an intrinsic three-order powder-property range.

### 2. Speed dependence separates flow regimes

**The trends are descriptive; the regime labels overreach.**

The endpoint changes reported in the digest are large for calcium lactate (−33%), xanthan gum (−55%), and white rice flour (+94%). They justify saying that **mass per revolution showed powder-dependent apparent speed dependence in this run**.

They do not establish the proposed mechanisms:

- Decreasing mass per revolution could reflect reduced flight filling time, but also hopper consolidation, progressive depletion, wall adhesion, transient conditioning, or order effects.
- Increasing mass per revolution could reflect agitation or arch disruption, but “fluidisation” is not established without direct observation or pressure/packing evidence.
- A +17% or +23% endpoint change is not evidence of “near-geometric metering” unless uncertainty around the slope is sufficiently narrow and replicated runs show practical equivalence to zero slope.
- Only three consecutive revolutions per speed and one run per powder cannot separate RPM from time/order. These revolutions are not independent biological-style replicates.

The CSV contains one aggregated block-D row per powder rather than speed-specific rows, so the stated endpoint slopes and their uncertainty cannot be independently reconstructed from the supplied CSVs. Show all revolution-level points by RPM and fit only an exploratory powder × RPM relationship. A randomized or counterbalanced RPM sequence across independent refills is needed for mechanistic classification. Prefer “apparent negative/positive/weak speed dependence” to named regimes in this paper.

### 3. Tap efficacy tracks feed factor

**Qualitatively plausible, but the threshold and broad property claim are unsupported.**

At 45°, calcium lactate and xanthan gum have both the two highest feed factors and the two largest tap responses. Across seven powders, Pearson correlation is high, $r=0.984$, but it is dominated by those two high-valued powders. Rank correlation is only $\rho=0.607$, $p=0.148$. With seven non-independent powder cases, this does not establish a general relationship or a threshold near 100 mg rev⁻¹.

For the low responses, 95% within-run *t* intervals include zero: for example, white rice flour is 0.113 ± 0.170 mg and CMC is 0.150 ± 0.257 mg at 45°. These should be called **not resolved from zero under this measurement protocol**, not simply tap quanta. The high responses are clearly resolved: calcium lactate 20.36 ± 2.36 mg and xanthan gum 13.61 ± 2.88 mg, based on eight within-run trials. Salt is intermediate at 3.05 ± 1.02 mg.

### 4. CMC has non-monotonic tilt behavior attributed to arching

**The observed transient is real within the run; arching is a credible hypothesis, not a demonstrated cause.**

CMC’s mean falls from 26.35 mg rev⁻¹ at 45° to 9.35 mg rev⁻¹ at 90°. At 90°, however, the six revolutions are 39.0, 7.4, 4.0, 1.8, 1.4, and 2.5 mg. The first is 11.4 times the mean of the remaining five (3.42 mg), showing a strong sequence transient. Calling this a stable vertical feed factor is questionable; summarize both the full sequence and the post-first-revolution result.

Arching over the intake is mechanically defensible because discharge collapses after an initially charged revolution. Other possibilities remain: depletion of preloaded flights, wall adhesion, compaction, channel formation, or a tilt-transition artifact. Confirmation should combine:

1. at least three independent refill/repack runs at 45° and 90°;
2. randomized tilt order, including repeated 45→90 and 90→45 transitions;
3. continuous mass-versus-time traces for each revolution;
4. video through a transparent hopper/intake or imaging that directly shows a stable cavity/bridge;
5. a controlled bridge-breaking intervention, such as a tap or probe, followed by immediate recovery of feed.

Recovery after visibly disrupting a bridge would be much stronger evidence than the mass trace alone.

### 5. Manual versus rig disagreement is bidirectional

**The disagreement may be useful motivation, but the mechanism is speculative and the comparison is not controlled.**

The bidirectional anecdotes argue against applying one simple manual-to-rig correction. They do not show that manual testing measures gravity flow while the rig measures mechanically broken arches, because operator, protocol, fill level, orientation history, number of turns, and outcome definitions differ.

Phrase this as: “Qualitative operator observations did not consistently predict powered conveying in the battery.” Then provide the manual protocol and raw records, or move the anecdotes to discussion. A defensible validation would test the same fill, tilt sequence, auger turns, and endpoint on the hand-operated and powered apparatus, ideally blinded to powder identity and with multiple operators/runs.

### 6. Dose accuracy is uncorrelated with feed factor and depends on similarity to salt

**The controller-transfer failure is strongly illustrated; the correlation and ‘proximity’ claims overreach.**

The outcomes are concrete:

- salt: mean error +0.2 mg, SD 7.5 mg; 2/3 within ±5 mg;
- calcium lactate: −26.5 mg, SD 10.0 mg;
- xanthan gum: −32.9 mg, SD 9.6 mg;
- CMC: −43.2 mg, SD 5.4 mg;
- white rice flour: −137.9 mg, SD 23.5 mg;
- sodium alginate: −291.5 mg, SD 18.2 mg;
- brown rice flour: −999.1 mg, SD 0.9 mg.

These show poor transfer of this salt-tuned policy. They do not establish “uncorrelated.” Using absolute mean error, the seven-powder Pearson estimate is $r=-0.432$, $p=0.332$; Spearman is $\rho=-0.786$, $p=0.036$, largely reflecting the non-conveying brown rice flour. Excluding brown rice flour gives $r=-0.458$, $p=0.361$ and $\rho=-0.657$, $p=0.156$. With only 6–7 powders and structurally different failure modes, correlation testing is not informative. Say **feed factor alone did not predict transfer performance** and illustrate this with calcium lactate versus sodium alginate.

“Proximity to salt’s properties” is undefined and untested. Define a priori properties such as feed factor, tap response, bulk density, particle-size distribution, cohesion, moisture, and compressibility, then test prediction in a larger powder set.

The logged `cycle-budget` and `stalled` statuses support two controller-level failure classes. The more detailed causal explanation involving anticipation, handover, and tap collapse should be backed by cycle-by-cycle traces and explicit state-transition rules. Note that poor dose accuracy here is partly **intentional censoring by safety/cycle limits**, not merely steady-state controller error.

### 7. Salt drifts within the run

**This is a serious warning about run order, but the current evidence does not prove a monotonic feed drift.**

The salt’s block-E/block-C 45° re-feed ratio is 2.68, compared with 0.74–1.08 for the other conveyable powders. Brown rice flour is 4.8 but is near the resolution limit and should not be used in this comparison. Salt dose errors progress from −4.7 to −3.5 to +8.8 mg, but three sequential values are too few to establish monotonic drift statistically, and dose error also depends on changing cycle paths: the third dose used no taps and fewer revolutions.

Repeat the complete salt battery before submission. More importantly, insert short identical reference checks throughout a run, for example 3–6 revolutions at 45°/30 RPM before and after every block. That separates time drift from block/protocol differences. Record hopper mass, fill height, humidity, elapsed time, tilt history, and any agitation.

Until repeated, label salt block-C and block-D results as affected by order-dependent instability and exclude salt from speed-slope interpretation. Calling block C a “lower bound” is only justified if all plausible biases can increase later output; presently it is safer to call it an **early-run estimate that was not reproduced later**. The issue weakens salt as a quantitative reference but does not erase the very large cross-powder contrasts. It does prevent strong claims about small differences involving salt.

### 8. No powder avalanches through a stationary auger

**Supported only as a protocol-bounded observation.**

All 21 single 15 s holds yielded recorded zero change. State exactly that: “No mass change at the 0.1 mg display increment was observed during any of the 21 15 s static holds.” Do not generalize to “no powder avalanches” or “the auger is a meter, not a valve” across time, fill levels, vibration, powders, or environments. Each powder–tilt condition has only one hold, and the 21 observations are not equivalent independent trials. Longer holds, independent refills, and vibration/disturbance tests are required for a leakage specification.

## Explicit answers to the seven questions

### 1. Is the frozen salt-tuned framing sound and fair?

**Yes, as a transferability stress test; no, as proof that one controller cannot work across powders.** State that the parameters were deliberately not optimized so powder effects could be observed under a common policy. Compare against a positive control only after repeating salt. Avoid blaming the controller for expected out-of-domain behavior. The conclusion should be that **calibration did not transfer under the tested constraints**, motivating per-powder characterization and adaptive or recipe-based control.

### 2. Are the speed-sweep flow regimes defensible?

The observed slopes are defensible as exploratory trends. The named regimes and mechanisms are not established by three revolutions per RPM in one ordered run. Use neutral slope language and treat gravity filling, agitation, and arch breaking as candidate mechanisms.

### 3. Is CMC arching adequately evidenced, and what would confirm it?

No. The trace supports a transient vertical-feed collapse consistent with arching. Confirmation requires replicated randomized tilt transitions plus direct visualization and recovery after deliberate bridge disruption.

### 4. How should salt drift be handled?

Repeat the full salt run and add interleaved reference checks. Caveat and exclude the current salt speed slope. Do not call block C a lower bound without directional evidence. The drift limits salt-centered quantitative comparisons but does not threaten order-of-magnitude contrasts among powders.

### 5. Which results are publication-quality now, and which need replication?

**Suitable now as transparent pilot/exploratory figures:**

- all raw block-C revolution values by powder and tilt;
- all 21 dose outcomes, statuses, cycle counts, and elapsed times;
- the CMC 90° revolution sequence as a case-study trace;
- tap-trial distributions, explicitly marking unresolved measurements;
- a controller state/failure-mode diagram tied to logged traces.

**Need independent replication for main-paper performance claims:**

- feed-factor rankings and tilt effects;
- RPM slopes and any regime classification;
- tap-response ranking or threshold;
- salt performance and drift;
- dose accuracy/repeatability;
- stationary leakage claims;
- manual-versus-rig conclusions.

At least three independent runs per powder, with empty/refill/repack between runs and preferably spread across days, would establish run-to-run reproducibility. Three is still a minimum, so show every run and confidence intervals rather than relying on normality tests with low power. Prioritize salt, CMC, one high-feed powder, one cycle-budget powder, and brown rice flour if running all seven is infeasible.

### 6. What statistical treatment and below-resolution handling are appropriate?

- Treat **independent runs**, not revolutions, as the experimental unit for powder-level inference.
- Show raw points and sequence/order. Use mean ± SD for within-run variability; do not use SEM bars as if they describe run-to-run reproducibility.
- Report median and range or interquartile range alongside mean/SD for skewed or zero-inflated series. RSD is unsuitable when the mean is near zero and becomes undefined or misleading; report detection frequency and absolute spread instead.
- For replicated runs, use a hierarchical or mixed-effects model with run as a random effect and tilt/RPM as within-run factors. With few runs, emphasize estimates and confidence intervals rather than p-values. Correct multiplicity if many pairwise powder/tilt comparisons are formally tested.
- For the three doses, show all points, mean error and SD, completion proportion, and failure status. Do not infer normality or report a precise 95% interval as a validated performance bound from $n=3$.
- Distinguish balance **display increment/readability** (0.1 mg) from detection limit, quantification limit, and noise. Eight unchanged baseline readings do not validate a detection limit under active dispensing.
- Values displayed as zero are interval-censored by rounding and instrument behavior; they are not exact zero. A mean below 0.1 mg can result from averaging repeated quantized readings but is not a directly resolved single-trial quantum.
- For low tap/feed measurements, report counts such as “$k/n$ trials produced a positive displayed increment,” the distribution of nonzero events, and cumulative mass across repeated actuations if available. If using bounds, specify the censoring model and interval. Do not automatically label every sub-0.1 mg average as an upper bound.

### 7. How limiting are the missing vibration and metal-powder data?

The missing vibration block means the paper cannot claim a complete fixed battery, quantify vibration effects, or evaluate leakage/flow under the disturbance that may matter most for cohesive powders. Rename it the “implemented battery excluding vibration,” or add vibration before submission. It does not invalidate the non-vibration blocks.

The lack of AlSi10Mg, silicon, or another application-relevant metal powder sharply limits relevance to metal additive-manufacturing or inorganic synthesis workflows. The current powders span behavior, but food and polymeric powders are not substitutes for metal powders with different density, morphology, abrasiveness, electrostatics, and safety constraints. Either:

1. add at least two real target powders, ideally one relatively flowable spherical alloy and one difficult/angular or fine powder, with appropriate containment and safety controls; or
2. narrow the manuscript’s claims to low-cost open-hardware powder dosing demonstrated on seven non-metal model powders.

For a hardware Full Paper, option 1 would materially strengthen external validity.

## Priority actions

1. **Repeat salt immediately**, with interleaved feed checks, environmental logging, and block-order diagnostics.
2. **Generate independent run replication** for the most claim-critical powders. Use fresh refill/repack and randomized tilt/RPM order. If possible, replicate all seven at least three times.
3. **Add application-relevant metal powders** or narrow the application claims explicitly.
4. **Complete or remove block F.** Do not present an unexecuted vibration block as part of the validated battery.
5. **Release revolution/trial-level data.** The provided summaries cannot reconstruct speed-specific slopes, zero counts, temporal patterns, or uncertainty correctly.
6. **Reframe mechanisms as hypotheses.** Replace “flow regimes,” “fluidises,” and “arching causes” with observed behavior followed by testable candidate explanations.
7. **Rebuild the cross-powder figure.** Panel A should show raw revolution points plus mean/SD, retain sequence where relevant, and mark censored/zero readings. The current bars hide the extreme within-condition variation, including CMC’s 157% RSD at 90°. Panel B should retain individual doses but add the ±5 mg acceptance band, failure symbols/statuses, and preferably elapsed time or cycle burden in a companion panel. A 0.1 mg “balance resolution” line should not imply a validated detection limit.
8. **Separate three outcomes:** conveyability, within-run metering variability, and closed-loop completion/accuracy. A powder can convey rapidly yet fail the transferred control policy; these are different hardware claims.
9. **Replace correlation language with contrasts.** “Feed factor alone did not determine success” is supported; “uncorrelated” and “tracks with a ~100 mg rev⁻¹ threshold” are not.
10. **Use a claim table in the manuscript/ESI** listing each result, experimental unit, sample size, uncertainty measure, and whether it is exploratory or replicated.

## Main threats to validity

- one independent run per powder and substantial pseudoreplication risk;
- fixed block order, confounding treatment with elapsed time and conditioning;
- salt’s large intra-run discrepancy;
- low-response measurements near a quantized display increment;
- possible changing hopper fill level, packing, humidity, and tilt history;
- only three sequential doses under different controller paths;
- no vibration data;
- no target metal powders;
- uncontrolled manual-versus-powered comparison;
- summaries that omit RPM-level and trial-level raw observations.

These limitations still permit a useful paper if it is positioned as an **open-hardware method plus exploratory transferability study**, with raw data and restrained mechanistic interpretation. They are not sufficient for broad claims of powder-class regimes, universal tap thresholds, or validated cross-powder dosing performance.

### Discretionary analytical decisions

- Treated independent battery runs, rather than revolutions or sequential doses, as the experimental unit for cross-powder inference.
- Used both Pearson and Spearman correlations only as diagnostics of observations 3 and 6; did not treat either as confirmatory with seven powders.
- Used 95% within-run *t* intervals to illustrate whether tap responses were resolved from zero, while explicitly not interpreting them as run-to-run reproducibility intervals.
- Recommended mean ± SD plus raw observations rather than SEM error bars because the immediate concern is observed variability, not precision conditional on one run.
- Recommended neutral “apparent speed dependence” categories rather than mechanistic flow-regime labels.
- Recommended at least three independent refill/repack runs per powder as a practical minimum, while recognizing that a precision-based sample-size calculation would be preferable after pilot variance is available.
- Treated balance-zero observations as interval-censored/quantized rather than exact zeros or automatically as upper bounds.
- Recommended narrowing claims if real metal powders and vibration testing cannot be added.