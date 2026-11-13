"""Rotating drum (dynamic angle of repose, GranuDrum / Revolution-style) with LIGGGHTS-PUBLIC 3.8.

A 16 mm diameter drum, axis along y, simulated as a 2.55 mm thick y-periodic slice (no end walls).
The drum wall is a ring of frozen 0.3 mm spheres rotated rigidly with fix move rotate (a rough
wall, so the bed does not slip). The free-surface angle is fitted to the top of the bed across
the middle of the chord in each dump and averaged over the steady part of the run.

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

SCRATCH = os.environ.get("SCRATCH", "/tmp/sims-scratch/dem-liggghts-drum")
R = 8.0e-3                 # drum inner radius
W = 6 * 0.425e-3           # slice thickness (periodic)
DW, SW = 0.3e-3, 0.25e-3   # wall sphere diameter, spacing
N = 2400                   # grains (about 35 % fill)
RPM = 20.0
T_FILL = 0.25
T_ROT = 1.2
T_AVG0 = 0.6               # average the angle over rotation time > T_AVG0


def build(variant, wd):
    os.makedirs(os.path.join(wd, "dump"), exist_ok=True)
    ced = L.CED_COHESIVE if variant == "coh" else 0.0
    B = R + 0.6e-3
    box = (-B, B, 0.0, W, -B, B)
    head, wall_model, dt = L.header(box, periodic="f p f", ced=ced)
    steps = lambda s: int(round(s / dt))  # noqa: E731
    rw = R + 0.5 * DW - 0.05e-3        # wall sphere centres (protrude 0.1 mm into the drum)
    nth = int(2 * math.pi * rw / SW)
    ny = int(round(W / SW))
    sy = W / ny
    lines = []
    for i in range(nth):
        a = 2 * math.pi * i / nth
        for j in range(ny):
            off = 0.5 * (j % 2) * 2 * math.pi / nth
            lines.append(f"create_atoms 1 single {rw * math.cos(a + off):.6e} {(j + 0.5) * sy:.6e} {rw * math.sin(a + off):.6e} units box")
    period = 60.0 / RPM
    deck = head + "\n".join(lines) + f"""
region wallreg cylinder y 0. 0. {R - 0.1e-3:.6e} INF INF side out units box
group wallp region wallreg
set group wallp diameter {DW:.6e}
set group wallp density {L.SALT['density']}
region fillreg cylinder y 0. 0. {R - 0.5e-3:.6e} 0. {W:.6e} units box
region fillcut block INF INF INF INF INF 3.0e-3 units box
region fill intersect 2 fillreg fillcut
group grains region fill
fix ins grains insert/pack seed 86028157 distributiontemplate pdd insert_every once overlapcheck yes all_in yes particles_in_region {N} region fill ntry_mc 20000
fix integr grains nve/sphere
variable t equal time
thermo_style custom step time atoms ke
thermo {steps(0.05)}
thermo_modify lost ignore norm no flush yes
dump dmp all custom {steps(0.02)} dump/p.*.txt id type radius x y z vx vy vz
run {steps(T_FILL)}
fix rot wallp move rotate 0. 0. 0. 0. -1. 0. {period:.6f}
run {steps(T_ROT)}
"""
    with open(os.path.join(wd, "in.drum"), "w") as f:
        f.write(deck)
    return dt, nth * ny


def surface_angle(d):
    x, z, r = d["x"], d["z"], d["radius"]
    g = r > 0.16e-3
    x, z, r = x[g], z[g], r[g]
    top = z + r
    # chord of the free surface: take bins over the central 60 % of the bed's x-extent at the surface
    xs = np.linspace(-0.6 * R, 0.6 * R, 25)
    xc, hc = [], []
    for a, b in zip(xs[:-1], xs[1:]):
        m = (x >= a) & (x < b)
        if m.sum() > 3:
            xc.append(0.5 * (a + b))
            hc.append(np.max(top[m]))
    xc, hc = np.array(xc), np.array(hc)
    if len(xc) < 6:
        return float("nan"), None
    p = np.polyfit(xc, hc, 1)
    return math.degrees(math.atan(abs(p[0]))), (xc, hc, p)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("variant")
    ap.add_argument("--analyze-only", action="store_true")
    a = ap.parse_args()
    wd = os.path.join(SCRATCH, a.variant)
    os.makedirs(wd, exist_ok=True)
    dt, nwall = build(a.variant, wd)
    res = {"variant": a.variant, "dt": dt, "n_wall_spheres": nwall, "rpm": RPM,
           "froude": (2 * math.pi * RPM / 60) ** 2 * R / 9.81}
    runjson = os.path.join(wd, "run.json")
    if not a.analyze_only:
        rc, wall, tail = L.run_liggghts(wd, "in.drum")
        res.update(rc=rc, wall_s=wall)
        if rc != 0:
            res["error_tail"] = tail[-2500:]
            L.write_json(runjson, res)
            print(tail[-2500:])
            sys.exit(rc)
    elif os.path.exists(runjson):
        res.update({k: v for k, v in json.load(open(runjson)).items() if k in ("rc", "wall_s")})
    files = L.dump_series(os.path.join(wd, "dump", "p.*.txt"))
    ts, angs = [], []
    for f in files:
        step, d = L.read_dump(f)
        t = step * dt - T_FILL
        ang, _ = surface_angle(d)
        ts.append(t)
        angs.append(ang)
    ts, angs = np.array(ts), np.array(angs)
    m = ts > T_AVG0
    res.update(t_rot=ts.tolist(), angle_deg=[None if not np.isfinite(v) else float(v) for v in angs],
               dyn_angle_mean_deg=float(np.nanmean(angs[m])), dyn_angle_std_deg=float(np.nanstd(angs[m])),
               n_grains=int(np.sum(L.read_dump(files[-1])[1]["radius"] > 0.16e-3)))
    L.write_json(runjson, res)
    print({k: res[k] for k in ("variant", "dyn_angle_mean_deg", "dyn_angle_std_deg", "n_grains", "froude")})


if __name__ == "__main__":
    main()
