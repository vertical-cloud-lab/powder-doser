#!/usr/bin/env python3
"""Results figure for a uniform powder-battery run that actually fed.

Companion to ``plot_battery_run.py``, which is the *did it feed at all?*
diagnostic.  This one is the four-panel per-powder result used in the
manuscript (PR #97):

  A  block C -- mass per 360 deg auger revolution vs tilt, with SEM
  B  block D -- mass-vs-time traces at each auger speed (pulsation)
  C  block E -- mg per tap vs the measured re-feed rotation, per tilt
  D  block G -- closed-loop 1 g doses against the target

Usage::

    python scripts/plot_battery_results.py \
        data/battery/<stamp>_<powder-id>/run_<powder-id>.json \
        data/battery/<stamp>_<powder-id>/<powder-id>_results.png
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
# Categorical slots 1-3: the trio validated all-pairs for CVD.
SERIES = ["#2a78d6", "#eb6834", "#1baf7a"]
NOISE = "#9d9c95"
TARGET = "#e34948"


def summary_rows(doc, block, phase=None):
    rows = [r for r in doc["host_summary"] if r["block"] == block
            and (phase is None or r["phase"] == phase)]
    rows.sort(key=lambda r: r["tilt_deg"])
    return rows


def baseline_noise(doc):
    """Largest |delta| seen in block A -- the no-actuation noise floor."""
    deltas = [abs(t["delta_g"]) for t in doc["trials"] if t["block"] == "A"]
    return max(deltas) if deltas else 0.0


def style(ax):
    ax.set_facecolor(SURFACE)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(GRID)
    ax.tick_params(colors=TEXT_SECONDARY, labelsize=9, length=3)
    ax.yaxis.grid(True, color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)


def panel_rotation(ax, doc):
    """Block C: mg per revolution vs tilt."""
    rows = summary_rows(doc, "C")
    xs = range(len(rows))
    values = [r["mean_g"] * 1000.0 for r in rows]
    errors = [(r["sem_g"] or 0.0) * 1000.0 for r in rows]
    noise_mg = baseline_noise(doc) * 1000.0

    ax.bar(xs, values, width=0.55, color=SERIES[0], yerr=errors,
           ecolor=TEXT_SECONDARY, capsize=4, error_kw={"linewidth": 1.2})
    if noise_mg > 0:
        ax.axhline(noise_mg, color=NOISE, linewidth=2, linestyle=(0, (4, 3)))
    for x, value, error, row in zip(xs, values, errors, rows):
        ax.annotate("{:.1f}\nRSD {:.0f}%".format(value, row["rsd_pct"] or 0),
                    xy=(x, value + error), xytext=(0, 8),
                    textcoords="offset points", ha="center", fontsize=8.5,
                    color=TEXT_PRIMARY)
    ax.set_xticks(list(xs))
    ax.set_xticklabels(["{:.0f}°".format(r["tilt_deg"]) for r in rows])
    ax.set_xlabel("tube tilt (0° horizontal, 90° vertical)",
                  fontsize=9.5, color=TEXT_SECONDARY)
    ax.set_ylabel("mass per 360° revolution (mg)", fontsize=9.5,
                  color=TEXT_SECONDARY)
    ax.set_ylim(0, max(values) * 1.45 if values else 1)
    ax.set_title("A  Block C — feed factor rises with tilt (n=6 each, "
                 "30 RPM)", fontsize=10.5, color=TEXT_PRIMARY, loc="left",
                 pad=10)


def panel_speed(ax, doc):
    """Block D: mass-vs-time trace at each auger speed."""
    polls = [p for p in doc["polls"] if p["block"] == "D"]
    rpms = sorted({p["rpm"] for p in polls})
    for i, rpm in enumerate(rpms):
        trace = [p for p in polls if p["rpm"] == rpm]
        if not trace:
            continue
        t0 = trace[0]["t_ms"]
        g0 = trace[0]["grams"]
        ax.plot([(p["t_ms"] - t0) / 1000.0 for p in trace],
                [(p["grams"] - g0) * 1000.0 for p in trace],
                color=SERIES[i % len(SERIES)], linewidth=2,
                marker="o", markersize=4.5, markeredgecolor=SURFACE,
                markeredgewidth=1.2,
                label="{:.0f} RPM".format(rpm))
        ax.annotate("{:.0f} RPM".format(rpm),
                    xy=((trace[-1]["t_ms"] - t0) / 1000.0,
                        (trace[-1]["grams"] - g0) * 1000.0),
                    xytext=(5, -2), textcoords="offset points",
                    fontsize=8.5, color=TEXT_SECONDARY)
    ax.set_xlabel("time within the 3-revolution burst (s)", fontsize=9.5,
                  color=TEXT_SECONDARY)
    ax.set_ylabel("delivered mass (mg)", fontsize=9.5,
                  color=TEXT_SECONDARY)
    ax.set_title("B  Block D — mass vs time at each auger speed "
                 "(tilt 45°)", fontsize=10.5, color=TEXT_PRIMARY,
                 loc="left", pad=10)
    legend = ax.legend(frameon=False, fontsize=9, loc="lower right")
    for text in legend.get_texts():
        text.set_color(TEXT_SECONDARY)


def panel_tap(ax, doc):
    """Block E: tap quantum against the re-feed rotation, per tilt."""
    taps = summary_rows(doc, "E", "tap")
    refeeds = summary_rows(doc, "E", "refeed")
    tilts = [r["tilt_deg"] for r in taps]
    xs = range(len(tilts))
    width = 0.36

    for offset, rows, label, color in (
            (-width / 2, refeeds, "360° re-feed rotation", SERIES[0]),
            (+width / 2, taps, "single tap", SERIES[1])):
        values = [r["mean_g"] * 1000.0 for r in rows]
        errors = [(r["sem_g"] or 0.0) * 1000.0 for r in rows]
        ax.bar([x + offset for x in xs], values, width=width - 0.02,
               color=color, yerr=errors, ecolor=TEXT_SECONDARY,
               capsize=4, error_kw={"linewidth": 1.2}, label=label)
        for x, value in zip(xs, values):
            ax.annotate("{:.2f}".format(value), xy=(x + offset, value),
                        xytext=(0, 5), textcoords="offset points",
                        ha="center", fontsize=8.5, color=TEXT_PRIMARY)
    ax.set_xticks(list(xs))
    ax.set_xticklabels(["{:.0f}°".format(t) for t in tilts])
    ax.set_xlabel("tube tilt", fontsize=9.5, color=TEXT_SECONDARY)
    ax.set_ylabel("mass per action (mg)", fontsize=9.5,
                  color=TEXT_SECONDARY)
    ax.set_title("C  Block E — tapping contributes almost nothing "
                 "(n=8 each)", fontsize=10.5, color=TEXT_PRIMARY,
                 loc="left", pad=10)
    legend = ax.legend(frameon=False, fontsize=9, loc="upper left")
    for text in legend.get_texts():
        text.set_color(TEXT_SECONDARY)


def panel_dose(ax, doc):
    """Block G: closed-loop doses against the target."""
    doses = doc["doses"]
    xs = range(len(doses))
    values = [d["dispensed_g"] for d in doses]
    target = doses[0]["target_g"] if doses else 1.0

    ax.bar(xs, values, width=0.5, color=SERIES[0])
    ax.axhline(target, color=TARGET, linewidth=2, linestyle=(0, (4, 3)))
    ax.annotate("target {:.3f} g".format(target), xy=(-0.45, target),
                xytext=(0, 6), textcoords="offset points", ha="left",
                fontsize=8.5, color=TEXT_SECONDARY)
    for x, dose in zip(xs, doses):
        ax.annotate("{:.4f} g\n({:+.3f} g)\n{}".format(
                        dose["dispensed_g"], dose["error_g"],
                        dose["status"]),
                    xy=(x, dose["dispensed_g"]), xytext=(0, -46),
                    textcoords="offset points", ha="center", fontsize=8.5,
                    color="#ffffff")
    ax.set_xticks(list(xs))
    ax.set_xticklabels(["dose {}\n{:.0f} s".format(d["n"] + 1, d["elapsed_s"])
                        for d in doses], fontsize=9)
    ax.set_ylabel("delivered mass (g)", fontsize=9.5,
                  color=TEXT_SECONDARY)
    ax.set_ylim(0, max(values + [target]) * 1.2)
    ax.set_title("D  Block G — three-phase doses run out of fine-phase "
                 "budget", fontsize=10.5, color=TEXT_PRIMARY, loc="left",
                 pad=10)


def main(path, out_path):
    doc = json.load(open(path))
    powder = doc.get("powder") or doc["powder_id"]

    fig, axes = plt.subplots(2, 2, figsize=(12.6, 8.6), facecolor=SURFACE)
    for ax in axes.flat:
        style(ax)

    panel_rotation(axes[0][0], doc)
    panel_speed(axes[0][1], doc)
    panel_tap(axes[1][0], doc)
    panel_dose(axes[1][1], doc)

    fig.suptitle(
        "{} — uniform powder battery, {}Z".format(
            powder, doc["started_utc"][:19].replace("T", " ")),
        fontsize=13, color=TEXT_PRIMARY, x=0.008, ha="left", y=0.985)
    fig.tight_layout(rect=(0, 0, 1, 0.955))
    fig.savefig(out_path, dpi=170, facecolor=SURFACE)
    print("wrote", out_path)


if __name__ == "__main__":
    run_json = sys.argv[1]
    out = sys.argv[2] if len(sys.argv) > 2 else "battery_results.png"
    main(run_json, out)
