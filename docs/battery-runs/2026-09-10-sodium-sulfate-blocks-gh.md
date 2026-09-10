# 2026-09-10 — Sodium sulfate blocks G+H (first of the metal/inorganic dose campaign)

Dose blocks G (3 × 1 g) + H (3 × 50 mg + 3 × 200 mg), frozen three-phase
controller, `dose_read_path=bracket`, on sodium sulfate in the EB B125 fume
hood. Adds the dose blocks to the valid 2026-08-20 A–E run, so sodium sulfate
now has the full battery minus only block F — per the operator's 2026-09-10
directive to run the dose blocks *before* granite isolation and record the
environment caveat instead of gating on it.

## Launch (session 20260910-1323)

| | |
|---|---|
| Run dir | `data/battery/20260910T133932Z_sodium-sulfate/` |
| Launched | **2026-09-10 13:39:32 UTC (07:39:32 MDT)** |
| Ended | **2026-09-10 13:47:41 UTC (07:47:41 MDT)** — 8 min 09 s (G 5:34, H 2:31) |
| Mode | detached in tmux `sulfate`; `--unattended`; upload runner-side after collection |
| Blocks | `GH` (9 doses) |
| Batch / operator | `inorganic-2026-08` / swcharles |
| MongoDB | `_id 6aa2b56a4c21fd11a9b89280`, QC promoted `unreviewed` → `ok`, `valid = true` |

### Pre-run gate

- **Environment survey** (180 s, runner-side): 96 % stable frames, jitter
  0.020 mg (display floor), **0 shock events**, drift **−1.6 mg/min** →
  180 s error 5.4–6.1 mg, *marginally over* the ±5 mg dose gate. Launched
  per the operator directive, with the bias bound recorded: baseline falling
  at ≤1.6 mg/min under-reads delivered mass by ≤1.6 mg/min × elapsed, so the
  controller over-delivers by the same bound (true error shifts *positive*).
  Worst case is the 175 s G dose: ≤4.7 mg. No dose classification is
  sensitive to the bound. The drift signature matches the freshly-handled
  vessel/enclosure drying seen on 2026-09-09 (calcium lactate), not drafts.
- **Pre-flight** (5 × 360° @ 30 RPM, tilt 90°): **feed confirmed,
  2.3114 g / 5 rev = 462.28 mg/rev**, per-rev 542/473/442/433/422 mg — no
  charging transient, column fully primed. 10 taps → 96.8 mg (9.68 mg/tap
  at 90°). 90 % above the 2026-08-20 pre-battery block C figure
  (243.6 mg/rev), consistent with a fresh full load; **the
  fastest-feeding column of the campaign so far.**
- Device-side environment counters for the run itself came back clean:
  0 shock events, 0.0000 g shock mass, 0 unsettled brackets.

## Results

| # | block | target | delivered | error | status | time | auger rev | taps | cycles |
|---|---|---|---|---|---|---|---|---|---|
| 0 | G | 1.000 g | 0.9971 g | **−2.9 mg** | **ok** | 86 s | 3.38 | 28 | bulk:10 fine:5 tap:14 |
| 1 | G | 1.000 g | 0.9953 g | **−4.7 mg** | **ok** | 73 s | 3.50 | 18 | bulk:8 fine:6 tap:9 |
| 2 | G | 1.000 g | 0.9951 g | **−4.9 mg** | **ok** | 175 s | 3.25 | 86 | bulk:8 fine:4 tap:43 |
| 0 | H | 50 mg | 67.7 mg | +17.7 mg | overshoot | 15 s | 0.25 | 0 | fine:2 |
| 1 | H | 50 mg | 72.1 mg | +22.1 mg | overshoot | 10 s | 0.13 | 0 | fine:1 |
| 2 | H | 50 mg | 96.9 mg | +46.9 mg | overshoot | 10 s | 0.13 | 0 | fine:1 |
| 3 | H | 200 mg | 206.6 mg | +6.6 mg | overshoot | 30 s | 0.63 | 0 | fine:5 |
| 4 | H | 200 mg | 230.2 mg | +30.2 mg | overshoot | 20 s | 0.38 | 0 | fine:3 |
| 5 | H | 200 mg | 195.5 mg | **−4.5 mg** | **ok** | 64 s | 0.63 | 20 | fine:5 tap:10 |

Per-target mean error: **1 g −4.2 mg (3/3 ok) · 200 mg +10.8 mg (1/3 ok) ·
50 mg +28.9 mg (0/3, all overshoot)**. Total dispensed 3.86 g
(≈6.26 g in the vessel including pre-flight).

### Block G: the first non-salt powder to pass — 3/3 inside ±5 mg

Every prior non-salt powder failed Block G (−19.6 to −292 mg mean error).
Sodium sulfate, under the identical frozen salt-tuned parameters, went
**three for three**: −2.9 / −4.7 / −4.9 mg, matching the 2026-08-12 salt
control (−4.4 / −3.2 / −4.7 mg) almost exactly. That refines the
"dose accuracy tracks proximity to salt" story: sodium sulfate conveys
**2× salt's feed factor**, so proximity in *feed factor* is not the
mechanism. What it shares with salt is a **small, reliable tap quantum at
tilt 0°** — dose 2 closed its last milligrams with 43 tap cycles, and H
dose 5's 10 tap cycles (20 taps) moved 17.2 mg ≈ 0.86 mg/tap, steady.
Phase 3 converging instead of stalling is what separates the two Block G
outcomes across the dataset, and this run is the second data point on the
convergent side.

### Block H: the quantum limit, at its sharpest

At 462 mg/rev one 45° fine increment carries ≈58 mg — **more than the
entire 50 mg target** — so every 50 mg dose was decided by its first one
or two fine cycles (0 taps ever fired) and overshot by +18 to +47 mg.
The 200 mg doses sit at the boundary: two overshot in 3–5 fine cycles,
one landed −4.5 mg when fine happened to stop 22 mg short and the tap
phase closed cleanly. This is the calcium-lactate mechanism
(lip-state-decided, overshoot-unrecoverable) amplified by the highest
feed factor of the campaign.

Mean |error| **rises as the target shrinks** — 4.2 → 13.8 → 28.9 mg at
1000 → 200 → 50 mg — the strongest quantum-limited example in the
campaign, the opposite scaling from sodium alginate (budget-limited,
error ∝ target). One controller, two regimes, split by feed factor:
exactly the #97 headline, now anchored at both extremes.

### Environment

Nothing in this run needed the artifact machinery: 0 shocks, 0 unsettled
brackets, 0 retries. The −1.6 mg/min preroll drift bounds per-dose bias
at ≤4.7 mg (worst dose) with a known sign (true errors shift positive);
no classification changes anywhere in the table. The 50 mg overshoots are
controller quanta, not environment.

## Follow-ups

- **Empty the vessel before the next powder** — ≈6.26 g of sodium sulfate.
- **Barium chloride is next** (operator): same G+H pattern on top of its
  2026-08-21 A–E run. Its feed factor is far lower, so expect the
  budget-limited regime and a much longer run — plan the detached launch
  around the ~900 s per-dose timeout.
- Block F still impossible (DRV2605L absent); granite isolation still
  pending — it remains the fix for multi-minute-dose environmental error,
  even though today's room happened to be clean.
