# Stream timestamps for the uniform powder-battery runs

Every battery run happens in front of the `picam-d1pr` bench camera, which
streams continuously to
[@byu-vcl-hardware-streams](https://youtube.com/@byu-vcl-hardware-streams) in
rolling 8 h broadcasts (03:00 / 11:00 / 19:00 UTC). That makes the video a
free, complete record of each run -- the only work is mapping a run's UTC
timestamps onto an offset into the right broadcast.

All three 2026-08-04 runs (issue #116) fall inside one broadcast:
**[powder doser stream picam-d1pr, 2026-08-04 UTC 19:00](https://youtu.be/w1D5DRiHFWM)**.

Regenerate this table after any new run:

```bash
python scripts/battery_stream_links.py data/battery/*/run_*.json
```

Links are offset 5 s early so the action starts just after the seek. Times
come from `started_utc` plus the per-trial device `t_ms` in each run
document, so they are good to a couple of seconds.

## Anchoring: do not trust the watch page's start timestamp

The `?t=` parameter is an offset into the video timeline, and for a live
broadcast that timeline does **not** start at the time YouTube reports on the
watch page:

| clock | 2026-08-04 19:00 broadcast |
|---|---|
| watch page `startTimestamp` | 19:01:12 UTC |
| fragment publish clock (`X-Head-Time` vs wall clock) | 19:01:10 UTC |
| **actual content t=0** (burned-in overlay) | **19:01:06 UTC** |

The 6 s gap is YouTube live ingest latency (~25 s here) partly cancelling the
publish-time offset. Six seconds is enough to land a link in the wrong trial
in block C, where each revolution is ~5 s, so the anchor is calibrated
against the timestamp overlay burned into the top-left of every frame -- that
is the capture clock and the only one that matches the balance readings.
Anchors are stored in [`stream-registry.json`](stream-registry.json);
`python scripts/battery_stream_links.py --calibrate` prints the procedure.

Note also that YouTube bot-blocks datacenter IP ranges: the channel listing
works from CI, but anything that touches the player (formats, fragments)
has to run from the Pi's residential connection.

## Clips

Sped-up excerpts pulled from the broadcast, in
[`clips/`](clips/) (`.gif` for inline viewing, `.mp4` for anything else):

| clip | source | speed |
|---|---|---|
| `wrf_preflight` | white rice flour pre-flight feed check, tilt 90 deg | 8x |
| `wrf_C90` | white rice flour block C, tilt 90 deg | 4x |
| `wrf_D_speed` | white rice flour block D, 15 / 45 / 90 RPM at tilt 45 deg | 4x |
| `brf2_C90` | brown rice flour re-run block C, tilt 90 deg | 4x |

`wrf_C90` and `brf2_C90` are the same block at the same tilt on the same rig
95 minutes apart: the balance climbs past 0.18 g in one and never leaves
0.0000 g in the other.

## Links

### brown-rice-flour -- 2026-08-04 20:43:16 UTC

Stream: [powder doser stream picam-d1pr, 2026-08-04 UTC 19:00](https://youtu.be/w1D5DRiHFWM) (content t=0 at 2026-08-04T19:01:06+00:00)

| segment | starts (UTC) | duration | link | |
|---|---|---|---|---|
| **whole run** | 20:43:16 | 7m05s | [watch](https://youtu.be/w1D5DRiHFWM?t=6125) | ok |
| A -- baseline (no actuation) | 20:43:23 | 0m15s | [watch](https://youtu.be/w1D5DRiHFWM?t=6133) |  |
| B -- static hold | 20:43:58 | 0m41s | [watch](https://youtu.be/w1D5DRiHFWM?t=6168) |  |
| C -- rotation vs tilt | 20:44:52 | 2m04s | [watch](https://youtu.be/w1D5DRiHFWM?t=6221) |  |
| &nbsp;&nbsp;tilt 0 deg | 20:44:52 | 0m36s | [watch](https://youtu.be/w1D5DRiHFWM?t=6221) |  |
| &nbsp;&nbsp;tilt 45 deg | 20:45:40 | 0m32s | [watch](https://youtu.be/w1D5DRiHFWM?t=6269) |  |
| &nbsp;&nbsp;tilt 90 deg | 20:46:24 | 0m32s | [watch](https://youtu.be/w1D5DRiHFWM?t=6313) |  |
| D -- rotation speed sweep | 20:47:01 | 0m28s | [watch](https://youtu.be/w1D5DRiHFWM?t=6351) |  |
| E -- solenoid tapping | 20:47:41 | 2m21s | [watch](https://youtu.be/w1D5DRiHFWM?t=6390) |  |
| G -- closed-loop 1 g doses | 20:50:01 | 0m16s | [watch](https://youtu.be/w1D5DRiHFWM?t=6531) |  |
| &nbsp;&nbsp;dose 1 | 20:50:01 | 0m06s | [watch](https://youtu.be/w1D5DRiHFWM?t=6531) | 0.0008 g, stalled |
| &nbsp;&nbsp;dose 2 | 20:50:08 | 0m05s | [watch](https://youtu.be/w1D5DRiHFWM?t=6537) | 0.0000 g, stalled |
| &nbsp;&nbsp;dose 3 | 20:50:12 | 0m05s | [watch](https://youtu.be/w1D5DRiHFWM?t=6542) | 0.0011 g, stalled |

### white-rice-flour -- 2026-08-04 21:14:22 UTC

Stream: [powder doser stream picam-d1pr, 2026-08-04 UTC 19:00](https://youtu.be/w1D5DRiHFWM) (content t=0 at 2026-08-04T19:01:06+00:00)

| segment | starts (UTC) | duration | link | |
|---|---|---|---|---|
| pre-flight feed check | 21:13:00 | 1m22s | [watch](https://youtu.be/w1D5DRiHFWM?t=7909) | feed confirmed |
| **whole run** | 21:14:22 | 47m49s | [watch](https://youtu.be/w1D5DRiHFWM?t=7991) | ok |
| A -- baseline (no actuation) | 21:14:29 | 0m15s | [watch](https://youtu.be/w1D5DRiHFWM?t=7999) |  |
| B -- static hold | 21:15:05 | 0m41s | [watch](https://youtu.be/w1D5DRiHFWM?t=8034) |  |
| C -- rotation vs tilt | 21:15:58 | 2m00s | [watch](https://youtu.be/w1D5DRiHFWM?t=8087) |  |
| &nbsp;&nbsp;tilt 0 deg | 21:15:58 | 0m32s | [watch](https://youtu.be/w1D5DRiHFWM?t=8087) |  |
| &nbsp;&nbsp;tilt 45 deg | 21:16:42 | 0m32s | [watch](https://youtu.be/w1D5DRiHFWM?t=8131) |  |
| &nbsp;&nbsp;tilt 90 deg | 21:17:26 | 0m32s | [watch](https://youtu.be/w1D5DRiHFWM?t=8176) |  |
| D -- rotation speed sweep | 21:18:04 | 0m28s | [watch](https://youtu.be/w1D5DRiHFWM?t=8213) |  |
| E -- solenoid tapping | 21:18:44 | 2m20s | [watch](https://youtu.be/w1D5DRiHFWM?t=8253) |  |
| G -- closed-loop 1 g doses | 21:21:04 | 41m05s | [watch](https://youtu.be/w1D5DRiHFWM?t=8393) |  |
| &nbsp;&nbsp;dose 1 | 21:21:04 | 13m42s | [watch](https://youtu.be/w1D5DRiHFWM?t=8393) | 0.8597 g, cycle-budget |
| &nbsp;&nbsp;dose 2 | 21:34:45 | 13m45s | [watch](https://youtu.be/w1D5DRiHFWM?t=9215) | 0.8399 g, cycle-budget |
| &nbsp;&nbsp;dose 3 | 21:48:31 | 13m38s | [watch](https://youtu.be/w1D5DRiHFWM?t=10040) | 0.8868 g, cycle-budget |

### brown-rice-flour -- 2026-08-04 22:49:37 UTC

Stream: [powder doser stream picam-d1pr, 2026-08-04 UTC 19:00](https://youtu.be/w1D5DRiHFWM) (content t=0 at 2026-08-04T19:01:06+00:00)

| segment | starts (UTC) | duration | link | |
|---|---|---|---|---|
| **whole run** | 22:49:37 | 6m58s | [watch](https://youtu.be/w1D5DRiHFWM?t=13707) | ok |
| A -- baseline (no actuation) | 22:49:45 | 0m15s | [watch](https://youtu.be/w1D5DRiHFWM?t=13714) |  |
| B -- static hold | 22:50:20 | 0m41s | [watch](https://youtu.be/w1D5DRiHFWM?t=13750) |  |
| C -- rotation vs tilt | 22:51:14 | 1m59s | [watch](https://youtu.be/w1D5DRiHFWM?t=13803) |  |
| &nbsp;&nbsp;tilt 0 deg | 22:51:14 | 0m32s | [watch](https://youtu.be/w1D5DRiHFWM?t=13803) |  |
| &nbsp;&nbsp;tilt 45 deg | 22:51:57 | 0m32s | [watch](https://youtu.be/w1D5DRiHFWM?t=13847) |  |
| &nbsp;&nbsp;tilt 90 deg | 22:52:41 | 0m32s | [watch](https://youtu.be/w1D5DRiHFWM?t=13890) |  |
| D -- rotation speed sweep | 22:53:19 | 0m27s | [watch](https://youtu.be/w1D5DRiHFWM?t=13928) |  |
| E -- solenoid tapping | 22:53:58 | 2m20s | [watch](https://youtu.be/w1D5DRiHFWM?t=13967) |  |
| G -- closed-loop 1 g doses | 22:56:17 | 0m16s | [watch](https://youtu.be/w1D5DRiHFWM?t=14107) |  |
| &nbsp;&nbsp;dose 1 | 22:56:17 | 0m06s | [watch](https://youtu.be/w1D5DRiHFWM?t=14107) | 0.0000 g, stalled |
| &nbsp;&nbsp;dose 2 | 22:56:23 | 0m05s | [watch](https://youtu.be/w1D5DRiHFWM?t=14113) | 0.0000 g, stalled |
| &nbsp;&nbsp;dose 3 | 22:56:28 | 0m05s | [watch](https://youtu.be/w1D5DRiHFWM?t=14118) | 0.0000 g, stalled |
