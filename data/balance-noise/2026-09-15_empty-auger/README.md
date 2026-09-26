# Empty-auger balance-disturbance battery, run 3 — 2026-09-15 (complete; interpretation corrected 2026-09-16)

Requested on PR #131 after the bench reported "the fume hood was never the
problem and scale drift has now been corrected": repeat the r1/r2 battery
with a **clean empty auger** (no powder anywhere) to get more reliable scale
noise data. Same script
([`balance_disturbance.py`](../../../hardware/test-module/firmware/balance_disturbance.py),
now carrying a `CONFIG_LABEL = "empty-auger"` metadata stamp), same
protocol and parameters; full ≈16 min sequence completed, no mass-guard
trip, 64 taps total. Session ≈ 19:17:45–19:33:30 UTC (±1 min).

> **Correction (2026-09-16).** This README originally concluded the run was
> "degenerate — the balance stream is clamped" by balance-side display
> processing (zero tracking and/or a heavy filter) introduced with the drift
> fix. Direct bench observation (williamulbz, PR #131) overturns that
> reading: the tests were watched live — the display genuinely did not
> change during actuation, a light shake of the table produces a visible
> reading change, and an added mass registers and stabilizes at the new
> value. The flat stream is real, not processed away. This file has been
> rewritten accordingly; the original text is preserved in git history
> (commit `9df0a51`) and the matching MongoDB document carries a
> `correction` field.

**Headline (corrected): on the post-fix bench, doser actuation couples less
than one display count (0.1 mg) into the balance, and the quiet floor is
sub-count.** 9,393 of 9,452 frames read *exactly* 0.0000 g (m0 was an exact
0.0000 too — the balance was re-zeroed during the fix), and the ST stable
flag is asserted on 99.7 % of frames, including during 75 rpm spins and tap
trains — because there was genuinely nothing to flag. Per-block detrended
sigma is exactly 0 in 25 of 29 blocks and ≤ 0.07 mg in three more
(single-count flickers); only `quiet_post` (1.09 mg) exceeds that, and its
variance is entirely two external bench events (next section). The flat-0
result held through:

- 20 single taps (r2, same rig, same morning: −8.3 mg mean kick at +0.9 s,
  individual readings ±30 mg) → not one displayed digit moved in any 2 s
  post-tap window;
- 8 three-pulse bursts, both RPM-ladder passes (15–75 rpm), stepper hold,
  10 × 45° increments, 20 s spin+tap, servo 0↔25↔60° moves → all flat 0.

Far from degenerate, r3 is the **best noise dataset this rig has produced**:
quieter than every pre-hood anchor (08-14 bench frames 0.13–0.42 mg; 08-07
floor 0.59 mg with −1.5 mg/min drift; r2 quiet windows 0.30–4.50 mg with
episodic multi-mg wander). Session drift: < 0.1 mg over 15.7 min, i.e.
< 0.007 mg/min.

## The stream is live and the flags are honest

The 59 frames that did move are what discriminate "genuinely quiet" from
"clamped", and on re-reading they corroborate the bench observation:

- `quiet_post` t ≈ 869.6 s: a +0.3/+0.4 mg wiggle — **9 frames flagged US**
  while it moved, back to S as it decayed through +0.1/+0.2 mg over
  ≈ 2.5 s, then 0.0000 again. The balance flagged a *three-count*
  disturbance as unstable: the stability discriminator is alive and
  sensitive at the sub-mg level.
- `quiet_post` t ≈ 904.5 s: +3.3 mg spike with a −1.4 mg undershoot,
  decaying over ≈ 1.5 s — US through the entire excursion, S again once
  settled. This is the signature of a light external bench disturbance —
  exactly the class of stimulus the bench confirms does register (a light
  shake of the table visibly moves the reading).
- Isolated ±0.1 mg single-count flickers inside `auger15_p1`,
  `post_auger15_p1` and `servo_moves` — a live ADC toggling at a code
  boundary (detrended sigma ≤ 0.07 mg).

So ST-on during spins does not mean the flag stopped discriminating — it
means the spins genuinely did not disturb the reading. The r2 contrast (ST
0–8 % mid-spin) was the same flag honestly reporting a genuinely disturbed
reading in that configuration.

Two details from the original analysis dissolve on inspection:

- *"Values are pulled back to a dead-exact zero"* — with constant true mass
  and sub-count noise, returning to the pre-event value **is** settling.
  Re-centering would only be suspicious if a crept value were being walked
  back, and that never occurs in this log.
- The apparent datum-rate halving (5.2 Hz here vs 10.4 Hz in r1/r2) is an
  analyzer artifact: `datum_rate_hz` is derived from value-*changes*, which
  a flat stream barely has (repeated counts during the two small transients
  dominate the median). It is not evidence the balance `Spd` setting
  changed.

## What r2 vs r3 actually measured

Same rig, same day, same sequence: r2 resolved every actuation state as
±10–60 mg structure; r3 resolves none of it. Two things changed together
between the runs: whatever the bench's drift fix physically was, and the
tube configuration (r2: covered exit on a powder-laden auger; r3: clean
empty auger). The data cannot split the credit between them — recording
what the fix was (one line, below) settles it. Either way, **r2's
disturbance map describes the pre-fix configuration, not the current
bench**: its spin-bias correction and ST-distrust rules should not be
applied to post-fix data.

## Consequences for the controllers (#124 / #162)

The corrected reading is much better news than the original:

1. **Measurement noise is quantization-dominated.** For the Kalman/R
   discussion: on the current bench R ≈ (0.1 mg)²/12 plus a sub-count
   residual, both quiet *and under actuation*. The r2-derived mg-scale
   R-under-disturbance values are superseded for this bench (kept as the
   historical/worst-case set).
2. **Raw mid-actuation frames are trustworthy.** Threshold stops, per-tap
   yield reads and flow estimates can consume every frame during a spin
   with no vibration penalty; settle-waits are only needed for real powder
   in flight, and ST can be trusted as the arbiter (it flags real 0.3 mg
   events within ≈ 0.1 s).
3. **Single taps are cleanly resolvable.** A 0.3–0.7 mg tap yield is a
   3–7-count step on a flat baseline — no averaging required at this
   floor.

## What to do next (small, for the record)

1. **Record what the drift fix physically was** (one line here or in the
   bench log): it decides how much of the r2→r3 change is bench vs tube
   configuration, and repo policy is that bench changes are reproducible
   from the docs.
2. **Read back the balance function table once** (`trc` zero tracking,
   `Cond` filter, stability band, `Spd`) and record it here. Not because
   the clamp reading is still on the table — the bench observation and the
   flag behaviour settle that — but because these settings parameterize the
   measurement model, they have never been recorded, and `trc` matters for
   exactly one regime none of the probes above exercise: a slow sub-mg/s
   trickle right after a tare (a dose's first seconds). Ten seconds at the
   balance closes it permanently.
3. Optional: a short repeat with a dead load (a few grams) on the pan would
   confirm the same floor away from display zero — completeness only, no
   longer a prerequisite for anything.

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
  external events) + actuation timeline
- `quietfloor_and_leak.png`, `disturbance_map.png` — standard battery
  figures (flat traces — that flatness *is* the finding)
- `r2_r3_compare.png` — the r2→r3 contrast in one figure: the sequence r2
  resolved as ±10–60 mg disturbance structure leaves r3 flat at 0.0000 g
  with ST asserted throughout (`scripts/plot_disturbance_compare.py`)
