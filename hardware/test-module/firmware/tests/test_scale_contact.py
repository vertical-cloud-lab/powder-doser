"""Dead-simple scale-contact diagnostic (MicroPython, zero keystrokes).

The single most common reason ``g <grams>`` "does nothing" is that the
Pico and the balance are not actually talking yet -- almost always a
swapped TX/RX pair, the wrong UART pins, or a serial-format mismatch.
This script makes that the *first* thing you can rule out: it opens the
scale UART, listens for traffic, asks the balance for one reading, and
prints a ``PASS`` / ``PARTIAL`` / ``FAIL`` verdict plus a focused
checklist.  On anything but a clean ``PASS`` it then re-opens the UART
at each *known* serial preset (HR-A factory 2400 7E1, AutoTrickler
19200 8N1) and probes again, so a balance whose settings were changed
for another system is identified in the same run.  No keypresses, no
dosing, no other channels -- just run it and read the verdict.

The hard-won lessons in the checklists come from the AC training-lab
RS-232 bring-up (AccelerationConsortium/ac-dev-lab#20), where the same
Waveshare-class RS-232 link stayed silent for weeks purely because the
TX/RX pair was not crossed over -- ``uart.any()`` was always 0 until
the scale's TX reached the Pico's RX and vice-versa.

Run it from VS Code + MicroPico ("Run current file on Pico"), exactly
like the other scripts in this folder.

The core :func:`probe_contact` takes a duck-typed scale object, so the
same logic is unit-tested under CPython against the simulated balance in
``sim/`` (see ``sim/test_dosing_sim.py``) -- this module imports
``machine`` lazily inside :func:`main` so it stays importable off-Pico.
"""

import sys

sys.path.insert(0, "..")
sys.path.insert(0, "/")

import config
import scale


SILENT_CHECKLIST = (
    "Most likely causes, in order:\n"
    "  1. TX/RX not landing where they should (the #1 cause of a silent\n"
    "     link). The Waveshare Pico-2CH-RS232 TTL header is labelled from\n"
    "     the Pico's point of view, so wire it straight across:\n"
    "       GP{tx} -> module TXD, GP{rx} <- module RXD.\n"
    "     If it is still silent, the remaining crossover is on the DB9 /\n"
    "     RS-232 cable to the balance (the scale's TX must reach the\n"
    "     module's RX path).  A swapped pair anywhere gives this result.\n"
    "  2. Wrong UART / pins. This build uses UART{uart} on GP{tx}/GP{rx};\n"
    "     make sure the wires land there (not the Tic's UART1 GP4/GP5).\n"
    "  3. Module unpowered. Feed the Pico's +3V3 (NOT 5 V, so RXD stays\n"
    "     Pico-safe) to the module's VSYS pin position (physical pin 39\n"
    "     -- that is what powers the SP3232) AND to its 3V3 position\n"
    "     (pin 36 -- that only powers the LEDs, so a lit PWR LED alone\n"
    "     does not prove the transceiver has power). GND to GND.\n"
    "  4. Scale serial settings changed from factory. There is no RS-232\n"
    "     on/off switch on the HR-A -- factory settings (2400/7/E/1)\n"
    "     answer 'Q' with no menu changes -- but a balance once set up\n"
    "     for an AutoTrickler runs 19200/8/N/1 instead (its setup guide\n"
    "     sets Sif bPS=5 + btPr=2) and discards our 'Q' SILENTLY\n"
    "     (factory erCd 0 = no error replies); key mode never transmits\n"
    "     on its own: zero bytes, same as a cut wire. This probe now\n"
    "     auto-scans the known presets -- see the scan verdict below.\n"
    "     On the balance: hold SAMPLE until bASFnc, tap SAMPLE to\n"
    "     5if, PRINT to enter, check bp5 2 (2400) + btpr 0 (7/even).\n"
    "     Tip: PRINT on a stable display (or dout prt 3 = stream mode)\n"
    "     makes the balance transmit WITHOUT our 'Q' -- if even that\n"
    "     yields nothing here, the fault is wiring, not settings.\n"
    "  5. Harness pinout. Buzz it out with a meter -- an idle RS-232 TXD\n"
    "     sits at about -5..-9 V relative to GND, which finds the scale's\n"
    "     transmit pin.\n"
)

GARBLED_CHECKLIST = (
    "Bytes are arriving but nothing parsed -- the link is wired but the\n"
    "serial *format* is wrong. Match config.py to the balance settings:\n"
    "  baud={baud}, bits={bits}, parity={par}, stop={stop}\n"
    "  (A&D HR-A factory default is 2400 / 7 / even / 1, A&D standard\n"
    "  format).  A garbled dump almost always means the baud rate is off\n"
    "  -- the preset scan below tries the known alternatives.\n"
)

