"""Quasi-2D tribocharging DEM of salt grains in a rotating PLA tube cross-section (numba).

Spheres (salt, d = 0.36-0.49 mm) confined to a plane inside a drum of the auger bore
radius (10.45 mm) turning at 60 rpm. Contacts: linear spring-dashpot + regularised
Coulomb friction, no particle rotation. Charging: condenser model (Matsuyama &
Yamamoto; Pei, Wu & Adams 2016; Korevaar et al. 2014):
    dq = k_acc * eps0 * dS / z0 * (V_c - z0 * (sigma_p - sigma_w) / eps0)
with dS the newly touched (loading) or swept (sliding) Hertzian contact area, the
wall counter-charge stored in 120 co-rotating wall patches, and |sigma| of every
particle and patch capped at eps0 * E_b (gas breakdown, Paschen at a gap of one
grain diameter). Forces: particle-particle Coulomb (direct sum), particle-patch
Coulomb (softened), dielectric image attraction to the PLA wall.

Usage: OMP_NUM_THREADS=1 NUMBA_NUM_THREADS=1 python run.py OUTDIR_REPO SCRATCH [N] [NREV] [K_ACC]
"""
import json
import os
import sys
import time

import numpy as np
import numba as nb

OUT = sys.argv[1]
SCR = sys.argv[2]
N = int(sys.argv[3]) if len(sys.argv) > 3 else 600
NREV = float(sys.argv[4]) if len(sys.argv) > 4 else 8.0
K_ACC = float(sys.argv[5]) if len(sys.argv) > 5 else 50.0
GASES = sys.argv[6].split(",") if len(sys.argv) > 6 else ["air", "argon"]
os.makedirs(SCR, exist_ok=True)

EPS0 = 8.854e-12
KE = 1.0 / (4 * np.pi * EPS0)
G = 9.81
RHO = 2165.0
RMIN, RMAX = 0.18e-3, 0.245e-3
D_MEAN = 0.42e-3
RD = 10.45e-3                 # bore radius
OMEGA = 2 * np.pi             # 60 rpm
KN = 5.0                      # N/m (soft; overlap < ~2 % d)
E_REST = 0.5
ZETA = -np.log(E_REST) / np.sqrt(np.pi ** 2 + np.log(E_REST) ** 2)
MU_PP, MU_PW = 0.5, 0.4       # LIGGGHTS twin values
CT_FAC = 5.0                  # tangential regularisation (x normal damping)
E_SALT, NU_SALT = 39e9, 0.25
E_PLA, NU_PLA = 3.5e9, 0.36
ESTAR_PP = 1.0 / (2 * (1 - NU_SALT ** 2) / E_SALT)
ESTAR_PW = 1.0 / ((1 - NU_SALT ** 2) / E_SALT + (1 - NU_PLA ** 2) / E_PLA)
VC = 0.5                      # V, contact potential difference salt-PLA (salt -> +)
Z0 = 0.4e-9                   # m, charge-transfer cut-off gap
EPS_R_PLA = 3.0
BETA = (EPS_R_PLA - 1) / (EPS_R_PLA + 1)
NB = 120                      # wall patches
PATCH_AREA = (2 * np.pi * RD / NB) * D_MEAN
SOFT_W = 0.5 * (2 * np.pi * RD / NB)


def paschen_field(A, B, gap_m, gamma=0.01, p_torr=760.0):
    pd = p_torr * gap_m * 100.0                      # Torr cm
    vb = B * pd / (np.log(A * pd) - np.log(np.log(1 + 1 / gamma)))
    return vb / gap_m, vb


# Townsend coefficients (Raizer, Gas Discharge Physics, 1991, Table 4.1)
EB_AIR, VB_AIR = paschen_field(15.0, 365.0, D_MEAN)
EB_AR, VB_AR = paschen_field(12.0, 180.0, D_MEAN)
SIG_CAP = {"air": EPS0 * EB_AIR, "argon": EPS0 * EB_AR}

CELL = 2 * RMAX
NC = int(np.ceil(2 * RD / CELL)) + 2


