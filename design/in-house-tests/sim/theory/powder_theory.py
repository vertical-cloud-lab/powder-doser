"""Textbook equation set for the ten in-house powder tests (design/in-house-tests/SPEC.md).

Everything here is computed, not measured. Each function names its source in the docstring.
Units are SI inside the functions (m, kg, s, Pa, C, V) unless a name says otherwise
(``_mm``, ``_g``, ``_deg``, ``_pct``).

Import it and call the functions, or run ``run_theory.py`` to evaluate every test for the two
reference powders of #196 and the 12 battery powders, and write ``results.json`` and the figures.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, asdict

import numpy as np

# ---------------------------------------------------------------------------------------------
# Constants (shared with sim/fea and sim/cfd; values given by the parent task)
# ---------------------------------------------------------------------------------------------
G = 9.81                    # m/s2
RHO_AIR = 1.184             # kg/m3, 25 C
MU_AIR = 1.85e-5            # Pa s, 25 C
D_VAPOUR = 2.5e-5           # m2/s, water vapour in air, 25 C
C_SAT_25 = 23.0e-3          # kg/m3, saturated water vapour density at 25 C
EPS0 = 8.854e-12            # F/m
RHO_WATER = 997.0           # kg/m3, 25 C
L_VAP = 2.44e6              # J/kg, latent heat of evaporation at 25 C
R_VAP = 461.5               # J/(kg K), gas constant of water vapour
E_BREAKDOWN = 3.0e6         # V/m, air breakdown field (uniform gap, about 1 cm; Paschen)


# ---------------------------------------------------------------------------------------------
# Powders
# ---------------------------------------------------------------------------------------------
@dataclass
class Powder:
    """Bulk properties used by the equations.

    rho_bulk, rho_tap: poured and tapped bulk density (kg/m3); d50: number median size (m);
    s_ln: log-width of a lognormal PSD (ln of the geometric standard deviation; assumed unless the
    source gives a distribution); aor_deg: angle of repose; rho_p: grain (true) density;
    mu_wall: powder-PLA wall friction coefficient (assumed 0.4 unless known); phi_i_deg: internal
    friction angle; c_pa: cohesion at 50-200 Pa (DEM run 6) or None; moisture_pct: as received.
    """
    name: str
    rho_bulk: float
    rho_tap: float
    d50: float
    aor_deg: float
    rho_p: float
    s_ln: float = 0.4
    mu_wall: float = 0.4
    phi_i_deg: float | None = None
    c_pa: float | None = None
    moisture_pct: float | None = None
    hygro_class: str = "none"
    source: str = ""

    @property
    def hausner(self) -> float:
        return self.rho_tap / self.rho_bulk

    @property
    def d90(self) -> float:
        """Number-weighted d90 of the lognormal (z = 1.2816)."""
        return self.d50 * math.exp(1.2816 * self.s_ln)

    @property
    def d10(self) -> float:
        return self.d50 * math.exp(-1.2816 * self.s_ln)


def _salt_ref_s_ln() -> float:
    """Log-width of the #196 reference size mix 0.361/0.425/0.489 mm in number fractions 0.3/0.4/0.3."""
    d = np.array([0.361, 0.425, 0.489])
    w = np.array([0.3, 0.4, 0.3])
    m = np.sum(w * np.log(d))
    return float(np.sqrt(np.sum(w * (np.log(d) - m) ** 2)))


SALT_DRY = Powder("salt-like dry (DEM ref)", 1249.0, 1337.0, 0.425e-3, 21.9, 2165.0,
                  s_ln=_salt_ref_s_ln(), mu_wall=0.4, phi_i_deg=24.8, c_pa=6.6, moisture_pct=0.05,
                  hygro_class="salt-NaCl",
                  source="#196 runs 2, 5, 6 (LIGGGHTS, real-size salt spheres); AoR 32 deg handbook")
COHESIVE = Powder("cohesive Bo 5 (DEM ref)", 1023.0, 1186.0, 0.425e-3, 39.3, 2165.0,
                  s_ln=_salt_ref_s_ln(), mu_wall=0.4, phi_i_deg=32.3, c_pa=11.9, moisture_pct=None,
                  hygro_class="none",
                  source="#196 runs 2, 5, 6 (SJKR 6 kJ/m3, Bo about 5)")

# Battery powders: literature_powder_properties.csv of #196 (commit e8811bd,
# docs/physics-simulations/runs/heldout-powders/data/). Handbook / class values, not measurements
# on our jars. s_ln and hygro_class are assumptions by powder class (marked in the README).
_BATTERY_ROWS = [
    # id, bulk g/mL, tapped g/mL, d50 um, AoR deg, true g/cm3, moisture %, s_ln (assumed), class
    ("salt", 1.19, 1.28, 425, 32, 2.165, 0.05, 0.30, "salt-NaCl"),
    ("white-rice-flour", 0.68, 0.80, 100, 45, 1.45, 11.7, 0.60, "starch"),
    ("brown-rice-flour", 0.68, 0.82, 130, 47, 1.45, 11.5, 0.60, "starch"),
    ("sodium-alginate", 0.55, 0.70, 120, 42, 1.65, 12.0, 0.60, "hydrocolloid"),
    ("calcium-lactate", 0.40, 0.55, 220, 40, 1.494, 0.5, 0.50, "hydrate"),
    ("carboxymethyl-cellulose", 0.60, 0.80, 60, 41, 1.60, 15.0, 0.60, "hydrocolloid"),
    ("xanthan-gum", 0.62, 0.77, 90, 35, 1.52, 12.0, 0.60, "hydrocolloid"),
    ("sodium-sulfate", 1.40, 1.68, 135, 32, 2.664, 0.06, 0.40, "salt-Na2SO4"),
    ("silicon-110-200", 1.25, 1.45, 106, 36, 2.33, 0.05, 0.30, "inert"),
    ("silicon-325", 0.77, 1.00, 25, 43, 2.33, 0.10, 0.70, "inert"),
    ("alsi10mg", 1.35, 1.60, 42, 30, 2.67, 0.03, 0.40, "inert"),
    ("barium-chloride", 1.30, 1.50, 300, 34, 3.097, 0.02, 0.40, "hydrate"),
]

