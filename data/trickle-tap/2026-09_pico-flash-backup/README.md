# Trickle-tap hand-tuning logs, recovered from the Pico's flash

William's manual trickle-tap sessions on salt (PR #154, roughly 2026-09-10 to
2026-09-21) tuned the values committed in `d21d652`, which became the frozen
baseline of the issue #164 campaign. The firmware writes each dose's telemetry
to `/trickle_log_NNN.csv` at the Pico's flash root (`LOG_TO_FLASH = True`).
Those files were never copied off the rig. PR #166's data audit (2026-09-25)
listed them as the biggest gap.

They were copied off unchanged on 2026-09-29, before the first campaign run.
That session had the rig handed over, so `mpremote` could stop the idle program
on the Pico. The flash copies are still in place; nothing on the Pico was deleted.

- `trickle_log_000.csv` to `trickle_log_025.csv`: one dose each, in the 15-column
  schema documented in the
  [firmware README](../../../hardware/test-module/firmware/trickle_tap/README.md#inspecting-a-run)
  (`t_s, phase, z_g, fresh, m_g, r_gps, sigma_g, ff_gpr, r_sp_gps, err_gps,
  integ, rpm_cmd, pred_g, cutoff_g, clamp_hits`). The Pico has no clock, so the
  files carry no dates, and the numbering is the only order. Targets are not
  recorded either. For completed doses the last raw reading approximates the
  dispensed mass, and those cluster at 0.5, 0.7, 1, 1.5, 2 and 3 g. Five logs
  stop in the bulk phase, and two end at readings no dose here would reach
  (56.6 g and 7.2 g), probably the cup being moved on the pan.
- `pico-root-code/`: the firmware files found at the flash root next to the
  logs, for provenance. `trickle_params.py` there is byte-identical to this
  branch's; `main_trickle.py` and `trickle_controller.py` are earlier (#154)
  versions; `trickle_kf.py` is identical; `main.py` is the multi-channel bench
  REPL that runs at power-up; `config.py` is the rig's own, which differs from
  the repo copy only in `SERVO_DEFAULT_DEG = 0`.

The logs cannot say which parameter values each dose ran with, because
parameters were changed live with `set` during tuning.

## Summary

| file | rows | last t_s | last raw reading z_g (g) | phases |
|---|---|---|---|---|
| `trickle_log_000.csv` | 15 | 16.8 | 0.53874 | bulk > trickle > trickle_end |
| `trickle_log_001.csv` | 21 | 35.6 | 1.06246 | bulk > trickle > trickle_end |
| `trickle_log_002.csv` | 57 | 103.0 | 1.00192 | bulk > trickle > trickle_end > tap |
| `trickle_log_003.csv` | 71 | 109.3 | 0.99568 | bulk > trickle > trickle_end > tap |
| `trickle_log_004.csv` | 44 | 52.2 | 0.71666 | bulk > trickle > trickle_end > tap |
| `trickle_log_005.csv` | 72 | 33.7 | 56.63440 | bulk > trickle > trickle_end |
| `trickle_log_006.csv` | 127 | 181.8 | 1.99838 | bulk > trickle > trickle_end > tap |
| `trickle_log_007.csv` | 132 | 187.2 | 1.99808 | bulk > trickle > trickle_end > tap |
| `trickle_log_008.csv` | 141 | 49.0 | 1.71984 | bulk |
| `trickle_log_009.csv` | 47 | 20.6 | 1.58038 | bulk |
| `trickle_log_010.csv` | 66 | 53.3 | 1.00554 | bulk > trickle > trickle_end > tap |
| `trickle_log_011.csv` | 106 | 220.6 | 1.19864 | bulk > trickle > trickle_end > tap |
| `trickle_log_012.csv` | 53 | 36.1 | 0.99974 | bulk > trickle > trickle_end > tap |
| `trickle_log_013.csv` | 19 | 22.9 | 0.50142 | bulk > trickle > trickle_end > tap |
| `trickle_log_014.csv` | 27 | 30.7 | 0.70502 | bulk > trickle > trickle_end > tap |
| `trickle_log_015.csv` | 96 | 47.8 | 3.00000 | bulk > trickle > trickle_end > tap |
| `trickle_log_016.csv` | 122 | 195.8 | 1.99846 | bulk > trickle > trickle_end > tap |
| `trickle_log_017.csv` | 50 | 66.9 | 0.99986 | bulk > trickle > trickle_end > tap |
| `trickle_log_018.csv` | 61 | 23.0 | 0.00238 | bulk |
| `trickle_log_019.csv` | 98 | 35.9 | 0.00227 | bulk |
| `trickle_log_020.csv` | 11 | 12.0 | 0.60844 | bulk |
| `trickle_log_021.csv` | 52 | 98.1 | 0.49904 | bulk > trickle > trickle_end > tap |
| `trickle_log_022.csv` | 70 | 109.4 | 7.22200 | bulk > trickle > trickle_end > tap |
| `trickle_log_023.csv` | 73 | 72.0 | 1.49868 | bulk > trickle > trickle_end > tap |
| `trickle_log_024.csv` | 55 | 105.4 | 0.49838 | bulk > trickle > trickle_end > tap |
| `trickle_log_025.csv` | 175 | 126.3 | 1.00022 | bulk > trickle > trickle_end > tap |
