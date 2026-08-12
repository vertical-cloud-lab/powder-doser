#!/usr/bin/env python3
"""Send a print to a LAN-mode Bambu printer through `bambulabs_api`.

This is the RECOMMENDED script for day-to-day use on the A1 mini
("Thumbelina") and the one the Step 5/6 Pi relay should wrap: the
library keeps a persistent MQTT connection and exposes status, so it is
a better base for automation than the raw-socket scripts. It carries
every guard the raw-MQTT scripts grew during Thumbelina bringup:

  - refuses a file that is not a sliced .gcode.3mf, or is sliced for a
    different printer (--expect-printer, default "A1 mini");
  - refuses a ghost-print bed temperature (< 45 C - the headless CLI's
    Cool Plate default, 2026-07-27);
  - reads the AMS filament source OUT OF THE SLICED FILE, so an AMS-fed
    job no longer needs `use_ams` hand-edited (2026-08-04);
  - sanitizes the remote filename (spaces caused printer-side error
    83935248 / hex 0500-C010);
  - verifies the upload actually landed instead of trusting the return
    value (the printer's FTPS TLS shutdown sometimes never completes);
  - ignores print_error codes LATCHED from earlier jobs and fails only
    on a new one, decoded to Bambu's hex form with a hint;
  - likewise ignores a LATCHED gcode_state: the printer keeps reporting
    the previous job's FAILED/FINISH until a new job overwrites it, so
    a verdict only counts once the state has actually moved
    (2026-08-05);
  - refuses to publish while another job is RUNNING/PREPARE;
  - optionally checks the printer's own camera for a clear plate
    (--camera-check, needs bambu_camera_check.py alongside this file);
  - watches the job through to FINISH and announces PRINT COMPLETE.

Usage - either fill in the block below and run with no arguments, or
pass everything on the command line:

    pip install bambulabs_api
    python h2d_step4_bambulabs_api.py part.gcode.3mf \
        --ip <IP> --access-code <CODE> --serial <SERIAL>

Credentials may also come from A1_MINI_IP / A1_MINI_ACCESS_CODE /
A1_MINI_SERIAL (H2D_* and BAMBU_* names work too). CLI beats env vars
beats the constants below.

For the H2D, add --expect-printer "H2D" (or edit EXPECT_PRINTER); the
transport is identical, only the payload check differs.

CAUTION: this starts a REAL print. Clear the bed first. The script asks
for confirmation; pass --yes to skip (proven for repeat runs on
Thumbelina, 2026-08-04).
"""

# ======================= FILL THESE IN =======================
# From the printer's touchscreen - see Step 1 of
# docs/a1-mini-programmatic-access.md:
PRINTER_IP = "PUT_PRINTER_IP_HERE"        # e.g. "192.168.1.42"  (Settings -> WLAN)
ACCESS_CODE = "PUT_ACCESS_CODE_HERE"      # 8-digit code         (Settings -> WLAN)
SERIAL = "PUT_SERIAL_HERE"                # 15 characters        (Settings -> Device)

# The sliced file to print. MUST be a .gcode.3mf sliced for this
# printer. Windows users: keep the r"" prefix.
FILE_TO_PRINT = r"PUT_PATH_TO_YOUR_FILE_HERE.gcode.3mf"

# Which printer the payload must be sliced for. "" disables the check.
EXPECT_PRINTER = "A1 mini"                # "H2D" for the H2D, "" for none

# AMS: leave USE_AMS = None to read the filament source out of the
# sliced file (recommended - see resolve_ams below). True/False forces
# it. AMS_MAPPING is one 0-indexed tray number per filament, e.g. [1]
# for AMS lite slot 2; "" derives it from the file.
USE_AMS = None
AMS_MAPPING = ""
# =============================================================

import argparse
import base64
import ftplib
import inspect
import os
import re
import socket
import ssl
import sys
import time
import zipfile

import bambulabs_api as bl


def _is_placeholder(value):
    return not value or "PUT_" in value or "_HERE" in value


# --- remote filename ---------------------------------------------------------
def sanitize_remote_name(name):
    """Restrict the remote filename to A-Za-z0-9._- .

    The name ends up verbatim in the MQTT `url`; on Thumbelina a
    filename with spaces was rejected printer-side with error 83935248
    (hex 0500-C010, a file-path/parse failure) even though the FTPS
    upload succeeded. Kept in sync with the other send scripts."""
    return re.sub(r"[^A-Za-z0-9._-]+", "_", name)


# --- print_error decoding ----------------------------------------------------
# Kept in sync across the send scripts. Bambu reports print_error as a
# decimal int; the community error tables use the hex form AAAA-BBBB
# (e.g. 83902467 == 0500-4003).
def fmt_print_error(err):
    try:
        n = int(err)
    except (TypeError, ValueError):
        return str(err)
    return f"{err} (hex {(n >> 16) & 0xFFFF:04X}-{n & 0xFFFF:04X})"


