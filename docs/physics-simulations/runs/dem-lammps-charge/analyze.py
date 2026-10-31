"""Post-process the charged-pour runs: bed height, packing fraction, wall adhesion, animation.

Usage: python analyze.py <scratch dir with final_*.lammpstrj, dump_*.lammpstrj, log.*> <this run dir>
"""
import json
import math
import sys
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

OUT = Path(sys.argv[1])
HERE = Path(sys.argv[2])
A = 0.425e-3                 # wall-sphere spacing and diameter
LX = LY = 10 * A
CASES = {  # tag: (q/m C/kg, wall sigma C/m^2, label)
    "A": (0.0, 0.0, "uncharged"),
    "B": (-1e-5, 1e-5, "q/m = -1e-5 C/kg, wall +1e-5 C/m$^2$"),
    "C": (-1e-4, 1e-5, "q/m = -1e-4 C/kg, wall +1e-5 C/m$^2$"),
    "D": (-1e-4, 0.0, "q/m = -1e-4 C/kg, wall uncharged"),
    "Clong": (-1e-4, 1e-5, "as C, run to 0.6 s"),
}


def read_dump(fn):
    frames = []
    with open(fn) as fh:
        while True:
            line = fh.readline()
            if not line:
                break
            if line.startswith("ITEM: TIMESTEP"):
                step = int(fh.readline())
                fh.readline(); n = int(fh.readline())
                fh.readline()
                [fh.readline() for _ in range(3)]
                cols = fh.readline().split()[2:]
                arr = np.array([fh.readline().split() for _ in range(n)], dtype=float)
                frames.append((step, dict(zip(cols, arr.T))))
    return frames


def metrics(d):
    mob = d["type"] < 4
    x, z, r = d["x"][mob], d["z"][mob], d["diameter"][mob] / 2
    vol = 4 / 3 * math.pi * r**3
    # solid-fraction profile in the bulk (away from both side walls)
    bulk = (x > 1.0e-3) & (x < LX - 0.6e-3)
    dz = 0.25e-3
    edges = np.arange(0, 0.012 + dz, dz)
    area = (LX - 0.6e-3 - 1.0e-3) * LY
    prof = np.array([vol[bulk & (z >= a) & (z < b)].sum() / (area * dz) for a, b in zip(edges[:-1], edges[1:])])
    zc = 0.5 * (edges[:-1] + edges[1:])
    plateau = np.median(prof[(zc > 0.6e-3) & (zc < 1.6e-3)])
    if plateau < 0.4:   # no dense bed formed: report the mean solid fraction of the column instead
        h = float("nan")
        phi = float(prof[(zc > 0.5e-3) & (zc < 8e-3)].mean())
    else:
        above = np.where((prof < 0.5 * plateau) & (zc > 1e-3))[0]
        h = zc[above[0]] if len(above) else float("nan")
        core = (zc > 0.6e-3) & (zc < h - 0.6e-3)
        phi = float(prof[core].mean()) if core.any() else float("nan")
    # grains touching the charged wall layer (centre within r + a/2 + 5 um of x = 0)
    touch = x < r + A / 2 + 5e-6
    # "above the bed": higher than the uncharged bed (3.38 mm) plus one grain diameter
    stuck_above = int((touch & (z > 3.375e-3 + A)).sum())
    wall_touch = int(touch.sum())
    lost = int(((z > 0.0185) | (z < 0)).sum())
    return dict(bed_height_mm=float(h * 1e3), phi_bulk=phi, grains_touching_wall=wall_touch,
                grains_on_wall_above_bed=stuck_above, n_mobile=int(mob.sum()),
                grains_near_lid=lost), (zc, prof)


def ke_series(tag):
    f = OUT / f"log.{tag}"
    t, ke = [], []
    on = False
    for line in open(f):
        s = line.split()
        if s[:2] == ["Step", "Time"]:
            on = True; continue
        if on:
            if s and s[0] == "Loop":
                on = False; continue
            try:
                t.append(float(s[1])); ke.append(float(s[2]))
            except (ValueError, IndexError):
                pass
    return np.array(t), np.array(ke)


