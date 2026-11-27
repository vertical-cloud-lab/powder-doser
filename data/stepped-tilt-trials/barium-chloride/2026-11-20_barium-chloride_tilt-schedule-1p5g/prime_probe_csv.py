#!/usr/bin/env python3
"""Split the priming spin and the per-angle flow probe out of session_launch2.log.

Both ran through the same ``mpremote run | stamp.py`` pipe as the trials,
into the same log, before the trial script (see run2.sh in the README).
Each script restarts the Pico's millisecond clock, so each block is anchored
to UTC on its own (smallest receipt-minus-Pico gap, as in
scripts/analyze_tilt_trials.py).

The 2026-11-19 new-auger copy, with the powder id set for the 2026-11-20c
barium chloride run (PR #131).

usage: python prime_probe_csv.py launch2_1741Z/session_launch2.log OUTDIR
writes OUTDIR/prime_spin_0deg.csv and OUTDIR/flow_probe_by_angle.csv
"""
import csv
import json
import os
import statistics
import sys
from datetime import datetime, timezone

POWDER_ID = "barium-chloride"

COLS = ["powder_id", "date_utc", "time_utc", "t_s", "balance_status",
        "mass_abs_g", "tilt_deg", "auger_rpm", "poll_ms", "step", "events"]


def blocks(path):
    cur, out = None, {"prime": [], "probe": []}
    for raw in open(path, encoding="utf-8", errors="replace"):
        raw = raw.rstrip("\n")
        if raw.startswith("PRIME_LAUNCH_UTC"):
            cur = "prime"
            continue
        if raw.startswith("PROBE_LAUNCH_UTC"):
            cur = "probe"
            continue
        if raw.startswith(("PRIME_EXIT", "PROBE_EXIT", "LAUNCH_UTC")):
            cur = None
            continue
        if cur and "\t" in raw:
            host, line = raw.split("\t", 1)
            out[cur].append((float(host), line.rstrip("\r")))
    return out


def write(rows_in, kind, path):
    offs, frames, pending = [], [], []
    step = "rest"
    for host, line in rows_in:
        p = line.split(",")
        if p[0] == "PRIME_SPIN_START":
            step = "spin"
            offs.append(host - int(p[1]) / 1000.0)
        elif p[0] == "PRIME_SPIN_STOP":
            step = "settle"
            offs.append(host - int(p[1]) / 1000.0)
        elif p[0] == "E" and len(p) >= 3:
            offs.append(host - int(p[1]) / 1000.0)
            pending.append(",".join(p[2:]))
        elif p[0] == "P":
            try:
                t = int(p[1])
            except ValueError:
                continue
            offs.append(host - t / 1000.0)
            frames.append({
                "t_ms": t, "stat": p[2], "g": p[3], "tilt": p[4],
                "rpm": p[5], "poll": p[6],
                "step": p[7] if (kind == "probe" and len(p) > 7) else step,
                "events": "; ".join(pending)})
            pending = []
    off = min(offs)
    with open(path, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(COLS)
        for f in frames:
            ts = datetime.fromtimestamp(off + f["t_ms"] / 1000.0, tz=timezone.utc)
            w.writerow([POWDER_ID, ts.strftime("%Y-%m-%d"),
                        ts.strftime("%H:%M:%S.") + "{:03d}".format(ts.microsecond // 1000),
                        "{:.3f}".format(f["t_ms"] / 1000.0), f["stat"], f["g"],
                        f["tilt"], f["rpm"], f["poll"], f["step"], f["events"]])
    return frames


def main():
    log, out = sys.argv[1], sys.argv[2]
    b = blocks(log)
    pf = write(b["prime"], "prime", os.path.join(out, "prime_spin_0deg.csv"))
    qf = write(b["probe"], "probe", os.path.join(out, "flow_probe_by_angle.csv"))
    pre = [float(f["g"]) for f in pf if f["step"] == "rest" and f["g"]][-8:]
    spin = [f for f in pf if f["step"] == "spin"]
    first0 = [float(f["g"]) for f in qf if f["step"] == "pre" and f["g"]][-6:]
    print(json.dumps({
        "prime_m0_abs_g": statistics.median(pre),
        "prime_spin_s": round((spin[-1]["t_ms"] - spin[0]["t_ms"]) / 1000.0, 1),
        "probe_start_abs_g_0deg": statistics.median(first0),
        "prime_gain_g": round(statistics.median(first0) - statistics.median(pre), 4),
        "prime_frames": len(pf), "probe_frames": len(qf)}))
    for host, line in b["probe"]:
        if line.startswith("STEP,"):
            s = json.loads(line[5:])
            print("probe step {k}: {tilt_deg:.0f} deg  {gain_g:+.4f} g".format(**s))


if __name__ == "__main__":
    main()
