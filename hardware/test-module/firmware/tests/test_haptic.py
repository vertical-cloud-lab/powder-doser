"""Haptic-motor (DRV2605L + ERM coin) standalone test script.

Same pin map as the main rig firmware -- ``config.py`` is the
single source of truth.  Only the DRV2605L is touched.

To run on the Pico W:
    cp tests/test_haptic.py /Volumes/CIRCUITPY/code.py

Keyboard controls (single keystroke; no Enter needed):
    space   play the configured effect (TEST_EFFECT_ID) for TEST_DURATION_S
    n       advance to the next effect ID in TEST_EFFECT_SWEEP
    p       go back one effect ID in TEST_EFFECT_SWEEP
    l       toggle library between ERM (1) and LRA (6)
    s       print current state
    q       quit
"""

from __future__ import annotations

import time

import board
import busio
import digitalio
from microcontroller import Pin

import config
from tests._keypress import read_key


# ---------------------------------------------------------------------------
# Adjustable test parameters.
# ---------------------------------------------------------------------------
TEST_EFFECT_ID    = config.VIBRATION_EFFECT_ID   # 1..123 (DRV2605L ROM)
TEST_DURATION_S   = config.VIBRATION_DURATION_S  # seconds
TEST_LIBRARY      = config.VIBRATION_LIBRARY     # 1 = ERM, 6 = LRA
# Effects worth cycling through on the bench (good cross-section of the
# ROM: clicks, buzzes, ramps, long alarms).  Pick from 1..123.
TEST_EFFECT_SWEEP = [1, 14, 47, 70, 84, 118]


def main() -> None:
    enable_pin = digitalio.DigitalInOut(
        getattr(board, "GP{}".format(config.PIN_HAPT_EN)))
    enable_pin.direction = digitalio.Direction.OUTPUT
    enable_pin.value = True

    import adafruit_drv2605
    i2c = busio.I2C(getattr(board, "GP{}".format(config.PIN_I2C_SCL)),
                    getattr(board, "GP{}".format(config.PIN_I2C_SDA)))
    drv = adafruit_drv2605.DRV2605(i2c)

    state = {"effect": TEST_EFFECT_ID, "library": TEST_LIBRARY,
             "duration": TEST_DURATION_S}

    def apply() -> None:
        drv.library = state["library"]
        drv.sequence[0] = adafruit_drv2605.Effect(state["effect"])

    apply()

    def buzz() -> None:
        enable_pin.value = True
        drv.play()
        time.sleep(state["duration"])
        drv.stop()

    def show() -> str:
        return ("haptic: effect={effect} (library={library}), "
                "duration={duration:.2f}s, enabled={en}").format(
                    en=enable_pin.value, **state)

    print("[haptic-test] ready on I2C SCL=GP{scl}/SDA=GP{sda}, "
          "EN=GP{en}".format(scl=config.PIN_I2C_SCL,
                             sda=config.PIN_I2C_SDA,
                             en=config.PIN_HAPT_EN))
    print("space=buzz  n=next effect  p=prev  l=toggle ERM/LRA  s=state  q=quit")
    print(show())

    idx = (TEST_EFFECT_SWEEP.index(TEST_EFFECT_ID)
           if TEST_EFFECT_ID in TEST_EFFECT_SWEEP else 0)
    try:
        while True:
            key = read_key()
            if key is None:
                time.sleep(0.01)
                continue
            if key == " ":
                buzz()
            elif key == "n":
                idx = (idx + 1) % len(TEST_EFFECT_SWEEP)
                state["effect"] = TEST_EFFECT_SWEEP[idx]
                apply()
                print(show())
            elif key == "p":
                idx = (idx - 1) % len(TEST_EFFECT_SWEEP)
                state["effect"] = TEST_EFFECT_SWEEP[idx]
                apply()
                print(show())
            elif key == "l":
                state["library"] = 6 if state["library"] == 1 else 1
                apply()
                print(show())
            elif key == "s":
                print(show())
            elif key == "q":
                drv.stop()
                enable_pin.value = False
                print("[haptic-test] stopped; exiting")
                return
            elif key in ("h", "?"):
                print("space=buzz  n/p=cycle effect  "
                      "l=toggle library  s=state  q=quit")
    except KeyboardInterrupt:
        drv.stop()
        enable_pin.value = False
        print("[haptic-test] interrupted; stopped")


if __name__ == "__main__":
    main()
