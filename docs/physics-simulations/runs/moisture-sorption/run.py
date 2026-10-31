#!/usr/bin/env python3
"""Moisture uptake -> capillary cohesion -> flow, for the "dose before and after
humid air" test on NaCl (and BaCl2.2H2O).

Chain (all closed-form or 1D PDE; numpy/scipy):
 1. GAB isotherm for adsorbed water below the deliquescence RH (DRH).
 2. 1D Fickian vapour diffusion into a powder layer with GAB sorption storage
    (method of lines, scipy BDF): RH(z, t).
 3. Kelvin radius of a saturated-brine meniscus, r* = g Vm / (R T ln(DRH/RH)),
    decides whether a particle-scale brine bridge can span the asperity gap H;
    Kelvin-limited bridge volume; above DRH the bridge grows from the vapour
    flux (deliquescence, uniform wicking assumed).
 4. Capillary force: Rabinovich et al. (2005) sphere-sphere bridge formula
    (Willett et al. 2000 closed form for comparison) -> granular Bond number.
 5. Bo -> Rumpf (1970) tensile strength -> Mohr-Coulomb unconfined yield
    strength -> ffc at the doser's consolidation stress and Jenike critical
    outlet, compared with the 1.07 mm core-tip annulus gap and the 3 mm exit.

Usage: python run.py   (about 10 s, 1 core).  Writes result.json and
moisture_sorption.png next to this file.
"""
import json
import os
import platform
import time

os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")

import numpy as np
import scipy
from scipy.integrate import solve_ivp
from scipy.sparse import diags
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

T0 = time.time()
HERE = os.path.dirname(os.path.abspath(__file__))

# ------------------------------------------------------------- constants
g = 9.81
Rgas, T = 8.314462, 298.15
RT = Rgas * T
VM = 1.807e-5                 # m3/mol, molar volume of liquid water
P_SAT = 3169.9                # Pa, water at 25 C
C_SAT = P_SAT * 0.018015 / RT  # kg/m3 saturated vapour density
D_V = 2.178e-5 * (T / 273.15) ** 1.81   # m2/s water vapour in air (Massman 1998)
GAMMA_W = 0.0720              # N/m pure water, 25 C
GAMMA_MONO = 0.299e-6         # kg/m2, one adsorbed water monolayer (1.0e19 molecules/m2)
A_HAM = 6e-20                 # J, Hamaker constant (assumed)
Z0 = 0.4e-9                   # m, contact separation for van der Waals
R_ASP = 100e-9                # m, asperity tip radius (assumed)
Z_COORD = 6                   # coordination number (assumed)
PHI_INT = np.radians(34.0)    # internal friction angle of the salt
H_CONE = 2.0 + 37.0 / 60.0    # Jenike H(theta), 37 deg cone
GAP, EXIT = 1.07e-3, 3.0e-3   # m, core-tip annulus gap and exit diameter
SIG1_DOSER = 400.0            # Pa, Janssen saturation stress (analytic-orifice-screw, mu_w = 0.4)
SIG1_CELL = 3000.0            # Pa, low-stress shear-cell standard
RH_LAB = 0.30                 # initial ("before") RH of the powder (assumed)
DELTA_BL = 2e-3               # m, still-air boundary layer above the bed (assumed)

GAB_C, GAB_K = 10.0, 0.9      # assumed GAB constants (per-area adsorption)

materials = {
    "NaCl": dict(rho_p=2165.0, d=0.425e-3, rho_b=1250.0, DRH=0.753, gamma=0.082,
                 brine_vol_per_kg_water=1.0 / (1197.0 * (1 - 0.2644))),
    "BaCl2.2H2O": dict(rho_p=3097.0, d=0.425e-3, rho_b=1250.0 * 3097.0 / 2165.0, DRH=0.90,
                       gamma=0.076, brine_vol_per_kg_water=1.0 / (1280.0 * (1 - 0.27))),
}
for m in materials.values():
    m["eps"] = 1 - m["rho_b"] / m["rho_p"]
    m["R"] = m["d"] / 2
    m["m_p"] = m["rho_p"] * np.pi * m["d"] ** 3 / 6
    m["W_p"] = m["m_p"] * g
    m["SSA"] = 6.0 / (m["rho_p"] * m["d"])          # m2/kg
    m["X_m"] = m["SSA"] * GAMMA_MONO                 # kg water / kg solid per monolayer
    m["D_eff"] = D_V * m["eps"] ** 1.5               # Bruggeman tortuosity


