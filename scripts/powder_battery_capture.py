#!/usr/bin/env python3
"""Bench-host capture for the uniform powder test battery (issue #116).

Companion to ``hardware/test-module/firmware/powder_battery.py``.
Connects to the Pico over USB serial, starts the battery for the named
powder, relays operator keyboard input to the Pico's prompts (attended
mode), and records every line the run emits.  When the run ends it
writes, under ``--out`` (``<id>`` is the required ``--powder-id``,
e.g. ``brown-rice-flour``):

    raw_serial_<id>.log   every serial line, verbatim
    trials_<id>.csv       one row per measured action (all blocks)
    polls_<id>.csv        streamed scale polls from the speed sweep
    doses_<id>.csv        one row per three-phase closed-loop dose
    summary_<id>.csv      per-(block, tilt, phase) statistics
    run_<id>.json         the complete run document

With ``--upload`` the run document is inserted into MongoDB Atlas
(``powder_doser.battery_runs`` -- same database as issue #126, its own
collection so uniform-battery data never mixes with sweep or
optimization data).  Runs recorded offline can be backfilled later
with ``--upload-file path/to/run_<id>.json``.

Usage (attended, at the bench)::

    python scripts/powder_battery_capture.py --port /dev/ttyACM0 \
        --powder-id brown-rice-flour --operator cr --upload

Unattended (e.g. driven remotely over Tailscale SSH; every operator
prompt auto-continues, stall prompts auto-answer ``keep``)::

    python scripts/powder_battery_capture.py --port /dev/ttyACM0 \
        --powder-id brown-rice-flour --unattended --upload

Dependencies: ``pyserial`` (capture), ``pymongo`` (only for --upload).
The MongoDB connection string is read from the ``MONGODB_URI``
environment variable -- never passed on the command line, never
printed.
"""

import argparse
import csv
import datetime
import json
import math
import os
import re
import subprocess
import sys
import threading
import time

# Serial-stream contract (what the Pico emits) -- no powder_id here.
TRIAL_FIELDS = ["block", "tilt_deg", "phase", "trial", "action", "rpm",
                "before_g", "after_g", "delta_g", "flag", "t_ms"]
POLL_FIELDS = ["block", "tilt_deg", "rpm", "t_ms", "grams", "stable"]
DOSE_FIELDS = ["n", "target_g", "dispensed_g", "error_g", "status",
               "elapsed_s", "auger_rev", "taps", "phase_cycles", "t_ms"]
SUMMARY_FIELDS = ["block", "tilt_deg", "phase", "n", "mean_g", "std_g",
                  "sem_g", "min_g", "max_g", "rsd_pct"]
# CSV files on disk lead every row with the powder ID so a file stays
# attributable after it is copied out of its run directory.
OUT_TRIAL_FIELDS = ["powder_id"] + TRIAL_FIELDS
OUT_POLL_FIELDS = ["powder_id"] + POLL_FIELDS
OUT_DOSE_FIELDS = ["powder_id"] + DOSE_FIELDS
OUT_SUMMARY_FIELDS = ["powder_id"] + SUMMARY_FIELDS
SCHEMA_VERSION = 1


def normalize_powder_id(value):
    """Validate/normalize a powder ID into a filesystem-safe slug."""
    slug = (value or "").strip().lower().replace(" ", "-")
    if not re.match(r"^[a-z0-9][a-z0-9._-]*$", slug):
        raise ValueError(
            "invalid powder id {!r}: use letters/digits/dash/underscore/"
            "dot, e.g. salt, xanthan, brown-rice-flour".format(value))
    return slug


# ---------------------------------------------------------------------------
# Parsing -- pure functions over the serial line stream (unit-tested in
# scripts/tests/test_powder_battery_capture.py).
# ---------------------------------------------------------------------------

def _float_or_none(text):
    return float(text) if text else None


