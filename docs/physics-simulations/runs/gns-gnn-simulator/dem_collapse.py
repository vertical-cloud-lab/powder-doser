"""Tiny 2D granular column-collapse DEM (numba) used to make GNS training data.

Discs (radius 0.007-0.009, density 1 per unit area), linear spring-dashpot normal
contact (k_n = 300, restitution 0.5), tangential force = viscously regularised
Coulomb friction (mu = 0.5, also on walls), translational DOF only (no disc
rotation, a crude stand-in for rolling resistance/angular grains). Dimensionless
units: box [0,1]^2, g = 1. A column of width W and height H rests against the
left wall behind a gate at x = W; the gate is removed at t = 0 and 150 frames are
saved every dt_frame = 0.0133 (t = 0..2).

Usage: python dem_collapse.py OUTDIR N_TRAIN N_VALID N_TEST SEED
"""
import json
import os
import sys
import time

import numpy as np
import numba as nb

KN = 300.0
E_REST = 0.5
MU = 0.5
G = 1.0
RMIN, RMAX = 0.007, 0.009
NFRAMES = 150
DT_FRAME = 2.0 / NFRAMES
ZETA = -np.log(E_REST) / np.sqrt(np.pi ** 2 + np.log(E_REST) ** 2)


@nb.njit(cache=True)
def step_forces(x, v, r, m, gate_x):
    n = x.shape[0]
    f = np.zeros_like(x)
    for i in range(n):
        f[i, 1] -= m[i] * G
    for i in range(n):
        for j in range(i + 1, n):
            dx = x[j, 0] - x[i, 0]
            dy = x[j, 1] - x[i, 1]
            rs = r[i] + r[j]
            if abs(dx) >= rs or abs(dy) >= rs:
                continue
            d2 = dx * dx + dy * dy
            if d2 >= rs * rs:
                continue
            d = np.sqrt(d2)
            nx = dx / d
            ny = dy / d
            delta = rs - d
            dvx = v[j, 0] - v[i, 0]
            dvy = v[j, 1] - v[i, 1]
            vn = dvx * nx + dvy * ny
            meff = m[i] * m[j] / (m[i] + m[j])
            c = 2.0 * ZETA * np.sqrt(KN * meff)
            fn = KN * delta - c * vn
            if fn < 0.0:
                fn = 0.0
            tx = -ny
            ty = nx
            vt = dvx * tx + dvy * ty
            ft = -c * 5.0 * vt
            lim = MU * fn
            if ft > lim:
                ft = lim
            elif ft < -lim:
                ft = -lim
            fx = fn * nx + ft * tx
            fy = fn * ny + ft * ty
            f[j, 0] += fx
            f[j, 1] += fy
            f[i, 0] -= fx
            f[i, 1] -= fy
    for i in range(n):
        c = 2.0 * ZETA * np.sqrt(KN * m[i])
        # floor y = 0
        delta = r[i] - x[i, 1]
        if delta > 0.0:
            fn = KN * delta - c * v[i, 1]
            if fn < 0.0:
                fn = 0.0
            ft = -c * 5.0 * v[i, 0]
            lim = MU * fn
            ft = min(max(ft, -lim), lim)
            f[i, 1] += fn
            f[i, 0] += ft
        # left wall x = 0
        delta = r[i] - x[i, 0]
        if delta > 0.0:
            fn = KN * delta - c * v[i, 0]
            if fn < 0.0:
                fn = 0.0
            ft = -c * 5.0 * v[i, 1]
            lim = MU * fn
            ft = min(max(ft, -lim), lim)
            f[i, 0] += fn
            f[i, 1] += ft
        # right wall (gate during settling, x = 1 afterwards)
        delta = x[i, 0] + r[i] - gate_x
        if delta > 0.0:
            fn = KN * delta + c * v[i, 0]
            if fn < 0.0:
                fn = 0.0
            ft = -c * 5.0 * v[i, 1]
            lim = MU * fn
            ft = min(max(ft, -lim), lim)
            f[i, 0] -= fn
            f[i, 1] += ft
    return f


