#!/usr/bin/env python3
"""Per-dose executor for the issue #164 optimization campaign (Pi Zero).

The fully non-interactive rig side of ``opt_campaign.py`` -- one
invocation, one dose (campaign-setup.md sections 1.1 / 3 / 5.3):

1. connect to the Pico over USB serial (``main_trickle.py`` running; if
   the Pico sits at a bare REPL after a power cycle, it is bootstrapped
   automatically),
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


def log(msg):
    print("[opt-dose] {}".format(msg), file=sys.stderr, flush=True)


# ---------------------------------------------------------------------------
# Serial session
# ---------------------------------------------------------------------------

class PicoSession:
    """Line-oriented conversation with the running main_trickle REPL."""

    def __init__(self, port_path, baud, raw_log_path):
        import serial                     # pip install pyserial
        self.port = serial.Serial(port_path, baud, timeout=0.25)
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

    def collect_until(self, predicate, timeout_s):
        """Collect lines until ``predicate(line)`` is truthy; returns
        (matching line or None, all lines seen)."""
        seen = []
        for line in self.lines(timeout_s):
            seen.append(line)
            if predicate(line):
                return line, seen
        return None, seen


def ensure_runner(sess, boot_timeout_s=60):
    """Make sure main_trickle's command loop is answering.

    Probes with ``s``; on silence assumes a bare REPL (fresh power-up)
    and boots the runner, which the MicroPico workflow otherwise starts
    by hand.  Raises RuntimeError when the rig cannot be reached.
    """
    sess.send("")
    match, _ = sess.collect_until(lambda l: READY_MARKER in l, 4)
    if match is None:
        sess.send("s")
        match, _ = sess.collect_until(lambda l: READY_MARKER in l, 6)
    if match is not None:
        return
    log("runner not answering; bootstrapping main_trickle on the Pico")
    sess.port.write(b"\x03\x03")          # -> >>> (idle REPL only)
    time.sleep(1.0)
    sess.send("import main_trickle")
    time.sleep(1.0)
    sess.send("main_trickle.main()")
    match, _ = sess.collect_until(lambda l: READY_MARKER in l,
                                  boot_timeout_s)
    if match is None:
        sess.send("s")
        match, _ = sess.collect_until(lambda l: READY_MARKER in l, 10)
    if match is None:
        raise RuntimeError(
            "Pico did not reach the main_trickle command loop -- is the "
            "trickle_tap folder uploaded and the USB cable good?")


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
    try:
        sess = PicoSession(args.port, args.baud, raw_log)
    except Exception as exc:
        log("cannot open {}: {}".format(args.port, exc))
        sess = None
    if sess is not None:
        try:
            ensure_runner(sess)
            push_params(sess, params)
            result_doc, status = run_dose(sess, args.target_g,
                                          args.timeout_s)
            if result_doc is not None:
                telemetry = pull_telemetry(sess)
        except Exception as exc:
            log("dose attempt failed: {}".format(exc))
            status = "serial-error"
        finally:
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
