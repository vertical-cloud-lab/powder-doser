"""Post-process the LAMMPS simple-shear runs: mu(I) and the cohesive yield line.

Usage: python analyze.py <scratch dir with stress_*.dat, dump_*.lammpstrj> <this run dir>
Writes result.json, shear_mu_I.png, shear_animation.gif/.mp4 into <this run dir>.
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
RHO, D, DT, NB, NPREP = 2165.0, 0.425e-3, 1.0e-5, 100, 10000
STAGES_BY_TAG = {  # (rate 1/s, P Pa, strain): in.shear defaults (noncoh) and the reduced list in run.sh (jkr)
    "noncoh": [(2.5, 100.0, 2.5), (7.5, 100.0, 2.0), (25.0, 100.0, 3.0), (75.0, 100.0, 4.0),
               (150.0, 100.0, 5.0), (2.5, 200.0, 1.5), (2.5, 50.0, 1.5), (2.5, 25.0, 1.5)],
    "jkr": [(2.5, 100.0, 2.0), (25.0, 100.0, 2.0), (150.0, 100.0, 4.0), (2.5, 200.0, 1.0), (2.5, 25.0, 1.0)]}
STAGES = STAGES_BY_TAG["noncoh"]
GAMMA_JKR = 8.5e-3  # J/m^2, as in run.sh
R_EFF = D / 4.0      # effective radius of two equal grains
MG = RHO * math.pi / 6 * D**3 * 9.81
F_PULL = 3 * math.pi * GAMMA_JKR * R_EFF  # nominal JKR pull-off force


def stage_windows(stages=None):
    """Step windows (start, end) of each stage, and the averaging window (second half;
    last 1.0 strain for the first stage, which includes the start-up transient)."""
    s0 = NPREP
    out = []
    for k, (rate, p, strain) in enumerate(stages or STAGES):
        nblk = math.ceil(strain / (rate * DT) / NB)
        n = nblk * NB
        frac = 1.0 / strain if k == 0 else 0.5
        out.append((s0, s0 + n, s0 + n - int(frac * n)))
        s0 += n
    return out


def load(tag):
    f = OUT / f"stress_{tag}.dat"
    if not f.exists():
        return None
    a = np.loadtxt(f, comments="#")
    return a  # step rate P Pyy Pxy phi temp


def summarise(a, stages):
    rows = []
    for (rate, p, strain), (s0, s1, sa) in zip(stages, stage_windows(stages)):
        m = (a[:, 0] > sa) & (a[:, 0] <= s1)
        if m.sum() < 4:
            rows.append(None)
            continue
        pyy, tau, phi = a[m, 3], -a[m, 4], a[m, 5]
        # standard error of the mean from 4 consecutive blocks
        blocks = np.array_split(np.arange(m.sum()), 4)
        mu_b = [tau[b].mean() / pyy[b].mean() for b in blocks]
        P, T = pyy.mean(), tau.mean()
        rows.append(dict(rate=rate, P_target=p, Pyy=P, tau=T, mu=T / P,
                         mu_err=float(np.std(mu_b, ddof=1) / 2.0),
                         I=rate * D / math.sqrt(P / RHO), phi=phi.mean(),
                         tau_err=float(np.std([tau[b].mean() for b in blocks], ddof=1) / 2.0),
                         n_samples=int(m.sum())))
    return rows


def jop_fit(I, mu):
    from scipy.optimize import curve_fit
    f = lambda x, ms, m2, i0: ms + (m2 - ms) / (1 + i0 / x)
    try:
        p, _ = curve_fit(f, I, mu, p0=[mu.min(), mu.max() + 0.1, 0.1], maxfev=20000)
        return p, f
    except Exception as exc:  # noqa
        print("mu(I) fit failed:", exc)
        return None, f


res = {}
for tag in ("noncoh", "jkr"):
    a = load(tag)
    if a is not None:
        res[tag] = summarise(a, STAGES_BY_TAG[tag])

fig, ax = plt.subplots(1, 2, figsize=(10, 4.2))
cols = {"noncoh": "#1f77b4", "jkr": "#d62728"}
labels = {"noncoh": "non-cohesive (Hertz-Mindlin)",
          "jkr": f"JKR, $\\gamma$ = {GAMMA_JKR*1e3:.1f} mJ/m$^2$ (Bo$_g$ $\\approx$ {F_PULL/MG:.0f})"}
key = {}
for tag, rows in res.items():
    st = STAGES_BY_TAG[tag]
    r100 = [r for r, x in zip(rows, st) if r and x[1] == 100.0]
    I = np.array([r["I"] for r in r100]); mu = np.array([r["mu"] for r in r100])
    err = np.array([r["mu_err"] for r in r100])
    ax[0].errorbar(I, mu, yerr=err, fmt="o", color=cols[tag], label=labels[tag], capsize=3)
    p, f = jop_fit(I, mu) if len(I) >= 4 else (None, None)
    if p is not None and not (0 < p[0] < p[1] < 3 and 0 < p[2] < 10):
        p = None  # reject unphysical fits
    if p is not None:
        xx = np.logspace(np.log10(I.min() / 1.5), np.log10(I.max() * 1.5), 100)
        ax[0].plot(xx, f(xx, *p), "-", color=cols[tag], lw=1)
    # yield line at the lowest rate: stages 0 (P=100), 5, 6, 7
    low = sorted([r for r, x in zip(rows, st) if r and x[0] == 2.5], key=lambda r: r["Pyy"])
    P = np.array([r["Pyy"] for r in low]); T = np.array([r["tau"] for r in low])
    Te = np.array([r["tau_err"] for r in low])
    slope, icpt = np.polyfit(P, T, 1)
    ax[1].errorbar(P, T, yerr=Te, fmt="o", color=cols[tag], capsize=3, label=labels[tag])
    xx = np.linspace(0, P.max() * 1.1, 50)
    ax[1].plot(xx, slope * xx + icpt, "-", color=cols[tag], lw=1)
    key[tag] = dict(
        stages=rows,
        mu_I_fit_Jop2006=(dict(mu_s=float(p[0]), mu_2=float(p[1]), I0=float(p[2])) if p is not None else None),
        yield_line_low_rate=dict(rate_per_s=2.5, slope_mu=float(slope), intercept_Pa=float(icpt),
                                 points=[dict(Pyy=float(a), tau=float(b)) for a, b in zip(P, T)]))
ax[0].set_xscale("log")
ax[0].set_xlabel("inertial number I = $\\dot\\gamma d/\\sqrt{P/\\rho_p}$ (-)")
ax[0].set_ylabel("effective friction $\\mu = \\tau/P$ (-)")
ax[0].set_title("(a) $\\mu(I)$ at P = 100 Pa (lines: Jop et al. 2006 fit)", fontsize=10)
ax[0].legend(fontsize=8, loc="upper left")
ax[1].set_xlabel("normal stress $P_{yy}$ (Pa)")
ax[1].set_ylabel("shear stress $\\tau$ (Pa)")
ax[1].set_title("(b) steady shear stress at $\\dot\\gamma$ = 2.5 s$^{-1}$ (I $\\leq$ 0.01)", fontsize=10)
ax[1].set_xlim(left=0); ax[1].set_ylim(bottom=0)
ax[1].legend(fontsize=8, loc="upper left")
fig.suptitle("LAMMPS GRANULAR periodic simple shear, 1500 polydisperse salt spheres (0.36-0.49 mm)", fontsize=10)
fig.tight_layout()
fig.savefig(HERE / "shear_mu_I.png", dpi=110)
print(json.dumps({k: {kk: vv for kk, vv in v.items() if kk != "stages"} for k, v in key.items()}, indent=1))
json.dump(dict(key=key, F_pulloff_N=F_PULL, weight_N=MG, Bo_g=F_PULL / MG,
               Coh_at_100Pa=F_PULL / (100 * D**2), Coh_at_25Pa=F_PULL / (25 * D**2)),
          open(HERE / "analysis_summary.json", "w"), indent=1)


# ---------------- animation from the non-cohesive dump (first two stages)
def read_dump(fn, max_step=None):
    frames = []
    with open(fn) as fh:
        while True:
            line = fh.readline()
            if not line:
                break
            if line.startswith("ITEM: TIMESTEP"):
                step = int(fh.readline())
                fh.readline(); n = int(fh.readline())
                hdr = fh.readline()
                b = [list(map(float, fh.readline().split())) for _ in range(3)]
                cols = fh.readline().split()[2:]
                arr = np.array([fh.readline().split() for _ in range(n)], dtype=float)
                if max_step and step > max_step:
                    break
                frames.append((step, b, dict(zip(cols, arr.T))))
    return frames


import os
dump = OUT / "dump_noncoh.lammpstrj"
if dump.exists() and not os.environ.get("NOANIM"):
    import imageio.v2 as imageio
    w = stage_windows()
    frames = read_dump(dump, max_step=w[1][1])
    frames = [f for f in frames if f[0] >= NPREP]
    ids0 = frames[0][2]["id"]; x0 = frames[0][2]["x"]
    band = {int(i) for i, x in zip(ids0, x0) if (x % 0.0047) < 0.0012}
    imgs = []
    for step, b, d in frames:
        xlo_b, xhi_b, xy = b[0]; ylo, yhi = b[1][:2]; zlo, zhi = b[2][:2]
        xlo = xlo_b - min(0.0, xy); xhi = xhi_b - max(0.0, xy)
        lx, ly, lz = xhi - xlo, yhi - ylo, zhi - zlo
        sl = np.abs(d["z"] - (zlo + lz / 2)) < 0.6e-3
        fig, axx = plt.subplots(figsize=(6.0, 4.2), dpi=100)
        cc = np.array(["#d62728" if int(i) in band else "#9ecae1" for i in d["id"][sl]])
        axx.scatter(d["x"][sl] * 1e3, d["y"][sl] * 1e3, s=(d["diameter"][sl] * 1e3 * 22) ** 2,
                    c=cc, edgecolors="k", linewidths=0.2)
        px = np.array([xlo, xhi, xhi + xy, xlo + xy, xlo]) * 1e3
        py = np.array([ylo, ylo, yhi, yhi, ylo]) * 1e3
        axx.plot(px, py, "k-", lw=0.8)
        stage = max(i for i, s in enumerate(w) if step >= s[0])
        rate = STAGES[stage][0]
        axx.set_aspect("equal"); axx.set_xlim(-3, 9); axx.set_ylim(-0.3, ly * 1e3 + 0.3)
        axx.set_xlabel("x, flow direction (mm)"); axx.set_ylabel("y, gradient direction (mm)")
        axx.set_title(f"LAMMPS GRANULAR simple shear (Lees-Edwards), slice |z-z_c|<0.6 mm\n"
                      f"t = {(step-NPREP)*DT:.3f} s, shear rate {rate:g} 1/s, P = 100 Pa", fontsize=9)
        fig.tight_layout()
        fig.canvas.draw()
        imgs.append(np.asarray(fig.canvas.buffer_rgba())[..., :3].copy())
        plt.close(fig)
    imageio.mimsave(HERE / "shear_animation.gif", imgs, duration=1 / 10, loop=0)
    import imageio_ffmpeg  # noqa
    wr = imageio.get_writer(HERE / "shear_animation.mp4", fps=10, codec="libx264",
                            pixelformat="yuv420p", macro_block_size=8)
    for im in imgs:
        wr.append_data(im)
    wr.close()
    print("animation frames:", len(imgs))
