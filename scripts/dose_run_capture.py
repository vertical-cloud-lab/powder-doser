#!/usr/bin/env python3
"""Turn a dose-run device stream into one canonical MongoDB document.

Companion to ``scripts/characterize_capture.py`` (characterization
sweeps, issue #130); this one covers the *dose* path (issue #126).  It
consumes the line protocol that
``hardware/test-module/firmware/pid_dose.py`` emits --

    M,<key>,<value>                                        (metadata)
    D,<t_ms>,<mass_g>,<S|U|X>,<tilt_deg>,<rpm_cmd>,<taps_cum>,<phase>
    E,<t_ms>,<event text>
    SUMMARY,status=...,final_g=...,target_g=...,taps=...

-- and emits **one document per dose run**: the full in-dose time
series stored columnwise, the events, the summary, and provenance
(git commit + dirty flag, controller gains, powder, operator, device).
That is tier 1 of ``docs/data-streaming-design.md``: storage scales
with doses performed rather than wall-clock time.

Live capture (the run and the upload in one pipe, so nothing depends
on an agent hand-assembling a document afterwards)::

    mpremote connect /dev/ttyACM0 run hardware/test-module/firmware/pid_dose.py \
        | tee data/pid-dose/2026-07-31_salt/raw_run1.log \
        | python scripts/dose_run_capture.py - --powder-id salt \
              --operator wm --out data/pid-dose/2026-07-31_salt/run1.json --upload

Backfill of a log captured earlier::

    python scripts/dose_run_capture.py path/to/telemetry_run2_salt.log \
        --powder-id salt --started-utc 2026-07-29T20:52:00Z --upload

``--upload`` is idempotent: every document carries a ``run_uid``
(SHA-1 of the device stream) and is upserted on it, so re-running a
backfill updates rather than duplicates.  The connection string is
read from ``MONGODB_URI`` -- never passed on the command line, never
printed.

Reading from ``-`` (stdin) tees every line back to stdout, so the
operator still watches the run scroll by in real time.

Dependencies: stdlib for parsing (unit-tested in
``scripts/tests/test_dose_run_capture.py``); ``pymongo`` only for
``--upload`` / ``--ensure-indexes``.
"""

import argparse
import datetime
import hashlib
import json
import os
import subprocess
import sys

SCHEMA_VERSION = 1
DOC_TYPE = "dose_run"

# Device-stream contract (see pid_dose.py module docstring).
SAMPLE_FIELDS = ["t_ms", "mass_g", "frame", "tilt_deg", "rpm_cmd",
                 "taps_cum", "phase"]
# M,<key>,<value> keys that are numeric controller gains rather than
# free-form strings.  Anything else stays a string under ``meta``.
GAIN_KEYS = ["kp", "ki", "kd", "t_ant_s", "max_rpm", "tol_g",
             "target_g", "settle_ms"]


# ---------------------------------------------------------------------------
# Parsing -- pure functions over the device line stream.
# ---------------------------------------------------------------------------

def strip_wrapper(line):
    """Strip the decorations mpremote/REPL capture adds around a line.

    A raw device line arrives as ``D,140,1.9243,S,...``; the same line
    seen through a logged REPL session arrives as
    ``[   10.9s]   | D,140,...``.  Both must parse identically, so the
    optional ``[<elapsed>s]`` stamp, the ``| `` gutter, and any ``>>>``
    prompt are removed before classification.
    """
    text = line.rstrip("\r\n")
    if text.lstrip().startswith("["):
        close = text.find("]")
        if close != -1:
            text = text[close + 1:]
    text = text.lstrip()
    while text.startswith(">>>") or text.startswith("|"):
        text = text[3:].lstrip() if text.startswith(">>>") else text[1:].lstrip()
    return text.strip()


def _float(value):
    """Parse a float, mapping the device's ``nan`` placeholder to None.

    An ``X`` frame means the poll returned no usable reading; storing
    None (BSON null) keeps the sample's timestamp and actuator state
    while making the gap explicit, and keeps the document JSON-valid
    (JSON has no NaN literal).
    """
    if value is None:
        return None
    text = value.strip()
    if not text or text.lower() in ("nan", "none", "-"):
        return None
    return float(text)


