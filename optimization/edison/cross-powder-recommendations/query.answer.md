# Cross-Powder Characterization and Its Impact on Salt-Derived MPC / Stop-Response Recommendations

## Executive Summary

The seven-powder uniform battery (Dataset A) materially revises several salt-only recommendations while strengthening others. The core MPC architecture (phase-switched, observer-based) remains sound, but the **data-collection plan, model structure, and protocol upgrades all require revision** in light of the 3-order-of-magnitude spread in feed factor, sign-flipping speed dependence, non-monotonic tilt behaviour, and the two distinct failure modes observed across powders. Below, each numbered question is answered with citation-backed reasoning.

| Recommendation area | Original salt-only recommendation | Cross-powder evidence | Verdict (holds/revise/strengthen) | Priority change |
|---|---|---|---|---|
| Per-powder identification vs transfer learning | Run full identification on 3–5 anchor powders, then reduced transfer sets for new powders, indexed by density/FFC | Dataset A shows ~3 orders of magnitude spread in feed factor, sign-flipping speed dependence, and non-monotonic tilt response (CMC peaks at 45°, then drops at 90°), so powder behavior is not smoothly ordered by a single descriptor; literature supports density/conditioned bulk density as a good predictor of feed-factor magnitude, but not a sufficient predictor of all dynamics, while flowability/compressibility help explain variability and hopper-emptying effects (li2020predictiveperformanceof pages 36-40, li2020predictiveperformanceof pages 49-53, bostijn2019amultivariateapproach pages 22-26, jonessalkey2023reviewingtheimpact pages 8-10) | Revise | Increase: reduced transfer sets are still useful for screening/priors, but each new powder now needs at least a short direct identification burst before closed-loop use |
| Feed-factor map contents | Identify per-powder feed maps ff(tilt, fill, ω) with explicit in-flight and lip states | Dataset A strongly supports this: feed factor changes massively by powder and tilt, and speed dependence changes sign by powder; literature also shows hopper level/stress changes effective density and therefore feed factor, and screw-speed effects can be nontrivial and material-dependent (bostijn2019amultivariateapproach pages 10-14, fathollahi2024improvingcontinuouslossinweight pages 1-2, bascone2020hybridmechanisticempiricalapproach pages 11-14, bascone2020hybridmechanisticempiricalapproach pages 25-30) | Strengthen | Increase to top priority |
| Descriptor-based priors | Use bulk/tapped density and FFC to index priors across powders | Cross-powder evidence does not kill descriptor-based priors, but it narrows their role: literature shows conditioned/bulk density predicts feed-factor magnitude well, and FFC/flowability help predict variability/stability; neither is enough to predict sign of speed dependence or tilt non-monotonicity from current evidence (li2020predictiveperformanceof pages 36-40, li2020predictiveperformanceof pages 49-53, bostijn2019amultivariateapproach pages 22-26, jonessalkey2023reviewingtheimpact pages 8-10) | Revise | Keep as medium-priority support layer, not primary model-transfer mechanism |
| Stop-response tests | Measure stop tests and treat τ≈1 s as a seed for observer/Smith-predictor design, not a fixed offset | Dataset A makes powder invariance of τ less plausible because per-rev slug mass and flow regime differ dramatically across powders; literature on feeders emphasizes powder-dependent effective density, fill level, and flow regime changes, while dead-time compensation remains sensible if re-identified per material/condition (bascone2020hybridmechanisticempiricalapproach pages 11-14, fathollahi2021developmentofa pages 4-5, li2020predictiveperformanceof pages 36-40) | Hold, but revise scope | Increase: cross-powder stop-response is now mandatory before assuming a shared τ |
| Protocol upgrade: randomize tilt order and halt masses | Randomize order of tilt and stop mass to reduce drift/confounding | Dataset A salt drift within one run and strong powder-specific tilt effects make fixed-order protocols even less trustworthy; literature shows feeder response changes with hopper stress/fill and operating point, so randomization remains necessary (bostijn2019amultivariateapproach pages 10-14, fathollahi2024improvingcontinuouslossinweight pages 1-2, fathollahi2024improvingcontinuouslossinweight pages 4-6) | Strengthen | Increase |
| Protocol upgrade: deconfound actuators | Separate auger-only, tap-only, and combined stop-response trials | Dataset A shows tap efficacy tracks powder/feed regime and collapses toward zero for some powders, so actuator-separable characterization is even more important; otherwise controller failure modes cannot be attributed correctly (supported mechanistically by distinct screw-fed vs density/state-dependent behaviors in feeder literature) (bascone2020hybridmechanisticempiricalapproach pages 11-14, fathollahi2021developmentofa pages 4-5, fathollahi2021developmentofa pages 12-13) | Strengthen | Increase to top priority |
| Protocol upgrade: track fill level every trial | Track fill level as a primary factor | Dataset B already suggested fill affects auger and tap differently; Dataset A plus literature on feeder densification/refill disturbances makes fill/state tracking the single highest-value protocol addition. Hopper stress and refill perturb density, feed factor, and drift (bostijn2019amultivariateapproach pages 10-14, fathollahi2024improvingcontinuouslossinweight pages 1-2, fathollahi2024improvingcontinuouslossinweight pages 2-4, fathollahi2024improvingcontinuouslossinweight pages 6-7, li2020predictiveperformanceof pages 66-73, bascone2020hybridmechanisticempiricalapproach pages 11-14) | Strengthen | Increase to highest priority |
| Protocol upgrade: tilt-only blanks and avoid tilt moves near endpoint | Add tilt-only blank trials; interlock tilt changes away from final approach | Dataset B found a tilt move can release mass; Dataset A’s strong tilt sensitivity across powders means this remains critical and likely powder-specific (owen2009predictionofscrew pages 11-13, owen2009predictionofscrew pages 10-11) | Hold | No change to high priority |
| Protocol upgrade: measure balance step response | Characterize balance-only settling separately from powder settling | Cross-powder evidence does not weaken this; if powders differ strongly in afterflow/landing dynamics, separating instrument response from powder response becomes even more valuable for observer design | Hold | Slight increase |
| Continuous-rate endpoint control | Use anticipation/observer logic rather than naive continuous-RPM control near endpoint | Dataset A and B reinforce that endpoint control cannot assume a smooth continuous rate; B shows quantized per-revolution delivery and A shows powder-dependent feed maps; DEM/mechanistic literature also describes screw transport as structured by angular position, inclination, fill, and flow regime rather than ideal continuous discharge (owen2009predictionofscrew pages 10-11, owen2009predictionofscrew pages 1-2, owen2009predictionofscrew pages 2-4) | Strengthen | Increase |
| Stationarity/session qualification | Implicitly assume session data are usable after normal setup | Dataset A salt drift and Dataset B fill/repack reversals imply a formal pre-check is needed before trusting a session; literature reports refill/fill-state disturbances and long relaxation of density/stress fields (fathollahi2024improvingcontinuouslossinweight pages 6-7, fathollahi2024improvingcontinuouslossinweight pages 4-6, bascone2020hybridmechanisticempiricalapproach pages 11-14) | Revise | Add new high-priority gate before any characterization run |
| Validation breadth | Test 2–3 more powders before generalizing | Dataset A already supplies multi-powder evidence and shows the need for broader validation, not less; literature likewise emphasizes strong material dependence of feeder performance (bostijn2019amultivariateapproach pages 22-26, jonessalkey2023reviewingtheimpact pages 8-10, owen2009predictionofscrew pages 1-2) | Strengthen | Increase from desirable to essential |
| Controller tuning strategy | Collect data for a phase-switched MPC-style controller with observer states for in-flight and lip inventory | Dataset A supports the architecture choice but shows the observer/model must include powder-specific ff maps, fill/state dependence, and actuator-specific trim efficacy; literature supports material-specific calibration plus adaptive correction rather than one frozen calibration (bascone2020hybridmechanisticempiricalapproach pages 11-14, fathollahi2021developmentofa pages 4-5, fathollahi2021developmentofa pages 12-13, fathollahi2021developmentofa pages 13-14) | Hold, but expand modeled states | Increase |


