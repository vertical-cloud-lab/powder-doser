#!/usr/bin/env python3
"""Show what the environment did to a battery run, and what was removed.

Three panels from one ``run_<powder>.json`` written by a
``battery_version`` 2 device:

A. Block C feed factor per revolution with the trial's own uncertainty
   as an error bar.  Version 1 had no error bars to draw -- a trial was
   a single stable reading -- so the spread had to be inferred from the
   scatter of six revolutions, which conflates powder variability with
   whatever the room did.  Now the two are separable.
B. What each trial's raw before/after difference *would* have said,
   against the drift- and shock-corrected value actually recorded.  The
   gap is the correction, so it can be argued with rather than trusted.
C. The artifact rate over the run: corrections applied, and retries.

Usage::

    python scripts/plot_battery_environment.py data/battery/<run>/run_*.json
"""

from __future__ import annotations

import argparse
import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

MG = 1000.0


def load(path):
    with open(path) as fh:
        return json.load(fh)


def quality_colour(quality):
    return {"ok": "#2e7d32", "unsettled": "#ef6c00",
            "shock": "#c62828"}.get(quality, "#777777")


def plot(doc, out_path):
    trials = [t for t in doc.get("trials", []) if t.get("sigma_g") is not None]
    if not trials:
        raise SystemExit("no battery_version 2 trials in this run -- "
                         "nothing to plot")
    powder = doc.get("powder_id", "?")
    env = doc.get("environment") or {}

    fig, axes = plt.subplots(1, 3, figsize=(16, 4.8))

    # -- A: block C with real error bars --------------------------------
    ax = axes[0]
    rows = [t for t in trials if t["block"] == "C"]
    tilts = sorted({t["tilt_deg"] for t in rows})
    for i, tilt in enumerate(tilts):
        sel = [t for t in rows if t["tilt_deg"] == tilt]
        xs = [i + 0.16 * (j - (len(sel) - 1) / 2) for j in range(len(sel))]
        ax.errorbar(xs, [MG * t["delta_g"] for t in sel],
                    yerr=[MG * t["sigma_g"] for t in sel],
                    fmt="o", ms=5, capsize=3, lw=1.2,
                    ecolor="#999999", mfc="none", mec="#1565c0")
        mean = sum(t["delta_g"] for t in sel) / len(sel) * MG
        ax.hlines(mean, i - 0.34, i + 0.34, color="#1565c0", lw=2)
    ax.set_xticks(range(len(tilts)))
    ax.set_xticklabels(["{:.0f}$\\degree$".format(t) for t in tilts])
    ax.set_xlabel("tilt")
    ax.set_ylabel("mass per 360$\\degree$ revolution (mg)")
    ax.set_title("A  feed factor, with each trial's own uncertainty")
    ax.grid(alpha=0.25, axis="y")

    # -- B: raw vs corrected --------------------------------------------
    ax = axes[1]
    raw, corrected, colours = [], [], []
    for t in trials:
        correction = (t.get("drift_g") or 0.0) + (t.get("shock_g") or 0.0)
        corrected.append(MG * t["delta_g"])
        raw.append(MG * (t["delta_g"] + correction))
        colours.append(quality_colour(t.get("quality")))
    lo = min(min(raw), min(corrected))
    hi = max(max(raw), max(corrected))
    pad = 0.08 * (hi - lo) or 1.0
    lo, hi = lo - pad, hi + pad
    ax.plot([lo, hi], [lo, hi], color="#bbbbbb", lw=1, zorder=0)
    ax.set_xlim(lo, hi)
    ax.set_ylim(lo, hi)
    ax.scatter(raw, corrected, s=26, c=colours, alpha=0.85, zorder=2)
    ax.set_xlabel("uncorrected before/after difference (mg)")
    ax.set_ylabel("recorded, drift + shock corrected (mg)")
    ax.set_title("B  what the correction changed")
    ax.grid(alpha=0.25)
    for label, key in (("clean", "ok"), ("unsettled", "unsettled"),
                       ("shock removed", "shock")):
        ax.scatter([], [], s=26, c=quality_colour(key), label=label)
    ax.legend(loc="upper left", fontsize=8, frameon=False)

    # -- C: artifact rate over the run ----------------------------------
    ax = axes[2]
    t_min = [t["t_ms"] / 60000.0 for t in trials]
    ax.scatter(t_min, [MG * abs((t.get("drift_g") or 0.0)) for t in trials],
               s=20, label="drift removed", c="#1565c0")
    ax.scatter(t_min, [MG * abs((t.get("shock_g") or 0.0)) for t in trials],
               s=20, marker="x", label="shock removed", c="#c62828")
    ax.scatter(t_min, [MG * t["sigma_g"] for t in trials],
               s=16, marker="^", label="trial $\\sigma$", c="#2e7d32")
    ax.set_xlabel("minutes into the run")
    ax.set_ylabel("mg")
    ax.set_title("C  artifact rate, reported not hidden")
    ax.grid(alpha=0.25)
    ax.legend(fontsize=8, frameon=False)

    counts = env.get("quality_counts", {})
    fig.suptitle(
        "{} -- {} trials, {} clean / {} unsettled / {} shock-corrected, "
        "{} retries; median trial $\\sigma$ {:.1f} mg".format(
            powder, env.get("trials", len(trials)), counts.get("ok", 0),
            counts.get("unsettled", 0), counts.get("shock", 0),
            env.get("retried_trials", 0),
            MG * (env.get("median_sigma_g") or 0.0)),
        fontsize=11)
    fig.tight_layout(rect=(0, 0, 1, 0.93))
    fig.savefig(out_path, dpi=140)
    print("[plot] wrote {}".format(out_path))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument("run_json")
    ap.add_argument("--out", default=None)
    args = ap.parse_args(argv)
    doc = load(args.run_json)
    out = args.out or os.path.join(
        os.path.dirname(os.path.abspath(args.run_json)),
        "{}_environment.png".format(doc.get("powder_id", "run")))
    plot(doc, out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
