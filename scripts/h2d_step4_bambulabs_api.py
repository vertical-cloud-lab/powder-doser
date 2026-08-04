#!/usr/bin/env python3
"""Step 4 - the same print as Step 3, driven through `bambulabs_api`.

Once Step 3 is green from the raw FTPS/MQTT script, this is the
library-backed version you'd actually build on (it is also what the
Step 5/6 Pi relay in the doc wraps in FastAPI). Internally
`bambulabs_api` does the identical implicit-FTPS upload + MQTT
`print.project_file` publish that h2d_step3_send_print.py does by hand.

Verified on the A1 mini ("Thumbelina") 2026-08-04 with
payloads/Testpart2.gcode.3mf - print started and completed. Still
unexercised on the H2D itself.

CAUTION: this starts a REAL print. Clear the bed first. The script asks
for confirmation; pass --yes to skip (for automation).

    pip install bambulabs_api
    python h2d_step4_bambulabs_api.py cube_h2d.gcode.3mf \
        --ip <IP> --access-code <CODE> --serial <SERIAL>

    # A1 mini feeding from AMS lite tray 2 (trays are 0-indexed):
    python h2d_step4_bambulabs_api.py part.gcode.3mf --use-ams --ams-mapping 1

Credentials may also come from H2D_IP / H2D_ACCESS_CODE / H2D_SERIAL
(or the A1_MINI_* equivalents, so one env file serves both printers).

Note: `bambulabs_api` is community-maintained and its signatures have
shifted between releases (see the H2D-untested caveat in the doc's
library table). This script targets the shape used in the project's own
examples - `Printer(ip, code, serial)`, `upload_file(fileobj, name)`
returning an FTP status string, `start_print(name, plate)` - and prints
the library version up front so a mismatch is easy to spot. Optional
kwargs (`use_ams`, `ams_mapping`) are passed defensively and dropped if
the installed release doesn't accept them.
"""

import argparse
import os
import re
import sys
import time

import bambulabs_api as bl


def env(*names):
    """First non-empty value among the named environment variables."""
    for name in names:
        value = os.environ.get(name)
        if value:
            return value
    return None


def normalize_ams_mapping(value):
    """Accept [0], "0", "0,1", or "[1]" and return a list of ints (AMS
    tray numbers, 0-indexed), or None for "no explicit mapping".

    Kept in sync with a1_mini_send_print.py - the bracketed string form
    is what LLM-suggested commands tend to produce, so accept it too.
    """
    if value in ("", None, []):
        return None
    if isinstance(value, str):
        parts = [p for p in re.split(r"[\s,;\[\]]+", value.strip()) if p]
        try:
            return [int(p) for p in parts]
        except ValueError:
            sys.exit('ERROR: --ams-mapping must be comma-separated tray '
                     f'numbers (e.g. "0" or "0,1"), got: {value!r}')
    return [int(v) for v in value]


