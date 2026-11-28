"""Test 10: air pumped into the Faraday cup by the falling powder stream, and where fine grains go.

Axisymmetric (r, z) laminar flow, mac2d with hybrid differencing, air nu = 1.56e-5 m2/s.
Geometry (mm): grounded can, inner radius 35, wall 1, z 0-80; printed lid z 80-83 with a Ø20 inlet;
inner cup Ø40 x 50 (wall and floor 1 mm) on 15 mm standoffs: floor z 15-16, rim at z 65.
Doser outlet on the axis 10 mm above the lid (z = 93). Open top at z = 123, outer radius 60.
The stream (radius 1.5 mm) relaxes the air towards the grain speed v_p(z) from stream_model at the
local drag rate  c = mdot f / (v_p pi b^2 rho_a tau_p)  (two-way momentum coupling, implicit).
Tracer grains (5-100 um, rho 1450 / 2165 / 3100) are then tracked in the time-averaged field with
drag (Schiller-Naumann) and gravity: injected (1) in the stream at the lid inlet with the stream
speed, (2) at the stream's edge (r 1.5-4 mm) with the local air velocity, (3) as splash from the
heap (0.1-0.5 m/s, 10-80 deg up). Outcome: stays in the inner cup
(on a wall, the floor or airborne at the end) or leaves it (through its Ø40 mouth; and of those,
out through the lid's Ø20 inlet).
Usage: python faraday_flow.py flow <case>    python faraday_flow.py track <case>
cases: fine1 (Si-325, 1 g/s), fine01 (Si-325, 0.1 g/s), salt1 (salt 425 um, 1 g/s)
"""
import json
import sys
import time

import numpy as np

from mac2d import MAC2D
import stream_model as sm

NU = 1.56e-5
CASES = {
    "fine1": dict(mdot=1e-3, d=25e-6, rho_p=2330.0, rho_b=770.0, label="Si-325-like, d50 25 um, 1 g/s"),
    "fine01": dict(mdot=1e-4, d=25e-6, rho_p=2330.0, rho_b=770.0, label="Si-325-like, d50 25 um, 0.1 g/s"),
    "salt1": dict(mdot=1e-3, d=425e-6, rho_p=2165.0, rho_b=1249.0, label="salt-like, d 425 um, 1 g/s"),
    # design variant: inner cup 60 mm tall, rim 5 mm under the lid (baseline: 50 mm, rim 15 mm under)
    "fine1_tall": dict(mdot=1e-3, d=25e-6, rho_p=2330.0, rho_b=770.0,
                       label="Si-325-like, 1 g/s, inner cup 60 mm tall"),
}
Z_OUT = 0.093
Z_FLOOR = 0.016
R_CUP, Z_RIM = 0.020, 0.065
R_INLET, Z_LID0, Z_LID1 = 0.010, 0.080, 0.083
R_CAN = 0.035


def geometry(h):
    Lr, Lz = 0.060, 0.123
    nr, nz = int(round(Lr / h)), int(round(Lz / h))
    rc = (np.arange(nr) + 0.5) * h
    zc = (np.arange(nz) + 0.5) * h
    R, Z = np.meshgrid(rc, zc, indexing="ij")
    lab = np.zeros((nr, nz), np.int8)            # 0 fluid, 1 inner cup, 2 can / lid / outside
    lab[(R > R_CAN) & (Z < Z_LID1)] = 2
    lab[(R > R_INLET) & (Z > Z_LID0) & (Z < Z_LID1)] = 2
    lab[(R > R_CUP) & (R < R_CUP + 0.001) & (Z > 0.015) & (Z < Z_RIM)] = 1
    lab[(R < R_CUP + 0.001) & (Z > 0.015) & (Z < Z_FLOOR)] = 1
    return nr, nz, Lr, Lz, R, Z, lab


