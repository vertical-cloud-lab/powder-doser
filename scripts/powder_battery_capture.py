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
# battery_version 2 appends per-trial quality columns produced by the
# actuator-gated artifact rejection in balance_filter.py.  Rows from a
# version 1 device are still accepted and simply leave these empty, so
# the nine committed runs keep parsing with the same code.
TRIAL_QUALITY_FIELDS = ["sigma_g", "drift_g", "shock_g", "retries",
                        "quality"]
TRIAL_FIELDS_V2 = TRIAL_FIELDS + TRIAL_QUALITY_FIELDS
RETRY_FIELDS = ["block", "tilt_deg", "phase", "trial", "reason",
                "shock_g", "discarded_delta_g", "t_ms"]
POLL_FIELDS = ["block", "tilt_deg", "rpm", "t_ms", "grams", "stable"]
DOSE_FIELDS = ["n", "target_g", "dispensed_g", "error_g", "status",
               "elapsed_s", "auger_rev", "taps", "phase_cycles", "t_ms"]
# battery_version 3 appends the block letter, because Block H doses at
# 50/200 mg alongside Block G's 1.000 g and a target alone no longer
# identifies which block a dose belongs to.  Rows without it are Block
# G by definition -- H did not exist -- so the eleven committed runs
# keep parsing unchanged.
DOSE_FIELDS_V3 = DOSE_FIELDS + ["block"]
DEFAULT_DOSE_BLOCK = "G"
SUMMARY_FIELDS = ["block", "tilt_deg", "phase", "n", "mean_g", "std_g",
                  "sem_g", "min_g", "max_g", "rsd_pct"]
# CSV files on disk lead every row with the powder ID so a file stays
# attributable after it is copied out of its run directory.
OUT_TRIAL_FIELDS = ["powder_id"] + TRIAL_FIELDS_V2
OUT_RETRY_FIELDS = ["powder_id"] + RETRY_FIELDS
OUT_POLL_FIELDS = ["powder_id"] + POLL_FIELDS
OUT_DOSE_FIELDS = ["powder_id"] + DOSE_FIELDS_V3
OUT_SUMMARY_FIELDS = ["powder_id"] + SUMMARY_FIELDS
TIMELINE_FIELDS = ["block", "started_utc", "started_local", "elapsed_s"]
OUT_TIMELINE_FIELDS = ["powder_id"] + TIMELINE_FIELDS
# 2 adds elapsed_s + block_timeline; 3 adds the lab-local clock alongside
# every UTC stamp.  Every earlier field is unchanged and still populated,
# so schema_version 1 and 2 documents stay readable by the same consumers.
SCHEMA_VERSION = 3


def local_stamp(when=None):
    """Wall clock in the lab's own timezone, e.g. '2026-08-05 15:12:16 MDT'.

    UTC stays the canonical clock -- it is what the run directories, the
    stream anchors and MongoDB are keyed on -- but the people reading
    these runs are in the lab, and cross-referencing a bench observation
    against a UTC stamp is a needless subtraction every single time.  The
    bench camera's burned-in overlay is lab-local too, so this is also the
    clock that matches the video.
    """
    when = when or time.localtime()
    return time.strftime("%Y-%m-%d %H:%M:%S %Z", when)


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
        if len(parts) == len(TRIAL_FIELDS_V2) + 1:
            fields = TRIAL_FIELDS_V2
        elif len(parts) == len(TRIAL_FIELDS) + 1:
            fields = TRIAL_FIELDS
        else:
            return None
        row = dict(zip(fields, parts[1:]))
        row["tilt_deg"] = float(row["tilt_deg"])
        for key in ("before_g", "after_g", "delta_g"):
            row[key] = _float_or_none(row[key])
        row["rpm"] = _float_or_none(row["rpm"])
        row["trial"] = int(row["trial"])
        row["t_ms"] = int(row["t_ms"])
        for key in ("sigma_g", "drift_g", "shock_g"):
            if key in row:
                row[key] = _float_or_none(row[key])
        if row.get("retries") not in (None, ""):
            row["retries"] = int(row["retries"])
        return "trial", row
    if line.startswith("RETRY,"):
        parts = line.split(",")
        if len(parts) != len(RETRY_FIELDS) + 1:
            return None
        row = dict(zip(RETRY_FIELDS, parts[1:]))
        row["tilt_deg"] = _float_or_none(row["tilt_deg"])
        for key in ("shock_g", "discarded_delta_g"):
            row[key] = _float_or_none(row[key])
        row["t_ms"] = int(row["t_ms"])
        return "retry", row
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
        if len(parts) == len(DOSE_FIELDS_V3) + 1:
            fields = DOSE_FIELDS_V3
        elif len(parts) == len(DOSE_FIELDS) + 1:
            fields = DOSE_FIELDS
        else:
            return None
        row = dict(zip(fields, parts[1:]))
        row.setdefault("block", DEFAULT_DOSE_BLOCK)
        row["block"] = row["block"] or DEFAULT_DOSE_BLOCK
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