KNOWN_PRINT_ERRORS = {
    0x0500C010: "file-path/parse failure - bad characters in the url, or "
                "the url does not point at the uploaded file. This script "
                "sanitizes the filename, so suspect the upload path next.",
    0x05004003: "printer could not parse/find the print file - the classic "
                "wrong-upload-path error (ac-dev-lab / bambulabs_api#99). "
                "bambulabs_api uploads to the FTP root and starts with "
                "ftp:///<name>, which is the A1-mini-proven combination.",
}


def print_error_hint(err):
    try:
        return KNOWN_PRINT_ERRORS.get(int(err))
    except (TypeError, ValueError):
        return None


def fmt_remaining(minutes):
    """get_time() reports minutes remaining; render as 3h05m / 42m."""
    try:
        m = int(minutes)
    except (TypeError, ValueError):
        return None
    return f"{m // 60}h{m % 60:02d}m" if m >= 60 else f"{m}m"


# --- sliced-file inspection ---------------------------------------------------
# Kept in sync with a1_mini_send_print.py / a1_mini_slice_and_send.py.
def read_gcode_metadata(zf):
    """Parse `; key = value` comment lines from the HEADER_BLOCK and
    CONFIG_BLOCK at the top of Metadata/plate_1.gcode."""
    fields = {}
    with zf.open("Metadata/plate_1.gcode") as f:
        for i, raw in enumerate(f):
            if i > 5000:
                break
            line = raw.decode("utf-8", "replace")
            if "CONFIG_BLOCK_END" in line or "EXECUTABLE_BLOCK_START" in line:
                break
            m = re.match(r";\s*([^=:]+?)\s*[=:]\s*(.*)", line)
            if m:
                fields.setdefault(m.group(1).strip(), m.group(2).strip())
    return fields


# Below this commanded first-layer bed temperature nothing adheres to
# the plate and the job "prints" air (the 2026-07-27 Thumbelina ghost
# print ran M190 S35 from the headless CLI's Cool Plate default).
MIN_SANE_BED_C = 45


def commanded_bed_temp(zf):
    """First executable M190/M140 with S > 0 - the bed temperature the
    printer will actually run, regardless of the header tables."""
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


def filament_slots_used(zf, plate=1):
    """Which project filament slots (1-indexed, as Bambu Studio numbers
    them in the filament dropdown) this plate actually prints with.

    Primary source is Metadata/slice_info.config, which lists one
    `<filament id="N" .../>` per slot the plate consumes. On
    Thumbelina's Testpart2.gcode.3mf that is `id="2"` - the job feeds
    from project slot 2, i.e. AMS lite tray index 1, which is exactly
    the AMS_MAPPING = [1] that worked in the field.

    Falls back to the executable G-code's own `M620 S<n>A` / `T<n>`
    tool-change commands (0-indexed) if slice_info.config is missing.
    Returns a sorted list of ints, or None if nothing could be read."""
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

    # Fallback: the resolved start G-code carries `M620 S<n>A` with the
    # 0-indexed tool the job loads (255 = unload/no AMS sentinel).
    tools = set()
    try:
        with zf.open("Metadata/plate_1.gcode") as f:
            for i, raw in enumerate(f):
                if i > 200000:
                    break
                line = raw.decode("utf-8", "replace")
                m = re.match(r"M620\s+S(\d+)A", line)
                if m and int(m.group(1)) < 250:
                    tools.add(int(m.group(1)) + 1)
    except KeyError:
        return None
    return sorted(tools) or None


def has_filament_load(zf):
    """True if the executable G-code carries an M620 S<n>A material-load
    (S255 is the end-G-code pullback, not a load). Every real Bambu
    start sequence has one, AMS or external spool alike; a file without
    one can only ghost-print. Kept in sync with a1_mini_send_print.py /
    a1_mini_slice_and_send.py."""
    with zf.open("Metadata/plate_1.gcode") as f:
        for i, raw in enumerate(f):
            if i > 200000:
                break
            m = re.match(r"M620\s+S(\d+)A", raw.decode("utf-8", "replace"))
            if m and int(m.group(1)) < 250:
                return True
    return False


