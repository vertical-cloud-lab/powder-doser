"""Isaac Sim 6.1 (pip) on a GPU-less host: CPU PhysX rigid spheres in a funnel, then a PBD powder probe.

Used for sim/dem/engines/gpu_engines_on_cpu.md. Pure USD + omni.physx (the isaacsim.core.experimental
API does not load without libcuda.so.1). Run in a venv with isaacsim[all,extscache]==6.1.0.0:

    OMNI_KIT_ACCEPT_EULA=YES python isaac_cpu_probe.py --spheres 400 --steps 600 --outlet-r 0.006
    OMNI_KIT_ACCEPT_EULA=YES python isaac_cpu_probe.py --force-gpu   # MATTERIX-style: overwrite_gpu_setting(1)
"""
import argparse
import math
import time

ap = argparse.ArgumentParser()
ap.add_argument("--spheres", type=int, default=400)
ap.add_argument("--steps", type=int, default=600)
ap.add_argument("--outlet-r", type=float, default=0.006, help="funnel outlet radius [m]")
ap.add_argument("--force-gpu", action="store_true", help="request GPU dynamics as MATTERIX does for particle scenes")
args = ap.parse_args()
T0 = time.time()


def mark(msg):
    print(f"[MARK {time.time() - T0:6.1f}s] {msg}", flush=True)


from isaacsim import SimulationApp  # noqa: E402

app = SimulationApp({"headless": True, "renderer": "MinimalRendering", "extra_args": [
    "--/physics/numThreads=2", "--/plugins/carb.tasking.plugin/threadCount=2"]})
mark("SimulationApp started")

import omni.physx  # noqa: E402
import omni.usd  # noqa: E402
from omni.physx.scripts import particleUtils  # noqa: E402
from pxr import Gf, PhysxSchema, Sdf, UsdGeom, UsdPhysics  # noqa: E402

phx = omni.physx.get_physx_interface()
if args.force_gpu:
    phx.overwrite_gpu_setting(1)  # same call as MATTERIX envs/matterix_base_env_cfg.py
ctx = omni.usd.get_context()
ctx.new_stage()
stage = ctx.get_stage()
UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.z)
UsdGeom.SetStageMetersPerUnit(stage, 1.0)
scene = UsdPhysics.Scene.Define(stage, "/World/physicsScene")
scene.CreateGravityDirectionAttr(Gf.Vec3f(0, 0, -1))
scene.CreateGravityMagnitudeAttr(9.81)
px = PhysxSchema.PhysxSceneAPI.Apply(scene.GetPrim())
px.CreateEnableGPUDynamicsAttr(bool(args.force_gpu))
px.CreateBroadphaseTypeAttr("GPU" if args.force_gpu else "MBP")
px.CreateSolverTypeAttr("TGS")
px.CreateTimeStepsPerSecondAttr(600)
DT = 1.0 / 600.0

# Funnel: open frustum, top r = 40 mm at z = 60 mm, outlet r = args.outlet_r at z = 0, built from 48 static thin
# box staves (primitive shapes, no mesh cooking). Note: a triangle-mesh funnel whose normals faced outward let the
# spheres fall straight through (PhysX mesh contacts are one-sided).
NSEG, R_TOP, H, R_BOT, T = 48, 0.040, 0.060, args.outlet_r, 0.002
alpha = math.atan2(R_TOP - R_BOT, H)  # wall angle from vertical
L = math.hypot(R_TOP - R_BOT, H)
W = 2 * R_TOP * math.tan(math.pi / NSEG) * 1.05
for i in range(NSEG):
    a = 2 * math.pi * i / NSEG
    rc = 0.5 * (R_TOP + R_BOT) + 0.5 * T * math.cos(alpha)  # inner face on the cone surface
    zc = 0.5 * H - 0.5 * T * math.sin(alpha)
    st = UsdGeom.Cube.Define(stage, f"/World/funnel/stave{i}")
    st.CreateSizeAttr(1.0)
    xf = UsdGeom.XformCommonAPI(st)
    xf.SetTranslate(Gf.Vec3d(rc * math.cos(a), rc * math.sin(a), zc))
    xf.SetRotate(Gf.Vec3f(0.0, math.degrees(alpha), math.degrees(a)), UsdGeom.XformCommonAPI.RotationOrderXYZ)
    xf.SetScale(Gf.Vec3f(T, W, L))
    UsdPhysics.CollisionAPI.Apply(st.GetPrim())
