# Controller benchmark suite (issue #123 / PR #124)

Simulation study comparing the candidate dosing control methods proposed in
PR #124 and the Edison reviews, against the digital twin
(`../simulation/powder_sim.py`, v2 — revised per the Edison benchmark critique
in `../edison/query_out/sim_critique.answer.md`).

**Interpretation caveat (from the critique):** the twin's coefficients are
provisional until the bench calibration experiments are run, so results here
are a *simulation sensitivity study* — evidence about controller structure and
failure modes, not proof that one controller is superior on hardware.

## Layout

| File | Purpose |
|---|---|
| `rig.py` | Fair sensor/actuator surface: controllers see only the simulated 10 Hz balance stream (`read_frame()` adds the frame tick) and their own commanded state — never lip/screw/true mass. Ground truth is read only for scoring, after the dose ends. |
| `controllers.py` | The five feedback/policy method families: `three_phase` (firmware baseline), `three_phase_vel` (velocity bulk), `rate_pi_kf` (rate-PI + switching-R Kalman filter, filterpy), `dual_ukf` (joint state+feed-factor UKF, filterpy), `mpc` (short-horizon MPC, cvxpy/OSQP). All share the identical tap-until-tolerance endgame. |
| `bangbang.py` | The bang-bang family (PR #124, 2026-08-12 direction): dispense at max rate, hard-stop on a predicted-settled-mass cutoff. `bangbang_naive` (stop at raw crossing — a control), `bangbang_ff` (KF committed-mass predictor), `bangbang_safe` (+ k·σ undershoot bias), `bangbang_trim` (fast bang-bang bulk → seeded rate-PI trickle → tap finish). Uses `MassRateLagKF`, a **3-state (mass, rate, balance-reading) KF that models the balance's 0.7 s integration lag explicitly** — the deferred item below — so the committed-mass predictor works off the lag-free true-mass estimate. |
| `test_bangbang.py` | Behaviour + estimator checks for the bang-bang family (iteration story, convergence/no-hang, overshoot bound, lag-KF estimator-truth advantage over the raw balance and the 2-state KF, safe abort on a blocked cohesive dose). |
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
* **It buys speed at the cost of the overshoot constraint.** Paired vs
  `dual_ukf` (seed-cluster bootstrap, CIs exclude 0): **−98 s dose time and
  −38 taps**, but **+37 pts strict overshoot** and −14 pts within-tolerance.
  Arriving fast leaves a charged lip whose stochastic tap-slug can cross target
  — a genuine speed↔overshoot Pareto frontier, with bang-bang at the fast end
  and the KF/UKF feedback methods at the slow/safe end.
* **One global parameter set can't serve all powders.** salt and lactose reach
  ~5 mg *median* accuracy (though overshoot is still elevated, ~33–38 %); a fast
  free-flowing powder (AlSi10Mg, "flows like a liquid" per the #116
  observations) is much worse — median 22 mg, 64 % overshoot on small targets.
  Closing this is exactly the per-powder BO/context layer the roadmap already
  has (`bo_tuning.py` extends to the bang-bang parameter vector).

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
