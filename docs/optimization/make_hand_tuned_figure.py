#!/usr/bin/env python3
"""Figure for campaign-setup.md section 2.9: where the hand-tuned
trickle_params.py values enter the campaign.

Left: each continuous parameter's search box, normalized, with the
screening levels (corners at the edges, centers at the midpoint), the
BO suggestions, and the hand-tuned value.  Right: the same campaign in
objective space, with the baseline doses as the reference the front has
to beat.

    python scripts/opt_campaign.py --powder-id salt --simulate \
        --model moo --budget 14 --state-dir /tmp/simfig
    python docs/optimization/make_hand_tuned_figure.py \
        /tmp/simfig/salt-<stamp> docs/optimization/hand-tuned-baseline.png

Reads only the campaign directory (campaign.json + campaign_records.jsonl).
"""

import json
import os
import random
import statistics
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt                                # noqa: E402
from matplotlib.lines import Line2D                            # noqa: E402
from matplotlib.patches import Patch                           # noqa: E402

SURFACE = "#fcfcfb"
TEXT = "#0b0b0b"
TEXT_2 = "#52514e"
MUTED = "#8a8984"
GRID = "#e7e6e2"
BLUE, ORANGE, AQUA = "#2a78d6", "#eb6834", "#1baf7a"   # slots 1-3

ROWS = [   # (param, label, unit format)
    ("bulk_tilt_deg", "Bulk tilt", "{:g}°"),
    ("trickle_tilt_deg", "Trickle tilt", "{:g}°"),
    ("tap_tilt_deg", "Tap tilt", "{:g}°"),
    ("bulk_rpm", "Bulk RPM", "{:g}"),
    ("trickle_start_remaining_g", "Bulk→trim threshold", "{:g} g"),
    ("tolerance_g", "Tolerance band", "{:g} mg"),
]
Y_MAX = 25.0      # |error| axis cap, mg


def fmt(param, value, unit=True):
    spec = dict((p, f) for p, _l, f in ROWS)[param]
    if not unit:
        spec = "{:g}"
    return spec.format(round(value * 1000.0, 1) if param == "tolerance_g"
                       else round(value, 3))


def box_label(param, lo, hi):
    spec = dict((p, f) for p, _l, f in ROWS)[param]
    unit = spec.replace("{:g}", "").strip()
    return "{}–{}{}".format(fmt(param, lo, False), fmt(param, hi, False),
                            ("" if unit == "°" else " ") + unit
                            if unit else "")


def load(campaign_dir):
    with open(os.path.join(campaign_dir, "campaign.json")) as f:
        doc = json.load(f)
    with open(os.path.join(campaign_dir, "campaign_records.jsonl")) as f:
        records = [json.loads(l) for l in f if l.strip()]
    return doc, records


def kind(record):
    label = record["label"]
    if "baseline-" in label:
        return "baseline"
    if record["mode"] == "bo":
        return "bo"
    return "screen"


