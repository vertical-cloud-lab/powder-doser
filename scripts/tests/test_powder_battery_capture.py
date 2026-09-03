"""Unit tests for the pure functions in powder_battery_capture.py.

Run:  python3 scripts/tests/test_powder_battery_capture.py
"""

import sys
import json
import os
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import powder_battery_capture as cap

FAILURES = []


def check(name, cond, detail=""):
    status = "PASS" if cond else "FAIL"
    print("{:4} {} {}".format(status, name, detail if not cond else ""))
    if not cond:
        FAILURES.append(name)


def test_parse_trial():
    kind, row = cap.parse_line(
        "CSV,C,45.0,rotation,2,360.0,30,0.1000,0.1310,0.0310,,182345")
    check("trial kind", kind == "trial")
    check("trial fields", row["block"] == "C" and row["tilt_deg"] == 45.0
          and row["phase"] == "rotation" and row["trial"] == 2
          and row["rpm"] == 30.0 and abs(row["delta_g"] - 0.031) < 1e-9
          and row["flag"] == "" and row["t_ms"] == 182345, row)
    kind, row = cap.parse_line(
        "CSV,E,0.0,tap,0,1,,0.2000,0.2030,0.0030,lowflow,9000")
    check("trial empty rpm + flag", kind == "trial" and row["rpm"] is None
          and row["flag"] == "lowflow")


def test_parse_poll():
    kind, row = cap.parse_line("POLL,D,45.0,90,120400,0.4521,0")
    check("poll kind", kind == "poll")
    check("poll fields", row["rpm"] == 90.0 and row["stable"] == 0
          and abs(row["grams"] - 0.4521) < 1e-9, row)


def test_parse_dose():
    kind, row = cap.parse_line(
        "DOSE,1,1.0000,0.9993,-0.0007,ok,280.0,7.68,63,"
        "bulk:17;fine:10;tap:43,1830000")
    check("dose kind", kind == "dose")
    check("dose fields", row["n"] == 1 and row["status"] == "ok"
          and abs(row["error_g"] + 0.0007) < 1e-9 and row["taps"] == 63
          and row["phase_cycles"] == "bulk:17;fine:10;tap:43", row)
    # battery_version 2 rows -- every committed run is made of these --
    # carry no block, and predate Block H, so they are Block G.
    check("v2 dose row is block G", row["block"] == "G", row.get("block"))
    _, row = cap.parse_line(
        "DOSE,4,0.0500,0.0468,-0.0032,ok,61.0,0.42,9,"
        "fine:3;tap:19,1900000,H")
    check("v3 dose row carries its block", row["block"] == "H", row)
    check("v3 dose fields", row["n"] == 4
          and abs(row["target_g"] - 0.05) < 1e-9
          and abs(row["error_g"] + 0.0032) < 1e-9, row)
    check("dose row of the wrong width ignored",
          cap.parse_line("DOSE,1,1.0000,0.9993,-0.0007,ok,280.0") is None)


def test_parse_other():
    check("summary", cap.parse_line(
        "SUM,C,90.0,rotation,6,0.0450,0.0060,0.0024,0.0380,0.0530")[0]
        == "device_summary")
    check("meta", cap.parse_line("META,powder_id,salt")
          == ("meta", ("powder_id", "salt")))
    check("run end", cap.parse_line("RUN,END,ok") == ("run", ["END", "ok"]))
    check("prompt", cap.parse_line("PROMPT,empty the cup, then Enter")[1]
          == "empty the cup, then Enter")
    check("noise ignored", cap.parse_line("[battery] block C") is None)
    check("short row ignored", cap.parse_line("CSV,C,45.0") is None)


def test_normalize_powder_id():
    check("slugify", cap.normalize_powder_id("Brown Rice Flour")
          == "brown-rice-flour")
    check("pass-through", cap.normalize_powder_id("alsi10mg")
          == "alsi10mg")
    try:
        cap.normalize_powder_id("!bad!")
        check("reject invalid", False)
    except ValueError:
        check("reject invalid", True)


def test_summarize():
    trials = [
        {"block": "C", "tilt_deg": 45.0, "phase": "rotation",
         "delta_g": d, "flag": ""} for d in (0.03, 0.04, 0.05)
    ] + [
        {"block": "C", "tilt_deg": 0.0, "phase": "rotation",
         "delta_g": 0.0, "flag": "lowflow"},
    ]
    summary = cap.summarize(trials)
    by_key = {(r["block"], r["tilt_deg"], r["phase"]): r for r in summary}
    row = by_key[("C", 45.0, "rotation")]
    check("summarize stats", row["n"] == 3
          and abs(row["mean_g"] - 0.04) < 1e-9
          and abs(row["std_g"] - 0.01) < 1e-9, row)
    check("lowflow rows are data",
          by_key[("C", 0.0, "rotation")]["n"] == 1)