def run_flow(case, h=0.0005, t_end=2.0, tag=""):
    p = CASES[case]
    if h < 0.0006:
        t_end = min(t_end, 1.0)    # grid check: the inflow settles in 0.3 s; average over 0.75-1 s
    nr, nz, Lr, Lz, R, Z, lab = geometry(h)
    s = MAC2D(nr, nz, Lr, Lz, nu=NU, axisym=True, top="open", upwind="hybrid")
    s.solid = lab > 0
    s._masks()
    s._poisson()
    st = sm.stream(p["mdot"], p["d"], p["rho_p"], p["rho_b"], s_end=Z_OUT - Z_FLOOR + 1e-4)
    # grain speed and drag rate on v faces inside the stream
    zf = s.yf
    sdist = Z_OUT - zf
    # the stream's drag stops 1.5 mm (one stream radius) above the floor: below that the air turns in
    # the stagnation layer over the heap; forcing it down to the wall would push air into the floor
    inside = (sdist > 0) & (zf > Z_FLOOR + sm.B_OUT)
    vp = np.interp(np.clip(sdist, 0, None), st["s"], st["v"])
    tp = sm.tau_p(p["d"], p["rho_p"])
    f = sm.drag_factor(vp - np.interp(np.clip(sdist, 0, None), st["s"], st["u"]), p["d"])
    c = p["mdot"] * f / (vp * np.pi * sm.B_OUT ** 2 * sm.RHO_A * tp)
    cv = np.zeros_like(s.v)
    vt = np.zeros_like(s.v)
    # area fraction of each cell column inside the stream radius, so the momentum source is the
    # same on every grid (a cell that straddles r = 1.5 mm gets its share)
    r_in, r_out = s.xf[:-1], s.xf[1:]
    wfrac = np.clip((np.minimum(r_out, sm.B_OUT) ** 2 - r_in ** 2) / (r_out ** 2 - r_in ** 2), 0.0, 1.0)
    for i in np.nonzero(wfrac > 0)[0]:
        cv[i, :] = np.where(inside, c * wfrac[i], 0.0)
        vt[i, :] = np.where(inside, -vp, 0.0)
    s.cv, s.v_target = cv, vt
    umax = 1.3 * float(vp[inside].max())
    dt = 0.3 * h / umax
    nsteps = int(t_end / dt)
    t0 = time.time()
    hist = []
    j_in = int(round(Z_LID0 / h))          # plane z = 80 mm (bottom of the lid)
    j_rim = int(round(Z_RIM / h))
    ua = np.zeros_like(s.u)
    va = np.zeros_like(s.v)
    na = 0
    for n in range(nsteps):
        s.step(dt)
        if n % 2000 == 0 or n == nsteps - 1:
            vin = s.v[:, j_in]
            area = 2 * np.pi * s.xc * h
            q_down = float(-np.sum(np.minimum(vin, 0) * area))
            vr = s.v[:, j_rim]
            q_rim_up = float(np.sum(np.maximum(vr, 0) * area * (s.xc < R_CUP)))
            hist.append((n * dt, q_down, q_rim_up))
            print(f"  t = {n*dt:.3f} s  Q down through inlet = {q_down*1e6:.2f} mL/s  up through cup mouth = "
                  f"{q_rim_up*1e6:.2f} mL/s  wall {time.time()-t0:.0f} s", flush=True)
        if n * dt > 0.75 * t_end:
            ua += s.u
            va += s.v
            na += 1
    s.u, s.v = ua / na, va / na
    np.savez_compressed(f"faraday_flow_{case}{tag}.npz", u=s.u, v=s.v, lab=lab, h=h, Lr=Lr, Lz=Lz,
                        s=st["s"], vp=st["v"], ua=st["u"])
    # return-flow speeds
    uc, vc = s.cell_velocity()
    up_cup = vc[(R < R_CUP) & (R > 0.010) & (Z > 0.030) & (Z < 0.060) & (lab == 0)]
    out = dict(case=case, params=p, h=h, dt=dt, steps=nsteps, wall_s=time.time() - t0,
               hist=hist, Q_inlet_down_mLs=hist[-1][1] * 1e6, Q_cupmouth_up_mLs=hist[-1][2] * 1e6,
               v_up_mean_in_cup_outer_half=float(np.mean(np.maximum(up_cup, 0))),
               v_up_max_in_cup=float(vc[(R < R_CUP) & (lab == 0) & (Z > 0.02) & (Z < 0.064)].max()),
               v_up_inlet_annulus_max=float(np.max(s.v[(s.xc > 0.002) & (s.xc < R_INLET), j_in])),
               stream_v_at_floor=float(np.interp(Z_OUT - Z_FLOOR, st["s"], st["v"])),
               stream_v_at_inlet=float(np.interp(Z_OUT - Z_LID1, st["s"], st["v"])),
               stream_Q_free_plume_at_floor_mLs=float(np.interp(Z_OUT - Z_FLOOR, st["s"], st["Q"]) * 1e6))
    json.dump(out, open(f"faraday_flow_{case}{tag}.json", "w"), indent=1)
    print({k: v for k, v in out.items() if k not in ("hist", "params")}, flush=True)
    return out


