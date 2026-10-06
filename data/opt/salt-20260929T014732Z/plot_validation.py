#!/usr/bin/env python3
"""Plot the 2026-10-06 validation blocks of campaign salt-20260929T014732Z.

    python3 data/opt/salt-20260929T014732Z/plot_validation.py [out png]

Left: every replicate's dose time against its final error, one colour per
point, with the campaign's single dose at the same values for reference.
Right: each replicate's mass still to go (log scale) against time, one
panel per point, from the per-poll telemetry in the Zero's trial documents.
"""

import json
import os
import statistics
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt                                # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
POINTS = [("bo-005", "#2a78d6"), ("corner-09", "#eb6834")]
SURFACE = "#fcfcfb"
INK = "#0b0b0b"
INK_2 = "#52514e"
GRID = "#e4e3df"
BAND = "#f0efec"
FLOOR_MG = 0.3                       # log-axis floor for "mg to go"


def load():
    with open(os.path.join(HERE, "campaign.json")) as f:
        doc = json.load(f)
    with open(os.path.join(HERE, "campaign_records.jsonl")) as f:
        records = [json.loads(line) for line in f if line.strip()]
    return doc, records


def trial_doc(uuid):
    path = os.path.join(HERE, "zero", "trial_{}.json".format(uuid))
    if not os.path.exists(path):
        return None
    with open(path) as f:
        return json.load(f)


def blocks(doc, records):
    """point -> (block replicates, earlier replicates, campaign dose).

    A block is the last ``replicates`` validation doses of the point; any
    earlier ones ran before a restart and are not in its profile."""
    out = {}
    for point, _c in POINTS:
        vals = [r for r in records if r["mode"] == "validation"
                and r["label"].startswith("val-{}-".format(point))]
        prof = [p for p in doc.get("profiles") or [] if p.get("point") == point]
        n = (prof[-1]["validation"]["replicates"] if prof else len(vals))
        n = min(n, len(vals))
        origin = [r for r in records if r["label"] == point]
        out[point] = (vals[len(vals) - n:], vals[:len(vals) - n],
                      origin[-1] if origin else None)
    return out


def style(ax):
    ax.set_facecolor(SURFACE)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(INK_2)
    ax.tick_params(colors=INK_2, labelsize=9)
    ax.grid(True, color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)


def trace(doc):
    """(t_s, mg still to go) per telemetry row, raw balance reading."""
    tel = (doc or {}).get("telemetry") or {}
    target = doc["target_g"] if doc else 0.5
    ts, ys = [], []
    for row in tel.get("rows") or []:
        f = row.split(",")
        try:
            t, z = float(f[0]), float(f[2])
        except (ValueError, IndexError):
            continue
        ts.append(t)
        ys.append(max((target - z) * 1000.0, FLOOR_MG))
    return ts, ys


