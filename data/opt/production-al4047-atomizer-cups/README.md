# Al 4047 doses into atomizer cups (byu-vcl composition spread)

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
