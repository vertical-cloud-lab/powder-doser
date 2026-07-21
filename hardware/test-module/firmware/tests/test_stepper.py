"""Stepper-motor (Pololu Tic T500 + NEMA-11) standalone test (MicroPython).

Pin assignments are imported from ``config.py``, which is also the
contract the KiCad schematic is generated from -- so this script and
the full rig firmware stay in lockstep.  Only the stepper channel is
exercised; everything else (haptic, solenoid, servo) is untouched.

The auger is driven through a Pololu Tic T500 over UART (TTL serial):
this script opens the same UART1 the main firmware uses and sends the
Tic serial commands via the shared ``tic.TicSerial`` driver.  Set the
Tic's current limit and "Control mode = Serial / I2C / USB" once with
the Tic Control Center over USB before running this (and disable the
Tic's "Command timeout" so a long move isn't cut short).

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
    e       toggle energise (drive de-energised vs. holding torque)
    s       print state
    q       quit (de-energise and exit the loop)
"""

import sys
import time

# Allow `python tests/test_stepper.py` style invocation from the
# firmware/ folder root by making the parent dir importable.
sys.path.insert(0, "..")
sys.path.insert(0, "/")

from machine import Pin, UART

import config
import tic
from tests._keypress import read_key


# ---------------------------------------------------------------------------
# Adjustable test parameters (independent of the main rig config).
# ---------------------------------------------------------------------------
DEFAULT_MOVE_DEG = 90.0      # how far each spacebar press rotates
SPEED_STEP_RPM   = 10        # +/- adjustment granularity
START_DIRECTION  = +1        # +1 = CW from motor face, -1 = CCW


class StepperTest:
    def __init__(self):
        self.uart = UART(config.TIC_UART_ID, baudrate=config.TIC_BAUD,
                         tx=Pin(config.PIN_TIC_TX), rx=Pin(config.PIN_TIC_RX),
                         timeout=config.TIC_READ_TIMEOUT_MS)
        self.tic = tic.TicSerial(self.uart)
        self.steps_per_rev = (config.STEPPER_FULL_STEPS_REV
                              * config.STEPPER_MICROSTEPS)
        self.rpm = float(config.STEPPER_SPEED_RPM)
        self.direction = +1 if START_DIRECTION >= 0 else -1
        self.enabled = False
        self._position = 0
        # Bring the Tic up, push step mode / speed / accel, zero position.
        self.tic.exit_safe_start()
        self.tic.clear_driver_error()
        self.tic.set_step_mode(config.STEPPER_MICROSTEPS)
        self._apply_speed()
        accel = max(1, int(config.STEPPER_ACCEL_REV_PER_S2
                           * self.steps_per_rev * 100))
        self.tic.set_max_accel(accel)
        self.tic.set_max_decel(accel)
        self.tic.halt_and_set_position(0)

    def _apply_speed(self):
        usteps_per_s = self.rpm / 60.0 * self.steps_per_rev
        self.tic.set_max_speed(max(1, int(usteps_per_s * 10000)))

    def enable(self, on=True):
        if on:
            self.tic.energize()
            self.tic.exit_safe_start()
        else:
            self.tic.deenergize()
        self.enabled = on

    def set_rpm(self, rpm):
        self.rpm = max(1.0, rpm)
        self._apply_speed()

    def rotate(self, degrees):
        signed = degrees * self.direction
        delta = int(round(signed / 360.0 * self.steps_per_rev))
        if delta == 0:
            return
        if not self.enabled:
            self.enable(True)
        # update our local position estimate
        self._position += delta
        # tell the Tic the new target
        self.tic.set_target_position(self._position)
        # wait an estimated time for the move to complete (no telemetry required)
        self._wait_estimated_time(delta)

    def _wait_estimated_time(self, delta):
        """Wait based on commanded microstep delta and current RPM.
        This does not read the Tic's telemetry; it only keeps the Tic's
        command timeout alive while waiting.
        """
        # usteps_per_s = microsteps/second based on current rpm & steps_per_rev
        usteps_per_s = max(1.0, self.rpm / 60.0 * self.steps_per_rev)
        est_s = abs(delta) / usteps_per_s
        # add a safety margin
        est_s += 0.2
        # cap very small waits to a short sleep to avoid busy-looping
        wait_ms = int(est_s * 1000)
        # keep resetting Tic command timeout during the wait in small chunks
        deadline = time.ticks_add(time.ticks_ms(), wait_ms + 2000)
        while time.ticks_diff(deadline, time.ticks_ms()) > 0:
            # keep Tic from timing out (the Tic stops if it doesn't see timeout reset)
            try:
                self.tic.reset_command_timeout()
            except Exception:
                # be defensive: ignore if reset_command_timeout doesn't reply
                pass
            # sleep in small increments so we can service KeyboardInterrupt in interactive tests
            time.sleep_ms(50)

    def state(self):
        return ("stepper: rpm={:.1f}, dir={:+d}, microsteps=1/{}, "
                "steps/rev={}, enabled={}").format(
                    self.rpm, self.direction,
                    config.STEPPER_MICROSTEPS,
                    self.steps_per_rev, self.enabled)


HELP = (
    "Stepper test (Tic T500) -- keyboard controls:\n"
    "  space  rotate {move} deg\n"
    "  f      one full revolution (360 deg)\n"
    "  r      reverse direction\n"
    "  +/-    adjust RPM by {step}\n"
    "  e      toggle energise (holding torque on/off)\n"
    "  s      print state\n"
    "  q      quit\n"
).format(move=DEFAULT_MOVE_DEG, step=SPEED_STEP_RPM)


def main():
    rig = StepperTest()
    print("[stepper-test] Tic T500 on UART{id} (TX=GP{tx}, RX=GP{rx})".format(
        id=config.TIC_UART_ID, tx=config.PIN_TIC_TX, rx=config.PIN_TIC_RX))
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
