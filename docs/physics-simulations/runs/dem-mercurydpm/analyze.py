"""Post-process the MercuryDPM SaltSilo runs: discharge rate vs Beverloo, figure and animation.

Usage: python analyze.py <scratch dir with SaltSilo_D*.flow / .data> <this run dir>
"""
import glob
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
RHO_P, G, RS, T_OPEN = 2165.0, 9.81, 12.5e-3, 0.25
D_MEAN = 1.7e-3                  # number-mean grain diameter after coarse-graining (x4)
C_BEV, K_BEV = 0.58, 1.5         # Beverloo et al. (1961) constants as usually quoted


def read_data(fn):
    frames = []
    with open(fn) as fh:
        while True:
            line = fh.readline()
            if not line:
                break
            h = line.split()
            if len(h) != 8:
                continue
            n, t = int(float(h[0])), float(h[1])
            arr = np.array([fh.readline().split()[:7] for _ in range(n)], dtype=float)
            frames.append((t, arr))
    return frames


results = {}
fig, ax = plt.subplots(1, 2, figsize=(10.5, 4.2))
for flow in sorted(glob.glob(str(OUT / "SaltSilo_D*.flow"))):
    name = Path(flow).stem
    Dmm = float(name.split("_D")[1])
    a = np.loadtxt(flow, comments="#")
    t, n, m = a[:, 0], a[:, 1], a[:, 2]
    m0 = m[np.argmin(np.abs(t - T_OPEN))]
    # bulk density of the settled fill just before opening, from the .data snapshot
    frames = read_data(OUT / f"{name}.data")
    tf = np.array([f[0] for f in frames])
    t0, arr = frames[int(np.argmin(np.abs(tf - (T_OPEN - 0.01))))]
    z, r = arr[:, 2], arr[:, 6]
    inner = np.hypot(arr[:, 0], arr[:, 1]) < RS - 2 * D_MEAN
    top = np.percentile(z[inner] + r[inner], 98)
    vol_p = (4 / 3 * math.pi * r**3).sum()
    phi_fill = vol_p / (math.pi * RS**2 * top)
    rho_b = phi_fill * RHO_P
    # steady discharge window: 0.15 s after opening until 35 % of the fill has left
    win = (t > T_OPEN + 0.15) & (m > 0.65 * m0)
    if win.sum() < 10:
        win = (t > T_OPEN + 0.1) & (t < T_OPEN + 0.6)
    slope, icpt = np.polyfit(t[win], m[win], 1)
    W_sim = -slope
    D = Dmm * 1e-3
    W_bev = C_BEV * rho_b * math.sqrt(G) * (D - K_BEV * D_MEAN) ** 2.5
    C_fit = W_sim / (rho_b * math.sqrt(G) * (D - K_BEV * D_MEAN) ** 2.5)
    results[name] = dict(D_mm=Dmm, D_over_d=D / D_MEAN, N=int(n[0]), fill_mass_kg=float(m0),
                         fill_height_mm=float(top * 1e3), phi_fill=float(phi_fill),
                         bulk_density_kg_m3=float(rho_b), W_sim_kg_s=float(W_sim),
                         W_beverloo_kg_s=float(W_bev), W_sim_over_W_bev=float(W_sim / W_bev),
                         C_fitted_with_k1p5=float(C_fit),
                         window_s=[float(t[win][0]), float(t[win][-1])],
                         mass_left_at_end_kg=float(m[-1]))
    ax[0].plot(t, m * 1e3, "-", label=f"D = {Dmm:g} mm (D/d = {D/D_MEAN:.1f})")
    ax[0].plot(t[win], (slope * t[win] + icpt) * 1e3, "k--", lw=1)
    ax[1].plot(Dmm, W_sim * 1e3, "o", ms=8, label=f"MercuryDPM, D = {Dmm:g} mm")

if results:
    rb = np.mean([v["bulk_density_kg_m3"] for v in results.values()])
    DD = np.linspace(K_BEV * D_MEAN * 1e3 + 0.5, 14, 100)
    ax[1].plot(DD, C_BEV * rb * math.sqrt(G) * ((DD * 1e-3) - K_BEV * D_MEAN) ** 2.5 * 1e3, "k-",
               label=f"Beverloo, C = {C_BEV}, k = {K_BEV}, $\\rho_b$ = {rb:.0f} kg/m$^3$")
ax[0].axvline(T_OPEN, color="0.6", ls=":", lw=1)
ax[0].set_xlabel("time (s)"); ax[0].set_ylabel("mass in silo (g)")
ax[0].set_title("(a) silo mass; dashed: linear fit in the steady window", fontsize=10)
ax[0].legend(fontsize=8)
ax[1].set_xlabel("orifice diameter D (mm)"); ax[1].set_ylabel("discharge rate W (g/s)")
ax[1].set_title("(b) discharge rate vs Beverloo correlation", fontsize=10)
ax[1].legend(fontsize=8)
fig.suptitle("MercuryDPM: flat-bottomed silo (25 mm dia.), coarse-grained salt spheres (x4: 1.44-1.96 mm)", fontsize=10)
fig.tight_layout()
fig.savefig(HERE / "silo_beverloo.png", dpi=110)
json.dump(results, open(HERE / "analysis_summary.json", "w"), indent=1)
print(json.dumps(results, indent=1))

# animation from the first run's .data file (side view of a 6 mm thick central slice)
names = sorted(results)
if names:
    import imageio.v2 as imageio
    name = names[0]
    frames = read_data(OUT / f"{name}.data")
    imgs = []
    Dmm = results[name]["D_mm"]
    for t, arr in frames:
        f2, axx = plt.subplots(figsize=(5.0, 5.0), dpi=100)
        sl = np.abs(arr[:, 1]) < 3e-3
        x, z, r = arr[sl, 0], arr[sl, 2], arr[sl, 6]
        axx.scatter(x * 1e3, z * 1e3, s=(r * 2e3 * 5.2) ** 2, c=np.where(z > 0, "#1f77b4", "#ff7f0e"),
                    edgecolors="k", linewidths=0.2)
        R, Ro = RS * 1e3, Dmm / 2
        axx.plot([-R, -R], [0, 45], "k-", lw=2); axx.plot([R, R], [0, 45], "k-", lw=2)
        axx.plot([-R, -Ro], [0, 0], "k-", lw=3); axx.plot([Ro, R], [0, 0], "k-", lw=3)
        if t < T_OPEN:
            axx.plot([-Ro, Ro], [0, 0], "k:", lw=1.5)
        axx.set_aspect("equal"); axx.set_xlim(-R - 1, R + 1); axx.set_ylim(-30, 40)
        axx.set_xlabel("x (mm)"); axx.set_ylabel("z (mm)")
        axx.set_title(f"MercuryDPM silo discharge (central slice), D = {Dmm:g} mm\n"
                      f"t = {t:.2f} s ({'orifice closed' if t < T_OPEN else 'discharging'})", fontsize=9)
        f2.tight_layout(); f2.canvas.draw()
        imgs.append(np.asarray(f2.canvas.buffer_rgba())[..., :3].copy())
        plt.close(f2)
    imageio.mimsave(HERE / "silo_animation.gif", imgs, duration=1 / 12, loop=0)
    wr = imageio.get_writer(HERE / "silo_animation.mp4", fps=12, codec="libx264",
                            pixelformat="yuv420p", macro_block_size=8)
    for im in imgs:
        wr.append_data(im)
    wr.close()
    print("animation frames:", len(imgs))
