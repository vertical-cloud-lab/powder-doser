#!/usr/bin/env python3
"""2D MLS-MPM (Hu et al. 2018) with Drucker-Prager elastoplasticity in Hencky strain
(Klar et al. 2016), Taichi on CPU, 1 thread.
Cases: (a) granular column collapse, phi=34 deg, c=0 and c>0 (apex-shifted cone);
       (b) flat-bottomed silo discharge through a slot, 3 widths -> W vs D, Beverloo fit.
Outputs raw data (npz) to /tmp/sims-scratch/mpm-taichi and result.json/figure via plots in this script."""
import os, sys, json, time
import numpy as np
import taichi as ti

OUT = os.path.dirname(os.path.abspath(__file__))
SCR = "/tmp/sims-scratch/mpm-taichi"
os.makedirs(SCR, exist_ok=True)
ti.init(arch=ti.cpu, cpu_max_num_threads=1, default_fp=ti.f32, random_seed=1)

# ---------------- parameters (SI units, 2D plane strain, per metre depth) ----------------
L = 0.2; n_grid = int(os.environ.get("MPM_NGRID", 128)); dx = L / n_grid; inv_dx = 1.0 / dx
rho_b = 1250.0            # bulk density of salt bed, kg/m^3 (assumed; measured 1200-1300)
E, nu = 3.0e5, 0.3        # deliberately soft (rigid limit: rho g h/E < 0.4 %)
mu0 = E / (2 * (1 + nu)); lam0 = E * nu / ((1 + nu) * (1 - 2 * nu))
grav = 9.81
p_vol = (dx * 0.5) ** 2   # 2x2 particles per cell
p_mass = rho_b * p_vol
cwave = np.sqrt((lam0 + 2 * mu0) / rho_b)
DT = 0.35 * dx / cwave
max_p = int(os.environ.get("MPM_MAXP", 30000))

x = ti.Vector.field(2, ti.f32, max_p); v = ti.Vector.field(2, ti.f32, max_p)
C = ti.Matrix.field(2, 2, ti.f32, max_p); F = ti.Matrix.field(2, 2, ti.f32, max_p)
active = ti.field(ti.i32, max_p); passed = ti.field(ti.i32, max_p)
grid_v = ti.Vector.field(2, ti.f32, (n_grid, n_grid)); grid_m = ti.field(ti.f32, (n_grid, n_grid))
n_p = ti.field(ti.i32, ()); alpha = ti.field(ti.f32, ()); tr0 = ti.field(ti.f32, ())
case = ti.field(ti.i32, ())    # 0 column, 1 silo
floor_y = ti.field(ti.f32, ()); xl = ti.field(ti.f32, ()); xr = ti.field(ti.f32, ())
halfD = ti.field(ti.f32, ()); is_open = ti.field(ti.i32, ())
mu = ti.static(mu0); lam = ti.static(lam0); dt = ti.static(DT)

@ti.func
def dp_project(s0, s1):
    e0 = ti.log(ti.max(ti.abs(s0), 1e-4)); e1 = ti.log(ti.max(ti.abs(s1), 1e-4))
    tr = e0 + e1
    h0 = e0 - 0.5 * tr; h1 = e1 - 0.5 * tr
    hn = ti.sqrt(h0 * h0 + h1 * h1)
    trp = tr - tr0[None]
    r0 = e0; r1 = e1
    if trp >= 0.0:                      # beyond apex: project to apex (tension cut-off)
        r0 = 0.5 * tr0[None]; r1 = 0.5 * tr0[None]
    else:
        dg = hn + (2.0 * lam + 2.0 * mu) / (2.0 * mu) * trp * alpha[None]
        if dg > 0.0 and hn > 1e-10:     # radial return in deviatoric plane, no dilatancy
            r0 = e0 - dg * h0 / hn; r1 = e1 - dg * h1 / hn
    return r0, r1

