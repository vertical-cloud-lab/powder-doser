#!/usr/bin/env python3
"""Step 4 - the same print as Step 3, driven through `bambulabs_api`.

Once Step 3 is green from the raw FTPS/MQTT script, this is the
library-backed version you'd actually build on (it is also what the
Step 5/6 Pi relay in the doc wraps in FastAPI). Internally
`bambulabs_api` does the identical implicit-FTPS upload + MQTT
`print.project_file` publish that h2d_step3_send_print.py does by hand.

CAUTION: this starts a REAL print. Clear the bed first. The script asks
for confirmation; pass --yes to skip (for automation).

    pip install bambulabs_api
    python h2d_step4_bambulabs_api.py cube_h2d.gcode.3mf \
        --ip <IP> --access-code <CODE> --serial <SERIAL>

Credentials may also come from H2D_IP / H2D_ACCESS_CODE / H2D_SERIAL.

Note: `bambulabs_api` is community-maintained and its signatures have
shifted between releases (see the H2D-untested caveat in the doc's
library table). This script targets the shape used in the project's own
examples - `Printer(ip, code, serial)`, `upload_file(fileobj, name)`
returning an FTP status string, `start_print(name, plate)` - and prints
the library version up front so a mismatch is easy to spot.
"""

import argparse
import os
import sys
import time

import bambulabs_api as bl


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("file", help="path to a sliced .gcode.3mf")
    parser.add_argument("--ip", default=os.environ.get("H2D_IP"))
    parser.add_argument("--access-code", default=os.environ.get("H2D_ACCESS_CODE"))
    parser.add_argument("--serial", default=os.environ.get("H2D_SERIAL"))
    parser.add_argument("--plate", type=int, default=1,
                        help="plate number inside the 3MF (default 1)")
    parser.add_argument("--yes", action="store_true",
                        help="skip the clear-the-bed confirmation prompt")
    parser.add_argument("--watch", type=int, default=180, metavar="SECONDS",
                        help="how long to wait for RUNNING (default 180)")
    args = parser.parse_args()
    missing = [n for n, v in
               [("--ip", args.ip), ("--access-code", args.access_code),
                ("--serial", args.serial)] if not v]
    if missing:
        parser.error("missing " + ", ".join(missing) +
                     " (flags or H2D_IP/H2D_ACCESS_CODE/H2D_SERIAL env vars)")
    if not os.path.isfile(args.file):
        parser.error(f"no such file: {args.file}")

    print(f"bambulabs_api version: {getattr(bl, '__version__', 'unknown')}")
    remote_name = os.path.basename(args.file)

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

        if not args.yes:
            answer = input(f"About to start a REAL print of {remote_name} on "
                           f"{args.serial}. Is the bed clear? [y/N] ")
            if answer.strip().lower() not in ("y", "yes"):
                print("Aborted before start_print. File remains on the printer.")
                return 1

        # The H2D dry run uses neither AMS; some releases don't take the
        # use_ams kwarg, so fall back to the positional-only form.
        try:
            printer.start_print(remote_name, args.plate, use_ams=False)
        except TypeError:
            printer.start_print(remote_name, args.plate)
        print("start_print sent; watching gcode_state ...")

        last = None
        deadline = time.monotonic() + args.watch
        while time.monotonic() < deadline:
            state = str(printer.get_state())
            if state != last:
                print(f"gcode_state: {state}")
                last = state
            if state == "RUNNING":
                print("SUCCESS: printer reached RUNNING.")
                return 0
            if state in ("FAILED", "OFFLINE"):
                print("FAILED: see the Step 3 triage list in "
                      "docs/h2d-programmatic-access.md.")
                return 2
            time.sleep(3)
        print(f"TIMEOUT: no RUNNING within {args.watch}s (last state: {last}).")
        return 3
    finally:
        printer.disconnect()


if __name__ == "__main__":
    sys.exit(main())
