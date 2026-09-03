"""One-sided scoring for the trim study (issue #153).

The 2026-08-22 Edison spot-check rejected the scorecard PR #124 was using
("strict overshoot % plus +/-5 mg yield %") on the grounds that *a symmetric
tolerance rate can conceal the hard asymmetry*.  Overshoot scraps the dose;
undershoot costs a few seconds.  Scoring them with one symmetric number hides
the only distinction that matters.

This module implements the replacement it asked for, per powder/target/context:

* ``p_over``      -- P(E > 0), the hard-constraint violation rate
* ``p_over_5``    -- P(E > +5 mg), consequential overshoot
* ``p_under_5``   -- P(E < -5 mg), consequential undershoot
* ``epe``         -- E[max(E, 0)], expected positive excess
* ``yield_band``  -- P(-5 mg <= E <= 0), the genuinely acceptable one-sided band
* ``p95``, ``p99``, ``max_pos`` -- upper excess quantiles
* completion/stall rate, taps, cycle time
* confidence bounds on every safety probability

It also provides the paired inference the review asked for.  Methods are run on
shared seeds, so comparisons are paired: ``paired_diff`` uses a cluster
bootstrap over seeds and ``mcnemar`` handles the overshoot indicator.  This
matters -- the review pointed out that 15 seeds cannot resolve 21 % vs 31 %
(the intervals were 22-41 % and 37-57 %, overlapping), and that "hundreds per
cell may be needed for a hard safety claim".
"""
from __future__ import annotations

import math
import random
from dataclasses import dataclass

__all__ = ["Outcome", "summarize", "wilson", "paired_diff", "mcnemar",
           "METRIC_LABELS"]

MG = 1000.0

METRIC_LABELS = {
    "n": "doses",
    "p_over": "P(E>0)",
    "p_over_5": "P(E>+5mg)",
    "p_under_5": "P(E<-5mg)",
    "epe_mg": "E[max(E,0)] mg",
    "yield_band": "P(-5<=E<=0)",
    "median_mg": "median E mg",
    "p95_mg": "p95 E mg",
    "p99_mg": "p99 E mg",
    "max_pos_mg": "max +excess mg",
    "median_time_s": "median t s",
    "median_taps": "median taps",
    "p_incomplete": "P(stall/timeout)",
    "p_short": "P(stopped short)",
}


@dataclass
class Outcome:
    method: str
    powder: str
    seed: int
    target_g: float
    tau_bal_plant_s: float
    tau_bal_belief_s: float
    slug_cv: float
    start_deficit_g: float
    delivered_g: float
    signed_error_mg: float     # delivered - target, in mg (positive = overshoot)
    time_s: float
    taps: int
    auger_rev: float
    settle_waits: int
    status: str

    @property
    def key(self) -> tuple:
        """Identifies the design cell a dose belongs to (everything but method)."""
        return (self.powder, self.seed, self.target_g, self.tau_bal_plant_s,
                self.tau_bal_belief_s, self.slug_cv, self.start_deficit_g)


def _quantile(sorted_xs: list[float], p: float) -> float:
    if not sorted_xs:
        return float("nan")
    if len(sorted_xs) == 1:
        return sorted_xs[0]
    i = p * (len(sorted_xs) - 1)
    lo = int(math.floor(i))
    hi = min(lo + 1, len(sorted_xs) - 1)
    return sorted_xs[lo] + (i - lo) * (sorted_xs[hi] - sorted_xs[lo])


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """Wilson score interval for a binomial proportion.

    Used rather than the normal approximation because the safety probabilities
    we care about are near 0, where the normal interval is badly wrong (and can
    dip below zero).
    """
    if n == 0:
        return (float("nan"), float("nan"))
    p = k / n
    d = 1.0 + z * z / n
    c = p + z * z / (2 * n)
    h = z * math.sqrt(max(0.0, p * (1 - p) / n + z * z / (4 * n * n)))
    return ((c - h) / d, (c + h) / d)


