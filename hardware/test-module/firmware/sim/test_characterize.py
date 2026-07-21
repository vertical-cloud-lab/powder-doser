"""CPython simulation tests for ``characterize.py`` (issue #130).

Drives the exact ``Characterizer`` control flow that runs on the Pico
against a deterministic fake rig, and checks the property the whole
sweep exists for: the tap-phase deltas are *tap-only* -- the re-feed
rotations interleaved between taps are measured into their own rows and
never attributed to the tap.

Run from the repo root (no dependencies beyond the stdlib)::

    python hardware/test-module/firmware/sim/test_characterize.py

or via pytest.
"""

import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import characterize
from characterize import Characterizer, sample_stats


# ---------------------------------------------------------------------------
# Deterministic fake rig.  Physics model:
#   * one auger rotation moves GPR_BASE + GPR_PER_DEG * angle grams;
#   * a rotation also loads the tube lip with LIP_LOAD_G;
#   * each tap knocks half of the current lip charge into the cup, so
#     taps decay geometrically unless a rotation re-feeds the lip.
# ---------------------------------------------------------------------------

GPR_BASE = 0.050        # g per 360 deg at angle 0
GPR_PER_DEG = 0.0002    # extra g per 360 deg per servo degree
LIP_LOAD_G = 0.003      # lip charge after any rotation


class FakeSim:
    def __init__(self):
        self.mass = 0.0     # grams on the pan (relative to tare)
        self.lip = 0.0      # grams sitting on the tube lip
        self.angle = 0.0


class FakeReading:
    def __init__(self, grams):
        self.grams = grams
        self.stable = True
        self.overload = False
        self.unit = "g"


class FakeScale:
    def __init__(self, sim):
        self.sim = sim
        self.zero_count = 0

    def read_stable(self, timeout_ms=0):
        return FakeReading(round(self.sim.mass, 4))

    def zero(self):
        self.sim.mass = 0.0
        self.zero_count += 1


class FakeStepper:
    def __init__(self, sim):
        self.sim = sim
        self.total_deg = 0.0

    def rotate_degrees(self, deg):
        self.total_deg += deg
        gpr = GPR_BASE + GPR_PER_DEG * self.sim.angle
        self.sim.mass += gpr * deg / 360.0
        self.sim.lip = LIP_LOAD_G

    def enable(self, on=True):
        pass


class FakeTap:
    def __init__(self, sim):
        self.sim = sim

    def tap(self, count):
        for _ in range(count):
            knocked = self.sim.lip * 0.5
            self.sim.mass += knocked
            self.sim.lip -= knocked

    def _off(self):
        pass


class FakeServo:
    def __init__(self, sim):
        self.sim = sim

    def move_to(self, angle):
        self.sim.angle = angle


def _run_sweep(angles=(0, 45, 90), points=4, **overrides):
    sim = FakeSim()
    lines = []
    characterizer = Characterizer(
        FakeStepper(sim), FakeTap(sim), FakeServo(sim), FakeScale(sim),
        log=lines.append,
        sleep_ms=lambda ms: None,
        input_line=None,                 # unattended: prompts auto-continue
        angles_deg=list(angles),
        points_per_angle=points,
        baseline_reads=2,
        settle_ms=0, angle_settle_ms=0,
        **overrides)
    status = characterizer.run_all()
    return sim, lines, status


def _rows(lines, kind):
    return [line.split(",") for line in lines if line.startswith(kind + ",")]


def _trials(lines, angle, phase):
    out = []
    for row in _rows(lines, "CSV"):
        if float(row[1]) == angle and row[2] == phase:
            out.append(row)
    return out


def test_counts_and_structure():
    angles, points = (0, 45, 90), 4
    sim, lines, status = _run_sweep(angles, points)
    assert status == "ok"
    assert [r[1] for r in _rows(lines, "RUN")] == ["BEGIN", "END"]
    for angle in angles:
        assert len(_trials(lines, angle, "baseline")) == 2
        assert len(_trials(lines, angle, "rotation")) == points
        assert len(_trials(lines, angle, "refeed")) == points
        assert len(_trials(lines, angle, "tap")) == points
    # 4 SUM rows (baseline/rotation/refeed/tap) per angle.
    assert len(_rows(lines, "SUM")) == 4 * len(angles)
    # META rows carry the run parameters.
    meta = {r[1]: r[2] for r in _rows(lines, "META")}
    assert meta["points_per_angle"] == str(points)


