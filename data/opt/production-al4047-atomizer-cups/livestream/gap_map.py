#!/usr/bin/env python3
"""Run on the Zero (YouTube refuses the CI runner): map the gaps in a live
broadcast's ingest.  Each DASH media segment of a YouTube live broadcast
starts with text metadata that includes Ingestion-Walltime-Us, the wall
time YouTube received it.  Segments are 2 s, so wall(sq) - 2*sq is constant
while the encoder is connected and jumps by the outage length at each
reconnect.  Samples every STEP segments, then bisects each jump.  Fetches
only the first 2 kB of the 144p segments (format 160), rate-capped.

    gap_map.py VIDEO_ID [STEP [MAX_SQ [DUMP.json]]]   -> JSON lines on stdout

DUMP.json gets every fetched segment's sequence number and wall time.
"""
import datetime as dt
import json
import os
import re
import subprocess
import sys
import time
import urllib.request

YTDLP = os.path.expanduser("~/powder-doser-venv/bin/yt-dlp")
vid = sys.argv[1]
step = int(sys.argv[2]) if len(sys.argv) > 2 else 60
max_sq = int(sys.argv[3]) if len(sys.argv) > 3 else None
dump = sys.argv[4] if len(sys.argv) > 4 else None
meta = json.loads(subprocess.check_output(
    [YTDLP, "--live-from-start", "-J", "--no-warnings", "--skip-download",
     "https://www.youtube.com/watch?v=" + vid], text=True, timeout=180))
base = [f for f in meta["formats"] if f["format_id"] == "160"][0]["url"]
cache = {}
n_fetch = 0


def head(n):
    """(Ingestion-Walltime s, raw metadata dict) of segment n, or None."""
    global n_fetch
    if n in cache:
        return cache[n]
    req = urllib.request.Request(base + "&sq=%d" % n,
                                 headers={"Range": "bytes=0-2047"})
    try:
        data = urllib.request.urlopen(req, timeout=60).read(2048)
    except Exception as e:                                   # noqa: BLE001
        cache[n] = None
        return None
    n_fetch += 1
    time.sleep(0.15)                       # stays far under 100 kB/s
    md = dict((k.decode(), v.decode()) for k, v in
              re.findall(rb"([A-Za-z\-]+): ([0-9A-Za-z_\-\.]+)", data[:2048]))
    w = md.get("Ingestion-Walltime-Us")
    cache[n] = (int(w) / 1e6, md) if w else None
    return cache[n]


def off(n):
    h = head(n)
    return None if h is None else h[0] - 2.0 * n


# live head
req = urllib.request.Request(base + "&sq=0", headers={"Range": "bytes=0-0"})
r = urllib.request.urlopen(req, timeout=60)
last = int(r.headers.get("X-Head-Seqnum"))
if max_sq is not None:
    last = min(last, max_sq)
iso = lambda t: dt.datetime.fromtimestamp(t, dt.timezone.utc).isoformat(timespec="seconds")
print(json.dumps({"video": vid, "title": meta.get("title"), "live_status": meta.get("live_status"),
                  "release_utc": iso(meta["release_timestamp"]) if meta.get("release_timestamp") else None,
                  "head_seqnum": last}), flush=True)
first = head(0)
print(json.dumps({"seg0_walltime_utc": iso(first[0]) if first else None}), flush=True)


# the head segment can still be open (no metadata yet); use the last one with a wall time
while last > 0 and head(last) is None:
    last -= 1
samples = list(range(0, last, step)) + [last]
gaps = []


def split(a, b):
    """Record every 1-segment step inside (a, b] whose offset changes by
    >= 1 s.  A real outage shows up as one step of + its length."""
    oa, ob = off(a), off(b)
    if oa is None or ob is None or abs(ob - oa) < 1.0:
        return
    if b - a == 1:
        wa, wb = head(a)[0], head(b)[0]
        gaps.append({"after_sq": a, "resume_sq": b,
                     "last_before_utc": iso(wa + 2.0), "resume_utc": iso(wb),
                     "gap_s": round(wb - wa - 2.0, 1)})
        print(json.dumps(gaps[-1]), flush=True)
        return
    mid = (a + b) // 2
    split(a, mid)
    split(mid, b)


for a, b in zip(samples, samples[1:]):
    split(a, b)
print(json.dumps({"last_seg_with_walltime": last, "last_seg_end_utc": iso(head(last)[0] + 2.0)}), flush=True)
print(json.dumps({"n_gaps": len(gaps), "total_gap_s": round(sum(g["gap_s"] for g in gaps), 1),
                  "segments_fetched": n_fetch}), flush=True)
if dump:
    with open(dump, "w") as f:
        json.dump({"video": vid, "title": meta.get("title"),
                   "segments": {str(k): v[0] for k, v in sorted(cache.items()) if v}},
                  f, indent=0)