def main(campaign_dir, out_png):
    doc, records = load(campaign_dir)
    bounds = {p["name"]: p["bounds"] for p in doc["search_space"]
              if p.get("bounds")}
    base = doc["baseline_params"]
    usable = [r for r in records
              if not r["summary"]["infra_error"] and not r.get("void")]

    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10,
                         "axes.edgecolor": GRID, "axes.labelcolor": TEXT_2,
                         "xtick.color": TEXT_2, "ytick.color": TEXT_2})
    fig, (ax1, ax2) = plt.subplots(
        1, 2, figsize=(13.5, 5.2), gridspec_kw={"width_ratios": [1.05, 1]})
    fig.patch.set_facecolor(SURFACE)
    for ax in (ax1, ax2):
        ax.set_facecolor(SURFACE)
        for side in ("top", "right"):
            ax.spines[side].set_visible(False)

    # ---- left: the tuned point inside each box ----------------------
    rng = random.Random(3)
    bo_pts = [r["params"] for r in usable if kind(r) == "bo"]
    for i, (param, label, _f) in enumerate(ROWS):
        y = len(ROWS) - 1 - i
        lo, hi = bounds[param]
        ax1.plot([0, 1], [y, y], color=GRID, lw=6, solid_capstyle="round",
                 zorder=1)
        xs = [(p[param] - lo) / (hi - lo) for p in bo_pts]
        ys = [y + rng.uniform(-0.22, 0.22) for _ in xs]
        ax1.scatter(xs, ys, s=42, marker="s", color=AQUA, edgecolor=SURFACE,
                    linewidth=1.5, zorder=3)
        ax1.scatter([0, 0.5, 1], [y, y, y], s=80, color=BLUE,
                    edgecolor=SURFACE, linewidth=2, zorder=4)
        xb = (base[param] - lo) / (hi - lo)
        ax1.scatter([xb], [y], s=190, marker="D", color=ORANGE,
                    edgecolor=SURFACE, linewidth=2, zorder=5)
        ax1.annotate(fmt(param, base[param]), (xb, y), xytext=(0, 11),
                     textcoords="offset points", ha="center", va="bottom",
                     fontsize=9.5, color=TEXT, fontweight="bold")
        ax1.text(-0.06, y, "{}\n{}".format(label, box_label(param, lo, hi)),
                 ha="right", va="center", fontsize=9.5, color=TEXT_2)
    ax1.set_xlim(-0.04, 1.04)
    ax1.set_ylim(-0.6, len(ROWS) - 0.35)
    ax1.set_yticks([])
    ax1.spines["left"].set_visible(False)
    ax1.set_xticks([0, 0.25, 0.5, 0.75, 1.0])
    ax1.set_xticklabels(["lower\nbound", "", "midpoint", "", "upper\nbound"])
    ax1.set_title("Where the hand-tuned values sit in each search box\n"
                  "(both taps: tuned off; the screen tests off and 2 Hz)",
                  fontsize=11, color=TEXT, loc="left")

    # ---- right: objective space ------------------------------------
    t_ref, e_ref = doc["objectives"]["t_total_s"], \
        doc["objectives"]["abs_error_mg"]
    fitted = [r for r in usable if kind(r) == "baseline"
              and r["mode"] == "recenter" and not r["summary"]["jam"]]
    ref = fitted or [r for r in usable if kind(r) == "baseline"]
    # the same medians the campaign readout reports
    tb = statistics.median(r["summary"]["t_total_s"] for r in ref)
    eb = statistics.median(r["summary"]["abs_error_mg"] for r in ref)
    ax2.fill_between([0, tb], 0, eb, color=ORANGE, alpha=0.10, lw=0,
                     zorder=0)
    ax2.axvline(t_ref, color=MUTED, lw=1, zorder=0)
    ax2.axhline(e_ref, color=MUTED, lw=1, zorder=0)
    ax2.text(t_ref - 2, Y_MAX * 0.985,
             "reference point\n({:g} s, {:g} mg)".format(t_ref, e_ref),
             ha="right", va="top", fontsize=8.5, color=TEXT_2)

    off = 0
    style = {"screen": (BLUE, "o", 55), "baseline": (ORANGE, "D", 120),
             "bo": (AQUA, "s", 55)}
    for r in usable:
        t, e = r["summary"]["t_total_s"], r["summary"]["abs_error_mg"]
        if t is None or e is None:
            continue
        if e > Y_MAX:
            off += 1
            continue
        color, marker, size = style[kind(r)]
        hollow = r["mode"] == "recenter"
        ax2.scatter([t], [e], s=size, marker=marker,
                    color=SURFACE if hollow else color,
                    edgecolor=color if hollow else SURFACE,
                    linewidth=2, zorder=4 if kind(r) != "baseline" else 5)
    pts = sorted((r["summary"]["t_total_s"], r["summary"]["abs_error_mg"])
                 for r in usable if not r["summary"]["jam"]
                 and not r["spill"] and r["summary"]["t_total_s"] is not None
                 and r["summary"]["t_total_s"] <= t_ref
                 and r["summary"]["abs_error_mg"] <= e_ref)
    front, best = [], float("inf")
    for t, e in pts:
        if e < best:
            front.append((t, e))
            best = e
    fx, fy = [], []
    for j, (t, e) in enumerate(front):
        fx += [t, front[j + 1][0] if j + 1 < len(front) else t_ref]
        fy += [e, e]
    ax2.plot(fx, fy, color=TEXT_2, lw=2, zorder=3, solid_joinstyle="round")
    ax2.scatter([tb], [eb], s=30, marker="+", color=TEXT, linewidth=1.5,
                zorder=6)
    ax2.annotate("hand-tuned median, fitted τ\n({:.0f} s, {:.1f} mg)".format(
                     tb, eb),
                 (tb, eb), xytext=(tb - 62, 17.5), textcoords="data",
                 fontsize=9, color=TEXT, fontweight="bold", ha="left",
                 arrowprops={"arrowstyle": "-", "color": TEXT_2, "lw": 1,
                             "shrinkA": 2, "shrinkB": 3})
    if off:
        ax2.text(4, Y_MAX * 0.985, "{} dose(s) above {:g} mg off-scale"
                 .format(off, Y_MAX), fontsize=8.5, color=TEXT_2, va="top")
    ax2.set_xlim(0, max(200.0, t_ref + 15))
    ax2.set_ylim(0, Y_MAX)
    ax2.set_xlabel("t_total (s)")
    ax2.set_ylabel("|error| (mg)")
    ax2.grid(True, color=GRID, lw=1)
    ax2.set_axisbelow(True)
    ax2.set_title("What Ax sees: simulated campaign (virtual plant, "
                  "not rig data)", fontsize=11, color=TEXT, loc="left")

    handles = [
        Line2D([], [], marker="D", ls="", ms=10, mfc=ORANGE, mec=ORANGE,
               label="Hand-tuned point (d21d652): baseline doses"),
        Line2D([], [], marker="o", ls="", ms=8, mfc=BLUE, mec=BLUE,
               label="Screening design: corners at the edges, "
                     "centers at the midpoint"),
        Line2D([], [], marker="s", ls="", ms=8, mfc=AQUA, mec=AQUA,
               label="BO suggestions (Ax)"),
        Line2D([], [], marker="o", ls="", ms=8, mfc=SURFACE, mec=TEXT_2,
               mew=2, label="Hollow: re-dosed under the fitted τ "
                            "(filled: τ = 0.30 s)"),
        Line2D([], [], color=TEXT_2, lw=2,
               label="Observed front (inside 180 s / 20 mg)"),
        Patch(facecolor=ORANGE, alpha=0.18, lw=0,
              label="Beats the hand-tuned median on both objectives"),
    ]
    fig.legend(handles=handles, loc="lower center", ncol=3, frameon=False,
               fontsize=9.5, labelcolor=TEXT_2, bbox_to_anchor=(0.5, 0.0))
    fig.suptitle("How the hand-tuned trickle_params.py values enter the "
                 "campaign", fontsize=13, color=TEXT, x=0.01, ha="left",
                 y=0.995)
    fig.tight_layout(rect=(0.075, 0.1, 1, 1.0))
    fig.savefig(out_png, dpi=150, facecolor=SURFACE)
    print("wrote", out_png)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
