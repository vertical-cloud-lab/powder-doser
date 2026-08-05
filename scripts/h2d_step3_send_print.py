#!/usr/bin/env python3
"""Step 3 - end-to-end dry run: upload a .gcode.3mf and start the print.

Does the doc's 3a/3b/3c in one command (Win/macOS/Linux, no lftp or
mosquitto needed):

  1. Uploads the file to the printer's /cache over implicit FTPS
     (TLS 1.2 session reuse - same verified stack as h2d_smoketest.py).
  2. Publishes the `print.project_file` command over MQTT-over-TLS.
  3. Watches device/<SERIAL>/report and prints every `gcode_state`
     transition; once RUNNING, keeps watching (with progress lines)
     until the print FINISHes and announces PRINT COMPLETE. Ctrl-C
     during that wait detaches WITHOUT stopping the print; --no-wait
     exits at RUNNING instead.

CAUTION: this starts a REAL print. Clear the bed first. The script asks
for confirmation before publishing; pass --yes to skip (for automation).

    pip install paho-mqtt
    python h2d_step3_send_print.py cube_h2d.gcode.3mf \
        --ip <IP> --access-code <CODE> --serial <SERIAL>

Credentials may also come from H2D_IP / H2D_ACCESS_CODE / H2D_SERIAL.
Use --upload-only to run just the FTPS leg (3a) without starting a print.

The filament source (external spool vs. AMS tray) is read out of the
sliced file - see apply_payload_ams() - so an AMS-fed job needs no
flags; --use-ams / --no-ams / --ams-mapping override the detection.

If gcode_state never leaves IDLE, see the triage list under Step 3 in
docs/h2d-programmatic-access.md (url path mismatch - note the THREE
slashes in ftp:///cache/..., wrong-printer slicer profile, or Developer
Mode silently re-disabled by a firmware update).
"""

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


def make_mqtt_client():
    # paho-mqtt 2.x deprecates the bare Client() constructor (the lab
    # laptops printed "Callback API version 1 is deprecated"). on_message
    # has the same signature under VERSION2, so use it when available;
    # paho-mqtt 1.x has no CallbackAPIVersion and takes the old form.
    try:
        return mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    except AttributeError:
        return mqtt.Client()


def sanitize_remote_name(name):
    """Restrict the remote filename to A-Za-z0-9._- .

    The name is embedded verbatim in the MQTT `url`
    (`ftp:///cache/<name>`); on the lab's A1 mini a filename with spaces
    was rejected printer-side with error 83935248 (hex 0500-C010, a
    file-path/parse failure) even though the FTPS upload succeeded, and
    the same URL parsing applies fleet-wide."""
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
                "Make sure the upload dir and the url agree; on the lab's "
                "A1 mini the fix was --remote-dir '' (FTP root + "
                "ftp:///<name>), and the same is worth trying here.",
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


# --- Step 3a: FTPS upload ---------------------------------------------------
# Kept in sync with a1_mini_send_print.py and a1_mini_slice_and_send.py.
def _ftps_connect(ip, code):
    ftps = ImplicitFTP_TLS(context=make_ftps_context())
    ftps.connect(ip, 990, 30)
    ftps.login("bblp", code)
    ftps.prot_p()
    return ftps


def upload(ip, code, local_path, remote_name, remote_dir="cache"):
    dest = remote_path(remote_dir, remote_name)
    list_dir = "/" + remote_dir if remote_dir else "/"
    ftps = _ftps_connect(ip, code)
    interrupted = None
    with open(local_path, "rb") as f:
        try:
            resp = ftps.storbinary(f"STOR {dest}", f)
            print(f"FTPS upload: {resp}")
        except (OSError, ftplib.Error) as e:
            # Field-tested on the real A1 mini (Thumbelina, PR #23), and
            # plausibly fleet-wide: after a successful STOR the printer
            # sometimes never completes the TLS shutdown on the data
            # channel, so the client times out (or sees an SSL error)
            # waiting for the 226 even though every byte landed. The
            # control channel is then out of sync - the late 226 surfaces
            # as a bogus reply to the next command - so don't trust this
            # session: reconnect and check whether the file arrived.
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


# --- Step 3c payload (matches the doc's verified minimal command) -----------
# --- AMS auto-detection from the sliced file ---------------------------------
# Kept in sync with the other send scripts.
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


