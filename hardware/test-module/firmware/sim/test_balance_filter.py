"""Simulation tests for environment-artifact rejection (issue #116).

Two layers:

* unit tests of ``balance_filter`` -- step detection, drift correction,
  uncertainty, and the "wait for a quiet window" loop;
* integration tests that run the real ``powder_battery.Battery`` loop
  against a balance model reproducing the 2026-08-20 bare-pan survey
  (0.1 mg jitter, ~5 mg/min creep, occasional ~100 mg shock steps) and
  a balance that never asserts ``ST`` -- the condition that aborted
  three sessions with ``scale-unreadable``.

Run: python3 hardware/test-module/firmware/sim/test_balance_filter.py
"""

import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))
sys.path.insert(0, str(_HERE.parents[3] / "scripts"))

import balance_filter as bf
import powder_battery as pb
import powder_battery_capture as cap

FAILURES = []


def check(label, ok, detail=""):
    print("{} {} {}".format("PASS" if ok else "FAIL", label, detail))
    if not ok:
        FAILURES.append(label)


def approx(a, b, tol):
    return abs(a - b) <= tol


# ---------------------------------------------------------------------------
# Fakes
# ---------------------------------------------------------------------------

class Clock:
    def __init__(self):
        self.t_ms = 0.0

    def sleep_ms(self, ms):
        self.t_ms += ms

    def ticks_ms(self):
        return int(self.t_ms)


class Reading:
    def __init__(self, grams, stable=False, overload=False):
        self.grams = grams
        self.stable = stable
        self.overload = overload
        self.unit = "g"


class NoisyScale:
    """A balance in a working lab.

    Reproduces the three effects the survey separated: deterministic
    zig-zag jitter at the display resolution, a smooth creep, and step
    shocks scheduled at fixed times so the test stays reproducible
    without ``random`` (which MicroPython builds may not ship).
    """

    def __init__(self, column, clock, creep_g_per_s=0.0, jitter_g=0.0001,
                 shocks=(), never_stable=True):
        self.column = column
        self.clock = clock
        self.creep_g_per_s = creep_g_per_s
        self.jitter_g = jitter_g
        self.shocks = list(shocks)          # (t_ms, step_g)
        self.never_stable = never_stable
        self.tare = 0.0
        self.t0_ms = clock.ticks_ms()
        self._i = 0
        self.reads = 0

    def _artifact_g(self):
        t_s = (self.clock.ticks_ms() - self.t0_ms) / 1000.0
        offset = self.creep_g_per_s * t_s
        for t_ms, step in self.shocks:
            if self.clock.ticks_ms() >= t_ms:
                offset += step
        return offset

    def _value(self):
        self._i += 1
        jitter = self.jitter_g * (1 if self._i % 2 else -1)
        return self.column.pan_g - self.tare + self._artifact_g() + jitter

    def zero(self):
        self.tare = self.column.pan_g + self._artifact_g()

    def read(self):
        self.reads += 1
        self.clock.sleep_ms(30)             # a real Q round trip
        return Reading(self._value(),
                       stable=not self.never_stable)

    def read_stable(self, timeout_ms=10000):
        if self.never_stable:
            self.clock.sleep_ms(timeout_ms)
            return Reading(self._value(), stable=False)
        return Reading(self._value(), stable=True)


class SilentScale:
    def zero(self):
        pass

    def read(self):
        return None

    def read_stable(self, timeout_ms=10000):
        return None


class Column:
    def __init__(self, g_per_rev=0.030):
        self.pan_g = 0.0
        self.g_per_rev = g_per_rev
        self.plate_deg = 0.0

    def rotate(self, degrees):
        self.pan_g += degrees / 360.0 * self.g_per_rev


class Stepper:
    def __init__(self, column, clock):
        self.column = column
        self.clock = clock
        self.rpm = 30.0
        self.run_rpm = 0.0

    def set_speed(self, rpm):
        self.rpm = rpm

    def rotate_degrees(self, deg):
        self.clock.sleep_ms(int(deg / 360.0 / self.rpm * 60000))
        self.column.rotate(deg)

    def run_at_rpm(self, rpm):
        self.run_rpm = rpm

    def keep_alive(self):
        pass

    def stop(self):
        self.run_rpm = 0.0


