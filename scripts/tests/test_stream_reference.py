"""Unit tests for the bench-camera video reference (issue #148).

Run:  python3 scripts/tests/test_stream_reference.py
"""

import datetime
import json
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import stream_reference as sr

FAILURES = []

# One anchored broadcast, the shape the real registry uses.
STREAMS = [
    {
        "video_id": "w1D5DRiHFWM",
        "title": "powder doser stream picam-d1pr, 2026-08-04 UTC 19:00",
        "camera": "picam-d1pr",
        "content_t0_utc": "2026-08-04T19:01:06+00:00",
        "content_t0_uncertainty_s": 1,
    },
]


def check(name, cond, detail=""):
    status = "PASS" if cond else "FAIL"
    print("{:4} {} {}".format(status, name, detail if not cond else ""))
    if not cond:
        FAILURES.append(name)


def test_parse_utc():
    aware = sr.parse_utc("2026-08-04T19:01:06+00:00")
    check("offset stamp", aware.hour == 19 and aware.minute == 1)
    check("Z suffix", sr.parse_utc("2026-08-04T19:01:06Z") == aware,
          "fromisoformat only accepts Z from 3.11")
    check("naive means UTC", sr.parse_utc("2026-08-04T19:01:06") == aware)
    check("other offsets normalize",
          sr.parse_utc("2026-08-04T13:01:06-06:00") == aware)


def test_broadcast_slot():
    def slot(stamp):
        return sr.broadcast_slot(sr.parse_utc(stamp)).isoformat()

    check("mid-afternoon lands in the 11:00 slot",
          slot("2026-09-01T16:50:26Z") == "2026-09-01T11:00:00+00:00")
    check("exactly on a rollover takes that slot",
          slot("2026-09-01T19:00:00Z") == "2026-09-01T19:00:00+00:00")
    check("just before a rollover stays in the older slot",
          slot("2026-09-01T18:59:59Z") == "2026-09-01T11:00:00+00:00")
    check("after midnight belongs to yesterday's 19:00 broadcast",
          slot("2026-09-02T01:30:00Z") == "2026-09-01T19:00:00+00:00")


def test_resolved():
    ref = sr.describe("2026-08-04T21:17:41+00:00",
                      "2026-08-04T21:20:34+00:00", streams=STREAMS)
    check("resolved", ref["resolved"] is True, ref)
    check("video id", ref["video_id"] == "w1D5DRiHFWM")
    # 21:17:41 - 19:01:06 = 2 h 16 m 35 s
    check("offset", abs(ref["t_offset_s"] - 8195.0) < 1e-6, ref["t_offset_s"])
    check("link carries the lead-in",
          ref["url"] == "https://youtu.be/w1D5DRiHFWM?t=8190", ref["url"])
    check("duration", abs(ref["duration_s"] - 173.0) < 1e-6)
    check("slot recorded even when resolved",
          ref["broadcast_slot_utc"] == "2026-08-04T19:00:00+00:00")
    check("anchor uncertainty carried", ref["content_t0_uncertainty_s"] == 1)


def test_unresolved_is_still_useful():
    """The common case at capture time: nobody has anchored today's stream."""
    ref = sr.describe("2026-09-01T16:50:26Z", "2026-09-01T16:53:19Z",
                      streams=STREAMS)
    check("unresolved", ref["resolved"] is False)
    check("no link invented", ref["url"] is None)
    check("names the broadcast to go find",
          ref["broadcast_slot_utc"] == "2026-09-01T11:00:00+00:00")
    check("says how to fix it", "calibrate" in ref.get("note", ""))
    check("run window is self-contained",
          ref["started_utc"] == "2026-09-01T16:50:26Z"
          and ref["ended_utc"] == "2026-09-01T16:53:19Z")


