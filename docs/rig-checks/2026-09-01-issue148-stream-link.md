# 2026-09-01 — issue #148: stream link for the 2 g salt dose, and capturing it at run time

The issue #148 demo dose (2 g salt, `status ok`, 1.9963 g) was recorded
on the bench livestream like every other run, but the link had to be
reconstructed by hand afterwards. This note records the link, how its
anchor was derived, and the change that makes future runs record their
own link.

## The link

**<https://youtu.be/BH0wATmJbMs?t=20947>**

| moment | UTC | offset | `t=` |
|---|---|---|---|
| broadcast content `t=0` | 11:01:04 | 0:00:00 | — |
| jump link (15 s lead-in) | 16:50:11.6 | 5:49:07.6 | 20947 |
| capture start / tare | 16:50:26.6 | 5:49:22.6 | 20963 |
| block G start | 16:50:30.1 | 5:49:26.1 | 20966 |
| dose start (auger, bulk phase) | 16:50:32.2 | 5:49:28.2 | 20968 |
| dose complete — 1.9963 g | 16:53:19.2 | 5:52:15.2 | 21135 |

Broadcast: `BH0wATmJbMs`, "powder doser stream picam-d1pr, 2026-09-01
UTC 11:00", 7:58:58, archived.

## Anchoring, and why `t=0` is not 11:00:00

Three clocks disagree about when a broadcast starts, and the difference
matters: at 55 rpm the bulk phase turns an auger revolution about every
second, so a minute of error is a minute of watching the wrong thing.

| clock | value for `BH0wATmJbMs` |
|---|---|
| title's nominal window | 11:00:00 |
| `release_timestamp` (broadcast accepted) | 11:01:10 |
| **content `t=0`** | **11:01:04** |

The encoder needs about a minute to come up after the roll-over fires,
which is the 11:00:00 → 11:01:10 gap; YouTube's live ingest latency then
puts the first archived fragment slightly *before* the accepted time,
which is the −6 s.

That −6 s is not a guess. It was measured on `w1D5DRiHFWM`
(2026-08-04 19:00 UTC) by reading the camera's burned-in overlay clock
out of decoded frames — see `docs/battery-runs/stream-registry.json` —
where `release_timestamp` was 19:01:12 and content `t=0` was 19:01:06.

Cross-check on the same quantity, using only arithmetic: these
broadcasts are cut by the next roll-over, so `content_t0 + duration`
should land on a 03:00 / 11:00 / 19:00 UTC boundary.

| broadcast | duration | `content_t0 + duration` |
|---|---|---|
| `w1D5DRiHFWM` (calibrated) | 28733 s | 02:59:59 — 1 s early |
| `BH0wATmJbMs` (this one) | 28738 s | 19:00:02 — 2 s late |

Both land within the ±3 s uncertainty quoted for the anchor, from two
independent directions, which is why the constant is applied rather than
re-derived per broadcast. Frame-level work (picking out a single auger
revolution) still wants a real calibration entry in
`stream-registry.json`; `scripts/stream_anchor.py` prefers one whenever
it exists.

This run's link was **not** verified against a decoded frame: `ffmpeg`
is not installed on the doser Pi, and installing one to pull fragments
over its residential link was not worth it for a ±3 s answer with a 15 s
lead-in.

## Capturing it at run time (the actual fix)

`scripts/stream_anchor.py` (new) resolves a UTC instant to a broadcast
and an offset, and `scripts/powder_battery_capture.py` now calls it as
the last step before writing a run, so `run_<id>.json` — and therefore
the MongoDB document — carries:

```json
"video": {
  "video_id": "BH0wATmJbMs",
  "url": "https://youtu.be/BH0wATmJbMs?t=20947",
  "content_t0_utc": "2026-09-01T11:01:04+00:00",
  "anchor": "release_timestamp-6s",
  "anchor_uncertainty_s": 3,
  "started_t_s": 20962.6, "ended_t_s": 21135.2,
  "blocks": [{"block": "G", "t_s": 20966.1, "url": "..."}],
  "doses":  [{"n": 0,       "t_s": 20968.2, "url": "..."}]
}
```

Deliberately best effort. It is the only network step a capture makes
besides `--upload`, it runs *after* the run is complete, it is capped at
90 s, and every failure — no yt-dlp, no network, no covering broadcast,
a listing that has not caught up with a stream that started minutes ago
— lands in `video.error` and leaves the run otherwise untouched. Skip it
entirely with `--no-stream-link`.

Backfill a run that missed it (or predates the change):

    python scripts/stream_anchor.py --run-json run_<id>.json --push

`SCHEMA_VERSION` goes 3 → 4. Read `video` optionally: a backfilled
document keeps the `schema_version` it was captured with, so a v3
document can carry a `video` block — as this run's does.

Resolution needs the Pi's residential IP (YouTube bot-blocks the CI
runner's datacenter range) while `MONGODB_URI` lives on the runner, so
the two halves can be split across machines: resolve on the Pi, then
`--no-resolve --push` on the runner.

## Pi-side changes

Recorded here per CLAUDE.md — the doser Pi's `~/powder-doser/` is a
plain directory, not a checkout, so nothing there is under version
control.

- `~/powder-doser/scripts/stream_anchor.py` — new, copy of this branch's.
- `~/powder-doser/scripts/powder_battery_capture.py` — replaced with
  this branch's patched copy. The previous file (byte-identical to
  `claude/issue-116-20260821-1907`) is kept as
  `powder_battery_capture.py.bak-20260901`.
- `~/powder-doser/data/battery/20260901T165026Z_salt/run_salt.json` now
  has its `video` block.

No hardware was actuated: no serial port was opened, no dose was run.

## MongoDB

`powder_doser.battery_runs`, `_id 6a970324467c700d5bcfcd51` — `video`
`$set` on the existing document (1 matched, 1 modified) and read back
from Atlas. No measured field was touched.

The earlier failed attempt (`_id 6a97025021119262684581ca`, `stalled`)
was left alone; it is one `--run-json ... --push` away if it is ever
worth watching.

## Tests

`python3 scripts/tests/test_stream_anchor.py` — offsets, the
uncalibrated fallback, registry precedence, and the promise that a
lookup failure is recorded rather than raised. The 2026-09-01 numbers
above are the fixture, so the published links are a regression anchor.
`python3 scripts/tests/test_powder_battery_capture.py` still passes
unchanged.