BATTERY = [Powder(r[0], r[1] * 1000, r[2] * 1000, r[3] * 1e-6, r[4], r[5] * 1000, s_ln=r[7],
                  moisture_pct=r[6], hygro_class=r[8],
                  source="#196 literature_powder_properties.csv (class/handbook values)")
           for r in _BATTERY_ROWS]

PLA_DENSITY = 1240.0        # kg/m3


# =============================================================================================
# Test 1. Heap angle of repose on a pedestal
# =============================================================================================
def heap_on_pedestal(D_ped: float, aor_deg: float, rho_heap: float) -> dict:
    """Cone on a fixed base (ISO 4324 geometry): h = R tan(theta), V = pi R^2 h / 3, m = rho V.

    A cohesive heap ends in a cliff at the rim (#196 run 2), so the cone is a lower bound on
    its height and mass.
    """
    R = D_ped / 2
    h = R * math.tan(math.radians(aor_deg))
    V = math.pi * R ** 2 * h / 3
    return {"h_mm": h * 1e3, "V_mm3": V * 1e9, "m_g": rho_heap * V * 1e3,
            "flank_mm": R / math.cos(math.radians(aor_deg)) * 1e3}


def apparent_angle_finite_distance(aor_deg: float, R: float, D_cam: float) -> float:
    """Silhouette slope of a cone seen by a pinhole camera at distance D_cam from the axis, level
    with the base: tan(theta_app) = tan(theta) * sqrt(1 - (R/D_cam)^2).

    Derivation: the silhouette generators pass through the apex and the tangent points of the base
    circle seen from the camera, (R^2/D, +-R sqrt(1 - R^2/D^2)) (elementary projective geometry).
    """
    t = math.tan(math.radians(aor_deg)) * math.sqrt(1 - (R / D_cam) ** 2)
    return math.degrees(math.atan(t))


def aor_fit_sigma(aor_deg: float, D_ped: float, d_grain: float, px: float,
                  rough_frac: float = 0.3, edge_noise_px: float = 0.2,
                  fit_lo: float = 0.15, fit_hi: float = 0.85) -> dict:
    """Standard error of one flank angle from a least-squares line fit.

    Slope variance of a straight-line fit to N points spread evenly over a length L with
    independent scatter sigma perpendicular to the line: var = 12 sigma^2 / (N L^2)
    (e.g. Taylor, An Introduction to Error Analysis, 2nd ed., ch. 8). Two scatter sources:
    grain-scale roughness of the silhouette (sigma_r = rough_frac * d, correlated over about one
    grain: N_r = L / (sqrt(pi) d) independent points, sqrt(pi) d being the integral scale of the
    roughness used in aor_fit_mc) and edge-detection noise (edge_noise_px pixels per image row;
    N_px = rows in the fit window). Pixel noise is horizontal: its perpendicular part is
    sigma_px * sin(theta).
    """
    th = math.radians(aor_deg)
    R = D_ped / 2
    h = R * math.tan(th)
    L = (fit_hi - fit_lo) * R / math.cos(th)          # flank length inside the fit window
    n_rows = max(2.0, (fit_hi - fit_lo) * h / px)
    n_r = max(2.0, L / (math.sqrt(math.pi) * d_grain))
    s_r = rough_frac * d_grain
    s_px = edge_noise_px * px * math.sin(th)
    var = 12 * s_r ** 2 / (n_r * L ** 2) + 12 * s_px ** 2 / (n_rows * L ** 2)
    return {"sigma_flank_deg": math.degrees(math.sqrt(var)), "L_fit_mm": L * 1e3,
            "rows": n_rows, "grains_along_fit": n_r}


