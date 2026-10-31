"""PyChrono core ChSystemSMC (CPU, Bullet collision) flat-bottomed silo discharge through a square orifice.

Usage: python silo_discharge.py --L 9 --n 1200 --out /tmp/sims-scratch/dem-chrono-cpu
       python silo_discharge.py --rolling-check      (single-sphere test of SetRollingFriction)
Coarse-grained salt: diameters 4 x (0.361/0.425/0.489) mm, number fractions 0.3/0.4/0.3.
"""
import argparse, json, math, os, time
import numpy as np
import pychrono as chrono

ap = argparse.ArgumentParser()
ap.add_argument('--L', type=float, default=9.0, help='square orifice side, mm')
ap.add_argument('--n', type=int, default=1200)
ap.add_argument('--box', type=float, default=18.0, help='silo inner width, mm')
ap.add_argument('--cg', type=float, default=4.0)
ap.add_argument('--dt', type=float, default=5e-5)
ap.add_argument('--t-settle', type=float, default=0.25)
ap.add_argument('--t-flow', type=float, default=0.8)
ap.add_argument('--young', type=float, default=2e5)
ap.add_argument('--out', default='/tmp/sims-scratch/dem-chrono-cpu')
ap.add_argument('--snap-every', type=float, default=0.02)
ap.add_argument('--rolling-check', action='store_true')
ap.add_argument('--lu', type=float, default=1000.0, help='internal length unit factor: 1000 = millimetres (Bullet is unstable with mm-size bodies in metres)')
ap.add_argument('--cbt', type=float, default=-1.0, help='Bullet contact breaking threshold (m); <0 keeps the default')
a = ap.parse_args()
os.makedirs(a.out, exist_ok=True)

RHO, NU, EN = 2165.0, 0.3, 0.5
LU = a.lu                      # length unit factor; SI values are converted on input/output
RHO_U = RHO / LU ** 3          # kg per (length unit)^3
MU_PP, MU_PW, MU_ROLL = 0.5, 0.4, 0.3


def make_system():
    if a.cbt > 0:
        chrono.ChCollisionSystemBullet.SetContactBreakingThreshold(a.cbt * LU)
    s = chrono.ChSystemSMC()
    s.SetCollisionSystemType(chrono.ChCollisionSystem.Type_BULLET)
    s.SetContactForceModel(chrono.ChSystemSMC.Hertz)
    s.SetTangentialDisplacementModel(chrono.ChSystemSMC.MultiStep)
    s.UseMaterialProperties(True)
    s.SetNumThreads(1, 1, 1)
    s.SetGravitationalAcceleration(chrono.ChVector3d(0, 0, -9.81 * LU))
    return s


def material(mu, roll):
    m = chrono.ChContactMaterialSMC()
    m.SetYoungModulus(a.young / LU)   # Pa -> kg/(unit s^2)
    m.SetPoissonRatio(NU)
    m.SetRestitution(EN)
    m.SetFriction(mu)
    m.SetRollingFriction(roll)
    return m


def add_box(s, mat, hx, hy, hz, pos):
    b = chrono.ChBody()
    b.SetFixed(True)
    b.SetPos(chrono.ChVector3d(*[LU * c for c in pos]))
    b.AddCollisionShape(chrono.ChCollisionShapeBox(mat, 2 * hx * LU, 2 * hy * LU, 2 * hz * LU))
    b.EnableCollision(True)
    s.AddBody(b)
    return b


def add_sphere(s, mat, r, pos, vel=(0, 0, 0)):
    m = RHO * 4.0 / 3.0 * math.pi * r ** 3          # kg (same in any length unit)
    ru = r * LU
    b = chrono.ChBody()
    b.SetMass(m)
    b.SetInertiaXX(chrono.ChVector3d(*(3 * [0.4 * m * ru * ru])))
    b.SetPos(chrono.ChVector3d(*[LU * c for c in pos]))
    b.SetPosDt(chrono.ChVector3d(*[LU * c for c in vel]))
    b.AddCollisionShape(chrono.ChCollisionShapeSphere(mat, ru))
    b.EnableCollision(True)
    s.AddBody(b)
    return b, m


