#!/usr/bin/env python3
"""Send a print to the Bambu Lab A1 mini ("Thumbelina").

The A1-mini-specific version of scripts/h2d_step3_send_print.py:

  1. Edit the FILL THESE IN block below (IP, access code, serial, and
     the path to the sliced .gcode.3mf you want to print).
  2. pip install paho-mqtt
  3. python a1_mini_send_print.py

It uploads the file to the printer's /cache over implicit FTPS
(TLS 1.2 session reuse - the same stack verified against the H2D in
PR #23; the FTPS quirks are fleet-wide Bambu behaviour, not
model-specific), publishes the `print.project_file` MQTT command, and
watches device/<SERIAL>/report until `gcode_state` reaches RUNNING.

A1-mini extras over the H2D script:
  - Refuses files that look sliced for another printer (the IDEX
    header in an H2D .gcode.3mf is exactly what single-extruder
    firmware chokes on). Override with --force if you know better.
  - USE_AMS / AMS_MAPPING knobs for an AMS lite (defaults print from
    the external spool holder).

Everything in the FILL THESE IN block can also be given on the command
line (--ip/--access-code/--serial and the file as a positional
argument) or via A1_MINI_IP / A1_MINI_ACCESS_CODE / A1_MINI_SERIAL env
vars - CLI beats env vars beats the constants below.

CAUTION: this starts a REAL print. Clear the bed first. The script
asks for confirmation before publishing; pass --yes to skip.
"""

# ======================= FILL THESE IN =======================
# Find these on the printer's touchscreen (see Step 1 of
# docs/a1-mini-programmatic-access.md):
PRINTER_IP = "PUT_PRINTER_IP_HERE"          # e.g. "192.168.1.42"  (Settings -> WLAN)
ACCESS_CODE = "PUT_ACCESS_CODE_HERE"        # 8-digit code         (Settings -> WLAN)
SERIAL = "PUT_SERIAL_HERE"                  # 15 characters        (Settings -> Device)

# Path to the sliced file you want to print. MUST be a .gcode.3mf
# sliced with an A1 mini profile (export from Bambu Studio, or the CLI
# recipe in the doc). Windows users: keep the r"" prefix.
FILE_TO_PRINT = r"PUT_PATH_TO_YOUR_FILE_HERE.gcode.3mf"  # e.g. r"C:\Users\me\cube_a1m.gcode.3mf"

# AMS lite: leave as-is to print from the external spool holder. To
# feed from an AMS lite set USE_AMS = True and AMS_MAPPING to the tray
# mapping (see ac-dev-lab issues #147/#149 for working examples).
USE_AMS = False
AMS_MAPPING = ""
# =============================================================

import argparse
import ftplib
import json
import os
import socket
import ssl
import sys
import threading
import time
import zipfile

import paho.mqtt.client as mqtt


def _is_placeholder(value):
    return not value or "PUT_" in value or "_HERE" in value


# --- Implicit FTPS with TLS 1.2 session reuse ------------------------------
# Copied verbatim from h2d_smoketest.py so this file stays standalone (it
# gets dropped onto lab laptops on its own). Keep the copies in sync.
class ImplicitFTP_TLS(ftplib.FTP_TLS):
    def connect(self, host="", port=0, timeout=-999, source_address=None):
        if host:
            self.host = host
        if port:
            self.port = port
        if timeout != -999:
            self.timeout = timeout
        if source_address is not None:
            self.source_address = source_address
        self.sock = socket.create_connection((self.host, self.port), self.timeout)
        self.af = self.sock.family
        self.sock = self.context.wrap_socket(self.sock, server_hostname=self.host)
        self.file = self.sock.makefile("r", encoding=self.encoding)
        self.welcome = self.getresp()
        return self.welcome

    def ntransfercmd(self, cmd, rest=None):
        conn, size = ftplib.FTP.ntransfercmd(self, cmd, rest)
        if self._prot_p:
            conn = self.context.wrap_socket(
                conn,
                server_hostname=self.host,
                session=self.sock.session,
            )
        return conn, size


def make_ftps_context():
    ctx = ssl._create_unverified_context()
    ctx.minimum_version = ssl.TLSVersion.TLSv1_2
    ctx.maximum_version = ssl.TLSVersion.TLSv1_2
    return ctx


