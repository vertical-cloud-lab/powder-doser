#!/usr/bin/env python3
"""Checks for the generated run log (``scripts/build_run_log.py``).

The log is the thing you reach for months later to answer "what was running
then, and where is the video?", so the ways it can quietly lie matter more
than usual:

* a run pointing at the **wrong broadcast**, or at a `?t=` offset computed
  from the wrong anchor -- the link still opens, it just shows the wrong hour;
* an **approximate link labelled exact**, which would send someone hunting for
  a specific auger revolution at a link that cannot resolve one;
* the **wrong run notes** attached to a run, which is easy when the same
  powder ran three times in two days;
* **dispensed mass** silently netting balance artifacts against real powder.

Each of those is pinned below against fixtures, plus a consistency pass over
the real committed runs.

Usage::

    python scripts/tests/test_build_run_log.py
"""

import datetime as dt
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                os.pardir))

import build_run_log as rl  # noqa: E402

FAILURES = []


def check(name, condition, detail=""):
    status = "ok  " if condition else "FAIL"
    print("[{}] {}{}".format(status, name, "  -- " + detail if detail else ""))
    if not condition:
        FAILURES.append(name)


def _utc(s):
    return dt.datetime.fromisoformat(s)


BROADCASTS = [
    {"video_id": "aaa", "title": "b1", "_start": _utc("2026-08-20T03:00:00+00:00")},
    {"video_id": "bbb", "title": "b2", "_start": _utc("2026-08-20T11:00:00+00:00")},
    {"video_id": "ccc", "title": "b3", "_start": _utc("2026-08-20T19:00:00+00:00")},
]


def test_video_picks_the_covering_broadcast():
    print("\n-- the link points at the broadcast that was live --")
    v = rl.find_video(_utc("2026-08-20T17:56:31+00:00"), BROADCASTS, {})
    check("run inside the 11:00 window uses that broadcast",
          v and v["video_id"] == "bbb", str(v))
    check("offset is measured from the broadcast start",
          v and v["offset_s"] == 6 * 3600 + 56 * 60 + 31 - rl.LINK_LEAD_S,
          str(v and v["offset_s"]))
    v = rl.find_video(_utc("2026-08-20T19:22:25+00:00"), BROADCASTS, {})
    check("a run just after a rollover uses the new broadcast",
          v and v["video_id"] == "ccc", str(v))
    check("no broadcast before the listing starts",
          rl.find_video(_utc("2026-08-19T23:00:00+00:00"), BROADCASTS, {})
          is None)


def test_a_calibrated_anchor_wins_and_is_labelled():
    print("\n-- approximate links are never labelled exact --")
    when = _utc("2026-08-20T11:10:00+00:00")
    plain = rl.find_video(when, BROADCASTS, {})
    check("uncalibrated link is marked inexact", plain and not plain["exact"])
    anchored = rl.find_video(
        when, BROADCASTS, {"bbb": _utc("2026-08-20T11:01:06+00:00")})
    check("calibrated link is marked exact", anchored and anchored["exact"])
    check("calibrated offset is shifted by the anchor",
          anchored["offset_s"] == plain["offset_s"] - 66,
          "{} vs {}".format(anchored["offset_s"], plain["offset_s"]))


def test_link_never_seeks_before_the_video_starts():
    print("\n-- a run at the very start of a broadcast still yields a link --")
    v = rl.find_video(_utc("2026-08-20T19:00:02+00:00"), BROADCASTS, {})
    check("offset is clamped at zero", v and v["offset_s"] == 0, str(v))


def test_dispensed_mass_ignores_negative_artifacts():
    print("\n-- balance artifacts are not netted against real powder --")
    run = {"trials": [{"delta_g": 0.20}, {"delta_g": -0.05}, {"delta_g": 0.10}],
           "doses": [{"dispensed_g": 0.99}, {"dispensed_g": -0.01}]}
    check("negative trial deltas are dropped, not subtracted",
          abs(rl.dispensed_g(run) - (0.20 + 0.10 + 0.99)) < 1e-9,
          str(rl.dispensed_g(run)))
    check("a run with no trials reports nothing rather than zero",
          rl.dispensed_g({}) is None)


def test_blocks_reflect_what_ran_not_what_was_asked_for():
    print("\n-- a skipped block does not appear as if it ran --")
    run = {"parameters": {"blocks": "ABCDEFG"},
           "trials": [{"block": "A"}, {"block": "C"}, {"block": "E"}],
           "doses": []}
    got = rl.blocks_run(run)
    check("only blocks with trials are listed", got == "ACE", got)
    check("block F is not claimed when the driver was absent", "F" not in got,
          got)
    run["doses"] = [{"n": 0}]
    check("closed-loop doses add block G", "G" in rl.blocks_run(run),
          rl.blocks_run(run))


