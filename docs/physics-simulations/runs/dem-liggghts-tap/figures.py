"""Figure + animation + result.json for dem-liggghts-tap."""
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

VARS = [v for v in ("dry", "coh") if os.path.exists(os.path.join(R.SCRATCH, v, "run.json"))]
LABEL = {"dry": "non-cohesive", "coh": "cohesive (SJKR 6 kJ/m³, Bo≈5)"}


def main():
    res = {v: json.load(open(os.path.join(R.SCRATCH, v, "run.json"))) for v in VARS}
    fig, axs = plt.subplots(1, 3, figsize=(12, 3.8), gridspec_kw=dict(width_ratios=[1.3, 1, 1]))
    fig.patch.set_facecolor(L.SURF)
    ax = axs[0]
    L.style_axes(ax)
    for v in VARS:
        r = res[v]
        phis = [r["poured"]["phi_slab"]] + [t["phi_slab"] for t in r["taps"]]
        ax.plot(range(len(phis)), phis, "o-", color=L.COLORS[v], ms=4, lw=1.5,
                label=f"{LABEL[v]}: Hausner {r.get('hausner', float('nan')):.3f}")
    ax.set_xlabel("number of 3 mm taps (0 = as poured)")
    ax.set_ylabel("packing fraction φ (slab, no walls)")
    ax.legend(fontsize=7.5, frameon=False, loc="lower right")
    ax.set_title("Poured → tapped packing fraction", fontsize=9, color=L.INK)
    for k, v in enumerate(VARS):
        ax = axs[k + 1]
        L.style_axes(ax)
        for j, (name, off) in enumerate((("poured.txt", 0.0), (f"tap_{R.NTAP}.txt", 6.0))):
            f = os.path.join(R.SCRATCH, v, "dump", name)
            if not os.path.exists(f):
                continue
            _, d = L.read_dump(f)
            m = (d["y"] % R.LY) < 1.2e-3
            L.draw_grains(ax, (d["x"][m] % R.LX) * 1e3 + off, d["z"][m] * 1e3, d["radius"][m] * 1e3, color=L.COLORS[v])
            ax.text(off + 2.55, -0.9, "poured" if j == 0 else f"after {R.NTAP} taps", ha="center", fontsize=8, color=L.INK2)
        ax.plot([-0.3, 11.4], [0, 0], color=L.INK, lw=2)
        ax.set_xlim(-0.5, 11.6)
        ax.set_ylim(-1.5, 8)
        ax.set_aspect("equal")
        ax.set_xlabel("x (mm), periodic cell 5.1 mm (two copies side by side)")
        ax.set_ylabel("z (mm)")
        ax.set_title(f"{LABEL[v]}: slice 0<y<1.2 mm", fontsize=9, color=L.INK)
    fig.suptitle("dem-liggghts-tap: apparent and tapped density of salt grains (LIGGGHTS-PUBLIC 3.8)", fontsize=10)
    fig.tight_layout()
    fig.savefig(os.path.join(HERE, "tap.png"), dpi=110, facecolor=L.SURF)
    plt.close(fig)

    series = {v: L.dump_series(os.path.join(R.SCRATCH, v, "dump", "p.*.txt")) for v in VARS}
    nfr = min(len(s) for s in series.values())
    frames = []
    cmap = L.speed_cmap()
    for i in range(0, min(nfr, 120), 2):
        fig, axs = plt.subplots(1, len(VARS), figsize=(6.4, 4.0))
        fig.patch.set_facecolor(L.SURF)
        axs = np.atleast_1d(axs)
        for k, v in enumerate(VARS):
            ax = axs[k]
            L.style_axes(ax)
            step, d = L.read_dump(series[v][i])
            m = (d["y"] % R.LY) < 1.2e-3
            sp = np.sqrt(d["vx"] ** 2 + d["vy"] ** 2 + d["vz"] ** 2)[m]
            ec = L.draw_grains(ax, (d["x"][m] % R.LX) * 1e3, d["z"][m] * 1e3, d["radius"][m] * 1e3, c=sp, cmap=cmap, vmax=0.3)
            ax.plot([0, R.LX * 1e3], [0, 0], color=L.INK, lw=2)
            ax.set_xlim(0, R.LX * 1e3)
            ax.set_ylim(-0.3, 10)
            ax.set_aspect("equal")
            ax.set_xlabel("x (mm)")
            ax.set_ylabel("z (mm)")
            ax.set_title(f"{LABEL[v].split(' (')[0]}  t={step * res[v]['dt']:.2f} s", fontsize=8)
        cb = fig.colorbar(ec, ax=list(axs), shrink=0.8, pad=0.03)
        cb.set_label("grain speed (m/s)", fontsize=8)
        fig.suptitle("dem-liggghts-tap (LIGGGHTS-PUBLIC 3.8): 3 mm taps", fontsize=9)
        frames.append(L.fig_to_array(fig))
        plt.close(fig)
    L.save_animation(frames, os.path.join(HERE, "tap.gif"), os.path.join(HERE, "tap.mp4"), fps=12)

    kr = {v: {"phi_bulk_poured": round(res[v]["phi_bulk"], 4), "phi_tapped_mean_last5": round(res[v]["phi_tapped_last5"], 4),
              "taps": len(res[v]["taps"]), "hausner": round(res[v]["hausner"], 3), "carr_index_pct": round(res[v]["carr_index_pct"], 1),
              "bulk_density_kg_m3": round(res[v]["phi_bulk"] * L.SALT["density"], 0),
              "tapped_density_kg_m3": round(res[v]["phi_tapped_last5"] * L.SALT["density"], 0),
              "hausner_from_whole_bed": round(res[v]["hausner_overall"], 3)} for v in VARS}
    out = {"id": "dem-liggghts-tap", "method": "poured (apparent) and tapped density, laterally periodic column, 3 mm taps",
           "code": "LIGGGHTS-PUBLIC", "version": "3.8.0 (Debian package liggghts)", "status": "ran",
           "wall_s": {v: round(res[v].get("wall_s", float("nan")), 1) for v in VARS}, "cores": 1,
           "particles": R.N, "key_results": kr,
           "notes": f"{R.NTAP} taps only (ASTM B527 uses up to 3000); the tapped value is the mean of the last 5 taps. "
                    "Packing fraction in a slab 1 mm above the floor to 1 mm below the free surface; no side walls (periodic)."}
    L.write_json(os.path.join(HERE, "result.json"), out)
    print(json.dumps(kr, indent=1))


if __name__ == "__main__":
    main()
