"""Angle-sweep characterization of the powder doser (issue #130).

Measures, at each dispensing angle, how much powder the auger moves per
rotation and how much each solenoid tap knocks loose, with enough
repeats per angle to estimate the uncertainty of both.

Procedure per angle in ``ANGLES_DEG``:

1. Move the dispensing-angle servo to the angle and let the rig settle.
2. (Optional) prompt the operator to empty the collection cup / check
   the hopper, then re-zero (tare) the balance.
3. Take ``BASELINE_READS`` back-to-back stable readings with *no*
   actuation, ``SETTLE_MS`` apart.  The spread of these deltas is the
   scale's noise + drift floor at this angle -- the measurement
   uncertainty underneath every trial.
4. ``POINTS_PER_ANGLE`` **rotation trials**: stable reading, rotate the
   auger ``ROTATION_STEP_DEG``, wait ``SETTLE_MS``, stable reading.
   ``delta_g`` is the per-rotation yield.
5. ``POINTS_PER_ANGLE`` **tap trials**: taps dispense less and less if
   the tube lip is never re-fed, so every tap trial is preceded by a
   ``REFEED_DEG`` auger rotation whose mass change is measured and
   recorded as its own ``refeed`` row -- it is *never* attributed to
   the tap.  The tap's ``delta_g`` is measured from the post-re-feed
   mass, so it is the tap-only yield.  (``refeed`` rows use the same
   rotation size as step 4 by default, so they can be pooled with the
   ``rotation`` rows for extra per-rotation data points.)

Every trial is a *stable*-reading-to-stable-reading delta
(``scale.read_stable``), so each data point already waits out the
balance's settling time on both sides of the actuation.

Output is one machine-readable line per event over USB serial::

    RUN,BEGIN
    META,<key>,<value>                       run parameters + config echo
    CSV,<angle_deg>,<phase>,<trial>,<action>,<before_g>,<after_g>,<delta_g>,<flag>,<t_ms>
    SUM,<angle_deg>,<phase>,<n>,<mean_g>,<std_g>,<sem_g>,<min_g>,<max_g>
    RUN,END,<status>

``phase`` is ``baseline`` / ``rotation`` / ``refeed`` / ``tap``;
``action`` is the rotation in degrees or the tap count; ``flag`` is
empty or ``lowflow`` (see stall handling below); ``std`` is the sample
standard deviation (n-1) and ``sem`` = std/sqrt(n).  Capture the stream
on the bench host with ``scripts/characterize_capture.py``, which
re-derives the statistics, writes CSV/JSON, and can upload the run
document to MongoDB (issue #126).

Stall handling: if ``MAX_STALLS`` consecutive rotations each move less
than ``MIN_FLOW_G``, the hopper is probably empty (or the powder is
bridging) and the operator is prompted to refill.  Pressing Enter
discards the low-flow points (they stay in the CSV flagged ``lowflow``)
and retries them; typing ``keep`` accepts low flow as real data for
this angle (e.g. shallow angles that genuinely barely flow).

Running on the Pico (needs the PR #100 firmware stack uploaded next to
this file: ``config.py``, ``tic.py``, ``scale.py``, ``main.py``):
interrupt the main REPL loop with Ctrl+C, then::

    >>> import characterize
    >>> characterize.run()

Any tunable below can be overridden per-run without editing the file::

    >>> characterize.run(points_per_angle=10, angles_deg=[30, 60, 90])

This module is import-safe under CPython; ``sim/test_characterize.py``
drives the same ``Characterizer`` against a simulated rig.
"""

import math
import sys
import time