def test_notes_match_the_right_run():
    print("\n-- follow-up notes stay attached to their own run --")
    for dirname, want in rl.NOTES_OVERRIDES.items():
        run = {"_dir": rl.BATTERY_DIR / dirname, "powder_id": "x"}
        got = rl.find_notes(run)
        check("pinned notes exist for {}".format(dirname),
              got is not None and got.name == want,
              str(got))


def test_feed_factor_reports_horizontal():
    """Tilt 0 deg is falsy, and an ``or``-style default silently ate it.

    Every entry in the log read "0 deg -- mg/rev" from the day it was
    generated, for every run, including ones whose block C at 0 deg is a
    perfectly good measurement (silicon, 57.2 mg/rev).
    """
    print("\n-- feed factor at every tilt --")
    run = {"host_summary": [
        {"block": "C", "phase": "rotation", "tilt_deg": 0.0,
         "mean_g": 0.0572},
        {"block": "C", "phase": "rotation", "tilt_deg": 45.0,
         "mean_g": 0.2107},
        {"block": "C", "phase": "rotation", "tilt_deg": 90.0,
         "mean_g": 0.3024},
    ]}
    check("tilt 0 is reported",
          abs((rl.feed_factor(run, 0.0) or 0) - 57.2) < 0.05,
          "{}".format(rl.feed_factor(run, 0.0)))
    check("tilt 45 is reported",
          abs((rl.feed_factor(run, 45.0) or 0) - 210.7) < 0.05)
    check("tilt 90 is reported",
          abs((rl.feed_factor(run, 90.0) or 0) - 302.4) < 0.05)
    check("a tilt that was not run stays None",
          rl.feed_factor(run, 30.0) is None)
    check("a row with no tilt does not match",
          rl.feed_factor({"host_summary": [
              {"block": "C", "phase": "rotation", "mean_g": 0.1}]},
              0.0) is None)
    # And on the real runs, not just the fixture.
    zeros = [r for r in rl.load_runs()
             if rl.feed_factor(r, 90.0) is not None
             and rl.feed_factor(r, 0.0) is None]
    check("no committed run reports 45/90 but not 0", not zeros,
          ", ".join(r.get("powder_id", "?") for r in zeros))


def test_real_runs_are_consistent():
    print("\n-- the committed runs all resolve --")
    runs = rl.load_runs()
    broadcasts = rl.load_broadcasts()
    anchors = rl.load_anchors()
    check("runs were found", len(runs) > 0, "{}".format(len(runs)))
    check("broadcast listing was found", len(broadcasts) > 0,
          "{}".format(len(broadcasts)))
    rows = [rl.row_for(r, broadcasts, anchors) for r in runs]
    check("every run has a start time",
          all(r["started_utc"] for r in rows))
    check("every run resolves to a broadcast",
          all(r["video_url"] for r in rows),
          ", ".join(r["powder_id"] for r in rows if not r["video_url"]))
    check("every run has a data directory",
          all(os.path.isdir(rl.REPO / r["data_dir"]) for r in rows))
    check("linked notes exist on disk",
          all(os.path.isfile(rl.REPO / r["notes"])
              for r in rows if r["notes"]))
    check("no two runs share a start time",
          len({r["started_utc"] for r in rows}) == len(rows))
    md = rl.render_md(rows)
    check("markdown has a row per run",
          all(r["powder_id"] in md for r in rows))
    check("markdown renders every video link",
          all(r["video_url"] in md for r in rows if r["video_url"]))
    csv_text = rl.render_csv(rows)
    check("csv has a line per run plus a header",
          len(csv_text.strip().splitlines()) == len(rows) + 1)


def main():
    test_video_picks_the_covering_broadcast()
    test_a_calibrated_anchor_wins_and_is_labelled()
    test_link_never_seeks_before_the_video_starts()
    test_dispensed_mass_ignores_negative_artifacts()
    test_blocks_reflect_what_ran_not_what_was_asked_for()
    test_notes_match_the_right_run()
    test_feed_factor_reports_horizontal()
    test_real_runs_are_consistent()
    if FAILURES:
        print("\n{} check(s) failed: {}".format(len(FAILURES),
                                                ", ".join(FAILURES)))
        return 1
    print("\nall checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
