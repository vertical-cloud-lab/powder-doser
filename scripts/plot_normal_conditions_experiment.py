#!/usr/bin/env python3
"""Plot the 2026-07-30 "normal conditions" PID dose experiment.

Reads the raw telemetry logs emitted by
``hardware/test-module/firmware/pid_dose.py`` (D/E/M rows over USB serial)
and renders two figures:

  1. ``pid_normal_conditions_dashboard.png`` -- mass / auger rpm / tilt for the
     three stock replicates, full run including pre- and post-roll.
  2. ``pid_normal_conditions_slugs.png`` -- terminal-approach zoom aligned on
     the auger halt, per-sample delivery increments, and the final-mass ledger.

Usage::

    python scripts/plot_normal_conditions_experiment.py \
        data/pid-dose/2026-07-30_salt
"""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

# Categorical slots 1 and 2 of the validated light-mode palette.
STOCK = "#2a78d6"
VARIANT = "#eb6834"
INK = "#0b0b0b"
INK_2 = "#52514e"
MUTED = "#b8b7b1"
SURFACE = "#fcfcfb"


@dataclass
class Run:
    name: str
    label: str
    meta: dict = field(default_factory=dict)
    t: list = field(default_factory=list)
    mass: list = field(default_factory=list)
    stable: list = field(default_factory=list)
    tilt: list = field(default_factory=list)
    rpm: list = field(default_factory=list)
    taps: list = field(default_factory=list)
    phase: list = field(default_factory=list)
    events: list = field(default_factory=list)

    @property
    def target(self):
        return float(self.meta.get("target_g", 1.0))

    @property
    def halt_t(self):
        """Time of the auger halt (overshoot guard or target window)."""
        for t, msg in self.events:
            if "guard" in msg or "window reached" in msg:
                return t
        return None

    @property
    def final_g(self):
        for t, msg in self.events:
            if "final stable weigh" in msg:
                return float(msg.rsplit(":", 1)[1].strip().split()[0])
        return None


def load(path: Path, label: str) -> Run:
    run = Run(name=path.stem, label=label)
    for line in path.open(newline=""):
        parts = line.strip().split(",")
        if parts[0] == "M" and len(parts) >= 3:
            run.meta[parts[1]] = parts[2]
        elif parts[0] == "E" and len(parts) >= 3:
            run.events.append((int(parts[1]) / 1000.0, ",".join(parts[2:])))
        elif parts[0] == "D" and len(parts) >= 8:
            run.t.append(int(parts[1]) / 1000.0)
            run.mass.append(float("nan") if parts[2] == "nan" else float(parts[2]))
            run.stable.append(parts[3])
            run.tilt.append(float(parts[4]))
            run.rpm.append(float(parts[5]))
            run.taps.append(int(parts[6]))
            run.phase.append(parts[7])
    return run


def tidy(ax, ylabel):
    ax.set_ylabel(ylabel, color=INK_2, fontsize=9)
    ax.grid(True, color=MUTED, linewidth=0.6, alpha=0.5)
    ax.set_axisbelow(True)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(MUTED)
    ax.tick_params(colors=INK_2, labelsize=8, length=3)


def dashboard(stock, out: Path):
    fig, axes = plt.subplots(3, 1, figsize=(11, 8.4), sharex=True,
                             gridspec_kw={"height_ratios": [2.2, 1, 1]})
    fig.patch.set_facecolor(SURFACE)
    for ax in axes:
        ax.set_facecolor(SURFACE)

    target = stock[0].target
    tol = float(stock[0].meta.get("tol_g", 0.002))

    ax = axes[0]
    ax.axhspan(target - tol, target + tol, color=MUTED, alpha=0.55, lw=0)
    ax.axhline(target, color=INK_2, lw=1.0, ls="--")
    ax.annotate("target 1.000 g  (±2 mg band)", xy=(28.0, target),
                xytext=(28.0, target - 0.11), color=INK_2, fontsize=8.5)
    # stack the end labels by rank so they never collide
    rank = {id(r): k for k, r in
            enumerate(sorted(stock, key=lambda x: -x.final_g))}
    for i, r in enumerate(stock):
        ax.plot(r.t, r.mass, color=STOCK, lw=1.6, alpha=0.55 + 0.15 * i,
                label=r.label if i == 0 else None)
        if r.halt_t is not None:
            ax.plot([r.halt_t], [r.final_g], "o", ms=7, mfc=STOCK,
                    mec=SURFACE, mew=2, zorder=5)
        ax.annotate("rep {}: {:.4f} g".format(i + 1, r.final_g),
                    xy=(r.t[-1], r.final_g), xytext=(6, (1 - rank[id(r)]) * 13),
                    textcoords="offset points", color=INK, fontsize=8.5,
                    va="center", annotation_clip=False)
    for t, msg in stock[0].events:
        if "tare" in msg and "sent" in msg:
            for a in axes:
                a.axvline(t, color=MUTED, lw=1.0, ls=":")
            ax.annotate("tare", xy=(t, 0.02), xytext=(3, 0), fontsize=8,
                        textcoords="offset points", color=INK_2)
    tidy(ax, "cup mass (g)")
    ax.set_title("Powder doser -- stock PID controller, default parameters, 1.000 g salt "
                 "(3 replicates, 2026-07-30)",
                 color=INK, fontsize=11.5, loc="left", pad=10)
    ax.legend(frameon=False, fontsize=9, labelcolor=INK_2, loc="center left")

    ax = axes[1]
    for i, r in enumerate(stock):
        ax.plot(r.t, r.rpm, color=STOCK, lw=1.6, alpha=0.55 + 0.15 * i)
    tidy(ax, "auger cmd (rpm)")

    ax = axes[2]
    for i, r in enumerate(stock):
        ax.plot(r.t, r.tilt, color=STOCK, lw=1.6, alpha=0.55 + 0.15 * i)
    tidy(ax, "plate tilt (deg)")
    ax.set_xlabel("time since controller start (s)   |   taps commanded during dose: 0 in all runs",
                  color=INK_2, fontsize=9)

    fig.tight_layout(rect=(0, 0, 0.93, 1))
    fig.savefig(out, dpi=150, facecolor=SURFACE)
    plt.close(fig)
    print("wrote", out)


