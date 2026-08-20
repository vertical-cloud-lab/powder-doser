#!/usr/bin/env python3
"""Grab a still frame of the bench rig from the picam live stream.

Why this exists
---------------

A powder battery that reads a flat 0.0000 g is ambiguous: a genuinely
cohesive powder, a capped or taped outlet, an auger that is not seated in
the drive coupler, and a collection dish that is not under the outlet all
produce byte-identical data.  Issue #116 has now lost three runs to that
ambiguity.

The bench camera resolves it in about a minute, because the rig is
streamed continuously.  On 2026-08-05 the carboxymethyl cellulose
pre-flight read exactly 0.0000 g through 25 auger revolutions and 60
taps; one frame showed red tape still folded over the delivery end, and
a second frame from the calcium lactate run 66 minutes earlier showed the
same geometry with a bare outlet.  That is a two-image diagnosis instead
of a 50-minute battery producing unusable numbers.

Two-stage fetch
---------------

YouTube bot-blocks the CI runner's datacenter IP, so the media has to be
fetched over the Pi's residential connection -- but the Pi has no ffmpeg
and is on constrained residential Wi-Fi.  So:

1. on the **Pi**: resolve the HLS manifest with ``yt-dlp -g``, then pull a
   single ~2 s transport-stream segment with rate-limited ``curl``
   (~150 kB at 720p -- no ffmpeg needed, and nothing is installed
   permanently);
2. on the **runner**: decode one frame out of that segment with ffmpeg.

Each frame carries a burned-in overlay clock in the **lab's local time**
(MDT), which is the capture clock and the one that matches balance
readings -- prefer it over the YouTube watch-page timestamp, which is off
by several seconds (see ``docs/battery-runs/stream-timestamps.md``).

Usage
-----

Latest frame from the live powder-doser broadcast::

    python scripts/bench_frame.py --out /tmp/now.png

A frame from N seconds ago (the DVR window is ~2 h)::

    python scripts/bench_frame.py --seconds-ago 4000 --out /tmp/earlier.png

Requires ``ffmpeg`` on the local machine (``pip install imageio-ffmpeg``
provides one; pass ``--ffmpeg`` to point at it) and SSH access to the Pi
per ``CLAUDE.md``.  ``yt-dlp`` is installed to ``/tmp`` on the Pi on
first use and is not persisted anywhere else.
"""

from __future__ import annotations

import argparse
import json
import os
import shlex
import subprocess
import sys
import tempfile

CHANNEL = "https://www.youtube.com/@byu-vcl-hardware-streams/streams"
DEFAULT_STREAM_MATCH = "powder doser"
SEGMENT_SECONDS = 2.0
YTDLP_URL = ("https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp")
YTDLP_PI_PATH = "/tmp/yt-dlp"
RATE_LIMIT = "1500K"          # keep off the Pi's residential uplink


class BenchFrameError(RuntimeError):
    pass


def _pi_target() -> str:
    user = os.environ.get("RPI_POWDER_DOSER_USERNAME")
    host = os.environ.get("RPI_POWDER_DOSER_HOSTNAME")
    if not user or not host:
        raise BenchFrameError(
            "set RPI_POWDER_DOSER_USERNAME and RPI_POWDER_DOSER_HOSTNAME "
            "(injected by the workflow; never print their values)")
    return "{}@{}".format(user, host)


def pi_run(command: str, timeout: int = 300) -> str:
    """Run a shell command on the Pi over Tailscale SSH, return stdout."""
    proc = subprocess.run(
        ["ssh", "-o", "StrictHostKeyChecking=no", "-o", "ConnectTimeout=20",
         _pi_target(), command],
        capture_output=True, text=True, timeout=timeout)
    if proc.returncode != 0:
        raise BenchFrameError(
            "remote command failed ({}): {}".format(
                proc.returncode, proc.stderr.strip()[:400]))
    return proc.stdout