def inspect_payload(path, plate, expect_printer, force):
    """Print what the file is and hard-stop on the known-bad shapes.
    Returns the filament slots the job uses (see filament_slots_used).

    The printer-identity check reads the CONFIG_BLOCK's own fields. It
    must NOT grep the header for substrings like "filament_map_mode":
    BambuStudio >= 2.x writes the full config key set - including the
    multi-extruder keys - into EVERY printer's G-code, so a genuine
    A1-mini slice contains `filament_map_mode = Auto For Flush` too.
    The old substring check false-positived on every legitimate
    A1-mini file (Thumbelina field testing, PR #23)."""
    try:
        zf = zipfile.ZipFile(path)
    except zipfile.BadZipFile:
        sys.exit(f"ERROR: {path} is not a .3mf/zip archive - did you point "
                 "this at an STL? Slice it first.")
    if "Metadata/plate_1.gcode" not in zf.namelist():
        sys.exit(f"ERROR: {path} has no Metadata/plate_1.gcode - this is a "
                 "project 3MF, not a sliced .gcode.3mf. Slice it (Bambu "
                 "Studio export, or the CLI recipe in the doc) and retry.")

    meta = read_gcode_metadata(zf)
    model = meta.get("printer_model") or meta.get("printer_settings_id") or ""
    bed_type = meta.get("curr_bed_type", "?")
    bed_cmd = commanded_bed_temp(zf)
    print(f"Payload: sliced for {model or '?'!r}; build plate {bed_type!r}; "
          f"commanded first-layer bed temp "
          f"{bed_cmd if bed_cmd is not None else '?'} C")

    # filament_map assigns each filament to an extruder; any value >= 2
    # means a second extruder, which only the IDEX machines have.
    map_values = [int(v) for v in
                  re.findall(r"\d+", meta.get("filament_map", ""))]

    problem = None
    if expect_printer and model and expect_printer.lower() not in model.lower():
        problem = (f'{path} is sliced for "{model}", not a {expect_printer}. '
                   f"Re-slice with a {expect_printer} profile")
    elif (expect_printer and "h2d" not in expect_printer.lower()
            and any(v >= 2 for v in map_values)):
        problem = (f"{path} maps filaments to a second extruder "
                   f"(filament_map = {meta.get('filament_map')}) - a "
                   f"dual-extruder (H2D/IDEX) slice, which single-extruder "
                   f"firmware chokes on. Re-slice with a {expect_printer} "
                   "profile")
    elif bed_cmd is not None and bed_cmd < MIN_SANE_BED_C:
        problem = (f"{path} commands a first-layer bed temp of only {bed_cmd} C "
                   f"(plate type {bed_type!r}) - nothing adheres to the textured "
                   "PEI sheet below ~45 C and the job GHOST-PRINTS (runs the "
                   "motions with nothing staying on the bed). Re-export with the "
                   "correct build plate selected")
    elif not has_filament_load(zf):
        # Second ghost-print class (Thumbelina 2026-08-12): profiles
        # flattened without the template-sidecar machine G-code slice
        # into jobs with no M620/T<n> material-load at all - the printer
        # heats up, runs every motion, and never extrudes.
        problem = (f"{path} contains no M620 S<n>A material-load command - "
                   "its machine start G-code is the generic fallback, so the "
                   "printer would run the whole job WITHOUT loading or "
                   "extruding filament. Re-slice with profiles from the "
                   "updated scripts/flatten_bambu_profiles.py (2026-08-12: "
                   "merges the template G-code sidecars), or re-export from "
                   "desktop Bambu Studio")
    if problem:
        if force:
            print("WARN (--force): " + problem + ".")
        else:
            sys.exit("ERROR: " + problem + ". Pass --force to send it anyway.")
    elif expect_printer and not model:
        print("WARN: no printer_model/printer_settings_id in the G-code "
              f"header - could not confirm this file is a {expect_printer} "
              "slice.")

    slots = filament_slots_used(zf, plate)
    if slots:
        print(f"Payload filament slots in use: {slots} "
              f"(-> AMS tray indices {[s - 1 for s in slots]}, 0-indexed)")
    else:
        print("NOTE: could not read the filament slots from the payload - "
              "the AMS auto-detection below falls back to the flags.")
    return slots


# --- AMS resolution -----------------------------------------------------------
def normalize_ams_mapping(value):
    """Accept [0], "0", "0,1" or "[1]" and return a list of ints (AMS
    tray indices, 0-indexed), or "" for no mapping. Kept in sync with
    a1_mini_send_print.py."""
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


def resolve_ams(slots, cli_use_ams, cli_mapping, force):
    """Decide (use_ams, ams_mapping) from the payload + the flags.

    The old version of this script hard-coded use_ams=False, which made
    every AMS-fed job need a source edit (Thumbelina, 2026-08-04). The
    sliced file already knows: a job that consumes project filament
    slot N > 1 can only come from an AMS - the external spool holder is
    always slot 1 - so slot > 1 implies use_ams with tray N-1.

    Slot 1 alone is genuinely ambiguous (external spool and AMS tray 1
    both look like slot 1 in the slice), so that case keeps the
    external-spool default and says so out loud.

    An explicit --no-ams that contradicts the file is refused rather
    than silently obeyed: that combination is the failure mode where
    the printer runs the job without ever loading the filament."""
    expected = [s - 1 for s in slots] if slots else None
    needs_ams = bool(expected) and max(expected) > 0
    cli_mapping = normalize_ams_mapping(cli_mapping)

    if cli_use_ams is None:
        if needs_ams:
            use_ams = True
            print(f"AMS auto-detected from the payload: the job uses filament "
                  f"slot(s) {slots}, which only an AMS can feed.")
        else:
            use_ams = False
            if expected:
                print("AMS auto-detection: the job uses filament slot 1 only, "
                      "which could be either the external spool holder or AMS "
                      "tray 1 - defaulting to the external spool. If the "
                      "filament is in the AMS, pass --use-ams (optionally "
                      '--ams-mapping "0").')
    else:
        use_ams = cli_use_ams

    if needs_ams and not use_ams:
        msg = (f"{'--no-ams was passed' if cli_use_ams is False else 'AMS is off'} "
               f"but this job prints from filament slot(s) {slots} "
               f"(AMS tray {expected}) - with use_ams false the printer never "
               "loads that tray and the job runs dry")
        if force:
            print("WARN (--force): " + msg + ".")
        else:
            sys.exit("ERROR: " + msg + ". Drop --no-ams, or re-slice the part "
                     "onto filament slot 1 for the external spool.")

    if not use_ams:
        return False, ""

    mapping = cli_mapping if cli_mapping != "" else (expected or "")
    if cli_mapping != "" and expected is not None:
        if len(cli_mapping) != len(expected):
            print(f"WARN: --ams-mapping {cli_mapping} has "
                  f"{len(cli_mapping)} entry/entries but the job uses "
                  f"{len(expected)} filament slot(s) (expected mapping "
                  f"{expected}).")
        elif cli_mapping != expected:
            print(f"NOTE: --ams-mapping {cli_mapping} overrides the tray the "
                  f"slice implies ({expected}) - fine if you deliberately "
                  "moved the spool to another tray.")
    if mapping == "":
        print('WARN: use_ams with no mapping - the printer picks its own '
              'tray; pass --ams-mapping "0" (etc.) to be explicit.')
    return True, mapping


