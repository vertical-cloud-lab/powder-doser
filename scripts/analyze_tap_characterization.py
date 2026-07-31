#!/usr/bin/env python3
"""Analyze the single-tap / lip-depletion characterization experiment.

Reads the raw telemetry emitted by
``hardware/test-module/firmware/tap_characterize.py`` (P/D/E/M rows over USB
serial) and produces:

  * ``taps_tidy.csv``    -- one row per single tap (angle, rep, tap index,
                            marginal yield, cumulative yield)
  * ``trials_summary.csv`` -- one row per (angle, rep) trial
  * ``tap_depletion.png``  -- marginal yield vs tap index, per tilt angle
  * ``tap_model.png``      -- cumulative yield + fitted lip-inventory model,
                             tap gain vs tilt, refill per revolution vs tilt

Model fitted per (angle, rep):  y_i = y_inf + A * r^(i-1)
  A       first-tap yield above the floor   (mg)
  r       per-tap depletion ratio           (dimensionless)
  y_inf   non-depleting floor               (mg/tap)
  M_lip = A / (1 - r)                       extractable lip inventory (mg)

Usage::

    python scripts/analyze_tap_characterization.py \
        data/tap-characterization/2026-07-31_salt
"""

from __future__ import annotations

import csv
import sys
from collections import defaultdict
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

# Tilt is an ORDERED quantity -> ordinal blue ramp (validated light-mode
# steps 250/400/500/650; nothing lighter than 250 on the light surface).
ANGLE_COLORS = ["#86b6ef", "#3987e5", "#256abf", "#104281"]
ACCENT = "#eb6834"          # categorical slot 2, for the non-tilt series
INK = "#0b0b0b"
INK_2 = "#52514e"
MUTED = "#b8b7b1"
SURFACE = "#fcfcfb"


def parse(log_path: Path):
    """Return (meta, settled_points, raw_samples)."""
    meta, pts, raw = {}, [], []
    for line in log_path.read_text().splitlines():
        f = line.strip().split(",")
        if f[0] == "M" and len(f) >= 3:
            meta[f[1]] = ",".join(f[2:])
        elif f[0] == "P" and len(f) >= 8:
            pts.append(
                dict(t_ms=int(f[1]), trial=int(f[2]), angle=float(f[3]),
                     rep=int(f[4]), idx=int(f[5]), kind=f[6],
                     mass_g=None if f[7] == "nan" else float(f[7]))
            )
        elif f[0] == "D" and len(f) >= 7:
            raw.append(
                dict(t_ms=int(f[1]), trial=int(f[2]), idx=int(f[3]),
                     kind=f[4],
                     mass_g=None if f[5] == "nan" else float(f[5]),
                     stable=f[6])
            )
    return meta, pts, raw


def build_trials(pts, n_ctrl, n_taps, n_post):
    """Collapse settled points into per-trial records (masses in mg)."""
    by_trial = defaultdict(dict)
    info = {}
    for p in pts:
        by_trial[p["trial"]][(p["kind"], p["idx"])] = p["mass_g"]
        info[p["trial"]] = (p["angle"], p["rep"])
    trials = []
    for trial in sorted(by_trial):
        d = by_trial[trial]
        angle, rep = info[trial]
        base, prime = d[("base", 0)], d[("prime", 0)]
        ctrl = [d[("ctrl", i)] for i in range(1, n_ctrl + 1)]
        taps = [d[("tap", i)] for i in range(1, n_taps + 1)]
        post = [d[("post", i)] for i in range(1, n_post + 1)]
        start = ctrl[-1]                      # mass just before tap 1
        marg = [(taps[0] - start) * 1000.0]
        marg += [(taps[i] - taps[i - 1]) * 1000.0 for i in range(1, len(taps))]
        trials.append(dict(
            trial=trial, angle=angle, rep=rep,
            prime_mg=(prime - base) * 1000.0,
            ctrl_mg_per_interval=(ctrl[-1] - prime) * 1000.0 / len(ctrl),
            post_mg_per_interval=(post[-1] - taps[-1]) * 1000.0 / len(post),
            marginal_mg=marg,
            total_mg=sum(marg),
        ))
    return trials


