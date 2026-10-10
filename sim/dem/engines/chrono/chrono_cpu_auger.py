"""CPU (no-GPU) Chrono version of the rig-auger DEM twin, for comparison with LIGGGHTS.

PyChrono 10.0.0 from conda (both the ``conda-forge`` and the CUDA ``projectchrono``
builds) ships neither ``pychrono.gpu`` nor ``pychrono.multicore``. This script
therefore runs the *core* ``ChSystemSMC`` (smooth-contact Hertz DEM) with Chrono's
OpenMP ``MULTICORE`` collision system (``--collision bullet`` for Bullet). Use the
``projectchrono`` build: the ``conda-forge`` build has no Thrust, hence no multicore
collision system. Core ``ChSystemSMC`` ignores ``SetRollingFriction`` (see README). If a
build with ``pychrono.multicore`` is ever available, ``--system multicore`` uses
``ChSystemMulticoreSMC`` instead.

Set-up mirrors ``run_case.py``:

* the auger surface from ``geometry.auger_triangles`` (mm -> m) is written to an OBJ
  and loaded as one triangle-mesh body, spun about +z by a ``ChLinkMotorRotationAngle``;
* grains come from ``run_case.initial_packing`` (same lattice, PSD, seed and
  ``fill_x_max_mm`` cut as LIGGGHTS); ``--n-max`` keeps only the N lowest grains;
* gravity is tilted (``incline_deg``), the exit is plugged by a fixed box for
  ``--t-settle`` seconds, then the plug is parked out of the way and the motor starts;
* a grain whose centre drops below z = -0.3 mm is counted (same plane as the
  LIGGGHTS counting disk) and parked, fixed, in a slot well below the exit;
* there is no feed insertion above the flight (runs are much shorter than a rev).

Usage (from sim/dem)::

    /tmp/chrono_pc/bin/python engines/chrono/chrono_cpu_auger.py \
        results/cases/rig_t27p5_r60/config.json --n-max 2000 --t-settle 0.03 --t-rot 0.05 \
        --out engines/chrono/run_small
"""

from __future__ import annotations

import argparse
import json
import math
import os
import sys
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
DEM = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, DEM)
from geometry import AugerParams, auger_triangles  # noqa: E402
from run_case import DEFAULTS, initial_packing, rayleigh_dt  # noqa: E402

import pychrono as chrono  # noqa: E402

try:
    import pychrono.multicore as mc  # not in the conda builds of 10.0.0
except ImportError:
    mc = None

Z_COUNT_M = -0.3e-3  # counting plane, as the LIGGGHTS outlet disk


def write_obj(path, tris_mm, two_sided):
    """Auger triangles (mm) -> OBJ in metres with shared vertices. Returns (n_vert, n_face)."""
    T = np.asarray(tris_mm, float)
    nrm = np.cross(T[:, 1] - T[:, 0], T[:, 2] - T[:, 0])
    T = T[np.linalg.norm(nrm, axis=1) > 1e-14] * 1e-3  # drop degenerate facets, as write_ascii_stl
    V, inv = np.unique(np.round(T.reshape(-1, 3), 9), axis=0, return_inverse=True)
    F = inv.reshape(-1, 3)
    F = F[(F[:, 0] != F[:, 1]) & (F[:, 1] != F[:, 2]) & (F[:, 0] != F[:, 2])]
    if two_sided:  # duplicate every facet with reversed winding (multicore triangle contact is one-sided)
        F = np.vstack([F, F[:, ::-1]])
    with open(path, "w") as f:
        f.write("# rig auger surface from sim/dem/geometry.py, metres\n")
        np.savetxt(f, V, fmt="v %.9f %.9f %.9f")
        np.savetxt(f, F + 1, fmt="f %d %d %d")
    return len(V), len(F)