*Table: This table compares the original salt-only recommendations with what the seven-powder dataset now shows. It highlights which recommendations remain valid, which must be revised, and which become higher priority for building a robust cross-powder dosing controller.*

---

## Question 1: Does Dataset A Change the Data-Collection Priorities?

**Yes — substantially.** The salt-only plan proposed 3–5 anchor powders with a reduced transfer set indexed by bulk/tapped density and FFC. Dataset A shows that powder space is **not smoothly interpolable** by these descriptors alone:

- **Feed factor magnitude** spans ~3 orders of magnitude (232 mg/rev for calcium lactate at 90° down to <0.3 mg/rev for brown rice flour). The literature consistently identifies **conditioned bulk density (cBD)** as the best single predictor of feed-factor magnitude across screw feeders (R² > 0.9 in one 14-material study), with bulk and tapped density positively correlated with the maximum feed factor (li2020predictiveperformanceof pages 49-53, li2020predictiveperformanceof pages 36-40). This is mechanistically expected: a constant-volume screw flight delivers mass proportional to the in-flight packing density.

- **Sign of speed dependence** is not predicted by density or FFC. Dataset A shows calcium lactate and xanthan gum (high feed factor, likely free-flowing in the auger) exhibit **decreasing** mass-per-rev with increasing RPM (−33% and −55%, respectively), while white rice flour shows a **+94% increase**. The literature reports only a "weak negative correlation" between screw speed and FFmax that remains consistent across tested powders in pharmaceutical twin-screw feeders (bostijn2019amultivariateapproach pages 22-26), and no known single descriptor predicts the sign flip. DEM studies show that the balance between recirculatory avalanching flow (dominant at low inclination/low fill) and swirling bed flow (dominant at high inclination) shifts with speed, fill, and particle friction properties (owen2009predictionofscrew pages 11-13, owen2009predictionofscrew pages 10-11), suggesting that the sign of speed dependence is governed by the **flow regime** (flood-fed vs. starve-fed, cohesive arch vs. free avalanche) rather than a simple scalar property.

