"""Issue #186, 2026-10-20 (second session): the balance through the reverse turns at 0°, the
forward/reverse A/B test and the stepwise reverse dose, from the raw serial log.

    python3 data/opt/production-al4047-atomizer-cups/plot_reverse.py
"""
import os
import re

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt                                   # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
LOG = os.path.join(HERE, "zero", "serial_readback_20261020b.log")
SURFACE, INK, INK2, MUTED, GRID, AXIS = (
    "#fcfcfb", "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#c3c2b7")
REV, FWD = "#2a78d6", "#eb6834"              # categorical slots 1-2 of the reference palette
# already in the cup but below the current tare: 10-19 leak, a5fdadaa, b13e5997
BELOW_TARE_G = 0.0103 + 0.2028 + 0.0029
TARGET_G = 3.0407


def parse():
    """-> list of sessions; each {"cmds", "reads": [(turns, g, stable)],
    "moves": [(turns, deg, index of the next read)]}.  ``turns`` counts every auger turn
    either way since the first session."""
    sessions, turns = [], 0.0
    for line in open(LOG, errors="replace"):
        line = line.rstrip("\n")
        m = re.match(r"--- rig_cmd (.*) ---$", line)
        if m:
            sessions.append({"cmds": m.group(1), "reads": [], "moves": []})
            continue
        if not sessions:
            continue
        s = sessions[-1]
        m = re.match(r">> r (-?[\d.]+)$", line)
        if m:
            deg = float(m.group(1))
            s["moves"].append((turns, deg, len(s["reads"])))
            turns += abs(deg) / 360.0
            continue
        m = re.match(r"\[scale\] (ST|US) (-?[\d.]+) g", line)
        if m:
            s["reads"].append((turns, float(m.group(2)), m.group(1) == "ST"))
    return sessions


def steps(sessions):
    """-> [(turns at start, deg, mg added)]: the last read before each move to the last
    read before the next move (or the session's end).  Without taps or a stable-read
    wait between moves, that read can still be marked unstable."""
    out = []
    for s in sessions:
        reads, moves = s["reads"], s["moves"]
        for k, (t, deg, i_read) in enumerate(moves):
            if i_read == 0:
                continue
            before = reads[i_read - 1][1]
            j = moves[k + 1][2] if k + 1 < len(moves) else len(reads)
            if j - 1 < i_read:
                continue
            after = reads[j - 1][1]
            out.append((t, deg, 1000.0 * (after - before)))
    return out


def main():
    sessions = parse()
    plt.rcParams.update({"font.size": 11, "axes.edgecolor": AXIS, "axes.labelcolor": INK2,
                         "xtick.color": MUTED, "ytick.color": MUTED, "text.color": INK})
    fig, (a, b) = plt.subplots(2, 1, figsize=(8.6, 7.0), sharex=True, facecolor=SURFACE,
                               gridspec_kw={"height_ratios": [1.25, 1], "hspace": 0.14})
    for ax in (a, b):
        ax.set_facecolor(SURFACE)
        ax.grid(True, color=GRID, linewidth=0.8)
        ax.set_axisbelow(True)
        for s in ("top", "right"):
            ax.spines[s].set_visible(False)

    pts = [(t, g + BELOW_TARE_G) for s in sessions for t, g, stable in s["reads"] if stable]
    a.plot([p[0] for p in pts], [p[1] for p in pts], color=INK2, linewidth=1.6)
    a.axhline(TARGET_G, color=MUTED, linewidth=1, linestyle="--")
    a.text(20.2, TARGET_G - 0.07, "target: 3.0407 g of powder (7.5 wt%)", color=INK2,
           fontsize=10, va="top", ha="right")
    a.text(0.6, 0.42, "first 12.75 reverse turns:\n+7 mg", color=INK2, fontsize=10)
    a.text(45.6, 2.62, "3.0432 g\n(+2.5 mg)", color=INK2, fontsize=10, ha="right",
           va="top")
    a.set_ylabel("powder in the cup (g)")
    a.set_ylim(0, 3.35)

    st = steps(sessions)
    for t, deg, mg in st:
        if abs(deg) < 179:
            continue
        b.scatter([t], [mg], s=22, color=REV if deg < 0 else FWD, zorder=3, linewidths=0)
    b.scatter([], [], s=22, color=REV, label="half turn in reverse")
    b.scatter([], [], s=22, color=FWD, label="half turn forward")
    b.legend(loc="upper left", frameon=False, fontsize=9.5, labelcolor=INK2, handletextpad=0.3)
    b.set_ylabel("mg added per half turn")
    b.set_xlabel("auger turns since the session started (either direction)")
    b.set_ylim(-5, 92)

    # phase boundaries: the session (rig_cmd call) where each phase starts
    starts = {}
    for s in sessions:
        if s["moves"]:
            c = s["cmds"]
            key = ("dose" if "dose:" in c else "ab" if "tap4" in c else
                   "rev" if "rev" not in starts else None)
            if key and key not in starts:
                starts[key] = s["moves"][0][0]
    a.set_title("Reversing at 0° freed the outlet after about 13 turns. After that the tube fed\n"
                "in both directions, and taps alone moved nothing",
                loc="left", fontsize=12, color=INK, pad=10)
    for key, label in (("rev", "reverse + taps"), ("ab", "A/B test"),
                       ("dose", "stepwise reverse dose")):
        if key in starts:
            for ax in (a, b):
                ax.axvline(starts[key], color=AXIS, linewidth=1)
            a.text(starts[key] + 0.3, 3.25, label, color=INK2, fontsize=9.5, va="top")

    out = os.path.join(HERE, "reverse_trace.png")
    fig.savefig(out, dpi=150, bbox_inches="tight", facecolor=SURFACE)
    print(out)
    for t, deg, mg in st:
        print("{:7.2f} turns {:+7.1f} deg {:+7.1f} mg".format(t, deg, mg))


if __name__ == "__main__":
    main()