def make_system(kind, collision, threads):
    if kind == "multicore":
        if mc is None:
            raise SystemExit("pychrono.multicore is not available in this PyChrono build")
        sys_ = mc.ChSystemMulticoreSMC()
        sys_.SetCollisionSystemType(chrono.ChCollisionSystem.Type_MULTICORE)
        s = sys_.GetSettings()
        s.solver.contact_force_model = chrono.ChSystemSMC.Hertz
        s.solver.tangential_displ_mode = chrono.ChSystemSMC.MultiStep
        s.solver.use_material_properties = True
        s.solver.max_iteration_bilateral = 50
        sys_.SetNumThreads(threads)
        return sys_
    sys_ = chrono.ChSystemSMC()
    sys_.SetCollisionSystemType(chrono.ChCollisionSystem.Type_MULTICORE if collision == "multicore"
                                else chrono.ChCollisionSystem.Type_BULLET)
    sys_.SetContactForceModel(chrono.ChSystemSMC.Hertz)
    sys_.SetTangentialDisplacementModel(chrono.ChSystemSMC.MultiStep)
    sys_.UseMaterialProperties(True)
    sys_.SetNumThreads(threads, threads, 1)
    return sys_


def tune_multicore_grid(sys_, bin_size_m=None, density=None):
    """Set the multicore broadphase grid, which PyChrono does not wrap (default: a fixed 10 x 10 x 10 grid).

    ``GetCollisionSystem()`` hands back a SWIG proxy around ``std::shared_ptr<ChCollisionSystem>*``; the first
    word of the shared_ptr is the object pointer, and ChCollisionSystemMulticore (single inheritance) exports
    ``SetBroadphaseGridSize(const ChVector3d&)`` / ``SetBroadphaseGridDensity(double)`` from libChrono_core.so.
    """
    import ctypes
    import glob
    cs = sys_.GetCollisionSystem()
    if cs.GetType() != chrono.ChCollisionSystem.Type_MULTICORE:
        return "not a multicore collision system"
    libs = glob.glob(os.path.join(os.path.dirname(chrono.__file__), "..", "..", "..", "libChrono_core.so"))
    lib = ctypes.CDLL(libs[0] if libs else "libChrono_core.so")
    obj = ctypes.c_void_p.from_address(int(cs.this)).value  # shared_ptr -> raw pointer
    if bin_size_m:
        f = lib["_ZN6chrono26ChCollisionSystemMulticore21SetBroadphaseGridSizeERKNS_9ChVector3IdEE"]
        f.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_double * 3)]
        f(obj, ctypes.byref((ctypes.c_double * 3)(*(3 * [bin_size_m]))))
        return f"fixed bin size {bin_size_m * 1e3:.2f} mm"
    if density:
        f = lib["_ZN6chrono26ChCollisionSystemMulticore24SetBroadphaseGridDensityEd"]
        f.argtypes = [ctypes.c_void_p, ctypes.c_double]
        f(obj, density)
        return f"grid density {density} shapes/bin"
    return "default fixed 10 x 10 x 10 bins"


