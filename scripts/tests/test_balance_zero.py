#!/usr/bin/env python3
"""Checks for the remote balance re-zero helper (issue #116).

Two things here have already gone wrong on the bench and are worth
pinning:

1. **The A&D ``Z`` command is range-limited.**  It is the RE-ZERO key, so
   it only works within a few percent of capacity around the calibrated
   zero, and this HR-100A has ``erCd = 0`` so a refusal is silent.  On
   2026-08-21 the balance was sitting 4.2 g out from a stale mid-run tare
   and ``balance_zero.py`` reported "sent 'Z'" and then warned about the
   very offset it had failed to clear.  The fallback to ``T`` (tare, full
   range) is what makes the script honest.

2. **``parse()`` is shared.**  ``balance_environment_survey.py`` imports
   it, so a change to its return signature breaks the survey at runtime
   -- which is exactly what happened when the ``CMD`` rows were added.

The device snippet is MicroPython that runs on the Pico, so it is
executed here against a fake UART that behaves like the balance: it
answers ``Q`` with the current reading, honours ``T`` always, and honours
``Z`` only within a re-zero band.
"""

from __future__ import annotations

import sys
import time as _time
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import balance_zero  # noqa: E402

# A&D re-zero band: a few percent of the 102 g capacity.  The balance
# refuses 'Z' outside it, silently.
REZERO_BAND_MG = 2000.0


class FakeUART:
    """Enough of an A&D HR-100A to exercise the snippet's decisions."""

    def __init__(self, offset_mg, honour_z=True):
        self.offset_mg = float(offset_mg)
        self.honour_z = honour_z
        self.commands = []
        self._out = b""

    def write(self, payload):
        cmd = payload.decode().strip()
        self.commands.append(cmd)
        if cmd == "Q":
            self._out += "ST,{:+09.4f}  g\r\n".format(
                self.offset_mg / 1000.0).encode()
        elif cmd == "T":                       # tare: full range, always works
            self.offset_mg = 0.0
        elif cmd == "Z":                       # re-zero: range-limited
            if self.honour_z and abs(self.offset_mg) <= REZERO_BAND_MG:
                self.offset_mg = 0.0

    def read(self):
        out, self._out = self._out, b""
        return out or None


def run_snippet(uart, do_zero=True, settle_ms=400):
    """Execute the device snippet in CPython against ``uart``."""
    printed = []
    ns = {
        "print": lambda *a: printed.append(" ".join(str(x) for x in a)),
        "DO_ZERO": do_zero,
        "SETTLE_MS": settle_ms,
    }
    fake_time = types.SimpleNamespace(
        ticks_ms=lambda: int(_time.monotonic() * 1000),
        ticks_diff=lambda a, b: a - b,
        sleep_ms=lambda ms: None,
    )
    machine = types.ModuleType("machine")
    machine.UART = lambda *a, **k: uart
    machine.Pin = lambda *a, **k: None
    config = types.ModuleType("config")
    for name, value in (("SCALE_PARITY", 0), ("SCALE_BAUD", 19200),
                        ("SCALE_UART_ID", 0), ("SCALE_BITS", 8),
                        ("SCALE_STOP", 1), ("PIN_SCALE_TX", 12),
                        ("PIN_SCALE_RX", 13)):
        setattr(config, name, value)
    saved = {k: sys.modules.get(k) for k in ("machine", "config", "time")}
    sys.modules["machine"] = machine
    sys.modules["config"] = config
    sys.modules["time"] = fake_time
    try:
        exec(compile(balance_zero.DEVICE_SNIPPET, "<snippet>", "exec"), ns)
    finally:
        for k, v in saved.items():
            if v is None:
                sys.modules.pop(k, None)
            else:
                sys.modules[k] = v
    return "\n".join(printed)


def check(cond, msg):
    if not cond:
        raise AssertionError(msg)


def test_z_alone_when_in_range():
    uart = FakeUART(offset_mg=-40.0)
    out = run_snippet(uart)
    _before, cmds, samples = balance_zero.parse(out)
    check(cmds == ["Z"], "in-range re-zero should send Z only, got {}".format(cmds))
    check("T" not in uart.commands, "T must not be sent when Z worked")
    check(samples, "expected samples")
    check(abs(samples[-1][2]) < 1.0,
          "balance should read ~0 after a successful Z, got {}".format(samples[-1][2]))


def test_falls_back_to_tare_when_z_refused():
    # 4.2 g out -- the real 2026-08-21 case, well outside the re-zero band.
    uart = FakeUART(offset_mg=-4200.0)
    out = run_snippet(uart)
    _before, cmds, samples = balance_zero.parse(out)
    check(cmds == ["Z", "T"],
          "an out-of-range offset must escalate Z -> T, got {}".format(cmds))
    check(abs(samples[-1][2]) < 1.0,
          "T should have cleared the offset, got {}".format(samples[-1][2]))


