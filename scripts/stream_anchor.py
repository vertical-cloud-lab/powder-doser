#!/usr/bin/env python3
"""Resolve the bench livestream link that covers a battery run (issue #148).

The bench camera streams continuously to
https://youtube.com/@byu-vcl-hardware-streams in rolling 8 h broadcasts, so
every run is already on video.  Until now the mapping from a run to its
video was reconstructed after the fact, by hand, from the run's UTC stamps
-- which works, but only for as long as someone remembers how, and only
while the broadcast is still listed.  This module does that resolution at
capture time and writes the answer into the run document itself, next to
the numbers it explains::

    "video": {
      "video_id": "BH0wATmJbMs",
      "url": "https://youtu.be/BH0wATmJbMs?t=20948",
      "content_t0_utc": "2026-09-01T11:01:04+00:00",
      "started_t_s": 20963, "ended_t_s": 21135,
      "blocks": [{"block": "G", "t_s": 20966, "url": "..."}],
      "doses": [{"n": 0, "t_s": 20968, "url": "..."}]
    }

Anchoring, i.e. what wall-clock instant is video offset ``t=0``:

* A broadcast's *title* announces its nominal window ("... 2026-09-01 UTC
  11:00").  That is when the roll-over fired, not when the video starts --
  the encoder needs about a minute to come up, so a ``?t=`` computed from
  it lands ~60 s early.  Good enough to find a run, not good enough to
  land on an auger revolution.
* YouTube's ``release_timestamp`` is when the broadcast was accepted.  On
  the one broadcast calibrated frame-by-frame against the camera's
  burned-in overlay clock (``w1D5DRiHFWM``, 2026-08-04 19:00 UTC), content
  ``t=0`` was 6 s *before* that -- live ingest latency partly cancelling
  the publish-time offset.  So ``release_timestamp - 6 s`` is the anchor
  used here, and it is good to about ±3 s.
* Independent check on the same quantity: these broadcasts are cut by the
  roll-over, so ``content_t0 + duration`` should land on the next 03:00 /
  11:00 / 19:00 UTC boundary.  For ``w1D5DRiHFWM`` it gives 02:59:59 and
  for ``BH0wATmJbMs`` 19:00:02 -- both within the stated uncertainty,
  which is why the constant is trusted rather than assumed.

A frame-calibrated anchor in ``docs/battery-runs/stream-registry.json``
always wins over either of the above when one exists for the broadcast.

Everything here is best effort: it shells out to ``yt-dlp`` over the
network, and a capture run must never fail, stall, or lose data because
YouTube was slow.  Failures are recorded in the document as
``video.error`` and the run is written exactly as before.

Usage::

    # backfill an already-recorded run (writes the local file; --push
    # also $sets video on the MongoDB document, touching nothing else)
    python scripts/stream_anchor.py --run-json data/battery/<run>/run_salt.json --push

    # ad-hoc: what is the link for this instant?
    python scripts/stream_anchor.py --when 2026-09-01T16:50:26Z
"""

from __future__ import annotations

import argparse
import datetime
import json
import os
import re
import shutil
import subprocess
import sys

CHANNEL = "https://youtube.com/@byu-vcl-hardware-streams"
CAMERA = "picam-d1pr"
DB = "powder_doser"
COLLECTION = "battery_runs"
URI_ENV = "MONGODB_URI"

# Rate-cap every transfer over the Pi's residential link (CLAUDE.md).
RATE_LIMIT = "500K"
# yt-dlp over that link takes a few seconds; cap it so a slow or blocked
# YouTube cannot hold a finished run hostage.
DEFAULT_TIMEOUT_S = 90
# How far back in the channel listing to look.  Two cameras stream in
# parallel and each rolls over every 8 h, so 30 entries is ~5 days.
LISTING_ENTRIES = 30

# See the module docstring: calibrated against the burned-in overlay clock
# on w1D5DRiHFWM (2026-08-04 19:00 UTC), cross-checked against the
# roll-over boundary on BH0wATmJbMs (2026-09-01 11:00 UTC).
RELEASE_TO_CONTENT_S = -6.0
ANCHOR_UNCERTAINTY_S = 3
# Seek this far before the moment of interest so the viewer sees the tare
# and the plate tilting into position rather than an auger already turning.
LEAD_IN_S = 15

