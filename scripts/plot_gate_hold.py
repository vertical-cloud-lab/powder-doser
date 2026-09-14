"""Figure for a dose-gate hold: baseline wander across repeated surveys.

Renders the pre-launch gate story for a blocks-G/H attempt: every 180 s
environment survey window on one wall-clock axis (top panel), and each
window's end-to-end drift rate against the launch condition the campaign
has actually used (bottom panel).  Written for the 2026-09-10 silicon
-110/+200 stand-down; reusable for any hold recorded as a series of
``*-preroll-survey*-180s.csv`` captures.

Usage:
    python scripts/plot_gate_hold.py --out gate_hold.png \
        docs/rig-checks/data/2026-09-10_silicon-110-200-preroll-survey*.csv
"""

import argparse
import csv
import os
from datetime import datetime, timedelta, timezone

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

UTC_TO_MDT = timedelta(hours=-6)
DOSE_BAND_MG = 5.0          # block G/H tolerance, for scale reference
LAUNCH_DRIFT_MG_MIN = 2.0   # the end-to-end drift the campaign has launched at
INK = "#3d4451"
MUTED = "#7a8294"
SERIES = "#3b6fd4"
BAND = "#e8eaef"

# gate conditions the four 2026-09-10 launches were accepted at (mg/min)
TODAY_LAUNCHES = {"sulfate": -1.6, "AlSi10Mg": +2.0, "Si -325": +0.6}


def load_window(path):
    """A survey CSV (t_s,status,mg) plus its wall-clock end from mtime."""
    with open(path) as fh:
        rows = list(csv.DictReader(fh))
    t = [float(r["t_s"]) for r in rows]
    mg = [float(r["mg"]) for r in rows]
    end = (datetime.fromtimestamp(os.path.getmtime(path), tz=timezone.utc)
           .replace(tzinfo=None) + UTC_TO_MDT)
    start = end - timedelta(seconds=t[-1] if t else 0.0)
    times = [start + timedelta(seconds=s) for s in t]
    return times, mg


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("csvs", nargs="+", help="survey CSVs, chronological")
    ap.add_argument("--out", required=True)
    ap.add_argument("--offscale", default=None,
                    help="path of a window to keep off the top panel "
                         "(e.g. post-pre-flight, sitting grams above)")
    ap.add_argument("--event", action="append", default=[],
                    metavar="HH:MM:SS,label", help="MDT event annotation")
    args = ap.parse_args()

    csvs = sorted(args.csvs, key=os.path.getmtime)
    windows = [(p, *load_window(p)) for p in csvs]

    fig, (ax, axd) = plt.subplots(
        2, 1, figsize=(10, 6.4), sharex=True,
        gridspec_kw={"height_ratios": [2.2, 1.0], "hspace": 0.12})

    day = windows[0][1][0].strftime("%Y-%m-%d")
    for path, times, mg in windows:
        off = args.offscale and os.path.basename(args.offscale) in path
        if off:
            continue
        first = mg[0]
        ax.axhspan(first - DOSE_BAND_MG, first + DOSE_BAND_MG,
                   xmin=0, xmax=1, color=BAND, zorder=0, alpha=0.0)
        ax.plot(times, mg, color=SERIES, lw=1.4, solid_capstyle="round")

    lo = min(min(mg) for p, t, mg in windows
             if not (args.offscale and os.path.basename(args.offscale) in p))
    ax.axhspan(lo, lo + 2 * DOSE_BAND_MG, color=BAND, zorder=0)
    ax.text(windows[0][1][0], lo + 2 * DOSE_BAND_MG, "  width of the full ±5 mg dose band",
            va="bottom", ha="left", fontsize=8, color=MUTED)

    for ev in args.event:
        clock, label = ev.split(",", 1)
        when = datetime.strptime(day + " " + clock, "%Y-%m-%d %H:%M:%S")
        for a in (ax, axd):
            a.axvline(when, color=MUTED, lw=0.8, ls=":")
        ax.text(when, ax.get_ylim()[1], " " + label, rotation=90,
                va="top", ha="right", fontsize=8, color=MUTED)

    ax.set_ylabel("balance reading (mg, as read)", color=INK)
    ax.set_title("Dose-gate hold: baseline wander vs wall clock (MDT), "
                 "zero mechanical shocks throughout", color=INK, fontsize=11)

    # bottom: end-to-end drift per window vs the launch condition
    mids, rates, labels = [], [], []
    for path, times, mg in windows:
        dur_min = (times[-1] - times[0]).total_seconds() / 60.0
        rate = (mg[-1] - mg[0]) / dur_min if dur_min else 0.0
        mids.append(times[0] + (times[-1] - times[0]) / 2)
        rates.append(rate)
        labels.append(os.path.basename(path))
    axd.axhspan(-LAUNCH_DRIFT_MG_MIN, LAUNCH_DRIFT_MG_MIN, color="#dcefdc",
                zorder=0)
    axd.axhline(0, color=MUTED, lw=0.6)
    for m, r, name in zip(mids, rates, labels):
        post = args.offscale and os.path.basename(args.offscale) in name
        axd.bar([m], [r], width=timedelta(minutes=2.4), color="none" if post
                else SERIES, edgecolor=SERIES, hatch="///" if post else None,
                linewidth=1.0)
    axd.text(mids[0], LAUNCH_DRIFT_MG_MIN, "  ±2 mg/min: every launch today "
             "was accepted inside this band "
             "(sulfate −1.6, AlSi10Mg +2.0, Si −325 +0.6)",
             va="bottom", fontsize=8, color=MUTED)
    axd.set_ylabel("end-to-end drift\n(mg/min)", color=INK)

    for a in (ax, axd):
        a.spines[["top", "right"]].set_visible(False)
        a.grid(axis="y", color="#eef0f4", lw=0.7)
        a.set_axisbelow(True)
        a.tick_params(colors=MUTED, labelsize=8)
        a.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
    axd.set_xlabel("lab wall clock (MDT), " + day, color=INK)

    fig.savefig(args.out, dpi=160, bbox_inches="tight")
    print("wrote", args.out)


if __name__ == "__main__":
    main()
