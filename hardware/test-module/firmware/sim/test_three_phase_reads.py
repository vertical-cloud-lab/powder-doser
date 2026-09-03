"""CPython simulation tests for the three-phase doser's balance reads.

Blocks G and H both dose through ``main_three_phase.ThreePhaseDoser``.
Until 2026-09-03 it read the balance with ``read_stable()``, which waits
for the A&D to assert ``ST`` and returns ``None`` otherwise.  On the
first two Block H hardware runs that abandoned four of six doses as
``scale-error`` and turned a silently-refused tare into two phantom
"overshoots" of 7.5393 g and 1.5410 g -- mass the auger never dispensed,
because it never turned.

These tests drive the real ``ThreePhaseDoser`` against a balance that
reproduces each of those bench conditions.  ``config`` and ``tic`` live
only on the Pico, so they are stubbed before the import; nothing else
about the module under test is faked.

Run:  python3 hardware/test-module/firmware/sim/test_three_phase_reads.py
"""

import sys
import types
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))          # firmware modules


# --- stub the Pico-only modules main_three_phase imports ------------------

_config = types.ModuleType("config")
for _k, _v in (
        ("SCALE_UART_ID", 0), ("PIN_SCALE_TX", 12), ("PIN_SCALE_RX", 13),
        ("SCALE_BAUD", 19200), ("SCALE_BITS", 8), ("SCALE_PARITY", 0),
        ("SCALE_STOP", 1), ("SCALE_RESPONSE_TIMEOUT_MS", 1000),
        ("SCALE_STABLE_TIMEOUT_MS", 10000), ("STEPPER_SPEED_RPM", 30.0),
        ("STEPPER_MICROSTEPS", 8), ("STEPPER_FULL_STEPS_REV", 200),
        ("STEPPER_ACCEL_REV_PER_S2", 2.0), ("STEPPER_DISPENSE_DEG", 360.0),
        ("TAP_ON_MS", 60), ("TAP_OFF_MS", 150), ("TAP_PWM_DUTY", 40000),
        ("TAP_COUNT", 1), ("SERVO_SPEED_DEG_PER_S", 60.0),
        ("SERVO_PRESETS", {"horizontal": 0, "vertical": 90}),
        ("PIN_SERVO_A", 14), ("PIN_SERVO_B", 15),
        ("PIN_TAP", 16), ("TIC_UART_ID", 1),
        ("PIN_TIC_TX", 4), ("PIN_TIC_RX", 5), ("TIC_BAUD", 9600),
        ("TIC_DEVICE_NUMBER", None)):
    setattr(_config, _k, _v)
sys.modules.setdefault("config", _config)

_tic = types.ModuleType("tic")


class _TicSerial:                                  # never instantiated here
    def __init__(self, *a, **k):
        raise RuntimeError("sim tests do not touch the Tic")


_tic.TicSerial = _TicSerial
_tic.TicStepper = _TicSerial
sys.modules.setdefault("tic", _tic)

import main_three_phase as m3p                                       # noqa: E402


# ---------------------------------------------------------------------------
# Fakes
# ---------------------------------------------------------------------------

class VirtualClock:
    def __init__(self):
        self.t = 0.0

    def sleep_ms(self, ms):
        self.t += ms / 1000.0

    def time(self):
        return self.t


class Reading:
    def __init__(self, grams, stable):
        self.grams = grams
        self.stable = stable
        self.overload = False
        self.unit = "g"


