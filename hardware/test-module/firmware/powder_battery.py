"""Uniform powder test battery (issue #116).

One FIXED sequence of tests, run identically for every powder, so the
results are directly comparable across powders.  This is deliberately
*not* an optimization workflow: the parameters below are frozen (the
tuned-salt values from the PR #124 three-phase demos) and the point is
to see how each powder behaves under the same conditions.

The battery covers every degree of freedom of the rig once:

  Block A  "baseline"  Scale noise floor: 8 no-actuation stable-reading
                       deltas at tilt 45.
  Block B  "hold"      Static-tilt avalanche check: at tilt 0, 45 and
                       90, hold 15 s with NO actuation and measure the
                       mass change.  Free-flowing powders discharge on
                       their own near vertical; cohesive ones do not.
  Block C  "rotation"  Tilt x rotation yield: at tilt 0, 45 and 90,
                       six incremental 360-deg auger rotations at
                       30 auger RPM, stable reading after each -->
                       grams-per-revolution vs tilt, and its spread.
  Block D  "speed"     Rotation-speed sweep: at tilt 45, three auger
                       revolutions of continuous rotation at 15, 45
                       and 90 auger RPM, streaming instantaneous scale
                       polls --> flow rate vs speed and pulsation.
  Block E  "tap"       Tap yield: at tilt 0 and 45, eight single-tap
                       trials, each preceded by a measured 360-deg
                       re-feed rotation (characterize.py-style re-feed
                       accounting, so tap deltas stay tap-only).
  Block F  "vib"       Vibration yield: same shape as Block E with the
                       DRV2605L haptic motor instead of the solenoid.
                       Skipped (with a META row) when the driver is
                       unavailable, as it currently reports EIO.
  Block G  "dose"      The headline: three closed-loop 1.000 g doses
                       with the THREE-PHASE controller (PR #124) under
                       the frozen parameter set below --> accuracy,
                       time-to-dose and phase breakdown per powder.

Tilt convention: user-facing TILT degrees, 0 = tube horizontal,
90 = tube vertical -- i.e. the servo-horn convention of main.py and
the 0/45/90 requested in issue #116.  The three-phase servo speaks
mounting-PLATE degrees (2:1 horn gearing, plate 45 = vertical), so
tilt is halved at the servo boundary (``PLATE_PER_TILT``).

Serial protocol (one machine-readable line per event, superset of the
characterize.py stream; captured by ``scripts/powder_battery_capture.py``)::

    RUN,BEGIN
    META,<key>,<value>
    CSV,<block>,<tilt_deg>,<phase>,<trial>,<action>,<rpm>,<before_g>,<after_g>,<delta_g>,<flag>,<t_ms>
    POLL,<block>,<tilt_deg>,<rpm>,<t_ms>,<grams>,<stable>
    DOSE,<n>,<target_g>,<dispensed_g>,<error_g>,<status>,<elapsed_s>,<auger_rev>,<taps>,<phase_cycles>,<t_ms>
    SUM,<block>,<tilt_deg>,<phase>,<n>,<mean_g>,<std_g>,<sem_g>,<min_g>,<max_g>
    PROMPT,<message>
    RUN,END,<status>

``flag`` is empty or ``lowflow``.  Low-flow trials are DATA here, not
errors -- a cohesive powder refusing to move at tilt 0 is exactly the
behaviour the battery exists to record -- so they are kept (flagged);
the operator is only prompted after ``MAX_STALLS`` consecutive
low-flow rows in case the hopper is simply empty.  Unattended runs
(``attended=False``) auto-answer every prompt (stall prompts answer
``keep``), so the battery never blocks on a keyboard.

Running on the Pico (needs the PR #100 driver stack -- ``config.py``,
``tic.py``, ``scale.py`` -- and PR #124's ``main_three_phase.py``
uploaded next to this file; all are already on the bench Pico)::

    >>> import powder_battery
    >>> powder_battery.run(powder_id="brown-rice-flour")

Any tunable below can be overridden per run, e.g.
``run(powder_id="salt", blocks="CG", dose_repeats=1)``.

This module is import-safe under CPython and fully hardware-agnostic:
``sim/test_powder_battery.py`` drives the same ``Battery`` against
fakes, and only ``run()`` touches the firmware stack.
"""

import math
import sys
import time

import balance_filter

# -----------------------------------------------------------------------
# Frozen battery parameters -- identical for every powder.  Change them
# only deliberately (and bump SCHEMA "battery_version"), because edits
# break comparability with earlier runs.
# -----------------------------------------------------------------------
BATTERY_VERSION   = 2
POWDER_ID         = None

TILTS_DEG         = [0.0, 45.0, 90.0]  # tube tilt; 0 horizontal, 90 vertical
PLATE_PER_TILT    = 0.5                # plate deg per tilt deg (2:1 gearing)
PARK_TILT_DEG     = 0.0                # tilt the rig is left at after a run

BASELINE_READS    = 8       # Block A
BASELINE_TILT     = 45.0

HOLD_S            = 15      # Block B: static hold per tilt

