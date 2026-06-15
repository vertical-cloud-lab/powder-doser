"""Powder-doser test-rig firmware (MicroPython, Raspberry Pi Pico W).

This is the multi-channel REPL ``main.py`` for the bench rig described
in ``hardware/test-module/README.md``.  It brings up the four actuators
(stepper, ERM coin via DRV2605L, solenoid via DRV8871, dispensing-angle
servo) and exposes a one-line-per-command serial REPL so the bench
operator can exercise any single channel while the others stay idle.

Target stack
------------
* MicroPython 1.22+ for the Raspberry Pi Pico W (RP2040 + CYW43439).
* Edited and run from VS Code via the **MicroPico** extension
  ( https://marketplace.visualstudio.com/items?itemName=paulober.pico-w-go ).
  MicroPico uploads this file as ``main.py`` and gives you a built-in
  terminal that's already wired to the Pico's USB-CDC serial port, so
  the keyboard-driven test scripts in ``tests/`` work without any extra
  terminal program.

Every pin we use is in the GP0..GP15 range, which is identical on the
plain Pico and the Pico W; the Pico W's wireless module owns
GP23/24/25/29 internally, none of which are wired here, so the same
firmware runs unmodified on either board.

Tunables live in ``config.py``; the MicroPico "Run" button re-uploads
and re-runs in a second, so edit-save-run stays quick.

Required modules on the Pico (upload alongside this file):
  - ``config.py``   (next to this file)
  - ``drv2605.py``  (next to this file)
  - ``tic.py``      (next to this file -- Tic T500 serial driver)

Wire-on commands (one per line over USB-serial):
    h            help
    s            print current state / config
    d            dispense (run auger STEPPER_DISPENSE_DEG)
    r <deg>      rotate auger by <deg> degrees (signed)
    v            vibrate (single canned effect)
    t            tap (run TAP_COUNT solenoid pulses)
    a <deg>      smoothly move dispensing-angle servo to <deg>
    p <name>     smoothly move servo to a preset (horizontal/tilt/vertical/tip)
    !            emergency stop -- de-energise everything
"""

import sys
import time

from machine import I2C, Pin, PWM, UART

import config
import tic

# Module-level poll object for MicroPython (functions can't have new
# attributes on MicroPython function objects). See _readline_nonblocking.
_readline_poll = None


# ---------------------------------------------------------------------------
# Low-level driver helpers
# ---------------------------------------------------------------------------

def _out(pin_num, value=0):
    return Pin(pin_num, Pin.OUT, value=value)


def _pwm(pin_num, freq, duty=0.0):
    pwm = PWM(Pin(pin_num))
    pwm.freq(freq)
    pwm.duty_u16(int(max(0.0, min(1.0, duty)) * 65535))
    return pwm


# ---------------------------------------------------------------------------
# Stepper (Pololu Tic T500 over TTL serial -> NEMA-11)
#
# The Pico W no longer bit-bangs STEP/DIR; it sends serial commands to the
# Tic T500, whose on-board MCU runs the motion planner (accel/decel ramps)
# and current limiting.  We keep a local shadow of the target position in
# microsteps so ``rotate_degrees`` can issue relative moves and estimate
# move durations -- the Tic's position telemetry proved unreliable on the
# bench rig, so the firmware does not read it back (see ``_wait_estimated_time``).
# ---------------------------------------------------------------------------

