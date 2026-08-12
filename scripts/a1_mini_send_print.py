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
watches device/<SERIAL>/report until `gcode_state` reaches RUNNING -
then keeps watching (with progress lines) until the print FINISHes
and announces PRINT COMPLETE. Ctrl-C during that wait detaches
WITHOUT stopping the print; --no-wait exits at RUNNING like the old
behaviour.

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


def fmt_remaining(minutes):
    """mc_remaining_time is reported in minutes; render as 3h05m / 42m."""
    try:
        m = int(minutes)
    except (TypeError, ValueError):
        return None
    return f"{m // 60}h{m % 60:02d}m" if m >= 60 else f"{m}m"


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


# Below this commanded first-layer bed temperature nothing adheres to
# the textured PEI sheet and the job "prints" air (the 2026-07-27
# Thumbelina ghost print ran M190 S35 from the headless CLI's Cool
# Plate default). PLA on the stock plate needs 55-65 C.
MIN_SANE_BED_C = 45


def commanded_bed_temp(zf):
    """First executable M190/M140 with S > 0 - the bed temperature the
    printer will actually run, regardless of what the header tables
    say. (Comment lines start with ';' so startswith() skips them.)
    Kept in sync with a1_mini_slice_and_send.py."""
    with zf.open("Metadata/plate_1.gcode") as f:
        for i, raw in enumerate(f):
            if i > 200000:
                break
            line = raw.decode("utf-8", "replace")
            if line.startswith(("M190", "M140")):
                m = re.search(r"S(\d+)", line)
                if m and int(m.group(1)) > 0:
                    return int(m.group(1))
    return None


# --- A1-mini payload sanity check -------------------------------------------
# Kept in sync with a1_mini_slice_and_send.py.
def has_filament_load(zf):
    """True if the executable G-code carries an M620 S<n>A material-load
    (S255 is the end-G-code pullback, not a load). Every real Bambu
    start sequence has one, AMS or external spool alike; a file without
    one can only ghost-print. Kept in sync with
    a1_mini_slice_and_send.py / h2d_step4_bambulabs_api.py."""
    with zf.open("Metadata/plate_1.gcode") as f:
        for i, raw in enumerate(f):
            if i > 200000:
                break
            m = re.match(r"M620\s+S(\d+)A", raw.decode("utf-8", "replace"))
            if m and int(m.group(1)) < 250:
                return True
    return False


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
        problem = (f'{path} is sliced for "{model}", not an A1 mini. '
                   "Re-slice with an A1 mini profile")
    elif any(v >= 2 for v in map_values):
        problem = (f"{path} maps filaments to a second extruder "
                   f"(filament_map = {meta.get('filament_map')}) - a "
                   "dual-extruder (H2D/IDEX) slice. Re-slice with an "
                   "A1 mini profile")
    if problem is None:
        # Ghost-print guard: a job sliced for the wrong build plate runs
        # the motions with nothing sticking to the bed (Thumbelina
        # 2026-07-27: the headless CLI's Cool Plate default -> M190 S35
        # on the textured PEI sheet).
        plate = meta.get("curr_bed_type", "?")
        bed_cmd = commanded_bed_temp(zf)
        print(f"Build plate: {plate}; commanded first-layer bed temp: "
              f"{bed_cmd if bed_cmd is not None else '?'} C")
        if bed_cmd is not None and bed_cmd < MIN_SANE_BED_C:
            problem = (
                f"{path} commands a first-layer bed temp of only "
                f"{bed_cmd} C (plate type {plate!r}) - nothing adheres "
                "to the textured PEI sheet below ~45 C and the job "
                "GHOST-PRINTS (runs the motions with nothing staying on "
                "the bed). Re-export from Bambu Studio with the "
                "Textured PEI Plate selected, or re-slice with "
                'a1_mini_slice_and_send.py (defaults to --bed-type '
                '"Textured PEI Plate")')
        if problem is None and not has_filament_load(zf):
            # Second ghost-print class (Thumbelina 2026-08-12): a slice
            # made with profiles missing the template-sidecar machine
            # G-code has no M620/T<n> material-load at all - the printer
            # heats up, runs every motion, and never extrudes.
            problem = (
                f"{path} contains no M620 S<n>A material-load command - "
                "its machine start G-code is the generic fallback, so "
                "the printer would run the whole job WITHOUT loading or "
                "extruding filament. Re-slice with profiles from the "
                "updated scripts/flatten_bambu_profiles.py (2026-08-12: "
                "merges the template G-code sidecars), or re-export from "
                "desktop Bambu Studio")
    if problem:
        if force:
            warnings.append("WARN (--force): " + problem + ".")
        else:
            sys.exit("ERROR: " + problem + ". Pass --force to send it anyway.")
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


