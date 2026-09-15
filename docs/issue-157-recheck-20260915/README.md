# Issue #157 — Sep 15 recheck: drift after the balance was moved out of the hood

Session context: @williamulbz moved the HR-100A out of the EB B125 fume hood
(comment 2026-09-15 18:24 UTC, "drifting no matter where it is placed"), and
@sgbaird asked when the "consistent" drift was introduced, whether it could be
damage or relocation-related, and whether a factory reset would help. This
folder holds the evidence gathered live during that session (all times MDT,
2026-09-15).

## Timeline established this session

| time | event | evidence |
|---|---|---|
| 12:05:54 | bench power cycled — Pi boot time (`uptime -s`); balance therefore also unplugged/replugged during the move | Pi boot log |
| 12:11 | picam-d1pr stream restarted | broadcast title timestamp |
| 12:40:38 | display **50.6077 g** — beaker on pan, nobody in frame | `frame_1240_display50.6077.png` |
| 12:47:56 | display **50.6996 g** → **+12.6 mg/min** over the interval | `frame_1247_display50.6996.png` |
| 12:51:50 | display **50.7573 g** → **+14.8 mg/min** over the interval | `frame_1251_display50.7573.png` |
| ≈12:52–12:59 | balance physically removed from under the rig; RS-232 lead and AC barrel plug left on the counter | `frame_1259_balance_removed.png` |
| 12:59+ | serial `Q` polls return nothing ("is the balance switched on?") — consistent with the removal | gate output |

The display climb of **+13–15 mg/min at 35–45 min after power-on** matches the
frame-validated Sep 7 observation in the hood (started at +13.5 mg/min, decayed
with τ ≈ 21 min; `docs/issue-157-drift/` on branch
`claude/issue-157-20260908-0427`). Same signature, different location →
the drift tracks time-since-disturbance (power-up, relocation), not the room
position, and per the manual restarts at every move.

## A&D HR-A manual facts (official PDF, 1WMPD4002375C)

- Installation: "Connect the AC adapter to the balance. **Warm up the balance
  for at least one hour** with nothing on the weighing pan." Level via the
  bubble level first.
- Precautions: "**Calibrate the balance before use or after having moved it to
  another location.**"
- §9-2 Initializing the Balance returns to factory settings: **calibration
  data**, function table, unit/reference masses, the stored external
  calibration weight value, function-switch settings, statistical data —
  and "Be sure to calibrate the balance after initialization."
- Calibration weight for the HR-100A: **100 g (factory setting) or 50 g**,
  stored value adjustable −0.0150 g to +0.0150 g.
- Neither the unpacking contents nor the options/peripherals chapter lists a
  calibration weight — the HR-100A is the external-calibration model and ships
  without one (the HR-100AZ carries the internal motorized weight).
- The breeze break "may be charged with static electricity … when the humidity
  is low. If the weight value is unstable even when there are no drafts …
  remove the breeze break" or use the AD-1683 static eliminator.

## ⚠️ Discrepancy found: readiness-gate live fits vs the photographed display

Three 90 s live samples were taken with `balance_readiness.py --once`
(read-only A&D `Q` polls; tooling from branch `claude/issue-157-20260908-1634`
@ `47aee46`; state files committed here):

| window (MDT) | gate live fit | display over same period (frames) |
|---|---|---|
| 12:41:55–12:43:25 | −1.8 mg/min (`state1.json`) | ≈ **+12.6 mg/min** |
| 12:44:50–12:46:20 | −4.5 mg/min (`state2.json`) | ≈ +12.6 → +14.8 mg/min |
| 12:48:22–12:49:52 | −25.5 mg/min (`state3.json`) | ≈ **+14.8 mg/min** |

The two channels agreed to 1–2 mg on Sep 7 — but that session sampled via
`balance_environment_survey.py` running on the Pi. The readiness gate's
*remote live path* (runner-side heredoc plumbing via `balance_zero.py`, added
Sep 8) was only ever validated against itself, and it is the differing
variable. Its slope sign/magnitude cannot be trusted until this is fixed; the
Sep 8 "live shakedown" numbers (including the +0.03 mg/min "settled" reading)
came from the same path and inherit the doubt. Suspects: sample timestamping
or ordering in the remote collection path (sample-to-sample jitter looked sane
at 0.075 mg, which points at timestamps rather than values). `--from-csv`
replay mode and all Sep 7 conclusions are unaffected (frame-validated).

Repro next time the balance is connected: run the gate with `--csv-dir`, grab
one DVR frame pair (`bench_frame.py --seconds-ago …`, branch
`claude/issue-116-blockh-recovered` @ `81bbe75`), and compare raw CSV slope
against the display.

## Notes

- Read-only session: `Q` polls only; the auger (loaded with silicon per
  `~/RIG-NOTICE-20260915.txt`) was never actuated; nothing persisted on the Pi
  outside `/tmp`.
- A beaker (~50.6 g) sat on the pan throughout the 12:40–12:52 window, so the
  climb is balance warm-up plus whatever the glassware contributes; bare-pan
  behavior should be confirmed once the balance is parked and warmed up.
