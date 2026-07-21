#!/usr/bin/env python3
"""Bench-host capture for the powder-doser characterization sweep.

Companion to ``hardware/test-module/firmware/characterize.py`` (issue
#130).  Connects to the Pico W over USB serial, starts the sweep,
relays the operator's keyboard to the Pico's prompts (empty the cup /
refill the hopper), and records every line the sweep emits.  When the
run ends it writes, under ``--out``:

    raw_serial.log   every serial line, verbatim
    trials.csv       one row per measured action (all phases, flags kept)
    summary.csv      per-angle statistics recomputed on the host
    run.json         the complete run document (issue #126 shape)

and, with ``--upload``, inserts ``run.json`` into MongoDB (Atlas), the
storage plan from issue #126.  Runs recorded offline can be backfilled
later with ``--upload-file path/to/run.json``.

Usage::

    python scripts/characterize_capture.py --port /dev/ttyACM0 \
        --powder "xanthan gum" --operator wm [--upload]

Host statistics: for every (angle, phase) the mean, sample standard
deviation (n-1), standard error of the mean, min, max, and n are
computed over rows not flagged ``lowflow``; ``rotation`` and ``refeed``
rows are additionally pooled into a ``rotation+refeed`` set (both are
the same auger action when ``REFEED_DEG == ROTATION_STEP_DEG``), and
the ``baseline`` phase's spread is the scale noise/drift floor.

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
import subprocess
import sys
import threading
import time

TRIAL_FIELDS = ["angle_deg", "phase", "trial", "action",
                "before_g", "after_g", "delta_g", "flag", "t_ms"]
SUMMARY_FIELDS = ["angle_deg", "phase", "n", "mean_g", "std_g", "sem_g",
                  "min_g", "max_g", "rsd_pct"]
SCHEMA_VERSION = 1


# ---------------------------------------------------------------------------
# Parsing -- pure functions over the serial line stream (unit-tested in
# scripts/tests/test_characterize_capture.py).
# ---------------------------------------------------------------------------

def parse_line(line):
    """Classify one serial line -> (kind, payload) or None.

    kinds: ``trial`` (dict), ``device_summary`` (dict), ``meta``
    ((key, value)), ``run`` (marker string), ``prompt`` (message).
    """
    line = line.strip()
    if line.startswith("CSV,"):
        parts = line.split(",")
        if len(parts) != len(TRIAL_FIELDS) + 1:
            return None
        row = dict(zip(TRIAL_FIELDS, parts[1:]))
        for key in ("angle_deg", "before_g", "after_g", "delta_g"):
            row[key] = float(row[key]) if row[key] else None
        row["trial"] = int(row["trial"])
        row["t_ms"] = int(row["t_ms"])
        return "trial", row
    if line.startswith("SUM,"):
        parts = line.split(",")
        if len(parts) != 9:
            return None
        keys = ["angle_deg", "phase", "n", "mean_g", "std_g", "sem_g",
                "min_g", "max_g"]
        row = dict(zip(keys, parts[1:]))
        row["angle_deg"] = float(row["angle_deg"])
        row["n"] = int(row["n"])
        for key in ("mean_g", "std_g", "sem_g", "min_g", "max_g"):
            row[key] = float(row[key]) if row[key] else None
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
    """Host-side per-(angle, phase) statistics over unflagged trials.

    Adds a pooled ``rotation+refeed`` phase per angle (same auger
    action, so re-feed rows are free extra rotation data points) and a
    relative standard deviation column.
    """
    groups = {}
    for row in trials:
        if row["flag"]:
            continue        # lowflow rows are kept in trials.csv only
        key = (row["angle_deg"], row["phase"])
        groups.setdefault(key, []).append(row["delta_g"])
        if row["phase"] in ("rotation", "refeed"):
            pooled = (row["angle_deg"], "rotation+refeed")
            groups.setdefault(pooled, []).append(row["delta_g"])
    out = []
    for (angle, phase) in sorted(groups):
        n, mean, std, sem, lo, hi = sample_stats(groups[(angle, phase)])
        rsd = (100.0 * std / abs(mean)
               if std is not None and mean else None)
        out.append({"angle_deg": angle, "phase": phase, "n": n,
                    "mean_g": mean, "std_g": std, "sem_g": sem,
                    "min_g": lo, "max_g": hi, "rsd_pct": rsd})
    return out


def build_run_document(meta, trials, device_summaries, host_summary,
                       status, args, started_utc, ended_utc):
    """One self-contained document per run -- the issue #126 shape:
    raw data + derived statistics + full provenance in a single record.
    """
    try:
        git_commit = subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=os.path.dirname(os.path.abspath(__file__)),
            stderr=subprocess.DEVNULL).decode().strip()
    except Exception:
        git_commit = None
    return {
        "kind": "characterization_run",
        "schema_version": SCHEMA_VERSION,
        "status": status,
        "started_utc": started_utc,
        "ended_utc": ended_utc,
        "powder": args.powder,
        "operator": args.operator,
        "notes": args.notes,
        "git_commit": git_commit,
        "parameters": meta,
        "trials": trials,
        "device_summary": device_summaries,
        "host_summary": host_summary,
    }


# ---------------------------------------------------------------------------
# Capture
# ---------------------------------------------------------------------------

def start_sweep(port, extra=""):
    """Interrupt main.py's REPL loop and launch the sweep."""
    port.write(b"\x03\x03")          # KeyboardInterrupt -> >>> prompt
    time.sleep(1.0)
    port.reset_input_buffer()
    port.write(b"import characterize\r\n")
    time.sleep(0.5)
    port.write("characterize.run({})\r\n".format(extra).encode())


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
            (args.powder or "powder").replace(" ", "-")))
    os.makedirs(out_dir, exist_ok=True)
    started_utc = datetime.datetime.now(
        datetime.timezone.utc).isoformat()

    port = serial.Serial(args.port, args.baud, timeout=1)
    stop = threading.Event()
    relay = threading.Thread(target=stdin_relay, args=(port, stop),
                             daemon=True)
    relay.start()

    meta, trials, device_summaries = {}, [], []
    status = "incomplete"
    raw_path = os.path.join(out_dir, "raw_serial.log")
    print("[capture] writing to {}".format(out_dir))
    print("[capture] answer Pico prompts here (Enter / keep / skip / "
          "abort); Ctrl+C stops the capture")
    try:
        with open(raw_path, "w") as raw:
            if not args.no_start:
                start_sweep(port, args.run_args)
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
    doc = build_run_document(meta, trials, device_summaries, host_summary,
                             status, args, started_utc, ended_utc)

    write_outputs(out_dir, trials, host_summary, doc)
    print_summary(host_summary)
    if args.upload:
        upload(doc, args)
    return doc


