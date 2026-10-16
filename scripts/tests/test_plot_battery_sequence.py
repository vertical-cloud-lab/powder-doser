#!/usr/bin/env python3
"""Checks for the block C sequence figure's shape classification.

The caption on that figure is the whole point of it -- it is what says
"this mean describes no revolution that actually happened" -- so pin the
classifier against the real per-revolution series from every run so far.
No hardware and no plotting; ``trend`` is pure.

Usage::

    python scripts/tests/test_plot_battery_sequence.py
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                os.pardir))

import plot_battery_sequence as seq  # noqa: E402

FAILURES = []


def check(name, condition, detail=""):
    if condition:
        print("PASS {} {}".format(name, detail))
    else:
        FAILURES.append(name)
        print("FAIL {} {}".format(name, detail))


def test_trend():
    # Carboxymethyl cellulose, tilt 90 deg: 39.0 mg then a collapse to
    # ~2 mg/rev.  Its 9.3 mg mean is an artefact of the first revolution.
    check("decaying", seq.trend([39.0, 7.4, 4.0, 1.8, 1.4, 2.5])
          == "decaying")
    # Same run, tilt 45 deg: flat, so the mean is a real feed factor.
    check("steady", seq.trend([26.2, 27.7, 28.7, 26.5, 21.8, 27.2])
          == "steady")
    # White rice flour pre-flight shape: the delivery section filling.
    check("charging", seq.trend([1.7, 23.3, 70.2, 50.3, 43.4, 48.0])
          == "charging")
    # Brown rice flour auger #2, tilt 0 deg: 13 of 18 revolutions across
    # the block were exactly 0.0000 g, the rest single clump releases.
    # "charging"/"decaying" here would describe where the clumps landed,
    # not the powder.
    check("intermittent", seq.trend([0.0, 0.5, 0.0, 0.0, 1.3, 0.0])
          == "intermittent")
    check("intermittent, clumps late",
          seq.trend([0.0, 0.0, 0.0, 0.0, 1.2, 1.4]) == "intermittent")
    # Brown rice flour auger #1: nothing cleared the balance at all.
    check("below resolution", seq.trend([0.0, 0.0, 0.0, 0.0, 0.0, 0.0])
          == "below resolution")
    check("below resolution, at the limit",
          seq.trend([0.1, 0.05, 0.0, 0.1, 0.0, 0.1]) == "below resolution")
    # Degenerate input must not raise.
    check("too short", seq.trend([1.0, 2.0]) is None)
    check("empty", seq.trend([]) is None)


def main():
    print("--- test_trend")
    test_trend()
    print()
    if FAILURES:
        print("FAILED: {}".format(", ".join(FAILURES)))
        return 1
    print("all sequence-figure checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
