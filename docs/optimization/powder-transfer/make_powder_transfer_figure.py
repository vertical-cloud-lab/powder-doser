#!/usr/bin/env python3
"""Figure for the powder-transfer example (PR #166).

(a) R1: the afterflow rule's threshold floor against bulk rpm, for salt's
    two session fingerprints and AlSi10Mg, over every salt campaign dose.
(b) Tap yield per cycle against tap tilt, per dose: the property that varies
    by day and is NOT turned into a bound.
(c) The warm-started Ax model (ax_warm_start.py): predicted dose time for
    three salt points in each context, against the doses measured there.

Every marker is a measured dose; only the bars in (c) are model output.

    python docs/optimization/powder-transfer/ax_warm_start.py   # writes the json
    python docs/optimization/powder-transfer/make_powder_transfer_figure.py
"""
from __future__ import annotations

import json
import math
import os
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import powder_box as pb  # noqa: E402

INK, INK2, MUTED, GRID = "#0b0b0b", "#52514e", "#898781", "#e6e5e1"
SURFACE = "#fcfcfb"
CRITICAL = "#d03b3b"            # status colour: overshoot (always with x + label)
SERIES = {"salt (09-29, 10-06)": "#2a78d6", "salt (10-13, 10-15)": "#1baf7a",
          "AlSi10Mg": "#eb6834"}
SHORT = {"salt (09-29, 10-06)": "salt, 09-29 / 10-06",
         "salt (10-13, 10-15)": "salt, 10-13 / 10-15", "AlSi10Mg": "AlSi10Mg"}

plt.rcParams.update({
    "font.size": 11.5, "axes.edgecolor": MUTED, "axes.labelcolor": INK2,
    "xtick.color": INK2, "ytick.color": INK2, "axes.spines.top": False,
    "axes.spines.right": False, "figure.facecolor": SURFACE,
    "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE,
})


def sunflower(n, i, dx, dy):
    """Deterministic spread of the i-th of n overlapping points."""
    if n == 1:
        return 0.0, 0.0
    r = math.sqrt(i + 0.5) / math.sqrt(n)
    a = i * 2.39996
    return r * dx * math.cos(a), r * dy * math.sin(a)


def panel_rule(ax, res, doses):
    campaign = [d for d in doses if d["mode"] != "validation"]
    groups = {}
    for d in campaign:
        key = (d["params"]["bulk_rpm"], d["params"]["trickle_start_remaining_g"])
        groups.setdefault(key, []).append(d)
    lead = res["lead_g"]
    rpm = [20 + i for i in range(81)]
    ax.add_patch(plt.Rectangle((20, 0.05), 80, 0.25, fill=False,
                               edgecolor=MUTED, lw=1.0, ls=(0, (2, 2))))
    order = ["AlSi10Mg", "salt (10-13, 10-15)", "salt (09-29, 10-06)"]
    for name in order:
        c, dd = pb.afterflow_constraint(res["fingerprints"][name], lead)
        floor = [c * r - dd for r in rpm]
        clipped = [max(0.05, f) for f in floor]
        ax.fill_between(rpm, 0.05, clipped, color=SERIES[name],
                        alpha=0.10 if name == "AlSi10Mg" else 0.16, lw=0)
        ax.plot(rpm, floor, color=SERIES[name], lw=1.0, ls=(0, (3, 2)))
        bind = [(r, f) for r, f in zip(rpm, floor) if f >= 0.05]
        if bind:
            ax.plot(*zip(*bind), color=SERIES[name], lw=2.4)
    # direct labels right of the 100 rpm cluster, spread so they never touch
    text = {"AlSi10Mg": "AlSi10Mg (feed x1.44, #116)",
            "salt (10-13, 10-15)": "salt, 10-13 / 10-15",
            "salt (09-29, 10-06)": "salt, 09-29 / 10-06"}
    for name, y in (("AlSi10Mg", 0.104), ("salt (10-13, 10-15)", 0.084),
                    ("salt (09-29, 10-06)", 0.068)):
        c, dd = pb.afterflow_constraint(res["fingerprints"][name], lead)
        ax.plot([100.0, 104.5], [c * 100 - dd, y], color=SERIES[name], lw=1.0)
        ax.text(105.0, y, text[name], color=INK2, fontsize=10.5, va="center")

    for (r, t), ds in groups.items():
        for i, d in enumerate(sorted(ds, key=lambda d: d["status"])):
            ox, oy = sunflower(len(ds), i, 3.2, 0.012)
            x, y = r + ox, t + oy
            if d["status"] == "overshoot":
                ax.scatter(x, y, marker="x", s=46, color=CRITICAL, lw=1.8,
                           zorder=4)
            elif d["jam"]:
                ax.scatter(x, y, marker="v", s=34, facecolor="none",
                           edgecolor=INK2, lw=1.1, zorder=3)
            elif d["feasible"]:
                ax.scatter(x, y, marker="o", s=34, color=INK, zorder=3,
                           edgecolor=SURFACE, lw=0.8)
            else:
                ax.scatter(x, y, marker="o", s=30, facecolor="none",
                           edgecolor=MUTED, lw=1.1, zorder=3)
    retro = res["retrospective"]["salt (09-29, 10-06)"]
    ax.annotate("{} of {} overshoots on 09-29\nsat in this sliver: 1.1% of\n"
                "the box".format(retro["excluded_overshoots"],
                                 retro["overshoots"]),
                xy=(96.5, 0.056), xytext=(52, 0.112), fontsize=10.5,
                color=INK2, arrowprops=dict(arrowstyle="-", color=MUTED,
                                            lw=1.0))
    ax.set_xlim(14, 142)
    ax.set_ylim(0.0, 0.335)
    ax.set_xticks([20, 40, 60, 80, 100])
    ax.set_xlabel("bulk rpm")
    ax.set_ylabel("bulk -> trim threshold (g)")
    ax.grid(color=GRID, lw=0.8)
    ax.set_axisbelow(True)
    # marker key, direct and in ink
    keys = [("o", INK, "feasible", None), ("o", "none", "ok, too slow", MUTED),
            ("v", "none", "jam / stall", INK2), ("x", CRITICAL, "overshoot",
                                                 None)]
    for (m, fc, text, ec), x in zip(keys, (18, 42, 72, 99)):
        if m == "x":
            ax.scatter(x, 0.322, marker="x", s=40, color=fc, lw=1.8)
        else:
            ax.scatter(x, 0.322, marker=m, s=30, facecolor=fc,
                       edgecolor=ec or SURFACE, lw=1.1)
        ax.text(x + 2.2, 0.322, text, fontsize=10, va="center", color=INK2)
    ax.set_title("(a)  R1: afterflow sets a threshold floor that rises "
                 "with rpm", loc="left", fontsize=12.5, color=INK)