@nb.njit(cache=True)
def build_cells(x):
    n = x.shape[0]
    head = -np.ones((NC, NC), np.int64)
    nxt = -np.ones(n, np.int64)
    for i in range(n):
        cx = int((x[i, 0] + RD) / CELL) + 1
        cy = int((x[i, 1] + RD) / CELL) + 1
        cx = min(max(cx, 0), NC - 1)
        cy = min(max(cy, 0), NC - 1)
        nxt[i] = head[cx, cy]
        head[cx, cy] = i
    return head, nxt


@nb.njit(cache=True)
def elec_forces(x, q, r, qw, t):
    n = x.shape[0]
    f = np.zeros((n, 2))
    for i in range(n):
        for j in range(i + 1, n):
            dx = x[j, 0] - x[i, 0]
            dy = x[j, 1] - x[i, 1]
            d = np.sqrt(dx * dx + dy * dy)
            ds = max(d, r[i] + r[j])
            fm = KE * q[i] * q[j] / (ds * ds * d)
            f[j, 0] += fm * dx
            f[j, 1] += fm * dy
            f[i, 0] -= fm * dx
            f[i, 1] -= fm * dy
    for b in range(NB):
        if qw[b] == 0.0:
            continue
        ang = (b + 0.5) * 2 * np.pi / NB + OMEGA * t
        px = RD * np.cos(ang)
        py = RD * np.sin(ang)
        for i in range(n):
            dx = x[i, 0] - px
            dy = x[i, 1] - py
            d2 = dx * dx + dy * dy + SOFT_W * SOFT_W
            fm = KE * q[i] * qw[b] / (d2 * np.sqrt(d2))
            f[i, 0] += fm * dx
            f[i, 1] += fm * dy
    for i in range(n):
        rr = np.sqrt(x[i, 0] ** 2 + x[i, 1] ** 2)
        s = max(RD - rr, 0.5 * r[i])
        fm = BETA * KE * q[i] * q[i] / (4 * s * s)
        f[i, 0] += fm * x[i, 0] / rr
        f[i, 1] += fm * x[i, 1] / rr
    return f