def ensure_ytdlp() -> None:
    pi_run(
        "test -x {p} || (curl -sSL --limit-rate {r} -o {p} {u} && chmod +x {p})"
        .format(p=YTDLP_PI_PATH, r=RATE_LIMIT, u=YTDLP_URL),
        timeout=600)


def find_live_video(match: str = DEFAULT_STREAM_MATCH) -> dict:
    """Return the live broadcast whose title contains ``match``."""
    out = pi_run(
        "timeout 120 python3 {p} --no-warnings --flat-playlist -J {c} "
        "2>/dev/null".format(p=YTDLP_PI_PATH, c=shlex.quote(CHANNEL)),
        timeout=600)
    try:
        entries = json.loads(out).get("entries", [])
    except json.JSONDecodeError as exc:
        raise BenchFrameError("could not parse channel listing: {}".format(exc))

    needle = match.lower()
    for entry in entries:
        title = (entry.get("title") or "").lower()
        if needle in title and entry.get("live_status") == "is_live":
            return {"id": entry["id"], "title": entry.get("title")}
    raise BenchFrameError(
        "no live broadcast matching {!r}; titles seen: {}".format(
            match, [e.get("title") for e in entries[:6]]))


# Which itags a live broadcast advertises depends on the client yt-dlp
# managed to use, and that has changed under us more than once: the Pi's
# yt-dlp has no JS runtime, so it falls back to the android-vr player API
# and sees the classic 91-95 ladder, while other extraction paths return
# the 229-232/269 set.  Ask for all of them, best resolution first, rather
# than pinning one and failing with "no manifest".
DEFAULT_ITAGS = ("95", "232", "94", "231", "93", "230", "229", "269")


def fetch_segment(video_id: str, itag: str, seconds_ago: float,
                  remote_path: str = "/tmp/bench_frame.ts") -> int:
    """Pull one HLS segment on the Pi. Returns its size in bytes.

    ``seconds_ago`` counts back from the live edge; the DVR playlist holds
    roughly two hours, so anything older raises.
    """
    back = max(1, int(round(seconds_ago / SEGMENT_SECONDS)) + 1)
    script = "\n".join([
        "set -e",
        'URL=$(timeout 120 python3 {p} -f {i} -g '
        '"https://www.youtube.com/watch?v={v}" 2>/dev/null | head -1)'.format(
            p=YTDLP_PI_PATH, i=shlex.quote(itag), v=video_id),
        '[ -n "$URL" ] || {{ echo "no manifest for itag {}" >&2; exit 3; }}'
        .format(itag),
        'curl -sSL --limit-rate {r} "$URL" -o /tmp/bench_frame.m3u8'.format(
            r=RATE_LIMIT),
        'N=$(grep -c "^https" /tmp/bench_frame.m3u8 || true)',
        '[ "$N" -ge {b} ] || {{ echo "requested segment is older than the '
        'DVR window (playlist holds $N segments)" >&2; exit 4; }}'.format(
            b=back),
        'SEG=$(grep "^https" /tmp/bench_frame.m3u8 | tail -{b} | head -1)'
        .format(b=back),
        'curl -sSL --limit-rate {r} "$SEG" -o {o}'.format(
            r=RATE_LIMIT, o=remote_path),
        'stat -c %s {o}'.format(o=remote_path),
    ])
    out = pi_run("bash -s <<'BENCHEOF'\n{}\nBENCHEOF".format(script),
                 timeout=900)
    size = int(out.strip().splitlines()[-1])
    if size <= 0:
        raise BenchFrameError(
            "empty segment for itag {} -- try a lower --itag".format(itag))
    return size


def fetch_segment_any(video_id: str, itags, seconds_ago: float,
                      remote_path: str = "/tmp/bench_frame.ts") -> int:
    """``fetch_segment`` over a list of itags, first one that works wins.

    A single hard-coded itag is fragile: YouTube has renumbered its live
    formats at least once, and a broadcast that does not carry the one we
    ask for returns "no manifest" rather than a smaller rendition.
    """
    errors = []
    for itag in itags:
        try:
            size = fetch_segment(video_id, itag, seconds_ago, remote_path)
        except BenchFrameError as exc:
            # An older-than-DVR request fails identically on every itag, so
            # do not burn four more round trips on it.
            if "DVR window" in str(exc):
                raise
            errors.append("itag {}: {}".format(itag, exc))
            continue
        print("[bench-frame] itag {}".format(itag))
        return size
    raise BenchFrameError(
        "no itag produced a segment. Tried:\n  " + "\n  ".join(errors))