- **Tap efficacy** tracks feed factor magnitude (20 mg/tap for high-feed powders, <0.25 mg for low-feed powders), which is consistent with tap yield being proportional to the mass of loosely retained lip inventory — itself set by the feed factor at the operating tilt.

- **Tilt non-monotonicity** (CMC peaks at 45°, drops 2.8× at 90°) is unique among the seven powders. DEM studies confirm that inclination changes the flow pattern from a bulldozer-heap regime (low angles) to a uniform-depth swirling bed (high angles), with axial velocity dropping linearly up to ~60° then levelling off (owen2009predictionofscrew pages 11-13, owen2009predictionofscrew pages 10-11). CMC's non-monotonicity likely reflects a cohesive arch or bridging interaction at high tilt that is not captured by a monotonic density/FFC index.

**Recommendation:** A density/FFC-indexed transfer-learning approach is **defensible for initialising priors** on feed-factor magnitude, but **not sufficient** for predicting speed-dependence sign, tilt optima, or tap efficacy. Each new powder requires at minimum a **short direct identification burst** (a few revolutions at 2–3 tilts and 2–3 speeds, plus a tap sequence) before closed-loop dosing. The "reduced ~60–90 min transfer set" should be retained but understood as an identification experiment, not a mere validation of a transferred model. The most predictive descriptors from the literature are: (i) conditioned bulk density for feed-factor magnitude (li2020predictiveperformanceof pages 49-53, bostijn2019amultivariateapproach pages 22-26), (ii) FFC/flowability for feed-rate variability and stability (jonessalkey2023reviewingtheimpact pages 8-10), and (iii) compressibility (Carr Index, C@15kPa) for feed-factor decay with hopper emptying (bostijn2019amultivariateapproach pages 22-26). No established descriptor predicts speed-dependence sign; this must be measured directly.

