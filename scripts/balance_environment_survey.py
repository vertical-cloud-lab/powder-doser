#!/usr/bin/env python3
"""Decide whether the bench environment is quiet enough to run, and for how long.

Why this exists
---------------
The A&D HR-100A in the polishing-lab fume hood is not noisy in the usual
sense.  Between disturbances it sits at 0.02-0.04 mg sample-to-sample
jitter with 93-100 % of frames stable -- better than its own 0.1 mg display
resolution.  What it does instead is

  * drift slowly, of order 5-10 mg/min, and
  * take occasional step offsets of order 100 mg when something mechanical
    happens in the room (a door, a polishing machine, someone at the bench).

Neither shows up as jitter, so the usual "is it stable?" check passes right
up until the data is wrong.  What actually matters is **how long a single
measurement takes**: a 2 s auger revolution is barely touched, a 14 min
closed-loop dose is destroyed.

So this script answers the question the battery actually needs answered:
*given the room right now, what is the worst-case mass error for a
measurement of duration T?*  It reports that per duration and maps it onto
the battery's blocks, so a run is a go/no-go decision rather than a hope.

Usage::

    python scripts/balance_environment_survey.py                 # 10 min survey
    python scripts/balance_environment_survey.py --settle 300    # quicker
    python scripts/balance_environment_survey.py --csv out.csv

Read-only: it sends only the A&D ``Q`` query, so it is safe with a loaded
auger and will not disturb the balance it is measuring.
"""

from __future__ import annotations

import argparse
import csv
import statistics
import sys

# Reuse the device plumbing rather than duplicating the UART framing.
from balance_zero import parse, run_on_device  # noqa: E402

# Durations that matter, and what in the battery takes about that long.
BLOCK_DURATIONS = [
    (5.0, "block C/E: one 360 deg revolution, or one tap, bracketed"),
    (10.0, "block D: three revolutions at 90 RPM"),
    (15.0, "block B: a static hold; block D at 15 RPM"),
    (30.0, "block A baseline sweep"),
    (60.0, "a slow trial, or one dose phase"),
    (180.0, "block G: a short closed-loop dose"),
]

# A trial is only worth recording if the environment contributes less than
# this.  Block G's whole acceptance band is +/-5 mg, so 2 mg is the point
# where the environment stops being a rounding error and starts being the
# measurement.
GOOD_MG = 2.0
USABLE_MG = 5.0


def window_spreads(t: list[float], mg: list[float], dur: float) -> list[float]:
    """Peak-to-peak of every window of length ``dur`` in the record."""
    out = []
    n = len(t)
    j = 0
    for i in range(n):
        while j < n and t[j] - t[i] < dur:
            j += 1
        if j - i < 5 or t[j - 1] - t[i] < dur * 0.8:
            continue
        seg = mg[i:j]
        out.append(max(seg) - min(seg))
    return out


def drift_rate(t: list[float], mg: list[float]) -> float:
    """Least-squares slope in mg/min, robust enough for a go/no-go."""
    if len(t) < 3:
        return 0.0
    mt = statistics.mean(t)
    mm = statistics.mean(mg)
    den = sum((v - mt) ** 2 for v in t)
    if den == 0:
        return 0.0
    return 60.0 * sum((t[i] - mt) * (mg[i] - mm) for i in range(len(t))) / den


def find_steps(t: list[float], mg: list[float], threshold: float = 10.0):
    """Sample-to-sample jumps too large to be powder.

    Nothing is being dispensed during a survey, so any jump at all is an
    artifact.  During a real run the same test still holds during intervals
    where no actuator is commanded: the fastest powder measured conveys
    ~116 mg/s while rotating and essentially nothing while stopped, so a
    >10 mg jump inside one ~0.2 s poll interval is not mass arriving.
    """
    raw = [(t[i + 1], mg[i + 1] - mg[i])
           for i in range(len(t) - 1)
           if abs(mg[i + 1] - mg[i]) > threshold]
    # One knock rings for several poll intervals; count it once, and report
    # the net offset it left behind rather than each sample of the ringing.
    events = []
    for ts, dv in raw:
        if events and ts - events[-1][0] < 2.0:
            events[-1] = (events[-1][0], events[-1][1] + dv)
        else:
            events.append((ts, dv))
    return events