def copy_from_pi(remote_path: str, local_path: str) -> None:
    proc = subprocess.run(
        ["scp", "-q", "-o", "StrictHostKeyChecking=no",
         "{}:{}".format(_pi_target(), remote_path), local_path],
        capture_output=True, text=True, timeout=600)
    if proc.returncode != 0:
        raise BenchFrameError("scp failed: {}".format(proc.stderr.strip()[:400]))


def decode_frame(ts_path: str, out_path: str, ffmpeg: str,
                 crop: str | None = None) -> None:
    cmd = [ffmpeg, "-y", "-loglevel", "error", "-i", ts_path, "-frames:v", "1"]
    if crop:
        cmd += ["-vf", crop]
    cmd.append(out_path)
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    if proc.returncode != 0 or not os.path.exists(out_path):
        raise BenchFrameError(
            "ffmpeg failed: {}".format(proc.stderr.strip()[:400]))


def resolve_ffmpeg(explicit: str | None) -> str:
    if explicit:
        return explicit
    for candidate in ("ffmpeg",):
        try:
            subprocess.run([candidate, "-version"], capture_output=True,
                           timeout=30, check=True)
            return candidate
        except (OSError, subprocess.SubprocessError):
            pass
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except ImportError:
        raise BenchFrameError(
            "no ffmpeg found -- `pip install imageio-ffmpeg` or pass --ffmpeg")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--out", default="bench_frame.png",
                        help="local PNG to write")
    parser.add_argument("--seconds-ago", type=float, default=0.0,
                        help="how far back from the live edge (DVR ~2 h)")
    parser.add_argument("--video-id",
                        help="broadcast id; default is the live powder-doser one")
    parser.add_argument("--match", default=DEFAULT_STREAM_MATCH,
                        help="substring identifying the stream to use")
    parser.add_argument("--itag", default=",".join(DEFAULT_ITAGS),
                        help="comma-separated itags, tried in order. YouTube "
                             "renumbered its live formats in 2026: the current "
                             "set is 232=720x1280, 231/230/229 smaller, 269 "
                             "lowest. The old 91-96 no longer exist.")
    parser.add_argument("--crop",
                        help="optional ffmpeg -vf filter, e.g. "
                             "'crop=260:260:340:540,scale=1040:1040'")
    parser.add_argument("--ffmpeg", help="path to an ffmpeg binary")
    args = parser.parse_args(argv)

    try:
        ffmpeg = resolve_ffmpeg(args.ffmpeg)
        ensure_ytdlp()
        if args.video_id:
            video = {"id": args.video_id, "title": "(explicit)"}
        else:
            video = find_live_video(args.match)
        print("[bench-frame] broadcast {} ({})".format(
            video["id"], video["title"]))

        size = fetch_segment_any(
            video["id"], [t.strip() for t in args.itag.split(",") if t.strip()],
            args.seconds_ago)
        print("[bench-frame] segment {} bytes, {:.0f} s behind live".format(
            size, args.seconds_ago))

        with tempfile.TemporaryDirectory() as tmp:
            local_ts = os.path.join(tmp, "bench_frame.ts")
            copy_from_pi("/tmp/bench_frame.ts", local_ts)
            decode_frame(local_ts, args.out, ffmpeg, args.crop)
    except BenchFrameError as exc:
        print("[bench-frame] {}".format(exc), file=sys.stderr)
        return 1

    print("[bench-frame] wrote {}".format(args.out))
    print("[bench-frame] the burned-in overlay clock is lab-local (MDT); "
          "trust it over the watch-page timestamp")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
