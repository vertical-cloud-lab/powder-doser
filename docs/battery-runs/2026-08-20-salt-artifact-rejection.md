# Salt, 2026-08-20 -- first run with environment-artifact rejection

`data/battery/20260820T175631Z_salt/` -- MongoDB `powder_doser.battery_runs`
`_id 6a87472ba5dfec6360656340`. **`qc.valid_for_cross_powder_comparison =
false`** (see "Why this run is not in the cross-powder set" below).

| | |
|---|---|
| Started | 2026-08-20 11:56:31 MDT (17:56:31 UTC) |
| Stopped | 2026-08-20 12:24 MDT, by the operator, mid-block-E |
| Blocks | A, B, C complete; D complete; E complete at tilt 0, one trial at tilt 45 |
| `battery_version` | 2 (first run) |
| Status | `truncated` -- no `RUN,END`; rebuilt from the raw serial log |

## Why it matters

This is the first battery run on this rig since the 2026-08-19 move that
produced data at all.  Three consecutive sessions had aborted in
`battery_preflight` with `scale-unreadable`.

The cause was not the room.  `scale.zero()` sends the A&D tare command,
**the balance silently refuses it while it considers itself unstable**,
and then emits nothing for roughly 19 s.  The battery read that silence
as a dead balance.  During the 11:44 environment survey only 2 % of
frames were stable, so the tare was refused essentially every time.

The tare is now best-effort.  Nothing downstream needs the displayed
value to be zero: every measurement in the battery is a *difference*
between two bracket fits, so a stale zero cancels exactly.  Its only
real job is keeping the gross load inside the 102 g capacity, which the
battery now checks explicitly.

Pre-flight then passed first time: **1.0698 g over 5 revolutions at tilt
90 deg = 214 mg/rev, `feed confirmed`** -- with *zero* stable frames in
the whole check.

## The room during the run

The 300 s bare survey immediately before the run
(`docs/rig-checks/data/2026-08-20_balance-beaker-back-survey-300s.csv`):

| | |
|---|---|
| sample-to-sample jitter | 2.13 mg |
| stable frames | 26 / 1046 (2 %) |
| drift | +6.8 mg/min |
| shock events > 10 mg | 11 in 5 min (2.2 / min) |
| survey verdict | "even short trials are being disturbed" |

That is roughly 20x the jitter and 10x the shock rate of the 2026-08-20
09:50 bare-pan window.  The run went ahead deliberately: this is the
condition the new code exists for, so it is a test of it rather than a
formality.

## What the artifact rejection did

Over 48 trials:

| | |
|---|---|
| trials clean / unsettled / shock-corrected | 1 / 12 / 35 |
| shock events removed | 36, totalling 539 mg |
| drift removed | median 15 mg per trial, 920 mg total |
| trials re-measured | 57 retries across 48 trials |
| median trial sigma | 12.1 mg (p90 29 mg, max 62 mg) |

The correction moves *block means* by only 4-8 mg, because random shocks
largely cancel over six trials.  Its value is elsewhere:

1. **The run happened.**  Version 1 would have aborted before block A.
2. **No single trial is wrecked.**  A 100 mg knock is removed rather than
   recorded as 100 mg of powder.
3. **Every trial carries an uncertainty**, so the spread of six
   revolutions no longer has to stand in for both powder variability and
   whatever the room did.
4. **Block A is the cleanest demonstration**: the no-actuation baseline
   reads 1.0 mg corrected against 5.5 mg uncorrected.

## Results

Block C, six 360 deg revolutions at 30 RPM per tilt:

| tilt | mg/rev | RSD | median trial sigma | 2026-08-12 salt |
|---|---|---|---|---|
| 0 deg | 50.4 | 38.5 % | 14.9 mg | 34.3 |
| 45 deg | 155.0 | 19.8 % | 12.8 mg | 175.3 |
| 90 deg | 208.5 | 17.1 % | 20.7 mg | 230.4 |

Monotonic in tilt, saturating above 45 deg, and within 12 % of the
2026-08-12 salt run at 45 and 90 deg -- a different room, a different
vessel, eight days apart.  The mechanism is fine.

Other blocks: **A** baseline 1.0 mg mean over 8 no-actuation reads;
**B** no discharge at any tilt (deltas -54 / +93 / +35 mg are inside the
environment's own contribution over a 15 s hold, so this is a null
result, not a measurement of avalanching); **D** 476 mg over 3
revolutions at tilt 45; **E** at tilt 0, refeed 48.9 mg/rev and tap
7.2 mg/tap (RSD 221 %, i.e. not resolved from zero).

## Why this run is not in the cross-powder set

- It is **truncated**: block E is incomplete and F/G never ran.
- The median trial sigma of **12.1 mg** is comparable to the block C
  tilt-0 signal itself (50 mg/rev).  The 2026-08-12 salt run had RSDs of
  6-9 % against today's 17-39 %.
- 35 of 48 trials required a shock correction.  The numbers are
  defensible, but they rest on the correction to a degree that the rest
  of the dataset does not.

It is recorded as `qc.verdict = "environment-stress-test"` and kept as
evidence that the pipeline works end to end under bad conditions.

## Follow-ups

1. **Isolation is now the binding constraint**, not software.  The
   balance sits directly on the fume-hood deck with the doser platform's
   feet on the same surface, so the rig is itself a coupling path.  A
   20-30 kg stone paver on sorbothane, with the doser decoupled from it,
   is the cheap version of an anti-vibration table.
2. **Re-run salt for the record** in a quiet window, `blocks="ABCDE"`,
   about 28 minutes.
3. **Block G stays blocked** in this room.  A multi-minute closed-loop
   dose against a +/-5 mg band cannot be rescued by per-trial bracketing;
   the survey puts the environment's own contribution over 180 s at
   33-40 mg.
4. Block F (vibration) is still missing everywhere -- the DRV2605L is not
   on the I2C bus.
