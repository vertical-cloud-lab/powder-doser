# Yade (yadedaily) script: lifted-cylinder heap of NaCl-like grains.
# Compares (1) spheres, (2) spheres + rolling resistance, (3) 8-sphere rigid clumps
# approximating cubic salt crystals.  Usage (one case per process):
#   CASE=sphere|sphere_rr|cube8 NPART=1000 OUT=/tmp/... yadedaily -n -x heap_yade.py
import os, json, math, time
import numpy as np
from yade import pack, geom, utils

CASE = os.environ.get('CASE', 'sphere')
N = int(os.environ.get('NPART', '1000'))
OUT = os.environ.get('OUT', '/tmp/sims-scratch/dem-nonspherical/out')
SEED = int(os.environ.get('SEED', '1'))
ETA_ROLL = float(os.environ.get('ETA_ROLL', '0.15'))
os.makedirs(OUT, exist_ok=True)
rng = np.random.default_rng(SEED)

# ---- material parameters (NaCl, from the repo's LIGGGHTS twin) ----
rho = 2165.0           # kg/m3
E = 2e5                # Pa (reduced, as in the LIGGGHTS twin)
mu_pp, mu_pw = 0.5, 0.4
dmin, dmax = 0.36e-3, 0.49e-3      # sieve range, d50 = 0.425 mm
d50 = 0.425e-3
Rc = float(os.environ.get('RC', '1.6e-3'))   # cylinder radius (m); column H/R ~ 2 so it collapses
Hcloud = 1.2 * N * (math.pi / 6 * d50 ** 3) / (0.28 * (2 * 0.95 * Rc / math.sqrt(2)) ** 2)  # loose-cloud height (m)
Hcyl = Hcloud + 2e-3
VLIFT = 0.05           # m/s cylinder lift speed
damp = 0.3             # Cundall non-viscous damping (stands in for restitution)

O.reset()
if CASE == 'sphere_rr':
    pmat = O.materials.append(CohFrictMat(young=E, poisson=0.3, density=rho,
            frictionAngle=math.atan(mu_pp), isCohesive=False, momentRotationLaw=True,
            etaRoll=ETA_ROLL, alphaKr=2.0, normalCohesion=0, shearCohesion=0, label='p'))
    wmat = O.materials.append(CohFrictMat(young=E, poisson=0.3, density=rho,
            frictionAngle=math.atan(mu_pw), isCohesive=False, momentRotationLaw=True,
            etaRoll=ETA_ROLL, alphaKr=2.0, normalCohesion=0, shearCohesion=0, label='w'))
else:
    pmat = O.materials.append(FrictMat(young=E, poisson=0.3, density=rho,
            frictionAngle=math.atan(mu_pp), label='p'))
    wmat = O.materials.append(FrictMat(young=E, poisson=0.3, density=rho,
            frictionAngle=math.atan(mu_pw), label='w'))

# floor (2 facets) and side wall of the cylinder (facets, side only)
L = 20e-3
floor = [utils.facet([(-L, -L, 0), (L, -L, 0), (L, L, 0)], material=wmat, fixed=True),
         utils.facet([(-L, -L, 0), (L, L, 0), (-L, L, 0)], material=wmat, fixed=True)]
O.bodies.append(floor)
cyl = geom.facetCylinder((0, 0, Hcyl / 2), Rc, Hcyl, segmentsNumber=32, wallMask=4,
                         material=wmat, fixed=True)
cylIds = O.bodies.append(cyl)
# make sure the cylinder axis is vertical (doc: reference axis may be +x in this build)
zs = [O.bodies[i].state.pos[2] for i in cylIds]
if max(zs) - min(zs) < 0.5 * Hcyl:
    for i in cylIds:
        O.bodies.erase(i)
    cyl = geom.facetCylinder((0, 0, Hcyl / 2), Rc, Hcyl, orientation=Quaternion((0, 1, 0), -math.pi / 2),
                             segmentsNumber=32, wallMask=4, material=wmat, fixed=True)
    cylIds = O.bodies.append(cyl)