def aor_fit_mc(aor_deg: float, D_ped: float, d_grain: float, px: float, rng: np.random.Generator,
               rough_frac: float = 0.3, edge_noise_px: float = 0.2, subpixel: bool = True,
               n_trials: int = 300, fit_lo: float = 0.15, fit_hi: float = 0.85) -> dict:
    """Monte Carlo of the flank fit on synthetic silhouettes.

    A straight flank with a rough edge (Gaussian-filtered white noise, correlation length one grain,
    SD rough_frac * d perpendicular to the flank) is sampled once per pixel row. The edge is found
    with sub-pixel noise (edge_noise_px) or by thresholding to whole pixels. A line x = a + b y is
    fitted between 15 % and 85 % of the height, as in SPEC test 1.
    """
    th = math.radians(aor_deg)
    R = D_ped / 2
    h = R * math.tan(th)
    y = np.arange(fit_lo * h + px / 2, fit_hi * h, px)
    s_flank = (h - y) / math.sin(th)                  # arc length from the apex
    L = R / math.cos(th)
    ds = d_grain / 8
    ns = int(L / ds) + 64
    k = np.arange(-24, 25) * ds
    ker = np.exp(-0.5 * (k / (d_grain / 2)) ** 2)
    errs = np.empty(n_trials)
    for i in range(n_trials):
        w = np.convolve(rng.standard_normal(ns), ker, mode="same")
        w *= rough_frac * d_grain / w.std()
        r = np.interp(s_flank, np.arange(ns) * ds, w)
        x = (h - y) / math.tan(th) + r / math.sin(th)
        if subpixel:
            x = x + rng.normal(0, edge_noise_px * px, x.size)
        else:
            x = (np.floor(x / px) + 0.5) * px
        b = np.polyfit(y, x, 1)[0]
        errs[i] = math.degrees(math.atan(-1 / b)) - aor_deg
    return {"mean_err_deg": float(errs.mean()), "sigma_deg": float(errs.std(ddof=1))}


# =============================================================================================
# Test 2. Bulk and tapped density in a graduated cylinder
# =============================================================================================
def column_height(m: float, rho: float, ID: float) -> float:
    """H = m / (rho * pi ID^2 / 4)."""
    return m / (rho * math.pi * ID ** 2 / 4)


def poured_cone_height(ID: float, aor_deg: float) -> float:
    """A centred pour leaves a cone of height (ID/2) tan(theta) on top of the column. Its volume
    equals a flat layer of one third of that height (cone volume = base x height / 3)."""
    return ID / 2 * math.tan(math.radians(aor_deg))


def bore_calibration_sigma(dH: float, sigma_H: float, dm_w: float, sigma_m: float = 0.2e-6) -> float:
    """Relative error of the bore area from a two-point water fill, A = dm_w / (rho_w dH).

    Two heights cancel the meniscus volume. Relative variance: (sigma_m/dm)^2 + 2 (sigma_H/dH)^2
    (each height read once).
    """
    return math.sqrt((sigma_m / dm_w) ** 2 + 2 * (sigma_H / dH) ** 2)


def density_sigma(H: float, sigma_H: float, sigma_A_rel: float, m: float, sigma_m: float = 0.2e-6,
                  surface_sigma: float = 0.0) -> float:
    """Relative error of rho = m / (A H): quadrature of mass, area, height reading and the
    uncertainty of the top surface (roughness or the residual of the cone correction)."""
    return math.sqrt((sigma_m / m) ** 2 + sigma_A_rel ** 2 + (sigma_H / H) ** 2 + (surface_sigma / H) ** 2)


def hausner_sigma(H0: float, HN: float, sigma_H: float, surface_sigma: float = 0.0) -> float:
    """HR = rho_tap / rho_bulk = H0 / HN at the same mass, so the bore area cancels.
    Relative error = sqrt((s0/H0)^2 + (sN/HN)^2) with s^2 = sigma_H^2 + surface^2."""
    s = math.sqrt(sigma_H ** 2 + surface_sigma ** 2)
    return math.sqrt((s / H0) ** 2 + (s / HN) ** 2)


def carr_index(hausner: float) -> float:
    """Carr index CI = 100 (1 - 1/HR) % (Carr 1965)."""
    return 100 * (1 - 1 / hausner)


def kawakita(N, a: float, b: float):
    """Kawakita and Ludde (1971): C = (V0 - VN)/V0 = a b N / (1 + b N). a = 1 - rho_bulk/rho_tap,inf
    is the limiting compaction, 1/b the number of taps to reach half of it."""
    N = np.asarray(N, dtype=float)
    return a * b * N / (1 + b * N)


def tap_impact_velocity(drop: float) -> float:
    """Free fall: v = sqrt(2 g h); a 3.0 mm drop gives 0.243 m/s."""
    return math.sqrt(2 * G * drop)


# =============================================================================================
# Test 3. Tilting plate, wall friction (mode A) and layer start (mode B)
# =============================================================================================
RING_ID, RING_H, RING_WALL = 25e-3, 6e-3, 1.2e-3


def ring_normal_stress(rho_b: float, lid_g: float, theta_deg: float = 0.0, ring_infill: float = 1.0) -> dict:
    """sigma_n = (m_lid + m_powder + m_ring) g cos(theta) / A (Jenike wall-friction test, ASTM D6128
    logic). With the shims out, the ring hangs on the powder by wall friction, so its weight reaches
    the plate through the powder. A = pi ID^2 / 4 = 491 mm2."""
    A = math.pi * RING_ID ** 2 / 4
    m_p = rho_b * A * RING_H
    m_ring = PLA_DENSITY * ring_infill * math.pi / 4 * ((RING_ID + 2 * RING_WALL) ** 2 - RING_ID ** 2) * RING_H
    m = m_p + m_ring + lid_g * 1e-3
    return {"m_powder_g": m_p * 1e3, "m_ring_g": m_ring * 1e3, "m_total_g": m * 1e3,
            "sigma_n_Pa": m * G * math.cos(math.radians(theta_deg)) / A}


