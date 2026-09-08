#!/usr/bin/env python3
"""Wait for the balance to settle: measured go/no-go with a predicted ready time.

Why this exists (issue #157)
----------------------------
After any disturbance -- someone at the hood, the sash, the lights, the
door -- the HR-100A's reading drifts, and the drift decays exponentially
(tau ~= 21 min, measured overnight on 2026-09-07 in EB B125; see
``docs/issue-157-drift/``).  The safe-but-wasteful rule is "wait an hour
before long measurements", which charges every run the worst case and,
as issue #157 puts it, more than doubles operating time.

This tool replaces the fixed wait with a measurement.  It takes a short
read-only sample (default 90 s of A&D ``Q`` polls), extracts the current
drift rate, fits the decay across successive samples, and answers the
only question that matters: *is the environment good enough for the
measurement I am about to make, and if not, when will it be?*

By default it **blocks until ready**, so the settling window costs no
operator time at all::

    python scripts/balance_readiness.py --profile block-g \\
        && <start the run>

Usage::

    python scripts/balance_readiness.py --once          # one sample, verdict, ETA
    python scripts/balance_readiness.py                 # block until block-g is safe
    python scripts/balance_readiness.py --profile short --once
    python scripts/balance_readiness.py --duration 300 --budget 5   # custom
    python scripts/balance_readiness.py --from-csv seg1.csv@230 seg2.csv@558

Runs on the CI runner (over Tailscale SSH via the ``RPI_*`` env vars,
like ``balance_zero.py``) or on the Pi itself with ``--local``.

Read-only: it only ever sends the A&D ``Q`` query, so it is safe with a
loaded auger and will not disturb the balance it is measuring.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import os
import shlex
import statistics
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timedelta, timezone

# Reuse the device plumbing and the survey's analysis primitives.
import balance_zero  # noqa: E402
from balance_environment_survey import drift_rate, find_steps  # noqa: E402

# What a measurement needs from the environment.  The budget is what the
# environment may contribute over one measurement of that duration; 5 mg
# is block G's whole acceptance band, so it is the ceiling everywhere.
# The gate on drift is then budget / duration, in mg/min.
PROFILES = {
    # name: (duration_s, budget_mg, what takes that long)
    "short":   (10.0, 5.0, "blocks A-F: bracketed trials of 10 s or less"),
    "block-h": (17.0, 5.0, "block H: one 17 s bracketed micro-dose"),
    "dose-60": (60.0, 5.0, "a slow trial, or one dose phase"),
    "block-g": (180.0, 5.0, "block G: multi-minute closed-loop dose, +/-5 mg band"),
}

# Measured on 2026-09-07 (issue #157): drift rate relaxed with tau ~= 21
# min after an evening of occupancy.  Used for the ETA until enough live
# samples exist to fit tau from the decay actually in progress.
DEFAULT_TAU_MIN = 21.0
TAU_BOUNDS_MIN = (5.0, 90.0)

# Below this the rate is equilibrium wobble, not a decaying transient;
# such samples prove readiness but carry no information about tau.
RATE_FLOOR_MG_MIN = 0.5

# The survey's draft threshold: jitter above this means air is moving.
JITTER_LIMIT_MG = 0.30

MIN_SAMPLES = 20


def quiet_rate(t: list[float], mg: list[float]) -> float:
    """Drift rate (mg/min) over the longest step-free stretch.

    Same policy as the survey: a single knock otherwise dominates the
    slope and hides the creep rate that actually predicts settling.
    """
    bounds = [0] + [i for i in range(len(t) - 1)
                    if abs(mg[i + 1] - mg[i]) > 10.0] + [len(t) - 1]
    a, b = max(((bounds[k], bounds[k + 1]) for k in range(len(bounds) - 1)),
               key=lambda ab: ab[1] - ab[0])
    a += 1
    return drift_rate(t[a:b], mg[a:b])


def analyze(t: list[float], mg: list[float], status: list[str]) -> dict:
    """One sample -> the numbers the gate decides on."""
    n = len(t)
    jitter = (sum(abs(mg[i + 1] - mg[i]) for i in range(n - 1)) / (n - 1)
              if n > 1 else 0.0)
    return {
        "n": n,
        "span_s": t[-1] - t[0] if n > 1 else 0.0,
        "rate_mg_min": quiet_rate(t, mg),
        "jitter_mg": jitter,
        "steps": find_steps(t, mg),
        "stable_pct": 100.0 * sum(1 for s in status if s == "ST") / n if n else 0.0,
        "last_mg": mg[-1] if mg else None,
    }


def fit_tau_min(history: list[tuple[float, float]]) -> float | None:
    """Fit the decay time constant from (t_s, |rate|) samples.

    Straight line through ln|rate| vs t, using only rates above the
    noise floor.  Returns minutes, or None when there are not yet two
    usable points or the rates are not decaying.
    """
    pts = [(t, abs(r)) for t, r in history if abs(r) > RATE_FLOOR_MG_MIN]
    pts = pts[-6:]
    if len(pts) < 2 or pts[-1][1] >= pts[0][1]:
        return None
    ts = [p[0] for p in pts]
    ys = [math.log(p[1]) for p in pts]
    mt = statistics.mean(ts)
    my = statistics.mean(ys)
    den = sum((v - mt) ** 2 for v in ts)
    if den == 0:
        return None
    slope = sum((ts[i] - mt) * (ys[i] - my) for i in range(len(ts))) / den
    if slope >= 0:
        return None
    tau = -1.0 / slope / 60.0
    return min(max(tau, TAU_BOUNDS_MIN[0]), TAU_BOUNDS_MIN[1])


def eta_min(rate_mg_min: float, limit_mg_min: float, tau_min: float) -> float:
    """Minutes until an exponentially decaying |rate| crosses the limit."""
    r = abs(rate_mg_min)
    if r <= limit_mg_min:
        return 0.0
    return tau_min * math.log(r / limit_mg_min)


def limit_for(duration_s: float, budget_mg: float) -> float:
    return budget_mg / (duration_s / 60.0)


def verdict(sample: dict, duration_s: float, budget_mg: float) -> tuple[bool, str]:
    """(ready, reason).  Ready means one clean sample inside every gate."""
    if sample["n"] < MIN_SAMPLES:
        return False, "too few samples (balance off, or mid-calibration?)"
    if sample["steps"]:
        return False, "mechanical shock during the sample"
    if sample["jitter_mg"] > JITTER_LIMIT_MG:
        return False, "drafts (jitter {:.2f} mg)".format(sample["jitter_mg"])
    if abs(sample["rate_mg_min"]) > limit_for(duration_s, budget_mg):
        return False, "drift {:+.1f} mg/min".format(sample["rate_mg_min"])
    return True, "ok"


def acquire_live(sample_s: float, port: str, local: bool) -> str:
    if not local:
        return balance_zero.run_on_device(False, int(sample_s * 1000), port)
    # Same snippet, run through mpremote on this host (i.e. on the Pi).
    script = ("DO_ZERO = False\nSETTLE_MS = {}\n".format(int(sample_s * 1000))
              + balance_zero.DEVICE_SNIPPET)
    fd, path = tempfile.mkstemp(suffix=".py")
    try:
        with os.fdopen(fd, "w") as fh:
            fh.write(script)
        cmd = ("source {} 2>/dev/null; mpremote connect {} run {}"
               .format(balance_zero.PI_VENV, shlex.quote(port), shlex.quote(path)))
        proc = subprocess.run(["bash", "-c", cmd], text=True,
                              capture_output=True, timeout=sample_s + 120)
    finally:
        os.unlink(path)
    blob = (proc.stdout or "") + (proc.stderr or "")
    if "may be in use by another program" in blob:
        sys.exit("{} is busy -- another process is driving the Pico. "
                 "Wait for it rather than forcing the port.".format(port))
    if proc.returncode != 0:
        sys.exit("mpremote failed ({}): {}".format(
            proc.returncode, proc.stderr.strip()[-400:]))
    return proc.stdout


def read_csv(path: str) -> tuple[list[float], list[float], list[str]]:
    with open(path) as fh:
        rows = list(csv.DictReader(fh))
    t = [float(r["t_s"]) for r in rows]
    mg = [float(r["mg"]) for r in rows]
    status = [r["status"] for r in rows]
    return t, mg, status


def local_clock(dt_utc: datetime) -> str:
    """Ready-time in lab-local clock too, when the tz database allows."""
    try:
        from zoneinfo import ZoneInfo
        local = dt_utc.astimezone(ZoneInfo("America/Denver"))
        return "{} UTC ({} lab time)".format(
            dt_utc.strftime("%H:%M"), local.strftime("%H:%M"))
    except Exception:
        return dt_utc.strftime("%H:%M UTC")


def report_profiles(sample: dict, tau: tuple[float, str], chosen: str,
                    profiles: dict) -> None:
    print("[gate] readiness by measurement profile "
          "(tau {:.0f} min{}):".format(tau[0], tau[1]))
    for name, (dur, budget, what) in profiles.items():
        lim = limit_for(dur, budget)
        ready, why = verdict(sample, dur, budget)
        if ready:
            state = "GO  now"
        else:
            wait = eta_min(sample["rate_mg_min"], lim, tau[0])
            state = "WAIT {:3.0f} min".format(wait) if wait else "WAIT (" + why + ")"
        mark = " <-- --profile " + name if name == chosen else ""
        print("[gate]   {:8} limit {:5.1f} mg/min  {}  {}{}".format(
            name, lim, state, what, mark))


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--profile", default="block-g", choices=sorted(PROFILES),
                    help="measurement to gate on (default block-g, the "
                         "strictest in routine use)")
    ap.add_argument("--duration", type=float,
                    help="gate a custom measurement of this many seconds "
                         "instead of a named profile")
    ap.add_argument("--budget", type=float, default=5.0,
                    help="allowed environmental error for --duration, mg "
                         "(default 5)")
    ap.add_argument("--once", action="store_true",
                    help="one sample and a verdict; do not wait "
                         "(--confirm is ignored)")
    ap.add_argument("--confirm", type=int, default=1,
                    help="consecutive ready samples required before opening "
                         "(default 1; use 2 for unattended runs -- one clean "
                         "90 s window during active occupancy proves little)")
    ap.add_argument("--sample", type=float, default=90.0,
                    help="seconds per sample (default 90)")
    ap.add_argument("--interval", type=float, default=240.0,
                    help="seconds between sample starts while waiting "
                         "(default 240)")
    ap.add_argument("--max-wait", type=float, default=5400.0,
                    help="give up after this many seconds (default 5400)")
    ap.add_argument("--port", default="/dev/ttyACM0")
    ap.add_argument("--local", action="store_true",
                    help="drive mpremote on this host (run on the Pi) "
                         "instead of SSHing over Tailscale")
    ap.add_argument("--from-csv", nargs="+", metavar="PATH[@OFFSET_S]",
                    help="replay recorded captures instead of touching the "
                         "rig; offsets are seconds from the first sample")
    ap.add_argument("--csv-dir", help="save each live sample here as "
                                      "sample_<n>.csv")
    ap.add_argument("--json", help="write the latest state here after "
                                   "every sample (for orchestration)")
    ap.add_argument("--tau", type=float,
                    help="assume this decay constant in minutes instead of "
                         "the measured default ({:.0f})".format(DEFAULT_TAU_MIN))
    args = ap.parse_args(argv)

    profiles = dict(PROFILES)
    if args.duration:
        profiles["custom"] = (args.duration, args.budget,
                              "custom measurement from the command line")
        chosen = "custom"
    else:
        chosen = args.profile
    dur, budget, _ = profiles[chosen]
    lim = limit_for(dur, budget)

    replay = None
    if args.from_csv:
        replay = []
        for spec in args.from_csv:
            path, _, off = spec.partition("@")
            replay.append((path, float(off) if off else 0.0))

    if args.csv_dir:
        os.makedirs(args.csv_dir, exist_ok=True)

    history: list[tuple[float, float]] = []   # (t_s since start, rate)
    t_start = time.time()
    # Stamp saved samples per invocation, so gating twice in one day
    # never silently overwrites the first run's record.
    run_id = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    i = 0
    streak = 0
    while True:
        if replay is not None:
            if i >= len(replay):
                print("[gate] replay exhausted without reaching the "
                      "{} limit".format(chosen))
                return 1
            path, off = replay[i]
            t, mg, status = read_csv(path)
            now_s = off + (t[-1] - t[0]) / 2.0
            label = os.path.basename(path)
        else:
            t0 = time.time()
            stdout = acquire_live(args.sample, args.port, args.local)
            _before, _cmds, samples = balance_zero.parse(stdout)
            if not samples:
                print("[gate] no samples -- is the balance switched on?")
                return 2
            t = [s[0] for s in samples]
            status = [s[1] for s in samples]
            mg = [s[2] for s in samples]
            if args.csv_dir:
                out = os.path.join(args.csv_dir,
                                   "sample_{}_{}.csv".format(run_id, i))
                with open(out, "w", newline="") as fh:
                    w = csv.writer(fh)
                    w.writerow(["t_s", "status", "mg"])
                    for k in range(len(t)):
                        w.writerow(["{:.3f}".format(t[k]), status[k], mg[k]])
            now_s = (t0 - t_start) + (t[-1] - t[0]) / 2.0
            label = "sample {}".format(i)

        s = analyze(t, mg, status)
        if s["steps"]:
            # A shock is a fresh disturbance: the old decay no longer
            # describes the environment, so the clock starts again.
            print("[gate] {}: {} shock event(s) -- new disturbance, "
                  "restarting the settling clock".format(label, len(s["steps"])))
            history.clear()
        history.append((now_s, s["rate_mg_min"]))

        fitted = fit_tau_min(history)
        tau = ((args.tau, ", forced") if args.tau else
               (fitted, ", fitted live") if fitted else
               (DEFAULT_TAU_MIN, ", issue-157 default"))
        ready, why = verdict(s, dur, budget)
        streak = streak + 1 if ready else 0
        need = 1 if args.once else max(1, args.confirm)
        wait = eta_min(s["rate_mg_min"], lim, tau[0])

        print("[gate] {}: {} pts/{:.0f} s  drift {:+.2f} mg/min  "
              "jitter {:.3f} mg  {:.0f}% stable".format(
                  label, s["n"], s["span_s"], s["rate_mg_min"],
                  s["jitter_mg"], s["stable_pct"]))
        report_profiles(s, tau, chosen, profiles)

        if args.json:
            state = {
                "generated_utc": datetime.now(timezone.utc).isoformat(),
                "profile": chosen,
                "ready": ready,
                "reason": why,
                "rate_mg_min": round(s["rate_mg_min"], 3),
                "jitter_mg": round(s["jitter_mg"], 4),
                "step_events": len(s["steps"]),
                "tau_min": round(tau[0], 1),
                "tau_source": tau[1].strip(", "),
                "eta_min": round(wait, 1),
                "confirmed": streak >= need,
                "ready_streak": streak,
                "history": [{"t_s": round(a, 1), "rate_mg_min": round(b, 2)}
                            for a, b in history],
            }
            tmp = args.json + ".tmp"
            with open(tmp, "w") as fh:
                json.dump(state, fh, indent=1)
            os.replace(tmp, args.json)

        if ready and streak >= need:
            print("[gate] READY for {} ({}{}).".format(
                chosen, why,
                ", {} consecutive clean samples".format(streak)
                if need > 1 else ""))
            return 0
        if ready:
            print("[gate] clean sample {}/{} -- confirming before "
                  "opening".format(streak, need))
        elif wait:
            ready_at = datetime.now(timezone.utc) + timedelta(minutes=wait)
            print("[gate] not yet: {}; predicted ready ~{} min from now "
                  "(at {})".format(why, int(round(wait)),
                                   local_clock(ready_at)))
        else:
            print("[gate] not yet: {}".format(why))

        i += 1
        if replay is not None:
            continue
        if args.once:
            return 1
        elapsed = time.time() - t_start
        if elapsed + args.interval > args.max_wait:
            print("[gate] gave up after {:.0f} min (max-wait). Something "
                  "keeps disturbing the balance -- check occupancy, HVAC, "
                  "or lower --max-wait expectations.".format(elapsed / 60))
            return 1
        # Sleep the remainder of the interval; sampling is read-only and
        # cheap, but each sample is an SSH round-trip, and the decay
        # moves on ~20 min timescales, so ~4 min spacing is plenty.
        time.sleep(max(0.0, args.interval - (time.time() - t0)))


if __name__ == "__main__":
    sys.exit(main())
