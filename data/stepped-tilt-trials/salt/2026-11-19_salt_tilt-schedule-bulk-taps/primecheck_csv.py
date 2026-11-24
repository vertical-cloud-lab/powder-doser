#!/usr/bin/env python3
"""Split the tapped priming check (prime_check_taps.py) out of its session log.

The check ran through the same ``mpremote run | stamp.py`` pipe as the
trials (see run_check.sh).  Its Pico clock restarts at 0, so it is anchored
to UTC on its own: offset = the smallest receipt-minus-Pico gap, as in
scripts/analyze_tilt_trials.py.

usage: python primecheck_csv.py primecheck_2111Z/session_primecheck.log OUTDIR
writes OUTDIR/prime_check_frames.csv (every balance frame) and
OUTDIR/prime_check_steps.csv (one row per spin)
"""
import csv
import json
import os
import sys
from datetime import datetime, timezone

COLS = ["powder_id", "date_utc", "time_utc", "t_s", "balance_status",
        "mass_abs_g", "tilt_deg", "auger_rpm", "taps_cum", "step", "poll_ms",
        "events"]


def main(path, out_dir):
    frames, events, steps = [], [], []
    for raw in open(path, encoding="utf-8", errors="replace"):
        raw = raw.rstrip("\n")
        if "\t" not in raw:
            continue
        host_s, line = raw.split("\t", 1)
        host = float(host_s)
        if line.startswith("P,"):
            p = line.split(",")
            frames.append({"host": host, "t_ms": int(p[1]), "stat": p[2],
                           "g": p[3], "tilt": p[4], "rpm": p[5],
                           "taps": p[6], "step": p[7], "poll": p[8]})
        elif line.startswith("E,"):
            p = line.split(",", 2)
            events.append((int(p[1]), p[2], host))
        elif line.startswith("STEP,"):
            steps.append(json.loads(line[5:]))
    off = min(f["host"] - f["t_ms"] / 1000.0 for f in frames)
    for (t, _, h) in events:
        off = min(off, h - t / 1000.0)
    ev_at = {}
    for (t, text, _) in events:
        best = min(frames, key=lambda f: abs(f["t_ms"] - t))
        ev_at.setdefault(id(best), []).append(text)
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "prime_check_frames.csv"), "w",
              newline="") as fh:
        w = csv.writer(fh)
        w.writerow(COLS)
        for f in frames:
            u = datetime.fromtimestamp(off + f["t_ms"] / 1000.0, tz=timezone.utc)
            w.writerow(["salt", u.strftime("%Y-%m-%d"),
                        u.strftime("%H:%M:%S.%f")[:-3],
                        "{:.3f}".format(f["t_ms"] / 1000.0), f["stat"], f["g"],
                        f["tilt"], f["rpm"], f["taps"], f["step"], f["poll"],
                        "; ".join(ev_at.get(id(f), []))])
    keys = ["step", "tilt_deg", "spin_s", "revs", "taps", "m0_abs_g",
            "m1_abs_g", "gain_mg"]
    with open(os.path.join(out_dir, "prime_check_steps.csv"), "w",
              newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["powder_id"] + keys + ["mg_per_rev"])
        for s in steps:
            mpr = (None if s.get("gain_mg") is None
                   else round(s["gain_mg"] / s["revs"], 3))
            w.writerow(["salt"] + [s.get(k) for k in keys] + [mpr])
    print("frames", len(frames), "steps", len(steps))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
