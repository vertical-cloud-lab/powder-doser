#!/usr/bin/env python3
"""Timestamped YouTube share links for uniform powder-battery runs (issue #116).

The bench cameras stream continuously to
https://youtube.com/@byu-vcl-hardware-streams in rolling 8 h broadcasts, so
every battery run is already on video -- it just has to be found. Each run
document carries ``started_utc`` and per-trial ``t_ms``, which is enough to
turn any block, dose or trial into ``https://youtu.be/<id>?t=<seconds>``
once the stream's ``content_t0`` (wall-clock UTC of video offset zero) is
known. Anchors live in ``docs/battery-runs/stream-registry.json``.

Usage::

    # markdown link table for every committed run
    python scripts/battery_stream_links.py data/battery/*/run_*.json

    # how to anchor a stream that is not in the registry yet
    python scripts/battery_stream_links.py --calibrate

``content_t0`` cannot be taken from the watch page's ``startTimestamp``: that
is the broadcast-accepted time, and YouTube's live ingest latency shifts the
fragment clock away from the capture clock (25 s on 2026-08-04, which is
enough to land a link in the wrong trial). The reliable anchor is the
burned-in timestamp overlay in the top-left of the frame -- see --calibrate.
"""

import argparse
import datetime
import glob
import json
import os
import sys

REGISTRY = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "docs", "battery-runs", "stream-registry.json",
)

# Seconds of run-up before the event, so a link lands just before the thing
# it points at rather than a frame into it.
LEAD_IN_S = 5

BLOCK_LABELS = {
    "A": "baseline (no actuation)",
    "B": "static hold",
    "C": "rotation vs tilt",
    "D": "rotation speed sweep",
    "E": "solenoid tapping",
    "F": "vibration",
    "G": "closed-loop 1 g doses",
}

CALIBRATE_HELP = """\
Anchoring a stream (deriving content_t0)
----------------------------------------

1. Find the broadcast covering the run. Channel listing works from any IP:

       yt-dlp --flat-playlist --dump-json \\
           https://www.youtube.com/@byu-vcl-hardware-streams/streams

   Titles carry the nominal UTC start; the powder doser camera is picam-d1pr.

2. Pull a short window of video. Anything past the channel listing needs a
   residential IP -- YouTube bot-blocks datacenter ranges, so run this on the
   Pi rather than on a CI runner. Fetch the DASH fragments directly (2 s
   each, so fragment N covers video offset 2N):

       yt-dlp -f 243 --live-from-start -j <url>     # take .url, .target_duration
       curl "<url>&sq=0"    > clip.webm             # init segment
       curl "<url>&sq=4085" >> clip.webm            # ... and the window wanted

   Fragment PTS are absolute in the video timeline, so the concatenated file
   can be seeked with the same offsets a ?t= link uses.

3. Read the burned-in overlay clock (top-left, camera local time) from a
   frame at a known offset:

       ffmpeg -i clip.webm -vf "select='gte(t,8200)',crop=360:40:0:0" \\
           -vframes 1 overlay.png

       content_t0 = overlay_utc - pts_s

   Two samples a few thousand seconds apart confirm there is no drift.
"""


def load_registry(path=REGISTRY):
    with open(path) as fh:
        return json.load(fh)["streams"]


def parse_utc(text):
    return datetime.datetime.fromisoformat(text)


def hms(seconds):
    seconds = int(round(seconds))
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    return "%dh%02dm%02ds" % (h, m, s) if h else "%dm%02ds" % (m, s)


def pick_stream(streams, started, ended, camera="picam-d1pr"):
    """The stream whose coverage contains the whole run, if any."""
    for s in streams:
        if s.get("camera") != camera:
            continue
        t0 = parse_utc(s["content_t0_utc"])
        # Broadcasts roll every 8 h; treat that as the coverage window.
        if t0 <= started and ended <= t0 + datetime.timedelta(hours=8):
            return s
    return None


def link(video_id, offset_s, lead_in=LEAD_IN_S):
    return "https://youtu.be/%s?t=%d" % (video_id, max(0, int(round(offset_s)) - lead_in))


