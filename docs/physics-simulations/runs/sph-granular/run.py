#!/usr/bin/env python3
"""Compact 2D elastic-perfectly-plastic SPH for granular column collapse (after Bui et al. 2008,
Int. J. Numer. Anal. Meth. Geomech. 32:1537): Drucker-Prager fitted to Mohr-Coulomb in plane strain,
Jaumann stress rate, stress-scaling return + tension cut-off, Monaghan artificial viscosity,
continuity density, Wendland C2 kernel, fixed wall particles with Adami-type stress extrapolation.
numba, 1 thread. Writes raw output to /tmp/sims-scratch/sph-granular."""
import os, json, time, pickle
import numpy as np
from numba import njit

SCR = "/tmp/sims-scratch/sph-granular"; os.makedirs(SCR, exist_ok=True)
rho0 = 1250.0; E = 3.0e5; nu = 0.3; g = 9.81
G = E / (2 * (1 + nu)); K = E / (3 * (1 - 2 * nu))
cp = np.sqrt((K + 4 * G / 3) / rho0); cs = np.sqrt(K / rho0)
dp = 1.0e-3; h = 1.3 * dp; DT = 0.2 * h / cp
A_PI = 0.5   # Monaghan artificial viscosity; 0.1 (Bui et al. 2008 value) blew up at t = 0.02 s here
a0, H0 = 0.04, 0.08

@njit(cache=False)
def Wk(r, h):
    q = r / h
    if q >= 2.0: return 0.0
    return 7.0 / (4.0 * np.pi * h * h) * (1 - 0.5 * q) ** 4 * (2 * q + 1)

@njit(cache=False)
def dWk(r, h):  # dW/dr
    q = r / h
    if q >= 2.0: return 0.0
    return 7.0 / (4.0 * np.pi * h * h) * (-5.0 * q * (1 - 0.5 * q) ** 3) / h

@njit(cache=False)
def cells(x, n, cell, ncx, ncy, x0, y0):
    head = -np.ones(ncx * ncy, np.int64); nxt = -np.ones(n, np.int64)
    for i in range(n):
        cx = min(max(int((x[i, 0] - x0) / cell), 0), ncx - 1)
        cy = min(max(int((x[i, 1] - y0) / cell), 0), ncy - 1)
        c = cx * ncy + cy; nxt[i] = head[c]; head[c] = i
    return head, nxt

