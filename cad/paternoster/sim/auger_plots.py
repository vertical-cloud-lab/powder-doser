"""Plots + results JSON for the MuJoCo auger dosing runs (reads out/auger/run_*.json/.npz)."""
from __future__ import annotations

import glob
import json
import os

import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out", "auger")
COL = {0: "#4C78A8", 15: "#72B7B2", 30: "#F58518", 45: "#E45756", 60: "#54A24B", 90: "#B279A2"}


def load():
    runs = {}
    for f in sorted(glob.glob(os.path.join(OUT, "run_*.json"))):
        tag = os.path.basename(f)[4:-5]
        meta = json.load(open(f))
        dat = np.load(f.replace(".json", ".npz"))
        runs[tag] = (meta, dat["log"])
    return runs


def smooth(y, n=20):
    if len(y) < n:
        return y
    k = np.ones(n) / n
    return np.convolve(np.pad(y, (n - 1, 0), mode="edge"), k, mode="valid")


def per_run_plot(tag, meta, L):
    mg = meta["m_grain_g"] * 1e3
    t = L[:, 0]
    fig, ax = plt.subplots(figsize=(8, 4.2), dpi=130)
    ax.plot(t, L[:, 3] * mg, color="#333333", lw=2, label="passed the outlet (grain count x grain mass)")
    ax.plot(t, L[:, 2] * mg, color="#F58518", lw=2, label="in the vial (grain count)")
    ax.plot(t, smooth(L[:, 5] * 1e3), color="#4C78A8", lw=1.2, alpha=0.9, label="balance reading (spring force, 0.2 s mean)")
    t_rot = meta["revs"] / (meta["rpm"] / 60)
    t_rev = meta["reverse_revs"] / (meta["rpm"] / 60) if meta["reverse_revs"] else 0
    ax.axvspan(0, t_rot, color="#54A24B", alpha=0.08, lw=0)
    if t_rev:
        ax.axvspan(t_rot, t_rot + t_rev, color="#E45756", alpha=0.10, lw=0)
    for r in range(1, int(meta["revs"]) + 1):
        ax.axvline(r * 60 / meta["rpm"], color="#999999", lw=0.6, ls=":")
    if meta["tap_hz"] > 0:
        tp = np.arange(0, t[-1], 1 / meta["tap_hz"])
        ax.plot(tp, np.zeros_like(tp), "v", color="#E45756", ms=6, label=f"tap ({meta['tap_n']:g} N, {meta['tap_ms']:g} ms)")
    ax.set_xlabel("time after opening the outlet (s)")
    ax.set_ylabel("proxy mass (mg)")
    ttl = f"tilt {meta['tilt_deg']:.0f} deg, {meta['rpm']:.0f} rpm x {meta['revs']:g} rev"  # noqa
    if meta["reverse_revs"]:
        ttl += f", then {meta['reverse_revs']:g} rev reverse"
    if meta["revs"] == 0:
        ttl = f"tilt {meta['tilt_deg']:.0f} deg, motor off (stored), outlet open"
    ttl += ", taps" if meta["tap_hz"] > 0 else ", no taps"
    ax.set_title(ttl, fontsize=11, loc="left")
    ax.spines[["top", "right"]].set_visible(False)
    ax.legend(fontsize=8, frameon=False, loc="upper left")
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, f"mass_vs_time_{tag}.png"))
    plt.close(fig)


def summary_plot(runs):
    fig, ax = plt.subplots(figsize=(8, 4.4), dpi=130)
    for tag, (meta, L) in runs.items():
        if meta["revs"] == 0 or meta["reverse_revs"] or meta.get("exit") != "scaled" or meta["rpm"] != 60:
            continue
        mg = meta["m_grain_g"] * 1e3
        c = COL.get(int(meta["tilt_deg"]), "#777777")
        ls = "--" if meta["tap_hz"] > 0 else "-"
        ax.plot(L[:, 0] * meta["rpm"] / 60, L[:, 3] * mg, ls, color=c, lw=2,
                label=f"tilt {meta['tilt_deg']:.0f} deg" + (", taps 2 Hz" if meta["tap_hz"] > 0 else ""))
    ax.set_xlabel("auger revolutions after opening (60 rpm; motor stops at 2 rev)")
    ax.set_ylabel("dispensed proxy mass (mg)")
    ax.spines[["top", "right"]].set_visible(False)
    ax.legend(fontsize=8, frameon=False)
    ax.set_title("Dispensed mass vs revolutions: effect of tilt and tapping", fontsize=11, loc="left")
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "dose_vs_rev_summary.png"))
    plt.close(fig)


