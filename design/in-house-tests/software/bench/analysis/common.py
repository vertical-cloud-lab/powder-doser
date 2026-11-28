"""Shared helpers: grey conversion, two-level thresholds, sub-pixel edges,
line fits with standard errors."""

from dataclasses import asdict, dataclass

import numpy as np


def to_gray(img):
    """Float image in 0..1 from uint8/uint16/float, RGB or grey."""
    a = np.asarray(img)
    if a.ndim == 3:
        a = a[..., :3].astype(float) @ np.array([0.299, 0.587, 0.114])
    a = a.astype(float)
    if a.max() > 1.0 + 1e-9:
        a = a / (65535.0 if a.max() > 255 else 255.0)
    return a


def two_level(gray, thresh=None):
    """Dark and bright plateau levels and the 50 % level between them.

    The 50 % crossing of a blurred step edge is its true position, which is
    why edges are located at this level rather than at the Otsu threshold.
    """
    from skimage.filters import threshold_otsu
    t = threshold_otsu(gray) if thresh is None else thresh
    dark = float(np.median(gray[gray < t])) if np.any(gray < t) else 0.0
    bright = float(np.median(gray[gray >= t])) if np.any(gray >= t) else 1.0
    return dark, bright, 0.5 * (dark + bright)


def crossing(profile, i, level):
    """Sub-pixel position of the level crossing between samples i and i+1."""
    a, b = profile[i], profile[i + 1]
    if a == b:
        return i + 0.5
    return i + (level - a) / (b - a)


def largest_component(mask):
    from scipy import ndimage as ndi
    lab, n = ndi.label(mask)
    if n == 0:
        return mask
    sizes = ndi.sum(mask, lab, index=np.arange(1, n + 1))
    return lab == (1 + int(np.argmax(sizes)))


@dataclass
class LineFit:
    slope: float
    intercept: float
    r2: float
    rms: float
    slope_se: float
    intercept_se: float
    n: int

    def to_dict(self):
        return asdict(self)


def linfit(x, y, w=None):
    """Least-squares line y = slope x + intercept with standard errors."""
    x = np.asarray(x, float)
    y = np.asarray(y, float)
    n = len(x)
    if n < 2:
        raise ValueError("need at least 2 points")
    if w is None:
        A = np.vstack([x, np.ones(n)]).T
        coef, *_ = np.linalg.lstsq(A, y, rcond=None)
    else:
        sw = np.sqrt(np.asarray(w, float))
        A = np.vstack([x * sw, sw]).T
        coef, *_ = np.linalg.lstsq(A, y * sw, rcond=None)
    slope, icpt = float(coef[0]), float(coef[1])
    res = y - (slope * x + icpt)
    ss_res = float(np.sum(res ** 2))
    ss_tot = float(np.sum((y - y.mean()) ** 2))
    r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else 1.0
    dof = max(1, n - 2)
    s2 = ss_res / dof
    sxx = float(np.sum((x - x.mean()) ** 2))
    slope_se = float(np.sqrt(s2 / sxx)) if sxx > 0 else float("nan")
    icpt_se = float(np.sqrt(s2 * (1.0 / n + x.mean() ** 2 / sxx))) if sxx > 0 else float("nan")
    return LineFit(slope, icpt, r2, float(np.sqrt(ss_res / n)), slope_se, icpt_se, n)


def r_squared(y, yhat):
    y = np.asarray(y, float)
    ss_res = float(np.sum((y - np.asarray(yhat, float)) ** 2))
    ss_tot = float(np.sum((y - y.mean()) ** 2))
    return 1.0 - ss_res / ss_tot if ss_tot > 0 else 1.0


def check(name, passed, value=None, limit=None):
    """One acceptance check, as stored in results.json."""
    return {"check": name, "pass": bool(passed), "value": value, "limit": limit}