class Tap:
    def __init__(self, column, clock):
        self.column = column
        self.clock = clock
        self.count = 0

    def tap(self, count, on_ms, off_ms):
        self.count += count
        self.clock.sleep_ms(count * (on_ms + off_ms))
        self.column.pan_g += count * 0.0005


class Servo:
    def __init__(self, column):
        self.column = column
        self.moves = []

    def move_to(self, plate_deg):
        self.moves.append(plate_deg)
        self.column.plate_deg = plate_deg


def make_samples(values, start_ms=0, step_ms=400, stable=False):
    return [(start_ms + i * step_ms, v, stable)
            for i, v in enumerate(values)]


# ---------------------------------------------------------------------------
# Unit tests
# ---------------------------------------------------------------------------

def test_bracket_fits_drift():
    # +2 mg per 400 ms sample = 5 mg/s creep, no noise.
    b = bf.Bracket(make_samples([0.000, 0.002, 0.004, 0.006, 0.008, 0.010]))
    check("slope recovered", approx(b.slope_g_per_s, 0.005, 1e-9),
          b.slope_g_per_s)
    check("clean fit has no residual", b.resid_rms_g < 1e-9, b.resid_rms_g)
    check("no false shock", not b.shocked)
    check("extrapolates forward",
          approx(b.value_at(4000), 0.020, 1e-9), b.value_at(4000))
    check("settled", not b.unsettled)


def test_step_detected_and_removed():
    # A 100 mg step lands between samples 2 and 3; the underlying series
    # is otherwise flat.  A bracket is actuator-gated, so this cannot be
    # powder.
    b = bf.Bracket(make_samples([0.000, 0.000, 0.100, 0.100, 0.100, 0.100]))
    check("one step found", len(b.steps) == 1, b.steps)
    check("step size", approx(b.step_total_g, 0.100, 1e-9), b.step_total_g)
    check("cleaned series flat",
          max(b.clean_g) - min(b.clean_g) < 1e-9)
    check("slope not polluted by the step",
          abs(b.slope_g_per_s) < 1e-9, b.slope_g_per_s)
    check("flagged as shock", b.quality() == "shock", b.quality())


def test_jitter_is_not_a_shock():
    b = bf.Bracket(make_samples(
        [0.0000, 0.0001, -0.0001, 0.0001, 0.0000, -0.0001]))
    check("jitter leaves no steps", not b.shocked, b.steps)
    check("jitter is settled", not b.unsettled, b.resid_rms_g)


def test_delta_removes_creep():
    # 5 mg/s creep across a 4 s action would fake +20 mg of powder.
    before = bf.Bracket(make_samples(
        [0.000, 0.002, 0.004, 0.006, 0.008, 0.010], start_ms=0))
    after = bf.Bracket(make_samples(
        [0.050, 0.052, 0.054, 0.056, 0.058, 0.060], start_ms=6000))
    d = bf.Delta(before, after)
    check("drift-corrected delta is the true 20 mg",
          approx(d.delta_g, 0.020, 1e-6), d.delta_g)
    check("drift reported", approx(d.drift_g, 0.030, 1e-6), d.drift_g)
    check("corrected flag set", d.drift_corrected)
    raw = after.raw_g[0] - before.raw_g[-1]
    check("uncorrected would have been wrong",
          abs(raw - 0.020) > 0.015, raw)
    check("quality ok", d.quality() == "ok", d.quality())


def test_delta_reports_uncertainty():
    before = bf.Bracket(make_samples(
        [0.0000, 0.0003, -0.0002, 0.0002, 0.0000, 0.0001]))
    after = bf.Bracket(make_samples(
        [0.0300, 0.0302, 0.0299, 0.0301, 0.0300, 0.0301], start_ms=6000))
    d = bf.Delta(before, after)
    check("sigma positive", d.sigma_g > 0, d.sigma_g)
    check("sigma is sub-mg for a quiet pair", d.sigma_g < 0.001, d.sigma_g)
    check("delta about 30 mg", approx(d.delta_g, 0.030, 0.002), d.delta_g)


def test_long_gap_disables_extrapolation():
    before = bf.Bracket(make_samples([0.0, 0.002, 0.004, 0.006, 0.008, 0.01]))
    after = bf.Bracket(make_samples([1.0, 1.0, 1.0, 1.0, 1.0, 1.0],
                                    start_ms=600000))
    d = bf.Delta(before, after)
    check("no extrapolation across a 10 min gap", not d.drift_corrected)
    check("flagged as drift", d.quality() == "drift", d.quality())


