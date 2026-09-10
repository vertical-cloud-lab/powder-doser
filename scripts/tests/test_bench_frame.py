"""Unit tests for scripts/bench_frame.py (no network, no Pi, no camera).

The interesting logic is all in how the remote commands are built: which
broadcast gets picked, how far back in the DVR playlist a segment index
lands, and whether failures are reported rather than swallowed into an
empty image.  Those are exercised here with the SSH layer stubbed out.

Run:  python3 scripts/tests/test_bench_frame.py
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import bench_frame

FAILURES = []


def check(name, cond, detail=""):
    status = "PASS" if cond else "FAIL"
    print("{:4} {} {}".format(status, name, detail if not cond else ""))
    if not cond:
        FAILURES.append(name)


class FakePi:
    """Stands in for pi_run: records commands, replays canned stdout."""

    def __init__(self, responses):
        self.responses = list(responses)
        self.commands = []

    def __call__(self, command, timeout=300):
        self.commands.append(command)
        if not self.responses:
            return ""
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response


def listing(*entries):
    return json.dumps({"entries": list(entries)})


LIVE_DOSER = {"id": "_iDB8z83GdQ", "live_status": "is_live",
              "title": "powder doser stream picam-d1pr, 2026-08-05 UTC 19:00"}
LIVE_OT2 = {"id": "wi1ItzwcWs4", "live_status": "is_live",
            "title": "OT-2 stream picam-ot2, 2026-08-05 UTC 19:00"}
OLD_DOSER = {"id": "5ENY3XL4yhc", "live_status": "was_live",
             "title": "powder doser stream picam-d1pr, 2026-08-05 UTC 11:00"}


def with_pi(responses):
    fake = FakePi(responses)
    bench_frame.pi_run = fake
    return fake


def test_find_live_video():
    with_pi([listing(LIVE_OT2, LIVE_DOSER, OLD_DOSER)])
    video = bench_frame.find_live_video()
    check("picks the powder-doser stream, not the OT-2 one",
          video["id"] == "_iDB8z83GdQ", video)

    with_pi([listing(LIVE_OT2, LIVE_DOSER)])
    check("--match selects a different camera",
          bench_frame.find_live_video("OT-2")["id"] == "wi1ItzwcWs4")

    # An ended broadcast must not be mistaken for the live one: seeking the
    # live edge of a finished video silently returns stale footage, which is
    # exactly the failure mode that would make a "current" frame a lie.
    with_pi([listing(LIVE_OT2, OLD_DOSER)])
    try:
        bench_frame.find_live_video()
        check("was_live is rejected", False, "returned a finished broadcast")
    except bench_frame.BenchFrameError as exc:
        check("was_live is rejected", "no live broadcast" in str(exc))

    with_pi(["not json at all"])
    try:
        bench_frame.find_live_video()
        check("unparseable listing raises", False)
    except bench_frame.BenchFrameError:
        check("unparseable listing raises", True)


def _segment_index(command):
    """Pull the `tail -N` index out of the generated remote script."""
    for line in command.splitlines():
        if line.startswith("SEG=") and "tail -" in line:
            return int(line.split("tail -")[1].split(" ")[0].rstrip(")").strip())
    raise AssertionError("no segment selection in:\n{}".format(command))


def test_fetch_segment_index():
    fake = with_pi(["150000"])
    bench_frame.fetch_segment("vid", "95", 0.0)
    check("live edge takes the last segment",
          _segment_index(fake.commands[0]) == 1)

    fake = with_pi(["150000"])
    bench_frame.fetch_segment("vid", "95", 4000.0)
    # 4000 s / 2 s per segment = 2000 segments back, +1 for the live edge
    check("4000 s ago -> 2001 segments back",
          _segment_index(fake.commands[0]) == 2001,
          _segment_index(fake.commands[0]))

    fake = with_pi(["150000"])
    bench_frame.fetch_segment("vid", "93", 3.0)
    check("rounds to the nearest segment",
          _segment_index(fake.commands[0]) == 3,
          _segment_index(fake.commands[0]))
    check("itag is forwarded to yt-dlp", "-f 93" in fake.commands[0])

    fake = with_pi(["150000"])
    bench_frame.fetch_segment("vid", "95", 10.0)
    check("rate limit is applied to both fetches",
          fake.commands[0].count("--limit-rate") == 2)


def test_fetch_segment_failures():
    # A zero-byte segment is the real-world symptom of asking for a format
    # the broadcast does not carry.  It must raise, not write an empty file
    # that ffmpeg later turns into a confusing decode error.
    with_pi(["0"])
    try:
        bench_frame.fetch_segment("vid", "95", 0.0)
        check("empty segment raises", False)
    except bench_frame.BenchFrameError as exc:
        check("empty segment raises", "lower --itag" in str(exc))

    with_pi([bench_frame.BenchFrameError("remote command failed (4)")])
    try:
        bench_frame.fetch_segment("vid", "95", 99999.0)
        check("beyond the DVR window raises", False)
    except bench_frame.BenchFrameError:
        check("beyond the DVR window raises", True)


def test_itag_fallback():
    # Which itags a broadcast advertises has changed under us: the Pi's
    # yt-dlp sees the 91-95 ladder, other extraction paths return
    # 229-232/269.  Pinning one and failing with "no manifest" is what
    # cost a session; the list must be tried in order.
    check("default list covers both ladders",
          "95" in bench_frame.DEFAULT_ITAGS
          and "232" in bench_frame.DEFAULT_ITAGS)

    calls = []

    def fake(video_id, itag, seconds_ago, remote_path="/tmp/bench_frame.ts"):
        calls.append(itag)
        if itag != "93":
            raise bench_frame.BenchFrameError("no manifest for itag " + itag)
        return 4242

    original = bench_frame.fetch_segment
    bench_frame.fetch_segment = fake
    try:
        size = bench_frame.fetch_segment_any("vid", ["95", "232", "93"], 0.0)
        check("falls through to the first itag that works", size == 4242)
        check("tries them in order", calls == ["95", "232", "93"], calls)

        calls.clear()
        try:
            bench_frame.fetch_segment_any("vid", ["95", "232"], 0.0)
            check("exhausting every itag raises", False)
        except bench_frame.BenchFrameError as exc:
            check("exhausting every itag raises",
                  "95" in str(exc) and "232" in str(exc), str(exc))

        # An older-than-DVR request fails identically on every itag, so it
        # must propagate immediately rather than burn N more round trips.
        calls.clear()

        def dvr(video_id, itag, seconds_ago, remote_path="/tmp/bench_frame.ts"):
            calls.append(itag)
            raise bench_frame.BenchFrameError("older than the DVR window")

        bench_frame.fetch_segment = dvr
        try:
            bench_frame.fetch_segment_any("vid", ["95", "232", "93"], 99999.0)
            check("DVR-window failure is not retried", False)
        except bench_frame.BenchFrameError:
            check("DVR-window failure is not retried", calls == ["95"], calls)
    finally:
        bench_frame.fetch_segment = original


def test_curl_follows_redirects():
    # Live manifest and segment URLs answer 302.  Without -L, curl writes a
    # 0-byte file and the failure surfaces as "empty segment" -- which reads
    # as "wrong itag" and sends you chasing the wrong thing.
    source = Path(bench_frame.__file__).read_text()
    bare = [line.strip() for line in source.splitlines()
            if "curl -sS " in line and "curl -sSL" not in line]
    check("every curl follows redirects", not bare, bare)


def test_credentials_are_not_echoed():
    # CLAUDE.md: the Pi's hostname and credentials must never appear in
    # logs or output.  The module may read them, never print them.
    source = Path(bench_frame.__file__).read_text()
    check("hostname is read exactly once, from the environment",
          source.count('os.environ.get("RPI_POWDER_DOSER_HOSTNAME")') == 1)
    # The env var *name* may appear in the "you forgot to set this" message;
    # what must never happen is the *value* reaching stdout/stderr.
    printed = [line for line in source.splitlines()
               if "print(" in line and ("host" in line or "_pi_target" in line)]
    check("no print statement interpolates the host", not printed, printed)

    import os as _os
    saved = {k: _os.environ.get(k) for k in
             ("RPI_POWDER_DOSER_USERNAME", "RPI_POWDER_DOSER_HOSTNAME")}
    try:
        for key in saved:
            _os.environ.pop(key, None)
        try:
            bench_frame._pi_target()
            check("missing credentials raise a clear error", False)
        except bench_frame.BenchFrameError as exc:
            check("missing credentials raise a clear error",
                  "never print" in str(exc))
    finally:
        for key, value in saved.items():
            if value is not None:
                _os.environ[key] = value


def main():
    original = bench_frame.pi_run
    try:
        for test in (test_find_live_video, test_fetch_segment_index,
                     test_fetch_segment_failures, test_itag_fallback,
                     test_curl_follows_redirects,
                     test_credentials_are_not_echoed):
            print("--- {}".format(test.__name__))
            test()
    finally:
        bench_frame.pi_run = original

    print()
    if FAILURES:
        print("FAILED: {}".format(", ".join(FAILURES)))
        return 1
    print("all bench_frame checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
