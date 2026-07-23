#!/usr/bin/env python3
"""Headlessly slice, then print, on the Bambu Lab A1 mini ("Thumbelina").

The slice-and-send alternative to scripts/a1_mini_send_print.py: instead
of requiring an already-sliced .gcode.3mf, this script takes an STL or a
Bambu Studio *project* .3mf, slices it headlessly with the BambuStudio
CLI (the flow verified in PR #23 and documented in
docs/a1-mini-programmatic-access.md "Headless slicing"), then runs the
exact same verified upload + print.project_file + gcode_state-watch
pipeline as a1_mini_send_print.py.

  1. Edit the FILL THESE IN block below (IP, access code, serial, the
     STL/3MF to slice, the slicer binary, and - for STL input - the
     three flattened A1-mini profile JSONs).
  2. pip install paho-mqtt
  3. python a1_mini_slice_and_send.py            # slice + upload + print
     python a1_mini_slice_and_send.py --slice-only   # stop after slicing

RISKS of the headless method (details in the doc's "Risks of headless
slicing" subsection - read it before unattended use):
  - Nobody eyeballs the slice preview. Wrong scale/units, bad
    orientation, missing supports, or a mis-flattened profile all
    produce a "successful" slice that wastes filament or crashes the
    toolhead into the bed. This script prints a G-code header summary
    (printer, time, filament, temps) and asks for confirmation so a
    human sees *something* before plastic moves - do not --yes your way
    past it until the pipeline has earned trust.
  - The CLI does not resolve profile `inherits` chains; half-flattened
    profiles slice cleanly with wrong temperatures/speeds.
  - --load-settings/--load-filaments silently OVERRIDE settings
    embedded in a project 3MF (CLI flags > --load-* > 3MF contents).
  - The A1-mini CLI invocation is documented but was not empirically
    run in PR #23 (the P2S and H2D ones were) - treat first failures
    as profile flattening/patching problems.

Everything in the FILL THESE IN block can also be given on the command
line or via A1_MINI_IP / A1_MINI_ACCESS_CODE / A1_MINI_SERIAL /
A1_MINI_SLICER env vars - CLI beats env vars beats the constants below.

CAUTION: this starts a REAL print of G-code no human has previewed.
Clear the bed first. The script asks for confirmation before
publishing; pass --yes to skip (see risks above before you do).
"""

# ======================= FILL THESE IN =======================
# Find these on the printer's touchscreen (see Step 1 of
# docs/a1-mini-programmatic-access.md):
PRINTER_IP = "PUT_PRINTER_IP_HERE"          # e.g. "192.168.1.42"  (Settings -> WLAN)
ACCESS_CODE = "PUT_ACCESS_CODE_HERE"        # 8-digit code         (Settings -> WLAN)
SERIAL = "PUT_SERIAL_HERE"                  # 15 characters        (Settings -> Device)

# The file to SLICE (not a sliced .gcode.3mf - use a1_mini_send_print.py
# for those). Either a raw .stl or a Bambu Studio project .3mf saved
# with A1-mini settings. Windows users: keep the r"" prefix.
FILE_TO_SLICE = r"PUT_PATH_TO_YOUR_FILE_HERE.stl"  # e.g. r"C:\Users\me\part.stl"

# The BambuStudio binary/AppImage that provides the CLI (see the doc's
# "Headless slicing" section for the download). Examples:
#   Linux:   r"/home/me/bambu.AppImage"
#   Windows: r"C:\Program Files\Bambu Studio\bambu-studio.exe"
#   macOS:   r"/Applications/BambuStudio.app/Contents/MacOS/BambuStudio"
SLICER_CMD = r"PUT_PATH_TO_BAMBU_STUDIO_HERE"