ROTATION_TRIALS   = 6       # Block C: rotations per tilt
ROTATION_STEP_DEG = 360.0   # one full auger revolution per trial
ROTATION_RPM      = 30.0

SPEED_TILT        = 45.0    # Block D
SPEED_RPMS        = [15.0, 45.0, 90.0]
SPEED_REVS        = 3.0     # auger revolutions per speed point
SPEED_POLL_MS     = 250

TAP_TILTS         = [0.0, 45.0]  # Blocks E and F
TAP_TRIALS        = 8       # per tilt
TAPS_PER_POINT    = 1       # single tap isolates the per-tap quantum
TAP_ON_MS         = 60
TAP_OFF_MS        = 150
REFEED_DEG        = 360.0   # measured re-feed rotation before each trial
VIB_BURSTS        = 3       # DRV2605L effect plays per vibration trial

DOSE_REPEATS      = 3       # Block G
DOSE_TARGET_G     = 1.000
DOSE_TIMEOUT_S    = 900

SETTLE_MS         = 2000    # wait after actuation before trusting scale
TILT_SETTLE_MS    = 2000    # extra wait after a servo move
MIN_FLOW_G        = 0.0005  # below this a trial is flagged lowflow
MAX_STALLS        = 4       # consecutive lowflow rows before prompting
MAX_READ_RETRIES  = 3

# -----------------------------------------------------------------------
# Environment-artifact rejection (battery_version 2, 2026-08-20).
#
# Every trial is bracketed by two windows in which no actuator is
# commanded, so anything that moves during them is provably not powder.
# The bracket slope is the balance's creep, extrapolated across the
# action; a single-poll jump above SHOCK_G is a mechanical shock, and is
# subtracted as a zero step *and counted*; the residual scatter becomes
# the trial's uncertainty.  See balance_filter.py for the rationale and
# docs/rig-checks/2026-08-20-calibration-and-environment-survey.md for
# the measurements that set these numbers.
# -----------------------------------------------------------------------
BRACKET_N         = 6       # scale samples per bracket
BRACKET_MS        = 400     # spacing between bracket samples
SHOCK_G           = 0.010   # single-poll jump treated as a shock
MAX_RESID_G       = 0.0015  # residual RMS above which a bracket is unsettled
QUIET_TRIES       = 8       # brackets to try while waiting for a quiet one
MAX_TRIAL_RETRIES = 2       # re-measurements of a disturbed trial
DRIFT_CORRECT     = True    # extrapolate pre-action creep across the action

BLOCKS            = "ABCDEFG"   # which blocks to run, in order

# A&D HR-100A capacity.  Capacity is *gross*: taring the vessel does not
# buy any of it back, so the battery warns before it runs out rather
# than discovering it as an OL frame mid-block.
CAPACITY_G        = 102.0
CAPACITY_WARN_G   = 90.0

# Three-phase controller parameters for Block G: the tuned-salt set
# from the PR #124 bench demos (continuous bulk with the measured
# ~0.12 g in-flight anticipation; 45-deg fine increments so phase 3's
# taps actually run), frozen as the uniform cross-powder settings.
DOSE_THRESHOLDS = (0.500, 0.050, 0.005)   # t1 bulk->fine, t2 fine->tap, t3 +/-
DOSE_PHASES = (
    {
        "name": "bulk", "angle_deg": 45.0, "rotation_deg": 360.0,
        "rotation_rpm": 55.0, "continuous": 1, "poll_ms": 250,
        "anticipation_g": 0.12, "taps_per_cycle": 0, "tap_on_ms": 60,
        "tap_off_ms": 150, "settle_ms": 800, "min_gain_g": 0.002,
        "max_stall_cycles": 5, "stall_nudge_deg": 0.0, "max_nudges": 0,
        "max_cycles": 200,
    },
    {
        "name": "fine", "angle_deg": 22.5, "rotation_deg": 45.0,
        "rotation_rpm": 30.0, "continuous": 0, "poll_ms": 250,
        "anticipation_g": 0.0, "taps_per_cycle": 0, "tap_on_ms": 60,
        "tap_off_ms": 150, "settle_ms": 1500, "min_gain_g": 0.0005,
        "max_stall_cycles": 5, "stall_nudge_deg": 0.0, "max_nudges": 0,
        "max_cycles": 200,
    },
    {
        "name": "tap", "angle_deg": 0.0, "rotation_deg": 0.0,
        "rotation_rpm": 0.0, "continuous": 0, "poll_ms": 250,
        "anticipation_g": 0.0, "taps_per_cycle": 2, "tap_on_ms": 60,
        "tap_off_ms": 150, "settle_ms": 1500, "min_gain_g": 0.0002,
        "max_stall_cycles": 3, "stall_nudge_deg": 5.0, "max_nudges": 10,
        "max_cycles": 200,
    },
)

# Phase labels used in CSV/SUM rows.
BASELINE = "baseline"
HOLD     = "hold"
ROTATION = "rotation"
SPEED    = "speed"
REFEED   = "refeed"
TAP      = "tap"
VIB      = "vib"

try:
    _ticks_ms = time.ticks_ms            # MicroPython
    _ticks_diff = time.ticks_diff