# --- upload verification ------------------------------------------------------
# bambulabs_api's FTP helper swallows exceptions and returns None on
# failure, and the printer's FTPS server sometimes never completes the
# TLS shutdown after a successful STOR - so a non-226 return does NOT
# prove the file is missing (field-tested on Thumbelina, PR #23). Check
# the directory listing before deciding either way.
class ImplicitFTP_TLS(ftplib.FTP_TLS):
    """Implicit FTPS (TLS on connect) with control-session reuse on the
    data channel - copied from h2d_smoketest.py so the fallback works
    on any bambulabs_api release. Keep the copies in sync."""

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
                conn, server_hostname=self.host, session=self.sock.session)
        return conn, size


def list_ftp_root(printer, ip, code):
    """Best-effort listing of the printer's FTP root. Tries the
    library's own client first, then a stdlib implicit-FTPS session.
    Returns a list of names, or None if both routes failed."""
    try:
        listing = printer.ftp_client.list_directory("/")
        if listing:
            return [str(x) for x in listing]
    except Exception:
        pass
    try:
        ctx = ssl._create_unverified_context()
        ctx.minimum_version = ssl.TLSVersion.TLSv1_2
        ctx.maximum_version = ssl.TLSVersion.TLSv1_2
        ftps = ImplicitFTP_TLS(context=ctx)
        ftps.connect(ip, 990, 30)
        ftps.login("bblp", code)
        ftps.prot_p()
        try:
            return ftps.nlst("/")
        finally:
            try:
                ftps.quit()
            except Exception:
                ftps.close()
    except Exception as exc:
        print(f"WARN: could not list the printer's FTP root to verify the "
              f"upload ({type(exc).__name__}: {exc}).")
        return None


def upload_and_verify(printer, path, remote_name, ip, code):
    """Upload via the library, then confirm the file is really there.

    Returns True if the file is on the printer. A missing 226 is not
    fatal on its own: the printer's interrupted TLS shutdown produces
    exactly that while every byte lands."""
    try:
        with open(path, "rb") as f:
            result = printer.upload_file(f, remote_name)
    except Exception as exc:                      # library re-raises as Exception
        result = None
        print(f"FTPS upload raised {type(exc).__name__}: {exc}")
    print(f"Upload result: {result}")

    listing = list_ftp_root(printer, ip, code)
    if listing is not None:
        present = any(remote_name in str(entry) for entry in listing)
        print(f"FTP root now: {listing}")
        if present:
            if "226" not in str(result):
                print("Upload verified: the file is present despite the "
                      "interrupted/odd FTPS response.")
            return True
        print(f"ERROR: {remote_name} is NOT in the printer's FTP root after "
              "the upload - re-run, or use --upload-only to retry the "
              "transfer on its own.")
        return False

    # No listing available: fall back to trusting the transfer response.
    if "226" in str(result):
        print("NOTE: could not list the FTP root; the 226 Transfer complete "
              "response is the only evidence the file landed.")
        return True
    print("ERROR: FTPS upload did not return '226 Transfer complete' and the "
          "file could not be verified - not starting a print.")
    return False


