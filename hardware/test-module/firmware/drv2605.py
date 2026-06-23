"""Minimal MicroPython driver for the TI DRV2605L haptic driver.

Two playback paths are supported:

* **ROM library effect** -- pick a library (ERM = 1, LRA = 6), pick an
  effect (1..123), call :meth:`play`, sleep, call :meth:`stop`.  This is
  the "send a pulse" path the bench tests use.
* **Real-Time Playback (RTP)** -- :meth:`realtime` drives the motor at a
  constant amplitude *continuously* until :meth:`stop` is called, so the
  rig can turn the haptic motor on and off on command (not just pulse it).

That keeps the driver to ~60 lines instead of vendoring Adafruit's full
CircuitPython library.

Register map / sequence per the DRV2605 datasheet (SLOS854):
* MODE   (0x01) = 0x00 -- internal trigger, ROM library
*                 0x05 -- real-time playback (RTP)
* RTPIN  (0x02)        -- RTP amplitude (used in RTP mode only)
* LIB    (0x03) = library id (1..6)
* WAV0   (0x04) = effect id (1..123)
* WAV1   (0x05) = 0x00 -- end marker
* GO     (0x0C) = 0x01 -- start playback (auto-clears at end)
"""

_ADDR = 0x5A
_REG_MODE  = 0x01
_REG_RTPIN = 0x02
_REG_LIB   = 0x03
_REG_WAV0  = 0x04
_REG_WAV1  = 0x05
_REG_GO    = 0x0C

_MODE_INTTRIG = 0x00   # internal trigger, ROM library
_MODE_RTP     = 0x05   # real-time playback


class DRV2605:
    def __init__(self, i2c, address=_ADDR):
        self._i2c = i2c
        self._addr = address
        self._buf = bytearray(1)
        # Take the chip out of standby into internal-trigger ROM mode.
        self._write(_REG_MODE, _MODE_INTTRIG)
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
        # ROM-library pulse: make sure we're in internal-trigger mode in
        # case a previous continuous (RTP) burst left the chip in RTP mode.
        self._write(_REG_MODE, _MODE_INTTRIG)
        self._write(_REG_GO, 0x01)

    def realtime(self, amplitude):
        """Vibrate continuously at ``amplitude`` (0..127) until :meth:`stop`.

        Switches the chip into Real-Time Playback mode and writes the
        amplitude to ``RTPIN``; the motor runs until the amplitude is set
        back to 0 (via :meth:`stop`), giving the rig an on/off command
        instead of a fixed-length ROM pulse.
        """
        self._write(_REG_MODE, _MODE_RTP)
        self._write(_REG_RTPIN, max(0, min(127, int(amplitude))))

    def stop(self):
        self._write(_REG_GO, 0x00)
        # Drop the RTP amplitude too so a continuous "on" stops immediately.
        self._write(_REG_RTPIN, 0x00)
