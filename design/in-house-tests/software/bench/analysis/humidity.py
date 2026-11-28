"""Test 6: humidity chambers. Uptake vs time (first order), equilibrium
uptake vs RH, the RH where uptake jumps (deliquescence onset)."""

from dataclasses import asdict, dataclass

import numpy as np
from scipy.optimize import curve_fit

from .common import r_squared

# Greenspan (1977), saturated salt solutions: RH % at 15, 20, 25, 30 C.
GREENSPAN = {
    "MgCl2": (33.30, 33.07, 32.78, 32.44),
    "MgNO3": (55.87, 54.38, 52.89, 51.40),
    "NaCl": (75.61, 75.47, 75.29, 75.09),
    "KCl": (85.92, 85.11, 84.34, 83.62),
}
_T = (15.0, 20.0, 25.0, 30.0)
SILICA_RH = 5.0


def nominal_rh(box, temp_c=25.0):
    if box == "silica":
        return SILICA_RH
    return float(np.interp(temp_c, _T, GREENSPAN[box]))


def uptake_mg_per_g(mass_g, dry_mass_g):
    return (np.asarray(mass_g, float) - dry_mass_g) / dry_mass_g * 1000.0


def first_order(t, u_eq, tau):
    return u_eq * (1.0 - np.exp(-np.asarray(t, float) / tau))


@dataclass
class UptakeFit:
    u_eq: float          # mg/g
    tau_h: float
    u_eq_se: float
    tau_se: float
    r2: float

    def to_dict(self):
        return asdict(self)


def uptake_fit(t_h, u):
    t = np.asarray(t_h, float)
    u = np.asarray(u, float)
    u_end = u[-1] if abs(u[-1]) > 1e-9 else 1e-3
    tau0 = max(0.1, float(t[np.argmin(np.abs(u - 0.63 * u_end))]))
    try:
        (ueq, tau), cov = curve_fit(first_order, t, u, p0=(u_end, tau0),
                                    bounds=([-1e4, 0.01], [1e4, 1e4]), maxfev=20000)
        se = np.sqrt(np.diag(cov))
    except RuntimeError:
        ueq, tau, se = u_end, tau0, (float("nan"), float("nan"))
    return UptakeFit(float(ueq), float(tau), float(se[0]), float(se[1]),
                     r_squared(u, first_order(t, ueq, tau)))


def deliquescence_onset(rh, u_eq, ratio=5.0):
    """RH bracket where the isotherm's slope jumps by `ratio` over the slope
    below it. Returns (rh_low, rh_high, midpoint) or None."""
    rh = np.asarray(rh, float)
    u = np.asarray(u_eq, float)
    o = np.argsort(rh)
    rh, u = rh[o], u[o]
    slopes = np.diff(u) / np.diff(rh)
    for i in range(1, len(slopes)):
        base = max(np.max(np.abs(slopes[:i])), 1e-6)
        if slopes[i] > ratio * base:
            return float(rh[i]), float(rh[i + 1]), float(0.5 * (rh[i] + rh[i + 1]))
    return None


def isotherm(box_results):
    """Equilibrium uptake against RH from several boxes' results.

    box_results: iterable of dicts with "box_rh_end" (or "nominal_rh") and
    "fit" {"u_eq": ...} (humidity_result.json["results"]). Returns the sorted
    table and the deliquescence bracket."""
    pts = []
    for r in box_results:
        rh = r.get("box_rh_end", r.get("nominal_rh"))
        pts.append((float(rh), float(r["fit"]["u_eq"])))
    pts.sort()
    rh = [p[0] for p in pts]
    u = [p[1] for p in pts]
    return {"rh": rh, "u_eq_mg_g": u, "onset": deliquescence_onset(rh, u) if len(pts) >= 3 else None}
