#!/usr/bin/env python3
"""Cross-powder comparison figure for uniform powder-battery runs.

``plot_battery_results.py`` shows one powder in detail.  This one puts
several runs side by side on the axes that matter for the manuscript
(PR #97): the feed factor (mass per auger revolution) against tilt, and
the closed-loop dose outcome.

Powders in this dataset span orders of magnitude -- white rice flour
conveys ~37 mg per revolution at tilt 90 deg while brown rice flour
conveys less than the balance can resolve -- so panel A is logarithmic
and anything at or below the balance's 0.1 mg display resolution is
drawn at the detection limit and labelled as an upper bound rather than
silently plotted as a real small number.

Usage::

    python scripts/plot_battery_compare.py out.png run_a.json run_b.json ...
"""

import json
import sys
import textwrap

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# Reference palette (dataviz skill), light surface -- same as
# plot_battery_results.py so the figures read as one system.
SURFACE = "#fcfcfb"
TEXT_PRIMARY = "#0b0b0b"
TEXT_SECONDARY = "#52514e"
GRID = "#dcdbd6"
SERIES = ["#2a78d6", "#eb6834", "#1baf7a", "#9a5cd0"]
NOISE = "#9d9c95"
TARGET = "#e34948"

# The balance displays to 0.1 mg; half a display count is the smallest
# difference a single reading can express.
RESOLUTION_MG = 0.1
DETECTION_MG = RESOLUTION_MG / 2.0


def style(ax):
    ax.set_facecolor(SURFACE)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(GRID)
    ax.tick_params(colors=TEXT_SECONDARY, labelsize=9, length=3)
    ax.yaxis.grid(True, color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)


def rotation_rows(doc):
    """Block C summary rows (mass per 360 deg revolution), by tilt."""
    rows = [r for r in doc["host_summary"] if r["block"] == "C"]
    rows.sort(key=lambda r: r["tilt_deg"])
    return rows


def label_of(doc, docs=None):
    """Legend label; disambiguated when a powder appears more than once.

    Repeat runs of the same powder (a second auger, a re-run after a rig
    fix) share a ``powder_id``, so plotting two of them side by side
    would draw two identically-labelled bar groups.  When ``docs`` is
    given and the id repeats, the run date is appended.
    """
    name = doc.get("powder_id") or "run"
    if docs is None:
        return name
    siblings = [d for d in docs if (d.get("powder_id") or "run") == name]
    if len(siblings) < 2:
        return name
    return "{} ({})".format(name, (doc.get("started_utc") or "")[:10])


