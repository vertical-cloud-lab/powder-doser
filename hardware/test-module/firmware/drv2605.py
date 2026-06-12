"""Minimal MicroPython driver for the TI DRV2605L haptic driver.

We only need the "ROM library effect" path that the bench tests use --
pick a library (ERM = 1, LRA = 6), pick an effect (1..123), call
:meth:`play`, sleep, call :meth:`stop`.  That keeps the driver to ~40
lines instead of vendoring Adafruit's full CircuitPython library.

Register map / sequence per the DRV2605 datasheet (SLOS854):
* MODE   (0x01) = 0x00 -- internal trigger, ROM library
* RTPIN  (0x02) = 0x00 -- ignored in ROM mode
* LIB    (0x03) = library id (1..6)
* WAV0   (0x04) = effect id (1..123)
* WAV1   (0x05) = 0x00 -- end marker
* GO     (0x0C) = 0x01 -- start playback (auto-clears at end)
"""

_ADDR = 0x5A
_REG_MODE  = 0x01
_REG_LIB   = 0x03
_REG_WAV0  = 0x04
_REG_WAV1  = 0x05
_REG_GO    = 0x0C


class DRV2605:
    def __init__(self, i2c, address=_ADDR):
        self._i2c = i2c
        self._addr = address
        self._buf = bytearray(1)
        # Take the chip out of standby into internal-trigger ROM mode.
        self._write(_REG_MODE, 0x00)
        self.library = 1
        self.effect = 1

    def _write(self, reg, val):
        self._buf[0] = val
        self._i2c.writeto_mem(self._addr, reg, self._buf)

    @property
    def library(self):
        return self._library

    @library.setter
    def library(self, value):
        self._library = int(value) & 0x07
        self._write(_REG_LIB, self._library)

    @property
    def effect(self):
        return self._effect

    @effect.setter
    def effect(self, value):
        self._effect = max(1, min(123, int(value)))
        self._write(_REG_WAV0, self._effect)
        self._write(_REG_WAV1, 0x00)

    def play(self):
        self._write(_REG_GO, 0x01)

    def stop(self):
        self._write(_REG_GO, 0x00)