@nb.njit(cache=True)
def integrate(x, v, r, m, gate_x, dt, nsteps, nsub, frames):
    k = 0
    for s in range(nsteps):
        f = step_forces(x, v, r, m, gate_x)
        for i in range(x.shape[0]):
            v[i, 0] += f[i, 0] / m[i] * dt
            v[i, 1] += f[i, 1] / m[i] * dt
            x[i, 0] += v[i, 0] * dt
            x[i, 1] += v[i, 1] * dt
        if nsub > 0 and (s + 1) % nsub == 0 and k < frames.shape[0]:
            frames[k] = x
            k += 1
    return k


def make_column(width, height, rng):
    s = 2.0 * RMAX * 1.02
    pts = []
    row = 0
    y = RMAX * 1.05
    while y < height:
        x0 = RMAX * 1.05 + (s / 2 if row % 2 else 0.0)
        xx = x0
        while xx < width - RMAX:
            pts.append((xx, y))
            xx += s
        y += s * np.sqrt(3) / 2
        row += 1
    x = np.array(pts, float)
    x += rng.uniform(-0.1, 0.1, x.shape) * (s - 2 * RMAX)
    r = rng.uniform(RMIN, RMAX, len(x))
    return x, r


def simulate(width, height, seed):
    rng = np.random.default_rng(seed)
    x, r = make_column(width, height, rng)
    m = np.pi * r ** 2
    v = np.zeros_like(x)
    tc = np.pi * np.sqrt((np.pi * RMIN ** 2 / 2) / KN)
    nsub = int(np.ceil(DT_FRAME / (tc / 15)))
    dt = DT_FRAME / nsub
    dummy = np.zeros((1, x.shape[0], 2))
    integrate(x, v, r, m, width, dt, int(0.8 / dt), 0, dummy)     # settle behind the gate
    v[:] = 0.0
    frames = np.zeros((NFRAMES + 1, x.shape[0], 2))
    frames[0] = x
    integrate(x, v, r, m, 1.0, dt, NFRAMES * nsub, nsub, frames[1:])
    return frames.astype(np.float32), r.astype(np.float32), dt


def runout(pos, r):
    """front position: max x of particles (after excluding 0.5 % outliers)."""
    return float(np.percentile(pos[:, 0], 99.5))


if __name__ == "__main__":
    out, ntr, nva, nte, seed = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4]), int(sys.argv[5])
    os.makedirs(out, exist_ok=True)
    rng = np.random.default_rng(seed)
    t0 = time.time()
    meta_cases = {}
    for split, n in (("train", ntr), ("valid", nva), ("test", nte)):
        trajs = {}
        for k in range(n):
            if split == "test":
                # held-out geometries: inside the training range and one taller column
                width, aspect = [(0.17, 1.6), (0.14, 2.6), (0.20, 1.0)][k % 3]
            else:
                width = rng.uniform(0.12, 0.22)
                aspect = rng.uniform(0.7, 2.4)
            height = min(aspect * width, 0.55)
            pos, r, dt = simulate(width, height, seed * 1000 + k + {"train": 0, "valid": 500, "test": 900}[split])
            trajs[f"{split}_{k}"] = (pos, np.full(pos.shape[1], 6, dtype=np.int64), r)
            meta_cases[f"{split}_{k}"] = {"W": round(width, 4), "H": round(height, 4), "N": int(pos.shape[1]),
                                         "runout_final": runout(pos[-1], r)}
            print(split, k, "W=%.3f H=%.3f N=%d runout=%.3f dt=%.2e  t=%.1fs" % (
                width, height, pos.shape[1], runout(pos[-1], r), dt, time.time() - t0), flush=True)
        np.savez_compressed(os.path.join(out, f"{split}.npz"),
                            **{k: np.array([v[0], v[1], v[2]], dtype=object) for k, v in trajs.items()})
    with open(os.path.join(out, "cases.json"), "w") as f:
        json.dump({"cases": meta_cases, "wall_s": time.time() - t0, "nframes": NFRAMES + 1,
                   "dt_frame": DT_FRAME, "kn": KN, "e": E_REST, "mu": MU}, f, indent=1)
    print("done", time.time() - t0)
