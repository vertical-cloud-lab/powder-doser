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

### How long each block should take

Measured on the 2026-08-05 sodium alginate run (48 min 43 s end to end).
Almost the entire battery is block G, so a run that *looks* stalled is
usually a dose phase behaving exactly as designed.

| Block | Typical duration | Notes |
|---|---|---|
| A baseline | ~15 s | |
| B hold | ~40 s | fixed: 3 tilts × 15 s |
| C rotation | ~2 min | 18 revolutions + settling |
| D speed | ~10 s | |
| E tap | ~2.5 min | 32 measured actions |
| F vib | ~2.5 min | currently skipped in seconds |
| **G dose** | **~14 min per dose** | ~42 min for the default 3 |

A dose that exhausts the 200-cycle fine-phase budget takes ~14 min; one
that converges early takes less. Nothing else in the battery runs longer
than ~3 minutes, so **any wait beyond ~10 minutes is block G** unless the
run has genuinely died.

Block G is also the only block whose duration depends strongly on the
powder, so the whole-run estimate follows it. The 2026-08-05 calcium
lactate run finished in **19 min 22 s** and the 2026-08-06 xanthan gum
run in **16 min 12 s**, because each dose tripped the stall detector in
~3–4 min instead of grinding out the full fine-phase budget; a powder
that conveys nothing at all (brown rice flour) stalls in seconds and
finishes the battery in ~7 min. The 2026-08-06 salt run took
**16 min 37 s** for the opposite reason — its doses *converged*, in
113–265 s. Plan for ~50 min, but do not read an early finish as a crash
— check for `RUN,END,ok`.

Rule of thumb: the *better* a powder conveys, the *shorter* the run.
Well-conveying powders reach phase 3 and stall there in minutes; poorly
conveying ones exhaust the 200-cycle fine budget and take ~14 min per
dose. A run that finishes fast because block G *succeeded* looks
identical in duration to one that finished fast because it stalled —
read `doses_<powder>.csv`, not the clock.

The capture script prints the run start timestamp up front, prefixes every
device line with the UTC clock and elapsed time, and finishes with a
per-block timeline; the same timeline is stored in the run document as
`block_timeline` and in `timeline_<powder-id>.csv`. To check on a live run
without touching it:

```bash
tmux capture-pane -p -t battery | tail -5
```

The `[HH:MM:SS +H:MM:SS]` prefix on the last line gives the elapsed time
directly. Judge progress from that, not from the last block anyone saw.

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

1. **Storage cap _and tape_ removed from the delivery end.** These augers
   are printed with threaded caps and are taped shut for storage; either
   one delivers nothing. Both ends get sealed, so check the end that
   points at the beaker, not just the end you filled. This is the single
   most common cause of a wasted run — it has now cost three attempts
   (2026-08-04 brown rice flour, 2026-08-05 carboxymethyl cellulose).
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

**Never stop on `suspect-no-feed` alone — escalate.** Five revolutions
is not enough to charge a slow-cohesive powder's delivery section, so
the pre-flight can badly under-report a perfectly good column. The
2026-08-05 carboxymethyl cellulose run
([notes](battery-runs/2026-08-05-carboxymethyl-cellulose.md)) pre-flighted
at **0.36 mg/rev** and block C then measured **26.3 mg/rev** at tilt 45°
— a 73× under-report — because the diagnostic's 35 revolutions were what
it took to fill the flights (1.14 → 22.82 mg/rev, monotonic). White rice
flour charges in ~3 revolutions; this one needed ~30.

The discriminator is whether the reading is *exactly* zero:

| Pre-flight reading | Read it as | Do |
|---|---|---|
| tens of mg/rev | feed confirmed | run the battery |
| non-zero but low | possibly still charging | **escalate to the diagnostic** — do not abort |
| exactly `0.0000` everywhere | blocked path (tape, cap) | grab a camera frame, then check the bench list |

A powder that is genuinely too cohesive to convey still shakes *some*
fines through: brown rice flour delivered 5.1 mg from 30 taps. Exactly
zero across dozens of revolutions and taps is a mechanical block, not a
powder property.

### Then look at the rig: `scripts/bench_frame.py`

The two modules above can tell you *that* nothing is being conveyed, but
not *why* — and the operator is usually not at the bench when a remote run
starts. The rig is on camera continuously, so **grab a frame before
reporting a flat-zero pre-flight**:

```bash
python scripts/bench_frame.py --out /tmp/now.png                 # live edge
python scripts/bench_frame.py --seconds-ago 4000 --out /tmp/before.png
```

Pairing the current frame with one from a run that *did* convey is what
makes it conclusive — same rig, same balance, same geometry, one
difference. That is how the 2026-08-05 carboxymethyl cellulose attempt was
diagnosed in three minutes instead of costing a 50-minute battery and a
contaminated run document
([notes](battery-runs/2026-08-05-carboxymethyl-cellulose-aborted.md)).

The helper fetches the HLS segment over the Pi's residential connection
(YouTube bot-blocks the CI runner) and decodes it locally, so it needs
`ffmpeg` on the machine running it — `pip install imageio-ffmpeg`, or
`--ffmpeg /path/to/ffmpeg`. Nothing is installed permanently on the Pi
beyond `yt-dlp` in `/tmp`, and transfers are rate-capped.

Read the **burned-in overlay clock** in the frame, not the YouTube
watch-page timestamp — the overlay is the capture clock (lab-local MDT)
and matches the balance readings; the watch-page value is several seconds
off (see [stream-timestamps.md](battery-runs/stream-timestamps.md)).