def tilt_plot(table):
    rows = sorted([r for r in table.values() if r["revs"] == 2 and not r["reverse_revs"] and r["tap_hz"] == 0 and r["rpm"] == 60],
                  key=lambda r: r["tilt_deg"])
    taps = {r["tilt_deg"]: r for r in table.values() if r["revs"] == 2 and r["tap_hz"] > 0 and r["rpm"] == 60}
    x = np.array([r["tilt_deg"] for r in rows])
    fig, ax = plt.subplots(figsize=(7, 4), dpi=130)
    ax.plot(x, [r["dose_each_rev_mg"][0] for r in rows], "o-", color="#9D755D", lw=2, label="revolution 1 (includes the start-up dump)")
    ax.plot(x, [r["dose_each_rev_mg"][1] for r in rows], "s-", color="#4C78A8", lw=2, label="revolution 2 (conveyed)")
    for tl, r in taps.items():
        ax.plot([tl], [r["dose_each_rev_mg"][1]], "v", color="#E45756", ms=8,
                label="revolution 2 with 2 Hz taps" if tl == min(taps) else None)
    ax.set_xlabel("module tilt (deg; 0 = horizontal, 90 = outlet straight down)")
    ax.set_ylabel("proxy dose per revolution (mg)")
    ax.set_xticks([0, 15, 30, 45, 60, 90])
    ax.set_ylim(0, None)
    ax.spines[["top", "right"]].set_visible(False)
    ax.legend(fontsize=8, frameon=False)
    ax.set_title("Dose per revolution vs tilt (60 rpm, 1100-grain proxy)", fontsize=11, loc="left")
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "dose_per_rev_vs_tilt.png"))
    plt.close(fig)


if __name__ == "__main__":
    runs = load()
    table = {}
    for tag, (meta, L) in runs.items():
        per_run_plot(tag, meta, L)
        keys = ["tilt_deg", "rpm", "revs", "reverse_revs", "tap_hz", "tap_n", "tap_ms", "tap_when", "exit",
                "n_grains", "rp_mm", "m_grain_g", "exit_r_mm", "tip_r_mm", "n_exited_end_rotation", "n_exited_end_reverse",
                "n_exited_final", "n_in_vial_final", "n_floor_final", "mass_exited_rotation_mg", "dose_per_rev_mg",
                "dose_per_rev_after_first_mg", "dose_each_rev_mg", "flow_rate_mg_s", "afterflow_mg", "mass_vial_final_mg",
                "balance_reading_final_mg", "fill", "wall_s"]
        table[tag] = {k: meta.get(k) for k in keys}
    summary_plot(runs)
    tilt_plot(table)
    any_meta = next(iter(runs.values()))[0]
    settings = {k: any_meta[k] for k in ["units", "dt", "solver", "iterations", "solref", "mu", "mu_roll_mm", "mu_tors_mm",
                                         "rho", "rp_mm", "m_grain_g", "n_grains", "z_cut_mm", "exit_r_mm", "tip_r_mm",
                                         "vial_gap_mm", "vial_r_mm", "balance_k", "mount_k", "mount_c"]}
    heaps = [json.load(open(f)) for f in glob.glob(os.path.join(OUT, "heap_*.json"))]
    res = dict(settings=settings, runs=table,
               heap_tests=[{k: h.get(k) for k in ["n", "rp_mm", "mu", "mu_roll", "impratio", "noslip", "angle_of_repose_deg", "heap_h_mm"]} for h in heaps])
    json.dump(res, open(os.path.join(OUT, "auger_results.json"), "w"), indent=1)
    for tag, r in table.items():
        print(f"{tag:12s} tilt {r['tilt_deg']:4.0f} tap {r['tap_hz']:g}  exited(rot) {r['n_exited_end_rotation']:4d}  "
              f"{r['dose_per_rev_mg']:7.1f} mg/rev  each {np.round(r['dose_each_rev_mg'], 0)}  after-first {r.get('dose_per_rev_after_first_mg')}  "
              f"afterflow {r['afterflow_mg']:.0f} mg  vial {r['n_in_vial_final']} floor {r['n_floor_final']} final exited {r['n_exited_final']}")