# Flattened A1-mini profile JSONs (REQUIRED for .stl input; optional
# for a project .3mf that already embeds A1-mini settings - but if set,
# they override what's in the 3MF). Build them per the doc: flatten the
# `inherits` chain of the bundled `Bambu Lab A1 mini 0.4 nozzle` /
# `0.20mm Standard @BBL A1M` / `Bambu PLA Basic @BBL A1M` presets and
# patch from/inherits/printer_settings_id on the machine config.
MACHINE_JSON = r""                          # e.g. r"a1mini_machine_flat.json"
PROCESS_JSON = r""                          # e.g. r"a1mini_process_flat.json"
FILAMENT_JSON = r""                         # e.g. r"a1mini_filament_flat.json"

# AMS lite: leave as-is to print from the external spool holder (see
# a1_mini_send_print.py and ac-dev-lab issues #147/#149).
USE_AMS = False
AMS_MAPPING = ""
# =============================================================

import argparse
import ftplib
import json
import os
import platform
import re
import shutil
import socket
import ssl
import subprocess
import sys
import tempfile
import threading
import time
import zipfile

import paho.mqtt.client as mqtt

# A1-mini hardware maxima - a sliced job asking for more than this was
# sliced with a wrong (bigger-printer) profile, not a hot A1 mini.
A1_MINI_MAX_BED_C = 80
A1_MINI_MAX_NOZZLE_C = 300


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


# --- headless slicing --------------------------------------------------------
def classify_input(path):
    """Return 'stl', 'project_3mf', or exit for inputs we refuse."""
    ext = os.path.splitext(path)[1].lower()
    if ext == ".stl":
        return "stl"
    if ext == ".3mf":
        try:
            names = zipfile.ZipFile(path).namelist()
        except zipfile.BadZipFile:
            sys.exit(f"ERROR: {path} is not a valid .3mf/zip archive.")
        if "Metadata/plate_1.gcode" in names:
            sys.exit(f"ERROR: {path} is already sliced (it contains "
                     "Metadata/plate_1.gcode). Nothing to slice - send it "
                     "with a1_mini_send_print.py instead.")
        return "project_3mf"
    sys.exit(f"ERROR: {path} is neither .stl nor .3mf - the slicer CLI "
             "takes model files, not G-code.")


