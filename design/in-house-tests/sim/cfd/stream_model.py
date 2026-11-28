"""Falling powder stream from the doser outlet: grain velocity, entrained air, impact speed.

1D integral (top-hat) two-phase plume model, written for this folder:
  grains:   v dv/ds = g - (v - u) f(Re_p) / tau_p
  air flux: dQ/ds  = 2 pi b alpha u                   (entrainment, alpha = 0.1)
  air mom.: d(rho_a Q u)/ds = (mdot / v) (v - u) f / tau_p   (drag on the grains, per unit length)
  b = sqrt(Q / (pi u)); f = 1 + 0.15 Re_p^0.687 (Schiller-Naumann); tau_p = rho_p d^2 / (18 mu).
This is the momentum-balance / entrainment model family used for free-falling particle plumes
(e.g. Liu 2004; Ansart et al. 2009). alpha = 0.1 is a jet/plume value (Morton, Taylor and Turner 1956
give 0.08-0.12 for top-hat profiles); it is not fitted to powder data, so Q is an estimate.
Single grains: the same grain equation with u = 0 (still air).
"""
import numpy as np
from scipy.integrate import solve_ivp

G = 9.81
RHO_A = 1.184
MU = 1.85e-5
A_OUT = 6.6e-6          # outlet annulus, m2
B_OUT = 1.5e-3          # stream radius at the outlet, m


def drag_factor(rel, d):
    Re = RHO_A * np.abs(rel) * d / MU
    return 1.0 + 0.15 * Re ** 0.687


def tau_p(d, rho_p):
    return rho_p * d * d / (18 * MU)


def single_grain(d, rho_p, v0, s_end, u_air=None):
    """Grain speed vs distance fallen. u_air(s) optional co-flowing air speed."""
    tp = tau_p(d, rho_p)

    def rhs(s, y):
        v = max(y[0], 1e-6)
        u = 0.0 if u_air is None else float(u_air(s))
        f = drag_factor(v - u, d)
        return [(G - (v - u) * f / tp) / v]
    sol = solve_ivp(rhs, (0, s_end), [max(v0, 1e-4)], rtol=1e-8, atol=1e-10, dense_output=True,
                    max_step=s_end / 200)
    return sol


def stream(mdot, d, rho_p, rho_b, s_end=0.10, alpha=0.10, u0=0.01):
    """Integrate the coupled stream. Returns dict of arrays along s (distance below the outlet)."""
    v0 = mdot / (rho_b * A_OUT)
    tp = tau_p(d, rho_p)
    Q0 = np.pi * B_OUT ** 2 * u0
    M0 = RHO_A * Q0 * u0

    def rhs(s, y):
        v, Q, M = y
        v = max(v, 1e-6)
        u = M / (RHO_A * Q)
        b = np.sqrt(Q / (np.pi * max(u, 1e-9)))
        f = drag_factor(v - u, d)
        Fd = mdot / v * (v - u) * f / tp      # N/m on the air
        dv = (G - (v - u) * f / tp) / v
        dQ = 2 * np.pi * b * alpha * u
        dM = Fd
        return [dv, dQ, dM]
    s_eval = np.linspace(0, s_end, 401)
    sol = solve_ivp(rhs, (0, s_end), [v0, Q0, M0], t_eval=s_eval, rtol=1e-8, atol=1e-14,
                    method="LSODA")
    v, Q, M = sol.y
    u = M / (RHO_A * Q)
    b = np.sqrt(Q / (np.pi * u))
    f = drag_factor(v - u, d)
    Fd = mdot / v * (v - u) * f / tp
    # solids volume fraction in a stream of radius B_OUT
    phi_s = mdot / (rho_p * v * np.pi * B_OUT ** 2)
    return dict(s=sol.t, v=v, Q=Q, u=u, b=b, Fd=Fd, phi_s=phi_s, v0=v0)


def vacuum_speed(v0, s):
    return np.sqrt(v0 ** 2 + 2 * G * s)
