#!/usr/bin/env python3
"""Send a print to the Bambu Lab A1 mini ("Thumbelina").

The A1-mini-specific version of scripts/h2d_step3_send_print.py:

  1. Edit the FILL THESE IN block below (IP, access code, serial, and
     the path to the sliced .gcode.3mf you want to print).
  2. pip install paho-mqtt
  3. python a1_mini_send_print.py

It uploads the file to the printer's FTP root over implicit FTPS
(TLS 1.2 session reuse - the same stack verified against the H2D in
PR #23; the FTPS quirks are fleet-wide Bambu behaviour, not
model-specific), publishes the `print.project_file` MQTT command, and
watches device/<SERIAL>/report until `gcode_state` reaches RUNNING.

Upload goes to the FTP ROOT and the url is `ftp:///<name>` - that is
what bambulabs_api and the ac-dev-lab A1-mini scripts (the only stack
proven to actually start prints on a real A1 mini) use. The first
Thumbelina attempts used `/cache/` + `ftp:///cache/<name>` and the
printer answered with error 0500-4003 ("unable to parse file" - the
ac-dev-lab wrong-storage-path classic). --remote-dir cache restores
the old behaviour if you need it.

A1-mini extras over the H2D script:
  - Reads the printer identity (`printer_model`) from the G-code
    CONFIG_BLOCK and refuses files sliced for another printer (the
    IDEX header in an H2D .gcode.3mf is exactly what single-extruder
    firmware chokes on). Override with --force if you know better.
    Note it does NOT grep for substrings like "filament_map_mode" -
    BambuStudio >= 2.x writes those keys into every printer's G-code,
    A1 mini included (field-tested on Thumbelina, PR #23).
  - USE_AMS / AMS_MAPPING knobs for an AMS lite (defaults print from
    the external spool holder). Tray numbers are 0-indexed: [0] is
    the first AMS lite slot. --no-ams forces the external spool.
  - Survives the printer's FTPS quirk where the TLS shutdown after a
    successful upload times out: it reconnects and verifies the file
    actually landed instead of failing (or blindly trusting). Also
    field-tested on Thumbelina.
  - Ignores print_error codes latched from EARLIER jobs (the printer
    re-reports the last error to every fresh subscriber) and fails
    only on a new error appearing after our start command - with the
    code decoded to Bambu's hex form and a hint for the known ones.

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
# mapping - one entry per filament used by the job, tray numbers
# 0-indexed, e.g. [0] for a single-filament job feeding from the first
# slot (see ac-dev-lab issues #147/#149 for working examples).
USE_AMS = False
AMS_MAPPING = ""
# =============================================================

import argparse
import ftplib
import json
import os
import re
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


def make_mqtt_client():
    # paho-mqtt 2.x deprecates the bare Client() constructor (both lab
    # laptops printed "Callback API version 1 is deprecated" during
    # Thumbelina field testing). on_message has the same signature under
    # VERSION2, so use it when available; paho-mqtt 1.x has no
    # CallbackAPIVersion and takes the old constructor.
    try:
        return mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    except AttributeError:
        return mqtt.Client()


def sanitize_remote_name(name):
    """Restrict the remote filename to A-Za-z0-9._- .

    The name is embedded verbatim in the MQTT `url`
    (`ftp:///<name>`); on Thumbelina a filename with spaces was
    rejected printer-side with error 83935248 (hex 0500-C010, a
    file-path/parse failure) even though the FTPS upload succeeded."""
    return re.sub(r"[^A-Za-z0-9._-]+", "_", name)


def remote_path(remote_dir, remote_name):
    return f"/{remote_dir}/{remote_name}" if remote_dir else f"/{remote_name}"


def remote_url(remote_dir, remote_name):
    # Three slashes are intentional: ftp:// + absolute path.
    return "ftp://" + remote_path(remote_dir, remote_name)


# --- print_error decoding ----------------------------------------------------
# Kept in sync across the three send scripts. Bambu reports print_error
# as a decimal int; the community error tables use the hex form
# AAAA-BBBB (e.g. 83902467 == 0500-4003).
def fmt_print_error(err):
    try:
        n = int(err)
    except (TypeError, ValueError):
        return str(err)
    return f"{err} (hex {(n >> 16) & 0xFFFF:04X}-{n & 0xFFFF:04X})"


KNOWN_PRINT_ERRORS = {
    0x0500C010: "file-path/parse failure - bad characters in the url, or "
                "the url does not point at the uploaded file",
    0x05004003: "printer could not parse/find the print file - the classic "
                "wrong-upload-path error (ac-dev-lab / bambulabs_api#99). "
                "Make sure the upload dir and the url agree; the "
                "A1-mini-proven combination is FTP root + ftp:///<name> "
                "(this script's default).",
}


def print_error_hint(err):
    try:
        return KNOWN_PRINT_ERRORS.get(int(err))
    except (TypeError, ValueError):
        return None


# --- G-code metadata parsing --------------------------------------------------
# Kept in sync with a1_mini_slice_and_send.py.
def read_gcode_metadata(zf):
    """Parse `; key = value` / `; key: value` comment lines from the
    HEADER_BLOCK and CONFIG_BLOCK at the top of Metadata/plate_1.gcode.
    First occurrence wins; stops at the end of the config block."""
    fields = {}
    with zf.open("Metadata/plate_1.gcode") as f:
        for i, raw in enumerate(f):
            if i > 5000:
                break
            line = raw.decode("utf-8", "replace")
            if ("CONFIG_BLOCK_END" in line
                    or "EXECUTABLE_BLOCK_START" in line):
                break
            m = re.match(r";\s*([^=:]+?)\s*[=:]\s*(.*)", line)
            if m:
                fields.setdefault(m.group(1).strip(), m.group(2).strip())
    return fields


# --- A1-mini payload sanity check -------------------------------------------
# Kept in sync with a1_mini_slice_and_send.py.
def check_payload(path, force):
    """Best-effort check that `path` is a sliced job for an A1 mini.

    Returns a list of warnings; raises SystemExit on hard failures
    (not a sliced 3mf, or sliced for a different printer without
    --force).

    The check reads the CONFIG_BLOCK's own identity fields. It must
    NOT grep the header for substrings like "filament_map_mode":
    BambuStudio >= 2.x writes the full config key set - including the
    multi-extruder keys - into EVERY printer's G-code, so a genuine
    A1-mini slice contains `filament_map_mode = Auto For Flush` too.
    The old substring check false-positived on every legitimate
    A1-mini file (found in Thumbelina field testing, PR #23, and
    reproduced against a real v02.06.00.51 CLI slice).
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

    meta = read_gcode_metadata(zf)
    model = meta.get("printer_model") or meta.get("printer_settings_id") or ""
    # filament_map assigns each filament to an extruder; any value >= 2
    # means the job uses a second extruder, which the A1 mini lacks.
    map_values = [int(v) for v in
                  re.findall(r"\d+", meta.get("filament_map", ""))]

    problem = None
    if model and "A1 mini" not in model:
        problem = f'{path} is sliced for "{model}", not an A1 mini'
    elif any(v >= 2 for v in map_values):
        problem = (f"{path} maps filaments to a second extruder "
                   f"(filament_map = {meta.get('filament_map')}) - a "
                   "dual-extruder (H2D/IDEX) slice")
    if problem:
        msg = problem + ". Re-slice with an A1 mini profile."
        if force:
            warnings.append("WARN (--force): " + msg)
        else:
            sys.exit("ERROR: " + msg + " Pass --force to send it anyway.")
    elif not model:
        warnings.append("WARN: no printer_model/printer_settings_id in the "
                        "G-code header - could not confirm this file was "
                        "sliced for the A1 mini.")
    return warnings