class BenchScale:
    """A balance with the failure modes seen on the bench.

    ``stable_frames`` False reproduces 2026-09-03: the A&D reported 97 %
    stable at rest and 0-2 % the moment the rig actuated, so
    ``read_stable`` returns ``None`` on essentially every call.

    ``tare_works`` False reproduces the silently-refused tare -- ``zero()``
    is accepted over the wire and changes nothing.

    ``drift_g_per_s`` reproduces the new fume hood's smooth ramp
    (-1.8 to -3.6 mg/min measured on 2026-09-03), and ``jitter_g`` the
    sample-to-sample noise.
    """

    def __init__(self, column, clock, stable_frames=True, tare_works=True,
                 drift_g_per_s=0.0, jitter_g=0.0, silent=False,
                 quiet_after_zero_s=0.0):
        self.column = column
        self.clock = clock
        self.stable_frames = stable_frames
        self.tare_works = tare_works
        self.drift_g_per_s = drift_g_per_s
        self.jitter_g = jitter_g
        self.silent = silent
        self.quiet_after_zero_s = quiet_after_zero_s
        self.quiet_until = 0.0
        self.tare = 0.0
        self.reads = 0
        self.stable_reads = 0
        self.silent_reads = 0
        self.zeroes = 0

    def _quiet(self):
        """The A&D answers nothing for a while after a tare command."""
        if self.clock.time() < self.quiet_until:
            self.silent_reads += 1
            return True
        return False

    def _displayed(self):
        drift = self.drift_g_per_s * self.clock.time()
        # Deterministic alternating jitter: averages out over a bracket,
        # which is exactly the property the bracket read relies on.
        self.reads += 1
        wobble = self.jitter_g * (1 if self.reads % 2 else -1)
        return self.column.pan_g - self.tare + drift + wobble

    def zero(self):
        self.zeroes += 1
        self.quiet_until = self.clock.time() + self.quiet_after_zero_s
        if self.tare_works:
            self.tare = self.column.pan_g + self.drift_g_per_s * \
                self.clock.time()

    def read(self):
        if self.silent or self._quiet():
            return None
        return Reading(self._displayed(), self.stable_frames)

    def read_stable(self, timeout_ms=0):
        self.stable_reads += 1
        if self.silent or not self.stable_frames:
            return None
        return Reading(self._displayed(), True)


class Column:
    """Powder that arrives when the auger turns or the solenoid fires."""

    def __init__(self, g_per_rev=0.230, tap_g=0.003, start_pan_g=0.0):
        self.pan_g = start_pan_g
        self.g_per_rev = g_per_rev
        self.tap_g = tap_g

    def rotate(self, degrees):
        self.pan_g += degrees / 360.0 * self.g_per_rev

    def tap(self, count):
        self.pan_g += count * self.tap_g


class FakeStepper:
    def __init__(self, column, clock):
        self.column = column
        self.clock = clock
        self.rpm = 30.0
        self.run_rpm = 0.0
        self.total_deg = 0.0

    def set_speed(self, rpm):
        self.rpm = rpm

    def rotate_degrees(self, deg):
        self.total_deg += deg
        self.column.rotate(deg)
        self.clock.sleep_ms(int(abs(deg) / 360.0 / max(1.0, self.rpm)
                                * 60000))

    def run_at_rpm(self, rpm):
        self.run_rpm = rpm

    def keep_alive(self):
        if self.run_rpm:
            self.column.rotate(self.run_rpm / 60.0 * 360.0 * 0.25)

    def stop(self):
        self.run_rpm = 0.0

    def enable(self, on=True):
        pass


class FakeTap:
    def __init__(self, column):
        self.column = column
        self.count = 0

    def tap(self, count=1, on_ms=None, off_ms=None):
        self.count += count
        self.column.tap(count)

    def _off(self):
        pass


class FakeServo:
    def __init__(self):
        self.deg = 0.0

    def move_to(self, deg):
        self.deg = deg


def make_doser(column, clock, target_g=0.200, thresholds=None,
               bracket_reads=True, **scale_kw):
    scale = BenchScale(column, clock, **scale_kw)
    doser = m3p.ThreePhaseDoser(
        FakeStepper(column, clock), FakeTap(column), FakeServo(), scale,
        m3p.config,
        phases=[dict(p) for p in m3p.PHASES],
        thresholds=list(thresholds or (min(0.250, target_g),
                                       min(0.025, target_g / 2.0), 0.005)),
        timeout_s=600, log=lambda *a: None,
        monotonic=clock.time, sleep_ms=clock.sleep_ms,
        ticks_ms=lambda: int(clock.time() * 1000),
        bracket_reads=bracket_reads)
    return doser, scale


# ---------------------------------------------------------------------------

_FAILURES = []