# ------------------------------------------------------------------ tracking
class Field:
    def __init__(self, case):
        d = np.load(f"faraday_flow_{case}.npz")       # case may carry a grid tag, e.g. salt1_h1.00
        self.u, self.v, self.lab = d["u"], d["v"], d["lab"]
        self.h = float(d["h"])
        self.nr, self.nz = self.lab.shape

    def vel(self, r, z):
        h = self.h
        # u at (i h, (j+.5) h)
        x = np.clip(r / h, 0, self.nr - 1e-6)
        y = np.clip(z / h - 0.5, 0, self.nz - 1 - 1e-6)
        i, j = x.astype(int), y.astype(int)
        fx, fy = x - i, y - j
        u = self.u
        ur = (u[i, j] * (1 - fx) * (1 - fy) + u[np.minimum(i + 1, self.nr), j] * fx * (1 - fy)
              + u[i, np.minimum(j + 1, self.nz - 1)] * (1 - fx) * fy
              + u[np.minimum(i + 1, self.nr), np.minimum(j + 1, self.nz - 1)] * fx * fy)
        x = np.clip(r / h - 0.5, 0, self.nr - 1 - 1e-6)
        y = np.clip(z / h, 0, self.nz - 1e-6)
        i, j = x.astype(int), y.astype(int)
        fx, fy = x - i, y - j
        v = self.v
        uz = (v[i, j] * (1 - fx) * (1 - fy) + v[np.minimum(i + 1, self.nr - 1), j] * fx * (1 - fy)
              + v[i, np.minimum(j + 1, self.nz)] * (1 - fx) * fy
              + v[np.minimum(i + 1, self.nr - 1), np.minimum(j + 1, self.nz)] * fx * fy)
        return ur, uz

    def label(self, r, z):
        i = np.clip((r / self.h).astype(int), 0, self.nr - 1)
        j = np.clip((z / self.h).astype(int), 0, self.nz - 1)
        return self.lab[i, j]


def track(F, r0, z0, vr0, vz0, d, rho_p, t_max=6.0, dt=4e-4):
    """Vectorised grain tracking in the meridional plane. Outcome codes:
    0 airborne inside the inner cup at t_max, 1 touched the inner cup (inside or outside: both its
    charge and its mass are counted), 2 touched the can, lid or can floor, 3 left through the lid
    inlet, 4 airborne outside the inner cup at t_max. Captured = 0 or 1."""
    r, z, vr, vz = r0.copy(), z0.copy(), vr0.copy(), vz0.copy()
    n = r.size
    tp = sm.tau_p(d, rho_p)
    state = np.full(n, -1)
    t = 0.0
    dt_max = dt
    while t < t_max and np.any(state < 0):
        a = state < 0
        # adaptive step: no grain moves more than 0.15 cell per step (avoids stepping into walls)
        vmax = float(np.max(np.hypot(vr[a], vz[a]))) + 1e-9
        dt = min(dt_max, 0.15 * F.h / vmax)
        ur, uz = F.vel(r[a], z[a])
        rel = np.hypot(vr[a] - ur, vz[a] - uz)
        te = tp[a] / sm.drag_factor(rel, d[a])
        e = np.exp(-dt / te)
        vr_new = ur + (vr[a] - ur) * e
        vz_new = (uz - sm.G * te) + (vz[a] - (uz - sm.G * te)) * e
        r_new = np.abs(r[a] + 0.5 * (vr[a] + vr_new) * dt)
        z_new = z[a] + 0.5 * (vz[a] + vz_new) * dt
        vr[a], vz[a], r[a], z[a] = vr_new, vz_new, r_new, z_new
        idx = np.nonzero(a)[0]
        out_top = z[idx] > Z_LID1 + 0.002
        lab = F.label(r[idx], z[idx])
        hit1 = lab == 1
        hit2 = (lab == 2) | (z[idx] < 0.0005)
        state[idx[out_top]] = 3
        state[idx[hit1 & ~out_top]] = 1
        state[idx[hit2 & ~out_top & ~hit1]] = 2
        t += dt
    rem = state < 0
    inside = (r < R_CUP) & (z > Z_FLOOR) & (z < Z_RIM)
    state[rem & inside] = 0
    state[rem & ~inside] = 4
    return state