# ------------------------------------------------------------- isotherm
def gab_n(a):
    u = GAB_K * np.asarray(a, float)
    return GAB_C * u / ((1 - u) * (1 - u + GAB_C * u))


def gab_dn_da(a):
    u = GAB_K * np.asarray(a, float)
    return GAB_K * GAB_C * (1 + (GAB_C - 1) * u ** 2) / ((1 - u) ** 2 * (1 + (GAB_C - 1) * u) ** 2)


# ------------------------------------------------------------- bridges
def r_kelvin(a, mat):
    a = np.asarray(a, float)
    with np.errstate(divide="ignore", invalid="ignore"):
        r = mat["gamma"] * VM / (RT * np.log(mat["DRH"] / a))
    return np.where(a < mat["DRH"], r, np.inf)


def v_kelvin(a, H, mat):
    """Kelvin-limited brine bridge volume between two spheres separated by H."""
    r = r_kelvin(a, mat)
    R = mat["R"]
    with np.errstate(invalid="ignore"):
        V = np.pi * R * (2 * r - H) * (r + H / 2)
    return np.where(2 * r > H, V, 0.0)


def f_rabinovich(V, H, mat):
    V = np.asarray(V, float)
    R, gam = mat["R"], mat["gamma"]
    with np.errstate(divide="ignore", invalid="ignore", over="ignore"):
        dsp = 0.5 * H * (np.sqrt(1 + 2 * V / (np.pi * R * H ** 2)) - 1)
        F = 2 * np.pi * R * gam / (1 + H / (2 * dsp))
    return np.where(V > 0, np.nan_to_num(F, nan=0.0, posinf=2 * np.pi * R * gam), 0.0)


def f_willett(V, H, mat):
    V = np.asarray(V, float)
    R, gam = mat["R"], mat["gamma"]
    with np.errstate(divide="ignore", invalid="ignore"):
        s = (H / 2) * np.sqrt(R / V)
        F = 2 * np.pi * R * gam / (1 + 2.1 * s + 10.0 * s ** 2)
    return np.where(V > 0, np.nan_to_num(F, nan=0.0), 0.0)


def f_low():
    """Asperity-scale cohesion: van der Waals + water meniscus at an asperity
    contact (sphere-sphere, radius R_ASP), independent of RH."""
    return A_HAM * R_ASP / (12 * Z0 ** 2) + 2 * np.pi * GAMMA_W * R_ASP


def force(a, H, mat, V_liq=0.0):
    Vb = np.maximum(v_kelvin(a, H, mat), V_liq)
    return np.maximum(f_low(), f_rabinovich(Vb, H, mat))


def flow_chain(F, mat):
    eps = mat["eps"]
    sig_t = (1 - eps) / eps * F / mat["d"] ** 2              # Rumpf 1970
    s = np.sin(PHI_INT)
    sig_c = 2 * sig_t * s / (1 - s)                          # Mohr-Coulomb, tension cut at sig_t
    Bc = H_CONE * sig_c / (mat["rho_b"] * g)                 # Jenike critical outlet
    return dict(sigma_t_Pa=sig_t, sigma_c_Pa=sig_c, ffc_at_400Pa=SIG1_DOSER / sig_c,
                ffc_at_3kPa=SIG1_CELL / sig_c, Bc_mm=Bc * 1e3)


