"""Figures for the MuJoCo mesh studies (reads out/mujoco/*.json and the run logs).

    python mesh_plots.py
"""
from __future__ import annotations

import json

import numpy as np

import common as C
import vizstyle as V

MJ = C.OUT / "mujoco"


def load(name):
    p = MJ / f"{name}.json"
    return json.loads(p.read_text()) if p.exists() else []


def stall_figure():
    import matplotlib.pyplot as plt
    rows = load("stall_sweep") + load("stall_sweep_final")
    if not rows:
        return
    show = [("as drawn", "Sam's carriage as drawn (gravity only)"), ("magnet + steel pinion", "+ magnet + steel pinion (old pin)"),
            ("pin (48,-58)", "+ pin moved to (48, -58)"), ("final", "as built: stub pins at COM height, 32.25 mm")]
    fig, ax = plt.subplots(figsize=(7.8, 4.6))
    ax.axhline(0.1 * C.Z2 / C.Z1, color=V.INK2, lw=0.8)
    ax.text(1, 0.1 * C.Z2 / C.Z1 + 0.006, "motor holding torque at the auger (0.22 N·m)", fontsize=8, color=V.INK2)
    for (cfg, lab), col in zip(show, V.SERIES):
        rr = sorted([r for r in rows if r["config"] == cfg], key=lambda r: r["tilt"])
        if not rr:
            continue
        t = [r["tilt"] for r in rr]
        y = [(r["load_at_failure_Nm"] or 0.0) if r["mode"] != "held" else 0.45 for r in rr]
        ax.plot(t, y, color=col, label=lab, marker="o", ms=0, lw=1.6)
        for ti, yi, r in zip(t, y, rr):
            if r["mode"] == "tooth jump":
                ax.plot(ti, yi, marker="x", ms=8, mew=2.0, color=V.CRITICAL, zorder=5)
            else:
                ax.plot(ti, yi, marker="o", ms=8, color=col, markeredgecolor=V.SURFACE, mew=2.0, zorder=5)
    ax.plot([], [], marker="o", ms=8, ls="", color=V.INK2, label="motor stalled first (mesh held)")
    ax.plot([], [], marker="x", ms=8, mew=2, ls="", color=V.CRITICAL, label="teeth jumped / dock opened")
    ax.set_xlim(-3, 93)
    ax.set_ylim(-0.01, 0.27)
    ax.set_xticks(range(0, 91, 15))
    ax.set_xlabel("module tilt at the station (deg)")
    ax.set_ylabel("auger load when something gave (N·m)")
    ax.set_title("Load ramp at 30 rpm: only the as-built station holds the mesh at every tilt")
    ax.legend(loc="center left", fontsize=7.8, bbox_to_anchor=(0.0, 0.42))
    fig.tight_layout()
    fig.savefig(C.OUT / "mujoco_stall_vs_tilt.png", dpi=150)
    plt.close(fig)


def table_speed(name):
    rows = load(name)
    out = {}
    for r in rows:
        out.setdefault(r["config"], {}).setdefault(r["tilt"], {})[r["rpm"]] = (r["tooth_jumps"], r["stall_s"] is not None,
                                                                               r["centre_distance_mm"]["max"])
    return out


def timeseries_figure(tag, title, out_name):
    import matplotlib.pyplot as plt
    p = MJ / f"{tag}.npz"
    if not p.exists():
        return
    A = np.load(p)["log"]
    t = A[:, 0] - A[0, 0]
    fig, axs = plt.subplots(2, 1, figsize=(7.8, 4.8), sharex=True)
    axs[0].plot(t, A[:, 5], color=V.SERIES[0])
    axs[0].set_ylabel("centre distance (mm)")
    axs[0].set_title(title)
    axs[1].plot(t, A[:, 6], color=V.SERIES[1], label="rim gap, front")
    axs[1].plot(t, A[:, 8], color=V.SERIES[2], label="magnet gap")
    axs[1].set_ylabel("gap (mm)")
    axs[1].set_xlabel("time (s)")
    axs[1].legend(loc="upper right")
    fig.tight_layout()
    fig.savefig(C.OUT / out_name, dpi=150)
    plt.close(fig)


if __name__ == "__main__":
    V.setup()
    stall_figure()
    for n in ("speed_sweep_ideal", "speed_sweep_errors"):
        print(n, json.dumps(table_speed(n), indent=0)[:2000])
