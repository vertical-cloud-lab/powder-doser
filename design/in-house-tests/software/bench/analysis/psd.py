"""Test 4: particle size and shape from backlit microscope images.

Pipeline per field: threshold (Otsu or adaptive) -> clean-up -> watershed
split of touching grains (markers = h-maxima of the distance transform) ->
drop grains touching the image edge -> per-grain ECD, Feret max/min,
aspect ratio, circularity, solidity. Grains cut by the edge are excluded
and the rest weighted by the Miles-Lantuejoul factor W H / ((W - w)(H - h)),
which removes the bias against large grains that edge exclusion causes.
Number- and volume-weighted d10/d50/d90 with bootstrap confidence intervals.
"""

import math

import numpy as np
from scipy import ndimage as ndi

from .common import to_gray

FIELDS = ("ecd_um", "feret_max_um", "feret_min_um", "aspect", "circularity", "solidity", "area_um2",
          "weight", "field")


def segment(img, method="otsu", block_px=151, offset=0.02, min_area_px=12):
    from skimage.filters import threshold_local, threshold_otsu
    g = to_gray(img)
    if method == "otsu":
        mask = g < threshold_otsu(g)
    elif method == "adaptive":
        mask = g < (threshold_local(g, block_px | 1, offset=offset))
    else:
        raise ValueError("method must be otsu or adaptive")
    mask = ndi.binary_opening(mask, iterations=1)
    mask = ndi.binary_fill_holes(mask)
    lab, n = ndi.label(mask)
    sizes = np.bincount(lab.ravel())
    keep = sizes >= min_area_px
    keep[0] = False
    return keep[lab]


def split_touching(mask, h_px=1.5, smooth=0.7):
    """Watershed on the distance transform. h_px sets how deep a neck must
    be (in px of distance) to split two grains; it stops elongated grains
    from being cut in two."""
    from skimage.morphology import h_maxima
    from skimage.segmentation import watershed
    dist = ndi.distance_transform_edt(mask)
    if smooth:
        dist = ndi.gaussian_filter(dist, smooth)
    peaks = h_maxima(dist, h_px)
    markers, _ = ndi.label(peaks)
    return watershed(-dist, markers, mask=mask)


def _min_feret(coords):
    """Minimum caliper width of a point set (rotating the hull edges)."""
    import cv2
    pts = coords[:, ::-1].astype(np.float32)
    # pixel corners, so a 1-px-wide grain has width 1
    corners = np.concatenate([pts + np.float32(d) for d in ((-.5, -.5), (-.5, .5), (.5, -.5), (.5, .5))])
    hull = cv2.convexHull(corners.astype(np.float32)).reshape(-1, 2).astype(float)
    if len(hull) < 3:
        return 1.0
    best = float("inf")
    for i in range(len(hull)):
        p, q = hull[i], hull[(i + 1) % len(hull)]
        e = q - p
        n = np.hypot(*e)
        if n == 0:
            continue
        d = np.abs((hull - p) @ np.array([-e[1], e[0]])) / n
        best = min(best, d.max())
    return best


def measure(labels, um_per_px, field=0, exclude_edge=True):
    """Per-grain table (dict of arrays) for one labelled field."""
    from skimage.measure import regionprops
    H, W = labels.shape
    rows = {k: [] for k in FIELDS}
    n_edge = 0
    for p in regionprops(labels):
        y0, x0, y1, x1 = p.bbox
        if exclude_edge and (y0 == 0 or x0 == 0 or y1 == H or x1 == W):
            n_edge += 1
            continue
        bw, bh = x1 - x0, y1 - y0
        w = (W * H) / max(1.0, (W - bw) * (H - bh))
        area = p.area * um_per_px ** 2
        per = p.perimeter * um_per_px
        fmax = p.feret_diameter_max * um_per_px
        fmin = _min_feret(p.coords) * um_per_px
        rows["ecd_um"].append(math.sqrt(4.0 * area / math.pi))
        rows["feret_max_um"].append(fmax)
        rows["feret_min_um"].append(fmin)
        rows["aspect"].append(min(1.0, fmin / fmax) if fmax > 0 else 1.0)
        rows["circularity"].append(min(1.0, 4.0 * math.pi * area / per ** 2) if per > 0 else 1.0)
        rows["solidity"].append(float(p.solidity))
        rows["area_um2"].append(area)
        rows["weight"].append(w)
        rows["field"].append(field)
    out = {k: np.asarray(v, float) for k, v in rows.items()}
    out["n_edge"] = n_edge
    return out