def check(name, cond, detail=""):
    if cond:
        print("  ok   {}".format(name))
    else:
        print("  FAIL {} {}".format(name, detail))
        _FAILURES.append(name)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_balance_never_stable_still_doses():
    """The 2026-09-03 failure: 0 % stable frames must not kill the dose."""
    clock = VirtualClock()
    column = Column(g_per_rev=0.230)
    doser, scale = make_doser(column, clock, target_g=0.200,
                              stable_frames=False)
    res = doser.dose(0.200)
    check("never-stable balance does not abort the dose",
          res.status != m3p.DoseResult.SCALE_ERROR,
          "got {}".format(res.status))
    check("never-stable balance: read_stable was never relied on",
          scale.stable_reads == 0,
          "read_stable called {} times".format(scale.stable_reads))
    check("never-stable balance: the auger actually turned",
          res.auger_deg > 0, "auger_deg={}".format(res.auger_deg))
    # Deliberately NOT "delivered ~= target".  Whether the frozen
    # controller can hit 200 mg on a 230 mg/rev powder is a control
    # question -- and the answer is no, one 180 deg increment is 115 mg.
    # What the read path owes is that the reported mass is the mass that
    # actually landed.
    check("never-stable balance: reported mass is the mass that landed",
          abs(res.dispensed_g - column.pan_g) < 0.006,
          "reported {:.4f} g, on pan {:.4f} g".format(
              res.dispensed_g, column.pan_g))


def test_old_path_fails_where_new_one_works():
    """Same bench condition through read_stable() -- the regression guard."""
    clock = VirtualClock()
    column = Column(g_per_rev=0.230)
    doser, _ = make_doser(column, clock, target_g=0.200,
                          stable_frames=False, bracket_reads=False)
    res = doser.dose(0.200)
    check("read_stable path still aborts on a never-stable balance",
          res.status == m3p.DoseResult.SCALE_ERROR,
          "got {} -- the fix must be the bracket, not a fake".format(
              res.status))


def test_refused_tare_never_reports_leftovers_as_delivered():
    """The phantom-overshoot fault: 1.541 g in the cup, tare refused.

    The cup legitimately holds ~1 g after a pre-flight and an unattended
    run cannot empty it, so refusing outright would block every dose.
    Subtracting the baseline is what makes this safe: the dose is then a
    difference, and the leftover cancels instead of being reported.
    """
    clock = VirtualClock()
    column = Column(g_per_rev=0.230, start_pan_g=1.541)   # the 09-03 cup
    doser, _ = make_doser(column, clock, target_g=0.050,
                          thresholds=(0.050, 0.025, 0.005),
                          stable_frames=False, tare_works=False)
    before = column.pan_g
    res = doser.dose(0.050)
    # The bound is "nothing like the 1.541 g leftover", not "on target":
    # one 180 deg fine increment is ~121 mg on a 230 mg/rev powder, so
    # the frozen controller genuinely overshoots a 50 mg target here.
    # That overshoot is the Block H finding; reporting the leftover as
    # delivery was the bug.
    check("refused tare + full cup does not report 1.541 g as delivered",
          res.dispensed_g < 0.500,
          "reported {:.4f} g".format(res.dispensed_g))
    check("refused tare + full cup reports the increment it conveyed",
          abs(res.dispensed_g - (column.pan_g - before)) < 0.006,
          "reported {:.4f} g, conveyed {:.4f} g".format(
              res.dispensed_g, column.pan_g - before))
    check("refused tare is recorded as a baseline for the run document",
          abs(doser.last_baseline_g - 1.541) < 0.006,
          "baseline {:.4f} g".format(doser.last_baseline_g))


def test_pan_too_loaded_still_refuses():
    """Past the capacity ceiling it is still a refusal, not a dose."""
    clock = VirtualClock()
    column = Column(g_per_rev=0.230, start_pan_g=40.0)
    doser, _ = make_doser(column, clock, target_g=0.050,
                          thresholds=(0.050, 0.025, 0.005),
                          stable_frames=False, tare_works=False)
    res = doser.dose(0.050)
    check("an overloaded pan is NOT_TARED",
          res.status == m3p.DoseResult.NOT_TARED,
          "got {}".format(res.status))
    check("an overloaded pan never turns the auger",
          res.auger_deg == 0.0, "auger_deg={}".format(res.auger_deg))