except AttributeError:                   # CPython (sim tests)
    def _ticks_ms():
        return int(time.monotonic() * 1000)

    def _ticks_diff(a, b):
        return a - b


def sample_stats(values):
    """``(n, mean, std, sem, min, max)``; std/sem are ``None`` for n<2."""
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


class SkipBlock(Exception):
    pass


def _fmt_g(value):
    return "" if value is None else "{:.4f}".format(value)


class Battery:
    """Drives the battery against duck-typed hardware.

    ``stepper`` needs ``rotate_degrees(deg)`` / ``set_speed(rpm)`` plus
    the velocity mode ``run_at_rpm(rpm)`` / ``keep_alive()`` /
    ``stop()``; ``tap`` needs ``tap(count, on_ms, off_ms)``; ``servo``
    needs ``move_to(plate_deg)``; ``scale`` needs ``read()`` /
    ``read_stable(timeout_ms)`` / ``zero()`` returning
    ``scale.ScaleReading``-shaped objects; ``vib`` (optional) needs
    ``buzz()``; ``doser`` (optional, needed for Block G) needs
    ``dose(target_g)`` returning a PR #124 ``DoseResult``-shaped
    object.  These are exactly the surfaces of the classes in
    ``main_three_phase.py`` and of the fakes in ``sim/``.
    """

    def __init__(self, stepper, tap, servo, scale, vib=None, doser=None,
                 log=print, sleep_ms=None, input_line=None, attended=True,
                 config_echo=None, stable_timeout_ms=10000, powder_id=None,
                 blocks=None, tilts_deg=None, baseline_reads=None,
                 hold_s=None, rotation_trials=None, rotation_step_deg=None,
                 rotation_rpm=None, speed_rpms=None, speed_revs=None,
                 speed_poll_ms=None, tap_tilts=None, tap_trials=None,
                 taps_per_point=None, refeed_deg=None, vib_bursts=None,
                 dose_repeats=None, dose_target_g=None, settle_ms=None,
                 tilt_settle_ms=None, min_flow_g=None, max_stalls=None,
                 max_read_retries=None, bracket_n=None, bracket_ms=None,
                 shock_g=None, max_resid_g=None, quiet_tries=None,
                 max_trial_retries=None, drift_correct=None,
                 ticks_ms=None):
        self.stepper = stepper
        self.tap = tap
        self.servo = servo
        self.scale = scale
        self.vib = vib
        self.doser = doser
        self.log = log
        if sleep_ms is None:
            try:
                sleep_ms = time.sleep_ms          # MicroPython
            except AttributeError:
                sleep_ms = lambda ms: time.sleep(ms / 1000.0)
        self._sleep_ms = sleep_ms
        self._input_line = input_line
        self.attended = attended and input_line is not None
        self.config_echo = config_echo or {}
        self.stable_timeout_ms = stable_timeout_ms

        def _default(value, fallback):
            return fallback if value is None else value

        self.powder_id = _default(powder_id, POWDER_ID)
        self.blocks = str(_default(blocks, BLOCKS)).upper()
        self.tilts_deg = list(_default(tilts_deg, TILTS_DEG))
        self.baseline_reads = _default(baseline_reads, BASELINE_READS)
        self.hold_s = _default(hold_s, HOLD_S)
        self.rotation_trials = _default(rotation_trials, ROTATION_TRIALS)
        self.rotation_step_deg = _default(rotation_step_deg,
                                          ROTATION_STEP_DEG)
        self.rotation_rpm = _default(rotation_rpm, ROTATION_RPM)
        self.speed_rpms = list(_default(speed_rpms, SPEED_RPMS))
        self.speed_revs = _default(speed_revs, SPEED_REVS)
        self.speed_poll_ms = _default(speed_poll_ms, SPEED_POLL_MS)
        self.tap_tilts = list(_default(tap_tilts, TAP_TILTS))
        self.tap_trials = _default(tap_trials, TAP_TRIALS)
        self.taps_per_point = _default(taps_per_point, TAPS_PER_POINT)
        self.refeed_deg = _default(refeed_deg, REFEED_DEG)
        self.vib_bursts = _default(vib_bursts, VIB_BURSTS)
        self.dose_repeats = _default(dose_repeats, DOSE_REPEATS)
        self.dose_target_g = _default(dose_target_g, DOSE_TARGET_G)
        self.settle_ms = _default(settle_ms, SETTLE_MS)
        self.tilt_settle_ms = _default(tilt_settle_ms, TILT_SETTLE_MS)
        self.min_flow_g = _default(min_flow_g, MIN_FLOW_G)
        self.max_stalls = _default(max_stalls, MAX_STALLS)
        self.max_read_retries = _default(max_read_retries, MAX_READ_RETRIES)
        self.bracket_n = _default(bracket_n, BRACKET_N)
        self.bracket_ms = _default(bracket_ms, BRACKET_MS)
        self.shock_g = _default(shock_g, SHOCK_G)
        self.max_resid_g = _default(max_resid_g, MAX_RESID_G)
        self.quiet_tries = _default(quiet_tries, QUIET_TRIES)
        self.max_trial_retries = _default(max_trial_retries,
                                          MAX_TRIAL_RETRIES)
        self.drift_correct = _default(drift_correct, DRIFT_CORRECT)
        # Injectable so the simulation tests can drive a virtual clock
        # through the same drift/shock arithmetic the Pico runs.
        self._ticks_ms = ticks_ms or _ticks_ms

        self._t0 = self._ticks_ms()
        self._tilt = None
        # Environment bookkeeping, reported as META rows at the end so
        # the artifact rate lands in the data rather than being silently
        # absorbed into the measurements.
        self.env = {"shock_events": 0, "shock_total_g": 0.0,
                    "retries": 0, "quiet_waits": 0, "disturbed_trials": 0,
                    "brackets": 0, "unsettled_brackets": 0,
                    "drift_corrected_g": 0.0}

    # -- plumbing ------------------------------------------------------

    def _elapsed_ms(self):
        return _ticks_diff(self._ticks_ms(), self._t0)

    def _emit(self, *parts):
        self.log(",".join(str(p) for p in parts))

    def _emit_trial(self, block, tilt, phase, trial, action, rpm,
                    before, after, delta, flag="", meas=None, retries=0):
        """One CSV row.

        Columns 1-11 are the battery_version 1 contract, unchanged, so
        every existing parser and every committed run stays readable.
        battery_version 2 appends the per-trial quality columns:
        ``sigma_g`` (the trial's own uncertainty), ``drift_g`` (creep
        removed by extrapolating the pre-action bracket), ``shock_g``
        (mechanical-shock steps removed) and ``retries`` /``quality``.
        """
        self._emit("CSV", block, "{:.1f}".format(tilt), phase, trial,
                   action, "{:.0f}".format(rpm) if rpm else "",
                   _fmt_g(before), _fmt_g(after), _fmt_g(delta), flag,
                   self._elapsed_ms(),
                   _fmt_g(meas.sigma_g) if meas is not None else "",
                   _fmt_g(meas.drift_g) if meas is not None else "",
                   _fmt_g(meas.shock_g) if meas is not None else "",
                   retries,
                   meas.quality() if meas is not None else "")

    def _emit_summary(self, block, tilt, phase, values):
        n, mean, std, sem, lo, hi = sample_stats(values)
        self._emit("SUM", block, "{:.1f}".format(tilt), phase, n,
                   _fmt_g(mean), _fmt_g(std), _fmt_g(sem), _fmt_g(lo),
                   _fmt_g(hi))

    def _prompt(self, message, default=""):
        """Show ``message``; return the operator's answer or ``default``.

        Attended runs block on the keyboard; unattended runs emit the
        PROMPT line (so the capture log shows the state) and continue
        with ``default`` immediately.
        """
        self._emit("PROMPT", message)
        if not self.attended:
            return default
        line = self._input_line()
        return (line or "").strip().lower()

    def _prompt_or_raise(self, message, default=""):
        ans = self._prompt(message, default)
        if ans == "abort":
            raise AbortRun("operator abort")
        if ans == "skip":
            raise SkipBlock("operator skip")
        return ans

    def _move_tilt(self, tilt_deg):
        if self._tilt == tilt_deg:
            return
        self.servo.move_to(tilt_deg * PLATE_PER_TILT)
        self._tilt = tilt_deg
        self._sleep_ms(self.tilt_settle_ms)

    def _park_tilt(self):
        """Return the tube to the parked (horizontal) tilt.

        Runs unconditionally at the end of ``run_all`` -- including
        after an abort or a scale failure -- so the rig is always left
        at a known angle for the operator swapping the next auger.
        Block G hands the servo back with ``self._tilt`` unknown, so the
        move is forced rather than skipped on the cached value.
        """
        self._tilt = None
        try:
            self._move_tilt(PARK_TILT_DEG)
        except Exception as exc:                    # pragma: no cover
            self.log("[battery] could not park tilt at {} deg: {}".format(
                PARK_TILT_DEG, exc))
            return
        self._emit("META", "park_tilt_deg", "{:.1f}".format(PARK_TILT_DEG))

    def _await_frames(self, timeout_ms=25000):
        """Wait out a balance that has gone quiet; ``None`` if it stays so.

        A refused A&D command leaves this balance emitting nothing for
        roughly 19 s.  That is a recoverable pause, not a fault, so it
        gets waited out rather than escalated.
        """
        waited = 0
        while True:
            try:
                return self._bracket()
            except balance_filter.BalanceSilent:
                if waited >= timeout_ms:
                    return None
                self._sleep_ms(1000)
                waited += 1000 + self.bracket_n * self.bracket_ms

    def _tare(self):
        """Establish the zero for the next block -- best effort, not required.

        The A&D balance silently refuses a tare while it considers
        itself unstable, and then emits nothing at all for ~19 s.  In a
        working lab it may *never* report stable -- only 2 % of frames
        were stable during the 2026-08-20 11:44 survey -- so version 1
        read that silence as ``scale-unreadable`` and aborted the run.

        Nothing downstream needs the displayed value to be zero: every
        measurement in this battery is a difference between two bracket
        fits, so a stale zero cancels exactly.  The tare's only real job
        is keeping the gross load inside the balance's capacity, so it
        is attempted when the balance looks willing, skipped when it
        does not, and never allowed to stop a run.
        """
        before = self._await_frames()
        if before is None:
            self._emit("META", "tare", "balance-silent")
            return
        gross = before.value_at(before.mid_t_ms)
        if gross >= CAPACITY_WARN_G:
            self._prompt_or_raise(
                "balance reads {:.1f} g gross, near its {:.0f} g "
                "capacity -- empty the collection vessel, then Enter "
                "('skip'/'abort')".format(gross, CAPACITY_G))
        if before.n_stable == 0:
            # Sending it now would be refused and cost ~19 s of silence.
            self._emit("META", "tare", "skipped-unstable")
            self._sleep_ms(self.settle_ms)
            return
        self.scale.zero()
        self._sleep_ms(self.settle_ms)
        after = self._await_frames()
        if after is None:
            self._emit("META", "tare", "silent-after-tare")
            return
        moved = abs(gross) - abs(after.value_at(after.mid_t_ms))
        self._emit("META", "tare",
                   "ok" if moved > 0.5 * abs(gross) else "refused")

    # -- measurement ---------------------------------------------------

    def _bracket(self, settle_ms=0):
        """One actuator-gated window of scale samples.

        ``settle_ms`` replaces a blind post-action wait with sampling.
        The auger has already stopped, so the settle window is
        actuator-gated too: a bench knock landing in it is still
        provably not powder.  Sampling through it rather than sleeping
        through it shrinks the window in which a shock is
        indistinguishable from powder down to the action itself
        (~2 s for one revolution), where the survey puts the
        environment's median contribution at 0.70 mg.

        Deliberately built from instantaneous (``Q``) frames rather than
        from ``read_stable``.  In a working lab the balance may never
        assert ``ST`` -- that is exactly what aborted the 2026-08-20
        pre-flight with ``scale-unreadable`` -- yet its ``US`` frames
        carry perfectly good numbers, and a fitted window of them beats
        a single stable frame: it also yields the creep rate and an
        uncertainty.
        """
        settle_n = int(settle_ms // self.bracket_ms) if settle_ms else 0
        bracket = balance_filter.collect(
            self.scale, n=self.bracket_n, interval_ms=self.bracket_ms,
            sleep_ms=self._sleep_ms, ticks_ms=self._ticks_ms,
            shock_g=self.shock_g, max_resid_g=self.max_resid_g,
            settle_n=settle_n)
        self.env["brackets"] += 1
        if bracket.steps:
            self.env["shock_events"] += len(bracket.steps)
            self.env["shock_total_g"] += bracket.step_total_g
        if bracket.unsettled:
            self.env["unsettled_brackets"] += 1
        return bracket

    def _quiet_bracket(self):
        """Wait for an undisturbed bracket rather than failing on noise.

        96 % of 5 s windows in the 2026-08-20 survey were inside 2 mg,
        so a quiet window normally arrives at once; when the room stays
        busy the best available bracket is used and the trial carries
        its quality flag, which is far better than aborting the run.
        """
        failures = 0
        while True:
            try:
                bracket, attempts, quiet = balance_filter.quiet_bracket(
                    self.scale, tries=self.quiet_tries, n=self.bracket_n,
                    interval_ms=self.bracket_ms, sleep_ms=self._sleep_ms,
                    ticks_ms=self._ticks_ms, shock_g=self.shock_g,
                    max_resid_g=self.max_resid_g)
            except balance_filter.BalanceSilent as exc:
                # A genuinely silent or overloaded balance is a real
                # fault -- unlike mere noise, no amount of waiting fixes
                # it -- so this is still the path that stops the block.
                failures += 1
                if failures >= self.max_read_retries:
                    raise SkipBlock("scale reads failing: {}".format(exc))
                self._prompt_or_raise(
                    "scale silent or overloaded -- clear the problem "
                    "(empty the cup if full, check the balance is on and "
                    "reading in g), then Enter to re-tare and retry, "
                    "'skip' for next block, 'abort'")
                self._tare()
                continue
            self.env["brackets"] += attempts
            if attempts > 1:
                self.env["quiet_waits"] += 1
            if bracket.steps:
                self.env["shock_events"] += len(bracket.steps)
                self.env["shock_total_g"] += bracket.step_total_g
            if bracket.unsettled:
                self.env["unsettled_brackets"] += 1
            return bracket

    def _read_required(self):
        """Best available settled value in grams (drift-corrected fits)."""
        return self._quiet_bracket().value_at(self._ticks_ms())

    def _delta(self, before, after):
        meas = balance_filter.Delta(before, after,
                                    drift_correct=self.drift_correct,
                                    max_extrap_s=balance_filter.MAX_EXTRAP_S)
        self.env["drift_corrected_g"] += abs(meas.drift_g)
        return meas

    def _measured(self, action_fn, block=None, tilt=None, phase=None,
                  trial=None):
        """Bracket, act, settle, bracket -- retrying a disturbed trial.

        Returns ``(before_g, after_g, meas, retries)``.  ``before_g`` and
        ``after_g`` are the fitted bracket values, so the legacy CSV
        columns keep meaning what they always did; ``meas`` carries the
        drift correction, the removed shocks and the uncertainty.

        A trial whose *after* bracket is disturbed is re-measured rather
        than kept: the shock happened while the powder was already in
        the cup, so a fresh action measures cleanly, and the discarded
        attempt is emitted as a RETRY row so nothing is hidden.  Each
        attempt is independently bracketed, so no mass is double
        counted -- a retry costs one more actuation, not accuracy.
        """
        retries = 0
        while True:
            before = self._quiet_bracket()
            action_fn()
            after = self._bracket(settle_ms=self.settle_ms)
            meas = self._delta(before, after)
            # Retry on a shock only, for the same reason quiet_bracket
            # waits on a shock only: a shock is a transient a fresh
            # measurement escapes, whereas re-measuring into steady
            # jitter just spends powder to get the same uncertainty.
            if (not after.shocked or retries >= self.max_trial_retries
                    or self.max_trial_retries <= 0):
                break
            self._emit("RETRY", block or "", "" if tilt is None
                       else "{:.1f}".format(tilt), phase or "",
                       "" if trial is None else trial, after.quality(),
                       _fmt_g(meas.shock_g), _fmt_g(meas.delta_g),
                       self._elapsed_ms())
            retries += 1
            self.env["retries"] += 1
        if meas.disturbed:
            self.env["disturbed_trials"] += 1
        return meas.baseline_g, meas.after_g, meas, retries

    def _stall_gate(self, streak, block, tilt):
        """After MAX_STALLS consecutive lowflow rows, check the hopper.

        Returns True when stall counting should continue (operator
        refilled), False when the operator accepted low flow as real
        data (``keep``, the unattended default: for this battery,
        no-flow IS data).
        """
        ans = self._prompt_or_raise(
            "{} consecutive trials moved <{} g (block {}, tilt {}) -- "
            "hopper empty?  Refill and press Enter to continue, 'keep' "
            "to accept low flow as this powder's behaviour, 'skip'/"
            "'abort'".format(streak, self.min_flow_g, block, tilt),
            default="keep")
        return ans != "keep"

    # -- blocks --------------------------------------------------------

    def _block_a_baseline(self):
        tilt = BASELINE_TILT
        self._move_tilt(tilt)
        self._tare()
        deltas = []
        previous = self._quiet_bracket()
        for i in range(self.baseline_reads):
            self._sleep_ms(self.settle_ms)
            current = self._bracket()
            meas = self._delta(previous, current)
            self._emit_trial("A", tilt, BASELINE, i, "", 0,
                             meas.baseline_g, meas.after_g, meas.delta_g,
                             meas=meas)
            deltas.append(meas.delta_g)
            previous = current
        self._emit_summary("A", tilt, BASELINE, deltas)

    def _block_b_hold(self):
        for tilt in self.tilts_deg:
            self._move_tilt(tilt)
            self._tare()
            before = self._quiet_bracket()
            after = self._bracket(settle_ms=int(self.hold_s * 1000))
            meas = self._delta(before, after)
            self._emit_trial("B", tilt, HOLD, 0, self.hold_s, 0,
                             meas.baseline_g, meas.after_g, meas.delta_g,
                             meas=meas)

    def _block_c_rotation(self):
        self.stepper.set_speed(self.rotation_rpm)
        for tilt in self.tilts_deg:
            self._move_tilt(tilt)
            self._prompt_or_raise(
                "block C at tilt {} -- empty the collection cup if it is "
                "getting full, then Enter ('skip'/'abort')".format(tilt))
            self._tare()
            deltas = []
            streak = 0
            stall_check = self.min_flow_g > 0
            for trial in range(self.rotation_trials):
                before, after, meas, retries = self._measured(
                    lambda: self.stepper.rotate_degrees(
                        self.rotation_step_deg),
                    block="C", tilt=tilt, phase=ROTATION, trial=trial)
                delta = meas.delta_g
                lowflow = stall_check and delta < self.min_flow_g
                self._emit_trial("C", tilt, ROTATION, trial,
                                 self.rotation_step_deg, self.rotation_rpm,
                                 before, after, delta,
                                 "lowflow" if lowflow else "",
                                 meas=meas, retries=retries)
                deltas.append(delta)
                streak = streak + 1 if lowflow else 0
                if streak >= self.max_stalls:
                    if not self._stall_gate(streak, "C", tilt):
                        stall_check = False
                    streak = 0
            self._emit_summary("C", tilt, ROTATION, deltas)

    def _block_d_speed(self):
        tilt = SPEED_TILT
        self._move_tilt(tilt)
        self._tare()
        deltas = []
        for trial, rpm in enumerate(self.speed_rpms):
            before = self._quiet_bracket()
            spin_ms = self.speed_revs / rpm * 60.0 * 1000
            self.stepper.run_at_rpm(rpm)
            waited_ms = 0
            misses = 0
            try:
                while waited_ms < spin_ms:
                    self._sleep_ms(self.speed_poll_ms)
                    waited_ms += self.speed_poll_ms
                    self.stepper.keep_alive()
                    reading = self.scale.read()
                    if (reading is None or reading.overload
                            or reading.grams is None):
                        misses += 1
                        if misses >= 20:
                            self.log("[battery] scale went quiet during "
                                     "the speed sweep")
                            break
                        continue
                    misses = 0
                    self._emit("POLL", "D", "{:.1f}".format(tilt),
                               "{:.0f}".format(rpm), self._elapsed_ms(),
                               _fmt_g(reading.grams),
                               1 if reading.stable else 0)
            finally:
                self.stepper.stop()
            after = self._bracket(settle_ms=self.settle_ms)
            meas = self._delta(before, after)
            self._emit_trial("D", tilt, SPEED, trial, self.speed_revs,
                             rpm, meas.baseline_g, meas.after_g,
                             meas.delta_g, meas=meas)
            deltas.append(meas.delta_g)
        self._emit_summary("D", tilt, SPEED, deltas)

    def _burst_block(self, block, phase, action_fn, action_label):
        """Shared shape of Blocks E and F: refeed + burst per trial."""
        self.stepper.set_speed(self.rotation_rpm)
        for tilt in self.tap_tilts:
            self._move_tilt(tilt)
            self._tare()
            refeed_deltas = []
            burst_deltas = []
            streak = 0
            stall_check = self.min_flow_g > 0
            for trial in range(self.tap_trials):
                before, after, meas, retries = self._measured(
                    lambda: self.stepper.rotate_degrees(self.refeed_deg),
                    block=block, tilt=tilt, phase=REFEED, trial=trial)
                refeed_delta = meas.delta_g
                lowflow = stall_check and refeed_delta < self.min_flow_g
                self._emit_trial(block, tilt, REFEED, trial,
                                 self.refeed_deg, self.rotation_rpm,
                                 before, after, refeed_delta,
                                 "lowflow" if lowflow else "",
                                 meas=meas, retries=retries)
                refeed_deltas.append(refeed_delta)
                streak = streak + 1 if lowflow else 0
                if streak >= self.max_stalls:
                    if not self._stall_gate(streak, block, tilt):
                        stall_check = False
                    streak = 0
                before, after, meas, retries = self._measured(
                    action_fn, block=block, tilt=tilt, phase=phase,
                    trial=trial)
                delta = meas.delta_g
                self._emit_trial(block, tilt, phase, trial, action_label,
                                 0, before, after, delta,
                                 meas=meas, retries=retries)
                burst_deltas.append(delta)
            self._emit_summary(block, tilt, REFEED, refeed_deltas)
            self._emit_summary(block, tilt, phase, burst_deltas)

    def _block_e_tap(self):
        self._burst_block(
            "E", TAP,
            lambda: self.tap.tap(self.taps_per_point, TAP_ON_MS,
                                 TAP_OFF_MS),
            self.taps_per_point)

    def _block_f_vib(self):
        if self.vib is None:
            self._emit("META", "vib", "unavailable")
            self.log("[battery] vibration driver unavailable -- "
                     "skipping block F")
            return

        def bursts():
            for _ in range(self.vib_bursts):
                self.vib.buzz()
                self._sleep_ms(200)

        self._burst_block("F", VIB, bursts, self.vib_bursts)

    def _block_g_dose(self):
        if self.doser is None:
            self._emit("META", "dose", "unavailable")
            self.log("[battery] no three-phase doser wired -- "
                     "skipping block G")
            return
        self._prompt_or_raise(
            "block G (three-phase doses): EMPTY the collection cup now, "
            "then Enter ('skip'/'abort')")
        for n in range(self.dose_repeats):
            result = self.doser.dose(self.dose_target_g)
            cycles = ";".join("{}:{}".format(name, count)
                              for name, count in result.phase_cycles)
            self._emit("DOSE", n, _fmt_g(result.target_g),
                       _fmt_g(result.dispensed_g),
                       _fmt_g(result.dispensed_g - result.target_g),
                       result.status, "{:.1f}".format(result.elapsed_s),
                       "{:.2f}".format(result.auger_deg / 360.0),
                       result.taps, cycles, self._elapsed_ms())
            self._tilt = None    # the doser moved the servo itself
            if n + 1 < self.dose_repeats:
                self._prompt_or_raise(
                    "dose {} done -- empty the cup for the next dose, "
                    "then Enter ('skip'/'abort')".format(n + 1))

    # -- entry ---------------------------------------------------------

    def run_all(self):
        self._t0 = self._ticks_ms()
        self._emit("RUN", "BEGIN")
        if self.powder_id:
            self._emit("META", "powder_id", self.powder_id)
        for key, value in (
                ("battery_version", BATTERY_VERSION),
                ("blocks", self.blocks),
                ("tilts_deg", ";".join(str(t) for t in self.tilts_deg)),
                ("baseline_reads", self.baseline_reads),
                ("hold_s", self.hold_s),
                ("rotation_trials", self.rotation_trials),
                ("rotation_step_deg", self.rotation_step_deg),
                ("rotation_rpm", self.rotation_rpm),
                ("speed_rpms", ";".join(str(r) for r in self.speed_rpms)),
                ("speed_revs", self.speed_revs),
                ("tap_tilts", ";".join(str(t) for t in self.tap_tilts)),
                ("tap_trials", self.tap_trials),
                ("taps_per_point", self.taps_per_point),
                ("refeed_deg", self.refeed_deg),
                ("vib_bursts", self.vib_bursts),
                ("dose_repeats", self.dose_repeats),
                ("dose_target_g", self.dose_target_g),
                ("settle_ms", self.settle_ms),
                ("min_flow_g", self.min_flow_g),
                ("bracket_n", self.bracket_n),
                ("bracket_ms", self.bracket_ms),
                ("shock_g", self.shock_g),
                ("max_resid_g", self.max_resid_g),
                ("quiet_tries", self.quiet_tries),
                ("max_trial_retries", self.max_trial_retries),
                ("drift_correct", 1 if self.drift_correct else 0),
                ("attended", 1 if self.attended else 0)):
            self._emit("META", key, value)
        for key in sorted(self.config_echo):
            self._emit("META", "config." + key, self.config_echo[key])
        runners = {
            "A": self._block_a_baseline,
            "B": self._block_b_hold,
            "C": self._block_c_rotation,
            "D": self._block_d_speed,
            "E": self._block_e_tap,
            "F": self._block_f_vib,
            "G": self._block_g_dose,
        }
        status = "ok"
        try:
            for block in self.blocks:
                if block not in runners:
                    self.log("[battery] unknown block {!r} -- "
                             "skipping".format(block))
                    continue
                self.log("[battery] block {}".format(block))
                try:
                    runners[block]()
                except SkipBlock as exc:
                    self.log("[battery] skipping block {}: {}".format(
                        block, exc))
        except AbortRun as exc:
            self.log("[battery] run aborted: {}".format(exc))
            status = "aborted"
        except KeyboardInterrupt:
            status = "interrupted"
            raise
        finally:
            self._park_tilt()
            self._emit_environment()
            self._emit("RUN", "END", status)
        return status

    def _emit_environment(self):
        """Report the artifact rate as data, not as a silent correction.

        A run that quietly subtracts shocks and creep looks identical to
        a run in a perfectly quiet room.  These rows are what let the
        analysis say how much of a result rests on corrected data.
        """
        for key in sorted(self.env):
            value = self.env[key]
            self._emit("META", "env." + key,
                       "{:.4f}".format(value) if isinstance(value, float)
                       else value)


# config.py keys echoed as META rows for provenance.
CONFIG_ECHO_KEYS = (
    "STEPPER_SPEED_RPM", "STEPPER_MICROSTEPS", "STEPPER_FULL_STEPS_REV",
    "STEPPER_ACCEL_REV_PER_S2", "TAP_ON_MS", "TAP_OFF_MS", "TAP_PWM_DUTY",
    "SERVO_SPEED_DEG_PER_S", "SCALE_BAUD", "SCALE_BITS", "SCALE_PARITY",
    "SCALE_STOP", "SCALE_STABLE_TIMEOUT_MS",
)


def run(powder_id=None, attended=True, **overrides):
    """Bring up the rig and run the battery (Pico entry point).

    Needs the PR #100 driver stack (``config.py``, ``tic.py``,
    ``scale.py``) and PR #124's ``main_three_phase.py`` next to this
    file.  The drivers come from ``main_three_phase`` so every value is
    true auger/plate units, and Block G runs its ``ThreePhaseDoser``
    with the frozen ``DOSE_PHASES`` / ``DOSE_THRESHOLDS`` above.
    """
    import config
    import main_three_phase as m3p

    stepper = m3p.Stepper()
    tap = m3p.Tap()
    servo = m3p.Servo()
    balance = m3p.Scale()
    doser = m3p.ThreePhaseDoser(
        stepper, tap, servo, balance, config,
        phases=[dict(p) for p in DOSE_PHASES],
        thresholds=list(DOSE_THRESHOLDS),
        timeout_s=DOSE_TIMEOUT_S)
    vib = None
    try:
        import main as rig_main            # resident PR #100 firmware
        candidate = rig_main.Vibration()
        if getattr(candidate, "_available", False):
            vib = candidate
    except Exception as exc:
        print("[battery] vibration bring-up failed ({}); "
              "block F will be skipped".format(exc))
    echo = {k: getattr(config, k) for k in CONFIG_ECHO_KEYS
            if hasattr(config, k)}
    battery = Battery(
        stepper, tap, servo, balance, vib=vib, doser=doser,
        input_line=sys.stdin.readline if attended else None,
        attended=attended, config_echo=echo,
        stable_timeout_ms=getattr(config, "SCALE_STABLE_TIMEOUT_MS", 10000),
        powder_id=powder_id, **overrides)
    try:
        return battery.run_all()
    finally:
        # Never leave the motor energised or the solenoid latched.
        try:
            stepper.stop()
        except Exception:
            pass
        try:
            stepper.enable(False)
        except Exception:
            pass
        try:
            tap._off()
        except Exception:
            pass
