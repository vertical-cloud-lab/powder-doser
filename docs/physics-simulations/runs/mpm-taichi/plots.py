#!/usr/bin/env python3
"""Figure, animation and result.json for mpm-taichi from /tmp/sims-scratch/mpm-taichi outputs."""
import os, json, pickle
import numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
import imageio.v2 as imageio
import imageio_ffmpeg

OUT = os.path.dirname(os.path.abspath(__file__)); SCR = "/tmp/sims-scratch/mpm-taichi"
R = json.load(open(f"{SCR}/raw_results.json")); P = pickle.load(open(f"{SCR}/frames.pkl", "rb"))
dx = R["params"]["dx_m"]; rho_b = R["params"]["rho_bulk"]; g = 9.81
# Beverloo-type plane-flow law through the two largest slots (exact 2-point solve), exponent 3/2
Ds = np.array([r["D_m"] for r in R["silo"]]); Ws = np.array([r["W_kg_per_m_s"] for r in R["silo"]])
r32 = (Ws[2] / Ws[1]) ** (2 / 3); D0 = (r32 * Ds[1] - Ds[2]) / (r32 - 1)
Cb = Ws[2] / (rho_b * np.sqrt(g) * (Ds[2] - D0) ** 1.5)
pred_small = Cb * rho_b * np.sqrt(g) * max(Ds[0] - D0, 0) ** 1.5
pexp = np.polyfit(np.log(Ds), np.log(Ws), 1)[0]
Wbev103 = 1.03 * rho_b * np.sqrt(g) * Ds ** 1.5

fig, ax = plt.subplots(1, 3, figsize=(13, 3.9))
cols = {"c0": "#1f6fb4", "c100": "#d9622b"}
for tag, lab in [("c0", "c = 0 Pa"), ("c100", "c = 100 Pa")]:
    xc, hx = P["col_prof"][tag]
    ax[0].plot(xc * 1e3, hx * 1e3, color=cols[tag], lw=2, label=f"final deposit, {lab}")
ax[0].plot([0, 40, 40], [80, 80, 0], "k--", lw=1, label="initial column (a = 2)")
ax[0].set_xlabel("distance from wall x (mm)"); ax[0].set_ylabel("deposit height h (mm)")
ax[0].set_title("(a) column collapse, φ = 34°"); ax[0].legend(fontsize=8); ax[0].set_xlim(0, 180)
for (tag, (t, m)), c in zip(P["silo_curves"].items(), ["#1f6fb4", "#2a9d5c", "#d9622b"]):
    ax[1].plot(t, m, color=c, label=f"D = {tag[1:]} mm")
ax[1].axvspan(0.08, 0.25, color="0.9", zorder=0, label="fit window")
ax[1].set_xlabel("time after opening (s)"); ax[1].set_ylabel("discharged mass (kg per m depth)")
ax[1].set_title("(b) flat-bottomed silo discharge"); ax[1].legend(fontsize=8)
DD = np.linspace(0.004, 0.018, 100)
ax[2].plot(Ds * 1e3, Ws, "o", color="#1f6fb4", ms=8, label="MPM (Taichi)")
ax[2].plot(DD * 1e3, 1.03 * rho_b * np.sqrt(g) * DD ** 1.5, "k--", lw=1, label="plane Beverloo, C=1.03, k·d=0")
ax[2].plot(DD * 1e3, Cb * rho_b * np.sqrt(g) * np.clip(DD - D0, 0, None) ** 1.5, color="#d9622b",
           label=f"3/2 law through 12,16 mm: C={Cb:.2f}, D0={D0*1e3:.1f} mm")
ax[2].set_xlabel("slot width D (mm)"); ax[2].set_ylabel("mass flow W (kg s$^{-1}$ per m depth)")
ax[2].set_title(f"(c) W vs D; dx = {dx*1e3:.2f} mm"); ax[2].legend(fontsize=7.5)
fig.suptitle("MPM (MLS-MPM, Drucker–Prager, Klar et al. 2016) in Taichi 1.7.4, 2D plane strain", fontsize=10)
fig.tight_layout(); fig.savefig(f"{OUT}/mpm_taichi.png", dpi=110); plt.close(fig)

