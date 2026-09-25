#!/usr/bin/env python3
"""Per-dose executor for the issue #164 optimization campaign (Pi Zero).

The fully non-interactive rig side of ``opt_campaign.py`` -- one
invocation, one dose (campaign-setup.md sections 1.1 / 3 / 5.3):

1. connect to the Pico over USB serial (``main_trickle.py`` running; if
   the Pico sits idle at a bare ``>>>`` REPL, the runner is booted from
   ``/trickle_tap`` automatically).  The Pico is SHARED with other
   sessions' firmware and tools, so this refuses (status ``rig-busy``,
   nothing sent that could disturb it, nothing dosed) when another
   process holds the port, when an unknown program is running, or when
   the runner is not ``opt_common.FIRMWARE_ID`` -- ``--takeover`` is the
   operator's explicit override (campaign-setup section 5.1),
2. push the trial's parameter set as ``set <key> <value>`` lines and
   verify every echo,
3. run ``g <target>``, stream every line to a raw log, and parse the
   firmware's machine-readable ``RESULT {json}`` line,
4. pull the dose telemetry CSV (``log``),
5. build the opt_trials document, spool it to the SD card
   (``data/opt/<campaign_id>/``), upload it to MongoDB when a
   connection string resolves (``$MONGODB_URI``, ``$PI_MONGODB_URI``,
   or the #131 ``~/.config/powder-doser/env`` file -- see
   ``opt_common.resolve_mongo_uri``), and
6. print exactly ONE JSON summary line on stdout for the laptop.

Everything human-readable goes to stderr; stdout is the contract.

Atomicity on a dropped SSH pipe: SIGHUP is ignored, so a dose in
flight completes, spools, and uploads even if the laptop vanishes; the
laptop then re-runs with the same ``--trial`` uuid (or ``--fetch``) and
gets the stored result back instead of re-dosing -- invoking this
script twice with one uuid NEVER doses twice.

Usage (normally built by opt_campaign.py, not typed):

    python3 scripts/opt_dose_capture.py \
        --powder-id salt --target-g 0.5 \
        --campaign-id salt-20260923T010203Z --trial <uuid> \
        --trial-index 7 --mode bo \
        --params '{"bulk_tap": "off", "trim_tap": "off", ...}'

    python3 scripts/opt_dose_capture.py --fetch <uuid>

Dependencies: pyserial; pymongo only when uploading.
"""

import argparse
import json
import os
import signal
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import opt_common as oc                                       # noqa: E402

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_OUT = os.path.join(REPO_ROOT, "data", "opt")

TELEMETRY_BEGIN = "--- BEGIN trickle telemetry CSV ---"
TELEMETRY_END = "--- END trickle telemetry CSV ---"
READY_MARKER = "trickle parameters"       # the 's' state listing
FIRMWARE_PREFIX = "firmware: "             # first line of that listing
IDLE_PROMPT = ">>>"                        # a bare MicroPython REPL


def log(msg):
    print("[opt-dose] {}".format(msg), file=sys.stderr, flush=True)


# ---------------------------------------------------------------------------
# Serial session
# ---------------------------------------------------------------------------

class RigBusy(RuntimeError):
    """The shared Pico belongs to someone else right now; nothing that
    could disturb it was sent, and nothing was dosed."""


def port_holders(port_path):
    """Other local processes with the serial device open -> [(pid, cmd)].

    The exclusive open below already refuses lock-takers (mpremote and
    the #116 portguard.sh take the same flock); this catches the bench
    tools that open the port WITHOUT a lock (the #116/#131 capture
    scripts use a plain ``serial.Serial``).  Without root only the rig
    user's own processes are visible -- which is every rig session.
    """
    target = os.path.realpath(port_path)
    holders = []
    try:
        pids = [p for p in os.listdir("/proc") if p.isdigit()]
    except OSError:
        return holders
    for pid in pids:
        if int(pid) == os.getpid():
            continue
        fd_dir = os.path.join("/proc", pid, "fd")
        try:
            links = [os.readlink(os.path.join(fd_dir, fd))
                     for fd in os.listdir(fd_dir)]
        except OSError:
            continue
        if target in links:
            try:
                with open(os.path.join("/proc", pid, "cmdline"), "rb") as f:
                    cmd = f.read().replace(b"\0", b" ").decode(
                        errors="replace").strip()
            except OSError:
                cmd = "?"
            holders.append((int(pid), cmd[:120]))
    return holders