def test_no_command_when_check_only():
    uart = FakeUART(offset_mg=-4200.0)
    out = run_snippet(uart, do_zero=False)
    _before, cmds, _samples = balance_zero.parse(out)
    check(cmds == [], "--check-only must not send a zero/tare command")
    check(uart.commands and set(uart.commands) == {"Q"},
          "--check-only must only query, got {}".format(set(uart.commands)))
    check(uart.offset_mg == -4200.0, "--check-only must not change the balance")


def test_parse_returns_three_values_and_survey_agrees():
    out = "BEFORE,US,-4200.0\nCMD,Z\nCMD,T\n0,ST,0.1\n180,ST,0.2\nEND\n"
    result = balance_zero.parse(out)
    check(len(result) == 3, "parse() must return (before, cmds, samples)")
    before, cmds, samples = result
    check(before == ["US", "-4200.0"], "before row mis-parsed: {}".format(before))
    check(cmds == ["Z", "T"], "CMD rows mis-parsed: {}".format(cmds))
    check(len(samples) == 2, "expected 2 samples, got {}".format(len(samples)))
    # balance_environment_survey.py imports parse(); a signature change that
    # is not mirrored there fails only on the bench, mid-session.
    survey = (ROOT / "scripts" / "balance_environment_survey.py").read_text()
    check("parse(stdout)" in survey, "survey no longer calls parse()")
    for line in survey.splitlines():
        if "= parse(stdout)" in line:
            names = line.split("=")[0].strip()
            check(len(names.split(",")) == 3,
                  "survey unpacks parse() into {} names, not 3: {!r}".format(
                      len(names.split(",")), line.strip()))


def test_snippet_documents_why_the_fallback_exists():
    src = balance_zero.DEVICE_SNIPPET
    check("range-limited" in src,
          "the snippet should say why Z can fail, or the next reader will "
          "'simplify' the fallback away")
    check("erCd" in src, "the silent-refusal reason should be recorded")


def _run_on_device_with(stdout="", stderr="", returncode=0):
    """Drive run_on_device() against a stubbed ssh, returning the remote script."""
    import os
    import subprocess as _sp

    captured = {}

    class FakeProc:
        def __init__(self):
            self.stdout, self.stderr, self.returncode = stdout, stderr, returncode

    def fake_run(argv, **kwargs):
        captured["remote"] = kwargs.get("input", "")
        return FakeProc()

    saved_run, saved_env = _sp.run, dict(os.environ)
    os.environ["RPI_POWDER_DOSER_USERNAME"] = "u"
    os.environ["RPI_POWDER_DOSER_HOSTNAME"] = "h"
    balance_zero.subprocess.run = fake_run
    try:
        out = balance_zero.run_on_device(False, 400, "/dev/ttyACM0")
        return captured.get("remote", ""), out
    finally:
        balance_zero.subprocess.run = saved_run
        os.environ.clear()
        os.environ.update(saved_env)


def test_mpremote_failure_is_not_swallowed_by_the_cleanup_rm():
    # The remote command used to end `mpremote ... run X; rm -f X`, so ssh
    # reported rm's status.  A failed mpremote then exited 0 with empty
    # output, and summarize() blamed the balance.
    remote, _out = _run_on_device_with()
    tail = remote.strip().splitlines()[-1]
    check("rc=$?" in tail and tail.rstrip().endswith("exit $rc"),
          "mpremote's exit status must survive the cleanup rm: {!r}".format(tail))
    check(tail.index("rc=$?") < tail.index("rm -f"),
          "the status has to be captured before rm runs: {!r}".format(tail))


def test_busy_port_is_not_diagnosed_as_a_dead_balance():
    # 2026-09-03: a parallel session held /dev/ttyACM0 for a servo
    # diagnostic.  The script printed "no samples -- is the balance switched
    # on?" and the balance was fine.  Wrong instrument blamed, wrong fix.
    busy = "mpremote: failed to access /dev/ttyACM0 (it may be in use by another program)"
    for where in ("stdout", "stderr"):
        try:
            _run_on_device_with(**{where: busy}, returncode=1)
        except SystemExit as exc:
            msg = str(exc)
            check("busy" in msg, "a busy port should say so, got {!r}".format(msg))
            check("switched on" not in msg,
                  "a busy port must not be reported as a dead balance")
        else:
            raise AssertionError("a busy port on {} should abort".format(where))


def main():
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
    print("all balance_zero checks passed")


if __name__ == "__main__":
    main()
