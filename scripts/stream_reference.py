#!/usr/bin/env python3
"""Bench-camera video reference, stamped into the run document itself.

Every run happens in front of a bench camera that streams continuously to
https://youtube.com/@byu-vcl-hardware-streams in rolling 8 h broadcasts, so
a video record of each run already exists -- historically it had to be found
again afterwards, by feeding the run's UTC timestamps through
``scripts/battery_stream_links.py``.  Reconstructing it after the fact is
fragile: it needs the registry, the run document, and someone who remembers
the two are related.  This module lets a capture script stamp the reference
into the run document *as the run is recorded*, so every artifact carries
its own pointer back at the video (issue #148).

``describe(started_utc, ended_utc)`` returns the ``video`` block that
``powder_battery_capture.py`` and ``characterize_capture.py`` embed::

    "video": {
      "camera": "picam-d1pr",
      "channel_url": "https://youtube.com/@byu-vcl-hardware-streams",
      "broadcast_slot_utc": "2026-08-04T19:00:00+00:00",
      "started_utc": "2026-08-04T21:17:41+00:00",
      "ended_utc": "2026-08-04T21:20:34+00:00",
      "duration_s": 173.0,
      "resolved": true,
      "video_id": "w1D5DRiHFWM",
      "content_t0_utc": "2026-08-04T19:01:06+00:00",
      "content_t0_uncertainty_s": 1,
      "t_offset_s": 8195.0,
      "url": "https://youtu.be/w1D5DRiHFWM?t=8190"
    }

A run usually cannot be resolved to a ``?t=`` link at capture time: the
covering broadcast has to be anchored first, and its content t=0 is only
knowable from the burned-in overlay clock (``battery_stream_links.py
--calibrate``), which needs the Pi's residential IP because YouTube
bot-blocks datacenter ranges.  An unresolved block is still worth writing
down -- it names the camera, the channel and the exact 8 h broadcast slot
to look in -- and it is filled in later by::

    python scripts/stream_reference.py --backfill data/battery/*/run_*.json

which re-resolves each run against the current registry and rewrites its
``video`` block in place.  Resolving is deliberately never fatal: a capture
run must not fail because a video link could not be worked out.
"""

import argparse
import datetime
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REGISTRY = os.path.join(REPO, "docs", "battery-runs", "stream-registry.json")

CHANNEL_URL = "https://youtube.com/@byu-vcl-hardware-streams"
DEFAULT_CAMERA = "picam-d1pr"

# Broadcasts roll over every 8 h; the actual content starts a minute or so
# after the nominal slot (19:01:06 for the 19:00 slot on 2026-08-04).
ROLLOVER_HOURS_UTC = (3, 11, 19)
BROADCAST_HOURS = 8

# Seconds of run-up before the event, so a link lands just before the thing
# it points at rather than a frame into it.
LEAD_IN_S = 5


def load_registry(path=REGISTRY):
    with open(path) as fh:
        return json.load(fh)["streams"]


def parse_utc(text):
    """ISO-8601 to an aware UTC datetime.

    Tolerates the ``Z`` suffix (``fromisoformat`` only learned it in 3.11)
    and naive stamps, which every producer here means as UTC.
    """
    if isinstance(text, datetime.datetime):
        stamp = text
    else:
        stamp = datetime.datetime.fromisoformat(
            text.strip().replace("Z", "+00:00"))
    if stamp.tzinfo is None:
        stamp = stamp.replace(tzinfo=datetime.timezone.utc)
    return stamp.astimezone(datetime.timezone.utc)


def hms(seconds):
    seconds = int(round(seconds))
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    return "%dh%02dm%02ds" % (h, m, s) if h else "%dm%02ds" % (m, s)


def link(video_id, offset_s, lead_in=LEAD_IN_S):
    return "https://youtu.be/%s?t=%d" % (
        video_id, max(0, int(round(offset_s)) - lead_in))


def broadcast_slot(when):
    """Nominal start of the 8 h broadcast covering ``when``.

    Names the broadcast to go looking for when no anchor exists yet; the
    stream's real content t=0 lags this by however long the encoder took to
    come up, which is exactly what calibration measures.
    """
    midnight = when.replace(hour=0, minute=0, second=0, microsecond=0)
    starts = [midnight + datetime.timedelta(days=day, hours=hour)
              for day in (-1, 0) for hour in ROLLOVER_HOURS_UTC]
    return max(start for start in starts if start <= when)


