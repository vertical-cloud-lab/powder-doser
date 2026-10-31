"""Figure + animation for the GNS column-collapse run.
Usage: python plot_gns.py SCRATCH_OUT REPO_OUT DATA_DIR
"""
import json
import os
import sys

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import imageio.v2 as imageio
import imageio_ffmpeg

SCR, OUT, DATA = sys.argv[1], sys.argv[2], sys.argv[3]
summ = json.load(open(os.path.join(SCR, "train_summary.json")))
cases = sorted(summ["cases"].keys())
DT_FRAME = 2.0 / 150
D = 0.016

fig, ax = plt.subplots(2, 3, figsize=(15, 8.6))
roll0 = np.load(os.path.join(SCR, f"rollout_{cases[0]}.npz"))
tr, pr, r = roll0["true"], roll0["pred"], roll0["r"]
for a, k in zip(ax[0], [0, 40, tr.shape[0] - 1]):
    a.scatter(tr[k, :, 0], tr[k, :, 1], s=9, c="C0", label="DEM (ground truth)")
    a.scatter(pr[k, :, 0], pr[k, :, 1], s=9, facecolors="none", edgecolors="C1", lw=0.7, label="GNS rollout")
    a.set_xlim(0, 0.45); a.set_ylim(0, 0.32); a.set_aspect("equal")
    a.set_xlabel("x (box units, 1 = box width)"); a.set_ylabel("y (box units)")
    a.set_title(f"{cases[0]}: t = {k * DT_FRAME:.2f} (step {k})")
    a.legend(fontsize=8, loc="upper right")
for k in cases:
    c = summ["cases"][k]
    e = np.array(c["err_curve_over_d"])
    ax[1, 0].plot(np.arange(len(e)) * DT_FRAME, e, label=f"{k} (N={c['N']}, H0/W={c['H0'] / c['W']:.1f})")
    t = np.arange(len(c["runout_true"])) * DT_FRAME
    l, = ax[1, 1].plot(t, c["runout_true"], "-", label=f"{k} DEM")
    ax[1, 1].plot(t, c["runout_gns"], "--", color=l.get_color(), label=f"{k} GNS")
ax[1, 0].set_xlabel("time (dimensionless, g = 1)"); ax[1, 0].set_ylabel("RMS position error (grain diameters)")
ax[1, 0].set_title("rollout error vs time (held-out columns)"); ax[1, 0].legend(fontsize=8)
ax[1, 1].set_xlabel("time (dimensionless, g = 1)"); ax[1, 1].set_ylabel("front position x (box units)")
ax[1, 1].set_title("runout: DEM (solid) vs GNS (dashed)"); ax[1, 1].legend(fontsize=7, ncol=2)
log = summ["log"]
ax[1, 2].semilogy([l["step"] for l in log], [l["loss"] for l in log], "o-", ms=3, label="training loss (normalised accel. MSE)")
vl = [(l["step"], l["val_onestep_mse"]) for l in log if "val_onestep_mse" in l]
if vl:
    ax2 = ax[1, 2].twinx()
    ax2.semilogy(*zip(*vl), "s-", color="C3", ms=4, label="valid one-step position MSE")
    ax2.set_ylabel("one-step position MSE (box units$^2$)", color="C3")
ax[1, 2].set_xlabel("training step (batch of 2 windows)"); ax[1, 2].set_ylabel("loss (-)")
ax[1, 2].set_title(f"training: {summ['steps']} steps in {summ['train_s'] / 60:.1f} min, 1 CPU thread")
ax[1, 2].legend(fontsize=8, loc="upper right")
fig.suptitle("gns-gnn-simulator: geoelements/gns LearnedSimulator (reduced: latent %d, %d message-passing steps) "
             "trained on a numba-DEM column-collapse set (40 trajectories)" % (summ["latent"], summ["nmp"]), fontsize=11)
fig.tight_layout()
fig.savefig(os.path.join(OUT, "gns_rollout.png"), dpi=95)

# ---------- animation: one in-range column (test_0) and the out-of-range tall column ----------
k_tall = max(cases, key=lambda k: summ["cases"][k]["H0"] / summ["cases"][k]["W"])
anim_cases = [cases[0], k_tall] if k_tall != cases[0] else [cases[0]]
zz = {k: np.load(os.path.join(SCR, f"rollout_{k}.npz")) for k in anim_cases}
nt = min(z["true"].shape[0] for z in zz.values())
frames = []
for k in range(0, nt, 2):
    f, a = plt.subplots(len(anim_cases), 2, figsize=(6.4, 2.6 * len(anim_cases)), dpi=100, squeeze=False)
    for row, kc in enumerate(anim_cases):
        tr, pr = zz[kc]["true"], zz[kc]["pred"]
        tag = "in training range" if kc != k_tall else "taller than any training column"
        for aa, p, ttl, col in ((a[row, 0], tr, f"{kc} DEM ({tag})", "C0"), (a[row, 1], pr, f"{kc} GNS rollout", "C1")):
            aa.scatter(p[k, :, 0], p[k, :, 1], s=4, c=col)
            aa.set_xlim(0, 0.45); aa.set_ylim(0, 0.33); aa.set_aspect("equal")
            aa.set_title(ttl, fontsize=7); aa.tick_params(labelsize=6)
        a[row, 0].set_ylabel("y (box units)", fontsize=7)
    a[-1, 0].set_xlabel("x (box units)", fontsize=7); a[-1, 1].set_xlabel("x (box units)", fontsize=7)
    f.suptitle(f"gns-gnn-simulator (geoelements/gns) vs numba DEM, t = {k * DT_FRAME:.2f}", fontsize=8)
    f.tight_layout()
    f.canvas.draw()
    img = np.asarray(f.canvas.buffer_rgba())[:, :, :3].copy()
    frames.append(img)
    plt.close(f)
k_anim = ",".join(anim_cases)
h, w = frames[0].shape[:2]
h2, w2 = h - h % 2, w - w % 2
frames = [fr[:h2, :w2] for fr in frames]
imageio.mimsave(os.path.join(OUT, "gns_rollout.gif"), frames, duration=1 / 12, loop=0)
os.environ.setdefault("IMAGEIO_FFMPEG_EXE", imageio_ffmpeg.get_ffmpeg_exe())
wr = imageio.get_writer(os.path.join(OUT, "gns_rollout.mp4"), fps=12, codec="libx264",
                        pixelformat="yuv420p", macro_block_size=1, ffmpeg_params=["-crf", "28"])
for fr in frames:
    wr.append_data(fr)
wr.close()
print("animated", k_anim, len(frames), "frames", w2, "x", h2)
