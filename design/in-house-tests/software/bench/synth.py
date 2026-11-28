"""Synthetic data with known answers, for the tests and the simulator.

Every generator returns (data, truth). Images are float 0..1, rendered
with 4x supersampling (anti-aliased edges), then blurred (optics) and
noised (sensor), so the analysis sees realistic sub-pixel edges.
"""

import math

import numpy as np
from scipy import ndimage as ndi

SS = 4  # supersampling factor


def _finish(img, blur_px, noise, rng):
    if blur_px:
        img = ndi.gaussian_filter(img, blur_px)
    if noise:
        img = img + rng.normal(0.0, noise, img.shape)
    return np.clip(img, 0.0, 1.0).astype(np.float32)


def _grid(shape):
    h, w = shape
    ys = (np.arange(h * SS, dtype=np.float32) + 0.5) / SS - 0.5
    xs = (np.arange(w * SS, dtype=np.float32) + 0.5) / SS - 0.5
    return xs, ys


def _down(hi):
    h, w = hi.shape[0] // SS, hi.shape[1] // SS
    return hi.reshape(h, SS, w, SS).mean(axis=(1, 3))


def _smooth_noise(n, corr, amp, rng):
    if amp <= 0:
        return np.zeros(n, np.float32)
    z = rng.normal(0, 1, n)
    if corr > 1:
        z = ndi.gaussian_filter1d(z, corr)
    z = z / (z.std() + 1e-12) * amp
    return z.astype(np.float32)


# ---------------------------------------------------------------------------
# Test 1: heap on a pedestal
# ---------------------------------------------------------------------------

def heap_profile(x_mm, left_deg, right_deg, base_mm, round_mm=0.0):
    """Height (mm) of a cone with different flank angles whose apex is
    rounded by a circular arc of radius round_mm tangent to both flanks.
    Returns (h, H_cone, x_apex)."""
    R = base_mm / 2.0
    tl, tr = math.tan(math.radians(left_deg)), math.tan(math.radians(right_deg))
    xa = R * (tr - tl) / (tl + tr)
    H = (xa + R) * tl
    x_mm = np.asarray(x_mm, float)
    h = np.where(x_mm < xa, H - (xa - x_mm) * tl, H - (x_mm - xa) * tr)
    if round_mm > 0:
        thl, thr = math.radians(left_deg), math.radians(right_deg)
        d1 = np.array([-math.cos(thl), -math.sin(thl)])
        d2 = np.array([math.cos(thr), -math.sin(thr)])
        u = d1 + d2
        u /= np.linalg.norm(u)
        alpha = 0.5 * math.acos(float(np.clip(d1 @ d2, -1, 1)))
        s = round_mm / math.sin(alpha)
        c = np.array([xa, H]) + s * u
        t1 = np.array([xa, H]) + s * math.cos(alpha) * d1
        t2 = np.array([xa, H]) + s * math.cos(alpha) * d2
        arc = (x_mm > t1[0]) & (x_mm < t2[0])
        h = np.where(arc, c[1] + np.sqrt(np.maximum(round_mm ** 2 - (x_mm - c[0]) ** 2, 0.0)), h)
    return h, H, xa


