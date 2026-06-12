"""Solenoid (DRV8871 + JF-0530B) standalone test (MicroPython).

Pin map from ``config.py``.  Only the DRV8871 outputs are touched.
Run from VS Code's MicroPico extension ("Run current file on Pico").

Keyboard controls (single keystroke; no Enter needed):
    space   one tap (energise TEST_ON_MS, then off)
    b       burst of TEST_BURST_COUNT taps, TEST_OFF_MS apart
    +/-     adjust the holding-PWM duty by 0.1 (0.0..1.0)
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
TEST_ON_MS       = config.TAP_ON_MS       # coil energised per tap
TEST_OFF_MS      = config.TAP_OFF_MS      # quiet gap between burst taps
TEST_BURST_COUNT = config.TAP_COUNT       # how many taps the `b` key fires
TEST_DUTY        = config.TAP_PWM_DUTY    # 0.0..1.0 holding force
PWM_FREQ_HZ      = 20_000                 # >> audible, within DRV8871 filter


def main():
    in1 = PWM(Pin(config.PIN_SOL_IN1))
    in1.freq(PWM_FREQ_HZ)
    in1.duty_u16(0)
    in2 = Pin(config.PIN_SOL_IN2, Pin.OUT, value=0)

    state = {"duty": float(TEST_DUTY),
             "on_ms": TEST_ON_MS,
             "off_ms": TEST_OFF_MS,
             "burst": TEST_BURST_COUNT}

    def _energise(duty):
        in2.value(0)
        in1.duty_u16(int(max(0.0, min(1.0, duty)) * 65535))

    def _off():
        in1.duty_u16(0)

    def tap_once():
        _energise(state["duty"])
        time.sleep_ms(state["on_ms"])
        _off()

    def burst():
        for _ in range(state["burst"]):
            tap_once()
            time.sleep_ms(state["off_ms"])

    def show():
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
                time.sleep_ms(10)
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
