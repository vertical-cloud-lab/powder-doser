"""Test 3: tilting plate. Slip angle from the IMU stream and the ring's
displacement in side-view images; wall friction fit tau = c_w + sigma tan(phi_w);
layer start angle (mode B) from frame differences."""

import math
from dataclasses import asdict, dataclass

import numpy as np

from .common import linfit, to_gray

G = 9.80665


def dark_centroid_x(img, roi=None, level=None):
    """Intensity-weighted x centroid (px) of the dark object in the ROI
    (y0, y1, x0, x1). Weights = darkness below the 50 % level, so the
    result moves smoothly with sub-pixel motion."""
    g = to_gray(img)
    if roi is not None:
        y0, y1, x0, x1 = roi
        g = g[y0:y1, x0:x1]
    else:
        x0 = 0
    if level is None:
        level = 0.5 * (np.percentile(g, 5) + np.percentile(g, 95))
    w = np.clip(level - g, 0, None)
    tot = w.sum()
    if tot <= 0:
        return float("nan")
    xs = np.arange(g.shape[1])
    return float((w.sum(axis=0) * xs).sum() / tot) + x0


def ring_displacement(frames, px_per_mm, roi=None, fiducial_roi=None):
    """Displacement (mm) of the ring along the plate, relative to the first
    frame. If the camera does not ride on the plate, give fiducial_roi (a
    dark mark fixed to the plate) and the ring is measured relative to it."""
    xs = []
    for f in frames:
        x = dark_centroid_x(f, roi)
        if fiducial_roi is not None:
            x -= dark_centroid_x(f, fiducial_roi)
        xs.append(x)
    xs = np.asarray(xs)
    return (xs - xs[0]) / px_per_mm


def detect_slip(t, disp_mm, threshold_mm=0.5, baseline_n=3):
    """First time the displacement exceeds threshold_mm above the baseline,
    interpolated between frames. Returns (t_slip or None, index or None)."""
    t = np.asarray(t, float)
    d = np.asarray(disp_mm, float)
    base = float(np.median(d[:baseline_n]))
    above = np.flatnonzero(d - base > threshold_mm)
    if above.size == 0:
        return None, None
    i = int(above[0])
    if i == 0:
        return float(t[0]), 0
    d0, d1 = d[i - 1] - base, d[i] - base
    frac = (threshold_mm - d0) / (d1 - d0) if d1 != d0 else 1.0
    return float(t[i - 1] + frac * (t[i] - t[i - 1])), i


def angle_at(t_query, t_imu, deg_imu):
    return float(np.interp(t_query, t_imu, deg_imu))


def ramp_angle_at(t_query, t_imu, deg_imu, t_end=None, window_s=5.0, guard_s=0.2):
    """Plate angle at t_query from a straight line fitted to the IMU angle
    over the window_s before t_end - guard_s (t_end: the earliest event).
    The accelerometer reads the slip's own jolt as tilt, so samples at and
    after the event are left out; the steady 0.5 deg/s ramp is a line."""
    t = np.asarray(t_imu, float)
    d = np.asarray(deg_imu, float)
    t_end = t_query if t_end is None else t_end
    sel = (t >= t_end - guard_s - window_s) & (t <= t_end - guard_s)
    if sel.sum() < 5:
        return angle_at(t_query, t, d)
    f = linfit(t[sel], d[sel])
    return float(f.slope * t_query + f.intercept)


def jolt_time(t, jolt, k=8.0, skip_s=1.0):
    """First IMU sample whose jolt exceeds median + k * MAD (after skip_s)."""
    t = np.asarray(t, float)
    j = np.asarray(jolt, float)
    sel = t >= t[0] + skip_s
    if not np.any(sel):
        return None
    med = np.median(j[sel])
    mad = np.median(np.abs(j[sel] - med)) * 1.4826 + 1e-9
    hit = np.flatnonzero(sel & (j > med + k * mad))
    return float(t[hit[0]]) if hit.size else None


def ramp_rate(t, deg, t_center, window_s=10.0):
    sel = (np.asarray(t) > t_center - window_s) & (np.asarray(t) <= t_center)
    if sel.sum() < 3:
        return float("nan")
    return linfit(np.asarray(t)[sel], np.asarray(deg)[sel]).slope


def stresses_at_slip(mass_g, theta_deg, area_mm2):
    """Normal and shear stress (Pa) on the powder-wall contact at the slip
    angle, for the total mass carried by that contact (powder + ring + lid)."""
    w = mass_g / 1000.0 * G
    a = area_mm2 * 1e-6
    th = math.radians(theta_deg)
    return w * math.cos(th) / a, w * math.sin(th) / a


@dataclass
class WallFriction:
    phi_w_deg: float
    mu_w: float
    c_w_pa: float
    phi_w_se_deg: float
    c_w_se_pa: float
    r2: float
    n: int

    def to_dict(self):
        return asdict(self)


def wall_friction_fit(sigma_pa, tau_pa):
    f = linfit(sigma_pa, tau_pa)
    phi = math.degrees(math.atan(f.slope))
    phi_se = math.degrees(f.slope_se / (1.0 + f.slope ** 2))
    return WallFriction(phi_w_deg=phi, mu_w=f.slope, c_w_pa=f.intercept, phi_w_se_deg=phi_se,
                        c_w_se_pa=f.intercept_se, r2=f.r2, n=f.n)


def layer_start(frames, roi=None, k=6.0, baseline_n=5):
    """Mode B: index of the first frame whose mean absolute difference from
    the first frame exceeds the baseline by k standard deviations."""
    ref = to_gray(frames[0])
    if roi is not None:
        y0, y1, x0, x1 = roi
        ref = ref[y0:y1, x0:x1]
    diffs = []
    for f in frames:
        g = to_gray(f)
        if roi is not None:
            g = g[y0:y1, x0:x1]
        diffs.append(float(np.mean(np.abs(g - ref))))
    diffs = np.asarray(diffs)
    base = diffs[1:baseline_n + 1]
    thr = base.mean() + k * (base.std() + 1e-6)
    hit = np.flatnonzero(diffs > thr)
    hit = hit[hit > baseline_n]
    return (int(hit[0]) if hit.size else None), diffs
