#!/usr/bin/env python3
"""Paired uncertainty analysis for results/results.jsonl (methods-check D).

Pooled medians are kept in summary.md for description only; ranking claims
should come from here.  For each controller pair this script reports, per
metric:

* the equal-cell-weight study-level paired difference: within each of the 12
  (powder, context, target) design cells, the mean over seeds of the
  per-seed paired difference; then the unweighted mean over cells;
* a 95% percentile CI from a SEED-CLUSTER bootstrap: seed labels are
  resampled with replacement and every cell/method row belonging to a
  sampled seed moves together (the same seed is reused across cells, so rows
  are not independent);
* for binary outcomes (within tolerance, strict overshoot): the paired risk
  difference with the same bootstrap, plus pooled discordant counts;
* the per-cell mean |error| differences, so interactions pooled tables hide
  stay visible.

Dose time is right-censored at the 300 s rig timeout; censoring rates are
reported separately and time differences treat a censored dose as 300 s
(conservative for "which is faster" only when censoring is comparable -
check the censoring table before reading the time row).

Usage: python paired_stats.py [--out results/paired_stats.md]
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

HERE = Path(__file__).parent
RES = HERE / "results"

BASELINE = "three_phase"
ORDER = ["three_phase", "three_phase_vel", "rate_pi_kf", "dual_ukf", "mpc",
         "bo_three_phase", "bangbang_ff", "bangbang_safe", "bangbang_trim"]
#: pairs reported: everything vs the firmware baseline + the feedback trio, plus
#: the bang-bang hybrid vs the best feedback methods (the speed/overshoot front)
EXTRA_PAIRS = [("rate_pi_kf", "dual_ukf"), ("rate_pi_kf", "mpc"),
               ("dual_ukf", "mpc"), ("bangbang_trim", "dual_ukf"),
               ("bangbang_trim", "rate_pi_kf")]
N_BOOT = 4000
TIMEOUT_S = 300.0

METRICS = {
    "|error| (mg)": lambda r: r["error_mg"],
    "time (s, cens. 300)": lambda r: min(r["time_s"], TIMEOUT_S),
    "taps": lambda r: float(r["taps"]),
    "within ±5 mg": lambda r: float(r["within_tol"]),
    "overshoot (strict)": lambda r: float(r["overshoot"]),
}
BINARY = {"within ±5 mg", "overshoot (strict)"}


def load(path: Path):
    rows = [json.loads(l) for l in path.open()]
    by = {}
    for r in rows:
        by[(r["method"], r["powder"], r["context_name"], r["target_g"],
            r["seed"])] = r
    cells = sorted({(r["powder"], r["context_name"], r["target_g"])
                    for r in rows})
    seeds = sorted({r["seed"] for r in rows})
    methods = [m for m in ORDER if any(r["method"] == m for r in rows)]
    return by, cells, seeds, methods


def diff_matrix(by, cells, seeds, a: str, b: str, fn):
    """d[i, j] = metric(a) - metric(b) for cell i, seed j (NaN if missing)."""
    d = np.full((len(cells), len(seeds)), np.nan)
    for i, (p, c, t) in enumerate(cells):
        for j, s in enumerate(seeds):
            ra, rb = by.get((a, p, c, t, s)), by.get((b, p, c, t, s))
            if ra is not None and rb is not None:
                d[i, j] = fn(ra) - fn(rb)
    return d


def study_estimate(d: np.ndarray) -> float:
    """Equal cell weight: mean over cells of the per-cell mean over seeds."""
    return float(np.nanmean(np.nanmean(d, axis=1)))


def cluster_boot_ci(d: np.ndarray, rng) -> tuple[float, float]:
    n_seeds = d.shape[1]
    stats = []
    for _ in range(N_BOOT):
        take = rng.integers(0, n_seeds, size=n_seeds)
        stats.append(study_estimate(d[:, take]))
    return tuple(np.percentile(stats, [2.5, 97.5]))


def discordant(by, cells, seeds, a, b, fn) -> tuple[int, int]:
    n10 = n01 = 0
    for (p, c, t) in cells:
        for s in seeds:
            ra, rb = by.get((a, p, c, t, s)), by.get((b, p, c, t, s))
            if ra is None or rb is None:
                continue
            va, vb = fn(ra), fn(rb)
            n10 += int(va > vb)   # a=1, b=0
            n01 += int(va < vb)
    return n10, n01


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--results", default=str(RES / "results.jsonl"))
    ap.add_argument("--out", default=str(RES / "paired_stats.md"))
    args = ap.parse_args()

    by, cells, seeds, methods = load(Path(args.results))
    rng = np.random.default_rng(0)
    pairs = [(m, BASELINE) for m in methods if m != BASELINE]
    pairs += [p for p in EXTRA_PAIRS
              if p[0] in methods and p[1] in methods]

    out = ["# Paired analysis (seed-cluster bootstrap)\n",
           f"{len(cells)} design cells x {len(seeds)} seed clusters; "
           f"{N_BOOT} bootstrap resamples of whole seed clusters "
           "(all cells and methods for a sampled seed move together). "
           "Estimand: equal-weight mean over cells of the per-cell mean "
           "paired difference. A CI excluding 0 indicates a difference "
           "robust to seed-level noise; with "
           f"{len(seeds)} clusters these intervals are still coarse.\n"]

    # censoring / failure-mode table first: time rows are conditional on it
    out.append("### Failure modes (rates over all doses per method)\n")
    out.append("| method | timeout % | stalled % | error % | "
               "overshoot_abort % |")
    out.append("|---|---|---|---|---|")
    all_rows = [r for r in by.values()]
    for m in methods:
        rs = [r for r in all_rows if r["method"] == m]
        n = len(rs)

        def pct(pred):
            return 100.0 * sum(pred(r) for r in rs) / n

        out.append(
            f"| {m} | {pct(lambda r: r['status'] == 'timeout'):.0f} | "
            f"{pct(lambda r: r['status'] == 'stalled'):.0f} | "
            f"{pct(lambda r: r['status'].startswith('error')):.0f} | "
            f"{pct(lambda r: r['status'] == 'overshoot_abort'):.0f} |")
    out.append("")

    for a, b in pairs:
        out.append(f"### {a} − {b}\n")
        out.append("| metric | diff (a−b) | 95% CI | discordant (a>b / a<b) |")
        out.append("|---|---|---|---|")
        for name, fn in METRICS.items():
            d = diff_matrix(by, cells, seeds, a, b, fn)
            est = study_estimate(d)
            lo, hi = cluster_boot_ci(d, rng)
            disc = ""
            if name in BINARY:
                n10, n01 = discordant(by, cells, seeds, a, b, fn)
                disc = f"{n10} / {n01}"
            star = " **\\***" if (lo > 0 or hi < 0) else ""
            out.append(f"| {name} | {est:+.2f}{star} | "
                       f"[{lo:+.2f}, {hi:+.2f}] | {disc} |")
        out.append("")
        # per-cell |error| mean differences (interactions)
        d = diff_matrix(by, cells, seeds, a, b, METRICS["|error| (mg)"])
        out.append("<details><summary>per-cell mean Δ|error| (mg)</summary>\n")
        out.append("| powder | context | target g | Δ|e| mg |")
        out.append("|---|---|---|---|")
        for i, (p, c, t) in enumerate(cells):
            out.append(f"| {p} | {c} | {t} | {np.nanmean(d[i]):+.2f} |")
        out.append("\n</details>\n")

    out.append("\\* = 95% cluster-bootstrap CI excludes zero.\n")
    Path(args.out).write_text("\n".join(out))
    print(f"wrote {args.out} ({len(pairs)} pairs)")


if __name__ == "__main__":
    main()