def parse_line(line):
    """Classify one device line -> (kind, payload) or None.

    kinds: ``sample`` (dict), ``event`` ((t_ms, text)), ``meta``
    ((key, value)), ``summary`` (dict).  Unrecognized lines (banners,
    prompts, tracebacks) return None and are counted, not dropped
    silently -- see ``parse_stream``.
    """
    text = strip_wrapper(line)
    if text.startswith("D,"):
        parts = text.split(",")
        if len(parts) != len(SAMPLE_FIELDS) + 1:
            return None
        row = dict(zip(SAMPLE_FIELDS, parts[1:]))
        row["t_ms"] = int(row["t_ms"])
        row["mass_g"] = _float(row["mass_g"])
        for key in ("tilt_deg", "rpm_cmd"):
            row[key] = _float(row[key])
        row["taps_cum"] = int(row["taps_cum"])
        return "sample", row
    if text.startswith("E,"):
        parts = text.split(",", 2)
        if len(parts) != 3:
            return None
        return "event", (int(parts[1]), parts[2].strip())
    if text.startswith("M,"):
        parts = text.split(",", 2)
        if len(parts) != 3:
            return None
        return "meta", (parts[1].strip(), parts[2].strip())
    if text.startswith("SUMMARY,"):
        summary = {}
        for field in text[len("SUMMARY,"):].split(","):
            if "=" not in field:
                continue
            key, value = field.split("=", 1)
            summary[key.strip()] = value.strip()
        for key in ("final_g", "target_g"):
            if key in summary:
                summary[key] = _float(summary[key])
        if "taps" in summary:
            summary["taps"] = int(summary["taps"])
        return "summary", summary
    return None


def parse_stream(lines, tee=None):
    """Parse a whole device stream into its four parts.

    Returns ``{meta, samples, events, summary, device_lines,
    unparsed}``.  ``device_lines`` is the normalized (wrapper-stripped)
    protocol text, which is what ``run_uid`` hashes -- so the same run
    captured live and re-parsed from a logged REPL session yields the
    same identifier.
    """
    meta, samples, events, device_lines = {}, [], [], []
    summary, unparsed = None, 0
    for line in lines:
        if tee is not None:
            tee.write(line if line.endswith("\n") else line + "\n")
            tee.flush()
        parsed = parse_line(line)
        if parsed is None:
            if strip_wrapper(line):
                unparsed += 1
            continue
        kind, payload = parsed
        device_lines.append(strip_wrapper(line))
        if kind == "sample":
            samples.append(payload)
        elif kind == "event":
            events.append(payload)
        elif kind == "meta":
            meta[payload[0]] = payload[1]
        elif kind == "summary":
            summary = payload
    return {"meta": meta, "samples": samples, "events": events,
            "summary": summary, "device_lines": device_lines,
            "unparsed": unparsed}


# ---------------------------------------------------------------------------
# Document assembly
# ---------------------------------------------------------------------------

def encode_rle(values):
    """Run-length-encode a column as ``[[value, count], ...]``.

    Every column except ``t_ms`` is piecewise constant at the 10 Hz
    poll rate -- a real 4,450-sample run holds 121 distinct mass runs,
    31 tilt runs, and 5 phase runs, because the HR-100A repeats a
    reading until it changes.  RLE is therefore lossless *and* cuts
    that run's series from 267 KB of BSON to ~53 KB (the remaining
    cost is ``t_ms``, which is genuinely all-distinct).  See
    ``test_columnar_layout_beats_row_documents``.
    """
    runs = []
    for value in values:
        if runs and runs[-1][0] == value:
            runs[-1][1] += 1
        else:
            runs.append([value, 1])
    return runs


def decode_rle(runs):
    """Inverse of ``encode_rle``."""
    out = []
    for value, count in runs:
        out.extend([value] * count)
    return out


def encode_series(samples):
    """Columns for one run: ``t_ms`` verbatim, every value column RLE'd.

    The ``_rle`` suffix is the encoding marker, so ``decode_series``
    handles both forms and a column can switch encoding later without
    breaking readers of older documents.
    """
    series = {"t_ms": [s["t_ms"] for s in samples]}
    for field in SAMPLE_FIELDS:
        if field == "t_ms":
            continue
        series[field + "_rle"] = encode_rle([s[field] for s in samples])
    return series


def decode_series(series):
    """Inverse of ``encode_series`` -> ``{field: [values]}``."""
    out = {}
    for key, value in series.items():
        if key.endswith("_rle"):
            out[key[:-len("_rle")]] = decode_rle(value)
        else:
            out[key] = list(value)
    return out


