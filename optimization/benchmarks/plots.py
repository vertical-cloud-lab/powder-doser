#!/usr/bin/env python3
"""Benchmark result figures (static PNG, matplotlib).

Reads results/results.jsonl (benchmark.py output) and writes:
  results/fig_error_dist.png     - |error| distributions by method x powder
  results/fig_pareto.png         - dose time vs |error| trade-off per method
  results/fig_rates.png          - within-tolerance and overshoot rates
"""
from __future__ import annotations

import json
import statistics
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

HERE = Path(__file__).parent
RES = HERE / "results"

SURFACE = "#fcfcfb"
TEXT = "#0b0b0b"
TEXT2 = "#52514e"
GRID = "#e4e3df"
# validated categorical palette (dataviz reference instance), fixed order
METHOD_ORDER = ["three_phase", "three_phase_vel", "rate_pi_kf",
                "dual_ukf", "mpc", "bo_three_phase",
                "bangbang_ff", "bangbang_safe", "bangbang_trim"]
METHOD_LABEL = {"three_phase": "3-phase (firmware)",
                "three_phase_vel": "3-phase velocity",
                "rate_pi_kf": "rate-PI + KF",
                "dual_ukf": "dual UKF",
                "mpc": "MPC (cvxpy)",
                "bo_three_phase": "BO-tuned 3-phase",
                "bangbang_ff": "bang-bang (FF)",
                "bangbang_safe": "bang-bang (safe)",
                "bangbang_trim": "bang-bang + trim"}
COLOR = {"three_phase": "#2a78d6", "three_phase_vel": "#eb6834",
         "rate_pi_kf": "#1baf7a", "dual_ukf": "#eda100",
         "mpc": "#e87ba4", "bo_three_phase": "#008300",
         "bangbang_ff": "#8a8683", "bangbang_safe": "#6c4bd6",
         "bangbang_trim": "#c1121f"}
POWDER_MARK = {"salt": "o", "lactose": "s", "AlSi10Mg": "^"}


def load():
    rows = [json.loads(l) for l in (RES / "results.jsonl").open()]
    return [r for r in rows if r["method"] in METHOD_ORDER]


def style_ax(ax):
    ax.set_facecolor(SURFACE)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(GRID)
    ax.tick_params(colors=TEXT2, labelsize=8)
    ax.yaxis.grid(True, color=GRID, linewidth=0.6)
    ax.set_axisbelow(True)


def fig_error_dist(rows):
    powders = sorted({r["powder"] for r in rows})
    methods = [m for m in METHOD_ORDER if any(r["method"] == m for r in rows)]
    fig, axes = plt.subplots(1, len(powders), figsize=(3.4 * len(powders), 4.2),
                             sharey=True, facecolor=SURFACE)
    rng = np.random.default_rng(0)
    for ax, powder in zip(np.atleast_1d(axes), powders):
        style_ax(ax)
        for i, m in enumerate(methods):
            errs = [max(r["error_mg"], 0.05) for r in rows
                    if r["powder"] == powder and r["method"] == m]
            if not errs:
                continue
            x = i + rng.uniform(-0.16, 0.16, len(errs))
            ax.scatter(x, errs, s=14, color=COLOR[m], alpha=0.65,
                       edgecolors=SURFACE, linewidths=0.5, zorder=3)
            med = statistics.median(errs)
            ax.hlines(med, i - 0.28, i + 0.28, color=COLOR[m], linewidth=2,
                      zorder=4)
        ax.axhline(5.0, color=TEXT2, linewidth=0.8, linestyle=(0, (4, 3)))
        ax.text(len(methods) - 0.4, 5.0, " ±5 mg tol", color=TEXT2,
                fontsize=7, va="bottom", ha="right")
        ax.set_yscale("log")
        ax.set_xticks(range(len(methods)))
        ax.set_xticklabels([METHOD_LABEL[m].replace(" ", "\n", 1)
                            for m in methods], fontsize=7, color=TEXT)
        ax.set_title(powder, fontsize=10, color=TEXT)
    np.atleast_1d(axes)[0].set_ylabel("|mass error| after settle (mg, log)",
                                      fontsize=9, color=TEXT)
    fig.suptitle("Dose error by method and powder "
                 "(all contexts, targets, seeds; bar = median)",
                 fontsize=11, color=TEXT)
    fig.tight_layout(rect=(0, 0, 1, 0.95))
    fig.savefig(RES / "fig_error_dist.png", dpi=160, facecolor=SURFACE)
    plt.close(fig)