def parse_line(line):
    """Classify one serial line -> (kind, payload) or None.

    kinds: ``trial`` (dict), ``poll`` (dict), ``dose`` (dict),
    ``device_summary`` (dict), ``meta`` ((key, value)), ``run``
    (marker list), ``prompt`` (message).
    """
    line = line.strip()
    if line.startswith("CSV,"):
        parts = line.split(",")
        if len(parts) != len(TRIAL_FIELDS) + 1:
            return None
        row = dict(zip(TRIAL_FIELDS, parts[1:]))
        row["tilt_deg"] = float(row["tilt_deg"])
        for key in ("before_g", "after_g", "delta_g"):
            row[key] = _float_or_none(row[key])
        row["rpm"] = _float_or_none(row["rpm"])
        row["trial"] = int(row["trial"])
        row["t_ms"] = int(row["t_ms"])
        return "trial", row
    if line.startswith("POLL,"):
        parts = line.split(",")
        if len(parts) != len(POLL_FIELDS) + 1:
            return None
        row = dict(zip(POLL_FIELDS, parts[1:]))
        row["tilt_deg"] = float(row["tilt_deg"])
        row["rpm"] = float(row["rpm"])
        row["t_ms"] = int(row["t_ms"])
        row["grams"] = _float_or_none(row["grams"])
        row["stable"] = int(row["stable"])
        return "poll", row
    if line.startswith("DOSE,"):
        parts = line.split(",")
        if len(parts) != len(DOSE_FIELDS) + 1:
            return None
        row = dict(zip(DOSE_FIELDS, parts[1:]))
        row["n"] = int(row["n"])
        for key in ("target_g", "dispensed_g", "error_g"):
            row[key] = _float_or_none(row[key])
        row["elapsed_s"] = float(row["elapsed_s"])
        row["auger_rev"] = float(row["auger_rev"])
        row["taps"] = int(row["taps"])
        row["t_ms"] = int(row["t_ms"])
        return "dose", row
    if line.startswith("SUM,"):
        parts = line.split(",")
        if len(parts) != 10:
            return None
        keys = ["block", "tilt_deg", "phase", "n", "mean_g", "std_g",
                "sem_g", "min_g", "max_g"]
        row = dict(zip(keys, parts[1:]))
        row["tilt_deg"] = float(row["tilt_deg"])
        row["n"] = int(row["n"])
        for key in ("mean_g", "std_g", "sem_g", "min_g", "max_g"):
            row[key] = _float_or_none(row[key])
        return "device_summary", row
    if line.startswith("META,"):
        _, key, value = line.split(",", 2)
        return "meta", (key, value)
    if line.startswith("RUN,"):
        return "run", line.split(",", 2)[1:]
    if line.startswith("PROMPT,"):
        return "prompt", line.split(",", 1)[1]
    return None


def sample_stats(values):
    """(n, mean, std, sem, min, max); std/sem None for n < 2."""
    n = len(values)
    if n == 0:
        return 0, None, None, None, None, None
    mean = sum(values) / n
    if n > 1:
        var = sum((v - mean) ** 2 for v in values) / (n - 1)
        std = math.sqrt(var)
        sem = std / math.sqrt(n)
    else:
        std = sem = None
    return n, mean, std, sem, min(values), max(values)


def summarize(trials):
    """Host-side per-(block, tilt, phase) statistics over all trials.

    Low-flow rows are data in this battery (cohesive powders refusing
    to move IS the behaviour under test), so nothing is excluded; the
    ``flag`` column in trials.csv marks them for downstream filtering.
    """
    groups = {}
    for row in trials:
        key = (row["block"], row["tilt_deg"], row["phase"])
        groups.setdefault(key, []).append(row["delta_g"])
    out = []
    for (block, tilt, phase) in sorted(groups):
        n, mean, std, sem, lo, hi = sample_stats(
            groups[(block, tilt, phase)])
        rsd = (100.0 * std / abs(mean)
               if std is not None and mean else None)
        out.append({"block": block, "tilt_deg": tilt, "phase": phase,
                    "n": n, "mean_g": mean, "std_g": std, "sem_g": sem,
                    "min_g": lo, "max_g": hi, "rsd_pct": rsd})
    return out


