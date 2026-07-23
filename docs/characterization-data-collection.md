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

On the bench host (`pip install pyserial`):

```bash
python scripts/characterize_capture.py --port /dev/ttyACM0 \
    --powder-id xanthan --powder "xanthan gum, batch 3" \
    --operator wm --notes "auger 4, cup v2"
```

`--powder-id` is **required**: a short identifier for the powder in
the hopper (`salt`, `xanthan`, `flour`, ...) that is stamped on every
file name, on every CSV row, into the device's own serial stream (a
`META,powder_id` row, so even `raw_serial_*.log` is self-describing),
and as a top-level field of the run document — every artifact says
which powder it belongs to even after it is copied out of its run
directory.  It is normalized to a slug (lowercase,
letters/digits/dash/underscore/dot), so pick consistent IDs and reuse
them across runs; Mongo queries like `{powder_id: "salt"}` then pull a
powder's whole history.  `--powder` stays free-form for the longer
description (brand, batch, lot number).

The script interrupts the rig REPL, starts `characterize.run()`,
streams everything to your terminal, and relays your keyboard to the
Pico's prompts (`Enter` to continue, `keep` / `skip` / `abort`).  A run
of 7 angles × 5 points is ~20–25 min, dominated by settle waits; empty
the cup at the angle prompts so the pan never overloads.

Each run lands in `data/characterization/<UTC-stamp>_<powder-id>/`:

- `raw_serial_<powder-id>.log` — every serial line, verbatim
- `trials_<powder-id>.csv` — one row per measured action (all phases,
  flags kept), each row leading with the powder ID
- `summary_<powder-id>.csv` — host-recomputed per-angle statistics
  (`n`, mean, std, SEM, min, max, RSD%), including the pooled
  `rotation+refeed` set
- `run_<powder-id>.json` — the complete run document (below)

The on-device `SUM` rows and the host statistics are computed
independently and cross-checked in tests, so a corrupted capture is
detectable.  Simulation tests you can run without hardware:

```bash
python hardware/test-module/firmware/sim/test_characterize.py
python scripts/tests/test_characterize_capture.py
```

## Running remotely: Pi Zero + Tailscale SSH

The Pico plugs into a Raspberry Pi Zero (RPi OS) that sits on the
tailnet; the Zero **is** the "bench host" above — you SSH into it over
Tailscale and run the capture script there, and it uploads straight to
MongoDB over its own internet connection.  What the Zero needs:

1. **One-time setup** (SSH in: `ssh <user>@<zero-hostname>` using the
   machine name from the Tailscale admin console):

   ```bash
   sudo apt update && sudo apt install -y git python3-pip python3-venv tmux
   git clone https://github.com/vertical-cloud-lab/powder-doser.git
   cd powder-doser
   python3 -m venv ~/.venvs/doser
   ~/.venvs/doser/bin/pip install pyserial "pymongo[srv]"
   sudo usermod -aG dialout $USER    # serial-port access; re-login after
   ```

   RPi OS's pip pulls prebuilt wheels from piwheels, so `pymongo`
   installs without compiling even on the Zero 1's armv6.  The
   `[srv]` extra (dnspython) is required for Atlas's
   `mongodb+srv://` connection strings — plain `pip install pymongo`
   will fail to resolve them.

2. **Check the Pico enumerates**: with the Pico in the Zero's USB
   *data* port (the middle micro-USB on a Zero, not PWR — via an OTG
   adapter/shim), `ls /dev/ttyACM*` should show `/dev/ttyACM0`.

3. **`MONGODB_URI` on the Zero** — in an env file, never in the repo:

   ```bash
   mkdir -p ~/.config/powder-doser
   printf 'export MONGODB_URI="mongodb+srv://<user>:<pw>@<cluster>.mongodb.net/"\n' \
       > ~/.config/powder-doser/env
   chmod 600 ~/.config/powder-doser/env
   ```

4. **Atlas must allow the Zero's egress IP.**  Uploads do *not* go
   through Tailscale — that only carries your SSH session; pymongo
   goes out the Zero's normal internet connection.  So the IP to
   allowlist (Atlas → Security → Network Access) is what `curl -s
   ifconfig.me` prints *on the Zero* (the lab/home router's public
   IP), not any `100.x` Tailscale address.  If that IP is dynamic,
   allow the ISP range or temporarily `0.0.0.0/0` with a strong
   database password.

5. **Run the sweep inside `tmux`** so a dropped SSH session (laptop
   sleep, Wi-Fi blip) doesn't kill a 25-minute interactive run:

   ```bash
   tmux new -s sweep
   source ~/.venvs/doser/bin/activate
   source ~/.config/powder-doser/env
   python scripts/characterize_capture.py --port /dev/ttyACM0 \
       --powder-id salt --operator wm --upload
   ```

   Detach with `Ctrl+B` `D`; reattach any time (from any tailnet
   machine) with `tmux attach -t sweep`.  The operator prompts (empty
   the cup, refill the hopper) still need someone physically at the
   rig; whoever is SSH'd in answers them in the tmux session.

6. **Nothing is lost offline.**  Every run is written to the Zero's SD
   card first (`data/characterization/...`); if the upload fails or
   `--upload` was forgotten, backfill later with
   `--upload-file .../run_<powder-id>.json`, and copy files off over
   the tailnet with `scp`/`rsync` if wanted.

7. **Clock**: run timestamps come from the Zero, which has no RTC —
   check `timedatectl` shows `System clock synchronized: yes` (RPi OS
   NTP default) so `started_utc` is trustworthy.