def panel_taps(ax, res, doses):
    pts = {}
    for d in doses:
        cyc = d["tap_cycles_g"]
        if len(cyc) < 3:
            continue
        name = next(n for n, dates in pb.SALT_SESSIONS.items()
                    if d["date"] in dates)
        pts.setdefault(name, []).append(
            (d["params"]["tap_tilt_deg"], 1000.0 * sum(cyc) / len(cyc)))
    off = {"salt (09-29, 10-06)": -0.35, "salt (10-13, 10-15)": 0.35}
    marker = {"salt (09-29, 10-06)": "o", "salt (10-13, 10-15)": "s"}
    for name, xy in pts.items():
        ax.scatter([x + off[name] for x, _y in xy], [max(y, 0.02) for _x, y in xy],
                   s=26, marker=marker[name], color=SERIES[name], alpha=0.75,
                   edgecolor=SURFACE, lw=0.6, zorder=3)
        pooled = res["fingerprints"][name]["tap15"]
        ax.plot([14.0, 16.0], [pooled, pooled], color=SERIES[name], lw=2.4)
    alsi = res["fingerprints"]["AlSi10Mg"]["tap15"]
    ax.scatter(15.0, alsi, marker="D", s=46, color=SERIES["AlSi10Mg"],
               edgecolor=SURFACE, lw=0.8, zorder=4)
    al = res["fingerprints"]["Al 4047 (clogged)"]["tap15"]
    ax.scatter(15.0, al, marker="D", s=40, facecolor="none", edgecolor=INK2,
               lw=1.2, zorder=4)
    ax.text(16.3, res["fingerprints"]["salt (09-29, 10-06)"]["tap15"],
            "salt, 09-29 / 10-06\npooled {:.2f} mg".format(
                res["fingerprints"]["salt (09-29, 10-06)"]["tap15"]),
            fontsize=10, va="center", color=INK2)
    ax.text(16.3, res["fingerprints"]["salt (10-13, 10-15)"]["tap15"] * 0.92,
            "salt, 10-13 / 10-15\npooled {:.2f} mg".format(
                res["fingerprints"]["salt (10-13, 10-15)"]["tap15"]),
            fontsize=10, va="center", color=INK2)
    ax.text(16.3, alsi * 1.08, "AlSi10Mg, 8 g dose", fontsize=10,
            va="center", color=INK2)
    ax.text(16.3, al, "Al 4047, clogged", fontsize=10, va="center", color=INK2)
    ax.annotate("corner-03 at 0 deg, 10-13:\n28 s, no taps at all (the\n"
                "trickle finished the dose).\nA tap-tilt floor would\n"
                "have cut it.", xy=(0.0, 0.05), xytext=(1.2, 0.022),
                fontsize=10, color=INK2, va="bottom")
    ax.set_yscale("log")
    ax.set_ylim(0.02, 30)
    ax.set_xlim(-1.5, 24.5)
    ax.set_xticks([0, 5, 10, 15])
    ax.set_xlabel("tap tilt (deg)")
    ax.set_ylabel("mg per tap cycle (dose mean)")
    ax.grid(color=GRID, lw=0.8, which="major")
    ax.set_axisbelow(True)
    ax.set_title("(b)  Tap yield moves 3x between sessions: a model input, "
                 "not a bound", loc="left", fontsize=12.5, color=INK)