def heap_image(left_deg=32.0, right_deg=None, base_mm=20.0, px_per_mm=28.6, round_mm=1.0,
               rough_mm=0.05, blur_px=1.0, noise=0.02, shape=(700, 900), base_frac=0.62,
               empty=False, seed=0, bright=0.92, dark=0.08, heap_base_mm=None):
    """Silhouette of a heap on a pedestal (sharp rim, 0.4 mm land, 45 deg
    chamfer, riser) against a backlight. empty=True draws the pedestal only.
    heap_base_mm: base of a heap still growing (smaller than the pedestal)."""
    ped_mm = base_mm
    base_mm = ped_mm if heap_base_mm is None else min(heap_base_mm, ped_mm)
    rng = np.random.default_rng(seed)
    right_deg = left_deg if right_deg is None else right_deg
    H_img, W_img = shape
    xs, ys = _grid(shape)
    cx = W_img / 2.0
    yb = H_img * base_frac
    x_mm = (xs - cx) / px_per_mm
    up_mm = (yb - ys) / px_per_mm                    # height above the pedestal top
    R = base_mm / 2.0
    h, Hc, xa = heap_profile(x_mm, left_deg, right_deg, base_mm, round_mm)
    h = h + _smooth_noise(len(h), 0.4 * px_per_mm * SS / 4, rough_mm, rng)
    h = np.where(np.abs(x_mm) <= R, np.maximum(h, 0.0), 0.0)
    R = ped_mm / 2.0
    land, riser_r = 0.4, min(R, 8.0) - 1.0
    X = x_mm[None, :]
    U = up_mm[:, None]
    ped = (U < 0) & (U >= -land) & (np.abs(X) <= R)
    ped |= (U < -land) & (np.abs(X) <= R + (U + land))  & (np.abs(X) > riser_r - 1e9)
    ped &= (U >= -(land + (R - riser_r)))
    riser = (U < -(land + (R - riser_r))) & (np.abs(X) <= riser_r)
    sil = ped | riser
    if not empty:
        sil |= (U >= 0) & (U <= h[None, :])
    hi = np.where(sil, dark, bright).astype(np.float32)
    img = _finish(_down(hi), blur_px, noise, rng)
    # truth: the same volume definition the analysis uses (silhouette of revolution)
    xf = np.linspace(-base_mm / 2.0, base_mm / 2.0, 20001)
    hf, _, _ = heap_profile(xf, left_deg, right_deg, base_mm, round_mm)
    hf = np.maximum(hf, 0)
    zs = np.linspace(0, hf.max(), 2000)
    vol = 0.0
    for z0, z1 in zip(zs[:-1], zs[1:]):
        inside = xf[hf >= 0.5 * (z0 + z1)]
        if inside.size:
            r = 0.5 * (inside.max() - inside.min())
            vol += math.pi * r * r * (z1 - z0)
    truth = {"left_deg": left_deg, "right_deg": right_deg, "height_mm": float(hf.max()),
             "cone_height_mm": Hc, "base_mm": base_mm, "volume_mm3": vol,
             "apex_deg": math.degrees(math.atan(2 * hf.max() / base_mm)),
             "base_row": yb - 0.0, "px_per_mm": px_per_mm}
    return img, truth


# ---------------------------------------------------------------------------
# Test 2: powder column in a backlit graduated cylinder
# ---------------------------------------------------------------------------

def column_image(top_mm, bore_mm=13.0, px_per_mm=16.0, datum_row=1220, shape=(1300, 320),
                 tilt_mm=0.0, bump_mm=0.0, wall_mm=1.2, graduations=True, blur_px=1.0,
                 noise=0.02, seed=0, texture=0.06):
    """Cylinder with powder up to top_mm above the datum row (the inside
    bottom). tilt_mm: left-right height difference of the surface;
    bump_mm: centre-to-edge height of a mound (negative: a crater)."""
    rng = np.random.default_rng(seed)
    H, W = shape
    xs, ys = _grid(shape)
    cx = W / 2.0
    x_mm = (xs - cx) / px_per_mm
    up = (datum_row - ys) / px_per_mm
    R = bore_mm / 2.0
    X = x_mm[None, :]
    U = up[:, None]
    xn = np.clip(X / R, -1, 1)
    # axisymmetric mound (or crater) whose volume-mean height is top_mm, plus a tilt
    surf = top_mm + tilt_mm * 0.5 * xn + bump_mm * (1 - xn ** 2) - bump_mm * 0.5
    bright, dark = 0.9, 0.12
    img = np.full((H * SS, W * SS), bright, np.float32)
    img = img - 0.05 * np.abs(xn) ** 4                       # lens-like falloff through the glass
    inner = np.abs(X) <= R
    powder = inner & (U <= surf) & (U >= 0)
    img = np.where(powder, dark, img)
    wall = (np.abs(X) > R) & (np.abs(X) <= R + wall_mm)
    img = np.where(wall, 0.25, img)
    img = np.where(U < 0, 0.2, img)                        # foot / holder below the datum
    out = _down(img)
    if texture:
        tex = ndi.gaussian_filter(rng.normal(0, 1, out.shape), 1.0) * texture
        pm = _down(powder.astype(np.float32)) > 0.5
        out = np.where(pm, out + tex, out)
    if graduations:
        step = 0.75 * px_per_mm                             # 0.1 mL on a 13 mm bore
        for k in range(1, int(H / step)):
            y = int(datum_row - k * step)
            if 0 <= y < H:
                x0 = int(cx - R * px_per_mm * 0.9)
                x1 = int(cx - R * px_per_mm * (0.45 if k % 10 else 0.0))
                out[y, x0:x1] -= 0.35
    return _finish(out, blur_px, noise, rng), {"top_mm": top_mm, "datum_row": datum_row}


