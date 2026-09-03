#!/usr/bin/env python3
"""Re-zero the A&D HR-100A balance over RS-232, without opening the enclosure.

Why this exists
---------------
Pressing the balance's front-panel ``RE-ZERO`` key means reaching into the
fume hood and past the breeze break.  That is exactly the disturbance the
balance's stability check rejects, so the press comes back as ``Error 1``
(``EC,E11``, stability error -- see section 19-2 of the HR-A/HR-AZ manual).
The same operation issued as an A&D ``Z`` command is documented as *"Same
as the RE-ZERO key"* and succeeds with the enclosure closed, because
nothing touches the rig.

So: **do not tare this balance by hand.**  Run this instead.

Usage::

    python scripts/balance_zero.py                # re-zero, then verify
    python scripts/balance_zero.py --check-only   # read without re-zeroing
    python scripts/balance_zero.py --settle 240   # longer drift capture
    python scripts/balance_zero.py --csv out.csv  # save the samples

It runs on the host and drives the Pico over the Pi via ``mpremote``, the
same path ``powder_battery_capture.py`` uses.  The Pi's hostname and
credentials come from the environment (``RPI_POWDER_DOSER_*``) and are
never printed, per ``CLAUDE.md``.

It only ever sends query and re-zero commands -- no stepper, servo or
solenoid is touched, so it is safe to run with a loaded auger.
"""

from __future__ import annotations

import argparse
import os
import shlex
import subprocess
import sys

PICO_PORT = "/dev/ttyACM0"
PI_VENV = "~/powder-doser-venv/bin/activate"

# Runs on the Pico.  Keeps its own UART framing so it does not depend on
# which revision of scale.py happens to be deployed.
DEVICE_SNIPPET = r'''
import time
from machine import UART, Pin
import config

parity = {0: None, 1: 1, 2: 0}[config.SCALE_PARITY]
u = UART(config.SCALE_UART_ID, baudrate=config.SCALE_BAUD,
         bits=config.SCALE_BITS, parity=parity, stop=config.SCALE_STOP,
         tx=Pin(config.PIN_SCALE_TX), rx=Pin(config.PIN_SCALE_RX), timeout=0)

_buf = b""


def _line(timeout_ms):
    global _buf
    t0 = time.ticks_ms()
    while time.ticks_diff(time.ticks_ms(), t0) < timeout_ms:
        chunk = u.read()
        if chunk:
            _buf += chunk
        idx = _buf.find(b"\n")
        if idx >= 0:
            line = _buf[:idx]
            _buf = _buf[idx + 1:]
            return line.decode().strip()
        time.sleep_ms(10)
    return None


def query():
    """One immediate datum as (status, milligrams), or (None, None)."""
    global _buf
    _buf = b""
    u.write(b"Q\r\n")
    line = _line(1500)
    if not line or len(line) < 4 or line[2] != ",":
        return None, None
    status = line[:2]
    if status == "OL":
        return status, None
    body = line[3:].replace("g", "").strip()
    try:
        return status, float(body) * 1000.0
    except ValueError:
        return status, None


def send(cmd):
    global _buf
    _buf = b""
    u.write(cmd + b"\r\n")
    time.sleep_ms(1800)


if DO_ZERO:
    st, mg = query()
    print("BEFORE,%s,%s" % (st, mg))
    # A&D 'Z' is the RE-ZERO key: full precision, but range-limited to a few
    # percent of capacity around the calibrated zero, and this balance has
    # erCd=0 so a refusal is silent.  A stale mid-run tare can easily leave
    # the display several grams out, which 'Z' will not clear.  'T' (tare) is
    # full-range, so fall back to it when 'Z' visibly did not take.
    send(b"Z")
    print("CMD,Z")
    st2, mg2 = query()
    if mg2 is None or abs(mg2) > 500.0:
        send(b"T")
        print("CMD,T")

print("t_ms,status,mg")
t0 = time.ticks_ms()
while time.ticks_diff(time.ticks_ms(), t0) < SETTLE_MS:
    st, mg = query()
    if st is not None:
        print("%d,%s,%s" % (time.ticks_diff(time.ticks_ms(), t0), st, mg))
    time.sleep_ms(180)
print("END")
'''


def pi_target() -> str:
    user = os.environ.get("RPI_POWDER_DOSER_USERNAME")
    host = os.environ.get("RPI_POWDER_DOSER_HOSTNAME")
    if not user or not host:
        sys.exit("set RPI_POWDER_DOSER_USERNAME and RPI_POWDER_DOSER_HOSTNAME "
                 "(injected by the workflow; never print their values)")
    return "{}@{}".format(user, host)