---

## Question 2: Is τ ≈ 1 s Afterflow Constant Powder-Invariant or Powder-Specific?

**Almost certainly powder-specific.** The afterflow time constant τ was measured only on coarse granulated NaCl. Several lines of reasoning predict powder dependence:

1. **Physical mechanism:** Afterflow comprises (a) material already in the screw flights continuing to discharge after motor stop (inertial rundown), and (b) material draining from the lip/tube exit under gravity. The mass of (a) scales with the per-flight slug mass, which spans 3 orders of magnitude across Dataset A powders. While the *time* for inertial rundown depends primarily on screw/motor deceleration (geometry-dominated), the *draining time* of residual lip material depends on powder cohesion, angle of repose, and packing state — all powder-specific.

2. **Literature evidence:** Hybrid mechanistic-empirical models of screw feeders (Bascone et al.) show that the effective density within the screw is a function of vertical stress and compressibility, and is modelled with powder-specific parameters (ρ₀, κ) (bascone2020hybridmechanisticempiricalapproach pages 11-14). Hopper/feeder dynamics during transients are powder-dependent: materials with better flowability (high permeability, low cohesion) recover faster from disturbances than poorly flowing materials (li2020predictiveperformanceof pages 114-118). This implies that the settling/draining portion of afterflow is cohesion-dependent.

3. **Dataset A implication:** For calcium lactate (232 mg/rev), a single revolution delivers ~20× the mass of salt at matched tilt. The afterflow *mass* will therefore be far larger. Whether the afterflow *time* is conserved depends on whether the drainage rate scales proportionally — an untested assumption.

**Minimum cross-powder stop-response design:** Run at least 3 powders spanning the feed-factor range (e.g., calcium lactate, salt, sodium alginate) × 2 tilts × 2 speeds, with n ≥ 5 stops per condition. This gives ~60 stop trials, achievable in 2–3 hours. Measure afterflow mass and time to within-2-mg settling separately for each. If τ varies by >2× across powders, it must be a per-powder identified parameter in the observer.

---

## Question 3: Quantized Per-Revolution Discharge — Should It Be Treated as a Discrete Event?

**Yes — the literature strongly supports this.** DEM simulations of single-flight screw conveyors show that powder is transported as a structured heap or bed confined between successive screw flights, with the discharge at the outlet occurring as the flight passes the exit plane (owen2009predictionofscrew pages 1-2, owen2009predictionofscrew pages 2-4). Owen and Cleary's DEM study describes the flow as a "bull dozer pushing a circulating heap" at low inclinations, transitioning to a uniform-depth bed at high angles — in both regimes, the material is bounded by the screw pitch geometry and discharges discretely as each flight clears the outlet (owen2009predictionofscrew pages 4-8, owen2009predictionofscrew pages 10-11).

Dataset B confirms this: ~110 mg slugs at one per revolution, with up to 27 mg in a single 100 ms sample and troughs of zero between. This is the **per-flight discharge** phenomenon, not measurement noise. Treating this as a modelled discrete event and halting in a trough (at a known auger phase) is therefore well-motivated by both theory and observation.

**Stability across fill level:** DEM studies show that average axial speed is "almost invariant to changes in volumetric fill level" (owen2009predictionofscrew pages 10-11), but the pharmaceutical feeder literature shows that higher fill levels increase effective density at the screw entrance through powder densification, increasing the mass carried per flight (bostijn2019amultivariateapproach pages 10-14, fathollahi2024improvingcontinuouslossinweight pages 1-2, li2020predictiveperformanceof pages 66-73). Therefore, per-flight discharge mass is **fill-level-dependent** and must be re-identified or estimated online as fill changes.

