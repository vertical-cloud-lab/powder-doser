"""Host-side client for the test-rig REPL (``hardware/test-module/firmware``).

Speaks the ack protocol added in issue #139: one command per line, and
one ``ok <cmd> t0=.. t1=.. est=..`` or ``err <cmd> <msg>`` line back.
Blocking on that ack is what lets a sweep run unattended -- without it
the host would have to guess how long a move takes, and any guess that is
too short silently overlaps the next condition's actuation with this
one's ringdown.

Note on timestamps: ``t0``/``t1`` come from the Pico's ``ticks_ms`` clock
and the firmware returns only after an *estimated* move time plus a pad,
so they bound the motion window loosely rather than marking when motion
actually stopped. The analysis therefore anchors settle time to the
host-clock balance stream (see :mod:`characterization.analyze`); the
device timestamps are recorded for cross-checking, not for measurement.
"""

from __future__ import annotations

import re
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional

_ACK_RE = re.compile(r"^ok\s+(?P<cmd>\S+)"
                     r"(?:\s+t0=(?P<t0>-?\d+))?"
                     r"(?:\s+t1=(?P<t1>-?\d+))?"
                     r"(?:\s+est=(?P<est>-?\d+))?")
_ERR_RE = re.compile(r"^err\s+(?P<cmd>\S+)\s*(?P<msg>.*)$")


class RigError(RuntimeError):
    """The rig reported ``err``, or did not acknowledge in time."""


@dataclass
class Ack:
    cmd: str
    ok: bool
    t0_ms: Optional[int] = None
    t1_ms: Optional[int] = None
    est_ms: Optional[int] = None
    lines: List[str] = field(default_factory=list)
    message: str = ""
    #: Host-clock times bracketing the command, used to align with the
    #: balance stream.
    host_start: float = 0.0
    host_end: float = 0.0

    @property
    def device_duration_s(self) -> Optional[float]:
        if self.t0_ms is None or self.t1_ms is None:
            return None
        # ticks_ms wraps; the firmware's own ticks_diff semantics are
        # 30-bit signed on MicroPython, so mirror the wrap here.
        delta = (self.t1_ms - self.t0_ms) % (1 << 30)
        if delta >= (1 << 29):
            delta -= (1 << 30)
        return delta / 1000.0


class Rig:
    """Interface implemented by :class:`SerialRig` and the mock."""

    def command(self, line: str, timeout: float = 30.0) -> Ack:
        raise NotImplementedError

    def close(self) -> None:
        pass

    # -- convenience wrappers -------------------------------------------
    def set_param(self, name: str, value) -> Ack:
        if isinstance(value, bool):
            value = 1 if value else 0
        return self.command("set {} {}".format(name, value))

    def set_params(self, values: Dict[str, object]) -> None:
        for name, value in values.items():
            self.set_param(name, value)

    def reset_params(self) -> Ack:
        return self.command("reset")

    def params(self) -> Dict[str, object]:
        """The rig's own report of every active parameter.

        Read back after setting, never assumed: recording what the host
        *intended* rather than what the rig *has* is how a sweep ends up
        with mislabelled runs that nobody can detect afterwards.
        """
        import json

        ack = self.command("params")
        for line in reversed(ack.lines):
            line = line.strip()
            if line.startswith("{"):
                return json.loads(line)
        raise RigError("no parameter snapshot in response: {!r}".format(
            ack.lines))

    def dispense(self, timeout: float = 60.0) -> Ack:
        return self.command("d", timeout=timeout)

    def rotate(self, degrees: float, timeout: float = 60.0) -> Ack:
        return self.command("r {}".format(degrees), timeout=timeout)

    def vibrate(self, timeout: float = 60.0) -> Ack:
        return self.command("v", timeout=timeout)

    def tap(self, timeout: float = 60.0) -> Ack:
        return self.command("t", timeout=timeout)

    def servo(self, degrees: float, timeout: float = 60.0) -> Ack:
        return self.command("a {}".format(degrees), timeout=timeout)

    def energize(self, on: bool = True) -> Ack:
        return self.command("e {}".format(1 if on else 0))

    def stop(self) -> Ack:
        return self.command("!")

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        try:
            self.stop()
        finally:
            self.close()


class SerialRig(Rig):
    """The rig over its USB-CDC serial port."""

    def __init__(self, port: str, baudrate: int = 115200,
                 timeout: float = 0.2, settle_s: float = 2.0):
        try:
            import serial
        except ImportError as exc:  # pragma: no cover - environment dependent
            raise RigError("pyserial is required for SerialRig; "
                           "pip install pyserial") from exc
        self._ser = serial.Serial(port, baudrate, timeout=timeout)
        # The Pico reboots when the port opens; give main() time to bring
        # the actuators up, then discard its banner.
        time.sleep(settle_s)
        self._drain()

    def _drain(self) -> List[str]:
        lines = []
        while self._ser.in_waiting:
            raw = self._ser.readline()
            if not raw:
                break
            lines.append(raw.decode("ascii", errors="replace").rstrip())
        return lines

    def close(self) -> None:
        try:
            self._ser.close()
        except Exception:  # pragma: no cover - best-effort teardown
            pass

    def command(self, line: str, timeout: float = 30.0) -> Ack:
        self._drain()
        host_start = time.monotonic()
        self._ser.write((line.rstrip() + "\r\n").encode("ascii"))
        self._ser.flush()
        collected: List[str] = []
        deadline = host_start + timeout
        while time.monotonic() < deadline:
            raw = self._ser.readline()
            if not raw:
                continue
            text = raw.decode("ascii", errors="replace").rstrip()
            if not text:
                continue
            match = _ACK_RE.match(text)
            if match:
                g = match.groupdict()
                return Ack(
                    cmd=g["cmd"], ok=True,
                    t0_ms=int(g["t0"]) if g["t0"] else None,
                    t1_ms=int(g["t1"]) if g["t1"] else None,
                    est_ms=int(g["est"]) if g["est"] else None,
                    lines=collected, host_start=host_start,
                    host_end=time.monotonic(),
                )
            err = _ERR_RE.match(text)
            if err:
                raise RigError("{}: {}".format(line, err.group("msg")))
            collected.append(text)
        raise RigError(
            "no ack for {!r} within {:.1f}s (last lines: {})".format(
                line, timeout, collected[-3:]))