def verdict(Bc_mm):
    if Bc_mm < GAP * 1e3:
        return "flows (no cohesive arch over the 1.07 mm annulus gap)"
    if Bc_mm < EXIT * 1e3:
        return "arches over the annulus gap: more stalled increments expected"
    return "arches over the 3 mm exit: dosing expected to stall without agitation"


# ------------------------------------------------------------- vapour PDE
def run_bed(mat, rh_top, L, N=80, t_end=7200.0, a0=RH_LAB):
    dz = L / N
    D = mat["D_eff"] * C_SAT
    cap0 = mat["eps"] * C_SAT

    def rhs(t, a):
        flux = np.empty(N + 1)
        flux[0] = D * (rh_top - a[0]) / (dz / 2)
        flux[1:N] = D * (a[:-1] - a[1:]) / dz
        flux[N] = 0.0
        cap = cap0 + mat["rho_b"] * mat["X_m"] * gab_dn_da(a)
        return (flux[:-1] - flux[1:]) / (dz * cap)

    t_eval = np.minimum(np.concatenate([[0.0], np.logspace(-1, np.log10(t_end), 160)]), t_end)
    sp = diags([1.0, 1.0, 1.0], [-1, 0, 1], shape=(N, N))
    sol = solve_ivp(rhs, (0, t_end), np.full(N, a0), method="BDF", t_eval=t_eval,
                    jac_sparsity=sp, rtol=1e-7, atol=1e-10)
    z = (np.arange(N) + 0.5) * dz
    return sol.t, z, sol.y, sol.nfev


def liquid_from_flux(mat, rh, L, t):
    """Above DRH: vapour flux through the boundary layer is absorbed as brine and
    spread uniformly over depth L (wicking assumption). Returns bridge volume per
    contact (m3) and pore liquid saturation."""
    J = D_V / DELTA_BL * C_SAT * max(rh - mat["DRH"], 0.0)     # kg/m2/s
    w = J * np.asarray(t, float) / (mat["rho_b"] * L)          # kg water / kg solid
    Vbrine_per_particle = w * mat["m_p"] * mat["brine_vol_per_kg_water"]
    V_contact = Vbrine_per_particle / (Z_COORD / 2)
    sat = w * mat["rho_b"] * mat["brine_vol_per_kg_water"] / mat["eps"]
    return V_contact, sat, J


# ------------------------------------------------------------- runs
H_LIST = [50e-9, 200e-9, 1000e-9]
H0 = 200e-9
L_DISH, L_RES = 10e-3, 40e-3
RH_CASES = [0.40, 0.60, 0.75, 0.80]