class PicoSession:
    """Line-oriented conversation with the running main_trickle REPL."""

    def __init__(self, port_path, baud, raw_log_path):
        import serial                     # pip install pyserial
        try:
            # The same advisory lock mpremote takes: while a dose runs,
            # other sessions' mpremote calls fail fast instead of
            # interleaving with it, and theirs keep us out likewise.
            self.port = serial.Serial(port_path, baud, timeout=0.25,
                                      exclusive=True)
        except OSError as exc:            # pyserial's SerialException
            if "lock" in str(exc).lower():
                raise RigBusy("{} is locked by another session (mpremote "
                              "or a port guard)".format(port_path))
            raise
        holders = port_holders(port_path)
        if holders:
            self.port.close()
            raise RigBusy("{} is also open in {}".format(
                port_path, "; ".join("pid {} ({})".format(p, c)
                                     for p, c in holders)))
        self.raw = open(raw_log_path, "a")
        self.raw.write("--- session {} ---\n".format(oc.utcnow_iso()))

    def close(self):
        try:
            self.port.close()
        finally:
            self.raw.close()

    def send(self, line):
        self.raw.write(">> {}\n".format(line))
        self.port.write(line.encode() + b"\r\n")
        self.port.flush()

    def lines(self, timeout_s, idle_stop_s=None):
        """Yield decoded lines until ``timeout_s`` elapses (or the port
        stays silent ``idle_stop_s`` after having spoken)."""
        deadline = time.monotonic() + timeout_s
        last = time.monotonic()
        spoke = False
        while time.monotonic() < deadline:
            raw = self.port.readline()
            if not raw:
                if (idle_stop_s and spoke
                        and time.monotonic() - last > idle_stop_s):
                    return
                continue
            line = raw.decode(errors="replace").rstrip("\r\n")
            self.raw.write(line + "\n")
            self.raw.flush()
            spoke = True
            last = time.monotonic()
            yield line

    def drain(self, quiet_s=0.5, max_s=3.0):
        """Read whatever is pending -> (lines, went_quiet): stops at the
        first ``quiet_s`` of silence, or gives up after ``max_s``."""
        seen = []
        deadline = time.monotonic() + max_s
        last = time.monotonic()
        while time.monotonic() < deadline:
            raw = self.port.readline()
            if raw:
                line = raw.decode(errors="replace").rstrip("\r\n")
                self.raw.write(line + "\n")
                self.raw.flush()
                seen.append(line)
                last = time.monotonic()
            elif time.monotonic() - last >= quiet_s:
                return seen, True
        return seen, False

    def collect_until(self, predicate, timeout_s):
        """Collect lines until ``predicate(line)`` is truthy; returns
        (matching line or None, all lines seen)."""
        seen = []
        for line in self.lines(timeout_s):
            seen.append(line)
            if predicate(line):
                return line, seen
        return None, seen


def _classify(lines):
    """-> "runner" (main_trickle's listing), "repl" (idle >>>), or None."""
    for line in lines:
        if READY_MARKER in line:
            return "runner"
        if line.startswith(IDLE_PROMPT):
            return "repl"
    return None


def _probe(sess, line, timeout_s):
    """Send ``line``; -> (classification, lines seen)."""
    sess.send(line)
    seen = []
    for got in sess.lines(timeout_s):
        seen.append(got)
        kind = _classify([got])
        if kind:
            return kind, seen
    return None, seen


