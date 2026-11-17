"""Monte Carlo comparison of trim-dispensing methods (issue #153).

Usage::

    python run_study.py main       # the headline comparison
    python run_study.py tau        # plant/filter balance-lag mismatch sweep
    python run_study.py cv         # slug-dispersion sensitivity
    python run_study.py regime     # is the trim regime a continuum? (no sim)
    python run_study.py alpha      # the risk / accuracy Pareto
    python run_study.py quantum    # required terminal quantum (no sim)
    python run_study.py all

Results land in ``results/`` as JSON plus a markdown summary.  Every method is
run on identical (powder, seed, target) cells so all comparisons are paired.
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

from metrics import Outcome, mcnemar, paired_diff, summarize
from trim_methods import METHODS
from trim_sim import POWDERS, make_rig

RESULTS = Path(__file__).parent / "results"

# 120 seeds x 3 powders x 2 deficits = 720 doses per method.  The Edison review
# was explicit that 15 seeds cannot resolve a 10-point difference in overshoot
# rate and that "hundreds per cell may be needed for a hard safety claim".
N_SEEDS = 120
DEFICITS_G = (0.30, 0.10)
TAU_PLANT_DEFAULT = 0.7

METHOD_ORDER = ["margin_only", "rate_pi", "rate_pid", "fixed_increment",
                "chance_increment", "chance_tap"]


def run_cell(method: str, powder: str, seed: int, deficit_g: float,
             tau_plant: float = TAU_PLANT_DEFAULT,
             tau_belief: float | None = None,
             slug_cv: float | None = None) -> Outcome:
    rig, plant, target_g = make_rig(
        powder, seed, tau_bal_plant_s=tau_plant, tau_bal_belief_s=tau_belief,
        slug_cv=slug_cv, start_deficit_g=deficit_g)
    t0 = rig.t
    try:
        status = METHODS[method](rig, target_g)
    except Exception as exc:                       # a controller bug is a result
        status = "error:{}".format(type(exc).__name__)
    elapsed = rig.t - t0
    delivered = plant.settled_mass_g()
    return Outcome(
        method=method, powder=powder, seed=seed, target_g=target_g,
        tau_bal_plant_s=tau_plant,
        tau_bal_belief_s=rig.tau_bal_belief_s,
        slug_cv=(slug_cv if slug_cv is not None
                 else POWDERS[powder].slug_cv),
        start_deficit_g=deficit_g,
        delivered_g=delivered,
        signed_error_mg=(delivered - target_g) * 1000.0,
        time_s=elapsed, taps=rig.taps, auger_rev=rig.auger_rev,
        settle_waits=rig.settle_waits, status=status)


def sweep(methods, powders, seeds, deficits, **kw) -> list[Outcome]:
    out = []
    total = len(methods) * len(powders) * len(seeds) * len(deficits)
    done = 0
    for m in methods:
        for p in powders:
            for d in deficits:
                for s in seeds:
                    out.append(run_cell(m, p, s, d, **kw))
                    done += 1
            print(f"  {m:18s} {p:10s} {done}/{total}", flush=True)
    return out


def _fmt(v, nd=1):
    if isinstance(v, float):
        return f"{v:.{nd}f}"
    return str(v)


def scorecard_table(rows: dict[str, dict]) -> str:
    """Markdown table of the one-sided scorecard, one row per method."""
    cols = [("p_over", "P(E>0)", "pct"), ("p_over_5", "P(E>+5mg)", "pct"),
            ("p_under_5", "P(E<-5mg)", "pct"), ("epe_mg", "E[max(E,0)]", "mg"),
            ("yield_band", "P(-5..0 mg)", "pct"), ("median_mg", "median E", "mg"),
            ("p95_mg", "p95 E", "mg"), ("max_pos_mg", "max +excess", "mg"),
            ("median_time_s", "median t", "s"),
            ("p_short", "stopped short", "pct"),
            ("p_incomplete", "stall/timeout", "pct")]
    head = "| method | n | " + " | ".join(c[1] for c in cols) + " |"
    sep = "|---|---:|" + "---:|" * len(cols)
    lines = [head, sep]
    for name, s in rows.items():
        cells = []
        for key, _, unit in cols:
            v = s.get(key, float("nan"))
            cells.append(f"{100*v:.1f}%" if unit == "pct" else _fmt(v, 1))
        lines.append(f"| `{name}` | {s['n']} | " + " | ".join(cells) + " |")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# study 1: headline comparison
# ---------------------------------------------------------------------------

def study_main() -> str:
    seeds = list(range(N_SEEDS))
    powders = list(POWDERS)
    print("[main] running", len(METHOD_ORDER), "methods")
    outs = sweep(METHOD_ORDER, powders, seeds, DEFICITS_G)
    _dump(outs, "main")

    by_method = {m: [o for o in outs if o.method == m] for m in METHOD_ORDER}
    rows = {m: summarize(v) for m, v in by_method.items()}

    md = ["## Headline comparison",
          "",
          f"{N_SEEDS} seeds x {len(powders)} powders x {len(DEFICITS_G)} handover "
          f"deficits = {N_SEEDS*len(powders)*len(DEFICITS_G)} doses per method. "
          f"Plant balance time constant {TAU_PLANT_DEFAULT} s, controller belief "
          f"matched (the favourable case for the rate methods).",
          "",
          scorecard_table(rows), ""]

    # Paired comparisons against the deployed controller.
    md += ["### Paired against `rate_pi` (the deployed trickle)", "",
           "| method | ΔP(E>0) [95% CI] | ΔE[max(E,0)] mg [95% CI] | "
           "McNemar p | Δ median time s |", "|---|---|---|---:|---:|"]
    base = by_method["rate_pi"]
    for m in METHOD_ORDER:
        if m == "rate_pi":
            continue
        d_over = paired_diff(by_method[m], base, "p_over")
        d_epe = paired_diff(by_method[m], base, "epe_mg")
        mc = mcnemar(by_method[m], base)
        dt = rows[m]["median_time_s"] - rows["rate_pi"]["median_time_s"]
        md.append(
            f"| `{m}` | {100*d_over['diff']:+.1f}% "
            f"[{100*d_over['ci'][0]:+.1f}, {100*d_over['ci'][1]:+.1f}] "
            f"| {d_epe['diff']:+.2f} [{d_epe['ci'][0]:+.2f}, {d_epe['ci'][1]:+.2f}] "
            f"| {mc['p']:.1e} | {dt:+.1f} |")
    md.append("")

    # Per-powder breakdown of the two headline methods.
    md += ["### Per powder", "",
           "| powder | method | P(E>0) [95% CI] | E[max(E,0)] mg | "
           "P(-5..0 mg) | median t s |", "|---|---|---|---:|---:|---:|"]
    for p in powders:
        for m in ("rate_pi", "rate_pid", "chance_tap"):
            s = summarize([o for o in by_method[m] if o.powder == p])
            md.append(
                f"| {p} | `{m}` | {100*s['p_over']:.1f}% "
                f"[{100*s['p_over_ci'][0]:.1f}, {100*s['p_over_ci'][1]:.1f}] "
                f"| {s['epe_mg']:.2f} | {100*s['yield_band']:.1f}% "
                f"| {s['median_time_s']:.1f} |")
    md.append("")
    return "\n".join(md)


# ---------------------------------------------------------------------------
# study 2: balance-lag mismatch (the Edison sensitivity)
# ---------------------------------------------------------------------------

def study_tau() -> str:
    """Sweep the true plant balance time constant with the belief pinned at 0.7 s.

    The twin used 0.7 s in both plant and filter, which handed the estimator a
    perfectly specified sensor.  Bench drop tests suggest the real HR-100A may
    be ~0.16 s.  At the trim flow rate that mismatch is worth
    (0.70-0.16) x 0.042 = 22.7 mg -- larger than the tolerance and larger than
    the whole rate-lookahead term.  This is the sweep that prices it.
    """
    seeds = list(range(60))
    methods = ["rate_pi", "rate_pid", "chance_tap"]
    taus = [0.16, 0.40, 0.70, 1.00]
    md = ["## Balance-lag mismatch (controller believes tau_bal = 0.70 s)", "",
          "| plant tau_bal s | method | P(E>0) | E[max(E,0)] mg | p95 E mg | "
          "median t s |", "|---:|---|---:|---:|---:|---:|"]
    allouts = []
    for tau in taus:
        print(f"[tau] plant tau_bal = {tau}")
        outs = sweep(methods, list(POWDERS), seeds, (0.30,),
                     tau_plant=tau, tau_belief=0.70)
        allouts += outs
        for m in methods:
            s = summarize([o for o in outs if o.method == m])
            md.append(f"| {tau:.2f} | `{m}` | {100*s['p_over']:.1f}% "
                      f"| {s['epe_mg']:.2f} | {s['p95_mg']:.1f} "
                      f"| {s['median_time_s']:.1f} |")
    _dump(allouts, "tau")
    md.append("")
    return "\n".join(md)


# ---------------------------------------------------------------------------
# study 3: slug dispersion sensitivity
# ---------------------------------------------------------------------------

def study_cv() -> str:
    """Sweep slug dispersion.

    The 15.9 mg slug sd was measured on 45 deg steps on a depleted tube and
    includes reading noise, so the true mark dispersion is somewhat smaller.
    ``slug_cv`` 1.0 / 1.75 / 2.48 spans "much tidier than measured" to "as
    measured".
    """
    seeds = list(range(60))
    methods = ["rate_pi", "chance_tap"]
    cvs = [1.00, 1.75, 2.48, 3.20]
    md = ["## Slug-dispersion sensitivity", "",
          "| slug CV | method | P(E>0) | E[max(E,0)] mg | P(-5..0 mg) | "
          "median t s |", "|---:|---|---:|---:|---:|---:|"]
    allouts = []
    for cv in cvs:
        print(f"[cv] slug_cv = {cv}")
        outs = sweep(methods, list(POWDERS), seeds, (0.30,), slug_cv=cv)
        allouts += outs
        for m in methods:
            s = summarize([o for o in outs if o.method == m])
            md.append(f"| {cv:.2f} | `{m}` | {100*s['p_over']:.1f}% "
                      f"| {s['epe_mg']:.2f} | {100*s['yield_band']:.1f}% "
                      f"| {s['median_time_s']:.1f} |")
    _dump(allouts, "cv")
    md.append("")
    return "\n".join(md)


# ---------------------------------------------------------------------------
# study 4: is the trim regime a continuum?  (arithmetic, no simulation)
# ---------------------------------------------------------------------------

def study_regime() -> str:
    """Marked-point-process diagnostics for the deployed 0.30 s lookahead.

    Reproduces the Edison spot-check calculation from our own powder constants:
    N_T = lambda*T expected events, P(no event) = exp(-lambda*T), and the
    compound-Poisson sd of the mass delivered over the horizon.  A rate-based
    lookahead is only meaningful where that sd is small against the tolerance.
    """
    T = 0.30
    md = ["## Is the trim regime a continuum?", "",
          f"Committed mass over the deployed {T:.2f} s lookahead, as a marked "
          "point process. `E[M]` is the correction the cutoff rule applies; "
          "`sd[M]` is the irreducible physical scatter of what it is correcting "
          "for.", "",
          "| powder | flow g/s | lambda /s | E[N] | P(N=0) | E[M] mg | sd[M] mg "
          "| sd/tol |", "|---|---:|---:|---:|---:|---:|---:|---:|"]
    for name, p in POWDERS.items():
        for rpm in (18.0, 6.0):
            q = rpm / 60.0 * p.feed_factor_g_per_rev
            lam = q / p.mean_slug_g
            ey2 = (p.mean_slug_g ** 2) * (1.0 + p.slug_cv ** 2)
            mean_m = lam * T * p.mean_slug_g
            sd_m = math.sqrt(lam * T * ey2)
            md.append(
                f"| {name} @{rpm:.0f} rpm | {q:.4f} | {lam:.2f} | {lam*T:.2f} "
                f"| {math.exp(-lam*T):.2f} | {1000*mean_m:.1f} "
                f"| {1000*sd_m:.1f} | {sd_m/0.005:.1f}x |")
    md += ["",
           "A continuum approximation is credible only when many independent "
           "events fall inside the horizon and their upper quantile is small "
           "against the allowed error. Here `sd[M]` is several times the ±5 mg "
           "tolerance and larger than `E[M]` itself, and one stop decision in "
           "five to seven sees no event at all.", ""]
    return "\n".join(md)


# ---------------------------------------------------------------------------
# study 5: the risk / accuracy Pareto
# ---------------------------------------------------------------------------

def study_alpha() -> str:
    """Map the per-decision risk alpha onto realised dose-level performance.

    This is the knob the deployed rate-PI does not have.  Its 40-odd percent
    overshoot rate is an emergent property of a margin that was tuned once; here
    the overshoot rate is a specification, and the table is the exchange rate
    between it and accuracy.
    """
    from trim_methods import chance_tap
    seeds = list(range(60))
    alphas = [0.30, 0.20, 0.10, 0.05, 0.02, 0.01]
    md = ["## Risk/accuracy Pareto for the chance-constrained trim", "",
          "| per-decision alpha | P(E>0) [95% CI] | E[max(E,0)] mg | median E mg "
          "| p95 E mg | P(-5..0 mg) | median t s |",
          "|---:|---|---:|---:|---:|---:|---:|"]
    allouts = []
    for a in alphas:
        METHODS["_alpha_probe"] = (
            lambda rig, tgt, _a=a: chance_tap(rig, tgt, alpha=_a))
        print(f"[alpha] {a}")
        outs = sweep(["_alpha_probe"], list(POWDERS), seeds, (0.30,))
        for o in outs:
            o.method = f"chance_tap@{a}"
        allouts += outs
        s = summarize(outs)
        md.append(
            f"| {a:.2f} | {100*s['p_over']:.1f}% "
            f"[{100*s['p_over_ci'][0]:.1f}, {100*s['p_over_ci'][1]:.1f}] "
            f"| {s['epe_mg']:.2f} | {s['median_mg']:+.1f} | {s['p95_mg']:+.1f} "
            f"| {100*s['yield_band']:.1f}% | {s['median_time_s']:.1f} |")
    METHODS.pop("_alpha_probe", None)
    _dump(allouts, "alpha")
    md.append("")
    return "\n".join(md)


# ---------------------------------------------------------------------------
# study 6: what quantum would the hardware need?
# ---------------------------------------------------------------------------

def study_quantum() -> str:
    """Invert the safety rule into a hardware specification.

    No commanded action can promise to deliver less than one slug.  So for a
    one-sided tolerance ``tol`` at per-decision risk ``alpha``, the terminal
    actuator's mean quantum must satisfy ``P(one slug > tol) <= alpha``.  This
    solves that for the mean quantum, which is a bench-measurable, purchasable
    specification rather than a control-law parameter.
    """
    from estimators import compound_poisson_exceedance
    md = ["## Required terminal quantum", "",
          "Largest mean slug mass whose single-slug exceedance stays inside the "
          "risk budget, at the measured dispersion (CV 2.48) and "
          "`trigger_risk = 0.5`. Compare against what the rig delivers today: a "
          "5 deg salt auger command yields mean 2.5 mg / p95 17.7 mg, and a salt "
          "tap yields mean 6.5 mg / p95 21.7 mg.", "",
          "| tolerance | alpha=0.05 | alpha=0.02 | alpha=0.01 |",
          "|---|---:|---:|---:|"]
    for tol_mg in (5.0, 2.0, 1.0):
        row = []
        for a in (0.05, 0.02, 0.01):
            lo, hi = 1e-6, 5e-2
            for _ in range(60):
                mid = 0.5 * (lo + hi)
                if compound_poisson_exceedance(0.5, mid, 2.48,
                                               tol_mg / 1000.0) <= a:
                    lo = mid
                else:
                    hi = mid
            row.append(f"{1000*lo:.2f} mg")
        md.append(f"| ±{tol_mg:.0f} mg | " + " | ".join(row) + " |")
    md += ["",
           "Read the ±5 mg row against today's ~6.5 mg tap quantum: the terminal "
           "actuator is roughly an order of magnitude too coarse. That gap is a "
           "hardware problem, not a tuning problem -- no control law can deliver "
           "a fraction of a slug.", ""]
    return "\n".join(md)


def _dump(outs: list[Outcome], tag: str) -> None:
    RESULTS.mkdir(exist_ok=True)
    with open(RESULTS / f"outcomes_{tag}.jsonl", "w") as fh:
        for o in outs:
            fh.write(json.dumps(o.__dict__) + "\n")


def main(argv: list[str]) -> int:
    what = argv[1] if len(argv) > 1 else "main"
    RESULTS.mkdir(exist_ok=True)
    parts = ["# Trim-method study results",
             "",
             "Generated by `run_study.py`. See `README.md` for the model and "
             "`docs/trim-dispensing.md` for the argument.", ""]
    if what in ("regime", "all"):
        parts.append(study_regime())
    if what in ("main", "all"):
        parts.append(study_main())
    if what in ("tau", "all"):
        parts.append(study_tau())
    if what in ("cv", "all"):
        parts.append(study_cv())
    if what in ("alpha", "all"):
        parts.append(study_alpha())
    if what in ("quantum", "all"):
        parts.append(study_quantum())
    out = "\n".join(parts)
    path = RESULTS / (f"summary_{what}.md" if what != "all" else "summary.md")
    path.write_text(out)
    print(out)
    print(f"\n[written] {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
