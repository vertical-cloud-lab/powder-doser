# Data streaming & storage design for the powder-doser scale

Status: **draft for discussion** — issue
[#126](https://github.com/vertical-cloud-lab/powder-doser/issues/126).
Builds on the rig in PR
[#100](https://github.com/vertical-cloud-lab/powder-doser/pull/100)
(`copilot/integrate-scale-feedback-loop`) and the prior art in
[ac-dev-lab #113](https://github.com/AccelerationConsortium/ac-dev-lab/issues/113)
/ [autotrickler-scale](https://github.com/AccelerationConsortium/ac-dev-lab/tree/main/src/ac_training_lab/picow/autotrickler-scale).

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

The `Doser` in PR #100 already produces a `DoseResult`
(`status, target_g, dispensed_g, coarse_revs, taps, elapsed_s`). During
a dose, the control loop is the only reader of the scale UART, so it
can log every reading and actuator event it already takes into a RAM
buffer and emit one JSON document at the end.

```jsonc
{
  "schema": 1,
  "device_id": "picow-a1b2c3",
  "t_start": 1783019456000,            // UTC epoch ms (host-stamped)
  "target_g": 0.5000,
  "result": {                           // DoseResult verbatim
    "status": "ok", "dispensed_g": 0.5002,
    "coarse_revs": 3.42, "taps": 17, "elapsed_s": 41.3
  },
  "series": {                           // parallel arrays (compact)
    "t_ms":  [0, 210, 430, ...],        // offsets from t_start
    "grams": [0.0000, 0.0412, ...],
    "stable":[false, false, ...],
    "event": [null, "auger:15deg", null, "tap:3", ...]
  },
  "provenance": {
    "firmware_git": "43ca602-dirty",    // git describe from the host
    "repo": "vertical-cloud-lab/powder-doser",
    "config": { "DOSE_COARSE_FRACTION": 0.9, "...": "full config.py dump" },
    "scale": { "model": "HR-100A", "resolution_g": 0.0001 },
    "operator": "sgbaird",
    "powder": "xanthan gum"
  }
}
```

Notes:

- **Size**: a 2-minute dose at ~10 Hz is ~1,200 samples; as parallel
  arrays that is ~15–40 KB. The 16 MB BSON document limit is three
  orders of magnitude away, and 512 MB holds **>10,000 doses** even in a
  plain (non-time-series) collection. Store dose documents in a
  *regular* collection — they are event records, not metric streams,
  and you want normal indexing/updating on them.
- **Code snapshot**: store the commit hash + `--dirty` flag + the full
  `config.py` values, *not* the source text — git is the source
  archive. If running uncommitted firmware is a real workflow, add a
  small `firmware_versions` collection keyed by content hash and
  reference it, so the source is stored once per version rather than
  per dose.
- **RAM**: ~1,200 samples of `(int, float, bool)` is well within the
  Pico W's budget; if doses run long, halve the in-dose sampling or
  flush partial chunks over USB mid-dose.

## 3. Tier 2: drift & lab conditions without raw-forever

Two facts make this cheap:

1. **A dead-band of exactly one scale count is lossless.** The HR-100A
   cannot report a change smaller than its 0.1 mg resolution, so
   "record only when the displayed value changes, plus a heartbeat
   every 60 s" preserves *every value the scale ever reported*. What it
   drops is repeated identical readings, whose only information ("no
   change between heartbeats") the heartbeat timestamps already bound.
   Small changes and slow drift are therefore fully captured — no
   trade-off against Sterling's drift-tracking goal.
2. **Noise statistics live in the aggregates.** Per-minute
   `min/max/mean/std/count` (~1,440 docs/day ≈ ~5 MB/month including
   index) captures the vibration/HVAC/draft signature that makes the
   scale a lab-conditions sensor. `std` and `count` (count spikes =
   flicker = drafts or vibration) are the interesting columns. Keep
   these forever; they are too small to matter.

One caveat: an idle 0.1 mg scale can flicker ±1 count nearly
continuously in a bad environment, so worst-case Tier 3 volume
approaches continuous 1 Hz (~12 MB/day in a plain collection, ~1–2
MB/day in a time-series collection). That is exactly why Tier 3 gets a
TTL and Tier 2 is the permanent record.

## 4. MongoDB free tier: what is and isn't restricted

- **Time-series collections are supported on Atlas M0** — they are not
  in the [free-tier unsupported list](https://www.mongodb.com/docs/atlas/reference/free-shared-limitations/).
  Use one for Tier 3 (and optionally Tier 2). The earlier hedge in this
  issue was only about *how the 512 MB quota is metered* for bucketed
  collections — verify empirically with `db.stats()` after a day of
  real ingestion.
- **Change streams do not work on time-series collections** (any tier),
  so nothing can "trigger on insert" of raw readings — the uploader
  owns downsampling.
- **Atlas Online Archive requires M10+**, so the planned periodic
  offload (§6) must be a scripted export, not an Atlas feature.
- Other M0 limits (100 ops/s, 500 connections, 10 GB ingress/7 days)
  are far above this workload.

Budget under this design: Tier 1 ~30 KB/dose, Tier 2 ~5 MB/month,
Tier 3 bounded by TTL at ~50–100 MB steady-state. The free tier
comfortably holds **1–2+ years** before any offload is forced.

## 5. Transport: who talks to Mongo?

Key fact: the PR #100 rig is **host-attached** — a computer drives the
Pico over USB-serial. That machine runs CPython, so the simplest
correct answer today is:

```
Pico W ──USB-serial──> host (CPython)
                         └─ pymongo ──> Atlas M0
```

- **Phase 1 (now): host-direct pymongo.** The host script that issues
  `g <grams>` also receives the dose document, stamps provenance
  (git hash, operator, powder), and `insert_one`s it. Zero new
  infrastructure, no broker, no Lambda, works offline (queue documents
  to disk, upload when connected). Secrets stay in the host's env.
- **Phase 2 (when the rig goes standalone WiFi): AWS Lambda ingest.**
  Sterling's instinct is right that no broker is needed for
  persistence. A Lambda Function URL fronting pymongo is a good fit
  *for the dose-document model specifically*, because the request rate
  is one POST per dose (plus one per minute for aggregates), not one
  per reading:
  - Free tier (1M requests/month) is ~4 orders of magnitude of
    headroom; a Function URL avoids API Gateway cost.
  - Reuse the `MongoClient` outside the handler (cold-start connection
    churn is the classic Lambda+Mongo failure mode; at this rate it is
    a non-issue, but do it anyway).
  - Auth: a per-device bearer token in the header, stored in
    `my_secrets.py` on the Pico; validate in the Lambda. (The old
    device→Atlas Data API path is dead — EOL 2025-09-30.)
  - Pico-side: one `urequests.post()` of a 30 KB JSON at dose end is
    easy; do **not** attempt per-reading HTTPS from MicroPython.
- **MQTT (HiveMQ) is only needed for live fan-out** — e.g. the
  scale-monitor HF space watching the balance in real time, or remote
  orchestration. It is orthogonal to persistence and can be added (or
  not) independently. If revived, fix the payload schema and the
  credential exposure noted earlier in #126 first.

## 6. Long-term offload (Zenodo etc.)

Since Online Archive is unavailable on M0, offload is a scheduled
GitHub Action (this repo already runs Actions):

1. Export closed periods (e.g. completed months, on a ~6-month cadence)
   of `dose_events` + Tier 2 aggregates via `mongoexport` →
   Parquet/JSONL.gz.
2. Publish:
   - **Hugging Face Datasets** for the rolling archive — appendable,
     has a data viewer, and the org already lives on HF; then delete
     the exported raw Tier 3 periods from Atlas if space demands it.
   - **Zenodo** for citable, DOI-versioned snapshots at milestones
     (paper submission, campaign end). Zenodo records are immutable —
     publish only curated, closed periods, one version per deposit.
3. The "pain" is contained: it's one workflow file with `cron` +
   `workflow_dispatch`, and under this design it's optional for years —
   Tier 1+2 alone won't hit 512 MB for a long time.

## 7. Suggested implementation order

1. **Dose-document capture** in `dosing.py`/`main.py` (RAM buffer →
   JSON over USB at dose end) + a small host uploader
   (`scripts/dose_uploader.py`: pyserial + pymongo, disk queue for
   offline). *This alone delivers the science record.*
2. Tier 2 aggregator in the same host script (it already sees every
   reading when polling idle).
3. Tier 3 raw-on-change into a time-series collection with
   `expireAfterSeconds`, once 1–2 prove out.
4. Lambda ingest + on-device WiFi upload only when the rig actually
   needs to be untethered.
5. Offload Action when `db.stats()` says so, or at first publication.
