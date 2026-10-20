#!/usr/bin/env python3
"""Issue #186 helper (runs on the Zero): save the newest N segments of
the powder-doser livestream's HLS playlist.  YouTube blocks the Actions
runner's IP, so this fetches from the Zero.

    grab_live.py VIDEO_ID OUTDIR N [FORMAT]
"""
import os
import subprocess
import sys
import urllib.request

vid, outdir, n = sys.argv[1], sys.argv[2], int(sys.argv[3])
fmt = sys.argv[4] if len(sys.argv) > 4 else "best[height<=720]"
cache = os.path.join(outdir, ".m3u8_url")
os.makedirs(outdir, exist_ok=True)
url = None
if os.path.exists(cache):
    url = open(cache).read().strip()
for attempt in range(2):
    if not url:
        url = subprocess.check_output(
            [os.path.expanduser("~/powder-doser-venv/bin/yt-dlp"), "-g",
             "-f", fmt, "https://www.youtube.com/watch?v=" + vid],
            text=True).strip().splitlines()[0]
        open(cache, "w").write(url)
    try:
        playlist = urllib.request.urlopen(url, timeout=30).read().decode()
        break
    except Exception:
        url = None
segs = [l for l in playlist.splitlines() if l and not l.startswith("#")]
for i, seg in enumerate(segs[-n:]):
    data = urllib.request.urlopen(seg, timeout=60).read()
    path = os.path.join(outdir, "seg{:02d}.ts".format(i))
    with open(path, "wb") as f:
        f.write(data)
    print(path, len(data), flush=True)