@ti.kernel
def substep():
    for i, j in grid_m:
        grid_v[i, j] = [0, 0]; grid_m[i, j] = 0
    for p in range(n_p[None]):
        if active[p] == 1:
            Xp = x[p] * inv_dx
            base = int(Xp - 0.5); fx = Xp - base
            w = [0.5 * (1.5 - fx) ** 2, 0.75 - (fx - 1) ** 2, 0.5 * (fx - 0.5) ** 2]
            Fp = (ti.Matrix.identity(ti.f32, 2) + dt * C[p]) @ F[p]
            U, sig, V = ti.svd(Fp)
            r0, r1 = dp_project(sig[0, 0], sig[1, 1])
            F[p] = U @ ti.Matrix([[ti.exp(r0), 0.0], [0.0, ti.exp(r1)]]) @ V.transpose()
            trr = r0 + r1
            tau = U @ ti.Matrix([[2 * mu * r0 + lam * trr, 0.0], [0.0, 2 * mu * r1 + lam * trr]]) @ U.transpose()
            affine = (-dt * p_vol * 4 * inv_dx * inv_dx) * tau + p_mass * C[p]
            for a, b in ti.static(ti.ndrange(3, 3)):
                off = ti.Vector([a, b]); dpos = (off.cast(float) - fx) * dx
                wt = w[a][0] * w[b][1]
                grid_v[base + off] += wt * (p_mass * v[p] + affine @ dpos)
                grid_m[base + off] += wt * p_mass
    for i, j in grid_m:
        if grid_m[i, j] > 0:
            vg = grid_v[i, j] / grid_m[i, j]
            vg[1] -= dt * grav
            xi = i * dx; yj = j * dx
            if i < 3 and vg[0] < 0: vg[0] = 0
            if i > n_grid - 3 and vg[0] > 0: vg[0] = 0
            if j > n_grid - 3 and vg[1] > 0: vg[1] = 0
            if j < 3: vg = [0.0, 0.0]                       # rough (no-slip) floor
            if case[None] == 1:
                if yj > floor_y[None] - 1.5 * dx and (xi < xl[None] or xi > xr[None]):
                    vg = [0.0, 0.0]                         # rough silo walls
                if ti.abs(yj - floor_y[None]) < 1.01 * dx:
                    if is_open[None] == 0 or ti.abs(xi - 0.5 * (xl[None] + xr[None])) > halfD[None]:
                        vg = [0.0, 0.0]                     # rough silo floor outside slot
            grid_v[i, j] = vg
    for p in range(n_p[None]):
        if active[p] == 1:
            Xp = x[p] * inv_dx
            base = int(Xp - 0.5); fx = Xp - base
            w = [0.5 * (1.5 - fx) ** 2, 0.75 - (fx - 1) ** 2, 0.5 * (fx - 0.5) ** 2]
            nv = ti.Vector.zero(ti.f32, 2); nC = ti.Matrix.zero(ti.f32, 2, 2)
            for a, b in ti.static(ti.ndrange(3, 3)):
                off = ti.Vector([a, b]); dpos = off.cast(float) - fx
                gv = grid_v[base + off]; wt = w[a][0] * w[b][1]
                nv += wt * gv; nC += 4 * inv_dx * wt * gv.outer_product(dpos)
            v[p] = nv; C[p] = nC; x[p] += dt * nv
            if case[None] == 1:
                if x[p][1] < floor_y[None] - 3 * dx: passed[p] = 1
                if x[p][1] < 6 * dx: active[p] = 0
            x[p] = ti.max(ti.min(x[p], L - 2.01 * dx), 2.01 * dx)

def seed_block(x0, y0, w, h):
    nx = int(round(w / (dx / 2))); ny = int(round(h / (dx / 2)))
    xs = x0 + (np.arange(nx) + 0.5) * dx / 2; ys = y0 + (np.arange(ny) + 0.5) * dx / 2
    X, Y = np.meshgrid(xs, ys, indexing="ij")
    P = np.stack([X.ravel(), Y.ravel()], 1).astype(np.float32)
    P += (np.random.default_rng(0).random(P.shape).astype(np.float32) - 0.5) * 0.1 * dx
    return P

