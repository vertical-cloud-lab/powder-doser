"""Longitudinal half-sections: the CAD auger the twin used vs the printed open-end auger.

Left: ``threaded-auger-final`` as modelled in ``results/cases/rig_t27p5_r60``
(12 mm cone to a 3 mm exit, core tip in the hole). Right: the bore and core
radii recovered from the ``auger_open_end`` print job by ``gcode_profile.py``.
"""

import json
import os
import sys

import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from geometry import AugerParams, _r_in, _r_out  # noqa: E402

INK, INK2, SURF = "#0b0b0b", "#52514e", "#fcfcfb"
WALL, CORE = "#2a78d6", "#eb6834"  # wall / flight and core


def draw(ax, z, r_wall, r_core, r_outer, title, note, pitch, t_flight):
    for s in (-1, 1):
        ax.fill_betweenx(z, s * r_wall, s * r_outer, color=WALL, alpha=0.35, lw=0)
        ax.fill_betweenx(z, s * 0, s * r_core, color=CORE, alpha=0.35, lw=0)
        ax.plot(s * r_wall, z, color=WALL, lw=1.5)
        ax.plot(s * r_core, z, color=CORE, lw=1.5)
    # flight crossings of the section plane (right-handed, one start)
    for k in range(-1, 4):
        for s, z0 in ((1, 0.0), (-1, pitch / 2)):
            zc = z0 + k * pitch
            if zc < 0.4 or zc > z.max():
                continue
            i = np.argmin(np.abs(z - zc))
            ax.fill_between([s * r_core[i], s * r_wall[i]], zc, zc + t_flight, color=WALL, alpha=0.8, lw=0)
    ax.axhline(0, color=INK2, lw=0.8, ls=(0, (4, 3)))
    ax.text(0, -1.2, "exit plane", ha="center", va="top", fontsize=8, color=INK2)
    ax.set_title(title, fontsize=9, color=INK, loc="left")
    ax.text(0, -3.4, note, ha="center", va="top", fontsize=7.5, color=INK)
    ax.set_xlim(-14, 14)
    ax.set_ylim(-8.5, z.max())
    ax.set_yticks(np.arange(0, z.max() + 0.1, 5))
    ax.set_aspect("equal")
    ax.set_xlabel("radius (mm)", fontsize=8, color=INK2)
    ax.tick_params(labelsize=7, colors=INK2)
    for sp in ax.spines.values():
        sp.set_color("#c3c2b7")


def main():
    zmax = 30.0
    cfg = json.load(open(os.path.join(os.path.dirname(HERE), "results/cases/rig_t27p5_r60/config.json")))
    P = AugerParams(**cfg["geometry"])
    z = np.linspace(0, zmax, 601)
    r_out_cad, r_core_cad = _r_out(P, z), _r_in(P, z)
    prof = np.loadtxt(os.path.join(HERE, "auger_open_end_profile.csv"), delimiter=",", skiprows=1)
    zp = prof[:, 0]
    m = zp <= zmax
    zp, bore, core = zp[m], prof[m, 1], prof[m, 2]
    # below z = 2 the core is a printed pin too thin to close a wall loop; continue its cone (r = 1.04 + z/2)
    core = np.where(core > 0, core, np.clip(1.04 + 0.5 * zp, 0, None))
    zp = np.r_[0.0, zp]
    bore, core = np.r_[bore[0], bore], np.r_[1.04, core]
    fig, axs = plt.subplots(1, 2, figsize=(8.4, 5.6), facecolor=SURF)
    for ax in axs:
        ax.set_facecolor(SURF)
    a_cad = np.pi * (P.exit_r ** 2 - P.tip_r ** 2)
    a_pr = np.pi * (bore[0] ** 2 - core[0] ** 2)
    draw(axs[0], z, r_out_cad, r_core_cad, np.full_like(z, 12.6),
         "CAD threaded-auger-final (the PR #180 twin)",
         f"exit: annulus r {P.tip_r:.2f}-{P.exit_r:.2f} mm, {a_cad:.1f} mm²\n12 mm cone, Ø8 core, tip in the hole",
         P.pitch, P.flight_t)
    draw(axs[1], zp, bore, core, np.full_like(zp, 12.6),
         "printed auger_open_end (A1 mini, 2026-09-09)",
         f"exit: annulus r {core[0]:.1f}-{bore[0]:.1f} mm, {a_pr:.0f} mm² ({a_pr / a_cad:.0f}x)\n"
         "no cone, Ø14 core tapering to the exit",
         10.42, 0.5)
    axs[0].set_ylabel("height above the exit (mm)", fontsize=8, color=INK2)
    fig.text(0.5, 0.015, "Longitudinal section through the axis: wall and flight blue, core orange. "
             "Printed profile from the job's G-code (gcode_profile.py).", ha="center", fontsize=7.5, color=INK2)
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    out = os.path.join(HERE, "exit_cad_vs_printed.png")
    fig.savefig(out, dpi=130, facecolor=SURF)
    print(out, f"CAD exit {a_cad:.2f} mm2, printed exit {a_pr:.1f} mm2")


if __name__ == "__main__":
    main()
