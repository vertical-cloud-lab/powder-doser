#!/usr/bin/env python3
"""Local mu(I) rheology and the non-local granular fluidity (NGF) model for steady
flow down a rough inclined plane, plus the thickness dependence of the stopping
angle (h_stop) that only the non-local model captures.

Units: lengths in grain diameters d, time in sqrt(d/g), velocity in sqrt(g d),
stress in rho_s g d.  Glass-bead parameters (d = 0.5 mm) from
Jop, Forterre & Pouliquen (2006) and Henann & Kamrin (2013).

Usage:  OMP_NUM_THREADS=1 NUMBA_NUM_THREADS=1 python run.py
"""
import json
import os
import time

import numpy as np
from numba import njit
from scipy.linalg import solve_banded

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

OUT = os.path.dirname(os.path.abspath(__file__))
T_WALL0 = time.time()

# ---------------------------------------------------------------- parameters
D_GRAIN = 0.5e-3          # m, glass beads of Jop et al. (2006)
GRAV = 9.81               # m/s^2
PHI = 0.6                 # solid fraction (Jop et al. 2006 use 0.6)
MU_S = np.tan(np.radians(20.9))    # 0.3819
MU_2 = np.tan(np.radians(32.76))   # 0.6435
I0 = 0.279
B_NGF = (MU_2 - MU_S) / I0         # 0.9377 = slope of mu(I) at I=0 (Henann & Kamrin 2013)
A_NGF = 0.48                        # non-local amplitude, glass beads (Henann & Kamrin 2013)
BETA_P = 0.136                      # Pouliquen flow-rule slope, glass beads
# Pouliquen h_stop length L implied by I0 via u_mean(Bagnold) = Pouliquen flow rule:
#   I0 = 5 beta d / (2 L sqrt(phi cos theta)), evaluated at theta = 25 deg
L_POU = 5 * BETA_P / (2 * I0 * np.sqrt(PHI * np.cos(np.radians(25.0))))
U_SCALE = np.sqrt(GRAV * D_GRAIN)   # m/s
T_SCALE = np.sqrt(D_GRAIN / GRAV)   # s


def mu_jop(I):
    return MU_S + (MU_2 - MU_S) * I / (I0 + I)


def bagnold_jop(theta_deg, h, z):
    """Analytic steady profile for the local Jop mu(I) law."""
    t = np.tan(np.radians(theta_deg))
    I = I0 * (t - MU_S) / (MU_2 - t)
    c = np.sqrt(PHI * np.cos(np.radians(theta_deg)))
    return (2.0 / 3.0) * I * c * (h ** 1.5 - (h - z) ** 1.5)


def bagnold_linear(theta_deg, h, z):
    """Analytic steady profile for the linearised law mu = mu_s + b I (NGF local limit)."""
    t = np.tan(np.radians(theta_deg))
    I = (t - MU_S) / B_NGF
    c = np.sqrt(PHI * np.cos(np.radians(theta_deg)))
    return (2.0 / 3.0) * I * c * (h ** 1.5 - (h - z) ** 1.5)


# ------------------------------------------------ (a) local mu(I), transient FD
@njit(cache=False)
def _local_transient(sin_t, cos_t, h, N, t_end, mu_s, mu_2, i0, phi, gd_reg, rec_every):
    dz = h / N
    u = np.empty(N + 1)
    for i in range(N + 1):
        u[i] = 1e-3 * i * dz            # tiny initial shear so that gamma_dot > 0
    Pf = np.empty(N)
    for i in range(N):
        Pf[i] = phi * cos_t * (h - (i + 0.5) * dz)
    eta_max = (mu_2 - mu_s) / i0 * np.sqrt(Pf[0])
    dt = 0.2 * phi * dz * dz / eta_max
    nsteps = int(t_end / dt) + 1
    nrec = nsteps // rec_every + 1
    t_hist = np.zeros(nrec)
    us_hist = np.zeros(nrec)
    tau = np.empty(N)
    acc = np.zeros(N + 1)
    k = 0
    max_acc = 0.0
    for n in range(nsteps):
        for i in range(N):
            gd = (u[i + 1] - u[i]) / dz
            I = abs(gd) / np.sqrt(Pf[i])
            mu = mu_s + (mu_2 - mu_s) * I / (i0 + I)
            tau[i] = mu * Pf[i] * gd / np.sqrt(gd * gd + gd_reg * gd_reg)
        max_acc = 0.0
        for i in range(1, N):
            acc[i] = (tau[i] - tau[i - 1]) / dz / phi + sin_t
            if abs(acc[i]) > max_acc:
                max_acc = abs(acc[i])
        acc[N] = -tau[N - 1] / (0.5 * dz) / phi + sin_t
        for i in range(1, N + 1):
            u[i] += dt * acc[i]
        if n % rec_every == 0 and k < nrec:
            t_hist[k] = n * dt
            us_hist[k] = u[N]
            k += 1
    return u, t_hist[:k], us_hist[:k], max_acc, dt


