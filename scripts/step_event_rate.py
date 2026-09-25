#!/usr/bin/env python3
"""Compare mechanical step-event rates between balance-mounting configurations.

Why this exists
---------------
``balance_environment_survey.py`` answers "is the room quiet enough to run
*right now*".  This answers a different question: **did changing the mounting
actually reduce the ~100 mg step events, or did the room just have a quiet
afternoon?**

Those are not the same question, and the difference is not a detail.  The
events arrive at roughly 1 per 10 min, so a single 600 s survey run expects
*one* event.  Comparing one run against another is comparing 1 count to 1
count: even a real 5x improvement is invisible, and pure chance routinely
produces 0-vs-3.  The default 10 min survey cannot resolve this no matter how
carefully it is run, so a slab that does nothing and a slab that works look
identical.  Hours of exposure per configuration are required -- see
``power_note()`` for the arithmetic.

What it does
------------
Pools every capture belonging to a configuration ("arm"), counts step events
with the same rule the survey uses (>10 mg inside one poll interval, ringing
inside 2 s coalesced into one event, reported as the net offset left behind),
and compares arms with the **exact conditional Poisson test** -- the binomial
test on the split of the pooled count, which is valid at the small counts this
experiment actually produces.  Normal approximations are not.

Usage::

    # one directory per arm, each holding the hourly CSVs from --csv
    python scripts/step_event_rate.py runs/A0-bare-deck runs/A-granite \\
                                      runs/C-granite-mat runs/B-granite-pads

    python scripts/step_event_rate.py --ref runs/A-granite runs/*/   # pick baseline
    python scripts/step_event_rate.py --power                        # just the sizing table

The first directory is the reference arm unless ``--ref`` says otherwise.
Read-only: it touches captured CSVs, never the rig.
"""

from __future__ import annotations

import argparse
import csv
import math
import os
import sys

# Matches balance_environment_survey.find_steps(): nothing is being dispensed
# during a survey, so a jump this large inside one ~0.2 s poll is an artifact.
STEP_MG = 10.0
COALESCE_S = 2.0

# The measured pre-slab baseline, used only to size runs in power_note().
BASELINE_PER_HOUR = 6.0


# --------------------------------------------------------------------- events

def find_steps(t: list[float], mg: list[float], threshold: float = STEP_MG):
    """Sample-to-sample jumps too large to be powder, ringing coalesced.

    Deliberately identical to the survey's detector so the two tools cannot
    disagree about what an event is.
    """
    raw = [(t[i + 1], mg[i + 1] - mg[i])
           for i in range(len(t) - 1)
           if abs(mg[i + 1] - mg[i]) > threshold]
    events = []
    for ts, dv in raw:
        if events and ts - events[-1][0] < COALESCE_S:
            events[-1] = (events[-1][0], events[-1][1] + dv)
        else:
            events.append((ts, dv))
    return events


def read_capture(path: str):
    """Return (exposure_s, [net offsets mg]) for one survey CSV."""
    with open(path) as fh:
        rows = list(csv.DictReader(fh))
    if len(rows) < 2:
        return 0.0, []
    t = [float(r["t_s"]) for r in rows]
    mg = [float(r["mg"]) for r in rows]
    return t[-1] - t[0], [dv for _ts, dv in find_steps(t, mg)]


def load_arm(path: str):
    """Pool every CSV under a directory (or a single CSV file) into one arm."""
    if os.path.isfile(path):
        files = [path]
    else:
        files = sorted(os.path.join(path, f) for f in os.listdir(path)
                       if f.lower().endswith(".csv"))
    exposure, offsets, used = 0.0, [], 0
    for f in files:
        dur, offs = read_capture(f)
        if dur <= 0:
            continue
        exposure += dur
        offsets.extend(offs)
        used += 1
    return {"name": os.path.basename(path.rstrip("/")) or path,
            "path": path, "files": used,
            "exposure_h": exposure / 3600.0, "offsets": offsets,
            "n": len(offsets)}


# ------------------------------------------------------- exact Poisson compare

def _binom_cdf(k: int, n: int, p: float) -> float:
    """P(X <= k) for X ~ Binom(n, p). Exact finite sum; n here is tiny."""
    if k < 0:
        return 0.0
    if k >= n:
        return 1.0
    return sum(math.comb(n, i) * p ** i * (1 - p) ** (n - i)
               for i in range(k + 1))


