"""Figure + animation + result.json for dem-liggghts-capillary (AoR with liquid bridges).

Uses the AoR runs in /tmp/sims-scratch/dem-liggghts-aor/{dry,cap_low,cap_high}.
"""
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

VARS = [v for v in ("dry", "cap_low", "cap_high") if os.path.exists(os.path.join(R.SCRATCH, v, "run.json"))]
LABEL = {"dry": "dry", "cap_low": f"liquid {R.CAP['cap_low']} (surfaceLiquidContentInitial)",
         "cap_high": f"liquid {R.CAP['cap_high']} (surfaceLiquidContentInitial)"}


def slice_xz(d, half=0.6e-3):
    m = np.abs(d["y"]) < half
    return d["x"][m], d["z"][m], d["radius"][m], np.sqrt(d["vx"][m] ** 2 + d["vy"][m] ** 2 + d["vz"][m] ** 2)


def main():
    res = {v: json.load(open(os.path.join(R.SCRATCH, v, "run.json"))) for v in VARS}
    fig, axs = plt.subplots(1, len(VARS) + 1, figsize=(4 * (len(VARS) + 1), 3.6))
    fig.patch.set_facecolor(L.SURF)
    ax = axs[0]
    L.style_axes(ax)
    for v in VARS:
        r = res[v]
        ax.errorbar(r["r_mm"], r["h_mm"], yerr=r["h_std_mm"], fmt="o", ms=4, color=L.COLORS[v], lw=1,
                    label=f"{LABEL[v].split(' (')[0]}: fit {r['angle_fit_deg']:.1f}°, apex {r['angle_iso_deg']:.1f}°")
        p = r["fit"]
        xx = np.linspace(1.0, 5.2, 10)
        ax.plot(xx, (p[0] * xx * 1e-3 + p[1]) * 1e3, color=L.COLORS[v], lw=2)
    ax.set_xlabel("radius from heap axis r (mm)")
    ax.set_ylabel("heap surface height h (mm)")
    ax.set_xlim(0, 6.2)
    ax.set_ylim(0, None)
    ax.legend(fontsize=7, frameon=False, loc="lower left")
    ax.set_title("Heap profiles, 12 mm base", fontsize=9)
    for k, v in enumerate(VARS):
        ax = axs[k + 1]
        L.style_axes(ax)
        files = L.dump_series(os.path.join(R.SCRATCH, v, "dump", "p.*.txt"))
        _, d = L.read_dump(files[-1])
        x, z, r, s = slice_xz(d)
        L.draw_grains(ax, x * 1e3, z * 1e3, r * 1e3, color=L.COLORS[v])
        ax.plot([-6, 6], [0, 0], color=L.INK, lw=2)
        ax.set_xlim(-8, 8)
        ax.set_ylim(-0.5, 12)
        ax.set_aspect("equal")
        ax.set_xlabel("x (mm)")
        ax.set_ylabel("z (mm)")
        ax.set_title(f"{LABEL[v]}", fontsize=8)
    fig.suptitle("dem-liggghts-capillary: angle of repose with liquid bridges (easo/capillary/viscous, LIGGGHTS-PUBLIC 3.8)", fontsize=10)
    fig.tight_layout()
    fig.savefig(os.path.join(HERE, "capillary.png"), dpi=110, facecolor=L.SURF)
    plt.close(fig)

    an = [v for v in ("cap_low", "cap_high") if v in res]
    series = {v: L.dump_series(os.path.join(R.SCRATCH, v, "dump", "p.*.txt")) for v in an}
    frames = []
    if an:
        nfr = min(len(s) for s in series.values())
        cmap = L.speed_cmap()
        for i in range(nfr):
            fig, axs = plt.subplots(1, len(an), figsize=(8, 3.3))
            fig.patch.set_facecolor(L.SURF)
            axs = np.atleast_1d(axs)
            for k, v in enumerate(an):
                ax = axs[k]
                L.style_axes(ax)
                step, d = L.read_dump(series[v][i])
                x, z, r, s = slice_xz(d)
                ec = L.draw_grains(ax, x * 1e3, z * 1e3, r * 1e3, c=s, cmap=cmap, vmax=0.4)
                ax.plot([-6, 6], [0, 0], color=L.INK, lw=2)
                ax.set_xlim(-8, 8)
                ax.set_ylim(-0.5, 14.5)
                ax.set_aspect("equal")
                ax.set_xlabel("x (mm)")
                ax.set_ylabel("z (mm)")
                ax.set_title(f"{LABEL[v].split(' (')[0]}  t = {step * res[v]['dt']:.2f} s", fontsize=8)
            if ec is not None:
                cb = fig.colorbar(ec, ax=list(axs), shrink=0.8, pad=0.02)
                cb.set_label("grain speed (m/s)", fontsize=8)
            fig.suptitle("dem-liggghts-capillary (LIGGGHTS-PUBLIC 3.8): wet pour, slice |y|<0.6 mm", fontsize=9)
            frames.append(L.fig_to_array(fig))
            plt.close(fig)
        L.save_animation(frames, os.path.join(HERE, "capillary.gif"), os.path.join(HERE, "capillary.mp4"), fps=10)
    status = "ran" if all(v in res for v in ("dry", "cap_low", "cap_high")) else ("partial" if len(res) > 1 else "failed")
    out = {"id": "dem-liggghts-capillary", "method": "angle of repose (dem-liggghts-aor setup) with liquid-bridge cohesion, dry vs two liquid contents",
           "code": "LIGGGHTS-PUBLIC", "version": "3.8.0 (Debian package liggghts), cohesion model easo/capillary/viscous",
           "status": status, "wall_s": {v: round(res[v].get("wall_s", float("nan")), 1) for v in VARS}, "cores": 1,
           "particles": {v: {"poured": res[v]["n_poured"], "on_base_at_end": res[v]["n_on_base"]} for v in VARS},
           "key_results": {v: {"surfaceLiquidContentInitial": (0.0 if v == "dry" else R.CAP[v]),
                               "repose_angle_profile_fit_deg": round(res[v]["angle_fit_deg"], 1),
                               "repose_angle_sector_std_deg": round(res[v]["angle_fit_sector_std_deg"], 1),
                               "repose_angle_apex_iso_deg": round(res[v]["angle_iso_deg"], 1),
                               "apex_height_mm": round(res[v]["apex_height_mm"], 2)} for v in VARS},
           "notes": "Dry baseline = the dry run of dem-liggghts-aor (identical setup). Liquid: surface tension 0.072 N/m, viscosity 1 mPa s, "
                    "contact angle 20 deg, bridge rupture at 1.1 x contact distance (maxSeparationDistanceRatio), min separation ratio 1.01; "
                    "grain-wall contacts dry."}
    L.write_json(os.path.join(HERE, "result.json"), out)
    print(json.dumps(out["key_results"], indent=1))


if __name__ == "__main__":
    main()
