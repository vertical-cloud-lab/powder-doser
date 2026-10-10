"""Run one LIGGGHTS auger-dosing case and collect the outflow time series.

A case is a JSON-able dict (see DEFAULTS). The pipeline is:

1. ``geometry.py`` meshes the bottom ``n_turns`` of the rotating auger
   plus a counting disk 1.5 mm below the exit hole.
2. ``initial_packing`` fills every free voxel of the meshed section
   (bore, open core, funnel and the feed zone above the last flight)
   with a jittered FCC lattice of polydisperse spheres, written as a
   LIGGGHTS data file, so no particle starts inside the flight.
3. LIGGGHTS settles the column under tilted gravity with the exit
   plugged, removes the plug, then spins the mesh for ``revs``
   revolutions while ``insert/rate/region`` keeps the feed zone topped
   up. ``fix massflow/mesh`` counts (and deletes) every particle that
   falls through the counting disk; its cumulative mass is logged every
   ``log_every_s`` seconds.
4. Optionally the motor stops for ``stop_s`` seconds to measure
   afterflow (mass that leaves after the auger stops).

Gravity is tilted rather than the mesh: ``incline_deg`` is the angle of
the auger axis above horizontal (90 = exit straight down).
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
from dataclasses import asdict

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from geometry import AugerParams, auger_triangles, write_ascii_stl, write_disk_stl  # noqa: E402

DEFAULTS = {
    "name": "case",
    "geometry": {},
    # powder (SI). Salt defaults: NaCl crystals, d50 about 0.4 mm.
    "d_mean_mm": 0.40,
    "d_spread": 0.15,           # +- fraction for the 3-size distribution
    "density": 2160.0,
    "youngs": 5.0e6,            # softened, standard DEM practice
    "poisson": 0.3,
    "restitution": 0.5,
    "mu_pp": 0.5,               # sliding friction particle-particle
    "mu_pw": 0.4,               # particle-wall (PLA)
    "mu_roll": 0.3,             # EPSD2 rolling friction (stands in for angular shape)
    "ced": 0.0,                 # SJKR cohesion energy density J/m3 (0 = dry)
    "incline_deg": 45.0,
    "rpm": 30.0,
    "revs": 2.0,
    "settle_s": 0.25,
    "stop_s": 0.0,
    "dt": None,                 # auto from Rayleigh time if None
    "log_every_s": 0.005,
    "dump_every_s": 0.0,        # 0 = no particle dumps
    "dump_start_s": 0.0,
    "np": 4,
    "fill_frac": 1.0,           # fraction of the meshed height to pre-fill
    "fill_x_max_mm": None,      # pre-fill only x < this (gravity's side component is -x)
    "feed": True,
    "seed": 12345,
}


def rayleigh_dt(d, rho, E, nu):
    G = E / (2 * (1 + nu))
    r = d / 2
    return math.pi * r * math.sqrt(rho / G) / (0.1631 * nu + 0.8766)


def free_point_mask(P, pts, rad, margin=1.02):
    """True where a sphere of radius rad at pts (mm) clears all walls."""
    x, y, z = pts[:, 0], pts[:, 1], pts[:, 2]
    r = np.hypot(x, y)
    th = np.arctan2(y, x)
    ok = np.ones(len(pts), bool)
    c = rad * margin
    # bore
    ok &= r < P.bore_r - c
    # funnel cone (z < funnel_h): r < cone radius minus normal clearance
    zc = z < P.funnel_h + c
    slope = (P.funnel_top_r - P.exit_r) / P.funnel_h
    rc = P.exit_r + slope * z
    ok &= ~zc | (r < rc - c * math.sqrt(1 + slope ** 2))
    ok &= z > c
    # solid core: cylinder above the funnel, conical tip (or flat cap) below
    if P.shaft_r > 0:
        ok &= (r > P.shaft_r + c) | (z < P.funnel_h - c)
        if P.tip_r is not None:
            ts = (P.shaft_r - P.tip_r) / P.funnel_h
            rt = P.tip_r + ts * np.clip(z, P.tip_z0, None)
            ok &= (z >= P.funnel_h) | (z < P.tip_z0 - c) | (r > rt + c * math.sqrt(1 + ts ** 2))
    # flight: helical phase distance
    r_in = max(P.core_r, P.shaft_r)
    lead = P.pitch * P.starts
    z_start = max(P.flight_z0, P.tip_z0) if P.flight_into_funnel else P.funnel_h
    in_flight_band = (r > r_in - c) | ((z < P.funnel_h) & (P.tip_r is not None))
    for k in range(P.starts):
        ph = 2 * np.pi * k / P.starts
        theta = np.mod(th - ph, 2 * np.pi)
        zl = z - P.funnel_h - lead * theta / (2 * np.pi)
        u = np.mod(zl, lead)
        rr = np.maximum(r, 1e-6)
        helix_tan = lead / (2 * np.pi * rr)
        ax_clear = c * np.sqrt(1 + helix_tan ** 2)
        clash = (u < P.flight_t + ax_clear) | (u > lead - ax_clear)
        within = (z > z_start - 2 * c) & (z < P.flight_top + P.flight_t + 2 * c)
        ok &= ~(in_flight_band & within & clash)
    return ok


def initial_packing(P, d_mean, spread, z_max, seed=0):
    rng = np.random.default_rng(seed)
    d_max = d_mean * (1 + spread)
    s = 1.03 * d_max                      # nearest-neighbour spacing
    a = s * math.sqrt(2)                  # FCC lattice constant
    R = P.bore_r
    nx = int(math.ceil(2 * R / a)) + 1
    nz = int(math.ceil(z_max / a)) + 1
    base = np.array([[0, 0, 0], [0.5, 0.5, 0], [0.5, 0, 0.5], [0, 0.5, 0.5]])
    g = np.stack(np.meshgrid(np.arange(-nx, nx), np.arange(-nx, nx), np.arange(0, nz), indexing="ij"), -1).reshape(-1, 3)
    pts = (g[:, None, :] + base[None]).reshape(-1, 3) * a
    pts[:, 2] += 0.6 * d_max
    pts = pts[(np.abs(pts[:, 0]) < R) & (np.abs(pts[:, 1]) < R) & (pts[:, 2] < z_max)]
    pts += rng.uniform(-0.01, 0.01, pts.shape) * d_mean
    choice = rng.choice(3, size=len(pts), p=[0.3, 0.4, 0.3])
    diam = d_mean * np.array([1 - spread, 1.0, 1 + spread])[choice]
    ok = free_point_mask(P, pts, d_max / 2)
    return pts[ok], diam[ok]


def write_data(path, pts_mm, diam_mm, rho, box):
    with open(path, "w") as f:
        f.write("LIGGGHTS data file: initial auger packing\n\n")
        f.write(f"{len(pts_mm)} atoms\n2 atom types\n\n")
        f.write(f"{box[0]} {box[1]} xlo xhi\n{box[2]} {box[3]} ylo yhi\n{box[4]} {box[5]} zlo zhi\n\n")
        f.write("Atoms\n\n")
        for i, (p, d) in enumerate(zip(pts_mm, diam_mm), 1):
            f.write(f"{i} 1 {d * 1e-3:.6e} {rho:.1f} {p[0] * 1e-3:.6e} {p[1] * 1e-3:.6e} {p[2] * 1e-3:.6e}\n")


TEMPLATE = """# auto-generated by sim/dem/run_case.py -- case {name}
atom_style      granular
atom_modify     map array
boundary        f f f
newton          off
communicate     single vel yes
units           si
soft_particles  yes
processors      1 1 *
read_data       data.init
neighbor        {skin:.3e} bin
neigh_modify    delay 0