**Best measurement approach:** Run a set of single-revolution trials (one full revolution from a known phase, weigh the deposit) at multiple fill levels and tilts. A minimum of 5 revolutions × 3 fill levels × 3 tilts = 45 trials per powder. Phase-locked stopping (halting at a known angular position in a trough) will reduce endpoint variability by up to the full slug amplitude (~110 mg for salt, potentially much larger for high-feed powders).

---

## Question 4: Fill Level Moves Auger and Tap in Opposite Directions — How Should Fill Enter the Model?

The observation that higher fill level **increased** auger feed-per-rev but **decreased** tap yield on salt means a single scalar "fill factor" multiplying both actuators is structurally wrong. This is consistent with the literature: higher fill level increases compressive stress at the screw entrance, densifying powder in the flights and increasing mass throughput per revolution (fathollahi2024improvingcontinuouslossinweight pages 1-2, fathollahi2024improvingcontinuouslossinweight pages 6-7, bascone2020hybridmechanisticempiricalapproach pages 11-14). Meanwhile, a brim-full tube likely packs the lip zone more tightly, reducing the loosely retained inventory that taps can dislodge.

**Model recommendation:** Fill level should enter the observer as **two separate gain multipliers**: one for the auger channel (monotonically increasing with fill, modelled via an effective density ρ_eff(σ_v) relationship as in Bascone et al. (bascone2020hybridmechanisticempiricalapproach pages 11-14)), and one for the tap channel (monotonically decreasing with fill, modelled as the available lip inventory x_lip). This requires the observer to maintain **separate state estimates** for in-tube fill and lip inventory.

**Is cumulative dispensed mass an adequate fill surrogate?** Partially. Cumulative dispensed mass gives a monotone-decreasing estimate of remaining tube fill, which is useful between refills. However, **refill/repack events reset the state discontinuously** — the session-1 vs session-2 tap reversal in Dataset B is direct evidence, and the LIW literature extensively documents refill-induced perturbations that change density profiles, require ~300 seconds to stabilize, and cause feed-factor excursions (fathollahi2024improvingcontinuouslossinweight pages 6-7, fathollahi2024improvingcontinuouslossinweight pages 4-6). Therefore, refill events must be treated as **state resets** in the observer, not smooth continuations. After any refill, a short re-identification sequence (e.g., 3–5 single revolutions + a tap sequence at the operating tilt) should re-calibrate the fill-dependent gains before resuming closed-loop dosing.

---

## Question 5: Do the Stop-Response Protocol Upgrades Still Stand?

**All six protocol upgrades stand; several are elevated in priority by Dataset A.**

**(a) Randomize tilt order and halt masses:** Strengthened. Salt's intra-run drift (feed factor changing 2.7× in 17 min, dose errors trending monotonically) makes fixed-order protocols unreliable. The literature confirms that feeder response changes with operating history and stress state (fathollahi2024improvingcontinuouslossinweight pages 6-7, fathollahi2024improvingcontinuouslossinweight pages 4-6).

**(b) Deconfound actuators (auger-only vs tap-only vs combined):** Elevated to **top priority**. Dataset A shows tap efficacy collapses to <0.25 mg for low-feed powders (below balance resolution), meaning the tap actuator is effectively absent for those materials. The controller's phase-3 stall failure mode for fast powders is directly attributable to assuming tap efficacy at 0° tilt that doesn't exist. Actuator deconfounding should be run per-powder, not only on anchors, because the tap/auger balance varies qualitatively across powders.