def run_uid(device_lines):
    """Stable identifier for a run: SHA-1 of its device stream.

    The Pico has no real-time clock and its ``t_ms`` restarts every
    run, so nothing in the stream is globally unique on its own.
    Hashing the stream gives a dedupe key that survives re-uploads and
    backfills of the same log from a different machine.
    """
    digest = hashlib.sha1()
    for line in device_lines:
        digest.update(line.encode("utf-8"))
        digest.update(b"\n")
    return digest.hexdigest()


def git_provenance(root=None):
    """Commit hash + dirty flag for the checkout that ran the dose.

    Per the issue #126 discussion this stores the *pointer*, not the
    source: git is the archive.  ``dirty`` is the honest part -- a run
    made from an edited working tree is not reproducible from the hash
    alone and says so.
    """
    root = root or os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
    info = {"commit": None, "dirty": None}
    try:
        info["commit"] = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=root,
            stderr=subprocess.DEVNULL).decode().strip()
        info["dirty"] = bool(subprocess.check_output(
            ["git", "status", "--porcelain"], cwd=root,
            stderr=subprocess.DEVNULL).decode().strip())
    except (OSError, subprocess.CalledProcessError):
        pass
    return info


def split_meta(meta):
    """Split the device's ``M,`` rows into numeric gains and strings."""
    gains, rest = {}, {}
    for key, value in meta.items():
        if key in GAIN_KEYS:
            try:
                gains[key] = float(value)
                continue
            except ValueError:
                pass
        rest[key] = value
    return gains, rest


def build_run_document(parsed, powder_id=None, operator=None, notes=None,
                       started_utc=None, device=None, source=None,
                       provenance=None, extra=None):
    """Assemble the canonical one-document-per-dose record.

    The time series is stored **columnwise** (parallel arrays) rather
    than as one sub-document per sample: BSON repeats every key name
    in every sub-document, so seven keys x thousands of samples is
    mostly field names.  Columns + RLE cut a typical run to well under
    half the size with no loss.
    """
    samples = parsed["samples"]
    gains, meta_rest = split_meta(parsed["meta"])
    # Pop unconditionally so the device's row never lingers in ``meta``
    # once promoted; an explicit powder_id from the operator wins, since
    # the firmware's default is what gets forgotten between powders.
    device_powder = meta_rest.pop("powder_id", None)
    powder = powder_id or device_powder
    summary = dict(parsed["summary"] or {})

    target_g = summary.get("target_g", gains.get("target_g"))
    final_g = summary.get("final_g")
    if final_g is not None and target_g is not None:
        summary["error_mg"] = round((final_g - target_g) * 1000.0, 4)
        tol_g = gains.get("tol_g")
        if tol_g is not None:
            summary["within_tolerance"] = abs(final_g - target_g) <= tol_g

    doc = {
        "schema_version": SCHEMA_VERSION,
        "doc_type": DOC_TYPE,
        "run_uid": run_uid(parsed["device_lines"]),
        "powder_id": powder,
        "started_utc": started_utc,
        "operator": operator,
        "notes": notes,
        "controller": meta_rest.get("controller"),
        "gains": gains,
        "meta": meta_rest,
        "device": device or {},
        "provenance": dict(provenance or {}, source=source),
        "summary": summary,
        "n_samples": len(samples),
        "duration_s": (samples[-1]["t_ms"] - samples[0]["t_ms"]) / 1000.0
                      if samples else None,
        "series": encode_series(samples),
        "events": [{"t_ms": t, "text": text} for t, text in parsed["events"]],
        "unparsed_lines": parsed["unparsed"],
    }
    if extra:
        doc.update(extra)
    return doc


def samples_from_document(doc):
    """Round-trip helper: columnar document -> list of sample dicts.

    Anything reading these documents back (plots, fitting, export to
    Parquet for the Zenodo/HF offload) goes through here rather than
    reimplementing the column layout.
    """
    columns = decode_series(doc["series"])
    return [dict((field, columns[field][i]) for field in SAMPLE_FIELDS)
            for i in range(len(columns["t_ms"]))]


# ---------------------------------------------------------------------------
# MongoDB
# ---------------------------------------------------------------------------