def slice_headless(slicer, input_path, kind, machine, process, filament,
                   arrange, timeout_s, keep_dir):
    """Run the BambuStudio CLI on input_path; return path to the
    exported .gcode.3mf (inside a temp dir the caller may keep)."""
    for label, p in [("slicer", slicer)] + (
            [("machine profile", machine), ("process profile", process),
             ("filament profile", filament)] if kind == "stl" else []):
        if not p:
            sys.exit(f"ERROR: {label} is required for {kind} input - fill "
                     "it in the FILL THESE IN block or pass the flag.")
        if not os.path.isfile(p):
            sys.exit(f"ERROR: {label} not found: {p}")

    out_dir = tempfile.mkdtemp(prefix="a1m_slice_")
    export_name = (os.path.splitext(os.path.basename(input_path))[0]
                   .replace(" ", "_") + ".gcode.3mf")
    if export_name.endswith(".3mf.gcode.3mf"):
        export_name = export_name[:-len(".3mf.gcode.3mf")] + ".gcode.3mf"

    cmd = [slicer]
    if arrange:
        cmd += ["--orient", "1", "--arrange", "1"]
    if machine and process:
        cmd += ["--load-settings", f"{machine};{process}"]
    if filament:
        # Single-extruder A1 mini: exactly one filament profile, and no
        # --filament-map-mode/--filament-map (those are the H2D's IDEX
        # flags - a wrong-printer smell here).
        cmd += ["--load-filaments", filament]
    cmd += ["--slice", "0", "--export-3mf", export_name,
            "--outputdir", out_dir, input_path]

    # The CLI links wxWidgets, so on a headless Linux box it needs a
    # virtual display. Windows/macOS run it directly.
    if platform.system() == "Linux" and not os.environ.get("DISPLAY"):
        if shutil.which("xvfb-run"):
            cmd = ["xvfb-run", "-a", "-s", "-screen 0 1280x1024x24"] + cmd
        else:
            print("WARN: no DISPLAY and no xvfb-run - the slicer will "
                  "likely abort. apt install xvfb.")

    print("Slicing:", " ".join(cmd))
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True,
                              timeout=timeout_s)
    except subprocess.TimeoutExpired:
        if not keep_dir:
            shutil.rmtree(out_dir, ignore_errors=True)
        sys.exit(f"ERROR: slicer exceeded {timeout_s}s - oversized model, "
                 "or the CLI is stuck waiting on a display.")

    result_path = os.path.join(out_dir, "result.json")
    result = None
    if os.path.isfile(result_path):
        with open(result_path) as f:
            result = json.load(f)
        print(f"Slicer result.json: return_code="
              f"{result.get('return_code')!r} "
              f"error_string={result.get('error_string')!r}")

    export_path = os.path.join(out_dir, export_name)
    failed = (proc.returncode != 0
              or (result is not None and result.get("return_code") not in (0, "0"))
              or not os.path.isfile(export_path))
    if failed:
        tail = "\n".join((proc.stdout or "").splitlines()[-15:])
        if not keep_dir:
            shutil.rmtree(out_dir, ignore_errors=True)
        sys.exit("ERROR: slicing failed (exit code "
                 f"{proc.returncode}).\nLast slicer output:\n{tail}\n"
                 "First suspects (doc: 'Headless slicing'): unflattened "
                 "`inherits` chains in the profile JSONs, or missing "
                 "from/inherits/printer_settings_id patches on the "
                 "machine config.")

    size_kb = os.path.getsize(export_path) // 1024
    print(f"Sliced OK: {export_path} ({size_kb} KB)")
    return export_path, out_dir


# --- G-code header summary / hardware sanity ---------------------------------
def _header_lines(path, n=400):
    with zipfile.ZipFile(path).open("Metadata/plate_1.gcode") as f:
        lines = []
        for _ in range(n):
            line = f.readline().decode("utf-8", "replace")
            if not line:
                break
            lines.append(line)
    return lines


def _max_temp(value):
    nums = [int(x) for x in re.findall(r"\d+", value)]
    return max(nums) if nums else None


def summarize_and_check(path, force):
    """Print what is about to be printed; exit if the sliced job exceeds
    A1-mini hardware maxima (a wrong-profile symptom, not a preference)."""
    fields = {}
    for line in _header_lines(path):
        m = re.match(r";\s*([^=:]+?)\s*[=:]\s*(.+)", line)
        if m:
            fields.setdefault(m.group(1).strip(), m.group(2).strip())

    printer = fields.get("printer_settings_id") or fields.get("printer_model", "?")
    est_time = fields.get("total estimated time", "?")
    weight = fields.get("total filament weight [g]",
                        fields.get("filament used [g]", "?"))
    bed = _max_temp(fields.get("first_layer_bed_temperature", ""))
    nozzle = _max_temp(fields.get("nozzle_temperature", ""))

    print("--- Sliced job summary ------------------------------------")
    print(f"  printer profile : {printer}")
    print(f"  estimated time  : {est_time}")
    print(f"  filament [g]    : {weight}")
    print(f"  bed temp (1st)  : {bed if bed is not None else '?'} C "
          f"(A1 mini max {A1_MINI_MAX_BED_C})")
    print(f"  nozzle temp     : {nozzle if nozzle is not None else '?'} C "
          f"(A1 mini max {A1_MINI_MAX_NOZZLE_C})")
    print("------------------------------------------------------------")

    problems = []
    if bed is not None and bed > A1_MINI_MAX_BED_C:
        problems.append(f"bed {bed} C > printer max {A1_MINI_MAX_BED_C} C")
    if nozzle is not None and nozzle > A1_MINI_MAX_NOZZLE_C:
        problems.append(f"nozzle {nozzle} C > printer max "
                        f"{A1_MINI_MAX_NOZZLE_C} C")
    if bed is None or nozzle is None:
        print("WARN: could not read temperature setpoints from the G-code "
              "header - unusual for a BambuStudio slice; inspect the file.")
    if problems:
        msg = ("sliced job exceeds A1-mini hardware limits ("
               + "; ".join(problems) + ") - almost certainly sliced with a "
               "wrong-printer profile.")
        if force:
            print("WARN (--force): " + msg)
        else:
            sys.exit("ERROR: " + msg + " Pass --force to send anyway.")


