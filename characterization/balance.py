"""Balance (analytical scale) interfaces.

The sweep needs two things from the balance that a single "read the
weight" call cannot give:

1. **The raw stream at full rate**, so settling dynamics are observable.
2. **The balance's own stability flag**, kept as a separate channel,
   because "what the controller sees" and "what the load cell is doing"
   are different questions and the interesting failure modes live in the
   gap between them (a balance that declares stable at a biased value,
   or -- in a glovebox -- one that never declares stable at all).

So this module models a balance as a *stream of* :class:`Reading`, not as
a scalar getter.  Everything downstream consumes that stream and both
channels are written to disk; the stable flag is never used to filter
what gets recorded.

Line formats
------------
Continuous-output ("print on stability" off, "continuous send" on) framing
varies by vendor, so :data:`FORMATS` holds named regexes.  ``mtsics`` and
``and`` are the two common ones; ``sbi`` covers many Sartorius/Ohaus
units.  **Verify the preset against your own balance before trusting a
sweep** -- run ``python -m characterization.balance --port ... --sniff``
and check that the parsed values and flags match the display.
"""

from __future__ import annotations

import re
import time
from dataclasses import dataclass
from typing import Callable, Dict, Iterator, Optional

#: Unit conversion to grams, the canonical unit everywhere downstream.
_TO_GRAMS = {"g": 1.0, "mg": 1e-3, "kg": 1e3, "ct": 0.2, "": 1.0}


@dataclass(frozen=True)
class Reading:
    """One parsed line from the balance.

    ``t`` is a host ``time.monotonic()`` timestamp taken when the line was
    read, not a balance-side timestamp -- USB/serial latency is therefore
    baked in.  It is consistent to well under the millisecond scale we
    care about here (settle times are hundreds of ms to seconds), and it
    shares a clock with the actuation commands, which is what matters.
    """

    t: float
    grams: float
    stable: bool
    raw: str


@dataclass(frozen=True)
class LineFormat:
    name: str
    pattern: str
    stable_values: tuple = ()
    unstable_values: tuple = ()
    #: When true, a *present* stability group means unstable (e.g. a
    #: trailing "?" on SBI) rather than stable.
    flag_marks_unstable: bool = False
    tare_command: str = "T\r\n"
    zero_command: str = "Z\r\n"

    def parse(self, line: str, t: float) -> Optional[Reading]:
        match = re.match(self.pattern, line.strip())
        if not match:
            return None
        groups = match.groupdict()
        try:
            value = float(groups["val"].replace(" ", ""))
        except (TypeError, ValueError):
            return None
        unit = (groups.get("unit") or "").strip().lower()
        grams = value * _TO_GRAMS.get(unit, 1.0)
        flag = (groups.get("st") or "").strip().upper()
        if self.flag_marks_unstable:
            stable = not flag
        elif self.stable_values:
            stable = flag in self.stable_values
        else:
            stable = True
        return Reading(t=t, grams=grams, stable=stable, raw=line.rstrip())


FORMATS: Dict[str, LineFormat] = {
    # Mettler-Toledo MT-SICS continuous ("SIR"/"S S"): "S S      1.23456 g"
    "mtsics": LineFormat(
        name="mtsics",
        pattern=r"^S\s+(?P<st>[SD])\s+(?P<val>[-+]?[\d.]+)\s*(?P<unit>\w+)?",
        stable_values=("S",),
        unstable_values=("D",),
        tare_command="T\r\n",
        zero_command="Z\r\n",
    ),
    # A&D / many OEM clones: "ST,+00012.345 g" / "US," while unstable.
    "and": LineFormat(
        name="and",
        pattern=(r"^(?P<st>ST|US|QT|OL)\s*,\s*"
                 r"(?P<val>[-+]?[\d. ]+?)\s*(?P<unit>[a-zA-Z]+)?$"),
        stable_values=("ST", "QT"),
        unstable_values=("US", "OL"),
        tare_command="T\r\n",
        zero_command="Z\r\n",
    ),
    # Sartorius/Ohaus SBI: "+   123.456 g", trailing "?" while unstable.
    "sbi": LineFormat(
        name="sbi",
        pattern=(r"^[NG]?\s*(?P<val>[-+]?\s*[\d.]+)\s*"
                 r"(?P<unit>g|mg|kg|ct)?\s*(?P<st>\?)?$"),
        flag_marks_unstable=True,
        tare_command="T\r\n",
        zero_command="Z\r\n",
    ),
}