### As-built state of the lab Zero (installed 2026-07-21)

The lab's bench host is a **Pi Zero 2 W** (aarch64, Debian 13), so the
armv6/piwheels caveat above doesn't apply to it.  The setup that is
actually on the device deviates slightly from the generic instructions
above — recorded here so it can be reproduced:

- **No git clone.**  The repo tip is ~135 MB (CAD/hardware assets),
  which is a lot to pull over the Zero's residential Wi-Fi for two
  Python files.  Instead the needed files were copied over SSH and live
  at `~/powder-doser/scripts/characterize_capture.py` (host capture)
  and `~/powder-doser/hardware/test-module/firmware/characterize.py`
  (to be copied onto the Pico with `mpremote cp`).  If the full repo is
  ever wanted on the Zero, prefer a blob-filtered sparse clone
  (`git clone --filter=blob:none --sparse ...`) over a plain clone.
- **Venv** at `~/powder-doser-venv` (not `~/.venvs/doser`), with
  `pymongo` 4.17, `pyserial` 3.5, and `mpremote` 1.28 installed.
- **Credentials** at `~/.config/powder-doser/env` (mode 600), in
  `export MONGODB_URI='...'` form, holding a **scoped Atlas user**
  (`readWrite` on `powder_doser` only — not the admin user).
- **Verified end-to-end**: a smoke `--upload-file` run executed on the
  Zero itself inserted into `powder_doser.characterization_runs`, which
  also confirms the Atlas network allowlist admits the Zero's egress
  IP.  NTP sync was confirmed at the same time.

So a real sweep on this device is:

```bash
tmux new -s sweep
source ~/.config/powder-doser/env
~/powder-doser-venv/bin/python ~/powder-doser/scripts/characterize_capture.py \
    --port /dev/ttyACM0 --powder-id salt --operator wm --upload
```

### Atlas users and multiple clusters

Atlas database users live at the **project** level, not the cluster
level: a user created without the "restrict to specific clusters"
option works on every cluster in the project, including ones created
later.  Two consequences for growth past the free tier's 512 MB:

- **Same project, new (Flex/paid) cluster**: the existing user and
  password just work — only the host part of the connection string
  changes, since URIs are always per-cluster.
- **Second free (M0) cluster**: Atlas allows only one M0 per project,
  so a second free cluster means a **new project**, and users do *not*
  carry across projects — the scoped user would need to be recreated
  there and the Zero's env file updated.

At ~40 KB per run document, 512 MB is >10,000 runs, so this is not a
near-term concern.

## Where the data goes (issue #126) and what you need to do

Issue #126 settled on the **one-document-per-event** model: each
characterization run becomes a single self-contained MongoDB document
(`kind: "characterization_run"`) holding the raw trials, both summary
sets, and provenance (powder, operator, git commit, and an echo of the
`config.py` parameters the run executed under).  A 7-angle × 5-point
run is ~40 KB — an Atlas free-tier cluster (512 MB) holds >10,000 runs,
and the local `run.json` is always written first, so nothing is lost if
the upload path is down.

One-time checklist on your end:

1. **Create the Atlas cluster** — a free M0 at
   [cloud.mongodb.com](https://cloud.mongodb.com) (name suggestion:
   `powder-doser`).  No time-series collection needed for these run
   documents; a plain collection is right.
2. **Create a database user** with `readWrite` on the `powder_doser`
   database (Security → Database Access).
3. **Allow the bench host's IP** (Security → Network Access).  For a
   lab machine on dynamic IP, allow the campus range or 0.0.0.0/0
   temporarily — revisit before storing anything sensitive.
4. **Put the connection string in the environment**, never in the repo
   or on the command line:

   ```bash
   pip install "pymongo[srv]"
   export MONGODB_URI="mongodb+srv://<user>:<password>@<cluster>.mongodb.net/"
   ```

   (On the shared bench machine, put it in `~/.bashrc` or a
   `direnv`-style `.envrc` that is gitignored.)
5. **Capture with `--upload`**:

   ```bash
   python scripts/characterize_capture.py --port /dev/ttyACM0 \
       --powder-id xanthan --operator wm --upload
   ```

   Offline or forgotten runs backfill later:

   ```bash
   python scripts/characterize_capture.py --upload-file \
       data/characterization/20260721T190000Z_xanthan/run_xanthan.json
   ```

   (A `run.json` from before the powder-ID change backfills with
   `--upload-file ... --powder-id <id>`, which stamps the ID into the
   document on the way up.)

6. **Commit the CSVs** (or at least `run.json`) for small campaigns —
   git is a perfectly good secondary store at these sizes, and it keeps
   the data reviewable in PRs.

Later steps from the #126 design (not needed to start collecting):
per-minute idle aggregates and a TTL'd raw stream, an AWS Lambda ingest
once the rig goes standalone-WiFi (the Atlas Data API is EOL), and
periodic offload to Hugging Face Datasets / Zenodo.  See the design
doc on the issue #126 branch:
[`docs/data-streaming-design.md`](https://github.com/vertical-cloud-lab/powder-doser/blob/claude/issue-126-20260709-1827/docs/data-streaming-design.md).

## Run document schema (v1)

```jsonc
{
  "kind": "characterization_run",
  "schema_version": 1,
  "status": "ok",                       // ok | aborted | capture-interrupted
  "started_utc": "...", "ended_utc": "...",
  "powder_id": "xanthan",               // required slug; query key across runs
  "powder": "xanthan gum, batch 3",     // free-form description
  "operator": "wm", "notes": "...",
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