def fig_pareto(rows):
    fig, ax = plt.subplots(figsize=(6.4, 4.6), facecolor=SURFACE)
    style_ax(ax)
    ax.xaxis.grid(True, color=GRID, linewidth=0.6)
    for m in METHOD_ORDER:
        for powder, mark in POWDER_MARK.items():
            sub = [r for r in rows if r["method"] == m and r["powder"] == powder]
            if not sub:
                continue
            t = statistics.median(r["time_s"] for r in sub)
            e = max(statistics.median(r["error_mg"] for r in sub), 0.05)
            ax.scatter(t, e, s=52, marker=mark, color=COLOR[m],
                       edgecolors=SURFACE, linewidths=0.8, zorder=3)
    ax.set_yscale("log")
    ax.axhline(5.0, color=TEXT2, linewidth=0.8, linestyle=(0, (4, 3)))
    ax.text(ax.get_xlim()[1], 5.0, "±5 mg tol ", color=TEXT2, fontsize=7,
            va="bottom", ha="right")
    ax.set_xlabel("median dose time (s)", fontsize=9, color=TEXT)
    ax.set_ylabel("median |mass error| (mg, log)", fontsize=9, color=TEXT)
    ax.set_title("Accuracy vs speed (point = method x powder; "
                 "marker shape = powder)", fontsize=10, color=TEXT)
    handles = [plt.Line2D([], [], marker="o", ls="", color=COLOR[m],
                          label=METHOD_LABEL[m])
               for m in METHOD_ORDER if any(r["method"] == m for r in rows)]
    handles += [plt.Line2D([], [], marker=mk, ls="", color=TEXT2, label=p)
                for p, mk in POWDER_MARK.items()]
    ax.legend(handles=handles, fontsize=7, frameon=False, ncol=2,
              labelcolor=TEXT)
    fig.tight_layout()
    fig.savefig(RES / "fig_pareto.png", dpi=160, facecolor=SURFACE)
    plt.close(fig)


def fig_rates(rows):
    methods = [m for m in METHOD_ORDER if any(r["method"] == m for r in rows)]
    fig, axes = plt.subplots(1, 3, figsize=(10.5, 3.6), facecolor=SURFACE)
    specs = [("within ±5 mg (%)", lambda rs: 100 * sum(r["within_tol"] for r in rs) / len(rs)),
             ("overshoot m > target (%)", lambda rs: 100 * sum(r["overshoot"] for r in rs) / len(rs)),
             ("median taps per dose", lambda rs: statistics.median(r["taps"] for r in rs))]
    for ax, (title, fn) in zip(axes, specs):
        style_ax(ax)
        ax.yaxis.grid(False)
        ax.xaxis.grid(True, color=GRID, linewidth=0.6)
        vals = [fn([r for r in rows if r["method"] == m]) for m in methods]
        y = np.arange(len(methods))[::-1]
        ax.barh(y, vals, height=0.55, color=[COLOR[m] for m in methods],
                zorder=3)
        for yi, v in zip(y, vals):
            ax.text(v, yi, f" {v:.0f}", va="center", fontsize=8, color=TEXT)
        ax.set_yticks(y)
        ax.set_yticklabels([METHOD_LABEL[m] for m in methods], fontsize=8,
                           color=TEXT)
        ax.set_title(title, fontsize=9, color=TEXT)
    fig.suptitle("Constraint satisfaction and wear (all cells pooled)",
                 fontsize=11, color=TEXT)
    fig.tight_layout(rect=(0, 0, 1, 0.93))
    fig.savefig(RES / "fig_rates.png", dpi=160, facecolor=SURFACE)
    plt.close(fig)


def main():
    rows = load()
    fig_error_dist(rows)
    fig_pareto(rows)
    fig_rates(rows)
    print(f"wrote 3 figures from {len(rows)} doses -> {RES}")


if __name__ == "__main__":
    main()
