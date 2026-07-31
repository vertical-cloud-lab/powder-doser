#!/usr/bin/env python3
"""Plot an idle-scale capture: what the balance does with nobody dosing.

Input is a ``scale_stream.py`` log (see ``scale_stream_capture.py``)::

    python scripts/plot_scale_idle.py data/scale-idle/<run>/idle.log \\
        --out data/scale-idle/<run>/idle.png

Three panels, because three different questions get asked of this data:
mass excursion over time (drift), per-minute spread (is the bench quiet
right now?), and the histogram of reported values (how many scale counts
does an idle balance actually visit?).
"""

from __future__ import annotations

import argparse
import os
import sys
from collections import Counter

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import scale_stream_capture as ssc  # noqa: E402

SURFACE = "#fcfcfb"
INK = "#0b0b0b"
MUTED = "#52514e"
GRID = "#c3c2b7"
SERIES_1 = "#2a78d6"
SERIES_2 = "#eb6834"


def load(path):
    samples = []
    meta = {}
    with open(path, errors="replace") as handle:
        for line in handle:
            parsed = ssc.parse_line(line)
            if parsed is None:
                continue
            kind, payload = parsed
            if kind == "M":
                meta[payload[0]] = ssc.coerce_meta(payload[1])
            elif kind == "S":
                samples.append(payload)
    return samples, meta


def style(ax):
    ax.set_facecolor(SURFACE)
    ax.grid(True, color=GRID, linewidth=0.6, alpha=0.55)
    ax.set_axisbelow(True)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(GRID)
    ax.tick_params(colors=MUTED, labelsize=9)


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("log")
    p.add_argument("--out", default=None)
    p.add_argument("--title", default="Idle A&D HR-100A, powder-doser bench")
    args = p.parse_args(argv)

    samples, meta = load(args.log)
    valued = [s for s in samples if s.grams is not None]
    if not valued:
        raise SystemExit("no valued samples in " + args.log)

    t_min = np.array([s.t_ms for s in valued]) / 60000.0
    grams = np.array([s.grams for s in valued])
    baseline = float(np.median(grams))
    dev_mg = (grams - baseline) * 1000.0

    # Per-minute stats, computed from every sample the way the tier-2
    # aggregator does (so the plot and the stored aggregates agree).
    minute = (np.array([s.t_ms for s in valued]) // 60000).astype(int)
    minutes = sorted(set(minute.tolist()))
    ptp, std, counts = [], [], []
    for m in minutes:
        block = dev_mg[minute == m]
        ptp.append(float(block.max() - block.min()))
        std.append(float(block.std()))
        counts.append(int(block.size))

    n_missed = sum(1 for s in samples if s.flag in ("X", "O"))
    n_unstable = sum(1 for s in samples if s.flag == "U")
    span_min = (samples[-1].t_ms - samples[0].t_ms) / 60000.0
    rate = (len(samples) - 1) / (span_min * 60.0) if span_min else 0.0

    fig, axes = plt.subplots(3, 1, figsize=(10, 9),
                             gridspec_kw={"height_ratios": [2, 1, 1]})
    fig.patch.set_facecolor(SURFACE)

    ax = axes[0]
    style(ax)
    ax.plot(t_min, dev_mg, color=SERIES_1, linewidth=1.6)
    ax.axhline(0.0, color=MUTED, linewidth=1.0, alpha=0.5)
    ax.set_ylabel("deviation from median (mg)", color=MUTED, fontsize=10)
    ax.set_title(
        f"{args.title}\n{len(samples):,} polls over {span_min:.1f} min at "
        f"{rate:.2f} Hz  ·  median {baseline:.4f} g  ·  "
        f"{n_unstable} unstable, {n_missed} missed",
        color=INK, fontsize=12, loc="left")

    ax = axes[1]
    style(ax)
    ax.bar(minutes, ptp, color=SERIES_1, width=0.72, label="peak-to-peak")
    ax.plot(minutes, std, color=SERIES_2, linewidth=2.0, marker="o",
            markersize=5, label="std dev")
    ax.set_ylabel("per-minute spread (mg)", color=MUTED, fontsize=10)
    ax.set_xlabel("elapsed (min)", color=MUTED, fontsize=10)
    leg = ax.legend(frameon=False, fontsize=9, loc="upper right")
    for text in leg.get_texts():
        text.set_color(MUTED)

    ax = axes[2]
    style(ax)
    hist = Counter(np.round(dev_mg, 1))
    keys = sorted(hist)
    ax.bar(keys, [hist[k] for k in keys], color=SERIES_1,
           width=0.08 if len(keys) > 4 else 0.04)
    ax.set_ylabel("polls", color=MUTED, fontsize=10)
    ax.set_xlabel("reported value, deviation from median (mg)",
                  color=MUTED, fontsize=10)
    ax.set_title(f"{len(keys)} distinct values visited in {len(valued):,} "
                 f"polls  ·  scale resolution 0.1 mg",
                 color=INK, fontsize=10, loc="left")

    fig.tight_layout()
    out = args.out or os.path.splitext(args.log)[0] + ".png"
    fig.savefig(out, dpi=140, facecolor=SURFACE)
    print(f"wrote {out}")
    print(f"distinct_values={len(keys)} ptp_total_mg={np.ptp(dev_mg):.2f} "
          f"std_total_mg={dev_mg.std():.3f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
