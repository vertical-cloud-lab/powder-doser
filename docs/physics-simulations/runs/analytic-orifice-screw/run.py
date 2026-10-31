#!/usr/bin/env python3
"""Closed-form / reduced-order models for the auger powder doser.

Beverloo (and the uncorrected Hagen-type 5/2 law) orifice discharge, Jenike
critical arching outlet, Janssen reservoir stress, and a screw-conveyor
volumetric model with an explicit tilt-dependent fill law, compared with the
measured salt delivery and the LIGGGHTS DEM twin (PR #180).

Pure numpy/scipy; runs in about a second.  Usage:  python run.py
Writes result.json and analytic_orifice_screw.png next to this file.
"""
import json
import os
import platform
import time

os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")

import numpy as np
import scipy
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker

T0 = time.time()
HERE = os.path.dirname(os.path.abspath(__file__))

# ----------------------------------------------------------------- inputs
g = 9.81                      # m/s2
RPM = 60.0
REV_PER_S = RPM / 60.0        # 1 rev/s, so g/s == g/rev at 60 rpm

salt = dict(rho_p=2165.0, d50=0.425e-3, d_lo=0.36e-3, d_hi=0.49e-3,
            rho_b=1250.0, rho_b_lo=1200.0, rho_b_hi=1300.0, phi_deg=34.0)
alsi = dict(rho_p=2670.0, d50=35e-6, rho_b=1350.0)   # rho_b assumed ~0.5 rho_p

C_BEV = 0.58                  # Beverloo circular-orifice coefficient
K_BEV, K_LO, K_HI = 1.5, 1.4, 1.6
C_SLOT = 1.03                 # slot coefficient (Nedderman 1992; Myers & Sellers 1971)

D_EXIT = 3.0e-3               # m
R_IN, R_OUT = 0.43e-3, 1.5e-3  # core-tip annulus radii at the exit plane
D_HALL, D_CARNEY = 2.54e-3, 5.08e-3

# auger
D_BORE, D_CORE, PITCH, T_FLIGHT = 20.9e-3, 7.96e-3, 10.4e-3, 0.5e-3
FUNNEL_HALF_ANGLE = 37.0      # deg from the funnel axis

# measured salt delivery at 60 rpm (mg/rev) vs tilt from horizontal (deg)
tilt_meas = np.array([0.0, 22.5, 27.5, 45.0])
m_meas = np.array([28.0, 108.0, 105.0, 195.0])
m_meas_err = np.array([np.nan, 2.0, 11.0, np.nan])   # 22.5: range 106-110
m_dem = np.array([33.0, 71.0, 105.0, 153.0])          # LIGGGHTS twin, PR #180


# ------------------------------------------------------------- Beverloo
def bev_circle(D, d, rho_b, k=K_BEV, C=C_BEV, geff=g):
    De = max(D - k * d, 0.0)
    return C * rho_b * np.sqrt(geff) * De ** 2.5            # kg/s


def bev_annulus_slot(ri, ro, d, rho_b, k=K_BEV, C=C_SLOT, geff=g):
    """Annulus unrolled into an endless slot: W = C_s rho sqrt(g) L (b-kd)^1.5,
    L = mean circumference (no end correction because the slot is closed)."""
    b = ro - ri
    L = np.pi * (ri + ro)
    be = max(b - k * d, 0.0)
    return C * rho_b * np.sqrt(geff) * L * be ** 1.5


def bev_annulus_hydraulic(ri, ro, d, rho_b, k=K_BEV, C=C_BEV, geff=g):
    """Beverloo written as W = (4C/pi) rho A_eff sqrt(g Dh_eff) (exact for a
    circle) and applied to the annulus shrunk by k*d/2 at both walls."""
    ri_e, ro_e = ri + k * d / 2, ro - k * d / 2
    if ro_e <= ri_e:
        return 0.0
    A = np.pi * (ro_e ** 2 - ri_e ** 2)
    Dh = 2 * (ro_e - ri_e)
    return 4 * C / np.pi * rho_b * A * np.sqrt(geff * Dh)