# Serial presets this bench has actually encountered, tried in order by
# the scan when config.py's own settings get nothing (or only garbage).
# Each entry is (label, baud, bits, parity, stop) with parity in
# config.py's encoding (0 = none, 1 = odd, 2 = even).  The settings live
# in the balance's non-volatile memory, so a scale that was once set up
# for an AutoTrickler keeps that preset (the official AutoTrickler
# setup guide sets Sif bPS=5 = 19200 baud and btPr=2 = 8N1) and stays
# silent at the HR-A factory 2400 7E1.
KNOWN_SERIAL_PRESETS = (
    ("A&D HR-A factory default", 2400, 7, 2, 1),
    ("AutoTrickler (Sif bPS=5, btPr=2)", 19200, 8, 0, 1),
)


def probe_contact(sc, listen_ms=2000, attempts=5, sleep_ms=None):
    """Check whether the balance is talking on ``sc``'s UART.

    Returns a dict with:
      ``saw_bytes`` -- any bytes (parseable or not) arrived,
      ``raw``       -- raw bytes captured (when the UART exposes ``read``),
      ``frames``    -- parsed :class:`scale.ScaleReading` objects,
      ``reading``   -- the first parsed reading, or ``None``.

    Uses only the duck-typed ``write`` / ``readline`` / ``any`` surface
    (plus an optional raw ``read``) so it runs unchanged against both a
    real ``machine.UART`` and the CPython ``SimScaleUart`` test double.
    """
    if sleep_ms is None:
        sleep_ms = sc._sleep_ms
    uart = sc.uart
    raw = b""
    frames = []
    saw_bytes = False
    has_read = hasattr(uart, "read")

    # 1) Passive listen -- catch balances configured to stream readings.
    # The UART is non-blocking, so 50 ms polls see ~12 chars each while
    # a full frame is ~17 chars: buffer the bytes and only parse
    # complete lines, or every streamed frame would look torn/garbled.
    linebuf = b""
    waited = 0
    while waited < listen_ms:
        if has_read:
            chunk = uart.read()
            if chunk:
                saw_bytes = True
                raw += chunk
                linebuf += chunk
                pieces = linebuf.replace(b"\r", b"\n").split(b"\n")
                linebuf = pieces.pop()      # keep the incomplete tail
                for piece in pieces:
                    reading = scale.parse_frame(piece)
                    if reading is not None:
                        frames.append(reading)
        else:
            line = uart.readline()
            if line:
                saw_bytes = True
                reading = scale.parse_frame(line)
                if reading is not None:
                    frames.append(reading)
        sleep_ms(50)
        waited += 50

    # 2) Active poll -- explicitly request a datum (A&D 'Q' command).
    for _ in range(attempts):
        reading = sc.read()
        if reading is not None:
            saw_bytes = True
            frames.append(reading)
            break
        # Garbled bytes may sit unread on the UART *or* already pulled
        # into the driver's line buffer -- either way, bytes arrived
        # (that's a PARTIAL, i.e. a serial-format problem, not FAIL).
        if hasattr(uart, "any") and uart.any():
            saw_bytes = True
        if getattr(sc, "_rxbuf", b""):
            saw_bytes = True
        sleep_ms(50)

    return {"saw_bytes": saw_bytes, "raw": raw, "frames": frames,
            "reading": frames[0] if frames else None}


def scan_serial_settings(make_scale, presets=KNOWN_SERIAL_PRESETS,
                         skip=None, listen_ms=1000, attempts=3):
    """Probe each known serial preset until one yields bytes.

    ``make_scale(baud, bits, parity, stop)`` must return a fresh scale
    client whose UART was re-opened with those parameters.  ``skip`` is
    the ``(baud, bits, parity, stop)`` tuple already probed (normally
    config.py's), so it is not tried twice.  Returns
    ``(preset, result)`` for the first preset whose probe saw bytes, or
    ``None`` when every preset stayed silent.
    """
    for preset in presets:
        _, baud, bits, parity, stop = preset
        if skip == (baud, bits, parity, stop):
            continue
        sc = make_scale(baud, bits, parity, stop)
        result = probe_contact(sc, listen_ms=listen_ms, attempts=attempts)
        if result["saw_bytes"]:
            return preset, result
    return None