def pick_stream(streams, started, ended, camera=DEFAULT_CAMERA):
    """The stream whose coverage contains the whole run, if any."""
    for stream in streams:
        if stream.get("camera") != camera:
            continue
        t0 = parse_utc(stream["content_t0_utc"])
        if t0 <= started and ended <= t0 + datetime.timedelta(
                hours=BROADCAST_HOURS):
            return stream
    return None


def describe(started_utc, ended_utc, camera=DEFAULT_CAMERA,
             registry_path=REGISTRY, streams=None, lead_in=LEAD_IN_S):
    """The ``video`` block for a run spanning ``started_utc``..``ended_utc``.

    Always returns a dict.  ``resolved`` says whether a calibrated anchor
    was found; when it is false the block still carries everything needed
    to resolve the link later.
    """
    ref = {
        "camera": camera,
        "channel_url": CHANNEL_URL,
        "started_utc": started_utc,
        "ended_utc": ended_utc,
        "resolved": False,
        "url": None,
    }
    try:
        started = parse_utc(started_utc)
        ended = parse_utc(ended_utc) if ended_utc else started
    except (TypeError, ValueError) as exc:
        ref["note"] = "unparseable run timestamps: %s" % exc
        return ref

    ref["broadcast_slot_utc"] = broadcast_slot(started).isoformat()
    ref["duration_s"] = round((ended - started).total_seconds(), 3)

    if streams is None:
        try:
            streams = load_registry(registry_path)
        except (OSError, ValueError, KeyError) as exc:
            ref["note"] = "stream registry unreadable (%s)" % exc
            return ref

    stream = pick_stream(streams, started, ended, camera)
    if stream is None:
        ref["note"] = (
            "no calibrated anchor covers the %s broadcast; add one with "
            "`python scripts/battery_stream_links.py --calibrate`, then "
            "`python scripts/stream_reference.py --backfill <run.json>`"
            % ref["broadcast_slot_utc"])
        return ref

    t0 = parse_utc(stream["content_t0_utc"])
    offset = (started - t0).total_seconds()
    ref.update({
        "resolved": True,
        "video_id": stream["video_id"],
        "title": stream.get("title"),
        "content_t0_utc": stream["content_t0_utc"],
        "content_t0_uncertainty_s": stream.get("content_t0_uncertainty_s"),
        "t_offset_s": round(offset, 3),
        "lead_in_s": lead_in,
        "url": link(stream["video_id"], offset, lead_in),
    })
    return ref


def backfill(doc, camera=None, registry_path=REGISTRY, streams=None):
    """Re-resolve ``doc['video']`` in place; True if the block changed.

    A run captured before an anchor existed gets its link the moment the
    covering broadcast is calibrated -- no need to re-derive which video a
    run belongs to, because the run already recorded that.
    """
    previous = doc.get("video") or {}
    camera = camera or previous.get("camera") or DEFAULT_CAMERA
    ref = describe(doc.get("started_utc"), doc.get("ended_utc"),
                   camera=camera, registry_path=registry_path,
                   streams=streams)
    doc["video"] = ref
    return ref != previous


def main(argv=None):
    parser = argparse.ArgumentParser(
        description=__doc__.split("\n", 1)[0],
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--backfill", nargs="+", metavar="RUN_JSON",
                        default=None,
                        help="re-resolve the video block of each run "
                        "document against the current registry, in place")
    parser.add_argument("--started", default=None, metavar="UTC",
                        help="run start, ISO-8601 UTC (prints the block)")
    parser.add_argument("--ended", default=None, metavar="UTC",
                        help="run end, ISO-8601 UTC (defaults to --started)")
    parser.add_argument("--camera", default=DEFAULT_CAMERA)
    parser.add_argument("--registry", default=REGISTRY)
    args = parser.parse_args(argv)

    if args.backfill:
        changed = 0
        for path in args.backfill:
            with open(path) as fh:
                doc = json.load(fh)
            if backfill(doc, camera=args.camera, registry_path=args.registry):
                with open(path, "w") as fh:
                    json.dump(doc, fh, indent=2)
                changed += 1
            ref = doc["video"]
            shown = os.path.relpath(path, REPO)
            if shown.startswith(os.pardir):
                shown = path
            print("%-58s %s" % (
                shown, ref["url"] if ref["resolved"] else "unresolved"))
        print("\n%d of %d run document(s) updated"
              % (changed, len(args.backfill)))
        return 0

    if not args.started:
        parser.error("give --backfill RUN_JSON... or --started UTC")
    print(json.dumps(describe(args.started, args.ended or args.started,
                              camera=args.camera,
                              registry_path=args.registry), indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