class BalanceError(RuntimeError):
    pass


class Balance:
    """Interface implemented by :class:`SerialBalance` and the mock."""

    def open(self) -> "Balance":
        return self

    def close(self) -> None:
        pass

    def readings(self) -> Iterator[Reading]:
        """Yield readings as they arrive; blocks between them."""
        raise NotImplementedError

    def tare(self) -> None:
        raise NotImplementedError

    def zero(self) -> None:
        raise NotImplementedError

    def __enter__(self):
        return self.open()

    def __exit__(self, *exc):
        self.close()


class SerialBalance(Balance):
    """Continuous-output balance on a serial port (via ``pyserial``).

    Set the balance to *continuous* output at the highest rate it offers
    before running a sweep.  Poll-per-reading modes cap the sample rate at
    the round-trip latency, which is typically far too slow to see the
    ringdown you are trying to measure.
    """

    def __init__(self, port: str, baudrate: int = 9600, fmt: str = "mtsics",
                 timeout: float = 1.0, clock: Callable[[], float] = time.monotonic,
                 **serial_kwargs):
        self.port = port
        self.baudrate = baudrate
        self.format = FORMATS[fmt] if isinstance(fmt, str) else fmt
        self.timeout = timeout
        self.clock = clock
        self.serial_kwargs = serial_kwargs
        self._ser = None
        self.n_unparsed = 0

    def open(self) -> "SerialBalance":
        try:
            import serial  # imported lazily so the mock path needs no dep
        except ImportError as exc:  # pragma: no cover - environment dependent
            raise BalanceError(
                "pyserial is required for SerialBalance; "
                "pip install pyserial") from exc
        self._ser = serial.Serial(self.port, self.baudrate,
                                  timeout=self.timeout, **self.serial_kwargs)
        return self

    def close(self) -> None:
        if self._ser is not None:
            self._ser.close()
            self._ser = None

    def _write(self, text: str) -> None:
        if self._ser is None:
            raise BalanceError("balance not open")
        self._ser.write(text.encode("ascii"))
        self._ser.flush()

    def tare(self) -> None:
        self._write(self.format.tare_command)

    def zero(self) -> None:
        self._write(self.format.zero_command)

    def readings(self) -> Iterator[Reading]:
        if self._ser is None:
            raise BalanceError("balance not open")
        while True:
            line = self._ser.readline()
            if not line:
                continue  # read timeout; the caller decides when to stop
            t = self.clock()
            text = line.decode("ascii", errors="replace")
            reading = self.format.parse(text, t)
            if reading is None:
                # Keep going but count it: a steadily climbing unparsed
                # count means the wrong preset, and silently dropping
                # every line would look identical to a quiet balance.
                self.n_unparsed += 1
                continue
            yield reading


def sniff(port: str, baudrate: int = 9600, seconds: float = 5.0,
          fmt: str = "mtsics") -> None:
    """Print raw and parsed lines side by side, to validate a preset."""
    bal = SerialBalance(port, baudrate, fmt=fmt).open()
    fmt_obj = bal.format
    deadline = time.monotonic() + seconds
    n_ok = n_bad = 0
    try:
        while time.monotonic() < deadline:
            raw = bal._ser.readline().decode("ascii", errors="replace")
            if not raw.strip():
                continue
            parsed = fmt_obj.parse(raw, time.monotonic())
            if parsed is None:
                n_bad += 1
                print("UNPARSED  {!r}".format(raw))
            else:
                n_ok += 1
                print("{:>10.5f} g  stable={}  <- {!r}".format(
                    parsed.grams, parsed.stable, raw.strip()))
    finally:
        bal.close()
    print("\nparsed {} line(s), failed on {} using format {!r}".format(
        n_ok, n_bad, fmt_obj.name))
    if n_bad:
        print("Try another --format, or add one to characterization/balance.py")


def _main(argv=None) -> int:
    import argparse

    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--port", required=True)
    ap.add_argument("--baud", type=int, default=9600)
    ap.add_argument("--format", default="mtsics", choices=sorted(FORMATS))
    ap.add_argument("--seconds", type=float, default=5.0)
    ap.add_argument("--sniff", action="store_true",
                    help="print raw vs parsed lines to validate the format")
    args = ap.parse_args(argv)
    sniff(args.port, args.baud, args.seconds, args.format)
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(_main())
