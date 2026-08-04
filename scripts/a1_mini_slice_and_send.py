#!/usr/bin/env python3
"""Headlessly slice, then print, on the Bambu Lab A1 mini ("Thumbelina").

The slice-and-send alternative to scripts/a1_mini_send_print.py: instead
of requiring an already-sliced .gcode.3mf, this script takes an STL or a
Bambu Studio *project* .3mf, slices it headlessly with the BambuStudio
CLI (the flow verified in PR #23 and documented in
docs/a1-mini-programmatic-access.md "Headless slicing"), then runs the
exact same verified upload + print.project_file + gcode_state-watch
pipeline as a1_mini_send_print.py (including the watch-until-FINISH
"PRINT COMPLETE" notice; --no-wait exits at RUNNING instead).

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
  - The exact A1-mini CLI invocation was empirically verified in
    PR #23 (2026-07-23, v02.06.00.51 AppImage + flattened A1M
    profiles -> return_code 0) - but only for a PLA test cube; treat
    failures on other profiles as flattening/patching problems.

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
# they override what's in the 3MF). Generate them with
#   python scripts/flatten_bambu_profiles.py --studio-dir "C:\Program Files\Bambu Studio"
# (walks the `inherits` chain of the bundled `Bambu Lab A1 mini 0.4
# nozzle` / `0.20mm Standard @BBL A1M` / `Bambu PLA Basic @BBL A1M`
# presets and applies the required patches). Do NOT point these at the
# per-user presets under AppData\Roaming\BambuStudio\user\... - those
# are diff-only files the CLI refuses ("unknown config type",
# return_code -5; field-seen on Thumbelina).
MACHINE_JSON = r""                          # e.g. r"a1mini_machine_flat.json"
PROCESS_JSON = r""                          # e.g. r"a1mini_process_flat.json"
FILAMENT_JSON = r""                         # e.g. r"a1mini_filament_flat.json"

# AMS lite: leave as-is to print from the external spool holder. To
# feed from an AMS lite set USE_AMS = True and AMS_MAPPING to the tray
# mapping - one entry per filament used by the job, tray numbers
# 0-indexed, e.g. [0] for a single-filament job feeding from the first
# slot (see a1_mini_send_print.py and ac-dev-lab issues #147/#149).
USE_AMS = False
AMS_MAPPING = ""

# Build plate the job is sliced FOR. The headless CLI has no plate
# picker and silently defaults to "Cool Plate" (35 C bed) - on the
# textured PEI sheet the A1 mini actually ships with, PLA will not
# stick at 35 C, and the result is a "ghost print": the toolhead runs
# the whole job while nothing stays on the bed (field-seen on
# Thumbelina 2026-07-27; the fix below is empirically verified to
# produce M190 S65). Match this to the plate physically installed.
BED_TYPE = "Textured PEI Plate"
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

# Below this commanded first-layer bed temperature nothing adheres to
# the textured PEI sheet and the job "prints" air (the 2026-07-27
# Thumbelina ghost print ran M190 S35 from the CLI's Cool Plate
# default). PLA on the stock plate needs 55-65 C.
MIN_SANE_BED_C = 45

# curr_bed_type values BambuStudio understands, with friendly aliases.
# "Textured PEI Plate" -> M190 S65 was verified against the real
# v02.06.00.51 CLI (PR #23, 2026-07-27).
BED_TYPE_ALIASES = {
    "textured": "Textured PEI Plate",
    "texturedpei": "Textured PEI Plate",
    "texturedpeiplate": "Textured PEI Plate",
    "cool": "Cool Plate",
    "coolplate": "Cool Plate",
    "eng": "Engineering Plate",
    "engineering": "Engineering Plate",
    "engineeringplate": "Engineering Plate",
    "hot": "High Temp Plate",
    "hightemp": "High Temp Plate",
    "hightempplate": "High Temp Plate",
}


def normalize_bed_type(value):
    if not value:
        return ""
    key = re.sub(r"[^a-z0-9]", "", value.lower())
    return BED_TYPE_ALIASES.get(key, value)


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


# --- STL sanity: unit / size check -------------------------------------------
def stl_bbox_mm(path):
    """Return (dx, dy, dz) of the STL's bounding box in file units, or
    None if the file can't be parsed as STL. Handles binary and ASCII."""
    import struct
    try:
        size = os.path.getsize(path)
        with open(path, "rb") as f:
            head = f.read(84)
            if len(head) < 84:
                return None
            (n_tri,) = struct.unpack("<I", head[80:84])
            if 84 + n_tri * 50 == size and n_tri > 0:
                mins = [float("inf")] * 3
                maxs = [float("-inf")] * 3
                for _ in range(n_tri):
                    rec = f.read(50)
                    if len(rec) < 50:
                        break
                    vals = struct.unpack("<12fH", rec)
                    for v in range(3):
                        for c in range(3):
                            x = vals[3 + v * 3 + c]
                            if x < mins[c]:
                                mins[c] = x
                            if x > maxs[c]:
                                maxs[c] = x
                return tuple(maxs[c] - mins[c] for c in range(3))
        # ASCII STL
        mins = [float("inf")] * 3
        maxs = [float("-inf")] * 3
        seen = False
        with open(path, "r", errors="replace") as f:
            for line in f:
                parts = line.split()
                if len(parts) == 4 and parts[0] == "vertex":
                    try:
                        xyz = [float(p) for p in parts[1:]]
                    except ValueError:
                        continue
                    seen = True
                    for c in range(3):
                        if xyz[c] < mins[c]:
                            mins[c] = xyz[c]
                        if xyz[c] > maxs[c]:
                            maxs[c] = xyz[c]
        return tuple(maxs[c] - mins[c] for c in range(3)) if seen else None
    except OSError:
        return None


