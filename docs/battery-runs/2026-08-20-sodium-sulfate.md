# Sodium sulfate -- uniform powder battery, 2026-08-20

First powder beyond salt after the move into the fume hood, and the first run
of the `inorganic-2026-08` batch.  Blocks A-E; block G was deliberately held
back (see *Why block G did not run*).

| | UTC | lab (MDT) |
|---|---|---|
| Pre-run environment survey | 19:16 -> 19:20 | 13:16 -> 13:20 |
| Pre-flight feed check | 19:21 | 13:21 |
| **Battery started** | **2026-08-20T19:22:24Z** | 13:22:24 |
| **Battery ended** | **2026-08-20T19:35:40Z** | 13:35:40 |
| **Elapsed** | **0:13:15** | |

Per block: A 45 s · B 1 m 29 s · C 4 m 37 s · D 56 s · E 5 m 23 s · F skipped
(DRV2605L absent from the I2C bus) · G not requested.

- Run document: [`data/battery/20260820T192224Z_sodium-sulfate/`](../../data/battery/20260820T192224Z_sodium-sulfate)
- MongoDB `powder_doser.battery_runs`, `_id` `6a8757a7072e3fb5b2146cac`
- Video: this run sits in broadcast `23PlXoQgjPQ` -- see the
  [run log](RUN-LOG.md) for the timestamped link.

## Pre-flight

Tilt 90 deg, five 360 deg revolutions at 30 RPM, then 10 taps.  Per
revolution: **-12, +11, +145, +302, +320 mg**; 10 taps added 34 mg.
Verdict `feed confirmed`, 153 mg/rev averaged over the five.

The first two revolutions are the delivery section charging from empty and the
last two are steady state, so the *averaged* pre-flight number understates the
real feed factor by about 2x here.  That is the same shape white rice flour
showed and the opposite of calcium lactate, which reached steady state on
revolution one.

## Block C -- feed factor vs tilt

Six 360 deg revolutions at 30 RPM per tilt.

| tilt | mg / revolution | RSD | median per-trial sigma |
|---|---|---|---|
| 0 deg | 51.2 | 34 % | 12.2 mg |
| 45 deg | 208.4 | 15 % | 7.8 mg |
| 90 deg | 243.6 | 12 % | 11.0 mg |

Monotonic in tilt and saturating above 45 deg (+17 % from 45 to 90), the same
shape as calcium lactate, sodium alginate and xanthan gum.

**243.6 mg/rev at 90 deg is the highest feed factor measured in this dataset**,
just past calcium lactate's 232.2.  The RSDs, though, are 4-5x calcium
lactate's -- and that difference is the room, not the powder (see
*Environment*).

Revolution by revolution:

| tilt | 1 | 2 | 3 | 4 | 5 | 6 |
|---|---|---|---|---|---|---|
| 0 deg | 60.3 | 51.2 | 47.3 | 59.2 | 16.7 | 72.5 |
| 45 deg | 237.4 | 257.9 | 197.5 | 197.2 | 184.2 | 176.2 |
| 90 deg | 253.6 | 284.0 | 261.9 | 236.1 | 221.7 | 204.0 |

Both 45 deg and 90 deg decline steadily across the six revolutions (-26 % and
-20 % from first to last).  That is consistent with the column depleting -- 7.9
g left the auger over the run -- but a single run cannot separate depletion
from a slow environmental trend, so it is recorded as an observation rather
than a finding.

## Block D -- speed

Three continuous revolutions at tilt 45 deg.

| auger RPM | mg / 3 rev | mg / revolution |
|---|---|---|
| 15 | 1269.7 | 423.2 |
| 45 | 790.8 | 263.6 |
| 90 | 656.6 | 218.9 |

Mass per revolution falls **48 %** across a 6x speed change, putting sodium
sulfate with calcium lactate (-33 %), xanthan gum (-55 %) and AlSi10Mg (-62 %)
in the filling-limited-by-time group: the flights fill under gravity at a
finite rate, so a faster screw carries less per turn.

**Do not read the slope too closely.**  Block C measured 208 mg/rev at 30 RPM,
which is *below* block D's 90 RPM point of 219 mg/rev -- so the 30 RPM point
does not fall on the block D line.  Block C uses six separate single
revolutions with a settle between each; block D uses three continuous
revolutions.  Whether that difference, or the ordering of the two blocks, is
responsible is not resolvable from one run.  Randomised block and RPM order
would settle it.

## Block E -- tapping

| tilt | 360 deg re-feed rotation | single tap |
|---|---|---|
| 0 deg | 41.01 mg (SEM 3.35) | 7.90 mg (SEM 2.65) |
| 45 deg | 184.71 mg (SEM 7.18) | 9.34 mg (SEM 2.63) |

