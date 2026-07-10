"""ALTERNATIVE MAIN -- three-phase powder dosing (Layer 1 rough draft).

This is an *alternative* to the two-phase ``main.py`` from PR #100: the
same bench-rig framework (Tic T500 auger stepper, DRV8871 tap solenoid,
dual dispensing-angle servos, A&D HR-100A scale, one-line serial REPL),
but the closed-loop dose is restructured into THREE distinct phases
(issue #123 / PR #124, "Layer 1" of the Edison-recommended
architecture):

1. **Phase 1 -- bulk**: get most of the way to the goal mass fast.
   Steeper dispensing angle, large auger rotations per cycle, short
   settle.  Runs until fewer than ``PHASE1_EXIT_REMAINING_G`` grams
   remain until the goal.
2. **Phase 2 -- fine dispensing**: small incremental auger rotations
   with a scale reading (pause) after every increment.  Runs until
   fewer than ``PHASE2_EXIT_REMAINING_G`` grams remain.
3. **Phase 3 -- tap-wait cycles**: solenoid tap bursts, each followed
   by a settle wait and a stable scale reading, until the measured
   mass is within ``PHASE3_TOLERANCE_G`` of the goal.

Every phase runs the same generic cycle -- [rotate?] [tap?] settle
measure print -- driven by its own parameter dict, so any phase can mix
rotation and tapping (e.g. cohesive powders that need taps during bulk:
set ``taps_per_cycle`` on phase 1).  Objective values (mass so far,
grams to go, gain this cycle, elapsed time) are printed at every cycle
pause and a summary is printed between phases.

The vibrating haptic motor (DRV2605L) is intentionally NOT used or
initialised here -- per the bench plan it stays out of the control code
for now.

Tuning
------
All three-phase knobs live at the top of THIS file (the base rig
config -- pins, servo range, scale serial -- still comes from
``config.py``).  Two ways to change them:

* Edit this file and re-run via MicroPico (edit-save-run, seconds), or
* live at the REPL without re-uploading::

      set 1 angle_deg 60        # phase 1 dispensing angle -> 60 deg
      set 2 rotation_deg 20     # phase 2 rotation per cycle -> 20 deg
      set 2 rotation_rpm 20     # phase 2 rotation speed -> 20 RPM
      set t1 0.4                # bulk -> fine at 0.4 g until goal
      set t3 0.002              # finish tolerance +/- 2 mg

Deployment
----------
Upload alongside the PR #100 firmware set -- this file needs
``config.py``, ``tic.py`` and ``scale.py`` next to it (it does NOT need
``dosing.py`` or ``drv2605.py``).  MicroPico "Run current file" runs it
directly; to make it the power-on program instead of the two-phase
``main.py``, upload it renamed as ``main.py``.

Wire-on commands (one per line over USB-serial):
    h            help
    s            print rig state, thresholds and per-phase parameters
    d            dispense (rotate auger STEPPER_DISPENSE_DEG)
    r <deg>      rotate auger by <deg> degrees (signed)
    t            tap (TAP_COUNT solenoid pulses)
    a <deg>      smoothly move dispensing-angle servos to <deg>
    p <name>     servos to a preset (horizontal/tilt/vertical/tip)
    w            read the scale (one weighing datum)
    z            re-zero (tare) the scale
    g <grams>    three-phase closed-loop dose to <grams>
    set ...      change a phase parameter or threshold (see Tuning)
    !            emergency stop -- de-energise everything
"""

import sys
import time

import config
import scale as scale_mod
import tic

try:
    from machine import Pin, PWM, UART
    _ON_HARDWARE = True
except ImportError:
    # CPython (e.g. the sim/ tests importing ThreePhaseDoser); the
    # hardware classes below are simply never instantiated.
    _ON_HARDWARE = False


# =========================================================================
# THREE-PHASE DOSE PARAMETERS -- the knobs this file exists for.
#
# All mass thresholds are "grams remaining until the goal mass": phase N
# keeps cycling while (goal - measured) is above its exit threshold, then
# hands over to the next phase.  A phase whose threshold is already met
# when it starts is skipped entirely (so a 0.3 g dose with the defaults
# below never runs the bulk phase).
#
# NOTE: keep each rotation phase's per-cycle throughput (rotation_deg
# x powder g/rev) comfortably below the gap between its exit threshold
# and the goal, or a single cycle can blow straight past the target --
# this rough draft has no online g/rev estimator (unlike dosing.py).
# =========================================================================

