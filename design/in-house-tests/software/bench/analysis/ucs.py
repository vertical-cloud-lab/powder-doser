"""Test 8: unconfined strength. Peak force from the load-cell stream,
sigma_c, flow function ff_c = sigma_1 / sigma_c."""

import math
from dataclasses import asdict, dataclass

import numpy as np
from scipy.ndimage import median_filter

from .common import linfit

G = 9.80665


@dataclass
class Peak:
    peak_g: float             # above the baseline (self weight before contact)
    peak_n: float
    t_peak: float
    noise_g: float
    t_contact: float
    failed: bool              # a drop of >= 20 % after the peak
    detected: bool            # peak > 5 x noise
    sigma_c_pa: float

    def to_dict(self):
        return asdict(self)


def peak_force(t, grams, diam_mm=20.0, base_s=2.0, smooth=5, k_detect=5.0):
    t = np.asarray(t, float)
    g = np.asarray(grams, float)
    sel = t <= t[0] + base_s
    base = float(np.median(g[sel]))
    noise = float(np.median(np.abs(g[sel] - base)) * 1.4826)
    f = median_filter(g - base, size=smooth, mode="nearest") if smooth > 1 else g - base
    i = int(np.argmax(f))
    peak = float(f[i])
    detected = peak > k_detect * max(noise, 1e-6)
    above = np.flatnonzero(f > max(3.0 * noise, 0.2 * peak) if detected else f > 1e9)
    t_contact = float(t[above[0]]) if above.size else float("nan")
    failed = bool(detected and np.any(f[i:] < 0.8 * peak))
    area = math.pi * (diam_mm / 2000.0) ** 2
    sigma = peak / 1000.0 * G / area if detected else 0.0
    return Peak(peak, peak / 1000.0 * G, float(t[i]), noise, t_contact, failed, bool(detected), sigma)


def consolidation_mass_g(sigma1_pa, diam_mm=20.0):
    """Total mass on the piston for a consolidation stress (SPEC 8)."""
    area = math.pi * (diam_mm / 2000.0) ** 2
    return sigma1_pa * area / G * 1000.0


def jenike_class(ffc):
    if ffc is None or not np.isfinite(ffc):
        return "free-flowing (collapsed)"
    if ffc < 1:
        return "not flowing"
    if ffc < 2:
        return "very cohesive"
    if ffc < 4:
        return "cohesive"
    if ffc < 10:
        return "easy-flowing"
    return "free-flowing"


def flow_function(sigma1_pa, sigma_c_pa):
    s1 = np.asarray(sigma1_pa, float)
    sc = np.asarray(sigma_c_pa, float)
    ffc = [float(a / b) if b > 0 else float("inf") for a, b in zip(s1, sc)]
    out = {"ffc": ffc, "class": [jenike_class(x if np.isfinite(x) else None) for x in ffc]}
    pos = sc > 0
    if pos.sum() >= 2:
        f = linfit(s1[pos], sc[pos])
        out.update({"slope": f.slope, "intercept_pa": f.intercept, "r2": f.r2,
                    "ffc_from_slope": 1.0 / f.slope if f.slope > 0 else float("inf")})
    return out