def load(P):
    n = len(P); assert n <= max_p
    xn = np.zeros((max_p, 2), np.float32); xn[:n] = P
    x.from_numpy(xn); v.from_numpy(np.zeros((max_p, 2), np.float32))
    C.from_numpy(np.zeros((max_p, 2, 2), np.float32))
    F.from_numpy(np.tile(np.eye(2, dtype=np.float32), (max_p, 1, 1)))
    act = np.zeros(max_p, np.int32); act[:n] = 1; active.from_numpy(act)
    passed.from_numpy(np.zeros(max_p, np.int32)); n_p[None] = n
    return n

def set_material(phi_deg, coh):
    s = np.sin(np.radians(phi_deg))
    alpha[None] = np.sqrt(2.0 / 3.0) * 2 * s / (3 - s)
    # apex at tensile mean stress c*cot(phi): (lam+mu)*tr0 = c cot(phi)  (2D)
    tr0[None] = coh / np.tan(np.radians(phi_deg)) / (lam0 + mu0)

def run_column(phi, coh, a0=0.04, h0=0.08, t_end=0.45, nframes=60, tag=""):
    case[None] = 0; set_material(phi, coh)
    P = seed_block(3 * dx, 3 * dx, a0, h0); n = load(P)
    nsteps = int(t_end / DT); every = max(1, nsteps // nframes)
    frames = []; t0 = time.time()
    for s in range(nsteps):
        substep()
        if s % every == 0:
            frames.append((s * DT, x.to_numpy()[:n].copy(), np.linalg.norm(v.to_numpy()[:n], axis=1)))
    X = x.to_numpy()[:n]; V = np.linalg.norm(v.to_numpy()[:n], axis=1)
    wall = time.time() - t0
    # deposit geometry (measured from wall at x=3dx and floor at y=3dx)
    xs = X[:, 0] - 3 * dx; ys = X[:, 1] - 3 * dx
    bins = np.arange(0, L, dx); idx = np.digitize(xs, bins)
    hx = np.array([ys[idx == k].max() if np.any(idx == k) else 0.0 for k in range(1, len(bins))])
    xc = bins[:-1] + dx / 2
    thick = hx > 1.0 * dx
    Linf = xc[thick].max() + dx / 2; Hinf = hx[:3].mean()
    m = (hx > 0.2 * Hinf) & (hx < 0.8 * Hinf) & thick
    slope = -np.polyfit(xc[m], hx[m], 1)[0] if m.sum() > 3 else np.nan
    res = dict(phi_deg=phi, cohesion_Pa=coh, a0_m=a0, h0_m=h0, aspect=h0 / a0, t_end_s=t_end,
               n_particles=int(n), steps=int(nsteps), wall_s=round(wall, 1),
               runout_Linf_m=float(Linf), final_height_Hinf_m=float(Hinf),
               runout_ratio=(float(Linf) - a0) / a0, height_ratio=float(Hinf) / h0,
               mean_slope_deg=float(np.degrees(np.arctan(Hinf / Linf))),
               fitted_mid_slope_deg=float(np.degrees(np.arctan(slope))),
               max_speed_end_mps=float(V.max()))
    np.savez_compressed(f"{SCR}/column_{tag}.npz", X=X, xc=xc, hx=hx,
                        ft=np.array([f[0] for f in frames]))
    return res, frames, (xc, hx)

def run_silo(D, phi=34.0, coh=0.0, W=0.08, H=0.08, t_settle=0.05, t_dis=0.25, nframes=60, tag=""):
    case[None] = 1; set_material(phi, coh)
    floor_y[None] = 0.07; xl[None] = 0.1 - W / 2; xr[None] = 0.1 + W / 2; halfD[None] = D / 2
    is_open[None] = 0
    P = seed_block(0.1 - W / 2 + dx, 0.07 + dx, W - 2 * dx, H); n = load(P)
    nsteps = int((t_settle + t_dis) / DT); every = max(1, nsteps // nframes)
    ts, ms, frames = [], [], []; t0 = time.time()
    for s in range(nsteps):
        t = s * DT
        if t >= t_settle: is_open[None] = 1
        substep()
        if s % 20 == 0:
            ts.append(t - t_settle); ms.append(passed.to_numpy()[:n].sum() * p_mass)
        if s % every == 0:
            act = active.to_numpy()[:n] == 1
            Xn = x.to_numpy()[:n]
            frames.append((t - t_settle, Xn[act].copy(), np.linalg.norm(v.to_numpy()[:n][act], axis=1)))
    wall = time.time() - t0
    ts = np.array(ts); ms = np.array(ms)
    sel = (ts > 0.08) & (ts < t_dis)
    Wrate = np.polyfit(ts[sel], ms[sel], 1)[0] if sel.sum() > 5 else np.nan
    np.savez_compressed(f"{SCR}/silo_{tag}.npz", t=ts, m=ms)
    return dict(D_m=D, D_over_dx=D / dx, n_particles=int(n), wall_s=round(wall, 1),
                W_kg_per_m_s=float(Wrate), discharged_kg_per_m=float(ms[-1])), frames, (ts, ms)

if __name__ == "__main__" and len(sys.argv) > 2 and sys.argv[1] == "silo":
    # resolution check: e.g. MPM_NGRID=256 MPM_MAXP=45000 python run.py silo 0.012
    T0 = time.time(); out = []
    for D in [float(a) for a in sys.argv[2:]]:
        r, fr, cur = run_silo(D, tag=f"D{int(D*1e3)}_n{n_grid}"); r["n_grid"] = n_grid; out.append(r)
        print("silo", r, flush=True)
    json.dump(out, open(f"{SCR}/raw_results_silo_n{n_grid}.json", "w"), indent=1)
    print("DONE", round(time.time() - T0, 1)); sys.exit(0)

if __name__ == "__main__":
    T0 = time.time()
    print(f"dx={dx*1e3:.3f} mm, dt={DT:.3e} s, c={cwave:.1f} m/s", flush=True)
    results = {"columns": [], "silo": []}
    col_frames, col_prof, silo_frames, silo_curves = {}, {}, {}, {}
    for coh, tag in [(0.0, "c0"), (100.0, "c100")]:
        r, fr, prof = run_column(34.0, coh, tag=tag)
        results["columns"].append(r); col_frames[tag] = fr; col_prof[tag] = prof
        print("column", tag, r, flush=True)
    for D in [0.008, 0.012, 0.016]:
        tag = f"D{int(D*1e3)}"
        r, fr, cur = run_silo(D, tag=tag)
        results["silo"].append(r); silo_frames[tag] = fr; silo_curves[tag] = cur
        print("silo", tag, r, flush=True)
    # Beverloo plane-flow fit: W = Cb rho sqrt(g) (D - D0)^1.5, Cb and D0 free
    from scipy.optimize import curve_fit
    Ds = np.array([r["D_m"] for r in results["silo"]]); Ws = np.array([r["W_kg_per_m_s"] for r in results["silo"]])
    f = lambda D, Cb, D0: Cb * rho_b * np.sqrt(grav) * np.clip(D - D0, 1e-9, None) ** 1.5
    (Cb, D0), _ = curve_fit(f, Ds, Ws, p0=[1.0, 0.002])
    pexp = np.polyfit(np.log(Ds), np.log(Ws), 1)[0]
    results["beverloo_fit"] = dict(C=float(Cb), D0_m=float(D0), D0_over_dx=float(D0 / dx),
                                   loglog_exponent_no_offset=float(pexp),
                                   residuals_rel=[float(a) for a in (Ws - f(Ds, Cb, D0)) / Ws])
    results["params"] = dict(dx_m=dx, dt_s=DT, rho_bulk=rho_b, E_Pa=E, nu=nu, phi_deg=34.0,
                             grid=n_grid, ppc=4)
    results["total_wall_s"] = round(time.time() - T0, 1)
    json.dump(results, open(f"{SCR}/raw_results.json", "w"), indent=1)
    import pickle
    pickle.dump(dict(col_frames=col_frames, col_prof=col_prof, silo_frames=silo_frames,
                     silo_curves=silo_curves), open(f"{SCR}/frames.pkl", "wb"))
    print("DONE", results["beverloo_fit"], results["total_wall_s"], flush=True)