def report_scan(hit):
    """Print a human verdict for a :func:`scan_serial_settings` result."""
    if hit is None:
        print("[scale-contact] preset scan: silent at every known preset\n"
              "  -> the balance is not reaching the Pico at ANY baud rate,\n"
              "     so the fault is wiring/power (checklist items 1-3),\n"
              "     not the balance's serial settings.")
        return
    preset, result = hit
    label, baud, bits, parity, stop = preset
    par = {0: "N", 1: "O", 2: "E"}.get(parity, str(parity))
    print("[scale-contact] preset scan: the balance ANSWERED at "
          "{} {}{}{} -- {}.".format(baud, bits, par, stop, label))
    if result["reading"] is not None:
        r = result["reading"]
        print("  parsed: status={} grams={} unit={!r}".format(
            r.status, r.grams, r.unit))
    print("  The harness is GOOD (ignore the wiring checklist above);\n"
          "  config.py and the balance just disagree on serial settings.\n"
          "  Fix ONE side:\n"
          "    a) config.py: SCALE_BAUD={}, SCALE_BITS={}, SCALE_PARITY={},\n"
          "       SCALE_STOP={} -- then re-upload + soft-reset; or\n"
          "    b) the balance: hold SAMPLE until bASFnc, tap SAMPLE to\n"
          "       5if, PRINT to enter, set bp5 2 / btpr 0 to restore the\n"
          "       HR-A factory 2400 7E1 (RE-ZERO cycles values, PRINT\n"
          "       stores, CAL exits).".format(baud, bits, parity, stop))


class _Override:
    """Read-through view of ``config`` with a few attributes replaced,
    so :func:`scale.open_uart` can be re-driven at scan settings without
    mutating the real config module.
    """

    def __init__(self, base, **overrides):
        self._base = base
        for name, value in overrides.items():
            setattr(self, name, value)

    def __getattr__(self, name):
        return getattr(self._base, name)


def _fmt(template):
    par = {0: "N (none)", 1: "O (odd)", 2: "E (even)"}.get(
        config.SCALE_PARITY, str(config.SCALE_PARITY))
    return template.format(
        uart=config.SCALE_UART_ID, tx=config.PIN_SCALE_TX,
        rx=config.PIN_SCALE_RX, baud=config.SCALE_BAUD,
        bits=config.SCALE_BITS, par=par, stop=config.SCALE_STOP)


def report(result):
    """Print a human verdict for a :func:`probe_contact` result dict."""
    if result["reading"] is not None:
        reading = result["reading"]
        print("[scale-contact] PASS -- the balance is talking.")
        print("  parsed: status={} grams={} unit={!r}".format(
            reading.status, reading.grams, reading.unit))
    elif result["saw_bytes"]:
        print("[scale-contact] PARTIAL -- bytes arriving but unparseable.")
        if result["raw"]:
            print("  raw: {!r}".format(result["raw"][:120]))
        print(_fmt(GARBLED_CHECKLIST))
    else:
        print("[scale-contact] FAIL -- silent link (no bytes at all).")
        print(_fmt(SILENT_CHECKLIST))


def main():
    from machine import Pin, UART

    # Non-blocking UART (timeout=0) is what keeps this probe honest:
    # with a blocking hardware timeout every read on a silent link
    # stalls ~1 s while the wait counters below only advance 20-50 ms,
    # stretching the "2 s" probe to ~5 minutes of apparent hang
    # (PR #100 "test_scale_contact runs forever").
    uart = scale.open_uart(config, UART, Pin)
    sc = scale.AndScale(
        uart, response_timeout_ms=config.SCALE_RESPONSE_TIMEOUT_MS)

    print(_fmt("[scale-contact] UART{uart} GP{tx}/GP{rx} @ {baud} {bits}"
               "/{par}/{stop} -- probing (no keypress needed)..."))
    result = probe_contact(sc)
    report(result)

    if result["reading"] is None:
        # Nothing parseable at config.py's settings.  The balance may
        # simply be talking at a different baud/parity -- e.g. a scale
        # that was once set up for an AutoTrickler answers only at
        # 19200 8N1.  Re-open the UART at each known preset and probe
        # again (~5 s per preset).
        print("[scale-contact] scanning other known serial presets...")

        def make_scale(baud, bits, parity, stop):
            u = scale.open_uart(
                _Override(config, SCALE_BAUD=baud, SCALE_BITS=bits,
                          SCALE_PARITY=parity, SCALE_STOP=stop),
                UART, Pin)
            return scale.AndScale(
                u, response_timeout_ms=config.SCALE_RESPONSE_TIMEOUT_MS)

        skip = (config.SCALE_BAUD, config.SCALE_BITS,
                config.SCALE_PARITY, config.SCALE_STOP)
        report_scan(scan_serial_settings(make_scale, skip=skip))


if __name__ == "__main__":
    main()
