"""Figure + animation + result.json for dem-liggghts-auger-short (reads the scratch case folders)."""
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

SCRATCH = os.environ.get("SCRATCH", "/tmp/sims-scratch/dem-liggghts-auger-short")
CASES = {"dry": "auger_short_dry", "coh": "auger_short_coh"}
LABEL = {"dry": "non-cohesive", "coh": "cohesive (SJKR 6 kJ/m³, Bo≈5)"}
T_SETTLE = 0.12
PERIOD = 1.0


def load(v):
    wd = os.path.join(SCRATCH, CASES[v])
    A = np.loadtxt(os.path.join(wd, "outflow.txt"))
    meta = json.load(open(os.path.join(wd, "case.json")))
    return wd, A, meta


def main():
    have = {v: os.path.exists(os.path.join(SCRATCH, CASES[v], "outflow.txt")) for v in CASES}
    data = {v: load(v) for v in CASES if have[v]}
    fig, axs = plt.subplots(1, 2, figsize=(11, 4.0), gridspec_kw=dict(width_ratios=[1.2, 1]))
    fig.patch.set_facecolor(L.SURF)
    ax = axs[0]
    L.style_axes(ax)
    kr = {}
    for v, (wd, A, meta) in data.items():
        t, m = A[:, 0], A[:, 1] * 1e6
        rot = (t - T_SETTLE) / PERIOD * 360.0
        ax.plot(rot, m, color=L.COLORS[v], lw=2, label=LABEL[v])
        t_end = float(t[-1])
        revs_done = max(0.0, (t_end - T_SETTLE) / PERIOD)
        m_settle = float(np.interp(T_SETTLE, t, m))
        kr[v] = {"t_end_s": round(t_end, 4), "revolutions_simulated": round(revs_done, 3),
                 "mg_delivered_after_settle": round(float(m[-1] - m_settle), 2),
                 "mg_leaked_during_settle": round(m_settle, 2),
                 "grains_delivered": int(A[-1, 2] - np.interp(T_SETTLE, t, A[:, 2])),
                 "grains_in_domain_end": int(A[-1, 3]),
                 "complete": bool(revs_done >= 0.249),
                 "wall_s": meta.get("wall_s")}
        if revs_done > 0.05:
            kr[v]["mg_per_rev_equivalent"] = round(float(m[-1] - m_settle) / revs_done, 1)
    ax.axvline(0, color=L.INK2, lw=1, ls="--")
    ax.text(2, ax.get_ylim()[1] * 0.92 if ax.get_ylim()[1] > 0 else 1, "exit opens, motor starts", fontsize=7, color=L.INK2)
    ax.set_xlabel("auger rotation after settling (degrees; 60 rpm, 27.5° tilt)")
    ax.set_ylabel("salt delivered through the exit (mg)")
    ax.legend(fontsize=8, frameon=False, loc="upper left")
    ax.set_title("Cumulative delivery, rig_t27p5_r60 geometry (PR #180)", fontsize=9, color=L.INK)
    # snapshot panel: final frame of dry run, slice through the axis plane
    ax = axs[1]
    L.style_axes(ax)
    v0 = "dry" if "dry" in data else list(data)[0]
    files = L.dump_series(os.path.join(SCRATCH, CASES[v0], "dump", "p.*.txt"))
    if files:
        step, d = L.read_dump(files[-1])
        mm = np.abs(d["y"]) < 1.0e-3
        sp = np.sqrt(d["vx"] ** 2 + d["vy"] ** 2 + d["vz"] ** 2)[mm]
        ec = L.draw_grains(ax, d["x"][mm] * 1e3, d["z"][mm] * 1e3, d["radius"][mm] * 1e3, c=sp, cmap=L.speed_cmap(), vmax=0.1)
        cb = fig.colorbar(ec, ax=ax, shrink=0.85)
        cb.set_label("grain speed (m/s)", fontsize=8)
        ax.set_aspect("equal")
        ax.set_xlim(-14, 12)
        ax.set_ylim(-6, 34)
        ax.set_xlabel("x (mm) (gravity's side component is −x)")
        ax.set_ylabel("z along auger axis (mm)")
        ax.set_title(f"{LABEL[v0]}: slice |y|<1 mm at the end of the run", fontsize=9, color=L.INK)
    fig.suptitle("dem-liggghts-auger-short: smoke-test rerun of the #180 auger twin (LIGGGHTS-PUBLIC 3.8)", fontsize=10)
    fig.tight_layout()
    fig.savefig(os.path.join(HERE, "auger_short.png"), dpi=110, facecolor=L.SURF)
    plt.close(fig)

    # animation of the dry run (cut through the axis plane)
    frames = []
    for f in files:
        step, d = L.read_dump(f)
        fig, ax = plt.subplots(figsize=(4.6, 5.6))
        fig.patch.set_facecolor(L.SURF)
        L.style_axes(ax)
        mm = np.abs(d["y"]) < 1.0e-3
        sp = np.sqrt(d["vx"] ** 2 + d["vy"] ** 2 + d["vz"] ** 2)[mm]
        ec = L.draw_grains(ax, d["x"][mm] * 1e3, d["z"][mm] * 1e3, d["radius"][mm] * 1e3, c=sp, cmap=L.speed_cmap(), vmax=0.1)
        cb = fig.colorbar(ec, ax=ax, shrink=0.8)
        cb.set_label("grain speed (m/s)", fontsize=8)
        ax.set_aspect("equal")
        ax.set_xlim(-14, 12)
        ax.set_ylim(-6, 34)
        ax.set_xlabel("x (mm)")
        ax.set_ylabel("z along auger axis (mm)")
        t = step * data[v0][2]["dt"]
        ax.set_title(f"dem-liggghts-auger-short (LIGGGHTS-PUBLIC 3.8)\n{LABEL[v0]}, t = {t:.3f} s, slice |y|<1 mm", fontsize=8)
        frames.append(L.fig_to_array(fig))
        plt.close(fig)
    if frames:
        L.save_animation(frames, os.path.join(HERE, "auger_short.gif"), os.path.join(HERE, "auger_short.mp4"), fps=8)
    status = "ran" if all(have.values()) and all(k["complete"] for k in kr.values()) else "partial"
    out = {"id": "dem-liggghts-auger-short", "method": "smoke-test rerun of PR #180 rig auger case rig_t27p5_r60: 0.12 s settle + 0.25 rev, dry vs SJKR cohesion",
           "code": "LIGGGHTS-PUBLIC", "version": "3.8.0 (Debian package liggghts)", "status": status,
           "wall_s": {v: (None if kr[v]["wall_s"] is None else round(kr[v]["wall_s"], 1)) for v in kr}, "cores": 1,
           "particles": {v: kr[v]["grains_in_domain_end"] for v in kr}, "key_results": kr,
           "notes": "Geometry/inputs regenerated with the #180 branch's geometry.py + run_case.py (STL meshes, np=1). "
                    "PR #180 reported 12 mg in the first quarter revolution for this case."}
    L.write_json(os.path.join(HERE, "result.json"), out)
    print(json.dumps(kr, indent=1))


if __name__ == "__main__":
    main()