def bev_annulus_area_equiv(ri, ro, d, rho_b, k=K_BEV, C=C_BEV, geff=g):
    """Circle with the same open area (ignores the narrow gap; shown as an
    over-estimate)."""
    Deq = 2 * np.sqrt(ro ** 2 - ri ** 2)
    return bev_circle(Deq, d, rho_b, k, C, geff)


rows = []


def add(name, fn, *args, rho_b):
    W = fn(*args, rho_b, k=K_BEV)
    Wlo = fn(*args, rho_b, k=K_HI)      # larger k -> smaller flow
    Whi = fn(*args, rho_b, k=K_LO)
    W0 = fn(*args, rho_b, k=0.0)        # uncorrected Hagen-type 5/2 law
    rows.append(dict(orifice=name, W_g_s=W * 1e3, W_g_s_k1p6=Wlo * 1e3,
                     W_g_s_k1p4=Whi * 1e3, W_g_s_k0_hagen_type=W0 * 1e3,
                     mg_per_rev_60rpm=W * 1e6 / REV_PER_S))


d = salt["d50"]
rb = salt["rho_b"]
add("salt, exit 3.00 mm (no core tip)", bev_circle, D_EXIT, d, rho_b=rb)
add("salt, core-tip annulus, slot", bev_annulus_slot, R_IN, R_OUT, d, rho_b=rb)
add("salt, core-tip annulus, hydraulic", bev_annulus_hydraulic, R_IN, R_OUT, d, rho_b=rb)
add("salt, core-tip annulus, area-equiv.", bev_annulus_area_equiv, R_IN, R_OUT, d, rho_b=rb)
add("salt, Hall 2.54 mm", bev_circle, D_HALL, d, rho_b=rb)
add("salt, Carney 5.08 mm", bev_circle, D_CARNEY, d, rho_b=rb)
add("AlSi10Mg, Hall 2.54 mm", bev_circle, D_HALL, alsi["d50"], rho_b=alsi["rho_b"])
add("AlSi10Mg, Carney 5.08 mm", bev_circle, D_CARNEY, alsi["d50"], rho_b=alsi["rho_b"])
for r in rows:
    r["s_per_50g"] = 50.0 / r["W_g_s"] if r["W_g_s"] > 0 else None

# sensitivity of the annulus (slot) capacity to grain size and bulk density
ann_sens = {}
for dd in (salt["d_lo"], salt["d50"], salt["d_hi"]):
    for rr in (salt["rho_b_lo"], salt["rho_b"], salt["rho_b_hi"]):
        ann_sens[f"d={dd*1e3:.3f}mm,rho_b={rr:.0f}"] = round(
            bev_annulus_slot(R_IN, R_OUT, dd, rr) * 1e6, 1)

gap = R_OUT - R_IN
gap_over_d = gap / d

# ----------------------------------------------- tilt: outlet-limited model
alpha = np.linspace(0, 60, 241)
sa = np.sin(np.radians(alpha))


def ann_mgrev(alpha_deg, k=K_BEV, rho_b=rb, dd=d):
    s = np.sin(np.radians(alpha_deg))
    return np.array([bev_annulus_slot(R_IN, R_OUT, dd, rho_b, k=k, geff=g * si)
                     for si in np.atleast_1d(s)]) * 1e6 / REV_PER_S


out_lim = ann_mgrev(alpha)
out_lim_lo = ann_mgrev(alpha, k=K_HI)
out_lim_hi = ann_mgrev(alpha, k=K_LO)
out_lim_at_meas = ann_mgrev(tilt_meas)

# ------------------------------------------- screw-conveyor volumetric model
A_ann = np.pi * (D_BORE ** 2 - D_CORE ** 2) / 4
V_swept = A_ann * PITCH                      # m3 per pitch (= per rev)
V_flight = A_ann * T_FLIGHT                  # axial-thickness approximation
V_p = V_swept - V_flight
m_full = rb * V_p * 1e6                      # mg per rev at 100 % fill
phi_eff_meas = m_meas / m_full
phi_eff_dem = m_dem / m_full


