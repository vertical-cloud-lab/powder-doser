"""Figure + animation + result.json for dem-liggghts-aor (reads the scratch run folders)."""
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


def slice_xz(d, half=0.6e-3):
    m = np.abs(d["y"]) < half
    return d["x"][m], d["z"][m], d["radius"][m], np.sqrt(d["vx"][m] ** 2 + d["vy"][m] ** 2 + d["vz"][m] ** 2)


def main():
    res = {v: json.load(open(os.path.join(R.SCRATCH, v, "run.json"))) for v in VARS}
    fig, axs = plt.subplots(1, 3, figsize=(12, 3.6), gridspec_kw=dict(width_ratios=[1.1, 1, 1]))
    fig.patch.set_facecolor(L.SURF)
    ax = axs[0]
    L.style_axes(ax)
    for v in VARS:
        r = res[v]
        rr = np.array(r["r_mm"])
        ax.errorbar(rr, r["h_mm"], yerr=r["h_std_mm"], fmt="o", ms=4, color=L.COLORS[v], lw=1, capsize=0,
                    label=f"{LABEL[v]}: fit {r['angle_fit_deg']:.1f}°, apex {r['angle_iso_deg']:.1f}°")
        p = r["fit"]
        xx = np.linspace(1.0, 5.2, 10)
        ax.plot(xx, (p[0] * xx * 1e-3 + p[1]) * 1e3, color=L.COLORS[v], lw=2)
    ax.set_xlabel("radius from heap axis r (mm)")
    ax.set_ylabel("heap surface height h (mm)")
    ax.set_xlim(0, 6.2)
    ax.set_ylim(0, None)
    ax.legend(fontsize=7, frameon=False, loc="lower left")
    ax.set_title("Heap profile on a 12 mm base", fontsize=9, color=L.INK)
    for k, v in enumerate(VARS):
        ax = axs[k + 1]
        L.style_axes(ax)
        files = L.dump_series(os.path.join(R.SCRATCH, v, "dump", "p.*.txt"))
        _, d = L.read_dump(files[-1])
        x, z, r, s = slice_xz(d)
        L.draw_grains(ax, x * 1e3, z * 1e3, r * 1e3, color=L.COLORS[v])
        ax.plot([-6, 6], [0, 0], color=L.INK, lw=2)
        ax.set_xlim(-8, 8)
        ax.set_ylim(-0.5, 9)
        ax.set_aspect("equal")
        ax.set_xlabel("x (mm)")
        ax.set_ylabel("z (mm)")
        ax.set_title(f"{LABEL[v]}: final heap, slice |y| < 0.6 mm", fontsize=9, color=L.INK)
    fig.suptitle("dem-liggghts-aor: poured angle of repose of salt grains (LIGGGHTS-PUBLIC 3.8)", fontsize=10, color=L.INK)
    fig.tight_layout()
    fig.savefig(os.path.join(HERE, "aor.png"), dpi=110, facecolor=L.SURF)
    plt.close(fig)

    # animation: both variants side by side
    series = {v: L.dump_series(os.path.join(R.SCRATCH, v, "dump", "p.*.txt")) for v in VARS}
    nfr = min(len(s) for s in series.values())
    frames = []
    cmap = L.speed_cmap()
    for i in range(nfr):
        fig, axs = plt.subplots(1, len(VARS), figsize=(8, 3.3))
        fig.patch.set_facecolor(L.SURF)
        for k, v in enumerate(VARS):
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
            ax.set_title(f"{LABEL[v]}  t = {step * res[v]['dt']:.2f} s", fontsize=8, color=L.INK)
        if ec is not None:
            cb = fig.colorbar(ec, ax=axs, shrink=0.8, pad=0.02)
            cb.set_label("grain speed (m/s)", fontsize=8)
        fig.suptitle("dem-liggghts-aor (LIGGGHTS-PUBLIC 3.8): pouring onto a 12 mm base, slice |y|<0.6 mm", fontsize=9)
        frames.append(L.fig_to_array(fig))
        plt.close(fig)
    L.save_animation(frames, os.path.join(HERE, "aor.gif"), os.path.join(HERE, "aor.mp4"), fps=10)

    out = {
        "id": "dem-liggghts-aor", "method": "angle of repose, poured heap on a fixed 12 mm base (ISO 4324 style, reduced scale)",
        "code": "LIGGGHTS-PUBLIC", "version": "3.8.0 (Debian package liggghts, compiled 2024-03-31)",
        "status": "ran", "wall_s": {v: round(res[v].get("wall_s", float("nan")), 1) for v in VARS}, "cores": 1,
        "particles": {v: {"poured": res[v]["n_poured"], "on_base_at_end": res[v]["n_on_base"]} for v in VARS},
        "key_results": {v: {"repose_angle_profile_fit_deg": round(res[v]["angle_fit_deg"], 1),
                            "repose_angle_sector_std_deg": round(res[v]["angle_fit_sector_std_deg"], 1),
                            "repose_angle_apex_iso_deg": round(res[v]["angle_iso_deg"], 1),
                            "apex_height_mm": round(res[v]["apex_height_mm"], 2)} for v in VARS},
        "notes": "Real-size salt grains (no coarse-graining), E reduced to 2e5 Pa. Profile-fit angle = slope of the "
                 "sector-averaged heap surface for 1.0 < r < 5.2 mm; apex angle = atan(apex height / base radius) as in ISO 4324.",
    }
    L.write_json(os.path.join(HERE, "result.json"), out)
    print(json.dumps(out["key_results"], indent=1))


if __name__ == "__main__":
    main()
