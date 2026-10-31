#!/usr/bin/env python3
"""Cellular automata for avalanches and intermittent feeder outflow.

(a) 1D Oslo rice-pile model (Christensen et al. 1996): critical slopes drawn at
    random from {1, 2} -> avalanche size distribution, finite-size scaling and the
    self-organised mean slope (an angle-of-repose analog).
(b) Tilted-feeder CA (self-written toy): a 1D column-height lattice standing for
    the powder between the end of the auger flight and the outlet lip, tilted by
    the doser angle, fed one parcel per rotation increment.  A column topples
    when its local surface slope exceeds a threshold; static (resting) columns
    need s_f + c, columns already moving in an avalanche only s_f.  c is the
    cohesion-like start/stop gap (tan theta_start - tan theta_stop).  Outputs:
    fraction of increments with zero outflow (the doser's I_stop), burst sizes,
    afterflow after the drive stops.

Usage:  OMP_NUM_THREADS=1 NUMBA_NUM_THREADS=1 python run.py
Frames/animations scratch: /tmp/sims-scratch/ca-avalanche
"""
import json
import os
import time

import numpy as np
from numba import njit

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon

OUT = os.path.dirname(os.path.abspath(__file__))
SCR = "/tmp/sims-scratch/ca-avalanche"
os.makedirs(SCR, exist_ok=True)
T0 = time.time()


# =========================================================== (a) Oslo model
@njit(cache=False)
def oslo(L, n_add, n_warm, seed):
    np.random.seed(seed)
    z = np.zeros(L, np.int64)
    zc = np.empty(L, np.int64)
    for i in range(L):
        zc[i] = 1 + (np.random.random() < 0.5)
    stack = np.empty(L + 2, np.int64)
    inst = np.zeros(L, np.bool_)
    sizes = np.zeros(n_add, np.int64)
    h1 = np.zeros(n_add, np.int64)
    for k in range(n_warm + n_add):
        z[0] += 1
        s = 0
        top = 0
        if z[0] > zc[0]:
            stack[0] = 0
            top = 1
            inst[0] = True
        while top > 0:
            top -= 1
            i = stack[top]
            inst[i] = False
            if z[i] <= zc[i]:
                continue
            s += 1
            if i == 0:
                z[0] -= 2
                z[1] += 1
            elif i == L - 1:
                z[L - 1] -= 1
                z[L - 2] += 1
            else:
                z[i] -= 2
                z[i - 1] += 1
                z[i + 1] += 1
            zc[i] = 1 + (np.random.random() < 0.5)
            for j in (i - 1, i, i + 1):
                if 0 <= j < L and (not inst[j]) and z[j] > zc[j]:
                    stack[top] = j
                    top += 1
                    inst[j] = True
        if k >= n_warm:
            sizes[k - n_warm] = s
            h1[k - n_warm] = z.sum()
    return sizes, h1


def logbin_pdf(s, nb=40):
    s = s[s > 0]
    edges = np.unique(np.floor(np.logspace(0, np.log10(s.max() + 1), nb)).astype(np.int64))
    edges = np.append(edges, edges[-1] + 1)
    cnt, _ = np.histogram(s, bins=edges)
    widths = np.diff(edges)
    pdf = cnt / widths / s.size
    centers = np.sqrt(edges[:-1] * np.maximum(edges[1:] - 1, edges[:-1]))
    m = cnt > 0
    return centers[m], pdf[m]


# ====================================================== (b) tilted feeder CA
MEM = 3   # sweeps a column stays "moving" (cohesion broken) after it toppled


