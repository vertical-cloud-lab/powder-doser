"""Blade recoating of a powder layer (powder-bed AM spreadability) with LIGGGHTS-PUBLIC 3.8.

A 4.25 mm wide, y-periodic slice. A heap of salt grains rests on a flat plate in front of a
vertical blade; the blade (a dense wall of frozen 0.2 mm spheres moved with fix move) travels
at 50 mm/s with its lower edge GAP above the plate and leaves a layer behind it.
The layer's packing fraction (grain volume inside 0 < z < GAP per plate area x GAP) and the
plate coverage (projected area of layer grains) are measured in 2 mm bins along the plate.

usage: python run.py VARIANT [--analyze-only]    VARIANT = dry | coh
"""
import argparse
import json
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import ligcommon as L  # noqa: E402

SCRATCH = os.environ.get("SCRATCH", "/tmp/sims-scratch/dem-liggghts-spread")
W = 4.25e-3                 # periodic width (10 mean diameters)
LXB = 40e-3
GAP = 2.5 * 0.425e-3        # blade gap = 2.5 mean diameters = 1.06 mm (2.2 d_max)
V_BLADE = 0.05              # m/s
X_B0, X_B1 = 1.0e-3, 36.0e-3
N_HEAP = 2500
DB, SB = 0.2e-3, 0.17e-3    # blade sphere diameter and spacing
BLADE_H = 6.0e-3
T_SETTLE = 0.2
X_MEAS = (12e-3, 32e-3)


def build(variant, wd):
    os.makedirs(os.path.join(wd, "dump"), exist_ok=True)
    ced = L.CED_COHESIVE if variant == "coh" else 0.0
    box = (0.0, LXB, 0.0, W, -0.5e-3, 12e-3)
    head, wall_model, dt = L.header(box, periodic="f p f", ced=ced)
    steps = lambda s: int(round(s / dt))  # noqa: E731
    ny = int(round(W / SB))
    sy = W / ny
    nz = int((BLADE_H - DB) / SB) + 1
    lines = []
    for j in range(ny):
        for k in range(nz):
            lines.append(f"create_atoms 1 single {X_B0:.6e} {(j + 0.5) * sy:.6e} {GAP + 0.5 * DB + k * SB:.6e} units box")
    t_spread = (X_B1 - X_B0) / V_BLADE
    deck = head + f"""
region bladereg block {X_B0 - 0.2e-3:.6e} {X_B0 + 0.2e-3:.6e} INF INF {GAP:.6e} {GAP + BLADE_H + 0.2e-3:.6e} units box
""" + "\n".join(lines) + f"""
group blade region bladereg
set group blade diameter {DB:.6e}
set group blade density {L.SALT['density']}
fix plate all wall/gran {wall_model} primitive type 2 zplane 0.0
fix dam all wall/gran {wall_model} primitive type 2 xplane {X_B0 + 0.25e-3:.6e}
region heapreg block {X_B0 + 0.35e-3:.6e} 9.0e-3 0. {W:.6e} 0.3e-3 9.5e-3 units box
group grains region heapreg
fix ins grains insert/pack seed 86028157 distributiontemplate pdd insert_every once overlapcheck yes all_in yes particles_in_region {N_HEAP} region heapreg ntry_mc 20000
fix integr grains nve/sphere
fix bmove blade move linear 0.0 0.0 0.0
variable t equal time
thermo_style custom step time atoms ke
thermo {steps(0.05)}
thermo_modify lost ignore norm no flush yes
dump dmp all custom {steps(0.02)} dump/p.*.txt id type radius x y z vx vy vz
run {steps(T_SETTLE)}
unfix dam
unfix bmove
fix bmove blade move linear {V_BLADE} 0.0 0.0
run {steps(t_spread)}
unfix bmove
fix bmove blade move linear 0.0 0.0 0.0
run {steps(0.06)}
write_dump all custom dump/final.txt id type radius x y z vx vy vz
"""
    with open(os.path.join(wd, "in.spread"), "w") as f:
        f.write(deck)
    return dt, ny * nz