def start_print(printer, remote_name, plate, use_ams, ams_mapping):
    """Call start_print with whatever kwargs this release understands.

    Releases differ on which of use_ams/ams_mapping exist; retry with a
    smaller kwarg set on TypeError rather than guessing a version.
    """
    attempts = [{"use_ams": use_ams}]
    if ams_mapping is not None:
        attempts.insert(0, {"use_ams": use_ams, "ams_mapping": ams_mapping})
    attempts.append({})
    for kwargs in attempts:
        try:
            return printer.start_print(remote_name, plate, **kwargs)
        except TypeError as exc:
            # Only a signature mismatch is retryable; a TypeError raised
            # from inside the library is a real bug and must surface.
            if "unexpected keyword" not in str(exc):
                raise
            print(f"NOTE: installed bambulabs_api rejected {sorted(kwargs)} "
                  f"({exc}); retrying with fewer arguments.")
    # Nothing matched - let the final, plainest call raise for real.
    return printer.start_print(remote_name, plate)


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("file", help="path to a sliced .gcode.3mf")
    parser.add_argument("--ip", default=env("H2D_IP", "A1_MINI_IP"))
    parser.add_argument("--access-code",
                        default=env("H2D_ACCESS_CODE", "A1_MINI_ACCESS_CODE"))
    parser.add_argument("--serial", default=env("H2D_SERIAL", "A1_MINI_SERIAL"))
    parser.add_argument("--plate", type=int, default=1,
                        help="plate number inside the 3MF (default 1)")
    parser.add_argument("--use-ams", dest="use_ams", action="store_true",
                        help="feed from the AMS instead of the external spool")
    parser.add_argument("--no-ams", dest="use_ams", action="store_false",
                        help="feed from the external spool holder (default)")
    parser.set_defaults(use_ams=False)
    parser.add_argument("--ams-mapping", default=None,
                        help='AMS tray per filament, 0-indexed - "0", "0,1" '
                             'or "[1]". Implies --use-ams.')
    parser.add_argument("--yes", action="store_true",
                        help="skip the clear-the-bed confirmation prompt")
    parser.add_argument("--watch", type=int, default=180, metavar="SECONDS",
                        help="how long to wait for RUNNING (default 180)")
    parser.add_argument("--no-wait", dest="wait_done", action="store_false",
                        help="exit once RUNNING instead of watching the print "
                             "through to FINISH")
    parser.set_defaults(wait_done=True)
    args = parser.parse_args()
    missing = [n for n, v in
               [("--ip", args.ip), ("--access-code", args.access_code),
                ("--serial", args.serial)] if not v]
    if missing:
        parser.error("missing " + ", ".join(missing) +
                     " (flags or H2D_IP/H2D_ACCESS_CODE/H2D_SERIAL env vars)")
    if not os.path.isfile(args.file):
        parser.error(f"no such file: {args.file}")

    ams_mapping = normalize_ams_mapping(args.ams_mapping)
    if ams_mapping is not None:
        args.use_ams = True

    print(f"bambulabs_api version: {getattr(bl, '__version__', 'unknown')}")
    # Spaces in the remote name break the printer's path parsing (field
    # note 4 in the A1-mini doc), so use the same charset the raw-MQTT
    # scripts sanitize to.
    remote_name = re.sub(r"[^A-Za-z0-9._-]", "_", os.path.basename(args.file))
    if remote_name != os.path.basename(args.file):
        print(f"NOTE: uploading as {remote_name} (sanitized - spaces and "
              "other characters break the printer's path parsing).")

    printer = bl.Printer(args.ip, args.access_code, args.serial)
    printer.connect()
    time.sleep(2)  # give the MQTT client a moment to receive first status
    try:
        print(f"Printer state before print: {printer.get_state()}")

        with open(args.file, "rb") as f:
            result = printer.upload_file(f, remote_name)
        print(f"Upload result: {result}")
        if "226" not in str(result):
            print("ERROR: FTPS upload did not return '226 Transfer complete' - "
                  "not starting a print.")
            return 2

        if args.use_ams:
            source = "AMS" + (f", tray mapping {ams_mapping}"
                              if ams_mapping is not None else "")
        else:
            source = "EXTERNAL spool holder"
        print(f"Filament source: {source}")
        if not args.yes:
            answer = input(f"About to start a REAL print of {remote_name} on "
                           f"{args.serial}. Is the bed clear? [y/N] ")
            if answer.strip().lower() not in ("y", "yes"):
                print("Aborted before start_print. File remains on the printer.")
                return 1

        start_print(printer, remote_name, args.plate, args.use_ams, ams_mapping)
        print("start_print sent; watching gcode_state ...")

        last = None
        running = False
        deadline = time.monotonic() + args.watch
        while True:
            state = str(printer.get_state())
            if state != last:
                print(f"gcode_state: {state}")
                last = state
            if state in ("FAILED", "OFFLINE"):
                print("FAILED: see the Step 3 triage list in "
                      "docs/h2d-programmatic-access.md.")
                return 2
            if state == "RUNNING" and not running:
                running = True
                print("SUCCESS: printer reached RUNNING.")
                if not args.wait_done:
                    return 0
                print("Watching until the print finishes - Ctrl-C detaches "
                      "WITHOUT stopping the print ...")
            # FINISH only counts once OUR job has been seen RUNNING: an
            # idle Bambu re-reports the PREVIOUS job's FINISH to every
            # fresh subscriber, which would otherwise fire immediately.
            if running and state == "FINISH":
                print("\a" + "=" * 62)
                print("PRINT COMPLETE: the printer reported gcode_state FINISH.")
                print("Remove the part from the bed before the next job.")
                print("=" * 62)
                return 0
            if not running and time.monotonic() > deadline:
                print(f"TIMEOUT: no RUNNING within {args.watch}s "
                      f"(last state: {last}).")
                return 3
            time.sleep(3)
    finally:
        printer.disconnect()


if __name__ == "__main__":
    sys.exit(main())
