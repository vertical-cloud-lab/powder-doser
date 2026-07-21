#!/usr/bin/env python3
"""Bench-host capture for the powder-doser characterization sweep.

Companion to ``hardware/test-module/firmware/characterize.py`` (issue
#130).  Connects to the Pico W over USB serial, starts the sweep,
relays the operator's keyboard to the Pico's prompts (empty the cup /
refill the hopper), and records every line the sweep emits.  When the
run ends it writes, under ``--out/<powder-id>_<UTC-stamp>/``:

    <powder-id>_<stamp>_raw_serial.log  every serial line, verbatim
    <powder-id>_<stamp>_trials.csv      one row per measured action
    <powder-id>_<stamp>_summary.csv     per-angle host statistics
    <powder-id>_<stamp>_run.json        the run document (issue #126)

and, with ``--upload``, inserts ``run.json`` into MongoDB (Atlas), the
storage plan from issue #126.  Successful uploads leave a
``.uploaded`` marker beside the run.json; runs recorded offline (or
whose upload failed) are backfilled idempotently with
``--upload-missing`` -- safe to run from cron on the Pi Zero.

Every output carries the **powder ID** (``--powder-id``, e.g. ``salt``,
``xanthan``, ``flour``): it is the first token of the run directory and
of every filename, a ``powder_id`` column in both CSVs, and a
``powder_id`` field in the run document -- so a file identifies its
powder even after being copied out of its directory.

Usage::

    python scripts/characterize_capture.py --port /dev/ttyACM0 \
        --powder-id xanthan --powder "xanthan gum, lot 240515" \
        --operator wm [--upload]

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
# CSVs on disk carry the powder ID in every row, so a file stays
# self-describing after being copied off the capture host.
OUT_TRIAL_FIELDS = ["powder_id"] + TRIAL_FIELDS
OUT_SUMMARY_FIELDS = ["powder_id"] + SUMMARY_FIELDS
SCHEMA_VERSION = 2                   # v2: adds powder_id


def normalize_powder_id(raw):
    """Slugify a powder ID: 'Xanthan Gum' -> 'xanthan-gum'.

    Raises ValueError when nothing usable remains, so a typo'd ID
    fails the run up front instead of producing anonymous files.
    """
    slug = "-".join((raw or "").strip().lower().split())
    slug = "".join(c for c in slug if c.isalnum() or c in "-_")
    if not slug or not slug.strip("-_"):
        raise ValueError("unusable powder id: {!r}".format(raw))
    return slug


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
        "powder_id": args.powder_id,
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

    base = "{}_{}".format(
        args.powder_id,
        datetime.datetime.now(datetime.timezone.utc)
        .strftime("%Y%m%dT%H%M%SZ"))
    out_dir = os.path.join(args.out, base)
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
    raw_path = os.path.join(out_dir, base + "_raw_serial.log")
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

    run_path = write_outputs(out_dir, base, args.powder_id,
                             trials, host_summary, doc)
    print_summary(host_summary)
    if args.upload:
        upload(doc, args, marker_for=run_path)
    return doc


def write_outputs(out_dir, base, powder_id, trials, host_summary, doc):
    """Write the three data files, each named and stamped with the
    powder ID; returns the run.json path (for the upload marker)."""
    trials_path = os.path.join(out_dir, base + "_trials.csv")
    with open(trials_path, "w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=OUT_TRIAL_FIELDS)
        writer.writeheader()
        writer.writerows(dict(row, powder_id=powder_id) for row in trials)
    with open(os.path.join(out_dir, base + "_summary.csv"),
              "w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=OUT_SUMMARY_FIELDS)
        writer.writeheader()
        writer.writerows(dict(row, powder_id=powder_id)
                         for row in host_summary)
    run_path = os.path.join(out_dir, base + "_run.json")
    with open(run_path, "w") as fh:
        json.dump(doc, fh, indent=2)
    print("[capture] wrote {}_{{trials.csv,summary.csv,run.json}}"
          .format(os.path.join(out_dir, base)))
    return run_path


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

def upload(doc, args, marker_for=None):
    """Insert one run document; on success drop a ``.uploaded`` marker
    next to the run.json so backfill sweeps never double-insert."""
    uri = os.environ.get(args.uri_env)
    if not uri:
        print("[upload] {} is not set -- skipping upload.  The run is "
              "saved locally; backfill later with --upload-missing"
              .format(args.uri_env))
        return False
    try:
        from pymongo import MongoClient   # pip install pymongo
    except ImportError:
        print("[upload] pymongo not installed (pip install pymongo) -- "
              "skipping upload; backfill later with --upload-missing")
        return False
    try:
        client = MongoClient(uri, serverSelectionTimeoutMS=15000)
        result = client[args.db][args.collection].insert_one(doc)
    except Exception as exc:
        print("[upload] failed ({}) -- the run is saved locally; "
              "backfill later with --upload-missing".format(exc))
        return False
    print("[upload] inserted into {}.{} as {}".format(
        args.db, args.collection, result.inserted_id))
    if marker_for:
        with open(marker_for + ".uploaded", "w") as fh:
            json.dump({"inserted_id": str(result.inserted_id),
                       "db": args.db, "collection": args.collection,
                       "uploaded_utc": datetime.datetime.now(
                           datetime.timezone.utc).isoformat()}, fh)
    return True


def find_unuploaded(root):
    """All ``*run.json`` under ``root`` without an ``.uploaded`` marker."""
    missing = []
    for dirpath, _, filenames in os.walk(root):
        for name in sorted(filenames):
            if (name.endswith("run.json")
                    and name + ".uploaded" not in filenames):
                missing.append(os.path.join(dirpath, name))
    return sorted(missing)


def upload_missing(args):
    """Sweep ``--out`` for runs never uploaded (offline captures,
    upload failures) and push them.  Idempotent -- safe from cron."""
    pending = find_unuploaded(args.out)
    if not pending:
        print("[upload] nothing pending under {}".format(args.out))
        return True
    ok = True
    for path in pending:
        print("[upload] backfilling {}".format(path))
        with open(path) as fh:
            doc = json.load(fh)
        ok = upload(doc, args, marker_for=path) and ok
    return ok


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
    parser.add_argument("--powder-id", default=None,
                        help="short powder identifier stamped into the run "
                        "directory, every filename, both CSVs, and the run "
                        "document (e.g. salt, xanthan, flour); required "
                        "for capture")
    parser.add_argument("--powder", default=None,
                        help="free-form powder description (provenance, "
                        "e.g. 'xanthan gum, lot 240515')")
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
    parser.add_argument("--upload-missing", action="store_true",
                        help="upload every run.json under --out that has "
                        "no .uploaded marker, then exit (idempotent; "
                        "cron-friendly)")
    parser.add_argument("--db", default="powder_doser")
    parser.add_argument("--collection", default="characterization_runs")
    parser.add_argument("--uri-env", default="MONGODB_URI",
                        help="env var holding the MongoDB connection string")
    args = parser.parse_args(argv)

    if args.upload_file:
        with open(args.upload_file) as fh:
            doc = json.load(fh)
        return 0 if upload(doc, args, marker_for=args.upload_file) else 1
    if args.upload_missing:
        return 0 if upload_missing(args) else 1

    if not args.powder_id:
        parser.error("--powder-id is required for capture "
                     "(e.g. --powder-id salt)")
    try:
        args.powder_id = normalize_powder_id(args.powder_id)
    except ValueError as exc:
        parser.error(str(exc))
    capture(args)
    return 0


if __name__ == "__main__":
    sys.exit(main())
