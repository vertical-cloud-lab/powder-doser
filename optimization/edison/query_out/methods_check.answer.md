## Verdict

The implementation is useful as a **simulation sensitivity study**, but it is not yet sound enough for a definitive ranking claim. The strongest supported result is that, in this twin, the three feedback controllers improve typical accuracy and completion behavior relative to the firmware-default three-phase policy. The data do **not** support claiming that the unscented Kalman filter (UKF) or model predictive control (MPC) is superior to rate proportional-integral control with a Kalman filter (rate-PI-KF), or that MPC enforces no overshoot.

The supplied `summary.md` has only aggregate tables. The raw `results.jsonl` and `bo_params.json` are absent, so I cannot verify the paired statistics, individual grid cells, Bayesian optimization parameters, failures, or percentile calculations. The source files parse successfully.

## A. Estimators

### Switching-R KF

`controllers.py:177-210`, `MassRateKF.update()` is mechanically consistent in several respects:

- `R` is selected from the controller-visible actuation state (`rig.actuating()`), not hidden plant state.
- The command used in the predict step is the command applied during the preceding wait interval.
- `B = [0, a·ff]ᵀ` is consistent with the code’s forward-Euler state model: mass advances using the old rate, and the input changes the next rate.

But this is only an approximate estimator, not a correctly specified filter for this observation process:

1. **The measurement model is the main problem.** The filter assumes `z = mass + white noise`, while `powder_sim.py:550-589` generates a 0.7 s low-pass balance response, session bias, random-walk drift, colored actuation vibration, a tonal component, quantization, and sample-and-hold. Changing only `R` cannot represent lag, bias, or serially correlated errors.
2. `Q_discrete_white_noise()` is derived for a constant-velocity model, but the implemented transition includes first-order rate decay and a control input. This is not fatal, but `Q` should be constructed or estimated for that model.
3. `B[0]=0` introduces a one-step input-to-mass delay. It matches forward Euler, but an exact zero-order-hold discretization would put a nonzero command term into the mass row. This matters at 0.2-0.25 s control periods.
4. Hard-clamping the posterior rate to zero changes the state without updating its covariance. A constrained filter, transformed rate state, or covariance-aware projection would be cleaner.

**Specific change:** replace `MassRateKF` with at least a 3-state model such as `[true/settled mass, rate, balance state]`, with the balance-state transition using the known integration time. Add a slowly varying balance-bias state if the controller does not tare. Derive `F`, `B`, and `Q` from the same continuous model. Log innovations and report normalized innovation squared and residual autocorrelation by actuation regime.

### Sample-and-hold timing

At the current periods, duplicate held frames are probably not the dominant error: 0.2 and 0.25 s are both slower than the 0.1 s balance clock, so each loop normally sees a newer frame. You are, however, discarding intervening 10 Hz frames, and the interface cannot detect duplicated or delayed frames if timing later changes.

**Specific change:** have `PowderDoserSim._sample_hold` include a monotonically increasing balance tick or acquisition timestamp; expose it through `Rig.read()`. Run `predict()` for elapsed time, but call `update()` only when the tick changes. Prefer processing every 10 Hz balance frame. Do not repeatedly update on an unchanged held value, because that falsely treats one observation as independent replicated evidence.

### UKF

`controllers.py:282-335` is an augmented-state UKF, not a “dual UKF” in the usual sense. Its process/measurement split is syntactically sound and the previous command is used during prediction. The larger issue is identifiability: feed factor is inferred from one lagged mass channel while unmodelled screw transport, lip storage, avalanches, blockage, and balance lag also affect mass increments. The UKF can therefore attribute transport delay or lip release to feed-factor changes.

The `max()` operations inside `fx`, followed by clipping `ff` after update without covariance adjustment, also distort the sigma-point moments. Use a transformed parameter such as `log(ff)` and avoid clipping sigma points.

Before calling this joint parameter estimation, show simulation truth diagnostics unavailable to the controller: feed-factor bias, interval coverage, and correlation between feed-factor error and hidden lip/screw inventory. These are estimator-validation outputs, not controller inputs.

## B. MPC

### Committed-mass constraint

`controllers.py:380`, `m + Lr <= target - margin`, is a reasonable **engineering heuristic** for delayed committed material. It is not a hard no-overshoot guarantee for this plant. The plant has three screw cells, a nonlinear lip reservoir, marked avalanches, free fall, blockage, and a lagged balance; different hidden inventories can produce the same `(m,r)`.

The lookahead also shares the plant’s `1.2·steepness²` coefficient family (`controllers.py:42-49` versus `powder_sim.py:441-447`). That is grey-box model leakage and likely makes the heuristic look better than it would under independently identified parameters. Even with this advantage, pooled MPC overshoot is 8%, versus 2% for the baseline.

### Future-input budget

