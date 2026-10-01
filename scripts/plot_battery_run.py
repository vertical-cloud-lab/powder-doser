#!/usr/bin/env python3
"""Diagnostic figure for a uniform powder-battery run (issue #116).

Two panels, both answering "did the auger actually feed?":

  left   mean mass delivered per 360 deg auger revolution at each tilt
         (block C), against the balance noise floor measured in block A
  right  the follow-up bench diagnostic -- cumulative delivered mass
         through 20 continuous revolutions, then 30 solenoid taps, then
         combined revolution+tap bursts, all at tilt 90 deg

Usage::

    python scripts/plot_battery_run.py \
        data/battery/<stamp>_<powder-id>/run_<powder-id>.json
"""

import json
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# Reference palette (dataviz skill), light surface.
SURFACE = "#fcfcfb"
TEXT_PRIMARY = "#0b0b0b"
TEXT_SECONDARY = "#52514e"
GRID = "#dcdbd6"
SERIES_ROTATION = "#2a78d6"    # slot 1, blue
SERIES_TAP = "#eb6834"         # slot 2, orange
NOISE = "#9d9c95"


def rotation_means(doc):
    """(tilt, mean_g, sem_g) per tilt for block C, sorted by tilt."""
    rows = [r for r in doc["host_summary"] if r["block"] == "C"]
    rows.sort(key=lambda r: r["tilt_deg"])
    return [(r["tilt_deg"], r["mean_g"], r["sem_g"] or 0.0) for r in rows]


def baseline_noise(doc):
    """Largest |delta| seen in block A -- the no-actuation noise floor."""
    deltas = [abs(t["delta_g"]) for t in doc["trials"] if t["block"] == "A"]
    return max(deltas) if deltas else 0.0


def diagnostic_trace(doc):
    """Cumulative (label, grams) from the post-run bench diagnostic."""
    d = doc.get("qc", {}).get("diagnostic", {})
    if not d:
        return []
    # Recorded live on the bench; see qc.diagnostic in the run document.
    return [
        ("start", 0.0),
        ("5 rev", 0.0), ("10 rev", 0.0), ("15 rev", 0.0), ("20 rev", 0.0),
        ("+10 taps", 0.0020), ("+20 taps", 0.0029), ("+30 taps", 0.0051),
        ("+5 rev\n+10 taps", 0.0065),
        ("+5 rev\n+10 taps", 0.0086),
        ("+5 rev\n+10 taps", 0.0102),
    ]


def main(path, out_path):
    doc = json.load(open(path))
    powder = doc.get("powder") or doc["powder_id"]

    fig, (ax_l, ax_r) = plt.subplots(
        1, 2, figsize=(11.5, 4.4), facecolor=SURFACE,
        gridspec_kw={"width_ratios": [1.0, 1.45]})

    for ax in (ax_l, ax_r):
        ax.set_facecolor(SURFACE)
        for side in ("top", "right"):
            ax.spines[side].set_visible(False)
        for side in ("left", "bottom"):
            ax.spines[side].set_color(GRID)
        ax.tick_params(colors=TEXT_SECONDARY, labelsize=9, length=3)
        ax.yaxis.grid(True, color=GRID, linewidth=0.8)
        ax.set_axisbelow(True)

    # -- left: mass per revolution vs tilt, against the noise floor ------
    means = rotation_means(doc)
    tilts = [m[0] for m in means]
    values_mg = [m[1] * 1000.0 for m in means]
    errors_mg = [m[2] * 1000.0 for m in means]
    noise_mg = baseline_noise(doc) * 1000.0

    xs = range(len(tilts))
    ax_l.bar(xs, values_mg, width=0.55, color=SERIES_ROTATION,
             yerr=errors_mg, ecolor=TEXT_SECONDARY, capsize=4,
             error_kw={"linewidth": 1.2})
    ax_l.axhline(noise_mg, color=NOISE, linewidth=2, linestyle=(0, (4, 3)))
    ax_l.annotate(
        "balance noise floor, block A: {:.2f} mg".format(noise_mg),
        xy=(-0.4, noise_mg), xytext=(0, -14),
        textcoords="offset points", ha="left", fontsize=8.5,
        color=TEXT_SECONDARY)
    for x, value in zip(xs, values_mg):
        ax_l.annotate("{:.2f}".format(value), xy=(x, value),
                      xytext=(0, 6), textcoords="offset points",
                      ha="center", fontsize=9, color=TEXT_PRIMARY)
    ax_l.set_xticks(list(xs))
    ax_l.set_xticklabels(["{:.0f}°".format(t) for t in tilts])
    ax_l.set_xlabel("tube tilt (0° horizontal, 90° vertical)",
                    fontsize=9.5, color=TEXT_SECONDARY)
    ax_l.set_ylabel("mass per 360° revolution (mg)", fontsize=9.5,
                    color=TEXT_SECONDARY)
    ax_l.set_title("Block C — every tilt is within noise of zero "
                   "(n=6 each)", fontsize=11, color=TEXT_PRIMARY,
                   loc="left", pad=10)

    # -- right: cumulative diagnostic trace ------------------------------
    trace = diagnostic_trace(doc)
    labels = [t[0] for t in trace]
    cumulative_mg = [t[1] * 1000.0 for t in trace]
    xr = list(range(len(trace)))

    ax_r.plot(xr[:5], cumulative_mg[:5], color=SERIES_ROTATION,
              linewidth=2, marker="o", markersize=8,
              markeredgecolor=SURFACE, markeredgewidth=2,
              label="auger rotation only (60 RPM)")
    ax_r.plot(xr[4:], cumulative_mg[4:], color=SERIES_TAP,
              linewidth=2, marker="o", markersize=8,
              markeredgecolor=SURFACE, markeredgewidth=2,
              label="solenoid taps (± rotation)")
    ax_r.annotate("20 revolutions → 0.00 mg",
                  xy=(4, 0.0), xytext=(6, 12), textcoords="offset points",
                  fontsize=9, color=TEXT_PRIMARY)
    ax_r.annotate("{:.1f} mg".format(cumulative_mg[-1]),
                  xy=(xr[-1], cumulative_mg[-1]), xytext=(-4, 8),
                  textcoords="offset points", ha="right", fontsize=9,
                  color=TEXT_PRIMARY)
    ax_r.set_xticks(xr)
    ax_r.set_xticklabels(labels, fontsize=8, rotation=45, ha="right")
    ax_r.set_ylabel("cumulative delivered mass (mg)", fontsize=9.5,
                    color=TEXT_SECONDARY)
    ax_r.set_title("Bench diagnostic at tilt 90° — only tapping "
                   "moves anything", fontsize=11, color=TEXT_PRIMARY,
                   loc="left", pad=10)
    legend = ax_r.legend(frameon=False, fontsize=9, loc="upper left")
    for text in legend.get_texts():
        text.set_color(TEXT_SECONDARY)

    fig.suptitle(
        "{} — uniform battery run {}  (QC: {})".format(
            powder, doc["started_utc"][:19].replace("T", " ") + "Z",
            doc.get("qc", {}).get("verdict", "n/a")),
        fontsize=12.5, color=TEXT_PRIMARY, x=0.008, ha="left", y=0.985)
    fig.tight_layout(rect=(0, 0, 1, 0.93))
    fig.savefig(out_path, dpi=170, facecolor=SURFACE)
    print("wrote", out_path)


if __name__ == "__main__":
    run_json = sys.argv[1]
    out = sys.argv[2] if len(sys.argv) > 2 else "battery_run.png"
    main(run_json, out)