# --- start_print kwarg probing ------------------------------------------------
def call_start_print(printer, remote_name, plate, use_ams, ams_mapping):
    """`bambulabs_api` releases differ in what start_print accepts, so
    pass only the kwargs this installed version declares (and fall back
    to the positional-only form if introspection fails)."""
    kwargs = {}
    try:
        params = inspect.signature(printer.start_print).parameters
        if "use_ams" in params:
            kwargs["use_ams"] = use_ams
        if ams_mapping != "" and "ams_mapping" in params:
            kwargs["ams_mapping"] = ams_mapping
    except (TypeError, ValueError):
        params = {}

    if use_ams and "use_ams" not in kwargs:
        print("WARN: this bambulabs_api release's start_print() takes no "
              "use_ams argument - the AMS setting is whatever the library "
              "defaults to. Upgrade the library, or use "
              "a1_mini_send_print.py, which builds the payload directly.")
    if ams_mapping != "" and "ams_mapping" not in kwargs:
        print(f"WARN: start_print() takes no ams_mapping argument - tray "
              f"{ams_mapping} cannot be requested through this release.")

    print(f"start_print(name={remote_name!r}, plate={plate}"
          + "".join(f", {k}={v!r}" for k, v in kwargs.items()) + ")")
    try:
        return printer.start_print(remote_name, plate, **kwargs)
    except TypeError as exc:
        # Only a signature mismatch is retryable; a TypeError raised
        # from inside the library is a real bug and must surface.
        if not kwargs or "unexpected keyword" not in str(exc):
            raise
        print(f"NOTE: installed bambulabs_api rejected {sorted(kwargs)} "
              f"({exc}); retrying without them.")
        return printer.start_print(remote_name, plate)


# --- state / error watch ------------------------------------------------------
def read_print_error(printer):
    """Current print_error code, or None if this release doesn't expose
    one. The printer LATCHES the last error until it is cleared, so the
    caller must compare against a pre-publish baseline."""
    getter = getattr(printer, "print_error_code", None)
    if getter is None:
        return None
    try:
        err = getter()
    except Exception:
        return None
    return err if err not in (None, 0, "0") else None


def request_status_refresh(printer):
    """Ask the printer for a full status snapshot right now.

    bambulabs_api reads a dict that MQTT reports merge into, and the
    incremental reports frequently omit gcode_state - so straight after
    publishing we may still be reading the previous job's value for
    several seconds. The library re-requests a snapshot on its own only
    every `pushall_timeout` (60 s by default). Asking once, immediately,
    shrinks that stale window; best-effort, since nothing here should
    fail because a private helper moved between releases."""
    for owner in (getattr(printer, "mqtt_client", None), printer):
        pushall = getattr(owner, "pushall", None)
        if callable(pushall):
            try:
                pushall()
                # Let the library's own throttle re-fire on the next read
                # rather than sitting on the value we just superseded.
                if hasattr(owner, "_last_update"):
                    owner._last_update = 0
                return True
            except Exception:
                return False
    return False


def load_camera_module():
    """Import bambu_camera_check.py from this script's own directory.

    Kept optional on purpose: these scripts get copied to lab laptops one
    file at a time, so a missing sibling must produce an instruction, not
    a traceback.
    """
    here = os.path.dirname(os.path.abspath(__file__))
    if here not in sys.path:
        sys.path.insert(0, here)
    try:
        import bambu_camera_check
    except ImportError:
        return None
    return bambu_camera_check


def grab_frame(printer, cam, ip, code, transport, timeout):
    """One JPEG frame, preferring the connection bambulabs_api already has.

    `Printer.connect()` starts the library's own camera thread on TCP
    6000, so opening a second socket to the same port risks the printer
    dropping one of them. Read the library's latest frame instead, and
    only fall back to our own capture when it never produced one (an
    H2D, where the camera is RTSPS on 322 and the library's thread never
    gets anything).
    """
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            # get_camera_frame() raises a bare Exception until the first
            # frame lands - the camera runs at roughly 1 fps.
            return base64.b64decode(printer.get_camera_frame())
        except Exception:
            time.sleep(1)
    if transport in ("auto", "rtsp"):
        try:
            return cam.capture(ip, code, transport="rtsp", timeout=timeout)
        except Exception as exc:
            print(f"NOTE: RTSPS fallback failed: {exc}")
    return None


