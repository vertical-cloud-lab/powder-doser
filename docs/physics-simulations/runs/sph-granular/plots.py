#!/usr/bin/env python3
"""Figure, animation and result.json for sph-granular from /tmp/sims-scratch/sph-granular outputs."""
import os, json, pickle
import numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
import imageio.v2 as imageio
import imageio_ffmpeg

OUT = os.path.dirname(os.path.abspath(__file__)); SCR = "/tmp/sims-scratch/sph-granular"
R = json.load(open(f"{SCR}/raw_results.json")); P = pickle.load(open(f"{SCR}/frames.pkl", "rb"))
mpm = None
if os.path.exists("/tmp/sims-scratch/mpm-taichi/frames.pkl"):
    mpm = pickle.load(open("/tmp/sims-scratch/mpm-taichi/frames.pkl", "rb"))["col_prof"]
cols = {"c0": "#1f6fb4", "c100": "#d9622b"}; labs = {"c0": "c = 0", "c100": "c = 100 Pa"}
fig, ax = plt.subplots(1, 2, figsize=(10.5, 3.9))
for tag in ["c0", "c100"]:
    xc, hx = P["prof"][tag]
    ax[0].plot(xc * 1e3, hx * 1e3, color=cols[tag], lw=2, label=f"SPH, {labs[tag]}")
    if mpm is not None:
        xm, hm = mpm[tag]
        ax[0].plot(xm * 1e3, hm * 1e3, color=cols[tag], lw=1, ls=":", label=f"MPM (mpm-taichi), {labs[tag]}")
    fr = P["frames"][tag]
    t = np.array([f[0] for f in fr]); front = np.array([np.percentile(f[1][:, 0], 99.5) for f in fr])
    ax[1].plot(t, front * 1e3, color=cols[tag], lw=2, label=f"SPH, {labs[tag]}")
ax[0].plot([0, 40, 40], [80, 80, 0], "k--", lw=1, label="initial column (a = 2)")
ax[0].set_xlabel("distance from wall x (mm)"); ax[0].set_ylabel("deposit height h (mm)")
ax[0].set_title("(a) final deposit, φ = 34°"); ax[0].legend(fontsize=7.5); ax[0].set_xlim(0, 180)
ax[1].set_xlabel("time (s)"); ax[1].set_ylabel("front position, 99.5th pct of x (mm)")
ax[1].set_title("(b) front advance"); ax[1].legend(fontsize=8)
fig.suptitle("SPH (elastic–perfectly plastic Drucker–Prager, after Bui et al. 2008), self-written numba code", fontsize=10)
fig.tight_layout(); fig.savefig(f"{OUT}/sph_granular.png", dpi=110); plt.close(fig)

frames = []; nf = min(len(P["frames"]["c0"]), len(P["frames"]["c100"]))
for k in range(nf):
    fig, ax = plt.subplots(1, 2, figsize=(8, 2.9), dpi=80)
    for a, tag in zip(ax, ["c0", "c100"]):
        t, X, V = P["frames"][tag][k]
        a.scatter(X[:, 0] * 1e3, X[:, 1] * 1e3, s=0.8, c=V, cmap="viridis", vmin=0, vmax=1.0, rasterized=True)
        a.set_xlim(-3, 180); a.set_ylim(-3, 90); a.set_aspect("equal")
        a.axhline(0, color="k", lw=1); a.axvline(0, color="k", lw=1)
        a.set_title(f"{labs[tag]}, t = {t:.2f} s", fontsize=8); a.set_xlabel("x (mm)", fontsize=7); a.tick_params(labelsize=6)
    fig.suptitle("SPH (Drucker–Prager, Bui-type), self-written numba WCSPH — colour = speed 0–1 m/s", fontsize=8)
    fig.tight_layout(); fig.canvas.draw()
    frames.append(np.asarray(fig.canvas.buffer_rgba())[..., :3].copy()); plt.close(fig)
imageio.mimsave(f"{OUT}/sph_granular.gif", frames, duration=1 / 12, loop=0)
os.environ["IMAGEIO_FFMPEG_EXE"] = imageio_ffmpeg.get_ffmpeg_exe()
H, W = frames[0].shape[:2]; frames2 = [f[: H - H % 2, : W - W % 2] for f in frames]
imageio.mimsave(f"{OUT}/sph_granular.mp4", frames2, fps=12, codec="libx264", pixelformat="yuv420p", macro_block_size=1)
cs = {c["cohesion_Pa"]: c for c in R["cases"]}
keys = ["runout_ratio", "height_ratio", "mean_slope_deg", "fitted_mid_slope_deg", "runout_Linf_m", "max_speed_end_mps", "density_ratio_min_max"]
res = {"id": "sph-granular", "method": "SPH, elastic-perfectly plastic Drucker-Prager (Bui et al. 2008 type), 2D plane strain",
       "code": "self-written numba SPH (run.py); PySPH 1.0b2 installed but has no granular/Drucker-Prager scheme",
       "version": "numba 0.68.1, numpy 2.5.4, python 3.12 (PySPH 1.0b2 built from PyPI sdist in a separate venv)",
       "status": "ran", "wall_s": R["total_wall_s"], "cores": 1,
       "key_results": {"column_c0": {k: cs[0.0][k] for k in keys}, "column_c100Pa": {k: cs[100.0][k] for k in keys},
                       "params": R["params"]},
       "notes": "First attempt with artificial viscosity alpha=0.1 blew up at t=0.02 s (particles ejected at 10 m/s); final runs use alpha=0.5."}
json.dump(res, open(f"{OUT}/result.json", "w"), indent=1)
print(json.dumps(res["key_results"], indent=1))
for f in ["sph_granular.png", "sph_granular.gif", "sph_granular.mp4"]:
    print(f, os.path.getsize(f"{OUT}/{f}") // 1024, "kB")
