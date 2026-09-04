# 2026-09-04 — issue #148: 1 g salt three-phase demo dose

Live-demo run requested in issue #148 ("1 g of salt with the three-phase method,
skip checks, straight to dispensing"). One closed-loop block G dose, first
attempt, no retries.

## Result

| | |
|---|---|
| target / delivered | 1.0000 g / **1.0040 g** (+3.9 mg, +0.39 %) |
| status | `ok`, 90.0 s, 3.08 auger rev, 16 taps |
| phases | bulk 5 cycles → 0.5953 g · fine 10 → 0.9948 g · tap 8 → 1.0040 g |
| capture window (UTC) | 2026-09-04T00:18:21.6 → 00:19:56.8 |
| run dir (Pi) | `~/powder-doser/data/battery/20260904T001821Z_salt/` |
| MongoDB | `powder_doser.battery_runs` `_id 6a9a0fb9edb3a09ea05b95b6` (doc 26; readback verified) |
| stream link | <https://youtu.be/xjtJNMo8DKw?t=15155> (±3 s anchor, 15 s lead-in) |

Invocation (from `~/powder-doser` on the Pi):

```bash
python3 scripts/powder_battery_capture.py --powder-id salt --operator claude \
  --batch food-safe-2026-08 --unattended \
  --run-args 'blocks="G",dose_repeats=1,dose_target_g=1.0'
```

Environment counters all zero (retries, shock events, drift corrections,
unsettled brackets). Tare baseline +0.0 mg, drift +12.4 mg/min, read noise
0.08 mg. `--unattended` auto-continued the "EMPTY the collection cup" prompt;
the tare absorbed whatever was on the pan, which now additionally holds this
run's ~1.0 g of salt.

## Stream anchor

The covering broadcast is `xjtJNMo8DKw` — *powder doser stream picam-d1pr,
2026-09-03 UTC 20:05*, still live when resolved. Yesterday's 19:00 roll-over
bounced (short `was_live` broadcasts at 19:37 and 19:38 before the 20:05
restart), so the title-matching in `scripts/stream_anchor.py` mattered:
`content_t0` = `2026-09-03T20:05:31Z` (`release_timestamp − 6 s`, the
calibration from the 2026-09-01 note), run offsets `t = 15170.6 → 15265.8 s`.
Not frame-verified (no ffmpeg on the Pi); same ±3 s basis as before.

## Pi-side changes (per CLAUDE.md, the Pi is not a checkout)

1. **`yt-dlp` reinstalled for the `vcl` user** —
   `python3 -m pip install --user --break-system-packages yt-dlp`
   (→ 2026.08.19, script at `~/.local/bin/yt-dlp`). The module present on
   2026-09-01 was gone (both the module and any standalone binary), so
   `stream_anchor.py` failed with `yt-dlp exited 1`. It must run on the Pi:
   the watch-page metadata half of yt-dlp is bot-blocked from datacenter IPs
   (confirmed from the Actions runner), while the flat channel listing works
   anywhere.
2. **`data/battery/20260904T001821Z_salt/run_salt.json` annotated in place**
   with the `video` block via `stream_anchor.py --run-json`.

## Observed, not changed

- `scripts/powder_battery_capture.py` on the Pi is a **newer version than the
  2026-09-01 stream-link-integrated one** (new `dose_read_path=bracket`
  bracketed-read/baseline-subtract features; operator `swcharles` ran block H
  "in the new fume hood" with it on 2026-09-03). It no longer calls
  `stream_anchor` — no `--no-stream-link`/`--run-json`/`--push` flags — so
  fresh runs get **no `video` block** (2026-09-03 runs have none) until the
  integration is re-applied. Post-run backfill works:
  `python3 scripts/stream_anchor.py --run-json <run.json> [--push]`.
- `pymongo` is not installed on the Pi (`--upload` skips with a warning).
  This run was uploaded from the Actions runner via `--upload-file`, which is
  also where CLAUDE.md wants cloud credentials used.
- Non-login SSH shells don't get `~/.local/bin` on `PATH`; `stream_anchor.py`
  falls back to `python3 -m yt_dlp`, which works regardless.
