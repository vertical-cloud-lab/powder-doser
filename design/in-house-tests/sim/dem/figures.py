"""Figures and short animations for the in-house test DEM runs (all simulated).

usage: python figures.py [t1 t7 t2 t5 t3 t8 t9 anim all]
Reads results/*.json and frames/*.npz; writes figures/*.png and figures/*.mp4.
"""
import glob
import json
import math
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import demlib as L  # noqa: E402

C = L.COLORS
GREY = "#9a9a96"


def res(name):
    p = os.path.join(HERE, "results", name + ".json")
    return json.load(open(p)) if os.path.exists(p) else None


def save(fig, name):
    fig.savefig(os.path.join(HERE, "figures", name), dpi=130, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def tag(ax, s):
    ax.text(0.0, 1.02, s, transform=ax.transAxes, fontsize=9, fontweight="bold", color=L.INK, va="bottom")


# ---------------------------------------------------------------- test 1
def fig_t1():
    runs = {k: res(f"t1_heap_{k}") for k in ("d12_dry", "d12_coh", "d20_dry", "d20_coh", "d30_dry")}
    runs = {k: v for k, v in runs.items() if v}
    if not runs:
        return
    fig, axs = plt.subplots(2, 2, figsize=(11, 7.6))
    ax = axs[0, 0]
    ls = {"d12": ":", "d20": "-", "d30": "--"}
    for k, r in runs.items():
        u, h = np.array(r["silhouette_view0"]["u_mm"]), np.array(r["silhouette_view0"]["h_mm"], dtype=float)
        col = C["coh"] if k.endswith("coh") else C["dry"]
        ax.plot(u, h, ls[k[:3]], color=col, lw=1.8, label=f"Ø{int(r['D_mm'])} {'cohesive' if k.endswith('coh') else 'dry'}")
        R = r["D_mm"] / 2
        ax.plot([-R, R], [0, 0], color=L.INK2, lw=3, solid_capstyle="butt")
    ax.set_xlabel("position across the heap (mm)")
    ax.set_ylabel("silhouette height (mm)")
    ax.set_aspect("equal")
    ax.legend(fontsize=7, frameon=False, loc="upper right")
    L.style_axes(ax)
    tag(ax, "a  Final silhouettes (camera view), simulated")
    ax = axs[0, 1]
    for k, r in runs.items():
        p = os.path.join(HERE, "results", f"t1_heap_{k}_heapmass.csv")
        A = np.loadtxt(p, delimiter=",", skiprows=1)
        col = C["coh"] if k.endswith("coh") else C["dry"]
        ax.plot(A[:, 0], A[:, 3] * 1e3, ls[k[:3]], color=col, lw=1.5, label=k.replace("_", " "))
        ax.axvline(r["t_pour_s"], color=col, lw=0.6, ls=ls[k[:3]], alpha=0.5)
    ax.set_xlabel("time (s)")
    ax.set_ylabel("mass on the pedestal (g)")
    ax.legend(fontsize=7, frameon=False)
    L.style_axes(ax)
    tag(ax, "b  Balance signal (vertical lines: feed stops)")
    ax = axs[1, 0]
    for k, r in runs.items():
        s = r["flank_angle_time_series"]
        t, a = np.array(s["t"]), np.array(s["angle"], dtype=float)
        col = C["coh"] if k.endswith("coh") else C["dry"]
        ax.plot(t, a, ls[k[:3]], color=col, lw=1.3, label=k.replace("_", " "))
    ax.set_xlabel("time (s)")
    ax.set_ylabel("flank angle, 15-85 % fit (deg)")
    ax.set_ylim(10, 75)
    ax.legend(fontsize=7, frameon=False)
    L.style_axes(ax)
    tag(ax, "c  Flank angle while the heap grows (4 views)")
    ax = axs[1, 1]
    for var, col, off in (("dry", C["dry"], -0.5), ("coh", C["coh"], 0.5)):
        ks = [k for k in runs if k.endswith(var)]
        D = np.array([runs[k]["D_mm"] for k in ks])
        o = np.argsort(D)
        D = D[o]
        fl = np.array([runs[k]["flank_angle_deg"] for k in ks])[o]
        sd = np.array([runs[k]["flank_angle_sd_deg"] for k in ks])[o]
        iso = np.array([runs[k]["iso_apex_angle_deg"] for k in ks])[o]
        pf = np.array([runs[k]["profile_fit_angle_deg"] for k in ks])[o]
        lab = "dry" if var == "dry" else "cohesive"
        ax.errorbar(D + off, fl, yerr=sd, fmt="o-", color=col, ms=6, lw=1.5, capsize=3, label=f"{lab}: flank fit (camera)")
        ax.plot(D + off, iso, "s--", color=col, ms=6, lw=1, mfc="white", label=f"{lab}: ISO atan(2h/D)")
        ax.plot(D + off, pf, "^:", color=col, ms=6, lw=1, mfc="white", label=f"{lab}: #196 profile fit")
    ax.plot([12], [21.9], "*", color=C["dry"], ms=11, label="#196 run 2, smooth Ø12 base, dry")
    ax.plot([12], [39.3], "*", color=C["coh"], ms=11, label="#196 run 2, smooth Ø12 base, cohesive")
    ax.set_xlabel("pedestal diameter (mm)")
    ax.set_ylabel("angle (deg)")
    ax.set_xticks([12, 20, 30])
    ax.legend(fontsize=6.5, frameon=False, ncol=1, loc="center left", bbox_to_anchor=(1.0, 0.5))
    L.style_axes(ax)
    tag(ax, "d  Angle against pedestal size")
    fig.suptitle("Test 1, heap on the glued-powder pedestal: DEM prediction (simulated, salt-like spheres)",
                 fontsize=10, color=L.INK)
    fig.tight_layout()
    save(fig, "t1_heap.png")


# ---------------------------------------------------------------- animation helper
def side_view_frames(npz_paths, titles, slab=0.6, xlim=None, zlim=None, extra_draw=None, every=1, width_in=10.0,
                     yname="y", frozen_ids=None):
    """Side-view (x-z) frames of a thin slab |y| < slab mm for one or more npz trajectories."""
    data = [np.load(p) for p in npz_paths]
    F = min(len(d["t"]) for d in data)
    frames = []
    for fi in range(0, F, every):
        fig, axs = plt.subplots(1, len(data), figsize=(width_in, width_in * 0.42 if len(data) > 1 else width_in * 0.6))
        axs = np.atleast_1d(axs)
        for ax, d, ti in zip(axs, data, titles):
            pos = d["pos"][fi].astype(np.float32)
            r = d["r"]
            ok = np.isfinite(pos[:, 0])
            yv = pos[:, 1]
            m = ok & (np.abs(yv - (0 if yname == "y" else np.nanmean(yv))) < slab)
            if yname != "y":
                m = ok & (np.abs(yv - slab_center(d)) < slab)
            ax.set_facecolor(L.SURF)
            cols = np.where(d["id"][m] <= (d["glued_ids_max"] if "glued_ids_max" in d.files else 0), 1, 0)
            L.draw_grains(ax, pos[m, 0], pos[m, 2], r[m], color="#3987e5")
            if cols.any():
                mm = m.copy()
                mm[m] = cols.astype(bool)
                L.draw_grains(ax, pos[mm, 0], pos[mm, 2], r[mm], color=L.INK2)
            if extra_draw:
                extra_draw(ax, d, fi)
            ax.set_aspect("equal")
            if xlim:
                ax.set_xlim(*xlim)
            if zlim:
                ax.set_ylim(*zlim)
            ax.set_title(f"{ti}   t = {float(d['t'][fi]):.2f} s", fontsize=9, color=L.INK)
            ax.tick_params(labelsize=7, colors=L.INK2)
            ax.set_xlabel("mm", fontsize=8, color=L.INK2)
        fig.tight_layout()
        frames.append(L.fig_to_array(fig))
        plt.close(fig)
    return frames


def slab_center(d):
    return 0.0


def anim_t1():
    ps = [os.path.join(HERE, "frames", f"t1_heap_{k}.npz") for k in ("d20_dry", "d20_coh")]
    if not all(os.path.exists(p) for p in ps):
        return

    def ped(ax, d, fi):
        R = float(d["pedestal_R_mm"])
        ax.fill([-R, R, R, R - 3, -R + 3, -R], [0, 0, -0.4, -3.4, -3.4, -0.4], color="#d9d8d3", lw=0)
    fr = side_view_frames(ps, ["Ø20 dry (simulated)", "Ø20 cohesive Bo≈5 (simulated)"], slab=0.6,
                          xlim=(-14, 14), zlim=(-4, 15), extra_draw=ped, every=2)
    L.save_mp4(fr, os.path.join(HERE, "figures", "t1_heap.mp4"), fps=12)



# ---------------------------------------------------------------- test 7 drum
def fig_t7():
    runs = {k: res(f"t7_drum_{k}") for k in ("dry", "coh")}
    runs = {k: v for k, v in runs.items() if v}
    if not runs:
        return
    fig = plt.figure(figsize=(11, 7.4))
    gs = fig.add_gridspec(2, 3)
    ax = fig.add_subplot(gs[0, :])
    for k, r in runs.items():
        s = r["series"]
        ax.plot(s["t"], s["angle_deg"], color=C[k], lw=1.2, label="dry" if k == "dry" else "cohesive (Bo≈5)")
    first = next(iter(runs.values()))
    for sp in first["speeds"]:
        a, b = sp["window_s"]
        ax.axvspan(a, b, color="#e6e5e1", alpha=0.6, lw=0)
        ax.text(0.5 * (a + b), 2, f"{sp['rpm']:g} rpm", ha="center", fontsize=8, color=L.INK2)
    ax.set_xlabel("time since the drum started turning (s)")
    ax.set_ylabel("surface angle (deg)")
    ax.set_ylim(0, 80)
    ax.legend(fontsize=8, frameon=False, loc="upper right")
    L.style_axes(ax)
    tag(ax, "a  Free-surface angle (line fit, central 60 % of the surface); grey: averaging windows")
    ax = fig.add_subplot(gs[1, 0])
    for k, r in runs.items():
        sp = [x for x in r["speeds"] if x.get("dynamic_angle_deg") is not None]
        rpm = np.array([x["rpm"] for x in sp])
        m = np.array([x["dynamic_angle_deg"] for x in sp])
        sd = np.array([x["angle_sd_deg"] for x in sp])
        ax.errorbar(rpm * (1.04 if k == "coh" else 0.96), m, yerr=sd, fmt="o-", color=C[k], capsize=3, ms=6,
                    label=("dry" if k == "dry" else "cohesive") + " mean ± sd")
        up = [x.get("upper_angle_deg") for x in sp]
        lo = [x.get("lower_angle_deg") for x in sp]
        ax.plot(rpm, [u if u else np.nan for u in up], "^", color=C[k], mfc="white", ms=6)
        ax.plot(rpm, [u if u else np.nan for u in lo], "v", color=C[k], mfc="white", ms=6)
    ax.errorbar([9.0], [39.2], yerr=[4.4], fmt="*", color=C["dry"], ms=10, capsize=2, label="#196 run 3 (Ø16 drum, 20 rpm, same Fr as 9 rpm here)")
    ax.set_xscale("log")
    ax.set_xticks([2, 5, 10, 20])
    ax.set_xticklabels(["2", "5", "10", "20"])
    ax.set_xlabel("drum speed (rpm)")
    ax.set_ylabel("angle (deg)")
    ax.legend(fontsize=6.5, frameon=False, loc="upper left")
    L.style_axes(ax)
    tag(ax, "b  Dynamic angle; triangles: avalanche start / stop")
    for j, k in enumerate(("dry", "coh")):
        p = os.path.join(HERE, "frames", f"t7_drum_{k}.npz")
        if not os.path.exists(p):
            continue
        d = np.load(p)
        ax = fig.add_subplot(gs[1, 1 + j])
        pos = d["pos"][-1].astype(np.float32)
        ok = np.isfinite(pos[:, 0])
        L.draw_grains(ax, pos[ok, 0], pos[ok, 2], d["r"][ok], color=C[k])
        th = np.linspace(0, 2 * np.pi, 200)
        ax.plot(20 * np.cos(th), 20 * np.sin(th), color=L.INK2, lw=1)
        ax.set_aspect("equal")
        ax.set_xlim(-21, 21)
        ax.set_ylim(-21, 21)
        ax.set_xticks([])
        ax.set_yticks([])
        ax.set_title(f"{'dry' if k == 'dry' else 'cohesive'}, last frame (t = {float(d['t'][-1]):.1f} s)", fontsize=8,
                     color=L.INK)
    fig.suptitle("Test 7, Ø40 ribbed drum at 40 % fill (periodic 2.13 mm slice): DEM prediction (simulated)",
                 fontsize=10, color=L.INK)
    fig.tight_layout()
    save(fig, "t7_drum.png")


# ---------------------------------------------------------------- test 2 tap
def fig_t2():
    runs = {k: res(f"t2_tap_{k}") for k in ("dry", "coh")}
    runs = {k: v for k, v in runs.items() if v}
    if not runs:
        return
    fig, axs = plt.subplots(1, 3, figsize=(12, 3.9), gridspec_kw=dict(width_ratios=[1.3, 1, 1]))
    ax = axs[0]
    for k, r in runs.items():
        s = r["series"]
        n = np.array(s["taps"], float)
        ax.plot(np.maximum(n, 0.5), s["phi_column"], "o-", color=C[k], ms=3, lw=1.3,
                label=("dry" if k == "dry" else "cohesive") + ", column height")
        ax.plot(np.maximum(n, 0.5), s["phi_slab"], "--", color=C[k], lw=1, label=("dry" if k == "dry" else "cohesive") + ", inner slab")
    ax.set_xscale("log")
    ax.set_xlabel("taps (0 plotted at 0.5)")
    ax.set_ylabel("packing fraction")
    ax.legend(fontsize=7, frameon=False)
    L.style_axes(ax)
    tag(ax, "a  Compaction curve, 3 mm drops")
    ax = axs[1]
    for k, r in runs.items():
        s = r["series"]
        n = np.array(s["taps"], float)
        h = np.array(s["h_mm"])
        Cc = (h[0] - h) / h[0]
        m = n >= 1
        ax.plot(n[m], n[m] / np.maximum(Cc[m], 1e-6), "o", color=C[k], ms=3)
        kw = r.get("kawakita")
        if kw:
            nn = np.linspace(1, n.max(), 50)
            ax.plot(nn, nn / kw["a"] + 1 / (kw["a"] * kw["b"]), color=C[k], lw=1.2,
                    label=f"{'dry' if k == 'dry' else 'cohesive'}: a = {kw['a']:.3f}, 1/b = {kw['one_over_b_taps']:.1f} taps")
    ax.set_xlabel("taps N")
    ax.set_ylabel("N / C")
    ax.legend(fontsize=7, frameon=False)
    L.style_axes(ax)
    tag(ax, "b  Kawakita fit, C = (h0 - hN)/h0")
    ax = axs[2]
    for j, k in enumerate(("dry", "coh")):
        p = os.path.join(HERE, "frames", f"t2_tap_{k}.npz")
        if not os.path.exists(p):
            continue
        d = np.load(p)
        pos = d["pos"][-1].astype(np.float32)
        ok = np.isfinite(pos[:, 0]) & (np.abs(pos[:, 1]) < 0.6)
        off = -7.5 if k == "dry" else 7.5
        L.draw_grains(ax, pos[ok, 0] + off, pos[ok, 2], d["r"][ok], color=C[k])
        ax.plot([off - 6.5, off - 6.5], [0, 12], color=L.INK2, lw=1)
        ax.plot([off + 6.5, off + 6.5], [0, 12], color=L.INK2, lw=1)
        ax.text(off, 12.5, "dry" if k == "dry" else "cohesive", ha="center", fontsize=8, color=L.INK)
    ax.plot([-14, 14], [0, 0], color=L.INK2, lw=1.5)
    ax.set_aspect("equal")
    ax.set_xlim(-15, 15)
    ax.set_ylim(-0.5, 14)
    ax.set_xticks([])
    ax.set_ylabel("height (mm)")
    L.style_axes(ax)
    tag(ax, "c  After the last tap, slice |y| < 0.6 mm")
    fig.suptitle("Test 2, 13 mm cylinder filled by the doser and tapped: DEM prediction (simulated)", fontsize=10,
                 color=L.INK)
    fig.tight_layout()
    save(fig, "t2_tap.png")


# ---------------------------------------------------------------- test 5 orifice
def fig_t5():
    runs = {k: res(f"t5_orifice_{k}") for k in ("dry", "coh")}
    runs = {k: v for k, v in runs.items() if v and v.get("orifices")}
    if not runs:
        return
    fig, axs = plt.subplots(1, 2, figsize=(11, 4.2))
    ax = axs[0]
    for k, r in runs.items():
        o = r["orifices"]
        D = np.array([x["D_mm"] for x in o])
        W = np.array([x["flow_rate_g_s"] for x in o])
        jam = np.array([x["jammed"] for x in o])
        lab = "dry" if k == "dry" else "cohesive"
        ax.plot(D[~jam], W[~jam], "o", color=C[k], ms=7, label=f"{lab}, flows")
        if jam.any():
            ax.plot(D[jam], np.full(jam.sum(), 0.02), "x", color=C[k], ms=9, mew=2, label=f"{lab}, jammed")
        b = r.get("beverloo")
        if b:
            Dd = np.linspace(max(b["k"] * 0.425 + 0.05, 1.0), 6.5, 100)
            Wb = b["C"] * b["rho_b"] * math.sqrt(9.81) * ((Dd - b["k"] * 0.425) * 1e-3) ** 2.5 * 1e3
            ax.plot(Dd, Wb, color=C[k], lw=1.2, label=f"{lab} Beverloo fit: C = {b['C']:.2f}, k = {b['k']:.2f}")
    ax.set_yscale("log")
    ax.set_xlabel("orifice diameter (mm)")
    ax.set_ylabel("flow rate (g/s)")
    ax.legend(fontsize=7, frameon=False)
    L.style_axes(ax)
    tag(ax, "a  Flow rate against orifice size (x at the bottom: jammed)")
    ax = axs[1]
    for k, r in runs.items():
        for x in r["orifices"]:
            mp = os.path.join(L.SCRATCH, "t5_orifice", k, f"D{x['D_mm']:g}", "mass.txt")
            if os.path.exists(mp):
                A = np.loadtxt(mp, skiprows=1, ndmin=2)
                ax.plot(A[:, 0], (A[0, 1] - A[:, 1]) * 1e3, color=C[k], lw=1.1, ls="-" if not x["jammed"] else ":")
                ax.text(A[-1, 0], (A[0, 1] - A[-1, 1]) * 1e3, f" {x['D_mm']:g}", fontsize=7, color=L.INK2, va="center")
    ax.set_xlabel("time after the gate opens (s)")
    ax.set_ylabel("discharged mass (g)")
    L.style_axes(ax)
    tag(ax, "b  Balance signal (blue dry, orange cohesive; label = D in mm)")
    fig.suptitle("Test 5, Ø25 flat-bottomed orifice cup: DEM prediction (simulated)", fontsize=10, color=L.INK)
    fig.tight_layout()
    save(fig, "t5_orifice.png")


# ---------------------------------------------------------------- test 3 tilt
def fig_t3():
    A = {k: res(f"t3_tilt_{k}") for k in ("A_dry_100", "A_dry_400", "A_coh_100", "A_coh_400", "A_cohw_100", "A_cohw_400")}
    B = {k: res(f"t3_tilt_{k}") for k in ("B_dry_1", "B_dry_2", "B_dry_3", "B_coh_1", "B_coh_2", "B_coh_3")}
    A = {k: v for k, v in A.items() if v}
    B = {k: v for k, v in B.items() if v}
    if not A and not B:
        return
    fig, axs = plt.subplots(1, 3, figsize=(12.5, 3.9))
    ax = axs[0]
    cmap = {"dry": C["dry"], "coh": C["coh"], "cohw": C["coh_wall"]}
    names = {"dry": "dry", "coh": "cohesive, plate not adhesive", "cohw": "cohesive + plate adhesion"}
    for k, r in A.items():
        _, var, sig = k.split("_")
        s = r["series"]
        ax.plot(s["theta"], np.array(s["v_grains"]) * 1e3, color=cmap[var], lw=1.2, ls="-" if sig == "100" else "--",
                label=f"{names[var]}, {sig} Pa")
    ax.axvline(math.degrees(math.atan(0.4)), color=L.INK2, lw=0.8, ls=":")
    ax.text(math.degrees(math.atan(0.4)), 45, " atan(0.4)", fontsize=7, color=L.INK2)
    ax.set_xlabel("tilt (deg)")
    ax.set_ylabel("mean grain speed down the slope (mm/s)")
    ax.set_ylim(-2, 60)
    ax.legend(fontsize=6.5, frameon=False, loc="upper left")
    L.style_axes(ax)
    tag(ax, "a  Mode A, ring of powder on PLA (mu_wall 0.4)")
    ax = axs[1]
    for var, off in (("dry", -2), ("coh", 0), ("cohw", 2)):
        xs, ys = [], []
        for sig in ("100", "400"):
            r = A.get(f"A_{var}_{sig}")
            if r and r.get("slip_angle_deg"):
                xs.append(float(sig))
                ys.append(r["slip_angle_deg"])
        if xs:
            ax.plot(np.array(xs) + off * 5, ys, "o-", color=cmap[var], ms=7, label=names[var])
    ax.axhline(math.degrees(math.atan(0.4)), color=L.INK2, lw=0.8, ls=":")
    ax.set_xlabel("normal stress on the plate (Pa)")
    ax.set_ylabel("slip angle (deg)")
    ax.legend(fontsize=7, frameon=False)
    L.style_axes(ax)
    tag(ax, "b  Slip angle; dotted: atan(mu_wall)")
    ax = axs[2]
    for var in ("dry", "coh"):
        xs, ys = [], []
        for h in ("1", "2", "3"):
            r = B.get(f"B_{var}_{h}")
            if r:
                xs.append(float(h))
                ys.append(r["slip_angle_deg"] if r.get("slip_angle_deg") else np.nan)
        if xs:
            ax.plot(xs, ys, "o-", color=C[var], ms=7, label="dry" if var == "dry" else "cohesive (Bo≈5)")
    ax.set_xlabel("layer thickness (mm)")
    ax.set_ylabel("start angle (deg)")
    ax.set_xticks([1, 2, 3])
    ax.legend(fontsize=7, frameon=False)
    L.style_axes(ax)
    tag(ax, "c  Mode B, layer start angle on a powder-roughened plate")
    fig.suptitle("Test 3, tilting plate: DEM prediction (simulated; periodic layers, tilt 12.5 deg/s)", fontsize=10,
                 color=L.INK)
    fig.tight_layout()
    save(fig, "t3_tilt.png")


# ---------------------------------------------------------------- test 8 ucs
def fig_t8():
    runs = {k: res(f"t8_ucs_{k}") for k in ("coh", "dry")}
    runs = {k: v for k, v in runs.items() if v}
    if not runs:
        return
    fig, axs = plt.subplots(1, 3, figsize=(12, 4.0), gridspec_kw=dict(width_ratios=[1, 1, 1.2]))
    for j, k in enumerate(("dry", "coh")):
        p = os.path.join(HERE, "frames", f"t8_ucs_{k}.npz")
        ax = axs[j]
        if not os.path.exists(p):
            continue
        d = np.load(p)
        t = d["t"]
        i_rel = int(np.argmin(np.abs(t - (t[0] + 1.34))))
        pos = d["pos"][i_rel].astype(np.float32)
        ok = np.isfinite(pos[:, 0])
        L.draw_grains(ax, pos[ok, 0], pos[ok, 2], d["r"][ok], color=C[k])
        ax.plot([-10, -10], [0, 40], color=L.INK2, lw=0.8, ls=":")
        ax.plot([10, 10], [0, 40], color=L.INK2, lw=0.8, ls=":")
        ax.plot([-16, 16], [0, 0], color=L.INK2, lw=1.5)
        ax.set_aspect("equal")
        ax.set_xlim(-16, 16)
        ax.set_ylim(-1, 46)
        ax.set_title(f"{'dry' if k == 'dry' else 'cohesive'}: 0.4 s after the mould opens", fontsize=8, color=L.INK)
        ax.set_xlabel("mm", fontsize=8)
        L.style_axes(ax)
    tag(axs[0], "a  Column after the mould is removed (slice |y| < 2 mm; dotted: mould)")
    ax = axs[2]
    for k, r in runs.items():
        s = r.get("platen_series")
        if s:
            ax.plot(s["travel_mm"], s["stress_Pa"], color=C[k], lw=1.3, label="dry" if k == "dry" else "cohesive")
    ax.set_xlabel("platen travel (mm)")
    ax.set_ylabel("platen force / column area (Pa)")
    ax.legend(fontsize=7, frameon=False)
    L.style_axes(ax)
    tag(ax, "b  Platen stress")
    fig.suptitle("Test 8, Ø20 x 40 column after 1 kPa consolidation: DEM prediction (simulated, grains 2x coarse-grained)",
                 fontsize=10, color=L.INK)
    fig.tight_layout()
    save(fig, "t8_ucs.png")


# ---------------------------------------------------------------- test 9 spreading
def fig_t9():
    cases = ("g0.2_dry", "g0.2_coh", "g1.0_dry", "g1.0_coh")
    runs = {k: res(f"t9_spread_{k}") for k in cases}
    runs = {k: v for k, v in runs.items() if v}
    if not runs:
        return
    fig = plt.figure(figsize=(12, 6.5))
    gs = fig.add_gridspec(len(runs) + 1, 2, width_ratios=[2.2, 1])
    for i, (k, r) in enumerate(runs.items()):
        ax = fig.add_subplot(gs[i, 0])
        p = os.path.join(HERE, "frames", f"t9_spread_{k}.npz")
        if os.path.exists(p):
            d = np.load(p)
            pos = d["pos"][-1].astype(np.float32)
            ok = np.isfinite(pos[:, 0]) & (pos[:, 2] < 3)
            L.draw_grains(ax, pos[ok, 0], pos[ok, 1], d["r"][ok], color=C["dry" if k.endswith("dry") else "coh"])
        ax.add_patch(plt.Rectangle((0, 0), 100, 10, fill=False, ec=L.INK2, lw=0.8))
        ax.set_xlim(-5, 112)
        ax.set_ylim(-0.5, 10.5)
        ax.set_aspect("equal")
        ax.set_yticks([])
        ax.tick_params(labelsize=7)
        ax.set_title(f"gap {r['gap_mm']:.1f} mm, {'dry' if k.endswith('dry') else 'cohesive'}: coverage {r['coverage_mean']:.2f}, "
                     f"layer phi {r['phi_layer_mean_where_covered']:.2f}", fontsize=8, color=L.INK, loc="left")
    ax = fig.add_subplot(gs[:, 1])
    for k, r in runs.items():
        x = [b["x_mm"] for b in r["bins"]]
        cv = [b["coverage"] for b in r["bins"]]
        ax.plot(x, cv, "o-" if k.startswith("g1.0") else "s:", color=C["dry" if k.endswith("dry") else "coh"], ms=4,
                lw=1.2, label=k.replace("_", " ").replace("g", "gap "))
    ax.set_xlabel("position along the coupon (mm)")
    ax.set_ylabel("coverage")
    ax.set_ylim(-0.02, 1.02)
    ax.legend(fontsize=7, frameon=False)
    L.style_axes(ax)
    fig.suptitle("Test 9, blade spreading at 50 mm/s on a 10 mm periodic strip of the coupon: DEM prediction (simulated, top view)",
                 fontsize=10, color=L.INK)
    fig.tight_layout()
    save(fig, "t9_spread.png")



# ---------------------------------------------------------------- animations
def _frames_from(npz_list, titles, draw, figsize, every=1, max_frames=90):
    data = [np.load(p) for p in npz_list]
    F = min(len(d["t"]) for d in data)
    idx = list(range(0, F, every))
    if len(idx) > max_frames:
        idx = list(np.linspace(0, F - 1, max_frames).round().astype(int))
    frames = []
    for fi in idx:
        fig, axs = plt.subplots(1, len(data), figsize=figsize)
        axs = np.atleast_1d(axs)
        for ax, d, ti in zip(axs, data, titles):
            ax.set_facecolor(L.SURF)
            draw(ax, d, fi)
            ax.set_title(f"{ti}   t = {float(d['t'][fi]):.2f} s", fontsize=9, color=L.INK)
            ax.tick_params(labelsize=7, colors=L.INK2)
        fig.tight_layout()
        frames.append(L.fig_to_array(fig))
        plt.close(fig)
    return frames


def _grains(ax, d, fi, mask_fn=None, xi=0, zi=2, color="#3987e5", cfn=None, vmax=None):
    pos = d["pos"][fi].astype(np.float32)
    ok = np.isfinite(pos[:, 0])
    if mask_fn is not None:
        ok &= mask_fn(pos)
    c = cfn(pos[ok]) if cfn else None
    L.draw_grains(ax, pos[ok, xi], pos[ok, zi], d["r"][ok], c=c, cmap=L.speed_cmap() if c is not None else None,
                  vmax=vmax, color=color)


def anim_t7():
    ps = [os.path.join(HERE, "frames", f"t7_drum_{k}.npz") for k in ("dry", "coh")]
    if not all(os.path.exists(p) for p in ps):
        return

    def draw(ax, d, fi):
        _grains(ax, d, fi, color="#3987e5")
        R = float(d["drum_R_mm"])
        th = np.linspace(0, 2 * np.pi, 200)
        ax.plot(R * np.cos(th), R * np.sin(th), color=L.INK2, lw=1)
        na = len(d["drum_angle_deg"])
        tt = np.linspace(float(d["t"][0]), float(d["t"][-1]), na)
        phi = math.radians(float(np.interp(float(d["t"][fi]), tt, d["drum_angle_deg"])))
        for k in range(int(d["n_ribs"])):
            a = 2 * math.pi * k / int(d["n_ribs"]) + phi
            ax.plot([R * math.cos(a), (R - float(d["rib_height_mm"])) * math.cos(a)],
                    [R * math.sin(a), (R - float(d["rib_height_mm"])) * math.sin(a)], color=L.INK, lw=2)
        ax.set_aspect("equal")
        ax.set_xlim(-R - 1, R + 1)
        ax.set_ylim(-R - 1, R + 1)
        ax.set_xticks([])
        ax.set_yticks([])
    fr = _frames_from(ps, ["dry (simulated)", "cohesive Bo≈5 (simulated)"], draw, (9, 4.6))
    L.save_mp4(fr, os.path.join(HERE, "figures", "t7_drum.mp4"), fps=10)


def anim_t2():
    ps = [os.path.join(HERE, "frames", f"t2_tap_{k}.npz") for k in ("dry", "coh")]
    if not all(os.path.exists(p) for p in ps):
        return

    def draw(ax, d, fi):
        _grains(ax, d, fi, mask_fn=lambda p: np.abs(p[:, 1]) < 0.6)
        R = float(d["bore_R_mm"])
        ax.plot([-R, -R], [0, 18], color=L.INK2, lw=1.2)
        ax.plot([R, R], [0, 18], color=L.INK2, lw=1.2)
        ax.plot([-R - 1, R + 1], [0, 0], color=L.INK2, lw=2)
        ti = int(d["tap_index"][fi]) if "tap_index" in d.files and fi < len(d["tap_index"]) else -1
        ax.text(0, 19, "filling" if ti < 0 else f"after tap {ti}", ha="center", fontsize=8, color=L.INK)
        ax.set_aspect("equal")
        ax.set_xlim(-R - 1.5, R + 1.5)
        ax.set_ylim(-0.5, 20.5)
    fr = _frames_from(ps, ["dry", "cohesive"], draw, (7, 5.4), max_frames=120)
    L.save_mp4(fr, os.path.join(HERE, "figures", "t2_tap.mp4"), fps=10)


def anim_t5():
    ps = [os.path.join(HERE, "frames", f"t5_orifice_{k}.npz") for k in ("dry", "coh")]
    ps = [p for p in ps if os.path.exists(p)]
    if not ps:
        return

    def draw(ax, d, fi):
        _grains(ax, d, fi)
        R = float(d["cup_R_mm"])
        D = float(d["orifice_D_mm"])
        ax.plot([-R, -R], [0, 12], color=L.INK2, lw=1.2)
        ax.plot([R, R], [0, 12], color=L.INK2, lw=1.2)
        ax.plot([-R, -D / 2], [0, 0], color=L.INK2, lw=2)
        ax.plot([D / 2, R], [0, 0], color=L.INK2, lw=2)
        ax.set_aspect("equal")
        ax.set_xlim(-R - 1, R + 1)
        ax.set_ylim(-8, 12)
    fr = _frames_from(ps, [("dry" if "dry" in p else "cohesive") + ", 4 mm orifice" for p in ps], draw,
                      (4.8 * len(ps), 4.4))
    L.save_mp4(fr, os.path.join(HERE, "figures", "t5_orifice.mp4"), fps=10)


def anim_t3():
    ps = [os.path.join(HERE, "frames", f"t3_tilt_{k}.npz") for k in ("B_dry_2", "B_coh_2")]
    ps = [p for p in ps if os.path.exists(p)]
    if not ps:
        return

    def draw(ax, d, fi):
        th = float(d["tilt_deg"][fi])
        _grains(ax, d, fi, mask_fn=lambda p: p[:, 1] < 1.0)
        ax.set_aspect("equal")
        ax.set_xlim(0, 8)
        ax.set_ylim(-0.3, 4)
        ax.text(0.2, 3.6, f"tilt {th:.1f} deg (plate frame, x down the slope)", fontsize=8, color=L.INK)
    fr = _frames_from(ps, [("dry" if "dry" in p else "cohesive") + ", 2 mm layer" for p in ps], draw,
                      (5.2 * len(ps), 3.0), max_frames=100)
    L.save_mp4(fr, os.path.join(HERE, "figures", "t3_tilt.mp4"), fps=10)


def anim_t8():
    ps = [os.path.join(HERE, "frames", f"t8_ucs_{k}.npz") for k in ("dry", "coh")]
    ps = [p for p in ps if os.path.exists(p)]
    if not ps:
        return

    def draw(ax, d, fi):
        _grains(ax, d, fi)
        ax.plot([-16, 16], [0, 0], color=L.INK2, lw=2)
        if float(d["t"][fi]) - float(d["t"][0]) < 0.95:
            ax.plot([-10, -10], [0, 60], color=L.INK2, lw=1.2)
            ax.plot([10, 10], [0, 60], color=L.INK2, lw=1.2)
        ax.set_aspect("equal")
        ax.set_xlim(-16, 16)
        ax.set_ylim(-1, 62)
    fr = _frames_from(ps, [("dry" if "dry" in p else "cohesive") for p in ps], draw, (3.6 * len(ps), 5.2))
    L.save_mp4(fr, os.path.join(HERE, "figures", "t8_ucs.mp4"), fps=10)


def anim_t9():
    ps = [os.path.join(HERE, "frames", f"t9_spread_{k}.npz") for k in ("g1.0_dry", "g1.0_coh")]
    ps = [p for p in ps if os.path.exists(p)]
    if not ps:
        return

    def draw(ax, d, fi):
        _grains(ax, d, fi, xi=0, zi=1, cfn=lambda p: p[:, 2], vmax=3.0)
        bx = float(d["blade_x_mm"][min(fi, len(d["blade_x_mm"]) - 1)])
        ax.axvspan(bx, bx + float(d["blade_thickness_mm"]), color=L.INK2, alpha=0.7)
        ax.add_patch(plt.Rectangle((0, 0), 100, 10, fill=False, ec=L.INK2, lw=0.8))
        ax.set_aspect("equal")
        ax.set_xlim(-5, 112)
        ax.set_ylim(-0.5, 10.5)
    data_titles = [("dry" if "dry" in p else "cohesive") + ", gap 1.0 mm, top view (colour: height)" for p in ps]
    frs = []
    data = [np.load(p) for p in ps]
    F = min(len(d["t"]) for d in data)
    for fi in range(F):
        fig, axs = plt.subplots(len(data), 1, figsize=(10, 1.9 * len(data)))
        axs = np.atleast_1d(axs)
        for ax, d, ti in zip(axs, data, data_titles):
            ax.set_facecolor(L.SURF)
            draw(ax, d, fi)
            ax.set_title(f"{ti}   t = {float(d['t'][fi]):.2f} s", fontsize=8, color=L.INK, loc="left")
            ax.tick_params(labelsize=7)
        fig.tight_layout()
        frs.append(L.fig_to_array(fig))
        plt.close(fig)
    L.save_mp4(frs, os.path.join(HERE, "figures", "t9_spread.mp4"), fps=10)


def main(which):
    which = which or ["all"]
    if "t1" in which or "all" in which:
        fig_t1()
    for k, f in (("t7", fig_t7), ("t2", fig_t2), ("t5", fig_t5), ("t3", fig_t3), ("t8", fig_t8), ("t9", fig_t9)):
        if k in which or "all" in which:
            f()
    if "a1" in which or "anim" in which or "all" in which:
        anim_t1()
    for k, f in (("a7", anim_t7), ("a2", anim_t2), ("a5", anim_t5), ("a3", anim_t3), ("a8", anim_t8), ("a9", anim_t9)):
        if k in which or "anim" in which or "all" in which:
            f()


if __name__ == "__main__":
    main(sys.argv[1:])