class Stepper:
    def __init__(self):
        self.uart = UART(config.TIC_UART_ID, baudrate=config.TIC_BAUD,
                         tx=Pin(config.PIN_TIC_TX), rx=Pin(config.PIN_TIC_RX),
                         timeout=config.TIC_READ_TIMEOUT_MS)
        self.tic = tic.TicSerial(self.uart)
        self.steps_per_rev = (config.STEPPER_FULL_STEPS_REV
                              * config.STEPPER_MICROSTEPS)
        # Shadow target position (microsteps); the Tic starts at 0 once we
        # call halt_and_set_position below.
        self._position = 0
        self._rpm = float(config.STEPPER_SPEED_RPM)
        self._enabled = False
        self._configure()

    def _accel_units(self):
        # Tic acceleration unit = 1/100 microstep per second per second.
        usteps_per_s2 = config.STEPPER_ACCEL_REV_PER_S2 * self.steps_per_rev
        return max(1, int(usteps_per_s2 * 100))

    def _configure(self):
        t = self.tic
        # Bring the driver out of any latched error/safe-start state, push
        # the motion settings the firmware owns, and zero the position.
        t.exit_safe_start()
        t.clear_driver_error()
        t.set_step_mode(config.STEPPER_MICROSTEPS)
        self.set_speed(config.STEPPER_SPEED_RPM)
        accel = self._accel_units()
        t.set_max_accel(accel)
        t.set_max_decel(accel)
        t.halt_and_set_position(0)
        self._position = 0

    def set_speed(self, rpm):
        # Tic speed unit = 1/10000 microstep per second.
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

    def _wait_estimated_time(self, delta):
        # The Tic T500's TX line proved unreliable at reporting position
        # back to the Pico on the bench rig, so instead of polling
        # ``current_position()`` we wait an estimated time based on the
        # commanded microstep delta and the current speed.  We still ping
        # the Tic's command-timeout watchdog throughout so a long move
        # isn't cut short.  Position is tracked locally (``self._position``);
        # missed steps go undetected, which is acceptable for auger
        # rotation where exact position isn't critical.
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
# Vibration (DRV2605L)
# ---------------------------------------------------------------------------

class Vibration:
    def __init__(self):
        self.enable_pin = _out(config.PIN_HAPT_EN, 1)
        try:
            import drv2605
            self.i2c = I2C(0, scl=Pin(config.PIN_I2C_SCL),
                              sda=Pin(config.PIN_I2C_SDA),
                              freq=400_000)
            self.drv = drv2605.DRV2605(self.i2c)
            self.drv.library = config.VIBRATION_LIBRARY
            self.drv.effect = config.VIBRATION_EFFECT_ID
            self._available = True
        except Exception as exc:
            print("[vib] DRV2605L unavailable ({}); skipping init".format(exc))
            self._available = False

    def buzz(self, duration_s=None):
        if not self._available:
            print("[vib] driver missing -- ignoring buzz")
            return
        seconds = (config.VIBRATION_DURATION_S
                   if duration_s is None else duration_s)
        self.enable_pin.value(1)
        self.drv.play()
        time.sleep(seconds)
        self.drv.stop()


# ---------------------------------------------------------------------------
# Tap (DRV8871 + solenoid).  IN1 PWM, IN2 low gives forward-drive with
# coil-side flyback handled internally by the DRV8871.
# ---------------------------------------------------------------------------

class Tap:
    def __init__(self):
        # 20 kHz PWM is above audible, well within DRV8871's input filter.
        self.in1 = _pwm(config.PIN_SOL_IN1, freq=20_000, duty=0.0)
        self.in2 = _out(config.PIN_SOL_IN2, 0)

    def _on(self, duty):
        self.in2.value(0)
        self.in1.duty_u16(int(max(0.0, min(1.0, duty)) * 65535))

    def _off(self):
        self.in1.duty_u16(0)

    def tap(self, count=None):
        n = config.TAP_COUNT if count is None else count
        for _ in range(n):
            self._on(config.TAP_PWM_DUTY)
            time.sleep_ms(config.TAP_ON_MS)
            self._off()
            time.sleep_ms(config.TAP_OFF_MS)


# ---------------------------------------------------------------------------
# Dispensing-angle servo (hobby servo on Pico GPIO via 50 Hz PWM).
# ---------------------------------------------------------------------------