nacl, bacl = materials["NaCl"], materials["BaCl2.2H2O"]
res_cases = {}
curves = {}
profiles75 = None
nfev_total = 0
for name, mat in materials.items():
    for rh in RH_CASES:
        for L in ((L_DISH, L_RES) if (name == "NaCl" and rh == 0.75) else (L_DISH,)):
            rh_bc = min(rh, mat["DRH"])
            t, z, A, nfev = run_bed(mat, rh_bc, L)
            nfev_total += nfev
            Vliq, sat, J = liquid_from_flux(mat, rh, L, t)
            F = np.array([force(A[:, i], H0, mat, V_liq=Vliq[i]) for i in range(len(t))])
            Bo = F / mat["W_p"]
            Bo_bed = Bo.mean(axis=1)
            a_th = mat["DRH"] * np.exp(-2 * mat["gamma"] * VM / (H0 * RT))
            frac_bridged = (F > 1.5 * f_low()).mean(axis=1)
            key = f"{name}_RH{int(rh*100)}_L{int(L*1e3)}mm"
            curves[key] = (t, Bo_bed)
            if name == "NaCl" and rh == 0.75 and L == L_DISH:
                profiles75 = (t, z, A, a_th)

            def t_first(cond):
                idx = np.where(cond)[0]
                return float(t[idx[0]]) if len(idx) else None

            ads_ppm = 1e6 * mat["X_m"] * gab_n(A.mean(axis=0))
            out = {"Bo_bed_t0": float(Bo_bed[0]),
                   "Bo_bed_at_t_s": {str(tt_): float(np.interp(tt_, t, Bo_bed)) for tt_ in (0.1, 1.0, 10.0, 100.0)},
                   "Bo_bed_10min": float(np.interp(600, t, Bo_bed)),
                   "Bo_bed_1h": float(np.interp(3600, t, Bo_bed)),
                   "mean_RH_1h": float(np.interp(3600, t, A.mean(axis=0))),
                   "t_mean_RH_within_1pct_of_top_s": t_first(np.abs(A.mean(axis=0) - rh_bc) < 0.01 * rh_bc),
                   "adsorbed_water_1h_ppm": float(np.interp(3600, t, ads_ppm)),
                   "bridging_threshold_RH": float(a_th),
                   "t_half_bed_bridged_s": t_first(frac_bridged >= 0.5),
                   "t_full_bed_bridged_s": t_first(frac_bridged >= 0.999)}
            if rh > mat["DRH"]:
                out["vapour_flux_g_m2_h"] = float(J * 3600 * 1e3)
                out["pore_saturation_1h"] = float(np.interp(3600, t, sat))
                out["t_to_pore_saturation_10pct_h"] = float(0.10 / (sat[-1] / t[-1]) / 3600)
            out.update({k: float(v) for k, v in flow_chain(np.interp(3600, t, Bo_bed) * mat["W_p"], mat).items()})
            out["verdict_after_1h"] = verdict(out["Bc_mm"])
            res_cases[key] = out
            print(key, {k: (round(v, 4) if isinstance(v, float) else v) for k, v in out.items()}, flush=True)

# equilibrium sweeps vs RH (for figure + table)
rh_grid = np.linspace(0.30, 0.95, 651)
eq = {}
for name, mat in materials.items():
    for H in H_LIST:
        Vliq_1h = np.array([liquid_from_flux(mat, r, L_DISH, 3600.0)[0] for r in rh_grid])
        F = np.array([force(r, H, mat, V_liq=v) for r, v in zip(rh_grid, Vliq_1h)])
        eq[(name, H)] = F / mat["W_p"]
thresholds = {f"{name},H={int(H*1e9)}nm": float(mat["DRH"] * np.exp(-2 * mat["gamma"] * VM / (H * RT)))
              for name, mat in materials.items() for H in H_LIST}
eq_table = {}
for name, mat in materials.items():
    for H in H_LIST:
        for rh in [RH_LAB] + RH_CASES:
            Vl = liquid_from_flux(mat, rh, L_DISH, 3600.0)[0]
            F = float(force(rh, H, mat, V_liq=Vl))
            fc = flow_chain(F, mat)
            eq_table[f"{name},H={int(H*1e9)}nm,RH={int(rh*100)}"] = {
                "Bo": round(F / mat["W_p"], 4), "sigma_c_Pa": round(fc["sigma_c_Pa"], 3),
                "ffc_at_400Pa": round(fc["ffc_at_400Pa"], 3), "Bc_mm": round(fc["Bc_mm"], 4),
                "verdict": verdict(fc["Bc_mm"])}

# force vs bridge volume (NaCl)
Vgrid = np.logspace(-22, -12, 400)
fv = {H: (f_rabinovich(Vgrid, H, nacl) / nacl["W_p"], f_willett(Vgrid, H, nacl) / nacl["W_p"]) for H in H_LIST}
VK75 = float(v_kelvin(0.75, H0, nacl))
VK60 = float(v_kelvin(0.60, 50e-9, nacl))
willett_vs_rab_at_VK75 = float(f_willett(VK75, H0, nacl) / f_rabinovich(VK75, H0, nacl))

# ------------------------------------------------------------- figure
BLUE, ORANGE, AQUA, YELLOW, MAGENTA, GREEN, VIOLET, RED = (
    "#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#6250d6", "#e34948")
