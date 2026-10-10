"""How many particles fit in one auger? Throughput and memory scaling.

Fills the *entire* 250 mm bore of the parametric auger (23 flight turns +
funnel; the default open-core AugerParams) with a
dense FCC packing of monodisperse spheres (0.2 % initial overlap, so
every particle starts with its full contact set), then times a fixed
number of LIGGGHTS steps against the static mesh. Particle diameter
sets the count: 0.9 mm -> 0.11 M ... 0.35 mm -> 2.05 M particles.

Reports wall time per step, particle-steps per second, and peak RSS
(memory) per particle, which is what limits a CPU twin.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import re
import subprocess
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from geometry import AugerParams, auger_triangles, write_ascii_stl  # noqa: E402
from run_case import free_point_mask, write_data  # noqa: E402

TEMPLATE = """atom_style granular
atom_modify map array
boundary f f f
newton off
communicate single vel yes
units si
soft_particles yes
processors 1 1 *
read_data data.init
neighbor {skin:.3e} bin
neigh_modify delay 0
fix m1 all property/global youngsModulus peratomtype 2e5 2e5
fix m2 all property/global poissonsRatio peratomtype 0.3 0.3
fix m3 all property/global coefficientRestitution peratomtypepair 2 0.5 0.5 0.5 0.5
fix m4 all property/global coefficientFriction peratomtypepair 2 0.5 0.4 0.4 0.4
fix m5 all property/global coefficientRollingFriction peratomtypepair 2 0.3 0.3 0.3 0.3
pair_style gran model hertz tangential history rolling_friction epsd2
pair_coeff * *
timestep {dt:.4e}
fix gravi all gravity 9.81 vector -0.866025 0. -0.5
fix auger all mesh/surface file auger.stl type 2 scale 0.001 curvature_tolerant yes
fix walls all wall/gran model hertz tangential history rolling_friction epsd2 mesh n_meshes 1 meshes auger
fix integr all nve/sphere
thermo {steps}
thermo_modify lost ignore norm no
run {warm}
run {steps}
"""


def dense_packing(P, d, z_max):
    s = 0.998 * d
    a = s * math.sqrt(2)
    R = P.bore_r
    nx = int(math.ceil(2 * R / a)) + 1
    nz = int(math.ceil(z_max / a)) + 1
    base = np.array([[0, 0, 0], [0.5, 0.5, 0], [0.5, 0, 0.5], [0, 0.5, 0.5]])
    out = []
    for kz in range(nz):  # slab by slab keeps memory flat for millions of points
        g = np.stack(np.meshgrid(np.arange(-nx, nx), np.arange(-nx, nx), [kz], indexing="ij"), -1).reshape(-1, 3)
        pts = (g[:, None, :] + base[None]).reshape(-1, 3) * a
        pts[:, 2] += 0.55 * d
        pts = pts[(pts[:, 2] < z_max) & (np.hypot(pts[:, 0], pts[:, 1]) < R)]
        if len(pts):
            out.append(pts[free_point_mask(P, pts, d / 2, margin=1.01)])
    return np.concatenate(out)


def run_one(d_mm, workdir, steps=150, warm=20):
    os.makedirs(workdir, exist_ok=True)
    P = AugerParams(n_turns=23, feed_h=4.0)  # full 250 mm bore
    write_ascii_stl(os.path.join(workdir, "auger.stl"), auger_triangles(P))
    pts = dense_packing(P, d_mm, P.flight_top + P.flight_t)
    R = P.bore_r + 1.0
    box = (-R * 1e-3, R * 1e-3, -R * 1e-3, R * 1e-3, -2e-3, (P.z_top + 2) * 1e-3)
    write_data(os.path.join(workdir, "data.init"), pts, np.full(len(pts), d_mm), 2160.0, box)
    G = 2e5 / 2.6
    dt = 0.2 * math.pi * (d_mm / 2e3) * math.sqrt(2160 / G) / (0.1631 * 0.3 + 0.8766)
    with open(os.path.join(workdir, "in.bench"), "w") as f:
        f.write(TEMPLATE.format(skin=0.5 * d_mm * 1e-3, dt=dt, steps=steps, warm=warm))
    t0 = time.time()
    p = subprocess.run(["/usr/bin/time", "-v", "liggghts", "-in", "in.bench", "-log", "log.bench", "-echo", "none",
                        "-screen", "screen.txt"], cwd=workdir, capture_output=True, text=True)
    wall = time.time() - t0
    rss_kb = int(re.search(r"Maximum resident set size \(kbytes\): (\d+)", p.stderr).group(1))
    loops = re.findall(r"Loop time of ([\d.eE+-]+) on \d+ procs for (\d+) steps with (\d+) atoms",
                       open(os.path.join(workdir, "screen.txt")).read())
    loop_t, n_steps, n_atoms = float(loops[-1][0]), int(loops[-1][1]), int(loops[-1][2])
    res = {"d_mm": d_mm, "n_particles": n_atoms, "steps": n_steps, "loop_s": loop_t,
           "s_per_step": loop_t / n_steps, "particle_steps_per_s": n_atoms * n_steps / loop_t,
           "peak_rss_mb": rss_kb / 1024, "bytes_per_particle": rss_kb * 1024 / n_atoms,
           "dt_s": dt, "total_wall_s": wall, "rc": p.returncode}
    print(json.dumps(res), flush=True)
    return res


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--diams", default="0.9,0.6,0.45,0.35")
    ap.add_argument("--root", default="/tmp/dem/bench")
    ap.add_argument("--out", default="bench_results.jsonl")
    a = ap.parse_args()
    for dm in [float(x) for x in a.diams.split(",")]:
        r = run_one(dm, os.path.join(a.root, f"d{dm:.2f}"))
        with open(a.out, "a") as f:
            f.write(json.dumps(r) + "\n")