TITLE_RE = re.compile(
    r"^(?P<what>.+?) stream (?P<cam>[\w-]+), "
    r"(?P<date>\d{4}-\d{2}-\d{2}) UTC (?P<h>\d{2}):(?P<m>\d{2})$")

REGISTRY = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "docs", "battery-runs", "stream-registry.json")

# A broadcast covers at most one roll-over window; anything past this is a
# different video even if the listing is stale.
WINDOW_S = 8 * 3600


def parse_utc(value):
    """Parse an ISO-8601 stamp (or epoch seconds) into an aware datetime."""
    if isinstance(value, (int, float)):
        return datetime.datetime.fromtimestamp(
            value, datetime.timezone.utc)
    text = str(value).strip().replace("Z", "+00:00")
    stamp = datetime.datetime.fromisoformat(text)
    if stamp.tzinfo is None:
        stamp = stamp.replace(tzinfo=datetime.timezone.utc)
    return stamp.astimezone(datetime.timezone.utc)


def share_url(video_id, t_s):
    return "https://youtu.be/{}?t={}".format(video_id, int(t_s))


def _yt_dlp_argv():
    """yt-dlp as an argv prefix, from PATH or from this interpreter."""
    found = shutil.which("yt-dlp")
    if found:
        return [found]
    return [sys.executable, "-m", "yt_dlp"]


def _run(argv, timeout_s):
    proc = subprocess.run(argv, stdout=subprocess.PIPE,
                          stderr=subprocess.DEVNULL, timeout=timeout_s)
    if proc.returncode != 0:
        raise RuntimeError("yt-dlp exited {}".format(proc.returncode))
    return proc.stdout.decode("utf-8", "replace")


def list_broadcasts(camera=CAMERA, entries=LISTING_ENTRIES,
                    timeout_s=DEFAULT_TIMEOUT_S):
    """Recent broadcasts for one camera, newest first.

    Reads only the flat listing -- ids and titles, no formats -- which is
    the cheap half of yt-dlp and the half that is not IP-blocked.
    """
    out = _run(_yt_dlp_argv() + [
        "--limit-rate", RATE_LIMIT, "--flat-playlist", "--dump-json",
        "--playlist-end", str(entries), "--no-warnings",
        CHANNEL.rstrip("/") + "/streams"], timeout_s)
    found = []
    for line in out.splitlines():
        try:
            entry = json.loads(line)
        except ValueError:
            continue
        match = TITLE_RE.match((entry.get("title") or "").strip())
        if not match or match.group("cam") != camera:
            continue
        nominal = datetime.datetime(
            *[int(p) for p in match.group("date").split("-")],
            int(match.group("h")), int(match.group("m")),
            tzinfo=datetime.timezone.utc)
        found.append({
            "video_id": entry.get("id"),
            "title": entry.get("title"),
            "camera": camera,
            "nominal_start_utc": nominal,
            "duration_s": entry.get("duration"),
            "live_status": entry.get("live_status"),
        })
    return found


def broadcast_metadata(video_id, timeout_s=DEFAULT_TIMEOUT_S):
    """``release_timestamp`` and duration for one broadcast."""
    out = _run(_yt_dlp_argv() + [
        "--limit-rate", RATE_LIMIT, "--skip-download", "--no-warnings",
        "--print", "%(release_timestamp)s|%(duration)s",
        "https://www.youtube.com/watch?v=" + video_id], timeout_s)
    release, _, duration = out.strip().splitlines()[-1].partition("|")
    return {
        "release_timestamp": None if release in ("", "NA") else int(release),
        "duration_s": None if duration in ("", "NA") else int(float(duration)),
    }


