"""Figure + animation + result.json for dem-liggghts-spread."""
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

VARS = [v for v in ("dry", "coh", "coh_sub") if os.path.exists(os.path.join(R.SCRATCH, v, "run.json"))]
LABEL = {"dry": "non-cohesive", "coh": "cohesive (SJKR 6 kJ/m³, Bo≈5)", "coh_sub": "cohesive + cohesive plate"}
L.COLORS["coh_sub"] = L.COLORS["cap_low"]


def n_inserted(v):
    import re
    txt = open(os.path.join(R.SCRATCH, v, "screen.txt")).read()
    m = re.findall(r"a total of (\d+) particle templates", txt)
    return int(m[-1]) if m else None


def main():
    res = {v: json.load(open(os.path.join(R.SCRATCH, v, "run.json"))) for v in VARS}
    fig = plt.figure(figsize=(12, 1.6 + 1.6 * len(VARS)))
    fig.patch.set_facecolor(L.SURF)
    gs = fig.add_gridspec(len(VARS), 2, width_ratios=[1, 1.6])
    ax = fig.add_subplot(gs[:, 0])
    L.style_axes(ax)
    for v in VARS:
        b = res[v]["bins"]
        xc = [0.5 * (q["x0_mm"] + q["x1_mm"]) for q in b]
        ax.plot(xc, [q["phi_layer"] for q in b], "o-", color=L.COLORS[v], lw=1.5, ms=4,
                label=f"{LABEL[v]}: φ_layer {res[v]['phi_layer_mean']:.3f}")
        ax.plot(xc, [q["coverage"] for q in b], "s--", color=L.COLORS[v], lw=1, ms=4, mfc="none",
                label=f"{LABEL[v]}: coverage {res[v]['coverage_mean']:.2f}")
    ax.set_ylim(0, 1)
    ax.set_xlabel("position along the plate x (mm)")
    ax.set_ylabel("layer packing fraction (solid) / plate coverage (dashed)")
    ax.legend(fontsize=7, frameon=False, loc="lower left")
    ax.set_title(f"Layer behind a blade at gap {R.GAP * 1e3:.2f} mm, 50 mm/s", fontsize=9, color=L.INK)
    for k, v in enumerate(VARS):
        ax = fig.add_subplot(gs[k, 1])
        L.style_axes(ax)
        _, d = L.read_dump(os.path.join(R.SCRATCH, v, "dump", "final.txt"))
        g = (d["radius"] > 0.15e-3) & (d["z"] < R.GAP)
        L.draw_grains(ax, d["x"][g] * 1e3, (d["y"][g] % R.W) * 1e3, d["radius"][g] * 1e3, color=L.COLORS[v])
        ax.axvspan(R.X_MEAS[0] * 1e3, R.X_MEAS[1] * 1e3, color="#efeee9", lw=0, zorder=0)
        ax.set_xlim(0, 40)
        ax.set_ylim(0, R.W * 1e3)
        ax.set_aspect("equal")
        ax.set_xlabel("x (mm)")
        ax.set_ylabel("y (mm)")
        ax.set_title(f"{LABEL[v]}: top view of layer grains (centre below the gap); grey = measured zone", fontsize=8)
    fig.suptitle("dem-liggghts-spread: blade recoating of salt grains (LIGGGHTS-PUBLIC 3.8)", fontsize=10)
    fig.tight_layout()
    fig.savefig(os.path.join(HERE, "spread.png"), dpi=110, facecolor=L.SURF)
    plt.close(fig)

    series = {v: L.dump_series(os.path.join(R.SCRATCH, v, "dump", "p.*.txt")) for v in VARS}
    nfr = min(len(s) for s in series.values())
    frames = []
    cmap = L.speed_cmap()
    for i in range(0, nfr):
        fig, axs = plt.subplots(len(VARS), 1, figsize=(8, 1.6 + 1.4 * len(VARS)))
        fig.patch.set_facecolor(L.SURF)
        axs = np.atleast_1d(axs)
        for k, v in enumerate(VARS):
            ax = axs[k]
            L.style_axes(ax)
            step, d = L.read_dump(series[v][i])
            g = d["radius"] > 0.15e-3
            sp = np.sqrt(d["vx"] ** 2 + d["vy"] ** 2 + d["vz"] ** 2)
            ec = L.draw_grains(ax, d["x"][g] * 1e3, d["z"][g] * 1e3, d["radius"][g] * 1e3, c=sp[g], cmap=cmap, vmax=0.06)
            b = ~g
            L.draw_grains(ax, d["x"][b] * 1e3, d["z"][b] * 1e3, d["radius"][b] * 1e3, color="#52514e")
            ax.plot([0, 40], [0, 0], color=L.INK, lw=1.5)
            ax.set_xlim(0, 40)
            ax.set_ylim(-0.3, 7)
            ax.set_aspect("equal")
            ax.set_ylabel("z (mm)")
            ax.set_title(f"{LABEL[v]}  t={step * res[v]['dt']:.2f} s (side view, all y)", fontsize=8)
        axs[-1].set_xlabel("x (mm)")
        cb = fig.colorbar(ec, ax=list(axs), shrink=0.8, pad=0.02)
        cb.set_label("grain speed (m/s)", fontsize=8)
        fig.suptitle("dem-liggghts-spread (LIGGGHTS-PUBLIC 3.8): blade (grey) at 50 mm/s", fontsize=9)
        frames.append(L.fig_to_array(fig))
        plt.close(fig)
    L.save_animation(frames, os.path.join(HERE, "spread.gif"), os.path.join(HERE, "spread.mp4"), fps=10)
    kr = {v: {"phi_layer_mean": round(res[v]["phi_layer_mean"], 3), "phi_layer_std_between_bins": round(res[v]["phi_layer_std"], 3),
              "coverage_mean": round(res[v]["coverage_mean"], 3), "coverage_min_bin": round(res[v]["coverage_min"], 3),
              "mass_per_area_cv": None if res[v]["mass_per_area_cv"] is None else round(res[v]["mass_per_area_cv"], 3)} for v in VARS}
    out = {"id": "dem-liggghts-spread", "method": "blade recoating, gap 2.5 mean diameters (1.06 mm), 50 mm/s, y-periodic 4.25 mm slice",
           "code": "LIGGGHTS-PUBLIC", "version": "3.8.0 (Debian package liggghts)", "status": "ran",
           "wall_s": {v: round(res[v].get("wall_s", float("nan")), 1) for v in VARS}, "cores": 1,
           "particles": {"grains": n_inserted(VARS[0]), "blade_spheres": res[VARS[0]]["n_blade"]}, "key_results": kr,
           "notes": "Measured over x = 12-32 mm in 2 mm bins. Layer packing fraction = grain volume inside 0<z<gap / (bin area x gap). "
                    "Coverage = projected area of grains whose centre is below the gap / bin area."}
    L.write_json(os.path.join(HERE, "result.json"), out)
    print(json.dumps(kr, indent=1))


if __name__ == "__main__":
    main()
