# Balance noise with the breeze break removed (fume hood, 2026-08-19)

**Question asked** (@swcharles, issue #116): the replacement 100 mL beaker was
too tall for the breeze break, so the top of the shield was removed; the
balance then became effectively un-tareable in the fume-hood draft.  Is that
"terrible", or a cosmetic annoyance?

**Answer: it is disqualifying, and it is measurable.**  With the shield off,
the A&D HR-100A is 50-90x noisier than its own repeatability specification,
and the noise is *low frequency*, so it cannot be averaged away.

## Measurement

Read-only.  No actuator was commanded; no auger was dosed.  The Pico polled
the balance with the A&D `Q` (immediate datum) command at ~3.4 Hz for 75 s,
twice, about 7 minutes apart, with the pan carrying the empty vessel
(62.15-62.20 g) and the fume hood running.

| | window 1 | window 2 |
|---|---|---|
| samples | 262 | 262 |
| reported **stable** (`ST`) | 43 (16 %) | 57 (22 %) |
| mean | 62.1880 g | 62.1490 g |
| **standard deviation** | **8.92 mg** | **5.15 mg** |
| **peak-to-peak** | **34.5 mg** | **20.3 mg** |
| SD of a 10 s rolling mean | 6.91 mg | 4.33 mg |
| sample-to-sample \|delta\| (mean / max) | 0.52 / 5.70 mg | - |

Raw captures: `data/2026-08-19_balance-draft-noise-window1.csv`,
`data/2026-08-19_balance-draft-noise-window2.csv`.

Between the two windows the *baseline itself* moved by 39 mg in ~7 minutes,
which is larger than either window's peak-to-peak spread.

## Why this is disqualifying

- **Against spec.** The HR-100A's published repeatability is a standard
  deviation of **0.1 mg** (manual section 21, capacity 102.0084 g, minimum
  display 0.1 mg). Measured: 5.15-8.92 mg.
- **Against our own prior runs.** Block A (8 no-actuation reads) returned
  deltas of exactly 0.0000 g on every valid battery run to date -- a noise
  floor below the 0.1 mg display resolution. This is a ~50-90x regression.
- **Against the dose tolerance.** Block G's closed-loop tolerance is +/-5 mg.
  In window 1, **63 % of samples sat more than 5 mg from the median**. The
  reading wanders further than the entire acceptance band, so the three-phase
  controller would chase drift as if it were powder -- and would report
  convergence or overshoot that never happened.
- **Averaging does not rescue it.** Sample-to-sample jitter is small (0.52 mg
  mean), but the SD of a 10 s rolling mean is still 4.3-6.9 mg. The
  disturbance is low frequency -- it lives in the same band as the dosing
  signal itself, so any filter that removes it also removes the measurement.
- **Most block-scale quantities disappear.** The measured tap quantum ranges
  from 0.11 mg (white rice flour) to 20.4 mg (calcium lactate); feed factor
  from <0.3 mg/rev (brown rice flour) to 232 mg/rev (calcium lactate). With a
  +/-10 to +/-17 mg wander, everything below roughly 30 mg per trial is
  unmeasurable.

The failure mode is worse than "the tare fails". A tare usually *succeeds* --
`read_stable()` returned an `ST` datum in 94-3683 ms across five attempts --
but it latches an arbitrary point inside a 20-35 mg wander, so the zero is
silently wrong by an unknown amount that then drifts during the run.

## What the manufacturer says

From the HR-A / HR-AZ manual
([PDF](https://weighing.andonline.com/wp-content/uploads/2024/01/HR-A_HR-AZ_Manual_02.pdf)):

- Troubleshooting checklist, section 19-1: *"Is the operating environment free
  from vibration and drafts? **Has the breeze break been installed?**"*
- Section 8-1: *"When calibrating, be sure to install the provided large breeze
  break."* -- the shield is part of the instrument, not an accessory.
- Section 19-2: `EC,E11` stability error (the `Error 1` seen on 2026-08-19) is
  *"The balance can not stabilize due to an environmental problem. Prevent
  vibration, drafts, ..."*, and points at section 7 for response adjustment.

## Mitigations, in order of preference

1. **Restore a closed breeze break around a vessel that fits inside it.** This
   is the only fix that recovers the sub-0.1 mg floor the existing dataset was
   collected at. A shorter vessel is the enabler, not the goal.
2. **Reduce the draft at the balance** -- lower the sash to the marked working
   height, and keep the balance out of the direct inflow path at the hood face.
   Note this trades against containment for the metal powders, so it is a
   complement to (1), not a substitute.
3. **Response adjustment (`SLOW`)** -- press and hold `MODE` until `RESPONSE`
   appears, then `MODE` to select `FAST` / `MID.` / `SLOW` (manual section 7).
   `SLOW` sets `Cond 2` ("strong against drafts and vibration") and
   `5pd 0`. Caveat: this adds settling lag, and the manual explicitly
   recommends `Cond 0` / `FAST` for *"powder target weighing"*. The block G
   fine phase runs on a ~4 s cycle, so a slower response will change dosing
   dynamics -- if we ever ship a run at `SLOW`, the response setting must be
   recorded in the run document, because it is no longer comparable with the
   existing runs.
4. **Do not reach for zero tracking (`trc`).** Strong zero tracking would hide
   the drift by silently subtracting it -- and would also subtract genuine slow
   feed. Brown rice flour delivers ~0.2 mg per revolution; zero tracking would
   erase exactly that signal.

## Capacity note

The vessel currently on the pan weighs **62.15 g** against a **102.0084 g**
capacity, leaving ~40 g of headroom. That is ample for 1 g doses, so capacity
is not the constraint -- **fitting under the breeze break is**. A smaller
beaker helps on both counts; a light vessel (paper cup) helps capacity but is
the most draft-sensitive option, which is now the binding constraint rather
than a theoretical one.

## Status

No battery run should be started until the balance is back under a closed
shield and a fresh noise window shows block-A-style deltas at or below
0.1 mg. That check takes ~75 s and is worth running before every session in
the hood.