# --- A1-mini payload sanity check -------------------------------------------
def check_payload(path, force):
    """Best-effort check that `path` is a sliced job for an A1 mini.

    Returns a list of warnings; raises SystemExit on hard failures
    (not a sliced 3mf, or sliced for a different printer without
    --force).
    """
    warnings = []
    try:
        zf = zipfile.ZipFile(path)
    except zipfile.BadZipFile:
        sys.exit(f"ERROR: {path} is not a .3mf/zip archive - "
                 "did you point FILE_TO_PRINT at an STL? Slice it first.")
    names = zf.namelist()
    if "Metadata/plate_1.gcode" not in names:
        sys.exit(f"ERROR: {path} has no Metadata/plate_1.gcode - this is a "
                 "project 3MF, not a sliced .gcode.3mf. Slice it (Bambu "
                 "Studio export, or the CLI recipe in "
                 "docs/a1-mini-programmatic-access.md) and retry.")

    # The BambuStudio G-code header names the target printer and, on
    # IDEX machines, carries filament_map lines. Scan the first ~200
    # header lines only.
    with zf.open("Metadata/plate_1.gcode") as f:
        header = []
        for _ in range(200):
            line = f.readline().decode("utf-8", "replace")
            if not line:
                break
            header.append(line)
    header_text = "".join(header)

    wrong_printer = "H2D" in header_text or "filament_map_mode" in header_text
    if wrong_printer:
        msg = (f"{path} looks sliced for an H2D/IDEX printer (its header "
               "carries the dual-extruder metadata a single-extruder A1 "
               "mini will choke on). Re-slice with an A1 mini profile.")
        if force:
            warnings.append("WARN (--force): " + msg)
        else:
            sys.exit("ERROR: " + msg + " Pass --force to send it anyway.")
    elif "A1" not in header_text:
        warnings.append("WARN: could not confirm an A1 mini profile in the "
                        "G-code header - make sure this file was sliced "
                        "for the A1 mini.")
    return warnings


# --- FTPS upload -------------------------------------------------------------
def upload(ip, code, local_path, remote_name):
    ftps = ImplicitFTP_TLS(context=make_ftps_context())
    ftps.connect(ip, 990, 30)
    ftps.login("bblp", code)
    ftps.prot_p()
    with open(local_path, "rb") as f:
        resp = ftps.storbinary(f"STOR /cache/{remote_name}", f)
    listing = ftps.nlst("/cache")
    ftps.quit()
    print(f"FTPS upload: {resp}")
    print(f"FTPS /cache now: {listing}")
    if remote_name not in " ".join(listing):
        print("WARN: uploaded file not visible in /cache listing - "
              "check the url path before blaming the printer.")
    return resp


# --- print.project_file payload ---------------------------------------------
def project_file_payload(remote_name, use_ams, ams_mapping):
    return {
        "print": {
            "sequence_id": "0",
            "command": "project_file",
            "param": "Metadata/plate_1.gcode",
            "project_id": "0",
            "profile_id": "0",
            "task_id": "0",
            "subtask_id": "0",
            "subtask_name": "",
            # Three slashes are intentional: ftp:// + absolute path /cache/...
            "url": f"ftp:///cache/{remote_name}",
            "md5": "",
            "timelapse": False,
            "bed_type": "auto",
            "bed_levelling": True,
            "flow_cali": True,
            "vibration_cali": True,
            "layer_inspect": True,
            "ams_mapping": ams_mapping,
            "use_ams": use_ams,
        }
    }


