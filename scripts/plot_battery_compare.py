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

Pass ``--valid-only`` to drop runs whose
``qc.valid_for_cross_powder_comparison`` is false, which is what you
want when globbing the whole of ``data/battery/``::

    python scripts/plot_battery_compare.py --valid-only \\
        data/battery/battery_compare_all.png data/battery/*/run_*.json
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
# Eleven slots.  Started at four, silently repainted a fifth powder the
# same blue as the first, then grew one slot at a time as powders were
# added: the eighth (brown) for the first non-food-safe powder
# (alsi10mg), the ninth (olive) for sodium sulfate, the tenth (teal) for
# silicon, the eleventh (slate) for the 2026-08-21 alsi10mg re-run.
# Validated as an ordered set for the adjacent pairlist a grouped bar
# chart uses -- adjacent is the bar that matters, since consecutive
# powders are the bars that touch, and every bar also carries a direct
# value label.  The slate is now the set's worst adjacent pair and is
# still comfortable: 7.57:1 against the surface, 22.0 dE from the teal
# in normal vision, 12.6 dE under simulated deuteranopia and 13.1 under
# protanopia.  A second brown scored higher still on CVD separation but
# was rejected -- two browns read as one series to normal vision
# whatever dE says.  The green (#1baf7a, 2.74:1) and the pink (#e87ba4,
# 2.62:1) sit under 3:1 contrast, which the direct bar labels cover.
# Red is left out on purpose -- it is TARGET below, and a series must
# not wear it.
#
# These separations are pinned by scripts/tests/test_plot_battery_compare.py
# rather than asserted here, because a comment saying "validated" is
# exactly what failed to stop the fifth powder being repainted the first
# powder's blue.  Note the dE figures depend on the dichromat model; the
# test states the model it uses.
#
# Eleven is the end of the road for stretching this: the next powder
# should get per-batch facets rather than a twelfth slot, because the
# remaining unused hues all land inside an existing series under CVD.
# Beyond eleven this warns rather than cycling.
SERIES = ["#2a78d6", "#eb6834", "#1baf7a", "#9a5cd0",
          "#e87ba4", "#008300", "#4a3aa7", "#8c5a2b", "#a88700",
          "#00798a", "#3f5566"]
NOISE = "#9d9c95"
TARGET = "#e34948"

# The balance displays to 0.1 mg; half a display count is the smallest
# difference a single reading can express.
RESOLUTION_MG = 0.1
DETECTION_MG = RESOLUTION_MG / 2.0

# Vertical offsets (points) cycled across the doses within one powder so
# their value labels do not overlap.  The cycle length must not divide the
# number of doses in a way that puts two adjacent bars on one baseline, so
# it is a two-element alternation and adjacent entries always differ.
DOSE_LABEL_DY = (5, 17)


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
        # Ten powders share a tilt group, so a bar is narrower than its own
        # horizontal value label and neighbours run together into digit
        # soup ("34.351.257.2").  Staggering the offset is not enough --
        # it is measured from each bar's own top, so two bars of similar
        # height end up staggered onto each other anyway ("3710.9" at
        # tilt 90 deg).  Rotating the labels makes a label about as wide
        # as its font is tall, which fits the bar slot whatever the
        # values do, and the problem cannot come back as powders are
        # added.
        for x, value, is_censored in zip(xs, values, censored):
            ax.annotate(
                "< {:.1f}".format(RESOLUTION_MG) if is_censored
                else "{:.1f}".format(value),
                xy=(x, value), xytext=(0, 4), textcoords="offset points",
                ha="center", va="bottom", rotation=90, fontsize=8.5,
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
    # "upper left" legend before this.  The extra 0.6 decade is for the
    # rotated labels above, which stand roughly five times taller than
    # the horizontal ones this allowance was first sized for.
    ncol = min(len(docs), 2)
    rows = -(-len(docs) // ncol)
    bottom, top = ax.get_ylim()
    ax.set_ylim(bottom, top * (10.0 ** (0.75 * rows + 0.6)))
    legend = ax.legend(frameon=False, fontsize=9, loc="upper left",
                       ncol=ncol, columnspacing=1.4)
    for text in legend.get_texts():
        text.set_color(TEXT_SECONDARY)


def panel_dose(ax, docs):
    """Block G: delivered mass per closed-loop 1 g dose, per powder."""
    target = 1.0
    xs, values, colors, labels, label_dy = [], [], [], [], []
    groups = []
    position = 0
    for i, doc in enumerate(docs):
        start = position
        statuses = []
        for k, dose in enumerate(doc["doses"]):
            xs.append(position)
            values.append(dose["dispensed_g"])
            colors.append(SERIES[i % len(SERIES)])
            # Just the dose number per tick -- the exit status goes under
            # the powder name, since printing it three times per powder
            # collides with the neighbouring group.
            labels.append(str(dose["n"] + 1))
            # Three doses of the same powder land within a few mg of each
            # other, so their "0.995" labels overlap into an unreadable
            # run of digits (salt, calcium lactate, xanthan gum all did).
            # Alternate the vertical offset so no two adjacent labels
            # share a baseline.
            label_dy.append(DOSE_LABEL_DY[k % len(DOSE_LABEL_DY)])
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

    if not xs:
        # Block G is skipped whenever the bench is too noisy for a
        # multi-minute dose against a +/-5 mg band, so a facet can have
        # no doses at all.  An empty axes reads as "every dose delivered
        # zero", which is the opposite of "no dose was attempted".
        ax.text(0.5, 0.5, "no closed-loop doses recorded\n"
                          "(block G not run for these powders)",
                transform=ax.transAxes, ha="center", va="center",
                fontsize=10, color=TEXT_SECONDARY)

    ax.bar(xs, values, width=0.62, color=colors)
    ax.axhline(target, color=TARGET, linewidth=2, linestyle=(0, (4, 3)))
    ax.annotate("target {:.3f} g".format(target), xy=(min(xs, default=0), target),
                xytext=(0, 6), textcoords="offset points", ha="left",
                fontsize=8.5, color=TEXT_SECONDARY)
    for x, value, dy in zip(xs, values, label_dy):
        ax.annotate("{:.3f}".format(value), xy=(x, value), xytext=(0, dy),
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


def valid_for_comparison(doc):
    """Whether a run document is cleared for the cross-powder dataset."""
    return bool(doc.get("qc", {}).get("valid_for_cross_powder_comparison"))


def batch_of(doc):
    """Fill-container batch a run belongs to, e.g. ``metal-2026-08``."""
    return doc.get("batch") or "unbatched"


def group_by_batch(docs):
    """Runs grouped by batch, batches ordered by their first run.

    Ordering by first appearance rather than alphabetically keeps the
    facets in the order the work actually happened, which is how the run
    log and the issue thread read.
    """
    order, groups = [], {}
    for doc in docs:
        key = batch_of(doc)
        if key not in groups:
            order.append(key)
            groups[key] = []
        groups[key].append(doc)
    return [(key, groups[key]) for key in order]


def main(out_path, paths, valid_only=False, facet=None):
    docs = [json.load(open(p)) for p in paths]
    if valid_only:
        # Three of the runs so far are retracted no-feed attempts.  A
        # glob over data/battery/*/run_*.json otherwise plots them beside
        # real measurements with nothing marking them as withdrawn.
        kept = [d for d in docs if valid_for_comparison(d)]
        for doc in docs:
            if doc not in kept:
                print("skipping {} ({})".format(
                    doc.get("powder_id"),
                    doc.get("qc", {}).get("verdict", "unreviewed")))
        docs = kept
    if not docs:
        raise SystemExit("no runs to plot")
    # The palette is eleven slots and stretching it further was ruled
    # out: the remaining unused hues all land inside an existing series
    # under CVD.  So past eleven the figure facets by batch instead of
    # repainting a powder someone else's colour.  Colours only have to be
    # distinct *within* a facet, so each batch restarts the palette.
    if facet is None:
        facet = len(docs) > len(SERIES)
    if facet:
        return _plot_faceted(out_path, docs)
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