**(c) Track fill level every trial:** Now the **single highest-value addition**. Fill dominates both actuators in opposite directions (Dataset B), and the LIW literature identifies fill-induced stress/densification as the primary source of feed-factor drift and refill disturbances (bostijn2019amultivariateapproach pages 10-14, fathollahi2024improvingcontinuouslossinweight pages 1-2, fathollahi2024improvingcontinuouslossinweight pages 2-4, bascone2020hybridmechanisticempiricalapproach pages 11-14). A practical protocol: weigh the loaded tube before and after each block (when within scale capacity), or track cumulative dispensed mass with explicit resets at refills.

**(d) Tilt-only blanks and interlock tilt moves:** Retained at high priority. Dataset B showed a single tilt move released +25.4 mg. Dataset A's strong tilt sensitivity across all powders means tilt changes are themselves dispensing events, powder-specifically.

**(e) Balance step response with known masses:** Retained. Separating instrument settling from powder settling becomes more important when afterflow characteristics vary by powder.

**(f) Test 2–3 more powders before generalizing:** Already accomplished by Dataset A (7 powders). However, metal powders (AlSi10Mg, Si) remain untested, and given the extreme variability observed, they should be added before any τ or control parameter is treated as universal.

**Stationarity/conditioning pre-check:** Given salt's 2.7× intra-run drift, every session should begin with a **stationarity gate**: run 3–5 matched single-revolution trials at a reference tilt/speed; if the per-revolution mass changes by more than ±15% across the set, the tube must be re-conditioned (e.g., 10 conditioning revolutions) and the gate repeated before trusting any subsequent data.

---

## Question 6: Controller Architecture Implications

The frozen salt-tuned controller failed on all 6 non-salt powders via two distinct modes: **cycle-budget exhaustion** (slow powders: bulk phase halts too early on salt's anticipation threshold, fine phase can't close the gap) and **phase-3 stall** (fast powders: fine phase oversteps handover, then taps at 0° where tap quantum collapses). This argues strongly against a single frozen calibration.

The literature on feeder control points toward a hybrid of options (i) and (iii):

**(i) Online feed-factor estimator (favored).** The pharmaceutical micro-feeder literature demonstrates successful feed-forward control using a pre-characterized displacement-feed-factor profile, combined with iterative learning control that updates the profile online — achieving <1.5% deviation from setpoint across diverse materials (fathollahi2021developmentofa pages 4-5, fathollahi2021developmentofa pages 12-13, fathollahi2021developmentofa pages 13-14). This architecture is directly analogous to what the open-source doser needs: a per-powder feed-factor profile (ff as a function of tilt, fill, and speed) used as a feed-forward model, with an online estimator that corrects the profile within-dose based on balance observations.

**(iii) Short per-powder identification burst before each dose.** Given the 3-order-of-magnitude feed-factor range, the controller needs at minimum a rough estimate of the powder's feed factor before attempting a dose. A "probe phase" of 2–3 revolutions at the operating tilt would suffice to set the correct gain scale. This is compatible with the phase-switched architecture: insert a "Phase 0" probe before the bulk dispense phase.

**(ii) Gain-schedule on a measured descriptor** is useful as an initialisation prior (density predicts ff magnitude well (li2020predictiveperformanceof pages 49-53, bostijn2019amultivariateapproach pages 22-26)) but cannot replace direct measurement because it does not predict speed-dependence sign or tilt optima.

**Within-run adaptation vs a-priori calibration:** The LIW literature relies on a-priori calibration (feed-factor profiles) for steady-state operation and switches to volumetric (open-loop) mode during transients like refills (li2020predictiveperformanceof pages 36-40). However, the micro-feeder control literature shows that adding iterative/adaptive correction on top of calibration significantly improves performance, especially for materials with high feed-rate fluctuations (fathollahi2021developmentofa pages 12-13, fathollahi2021developmentofa pages 13-14). Given the observed intra-run drift on salt (2.7× in 17 min), **within-dose online adaptation is essential**, not optional. A recursive least-squares or exponentially weighted moving average estimator on ff, updated every revolution, is the minimum viable approach.

