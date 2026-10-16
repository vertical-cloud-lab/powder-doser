"""Figures for the trim study (issue #153).

Run ``python run_study.py all`` first, then ``python plots.py``.  Reads the
JSONL outcome dumps in ``results/`` so the figures always match the tables.
"""
from __future__ import annotations

import json
import math
from collections import defaultdict
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from estimators import compound_poisson_exceedance  # noqa: E402
from trim_sim import POWDERS  # noqa: E402

RESULTS = Path(__file__).parent / "results"

# Colour-blind-safe categorical palette, dark enough to read on white.
C = {"margin_only": "#6E6E6E", "rate_pi": "#D55E00", "rate_pid": "#CC79A7",
     "fixed_increment": "#0072B2", "chance_increment": "#009E73",
     "chance_tap": "#000000"}
LABEL = {"margin_only": "no trim (guard band only)",
         "rate_pi": "rate-PI (deployed)", "rate_pid": "rate-PID",
         "fixed_increment": "fixed 45° increments",
         "chance_increment": "chance-constrained increments",
         "chance_tap": "chance-constrained + tap"}


def _load(tag):
    path = RESULTS / f"outcomes_{tag}.jsonl"
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text().splitlines() if line]


def _style(ax, title, xlabel, ylabel):
    ax.set_title(title, fontsize=11, loc="left", pad=8)
    ax.set_xlabel(xlabel, fontsize=9)
    ax.set_ylabel(ylabel, fontsize=9)
    ax.tick_params(labelsize=8)
    ax.grid(alpha=0.25, linewidth=0.6)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)