def test_collect_and_quiet_bracket():
    clock = Clock()
    column = Column()
    scale = NoisyScale(column, clock, creep_g_per_s=0.00008,
                       shocks=[(1000, 0.10)])
    b, attempts, quiet = bf.quiet_bracket(
        scale, tries=6, sleep_ms=clock.sleep_ms, ticks_ms=clock.ticks_ms)
    check("a quiet window is eventually found", quiet, attempts)
    check("the kept bracket is unshocked", not b.shocked)
    check("more than one attempt was needed", attempts > 1, attempts)


def test_silent_balance_still_raises():
    try:
        bf.collect(SilentScale(), n=3, interval_ms=1,
                   sleep_ms=lambda ms: None, ticks_ms=lambda: 0)
    except bf.BalanceSilent:
        check("silent balance raises", True)
        return
    check("silent balance raises", False)


def test_overload_is_not_treated_as_data():
    class OL:
        def read(self):
            return Reading(None, overload=True)
    try:
        bf.collect(OL(), n=3, interval_ms=1, sleep_ms=lambda ms: None,
                   ticks_ms=lambda: 0)
    except bf.BalanceSilent:
        check("overload raises rather than reading 0", True)
        return
    check("overload raises rather than reading 0", False)


def test_error_vs_duration():
    # Flat for 10 s, then a 100 mg step: short measurements are clean,
    # long ones straddle the step.  This is the survey's headline table.
    samples = make_samples([0.0] * 25 + [0.1] * 25, step_ms=400)
    table = bf.error_vs_duration(samples, [1, 2, 16])
    check("short window is clean", table[1]["median_g"] < 1e-9, table[1])
    check("long window sees the step", table[16]["max_g"] >= 0.099,
          table[16])


# ---------------------------------------------------------------------------
# Integration: the real Battery loop
# ---------------------------------------------------------------------------

def run_battery(scale, column, clock, blocks="C", **kw):
    lines = []
    stepper = Stepper(column, clock)
    tap = Tap(column, clock)
    servo = Servo(column)
    battery = pb.Battery(
        stepper, tap, servo, scale, log=lines.append,
        sleep_ms=clock.sleep_ms, ticks_ms=clock.ticks_ms,
        attended=False, blocks=blocks, powder_id="sim",
        rotation_trials=kw.pop("rotation_trials", 4),
        tilts_deg=kw.pop("tilts_deg", [45.0]), **kw)
    status = battery.run_all()
    return status, lines, battery


def parse_trials(lines):
    out = []
    for line in lines:
        parsed = cap.parse_line(line)
        if parsed and parsed[0] == "trial":
            out.append(parsed[1])
    return out


def test_creep_does_not_inflate_yield():
    """A creeping zero must not be read as powder."""
    clock = Clock()
    column = Column(g_per_rev=0.030)
    # 5 mg/min creep, the survey's rate.
    scale = NoisyScale(column, clock, creep_g_per_s=0.005 / 60.0)
    status, lines, battery = run_battery(scale, column, clock)
    trials = [t for t in parse_trials(lines) if t["phase"] == "rotation"]
    check("run completed", status == "ok", status)
    check("four rotations recorded", len(trials) == 4, len(trials))
    mean = sum(t["delta_g"] for t in trials) / len(trials)
    check("mean yield within 1 mg of truth",
          approx(mean, 0.030, 0.001), mean)
    check("every trial carries a sigma",
          all(t.get("sigma_g") is not None for t in trials))
    check("drift was actually corrected",
          any(abs(t["drift_g"]) > 0 for t in trials),
          [t["drift_g"] for t in trials])


def test_shock_is_rejected_not_measured():
    """A 100 mg bench knock must not become 100 mg of powder."""
    clock = Clock()
    column = Column(g_per_rev=0.030)
    scale = NoisyScale(column, clock, shocks=[(9000, 0.100)])
    status, lines, battery = run_battery(scale, column, clock)
    trials = [t for t in parse_trials(lines) if t["phase"] == "rotation"]
    worst = max(abs(t["delta_g"] - 0.030) for t in trials)
    check("no trial is off by anything like the 100 mg shock",
          worst < 0.010, worst)
    check("the shock was counted", battery.env["shock_events"] >= 1,
          battery.env)
    flagged = [t for t in trials if t.get("quality") != "ok"]
    check("shock is visible in the data as a flag or a retry",
          bool(flagged) or battery.env["retries"] >= 1,
          (len(flagged), battery.env["retries"]))


