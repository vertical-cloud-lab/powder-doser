"""Powder-doser test-rig firmware (CircuitPython, Raspberry Pi Pico W).

This file is the entry point CircuitPython auto-runs on boot.  It
brings up the four actuators wired in `hardware/test-module/README.md`
(stepper, ERM coin via DRV2605L, solenoid via DRV8871, dispensing-angle
servo) and exposes a one-character-per-command serial REPL so the bench
operator can exercise any single channel while the others stay idle.

The firmware targets the **Raspberry Pi Pico W** (RP2040 + CYW43439).
Every pin we use is in the GP0..GP15 range, which is identical between
the Pico and Pico W; the Pico W's wireless module uses GP23/24/25/29
internally, none of which are wired in this design, so the same binary
runs unmodified on either board.

Tunables live in ``config.py``.  Reload-on-save means tweaking a
parameter does not require re-flashing the firmware.

Required CircuitPython libraries (drop into /lib on the Pico W):
  - adafruit_bus_device
  - adafruit_drv2605

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

from __future__ import annotations

import sys
import time

import board
import busio
import digitalio
import pwmio
from microcontroller import Pin

import config


# ---------------------------------------------------------------------------
# Low-level driver helpers
# ---------------------------------------------------------------------------

def _gpio(pin_num: int, *, direction=digitalio.Direction.OUTPUT,
          initial: bool = False) -> digitalio.DigitalInOut:
    pin: Pin = getattr(board, f"GP{pin_num}")
    io = digitalio.DigitalInOut(pin)
    io.direction = direction
    if direction == digitalio.Direction.OUTPUT:
        io.value = initial
    return io


def _pwm(pin_num: int, frequency: int, duty: float = 0.0) -> pwmio.PWMOut:
    pin: Pin = getattr(board, f"GP{pin_num}")
    pwm = pwmio.PWMOut(pin, frequency=frequency, duty_cycle=0)
    pwm.duty_cycle = int(max(0.0, min(1.0, duty)) * 0xFFFF)
    return pwm


# ---------------------------------------------------------------------------
# Stepper (DRV8825 -> NEMA-11)
# ---------------------------------------------------------------------------

_MICROSTEP_TABLE = {
    1: (False, False, False),
    2: (False, False, True),
    4: (False, True, False),
    8: (False, True, True),
    16: (True, False, False),
    32: (True, True, True),
}


class Stepper:
    def __init__(self) -> None:
        self.step = _gpio(config.PIN_STEP)
        self.dir = _gpio(config.PIN_DIR)
        # ~ENABLE is active-low; start disabled (high) so the motor coasts.
        self.enable_n = _gpio(config.PIN_STEPPER_EN, initial=True)
        m2, m1, m0 = _MICROSTEP_TABLE[config.STEPPER_MICROSTEPS]
        self.m0 = _gpio(config.PIN_M0, initial=m0)
        self.m1 = _gpio(config.PIN_M1, initial=m1)
        self.m2 = _gpio(config.PIN_M2, initial=m2)
        self.steps_per_rev = (config.STEPPER_FULL_STEPS_REV
                              * config.STEPPER_MICROSTEPS)
        self.set_speed(config.STEPPER_SPEED_RPM)

    def set_speed(self, rpm: float) -> None:
        # half-period of the STEP square wave at the requested RPM
        steps_per_sec = rpm / 60.0 * self.steps_per_rev
        self._half_period_s = max(1e-6, 0.5 / steps_per_sec)

    def enable(self, on: bool = True) -> None:
        self.enable_n.value = not on

    def rotate_degrees(self, degrees: float) -> None:
        signed = degrees * (1 if config.STEPPER_DIRECTION >= 0 else -1)
        direction = signed >= 0
        self.dir.value = direction
        steps = int(abs(signed) / 360.0 * self.steps_per_rev)
        if steps == 0:
            return
        self.enable(True)
        # DRV8825 needs ~1.7 us setup after DIR change; the call overhead
        # of CircuitPython is already >> that, so no explicit delay.
        try:
            half = self._half_period_s
            for _ in range(steps):
                self.step.value = True
                time.sleep(half)
                self.step.value = False
                time.sleep(half)
        finally:
            # Leave the driver enabled briefly so the auger can hold position
            # against bridged powder; the operator can disable via "!".
            pass


# ---------------------------------------------------------------------------
# Vibration (DRV2605L)
# ---------------------------------------------------------------------------

class Vibration:
    def __init__(self) -> None:
        self.enable_pin = _gpio(config.PIN_HAPT_EN, initial=True)
        try:
            import adafruit_drv2605
            self.i2c = busio.I2C(getattr(board, f"GP{config.PIN_I2C_SCL}"),
                                 getattr(board, f"GP{config.PIN_I2C_SDA}"))
            self.drv = adafruit_drv2605.DRV2605(self.i2c)
            self.drv.library = config.VIBRATION_LIBRARY
            self.drv.sequence[0] = adafruit_drv2605.Effect(
                config.VIBRATION_EFFECT_ID)
            self._available = True
        except Exception as exc:  # noqa: BLE001 -- bench tool, log + degrade
            print(f"[vib] DRV2605L unavailable ({exc!r}); skipping init")
            self._available = False

    def buzz(self, duration_s: float | None = None) -> None:
        if not self._available:
            print("[vib] driver missing -- ignoring buzz")
            return
        seconds = config.VIBRATION_DURATION_S if duration_s is None else duration_s
        self.enable_pin.value = True
        self.drv.play()
        time.sleep(seconds)
        self.drv.stop()


# ---------------------------------------------------------------------------
# Tap (DRV8871 + solenoid).  IN1 PWM, IN2 low gives forward-drive with
# coil-side flyback handled internally by the DRV8871.
# ---------------------------------------------------------------------------

class Tap:
    def __init__(self) -> None:
        # 20 kHz PWM is above audible, well within DRV8871's input filter.
        self.in1 = _pwm(config.PIN_SOL_IN1, frequency=20_000, duty=0.0)
        self.in2 = _gpio(config.PIN_SOL_IN2, initial=False)

    def _on(self, duty: float) -> None:
        self.in2.value = False
        self.in1.duty_cycle = int(max(0.0, min(1.0, duty)) * 0xFFFF)

    def _off(self) -> None:
        self.in1.duty_cycle = 0

    def tap(self, count: int | None = None) -> None:
        n = config.TAP_COUNT if count is None else count
        for _ in range(n):
            self._on(config.TAP_PWM_DUTY)
            time.sleep(config.TAP_ON_MS / 1000.0)
            self._off()
            time.sleep(config.TAP_OFF_MS / 1000.0)


# ---------------------------------------------------------------------------
# Dispensing-angle servo (5 V hobby servo on Pico GPIO via 50 Hz PWM).
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

    def __init__(self) -> None:
        self.pwm = _pwm(config.PIN_SERVO_SIG, frequency=50, duty=0.0)
        # Track position internally so smoothing can interpolate from
        # "wherever we are now" without re-querying the servo.
        self.angle = float(config.SERVO_DEFAULT_DEG)
        # Seed the PWM at the default angle so the servo doesn't jump
        # from 0 on its first interpolated move.
        self._write_angle(self.angle)
        # Then re-issue the default through the smooth path so a freshly
        # powered (but already-centred) servo still ramps gently into
        # position rather than slamming there.
        self.move_to(config.SERVO_DEFAULT_DEG)

    def _write_angle(self, angle_deg: float) -> None:
        """Drive the PWM hard to the given angle (no smoothing)."""
        span = config.SERVO_MAX_ANGLE_DEG - config.SERVO_MIN_ANGLE_DEG
        frac = ((angle_deg - config.SERVO_MIN_ANGLE_DEG) / span
                if span else 0)
        pulse_us = (config.SERVO_MIN_PULSE_US
                    + frac * (config.SERVO_MAX_PULSE_US
                              - config.SERVO_MIN_PULSE_US))
        duty = pulse_us / self.PERIOD_US
        self.pwm.duty_cycle = int(duty * 0xFFFF)

    def move_to(self, angle_deg: float) -> None:
        """Smoothly interpolate from the current angle to ``angle_deg``.

        Falls back to an instantaneous jump if
        ``config.SERVO_SPEED_DEG_PER_S`` is non-positive.
        """
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
        # Walk toward the target in fixed-size steps; the final iteration
        # snaps exactly onto the target so we don't accumulate float drift.
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
    def __init__(self) -> None:
        print("[rig] bringing up powder-doser test module")
        self.stepper = Stepper()
        self.vib = Vibration()
        self.tap = Tap()
        self.servo = Servo()
        print("[rig] ready -- type 'h' for help")

    def state(self) -> None:
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

    def emergency_stop(self) -> None:
        print("[rig] EMERGENCY STOP")
        self.stepper.enable(False)
        self.tap._off()
        if self.vib._available:
            try:
                self.vib.drv.stop()
            except Exception:
                pass
            self.vib.enable_pin.value = False

    def handle(self, line: str) -> None:
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
                    print(f"unknown preset {arg!r}; "
                          f"choose from {list(config.SERVO_PRESETS)}")
                    return
                self.servo.move_to(config.SERVO_PRESETS[arg])
            elif cmd in ("!", "stop"):
                self.emergency_stop()
            else:
                print(f"unknown command {cmd!r}; 'h' for help")
        except Exception as exc:  # noqa: BLE001
            print(f"[rig] command failed: {exc!r}")


def _readline_nonblocking() -> str | None:
    """Buffer characters from sys.stdin until a newline arrives."""
    if not hasattr(_readline_nonblocking, "buf"):
        _readline_nonblocking.buf = ""  # type: ignore[attr-defined]
    try:
        import supervisor
        n = supervisor.runtime.serial_bytes_available
    except (ImportError, AttributeError):
        n = 0
    if not n:
        return None
    ch = sys.stdin.read(n)
    buf = _readline_nonblocking.buf + ch  # type: ignore[attr-defined]
    if "\n" not in buf and "\r" not in buf:
        _readline_nonblocking.buf = buf  # type: ignore[attr-defined]
        return None
    # Split on first newline, keep remainder.
    nl = min((buf.find(c) for c in "\r\n" if c in buf), default=-1)
    line, rest = buf[:nl], buf[nl + 1:]
    # Skip an immediately-following \n after \r (CRLF).
    if rest.startswith("\n"):
        rest = rest[1:]
    _readline_nonblocking.buf = rest  # type: ignore[attr-defined]
    return line


def main() -> None:
    rig = Rig()
    rig.state()
    while True:
        line = _readline_nonblocking()
        if line is not None:
            rig.handle(line)
        time.sleep(0.01)


if __name__ == "__main__":
    main()