def fig_error_distribution():
    """Signed error by method, with the one-sided structure made visible."""
    rows = _load("main")
    if not rows:
        return
    by = defaultdict(list)
    for r in rows:
        by[r["method"]].append(r["signed_error_mg"])
    order = [m for m in LABEL if m in by]

    fig, ax = plt.subplots(figsize=(9, 4.2))
    ax.axvspan(-5, 0, color="#009E73", alpha=0.10, zorder=0)
    ax.axvline(0.0, color="#B22222", lw=1.4, zorder=3)
    for i, m in enumerate(order):
        xs = [min(max(x, -220.0), 120.0) for x in by[m]]
        ax.scatter(xs, [i + (hash((m, j)) % 100 - 50) / 420.0
                        for j in range(len(xs))],
                   s=3, alpha=0.25, color=C[m], edgecolors="none", zorder=2)
        med = sorted(by[m])[len(by[m]) // 2]
        ax.plot([med], [i], marker="|", ms=18, mew=2.5, color=C[m], zorder=4)
    ax.set_yticks(range(len(order)))
    ax.set_yticklabels([LABEL[m] for m in order], fontsize=9)
    ax.set_xlim(-225, 125)
    _style(ax, "Signed dose error by trim method — green band is the acceptable "
               "[-5, 0] mg window,\nanything right of the red line is a scrapped "
               "dose", "signed error (mg)", "")
    fig.tight_layout()
    fig.savefig(RESULTS / "fig_error_distribution.png", dpi=150)
    plt.close(fig)


def fig_pareto():
    """Overshoot risk against accuracy, as alpha is swept."""
    rows = _load("alpha")
    main = _load("main")
    if not rows:
        return
    by = defaultdict(list)
    for r in rows:
        by[r["method"]].append(r)
    pts = []
    for name, rs in by.items():
        alpha = float(name.split("@")[1])
        e = sorted(r["signed_error_mg"] for r in rs)
        pts.append((alpha, sum(1 for x in e if x > 0) / len(e),
                    abs(e[len(e) // 2])))
    pts.sort()

    fig, ax = plt.subplots(figsize=(6.6, 4.4))
    ax.plot([100 * p[1] for p in pts], [p[2] for p in pts], "-o",
            color="#000000", ms=5, lw=1.6, label="chance-constrained trim")
    for a, po, med in pts:
        ax.annotate(f"α={a:g}", (100 * po, med), fontsize=7.5,
                    xytext=(4, 4), textcoords="offset points")
    if main:
        for m in ("rate_pi", "rate_pid"):
            e = sorted(r["signed_error_mg"] for r in main if r["method"] == m)
            if e:
                ax.plot([100 * sum(1 for x in e if x > 0) / len(e)],
                        [abs(e[len(e) // 2])], "D", ms=7, color=C[m],
                        label=LABEL[m])
    ax.legend(fontsize=8, frameon=False)
    _style(ax, "Overshoot risk buys accuracy — but only one of these\n"
               "controllers lets you choose the exchange rate",
           "P(overshoot) %", "|median error| (mg)")
    fig.tight_layout()
    fig.savefig(RESULTS / "fig_pareto.png", dpi=150)
    plt.close(fig)


def fig_tau_sensitivity():
    """Overshoot rate against the true balance time constant."""
    rows = _load("tau")
    if not rows:
        return
    by = defaultdict(lambda: defaultdict(list))
    for r in rows:
        by[r["method"]][r["tau_bal_plant_s"]].append(r["signed_error_mg"])

    fig, ax = plt.subplots(figsize=(6.6, 4.2))
    for m, d in by.items():
        taus = sorted(d)
        ax.plot(taus, [100 * sum(1 for x in d[t] if x > 0) / len(d[t])
                       for t in taus],
                "-o", ms=5, lw=1.8, color=C.get(m, "#444"), label=LABEL.get(m, m))
    ax.axvline(0.70, color="#888", ls="--", lw=1.0)
    ax.annotate("controller's belief", (0.70, ax.get_ylim()[1] * 0.95),
                fontsize=7.5, ha="right", color="#666")
    ax.legend(fontsize=8, frameon=False)
    _style(ax, "Rate feedback degrades when the balance model is wrong;\n"
               "measuring at rest does not care",
           "true plant balance time constant τ_bal (s)", "P(overshoot) %")
    fig.tight_layout()
    fig.savefig(RESULTS / "fig_tau_sensitivity.png", dpi=150)
    plt.close(fig)


def fig_regime():
    """Why a rate lookahead cannot work at trim flow."""
    T = 0.30
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4.0))

    rpms = [x for x in range(2, 60, 1)]
    for name, p in POWDERS.items():
        mean, sd = [], []
        for rpm in rpms:
            q = rpm / 60.0 * p.feed_factor_g_per_rev
            lam = q / p.mean_slug_g
            mean.append(1000 * lam * T * p.mean_slug_g)
            sd.append(1000 * math.sqrt(lam * T * (p.mean_slug_g ** 2)
                                       * (1 + p.slug_cv ** 2)))
        ax1.plot(rpms, mean, lw=1.8, label=f"{name}: correction applied")
        ax1.plot(rpms, sd, lw=1.4, ls="--",
                 color=ax1.lines[-1].get_color(), label=f"{name}: its own scatter")
    ax1.axhline(5.0, color="#B22222", lw=1.2)
    ax1.annotate("±5 mg tolerance", (55, 5.6), fontsize=7.5, ha="right",
                 color="#B22222")
    ax1.axvline(18.0, color="#888", ls=":", lw=1.0)
    ax1.annotate("deployed cutoff\n(18 rpm)", (18.5, 40), fontsize=7.5,
                 color="#666")
    ax1.legend(fontsize=7, frameon=False, ncol=1)
    _style(ax1, "The 0.30 s rate lookahead vs its own shot noise",
           "auger rpm during trim", "mass over the lookahead (mg)")

    budgets = [1.0 * i for i in range(1, 121)]
    for mu, lab in ((6.4e-3, "today's quantum (6.4 mg)"),
                    (1.6e-3, "1.6 mg quantum"),
                    (0.8e-3, "0.8 mg quantum")):
        ax2.plot(budgets, [100 * compound_poisson_exceedance(0.5, mu, 2.48,
                                                             b / 1000.0)
                           for b in budgets], lw=1.8, label=lab)
    for a in (5.0, 2.0):
        ax2.axhline(a, color="#888", ls="--", lw=0.9)
        ax2.annotate(f"α = {a:g}%", (118, a + 0.4), fontsize=7.5, ha="right",
                     color="#666")
    ax2.axvline(5.0, color="#B22222", lw=1.2)
    ax2.annotate("±5 mg", (6, 28), fontsize=7.5, color="#B22222")
    ax2.set_ylim(0, 32)
    ax2.legend(fontsize=8, frameon=False)
    _style(ax2, "One slug can blow the budget",
           "remaining budget (mg)", "P(one slug > budget) %")

    fig.tight_layout()
    fig.savefig(RESULTS / "fig_regime.png", dpi=150)
    plt.close(fig)


def main():
    RESULTS.mkdir(exist_ok=True)
    fig_regime()
    fig_error_distribution()
    fig_pareto()
    fig_tau_sensitivity()
    print("figures written to", RESULTS)


if __name__ == "__main__":
    main()
