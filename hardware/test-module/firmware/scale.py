"""A&D HR-100A (HR-A series) balance driver over RS-232C (MicroPython).

The bench rig reads the scale through a Waveshare Pico-2CH-RS232 module
(SP3232EEN transceiver) on UART0
(``config.PIN_SCALE_TX``/``PIN_SCALE_RX``) -- see
``hardware/test-module/README.md`` for the wiring.  The HR-A series
talks A&D's standard ASCII protocol:

Host -> balance commands (terminated ``\\r\\n``):
    ``Q``   request the current weighing datum immediately
    ``S``   request the next *stable* weighing datum
    ``Z``   re-zero (tare) the balance
    ``C``   cancel an outstanding ``S`` request

Balance -> host data (terminated ``\\r\\n``), A&D standard format::

    ST,+00012.345  g      stable datum
    US,+00012.345  g      unstable datum (still settling)
    OL,+99999.999  g      overload

The HR-A factory default serial settings are **2400 baud, 7 data bits,
even parity, 1 stop bit** -- mirror whatever the balance's function
settings say in ``config.py`` (``SCALE_BAUD`` / ``SCALE_BITS`` /
``SCALE_PARITY`` / ``SCALE_STOP``).

This module is import-safe under CPython (for the simulation tests in
``sim/``): anything MicroPython-specific lives behind the ``AndScale``
constructor, while the frame parser is a plain function.
"""

import time

# Status prefixes from the A&D standard format.
STABLE = "ST"
UNSTABLE = "US"
OVERLOAD = "OL"

_KNOWN_HEADERS = (STABLE, UNSTABLE, OVERLOAD)


class ScaleReading:
    """One parsed weighing datum."""

    def __init__(self, status, grams, unit):
        self.status = status      # "ST" / "US" / "OL"
        self.grams = grams        # float, signed (None when overloaded)
        self.unit = unit          # e.g. "g"

    @property
    def stable(self):
        return self.status == STABLE

    @property
    def overload(self):
        return self.status == OVERLOAD

    def __repr__(self):
        return "ScaleReading({}, {}, {!r})".format(
            self.status, self.grams, self.unit)


def parse_frame(line):
    """Parse one A&D standard-format line into a :class:`ScaleReading`.

    Returns ``None`` for empty / unrecognised lines (the balance can
    emit blank lines or echoes depending on its function settings, so
    the caller should just skip those rather than abort a dose).
    """
    if line is None:
        return None
    if isinstance(line, bytes):
        try:
            line = line.decode()
        except Exception:
            return None
    line = line.strip()
    if len(line) < 3 or line[2] != ",":
        return None
    header = line[:2]
    if header not in _KNOWN_HEADERS:
        return None
    body = line[3:].strip()
    # body looks like "+00012.345  g" -- number then unit.
    unit = ""
    num_end = len(body)
    for i, ch in enumerate(body):
        if not (ch.isdigit() or ch in "+-. "):
            unit = body[i:].strip()
            num_end = i
            break
    num_txt = body[:num_end].replace(" ", "")
    if header == OVERLOAD:
        return ScaleReading(OVERLOAD, None, unit)
    try:
        grams = float(num_txt)
    except ValueError:
        return None
    return ScaleReading(header, grams, unit)


class AndScale:
    """A&D HR-A series balance on a MicroPython UART.

    ``uart`` only needs ``write``/``readline``/``any`` -- a fake with
    the same surface drives the CPython simulation tests.
    """

    def __init__(self, uart, response_timeout_ms=1000, sleep_ms=None):
        self.uart = uart
        self.response_timeout_ms = response_timeout_ms
        if sleep_ms is None:
            try:
                sleep_ms = time.sleep_ms          # MicroPython
            except AttributeError:
                sleep_ms = lambda ms: time.sleep(ms / 1000.0)
        self._sleep_ms = sleep_ms

    # -- low level ---------------------------------------------------

    def _command(self, cmd):
        self.uart.write(cmd + b"\r\n" if isinstance(cmd, bytes)
                        else (cmd + "\r\n").encode())

    def _read_reading(self, timeout_ms=None):
        """Read frames until one parses, or until the timeout lapses."""
        if timeout_ms is None:
            timeout_ms = self.response_timeout_ms
        waited = 0
        while waited <= timeout_ms:
            line = self.uart.readline()
            if line:
                reading = parse_frame(line)
                if reading is not None:
                    return reading
                continue  # skip blank/garbled frame, no extra wait
            self._sleep_ms(20)
            waited += 20
        return None

    # -- public API ----------------------------------------------------

    def read(self):
        """Request and return the current datum (stable or not)."""
        self._drain()
        self._command("Q")
        return self._read_reading()

    def read_stable(self, timeout_ms=10000):
        """Poll until the balance reports a stable (``ST``) datum.

        Returns the stable :class:`ScaleReading`, or the last reading
        seen (possibly unstable / ``None``) once ``timeout_ms`` lapses.
        """
        deadline = timeout_ms
        waited = 0
        last = None
        while waited <= deadline:
            reading = self.read()
            if reading is not None:
                last = reading
                if reading.stable:
                    return reading
            self._sleep_ms(100)
            waited += 100 + self.response_timeout_ms
        return last

    def zero(self):
        """Re-zero (tare) the balance and wait for it to settle."""
        self._drain()
        self._command("Z")
        # The HR-A takes a moment to re-zero; settle before next read.
        self._sleep_ms(500)

    def _drain(self):
        """Throw away any stale buffered frames before a fresh request."""
        try:
            while self.uart.any():
                if not self.uart.readline():
                    break
        except AttributeError:
            pass