# --- Phase-shift thresholds (grams until goal mass) ----------------------
PHASE1_EXIT_REMAINING_G = 0.500   # bulk -> fine when <= this many g to go
PHASE2_EXIT_REMAINING_G = 0.050   # fine -> tap  when <= this many g to go
PHASE3_TOLERANCE_G      = 0.005   # done when within +/- this of the goal

# --- Global safety limits ------------------------------------------------
DOSE_TIMEOUT_S = 600              # hard wall-clock limit for one dose

# --- Per-phase parameters ------------------------------------------------
# Every phase understands the same keys:
#   angle_deg        dispensing angle (servo) held for the whole phase
#   rotation_deg     auger rotation per cycle (0 = no rotation)
#   rotation_rpm     auger speed while this phase rotates
#   taps_per_cycle   solenoid taps per cycle (0 = no tapping)
#   tap_on_ms/off_ms solenoid timing for this phase's taps
#   settle_ms        wait after actuating before trusting the scale
#   min_gain_g       a cycle gaining less than this counts as a stall
#   max_stall_cycles consecutive stalls before nudging/aborting
#   stall_nudge_deg  auger nudge to re-feed the tube lip on a stall
#                    (0 = don't nudge, abort instead; mainly for phase 3,
#                    where taps only deliver powder already at the lip)
#   max_nudges       stall-nudge budget for the phase
#   max_cycles       safety budget: abort the dose if exceeded
#
# Angles are servo degrees; per config.SERVO_PRESETS the bench mapping is
# horizontal=0, tilt=45, vertical=90, tip=135.  Bench observation
# (PR #124): steeper/more-vertical angles dispense a lot more per action,
# horizontal is the most precise -- hence steep bulk, horizontal taps.
# All defaults are UNTUNED starting guesses from the salt demos.

PHASE1_BULK = {
    "name": "bulk",
    "angle_deg": 90.0,        # vertical -- fast flow
    "rotation_deg": 360.0,    # full turn per cycle
    "rotation_rpm": 120.0,
    "taps_per_cycle": 0,      # some powders may want taps here too
    "tap_on_ms": 60,
    "tap_off_ms": 150,
    "settle_ms": 800,         # bulk can trust a rougher reading
    "min_gain_g": 0.002,
    "max_stall_cycles": 5,    # 5 dry cycles = empty hopper / jam -> abort
    "stall_nudge_deg": 0.0,
    "max_nudges": 0,
    "max_cycles": 100,
}

PHASE2_FINE = {
    "name": "fine",
    "angle_deg": 45.0,        # tilt -- moderate flow
    "rotation_deg": 30.0,     # small increment, measure every pause
    "rotation_rpm": 30.0,
    "taps_per_cycle": 0,
    "tap_on_ms": 60,
    "tap_off_ms": 150,
    "settle_ms": 1500,        # HR-A needs ~1.5 s for a stable reading
    "min_gain_g": 0.0005,
    "max_stall_cycles": 5,
    "stall_nudge_deg": 0.0,
    "max_nudges": 0,
    "max_cycles": 150,
}

PHASE3_TAP = {
    "name": "tap",
    "angle_deg": 0.0,         # horizontal -- most precise
    "rotation_deg": 0.0,      # no auger; taps only
    "rotation_rpm": 0.0,
    "taps_per_cycle": 2,
    "tap_on_ms": 60,
    "tap_off_ms": 150,
    "settle_ms": 1500,
    "min_gain_g": 0.0002,
    "max_stall_cycles": 3,    # 3 dry bursts = tube lip empty ...
    "stall_nudge_deg": 5.0,   # ... so nudge the auger to re-feed it
    "max_nudges": 10,
    "max_cycles": 150,
}

PHASES = (PHASE1_BULK, PHASE2_FINE, PHASE3_TAP)
THRESHOLDS = (PHASE1_EXIT_REMAINING_G, PHASE2_EXIT_REMAINING_G,
              PHASE3_TOLERANCE_G)


