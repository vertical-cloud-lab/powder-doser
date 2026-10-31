"""Figure + animation + result.json for dem-liggghts-drum."""
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
    fig, axs = plt.subplots(1, 1 + len(VARS), figsize=(12, 3.9), gridspec_kw=dict(width_ratios=[1.3] + [1] * len(VARS)))
    fig.patch.set_facecolor(L.SURF)
    ax = axs[0]
    L.style_axes(ax)
    for v in VARS:
        r = res[v]
        t = np.array(r["t_rot"])
        a = np.array([np.nan if q is None else q for q in r["angle_deg"]])
        m = t >= 0
        ax.plot(t[m], a[m], "-", color=L.COLORS[v], lw=1.5,
                label=f"{LABEL[v]}: {r['dyn_angle_mean_deg']:.1f}° ± {r['dyn_angle_std_deg']:.1f}°")
    ax.axvspan(R.T_AVG0, R.T_ROT, color="#efeee9", lw=0, zorder=0)
    ax.set_xlabel(f"time since rotation started (s), {R.RPM:.0f} rpm")
    ax.set_ylabel("free-surface angle (deg)")
    ax.set_ylim(0, None)
    ax.legend(fontsize=7.5, frameon=False, loc="lower right")
    ax.set_title("Dynamic angle of repose (grey: averaging window)", fontsize=9)
    for k, v in enumerate(VARS):
        ax = axs[k + 1]
        L.style_axes(ax)
        files = L.dump_series(os.path.join(R.SCRATCH, v, "dump", "p.*.txt"))
        step, d = L.read_dump(files[-1])
        g = d["radius"] > 0.16e-3
        sp = np.sqrt(d["vx"] ** 2 + d["vy"] ** 2 + d["vz"] ** 2)
        ec = L.draw_grains(ax, d["x"][g] * 1e3, d["z"][g] * 1e3, d["radius"][g] * 1e3, c=sp[g], cmap=L.speed_cmap(), vmax=0.05)
        th = np.linspace(0, 2 * math.pi, 200)
        ax.plot(R.R * 1e3 * np.cos(th), R.R * 1e3 * np.sin(th), color=L.INK, lw=1.5)
        ax.set_aspect("equal")
        ax.set_xlim(-8.8, 8.8)
        ax.set_ylim(-8.8, 8.8)
        ax.set_xlabel("x (mm)")
        ax.set_ylabel("z (mm)")
        ax.set_title(f"{LABEL[v]}: end of run (all y)", fontsize=9)
    cb = fig.colorbar(ec, ax=list(axs[1:]), shrink=0.85, pad=0.02)
    cb.set_label("grain speed (m/s)", fontsize=8)
    fig.suptitle(f"dem-liggghts-drum: 16 mm rotating drum, {R.RPM:.0f} rpm, salt grains (LIGGGHTS-PUBLIC 3.8)", fontsize=10)
    fig.savefig(os.path.join(HERE, "drum.png"), dpi=110, facecolor=L.SURF, bbox_inches="tight")
    plt.close(fig)

    series = {v: L.dump_series(os.path.join(R.SCRATCH, v, "dump", "p.*.txt")) for v in VARS}
    nfr = min(len(s) for s in series.values())
    frames = []
    for i in range(0, nfr):
        fig, axs = plt.subplots(1, len(VARS), figsize=(7.2, 3.8))
        fig.patch.set_facecolor(L.SURF)
        axs = np.atleast_1d(axs)
        for k, v in enumerate(VARS):
            ax = axs[k]
            L.style_axes(ax)
            step, d = L.read_dump(series[v][i])
            g = d["radius"] > 0.16e-3
            sp = np.sqrt(d["vx"] ** 2 + d["vy"] ** 2 + d["vz"] ** 2)
            ec = L.draw_grains(ax, d["x"][g] * 1e3, d["z"][g] * 1e3, d["radius"][g] * 1e3, c=sp[g], cmap=L.speed_cmap(), vmax=0.05)
            w = ~g
            L.draw_grains(ax, d["x"][w] * 1e3, d["z"][w] * 1e3, d["radius"][w] * 1e3, color="#52514e")
            ax.set_aspect("equal")
            ax.set_xlim(-8.8, 8.8)
            ax.set_ylim(-8.8, 8.8)
            ax.set_xlabel("x (mm)")
            ax.set_ylabel("z (mm)")
            ax.set_title(f"{LABEL[v].split(' (')[0]}  t = {step * res[v]['dt'] - R.T_FILL:+.2f} s", fontsize=8)
        cb = fig.colorbar(ec, ax=list(axs), shrink=0.8, pad=0.02)
        cb.set_label("grain speed (m/s)", fontsize=8)
        fig.suptitle(f"dem-liggghts-drum (LIGGGHTS-PUBLIC 3.8): {R.RPM:.0f} rpm, rough wall of glued spheres", fontsize=9)
        frames.append(L.fig_to_array(fig))
        plt.close(fig)
    L.save_animation(frames, os.path.join(HERE, "drum.gif"), os.path.join(HERE, "drum.mp4"), fps=10)
    def extrema(v):
        t = np.array(res[v]["t_rot"])
        a = np.array([np.nan if q is None else q for q in res[v]["angle_deg"]])
        m = t > R.T_AVG0 - 0.1
        t, a = t[m], a[m]
        mx = [a[i] for i in range(1, len(a) - 1) if a[i] >= a[i - 1] and a[i] > a[i + 1] and t[i] >= R.T_AVG0]
        mn = [a[i] for i in range(1, len(a) - 1) if a[i] <= a[i - 1] and a[i] < a[i + 1] and t[i] >= R.T_AVG0]
        return mx, mn
    kr = {}
    for v in VARS:
        mx, mn = extrema(v)
        kr[v] = {"dynamic_angle_mean_deg": round(res[v]["dyn_angle_mean_deg"], 1), "dynamic_angle_std_deg": round(res[v]["dyn_angle_std_deg"], 1),
                 "averaging_window_s": [R.T_AVG0, R.T_ROT],
                 "local_max_angles_deg": [round(float(x), 1) for x in mx], "local_min_angles_deg": [round(float(x), 1) for x in mn]}
    out = {"id": "dem-liggghts-drum", "method": "rotating drum, 16 mm diameter, 2.55 mm periodic slice, 20 rpm (Froude 0.0036)",
           "code": "LIGGGHTS-PUBLIC", "version": "3.8.0 (Debian package liggghts)", "status": "ran",
           "wall_s": {v: round(res[v].get("wall_s", float("nan")), 1) for v in VARS}, "cores": 1,
           "particles": {"grains": R.N, "wall_spheres": res[VARS[0]]["n_wall_spheres"]}, "key_results": kr,
           "notes": "Angle = slope of a line fitted to the top of the bed over the central 60 % of the drum width, per 0.02 s dump, "
                    "averaged over the window. Rough wall: frozen 0.3 mm spheres rotated with fix move rotate."}
    L.write_json(os.path.join(HERE, "result.json"), out)
    print(json.dumps(kr, indent=1))


if __name__ == "__main__":
    main()