# -----------------------------------------------------------------------
# Tunables -- edit here (or pass as keyword overrides to ``run()``).
# -----------------------------------------------------------------------
# Number of data points collected per angle, for BOTH the rotation
# phase and the tap phase.  The single most-edited knob.
POINTS_PER_ANGLE  = 5
# Dispensing angles to sweep (deg, within SERVO_MIN/MAX_ANGLE_DEG).
ANGLES_DEG        = [0, 15, 30, 45, 60, 75, 90]
# Auger rotation per rotation trial (deg).  360 = one full rotation.
ROTATION_STEP_DEG = 360.0
# Solenoid taps fired per tap trial (1 isolates a single tap).
TAPS_PER_POINT    = 1
# Auger re-feed between tap trials (deg).  Keep equal to
# ROTATION_STEP_DEG so refeed rows pool with rotation rows.
REFEED_DEG        = 360.0
# No-actuation stable readings per angle (scale noise/drift floor).
BASELINE_READS    = 5
# Wait after every actuation before trusting the balance (ms).  The
# HR-100A needs ~1.5 s to stabilise; stable reads add their own wait.
SETTLE_MS         = 2000
# Extra wait after the servo reaches a new angle (rig stops swaying).
ANGLE_SETTLE_MS   = 2000
# Re-zero (tare) the balance at the start of every angle.
ZERO_EACH_ANGLE   = True
# Pause for the operator (empty cup / check hopper) at every angle.
PROMPT_EACH_ANGLE = True
# Stall detection: a rotation moving less than MIN_FLOW_G counts as
# low-flow; MAX_STALLS consecutive low-flow rotations prompt a refill.
MIN_FLOW_G        = 0.0005
MAX_STALLS        = 3
# Give up on an angle after this many failed scale reads in a row.
MAX_READ_RETRIES  = 3

# Phase labels used in CSV/SUM rows.
BASELINE = "baseline"
ROTATION = "rotation"
REFEED   = "refeed"
TAP      = "tap"

# config.py keys echoed as META rows for provenance (issue #126: every
# dataset carries the parameters it was collected under).
CONFIG_ECHO_KEYS = (
    "STEPPER_SPEED_RPM", "STEPPER_MICROSTEPS", "STEPPER_FULL_STEPS_REV",
    "STEPPER_ACCEL_REV_PER_S2", "TAP_ON_MS", "TAP_OFF_MS", "TAP_PWM_DUTY",
    "SERVO_SPEED_DEG_PER_S", "SCALE_BAUD", "SCALE_BITS", "SCALE_PARITY",
    "SCALE_STOP", "SCALE_STABLE_TIMEOUT_MS", "DOSE_SETTLE_MS",
)

try:
    _ticks_ms = time.ticks_ms            # MicroPython
    _ticks_diff = time.ticks_diff
except AttributeError:                   # CPython (sim tests)
    def _ticks_ms():
        return int(time.monotonic() * 1000)

    def _ticks_diff(a, b):
        return a - b


def sample_stats(values):
    """``(n, mean, std, sem, min, max)``; std/sem are ``None`` for n<2.

    ``std`` is the *sample* standard deviation (n-1 denominator) --
    the uncertainty of a single trial; ``sem = std/sqrt(n)`` is the
    uncertainty of the reported mean.
    """
    n = len(values)
    if n == 0:
        return 0, None, None, None, None, None
    mean = sum(values) / n
    if n > 1:
        var = sum((v - mean) ** 2 for v in values) / (n - 1)
        std = math.sqrt(var)
        sem = std / math.sqrt(n)
    else:
        std = None
        sem = None
    return n, mean, std, sem, min(values), max(values)


class AbortRun(Exception):
    pass


class SkipAngle(Exception):
    pass


def _fmt_g(value):
    return "" if value is None else "{:.4f}".format(value)