def test_rotation_yield_tracks_angle():
    angles, points = (0, 45, 90), 4
    sim, lines, status = _run_sweep(angles, points)
    for angle in angles:
        expected = GPR_BASE + GPR_PER_DEG * angle
        deltas = [float(r[7]) for r in _trials(lines, angle, "rotation")]
        for delta in deltas:
            assert abs(delta - expected) < 2e-4, (angle, delta, expected)
        # refeed rotations are the same action -- poolable with rotation.
        for row in _trials(lines, angle, "refeed"):
            assert abs(float(row[7]) - expected) < 2e-4


def test_tap_deltas_exclude_refeed_mass():
    """The core accounting: tap rows measure the tap ONLY.

    With a re-feed before every tap the lip always holds LIP_LOAD_G, so
    every tap should knock exactly LIP_LOAD_G/2 -- NOT decay away, and
    NOT include the ~0.05 g the re-feed rotation moved.
    """
    sim, lines, status = _run_sweep(angles=(45,), points=5)
    taps = [float(r[7]) for r in _trials(lines, 45, "tap")]
    assert len(taps) == 5
    for delta in taps:
        assert abs(delta - LIP_LOAD_G / 2.0) < 2e-4, taps
    # Without interleaved re-feeds the same physics decays geometrically
    # -- proving the sweep design (not the fake) keeps the yield flat.
    sim2 = FakeSim()
    stepper2, tap2 = FakeStepper(sim2), FakeTap(sim2)
    stepper2.rotate_degrees(360)
    decayed = []
    for _ in range(5):
        before = sim2.mass
        tap2.tap(1)
        decayed.append(sim2.mass - before)
    assert decayed[0] > 4 * decayed[4]


def test_device_summary_matches_recomputation():
    sim, lines, status = _run_sweep(angles=(30,), points=6)
    deltas = [float(r[7]) for r in _trials(lines, 30, "rotation")]
    n, mean, std, sem, lo, hi = sample_stats(deltas)
    summary = [r for r in _rows(lines, "SUM")
               if float(r[1]) == 30 and r[2] == "rotation"][0]
    assert int(summary[3]) == n == 6
    assert abs(float(summary[4]) - mean) < 1e-4
    assert abs(float(summary[5]) - std) < 1e-4
    assert abs(float(summary[6]) - sem) < 1e-4
    assert abs(float(summary[7]) - lo) < 1e-4
    assert abs(float(summary[8]) - hi) < 1e-4
    # sem really is std/sqrt(n)
    assert abs(sem - std / math.sqrt(n)) < 1e-12


def test_baseline_is_quiet_on_ideal_scale():
    sim, lines, status = _run_sweep(angles=(60,), points=2)
    for row in _trials(lines, 60, "baseline"):
        assert abs(float(row[7])) < 1e-9


def test_stall_prompts_and_keep():
    """An empty hopper triggers the refill prompt; 'keep' accepts low flow."""
    sim = FakeSim()
    lines = []
    # rotation phase: Enter (discard+retry) then 'keep'; tap phase's
    # re-feed also stalls once -> 'keep' taps anyway.
    answers = iter(["", "keep", "keep"])

    class EmptyStepper(FakeStepper):
        def rotate_degrees(self, deg):
            self.total_deg += deg   # moves nothing: hopper empty

    characterizer = Characterizer(
        EmptyStepper(sim), FakeTap(sim), FakeServo(sim), FakeScale(sim),
        log=lines.append, sleep_ms=lambda ms: None,
        input_line=lambda: next(answers),
        angles_deg=[45], points_per_angle=3, baseline_reads=1,
        settle_ms=0, angle_settle_ms=0,
        prompt_each_angle=False, max_stalls=3)
    status = characterizer.run_all()
    assert status == "ok"
    prompts = [line for line in lines if line.startswith("PROMPT,")]
    # Rotation: "" (discard + retry) then "keep"; re-feed: "keep".
    assert len(prompts) == 3
    rot = _trials(lines, 45, "rotation")
    flagged = [r for r in rot if r[8] == "lowflow"]
    assert len(rot) == 6 and len(flagged) == 6
    summary = [r for r in _rows(lines, "SUM")
               if float(r[1]) == 45 and r[2] == "rotation"][0]
    assert int(summary[3]) == 3    # 'keep' counted the second streak


def main():
    tests = [(name, fn) for name, fn in sorted(globals().items())
             if name.startswith("test_") and callable(fn)]
    for name, fn in tests:
        fn()
        print("PASS {}".format(name))
    print("{} tests passed".format(len(tests)))


if __name__ == "__main__":
    main()