def fit_decay(y):
    """Grid+refine least-squares fit of y_i = y_inf + A * r**(i-1)."""
    n = len(y)
    best = None
    for k in range(1, 1000):                  # r in (0.001 .. 0.999)
        r = k / 1000.0
        b = [r ** i for i in range(n)]
        # linear LS for [A, y_inf] given r
        sbb = sum(v * v for v in b)
        sb = sum(b)
        sby = sum(bi * yi for bi, yi in zip(b, y))
        sy = sum(y)
        det = sbb * n - sb * sb
        if abs(det) < 1e-12:
            continue
        A = (sby * n - sb * sy) / det
        y_inf = (sbb * sy - sb * sby) / det
        if A < 0:
            continue
        sse = sum((y_inf + A * bi - yi) ** 2 for bi, yi in zip(b, y))
        if best is None or sse < best[0]:
            best = (sse, A, r, y_inf)
    if best is None:
        return dict(A=float("nan"), r=float("nan"), y_inf=float("nan"),
                    m_lip=float("nan"), sse=float("nan"))
    sse, A, r, y_inf = best
    return dict(A=A, r=r, y_inf=max(0.0, y_inf), m_lip=A / (1.0 - r),
                sse=sse)


def mean(xs):
    xs = [x for x in xs if x == x]
    return sum(xs) / len(xs) if xs else float("nan")


def sd(xs):
    xs = [x for x in xs if x == x]
    if len(xs) < 2:
        return 0.0
    m = mean(xs)
    return (sum((x - m) ** 2 for x in xs) / (len(xs) - 1)) ** 0.5


def style(ax):
    ax.set_facecolor(SURFACE)
    ax.grid(True, color=MUTED, linewidth=0.6, alpha=0.45)
    ax.set_axisbelow(True)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(MUTED)
    ax.tick_params(colors=INK_2, labelsize=9)


def plot_depletion(by_angle, angles, n_taps, ctrl_mg, out):
    fig, axes = plt.subplots(1, 2, figsize=(12.5, 5.0), facecolor=SURFACE)
    ax, ax2 = axes
    xs = list(range(1, n_taps + 1))
    for c, a in zip(ANGLE_COLORS, angles):
        ts = by_angle[a]
        for t in ts:                                    # individual replicates
            ax.plot(xs, t["marginal_mg"], color=c, linewidth=0.9, alpha=0.35,
                    zorder=2)
        m = [mean([t["marginal_mg"][i] for t in ts]) for i in range(n_taps)]
        ax.plot(xs, m, color=c, linewidth=2.0, marker="o", markersize=5.5,
                markeredgecolor=SURFACE, markeredgewidth=1.2, zorder=3)
        ax.annotate("{:.0f}°".format(a), (xs[0], m[0]),
                    xytext=(-8, 0), textcoords="offset points", color=c,
                    fontsize=10, fontweight="bold", ha="right", va="center")
    ax.axhline(ctrl_mg, color=ACCENT, linewidth=1.6, linestyle="--", zorder=1)
    ax.annotate("no-tap control interval: {:+.2f} mg".format(ctrl_mg),
                (1, ctrl_mg), xytext=(0, -14), textcoords="offset points",
                color=ACCENT, fontsize=9, ha="left")
    ax.set_ylim(bottom=-2.6)
    style(ax)
    ax.set_xticks(xs)
    ax.set_xlabel("tap index since the priming rotation", color=INK_2)
    ax.set_ylabel("marginal yield of that single tap (mg)", color=INK_2)
    ax.set_title("Successive single taps deplete the tube lip",
                 color=INK, fontsize=12, loc="left", fontweight="bold")

    # cumulative, with the fitted saturation
    for c, a in zip(ANGLE_COLORS, angles):
        ts = by_angle[a]
        cums = []
        for t in ts:
            run, acc = [], 0.0
            for v in t["marginal_mg"]:
                acc += v
                run.append(acc)
            cums.append(run)
        m = [mean([cu[i] for cu in cums]) for i in range(n_taps)]
        ax2.plot(xs, m, color=c, linewidth=2.0, marker="o", markersize=5.5,
                 markeredgecolor=SURFACE, markeredgewidth=1.2,
                 label="{:.0f}° tilt".format(a))
        fit = fit_decay([mean([t["marginal_mg"][i] for t in ts])
                         for i in range(n_taps)])
        yy, acc = [], 0.0
        for i in range(n_taps):
            acc += fit["y_inf"] + fit["A"] * fit["r"] ** i
            yy.append(acc)
        ax2.plot(xs, yy, color=c, linewidth=1.1, linestyle=":", zorder=1)
    style(ax2)
    ax2.set_xticks(xs)
    ax2.set_xlabel("tap index since the priming rotation", color=INK_2)
    ax2.set_ylabel("cumulative mass delivered by taps (mg)", color=INK_2)
    ax2.set_title("Cumulative delivery saturates — a finite lip inventory",
                  color=INK, fontsize=12, loc="left", fontweight="bold")
    leg = ax2.legend(frameon=False, fontsize=9, loc="upper left")
    for txt in leg.get_texts():
        txt.set_color(INK_2)
    ax2.annotate("dotted: fit  yᵢ = y∞ + A·rⁱ⁻¹",
                 (0.98, 0.06), xycoords="axes fraction", ha="right",
                 color=INK_2, fontsize=9)
    fig.suptitle("Single-tap characterization — salt, one auger "
                 "revolution as the lip re-feed (3 replicates per tilt)",
                 color=INK, fontsize=13, fontweight="bold", x=0.005, ha="left")
    fig.tight_layout(rect=(0, 0, 1, 0.95))
    fig.savefig(out, dpi=150, facecolor=SURFACE)
    plt.close(fig)


