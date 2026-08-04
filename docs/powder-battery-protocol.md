# Uniform powder test battery (issue #116)

One **fixed** test sequence, run identically for every powder, so results
are directly comparable across powders. This is *not* an optimization
workflow: nothing is tuned per powder. The parameters are frozen (the
tuned-salt values from the PR #124 three-phase bench demos) and the goal
is to record how each powder behaves under the same conditions — the
cross-powder dataset for the manuscript (PR #97) and the raw material for
the future MPC/optimization work (issues #123/#130), which will pick its
own parameters later.

Code:

- Firmware: [`hardware/test-module/firmware/powder_battery.py`](../hardware/test-module/firmware/powder_battery.py)
- Host capture + MongoDB upload: [`scripts/powder_battery_capture.py`](../scripts/powder_battery_capture.py)
- Simulation tests (CI, no hardware): [`hardware/test-module/firmware/sim/test_powder_battery.py`](../hardware/test-module/firmware/sim/test_powder_battery.py),
  [`scripts/tests/test_powder_battery_capture.py`](../scripts/tests/test_powder_battery_capture.py)

## The chosen tests

Tilt is the user-facing tube angle: 0° = horizontal, 90° = vertical
(the servo-horn convention; the three-phase drivers speak mounting-plate
degrees, tilt/2, converted internally).

| Block | Name | What runs | Degree of freedom | What it measures | Paper use |
|---|---|---|---|---|---|
| A | baseline | 8 no-actuation stable readings at tilt 45°, 2 s apart | — | Balance noise + drift floor under every later number | error bars |
| B | hold | 15 s static hold at tilt 0°, 45°, 90°, no actuation | tilt | Spontaneous discharge (avalanche) vs cohesion | flowability classification |
| C | rotation | 6 × 360° auger rotations at 30 RPM, at tilt 0°, 45°, 90°, stable reading after each | tilt × rotation | g/rev vs tilt, and its trial-to-trial spread (RSD) | feed-factor map; Fig. 3-style yield plots |
| D | speed | 3 auger revolutions of continuous rotation at 15, 45, 90 RPM at tilt 45°, streaming ~4 Hz scale polls | rotation speed | Flow rate vs speed, pulsation in the mass-vs-time trace | "dose CV vs auger speed" panel; mass-vs-time traces |
| E | tap | 8 single-tap trials at tilt 0° and 45°, each preceded by a measured 360° re-feed rotation | tapping | mg/tap (tap-only, re-feed accounted separately, per #131) | fine-actuator quantum per powder |
| F | vib | Same shape as E with 3 DRV2605L effect bursts per trial instead of the tap | vibration | mg/burst; skipped with a `META,vib,unavailable` row while the driver reports EIO | vibration ablation |
| G | dose | 3 × 1.000 g closed-loop doses with the **three-phase controller** (PR #124) under the frozen parameter set below | all, closed loop | Accuracy (error vs ±5 mg tolerance), time-to-dose, phase breakdown (cycles, taps, revolutions) | the headline per-powder dosing table; measured-vs-requested panel |

Frozen three-phase parameters for Block G (identical for every powder;
from the tuned salt demo that landed −0.7 mg):

- Thresholds: bulk→fine at 0.500 g-to-go, fine→tap at 0.050 g-to-go,
  done at ±5 mg.
- Phase 1 *bulk*: continuous rotation at 55 auger RPM, tilt 90°
  (plate 45°), anticipation 0.12 g (the measured in-flight mass).
- Phase 2 *fine*: 45° auger increments at 30 RPM, tilt 45° (plate 22.5°).
- Phase 3 *tap*: 2-tap bursts at tilt 0° (plate 0°), 5° re-feed nudges
  (max 10) when the lip runs dry.

Budget per powder: roughly **4–10 g** (powder-dependent — free-flowing
powders dispense more in blocks C/D) and **~40–50 min** wall clock.

**Low flow is data here, not an error.** A cohesive powder moving
nothing at tilt 0° is exactly the behaviour the battery exists to
record, so low-flow trials are kept and flagged `lowflow` in the CSV.
The operator is only prompted after 4 consecutive low-flow rows in case
the hopper is simply empty; unattended runs auto-answer `keep`.

## Running it

### At the bench (attended)

```bash
python scripts/powder_battery_capture.py --port /dev/ttyACM0 \
    --powder-id brown-rice-flour --powder "brown rice flour, <brand/lot>" \
    --operator cr --upload
```

Answer the prompts (empty cup / refill hopper) in the same terminal:
Enter to continue, `keep` to accept low flow, `skip` for next block,
`abort` to end.

### Remotely / "@claude, I've loaded Brown Rice Flour, run the test"

The intended flow for a comment like that: Claude SSHes to the Pi Zero
over Tailscale (per `CLAUDE.md`), then inside `tmux`:

```bash
source ~/.config/powder-doser/env       # MONGODB_URI
~/powder-doser-venv/bin/python ~/powder-doser/scripts/powder_battery_capture.py \
    --port /dev/ttyACM0 --powder-id brown-rice-flour --unattended --upload
```

`--unattended` makes every device prompt auto-continue (stall prompts
auto-answer `keep`), so the run never blocks on a keyboard.

### Pre-run bench checklist (the manual step)

An unattended run cannot see the rig, and every item below produces the
same "flat zero" data that a genuinely cohesive powder does. Whoever
loads the powder confirms these **before** commenting:

1. **Storage cap removed from the delivery end.** These augers are
   printed with threaded caps; a capped outlet delivers nothing.
2. **Auger seated in the drive coupler.** The firmware verifies the
   stepper turned, not that the tube turned with it.
3. **Powder present in the delivery flights**, not only at the rear.
4. **Outlet aimed into the collection dish**, and the **dish emptied**.

Since the 2026-08-04 brown-rice-flour failure, the remote workflow runs a
**pre-flight feed check** before committing to a 45-minute battery: tare,
tilt 90 deg, five 360 deg revolutions at 30 RPM. Tens of mg per revolution
means the path is clear; a flat 0.0000 g means stop and check the list
above. See the white-rice-flour run
([notes](battery-runs/2026-08-04-white-rice-flour.md)) for both sides of
that comparison.

That check is
[`hardware/test-module/firmware/battery_preflight.py`](../hardware/test-module/firmware/battery_preflight.py)
(~1 minute):

```bash
mpremote connect /dev/ttyACM0 exec "import battery_preflight; battery_preflight.run()"
```

It prints `PRE,...` rows and one of `feed confirmed` /
`suspect-no-feed` / `empty-or-blocked` / `scale-unreadable`.

When the pre-flight does *not* confirm feed, escalate with
[`battery_feed_diagnostic.py`](../hardware/test-module/firmware/battery_feed_diagnostic.py)
(~3 minutes), which separates a **cohesive powder arching over the
auger** from a **mechanically blocked delivery path** — the two look
identical over a single short rotation:

```bash
mpremote connect /dev/ttyACM0 exec "import battery_feed_diagnostic as d; d.run()"
```

| Observation | Verdict |
|---|---|
| long/fast continuous rotation conveys | `conveying-slowly` — run the battery |
| rotation dead, but rotation *after* tapping conveys | `arching-responds-to-agitation` |
| rotation dead before and after agitation, taps alive | `mechanical-no-feed` — check the list above |
| nothing moves at all | `empty-or-fully-blocked` |

Both modules are covered by simulation tests
([`sim/test_battery_preflight.py`](../hardware/test-module/firmware/sim/test_battery_preflight.py)).

### Recording the QC decision

The capture script takes the verdict as arguments rather than having it
hand-patched into `run.json` afterwards:

- `--preflight-json FILE` embeds the feed-check result under `preflight`
- `--qc-verdict STR` sets `qc.verdict`
- `--qc-valid` sets `qc.valid_for_cross_powder_comparison` — **runs are
  excluded by default**, so a battery only joins the cross-powder
  dataset when someone has confirmed the rig actually fed
- `--batch STR` labels runs that came out of the same fill container

The 2026-08-04 brown-rice-flour run
([notes](battery-runs/2026-08-04-brown-rice-flour.md)) failed on one of
these: 20 continuous auger revolutions at tilt 90° delivered exactly
0.0000 g while taps still shook out fines. That is the no-feed
signature — if a run comes back with rotation deltas at the balance
noise floor across *all* tilts, check the list above before recording
it as the powder's behaviour.

One-time deploy of the firmware module to the Pico (from the Zero):

```bash
~/powder-doser-venv/bin/mpremote cp \
    ~/powder-doser/hardware/test-module/firmware/powder_battery.py :
```

Requirements on the Pico: the PR #100 driver stack (`config.py`,
`tic.py`, `scale.py`) and PR #124's `main_three_phase.py` — all already
on the bench Pico. Block F needs `drv2605.py` + working I²C (currently
reporting EIO, so F self-skips).

### Reduced runs

`--run-args` forwards keyword overrides, e.g. only the closed-loop
doses: `--run-args 'blocks="G"'`, or a quick smoke:
`--run-args 'blocks="ACG", rotation_trials=3, dose_repeats=1'`.

## Outputs

Per run, under `data/battery/<UTC-stamp>_<powder-id>/`:

| File | Contents |
|---|---|
| `raw_serial_<id>.log` | every serial line, verbatim |
| `trials_<id>.csv` | one row per measured action: `powder_id, block, tilt_deg, phase, trial, action, rpm, before_g, after_g, delta_g, flag, t_ms` |
| `polls_<id>.csv` | streamed scale polls from Block D (mass-vs-time traces) |
| `doses_<id>.csv` | one row per Block G dose: target, dispensed, error, status, elapsed, revolutions, taps, per-phase cycles |
| `summary_<id>.csv` | per-(block, tilt, phase) n/mean/std/sem/min/max/RSD |
| `run_<id>.json` | the complete self-contained run document |

Plots: `scripts/plot_battery_run.py` is the *did it feed at all?* diagnostic
(used on the no-feed brown-rice-flour run); `scripts/plot_battery_results.py`
is the four-panel per-powder result figure (blocks C, D, E, G) for runs that
did feed.

With `--upload`, `run_<id>.json` is inserted into MongoDB Atlas as one
document in **`powder_doser.battery_runs`** — the same database as the
issue #126 plan, in its own collection so uniform-battery data never
mixes with the #131 characterization sweeps. Top-level `powder_id` +
`started_utc` follow the existing index pattern, so
`find({powder_id: "brown-rice-flour"}).sort("started_utc", -1)` pulls a
powder's history. Offline runs backfill with
`--upload-file path/to/run_<id>.json`.

## Powder IDs

Slugs, normalized by the capture script (`Brown Rice Flour` →
`brown-rice-flour`). Suggested IDs for the current set: `salt`,
`white-rice-flour`, `brown-rice-flour`, `cmc`, `calcium-lactate`,
`sodium-alginate`, `xanthan-gum`, `alsi10mg`, `si`.