# --- AMS mapping normalization ------------------------------------------------
# Kept in sync with a1_mini_slice_and_send.py.
def normalize_ams_mapping(value):
    """Accept [0], "0", "0,1", or "[1]" (bracketed strings included -
    that's the form LLM-suggested commands tend to produce) and return
    what the payload expects: a list of ints (one entry per filament in
    the job, AMS lite tray numbers 0-indexed), or "" for no mapping."""
    if value in ("", None) or value == []:
        return ""
    if isinstance(value, str):
        parts = [p for p in re.split(r"[\s,;\[\]]+", value.strip()) if p]
        try:
            return [int(p) for p in parts]
        except ValueError:
            sys.exit('ERROR: --ams-mapping must be comma-separated tray '
                     f'numbers (e.g. "0" or "0,1"), got: {value!r}')
    return [int(v) for v in value]


# --- FTPS upload -------------------------------------------------------------
# Kept in sync with a1_mini_slice_and_send.py and h2d_step3_send_print.py.
def _ftps_connect(ip, code):
    ftps = ImplicitFTP_TLS(context=make_ftps_context())
    ftps.connect(ip, 990, 30)
    ftps.login("bblp", code)
    ftps.prot_p()
    return ftps


def upload(ip, code, local_path, remote_name, remote_dir=""):
    dest = remote_path(remote_dir, remote_name)
    list_dir = "/" + remote_dir if remote_dir else "/"
    ftps = _ftps_connect(ip, code)
    interrupted = None
    with open(local_path, "rb") as f:
        try:
            resp = ftps.storbinary(f"STOR {dest}", f)
            print(f"FTPS upload: {resp}")
        except (OSError, ftplib.Error) as e:
            # Field-tested on the real A1 mini (Thumbelina, PR #23):
            # after a successful STOR the printer sometimes never
            # completes the TLS shutdown on the data channel, so the
            # client times out (or sees an SSL error) waiting for the
            # 226 even though every byte landed. The control channel is
            # then out of sync - the late 226 surfaces as a bogus reply
            # to the next command - so don't trust this session:
            # reconnect and check whether the file actually arrived.
            interrupted = e
            print(f"FTPS: transfer ended with {type(e).__name__}: {e}")
            print("FTPS: reconnecting to verify whether the upload landed...")
    if interrupted is not None:
        try:
            ftps.close()
        except Exception:
            pass
        ftps = _ftps_connect(ip, code)

    listing = []
    try:
        listing = ftps.nlst(list_dir)
        print(f"FTPS {list_dir} now: {listing}")
    except (OSError, ftplib.Error) as e:
        print(f"WARN: could not list {list_dir} to verify the upload ({e}).")

    uploaded = remote_name in " ".join(listing)
    if interrupted is not None:
        if uploaded:
            print(f"FTPS upload verified: file is present in {list_dir} "
                  "despite the interrupted TLS shutdown.")
        elif listing:
            sys.exit("ERROR: the FTPS transfer was interrupted and "
                     f"{remote_name} is NOT in {list_dir} - re-run the upload.")
        else:
            sys.exit("ERROR: the FTPS transfer was interrupted and the "
                     "upload could not be verified (listing failed too) - "
                     "re-run with --upload-only and check the printer.")
    elif listing and not uploaded:
        print("WARN: uploaded file not visible in the listing - "
              "check the url path before blaming the printer.")

    try:
        ftps.quit()
    except Exception:
        try:
            ftps.close()
        except Exception:
            pass