def plot_model(by_angle, angles, fits, out):
    fig, axes = plt.subplots(1, 3, figsize=(14.5, 4.6), facecolor=SURFACE)
    ax1, ax2, ax3 = axes

    # (1) tap gain vs tilt: first tap, late taps, fitted floor
    first = [mean([t["marginal_mg"][0] for t in by_angle[a]]) for a in angles]
    first_sd = [sd([t["marginal_mg"][0] for t in by_angle[a]]) for a in angles]
    late = [mean([mean(t["marginal_mg"][7:]) for t in by_angle[a]])
            for a in angles]
    ax1.errorbar(angles, first, yerr=first_sd, color=ANGLE_COLORS[3],
                 linewidth=2.0, marker="o", markersize=7,
                 markeredgecolor=SURFACE, markeredgewidth=1.2, capsize=3,
                 label="first tap after re-feed")
    ax1.plot(angles, late, color=ACCENT, linewidth=2.0, marker="s",
             markersize=6, markeredgecolor=SURFACE, markeredgewidth=1.2,
             label="taps 8–10 (depleted lip)")
    style(ax1)
    ax1.set_xlabel("plate tilt (deg)", color=INK_2)
    ax1.set_ylabel("yield per single tap (mg)", color=INK_2)
    ax1.set_title("Tap gain rises ~7× with tilt", color=INK, fontsize=11,
                  loc="left", fontweight="bold")
    leg = ax1.legend(frameon=False, fontsize=9, loc="upper left")
    for txt in leg.get_texts():
        txt.set_color(INK_2)

    # (2) extractable lip inventory + refill per revolution
    m_lip = [fits[a]["m_lip"] for a in angles]
    prime = [mean([t["prime_mg"] for t in by_angle[a]]) for a in angles]
    ax2.plot(angles, prime, color=ANGLE_COLORS[1], linewidth=2.0, marker="o",
             markersize=7, markeredgecolor=SURFACE, markeredgewidth=1.2,
             label="delivered by the priming revolution")
    ax2.plot(angles, m_lip, color=ACCENT, linewidth=2.0, marker="s",
             markersize=6, markeredgecolor=SURFACE, markeredgewidth=1.2,
             label="tap-extractable lip inventory  M_lip = A/(1−r)")
    style(ax2)
    ax2.set_xlabel("plate tilt (deg)", color=INK_2)
    ax2.set_ylabel("mass (mg)", color=INK_2)
    ax2.set_title("Auger refill vs. what taps can reach", color=INK,
                  fontsize=11, loc="left", fontweight="bold")
    leg = ax2.legend(frameon=False, fontsize=8.5, loc="upper left")
    for txt in leg.get_texts():
        txt.set_color(INK_2)

    # (3) depletion ratio r per angle
    rs = [fits[a]["r"] for a in angles]
    bars = ax3.bar([str(int(a)) for a in angles], rs, width=0.55,
                   color=ANGLE_COLORS, edgecolor=SURFACE, linewidth=2.0)
    for b, r in zip(bars, rs):
        ax3.annotate("{:.2f}".format(r),
                     (b.get_x() + b.get_width() / 2, b.get_height()),
                     xytext=(0, 4), textcoords="offset points", ha="center",
                     color=INK_2, fontsize=9.5)
    style(ax3)
    ax3.set_ylim(0, 1.0)
    ax3.set_xlabel("plate tilt (deg)", color=INK_2)
    ax3.set_ylabel("per-tap depletion ratio r", color=INK_2)
    ax3.set_title("Each tap leaves a fraction r behind", color=INK,
                  fontsize=11, loc="left", fontweight="bold")
    fig.tight_layout()
    fig.savefig(out, dpi=150, facecolor=SURFACE)
    plt.close(fig)