def dose_summary(doses):
    """Aggregate accuracy/speed over the closed-loop doses."""
    if not doses:
        return None
    errors = [d["error_g"] for d in doses if d["error_g"] is not None]
    times = [d["elapsed_s"] for d in doses]
    n, mean_err, std_err, _, lo, hi = sample_stats(errors)
    return {
        "n": len(doses),
        "ok": sum(1 for d in doses if d["status"] == "ok"),
        "mean_error_g": mean_err,
        "std_error_g": std_err,
        "max_abs_error_g": max(abs(e) for e in errors) if errors else None,
        "mean_elapsed_s": sum(times) / len(times) if times else None,
    }


def build_run_document(meta, trials, polls, doses, device_summaries,
                       host_summary, status, args, started_utc,
                       ended_utc):
    """One self-contained document per run (issue #126 shape)."""
    try:
        git_commit = subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=os.path.dirname(os.path.abspath(__file__)),
            stderr=subprocess.DEVNULL).decode().strip()
    except Exception:
        git_commit = None
    preflight = None
    if getattr(args, "preflight_json", None):
        with open(args.preflight_json) as handle:
            preflight = json.load(handle)
    qc = {
        # Default to excluding a run: a battery is only comparable across
        # powders once someone has confirmed the rig actually fed.
        "valid_for_cross_powder_comparison": bool(
            getattr(args, "qc_valid", False)),
        "verdict": getattr(args, "qc_verdict", None) or "unreviewed",
    }
    if preflight is not None:
        qc["preflight_verdict"] = preflight.get("verdict")
    return {
        "kind": "battery_run",
        "schema_version": SCHEMA_VERSION,
        "status": status,
        "started_utc": started_utc,
        "ended_utc": ended_utc,
        "powder_id": args.powder_id,
        "powder": args.powder,
        "batch": getattr(args, "batch", None),
        "operator": args.operator,
        "notes": args.notes,
        "qc": qc,
        "preflight": preflight,
        "git_commit": git_commit,
        "parameters": meta,
        "trials": trials,
        "polls": polls,
        "doses": doses,
        "dose_summary": dose_summary(doses),
        "device_summary": device_summaries,
        "host_summary": host_summary,
    }


# ---------------------------------------------------------------------------
# Capture
# ---------------------------------------------------------------------------

def start_battery(port, extra=""):
    """Interrupt main.py's REPL loop and launch the battery."""
    port.write(b"\x03\x03")          # KeyboardInterrupt -> >>> prompt
    time.sleep(1.0)
    port.reset_input_buffer()
    port.write(b"import powder_battery\r\n")
    time.sleep(0.5)
    port.write("powder_battery.run({})\r\n".format(extra).encode())


def stdin_relay(port, stop):
    """Forward operator keyboard lines to the Pico (prompt answers)."""
    while not stop.is_set():
        line = sys.stdin.readline()
        if not line:
            return
        port.write(line.rstrip("\n").encode() + b"\r\n")


