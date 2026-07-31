"""Idle scale streamer -- reads the HR-100A and nothing else.

Runs ON the Pico via ``mpremote run`` (RAM only; nothing is written to
the Pico's filesystem).  Unlike ``pid_dose.py`` / ``characterize.py``
this module imports **only** ``config`` and ``scale``: no stepper, no
servo, no solenoid, no tap.  Importing it cannot move the rig, which is
what makes it safe to leave running between experiments (issue #126,
tiers 2/3 -- the "idle stream" the design doc says is missing).

Protocol (CSV over USB stdout), deliberately the same shape as
``pid_dose.py`` so one parser family covers both::

    M,<key>,<value>            metadata, emitted once at start
    S,<t_ms>,<grams>,<flag>    one poll; flag is S/U/O/X
    E,<t_ms>,<text>            event (start/stop/error)

``flag`` is ``S`` stable, ``U`` unstable, ``O`` overload, ``X`` no reply
(the poll timed out -- logged rather than dropped so gaps are visible).
``grams`` is ``nan`` for ``O``/``X``.

Duration and rate are injected by the host by prepending assignments to
this file before ``mpremote run`` (see ``scripts/scale_stream_capture.py``);
``globals().get`` picks them up when present and falls back otherwise.
``DURATION_S = 0`` streams until interrupted.
"""

import time

import config
import scale as scale_mod

from machine import UART, Pin

DURATION_S = globals().get("DURATION_S", 0.0)
POLL_HZ = globals().get("POLL_HZ", 5.0)

_t0 = time.ticks_ms()


def t_ms():
    return time.ticks_diff(time.ticks_ms(), _t0)


def meta(key, value):
    print("M,{},{}".format(key, value))


def ev(text):
    print("E,{},{}".format(t_ms(), text))


def main():
    period_ms = int(1000.0 / POLL_HZ) if POLL_HZ > 0 else 0
    meta("stream", "scale-idle-v1")
    meta("poll_hz", POLL_HZ)
    meta("duration_s", DURATION_S)
    meta("baud", config.SCALE_BAUD)
    meta("bits", config.SCALE_BITS)
    meta("parity", config.SCALE_PARITY)
    meta("stop", config.SCALE_STOP)
    meta("response_timeout_ms", config.SCALE_RESPONSE_TIMEOUT_MS)

    uart = scale_mod.open_uart(config, UART, Pin)
    balance = scale_mod.AndScale(
        uart, response_timeout_ms=config.SCALE_RESPONSE_TIMEOUT_MS)
    ev("stream start")

    n = 0
    misses = 0
    try:
        while True:
            tick = time.ticks_ms()
            reading = balance.read()
            ts = t_ms()
            if reading is None:
                misses += 1
                print("S,{},nan,X".format(ts))
            elif reading.overload:
                print("S,{},nan,O".format(ts))
            else:
                print("S,{},{:.4f},{}".format(
                    ts, reading.grams, "S" if reading.stable else "U"))
            n += 1
            if DURATION_S and ts >= DURATION_S * 1000:
                break
            # Pace to POLL_HZ; a slow reply just means the next poll is
            # immediate rather than the stream sliding out of phase.
            slack = period_ms - time.ticks_diff(time.ticks_ms(), tick)
            if slack > 0:
                time.sleep_ms(slack)
    except KeyboardInterrupt:
        ev("interrupted")
    finally:
        # No sys.stdout.flush() here: MicroPython's stdout wrapper has no
        # flush(), and raising inside finally would mask the real reason
        # the loop ended.
        ev("stream stop n={} misses={}".format(n, misses))


main()
