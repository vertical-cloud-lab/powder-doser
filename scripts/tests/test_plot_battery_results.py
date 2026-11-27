"""Unit tests for the data-driven panel titles in plot_battery_results.py.

The panel titles used to be fixed strings describing whatever the first
few powders did.  By the 2026-08-05 calcium lactate run two of them were
false -- it moves ~20 mg per tap and its doses stall in the tap phase,
where the hard-coded titles claimed tapping "contributes almost nothing"
and that doses "run out of fine-phase budget".  These tests pin the
titles to the data so they cannot silently go stale again.

Run:  python3 scripts/tests/test_plot_battery_results.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import plot_battery_results as plot

FAILURES = []


def check(name, cond, detail=""):
    status = "PASS" if cond else "FAIL"
    print("{:4} {} {}".format(status, name, detail if not cond else ""))
    if not cond:
        FAILURES.append(name)


def rows(*means_mg):
    """Block C summary rows at tilt 0 / 45 / 90, means given in mg."""
    return [{"tilt_deg": tilt, "mean_g": mg / 1000.0}
            for tilt, mg in zip((0.0, 45.0, 90.0), means_mg)]


def taps(*means_mg):
    return [{"tilt_deg": tilt, "mean_g": mg / 1000.0}
            for tilt, mg in zip((0.0, 45.0), means_mg)]


def dose(status, phase_cycles):
    return {"status": status, "phase_cycles": phase_cycles}


def test_tilt_headline():
    # White rice flour: 3.75 -> 12.78 -> 37.15 mg/rev, still climbing.
    check("tilt rises", plot.tilt_headline(rows(3.75, 12.78, 37.15))
          == "feed factor rises with tilt")
    # Sodium alginate and calcium lactate both flatten off above 45 deg.
    check("tilt saturates",
          plot.tilt_headline(rows(0.75, 9.58, 10.87))
          == "feed factor rises with tilt, saturating above 45°")
    check("tilt saturates (calcium lactate)",
          plot.tilt_headline(rows(47.3, 198.3, 232.2))
          == "feed factor rises with tilt, saturating above 45°")
    # Brown rice flour auger #2: flat within its own scatter, and the
    # trend is slightly *downward*, so "rises" would be plain wrong.
    check("tilt flat", plot.tilt_headline(rows(0.30, 0.25, 0.20))
          == "feed factor is flat across tilt")
    # Carboxymethyl cellulose: 2.6 -> 26.3 -> 9.3 mg/rev.  The peak is
    # at 45 deg and 90 deg is nearly 3x worse, so neither "rises" nor
    # "saturating" is true -- the one-sided saturation test used to call
    # this one "saturating above 45 deg", inverting the result.
    check("tilt peaks mid", plot.tilt_headline(rows(2.63, 26.32, 9.35))
          == "feed factor peaks at 45° and falls above it")
    # A genuine monotonic fall is its own case, not a peak.
    check("tilt falls", plot.tilt_headline(rows(40.0, 12.0, 3.0))
          == "feed factor falls with tilt")
    # Degenerate inputs must not raise or divide by zero.
    check("tilt all zero", plot.tilt_headline(rows(0.0, 0.0, 0.0))
          == "feed factor vs tilt")
    check("tilt empty", plot.tilt_headline([]) == "feed factor vs tilt")


def test_tap_headline():
    check("tap negligible", plot.tap_headline(taps(0.09, 0.11))
          == "tapping contributes almost nothing")
    check("tap real", plot.tap_headline(taps(2.31, 20.36))
          == "tapping moves up to 20 mg per tap")
    # The peak is what matters, not the last tilt measured.
    check("tap uses peak", plot.tap_headline(taps(20.36, 2.31))
          == "tapping moves up to 20 mg per tap")
    check("tap empty", plot.tap_headline([])
          == "tapping contributes almost nothing")


def test_dose_headline():
    check("dose converged",
          plot.dose_headline([dose("ok", "bulk:9;fine:12")] * 3)
          == "three-phase doses converge within tolerance")
    check("dose cycle budget",
          plot.dose_headline([dose("cycle-budget", "bulk:51;fine:200")] * 3)
          == "three-phase doses run out of fine-phase budget")
    # Calcium lactate: reaches phase 3 and stalls there.
    check("dose stalls in tap",
          plot.dose_headline([dose("stalled", "bulk:13;fine:16;tap:83")] * 3)
          == "three-phase doses stall in the tap phase")
    # Brown rice flour: never leaves bulk.
    check("dose stalls in bulk",
          plot.dose_headline([dose("stalled", "bulk:14")] * 3)
          == "three-phase doses stall in the bulk phase")
    # Doses that stall in different phases get a neutral summary rather
    # than a claim about a phase only some of them reached.
    check("dose stalls inconsistently",
          plot.dose_headline([dose("stalled", "bulk:14"),
                              dose("stalled", "bulk:13;fine:16;tap:83"),
                              dose("stalled", "bulk:14")])
          == "three-phase doses stall short of the target")
    check("dose mixed statuses",
          plot.dose_headline([dose("ok", "bulk:9;fine:12"),
                              dose("stalled", "bulk:14")])
          == "three-phase doses vs the target")
    check("dose empty", plot.dose_headline([]) == "no closed-loop doses")


def main():
    for test in (test_tilt_headline, test_tap_headline, test_dose_headline):
        print("--- {}".format(test.__name__))
        test()
    print()
    if FAILURES:
        print("FAILED: {}".format(", ".join(FAILURES)))
        return 1
    print("all plot title checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