def _plot_faceted(out_path, docs):
    """One row of panels per batch, each row restarting the palette."""
    groups = group_by_batch(docs)
    over = [key for key, members in groups if len(members) > len(SERIES)]
    if over:
        # Faceting bought headroom; it did not make the palette infinite.
        # If a single batch outgrows it, say so rather than cycling
        # inside the facet, which is the original bug at smaller scale.
        print("WARNING: batch(es) {} exceed {} colours even faceted -- "
              "split those by sub-batch or date."
              .format(", ".join(over), len(SERIES)))
    rows = len(groups)
    fig, axes = plt.subplots(rows, 2, figsize=(13.0, 4.6 * rows),
                             facecolor=SURFACE, squeeze=False)
    for row, (key, members) in enumerate(groups):
        for ax in axes[row]:
            style(ax)
        panel_feed_factor(axes[row][0], members)
        panel_dose(axes[row][1], members)
        axes[row][0].set_ylabel("{}\n{}".format(
            key, axes[row][0].get_ylabel()))
    title = ("Uniform powder battery — cross-powder comparison, "
             "{} runs in {} batches ({})").format(
                 len(docs), len(groups),
                 "; ".join("{}: {}".format(
                     key, ", ".join(label_of(d, members) for d in members))
                     for key, members in groups))
    fig.suptitle(textwrap.fill(title, 108), fontsize=13, color=TEXT_PRIMARY,
                 x=0.008, ha="left", va="top", y=0.995)
    lines = len(textwrap.wrap(title, 108))
    fig.tight_layout(rect=(0, 0, 1, 1 - 0.018 * (lines + 1)))
    fig.savefig(out_path, dpi=170, facecolor=SURFACE)
    print("wrote {} ({} batch facets)".format(out_path, len(groups)))


if __name__ == "__main__":
    argv = [a for a in sys.argv[1:]
            if a not in ("--valid-only", "--facet", "--no-facet")]
    if len(argv) < 2:
        raise SystemExit(__doc__)
    facet = None
    if "--facet" in sys.argv:
        facet = True
    if "--no-facet" in sys.argv:
        facet = False
    main(argv[0], argv[1:], valid_only="--valid-only" in sys.argv, facet=facet)
