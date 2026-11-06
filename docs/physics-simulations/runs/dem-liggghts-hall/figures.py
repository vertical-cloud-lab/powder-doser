"""Figure + animation + result.json for dem-liggghts-hall (Hall and Carney funnels)."""
import json
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

CASES = [c for c in ("hall", "carney", "hall_coh") if os.path.exists(os.path.join(R.SCRATCH, c, "run.json"))]
LABEL = {"hall": "Hall, 2.54 mm orifice", "carney": "Carney, 5.08 mm orifice", "hall_coh": "Hall, cohesive (SJKR 6 kJ/m³)"}
COL = {"hall": L.COLORS["dry"], "carney": L.COLORS["cap_low"], "hall_coh": L.COLORS["coh"]}


def main():
    res = {c: json.load(open(os.path.join(R.SCRATCH, c, "run.json"))) for c in CASES}
    fig, axs = plt.subplots(1, 2, figsize=(11, 4.0))
    fig.patch.set_facecolor(L.SURF)
    for k, grp in enumerate((["hall", "hall_coh"], ["carney"])):
        ax = axs[k]
        L.style_axes(ax)
        for c in grp:
            if c not in res:
                continue
            A = np.loadtxt(os.path.join(R.SCRATCH, c, "outflow.txt"))
            tt = A[:, 0] - R.T_FILL
            m = A[:, 1] * 1e3
            r = res[c]
            lab = f"{LABEL[c]}: {r['W_g_s']:.2f} g/s" + (" (jammed)" if r["jammed"] else "")
            ax.plot(tt, m, color=COL[c], lw=2, label=lab)
        c0 = grp[0]
        if c0 in res:
            tline = np.linspace(0, R.CASES[c0]["t_dis"], 10)
            for kk, ls in (("k=1.5", ":"), ("k=2.9", "--")):
                ax.plot(tline, res[c0]["beverloo"][kk] * tline, color=L.INK2, lw=1, ls=ls,
                        label=f"Beverloo C=0.58, {kk}: {res[c0]['beverloo'][kk]:.2f} g/s")
        ax.set_xlim(0, None)
        ax.set_ylim(0, None)
        ax.set_xlabel("time after the orifice opens (s)")
        ax.set_ylabel("mass discharged (g)")
        ax.legend(fontsize=7, frameon=False, loc="upper left")
        ax.set_title(("Hall funnel (ASTM B213 geometry, reduced height)" if k == 0 else "Carney funnel (ASTM B964 geometry, reduced height)"), fontsize=9)
    fig.suptitle("dem-liggghts-hall: funnel discharge of salt grains (LIGGGHTS-PUBLIC 3.8)", fontsize=10)
    fig.tight_layout()
    fig.savefig(os.path.join(HERE, "hall.png"), dpi=110, facecolor=L.SURF)
    plt.close(fig)

    anim = [c for c in ("hall", "carney") if c in res]
    series = {c: L.dump_series(os.path.join(R.SCRATCH, c, "dump", "p.*.txt")) for c in anim}
    nfr = min(len(s) for s in series.values())
    frames = []
    cmap = L.speed_cmap()
    for i in range(nfr):
        fig, axs = plt.subplots(1, len(anim), figsize=(7.5, 4.2))
        fig.patch.set_facecolor(L.SURF)
        axs = np.atleast_1d(axs)
        for k, c in enumerate(anim):
            ax = axs[k]
            L.style_axes(ax)
            step, d = L.read_dump(series[c][i])
            m = np.abs(d["y"]) < 0.6e-3
            sp = np.sqrt(d["vx"] ** 2 + d["vy"] ** 2 + d["vz"] ** 2)[m]
            ec = L.draw_grains(ax, d["x"][m] * 1e3, d["z"][m] * 1e3, d["radius"][m] * 1e3, c=sp, cmap=cmap, vmax=0.3)
            cc = R.CASES[c]
            r0 = cc["D0"] / 2 * 1e3
            Hc = res[c]["cone_height_mm"]
            Rt = cc["Rtop"] * 1e3
            zs = [-R.STEM * 1e3, 0, Hc, Hc + cc["Hcyl"] * 1e3]
            rs = [r0, r0, Rt, Rt]
            ax.plot(rs, zs, color=L.INK, lw=1.5)
            ax.plot([-q for q in rs], zs, color=L.INK, lw=1.5)
            t = step * res[c]["dt"] - R.T_FILL
            ax.set_aspect("equal")
            ax.set_xlim(-Rt - 1, Rt + 1)
            ax.set_ylim(-6.5, zs[-1] + 0.5)
            ax.set_xlabel("x (mm)")
            ax.set_ylabel("z (mm)")
            ax.set_title(f"{LABEL[c]}\nt = {t:+.2f} s from opening", fontsize=8)
        cb = fig.colorbar(ec, ax=list(axs), shrink=0.8, pad=0.02)
        cb.set_label("grain speed (m/s)", fontsize=8)
        fig.suptitle("dem-liggghts-hall (LIGGGHTS-PUBLIC 3.8): slice |y|<0.6 mm", fontsize=9)
        frames.append(L.fig_to_array(fig))
        plt.close(fig)
    L.save_animation(frames, os.path.join(HERE, "hall.gif"), os.path.join(HERE, "hall.mp4"), fps=10)
    kr = {c: {"mass_flow_g_s": round(res[c]["W_g_s"], 3), "time_per_50g_s_extrapolated": None if not res[c]["t50_s"] else round(res[c]["t50_s"], 1),
              "jammed_at_end": res[c]["jammed"], "zero_flow_25ms_windows": res[c]["n_windows_zero"],
              "discharged_g": round(res[c]["m_out_total_g"], 3), "orifice_over_mean_d": round(res[c]["D0_over_d"], 2),
              "beverloo_g_s": {k: round(v, 3) for k, v in res[c]["beverloo"].items()},
              "beverloo_rho_b_kg_m3": round(res[c]["beverloo_rho_b"], 0)} for c in CASES}
    out = {"id": "dem-liggghts-hall", "method": "Hall (2.54 mm) and Carney (5.08 mm) 60-degree funnel discharge, reduced funnel height",
           "code": "LIGGGHTS-PUBLIC", "version": "3.8.0 (Debian package liggghts)", "status": "ran",
           "wall_s": {c: round(res[c].get("wall_s", float("nan")), 1) for c in CASES}, "cores": 1,
           "particles": {c: R.CASES[c]["N"] for c in CASES}, "key_results": kr,
           "notes": "Mass flow = linear fit to discharged mass from 0.05 s after opening to the end of the run. Beverloo: "
                    "W = C rho_b sqrt(g) (D0 - k d)^2.5 with C = 0.58, d = 0.425 mm, rho_b from the poured packing fraction of dem-liggghts-tap."}
    L.write_json(os.path.join(HERE, "result.json"), out)
    print(json.dumps(kr, indent=1))


if __name__ == "__main__":
    main()
