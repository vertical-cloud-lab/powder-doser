#!/usr/bin/env python3
"""Plot one production dose from its Zero trial document.

    python3 data/opt/production-alsi10mg/plot_dose.py [trial json] [out png]

Top: the whole dose (reading vs time, by phase).  Bottom: the endgame
from the bulk halt on, with the target and the tolerance band.
"""

import json
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt                                # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
TRIAL = os.path.join(HERE, "zero",
                     "trial_64714f7c-c9ed-4ebe-887f-87a7e9bc16b0.json")

SURFACE = "#fcfcfb"
INK = "#0b0b0b"
INK_2 = "#52514e"
GRID = "#e4e3df"
PHASES = [("bulk", "Bulk (auger 100 rpm, 40°, 2 Hz taps)", "#2a78d6"),
          ("trickle", "Trickle (rate-PI, 10°)", "#eb6834"),
          ("tap", "Taps (15°)", "#1baf7a")]


def load(path):
    with open(path) as f:
        doc = json.load(f)
    rows = [r.split(",") for r in doc["telemetry"]["rows"]]
    series = {}
    for r in rows:
        phase = "trickle" if r[1] == "trickle_end" else r[1]
        series.setdefault(phase, []).append((float(r[0]), float(r[2])))
    return doc, series


def style(ax):
    ax.set_facecolor(SURFACE)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(INK_2)
    ax.tick_params(colors=INK_2, labelsize=9)
    ax.grid(True, color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)


def main(argv):
    path = argv[1] if len(argv) > 1 else TRIAL
    out = argv[2] if len(argv) > 2 else os.path.join(HERE, "dose_trace.png")
    doc, series = load(path)
    target = doc["target_g"]
    tol = doc["parameters"]["tolerance_g"]
    o = doc["outcomes"]
    t_end = o["t_total_s"]
    final = o["settled_final_g"]

    fig, (top, bot) = plt.subplots(2, 1, figsize=(9, 7.2), dpi=150,
                                   gridspec_kw={"height_ratios": [1, 1.15]})
    fig.patch.set_facecolor(SURFACE)
    for ax in (top, bot):
        style(ax)

    # the bulk series ends on the settled read after the halt; link the
    # phases so the trace is continuous
    prev = None
    for key, label, color in PHASES:
        pts = series.get(key, [])
        if prev is not None:
            pts = [prev] + pts
        t = [p[0] for p in pts]
        m = [p[1] for p in pts]
        top.plot(t, m, color=color, linewidth=2, label=label,
                 solid_capstyle="round")
        bot.plot(t, [1000.0 * (v - target) for v in m], color=color,
                 linewidth=2, marker="o" if key == "tap" else None,
                 markersize=3.2, markeredgewidth=0, label=label)
        prev = pts[-1]

    ev = doc["stop_events"][0]
    top.axhline(target, color=INK_2, linewidth=1, linestyle=(0, (4, 3)))
    top.text(t_end, target + 0.12, "target {:.3f} g".format(target),
             ha="right", va="bottom", fontsize=9, color=INK_2)
    first_flow = next(t for t, m in series["bulk"] if m > 0.01)
    top.annotate("auger priming after the fresh load:\nno flow for {:.0f} s"
                 .format(first_flow - series["bulk"][0][0]),
                 xy=(first_flow, 0.05), xytext=(70, 0.7),
                 fontsize=9, color=INK_2,
                 arrowprops={"arrowstyle": "-", "color": INK_2, "lw": 0.8})
    top.annotate("steady bulk flow about 0.25 g/s\nhalt at {:.3f} g, then "
                 "+{:.0f} mg afterflow".format(ev["m_stop_g"],
                                               1000.0 * ev["afterflow_g"]),
                 xy=(ev["t_stop_s"] - 2.5, ev["m_stop_g"]),
                 xytext=(92, 4.2), fontsize=9, color=INK_2,
                 arrowprops={"arrowstyle": "-", "color": INK_2, "lw": 0.8})
    top.set_xlim(0, t_end + 8)
    top.set_ylim(-0.2, target + 0.6)
    top.set_ylabel("Delivered mass (g)", color=INK, fontsize=10)
    top.legend(loc="lower right", frameon=False, fontsize=9,
               labelcolor=INK)
    top.set_title("Whole dose", loc="left", fontsize=10, color=INK)

    # endgame, in mg from the target
    bot.axhspan(-1000.0 * tol, 1000.0 * tol, color=GRID, alpha=0.9,
                linewidth=0)
    bot.axhline(0, color=INK_2, linewidth=1, linestyle=(0, (4, 3)))
    bot.text(ev["t_stop_s"] - 1, 1000.0 * tol + 1.5,
             "target, ±{:.0f} mg band".format(1000.0 * tol),
             fontsize=9, color=INK_2, va="bottom")
    bot.plot([t_end], [1000.0 * (final - target)], marker="D",
             markersize=6, color=INK, linestyle="none")
    bot.annotate("scoring read after 2 s settle:\n{:.4f} g ({:+.1f} mg)"
                 .format(final, 1000.0 * (final - target)),
                 xy=(t_end, 1000.0 * (final - target)),
                 xytext=(t_end - 95, -40), fontsize=9, color=INK,
                 arrowprops={"arrowstyle": "-", "color": INK_2, "lw": 0.8})
    tap = series["tap"]
    bot.annotate("{} tap cycles in {:.0f} s, about {:.1f} mg each"
                 .format(len(tap), o["t_tap_s"],
                         1000.0 * (tap[-1][1] - series["trickle"][-1][1])
                         / len(tap)),
                 xy=(tap[len(tap) // 3][0], 1000.0 * (tap[len(tap) // 3][1]
                                                      - target)),
                 xytext=(150, -95), fontsize=9, color=INK_2,
                 arrowprops={"arrowstyle": "-", "color": INK_2, "lw": 0.8})
    bot.set_xlim(ev["t_stop_s"] - 4, t_end + 8)
    bot.set_ylim(-130, 12)
    bot.set_xlabel("Time since the dose command (s)", color=INK,
                   fontsize=10)
    bot.set_ylabel("Error from target (mg)", color=INK, fontsize=10)
    bot.set_title("Endgame from the bulk halt", loc="left", fontsize=10,
                  color=INK)

    fig.suptitle("AlSi10Mg, 8 g target with the salt-optimized parameters: "
                 "{:.4f} g in {:.0f} s".format(final, t_end),
                 x=0.07, ha="left", fontsize=11.5, color=INK)
    fig.tight_layout(rect=(0, 0, 1, 0.97))
    fig.savefig(out, facecolor=SURFACE)
    print(out)


if __name__ == "__main__":
    main(sys.argv)