def test_coverage_boundaries():
    before = sr.describe("2026-08-04T19:00:00Z", "2026-08-04T19:05:00Z",
                         streams=STREAMS)
    check("a run starting before content t=0 is not claimed",
          before["resolved"] is False)
    past = sr.describe("2026-08-05T03:30:00Z", "2026-08-05T03:35:00Z",
                       streams=STREAMS)
    check("a run past the 8 h broadcast is not claimed",
          past["resolved"] is False)
    other = sr.describe("2026-08-04T21:17:41Z", "2026-08-04T21:20:34Z",
                        camera="picam-other", streams=STREAMS)
    check("another camera's run is not claimed", other["resolved"] is False)
    check("the requested camera is echoed back",
          other["camera"] == "picam-other")


def test_never_raises():
    """Provenance must not be able to break a capture run."""
    missing = sr.describe("2026-08-04T21:17:41Z", "2026-08-04T21:20:34Z",
                          registry_path="/nonexistent/registry.json")
    check("missing registry degrades gracefully",
          missing["resolved"] is False and "registry" in missing["note"])
    bad = sr.describe("not a timestamp", None, streams=STREAMS)
    check("unparseable stamps degrade gracefully",
          bad["resolved"] is False and "unparseable" in bad["note"])

    with tempfile.NamedTemporaryFile("w", suffix=".json",
                                     delete=False) as handle:
        handle.write("{ not json")
        junk = handle.name
    try:
        broken = sr.describe("2026-08-04T21:17:41Z", "2026-08-04T21:20:34Z",
                             registry_path=junk)
        check("corrupt registry degrades gracefully",
              broken["resolved"] is False)
    finally:
        os.unlink(junk)


def test_backfill():
    doc = {"started_utc": "2026-08-04T21:17:41+00:00",
           "ended_utc": "2026-08-04T21:20:34+00:00"}
    changed = sr.backfill(doc, streams=STREAMS)
    check("backfill adds the block", changed and doc["video"]["resolved"])
    check("backfill is idempotent",
          sr.backfill(doc, streams=STREAMS) is False)
    doc["video"] = {"camera": "picam-other", "resolved": False}
    sr.backfill(doc, streams=STREAMS)
    check("backfill keeps the camera the run was shot on",
          doc["video"]["camera"] == "picam-other")


def test_registry_ships_parseable():
    streams = sr.load_registry()
    check("committed registry loads", len(streams) >= 1)
    for stream in streams:
        sr.parse_utc(stream["content_t0_utc"])
        check("registry entry %s is complete" % stream.get("video_id"),
              bool(stream.get("video_id")) and bool(stream.get("camera")))


def test_capture_scripts_embed_it():
    import characterize_capture
    import powder_battery_capture

    class Bare(object):
        powder_id = "salt"
        powder = None
        operator = None
        notes = None

    battery = powder_battery_capture.build_run_document(
        {}, [], [], [], [], [], "ok", Bare(),
        "2026-08-04T21:17:41+00:00", "2026-08-04T21:20:34+00:00")
    check("battery run document carries video",
          battery["video"]["url"]
          == "https://youtu.be/w1D5DRiHFWM?t=8190", battery.get("video"))

    sweep = characterize_capture.build_run_document(
        {}, [], [], [], "ok", Bare(),
        "2026-08-04T21:17:41+00:00", "2026-08-04T21:20:34+00:00")
    check("characterization run document carries video",
          sweep["video"]["url"] == "https://youtu.be/w1D5DRiHFWM?t=8190",
          sweep.get("video"))
    check("default camera is the powder-doser rig",
          sweep["video"]["camera"] == "picam-d1pr")


def main():
    for test in (test_parse_utc, test_broadcast_slot, test_resolved,
                 test_unresolved_is_still_useful, test_coverage_boundaries,
                 test_never_raises, test_backfill,
                 test_registry_ships_parseable,
                 test_capture_scripts_embed_it):
        print("--- {}".format(test.__name__))
        test()
    print()
    if FAILURES:
        print("FAILED: {}".format(", ".join(FAILURES)))
        return 1
    print("all stream-reference tests passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
