"""CPython simulation tests for the battery pre-flight feed check.

Reuses the fake hardware from ``test_powder_battery`` and asserts the
three verdicts the check exists to distinguish:

- a feeding column          -> ``feed confirmed``
- a blocked delivery path    -> ``suspect-no-feed`` (rotation dead, taps alive)
- an empty/fully blocked one -> ``empty-or-blocked``

Run:  python3 hardware/test-module/firmware/sim/test_battery_preflight.py
"""

import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))                       # firmware modules
sys.path.insert(0, str(_HERE))                              # sibling tests

import battery_preflight as pre
from test_powder_battery import (
    Column, FakeScale, FakeServo, FakeStepper, FakeTap, VirtualClock,
)

_FAILURES = []


def check(name, ok, detail=""):
    print("{} {}{}".format("PASS" if ok else "FAIL", name,
                           "" if ok else "  <- {}".format(detail)))
    if not ok:
        _FAILURES.append(name)


class BlockedColumn(Column):
    """Delivery path blocked: the auger turns but conveys nothing.

    Taps still shake loose the fines already past the blockage -- the
    exact signature of the 2026-08-04 no-feed run.
    """

    def rotate(self, degrees):
        pass


class DeadColumn(BlockedColumn):
    """Blocked *and* nothing loose to shake out."""

    def __init__(self):
        super().__init__(tap_g=0.0)


def run_check(column, **kwargs):
    clock = VirtualClock()
    lines = []
    result = pre.check(
        FakeStepper(column, clock), FakeTap(column), FakeServo(column),
        FakeScale(column), log=lines.append, sleep_ms=clock.sleep_ms,
        **kwargs)
    return result, lines


def test_feeding_column():
    column = Column(g_per_rev=0.04)
    result, _ = run_check(column)
    check("feeding verdict", result["verdict"] == "feed confirmed",
          result["verdict"])
    check("feeding revolutions counted",
          result["rotation_rev_total"] == pre.REVS, result["rotation_rev_total"])
    check("feeding mass conveyed", result["rotation_delta_g"] > 0.02,
          result["rotation_delta_g"])
    check("feeding per-rev deltas all positive",
          all(d > 0 for d in result["rev_deltas"]), result["rev_deltas"])


def test_blocked_path_reads_as_no_feed():
    result, _ = run_check(BlockedColumn(tap_g=0.002))
    check("blocked verdict", result["verdict"] == "suspect-no-feed",
          result["verdict"])
    check("blocked rotation is zero", result["rotation_delta_g"] == 0.0,
          result["rotation_delta_g"])
    check("blocked taps still move mass", result["taps_delta_g"] > 0,
          result["taps_delta_g"])


def test_empty_column():
    result, _ = run_check(DeadColumn())
    check("empty verdict", result["verdict"] == "empty-or-blocked",
          result["verdict"])
    check("empty taps move nothing", result["taps_delta_g"] == 0.0,
          result["taps_delta_g"])


def test_geometry_and_settings():
    column = Column()
    clock = VirtualClock()
    servo = FakeServo(column)
    stepper = FakeStepper(column, clock)
    pre.check(stepper, FakeTap(column), servo, FakeScale(column),
              log=lambda *_: None, sleep_ms=clock.sleep_ms)
    check("tilt 90 deg -> plate 45 deg", servo.history[0] == 45.0,
          servo.history)
    check("auger speed set to 30 RPM", stepper.rpm == pre.RPM, stepper.rpm)
    check("total rotation is REVS x 360",
          stepper.total_deg == pre.REVS * 360.0, stepper.total_deg)


def test_cohesive_powder_still_feeds_vertically():
    """A genuinely cohesive powder must not be mistaken for a blockage.

    The check runs at tilt 90 deg precisely because that is where even
    cohesive powders convey -- so ``feed confirmed`` stays meaningful.
    """
    result, _ = run_check(Column(g_per_rev=0.01, cohesive=True))
    check("cohesive powder passes pre-flight",
          result["verdict"] == "feed confirmed", result["verdict"])


def main():
    for test in (test_feeding_column, test_blocked_path_reads_as_no_feed,
                 test_empty_column, test_geometry_and_settings,
                 test_cohesive_powder_still_feeds_vertically):
        test()
    print()
    if _FAILURES:
        print("{} check(s) failed: {}".format(len(_FAILURES),
                                              ", ".join(_FAILURES)))
        return 1
    print("all pre-flight checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
