"""Mass delivered by the three stalled doses of issue #186 (10-19 at 40 deg, 10-20 at 60 and 75 deg),
from their telemetry.

    python3 data/opt/production-al4047-atomizer-cups/plot_unclog.py
"""
import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt                                   # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
SURFACE, INK, INK2, MUTED, GRID, AXIS = (
    "#fcfcfb", "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#c3c2b7")
# categorical slots 1-3 of the reference palette, in fixed order
DOSES = [
    ("a5fdadaa-d609-40bf-9316-af67b75a9b1f", "#2a78d6", "10-19: 40°"),
    ("b13e5997-8beb-4658-a0cc-859a1eea635b", "#eb6834", "10-20: 60°"),
    ("f6a3403f-d381-4824-869e-82675832a916", "#1baf7a", "10-20: 75°"),
]


def load(uuid):
    doc = json.load(open(os.path.join(HERE, "zero", "trial_{}.json".format(uuid))))
    cols = doc["telemetry"]["header"].split(",")
    rows = [dict(zip(cols, r.split(","))) for r in doc["telemetry"]["rows"]]
    t0 = float(rows[0]["t_s"])                     # first poll after the auger started
    t = [float(r["t_s"]) - t0 for r in rows]
    mg = [1000.0 * float(r["z_g"]) for r in rows]
    out = doc["outcomes"]
    p = doc["parameters_executed"]
    rpm = 60.0 * out["auger_rev"] / out["t_bulk_s"]
    hz = out["taps"] / out["t_bulk_s"]
    label = "{:.0f}° tilt, {:.0f} rpm, {:.1f} taps/s: {:.1f} mg in {:.0f} s".format(
        p["bulk_tilt_deg"], rpm, hz, 1000.0 * out["settled_final_g"], t[-1])
    return t, mg, label


def main():
    plt.rcParams.update({"font.size": 11, "axes.edgecolor": AXIS, "axes.labelcolor": INK2,
                         "xtick.color": MUTED, "ytick.color": MUTED, "text.color": INK})
    fig, (a, b) = plt.subplots(2, 1, figsize=(8.6, 6.6), sharex=True, facecolor=SURFACE,
                               gridspec_kw={"height_ratios": [1, 1], "hspace": 0.16})
    for ax in (a, b):
        ax.set_facecolor(SURFACE)
        ax.grid(True, color=GRID, linewidth=0.8)
        ax.set_axisbelow(True)
        for s in ("top", "right"):
            ax.spines[s].set_visible(False)

    data = [(load(u), color, tag) for u, color, tag in DOSES]
    for (t, mg, label), color, tag in data:
        for ax in (a, b):
            ax.plot(t, mg, color=color, linewidth=2, label="{}: {}".format(tag[:5], label))

    a.set_ylim(0, 230)
    a.set_ylabel("mass delivered (mg)")
    a.text(119, 207, "40°: 86 mg in the first 6 s, then about 1 mg/s",
           color=INK2, fontsize=10, ha="right", va="bottom")
    a.set_title("Steeper tilt, 109 rpm and faster taps fed less, not more: the auger turns but\n"
                "nothing reaches the outlet (salt at 100 rpm feeds about 190 mg/s)",
                loc="left", fontsize=12, color=INK, pad=10)

    b.set_ylim(0, 12)
    b.set_ylabel("mass delivered (mg)\nzoomed to 0-12 mg")
    (tb, mb, _), _, _ = data[1]
    (tc, mc, _), _, _ = data[2]
    b.text(tb[-1] + 1.0, mb[-1], "60°: stalled", color=INK2, fontsize=10, va="center")
    b.text(tc[-1] + 1.0, mc[-1], "75°: stalled", color=INK2, fontsize=10, va="center")
    b.text(9, 10.6, "40° (off this scale after 1 s)", color=INK2, fontsize=10, va="center")
    b.legend(loc="upper right", frameon=False, fontsize=9.5, labelcolor=INK2, handlelength=1.6)
    b.set_xlabel("time since the auger started (s)")
    b.set_xlim(0, 122)

    out = os.path.join(HERE, "unclog_trace.png")
    fig.savefig(out, dpi=150, bbox_inches="tight", facecolor=SURFACE)
    print(out)


if __name__ == "__main__":
    main()