def write_outputs(out_dir, trials, host_summary, doc):
    with open(os.path.join(out_dir, "trials.csv"), "w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=TRIAL_FIELDS)
        writer.writeheader()
        writer.writerows(trials)
    with open(os.path.join(out_dir, "summary.csv"), "w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=SUMMARY_FIELDS)
        writer.writeheader()
        writer.writerows(host_summary)
    with open(os.path.join(out_dir, "run.json"), "w") as fh:
        json.dump(doc, fh, indent=2)
    print("[capture] wrote trials.csv, summary.csv, run.json")


def print_summary(host_summary):
    header = "{:>9} {:>16} {:>4} {:>10} {:>10} {:>10} {:>7}".format(
        "angle", "phase", "n", "mean_g", "std_g", "sem_g", "rsd%")
    print(header)
    for row in host_summary:
        print("{:>9.1f} {:>16} {:>4} {:>10} {:>10} {:>10} {:>7}".format(
            row["angle_deg"], row["phase"], row["n"],
            *["{:.4f}".format(row[k]) if row[k] is not None else "-"
              for k in ("mean_g", "std_g", "sem_g")],
            "{:.1f}".format(row["rsd_pct"])
            if row["rsd_pct"] is not None else "-"))


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
    parser.add_argument("--out", default="data/characterization",
                        help="output directory root")
    parser.add_argument("--powder", default=None,
                        help="powder name (provenance, e.g. 'xanthan gum')")
    parser.add_argument("--operator", default=None,
                        help="operator initials (provenance)")
    parser.add_argument("--notes", default=None,
                        help="free-form run notes (provenance)")
    parser.add_argument("--no-start", action="store_true",
                        help="don't auto-start; sweep already running")
    parser.add_argument("--run-args", default="",
                        help="keyword overrides forwarded to "
                        "characterize.run(), e.g. "
                        "'points_per_angle=10, angles_deg=[30,60]'")
    parser.add_argument("--upload", action="store_true",
                        help="insert run.json into MongoDB after capture")
    parser.add_argument("--upload-file", default=None, metavar="RUN_JSON",
                        help="upload an existing run.json and exit")
    parser.add_argument("--db", default="powder_doser")
    parser.add_argument("--collection", default="characterization_runs")
    parser.add_argument("--uri-env", default="MONGODB_URI",
                        help="env var holding the MongoDB connection string")
    args = parser.parse_args(argv)

    if args.upload_file:
        with open(args.upload_file) as fh:
            doc = json.load(fh)
        return 0 if upload(doc, args) else 1

    capture(args)
    return 0


if __name__ == "__main__":
    sys.exit(main())
