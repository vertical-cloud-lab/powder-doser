"""Dual hobby-servo (dispensing-angle axis) standalone test (MicroPython).

Pin map from ``config.py``.  Two servos drive the dispensing-angle axis
together (one on each side of the baseplate); only their two PWM pins are
touched.  The servos always move in unison off a single logical angle --
there is no independent control.  Because they face opposite directions,
servo 2 is driven with the mirror-image angle of servo 1 (reflected about
the midpoint of the range) when ``TEST_INVERT`` is True.

Smoothing is on by default (interpolated motion at
``TEST_SPEED_DEG_PER_S`` deg/s) so the test mirrors what the powder
actually sees on the production rig.  Set ``TEST_SPEED_DEG_PER_S = 0``
to revert to instantaneous moves.

Run from VS Code via the MicroPico extension's "Run current file on
Pico" button.

Keyboard controls (single keystroke; no Enter needed):
    space   toggle between TEST_ANGLE_A and TEST_ANGLE_B
    a       go to TEST_ANGLE_A
    b       go to TEST_ANGLE_B
    c       go to centre (midpoint of the configured range)
    j       nudge by -TEST_STEP_DEG
    k       nudge by +TEST_STEP_DEG
    i       toggle servo-2 inversion (to check mounting orientation)
    +/-     adjust the smoothing speed by 10 deg/s
    s       print state
    q       quit
"""

import sys
import time

sys.path.insert(0, "..")
sys.path.insert(0, "/")

from machine import Pin, PWM

import config
from tests._keypress import read_key


# ---------------------------------------------------------------------------
# Adjustable test parameters.
# ---------------------------------------------------------------------------
TEST_ANGLE_A         = config.SERVO_MIN_ANGLE_DEG
TEST_ANGLE_B         = config.SERVO_MAX_ANGLE_DEG
TEST_STEP_DEG        = 5.0
TEST_SPEED_DEG_PER_S = config.SERVO_SPEED_DEG_PER_S
TEST_UPDATE_HZ       = config.SERVO_UPDATE_HZ
TEST_START_ANGLE     = float(config.SERVO_DEFAULT_DEG)
TEST_INVERT          = config.SERVO2_INVERT  # servo 2 mirrors servo 1

PERIOD_US = 20_000  # 50 Hz servo frame


class ServoTest:
    def __init__(self):
        self.pwm1 = PWM(Pin(config.PIN_SERVO_SIG))
        self.pwm1.freq(50)
        self.pwm1.duty_u16(0)
        self.pwm2 = PWM(Pin(config.PIN_SERVO_SIG2))
        self.pwm2.freq(50)
        self.pwm2.duty_u16(0)
        self.angle = TEST_START_ANGLE
        self.speed = float(TEST_SPEED_DEG_PER_S)
        self.invert = bool(TEST_INVERT)
        self._write(self.angle)

    def _mirror(self, angle):
        if self.invert:
            return ((config.SERVO_MIN_ANGLE_DEG + config.SERVO_MAX_ANGLE_DEG)
                    - angle)
        return angle

    def _duty(self, angle):
        span = config.SERVO_MAX_ANGLE_DEG - config.SERVO_MIN_ANGLE_DEG
        frac = ((angle - config.SERVO_MIN_ANGLE_DEG) / span) if span else 0
        pulse_us = (config.SERVO_MIN_PULSE_US
                    + frac * (config.SERVO_MAX_PULSE_US
                              - config.SERVO_MIN_PULSE_US))
        return int((pulse_us / PERIOD_US) * 65535)

    def _write(self, angle):
        # Both servos move in unison; servo 2 takes the mirrored angle.
        self.pwm1.duty_u16(self._duty(angle))
        self.pwm2.duty_u16(self._duty(self._mirror(angle)))

    def move_to(self, target):
        target = max(config.SERVO_MIN_ANGLE_DEG,
                     min(config.SERVO_MAX_ANGLE_DEG, target))
        if self.speed <= 0:
            self._write(target)
            self.angle = target
            return
        hz = max(1, TEST_UPDATE_HZ)
        step = self.speed / hz
        dt = 1.0 / hz
        delta = target - self.angle
        if abs(delta) <= step:
            self._write(target)
            self.angle = target
            return
        direction = step if delta > 0 else -step
        while abs(target - self.angle) > step:
            self.angle += direction
            self._write(self.angle)
            time.sleep(dt)
        self._write(target)
        self.angle = target

    def nudge(self, delta):
        self.move_to(self.angle + delta)


def main():
    servo = ServoTest()
    last_target = TEST_ANGLE_A

    def show():
        return ("servo: angle={a:.1f}, range=[{lo}..{hi}], "
                "speed={s} deg/s, smoothing={on}, "
                "dual(GP{p1}+GP{p2}) invert={inv}").format(
                    a=servo.angle,
                    lo=config.SERVO_MIN_ANGLE_DEG,
                    hi=config.SERVO_MAX_ANGLE_DEG,
                    s=servo.speed,
                    on="on" if servo.speed > 0 else "off (instant)",
                    p1=config.PIN_SERVO_SIG,
                    p2=config.PIN_SERVO_SIG2,
                    inv=servo.invert)

    print("[servo-test] ready on GP{s1}+GP{s2} (dual, invert={inv})".format(
        s1=config.PIN_SERVO_SIG, s2=config.PIN_SERVO_SIG2, inv=TEST_INVERT))
    print("space=toggle A/B  a/b=goto  c=centre  j/k=nudge  i=invert  "
          "+/-=speed  s=state  q=quit")
    print(show())

    centre = 0.5 * (config.SERVO_MIN_ANGLE_DEG + config.SERVO_MAX_ANGLE_DEG)
    try:
        while True:
            key = read_key()
            if key is None:
                time.sleep_ms(10)
                continue
            if key == " ":
                last_target = (TEST_ANGLE_B if last_target == TEST_ANGLE_A
                               else TEST_ANGLE_A)
                servo.move_to(last_target)
            elif key == "a":
                last_target = TEST_ANGLE_A
                servo.move_to(TEST_ANGLE_A)
            elif key == "b":
                last_target = TEST_ANGLE_B
                servo.move_to(TEST_ANGLE_B)
            elif key == "c":
                servo.move_to(centre)
            elif key == "j":
                servo.nudge(-TEST_STEP_DEG)
            elif key == "k":
                servo.nudge(+TEST_STEP_DEG)
            elif key == "i":
                servo.invert = not servo.invert
                servo._write(servo.angle)
                print(show())
            elif key == "+":
                servo.speed += 10
                print(show())
            elif key == "-":
                servo.speed = max(0.0, servo.speed - 10)
                print(show())
            elif key == "s":
                print(show())
            elif key == "q":
                print("[servo-test] exiting (PWM left holding last angle)")
                return
            elif key in ("h", "?"):
                print("space=toggle A/B  a/b=goto  c=centre  j/k=nudge  "
                      "i=invert  +/-=speed  s=state  q=quit")
    except KeyboardInterrupt:
        print("[servo-test] interrupted")


if __name__ == "__main__":
    main()