tray = UsdGeom.Cube.Define(stage, "/World/tray")  # catch tray, top at z = -60 mm
tray.CreateSizeAttr(1.0)
UsdGeom.XformCommonAPI(tray).SetTranslate(Gf.Vec3d(0, 0, -0.065))
UsdGeom.XformCommonAPI(tray).SetScale(Gf.Vec3f(0.4, 0.4, 0.01))
UsdPhysics.CollisionAPI.Apply(tray.GetPrim())

# Rigid spheres, r = 2.5 mm, 2500 kg/m^3, loose grid above the funnel.
R = 0.0025
paths = []
side = int(math.ceil(args.spheres ** (1 / 3)))
for iz in range(side + 2):
    for iy in range(side):
        for ix in range(side):
            x, y = (ix - side / 2) * 2.6 * R, (iy - side / 2) * 2.6 * R
            if len(paths) >= args.spheres or x * x + y * y > (R_TOP - 3 * R) ** 2:
                continue
            p = f"/World/s{len(paths)}"
            sp = UsdGeom.Sphere.Define(stage, p)
            sp.CreateRadiusAttr(R)
            UsdGeom.XformCommonAPI(sp).SetTranslate(Gf.Vec3d(x, y, H + 0.005 + iz * 2.6 * R))
            UsdPhysics.CollisionAPI.Apply(sp.GetPrim())
            UsdPhysics.RigidBodyAPI.Apply(sp.GetPrim())
            UsdPhysics.MassAPI.Apply(sp.GetPrim()).CreateDensityAttr(2500.0)
            paths.append(p)

phx.start_simulation()
for i in range(args.steps):
    if i == 10:
        t_b = time.time()
    phx.update_simulation(elapsedStep=DT, currentTime=i * DT)
    if i % 50 == 0:  # sync poses to USD while bodies are awake (sleeping bodies are not written back at the end)
        phx.update_transformations(False, True, True, False)
rate = (args.steps - 10) / (time.time() - t_b)
phx.update_transformations(False, True, True, False)
z = sorted(UsdGeom.Xformable(stage.GetPrimAtPath(p)).ComputeLocalToWorldTransform(0).ExtractTranslation()[2]
           for p in paths)
xyz = [UsdGeom.Xformable(stage.GetPrimAtPath(p)).ComputeLocalToWorldTransform(0).ExtractTranslation() for p in paths]
inside = sum(1 for v in xyz if 0 <= v[2] <= H and math.hypot(v[0], v[1]) < R_BOT + (R_TOP - R_BOT) * v[2] / H)
mark(f"RIGID: {len(paths)} spheres, {args.steps} steps of 1/600 s, {rate:.0f} steps/s; "
     f"{sum(v < 0 for v in z)} below outlet, {inside} inside the funnel cone, "
     f"median z {z[len(z) // 2]:.4f} m, outlet r {R_BOT * 1e3:.1f} mm")
phx.reset_simulation()

# PBD powder probe (the PhysX particle API MATTERIX uses for powders: fluid=False).
ps = Sdf.Path("/World/particleSystem")
particleUtils.add_physx_particle_system(
    stage, ps, particle_system_enabled=True, simulation_owner=scene.GetPath(), contact_offset=0.0012,
    rest_offset=0.0007, particle_contact_offset=0.0012, solid_rest_offset=0.0007, fluid_rest_offset=0.0006,
    solver_position_iterations=4)
particleUtils.add_pbd_particle_material(stage, Sdf.Path("/World/powderMat"), friction=0.5, cohesion=0.01,
                                       viscosity=20.0)
ppos = [Gf.Vec3f(0.0012 * (i % 10), 0.0012 * ((i // 10) % 10), H + 0.02 + 0.0012 * (i // 100)) for i in range(1000)]
particleUtils.add_physx_particleset_points(stage, Sdf.Path("/World/powder"), ppos, [Gf.Vec3f(0, 0, 0)] * len(ppos),
                                          [0.0012] * len(ppos), ps, self_collision=True, fluid=False,
                                          particle_group=0, particle_mass=1e-6, density=0.0)
pts_attr = UsdGeom.Points.Get(stage, "/World/powder").GetPointsAttr()
z0 = sum(p[2] for p in pts_attr.Get()) / len(ppos)
phx.start_simulation()
for i in range(60):
    phx.update_simulation(elapsedStep=DT, currentTime=i * DT)
phx.update_transformations(False, True, True, False)
z1 = sum(p[2] for p in pts_attr.Get()) / len(ppos)
mark(f"PBD: 1000 powder particles, mean z {z0:.5f} -> {z1:.5f} m after 60 steps "
     f"(free fall would drop {0.5 * 9.81 * (60 * DT) ** 2:.4f} m)")
app.close()