@njit(cache=False)
def step(x, v, rho, sig, m, n, ns, h, dt, G, K, aphi, kc, cs, aPi, g, cell, ncx, ncy, x0, y0):
    head, nxt = cells(x, n, cell, ncx, ncy, x0, y0)
    # wall stress: Shepard extrapolation from soil + hydrostatic correction (Adami et al. 2012)
    for i in range(ns, n):
        cx = min(max(int((x[i, 0] - x0) / cell), 0), ncx - 1); cy = min(max(int((x[i, 1] - y0) / cell), 0), ncy - 1)
        sw = 0.0; a0_ = 0.0; a1 = 0.0; a2 = 0.0; a3 = 0.0; gr = 0.0
        for ox in range(-1, 2):
            for oy in range(-1, 2):
                X = cx + ox; Y = cy + oy
                if X < 0 or Y < 0 or X >= ncx or Y >= ncy: continue
                j = head[X * ncy + Y]
                while j >= 0:
                    if j < ns:
                        dx_ = x[i, 0] - x[j, 0]; dy_ = x[i, 1] - x[j, 1]; r = np.sqrt(dx_ * dx_ + dy_ * dy_)
                        if r < 2 * h:
                            w = Wk(r, h); sw += w
                            a0_ += sig[j, 0] * w; a1 += sig[j, 1] * w; a2 += sig[j, 2] * w; a3 += sig[j, 3] * w
                            gr += rho[j] * (-g * dy_) * w
                    j = nxt[j]
        if sw > 1e-12:
            sig[i, 0] = (a0_ - gr) / sw; sig[i, 1] = (a1 - gr) / sw; sig[i, 2] = a2 / sw; sig[i, 3] = (a3 - gr) / sw
        else:
            sig[i, 0] = 0.0; sig[i, 1] = 0.0; sig[i, 2] = 0.0; sig[i, 3] = 0.0
    acc = np.zeros((ns, 2)); Lg = np.zeros((ns, 4)); drho = np.zeros(ns)
    for i in range(ns):
        cx = min(max(int((x[i, 0] - x0) / cell), 0), ncx - 1); cy = min(max(int((x[i, 1] - y0) / cell), 0), ncy - 1)
        ax = 0.0; ay = -g; l00 = 0.0; l01 = 0.0; l10 = 0.0; l11 = 0.0; dr = 0.0
        ri2 = rho[i] * rho[i]
        for ox in range(-1, 2):
            for oy in range(-1, 2):
                X = cx + ox; Y = cy + oy
                if X < 0 or Y < 0 or X >= ncx or Y >= ncy: continue
                j = head[X * ncy + Y]
                while j >= 0:
                    if j != i:
                        dx_ = x[i, 0] - x[j, 0]; dy_ = x[i, 1] - x[j, 1]; r2 = dx_ * dx_ + dy_ * dy_
                        if r2 < 4 * h * h and r2 > 1e-20:
                            r = np.sqrt(r2); f = dWk(r, h) / r; gx = f * dx_; gy = f * dy_
                            vjx = 0.0; vjy = 0.0
                            if j < ns: vjx = v[j, 0]; vjy = v[j, 1]
                            vx = v[i, 0] - vjx; vy = v[i, 1] - vjy
                            Vj = m[j] / rho[j]
                            l00 += Vj * (vjx - v[i, 0]) * gx; l01 += Vj * (vjx - v[i, 0]) * gy
                            l10 += Vj * (vjy - v[i, 1]) * gx; l11 += Vj * (vjy - v[i, 1]) * gy
                            dr += m[j] * (vx * gx + vy * gy)
                            vr = vx * dx_ + vy * dy_; Pi = 0.0
                            if vr < 0:
                                muij = h * vr / (r2 + 0.01 * h * h)
                                Pi = -aPi * cs * muij / (0.5 * (rho[i] + rho[j]))
                            rj2 = rho[j] * rho[j]
                            fxx = sig[i, 0] / ri2 + sig[j, 0] / rj2 - Pi
                            fyy = sig[i, 1] / ri2 + sig[j, 1] / rj2 - Pi
                            fxy = sig[i, 2] / ri2 + sig[j, 2] / rj2
                            ax += m[j] * (fxx * gx + fxy * gy); ay += m[j] * (fxy * gx + fyy * gy)
                    j = nxt[j]
        acc[i, 0] = ax; acc[i, 1] = ay; drho[i] = dr
        Lg[i, 0] = l00; Lg[i, 1] = l01; Lg[i, 2] = l10; Lg[i, 3] = l11
    for i in range(ns):
        v[i, 0] += dt * acc[i, 0]; v[i, 1] += dt * acc[i, 1]
        x[i, 0] += dt * v[i, 0]; x[i, 1] += dt * v[i, 1]
        if x[i, 1] < 0.25 * 1e-3:  # safety: no penetration of the floor
            x[i, 1] = 0.25 * 1e-3; v[i, 1] = max(v[i, 1], 0.0)
        if x[i, 0] < 0.25 * 1e-3:
            x[i, 0] = 0.25 * 1e-3; v[i, 0] = max(v[i, 0], 0.0)
        rho[i] += dt * drho[i]
        exx = Lg[i, 0]; eyy = Lg[i, 3]; exy = 0.5 * (Lg[i, 1] + Lg[i, 2]); wxy = 0.5 * (Lg[i, 1] - Lg[i, 2])
        tr = exx + eyy
        sxx = sig[i, 0]; syy = sig[i, 1]; sxy = sig[i, 2]; szz = sig[i, 3]
        sxx += dt * (2 * sxy * wxy + 2 * G * (exx - tr / 3) + K * tr)
        syy += dt * (-2 * sxy * wxy + 2 * G * (eyy - tr / 3) + K * tr)
        sxy += dt * (wxy * (sig[i, 1] - sig[i, 0]) + 2 * G * exy)
        szz += dt * (2 * G * (-tr / 3) + K * tr)
        I1 = sxx + syy + szz
        if -aphi * I1 + kc < 0:  # tension cracking: shift to apex
            sh = (I1 - kc / aphi) / 3.0
            sxx -= sh; syy -= sh; szz -= sh; I1 = sxx + syy + szz
        pm = I1 / 3.0
        dxx = sxx - pm; dyy = syy - pm; dzz = szz - pm
        J2 = 0.5 * (dxx * dxx + dyy * dyy + dzz * dzz) + sxy * sxy
        sJ = np.sqrt(J2)
        lim = -aphi * I1 + kc
        if sJ > lim and sJ > 1e-12:  # stress scaling back to the DP cone
            rr = lim / sJ
            dxx *= rr; dyy *= rr; dzz *= rr; sxy *= rr
        sig[i, 0] = dxx + pm; sig[i, 1] = dyy + pm; sig[i, 2] = sxy; sig[i, 3] = dzz + pm

