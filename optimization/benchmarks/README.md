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
| `controllers.py` | The five method families: `three_phase` (firmware baseline), `three_phase_vel` (velocity bulk), `rate_pi_kf` (rate-PI + switching-R Kalman filter, filterpy), `dual_ukf` (joint state+feed-factor UKF, filterpy), `mpc` (short-horizon MPC, cvxpy/OSQP). All share the identical tap-until-tolerance endgame. |
| `bo_tuning.py` | Ax/BoTorch constrained tuning of 7 three-phase policy parameters per powder (strict overshoot as an outcome constraint, rotating scenario seeds, frozen endgame, firmware defaults as safe seed). Writes `results/bo_params.json`. |
| `benchmark.py` | Grid runner: methods × powders × contexts × targets × 30 seeds → `results/results.jsonl`. |
| `summary_md.py` | Descriptive markdown tables → `results/summary.md`. |
| `paired_stats.py` | Ranking evidence: per-cell paired differences + seed-cluster bootstrap CIs → `results/paired_stats.md`. |
| `plots.py` | Figures → `results/fig_*.png`. |

## Reproduce

```bash
pip install numpy scipy filterpy cvxpy ax-platform matplotlib
python bo_tuning.py                    # per-powder constrained BO campaigns
python benchmark.py                    # full grid (adds bo_three_phase)
python summary_md.py && python paired_stats.py && python plots.py
```

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

Deliberately deferred (noted for future work): a 3-state KF that models the
balance lag/bias explicitly, offset-free/tube MPC with an explicit committed-
inventory state, independent calibration + perturbation of the `L(tilt)`
lookahead coefficient (it currently shares the plant's coefficient family —
a grey-box leakage the review flags when reading MPC/KF cutoff results), and
estimator truth diagnostics (innovation whiteness, feed-factor coverage).