def _firmware_of(lines):
    for line in lines:
        if line.startswith(FIRMWARE_PREFIX):
            return line[len(FIRMWARE_PREFIX):].strip()
    return None


def _wait_for(sess, text, timeout_s):
    match, _ = sess.collect_until(lambda l: text in l, timeout_s)
    if match is None:
        raise RuntimeError("Pico never printed {!r}".format(text))


def _boot_runner(sess, pico_dir, boot_timeout_s):
    """From an idle REPL: clean soft reset, then start /trickle_tap's
    runner.  The raw-REPL soft reset (what mpremote does) empties
    sys.modules -- no root-level config/main_three_phase left over from
    another session -- without running main.py.  -> listing lines."""
    log("booting main_trickle from {} on the Pico".format(pico_dir or "/"))
    sess.port.write(b"\r\x01")               # ctrl-A: raw REPL
    _wait_for(sess, "raw REPL; CTRL-B to exit", 5)
    sess.port.write(b"\x04")                  # ctrl-D: soft reset
    _wait_for(sess, "soft reboot", 10)
    _wait_for(sess, "raw REPL; CTRL-B to exit", 10)
    sess.port.write(b"\x02")                  # ctrl-B: friendly REPL
    _wait_for(sess, IDLE_PROMPT, 5)
    boot = "import main_trickle; main_trickle.main()"
    if pico_dir.strip("/"):
        boot = "import sys; sys.path.insert(0, {!r}); {}".format(
            pico_dir, boot)
    sess.send(boot)
    match, seen = sess.collect_until(lambda l: READY_MARKER in l,
                                     boot_timeout_s)
    if match is None:
        raise RuntimeError(
            "Pico did not reach the main_trickle command loop -- is the "
            "trickle_tap build uploaded to {} (README) and the USB cable "
            "good?".format(pico_dir or "/"))
    return seen


def ensure_runner(sess, pico_dir=oc.PICO_FIRMWARE_DIR, takeover=False,
                  boot_timeout_s=60):
    """Make sure OUR main_trickle build is answering -- without ever
    interrupting a program someone else started on the shared Pico.

    * our runner answering ``s`` with the expected ``firmware:`` line
      -> use it;
    * an idle ``>>>`` REPL -> clean-boot the runner from ``pico_dir``;
    * anything else (output streaming with nobody connected, a program
      that answers neither probe, another firmware's runner) -> RigBusy,
      unless ``takeover`` (operator's call): then ctrl-C and boot ours.

    Raises RigBusy (nothing disturbed) or RuntimeError (rig fault).
    """
    # Output streaming while nobody holds the port means a program is
    # mid-run (another session's, or a dose whose executor died): never
    # type into it.
    pending, quiet = sess.drain()
    kind, seen = None, pending
    if quiet:
        kind, seen = _probe(sess, "", 2)
        if kind != "repl":                # "runner" only from a fresh 's'
            kind, seen = _probe(sess, "s", 4)
    if kind == "runner":
        rest, _ = sess.drain()
        fw = _firmware_of(seen + rest)
        if fw == oc.FIRMWARE_ID:
            return
        what = "a runner reporting firmware {!r}".format(fw) if fw else \
            "a trickle runner without a firmware id (another build)"
        if not takeover:
            raise RigBusy(
                "the Pico is running {} -- expected {!r}.  If it is a "
                "stale copy of ours, re-run with --takeover to restart "
                "it".format(what, oc.FIRMWARE_ID))
        log("--takeover: stopping {}".format(what))
    elif kind is None:
        if not takeover:
            raise RigBusy(
                "the Pico is {} -- probably another session's program; "
                "not interrupting it.  Re-run with --takeover only if you "
                "know it is safe to stop".format(
                    "answering neither main_trickle's 's' nor a >>> prompt"
                    if quiet else "streaming output with nobody connected"))
        log("--takeover: interrupting whatever is running on the Pico")
    if kind != "repl":
        # ctrl-C stops a program; ctrl-B also leaves a raw REPL behind
        sess.port.write(b"\x03\x03\x02")
        _wait_for(sess, IDLE_PROMPT, 5)
    listing = _boot_runner(sess, pico_dir, boot_timeout_s)
    rest, _ = sess.drain()
    fw = _firmware_of(listing + rest)
    if fw != oc.FIRMWARE_ID:
        raise RuntimeError(
            "booted firmware {!r} from {}, expected {!r} -- upload this "
            "branch's trickle_tap build there (README)".format(
                fw, pico_dir or "/", oc.FIRMWARE_ID))