INK, INK2 = "#0b0b0b", "#52514e"
plt.rcParams.update({"font.size": 8.5, "axes.edgecolor": INK2, "axes.labelcolor": INK,
                     "xtick.color": INK2, "ytick.color": INK2, "axes.grid": True,
                     "grid.color": "#e4e3df", "grid.linewidth": 0.6,
                     "axes.spines.top": False, "axes.spines.right": False})
fig, ax = plt.subplots(2, 3, figsize=(14.5, 8.6))
Hcol = {50e-9: BLUE, 200e-9: ORANGE, 1000e-9: AQUA}

# (a) isotherm
a_ = ax[0, 0]
for name, mat, col in (("NaCl", nacl, BLUE), ("BaCl2.2H2O", bacl, ORANGE)):
    rr = np.linspace(0.05, mat["DRH"] - 1e-3, 300)
    a_.plot(100 * rr, 1e6 * mat["X_m"] * gab_n(rr), color=col, lw=2,
            label=f"{name}: GAB adsorbed water (X_m = {1e6*mat['X_m']:.2f} ppm)")
    a_.axvline(100 * mat["DRH"], color=col, ls=":", lw=1.2)
    a_.text(100 * mat["DRH"] - 1, 11.3, f"DRH {100*mat['DRH']:.1f} %", rotation=90, ha="right",
            va="top", fontsize=7.5, color=INK2)
a_.set_xlim(0, 100)
a_.set_ylim(0, 14)
a_.set_xlabel("relative humidity (%)")
a_.set_ylabel("adsorbed water (ppm by mass)")
a_.legend(fontsize=7, loc="upper left", frameon=False)
a_.set_title("(a) GAB isotherm below deliquescence\n(C = 10, K = 0.9, assumed)", loc="left", fontsize=9.5)

# (b) Kelvin radius vs RH
b_ = ax[0, 1]
rr = np.linspace(0.30, 0.7529, 800)
b_.plot(100 * rr, r_kelvin(rr, nacl) * 1e9, color=BLUE, lw=2, label="NaCl brine meniscus r*")
for H in H_LIST:
    b_.axhline(H / 2 * 1e9, color=Hcol[H], ls="--", lw=1.2)
    b_.text(31, H / 2 * 1e9 * 1.12, f"H/2 for H = {int(H*1e9)} nm (bridge forms above this)",
            fontsize=7, color=INK2)
b_.set_yscale("log")
b_.set_xlim(30, 76)
b_.set_ylim(0.3, 3e3)
b_.set_xlabel("relative humidity (%)")
b_.set_ylabel("Kelvin radius r* (nm)")
b_.legend(fontsize=7, loc="lower right", frameon=False)
b_.set_title("(b) when can a brine bridge span the asperity gap?", loc="left", fontsize=9.5)

# (c) force vs volume
c_ = ax[0, 2]
for H in H_LIST:
    c_.plot(Vgrid * 1e18, fv[H][0], color=Hcol[H], lw=2, label=f"Rabinovich 2005, H = {int(H*1e9)} nm")
    c_.plot(Vgrid * 1e18, fv[H][1], color=Hcol[H], lw=1.2, ls="--")
c_.plot([], [], color=INK2, ls="--", lw=1.2, label="Willett 2000 closed form")
c_.axhline(f_low() / nacl["W_p"], color=INK2, lw=1, ls=":")
c_.text(2e-4, f_low() / nacl["W_p"] * 1.3, "asperity-scale vdW + meniscus", fontsize=7, color=INK2)
c_.plot([VK75 * 1e18], [f_rabinovich(VK75, H0, nacl) / nacl["W_p"]], "o", ms=8, mfc=ORANGE,
        mec="white", mew=1.5)
c_.annotate("Kelvin-limited bridge,\n75 % RH, H = 200 nm", (VK75 * 1e18, f_rabinovich(VK75, H0, nacl) / nacl["W_p"]),
            xytext=(1e-1, 2), fontsize=7, color=INK2, arrowprops=dict(arrowstyle="-", color=INK2, lw=0.8))