# cloud of particle centres inside the square inscribed in the cylinder
h = Rc / math.sqrt(2) * 0.95
if CASE == 'cube8':
    # 8 spheres of radius 0.3a at (+-0.2a)^3 -> rounded cube of side a.
    # choose a so that the clump (union) volume equals the volume of a sphere of diameter d.
    pts = rng.uniform(-0.5, 0.5, size=(400000, 3))
    cen = np.array([[sx, sy, sz] for sx in (-.2, .2) for sy in (-.2, .2) for sz in (-.2, .2)])
    inside = np.zeros(len(pts), bool)
    for c in cen:
        inside |= ((pts - c) ** 2).sum(1) <= 0.3 ** 2
    fvol = inside.mean()               # union volume / a^3
    rcirc_rel = math.sqrt(3) * 0.2 + 0.3   # circumscribed radius / a
else:
    fvol, rcirc_rel = None, None

sp = pack.SpherePack()
rmean = 0.5 * d50
if CASE == 'cube8':
    a50 = (math.pi / 6 * d50 ** 3 / fvol) ** (1 / 3)
    rmean = rcirc_rel * a50
nplaced = sp.makeCloud((-h, -h, 0.3e-3), (h, h, Hcloud), rMean=rmean, rRelFuzz=(dmax - dmin) / (dmax + dmin),
                       num=N, seed=SEED)
print('placed', nplaced, 'of', N)
partIds = []
vol_solid = 0.0
if CASE == 'cube8':
    for (c, r) in sp:
        a = r / rcirc_rel
        q = Quaternion(Vector3(*rng.normal(size=3)).normalized(), rng.uniform(0, 2 * math.pi))
        mem = []
        for cc in cen:
            off = q * Vector3(*(cc * a))
            mem.append(utils.sphere(c + off, 0.3 * a, material=pmat))
        cid, mids = O.bodies.appendClumped(mem, discretization=12)
        partIds.append(cid)
        vol_solid += fvol * a ** 3
else:
    for (c, r) in sp:
        partIds.append(O.bodies.append(utils.sphere(c, r, material=pmat)))
        vol_solid += 4 / 3 * math.pi * r ** 3

if CASE == 'sphere_rr':
    igs = [Ig2_Sphere_Sphere_ScGeom6D(), Ig2_Facet_Sphere_ScGeom6D()]
    ips = [Ip2_CohFrictMat_CohFrictMat_CohFrictPhys()]
    laws = [Law2_ScGeom6D_CohFrictPhys_CohesionMoment(always_use_moment_law=True, useIncrementalForm=True)]
else:
    igs = [Ig2_Sphere_Sphere_ScGeom(), Ig2_Facet_Sphere_ScGeom()]
    ips = [Ip2_FrictMat_FrictMat_FrictPhys()]
    laws = [Law2_ScGeom_FrictPhys_CundallStrack()]

O.engines = [
    ForceResetter(),
    InsertionSortCollider([Bo1_Sphere_Aabb(), Bo1_Facet_Aabb()]),
    InteractionLoop(igs, ips, laws),
    GlobalStiffnessTimeStepper(active=True, timeStepUpdateInterval=50, timestepSafetyCoefficient=0.5),
    NewtonIntegrator(damping=damp, gravity=(0, 0, -9.81)),
]
O.dt = 1e-6

frames = []  # (t, x, z, r) snapshots of a central slice for the animation
def snap():
    xs, zs_, rs = [], [], []
    for b in O.bodies:
        if isinstance(b.shape, Sphere) and abs(b.state.pos[1]) < 0.6e-3:
            xs.append(b.state.pos[0]); zs_.append(b.state.pos[2]); rs.append(b.shape.radius)
    frames.append((O.time, np.array(xs), np.array(zs_), np.array(rs)))

def run_until(tend, every=0.01):
    nxt = O.time
    while O.time < tend:
        if O.time >= nxt:
            snap(); nxt += every
        O.run(200, True)

t0 = time.time()
# 1) pour/settle inside the cylinder
run_until(0.12)
while utils.kineticEnergy() > 1e-10 and O.time < 0.18:
    run_until(O.time + 0.01)