@nb.njit(cache=True)
def run_steps(x, v, r, m, q, qw, t, dt, nsteps, ne, fe, charge_on, k_acc, sig_cap, stats):
    """stats: [n_wall_loading_events, total_dq_wall]"""
    n = x.shape[0]
    qcap = sig_cap * 4 * np.pi * r * r
    qwcap = sig_cap * PATCH_AREA
    for s in range(nsteps):
        if s % ne == 0:
            fe[:, :] = elec_forces(x, q, r, qw, t)
        f = fe.copy()
        for i in range(n):
            f[i, 1] -= m[i] * G
        head, nxt = build_cells(x)
        for i in range(n):
            cx = int((x[i, 0] + RD) / CELL) + 1
            cy = int((x[i, 1] + RD) / CELL) + 1
            for ax in range(cx - 1, cx + 2):
                for ay in range(cy - 1, cy + 2):
                    if ax < 0 or ay < 0 or ax >= NC or ay >= NC:
                        continue
                    j = head[ax, ay]
                    while j >= 0:
                        if j > i:
                            dx = x[j, 0] - x[i, 0]
                            dy = x[j, 1] - x[i, 1]
                            rs = r[i] + r[j]
                            d2 = dx * dx + dy * dy
                            if d2 < rs * rs:
                                d = np.sqrt(d2)
                                nx = dx / d
                                ny = dy / d
                                delta = rs - d
                                dvx = v[j, 0] - v[i, 0]
                                dvy = v[j, 1] - v[i, 1]
                                vn = dvx * nx + dvy * ny
                                meff = m[i] * m[j] / (m[i] + m[j])
                                c = 2.0 * ZETA * np.sqrt(KN * meff)
                                fn = max(KN * delta - c * vn, 0.0)
                                vt = -dvx * ny + dvy * nx
                                ft = -CT_FAC * c * vt
                                lim = MU_PP * fn
                                sliding = False
                                if ft > lim:
                                    ft = lim
                                    sliding = True
                                elif ft < -lim:
                                    ft = -lim
                                    sliding = True
                                fx = fn * nx - ft * ny
                                fy = fn * ny + ft * nx
                                f[j, 0] += fx
                                f[j, 1] += fy
                                f[i, 0] -= fx
                                f[i, 1] -= fy
                                if charge_on and fn > 0.0:
                                    rstar = r[i] * r[j] / rs
                                    a = (3 * fn * rstar / (4 * ESTAR_PP)) ** (1.0 / 3.0)
                                    S = np.pi * a * a
                                    dS = 0.0
                                    if vn < 0.0:
                                        dS += (2.0 / 3.0) * S * (-vn * dt) / delta
                                    if sliding:
                                        dS += 2 * a * abs(vt) * dt
                                    si = q[i] / (4 * np.pi * r[i] * r[i])
                                    sj = q[j] / (4 * np.pi * r[j] * r[j])
                                    dq = k_acc * dS * (sj - si) * 0.5
                                    q[i] += dq
                                    q[j] -= dq
                        j = nxt[j]
        # wall
        for i in range(n):
            rr = np.sqrt(x[i, 0] ** 2 + x[i, 1] ** 2)
            delta = r[i] - (RD - rr)
            if delta > 0.0:
                ox = x[i, 0] / rr
                oy = x[i, 1] / rr
                wvx = -OMEGA * RD * oy
                wvy = OMEGA * RD * ox
                rvx = v[i, 0] - wvx
                rvy = v[i, 1] - wvy
                vn = rvx * ox + rvy * oy             # >0: moving into the wall
                c = 2.0 * ZETA * np.sqrt(KN * m[i])
                fn = max(KN * delta + c * vn, 0.0)
                vt = -rvx * oy + rvy * ox
                ft = -CT_FAC * c * vt
                lim = MU_PW * fn
                sliding = False
                if ft > lim:
                    ft = lim
                    sliding = True
                elif ft < -lim:
                    ft = -lim
                    sliding = True
                f[i, 0] += -fn * ox - ft * oy
                f[i, 1] += -fn * oy + ft * ox
                if charge_on and fn > 0.0:
                    a = (3 * fn * r[i] / (4 * ESTAR_PW)) ** (1.0 / 3.0)
                    S = np.pi * a * a
                    dS = 0.0
                    if vn > 0.0:
                        dS += (2.0 / 3.0) * S * (vn * dt) / delta
                        stats[0] += dt * vn / delta
                    if sliding:
                        dS += 2 * a * abs(vt) * dt
                    ang = np.arctan2(x[i, 1], x[i, 0]) - OMEGA * t
                    ang = ang % (2 * np.pi)
                    if ang < 0.0:
                        ang += 2 * np.pi
                    b = int(ang / (2 * np.pi) * NB) % NB
                    sp = q[i] / (4 * np.pi * r[i] * r[i])
                    sw = qw[b] / PATCH_AREA
                    dq = k_acc * EPS0 * dS / Z0 * (VC - Z0 * (sp - sw) / EPS0)
                    # gas-breakdown caps on the particle and on the wall patch
                    if dq > 0.0:
                        dq = min(dq, min(max(qcap[i] - q[i], 0.0), max(qwcap + qw[b], 0.0)))
                    else:
                        dq = max(dq, max(-max(qcap[i] + q[i], 0.0), -max(qwcap - qw[b], 0.0)))
                    q[i] += dq
                    qw[b] -= dq
                    stats[1] += dq
        for i in range(n):
            v[i, 0] += f[i, 0] / m[i] * dt
            v[i, 1] += f[i, 1] / m[i] * dt
            x[i, 0] += v[i, 0] * dt
            x[i, 1] += v[i, 1] * dt
        t += dt
    return t


def init_particles(n, rng):
    r = rng.uniform(RMIN, RMAX, n)
    pts = []
    s = 2 * RMAX * 1.05
    y = -RD + RMAX * 1.2
    row = 0
    while len(pts) < n:
        xx = -RD + (s / 2 if row % 2 else 0.0)
        while xx < RD and len(pts) < n:
            if xx * xx + y * y < (RD - 1.2 * RMAX) ** 2:
                pts.append((xx, y))
            xx += s
        y += s * np.sqrt(3) / 2
        row += 1
    x = np.array(pts[:n])
    m = RHO * 4.0 / 3.0 * np.pi * r ** 3
    return x, np.zeros_like(x), r, m


