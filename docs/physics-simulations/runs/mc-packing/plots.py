"""Figure, animation and result.json for the mc-packing run (reads scratch npz)."""
import json
import math
import os

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.collections import EllipseCollection  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
SCR = "/tmp/sims-scratch/mc-packing"
C = {"salt": "#2a78d6", "alsi10mg": "#eb6834", "mono": "#52514e"}
NAMES = {"salt": "NaCl (0.36-0.49 mm)", "alsi10mg": "AlSi10Mg (d50 35 um, span 1)",
         "mono": "monodisperse"}
DREF = {"salt": 0.425, "alsi10mg": 0.035, "mono": 1.0}   # mm per unit length
RHO = {"salt": 2165.0, "alsi10mg": 2670.0}
plt.rcParams.update({"font.size": 9, "axes.spines.top": False, "axes.spines.right": False,
                     "axes.edgecolor": "#8a8984", "axes.labelcolor": "#0b0b0b",
                     "xtick.color": "#52514e", "ytick.color": "#52514e"})


def load():
    with open(f"{SCR}/raw_results.json") as f:
        return json.load(f)


def cut_circles(pos, rad, L, y0, idx=None):
    if idx is not None:
        pos, rad = pos[idx], rad[idx]
    dy = pos[:, 1] - y0
    dy -= L * np.floor(dy / L + 0.5)
    m = np.abs(dy) < rad
    x, z, rc = pos[m, 0], pos[m, 2], np.sqrt(rad[m] ** 2 - dy[m] ** 2)
    # periodic images in x
    xs, zs, rs = [x], [z], [rc]
    left = x - rc < 0
    right = x + rc > L
    xs += [x[left] + L, x[right] - L]
    zs += [z[left], z[right]]
    rs += [rc[left], rc[right]]
    return np.concatenate(xs), np.concatenate(zs), np.concatenate(rs)


def draw_cut(ax, pos, rad, L, scale, color, zmax_mm, idx=None):
    x, z, rc = cut_circles(pos, rad, L, 0.5 * L, idx)
    ec = EllipseCollection(2 * rc * scale, 2 * rc * scale, np.zeros_like(rc), units="xy",
                           offsets=np.c_[x * scale, z * scale], offset_transform=ax.transData,
                           facecolors=color, edgecolors="#0b0b0b", linewidths=0.3)
    ax.add_collection(ec)
    ax.set_xlim(0, L * scale)
    ax.set_ylim(0, zmax_mm)
    ax.set_aspect("equal")
    ax.set_facecolor("#fcfcfb")


