"""Test 7: rotating drum. Free-surface angle per frame, avalanche start and
stop angles, surface fluctuation (cohesive index), Froude number."""

import math
from dataclasses import asdict, dataclass

import numpy as np

from .common import crossing, linfit, to_gray, two_level

G = 9.80665


def find_drum(img, r_min_px=50, r_max_px=None):
    """Drum centre and radius (px) from the bright rear wall (Hough circle)."""
    import cv2
    g = (to_gray(img) * 255).astype(np.uint8)
    r_max_px = r_max_px or min(g.shape) // 2
    c = cv2.HoughCircles(cv2.GaussianBlur(g, (5, 5), 1.5), cv2.HOUGH_GRADIENT, 1.5, g.shape[0],
                         param1=80, param2=40, minRadius=r_min_px, maxRadius=r_max_px)
    if c is None:
        raise ValueError("no drum circle found")
    x, y, r = c[0][0]
    return (float(x), float(y)), float(r)


def surface_profile(img, center, radius, margin=0.25, level=None, rib_px=None):
    """Top of the powder bed in each column of the central chord, sub-pixel.

    The bed fills the bottom of the drum, so in each column the surface is
    the top of the dark run that reaches the bottom of the drum; dark ribs
    or specks above it are ignored. margin: fraction of the radius left out
    at each end of the chord. rib_px: depth of the wall ribs (default 4 %
    of the radius). Returns xs, ys (px)."""
    g = to_gray(img)
    cx, cy = center
    R = radius
    rib_px = 0.04 * R if rib_px is None else rib_px
    Ri = R - rib_px - 2.0
    if level is None:
        y0, y1 = int(cy - 0.9 * R), int(cy + 0.9 * R)
        x0, x1 = int(cx - 0.7 * R), int(cx + 0.7 * R)
        _, _, level = two_level(g[y0:y1, x0:x1])
    xs, ys = [], []
    for x in range(int(cx - (1 - margin) * R), int(cx + (1 - margin) * R) + 1):
        dy = math.sqrt(max(Ri * Ri - (x - cx) ** 2, 0.0))
        top, bot = int(math.ceil(cy - dy)), int(cy + dy)
        col = g[top:bot, x]
        if col.size < 5 or col[-1] >= level:
            continue
        bright = np.flatnonzero(col >= level)
        if bright.size == 0:
            continue                                  # column all bed: surface above the drum
        i = int(bright[-1])
        xs.append(x)
        ys.append(top + crossing(col, i, level))
    return np.asarray(xs, float), np.asarray(ys, float)


def fill_fraction(img, center, radius, rib_px=None):
    """Share of the drum's face covered by the bed (dark), inside the ribs."""
    g = to_gray(img)
    cx, cy = center
    Ri = radius - (0.04 * radius if rib_px is None else rib_px) - 2.0
    yy, xx = np.mgrid[0:g.shape[0], 0:g.shape[1]]
    inside = (xx - cx) ** 2 + (yy - cy) ** 2 <= Ri * Ri
    _, _, level = two_level(g[inside])
    return float(np.mean(g[inside] < level))


@dataclass
class SurfaceAngle:
    angle_deg: float          # positive: surface rises to the left (image)
    r2: float
    rms_px: float
    n: int

    def to_dict(self):
        return asdict(self)


def surface_angle(xs, ys):
    f = linfit(xs, ys)
    return SurfaceAngle(math.degrees(math.atan(f.slope)), f.r2, f.rms, f.n)


def drum_angles(frames, center, radius, min_r2=0.9, margin=0.25):
    angles, r2s, profiles = [], [], []
    for fr in frames:
        xs, ys = surface_profile(fr, center, radius, margin)
        if xs.size < 10:
            angles.append(float("nan"))
            r2s.append(0.0)
            profiles.append((xs, ys))
            continue
        s = surface_angle(xs, ys)
        angles.append(s.angle_deg)
        r2s.append(s.r2)
        profiles.append((xs, ys))
    angles = np.asarray(angles)
    r2s = np.asarray(r2s)
    valid = r2s >= min_r2
    return angles, valid, profiles


@dataclass
class Avalanches:
    n: int
    start_mean: float
    start_sd: float
    stop_mean: float
    stop_sd: float
    per_min: float
    starts: list
    stops: list

    def to_dict(self):
        return asdict(self)


def avalanches(t, angle, min_drop_deg=2.0, span=3, deg_per_frame=0.0):
    """Drops of at least min_drop_deg within `span` frames: the angle before
    the drop is a start angle, the minimum after it a stop angle.
    deg_per_frame (6 x rpm / fps): the drum turns this much between frames,
    so the frame before an avalanche reads half of it low on average and the
    frame after reads half of it high; both are corrected."""
    t = np.asarray(t, float)
    a = np.asarray(angle, float)
    starts, stops = [], []
    i = 1
    n = a.size
    while i < n:
        j_end = min(n, i + span)
        drop = a[i - 1] - a[i:j_end].min() if i < n else 0
        if drop >= min_drop_deg and a[i] < a[i - 1]:
            k = i + int(np.argmin(a[i:j_end]))
            starts.append(float(a[i - 1]) + 0.5 * deg_per_frame)
            stops.append(float(a[k]) - 0.5 * deg_per_frame)
            i = k + 1
        else:
            i += 1
    dur_min = (t[-1] - t[0]) / 60.0 if t.size > 1 else float("nan")
    s, p = np.asarray(starts), np.asarray(stops)
    return Avalanches(len(starts), float(s.mean()) if s.size else float("nan"),
                      float(s.std(ddof=1)) if s.size > 1 else float("nan"),
                      float(p.mean()) if p.size else float("nan"),
                      float(p.std(ddof=1)) if p.size > 1 else float("nan"),
                      len(starts) / dur_min if dur_min else float("nan"), starts, stops)


def cohesive_index(profiles, radius_px):
    """Mean over columns of the time-SD of the interface height, in units of
    the drum radius x 1000 (GranuDrum-style interface fluctuation)."""
    common = None
    for xs, _ in profiles:
        s = set(np.asarray(xs).astype(int).tolist())
        common = s if common is None else common & s
    if not common:
        return float("nan")
    cols = np.array(sorted(common))
    stack = []
    for xs, ys in profiles:
        lut = dict(zip(np.asarray(xs).astype(int).tolist(), ys))
        stack.append([lut[c] for c in cols])
    stack = np.asarray(stack)
    return float(np.mean(np.std(stack, axis=0)) / radius_px * 1000.0)


def froude(rpm, radius_m):
    w = rpm * 2.0 * math.pi / 60.0
    return w * w * radius_m / G
