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


def taps_sem(*mean_sem_mg):
    """Block E tap rows carrying their own standard error."""
    return [{"block": "E", "phase": "tap", "tilt_deg": tilt,
             "mean_g": m / 1000.0, "sem_g": s / 1000.0}
            for tilt, (m, s) in zip((0.0, 45.0), mean_sem_mg)]


def doc_with_baseline(baseline_sd_mg, tap_rows):
    """A run document whose block A no-actuation scatter is known."""
    return {"host_summary": [{"block": "A", "phase": "baseline",
                              "tilt_deg": 45.0, "mean_g": 0.0,
                              "std_g": baseline_sd_mg / 1000.0}]
            + list(tap_rows)}


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


def test_tap_headline_respects_the_noise_floor():
    """A tap quantum smaller than the do-nothing scatter is not a quantum.

    Sodium sulfate (2026-08-20) averaged 9 mg per tap in a room whose eight
    no-actuation block A trials scattered over 23 mg.  The title read
    "tapping moves up to 9 mg per tap", which described the bench rather
    than the powder.
    """
    rows = taps_sem((7.90, 2.65), (9.34, 2.63))
    noisy = plot.tap_headline(rows, doc_with_baseline(22.69, rows))
    check("noisy room: quantum is not claimed", "not resolved" in noisy,
          noisy)
    check("noisy room: no figure is quoted", "mg per tap" not in noisy, noisy)
    quiet = plot.tap_headline(rows, doc_with_baseline(0.0, rows))
    check("quiet room: the same taps do read as a quantum",
          quiet == "tapping moves up to 9 mg per tap", quiet)
    # Calcium lactate and xanthan gum must keep their real quanta.
    cl = taps_sem((2.31, 0.29), (20.36, 1.01))
    check("calcium lactate keeps its quantum",
          plot.tap_headline(cl, doc_with_baseline(0.0, cl))
          == "tapping moves up to 20 mg per tap")
    # A tap swamped by its own scatter is not resolved either, even on a
    # quiet bench.
    noisy_tap = taps_sem((1.0, 0.2), (4.0, 6.0))
    check("a tap lost in its own scatter is not claimed",
          "not resolved" in plot.tap_headline(
              noisy_tap, doc_with_baseline(0.0, noisy_tap)),
          plot.tap_headline(noisy_tap, doc_with_baseline(0.0, noisy_tap)))
    # Sub-mg taps read as almost nothing on a quiet bench, where the
    # trials genuinely bound the quantum.  White rice flour's real block A
    # was 0.0000 g on every trial, which is what earns that wording.
    wrf = taps_sem((0.11, 0.08), (0.11, 0.07))
    check("a sub-mg tap on a quiet bench reads as almost nothing",
          plot.tap_headline(wrf, doc_with_baseline(0.0, wrf))
          == "tapping contributes almost nothing")
    # ...but not in a room with a 22 mg do-nothing scatter.  "Almost
    # nothing" is a claim about the powder too, and these trials cannot
    # support it: a real 15 mg quantum would have looked identical.
    check("the same sub-mg tap in a noisy room is not claimed either",
          "not resolved" in plot.tap_headline(
              wrf, doc_with_baseline(22.0, wrf)),
          plot.tap_headline(wrf, doc_with_baseline(22.0, wrf)))
    # Silicon (2026-08-20): taps averaged -3.5 mg against a 20 mg block A
    # spread.  A negative mean is not evidence of a small quantum.
    si = taps_sem((-3.73, 2.64), (-3.52, 2.35))
    check("a negative tap mean in a noisy room is not resolved",
          "not resolved" in plot.tap_headline(
              si, doc_with_baseline(20.19, si)),
          plot.tap_headline(si, doc_with_baseline(20.19, si)))
    # AlSi10Mg (2026-08-11): also a negative mean, but on a bench whose
    # block A was flat to the display resolution.  The materiality guard
    # keeps that reading as "almost nothing" rather than flipping every
    # quiet run with a slightly negative mean.
    al = taps_sem((-0.33, 0.21), (-0.04, 0.19))
    check("a negative tap mean on a quiet bench still reads as almost nothing",
          plot.tap_headline(al, doc_with_baseline(0.0, al))
          == "tapping contributes almost nothing",
          plot.tap_headline(al, doc_with_baseline(0.0, al)))
    # The one-argument form used elsewhere must keep working.
    check("no doc: falls back to mean and own error",
          plot.tap_headline(taps(2.31, 20.36))
          == "tapping moves up to 20 mg per tap")


def test_baseline_spread_is_read_from_block_a():
    rows = taps_sem((1.0, 0.1))
    check("block A std is reported in mg",
          abs(plot.baseline_spread_mg(doc_with_baseline(22.69, rows))
              - 22.69) < 1e-6)
    check("a run with no block A reports no spread",
          plot.baseline_spread_mg({"host_summary": []}) == 0.0)
    check("a missing summary does not raise",
          plot.baseline_spread_mg({}) == 0.0)


def main():
    for test in (test_tilt_headline, test_tap_headline, test_dose_headline,
                 test_tap_headline_respects_the_noise_floor,
                 test_baseline_spread_is_read_from_block_a):
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