def local_transient(theta_deg, h=20.0, N=100, t_end=1500.0):
    th = np.radians(theta_deg)
    u, th_t, th_us, max_acc, dt = _local_transient(np.sin(th), np.cos(th), h, N, t_end,
                                                    MU_S, MU_2, I0, PHI, 1e-7, 200)
    z = np.linspace(0, h, N + 1)
    return z, u, th_t, th_us, max_acc, dt


# --------------------------------------------- NGF (Kamrin & Henann 2015 dynamic form)
# t0 dg/dt = A^2 d^2 lap(g) - (mu_s - mu) g - b mu sqrt(rho_s d^2 / P) g^2
# cell-centred grid, g = 0 at the rough base (Dirichlet), dg/dz = 0 at the free surface.
def _lap_bands(N, dz, A):
    c = A * A / dz ** 2
    diag = np.full(N, 2 * c)
    diag[0] = 3 * c           # ghost g_-1 = -g_0  (g = 0 on the base face)
    diag[-1] = c              # ghost g_N = g_N-1  (zero flux at free surface)
    off = np.full(N - 1, -c)
    return diag, off           # bands of  -A^2 lap


def ngf_setup(theta_deg, h, N):
    th = np.radians(theta_deg)
    mu = np.tan(th)
    dz = h / N
    zc = (np.arange(N) + 0.5) * dz
    P = PHI * np.cos(th) * (h - zc)
    return mu, dz, zc, P


def ngf_step(g, dt, mu, P, diag_lap, off_lap):
    N = g.size
    ab = np.zeros((3, N))
    ab[0, 1:] = off_lap
    ab[2, :-1] = off_lap
    ab[1, :] = 1.0 / dt + diag_lap + B_NGF * mu * g / np.sqrt(P)
    rhs = g * (1.0 / dt + (mu - MU_S))
    return solve_banded((1, 1), ab, rhs)


def ngf_grows(theta_deg, h, N=120, seed=0):
    """Small-amplitude run of the full dynamic NGF equation: does a fluidity seed grow?"""
    mu, dz, zc, P = ngf_setup(theta_deg, h, N)
    dmu = mu - MU_S
    diag_lap, off_lap = _lap_bands(N, dz, A_NGF)
    rng = np.random.default_rng(seed)
    g = 1e-9 * (np.sin(np.pi * zc / (2 * h)) + 0.5 * rng.random(N))
    dt = 0.2 / max(dmu, 1e-6)
    nst = 600
    norms = []
    for n in range(nst):
        g = ngf_step(g, dt, mu, P, diag_lap, off_lap)
        if n in (50, nst - 1):          # step 50: higher modes have decayed
            norms.append(np.linalg.norm(g))
    return norms[1] > norms[0]


def ngf_hstop_bisect(theta_deg, N=120, n_iter=40):
    lo, hi = 0.2, 400.0
    if ngf_grows(theta_deg, lo, N):
        return lo
    if not ngf_grows(theta_deg, hi, N):
        return np.nan
    for _ in range(n_iter):
        mid = np.sqrt(lo * hi)
        if ngf_grows(theta_deg, mid, N):
            hi = mid
        else:
            lo = mid
    return np.sqrt(lo * hi)


