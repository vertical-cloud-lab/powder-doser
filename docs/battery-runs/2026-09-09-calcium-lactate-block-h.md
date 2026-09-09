# 2026-09-09 — Calcium lactate Block H (last of the food-safe campaign)

Small-target dosing (3 × 50 mg + 3 × 200 mg, frozen three-phase controller,
`dose_read_path=bracket`) on calcium lactate, EB B125 fume hood. This is the
Block H counterpart to the powder with the **largest resolved tap quantum**
(20.4 mg at 45°, 2026-08-05) and the second-highest feed factor of the
food-safe set — so the failure mode to watch is *overshoot* on the 50 mg
target (one fine increment ≈ 25 mg ≈ half the target), the same risk xanthan
gum realised at +17.8 mg.

## Launch (2026-09-09, session 20260909-2129)

| | |
|---|---|
| Run dir (on Pi) | `data/battery/20260909T225206Z_calcium-lactate/` |
| Launched | **2026-09-09 22:52:06 UTC (16:52:06 MDT)** |
| Mode | detached in tmux `lactate`; `--unattended`, upload runner-side after collection |
| Blocks | H only (3 × 50 mg + 3 × 200 mg) |
| Batch / operator | `food-safe-2026-08` / swcharles |

### Pre-run gate

- **Balance check** (60 s): 100 % stable frames, jitter 0.023 mg.
- **Pre-flight** (5 × 360° @ 30 RPM, tilt 90°): **feed confirmed,
  1.4430 g / 5 rev = 288.6 mg/rev**, revs 341/291/266/265/281 mg — no
  charging transient, column fully primed. 10 taps → 55.9 mg
  (5.59 mg/tap at 90°). 18 % above the 2026-08-05 pre-flight
  (244.9 mg/rev), consistent with a fresh full load. Outlet aligned —
  full-rate mass reaches the vessel (no #156-style shortfall).
- **Environment: launch was held ~50 min for a baseline drift to decay.**
  First survey (21:49 UTC, ~20 min after the operator was at the bench)
  showed **−9.7 mg/min** with zero shocks and jitter at the display
  floor — a quiet, steady, negative walk, the drying/evaporation
  signature, not drafts and not impulses. Successive 180 s surveys:
  −9.7 → −3.7 → −4.8 → −1.4 → −2.2 → −2.5 mg/min. The fast component
  decayed; a **~2 mg/min floor persisted** through three consecutive
  surveys (180 s error 5.1–7.4 mg vs the ≤5 mg dose gate).
- **Why it launched anyway, documented rather than silent:** calcium
  lactate doses are short (its 1 g Block G doses ran 215–265 s), so a
  ~2 mg/min drift bounds the per-dose bias at roughly **2–8 mg
  apparent under-read** (baseline falls during the dose → controller
  slightly over-delivers; recorded mass under-reports by the same
  amount). The bound is computable per dose from `elapsed_s`. Part of
  the residual may also be the **dispensed calcium lactate itself**
  (a hydrate) losing moisture to the hood draft — 1.5 g of pre-flight
  powder was already in the beaker while the floor persisted — in
  which case no amount of waiting removes it and it is a real property
  of weighing this powder at the mg scale. A post-run no-actuation
  capture is planned to attribute it (slope with ~3 g in the beaker vs
  the ~2 mg/min seen with 1.5 g).

## Results

**Pending collection** — the collecting session fills in the dose table,
per-target means vs the campaign (salt +2.8/+4.2, WRF −4.9/−4.7, xanthan
+2.9/+17.8, CMC −22.6/−2.2, sodium alginate −101.5/−19.6 mg at
200/50 mg), the drift attribution, and QC. Recovery pointers live in
`~/handoff/2026-09-09_calcium-lactate-blockh-RECOVERY.md` on the Pi.