def test_retry_survives_a_one_second_resolution_clock():
    """MicroPython's time.time() ticks in whole seconds on this build.

    The first version of the retry used a seconds-based deadline against
    that clock and gave up after a single attempt on the bench, so the
    retry is counted rather than timed.  This pins that: with a clock
    that never advances at all, the retry must still happen.
    """
    clock = VirtualClock()

    class FrozenClock:
        def time(self):
            return 1609466033        # never advances, like an int clock

        def sleep_ms(self, ms):
            clock.sleep_ms(ms)

    frozen = FrozenClock()
    column = Column(g_per_rev=0.230)
    scale = BenchScale(column, clock, stable_frames=False,
                       quiet_after_zero_s=3.0)
    doser = m3p.ThreePhaseDoser(
        FakeStepper(column, clock), FakeTap(column), FakeServo(), scale,
        m3p.config, phases=[dict(p) for p in m3p.PHASES],
        thresholds=[0.200, 0.025, 0.005], timeout_s=600,
        log=lambda *a: None, monotonic=frozen.time,
        sleep_ms=frozen.sleep_ms,
        ticks_ms=lambda: int(clock.time() * 1000))
    res = doser.dose(0.200)
    check("a frozen 1 s-resolution clock does not collapse the retry",
          doser.read_retries > 0,
          "no retry happened (read_retries={})".format(doser.read_retries))
    check("and the dose still reads the balance",
          res.status != m3p.DoseResult.SCALE_ERROR,
          "got {}".format(res.status))


def test_balance_quiet_after_tare_is_waited_out():
    """The 2026-09-03 re-run fault: no frames for a few seconds after T."""
    clock = VirtualClock()
    column = Column(g_per_rev=0.230)
    doser, scale = make_doser(column, clock, target_g=0.200,
                              stable_frames=False, quiet_after_zero_s=3.0)
    res = doser.dose(0.200)
    check("a balance quiet for 3 s after taring does not kill the dose",
          res.status != m3p.DoseResult.SCALE_ERROR,
          "got {}".format(res.status))
    check("the quiet window was actually exercised",
          scale.silent_reads > 0,
          "silent_reads={}".format(scale.silent_reads))
    check("the retry is counted for the run document",
          doser.read_retries > 0,
          "read_retries={}".format(doser.read_retries))


def test_balance_quiet_forever_is_still_an_error():
    clock = VirtualClock()
    column = Column()
    doser, _ = make_doser(column, clock, target_g=0.200,
                          stable_frames=False, quiet_after_zero_s=1e6)
    res = doser.dose(0.200)
    check("a permanently quiet balance is still scale-error",
          res.status == m3p.DoseResult.SCALE_ERROR,
          "got {}".format(res.status))


def test_refused_tare_with_empty_cup_still_doses():
    """A refused tare on an EMPTY pan is harmless -- do not block on it."""
    clock = VirtualClock()
    column = Column(g_per_rev=0.230, start_pan_g=0.003)
    doser, _ = make_doser(column, clock, target_g=0.200,
                          stable_frames=False, tare_works=False)
    res = doser.dose(0.200)
    check("refused tare + empty cup still doses",
          res.status != m3p.DoseResult.NOT_TARED,
          "got {}".format(res.status))
    check("refused tare + empty cup subtracts the 3 mg baseline",
          abs(res.dispensed_g - (column.pan_g - 0.003)) < 0.006,
          "reported {:.4f} g, on pan {:.4f} g".format(
              res.dispensed_g, column.pan_g))


def test_baseline_is_subtracted_not_counted():
    """Whatever the tare leaves behind is an offset, not a delivery."""
    clock = VirtualClock()
    column = Column(g_per_rev=0.230, start_pan_g=0.012)
    doser, _ = make_doser(column, clock, target_g=0.200,
                          stable_frames=False, tare_works=False)
    before = column.pan_g
    res = doser.dose(0.200)
    conveyed = column.pan_g - before          # mass actually conveyed
    check("delivered mass matches what the column actually conveyed",
          abs(res.dispensed_g - conveyed) < 0.006,
          "reported {:.4f} g, conveyed {:.4f} g".format(
              res.dispensed_g, conveyed))