# ---------------------------------------------------------------------------
# Low-level driver helpers (same framework as PR #100's main.py).
# ---------------------------------------------------------------------------

def _out(pin_num, value=0):
    return Pin(pin_num, Pin.OUT, value=value)


def _pwm(pin_num, freq, duty=0.0):
    pwm = PWM(Pin(pin_num))
    pwm.freq(freq)
    pwm.duty_u16(int(max(0.0, min(1.0, duty)) * 65535))
    return pwm


# ---------------------------------------------------------------------------
# Stepper (Pololu Tic T500 over TTL serial -> NEMA-11).  Identical to the
# PR #100 main.py class; see there for the design notes (shadow position,
# estimated-time waits, idle de-energise).
# ---------------------------------------------------------------------------

class Stepper:
    def __init__(self):
        self.uart = UART(config.TIC_UART_ID, baudrate=config.TIC_BAUD,
                         tx=Pin(config.PIN_TIC_TX), rx=Pin(config.PIN_TIC_RX),
                         timeout=config.TIC_READ_TIMEOUT_MS)
        self.tic = tic.TicSerial(self.uart)
        self.steps_per_rev = (config.STEPPER_FULL_STEPS_REV
                              * config.STEPPER_MICROSTEPS)
        self._position = 0
        self._rpm = float(config.STEPPER_SPEED_RPM)
        self._enabled = False
        self._configure()

    def _accel_units(self):
        usteps_per_s2 = config.STEPPER_ACCEL_REV_PER_S2 * self.steps_per_rev
        return max(1, int(usteps_per_s2 * 100))

    def _configure(self):
        t = self.tic
        t.exit_safe_start()
        t.clear_driver_error()
        t.set_step_mode(config.STEPPER_MICROSTEPS)
        self.set_speed(config.STEPPER_SPEED_RPM)
        accel = self._accel_units()
        t.set_max_accel(accel)
        t.set_max_decel(accel)
        t.halt_and_set_position(0)
        self._position = 0
        if self._idle_deenergize():
            t.deenergize()

    @staticmethod
    def _idle_deenergize():
        return getattr(config, "STEPPER_IDLE_DEENERGIZE", True)

    def set_speed(self, rpm):
        self._rpm = float(rpm)
        usteps_per_s = rpm / 60.0 * self.steps_per_rev
        self.tic.set_max_speed(max(1, int(usteps_per_s * 10000)))

    def enable(self, on=True):
        if on:
            self.tic.energize()
            self.tic.exit_safe_start()
        else:
            self.tic.deenergize()
        self._enabled = on

    def rotate_degrees(self, degrees):
        signed = degrees * (1 if config.STEPPER_DIRECTION >= 0 else -1)
        delta = int(round(signed / 360.0 * self.steps_per_rev))
        if delta == 0:
            return
        if not self._enabled:
            self.enable(True)
        self._position += delta
        self.tic.set_target_position(self._position)
        self._wait_estimated_time(delta)
        if self._idle_deenergize():
            self.enable(False)

    def _wait_estimated_time(self, delta):
        usteps_per_s = max(1.0, self._rpm / 60.0 * self.steps_per_rev)
        est_s = abs(delta) / usteps_per_s + 0.2
        deadline = time.ticks_add(time.ticks_ms(), int(est_s * 1000) + 2000)
        while time.ticks_diff(deadline, time.ticks_ms()) > 0:
            try:
                self.tic.reset_command_timeout()
            except Exception:
                pass
            time.sleep_ms(50)


# ---------------------------------------------------------------------------
# Tap (DRV8871 + solenoid).  Same as PR #100, plus optional per-call
# on/off timing so each dose phase can tap with its own rhythm.
# ---------------------------------------------------------------------------

class Tap:
    def __init__(self):
        self.in1 = _pwm(config.PIN_SOL_IN1, freq=20_000, duty=0.0)
        self.in2 = _out(config.PIN_SOL_IN2, 0)

    def _on(self, duty):
        self.in2.value(0)
        self.in1.duty_u16(int(max(0.0, min(1.0, duty)) * 65535))

    def _off(self):
        self.in1.duty_u16(0)

    def tap(self, count=None, on_ms=None, off_ms=None):
        n = config.TAP_COUNT if count is None else count
        on = config.TAP_ON_MS if on_ms is None else int(on_ms)
        off = config.TAP_OFF_MS if off_ms is None else int(off_ms)
        for _ in range(n):
            self._on(config.TAP_PWM_DUTY)
            time.sleep_ms(on)
            self._off()
            time.sleep_ms(off)