def summarize(outcomes: list[Outcome]) -> dict:
    """One-sided scorecard for a list of doses."""
    n = len(outcomes)
    if n == 0:
        return {"n": 0}
    e = sorted(o.signed_error_mg for o in outcomes)
    pos = [x for x in e if x > 0.0]
    k_over = len(pos)
    k_over5 = sum(1 for x in e if x > 5.0)
    k_under5 = sum(1 for x in e if x < -5.0)
    k_band = sum(1 for x in e if -5.0 <= x <= 0.0)
    # "short" means the controller correctly ran out of safe actions; only
    # stalls, timeouts and errors are failures.
    k_bad = sum(1 for o in outcomes if o.status not in ("ok", "short"))
    times = sorted(o.time_s for o in outcomes)
    taps = sorted(o.taps for o in outcomes)
    lo_over, hi_over = wilson(k_over, n)
    lo_b, hi_b = wilson(k_band, n)
    return {
        "n": n,
        "p_over": k_over / n,
        "p_over_ci": (lo_over, hi_over),
        "p_over_5": k_over5 / n,
        "p_under_5": k_under5 / n,
        "epe_mg": sum(pos) / n,                  # expected positive excess
        "yield_band": k_band / n,
        "yield_band_ci": (lo_b, hi_b),
        "median_mg": _quantile(e, 0.50),
        "p95_mg": _quantile(e, 0.95),
        "p99_mg": _quantile(e, 0.99),
        "max_pos_mg": max(pos) if pos else 0.0,
        "median_time_s": _quantile(times, 0.50),
        "median_taps": _quantile([float(t) for t in taps], 0.50),
        "p_incomplete": k_bad / n,
        "p_short": sum(1 for o in outcomes if o.status == "short") / n,
    }


def paired_diff(a: list[Outcome], b: list[Outcome], stat: str,
                n_boot: int = 4000, seed: int = 0) -> dict:
    """Paired cluster bootstrap of ``stat(a) - stat(b)`` over shared design cells.

    Methods are run on identical seeds and powders, so the correct comparison
    resamples *cells*, not individual doses.  ``stat`` is one of the scalar keys
    ``summarize`` returns.
    """
    by_key_a = {o.key: o for o in a}
    by_key_b = {o.key: o for o in b}
    keys = sorted(set(by_key_a) & set(by_key_b))
    if not keys:
        return {"n_pairs": 0}
    pa = [by_key_a[k] for k in keys]
    pb = [by_key_b[k] for k in keys]
    point = summarize(pa)[stat] - summarize(pb)[stat]
    rng = random.Random(seed)
    draws = []
    m = len(keys)
    for _ in range(n_boot):
        idx = [rng.randrange(m) for _ in range(m)]
        draws.append(summarize([pa[i] for i in idx])[stat]
                     - summarize([pb[i] for i in idx])[stat])
    draws.sort()
    return {
        "n_pairs": m,
        "diff": point,
        "ci": (_quantile(draws, 0.025), _quantile(draws, 0.975)),
    }


def mcnemar(a: list[Outcome], b: list[Outcome],
            predicate=lambda o: o.signed_error_mg > 0.0) -> dict:
    """Exact McNemar test on a paired binary outcome (default: strict overshoot).

    Reports the discordant counts and a two-sided exact binomial p-value.  This
    is the right test for "does method A overshoot less often than method B" on
    shared seeds, and it is what the review asked for in place of comparing two
    independent proportions.
    """
    by_key_a = {o.key: o for o in a}
    by_key_b = {o.key: o for o in b}
    keys = sorted(set(by_key_a) & set(by_key_b))
    b01 = sum(1 for k in keys
              if not predicate(by_key_a[k]) and predicate(by_key_b[k]))
    b10 = sum(1 for k in keys
              if predicate(by_key_a[k]) and not predicate(by_key_b[k]))
    nd = b01 + b10
    if nd == 0:
        return {"n_pairs": len(keys), "a_only": 0, "b_only": 0, "p": 1.0}
    # two-sided exact binomial against p = 0.5
    k = min(b01, b10)
    tail = sum(math.comb(nd, i) for i in range(k + 1)) / (2.0 ** nd)
    return {
        "n_pairs": len(keys),
        "a_only": b10,          # A overshot, B did not
        "b_only": b01,          # B overshot, A did not
        "p": min(1.0, 2.0 * tail),
    }
