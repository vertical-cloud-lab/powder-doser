"""Test 1: heap angle of repose from a backlit silhouette.

analyze_heap(img, px_per_mm, ref=None) fits straight lines to both flanks
between 15 % and 85 % of the heap height (leaving out the rounded apex and
the toe), and reports the ISO apex angle atan(2h/D), the volume of the
silhouette turned about its axis, and the heap density when the mass is
given. Edges are found to sub-pixel precision at the 50 % level between
the dark (heap) and bright (backlight) plateaus.

ref: an image of the empty pedestal from the same camera position. It
gives the pedestal top (the heap base) exactly; without it the base is
found as the widest row (the pedestal rim), refined by the flank lines.
"""

import math
from dataclasses import asdict, dataclass, field

import numpy as np
from scipy import ndimage as ndi

from .common import crossing, largest_component, linfit, to_gray, two_level


@dataclass
class HeapResult:
    left_deg: float
    right_deg: float
    flank_deg: float            # mean of the two flanks
    apex_deg: float             # ISO 4324 style, atan(2h/D)
    height_mm: float
    base_mm: float
    volume_mm3: float
    rms_left_px: float
    rms_right_px: float
    base_row: float
    apex_row: float
    axis_x: float
    rows_used: int
    mass_g: float = None
    density_kg_m3: float = None
    fits: dict = field(default_factory=dict)

    def to_dict(self):
        d = asdict(self)
        d.pop("fits", None)
        return d


def silhouette(gray, level):
    mask = gray < level
    mask = largest_component(mask)
    return ndi.binary_fill_holes(mask)


def _row_edges(gray, mask, y, level):
    xs = np.flatnonzero(mask[y])
    if xs.size == 0:
        return None
    x0, x1 = int(xs[0]), int(xs[-1])
    w = gray.shape[1]
    xl = crossing(gray[y], x0 - 1, level) if x0 > 0 else float(x0)
    xr = crossing(gray[y], x1, level) if x1 < w - 1 else float(x1)
    return xl, xr


def base_from_reference(ref_gray, level):
    """Pedestal top row (sub-pixel) from an image of the empty pedestal."""
    m = silhouette(ref_gray, level)
    ys, xs = np.nonzero(m)
    top = ys.min()
    cols = xs[ys == top]
    cx = int(np.median(cols))
    col = ref_gray[:, cx]
    return crossing(col, top - 1, level), cx


def analyze_heap(img, px_per_mm, ref=None, base_row=None, lo=0.15, hi=0.85, mass_g=None):
    gray = to_gray(img)
    dark, bright, level = two_level(gray)
    mask = silhouette(gray, level)
    ys, xs = np.nonzero(mask)
    if ys.size == 0:
        raise ValueError("no silhouette found")
    top = int(ys.min())

    widths = np.zeros(gray.shape[0])
    edges = {}
    for y in range(top, int(ys.max()) + 1):
        e = _row_edges(gray, mask, y, level)
        if e is not None:
            edges[y] = e
            widths[y] = e[1] - e[0]

    refined = False
    if base_row is None and ref is not None:
        base_row, _ = base_from_reference(to_gray(ref), level)
    if base_row is None:
        # widest row = pedestal rim; the heap above it narrows, the chamfer below it narrows
        wmax = widths.max()
        cand = np.flatnonzero(widths >= wmax - 1.0)
        base_row = float(cand.min())
        refined = True

    # apex: sub-pixel crossing in the topmost column(s)
    top_cols = np.flatnonzero(mask[top])
    cx_top = int(round(np.median(top_cols)))
    apex_row = crossing(gray[:, cx_top], top - 1, level) if top > 0 else float(top)

    def fit_flanks(base):
        h = base - apex_row
        y_lo = base - hi * h            # 85 % of the height (upper limit, smaller row)
        y_hi = base - lo * h            # 15 % of the height
        rows = [y for y in edges if y_lo <= y <= y_hi]
        if len(rows) < 5:
            raise ValueError("heap too small: {} rows in the fit window".format(len(rows)))
        yy = np.array(rows, float)
        xl = np.array([edges[y][0] for y in rows])
        xr = np.array([edges[y][1] for y in rows])
        return linfit(yy, xl), linfit(yy, xr), rows

    fl, fr, rows = fit_flanks(base_row)
    if refined:
        # where the flank lines reach the rim width: average of both sides
        rim_l = edges[int(base_row)][0] if int(base_row) in edges else None
        rim_r = edges[int(base_row)][1] if int(base_row) in edges else None
        if rim_l is not None and fl.slope != 0 and fr.slope != 0:
            yl = (rim_l - fl.intercept) / fl.slope
            yr = (rim_r - fr.intercept) / fr.slope
            base_row = float(0.5 * (yl + yr))
            fl, fr, rows = fit_flanks(base_row)

    left = math.degrees(math.atan(1.0 / abs(fl.slope))) if fl.slope else 90.0
    right = math.degrees(math.atan(1.0 / abs(fr.slope))) if fr.slope else 90.0

    # base width at the base row (the pedestal rim)
    yb = int(round(base_row))
    near = [y for y in range(yb, yb + 3) if y in edges]
    base_px = max(widths[y] for y in near) if near else widths.max()
    h_px = base_row - apex_row
    apex = math.degrees(math.atan(2.0 * h_px / base_px))

    # volume of revolution: rows from the apex to the base
    vol_px = 0.0
    for y in range(int(math.ceil(apex_row)), int(math.floor(base_row)) + 1):
        if y in edges:
            r = 0.5 * (edges[y][1] - edges[y][0])
            frac = min(1.0, base_row - y + 0.5) if y > base_row - 0.5 else 1.0
            vol_px += math.pi * r * r * max(0.0, frac)
    volume = vol_px / px_per_mm ** 3
    axis_x = float(np.mean([0.5 * (edges[y][0] + edges[y][1]) for y in rows]))
    dens = None
    if mass_g is not None and volume > 0:
        dens = mass_g / volume * 1e6      # g/mm3 -> kg/m3
    return HeapResult(
        left_deg=left, right_deg=right, flank_deg=0.5 * (left + right), apex_deg=apex,
        height_mm=h_px / px_per_mm, base_mm=base_px / px_per_mm, volume_mm3=volume,
        rms_left_px=fl.rms, rms_right_px=fr.rms, base_row=float(base_row), apex_row=float(apex_row),
        axis_x=axis_x, rows_used=len(rows), mass_g=mass_g, density_kg_m3=dens,
        fits={"left": fl.to_dict(), "right": fr.to_dict()})


def avalanche_drops(mass_g, min_drop_g=0.002):
    """Mass drops between successive readings of a growing heap: grains
    sliding off the pedestal. Returns the drop sizes (g)."""
    m = np.asarray(mass_g, float)
    d = np.diff(m)
    return [float(-x) for x in d if x < -min_drop_g]


def growth_stopped(masses, frac=0.02, n=3):
    """True when the last n revolutions each grew the heap by < frac."""
    m = np.asarray(masses, float)
    if len(m) < n + 1:
        return False
    rel = np.diff(m[-(n + 1):]) / np.maximum(m[-(n + 1):-1], 1e-9)
    return bool(np.all(rel < frac))