def diagnostics(x, r, m, q, sig_cap):
    rr = np.sqrt((x ** 2).sum(1))
    contact = (RD - rr) < 1.05 * r
    stuck = contact & (x[:, 1] > 0.6 * RD)            # on the wall above the bed's highest point (~0.4 R): held by adhesion
    qcap = sig_cap * 4 * np.pi * r ** 2
    return {"q_over_m_uC_per_kg": float(q.sum() / m.sum() * 1e6),
            "absq_over_m_uC_per_kg": float(np.abs(q).sum() / m.sum() * 1e6),
            "frac_at_cap": float(np.mean(np.abs(q) >= 0.98 * qcap)),
            "frac_stuck_top": float(stuck.mean()),
            "frac_wall_contact": float(contact.mean())}


def simulate(gas, seed=3):
    rng = np.random.default_rng(seed)
    x, v, r, m = init_particles(N, rng)
    q = np.zeros(N)
    qw = np.zeros(NB)
    fe = np.zeros((N, 2))
    stats = np.zeros(2)
    tc = np.pi * np.sqrt((RHO * 4 / 3 * np.pi * RMIN ** 3 / 2) / KN)
    dt = tc / 15
    steps_per_rev = int(round(1.0 / dt))
    dt = 1.0 / steps_per_rev
    ne = 25
    frames_per_rev = 12
    chunk = steps_per_rev // frames_per_rev
    sig = SIG_CAP[gas]
    t = 0.0
    t = run_steps(x, v, r, m, q, qw, t, dt, int(0.75 * steps_per_rev), ne, fe, False, K_ACC, sig, stats)
    hist, frames = [], []
    nframes = int(NREV * frames_per_rev)
    d0 = diagnostics(x, r, m, q, sig)
    d0["rev"] = 0.0
    hist.append(d0)
    frames.append((x.copy(), q.copy()))
    t1 = time.time()
    for k in range(nframes):
        t = run_steps(x, v, r, m, q, qw, t, dt, chunk, ne, fe, True, K_ACC, sig, stats)
        d = diagnostics(x, r, m, q, sig)
        d["rev"] = (k + 1) / frames_per_rev
        hist.append(d)
        frames.append((x.copy(), q.copy()))
        if (k + 1) % frames_per_rev == 0:
            print(gas, "rev %.1f" % d["rev"], {kk: round(vv, 4) for kk, vv in d.items()},
                  "wall q total %.3e C" % qw.sum(), "%.1fs" % (time.time() - t1), flush=True)
    np.savez_compressed(os.path.join(SCR, f"frames_{gas}.npz"), x=np.array([f[0] for f in frames], np.float32),
                        q=np.array([f[1] for f in frames], np.float32), r=r.astype(np.float32),
                        qcap=(sig * 4 * np.pi * r ** 2).astype(np.float32), qw=qw)
    charge_cons = float(q.sum() + qw.sum())
    return {"hist": hist, "dt": dt, "steps_per_rev": steps_per_rev, "sigma_cap": sig, "charge_conservation_C": charge_cons,
            "wall_patch_frac_at_cap": float(np.mean(np.abs(qw) >= 0.98 * sig * PATCH_AREA)),
            "q_particle_total_C": float(q.sum())}


if __name__ == "__main__":
    t0 = time.time()
    out = {"N": N, "NREV": NREV, "K_ACC": K_ACC, "E_b_air_V_per_m": EB_AIR, "E_b_argon_V_per_m": EB_AR,
           "V_b_air": VB_AIR, "V_b_argon": VB_AR, "sigma_cap": SIG_CAP, "runs": {}}
    for gas in GASES:
        tg = time.time()
        out["runs"][gas] = simulate(gas)
        out["runs"][gas]["wall_s"] = time.time() - tg
    out["wall_s"] = time.time() - t0
    with open(os.path.join(SCR, "charge_runs.json"), "w") as f:
        json.dump(out, f, indent=1)
    print("total wall", out["wall_s"])