`controllers.py:382` correctly constrains cumulative **planned new screw input** under its assumed feed factor. It does not bound total committed mass because it omits explicit screw-cell and lip inventories. `ff_hi = 1.3·ff` is an arbitrary multiplier, not a calibrated upper confidence bound, and it may fail after regime changes. Calling this an “arching guard” is too strong: arching reduces immediate pickup, but material already in the screw can still emerge, and clearance changes the dynamics.

There is also a performance issue: hard constraints can make the quadratic program infeasible whenever the estimated current committed mass already violates the bound. The exception handler then silently sets input to zero (`controllers.py:431-438`), making solver/model failures indistinguishable from deliberate control.

### Better practice

For this benchmark, I would prioritize:

1. **Soft committed-mass constraint with an exact/L1 slack penalty**, logging every slack use and infeasible solve. Keep actuator and slew bounds hard.
2. **Offset-free MPC** with a disturbance/feed-bias state. This addresses persistent feed-factor mismatch more directly than the present EWMA.
3. Only after calibration, consider stochastic or tube MPC using empirically estimated uncertainty bounds for feed factor, delay, and retained inventory. A tube based on arbitrary twin coefficients would add complexity without adding validity.

Add an explicit low-order committed-inventory state if MPC is meant to claim physical constraint handling. Otherwise label `m+Lr` as a cutoff heuristic.

## C. Bayesian optimization

The current optimization is not SafeOpt-like in a technical sense. A safe seed does not prevent Ax from proposing unsafe later trials. In addition:

- `for _ in range(trials)` runs 24 generated trials **in addition to** the attached seed, so the default campaign is 25 evaluations per powder, not 24 (`bo_tuning.py:79-86`).
- Every candidate is evaluated on only four fixed dose realizations: two seeds × two targets (`bo_tuning.py:66-69`). Fixed common random numbers reduce noise but create severe overfitting to four trajectories across nine parameters.
- The penalty is activated only above +5 mg (`bo_tuning.py:61`), while the benchmark defines overshoot strictly as true mass greater than target. The optimization and benchmark constraints therefore disagree.
- Exceptions are swallowed without an explicit failure penalty.
- The scalar weights have not been justified by engineering exchange rates.

A scalarized objective is defensible if the tradeoffs are pre-specified, but a penalty is not a substitute for a hard safety constraint. At this budget, I would use constrained single-objective BO rather than qNEHVI: optimize the pre-specified accuracy/time/wear cost, with a separate overshoot outcome constraint. Because per-dose zero overshoot cannot be established from four stochastic runs, model a conservative violation metric such as the upper confidence bound on overshoot probability, or the worst positive signed error across replicate scenarios.

**Specific changes in `bo_tuning.py`:**

- Make `trials-1` generated proposals after the seed if 24 is the total budget.
- Return separate metrics for cost and overshoot; make overshoot an Ax outcome constraint using the same strict definition as `benchmark.py`.
- Use more independent scenario seeds and rotate or resample them during optimization; reserve untouched nominal validation seeds as well as the stressed contexts.
- Penalize timeout, stall, and exception explicitly.

Per-powder tuning followed by stressed-context holdout is a reasonable robustness test. It is not a full generalization test because the same two target values and the same simulator family remain fixed. Also report untouched nominal-seed validation, so degradation can be separated into stochastic overfitting versus context shift.

## D. Benchmark statistics

### What should be reported

Do not rank methods using the pooled medians in `summary.md`. Pooling mixes powders, contexts, targets, and many 300 s censored failures. It hides interactions visible in the supplied tables.

For each controller pair:

1. Form paired differences within `(powder, context, target, seed)` for absolute error, time, and taps.
2. Report each of the 12 cell-specific median or mean paired differences with a confidence interval.
3. For one study-level estimand, give every design cell equal weight and bootstrap entire **seed clusters**, preserving all methods and cells for a sampled seed. The same seed is reused across powders, contexts, and targets, so treating 120 rows per method as independent is incorrect.
4. For binary outcomes, report paired discordant counts and a paired risk difference. Use an exact McNemar test only as a secondary test. Apply a multiplicity correction if many controller pairs are tested.
5. Report failures and strict overshoots separately. Time-to-completion is right-censored near 300 s; a pooled median time of 300 s is not an ordinary continuous outcome.

Ten seed clusters give limited precision. Bootstrap intervals will be coarse, and asymptotic cluster-robust intervals are unreliable. I would increase to at least 30 independent seeds per design cell before ranking closely performing methods, with the final number justified by a simulation-based precision or power calculation.

### Common random numbers

Matching seed labels does not fully align stochastic events. `event_rng` is shared by blockage transitions, lip avalanches, free-fall jitter, and taps. Controllers consume these draws conditionally and at different times, so one method’s first tap can receive a random draw used for another method’s avalanche. This weakens and can unpredictably alter the pairing.

