# Powder-doser characterization: data collection & upload

How to measure, per dispensing angle, the mass dispensed **per auger
rotation** and **per solenoid tap**, with repeats and uncertainty, and
how the data gets stored per the issue #126 plan.  (Issues #130, #126.)

## What gets measured

At every angle in `ANGLES_DEG` (default `0..90` in 15° steps), the
sweep in [`hardware/test-module/firmware/characterize.py`](../hardware/test-module/firmware/characterize.py) collects:

| phase      | what it is                                                       | data points        |
|------------|------------------------------------------------------------------|--------------------|
| `baseline` | stable readings with **no actuation**, `SETTLE_MS` apart         | `BASELINE_READS`   |
| `rotation` | mass change from one `ROTATION_STEP_DEG` auger rotation          | `POINTS_PER_ANGLE` |
| `refeed`   | the auger rotation fired **before every tap** (see below)        | `POINTS_PER_ANGLE` |
| `tap`      | mass change from `TAPS_PER_POINT` solenoid tap(s), tap-only      | `POINTS_PER_ANGLE` |

Design decisions baked in (from issue #130):

- **`POINTS_PER_ANGLE` is the one easily-editable knob** for how many
  data points to collect at each angle.  All tunables sit at the top of
  `characterize.py` and can also be overridden per run without editing
  anything: `characterize.run(points_per_angle=10, angles_deg=[30, 60])`.
- **Settling time**: every data point is a *stable-reading →
  actuation → `SETTLE_MS` wait → stable-reading* delta.  Stable means
  the balance itself reported `ST`, so each point waits out the
  HR-100A's ~1.5 s settling on both sides of the action.
- **Taps decay without rotation in between**: each tap knocks powder
  off the auger-tube lip, so consecutive taps dispense less and less.
  The sweep therefore fires a `REFEED_DEG` rotation before **every**
  tap trial, and measures that rotation into its own `refeed` row —
  the mass it displaces is fully accounted for and never attributed to
  the tap.  Bonus: with `REFEED_DEG == ROTATION_STEP_DEG` (the
  default), `refeed` rows are extra per-rotation data points, doubling
  the rotation sample size at each angle for free.
- **Uncertainty at each angle** comes out at three levels:
  1. `baseline` spread — the scale's noise + drift floor with nothing
     moving (the uncertainty underneath every single trial);
  2. sample standard deviation (n−1) of the per-rotation and per-tap
     deltas — the shot-to-shot repeatability;
  3. standard error of the mean (`std/√n`) — the uncertainty of the
     reported mean yield at that angle.
- **Empty-hopper protection**: `MAX_STALLS` consecutive rotations
  moving less than `MIN_FLOW_G` prompt the operator to refill; the
  low-flow rows stay in the data flagged `lowflow` (excluded from
  statistics by default), or type `keep` at the prompt for angles where
  near-zero flow is real.

## Running a sweep

Hardware: the PR #100 rig — Pico W + Tic T500 auger stepper + DRV8871
solenoid + dual angle servos, with the A&D HR-100A on RS-232 and the
collection cup on the pan.  The Pico needs the PR #100 firmware stack
uploaded (`config.py`, `tic.py`, `scale.py`, `dosing.py`, `main.py`)
plus `characterize.py`.

On the capture host (`pip install pyserial`):

```bash
python scripts/characterize_capture.py --port /dev/ttyACM0 \
    --powder-id xanthan \
    --powder "xanthan gum, lot 240515" --operator wm \
    --notes "auger 4, cup v2"
```

`--powder-id` is **required**: a short identifier for the powder
(`salt`, `xanthan`, `flour`, …).  It is normalized to a slug
(`"Xanthan Gum"` → `xanthan-gum`) and stamped everywhere the data
lives, so any file identifies its powder even after being copied off
the capture host:

- the run directory: `data/characterization/salt_20260721T190312Z/`
- **every filename** inside it: `salt_20260721T190312Z_trials.csv`,
  `…_summary.csv`, `…_run.json`, `…_raw_serial.log`
- a `powder_id` column on **every row** of both CSVs
- the `powder_id` field of the run document (schema v2), so MongoDB
  queries filter by powder directly:
  `db.characterization_runs.find({powder_id: "salt"})`

Keep `--powder` for the free-form description (lot number, grade);
`--powder-id` is the machine-readable key that ties runs of the same
material together across days and operators — reuse the exact same ID
for the same material.

The script interrupts the rig REPL, starts `characterize.run()`,
streams everything to your terminal, and relays your keyboard to the
Pico's prompts (`Enter` to continue, `keep` / `skip` / `abort`).  A run
of 7 angles × 5 points is ~20–25 min, dominated by settle waits; empty
the cup at the angle prompts so the pan never overloads.

Each run lands in `data/characterization/<powder-id>_<UTC-stamp>/`:

- `*_raw_serial.log` — every serial line, verbatim
- `*_trials.csv` — one row per measured action (all phases, flags kept)
- `*_summary.csv` — host-recomputed per-angle statistics (`n`, mean,
  std, SEM, min, max, RSD%), including the pooled `rotation+refeed` set
- `*_run.json` — the complete run document (below)

The on-device `SUM` rows and the host statistics are computed
independently and cross-checked in tests, so a corrupted capture is
detectable.  Simulation tests you can run without hardware:

```bash
python hardware/test-module/firmware/sim/test_characterize.py
python scripts/tests/test_characterize_capture.py
```

## Running remotely: Raspberry Pi Zero over Tailscale SSH

The Pico stays plugged into the Pi Zero (RPi OS) on the bench; you
drive the whole sweep from anywhere with `tailscale ssh pi@<zero>`.
The capture script needs no changes for this — the Zero *is* the
capture host.  One-time setup on the Zero:

1. **Serial**: the Pico enumerates on the Zero's USB OTG port as
   `/dev/ttyACM0` (use a data-capable micro-USB OTG cable, not
   charge-only).  Let your user open it without sudo:

   ```bash
   sudo usermod -aG dialout $USER   # then log out/in once
   ```

2. **Python environment**: RPi OS Bookworm blocks bare `pip install`
   (PEP 668), so use a venv; [piwheels](https://www.piwheels.org) is
   preconfigured on RPi OS and serves prebuilt ARM wheels, which
   matters on the Zero's slow CPU:

   ```bash
   sudo apt update && sudo apt install -y git python3-venv tmux
   git clone https://github.com/vertical-cloud-lab/powder-doser.git
   python3 -m venv ~/doser-venv
   ~/doser-venv/bin/pip install pyserial pymongo
   ```

   Note the original Pi Zero / Zero W is armv6 and slow, but the
   capture loop is I/O-bound (settle waits dominate), so it's plenty.

3. **Always capture inside `tmux`** — a dropped Tailscale session must
   not kill a 25-minute interactive run:

   ```bash
   tmux new -s doser     # reattach after a drop: tmux attach -t doser
   ~/doser-venv/bin/python scripts/characterize_capture.py \
       --port /dev/ttyACM0 --powder-id salt --operator wm --upload
   ```

   The operator prompts (empty the cup, refill the hopper) still need
   someone physically at the rig — coordinate over whatever channel
   you use, or run sweeps while you're in the room and only *retrieve*
   data remotely.

4. **Clock**: the Zero has no RTC, and every trial/document is
   timestamped.  Check `timedatectl` says `System clock synchronized:
   yes` before a run (automatic once the Zero has internet).

5. **Getting files off the Zero**: over the tailnet with
   `rsync -av pi@<zero>:powder-doser/data/characterization/ ./data/characterization/`
   — or skip copying entirely and let the Zero upload to MongoDB
   (next section), with the local files as the on-bench backup.

## Where the data goes (issue #126) and what you need to do

Issue #126 settled on the **one-document-per-event** model: each
characterization run becomes a single self-contained MongoDB document
(`kind: "characterization_run"`) holding the raw trials, both summary
sets, and provenance (powder, operator, git commit, and an echo of the
`config.py` parameters the run executed under).  A 7-angle × 5-point
run is ~40 KB — an Atlas free-tier cluster (512 MB) holds >10,000 runs,
and the local `run.json` is always written first, so nothing is lost if
the upload path is down.

One-time checklist to get the **Pi Zero uploading to MongoDB**:

1. **Create the Atlas cluster** — a free M0 at
   [cloud.mongodb.com](https://cloud.mongodb.com) (name suggestion:
   `powder-doser`).  No time-series collection needed for these run
   documents; a plain collection is right.
2. **Create a database user** with `readWrite` on the `powder_doser`
   database (Security → Database Access).
3. **Network Access: allowlist the Zero's *public* egress IP.**
   Tailscale only routes tailnet traffic — the Zero reaches Atlas
   through the lab network's ordinary internet connection, so the IP
   to allow is what `curl -s ifconfig.me` prints *on the Zero* (not
   its 100.x tailscale address).  If the lab IP is dynamic, allow the
   institution's range, or 0.0.0.0/0 temporarily — revisit before
   storing anything sensitive.
4. **Put the connection string in the Zero's environment**, never in
   the repo or on the command line.  On the Zero:

   ```bash
   install -m 600 /dev/null ~/.doser_env
   echo 'export MONGODB_URI="mongodb+srv://<user>:<password>@<cluster>.mongodb.net/"' >> ~/.doser_env
   echo '[ -f ~/.doser_env ] && . ~/.doser_env' >> ~/.bashrc
   ```

   (chmod-600 file kept out of git; sourced on every SSH login.)
5. **Verify once end-to-end**: `~/doser-venv/bin/python -c
   "import os, pymongo;
   pymongo.MongoClient(os.environ['MONGODB_URI'],
   serverSelectionTimeoutMS=15000).admin.command('ping');
   print('atlas ok')"` — if this hangs, it's step 3 (IP allowlist)
   ~95% of the time.
6. **Capture with `--upload`** (see the tmux invocation above).  A
   successful upload drops a `.uploaded` marker beside the run.json.
7. **Backfill safety net** — uploads that failed (Atlas down, Wi-Fi
   blip, `MONGODB_URI` unset) leave no marker, so a nightly cron on
   the Zero sweeps them up idempotently (`crontab -e`):

   ```cron
   0 3 * * * . $HOME/.doser_env && cd $HOME/powder-doser && $HOME/doser-venv/bin/python scripts/characterize_capture.py --upload-missing >> $HOME/doser-upload.log 2>&1
   ```

   The same command run by hand uploads all pending runs and exits;
   already-uploaded runs are never re-inserted.  A single old
   `run.json` can also be pushed with `--upload-file <path>`.
8. **Commit the CSVs** (or at least `run.json`) for small campaigns —
   git is a perfectly good secondary store at these sizes, and it
   keeps the data reviewable in PRs.  (`git` on the Zero, or `rsync`
   to a laptop first.)

Later steps from the #126 design (not needed to start collecting):
per-minute idle aggregates and a TTL'd raw stream, an AWS Lambda ingest
once the rig goes standalone-WiFi (the Atlas Data API is EOL), and
periodic offload to Hugging Face Datasets / Zenodo.  See the design
doc on the issue #126 branch:
[`docs/data-streaming-design.md`](https://github.com/vertical-cloud-lab/powder-doser/blob/claude/issue-126-20260709-1827/docs/data-streaming-design.md).

## Run document schema (v2)

v2 adds `powder_id` (v1 documents predate the field).

```jsonc
{
  "kind": "characterization_run",
  "schema_version": 2,
  "status": "ok",                       // ok | aborted | capture-interrupted
  "started_utc": "...", "ended_utc": "...",
  "powder_id": "xanthan",               // the key to query/group runs by
  "powder": "xanthan gum, lot 240515", "operator": "wm", "notes": "...",
  "git_commit": "<hash of the host repo at capture time>",
  "parameters": {                        // META rows from the device
    "points_per_angle": "5", "angles_deg": "0;15;30;45;60;75;90",
    "rotation_step_deg": "360.0", "taps_per_point": "1",
    "refeed_deg": "360.0", "settle_ms": "2000",
    "config.STEPPER_SPEED_RPM": "60", "config.TAP_ON_MS": "60", // ...
  },
  "trials": [                            // every measured action
    {"angle_deg": 45.0, "phase": "rotation", "trial": 0,
     "action": "360.0", "before_g": 0.1231, "after_g": 0.1742,
     "delta_g": 0.0511, "flag": "", "t_ms": 128840}
  ],
  "device_summary": [ /* SUM rows as computed on the Pico */ ],
  "host_summary":   [ /* recomputed + pooled rotation+refeed + RSD% */ ]
}
```

Feeding the optimizer (issue #124): the per-angle
`(mean, sem)` pairs for `rotation+refeed` and `tap` are exactly the
throughput model a dosing optimizer needs — `g/rev(angle)` for the
coarse phase and `g/tap(angle)` for the fine phase, each with its
uncertainty for acquisition functions that are noise-aware.
