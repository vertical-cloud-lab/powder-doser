"""Post-process the MercuryDPM SaltSilo runs: discharge rate vs Beverloo, clogging, figure, animation.

Usage: python analyze.py <scratch dir; searched recursively for SaltSilo_D*.flow/.data> <this run dir>
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
RHO_P, G, T_OPEN = 2165.0, 9.81, 0.25
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
            rs = float(h[5])
            arr = np.array([fh.readline().split()[:7] for _ in range(n)], dtype=float)
            frames.append((t, arr, rs))
    return frames


results, data = {}, {}
fig, ax = plt.subplots(1, 2, figsize=(10.5, 4.2))
for flow in sorted(OUT.rglob("SaltSilo_D*.flow")):
    if flow.stat().st_size == 0 or "attempt" in str(flow):
        continue  # skip the stopped first attempt
    name = flow.stem
    Dmm = float(name.split("_D")[1])
    a = np.loadtxt(flow, comments="#")
    t, n, m = a[:, 0], a[:, 1], a[:, 2]
    i0 = int(np.argmin(np.abs(t - T_OPEN)))
    m0 = m[i0]
    frames = read_data(flow.with_suffix(".data"))
    data[name] = frames
    tf = np.array([f[0] for f in frames])
    t0, arr, RS = frames[int(np.argmin(np.abs(tf - (T_OPEN - 0.01))))]
    z, r = arr[:, 2], arr[:, 6]
    inner = np.hypot(arr[:, 0], arr[:, 1]) < RS - 2 * D_MEAN
    top = np.percentile(z[inner] + r[inner], 98)
    phi_fill = (4 / 3 * math.pi * r**3).sum() / (math.pi * RS**2 * top)
    rho_b = phi_fill * RHO_P
    D = Dmm * 1e-3
    W_bev = C_BEV * rho_b * math.sqrt(G) * (D - K_BEV * D_MEAN) ** 2.5
    # clogging: no grain leaves during the last 0.1 s
    late = t > t[-1] - 0.1
    clogged = bool(n[late][0] == n[-1] and t[-1] - T_OPEN > 0.2)
    left = n[0] - n[-1]
    res = dict(D_mm=Dmm, D_over_d=D / D_MEAN, silo_radius_mm=RS * 1e3, N=int(n[0]), fill_mass_g=float(m0 * 1e3),
               fill_height_mm=float(top * 1e3), phi_fill=float(phi_fill), bulk_density_kg_m3=float(rho_b),
               W_beverloo_g_s=float(W_bev * 1e3), clogged=clogged, grains_discharged=int(left),
               mass_discharged_g=float((m0 - m[-1]) * 1e3), sim_time_after_opening_s=float(t[-1] - T_OPEN))
    if clogged:
        moved = np.where(np.diff(n) != 0)[0]
        res["time_of_last_exit_s"] = float(t[moved[-1] + 1]) if len(moved) else None
        res["W_sim_g_s"] = 0.0
        ax[0].plot(t, m * 1e3, "-", label=f"D = {Dmm:g} mm (D/d = {D/D_MEAN:.1f}): clogged")
        ax[1].plot(Dmm, 0.0, "x", ms=10, mew=2, color="C3", label=f"MercuryDPM, D = {Dmm:g} mm: clogged")
    else:
        # steady window: 0.08 s after opening, while more than 50 % of the fill remains
        win = (t > T_OPEN + 0.08) & (m > 0.5 * m0)
        slope, icpt = np.polyfit(t[win], m[win], 1)
        W_sim = -slope
        res.update(W_sim_g_s=float(W_sim * 1e3), W_sim_over_W_bev=float(W_sim / W_bev),
                   C_fitted_with_k1p5=float(W_sim / (rho_b * math.sqrt(G) * (D - K_BEV * D_MEAN) ** 2.5)),
                   window_s=[float(t[win][0]), float(t[win][-1])])
        ax[0].plot(t, m * 1e3, "-", label=f"D = {Dmm:g} mm (D/d = {D/D_MEAN:.1f})")
        ax[0].plot(t[win], (slope * t[win] + icpt) * 1e3, "k--", lw=1)
        ax[1].plot(Dmm, W_sim * 1e3, "o", ms=8, color="C0", label=f"MercuryDPM, D = {Dmm:g} mm")
    results[name] = res

if results:
    rb = np.mean([v["bulk_density_kg_m3"] for v in results.values()])
    DD = np.linspace(K_BEV * D_MEAN * 1e3 + 0.5, 16, 100)
    ax[1].plot(DD, C_BEV * rb * math.sqrt(G) * ((DD * 1e-3) - K_BEV * D_MEAN) ** 2.5 * 1e3, "k-",
               label=f"Beverloo, C = {C_BEV}, k = {K_BEV}, $\\rho_b$ = {rb:.0f} kg/m$^3$")
ax[0].axvline(T_OPEN, color="0.6", ls=":", lw=1)
ax[0].set_xlabel("time (s)"); ax[0].set_ylabel("mass above the plate (g)")
ax[0].set_title("(a) silo mass (orifice opens at 0.25 s); dashed: fit window", fontsize=9)
ax[0].legend(fontsize=8)
ax[1].set_xlabel("orifice diameter D (mm)"); ax[1].set_ylabel("discharge rate W (g/s)")
ax[1].set_title("(b) discharge rate vs Beverloo correlation", fontsize=10)
ax[1].legend(fontsize=7)
fig.suptitle("MercuryDPM: flat-bottomed cylindrical silo, coarse-grained salt spheres (x4: 1.44-1.96 mm), "
             "$\\mu$ = 0.5, $\\mu_r$ = 0.3", fontsize=9)
fig.tight_layout()
fig.savefig(HERE / "silo_beverloo.png", dpi=110)
json.dump(results, open(HERE / "analysis_summary.json", "w"), indent=1)
print(json.dumps(results, indent=1))

# animation: the flowing run if there is one, otherwise the first run
if results:
    import imageio.v2 as imageio
    flowing = [k for k, v in results.items() if not v["clogged"]]
    name = flowing[0] if flowing else sorted(results)[0]
    Dmm = results[name]["D_mm"]
    imgs = []
    for t, arr, RS in data[name]:
        f2, axx = plt.subplots(figsize=(5.0, 5.0), dpi=100)
        sl = np.abs(arr[:, 1]) < 3e-3
        x, z, r = arr[sl, 0], arr[sl, 2], arr[sl, 6]
        axx.scatter(x * 1e3, z * 1e3, s=(r * 2e3 * 4.6) ** 2, c=np.where(z > 0, "#1f77b4", "#ff7f0e"),
                    edgecolors="k", linewidths=0.2)
        R, Ro = RS * 1e3, Dmm / 2
        axx.plot([-R, -R], [0, 45], "k-", lw=2); axx.plot([R, R], [0, 45], "k-", lw=2)
        axx.plot([-R, -Ro], [0, 0], "k-", lw=3); axx.plot([Ro, R], [0, 0], "k-", lw=3)
        if t < T_OPEN:
            axx.plot([-Ro, Ro], [0, 0], "k:", lw=1.5)
        axx.set_aspect("equal"); axx.set_xlim(-R - 1, R + 1); axx.set_ylim(-30, 40)
        axx.set_xlabel("x (mm)"); axx.set_ylabel("z (mm)")
        axx.set_title(f"MercuryDPM silo discharge (6 mm central slice), D = {Dmm:g} mm\n"
                      f"t = {t:.2f} s ({'orifice closed' if t < T_OPEN else 'orifice open'})", fontsize=9)
        f2.tight_layout(); f2.canvas.draw()
        imgs.append(np.asarray(f2.canvas.buffer_rgba())[..., :3].copy())
        plt.close(f2)
    imageio.mimsave(HERE / "silo_animation.gif", imgs, duration=1 / 10, loop=0)
    wr = imageio.get_writer(HERE / "silo_animation.mp4", fps=10, codec="libx264",
                            pixelformat="yuv420p", macro_block_size=8)
    for im in imgs:
        wr.append_data(im)
    wr.close()
    print("animation frames:", len(imgs), "from", name)
