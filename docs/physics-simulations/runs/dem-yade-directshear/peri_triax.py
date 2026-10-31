# Yade periodic triaxial compression of salt-sized spheres with cohesive-frictional contacts (CohFrictMat).
# Usage: yadedaily -n -x peri_triax.py <sigma3_Pa> <outdir> [N]
import sys, os, json, time, math
import numpy as np
from yade import *
from yade import utils, pack

s3 = float(sys.argv[1]) if len(sys.argv) > 1 else 100.0
outdir = sys.argv[2] if len(sys.argv) > 2 else '/tmp/sims-scratch/dem-yade-directshear'
N = int(sys.argv[3]) if len(sys.argv) > 3 else 1000
os.makedirs(outdir, exist_ok=True)

d = np.array([0.361, 0.425, 0.489]) * 1e-3     # real salt diameters (no coarse graining)
nfrac = np.array([0.3, 0.4, 0.3])
rho, E, nu = 2165.0, 2.0e5, 0.3
mu_pp, mu_compact = 0.5, 0.1                    # friction while shearing / during compaction (denser sample)
eta_roll = 0.3                                   # rolling friction: M_max = eta_roll * R * Fn
Bo = 5.0                                         # granular Bond number of the mean particle (adhesion / weight)
m_mean = rho * math.pi / 6 * (0.425e-3) ** 3
F_adh = Bo * m_mean * 9.81                       # N, bond strength of a mean-size contact
coh = F_adh / (0.425e-3 / 2) ** 2                # Pa; Yade: normalAdhesion = normalCohesion * min(R1,R2)^2
I_target = 2.5e-3                                # inertial number for the shear phase
eps_max = 0.15                                   # axial (log) strain at end of shear

mat = O.materials.append(CohFrictMat(young=E, poisson=nu, density=rho, frictionAngle=math.atan(mu_compact),
                                     isCohesive=True, normalCohesion=coh, shearCohesion=coh, fragile=True,
                                     momentRotationLaw=True, etaRoll=eta_roll, alphaKr=2.0, label='salt'))
# random loose periodic cloud, trimodal number PSD
rng = np.random.default_rng(3)
radii = rng.choice(d, size=N, p=nfrac) / 2
Vs = np.sum(4 / 3 * np.pi * radii ** 3)
L = (Vs / 0.22) ** (1 / 3)
O.periodic = True
O.cell.hSize = Matrix3(L, 0, 0, 0, L, 0, 0, 0, L)
rads_sorted = np.sort(radii)[::-1]
cent = np.zeros((N, 3))
for i, r in enumerate(rads_sorted):
    for attempt in range(50000):
        c = rng.uniform(0, L, 3)
        if i == 0:
            break
        dv = cent[:i] - c
        dv -= L * np.round(dv / L)          # minimum image (periodic cell)
        if np.all(np.sum(dv ** 2, axis=1) > (rads_sorted[:i] + r) ** 2):
            break
    cent[i] = c
for c, r in zip(cent, rads_sorted):
    O.bodies.append(utils.sphere(tuple(c), r, material=mat))

O.engines = [
    ForceResetter(),
    InsertionSortCollider([Bo1_Sphere_Aabb()]),
    InteractionLoop(
        [Ig2_Sphere_Sphere_ScGeom6D()],
        [Ip2_CohFrictMat_CohFrictMat_CohFrictPhys(setCohesionNow=False, setCohesionOnNewContacts=True, label='ip2')],
        [Law2_ScGeom6D_CohFrictPhys_CohesionMoment(useIncrementalForm=True, always_use_moment_law=True, label='law')],
    ),
    PeriTriaxController(label='triax', goal=(-s3, -s3, -s3), stressMask=7, dynCell=True,
                        maxStrainRate=(5, 5, 5), maxUnbalanced=0.02, relStressTol=1e-2, doneHook='compDone()'),
    NewtonIntegrator(damping=0.2),
]
O.dt = 0.5 * PWaveTimeStep()
phase = {'p': 'compact'}
def compDone():
    phase['p'] = 'compacted'
    O.pause()

t0 = time.time()
O.run(60000, True)  # pauses at compDone
it_comp = O.iter
compacted = phase['p'] == 'compacted'
print('compaction: done=%s iter=%d stress=%s porosity=%.3f wall=%.0f s' % (compacted, O.iter, triax.stress, utils.porosity(), time.time() - t0), flush=True)
phi0 = 1 - utils.porosity()
# switch to shear: friction 0.5, constant lateral stress, strain-controlled axial compression
utils.setContactFriction(math.atan(mu_pp))
O.cell.trsf = Matrix3.Identity
rate = I_target / (0.425e-3 * math.sqrt(rho / s3))
triax.goal = (-s3, -s3, -eps_max)
triax.stressMask = 3
triax.maxStrainRate = (10 * rate, 10 * rate, rate)
triax.maxUnbalanced = 10
triax.doneHook = 'shearDone()'
def shearDone():
    phase['p'] = 'sheared'
    O.pause()
rows = []
def rec():
    st = utils.getStress()
    nb = sum(1 for i in O.interactions if i.isReal and i.phys.cohesionBroken is False)
    nreal = sum(1 for i in O.interactions if i.isReal)
    rows.append((O.cell.trsf[2, 2] - 1, -triax.strain[2], -st[0, 0], -st[1, 1], -st[2, 2], -sum(triax.strain), nb, nreal, 1 - utils.porosity()))
O.engines = O.engines + [PyRunner(command='rec()', iterPeriod=200)]
n_shear_max = int(1.3 * eps_max / rate / O.dt)
O.run(n_shear_max, True)
wall = time.time() - t0
rows = np.array(rows)
np.savetxt(os.path.join(outdir, 's3_%04d.csv' % s3), rows, delimiter=',',
           header='trsf_zz_minus1,eps_axial_log,sxx_Pa,syy_Pa,szz_Pa,eps_vol_log_compr_pos,n_cohesive,n_contacts,phi', comments='')
meta = dict(sigma3_Pa=s3, N=N, L_m=L, d_m=d.tolist(), nfrac=nfrac.tolist(), rho=rho, young=E, poisson=nu, mu_pp=mu_pp,
            mu_compaction=mu_compact, eta_roll=eta_roll, Bo=Bo, F_adh_N=F_adh, normalCohesion_Pa=coh,
            I_target=I_target, axial_rate_1_s=rate, eps_max=eps_max, dt=O.dt, compaction_done=compacted,
            iter_compaction=it_comp, iter_total=O.iter, phi_after_compaction=phi0, wall_s=wall, final_phase=phase['p'])
json.dump(meta, open(os.path.join(outdir, 's3_%04d_meta.json' % s3), 'w'), indent=1)
print(json.dumps(meta), flush=True)