def registry_anchor(video_id):
    """A frame-calibrated ``content_t0`` for this broadcast, if recorded."""
    try:
        with open(REGISTRY) as handle:
            registry = json.load(handle)
    except (OSError, ValueError):
        return None
    for stream in registry.get("streams", []):
        if stream.get("video_id") != video_id:
            continue
        t0 = stream.get("content_t0_utc")
        if not t0:
            continue
        return {
            "content_t0": parse_utc(t0),
            "anchor": "overlay-clock-calibrated (stream-registry.json)",
            "anchor_uncertainty_s": stream.get(
                "content_t0_uncertainty_s", 1),
        }
    return None


def covering_broadcast(when, broadcasts):
    """The broadcast whose window contains ``when``, or None."""
    candidates = [b for b in broadcasts
                  if b["nominal_start_utc"] <= when
                  and (when - b["nominal_start_utc"]).total_seconds() < WINDOW_S]
    if not candidates:
        return None
    return max(candidates, key=lambda b: b["nominal_start_utc"])


def anchor_for(when, camera=CAMERA, timeout_s=DEFAULT_TIMEOUT_S):
    """Resolve ``when`` to a broadcast plus the wall-clock of its ``t=0``."""
    broadcast = covering_broadcast(
        when, list_broadcasts(camera=camera, timeout_s=timeout_s))
    if broadcast is None:
        raise LookupError(
            "no {} broadcast covering {}".format(camera, when.isoformat()))
    calibrated = registry_anchor(broadcast["video_id"])
    if calibrated:
        broadcast.update(calibrated)
        return broadcast
    meta = broadcast_metadata(broadcast["video_id"], timeout_s=timeout_s)
    if meta.get("release_timestamp"):
        broadcast["content_t0"] = (
            parse_utc(meta["release_timestamp"])
            + datetime.timedelta(seconds=RELEASE_TO_CONTENT_S))
        broadcast["anchor"] = "release_timestamp{:+g}s".format(
            RELEASE_TO_CONTENT_S)
        broadcast["anchor_uncertainty_s"] = ANCHOR_UNCERTAINTY_S
        broadcast["duration_s"] = meta.get("duration_s")
    else:
        # No release stamp (a broadcast still live sometimes withholds
        # it).  The title's nominal start still finds the run, roughly.
        broadcast["content_t0"] = broadcast["nominal_start_utc"]
        broadcast["anchor"] = "title nominal start (uncalibrated)"
        broadcast["anchor_uncertainty_s"] = 90
    return broadcast


def _offset(content_t0, when):
    return round((when - content_t0).total_seconds(), 1)


def resolve(started_utc, ended_utc=None, timeline=None, doses=None,
            camera=CAMERA, timeout_s=DEFAULT_TIMEOUT_S, lead_in_s=LEAD_IN_S):
    """Build the ``video`` block for a run.  Never raises."""
    block = {"channel": CHANNEL, "camera": camera}
    try:
        started = parse_utc(started_utc)
        broadcast = anchor_for(started, camera=camera, timeout_s=timeout_s)
        t0 = broadcast["content_t0"]
        started_t = _offset(t0, started)
        block.update({
            "video_id": broadcast["video_id"],
            "title": broadcast["title"],
            "content_t0_utc": t0.isoformat(),
            "anchor": broadcast["anchor"],
            "anchor_uncertainty_s": broadcast["anchor_uncertainty_s"],
            "live_status": broadcast.get("live_status"),
            "lead_in_s": lead_in_s,
            "started_t_s": started_t,
            "url": share_url(broadcast["video_id"],
                             max(0, started_t - lead_in_s)),
        })
        if ended_utc:
            block["ended_t_s"] = _offset(t0, parse_utc(ended_utc))
        blocks = []
        for entry in timeline or []:
            if not entry.get("started_utc"):
                continue
            t_s = _offset(t0, parse_utc(entry["started_utc"]))
            blocks.append({"block": entry.get("block"), "t_s": t_s,
                           "url": share_url(broadcast["video_id"],
                                            max(0, t_s - lead_in_s))})
        if blocks:
            block["blocks"] = blocks
        # A dose reports its own duration, so its start is derivable even
        # though only the run's end is stamped: the run ends when the last
        # dose does.
        dose_rows = [d for d in (doses or []) if d.get("elapsed_s")]
        if dose_rows and ended_utc:
            end = parse_utc(ended_utc)
            starts = []
            remaining = 0.0
            for dose in reversed(dose_rows):
                remaining += float(dose["elapsed_s"])
                starts.append((dose.get("n"), end - datetime.timedelta(
                    seconds=remaining)))
            doses_out = []
            for n, start in reversed(starts):
                t_s = _offset(t0, start)
                doses_out.append({"n": n, "t_s": t_s,
                                  "url": share_url(broadcast["video_id"],
                                                   max(0, t_s - lead_in_s))})
            block["doses"] = doses_out
    except Exception as exc:                       # never break a capture
        block["error"] = "{}: {}".format(type(exc).__name__, exc)
    return block