# ---------------------------------------------------------------------------
# Dispensing-angle servos (dual, mirrored, smooth-ramped).  Identical to
# the PR #100 main.py class; see there for the design notes.
# ---------------------------------------------------------------------------

class Servo:
    PERIOD_US = 20_000  # 50 Hz

    def __init__(self):
        self.pwm1 = _pwm(config.PIN_SERVO_SIG, freq=50, duty=0.0)
        self.pwm2 = _pwm(config.PIN_SERVO_SIG2, freq=50, duty=0.0)
        self.angle = float(config.SERVO_DEFAULT_DEG)
        self._write_angle(self.angle)
        self.move_to(config.SERVO_DEFAULT_DEG)

    def _mirror(self, angle_deg):
        if config.SERVO2_INVERT:
            return ((config.SERVO_MIN_ANGLE_DEG + config.SERVO_MAX_ANGLE_DEG)
                    - angle_deg)
        return angle_deg

    def _angle_to_duty(self, angle_deg):
        span = config.SERVO_MAX_ANGLE_DEG - config.SERVO_MIN_ANGLE_DEG
        frac = ((angle_deg - config.SERVO_MIN_ANGLE_DEG) / span
                if span else 0)
        pulse_us = (config.SERVO_MIN_PULSE_US
                    + frac * (config.SERVO_MAX_PULSE_US
                              - config.SERVO_MIN_PULSE_US))
        return int(pulse_us / self.PERIOD_US * 65535)

    def _write_angle(self, angle_deg):
        self.pwm1.duty_u16(self._angle_to_duty(angle_deg))
        self.pwm2.duty_u16(self._angle_to_duty(self._mirror(angle_deg)))

    def move_to(self, angle_deg):
        target = max(config.SERVO_MIN_ANGLE_DEG,
                     min(config.SERVO_MAX_ANGLE_DEG, angle_deg))
        speed = float(config.SERVO_SPEED_DEG_PER_S)
        if speed <= 0:
            self._write_angle(target)
            self.angle = target
            return
        update_hz = max(1, config.SERVO_UPDATE_HZ)
        step_deg = speed / update_hz
        dt = 1.0 / update_hz
        delta = target - self.angle
        if abs(delta) <= step_deg:
            self._write_angle(target)
            self.angle = target
            return
        step = step_deg if delta > 0 else -step_deg
        while abs(target - self.angle) > step_deg:
            self.angle += step
            self._write_angle(self.angle)
            time.sleep(dt)
        self._write_angle(target)
        self.angle = target


# ---------------------------------------------------------------------------
# Scale (A&D HR-100A over RS-232C on UART0) -- same bring-up as PR #100.
# ---------------------------------------------------------------------------

_SCALE_CONFIG_KEYS = (
    "SCALE_UART_ID", "PIN_SCALE_TX", "PIN_SCALE_RX",
    "SCALE_BAUD", "SCALE_BITS", "SCALE_PARITY", "SCALE_STOP",
)


class Scale(scale_mod.AndScale):
    def __init__(self):
        uart = scale_mod.open_uart(config, UART, Pin)
        super().__init__(uart,
                         response_timeout_ms=config.SCALE_RESPONSE_TIMEOUT_MS)


# ---------------------------------------------------------------------------
# Three-phase dose controller.
#
# Hardware-agnostic like dosing.Doser: talks to duck-typed ``stepper``
# (rotate_degrees / set_speed), ``tap`` (tap(count, on_ms, off_ms)),
# ``servo`` (move_to) and ``scale`` (read_stable / zero), so the same
# loop runs on the Pico and against sim/sim_rig.py under CPython.
# ---------------------------------------------------------------------------

