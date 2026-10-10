"""Figures for the DEM twin write-up (sim/dem/README.md).

    python figures.py --runs /tmp/dem/runs --bench /tmp/dem/bench/bench_results.jsonl --out results/

Produces:
  baseline_vs_rig.png   cumulative dispensed mass of the faithful Auger4 case
                        vs the rig's bench feed factor, plus the per-45-deg
                        pulse train and the afterflow tail
  scaling.png           particle count vs throughput / memory on this runner,
                        with the particle counts of real doses and augers
  sweep.png             micro-auger geometry variants: mg per rev, dose
                        quantum spread, afterflow and dead inventory
"""

from __future__ import annotations

import argparse
import json
import math
import os
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from analyze import metrics  # noqa: E402

INK, INK2, GRID = "#0b0b0b", "#52514e", "#e4e3df"
C = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#6250d6", "#e34948"]

plt.rcParams.update({"font.size": 10, "axes.edgecolor": INK2, "axes.labelcolor": INK, "xtick.color": INK2,
                     "ytick.color": INK2, "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.8,
                     "axes.spines.top": False, "axes.spines.right": False, "lines.linewidth": 2.0,
                     "figure.facecolor": "#fcfcfb", "axes.facecolor": "#fcfcfb", "savefig.facecolor": "#fcfcfb"})


def load_case(case):
    meta = json.load(open(os.path.join(case, "case.json")))
    O = np.loadtxt(os.path.join(case, "outflow.txt"), comments="#", ndmin=2)
    return meta, O[:, 0], O[:, 1] * 1e6


# measured salt yields for the rig auger (mg per auger revolution, mean, sd, label)
RIG_DATA = {
    "rig_t27p5_r60": (105.0, 11.0, "PR #166 centre point, 27.5°, 60 rpm (n = 8)"),
    "rig_t22p5_r90": (108.0, 2.5, "battery D, 22.5°, 90 rpm (106.4 / 109.9)"),
    "rig_t27p5_r60_tip2": (105.0, 11.0, "PR #166 centre point, 27.5°, 60 rpm (n = 8)"),
}
CASE_LABEL = {
    "rig_t27p5_r60": "CAD exit",
    "rig_t22p5_r90": "CAD exit",
    "rig_t27p5_r60_tip2": "core tip cut 2 mm short",
}


def fig_rig(cases, out):
    cases = [c for c in cases if os.path.exists(os.path.join(c, "outflow.txt"))]
    if not cases:
        return
    fig, axes = plt.subplots(1, 2, figsize=(11.5, 4.3), gridspec_kw={"width_ratios": [1.3, 1]})
    a1, a2 = axes
    drawn = set()
    for i, case in enumerate(cases):
        key = os.path.basename(case.rstrip("/"))
        meta, t, m = load_case(case)
        T, t0 = meta["period_s"], meta["settle_s"]
        revs = meta["cfg"]["revs"]
        m0 = np.interp(t0, t, m)
        col = C[i]
        lab = f"twin, {CASE_LABEL.get(key, key)}: {meta['cfg']['incline_deg']:g}°, {meta['cfg']['rpm']:g} rpm"
        a1.plot((t - t0) / T, m - m0, color=col, label=lab)
        if key in RIG_DATA and RIG_DATA[key][2] not in drawn:
            mu, sd, rl = RIG_DATA[key]
            drawn.add(rl)
            rr = np.array([0, revs])
            a1.fill_between(rr, (mu - sd) * rr, (mu + sd) * rr, color=INK2, alpha=0.10, lw=0)
            a1.plot(rr, mu * rr, color=INK2, ls="--", lw=1.4, label=f"rig: {rl}")
        if key == "rig_t27p5_r60":
            w = T / 8
            t_stop = t0 + revs * T
            edges = np.arange(t0, min(t_stop, t[-1]) - w + 1e-12, w)
            dm = np.interp(edges + w, t, m) - np.interp(edges, t, m)
            a2.bar((edges - t0) / T + 1 / 16, dm, width=1 / 8 * 0.86, color=col, edgecolor="none")
            if key in RIG_DATA:
                a2.axhline(RIG_DATA[key][0] / 8, color=col, ls="--", lw=1.3)
                a2.text(0.01, RIG_DATA[key][0] / 8, " rig mean / 8", va="bottom", fontsize=8, color=INK2)
            a2.set_title(f"dose arrives in pulses ({meta['cfg']['incline_deg']:g}°, {meta['cfg']['rpm']:g} rpm)", fontsize=10)
    a1.axvline(0, color=INK2, lw=0.8, ls=":")
    a1.set_xlabel("auger revolutions since motor start (after the last tick the motor is stopped)")
    a1.set_ylabel("dispensed mass (mg)")
    a1.set_title("Rig auger, real-size salt (d50 0.425 mm): twin vs measured", fontsize=10)
    a1.legend(frameon=False, fontsize=8, loc="upper left")
    a2.set_xlabel("auger revolutions since motor start")
    a2.set_ylabel("mass per 45° of rotation (mg)")
    fig.tight_layout()
    fig.savefig(out, dpi=130)
    plt.close(fig)


