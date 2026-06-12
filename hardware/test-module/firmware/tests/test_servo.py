"""Hobby-servo (dispensing-angle axis) standalone test (MicroPython).

Pin map from ``config.py``.  Only the servo PWM pin is touched.
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

PERIOD_US = 20_000  # 50 Hz servo frame


class ServoTest:
    def __init__(self):
        self.pwm = PWM(Pin(config.PIN_SERVO_SIG))
        self.pwm.freq(50)
        self.pwm.duty_u16(0)
        self.angle = TEST_START_ANGLE
        self.speed = float(TEST_SPEED_DEG_PER_S)
        self._write(self.angle)

    def _write(self, angle):
        span = config.SERVO_MAX_ANGLE_DEG - config.SERVO_MIN_ANGLE_DEG
        frac = ((angle - config.SERVO_MIN_ANGLE_DEG) / span) if span else 0
        pulse_us = (config.SERVO_MIN_PULSE_US
                    + frac * (config.SERVO_MAX_PULSE_US
                              - config.SERVO_MIN_PULSE_US))
        self.pwm.duty_u16(int((pulse_us / PERIOD_US) * 65535))

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
                "speed={s} deg/s, smoothing={on}").format(
                    a=servo.angle,
                    lo=config.SERVO_MIN_ANGLE_DEG,
                    hi=config.SERVO_MAX_ANGLE_DEG,
                    s=servo.speed,
                    on="on" if servo.speed > 0 else "off (instant)")

    print("[servo-test] ready on GP{sig}".format(sig=config.PIN_SERVO_SIG))
    print("space=toggle A/B  a/b=goto  c=centre  j/k=nudge  +/-=speed  "
          "s=state  q=quit")
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
                      "+/-=speed  s=state  q=quit")
    except KeyboardInterrupt:
        print("[servo-test] interrupted")


if __name__ == "__main__":
    main()