def _client(uri_env):
    uri = os.environ.get(uri_env)
    if not uri:
        print("[upload] {} is not set -- skipping.  Save the run with "
              "--out and backfill later.".format(uri_env))
        return None
    try:
        from pymongo import MongoClient   # pip install pymongo
    except ImportError:
        print("[upload] pymongo not installed (pip install pymongo) -- "
              "skipping; save with --out and backfill later.")
        return None
    return MongoClient(uri, serverSelectionTimeoutMS=15000)


def ensure_indexes(db, collection):
    """Create the indexes this collection needs (run once, idempotent).

    ``run_uid`` unique is what makes re-uploads safe; the compound
    index is the query the analysis actually runs ("this powder's
    runs, newest first").
    """
    coll = db[collection]
    coll.create_index("run_uid", unique=True, name="run_uid_unique")
    coll.create_index([("powder_id", 1), ("started_utc", -1)],
                      name="powder_started")
    coll.create_index("doc_type", name="doc_type")
    return sorted(coll.index_information())


def upload(doc, db_name, collection, uri_env="MONGODB_URI"):
    """Upsert one run document on ``run_uid`` (idempotent)."""
    client = _client(uri_env)
    if client is None:
        return None
    result = client[db_name][collection].replace_one(
        {"run_uid": doc["run_uid"]}, doc, upsert=True)
    action = "inserted" if result.upserted_id else "updated"
    print("[upload] {} {}.{} run_uid={}".format(
        action, db_name, collection, doc["run_uid"][:12]))
    return result


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Capture a dose run into one MongoDB document "
                    "(issue #126, tier 1).")
    parser.add_argument("source", help="log file to parse, or - for stdin "
                                       "(stdin is teed back to stdout)")
    parser.add_argument("--powder-id", default=None,
                        help="powder slug; defaults to the device's "
                             "M,powder_id row")
    parser.add_argument("--operator", default=None)
    parser.add_argument("--notes", default=None)
    parser.add_argument("--started-utc", default=None,
                        help="ISO-8601 UTC start; defaults to now for a "
                             "live capture, and must be given by hand when "
                             "backfilling (the device stream is relative-time "
                             "only)")
    parser.add_argument("--device-host", default=None,
                        help="e.g. rpi-zero2w-powder-doser")
    parser.add_argument("--firmware", default="pid_dose.py")
    parser.add_argument("--out", default=None,
                        help="also write the document to this JSON path")
    parser.add_argument("--upload", action="store_true")
    parser.add_argument("--ensure-indexes", action="store_true",
                        help="create the collection's indexes and exit")
    parser.add_argument("--db", default="powder_doser")
    parser.add_argument("--collection", default="dose_runs")
    parser.add_argument("--uri-env", default="MONGODB_URI",
                        help="env var holding the connection string")
    args = parser.parse_args(argv)

    if args.ensure_indexes:
        client = _client(args.uri_env)
        if client is None:
            return 1
        print("[indexes] {}".format(
            ensure_indexes(client[args.db], args.collection)))
        return 0

    if args.source == "-":
        parsed = parse_stream(sys.stdin, tee=sys.stdout)
        started = args.started_utc or datetime.datetime.now(
            datetime.timezone.utc).replace(microsecond=0).isoformat()
    else:
        with open(args.source) as handle:
            parsed = parse_stream(handle)
        started = args.started_utc

    doc = build_run_document(
        parsed,
        powder_id=args.powder_id,
        operator=args.operator,
        notes=args.notes,
        started_utc=started,
        device={"host": args.device_host, "mcu": "pico-w",
                "firmware": args.firmware},
        source=None if args.source == "-" else args.source,
        provenance=git_provenance(),
    )

    body = json.dumps(doc)
    print("[run] {} samples, {:.1f} s, {} events, {} unparsed lines, "
          "{:.1f} KB".format(doc["n_samples"], doc["duration_s"] or 0.0,
                             len(doc["events"]), doc["unparsed_lines"],
                             len(body) / 1024.0), file=sys.stderr)
    if doc["summary"]:
        print("[run] summary {}".format(doc["summary"]), file=sys.stderr)
    if not doc["powder_id"]:
        print("[run] WARNING: no powder_id (pass --powder-id) -- the run "
              "will not join its powder's history", file=sys.stderr)

    if args.out:
        with open(args.out, "w") as handle:
            json.dump(doc, handle, indent=2)
        print("[run] wrote {}".format(args.out), file=sys.stderr)

    if args.upload:
        upload(doc, args.db, args.collection, args.uri_env)
    return 0


if __name__ == "__main__":
    sys.exit(main())