def lsq(x, y):
    X = np.column_stack([np.ones_like(x), x])
    coef, *_ = np.linalg.lstsq(X, y, rcond=None)
    pred = X @ coef
    res = y - pred
    return coef, pred, res


s_meas = np.sin(np.radians(tilt_meas))
# Fill law A (fitted): phi = phi0 + phi1 sin(alpha) -- linear in the axial
# gravity component (empirical linear inclination dependence, Owen & Cleary
# 2009-style).  Two free parameters fitted to the 4 measured points.
cA, predA, resA = lsq(s_meas, m_meas)
# Fill law B (fitted): phi = phi0 + phi1 sqrt(sin(alpha)) -- screw "push" plus
# a Beverloo outlet term with gravity projected on the outlet axis.
cB, predB, resB = lsq(np.sqrt(s_meas), m_meas)
# same laws fitted to the DEM numbers (for comparison only)
cA_dem, predA_dem, resA_dem = lsq(s_meas, m_dem)


def rmse(r):
    return float(np.sqrt(np.mean(r ** 2)))


# ---------------------------------------------------------------- Jenike
H_cone = 2.0 + FUNNEL_HALF_ANGLE / 60.0      # Jenike's approximation, conical
SIG_REF = 3000.0                              # Pa, ffc quoted at sigma_1 = 3 kPa
N_FF, N_LO, N_HI = 0.6, 0.4, 0.8              # FF curvature: sigma_c ~ sigma_1^n
FF, FF_LO, FF_HI = 1.5, 1.3, 1.8              # hopper flow factor (assumed)


def jenike_Bc(ffc, n=N_FF, ff=FF, rho_b=rb, H=H_cone, sref=SIG_REF):
    """Power-law flow function sigma_c = (sref/ffc)(sigma_1/sref)^n; critical
    point where sigma_c = sigma_1/ff; B_c = H sigma_c,crit/(rho_b g)."""
    s1 = sref * (ff / ffc) ** (1.0 / (1.0 - n))
    sc = s1 / ff
    return H * sc / (rho_b * g), sc


ffc_grid = np.logspace(0, np.log10(20), 200)
Bc_base = np.array([jenike_Bc(f)[0] for f in ffc_grid])
Bc_combos = np.array([[jenike_Bc(f, n=n, ff=ff)[0] for f in ffc_grid]
                      for n in (N_LO, N_HI) for ff in (FF_LO, FF_HI)])
Bc_min, Bc_max = Bc_combos.min(0), Bc_combos.max(0)
jen_tab = {}
for f in (1, 2, 4, 10):
    B, sc = jenike_Bc(f)
    allB = [jenike_Bc(f, n=n, ff=ff)[0] for n in (N_LO, N_HI) for ff in (FF_LO, FF_HI)]
    jen_tab[f"ffc={f}"] = dict(Bc_mm=round(B * 1e3, 3), sigma_c_crit_Pa=round(sc, 2),
                               Bc_mm_range=[round(min(allB) * 1e3, 4), round(max(allB) * 1e3, 1)])
# stress that acts in an arch spanning the outlet (strength needed to arch)
sig_arch_3mm = rb * g * D_EXIT / H_cone
H_plane = 1.0 + FUNNEL_HALF_ANGLE / 180.0     # plane-flow approximation for the slot
sig_arch_gap = rb * g * gap / H_plane

# mass-flow boundary for a cone (closed-form fit to Jenike's chart)
def theta_massflow(delta_deg, phiw_deg):
    dl, pw = np.radians(delta_deg), np.radians(phiw_deg)
    t = 90 - 0.5 * np.degrees(np.arccos((1 - np.sin(dl)) / (2 * np.sin(dl)))) \
        - 0.5 * (phiw_deg + np.degrees(np.arcsin(np.sin(pw) / np.sin(dl))))
    return float(t)


mf = {f"delta=40,phi_w={pw}": round(theta_massflow(40, pw), 1) for pw in (15, 20, 25)}

