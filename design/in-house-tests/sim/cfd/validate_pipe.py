"""Validation 2: axisymmetric mode of mac2d against Hagen-Poiseuille pipe flow.

Uniform inflow U at the bottom of a pipe (radius R, length 8 D), open top. Downstream
the profile must become u_z = 2 U (1 - r^2/R^2) and the kinematic pressure gradient
-dp/dz = 8 nu U / R^2. Re = U D / nu = 10. Grids 8, 16 and 32 cells across the radius.
Writes pipe_validation.json and pipe_validation.png.
"""
import json
import time

import numpy as np

from mac2d import MAC2D
import plotstyle as ps


def run(nr, Re=10.0):
    R, U = 1.0, 1.0
    D = 2 * R
    nu = U * D / Re
    Lz = 8 * D
    nz = int(round(nr * Lz / R))
    s = MAC2D(nr, nz, R, Lz, nu=nu, axisym=True, top="open", upwind=0.0)
    s.vbc[:, 0] = U                       # uniform inflow at z = 0
    s.v[:, :] = U
    dt = 0.4 * min(0.25 * s.dx ** 2 / nu, 2 * nu / (2 * U) ** 2, s.dx / (2 * U))
    t0 = time.time()
    t, n, du = s.run(60.0, dt, tol=1e-5, every=5000, verbose=False)
    # profile at z = 6 D (fully developed)
    j = int(6 * D / s.dy)
    vz = 0.5 * (s.v[:, j] + s.v[:, j + 1])
    exact = 2 * U * (1 - (s.xc / R) ** 2)
    # pressure gradient between z = 5 D and 7 D
    j1, j2 = int(5 * D / s.dy), int(7 * D / s.dy)
    dpdz = (s.p[0, j2] - s.p[0, j1]) / (s.yc[j2] - s.yc[j1])
    # flow rate check
    Q = np.sum(s.v[:, j] * 2 * np.pi * s.xc * s.dx)
    return dict(nr=nr, nz=nz, steps=n, wall_s=time.time() - t0, final_du=du,
                centre_velocity=float(vz[0] + (vz[0] - vz[1]) * 0.5 * 0.0),
                centre_velocity_extrap=float(np.polyval(np.polyfit(s.xc[:3] ** 2, vz[:3], 1), 0.0)),
                max_err_profile=float(np.abs(vz - exact).max() / (2 * U)),
                dpdz=float(-dpdz), dpdz_exact=8 * nu * U / R ** 2,
                dpdz_rel_err=float(abs(-dpdz - 8 * nu * U / R ** 2) / (8 * nu * U / R ** 2)),
                flow_rate=float(Q), flow_rate_exact=float(np.pi * R ** 2 * U),
                r=s.xc.tolist(), vz=vz.tolist())


def main():
    out = []
    for nr in (8, 12, 16):
        r = run(nr)
        print(f"nr = {nr}: profile err {r['max_err_profile']:.4f}, dp/dz err {r['dpdz_rel_err']:.4f}, "
              f"Q/Qexact {r['flow_rate'] / r['flow_rate_exact']:.5f}, {r['wall_s']:.0f} s", flush=True)
        out.append(r)
    json.dump(dict(case="Hagen-Poiseuille pipe, axisymmetric, Re = 10, uniform inflow",
                   runs=out), open("pipe_validation.json", "w"), indent=1)
    fig, ax = ps.plt.subplots(figsize=(5, 3.8))
    rr = np.linspace(0, 1, 100)
    ax.plot(rr, 2 * (1 - rr ** 2), color=ps.TEXT, lw=1.2, ls="--", label="exact, 2U(1 - r²/R²)")
    for k, r in enumerate(out):
        ax.plot(r["r"], r["vz"], "o", ms=4 + k, color=ps.CAT[k], mfc="none", mew=1.5,
                label=f"this solver, {r['nr']} cells across R")
    ax.set_xlabel("r / R")
    ax.set_ylabel("u_z / U at z = 6 D")
    ax.set_title("Axisymmetric check: pipe flow", loc="left")
    ps.tidy(ax)
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig("pipe_validation.png", dpi=150)


if __name__ == "__main__":
    main()