def slugs(stock, variant, out: Path):
    fig, axes = plt.subplots(1, 3, figsize=(13.5, 4.4))
    fig.patch.set_facecolor(SURFACE)
    for ax in axes:
        ax.set_facecolor(SURFACE)

    target = stock[0].target
    tol = float(stock[0].meta.get("tol_g", 0.002))

    # -- panel 1: terminal approach, aligned on the auger halt --------------
    ax = axes[0]
    ax.axhspan(target - tol, target + tol, color=MUTED, alpha=0.55, lw=0)
    ax.axhline(target, color=INK_2, lw=1.0, ls="--")
    ax.axvline(0.0, color=INK_2, lw=1.0, ls=":")
    for i, r in enumerate(stock + variant):
        colour = STOCK if r in stock else VARIANT
        h = r.halt_t
        xs = [t - h for t in r.t]
        pts = [(x, m) for x, m in zip(xs, r.mass) if -4.5 <= x <= 3.0]
        ax.plot([p[0] for p in pts], [p[1] for p in pts], color=colour, lw=1.7,
                alpha=0.8, label=(r.label if (i == 0 or r in variant) else None))
    ax.annotate("auger halt", xy=(0, target - 0.16), xytext=(3, 0), fontsize=8,
                textcoords="offset points", color=INK_2, rotation=90)
    tidy(ax, "cup mass (g)")
    ax.set_xlabel("time relative to auger halt (s)", color=INK_2, fontsize=9)
    ax.set_title("Terminal approach: powder arrives as slugs",
                 color=INK, fontsize=10.5, loc="left")
    ax.legend(frameon=False, fontsize=8.5, labelcolor=INK_2, loc="upper left")

    # -- panel 2: per-sample delivery increments ----------------------------
    ax = axes[1]
    r = stock[0]
    dose = [(t, m) for t, m, p in zip(r.t, r.mass, r.phase)
            if p == "dose" and m == m]
    xs = [dose[i][0] - dose[0][0] for i in range(1, len(dose))]
    dm = [(dose[i][1] - dose[i - 1][1]) * 1000.0 for i in range(1, len(dose))]
    ax.axhline(0, color=MUTED, lw=1.0)
    ax.axhline(2.0, color=INK_2, lw=1.0, ls="--")
    ax.annotate("±2 mg tolerance", xy=(9.6, 2.0), xytext=(0, 5), fontsize=8,
                textcoords="offset points", color=INK_2)
    ax.plot(xs, dm, color=STOCK, lw=1.4)
    tidy(ax, "mass delivered per sample (mg)")
    ax.set_xlabel("time since dose start (s)   [replicate 1]", color=INK_2, fontsize=9)
    ax.set_title("Delivery is periodic: ~1.35 s slugs, up to 27 mg/sample",
                 color=INK, fontsize=10.5, loc="left")

    # -- panel 3: final-mass ledger ----------------------------------------
    ax = axes[2]
    runs = stock + variant
    names = [r.label.split(" (")[0] if r in variant else "rep {}".format(i + 1)
             for i, r in enumerate(runs)]
    errs = [(r.final_g - target) * 1000.0 for r in runs]
    colours = [STOCK if r in stock else VARIANT for r in runs]
    bars = ax.bar(names, errs, color=colours, width=0.62)
    ax.axhspan(-tol * 1000, tol * 1000, color=MUTED, alpha=0.55, lw=0)
    ax.axhline(0, color=INK_2, lw=1.0)
    for b, e in zip(bars, errs):
        ax.annotate("{:+.1f}".format(e), xy=(b.get_x() + b.get_width() / 2, e),
                    xytext=(0, 4), textcoords="offset points",
                    ha="center", fontsize=9, color=INK)
    tidy(ax, "final error vs 1.000 g (mg)")
    ax.set_title("Every run overshoots; ±2 mg band shaded",
                 color=INK, fontsize=10.5, loc="left")
    ax.tick_params(axis="x", labelrotation=20)

    fig.tight_layout()
    fig.savefig(out, dpi=150, facecolor=SURFACE)
    plt.close(fig)
    print("wrote", out)


def main():
    d = Path(sys.argv[1] if len(sys.argv) > 1
             else "data/pid-dose/2026-07-30_salt")
    stock = [load(d / "pid_normal_run{}_salt.log".format(n),
                  "stock PID, default params (n=3)") for n in (1, 2, 3)]
    variant = [load(d / "pid_slowtail_run4_salt.log",
                    "slow-tail diagnostic (5 rpm cap below 0.2 g to go)")]
    dashboard(stock, d / "pid_normal_conditions_dashboard.png")
    slugs(stock, variant, d / "pid_normal_conditions_slugs.png")


if __name__ == "__main__":
    main()
