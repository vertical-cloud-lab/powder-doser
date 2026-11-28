"""Test 5: orifice cup. Flow rate from the balance stream, Beverloo fit,
critical orifice D_c and the arching strength estimate."""

import math
from dataclasses import asdict, dataclass

import numpy as np
from scipy.optimize import curve_fit

from .common import linfit

G = 9.80665


@dataclass
class Flow:
    rate_g_s: float
    rate_se: float
    r2: float
    n_fit: int
    mass_g: float
    t_start: float
    t_end: float
    method: str

    def to_dict(self):
        return asdict(self)


def flowed(t, m, min_g=0.05, t_from=None, window_s=60.0):
    """Did at least min_g arrive within window_s after t_from?"""
    t = np.asarray(t, float)
    m = np.asarray(m, float)
    t_from = t[0] if t_from is None else t_from
    sel = (t >= t_from) & (t <= t_from + window_s)
    if sel.sum() < 2:
        return False
    base = np.median(m[(t <= t_from)]) if np.any(t <= t_from) else m[sel][0]
    return bool(np.max(m[sel]) - base >= min_g)


def flow_rate(t, m, lo=0.2, hi=0.8, base_s=1.0, lag_s=0.0):
    """Steady discharge rate: a line through the samples between lo and hi
    of the total mass delivered (the middle of the ramp, away from the gate
    transient and the last grains). With fewer than 4 samples in that window
    (a short, fast discharge), use the interpolated crossing times instead.

    lag_s: the balance's first-order response time. A fast discharge (5 g in
    about 1 s through 6 mm) is short next to it, so the reading is corrected
    as m + lag_s dm/dt before the fit. Measure it once by dropping a weight
    on the pan (SOP 5)."""
    t = np.asarray(t, float)
    m = np.asarray(m, float)
    if lag_s > 0 and len(m) > 3:
        m = m + lag_s * np.gradient(m, t)
    m0 = float(np.median(m[t <= t[0] + base_s]))
    m1 = float(np.median(m[-max(3, len(m) // 20):]))
    total = m1 - m0
    if total <= 0:
        raise ValueError("no mass delivered")
    y = (m - m0) / total
    sel = (y >= lo) & (y <= hi)
    i_lo = int(np.argmax(y >= lo))
    i_hi = int(np.argmax(y >= hi))
    if sel.sum() >= 4:
        f = linfit(t[sel], m[sel])
        return Flow(f.slope, f.slope_se, f.r2, f.n, total, float(t[sel][0]), float(t[sel][-1]), "fit")
    # crossing times by interpolation
    def cross(level, i):
        if i == 0:
            return t[0]
        y0, y1 = y[i - 1], y[i]
        return t[i - 1] + (level - y0) / (y1 - y0) * (t[i] - t[i - 1])
    ta, tb = cross(lo, i_lo), cross(hi, i_hi)
    rate = (hi - lo) * total / (tb - ta) if tb > ta else float("nan")
    return Flow(rate, float("nan"), float("nan"), int(sel.sum()), total, float(ta), float(tb), "crossing")


def beverloo(D_mm, C, k, rho_b, d_mm):
    """W (g/s) = C rho_b sqrt(g) (D - k d)^2.5, SI inside."""
    D = np.clip((np.asarray(D_mm, float) - k * d_mm) / 1000.0, 0, None)
    return 1000.0 * C * rho_b * math.sqrt(G) * D ** 2.5


@dataclass
class BeverlooFit:
    C: float
    k: float
    C_se: float
    k_se: float
    r2: float
    n: int
    d0_mm: float              # D where the fitted flow reaches zero (k d)

    def to_dict(self):
        return asdict(self)


def beverloo_fit(D_mm, W_g_s, rho_b, d_mm):
    """Fit C and k with relative (log-space) errors, so the fast large-orifice
    points do not dominate. Start from the linear form W^0.4 vs D."""
    D = np.asarray(D_mm, float)
    W = np.asarray(W_g_s, float)
    # W^0.4 [g/s]^0.4 = (1000 C rho sqrt(g))^0.4 (D_mm - k d) / 1000, so the slope gives C
    lf = linfit(D, W ** 0.4)
    alpha = lf.slope
    C0 = (alpha * 1000.0) ** 2.5 / (1000.0 * rho_b * math.sqrt(G)) if alpha > 0 else 0.6
    k0 = -lf.intercept / alpha / d_mm if alpha > 0 else 1.5
    k_hi = 0.999 * D.min() / d_mm

    def logmodel(x, C, k):
        return np.log(np.maximum(beverloo(x, C, k, rho_b, d_mm), 1e-12))
    (C, k), cov = curve_fit(logmodel, D, np.log(W), p0=(C0, min(max(k0, 0.0), 0.9 * k_hi)),
                            bounds=([0.01, 0.0], [5.0, k_hi]), maxfev=20000)
    se = np.sqrt(np.diag(cov))
    resid = W - beverloo(D, C, k, rho_b, d_mm)
    ss_tot = float(np.sum((W - W.mean()) ** 2))
    r2 = 1.0 - float(np.sum(resid ** 2)) / ss_tot if ss_tot > 0 else 1.0
    return BeverlooFit(float(C), float(k), float(se[0]), float(se[1]), r2, len(D), float(k * d_mm))


def critical_orifice(results):
    """results: {D_mm: flowed bool}. Returns (largest no-flow D, smallest
    flowing D, estimate = their geometric mean), None where missing."""
    no = [d for d, ok in results.items() if not ok]
    yes = [d for d, ok in results.items() if ok]
    d_no = max(no) if no else None
    d_yes = min([d for d in yes if d_no is None or d > d_no], default=None)
    est = math.sqrt(d_no * d_yes) if (d_no and d_yes) else None
    return d_no, d_yes, est


def sigma_c_from_dc(rho_b, dc_mm, H=2.2):
    """Jenike arching estimate of the unconfined strength at the outlet (Pa)."""
    return rho_b * G * dc_mm / 1000.0 / H