class Characterizer:
    """Drives the sweep against duck-typed hardware.

    ``stepper`` needs ``rotate_degrees(deg)``, ``tap`` needs
    ``tap(count)``, ``servo`` needs ``move_to(deg)``, and ``scale``
    needs ``read_stable(timeout_ms)`` / ``zero()`` returning
    ``scale.ScaleReading``-shaped objects -- exactly the surface of the
    rig classes in ``main.py``/``scale.py``, and of the fakes in
    ``sim/``.
    """

    def __init__(self, stepper, tap, servo, scale,
                 log=print, sleep_ms=None, input_line=None,
                 config_echo=None, stable_timeout_ms=10000,
                 points_per_angle=None, angles_deg=None,
                 rotation_step_deg=None, taps_per_point=None,
                 refeed_deg=None, baseline_reads=None, settle_ms=None,
                 angle_settle_ms=None, zero_each_angle=None,
                 prompt_each_angle=None, min_flow_g=None,
                 max_stalls=None, max_read_retries=None):
        self.stepper = stepper
        self.tap = tap
        self.servo = servo
        self.scale = scale
        self.log = log
        if sleep_ms is None:
            try:
                sleep_ms = time.sleep_ms          # MicroPython
            except AttributeError:
                sleep_ms = lambda ms: time.sleep(ms / 1000.0)
        self._sleep_ms = sleep_ms
        # Called to get one operator line at a prompt; None = run
        # unattended (every prompt auto-continues).
        self._input_line = input_line
        self.config_echo = config_echo or {}
        self.stable_timeout_ms = stable_timeout_ms

        def _default(value, fallback):
            return fallback if value is None else value

        self.points_per_angle = _default(points_per_angle, POINTS_PER_ANGLE)
        self.angles_deg = list(_default(angles_deg, ANGLES_DEG))
        self.rotation_step_deg = _default(rotation_step_deg,
                                          ROTATION_STEP_DEG)
        self.taps_per_point = _default(taps_per_point, TAPS_PER_POINT)
        self.refeed_deg = _default(refeed_deg, REFEED_DEG)
        self.baseline_reads = _default(baseline_reads, BASELINE_READS)
        self.settle_ms = _default(settle_ms, SETTLE_MS)
        self.angle_settle_ms = _default(angle_settle_ms, ANGLE_SETTLE_MS)
        self.zero_each_angle = _default(zero_each_angle, ZERO_EACH_ANGLE)
        self.prompt_each_angle = _default(prompt_each_angle,
                                          PROMPT_EACH_ANGLE)
        self.min_flow_g = _default(min_flow_g, MIN_FLOW_G)
        self.max_stalls = _default(max_stalls, MAX_STALLS)
        self.max_read_retries = _default(max_read_retries, MAX_READ_RETRIES)

        self._t0 = _ticks_ms()

    # -- plumbing ------------------------------------------------------

    def _elapsed_ms(self):
        return _ticks_diff(_ticks_ms(), self._t0)

    def _emit(self, *parts):
        self.log(",".join(str(p) for p in parts))

    def _emit_trial(self, angle, phase, trial, action, before, after, delta,
                    flag=""):
        self._emit("CSV", "{:.1f}".format(angle), phase, trial, action,
                   _fmt_g(before), _fmt_g(after), _fmt_g(delta), flag,
                   self._elapsed_ms())

    def _emit_summary(self, angle, phase, values):
        n, mean, std, sem, lo, hi = sample_stats(values)
        self._emit("SUM", "{:.1f}".format(angle), phase, n, _fmt_g(mean),
                   _fmt_g(std), _fmt_g(sem), _fmt_g(lo), _fmt_g(hi))

    def _prompt(self, message):
        """Show ``message``, wait for the operator; '' / keep / skip / abort."""
        self.log("PROMPT,{}".format(message))
        if self._input_line is None:
            return ""
        line = self._input_line()
        return (line or "").strip().lower()

    def _prompt_or_raise(self, message):
        ans = self._prompt(message)
        if ans == "abort":
            raise AbortRun("operator abort")
        if ans == "skip":
            raise SkipAngle("operator skip")
        return ans

    # -- measurement ---------------------------------------------------

    def _read_grams(self):
        """One stable reading in grams, or ``None`` on scale trouble."""
        reading = self.scale.read_stable(timeout_ms=self.stable_timeout_ms)
        if (reading is None or not reading.stable or reading.overload or
                reading.grams is None):
            return None
        unit = getattr(reading, "unit", "g")
        if unit and unit != "g":
            # A balance left in grains (AutoTrickler preset) would skew
            # every number by 15.4x -- refuse rather than mis-record.
            self.log("[char] scale reports {!r}, not grams -- press MODE "
                     "on the balance to select g".format(unit))
            return None
        return reading.grams

    def _read_required(self):
        """Stable grams, prompting the operator through failures."""
        failures = 0
        while True:
            grams = self._read_grams()
            if grams is not None:
                return grams
            failures += 1
            if failures >= self.max_read_retries:
                raise SkipAngle("scale reads failing")
            self._prompt_or_raise(
                "scale read failed (silent/unstable/overload) -- clear the "
                "problem (empty the cup if full), then Enter to re-tare and "
                "retry, 'skip' for next angle, 'abort' to end")
            self.scale.zero()
            self._sleep_ms(self.settle_ms)

    def _measured(self, action_fn):
        """Stable reading, action, settle, stable reading -> (before, after)."""
        before = self._read_required()
        action_fn()
        self._sleep_ms(self.settle_ms)
        after = self._read_required()
        return before, after

    # -- phases --------------------------------------------------------

    def _baseline(self, angle):
        """No-actuation deltas: the scale noise/drift floor at this angle."""
        deltas = []
        previous = self._read_required()
        for i in range(self.baseline_reads):
            self._sleep_ms(self.settle_ms)
            reading = self._read_required()
            delta = reading - previous
            self._emit_trial(angle, BASELINE, i, "", previous, reading, delta)
            deltas.append(delta)
            previous = reading
        self._emit_summary(angle, BASELINE, deltas)

    def _rotations(self, angle):
        """POINTS_PER_ANGLE per-rotation yields, with stall handling."""
        deltas = []
        streak = []          # consecutive low-flow deltas, not yet counted
        stall_check = self.min_flow_g > 0
        trial = 0
        while len(deltas) < self.points_per_angle:
            before, after = self._measured(
                lambda: self.stepper.rotate_degrees(self.rotation_step_deg))
            delta = after - before
            lowflow = stall_check and delta < self.min_flow_g
            self._emit_trial(angle, ROTATION, trial, self.rotation_step_deg,
                             before, after, delta,
                             "lowflow" if lowflow else "")
            trial += 1
            if lowflow:
                streak.append(delta)
                if len(streak) >= self.max_stalls:
                    ans = self._prompt_or_raise(
                        "{} consecutive rotations moved <{} g at angle {} "
                        "-- hopper empty?  Refill and press Enter to retry "
                        "these points, 'keep' to accept low flow as real "
                        "data, 'skip'/'abort'".format(
                            len(streak), self.min_flow_g, angle))
                    if ans == "keep":
                        deltas.extend(streak)
                        stall_check = False
                    streak = []       # Enter: discarded (flagged in CSV)
                continue
            # Flow resumed after a brief dip: those dips were probably
            # real (powder bridging), keep them as data points.
            deltas.extend(streak)
            streak = []
            deltas.append(delta)
        self._emit_summary(angle, ROTATION, deltas)
        return deltas

    def _taps(self, angle):
        """POINTS_PER_ANGLE tap-only yields, re-feeding between taps.

        The re-feed rotation before every tap keeps the tube lip loaded
        (taps decay to nothing otherwise) and its mass is measured into
        its own ``refeed`` row so the tap delta stays tap-only.
        """
        tap_deltas = []
        refeed_deltas = []
        streak = 0
        stall_check = self.min_flow_g > 0
        trial = 0
        while len(tap_deltas) < self.points_per_angle:
            before, after = self._measured(
                lambda: self.stepper.rotate_degrees(self.refeed_deg))
            refeed_delta = after - before
            lowflow = stall_check and refeed_delta < self.min_flow_g
            self._emit_trial(angle, REFEED, trial, self.refeed_deg,
                             before, after, refeed_delta,
                             "lowflow" if lowflow else "")
            if lowflow:
                streak += 1
                if streak >= self.max_stalls:
                    ans = self._prompt_or_raise(
                        "{} consecutive re-feeds moved <{} g at angle {} "
                        "-- hopper empty?  Refill and press Enter to retry, "
                        "'keep' to tap anyway, 'skip'/'abort'".format(
                            streak, self.min_flow_g, angle))
                    streak = 0
                    if ans != "keep":
                        trial += 1
                        continue      # retry the re-feed after refill
                    stall_check = False
                else:
                    trial += 1
                    continue          # lip may be empty; re-feed again
            else:
                streak = 0
            refeed_deltas.append(refeed_delta)
            before, after = self._measured(
                lambda: self.tap.tap(self.taps_per_point))
            tap_delta = after - before
            self._emit_trial(angle, TAP, trial, self.taps_per_point,
                             before, after, tap_delta)
            tap_deltas.append(tap_delta)
            trial += 1
        self._emit_summary(angle, REFEED, refeed_deltas)
        self._emit_summary(angle, TAP, tap_deltas)
        return tap_deltas

    def _run_angle(self, angle):
        self.log("[char] angle {} deg".format(angle))
        self.servo.move_to(angle)
        self._sleep_ms(self.angle_settle_ms)
        if self.prompt_each_angle:
            self._prompt_or_raise(
                "at angle {} -- empty the collection cup if it is getting "
                "full, check the hopper, then Enter to start "
                "('skip'/'abort')".format(angle))
        if self.zero_each_angle:
            self.scale.zero()
            self._sleep_ms(self.settle_ms)
        self._baseline(angle)
        self._rotations(angle)
        self._taps(angle)

    # -- entry ---------------------------------------------------------

    def run_all(self):
        self._t0 = _ticks_ms()
        self._emit("RUN", "BEGIN")
        for key, value in (
                ("points_per_angle", self.points_per_angle),
                ("angles_deg", ";".join(str(a) for a in self.angles_deg)),
                ("rotation_step_deg", self.rotation_step_deg),
                ("taps_per_point", self.taps_per_point),
                ("refeed_deg", self.refeed_deg),
                ("baseline_reads", self.baseline_reads),
                ("settle_ms", self.settle_ms),
                ("min_flow_g", self.min_flow_g)):
            self._emit("META", key, value)
        for key in sorted(self.config_echo):
            self._emit("META", "config." + key, self.config_echo[key])
        status = "ok"
        try:
            for angle in self.angles_deg:
                try:
                    self._run_angle(angle)
                except SkipAngle as exc:
                    self.log("[char] skipping angle {}: {}".format(
                        angle, exc))
        except AbortRun as exc:
            self.log("[char] run aborted: {}".format(exc))
            status = "aborted"
        except KeyboardInterrupt:
            status = "interrupted"
            raise
        finally:
            self._emit("RUN", "END", status)
        return status