def ngf_steady(theta_deg, h, N=200, max_iter=5000, tol=1e-10):
    """Steady flowing state from the dynamic NGF equation (pseudo-time + Newton polish)."""
    mu, dz, zc, P = ngf_setup(theta_deg, h, N)
    dmu = mu - MU_S
    diag_lap, off_lap = _lap_bands(N, dz, A_NGF)
    g = dmu * np.sqrt(P) / (B_NGF * mu)          # start from the local (Bagnold) fluidity
    dt = 5.0 / dmu
    for it in range(max_iter):
        g_new = ngf_step(g, dt, mu, P, diag_lap, off_lap)
        ch = np.max(np.abs(g_new - g)) / max(np.max(np.abs(g_new)), 1e-300)
        g = g_new
        if ch < tol:
            break
    # Newton polish on F(g) = A^2 lap g + dmu g - b mu g^2/sqrt(P) = 0
    for _ in range(20):
        lapg = np.zeros(N)
        lapg[:] = -diag_lap * g
        lapg[:-1] -= off_lap * g[1:]
        lapg[1:] -= off_lap * g[:-1]
        F = lapg + dmu * g - B_NGF * mu * g ** 2 / np.sqrt(P)
        ab = np.zeros((3, N))
        ab[0, 1:] = -off_lap
        ab[2, :-1] = -off_lap
        ab[1, :] = -diag_lap + dmu - 2 * B_NGF * mu * g / np.sqrt(P)
        dg = solve_banded((1, 1), ab, -F)
        g = np.maximum(g + dg, 0.0)
        if np.max(np.abs(dg)) < 1e-14 * max(np.max(g), 1e-300):
            break
    gd = mu * g                                   # gamma_dot = mu g
    # velocity at faces by integrating gamma_dot from the no-slip base
    u_faces = np.concatenate([[0.0], np.cumsum(gd * dz)])
    z_faces = np.linspace(0, h, N + 1)
    u_mean = np.trapezoid(u_faces, z_faces) / h
    return z_faces, u_faces, u_mean, it, float(np.max(g))


def hstop_ngf_analytic(theta_deg, top="neumann"):
    dmu = np.tan(np.radians(theta_deg)) - MU_S
    k = 0.5 if top == "neumann" else 1.0
    return np.where(dmu > 0, k * np.pi * A_NGF / np.sqrt(np.maximum(dmu, 1e-300)), np.inf)


def hstop_pouliquen(theta_deg, tan1=MU_S, tan2=MU_2, L=L_POU):
    t = np.tan(np.radians(theta_deg))
    return np.where((t > tan1) & (t < tan2), L * (tan2 - t) / np.maximum(t - tan1, 1e-300), np.nan)


# ====================================================================== runs
results = {}
timings = {}

# (a) local mu(I) transient -> steady, vs Bagnold
t1 = time.time()
tilts_a = [22.0, 24.0, 26.0, 28.0]
H_A = 20.0
loc = {}
for th in tilts_a:
    z, u, tt, us, max_acc, dt = local_transient(th, H_A, N=100, t_end=4000.0)
    ub = bagnold_jop(th, H_A, z)
    err = np.sqrt(np.mean((u - ub) ** 2)) / ub[-1]
    i95 = np.argmax(us >= 0.95 * us[-1])
    loc[th] = dict(z=z, u=u, ub=ub, t=tt, us=us)
    results.setdefault("local_muI", {})[f"{th:.0f}deg"] = {
        "u_surface_numerical_sqrt_gd": float(u[-1]),
        "u_surface_bagnold_sqrt_gd": float(ub[-1]),
        "u_surface_numerical_m_per_s": float(u[-1] * U_SCALE),
        "rms_error_rel_to_surface_velocity": float(err),
        "residual_max_accel_g": float(max_acc),
        "t95_startup_s": float(tt[i95] * T_SCALE),
        "dt_dimensionless": float(dt),
    }
timings["local_transient_s"] = time.time() - t1
print("local done", timings, flush=True)

