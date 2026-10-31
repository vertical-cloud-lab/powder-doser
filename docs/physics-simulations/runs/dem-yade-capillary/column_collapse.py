# Yade column collapse of coarse-grained "salt" spheres with Willett liquid bridges.
# Usage: yadedaily -n -x column_collapse.py <case_name> <W_liquid_vol_fraction> <outdir>
#   W = 0 -> dry (no capillary force); W > 0 -> pendular liquid bridges, V_bridge = W*Vp_mean/3
import sys, os, json, time, math
import numpy as np
from yade import *
from yade import utils, geom

case = sys.argv[1] if len(sys.argv) > 1 else 'dry'
W = float(sys.argv[2]) if len(sys.argv) > 2 else 0.0
outdir = sys.argv[3] if len(sys.argv) > 3 else '/tmp/sims-scratch/dem-yade-capillary'
os.makedirs(outdir, exist_ok=True)

# ---------------- parameters ----------------
CG = 4.0                                   # coarse-graining factor on diameter
dsalt = np.array([0.361, 0.425, 0.489]) * 1e-3   # m, reference salt PSD
nfrac = np.array([0.3, 0.4, 0.3])          # number fractions
d = dsalt * CG                             # 1.444/1.700/1.956 mm
rho = 2165.0                               # kg/m3
mu_pp, mu_pw = 0.5, 0.4                    # sliding friction
en = et = 0.5                              # restitution (normal, tangential)
tc = 5.0e-4                                # s, contact duration (sets kn per contact, Pournin 2001)
gamma = 0.072                              # N/m, water surface tension
theta = 0.0                                # contact angle (rad), fully wetting
Vp_mean = float(np.sum(nfrac * np.pi / 6 * d**3))
Vb = W * Vp_mean / 3.0                     # bridge volume, assuming 3 bridges per particle (Z ~ 6)
N = 1200
R0 = 5 * 1.7e-3                            # cylinder radius = 5 mean diameters (8.5 mm)
t_settle = 0.20                            # s, settle inside cylinder
t_collapse = 0.40                          # s, max time after cylinder removal
O.dt = tc / 20.0
snap_dt = 0.02

capillar = W > 0
matP = O.materials.append(ViscElCapMat(density=rho, tc=tc, en=en, et=et, frictionAngle=math.atan(mu_pp),
                                       Capillar=capillar, Vb=Vb, gamma=gamma, theta=theta,
                                       CapillarType='Willett_numeric' if capillar else '', mR=0.0, label='salt'))
matW = O.materials.append(ViscElCapMat(density=rho, tc=tc, en=en, et=et, frictionAngle=math.atan(mu_pw),
                                       Capillar=capillar, Vb=Vb, gamma=gamma, theta=theta,
                                       CapillarType='Willett_numeric' if capillar else '', mR=0.0, label='wall'))

# floor (infinite plane z=0) and cylinder side (facets) holding the column
floor = O.bodies.append(utils.wall(0.0, axis=2, sense=1, material=matW))
Hcyl = 0.08
cyl = O.bodies.append(geom.facetCylinder(center=(0, 0, Hcyl / 2), radius=R0, height=Hcyl, segmentsNumber=24,
                                         wallMask=4, material=matW))

# particles on a lattice inside the cylinder, random diameters from the trimodal number PSD
rng = np.random.default_rng(1)
sp = 2.02e-3
pts = []
z = sp / 2 + 1e-4
while len(pts) < N:
    for x in np.arange(-R0, R0 + 1e-12, sp):
        for y in np.arange(-R0, R0 + 1e-12, sp):
            if math.hypot(x, y) <= R0 - sp / 2 - 2e-4 and len(pts) < N:
                pts.append((x + rng.uniform(-5e-5, 5e-5), y + rng.uniform(-5e-5, 5e-5), z))
    z += sp
diam = rng.choice(d, size=N, p=nfrac)
ids = []
for (x, y, zz), dd in zip(pts, diam):
    ids.append(O.bodies.append(utils.sphere((x, y, zz), dd / 2, material=matP)))
ids = [int(i) for i in ids]

O.engines = [
    ForceResetter(),
    InsertionSortCollider([Bo1_Sphere_Aabb(aabbEnlargeFactor=1.3 if capillar else 1.0), Bo1_Facet_Aabb(), Bo1_Wall_Aabb()], verletDist=-0.1),
    InteractionLoop(
        [Ig2_Sphere_Sphere_ScGeom(), Ig2_Facet_Sphere_ScGeom(), Ig2_Wall_Sphere_ScGeom()],  # bridges form at contact; existing ones persist while AABBs overlap
        [Ip2_ViscElCapMat_ViscElCapMat_ViscElCapPhys()],
        [Law2_ScGeom_ViscElCapPhys_Basic(label='capLaw')],
    ),
    NewtonIntegrator(damping=0.0, gravity=(0, 0, -9.81)),
]

snaps, snap_t, ts = [], [], []
def snapshot():
    a = np.array([[O.bodies[i].state.pos[0], O.bodies[i].state.pos[1], O.bodies[i].state.pos[2], O.bodies[i].shape.radius] for i in ids], dtype=np.float32)
    snaps.append(a); snap_t.append(O.time)

def kinetic():
    return sum(0.5 * O.bodies[i].state.mass * O.bodies[i].state.vel.squaredNorm() for i in ids)

t0 = time.time()
next_snap = 0.0
removed = False
t_removed = None
ke_hist = []
while True:
    O.run(int(round(0.005 / O.dt)), True)
    ke = kinetic(); ke_hist.append((O.time, ke, capLaw.NLiqBridg))
    if O.time + 1e-9 >= next_snap:
        snapshot(); next_snap += snap_dt
    if not removed and O.time >= t_settle:
        for fid in cyl:
            O.bodies.erase(fid)
        removed = True; t_removed = O.time
        print('cylinder removed at t=%.3f s, KE=%.3e J, bridges=%d' % (O.time, ke, capLaw.NLiqBridg), flush=True)
    if removed and (O.time - t_removed > 0.1) and ke < 1e-9:
        print('at rest at t=%.3f' % O.time, flush=True); break
    if removed and O.time - t_removed >= t_collapse:
        print('t_collapse reached', flush=True); break
snapshot()
wall = time.time() - t0
# column height just before removal (from the snapshot closest to t_settle)
iset = int(np.argmin([abs(t - t_removed) for t in snap_t]))
pre = snaps[iset]
H0 = float(np.max(pre[:, 2] + pre[:, 3]))
np.savez_compressed(os.path.join(outdir, '%s_snaps.npz' % case), snaps=np.array(snaps), t=np.array(snap_t),
                    ke=np.array(ke_hist), t_removed=t_removed)
meta = dict(case=case, W=W, Vb=Vb, N=N, CG=CG, d=d.tolist(), nfrac=nfrac.tolist(), rho=rho, mu_pp=mu_pp, mu_pw=mu_pw,
            en=en, et=et, tc=tc, dt=O.dt, gamma=gamma, theta=theta, R0=R0, H0=H0, t_removed=t_removed,
            t_end=O.time, wall_s=wall, steps=O.iter, final_bridges=int(capLaw.NLiqBridg),
            Vp_mean=Vp_mean, version=yade.config.version if hasattr(yade, 'config') else 'unknown')
json.dump(meta, open(os.path.join(outdir, '%s_meta.json' % case), 'w'), indent=1)
print(json.dumps(meta), flush=True)