def slip_angle_deg(mu_w: float, adhesion_pa: float, sigma_n: float) -> float:
    """Coulomb wall yield locus tau = mu_w sigma + a_w: slip when tan(theta) = mu_w + a_w / sigma_n
    (sigma_n evaluated at the slip angle; one fixed-point iteration is enough)."""
    th = math.atan(mu_w + adhesion_pa / sigma_n)
    for _ in range(5):
        th = math.atan(mu_w + adhesion_pa / (sigma_n * math.cos(th)))
    return math.degrees(th)


def ring_hang_check(rho_b: float, lid_g: float, mu_ring: float = 0.4, K: float = 0.5,
                    ring_infill: float = 1.0) -> dict:
    """Can wall friction on the ring's inner wall carry the ring once the shims are out?
    Capacity F = mu_ring K sigma_v,mean (pi ID H_ring), sigma_v,mean = m_lid g / A + rho_b g H_ring / 2
    (lateral pressure ratio K assumed 0.5). If F < m_ring g the ring settles onto the plate and its
    own friction on the plate adds to the measured force."""
    A = math.pi * RING_ID ** 2 / 4
    sv = lid_g * 1e-3 * G / A + rho_b * G * RING_H / 2
    F = mu_ring * K * sv * math.pi * RING_ID * RING_H
    m_ring = PLA_DENSITY * ring_infill * math.pi / 4 * ((RING_ID + 2 * RING_WALL) ** 2 - RING_ID ** 2) * RING_H
    return {"capacity_g": F / G * 1e3, "ring_g": m_ring * 1e3, "carried": F > m_ring * G}


def wall_locus_fit_sigma(sigma_n_list, theta_deg_list, sigma_theta_deg: float) -> dict:
    """Propagate the slip-angle error into the wall yield locus tau_i = sigma_i tan(theta_i)
    = mu_w sigma_i + a_w (weighted least squares, Taylor ch. 8)."""
    s = np.asarray(sigma_n_list)
    th = np.radians(theta_deg_list)
    st = s / np.cos(th) ** 2 * math.radians(sigma_theta_deg)       # sigma of tau_i
    w = 1 / st ** 2
    Sw, Sx, Sxx = w.sum(), (w * s).sum(), (w * s * s).sum()
    det = Sw * Sxx - Sx ** 2
    return {"sigma_mu": math.sqrt(Sw / det), "sigma_adhesion_Pa": math.sqrt(Sxx / det)}


def jolt_angle_error_deg(mu: float, a_n_over_g: float) -> float:
    """Early slip from a plate-normal jolt: slip when sin(th) = mu (cos(th) - a_n/g); returns the
    shift of the apparent slip angle (negative = early). Newton's second law in the plate frame."""
    th0 = math.atan(mu)
    th = th0
    for _ in range(50):
        f = math.sin(th) - mu * (math.cos(th) - a_n_over_g)
        df = math.cos(th) + mu * math.sin(th)
        th -= f / df
    return math.degrees(th - th0)


# =============================================================================================
# Test 4. PSD from images
# =============================================================================================
HQ_SENSOR_PX = (4056, 3040)         # IMX477 active pixels; 1.55 um pitch -> 6.29 x 4.71 mm
HQ_PIXEL = 1.55e-6
SLIDE_WINDOW = (40e-3, 30e-3)


def quantile_se_lognormal(s_ln: float, q: float, N: int) -> float:
    """Asymptotic standard error of ln(d_q) for N number-sampled grains from a lognormal:
    SE = s sqrt(q (1-q) / N) / phi(z_q) (Kendall and Stuart, sample quantiles)."""
    from scipy.stats import norm
    z = norm.ppf(q)
    return s_ln * math.sqrt(q * (1 - q) / N) / norm.pdf(z)


def n_needed_number_quantile(s_ln: float, q: float, rel_halfwidth: float, conf_z: float = 1.96) -> float:
    """N for the 95 % half-width of the number-weighted d_q to be within +-rel_halfwidth."""
    from scipy.stats import norm
    z = norm.ppf(q)
    k = s_ln * math.sqrt(q * (1 - q)) / norm.pdf(z)
    return (conf_z * k / math.log(1 + rel_halfwidth)) ** 2


def volume_weighted_ess_factor(s_ln: float) -> float:
    """Kish effective sample size of d^3 weights on a lognormal: N_eff / N = E[w]^2 / E[w^2]
    = exp(-9 s^2). Volume-weighted quantiles need roughly exp(9 s^2) times more grains."""
    return math.exp(-9 * s_ln ** 2)