def main(argv):
    d = Path(argv[1]) if len(argv) > 1 else Path(
        "data/tap-characterization/2026-07-31_salt")
    log = next(iter(sorted(d.glob("tap_characterize*.log"))))
    meta, pts, raw = parse(log)
    n_ctrl = int(meta.get("n_ctrl", 3))
    n_taps = int(meta.get("n_taps", 10))
    n_post = int(meta.get("n_post", 2))
    trials = build_trials(pts, n_ctrl, n_taps, n_post)

    by_angle = defaultdict(list)
    for t in trials:
        by_angle[t["angle"]].append(t)
    angles = sorted(by_angle)
    fits = {a: fit_decay([mean([t["marginal_mg"][i] for t in by_angle[a]])
                          for i in range(n_taps)]) for a in angles}
    ctrl_mg = mean([t["ctrl_mg_per_interval"] for t in trials])

    with (d / "taps_tidy.csv").open("w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["powder_id", "trial", "angle_plate_deg", "rep",
                    "tap_index", "marginal_mg", "cumulative_mg"])
        for t in trials:
            acc = 0.0
            for i, v in enumerate(t["marginal_mg"], start=1):
                acc += v
                w.writerow([meta.get("powder_id", "?"), t["trial"],
                            t["angle"], t["rep"], i,
                            "{:.1f}".format(v), "{:.1f}".format(acc)])

    with (d / "trials_summary.csv").open("w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["powder_id", "trial", "angle_plate_deg", "rep",
                    "prime_mg_per_rev", "ctrl_mg_per_interval",
                    "post_mg_per_interval", "tap1_mg", "taps8_10_mean_mg",
                    "total_10_taps_mg"])
        for t in trials:
            w.writerow([meta.get("powder_id", "?"), t["trial"], t["angle"],
                        t["rep"], "{:.1f}".format(t["prime_mg"]),
                        "{:.2f}".format(t["ctrl_mg_per_interval"]),
                        "{:.2f}".format(t["post_mg_per_interval"]),
                        "{:.1f}".format(t["marginal_mg"][0]),
                        "{:.2f}".format(mean(t["marginal_mg"][7:])),
                        "{:.1f}".format(t["total_mg"])])

    plot_depletion(by_angle, angles, n_taps, ctrl_mg, d / "tap_depletion.png")
    plot_model(by_angle, angles, fits, d / "tap_model.png")

    print("angle  prime_mg  tap1_mg  taps8-10  total10  A_mg     r     "
          "y_inf   M_lip_mg")
    for a in angles:
        ts = by_angle[a]
        f = fits[a]
        print("{:5.1f}  {:8.1f}  {:7.2f}  {:8.2f}  {:7.1f}  {:6.2f}  {:5.3f} "
              " {:5.2f}  {:8.1f}".format(
                  a, mean([t["prime_mg"] for t in ts]),
                  mean([t["marginal_mg"][0] for t in ts]),
                  mean([mean(t["marginal_mg"][7:]) for t in ts]),
                  mean([t["total_mg"] for t in ts]),
                  f["A"], f["r"], f["y_inf"], f["m_lip"]))
    print("no-tap control drift: {:+.3f} mg/interval "
          "({} raw samples logged)".format(ctrl_mg, len(raw)))


if __name__ == "__main__":
    main(sys.argv)
