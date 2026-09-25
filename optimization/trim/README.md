# Trim-dispensing method study (issue #153)

A self-contained comparison of ways to close the last few hundred milligrams of
a dose after the bang-bang bulk phase halts. The argument and the conclusions
live in [`docs/trim-dispensing.md`](../../docs/trim-dispensing.md); this file
covers how to run the code and what each module does.

## Running it

Only `numpy` is required to run the study; `matplotlib` is needed for figures.
There is no `filterpy` dependency — the Kalman filter is written out directly.

```bash
cd optimization/trim
python run_study.py all       # ~5 min, writes results/summary.md + JSONL
python plots.py               # figures into results/
python -m unittest test_trim  # 25 tests, ~3 s
```

Individual studies: `regime`, `main`, `tau`, `cv`, `alpha`, `quantum`. The
`regime` and `quantum` studies are pure arithmetic and run instantly.

## Modules

| file | what it is |
|---|---|
| `trim_sim.py` | The trim-regime plant: screw → lip → free fall → lagged, quantized balance. The lip discharges as a **marked point process**, which is what makes this regime different from the bulk phase. Calibrated against the PR #124 bench numbers. |
| `estimators.py` | Both worldviews side by side. `MassRateLagKF` is the 3-state `[mass, rate, balance]` filter the deployed controller uses. `YieldModel` never estimates a rate; it answers "what is the largest command whose overshoot probability is under α?" via an exact compound-Poisson tail. |
| `trim_methods.py` | Six trim methods, from "no trim at all" to the chance-constrained proposal. |
| `metrics.py` | The one-sided scorecard the 2026-08-22 Edison review asked for, plus paired cluster-bootstrap and exact McNemar comparisons. |
| `run_study.py` | Monte Carlo driver. All methods share seeds, so every comparison is paired. |
| `plots.py` | Figures, read back from the JSONL dumps so they cannot drift from the tables. |

## Why a separate simulator

This does **not** use `optimization/simulation/powder_sim.py`. Two reasons.

The first is scientific. The 08-22 Edison spot-check found that the twin uses
`BAL_TAU_S = 0.7 s` in *both* the plant and the filter, so it hands the
estimator a perfectly specified sensor — and bench drop tests suggest the real
HR-100A may be nearer 0.16 s, a mismatch worth 22.7 mg at the trim flow rate.
Any comparison that inherits that coupling cannot say anything about robustness.
Here the plant's `tau_bal_s` and the controller's `tau_bal_belief_s` are
separate arguments, and the mismatch is a first-class sweep axis.

The second is practical: `optimization/` exists only on the PR #124 branch, so a
study that imported it could not run on `main`. This module has no dependency on
that branch and will merge cleanly whichever lands first.

## Calibration

Every constant traces to a measurement. From the Edison spot-check and
[`diag_trickle_stages.txt`](https://github.com/vertical-cloud-lab/powder-doser/blob/9965710/optimization/benchmarks/results/diag_trickle_stages.txt):

| quantity | bench value | model reproduces |
|---|---|---|
| mean slug mass (salt, 45° steps, n=64) | 6.4 mg | 6.3 mg |
| slug mass sd | 15.9 mg | 11.2 mg |
| post-halt lip drain | +26.0 mg (p95 +52.4) | +25.6 mg (p95 +69.2) |
| feed factor at trim tilt | 0.113 g/rev median | 0.113 g/rev |
| balance readability / noise at rest / noise actuating | 0.1 / 0.5 / 8 mg | same |

Two of these deserve a caveat. The realized slug sd (11.2 mg) lands below the
15.9 mg bench figure because the model conserves mass — a release cannot exceed
what is on the lip. The review noted that the 15.9 mg was measured on a depleted
tube and includes reading noise, so the true mark dispersion is somewhat
smaller; `slug_cv` is swept from 1.0 to 3.2 rather than trusted as a point
value, and the conclusions do not move across that range. The drain p95 is
heavier than the bench figure, which is the conservative direction.

## Reading the results

`results/summary.md` holds all six studies. The scorecard is one-sided
throughout: `P(E>0)` is the hard-constraint violation rate, `E[max(E,0)]` the
expected positive excess, and `P(-5..0 mg)` the genuinely acceptable band. A
`stopped short` outcome is *not* a failure — it means the controller correctly
ran out of actions whose quantum fits the remaining budget — and it is counted
separately from `stall/timeout`.

## Limitations

These are simulation numbers from a model calibrated against a handful of bench
measurements, several of which the Edison review flagged as provisional. They
support statements about the *structure* of the problem — that the trim regime
is granular, that a rate lookahead is smaller than its own shot noise there,
that measuring at rest removes the `tau_bal` sensitivity — and they are not
evidence about achievable hardware performance. The bench measurements needed
to make them so are listed at the end of
[`docs/trim-dispensing.md`](../../docs/trim-dispensing.md).