def main():
    R = load()
    fig = plt.figure(figsize=(12.5, 8.2), dpi=100)
    gs = fig.add_gridspec(2, 4, width_ratios=[1.25, 1.25, 0.55, 0.55], hspace=0.38, wspace=0.42)

    # (a) packing fraction by algorithm
    ax = fig.add_subplot(gs[0, 0])
    algs = ["RSA\n(no gravity)", "sticky BD\n(p_stick=1)", "drop-and-roll\n(p_stick=0)",
            "force-biased\ncompression"]
    lit = [0.384, None, 0.582, 0.64]
    for si, name in enumerate(["mono", "salt", "alsi10mg"]):
        dep = R["deposit"][name]["runs"]
        vals = [R["rsa"][name]["phi"], dep["1.0"]["phi"], dep["0.0"]["phi"], R["compress"][name]["phi"]]
        xx = np.arange(4) + (si - 1) * 0.22
        ax.plot(xx, vals, "o", ms=8, color=C[name], label=NAMES[name], mec="#fcfcfb", mew=1.5)
        if name != "mono":
            for x_, v_ in zip(xx, vals):
                ax.annotate(f"{v_:.3f}", (x_, v_), xytext=(0, 7 if si == 1 else -12),
                            textcoords="offset points", ha="center", fontsize=7, color="#52514e")
    for i, v in enumerate(lit):
        if v is not None:
            ax.plot([i - 0.38, i + 0.38], [v, v], color="#0b0b0b", lw=1, ls=":")
    ax.plot([], [], color="#0b0b0b", lw=1, ls=":", label="monodisperse literature value")
    ax.set_xticks(range(4))
    ax.set_xticklabels(algs, fontsize=8)
    ax.set_ylabel("packing fraction  φ  (-)")
    ax.set_ylim(0.0, 0.75)
    ax.grid(axis="y", color="#e6e5e1", lw=0.6)
    ax.legend(fontsize=7, loc="upper left", frameon=False)
    ax.set_title("(a) 3D packing fraction by algorithm", loc="left", fontsize=10)

    # (b) loose packing vs stickiness
    ax = fig.add_subplot(gs[0, 1])
    for name in ("salt", "alsi10mg"):
        runs = R["deposit"][name]["runs"]
        ps = sorted(float(k) for k in runs)
        ph = [runs[str(p) if str(p) in runs else repr(p)]["phi"] for p in ps]
        ax.plot(ps, ph, "-o", color=C[name], lw=2, ms=7, mec="#fcfcfb", mew=1.5, label=NAMES[name] + ", deposition")
        ax.axhline(R["compress"][name]["phi"], color=C[name], lw=1.2, ls="--")
        ax.text(1.0, R["compress"][name]["phi"] + 0.006, "compression (dense)", color="#52514e",
                fontsize=7, ha="right", va="bottom")
    ax.set_xlabel("stick probability per contact  p_stick  (cohesion proxy, -)")
    ax.set_ylabel("loose (poured) packing fraction  φ  (-)")
    ax.set_ylim(0.0, 0.75)
    ax.grid(color="#e6e5e1", lw=0.6)
    ax.legend(fontsize=7, loc="lower left", frameon=False)
    ax.set_title("(b) loose packing vs stickiness", loc="left", fontsize=10)

    # (c) Hausner analog
    ax = fig.add_subplot(gs[1, 0])
    for thr, lab in [(1.11, "excellent"), (1.18, "good"), (1.25, "fair"), (1.34, "passable"),
                     (1.45, "poor"), (1.59, "very poor")]:
        ax.axhline(thr, color="#c3c2b7", lw=0.8)
        ax.text(1.02, thr, f"{lab} < {thr}", fontsize=6.5, color="#52514e", va="center",
                transform=ax.get_yaxis_transform())
    for name in ("salt", "alsi10mg"):
        runs = R["deposit"][name]["runs"]
        ps = sorted(float(k) for k in runs)
        H = [R["compress"][name]["phi"] / runs[str(p)]["phi"] for p in ps]
        ax.plot(ps, H, "-o", color=C[name], lw=2, ms=7, mec="#fcfcfb", mew=1.5, label=NAMES[name])
        ax.annotate(f"H = {H[0]:.3f}", (ps[0], H[0]), xytext=(4, -12 if name == "salt" else 6),
                    textcoords="offset points", fontsize=7, color="#52514e")
    ax.set_yscale("log")
    ax.set_yticks([1.0, 1.25, 1.5, 2, 3, 4, 5])
    ax.set_yticklabels(["1.0", "1.25", "1.5", "2", "3", "4", "5"])
    ax.set_ylim(1.0, 5.0)
    ax.set_xlabel("stick probability per contact  p_stick  (-)")
    ax.set_ylabel("Hausner-ratio analog  φ_dense / φ_loose  (-)")
    ax.legend(fontsize=7, loc="upper left", frameon=False)
    ax.set_title("(c) Hausner analog (USP <1174> classes at right)", loc="left", fontsize=10)

    # (d) density profiles
    ax = fig.add_subplot(gs[1, 1])
    for name, ls in (("salt", "-"), ("alsi10mg", "-")):
        z = np.load(f"{SCR}/dep_{name}_p0.0.npz")
        r0 = R["deposit"][name]["runs"]["0.0"]
        zz = (z["zb"] + 0.125) * DREF[name] * (1000 if name == "alsi10mg" else 1)
        unit_scale = DREF[name] * (1000 if name == "alsi10mg" else 1)
        # profile vs z / d_ref so both fit one axis
        ax.plot(z["zb"] + 0.125, z["prof"], ls, color=C[name], lw=1.2, label=NAMES[name] + ", p_stick = 0")
        ax.axvspan(r0["z_window"][0], r0["z_window"][1], color=C[name], alpha=0.08)
    ax.set_xlabel("height above floor  z / d_ref  (d_ref = 0.425 mm NaCl, 35 um AlSi10Mg)")
    ax.set_ylabel("slice packing fraction  φ(z)  (-)")
    ax.set_xlim(0, 32)
    ax.set_ylim(0, 1.0)
    ax.grid(color="#e6e5e1", lw=0.6)
    ax.legend(fontsize=7, loc="upper right", frameon=False)
    ax.set_title("(d) layering at the floor; shaded = measurement window", loc="left", fontsize=10)

    # (e,f) cut planes, salt
    for col, ps, title in ((2, "0.0", "(e) NaCl, drop-and-roll"), (3, "1.0", "(f) NaCl, sticky")):
        ax = fig.add_subplot(gs[:, col])
        z = np.load(f"{SCR}/dep_salt_p{ps}.npz")
        draw_cut(ax, z["pos"], z["rad"], float(z["L"]), DREF["salt"], C["salt"], 10.0)
        ax.set_xlabel("x (mm)")
        if col == 2:
            ax.set_ylabel("z (mm), vertical cut plane")
        phi = R["deposit"]["salt"]["runs"][ps]["phi"]
        ax.set_title(f"{title}\nφ = {phi:.3f}", loc="left", fontsize=9)
    fig.suptitle("mc-packing: Monte Carlo / geometric packing of polydisperse spheres "
                 "(own numba code, 3D, periodic in x-y)", fontsize=11, x=0.01, ha="left")
    out = os.path.join(HERE, "mc_packing.png")
    fig.savefig(out, dpi=100, bbox_inches="tight")
    print("wrote", out, os.path.getsize(out))