def camera_bed_check(printer, ip, code, args):
    """Return True (clear), False (occupied) or None (no verdict)."""
    cam = load_camera_module()
    if cam is None:
        print("ERROR: --camera-check needs bambu_camera_check.py next to "
              "this script (same folder). Copy it from scripts/ in the "
              "repo.")
        return None
    judge = getattr(args, "camera_judge", "diff")
    if judge in ("diff", "both") and not os.path.exists(args.bed_reference):
        print(f"NOTE: no empty-bed reference at {args.bed_reference}. "
              "Create one with the plate clean:\n    python "
              "bambu_camera_check.py reference --ip <IP> --access-code "
              "<CODE>\n(or pass --camera-judge llm, which needs no "
              "reference)")
        return None
    frame = grab_frame(printer, cam, ip, code, args.camera_transport,
                       args.camera_timeout)
    if frame is None:
        print("NOTE: no camera frame. On the H2D, LAN Mode Liveview "
              "(Settings -> General) is a separate toggle from Developer "
              "Mode; with it off the camera port stays closed. (The A1 "
              "mini has no such toggle - check network/access code.)")
        return None
    save_to = args.camera_save or "bed_before_print.jpg"
    try:
        with open(save_to, "wb") as fh:
            fh.write(frame)
        print(f"Camera frame saved to {save_to}")
    except OSError as exc:
        print(f"NOTE: could not save the camera frame: {exc}")

    verdicts = []
    if judge in ("diff", "both"):
        try:
            roi = cam.parse_roi(args.camera_roi)
        except ValueError as exc:
            print(f"NOTE: camera check skipped: {exc}")
            return None
        compare = getattr(cam, "compare_against_references", None)
        if compare is not None:
            verdict, _fraction, detail = compare(
                frame, args.bed_reference, roi=roi,
                pixel_delta=args.camera_pixel_delta,
                area_fraction=args.camera_area_fraction)
        else:
            # Older copy of bambu_camera_check.py without alignment /
            # folder support - single rigid comparison.
            try:
                with open(args.bed_reference, "rb") as fh:
                    reference = fh.read()
            except OSError as exc:
                print(f"NOTE: camera check skipped: {exc}")
                return None
            verdict, _fraction, detail = cam.compare_frames(
                frame, reference, roi=roi,
                pixel_delta=args.camera_pixel_delta,
                area_fraction=args.camera_area_fraction)
        verdicts.append((verdict, detail))
    if judge in ("llm", "both"):
        llm_check = getattr(cam, "llm_bed_check", None)
        if llm_check is None:
            print("NOTE: this copy of bambu_camera_check.py has no LLM "
                  "judge - pull a fresh one from the repo.")
            verdicts.append((None, "LLM judge unavailable"))
        else:
            verdicts.append(llm_check(frame, model=args.camera_llm_model))

    detail = " | ".join(d for _, d in verdicts)
    if any(v is False for v, _ in verdicts):
        print(f"Camera: bed does NOT look clear - {detail}")
        return False
    if verdicts and all(v is True for v, _ in verdicts):
        print(f"Camera: bed looks CLEAR - {detail}")
        return True
    print(f"NOTE: camera check inconclusive: {detail}")
    return None


def _progress_line(printer):
    bits = []
    for attr, fmt in (("get_percentage", "{}%"),):
        getter = getattr(printer, attr, None)
        if getter is None:
            continue
        try:
            value = getter()
        except Exception:
            continue
        if value not in (None, "", "Unknown"):
            bits.append(fmt.format(value))
    try:
        rem = fmt_remaining(printer.get_time())
        if rem:
            bits.append(f"~{rem} left")
    except Exception:
        pass
    try:
        layer, total = printer.current_layer_num(), printer.total_layer_num()
        if layer is not None and total:
            bits.append(f"layer {layer}/{total}")
    except Exception:
        pass
    return ", ".join(bits)


def watch(printer, watch_seconds, wait_done, baseline_errors,
          baseline_state=None):
    """Follow gcode_state to RUNNING, then (unless --no-wait) stay
    attached until the printer reports FINISH.

    Every verdict here has to survive the same trap: the printer's
    status is STICKY. `gcode_state` and `print_error` keep reporting the
    last job's values until a new job overwrites them, and the library
    reads a cached dict that is only refreshed when a report containing
    that field arrives. So for a short window after our start command we
    are still reading the PREVIOUS job's outcome.

    Three guards, one per direction:
      - FINISH only counts once RUNNING has been seen (an idle Bambu
        re-reports the last job's FINISH to every fresh subscriber);
      - a print_error latched before we published is history, not a
        verdict (baseline_errors);
      - FAILED/OFFLINE only counts once the state has MOVED off what the
        printer was already reporting before we published
        (baseline_state). Without this, one failed job poisons every
        later run in that session: the latch stays FAILED, so the next
        run reads FAILED on its first poll - about a second after
        publishing - and quits while the print it just started carries
        on. Field-reported on Thumbelina 2026-08-05.
    """
    last = None
    running = False
    moved = baseline_state is None
    deadline = time.monotonic() + watch_seconds
    last_progress = 0.0
    seen_errors = set(baseline_errors)
    while True:
        state = str(printer.get_state())
        if state != last:
            print(f"gcode_state: {state}")
            last = state
        if not moved and state != baseline_state:
            if baseline_state == "UNKNOWN" and state != "UNKNOWN":
                # No status had arrived when we sampled the baseline
                # (ac-dev-lab saw this right after connect()), so the
                # first real value IS the pre-publish state - adopt it
                # rather than reading it as a transition.
                baseline_state = state
            else:
                moved = True

        err = read_print_error(printer)
        if err is not None and err not in seen_errors:
            seen_errors.add(err)
            print(f"print_error: {fmt_print_error(err)}")
            hint = print_error_hint(err)
            if hint:
                print(f"  {hint}")
            print("FAILED: the printer reported a NEW error after our start "
                  "command - see the Step 3 triage list in "
                  "docs/a1-mini-programmatic-access.md.")
            return 2

        if state == "RUNNING" and not running:
            running = True
            print("SUCCESS: printer reached RUNNING.")
            if not wait_done:
                return 0
            print("Watching until it finishes - Ctrl-C detaches WITHOUT "
                  "stopping the print (--no-wait skips this next time) ...")
        if state in ("FAILED", "OFFLINE") and moved:
            print("FAILED: see the Step 3 triage list in "
                  "docs/a1-mini-programmatic-access.md.")
            return 2
        if running and state in ("FINISH", "FINISHED"):
            print("\a" + "=" * 62)
            print(f"PRINT COMPLETE: the printer reported gcode_state {state}.")
            print("Remove the part from the bed before starting the next job.")
            print("=" * 62)
            return 0
        if running and state == "IDLE":
            # Not FINISH: the job stopped without completing (cancelled
            # at the panel, or aborted). Don't claim success.
            print("STOPPED: the printer went back to IDLE without reporting "
                  "FINISH - the job was cancelled or aborted.")
            return 2
        if not running and time.monotonic() > deadline:
            if not moved:
                print(f"TIMEOUT: the printer never moved off the "
                      f"{baseline_state} it was ALREADY reporting before "
                      f"the start command ({watch_seconds}s). That means "
                      "the command was ignored, not that this job failed: "
                      "check the touchscreen for an undismissed error "
                      "dialog from the previous job, then re-run.")
            else:
                print(f"TIMEOUT: no RUNNING within {watch_seconds}s "
                      f"(last state: {last}). A wrong-printer or "
                      "unparseable file shows up exactly like this - see "
                      "the Step 3 triage list in "
                      "docs/a1-mini-programmatic-access.md.")
            return 3
        if running and time.monotonic() - last_progress > 60:
            last_progress = time.monotonic()
            line = _progress_line(printer)
            if line:
                print(f"progress: {line}")
        time.sleep(3)


