#!/usr/bin/env python3
"""Host-side runner for balance_stream.py: run a tare-and-stream capture
on the Pico and save the output to a named file.

``mpremote run`` does not forward keyboard input to the device, so this
wrapper takes the duration here on the host, substitutes it into the
device script, runs it, and tees every line to both the console and the
output file.

Usage (from this directory, Pico on USB, ``pip install mpremote``):

    python balance_stream_host.py 40 a1_drop_0p5g_rep01.csv
    python balance_stream_host.py 60 baseline.csv --label "post-tare quiet check"
    python balance_stream_host.py            # prompts for duration and file

Options: --label embeds a free-text tag in the file's metadata rows,
--device picks a serial port when mpremote's auto-detect grabs the
wrong one (e.g. COM5 or /dev/ttyACM0), --force allows overwriting an
existing output file.  Ctrl-C stops the capture early; whatever was
streamed so far is kept in the file.
"""

import argparse
import re
import subprocess
import sys
import tempfile
from pathlib import Path

DEVICE_SCRIPT = Path(__file__).with_name("balance_stream.py")


def build_payload(seconds, label):
    src = DEVICE_SCRIPT.read_text()
    src, n = re.subn(r"^DURATION_S = None.*$",
                     "DURATION_S = {:.3f}".format(seconds),
                     src, count=1, flags=re.M)
    if n != 1:
        sys.exit("could not find the DURATION_S line in {}".format(
            DEVICE_SCRIPT))
    # We save on the PC here; don't also leave a copy on the Pico's flash.
    src, n = re.subn(r"^OUTPUT_FILE = .*$", "OUTPUT_FILE = None",
                     src, count=1, flags=re.M)
    if n != 1:
        sys.exit("could not find the OUTPUT_FILE line in {}".format(
            DEVICE_SCRIPT))
    if label:
        src, n = re.subn(r'^LABEL = "".*$', "LABEL = {!r}".format(label),
                         src, count=1, flags=re.M)
        if n != 1:
            sys.exit("could not find the LABEL line in {}".format(
                DEVICE_SCRIPT))
    return src


def main():
    ap = argparse.ArgumentParser(
        description=__doc__.splitlines()[0],
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("seconds", nargs="?", type=float,
                    help="stream duration in seconds (prompted if omitted)")
    ap.add_argument("out", nargs="?",
                    help="output CSV file name (prompted if omitted)")
    ap.add_argument("--label", default="",
                    help="free-text tag stored in the file's metadata")
    ap.add_argument("--device", default="",
                    help="serial port for mpremote connect (default: auto)")
    ap.add_argument("--force", action="store_true",
                    help="overwrite the output file if it already exists")
    args = ap.parse_args()

    seconds = args.seconds
    while seconds is None or seconds <= 0:
        try:
            seconds = float(input("stream duration seconds: ").strip())
        except ValueError:
            seconds = None
    out = Path(args.out or input("output file name: ").strip())
    if out.exists() and not args.force:
        sys.exit("{} already exists (use --force to overwrite)".format(out))

    payload = build_payload(seconds, args.label)
    tmp = tempfile.NamedTemporaryFile(
        mode="w", suffix=".py", prefix="balance_stream_",
        delete=False)
    try:
        tmp.write(payload)
        tmp.close()
        cmd = ["mpremote"]
        if args.device:
            cmd += ["connect", args.device]
        cmd += ["run", tmp.name]
        print("running: {}".format(" ".join(cmd)))
        print("saving to: {}".format(out))
        lines = 0
        with out.open("w") as f:
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                                    stderr=subprocess.STDOUT,
                                    text=True, bufsize=1)
            try:
                for line in proc.stdout:
                    sys.stdout.write(line)
                    f.write(line)
                    lines += 1
            except KeyboardInterrupt:
                proc.terminate()
                print("\ninterrupted -- partial capture kept")
            rc = proc.wait()
        if rc not in (0, None) and lines == 0:
            sys.exit("mpremote failed (exit {}) -- is the Pico connected "
                     "and mpremote installed?".format(rc))
        print("saved {} lines to {}".format(lines, out))
    finally:
        Path(tmp.name).unlink(missing_ok=True)


if __name__ == "__main__":
    main()