def main(argv):
    out = argv[1] if len(argv) > 1 else os.path.join(
        HERE, "validation_20261006.png")
    doc, records = load()
    by_point = blocks(doc, records)
    fig = plt.figure(figsize=(13.5, 4.8), facecolor=SURFACE)
    gs = fig.add_gridspec(1, 3, width_ratios=[1.05, 1, 1], wspace=0.28)
    ax = fig.add_subplot(gs[0])
    style(ax)
    ax.axhspan(-3, 3, color=BAND, zorder=0)
    ax.axhline(0, color=INK_2, lw=0.8, zorder=1)
    ax.text(0.01, -2.8, "±3 mg band", transform=ax.get_yaxis_transform(),
            ha="left", va="bottom", fontsize=8.5, color=INK_2)
    worst = [abs(r["summary"]["error_mg"]) for b in by_point.values()
             for r in b[0] + b[1] + ([b[2]] if b[2] else [])
             if r["summary"].get("error_mg") is not None]
    lim = max([6.0] + [w * 1.15 for w in worst])
    ax.set_ylim(-lim, lim)
    for point, color in POINTS:
        block, early, origin = by_point[point]
        for group, kw in ((block, dict(facecolors=color, s=52)),
                          (early, dict(facecolors="none", s=52))):
            pts = [(r["summary"]["t_total_s"], r["summary"]["error_mg"])
                   for r in group if r["summary"]["t_total_s"] is not None
                   and r["summary"].get("error_mg") is not None]
            if pts:
                ax.scatter(*zip(*pts), edgecolors=color, linewidths=1.6,
                           zorder=3, **kw)
        if origin is not None and origin["summary"]["t_total_s"]:
            ax.scatter(origin["summary"]["t_total_s"],
                       origin["summary"]["error_mg"], marker="D", s=60,
                       facecolors="none", edgecolors=INK, linewidths=1.2,
                       zorder=4)
            ax.annotate("campaign dose", (origin["summary"]["t_total_s"],
                                          origin["summary"]["error_mg"]),
                        xytext=(6, -12), textcoords="offset points",
                        fontsize=8, color=INK_2)
    # identity legend: colour = point, fill = in the block
    handles = [plt.Line2D([], [], ls="", marker="o", ms=7, mfc=c, mec=c,
                          label=p) for p, c in POINTS]
    if any(by_point[p][1] for p, _c in POINTS):
        handles.append(plt.Line2D([], [], ls="", marker="o", ms=7,
                                  mfc="none", mec=INK_2,
                                  label="before the restart (not in block)"))
    handles.append(plt.Line2D([], [], ls="", marker="D", ms=6, mfc="none",
                              mec=INK, label="campaign's single dose"))
    ax.legend(handles=handles, fontsize=8.5, frameon=False,
              loc="upper right")
    ax.set_xlabel("dose time, start to settled reading (s)", color=INK)
    ax.set_ylabel("final error vs 0.5 g (mg)", color=INK)
    ax.set_title("Each replicate: time and final error", loc="left",
                 fontsize=10.5, color=INK)

    share = None
    for i, (point, color) in enumerate(POINTS):
        block, _early, origin = by_point[point]
        a = fig.add_subplot(gs[i + 1], sharey=share)
        share = share or a
        style(a)
        a.set_yscale("log")
        thr = None
        if origin is not None:
            ts, ys = trace(trial_doc(origin["trial_uuid"]))
            if ts:
                a.plot(ts, ys, color=INK, lw=1.1, ls="--", zorder=4)
                a.annotate("campaign dose", (ts[-1], ys[-1]),
                           xytext=(4, -10), textcoords="offset points",
                           fontsize=8, color=INK_2)
        for r in block:
            ts, ys = trace(trial_doc(r["trial_uuid"]))
            if ts:
                a.plot(ts, ys, color=color, lw=1.4, alpha=0.8, zorder=3)
            thr = r["params"].get("trickle_start_remaining_g", thr)
        if thr:
            a.axhline(thr * 1000.0, color=INK_2, lw=0.8, ls="--", zorder=2)
            a.text(0.99, thr * 1000.0 * 1.08,
                   "bulk stops {:.0f} mg short".format(thr * 1000.0),
                   transform=a.get_yaxis_transform(), ha="right",
                   va="bottom", fontsize=8.5, color=INK_2)
        a.axhline(3, color=INK_2, lw=0.8, ls=":", zorder=2)
        a.text(0.99, 3.3, "3 mg", transform=a.get_yaxis_transform(),
               ha="right", va="bottom", fontsize=8.5, color=INK_2)
        times = [r["summary"]["t_total_s"] for r in block
                 if r["summary"]["t_total_s"] is not None]
        errs = [r["summary"]["abs_error_mg"] for r in block
                if r["summary"]["abs_error_mg"] is not None]
        head = "{}: {} replicates".format(point, len(block))
        if times and errs:
            head += ", median {:.0f} s and {:.1f} mg".format(
                statistics.median(times), statistics.median(errs))
        a.set_title(head, loc="left", fontsize=10.5, color=INK)
        a.set_xlabel("time since the dose command (s)", color=INK)
        if i == 0:
            a.set_ylabel("mass still to go (mg, log)", color=INK)
        a.set_ylim(FLOOR_MG * 0.8, 700)
    fig.savefig(out, dpi=150, bbox_inches="tight", facecolor=SURFACE)
    plt.close(fig)
    print("wrote", out)


if __name__ == "__main__":
    main(sys.argv)