def test_disturbed_trial_is_remeasured():
    clock = Clock()
    column = Column(g_per_rev=0.030)
    # Shock scheduled to land inside an *after* bracket.
    scale = NoisyScale(column, clock, shocks=[(9000, 0.080)])
    status, lines, battery = run_battery(scale, column, clock,
                                         max_trial_retries=2)
    retries = [cap.parse_line(l)[1] for l in lines
               if cap.parse_line(l) and cap.parse_line(l)[0] == "retry"]
    check("the disturbed trial was retried", battery.env["retries"] >= 1,
          battery.env["retries"])
    check("retry rows are emitted, not swallowed",
          len(retries) == battery.env["retries"],
          (len(retries), battery.env["retries"]))
    check("the discarded attempt is auditable",
          all(r["reason"] and r["shock_g"] is not None for r in retries),
          retries)
    trials = [t for t in parse_trials(lines) if t["phase"] == "rotation"]
    check("all trials still recorded after retries", len(trials) == 4,
          len(trials))
    check("retried trials report their retry count",
          all(t.get("retries") is not None for t in trials))


def test_runs_when_balance_never_reports_stable():
    """The 2026-08-20 regression: no ``ST`` frame must not abort a run."""
    clock = Clock()
    column = Column(g_per_rev=0.030)
    scale = NoisyScale(column, clock, never_stable=True)
    status, lines, battery = run_battery(scale, column, clock, blocks="ABC")
    trials = parse_trials(lines)
    check("run completes with no stable frame ever", status == "ok", status)
    check("rotation trials still measured",
          len([t for t in trials if t["phase"] == "rotation"]) == 4)
    prompts = [cap.parse_line(l)[1] for l in lines
               if cap.parse_line(l) and cap.parse_line(l)[0] == "prompt"]
    check("no scale-failure prompt was raised",
          scale.reads > 0 and not any("scale" in p for p in prompts),
          prompts)


def test_environment_lands_in_the_run_document():
    clock = Clock()
    column = Column(g_per_rev=0.030)
    scale = NoisyScale(column, clock, creep_g_per_s=0.0001,
                       shocks=[(9000, 0.05)])
    status, lines, battery = run_battery(scale, column, clock)
    meta, trials, retries = {}, [], []
    for line in lines:
        parsed = cap.parse_line(line)
        if not parsed:
            continue
        kind, payload = parsed
        if kind == "meta":
            meta[payload[0]] = payload[1]
        elif kind == "trial":
            trials.append(payload)
        elif kind == "retry":
            retries.append(payload)
    check("device reports env META rows",
          any(k.startswith("env.") for k in meta), sorted(meta)[:4])
    env = cap.environment_summary(meta, trials, retries)
    check("host builds an environment block", env is not None)
    check("environment records the artifact rate",
          env["shock_events"] >= 0 and "quality_counts" in env, env)
    check("environment carries the device counters",
          "device" in env and "shock_events" in env["device"], env.get("device"))
    check("median sigma reported", env["median_sigma_g"] is not None)


def test_version_1_rows_still_parse():
    v1 = "CSV,C,45.0,rotation,0,360.0,30,0.0000,0.0300,0.0300,,1234"
    kind, row = cap.parse_line(v1)
    check("battery_version 1 rows still parse", kind == "trial")
    check("v1 rows carry no quality columns", "quality" not in row)
    check("v1 environment summary is empty",
          cap.environment_summary({}, [row], []) is None)


def main():
    for fn in (test_bracket_fits_drift, test_step_detected_and_removed,
               test_jitter_is_not_a_shock, test_delta_removes_creep,
               test_delta_reports_uncertainty,
               test_long_gap_disables_extrapolation,
               test_collect_and_quiet_bracket,
               test_silent_balance_still_raises,
               test_overload_is_not_treated_as_data,
               test_error_vs_duration,
               test_creep_does_not_inflate_yield,
               test_shock_is_rejected_not_measured,
               test_disturbed_trial_is_remeasured,
               test_runs_when_balance_never_reports_stable,
               test_environment_lands_in_the_run_document,
               test_version_1_rows_still_parse):
        print("--- {}".format(fn.__name__))
        fn()
    print()
    if FAILURES:
        print("FAILED: " + ", ".join(FAILURES))
        return 1
    print("all balance-filter checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