# --- AMS auto-detection from the sliced file ---------------------------------
# Kept in sync with h2d_step4_bambulabs_api.py.
def filament_slots_used(zf, plate=1):
    """Which project filament slots (1-indexed, as Bambu Studio numbers
    them in the filament dropdown) this plate actually prints with.

    Metadata/slice_info.config lists one `<filament id="N" .../>` per
    slot the plate consumes. On Thumbelina's Testpart2.gcode.3mf that
    is `id="2"` - the job feeds from project slot 2, i.e. AMS lite tray
    index 1, which is exactly the AMS_MAPPING = [1] that worked in the
    field. Falls back to the executable G-code's own `M620 S<n>A`
    tool-load commands (0-indexed). Returns a sorted list, or None."""
    try:
        xml = zf.read("Metadata/slice_info.config").decode("utf-8", "replace")
    except KeyError:
        xml = ""
    blocks = re.findall(r"<plate>(.*?)</plate>", xml, re.S)
    chosen = None
    for block in blocks:
        m = re.search(r'<metadata\s+key="index"\s+value="(\d+)"', block)
        if m and int(m.group(1)) == plate:
            chosen = block
            break
    if chosen is None and blocks:
        chosen = blocks[0]
    if chosen:
        ids = [int(i) for i in re.findall(r'<filament\s+id="(\d+)"', chosen)]
        if ids:
            return sorted(set(ids))

    tools = set()
    try:
        with zf.open("Metadata/plate_1.gcode") as f:
            for i, raw in enumerate(f):
                if i > 200000:
                    break
                m = re.match(r"M620\s+S(\d+)A", raw.decode("utf-8", "replace"))
                if m and int(m.group(1)) < 250:
                    tools.add(int(m.group(1)) + 1)
    except KeyError:
        return None
    return sorted(tools) or None