fix m1 all property/global youngsModulus peratomtype {E:.4e} {E:.4e}
fix m2 all property/global poissonsRatio peratomtype {nu} {nu}
fix m3 all property/global coefficientRestitution peratomtypepair 2 {e} {e} {e} {e}
fix m4 all property/global coefficientFriction peratomtypepair 2 {mu_pp} {mu_pw} {mu_pw} {mu_pw}
fix m5 all property/global coefficientRollingFriction peratomtypepair 2 {mu_r} {mu_r} {mu_r} {mu_r}
{ced_line}
pair_style gran model hertz tangential history rolling_friction epsd2 {cohesion}
pair_coeff * *
timestep {dt:.4e}

fix gravi all gravity 9.81 vector {gx:.6f} {gy:.6f} {gz:.6f}
fix auger  all mesh/surface file auger.stl type 2 scale 0.001 curvature_tolerant yes
fix plug   all mesh/surface file plug.stl type 2 scale 0.001
fix outlet all mesh/surface/planar file outlet.stl type 2 scale 0.001
fix walls  all wall/gran model hertz tangential history rolling_friction epsd2 {cohesion} mesh n_meshes 2 meshes auger plug

fix pts1 all particletemplate/sphere 15485863 atom_type 1 density constant {rho} radius constant {r1:.6e}
fix pts2 all particletemplate/sphere 15485867 atom_type 1 density constant {rho} radius constant {r2:.6e}
fix pts3 all particletemplate/sphere 32452843 atom_type 1 density constant {rho} radius constant {r3:.6e}
fix pdd  all particledistribution/discrete/numberbased 49979687 3 pts1 0.3 pts2 0.4 pts3 0.3