def test_dose_summary():
    doses = [
        {"n": 0, "error_g": 0.002, "elapsed_s": 100.0, "status": "ok"},
        {"n": 1, "error_g": -0.004, "elapsed_s": 200.0,
         "status": "overshoot"},
    ]
    agg = cap.dose_summary(doses)
    check("dose summary", agg["n"] == 2 and agg["ok"] == 1
          and abs(agg["mean_error_g"] + 0.001) < 1e-9
          and abs(agg["max_abs_error_g"] - 0.004) < 1e-9
          and abs(agg["mean_elapsed_s"] - 150.0) < 1e-9, agg)
    check("empty dose summary", cap.dose_summary([]) is None)


def test_dose_summary_by_target():
    """The Block G vs Block H comparison.

    Same absolute error at both targets must show as the same
    ``mean_error_g`` and a relative error that grows as the target
    shrinks -- that contrast is the entire point of Block H.
    """
    doses = (
        [{"n": i, "block": "H", "target_g": 0.050, "error_g": -0.004,
          "elapsed_s": 60.0, "status": "ok"} for i in range(3)]
        + [{"n": i + 3, "block": "H", "target_g": 0.200, "error_g": -0.004,
            "elapsed_s": 90.0, "status": "stalled"} for i in range(3)]
        + [{"n": i, "block": "G", "target_g": 1.000, "error_g": -0.004,
            "elapsed_s": 200.0, "status": "ok"} for i in range(3)]
    )
    rows = cap.dose_summary_by_target(doses)
    check("one row per target", len(rows) == 3, rows)
    check("ordered by target",
          [r["target_g"] for r in rows] == [0.050, 0.200, 1.000])
    check("blocks preserved", [r["block"] for r in rows] == ["H", "H", "G"])
    check("absolute error is flat",
          all(abs(r["mean_error_g"] + 0.004) < 1e-9 for r in rows), rows)
    check("relative error grows as the target shrinks",
          [r["mean_rel_error_pct"] for r in rows] == [-8.0, -2.0, -0.4],
          [r["mean_rel_error_pct"] for r in rows])
    check("statuses carried", rows[1]["statuses"] == ["stalled"]
          and rows[1]["ok"] == 0, rows[1])
    # A version 2 run has no block column; it must still aggregate.
    legacy = [{"n": i, "target_g": 1.000, "error_g": -0.004,
               "elapsed_s": 200.0, "status": "ok"} for i in range(3)]
    rows = cap.dose_summary_by_target(legacy)
    check("legacy doses group as block G",
          len(rows) == 1 and rows[0]["block"] == "G" and rows[0]["n"] == 3,
          rows)
    check("empty by-target summary",
          cap.dose_summary_by_target([]) is None)


def test_block_marker():
    check("block marker", cap.block_marker("[battery] block C") == "C")
    check("block marker trailing text",
          cap.block_marker("[battery] block G (three-phase doses)") == "G")
    check("block marker ignores skip note",
          cap.block_marker(
              "[battery] vibration driver unavailable -- skipping "
              "block F") is None)
    check("block marker ignores csv",
          cap.block_marker("CSV,C,45.0,rotation,2,360.0,30,0.1,0.13,"
                           "0.03,,182345") is None)
    # Only a bare letter starts a block.  A line that merely mentions a
    # block would append a second timeline entry mid-block, restarting
    # its clock and under-reporting how long the block actually took --
    # which is the whole reason the timeline exists.
    check("block marker ignores a within-block note",
          cap.block_marker("[battery] block H: skipping 0.0100 g") is None)
    check("block marker ignores a word that is not a letter",
          cap.block_marker("[battery] block target 0.0500 g") is None)


def test_format_elapsed():
    check("format elapsed under a minute", cap.format_elapsed(7.5) == "0:00:07")
    check("format elapsed minutes", cap.format_elapsed(119.4) == "0:01:59")
    # The sodium-alginate run: 48 min 43 s, nearly all of it block G.
    check("format elapsed run length", cap.format_elapsed(2923) == "0:48:43")
    check("format elapsed hours", cap.format_elapsed(3661) == "1:01:01")