class DoseResult:
    OK = "ok"
    TIMEOUT = "timeout"
    OVERSHOOT = "overshoot"
    SCALE_ERROR = "scale-error"
    STALLED = "stalled"          # no powder flow (hopper empty / lip dry)
    BUDGET = "cycle-budget"      # a phase exceeded its max_cycles

    def __init__(self, status, target_g, dispensed_g, elapsed_s,
                 phase_cycles, taps, auger_deg):
        self.status = status
        self.target_g = target_g
        self.dispensed_g = dispensed_g
        self.elapsed_s = elapsed_s
        self.phase_cycles = phase_cycles   # list of (phase name, cycles)
        self.taps = taps
        self.auger_deg = auger_deg

    @property
    def ok(self):
        return self.status == self.OK

    def __repr__(self):
        cyc = ", ".join("{}:{}".format(n, c) for n, c in self.phase_cycles)
        return ("DoseResult({s}: {d:.4f}/{t:.4f} g in {e:.1f}s; "
                "cycles {c}; {r:.2f} auger rev, {n} taps)").format(
                    s=self.status, d=self.dispensed_g, t=self.target_g,
                    e=self.elapsed_s, c=cyc or "-",
                    r=self.auger_deg / 360.0, n=self.taps)


class ThreePhaseDoser:
    def __init__(self, stepper, tap, servo, scale, cfg,
                 phases=None, thresholds=None, timeout_s=DOSE_TIMEOUT_S,
                 log=print, monotonic=None, sleep_ms=None):
        self.stepper = stepper
        self.tap = tap
        self.servo = servo
        self.scale = scale
        self.cfg = cfg
        # Own (mutable) copies, so live `set` tuning at the REPL never
        # rewrites the module-level defaults.
        self.phases = [dict(p) for p in (phases or PHASES)]
        self.thresholds = list(thresholds or THRESHOLDS)
        self.timeout_s = timeout_s
        self.log = log
        if monotonic is None:
            monotonic = time.time
        if sleep_ms is None:
            try:
                sleep_ms = time.sleep_ms       # MicroPython
            except AttributeError:
                sleep_ms = lambda ms: time.sleep(ms / 1000.0)
        self._now = monotonic
        self._sleep_ms = sleep_ms

    @property
    def tolerance_g(self):
        return self.thresholds[-1]

    # ------------------------------------------------------------------

    def _stable_grams(self):
        """Stable reading relative to the tare, or None on scale trouble."""
        reading = self.scale.read_stable(
            timeout_ms=self.cfg.SCALE_STABLE_TIMEOUT_MS)
        if (reading is None or not reading.stable or reading.overload or
                reading.grams is None):
            return None
        if reading.unit and reading.unit != "g":
            self.log("[dose] scale reports {!r}, not grams -- press MODE "
                     "on the balance to select g".format(reading.unit))
            return None
        return reading.grams

    def _objectives(self, tag, grams, target_g, gain, t0,
                    gain_label="this cycle"):
        """One objective-values line: mass, error-to-go, gain, time."""
        self.log("{} mass {:.4f} / {:.4f} g ({:.4f} g to go, "
                 "{:+.4f} g {}), elapsed {:.1f} s".format(
                     tag, grams, target_g, max(0.0, target_g - grams),
                     gain, gain_label, self._now() - t0))

    def dose(self, target_g):
        """Three-phase dispense of ``target_g`` grams onto the tared pan."""
        t0 = self._now()
        state = {"taps": 0, "deg": 0.0}
        phase_cycles = []

        def result(status, grams):
            res = DoseResult(status, target_g, grams, self._now() - t0,
                             phase_cycles, state["taps"], state["deg"])
            self.log("[dose] done: {!r}".format(res))
            return res

        if target_g <= 0:
            return result(DoseResult.OK, 0.0)

        self.log("[dose] three-phase dose to {:.4f} g; taring scale"
                 .format(target_g))
        self.scale.zero()
        grams = self._stable_grams()
        if grams is None:
            return result(DoseResult.SCALE_ERROR, 0.0)

        for idx in range(len(self.phases)):
            p = self.phases[idx]
            exit_g = self.thresholds[idx]
            remaining = target_g - grams
            if remaining <= exit_g:
                self.log("=== phase {}/{} '{}' skipped ({:.4f} g to go is "
                         "already <= {:.4f} g threshold)".format(
                             idx + 1, len(self.phases), p["name"],
                             remaining, exit_g))
                phase_cycles.append((p["name"], 0))
                continue
            self.log("=== phase {}/{} '{}' start: {:.4f} g to go, exit at "
                     "{:.4f} g to go; angle {:.0f} deg, {:.0f} deg/cycle @ "
                     "{:.0f} rpm, {} taps/cycle, settle {} ms".format(
                         idx + 1, len(self.phases), p["name"], remaining,
                         exit_g, p["angle_deg"], p["rotation_deg"],
                         p["rotation_rpm"], p["taps_per_cycle"],
                         p["settle_ms"]))
            before_phase = grams
            grams, status, cycles = self._run_phase(
                idx + 1, p, exit_g, target_g, grams, t0, state)
            phase_cycles.append((p["name"], cycles))
            self._objectives(
                "=== phase {}/{} '{}' end ({} cycles):".format(
                    idx + 1, len(self.phases), p["name"], cycles),
                grams, target_g, grams - before_phase, t0,
                gain_label="this phase")
            if status is not None:
                self._restore_rig()
                return result(status, grams)

        self._restore_rig()
        status = DoseResult.OK
        if grams > target_g + self.tolerance_g:
            status = DoseResult.OVERSHOOT
        return result(status, grams)

    def _restore_rig(self):
        # Put the auger speed back for the manual REPL commands.  The
        # servos deliberately STAY at the last phase's angle -- no
        # surprise tilting over a full pan; move them with `a`/`p`.
        self.stepper.set_speed(self.cfg.STEPPER_SPEED_RPM)

    def _run_phase(self, num, p, exit_g, target_g, grams, t0, state):
        """Run one phase; returns (grams, abort_status_or_None, cycles)."""
        self.servo.move_to(p["angle_deg"])
        rot = float(p["rotation_deg"])
        taps_n = int(p["taps_per_cycle"])
        if rot > 0 and p["rotation_rpm"] > 0:
            self.stepper.set_speed(p["rotation_rpm"])
        if rot <= 0 and taps_n <= 0:
            self.log("[phase {} {}] no rotation and no taps configured -- "
                     "phase does nothing, skipping".format(num, p["name"]))
            return grams, None, 0

        tag = "[phase {} {}]".format(num, p["name"])
        cycles = 0
        stalls = 0
        nudges = 0
        while target_g - grams > exit_g:
            if self._now() - t0 > self.timeout_s:
                self.log(tag + " dose timeout ({} s)".format(self.timeout_s))
                return grams, DoseResult.TIMEOUT, cycles
            if cycles >= p["max_cycles"]:
                self.log(tag + " cycle budget ({}) exhausted".format(
                    p["max_cycles"]))
                return grams, DoseResult.BUDGET, cycles
            before = grams
            if rot > 0:
                self.stepper.rotate_degrees(rot)
                state["deg"] += rot
            if taps_n > 0:
                self.tap.tap(taps_n, p["tap_on_ms"], p["tap_off_ms"])
                state["taps"] += taps_n
            self._sleep_ms(int(p["settle_ms"]))
            grams = self._stable_grams()
            if grams is None:
                return before, DoseResult.SCALE_ERROR, cycles
            cycles += 1
            self._objectives(tag + " cycle {}:".format(cycles),
                             grams, target_g, grams - before, t0)
            if grams - before < p["min_gain_g"]:
                stalls += 1
                if stalls >= p["max_stall_cycles"]:
                    if p["stall_nudge_deg"] > 0 and nudges < p["max_nudges"]:
                        nudges += 1
                        self.log(tag + " lip empty; nudging auger {:.1f} deg"
                                 " (nudge {}/{})".format(
                                     p["stall_nudge_deg"], nudges,
                                     p["max_nudges"]))
                        self.stepper.rotate_degrees(p["stall_nudge_deg"])
                        state["deg"] += p["stall_nudge_deg"]
                        stalls = 0
                    else:
                        self.log(tag + " no powder flow -- hopper empty, "
                                 "jam, or nudge budget spent")
                        return grams, DoseResult.STALLED, cycles
            else:
                stalls = 0
        return grams, None, cycles