def setup(phi_deg):
    nx, ny = int(round(a0 / dp)), int(round(H0 / dp))
    X, Y = np.meshgrid((np.arange(nx) + 0.5) * dp, (np.arange(ny) + 0.5) * dp, indexing="ij")
    soil = np.stack([X.ravel(), Y.ravel()], 1)
    walls = []
    for k in range(3):
        for xx in np.arange(-3 * dp + 0.5 * dp, 0.30, dp): walls.append([xx, -(k + 0.5) * dp])
        for yy in np.arange(0.5 * dp, 0.11, dp): walls.append([-(k + 0.5) * dp, yy])
    walls = np.array(walls)
    x = np.vstack([soil, walls]); n = len(x); ns = len(soil)
    v = np.zeros((n, 2)); rho = np.full(n, rho0); m = np.full(n, rho0 * dp * dp)
    sig = np.zeros((n, 4))
    K0 = 1 - np.sin(np.radians(phi_deg))   # Jaky, geostatic initial stress
    syy = -rho0 * g * (H0 - soil[:, 1])
    sig[:ns, 1] = syy; sig[:ns, 0] = K0 * syy; sig[:ns, 3] = K0 * syy
    return x, v, rho, sig, m, n, ns

def run(phi_deg, coh, t_end=0.45, nframes=60, tag=""):
    tp = np.tan(np.radians(phi_deg)); den = np.sqrt(9 + 12 * tp * tp)
    aphi = tp / den; kc = 3 * coh / den
    if kc == 0: kc = 1e-9
    x, v, rho, sig, m, n, ns = setup(phi_deg)
    cell = 2 * h; x0, y0 = -0.01, -0.01; ncx = int(0.33 / cell) + 1; ncy = int(0.13 / cell) + 1
    nsteps = int(t_end / DT); every = max(1, nsteps // nframes); frames = []
    t0 = time.time()
    for s in range(nsteps):
        step(x, v, rho, sig, m, n, ns, h, DT, G, K, aphi, kc, cs, A_PI, g, cell, ncx, ncy, x0, y0)
        if s % every == 0:
            frames.append((s * DT, x[:ns].copy(), np.hypot(v[:ns, 0], v[:ns, 1])))
            if not np.isfinite(x[:ns]).all():
                raise RuntimeError(f"non-finite positions at step {s}")
    wall = time.time() - t0
    xs, ys = x[:ns, 0], x[:ns, 1]
    bins = np.arange(0, 0.3, dp); idx = np.digitize(xs, bins)
    hx = np.array([ys[idx == k].max() + 0.5 * dp if np.any(idx == k) else 0.0 for k in range(1, len(bins))])
    xc = bins[:-1] + dp / 2
    thick = hx > 1.5 * dp
    Linf = xc[thick].max() + dp / 2; Hinf = hx[:3].mean()
    msk = (hx > 0.2 * Hinf) & (hx < 0.8 * Hinf) & thick
    slope = -np.polyfit(xc[msk], hx[msk], 1)[0] if msk.sum() > 3 else np.nan
    res = dict(phi_deg=phi_deg, cohesion_Pa=coh, n_soil=int(ns), n_wall=int(n - ns), steps=int(nsteps),
               dt_s=DT, wall_s=round(wall, 1), runout_Linf_m=float(Linf), final_height_Hinf_m=float(Hinf),
               runout_ratio=float((Linf - a0) / a0), height_ratio=float(Hinf / H0),
               mean_slope_deg=float(np.degrees(np.arctan(Hinf / Linf))),
               fitted_mid_slope_deg=float(np.degrees(np.arctan(slope))),
               max_speed_end_mps=float(np.hypot(v[:ns, 0], v[:ns, 1]).max()),
               density_ratio_min_max=[float(rho[:ns].min() / rho0), float(rho[:ns].max() / rho0)])
    return res, frames, (xc, hx)

if __name__ == "__main__":
    import sys
    T0 = time.time()
    t_end = float(sys.argv[1]) if len(sys.argv) > 1 else 0.45
    print(f"dp={dp}, h={h}, dt={DT:.3e}, cp={cp:.1f}", flush=True)
    out = {"cases": []}; FR = {}; PR = {}
    for coh, tag in [(0.0, "c0"), (100.0, "c100")]:
        r, fr, pr = run(34.0, coh, t_end=t_end, tag=tag)
        out["cases"].append(r); FR[tag] = fr; PR[tag] = pr
        print(tag, r, flush=True)
    out["params"] = dict(rho0=rho0, E=E, nu=nu, dp=dp, h=h, dt=DT, alpha_Pi=A_PI, kernel="Wendland C2",
                         a0=a0, H0=H0, phi_deg=34.0)
    out["total_wall_s"] = round(time.time() - T0, 1)
    json.dump(out, open(f"{SCR}/raw_results.json", "w"), indent=1)
    pickle.dump(dict(frames=FR, prof=PR), open(f"{SCR}/frames.pkl", "wb"))
    print("DONE", out["total_wall_s"], flush=True)