class Servo:
    """Hobby servo with smooth interpolated motion.

    Every angle command is ramped from the current position to the
    target at ``config.SERVO_SPEED_DEG_PER_S`` deg/s, updated at
    ``config.SERVO_UPDATE_HZ`` Hz.  This avoids the violent "snap" you
    get from writing the new pulse width in a single PWM frame, which
    is important on the powder-doser dispense axis to keep loose powder
    from jumping out of the cup.
    """

    PERIOD_US = 20_000  # 50 Hz

    def __init__(self):
        self.pwm = _pwm(config.PIN_SERVO_SIG, freq=50, duty=0.0)
        self.angle = float(config.SERVO_DEFAULT_DEG)
        # Seed the PWM at the default angle so the servo doesn't jump
        # from 0 on its first interpolated move.
        self._write_angle(self.angle)
        # Re-issue through the smooth path so a freshly powered (but
        # already-centred) servo still ramps gently into position.
        self.move_to(config.SERVO_DEFAULT_DEG)

    def _write_angle(self, angle_deg):
        span = config.SERVO_MAX_ANGLE_DEG - config.SERVO_MIN_ANGLE_DEG
        frac = ((angle_deg - config.SERVO_MIN_ANGLE_DEG) / span
                if span else 0)
        pulse_us = (config.SERVO_MIN_PULSE_US
                    + frac * (config.SERVO_MAX_PULSE_US
                              - config.SERVO_MIN_PULSE_US))
        duty = pulse_us / self.PERIOD_US
        self.pwm.duty_u16(int(duty * 65535))

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
# Top-level test rig
# ---------------------------------------------------------------------------

HELP = (
    "Commands:\n"
    "  h            show this help\n"
    "  s            print rig state / config\n"
    "  d            dispense (rotate auger STEPPER_DISPENSE_DEG)\n"
    "  r <deg>      rotate auger by <deg> (signed)\n"
    "  v            vibrate (single canned effect)\n"
    "  t            tap (TAP_COUNT solenoid pulses)\n"
    "  a <deg>      servo to <deg>\n"
    "  p <preset>   servo to named preset\n"
    "  !            emergency stop\n"
)


class Rig:
    def __init__(self):
        print("[rig] bringing up powder-doser test module")
        self.stepper = Stepper()
        self.vib = Vibration()
        self.tap = Tap()
        self.servo = Servo()
        print("[rig] ready -- type 'h' for help")

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
            "vib: effect={eff} (lib={lib}), duration={dur}s".format(
                eff=config.VIBRATION_EFFECT_ID,
                lib=config.VIBRATION_LIBRARY,
                dur=config.VIBRATION_DURATION_S,
            ))
        print(
            "tap: count={c}, on={on}ms, off={off}ms, duty={d}".format(
                c=config.TAP_COUNT,
                on=config.TAP_ON_MS,
                off=config.TAP_OFF_MS,
                d=config.TAP_PWM_DUTY,
            ))
        print(
            "servo: angle={a:.1f}, range=[{lo}..{hi}], "
            "speed={s} deg/s, presets={p}".format(
                a=self.servo.angle,
                lo=config.SERVO_MIN_ANGLE_DEG,
                hi=config.SERVO_MAX_ANGLE_DEG,
                s=config.SERVO_SPEED_DEG_PER_S,
                p=list(config.SERVO_PRESETS),
            ))

    def emergency_stop(self):
        print("[rig] EMERGENCY STOP")
        self.stepper.enable(False)
        self.tap._off()
        if self.vib._available:
            try:
                self.vib.drv.stop()
            except Exception:
                pass
            self.vib.enable_pin.value(0)

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
            elif cmd == "v":
                self.vib.buzz()
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
            elif cmd in ("!", "stop"):
                self.emergency_stop()
            else:
                print("unknown command {!r}; 'h' for help".format(cmd))
        except Exception as exc:
            print("[rig] command failed: {!r}".format(exc))


def _readline_nonblocking(buf=[""]):
    """Buffer characters from stdin until a newline arrives.

    Uses ``uselect.poll()`` on ``sys.stdin`` (MicroPython) so the main
    loop doesn't block while waiting for the operator to finish typing
    the next command.
    """
    global _readline_poll
    try:
        import uselect
    except ImportError:
        # CPython fallback (no non-blocking stdin): just read a line.
        return sys.stdin.readline().rstrip("\r\n")
    if _readline_poll is None:
        _readline_poll = uselect.poll()
        _readline_poll.register(sys.stdin, uselect.POLLIN)
    if not _readline_poll.poll(0):
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


if __name__ == "__main__":
    main()