def capture(args):
    import serial                    # pip install pyserial

    out_dir = os.path.join(
        args.out, "{}_{}".format(
            datetime.datetime.now(datetime.timezone.utc)
            .strftime("%Y%m%dT%H%M%SZ"),
            args.powder_id))
    os.makedirs(out_dir, exist_ok=True)
    started_utc = datetime.datetime.now(
        datetime.timezone.utc).isoformat()

    port = serial.Serial(args.port, args.baud, timeout=1)
    stop = threading.Event()
    if not args.unattended:
        relay = threading.Thread(target=stdin_relay, args=(port, stop),
                                 daemon=True)
        relay.start()

    meta, trials, polls, doses, device_summaries = {}, [], [], [], []
    status = "incomplete"
    raw_path = os.path.join(
        out_dir, "raw_serial_{}.log".format(args.powder_id))
    print("[capture] writing to {}".format(out_dir))
    if args.unattended:
        print("[capture] UNATTENDED run -- prompts auto-continue on the "
              "device; Ctrl+C stops the capture")
    else:
        print("[capture] answer Pico prompts here (Enter / keep / skip / "
              "abort); Ctrl+C stops the capture")
    try:
        with open(raw_path, "w") as raw:
            if not args.no_start:
                run_args = "powder_id={!r}, attended={}".format(
                    args.powder_id, not args.unattended)
                if args.run_args:
                    run_args += ", " + args.run_args
                start_battery(port, run_args)
            while True:
                line = port.readline().decode(errors="replace")
                if not line:
                    continue
                raw.write(line)
                raw.flush()
                print(line.rstrip())
                parsed = parse_line(line)
                if parsed is None:
                    continue
                kind, payload = parsed
                if kind == "trial":
                    trials.append(payload)
                elif kind == "poll":
                    polls.append(payload)
                elif kind == "dose":
                    doses.append(payload)
                elif kind == "device_summary":
                    device_summaries.append(payload)
                elif kind == "meta":
                    meta[payload[0]] = payload[1]
                elif kind == "run" and payload[0] == "END":
                    status = payload[1] if len(payload) > 1 else "ok"
                    break
    except KeyboardInterrupt:
        print("\n[capture] interrupted -- saving partial run")
        status = "capture-interrupted"
    finally:
        stop.set()
        port.close()

    ended_utc = datetime.datetime.now(datetime.timezone.utc).isoformat()
    host_summary = summarize(trials)
    doc = build_run_document(meta, trials, polls, doses,
                             device_summaries, host_summary, status,
                             args, started_utc, ended_utc)

    write_outputs(out_dir, args.powder_id, trials, polls, doses,
                  host_summary, doc)
    print_summary(host_summary, doses)
    if args.upload:
        upload(doc, args)
    return doc


def write_outputs(out_dir, powder_id, trials, polls, doses,
                  host_summary, doc):
    def write_csv(stem, fields, rows):
        path = os.path.join(
            out_dir, "{}_{}.csv".format(stem, powder_id))
        with open(path, "w", newline="") as fh:
            writer = csv.DictWriter(fh, fieldnames=fields)
            writer.writeheader()
            writer.writerows(dict(row, powder_id=powder_id)
                             for row in rows)

    write_csv("trials", OUT_TRIAL_FIELDS, trials)
    write_csv("polls", OUT_POLL_FIELDS, polls)
    write_csv("doses", OUT_DOSE_FIELDS, doses)
    write_csv("summary", OUT_SUMMARY_FIELDS, host_summary)
    with open(os.path.join(
            out_dir, "run_{}.json".format(powder_id)), "w") as fh:
        json.dump(doc, fh, indent=2)
    print("[capture] wrote trials_{0}.csv, polls_{0}.csv, doses_{0}.csv, "
          "summary_{0}.csv, run_{0}.json".format(powder_id))


def print_summary(host_summary, doses):
    header = "{:>5} {:>8} {:>10} {:>4} {:>10} {:>10} {:>10} {:>7}".format(
        "block", "tilt", "phase", "n", "mean_g", "std_g", "sem_g", "rsd%")
    print(header)
    for row in host_summary:
        print("{:>5} {:>8.1f} {:>10} {:>4} {:>10} {:>10} {:>10} {:>7}"
              .format(
                  row["block"], row["tilt_deg"], row["phase"], row["n"],
                  *["{:.4f}".format(row[k]) if row[k] is not None else "-"
                    for k in ("mean_g", "std_g", "sem_g")],
                  "{:.1f}".format(row["rsd_pct"])
                  if row["rsd_pct"] is not None else "-"))
    for dose in doses:
        print("dose {}: {} {:.4f}/{:.4f} g ({:+.4f} g) in {:.1f} s, "
              "{} taps, cycles {}".format(
                  dose["n"], dose["status"], dose["dispensed_g"],
                  dose["target_g"], dose["error_g"], dose["elapsed_s"],
                  dose["taps"], dose["phase_cycles"]))


# ---------------------------------------------------------------------------
# Upload (issue #126: MongoDB Atlas, one document per run)
# ---------------------------------------------------------------------------