def push_params(sess, params):
    """Send every ``set`` line and verify the firmware's echo."""
    for line in oc.firmware_set_lines(params):
        key = line.split()[1]
        sess.send(line)
        ok, seen = sess.collect_until(
            lambda l: "[set] {} = ".format(key) in l, 5)
        if ok is None:
            bad = [l for l in seen if "[set]" in l]
            raise RuntimeError(
                "parameter push failed at {!r} (firmware said: {})".format(
                    line, bad or "nothing"))


def run_dose(sess, target_g, timeout_s):
    """Issue the dose; returns (result_doc or None, status_str)."""
    sess.send("g {:.4f}".format(target_g))
    match, _ = sess.collect_until(
        lambda l: l.startswith(oc.RESULT_PREFIX), timeout_s)
    if match is None:
        # The dose may have finished while a buffer hiccuped -- ask the
        # firmware to reprint its last RESULT before giving up.
        log("no RESULT line inside {} s; asking for a reprint".format(
            timeout_s))
        sess.send("res")
        match, _ = sess.collect_until(
            lambda l: l.startswith(oc.RESULT_PREFIX), 10)
    if match is None:
        return None, "no-result"
    try:
        doc = json.loads(match[len(oc.RESULT_PREFIX):])
    except ValueError as exc:
        log("RESULT line did not parse: {}".format(exc))
        return None, "no-result"
    return doc, doc.get("status", "no-result")


def pull_telemetry(sess):
    """-> (header or None, rows) from the ``log`` command."""
    sess.send("log")
    header, rows, inside = None, [], False
    for line in sess.lines(30, idle_stop_s=3):
        if line.startswith(TELEMETRY_BEGIN):
            inside = True
            continue
        if line.startswith(TELEMETRY_END):
            break
        if "[log] no telemetry" in line:
            break
        if inside:
            if header is None:
                header = line
            else:
                rows.append(line)
    return header, rows


# ---------------------------------------------------------------------------
# Modes
# ---------------------------------------------------------------------------

def emit(summary):
    """The stdout contract: exactly one JSON line."""
    try:
        print(json.dumps(summary), flush=True)
    except BrokenPipeError:               # laptop went away mid-print;
        pass                              # the spool already has it


def do_fetch(args):
    doc = oc.find_spooled_trial(args.out, args.fetch,
                                campaign_id=args.campaign_id or None)
    if doc is None:
        emit({"kind": "opt_trial_summary", "trial_uuid": args.fetch,
              "status": "not-found", "infra_error": True})
        return 3
    emit(oc.trial_summary(doc, uploaded=None))
    return 0


