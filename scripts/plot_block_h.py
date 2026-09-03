#!/usr/bin/env python3
"""Block H figure: does dose error scale with the target, or not?

Block H exists to answer one question (see ``_block_h_small_dose`` in
``powder_battery.py``): is the closed-loop dose error a **fixed mass**,
so a 50 mg dose is 20x worse in relative terms than a 1 g one, or a
**fixed fraction** of the target?  Only a run that spans targets can
tell, so this figure puts a run's Block H doses next to the Block G
1.000 g doses for the same powder.

  A  absolute error per dose, with the +/-5 mg tolerance band
  B  relative error vs target (log x) -- the fixed-mass vs
     fixed-fraction discriminator
  C  time and actuation cost per dose

Panel titles are derived, never asserted: a title that says "error is a
fixed mass" when the data says otherwise is the bug this repo has now
fixed three times (2026-08-05, 08-05, 08-20).

Usage::

    python scripts/plot_block_h.py OUT.png RUN.json [MORE_RUNS.json ...]
"""

import json
import sys
import textwrap

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# Reference palette (dataviz skill), light surface.
SURFACE = "#fcfcfb"
TEXT_PRIMARY = "#0b0b0b"
TEXT_SECONDARY = "#52514e"
GRID = "#dcdbd6"
SERIES = ["#2a78d6", "#eb6834", "#1baf7a"]
TARGET = "#e34948"
OKC = "#1baf7a"
BADC = "#eb6834"

TOLERANCE_G = 0.005


def style(ax):
    ax.set_facecolor(SURFACE)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(GRID)
    ax.tick_params(colors=TEXT_SECONDARY, labelsize=9, length=3)
    ax.yaxis.grid(True, color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)


def load_doses(paths):
    """Every dose across the given run documents, newest label wins."""
    doses = []
    for path in paths:
        doc = json.load(open(path))
        label = (doc.get("started_utc") or "")[:10]
        params = doc.get("parameters") or {}
        read_path = params.get("config.dose_read_path", "read_stable")
        for d in doc.get("doses", []):
            if d.get("dispensed_g") is None or d.get("target_g") in (None, 0):
                continue
            # A dose that never reached a terminal control state is not a
            # measurement of dose accuracy -- the 2026-09-03 morning runs
            # reported 7.5393 g of "overshoot" the auger never dispensed.
            if d.get("status") in ("scale-error", "not-tared"):
                continue
            doses.append({
                "target_g": float(d["target_g"]),
                "delivered_g": float(d["dispensed_g"]),
                "error_g": float(d["dispensed_g"]) - float(d["target_g"]),
                "status": d.get("status", "?"),
                "elapsed_s": float(d.get("elapsed_s") or 0.0),
                "taps": int(d.get("taps") or 0),
                "block": d.get("block") or "G",
                "read_path": read_path,
                "date": label,
                "powder_id": doc.get("powder_id", "?"),
            })
    doses.sort(key=lambda d: (d["target_g"], d["date"]))
    return doses


def by_target(doses):
    groups = {}
    for d in doses:
        groups.setdefault(d["target_g"], []).append(d)
    return [(t, groups[t]) for t in sorted(groups)]


def mean(xs):
    return sum(xs) / len(xs) if xs else 0.0


def scaling_headline(groups):
    """Derive whether error looks like a fixed mass or a fixed fraction.

    Fixed mass  -> mean |error| roughly constant across targets, so
                   relative error falls as the target grows.
    Fixed frac  -> mean |error| grows in proportion to the target.

    With few targets and n=3 per target this is a description of the
    measured points, not a fitted law, and the wording says so.
    """
    if len(groups) < 2:
        return "single target -- no scaling statement possible"
    targets = [t for t, _ in groups]
    abs_err = [mean([abs(d["error_g"]) for d in g]) for _, g in groups]
    span_target = max(targets) / min(targets)
    lo, hi = abs_err[0] or 1e-9, abs_err[-1] or 1e-9
    span_err = max(lo, hi) / min(lo, hi)
    # Proportional scaling would make span_err track span_target.
    if span_err < span_target / 3.0:
        return ("absolute error is roughly constant across a {:.0f}x span "
                "in target, so relative error falls with target size"
                .format(span_target))
    if span_err > span_target / 1.5:
        return ("absolute error grows roughly in proportion to the target "
                "over a {:.0f}x span".format(span_target))
    return ("absolute error grows with target, but more slowly than in "
            "proportion, over a {:.0f}x span".format(span_target))


def panel_absolute(ax, groups):
    xs, labels = [], []
    for i, (target, ds) in enumerate(groups):
        for j, d in enumerate(ds):
            x = i + (j - (len(ds) - 1) / 2.0) * 0.18
            ax.plot([x], [1000.0 * d["error_g"]], "o", markersize=8,
                    color=OKC if d["status"] == "ok" else BADC,
                    markeredgecolor="white", markeredgewidth=0.8, zorder=3)
        xs.append(i)
        paths = sorted({d["read_path"] for d in ds})
        labels.append("{:.0f} mg\nblock {} - n={}\nread: {}".format(
            1000.0 * target, "/".join(sorted({d["block"] for d in ds})),
            len(ds), "/".join(paths)))
    ax.axhspan(-1000.0 * TOLERANCE_G, 1000.0 * TOLERANCE_G,
               color=TARGET, alpha=0.10, zorder=0)
    ax.axhline(0, color=TARGET, linewidth=1.0, zorder=1)
    ax.set_xticks(xs)
    ax.set_xticklabels(labels, fontsize=8)
    ax.set_ylabel("dose error (mg)", color=TEXT_SECONDARY, fontsize=9)
    n_ok = sum(1 for _, ds in groups for d in ds if d["status"] == "ok")
    n = sum(len(ds) for _, ds in groups)
    ax.set_title("\n".join(textwrap.wrap(
        "A  {}/{} doses inside the +/-5 mg band".format(n_ok, n), 46)),
        color=TEXT_PRIMARY, fontsize=10, loc="left")
    style(ax)


