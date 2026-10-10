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
RIG_G_PER_REV = 0.113   # bench salt feed factor (trickle_params.py FF_PRIOR comment, PR #166 branch)
RIG_TAU_S = 0.8338      # salt tau_afterflow (data/powder_models/salt.json, PR #166 branch)

plt.rcParams.update({"font.size": 10, "axes.edgecolor": INK2, "axes.labelcolor": INK, "xtick.color": INK2,
                     "ytick.color": INK2, "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.8,
                     "axes.spines.top": False, "axes.spines.right": False, "lines.linewidth": 2.0,
                     "figure.facecolor": "#fcfcfb", "axes.facecolor": "#fcfcfb", "savefig.facecolor": "#fcfcfb"})


def load_case(case):
    meta = json.load(open(os.path.join(case, "case.json")))
    O = np.loadtxt(os.path.join(case, "outflow.txt"), comments="#", ndmin=2)
    return meta, O[:, 0], O[:, 1] * 1e6


def fig_baseline(case, out):
    meta, t, m = load_case(case)
    T, t0 = meta["period_s"], meta["settle_s"]
    revs = meta["cfg"]["revs"]
    t_stop = t0 + revs * T
    m0 = np.interp(t0, t, m)
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(11, 4.2), gridspec_kw={"width_ratios": [1.35, 1]})
    a1.axvspan(0, (t_stop - t0) / T, color="#eef4e8", zorder=0, lw=0)
    a1.plot((t - t0) / T, m - m0, color=C[0], label="DEM twin")
    a1.plot([0, revs], [0, RIG_G_PER_REV * 1e3 * revs], color=C[1], ls="--", lw=1.6,
            label=f"rig feed factor ({RIG_G_PER_REV * 1e3:.0f} mg/rev)")
    a1.set_xlabel("auger revolutions since motor start")
    a1.set_ylabel("dispensed mass (mg)")
    a1.set_xlim(left=min(-0.1, (t[0] - t0) / T))
    a1.text(0.02, 0.96, "motor on", transform=a1.transAxes, va="top", color="#4a7a2a", fontsize=9)
    a1.legend(frameon=False, loc="upper left", bbox_to_anchor=(0.0, 0.9))
    a1.set_title("Auger4, salt d = 0.45 mm, 30° tilt, 55 rpm", fontsize=10, color=INK)
    # 45-degree pulse train during steady rotation
    w = T / 8
    edges = np.arange(t0, min(t_stop, t[-1]) - w + 1e-12, w)
    dm = np.interp(edges + w, t, m) - np.interp(edges, t, m)
    a2.bar((edges - t0) / T + 1 / 16, dm, width=1 / 8 * 0.86, color=C[0], edgecolor="none")
    a2.axhline(RIG_G_PER_REV * 1e3 / 8, color=C[1], ls="--", lw=1.4)
    a2.set_xlabel("auger revolutions since motor start")
    a2.set_ylabel("mass per 45° of rotation (mg)")
    a2.set_title("dose arrives in pulses", fontsize=10, color=INK)
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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", default="/tmp/dem/runs")
    ap.add_argument("--bench", default="/tmp/dem/bench/bench_results.jsonl")
    ap.add_argument("--out", default="results")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    if os.path.exists(os.path.join(a.runs, "baseline", "outflow.txt")):
        fig_baseline(os.path.join(a.runs, "baseline"), os.path.join(a.out, "baseline_vs_rig.png"))
    if os.path.exists(a.bench):
        fig_scaling(a.bench, os.path.join(a.out, "scaling.png"))
    labels = {
        "micro_open": "micro, open 4 mm core",
        "micro_shaft": "micro, solid shaft",
        "micro_exit18": "micro, 1.8 mm exit",
        "micro_pitch3": "micro, 3 mm pitch",
        "micro_2start": "micro, 2-start flight",
        "micro_tilt0": "micro, 0° tilt",
        "a4_tilt15": "Auger4 (rig), 15° tilt",
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
    with open(os.path.join(a.out, "metrics.jsonl"), "w") as f:
        for k in ["baseline", *labels]:
            c = os.path.join(a.runs, k)
            if os.path.exists(os.path.join(c, "outflow.txt")):
                f.write(json.dumps(metrics(c)) + "\n")


if __name__ == "__main__":
    main()