def bore_volume_ml(h_mm, bore_mm=13.0):
    return math.pi * (bore_mm / 2.0) ** 2 * h_mm / 1000.0


def kawakita_volumes(taps, v0_ml, a, b):
    n = np.asarray(taps, float)
    c = a * b * n / (1.0 + b * n)
    return v0_ml * (1.0 - c)


# ---------------------------------------------------------------------------
# Test 3: tilting plate
# ---------------------------------------------------------------------------

def slip_angle_for(mass_g, area_mm2, phi_w_deg, c_w_pa):
    """Angle at which tau = c_w + sigma tan(phi_w), with sigma = W cos / A and
    tau = W sin / A (solved by bisection)."""
    W = mass_g / 1000.0 * 9.80665
    A = area_mm2 * 1e-6
    mu = math.tan(math.radians(phi_w_deg))
    lo, hi = 0.0, 89.9
    for _ in range(80):
        th = 0.5 * (lo + hi)
        t = math.radians(th)
        if W * math.sin(t) / A - (c_w_pa + W * math.cos(t) / A * mu) > 0:
            hi = th
        else:
            lo = th
    return 0.5 * (lo + hi)


def imu_ramp(rate=0.5, t_end=80.0, hz=20.0, start_deg=0.0, noise_deg=0.03, seed=0,
             slip_t=None, jolt_g=0.03):
    rng = np.random.default_rng(seed)
    t = np.arange(0, t_end, 1.0 / hz)
    deg = start_deg + rate * t + rng.normal(0, noise_deg, t.size)
    jolt = np.abs(rng.normal(0, 0.002, t.size))
    if slip_t is not None:
        k = np.searchsorted(t, slip_t)
        jolt[k:k + 2] += jolt_g
    return t, deg, jolt


def ring_frames(times, slip_t, px_per_mm=12.0, shape=(240, 480), x0_mm=10.0, accel_mm_s2=400.0,
                ring_mm=(25.0, 8.0), blur_px=1.0, noise=0.02, seed=0, creep_mm_s=0.0):
    """Side view in the plate frame: a ring (dark rectangle) on the plate line,
    still until slip_t, then sliding with a constant acceleration."""
    rng = np.random.default_rng(seed)
    H, W = shape
    frames = []
    xs, ys = _grid(shape)
    plate_row = H * 0.7
    for t in times:
        dt = max(0.0, t - slip_t)
        x = x0_mm + creep_mm_s * t + 0.5 * accel_mm_s2 * dt * dt
        xl = 40 + x * px_per_mm
        xr = xl + ring_mm[0] * px_per_mm
        yt = plate_row - ring_mm[1] * px_per_mm
        X = xs[None, :]
        Y = ys[:, None]
        hi = np.full((H * SS, W * SS), 0.9, np.float32)
        hi = np.where(Y > plate_row, 0.35, hi)                     # the plate edge
        hi = np.where((X >= xl) & (X <= xr) & (Y >= yt) & (Y <= plate_row), 0.1, hi)
        frames.append(_finish(_down(hi), blur_px, noise, rng))
    return frames


# ---------------------------------------------------------------------------
# Test 4: backlit grains for PSD
# ---------------------------------------------------------------------------

