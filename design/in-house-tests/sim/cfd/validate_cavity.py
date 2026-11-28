"""Validation 1: lid-driven cavity, Re = 100, against Ghia, Ghia and Shin (1982).

Runs mac2d.MAC2D (central differences) on 32, 64 and 128 cells and compares the
centreline profiles with Ghia et al. Table I (u on x = 0.5) and Table II (v on y = 0.5).
Writes cavity_validation.json and cavity_validation.png.
"""
import json
import sys
import time

import numpy as np

from mac2d import MAC2D
import plotstyle as ps

GHIA_U = np.array([  # y, u  (Ghia et al. 1982, Table I, Re = 100)
    [1.0000, 1.00000], [0.9766, 0.84123], [0.9688, 0.78871], [0.9609, 0.73722],
    [0.9531, 0.68717], [0.8516, 0.23151], [0.7344, 0.00332], [0.6172, -0.13641],
    [0.5000, -0.20581], [0.4531, -0.21090], [0.2813, -0.15662], [0.1719, -0.10150],
    [0.1016, -0.06434], [0.0703, -0.04775], [0.0625, -0.04192], [0.0547, -0.03717],
    [0.0000, 0.00000]])
GHIA_V = np.array([  # x, v  (Ghia et al. 1982, Table II, Re = 100)
    [1.0000, 0.00000], [0.9688, -0.05906], [0.9609, -0.07391], [0.9531, -0.08864],
    [0.9453, -0.10313], [0.9063, -0.16914], [0.8594, -0.22445], [0.8047, -0.24533],
    [0.5000, 0.05454], [0.2344, 0.17527], [0.2266, 0.17507], [0.1563, 0.16077],
    [0.0938, 0.12317], [0.0781, 0.10890], [0.0703, 0.10091], [0.0625, 0.09233],
    [0.0000, 0.00000]])


def run(N, Re=100.0, t_end=30.0):
    s = MAC2D(N, N, 1.0, 1.0, nu=1.0 / Re, top="wall", lid_u=1.0, upwind=0.0)
    dt = 0.9 * min(0.25 * s.dx ** 2 / s.nu, 2.0 * s.nu / 1.0)
    t0 = time.time()
    t, n, du = s.run(t_end, dt, tol=1e-5, every=4000, verbose=True)
    # centreline profiles
    i_mid = N // 2                      # u-face column at x = 0.5
    y = np.concatenate([[0.0], s.yc, [1.0]])
    u = np.concatenate([[0.0], s.u[i_mid, :], [1.0]])
    j_mid = N // 2                      # v-face row at y = 0.5
    x = np.concatenate([[0.0], s.xc, [1.0]])
    v = np.concatenate([[0.0], s.v[:, j_mid], [0.0]])
    uG = np.interp(GHIA_U[:, 0], y, u)
    vG = np.interp(GHIA_V[:, 0], x, v)
    err_u = np.abs(uG - GHIA_U[:, 1])
    err_v = np.abs(vG - GHIA_V[:, 1])
    return dict(N=N, t_end=t, steps=n, final_du=du, wall_s=time.time() - t0,
                max_err_u=float(err_u.max()), max_err_v=float(err_v.max()),
                rms_err_u=float(np.sqrt(np.mean(err_u ** 2))),
                rms_err_v=float(np.sqrt(np.mean(err_v ** 2))),
                u_min=float(u.min()), v_min=float(v.min()), v_max=float(v.max()),
                profile_y=y.tolist(), profile_u=u.tolist(),
                profile_x=x.tolist(), profile_v=v.tolist())


def main():
    Ns = [int(a) for a in sys.argv[1:]] or [32, 64, 128]
    out = []
    for N in Ns:
        print(f"cavity N = {N}", flush=True)
        r = run(N)
        print(f"  max|err u| = {r['max_err_u']:.4f}, max|err v| = {r['max_err_v']:.4f}, "
              f"{r['wall_s']:.0f} s", flush=True)
        out.append(r)
    res = dict(case="lid-driven cavity Re = 100", reference="Ghia, Ghia and Shin (1982) J. Comput. "
               "Phys. 48, 387-411, Tables I and II (values transcribed; see README)",
               scheme="MAC grid, central differences, forward Euler, projection", runs=out,
               ghia_u_min=float(GHIA_U[:, 1].min()), ghia_v_min=float(GHIA_V[:, 1].min()),
               ghia_v_max=float(GHIA_V[:, 1].max()))
    # observed order of convergence from the max errors
    if len(out) >= 3:
        e = [r["rms_err_u"] + r["rms_err_v"] for r in out]
        res["observed_order_rms"] = float(np.log(e[-2] / e[-1]) / np.log(2.0))
    with open("cavity_validation.json", "w") as f:
        json.dump(res, f, indent=1)

    fig, axs = ps.plt.subplots(1, 2, figsize=(10, 4.4))
    for k, r in enumerate(out):
        c = ps.CAT[k]
        axs[0].plot(r["profile_u"], r["profile_y"], color=c, lw=2, label=f"this solver, {r['N']}$^2$ cells")
        axs[1].plot(r["profile_x"], r["profile_v"], color=c, lw=2, label=f"this solver, {r['N']}$^2$ cells")
    axs[0].plot(GHIA_U[:, 1], GHIA_U[:, 0], "o", ms=6, mfc="white", mec=ps.TEXT, mew=1.5,
                label="Ghia et al. 1982")
    axs[1].plot(GHIA_V[:, 0], GHIA_V[:, 1], "o", ms=6, mfc="white", mec=ps.TEXT, mew=1.5,
                label="Ghia et al. 1982")
    axs[0].set_xlabel("u / U on x = 0.5")
    axs[0].set_ylabel("y / L")
    axs[1].set_xlabel("x / L")
    axs[1].set_ylabel("v / U on y = 0.5")
    axs[0].set_title("Lid-driven cavity, Re = 100: u", loc="left")
    axs[1].set_title("v", loc="left")
    for a in axs:
        ps.tidy(a)
    axs[1].legend(frameon=False, fontsize=8)
    fig.text(0.01, 0.005, "Computed, not measured. Errors in cavity_validation.json.",
             color=ps.TEXT2, fontsize=8)
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    fig.savefig("cavity_validation.png", dpi=150)


if __name__ == "__main__":
    main()