def block_spans(doc):
    """(block, first_t_ms, last_t_ms) in run order, doses expanded per dose."""
    spans = {}
    for row in doc.get("trials", []) + doc.get("polls", []):
        span = spans.setdefault(row["block"], [row["t_ms"], row["t_ms"]])
        span[0] = min(span[0], row["t_ms"])
        span[1] = max(span[1], row["t_ms"])
    for dose in doc.get("doses", []):
        start = dose["t_ms"] - dose["elapsed_s"] * 1000
        span = spans.setdefault("G", [start, dose["t_ms"]])
        span[0] = min(span[0], start)
        span[1] = max(span[1], dose["t_ms"])
    return sorted(((b, a, z) for b, (a, z) in spans.items()), key=lambda r: r[1])


def tilt_spans(doc, block):
    """(tilt, first_t_ms, last_t_ms) within one block, in run order."""
    spans = {}
    for row in doc.get("trials", []):
        if row["block"] != block:
            continue
        span = spans.setdefault(row["tilt_deg"], [row["t_ms"], row["t_ms"]])
        span[0] = min(span[0], row["t_ms"])
        span[1] = max(span[1], row["t_ms"])
    return sorted(((t, a, z) for t, (a, z) in spans.items()), key=lambda r: r[1])


def run_rows(doc, stream):
    """Markdown rows for one run: the run, each block, and the detail worth
    linking on its own (block C per tilt, block G per dose, pre-flight)."""
    t0 = parse_utc(stream["content_t0_utc"])
    started = parse_utc(doc["started_utc"])
    ended = parse_utc(doc["ended_utc"])
    base = (started - t0).total_seconds()
    vid = stream["video_id"]

    def row(label, offset, duration_s, note=""):
        wall = t0 + datetime.timedelta(seconds=offset)
        return (label, wall.strftime("%H:%M:%S"), hms(duration_s),
                link(vid, offset), note)

    rows = []
    preflight = doc.get("preflight") or {}
    if preflight.get("run_utc"):
        offset = (parse_utc(preflight["run_utc"]) - t0).total_seconds()
        rows.append(row("pre-flight feed check", offset,
                        base - offset, preflight.get("verdict", "")))
    rows.append(row("**whole run**", base, (ended - started).total_seconds(),
                    doc.get("status", "")))

    for block, first, last in block_spans(doc):
        label = "%s -- %s" % (block, BLOCK_LABELS.get(block, ""))
        rows.append(row(label, base + first / 1000.0, (last - first) / 1000.0))
        if block == "C":
            for tilt, a, z in tilt_spans(doc, block):
                rows.append(row("&nbsp;&nbsp;tilt %g deg" % tilt,
                                base + a / 1000.0, (z - a) / 1000.0))
        elif block == "G":
            for dose in doc.get("doses", []):
                start = dose["t_ms"] / 1000.0 - dose["elapsed_s"]
                rows.append(row("&nbsp;&nbsp;dose %d" % (dose["n"] + 1),
                                base + start, dose["elapsed_s"],
                                "%.4f g, %s" % (dose["dispensed_g"], dose["status"])))
    return rows


def emit_markdown(paths, streams, out=sys.stdout):
    for path in paths:
        with open(path) as fh:
            doc = json.load(fh)
        started = parse_utc(doc["started_utc"])
        ended = parse_utc(doc["ended_utc"])
        stream = pick_stream(streams, started, ended)
        heading = "%s -- %s UTC" % (doc["powder_id"], started.strftime("%Y-%m-%d %H:%M:%S"))
        print("\n### %s\n" % heading, file=out)
        if stream is None:
            print("_No registered stream covers this run; add one with "
                  "`--calibrate`._", file=out)
            continue
        print("Stream: [%s](https://youtu.be/%s) (content t=0 at %s)\n"
              % (stream["title"], stream["video_id"], stream["content_t0_utc"]), file=out)
        print("| segment | starts (UTC) | duration | link | |", file=out)
        print("|---|---|---|---|---|", file=out)
        for label, wall, dur, url, note in run_rows(doc, stream):
            print("| %s | %s | %s | [watch](%s) | %s |"
                  % (label, wall, dur, url, note), file=out)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("runs", nargs="*", help="run_<powder-id>.json files")
    ap.add_argument("--registry", default=REGISTRY)
    ap.add_argument("--calibrate", action="store_true",
                    help="print how to derive content_t0 for a new stream")
    args = ap.parse_args(argv)

    if args.calibrate:
        print(CALIBRATE_HELP)
        return 0
    paths = args.runs or sorted(glob.glob("data/battery/*/run_*.json"))
    if not paths:
        ap.error("no run documents found")
    emit_markdown(paths, load_registry(args.registry))
    return 0


if __name__ == "__main__":
    sys.exit(main())
