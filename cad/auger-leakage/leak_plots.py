"""Plots and the results JSON for the leakage study (reads out/<tag>.json and out/<tag>.npz).

    python leak_plots.py      # -> out/exit_powder.png, out/v2_lap_pumping.png, out/leak_results.json
"""
from __future__ import annotations

import glob
import json
import os

import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")

# reference palette (dataviz skill): categorical slots in fixed order, recessive ink and grid
CAT = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100"]
INK, INK2, GRID, SURF = "#0b0b0b", "#52514e", "#e4e3df", "#fcfcfb"
plt.rcParams.update({"font.size": 10.5, "axes.edgecolor": INK2, "axes.labelcolor": INK, "xtick.color": INK2,
                     "ytick.color": INK2, "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.8,
                     "axes.spines.top": False, "axes.spines.right": False, "figure.facecolor": SURF,
                     "axes.facecolor": SURF, "savefig.facecolor": SURF, "legend.frameon": False})


def load(tag):
    p = os.path.join(OUT, f"{tag}.json")
    if not os.path.exists(p):
        return None, None
    z = os.path.join(OUT, f"{tag}.npz")
    return json.load(open(p)), (np.load(z) if os.path.exists(z) else None)


def n_phase(z, phases):
    return int(np.isin(z["exit_ph"], np.atleast_1d(phases)).sum())


def entry(r, z):
    L = z["log"]
    e = dict(kind=r["kind"], alpha_deg=r["alpha_deg"], seed=r.get("seed", 0), exits_by_phase=r["exits_by_phase"],
             at_exit_start=int(L[0, 6]), at_exit_final=int(L[-1, 6]))
    for k in ("prefix", "hold_s", "protocol", "R_rev", "transit", "vib_g", "vib_hz", "direction", "dose_tilt_world"):
        if k in r:
            e[k] = r[k]
    if r["kind"] == "branch":
        e["out_reverse_at_dose_tilt"] = n_phase(z, 3)
        e["out_hold_at_dose_tilt"] = n_phase(z, 2)
        e["out_return"] = n_phase(z, 4)
        e["out_at_rest"] = n_phase(z, [5, 6, 7, 14, 15, 16])      # what a moving or shaken module could lose
        e["vial_gain"] = int(L[-1, 7] - L[0, 7])                  # grains that landed in the vial during the branch
    if r["kind"] == "v2lap":
        e["at_exit_start"] = int(L[L[:, 1] >= 9, 6][0])            # at the first corner
        e["out_lap"] = n_phase(z, [9, 10, 11, 12, 13])
        e["out_by_corner"] = [n_phase(z, 9 + c) for c in range(4)]
    if r["kind"] == "store":
        e["at_exit_start"] = int(L[L[:, 1] == 14, 6][0])           # when the taps start
        e["out_taps"] = n_phase(z, 14)
    return e