# --- publish start command, watch gcode_state --------------------------------
def start_and_watch(ip, code, serial, remote_name, use_ams, ams_mapping,
                    watch_seconds):
    states = []          # ordered gcode_state transitions seen
    running = threading.Event()
    failed = threading.Event()

    def on_msg(c, u, m):
        try:
            report = json.loads(m.payload)
        except ValueError:
            return
        p = report.get("print", {})
        state = p.get("gcode_state")
        if state and (not states or states[-1] != state):
            states.append(state)
            print(f"gcode_state: {' -> '.join(states)}")
            if state == "RUNNING":
                running.set()
            if state in ("FAILED", "OFFLINE"):
                failed.set()
        err = p.get("print_error")
        if err not in (None, 0, "0"):
            print(f"print_error: {err}")
            failed.set()

    c = mqtt.Client()
    c.username_pw_set("bblp", code)
    c.tls_set(cert_reqs=ssl.CERT_NONE)
    c.tls_insecure_set(True)
    c.on_message = on_msg
    c.connect(ip, 8883, 30)
    c.subscribe(f"device/{serial}/report")
    c.loop_start()

    request_topic = f"device/{serial}/request"
    # Ask for a full status push so we see the pre-print gcode_state too
    # (reports are otherwise incremental).
    c.publish(request_topic,
              json.dumps({"pushing": {"sequence_id": "0", "command": "pushall"}}))
    time.sleep(2)

    payload = project_file_payload(remote_name, use_ams, ams_mapping)
    print(f"Publishing print.project_file for ftp:///cache/{remote_name} ...")
    c.publish(request_topic, json.dumps(payload))

    deadline = time.monotonic() + watch_seconds
    while time.monotonic() < deadline and not running.is_set() and not failed.is_set():
        time.sleep(1)

    c.loop_stop()
    c.disconnect()

    if running.is_set():
        print("SUCCESS: printer reached RUNNING.")
        return 0
    if failed.is_set():
        print("FAILED: printer reported an error - see the Step 3 triage "
              "list in docs/a1-mini-programmatic-access.md.")
        return 2
    print(f"TIMEOUT: no RUNNING within {watch_seconds}s "
          f"(states seen: {' -> '.join(states) or 'none'}). "
          "See the Step 3 triage list in docs/a1-mini-programmatic-access.md "
          "- an H2D-sliced or wrong-printer file shows up exactly like this.")
    return 3


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("file", nargs="?", default=None,
                        help="path to a sliced A1-mini .gcode.3mf "
                        "(overrides FILE_TO_PRINT at the top of this script)")
    parser.add_argument("--ip", default=os.environ.get("A1_MINI_IP"))
    parser.add_argument("--access-code", default=os.environ.get("A1_MINI_ACCESS_CODE"))
    parser.add_argument("--serial", default=os.environ.get("A1_MINI_SERIAL"))
    parser.add_argument("--use-ams", action="store_true", default=USE_AMS,
                        help="feed from the AMS lite instead of the "
                        "external spool holder")
    parser.add_argument("--ams-mapping", default=AMS_MAPPING,
                        help="AMS tray mapping (only with --use-ams)")
    parser.add_argument("--upload-only", action="store_true",
                        help="run the FTPS upload only; don't start a print")
    parser.add_argument("--force", action="store_true",
                        help="send even if the file looks sliced for a "
                        "different printer")
    parser.add_argument("--yes", action="store_true",
                        help="skip the clear-the-bed confirmation prompt")
    parser.add_argument("--watch", type=int, default=180, metavar="SECONDS",
                        help="how long to wait for RUNNING (default 180)")
    args = parser.parse_args()

    # CLI/env beats the FILL THESE IN constants; placeholders count as unset.
    ip = args.ip or (None if _is_placeholder(PRINTER_IP) else PRINTER_IP)
    code = args.access_code or (None if _is_placeholder(ACCESS_CODE) else ACCESS_CODE)
    serial = args.serial or (None if _is_placeholder(SERIAL) else SERIAL)
    path = args.file or (None if _is_placeholder(FILE_TO_PRINT) else FILE_TO_PRINT)

    missing = [n for n, v in [("printer IP", ip), ("access code", code),
                              ("serial", serial), ("file to print", path)]
               if not v]
    if missing:
        parser.error(
            "missing " + ", ".join(missing) + ". Edit the FILL THESE IN "
            "block at the top of this script (replace the PUT_..._HERE "
            "placeholders), or pass --ip/--access-code/--serial and the "
            "file path on the command line.")
    if not os.path.isfile(path):
        parser.error(f"no such file: {path}")

    for warning in check_payload(path, args.force):
        print(warning)

    remote_name = os.path.basename(path)
    upload(ip, code, path, remote_name)
    if args.upload_only:
        print("Upload-only mode: not starting a print.")
        return 0

    if not args.yes:
        answer = input(f"About to start a REAL print of {remote_name} on "
                       f"{serial}. Is the bed clear? [y/N] ")
        if answer.strip().lower() not in ("y", "yes"):
            print("Aborted before publishing. File remains in /cache.")
            return 1

    return start_and_watch(ip, code, serial, remote_name,
                           args.use_ams, args.ams_mapping, args.watch)


if __name__ == "__main__":
    sys.exit(main())