def panel_relative(ax, groups):
    targets = [1000.0 * t for t, _ in groups]
    rel = [100.0 * mean([abs(d["error_g"]) for d in ds]) / t
           for t, ds in groups]
    absmg = [1000.0 * mean([abs(d["error_g"]) for d in ds])
             for _, ds in groups]
    ax.plot(targets, rel, "o-", color=SERIES[0], markersize=8,
            markeredgecolor="white", markeredgewidth=0.8, linewidth=2)
    for i, (t, r, a) in enumerate(zip(targets, rel, absmg)):
        # Nudge the end labels inward so they do not clip on the axes.
        dx = 12 if i == 0 else (-12 if i == len(targets) - 1 else 0)
        ax.annotate("{:.1f} %\n({:.1f} mg)".format(r, a), (t, r),
                    textcoords="offset points", xytext=(dx, 11),
                    ha="center", fontsize=8, color=TEXT_SECONDARY)
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("dose target (mg, log)", color=TEXT_SECONDARY, fontsize=9)
    ax.set_ylabel("mean |error| (% of target, log)",
                  color=TEXT_SECONDARY, fontsize=9)
    ax.set_title("\n".join(textwrap.wrap("B  " + scaling_headline(groups),
                                         46)),
                 color=TEXT_PRIMARY, fontsize=10, loc="left")
    style(ax)
    ax.margins(y=0.35)


def panel_cost(ax, groups):
    xs = list(range(len(groups)))
    secs = [mean([d["elapsed_s"] for d in ds]) for _, ds in groups]
    taps = [mean([d["taps"] for d in ds]) for _, ds in groups]
    ax.bar([x - 0.18 for x in xs], secs, width=0.34, color=SERIES[0],
           label="mean seconds")
    ax.bar([x + 0.18 for x in xs], taps, width=0.34, color=SERIES[1],
           label="mean taps")
    for x, s, t in zip(xs, secs, taps):
        ax.annotate("{:.0f} s".format(s), (x - 0.18, s), ha="center",
                    textcoords="offset points", xytext=(0, 3), fontsize=8,
                    color=TEXT_SECONDARY)
        ax.annotate("{:.0f}".format(t), (x + 0.18, t), ha="center",
                    textcoords="offset points", xytext=(0, 3), fontsize=8,
                    color=TEXT_SECONDARY)
    ax.set_xticks(xs)
    ax.set_xticklabels(["{:.0f} mg".format(1000.0 * t) for t, _ in groups],
                       fontsize=8)
    ax.set_ylabel("per dose", color=TEXT_SECONDARY, fontsize=9)
    ax.legend(frameon=False, fontsize=8, labelcolor=TEXT_SECONDARY)
    ax.set_title("\n".join(textwrap.wrap(
        "C  a smaller dose is not a proportionally cheaper one", 46)),
        color=TEXT_PRIMARY, fontsize=10, loc="left")
    style(ax)
    ax.margins(y=0.25)


def build(out_path, run_paths):
    doses = load_doses(run_paths)
    if not doses:
        raise SystemExit("no doses reached a terminal control state")
    groups = by_target(doses)
    fig, axes = plt.subplots(1, 3, figsize=(14.0, 4.6))
    fig.patch.set_facecolor(SURFACE)
    panel_absolute(axes[0], groups)
    panel_relative(axes[1], groups)
    panel_cost(axes[2], groups)
    powder = doses[0]["powder_id"]
    dates = sorted({d["date"] for d in doses})
    fig.suptitle(
        "Closed-loop dose accuracy vs target -- {} ({})".format(
            powder, ", ".join(dates)),
        color=TEXT_PRIMARY, fontsize=12, x=0.008, ha="left")
    paths = sorted({d["read_path"] for d in doses})
    caption = ("Frozen three-phase controller, identical parameters at "
               "every target. Green = inside +/-5 mg, orange = outside. "
               "Doses that never reached a terminal control state are "
               "excluded, not plotted as zeros.")
    if len(paths) > 1:
        caption += (" NOTE: targets were not all measured the same way -- "
                    "read paths present: " + ", ".join(paths) +
                    ". Compare across targets with that in mind.")
    fig.text(0.008, 0.012, "\n".join(textwrap.wrap(caption, 150)),
             color=TEXT_SECONDARY, fontsize=8, ha="left", va="bottom")
    fig.tight_layout(rect=(0, 0.10, 1, 0.92))
    fig.savefig(out_path, dpi=150, facecolor=SURFACE)
    print("[block-h] wrote {} ({} doses, {} targets)".format(
        out_path, len(doses), len(groups)))
    return groups


def main(argv):
    if len(argv) < 3:
        raise SystemExit(__doc__)
    build(argv[1], argv[2:])
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