---

## Question 7: Minimum Experimental Program for ±2 mg Across This Powder Range

Given one balance, finite bench time, and n ≈ 1 per powder, the following prioritized program is recommended:

**Stage 1: Stationarity and Fill-Level Calibration (salt only, ~2 hours)**
- Establish a stationarity gate protocol (5 matched revolutions, ±15% criterion).
- Characterize fill-level effect on per-rev mass at 3 fill levels × 2 tilts (30 trials).
- Characterize fill-level effect on tap yield at same 3 fills × 2 tilts (30 trials).
- **Gate:** Demonstrate <20% variation in per-rev mass across consecutive matched trials before proceeding.

**Stage 2: Cross-Powder Stop-Response (3 powders, ~3 hours)**
- Select calcium lactate (high feed), salt (medium), sodium alginate (low feed).
- Auger-only stops: 5 stops × 2 tilts × 2 speeds = 20 per powder.
- Tap-only stops (where tap is resolvable): 5 stops × 2 tilts = 10 per powder.
- **Gate:** Determine whether τ varies >2× across powders. If yes, τ must be per-powder identified.

**Stage 3: Per-Powder Identification Burst Protocol (all 7 powders, ~1 hour each)**
- Per powder: 5 revolutions × 3 tilts × 2 speeds = 30 trials (feed-factor map).
- Per powder: 5 taps × 2 tilts = 10 trials (tap map).
- Per powder: 1 tilt-blank trial.
- **Gate:** Feed-factor map RSD <25% at best operating point; tap yield resolvable from zero at ≥1 tilt.

**Stage 4: Adaptive Controller Development and Single-Powder Validation (salt + 1 fast + 1 slow, ~4 hours)**
- Implement Phase 0 probe (2–3 revolutions) + online ff estimator + phase-locked stopping.
- Validate ±2 mg on n = 10 doses of salt.
- Validate on calcium lactate (fast) and sodium alginate or white rice flour (slow).
- **Gate:** ≥8/10 doses within ±2 mg on salt; ≥6/10 on each non-salt powder.

**Stage 5: Cross-Powder Validation (remaining 4 powders, ~4 hours)**
- Run n = 5 doses per powder with the adaptive controller.
- **Gate:** ≥4/5 within ±2 mg for powders with resolvable feed factors; for brown rice flour (below resolution), document minimum achievable dose and accuracy.

**Stage 6: Metal Powder Extension (AlSi10Mg, Si, ~2 hours each)**
- Run Stage 3 identification + Stage 4 validation on each metal powder.
- **Gate:** Same as Stage 4.

**Total estimated bench time:** ~20–25 hours across ~6 sessions. This is aggressive but achievable if each session is well-planned and the stationarity gate is enforced. The key quantitative gates ensure that data quality is verified before advancing, and that the controller is validated on powders spanning the full 3-order-of-magnitude range before being declared general.

---

## Summary of Revisions to Prior Recommendations

The cross-powder evidence **does not invalidate** the MPC architecture or the core data-collection strategy, but it **materially revises** several assumptions:

1. **Density/FFC indexing** is useful for initialising feed-factor magnitude priors but cannot predict speed-dependence sign, tilt optima, or tap efficacy — each powder needs direct identification.
2. **τ ≈ 1 s** should be treated as powder-specific until cross-powder stop-response data prove otherwise.
3. **Per-revolution discrete discharge** is well-supported by DEM literature and Dataset B; phase-locked stopping should be the default endpoint strategy.
4. **Fill level** must enter the model as separate gain multipliers for auger and tap channels, with refills treated as state resets.
5. **Fill tracking** is now the single highest-priority protocol upgrade.
6. **Online feed-factor estimation** (within-dose adaptation) is essential given the observed variability and drift, not merely desirable.
7. A **stationarity pre-check** should gate every session before data are trusted.
