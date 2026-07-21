#!/usr/bin/env python3
"""Step 3 - end-to-end dry run: upload a .gcode.3mf and start the print.

Does the doc's 3a/3b/3c in one command (Win/macOS/Linux, no lftp or
mosquitto needed):

  1. Uploads the file to the printer's /cache over implicit FTPS
     (TLS 1.2 session reuse - same verified stack as h2d_smoketest.py).
  2. Publishes the `print.project_file` command over MQTT-over-TLS.
  3. Watches device/<SERIAL>/report and prints every `gcode_state`
     transition; exits 0 once the state reaches RUNNING.

CAUTION: this starts a REAL print. Clear the bed first. The script asks
for confirmation before publishing; pass --yes to skip (for automation).

    pip install paho-mqtt
    python h2d_step3_send_print.py cube_h2d.gcode.3mf \
        --ip <IP> --access-code <CODE> --serial <SERIAL>

Credentials may also come from H2D_IP / H2D_ACCESS_CODE / H2D_SERIAL.
Use --upload-only to run just the FTPS leg (3a) without starting a print.

If gcode_state never leaves IDLE, see the triage list under Step 3 in
docs/h2d-programmatic-access.md (url path mismatch - note the THREE
slashes in ftp:///cache/..., wrong-printer slicer profile, or Developer
Mode silently re-disabled by a firmware update).
"""

import argparse
import ftplib
import json
import os
import socket
import ssl
import sys
import threading
import time

import paho.mqtt.client as mqtt


# --- Implicit FTPS with TLS 1.2 session reuse ------------------------------
# Copied verbatim from h2d_smoketest.py so this file stays standalone (it
# gets dropped onto lab laptops on its own). Keep the two in sync.
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


# --- Step 3a: FTPS upload ---------------------------------------------------
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


# --- Step 3c payload (matches the doc's verified minimal command) -----------
def project_file_payload(remote_name):
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
            "ams_mapping": "",
            "use_ams": False,
        }
    }


# --- Step 3b+3c: publish start command, watch gcode_state -------------------
def start_and_watch(ip, code, serial, remote_name, watch_seconds):
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

    payload = project_file_payload(remote_name)
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
        print("FAILED: printer reported an error - see triage list in the doc "
              "(Step 3).")
        return 2
    print(f"TIMEOUT: no RUNNING within {watch_seconds}s "
          f"(states seen: {' -> '.join(states) or 'none'}). "
          "See the Step 3 triage list in docs/h2d-programmatic-access.md.")
    return 3


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("file", help="path to a sliced .gcode.3mf "
                        "(must contain Metadata/plate_1.gcode)")
    parser.add_argument("--ip", default=os.environ.get("H2D_IP"))
    parser.add_argument("--access-code", default=os.environ.get("H2D_ACCESS_CODE"))
    parser.add_argument("--serial", default=os.environ.get("H2D_SERIAL"))
    parser.add_argument("--upload-only", action="store_true",
                        help="run 3a (FTPS upload) only; don't start a print")
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
    if not args.file.endswith(".gcode.3mf"):
        print("WARN: file doesn't end in .gcode.3mf - project 3MFs without "
              "Metadata/plate_1.gcode inside will not start.")

    remote_name = os.path.basename(args.file)
    upload(args.ip, args.access_code, args.file, remote_name)
    if args.upload_only:
        print("Upload-only mode: not starting a print.")
        return 0

    if not args.yes:
        answer = input(f"About to start a REAL print of {remote_name} on "
                       f"{args.serial}. Is the bed clear? [y/N] ")
        if answer.strip().lower() not in ("y", "yes"):
            print("Aborted before publishing. File remains in /cache.")
            return 1

    return start_and_watch(args.ip, args.access_code, args.serial,
                           remote_name, args.watch)


if __name__ == "__main__":
    sys.exit(main())