def _binom_sf(k: int, n: int, p: float) -> float:
    """P(X >= k)."""
    return 1.0 - _binom_cdf(k - 1, n, p)


def _bisect(f, lo: float, hi: float, target: float, rising: bool) -> float:
    """Solve f(p) = target on [lo, hi] for a monotone f."""
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        v = f(mid)
        if (v < target) == rising:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


def compare(a: dict, b: dict, alpha: float = 0.05):
    """Exact conditional test of rate_a vs rate_b, plus a rate-ratio CI.

    Conditioning on the total count n = x_a + x_b removes the nuisance
    parameter: x_a ~ Binom(n, p) with p = lam_a*T_a / (lam_a*T_a + lam_b*T_b),
    so H0: lam_a = lam_b becomes H0: p = T_a/(T_a+T_b) -- an exact binomial
    test, valid at n = 3 where a normal approximation is not.
    """
    xa, xb = a["n"], b["n"]
    Ta, Tb = a["exposure_h"], b["exposure_h"]
    n = xa + xb
    out = {"x_a": xa, "x_b": xb, "T_a": Ta, "T_b": Tb}
    if Ta <= 0 or Tb <= 0:
        out["note"] = "zero exposure"
        return out
    out["rate_a"] = xa / Ta
    out["rate_b"] = xb / Tb
    out["rate_ratio"] = (xa / Ta) / (xb / Tb) if xb else float("inf")
    if n == 0:
        out["p_value"] = 1.0
        out["note"] = "no events in either arm"
        return out

    p0 = Ta / (Ta + Tb)
    # Two-sided exact binomial p-value, summing all outcomes no more likely
    # than the observed one (the standard "method of small p-values").
    obs = math.comb(n, xa) * p0 ** xa * (1 - p0) ** (n - xa)
    tol = obs * (1 + 1e-9)
    out["p_value"] = min(1.0, sum(
        math.comb(n, i) * p0 ** i * (1 - p0) ** (n - i)
        for i in range(n + 1)
        if math.comb(n, i) * p0 ** i * (1 - p0) ** (n - i) <= tol))

    # Clopper-Pearson interval on p, mapped to the rate ratio.
    pl = 0.0 if xa == 0 else _bisect(
        lambda p: _binom_sf(xa, n, p), 0.0, 1.0, alpha / 2, rising=True)
    pu = 1.0 if xa == n else _bisect(
        lambda p: _binom_cdf(xa, n, p), 0.0, 1.0, alpha / 2, rising=False)
    scale = Tb / Ta
    out["rr_lo"] = (pl / (1 - pl)) * scale if pl < 1 else float("inf")
    out["rr_hi"] = (pu / (1 - pu)) * scale if pu < 1 else float("inf")
    return out


# ------------------------------------------------------------------ run sizing

