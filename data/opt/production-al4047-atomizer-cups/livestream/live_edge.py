#!/usr/bin/env python3
"""Run on the Zero: for each video id, resolve a fresh HLS playlist with
yt-dlp and report its live edge (last segment's sequence number and the
wall time it implies) and the server's live-head headers."""
import datetime as dt, json, os, re, subprocess, sys, urllib.request
YTDLP = os.path.expanduser("~/powder-doser-venv/bin/yt-dlp")
for vid in sys.argv[1:]:
    try:
        url = subprocess.check_output([YTDLP, "-g", "-f", "229/worstvideo", "--no-warnings",
                                       "https://www.youtube.com/watch?v=" + vid],
                                      text=True, timeout=150).split()[0]
    except Exception as e:
        print(vid, "yt-dlp failed:", type(e).__name__); continue
    pl = urllib.request.urlopen(url, timeout=30).read().decode().splitlines()
    head = {l.split(":")[0]: l.split(":", 1)[1] for l in pl if l.startswith("#EXT-X-") and ":" in l}
    segs = [l for l in pl if l and not l.startswith("#")]
    n_disc = sum(1 for l in pl if l == "#EXT-X-DISCONTINUITY")
    pdts = [l.split(":", 1)[1] for l in pl if l.startswith("#EXT-X-PROGRAM-DATE-TIME")]
    t0 = dt.datetime.fromisoformat(pdts[0]) if pdts else None
    # wall time of the end of the window, assuming no gap inside the window
    dur = sum(float(l.split(":")[1].rstrip(",")) for l in pl if l.startswith("#EXTINF"))
    req = urllib.request.Request(segs[-1], headers={"Range": "bytes=0-0"})
    r = urllib.request.urlopen(req, timeout=30)
    now = dt.datetime.now(dt.timezone.utc)
    end = t0 + dt.timedelta(seconds=dur) if t0 else None
    print(json.dumps({
        "video": vid, "fetched_utc": now.isoformat(timespec="seconds"),
        "media_sequence": int(head.get("#EXT-X-MEDIA-SEQUENCE", -1)),
        "discontinuity_sequence": int(head.get("#EXT-X-DISCONTINUITY-SEQUENCE", 0)),
        "discontinuities_in_window": n_disc, "segments": len(segs),
        "window_start_utc": t0.isoformat(timespec="seconds") if t0 else None,
        "window_end_utc": end.isoformat(timespec="seconds") if end else None,
        "behind_now_s": round((now - end).total_seconds()) if end else None,
        "x_head_seqnum": r.headers.get("X-Head-Seqnum"),
        "x_head_time_sec": r.headers.get("X-Head-Time-Sec"),
        "endlist": any(l.startswith("#EXT-X-ENDLIST") for l in pl)}))
