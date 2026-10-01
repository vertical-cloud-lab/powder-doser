#!/usr/bin/env python3
"""Analyze the phase-resolved afterflow battery (PR #131, 2026-08-13).

Parses the CSV-over-stdout telemetry from
``hardware/test-module/firmware/afterflow_phase.py`` and produces:

  Test A -- slug periodicity: per-increment yield binned by auger phase
            (is delivery periodic at exactly 360 deg of auger?), plus the
            cumulative mass-vs-angle staircase.
  Test B -- afterflow vs halt phase: afterflow (settled - m_halt) vs the
            COMMANDED auger stop phase, per tilt, with a single-harmonic
            fit to test phase dependence.

Usage:  python scripts/analyze_afterflow_phase.py <log> <outdir>
"""
import sys
import os
import math
import csv

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def parse(path):
    meta = {}
    A = []   # (trial,scan,incr,tilt,rpm,incr_deg,cum_deg,phase_deg,rev,mb,ma,yld)
    B = []   # (trial,tilt,rep,rpm,cruise,phase,rev_tot,mbase,mhalt,tmove,mset,after,disp,absm,verdict)
    D = []   # (t_ms,trial,phase,mass,stab,rpm,rev,phase_deg)
    with open(path) as f:
        for line in f:
            p = line.rstrip("\n").split(",")
            if not p:
                continue
            k = p[0]
            try:
                if k == "M" and len(p) >= 3:
                    meta[p[1]] = p[2]
                elif k == "A" and len(p) >= 12:
                    A.append((int(p[1]), int(p[2]), int(p[3]), float(p[4]),
                              float(p[5]), float(p[6]), float(p[7]),
                              float(p[8]), float(p[9]), float(p[10]),
                              float(p[11]), float(p[12] if len(p) > 12
                                                 else p[11])))
                elif k == "B" and len(p) >= 15:
                    def fv(x):
                        return float("nan") if x == "nan" else float(x)
                    B.append((int(p[1]), float(p[2]), int(p[3]), float(p[4]),
                              int(p[5]), float(p[6]), fv(p[7]), fv(p[8]),
                              fv(p[9]), fv(p[10]), fv(p[11]), fv(p[12]),
                              fv(p[13]), fv(p[14]), p[15]))
                elif k == "D" and len(p) >= 9:
                    mass = float("nan") if p[4] == "nan" else float(p[4])
                    D.append((int(p[1]), int(p[2]), p[3], mass, p[5],
                              float(p[6]), float(p[7]), float(p[8])))
            except (ValueError, IndexError):
                continue
    return meta, A, B, D


def mean(xs):
    xs = [x for x in xs if x == x]
    return sum(xs) / len(xs) if xs else float("nan")


def sem(xs):
    xs = [x for x in xs if x == x]
    if len(xs) < 2:
        return float("nan")
    m = sum(xs) / len(xs)
    v = sum((x - m) ** 2 for x in xs) / (len(xs) - 1)
    return (v / len(xs)) ** 0.5


def harmonic_fit(phases_deg, ys):
    """Least-squares fit y = a0 + a1*cos(phi) + b1*sin(phi).  Returns
    (a0, amplitude, phase0_deg, frac_var_explained)."""
    pts = [(p, y) for p, y in zip(phases_deg, ys) if y == y]
    n = len(pts)
    if n < 4:
        return float("nan"), float("nan"), float("nan"), float("nan")
    # normal equations for [1, cos, sin]
    import itertools
    S = [[0.0] * 3 for _ in range(3)]
    T = [0.0] * 3
    for p, y in pts:
        r = math.radians(p)
        basis = [1.0, math.cos(r), math.sin(r)]
        for i in range(3):
            T[i] += basis[i] * y
            for j in range(3):
                S[i][j] += basis[i] * basis[j]
    # solve 3x3 (Gaussian elimination)
    M = [row[:] + [T[i]] for i, row in enumerate(S)]
    for c in range(3):
        piv = max(range(c, 3), key=lambda r: abs(M[r][c]))
        if abs(M[piv][c]) < 1e-12:
            return float("nan"), float("nan"), float("nan"), float("nan")
        M[c], M[piv] = M[piv], M[c]
        d = M[c][c]
        M[c] = [v / d for v in M[c]]
        for r in range(3):
            if r != c:
                f = M[r][c]
                M[r] = [a - f * b for a, b in zip(M[r], M[c])]
    a0, a1, b1 = M[0][3], M[1][3], M[2][3]
    amp = (a1 ** 2 + b1 ** 2) ** 0.5
    ph0 = math.degrees(math.atan2(b1, a1)) % 360   # peak of amp*cos(x-ph0)
    ys_only = [y for _, y in pts]
    ybar = sum(ys_only) / n
    sst = sum((y - ybar) ** 2 for y in ys_only)
    ssr = 0.0
    for p, y in pts:
        r = math.radians(p)
        pred = a0 + a1 * math.cos(r) + b1 * math.sin(r)
        ssr += (y - pred) ** 2
    frac = 1 - ssr / sst if sst > 0 else float("nan")
    return a0, amp, ph0, frac