**The tap quantum is not resolved.**  The taps average 8-9 mg, but block A's
eight *no-actuation* trials in the same run scattered over 22.7 mg with a mean
of +7.5 mg (SEM 8.0).  A per-action quantum smaller than what the procedure
returns when nothing happens is a description of the room, not of the powder.
It should not enter the cross-powder tap table.

This matters because the cross-powder pattern so far is that tap efficacy
tracks feed factor: the two powders where tapping moved real mass, calcium
lactate (20.4 mg/tap) and xanthan gum (13.6 mg/tap), are the two highest-feed
powders.  Sodium sulfate now has the highest feed factor of all, so that
pattern predicts a large tap quantum here.  The measurement is *consistent*
with it and cannot confirm it.  Re-measuring block E on a quiet bench would.

`plot_battery_results.py` now derives this: the panel C title reads "tap
quantum not resolved above the no-actuation baseline" rather than quoting a
figure, whenever the peak tap mean fails to clear both block A's spread and
twice its own standard error.

## Blocks A and B

**A** -- eight no-actuation reads: -8.0, +42.0, +13.9, -23.5, +41.9, -13.8,
+7.1, +0.4 mg.  Mean +7.5 mg, sd 22.7 mg, SEM 8.0 mg.  The mean is not
distinguishable from zero; the *spread* is the run's noise floor and it is what
limits blocks C at 0 deg and E.  Every valid run before the fume-hood move
returned 0.0000 g here.

**B** -- 15 s static holds, no actuation: **+119.5 mg at 0 deg**, -6.2 mg at
45 deg, -20.1 mg at 90 deg.  All three trials are flagged `shock`.

The 0 deg reading is an artifact, not a discharge, and the geometry says so:
horizontal is the *least* favourable orientation for gravity flow, so a powder
that discharges at 0 deg but not at 90 deg is not discharging.  It is a bench
knock inside the hold window, which is the one place the actuator gate cannot
help -- there is no action to bracket against.  Recorded as such; the
conclusion is unchanged from the other eight powders: **nothing in this dataset
avalanches through a stationary auger, even fully vertical.**

## Environment

The pre-run survey was discouraging -- 2.12 mg sample-to-sample jitter, 2 % of
frames stable, one shock event in four minutes, and a verdict of "even short
trials are being disturbed".  The run itself landed in a calmer stretch:

| | pre-run survey | this run | 2026-08-20 salt run |
|---|---|---|---|
| median per-trial sigma | -- | **5.9 mg** | 12.4 mg |
| shock events (host) | 0.3 / min | **9** | 36 |
| re-measured trials | -- | **3** | 57 |
| clean trials | -- | **12 / 64 (19 %)** | 1 / 48 (2 %) |
| drift removed | -- | 0.726 g | 0.920 g |

So the room is roughly 2x quieter than it was for the salt run three hours
earlier, and the artifact-rejection pipeline had correspondingly less work to
do.  Device-side counters (141 brackets, 82 unsettled, 20 shocks, 2 quiet
waits) are in the run document under `environment.device`.

Against a feed factor of 208-244 mg/rev, a 5.9 mg per-trial sigma is 2-3 % --
which is why block C is a usable measurement while block E is not.

## QC

Recorded `valid_for_cross_powder_comparison = true`, `verdict = ok`, with the
block-level caveats above.  The reasoning:

- The headline cross-powder quantity, block C feed factor at 45 deg and
  90 deg, has SEM 13.1 and 11.8 mg on means of 208 and 244 mg -- ±6 % and ±5 %.
  That is a real measurement, comparable to white rice flour's (37 % RSD at
  45 deg) which is in the dataset as valid.
- The independent internal check passes: block C at 45 deg (208.4 mg/rev) and
  block E's re-feed rotations at the same tilt and RPM five minutes later
  (184.7 mg/rev) give a ratio of **0.89**, inside the 0.74-1.12 band every
  well-behaved run has shown.  The 2026-08-06 salt run, which failed this
  check at 2.68, was the one recorded as a lower bound.
- What is *not* valid is per-block and is flagged rather than folded in: the
  block E tap quantum, and the block B 0 deg hold.

Worth stating plainly: the block A noise floor here is 22.7 mg where every
pre-move run returned 0.0000 g.  Anyone comparing per-revolution *spread*
across powders should treat this run's RSDs as upper bounds.  Comparing
*means* is fine.

## Why block G did not run

The pre-run survey put the environmental error over a 180 s window at
**18.3 mg**, against block G's ±5 mg dose tolerance.  A closed-loop dose runs
2-14 minutes, so the baseline can move further than the whole acceptance band
during a single dose, and the actuator gate cannot help: mass genuinely does
arrive throughout a dose, so there is no do-nothing interval to bracket
against.

Block G is unblocked by isolating the balance, not by more software.  The
balance currently sits directly on the fume-hood deck with the doser
platform's feet on the same surface, so the rig is itself a coupling path.