def analyze_field(img, um_per_px, field=0, method="otsu", h_px=1.5, min_area_px=12):
    mask = segment(img, method, min_area_px=min_area_px)
    labels = split_touching(mask, h_px)
    return measure(labels, um_per_px, field)


def merge(tables):
    out = {k: np.concatenate([t[k] for t in tables]) if tables else np.array([]) for k in FIELDS}
    out["n_edge"] = int(sum(t.get("n_edge", 0) for t in tables))
    return out


def weighted_quantile(x, w, q):
    x = np.asarray(x, float)
    w = np.asarray(w, float)
    o = np.argsort(x)
    x, w = x[o], w[o]
    c = np.cumsum(w) - 0.5 * w
    c /= w.sum()
    return np.interp(q, c, x)


def quantiles(ecd, w, weight="number", qs=(0.1, 0.5, 0.9)):
    ww = np.asarray(w, float) * (np.asarray(ecd, float) ** 3 if weight == "volume" else 1.0)
    return [float(weighted_quantile(ecd, ww, q)) for q in qs]


def psd_summary(table, n_boot=500, seed=0, by_field=False, um_per_px=None):
    """d10/d50/d90 (number and volume), span, shape means, bootstrap 95 % CIs."""
    rng = np.random.default_rng(seed)
    ecd, w = table["ecd_um"], table["weight"]
    n = ecd.size
    out = {"n": int(n), "n_edge_excluded": int(table.get("n_edge", 0))}
    if n < 5:
        raise ValueError("too few grains ({})".format(n))
    fields = np.unique(table["field"]) if by_field else None
    for weight in ("number", "volume"):
        d10, d50, d90 = quantiles(ecd, w, weight)
        boots = []
        for _ in range(n_boot):
            if by_field and fields.size > 1:
                pick = rng.choice(fields, fields.size)
                idx = np.concatenate([np.flatnonzero(table["field"] == f) for f in pick])
            else:
                idx = rng.integers(0, n, n)
            boots.append(quantiles(ecd[idx], w[idx], weight))
        boots = np.asarray(boots)
        lo, hi = np.percentile(boots, [2.5, 97.5], axis=0)
        key = "n" if weight == "number" else "v"
        out.update({"d10_{}".format(key): d10, "d50_{}".format(key): d50, "d90_{}".format(key): d90,
                    "span_{}".format(key): (d90 - d10) / d50,
                    "d10_{}_ci".format(key): [float(lo[0]), float(hi[0])],
                    "d50_{}_ci".format(key): [float(lo[1]), float(hi[1])],
                    "d90_{}_ci".format(key): [float(lo[2]), float(hi[2])]})
    for k in ("aspect", "circularity", "solidity"):
        out[k + "_mean"] = float(np.average(table[k], weights=w))
    if um_per_px:
        out["frac_under_10px"] = float(np.mean(ecd < 10 * um_per_px))
    return out


def scale_from_micrometer(img, spacing_um=10.0, axis=1):
    """um per pixel from an image of a stage micrometer (parallel lines,
    spacing_um apart), from the strongest peak of the line profile's
    spectrum, refined by parabolic interpolation."""
    g = to_gray(img)
    prof = g.mean(axis=0 if axis == 1 else 1)
    prof = prof - prof.mean()
    n = prof.size
    win = np.hanning(n)
    pad = 16 * n
    spec = np.abs(np.fft.rfft(prof * win, pad))
    spec[:pad // n * 3] = 0          # drop the lowest frequencies
    k = int(np.argmax(spec))
    if 0 < k < spec.size - 1:
        a, b, c = spec[k - 1], spec[k], spec[k + 1]
        k = k + 0.5 * (a - c) / (a - 2 * b + c)
    period_px = pad / k
    return spacing_um / period_px