# ---------------------------------------------------------------- Janssen
K_J = 0.4
z = np.linspace(0, 0.10, 201)
jans = {}
for mu in (0.3, 0.4, 0.5):
    lam = D_BORE / (4 * mu * K_J)
    jans[mu] = (rb * g * lam * (1 - np.exp(-z / lam)), lam)
jan_tab = {f"mu_w={mu}": dict(sigma_inf_Pa=round(rb * g * jans[mu][1], 1),
                              length_scale_mm=round(jans[mu][1] * 1e3, 1),
                              sigma_at_50mm_Pa=round(float(np.interp(0.05, z, jans[mu][0])), 1))
           for mu in jans}
hydro_50 = rb * g * 0.05

# ---------------------------------------------------------------- figure
BLUE, ORANGE, AQUA, YELLOW, MAGENTA, GREEN, VIOLET, RED = (
    "#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#6250d6", "#e34948")
INK, INK2 = "#0b0b0b", "#52514e"
plt.rcParams.update({"font.size": 9, "axes.edgecolor": INK2, "axes.labelcolor": INK,
                     "xtick.color": INK2, "ytick.color": INK2, "axes.grid": True,
                     "grid.color": "#e4e3df", "grid.linewidth": 0.6,
                     "axes.spines.top": False, "axes.spines.right": False})
fig, ax = plt.subplots(2, 2, figsize=(11.0, 8.2))

# (a) mg/rev vs tilt
a = ax[0, 0]
a.fill_between(alpha, out_lim_lo, out_lim_hi, color=BLUE, alpha=0.15, lw=0)
a.plot(alpha, out_lim, color=BLUE, lw=2,
       label="outlet-limited: Beverloo slot through core-tip annulus,\n"
             "g sin(tilt), k = 1.5 (band 1.4-1.6), no fit")
a.plot(alpha, cA[0] + cA[1] * sa, color=ORANGE, lw=2,
       label=f"fill law A (fitted): {cA[0]:.0f} + {cA[1]:.0f} sin(tilt) mg/rev")
a.plot(alpha, cB[0] + cB[1] * np.sqrt(sa), color=VIOLET, lw=2, ls="--",
       label=f"fill law B (fitted): {cB[0]:.0f} + {cB[1]:.0f} sqrt(sin tilt) mg/rev")
a.errorbar(tilt_meas, m_meas, yerr=np.nan_to_num(m_meas_err), fmt="o", ms=8,
           color=INK, mfc=INK, capsize=3, label="measured (salt, 60 rpm)", zorder=5)
a.plot(tilt_meas, m_dem, "s", ms=8, mfc="white", mec=RED, mew=2,
       label="LIGGGHTS DEM twin (PR #180)", zorder=6)
a.set_xlabel("auger tilt from horizontal (deg)")
a.set_ylabel("delivered mass per revolution (mg/rev)")
a.set_xlim(-1, 60)
a.set_ylim(0, 330)
a.text(59, 8, f"full-fill volumetric capacity rho_b*V_pitch = {m_full:.0f} mg/rev\n(off scale); "
               f"measured data imply fill {100*phi_eff_meas.min():.1f}-{100*phi_eff_meas.max():.1f} %",
       fontsize=7.5, color=INK2, va="bottom", ha="right")
a.legend(fontsize=7, loc="upper left", frameon=False)
a.set_title("(a) delivery vs tilt: outlet and screw models", loc="left", fontsize=10)