# (b) NGF h_stop by bisection on small-amplitude runs of the dynamic model
t1 = time.time()
thetas_b = np.array([20.95, 21.0, 21.2, 21.5, 22.0, 23.0, 24.0, 25.0, 26.0, 28.0, 30.0, 32.0])
hstop_sim = np.array([ngf_hstop_bisect(th) for th in thetas_b])
hstop_an = hstop_ngf_analytic(thetas_b)
timings["ngf_hstop_bisection_s"] = time.time() - t1
print("hstop done", timings, flush=True)
# grid check at 24 deg
hs_N60 = ngf_hstop_bisect(24.0, N=60)
hs_N480 = ngf_hstop_bisect(24.0, N=480)

# finite-amplitude check: start from a flowing (Bagnold) state, does the layer stop?
t1 = time.time()
phase = []
for th in [21.5, 22.0, 24.0, 26.0, 28.0]:
    hs = float(hstop_ngf_analytic(th))
    for fac in [0.6, 0.85, 1.15, 1.6]:
        h = fac * hs
        _, _, um, it, gmax = ngf_steady(th, h, N=160)
        phase.append((th, h, gmax))
timings["ngf_phase_check_s"] = time.time() - t1

# (c) NGF steady profiles vs thickness at 24 deg
t1 = time.time()
TH_PROF = 24.0
prof = {}
for h in [4.0, 6.0, 10.0, 20.0, 40.0]:
    zf, uf, um, it, gmax = ngf_steady(TH_PROF, h, N=200)
    prof[h] = (zf, uf, um, it)
# NGF vs Jop/linear Bagnold at H_A for the (a) tilts
ngf_a = {}
for th in tilts_a:
    zf, uf, um, it, gmax = ngf_steady(th, H_A, N=200)
    ngf_a[th] = (zf, uf)
    results.setdefault("ngf_h20", {})[f"{th:.0f}deg"] = {
        "u_surface_ngf_sqrt_gd": float(uf[-1]),
        "u_surface_linear_bagnold_sqrt_gd": float(bagnold_linear(th, H_A, H_A)),
        "ratio_ngf_to_linear_bagnold": float(uf[-1] / bagnold_linear(th, H_A, H_A)),
    }
# thick-layer convergence of NGF to its local limit
zf, uf, um, it, gmax = ngf_steady(24.0, 200.0, N=400)
thick_ratio = uf[-1] / bagnold_linear(24.0, 200.0, 200.0)

# (d) flow rule Fr = u_mean / sqrt(g h) vs h / h_stop
flow = []
for th in [21.5, 22.0, 23.0, 24.0, 26.0, 28.0]:
    hs = float(hstop_ngf_analytic(th))
    for fac in [1.2, 1.5, 2.0, 3.0, 5.0, 8.0, 12.0]:
        h = fac * hs
        zf, uf, um, it, gmax = ngf_steady(th, h, N=200)
        flow.append((th, h, hs, um / np.sqrt(h)))
flow = np.array(flow)
timings["ngf_profiles_flowrule_s"] = time.time() - t1
# linear fit Fr = beta h/hstop + c over the points
xfit = flow[:, 1] / flow[:, 2]
yfit = flow[:, 3]
beta_fit, c_fit = np.polyfit(xfit, yfit, 1)
resid = yfit - (beta_fit * xfit + c_fit)
r2 = 1 - np.sum(resid ** 2) / np.sum((yfit - yfit.mean()) ** 2)
print("flow rule done", timings, flush=True)

# salt-like what-if: shift mu_s to tan(34 deg), keep glass-bead A and Pouliquen span/L
salt = {}
mu_s_salt = np.tan(np.radians(34.0))
for hd in [2.5, 7.0, 15.0]:
    dt_ngf = (0.5 * np.pi * A_NGF / hd) ** 2
    dt_pou = (MU_2 - MU_S) / (1 + hd / L_POU)
    salt[f"h={hd}d"] = {
        "theta_stop_ngf_deg": float(np.degrees(np.arctan(mu_s_salt + dt_ngf))),
        "theta_stop_pouliquen_deg": float(np.degrees(np.arctan(mu_s_salt + dt_pou))),
    }