# ---------------------------------------------------------------------------
# Top-level rig + REPL
# ---------------------------------------------------------------------------

HELP = (
    "Three-phase doser commands:\n"
    "  h                    show this help\n"
    "  s                    print rig state, thresholds, phase parameters\n"
    "  d                    dispense (rotate auger STEPPER_DISPENSE_DEG)\n"
    "  r <deg>              rotate auger by <deg> (signed)\n"
    "  t                    tap (TAP_COUNT solenoid pulses)\n"
    "  a <deg>              servos to <deg>\n"
    "  p <preset>           servos to named preset\n"
    "  w                    weigh (read the scale once)\n"
    "  z                    re-zero (tare) the scale\n"
    "  g <grams>            three-phase dose to <grams>\n"
    "  set t<N> <grams>     phase-shift threshold N (g until goal);\n"
    "                       t1 bulk->fine, t2 fine->tap, t3 tolerance\n"
    "  set <N> <key> <val>  phase-N parameter, e.g. set 1 angle_deg 60\n"
    "  !                    emergency stop\n"
)


class Rig:
    def __init__(self):
        print("[rig] bringing up powder-doser test module "
              "(three-phase alternative main; no haptics)")
        self.stepper = Stepper()
        self.tap = Tap()
        self.servo = Servo()
        self.scale = self._bring_up_scale()
        self.doser = (ThreePhaseDoser(self.stepper, self.tap, self.servo,
                                      self.scale, config)
                      if self.scale is not None else None)
        print("[rig] ready -- type 'h' for help")

    def _bring_up_scale(self):
        missing = [k for k in _SCALE_CONFIG_KEYS if not hasattr(config, k)]
        if missing:
            print("[scale] config.py is missing {}; the Pico is likely "
                  "running an OLD config.py.  Re-upload ALL firmware files "
                  "(MicroPico: 'Upload project to Pico'), then soft-reset "
                  "(Ctrl+D).  Scale + dosing disabled.".format(
                      ", ".join(missing)))
            return None
        try:
            return Scale()
        except Exception as exc:
            print("[scale] unavailable ({}); scale + dosing disabled.  "
                  "Run tests/test_scale_contact.py to check the link."
                  .format(exc))
            return None

    def state(self):
        print(
            "stepper: rpm={rpm}, microsteps=1/{ms}, steps/rev={spr}, "
            "dispense_deg={dd}".format(
                rpm=config.STEPPER_SPEED_RPM,
                ms=config.STEPPER_MICROSTEPS,
                spr=self.stepper.steps_per_rev,
                dd=config.STEPPER_DISPENSE_DEG,
            ))
        print(
            "tap: count={c}, on={on}ms, off={off}ms, duty={d}".format(
                c=config.TAP_COUNT,
                on=config.TAP_ON_MS,
                off=config.TAP_OFF_MS,
                d=config.TAP_PWM_DUTY,
            ))
        print(
            "servo: angle={a:.1f}, range=[{lo}..{hi}], speed={s} deg/s, "
            "presets={p}".format(
                a=self.servo.angle,
                lo=config.SERVO_MIN_ANGLE_DEG,
                hi=config.SERVO_MAX_ANGLE_DEG,
                s=config.SERVO_SPEED_DEG_PER_S,
                p=list(config.SERVO_PRESETS),
            ))
        if self.doser is None:
            print("scale: unavailable -- see boot message "
                  "(re-upload config.py / check wiring); dosing disabled")
            return
        print("scale: UART{u} @ {baud} (GP{tx}/GP{rx})".format(
            u=config.SCALE_UART_ID, baud=config.SCALE_BAUD,
            tx=config.PIN_SCALE_TX, rx=config.PIN_SCALE_RX))
        names = [p["name"] for p in self.doser.phases]
        print("thresholds (g until goal): " + ", ".join(
            "t{} {}->{}: {:.4f}".format(
                i + 1, names[i],
                names[i + 1] if i + 1 < len(names) else "done",
                self.doser.thresholds[i])
            for i in range(len(self.doser.thresholds))))
        for i, p in enumerate(self.doser.phases):
            print("phase {} '{}': angle {:.0f} deg, rot {:.0f} deg @ "
                  "{:.0f} rpm, taps {} ({}on/{}off ms), settle {} ms, "
                  "min_gain {:.4f} g, nudge {:.0f} deg x{}, "
                  "max {} cycles".format(
                      i + 1, p["name"], p["angle_deg"], p["rotation_deg"],
                      p["rotation_rpm"], p["taps_per_cycle"], p["tap_on_ms"],
                      p["tap_off_ms"], p["settle_ms"], p["min_gain_g"],
                      p["stall_nudge_deg"], p["max_nudges"],
                      p["max_cycles"]))

    def set_param(self, arg):
        if self.doser is None:
            print("[set] dosing unavailable (no scale)")
            return
        parts = arg.split()
        if len(parts) == 2 and parts[0].lower() in ("t1", "t2", "t3"):
            idx = int(parts[0][1]) - 1
            self.doser.thresholds[idx] = float(parts[1])
            print("[set] threshold {} = {:.4f} g until goal".format(
                parts[0], self.doser.thresholds[idx]))
            return
        if len(parts) == 3 and parts[0] in ("1", "2", "3"):
            p = self.doser.phases[int(parts[0]) - 1]
            key = parts[1]
            if key == "name" or key not in p:
                print("[set] unknown phase key {!r}; choose from {}".format(
                    key, sorted(k for k in p if k != "name")))
                return
            p[key] = float(parts[2])
            print("[set] phase {} '{}' {} = {}".format(
                parts[0], p["name"], key, p[key]))
            return
        print("[set] usage: 'set t<N> <grams>' or 'set <N> <key> <value>'")

    def emergency_stop(self):
        print("[rig] EMERGENCY STOP")
        self.stepper.enable(False)
        self.tap._off()

    def _scale_ready(self):
        if self.scale is None:
            print("[scale] unavailable -- see boot message "
                  "(re-upload config.py / check wiring)")
            return False
        return True

    def handle(self, line):
        line = line.strip()
        if not line:
            return
        cmd, _, arg = line.partition(" ")
        cmd = cmd.lower()
        try:
            if cmd in ("h", "?", "help"):
                print(HELP)
            elif cmd == "s":
                self.state()
            elif cmd == "d":
                self.stepper.rotate_degrees(config.STEPPER_DISPENSE_DEG)
            elif cmd == "r":
                self.stepper.rotate_degrees(float(arg))
            elif cmd == "t":
                self.tap.tap()
            elif cmd == "a":
                self.servo.move_to(float(arg))
            elif cmd == "p":
                if arg not in config.SERVO_PRESETS:
                    print("unknown preset {!r}; choose from {}".format(
                        arg, list(config.SERVO_PRESETS)))
                    return
                self.servo.move_to(config.SERVO_PRESETS[arg])
            elif cmd == "w":
                if not self._scale_ready():
                    return
                reading = self.scale.read()
                if reading is None:
                    print("[scale] no response -- check wiring / baud "
                          "(see README scale section)")
                else:
                    print("[scale] {} {} {}".format(
                        reading.status, reading.grams, reading.unit))
            elif cmd == "z":
                if not self._scale_ready():
                    return
                self.scale.zero()
                print("[scale] re-zeroed")
            elif cmd in ("g", "dose"):
                if self.doser is None:
                    print("[scale] unavailable -- dosing needs the scale; "
                          "see boot message")
                    return
                self.doser.dose(float(arg))
            elif cmd == "set":
                self.set_param(arg)
            elif cmd in ("!", "stop"):
                self.emergency_stop()
            else:
                print("unknown command {!r}; 'h' for help".format(cmd))
        except Exception as exc:
            print("[rig] command failed: {!r}".format(exc))


# Non-blocking line reader for the command loop (same as PR #100 main.py).
_stdin_poll = None


def _readline_nonblocking(buf=[""]):
    global _stdin_poll
    try:
        import uselect
    except ImportError:
        return sys.stdin.readline().rstrip("\r\n")
    if _stdin_poll is None:
        _stdin_poll = uselect.poll()
        _stdin_poll.register(sys.stdin, uselect.POLLIN)
    if not _stdin_poll.poll(0):
        return None
    ch = sys.stdin.read(1)
    if ch in ("\r", "\n"):
        line, buf[0] = buf[0], ""
        return line
    buf[0] += ch
    return None


def main():
    rig = Rig()
    rig.state()
    while True:
        line = _readline_nonblocking()
        if line is not None:
            rig.handle(line)
        time.sleep_ms(10)


if __name__ == "__main__" and _ON_HARDWARE:
    main()