def resolve_for_document(doc, camera=CAMERA, timeout_s=DEFAULT_TIMEOUT_S):
    """The ``video`` block for an already-built run document."""
    return resolve(doc.get("started_utc"), doc.get("ended_utc"),
                   timeline=doc.get("block_timeline"),
                   doses=doc.get("doses"), camera=camera,
                   timeout_s=timeout_s)


def push(doc, args):
    """``$set`` the video block on the MongoDB document, nothing else."""
    uri = os.environ.get(args.uri_env)
    if not uri:
        print("[push] {} is not set -- local file only".format(args.uri_env))
        return False
    try:
        from pymongo import MongoClient
    except ImportError:
        print("[push] pymongo not installed -- local file only")
        return False
    client = MongoClient(uri, serverSelectionTimeoutMS=15000)
    if getattr(args, "id", None):
        from bson import ObjectId
        query = {"_id": ObjectId(args.id)}
    else:
        # started_utc is microsecond-resolution and the collection holds
        # one document per run, so this identifies the run without
        # needing anyone to carry an ObjectId around.
        query = {"kind": "battery_run", "started_utc": doc["started_utc"],
                 "powder_id": doc.get("powder_id")}
    result = client[args.db][args.collection].update_many(
        query, {"$set": {"video": doc["video"]}})
    print("[push] matched {} modified {} in {}.{}".format(
        result.matched_count, result.modified_count,
        args.db, args.collection))
    return result.modified_count > 0


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Resolve the bench livestream link for a run or instant")
    parser.add_argument("--run-json", help="path to run_<powder>.json")
    parser.add_argument("--when", help="ad-hoc UTC instant, e.g. "
                        "2026-09-01T16:50:26Z")
    parser.add_argument("--camera", default=CAMERA)
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT_S)
    parser.add_argument("--push", action="store_true",
                        help="also $set video on the MongoDB document")
    parser.add_argument("--no-resolve", action="store_true",
                        help="push the video block already in the run "
                        "file instead of looking it up again")
    parser.add_argument("--id", default=None, metavar="OBJECTID",
                        help="target this _id instead of matching on "
                        "started_utc + powder_id")
    parser.add_argument("--db", default=DB)
    parser.add_argument("--collection", default=COLLECTION)
    parser.add_argument("--uri-env", default=URI_ENV)
    args = parser.parse_args(argv)

    if not args.run_json and not args.when:
        parser.error("give --run-json or --when")

    if args.when:
        when = parse_utc(args.when)
        block = resolve(when.isoformat(), camera=args.camera,
                        timeout_s=args.timeout)
        print(json.dumps(block, indent=2))
        return 0 if "error" not in block else 1

    with open(args.run_json) as handle:
        doc = json.load(handle)
    if args.no_resolve:
        # Resolution needs the Pi's residential IP (YouTube bot-blocks
        # datacenter ranges) but the MongoDB URI lives on the CI runner,
        # so the two halves sometimes run on different machines.
        block = doc.get("video")
        if not block or "error" in block:
            print("[resolve] --no-resolve but the run has no usable "
                  "video block")
            return 1
    else:
        block = resolve_for_document(doc, camera=args.camera,
                                     timeout_s=args.timeout)
        doc["video"] = block
        with open(args.run_json, "w") as handle:
            json.dump(doc, handle, indent=2)
            handle.write("\n")
    print(json.dumps(block, indent=2))
    if "error" in block:
        return 1
    if args.push:
        push(doc, args)
    return 0


if __name__ == "__main__":
    sys.exit(main())
