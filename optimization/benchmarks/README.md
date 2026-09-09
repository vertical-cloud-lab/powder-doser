# Controller benchmark suite (issue #123 / PR #124)

Simulation study comparing the candidate dosing control methods proposed in
PR #124 and the Edison reviews, against the digital twin
(`../simulation/powder_sim.py`, v2 — revised per the Edison benchmark critique
in `../edison/query_out/sim_critique.answer.md`).

**Interpretation caveat (from the critique):** the twin's coefficients are
provisional; results here are a *simulation sensitivity study* — evidence about
controller structure and failure modes, not proof that one controller is
superior on hardware.

**Calibration (2026-08-13).** The three benchmark powders' feed factors and
tilt-gain shapes are now **fitted to real experimental data** pulled from
MongoDB `battery_runs` (the issue #116 / PR #131 characterization battery), via
`../simulation/calibrate_from_mongo.py`. The battery's rotation block measures
grams conveyed per 360° (= one auger rev) at three tilts, which is exactly the
twin's feed factor vs. tilt, so `feed_factor_g_per_rev` (reference condition),
`tilt_g0`, and `tilt_exp` are least-squares/analytic fits rather than guesses;
a cohesion proxy comes from the `lowflow`-flag rate and absolute feed factor.
The fit is written to `../simulation/calibrated_powders.json` and applied by
`benchmark.py` (disable with `--uncalibrated`). Powder→data mapping and the
data-quality caveats it exposes:

| slot | real powder (run) | ref g/rev | tilt g0 / exp | note |
|---|---|---|---|---|
| salt | salt (2026-08-12) | 0.233 | 0.14 / 0.53 | full valid tilt sweep; tilt camera-verified. The 2026-08-06 salt run conveyed ~10× less and was **not** used (suspected un-achieved tilt). |
| lactose | calcium-lactate (2026-08-05) | 0.229 | 0.23 / 0.33 | full valid tilt sweep; moderately free-flowing pharma powder. |
| AlSi10Mg | alsi10mg (2026-08-11) | 0.139 | 0.60 / 0.80 | **tilt-servo fault** invalidated the tilt sweep (plate stuck at 0°); ref feed factor taken from the valid horizontal trials, tilt gain is a free-flowing *prior*, not fit. |

The strongly-cohesive battery powders (brown-rice-flour, sodium-alginate,
carboxymethyl-cellulose) convey ≲0.03 g/rev with `lowflow`-flagged trials — the
data says the current rig effectively **cannot dose them**, so they are catalogued
in `calibrated_powders.json::all_powder_fits` but not used as benchmark slots
(a 2 g dose would be all timeout, giving no controller discrimination).

## Layout

| File | Purpose |
|---|---|
| `rig.py` | Fair sensor/actuator surface: controllers see only the simulated 10 Hz balance stream (`read_frame()` adds the frame tick) and their own commanded state — never lip/screw/true mass. Ground truth is read only for scoring, after the dose ends. |
| `controllers.py` | The five feedback/policy method families: `three_phase` (firmware baseline), `three_phase_vel` (velocity bulk), `rate_pi_kf` (rate-PI + switching-R Kalman filter, filterpy), `dual_ukf` (joint state+feed-factor UKF, filterpy), `mpc` (short-horizon MPC, cvxpy/OSQP). All share the identical tap-until-tolerance endgame. |
| `bangbang.py` | The bang-bang family (PR #124, 2026-08-12 direction): dispense at max rate, hard-stop on a predicted-settled-mass cutoff. `bangbang_naive` (stop at raw crossing — a control), `bangbang_ff` (KF committed-mass predictor), `bangbang_safe` (+ k·σ undershoot bias), `bangbang_trim` (fast bang-bang bulk → seeded rate-PI trickle → tap finish). Uses `MassRateLagKF`, a **3-state (mass, rate, balance-reading) KF that models the balance's 0.7 s integration lag explicitly** — the deferred item below — so the committed-mass predictor works off the lag-free true-mass estimate. |
| `test_bangbang.py` | Behaviour + estimator checks for the bang-bang family (iteration story, convergence/no-hang, overshoot bound, lag-KF estimator-truth advantage over the raw balance and the 2-state KF, safe abort on a blocked cohesive dose). |
| `../simulation/calibrate_from_mongo.py` | Pulls `battery_runs` from MongoDB, fits each powder's reference feed factor + tilt gain from the rotation block, writes `calibrated_powders.json` (+ an offline `battery_snapshot.json` for reproducibility). |
| `bo_tuning.py` | Ax/BoTorch constrained tuning of 7 three-phase policy parameters per powder (strict overshoot as an outcome constraint, rotating scenario seeds, frozen endgame, firmware defaults as safe seed). Writes `results/bo_params.json`. |
| `benchmark.py` | Grid runner: methods × powders × contexts × targets × 30 seeds → `results/results.jsonl`. |
| `summary_md.py` | Descriptive markdown tables → `results/summary.md`. |
| `paired_stats.py` | Ranking evidence: per-cell paired differences + seed-cluster bootstrap CIs → `results/paired_stats.md`. |
| `plots.py` | Figures → `results/fig_*.png`. |

## Reproduce

```bash
pip install numpy scipy filterpy cvxpy ax-platform matplotlib
python bo_tuning.py                    # per-powder constrained BO campaigns
python benchmark.py                    # full grid (feedback + bang-bang + bo)
python summary_md.py && python paired_stats.py && python plots.py
python test_bangbang.py               # bang-bang behaviour/estimator checks
```

## Bang-bang finding (2026-08 iterations)

Prototyped iteratively against the twin per the 2026-08-12 direction. Four
takeaways:

* **The predictor is the whole problem.** A naive max-rate stop-at-crossing
  overshoots ~500–1000 mg on this twin — but ~80 % of that is *balance lag*
  (the 0.7 s integration), not afterflow. The 3-state lag KF removes it, so the
  committed-mass predictor only has to cover the physical afterflow (τ ≈ 0.3 s,
  a bench-calibrated scalar, **not** the plant-coupled `committed_lookahead_s`
  the methods-check flagged as grey-box leakage). This is the deferred 3-state
  KF, now built and validated (`test_bangbang.py` shows it beats the raw
  balance and the 2-state KF on true-mass RMSE during the rising ramp).
* **Pure bang-bang cannot hit ±5 mg.** An irreducible ~±150 mg spread
  (rate-estimate noise × τ + slug quantization) means a single hard stop is a
  bulk primitive, not a finisher — so `bangbang_trim` hands off to a seeded
  rate-PI trickle + tap endgame.
* **It buys speed at the cost of the overshoot constraint.** On the
  **calibrated** twin, paired vs `dual_ukf` (seed-cluster bootstrap, CIs exclude
  0): **−139 s dose time and −54 taps**, with matched median accuracy
  (Δ|error| +0.1 mg, CI spans 0) and +12 pts within-tolerance, but **+20 pts
  strict overshoot**. Arriving fast leaves a charged lip whose stochastic
  tap-slug can cross target — a genuine speed↔overshoot Pareto frontier, with
  bang-bang at the fast end and the KF/UKF feedback methods at the slow/safe end.
* **Overshoot is powder-dependent.** With the real fitted feed factors, median
  accuracy is ~4.5–5 mg across salt / lactose / AlSi10Mg, but overshoot rate
  splits by powder (salt 16 %, AlSi10Mg 19 %, lactose 30 %). One global bang-bang
  parameter set leaves overshoot elevated on the more variable powders — exactly
  the per-powder BO/context layer the roadmap already has (`bo_tuning.py` extends
  to the bang-bang parameter vector).

Objectives/constraints scored per dose: |mass error| after full settle
(tolerance ±5 mg), dose time, tap count (wear), strict overshoot
(true mass > target — the asymmetric hard constraint), and failure status
(stall / timeout / overshoot-abort).

## Methods-check revisions (Edison analysis #2)

Applied from `../edison/query_out/methods_check.answer.md`:

* **A (estimator timing):** the twin exposes a balance frame tick; the KF/UKF
  controllers run predict every control period but only do a measurement
  update on a *fresh* frame (a held sample is not independent evidence).
* **B (MPC):** the committed-mass bound `m + L·r ≤ target − margin` is
  explicitly labeled a cutoff heuristic, made *soft* with an exact L1 slack
  penalty (hard version went infeasible whenever the estimate already
  violated it), and slack activations / failed solves are counted.
* **C (BO):** strict overshoot became an Ax outcome constraint (not a cost
  penalty), scenario seeds rotate per trial (fixed 4-dose CRN caused the
  v1 campaign to overfit badly), failures are penalized explicitly, the tap
  endgame is frozen at firmware defaults for fairness, and the seed trial
  counts toward the budget.
* **D (statistics):** 30 seeds per cell; per-mechanism event RNG streams with
  time-indexed hazard draws so shocks align across controllers sharing a
  seed; `paired_stats.py` reports cell-level paired contrasts with
  seed-cluster bootstrap CIs; pooled tables are labeled descriptive-only.

Deliberately deferred (noted for future work): ~~a 3-state KF that models the
balance lag/bias explicitly~~ (**built** in `bangbang.py::MassRateLagKF`,
2026-08), offset-free/tube MPC with an explicit committed-inventory state,
independent calibration + perturbation of the `L(tilt)` lookahead coefficient
(it currently shares the plant's coefficient family — a grey-box leakage the
review flags when reading MPC/KF cutoff results; the bang-bang predictor
avoids it by using a fixed bench-calibrated τ instead), per-powder BO of the
bang-bang parameter vector, and further estimator truth diagnostics
(innovation whiteness, feed-factor coverage).
