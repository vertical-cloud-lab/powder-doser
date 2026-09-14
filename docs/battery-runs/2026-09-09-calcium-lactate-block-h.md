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

## Results (collected the same session)

Ran **22:52:06 → ~23:24 UTC device-side**; the capture's own window ends
23:26:48 UTC (`status: capture-interrupted`, below). MongoDB
`_id 6aa1ed98d73e09708a7023f4`, QC promoted `unreviewed` → `ok`,
`valid = true`.

| # | target | delivered | error | status | time | auger rev | taps | cycles |
|---|---|---|---|---|---|---|---|---|
| 0 | 50 mg | 48.7 mg | **−1.3** | **ok** | 47 s | 0.50 | 12 | fine:4 tap:6 |
| 1 | 50 mg | 71.0 mg | **+21.0** | overshoot | 12 s | 0.92 | 2 | bulk:1 tap:1 |
| 2 | 50 mg | 62.1 mg | **+12.1** | overshoot | 9 s | 0.00 | 0 | bulk:1 |
| 3 | 200 mg | 195.1 mg | **−4.9** | **ok** | 220 s | 0.50 | 116 | bulk:1 fine:4 tap:58 |
| 4 | 200 mg | 191.0 mg | −9.0 | cycle-budget | 707 s | 0.60 | 400 | bulk:1 fine:4 tap:200 |
| 5* | 200 mg | ≈164.5 mg | ≈**−35.5** | stalled (nudges 10/10) | ~560–900 s | — | ~150 | fine:38+, tap to nudge budget |

\* **Dose 5 is reconstructed, not in the run document's `doses` array.**
At 23:18 UTC, immediately after `nudge 10/10`, the USB serial stream
corrupted (the raw log's last legible line is the nudge; then
interleaved fragments of the device's `META`/`RUN,END` output) and the
capture hung reading it. The device finished on its own and parked —
the bench camera at 23:28:57 UTC shows the tube horizontal and the
run's final tare-relative mass static at 0.1635 g, and the 300 s
post-run capture reads 164.9 → 164.5 mg. The SIGINT recovery flushed
`run.json` and every CSV intact at 23:26:48 UTC; the full
wall-clock-stamped console is preserved in
[`capture_pane_scrollback.txt`](../../data/battery/20260909T225206Z_calcium-lactate/capture_pane_scrollback.txt).

Per-target (capture summary, bracket read path): **50 mg mean +9.9 mg
(1/3 ok, both misses overshoots) · 200 mg recorded pair −6.9 mg
(1/2 ok); ≈−16 mg including the reconstructed dose 5.** Total
dispensed ≈0.73 g (≈2.2 g in the vessel with the pre-flight).

### The predicted overshoot happened — the first quantum exceeds the target

Calcium lactate conveys ≈290 mg/rev here, and doses 1–2 show the
mechanism cleanly: a single opening bulk actuation (`bulk:1`, 0–0.92
rev) delivered 62–71 mg **before the first feedback reading could halt
anything** — more than the entire 50 mg target, in 9–12 s, with 0–2
taps. Dose 0 escaped only because it started with a freshly drained
lip (pre-flight taps + tare immediately before), skipped bulk
(`bulk:0`), and closed −1.3 mg with fine + taps. So on a fast powder
the 50 mg outcome is decided by the *lip state at dose start*, not by
the controller loop — same failure xanthan gum showed (+17.8 mg), now
with the mechanism resolved. Overshoot is unrecoverable by design
(powder cannot be un-dispensed), which makes this the worse failure
mode despite the small numbers.

### 200 mg behaves like a miniature Block G

All three ground into phase 3 at tilt 0° (116 / 400 / ~150+ taps),
where calcium lactate's tap quantum collapses from 20.4 mg (45°) to
~2 mg — dose 4 burned its full 200-cycle tap budget for the last 9 mg
and dose 5 exhausted the nudge budget. Same endgame Block G documented
at 1 g (−26.5 mg mean, 2026-08-05).

### Error vs target: the opposite discriminator result from sodium alginate

Mean |error| is roughly **constant in mass** across the 20× span
(11.5 / 7.0 / 26.5 mg at 50 / 200 / 1000 mg) so *relative* error falls
with target — where alginate's error scaled *with* the target
(fixed-fraction, 29–51 %). One frozen controller, two opposite scaling
regimes, split by feed factor: fast powders are quantum-limited (the
first actuation decides), slow powders are budget-limited (the
timeout decides). That is the Block H campaign's headline for #97.

### Campaign table complete (per-target mean error, mg)

| powder | 200 mg | 50 mg |
|---|---|---|
| salt | +2.8 | +4.2 |
| white rice flour | −4.9 | −4.7 |
| xanthan gum | +2.9 | +17.8 |
| carboxymethyl cellulose | −22.6 | −2.2 |
| sodium alginate | −101.5 | −19.6 |
| **calcium lactate** | **−6.9** (≈−16 with dose 5) | **+9.9** |

### Drift epilogue — it was the vessel, not the powder

The ~2 mg/min floor that held the launch turned out to be the
vessel/enclosure still drying: the 300 s post-run capture, with ~50 %
*more* calcium lactate sitting in the beaker, reads **−0.08 mg/min**
(96 % stable, jitter 0.025 mg) — if the powder itself were losing
moisture at the mg/min scale, more powder would drift more, not 25×
less. In-run bias bounds from the decaying slope: doses 0–2 (<50 s)
< 2 mg; dose 3 (220 s) < 7 mg; dose 4 (707 s) < 20 mg — none of which
changes any dose's classification. Data:
[`2026-09-09_calcium-lactate-postrun-drift-300s.csv`](../rig-checks/data/2026-09-09_calcium-lactate-postrun-drift-300s.csv).
Bench note for future sessions: a freshly washed/wiped vessel needs
**~1 h in the hood draft** before the 180 s gate passes — load powder
first, let the vessel dry, run last.
