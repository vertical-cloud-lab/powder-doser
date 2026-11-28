"""Validation 3: the transient diffusion solver (scalar.py, 3D, backward Euler) against the
analytical solution for a slab (length H) with a fixed value at z = 0 and no flux at z = H:
    phi(z, t) = 1 - sum_n 4/((2n+1) pi) sin((2n+1) pi z / 2H) exp(-(2n+1)^2 pi^2 D t / 4H^2)
H = 80 mm, D = 2.5e-5 m2/s (water vapour in air): the height scale of the humidity box.
Writes diffusion_validation.json and diffusion_validation.png.
"""
import json
import numpy as np
from scalar import Grid, Transport
import plotstyle as ps

D, H = 2.5e-5, 0.080


def exact(z, t, nterm=200):
    s = np.zeros_like(np.asarray(z, float))
    for n in range(nterm):
        k = 2 * n + 1
        s = s + 4 / (k * np.pi) * np.sin(k * np.pi * z / (2 * H)) * np.exp(-k * k * np.pi ** 2 * D * t / (4 * H * H))
    return 1 - s


def run(h, dt):
    nz = int(round(H / h))
    g = Grid((3, 3, nz), h, D)
    bottom = g.idx[:, :, 0].ravel()
    tr = Transport(g, dirichlet=(bottom, np.full(bottom.size, D * g.area / (h / 2) * g.csat), 1.0))
    phi = np.zeros(g.n)
    zc = (np.arange(nz) + 0.5) * h
    ts, top, mid = [0.0], [0.0], [0.0]
    t = 0.0
    while t < 900.0 - 1e-9:
        phi = tr.step(phi, dt, solver="cg")
        t += dt
        p = phi.reshape(g.shape)[1, 1, :]
        ts.append(t)
        top.append(np.interp(H, np.r_[zc, H], np.r_[p, p[-1]]))
        mid.append(np.interp(H / 2, zc, p))
    ts = np.array(ts)
    ex_top = exact(H, np.maximum(ts, 1e-9))
    ex_mid = exact(H / 2, np.maximum(ts, 1e-9))
    err = max(np.abs(np.array(top) - ex_top).max(), np.abs(np.array(mid) - ex_mid).max())
    # time to reach 0.95 of the step at z = H
    def t_reach(y, lev):
        y = np.asarray(y)
        k = np.argmax(y >= lev)
        return float(np.interp(lev, [y[k - 1], y[k]], [ts[k - 1], ts[k]]))
    return dict(h_mm=h * 1e3, dt_s=dt, max_abs_err=float(err), t95_top=t_reach(top, 0.95),
                t99_top=t_reach(top, 0.99), t=ts.tolist(), top=list(map(float, top)), mid=list(map(float, mid)))


def main():
    # analytical t95 / t99 at z = H
    tt = np.linspace(1, 2000, 200000)
    e = exact(H, tt)
    t95 = float(tt[np.argmax(e >= 0.95)])
    t99 = float(tt[np.argmax(e >= 0.99)])
    runs = []
    for h, dt in ((0.010, 4.0), (0.005, 2.0), (0.0025, 1.0), (0.0025, 0.25)):
        r = run(h, dt)
        print(f"h = {h*1e3:.1f} mm, dt = {dt} s: max err {r['max_abs_err']:.4f}, t95 {r['t95_top']:.1f} s "
              f"(exact {t95:.1f}), t99 {r['t99_top']:.1f} s (exact {t99:.1f})", flush=True)
        runs.append(r)
    json.dump(dict(case="1D slab diffusion through the 3D solver", D=D, H=H, t95_exact=t95, t99_exact=t99,
                   runs=runs), open("diffusion_validation.json", "w"), indent=1)
    fig, ax = ps.plt.subplots(figsize=(5.4, 3.8))
    tf = np.linspace(0.5, 900, 400)
    ax.plot(tf, exact(H, tf), color=ps.TEXT, lw=1.2, ls="--", label="exact, z = H")
    ax.plot(tf, exact(H / 2, tf), color=ps.TEXT2, lw=1.2, ls=":", label="exact, z = H/2")
    for k, r in enumerate(runs[:3]):
        ax.plot(r["t"][::4], r["top"][::4], "o", ms=4, color=ps.CAT[k], mfc="none",
                label=f"solver, h = {r['h_mm']:.1f} mm, dt = {r['dt_s']:.0f} s")
        ax.plot(r["t"][::4], r["mid"][::4], "s", ms=4, color=ps.CAT[k], mfc="none")
    ax.set_xlabel("time after the step (s)")
    ax.set_ylabel("fraction of the step")
    ax.set_title("Diffusion check: 80 mm slab, D = 2.5e-5 m²/s", loc="left")
    ps.tidy(ax)
    ax.legend(fontsize=7.5)
    fig.tight_layout()
    fig.savefig("diffusion_validation.png", dpi=150)


if __name__ == "__main__":
    main()
