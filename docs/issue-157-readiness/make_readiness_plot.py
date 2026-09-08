#!/usr/bin/env python3
"""Rebuild readiness_replay.png from the drift-night CSVs.

Replays docs/issue-157-drift/ through scripts/balance_readiness.py (the
same functions the gate runs, not a reimplementation) and draws what the
gate saw and predicted, against the fixed one-hour rule it replaces.
"""

from __future__ import annotations

import math
import statistics
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import balance_readiness as br  # noqa: E402

DRIFT = ROOT / "docs" / "issue-157-drift"
# Segment start offsets (s) from the wall clocks in the drift README;
# t=0 is 22:37:57 MDT, the start of sampling after the disturbance.
SEGMENTS = [("seg0_smoke.csv", 0), ("seg1.csv", 230), ("seg2.csv", 558),
            ("seg3.csv", 887), ("seg4.csv", 1215), ("seg5.csv", 1544)]

BLOCK_G = br.limit_for(180.0, 5.0)

# Palette: categorical slots 1-2 plus ink/surface tokens (validated).
BLUE, ORANGE = "#2a78d6", "#eb6834"
INK, INK2, GRID, SURFACE = "#0b0b0b", "#52514e", "#e3e2dd", "#fcfcfb"


def mdt(minutes: float) -> str:
    m = 22 * 60 + 37 + 57 / 60 + minutes          # from 22:37:57
    return "{:02.0f}:{:02.0f}".format(m // 60, m % 60)


def main() -> None:
    mids, rates, preds = [], [], []
    history = []
    for name, off in SEGMENTS:
        t, mg, status = br.read_csv(str(DRIFT / name))
        s = br.analyze(t, mg, status)
        mid = (off + (t[-1] - t[0]) / 2.0) / 60.0
        history.append((mid * 60.0, s["rate_mg_min"]))
        tau = br.fit_tau_min(history) or br.DEFAULT_TAU_MIN
        preds.append(mid + br.eta_min(s["rate_mg_min"], BLOCK_G, tau))
        mids.append(mid)
        rates.append(abs(s["rate_mg_min"]))

    # Full-record fit, for the drawn decay and the "actual" crossing.
    ys = [math.log(r) for r in rates]
    mt, my = statistics.mean(mids), statistics.mean(ys)
    b = (sum((mids[i] - mt) * (ys[i] - my) for i in range(len(mids)))
         / sum((v - mt) ** 2 for v in mids))
    tau_full = -1.0 / b
    r0 = math.exp(my - b * mt)
    t_cross = tau_full * math.log(r0 / BLOCK_G)

    fig, (ax1, ax2) = plt.subplots(
        1, 2, figsize=(10.5, 4.3), dpi=150, facecolor=SURFACE)

    # --- Panel A: the decay the gate measures -------------------------
    ax1.set_facecolor(SURFACE)
    tt = [x * t_cross * 1.12 / 120 for x in range(121)]
    ax1.plot(tt, [r0 * math.exp(-x / tau_full) for x in tt],
             color=BLUE, lw=2, zorder=2)
    ax1.plot(mids, rates, "o", color=BLUE, ms=7,
             mec=SURFACE, mew=1.5, zorder=3)
    for lim, name in [(BLOCK_G, "block G limit ({:.1f})".format(BLOCK_G)),
                      (5.0, "60 s dose limit (5.0)"),
                      (17.6, "block H limit (17.6)")]:
        ax1.axhline(lim, color=INK2, lw=1, ls=(0, (4, 3)), alpha=0.55,
                    zorder=1)
        ax1.text(t_cross * 1.12, lim * 1.06, name, ha="right", va="bottom",
                 fontsize=8, color=INK2)
    ax1.plot([t_cross], [BLOCK_G], "o", ms=9, mfc=SURFACE, mec=BLUE,
             mew=2, zorder=4)
    ax1.annotate("gate opens\n{} ({:.0f} min)".format(mdt(t_cross), t_cross),
                 (t_cross, BLOCK_G), textcoords="offset points",
                 xytext=(-8, -34), ha="right", fontsize=9, color=INK)
    ax1.text(mids[2], rates[2] * 1.25,
             "measured drift rate\n(fit: τ = {:.0f} min)".format(tau_full),
             fontsize=9, color=INK, ha="left")
    ax1.set_yscale("log")
    ax1.set_yticks([1, 2, 3, 5, 10, 20, 30])
    ax1.set_yticklabels(["1", "2", "3", "5", "10", "20", "30"])
    ax1.yaxis.set_minor_formatter(matplotlib.ticker.NullFormatter())
    ax1.set_ylim(1.1, 33)
    ax1.set_xlim(-1.5, t_cross * 1.16)
    ax1.set_xlabel("minutes after the disturbance (22:38 MDT)", fontsize=9)
    ax1.set_ylabel("|drift rate|  (mg/min)", fontsize=9)
    ax1.set_title("Drift decays exponentially — so measure it, don't wait it out",
                  fontsize=10, color=INK, pad=10)

    # --- Panel B: what the gate predicted, sample by sample -----------
    ax2.set_facecolor(SURFACE)
    ax2.axhline(60.0, color=INK2, lw=1.4, ls=(0, (4, 3)), alpha=0.8)
    ax2.text(0.2, 60.8, "fixed “wait an hour” rule ({})".format(mdt(60)),
             fontsize=8.5, color=INK2, va="bottom")
    ax2.axhline(t_cross, color=INK2, lw=1.4, alpha=0.8)
    ax2.text(0.2, t_cross + 1.6, "actual crossing, extrapolated\nfrom the "
             "full record ({})".format(mdt(t_cross)),
             fontsize=8.5, color=INK2, va="bottom", ha="left")
    ax2.plot(mids, preds, "-o", color=ORANGE, lw=2, ms=7,
             mec=SURFACE, mew=1.5, zorder=3)
    ax2.annotate("the gate's live prediction,\nfrom data available at that "
                 "moment", (mids[2], preds[2]), textcoords="offset points",
                 xytext=(6, -30), fontsize=9, color=INK)
    ax2.set_xlabel("when the prediction was made\n(minutes after the disturbance)",
                   fontsize=9)
    ax2.set_ylabel("predicted “ready for block G”\n(minutes after the disturbance)",
                   fontsize=9)
    ax2.set_ylim(0, 70)
    ax2.set_xlim(-1.5, 31)
    ax2.set_title("Every live prediction beat the fixed one-hour rule",
                  fontsize=10, color=INK, pad=10)

    for ax in (ax1, ax2):
        ax.grid(True, color=GRID, lw=0.7)
        ax.tick_params(colors=INK2, labelsize=8.5)
        for side in ("top", "right"):
            ax.spines[side].set_visible(False)
        for side in ("left", "bottom"):
            ax.spines[side].set_color(GRID)

    fig.tight_layout()
    out = Path(__file__).resolve().parent / "readiness_replay.png"
    fig.savefig(out, facecolor=SURFACE, bbox_inches="tight")
    print("wrote", out)


if __name__ == "__main__":
    main()