c_.set_xscale("log")
c_.set_yscale("log")
c_.set_xlim(1e-4, 1e6)
c_.set_ylim(1e-3, 300)
c_.set_xlabel("brine bridge volume per contact (µm³)")
c_.set_ylabel("granular Bond number F/(m g) (-)")
c_.legend(fontsize=7, loc="upper left", frameon=False)
c_.set_title("(c) capillary force vs bridge volume, NaCl d = 0.425 mm", loc="left", fontsize=9.5)

# (d) RH profiles 75 %
d_ = ax[1, 0]
t75, z75, A75, ath = profiles75
cols = [BLUE, ORANGE, AQUA, YELLOW, VIOLET]
for ti, col in zip((1.0, 5.0, 15.0, 40.0, 120.0), cols):
    i = np.argmin(np.abs(t75 - ti))
    d_.plot(100 * A75[:, i], z75 * 1e3, color=col, lw=2, label=f"t = {t75[i]:.0f} s")
d_.axvline(100 * ath, color=INK, ls="--", lw=1.2)
d_.annotate(f"bridging threshold {100*ath:.2f} %\n(H = 200 nm)", (100 * ath, 9.0), xytext=(40, 9.0),
            fontsize=7, color=INK2, va="center", arrowprops=dict(arrowstyle="-", color=INK2, lw=0.8))
d_.invert_yaxis()
d_.set_xlim(30, 77)
d_.set_xlabel("local relative humidity in the pores (%)")
d_.set_ylabel("depth below the bed surface (mm)")
d_.legend(fontsize=7, loc="upper left", frameon=False)
d_.set_title("(d) NaCl layer 10 mm, 30 -> 75 % RH: vapour diffusion", loc="left", fontsize=9.5)

# (e) Bo vs time
e_ = ax[1, 1]
for key, col, lab in (("NaCl_RH40_L10mm", BLUE, "NaCl 40 % RH"), ("NaCl_RH60_L10mm", AQUA, "NaCl 60 % RH"),
                      ("NaCl_RH75_L10mm", ORANGE, "NaCl 75 % RH, 10 mm layer"),
                      ("NaCl_RH75_L40mm", YELLOW, "NaCl 75 % RH, 40 mm layer"),
                      ("NaCl_RH80_L10mm", GREEN, "NaCl 80 % RH (> DRH), 10 mm"),
                      ("BaCl2.2H2O_RH80_L10mm", VIOLET, "BaCl2.2H2O 80 % RH, 10 mm")):
    tt, bb = curves[key]
    e_.plot(np.maximum(tt, 0.1), bb, color=col, lw=2, label=lab,
            ls="--" if key.startswith("BaCl2") else "-")
e_.set_xscale("log")
e_.set_yscale("log")
e_.set_xlim(0.1, 7200)
e_.set_ylim(1e-2, 300)
e_.set_xlabel("time in humid air (s)")
e_.set_ylabel("bed-averaged granular Bond number (-)")
e_.legend(fontsize=7, loc="center right", frameon=False)
e_.set_title("(e) Bond number vs exposure time (H = 200 nm)", loc="left", fontsize=9.5)

# (f) Jenike critical outlet vs RH
f_ = ax[1, 2]
for H in H_LIST:
    Bc = flow_chain(eq[("NaCl", H)] * nacl["W_p"], nacl)["Bc_mm"]
    f_.plot(100 * rh_grid, Bc, color=Hcol[H], lw=2, label=f"NaCl, H = {int(H*1e9)} nm")
