# Kalman-filter bang-bang stop accuracy — salt — 2026-08-17

First **hardware** test of the 3-state balance-lag Kalman filter
(`MassRateLagKF`, prototyped in simulation on the PR #124 branch,
`optimization/benchmarks/bangbang.py`) driving a bang-bang stop rule:
spin the auger at one constant rate, hard-stop the instant the *predicted
settled* cup mass reaches target.

Firmware: `hardware/test-module/firmware/kf_bangbang.py` (runs on the Pico
via `mpremote run`, RAM only; the KF is re-implemented dependency-free —
no numpy/filterpy on a Pico). Analysis: `scripts/analyze_kf_bangbang.py`.

## Estimator constants and where they came from

| constant | value | source |
|---|---|---|
| `TAU_BAL_S` | **0.16 s** | measured instrument lag, 2026-08-14 known-mass drop tests (`data/balance-step/2026-08-14/`) — the twin had assumed 0.7 s |
| `TAU_AFTER_S` | 0.25 s | physical afterflow lookahead, calibrated offline by replaying this filter over the 2026-08-12 afterflow battery (`--replay`) |
| `Q_ACC_SD` | 0.25 g/s² | same offline replay (rate process noise) |
| `R_SD` | 0.4 mg quiet / 2.0 mg actuating | balance-step noise floor + in-dispense scatter |
| `K_SIGMA` | 2.0 | `kfsafe` undershoot bias, in predictor sigmas |

Offline replay result (auger-only trials, n=12): predictor error
**+6 ± 19 mg** with τ_bal = 0.16 s, versus **+43 ± 34 mg** with the twin's
0.7 s and **−27 mg** for the raw balance reading.

## Protocol

Auger-only (no taps), tilt 55° plate, 55 rpm (two trials at 90 rpm),
poll ~10.5 Hz. Per trial: settled baseline → 1.5 s pre-roll → spin at
constant rpm → hard stop (`halt_and_set_position`, no decel ramp) the
first frame the variant's stop rule fires → de-energise → 6 s settle
stream → settled weigh → 3 s → confirmation weigh. No hardware tare (the
A&D `Z` is unreliable with a loaded pan); every trial works in
differences from its own settled baseline.

Stop rules (variants):

- `naive` — raw reading ≥ target (control)
- `kflag` — KF lag-free mass `m̂` ≥ target
- `kf` — `m̂ + r̂·τ_after` ≥ target (BangBangFF)
- `kfsafe` — `m̂ + r̂·τ_after + 2σ` ≥ target (BangBangSafe, undershoot-biased)

24 trials in two passes, interleaved so hopper drawdown cannot alias onto
variant or target. Targets 0.10 / 0.20 / 0.50 / 1.00 / 2.00 g.
Total dispensed 19.29 g; cup ended at 20.19 g absolute.

## Headline results

| variant | n | mean error | sd | max abs |
|---|---|---|---|---|
| `kf` | 16 | **+15.1 mg** | 29.3 | 62.6 |
| `kf` (55 rpm only) | 14 | **+11.4 mg** | 28.5 | 62.6 |
| `kflag` | 2 | +35.2 | 30.0 | 65.2 |
| `kfsafe` | 3 | −47.7 (never overshot) | 34.1 | 91.0 |
| `naive` | 3 | +108.6 | 9.2 | 116.2 |

`kf` by target: 0.10 g +27.9 ± 23.2 · 0.20 g +9.7 ± 22.0 ·
0.50 g +36.4 ± 28.3 · 1.00 g +15.4 ± 26.1 · 2.00 g −9.9 ± 24.3 mg.
The error is essentially **target-independent in absolute mg**, so the
relative error runs ~1.5 % at 2 g and 5–50 % at 0.1 g.

Afterflow actually cancelled: 70.7 ± 31.1 mg per trial (flow at halt
0.135 g/s mean) — implied lumped time constant ≈ 0.52 s, consistent with
the 0.56 s measured auger-only on 2026-08-12.

## Files

- `kf_bangbang_salt.log`, `kf_bangbang_salt_p2.log` — raw CSV telemetry
  (M/E/D/P/T rows; D = per-frame balance + KF state incl. unstable frames)
- `trials.csv` — 24 trials, one row each
- `samples.csv` — 2 902 per-frame samples with the live KF state
- `kf_bangbang_accuracy.png` — error vs target by variant; relative
  accuracy; predictor calibration at the halt
- `kf_bangbang_traces.png` — representative traces: raw balance vs `m̂` vs
  predicted settled, with the halt marked

## Caveats

- Hopper fill was **not** weighed before the session (the tube exceeds the
  balance's 102 g range). Flow held at ~0.13 g/s throughout, well above
  the 0.04 g/s of the depleted 2026-08-12 tube, so a refill is likely but
  unconfirmed; the salt ledger records this.
- n = 2–5 per target for `kf` and only 2–3 per non-`kf` variant: the
  variant contrast is large (≈ 100 mg) relative to the scatter, but the
  per-target trend is not resolvable at this n.
- Auger-only. Tap-while-rotating needs a larger `TAU_AFTER_S` (~0.45 s per
  the same offline replay on the C6 trials).