def bootstrap_quantiles(s_ln: float, N: int, B: int, rng: np.random.Generator) -> dict:
    """B synthetic samples of N grains (lognormal, median 1) -> relative 95 % half-widths of the
    number- and volume-weighted d50 and d90."""
    x = np.sort(rng.lognormal(0.0, s_ln, size=(B, N)), axis=1)
    out = {}
    for q in (0.5, 0.9):
        nq = x[:, int(round(q * (N - 1)))]
        true_n = math.exp(s_ln * {0.5: 0.0, 0.9: 1.2815516}[q])
        lo, hi = np.percentile(nq / true_n, [2.5, 97.5])
        out[f"n_d{int(q*100)}"] = float((hi - lo) / 2)
    w = x ** 3
    cw = np.cumsum(w, axis=1)
    cw /= cw[:, -1:]
    for q in (0.5, 0.9):
        idx = np.argmax(cw >= q, axis=1)
        vq = x[np.arange(B), idx]
        true_v = math.exp(3 * s_ln ** 2 + s_ln * {0.5: 0.0, 0.9: 1.2815516}[q])
        lo, hi = np.percentile(vq / true_v, [2.5, 97.5])
        out[f"v_d{int(q*100)}"] = float((hi - lo) / 2)
    return out


def pixel_sizing_mc(n_px: float, rng: np.random.Generator, n_trials: int = 400) -> dict:
    """Area-equivalent diameter of a disc of n_px pixels diameter, measured by counting pixel
    centres inside it, at random sub-pixel positions. Returns bias and SD relative to the true d."""
    r = n_px / 2
    g = np.arange(-math.ceil(r) - 2, math.ceil(r) + 3)
    X, Y = np.meshgrid(g, g)
    res = np.empty(n_trials)
    for i in range(n_trials):
        cx, cy = rng.random(2)
        cnt = np.count_nonzero((X - cx) ** 2 + (Y - cy) ** 2 <= r * r)
        res[i] = 2 * math.sqrt(cnt / math.pi) / n_px - 1
    return {"bias": float(res.mean()), "sd": float(res.std(ddof=1))}


def psd_imaging_plan(p: Powder, coverage: float = 0.05, px_floor_count: float = 10.0) -> dict:
    """Pick the zoom so that d10 spans >= 10 px (assumed sizing floor), bounded by the lens
    (0.86-12.9 um/px), and count grains per field at a given area coverage:
    N_field = coverage * A_field / (pi/4 * d50^2 * exp(2 s^2)) (mean projected area of a
    number-lognormal)."""
    px = min(12.9e-6, max(0.86e-6, p.d10 / px_floor_count))
    fx, fy = HQ_SENSOR_PX[0] * px, HQ_SENSOR_PX[1] * px
    fx, fy = min(fx, SLIDE_WINDOW[0]), min(fy, SLIDE_WINDOW[1])
    a_mean = math.pi / 4 * p.d50 ** 2 * math.exp(2 * p.s_ln ** 2)
    n_field = coverage * fx * fy / a_mean
    d99 = p.d50 * math.exp(2.326 * p.s_ln)
    return {"px_um": px * 1e6, "field_mm": [fx * 1e3, fy * 1e3], "grains_per_field": n_field,
            "d10_px": p.d10 / px, "d99_over_field": d99 / fy,
            "edge_loss_d90": 1 - (fx - p.d90) * (fy - p.d90) / (fx * fy)}


# =============================================================================================
# Test 5. Orifice cup: Beverloo, jamming, Jenike arching
# =============================================================================================
ORIFICES_MM = [1.0, 1.5, 2.0, 2.54, 3.0, 4.0, 5.08, 6.0]
CUP_ID = 25e-3


def beverloo(D: float, d: float, rho_b: float, C: float = 0.58, k: float = 1.5) -> float:
    """Beverloo, Leniger and van de Velde (1961): W = C rho_b sqrt(g) (D - k d)^2.5 (kg/s).
    C = 0.58 and k = 1.5 matched the #196 DEM Hall run within 1 %; angular grains take k up to 2.9."""
    De = D - k * d
    return C * rho_b * math.sqrt(G) * De ** 2.5 if De > 0 else 0.0


def jamming_diameter(d: float, ratio: float = 4.94) -> float:
    """Clogging of cohesionless spheres in a flat-bottomed silo: D/d about 4.94 (Zuriguel et al.
    2005, Phys. Rev. E 71, 051303, divergence of the mean avalanche size). Below it, arches form
    within seconds."""
    return ratio * d


def jenike_H(theta_deg: float) -> float:
    """Jenike's arching function for a conical channel, about H = 2 + theta/60 (theta, half-angle
    from vertical, in degrees; a common fit to Jenike 1964's chart). Flat-bottomed cup with a
    funnel-flow channel: theta 0-45 deg, so H 2.0-2.75 (SPEC uses 2.2)."""
    return 2 + theta_deg / 60


def sigma_c_from_Dc(D_c: float, rho_b: float, H: float = 2.2) -> float:
    """Jenike arching: a stable arch of span D_c needs sigma_c = rho_b g D_c / H(theta)."""
    return rho_b * G * D_c / H


def Dc_from_sigma_c(sigma_c: float, rho_b: float, H: float = 2.2) -> float:
    return H * sigma_c / (rho_b * G)


def flat_cup_heel_mass(rho_b: float, crater_deg: float, D: float, R_cup: float = CUP_ID / 2) -> float:
    """Powder left in a flat-bottomed cup when flow stops: a ring sloping down to the orifice at the
    drained angle: V = 2 pi tan(theta) (R^3/3 - r R^2/2 + r^3/6), r = D/2 (integral of
    2 pi r (r - r0) tan(theta) dr). Uses the AoR as the drained angle (a lower bound)."""
    r = D / 2
    V = 2 * math.pi * math.tan(math.radians(crater_deg)) * (R_cup ** 3 / 3 - r * R_cup ** 2 / 2 + r ** 3 / 6)
    return rho_b * V