# (b) Beverloo capacities
b = ax[0, 1]
names = [r["orifice"] for r in rows]
W = np.array([r["W_g_s"] for r in rows])
Wl = np.array([r["W_g_s_k1p6"] for r in rows])
Wh = np.array([r["W_g_s_k1p4"] for r in rows])
W0 = np.array([r["W_g_s_k0_hagen_type"] for r in rows])
yy = np.arange(len(rows))[::-1]
b.barh(yy, W, height=0.55, color=[BLUE] * 6 + [AQUA] * 2, edgecolor="white", lw=2)
b.errorbar(W, yy, xerr=[W - Wl, Wh - W], fmt="none", ecolor=INK, capsize=3, lw=1)
b.plot(W0, yy, "D", mfc="white", mec=ORANGE, mew=1.5, ms=6, label="k = 0 (uncorrected 5/2 law)")
b.axvline(0.195, color=INK2, ls=":", lw=1.2)
b.text(0.2, yy[0] + 0.45, "measured, 45 deg tilt: 0.195 g/s", fontsize=7, color=INK2)
b.set_yticks(yy)
b.set_yticklabels(names, fontsize=7.5)
b.set_xscale("log")
b.set_xlim(0.1, 8)
b.set_ylim(yy[-1] - 0.6, yy[0] + 0.9)
b.set_xticks([0.1, 0.2, 0.5, 1, 2, 5])
b.set_xticklabels(["0.1", "0.2", "0.5", "1", "2", "5"])
b.xaxis.set_minor_formatter(matplotlib.ticker.NullFormatter())
b.set_xlabel("outlet capacity (g/s); at 60 rpm 1 g/s = 1000 mg/rev")
b.legend(fontsize=7, loc="upper right", bbox_to_anchor=(1.0, 0.93), frameon=False)
b.set_title("(b) Beverloo capacity, k = 1.5 (bars: k 1.4-1.6)", loc="left", fontsize=10)

# (c) Jenike critical outlet
c = ax[1, 0]
c.fill_between(ffc_grid, Bc_min * 1e3, Bc_max * 1e3, color=VIOLET, alpha=0.15, lw=0,
               label="n 0.4-0.8, ff 1.3-1.8")
c.plot(ffc_grid, Bc_base * 1e3, color=VIOLET, lw=2, label="n = 0.6, ff = 1.5")
c.axhline(3.0, color=INK, lw=1.2, ls="--")
c.text(1.05, 3.4, "exit 3 mm", fontsize=8, color=INK)
c.axhline(gap * 1e3, color=INK2, lw=1.2, ls=":")
c.text(1.05, gap * 1e3 * 0.5, f"annulus gap {gap*1e3:.2f} mm", fontsize=8, color=INK2)
c.set_xscale("log")
c.set_yscale("log")
c.set_ylim(1e-2, 1e4)
c.set_xlabel("flow function coefficient ffc at sigma_1 = 3 kPa (-)")
c.set_ylabel("Jenike critical outlet diameter B_c (mm)")
c.legend(fontsize=7.5, loc="upper right", frameon=False)
c.set_title("(c) cohesive arching, cone 37 deg, rho_b 1250 kg/m3", loc="left", fontsize=10)

# (d) Janssen
dd_ = ax[1, 1]
for mu, col in zip((0.3, 0.4, 0.5), (BLUE, ORANGE, AQUA)):
    dd_.plot(z * 1e3, jans[mu][0], color=col, lw=2, label=f"Janssen, mu_w = {mu}, K = 0.4")
dd_.plot(z * 1e3, rb * g * z, color=INK2, lw=1.2, ls="--", label="hydrostatic rho_b g z")
dd_.set_xlim(0, 100)
dd_.set_ylim(0, 800)
dd_.set_xlabel("powder fill height above the auger (mm)")
dd_.set_ylabel("mean vertical stress at the auger (Pa)")
dd_.legend(fontsize=7.5, loc="upper left", frameon=False)
dd_.set_title("(d) reservoir stress, bore 20.9 mm", loc="left", fontsize=10)

fig.suptitle("Closed-form orifice / screw / arching / Janssen models for the auger doser "
             "(analytic-orifice-screw, numpy)", fontsize=11)
fig.tight_layout(rect=[0, 0, 1, 0.96])
png = os.path.join(HERE, "analytic_orifice_screw.png")
fig.savefig(png, dpi=105)