def run(**overrides):
    """Bring up the rig hardware and run the sweep (Pico entry point).

    Requires the PR #100 firmware stack on the Pico (``config.py``,
    ``tic.py``, ``scale.py``, ``main.py``).  Keyword overrides map to
    the module tunables, e.g. ``run(points_per_angle=10)``.
    """
    import config
    import main as rig_main
    import scale as scale_mod
    from machine import UART, Pin

    stepper = rig_main.Stepper()
    tap = rig_main.Tap()
    servo = rig_main.Servo()
    uart = scale_mod.open_uart(config, UART, Pin)
    balance = scale_mod.AndScale(
        uart, response_timeout_ms=getattr(
            config, "SCALE_RESPONSE_TIMEOUT_MS", 1000))
    echo = {k: getattr(config, k) for k in CONFIG_ECHO_KEYS
            if hasattr(config, k)}
    characterizer = Characterizer(
        stepper, tap, servo, balance,
        input_line=sys.stdin.readline,
        config_echo=echo,
        stable_timeout_ms=getattr(config, "SCALE_STABLE_TIMEOUT_MS", 10000),
        **overrides)
    try:
        return characterizer.run_all()
    finally:
        # Never leave the motor energised or the solenoid latched.
        try:
            stepper.enable(False)
        except Exception:
            pass
        try:
            tap._off()
        except Exception:
            pass
