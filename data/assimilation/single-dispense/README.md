# Five powders, one continuous auger dispense each, with continuous balance readings (issue #210)

Issue [#210](https://github.com/vertical-cloud-lab/powder-doser/issues/210) asked for runs of five
different powders, with all their data, temperature and humidity in each run's CSV, a single
dispense rather than the three-stage controller, and continuous balance readings.

These runs come from **Block D ("speed") of the powder battery** (issue #116). In Block D the
auger turns continuously at one fixed speed, with the tube 22.5° above horizontal, while the
balance is read every 0.39 s. There is no controller at all: no bulk, fine or tap stages, no
feedback and no taps. Each run is one uninterrupted dispense. Every powder ran the same protocol
and settings (battery version 2) within 24 hours on 2026-08-20 and 2026-08-21. Each battery run
did three dispenses, at 15, 45 and 90 rpm, so there are 15 runs in all.

| powder | battery run | 15 rpm dispense | 45 rpm | 90 rpm | outdoor temp / RH |
|---|---|---|---|---|---|
| salt (NaCl) | `20260821T192031Z_salt` | [0.740 g](runs/salt_15rpm.csv) | [0.656 g](runs/salt_45rpm.csv) | [0.493 g](runs/salt_90rpm.csv) | 33.9 °C / 23 % |
| sodium sulfate (Na₂SO₄) | `20260820T192224Z_sodium-sulfate` | [1.270 g](runs/sodium-sulfate_15rpm.csv) | [0.791 g](runs/sodium-sulfate_45rpm.csv) | [0.657 g](runs/sodium-sulfate_90rpm.csv) | 35.1 °C / 19 % |
| silicon, −110/+200 mesh | `20260820T214823Z_silicon-110-200` | [0.914 g](runs/silicon-110-200_15rpm.csv) | [0.778 g](runs/silicon-110-200_45rpm.csv) | [0.631 g](runs/silicon-110-200_90rpm.csv) | 37.8 °C / 16 % |
| AlSi10Mg (AM alloy) | `20260821T151337Z_alsi10mg` | [1.067 g](runs/alsi10mg_15rpm.csv) | [0.921 g](runs/alsi10mg_45rpm.csv) | [0.547 g](runs/alsi10mg_90rpm.csv) | 27.0 °C / 34 % |
| barium chloride (BaCl₂) | `20260821T170712Z_barium-chloride` | [0.783 g](runs/barium-chloride_15rpm.csv) | [0.135 g](runs/barium-chloride_45rpm.csv) | [0.409 g](runs/barium-chloride_90rpm.csv) | 32.7 °C / 26 % |

The masses are the settled mass delivered by each dispense. **The 15 rpm runs are the five to
start with.** Each is the first dispense of its block and the longest: 48 readings over 18.4 s.
The 45 rpm runs have 16 readings over 6.1 s, and the 90 rpm runs 8 readings over 3.1 s.
Barium chloride's 45 and 90 rpm runs are not comparable with the rest: at 45 rpm its feed stopped
after 1.5 s. Its
[run notes](https://github.com/vertical-cloud-lab/powder-doser/blob/f754450/docs/battery-runs/2026-08-21-barium-chloride.md#block-d--per-speed-split-unusable-for-this-powder)
give two possible causes and can't tell them apart: the 15 rpm run emptied the outlet, or powder
from one run landed in the next.

## Files

- **[`all_runs.csv`](all_runs.csv)**: every row of all 15 runs in one file (390 rows).
- [`runs/<powder>_<rpm>rpm.csv`](runs/): one file per run, in the same columns.
- [`runs_summary.csv`](runs_summary.csv): one row per run (15 rows), with the start time, readings,
  estimated auger turns, settled masses, the balance's quality flags, temperature and humidity,
  operator and run notes.
- [`source/<battery run>/`](source/): everything the doser recorded for each battery run, Blocks A
  to E, as committed at `f754450` on branch `claude/issue-116-20260915-1622`:
  - `raw_serial_*.log`: the raw serial session
  - `polls_*.csv`: the continuous readings
  - `trials_*.csv`: every settled measurement of every block
  - `run_*.json`: the whole run record
  - `summary_*.csv`, `timeline_*.csv`, `retries_*.csv`, `doses_*.csv` (empty, as no dose block ran)
  - `mongodb_battery_runs.json`: the run's document in MongoDB `powder_doser.battery_runs`
    (read 2026-11-12)

  The PNG figures were left out. They are still at the pinned commit.
- [`weather/`](weather/): the hourly weather reports used for temperature and humidity.
- [`extract.py`](extract.py) rebuilds everything here (see [Rebuilding](#rebuilding)).

Run notes, written at the time, are at the pinned commit:
[salt](https://github.com/vertical-cloud-lab/powder-doser/blob/f754450/docs/battery-runs/2026-08-21-salt-control-repeat.md),
[sodium sulfate](https://github.com/vertical-cloud-lab/powder-doser/blob/f754450/docs/battery-runs/2026-08-20-sodium-sulfate.md),
[silicon](https://github.com/vertical-cloud-lab/powder-doser/blob/f754450/docs/battery-runs/2026-08-20-silicon-110-200.md),
[AlSi10Mg](https://github.com/vertical-cloud-lab/powder-doser/blob/f754450/docs/battery-runs/2026-08-21-alsi10mg.md),
[barium chloride](https://github.com/vertical-cloud-lab/powder-doser/blob/f754450/docs/battery-runs/2026-08-21-barium-chloride.md).
The runs were livestreamed. The
[run log](https://github.com/vertical-cloud-lab/powder-doser/blob/f754450/docs/battery-runs/run-log.csv)
links each to its recording, at an approximate start time.

## Columns of the run files

| column | meaning |
|---|---|
| `powder_id`, `run_id`, `dispense_id` | the powder, the battery run it came from, and `<powder>_<rpm>rpm` |
| `auger_rpm` | auger speed, constant for the whole run |
| `tilt_deg`, `tube_angle_deg` | the tilt setting as logged (45), and the tube's physical angle above horizontal (22.5°). The tilt plate is geared 2:1, so the angle is half the setting; the firmware docs were corrected for this on 2026-10-01 |
| `row_type` | `settled_before`: the balance's settled level just before the auger started. `reading`: one instantaneous reading while the auger turns. `settled_after`: the settled level after the auger stopped |
| `t_s` | seconds since the auger started (estimated as one poll period before the first reading) |
| `t_device_ms` | the doser's own clock, ms since the battery run started. Empty for `settled_before`, which the firmware doesn't time-stamp |
| `utc` | UTC time of the row (see [Timing](#timing)) |
| `balance_g` | the balance reading in g, as logged |
| `mass_g` | `balance_g` minus the `settled_before` level: **the mass dispensed so far in this run** |
| `stable` | the balance's own stability flag on that reading (1 = stable). Nearly always 0 while the auger turns |
| `auger_on` | 1 while the auger is turning (every `reading` row), 0 otherwise |
| `outdoor_temp_c`, `outdoor_rh_pct`, `outdoor_dewpoint_c` | outdoor temperature, relative humidity and dew point at the start of the run (see [Temperature and humidity](#temperature-and-humidity)). The same value on every row of a run |

`runs_summary.csv` adds the start time in UTC and lab time (MDT, UTC−6), the number of readings,
the poll period, the estimated time the auger ran and turns it made, the settled masses, the last
reading, how much the balance gained after the auger stopped (`gain_after_stop_g`), the fitted
brackets' noise, drift, shock and quality flags (`ok`, `unsettled` or `shock`), the weather
reports used, the operator and the run notes.

## Things to know before using the data

- **There was no target mass.** Each run is a fixed speed for a fixed time: the auger was told to
  turn 3 times. A Block D run is therefore "a single dispense" with an open-loop stopping rule, not
  a dispense that stopped on reaching a mass. The five powders delivered 0.14–1.27 g per run.
- **The auger turned about 4.6 times, not 3.** The firmware counts only the 250 ms sleeps between
  readings toward the run time, not the ~136 ms each loop spends reading the balance. So the auger
  ran 48 × 0.386 s = 18.4 s at 15 rpm instead of 12 s, and likewise at 45 and 90 rpm.
  `auger_revs_est` in the summary is the corrected figure. The same runs' single-turn trials
  (Block C, same tilt) agree: the 15 rpm mass divided by 4.6 turns is within 10 % of the
  Block C yield per turn for four powders (0.161 vs 0.146 g for salt, 0.232 vs 0.231 g for
  AlSi10Mg) and 33 % high for sodium sulfate. Divided by 3, all five are 41–103 % high. Where
  the run notes quote Block D in mg/rev, they divided by 3.
- **Readings stop when the auger stops.** The firmware streams the balance only while the auger
  turns. It then samples through a 2 s settle and fits a window of 6 readings 0.4 s apart, with
  shocks removed. That fitted level is the `settled_after` row, about 5 s after the last reading.
  Powder still in flight and the balance's lag land in that gap: `gain_after_stop_g` is −4 to
  +109 mg at 15 rpm and 139–242 mg at 90 rpm.
- **The readings are instantaneous and noisy.** The balance is an A&D HR-100A (0.1 mg
  readability), in a fume hood that week. A survey on 2026-08-20 put its error over 180 s windows
  at 18–21 mg there. The first readings of some runs dip below zero (salt at 15 rpm reaches
  −31 mg) as the auger starts.
- **The balance wasn't zeroed between the three speeds.** At the start of Block D the tare was
  skipped in four of the five runs because the balance was unstable (all but barium chloride). So `balance_g` still includes
  the powder from earlier blocks and runs. `mass_g` takes care of this.
- **AlSi10Mg's raw serial log was never committed.** Its readings and settled values come from
  `run_alsi10mg.json`, which was rebuilt from that log, and match MongoDB.

## Temperature and humidity

**The lab never recorded temperature or humidity.** The doser has no such sensor, the HR-100A
has none, and none of MongoDB `powder_doser`, any branch of this repo or any run log has a
reading.

So the CSVs carry the **outdoor** weather instead: hourly reports (METAR) from Provo Municipal
Airport (KPVU, 1369 m), about 7 km from the BYU campus, interpolated linearly to the start of each
run. They came from the Iowa Environmental Mesonet's ASOS archive. The raw reports are in
[`weather/`](weather/).

Use them as a covariate, not as the conditions at the balance. It was 27–38 °C and 16–34 % RH
outside during these runs, and an indoor lab is normally held much cooler. If the room was near
22 °C and its air held as much water as the outside air (dew point 7.8–10.4 °C), its humidity
would have been about 40–48 % RH. Nothing measured that, though.

## Timing

The doser's clock (`t_device_ms`) was converted to UTC from the times the host logged at the start
of each block. In the three runs that have those times (salt, silicon and barium chloride) the
offset is 2.34–2.36 s, and the Block D and Block E anchors agree to 0.01 s. The sodium sulfate
and AlSi10Mg records have no block times, so their UTC uses the run start plus the median offset,
2.35 s. That is a few tenths of a second uncertain at most, far finer than the hourly weather
reports.

## More runs like these

- **More powders, older battery version (1).** Block D also ran on calcium lactate (0.57 g at
  15 rpm), xanthan gum (0.70 g), AlSi10Mg (0.35 g), salt (0.15 and 0.71 g), carboxymethyl cellulose
  (0.07 g), white rice flour (0.06 g) and sodium alginate (0.03 g), on 2026-08-04 to 2026-08-12.
  Those readings are 0.29 s apart and the auger made about 3.4 turns. The files are under
  `data/battery/` at `f754450`, and the same records are in `battery_runs`.
- **Poor feeders.** Fumed silica and silicon −325 mesh ran Block D on 2026-08-21 but barely moved
  (under 30 mg), and brown rice flour (version 1) moved nothing.
- **A single dispense that stops on mass.** The only one on file is the `bulk_only` mode of the
  `trickle_tap` firmware, which ran only on Al 4047 (October 2026). It is one stage at a fixed
  tilt, but it slows the auger near the target and taps on a fixed cadence. Two of its eight doses
  finished `ok`: 0.3189 g (`56a01060`) and 1.1012 g (`5851b6d6`). They are on branch
  `claude/issue-210-20261112-0137` under `data/assimilation/new-controller-powders/`.

## Rebuilding

```bash
git fetch origin                                             # the pinned commit f754450 must be present
python3 data/assimilation/single-dispense/extract.py --fetch # recopy source/ and weather/ (MONGODB_URI for the database copies)
python3 data/assimilation/single-dispense/extract.py         # rebuild runs/, all_runs.csv and runs_summary.csv
```

The rebuild needs only the Python standard library. It checks that every reading and Block D
settled mass matches the MongoDB copy.
