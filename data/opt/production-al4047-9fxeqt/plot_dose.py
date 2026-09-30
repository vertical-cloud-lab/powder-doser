#!/usr/bin/env python3
"""Plot the bulk-only Al 4047 top-up dose from its Zero trial document.

    python3 data/opt/production-al4047-9fxeqt/plot_dose.py [trial json] [out png]

Top: balance reading vs time.  Middle: the commanded auger rpm (the taper
and the no-flow boosts).  Bottom: the endgame against the target and the
3 mg tolerance band.
"""

import json
import os
import re
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt                                # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
UUID = "56a01060-e9d2-493a-9ea5-79ef3300605e"
TRIAL = os.path.join(HERE, "zero", "trial_%s.json" % UUID)
SERIAL = os.path.join(HERE, "zero", "serial_%s.log" % UUID)

SURFACE = "#fcfcfb"
INK = "#0b0b0b"
INK_2 = "#52514e"
GRID = "#e4e3df"
BAND = "#e9e8e4"
MASS = "#2a78d6"
MARK = "#eb6834"


def load(path):
    with open(path) as f:
        doc = json.load(f)
    t, z, rpm, t_end, z_end = [], [], [], None, None
    for row in doc["telemetry"]["rows"]:
        r = row.split(",")
        if r[1] == "bulk":
            t.append(float(r[0]))
            z.append(float(r[2]))
            rpm.append(float(r[11]))
        elif r[1] == "bulk_end":
            t_end, z_end = float(r[0]), float(r[2])
    return doc, t, z, rpm, t_end, z_end


def boost_times(path):
    """Elapsed time of each "no flow ... rpm up" line (its last poll)."""
    out, last = [], None
    with open(path, errors="replace") as f:
        for line in f:
            m = re.search(r"bulk-only\] poll \d+:.*elapsed ([\d.]+) s", line)
            if m:
                last = float(m.group(1))
            elif "rpm up" in line and last is not None:
                out.append(last)
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