@njit(cache=False)
def _sweep(h, noise, active, mv, L, nasp, t, s_f, c, sigma):
    """One synchronous sweep; returns (parcels out over the lip, any toppling).
    active[x] > 0: column x toppled within the last MEM sweeps, so it is moving and
    needs only s_f; active[x] == 0: at rest, needs s_f + c."""
    for x in range(L):
        mv[x] = 0
        if h[x] <= 0:
            continue
        Hx = h[x] / nasp - t * x
        if x < L - 1:
            Hf = h[x + 1] / nasp - t * (x + 1)
        else:
            Hf = -t * (x + 1)                      # outlet lip at base level
        thr = s_f + noise[x]
        if active[x] == 0:
            thr += c
        sf = Hx - Hf
        sb = -1e9
        if x > 0:                                   # x = 0 is backed by the flight
            sb = Hx - (h[x - 1] / nasp - t * (x - 1))
        if sf > thr and sf >= sb:
            mv[x] = 1
        elif sb > thr:
            mv[x] = -1
    nout = 0
    any_t = False
    for x in range(L):
        if mv[x] != 0:
            any_t = True
            h[x] -= 1
            if mv[x] == 1:
                if x == L - 1:
                    nout += 1
                else:
                    h[x + 1] += 1
            else:
                h[x - 1] += 1
            noise[x] = sigma * np.random.randn()
    for x in range(L):
        if active[x] > 0:
            active[x] -= 1
    for x in range(L):
        if mv[x] != 0:
            active[x] = MEM            # only a column that itself moved loses its cohesion
    return nout, any_t