def slab_vol(z, r, z0, z1):
    def below(h, r):
        h = np.clip(h, -r, r)
        return math.pi * (r + h) ** 2 * (2 * r - h) / 3.0
    return below(z1 - z, r) - below(z0 - z, r)


def layer_stats(d, nblade):
    x, y, z, r = d["x"], d["y"], d["z"], d["radius"]
    grain = r > 0.15e-3
    x, y, z, r = x[grain], y[grain] % W, z[grain], r[grain]
    edges = np.arange(X_MEAS[0], X_MEAS[1] + 1e-9, 2e-3)
    rows = []
    pix = 0.02e-3
    for a, b in zip(edges[:-1], edges[1:]):
        m = (x > a - 0.5e-3) & (x < b + 0.5e-3) & (z - r < GAP)
        v = slab_vol(z[m], r[m], 0.0, GAP)
        # only the part of each grain inside the bin in x (approximate: by centre)
        inb = (x[m] >= a) & (x[m] < b)
        phi = float(np.sum(v[inb]) / ((b - a) * W * GAP))
        # coverage: rasterise projected discs of layer grains (centre below GAP) on the plate
        gx = np.arange(a + pix / 2, b, pix)
        gy = np.arange(pix / 2, W, pix)
        X, Y = np.meshgrid(gx, gy, indexing="ij")
        cov = np.zeros_like(X, dtype=bool)
        mm = m & (z < GAP)
        for xi, yi, ri in zip(x[mm], y[mm], r[mm]):
            for yy in (yi - W, yi, yi + W):
                ix0, ix1 = np.searchsorted(gx, [xi - ri, xi + ri])
                iy0, iy1 = np.searchsorted(gy, [yy - ri, yy + ri])
                if ix1 <= ix0 or iy1 <= iy0:
                    continue
                sub = (X[ix0:ix1, iy0:iy1] - xi) ** 2 + (Y[ix0:ix1, iy0:iy1] - yy) ** 2 < ri ** 2
                cov[ix0:ix1, iy0:iy1] |= sub
        mass = float(np.sum((4 / 3 * math.pi * r[m][inb] ** 3)) * L.SALT["density"])
        rows.append(dict(x0_mm=a * 1e3, x1_mm=b * 1e3, phi_layer=phi, coverage=float(cov.mean()),
                         mass_per_area_kg_m2=mass / ((b - a) * W), n=int(inb.sum())))
    phis = np.array([q["phi_layer"] for q in rows])
    covs = np.array([q["coverage"] for q in rows])
    mpa = np.array([q["mass_per_area_kg_m2"] for q in rows])
    return dict(bins=rows, phi_layer_mean=float(phis.mean()), phi_layer_std=float(phis.std()),
                coverage_mean=float(covs.mean()), coverage_min=float(covs.min()),
                mass_per_area_cv=float(mpa.std() / mpa.mean()) if mpa.mean() > 0 else None,
                n_grains_total=int(grain.sum()), n_blade=nblade)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("variant")
    ap.add_argument("--analyze-only", action="store_true")
    a = ap.parse_args()
    wd = os.path.join(SCRATCH, a.variant)
    os.makedirs(wd, exist_ok=True)
    dt, nblade = build(a.variant, wd)
    res = {"variant": a.variant, "dt": dt}
    runjson = os.path.join(wd, "run.json")
    if not a.analyze_only:
        rc, wall, tail = L.run_liggghts(wd, "in.spread")
        res.update(rc=rc, wall_s=wall)
        if rc != 0:
            res["error_tail"] = tail[-2500:]
            L.write_json(runjson, res)
            print(tail[-2500:])
            sys.exit(rc)
    elif os.path.exists(runjson):
        res.update({k: v for k, v in json.load(open(runjson)).items() if k in ("rc", "wall_s")})
    _, d = L.read_dump(os.path.join(wd, "dump", "final.txt"))
    res.update(layer_stats(d, nblade))
    L.write_json(runjson, res)
    print({k: res[k] for k in ("variant", "phi_layer_mean", "phi_layer_std", "coverage_mean", "coverage_min", "mass_per_area_cv")})


if __name__ == "__main__":
    main()