# --- print.project_file payload ---------------------------------------------
def project_file_payload(remote_name, remote_dir, use_ams, ams_mapping):
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
            "url": remote_url(remote_dir, remote_name),
            # bambulabs_api's A1-mini-proven payload also names the file
            # directly; harmless where unused.
            "file": remote_name,
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
# Kept in sync across the three send scripts.
def start_and_watch(ip, code, serial, remote_name, remote_dir, use_ams,
                    ams_mapping, watch_seconds):
    states = []          # ordered gcode_state transitions seen
    running = threading.Event()
    failed = threading.Event()
    armed = threading.Event()    # set once OUR start command is published
    baseline_errors = set()      # nonzero print_error codes seen pre-publish
    new_errors = []              # codes that first appeared after publish

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
            if armed.is_set():
                if state == "RUNNING":
                    running.set()
                if state in ("FAILED", "OFFLINE"):
                    failed.set()
        err = p.get("print_error")
        if err in (None, 0, "0"):
            return
        if not armed.is_set():
            # The printer LATCHES the last print_error in its status until
            # it is cleared or overwritten, and the pushall snapshot
            # re-delivers it to every fresh subscriber. It is history from
            # an earlier job, not a verdict on the one we have not started
            # yet. (Field-seen on Thumbelina: a 0500-C010 from a May
            # attempt was still being reported in July, and the old
            # version of this script aborted on it before publishing.)
            if err not in baseline_errors:
                baseline_errors.add(err)
                print(f"NOTE: pre-existing print_error "
                      f"{fmt_print_error(err)} latched from an EARLIER "
                      "job - ignoring it for this run. Dismiss any error "
                      "dialog on the touchscreen.")
        elif err not in baseline_errors and err not in new_errors:
            # A repeat of the latched code would be invisible here; the
            # FAILED state / timeout paths still catch that job.
            new_errors.append(err)
            print(f"print_error: {fmt_print_error(err)}")
            failed.set()

    c = make_mqtt_client()
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

    if states and states[-1] in ("RUNNING", "PREPARE", "PAUSE"):
        c.loop_stop()
        c.disconnect()
        print(f"ABORT: printer is already busy (gcode_state "
              f"{states[-1]}) - not publishing a second job.")
        return 4

    payload = project_file_payload(remote_name, remote_dir, use_ams,
                                   ams_mapping)
    print("Publishing print.project_file for "
          f"{remote_url(remote_dir, remote_name)} ...")
    armed.set()
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
        for err in new_errors:
            hint = print_error_hint(err)
            if hint:
                print(f"  {fmt_print_error(err)}: {hint}")
        print("FAILED: printer rejected or aborted the job - see the Step 3 "
              "triage list in docs/a1-mini-programmatic-access.md.")
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
    parser.add_argument("--use-ams", dest="use_ams", action="store_true",
                        default=None,
                        help="feed from the AMS lite instead of the "
                        "external spool holder")
    parser.add_argument("--no-ams", dest="use_ams", action="store_false",
                        help="print from the external spool holder even if "
                        "USE_AMS = True in this file")
    parser.add_argument("--ams-mapping", default=None,
                        help='AMS tray mapping, one 0-indexed tray number '
                        'per filament in the job, e.g. "0" (only with '
                        '--use-ams)')
    parser.add_argument("--remote-dir", default="", metavar="DIR",
                        help="printer-side directory to upload to and "
                        "reference in the url (default: FTP root, the "
                        "A1-mini-proven path; 'cache' restores the old "
                        "/cache behaviour)")
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

    use_ams = USE_AMS if args.use_ams is None else args.use_ams
    ams_mapping = normalize_ams_mapping(
        args.ams_mapping if args.ams_mapping is not None else AMS_MAPPING)
    if not use_ams:
        ams_mapping = ""  # external spool holder: no mapping in the payload
    elif ams_mapping == "":
        print("WARN: --use-ams without an AMS mapping - the printer will "
              'try its default tray; pass --ams-mapping "0" (etc.) to be '
              "explicit.")

    for warning in check_payload(path, args.force):
        print(warning)

    remote_dir = args.remote_dir.strip("/")
    remote_name = sanitize_remote_name(os.path.basename(path))
    if remote_name != os.path.basename(path):
        print(f"NOTE: uploading as {remote_name!r} - spaces/special "
              "characters in the filename break the printer's file-path "
              "parsing (error 83935248 / 0500-C010).")
    upload(ip, code, path, remote_name, remote_dir)
    if args.upload_only:
        print("Upload-only mode: not starting a print.")
        return 0

    if not args.yes:
        answer = input(f"About to start a REAL print of {remote_name} on "
                       f"{serial}. Is the bed clear? [y/N] ")
        if answer.strip().lower() not in ("y", "yes"):
            print("Aborted before publishing. File remains on the printer.")
            return 1

    return start_and_watch(ip, code, serial, remote_name, remote_dir,
                           use_ams, ams_mapping, args.watch)


if __name__ == "__main__":
    sys.exit(main())
