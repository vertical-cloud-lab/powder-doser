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

Units (PR #124 review): every rotation value in this file is TRUE AUGER
degrees / RPM and every angle is TRUE MOUNTING-PLATE degrees -- the
44:20 stepper->auger and 2:1 servo->plate gear ratios are folded in at
the driver layer (``AUGER_GEAR_RATIO`` / ``PLATE_GEAR_RATIO`` below).
config.py's servo values stay servo-horn degrees and are converted
where used: horn 90 = plate 45 = the "vertical" preset, the confirmed
bench mapping.

Any rotation phase can optionally run in CONTINUOUS (velocity) mode
instead of the default incremental rotate-settle-measure cycles --
meant for phase 1 (``set 1 continuous 1``): the auger spins steadily at
``rotation_rpm`` while the scale is polled every ``poll_ms`` with
instantaneous (possibly unstable) readings, and the auger halts once
the mass is within ``anticipation_g`` of the phase-exit threshold (an
in-flight/settling margin).  The Tic's TX line is not wired back to the
Pico on this rig, so after each continuous run the stepper position is
simply re-zeroed (halt and set position 0) rather than read back.

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

      set 1 angle_deg 40        # phase 1 dispensing angle -> 40 plate deg
      set 2 rotation_deg 20     # phase 2 rotation per cycle -> 20 auger deg
      set 2 rotation_rpm 20     # phase 2 rotation speed -> 20 auger RPM
      set 1 continuous 1        # phase 1: velocity mode (0 = incremental)
      set 1 anticipation_g 0.05 # velocity mode: halt 50 mg early
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
    d            dispense (rotate auger STEPPER_DISPENSE_DEG, auger deg)
    r <deg>      rotate auger by <deg> auger degrees (signed)
    t            tap (TAP_COUNT solenoid pulses)
    a <deg>      smoothly move mounting plate to <deg> plate degrees
    p <name>     plate to a preset (horizontal/tilt/vertical/tip)
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
# GEAR RATIOS (PR #124 review) -- every user-facing value in this file
# is a true MECHANISM value: auger degrees / auger RPM for rotations,
# mounting-plate degrees for the dispensing angle.  The ratios below
# convert to the actuator shafts at the driver layer:
#   * stepper pinion 20 T -> auger gear 44 T: the stepper turns
#     44/20 = 2.2x per auger turn;
#   * servo pinion -> mounting plate 2:1: the servo horn turns 2 deg
#     per plate degree (horn 90 = plate 45 = "vertical", confirmed).
# =========================================================================
AUGER_GEAR_RATIO = 44.0 / 20.0    # stepper-shaft rev per auger rev
PLATE_GEAR_RATIO = 2.0            # servo-horn deg per plate deg

# config.py's stepper safety range (5..240 RPM) is MOTOR-shaft RPM; the
# same ceiling expressed at the auger:
MAX_AUGER_RPM = 240.0 / AUGER_GEAR_RATIO   # ~109 auger RPM


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
# x powder g per auger rev) comfortably below the gap between its exit
# threshold and the goal, or a single cycle can blow straight past the
# target -- this rough draft has no online g/rev estimator (unlike
# dosing.py).  Velocity mode has its own margin knob (anticipation_g).
# =========================================================================

# --- Phase-shift thresholds (grams until goal mass) ----------------------
PHASE1_EXIT_REMAINING_G = 0.500   # bulk -> fine when <= this many g to go
PHASE2_EXIT_REMAINING_G = 0.050   # fine -> tap  when <= this many g to go
PHASE3_TOLERANCE_G      = 0.005   # done when within +/- this of the goal

# --- Global safety limits ------------------------------------------------
DOSE_TIMEOUT_S = 600              # hard wall-clock limit for one dose

# --- Per-phase parameters ------------------------------------------------
# Every phase understands the same keys:
#   angle_deg        dispensing angle (mounting-plate degrees) for the phase
#   rotation_deg     auger rotation per cycle (auger deg; 0 = no rotation)
#   rotation_rpm     auger speed (auger RPM) while this phase rotates
#   continuous       1 = velocity mode: spin the auger steadily at
#                    rotation_rpm while polling the scale, halt at
#                    exit threshold + anticipation_g.  Ignores
#                    rotation_deg and taps_per_cycle.  0 = incremental
#                    rotate-settle-measure cycles (the default).
#   poll_ms          velocity mode: scale polling interval
#   anticipation_g   velocity mode: halt this many grams BEFORE the
#                    phase-exit threshold (margin for in-flight powder
#                    and post-halt settling)
#   taps_per_cycle   solenoid taps per cycle (0 = no tapping)
#   tap_on_ms/off_ms solenoid timing for this phase's taps
#   settle_ms        wait after actuating before trusting the scale
#   min_gain_g       a cycle gaining less than this counts as a stall
#                    (velocity mode: no min_gain_g of flow within
#                    max_stall_cycles x settle_ms while spinning = stall)
#   max_stall_cycles consecutive stalls before nudging/aborting
#   stall_nudge_deg  auger nudge to re-feed the tube lip on a stall
#                    (0 = don't nudge, abort instead; mainly for phase 3,
#                    where taps only deliver powder already at the lip)
#   max_nudges       stall-nudge budget for the phase
#   max_cycles       safety budget: abort the dose if exceeded
#
# Angles are mounting-plate degrees; config.SERVO_PRESETS (servo-horn
# degrees) map to horizontal=0, tilt=22.5, vertical=45, tip=67.5 plate
# deg through the 2:1 gearing.  Bench observation (PR #124):
# steeper/more-vertical angles dispense a lot more per action,
# horizontal is the most precise -- hence steep bulk, horizontal taps.
# All defaults are UNTUNED starting guesses from the salt demos.

PHASE1_BULK = {
    "name": "bulk",
    "angle_deg": 45.0,        # "vertical" plate angle -- fast flow
    "rotation_deg": 360.0,    # full auger turn per cycle
    "rotation_rpm": 55.0,     # ~120 motor RPM; auger ceiling is ~109
    "continuous": 0,          # set 1 for velocity mode (phase 1's option)
    "poll_ms": 250,
    "anticipation_g": 0.0,
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
    "angle_deg": 22.5,        # "tilt" plate angle -- moderate flow
    "rotation_deg": 30.0,     # small auger increment, measure every pause
    "rotation_rpm": 30.0,
    "continuous": 0,
    "poll_ms": 250,
    "anticipation_g": 0.0,
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
    "continuous": 0,
    "poll_ms": 250,
    "anticipation_g": 0.0,
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
# Stepper (Pololu Tic T500 over TTL serial -> NEMA-11).  The PR #100
# main.py class (shadow position, estimated-time waits, idle de-energise;
# see there for the design notes) with two additions for PR #124:
#   * the 44:20 stepper->auger gearing is folded into steps_per_rev, so
#     the whole API -- rotate_degrees, set_speed, run_at_rpm -- speaks
#     TRUE AUGER degrees and RPM;
#   * velocity mode (run_at_rpm / keep_alive / stop) for the continuous
#     bulk phase.
# ---------------------------------------------------------------------------

class Stepper:
    def __init__(self):
        self.uart = UART(config.TIC_UART_ID, baudrate=config.TIC_BAUD,
                         tx=Pin(config.PIN_TIC_TX), rx=Pin(config.PIN_TIC_RX),
                         timeout=config.TIC_READ_TIMEOUT_MS)
        self.tic = tic.TicSerial(self.uart)
        # Microsteps per AUGER revolution (gearing folded in): every
        # degree/RPM at this API is true auger motion.
        self.steps_per_rev = (config.STEPPER_FULL_STEPS_REV
                              * config.STEPPER_MICROSTEPS
                              * AUGER_GEAR_RATIO)
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
        rpm = float(rpm)
        if rpm > MAX_AUGER_RPM:
            print("[stepper] {:.0f} auger RPM exceeds the ~{:.0f} auger-RPM "
                  "ceiling (240 RPM at the motor); clamping".format(
                      rpm, MAX_AUGER_RPM))
            rpm = MAX_AUGER_RPM
        self._rpm = rpm
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
            self.keep_alive()
            time.sleep_ms(50)

    # -- velocity mode (continuous rotation) --------------------------
    # The Tic's "Set target velocity" spins the motor until halted while
    # the dose loop polls the scale.  TX from the Tic is not wired back
    # to the Pico on this rig, so stop() cannot read the true position --
    # it halts and (re)defines the current position as ZERO, which also
    # re-syncs the shadow position the position moves rely on.

    def run_at_rpm(self, rpm):
        """Spin continuously at ``rpm`` (auger RPM) until stop().

        The caller must invoke keep_alive() at least every ~1 s while
        spinning, or a Tic with its serial command timeout enabled
        halts the motor mid-phase.
        """
        self.set_speed(rpm)          # velocity is capped by max speed
        if not self._enabled:
            self.enable(True)
        sign = 1 if config.STEPPER_DIRECTION >= 0 else -1
        usteps_per_s = self._rpm / 60.0 * self.steps_per_rev
        self.tic.set_target_velocity(sign * max(1, int(usteps_per_s * 10000)))

    def keep_alive(self):
        try:
            self.tic.reset_command_timeout()
        except Exception:
            pass

    def stop(self):
        """Halt continuous rotation and re-zero the position (no TX)."""
        self.tic.halt_and_set_position(0)
        self._position = 0
        if self._idle_deenergize():
            self.enable(False)


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
# Dispensing-angle servos (dual, mirrored, smooth-ramped).  The PR #100
# main.py class, except the public API -- move_to() and .angle -- speaks
# TRUE MOUNTING-PLATE degrees: the 2:1 servo->plate gearing is applied
# at the horn-degree boundary (_write_angle).  config.py's servo values
# (SERVO_DEFAULT_DEG, SERVO_MIN/MAX_ANGLE_DEG, SERVO_SPEED_DEG_PER_S,
# SERVO_PRESETS) remain servo-horn degrees and are divided by
# PLATE_GEAR_RATIO where used, so the unmodified PR #100 config.py keeps
# working (horn 90 = plate 45 = "vertical", the confirmed mapping).
# ---------------------------------------------------------------------------

class Servo:
    PERIOD_US = 20_000  # 50 Hz

    def __init__(self):
        self.pwm1 = _pwm(config.PIN_SERVO_SIG, freq=50, duty=0.0)
        self.pwm2 = _pwm(config.PIN_SERVO_SIG2, freq=50, duty=0.0)
        self.min_plate_deg = config.SERVO_MIN_ANGLE_DEG / PLATE_GEAR_RATIO
        self.max_plate_deg = config.SERVO_MAX_ANGLE_DEG / PLATE_GEAR_RATIO
        self.angle = float(config.SERVO_DEFAULT_DEG) / PLATE_GEAR_RATIO
        self._write_angle(self.angle)
        self.move_to(self.angle)

    def _mirror(self, horn_deg):
        if config.SERVO2_INVERT:
            return ((config.SERVO_MIN_ANGLE_DEG + config.SERVO_MAX_ANGLE_DEG)
                    - horn_deg)
        return horn_deg

    def _angle_to_duty(self, horn_deg):
        span = config.SERVO_MAX_ANGLE_DEG - config.SERVO_MIN_ANGLE_DEG
        frac = ((horn_deg - config.SERVO_MIN_ANGLE_DEG) / span
                if span else 0)
        pulse_us = (config.SERVO_MIN_PULSE_US
                    + frac * (config.SERVO_MAX_PULSE_US
                              - config.SERVO_MIN_PULSE_US))
        return int(pulse_us / self.PERIOD_US * 65535)

    def _write_angle(self, plate_deg):
        horn_deg = plate_deg * PLATE_GEAR_RATIO
        self.pwm1.duty_u16(self._angle_to_duty(horn_deg))
        self.pwm2.duty_u16(self._angle_to_duty(self._mirror(horn_deg)))

    def move_to(self, angle_deg):
        """Smooth-move the mounting plate to ``angle_deg`` plate degrees."""
        target = max(self.min_plate_deg,
                     min(self.max_plate_deg, angle_deg))
        # config speed is horn deg/s; the plate moves half as fast.
        speed = float(config.SERVO_SPEED_DEG_PER_S) / PLATE_GEAR_RATIO
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
# (rotate_degrees / set_speed, plus run_at_rpm / keep_alive / stop for
# velocity mode), ``tap`` (tap(count, on_ms, off_ms)), ``servo``
# (move_to) and ``scale`` (read / read_stable / zero), so the same
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
            if int(p["continuous"]):
                actu = ("CONTINUOUS @ {:.0f} auger rpm (poll {} ms, "
                        "anticipation {:.4f} g)".format(
                            p["rotation_rpm"], int(p["poll_ms"]),
                            max(0.0, p["anticipation_g"])))
            else:
                actu = ("{:.0f} auger deg/cycle @ {:.0f} rpm, {} taps/cycle"
                        .format(p["rotation_deg"], p["rotation_rpm"],
                                p["taps_per_cycle"]))
            self.log("=== phase {}/{} '{}' start: {:.4f} g to go, exit at "
                     "{:.4f} g to go; angle {:.1f} plate deg, {}, "
                     "settle {} ms".format(
                         idx + 1, len(self.phases), p["name"], remaining,
                         exit_g, p["angle_deg"], actu, p["settle_ms"]))
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
        if int(p["continuous"]):
            return self._run_phase_continuous(num, p, exit_g, target_g,
                                              grams, t0, state)
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

    def _run_phase_continuous(self, num, p, exit_g, target_g, grams, t0,
                              state):
        """Velocity-mode phase: spin the auger steadily, halt on threshold.

        The auger runs continuously at ``rotation_rpm`` while the scale
        is polled every ``poll_ms`` with INSTANTANEOUS readings -- the
        balance rarely asserts ST while mass is rising and the pan
        vibrates, so waiting for stable frames here would hang.  The
        auger halts once remaining <= exit threshold + ``anticipation_g``
        (margin for in-flight powder and the halt itself), then one
        settled stable reading closes the phase.  ``rotation_deg`` and
        ``taps_per_cycle`` are ignored in this mode.

        Stall rule: less than ``min_gain_g`` of flow within
        ``max_stall_cycles`` x ``settle_ms`` of spinning aborts as
        stalled (empty hopper / jam) instead of spinning forever.

        Returns (grams, abort_status_or_None, polls) -- the cycle count
        in the dose summary is the number of scale polls.
        """
        tag = "[phase {} {}]".format(num, p["name"])
        rpm = float(p["rotation_rpm"])
        if rpm <= 0:
            self.log(tag + " continuous mode needs rotation_rpm > 0 -- "
                     "phase does nothing, skipping")
            return grams, None, 0
        halt_at_g = exit_g + max(0.0, p["anticipation_g"])
        poll_ms = max(50, int(p["poll_ms"]))
        stall_limit_s = (p["max_stall_cycles"] * p["settle_ms"]) / 1000.0
        polls = 0
        misses = 0
        prev = grams
        gain_ref = grams            # last mass that counted as flow ...
        gain_ref_t = self._now()    # ... and when it was seen
        spin_started = self._now()
        status = None
        self.stepper.run_at_rpm(rpm)
        try:
            while True:
                if self._now() - t0 > self.timeout_s:
                    self.log(tag + " dose timeout ({} s)".format(
                        self.timeout_s))
                    status = DoseResult.TIMEOUT
                    break
                self._sleep_ms(poll_ms)
                self.stepper.keep_alive()
                reading = self.scale.read()
                polls += 1
                if (reading is None or reading.overload
                        or reading.grams is None):
                    misses += 1
                    if misses >= 10:
                        self.log(tag + " scale went quiet mid-rotation")
                        status = DoseResult.SCALE_ERROR
                        break
                    continue
                misses = 0
                grams = reading.grams
                self._objectives(
                    tag + " poll {}{}:".format(
                        polls, "" if reading.stable else " (unstable)"),
                    grams, target_g, grams - prev, t0,
                    gain_label="this poll")
                prev = grams
                if target_g - grams <= halt_at_g:
                    break
                if grams - gain_ref >= p["min_gain_g"]:
                    gain_ref = grams
                    gain_ref_t = self._now()
                elif self._now() - gain_ref_t > stall_limit_s:
                    self.log(tag + " no powder flow for {:.1f} s while "
                             "spinning -- hopper empty or jam".format(
                                 stall_limit_s))
                    status = DoseResult.STALLED
                    break
        finally:
            # Always halt, even on a scale exception; no TX from the
            # Tic, so the position is re-zeroed rather than read back.
            self.stepper.stop()
        state["deg"] += rpm / 60.0 * 360.0 * (self._now() - spin_started)
        if status is not None:
            return grams, status, polls
        self.log(tag + " auger halted at {:.4f} g to go (halt threshold "
                 "{:.4f} g); settling {} ms".format(
                     max(0.0, target_g - grams), halt_at_g,
                     int(p["settle_ms"])))
        self._sleep_ms(int(p["settle_ms"]))
        settled = self._stable_grams()
        if settled is None:
            return grams, DoseResult.SCALE_ERROR, polls
        self._objectives(tag + " settled:", settled, target_g,
                         settled - grams, t0, gain_label="while settling")
        return settled, None, polls


# ---------------------------------------------------------------------------
# Top-level rig + REPL
# ---------------------------------------------------------------------------

HELP = (
    "Three-phase doser commands (auger deg/RPM and plate deg -- gear\n"
    "ratios 44:20 and 2:1 are already folded in):\n"
    "  h                    show this help\n"
    "  s                    print rig state, thresholds, phase parameters\n"
    "  d                    dispense (STEPPER_DISPENSE_DEG of auger)\n"
    "  r <deg>              rotate auger by <deg> auger degrees (signed)\n"
    "  t                    tap (TAP_COUNT solenoid pulses)\n"
    "  a <deg>              mounting plate to <deg> plate degrees\n"
    "  p <preset>           plate to named preset (vertical = 45 plate deg)\n"
    "  w                    weigh (read the scale once)\n"
    "  z                    re-zero (tare) the scale\n"
    "  g <grams>            three-phase dose to <grams>\n"
    "  set t<N> <grams>     phase-shift threshold N (g until goal);\n"
    "                       t1 bulk->fine, t2 fine->tap, t3 tolerance\n"
    "  set <N> <key> <val>  phase-N parameter, e.g. set 1 angle_deg 40;\n"
    "                       set 1 continuous 1 spins phase 1 steadily\n"
    "                       until t1 + anticipation_g (velocity mode)\n"
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
            "stepper: {rpm} auger rpm (gear {gr:.2f}:1, max {mx:.0f}), "
            "microsteps=1/{ms}, usteps/auger-rev={spr:.0f}, "
            "dispense_deg={dd} auger deg".format(
                rpm=config.STEPPER_SPEED_RPM,
                gr=AUGER_GEAR_RATIO,
                mx=MAX_AUGER_RPM,
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
            "plate: angle={a:.1f} plate deg (gear {gr:.0f}:1), "
            "range=[{lo:.0f}..{hi:.0f}], presets={p}".format(
                a=self.servo.angle,
                gr=PLATE_GEAR_RATIO,
                lo=self.servo.min_plate_deg,
                hi=self.servo.max_plate_deg,
                p={k: v / PLATE_GEAR_RATIO
                   for k, v in config.SERVO_PRESETS.items()},
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
            mode = (" CONTINUOUS (poll {} ms, anticipation {:.4f} g)"
                    .format(int(p["poll_ms"]), p["anticipation_g"])
                    if int(p["continuous"]) else "")
            print("phase {} '{}': angle {:.1f} plate deg, rot {:.0f} auger "
                  "deg @ {:.0f} rpm{}, taps {} ({}on/{}off ms), settle "
                  "{} ms, min_gain {:.4f} g, nudge {:.0f} deg x{}, "
                  "max {} cycles".format(
                      i + 1, p["name"], p["angle_deg"], p["rotation_deg"],
                      p["rotation_rpm"], mode, p["taps_per_cycle"],
                      p["tap_on_ms"], p["tap_off_ms"], p["settle_ms"],
                      p["min_gain_g"], p["stall_nudge_deg"],
                      p["max_nudges"], p["max_cycles"]))

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
        try:
            # Halt any continuous rotation and re-zero the Tic position
            # so the shadow position stays in sync (no TX read-back).
            self.stepper.stop()
        except Exception:
            pass
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
                # config presets are servo-horn degrees (PR #100);
                # convert to true plate degrees through the 2:1 gearing.
                self.servo.move_to(
                    config.SERVO_PRESETS[arg] / PLATE_GEAR_RATIO)
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