t_settled = O.time
# packing fraction of the settled column
def particle_list():
    out = []
    for i in partIds:
        b = O.bodies[i]
        if b is None:
            continue
        if CASE == 'cube8':
            v = b.state.mass / rho
            out.append((b.state.pos, v))
        else:
            out.append((b.state.pos, 4 / 3 * math.pi * b.shape.radius ** 3))
    return out
pl = particle_list()
ztop = np.percentile([p[2] for p, v in pl], 95)
zlo, zhi, rr = d50, ztop - d50, Rc - d50
vin = sum(v for p, v in pl if (p[0] ** 2 + p[1] ** 2) < rr ** 2 and zlo < p[2] < zhi)
phi_col = vin / (math.pi * rr ** 2 * max(zhi - zlo, 1e-9))
print('settled at t=%.3f s, bed top ~%.2f mm, packing fraction %.3f' % (t_settled, ztop * 1e3, phi_col))

# 2) lift the cylinder
for i in cylIds:
    O.bodies[i].state.vel = Vector3(0, 0, VLIFT)
    O.bodies[i].state.blockedDOFs = 'xyzXYZ'
t_lift0 = O.time
run_until(t_lift0 + (ztop + 2 * d50) / VLIFT + 0.002)
for i in cylIds:
    O.bodies.erase(i)
# 3) let the heap come to rest
run_until(O.time + 0.10)
while utils.kineticEnergy() > 1e-10 and O.time < t_lift0 + 0.35:
    run_until(O.time + 0.01)
snap()
wall = time.time() - t0

# ---- angle of repose from the heap surface profile ----
sph = [(b.state.pos, b.shape.radius) for b in O.bodies if isinstance(b.shape, Sphere)]
P = np.array([[p[0], p[1], p[2]] for p, r in sph]); R = np.array([r for p, r in sph])
cxy = P[:, :2].mean(0)
rad = np.hypot(P[:, 0] - cxy[0], P[:, 1] - cxy[1])
top = P[:, 2] + R
bw = 0.4e-3
edges = np.arange(0, rad.max() + bw, bw)
rb, hb = [], []
for k in range(len(edges) - 1):
    m = (rad >= edges[k]) & (rad < edges[k + 1])
    if m.sum() >= 3:
        rb.append(0.5 * (edges[k] + edges[k + 1])); hb.append(np.max(top[m]))
rb, hb = np.array(rb), np.array(hb)
hmax = hb.max()
# fit on the flank between 20 % and 80 % of the heap height
sel = (hb > 0.2 * hmax) & (hb < 0.8 * hmax) & (rb > rb[np.argmax(hb)])
if sel.sum() >= 3:
    slope, icpt = np.polyfit(rb[sel], hb[sel], 1)
    aor = math.degrees(math.atan(-slope))
else:
    slope, icpt, aor = float('nan'), float('nan'), float('nan')
r_foot = rb[hb > 1.5 * d50].max() if (hb > 1.5 * d50).any() else float('nan')
res = dict(case=CASE, n_particles=len(partIds), n_spheres=len(sph), packing_fraction_column=phi_col,
           bed_top_mm=ztop * 1e3, heap_height_mm=hmax * 1e3, heap_foot_radius_mm=r_foot * 1e3,
           angle_of_repose_deg=aor, aor_from_height_over_foot_deg=math.degrees(math.atan(hmax / r_foot)),
           sim_time_s=O.time, wall_s=wall, steps=O.iter, dt_last=O.dt, eta_roll=(ETA_ROLL if CASE == 'sphere_rr' else 0.0),
           clump_union_volume_frac=fvol, profile_r_mm=(rb * 1e3).tolist(), profile_h_mm=(hb * 1e3).tolist(),
           fit_slope=slope, fit_intercept_mm=icpt * 1e3 if icpt == icpt else None)
print(json.dumps({k: v for k, v in res.items() if not k.startswith('profile')}, indent=1))
json.dump(res, open(os.path.join(OUT, 'result_%s.json' % CASE), 'w'), indent=1)
np.save(os.path.join(OUT, 'frames_%s.npy' % CASE), np.array(frames, dtype=object), allow_pickle=True)
np.save(os.path.join(OUT, 'final_%s.npy' % CASE), np.column_stack([P, R]))