def panel_model(ax, res, doses, warm):
    rows = []
    first = [d for d in doses if d["campaign_id"] == pb.SALT_CAMPAIGNS[0]]
    obs = {
        # the campaign dose plus every validation replicate at that point
        ("bo-005", "salt (09-29, 10-06)"): [
            d["t_total_s"] for d in first
            if d["label"] == "bo-005" or d["label"].startswith("val-bo-005")],
        ("corner-09", "salt (09-29, 10-06)"): [
            d["t_total_s"] for d in first
            if d["label"] == "corner-09"
            or d["label"].startswith("val-corner-09")],
        ("bo-012 (margin)", "salt (10-13, 10-15)"): [
            d["t_total_s"] for d in doses
            if d["campaign_id"].startswith("salt-margin")
            and d["label"] == "bo-012"],
    }
    y = 0
    yticks, ylabels = [], []
    for probe, by_ctx in warm["probe_predictions"].items():
        for ctx in ("salt (09-29, 10-06)", "salt (10-13, 10-15)", "AlSi10Mg"):
            mean, se = by_ctx[ctx]["t_total_s"]
            ax.plot([max(0, mean - 1.96 * se), mean + 1.96 * se], [y, y],
                    color=SERIES[ctx], lw=3.0, alpha=0.45,
                    solid_capstyle="round")
            ax.scatter(mean, y, s=42, color=SERIES[ctx], zorder=3,
                       edgecolor=SURFACE, lw=0.8)
            for t in obs.get((probe, ctx), []):
                ax.scatter(t, y, marker="|", s=110, color=INK, lw=1.4,
                           zorder=4)
            yticks.append(y)
            ylabels.append(SHORT[ctx])
            rows.append((probe, ctx, mean, se))
            y -= 1
        ax.text(-12, y + 3.55, probe.replace(" (margin)", ", 0 mg margin")
                if "margin" in probe else probe + ", 35 mg margin",
                fontsize=11, color=INK, fontweight="bold", ha="left")
        y -= 1.0
    ax.axvline(180, color=MUTED, lw=1.0, ls=(0, (3, 3)))
    ax.text(186, y + 0.75, "180 s threshold", fontsize=10, color=INK2)
    ax.set_yticks(yticks)
    ax.set_yticklabels(ylabels, fontsize=10.5)
    ax.set_ylim(y + 0.4, 1.1)
    ax.set_xlim(-12, 600)
    ax.set_xlabel("dose time (s): model mean +/- 1.96 SE; | measured doses")
    ax.grid(axis="x", color=GRID, lw=0.8)
    ax.set_axisbelow(True)
    ax.set_title("(c)  Warm-started model: sharp on salt, wide on AlSi10Mg",
                 loc="left", fontsize=12.5, color=INK)
    return rows


def main():
    res, doses = pb.build()
    with open(os.path.join(HERE, "ax_warm_start.json")) as f:
        warm = json.load(f)
    fig, axes = plt.subplots(1, 3, figsize=(19.5, 6.4),
                             gridspec_kw={"width_ratios": [1.15, 1.0, 1.05]})
    panel_rule(axes[0], res, doses)
    panel_taps(axes[1], res, doses)
    panel_model(axes[2], res, doses, warm)
    fig.text(0.01, 0.015,
             "Markers are measured salt doses (both salt campaigns, "
             "09-29 to 10-15) and the AlSi10Mg / Al 4047 production doses. "
             "The bars in (c) are model output from the 95 salt doses only: "
             "no 0.5 g AlSi10Mg dose exists yet.", fontsize=10, color=INK2)
    fig.tight_layout(rect=(0, 0.04, 1, 1), w_pad=2.5)
    out = os.path.join(HERE, "powder_transfer.png")
    fig.savefig(out, dpi=130)
    print("wrote", out)


if __name__ == "__main__":
    main()
