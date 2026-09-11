#!/usr/bin/env python3
"""Per-revolution sequence within block C, which the block mean hides.

``plot_battery_results.py`` panel A reduces each tilt to a mean and an
RSD.  That is the right summary only when the six revolutions at a tilt
are draws from one distribution, and several runs so far are nothing of
the sort:

* white rice flour *charges* -- 1.7 mg on revolution 1, 70 mg by
  revolution 3, as the delivery section fills from empty;
* carboxymethyl cellulose at tilt 90 deg *decays* -- 39.0 mg on
  revolution 1 then 7.4, 4.0, 1.8, 1.4, 2.5, so its 9.3 mg mean
  describes no revolution that actually happened;
* brown rice flour arrives as isolated clump releases with most
  revolutions at exactly 0.0000 g.

All three read as "a mean with a big RSD" in panel A and as three
completely different mechanisms here, so plot the sequence before
quoting a feed factor.

Block D is overlaid where it exists: it runs at tilt 45 deg immediately
after block C ends at 90 deg, so it distinguishes a *tilt* effect (feed
returns when the tube comes back to 45 deg) from a depleted hopper (it
does not).

Usage::

    python scripts/plot_battery_sequence.py \\
        data/battery/<stamp>_<powder-id>/run_<powder-id>.json \\
        data/battery/<stamp>_<powder-id>/<powder-id>_sequence.png
"""

import json
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

SURFACE = "#fcfcfb"
TEXT_PRIMARY = "#0b0b0b"
TEXT_SECONDARY = "#52514e"
GRID = "#dcdbd6"
SERIES = ["#2a78d6", "#eb6834", "#1baf7a"]
NOISE = "#9d9c95"

# The balance displays to 0.1 mg.
RESOLUTION_MG = 0.1


def style(ax):
    ax.set_facecolor(SURFACE)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(GRID)
    ax.tick_params(colors=TEXT_SECONDARY, labelsize=9, length=3)
    ax.yaxis.grid(True, color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)


def rotation_series(doc):
    """Block C deltas in mg, grouped by tilt, in the order they ran."""
    rows = [r for r in doc["trials"]
            if r["block"] == "C" and r["phase"] == "rotation"]
    tilts = sorted({r["tilt_deg"] for r in rows})
    return [(t, [r["delta_g"] * 1000.0 for r in rows if r["tilt_deg"] == t])
            for t in tilts]


def speed_series(doc):
    """Block D deltas in mg per revolution, labelled by RPM."""
    out = []
    for row in doc["trials"]:
        if row["block"] != "D" or not row.get("action"):
            continue
        revs = float(row["action"]) or 1.0
        out.append((row["rpm"], row["delta_g"] * 1000.0 / revs))
    return out


def trend(values):
    """Describe the within-tilt shape, for the caption."""
    if len(values) < 3:
        return None
    if max(values) <= RESOLUTION_MG:
        return "below resolution"
    # Check intermittency first.  Brown rice flour delivers exactly
    # 0.0000 g on most revolutions with an occasional clump release, and
    # comparing its first revolution against its last three then calls
    # that "charging" or "decaying" depending purely on where the clumps
    # happened to land.  Neither describes the mechanism.
    below = sum(1 for v in values if v <= RESOLUTION_MG)
    if below * 2 >= len(values):
        return "intermittent"
    head, tail = values[0], sum(values[-3:]) / 3.0
    if tail > max(head, RESOLUTION_MG) * 2.0:
        return "charging"
    if head > max(tail, RESOLUTION_MG) * 2.0:
        return "decaying"
    return "steady"


def main(run_path, out_path):
    doc = json.load(open(run_path))
    series = rotation_series(doc)
    speeds = speed_series(doc)

    fig, ax = plt.subplots(figsize=(9.0, 5.0), facecolor=SURFACE)
    style(ax)

    notes = []
    for i, (tilt, values) in enumerate(series):
        xs = range(1, len(values) + 1)
        colour = SERIES[i % len(SERIES)]
        ax.plot(xs, values, marker="o", markersize=7, linewidth=2,
                color=colour, label="tilt {:.0f}°".format(tilt))
        shape = trend(values)
        if shape:
            notes.append("{:.0f}°: {}".format(tilt, shape))

    if speeds:
        # One point per block D burst, plotted past the block C run so the
        # recovery (or not) at tilt 45 deg is visible on the same axis.
        offset = max(len(v) for _, v in series) + 1.5
        for j, (rpm, mg_per_rev) in enumerate(speeds):
            ax.plot([offset + j], [mg_per_rev], marker="D", markersize=8,
                    color=TEXT_SECONDARY, linestyle="none",
                    label="block D, tilt 45° (per rev)" if j == 0 else None)
            ax.annotate("{:.0f} RPM".format(rpm),
                        xy=(offset + j, mg_per_rev), xytext=(0, 9),
                        textcoords="offset points", ha="center",
                        fontsize=8, color=TEXT_SECONDARY)
        ax.axvline(offset - 0.75, color=GRID, linewidth=1.2,
                   linestyle=(0, (4, 3)))

    ax.axhline(RESOLUTION_MG, color=NOISE, linewidth=1.5,
               linestyle=(0, (4, 3)))
    ax.annotate("balance resolution (0.1 mg)", xy=(1, RESOLUTION_MG),
                xytext=(2, 4), textcoords="offset points", fontsize=8,
                color=TEXT_SECONDARY, va="bottom")

    ax.set_yscale("symlog", linthresh=RESOLUTION_MG)
    # Deltas are non-negative, and symlog otherwise spends half the
    # canvas on a mirrored negative decade nothing is plotted in.
    everything = [v for _, values in series for v in values] + \
                 [v for _, v in speeds]
    ax.set_ylim(0, max(everything + [RESOLUTION_MG]) * 2.5)
    ax.set_xlabel("360° revolution within the block (block D bursts at right)",
                  fontsize=9.5, color=TEXT_SECONDARY)
    ax.set_ylabel("mass delivered (mg, symlog)", fontsize=9.5,
                  color=TEXT_SECONDARY)
    ax.legend(frameon=False, fontsize=9, labelcolor=TEXT_SECONDARY,
              loc="lower left")

    ax.set_title("{} — block C revolution by revolution".format(doc["powder"]),
                 fontsize=11, color=TEXT_PRIMARY, loc="left", pad=16)
    if notes:
        # The per-tilt shape is the point of the figure, so it gets its
        # own line rather than being appended until the title overruns.
        ax.annotate(" · ".join(notes), xy=(0, 1), xycoords="axes fraction",
                    xytext=(0, 6), textcoords="offset points",
                    fontsize=9.5, color=TEXT_SECONDARY, va="bottom")

    fig.tight_layout()
    fig.savefig(out_path, dpi=170, facecolor=SURFACE)
    print("wrote {}".format(out_path))


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    main(sys.argv[1], sys.argv[2])