def survey(t: list[float], mg: list[float], status: list[str]) -> int:
    n = len(t)
    jitter = (sum(abs(mg[i + 1] - mg[i]) for i in range(n - 1)) / (n - 1)
              if n > 1 else 0.0)
    stable = sum(1 for s in status if s == "ST")
    print("[survey] {} samples over {:.0f} s, {}/{} stable ({:.0f} %)".format(
        n, t[-1] - t[0], stable, n, 100.0 * stable / n))
    print("[survey] sample-to-sample jitter {:.3f} mg".format(jitter))
    if jitter > 0.30:
        print("[survey]   -> DRAFTS. Breeze break closed? Sash down?")
    else:
        print("[survey]   -> drafts are not the problem "
              "(at or below the 0.1 mg display resolution)")

    steps = find_steps(t, mg)
    # Report drift from the longest step-free stretch: a single 100 mg step
    # otherwise dominates the slope and hides the real creep rate.
    bounds = [0] + [i for i in range(len(t) - 1)
                    if abs(mg[i + 1] - mg[i]) > 10.0] + [len(t) - 1]
    seg = max((( bounds[k], bounds[k + 1]) for k in range(len(bounds) - 1)),
              key=lambda ab: ab[1] - ab[0])
    a, b = seg[0] + 1, seg[1]
    print("[survey] drift {:+.1f} mg/min over the longest quiet stretch "
          "({:.0f} s)".format(drift_rate(t[a:b], mg[a:b]), t[b - 1] - t[a]))

    print("[survey] {} mechanical step event(s) > 10 mg".format(len(steps)))
    for ts, dv in steps[:8]:
        print("[survey]   t={:6.1f} s  {:+.1f} mg".format(ts, dv))
    if steps:
        rate = 60.0 * len(steps) / max(t[-1] - t[0], 1.0)
        print("[survey]   -> {:.1f} shock event(s) per minute. These leave a "
              "permanent zero offset; isolation, not shielding, is the fix."
              .format(rate))

    print()
    print("[survey] worst-case environmental error by measurement duration:")
    print("[survey]   {:>7}  {:>8} {:>8} {:>8}   {}".format(
        "dur", "median", "p90", "worst", "what takes that long"))
    verdict_ok = True
    for dur, what in BLOCK_DURATIONS:
        spreads = window_spreads(t, mg, dur)
        if not spreads:
            continue
        spreads.sort()
        med = spreads[len(spreads) // 2]
        p90 = spreads[int(0.9 * len(spreads))]
        mark = "ok " if p90 <= GOOD_MG else ("marg" if p90 <= USABLE_MG else "BAD")
        if p90 > USABLE_MG and dur <= 30.0:
            verdict_ok = False
        print("[survey]   {:>6.0f}s  {:8.2f} {:8.2f} {:8.2f}  {:4} {}".format(
            dur, med, p90, spreads[-1], mark, what))

    print()
    if verdict_ok:
        print("[survey] VERDICT: short-trial blocks (A-F) are safe to run now.")
    else:
        print("[survey] VERDICT: even short trials are being disturbed. "
              "Wait, or find the source, before running.")
    print("[survey] Block G (multi-minute closed-loop doses against a "
          "+/-5 mg band) is only safe when the 180 s row is inside 5 mg.")
    return 0 if verdict_ok else 1


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--settle", type=float, default=600.0,
                    help="survey length in seconds (default 600)")
    ap.add_argument("--port", default="/dev/ttyACM0")
    ap.add_argument("--csv", help="write the raw samples here")
    ap.add_argument("--from-csv", help="analyse an existing capture instead "
                                       "of touching the rig")
    args = ap.parse_args(argv)

    if args.from_csv:
        with open(args.from_csv) as fh:
            rows = list(csv.DictReader(fh))
        t = [float(r["t_s"]) for r in rows]
        mg = [float(r["mg"]) for r in rows]
        status = [r["status"] for r in rows]
    else:
        stdout = run_on_device(False, int(args.settle * 1000), args.port)
        _before, samples = parse(stdout)
        if not samples:
            print("[survey] no samples -- is the balance switched on?")
            return 2
        t = [s[0] for s in samples]
        status = [s[1] for s in samples]
        mg = [s[2] for s in samples]
        if args.csv:
            with open(args.csv, "w", newline="") as fh:
                w = csv.writer(fh)
                w.writerow(["t_s", "status", "mg"])
                for i in range(len(t)):
                    w.writerow(["{:.3f}".format(t[i]), status[i], mg[i]])
            print("[survey] wrote {}".format(args.csv))

    return survey(t, mg, status)


if __name__ == "__main__":
    sys.exit(main())