def run_track(case, n_per=120, seed=1, tag=""):
    F = Field(case + tag)
    p = CASES[case]
    st = sm.stream(p["mdot"], p["d"], p["rho_p"], p["rho_b"], s_end=Z_OUT - Z_FLOOR + 1e-4)
    v_in = float(np.interp(Z_OUT - Z_LID1, st["s"], st["v"]))
    rng = np.random.default_rng(seed)
    sizes = np.array([5, 7, 10, 14, 20, 30, 50, 70, 100]) * 1e-6
    out = dict(case=case, sizes_um=(sizes * 1e6).tolist(), stream_speed_at_inlet=v_in, results={})
    for rho in (1450.0, 2165.0, 3100.0):
        for inj in ("stream", "edge", "splash"):
            d = np.repeat(sizes, n_per)
            rp = np.full(d.size, rho)
            if inj == "stream":
                r0 = sm.B_OUT * np.sqrt(rng.random(d.size))
                z0 = np.full(d.size, Z_LID1)
                vr0 = np.zeros(d.size)
                vz0 = np.full(d.size, -v_in)
            elif inj == "edge":
                # dust shed at the stream's edge as it enters (r 1.5-4 mm), moving with the local air
                r0 = np.sqrt(sm.B_OUT ** 2 + (0.004 ** 2 - sm.B_OUT ** 2) * rng.random(d.size))
                z0 = np.full(d.size, Z_LID1)
                vr0, vz0 = F.vel(r0, z0)
            else:
                r0 = 0.003 * np.sqrt(rng.random(d.size))
                z0 = np.full(d.size, Z_FLOOR + 0.0015)
                sp_ = rng.uniform(0.1, 0.5, d.size)
                ang = np.radians(rng.uniform(10, 80, d.size))
                vr0 = sp_ * np.cos(ang)
                vz0 = sp_ * np.sin(ang)
            t0 = time.time()
            stt = track(F, r0, z0, vr0, vz0, d, rp)
            res = {}
            for k, dd in enumerate(sizes):
                m = slice(k * n_per, (k + 1) * n_per)
                s_ = stt[m]
                tau = sm.tau_p(dd, rho)
                res[f"{dd*1e6:.0f}"] = dict(
                    stokes_jet=float(tau * v_in / sm.B_OUT),
                    settling_mm_s=float(rho * dd ** 2 * sm.G / (18 * sm.MU) * 1e3),
                    captured=float(np.mean((s_ == 0) | (s_ == 1))),
                    hit_cup=float(np.mean(s_ == 1)), airborne_in_cup=float(np.mean(s_ == 0)),
                    on_can_or_lid=float(np.mean(s_ == 2)), airborne_outside=float(np.mean(s_ == 4)),
                    out_of_lid=float(np.mean(s_ == 3)))
            out["results"][f"rho{rho:.0f}_{inj}"] = res
            print(case, rho, inj, f"{time.time()-t0:.0f} s",
                  {k: round(v["captured"], 3) for k, v in res.items()}, flush=True)
    out["grid_tag"] = tag
    json.dump(out, open(f"faraday_track_{case}{tag}.json", "w"), indent=1)
    return out


if __name__ == "__main__":
    mode, case = sys.argv[1], sys.argv[2]
    if case.endswith("_tall"):
        Z_RIM = 0.075
    if mode == "flow":
        hmm = float(sys.argv[3]) if len(sys.argv) > 3 else 0.75
        tag = "" if abs(hmm - 0.75) < 1e-9 else f"_h{hmm:.2f}"
        run_flow(case, h=hmm * 1e-3, tag=tag)
    else:
        hmm = float(sys.argv[3]) if len(sys.argv) > 3 else 0.75
        tag = "" if abs(hmm - 0.75) < 1e-9 else f"_h{hmm:.2f}"
        run_track(case, tag=tag)