Total silence is itself diagnostic. A powder this rig genuinely cannot
convey still lets fines through under tapping — brown rice flour gave
5.1 mg from 30 taps. **Exactly 0.0000 g across tens of revolutions *and*
tens of taps means the path is closed, not that the powder is cohesive.**

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

### How the rig is left afterwards

`Battery.run_all()` parks the rig in its `finally`, so this happens after
a normal finish, an operator `abort`, or a scale failure alike:

- **tilt returned to 0°** (tube horizontal, `PARK_TILT_DEG`), recorded as
  a `META,park_tilt_deg,0.0` row immediately before `RUN,END` so the log
  proves it happened;
- stepper stopped and de-energised;
- solenoid released.

Block G hands the servo back with the cached tilt unknown, so the park
forces the move rather than skipping on a stale value. Whoever swaps the
next auger can therefore assume the tube is horizontal — grep the run's
raw serial log for `park_tilt_deg` if in doubt. The pre-flight check
([`battery_preflight.py`](../hardware/test-module/firmware/battery_preflight.py))
parks at 0° the same way.

## Outputs

Per run, under `data/battery/<UTC-stamp>_<powder-id>/`:

| File | Contents |
|---|---|
| `raw_serial_<id>.log` | every serial line, verbatim |
| `trials_<id>.csv` | one row per measured action: `powder_id, block, tilt_deg, phase, trial, action, rpm, before_g, after_g, delta_g, flag, t_ms` |
| `polls_<id>.csv` | streamed scale polls from Block D (mass-vs-time traces) |
| `doses_<id>.csv` | one row per Block G dose: target, dispensed, error, status, elapsed, revolutions, taps, per-phase cycles |
| `summary_<id>.csv` | per-(block, tilt, phase) n/mean/std/sem/min/max/RSD |
| `timeline_<id>.csv` | host wall clock at each block start: `powder_id, block, started_utc, elapsed_s` |
| `run_<id>.json` | the complete self-contained run document |

The run document carries `started_utc`, `ended_utc`, `elapsed_s` and
`block_timeline` (schema version 2; version 1 documents predate the last
two and are otherwise identical).

Plots: `scripts/plot_battery_run.py` is the *did it feed at all?* diagnostic
(used on the no-feed brown-rice-flour run); `scripts/plot_battery_results.py`
is the four-panel per-powder result figure (blocks C, D, E, G) for runs that
did feed; `scripts/plot_battery_compare.py [--valid-only] out.png run_a.json
run_b.json ...` puts several powders side by side (pass `--valid-only` when
globbing `data/battery/*/run_*.json`, or the retracted no-feed runs are
plotted as if they were measurements).

`scripts/plot_battery_sequence.py` plots block C **revolution by
revolution** rather than as a mean, and is worth generating for every run:
several powders' block C is not six draws from one distribution, so the
mean and RSD in the results figure can describe a process that never
happened. It labels each tilt `charging` / `steady` / `decaying` /
`intermittent` / `below resolution` — white rice flour charges, brown rice
flour is intermittent clump releases, and carboxymethyl cellulose at 90°
decays from 39 mg to 2 mg per revolution behind a 9.3 mg mean. It also
overlays block D, which runs at tilt 45° right after block C ends at 90°
and so separates a tilt effect from a depleted hopper.

### The within-run drift check (block C vs block E)

Blocks C and E measure the same quantity — mass per 360° revolution at
30 RPM — at tilts 0° and 45°, about five minutes apart. That redundancy
was not designed in, but it is the only check the battery has on whether
a powder's feed factor is *stable across the run*, so compute the ratio
before quoting block C as the feed factor:

```
E re-feed mean (block E, tilt t) / rotation mean (block C, tilt t)
```

Six of the seven 2026-08 runs land at **0.74–1.12** — flat, or drifting
slightly down as the column depletes, which is what the fixed block order
predicts. Salt at tilt 45° came in at **2.68**, and its block G doses
drifted with it (errors −4.7 → −3.5 → +8.8 mg across three doses six
minutes apart, the last an `overshoot`). See
[the salt run notes](battery-runs/2026-08-06-salt.md).

A ratio far from 1 means the block C mean is not a property of the
powder, it is a property of the powder *at minute 2 of the run*. Quote it
as a bound, say so, and consider a repeat run. Ratios computed on values
at the balance resolution floor (brown rice flour) are meaningless —
check the magnitudes first.

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

## Video record

The `picam-d1pr` bench camera streams continuously to
[@byu-vcl-hardware-streams](https://youtube.com/@byu-vcl-hardware-streams), so
every run is already on video and nothing extra needs recording. After a run,

```bash
python scripts/battery_stream_links.py data/battery/*/run_*.json
```

turns `started_utc` plus the per-trial `t_ms` into `https://youtu.be/<id>?t=<s>`
share links per block, per tilt and per dose. It needs the broadcast's content
`t=0` in [`battery-runs/stream-registry.json`](battery-runs/stream-timestamps.md);
add a new broadcast with `--calibrate`, which reads the anchor off the burned-in
timestamp overlay rather than the watch page (they differ by several seconds —
enough to miss a trial). Current links: [`battery-runs/stream-timestamps.md`](battery-runs/stream-timestamps.md).

The pairing itself is no longer something to rediscover afterwards: the capture
script stamps a `video` block into every run document as the run is recorded
(see [the schema](characterization-data-collection.md#run-document-schema-v1)).
A run captured before its broadcast is anchored records the camera, the channel
and the 8 h broadcast slot to look in, and picks up its `?t=` link later from

```bash
python scripts/stream_reference.py --backfill data/battery/*/run_*.json
```

which re-resolves each run against the current registry. Re-upload a backfilled
run (`--upload-file`) so the database copy matches the local artifact.
