"""Stepper-motor (DRV8825 + NEMA-11) standalone test (MicroPython).

Pin assignments are imported from ``config.py``, which is also the
contract the KiCad schematic is generated from -- so this script and
the full rig firmware stay in lockstep.  Only the stepper channel is
exercised; everything else (haptic, solenoid, servo) is untouched.

To run on the Pico W from VS Code + MicroPico:

1. Upload the firmware folder once ("Upload project" in MicroPico).
2. Open this file and hit MicroPico's "Run current file on Pico"
   (the green play arrow in the status bar) -- it streams stdout to
   the built-in terminal and feeds your keystrokes into ``sys.stdin``.

Keyboard controls (single keystroke; no Enter needed):
    space   step DEFAULT_MOVE_DEG in the current direction
    f       one full revolution (360 deg)
    r       reverse the direction flag
    +       speed up by SPEED_STEP_RPM
    -       slow down by SPEED_STEP_RPM
    e       toggle ~ENABLE (drive de-energised vs. holding torque)
    s       print state
    q       quit (de-energise and exit the loop)
"""

import sys
import time

# Allow `python tests/test_stepper.py` style invocation from the
# firmware/ folder root by making the parent dir importable.
sys.path.insert(0, "..")
sys.path.insert(0, "/")

from machine import Pin

import config
from tests._keypress import read_key


# ---------------------------------------------------------------------------
# Adjustable test parameters (independent of the main rig config).
# ---------------------------------------------------------------------------
DEFAULT_MOVE_DEG = 90.0      # how far each spacebar press rotates
SPEED_STEP_RPM   = 10        # +/- adjustment granularity
START_DIRECTION  = +1        # +1 = CW from motor face, -1 = CCW


_MICROSTEP_TABLE = {
    1:  (0, 0, 0),
    2:  (0, 0, 1),
    4:  (0, 1, 0),
    8:  (0, 1, 1),
    16: (1, 0, 0),
    32: (1, 1, 1),
}


def _out(n, v=0):
    return Pin(n, Pin.OUT, value=v)


class StepperTest:
    def __init__(self):
        self.step_pin = _out(config.PIN_STEP)
        self.dir_pin = _out(config.PIN_DIR)
        # ~ENABLE active-low; start disabled so a mis-wired board can't
        # cook the motor while the operator is still hooking up the rig.
        self.enable_n = _out(config.PIN_STEPPER_EN, 1)
        m2, m1, m0 = _MICROSTEP_TABLE[config.STEPPER_MICROSTEPS]
        _out(config.PIN_M0, m0)
        _out(config.PIN_M1, m1)
        _out(config.PIN_M2, m2)
        self.steps_per_rev = (config.STEPPER_FULL_STEPS_REV
                              * config.STEPPER_MICROSTEPS)
        self.rpm = float(config.STEPPER_SPEED_RPM)
        self.direction = +1 if START_DIRECTION >= 0 else -1
        self.enabled = False
        self._recompute_period()

    def _recompute_period(self):
        sps = self.rpm / 60.0 * self.steps_per_rev
        self._half_us = max(1, int(0.5 * 1_000_000 / sps))

    def enable(self, on=True):
        self.enable_n.value(0 if on else 1)
        self.enabled = on

    def set_rpm(self, rpm):
        self.rpm = max(1.0, rpm)
        self._recompute_period()

    def rotate(self, degrees):
        signed = degrees * self.direction
        self.dir_pin.value(1 if signed >= 0 else 0)
        steps = int(abs(signed) / 360.0 * self.steps_per_rev)
        if steps == 0:
            return
        if not self.enabled:
            self.enable(True)
        half = self._half_us
        sleep_us = time.sleep_us
        sp = self.step_pin
        for _ in range(steps):
            sp.value(1)
            sleep_us(half)
            sp.value(0)
            sleep_us(half)

    def state(self):
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
    "  +/-    adjust RPM by {step}\n"
    "  e      toggle ~ENABLE (holding torque on/off)\n"
    "  s      print state\n"
    "  q      quit\n"
).format(move=DEFAULT_MOVE_DEG, step=SPEED_STEP_RPM)


def main():
    rig = StepperTest()
    print("[stepper-test] ready on GP{step}/GP{dir}/GP{en}".format(
        step=config.PIN_STEP, dir=config.PIN_DIR, en=config.PIN_STEPPER_EN))
    print(HELP)
    print(rig.state())
    try:
        while True:
            key = read_key()
            if key is None:
                time.sleep_ms(10)
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