def do_dose(args):
    params = oc.validate_params(json.loads(args.params))
    covariates = json.loads(args.covariates) if args.covariates else {}
    powder_id = oc.normalize_powder_id(args.powder_id)

    # Idempotency: a re-invocation with a uuid that already dosed is a
    # fetch, never a second dose.
    prior = oc.find_spooled_trial(args.out, args.trial, args.campaign_id)
    if prior is not None:
        log("trial {} already spooled -- returning the stored result "
            "instead of re-dosing".format(args.trial))
        emit(oc.trial_summary(prior, uploaded=None))
        return 0

    started_utc = oc.utcnow_iso()
    spool = oc.spool_dir(args.out, args.campaign_id)
    raw_log = os.path.join(spool, "serial_{}.log".format(args.trial))

    result_doc, status, telemetry = None, "serial-error", (None, [])
    sess = None
    try:
        sess = PicoSession(args.port, args.baud, raw_log)
        ensure_runner(sess, pico_dir=args.pico_dir, takeover=args.takeover)
        push_params(sess, params)
        result_doc, status = run_dose(sess, args.target_g, args.timeout_s)
        if result_doc is not None:
            telemetry = pull_telemetry(sess)
    except RigBusy as exc:
        log("rig busy, nothing dosed: {}".format(exc))
        status = "rig-busy"
    except Exception as exc:
        log("dose attempt failed: {}".format(exc))
        status = "serial-error"
    finally:
        if sess is not None:
            sess.close()

    doc = oc.build_trial_doc(
        campaign_id=args.campaign_id, trial_uuid=args.trial,
        trial_index=args.trial_index, powder_id=powder_id,
        target_g=args.target_g, mode=args.mode, params=params,
        result_doc=result_doc, telemetry_rows=telemetry[1],
        telemetry_header=telemetry[0], covariates=covariates,
        operator=args.operator, started_utc=started_utc,
        repo_root=REPO_ROOT, raw_status=status)

    spool_path = oc.spool_trial(args.out, doc)
    uploaded = False
    if not args.no_upload:
        try:
            uploaded = oc.upload_trial(doc)
        except Exception as exc:
            log("Mongo upload failed ({}); document is spooled at {} "
                "for backfill".format(exc, spool_path))
    doc_flags = doc["flags"]
    log("dose {}: status={} jam={} t={}s |err|={}mg -> {} (uploaded={})"
        .format(args.trial[:8], doc_flags["status"], doc_flags["jam"],
                doc["outcomes"]["t_total_s"],
                doc["outcomes"]["abs_error_mg"], spool_path, uploaded))
    emit(oc.trial_summary(doc, spool_path=spool_path, uploaded=uploaded))
    return 0 if not doc_flags["infra_error"] else 4


def main(argv=None):
    # A dropped SSH pipe must never kill a dose in flight.
    try:
        signal.signal(signal.SIGHUP, signal.SIG_IGN)
    except (AttributeError, ValueError):
        pass

    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--port", default="/dev/ttyACM0")
    ap.add_argument("--baud", type=int, default=115200)
    ap.add_argument("--powder-id")
    ap.add_argument("--target-g", type=float)
    ap.add_argument("--campaign-id")
    ap.add_argument("--trial", help="trial uuid minted by the laptop")
    ap.add_argument("--trial-index", type=int, default=-1)
    ap.add_argument("--mode", default="bo",
                    choices=["screen", "recenter", "bo", "validation",
                             "production"])
    ap.add_argument("--params", help="JSON campaign-space parameters")
    ap.add_argument("--covariates", help="JSON session covariates")
    ap.add_argument("--operator")
    ap.add_argument("--out", default=DEFAULT_OUT)
    ap.add_argument("--timeout-s", type=float, default=720.0,
                    help="wall clock to wait for the RESULT line "
                         "(firmware dose timeout is 600 s)")
    ap.add_argument("--pico-dir", default=oc.PICO_FIRMWARE_DIR,
                    help="folder holding the trickle_tap build on the "
                         "Pico's flash ('/' = legacy root upload)")
    ap.add_argument("--takeover", action="store_true",
                    help="operator override: ctrl-C whatever runs on the "
                         "shared Pico and boot our runner")
    ap.add_argument("--no-upload", action="store_true")
    ap.add_argument("--fetch", metavar="UUID",
                    help="print a stored trial's summary; never doses")
    args = ap.parse_args(argv)

    if args.fetch:
        return do_fetch(args)
    missing = [n for n in ("powder_id", "target_g", "campaign_id",
                           "trial", "params") if getattr(args, n) is None]
    if missing:
        ap.error("missing required arguments: {}".format(
            ", ".join("--" + m.replace("_", "-") for m in missing)))
    return do_dose(args)


if __name__ == "__main__":
    sys.exit(main())