def build_parser():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("file", nargs="?", default=None,
                        help="path to a sliced .gcode.3mf (overrides "
                             "FILE_TO_PRINT at the top of this script)")
    parser.add_argument("--ip", default=os.environ.get(
        "A1_MINI_IP", os.environ.get("H2D_IP", os.environ.get("BAMBU_IP"))))
    parser.add_argument("--access-code", default=os.environ.get(
        "A1_MINI_ACCESS_CODE", os.environ.get(
            "H2D_ACCESS_CODE", os.environ.get("BAMBU_ACCESS_CODE"))))
    parser.add_argument("--serial", default=os.environ.get(
        "A1_MINI_SERIAL", os.environ.get(
            "H2D_SERIAL", os.environ.get("BAMBU_SERIAL"))))
    parser.add_argument("--plate", type=int, default=1,
                        help="plate number inside the 3MF (default 1)")
    parser.add_argument("--expect-printer", default=None, metavar="MODEL",
                        help='printer the payload must be sliced for '
                             '(default "%s"; "any" disables the check)'
                             % EXPECT_PRINTER)
    parser.add_argument("--use-ams", dest="use_ams", action="store_true",
                        default=None,
                        help="force AMS feed (default: read from the file)")
    parser.add_argument("--no-ams", dest="use_ams", action="store_false",
                        help="force the external spool holder (refused if the "
                             "file needs an AMS tray, unless --force)")
    parser.add_argument("--ams-mapping", default=None,
                        help='AMS tray indices, 0-indexed, e.g. "0" or "0,1" '
                             "(default: derived from the file)")
    parser.add_argument("--camera-check", action="store_true",
                        help="before starting, grab a camera frame and "
                             "compare it against --bed-reference to see "
                             "whether the plate is clear. Needs "
                             "bambu_camera_check.py alongside this script "
                             "and LAN Mode Liveview on at the printer.")
    parser.add_argument("--bed-reference", default="bed_reference.jpg",
                        metavar="JPEG",
                        help="empty-bed baseline: one image, or a folder of "
                             "images taken at different bed positions (make "
                             "them with `bambu_camera_check.py reference`)")
    parser.add_argument("--camera-judge", default="diff",
                        choices=("diff", "llm", "both"),
                        help="diff = pixel comparison against "
                             "--bed-reference; llm = send the frame to "
                             "Claude (pip install anthropic + "
                             "ANTHROPIC_API_KEY, no reference needed); "
                             "both = strictest (default diff)")
    parser.add_argument("--camera-llm-model", default="claude-opus-5",
                        help="model for --camera-judge llm "
                             "(default claude-opus-5)")
    parser.add_argument("--camera-transport", default="auto",
                        choices=("auto", "chamber", "rtsp"))
    parser.add_argument("--camera-roi", default=None, metavar="x0,y0,x1,y1",
                        help="limit the comparison to this fraction of the "
                             "frame, e.g. 0.2,0.3,0.8,0.9")
    parser.add_argument("--camera-save", default=None, metavar="JPEG",
                        help="where to keep the frame that was checked "
                             "(default bed_before_print.jpg)")
    parser.add_argument("--camera-timeout", type=float, default=20.0)
    parser.add_argument("--camera-pixel-delta", type=float, default=28.0)
    parser.add_argument("--camera-area-fraction", type=float, default=0.02)
    parser.add_argument("--upload-only", action="store_true",
                        help="upload and verify only; don't start a print")
    parser.add_argument("--yes", action="store_true",
                        help="skip the clear-the-bed confirmation prompt")
    parser.add_argument("--force", action="store_true",
                        help="send even if the payload checks object")
    parser.add_argument("--no-wait", dest="wait_done", action="store_false",
                        default=True,
                        help="exit once RUNNING instead of waiting for FINISH")
    parser.add_argument("--watch", type=int, default=180, metavar="SECONDS",
                        help="how long to wait for RUNNING (default 180)")
    return parser