def block_marker(line):
    """Block letter for a ``[battery] block X`` line, else None.

    The device announces each block in plain text rather than as a CSV
    record, so this is how the host learns where a run has got to.  The
    battery takes ~50 min and most of it is block G, so knowing which
    block is live -- and for how long -- is the difference between "this
    is stuck" and "this is the dose phase behaving normally".

    Only a bare block letter counts.  The device logs other lines that
    begin the same way -- Block H announces the thresholds it derived
    for each of its targets -- and taking the first word of those would
    append a second timeline entry mid-block, silently restarting the
    block's clock and shortening its measured duration.
    """
    line = line.strip()
    prefix = "[battery] block "
    if not line.startswith(prefix):
        return None
    rest = line[len(prefix):].strip()
    if not rest:
        return None
    word = rest.split()[0]
    return word if len(word) == 1 and word.isalpha() else None


def format_elapsed(seconds):
    """Seconds -> ``H:MM:SS`` for console and timeline output."""
    seconds = int(seconds)
    return "{}:{:02d}:{:02d}".format(
        seconds // 3600, (seconds % 3600) // 60, seconds % 60)


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
    """Aggregate accuracy/speed over the closed-loop doses.

    Kept over *all* doses so the field means what it always meant.  Once
    Block H runs, a single mean mixes 50 mg and 1 g targets and the
    number to read is ``dose_summary_by_target`` instead.
    """
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


def dose_summary_by_target(doses):
    """Per-(block, target) accuracy -- the Block G vs Block H comparison.

    Block H exists to ask whether dose error is a fixed *mass* or a
    fixed *fraction* of the target, so the relative error is carried
    alongside the absolute one; a fixed-mass controller shows a flat
    ``mean_error_g`` and a ``mean_rel_error_pct`` that grows as the
    target shrinks.
    """
    if not doses:
        return None
    groups = {}
    for dose in doses:
        key = (dose.get("block") or DEFAULT_DOSE_BLOCK, dose["target_g"])
        groups.setdefault(key, []).append(dose)
    out = []
    for (block, target), rows in sorted(
            groups.items(), key=lambda kv: (kv[0][1] or 0.0, kv[0][0])):
        errors = [r["error_g"] for r in rows if r["error_g"] is not None]
        times = [r["elapsed_s"] for r in rows]
        n, mean_err, std_err, _, lo, hi = sample_stats(errors)
        rel = (100.0 * mean_err / target
               if mean_err is not None and target else None)
        out.append({
            "block": block,
            "target_g": target,
            "n": len(rows),
            "ok": sum(1 for r in rows if r["status"] == "ok"),
            "statuses": sorted({r["status"] for r in rows}),
            "mean_error_g": mean_err,
            "std_error_g": std_err,
            "max_abs_error_g": (max(abs(e) for e in errors)
                                if errors else None),
            "mean_rel_error_pct": round(rel, 3) if rel is not None else None,
            "mean_elapsed_s": sum(times) / len(times) if times else None,
        })
    return out


def environment_summary(meta, trials, retries=None):
    """Per-run account of what the environment did and what was removed.

    Empty for battery_version 1 runs, which carry no quality columns.
    Deliberately reported rather than folded into the measurements: a
    run that silently subtracts shocks looks identical to a run in a
    quiet room, and the analysis needs to be able to tell them apart.
    """
    quality = [t.get("quality") for t in trials if t.get("quality")]
    if not quality and not (retries or []):
        return None
    sigmas = sorted(t["sigma_g"] for t in trials
                    if t.get("sigma_g") is not None)
    shocks = [t["shock_g"] for t in trials
              if t.get("shock_g") not in (None, 0.0)]
    drifts = [abs(t["drift_g"]) for t in trials
              if t.get("drift_g") is not None]
    counts = {}
    for q in quality:
        counts[q] = counts.get(q, 0) + 1
    out = {
        "trials": len(trials),
        "quality_counts": counts,
        "clean_trial_fraction": (round(counts.get("ok", 0) / len(quality), 4)
                                 if quality else None),
        "median_sigma_g": (sigmas[len(sigmas) // 2] if sigmas else None),
        "max_sigma_g": (sigmas[-1] if sigmas else None),
        "shock_events": len(shocks),
        "shock_removed_g": round(sum(abs(v) for v in shocks), 6),
        "drift_removed_median_g": (sorted(drifts)[len(drifts) // 2]
                                   if drifts else None),
        "drift_removed_total_g": round(sum(drifts), 6) if drifts else None,
        "retried_trials": len(retries or []),
    }
    for key, value in (meta or {}).items():
        if key.startswith("env."):
            out.setdefault("device", {})[key[4:]] = value
    return out


def load_preflight(value):
    """Return the pre-flight document from a file path or an inline JSON string.

    The flag reads naturally as "--preflight-json '{...}'", and that is how it
    has been mis-called at the bench -- which raised only *after* the battery
    had finished, at the point where the artifacts get written.  The raw serial
    log always survives that (``--from-raw`` rebuilds the run), but the block
    timeline does not, so the failure costs real data for a typo.  Accept both
    spellings instead of insisting on the one.
    """
    text = str(value).strip()
    if text.startswith("{"):
        return json.loads(text)
    with open(text) as handle:
        return json.load(handle)


def build_run_document(meta, trials, polls, doses, device_summaries,
                       host_summary, status, args, started_utc,
                       ended_utc, elapsed_s=None, timeline=None,
                       retries=None):
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
        preflight = load_preflight(args.preflight_json)
    qc = {
        # Default to excluding a run: a battery is only comparable across
        # powders once someone has confirmed the rig actually fed.
        "valid_for_cross_powder_comparison": bool(
            getattr(args, "qc_valid", False)),
        "verdict": getattr(args, "qc_verdict", None) or "unreviewed",
    }
    if preflight is not None:
        qc["preflight_verdict"] = preflight.get("verdict")
    env = environment_summary(meta, trials, retries)
    if env:
        qc["environment_corrected"] = True
        qc["shock_events"] = env.get("shock_events")
        qc["retried_trials"] = env.get("retried_trials")
    return {
        "kind": "battery_run",
        "schema_version": SCHEMA_VERSION,
        "status": status,
        "started_utc": started_utc,
        "ended_utc": ended_utc,
        "started_local": getattr(args, "started_local", None),
        "ended_local": getattr(args, "ended_local", None),
        "lab_timezone": time.strftime("%Z"),
        "elapsed_s": elapsed_s,
        "block_timeline": timeline or [],
        "powder_id": args.powder_id,
        "powder": args.powder,
        "batch": getattr(args, "batch", None),
        "operator": args.operator,
        "notes": args.notes,
        "qc": qc,
        "environment": env,
        "retries": retries or [],
        "preflight": preflight,
        "git_commit": git_commit,
        "parameters": meta,
        "trials": trials,
        "polls": polls,
        "doses": doses,
        "dose_summary": dose_summary(doses),
        "dose_summary_by_target": dose_summary_by_target(doses),
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
    retries = []
    timeline = []
    status = "incomplete"
    raw_path = os.path.join(
        out_dir, "raw_serial_{}.log".format(args.powder_id))
    started_monotonic = time.monotonic()
    args.started_local = local_stamp()
    print("[capture] run started {}  (local {})".format(
        started_utc, args.started_local))
    print("[capture] blocks A-F are the first ~15-25 min; the closed-loop "
          "dose blocks are the rest -- G is 3 x 1 g and H is 3 each at "
          "50 mg and 200 mg, so a full ABCDEFGH run can reach ~2 h")
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
                # The raw log stays byte-for-byte what the device sent;
                # the clock is a console/timeline concern only.
                raw.write(line)
                raw.flush()
                elapsed = time.monotonic() - started_monotonic
                print("[{} +{}] {}".format(
                    time.strftime("%H:%M:%S", time.gmtime()),
                    format_elapsed(elapsed), line.rstrip()))
                block = block_marker(line)
                if block is not None:
                    timeline.append({
                        "block": block,
                        "started_utc": datetime.datetime.now(
                            datetime.timezone.utc).isoformat(),
                        "started_local": local_stamp(),
                        "elapsed_s": round(elapsed, 1),
                    })
                parsed = parse_line(line)
                if parsed is None:
                    continue
                kind, payload = parsed
                if kind == "trial":
                    trials.append(payload)
                elif kind == "retry":
                    retries.append(payload)
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
        # stdout may already be gone (a killed `tee`, a closed tmux
        # pane), and losing a run's parsed outputs to a BrokenPipeError
        # while *printing* would be absurd -- the raw log is on disk
        # either way, but the CSVs and the run document are not.
        try:
            print("\n[capture] interrupted -- saving partial run")
        except Exception:
            pass
        status = "capture-interrupted"
    finally:
        stop.set()
        try:
            port.close()
        except Exception:
            pass

    ended_utc = datetime.datetime.now(datetime.timezone.utc).isoformat()
    args.ended_local = local_stamp()
    elapsed_s = round(time.monotonic() - started_monotonic, 1)
    host_summary = summarize(trials)
    doc = build_run_document(meta, trials, polls, doses,
                             device_summaries, host_summary, status,
                             args, started_utc, ended_utc,
                             elapsed_s=elapsed_s, timeline=timeline,
                             retries=retries)

    write_outputs(out_dir, args.powder_id, trials, polls, doses,
                  host_summary, doc, retries=retries)
    print_summary(host_summary, doses)
    print_timeline(started_utc, ended_utc, elapsed_s, timeline,
                   started_local=args.started_local,
                   ended_local=args.ended_local)
    if args.upload:
        upload(doc, args)
    return doc


def write_outputs(out_dir, powder_id, trials, polls, doses,
                  host_summary, doc, retries=None):
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
    write_csv("timeline", OUT_TIMELINE_FIELDS, doc.get("block_timeline", []))
    if retries:
        write_csv("retries", OUT_RETRY_FIELDS, retries)
    with open(os.path.join(
            out_dir, "run_{}.json".format(powder_id)), "w") as fh:
        json.dump(doc, fh, indent=2)
    print("[capture] wrote trials_{0}.csv, polls_{0}.csv, doses_{0}.csv, "
          "summary_{0}.csv, timeline_{0}.csv, run_{0}.json"
          .format(powder_id))


def print_timeline(started_utc, ended_utc, elapsed_s, timeline,
                   started_local=None, ended_local=None):
    """Wall-clock account of the run: when it started, where time went.

    Printed last so it is the final thing in the tmux scrollback, and
    so a run that looks slow can be checked against the block it was
    actually in rather than the last block anyone happened to see.

    Both clocks are shown: UTC because it keys the run directory and the
    database, lab-local because that is what the people at the bench (and
    the camera overlay) are reading.
    """
    print("[capture] started {}{}".format(
        started_utc, "  ({})".format(started_local) if started_local else ""))
    print("[capture] ended   {}{}".format(
        ended_utc, "  ({})".format(ended_local) if ended_local else ""))
    if elapsed_s is not None:
        print("[capture] elapsed {} ({:.1f} s)".format(
            format_elapsed(elapsed_s), elapsed_s))
    if not timeline:
        return
    print("{:>6} {:>10} {:>10}  {:<26} {}".format(
        "block", "at", "duration", "started_utc", "started_local"))
    for i, row in enumerate(timeline):
        end = (timeline[i + 1]["elapsed_s"] if i + 1 < len(timeline)
               else elapsed_s)
        duration = (format_elapsed(end - row["elapsed_s"])
                    if end is not None else "-")
        print("{:>6} {:>10} {:>10}  {:<26} {}".format(
            row["block"], format_elapsed(row["elapsed_s"]), duration,
            row["started_utc"], row.get("started_local", "")))


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
        print("dose {}{}: {} {:.4f}/{:.4f} g ({:+.4f} g) in {:.1f} s, "
              "{} taps, cycles {}".format(
                  dose.get("block") or DEFAULT_DOSE_BLOCK, dose["n"],
                  dose["status"], dose["dispensed_g"],
                  dose["target_g"], dose["error_g"], dose["elapsed_s"],
                  dose["taps"], dose["phase_cycles"]))
    by_target = dose_summary_by_target(doses) or []
    if len(by_target) > 1:
        # The Block G / Block H comparison, which is the point of
        # running both: absolute error flat across targets means a
        # fixed-mass controller, and the relative column is what grows.
        print("{:>5} {:>10} {:>4} {:>4} {:>11} {:>10} {:>9}".format(
            "block", "target_g", "n", "ok", "mean_err_g", "std_err_g",
            "rel_err%"))
        for row in by_target:
            print("{:>5} {:>10.4f} {:>4} {:>4} {:>11} {:>10} {:>9}".format(
                row["block"], row["target_g"], row["n"], row["ok"],
                *["{:+.4f}".format(row[k]) if row[k] is not None else "-"
                  for k in ("mean_error_g", "std_error_g")],
                "{:+.2f}".format(row["mean_rel_error_pct"])
                if row["mean_rel_error_pct"] is not None else "-"))


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


def replay(path, args):
    """Rebuild a run from its raw serial log.

    The capture is a pure parser over the device stream, so the raw log
    is a complete record: if the capture process dies -- a killed pipe,
    a dropped SSH session, a full disk -- nothing is actually lost, and
    this reconstructs the CSVs and the run document exactly as a live
    capture would have written them.  It is also how a run captured on
    one machine gets analysed on another.
    """
    meta, trials, polls, doses, device_summaries = {}, [], [], [], []
    retries, timeline = [], []
    status = "incomplete"
    with open(path, errors="replace") as fh:
        lines = fh.readlines()
    for line in lines:
        block = block_marker(line)
        if block is not None:
            timeline.append({"block": block, "started_utc": None,
                             "started_local": None, "elapsed_s": None})
        parsed = parse_line(line)
        if parsed is None:
            continue
        kind, payload = parsed
        if kind == "trial":
            trials.append(payload)
        elif kind == "retry":
            retries.append(payload)
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
    if status == "incomplete" and trials:
        # No RUN,END: the device stream was cut, not finished cleanly.
        status = "truncated"
    # Device timestamps are the only clock the log carries, so use them
    # rather than inventing wall-clock times the capture never saw.
    def _t(rows):
        return [r["t_ms"] for r in rows if r.get("t_ms") is not None]
    stamps = _t(trials) + _t(polls) + _t(doses)
    elapsed_s = round(max(stamps) / 1000.0, 1) if stamps else None
    for i, row in enumerate(timeline):
        row["elapsed_s"] = None
    out_dir = os.path.dirname(os.path.abspath(path))
    host_summary = summarize(trials)
    doc = build_run_document(meta, trials, polls, doses, device_summaries,
                             host_summary, status, args,
                             getattr(args, "started_utc", None),
                             getattr(args, "ended_utc", None),
                             elapsed_s=elapsed_s, timeline=timeline,
                             retries=retries)
    doc["reconstructed_from_raw_log"] = os.path.basename(path)
    write_outputs(out_dir, args.powder_id, trials, polls, doses,
                  host_summary, doc, retries=retries)
    print_summary(host_summary, doses)
    if args.upload:
        upload(doc, args)
    return doc


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
    parser.add_argument("--preflight-json", default=None, metavar="FILE_OR_JSON",
                        help="pre-flight feed check result to embed, as a "
                        "path to a JSON file or the JSON document itself "
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
    parser.add_argument("--from-raw", default=None, metavar="RAW_LOG",
                        help="rebuild a run's CSVs and run.json from a "
                        "raw serial log instead of capturing live "
                        "(recovers a run whose capture process died)")
    parser.add_argument("--started-utc", default=None,
                        help="run start time for --from-raw provenance")
    parser.add_argument("--ended-utc", default=None,
                        help="run end time for --from-raw provenance")
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

    if args.from_raw:
        if not args.powder_id:
            parser.error("--from-raw needs --powder-id")
        args.started_local = args.ended_local = None
        return 0 if replay(args.from_raw, args) is not None else 1

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