**Specific change in `PowderDoserSim.__init__`:** create separate streams for blockage, avalanche occurrence/mark, free fall, and taps. For time-driven hazards, use time-indexed or counter-based random variates so exogenous shocks align by simulated time rather than by call order. Keep run-level latent variables shared across methods. Then measure whether pairing actually reduces the variance of controller contrasts.

### Problems with the present summary

The marginal counts are arithmetically consistent, but row-level correctness cannot be checked without the JSONL. Specific concerns are:

- `benchmark.summarize()` uses an order-statistic index for p95 rather than a documented quantile estimator (`benchmark.py:136-137`).
- `not-ok` means controller status not beginning with `ok`; it is not the same as outside tolerance or failed true-mass performance.
- Crashes, timeouts, and stalls remain in ordinary medians without a declared estimand.
- Dose time excludes the extra 1 s scoring settle in `Rig.true_dispensed_g()`, although post-settle mass includes physical evolution during that second. Define a common completion/settling protocol and either include it in time or state explicitly that time ends at controller declaration.

## E. Fairness

Remaining method-class advantages include:

- **Shared `tap_finish` dominates outcomes.** This is fair if the question is only “which upstream feeder reaches a common endgame best,” but it masks end-to-end controller differences. The very high tap counts and long durations show that the common endgame is often the benchmark’s dominant subsystem.
- **BO is not using exactly the same endgame:** it can tune `tap_tilt` and `taps_per_cycle`, while advanced controllers use the fixed defaults. Either freeze the endgame for every controller or treat full-policy tuning as a separate comparison.
- **Grey-box coefficient leakage:** `committed_lookahead_s()` reuses the plant’s 1.2 steepness coefficient family. Estimate lookahead from a separate calibration set, then perturb it substantially in validation.
- **MPC structural matching:** its mass integrator and first-order rate response resemble the controller-side abstraction used to design the twin, although the actual plant is much richer. Include structural mismatch scenarios, such as different transport revolutions, balance time constant, lip law, and feed dynamics.
- **No controller tares the biased balance.** The simulator adds ~2 mg session bias. If hardware operation includes a tare, enforce the same initialization protocol for all methods.

Run two benchmark layers: a frozen common endgame to isolate upstream control, and an end-to-end policy benchmark where every family may optimize its own endgame under the same tuning budget.

## F. Conclusions supported by `summary.md`

Supported descriptively, conditional on this twin:

- Rate-PI-KF substantially improves on the baseline in pooled typical performance: median absolute error 4.62 versus 8.44 mg, tolerance success 58% versus 27%, median time 147 versus 300 s, and 16 versus 70 non-`ok` statuses.
- The UKF has the best pooled tail error among the tested methods: p95 8.4 mg versus 48.5 for rate-PI-KF and 119.1 for baseline. It is slower than rate-PI-KF and has more strict overshoots, 5% versus 2%.
- MPC is not supported as the best controller. It has 4.81 mg median error, 52% tolerance success, 228 s median time, 92 median taps, and 8% overshoot. Its supposed no-overshoot mechanism did not enforce the benchmark constraint.
- BO-tuned three-phase is worse than the firmware defaults on most pooled measures: median error 25.60 versus 8.44 mg, tolerance success 18% versus 27%, and 89 versus 70 non-`ok` statuses. This indicates a failed tuning/validation setup, not evidence that BO is intrinsically poor.

Not supported:

- A definitive ordering among rate-PI-KF, UKF, and MPC.
- Any hardware-performance claim.
- Any claim that MPC ensures no overshoot.
- Any claim of statistical superiority based on pooled medians.
- Any safety claim for the BO campaign.

## Highest-priority changes before reporting rankings

1. **Fix observation timing and estimator validation:** expose balance tick timestamps in `Rig.read()`, update only on new frames, augment the estimator with balance lag/bias, and report innovation and state-truth diagnostics.
2. **Regenerate and analyze row-level results with a valid paired design:** split event RNGs by mechanism, use at least ~30 independent seed clusters, report cell-specific paired contrasts and cluster-bootstrap intervals, and treat timeout/stall as separate outcomes.
3. **Remove tuning/model leakage:** make strict overshoot an explicit BO constraint, use independent optimization and validation seeds, freeze or separately benchmark the endgame, and calibrate/perturb `L` independently of the plant coefficient.

The present study can be reported now only as: **feedback control improved performance over firmware defaults in this provisional twin; relative rankings among feedback architectures remain unresolved.**

### Discretionary analytical decisions

- Treated the 12 powder × context × target combinations as equally weighted design cells rather than interpreting the pooled median as the primary estimand.
- Recommended seed-cluster bootstrap intervals because seed identifiers are reused across cells and only ten independent seed labels are present.
- Recommended constrained single-objective BO rather than multi-objective qNEHVI at this small evaluation budget.
- Prioritized soft-constraint, offset-free MPC before tube MPC because uncertainty sets have not yet been calibrated.
- Interpreted `m + Lr` as a cutoff heuristic rather than a physical safety guarantee.