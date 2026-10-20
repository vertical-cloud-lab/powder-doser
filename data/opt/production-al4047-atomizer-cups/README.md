# Al 4047 doses into atomizer cups (byu-vcl composition spread)

## 2026-10-20: steeper tilt, 109 rpm and faster taps all at once. Both tries stalled (2.9 mg and 8.3 mg)

@sgbaird asked in issue #186 to retry with a higher tilt, fast rotation and frequent tapping all at
once, because the outlet was probably still clogged with larger chunks (the 09-30 load in
[PR #166](https://github.com/vertical-cloud-lab/powder-doser/pull/166#issuecomment-5920101018)).

![three stalled doses](unclog_trace.png)

| trial | tilt | auger | cadence taps | no-flow window | result |
|---|---|---|---|---|---|
| `a5fdadaa` (10-19) | 40° | 99 rpm | 60/440 ms at a 250 ms poll: 2.0/s | 15 s | `stalled` at 124.5 s, 202.8 mg (86 mg in the first 6 s) |
| `b13e5997` | 60° | 109 rpm | 60/140 ms at a 100 ms poll: 3.5/s | 15 s | `stalled` at 20.4 s, 2.5 mg (2.9 mg read 2 min later) |
| `f6a3403f` | 75° | 109 rpm | 60/90 ms at a 50 ms poll: 4.2/s | 40 s | `stalled` at 44.6 s, 7.9 mg (8.3 mg read 1 min later) |

- **The auger turned at full speed and fed almost nothing.** The drive gear's teeth are sharp at rest and
  fully blurred during `f6a3403f`. That is 0.09 mg (60°) and 0.11 mg (75°) per auger turn, against
  about 0.6 mg per turn at 40° after the first 6 s and 113 mg per turn for salt.
- **A steeper tilt should only help gravity feed, and the auger turned without stalling.** So either
  nothing reaches the flights (an empty or bridged hopper), or the outlet is blocked and the auger
  spins inside packed powder. Settings on the rig can't tell these apart; someone has to look.
- **109 rpm is the firmware ceiling** (240 motor rpm through the 44:20 gearing), so this was only 9% faster
  than 10-19's 100 rpm.
- **The tap rate is capped near 4 taps/s by the balance poll.** In `bulk_only` the loop fires at most one
  cadence tap per balance poll. Each poll is the sleep, the 60 ms tap and the balance read (about 70–120 ms here).
  More taps per second would need a firmware change (several taps per poll).

![drive gear at rest and during f6a3403f](livestream_gear_blur.jpg)

### Checks before spinning at a steeper tilt

- The plate was stepped up in 5° steps with the auger stopped, from 40° to 60° before `b13e5997` and
  from 60° to 75° before `f6a3403f`. At every step `rig_cmd.py` waited for three agreeing stable reads.
  They stayed at 0.2028–0.2030 g and then 0.0029 g, so the outlet never touched the funnel and nothing
  fell out.
- The livestream shows the outlet still over the funnel at 60° and 75°. The tilt pivot sits close
  to the outlet, so the outlet barely moves while the drive end swings. The hopper looks coaxial with the
  tube, above the drive gear, so a steeper tilt raises its open end.
- Each try was a 0.5 g target with the 20 mg overshoot guard, so a clog breaking at 60–75° could
  not run on to the whole remainder. A halt doesn't level the tube. The tube would have to be tilted
  back after the dose to stop any afterflow.

![outlet over the funnel at 40, 60 and 75 degrees](livestream_tilt_steps.jpg)

### Timeline (UTC)

| | |
|---|---|
| 01:10 | Zero read-only: idle since the 10-19 handback, nothing held the Pico's port, checkout at `306bbee`. |
| 01:14 | Livestream: the cup and funnel still on the pan, the plug on the wipe, balance 0.2028 g. |
| 01:15 | `--takeover` of the power-on `main.py`, `/trickle_tap` runner booted. Stable 0.2030 g at 0° and at 40°. |
| 01:16–01:18 | Plate stepped 40→60°: stable 0.2028–0.2030 g at each step. |
| 01:20:36 | `b13e5997` started: 0.5 g at 60°. It stalled at 20.4 s with 2.5 mg. |
| 01:22–01:23 | Stable 0.0029 g over `b13e5997`'s tare; plate stepped 60→75°, 0.0029 g at each step. |
| 01:23:54 | `f6a3403f` started: 0.5 g at 75°, 40 s no-flow window. It stalled at 44.6 s with 7.9 mg. |
| 01:26 | Stable 0.0083 g over `f6a3403f`'s tare. Plate eased 75→40→0° (0.0083 g throughout), then the Pico was soft-rebooted into its power-on `main.py`. |

### State after this session

| | g |
|---|---|
| powder target for 7.5 wt% (see 10-19 below) | 3.0407 |
| already in the cup before 10-19 (operator) | 0.0103 |
| `a5fdadaa`, last read over its tare before the next tare (01:18 UTC) | 0.2028 |
| `b13e5997`, read over its tare (01:23 UTC) | 0.0029 |
| `f6a3403f`, read over its tare (01:26 UTC) | 0.0083 |
| **in the cup, or on the funnel** | **0.2243** |
| **still to dispense** | **2.8164** |

- The rig is free: the plate at 0°, the Pico on its power-on `main.py`, `/trickle_tap` and the Zero's
  checkout unchanged. `~/RIG-NOTICE-20261020-atomizer-cup.txt` on the Zero records the session.
- **Before the next try, someone needs to look at the rig:** whether there is 4047 in the hopper, and
  whether the outlet and tube are blocked by chunks (or salt left from 10-15). Sieving out the larger
  chunks before reloading would avoid a repeat. Once it flows, 40° fed 4047 well on 09-30.
- **Not tried: reversing the auger.** A turn or two backwards might back a wedged chunk off the
  outlet. Reverse rotation has never been used on this rig, and I couldn't check that the auger's
  coupling tolerates it, so it needs a go-ahead.

### How it was run

The same executor as on 10-19 (`scripts/opt_dose_capture.py` at `306bbee`, `--mode production`), started
detached on the Zero. `--frozen` was 10-19's push with these changes: `bulk_poll_ms` 100 / 50,
`tap_cadence_off_ms` 140 / 90, `bulk_taper_start_g` 0.1, `dose_timeout_s` 180 / 120, and for
`f6a3403f` `bulk_settle_ms` 4000 (a 40 s no-flow window). The campaign parameters set all three tilts
to 60° / 75° and `bulk_rpm` to 109. `bulk_tap` stays the campaign's on/off categorical (`2hz` = on).
The cadence actually run is in each document's `parameters_executed`.

`rig_cmd.py` is the helper for the scale reads, the guarded tilt steps and the handback. It reuses
the executor's own serial session class, with the same port lock and raw-log format.
`grab_live.py` fetched livestream segments (`picam-d1pr`) through the Zero, because YouTube blocks
the runner's IP. Both ran from `/tmp` on the Zero, which a reboot clears.

### Files (2026-10-20)

- `zero/trial_b13e5997-….json`, `zero/trial_f6a3403f-….json`: the `opt_trials` documents (also in MongoDB).
- `zero/serial_b13e5997-….log`, `zero/serial_f6a3403f-….log`: the raw serial sessions, including every `set` echo.
- `zero/serial_readback_20261020.log`: the takeover, every tilt step and scale read, and the handback.
- `zero/run_B_b13e5997.out`, `zero/run_C_f6a3403f.out`: the executor's stderr and summary line.
- `zero/trials.jsonl`: the spool index, now three trials. Home paths are scrubbed to `~`.
- `unclog_trace.png` (made by `plot_unclog.py`), `livestream_tilt_steps.jpg`, `livestream_gear_blur.jpg`.
- `rig_cmd.py`, `grab_live.py`: the session helpers above.

## 2026-10-19: one as-made cup at the 7.5 wt% point (issue #186). Stopped at 0.2028 g because the auger wasn't feeding

@sgbaird asked in issue #186 for the 7.5 wt% point of
[byu-vcl PR #232](https://github.com/vertical-cloud-lab/byu-vcl/pull/232#issuecomment-6032144024)
(3.1 g of 4047 powder in one as-made cup), rescaled to this cup's weighed mass, with 0.0103 g
already in the cup.

### Target

PR #232 defines the point as powder / (cup + plug + powder) = 7.5 wt%, and its 3.1 g comes from a
computed 38.71 g of 6063 for the cup and plug together (`composition_spread.py` at byu-vcl `e639fbd`).

| | g |
|---|---|
| cup, weighed without its plug (operator) | 32.5074 |
| plug, not weighed; PR #232's computed .508" × .5625" plug with a #60 vent | 4.995 |
| powder for 7.5 wt%: 0.075 / 0.925 × (32.5074 + 4.995) | **3.0407** |
| already in the cup (operator) | 0.0103 |
| **to dispense** | **3.0304** |

Why the 32.5074 g has to be the cup without its plug: by PR #232's dimensions, an as-made cup alone
is 33.0–34.4 g and 38.0–39.4 g with its plug, and a thin-wall cup alone is 22.1–24.6 g. Each 0.1 g
of error in the plug estimate moves the powder target by 8.1 mg (0.02 wt%). `target_mass.py`
reproduces the table.

### What happened

| UTC | |
|---|---|
| 23:14 | Zero read-only: idle since 10-15, nobody held the Pico's port, checkout at `306bbee`. |
| 23:17 | `--takeover` of the power-on `main.py`, then the `/trickle_tap` runner (`trickle_tap/2026-10-15`) booted. The balance read a stable 0.0 g, so it had been tared with the cup on. |
| 23:19 | Livestream frame (`livestream_setup.jpg`): the cup stands on the pan with a funnel in its mouth under the auger outlet. The tare includes the funnel. A small disc with a centre hole sits on a wipe beside the balance, presumably the plug. |
| 23:24:42 | Trial `a5fdadaa`, dose A: target 2.9904 g, 40 mg short of 3.0304 g on purpose. A slower top-up was to follow. |
| 23:26:47 | `stalled` after 124.5 s at **0.2028 g**. |
| 23:30 | Five scale reads: stable **0.2035 g** over dose A's tare. The Pico was soft-rebooted back to its power-on `main.py`. |

Dose A settings: bo-005's bulk settings (40° tilt, 100 rpm, 2 Hz cadence taps) in the `bulk_only`
mode that finished the 2026-09-30 Al 4047 dose, so the tube held one tilt over the funnel throughout.
Other settings: τ_afterflow 0.8338 s, tolerance 3 mg, one pass, and an rpm taper from 100 to 15 over
the last 0.5 g, which never started. The overshoot guard was 20 mg and the dose timeout 1200 s. Every
other setting was the salt campaign's frozen value, with `log_to_flash 0`.

![dose trace](dose_trace.png)

**The auger turned but moved almost no powder.**
- 86 mg fell in the first 6 s. That powder was already at the outlet.
- After that, 198 auger turns gave about 1 mg/s. That is about 1 mg per turn, against about 113 mg
  per turn for salt and 250 mg/s at 100 rpm for AlSi10Mg on 09-29.
- At about 0.5 mg per tap, the 237 cadence taps alone account for that trickle.
- In the video the drive gear blurs during the dose (turning), and the funnel stays empty with the
  outlet right above it (`livestream_dose.jpg`).
- This matches the last two salt doses on 10-15, which stalled after 184 and 155 mg. So the hopper
  is probably empty or bridged, or caked salt is still in the tube.

![livestream during dose A](livestream_dose.jpg)

### State after this session

- **The cup holds about 0.2138 g:** the 0.0103 g already in it, plus the 0.2035 g read over dose A's
  tare. Some of that 0.2035 g may be on the funnel rather than in the cup.
- **The first material out may not be 4047.** If the tube still held salt from 10-15, look at what's
  in the cup before you use it.
- **To reach 7.5 wt%, 2.8269 g more is needed** (3.0407 − 0.2138), with the cup left on the pan. Every
  dose tares first.
- **The rig is free.** `/trickle_tap` and the Zero's checkout are unchanged.

### How it was run

`scripts/opt_dose_capture.py` (PR #166 branch, `306bbee`) ran on the Zero in `--mode production`,
with campaign id `production-al4047-atomizer-cups`, powder id `al4047` and `--takeover`. It was
started detached from the Actions runner, so a dropped SSH session couldn't affect it. The trial
document is also in MongoDB `opt_trials`. The livestream frames are from `picam-d1pr`
(`@byu-vcl-hardware-streams`), fetched through the Zero because YouTube blocks the runner's IP.

### Files

- `zero/trial_a5fdadaa-….json`: the `opt_trials` document (RESULT, parameters as executed,
  telemetry), the same one as in MongoDB.
- `zero/serial_a5fdadaa-….log`: the raw serial session, including every `set` echo. It's
  force-added past the `*.log` ignore.
- `zero/serial_readback_20261019.log`: the scale reads before and after the dose, and the handback
  to `main.py`.
- `zero/trials.jsonl`: the Zero's spool index. The home-directory path is scrubbed to `~`.
- `dose_trace.png`: made by `plot_dose.py`. `target_mass.py` reproduces the target table.
- `livestream_setup.jpg`, `livestream_dose.jpg`: frames from the bench livestream at 23:19 and
  23:24–23:27 UTC (the clock burned into the frames is local time, UTC−6).