# animation
frames = []; nf = min(len(P["col_frames"]["c0"]), len(P["col_frames"]["c100"]), len(P["silo_frames"]["D12"]))
for k in range(nf):
    fig, ax = plt.subplots(1, 3, figsize=(8, 3.0), dpi=80)
    for a, (tag, ttl) in zip(ax[:2], [("c0", "column, c = 0"), ("c100", "column, c = 100 Pa")]):
        t, X, V = P["col_frames"][tag][k]
        a.scatter(X[:, 0] * 1e3, X[:, 1] * 1e3, s=0.4, c=V, cmap="viridis", vmin=0, vmax=1.0, rasterized=True)
        a.set_xlim(0, 180); a.set_ylim(0, 90); a.set_aspect("equal"); a.set_title(f"{ttl}\nt = {t:.2f} s", fontsize=8)
        a.set_xlabel("x (mm)", fontsize=7); a.tick_params(labelsize=6)
    t, X, V = P["silo_frames"]["D12"][k]
    ax[2].scatter(X[:, 0] * 1e3, X[:, 1] * 1e3, s=0.3, c=V, cmap="viridis", vmin=0, vmax=1.0, rasterized=True)
    ax[2].plot([60, 60, 94], [160, 70, 70], "k-", lw=1); ax[2].plot([140, 140, 106], [160, 70, 70], "k-", lw=1)
    ax[2].set_xlim(50, 150); ax[2].set_ylim(0, 160); ax[2].set_aspect("equal")
    ax[2].set_title(f"silo, D = 12 mm\nt = {t:+.2f} s after opening", fontsize=8)
    ax[2].set_xlabel("x (mm)", fontsize=7); ax[2].tick_params(labelsize=6)
    fig.suptitle("MPM (MLS-MPM + Drucker–Prager), Taichi 1.7.4 — colour = speed 0–1 m/s", fontsize=8)
    fig.tight_layout(); fig.canvas.draw()
    frames.append(np.asarray(fig.canvas.buffer_rgba())[..., :3].copy()); plt.close(fig)
imageio.mimsave(f"{OUT}/mpm_taichi.gif", frames, duration=1 / 12, loop=0)
os.environ["IMAGEIO_FFMPEG_EXE"] = imageio_ffmpeg.get_ffmpeg_exe()
H, W = frames[0].shape[:2]; frames2 = [f[: H - H % 2, : W - W % 2] for f in frames]
imageio.mimsave(f"{OUT}/mpm_taichi.mp4", frames2, fps=12, codec="libx264", pixelformat="yuv420p", macro_block_size=1)

col = {c["cohesion_Pa"]: c for c in R["columns"]}
res = {"id": "mpm-taichi", "method": "Material Point Method (MLS-MPM) with Drucker-Prager elastoplasticity (Klar et al. 2016)",
       "code": "Taichi (self-written MLS-MPM kernel, run.py)", "version": "taichi 1.7.4 (LLVM 15), python 3.12",
       "status": "ran", "wall_s": R["total_wall_s"], "cores": 1,
       "key_results": {
           "column_c0": {k: col[0.0][k] for k in ["runout_ratio", "height_ratio", "mean_slope_deg", "fitted_mid_slope_deg", "runout_Linf_m"]},
           "column_c100Pa": {k: col[100.0][k] for k in ["runout_ratio", "height_ratio", "mean_slope_deg", "fitted_mid_slope_deg", "runout_Linf_m"]},
           "silo_W_kg_per_m_s": {f"D{int(d*1e3)}mm": w for d, w in zip(Ds, Ws)},
           "loglog_exponent_W_vs_D": float(pexp),
           "three_halves_law_through_12_16mm": {"C": float(Cb), "D0_mm": float(D0 * 1e3), "D0_over_dx": float(D0 / dx),
                                                 "predicted_W_8mm": float(pred_small), "MPM_W_8mm": float(Ws[0])},
           "beverloo_C1p03_k0_W": {f"D{int(d*1e3)}mm": float(w) for d, w in zip(Ds, Wbev103)},
           "free_3param_fit_attempt": R["beverloo_fit"]},
       "notes": "2D plane strain, per metre depth; rho_bulk 1250 kg/m3 assumed; E=0.3 MPa (soft for speed); no grain size in the continuum, so the k*d term becomes a grid-scale offset."}
json.dump(res, open(f"{OUT}/result.json", "w"), indent=1)
print(json.dumps(res["key_results"], indent=1))
for f in ["mpm_taichi.png", "mpm_taichi.gif", "mpm_taichi.mp4"]:
    print(f, os.path.getsize(f"{OUT}/{f}") // 1024, "kB")