def stream_impact_offset(W: float, drop: float) -> dict:
    """Balance reading during steady flow. Impact force W v (v = sqrt(2 g h)) and the weight of
    the grains in flight, W t g (t = v/g), are equal, so the reading is the mass that has left the
    orifice (momentum balance; no correction needed in steady flow)."""
    v = math.sqrt(2 * G * drop)
    return {"impact_N": W * v, "in_flight_weight_N": W * v, "v_mps": v}


def rumpf_bond_number(d: float, rho_p: float, A_H: float = 1e-19, z0: float = 0.4e-9,
                      asperity: float = 0.2e-6) -> float:
    """Granular Bond number Bo = F_vdW / (m g) with Rumpf's asperity model
    F = A/(6 z0^2) [ r R/(r + R) + R/(1 + r/z0)^2 ] (Rumpf 1990; Rabinovich et al. 2000).
    Order of magnitude only (A_H, z0 and asperity radius r are assumed)."""
    R = d / 2
    r = asperity
    F = A_H / (6 * z0 ** 2) * (r * R / (r + R) + R / (1 + r / z0) ** 2)
    W = rho_p * G * math.pi * d ** 3 / 6
    return F / W


# =============================================================================================
# Test 6. Humidity chambers
# =============================================================================================
# Greenspan (1977), J. Res. NBS 81A, 89-96, Table 2: RH (%) over saturated solutions, 15-35 C.
# Transcribed values; check the third digit against the paper before quoting it.
GREENSPAN_T = np.array([15.0, 20.0, 25.0, 30.0, 35.0])
GREENSPAN = {
    "MgCl2":    {"rh": np.array([33.30, 33.07, 32.78, 32.44, 32.05]), "u25": 0.16},
    "Mg(NO3)2": {"rh": np.array([55.87, 54.38, 52.89, 51.40, 49.91]), "u25": 0.22},
    "NaCl":     {"rh": np.array([75.61, 75.47, 75.29, 75.09, 74.87]), "u25": 0.12},
    "KCl":      {"rh": np.array([85.92, 85.11, 84.34, 83.62, 82.95]), "u25": 0.26},
}


def greenspan_rh(salt: str, T_c: float) -> float:
    """RH over the saturated solution at T (cubic fit through Greenspan's 15-35 C values)."""
    c = np.polyfit(GREENSPAN_T, GREENSPAN[salt]["rh"], 3)
    return float(np.polyval(c, T_c))


def greenspan_drh_dT(salt: str, T_c: float = 25.0) -> float:
    c = np.polyfit(GREENSPAN_T, GREENSPAN[salt]["rh"], 3)
    return float(np.polyval(np.polyder(c), T_c))


def p_sat_hpa(T_c: float) -> float:
    """Magnus form, Alduchov and Eskridge (1996): e_s = 6.1094 exp(17.625 T / (T + 243.04)) hPa."""
    return 6.1094 * math.exp(17.625 * T_c / (T_c + 243.04))


def rh_at_offset(rh_source: float, T_source: float, dT: float) -> float:
    """RH at a point dT warmer than the slurry, at the same vapour pressure:
    RH = RH_src p_sat(T_src) / p_sat(T_src + dT). About -6 % of the RH per kelvin at 25 C."""
    return rh_source * p_sat_hpa(T_source) / p_sat_hpa(T_source + dT)


def gab(aw, Xm: float, C: float, K: float):
    """GAB sorption isotherm (Guggenheim-Anderson-de Boer; van den Berg 1985):
    X = Xm C K a / ((1 - K a)(1 - K a + C K a)), X in kg water per kg dry solid."""
    a = np.asarray(aw, dtype=float)
    return Xm * C * K * a / ((1 - K * a) * (1 - K * a + C * K * a))


# Class-typical GAB parameters (assumed; ranges in Al-Muhtaseb et al. 2002, Food Bioprod. Proc. 80,
# 118-128, for starches and hydrocolloids). "inert": monolayer only, about 1e-4 kg/kg.
GAB_CLASS = {
    "starch": (0.085, 15.0, 0.70),
    "hydrocolloid": (0.10, 10.0, 0.85),
}


def uptake_class(hygro_class: str, rh_pct: float) -> float | None:
    """Expected equilibrium water content (kg/kg dry) at an RH, by class. None = no simple
    isotherm (deliquescent salts above their DRH, hydrate transitions)."""
    a = rh_pct / 100
    if hygro_class in GAB_CLASS:
        return float(gab(a, *GAB_CLASS[hygro_class]))
    if hygro_class == "salt-NaCl":
        return 2e-4 * a if rh_pct < 75.3 else None   # adsorbed film only below the DRH
    if hygro_class in ("inert",):
        return 1e-4 * a
    if hygro_class == "salt-Na2SO4":
        return 2e-4 * a if rh_pct < 80 else None      # thenardite -> mirabilite at high RH
    if hygro_class == "hydrate":
        return 5e-4 * a if rh_pct < 85 else None      # stable hydrates below about 85-90 % RH
    return None