def leak_census(P, pos_mm, rad_mm):
    """Grains whose centres sit where no grain can be (through a wall). Returns counts per wall."""
    x, y, z = pos_mm.T
    r = np.hypot(x, y)
    cone_r = P.exit_r + (P.funnel_top_r - P.exit_r) * np.clip(z, 0, None) / P.funnel_h
    tip_r = P.tip_r + (P.shaft_r - P.tip_r) * np.clip(z, 0, None) / P.funnel_h if P.tip_r is not None else 0 * z
    tol = 0.5 * rad_mm
    return {
        "outside_bore": int(np.sum((z >= P.funnel_h) & (r > P.bore_r + tol))),
        "outside_cone": int(np.sum((z > 0) & (z < P.funnel_h) & (r > cone_r + tol))),
        "inside_core": int(np.sum((z >= P.funnel_h) & (r < P.shaft_r - tol))) if P.shaft_r > 0 else 0,
        "inside_tip": int(np.sum((z > P.tip_z0) & (z < P.funnel_h) & (r < tip_r - tol))) if P.tip_r is not None else 0,
        "above_top": int(np.sum(z > P.z_top + 2.0)),
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("config", help="LIGGGHTS case config.json (same keys as run_case.DEFAULTS)")
    ap.add_argument("--out", required=True, help="output prefix (writes <out>.json and <out>_outflow.csv)")
    ap.add_argument("--n-max", type=int, default=0, help="keep only the N lowest grains (0 = all)")
    ap.add_argument("--t-settle", type=float, default=0.03, help="s with the exit plugged and the auger still")
    ap.add_argument("--t-rot", type=float, default=0.1, help="s of rotation after the plug is removed")
    ap.add_argument("--dt", type=float, default=None, help="time step (default: LIGGGHTS rule, 0.2 Rayleigh)")
    ap.add_argument("--threads", type=int, default=2)
    ap.add_argument("--system", choices=["smc", "multicore"], default="smc")
    ap.add_argument("--collision", choices=["multicore", "bullet"], default="multicore")
    ap.add_argument("--one-sided", action="store_true", help="do not duplicate facets with reversed winding")
    ap.add_argument("--mesh-static", action="store_true",
                    help="flag the mesh shape static (Bullet then uses a BVH mesh instead of GImpact)")
    ap.add_argument("--n-theta", type=int, default=None, help="override the mesh's circumferential resolution")
    ap.add_argument("--grid-size-mm", type=float, default=0.0, help="multicore broadphase bin size (0 = default grid)")
    ap.add_argument("--grid-density", type=float, default=0.0, help="multicore broadphase shapes per bin")
    ap.add_argument("--check-every", type=float, default=1e-3, help="s between outflow checks")
    ap.add_argument("--wall-limit", type=float, default=840.0, help="stop stepping after this many wall s")
    ap.add_argument("--workdir", default="/tmp/chrono_auger", help="where the (large) OBJ mesh goes")
    a = ap.parse_args()

    cfg = {**DEFAULTS, **json.load(open(a.config))}
    P = AugerParams(**cfg["geometry"])
    d = cfg["d_mean_mm"]
    P_mesh = AugerParams(**{**cfg["geometry"], **({"n_theta": a.n_theta} if a.n_theta else {})})
    t_start = time.time()

    # ---- grains: identical packing to run_case.build_case
    z_fill = P.funnel_h + (P.z_top - P.funnel_h) * cfg["fill_frac"]
    pts, diam = initial_packing(P, d, cfg["d_spread"], min(z_fill, P.z_top - d), cfg["seed"])
    if cfg["fill_x_max_mm"] is not None:
        keep = (pts[:, 0] < cfg["fill_x_max_mm"]) | (pts[:, 2] < P.funnel_h)
        pts, diam = pts[keep], diam[keep]
    n_full = len(pts)
    if a.n_max and a.n_max < len(pts):
        idx = np.argsort(pts[:, 2], kind="stable")[: a.n_max]
        pts, diam = pts[idx], diam[idx]

    dmin = d * (1 - cfg["d_spread"]) * 1e-3
    dt = a.dt or 0.2 * rayleigh_dt(dmin, cfg["density"], cfg["youngs"], cfg["poisson"])
    inc = math.radians(cfg["incline_deg"])
    g = chrono.ChVector3d(-9.81 * math.cos(inc), 0.0, -9.81 * math.sin(inc))
    omega = 2 * math.pi * cfg["rpm"] / 60.0

    # contact envelope/margin are static defaults (0.03 m / 0.01 m out of the box: far too big here)
    chrono.ChCollisionModel.SetDefaultSuggestedEnvelope(0.05 * d * 1e-3)
    chrono.ChCollisionModel.SetDefaultSuggestedMargin(0.02 * d * 1e-3)

    sysm = make_system(a.system, a.collision, a.threads)
    sysm.SetGravitationalAcceleration(g)
    grid = tune_multicore_grid(sysm, a.grid_size_mm * 1e-3, a.grid_density) if a.system == "smc" else "settings"

    def material(mu):
        m = chrono.ChContactMaterialSMC()
        m.SetYoungModulus(cfg["youngs"])
        m.SetPoissonRatio(cfg["poisson"])
        m.SetRestitution(cfg["restitution"])
        m.SetFriction(mu)
        m.SetRollingFriction(cfg["mu_roll"])  # no effect in core ChSystemSMC (checked with a rolling sphere)
        return m

    mat_p = material(cfg["mu_pp"])
    mat_w = material(cfg["mu_pw"])  # composite friction is the min, so p-w contacts get mu_pw

    ground = chrono.ChBody()
    ground.SetFixed(True)
    sysm.AddBody(ground)

    # ---- auger: triangle mesh body driven by an angle motor about +z
    os.makedirs(a.workdir, exist_ok=True)
    obj = os.path.join(a.workdir, "auger.obj")
    n_v, n_f = write_obj(obj, auger_triangles(P_mesh), two_sided=not a.one_sided)
    trimesh = chrono.ChTriangleMeshConnected.CreateFromWavefrontFile(obj, False, False)
    auger = chrono.ChBody()
    auger.SetMass(5.0)
    auger.SetInertiaXX(chrono.ChVector3d(0.05, 0.05, 0.05))
    auger.SetPos(chrono.ChVector3d(0, 0, 0))
    auger.AddCollisionShape(chrono.ChCollisionShapeTriangleMesh(mat_w, trimesh, a.mesh_static, False, 0.0))
    auger.EnableCollision(True)
    sysm.AddBody(auger)
    motor = chrono.ChLinkMotorRotationAngle()
    motor.Initialize(auger, ground, chrono.ChFramed(chrono.ChVector3d(0, 0, 0), chrono.QUNIT))
    motor.SetAngleFunction(chrono.ChFunctionConst(0.0))
    sysm.AddLink(motor)

    # ---- plug closing the exit while settling (top face at z = 0)
    plug_h = 0.25e-3
    plug_half = (P.exit_r + 0.6) * 1e-3
    plug = chrono.ChBody()
    plug.SetFixed(True)
    plug.SetPos(chrono.ChVector3d(0, 0, -plug_h))
    plug.AddCollisionShape(chrono.ChCollisionShapeBox(mat_w, 2 * plug_half, 2 * plug_half, 2 * plug_h))
    plug.EnableCollision(True)
    sysm.AddBody(plug)

    # ---- grains
    rho = cfg["density"]
    bodies = []
    for p, dm in zip(pts, diam):
        r = 0.5 * dm * 1e-3
        m = rho * 4.0 / 3.0 * math.pi * r ** 3
        b = chrono.ChBody()
        b.SetMass(m)
        b.SetInertiaXX(chrono.ChVector3d(*(3 * [0.4 * m * r * r])))
        b.SetPos(chrono.ChVector3d(*(p * 1e-3)))
        b.AddCollisionShape(chrono.ChCollisionShapeSphere(mat_p, r))
        b.EnableCollision(True)
        sysm.AddBody(b)
        bodies.append(b)
    masses = rho * math.pi / 6.0 * (diam * 1e-3) ** 3
    n = len(bodies)
    t_build = time.time() - t_start
    print(f"built {n} grains (full section {n_full}), mesh {n_f} facets, dt {dt:.3e} s, build {t_build:.1f} s, "
          f"broadphase: {grid}",
          flush=True)

    # parking slots for counted grains: a sparse grid 3..9 mm below the exit, 1.2 mm apart
    park = [(x, y, z) for z in np.arange(-3.0, -9.1, -1.2) for x in np.arange(-10.0, 10.01, 1.2)
            for y in np.arange(-10.0, 10.01, 1.2)]
    n_park = 0

    def park_body(b):
        nonlocal n_park
        x, y, z = park[n_park % len(park)]
        n_park += 1
        b.SetFixed(True)
        b.SetPos(chrono.ChVector3d(x * 1e-3, y * 1e-3, z * 1e-3))
        b.SetLinVel(chrono.ChVector3d(0, 0, 0))
        b.SetAngVelParent(chrono.ChVector3d(0, 0, 0))

    TIMERS = {"step": "GetTimerStep", "collision": "GetTimerCollision", "coll_broad": "GetTimerCollisionBroad",
              "coll_narrow": "GetTimerCollisionNarrow", "update": "GetTimerUpdate", "setup": "GetTimerSetup",
              "ls_setup": "GetTimerLSsetup", "ls_solve": "GetTimerLSsolve", "jacobian": "GetTimerJacobian",
              "advance": "GetTimerAdvance"}
    timers = dict.fromkeys(TIMERS, 0.0)
    active = np.ones(n, bool)
    ever_top = np.zeros(n, bool)  # grains that ever rose above the open top rim of the bore
    xs, ys, zs = (np.zeros(n) for _ in range(3))
    rows = []
    m_out = 0.0
    n_out = 0
    n_settle = max(1, int(round(a.t_settle / dt)))
    n_rot = max(1, int(round(a.t_rot / dt)))
    every = max(1, int(round(a.check_every / dt)))
    step = 0
    wall_step = 0.0
    cpu_step = 0.0
    psteps = 0.0
    stopped_early = False
    vmax_seen = 0.0
    t0_wall = time.time()
    phase = "settle"
    for step in range(1, n_settle + n_rot + 1):
        if step == n_settle + 1:
            phase = "rotate"
            plug.SetPos(chrono.ChVector3d(0, 0, -12e-3))  # fixed bodies can simply be moved out of the way
            t_now = sysm.GetChTime()
            motor.SetAngleFunction(chrono.ChFunctionRamp(-omega * t_now, omega))
            print(f"t={t_now:.4f} s: plug removed, motor on ({cfg['rpm']} rpm)", flush=True)
        ts, tc = time.time(), time.process_time()
        sysm.DoStepDynamics(dt)
        wall_step += time.time() - ts
        cpu_step += time.process_time() - tc  # CPU time summed over all threads (= core-seconds)
        for k, fn in TIMERS.items():
            timers[k] += getattr(sysm, fn)()
        psteps += active.sum()
        if step % every == 0 or step == n_settle + n_rot:
            vmax = 0.0
            for i in np.flatnonzero(active):
                p = bodies[i].GetPos()
                xs[i], ys[i], zs[i] = p.x, p.y, p.z
                v = bodies[i].GetPosDt()
                vmax = max(vmax, v.x * v.x + v.y * v.y + v.z * v.z)
            vmax = math.sqrt(vmax)
            vmax_seen = max(vmax_seen, vmax)
            ever_top |= active & (zs > P.z_top * 1e-3)
            rr = np.hypot(xs, ys) * 1e3
            outside = active & (zs * 1e3 >= P.funnel_h) & (rr > P.bore_r + 0.25 * diam)
            out = np.flatnonzero(active & (zs < Z_COUNT_M))
            for i in out:
                active[i] = False
                m_out += masses[i]
                n_out += 1
                park_body(bodies[i])
            t = sysm.GetChTime()
            el = time.time() - t0_wall
            rows.append((t, phase, n_out, m_out * 1e6, int(active.sum()), sysm.GetNumContacts(), vmax,
                         motor.GetMotorAngle(), el, int(outside.sum()), int((outside & ever_top).sum()),
                         int(ever_top.sum())))
            if len(rows) % 5 == 0 or step == n_settle + n_rot:
                print(f"t={t:.4f} {phase} out={n_out} ({m_out * 1e6:.2f} mg) contacts={sysm.GetNumContacts()} "
                      f"vmax={vmax:.3f} m/s angle={motor.GetMotorAngle():.3f} rad wall={el:.0f} s "
                      f"rate={psteps / max(wall_step, 1e-9) / 1e6:.3f} M p-steps/s wall, "
                      f"{psteps / max(cpu_step, 1e-9) / 1e6:.3f} per core-s", flush=True)
            if el > a.wall_limit:
                stopped_early = True
                print(f"wall limit reached at t={t:.4f} s", flush=True)
                break

    wall = time.time() - t0_wall
    pos = np.array([[bodies[i].GetPos().x, bodies[i].GetPos().y, bodies[i].GetPos().z] for i in np.flatnonzero(active)])
    rad = 0.5 * diam[active]
    leaks = leak_census(P, pos * 1e3, rad)
    t_rot0 = n_settle * dt
    rot_rows = [r for r in rows if r[1] == "rotate"]
    m_rot = (rows[-1][3] - ([r for r in rows if r[1] == "settle"] or [(0, 0, 0, 0.0)])[-1][3]) if rot_rows else 0.0
    t_rot_done = rows[-1][0] - t_rot0 if rot_rows else 0.0
    res = {
        "engine": f"PyChrono {getattr(chrono, '__version__', '10.0.0')} "
                  f"{'ChSystemMulticoreSMC' if a.system == 'multicore' else 'ChSystemSMC'} + "
                  f"{a.collision} collision, {a.threads} threads",
        "config": os.path.relpath(os.path.abspath(a.config), DEM),
        "n_grains": n, "n_full_section": n_full, "mesh_facets": n_f, "two_sided_mesh": not a.one_sided,
        "mesh_static_flag": a.mesh_static, "mesh_n_theta": P_mesh.n_theta, "broadphase_grid": grid,
        "dt_s": dt, "steps": step, "t_settle_s": t_rot0, "t_rot_done_s": t_rot_done,
        "build_s": t_build, "wall_s": wall, "wall_step_s": wall_step,
        "M_particle_steps_per_s": psteps / wall_step / 1e6,
        "cpu_step_s": cpu_step, "cpu_cores_used_avg": cpu_step / wall_step,
        "M_particle_steps_per_core_s": psteps / cpu_step / 1e6,
        "M_particle_steps_per_s_incl_python": psteps / wall / 1e6,
        "n_out": n_out, "m_out_mg": m_out * 1e6, "m_out_during_rotation_mg": m_rot,
        "mg_per_s_during_rotation": m_rot / t_rot_done if t_rot_done > 0 else None,
        "vmax_seen_m_s": vmax_seen, "leaks_at_end": leaks, "stopped_early": stopped_early,
        "final_contacts": sysm.GetNumContacts(), "motor_angle_rad": motor.GetMotorAngle(),
        "chrono_timers_s": {k: round(v, 3) for k, v in timers.items()},
        "grains_ever_above_top_rim": int(ever_top.sum()),
        "outside_bore_grains_mm_deg": [  # r, theta, z of grains outside the bore wall at the end, and ever-above-rim flag
            [round(float(np.hypot(xs[i], ys[i]) * 1e3), 3), round(float(np.degrees(np.arctan2(ys[i], xs[i]))), 1),
             round(float(zs[i] * 1e3), 3), bool(ever_top[i])]
            for i in np.flatnonzero(active & (zs * 1e3 >= P.funnel_h)
                                    & (np.hypot(xs, ys) * 1e3 > P.bore_r + 0.25 * diam))][:300],
    }
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    with open(a.out + ".json", "w") as f:
        json.dump(res, f, indent=1)
    with open(a.out + "_outflow.csv", "w") as f:
        f.write("t_s,phase,n_out,m_out_mg,n_active,n_contacts,vmax_m_s,motor_angle_rad,wall_s,"
                "n_outside_bore,n_outside_bore_via_top,n_ever_above_top\n")
        for r in rows:
            f.write(f"{r[0]:.5f},{r[1]},{r[2]},{r[3]:.4f},{r[4]},{r[5]},{r[6]:.4f},{r[7]:.4f},{r[8]:.1f},"
                    f"{r[9]},{r[10]},{r[11]}\n")
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
