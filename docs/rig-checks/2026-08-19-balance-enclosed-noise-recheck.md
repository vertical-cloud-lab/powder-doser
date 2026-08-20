# Balance noise with the enclosure replaced and the sash closed (2026-08-19)

**Question asked** (@swcharles, issue #116): after the shield-removed result,
the enclosure was replaced and the sash closed.  The balance "seems much
better" that way -- how much better, measured the same way as before?

**Answer: the draft noise is gone.**  Short-term scatter is 6-20x lower,
sample-to-sample jitter is back at the display resolution, and no sample in
any window sits more than 5 mg from its window median (it was 63 % of them).
What remains is a *slow baseline wander* of order 1-2 mg/min, which is
harmless for blocks A-E but is the same size as the block G dose tolerance
over a multi-minute dose.

Companion to `2026-08-19-balance-draft-noise-shield-removed.md`, which is the
before case.  Figure: `frames/2026-08-19_balance-enclosure-comparison.png`.

## Measurement

Identical protocol to the before case, so the numbers are directly
comparable: read-only, no actuator commanded, no auger dosed.  The Pico
polled the balance with the A&D `Q` (immediate datum) command at ~3.5 Hz
(286 ms period) for 75 s, with the fume hood running and the enclosure
closed over an empty vessel.

Three 75 s windows, plus one 8.4 min continuous record at ~1.4 Hz:

| | before w1 | before w2 | **after w1** | **after w2** | **after w3** |
|---|---|---|---|---|---|
| start (MDT) | ~14:00 | ~14:07 | **15:46:30** | **15:55:14** | **16:07:09** |
| samples | 262 | 262 | 262 | 262 | 262 |
| reported stable (`ST`) | 16 % | 22 % | **80 %** | **85 %** | **89 %** |
| mean | 62.1880 g | 62.1490 g | 11.6707 g | 11.7012 g | 11.5659 g |
| raw standard deviation | 8.92 mg | 5.15 mg | **1.84 mg** | **0.83 mg** | **0.92 mg** |
| raw peak-to-peak | 34.5 mg | 20.3 mg | **6.10 mg** | **3.20 mg** | **4.50 mg** |
| sample-to-sample \|delta\|, mean | 0.52 mg | - | **0.061 mg** | **0.047 mg** | **0.041 mg** |
| linear trend over the window | - | - | +5.5 mg | +2.3 mg | -2.8 mg |
| **scatter with that trend removed** | - | - | **0.93 mg** | **0.51 mg** | **0.42 mg** |
| samples >5 mg from window median | **63 %** | - | **0 %** | **0 %** | **0 %** |

Raw captures: `data/2026-08-19_balance-enclosed-noise-window{1,2,3}.csv`,
`data/2026-08-19_balance-enclosed-drift-8min.csv`.

The vessel on the pan now weighs **11.67 g** (it was 62.15 g), so the
capacity headroom against the 102.0084 g maximum went from ~40 g to ~90 g.

## What improved

- **Draft-band noise is gone.** Sample-to-sample change is 0.041-0.061 mg,
  i.e. at or below the 0.1 mg display resolution, against 0.52 mg with the
  shield off -- a ~10x improvement in the high-frequency term.
- **Every sample is inside the dose band.** 0 % of samples sit more than 5 mg
  from their window median, against 63 % before.
- **The balance now considers itself stable most of the time.** The `ST`
  fraction rose from 16-22 % to 80-89 %, and it *increases* across the three
  windows (80 -> 85 -> 89 %) as the enclosure settles.
- **A tare is now meaningful.** Before, `read_stable()` returned an `ST`
  datum but latched an arbitrary point inside a 20-35 mg wander.  The same
  call now latches inside a <1 mg scatter.

## What is left: a slow baseline wander

The residual is not noise, it is drift, and it needs to be reported
separately because the two behave differently.

Within each 75 s window the reading follows a smooth ramp of +0.074, +0.030
and -0.038 mg/s respectively; removing that ramp leaves 0.42-0.93 mg of
actual scatter.  The 8.4 min continuous record shows the same thing on a
longer baseline: flat for ~4.5 min, then rising at ~1.7 mg/min, for
**11.6 mg peak-to-peak end to end**, but

- **<=4.2 mg** inside any 60 s window, and
- **<=7.4 mg** inside any 180 s window.

The window means also moved between windows (+30.5 mg over the 8.7 min gap
w1->w2, -135.3 mg over the 12 min gap w2->w3).  Those gaps were *not*
observed, and the shifts are an order of magnitude larger than anything in
the continuous record, so they are most likely discrete disturbances (hood
sash, someone at the bench, the enclosure being touched) rather than the
instrument.  Reported here as unattributed rather than as a drift rate.

## What this means for a run

- **Blocks A-E are fine.** They measure a *delta* across a single trial
  lasting a few seconds to ~40 s, with a fresh reference read on either side.
  A <=4.2 mg/60 s wander plus <1 mg scatter is small against the quantities
  those blocks measure for every powder except brown rice flour.
- **Block G is marginal.** A closed-loop dose runs 2-14 min, and its
  acceptance band is +/-5 mg.  Over a 3 min dose the baseline can move as
  much as the entire band, so a dose reported as `ok` at -4 mg carries a
  comparable amount of baseline uncertainty.  Dose errors from runs collected
  in this condition should be quoted with that caveat until the drift is
  chased down.
- **It is not yet back to the historical floor.** Every valid battery run so
  far returned block A deltas of exactly 0.0000 g -- below the 0.1 mg display
  resolution.  We are at 0.4-0.9 mg of scatter, so ~5x the balance's 0.1 mg
  repeatability spec and worse than the runs this dataset is built from.  The
  gap is worth closing before a full battery is compared numerically against
  the 2026-08-04 to 2026-08-12 runs.

## Candidates for the residual drift, cheapest first

1. **Thermal settling.** The rig was moved back into the hood the same
   morning and the enclosure had just been replaced.  A load cell at a
   different temperature from its surroundings drifts smoothly until it
   equilibrates, which matches the decaying window slopes.  Cheapest test:
   leave the balance powered and undisturbed for an hour, then re-run this
   check.
2. **The balance has not been calibrated since the move.** The HR-A has an
   internal-mass calibration (`CAL`); a span/zero calibration after
   relocation is standard and the manual asks for it with the large breeze
   break installed.
3. **Something in light mechanical contact with the vessel.** This is the
   failure mode identified for the tall beaker: a contact force gives *low*
   scatter but large slow offset changes, which is exactly the signature
   here.  Worth eyeballing that the enclosure and the tap collar clear the
   vessel and the pan.
4. **Static.** A light insulating vessel in a dry hood accumulates charge;
   the resulting apparent-mass drift decays over minutes.

## Protocol note

This 75 s check is cheap (read-only, no powder consumed, no actuation) and
answers "is this session's data going to be worth collecting" before a
battery is started.  Run it at the start of every hood session, and record
the window's detrended scatter in the run notes.  Acceptance for a full
comparable battery: detrended scatter <=0.5 mg **and** no more than ~2 mg of
wander over 3 min.