# --- A1-mini payload sanity check --------------------------------------------
# Same gate as a1_mini_send_print.py; here it runs on OUR OWN slicer
# output, catching a wrong-printer profile bundle before upload.
def check_payload(path, force):
    warnings = []
    try:
        zf = zipfile.ZipFile(path)
    except zipfile.BadZipFile:
        sys.exit(f"ERROR: {path} is not a .3mf/zip archive.")
    if "Metadata/plate_1.gcode" not in zf.namelist():
        sys.exit(f"ERROR: {path} has no Metadata/plate_1.gcode - the "
                 "slicer exported a project 3MF, not a sliced job.")
    header_text = "".join(_header_lines(path, 200))
    wrong_printer = "H2D" in header_text or "filament_map_mode" in header_text
    if wrong_printer:
        msg = (f"{path} looks sliced for an H2D/IDEX printer - the "
               "profile JSONs you loaded are not A1-mini profiles.")
        if force:
            warnings.append("WARN (--force): " + msg)
        else:
            sys.exit("ERROR: " + msg + " Pass --force to send it anyway.")
    elif "A1" not in header_text:
        warnings.append("WARN: could not confirm an A1 mini profile in the "
                        "G-code header - check the profile JSONs.")
    return warnings


# --- FTPS upload --------------------------------------------------------------
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


# --- print.project_file payload -----------------------------------------------
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