# ===================================================================== figure
cols = ["#1b6ca8", "#2a9d8f", "#e9a23b", "#c8553d", "#6d597a"]
fig, ax = plt.subplots(2, 2, figsize=(11.5, 8.6))
a = ax[0, 0]
for c, th in zip(cols, tilts_a):
    d_ = loc[th]
    zmm = d_["z"] * D_GRAIN * 1e3
    a.plot(d_["ub"] * U_SCALE * 1e3, zmm, "-", color=c, lw=1.6,
           label=f"{th:.0f}°: Bagnold (Jop μ(I))")
    a.plot(d_["u"][::8] * U_SCALE * 1e3, zmm[::8], "o", ms=4, mfc="none", color=c)
    zf, uf = ngf_a[th]
    a.plot(uf * U_SCALE * 1e3, zf * D_GRAIN * 1e3, "--", color=c, lw=1.2)
    a.plot(bagnold_linear(th, H_A, zf) * U_SCALE * 1e3, zf * D_GRAIN * 1e3, ":", color=c, lw=1.0)
a.plot([], [], "ko", mfc="none", ms=4, label="local μ(I), FD transient → steady")
a.plot([], [], "k--", lw=1.2, label="non-local (NGF), steady")
a.plot([], [], "k:", lw=1.0, label="Bagnold, linearised μ = μs + bI (NGF local limit)")
a.set_xlabel("velocity u (mm/s)")
a.set_ylabel("height above base z (mm)")
a.set_title(f"(a) steady profiles, h = {H_A:.0f} d = {H_A * D_GRAIN * 1e3:.0f} mm, glass beads d = 0.5 mm",
            fontsize=9.5)
a.legend(fontsize=7, loc="lower right")

a = ax[0, 1]
for c, h in zip(cols, sorted(prof)):
    zf, uf, um, it = prof[h]
    a.plot(uf / uf[-1], zf / h, color=c, lw=1.6, label=f"NGF, h = {h:.0f} d")
s = np.linspace(0, 1, 100)
a.plot(1 - (1 - s) ** 1.5, s, "k:", lw=1.5, label="Bagnold shape (local)")
a.plot(s, s, color="0.6", ls="-.", lw=1, label="linear shape")
a.set_xlabel("u / u_surface (–)")
a.set_ylabel("z / h (–)")
a.set_title(f"(b) NGF profile shape vs thickness at θ = {TH_PROF:.0f}° "
            f"(h_stop = {float(hstop_ngf_analytic(TH_PROF)):.1f} d)", fontsize=9.5)
a.legend(fontsize=7.5, loc="upper left")

a = ax[1, 0]
thf = np.linspace(20.92, 33.5, 400)
a.semilogy(thf, hstop_ngf_analytic(thf), "-", color=cols[0], lw=1.5,
           label="NGF linear stability, πA/(2√(tanθ−μs))")
a.semilogy(thetas_b, hstop_sim, "o", color=cols[0], ms=6, mfc="none",
           label="NGF dynamic runs (bisection on h)")
fl = [p for p in phase if p[2] > 1e-8]
st = [p for p in phase if p[2] <= 1e-8]
if fl:
    a.semilogy([p[0] for p in fl], [p[1] for p in fl], "^", color=cols[1], ms=5,
               label="start flowing → keeps flowing")
if st:
    a.semilogy([p[0] for p in st], [p[1] for p in st], "v", color=cols[3], ms=5,
               label="start flowing → stops")
a.semilogy(thf, hstop_pouliquen(thf), "--", color=cols[2], lw=1.5,
           label=f"Pouliquen form, θ1=20.9°, θ2=32.76°, L={L_POU:.2f} d")
a.axvline(np.degrees(np.arctan(MU_S)), color="k", lw=1, ls=":")
a.text(np.degrees(np.arctan(MU_S)) + 0.15, 0.35, "local μ(I): h_stop = 0 for θ > 20.9°,\n"
       "∞ below (no thickness dependence)", fontsize=7)
