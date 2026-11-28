"""Test 9: blade spreading. Coverage and streak area from a top-down image,
areal mass, layer packing fraction, brightness scatter."""

import numpy as np
from scipy import ndimage as ndi

from .common import to_gray, two_level


def covered_mask(img, roi=None, powder_bright=True, thresh=None, ref=None, k=4.0):
    """Powder pixels in the coupon ROI (y0, y1, x0, x1). With a clean-coupon
    image `ref`, the threshold is its mean + k SD (robust to the coupon's
    own texture); otherwise Otsu inside the ROI."""
    from skimage.filters import threshold_otsu
    g = to_gray(img)
    if roi is not None:
        y0, y1, x0, x1 = roi
        g = g[y0:y1, x0:x1]
    if thresh is None:
        if ref is not None:
            r = to_gray(ref)
            if roi is not None:
                r = r[y0:y1, x0:x1]
            thresh = r.mean() + (k if powder_bright else -k) * r.std()
        else:
            thresh = two_level(g, threshold_otsu(g))[2]      # 50 % level: unbiased edges
    m = g > thresh if powder_bright else g < thresh
    # pad by edge replication so the image border is not read as uncovered
    m = np.pad(m, 2, mode="edge")
    m = ndi.binary_opening(ndi.binary_closing(m, iterations=1), iterations=1)
    return m[2:-2, 2:-2]


def coverage(mask):
    return float(np.mean(mask))


def streaks(mask, axis=1, min_len_frac=0.2):
    """Uncovered lines along the spreading axis (blade scratches, a dragged
    grain): an opening of the uncovered mask with a line min_len_frac of the
    coupon long keeps only long runs along the axis, which drops round voids.
    Returns (area fraction of the coupon, count)."""
    L = max(3, int(min_len_frac * mask.shape[axis]))
    se = np.ones((1, L), bool) if axis == 1 else np.ones((L, 1), bool)
    st = ndi.binary_opening(~mask, structure=se)
    _, n = ndi.label(st)
    return float(st.mean()), int(n)


def saturated_fraction(img, hi=0.995, lo=0.005):
    g = to_gray(img)
    return float(np.mean((g >= hi) | (g <= lo)))


def brightness_cv(img, mask, tile=32):
    """Coefficient of variation of the mean brightness of covered tiles
    (a proxy for areal-mass scatter)."""
    g = to_gray(img)
    vals = []
    for y in range(0, g.shape[0] - tile + 1, tile):
        for x in range(0, g.shape[1] - tile + 1, tile):
            m = mask[y:y + tile, x:x + tile]
            if m.mean() > 0.9:
                vals.append(g[y:y + tile, x:x + tile][m].mean())
    vals = np.asarray(vals)
    return float(vals.std() / vals.mean()) if vals.size > 2 else float("nan")


def areal_mass_g_m2(layer_g, area_mm2):
    return layer_g / (area_mm2 * 1e-6)


def packing_fraction(layer_g, area_mm2, gap_mm, rho_true_kg_m3, coverage_frac=1.0):
    """Solid fraction of the covered part of a layer of thickness gap_mm."""
    vol_m3 = area_mm2 * 1e-6 * coverage_frac * gap_mm * 1e-3
    return (layer_g / 1000.0) / (rho_true_kg_m3 * vol_m3) if vol_m3 > 0 else float("nan")