if a.rolling_check:
    # a sphere launched rolling on a plane: with a working rolling friction it should slow down
    res = {}
    for roll in (0.0, MU_ROLL):
        s = make_system()
        chrono.ChCollisionModel.SetDefaultSuggestedEnvelope(5e-5 * LU)
        chrono.ChCollisionModel.SetDefaultSuggestedMargin(2e-5 * LU)
        mp = material(MU_PP, roll)
        add_box(s, mp, 0.05, 0.05, 0.005, (0, 0, -0.005))
        r = 0.85e-3
        b, m = add_sphere(s, mp, r, (0, 0, r * 0.999), vel=(0.1, 0, 0))
        b.SetAngVelParent(chrono.ChVector3d(0, 0.1 / r, 0))
        for _ in range(int(0.5 / a.dt)):
            s.DoStepDynamics(a.dt)
        res['mu_roll=%g' % roll] = dict(vx_after_0p5s_m_s=b.GetPosDt().x / LU, x_after_0p5s_m=b.GetPos().x / LU, v0_m_s=0.1)
    print(json.dumps(res))
    json.dump(res, open(os.path.join(a.out, 'rolling_check.json'), 'w'), indent=1)
    raise SystemExit

d_ref = np.array([0.361, 0.425, 0.489]) * 1e-3 * a.cg
p_ref = np.array([0.3, 0.4, 0.3])
dmax = d_ref.max()
chrono.ChCollisionModel.SetDefaultSuggestedEnvelope(0.05 * d_ref.mean() * LU)
chrono.ChCollisionModel.SetDefaultSuggestedMargin(0.02 * d_ref.mean() * LU)

s = make_system()
mp = material(MU_PP, MU_ROLL)
mw = material(MU_PW, MU_ROLL)
W = a.box * 1e-3 / 2          # half width of silo
L = a.L * 1e-3 / 2            # half side of orifice
H = 0.10                      # wall height
t = 0.002                     # plate half thickness
# side walls
add_box(s, mw, t, W + 2 * t, H / 2, (W + t, 0, H / 2))
add_box(s, mw, t, W + 2 * t, H / 2, (-W - t, 0, H / 2))
add_box(s, mw, W, t, H / 2, (0, W + t, H / 2))
add_box(s, mw, W, t, H / 2, (0, -W - t, H / 2))
# floor = 4 plates around the square orifice, top surface at z = 0
add_box(s, mw, (W - L) / 2, W, t, ((W + L) / 2, 0, -t))
add_box(s, mw, (W - L) / 2, W, t, (-(W + L) / 2, 0, -t))
add_box(s, mw, L, (W - L) / 2, t, (0, (W + L) / 2, -t))
add_box(s, mw, L, (W - L) / 2, t, (0, -(W + L) / 2, -t))
plug = add_box(s, mw, L + 1e-3, L + 1e-3, t, (0, 0, -t))

# particles on a jittered lattice above the floor
rng = np.random.default_rng(7)
sp = dmax * 1.04
coords = np.arange(-W + sp / 2, W - sp / 2 + 1e-12, sp)
pts = []
z = sp / 2 + 1e-4
while len(pts) < a.n:
    for x in coords:
        for y in coords:
            if len(pts) < a.n:
                pts.append((x + rng.uniform(-3e-5, 3e-5), y + rng.uniform(-3e-5, 3e-5), z))
    z += sp
diam = rng.choice(d_ref, size=a.n, p=p_ref)
bodies, masses = [], []
for p, dm in zip(pts, diam):
    b, m = add_sphere(s, mp, dm / 2, p, vel=(rng.uniform(-0.02, 0.02), rng.uniform(-0.02, 0.02), 0))
    bodies.append(b); masses.append(m)
masses = np.array(masses)
n = len(bodies)
print('built %d spheres, lattice top z=%.1f mm, dt=%.1e' % (n, z * 1e3, a.dt), flush=True)

