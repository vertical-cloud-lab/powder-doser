#!/usr/bin/env python3
"""Per-minute disturbance profile of a battery run, for issue #116.

Every run's ``trials_<id>.csv`` carries, for each measured action, the
residual scatter about the bracket fit (``sigma_g``), the zero step the
actuator gate subtracted as a mechanical shock (``shock_g``), and how
many attempts were discarded and re-measured (``retries``).  Those are
a continuous record of what the room did to the balance while the run
was in progress, sampled wherever a trial happened to be.

Plotted against elapsed time they separate two disturbance sources that
the single per-run summary conflates:

* the **settling transient** -- a burst of shocks in the first two to
  four minutes, present in every run, left over from the operator
  handling the auger and stepping away.  It decays on its own.
* **episodic bench activity** -- later, isolated bursts that arrive
  after the bench has already settled.  These are what a person working
  nearby produces, and they are the ones worth scheduling around.

A run whose late window is quiet had nobody near it; a run with the
same early burst but a noisy tail did.  That contrast is the whole
figure.

Usage::

    python scripts/plot_bench_activity.py out.png run_a.json run_b.json ...

Run documents are read for provenance (start time, powder) and the
trial rows are read from the sibling ``trials_<id>.csv``.
"""

import csv
import json
import os
import statistics
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# Trials whose bracket contained a step at least this large had it
# subtracted as a zero offset; balance_filter uses the same threshold.
SHOCK_G = 0.010
SETTLING_MIN = 4.0          # minutes; the burst every run shows
LATE_MIN = 8.0              # minutes; by here the bench has settled


def _f(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def load(run_json):
    doc = json.load(open(run_json))
    pid = doc.get("powder_id") or "?"
    trials = os.path.join(os.path.dirname(run_json), "trials_%s.csv" % pid)
    rows = list(csv.DictReader(open(trials)))
    started = (doc.get("started_utc") or "")[:16].replace("T", " ")
    return pid, started, rows


def profile(rows):
    """Bucket trials by elapsed minute -> (median sigma, shocks, retries)."""
    buckets = {}
    for r in rows:
        t = _f(r.get("t_ms"))
        if t is None:
            continue
        b = buckets.setdefault(int(t // 60000), {"sig": [], "shock": 0, "ret": 0})
        sig = _f(r.get("sigma_g"))
        b["sig"].append((sig or 0.0) * 1000.0)
        shock = _f(r.get("shock_g")) or 0.0
        if abs(shock) >= SHOCK_G:
            b["shock"] += 1
        b["ret"] += int(r.get("retries") or 0)
    return buckets


def window(rows, lo_min, hi_min):
    """Shock rate and median sigma over an elapsed-time window."""
    sel = [r for r in rows
           if lo_min <= (_f(r.get("t_ms")) or 0.0) / 60000.0 < hi_min]
    if not sel:
        return None
    ts = [(_f(r.get("t_ms")) or 0.0) / 60000.0 for r in sel]
    # +0.5 min so a window holding a single trial is not a divide-by-zero
    # and does not report an absurd per-minute rate.
    span = (max(ts) - min(ts)) + 0.5
    shocks = sum(1 for r in sel
                 if abs(_f(r.get("shock_g")) or 0.0) >= SHOCK_G)
    sig = [(_f(r.get("sigma_g")) or 0.0) * 1000.0 for r in sel]
    return {"n": len(sel), "median_sigma_mg": statistics.median(sig),
            "shocks": shocks, "shocks_per_min": shocks / span,
            "retries_per_min": sum(int(r.get("retries") or 0) for r in sel) / span}


def main(out, run_jsons):
    runs = [load(p) for p in run_jsons]
    fig, axes = plt.subplots(2, 1, figsize=(11, 7.5), sharex=True)
    colours = plt.rcParams["axes.prop_cycle"].by_key()["color"]

    for i, (pid, started, rows) in enumerate(runs):
        buckets = profile(rows)
        mins = sorted(buckets)
        c = colours[i % len(colours)]
        label = "%s  %s" % (pid, started)
        axes[0].plot(mins, [statistics.median(buckets[m]["sig"]) for m in mins],
                     marker="o", ms=3, lw=1.4, color=c, label=label)
        shocks = [buckets[m]["shock"] for m in mins]
        axes[1].plot(mins, shocks, marker="s", ms=4, lw=1.2, color=c, alpha=0.85)
        for m, s in zip(mins, shocks):
            if s and m >= LATE_MIN:               # the ones that matter
                axes[1].annotate("", (m, s))

    axes[0].axvspan(0, SETTLING_MIN, color="0.85", zorder=0)
    axes[1].axvspan(0, SETTLING_MIN, color="0.85", zorder=0)
    axes[0].text(SETTLING_MIN / 2, axes[0].get_ylim()[1] * 0.95,
                 "settling\n(every run)", ha="center", va="top", fontsize=8,
                 color="0.35")
    axes[0].set_ylabel("median per-trial $\\sigma$ (mg)")
    axes[0].set_title("What the room did during each run, minute by minute\n"
                      "grey band = the settling burst every run shows; "
                      "anything after it is bench activity", fontsize=11)
    axes[0].legend(fontsize=8, ncol=2)
    axes[0].grid(alpha=0.3)
    axes[1].set_ylabel("mechanical shocks\n(> %d mg) per minute" % (SHOCK_G * 1000))
    axes[1].set_xlabel("elapsed time in run (minutes)")
    axes[1].grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(out, dpi=150)
    print("[plot] wrote %s" % out)

    print("\n%-24s | %-22s | %-22s" % ("run", "settling (min 0-%g)" % SETTLING_MIN,
                                       "late (min >= %g)" % LATE_MIN))
    print("%-24s | %6s %6s %8s | %6s %6s %8s"
          % ("", "med s", "shock", "shk/min", "med s", "shock", "shk/min"))
    for pid, started, rows in runs:
        e, l = window(rows, 0, SETTLING_MIN), window(rows, LATE_MIN, 1e9)
        if not (e and l):
            continue
        print("%-24s | %6.1f %6d %8.2f | %6.1f %6d %8.2f"
              % ("%s %s" % (pid, started[5:10]),
                 e["median_sigma_mg"], e["shocks"], e["shocks_per_min"],
                 l["median_sigma_mg"], l["shocks"], l["shocks_per_min"]))


if __name__ == "__main__":
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    main(sys.argv[1], sys.argv[2:])
