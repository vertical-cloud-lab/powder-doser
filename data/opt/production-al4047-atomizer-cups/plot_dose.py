"""Balance reading and feed rate of trial a5fdadaa (issue #186), from its telemetry.

    python3 data/opt/production-al4047-atomizer-cups/plot_dose.py
"""
import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt                                   # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
TRIAL = os.path.join(HERE, "zero", "trial_a5fdadaa-d609-40bf-9316-af67b75a9b1f.json")

SURFACE, INK, INK2, MUTED, GRID, AXIS, BLUE = (
    "#fcfcfb", "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#c3c2b7", "#2a78d6")


def main():
    doc = json.load(open(TRIAL))
    cols = doc["telemetry"]["header"].split(",")
    rows = [dict(zip(cols, r.split(","))) for r in doc["telemetry"]["rows"]]
    t = [float(r["t_s"]) for r in rows]
    g = [float(r["z_g"]) for r in rows]
    # feed rate over a trailing 4 s window (the firmware's own slope is 2 s and noisier)
    rate_t, rate = [], []
    j = 0
    for i in range(len(t)):
        while t[i] - t[j] > 4.0:
            j += 1
        if t[i] - t[j] >= 3.0:
            rate_t.append(t[i])
            rate.append(1000.0 * (g[i] - g[j]) / (t[i] - t[j]))

    plt.rcParams.update({"font.size": 11, "axes.edgecolor": AXIS, "axes.labelcolor": INK2,
                         "xtick.color": MUTED, "ytick.color": MUTED, "text.color": INK})
    fig, (a, b) = plt.subplots(2, 1, figsize=(8.0, 6.2), sharex=True, facecolor=SURFACE,
                               gridspec_kw={"height_ratios": [3, 2], "hspace": 0.12})
    for ax in (a, b):
        ax.set_facecolor(SURFACE)
        ax.grid(True, color=GRID, linewidth=0.8)
        ax.set_axisbelow(True)
        for s in ("top", "right"):
            ax.spines[s].set_visible(False)

    a.plot(t, g, color=BLUE, linewidth=2)
    a.set_ylabel("balance reading (g)")
    a.set_ylim(0, 0.25)
    a.annotate("86 mg in the first 6 s\n(powder already at the outlet)", xy=(12.0, 0.0858),
               xytext=(22, 0.035), color=INK2, fontsize=10,
               arrowprops={"arrowstyle": "-", "color": MUTED, "linewidth": 1})
    a.annotate("stalled at 0.2028 g\n(target 2.9904 g)", xy=(t[-1], g[-1]), xytext=(78, 0.225),
               color=INK2, fontsize=10, arrowprops={"arrowstyle": "-", "color": MUTED, "linewidth": 1})
    a.set_title("40° tilt, 100 rpm, 2 Hz taps: the auger fed about 1 mg/s after the first 6 s",
                loc="left", fontsize=12, color=INK, pad=10)

    b.plot(rate_t, rate, color=BLUE, linewidth=2)
    b.axhline(2.0 / 3.0, color=MUTED, linewidth=1.2, linestyle=(0, (4, 3)))
    b.text(2, 0.47, "stall line: under 2 mg per 3 s", color=INK2, fontsize=10, ha="left")
    b.set_ylabel("feed rate (mg/s, 4 s window)")
    b.set_xlabel("time since the dose started (s)")
    b.set_yscale("log")
    b.set_ylim(0.2, 30)
    b.set_yticks([0.3, 1, 3, 10, 30])
    b.set_yticklabels(["0.3", "1", "3", "10", "30"])
    b.minorticks_off()
    b.set_xlim(0, 128)

    out = os.path.join(HERE, "dose_trace.png")
    fig.savefig(out, dpi=150, bbox_inches="tight", facecolor=SURFACE)
    print(out)


if __name__ == "__main__":
    main()
