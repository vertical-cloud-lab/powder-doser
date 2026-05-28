"""Stepper-motor (DRV8825 + NEMA-11) standalone test script.

Wiring is identical to the main ``code.py`` -- pin assignments are
imported from ``config.py`` so this script and the full rig firmware
stay in lockstep.  The only thing this file exercises is the stepper
channel; everything else (haptic, solenoid, servo) is left untouched.

To run on the Pico W:
    cp tests/test_stepper.py /Volumes/CIRCUITPY/code.py
(or rename to ``code.py`` on the CIRCUITPY drive).  CircuitPython
auto-reloads on save.

Keyboard controls (single keystroke over USB-serial; no Enter needed):
    space   step the configured DEFAULT_MOVE_DEG in the current direction
    f       rotate one full revolution (360 deg)
    r       reverse the direction flag
    +       speed up by SPEED_STEP_RPM
    -       slow down by SPEED_STEP_RPM
    e       toggle ~ENABLE (drive de-energised vs. holding)
    s       print current state
    q       quit (de-energise and exit the loop)
"""

from __future__ import annotations

import time

import board
import digitalio
from microcontroller import Pin

import config
from tests._keypress import read_key


# ---------------------------------------------------------------------------
# Adjustable test parameters (independent of the main rig config).
# ---------------------------------------------------------------------------
DEFAULT_MOVE_DEG = 90.0      # how far each spacebar press rotates
SPEED_STEP_RPM   = 10        # +/- adjustment granularity
START_DIRECTION  = +1        # +1 = CW from motor face, -1 = CCW


_MICROSTEP_TABLE = {
    1: (False, False, False),
    2: (False, False, True),
    4: (False, True, False),
    8: (False, True, True),
    16: (True, False, False),
    32: (True, True, True),
}


def _gpio(pin_num: int, initial: bool = False) -> digitalio.DigitalInOut:
    pin: Pin = getattr(board, "GP{}".format(pin_num))
    io = digitalio.DigitalInOut(pin)
    io.direction = digitalio.Direction.OUTPUT
    io.value = initial
    return io


class StepperTest:
    def __init__(self) -> None:
        self.step_pin = _gpio(config.PIN_STEP)
        self.dir_pin = _gpio(config.PIN_DIR)
        # ~ENABLE is active-low; start disabled so a mis-wired board can't
        # cook the motor while the operator is still hooking up the rig.
        self.enable_n = _gpio(config.PIN_STEPPER_EN, initial=True)
        m2, m1, m0 = _MICROSTEP_TABLE[config.STEPPER_MICROSTEPS]
        self.m0 = _gpio(config.PIN_M0, initial=m0)
        self.m1 = _gpio(config.PIN_M1, initial=m1)
        self.m2 = _gpio(config.PIN_M2, initial=m2)
        self.steps_per_rev = (config.STEPPER_FULL_STEPS_REV
                              * config.STEPPER_MICROSTEPS)
        self.rpm = float(config.STEPPER_SPEED_RPM)
        self.direction = +1 if START_DIRECTION >= 0 else -1
        self.enabled = False
        self._recompute_period()

    def _recompute_period(self) -> None:
        sps = self.rpm / 60.0 * self.steps_per_rev
        self._half_period_s = max(1e-6, 0.5 / sps)

    def enable(self, on: bool = True) -> None:
        self.enable_n.value = not on
        self.enabled = on

    def set_rpm(self, rpm: float) -> None:
        self.rpm = max(1.0, rpm)
        self._recompute_period()

    def rotate(self, degrees: float) -> None:
        signed = degrees * self.direction
        self.dir_pin.value = signed >= 0
        steps = int(abs(signed) / 360.0 * self.steps_per_rev)
        if steps == 0:
            return
        if not self.enabled:
            self.enable(True)
        half = self._half_period_s
        for _ in range(steps):
            self.step_pin.value = True
            time.sleep(half)
            self.step_pin.value = False
            time.sleep(half)

    def state(self) -> str:
        return ("stepper: rpm={:.1f}, dir={:+d}, microsteps=1/{}, "
                "steps/rev={}, enabled={}").format(
                    self.rpm, self.direction,
                    config.STEPPER_MICROSTEPS,
                    self.steps_per_rev, self.enabled)


HELP = (
    "Stepper test -- keyboard controls:\n"
    "  space  rotate {move} deg\n"
    "  f      one full revolution (360 deg)\n"
    "  r      reverse direction\n"
    "  +/-    adjust RPM by {step} (current shown after each change)\n"
    "  e      toggle ~ENABLE (holding torque on/off)\n"
    "  s      print state\n"
    "  q      quit\n"
).format(move=DEFAULT_MOVE_DEG, step=SPEED_STEP_RPM)


def main() -> None:
    rig = StepperTest()
    print("[stepper-test] ready on GP{step}/GP{dir}/GP{en}".format(
        step=config.PIN_STEP, dir=config.PIN_DIR, en=config.PIN_STEPPER_EN))
    print(HELP)
    print(rig.state())
    try:
        while True:
            key = read_key()
            if key is None:
                time.sleep(0.01)
                continue
            if key == " ":
                rig.rotate(DEFAULT_MOVE_DEG)
            elif key == "f":
                rig.rotate(360.0)
            elif key == "r":
                rig.direction = -rig.direction
                print(rig.state())
            elif key == "+":
                rig.set_rpm(rig.rpm + SPEED_STEP_RPM)
                print(rig.state())
            elif key == "-":
                rig.set_rpm(rig.rpm - SPEED_STEP_RPM)
                print(rig.state())
            elif key == "e":
                rig.enable(not rig.enabled)
                print(rig.state())
            elif key == "s":
                print(rig.state())
            elif key == "q":
                rig.enable(False)
                print("[stepper-test] de-energised; exiting")
                return
            elif key in ("h", "?"):
                print(HELP)
    except KeyboardInterrupt:
        rig.enable(False)
        print("[stepper-test] interrupted; de-energised")


if __name__ == "__main__":
    main()
