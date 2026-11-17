# Files recovered from the Pico's flash root, 2026-10-13

On 2026-10-13 the Pico's flash was full (0 KB free), and the margin campaign's
firmware upload (`trickle_tap/2026-10-09`, six files into `/trickle_tap`) needed
about 30 KB. Before freeing space, every data file at the flash root (30
`trickle_log_NNN.csv` and 5 `balance_capture_*.csv`) was copied to the Zero
(`~/pico-backup-20261013`) and checked by sha256 against the Pico.

- **Deleted from the Pico:** `trickle_log_000.csv` to `trickle_log_025.csv` only.
  Each was byte-identical to its copy committed in
  [`../2026-09_pico-flash-backup/`](../2026-09_pico-flash-backup/) and to the
  Zero's `~/pico-backup-20260929`. That freed 132 KB; 100 KB remained after the
  upload.
- **Kept on the Pico, and copied here unchanged:** the files below. They were not
  in the repo before.

The firmware names a new log after the first free number, so a
`trickle_log_000.csv` to `trickle_log_025.csv` written to the Pico after
2026-10-13 is a new dose, not one of the September logs.

## Dose logs

Same 15-column schema as the September logs (see the
[firmware README](../../../hardware/test-module/firmware/trickle_tap/README.md#inspecting-a-run)).
The Pico has no clock, so the files carry no dates, and their order is only their
numbering. 028 and 029 contain `refill` phases, so they were run with the PR #154
refill-tap runner.

| file | rows | last t_s | last raw reading z_g (g) | phases |
|---|---|---|---|---|
| `trickle_log_026.csv` | 78 | 151.37 | 0.77168 | bulk > trickle > trickle_end > tap |
| `trickle_log_027.csv` | 56 | 42.11 | 0.74824 | bulk > trickle > trickle_end > tap |
| `trickle_log_028.csv` | 52 | 155.85 | 0.49610 | bulk > trickle > trickle_end > tap, then 9 refill/tap rounds |
| `trickle_log_029.csv` | 83 | 226.25 | 0.49636 | bulk > trickle > trickle_end > tap, then 10 refill/tap rounds |

## Balance captures

Written by a `balance_stream` script: `M` rows are metadata (duration 55 or 70 s,
60 ms poll), `P` rows the pre-tare and post-tare readings, `E` rows timestamped
events in device milliseconds, and `D` rows the raw balance frames
(`D,<ms>,<grams>,<S|U>` for stable/unstable). The file names give the mass used
(2, 5 or 10 g); the suffixes (`10d`, `10l`, `10ad`) are not documented on the
device.

| file | raw frames | duration |
|---|---|---|
| `balance_capture_2g_10d.csv` | 359 | 70 s |
| `balance_capture_5g_10d.csv` | 233 | 55 s |
| `balance_capture_5g_10ad.csv` | 283 | 55 s |
| `balance_capture_10g_10d.csv` | 283 | 55 s |
| `balance_capture_10g_10l.csv` | 282 | 55 s |
