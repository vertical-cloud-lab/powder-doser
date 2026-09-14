#!/usr/bin/env python3
"""Checks for scripts/plot_powder_repeats.py.

The failure mode this script has to avoid is manufacturing agreement:
quietly pooling a run whose own QC says its feed factor is a bound would
make the between-run spread look smaller than it is, and quietly dropping
a good run would make it look larger.  So the pooling rule, the
comparison verdict and the caption's honesty about what was dropped are
all pinned here.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import plot_powder_repeats as rep  # noqa: E402

FAILURES = []


def check(name, ok, detail=""):
    print("{} {} {}".format("PASS" if ok else "FAIL", name, detail))
    if not ok:
        FAILURES.append(name)


def summary(c0, c45, c90, e45=None, rsd=(10.0, 10.0, 10.0)):
    rows = [{"block": "C", "phase": "rotation", "tilt_deg": t,
             "mean_g": v / 1000.0, "rsd_pct": r}
            for t, v, r in zip(rep.TILTS, (c0, c45, c90), rsd)]
    if e45 is not None:
        rows.append({"block": "E", "phase": "refeed", "tilt_deg": 45.0,
                     "mean_g": e45 / 1000.0, "rsd_pct": 5.0})
    return rows


def doc(date, c0, c45, c90, e45=None, valid=True, verdict="ok", reason="",
        powder_id="salt"):
    return {"powder_id": powder_id, "started_utc": date + "T00:00:00Z",
            "host_summary": summary(c0, c45, c90, e45),
            "qc": {"valid_for_cross_powder_comparison": valid,
                   "verdict": verdict, "reason": reason}}


def test_pooling_rules():
    check("valid run pools", rep.pooled(doc("2026-08-12", 34, 175, 230, 162),
                                        {"valid_for_cross_powder_comparison": True}))
    excluded = {"valid_for_cross_powder_comparison": False,
                "verdict": "environment-stress-test"}
    check("excluded run does not pool",
          not rep.pooled(doc("2026-08-20", 50, 155, 208), excluded))
    bound = {"valid_for_cross_powder_comparison": True,
             "reason": "block C recorded as a lower bound"}
    check("a run whose QC calls its feed factor a bound does not pool",
          not rep.pooled(doc("2026-08-06", 6, 17, 25), bound))


def test_consistency_gate_catches_the_2026_08_06_run():
    """Blocks C and E disagreed 2.68x that day; 45.8/17.1 is outside 0.74-1.12."""
    bad = doc("2026-08-06", 5.6, 17.1, 24.9, e45=45.8)
    check("C/E disagreement is caught", rep.consistency_failed(bad))
    good = doc("2026-08-21", 38.0, 146.5, 265.2, e45=155.4)
    check("C/E agreement passes", not rep.consistency_failed(good))
    check("a run with no block E is not failed on missing data",
          not rep.consistency_failed(doc("2026-08-21", 38, 146, 265)))


def test_only_matching_powder_is_loaded(tmp="/tmp/_repeats_test"):
    import json
    os.makedirs(tmp, exist_ok=True)
    paths = []
    for i, (pid, date) in enumerate((("salt", "2026-08-12"),
                                     ("xanthan-gum", "2026-08-06"),
                                     ("salt", "2026-08-21"))):
        p = os.path.join(tmp, "run_{}.json".format(i))
        json.dump(doc(date, 34, 175, 230, 162, powder_id=pid), open(p, "w"))
        paths.append(p)
    runs = rep.load_runs("salt", paths)
    check("only the named powder is loaded", len(runs) == 2, len(runs))
    check("runs come back oldest first",
          [r["date"] for r in runs] == ["2026-08-12", "2026-08-21"])


def test_verdict_follows_the_comparison():
    between = {45.0: {"rsd": 9.0}, 90.0: {"rsd": 12.0}}
    check("between <= within reads as reassuring",
          "no larger than" in rep.headline(between, {45.0: 18.0, 90.0: 12.4}))
    check("between > within everywhere is called out",
          "understate" in rep.headline(between, {45.0: 2.0, 90.0: 3.0}))
    check("a mixed result is not overstated either way",
          "some tilts" in rep.headline(between, {45.0: 2.0, 90.0: 30.0}))
    check("no data does not assert a verdict",
          "not yet estimable" in rep.headline({}, {}))


def test_caption_names_what_was_dropped():
    runs = [{"date": "2026-08-06", "verdict": "ok", "pooled": False,
             "means": {}, "rsds": {}},
            {"date": "2026-08-21", "verdict": "ok", "pooled": True,
             "means": {}, "rsds": {}}]
    text = rep.caption(runs, {}, {})
    check("caption counts the pool", "1 of 2 runs pooled" in text, text)
    check("caption names the dropped run", "2026-08-06" in text, text)


def main():
    for test in (test_pooling_rules,
                 test_consistency_gate_catches_the_2026_08_06_run,
                 test_only_matching_powder_is_loaded,
                 test_verdict_follows_the_comparison,
                 test_caption_names_what_was_dropped):
        print("--- {}".format(test.__name__))
        test()
    print()
    if FAILURES:
        print("FAILED: {}".format(", ".join(FAILURES)))
        return 1
    print("all powder-repeat checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