def test_run_document_timeline():
    class Args(object):
        powder_id = "sodium-alginate"
        powder = "sodium alginate"
        operator = "swcharles"
        notes = ""
        batch = "food-safe-2026-08"
        qc_valid = True
        qc_verdict = "ok"
        preflight_json = None

    timeline = [{"block": "A", "started_utc": "2026-08-05T14:57:32+00:00",
                 "started_local": "2026-08-05 08:57:32 MDT",
                 "elapsed_s": 7.5},
                {"block": "G", "started_utc": "2026-08-05T15:04:07+00:00",
                 "started_local": "2026-08-05 09:04:07 MDT",
                 "elapsed_s": 402.0}]
    doc = cap.build_run_document(
        {}, [], [], [], [], [], "ok", Args(),
        "2026-08-05T14:57:25+00:00", "2026-08-05T15:46:08+00:00",
        elapsed_s=2923.0, timeline=timeline)
    check("doc carries elapsed", doc["elapsed_s"] == 2923.0)
    check("doc carries timeline", doc["block_timeline"] == timeline)
    check("timeline fields match csv header",
          set(cap.TIMELINE_FIELDS) == set(timeline[0]))
    # Older calls must keep working -- the run doc is written from a
    # couple of places and a partial capture has no timeline yet.
    bare = cap.build_run_document(
        {}, [], [], [], [], [], "capture-interrupted", Args(),
        "2026-08-05T14:57:25+00:00", "2026-08-05T15:00:00+00:00")
    check("timeline optional",
          bare["elapsed_s"] is None and bare["block_timeline"] == [])


def test_lab_local_clock():
    """The lab reads MDT; UTC stays canonical but must not be the only clock."""
    stamp = cap.local_stamp()
    check("local stamp looks like a wall clock",
          len(stamp) >= 19 and stamp[4] == "-" and stamp[13] == ":", stamp)

    class Args(object):
        powder_id = "calcium-lactate"
        powder = "calcium lactate"
        operator = "swcharles"
        notes = ""
        batch = "food-safe-2026-08"
        qc_valid = True
        qc_verdict = "ok"
        preflight_json = None
        started_local = "2026-08-05 14:00:02 MDT"
        ended_local = "2026-08-05 14:19:24 MDT"

    doc = cap.build_run_document(
        {}, [], [], [], [], [], "ok", Args(),
        "2026-08-05T20:00:02+00:00", "2026-08-05T20:19:24+00:00",
        elapsed_s=1162.0, timeline=[])
    check("doc carries lab-local start",
          doc["started_local"] == "2026-08-05 14:00:02 MDT")
    check("doc carries lab-local end",
          doc["ended_local"] == "2026-08-05 14:19:24 MDT")
    check("doc names the lab timezone", bool(doc["lab_timezone"]))
    # UTC must survive untouched -- it keys the run directory, the stream
    # anchors and the MongoDB documents.
    check("utc is unchanged",
          doc["started_utc"] == "2026-08-05T20:00:02+00:00")
    check("schema version bumped", doc["schema_version"] == 3)

    # A partial capture that never reached the end still has to build a
    # document; the local stamps are simply absent rather than fatal.
    class Bare(Args):
        started_local = None
        ended_local = None

    partial = cap.build_run_document(
        {}, [], [], [], [], [], "capture-interrupted", Bare(),
        "2026-08-05T20:00:02+00:00", "2026-08-05T20:05:00+00:00")
    check("missing local stamps are tolerated",
          partial["started_local"] is None and partial["ended_local"] is None)


def test_load_preflight():
    """--preflight-json must take a file path *or* the JSON itself.

    Passing the document inline is the natural reading of the flag name, and
    the 2026-08-21 AlSi10Mg run did exactly that: the crash landed after
    RUN,END,ok, so the run had to be rebuilt from the raw log and lost its
    block timeline.  Both spellings are supported now; this pins that.
    """
    inline = cap.load_preflight('{"verdict": "feed confirmed", "rev": 5}')
    check("inline JSON is parsed",
          inline == {"verdict": "feed confirmed", "rev": 5}, repr(inline))

    handle = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False)
    json.dump({"verdict": "conveying-slowly"}, handle)
    handle.close()
    try:
        check("a file path is parsed",
              cap.load_preflight(handle.name) == {"verdict": "conveying-slowly"})
        check("leading/trailing space in a path is tolerated",
              cap.load_preflight("  " + handle.name + "  ")
              == {"verdict": "conveying-slowly"})
    finally:
        os.unlink(handle.name)

    try:
        cap.load_preflight("/nonexistent/preflight.json")
        check("a bad path still raises", False, "no exception")
    except OSError:
        check("a bad path still raises", True)


def main():
    for test in (test_parse_trial, test_parse_poll, test_parse_dose,
                 test_parse_other, test_normalize_powder_id,
                 test_summarize, test_dose_summary,
                 test_dose_summary_by_target, test_block_marker,
                 test_format_elapsed, test_run_document_timeline,
                 test_lab_local_clock, test_load_preflight):
        print("--- {}".format(test.__name__))
        test()
    print()
    if FAILURES:
        print("FAILED: {}".format(", ".join(FAILURES)))
        return 1
    print("all capture tests passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