def main():
    res = {"runs": {}, "summary": {}}
    mg = None
    for p in sorted(glob.glob(os.path.join(OUT, "*.json"))):
        tag = os.path.basename(p)[:-5]
        r, z = load(tag)
        if r is None or z is None or "exits_by_phase" not in r:
            continue
        mg = r["m_grain_mg"]
        res["runs"][tag] = entry(r, z)
    res["m_grain_mg"] = mg
    R = res["runs"]

    # ---- figure 1: powder left at the exit, vs rest pitch (left) and vs post-dose reverse (right)
    fig, axs = plt.subplots(1, 2, figsize=(11.0, 4.3), sharey=True, gridspec_kw=dict(width_ratios=[1, 1.25]))
    ax = axs[0]
    alphas = (0, 5, 10, 15)
    pitch = {}
    for lab, tags, col in (("dose at 15 deg, 3 runs", ["r15_a{a}", "r15_a{a}_s1", "r15_a{a}_s2"], CAT[1]),
                           ("dose at 30 deg", ["ret_a{a}"], CAT[0])):
        xs, mean, lo, hi = [], [], [], []
        for a in alphas:
            v = [R[t.format(a=a)]["at_exit_final"] * mg for t in tags if t.format(a=a) in R]
            if v:
                xs.append(a)
                mean.append(np.mean(v))
                lo.append(min(v))
                hi.append(max(v))
                pitch[f"{lab} | alpha {a}"] = v
        if xs:
            ax.plot(xs, mean, color=col, lw=2, marker="o", ms=6, label=lab)
            if len(tags) > 1:
                ax.fill_between(xs, lo, hi, color=col, alpha=0.15, lw=0)
    ax.set_xticks(alphas, [f"{a}" for a in alphas])
    ax.set_xlabel("rest pitch, nozzle up (deg)")
    ax.set_ylabel("powder within 15 mm of the exit at the end (proxy mg)")
    ax.set_title("Return only: rest pitch barely matters", fontsize=11, color=INK, loc="left")
    ax.legend(loc="lower left")
    ax = axs[1]
    rev = {}
    for lab, fmt, col, extra_key in (("return, then reverse at rest", "r15retrev_a10_R{x}", CAT[2], None),
                                     ("reverse at 15 deg, then return", "r15revdose_a10_R{x}", CAT[3], "out_reverse_at_dose_tilt")):
        base = R.get("r15_a10")
        if base is None:
            continue
        xs, ys, ex = [0.0], [base["at_exit_final"] * mg], [0]
        for x in (0.25, 0.5, 1, 2):
            t = fmt.format(x=x)
            if t in R:
                xs.append(x)
                ys.append(R[t]["at_exit_final"] * mg)
                ex.append(R[t].get(extra_key, 0) if extra_key else 0)
        ax.plot(xs, ys, color=col, lw=2, marker="o", ms=6, label=lab)
        rev[lab] = dict(R_rev=xs, at_exit_mg=ys, extra_dose_grains=ex)
        if extra_key:
            for x, y, e in zip(xs[1:], ys[1:], ex[1:]):
                ax.annotate(f"+{e * mg:.0f} mg\ninto the vial", (x, y), xytext=(6, 4), textcoords="offset points",
                            fontsize=8.5, color=INK2)
    ax.set_xticks([0, 0.25, 0.5, 1, 2], ["0", "0.25", "0.5", "1", "2"])
    ax.set_xlabel("reverse after the dose (auger revolutions), nozzle up 10 deg")
    ax.set_title("Reversing at rest clears the exit", fontsize=11, color=INK, loc="left")
    ax.legend(loc="upper right")
    ax.set_ylim(0, None)
    fig.suptitle("Paternoster module after a dose: what is left at the outlet for the next start-up dump (proxy)",
                 fontsize=11.5, color=INK, x=0.06, ha="left")
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "exit_powder.png"), dpi=150)
    plt.close(fig)
    res["summary"]["at_exit_vs_rest_pitch_mg"] = pitch
    res["summary"]["at_exit_vs_reverse"] = rev

    # ---- figure 2: v2 lap pumping, cumulative out vs roll angle
    fig, ax = plt.subplots(figsize=(7.6, 4.3))
    v2 = {}
    for tag, lab, col, ls in [("v2_a0_fwd", "today's direction (bottom run toward +y)", CAT[1], "-"),
                              ("v2_a0_fwd_s1", None, CAT[1], "-"),
                              ("v2_a10_fwd", "today's direction, nozzle up 10 deg", CAT[1], "--"),
                              ("v2_a0_rev", "reversed (bottom run toward -y)", CAT[0], "-"),
                              ("v2_a0_rev_s1", None, CAT[0], "-"),
                              ("v2_a10_rev", "reversed, nozzle up 10 deg", CAT[0], "--")]:
        r, z = load(tag)
        if r is None or z is None:
            continue
        L = z["log"]
        sel = L[:, 1] >= 9                     # from the first corner on
        roll = np.degrees(np.abs(L[sel, 3]))
        out = (L[sel, 5] - L[sel, 5][0]) * mg
        ax.plot(roll, out, color=col, ls=ls, lw=2 if lab else 1.2, alpha=1.0 if lab else 0.55, label=lab)
        v2[tag] = dict(direction=r["direction"], alpha_deg=r["alpha_deg"], seed=r.get("seed", 0),
                       out_lap_mg=float(out[-1]), out_by_corner_grains=R[tag]["out_by_corner"],
                       at_exit_start=R[tag]["at_exit_start"], at_exit_end=R[tag]["at_exit_final"])
    for c in (90, 180, 270):
        ax.axvline(c, color=GRID, lw=1, zorder=0)
    ax.set_xlim(0, 365)
    ax.set_xticks([0, 90, 180, 270, 360])
    ax.set_xlabel("module roll during one lap (deg); corners at 0-90, 90-180, 180-270, 270-360")
    ax.set_ylabel("powder pumped out of the outlet (proxy mg)")
    ax.set_title("v2: each lap turns the module once round the auger axis\n(primed auger, motor off; thin lines = a second run)",
                 fontsize=11, color=INK, loc="left")
    ax.legend(loc="upper left")
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "v2_lap_pumping.png"), dpi=150)
    plt.close(fig)
    res["summary"]["v2_lap"] = v2

    # ---- tables for the README
    res["summary"]["paternoster_after_dose"] = {t: {k: R[t].get(k) for k in ("alpha_deg", "dose_tilt_world", "hold_s", "out_return",
                                                                             "out_at_rest", "vial_gain", "at_exit_final")}
                                                for t in sorted(R) if R[t]["kind"] == "branch"}
    res["summary"]["storage"] = {t: R[t] for t in R if R[t]["kind"] == "store"}
    with open(os.path.join(OUT, "leak_results.json"), "w") as f:
        json.dump(res, f, indent=1)
    for t in sorted(R):
        e = R[t]
        print(f"{t:22s} a={e['alpha_deg']:4.0f}", {k: e[k] for k in ("out_return", "out_at_rest", "out_reverse_at_dose_tilt",
                                                                       "vial_gain", "out_lap", "out_taps", "at_exit_final") if k in e})


if __name__ == "__main__":
    main()