Bcb = flow_chain(eq[("BaCl2.2H2O", H0)] * bacl["W_p"], bacl)["Bc_mm"]
f_.plot(100 * rh_grid, Bcb, color=VIOLET, lw=2, ls="--", label="BaCl2.2H2O, H = 200 nm")
f_.axhline(EXIT * 1e3, color=INK, ls="--", lw=1.2)
f_.text(31, EXIT * 1e3 * 1.25, "exit 3 mm", fontsize=7.5, color=INK)
f_.axhline(GAP * 1e3, color=INK2, ls=":", lw=1.2)
f_.text(31, GAP * 1e3 * 0.55, "annulus gap 1.07 mm", fontsize=7.5, color=INK2)
f_.set_yscale("log")
f_.set_xlim(30, 95)
f_.set_ylim(0.05, 1000)
f_.set_xlabel("relative humidity after exposure (%)  [> DRH: 1 h of uptake]")
f_.set_ylabel("Jenike critical outlet B_c (mm)")
f_.legend(fontsize=7, loc="upper left", frameon=False)
f_.set_title("(f) predicted arching (Rumpf + Mohr-Coulomb + Jenike)", loc="left", fontsize=9.5)

fig.suptitle("Humid-air exposure of salt: GAB sorption, vapour diffusion, Kelvin/brine bridges, "
             "Rabinovich capillary force, Bond number and arching (moisture-sorption, numpy/scipy)",
             fontsize=10.5)
fig.tight_layout(rect=[0, 0, 1, 0.96])
png = os.path.join(HERE, "moisture_sorption.png")
fig.savefig(png, dpi=95)

wall = time.time() - T0
res = {
    "id": "moisture-sorption",
    "method": "GAB isotherm + Fickian vapour diffusion + Kelvin brine bridges + Rabinovich capillary force -> Bond number -> Rumpf/Mohr-Coulomb/Jenike flow prediction",
    "code": "custom Python (numpy/scipy solve_ivp BDF/matplotlib)",
    "version": f"python {platform.python_version()}, numpy {np.__version__}, scipy {scipy.__version__}, matplotlib {matplotlib.__version__}",
    "status": "ran",
    "wall_s": round(wall, 2),
    "cores": 1,
    "key_results": {
        "inputs": {name: {k: (float(v) if isinstance(v, (float, np.floating)) else v)
                          for k, v in mat.items()} for name, mat in materials.items()},
        "D_vapour_air_m2_s": D_V, "c_sat_kg_m3": C_SAT, "H_asperity_gap_nm": [50, 200, 1000],
        "F_asperity_scale_N": float(f_low()),
        "Bo_dry_baseline_NaCl": float(f_low() / nacl["W_p"]),
        "Bo_max_full_bridge_NaCl": float(2 * np.pi * nacl["R"] * nacl["gamma"] / nacl["W_p"]),
        "bridging_threshold_RH": thresholds,
        "H_crit_for_bridging_at_75pct_RH_nm": float(2 * nacl["gamma"] * VM / (RT * np.log(nacl["DRH"] / 0.75)) * 1e9),
        "kelvin_radius_nm_NaCl": {f"RH={int(r*100)}": float(r_kelvin(r, nacl) * 1e9) for r in (0.40, 0.60, 0.75)},
        "V_kelvin_75pct_H200_um3": VK75 * 1e18,
        "willett_over_rabinovich_at_VK75": willett_vs_rab_at_VK75,
        "time_dependent_cases": res_cases,
        "equilibrium_table": eq_table,
        "pde_rhs_evaluations": int(nfev_total),
    },
    "notes": "Many inputs are assumed (GAB C, K; asperity height and radius; Hamaker constant; coordination; "
             "boundary layer; wicking above DRH; BaCl2.2H2O DRH and brine surface tension). See README.",
}


def _clean(o):
    if isinstance(o, dict):
        return {k: _clean(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [_clean(v) for v in o]
    if isinstance(o, (np.floating, float)):
        return None if not np.isfinite(o) else float(o)
    if isinstance(o, np.integer):
        return int(o)
    return o


with open(os.path.join(HERE, "result.json"), "w") as f:
    json.dump(_clean(res), f, indent=1)
print("thresholds", thresholds)
print("wall", round(wall, 2), "png bytes", os.path.getsize(png))
