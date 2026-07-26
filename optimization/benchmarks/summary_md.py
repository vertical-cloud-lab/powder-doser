#!/usr/bin/env python3
"""Write results/summary.md (markdown tables) from results/results.jsonl."""
from __future__ import annotations

import json
import statistics
from pathlib import Path

HERE = Path(__file__).parent
RES = HERE / "results"

ORDER = ["three_phase", "three_phase_vel", "rate_pi_kf", "dual_ukf", "mpc",
         "bo_three_phase"]


def agg(rows):
    errs = sorted(r["error_mg"] for r in rows)
    p95 = errs[min(len(errs) - 1, int(0.95 * len(errs)))]
    return {
        "n": len(rows),
        "med_err": statistics.median(errs),
        "p95_err": p95,
        "tol_pct": 100 * sum(r["within_tol"] for r in rows) / len(rows),
        "over_pct": 100 * sum(r["overshoot"] for r in rows) / len(rows),
        "med_t": statistics.median(r["time_s"] for r in rows),
        "med_taps": statistics.median(r["taps"] for r in rows),
        "fail": sum(not r["status"].startswith("ok") for r in rows),
    }


def table(rows, keyfn, keys, title):
    out = [f"### {title}", "",
           "| group | method | n | med \\|e\\| mg | p95 \\|e\\| mg | ±5 mg % | overshoot % | med t (s) | med taps | not-ok |",
           "|---|---|---|---|---|---|---|---|---|---|"]
    for key in keys:
        for m in ORDER:
            sub = [r for r in rows if r["method"] == m and keyfn(r) == key]
            if not sub:
                continue
            a = agg(sub)
            out.append(
                f"| {key} | {m} | {a['n']} | {a['med_err']:.2f} | "
                f"{a['p95_err']:.1f} | {a['tol_pct']:.0f} | {a['over_pct']:.0f} | "
                f"{a['med_t']:.0f} | {a['med_taps']:.0f} | {a['fail']} |")
    return "\n".join(out) + "\n"


def main():
    rows = [json.loads(l) for l in (RES / "results.jsonl").open()]
    parts = ["# Benchmark summary\n",
             f"{len(rows)} doses. Grid: powders {sorted({r['powder'] for r in rows})}, "
             f"contexts {sorted({r['context_name'] for r in rows})}, "
             f"targets {sorted({r['target_g'] for r in rows})} g, "
             f"{len({r['seed'] for r in rows})} seeds/cell. Tolerance ±5 mg; "
             "overshoot = true mass > target (strict). All numbers are true "
             "post-settle vial mass; controllers saw only the simulated "
             "balance.\n\n"
             "**Descriptive only** (methods-check review): pooled medians mix "
             "powders/contexts/targets and include timeout-censored 300 s "
             "doses, so they must not be used to rank methods - see "
             "`paired_stats.md` for cell-level paired differences with "
             "seed-cluster bootstrap CIs. `time_s` ends at controller "
             "declaration and excludes the 1 s scoring settle; `not-ok` "
             "counts controller status (timeout/stall/error/overshoot-abort), "
             "which is distinct from being outside tolerance. p95 is the "
             "0.95 order statistic of the pooled sample.\n"]
    parts.append(table(rows, lambda r: "all", ["all"], "Pooled"))
    parts.append(table(rows, lambda r: r["powder"],
                       sorted({r["powder"] for r in rows}), "By powder"))
    parts.append(table(rows, lambda r: r["context_name"],
                       sorted({r["context_name"] for r in rows}), "By context"))
    parts.append(table(rows, lambda r: r["target_g"],
                       sorted({r["target_g"] for r in rows}), "By target (g)"))
    (RES / "summary.md").write_text("\n".join(parts))
    print(f"wrote {RES / 'summary.md'}")


if __name__ == "__main__":
    main()
