# Powder runs that tested the doser at several tube angles (issue #210)

Issue [#210](https://github.com/vertical-cloud-lab/powder-doser/issues/210) asked whether the runs
already provided include runs that tested the doser at several angles. They do. The five battery
runs in [`../single-dispense`](../single-dispense) (salt, sodium sulfate, silicon −110/+200,
AlSi10Mg and barium chloride, 2026-08-20/21) each tested the tube at several angles, in the blocks
just before and after their Block D dispenses. Block D, the continuous single dispense, was at one
angle only. Every run of the uniform powder battery (issue #116) has these blocks:

| block | what the doser did at each angle | angles (tube above horizontal) |
|---|---|---|
| B "hold" | nothing for 15 s: does powder fall out on its own? | 0°, 22.5°, 45° |
| C "rotation" | six single 360° auger turns at 30 rpm, weighed after each | 0°, 22.5°, 45° |
| E "tap" | eight pairs of one 360° re-feed turn at 30 rpm, then one tap, each weighed | 0°, 22.5° |

The firmware logs these as tilt **settings** 0, 45 and 90. The tilt plate is geared 2:1, so the
tube's angle is half the setting: 0°, 22.5° and 45°. The run notes, written before this was
corrected on 2026-10-01, call the angles 0°, 45° and 90°.

Mass per auger turn rises with the tube angle for all five powders, by 4.8–8.6× from flat to 45°:

| powder | Block C, g per turn at 0° | 22.5° | 45° | Block E re-feed turn at 0° | 22.5° | outdoor temp / RH |
|---|---|---|---|---|---|---|
| salt | 0.0380 | 0.1465 | 0.2652 | 0.0403 | 0.1554 | 33.9 °C / 23 % |
| sodium sulfate | 0.0512 | 0.2084 | 0.2435 | 0.0410 | 0.1847 | 35.0 °C / 19 % |
| silicon −110/+200 | 0.0572 | 0.2107 | 0.3024 | 0.0557 | 0.1746 | 37.7 °C / 16 % |
| AlSi10Mg | 0.0489 | 0.2310 | 0.3389 | 0.0540 | 0.2758 | 26.6 °C / 34 % |
| barium chloride | 0.0233 | 0.1847 | 0.2004 | 0.0374 | 0.1908 | 32.6 °C / 26 % |

Each value is the mean of the six Block C turns, or of the eight Block E re-feed turns, at that
angle. The weather is at the start of Block B. No powder fell out on its own during the Block B
holds at any angle.

## Files

- **[`all_trials.csv`](all_trials.csv)**: every Block B, C and E row of the five runs in one file
  (328 rows: 265 measured actions and 63 discarded attempts, explained below).
- [`runs/<powder>.csv`](runs/): the same rows, one file per run.
- [`angle_summary.csv`](angle_summary.csv): one row per run, block, action and angle (50 rows),
  with the mean, SD, RSD, min, max and sum of the mass per action, the number of discarded
  attempts and of rows flagged `ok`, the times, temperature and humidity, and a link to the run
  notes.
- [`more_powders_trials.csv`](more_powders_trials.csv) and
  [`more_powders_summary.csv`](more_powders_summary.csv): the same blocks from nine more battery
  runs, with seven more powders and two earlier salt runs (see [More powders](#more-powders)).
- The five runs' raw files (serial log, trials, retries, run record, MongoDB document) are in
  [`../single-dispense/source/`](../single-dispense/source). The nine others are in
  [`source/`](source/), copied from commit `f754450` on branch `claude/issue-116-20260915-1622`,
  with each run's document from MongoDB `powder_doser.battery_runs` (read 2026-11-13). The raw
  serial logs of AlSi10Mg (2026-08-21) and brown rice flour aren't on any branch; their trials
  files, run records and MongoDB documents are.
- [`weather/`](weather/): the weather reports for 2026-08-04 to 08-12. The 2026-08-20/21 reports
  are in [`../single-dispense/weather/`](../single-dispense/weather).
- [`extract.py`](extract.py) rebuilds every CSV here (see [Rebuilding](#rebuilding)).

## Columns of the trial files

| column | meaning |
|---|---|
| `powder_id`, `run_id` | the powder and the battery run |
| `block` | `B`, `C` or `E` |
| `test` | `hold` (Block B), `turn` (Block C), `refeed_turn` or `tap` (Block E) |
| `tilt_setting` | the tilt as logged: 0, 45 or 90 |
| `tube_angle_deg` | the tube's angle above horizontal: 0, 22.5 or 45 |
| `trial` | the firmware's trial number at that angle: 0–5 in Block C, 0–7 in Block E, 0 in Block B |
| `row_type` | `trial` for a measured action. `discarded_attempt` for an action whose measurement the firmware threw away and repeated (see below) |
| `auger_turn_deg`, `auger_rpm` | 360 and 30 for a turn, empty otherwise |
| `taps`, `hold_s` | 1 for a tap; 15 for a hold |
| `t_device_ms` | the doser's clock, ms since the battery run started, when it wrote the row: just after the last reading of the after-window |
| `utc` | the same moment in UTC (see [Timing](#timing)) |
| `settled_before_g` | the balance's level before the action, carried forward to the time of `settled_after_g` along the drift measured before the action |
| `settled_after_g` | the balance's level after the action |
| `delta_g` | **the mass the action delivered**: `settled_after_g − settled_before_g`. For a discarded attempt, the mass it measured before it was thrown away |
| `cum_delta_g` | running sum of `delta_g` over the measured actions of that block and angle, so the mass delivered so far at that angle. Discarded attempts aren't added |
| `sigma_g` | the firmware's uncertainty of `delta_g` |
| `drift_g` | the drift correction applied to `settled_before_g` |
| `shock_g` | the total of the sudden jumps (over 10 mg between two readings with nothing moving) removed as bumps, not powder |
| `retries` | how many attempts were discarded before this measured action |
| `quality` | `ok`, `unsettled` (the readings scattered more than 1.5 mg about a fitted line) or `shock` (a jump had to be removed from one of the windows). For a discarded attempt, why it was discarded (`shock`) |
| `flag` | `lowflow` when a turn delivered under 0.5 mg (none in the five runs) |
| `outdoor_temp_c`, `outdoor_rh_pct`, `outdoor_dewpoint_c` | outdoor temperature, relative humidity and dew point at that row's time (see [Temperature and humidity](#temperature-and-humidity)) |

`more_powders_trials.csv` adds `battery_version` and `qc_verdict`.

## How each row was measured

Each action is bracketed by two windows of balance readings with nothing moving:

1. Before the action the firmware takes six readings 0.4 s apart and fits a straight line (the
   level, plus the balance's slow drift). If the window is disturbed it tries again, up to 8
   times, for a quiet one.
2. It acts: one auger turn at 30 rpm (about 2 s), one tap, or nothing for 15 s (Block B).
3. It keeps reading through a 2 s settle (15 s in Block B), then fits six more readings 0.4 s
   apart. `settled_after_g` is that fit at the middle of its window, and `settled_before_g` is the
   first line carried forward to the same moment.

So each action gives one settled level before and one after. **There is no continuous stream of
readings in these blocks**: the individual readings were used on the device and not logged. In
Block C the turns at one angle are 11.6 s apart (the median gap between rows), so the six turns at
an angle take about 70 s. The only continuous readings in these runs are Block D's, at 22.5° only
(the [single-dispense set](../single-dispense)).

## Things to know before using the data

- **The angles always ran in the same order**: 0°, then 22.5°, then 45° in Block C, and 0° then
  22.5° in Block E, a few minutes apart. Angle is therefore mixed up with time and with the state
  of the powder in the tube. Some sequences are still changing: barium chloride's Block C turns
  rise from 10 to 33 mg at 0° as the tube fills, and fall from 319 to 147 mg at 45°. Its
  [run notes](https://github.com/vertical-cloud-lab/powder-doser/blob/f754450/docs/battery-runs/2026-08-21-barium-chloride.md#block-c--feed-factor-vs-tilt)
  call the six turns at one angle "not six draws from one distribution". Block E's re-feed turns
  are the same action at the same angle, 5–10 minutes later, so they give a second estimate at 0°
  and 22.5°.
- **Discarded attempts.** When a jump of over 10 mg hit the after-window, the firmware threw the
  measurement away and repeated the action, up to twice. The auger still turned, so that powder is
  in the cup: it shows up in the next row's `settled_before_g` but not in `cum_delta_g`. There are
  63 discarded attempts in the five runs, 38 of them AlSi10Mg's, and none in barium chloride's.
- **Most rows are flagged.** Only 91 of the 265 measured actions are `ok`: 159 are `unsettled`
  and 15 `shock`. The balance was in a fume hood that week and the room was busy, except during
  barium chloride's run, when every action was `ok` and the holds read exactly 0.0000 g. Use
  `sigma_g` as each row's observation error.
- **The balance was mostly not zeroed between angles.** The runs were unattended, so nobody
  emptied the cup. The firmware tries to zero the balance before each block and angle, but skips
  it while the balance isn't reading stable, which was most of the time except in barium
  chloride's run. The settled levels therefore carry over from block to block, and jump where a
  zeroing did take. `delta_g` is unaffected.
- **Taps move very little.** The mean per tap is under 10 mg at every angle, and some means are
  negative, so below the noise. Barium chloride's quiet run resolved them: 0.1 mg per tap at 0°
  and 2.1 mg at 22.5°.
- **Block B found no spontaneous flow.** Barium chloride's holds read exactly 0.0000 g. The other
  runs' holds read between −34 and +120 mg, and all but one are flagged. Sodium sulfate's run
  notes put its +120 mg at 0° down to a bump during the hold, since a flat tube is the least
  likely to discharge. Powder only moves when the auger turns.

## Temperature and humidity

The lab never recorded temperature or humidity: the doser and the balance have no such sensor,
and no run record has a reading. As in the single-dispense set, the CSVs carry the **outdoor**
weather instead: hourly reports from Provo Municipal Airport (KPVU, 1369 m), about 7 km from
campus, interpolated linearly to the time of each row. They came from the Iowa Environmental
Mesonet's ASOS archive. Outdoors it was 26.6–37.8 °C and 16–34 % RH during the five runs, and
18.8–32.9 °C and 18–52 % RH during the nine others. Treat these as a rough covariate, not the
conditions at the balance.

## Timing

The doser's clock was converted to UTC from the times the host logged at the start of each block.
In the runs that have those times the offset is 2.11–2.13 s (battery version 1) or 2.33–2.61 s
(version 2), and the anchors within a run agree to within 0.03 s. Runs without block times (sodium
sulfate, AlSi10Mg, white rice flour and sodium alginate) use the median offset of their battery
version; `angle_summary.csv` says which.

## More powders

Nine more battery runs did the same Blocks B, C and E and passed their quality review. Seven are
powders not in the main set, and two are earlier salt runs. All are in
[`more_powders_trials.csv`](more_powders_trials.csv) (477 rows) and
[`more_powders_summary.csv`](more_powders_summary.csv), in the same columns:

| run | powder | Block C, g per turn at 0° | 22.5° | 45° | QC verdict |
|---|---|---|---|---|---|
| `20260804T211422Z_white-rice-flour` | white rice flour | 0.0037 | 0.0128 | 0.0372 | ok |
| `20260805T145725Z_sodium-alginate` | sodium alginate | 0.0008 | 0.0096 | 0.0109 | ok |
| `20260805T185305Z_brown-rice-flour` | brown rice flour (second auger) | 0.0003 | 0.0003 | 0.0002 | conveying slowly |
| `20260805T200002Z_calcium-lactate` | calcium lactate | 0.0473 | 0.1983 | 0.2323 | ok |
| `20260805T215252Z_carboxymethyl-cellulose` | carboxymethyl cellulose | 0.0026 | 0.0263 | 0.0094 | ok |
| `20260806T140254Z_xanthan-gum` | xanthan gum | 0.0237 | 0.1612 | 0.1868 | ok |
| `20260806T145120Z_salt` | salt | 0.0056 | 0.0171 | 0.0249 | ok |
| `20260812T215154Z_salt` | salt (repeat) | 0.0343 | 0.1754 | 0.2304 | ok |
| `20260821T161838Z_silicon-325` | silicon, −325 mesh | 0.0000 | 0.0000 | 0.0012 | conveying slowly |

- The first eight are **battery version 1** (2026-08-04 to 08-12). Version 1 weighed each action
  with one stable reading before and after, not a fitted window, so `sigma_g`, `drift_g`,
  `shock_g`, `retries` and `quality` are empty, and there were no discarded attempts. Its Block C
  turns are 6.4 s apart. Silicon −325 is version 2, like the main set.
- **The 2026-08-06 salt run's Block C is a lower bound.** Salt's feed rose during that run: its
  Block E re-feed turns delivered 2.7× as much as Block C at 22.5°. Its
  [notes](https://github.com/vertical-cloud-lab/powder-doser/blob/f754450/docs/battery-runs/2026-08-06-salt.md#the-drift-and-why-block-c-is-a-lower-bound)
  could not settle why. The 2026-08-12 repeat showed no such drift.
- **Carboxymethyl cellulose delivers less at 45° than at 22.5°.** At 45° its first turn delivered
  39 mg and the rest 1–7 mg. Its
  [notes](https://github.com/vertical-cloud-lab/powder-doser/blob/f754450/docs/battery-runs/2026-08-05-carboxymethyl-cellulose.md#block-c--the-feed-factor-peaks-at-45)
  put this down to the powder arching over the auger's intake when the tube is steep.
- Brown rice flour and silicon −325 barely moved at any angle (QC verdict "conveying slowly"),
  and white rice flour and sodium alginate delivered 1–37 mg per turn.

Five more runs with Block C were left out, because their angles or their feed can't be trusted:

| run | why it was left out |
|---|---|
| `20260804T204316Z_brown-rice-flour`, `20260804T224937Z_brown-rice-flour` | the auger conveyed essentially nothing at any angle (QC: auger suspect) |
| `20260811T183043Z_alsi10mg` | the tilt servos were broken and the tube stayed at 0° for the whole run, so it never tested another angle |
| `20260820T175631Z_salt` | an environment stress test, cut short (Block E only at 0°) |
| `20260821T182705Z_fumed-silica` | conveyed at most 0.25 mg per turn, and nobody could see whether the outlet was clear |

Their files are under `data/battery/` at commit `f754450`, and their documents are in
`battery_runs`.

## Continuous readings at several angles

Only salt, and briefly Al 4047, has continuous readings at more than one angle. These are the
closest data, none of them extracted here:

- **Salt, 0.5 g optimization campaigns** `salt-20260929T014732Z` (60 doses, 2026-09-29 to 10-06)
  and `salt-margin-20261013T191339Z` (43 doses, 2026-10-13 to 10-15). The tube angle of each
  stage changed from dose to dose (bulk 15–40°, trickle 10–30°, taps 0–15°), and the balance was
  read every control step. They use the three-stage controller. The trial documents are in
  MongoDB `opt_trials` and on branch `claude/issue-164-20260922-1928` under `data/opt/`. The
  [salt set](https://github.com/vertical-cloud-lab/powder-doser/tree/c68fc04/data/assimilation/salt-0p5g)
  from earlier in this issue is five of these doses, all at the same angles.
- **Al 4047, one-stage doses** (`bulk_only` mode, 2026-09-30 and 10-19/20): six doses at 40°, one
  at 60° and one at 75°. The 60° and 75° doses (0.5 g targets) stalled after 2.5 and 7.9 mg as
  the tube clogged. They are in the
  [new-controller set](https://github.com/vertical-cloud-lab/powder-doser/tree/9085f9a/data/assimilation/new-controller-powders)
  from earlier in this issue.
- **Salt, slow-speed stopping test** (2026-08-17): three-turn spins at 5–25 rpm with the balance
  streamed while the auger turns, at 55° (20 runs) and 25° (8 runs). Branch
  `claude/issue-130-20260721-1807`, `data/lowrpm-quantum/2026-08-17_salt/`.
- **Salt, taps at eight angles** (2026-07-31): ten taps at each angle from 0° to 70°, three
  times over, weighed after each tap rather than continuously. Same branch,
  `data/tap-characterization/2026-07-31_salt_angles/`.

The angles in these four are the tube's own (those firmwares take the plate angle directly).
To get continuous readings at several angles for several powders, Block D (or a single fixed-speed
spin) would have to be run at more than one tilt, which needs new runs on the doser.

## Rebuilding

```bash
git fetch origin                                          # the pinned commit f754450 must be present
python3 data/assimilation/multi-angle/extract.py --fetch  # recopy source/ and weather/ (MONGODB_URI for the database copies)
python3 data/assimilation/multi-angle/extract.py          # rebuild the CSVs
```

The rebuild needs only the Python standard library. It reads the five main runs from
`../single-dispense/source/`, and checks every Block B, C and E row and discarded attempt
against the MongoDB copy of its run.
