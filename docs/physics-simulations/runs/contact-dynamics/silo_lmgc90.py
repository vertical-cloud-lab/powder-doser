"""2D flat-bottomed silo discharge with LMGC90 (non-smooth contact dynamics, Moreau-Jean
time stepping, NLGS contact solver, IQS_CLB: inelastic quasi-shock + Coulomb friction).
Rigid discs, mean diameter d = 1 mm (radii uniform in [0.4, 0.6] mm).  Rigid NSCD has no
stiffness scale, so results scale with d and sqrt(d/g): read W/d and Q*sqrt(d/g).
Usage: python silo_lmgc90.py <W_over_d> <workdir> [nsteps] [snap_every] [seed]
"""
import os, sys, json, math, time
import numpy as np

WD = float(sys.argv[1])
work = sys.argv[2]
nsteps = int(sys.argv[3]) if len(sys.argv) > 3 else 6000
snap_every = int(sys.argv[4]) if len(sys.argv) > 4 else 0
seed = int(sys.argv[5]) if len(sys.argv) > 5 else 1
os.makedirs(work, exist_ok=True)
os.chdir(work)

# NumPy >= 2.5 removed np.cross for 2-vectors, which LMGC90 2025's pre-processor still uses
_np_cross = np.cross
def _cross(a, b, *args, **kw):
    a, b = np.asarray(a), np.asarray(b)
    if a.shape[-1] == 2 and b.shape[-1] == 2:
        return a[..., 0] * b[..., 1] - a[..., 1] * b[..., 0]
    return _np_cross(a, b, *args, **kw)
np.cross = _cross

from pylmgc90 import pre, chipy

dmean = 1.0e-3
rmin, rmax = 0.4e-3, 0.6e-3
N = 600
Ls = 30 * dmean            # silo width
W = WD * dmean             # orifice width
t = 0.25e-3                # wall half-thickness
mu_pp, mu_pw = 0.5, 0.4
rho = 2165.0               # NaCl density (only scales the mass flow)

# ---------------- pre-processing ----------------
dim = 2
bodies = pre.avatars(); mats = pre.materials(); mods = pre.models()
svs = pre.see_tables(); tacts = pre.tact_behavs()
grain = pre.material(name='TDURx', materialType='RIGID', density=rho)
wallm = pre.material(name='TWALL', materialType='RIGID', density=rho)
mats.addMaterial(grain, wallm)
mod = pre.model(name='rigid', physics='MECAx', element='Rxx2D', dimension=dim)
mods.addModel(mod)
radii = pre.granulo_Random(N, rmin, rmax, seed=seed)
Hbox = 2.2 * N * math.pi * (0.5 * dmean) ** 2 / (0.8 * Ls)
nb, coor, radii = pre.depositInBox2D(radii, Ls, Hbox)
coor = np.asarray(coor).reshape(-1, 2)
for i in range(nb):
    bodies += pre.rigidDisk(r=radii[i], center=coor[i], model=mod, material=grain, color='BLUEx')
ytop = coor[:, 1].max() + rmax
Hwall = ytop + 5 * dmean
# bottom: two joncs leaving a gap W centred at Ls/2 (rounded ends included)
half = 0.5 * ((Ls - W) / 2 - 2 * t)
for xc in (t + half, Ls - t - half):
    b = pre.rigidJonc(axe1=half, axe2=t, center=[xc, -t], model=mod, material=wallm, color='WALLx')
    b.imposeDrivenDof(component=[1, 2, 3], dofty='vlocy'); bodies += b
for xc in (-t, Ls + t):
    b = pre.rigidJonc(axe1=0.5 * Hwall, axe2=t, center=[xc, 0.5 * Hwall], model=mod, material=wallm, color='WALLx')
    b.rotate(psi=math.pi / 2., center=b.nodes[1].coor)
    b.imposeDrivenDof(component=[1, 2, 3], dofty='vlocy'); bodies += b
lgg = pre.tact_behav(name='iqsg0', law='IQS_CLB', fric=mu_pp)
lgw = pre.tact_behav(name='iqsw0', law='IQS_CLB', fric=mu_pw)
tacts += lgg; tacts += lgw
alert = 0.2 * rmin
svs += pre.see_table(CorpsCandidat='RBDY2', candidat='DISKx', colorCandidat='BLUEx', behav=lgg,
                     CorpsAntagoniste='RBDY2', antagoniste='DISKx', colorAntagoniste='BLUEx', alert=alert)
svs += pre.see_table(CorpsCandidat='RBDY2', candidat='DISKx', colorCandidat='BLUEx', behav=lgw,
                     CorpsAntagoniste='RBDY2', antagoniste='JONCx', colorAntagoniste='WALLx', alert=alert)
post = pre.postpro_commands()
pre.writeDatbox(dim, mats, mods, bodies, tacts, svs, post=post, gravy=[0., -9.81, 0.])

# ---------------- computation (Moreau-Jean + NLGS) ----------------
dt = 2.0e-4
theta = 0.5
chipy.Initialize(); chipy.checkDirectories()
chipy.SetDimension(dim)
chipy.TimeEvolution_SetTimeStep(dt)
chipy.Integrator_InitTheta(theta)
chipy.ReadDatbox(deformable=False)
chipy.ComputeMass()
chipy.RBDY2_SetYminBoundary(-20 * dmean)   # discs far below the outlet become invisible
stype, norm, tol, relax, it1, it2 = 'Stored_Delassus_Loops         ', 'Quad ', 1e-3, 1.0, 25, 8
ts, nout, frames = [], [], []
t0 = time.time()
for k in range(nsteps):
    chipy.IncrementStep()
    chipy.ComputeFext(); chipy.ComputeBulk(); chipy.ComputeFreeVelocity()
    chipy.SelectProxTactors()
    chipy.RecupRloc(); chipy.ExSolver(stype, norm, tol, relax, it1, it2); chipy.StockRloc()
    chipy.ComputeDof(); chipy.UpdateStep()
    if k % 25 == 0:
        c = np.array(chipy.RBDY2_GetAllBodyVector('Coor_'))[:nb]
        ts.append((k + 1) * dt); nout.append(int((c[:, 1] < -2 * dmean).sum()))
        if snap_every and k % snap_every == 0:
            frames.append(np.column_stack([c[:, 0], c[:, 1]]).astype(np.float32))
wall = time.time() - t0
chipy.Finalize()
ts, nout = np.array(ts), np.array(nout)
# steady discharge rate: linear fit of the cumulative count while 10 %..60 % of the grains have left
m = (nout >= 0.10 * nb) & (nout <= 0.60 * nb)
rate = float(np.polyfit(ts[m], nout[m], 1)[0]) if m.sum() > 3 else float('nan')
res = dict(W_over_d=WD, n_discs=int(nb), dt=dt, nsteps=nsteps, t_end=nsteps * dt, wall_s=wall,
           rate_discs_per_s=rate, rate_dimless=rate * math.sqrt(dmean / 9.81),
           mass_rate_per_m_kg_s=rate * rho * math.pi * np.mean(np.asarray(radii[:nb]) ** 2),
           fit_points=int(m.sum()), n_out_final=int(nout[-1]), t=ts.tolist(), n_out=nout.tolist())
json.dump(res, open('result.json', 'w'))
if frames:
    np.save('frames.npy', np.array(frames)); np.save('radii.npy', np.asarray(radii[:nb]))
print(json.dumps({k: v for k, v in res.items() if k not in ('t', 'n_out')}))
