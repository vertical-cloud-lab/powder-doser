"""Minimal MicroPython driver for the Pololu Tic T500 over TTL serial.

The bench rig drives the auger stepper through a **Pololu Tic T500 USB
multi-interface stepper motor controller** (item #3134, MP6500 driver)
instead of a bare driver carrier.  The Pico W talks to the Tic over a
UART using the Tic's "compact" serial command protocol, and the Tic's
on-board microcontroller runs the motion planner (acceleration /
deceleration ramps, current position tracking, current limiting).

Only the handful of commands the rig needs are implemented here; the
full command set is documented in the Tic user's guide, section 9
("Serial command reference"):
https://www.pololu.com/docs/0J71/9

This module is hardware-abstraction-agnostic: it is handed any object
with ``write(bytes)`` / ``read(n)`` methods (a ``machine.UART`` on the
Pico, or a fake in a host-side unit test), so the byte encoding can be
exercised without a Pico attached.

Speed/acceleration units (per the Tic user's guide):
  * speed         : 1 unit = 1/10000 microstep per second
  * acceleration  : 1 unit = 1/100 microstep per second per second
"""

# Tic serial command bytes (compact protocol -- send the command byte as
# the first byte, no device-number header).
_CMD_SET_TARGET_POSITION   = 0xE0  # 32-bit signed
_CMD_SET_TARGET_VELOCITY   = 0xE3  # 32-bit signed
_CMD_HALT_AND_SET_POSITION = 0xEC  # 32-bit signed
_CMD_HALT_AND_HOLD         = 0x89  # quick
_CMD_RESET_COMMAND_TIMEOUT = 0x8C  # quick
_CMD_DEENERGIZE            = 0x86  # quick
_CMD_ENERGIZE              = 0x85  # quick
_CMD_EXIT_SAFE_START       = 0x83  # quick
_CMD_ENTER_SAFE_START      = 0x8F  # quick
_CMD_RESET                 = 0xB0  # quick
_CMD_CLEAR_DRIVER_ERROR    = 0x8A  # quick
_CMD_SET_MAX_SPEED         = 0xE6  # 32-bit
_CMD_SET_STARTING_SPEED    = 0xE5  # 32-bit
_CMD_SET_MAX_ACCEL         = 0xEA  # 32-bit
_CMD_SET_MAX_DECEL         = 0xE9  # 32-bit
_CMD_SET_STEP_MODE         = 0x94  # 7-bit
_CMD_SET_CURRENT_LIMIT     = 0x91  # 7-bit
_CMD_GET_VARIABLE          = 0xA1

# Offsets into the Tic's variable block (user's guide section 7).
_VAR_CURRENT_POSITION = 0x22  # int32, microsteps

# Step-mode codes accepted by "Set step mode" -- the Tic T500 (MP6500)
# only supports full .. 1/8 microstepping.
_STEP_MODE_CODES = {1: 0, 2: 1, 4: 2, 8: 3}


class TicSerial:
    """Talk to a Tic over a UART using the compact serial protocol."""

    def __init__(self, uart):
        self._uart = uart

    # -- low-level framing -------------------------------------------------

    def _quick(self, cmd):
        self._uart.write(bytes([cmd]))

    def _write7(self, cmd, value):
        self._uart.write(bytes([cmd, value & 0x7F]))

    def _write32(self, cmd, value):
        value &= 0xFFFFFFFF
        # First data byte carries bit 7 of each of the four 7-bit chunks;
        # the Tic reassembles the 32-bit value from these five bytes.
        msbs = (((value >> 7) & 1)
                | ((value >> 14) & 2)
                | ((value >> 21) & 4)
                | ((value >> 28) & 8))
        self._uart.write(bytes([
            cmd,
            msbs,
            value & 0x7F,
            (value >> 8) & 0x7F,
            (value >> 16) & 0x7F,
            (value >> 24) & 0x7F,
        ]))

    # -- quick commands ----------------------------------------------------

    def energize(self):
        self._quick(_CMD_ENERGIZE)

    def deenergize(self):
        self._quick(_CMD_DEENERGIZE)

    def exit_safe_start(self):
        self._quick(_CMD_EXIT_SAFE_START)

    def enter_safe_start(self):
        self._quick(_CMD_ENTER_SAFE_START)

    def reset_command_timeout(self):
        self._quick(_CMD_RESET_COMMAND_TIMEOUT)

    def halt_and_hold(self):
        self._quick(_CMD_HALT_AND_HOLD)

    def clear_driver_error(self):
        self._quick(_CMD_CLEAR_DRIVER_ERROR)

    def reset(self):
        self._quick(_CMD_RESET)

    # -- configuration -----------------------------------------------------

    def set_step_mode(self, microsteps):
        try:
            code = _STEP_MODE_CODES[microsteps]
        except KeyError:
            raise ValueError(
                "Tic T500 supports 1, 2, 4, or 8 microsteps, not {}".format(
                    microsteps))
        self._write7(_CMD_SET_STEP_MODE, code)

    def set_current_limit_code(self, code):
        # NB: the mA->code mapping is model-specific; we leave the current
        # limit to the Tic Control Center (set over USB) on the bench rig
        # and expose this only for completeness.
        self._write7(_CMD_SET_CURRENT_LIMIT, code)

    def set_max_speed(self, units):
        self._write32(_CMD_SET_MAX_SPEED, units)

    def set_starting_speed(self, units):
        self._write32(_CMD_SET_STARTING_SPEED, units)

    def set_max_accel(self, units):
        self._write32(_CMD_SET_MAX_ACCEL, units)

    def set_max_decel(self, units):
        self._write32(_CMD_SET_MAX_DECEL, units)

    # -- motion ------------------------------------------------------------

    def set_target_position(self, position):
        self._write32(_CMD_SET_TARGET_POSITION, position)

    def set_target_velocity(self, velocity):
        self._write32(_CMD_SET_TARGET_VELOCITY, velocity)

    def halt_and_set_position(self, position):
        self._write32(_CMD_HALT_AND_SET_POSITION, position)

    # -- telemetry ---------------------------------------------------------

    def _get_variable(self, offset, length):
        self._uart.write(bytes([_CMD_GET_VARIABLE, offset & 0x7F]))
        data = self._uart.read(length)
        if data is None or len(data) != length:
            return None
        return data

    def current_position(self):
        """Signed current position in microsteps, or ``None`` if the read
        timed out (e.g. the Tic's TX line is not wired back to the Pico)."""
        data = self._get_variable(_VAR_CURRENT_POSITION, 4)
        if data is None:
            return None
        value = data[0] | (data[1] << 8) | (data[2] << 16) | (data[3] << 24)
        if value >= 0x80000000:
            value -= 0x100000000
        return value
