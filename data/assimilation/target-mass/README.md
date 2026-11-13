# Doses with a target mass, one per powder (issue #210)

Issue [#210](https://github.com/vertical-cloud-lab/powder-doser/issues/210) asked for runs that
had "a determined end point they are trying to reach", preferably one per powder. Every dose
here was given a target mass and stopped on its own: when the balance said the target was
reached, or when the controller gave up (stalled, timed out or ran out of cycles). Nothing was
re-measured; the data was on unmerged branches and in MongoDB.

**12 powders have such a dose. 9 of them reached the target.** Barium chloride, silicon −325
and sodium alginate never did: the powder stopped feeding first.

## Files

- **[`one_per_powder.csv`](one_per_powder.csv)**: one dose per powder, every reading, in one
  file (12 doses, 1453 rows). Start here.
- [`all_doses.csv`](all_doses.csv): all 108 doses in one file (7538 rows), same columns.
- [`doses_summary.csv`](doses_summary.csv): one row per dose: target, final mass, error, status,
  time, number of readings, start time, weather, and `pick` = 1 for the dose in
  `one_per_powder.csv`.
- [`doses/`](doses/): one CSV per dose, same columns.
- [`source/`](source/): the original files. `battery/<run>/` has each battery run's raw serial
  log, `doses_*.csv`, `run_*.json`, `timeline_*.csv` (from commit `f754450` on branch
  `claude/issue-116-20260915-1622`) and its MongoDB `battery_runs` document. `al4047/` has the two
  `opt_trials` documents, their serial logs and the tidy telemetry series from set C on branch
  `claude/issue-210-20261112-0137` (commit `9085f9a`). `pid/` has the salt PID `dose_runs`
  document.
- [`weather/`](weather/): the weather reports (see [Temperature and humidity](#temperature-and-humidity)).
- [`extract.py`](extract.py) rebuilds everything (see [Rebuilding](#rebuilding)).

## One dose per powder

| powder | controller | target | final | error | status | time | readings | date (UTC) | outdoor temp / RH |
|---|---|---|---|---|---|---|---|---|---|
| salt | `pid_single_loop` | 1 g | 1.0012 g | +1.2 mg | ok | 35.1 s | 356, every 0.1 s | 2026-07-29 | 30.6 °C / 34 % |
| Al 4047 | `bulk_only` | 0.3189 g | 0.3199 g | +1.0 mg | ok | 65.0 s | 141, every 0.38 s | 2026-09-30 | 22.2 °C / 42 % |
| sodium sulfate | `three_phase` | 1 g | 0.9971 g | −2.9 mg | ok | 86 s | 30 | 2026-09-10 | 12.7 °C / 43 % |
| AlSi10Mg | `three_phase` | 1 g | 0.9989 g | −1.1 mg | ok | 193 s | 60 | 2026-09-10 | 25.2 °C / 31 % |
| silicon −110/+200 | `three_phase` | 1 g | 0.9995 g | −0.5 mg | ok | 177 s | 54 | 2026-09-15 | 18.3 °C / 33 % |
| white rice flour | `three_phase` | 0.2 g | 0.1952 g | −4.8 mg | ok | 766 s | 187 | 2026-09-04 | 28.3 °C / 23 % |
| xanthan gum | `three_phase` | 0.2 g | 0.2025 g | +2.5 mg | ok | 85 s | 20 | 2026-09-04 | 29.1 °C / 19 % |
| calcium lactate | `three_phase` | 0.2 g | 0.1951 g | −4.9 mg | ok | 220 s | 64 | 2026-09-09 | 29.3 °C / 17 % |
| carboxymethyl cellulose | `three_phase` | 0.2 g | 0.1955 g | −4.5 mg | ok | 818 s | 194 | 2026-09-08 | 26.5 °C / 41 % |
| sodium alginate | `three_phase` | 0.05 g | 0.0387 g | −11.3 mg | timeout | 902 s | 233 | 2026-09-09 | 23.6 °C / 31 % |
| barium chloride | `three_phase` | 1 g | 0.3453 g | −654.7 mg | stalled | 33 s | 94 | 2026-09-10 | 20.5 °C / 34 % |
| silicon −325 | `three_phase` | 0.2 g | 0.0008 g | −199.2 mg | stalled | 52 s | 9 | 2026-09-10 | 30.3 °C / 15 % |

How the pick was made: salt and Al 4047 get their single-dispense doses (below). For the other
powders, the largest target that finished `ok`, then the smallest error. Where no dose finished
`ok`, the dose that got closest to its target as a fraction of it.

### More doses per powder

`all_doses.csv` has every dose of the runs used, 2 to 14 per powder:

| powder | doses | `ok` | targets |
|---|---|---|---|
| salt | 14 (1 PID, 13 battery from 4 runs) | 11 | 0.05, 0.2, 1 g |
| Al 4047 | 2 | 2 | 0.3189, 1.1012 g |
| sodium sulfate, AlSi10Mg, silicon −110/+200 | 9 each (one run) | 4, 6, 7 | 0.05, 0.2, 1 g |
| white rice flour, xanthan gum, CMC | 9 each (two runs) | 6, 5, 4 | 0.05, 0.2, 1 g |
| calcium lactate | 8 (two runs) | 2 | 0.05, 0.2, 1 g |
| sodium alginate, barium chloride | 9 each | 0 | 0.05, 0.2, 1 g |
| silicon −325 | 12 (two runs) | 0 | 0.05, 0.2, 1 g |

The August runs dosed 1 g three times (Block G). The September runs dosed 0.05 g three times and
then 0.2 g three times (Block H), and some also dosed 1 g three times first (Block G).
`doses_summary.csv` has each run's quality verdict (`run_qc_verdict`) and a link to its notes.

Not here: brown rice flour (three 1 g doses on 2026-08-05 that stalled within 8 s with nothing
delivered; the run's serial log is on no branch, and the two earlier runs had a suspect auger),
fumed silica (no dose block), and a few runs with a hardware fault: AlSi10Mg 2026-08-11 (tilt
servos), salt 2026-09-03 16:35 and 17:04 (balance unreadable), CMC 2026-09-08 17:27 (outlet
misaligned).

## The three controllers

**`pid_single_loop`, salt.** One continuous dispense: a PI loop sets the auger speed from the
mass still to go (kp 150 rpm/g, ki 8, up to 45 rpm), with 1.1 s of flow anticipation and a
gain-scheduled tilt. It is not the three-tiered controller. Taps would only start if
flow stalled, and none were needed. The balance was read every 0.1 s, including unstable frames.
The session runs a 10 s pre-roll, a tare, the dose (10.8 to 21.9 s, when the loop ended on its
overshoot guard at 1.0033 g), a 2.5 s settle, a 10 s post-roll, tilt home, and a final stable
weigh at 35.1 s. Firmware `pid_dose.py`, PR #131, 2026-07-29 run 2. The same document holds run 1
(an earlier version that timed out at 0.94 g after 80 taps), which is not used here.

**`bulk_only`, Al 4047.** The `trickle_tap` firmware's single-stage mode, also one continuous
dispense. The whole dose runs at one tilt (40) with the auger at up to 100 rpm and a 60 ms tap
every 500 ms. The rpm tapers near the target, and a slope predictor halts the auger once the
reading plus 0.83 s of flow reaches the target minus 1.5 mg. The balance was read every
0.28–0.47 s. Two doses finished `ok`: `56a01060` (freshly atomized lot 9fxeqt, 2026-09-30, the
pick) and `5851b6d6` (atomizer-cup lot, 2026-10-20). Al 4047's other eight controller doses
stalled, timed out, ran out of cycles or crashed; they are in set C on branch
`claude/issue-210-20261112-0137`. Five more Al 4047 records in `opt_trials` are `manual` (an
operator dosing by hand), so they are left out.

**`three_phase`, the powder battery (issue #116).** Three stages, each ending at a set mass to
go:

1. bulk: tilt 45, auger turning continuously at 55 rpm, balance polled every 250 ms. It stops at
   0.5 g to go for a 1 g target (0.2 or 0.05 g to go for the smaller targets, so it rarely runs
   there), then a settled reading;
2. fine: tilt 22.5, 45° auger steps at 30 rpm, one settled reading after each step (about every
   5 s), until 0.05 g to go (0.025 g for 0.05 g targets);
3. tap: tilt 0, auger still, two taps per cycle, one settled reading per cycle (about every 3 s),
   until 5 mg to go.

The status is `ok` when the dose ended within 5 mg of the target, `overshoot` above that,
`stalled` when the controller saw no powder flow (its message: "hopper empty, jam, or nudge
budget spent"), `cycle-budget` when a stage used up its cycles, and `timeout` at 900 s.

## Columns

Each row is one balance reading.

| column | meaning |
|---|---|
| `powder_id`, `dose_id`, `controller` | the powder, the dose (`doses/<dose_id>.csv`), and `pid_single_loop`, `bulk_only` or `three_phase` |
| `target_g` | the requested mass |
| `t_s` | seconds since the dose command. Battery doses: whole seconds, as printed on the console, so the bulk polls (every 0.25 s) share a second; the tare takes the first 6 s. PID: from the start of the session, with the dose starting at 10.8 s. `bulk_only`: device time to 0.01 s; the tare takes the first 6 s |
| `utc` | the same moment in UTC (see [Timing](#timing)) |
| `phase` | the controller's stage. PID: `preroll`, `tare`, `dose`, `postroll`, `home`. `bulk_only`: `bulk`, `bulk_end` (settled reading after the halt), `final_scored`. Battery: `bulk`, `bulk_settled`, `fine`, `tap`, `final` |
| `read_type` | `poll` (a reading taken while things move), `settled` (a settled reading after a step or tap), `final` (the result the dose was scored on), `pre_tare` (PID pre-roll, before this dose's tare) |
| `mass_g` | **the balance reading**, net of the dose's tare. For `pre_tare` rows it is the reading before the tare (what was already in the cup) |
| `to_go_g` | `target_g − mass_g`; blank before the tare |
| `stable` | 1 if the balance flagged the reading stable, 0 if unstable, blank if not logged |
| `tilt_setting_deg` | the tilt as the firmware logged it. On the battery runs the tube's angle above horizontal is half this (2:1 gear; see [`../multi-angle/README.md`](../multi-angle/README.md)). I didn't check whether the PID and `bulk_only` firmware log it the same way |
| `auger_rpm_cmd` | commanded auger speed (rpm). Battery fine rows: 30 rpm for each 45° step |
| `taps_cum` | taps so far in the dose (blank for `bulk_only`, which taps every 500 ms throughout) |
| `actuation` | the stage settings as printed on the console (battery), or the tap cadence (`bulk_only`) |
| `outdoor_temp_c`, `outdoor_rh_pct`, `outdoor_dewpoint_c` | outdoor temperature, relative humidity and dew point at that row's time |

`doses_summary.csv` adds `final_g`, `error_mg`, `status`, `reached_target`, `elapsed_s` (dose
command to the final reading), `n_readings`, `time_resolution`, `started_utc` (UTC at `t_s` =
0), `auger_rev`, `taps`, `stages` (cycles per stage), `source`, `run_qc_verdict`,
`run_valid_for_cross_powder`, `battery_version`, `attended`, `utc_from`, the tare's baseline,
drift and read noise (September battery runs), `notes` (link to the run notes, or the PID's
event times) and `file`.

## Things to know

- **Only salt and Al 4047 have a single continuous dispense to a target.** Every other powder
  was only dosed to a target by the battery's three-stage controller, so that is what the other
  ten picks are.
- **The battery readings are not continuous.** The bulk stage polls every 250 ms, but the
  console printed whole seconds, so 2–4 polls share each `t_s`. The fine and tap stages give one
  settled reading per step, 3–5 s apart. Only the PID and `bulk_only` doses have readings at a
  steady fast rate with sub-second times.
- **Readings go slightly negative after the tare.** The first bulk polls can read down to −38 mg,
  so check before treating a series as monotone.
- **Small doses have few readings.** A 0.05 g dose that overshot in one fine step has 1–3
  readings. The picks have 9 to 356.
- **Doses within a run were back to back.** Every battery run was unattended (`attended` = 0):
  the doser printed its prompt to empty the cup but didn't wait, so each dose tared the balance
  with the earlier doses still in the cup. `mass_g` is net of that tare.

## Temperature and humidity

The lab never recorded temperature or humidity: the doser and the balance have no sensor, and no
run record has a reading. As in the [single-dispense](../single-dispense) and
[multi-angle](../multi-angle) sets, the CSVs carry the **outdoor** weather instead: the reports of
Provo Municipal Airport (KPVU, about 7 km from campus), from the Iowa Environmental Mesonet's
ASOS archive, interpolated linearly to each row's time. Treat them as a rough covariate, not the
conditions at the balance.

## Timing

- PID: the document's note gives the start as 20:52 UTC, to the minute; `utc` is that plus `t_s`.
- `bulk_only`: the trial document's `started_utc` plus `t_s`.
- Battery: the console's `DOSE` line gives the doser's clock (ms since the run started) at the end
  of each dose, and the host logged the UTC start of each dose block. A block starts on the doser
  right after the previous block's last dose, or with its first dose if it is the first block, so
  each block gives the offset between the two clocks. The offsets are 1.8–4.4 s, and two blocks of
  the same run agree to within 0.4 s. Runs without block times use the median offset (2.41 s);
  `utc_from` says which. With the whole-second `t_s`, `utc` is good to about a second.

## Rebuilding

```bash
git fetch origin                                              # the pinned commits must be present
python3 data/assimilation/target-mass/extract.py --fetch      # recopy source/ and weather/ (needs MONGODB_URI)
python3 data/assimilation/target-mass/extract.py              # rebuild doses/ and the CSVs
```

The rebuild needs only the Python standard library. It checks every parsed battery dose against
the run's own `doses_*.csv` and its MongoDB document.