def _z(p: float) -> float:
    """Inverse standard normal CDF (Acklam), good to ~1e-9 over the range used."""
    a = [-3.969683028665376e+01, 2.209460984245205e+02, -2.759285104469687e+02,
         1.383577518672690e+02, -3.066479806614716e+01, 2.506628277459239e+00]
    b = [-5.447609879822406e+01, 1.615858368580409e+02, -1.556989798598866e+02,
         6.680131188771972e+01, -1.328068155288572e+01]
    c = [-7.784894002430293e-03, -3.223964580411365e-01, -2.400758277161838e+00,
         -2.549732539343734e+00, 4.374664141464968e+00, 2.938163982698783e+00]
    d = [7.784695709041462e-03, 3.224671290700398e-01, 2.445134137142996e+00,
         3.754408661907416e+00]
    lo = 0.02425
    if p < lo:
        q = math.sqrt(-2 * math.log(p))
        return ((((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q
                 + c[5]) / ((((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1))
    if p > 1 - lo:
        q = math.sqrt(-2 * math.log(1 - p))
        return -((((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q
                  + c[5]) / ((((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1))
    q, r = p - 0.5, (p - 0.5) ** 2
    return ((((((a[0] * r + a[1]) * r + a[2]) * r + a[3]) * r + a[4]) * r + a[5])
            * q / (((((b[0] * r + b[1]) * r + b[2]) * r + b[3]) * r + b[4]) * r + 1))


def power_note(baseline_per_hour: float = BASELINE_PER_HOUR,
               alpha: float = 0.05, power: float = 0.80) -> None:
    """How many hours per arm, for a given effect size, at 80 % power."""
    rhs = (_z(1 - alpha / 2) + _z(power)) * math.sqrt(0.5)
    print("Run sizing at baseline {:.1f} events/h, alpha={:.2f}, power={:.0%}"
          .format(baseline_per_hour, alpha, power))
    print("  {:<22} {:>10} {:>11} {:>13}".format(
        "to detect", "events/arm", "hours/arm", "4 arms (days)"))
    for label, ratio in [("1.5x reduction", 1 / 1.5), ("2x reduction", 0.5),
                         ("3x reduction", 1 / 3), ("4x reduction", 0.25),
                         ("10x reduction", 0.1)]:
        m0 = (rhs / (1 - math.sqrt(ratio))) ** 2
        hrs = m0 / baseline_per_hour
        print("  {:<22} {:>10.0f} {:>11.1f} {:>13.1f}".format(
            label, m0, hrs, 4 * hrs / 24))
    print()
    print("  Seeing *zero* events is stronger evidence than the table implies:")
    for hrs in (1, 2, 4, 8, 24):
        ub = 3.0 / hrs                      # rule of three, 95 % upper bound
        print("    0 events in {:>2} h  ->  rate < {:.2f}/h (95 %), i.e. rules out "
              "anything worse than a {:.0f}x reduction".format(
                  hrs, ub, baseline_per_hour / ub))
    print()
    print("  A single default 600 s survey expects {:.1f} event(s). One run per "
          "arm cannot decide this.".format(baseline_per_hour / 6))


# ---------------------------------------------------------------------- report

def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("arms", nargs="*",
                    help="one directory (or CSV) per configuration")
    ap.add_argument("--ref", help="reference arm; default is the first given")
    ap.add_argument("--alpha", type=float, default=0.05)
    ap.add_argument("--power", action="store_true",
                    help="print the run-sizing table and exit")
    args = ap.parse_args(argv)

    if args.power or not args.arms:
        power_note(alpha=args.alpha)
        return 0

    arms = [load_arm(p) for p in args.arms]
    ref = next((a for a in arms if a["path"].rstrip("/") == (args.ref or "").rstrip("/")),
               arms[0])

    print("{:<22} {:>6} {:>9} {:>7} {:>10} {:>12} {:>12}".format(
        "arm", "files", "hours", "events", "per hour", "median |mg|", "worst |mg|"))
    print("-" * 84)
    for a in arms:
        mags = sorted(abs(v) for v in a["offsets"])
        med = mags[len(mags) // 2] if mags else 0.0
        worst = mags[-1] if mags else 0.0
        print("{:<22} {:>6} {:>9.2f} {:>7} {:>10.2f} {:>12.1f} {:>12.1f}".format(
            a["name"][:22], a["files"], a["exposure_h"], a["n"],
            a["n"] / a["exposure_h"] if a["exposure_h"] else float("nan"),
            med, worst))

    thin = [a["name"] for a in arms if a["exposure_h"] < 2.0]
    if thin:
        print("\n  WARNING: under 2 h of exposure in {} -- too thin to conclude "
              "anything. Run --power.".format(", ".join(thin)))

    print("\nExact conditional Poisson comparison against '{}':".format(ref["name"]))
    print("  {:<22} {:>11} {:>26} {:>9}".format(
        "arm", "rate ratio", "95 % CI on rate ratio", "p"))
    print("  " + "-" * 72)
    for a in arms:
        if a is ref:
            continue
        c = compare(a, ref, alpha=args.alpha)
        if "p_value" not in c:
            print("  {:<22} {}".format(a["name"][:22], c.get("note", "n/a")))
            continue
        rr = c.get("rate_ratio", float("nan"))
        lo, hi = c.get("rr_lo", float("nan")), c.get("rr_hi", float("nan"))
        print("  {:<22} {:>11.2f} {:>26} {:>9.3f}{}".format(
            a["name"][:22], rr,
            "[{:.2f}, {}]".format(lo, "inf" if hi == float("inf") else "{:.2f}".format(hi)),
            c["p_value"], "  *" if c["p_value"] < args.alpha else ""))
    print("\n  Rate ratio < 1 means fewer events than the reference. A CI that "
          "spans 1.0 means\n  this experiment did not separate the two "
          "configurations -- collect more hours.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