def analyze_A(A, outdir):
    if not A:
        return {}
    # bin per-increment yield by phase (use the phase at END of increment)
    bins = {}
    for row in A:
        (_, scan, incr, tilt, rpm, incr_deg, cum_deg, phase_deg, rev,
         mb, ma, yld) = row
        b = round(phase_deg)
        bins.setdefault(b, []).append(yld)
    phases = sorted(bins)
    means = [mean(bins[b]) for b in phases]
    sems = [sem(bins[b]) for b in phases]
    a0, amp, ph0, frac = harmonic_fit([float(b) for b in phases],
                                      [mean(bins[b]) for b in phases])
    # cumulative curve (scan 1)
    s1 = [r for r in A if r[1] == 1]

    fig, ax = plt.subplots(1, 2, figsize=(12, 4.6))
    ax[0].bar([str(int(b)) for b in phases], [m * 1000 for m in means],
              yerr=[(s * 1000 if s == s else 0) for s in sems],
              color="#4C78A8", capsize=3)
    ax[0].axhline(mean(means) * 1000, color="#888", ls="--", lw=1,
                  label="mean {:.1f} mg".format(mean(means) * 1000))
    ax[0].set_xlabel("auger phase bin (deg, end of 45-deg increment)")
    ax[0].set_ylabel("yield per 45 deg increment (mg)")
    ax[0].set_title("Test A: yield vs auger phase\n"
                    "(pooled over {} revolutions x {} scans)".format(
                        4, max(r[1] for r in A)))
    ax[0].legend(fontsize=8)

    for scan in sorted(set(r[1] for r in A)):
        rows = [r for r in A if r[1] == scan]
        ax[1].plot([r[6] / 360.0 for r in rows], [r[10] for r in rows],
                   marker=".", ms=4, lw=1, label="scan {}".format(scan))
    for x in range(1, 5):
        ax[1].axvline(x, color="#ddd", lw=1, zorder=0)
    ax[1].set_xlabel("cumulative auger revolutions")
    ax[1].set_ylabel("absolute cup mass (g)")
    ax[1].set_title("Test A: cumulative mass vs auger angle\n"
                    "(gridlines = whole auger revolutions)")
    ax[1].legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(os.path.join(outdir, "afterflow_phase_slug.png"), dpi=110)
    plt.close(fig)

    return {"phase_bins": phases, "bin_mean_mg": [m * 1000 for m in means],
            "harm_a0_mg": a0 * 1000, "harm_amp_mg": amp * 1000,
            "harm_peak_deg": ph0, "harm_frac_var": frac}


def _detrend_by_rep(rows):
    """Return {phase: [afterflow/rep_mean, ...]} after removing each
    (tilt,rep)'s mean afterflow -- isolates the phase effect from the
    strong within-session flow drift."""
    by_rep = {}
    for r in rows:
        by_rep.setdefault((r[1], r[2]), []).append(r)
    norm = {}
    for _, rs in by_rep.items():
        vals = [x[11] for x in rs if x[11] == x[11]]
        m = mean(vals)
        if not m:
            continue
        for x in rs:
            norm.setdefault(x[5], []).append(x[11] / m)
    return norm