@njit(cache=False)
def feeder(L, nasp, t, s_f, c, sigma, n_in, K, n_warm, n_meas, n_stop, seed, n_rec):
    np.random.seed(seed)
    h = np.zeros(L, np.int64)
    noise = np.empty(L)
    for x in range(L):
        noise[x] = sigma * np.random.randn()
    active = np.zeros(L, np.int64)
    mv = np.zeros(L, np.int64)
    out = np.zeros(n_meas, np.int64)
    mass = np.zeros(n_meas, np.int64)
    rec = np.zeros((n_rec, L), np.int64)
    after = np.zeros(n_stop)
    after_sweeps = np.zeros(n_stop)
    stop_every = max(n_meas // max(n_stop, 1), 1)
    ks = 0
    for inc in range(n_warm + n_meas):
        h[0] += n_in
        nout = 0
        if K > 0:                      # continuous rotation: K sweeps per increment
            for sw in range(K):
                o, a = _sweep(h, noise, active, mv, L, nasp, t, s_f, c, sigma)
                nout += o
        else:                          # incremental dosing: relax to rest every increment
            quiet = 0
            nsw = 0
            while nsw < 200000:
                o, a = _sweep(h, noise, active, mv, L, nasp, t, s_f, c, sigma)
                nout += o
                nsw += 1
                if a:
                    quiet = 0
                else:
                    quiet += 1
                    if quiet >= MEM:
                        break
        if inc >= n_warm:
            j = inc - n_warm
            out[j] = nout
            mass[j] = h.sum()
            if j < n_rec:
                rec[j, :] = h
            if j % stop_every == 0 and ks < n_stop:
                # drive stops here: relax a copy until quiescent, count afterflow
                h2 = h.copy()
                n2 = noise.copy()
                a2 = active.copy()
                m2 = np.zeros(L, np.int64)
                tot = 0
                nsw = 0
                quiet = 0
                while nsw < 200000:
                    o, a = _sweep(h2, n2, a2, m2, L, nasp, t, s_f, c, sigma)
                    tot += o
                    nsw += 1
                    if not a:
                        quiet += 1
                        if quiet >= MEM:
                            break
                    else:
                        quiet = 0
                after[ks] = tot
                after_sweeps[ks] = nsw
                ks += 1
    return out, mass, rec, after, after_sweeps


def burst_sizes(out):
    sizes = []
    cur = 0
    for o in out:
        if o > 0:
            cur += o
        elif cur > 0:
            sizes.append(cur)
            cur = 0
    if cur > 0:
        sizes.append(cur)
    return np.array(sizes)


# ================================================================== run (a)
res = {}
tim = {}
t1 = time.time()
Ls = [32, 64, 128, 256, 512]
oslo_res = {}
import sys
OSLO_CACHE = os.path.join(SCR, "oslo_cache.npz")
reuse = "--reuse-oslo" in sys.argv and os.path.exists(OSLO_CACHE)
if reuse:
    cache = np.load(OSLO_CACHE)
for L in Ls:
    n_add = 1_000_000
    if reuse:
        sizes, h1 = cache[f"s{L}"], cache[f"h{L}"]
    else:
        sizes, h1 = oslo(L, n_add, 3 * L * L, 1234 + L)
    zbar = h1 / L
    oslo_res[L] = (sizes, zbar)
    res.setdefault("oslo", {})[f"L={L}"] = {
        "mean_avalanche_size": float(sizes.mean()),
        "max_avalanche_size": int(sizes.max()),
        "mean_slope": float(zbar.mean()),
        "std_slope": float(zbar.std()),
        "fraction_zero_size_avalanches": float(np.mean(sizes == 0)),
    }
tim["oslo_s"] = time.time() - t1
if not reuse:
    np.savez_compressed(OSLO_CACHE, **{f"s{L}": oslo_res[L][0] for L in Ls},
                        **{f"h{L}": (oslo_res[L][1] * L).astype(np.int64) for L in Ls})
# exponent fit on the largest system, scaling region 10 <= s <= L^2.25/30
Lf = Ls[-1]
xc, pc = logbin_pdf(oslo_res[Lf][0])
m = (xc >= 10) & (xc <= Lf ** 2.25 / 30)
tau_fit, logA = np.polyfit(np.log(xc[m]), np.log(pc[m]), 1)
tau_fit = -tau_fit
# fit of mean slope vs L: z(L) = z_inf (1 + a L^-w), with w = 0.45 fixed? -> simple: fit z_inf + a L^-w
from scipy.optimize import curve_fit
Larr = np.array(Ls, float)
zm = np.array([oslo_res[L][1].mean() for L in Ls])
zs = np.array([oslo_res[L][1].std() for L in Ls])
try:
    popt, _ = curve_fit(lambda L, zi, a, w: zi + a * L ** (-w), Larr, zm, p0=(1.73, 0.1, 0.6), maxfev=20000)
    z_inf = float(popt[0]); w_fit = float(popt[2])
except Exception as e:  # noqa
    z_inf, w_fit = float("nan"), float("nan")
sig_slope, _ = np.polyfit(np.log(Larr), np.log(zs), 1)
res["oslo_fit"] = {"tau_s_fit_L512": float(tau_fit), "fit_range": [10, float(Lf ** 2.25 / 30)],
                   "literature_tau_s": 1.55, "literature_D": 2.25,
                   "mean_slope_extrapolated_z_inf": z_inf, "correction_exponent": w_fit,
                   "literature_z_inf": 1.7326,
                   "slope_fluctuation_scaling_exponent": float(sig_slope)}
print("oslo", res["oslo_fit"], tim, flush=True)

# ================================================================== run (b)
FE = dict(L=40, nasp=5.0, s_f=np.tan(np.radians(34.0)), sigma=0.10, n_in=1,
          n_warm=20000, n_meas=40000, n_stop=100)
tilts = [0.0, 22.5, 27.5, 36.0, 45.0]
cs = [0.0, 0.05, 0.1, 0.2, 0.3, 0.45, 0.6, 0.8, 1.0]
t1 = time.time()


def run_feeder(ti, ci, K, seed, n_meas=None, n_rec=1, n_stop=None):
    return feeder(FE["L"], FE["nasp"], np.tan(np.radians(ti)), FE["s_f"], ci, FE["sigma"], FE["n_in"], K,
                  FE["n_warm"], n_meas or FE["n_meas"], n_stop or FE["n_stop"], seed, n_rec)


def summarise(out, mass, after):
    bs = burst_sizes(out)
    half = out.size // 2
    return dict(
        I_stop=float(np.mean(out == 0)),
        I_stop_first_half=float(np.mean(out[:half] == 0)),
        I_stop_second_half=float(np.mean(out[half:] == 0)),
        mean_out=float(out.mean()),
        cv_out=float(out.std() / max(out.mean(), 1e-12)),
        mean_burst=float(bs.mean()) if bs.size else 0.0,
        max_burst=int(bs.max()) if bs.size else 0,
        afterflow_mean=float(after.mean()),
        mean_mass=float(mass.mean()),
        mass_drift_rel=float((mass[half:].mean() - mass[:half].mean()) / max(mass.mean(), 1)),
    )


# (b1) incremental dosing (relax to rest each increment): I_stop vs c and tilt
grid = {}
for ti in tilts:
    for ci in cs:
        out, mass, rec, after, asw = run_feeder(ti, ci, 0, 7 + int(100 * ci) + int(10 * ti), n_stop=1)
        grid[(ti, ci)] = summarise(out, mass, after)
res["feeder_incremental"] = {f"tilt={ti}deg,c={ci}": v for (ti, ci), v in grid.items()}
tim["feeder_scan_s"] = time.time() - t1
print("feeder scan", tim, flush=True)

# (b2) drive-rate scan: K sweeps of relaxation per increment (K small = fast rotation)
t1 = time.time()
Ks = [2, 5, 10, 20, 50, 100, 300, 0]
cs_k = [0.0, 0.3, 0.8]
TI_K = 22.5
kscan = {}
for ci in cs_k:
    for K in Ks:
        out, mass, rec, after, asw = run_feeder(TI_K, ci, K, 300 + K + int(100 * ci), n_meas=20000, n_stop=100)
        kscan[(ci, K)] = summarise(out, mass, after)
res["feeder_drive_rate_tilt22.5"] = {f"c={ci},K={'relax' if K == 0 else K}": v for (ci, K), v in kscan.items()}
tim["feeder_kscan_s"] = time.time() - t1

# seed repeatability at one point
rep = []
for sd in range(5):
    out, *_ = run_feeder(22.5, 0.3, 0, 1000 + sd, n_meas=40000, n_stop=1)
    rep.append(float(np.mean(out == 0)))
res["feeder_seed_repeat_incremental_tilt22.5_c0.3"] = {"I_stop": rep, "std": float(np.std(rep))}

# runs for the animation (incremental dosing)
N_REC = 120
TI_AN = 22.5
anim = {}
for ci in [0.0, 0.6]:
    out, mass, rec, after, asw = run_feeder(TI_AN, ci, 0, 99, n_meas=4000, n_rec=N_REC, n_stop=1)
    anim[ci] = (out, rec)
print("feeder done", tim, flush=True)

# ================================================================== figure
cols = ["#1b6ca8", "#2a9d8f", "#e9a23b", "#c8553d", "#6d597a"]
fig, ax = plt.subplots(2, 3, figsize=(14.5, 8.4))
a = ax[0, 0]
for cl, L in zip(cols, Ls):
    xc_, pc_ = logbin_pdf(oslo_res[L][0])
    a.loglog(xc_, pc_, "o-", ms=3, lw=0.8, color=cl, label=f"L = {L}")
xx = np.logspace(1, np.log10(Lf ** 2.25 / 30), 20)
a.loglog(xx, 3 * np.exp(logA) * xx ** (-tau_fit), "k--", lw=1.2, label=f"fit (L=512): τ = {tau_fit:.2f}")
a.set_xlabel("avalanche size s (topplings)")
a.set_ylabel("P(s) (–)")
a.set_title("(a) Oslo rice pile: avalanche size distribution", fontsize=9.5)
a.legend(fontsize=7.5)

a = ax[0, 1]
for cl, L in zip(cols, Ls):
    xc_, pc_ = logbin_pdf(oslo_res[L][0])
    a.loglog(xc_ / L ** 2.25, pc_ * xc_ ** 1.55, "o-", ms=3, lw=0.8, color=cl, label=f"L = {L}")
a.set_xlabel("s / L^D, D = 2.25 (–)")
a.set_ylabel("s^τ P(s), τ = 1.55 (–)")
a.set_title("(b) finite-size scaling collapse (literature D, τ)", fontsize=9.5)
a.legend(fontsize=7.5)

a = ax[0, 2]
a.errorbar(Larr, zm, yerr=zs, fmt="o", color=cols[0], capsize=3, label="mean slope ± std (time series)")
if np.isfinite(z_inf):
    Lff = np.logspace(np.log10(20), np.log10(2000), 50)
    a.plot(Lff, popt[0] + popt[1] * Lff ** (-popt[2]), "--", color=cols[0], lw=1,
           label=f"fit z∞ + a L^-w: z∞ = {z_inf:.3f}")
a.axhline(1, color="0.5", lw=0.8, ls=":")
a.axhline(2, color="0.5", lw=0.8, ls=":")
a.text(25, 1.03, "critical slope z_c = 1", fontsize=7)
a.text(25, 1.93, "critical slope z_c = 2", fontsize=7)
a.set_xscale("log")
a.set_xlabel("pile length L (sites)")
a.set_ylabel("self-organised mean slope ⟨z⟩ (grains/site)")
a.set_title("(c) angle-of-repose analog vs system size", fontsize=9.5)
a.legend(fontsize=7.5, loc="center right")

a = ax[1, 0]
cols5 = cols + ["#333333"]
for cl, ti in zip(cols5, tilts):
    a.plot(cs, [grid[(ti, ci)]["I_stop"] for ci in cs], "o-", color=cl, label=f"tilt {ti:g}°")
a.set_xlabel("cohesion-like start/stop gap c = tanθ_start − tanθ_stop (–)")
a.set_ylabel("I_stop: fraction of zero-outflow increments (–)")
a.set_title("(d) feeder CA, incremental dosing: I_stop vs cohesion, tilt", fontsize=9.5)
a.set_ylim(-0.03, 1.03)
a.legend(fontsize=7.5)

a = ax[1, 1]
for cl, ti in zip(cols5, tilts):
    a.semilogy(cs, [max(grid[(ti, ci)]["mean_burst"], 0.5) for ci in cs], "s-", color=cl, label=f"tilt {ti:g}°")
a.set_xlabel("cohesion-like start/stop gap c (–)")
a.set_ylabel("mean burst size (parcels = increments' worth)")
a.set_title("(e) mass freed per outflow event (bursts)", fontsize=9.5)
a.legend(fontsize=7.5)

a = ax[1, 2]
Kplot = [K if K > 0 else 3000 for K in Ks]
a2 = a.twinx()
for cl, ci in zip([cols[1], cols[2], cols[3]], cs_k):
    a.semilogx(Kplot, [kscan[(ci, K)]["I_stop"] for K in Ks], "o-", color=cl, label=f"I_stop, c = {ci:g}")
    a2.semilogx(Kplot, [kscan[(ci, K)]["afterflow_mean"] for K in Ks], "^:", color=cl, ms=4,
                label=f"afterflow, c = {ci:g}")
a.set_xticks([2, 10, 100, 3000])
a.set_xticklabels(["2", "10", "100", "relax"])
a.set_xlabel("relaxation sweeps per increment (fast rotation → slow, incremental)")
a.set_ylabel("I_stop (–), solid")
a2.set_ylabel("afterflow after stop (parcels), dotted")
a.set_title(f"(f) drive-rate dependence, tilt {TI_K:g}°", fontsize=9.5)
a.set_ylim(-0.03, 1.03)
h1_, l1_ = a.get_legend_handles_labels()
h2_, l2_ = a2.get_legend_handles_labels()
a.legend(h1_ + h2_, l1_ + l2_, fontsize=6.5, loc="center left")
fig.suptitle("Cellular automata (self-written, numba): Oslo rice pile and a tilted-feeder outflow toy",
             fontsize=11)
fig.tight_layout()
fig.savefig(os.path.join(OUT, "ca_avalanche.png"), dpi=90)
plt.close(fig)

# ================================================================== animation
t1 = time.time()
import imageio.v2 as iio2
import imageio.v3 as iio3

nasp, Lc, tt = FE["nasp"], FE["L"], np.tan(np.radians(TI_AN))
fig = plt.figure(figsize=(6.4, 4.8), dpi=100)
gs = fig.add_gridspec(2, 2, height_ratios=[1.35, 1])
axs = [fig.add_subplot(gs[0, 0]), fig.add_subplot(gs[0, 1]), fig.add_subplot(gs[1, :])]
polys = []
ttl = []
hmax = max(anim[0.0][1].max(), anim[0.6][1].max()) / nasp
for k, ci in enumerate([0.0, 0.6]):
    a = axs[k]
    p = Polygon(np.zeros((3, 2)), closed=True, fc="#d9b26f", ec="#8a6a2f", lw=0.6)
    a.add_patch(p)
    polys.append(p)
    a.plot([0, Lc], [0, -tt * Lc], "k-", lw=1.2)
    a.plot([0, 0], [0, hmax + 1], "k-", lw=2.5)
    a.text(0.5, hmax + 0.3, "flight", fontsize=7)
    a.annotate("", xy=(Lc + 1.5, -tt * Lc - 3), xytext=(Lc + 0.2, -tt * Lc), arrowprops=dict(arrowstyle="->"))
    a.set_xlim(-1, Lc + 3)
    a.set_ylim(-tt * Lc - 4, hmax + 1.5)
    a.set_xlabel("distance along trough (cells)", fontsize=7)
    a.set_ylabel("elevation (cells)", fontsize=7)
    a.tick_params(labelsize=6)
    ttl.append(a.set_title("", fontsize=8))
a = axs[2]
ln = []
for ci, cl in zip([0.0, 0.6], ["#2a9d8f", "#c8553d"]):
    l_, = a.step([], [], where="mid", color=cl, lw=1.2, label=f"c = {ci:g}")
    ln.append(l_)
a.set_xlim(0, N_REC)
a.set_ylim(-0.3, max(anim[0.0][0][:N_REC].max(), anim[0.6][0][:N_REC].max()) + 1)
a.set_xlabel("rotation increment", fontsize=7)
a.set_ylabel("outflow (parcels)", fontsize=7)
a.tick_params(labelsize=6)
a.legend(fontsize=7, loc="upper left")
fig.suptitle(f"Cellular automaton (self-written numba): tilted feeder, tilt {TI_AN:g}°", fontsize=9)
fig.tight_layout()
frames = []
for f in range(N_REC):
    for k, ci in enumerate([0.0, 0.6]):
        h = anim[ci][1][f]
        top = []
        for x in range(Lc):
            top += [(x, -tt * x + h[x] / nasp), (x + 1, -tt * (x + 1) + h[x] / nasp)]
        verts = top + [(Lc, -tt * Lc), (0, 0)]
        polys[k].set_xy(np.array(verts))
        o = anim[ci][0]
        ttl[k].set_text(f"c = {ci:g}  inc {f:3d}  out {o[f]}  I_stop so far {np.mean(o[:f + 1] == 0):.2f}")
    for l_, ci in zip(ln, [0.0, 0.6]):
        l_.set_data(np.arange(f + 1), anim[ci][0][:f + 1])
    fig.canvas.draw()
    frames.append(np.asarray(fig.canvas.buffer_rgba())[:, :, :3].copy())
plt.close(fig)
gif = os.path.join(OUT, "ca_feeder.gif")
iio3.imwrite(gif, frames, duration=83, loop=0)
mp4 = os.path.join(OUT, "ca_feeder.mp4")
w = iio2.get_writer(mp4, fps=12, codec="libx264", pixelformat="yuv420p", macro_block_size=16,
                    ffmpeg_params=["-crf", "28"])
for fr in frames:
    w.append_data(fr)
w.close()
tim["animation_s"] = time.time() - t1

wall = time.time() - T0
res["feeder_params"] = {k: (float(v) if isinstance(v, (float, np.floating)) else v) for k, v in FE.items()}
res["feeder_params"]["tilts_deg"] = tilts
res["feeder_params"]["c_values"] = cs
result = {
    "id": "ca-avalanche",
    "method": "cellular automata: 1D Oslo rice pile (avalanche statistics, self-organised slope) and a "
              "tilted-feeder outflow CA with a cohesion-like start/stop threshold gap (I_stop, afterflow)",
    "code": "self-written Python + numba",
    "version": f"numpy {np.__version__}",
    "status": "ran",
    "wall_s": round(wall, 1),
    "cores": 1,
    "key_results": res,
    "notes": "Lattice toy models: lengths in sites/cells, mass in parcels. Timings: "
             + json.dumps({k: round(v, 1) for k, v in tim.items()})
             + " Feeder rule: only a column that itself toppled is 'moving' (needs s_f) for 3 sweeps; an earlier "
               "version that also activated neighbours made c irrelevant and was discarded. I_stop ~ 1 - inflow/mean "
               "burst in incremental mode, so absolute I_stop depends on parcel size; trends with c, tilt and drive "
               "rate are the result.",
}
with open(os.path.join(OUT, "result.json"), "w") as f:
    json.dump(result, f, indent=1)
print("wall", wall, tim)
for ti in tilts:
    print(ti, [(ci, round(grid[(ti, ci)]["I_stop"], 3), round(grid[(ti, ci)]["mean_burst"], 1),
                round(grid[(ti, ci)]["mean_out"], 3), round(grid[(ti, ci)]["mass_drift_rel"], 3)) for ci in cs])
for ci in cs_k:
    print("K-scan c", ci, [(K, round(kscan[(ci, K)]["I_stop"], 3), round(kscan[(ci, K)]["afterflow_mean"], 1))
                         for K in Ks])