def fig_scaling(bench_jsonl, out):
    B = [json.loads(line) for line in open(bench_jsonl)]
    B.sort(key=lambda r: r["n_particles"])
    N = np.array([r["n_particles"] for r in B], float)
    thr = np.array([r["particle_steps_per_s"] for r in B])
    mem = np.array([r["peak_rss_mb"] for r in B]) / 1024
    # real counts
    free_vol_mm3 = (math.pi * 10.5 ** 2 - 63.1) * 238 + 1139  # Auger4 bore minus flight, plus funnel
    phi = 0.6

    def count(d_mm, vol_mm3):
        return phi * vol_mm3 / (math.pi / 6 * d_mm ** 3)

    def dose(d_mm, rho_mg_mm3, mg):
        return mg / (rho_mg_mm3 * math.pi / 6 * d_mm ** 3)

    marks = [
        ("10 mg salt (d 0.45 mm)", dose(0.45, 2.16, 10)),
        ("one rev of salt (113 mg)", dose(0.45, 2.16, 113)),
        ("1 mg Sc (d 40 µm)", dose(0.040, 2.99, 1)),
        ("10 mg AlSi10Mg (d 35 µm)", dose(0.035, 2.67, 10)),
        ("full Auger4 of salt", count(0.45, free_vol_mm3)),
        ("Auger4 funnel of AlSi10Mg", count(0.035, 1139)),
        ("full Auger4 of AlSi10Mg", count(0.035, free_vol_mm3)),
    ]
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(11, 4.4))
    nn = np.logspace(2, 10, 50)
    bpp = np.median([r["bytes_per_particle"] for r in B if r["n_particles"] > 3e5] or [2000])
    a1.loglog(N, mem, "o", color=C[0], ms=8, label="measured peak RAM (1 core)")
    a1.loglog(nn, nn * bpp / 1024 ** 3, color=C[0], lw=1.2, alpha=0.6, label=f"{bpp / 1e3:.1f} kB per particle")
    a1.axhline(15, color=C[7], lw=1.2, ls="--")
    a1.text(1.5e2, 17, "this runner: 15 GB", color=INK2, fontsize=8)
    for i, (lab, n) in enumerate(marks):
        a1.axvline(n, color=INK2, lw=0.6, alpha=0.5)
        a1.text(n * 1.08, 2e-3 * (3.2 ** (i % 4)), lab, rotation=90, fontsize=7.5, color=INK2, va="bottom")
    a1.set_xlim(1e2, 1e10)
    a1.set_ylim(1e-3, 1e4)
    a1.set_xlabel("particles in the simulation")
    a1.set_ylabel("memory (GB)")
    a1.legend(frameon=False, loc="upper left", fontsize=8)
    a1.set_title("Memory: how many grains fit", fontsize=10)
    # wall time per auger revolution at 55 rpm for salt-sized grains
    steps_rev = (60 / 55) / 2.18e-5
    per_core = np.median(thr)
    hrs1 = nn * steps_rev / per_core / 3600
    a2.loglog(nn, hrs1, color=C[0], label=f"1 CPU core ({per_core / 1e6:.2f} M particle-steps/s, measured)")
    a2.loglog(nn, hrs1 / 4 / 0.85, color=C[2], label="4 cores, ideal MPI (not working in this build)")
    a2.loglog(N, N * steps_rev / thr / 3600, "o", color=C[0], ms=7)
    for i, (lab, n) in enumerate(marks[:5]):
        a2.axvline(n, color=INK2, lw=0.6, alpha=0.5)
        a2.text(n * 1.08, 3e-3 * (4 ** (i % 3)), lab, rotation=90, fontsize=7.5, color=INK2, va="bottom")
    a2.axhline(1, color=INK2, lw=0.8, ls=":")
    a2.text(1.5e2, 1.2, "1 hour", fontsize=8, color=INK2)
    a2.axhline(24, color=INK2, lw=0.8, ls=":")
    a2.text(1.5e2, 29, "1 day", fontsize=8, color=INK2)
    a2.set_xlim(1e2, 1e7)
    a2.set_xlabel("particles in the simulation")
    a2.set_ylabel("wall time per auger revolution (h)")
    a2.set_title("Speed: salt-sized grains (dt 22 µs), 55 rpm", fontsize=10)
    a2.legend(frameon=False, loc="upper left", fontsize=8)
    fig.tight_layout()
    fig.savefig(out, dpi=130)
    plt.close(fig)