def analyze_B(B, outdir):
    B = [r for r in B if r[14] == "ok"]
    if not B:
        return {}
    tilts = sorted(set(r[1] for r in B))
    summary = {}

    fig, axes = plt.subplots(1, 3, figsize=(16.5, 4.8))

    # ---- panel 1: raw afterflow vs phase, per tilt (drift-dominated) ----
    ax = axes[0]
    colors = {55.0: "#4C78A8", 70.0: "#E45756"}
    for tilt in tilts:
        rows = [r for r in B if r[1] == tilt]
        by = {}
        for r in rows:
            by.setdefault(r[5], []).append(r[11])
        phs = sorted(by)
        ax.errorbar(phs, [mean(by[p]) * 1000 for p in phs],
                    yerr=[(sem(by[p]) * 1000 if sem(by[p]) == sem(by[p])
                           else 0) for p in phs],
                    marker="o", capsize=3, lw=1.8,
                    color=colors.get(tilt, "#555"),
                    label="{:.0f} deg tilt".format(tilt))
        _, amp, ph0, frac = harmonic_fit([r[5] for r in rows],
                                         [r[11] for r in rows])
        summary["tilt_{:.0f}".format(tilt)] = {
            "afterflow_grand_mean_mg": mean([r[11] for r in rows]) * 1000,
            "raw_harm_amp_mg": amp * 1000, "raw_harm_R2": frac}
    ax.set_xlabel("commanded auger stop phase (deg)")
    ax.set_ylabel("afterflow = settled - m_halt (mg)")
    ax.set_title("Test B panel 1: RAW afterflow vs stop phase\n"
                 "(dominated by session flow-drift, not phase)")
    ax.legend(fontsize=8)

    # ---- panel 2: detrended (per-rep) afterflow vs phase -- the signal ----
    ax = axes[1]
    norm = _detrend_by_rep(B)
    phs = sorted(norm)
    ms = [mean(norm[p]) for p in phs]
    es = [sem(norm[p]) for p in phs]
    for p in phs:
        for v in norm[p]:
            ax.scatter([p], [v], color="#4C78A8", s=18, alpha=0.45, zorder=3)
    ax.errorbar(phs, ms, yerr=[(e if e == e else 0) for e in es],
                color="#E45756", lw=2, marker="o", capsize=3, zorder=4,
                label="mean +/- sem")
    ax.axhline(1.0, color="#888", ls="--", lw=1)
    a0, amp, ph0, frac = harmonic_fit(
        [p for p in norm for _ in norm[p]],
        [v for p in norm for v in norm[p]])
    if amp == amp:
        xs = [i for i in range(0, 361, 5)]
        ys = [a0 + a1_b1(a0, amp, ph0, x) for x in xs]
        ax.plot(xs, ys, color="#54A24B", ls="--", lw=1.5,
                label="1-harmonic (R2={:.2f})".format(frac))
    ax.set_xlabel("commanded auger stop phase (deg)")
    ax.set_ylabel("afterflow / rep-mean  (detrended)")
    ax.set_title("Test B panel 2: DETRENDED afterflow vs phase\n"
                 "(per-rep drift removed -> phase effect isolated)")
    ax.legend(fontsize=8)
    summary["detrended"] = {"phases": phs,
                            "afterflow_frac_of_repmean": ms,
                            "harm_amp_frac": amp, "harm_peak_deg": ph0,
                            "harm_R2": frac}

    # ---- panel 3: session drift (afterflow vs trial order) ----
    ax = axes[2]
    for tilt in tilts:
        rows = sorted([r for r in B if r[1] == tilt], key=lambda r: r[0])
        ax.plot([r[0] for r in rows], [r[11] * 1000 for r in rows],
                marker="o", ms=4, lw=1.2, color=colors.get(tilt, "#555"),
                label="{:.0f} deg tilt".format(tilt))
    ax.set_xlabel("trial number (session order)")
    ax.set_ylabel("afterflow (mg)")
    ax.set_title("Test B panel 3: afterflow drifts DOWN over the session\n"
                 "(salt flow non-stationarity -- the dominant effect)")
    ax.legend(fontsize=8)

    fig.tight_layout()
    fig.savefig(os.path.join(outdir, "afterflow_phase_halt.png"), dpi=110)
    plt.close(fig)
    return summary


def a1_b1(a0, amp, ph0, x):
    return amp * math.cos(math.radians(x - ph0))


def write_csvs(A, B, outdir):
    with open(os.path.join(outdir, "afterflow_phase_A.csv"), "w") as f:
        w = csv.writer(f)
        w.writerow(["trial", "scan", "incr", "tilt", "rpm", "incr_deg",
                    "cum_deg", "phase_deg", "auger_rev", "m_before",
                    "m_after", "yield_g"])
        for r in A:
            w.writerow(r)
    with open(os.path.join(outdir, "afterflow_phase_B.csv"), "w") as f:
        w = csv.writer(f)
        w.writerow(["trial", "tilt", "rep", "rpm", "cruise_revs",
                    "phase_cmd_deg", "auger_rev_total", "m_base", "m_halt",
                    "t_move_s", "m_settled", "afterflow_g", "dispensed_g",
                    "abs_mass_g", "verdict"])
        for r in B:
            w.writerow(r)


def main():
    path = sys.argv[1]
    outdir = sys.argv[2]
    os.makedirs(outdir, exist_ok=True)
    meta, A, B, D = parse(path)
    write_csvs(A, B, outdir)
    sa = analyze_A(A, outdir)
    sb = analyze_B(B, outdir)
    print("=== META ===")
    for k in ("gear_ratio_stepper_per_auger", "steps_per_auger_rev",
              "tare_mode", "rpm_B", "cruise_revs_B"):
        if k in meta:
            print("  {} = {}".format(k, meta[k]))
    print("=== Test A (slug periodicity) ===")
    print("  ", sa)
    print("=== Test B (afterflow vs halt phase) ===")
    for k, v in sb.items():
        print("  {}: {}".format(k, v))
    print("A rows: {}, B rows(ok): {}".format(
        len(A), len([r for r in B if r[14] == "ok"])))


if __name__ == "__main__":
    main()