# --- publish start command, watch gcode_state ----------------------------------
def start_and_watch(ip, code, serial, remote_name, use_ams, ams_mapping,
                    watch_seconds):
    states = []
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
          "See the Step 3 triage list in docs/a1-mini-programmatic-access.md.")
    return 3


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("file", nargs="?", default=None,
                        help="STL or project .3mf to slice (overrides "
                        "FILE_TO_SLICE at the top of this script)")
    parser.add_argument("--ip", default=os.environ.get("A1_MINI_IP"))
    parser.add_argument("--access-code", default=os.environ.get("A1_MINI_ACCESS_CODE"))
    parser.add_argument("--serial", default=os.environ.get("A1_MINI_SERIAL"))
    parser.add_argument("--slicer", default=os.environ.get("A1_MINI_SLICER"),
                        help="BambuStudio binary/AppImage (overrides "
                        "SLICER_CMD)")
    parser.add_argument("--machine", default=None,
                        help="flattened A1-mini machine JSON (overrides "
                        "MACHINE_JSON)")
    parser.add_argument("--process", default=None,
                        help="flattened A1-mini process JSON (overrides "
                        "PROCESS_JSON)")
    parser.add_argument("--filament", default=None,
                        help="flattened A1-mini filament JSON (overrides "
                        "FILAMENT_JSON)")
    parser.add_argument("--no-arrange", action="store_true",
                        help="skip --orient/--arrange (use for project "
                        "3MFs whose plate layout you want kept)")
    parser.add_argument("--slice-timeout", type=int, default=900,
                        metavar="SECONDS",
                        help="kill the slicer after this long (default 900)")
    parser.add_argument("--keep-output", action="store_true",
                        help="keep the temp dir with the sliced 3mf and "
                        "result.json")
    parser.add_argument("--slice-only", action="store_true",
                        help="slice and summarize, but don't upload or print")
    parser.add_argument("--upload-only", action="store_true",
                        help="slice + FTPS upload only; don't start a print")
    parser.add_argument("--use-ams", action="store_true", default=USE_AMS)
    parser.add_argument("--ams-mapping", default=AMS_MAPPING)
    parser.add_argument("--force", action="store_true",
                        help="proceed even if the sliced job looks wrong "
                        "for an A1 mini")
    parser.add_argument("--yes", action="store_true",
                        help="skip the summary confirmation prompt "
                        "(read the RISKS note in this file first)")
    parser.add_argument("--watch", type=int, default=180, metavar="SECONDS")
    args = parser.parse_args()

    # CLI/env beats the FILL THESE IN constants; placeholders count as unset.
    ip = args.ip or (None if _is_placeholder(PRINTER_IP) else PRINTER_IP)
    code = args.access_code or (None if _is_placeholder(ACCESS_CODE) else ACCESS_CODE)
    serial = args.serial or (None if _is_placeholder(SERIAL) else SERIAL)
    path = args.file or (None if _is_placeholder(FILE_TO_SLICE) else FILE_TO_SLICE)
    slicer = args.slicer or (None if _is_placeholder(SLICER_CMD) else SLICER_CMD)
    machine = args.machine or (None if _is_placeholder(MACHINE_JSON) else MACHINE_JSON)
    process = args.process or (None if _is_placeholder(PROCESS_JSON) else PROCESS_JSON)
    filament = args.filament or (None if _is_placeholder(FILAMENT_JSON) else FILAMENT_JSON)

    needed = [("file to slice", path), ("slicer binary", slicer)]
    if not args.slice_only:
        needed += [("printer IP", ip), ("access code", code),
                   ("serial", serial)]
    missing = [n for n, v in needed if not v]
    if missing:
        parser.error(
            "missing " + ", ".join(missing) + ". Edit the FILL THESE IN "
            "block at the top of this script (replace the PUT_..._HERE "
            "placeholders), or pass the corresponding flags.")
    if not os.path.isfile(path):
        parser.error(f"no such file: {path}")
    if not os.path.isfile(slicer):
        parser.error(f"no such slicer binary: {slicer}")

    kind = classify_input(path)
    if kind == "project_3mf" and (machine or process or filament):
        print("NOTE: --load-settings/--load-filaments OVERRIDE the "
              "settings embedded in the project 3MF (CLI precedence). "
              "Clear the profile fields to slice with the 3MF's own "
              "settings.")

    sliced, out_dir = slice_headless(
        slicer, path, kind, machine, process, filament,
        arrange=not args.no_arrange, timeout_s=args.slice_timeout,
        keep_dir=args.keep_output)
    try:
        summarize_and_check(sliced, args.force)
        for warning in check_payload(sliced, args.force):
            print(warning)

        if args.slice_only:
            if not args.keep_output:
                print("NOTE: --slice-only without --keep-output deletes "
                      "the result; re-run with --keep-output to keep "
                      f"{sliced}")
            else:
                print(f"Slice-only mode: sliced file kept at {sliced}")
            return 0

        remote_name = os.path.basename(sliced)
        upload(ip, code, sliced, remote_name)
        if args.upload_only:
            print("Upload-only mode: not starting a print.")
            return 0

        if not args.yes:
            answer = input(f"About to start a REAL print of {remote_name} "
                           f"on {serial} - G-code NO HUMAN HAS PREVIEWED "
                           "(summary above). Is the bed clear and the "
                           "summary sane? [y/N] ")
            if answer.strip().lower() not in ("y", "yes"):
                print("Aborted before publishing. File remains in /cache.")
                return 1

        return start_and_watch(ip, code, serial, remote_name,
                               args.use_ams, args.ams_mapping, args.watch)
    finally:
        if not args.keep_output:
            shutil.rmtree(out_dir, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