def main():
    trial = sys.argv[1] if len(sys.argv) > 1 else TRIAL
    out = sys.argv[2] if len(sys.argv) > 2 else os.path.join(
        HERE, "dose_trace.png")
    doc, t, z, rpm, t_end, z_end = load(trial)
    boosts = boost_times(SERIAL) if os.path.exists(SERIAL) else []
    target = doc["target_g"]
    tol = doc["parameters"]["tolerance_g"]
    oc = doc["outcomes"]
    t_final, g_final = oc["t_total_s"], oc["settled_final_g"]
    taper_g = doc["parameters_executed"].get("bulk_taper_start_g", 0.1) \
        if isinstance(doc.get("parameters_executed"), dict) else 0.1
    t_taper = next((ti for ti, zi in zip(t, z) if target - zi < taper_g),
                   None)

    fig = plt.figure(figsize=(8.6, 8.4), facecolor=SURFACE)
    gs = fig.add_gridspec(3, 1, height_ratios=[1.25, 0.8, 1.05],
                          hspace=0.42)
    ax_m = fig.add_subplot(gs[0])
    ax_r = fig.add_subplot(gs[1], sharex=ax_m)
    ax_e = fig.add_subplot(gs[2])
    for ax in (ax_m, ax_r, ax_e):
        style(ax)

    # -- mass --------------------------------------------------------
    ax_m.axhline(target, color=INK_2, linewidth=1, linestyle=(0, (4, 3)))
    ax_m.text(t[0], target + 0.006, "target {:.4f} g".format(target),
              color=INK_2, fontsize=8.5, va="bottom")
    ax_m.plot(t, z, color=MASS, linewidth=2)
    ax_m.set_ylabel("balance reading (g)", color=INK, fontsize=9.5)
    ax_m.set_title("Balance reading: 40° plate tilt, 2 Hz cadence taps, no "
                   "trickle or tap stage", color=INK, fontsize=10.5,
                   loc="left")
    ax_m.set_ylim(-0.01, target * 1.12)

    # -- rpm ---------------------------------------------------------
    ax_r.step(t, rpm, where="post", color=MASS, linewidth=2)
    ax_r.set_ylabel("auger rpm", color=INK, fontsize=9.5)
    ax_r.set_ylim(0, 112)
    ax_r.set_title("Commanded auger speed: taper over the last 100 mg, "
                   "×1.5 after 3 s with no flow", color=INK, fontsize=10.5,
                   loc="left")
    if t_taper is not None:
        ax_r.axvline(t_taper, color=INK_2, linewidth=1,
                     linestyle=(0, (2, 2)))
        ax_r.text(t_taper - 0.6, 88, "taper starts\n({:.0f} mg to go)".format(
            1000.0 * taper_g), color=INK_2, fontsize=8.5, va="top",
            ha="right")
    for i, tb in enumerate(boosts):
        k = min(range(len(t)), key=lambda j: abs(t[j] - tb))
        k = min(k + 1, len(t) - 1)            # the poll that re-commanded
        tb, after = t[k], rpm[k]
        ax_r.plot([tb], [after], marker="o", markersize=8, color=MARK,
                  markeredgecolor=SURFACE, markeredgewidth=2, zorder=5)
        ax_r.annotate("no flow → rpm up", (tb, after),
                      xytext=(-4 if i == 0 else 6, 16),
                      textcoords="offset points", color=INK, fontsize=8.5,
                      ha="right" if i == 0 else "left")
    ax_r.set_xlabel("time since dose start (s)", color=INK, fontsize=9.5)

    # -- endgame -----------------------------------------------------
    t0 = next(ti for ti, zi in zip(t, z) if target - zi < 0.015) - 1.0
    idx = [i for i, ti in enumerate(t) if ti >= t0]
    err = [1000.0 * (z[i] - target) for i in idx]
    ax_e.axhspan(-1000.0 * tol, 1000.0 * tol, color=BAND, zorder=0)
    ax_e.axhline(0.0, color=INK_2, linewidth=1, linestyle=(0, (4, 3)))
    ax_e.text(t0 + 0.2, 1000.0 * tol + 0.4, "±{:.0f} mg band".format(
        1000.0 * tol), color=INK_2, fontsize=8.5, va="bottom")
    ax_e.plot([t[i] for i in idx], err, color=MASS, linewidth=2,
              marker="o", markersize=3.5)
    ax_e.axvline(t[-1], color=INK_2, linewidth=1, linestyle=(0, (2, 2)))
    ax_e.text(t[-1] - 0.3, -13.5, "auger halted\n({:.0f} rpm)".format(
        rpm[-1]), color=INK_2, fontsize=8.5, ha="right", va="bottom")
    pts = [(t_end, 1000.0 * (z_end - target), "settled\n{:+.2f} mg"),
           (t_final, oc["error_mg"], "scoring read\n{:+.2f} mg")]
    for j, (tx, ex, fmt) in enumerate(pts):
        if tx is None:
            continue
        ax_e.plot([tx], [ex], marker="o", markersize=8, color=MARK,
                  markeredgecolor=SURFACE, markeredgewidth=2, zorder=5)
        ax_e.annotate(fmt.format(ex), (tx, ex), xytext=(0, -12),
                      textcoords="offset points", color=INK, fontsize=8.5,
                      ha="center", va="top")
    ax_e.set_ylim(-16, 6)
    ax_e.set_xlim(t0, t_final + 1.0)
    ax_e.set_ylabel("reading − target (mg)", color=INK, fontsize=9.5)
    ax_e.set_xlabel("time since dose start (s)", color=INK, fontsize=9.5)
    ax_e.set_title("Endgame: the last 15 mg, the halt, the settle and the "
                   "2 s scoring read", color=INK, fontsize=10.5, loc="left")

    fig.suptitle("Al 4047 (9fxeqt) bulk-only top-up, trial {}: {:.4f} g of "
                 "{:.4f} g ({:+.2f} mg) in {:.0f} s".format(
                     UUID[:8], g_final, target, oc["error_mg"],
                     oc["t_total_s"]),
                 color=INK, fontsize=11.5, x=0.06, ha="left", y=0.965)
    fig.savefig(out, dpi=150, facecolor=SURFACE, bbox_inches="tight")
    print("wrote", out)


if __name__ == "__main__":
    main()