def check_stl_units(path, scale, force):
    """Catch the meters-unit export before the slicer does.

    Field-seen on Thumbelina (2026-07): an STL exported in meters (a
    38 mm part whose coordinates span 0.038 units - the Fusion 360 /
    OnShape default) slices fine in DESKTOP Bambu Studio because it
    pops an "object too small, scale it up?" dialog, but the headless
    CLI has no dialog and dies with "No layers were detected". The
    empirically verified fix is --scale 1000."""
    dims = stl_bbox_mm(path)
    if dims is None:
        print("WARN: could not parse the STL to check its size - "
              "proceeding.")
        return
    eff = [d * scale for d in dims]
    dims_s = " x ".join(f"{d:.3g}" for d in dims)
    if max(eff) < 1.0:
        msg = (f"{path} spans only {dims_s} units - effectively zero "
               "size once read as millimetres. This is the classic "
               "meters-unit export (Fusion 360 / OnShape default): the "
               "desktop slicer offers to scale it, the headless CLI "
               'fails with "No layers were detected". Re-export the STL '
               "in millimetres, or re-run with --scale 1000 (verified "
               "fix, PR #23). Inch-unit exports need --scale 25.4.")
        if force:
            print("WARN (--force): " + msg)
        else:
            sys.exit("ERROR: " + msg + " Pass --force to try anyway.")
    elif max(eff) < 10.0:
        print(f"NOTE: model is small ({dims_s} units x scale {scale:g}) "
              "- if this was exported in inches, add --scale 25.4.")


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
                   arrange, timeout_s, keep_dir, scale=1.0, bed_type=""):
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
    export_name = sanitize_remote_name(
        os.path.splitext(os.path.basename(input_path))[0]) + ".gcode.3mf"
    if export_name.endswith(".3mf.gcode.3mf"):
        export_name = export_name[:-len(".3mf.gcode.3mf")] + ".gcode.3mf"

    # The CLI has no plate-selection flag and defaults curr_bed_type to
    # "Cool Plate" (35 C bed on the A1 mini -> nothing sticks -> ghost
    # print, field-seen on Thumbelina 2026-07-27). Injecting
    # curr_bed_type into the process config is the empirically verified
    # way to select the plate headlessly (M190 S65 with "Textured PEI
    # Plate", PR #23). Patch a copy - never the user's file.
    if bed_type and process:
        with open(process, encoding="utf-8") as f:
            proc_cfg = json.load(f)
        if proc_cfg.get("curr_bed_type") != bed_type:
            proc_cfg["curr_bed_type"] = bed_type
            patched = os.path.join(out_dir, "process_bed_patched.json")
            with open(patched, "w", encoding="utf-8") as f:
                json.dump(proc_cfg, f, indent=2)
            print(f"Bed type: slicing for {bed_type!r} "
                  "(injected curr_bed_type into a copy of the process "
                  "profile; --bed-type changes it).")
            process = patched
    elif bed_type and not process:
        print(f"NOTE: cannot set bed type {bed_type!r} without a process "
              "profile - the project 3MF's own plate setting applies. The "
              "post-slice summary below shows the commanded bed "
              "temperature; verify it before printing.")

    cmd = [slicer]
    if scale and scale != 1.0:
        cmd += ["--scale", f"{scale:g}"]
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
        combined = (proc.stdout or "") + (proc.stderr or "")
        profile_paths = " ".join(p for p in (machine, process, filament) if p)
        if proc.returncode in (3221225477, -1073741819):
            # 0xC0000005: bambu-studio.exe crashed with a Windows access
            # violation (field-seen on Thumbelina bringup, PR #23).
            hint = ("Exit code 3221225477 is 0xC0000005, a Windows access "
                    "violation inside bambu-studio.exe. Field-seen causes, "
                    "in order of likelihood: (a) STL input without the "
                    "three flattened profile JSONs (or with unflattened "
                    "ones), (b) --orient/--arrange applied to a project "
                    "3MF - retry with --no-arrange, (c) a GUI Bambu Studio "
                    "instance still running or hung in the background - "
                    "close it (check Task Manager) and retry.")
        elif ("unknown config type" in combined
                or "input preset file is invalid" in combined
                or re.search(r"[\\/]BambuStudio[\\/]user[\\/]",
                             profile_paths)):
            # Field-seen on Thumbelina (2026-07): pointing --load-settings
            # at Bambu Studio USER presets (AppData\Roaming\BambuStudio\
            # user\<id>\machine\*.json). Those are diff-only files, not
            # full configs, and the CLI refuses them with return_code -5
            # ("The input preset file is invalid and can not be parsed").
            hint = ("The profile JSONs look like Bambu Studio *user "
                    "presets* (AppData\\Roaming\\BambuStudio\\user\\...). "
                    "Those store only the diff from a parent preset, so "
                    "the CLI cannot parse them. Generate proper flattened "
                    "profiles with scripts/flatten_bambu_profiles.py "
                    "(point it at your installed Bambu Studio) and load "
                    "those instead.")
        elif "No layers were detected" in combined:
            hint = ("'No layers were detected' means the model has ~zero "
                    "printable height - usually an STL exported in meters "
                    "(re-run with --scale 1000) or inches (--scale 25.4), "
                    "or a degenerate mesh. Field-seen on Thumbelina with a "
                    "Fusion-style meters export, PR #23.")
        else:
            hint = ("First suspects (doc: 'Headless slicing'): unflattened "
                    "`inherits` chains in the profile JSONs, or missing "
                    "from/inherits/printer_settings_id patches on the "
                    "machine config. scripts/flatten_bambu_profiles.py "
                    "generates known-good flattened profiles.")
        sys.exit("ERROR: slicing failed (exit code "
                 f"{proc.returncode}).\nLast slicer output:\n{tail}\n{hint}")

    size_kb = os.path.getsize(export_path) // 1024
    print(f"Sliced OK: {export_path} ({size_kb} KB)")
    return export_path, out_dir


