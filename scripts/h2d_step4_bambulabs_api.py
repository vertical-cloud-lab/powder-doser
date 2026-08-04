#!/usr/bin/env python3
"""Step 4 - the same print as Step 3, driven through `bambulabs_api`.

Once Step 3 is green from the raw FTPS/MQTT script, this is the
library-backed version you'd actually build on (it is also what the
Step 5/6 Pi relay in the doc wraps in FastAPI). Internally
`bambulabs_api` does the identical implicit-FTPS upload + MQTT
`print.project_file` publish that h2d_step3_send_print.py does by hand.

Works on any LAN-mode Bambu printer, not just the H2D: verified on the
A1 mini ("Thumbelina") 2026-08-04 with payloads/Testpart2.gcode.3mf -
print started and completed. Still unexercised on the H2D itself.

CAUTION: this starts a REAL print. Clear the bed first. The script asks
for confirmation; pass --yes to skip (for automation).

    pip install bambulabs_api
    python h2d_step4_bambulabs_api.py cube_h2d.gcode.3mf \
        --ip <IP> --access-code <CODE> --serial <SERIAL>

Credentials may also come from H2D_IP / H2D_ACCESS_CODE / H2D_SERIAL
(BAMBU_* and A1_MINI_* names are accepted too).

AMS: the filament source is read OUT OF THE SLICED FILE by default -
see resolve_ams() below - so an AMS-fed job no longer needs the
`use_ams=False` in this file to be hand-edited (Thumbelina, 2026-08-04).
Override with --use-ams / --no-ams / --ams-mapping.

Note: `bambulabs_api` is community-maintained and its signatures have
shifted between releases (see the H2D-untested caveat in the doc's
library table). This script targets the shape used in the project's own
examples - `Printer(ip, code, serial)`, `upload_file(fileobj, name)`
returning an FTP status string, `start_print(name, plate)` - probes
`start_print` for the kwargs it actually accepts, and prints the
library version up front so a mismatch is easy to spot.
"""

import argparse
import inspect
import os
import re
import sys
import time
import zipfile

import bambulabs_api as bl


# --- remote filename ---------------------------------------------------------
def sanitize_remote_name(name):
    """Restrict the remote filename to A-Za-z0-9._- .

    The name ends up verbatim in the MQTT `url`; on Thumbelina a
    filename with spaces was rejected printer-side with error 83935248
    (hex 0500-C010, a file-path/parse failure) even though the FTPS
    upload succeeded. Kept in sync with the other send scripts."""
    return re.sub(r"[^A-Za-z0-9._-]+", "_", name)


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
    # 0-indexed tool the job loads (255 = unload//no AMS sentinel).
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


def inspect_payload(path, plate, force):
    """Print what the file is and hard-stop on the known-bad shapes.
    Returns the filament slots the job uses (see filament_slots_used)."""
    try:
        zf = zipfile.ZipFile(path)
    except zipfile.BadZipFile:
        sys.exit(f"ERROR: {path} is not a .3mf/zip archive - did you point "
                 "this at an STL? Slice it first.")
    if "Metadata/plate_1.gcode" not in zf.namelist():
        sys.exit(f"ERROR: {path} has no Metadata/plate_1.gcode - this is a "
                 "project 3MF, not a sliced .gcode.3mf. Slice it and retry.")

    meta = read_gcode_metadata(zf)
    model = meta.get("printer_model") or meta.get("printer_settings_id") or "?"
    bed_type = meta.get("curr_bed_type", "?")
    bed_cmd = commanded_bed_temp(zf)
    print(f"Payload: sliced for {model!r}; build plate {bed_type!r}; "
          f"commanded first-layer bed temp "
          f"{bed_cmd if bed_cmd is not None else '?'} C")

    if bed_cmd is not None and bed_cmd < MIN_SANE_BED_C:
        msg = (f"{path} commands a first-layer bed temp of only {bed_cmd} C "
               f"(plate type {bed_type!r}) - nothing adheres to the textured "
               "PEI sheet below ~45 C and the job GHOST-PRINTS (runs the "
               "motions with nothing staying on the bed). Re-export with the "
               "correct build plate selected")
        if force:
            print("WARN (--force): " + msg + ".")
        else:
            sys.exit("ERROR: " + msg + ". Pass --force to send it anyway.")

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
              "h2d_step3_send_print.py, which builds the payload directly.")
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


# --- state watch --------------------------------------------------------------
def _progress_line(printer):
    bits = []
    for attr, fmt in (("get_percentage", "{}%"),
                      ("get_time", "~{} min left")):
        getter = getattr(printer, attr, None)
        if getter is None:
            continue
        try:
            value = getter()
        except Exception:
            continue
        if value not in (None, "", "Unknown"):
            bits.append(fmt.format(value))
    return ", ".join(bits)


