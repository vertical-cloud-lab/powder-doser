"""Poured angle of repose along the same flowability path as doser_path.py (LIGGGHTS-PUBLIC 3.8).

Same test as ../dem-liggghts-aor (4000 salt-sized grains poured from a 3 mm stream onto a 12 mm base,
ISO 4324 style, reduced scale), with the contact parameters of each path point:

    P0     mu_pp 0.3, mu_roll 0.1, k = 0
    P1     mu_pp 0.5, mu_roll 0.3, k = 0       (salt as in the #180 twin)
    kNNNN  salt friction plus SJKR cohesion energy density NNNN J/m3 between grains

The heap is read two ways: the sector-averaged profile slope, and the ISO 4324 apex formula atan(H/R),
which is how handbook and supplier repose angles are usually measured. predict.py uses the apex angle.

usage: python aor_path.py run NAME [NAME ...] | python aor_path.py summarize
"""
from __future__ import annotations

import json
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import ligcommon as L  # noqa: E402

SCRATCH = os.environ.get("SCRATCH", "/tmp/sims-scratch/heldout-powders")
R_BASE = 6.0e-3
N_POUR = 4000
RATE = 8000
T_SETTLE = 0.35

POINTS = {
    "P0": {"mu_pp": 0.3, "mu_roll": 0.1, "ced": 0.0},
    "P1": {"mu_pp": 0.5, "mu_roll": 0.3, "ced": 0.0},
    "k750": {"ced": 750.0},
    "k1500": {"ced": 1500.0},
    "k2250": {"ced": 2250.0},
    "k3000": {"ced": 3000.0},
    "k4500": {"ced": 4500.0},
    "k6000": {"ced": 6000.0},
    "k7500": {"ced": 7500.0},
    "k9000": {"ced": 9000.0},
}


def disk_stl(path, R, z, n=96):
    with open(path, "w") as f:
        f.write("solid base\n")
        for i in range(n):
            a0, a1 = 2 * math.pi * i / n, 2 * math.pi * (i + 1) / n
            p = [(0, 0, z), (R * math.cos(a0), R * math.sin(a0), z), (R * math.cos(a1), R * math.sin(a1), z)]
            f.write("facet normal 0 0 1\nouter loop\n")
            for q in p:
                f.write(f"vertex {q[0]:.6e} {q[1]:.6e} {q[2]:.6e}\n")
            f.write("endloop\nendfacet\n")
        f.write("endsolid base\n")


def build(name, wd):
    p = {"mu_pp": 0.5, "mu_roll": 0.3, "ced": 0.0, **POINTS[name]}
    L.SALT["mu_pp"], L.SALT["mu_roll"] = p["mu_pp"], p["mu_roll"]   # header() reads SALT at call time
    os.makedirs(os.path.join(wd, "dump"), exist_ok=True)
    disk_stl(os.path.join(wd, "base.stl"), R_BASE, 0.0)
    box = (-9e-3, 9e-3, -9e-3, 9e-3, -3e-3, 16e-3)
    head, wall_model, dt = L.header(box, ced=p["ced"])
    steps = lambda s: int(round(s / dt))  # noqa: E731
    deck = head + f"""
fix base all mesh/surface file base.stl type 2
fix walls all wall/gran {wall_model} mesh n_meshes 1 meshes base
region pour cylinder z 0. 0. 1.5e-3 1.0e-2 1.4e-2 units box
fix ins all insert/rate/region seed 86028157 distributiontemplate pdd nparticles {N_POUR} particlerate {RATE} insert_every {steps(0.01)} overlapcheck yes all_in yes vel constant 0. 0. -0.1 region pour ntry_mc 5000
fix integr all nve/sphere
variable t equal time
variable n equal atoms
thermo_style custom step time atoms ke
thermo {steps(0.05)}
thermo_modify lost ignore norm no flush yes
dump dmp all custom {steps(0.05)} dump/p.*.txt id type radius x y z vx vy vz
run {steps(N_POUR / RATE + T_SETTLE)}
"""
    with open(os.path.join(wd, "in.aor"), "w") as f:
        f.write(deck)
    return dt, p


def heap_profile(d, nbins=15, nsect=8):
    x, y, z, r = d["x"], d["y"], d["z"], d["radius"]
    rr = np.hypot(x, y)
    keep = (z > -0.5e-3) & (rr < R_BASE + 0.5e-3)
    x, y, z, r, rr = x[keep], y[keep], z[keep], r[keep], rr[keep]
    top = z + r
    edges = np.linspace(0, R_BASE, nbins + 1)
    th = np.arctan2(y, x)
    sect = ((th + math.pi) / (2 * math.pi) * nsect).astype(int) % nsect
    prof = np.full((nsect, nbins), np.nan)
    for s in range(nsect):
        for b in range(nbins):
            m = (sect == s) & (rr >= edges[b]) & (rr < edges[b + 1])
            if m.any():
                prof[s, b] = top[m].max()
    rc = 0.5 * (edges[1:] + edges[:-1])
    h = np.nanmean(prof, axis=0)
    fit = (rc > 1.0e-3) & (rc < 5.2e-3) & np.isfinite(h)
    pf = np.polyfit(rc[fit], h[fit], 1)
    angs = []
    for s in range(nsect):
        ok = fit & np.isfinite(prof[s])
        if ok.sum() > 4:
            angs.append(math.degrees(math.atan(-np.polyfit(rc[ok], prof[s, ok], 1)[0])))
    H = top[rr < 1.0e-3].max() if (rr < 1.0e-3).any() else float("nan")
    return dict(angle_fit_deg=math.degrees(math.atan(-pf[0])),
                angle_fit_sector_std_deg=float(np.std(angs)) if angs else None,
                apex_height_mm=float(H * 1e3), angle_iso_deg=math.degrees(math.atan(H / R_BASE)),
                n_on_base=int(keep.sum()), r_mm=(rc * 1e3).tolist(), h_mm=(h * 1e3).tolist())


def run(name):
    wd = os.path.join(SCRATCH, "aor_" + name)
    dt, p = build(name, wd)
    rc, wall, tail = L.run_liggghts(wd, "in.aor")
    res = {"point": name, "params": p, "dt": dt, "rc": rc, "wall_s": wall}
    if rc == 0:
        files = L.dump_series(os.path.join(wd, "dump", "p.*.txt"))
        _, d = L.read_dump(files[-1])
        res.update(heap_profile(d))
    else:
        res["error_tail"] = tail[-2000:]
    L.write_json(os.path.join(wd, "run.json"), res)
    print({k: res.get(k) for k in ("point", "angle_fit_deg", "angle_iso_deg", "n_on_base", "wall_s")}, flush=True)
    return rc


def main():
    cmd = sys.argv[1]
    if cmd == "run":
        sys.exit(max(run(n) for n in sys.argv[2:]))
    if cmd == "summarize":
        out = []
        for n in POINTS:
            f = os.path.join(SCRATCH, "aor_" + n, "run.json")
            if os.path.exists(f):
                out.append(json.load(open(f)))
        with open(os.path.join(HERE, "aor_path.json"), "w") as f:
            json.dump(out, f, indent=1)
        for r in out:
            print({k: r.get(k) for k in ("point", "angle_fit_deg", "angle_iso_deg", "n_on_base")})


if __name__ == "__main__":
    main()