def normalize_ams_mapping(value):
    """Accept [0], "0", "0,1" or "[1]" and return a list of ints (AMS
    tray indices, 0-indexed), or "" for no mapping. Kept in sync with
    the other send scripts."""
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
            # bambulabs_api's payload also names the file directly;
            # harmless where unused.
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


# --- Step 3b+3c: publish start command, watch gcode_state -------------------
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
            # yet. (Field-seen on the lab's A1 mini: a 0500-C010 from a
            # May attempt was still being reported in July.)
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
            print("FAILED: printer rejected or aborted the job - see triage "
                  "list in the doc (Step 3).")
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
          "See the Step 3 triage list in docs/h2d-programmatic-access.md.")
    return 3


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("file", help="path to a sliced .gcode.3mf "
                        "(must contain Metadata/plate_1.gcode)")
    parser.add_argument("--ip", default=os.environ.get("H2D_IP"))
    parser.add_argument("--access-code", default=os.environ.get("H2D_ACCESS_CODE"))
    parser.add_argument("--serial", default=os.environ.get("H2D_SERIAL"))
    parser.add_argument("--remote-dir", default="cache", metavar="DIR",
                        help="printer-side directory to upload to and "
                        "reference in the url (default: cache, the "
                        "community H2D flow; pass '' for the FTP root, "
                        "which is what fixed error 0500-4003 on the "
                        "lab's A1 mini)")
    parser.add_argument("--use-ams", dest="use_ams", action="store_true",
                        default=None,
                        help="feed from an AMS instead of the external spool "
                        "(default: read from the sliced file)")
    parser.add_argument("--no-ams", dest="use_ams", action="store_false",
                        help="force the external spool holder (refused if the "
                        "file needs an AMS tray, unless --force)")
    parser.add_argument("--ams-mapping", default=None,
                        help='AMS tray indices, 0-indexed, e.g. "0" or "0,1" '
                        "(default: derived from the sliced file)")
    parser.add_argument("--force", action="store_true",
                        help="send even if the AMS check objects")
    parser.add_argument("--upload-only", action="store_true",
                        help="run 3a (FTPS upload) only; don't start a print")
    parser.add_argument("--yes", action="store_true",
                        help="skip the clear-the-bed confirmation prompt")
    parser.add_argument("--watch", type=int, default=180, metavar="SECONDS",
                        help="how long to wait for RUNNING (default 180)")
    parser.add_argument("--no-wait", dest="wait_done", action="store_false",
                        default=True,
                        help="exit as soon as the printer reaches RUNNING "
                        "instead of watching until the print finishes")
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

    # The sliced file, not a hard-coded default, decides whether an AMS
    # tray has to be loaded (see apply_payload_ams).
    use_ams = bool(args.use_ams)
    ams_mapping = normalize_ams_mapping(args.ams_mapping)
    use_ams, ams_mapping = apply_payload_ams(
        args.file, use_ams, ams_mapping, args.use_ams is False, args.force)
    if not use_ams:
        ams_mapping = ""
    print("Filament source: "
          + (f"AMS, tray mapping {ams_mapping or '(printer default)'} "
             "(0-indexed)" if use_ams else "EXTERNAL spool holder"))

    remote_dir = args.remote_dir.strip("/")
    remote_name = sanitize_remote_name(os.path.basename(args.file))
    if remote_name != os.path.basename(args.file):
        print(f"NOTE: uploading as {remote_name!r} - spaces/special "
              "characters in the filename break the printer's file-path "
              "parsing (error 83935248 / 0500-C010).")
    upload(args.ip, args.access_code, args.file, remote_name, remote_dir)
    if args.upload_only:
        print("Upload-only mode: not starting a print.")
        return 0

    if not args.yes:
        answer = input(f"About to start a REAL print of {remote_name} on "
                       f"{args.serial}. Is the bed clear? [y/N] ")
        if answer.strip().lower() not in ("y", "yes"):
            print("Aborted before publishing. File remains on the printer.")
            return 1

    return start_and_watch(args.ip, args.access_code, args.serial,
                           remote_name, remote_dir, use_ams, ams_mapping,
                           args.watch, args.wait_done)


if __name__ == "__main__":
    sys.exit(main())