# --- G-code metadata parsing --------------------------------------------------
# Kept in sync with a1_mini_send_print.py.
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


def _max_temp(value):
    nums = [int(x) for x in re.findall(r"\d+", value)]
    return max(nums) if nums else None


# BambuStudio writes per-plate-type bed keys (cool/eng/hot/textured/
# supertack), NOT the PrusaSlicer-style `first_layer_bed_temperature`.
# For the hardware-limit check, take the worst case across plate types.
_BED_TEMP_KEYS = (
    "cool_plate_temp_initial_layer", "eng_plate_temp_initial_layer",
    "hot_plate_temp_initial_layer", "textured_plate_temp_initial_layer",
    "supertack_plate_temp_initial_layer",
    "cool_plate_temp", "eng_plate_temp", "hot_plate_temp",
    "textured_plate_temp", "supertack_plate_temp",
)


def commanded_bed_temp(zf):
    """First executable M190/M140 with S > 0 - the bed temperature the
    printer will actually run, regardless of what the header tables
    say. (Comment lines start with ';' so startswith() skips them.)"""
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


def summarize_and_check(path, force):
    """Print what is about to be printed; exit if the sliced job exceeds
    A1-mini hardware maxima (a wrong-profile symptom, not a preference)."""
    fields = read_gcode_metadata(zipfile.ZipFile(path))

    printer = fields.get("printer_settings_id") or fields.get("printer_model", "?")
    # The header packs two durations into one line ("; model printing
    # time: ...; total estimated time: ..."), so key-parse misses it.
    est_time = fields.get("total estimated time")
    if not est_time:
        m = re.search(r"total estimated time:\s*(.+)",
                      fields.get("model printing time", ""))
        est_time = m.group(1).strip() if m else "?"
    weight = fields.get("total filament weight [g]",
                        fields.get("filament used [g]", "?"))
    bed_temps = [_max_temp(fields.get(k, "")) for k in _BED_TEMP_KEYS]
    bed_temps = [t for t in bed_temps if t is not None]
    bed = max(bed_temps) if bed_temps else None
    nozzle = _max_temp(fields.get("nozzle_temperature", "") + " "
                       + fields.get("nozzle_temperature_initial_layer", ""))
    plate = fields.get("curr_bed_type", "?")
    bed_cmd = commanded_bed_temp(zipfile.ZipFile(path))

    print("--- Sliced job summary ------------------------------------")
    print(f"  printer profile : {printer}")
    print(f"  estimated time  : {est_time}")
    print(f"  filament [g]    : {weight}")
    print(f"  build plate     : {plate}")
    print(f"  bed temp commanded (first M190/M140) : "
          f"{bed_cmd if bed_cmd is not None else '?'} C "
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
    if bed_cmd is not None and bed_cmd < MIN_SANE_BED_C:
        problems.append(
            f"commanded first-layer bed temp is only {bed_cmd} C (plate "
            f"type {plate!r}) - nothing adheres to the textured PEI sheet "
            "below ~45 C and the job GHOST-PRINTS (runs the motions with "
            "nothing staying on the bed; field-seen on Thumbelina "
            "2026-07-27 with the CLI's Cool Plate 35 C default). Re-slice "
            'with --bed-type "Textured PEI Plate" (the default) or fix '
            "the plate selection in the project 3MF")
    if problems:
        msg = ("sliced job failed the sanity checks ("
               + "; ".join(problems) + ").")
        if force:
            print("WARN (--force): " + msg)
        else:
            sys.exit("ERROR: " + msg + " Pass --force to send anyway.")


# --- A1-mini payload sanity check --------------------------------------------
# Same gate as a1_mini_send_print.py (kept in sync); here it runs on OUR
# OWN slicer output, catching a wrong-printer profile bundle before
# upload. It reads the CONFIG_BLOCK's identity fields - it must NOT grep
# for substrings like "filament_map_mode", which BambuStudio >= 2.x
# writes into EVERY printer's G-code, A1 mini included (the old
# substring check false-positived on every legitimate A1-mini slice;
# found in Thumbelina field testing, PR #23).
def check_payload(path, force):
    warnings = []
    try:
        zf = zipfile.ZipFile(path)
    except zipfile.BadZipFile:
        sys.exit(f"ERROR: {path} is not a .3mf/zip archive.")
    if "Metadata/plate_1.gcode" not in zf.namelist():
        sys.exit(f"ERROR: {path} has no Metadata/plate_1.gcode - the "
                 "slicer exported a project 3MF, not a sliced job.")

    meta = read_gcode_metadata(zf)
    model = meta.get("printer_model") or meta.get("printer_settings_id") or ""
    # filament_map assigns each filament to an extruder; any value >= 2
    # means the job uses a second extruder, which the A1 mini lacks.
    map_values = [int(v) for v in
                  re.findall(r"\d+", meta.get("filament_map", ""))]

    problem = None
    if model and "A1 mini" not in model:
        problem = (f'{path} is sliced for "{model}", not an A1 mini - the '
                   "profile JSONs you loaded are not A1-mini profiles")
    elif any(v >= 2 for v in map_values):
        problem = (f"{path} maps filaments to a second extruder "
                   f"(filament_map = {meta.get('filament_map')}) - a "
                   "dual-extruder (H2D/IDEX) slice")
    if problem:
        if force:
            warnings.append("WARN (--force): " + problem + ".")
        else:
            sys.exit("ERROR: " + problem + ". Pass --force to send it anyway.")
    elif not model:
        warnings.append("WARN: no printer_model/printer_settings_id in the "
                        "G-code header - check the profile JSONs.")
    return warnings


# --- AMS mapping normalization ------------------------------------------------
# Kept in sync with a1_mini_send_print.py.
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
# Kept in sync with a1_mini_send_print.py / h2d_step4_bambulabs_api.py.
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


# --- FTPS upload --------------------------------------------------------------
# Kept in sync with a1_mini_send_print.py and h2d_step3_send_print.py.
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


# --- print.project_file payload -----------------------------------------------
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


# --- publish start command, watch gcode_state ----------------------------------
# Kept in sync across the three send scripts.
def start_and_watch(ip, code, serial, remote_name, remote_dir, use_ams,
                    ams_mapping, watch_seconds, wait_done=True):
    states = []
    running = threading.Event()
    finished = threading.Event()
    failed = threading.Event()
    armed = threading.Event()    # set once OUR start command is published
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
                if state in ("FAILED", "OFFLINE"):
                    failed.set()
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
            # yet. (Field-seen on Thumbelina.)
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
    parser.add_argument("--bed-type", default=None,
                        help="build plate to slice for (default from "
                        f"BED_TYPE, currently {BED_TYPE!r}; the CLI's own "
                        "default is Cool Plate / 35 C bed, which "
                        "ghost-prints on the stock textured sheet). "
                        'Aliases: textured, cool, eng, hot. Pass "" to '
                        "leave the profile/3MF value untouched")
    parser.add_argument("--scale", type=float, default=1.0,
                        help="uniform scale factor passed to the slicer "
                        "(1000 for a meters-unit STL, 25.4 for inches; "
                        "default 1.0)")
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
    parser.add_argument("--remote-dir", default="", metavar="DIR",
                        help="printer-side directory to upload to and "
                        "reference in the url (default: FTP root, the "
                        "A1-mini-proven path; 'cache' restores the old "
                        "/cache behaviour)")
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
    parser.add_argument("--force", action="store_true",
                        help="proceed even if the sliced job looks wrong "
                        "for an A1 mini")
    parser.add_argument("--yes", action="store_true",
                        help="skip the summary confirmation prompt "
                        "(read the RISKS note in this file first)")
    parser.add_argument("--watch", type=int, default=180, metavar="SECONDS")
    parser.add_argument("--no-wait", dest="wait_done", action="store_false",
                        default=True,
                        help="exit as soon as the printer reaches RUNNING "
                        "instead of watching until the print finishes")
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
    if slicer.lower().endswith(".lnk"):
        parser.error(
            f"{slicer} is a Windows Start-Menu shortcut (.lnk), not the "
            "program itself - subprocess cannot execute it. Point "
            "SLICER_CMD/--slicer at the real bambu-studio.exe (usually "
            r"C:\Program Files\Bambu Studio\bambu-studio.exe" ").")
    if not os.path.isfile(slicer):
        parser.error(f"no such slicer binary: {slicer}")

    use_ams = USE_AMS if args.use_ams is None else args.use_ams
    ams_mapping = normalize_ams_mapping(
        args.ams_mapping if args.ams_mapping is not None else AMS_MAPPING)
    if not use_ams:
        ams_mapping = ""  # external spool holder: no mapping in the payload
    elif ams_mapping == "":
        print("WARN: --use-ams without an AMS mapping - the printer will "
              'try its default tray; pass --ams-mapping "0" (etc.) to be '
              "explicit.")

    bed_type = normalize_bed_type(
        args.bed_type if args.bed_type is not None else BED_TYPE)

    kind = classify_input(path)
    if kind == "stl":
        check_stl_units(path, args.scale, args.force)
    if kind == "project_3mf" and (machine or process or filament):
        print("NOTE: --load-settings/--load-filaments OVERRIDE the "
              "settings embedded in the project 3MF (CLI precedence). "
              "Clear the profile fields to slice with the 3MF's own "
              "settings.")

    sliced, out_dir = slice_headless(
        slicer, path, kind, machine, process, filament,
        arrange=not args.no_arrange, timeout_s=args.slice_timeout,
        keep_dir=args.keep_output, scale=args.scale, bed_type=bed_type)
    try:
        summarize_and_check(sliced, args.force)
        for warning in check_payload(sliced, args.force):
            print(warning)

        # The sliced file, not this script's constants, is the authority
        # on whether an AMS tray has to be loaded (see apply_payload_ams).
        use_ams, ams_mapping = apply_payload_ams(
            sliced, use_ams, ams_mapping, args.use_ams is False, args.force)
        if not use_ams:
            ams_mapping = ""

        if args.slice_only:
            if not args.keep_output:
                print("NOTE: --slice-only without --keep-output deletes "
                      "the result; re-run with --keep-output to keep "
                      f"{sliced}")
            else:
                print(f"Slice-only mode: sliced file kept at {sliced}")
            return 0

        remote_dir = args.remote_dir.strip("/")
        remote_name = os.path.basename(sliced)
        upload(ip, code, sliced, remote_name, remote_dir)
        if args.upload_only:
            print("Upload-only mode: not starting a print.")
            return 0

        if use_ams:
            print(f"Filament source: AMS lite, tray mapping "
                  f"{ams_mapping or '(printer default)'} (0-indexed).")
        else:
            print("Filament source: EXTERNAL spool holder (use_ams "
                  "false). If your filament is actually loaded in the "
                  "AMS lite, pass --use-ams --ams-mapping <tray> or the "
                  "printer may run the job without feeding filament.")
        if not args.yes:
            answer = input(f"About to start a REAL print of {remote_name} "
                           f"on {serial} - G-code NO HUMAN HAS PREVIEWED "
                           "(summary above). Is the bed clear and the "
                           "summary sane? [y/N] ")
            if answer.strip().lower() not in ("y", "yes"):
                print("Aborted before publishing. File remains on the "
                      "printer.")
                return 1

        return start_and_watch(ip, code, serial, remote_name, remote_dir,
                               use_ams, ams_mapping, args.watch,
                               args.wait_done)
    finally:
        if not args.keep_output:
            shutil.rmtree(out_dir, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