def layer_uptake_t95(L: float, rho_b: float, eps: float, dq_drh: float, tortuosity: float = 1.5,
                     D: float = D_VAPOUR, c_sat: float = C_SAT_25) -> dict:
    """Vapour diffusion into a powder layer of depth L open at the top (impermeable dish below)
    with local sorption equilibrium. Apparent diffusivity
    D_app = (D eps / tau) / (eps + rho_b (dq/dRH) / c_sat) (Crank, The Mathematics of Diffusion,
    ch. 14, diffusion with linear immobilisation). 95 % of the uptake at D_app t / L^2 = 1.129
    (Crank eq. 4.18, plane sheet)."""
    D_eff = D * eps / tortuosity
    D_app = D_eff / (eps + rho_b * dq_drh / c_sat)
    return {"D_app_m2s": D_app, "t95_s": 1.129 * L ** 2 / D_app,
            "capacity_factor": rho_b * dq_drh / c_sat / eps}


def flat_plate_hm(U: float, L: float, nu: float = 1.57e-5, D: float = D_VAPOUR) -> float:
    """Mass-transfer coefficient over a flat plate in laminar flow: Sh = 0.664 Re^0.5 Sc^(1/3)
    (Incropera, heat-mass analogy), h_m = Sh D / L."""
    Re = U * L / nu
    Sc = nu / D
    return 0.664 * math.sqrt(Re) * Sc ** (1 / 3) * D / L


def deliquescence_rate(h_m: float, A: float, rh_box: float, rh_surface: float,
                       c_sat: float = C_SAT_25) -> float:
    """Vapour supply to a deliquescing sample: J = h_m A c_sat (RH_box - RH_surface) (kg/s). Above
    the DRH the uptake rate is a property of the chamber, not the powder."""
    return h_m * A * c_sat * (rh_box - rh_surface) / 100


def exposure_error(t_open: float, h_m: float, A: float, drh: float, c_sat: float = C_SAT_25) -> float:
    """Upper bound of the mass exchanged while the dish is out of the box for t_open seconds:
    h_m A c_sat dRH t (kg), limited by external mass transfer."""
    return h_m * A * c_sat * drh / 100 * t_open


# =============================================================================================
# Test 7. Rotating drum
# =============================================================================================
def froude(rpm: float, D: float) -> float:
    """Fr = omega^2 R / g."""
    w = rpm * 2 * math.pi / 60
    return w * w * (D / 2) / G


def drum_counting(rpm: float, delta_deg: float, sd_deg: float, T: float = 90.0) -> dict:
    """Avalanches seen in a run of T seconds when the surface saw-tooths by delta_deg between
    avalanches (slumping regime): n = 6 rpm T / delta. SE of the mean angle = sd / sqrt(n); relative
    SE of the scatter (the cohesive index) about 1 / sqrt(2 n) (normal-theory SE of an SD)."""
    n = 6 * rpm * T / delta_deg
    return {"avalanches": n, "se_mean_deg": sd_deg / math.sqrt(n), "rel_se_scatter": 1 / math.sqrt(2 * n)}


def drum_regime(Fr: float) -> str:
    """Mellmann (2001), Powder Technol. 118, 251-270, Table 1. The bands overlap (fill degree and
    wall friction move the transitions): slumping 1e-5 to 1e-3, rolling 1e-4 to 1e-2, cascading
    1e-3 to 0.1, cataracting 0.1 to 1, centrifuging >= 1. Returns every band that contains Fr
    (slipping, which needs a smooth wall, is left out; the drum wall is ribbed)."""
    bands = (("slumping", 1e-5, 1e-3), ("rolling", 1e-4, 1e-2), ("cascading", 1e-3, 1e-1),
             ("cataracting", 1e-1, 1.0), ("centrifuging", 1.0, float("inf")))
    hit = [n for n, lo, hi in bands if lo <= Fr < hi]
    return "/".join(hit) if hit else "slumping (below 1e-5)"


def rpm_for_froude(Fr: float, D: float) -> float:
    return math.sqrt(Fr * G / (D / 2)) * 60 / (2 * math.pi)


def endwall_angle_shift(theta_deg: float, mu_w: float, h_flow: float, W: float) -> float:
    """Side-wall friction raises the surface angle of a flow between walls W apart:
    tan(theta_obs) = tan(theta) + mu_w h / W, h = flowing-layer depth (Taberlet et al. 2003,
    Phys. Rev. Lett. 91, 264301). Returns theta_obs - theta (deg)."""
    t = math.tan(math.radians(theta_deg)) + mu_w * h_flow / W
    return math.degrees(math.atan(t)) - theta_deg


# =============================================================================================
# Test 8. Unconfined strength in a split mould
# =============================================================================================
MOULD_D, MOULD_H = 20e-3, 40e-3


def janssen_K(phi_i_deg: float) -> float:
    """Lateral pressure ratio K = 1.1 (1 - sin(phi_i)) (EN 1991-4:2006, from Jaky's K0)."""
    return 1.1 * (1 - math.sin(math.radians(phi_i_deg)))


def janssen_sigma_v(z, D: float, mu_w: float, K: float, rho_b: float, sigma0: float):
    """Janssen (1895) with a surcharge sigma0 at z = 0:
    sigma_v(z) = s_inf + (sigma0 - s_inf) exp(-z/lam), lam = D / (4 mu_w K), s_inf = rho_b g lam.
    Wall normal stress sigma_h = K sigma_v."""
    lam = D / (4 * mu_w * K)
    s_inf = rho_b * G * lam
    z = np.asarray(z, dtype=float)
    return s_inf + (sigma0 - s_inf) * np.exp(-z / lam)