def test_silent_balance_is_still_a_scale_error():
    """Robustness must not paper over a genuinely dead balance."""
    clock = VirtualClock()
    column = Column()
    doser, _ = make_doser(column, clock, target_g=0.200, silent=True)
    res = doser.dose(0.200)
    check("a silent balance is still scale-error",
          res.status == m3p.DoseResult.SCALE_ERROR,
          "got {}".format(res.status))


def test_drift_and_jitter_do_not_wreck_the_dose():
    """The new fume hood's actual condition: smooth ramp + 0.07 mg jitter."""
    clock = VirtualClock()
    column = Column(g_per_rev=0.230)
    doser, _ = make_doser(column, clock, target_g=0.200,
                          stable_frames=False,
                          drift_g_per_s=-0.0000300,     # -1.8 mg/min
                          jitter_g=0.00007)
    res = doser.dose(0.200)
    check("dose completes under new-hood drift and jitter",
          res.status in (m3p.DoseResult.OK, m3p.DoseResult.OVERSHOOT,
                         m3p.DoseResult.BUDGET, m3p.DoseResult.STALLED),
          "got {}".format(res.status))
    check("drift rate is measured and recorded",
          doser.baseline_drift_g_per_s != 0.0,
          "slope {}".format(doser.baseline_drift_g_per_s))
    check("per-read noise is recorded for the run document",
          doser.read_sigma_g >= 0.0)


def test_controller_parameters_are_untouched():
    """This is a measurement change, not a control change."""
    check("phase 1 angle unchanged", m3p.PHASE1_BULK["angle_deg"] == 25.0)
    check("phase 2 rotation unchanged",
          m3p.PHASE2_FINE["rotation_deg"] == 180)
    check("phase 3 taps at horizontal",
          m3p.PHASE3_TAP["angle_deg"] == 0.0)
    check("thresholds unchanged",
          tuple(m3p.THRESHOLDS) == (0.250, 0.025, 0.001))
    check("dose timeout unchanged", m3p.DOSE_TIMEOUT_S == 600)


def test_bracket_read_shape_is_sane():
    check("bracket is several frames", m3p.DOSE_BRACKET_N >= 3)
    check("a bracket read costs about a second, not a minute",
          0.5 <= m3p.DOSE_BRACKET_N * m3p.DOSE_BRACKET_INTERVAL_MS / 1000.0
          <= 3.0)
    check("baseline warning sits above drift, below a pre-flight leftover",
          0.010 <= m3p.DOSE_WARN_BASELINE_G <= 0.100)
    check("baseline ceiling clears a pre-flight leftover but not the pan",
          1.0 <= m3p.DOSE_MAX_BASELINE_G <= 50.0)
    check("the read is retried enough to outlast a quiet balance",
          m3p.DOSE_READ_RETRIES >= 8)


def main():
    for fn in (test_balance_never_stable_still_doses,
               test_old_path_fails_where_new_one_works,
               test_refused_tare_never_reports_leftovers_as_delivered,
               test_pan_too_loaded_still_refuses,
               test_balance_quiet_after_tare_is_waited_out,
               test_retry_survives_a_one_second_resolution_clock,
               test_balance_quiet_forever_is_still_an_error,
               test_refused_tare_with_empty_cup_still_doses,
               test_baseline_is_subtracted_not_counted,
               test_silent_balance_is_still_a_scale_error,
               test_drift_and_jitter_do_not_wreck_the_dose,
               test_controller_parameters_are_untouched,
               test_bracket_read_shape_is_sane):
        print(fn.__name__)
        fn()
    if _FAILURES:
        print("\n{} check(s) FAILED: {}".format(len(_FAILURES),
                                                ", ".join(_FAILURES)))
        return 1
    print("\nall three-phase read-path checks pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