def animate():
    import imageio.v2 as imageio
    import imageio_ffmpeg
    os.environ.setdefault("IMAGEIO_FFMPEG_EXE", imageio_ffmpeg.get_ffmpeg_exe())
    runs = []
    for ps in ("0.0", "1.0"):
        z = np.load(f"{SCR}/dep_salt_p{ps}.npz")
        pos, rad, L = z["pos"], z["rad"], float(z["L"])
        top = np.maximum.accumulate(pos[:, 2] + rad) * DREF["salt"]
        runs.append((pos, rad, L, top))
    hmax = 9.0  # mm of bed shown
    F = 60
    frames = []
    for f in range(1, F + 1):
        h = hmax * f / F
        fig, axs = plt.subplots(1, 2, figsize=(6.4, 4.8), dpi=100)
        for ax, (pos, rad, L, top), lab in zip(axs, runs, ("cohesionless: drop-and-roll\n(p_stick = 0)",
                                                           "cohesive limit: sticky\n(p_stick = 1)")):
            k = int(np.searchsorted(top, h)) + 1
            draw_cut(ax, pos, rad, L, DREF["salt"], C["salt"], hmax + 0.3, idx=np.arange(min(k, rad.size)))
            ax.set_title(f"{lab}\n{k} grains dropped", fontsize=8)
            ax.set_xlabel("x (mm)", fontsize=8)
            ax.tick_params(labelsize=7)
        axs[0].set_ylabel("z (mm), vertical cut plane", fontsize=8)
        fig.suptitle("mc-packing (own numba code): NaCl PSD, sequential deposition", fontsize=9)
        fig.tight_layout()
        fig.canvas.draw()
        img = np.asarray(fig.canvas.buffer_rgba())[:, :, :3].copy()
        plt.close(fig)
        frames.append(img)
    frames += [frames[-1]] * 12
    gif = os.path.join(HERE, "mc_packing_deposition.gif")
    imageio.mimsave(gif, frames, duration=1 / 12, loop=0)
    mp4 = os.path.join(HERE, "mc_packing_deposition.mp4")
    w = imageio.get_writer(mp4, fps=12, codec="libx264", pixelformat="yuv420p", quality=7,
                           macro_block_size=16)
    for fr in frames:
        w.append_data(fr)
    w.close()
    print("frame shape", frames[0].shape, "gif", os.path.getsize(gif), "mp4", os.path.getsize(mp4))