def main():
    parser = build_parser()
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

    expect = EXPECT_PRINTER if args.expect_printer is None else args.expect_printer
    if expect.strip().lower() in ("any", "none"):
        expect = ""

    print(f"bambulabs_api version: {getattr(bl, '__version__', 'unknown')}")
    slots = inspect_payload(path, args.plate, expect, args.force)
    use_ams, ams_mapping = resolve_ams(
        slots,
        USE_AMS if args.use_ams is None else args.use_ams,
        args.ams_mapping if args.ams_mapping is not None else AMS_MAPPING,
        args.force)
    print("Filament source: "
          + (f"AMS, tray mapping {ams_mapping or '(printer default)'} "
             "(0-indexed)" if use_ams else "EXTERNAL spool holder"))

    remote_name = sanitize_remote_name(os.path.basename(path))
    if remote_name != os.path.basename(path):
        print(f"NOTE: uploading as {remote_name} - spaces and other "
              "punctuation break the printer's file-path parsing "
              "(error 83935248 / 0500-C010).")

    printer = bl.Printer(ip, code, serial)
    printer.connect()
    time.sleep(2)  # give the MQTT client a moment to receive first status
    try:
        baseline_state = str(printer.get_state())
        print(f"Printer state before print: {baseline_state}")
        if baseline_state in ("RUNNING", "PREPARE") and not args.force:
            print("ABORT: the printer is already printing - not sending "
                  "another job. Pass --force to override.")
            return 4
        if baseline_state in ("FAILED", "OFFLINE"):
            print(f"NOTE: gcode_state {baseline_state} is LATCHED from an "
                  "EARLIER job - the printer reports the last outcome "
                  "until a new job overwrites it. Ignoring it for this "
                  "run, and only a FAILED that appears AFTER the state "
                  "moves will count. Dismiss any error dialog on the "
                  "touchscreen so the next job is not refused.")

        # Snapshot any error the printer has LATCHED from an earlier job:
        # the status carries the last error until it is cleared, and it
        # would otherwise read as a verdict on the job we haven't started
        # yet (field-seen on Thumbelina: a 0500-C010 from May was still
        # being reported in July).
        baseline_errors = set()
        latched = read_print_error(printer)
        if latched is not None:
            baseline_errors.add(latched)
            print(f"NOTE: pre-existing print_error {fmt_print_error(latched)} "
                  "latched from an EARLIER job - ignoring it for this run. "
                  "Dismiss any error dialog on the touchscreen.")
            hint = print_error_hint(latched)
            if hint:
                print(f"  (that code means: {hint})")

        if not upload_and_verify(printer, path, remote_name, ip, code):
            return 2
        if args.upload_only:
            print("Upload-only mode: not starting a print.")
            return 0

        bed_clear = None
        if args.camera_check:
            bed_clear = camera_bed_check(printer, ip, code, args)
            if bed_clear is False and not args.force:
                print("ABORT: the camera says something is still on the "
                      "plate. Clear it, or pass --force if you believe "
                      "the check is wrong (a stale reference image and a "
                      "moved camera both read as 'not clear').")
                return 5
            if bed_clear is None and args.yes and not args.force:
                # --yes means nobody is watching, so "no verdict" has to
                # fail closed - otherwise a camera fault silently turns
                # an automated queue back into an unchecked one.
                print("ABORT: --camera-check with --yes, but the camera "
                      "gave no verdict (see the note above). Fix the "
                      "camera, drop --yes so a human can confirm, or pass "
                      "--force.")
                return 5

        if not args.yes:
            gate = ("The camera says the bed looks clear. "
                    if bed_clear else "")
            answer = input(f"{gate}About to start a REAL print of "
                           f"{remote_name} on {serial}. Is the bed clear? "
                           "[y/N] ")
            if answer.strip().lower() not in ("y", "yes"):
                print("Aborted before start_print. File remains on the printer.")
                return 1

        call_start_print(printer, remote_name, args.plate, use_ams, ams_mapping)
        print("start_print sent; watching gcode_state ...")
        request_status_refresh(printer)
        try:
            return watch(printer, args.watch, args.wait_done, baseline_errors,
                         baseline_state)
        except KeyboardInterrupt:
            print("\nDetached; the print carries on at the printer. This "
                  "script only observes and cannot stop it.")
            return 0
    finally:
        printer.disconnect()


if __name__ == "__main__":
    sys.exit(main())