def ucs_mohr_coulomb(c: float, phi_deg: float) -> float:
    """Unconfined yield strength from a Mohr-Coulomb yield locus:
    sigma_c = 2 c cos(phi) / (1 - sin(phi)) (Mohr circle through the origin, tangent to the locus;
    Schulze, Powders and Bulk Solids, 2008, ch. 3)."""
    p = math.radians(phi_deg)
    return 2 * c * math.cos(p) / (1 - math.sin(p))


def consolidation_circle(sigma1: float, c: float, phi_deg: float) -> tuple[float, float]:
    """Centre and radius of a Mohr circle with major stress sigma1 tangent to tau = c + sigma tan(phi)."""
    p = math.radians(phi_deg)
    centre = (sigma1 - c * math.cos(p)) / (1 + math.sin(p))
    return centre, sigma1 - centre


def ffc_class(ffc: float) -> str:
    """Jenike (1964) classes as used by Schulze (2008): <1 not flowing, 1-2 very cohesive,
    2-4 cohesive, 4-10 easy-flowing, >10 free-flowing."""
    if ffc < 1:
        return "not flowing"
    if ffc < 2:
        return "very cohesive"
    if ffc < 4:
        return "cohesive"
    if ffc < 10:
        return "easy-flowing"
    return "free-flowing"


def column_self_weight_stress(rho_b: float, H: float = MOULD_H) -> float:
    """Axial stress at the foot of an unconfined column from its own weight, rho_b g H. A column
    whose strength at the foot is below this collapses when the mould opens."""
    return rho_b * G * H


# =============================================================================================
# Test 9. Blade spreading
# =============================================================================================
COUPON = (100e-3, 30e-3)


def layer_areal_mass(phi_layer: float, rho_p: float, gap: float) -> float:
    """Areal mass of a spread layer referred to the gap: m_A = phi rho_p gap (kg/m2), the layer
    packing fraction definition of #196 run 7."""
    return phi_layer * rho_p * gap


def passive_force_per_width(rho_b: float, h: float, phi_deg: float, c: float = 0.0) -> float:
    """Rankine passive resultant on a wall pushing a heap of height h:
    P = 0.5 Kp rho g h^2 + 2 c sqrt(Kp) h, Kp = (1 + sin phi)/(1 - sin phi) (N/m)."""
    s = math.sin(math.radians(phi_deg))
    Kp = (1 + s) / (1 - s)
    return 0.5 * Kp * rho_b * G * h ** 2 + 2 * c * math.sqrt(Kp) * h


# =============================================================================================
# Test 10. Faraday cup and charge amplifier
# =============================================================================================
ADS1115_FSR = [6.144, 4.096, 2.048, 1.024, 0.512, 0.256]


def charge_amp(Q: float, C_f: float) -> float:
    """Ideal charge amplifier: V_out = -Q / C_f (Horowitz and Hill, ch. 4)."""
    return -Q / C_f


def adc_charge_lsb(C_f: float, fsr: float = 4.096) -> float:
    """Charge per ADS1115 LSB: (FSR / 2^15) C_f."""
    return fsr / 32768 * C_f


def bias_drift_charge(I_b: float, t: float) -> float:
    """Charge integrated from the input bias current over a reading: Q = I_b t."""
    return I_b * t


def da_recovery_charge(DA: float, V_prev: float, C_f: float) -> float:
    """Dielectric absorption: after a short reset, the feedback capacitor recovers about DA x the
    previous voltage (Pease 1982, 'Understand capacitor soakage'), i.e. a false charge DA V C_f."""
    return DA * V_prev * C_f


def decay_fraction(t: float, R: float, C: float) -> float:
    """Fraction of a stored charge lost through a leakage R in time t: 1 - exp(-t / (R C))."""
    return 1 - math.exp(-t / (R * C))


def max_charge_per_mass(rho_p: float, d: float) -> float:
    """Upper bound on q/m for spheres of size d before the surface field reaches air breakdown:
    q/m = 6 eps0 E_b / (rho_p d) (Gauss's law; Matsusaka et al. 2010, Chem. Eng. Sci. 65, 5781)."""
    return 6 * EPS0 * E_BREAKDOWN / (rho_p * d)


def cup_capacitance_estimate(a: float = 20e-3, b: float = 35e-3, L: float = 50e-3, gap_bottom: float = 15e-3) -> float:
    """Coaxial estimate of the inner-cup-to-shield capacitance: 2 pi eps0 L / ln(b/a) plus the
    bottom disc eps0 pi a^2 / gap (fringing ignored; sim/fea solves the full field)."""
    return 2 * math.pi * EPS0 * L / math.log(b / a) + EPS0 * math.pi * a ** 2 / gap_bottom


def grain_mass(rho_p: float, d: float) -> float:
    return rho_p * math.pi * d ** 3 / 6


def as_dict(p: Powder) -> dict:
    d = asdict(p)
    d.update({"hausner": p.hausner, "d10_m": p.d10, "d90_m": p.d90})
    return d
