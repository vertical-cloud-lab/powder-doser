"""Clock shim: MicroPython ticks on the Pico, monotonic time under CPython.

Everything that waits or timestamps goes through a Clock object, so the
CPython tests can swap in a fake clock (sim_hw.FakeClock) and run fast.
"""

import time

try:
    _ticks_ms = time.ticks_ms
    _ticks_diff = time.ticks_diff
    _ticks_add = time.ticks_add
    _sleep_ms = time.sleep_ms
except AttributeError:  # CPython
    def _ticks_ms():
        return int(time.monotonic() * 1000)

    def _ticks_diff(a, b):
        return a - b

    def _ticks_add(a, b):
        return a + b

    def _sleep_ms(ms):
        time.sleep(ms / 1000.0)


class Clock:
    def ticks_ms(self):
        return _ticks_ms()

    def diff(self, a, b):
        return _ticks_diff(a, b)

    def add(self, a, b):
        return _ticks_add(a, b)

    def sleep_ms(self, ms):
        _sleep_ms(int(ms))
