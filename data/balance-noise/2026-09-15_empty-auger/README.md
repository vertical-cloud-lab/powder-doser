# Empty-auger balance-disturbance battery, run 3 — 2026-09-15 (complete, but degenerate)

Requested on PR #131 after the bench reported "the fume hood was never the
problem and scale drift has now been corrected": repeat the r1/r2 battery
with a **clean empty auger** (no powder anywhere) to get more reliable scale
noise data. Same script
([`balance_disturbance.py`](../../../hardware/test-module/firmware/balance_disturbance.py),
now carrying a `CONFIG_LABEL = "empty-auger"` metadata stamp), same
protocol and parameters; full ~16 min sequence completed, no mass-guard
trip, 64 taps total. Session ≈ 19:17:45–19:33:30 UTC (±1 min).

**Headline: the run is not a noise measurement — the balance stream is
clamped.** 9,393 of 9,452 frames read *exactly* 0.0000 g (m0 was an exact
0.0000 too — the balance was re-zeroed during the fix), and the ST stable
flag is asserted on **99.7 % of frames, including during 75 rpm spins and
tap trains**. For comparison, r2 — same rig, same day, same sequence —
resolved every actuation state as ±10–60 mg structure with ST at 0–8 %
mid-spin. r3's per-block detrended sigma is 0.000 mg with p2p 0.0 mg in 26
of 29 blocks (`blocks_summary.csv`), through:

- 20 single taps (r2: −8.3 mg mean kick at +0.9 s, individual readings
  ±30 mg) → **not one displayed digit moved** in any 2 s post-tap window;
- 8 three-pulse bursts, both RPM-ladder passes (15–75 rpm), stepper hold,
  10 × 45° increments, 20 s spin+tap, servo 0↔25↔60° moves → all flat 0.

## What escaped the clamp (proof the link is live, not frozen)

- `auger15_p1` / `servo_moves`: isolated ±0.1 mg single-digit flickers.
- `quiet_post` (nothing actuating): a ~0.1–0.4 mg wiggle at t≈870 s and a
  ±3 mg transient at t≈905 s decaying over ~1.5 s — an external mechanical
  event (bench/draft), the only structure in the whole session — after
  which the display returns to *exactly* 0.0000 and stays there.

So the serial link and datum pipeline work; values above a small threshold
break through and are then pulled back to a dead-exact zero.

## Reading: the "drift fix" is display processing, not a quieter bench

An unclamped 0.1 mg-resolution balance does not stream a bit-identical
value for 15 straight minutes on a bench where the same morning it
resolved milligram-scale actuator signatures. The signature — exact
constant at display zero, re-zeroed start, ST always on, small escapes
re-converging to exact zero — points at balance-side configuration:
**zero-tracking (A&D function `trc`) and/or a heavy response filter
(`Cond`) enabled when the drift was "corrected"**. Mechanical isolation
alone cannot produce a bit-frozen display or a stable flag that stays on
during a 75 rpm spin.

Two consequences beyond invalidating this battery:

1. **Zero-tracking actively fights gravimetric dosing near zero.** It is
   designed to absorb slow accumulation at display zero — which is what a
   dose's first trickle looks like after a tare. A&D's own guidance is to
   disable tracking for dispensing/filling applications. Early-dose mass
   will be under-reported until flow outruns the tracking rate.
2. **The ST flag no longer discriminates.** `read_stable()` and every
   settle-wait in the controllers assume ST ≈ "mechanically settled"; in
   this configuration ST was asserted through every disturbance state. If
   the filter (not just tracking) was changed, this holds away from zero
   too, and step response will also be slower than the 08-14 calibration.

## What to do before the next attempt

1. On the balance function table, check and record: `trc` (zero tracking
   — should be **off** for this rig), `Cond` (was FAST), stability-band
   width, `Spd` (should stay 10/s).
2. Re-run this battery **with a dead load on the pan** (empty cup + a few
   grams, e.g. a calibration mass) so the operating point is away from the
   zero-tracking region — that alone makes the battery meaningful even
   before settings are confirmed, and mirrors real dosing conditions.
3. Then the r2 disturbance map can be re-measured for the post-fix bench;
   r2 remains the best available R/settling dataset until then.

## State / provenance

- Rig left safe: battery's finally-block halted actuators; Pico
  soft-reset to resident firmware (`[rig] ready` confirmed); port
  released. Known `DRV2605L (EIO)` boot warning unchanged.
- Nothing dispensed (auger empty); salt ledger unaffected. Pan absolute
  read 0.0000 g start and end; net 0.0 mg.
- Launched detached on the Pi:
  `mpremote connect /dev/ttyACM0 run /tmp/balance_disturbance.py
  > /tmp/balance_disturbance_r3.log`; log fetched over Tailscale SSH.

## Files

- `balance_disturbance_r3.log` — raw telemetry (9,452 D-frames at ~10 Hz
  poll rate, ST/US flags, rpm/tap/servo state; M/E/P rows)
- `samples.csv`, `blocks_summary.csv`, `tap_epochs.csv`, `summary.json`
  — parsed outputs of `scripts/analyze_balance_disturbance.py`
- `empty_auger_overview.png` — full-session trace (flat, with the two
  escape events) + actuation timeline
- `quietfloor_and_leak.png`, `disturbance_map.png` — standard battery
  figures (degenerate for this run, kept for completeness)
- `r2_r3_compare.png` — the finding in one figure: r2 vs r3 tap impulse
  response, per-state sigma, per-state ST fraction
  (`scripts/plot_disturbance_compare.py`)
