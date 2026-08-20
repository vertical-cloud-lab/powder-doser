# Powder-doser run log

Every battery run on the bench rig, newest first: when it ran, what it ran, how much powder went through, and where the data and the video are. Issue [#116](https://github.com/vertical-cloud-lab/powder-doser/issues/116).

**Generated file -- do not edit by hand.** Rebuild with `python scripts/build_run_log.py` after each run (and `python scripts/refresh_stream_broadcasts.py` first if the run is on a broadcast newer than the listing). The same rows are in [`run-log.csv`](run-log.csv).

15 entries, 10 valid for cross-powder comparison. All times UTC; the lab is on MDT (UTC-6), given alongside per run below.

## Runs

| Start (UTC) | End | Dur | Powder | Blocks | Speeds (RPM) | Dispensed | Feed @90 deg | Doses | Environment | QC | Data | Video |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2026-08-20 21:48 | 2026-08-20 22:03 | 15:05 | `silicon-110-200` | ABCDE | C/E 30 · D 15/45/90 RPM | 7.72 g | 302.35 mg/rev | -- | sigma 7.9 mg, 9 shocks, 12 retries | valid<br>`ok` | [dir](https://github.com/vertical-cloud-lab/powder-doser/tree/main/data/battery/20260820T214823Z_silicon-110-200) · [notes](https://github.com/vertical-cloud-lab/powder-doser/blob/main/docs/battery-runs/2026-08-20-silicon-110-200.md) | [~1 min](https://youtu.be/23PlXoQgjPQ?t=10088) |
| 2026-08-20 19:22 | 2026-08-20 19:35 | 13:10 | `sodium-sulfate` | ABCDE | C/E 30 · D 15/45/90 RPM | 7.91 g | 243.55 mg/rev | -- | sigma 5.9 mg, 9 shocks, 3 retries | valid<br>`ok` | [dir](https://github.com/vertical-cloud-lab/powder-doser/tree/main/data/battery/20260820T192224Z_sodium-sulfate) · [notes](https://github.com/vertical-cloud-lab/powder-doser/blob/main/docs/battery-runs/2026-08-20-sodium-sulfate.md) | [~1 min](https://youtu.be/23PlXoQgjPQ?t=1329) |
| 2026-08-20 17:56 | 2026-08-20 18:24 | 27:39 | `salt` | ABCDE | C/E 30 · D 15/45/90 RPM | 4.56 g | 208.48 mg/rev | -- | sigma 12.4 mg, 36 shocks, 57 retries | excluded<br>`environment-stress-test` | [dir](https://github.com/vertical-cloud-lab/powder-doser/tree/main/data/battery/20260820T175631Z_salt) · [notes](https://github.com/vertical-cloud-lab/powder-doser/blob/main/docs/battery-runs/2026-08-20-salt-artifact-rejection.md) | [~1 min](https://youtu.be/_1u-y15Z5q8?t=24976) |
| 2026-08-12 21:51 | 2026-08-12 22:07 | 15:13 | `salt` | ABCDEG | C/E 30 · D 15/45/90 RPM | 8.89 g | 230.42 mg/rev | 3x, 3 ok, mean -4.1 mg | not recorded | valid<br>`ok` | [dir](https://github.com/vertical-cloud-lab/powder-doser/tree/main/data/battery/20260812T215154Z_salt) · [notes](https://github.com/vertical-cloud-lab/powder-doser/blob/main/docs/battery-runs/2026-08-12-salt-repeat.md) | [~1 min](https://youtu.be/k9gPANBiMjU?t=10299) |
| 2026-08-11 18:30 | 2026-08-11 18:53 | 22:24 | `alsi10mg` | ABCDEG | C/E 30 · D 15/45/90 RPM | 5.97 g | 68.30 mg/rev | 3x, 0 ok, mean -19.6 mg | not recorded | excluded<br>`no-tilt-servo-fault` | [dir](https://github.com/vertical-cloud-lab/powder-doser/tree/main/data/battery/20260811T183043Z_alsi10mg) · [notes](https://github.com/vertical-cloud-lab/powder-doser/blob/main/docs/battery-runs/2026-08-11-alsi10mg.md) | [~1 min](https://youtu.be/3UlVz61aPAE?t=27028) |
| 2026-08-06 14:51 | 2026-08-06 15:07 | 16:37 | `salt` | ABCDEG | C/E 30 · D 15/45/90 RPM | 4.01 g | 24.90 mg/rev | 3x, 2 ok, mean +0.2 mg | not recorded | valid<br>`ok` | [dir](https://github.com/vertical-cloud-lab/powder-doser/tree/main/data/battery/20260806T145120Z_salt) · [notes](https://github.com/vertical-cloud-lab/powder-doser/blob/main/docs/battery-runs/2026-08-06-salt.md) | [~1 min](https://youtu.be/UDCxlnSBsLg?t=13865) |
| 2026-08-06 14:02 | 2026-08-06 14:19 | 16:12 | `xanthan-gum` | ABCDEG | C/E 30 · D 15/45/90 RPM | 7.88 g | 186.77 mg/rev | 3x, 0 ok, mean -32.9 mg | not recorded | valid<br>`ok` | [dir](https://github.com/vertical-cloud-lab/powder-doser/tree/main/data/battery/20260806T140254Z_xanthan-gum) · [notes](https://github.com/vertical-cloud-lab/powder-doser/blob/main/docs/battery-runs/2026-08-06-xanthan-gum.md) | [~1 min](https://youtu.be/UDCxlnSBsLg?t=10959) |
| 2026-08-05 21:52 | 2026-08-05 22:33 | 40:12 | `carboxymethyl-cellulose` | ABCDEG | C/E 30 · D 15/45/90 RPM | 3.56 g | 9.35 mg/rev | 3x, 0 ok, mean -43.2 mg | not recorded | valid<br>`ok` | [dir](https://github.com/vertical-cloud-lab/powder-doser/tree/main/data/battery/20260805T215252Z_carboxymethyl-cellulose) · [notes](https://github.com/vertical-cloud-lab/powder-doser/blob/main/docs/battery-runs/2026-08-05-carboxymethyl-cellulose.md) | [~1 min](https://youtu.be/_iDB8z83GdQ?t=10357) |
| 2026-08-05 21:12 | -- | -- | `carboxymethyl-cellulose` | -- | -- | -- | -- | -- | not recorded | excluded<br>`mechanical-no-feed: delivery end taped` | [dir](https://github.com/vertical-cloud-lab/powder-doser/tree/main/data/battery/20260805T211216Z_carboxymethyl-cellulose_preflight) · [notes](https://github.com/vertical-cloud-lab/powder-doser/blob/main/docs/battery-runs/2026-08-05-carboxymethyl-cellulose-aborted.md) | [~1 min](https://youtu.be/_iDB8z83GdQ?t=7921) |
| 2026-08-05 20:00 | 2026-08-05 20:19 | 19:22 | `calcium-lactate` | ABCDEG | C/E 30 · D 15/45/90 RPM | 9.04 g | 232.25 mg/rev | 3x, 0 ok, mean -26.5 mg | not recorded | valid<br>`ok` | [dir](https://github.com/vertical-cloud-lab/powder-doser/tree/main/data/battery/20260805T200002Z_calcium-lactate) · [notes](https://github.com/vertical-cloud-lab/powder-doser/blob/main/docs/battery-runs/2026-08-05-calcium-lactate.md) | [~1 min](https://youtu.be/_iDB8z83GdQ?t=3587) |
| 2026-08-05 18:53 | 2026-08-05 19:00 | 7:07 | `brown-rice-flour` | ABCDEG | C/E 30 · D 15/45/90 RPM | 0.03 g | 0.20 mg/rev | 3x, 0 ok, mean -999.1 mg | not recorded | valid<br>`conveying-slowly` | [dir](https://github.com/vertical-cloud-lab/powder-doser/tree/main/data/battery/20260805T185305Z_brown-rice-flour) · [notes](https://github.com/vertical-cloud-lab/powder-doser/blob/main/docs/battery-runs/2026-08-05-brown-rice-flour-auger2.md) | [~1 min](https://youtu.be/5ENY3XL4yhc?t=28370) |
| 2026-08-05 14:57 | 2026-08-05 15:46 | 48:43 | `sodium-alginate` | ABCDEG | C/E 30 · D 15/45/90 RPM | 2.46 g | 10.87 mg/rev | 3x, 0 ok, mean -291.5 mg | not recorded | valid<br>`ok` | [dir](https://github.com/vertical-cloud-lab/powder-doser/tree/main/data/battery/20260805T145725Z_sodium-alginate) · [notes](https://github.com/vertical-cloud-lab/powder-doser/blob/main/docs/battery-runs/2026-08-05-sodium-alginate.md) | [~1 min](https://youtu.be/5ENY3XL4yhc?t=14230) |
| 2026-08-04 22:49 | 2026-08-04 22:56 | 6:57 | `brown-rice-flour` | ABCDEG | C/E 30 · D 15/45/90 RPM | 0.00 g | 0.00 mg/rev | 3x, 0 ok, mean -1000.0 mg | not recorded | excluded<br>`no-conveyance-auger-suspect` | [dir](https://github.com/vertical-cloud-lab/powder-doser/tree/main/data/battery/20260804T224937Z_brown-rice-flour) · [notes](https://github.com/vertical-cloud-lab/powder-doser/blob/main/docs/battery-runs/2026-08-04-brown-rice-flour-rerun.md) | [exact](https://youtu.be/w1D5DRiHFWM?t=13696) |
| 2026-08-04 21:14 | 2026-08-04 22:02 | 47:49 | `white-rice-flour` | ABCDEG | C/E 30 · D 15/45/90 RPM | 3.25 g | 37.15 mg/rev | 3x, 0 ok, mean -137.9 mg | not recorded | valid<br>`ok` | [dir](https://github.com/vertical-cloud-lab/powder-doser/tree/main/data/battery/20260804T211422Z_white-rice-flour) · [notes](https://github.com/vertical-cloud-lab/powder-doser/blob/main/docs/battery-runs/2026-08-04-white-rice-flour.md) | [exact](https://youtu.be/w1D5DRiHFWM?t=7981) |
| 2026-08-04 20:43 | 2026-08-04 20:50 | 7:04 | `brown-rice-flour` | ABCDEG | C/E 30 · D 15/45/90 RPM | 0.01 g | 0.10 mg/rev | 3x, 0 ok, mean -999.4 mg | not recorded | excluded<br>`no-conveyance-auger-suspect` | [dir](https://github.com/vertical-cloud-lab/powder-doser/tree/main/data/battery/20260804T204316Z_brown-rice-flour) · [notes](https://github.com/vertical-cloud-lab/powder-doser/blob/main/docs/battery-runs/2026-08-04-brown-rice-flour.md) | [exact](https://youtu.be/w1D5DRiHFWM?t=6115) |

## Per-run detail

### 2026-08-20 21:48 UTC -- silicon-110-200

- **Window** 2026-08-20T21:48:23.367756+00:00 -> 2026-08-20T22:03:28.536486+00:00  (15:05)
- **Lab clock** 2026-08-20 15:48:23 MDT -> 2026-08-20 16:03:28 MDT
- **Powder** silicon powder, -110/+200 mesh  ·  batch `metal-2026-08`  ·  operator swcharles (loaded), claude (remote)
- **Tests** blocks ABCDE  ·  64 measured trials  ·  C/E 30 · D 15/45/90 RPM
- **Dispensed** 7.7190 g
- **Feed factor (block C)** 0 deg 57.17 mg/rev  ·  45 deg 210.70 mg/rev  ·  90 deg 302.35 mg/rev
- **Pre-flight** feed confirmed
- **Environment** sigma 7.9 mg, 9 shocks, 12 retries
- **QC** valid -- `ok`
- **Data** [data/battery/20260820T214823Z_silicon-110-200](https://github.com/vertical-cloud-lab/powder-doser/tree/main/data/battery/20260820T214823Z_silicon-110-200)
- **Notes** [docs/battery-runs/2026-08-20-silicon-110-200.md](https://github.com/vertical-cloud-lab/powder-doser/blob/main/docs/battery-runs/2026-08-20-silicon-110-200.md)
- **Video** [https://youtu.be/23PlXoQgjPQ?t=10088](https://youtu.be/23PlXoQgjPQ?t=10088) -- accurate to about a minute

### 2026-08-20 19:22 UTC -- sodium-sulfate

- **Window** 2026-08-20T19:22:24.995883+00:00 -> 2026-08-20T19:35:40.211022+00:00  (13:10)
- **Powder** sodium sulfate (Na2SO4), non-toxic, first beyond salt  ·  batch `inorganic-2026-08`  ·  operator swcharles
- **Tests** blocks ABCDE  ·  64 measured trials  ·  C/E 30 · D 15/45/90 RPM
- **Dispensed** 7.9117 g
- **Feed factor (block C)** 0 deg 51.20 mg/rev  ·  45 deg 208.40 mg/rev  ·  90 deg 243.55 mg/rev
- **Pre-flight** feed confirmed
- **Environment** sigma 5.9 mg, 9 shocks, 3 retries
- **QC** valid -- `ok`
- **Data** [data/battery/20260820T192224Z_sodium-sulfate](https://github.com/vertical-cloud-lab/powder-doser/tree/main/data/battery/20260820T192224Z_sodium-sulfate)
- **Notes** [docs/battery-runs/2026-08-20-sodium-sulfate.md](https://github.com/vertical-cloud-lab/powder-doser/blob/main/docs/battery-runs/2026-08-20-sodium-sulfate.md)
- **Video** [https://youtu.be/23PlXoQgjPQ?t=1329](https://youtu.be/23PlXoQgjPQ?t=1329) -- accurate to about a minute

### 2026-08-20 17:56 UTC -- salt

- **Window** 2026-08-20T17:56:31Z -> 2026-08-20T18:24:00Z  (27:39)
- **Powder** salt (control; battery_version 2 artifact rejection)  ·  batch `food-safe-2026-08`  ·  operator swcharles
- **Tests** blocks ABCDE  ·  48 measured trials  ·  C/E 30 · D 15/45/90 RPM
- **Dispensed** 4.5588 g
- **Feed factor (block C)** 0 deg 50.42 mg/rev  ·  45 deg 155.00 mg/rev  ·  90 deg 208.48 mg/rev
- **Pre-flight** feed confirmed
- **Environment** sigma 12.4 mg, 36 shocks, 57 retries
- **QC** excluded -- `environment-stress-test`
- **Data** [data/battery/20260820T175631Z_salt](https://github.com/vertical-cloud-lab/powder-doser/tree/main/data/battery/20260820T175631Z_salt)
- **Notes** [docs/battery-runs/2026-08-20-salt-artifact-rejection.md](https://github.com/vertical-cloud-lab/powder-doser/blob/main/docs/battery-runs/2026-08-20-salt-artifact-rejection.md)
- **Video** [https://youtu.be/_1u-y15Z5q8?t=24976](https://youtu.be/_1u-y15Z5q8?t=24976) -- accurate to about a minute

### 2026-08-12 21:51 UTC -- salt

- **Window** 2026-08-12T21:51:54.498951+00:00 -> 2026-08-12T22:07:07.796058+00:00  (15:13)
- **Lab clock** 2026-08-12 15:51:54 MDT -> 2026-08-12 16:07:07 MDT
- **Powder** salt (food-safe batch), repeat run  ·  batch `food-safe-2026-08`  ·  operator sc
- **Tests** blocks ABCDEG  ·  64 measured trials  ·  C/E 30 · D 15/45/90 RPM
- **Dispensed** 8.8914 g
- **Feed factor (block C)** 0 deg 34.30 mg/rev  ·  45 deg 175.35 mg/rev  ·  90 deg 230.42 mg/rev
- **Closed-loop doses** 3x, 3 ok, mean -4.1 mg
- **Pre-flight** feed confirmed
- **Environment** not recorded
- **QC** valid -- `ok`
- **Data** [data/battery/20260812T215154Z_salt](https://github.com/vertical-cloud-lab/powder-doser/tree/main/data/battery/20260812T215154Z_salt)
- **Notes** [docs/battery-runs/2026-08-12-salt-repeat.md](https://github.com/vertical-cloud-lab/powder-doser/blob/main/docs/battery-runs/2026-08-12-salt-repeat.md)
- **Video** [https://youtu.be/k9gPANBiMjU?t=10299](https://youtu.be/k9gPANBiMjU?t=10299) -- accurate to about a minute

### 2026-08-11 18:30 UTC -- alsi10mg

- **Window** 2026-08-11T18:30:43.564056+00:00 -> 2026-08-11T18:53:08.395481+00:00  (22:24)
- **Lab clock** 2026-08-11 12:30:43 MDT -> 2026-08-11 12:53:08 MDT
- **Powder** AlSi10Mg (aluminum-silicon-magnesium AM metal powder, non-food-safe)  ·  batch `metal-2026-08`
- **Tests** blocks ABCDEG  ·  64 measured trials  ·  C/E 30 · D 15/45/90 RPM
- **Dispensed** 5.9716 g
- **Feed factor (block C)** 0 deg 82.60 mg/rev  ·  45 deg 75.55 mg/rev  ·  90 deg 68.30 mg/rev
- **Closed-loop doses** 3x, 0 ok, mean -19.6 mg
- **Pre-flight** feed confirmed
- **Environment** not recorded
- **QC** excluded -- `no-tilt-servo-fault`
- **Data** [data/battery/20260811T183043Z_alsi10mg](https://github.com/vertical-cloud-lab/powder-doser/tree/main/data/battery/20260811T183043Z_alsi10mg)
- **Notes** [docs/battery-runs/2026-08-11-alsi10mg.md](https://github.com/vertical-cloud-lab/powder-doser/blob/main/docs/battery-runs/2026-08-11-alsi10mg.md)
- **Video** [https://youtu.be/3UlVz61aPAE?t=27028](https://youtu.be/3UlVz61aPAE?t=27028) -- accurate to about a minute

### 2026-08-06 14:51 UTC -- salt

- **Window** 2026-08-06T14:51:20.847638+00:00 -> 2026-08-06T15:07:58.396290+00:00  (16:37)
- **Lab clock** 2026-08-06 08:51:20 MDT -> 2026-08-06 09:07:58 MDT
- **Powder** sodium chloride (table salt), food-safe batch  ·  batch `food-safe-2026-08`  ·  operator swcharles (loaded), claude (remote)
- **Tests** blocks ABCDEG  ·  64 measured trials  ·  C/E 30 · D 15/45/90 RPM
- **Dispensed** 4.0081 g
- **Feed factor (block C)** 0 deg 5.60 mg/rev  ·  45 deg 17.10 mg/rev  ·  90 deg 24.90 mg/rev
- **Closed-loop doses** 3x, 2 ok, mean +0.2 mg
- **Pre-flight** feed confirmed
- **Environment** not recorded
- **QC** valid -- `ok`
- **Data** [data/battery/20260806T145120Z_salt](https://github.com/vertical-cloud-lab/powder-doser/tree/main/data/battery/20260806T145120Z_salt)
- **Notes** [docs/battery-runs/2026-08-06-salt.md](https://github.com/vertical-cloud-lab/powder-doser/blob/main/docs/battery-runs/2026-08-06-salt.md)
- **Video** [https://youtu.be/UDCxlnSBsLg?t=13865](https://youtu.be/UDCxlnSBsLg?t=13865) -- accurate to about a minute

### 2026-08-06 14:02 UTC -- xanthan-gum

- **Window** 2026-08-06T14:02:54.080499+00:00 -> 2026-08-06T14:19:06.486063+00:00  (16:12)
- **Lab clock** 2026-08-06 08:02:54 MDT -> 2026-08-06 08:19:06 MDT
- **Powder** xanthan gum (food-safe batch)  ·  batch `food-safe-2026-08`  ·  operator claude
- **Tests** blocks ABCDEG  ·  64 measured trials  ·  C/E 30 · D 15/45/90 RPM
- **Dispensed** 7.8836 g
- **Feed factor (block C)** 0 deg 23.72 mg/rev  ·  45 deg 161.18 mg/rev  ·  90 deg 186.77 mg/rev
- **Closed-loop doses** 3x, 0 ok, mean -32.9 mg
- **Pre-flight** feed confirmed
- **Environment** not recorded
- **QC** valid -- `ok`
- **Data** [data/battery/20260806T140254Z_xanthan-gum](https://github.com/vertical-cloud-lab/powder-doser/tree/main/data/battery/20260806T140254Z_xanthan-gum)
- **Notes** [docs/battery-runs/2026-08-06-xanthan-gum.md](https://github.com/vertical-cloud-lab/powder-doser/blob/main/docs/battery-runs/2026-08-06-xanthan-gum.md)
- **Video** [https://youtu.be/UDCxlnSBsLg?t=10959](https://youtu.be/UDCxlnSBsLg?t=10959) -- accurate to about a minute

### 2026-08-05 21:52 UTC -- carboxymethyl-cellulose

- **Window** 2026-08-05T21:52:52.010546+00:00 -> 2026-08-05T22:33:04.131782+00:00  (40:12)
- **Lab clock** 2026-08-05 15:52:52 MDT -> 2026-08-05 16:33:04 MDT
- **Powder** carboxymethyl cellulose (food-safe batch)  ·  batch `food-safe-2026-08`  ·  operator swcharles
- **Tests** blocks ABCDEG  ·  64 measured trials  ·  C/E 30 · D 15/45/90 RPM
- **Dispensed** 3.5647 g
- **Feed factor (block C)** 0 deg 2.58 mg/rev  ·  45 deg 26.35 mg/rev  ·  90 deg 9.35 mg/rev
- **Closed-loop doses** 3x, 0 ok, mean -43.2 mg
- **Pre-flight** feed confirmed after extended charging
- **Environment** not recorded
- **QC** valid -- `ok`
- **Data** [data/battery/20260805T215252Z_carboxymethyl-cellulose](https://github.com/vertical-cloud-lab/powder-doser/tree/main/data/battery/20260805T215252Z_carboxymethyl-cellulose)
- **Notes** [docs/battery-runs/2026-08-05-carboxymethyl-cellulose.md](https://github.com/vertical-cloud-lab/powder-doser/blob/main/docs/battery-runs/2026-08-05-carboxymethyl-cellulose.md)
- **Video** [https://youtu.be/_iDB8z83GdQ?t=10357](https://youtu.be/_iDB8z83GdQ?t=10357) -- accurate to about a minute

### 2026-08-05 21:12 UTC -- carboxymethyl-cellulose

- **Window** 2026-08-05T21:12:16+00:00 -> (none)  (--)
- **Tests** blocks (none)  ·  0 measured trials  ·  n/a
- **Pre-flight** mechanical-no-feed: delivery end taped
- **Environment** not recorded
- **QC** excluded -- `mechanical-no-feed: delivery end taped`
- **Data** [data/battery/20260805T211216Z_carboxymethyl-cellulose_preflight](https://github.com/vertical-cloud-lab/powder-doser/tree/main/data/battery/20260805T211216Z_carboxymethyl-cellulose_preflight)
- **Notes** [docs/battery-runs/2026-08-05-carboxymethyl-cellulose-aborted.md](https://github.com/vertical-cloud-lab/powder-doser/blob/main/docs/battery-runs/2026-08-05-carboxymethyl-cellulose-aborted.md)
- **Video** [https://youtu.be/_iDB8z83GdQ?t=7921](https://youtu.be/_iDB8z83GdQ?t=7921) -- accurate to about a minute

### 2026-08-05 20:00 UTC -- calcium-lactate

- **Window** 2026-08-05T20:00:02.433141+00:00 -> 2026-08-05T20:19:24.951069+00:00  (19:22)
- **Powder** calcium lactate (food-safe batch)  ·  batch `food-safe-2026-08`  ·  operator swcharles
- **Tests** blocks ABCDEG  ·  64 measured trials  ·  C/E 30 · D 15/45/90 RPM
- **Dispensed** 9.0390 g
- **Feed factor (block C)** 0 deg 47.32 mg/rev  ·  45 deg 198.28 mg/rev  ·  90 deg 232.25 mg/rev
- **Closed-loop doses** 3x, 0 ok, mean -26.5 mg
- **Pre-flight** feed confirmed
- **Environment** not recorded
- **QC** valid -- `ok`
- **Data** [data/battery/20260805T200002Z_calcium-lactate](https://github.com/vertical-cloud-lab/powder-doser/tree/main/data/battery/20260805T200002Z_calcium-lactate)
- **Notes** [docs/battery-runs/2026-08-05-calcium-lactate.md](https://github.com/vertical-cloud-lab/powder-doser/blob/main/docs/battery-runs/2026-08-05-calcium-lactate.md)
- **Video** [https://youtu.be/_iDB8z83GdQ?t=3587](https://youtu.be/_iDB8z83GdQ?t=3587) -- accurate to about a minute

### 2026-08-05 18:53 UTC -- brown-rice-flour

- **Window** 2026-08-05T18:53:05.644181+00:00 -> 2026-08-05T19:00:13.279228+00:00  (7:07)
- **Powder** brown rice flour (food-safe batch), auger #2  ·  batch `food-safe-2026-08`  ·  operator swcharles
- **Tests** blocks ABCDEG  ·  64 measured trials  ·  C/E 30 · D 15/45/90 RPM
- **Dispensed** 0.0256 g
- **Feed factor (block C)** 0 deg 0.30 mg/rev  ·  45 deg 0.25 mg/rev  ·  90 deg 0.20 mg/rev
- **Closed-loop doses** 3x, 0 ok, mean -999.1 mg
- **Pre-flight** conveying-slowly
- **Environment** not recorded
- **QC** valid -- `conveying-slowly`
- **Data** [data/battery/20260805T185305Z_brown-rice-flour](https://github.com/vertical-cloud-lab/powder-doser/tree/main/data/battery/20260805T185305Z_brown-rice-flour)
- **Notes** [docs/battery-runs/2026-08-05-brown-rice-flour-auger2.md](https://github.com/vertical-cloud-lab/powder-doser/blob/main/docs/battery-runs/2026-08-05-brown-rice-flour-auger2.md)
- **Video** [https://youtu.be/5ENY3XL4yhc?t=28370](https://youtu.be/5ENY3XL4yhc?t=28370) -- accurate to about a minute

### 2026-08-05 14:57 UTC -- sodium-alginate

- **Window** 2026-08-05T14:57:25.298344+00:00 -> 2026-08-05T15:46:08.448811+00:00  (48:43)
- **Powder** sodium alginate (food-safe batch)  ·  batch `food-safe-2026-08`  ·  operator swcharles
- **Tests** blocks ABCDEG  ·  64 measured trials  ·  C/E 30 · D 15/45/90 RPM
- **Dispensed** 2.4563 g
- **Feed factor (block C)** 0 deg 0.75 mg/rev  ·  45 deg 9.58 mg/rev  ·  90 deg 10.87 mg/rev
- **Closed-loop doses** 3x, 0 ok, mean -291.5 mg
- **Pre-flight** feed confirmed
- **Environment** not recorded
- **QC** valid -- `ok`
- **Data** [data/battery/20260805T145725Z_sodium-alginate](https://github.com/vertical-cloud-lab/powder-doser/tree/main/data/battery/20260805T145725Z_sodium-alginate)
- **Notes** [docs/battery-runs/2026-08-05-sodium-alginate.md](https://github.com/vertical-cloud-lab/powder-doser/blob/main/docs/battery-runs/2026-08-05-sodium-alginate.md)
- **Video** [https://youtu.be/5ENY3XL4yhc?t=14230](https://youtu.be/5ENY3XL4yhc?t=14230) -- accurate to about a minute

### 2026-08-04 22:49 UTC -- brown-rice-flour

- **Window** 2026-08-04T22:49:37.985918+00:00 -> 2026-08-04T22:56:35.919313+00:00  (6:57)
- **Powder** brown rice flour (food-safe batch), re-run after tape removal  ·  batch `food-safe-2026-08`  ·  operator swcharles
- **Tests** blocks ABCDEG  ·  64 measured trials  ·  C/E 30 · D 15/45/90 RPM
- **Dispensed** 0.0043 g
- **Feed factor (block C)** 0 deg 0.00 mg/rev  ·  45 deg 0.00 mg/rev  ·  90 deg 0.00 mg/rev
- **Closed-loop doses** 3x, 0 ok, mean -1000.0 mg
- **Pre-flight** no-conveyance
- **Environment** not recorded
- **QC** excluded -- `no-conveyance-auger-suspect`
- **Data** [data/battery/20260804T224937Z_brown-rice-flour](https://github.com/vertical-cloud-lab/powder-doser/tree/main/data/battery/20260804T224937Z_brown-rice-flour)
- **Notes** [docs/battery-runs/2026-08-04-brown-rice-flour-rerun.md](https://github.com/vertical-cloud-lab/powder-doser/blob/main/docs/battery-runs/2026-08-04-brown-rice-flour-rerun.md)
- **Video** [https://youtu.be/w1D5DRiHFWM?t=13696](https://youtu.be/w1D5DRiHFWM?t=13696) -- frame-accurate

### 2026-08-04 21:14 UTC -- white-rice-flour

- **Window** 2026-08-04T21:14:22.351081+00:00 -> 2026-08-04T22:02:11.472390+00:00  (47:49)
- **Powder** white rice flour (food-safe batch)  ·  batch `food-safe-2026-08`  ·  operator swcharles
- **Tests** blocks ABCDEG  ·  64 measured trials  ·  C/E 30 · D 15/45/90 RPM
- **Dispensed** 3.2490 g
- **Feed factor (block C)** 0 deg 3.75 mg/rev  ·  45 deg 12.78 mg/rev  ·  90 deg 37.15 mg/rev
- **Closed-loop doses** 3x, 0 ok, mean -137.9 mg
- **Pre-flight** feed confirmed
- **Environment** not recorded
- **QC** valid -- `ok`
- **Data** [data/battery/20260804T211422Z_white-rice-flour](https://github.com/vertical-cloud-lab/powder-doser/tree/main/data/battery/20260804T211422Z_white-rice-flour)
- **Notes** [docs/battery-runs/2026-08-04-white-rice-flour.md](https://github.com/vertical-cloud-lab/powder-doser/blob/main/docs/battery-runs/2026-08-04-white-rice-flour.md)
- **Video** [https://youtu.be/w1D5DRiHFWM?t=7981](https://youtu.be/w1D5DRiHFWM?t=7981) -- frame-accurate

### 2026-08-04 20:43 UTC -- brown-rice-flour

- **Window** 2026-08-04T20:43:16.183255+00:00 -> 2026-08-04T20:50:20.999936+00:00  (7:04)
- **Powder** brown rice flour (food-safe batch)  ·  batch `food-safe-2026-08`  ·  operator swcharles
- **Tests** blocks ABCDEG  ·  64 measured trials  ·  C/E 30 · D 15/45/90 RPM
- **Dispensed** 0.0095 g
- **Feed factor (block C)** 0 deg 0.22 mg/rev  ·  45 deg 0.20 mg/rev  ·  90 deg 0.10 mg/rev
- **Closed-loop doses** 3x, 0 ok, mean -999.4 mg
- **Environment** not recorded
- **QC** excluded -- `no-conveyance-auger-suspect`
- **Data** [data/battery/20260804T204316Z_brown-rice-flour](https://github.com/vertical-cloud-lab/powder-doser/tree/main/data/battery/20260804T204316Z_brown-rice-flour)
- **Notes** [docs/battery-runs/2026-08-04-brown-rice-flour.md](https://github.com/vertical-cloud-lab/powder-doser/blob/main/docs/battery-runs/2026-08-04-brown-rice-flour.md)
- **Video** [https://youtu.be/w1D5DRiHFWM?t=6115](https://youtu.be/w1D5DRiHFWM?t=6115) -- frame-accurate

## How the video links work

The bench camera streams continuously in rolling 8 h broadcasts, so every run is already on video. A run's `started_utc` picks the covering broadcast out of [`stream-broadcasts.json`](stream-broadcasts.json) and becomes a `?t=` offset into it.

- **`~1 min`** -- the offset is measured from the broadcast title's start time, which is when YouTube accepted the broadcast rather than the video's `t=0`. Close enough to find the run; not close enough to land on one auger revolution.
- **`exact`** -- the broadcast has a calibrated anchor in [`stream-registry.json`](stream-registry.json), measured against the burned-in overlay clock. Add one with `python scripts/battery_stream_links.py --calibrate`, and per-block links become available from that script too.

Links carry a 15 s lead-in so the action starts just after the seek.