fix integr all nve/sphere
fix mf all massflow/mesh mesh outlet vec_side 0. 0. -1. count once delete_atoms yes
compute rke all erotate/sphere
variable t equal time
variable mout equal f_mf[1]
variable nout equal f_mf[2]
variable natoms equal atoms
thermo_style custom step time atoms f_mf[1] f_mf[2] ke c_rke
thermo {thermo_every}
thermo_modify lost ignore norm no flush yes
fix logmf all print {log_every} "${{t}} ${{mout}} ${{nout}} ${{natoms}}" file outflow.txt screen no

{feed_block}
{dump_block}
# --- settle with the exit plugged
run {settle_steps}
# --- open the exit and start the motor
unfix walls
fix walls2 all wall/gran model hertz tangential history rolling_friction epsd2 {cohesion} mesh n_meshes 1 meshes auger
fix spin all move/mesh mesh auger rotate origin 0. 0. 0. axis 0. 0. 1. period {period:.6f}
print "PHASE rotate start t=${{t}}"
run {rot_steps}
{stop_block}
print "PHASE done t=${{t}}"
"""


def build_case(cfg, workdir):
    os.makedirs(workdir, exist_ok=True)
    P = AugerParams(**cfg["geometry"])
    write_ascii_stl(os.path.join(workdir, "auger.stl"), auger_triangles(P))
    write_disk_stl(os.path.join(workdir, "outlet.stl"), radius=P.exit_r + 6.0, z=-1.5)
    # plug: small disk closing the exit throat during settling
    write_disk_stl(os.path.join(workdir, "plug.stl"), radius=P.exit_r + 0.6, z=0.0)
    d = cfg["d_mean_mm"]
    z_fill = P.funnel_h + (P.z_top - P.funnel_h) * cfg["fill_frac"]
    pts, diam = initial_packing(P, d, cfg["d_spread"], min(z_fill, P.z_top - d), cfg["seed"])
    if cfg["fill_x_max_mm"] is not None:
        keep = (pts[:, 0] < cfg["fill_x_max_mm"]) | (pts[:, 2] < P.funnel_h)
        pts, diam = pts[keep], diam[keep]
    R = P.bore_r + 1.0
    box = (-R * 1e-3, R * 1e-3, -R * 1e-3, R * 1e-3, -6e-3, (P.z_top + 2.0) * 1e-3)
    write_data(os.path.join(workdir, "data.init"), pts, diam, cfg["density"], box)

    dmin = d * (1 - cfg["d_spread"]) * 1e-3
    dt = cfg["dt"] or 0.2 * rayleigh_dt(dmin, cfg["density"], cfg["youngs"], cfg["poisson"])
    a = math.radians(cfg["incline_deg"])
    # gravity: component -sin(a) along the auger axis, cos(a) sideways (-x)
    gx, gy, gz = -math.cos(a), 0.0, -math.sin(a)
    period = 60.0 / cfg["rpm"]
    steps = lambda s: max(1, int(round(s / dt)))  # noqa: E731
    log_every = steps(cfg["log_every_s"])
    feed_block = ""
    if cfg["feed"]:
        zf0 = (P.flight_top + P.flight_t + 2 * d) * 1e-3
        zf1 = (P.z_top - 1.5 * d) * 1e-3
        rfeed = (P.bore_r - 1.2 * d) * 1e-3
        fx = cfg["fill_x_max_mm"]
        feed_x = (fx if fx is not None else P.bore_r) * 1e-3
        # mass rate well above any outflow; overlap check skips full slots
        feed_block = (
            f"region feedcyl cylinder z 0. 0. {rfeed:.6e} {zf0:.6e} {zf1:.6e} units box\n"
            f"region feedlow block {-rfeed:.6e} {feed_x:.6e} {-rfeed:.6e} {rfeed:.6e} {zf0:.6e} {zf1:.6e} units box\n"
            f"region feedreg intersect 2 feedcyl feedlow\n"
            f"fix feed all insert/rate/region seed 86028157 distributiontemplate pdd nparticles INF "
            f"particlerate {int(4000 * (0.4 / d) ** 3)} insert_every {steps(0.02)} overlapcheck yes all_in yes "
            f"vel constant 0. 0. -0.05 region feedreg ntry_mc 2000\n"
        )
    dump_block = ""
    if cfg["dump_every_s"] > 0:
        dump_block = (
            f"dump dmp all custom {steps(cfg['dump_every_s'])} dump/p.*.txt id type radius x y z vx vy vz\n"
            f"dump_modify dmp sort id\n"
        )
        os.makedirs(os.path.join(workdir, "dump"), exist_ok=True)
    stop_block = ""
    if cfg["stop_s"] > 0:
        stop_block = (
            "unfix spin\n"
            "print \"PHASE stop t=${t}\"\n"
            f"run {steps(cfg['stop_s'])}\n"
        )
    ced_line = ""
    cohesion = ""
    if cfg["ced"] > 0:
        ced_line = f"fix m6 all property/global cohesionEnergyDensity peratomtypepair 2 {cfg['ced']} {cfg['ced']} {cfg['ced']} {cfg['ced']}"
        cohesion = "cohesion sjkr"
    txt = TEMPLATE.format(
        name=cfg["name"], skin=0.5 * d * 1e-3, E=cfg["youngs"], nu=cfg["poisson"], e=cfg["restitution"],
        mu_pp=cfg["mu_pp"], mu_pw=cfg["mu_pw"], mu_r=cfg["mu_roll"], ced_line=ced_line, cohesion=cohesion,
        dt=dt, gx=gx, gy=gy, gz=gz, rho=cfg["density"],
        r1=d * (1 - cfg["d_spread"]) * 0.5e-3, r2=d * 0.5e-3, r3=d * (1 + cfg["d_spread"]) * 0.5e-3,
        thermo_every=steps(0.05), log_every=log_every, feed_block=feed_block, dump_block=dump_block,
        settle_steps=steps(cfg["settle_s"]), period=period, rot_steps=steps(cfg["revs"] * period),
        stop_block=stop_block,
    )
    with open(os.path.join(workdir, "in.auger"), "w") as f:
        f.write(txt)
    meta = {"cfg": cfg, "geometry": asdict(P), "dt": dt, "n_init": int(len(pts)),
            "settle_s": cfg["settle_s"], "period_s": period}
    with open(os.path.join(workdir, "case.json"), "w") as f:
        json.dump(meta, f, indent=1)
    return meta


def run(workdir, nproc):
    t0 = time.time()
    cmd = ["mpirun", "--oversubscribe", "-np", str(nproc), "liggghts", "-in", "in.auger", "-log", "log.liggghts",
           "-echo", "none", "-screen", "screen.txt"]
    if nproc == 1:
        cmd = cmd[4:]
    p = subprocess.run(cmd, cwd=workdir, capture_output=True, text=True)
    wall = time.time() - t0
    return p.returncode, wall, p.stdout[-2000:] + p.stderr[-2000:]


def parse_outflow(workdir):
    rows = []
    with open(os.path.join(workdir, "outflow.txt")) as f:
        for line in f:
            if line.startswith(("t_s", "#")) or not line.strip():
                continue
            rows.append([float(x) for x in line.split()])
    return np.array(rows)


def summarize(workdir, meta):
    A = parse_outflow(workdir)
    t, m = A[:, 0], A[:, 1] * 1e6  # mg
    t_rot0 = meta["settle_s"]
    T = meta["period_s"]
    revs = meta["cfg"]["revs"]
    per_rev = []
    for k in range(int(math.floor(revs + 1e-9))):
        a, b = t_rot0 + k * T, t_rot0 + (k + 1) * T
        per_rev.append(float(np.interp(b, t, m) - np.interp(a, t, m)))
    out = {"per_rev_mg": per_rev, "m_settle_mg": float(np.interp(t_rot0, t, m)),
           "m_total_mg": float(m[-1]), "n_atoms_final": int(A[-1, 3])}
    if meta["cfg"]["stop_s"] > 0:
        t_stop = t_rot0 + revs * T
        out["afterflow_mg"] = float(m[-1] - np.interp(t_stop, t, m))
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("config", help="JSON file or inline JSON overriding DEFAULTS")
    ap.add_argument("--workdir", required=True)
    ap.add_argument("--dry", action="store_true")
    a = ap.parse_args()
    user = json.load(open(a.config)) if os.path.exists(a.config) else json.loads(a.config)
    cfg = {**DEFAULTS, **user}
    meta = build_case(cfg, a.workdir)
    print(json.dumps({k: meta[k] for k in ("dt", "n_init", "period_s")}))
    if a.dry:
        sys.exit(0)
    rc, wall, tail = run(a.workdir, cfg["np"])
    meta["wall_s"] = wall
    meta["rc"] = rc
    if rc != 0:
        print(tail)
        sys.exit(rc)
    meta["summary"] = summarize(a.workdir, meta)
    with open(os.path.join(a.workdir, "case.json"), "w") as f:
        json.dump(meta, f, indent=1)
    print(json.dumps({"wall_s": wall, **meta["summary"]}))