wall = time.time() - T0
res = {
    "id": "analytic-orifice-screw",
    "method": "Beverloo/Hagen-type orifice discharge, Jenike arching, Janssen, screw volumetric model",
    "code": "custom Python (numpy/scipy/matplotlib)",
    "version": f"python {platform.python_version()}, numpy {np.__version__}, scipy {scipy.__version__}, matplotlib {matplotlib.__version__}",
    "status": "ran",
    "wall_s": round(wall, 2),
    "cores": 1,
    "key_results": {
        "assumptions": {"rho_b_salt": rb, "d50_salt_mm": 0.425, "C": C_BEV, "k": K_BEV,
                        "k_band": [K_LO, K_HI], "C_slot": C_SLOT, "rho_b_AlSi10Mg_assumed": alsi["rho_b"]},
        "beverloo_table": [{k_: (round(v, 4) if isinstance(v, float) else v) for k_, v in r.items()} for r in rows],
        "annulus_gap_mm": round(gap * 1e3, 3),
        "annulus_gap_over_d50": round(gap_over_d, 2),
        "annulus_slot_capacity_mg_rev_vs_d_and_rho_b": ann_sens,
        "outlet_limited_mg_rev_at_measured_tilts_no_fit": dict(zip([str(t) for t in tilt_meas],
                                                                   [round(float(v), 1) for v in out_lim_at_meas])),
        "volumetric_full_fill_mg_rev": round(m_full, 0),
        "swept_volume_per_pitch_mm3": round(V_p * 1e9, 0),
        "effective_fill_fraction_measured_pct": [round(100 * v, 2) for v in phi_eff_meas],
        "effective_fill_fraction_DEM_pct": [round(100 * v, 2) for v in phi_eff_dem],
        "fill_law_A_fit": {"form": "m = a + b sin(tilt) [mg/rev] == rho_b V_p (phi0 + phi1 sin tilt)",
                           "a_mg_rev": round(cA[0], 1), "b_mg_rev": round(cA[1], 1),
                           "phi0_pct": round(100 * cA[0] / m_full, 3), "phi1_pct": round(100 * cA[1] / m_full, 3),
                           "pred_at_measured_tilts": [round(v, 1) for v in predA],
                           "residuals_mg_rev": [round(v, 1) for v in resA], "rmse_mg_rev": round(rmse(resA), 1),
                           "residual_vs_DEM_mg_rev": [round(v, 1) for v in (m_dem - predA)],
                           "fitted_parameters": 2, "data_points": 4},
        "fill_law_B_fit": {"form": "m = a + b sqrt(sin tilt)", "a_mg_rev": round(cB[0], 1),
                           "b_mg_rev": round(cB[1], 1), "pred_at_measured_tilts": [round(v, 1) for v in predB],
                           "residuals_mg_rev": [round(v, 1) for v in resB], "rmse_mg_rev": round(rmse(resB), 1),
                           "b_vs_beverloo_annulus_full_g": round(cB[1] / (bev_annulus_slot(R_IN, R_OUT, d, rb) * 1e6), 3)},
        "law_A_refit_to_DEM": {"a": round(cA_dem[0], 1), "b": round(cA_dem[1], 1),
                               "rmse_mg_rev": round(rmse(resA_dem), 1)},
        "jenike": {"H_cone": round(H_cone, 3), "sigma_ref_Pa": SIG_REF, "n": N_FF, "ff": FF,
                   "table": jen_tab, "stress_in_arch_over_3mm_exit_Pa": round(sig_arch_3mm, 1),
                   "stress_in_arch_over_annulus_gap_Pa": round(sig_arch_gap, 1),
                   "mass_flow_limit_half_angle_deg": mf},
        "janssen": {"K": K_J, "table": jan_tab, "hydrostatic_at_50mm_Pa": round(hydro_50, 1)},
    },
    "notes": "Closed-form models; fill laws A and B have 2 parameters each fitted to the 4 measured points "
             "(stated, with residuals). Outlet-limited curve and all Beverloo/Jenike/Janssen numbers are not fitted.",
}
with open(os.path.join(HERE, "result.json"), "w") as f:
    json.dump(res, f, indent=1)
print(json.dumps(res["key_results"], indent=1))
print("wall", wall, "png bytes", os.path.getsize(png))
