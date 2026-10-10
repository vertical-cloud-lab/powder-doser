"""Summarise finished DEM cases into dosing metrics.

For each case directory (written by run_case.py) this computes:

* ``mg_per_rev``: steady discharge per auger revolution, from the mean
  rate after the first quarter turn (start-up transient excluded);
* ``rate_mg_s``: the same as a rate;
* windowed dose statistics: mass delivered per rotation increment of
  5, 15, 45 and 90 deg (mean, sd, CV and the fraction of empty
  windows), i.e. how finely a fixed nudge can meter powder;
* ``afterflow_mg``: mass leaving after the motor stops;
* ``funnel_holdup_mg``: powder sitting in the cone at the end (dead
  inventory that has to be bought and then cleaned out, the cost
  driver for Sc);
* grain mass, so doses can be expressed in grains.

Writes one JSON line per case and prints a markdown table.
"""

from __future__ import annotations

import argparse
import glob
import json
import math
import os
import re

import numpy as np


def load(case):
    meta = json.load(open(os.path.join(case, "case.json")))
    O = np.loadtxt(os.path.join(case, "outflow.txt"), comments="#", ndmin=2)
    return meta, O


def last_dump(case):
    files = glob.glob(os.path.join(case, "dump", "p.*.txt"))
    if not files:
        return None
    f = max(files, key=lambda p: int(re.findall(r"p\.(\d+)\.txt", p)[0]))
    with open(f) as fh:
        lines = fh.readlines()
    return np.loadtxt(lines[9:], ndmin=2)


def metrics(case):
    meta, O = load(case)
    cfg, geo = meta["cfg"], meta["geometry"]
    t, m = O[:, 0], O[:, 1] * 1e6
    T = meta["period_s"]
    t0 = meta["settle_s"]
    revs = cfg["revs"]
    t_stop = t0 + revs * T
    t_end = t[-1]
    done = t_end >= t_stop - 1e-6
    t_hi = min(t_stop, t_end)
    a = t0 + 0.25 * T
    rate = (np.interp(t_hi, t, m) - np.interp(a, t, m)) / max(t_hi - a, 1e-9)
    d = cfg["d_mean_mm"] * 1e-3
    grain_mg = cfg["density"] * math.pi / 6 * d ** 3 * 1e6
    out = {
        "case": os.path.basename(case.rstrip("/")),
        "incline_deg": cfg["incline_deg"], "rpm": cfg["rpm"], "d_mm": cfg["d_mean_mm"],
        "bore_d_mm": 2 * geo["bore_r"], "core_d_mm": 2 * max(geo["core_r"], geo["shaft_r"]),
        "shaft": geo["shaft_r"] > 0, "pitch_mm": geo["pitch"], "starts": geo["starts"],
        "exit_d_mm": 2 * geo["exit_r"], "n_particles_init": meta["n_init"],
        "complete": bool(done), "sim_time_s": float(t_end),
        "rate_mg_s": float(rate), "mg_per_rev": float(rate * T), "grain_mg": grain_mg,
        "m_first_rev_mg": float(np.interp(min(t0 + T, t_end), t, m) - np.interp(t0, t, m)),
        "wall_s": meta.get("wall_s"),
    }
    # windowed doses during steady rotation
    win = {}
    for deg in (5, 15, 45, 90):
        w = T * deg / 360.0
        edges = np.arange(a, t_hi - w + 1e-12, w)
        if len(edges) < 3:
            continue
        dm = np.interp(edges + w, t, m) - np.interp(edges, t, m)
        win[str(deg)] = {"mean_mg": float(dm.mean()), "sd_mg": float(dm.std(ddof=1)),
                         "cv": float(dm.std(ddof=1) / dm.mean()) if dm.mean() > 0 else None,
                         "p_empty": float(np.mean(dm < 0.5 * grain_mg)), "n": int(len(dm))}
    out["windows"] = win
    if cfg["stop_s"] > 0 and t_end > t_stop:
        out["afterflow_mg"] = float(m[-1] - np.interp(t_stop, t, m))
        out["afterflow_window_s"] = float(t_end - t_stop)
    A = last_dump(case)
    if A is not None and len(A):
        mass_mg = cfg["density"] * 4 / 3 * math.pi * A[:, 2] ** 3 * 1e6
        out["funnel_holdup_mg"] = float(mass_mg[A[:, 5] < geo["funnel_h"] * 1e-3].sum())
        out["section_holdup_mg"] = float(mass_mg.sum())
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cases", nargs="+")
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    rows = []
    for c in a.cases:
        if not os.path.exists(os.path.join(c, "outflow.txt")):
            continue
        try:
            rows.append(metrics(c))
        except Exception as e:  # noqa: BLE001 - keep summarising the other cases
            print("skip", c, e)
    if a.out:
        with open(a.out, "w") as f:
            for r in rows:
                f.write(json.dumps(r) + "\n")
    print("| case | tilt | rpm | bore | core | pitch | starts | exit | mg/rev | mg/s | CV@15deg | P(empty 5deg) | afterflow mg | funnel holdup mg | done |")
    print("|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    for r in rows:
        w15 = r["windows"].get("15", {})
        w5 = r["windows"].get("5", {})
        cv = w15.get("cv")
        print(f"| {r['case']} | {r['incline_deg']:g} | {r['rpm']:g} | {r['bore_d_mm']:g} | "
              f"{r['core_d_mm']:g}{' shaft' if r['shaft'] else ' open'} | {r['pitch_mm']:g} | {r['starts']} | {r['exit_d_mm']:g} | "
              f"{r['mg_per_rev']:.1f} | {r['rate_mg_s']:.1f} | {cv if cv is None else round(cv, 2)} | "
              f"{w5.get('p_empty', float('nan')):.2f} | {r.get('afterflow_mg', float('nan')):.1f} | "
              f"{r.get('funnel_holdup_mg', float('nan')):.0f} | {r['complete']} |")


if __name__ == "__main__":
    main()