def fig_sweep(rows, out, title):
    rows = [r for r in rows if r.get("complete")]
    if not rows:
        return
    labels = [r["label"] for r in rows]
    y = np.arange(len(rows))
    fig, ax = plt.subplots(1, 4, figsize=(13, 0.55 * len(rows) + 1.6), sharey=True)
    vals = [
        ([r["mg_per_rev"] for r in rows], "mass per revolution (mg)"),
        ([r["windows"].get("15", {}).get("sd_mg", np.nan) for r in rows], "sd of mass per 15° nudge (mg)"),
        ([r.get("afterflow_mg", np.nan) for r in rows], "afterflow in 0.5 s after stop (mg)"),
        ([r.get("funnel_holdup_mg", np.nan) for r in rows], "powder parked in funnel (mg)"),
    ]
    for a, (v, lab) in zip(ax, vals):
        a.barh(y, v, color=C[0], height=0.6)
        for yi, vi in zip(y, v):
            if np.isfinite(vi):
                a.text(vi, yi, f" {vi:.1f}" if vi < 100 else f" {vi:.0f}", va="center", fontsize=8, color=INK)
        a.set_xlabel(lab, fontsize=9)
        a.grid(axis="y", visible=False)
        a.margins(x=0.25)
    ax[0].set_yticks(y, labels)
    ax[0].invert_yaxis()
    fig.suptitle(title, fontsize=10.5)
    fig.tight_layout()
    fig.savefig(out, dpi=130)
    plt.close(fig)


def fig_quantum(rows, out):
    """sd of the mass delivered per rotation increment vs its mean, against the grain-counting limit."""
    rows = [r for r in rows if r.get("complete") and r["windows"]]
    if not rows:
        return
    fig, ax = plt.subplots(figsize=(6.8, 5.0))
    mm = np.logspace(-1.3, 2.3, 50)
    g = rows[0]["grain_mg"]
    ax.loglog(mm, np.sqrt(mm * g), color=INK2, lw=1.2, ls="--")
    ax.text(mm[-12], np.sqrt(mm[-12] * g) * 0.62, "Poisson limit\n(independent grains)", fontsize=8, color=INK2)
    for i, r in enumerate(rows[:8]):
        w = r["windows"]
        ks = [k for k in ("5", "15", "45", "90") if k in w]
        x = [w[k]["mean_mg"] for k in ks]
        y = [w[k]["sd_mg"] for k in ks]
        ax.loglog(x, y, "o-", color=C[i], ms=6, lw=1.6, label=r.get("label", r["case"]))
    ax.set_xlabel("mean mass per nudge (mg)  [5°, 15°, 45°, 90° of rotation]")
    ax.set_ylabel("sd of mass per nudge (mg)")
    ax.set_title("Dose quantum: how repeatable is a fixed rotation step?", fontsize=10)
    ax.legend(frameon=False, fontsize=7.5, loc="upper left")
    fig.tight_layout()
    fig.savefig(out, dpi=130)
    plt.close(fig)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", default="/tmp/dem/runs")
    ap.add_argument("--bench", default="/tmp/dem/bench/bench_results.jsonl")
    ap.add_argument("--out", default="results")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    fig_rig([os.path.join(a.runs, k) for k in RIG_DATA], os.path.join(a.out, "rig_vs_measured.png"))
    if os.path.exists(a.bench):
        fig_scaling(a.bench, os.path.join(a.out, "scaling.png"))
    labels = {
        "micro_open": "micro, open 4 mm core",
        "micro_shaft": "micro, solid shaft",
        "micro_exit18": "micro, 1.8 mm exit",
        "micro_pitch3": "micro, 3 mm pitch",
        "micro_2start": "micro, 2-start flight",
        "micro_tilt0": "micro, 0° tilt",
        "micro_rig": "micro, rig-style solid core + tip",
        "micro_cone45": "micro, 45° funnel (3 mm)",
        "micro_cone17": "micro, 17° funnel (10 mm)",
        "micro_hifric": "micro, high friction",
        "micro_cohesive": "micro, solid shaft, cohesive (SJKR)",
        "micro_shaft_pitch3": "micro, solid shaft, 3 mm pitch",
    }
    rows = []
    for k, lab in labels.items():
        c = os.path.join(a.runs, k)
        if os.path.exists(os.path.join(c, "outflow.txt")):
            r = metrics(c)
            r["label"] = lab
            rows.append(r)
    fig_sweep(rows, os.path.join(a.out, "sweep.png"),
              "Geometry variants at the trickle tilt (15°, 55 rpm, salt d = 0.45 mm); micro = 10 mm bore, 5 mm pitch, 2.5 mm exit")
    fig_quantum(rows, os.path.join(a.out, "dose_quantum.png"))
    with open(os.path.join(a.out, "metrics.jsonl"), "w") as f:
        for k in [*RIG_DATA, *labels]:
            c = os.path.join(a.runs, k)
            if os.path.exists(os.path.join(c, "outflow.txt")):
                f.write(json.dumps(metrics(c)) + "\n")


if __name__ == "__main__":
    main()