def panel_feed_factor(ax, docs):
    """Block C feed factor vs tilt, log scale, one bar group per powder."""
    tilts = sorted({r["tilt_deg"] for doc in docs for r in rotation_rows(doc)})
    width = 0.8 / max(len(docs), 1)

    for i, doc in enumerate(docs):
        by_tilt = {r["tilt_deg"]: r for r in rotation_rows(doc)}
        offset = (i - (len(docs) - 1) / 2.0) * width
        xs, values, censored = [], [], []
        for j, tilt in enumerate(tilts):
            row = by_tilt.get(tilt)
            if row is None:
                continue
            mg = row["mean_g"] * 1000.0
            xs.append(j + offset)
            values.append(max(mg, DETECTION_MG))
            censored.append(mg <= DETECTION_MG)
        ax.bar(xs, values, width=width * 0.9, color=SERIES[i % len(SERIES)],
               label=label_of(doc, docs),
               hatch=None)
        for x, value, is_censored in zip(xs, values, censored):
            ax.annotate(
                "< {:.1f}".format(RESOLUTION_MG) if is_censored
                else "{:.1f}".format(value),
                xy=(x, value), xytext=(0, 4), textcoords="offset points",
                ha="center", fontsize=8.5,
                color=TEXT_SECONDARY if is_censored else TEXT_PRIMARY)

    ax.axhline(DETECTION_MG, color=NOISE, linewidth=1.6,
               linestyle=(0, (4, 3)))
    ax.annotate("balance resolution ({:.1f} mg)".format(RESOLUTION_MG),
                xy=(-0.5, DETECTION_MG), xytext=(2, -12),
                textcoords="offset points", ha="left", fontsize=8.5,
                color=TEXT_SECONDARY)
    ax.set_yscale("log")
    ax.set_xticks(range(len(tilts)))
    ax.set_xticklabels(["{:.0f}°".format(t) for t in tilts])
    ax.set_xlabel("tube tilt (0° horizontal, 90° vertical)", fontsize=9.5,
                  color=TEXT_SECONDARY)
    ax.set_ylabel("mass per 360° revolution (mg, log)", fontsize=9.5,
                  color=TEXT_SECONDARY)
    ax.set_title("A  Block C — feed factor vs tilt (n=6 each, 30 RPM)",
                 fontsize=10.5, color=TEXT_PRIMARY, loc="left", pad=10)
    # Headroom above the tallest bar so the legend never lands on a bar
    # label -- calcium lactate's 47.3 mg bar at tilt 0 deg sat under an
    # "upper left" legend before this.
    ncol = min(len(docs), 2)
    rows = -(-len(docs) // ncol)
    bottom, top = ax.get_ylim()
    ax.set_ylim(bottom, top * (10.0 ** (0.75 * rows)))
    legend = ax.legend(frameon=False, fontsize=9, loc="upper left",
                       ncol=ncol, columnspacing=1.4)
    for text in legend.get_texts():
        text.set_color(TEXT_SECONDARY)


def panel_dose(ax, docs):
    """Block G: delivered mass per closed-loop 1 g dose, per powder."""
    target = 1.0
    xs, values, colors, labels = [], [], [], []
    groups = []
    position = 0
    for i, doc in enumerate(docs):
        start = position
        statuses = []
        for dose in doc["doses"]:
            xs.append(position)
            values.append(dose["dispensed_g"])
            colors.append(SERIES[i % len(SERIES)])
            # Just the dose number per tick -- the exit status goes under
            # the powder name, since printing it three times per powder
            # collides with the neighbouring group.
            labels.append(str(dose["n"] + 1))
            statuses.append(dose["status"])
            target = dose["target_g"]
            position += 1
        if position > start:
            unique = sorted(set(statuses))
            caption = "{}\n{}".format(
                label_of(doc, docs),
                unique[0] if len(unique) == 1 else "/".join(unique))
            groups.append(((start + position - 1) / 2.0, caption,
                           SERIES[i % len(SERIES)]))
        position += 0.6

    ax.bar(xs, values, width=0.62, color=colors)
    ax.axhline(target, color=TARGET, linewidth=2, linestyle=(0, (4, 3)))
    ax.annotate("target {:.3f} g".format(target), xy=(min(xs, default=0), target),
                xytext=(0, 6), textcoords="offset points", ha="left",
                fontsize=8.5, color=TEXT_SECONDARY)
    for x, value in zip(xs, values):
        ax.annotate("{:.3f}".format(value), xy=(x, value), xytext=(0, 5),
                    textcoords="offset points", ha="center", fontsize=8.5,
                    color=TEXT_PRIMARY)
    # Repeat-run labels carry a date and get long; stagger alternate
    # groups vertically so neighbouring captions cannot overlap.
    longest = max((len(n.split("\n")[0]) for _, n, _ in groups), default=0)
    size = 9.5 if longest <= 18 else 8.0
    for k, (x, name, color) in enumerate(groups):
        dy = -34 if (longest <= 18 or k % 2 == 0) else -58
        ax.annotate(name, xy=(x, 0), xytext=(0, dy),
                    textcoords="offset points", ha="center", fontsize=size,
                    color=color)
    ax.set_xticks(xs)
    ax.set_xticklabels(labels, fontsize=8)
    ax.set_ylabel("delivered mass (g)", fontsize=9.5, color=TEXT_SECONDARY)
    ax.set_ylim(0, target * 1.25)
    ax.set_title("B  Block G — 1 g closed-loop doses, frozen salt-tuned "
                 "controller", fontsize=10.5, color=TEXT_PRIMARY, loc="left",
                 pad=10)


def main(out_path, paths):
    docs = [json.load(open(p)) for p in paths]

    fig, axes = plt.subplots(1, 2, figsize=(13.0, 5.2), facecolor=SURFACE)
    for ax in axes:
        style(ax)

    panel_feed_factor(axes[0], docs)
    panel_dose(axes[1], docs)

    # Four dated labels overrun the figure width on one line, so the run
    # list wraps instead of being clipped at the right edge.
    title = "Uniform powder battery — cross-powder comparison ({})".format(
        ", ".join(label_of(d, docs) for d in docs))
    fig.suptitle(textwrap.fill(title, 108), fontsize=13, color=TEXT_PRIMARY,
                 x=0.008, ha="left", va="top", y=0.985)
    top = 0.94 if len(title) <= 108 else 0.90
    fig.tight_layout(rect=(0, 0, 1, top))
    fig.savefig(out_path, dpi=170, facecolor=SURFACE)
    print("wrote {}".format(out_path))


if __name__ == "__main__":
    if len(sys.argv) < 3:
        raise SystemExit(__doc__)
    main(sys.argv[1], sys.argv[2:])