active = np.ones(n, bool)
n_out, m_out = 0, 0.0
rows, snaps, snap_t = [], [], []
park_i = 0
Z_COUNT = -0.004
n_settle = int(round(a.t_settle / a.dt)); n_flow = int(round(a.t_flow / a.dt))
check = int(round(0.005 / a.dt)); snap_every = int(round(a.snap_every / a.dt))
fill_h = None
import signal
class _Stop(Exception):
    pass
def _on_term(signum, frame):
    raise _Stop()
signal.signal(signal.SIGTERM, _on_term)   # a timeout still writes what was simulated
stopped_early = False
t0 = time.time()
try:
  for step in range(1, n_settle + n_flow + 1):
      if step == n_settle + 1:
          zs = np.array([bodies[i].GetPos().z / LU for i in range(n)])
          fill_h = float(np.percentile(zs + diam / 2, 98))
          plug.SetPos(chrono.ChVector3d(0, 0, -0.05 * LU))
          print('t=%.3f s: plug removed; fill height %.2f mm' % (s.GetChTime(), fill_h * 1e3), flush=True)
      s.DoStepDynamics(a.dt)
      if step % check == 0:
          for i in np.flatnonzero(active):
              if bodies[i].GetPos().z / LU < Z_COUNT:
                  active[i] = False; n_out += 1; m_out += masses[i]
                  b = bodies[i]
                  b.SetFixed(True); b.EnableCollision(False)
                  b.SetPos(chrono.ChVector3d(LU * (-0.5 + 0.003 * (park_i % 300)), LU * 0.5, LU * (-0.5 - 0.003 * (park_i // 300))))
                  park_i += 1
          vmax = max((bodies[i].GetPosDt().Length() for i in np.flatnonzero(active)), default=0.0) / LU
          rows.append((s.GetChTime(), n_out, m_out, s.GetNumContacts(), time.time() - t0, vmax))
      if step % snap_every == 0 or step == 1:
          snaps.append(np.array([[bodies[i].GetPos().x / LU, bodies[i].GetPos().y / LU, bodies[i].GetPos().z / LU, diam[i] / 2,
                                  float(active[i])] for i in range(n)], dtype=np.float32))
          snap_t.append(s.GetChTime())
      if step % (4 * check) == 0:
          print('t=%.3f s  out=%d  contacts=%d  vmax=%.3g m/s  wall=%.0f s' % (s.GetChTime(), n_out, s.GetNumContacts(), rows[-1][5], time.time() - t0), flush=True)
except _Stop:
    stopped_early = True
    print('SIGTERM: stopping early at t=%.3f s' % s.GetChTime(), flush=True)
wall = time.time() - t0
rows = np.array(rows)
tag = 'L%04.1f' % a.L
np.savez_compressed(os.path.join(a.out, tag + '_snaps.npz'), snaps=np.array(snaps), t=np.array(snap_t))
np.savetxt(os.path.join(a.out, tag + '_outflow.csv'), rows, delimiter=',', header='t_s,n_out,m_out_kg,contacts,wall_s,vmax_m_s', comments='')
meta = dict(L_mm=a.L, n=n, box_mm=a.box, cg=a.cg, d_m=d_ref.tolist(), nfrac=p_ref.tolist(), rho=RHO, young=a.young,
            poisson=NU, restitution=EN, mu_pp=MU_PP, mu_pw=MU_PW, mu_roll_set=MU_ROLL, dt=a.dt,
            t_settle=a.t_settle, t_flow=a.t_flow, fill_height_m=fill_h, total_mass_kg=float(masses.sum()),
            n_out=int(n_out), m_out_kg=float(m_out), wall_s=wall, particle_steps=float(n) * (n_settle + n_flow),
            chrono_version='10.0.0 (conda-forge)', contact_breaking_threshold=a.cbt, length_unit_factor=LU, stopped_early=stopped_early, t_end=s.GetChTime())
json.dump(meta, open(os.path.join(a.out, tag + '_meta.json'), 'w'), indent=1)
print(json.dumps(meta), flush=True)