a.set_xlim(20.5, 33.5)
a.set_ylim(0.2, 300)
a.set_xlabel("inclination θ (deg)")
a.set_ylabel("stopping thickness h_stop / d (–)")
a.set_title("(c) thickness-dependent stopping angle", fontsize=9.5)
a.legend(fontsize=7, loc="upper right")

a = ax[1, 1]
for c, th in zip(cols + ["#333333"], sorted(set(flow[:, 0]))):
    m = flow[:, 0] == th
    a.plot(flow[m, 1] / flow[m, 2], flow[m, 3], "o", color=c, ms=5, label=f"NGF θ = {th:g}°")
xx = np.linspace(0, 13, 50)
a.plot(xx, BETA_P * xx, "k--", lw=1.2, label="Pouliquen glass beads, Fr = 0.136 h/h_stop")
a.plot(xx, beta_fit * xx + c_fit, ":", color="0.4", lw=1.2,
       label=f"fit to NGF: Fr = {beta_fit:.3f} h/h_stop {c_fit:+.3f}")
a.set_xlabel("h / h_stop(θ) (–)")
a.set_ylabel("Froude number ū / √(g h) (–)")
a.set_title("(d) flow rule from NGF steady states", fontsize=9.5)
a.legend(fontsize=7, loc="upper left")
fig.suptitle("μ(I) and non-local granular fluidity on a rough incline — numpy/scipy finite differences",
             fontsize=11)
fig.tight_layout()
png = os.path.join(OUT, "mui_rheology.png")
fig.savefig(png, dpi=100)

wall = time.time() - T_WALL0
results["ngf_hstop"] = {
    "theta_deg": thetas_b.tolist(),
    "hstop_over_d_simulated": [None if not np.isfinite(v) else float(v) for v in hstop_sim],
    "hstop_over_d_linear_stability": [float(v) for v in hstop_an],
    "max_rel_diff_sim_vs_analytic": float(np.nanmax(np.abs(hstop_sim / hstop_an - 1))),
    "hstop_24deg_N60_N120_N480": [float(hs_N60), float(hstop_sim[thetas_b == 24.0][0]), float(hs_N480)],
    "pouliquen_hstop_over_d_same_angles": [None if not np.isfinite(v) else float(v)
                                           for v in hstop_pouliquen(thetas_b)],
    "L_pouliquen_over_d": float(L_POU),
}
results["finite_amplitude_check"] = [
    {"theta_deg": float(p[0]), "h_over_d": float(p[1]), "h_over_hstop": float(p[1] / hstop_ngf_analytic(p[0])),
     "final_max_fluidity": float(p[2]), "flowing": bool(p[2] > 1e-8)} for p in phase]
results["ngf_thick_layer_h200_surface_velocity_ratio_to_linear_bagnold"] = float(thick_ratio)
results["flow_rule_fit"] = {"beta": float(beta_fit), "intercept": float(c_fit), "r2": float(r2),
                            "n_points": int(len(flow)), "pouliquen_beta_glass_beads": BETA_P}
results["salt_like_whatif_mu_s_tan34"] = salt
out = {
    "id": "mui-rheology",
    "method": "local mu(I) rheology (Jop et al. 2006) and non-local granular fluidity "
              "(Henann & Kamrin 2013; dynamic form, Kamrin & Henann 2015) for inclined-plane flow",
    "code": "self-written Python (numpy, scipy.linalg.solve_banded, numba)",
    "version": f"numpy {np.__version__}",
    "status": "ran",
    "wall_s": round(wall, 1),
    "cores": 1,
    "key_results": results,
    "notes": "Glass-bead parameters (d=0.5 mm): mu_s=tan20.9, mu_2=tan32.76, I0=0.279, b=(mu_2-mu_s)/I0, "
             "A=0.48, phi=0.6. NGF BCs: g=0 at rough base, dg/dz=0 at free surface. "
             "Timings: " + json.dumps({k: round(v, 1) for k, v in timings.items()}),
}
with open(os.path.join(OUT, "result.json"), "w") as f:
    json.dump(out, f, indent=1)
print(json.dumps(out, indent=1))
print("wall", wall)
