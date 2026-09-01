"""Unit tests for the offset arithmetic in stream_anchor.py.

The network half (yt-dlp against YouTube) is stubbed: what is worth
pinning down is the arithmetic between a broadcast anchor and a run's UTC
stamps, plus the promise that a capture is never broken by a link lookup.

The stub values are the real ones for the 2026-09-01 11:00 UTC powder
doser broadcast and the issue #148 salt dose, so the expected offsets
below are a regression anchor on links that have already been published.

Run:  python3 scripts/tests/test_stream_anchor.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import stream_anchor as sa

FAILURES = []

# Real listing entries for 2026-09-01 (camera picam-d1pr).
LISTING = [
    ("LMht8ZEB86E", "2026-09-01 UTC 19:00", None, "is_live"),
    ("BH0wATmJbMs", "2026-09-01 UTC 11:00", 28738, "was_live"),
    ("gIccn8I5Jug", "2026-09-01 UTC 03:00", 28733, "was_live"),
]
# yt-dlp release_timestamp for BH0wATmJbMs == 2026-09-01T11:01:10Z.
RELEASE = {"BH0wATmJbMs": 1788260470}

SALT_RUN = {
    "started_utc": "2026-09-01T16:50:26.581178+00:00",
    "ended_utc": "2026-09-01T16:53:19.190015+00:00",
    "powder_id": "salt",
    "block_timeline": [
        {"block": "G", "started_utc": "2026-09-01T16:50:30.072439+00:00"}],
    "doses": [{"n": 0, "elapsed_s": 167.0}],
}


def check(name, cond, detail=""):
    status = "PASS" if cond else "FAIL"
    print("{:4} {} {}".format(status, name, detail if not cond else ""))
    if not cond:
        FAILURES.append(name)


def broadcasts():
    return [{"video_id": vid,
             "title": "powder doser stream picam-d1pr, " + window,
             "camera": sa.CAMERA,
             "nominal_start_utc": sa.parse_utc(
                 window.replace(" UTC ", "T") + ":00Z"),
             "duration_s": duration,
             "live_status": status}
            for vid, window, duration, status in LISTING]


def stub_network(release=RELEASE, listing=None):
    """Point the two network calls at fixtures; return an undo callable."""
    saved = (sa.list_broadcasts, sa.broadcast_metadata, sa.registry_anchor)
    entries = broadcasts() if listing is None else listing
    sa.list_broadcasts = lambda **kw: entries
    sa.broadcast_metadata = lambda vid, **kw: {
        "release_timestamp": release.get(vid), "duration_s": 28738}
    sa.registry_anchor = lambda vid: None

    def undo():
        (sa.list_broadcasts, sa.broadcast_metadata,
         sa.registry_anchor) = saved
    return undo


def test_covering_broadcast():
    entries = broadcasts()
    hit = sa.covering_broadcast(
        sa.parse_utc("2026-09-01T16:50:26Z"), entries)
    check("picks the 11:00 window", hit["video_id"] == "BH0wATmJbMs", hit)
    hit = sa.covering_broadcast(
        sa.parse_utc("2026-09-01T19:30:00Z"), entries)
    check("picks the live 19:00 window", hit["video_id"] == "LMht8ZEB86E")
    check("nothing before the first listed broadcast",
          sa.covering_broadcast(
              sa.parse_utc("2026-08-30T00:00:00Z"), entries) is None)


def test_salt_run_offsets():
    undo = stub_network()
    try:
        block = sa.resolve_for_document(SALT_RUN)
    finally:
        undo()
    check("video id", block["video_id"] == "BH0wATmJbMs", block)
    check("content t0 is release - 6 s",
          block["content_t0_utc"].startswith("2026-09-01T11:01:04"),
          block["content_t0_utc"])
    check("run start offset", abs(block["started_t_s"] - 20962.6) < 0.1,
          block["started_t_s"])
    check("run end offset", abs(block["ended_t_s"] - 21135.2) < 0.1,
          block["ended_t_s"])
    check("block G offset", abs(block["blocks"][0]["t_s"] - 20966.1) < 0.1,
          block["blocks"])
    # The dose is stamped only by duration, so its start is backed out of
    # the run end -- 167 s before 16:53:19.
    check("dose offset", abs(block["doses"][0]["t_s"] - 20968.2) < 0.1,
          block["doses"])
    check("url leads the run in by lead_in_s",
          block["url"] == "https://youtu.be/BH0wATmJbMs?t=20947",
          block["url"])


def test_uncalibrated_fallback():
    """No release stamp: fall back to the title, and say so."""
    undo = stub_network(release={})
    try:
        block = sa.resolve_for_document(SALT_RUN)
    finally:
        undo()
    check("falls back to nominal start",
          block["content_t0_utc"].startswith("2026-09-01T11:00:00"),
          block["content_t0_utc"])
    check("uncertainty widens", block["anchor_uncertainty_s"] == 90,
          block["anchor_uncertainty_s"])
    check("anchor is labelled uncalibrated",
          "uncalibrated" in block["anchor"], block["anchor"])


def test_failures_never_raise():
    saved = sa.list_broadcasts

    def explode(**kw):
        raise RuntimeError("yt-dlp exited 1")
    sa.list_broadcasts = explode
    try:
        block = sa.resolve_for_document(SALT_RUN)
    finally:
        sa.list_broadcasts = saved
    check("network failure is recorded, not raised",
          block.get("error", "").endswith("yt-dlp exited 1"), block)
    check("no bogus url on failure", "url" not in block, block)

    undo = stub_network(listing=[])
    try:
        block = sa.resolve_for_document(SALT_RUN)
    finally:
        undo()
    check("an empty listing is an error, not a wrong link",
          "no picam-d1pr broadcast" in block.get("error", ""), block)


def test_registry_wins():
    """A frame-calibrated anchor beats the release-timestamp estimate."""
    undo = stub_network()
    sa.registry_anchor = lambda vid: {
        "content_t0": sa.parse_utc("2026-09-01T11:01:02Z"),
        "anchor": "overlay-clock-calibrated (stream-registry.json)",
        "anchor_uncertainty_s": 1}
    try:
        block = sa.resolve_for_document(SALT_RUN)
    finally:
        undo()
    check("uses the calibrated t0",
          block["content_t0_utc"].startswith("2026-09-01T11:01:02"),
          block["content_t0_utc"])
    check("tightens uncertainty", block["anchor_uncertainty_s"] == 1)
    check("offset shifts with the anchor",
          abs(block["started_t_s"] - 20964.6) < 0.1, block["started_t_s"])


def main():
    for test in (test_covering_broadcast, test_salt_run_offsets,
                 test_uncalibrated_fallback, test_failures_never_raise,
                 test_registry_wins):
        print("--- {}".format(test.__name__))
        test()
    print()
    if FAILURES:
        print("FAILED: {}".format(", ".join(FAILURES)))
        return 1
    print("all stream anchor tests passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
