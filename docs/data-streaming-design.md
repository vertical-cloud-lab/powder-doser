# Data streaming & storage design for the powder-doser scale

Status: **revision 2 (2026-07-31)** — issue
[#126](https://github.com/vertical-cloud-lab/powder-doser/issues/126).
Revision 1 (2026-07-09) was written before any of this existed; the
cluster, the Tailscale path to the rig, and real dose telemetry are now
live, so the numbers below are **measured rather than estimated** and
§0/§5/§8 have been rewritten around what the bench actually does.

Related: the rig in PR
[#100](https://github.com/vertical-cloud-lab/powder-doser/pull/100),
the characterization sweep in PR
[#131](https://github.com/vertical-cloud-lab/powder-doser/pull/131)
(issue #130), and the prior art in
[ac-dev-lab #113](https://github.com/AccelerationConsortium/ac-dev-lab/issues/113)
/ [autotrickler-scale](https://github.com/AccelerationConsortium/ac-dev-lab/tree/main/src/ac_training_lab/picow/autotrickler-scale).

## 0. Where this stands (2026-07-31)

What exists now:

- **The cluster is live.** `powder_doser` on Atlas holds
  `dose_runs` (5 documents) and `characterization_runs` (empty).
  `dbstats` reports 925 KB of data for those 5 documents — ~185 KB per
  run, which is 3–6× what this design budgets, for the reasons in §2.
- **The device speaks a parseable protocol.**
  `hardware/test-module/firmware/pid_dose.py` (PR #131) emits
  `M,`/`D,`/`E,`/`SUMMARY,` lines at ~10 Hz, including unstable (`U`)
  and dropped (`X`) frames. This is the tier-1 stream; nothing else
  needs to be invented on the device.
- **One upload path is automated**:
  `scripts/characterize_capture.py` builds and uploads a
  characterization run document. The **dose** path was not — the five
  documents in `dose_runs` were hand-assembled after the fact, in
  three different shapes (`doc_type` is `dose_run` twice and
  `pid_dose_telemetry` three times, with different field names for the
  same quantities), with no `schema_version`, no dedupe key, and no
  indexes beyond `_id`.
- **Transport is the Actions runner**, not the rig: GitHub Actions →
  Tailscale → `rpi-zero2w-powder-doser` → `mpremote` → Pico. The Pi is
  a bare bench host (`pyserial`, `pymongo`, `mpremote` in a venv; no
  service, no cron, no persisted data directory).

What this revision adds: `scripts/dose_run_capture.py` — the missing
dose-side capture/upload, closing tier 1 for real (§2, §8).

The open gap after that is tiers 2 and 3 (the idle stream), which
still have no producer, because nothing streams when a dose isn't
running.

## 1. Guiding principle: the dose document is the product

Continuous raw streaming is the *cheap* data; the *valuable* data is the
complete record of each dispense. So the design inverts the usual
telemetry-first approach:

- **Tier 1 (permanent, must-have): one document per dispense** — the
  full in-dose time series plus parameters, outcome, and provenance.
- **Tier 2 (permanent, tiny): 1-minute aggregates** of the idle scale
  signal (`min/max/mean/std/count`) — the drift and lab-conditions
  record.
- **Tier 3 (expiring, optional): raw idle readings**, record-on-change,
  TTL 30–90 days — for debugging only.

This bounds storage by *doses performed*, not by wall-clock time, which
is what makes a 512 MB free tier last years instead of weeks.

## 2. Tier 1: the dose document

`scripts/dose_run_capture.py` implements this. It consumes the
`pid_dose.py` line protocol — live from a pipe, or from a log for
backfill — and emits one document per run:

```jsonc
{
  "schema_version": 1,
  "doc_type": "dose_run",
  "run_uid": "3f9a…",                  // SHA-1 of the device stream
  "powder_id": "salt",
  "started_utc": "2026-07-29T20:52:00Z",
  "operator": "wm",
  "controller": "pid-v2",
  "gains": {"kp": 150.0, "ki": 8.0, "t_ant_s": 1.1, "tol_g": 0.002},
  "summary": {"status": "ok", "final_g": 1.0012, "target_g": 1.0,
              "error_mg": 1.2, "within_tolerance": true, "taps": 0},
  "n_samples": 356, "duration_s": 34.9,
  "series": {                           // columnar; real run2 values
    "t_ms":         [140, 235, 331, 427, …],
    "mass_g_rle":   [[1.9243, 104], [0.0, 11], [0.0071, 1], …],
    "tilt_deg_rle": [[0.0, 106], [1.1, 1], [2.4, 1], …],
    "rpm_cmd_rle":  [[0.0, 106], [45.0, 58], [44.4, 1], …],
    "taps_cum_rle": [[0, 356]],
    "frame_rle":    [["S", 115], ["U", 83], ["S", 6], …],
    "phase_rle":    [["preroll", 104], ["tare", 1], ["dose", 140], …]
  },
  "events": [{"t_ms": 10052, "text": "tare (Z) sent"}, …],
  "provenance": {"commit": "95a2539", "dirty": false, "source": "…log"},
  "device": {"host": "rpi-zero2w-powder-doser", "mcu": "pico-w",
             "firmware": "pid_dose.py"}
}
```

Three decisions worth keeping:

- **Columnar + RLE, not one sub-document per sample.** BSON repeats
  every field name in every sub-document, so a row-wise layout is
  mostly field names. More importantly, the HR-100A *repeats a reading
  until it changes*: a real 4,450-sample run collapses to 121 runs of
  constant mass, 31 of tilt, and 5 of phase. Measured on the three real
  logs in PR #131 (`data/pid-dose/2026-07-29_salt/`):

  | run | samples | this layout | row-wise |
  |---|---|---|---|
  | run2 (clean 1 g dose, 35 s) | 356 | **9.4 KB** | 41.1 KB |
  | run3 (0.5 g, stalls, 109 s) | 1,100 | **17.2 KB** | 124.5 KB |
  | run1 (bridged hopper, 442 s) | 4,450 | **56.3 KB** | 502.3 KB |

  ~9× smaller, lossless, and still plain BSON arrays — queryable and
  aggregatable, no custom binary codec to decode later.
  `samples_from_document()` is the one supported way to read it back.
- **`run_uid` = SHA-1 of the device stream.** The Pico has no clock and
  `t_ms` restarts every run, so nothing in the stream is globally
  unique. Hashing it gives a dedupe key, which makes `--upload` an
  idempotent upsert: re-running a backfill updates instead of
  duplicating. Host-side annotations (operator, notes) deliberately do
  not change it.
- **Provenance is a pointer, not a snapshot**: commit hash + `dirty`
  flag + the controller gains the device itself reported. Git is the
  archive; the `dirty` flag is the honest part, since a run made from
  an edited working tree is not reproducible from the hash alone. If
  running uncommitted firmware becomes routine, add a
  `firmware_versions` collection keyed by content hash so the source is
  stored once per version rather than once per dose.

**Do not put verbatim REPL logs in the document.** That is most of the
185 KB/run in the existing five documents; the raw log belongs in
`data/` in the repo (where it is diffable and free), with the document
carrying the parsed series. A document with `logs` embedded costs about
as much as three parsed runs.

Store dose documents in a *regular* collection, not a time-series one —
they are event records, not metric streams, and want normal indexing.
`--ensure-indexes` creates `run_uid` (unique), `(powder_id,
started_utc)`, and `doc_type`.

## 3. Tier 2: drift & lab conditions without raw-forever

Two facts make this cheap:

1. **A dead-band of exactly one scale count is lossless.** The HR-100A
   cannot report a change smaller than its resolution, so "record only
   when the displayed value changes, plus a heartbeat every 60 s"
   preserves *every value the scale ever reported*. What it drops is
   repeated identical readings, whose only information ("no change
   between heartbeats") the heartbeat timestamps already bound. Small
   changes and slow drift are therefore fully captured — no trade-off
   against the drift-tracking goal. The tier-1 measurements above are
   the empirical proof: 4,450 polls collapsed to 121 constant runs with
   nothing lost.
2. **Noise statistics live in the aggregates.** Per-minute
   `min/max/mean/std/count` (~1,440 docs/day ≈ ~5 MB/month including
   index) captures the vibration/HVAC/draft signature that makes the
   scale a lab-conditions sensor. `std` and `count` (count spikes =
   flicker = drafts or vibration) are the interesting columns. Keep
   these forever; they are too small to matter.

Worst case for tier 3 is an idle scale flickering ±1 count
continuously (~12 MB/day in a plain collection, ~1–2 MB/day in a
time-series collection). That is exactly why tier 3 gets a TTL and
tier 2 is the permanent record.

**Producer, once one exists.** Nothing polls the scale between doses
today — the Pico only runs `pid_dose.py`/`characterize.py` on demand.
Tier 2/3 need an idle poller (a `Q`-poll loop on the Pico plus a
long-lived host process on the Pi, i.e. the first thing here that has
to be a systemd service rather than an Actions-triggered command). That
is the natural moment to reconsider MQTT (§5), and the point at which
"streaming" in this issue's title becomes literal.

## 4. MongoDB free tier: what is and isn't restricted

- **Time-series collections are supported on Atlas M0** — they are not
  in the [free-tier unsupported list](https://www.mongodb.com/docs/atlas/reference/free-shared-limitations/).
  Use one for tier 3 (and optionally tier 2).
- **Change streams do not work on time-series collections** (any tier),
  so nothing can "trigger on insert" of raw readings — the uploader
  owns downsampling.
- **Atlas Online Archive requires M10+**, so the periodic offload (§6)
  must be a scripted export, not an Atlas feature.
- Other M0 limits (100 ops/s, 500 connections, 10 GB ingress/7 days)
  are far above this workload.

Budget under this design, using the measured tier-1 sizes: ~10–55 KB
per dose run (say 25 KB typical) → **512 MB is ~20,000 runs**, or
~1,900 runs at the current hand-assembled 185 KB/run. Tier 2 adds
~5 MB/month; tier 3 is bounded by its TTL at ~50–100 MB steady-state.
Re-check with `dbstats` once tier 3 is actually ingesting — that is the
term with real uncertainty.

## 5. Transport: who talks to Mongo?

The rig is **host-attached**, and as of this revision the host chain is
longer than revision 1 assumed:

```
GitHub Actions runner ──Tailscale SSH──> Pi (rpi-zero2w-powder-doser)
                                           └─ mpremote ──USB──> Pico W ──RS-232──> HR-100A
                                           └─ pymongo ──────> Atlas M0
```

- **Phase 1 (now): host-direct pymongo, from the Pi.** The Pi already
  has `pymongo` and the connection string arrives as an environment
  variable; `dose_run_capture.py` reads it from `MONGODB_URI` and never
  echoes it. The upload belongs in the same pipe as the run
  (`mpremote … | tee raw.log | dose_run_capture.py - --upload`) so a
  captured run cannot be forgotten, and so the document is a parse of
  the stream rather than a later reconstruction. Runs captured offline
  backfill later from the log; `run_uid` makes that safe.
- **Phase 2 (when the rig goes standalone WiFi): AWS Lambda ingest.**
  No broker is needed for persistence. A Lambda Function URL fronting
  pymongo fits the dose-document model specifically, because the
  request rate is one POST per dose (plus one per minute for
  aggregates), not one per reading:
  - Free tier (1M requests/month) is ~4 orders of magnitude of
    headroom; a Function URL avoids API Gateway cost.
  - Reuse the `MongoClient` outside the handler.
  - Auth: a per-device bearer token in the header, stored in
    `my_secrets.py` on the Pico and validated in the Lambda. (The old
    device→Atlas Data API path is dead — EOL 2025-09-30.)
  - Pico-side: one `urequests.post()` of a ~25 KB JSON at dose end is
    easy; do **not** attempt per-reading HTTPS from MicroPython.
- **MQTT (HiveMQ) is only needed for live fan-out** — a scale-monitor
  view, or remote orchestration. It is orthogonal to persistence and
  can be added independently, and it becomes interesting at the same
  time as the tier-2/3 idle poller (§3). If revived, fix the payload
  schema and the credential exposure noted earlier in #126 first.

## 6. Long-term offload (Zenodo etc.)

Since Online Archive is unavailable on M0, offload is a scheduled
GitHub Action (this repo already runs Actions):

1. Export closed periods (e.g. completed months, on a ~6-month cadence)
   of dose/characterization documents + tier-2 aggregates via
   `mongoexport` → Parquet/JSONL.gz. Decode `series` through
   `samples_from_document()` on the way out so the archive is flat and
   tool-agnostic.
2. Publish:
   - **Hugging Face Datasets** for the rolling archive — appendable,
     has a data viewer, and the org already lives on HF; then delete
     the exported tier-3 periods from Atlas if space demands it.
   - **Zenodo** for citable, DOI-versioned snapshots at milestones
     (paper submission, campaign end). Zenodo records are immutable —
     publish only curated, closed periods, one version per deposit.
3. The "pain" is contained: one workflow file with `cron` +
   `workflow_dispatch`, and under this design it is optional for years.

## 7. Schema hygiene for what is already in the cluster

The five existing `dose_runs` documents predate this schema and are
worth normalizing before the collection grows:

- Two shapes and two `doc_type` values (`dose_run`,
  `pid_dose_telemetry`) describe the same kind of event; unify on
  `dose_run` and let `controller` distinguish PID from three-phase.
- Same quantity, different names across documents (`final_g` vs
  `runs.<id>.summary.final_g`; `gains` vs per-run `meta`). The
  schema in §2 is the target.
- No `schema_version` and no `run_uid`: re-running a backfill would
  duplicate them. Anything migrated should be given both (for
  documents whose raw log survives in the repo, re-deriving through
  `dose_run_capture.py` is better than editing in place).
- `started_utc` is a string here and a `datetime` there; store BSON
  dates.

This is a small one-off script plus `--ensure-indexes`. It is
deliberately **not** run automatically — it rewrites a shared cluster,
so it should be a reviewed, explicit action.

## 8. Implementation order (updated)

1. ~~Dose-document capture + host uploader~~ — **done**:
   `scripts/dose_run_capture.py` (+ tests). Wire it into the bench
   procedure so every dose run uploads as it happens.
2. Run `--ensure-indexes` once, then migrate/re-derive the five legacy
   documents (§7).
3. Point `characterize_capture.py` at the same conventions
   (`schema_version`, `run_uid`, columnar series) so both collections
   read alike.
4. Idle poller for tiers 2 and 3 (§3) — the first piece that needs a
   long-lived service on the Pi, and where MQTT becomes worth
   revisiting.
5. Lambda ingest + on-device WiFi upload only when the rig actually
   needs to be untethered.
6. Offload Action when `dbstats` says so, or at first publication.