def apply_payload_ams(path, use_ams, ams_mapping, explicit_no_ams, force):
    """Reconcile the AMS knobs with what the sliced file actually needs.

    The file knows: a job that consumes project filament slot N > 1 can
    only come from an AMS - the external spool holder is always slot 1 -
    so slot > 1 implies use_ams with tray N-1. Before this existed,
    an AMS-fed job printed with use_ams false ran the motions without
    ever loading the tray (Thumbelina, 2026-08-04).

    Slot 1 alone is ambiguous (external spool and AMS tray 1 look
    identical in the slice), so it leaves the configured setting alone.
    Returns the (possibly corrected) (use_ams, ams_mapping)."""
    try:
        slots = filament_slots_used(zipfile.ZipFile(path))
    except (OSError, zipfile.BadZipFile, KeyError):
        return use_ams, ams_mapping
    if not slots:
        return use_ams, ams_mapping
    expected = [s - 1 for s in slots]
    print(f"Payload filament slots in use: {slots} (-> AMS tray indices "
          f"{expected}, 0-indexed)")
    if max(expected) == 0:
        return use_ams, ams_mapping  # slot 1 only: can't tell, leave as set

    if not use_ams:
        msg = (f"this job prints from filament slot(s) {slots} (AMS tray "
               f"{expected}), which only an AMS can feed - with use_ams "
               "false the printer never loads that tray and the job runs dry")
        if explicit_no_ams and not force:
            sys.exit("ERROR: --no-ams was passed but " + msg + ". Drop "
                     "--no-ams, or re-slice the part onto filament slot 1 "
                     "for the external spool.")
        if force:
            print("WARN (--force): " + msg + ".")
            return use_ams, ams_mapping
        print("NOTE: enabling the AMS automatically - " + msg + ".")
        use_ams = True
    if ams_mapping == "":
        print(f"AMS mapping auto-filled from the payload: {expected}.")
        return use_ams, expected
    if len(ams_mapping) != len(expected):
        print(f"WARN: AMS mapping {ams_mapping} has {len(ams_mapping)} "
              f"entry/entries but the job uses {len(expected)} filament "
              f"slot(s) (the payload implies {expected}).")
    elif ams_mapping != expected:
        print(f"NOTE: AMS mapping {ams_mapping} overrides the tray the slice "
              f"implies ({expected}) - fine if you deliberately moved the "
              "spool to another tray.")
    return use_ams, ams_mapping


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
                    ams_mapping, watch_seconds, wait_done=True):
    states = []          # ordered gcode_state transitions seen
    running = threading.Event()
    finished = threading.Event()
    failed = threading.Event()
    armed = threading.Event()    # set once OUR start command is published
    # gcode_state the printer was ALREADY reporting when we published.
    # The status is sticky: the last job's FAILED/FINISH keeps being
    # reported (and re-delivered to every fresh subscriber in the pushall
    # snapshot) until a new job overwrites it, so a terminal state is only
    # a verdict on OUR job once the state has moved off this baseline.
    baseline = {"state": None, "moved": False}
    baseline_errors = set()      # nonzero print_error codes seen pre-publish
    new_errors = []              # codes that first appeared after publish
    progress = {}                # latest mc_percent / remaining / layer info

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
                # Gate FINISH on running: an idle printer whose LAST job
                # completed still reports gcode_state FINISH, and the
                # pushall snapshot re-delivers that before our job starts.
                if state == "FINISH" and running.is_set():
                    finished.set()
                if baseline["state"] is None:
                    # The pre-publish pushall answer carried no
                    # gcode_state, so the first report we see after
                    # publishing IS the pre-publish state - adopt it as
                    # the baseline rather than reading it as a transition.
                    baseline["state"] = state
                elif state != baseline["state"]:
                    baseline["moved"] = True
                if state in ("FAILED", "OFFLINE"):
                    if baseline["moved"]:
                        failed.set()
                    else:
                        # Still the value the printer was reporting before
                        # we published, so it is the PREVIOUS job's
                        # outcome. A real rejection of THIS job still
                        # surfaces immediately as a new print_error below,
                        # and a start command that was ignored outright
                        # falls out as the timeout.
                        print(f"NOTE: gcode_state {state} is LATCHED from "
                              "an earlier job, not a verdict on this one - "
                              "waiting for the state to actually move. "
                              "Dismiss any error dialog on the touchscreen.")
        # Progress fields arrive incrementally and in separate messages;
        # remember the latest of each, print a line when the percent moves.
        for key, field in (("rem", "mc_remaining_time"),
                           ("layer", "layer_num"),
                           ("total", "total_layer_num")):
            if p.get(field) is not None:
                progress[key] = p[field]
        pct = p.get("mc_percent")
        if (wait_done and running.is_set() and not finished.is_set()
                and pct is not None and pct != progress.get("pct")):
            progress["pct"] = pct
            line = f"progress: {pct}%"
            rem = fmt_remaining(progress.get("rem"))
            if rem:
                line += f", ~{rem} left"
            if progress.get("layer") is not None and progress.get("total"):
                line += f", layer {progress['layer']}/{progress['total']}"
            print(line)
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

    def on_connect(c, u, flags, rc, properties=None):
        # Subscribing here (not once after connect()) means paho's
        # automatic reconnect re-subscribes too - a print watched to
        # completion can outlive the odd Wi-Fi hiccup.
        c.subscribe(f"device/{serial}/report")

    c = make_mqtt_client()
    c.username_pw_set("bblp", code)
    c.tls_set(cert_reqs=ssl.CERT_NONE)
    c.tls_insecure_set(True)
    c.on_connect = on_connect
    c.on_message = on_msg
    c.connect(ip, 8883, 30)
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
    baseline["state"] = states[-1] if states else None
    armed.set()
    c.publish(request_topic, json.dumps(payload))

    deadline = time.monotonic() + watch_seconds
    while time.monotonic() < deadline and not running.is_set() and not failed.is_set():
        time.sleep(1)

    detached = False
    if wait_done and running.is_set() and not failed.is_set():
        print("Print started. Watching until it finishes - Ctrl-C detaches "
              "WITHOUT stopping the print (--no-wait skips this next time).")
        try:
            while not finished.is_set() and not failed.is_set():
                time.sleep(5)
        except KeyboardInterrupt:
            print("\nDetached; the print carries on at the printer. This "
                  "script only observes and cannot re-attach - check the "
                  "touchscreen or Bambu Handy for completion.")
            detached = True

    c.loop_stop()
    c.disconnect()

    if detached:
        return 0
    if finished.is_set():
        print("\a" + "=" * 62)
        print("PRINT COMPLETE: the printer reported gcode_state FINISH.")
        print("Remove the part from the bed before starting the next job.")
        print("=" * 62)
        return 0
    if failed.is_set():
        for err in new_errors:
            hint = print_error_hint(err)
            if hint:
                print(f"  {fmt_print_error(err)}: {hint}")
        if running.is_set():
            print("FAILED: the print started but the printer reported an "
                  "error or abort before finishing - check the touchscreen.")
        else:
            print("FAILED: printer rejected or aborted the job - see the "
                  "Step 3 triage list in docs/a1-mini-programmatic-access.md.")
        return 2
    if running.is_set():
        print("SUCCESS: printer reached RUNNING. Not waiting for completion "
              "(--no-wait); watch the printer or Bambu Handy instead.")
        return 0
    if not baseline["moved"] and baseline["state"]:
        print(f"TIMEOUT: the printer never moved off the "
              f"{baseline['state']} it was ALREADY reporting before the "
              f"start command ({watch_seconds}s). That means the command "
              "was ignored, not that this job failed: check the "
              "touchscreen for an undismissed error dialog from the "
              "previous job, then re-run.")
        return 3
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
    parser.add_argument("--no-wait", dest="wait_done", action="store_false",
                        default=True,
                        help="exit as soon as the printer reaches RUNNING "
                        "instead of watching until the print finishes")
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
    for warning in check_payload(path, args.force):
        print(warning)

    # The sliced file, not this script's constants, is the authority on
    # whether an AMS tray has to be loaded (see apply_payload_ams).
    use_ams, ams_mapping = apply_payload_ams(
        path, use_ams, ams_mapping, args.use_ams is False, args.force)
    if not use_ams:
        ams_mapping = ""  # external spool holder: no mapping in the payload
    elif ams_mapping == "":
        print("WARN: --use-ams without an AMS mapping - the printer will "
              'try its default tray; pass --ams-mapping "0" (etc.) to be '
              "explicit.")

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

    if use_ams:
        print(f"Filament source: AMS lite, tray mapping "
              f"{ams_mapping or '(printer default)'} (0-indexed).")
    else:
        print("Filament source: EXTERNAL spool holder (use_ams false). "
              "If your filament is actually loaded in the AMS lite, pass "
              "--use-ams --ams-mapping <tray> or the printer may run the "
              "job without feeding filament.")
    if not args.yes:
        answer = input(f"About to start a REAL print of {remote_name} on "
                       f"{serial}. Is the bed clear? [y/N] ")
        if answer.strip().lower() not in ("y", "yes"):
            print("Aborted before publishing. File remains on the printer.")
            return 1

    return start_and_watch(ip, code, serial, remote_name, remote_dir,
                           use_ams, ams_mapping, args.watch, args.wait_done)


if __name__ == "__main__":
    sys.exit(main())