if __name__ == "__main__":
    main()
    animate()


def write_result(extra_wall=0.0):
    import platform
    import numba
    R = load()
    kr = {"units": "packing fraction phi (solid volume / total volume), dimensionless"}
    for name in ("mono", "salt", "alsi10mg"):
        dep = R["deposit"][name]["runs"]
        d = {"rsa_phi_at_1e7_attempts": round(R["rsa"][name]["phi"], 4),
             "rsa_phi_feder_extrapolated": round(R["rsa"][name]["phi_extrap"], 4),
             "drop_and_roll_phi_loose": round(dep["0.0"]["phi"], 4),
             "sticky_ballistic_phi": round(dep["1.0"]["phi"], 4),
             "compression_phi_dense": round(R["compress"][name]["phi"], 4),
             "hausner_analog_cohesionless": round(R["compress"][name]["phi"] / dep["0.0"]["phi"], 4),
             "hausner_analog_sticky": round(R["compress"][name]["phi"] / dep["1.0"]["phi"], 3)}
        if name in RHO:
            d["phi_loose_vs_p_stick"] = {k: round(v["phi"], 4) for k, v in sorted(dep.items(), key=lambda t: float(t[0]))}
            d["hausner_vs_p_stick"] = {k: round(R["compress"][name]["phi"] / v["phi"], 3)
                                       for k, v in sorted(dep.items(), key=lambda t: float(t[0]))}
            d["implied_bulk_density_kg_m3_drop_and_roll"] = round(dep["0.0"]["phi"] * RHO[name], 0)
            d["implied_dense_density_kg_m3_compression"] = round(R["compress"][name]["phi"] * RHO[name], 0)
            d["implied_bulk_density_kg_m3_sticky"] = round(dep["1.0"]["phi"] * RHO[name], 0)
            d["generated_volume_d10_d50_d90_mm"] = [round(x * DREF[name], 4) for x in R["deposit"][name]["d_vol_10_50_90"]]
        d["max_rel_overlap_any_packing"] = float(max([R["rsa"][name]["max_rel_overlap"], R["compress"][name]["max_rel_overlap"]] +
                                                     [v["max_rel_overlap"] for v in dep.values()]))
        d["deposition_particles_hitting_transition_cap"] = int(sum(v["stuck"] for v in dep.values()))
        kr[name] = d
    out = {"id": "mc-packing", "method": "Monte Carlo / geometric sphere packing: random sequential addition, "
           "sequential drop-and-roll deposition (Visscher-Bolsterli / Jullien-Meakin) with a stick-probability "
           "cohesion proxy, force-biased (FIRE overlap-removal) compression",
           "code": "own Python + numba (packing_kernels.py)",
           "version": f"python {platform.python_version()}, numpy {np.__version__}, numba {numba.__version__}",
           "status": "ran", "wall_s": round(R["wall_s_total"] + extra_wall, 1), "cores": 1,
           "key_results": kr,
           "notes": "3D, periodic in x-y (deposition: flat floor, phi measured in a bulk slab 3 d_max above the floor "
                    "to 2 d_max below the 10th-percentile surface height; RSA and compression: fully periodic cube). "
                    "Geometric packings are scale-free, so NaCl vs AlSi10Mg differ only through PSD shape; "
                    "cohesion enters only through p_stick. Monodisperse runs are validation against literature."}
    with open(os.path.join(HERE, "result.json"), "w") as f:
        json.dump(out, f, indent=1)
    print(json.dumps(kr, indent=1)[:3000])