res = {}
fig = plt.figure(figsize=(14, 4.6))
present = [t for t in CASES if (OUT / f"final_{t}.lammpstrj").exists()]
gs = fig.add_gridspec(1, len(present) + 1, width_ratios=[1] * len(present) + [1.5])
axp = fig.add_subplot(gs[0, -1])
colors = {"A": "#7f7f7f", "B": "#1f77b4", "C": "#d62728", "D": "#ff7f0e", "Clong": "#9467bd"}
for i, tag in enumerate(present):
    step, d = read_dump(OUT / f"final_{tag}.lammpstrj")[-1]
    m, (zc, prof) = metrics(d)
    t, ke = ke_series(tag)
    m["final_time_s"] = float(step * 1e-5)
    m["final_kinetic_energy_J"] = float(ke[-1]) if len(ke) else None
    qm, sig, lab = CASES[tag]
    m.update(q_over_m_C_per_kg=qm, wall_sigma_C_per_m2=sig)
    res[tag] = m
    ax = fig.add_subplot(gs[0, i])
    sl = np.abs(d["y"] - LY / 2) < 1.2e-3
    mob = (d["type"] < 4) & sl
    wal = (d["type"] == 4) & sl
    ax.scatter(d["x"][wal] * 1e3, d["z"][wal] * 1e3, s=(d["diameter"][wal] * 1e3 * 13) ** 2,
               c="#2ca02c" if sig > 0 else "#bbbbbb", edgecolors="none")
    ax.scatter(d["x"][mob] * 1e3, d["z"][mob] * 1e3, s=(d["diameter"][mob] * 1e3 * 13) ** 2,
               c=colors[tag], edgecolors="k", linewidths=0.2)
    ax.set_aspect("equal"); ax.set_xlim(-0.4, LX * 1e3 + 0.1); ax.set_ylim(0, 13)
    ax.set_xlabel("x (mm)")
    if i == 0:
        ax.set_ylabel("z (mm)")
    bed = "no dense bed" if not np.isfinite(m["bed_height_mm"]) else f"bed {m['bed_height_mm']:.2f} mm"
    ax.set_title(f"case {tag} (t = {step*1e-5:.1f} s)\n{bed}, $\\phi$ = {m['phi_bulk']:.2f}\n"
                 f"on wall above 3.8 mm: {m['grains_on_wall_above_bed']}", fontsize=8)
    axp.plot(prof, zc * 1e3, "-", color=colors[tag], label=f"{tag}: {lab}")
axp.set_xlabel("solid fraction in bulk, x > 1 mm (-)")
axp.set_ylabel("height z (mm)")
axp.set_ylim(0, 8); axp.set_xlim(0, 0.7)
axp.legend(fontsize=7, loc="upper right")
axp.set_title("solid-fraction profiles (end of run)", fontsize=9)
fig.suptitle("LAMMPS granular + coul/cut: 800 salt grains poured beside a charged wall "
             "(green = charged wall layer, slice |y - y_c| < 1.2 mm)", fontsize=9)
fig.tight_layout()
fig.savefig(HERE / "charge_settling.png", dpi=100)
clean = {t: {k: (None if isinstance(v, float) and not math.isfinite(v) else v) for k, v in m.items()} for t, m in res.items()}
json.dump(clean, open(HERE / "analysis_summary.json", "w"), indent=1)
print(json.dumps(clean, indent=1))

# animation of the strongest case
tag = "Clong" if (OUT / "dump_Clong.lammpstrj").exists() else ("C" if (OUT / "dump_C.lammpstrj").exists() else None)
if tag:
    import imageio.v2 as imageio
    frames = read_dump(OUT / f"dump_{tag}.lammpstrj")
    imgs = []
    for step, d in frames[::(2 if tag == "Clong" else 1)]:
        f2, ax = plt.subplots(figsize=(4.2, 6.0), dpi=100)
        sl = np.abs(d["y"] - LY / 2) < 1.2e-3
        mob = (d["type"] < 4) & sl
        wal = (d["type"] == 4) & sl
        ax.scatter(d["x"][wal] * 1e3, d["z"][wal] * 1e3, s=(d["diameter"][wal] * 1e3 * 15) ** 2, c="#2ca02c")
        ax.scatter(d["x"][mob] * 1e3, d["z"][mob] * 1e3, s=(d["diameter"][mob] * 1e3 * 15) ** 2,
                   c="#d62728", edgecolors="k", linewidths=0.2)
        ax.set_aspect("equal"); ax.set_xlim(-0.4, LX * 1e3 + 0.1); ax.set_ylim(0, 19.5)
        ax.set_xlabel("x (mm)"); ax.set_ylabel("z (mm)")
        ax.set_title(f"LAMMPS granular + coul/cut, case {tag}\nq/m = -1e-4 C/kg, wall +1e-5 C/m$^2$, "
                     f"t = {step*1e-5:.3f} s", fontsize=8)
        f2.tight_layout(); f2.canvas.draw()
        imgs.append(np.asarray(f2.canvas.buffer_rgba())[..., :3].copy())
        plt.close(f2)
    imageio.mimsave(HERE / "charge_animation.gif", imgs, duration=1 / 10, loop=0)
    wr = imageio.get_writer(HERE / "charge_animation.mp4", fps=10, codec="libx264",
                            pixelformat="yuv420p", macro_block_size=8)
    for im in imgs:
        wr.append_data(im)
    wr.close()
    print("animation frames:", len(imgs))