def particle_field(n=150, d50_px=30.0, gsd=1.4, shape=(768, 1024), aspect=(0.6, 1.0),
                   touch_frac=0.15, blur_px=0.8, noise=0.02, seed=0, max_tries=20000):
    """Ellipses with lognormal ECD (number median d50_px, geometric SD gsd).
    touch_frac of them are placed overlapping a neighbour by 10-25 % of the
    smaller radius (touching grains for the watershed). Returns the image and
    the true ECD, aspect, and whether each grain touches the image edge."""
    rng = np.random.default_rng(seed)
    H, W = shape
    ecd = np.exp(rng.normal(math.log(d50_px), math.log(gsd), n))
    ar = rng.uniform(aspect[0], aspect[1], n)
    ang = rng.uniform(0, math.pi, n)
    placed = []
    centres = []
    for i in range(n):
        r = ecd[i] / 2.0
        ok = False
        for _ in range(max_tries // n):
            if placed and rng.random() < touch_frac:
                j = rng.integers(len(placed))
                cj, rj = centres[j], ecd[placed[j]] / 2.0
                overlap = rng.uniform(0.10, 0.25) * min(r, rj)
                d = r + rj - overlap
                th = rng.uniform(0, 2 * math.pi)
                c = (cj[0] + d * math.cos(th), cj[1] + d * math.sin(th))
                others = [k for k in range(len(placed)) if k != j]
            else:
                c = (rng.uniform(-r, W + r), rng.uniform(-r, H + r))
                others = range(len(placed))
            clash = False
            for k in others:
                ck, rk = centres[k], ecd[placed[k]] / 2.0
                if math.hypot(c[0] - ck[0], c[1] - ck[1]) < (r + rk) * 1.08 + 2:
                    clash = True
                    break
            if not clash:
                ok = True
                break
        if ok:
            placed.append(i)
            centres.append(c)
    hi = np.full((H * SS, W * SS), 0.9, np.float32)
    xs, ys = _grid(shape)
    edge = []
    for idx, c in zip(placed, centres):
        r = ecd[idx] / 2.0
        a = r / math.sqrt(ar[idx])
        b = r * math.sqrt(ar[idx])
        ca, sa = math.cos(ang[idx]), math.sin(ang[idx])
        ext = a + 2
        x0, x1 = max(0, int((c[0] - ext + 0.5) * SS)), min(W * SS, int((c[0] + ext + 1.5) * SS))
        y0, y1 = max(0, int((c[1] - ext + 0.5) * SS)), min(H * SS, int((c[1] + ext + 1.5) * SS))
        if x1 <= x0 or y1 <= y0:
            edge.append(True)
            continue
        X = xs[x0:x1][None, :] - c[0]
        Y = ys[y0:y1][:, None] - c[1]
        u = X * ca + Y * sa
        v = -X * sa + Y * ca
        inside = (u / a) ** 2 + (v / b) ** 2 <= 1.0
        sub = hi[y0:y1, x0:x1]
        sub[inside] = 0.1
        # half-axis extents of the rotated ellipse
        hx = math.sqrt((a * ca) ** 2 + (b * sa) ** 2)
        hy = math.sqrt((a * sa) ** 2 + (b * ca) ** 2)
        edge.append(c[0] - hx < 0.5 or c[1] - hy < 0.5 or c[0] + hx > W - 1.5 or c[1] + hy > H - 1.5)
    img = _finish(_down(hi), blur_px, noise, rng)
    truth = {"ecd_px": ecd[placed], "aspect": ar[placed], "edge": np.array(edge, bool),
             "d50_px": d50_px, "gsd": gsd, "n": len(placed)}
    return img, truth


def lognormal_quantile(d50, gsd, q, weight="number"):
    """Analytic quantile of a lognormal PSD (Hatch-Choate for volume)."""
    from scipy.stats import norm
    s = math.log(gsd)
    med = d50 * math.exp(3 * s * s) if weight == "volume" else d50
    return med * math.exp(norm.ppf(q) * s)


def micrometer_image(um_per_px=1.55, spacing_um=10.0, shape=(400, 600), blur_px=0.8,
                     noise=0.02, seed=0):
    rng = np.random.default_rng(seed)
    H, W = shape
    x = np.arange(W)
    period = spacing_um / um_per_px
    line = (np.mod(x, period) < 0.25 * period).astype(np.float32)
    img = np.tile(0.85 - 0.6 * line, (H, 1))
    return _finish(img, blur_px, noise, rng), {"um_per_px": um_per_px}


# ---------------------------------------------------------------------------
# Test 5: orifice cup on the balance
# ---------------------------------------------------------------------------

def beverloo_rate_g_s(D_mm, C, k, d_mm, rho_b):
    D = (D_mm - k * d_mm) / 1000.0
    if D <= 0:
        return 0.0
    return 1000.0 * C * rho_b * math.sqrt(9.80665) * D ** 2.5


def balance_stream(rate_g_s, mass_g=5.0, hz=10.0, t_open=2.0, t_end=None, noise_g=0.0003,
                   lag_s=0.25, seed=0, dt_sim=0.001, start_g=0.0):
    """Mass on the catch beaker: flat, a ramp at rate_g_s after t_open until
    mass_g has left the cup, flat again; seen through a first-order lag."""
    rng = np.random.default_rng(seed)
    dur = mass_g / rate_g_s if rate_g_s > 0 else float("inf")
    t_end = t_end if t_end is not None else t_open + min(dur, 120.0) + 3.0
    tt = np.arange(0, t_end, dt_sim)
    true = np.clip((tt - t_open) * rate_g_s, 0, mass_g) + start_g
    seen = np.empty_like(true)
    y = true[0]
    a = dt_sim / (lag_s + dt_sim) if lag_s > 0 else 1.0
    for i, v in enumerate(true):
        y += a * (v - y)
        seen[i] = y
    ts = np.arange(0, t_end, 1.0 / hz)
    m = np.interp(ts, tt, seen) + rng.normal(0, noise_g, ts.size)
    return ts, np.round(m, 4), {"rate_g_s": rate_g_s, "t_open": t_open}


# ---------------------------------------------------------------------------
# Test 7: rotating drum
# ---------------------------------------------------------------------------

def drum_image(angle_deg, fill=0.4, px_per_mm=12.0, drum_mm=40.0, shape=(600, 600), rough_px=0.6,
               curve_px=0.0, blur_px=1.0, noise=0.02, seed=0, ribs=24):
    """Axial view of a drum (bright rear wall) with a dark powder bed whose
    free surface is a line at angle_deg (rising to the left) through the
    chord that leaves `fill` of the area below it. curve_px bends it into
    an S (as at higher speeds)."""
    rng = np.random.default_rng(seed)
    H, W = shape
    R = drum_mm / 2.0 * px_per_mm
    cx, cy = W / 2.0, H / 2.0
    # chord offset d (below the centre) leaving `fill` of the disc under it
    lo, hi_ = -R, R
    for _ in range(60):
        d = 0.5 * (lo + hi_)
        seg = R * R * math.acos(d / R) - d * math.sqrt(R * R - d * d)      # area beyond distance d
        if seg / (math.pi * R * R) > fill:
            lo = d
        else:
            hi_ = d
    d = 0.5 * (lo + hi_)
    xs, ys = _grid(shape)
    X = xs[None, :] - cx
    Y = ys[:, None] - cy
    th = math.radians(angle_deg)
    # normal pointing down into the bed (image y down); surface rises to the left
    nx, ny = -math.sin(th), math.cos(th)
    s = X * nx + Y * ny                            # signed distance below the line through the centre
    along = X * math.cos(th) + Y * math.sin(th)
    bump = curve_px * np.sin(math.pi * np.clip(along / R, -1, 1))
    rough = np.interp(along, np.linspace(-R, R, 400), _smooth_noise(400, 3, rough_px, rng))
    r2 = X * X + Y * Y
    img = np.full((H * SS, W * SS), 0.15, np.float32)        # outside the drum: dark bezel
    img = np.where(r2 <= R * R, 0.9, img)
    bed = (r2 <= R * R) & (s >= d + bump + rough)
    img = np.where(bed, 0.1, img)
    if ribs:
        ang = np.arctan2(Y, X)
        rib = (r2 <= R * R) & (r2 >= (R - 0.8 * px_per_mm) ** 2) & (np.mod(ang, 2 * math.pi / ribs) < 0.05)
        img = np.where(rib, 0.3, img)
    return _finish(_down(img), blur_px, noise, rng), {"angle_deg": angle_deg, "center": (cx - 0.0, cy - 0.0),
                                                      "radius_px": R, "chord_d_px": d}


def drum_angle_series(rpm, seconds=60.0, fps=10.0, start_deg=42.0, stop_deg=34.0, sd=1.0,
                      dynamic_deg=None, noise=0.3, seed=0):
    """Angle per frame: avalanching (sawtooth) at low speed, or a steady
    rolling angle with noise when dynamic_deg is given."""
    rng = np.random.default_rng(seed)
    t = np.arange(0, seconds, 1.0 / fps)
    if dynamic_deg is not None:
        return t, dynamic_deg + rng.normal(0, noise, t.size), {"starts": [], "stops": []}
    rate = rpm * 6.0                                 # deg/s of rigid rotation
    step = rate / fps
    ang = np.empty(t.size)
    a = stop_deg + rng.normal(0, sd)
    target = start_deg + rng.normal(0, sd)
    starts, stops = [], []
    for i in range(t.size):
        if a + step >= target:
            frac = (target - a) / step               # part of the frame before the avalanche
            starts.append(target)
            stop = stop_deg + rng.normal(0, sd)
            stops.append(stop)
            a = stop + (1.0 - frac) * step
            target = start_deg + rng.normal(0, sd)
        else:
            a += step
        ang[i] = a
    return t, ang + rng.normal(0, noise, t.size), {"starts": starts, "stops": stops}


# ---------------------------------------------------------------------------
# Test 8: unconfined compression on the load cell
# ---------------------------------------------------------------------------

def ucs_stream(peak_g, hz=80.0, speed_mm_s=0.1, contact_s=5.0, stiff_g_mm=None, self_g=12.0,
               noise_g=0.002, seed=0, after_frac=0.3, t_end=None):
    rng = np.random.default_rng(seed)
    stiff = stiff_g_mm if stiff_g_mm else max(peak_g / 0.6, 1e-6)     # peak at 0.6 mm of travel
    t_peak = contact_s + peak_g / stiff / speed_mm_s
    t_end = t_end if t_end is not None else t_peak + 6.0
    t = np.arange(0, t_end, 1.0 / hz)
    f = np.where(t < contact_s, 0.0, (t - contact_s) * speed_mm_s * stiff)
    f = np.where(t > t_peak, peak_g * after_frac, np.minimum(f, peak_g))
    g = self_g + f + rng.normal(0, noise_g, t.size)
    return t, g, {"peak_g": peak_g, "self_g": self_g}


# ---------------------------------------------------------------------------
# Test 9: spread layer, top-down
# ---------------------------------------------------------------------------

def spread_image(coverage_void=0.06, n_streaks=3, streak_w_px=6, shape=(300, 1000), seed=0,
                 blur_px=0.8, noise=0.03):
    """Coupon (dark steel) with a bright powder layer; random voids and
    streaks along x (the spreading direction). Returns truth coverage and
    streak area fraction (of the coupon)."""
    rng = np.random.default_rng(seed)
    H, W = shape
    covered = np.ones((H, W), bool)
    # voids: random blobs
    field = ndi.gaussian_filter(rng.normal(0, 1, (H, W)), 6)
    thr = np.quantile(field, coverage_void)
    covered &= field > thr
    streak = np.zeros((H, W), bool)
    for _ in range(n_streaks):
        y = rng.integers(20, H - 20)
        x0 = rng.integers(0, W // 3)
        x1 = rng.integers(2 * W // 3, W)
        streak[y:y + streak_w_px, x0:x1] = True
    covered &= ~streak
    tex = ndi.gaussian_filter(rng.normal(0, 1, (H, W)), 1.0) * 0.08
    img = np.where(covered, 0.75 + tex, 0.2)
    truth = {"coverage": float(covered.mean()), "streak_frac": float(streak.mean())}
    return _finish(img, blur_px, noise, rng), truth


# ---------------------------------------------------------------------------
# Test 10: charge amplifier
# ---------------------------------------------------------------------------

def charge_stream(dq_nc, hz=10.0, t_dose=(5.0, 8.0), drift_nc_s=0.01, noise_nc=0.03, t_end=14.0,
                  tau_s=0.4, seed=0):
    rng = np.random.default_rng(seed)
    t = np.arange(0, t_end, 1.0 / hz)
    t0, t1 = t_dose
    frac = np.clip((t - t0) / (t1 - t0), 0, 1)
    after = np.where(t > t1, 1 - np.exp(-(t - t1) / tau_s), 0.0)
    q = dq_nc * (0.85 * frac + 0.15 * after) + drift_nc_s * t + rng.normal(0, noise_nc, t.size)
    return t, q, {"dq_nc": dq_nc}


# ---------------------------------------------------------------------------
# Test 6: uptake
# ---------------------------------------------------------------------------

def uptake_series(u_eq, tau_h, times_h=(0, 1, 2, 4, 8, 24), noise=0.2, seed=0):
    rng = np.random.default_rng(seed)
    t = np.asarray(times_h, float)
    return t, u_eq * (1 - np.exp(-t / tau_h)) + rng.normal(0, noise, t.size)
