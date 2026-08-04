"""Unit tests for the pure functions in powder_battery_capture.py.

Run:  python3 scripts/tests/test_powder_battery_capture.py
"""

import sys
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


def main():
    for test in (test_parse_trial, test_parse_poll, test_parse_dose,
                 test_parse_other, test_normalize_powder_id,
                 test_summarize, test_dose_summary):
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
