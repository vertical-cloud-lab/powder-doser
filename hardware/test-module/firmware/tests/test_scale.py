"""A&D HR-100A scale standalone bench test (MicroPython, keyboard-driven).

Exercises only the scale channel: Pico UART0 (GP12/GP13) -> Waveshare
Pico-2CH-RS232 module -> RS-232 -> balance.  Wiring and balance function
settings are described in ``hardware/test-module/README.md`` (step 8).

Run from VS Code + MicroPico like the other scripts in this folder
(upload project, then "Run current file on Pico").

Keyboard controls (single keystroke; no Enter needed):
    w   request one weighing datum (Q command)
    W   wait for a *stable* datum (polls until ST)
    z   re-zero / tare (Z command)
    r   raw mode: dump every byte the scale sends for 5 s
    s   print configuration
    q   quit
"""

import sys
import time

sys.path.insert(0, "..")
sys.path.insert(0, "/")

from machine import Pin, UART

import config
import scale
from tests._keypress import read_key


HELP = (
    "Scale test (A&D HR-100A over Waveshare 2CH-RS232/UART0) -- keyboard controls:\n"
    "  w   read one weighing datum\n"
    "  W   wait for a stable (ST) datum\n"
    "  z   re-zero (tare)\n"
    "  r   raw dump for 5 s\n"
    "  s   print config\n"
    "  q   quit\n"
)


def make_scale():
    # Non-blocking UART (timeout=0): the driver paces itself; a blocking
    # hardware timeout multiplies every silent-link poll ~50x (PR #100).
    uart = scale.open_uart(config, UART, Pin)
    return uart, scale.AndScale(
        uart, response_timeout_ms=config.SCALE_RESPONSE_TIMEOUT_MS)


def state():
    par = {0: "N", 1: "O", 2: "E"}[config.SCALE_PARITY]
    print("[scale-test] UART{u} GP{tx}/GP{rx} @ {b} {bits}{par}{stop}".format(
        u=config.SCALE_UART_ID, tx=config.PIN_SCALE_TX,
        rx=config.PIN_SCALE_RX, b=config.SCALE_BAUD,
        bits=config.SCALE_BITS, par=par, stop=config.SCALE_STOP))


def raw_dump(uart, seconds=5):
    print("[scale-test] raw dump for {} s (sending Q each second)"
          .format(seconds))
    end = time.ticks_add(time.ticks_ms(), seconds * 1000)
    next_q = 0
    while time.ticks_diff(end, time.ticks_ms()) > 0:
        if time.ticks_diff(next_q, time.ticks_ms()) <= 0:
            uart.write(b"Q\r\n")
            next_q = time.ticks_add(time.ticks_ms(), 1000)
        data = uart.read()
        if data:
            print(repr(data))
        time.sleep_ms(50)


def main():
    uart, sc = make_scale()
    state()
    print(HELP)
    while True:
        key = read_key()
        if key is None:
            time.sleep_ms(10)
            continue
        if key == "w":
            print(sc.read())
        elif key == "W":
            print(sc.read_stable(timeout_ms=config.SCALE_STABLE_TIMEOUT_MS))
        elif key == "z":
            sc.zero()
            print("[scale-test] re-zeroed")
        elif key == "r":
            raw_dump(uart)
        elif key == "s":
            state()
        elif key == "q":
            print("[scale-test] bye")
            return
        elif key in ("h", "?"):
            print(HELP)


if __name__ == "__main__":
    main()