def run_on_device(do_zero: bool, settle_ms: int, port: str) -> str:
    header = "DO_ZERO = {}\nSETTLE_MS = {}\n".format(bool(do_zero), int(settle_ms))
    script = header + DEVICE_SNIPPET
    # Built by concatenation, not str.format: the device snippet contains
    # literal braces (the parity dict) that format() would try to expand.
    remote = (
        "cat > /tmp/_balance_zero.py <<'__EOF__'\n" + script + "\n__EOF__\n"
        + "source " + PI_VENV
        + "; mpremote connect " + shlex.quote(port)
        + " run /tmp/_balance_zero.py; rm -f /tmp/_balance_zero.py"
    )
    proc = subprocess.run(
        ["ssh", "-o", "StrictHostKeyChecking=no", pi_target(), "bash -s"],
        input=remote, text=True, capture_output=True,
        timeout=max(120, settle_ms // 1000 + 120),
    )
    if proc.returncode != 0:
        sys.exit("device command failed ({}): {}".format(
            proc.returncode, proc.stderr.strip()[-400:]))
    return proc.stdout


def summarize(samples: list[tuple[float, str, float]]) -> None:
    if not samples:
        print("[balance] no samples -- is the balance switched on?")
        return
    mg = [s[2] for s in samples]
    t = [s[0] for s in samples]
    n = len(mg)
    stable = sum(1 for s in samples if s[1] == "ST")
    mean = sum(mg) / n
    sd = (sum((v - mean) ** 2 for v in mg) / n) ** 0.5
    jitter = (sum(abs(mg[i + 1] - mg[i]) for i in range(n - 1)) / (n - 1)
              if n > 1 else 0.0)
    print("[balance] {} samples over {:.0f} s, {}/{} stable ({:.0f} %)".format(
        n, t[-1], stable, n, 100.0 * stable / n))
    print("[balance] first {:+.2f} mg   last {:+.2f} mg".format(mg[0], mg[-1]))
    print("[balance] sd {:.2f} mg   peak-to-peak {:.2f} mg".format(
        sd, max(mg) - min(mg)))
    print("[balance] sample-to-sample jitter {:.3f} mg  "
          "(draft noise lives here)".format(jitter))
    # Split the two failure modes: fast draft noise vs slow baseline walk.
    if jitter > 0.30:
        print("[balance] WARNING high jitter -- drafts. Is the breeze break "
              "closed and the sash down?")
    wander = max(mg) - min(mg)
    if wander > 5.0:
        print("[balance] WARNING baseline moved {:.1f} mg, more than the "
              "+/-5 mg block G tolerance. Let it settle, and check that "
              "nothing touches the vessel.".format(wander))
    if abs(mg[-1]) > 5.0:
        print("[balance] WARNING ended {:+.1f} mg from zero".format(mg[-1]))


def parse(stdout: str):
    samples = []
    before = None
    cmds = []
    for line in stdout.splitlines():
        line = line.strip()
        if line.startswith("BEFORE,"):
            before = line.split(",", 2)[1:]
            continue
        if line.startswith("CMD,"):
            cmds.append(line.split(",", 1)[1])
            continue
        parts = line.split(",")
        if len(parts) != 3 or not parts[0].isdigit():
            continue
        try:
            samples.append((int(parts[0]) / 1000.0, parts[1], float(parts[2])))
        except ValueError:
            continue
    return before, cmds, samples


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--check-only", action="store_true",
                    help="read the balance without re-zeroing it")
    ap.add_argument("--settle", type=float, default=20.0,
                    help="seconds of readings to take afterwards (default 20)")
    ap.add_argument("--csv", help="write the samples to this CSV")
    ap.add_argument("--port", default=PICO_PORT)
    args = ap.parse_args(argv)

    out = run_on_device(not args.check_only, int(args.settle * 1000), args.port)
    before, cmds, samples = parse(out)

    if before is not None:
        status, mg = before
        print("[balance] before re-zero: {} {} mg".format(status, mg))
        if "T" in cmds:
            print("[balance] sent A&D 'Z' (the RE-ZERO key); it was refused as "
                  "out of re-zero range, so sent 'T' (tare, full range)")
        else:
            print("[balance] sent A&D 'Z' (documented as 'Same as the RE-ZERO key')")
    summarize(samples)

    if args.csv:
        with open(args.csv, "w") as fh:
            fh.write("t_s,status,mg\n")
            for t, st, mg in samples:
                fh.write("{:.3f},{},{:.4f}\n".format(t, st, mg))
        print("[balance] wrote {}".format(args.csv))

    if not samples:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