def upload(doc, args):
    uri = os.environ.get(args.uri_env)
    if not uri:
        print("[upload] {} is not set -- skipping upload.  The run is "
              "saved locally; backfill later with --upload-file"
              .format(args.uri_env))
        return False
    try:
        from pymongo import MongoClient   # pip install pymongo
    except ImportError:
        print("[upload] pymongo not installed (pip install pymongo) -- "
              "skipping upload; backfill later with --upload-file")
        return False
    client = MongoClient(uri, serverSelectionTimeoutMS=15000)
    result = client[args.db][args.collection].insert_one(doc)
    print("[upload] inserted into {}.{} as {}".format(
        args.db, args.collection, result.inserted_id))
    return True


def main(argv=None):
    parser = argparse.ArgumentParser(
        description=__doc__.split("\n", 1)[0],
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--port", default="/dev/ttyACM0",
                        help="Pico USB-CDC serial port (COMx on Windows)")
    parser.add_argument("--baud", type=int, default=115200,
                        help="ignored by USB-CDC but required by pyserial")
    parser.add_argument("--out", default="data/battery",
                        help="output directory root")
    parser.add_argument("--powder-id", default=None,
                        help="short powder identifier stamped on every "
                        "file name, CSV row, and the run document "
                        "(e.g. salt, xanthan, brown-rice-flour); "
                        "required unless --upload-file")
    parser.add_argument("--powder", default=None,
                        help="free-form powder description (provenance)")
    parser.add_argument("--operator", default=None,
                        help="operator initials (provenance)")
    parser.add_argument("--notes", default=None,
                        help="free-form run notes (provenance)")
    parser.add_argument("--batch", default=None,
                        help="powder batch label shared by runs that came "
                        "out of the same fill container "
                        "(e.g. food-safe-2026-08)")
    parser.add_argument("--preflight-json", default=None, metavar="JSON",
                        help="pre-flight feed check result to embed "
                        "(from battery_preflight / battery_feed_diagnostic)")
    parser.add_argument("--qc-valid", action="store_true",
                        help="mark the run valid for cross-powder "
                        "comparison; runs are excluded by default")
    parser.add_argument("--qc-verdict", default=None,
                        help="short QC verdict string, e.g. ok, "
                        "suspect-no-feed, cohesive-no-flow")
    parser.add_argument("--unattended", action="store_true",
                        help="run without an operator: device prompts "
                        "auto-continue (stall prompts answer 'keep')")
    parser.add_argument("--no-start", action="store_true",
                        help="don't auto-start; battery already running")
    parser.add_argument("--run-args", default="",
                        help="keyword overrides forwarded to "
                        "powder_battery.run(), e.g. "
                        "'blocks=\"CG\", dose_repeats=1'")
    parser.add_argument("--upload", action="store_true",
                        help="insert run.json into MongoDB after capture")
    parser.add_argument("--upload-file", default=None, metavar="RUN_JSON",
                        help="upload an existing run.json and exit")
    parser.add_argument("--db", default="powder_doser")
    parser.add_argument("--collection", default="battery_runs")
    parser.add_argument("--uri-env", default="MONGODB_URI",
                        help="env var holding the MongoDB connection string")
    args = parser.parse_args(argv)

    if args.powder_id is not None:
        try:
            args.powder_id = normalize_powder_id(args.powder_id)
        except ValueError as exc:
            parser.error(str(exc))

    if args.upload_file:
        with open(args.upload_file) as fh:
            doc = json.load(fh)
        if not doc.get("powder_id"):
            if not args.powder_id:
                parser.error("{} has no powder_id -- re-run with "
                             "--powder-id <id>".format(args.upload_file))
            doc["powder_id"] = args.powder_id
        return 0 if upload(doc, args) else 1

    if not args.powder_id:
        parser.error("--powder-id is required "
                     "(e.g. --powder-id brown-rice-flour)")
    capture(args)
    return 0


if __name__ == "__main__":
    sys.exit(main())
