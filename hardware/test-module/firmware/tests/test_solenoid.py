"""Solenoid (DRV8871 + JF-0530B) standalone test script.

Same pin map as the main rig firmware; ``config.py`` is the single
source of truth.  Only the DRV8871 outputs are touched.

To run on the Pico W:
    cp tests/test_solenoid.py /Volumes/CIRCUITPY/code.py

Keyboard controls (single keystroke; no Enter needed):
    space   one tap (energise TEST_ON_MS, then off)
    b       burst of TEST_BURST_COUNT taps, TEST_OFF_MS apart
    +/-     adjust the holding-PWM duty by 0.1 (0.0..1.0)
    s       print state
    q       quit
"""

from __future__ import annotations

import time

import board
import digitalio
import pwmio
from microcontroller import Pin

import config
from tests._keypress import read_key


# ---------------------------------------------------------------------------
# Adjustable test parameters.
# ---------------------------------------------------------------------------
TEST_ON_MS       = config.TAP_ON_MS       # coil energised per tap
TEST_OFF_MS      = config.TAP_OFF_MS      # quiet gap between burst taps
TEST_BURST_COUNT = config.TAP_COUNT       # how many taps the `b` key fires
TEST_DUTY        = config.TAP_PWM_DUTY    # 0.0..1.0 holding force
PWM_FREQ_HZ      = 20_000                 # >> audible, within DRV8871 filter


def main() -> None:
    in1 = pwmio.PWMOut(getattr(board, "GP{}".format(config.PIN_SOL_IN1)),
                       frequency=PWM_FREQ_HZ, duty_cycle=0)
    in2 = digitalio.DigitalInOut(
        getattr(board, "GP{}".format(config.PIN_SOL_IN2)))
    in2.direction = digitalio.Direction.OUTPUT
    in2.value = False

    state = {"duty": float(TEST_DUTY),
             "on_ms": TEST_ON_MS,
             "off_ms": TEST_OFF_MS,
             "burst": TEST_BURST_COUNT}

    def _energise(duty: float) -> None:
        in2.value = False
        in1.duty_cycle = int(max(0.0, min(1.0, duty)) * 0xFFFF)

    def _off() -> None:
        in1.duty_cycle = 0

    def tap_once() -> None:
        _energise(state["duty"])
        time.sleep(state["on_ms"] / 1000.0)
        _off()

    def burst() -> None:
        for _ in range(state["burst"]):
            tap_once()
            time.sleep(state["off_ms"] / 1000.0)

    def show() -> str:
        return ("solenoid: on={on}ms, off={off}ms, burst={n}, "
                "duty={d:.2f}").format(on=state["on_ms"], off=state["off_ms"],
                                        n=state["burst"], d=state["duty"])

    print("[solenoid-test] ready on IN1=GP{in1}/IN2=GP{in2}".format(
        in1=config.PIN_SOL_IN1, in2=config.PIN_SOL_IN2))
    print("space=tap  b=burst  +/-=duty  s=state  q=quit")
    print(show())

    try:
        while True:
            key = read_key()
            if key is None:
                time.sleep(0.01)
                continue
            if key == " ":
                tap_once()
            elif key == "b":
                burst()
            elif key == "+":
                state["duty"] = min(1.0, state["duty"] + 0.1)
                print(show())
            elif key == "-":
                state["duty"] = max(0.0, state["duty"] - 0.1)
                print(show())
            elif key == "s":
                print(show())
            elif key == "q":
                _off()
                print("[solenoid-test] off; exiting")
                return
            elif key in ("h", "?"):
                print("space=tap  b=burst  +/-=duty  s=state  q=quit")
    except KeyboardInterrupt:
        _off()
        print("[solenoid-test] interrupted; off")


if __name__ == "__main__":
    main()
