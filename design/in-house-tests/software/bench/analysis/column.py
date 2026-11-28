"""Test 2: column height in a backlit cylinder -> volume -> densities.

column_top(img, ...) finds the powder top in each image column of a strip
inside the bore (sub-pixel, ignoring thin graduation lines), and returns
its median height in mm above the datum row (the inside bottom).
A water calibration table (height -> mL, from weighed water) turns heights
into volumes. Then bulk and tapped density, Hausner ratio, Carr index and
the Kawakita constants a and 1/b.
"""

from dataclasses import asdict, dataclass

import numpy as np
from scipy import ndimage as ndi
from scipy.optimize import curve_fit

from .common import crossing, linfit, r_squared, to_gray, two_level


@dataclass
class ColumnTop:
    top_mm: float
    top_row: float
    flat_mm: float            # p90 - p10 of the per-column heights
    tilt_mm: float            # right minus left half
    n_cols: int

    def to_dict(self):
        return asdict(self)


def column_top(img, px_per_mm, datum_row, x_range, mode="axisym", axis_x=None, min_run_mm=0.5,
               smooth_px=1.0):
    """Powder (or dyed-water) top in mm above the datum row (the inside bottom).

    x_range: (x0, x1) image columns inside the bore, clear of the wall glare.
    Thin dark lines (graduations) are skipped: the top is the first row that
    starts a dark run at least min_run_mm long.
    mode "axisym": the surface is taken as axisymmetric about axis_x (the
      bore centre, default the middle of x_range), and the result is its
      volume-equivalent flat height (2/R^2) * integral of h(r) r dr, with the
      left and right halves averaged. A tilt cancels; a mound or a crater
      counts with its true volume.
    mode "median": median height over the columns.
    mode "center": lowest point of the middle third (bottom of a water meniscus).
    """
    gray = to_gray(img)
    if smooth_px:
        gray = ndi.gaussian_filter1d(gray, smooth_px, axis=1)
    x0, x1 = int(x_range[0]), int(x_range[1])
    strip = gray[:int(datum_row), x0:x1]
    _, _, level = two_level(strip)
    run = max(3, int(round(min_run_mm * px_per_mm)))
    xs, tops = [], []
    for j in range(strip.shape[1]):
        col = strip[:, j]
        dark = col < level
        cs = np.convolve(dark.astype(int), np.ones(run, int), mode="valid")
        idx = np.flatnonzero(cs == run)
        if idx.size == 0:
            continue
        y = int(idx[0])
        xs.append(x0 + j)
        tops.append(crossing(col, y - 1, level) if y > 0 else float(y))
    if not tops:
        raise ValueError("no powder top found in the strip")
    xs = np.array(xs, float)
    tops = np.array(tops)
    hmm = (datum_row - tops) / px_per_mm
    if mode == "center":
        n = len(tops)
        mid = tops[n // 3: max(n // 3 + 1, 2 * n // 3)]
        h = (datum_row - float(np.max(mid))) / px_per_mm
    elif mode == "median":
        h = float(np.median(hmm))
    elif mode == "axisym":
        cx = 0.5 * (x0 + x1 - 1) if axis_x is None else float(axis_x)
        r = np.abs(xs - cx) / px_per_mm
        rmax = r.max()
        edges = np.linspace(0, rmax, 41)
        prof = []
        for a, b in zip(edges[:-1], edges[1:]):
            sel = (r >= a) & (r < b) if b < rmax else (r >= a)
            prof.append(np.mean(hmm[sel]) if np.any(sel) else np.nan)
        prof = np.asarray(prof)
        rc = 0.5 * (edges[:-1] + edges[1:])
        ok = np.isfinite(prof)
        prof = np.interp(rc, rc[ok], prof[ok])
        h = float(np.sum(prof * rc * np.diff(edges)) * 2.0 / rmax ** 2)
    else:
        raise ValueError("mode must be axisym, median or center")
    half = len(hmm) // 2
    return ColumnTop(top_mm=h, top_row=datum_row - h * px_per_mm,
                     flat_mm=float(np.percentile(hmm, 90) - np.percentile(hmm, 10)),
                     tilt_mm=float(np.mean(hmm[half:]) - np.mean(hmm[:half])), n_cols=len(tops))


class VolumeCalibration:
    """Height (mm above the datum) -> volume (mL), from weighed water.

    A straight bore is a line V = A h + V0; the fit residual is the check.
    Outside the calibrated range the line is extrapolated (flagged)."""

    # water/glass: capillary length squared a^2 = gamma / (rho g) = 7.4 mm^2,
    # contact angle about 0; raised volume = wall perimeter x a^2 cos(theta)
    A2_MM2 = 7.4

    def __init__(self, heights_mm, volumes_ml, meniscus_ml=None):
        h = np.asarray(heights_mm, float)
        v = np.asarray(volumes_ml, float)
        order = np.argsort(h)
        self.h, self.v = h[order], v[order]
        self.fit = linfit(self.h, self.v)
        self.residual_ml = float(np.max(np.abs(self.v - (self.fit.slope * self.h + self.fit.intercept))))
        if meniscus_ml is None:
            meniscus_ml = np.pi * self.bore_mm * self.A2_MM2 / 1000.0
        self.meniscus_ml = float(meniscus_ml)

    @classmethod
    def from_water(cls, heights_mm, water_g, temp_c=22.0, meniscus_ml=None):
        rho = water_density(temp_c)
        return cls(heights_mm, np.asarray(water_g, float) / rho, meniscus_ml)

    def volume(self, h_mm):
        """Water volume for a meniscus-bottom height (the calibration itself)."""
        return self.fit.slope * np.asarray(h_mm, float) + self.fit.intercept

    def powder_volume(self, h_mm):
        """Volume under a powder surface at h_mm (volume-equivalent height).
        The water readings were taken at the flat centre of the meniscus,
        so the calibration intercept carries the water raised at the wall;
        that is removed here (meniscus_ml)."""
        return self.volume(h_mm) - self.meniscus_ml

    def in_range(self, h_mm):
        return bool(self.h.min() - 2 <= h_mm <= self.h.max() + 2)

    @property
    def bore_mm(self):
        """Equivalent bore from the slope (mL per mm)."""
        return float(2.0 * np.sqrt(self.fit.slope * 1000.0 / np.pi))

    def to_dict(self):
        return {"heights_mm": self.h.tolist(), "volumes_ml": self.v.tolist(),
                "ml_per_mm": self.fit.slope, "v0_ml": self.fit.intercept,
                "residual_ml": self.residual_ml, "bore_mm": self.bore_mm, "meniscus_ml": self.meniscus_ml}

    def save_csv(self, path):
        with open(path, "w") as f:
            f.write("# meniscus_ml={:.5f}\n".format(self.meniscus_ml))
            f.write("height_mm,volume_ml\n")
            for a, b in zip(self.h, self.v):
                f.write("{:.4f},{:.5f}\n".format(a, b))

    @classmethod
    def load_csv(cls, path):
        men = None
        with open(path) as f:
            first = f.readline()
            if first.startswith("# meniscus_ml="):
                men = float(first.split("=")[1])
        d = np.genfromtxt(path, delimiter=",", names=True, comments="#")
        return cls(d["height_mm"], d["volume_ml"], men)


def water_density(temp_c):
    """g/mL, 0-40 C (Tanaka et al. 2001 formula)."""
    t = float(temp_c)
    return 0.999974950 * (1 - (t - 3.983035) ** 2 * (t + 301.797) / (522528.9 * (t + 69.34881)))


@dataclass
class DensityResult:
    mass_g: float
    v0_ml: float
    vf_ml: float
    rho_bulk: float           # kg/m3
    rho_tap: float
    hausner: float
    carr: float               # %
    kawakita_a: float
    kawakita_inv_b: float     # taps
    kawakita_r2: float
    taps: list
    volumes_ml: list
    last_change_pct: float

    def to_dict(self):
        return asdict(self)


def kawakita(n, a, b):
    n = np.asarray(n, float)
    return a * b * n / (1.0 + b * n)


def kawakita_fit(taps, volumes_ml):
    """C = (V0 - VN)/V0 = a b N / (1 + b N). Linear form N/C = N/a + 1/(a b)
    for the start, then a non-linear least-squares refinement."""
    n = np.asarray(taps, float)
    v = np.asarray(volumes_ml, float)
    v0 = v[n == 0][0] if np.any(n == 0) else v[0]
    sel = n > 0
    c = (v0 - v[sel]) / v0
    ok = c > 0
    lf = linfit(n[sel][ok], n[sel][ok] / c[ok])
    a0 = 1.0 / lf.slope if lf.slope > 0 else max(c.max(), 1e-3)
    b0 = lf.slope / lf.intercept if lf.intercept > 0 else 0.1
    try:
        (a, b), _ = curve_fit(kawakita, n[sel], c, p0=(a0, b0), bounds=([0, 0], [1, 10]), maxfev=10000)
    except RuntimeError:
        a, b = a0, b0
    r2 = r_squared(c, kawakita(n[sel], a, b))
    return float(a), float(1.0 / b), float(r2)


def densities(mass_g, taps, volumes_ml):
    taps = list(map(float, taps))
    v = list(map(float, volumes_ml))
    v0, vf = v[0], v[-1]
    a, inv_b, r2 = kawakita_fit(taps, v)
    last = 100.0 * abs(v[-2] - v[-1]) / v[-2] if len(v) > 1 else float("nan")
    return DensityResult(mass_g=mass_g, v0_ml=v0, vf_ml=vf, rho_bulk=mass_g / v0 * 1000.0,
                         rho_tap=mass_g / vf * 1000.0, hausner=v0 / vf, carr=100.0 * (v0 - vf) / v0,
                         kawakita_a=a, kawakita_inv_b=inv_b, kawakita_r2=r2, taps=taps, volumes_ml=v,
                         last_change_pct=last)
