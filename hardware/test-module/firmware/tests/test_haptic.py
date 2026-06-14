"""Haptic-motor (DRV2605L + ERM coin) standalone test (MicroPython).

Pin assignments come from ``config.py`` so this mirrors the main rig
wiring exactly.  Only the DRV2605L on I2C0 (SDA=GP0 / SCL=GP1) and the
EN line on GP14 are touched.  Uses the tiny ``drv2605.py`` driver
sitting next to ``main.py``.

Run from VS Code via the MicroPico extension's "Run current file on
Pico" button -- stdout/stdin land in the built-in MicroPico terminal.

Keyboard controls (single keystroke; no Enter needed):
    space   play the configured effect (TEST_EFFECT_ID) for TEST_DURATION_S
    n       advance to the next effect ID in TEST_EFFECT_SWEEP
    p       go back one effect ID in TEST_EFFECT_SWEEP
    l       toggle library between ERM (1) and LRA (6)
    s       print current state
    q       quit
"""

import sys
import time

sys.path.insert(0, "..")
sys.path.insert(0, "/")

from machine import I2C, Pin

import config
import drv2605
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


def main():
    enable_pin = Pin(config.PIN_HAPT_EN, Pin.OUT, value=1)
    i2c = I2C(0, scl=Pin(config.PIN_I2C_SCL),
                 sda=Pin(config.PIN_I2C_SDA),
                 freq=400_000)
    drv = drv2605.DRV2605(i2c)
    state = {"effect": TEST_EFFECT_ID,
             "library": TEST_LIBRARY,
             "duration": TEST_DURATION_S}

    def apply():
        drv.library = state["library"]
        drv.effect = state["effect"]

    apply()

    def buzz():
        enable_pin.value(1)
        drv.play()
        time.sleep(state["duration"])
        drv.stop()

    def show():
        return ("haptic: effect={effect} (library={library}), "
                "duration={duration:.2f}s, enabled={en}").format(
                    en=enable_pin.value(), **state)

    print("[haptic-test] ready on I2C SCL=GP{scl}/SDA=GP{sda}, EN=GP{en}".format(
        scl=config.PIN_I2C_SCL, sda=config.PIN_I2C_SDA,
        en=config.PIN_HAPT_EN))
    print("space=buzz  n=next effect  p=prev  l=toggle ERM/LRA  s=state  q=quit")
    print(show())

    idx = (TEST_EFFECT_SWEEP.index(TEST_EFFECT_ID)
           if TEST_EFFECT_ID in TEST_EFFECT_SWEEP else 0)
    try:
        while True:
            key = read_key()
            if key is None:
                time.sleep_ms(10)
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
                enable_pin.value(0)
                print("[haptic-test] stopped; exiting")
                return
            elif key in ("h", "?"):
                print("space=buzz  n/p=cycle effect  "
                      "l=toggle library  s=state  q=quit")
    except KeyboardInterrupt:
        drv.stop()
        enable_pin.value(0)
        print("[haptic-test] interrupted; stopped")


if __name__ == "__main__":
    main()
