"""Figure + animation + result.json for dem-liggghts-shear."""
import json
import math
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import ligcommon as L  # noqa: E402
import run as R  # noqa: E402

VARS = [v for v in ("dry", "coh") if os.path.exists(os.path.join(R.SCRATCH, v, "run.json"))]
LABEL = {"dry": "non-cohesive", "coh": "cohesive (SJKR 6 kJ/m³, Bo≈5)"}


def main():
    res = {v: json.load(open(os.path.join(R.SCRATCH, v, "run.json"))) for v in VARS}
    sched = json.load(open(os.path.join(R.SCRATCH, VARS[0], "schedule.json")))
    fig, axs = plt.subplots(1, 2, figsize=(12, 4.2), gridspec_kw=dict(width_ratios=[1.5, 1]))
    fig.patch.set_facecolor(L.SURF)
    ax = axs[0]
    L.style_axes(ax)
    for p in sched:
        if p["name"].startswith("shear"):
            ax.axvspan(p["t0"], p["t1"], color="#efeee9", lw=0)
            ax.text(0.5 * (p["t0"] + p["t1"]), 2, f"σ={p['sigma']:.0f} Pa", ha="center", fontsize=7, color=L.INK2)
        if p["name"].startswith("preshear"):
            ax.text(0.5 * (p["t0"] + p["t1"]), 2, "pre-shear\n200 Pa", ha="center", fontsize=7, color=L.INK2)
    for v in VARS:
        A = np.loadtxt(os.path.join(R.SCRATCH, v, "stress.txt"), skiprows=1)
        t, tau = A[:, 0], A[:, 1]
        k = np.ones(9) / 9
        ax.plot(t, np.convolve(tau, k, mode="same"), color=L.COLORS[v], lw=1.2, label=LABEL[v])
        for q in res[v]["points"]:
            pass
    ax.set_xlim(0.3, sched[-1]["t1"])
    ax.set_ylim(0, None)
    ax.set_xlabel("time (s)  [shear at 10 mm/s; grey = shear-to-failure steps]")
    ax.set_ylabel("shear stress on the bottom wall τ (Pa)")
    ax.legend(fontsize=8, frameon=False, loc="upper center", bbox_to_anchor=(0.5, -0.16), ncol=2)
    ax.set_title("Shear stress history (9-sample running mean)", fontsize=9, color=L.INK)

    ax = axs[1]
    L.style_axes(ax)
    smax = 0
    for v in VARS:
        r = res[v]
        s = np.array([q["sigma_meas_at_peak"] for q in r["points"]])
        tp = np.array([q["tau_peak"] for q in r["points"]])
        yl = r["yield_locus"]
        mo = r["mohr"]
        ax.plot(s, tp, "o", color=L.COLORS[v], ms=6, label=f"{LABEL[v]}: c={yl['cohesion_Pa']:.1f} Pa, φ={yl['phi_i_deg']:.1f}°, ffc={mo['ffc']:.1f}" if mo["ffc"] else LABEL[v])
        sp, tpre = r["preshear_point"]["sigma_Pa"], r["preshear_point"]["tau_Pa"]
        ax.plot([sp], [tpre], "s", color=L.COLORS[v], ms=6, mfc="none", mew=1.5)
        xx = np.linspace(0, max(mo["sigma_1_Pa"] if np.isfinite(mo["sigma_1_Pa"]) else sp, sp) * 1.02, 50)
        ax.plot(xx, yl["cohesion_Pa"] + yl["tan_phi"] * xx, color=L.COLORS[v], lw=1.5)
        th = np.linspace(0, math.pi, 100)
        if mo["sigma_c_Pa"] > 0:
            rc = mo["sigma_c_Pa"] / 2
            ax.plot(rc + rc * np.cos(th), rc * np.sin(th), color=L.COLORS[v], lw=1, ls="--")
        if np.isfinite(mo["centre_Pa"]):
            ax.plot(mo["centre_Pa"] + mo["radius_Pa"] * np.cos(th), mo["radius_Pa"] * np.sin(th), color=L.COLORS[v], lw=1, ls=":")
        smax = max(smax, mo["sigma_1_Pa"] if np.isfinite(mo["sigma_1_Pa"]) else sp)
    ax.set_xlim(0, smax * 1.05)
    ax.set_ylim(0, None)
    ax.set_aspect("equal")
    ax.set_xlabel("normal stress σ (Pa)")
    ax.set_ylabel("shear stress τ (Pa)")
    ax.legend(fontsize=7, frameon=False, loc="upper left")
    ax.set_title("Yield loci (dots: peaks; squares: pre-shear), Mohr circles", fontsize=9, color=L.INK)
    fig.suptitle("dem-liggghts-shear: plane (unrolled ring) shear cell, salt grains, LIGGGHTS-PUBLIC 3.8", fontsize=10)
    fig.tight_layout()
    fig.savefig(os.path.join(HERE, "shear.png"), dpi=110, facecolor=L.SURF)
    plt.close(fig)

    # animation: x-z projection coloured by vx / V_shear
    series = {v: L.dump_series(os.path.join(R.SCRATCH, v, "dump", "p.*.txt")) for v in VARS}
    nfr = min(len(s) for s in series.values())
    idx = list(range(25, nfr, 3))
    frames = []
    cmap = L.speed_cmap()
    for i in idx:
        fig, axs = plt.subplots(1, len(VARS), figsize=(8, 3.2))
        fig.patch.set_facecolor(L.SURF)
        axs = np.atleast_1d(axs)
        for k, v in enumerate(VARS):
            ax = axs[k]
            L.style_axes(ax)
            step, d = L.read_dump(series[v][i])
            m = d["y"] < 1.0e-3
            ec = L.draw_grains(ax, d["x"][m] * 1e3, d["z"][m] * 1e3, d["radius"][m] * 1e3,
                               c=np.clip(d["vx"][m] / R.V_SHEAR, 0, 1), cmap=cmap, vmax=1.0)
            t = step * res[v]["dt"]
            ph = [p for p in sched if p["t0"] <= t < p["t1"]]
            ax.set_xlim(0, R.LX * 1e3)
            ax.set_ylim(0, 8)
            ax.set_aspect("equal")
            ax.set_xlabel("x (mm), periodic")
            ax.set_ylabel("z (mm)")
            ax.set_title(f"{LABEL[v]}  t={t:.2f} s  {ph[0]['name'] if ph else ''}", fontsize=7)
        cb = fig.colorbar(ec, ax=list(axs), shrink=0.8, pad=0.02)
        cb.set_label("v_x / v_lid", fontsize=8)
        fig.suptitle("dem-liggghts-shear (LIGGGHTS-PUBLIC 3.8): slice 0<y<1 mm, lid moves +x", fontsize=9)
        frames.append(L.fig_to_array(fig))
        plt.close(fig)
    L.save_animation(frames, os.path.join(HERE, "shear.gif"), os.path.join(HERE, "shear.mp4"), fps=12)

    kr = {}
    for v in VARS:
        r = res[v]
        kr[v] = {"cohesion_Pa": round(r["yield_locus"]["cohesion_Pa"], 2), "phi_i_deg": round(r["yield_locus"]["phi_i_deg"], 1),
                 "preshear_sigma_Pa": round(r["preshear_point"]["sigma_Pa"], 1), "preshear_tau_Pa": round(r["preshear_point"]["tau_Pa"], 1),
                 "sigma_c_Pa": round(r["mohr"]["sigma_c_Pa"], 1), "sigma_1_Pa": round(r["mohr"]["sigma_1_Pa"], 1),
                 "ffc": None if r["mohr"]["ffc"] is None else round(r["mohr"]["ffc"], 1),
                 "points_sigma_tau_peak_Pa": [[round(q["sigma_meas_at_peak"], 1), round(q["tau_peak"], 1)] for q in r["points"]]}
    out = {"id": "dem-liggghts-shear", "method": "plane (unrolled Schulze ring) shear cell: pre-shear at 200 Pa, shear to failure at 50/100/150 Pa",
           "code": "LIGGGHTS-PUBLIC", "version": "3.8.0 (Debian package liggghts)", "status": "ran",
           "wall_s": {v: round(res[v].get("wall_s", float("nan")), 1) for v in VARS}, "cores": 1,
           "particles": {"grains": R.N_BULK, "wall_grains": 2 * R.NX * R.NY},
           "key_results": kr,
           "notes": "Real-size salt, E = 2e5 Pa, so normal stresses are kept at 50-200 Pa (overlaps < ~3 % of d); this is the "
                    "stress range of a few mm to cm of powder head, i.e. the doser's, far below FT4/Schulze test stresses (kPa). "
                    "Gravity off during shearing. ffc from Mohr circles on a straight yield locus through the three peak points."}
    L.write_json(os.path.join(HERE, "result.json"), out)
    print(json.dumps(kr, indent=1))


if __name__ == "__main__":
    main()