def watch(printer, watch_seconds, wait_done):
    """Follow gcode_state to RUNNING, then (unless --no-wait) stay
    attached until the printer reports FINISH.

    FINISH only counts once RUNNING has been seen: an idle Bambu keeps
    re-reporting the PREVIOUS job's FINISH, which would otherwise fire
    a false 'print complete' the moment we connect."""
    last = None
    running = False
    deadline = time.monotonic() + watch_seconds
    last_progress = 0.0
    while True:
        state = str(printer.get_state())
        if state != last:
            print(f"gcode_state: {state}")
            last = state
        if state == "RUNNING" and not running:
            running = True
            print("SUCCESS: printer reached RUNNING.")
            if not wait_done:
                return 0
            print("Watching until it finishes - Ctrl-C detaches WITHOUT "
                  "stopping the print ...")
        if state in ("FAILED", "OFFLINE"):
            print("FAILED: see the Step 3 triage list in "
                  "docs/h2d-programmatic-access.md.")
            return 2
        if running and state in ("FINISH", "FINISHED"):
            print("\a" + "=" * 62)
            print("PRINT COMPLETE: the printer reported gcode_state "
                  f"{state}.")
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
            print(f"TIMEOUT: no RUNNING within {watch_seconds}s "
                  f"(last state: {last}).")
            return 3
        if running and time.monotonic() - last_progress > 60:
            last_progress = time.monotonic()
            line = _progress_line(printer)
            if line:
                print(f"progress: {line}")
        time.sleep(3)


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("file", help="path to a sliced .gcode.3mf")
    parser.add_argument("--ip", default=os.environ.get(
        "H2D_IP", os.environ.get("BAMBU_IP", os.environ.get("A1_MINI_IP"))))
    parser.add_argument("--access-code", default=os.environ.get(
        "H2D_ACCESS_CODE", os.environ.get(
            "BAMBU_ACCESS_CODE", os.environ.get("A1_MINI_ACCESS_CODE"))))
    parser.add_argument("--serial", default=os.environ.get(
        "H2D_SERIAL", os.environ.get(
            "BAMBU_SERIAL", os.environ.get("A1_MINI_SERIAL"))))
    parser.add_argument("--plate", type=int, default=1,
                        help="plate number inside the 3MF (default 1)")
    parser.add_argument("--use-ams", dest="use_ams", action="store_true",
                        default=None,
                        help="force AMS feed (default: read from the file)")
    parser.add_argument("--no-ams", dest="use_ams", action="store_false",
                        help="force the external spool holder (refused if the "
                             "file needs an AMS tray, unless --force)")
    parser.add_argument("--ams-mapping", default=None,
                        help='AMS tray indices, 0-indexed, e.g. "0" or "0,1" '
                             "(default: derived from the file)")
    parser.add_argument("--yes", action="store_true",
                        help="skip the clear-the-bed confirmation prompt")
    parser.add_argument("--force", action="store_true",
                        help="send even if the payload checks object")
    parser.add_argument("--no-wait", dest="wait_done", action="store_false",
                        help="exit once RUNNING instead of waiting for FINISH")
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
    slots = inspect_payload(args.file, args.plate, args.force)
    use_ams, ams_mapping = resolve_ams(slots, args.use_ams, args.ams_mapping,
                                       args.force)
    print("Filament source: "
          + (f"AMS, tray mapping {ams_mapping or '(printer default)'} "
             "(0-indexed)" if use_ams else "EXTERNAL spool holder"))

    remote_name = sanitize_remote_name(os.path.basename(args.file))
    if remote_name != os.path.basename(args.file):
        print(f"NOTE: uploading as {remote_name} (the printer rejects paths "
              "with spaces and other punctuation).")

    printer = bl.Printer(args.ip, args.access_code, args.serial)
    printer.connect()
    time.sleep(2)  # give the MQTT client a moment to receive first status
    try:
        state = str(printer.get_state())
        print(f"Printer state before print: {state}")
        if state in ("RUNNING", "PREPARE") and not args.force:
            print("ERROR: the printer is already printing - not sending "
                  "another job. Pass --force to override.")
            return 2

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

        call_start_print(printer, remote_name, args.plate, use_ams, ams_mapping)
        print("start_print sent; watching gcode_state ...")
        try:
            return watch(printer, args.watch, args.wait_done)
        except KeyboardInterrupt:
            print("\nDetached. The print continues on the printer.")
            return 0
    finally:
        printer.disconnect()


if __name__ == "__main__":
    sys.exit(main())
