#!/usr/bin/env python
"""Evaluate powder_theory.py for tests 1-10: expected signals, uncertainty budgets, summary table.

Run:  OMP_NUM_THREADS=1 nice -n 10 /tmp/venv/bin/python run_theory.py
Writes results.json and fig_*.png next to this file (about 1-2 min, under 0.5 GB).
Everything is computed, not measured.
"""
from __future__ import annotations

import json
import math
import os
import sys
import time

import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import powder_theory as pt  # noqa: E402

PAL = ["#257de0", "#f47230", "#00b894", "#f2a600", "#ee7fac", "#008a17", "#6a4ce2", "#ec4647"]
TXT, TXT2, GRID = "#191919", "#666666", "#d9d9d9"
plt.rcParams.update({
    "font.size": 9, "text.color": TXT, "axes.labelcolor": TXT, "axes.edgecolor": TXT2,
    "xtick.color": TXT2, "ytick.color": TXT2, "axes.grid": True, "grid.color": GRID,
    "grid.linewidth": 0.6, "axes.spines.top": False, "axes.spines.right": False,
    "lines.linewidth": 1.6, "lines.markersize": 6, "legend.frameon": False, "figure.dpi": 150,
})

rng = np.random.default_rng(20261128)
T0 = time.time()
REFS = [pt.SALT_DRY, pt.COHESIVE]
ALL = REFS + pt.BATTERY
R: dict = {"status": "computed, not measured", "module": "powder_theory.py",
           "powders": {p.name: pt.as_dict(p) for p in ALL}}


def r3(x, n=3):
    """Round for JSON readability."""
    if isinstance(x, float):
        return float(f"{x:.{n}g}")
    if isinstance(x, dict):
        return {k: r3(v, n) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [r3(v, n) for v in x]
    return x


def rough_scale(p: pt.Powder) -> float:
    """Assumed silhouette roughness scale: one grain, or a 3-grain clump for cohesive powders
    (AoR >= 38 deg)."""
    return p.d50 * (3.0 if p.aor_deg >= 38 else 1.0)


# ============================== Test 1: heap AoR =============================================
PX_CAM = 35e-6          # m/px at 120 mm (SPEC 0.2)
D_CAM = 120e-3
t1 = {"px_um": 35, "camera_distance_mm": 120, "pedestals": {}}
for D_ped in (12e-3, 20e-3, 30e-3):
    rows = {}
    for p in ALL:
        heap = pt.heap_on_pedestal(D_ped, p.aor_deg, p.rho_bulk)
        an = pt.aor_fit_sigma(p.aor_deg, D_ped, rough_scale(p), PX_CAM)
        persp = pt.apparent_angle_finite_distance(p.aor_deg, D_ped / 2, D_CAM) - p.aor_deg
        rows[p.name] = {**heap, "sigma_flank_analytic_deg": an["sigma_flank_deg"],
                        "rows_in_fit": an["rows"], "perspective_bias_deg": persp,
                        "D_over_d50": D_ped / p.d50}
    t1["pedestals"][f"{D_ped*1e3:.0f}mm"] = rows
# Monte Carlo on synthetic silhouettes (both reference powders, three pedestals, two edge methods)
mc = {}
for p in REFS:
    for D_ped in (12e-3, 20e-3, 30e-3):
        for sub in (True, False):
            k = f"{p.name} | {D_ped*1e3:.0f}mm | {'subpixel' if sub else 'whole-pixel'}"
            mc[k] = pt.aor_fit_mc(p.aor_deg, D_ped, rough_scale(p), PX_CAM, rng, subpixel=sub, n_trials=300)
t1["mc"] = mc
# Budget for one pour on the 20 and 30 mm pedestals and n pours
GRAN_SD = {pt.SALT_DRY.name: 1.4, pt.COHESIVE.name: 3.6}   # deg, DEM run 2 sector scatter (per flank)
budget1 = {}
for p in REFS:
    for ped in (20, 30):
        fit = mc[f"{p.name} | {ped}mm | subpixel"]["sigma_deg"]
        per_flank = math.hypot(fit, GRAN_SD[p.name])
        per_pour = per_flank / math.sqrt(2)          # mean of the two flanks; camera roll cancels
        budget1[f"{p.name} | {ped}mm"] = {
            "fit_per_flank_deg": fit, "granular_per_flank_deg": GRAN_SD[p.name],
            "camera_roll_residual_deg": 0.0, "perspective_after_correction_deg": 0.02,
            "per_pour_sd_deg": per_pour, "se_3_pours_deg": per_pour / math.sqrt(3),
            "pours_for_se_1deg": math.ceil((per_pour / 1.0) ** 2)}
t1["budget"] = budget1
R["test1_aor"] = r3(t1)

# ============================== Test 2: bulk and tapped density ================================
ID = 13e-3
A_bore = math.pi * ID ** 2 / 4
sig_H = 0.05e-3
dm_water = pt.RHO_WATER * A_bore * 45e-3          # water added between the two calibration heights
sA = pt.bore_calibration_sigma(45e-3, sig_H, dm_water)
t2 = {"ID_mm": 13, "sigma_H_mm": 0.05, "bore_cal_two_point_rel": sA,
      "tap_v_mps": pt.tap_impact_velocity(3e-3),
      "tap_v_rel_tolerance": pt.tap_impact_velocity(3.2e-3) / pt.tap_impact_velocity(3e-3) - 1,
      "powders": {}}
for p in ALL:
    m = min(6e-3, 8e-6 * p.rho_bulk)
    H0 = pt.column_height(m, p.rho_bulk, ID)
    HN = pt.column_height(m, p.rho_tap, ID)
    hc = pt.poured_cone_height(ID, p.aor_deg)
    surf = max(0.5 * p.d50, 0.05e-3)
    a_k = 1 - 1 / p.hausner
    t2["powders"][p.name] = {
        "fill_g": m * 1e3, "H_bulk_mm": H0 * 1e3, "H_tap_mm": HN * 1e3,
        "cone_on_top_mm": hc * 1e3,
        "bias_if_apex_read_pct": -100 * (2 * hc / 3) / (H0 + 2 * hc / 3),
        "bias_if_wall_read_pct": 100 * (hc / 3) / (H0 - hc / 3),
        "rho_bulk_rel_sigma": pt.density_sigma(H0, sig_H, sA, m, surface_sigma=surf),
        "hausner": p.hausner, "hausner_rel_sigma": pt.hausner_sigma(H0, HN, sig_H, surf),
        "carr_pct": pt.carr_index(p.hausner), "kawakita_a": a_k,
        "kawakita_taps_to_95pct_if_b_0.1": 19 / 0.1,
        "smallest_resolvable_compaction_pct": 100 * sig_H / H0}
R["test2_density"] = r3(t2)

# ============================== Test 3: tilting plate ===========================================
t3 = {"ring": {"ID_mm": 25, "H_mm": 6, "wall_mm": 1.2}, "powders": {}}
for p in ALL:
    rows = {}
    for lid in (0, 5, 15):
        s0 = pt.ring_normal_stress(p.rho_bulk, lid)
        th = pt.slip_angle_deg(p.mu_wall, 0.0, s0["sigma_n_Pa"])
        rows[f"lid_{lid}g"] = {**s0, "sigma_n_at_slip_Pa": s0["sigma_n_Pa"] * math.cos(math.radians(th))}
    rows["shim_0.5mm_over_d90"] = 0.5e-3 / p.d90
    rows["shim_needed_mm_(2xd90)"] = max(0.5, 2 * p.d90 * 1e3)
    t3["powders"][p.name] = rows
# reference loci: dry (a_w = 0) and cohesive (a_w = 5 Pa assumed)
loci = {}
for p, aw in ((pt.SALT_DRY, 0.0), (pt.COHESIVE, 5.0)):
    s_list = [pt.ring_normal_stress(p.rho_bulk, lid)["sigma_n_Pa"] for lid in (0, 5, 15)]
    th = [pt.slip_angle_deg(p.mu_wall, aw, s) for s in s_list]
    fit = pt.wall_locus_fit_sigma(s_list, th, 0.5)
    loci[p.name] = {"adhesion_Pa_assumed": aw, "sigma_n_Pa": s_list, "slip_deg": th, **fit}
t3["wall_loci_sigma_theta_0.5deg"] = loci
t3["ring_hang"] = {p.name: {f"lid_{lid}g": pt.ring_hang_check(p.rho_bulk, lid) for lid in (0, 5, 15)} for p in ALL}
t3["imu_note"] = ("LSM6DSOX offset up to about 20 mg before calibration (about 1.1 deg); "
                  "two-position (flip) calibration leaves about 0.1 deg (assumed)")
t3["jolt_shift_deg"] = {f"mu_{mu}": {f"a_{a}g": pt.jolt_angle_error_deg(mu, a) for a in (0.005, 0.01, 0.03, 0.1)}
                        for mu in (0.4, 0.7)}
R["test3_tilt"] = r3(t3)

# ============================== Test 4: PSD counting statistics =================================
S_LIST = [round(pt.SALT_DRY.s_ln, 3), 0.3, 0.5, 0.7]
N_LIST = [100, 300, 1000, 3000, 10000, 30000]
boot = {}
for s in S_LIST:
    rows = {}
    for N in N_LIST:
        B = 200
        rows[N] = pt.bootstrap_quantiles(s, N, B, rng)
    boot[s] = rows


def n_needed(rows, key, target):
    Ns = np.array(N_LIST, float)
    hw = np.array([rows[N][key] for N in N_LIST])
    k = np.exp(np.mean(np.log(hw) + 0.5 * np.log(Ns)))      # hw = k / sqrt(N)
    return float((k / target) ** 2)


t4 = {"targets": "95 % half-width: d50 within +-2 %, d90 within +-5 %",
      "bootstrap_B": 200, "N_grid": N_LIST, "bootstrap": {}, "N_needed": {}}
for s in S_LIST:
    t4["bootstrap"][str(s)] = {str(N): boot[s][N] for N in N_LIST}
    t4["N_needed"][str(s)] = {
        "number_d50_2pct": n_needed(boot[s], "n_d50", 0.02),
        "number_d90_5pct": n_needed(boot[s], "n_d90", 0.05),
        "volume_d50_2pct": n_needed(boot[s], "v_d50", 0.02),
        "volume_d90_5pct": n_needed(boot[s], "v_d90", 0.05),
        "analytic_number_d50_2pct": pt.n_needed_number_quantile(s, 0.5, 0.02),
        "analytic_number_d90_5pct": pt.n_needed_number_quantile(s, 0.9, 0.05),
        "kish_volume_factor": 1 / pt.volume_weighted_ess_factor(s)}
t4["pixel_sizing_mc"] = {str(n): pt.pixel_sizing_mc(n, rng) for n in (3, 5, 7, 10, 15, 20, 30, 50)}
plans = {}
for p in ALL:
    plan = pt.psd_imaging_plan(p)
    s_key = min(S_LIST, key=lambda s: abs(s - p.s_ln))
    need = max(t4["N_needed"][str(s_key)]["number_d50_2pct"], t4["N_needed"][str(s_key)]["number_d90_5pct"])
    need_v = max(t4["N_needed"][str(s_key)]["volume_d50_2pct"], t4["N_needed"][str(s_key)]["volume_d90_5pct"])
    plan.update({"s_ln_assumed": p.s_ln, "grains_needed_number": need, "grains_needed_volume": need_v,
                 "fields_number": need / plan["grains_per_field"], "fields_volume": need_v / plan["grains_per_field"],
                 "sample_mass_mg_for_volume_count": need_v * pt.grain_mass(p.rho_p, p.d50) * math.exp(4.5 * p.s_ln ** 2) * 1e6,
                 "image_over_sieve_cube": 2 / math.sqrt(math.pi)})
    plans[p.name] = plan
t4["imaging_plans"] = plans
t4["sensor_note"] = "IMX477 active area 4056 x 3040 px x 1.55 um = 6.29 x 4.71 mm (SPEC says 7.1 x 5.4)"
R["test4_psd"] = r3(t4)

# ============================== Test 5: orifice cup =============================================
t5 = {"orifices_mm": pt.ORIFICES_MM, "C": 0.58, "k_range": [1.5, 2.9], "powders": {}}
for p in ALL:
    m_fill = 5e-3
    fill_h = m_fill / (p.rho_bulk * math.pi * pt.CUP_ID ** 2 / 4)
    rows = {"fill_height_mm_5g": fill_h * 1e3, "D_jam_mm": pt.jamming_diameter(p.d50) * 1e3,
            "bond_number_rumpf": pt.rumpf_bond_number(p.d50, p.rho_p), "discs": {}}
    for D in pt.ORIFICES_MM:
        Dm = D * 1e-3
        W15 = pt.beverloo(Dm, p.d50, p.rho_bulk, k=1.5)
        W29 = pt.beverloo(Dm, p.d50, p.rho_bulk, k=2.9)
        heel = pt.flat_cup_heel_mass(p.rho_bulk, p.aor_deg, Dm)
        out = max(0.0, m_fill - heel)
        rows["discs"][str(D)] = {
            "W_gps_k1.5": W15 * 1e3, "W_gps_k2.9": W29 * 1e3,
            "jams_geometric": Dm < pt.jamming_diameter(p.d50),
            "heel_g": heel * 1e3, "discharged_g": out * 1e3,
            "steady_s": out / W15 if W15 > 0 else None,
            "samples_10Hz": out / W15 * 10 if W15 > 0 else None,
            "sigma_c_if_Dc_Pa_H2.2": pt.sigma_c_from_Dc(Dm, p.rho_bulk, 2.2)}
    t5["powders"][p.name] = rows
# sigma_c brackets from disc steps and H(theta) range
brk = []
for lo, hi in zip(pt.ORIFICES_MM[:-1], pt.ORIFICES_MM[1:]):
    brk.append({"no_flow_mm": lo, "flows_mm": hi,
                "sigma_c_Pa_rho1000_H2.2": [pt.sigma_c_from_Dc(lo * 1e-3, 1000, 2.2), pt.sigma_c_from_Dc(hi * 1e-3, 1000, 2.2)],
                "step_rel_half_width": (hi - lo) / (hi + lo)})
t5["sigma_c_brackets"] = brk
t5["H_theta_range"] = {"theta0": pt.jenike_H(0), "theta45": pt.jenike_H(45), "rel_half_width": (2.75 - 2.0) / (2.75 + 2.0)}
sc_dry = pt.ucs_mohr_coulomb(pt.SALT_DRY.c_pa, pt.SALT_DRY.phi_i_deg)
sc_coh = pt.ucs_mohr_coulomb(pt.COHESIVE.c_pa, pt.COHESIVE.phi_i_deg)
t5["dem_ref_sigma_c_Pa"] = {"dry": sc_dry, "cohesive": sc_coh}
t5["dem_ref_Dc_mm_H2.2"] = {"dry_if_c_real": pt.Dc_from_sigma_c(sc_dry, pt.SALT_DRY.rho_bulk) * 1e3,
                            "cohesive": pt.Dc_from_sigma_c(sc_coh, pt.COHESIVE.rho_bulk) * 1e3}
t5["impact_vs_inflight_W3gps_40mm"] = pt.stream_impact_offset(3e-3, 40e-3)
R["test5_orifice"] = r3(t5)

# ============================== Test 6: humidity ================================================
t6 = {"greenspan": {}, "offsets": {}, "uptake_mg_per_g": {}, "kinetics_2mm": {}, "supply": {}}
for salt in pt.GREENSPAN:
    t6["greenspan"][salt] = {"RH_20": pt.greenspan_rh(salt, 20), "RH_25": pt.greenspan_rh(salt, 25),
                             "RH_30": pt.greenspan_rh(salt, 30), "dRH_dT_per_K": pt.greenspan_drh_dT(salt),
                             "u25": pt.GREENSPAN[salt]["u25"]}
    t6["offsets"][salt] = {f"dT_{dT}K": pt.rh_at_offset(pt.greenspan_rh(salt, 25), 25, dT) - pt.greenspan_rh(salt, 25)
                           for dT in (0.1, 0.5, 1.0)}
t6["dlnpsat_dT_25C"] = math.log(pt.p_sat_hpa(25.5) / pt.p_sat_hpa(24.5))
RH_LEVELS = [5, 32.8, 52.9, 75.3, 84.3]
for p in pt.BATTERY:
    t6["uptake_mg_per_g"][p.name] = {str(rh): (None if (u := pt.uptake_class(p.hygro_class, rh)) is None else 1000 * u)
                                      for rh in RH_LEVELS}
    t6["uptake_mg_per_g"][p.name]["class"] = p.hygro_class
# kinetics in a 2 mm layer, slope dq/dRH per unit RH (0-1)
slopes = {"inert (1e-4)": 1e-4, "salt below DRH (2e-4)": 2e-4,
          "starch 53-75 % (GAB)": float((pt.gab(0.753, *pt.GAB_CLASS["starch"]) - pt.gab(0.529, *pt.GAB_CLASS["starch"])) / 0.224),
          "hydrocolloid 53-75 % (GAB)": float((pt.gab(0.753, *pt.GAB_CLASS["hydrocolloid"]) - pt.gab(0.529, *pt.GAB_CLASS["hydrocolloid"])) / 0.224)}
for lbl, sl in slopes.items():
    rho_b, rho_p = (680.0, 1450.0) if "starch" in lbl else (600.0, 1600.0) if "hydro" in lbl else (1249.0, 2165.0)
    eps = 1 - rho_b / rho_p
    t6["kinetics_2mm"][lbl] = {"slope_per_RH": sl, "eps": eps, **pt.layer_uptake_t95(2e-3, rho_b, eps, sl)}
A_dish = math.pi * 0.03 ** 2
hm_still = pt.D_VAPOUR / 0.03
hm_fan = pt.flat_plate_hm(1.0, 0.06)
t6["supply"] = {"A_dish_m2": A_dish, "h_m_still_air_mps": hm_still, "h_m_fan_1mps": hm_fan,
                "NaCl_in_KCl_box_mg_per_h_still": pt.deliquescence_rate(hm_still, A_dish, 84.3, 75.3) * 3.6e9,
                "NaCl_in_KCl_box_mg_per_h_fan": pt.deliquescence_rate(hm_fan, A_dish, 84.3, 75.3) * 3.6e9,
                "water_to_dissolve_2g_NaCl_g": 2 / 0.36,
                "box_vapour_mg_at_75pct": 1.2e-3 * pt.C_SAT_25 * 0.753 * 1e6}
# weighing-exposure bound: 30 s out of the box, room 40 % RH, still room air h_m about 2e-3 m/s (assumed)
t6["exposure_30s"] = {f"box_{rh}": pt.exposure_error(30, 2e-3, A_dish, rh - 40) * 1e6 for rh in (52.9, 75.3, 84.3)}
t6["sht45_accuracy_pctRH_assumed"] = 1.0
# silica-gel box: water released by drying 2 g of a hydrocolloid from 52.9 % to 5 % RH, and the gel to hold it
rel = 2.0 * (pt.uptake_class("hydrocolloid", 52.9) - pt.uptake_class("hydrocolloid", 5)) * 1e3   # mg
t6["silica_gel"] = {"water_released_mg_2g_hydrocolloid": rel, "gel_capacity_at_5pct_assumed": 0.03,
                    "gel_needed_g": rel / 1e3 / 0.03}
R["test6_humidity"] = r3(t6)

# ============================== Test 7: drum =====================================================
DRUM_D, DRUM_W = 40e-3, 15e-3
t7 = {"D_mm": 40, "depth_mm": 15, "speeds": {}}
for rpm in (1, 2, 5, 10, 20, 30, 60, 109):
    Fr = pt.froude(rpm, DRUM_D)
    t7["speeds"][str(rpm)] = {"Fr": Fr, "regime": pt.drum_regime(Fr), "deg_per_s": 6 * rpm,
                              "frames_per_3deg_avalanche_10fps": 3 / (6 * rpm) * 10,
                              "frames_per_37deg_avalanche_10fps": 37 / (6 * rpm) * 10}
t7["counting_90s"] = {f"{r}rpm": {"dry_3deg_sd4.4": pt.drum_counting(r, 3, 4.4), "cohesive_37deg_sd12.4": pt.drum_counting(r, 37, 12.4),
                                    "cohesive_37deg_sd12.4_300s": pt.drum_counting(r, 37, 12.4, 300)} for r in (1, 2, 5)}
t7["granudrum_match"] = {f"{r}rpm_in_84mm": pt.rpm_for_froude(pt.froude(r, 84e-3), DRUM_D) for r in (2, 10, 30, 60)}
t7["endwall_shift_deg"] = {
    "coarse_salt_h=10d": pt.endwall_angle_shift(39.2, 0.4, 10 * 0.425e-3, DRUM_W),
    "fine_h=1mm": pt.endwall_angle_shift(39.2, 0.4, 1e-3, DRUM_W),
    "coarse_salt_depth25": pt.endwall_angle_shift(39.2, 0.4, 10 * 0.425e-3, 25e-3)}
V40 = 0.4 * math.pi * (DRUM_D / 2) ** 2 * DRUM_W
t7["fill"] = {p.name: {"mass_g_40pct": V40 * p.rho_bulk * 1e3, "D_over_d50": DRUM_D / p.d50} for p in ALL}
R["test7_drum"] = r3(t7)

# ============================== Test 8: mould and UCS ===========================================
z = np.linspace(0, pt.MOULD_H, 81)
t8 = {"consolidation_Pa_SPEC": {}, "janssen": {}, "self_weight_Pa": {}, "refs": {}}
for mg in (6.4, 16, 32, 64):
    t8["consolidation_Pa_SPEC"][f"{mg}g"] = {"on_bore_314mm2": mg * 1e-3 * pt.G / (math.pi * 0.01 ** 2),
                                             "on_piston_19.6": mg * 1e-3 * pt.G / (math.pi * 0.0098 ** 2)}
for p in REFS:
    K = pt.janssen_K(p.phi_i_deg)
    for mu_w, lbl in ((0.4, "PLA mu 0.4"), (0.25, "smooth SLA mu 0.25"), (0.15, "PTFE film mu 0.15")):
        rows = {"K": K, "lambda_mm": pt.MOULD_D / (4 * mu_w * K) * 1e3}
        for s0 in (200, 500, 1000, 2000):
            sv = pt.janssen_sigma_v(z, pt.MOULD_D, mu_w, K, p.rho_bulk, s0)
            rows[f"s0_{s0}"] = {"bottom_Pa": float(sv[-1]), "mean_Pa": float(sv.mean()),
                                "bottom_over_top": float(sv[-1] / s0), "wall_top_Pa": K * s0}
        t8["janssen"][f"{p.name} | {lbl}"] = rows
for p in ALL:
    t8["self_weight_Pa"][p.name] = {"H40": pt.column_self_weight_stress(p.rho_bulk, 0.04),
                                    "H20": pt.column_self_weight_stress(p.rho_bulk, 0.02)}
A_m = math.pi * 0.01 ** 2
for p, sc in ((pt.SALT_DRY, sc_dry), (pt.COHESIVE, sc_coh)):
    s1 = sc * (20.8 if p is pt.SALT_DRY else 13.8)
    t8["refs"][p.name] = {"sigma_c_Pa": sc, "sigma_1_Pa": s1, "ffc": s1 / sc, "class": pt.ffc_class(s1 / sc),
                          "platen_force_mN": sc * A_m * 1e3, "platen_force_g": sc * A_m / pt.G * 1e3,
                          "stands_H40": sc > pt.column_self_weight_stress(p.rho_bulk, 0.04),
                          "consolidation_circle": pt.consolidation_circle(s1, p.c_pa, p.phi_i_deg)}
t8["resolution_Pa_2mg"] = 2e-6 * pt.G / A_m
# largest ff_c whose column still stands at its foot: sigma_v,consol(H) / (rho g H), cohesive ref
stand = {}
pc = pt.COHESIVE
Kc = pt.janssen_K(pc.phi_i_deg)
for H in (0.02, 0.03, 0.04):
    for mu_w in (0.4, 0.25, 0.15):
        for s0 in (2000, 4000, 8000):
            sv = float(pt.janssen_sigma_v(H, pt.MOULD_D, mu_w, Kc, pc.rho_bulk, s0))
            stand[f"H{H*1e3:.0f} | mu {mu_w} | s0 {s0}"] = sv / pt.column_self_weight_stress(pc.rho_bulk, H)
t8["ffc_max_standing_cohesive_ref"] = stand
t8["load_on_cell_g_at_2kPa"] = {"weight": 64, "powder": pc.rho_bulk * A_m * 0.04 * 1e3, "mould_assumed": 25}
t8["ffc_max_measurable_at_2kPa_H40_rho1000"] = 2000 / pt.column_self_weight_stress(1000, 0.04)
R["test8_ucs"] = r3(t8)

# ============================== Test 9: spreading ===============================================
t9 = {"coupon_mm": [100, 30], "powders": {}}
Acoup = pt.COUPON[0] * pt.COUPON[1]
for p in ALL:
    phi = 0.26 if p is pt.COHESIVE else 0.34
    rows = {"phi_layer_assumed": phi, "dem_gap_2.5d50_mm": 2.5 * p.d50 * 1e3}
    for gap in (0.10e-3, 0.15e-3, 0.20e-3, 2.5 * p.d50, 2.5 * p.d90):
        mA = pt.layer_areal_mass(phi, p.rho_p, gap)
        rows[f"gap_{gap*1e3:.3g}mm"] = {"gap_over_d50": gap / p.d50, "gap_over_d90": gap / p.d90,
                                        "layer_g": mA * Acoup * 1e3, "feed_g_1.5x": 1.5 * mA * Acoup * 1e3}
    # passive force from the heap of a 0.5 g line across 30 mm
    Ax = 0.5e-3 / (p.rho_bulk * 0.03)
    h = math.sqrt(Ax * math.tan(math.radians(p.aor_deg)))
    rows["heap_h_mm_0.5g_line"] = h * 1e3
    rows["passive_force_mN"] = pt.passive_force_per_width(p.rho_bulk, h, p.phi_i_deg or p.aor_deg,
                                                          p.c_pa or 0.0) * 0.03 * 1e3
    t9["powders"][p.name] = rows
t9["phi_rel_sigma_gap_5um"] = {"0.10mm": 0.05, "0.20mm": 0.025, "1.0mm": 0.005}
R["test9_spread"] = r3(t9)

# ============================== Test 10: Faraday cup ============================================
C_cup = pt.cup_capacitance_estimate()
t10 = {"C_cup_estimate_pF": C_cup * 1e12, "ranges": {}, "signals": {}, "drift": {}, "DA": {}, "decay": {}}
for Cf in (10e-9, 100e-9):
    t10["ranges"][f"{Cf*1e9:.0f}nF"] = {"FS_nC_at_2.4V": 2.4 * Cf * 1e9, "LSB_pC_fsr4.096": pt.adc_charge_lsb(Cf) * 1e12,
                                        "noise_gain_with_1m_cable": 1 + (C_cup + 100e-12) / Cf}
for qm in (1e-6, 1e-5, 2.8e-5, 1e-4):
    t10["signals"][f"{qm:.0e}"] = {"Q_nC_0.5g": qm * 0.5e-3 * 1e9, "Q_nC_1g": qm * 1e-3 * 1e9,
                                   "max_dose_g_10nF": 24e-9 / qm * 1e3, "max_dose_g_100nF": 240e-9 / qm * 1e3,
                                   "rel_resolution_0.5g_10nF": pt.adc_charge_lsb(10e-9) / (qm * 0.5e-3)}
for Ib in (1e-15, 20e-15):
    t10["drift"][f"{Ib*1e15:.0f}fA"] = {"Q_pC_200s": pt.bias_drift_charge(Ib, 200) * 1e12}
for name, DA in (("PTFE", 1e-4), ("polystyrene", 2e-4), ("polypropylene", 3e-4), ("C0G", 1e-3)):
    t10["DA"][name] = {"DA_assumed": DA, "false_pC_after_FS_10nF": pt.da_recovery_charge(DA, 2.4, 10e-9) * 1e12,
                       "false_pC_after_FS_100nF": pt.da_recovery_charge(DA, 2.4, 100e-9) * 1e12,
                       "rel_to_0.5nC": pt.da_recovery_charge(DA, 2.4, 10e-9) / 0.5e-9}
for Rl in (1e11, 1e12, 1e13, 1e14):
    t10["decay"][f"{Rl:.0e}ohm"] = {"tau_s_10nF": Rl * 10e-9, "loss_pct_202s_10nF": 100 * pt.decay_fraction(202, Rl, 10e-9),
                                     "tau_s_100nF": Rl * 100e-9, "loss_pct_202s_100nF": 100 * pt.decay_fraction(202, Rl, 100e-9)}
t10["voltage_mode_V_for_100nC_with_1m_cable"] = 100e-9 / (C_cup + 100e-12)
t10["max_qm_breakdown_C_per_kg"] = {p.name: pt.max_charge_per_mass(p.rho_p, p.d50) for p in ALL}
t10["salt_grain"] = {"mass_ug": pt.grain_mass(2165, 0.425e-3) * 1e9,
                     "q_pC_at_1e-5": 1e-5 * pt.grain_mass(2165, 0.425e-3) * 1e12,
                     "grains_per_g": 1e-3 / pt.grain_mass(2165, 0.425e-3)}
R["test10_faraday"] = r3(t10)

# ============================== Internal checks =================================================
c = np.polyfit(pt.GREENSPAN_T, pt.GREENSPAN["NaCl"]["rh"], 3)
R["checks"] = {
    "beverloo_hall_dry_ref_gps": pt.beverloo(2.54e-3, pt.SALT_DRY.d50, pt.SALT_DRY.rho_bulk) * 1e3,
    "dem_run4_hall_gps": 0.363, "run4_beverloo_gps": 0.358,
    "greenspan_cubic_max_residual_pctRH": max(float(np.max(np.abs(np.polyval(np.polyfit(pt.GREENSPAN_T, v["rh"], 3), pt.GREENSPAN_T) - v["rh"])))
                                              for v in pt.GREENSPAN.values()),
    "aor_formula_over_mc_20mm": {p.name: t1["pedestals"]["20mm"][p.name]["sigma_flank_analytic_deg"] / mc[f"{p.name} | 20mm | subpixel"]["sigma_deg"] for p in REFS},
    "quantile_formula_over_bootstrap": {s_: {"d50": nn_["analytic_number_d50_2pct"] / nn_["number_d50_2pct"], "d90": nn_["analytic_number_d90_5pct"] / nn_["number_d90_5pct"]}
                                        for s_, nn_ in t4["N_needed"].items()},
    "consolidation_200Pa_from_6.4g": 6.4e-3 * pt.G / (math.pi * 0.01 ** 2),
    "tap_v_matches_run5_0.24mps": pt.tap_impact_velocity(3e-3),
}
R["checks"] = r3(R["checks"])

# ============================== Summary table ===================================================
b1 = budget1
bd20, bc20 = b1[f"{pt.SALT_DRY.name} | 20mm"], b1[f"{pt.COHESIVE.name} | 20mm"]
bd30, bc30 = b1[f"{pt.SALT_DRY.name} | 30mm"], b1[f"{pt.COHESIVE.name} | 30mm"]
cone_bias = [abs(v["bias_if_apex_read_pct"]) for v in t2["powders"].values()]
hr_sig = [100 * v["hausner_rel_sigma"] for v in t2["powders"].values()]
rb_sig = [100 * v["rho_bulk_rel_sigma"] for v in t2["powders"].values()]
lo3 = min(v["lid_0g"]["sigma_n_Pa"] for v in t3["powders"].values())
hi3 = max(v["lid_15g"]["sigma_n_Pa"] for v in t3["powders"].values())
mu_sig = loci[pt.SALT_DRY.name]["sigma_mu"]
nn = t4["N_needed"]
st = t8["ffc_max_standing_cohesive_ref"]
n_ok_gap = sum(1 for p in pt.BATTERY if 0.2e-3 / p.d50 >= 2.5)
summary = [
    ["1 Heap AoR", "flank angle (deg)", "22-47 (refs 21.9 / 39.3)",
     "35 um/px; fit SD per flank " f"{bd20['fit_per_flank_deg']:.1f} (dry) / {bc20['fit_per_flank_deg']:.1f} (cohesive) deg on 20 mm, "
     f"{bd30['fit_per_flank_deg']:.1f} / {bc30['fit_per_flank_deg']:.1f} on 30 mm",
     f"SE of 3 pours {bd20['se_3_pours_deg']:.1f} deg dry, {bc20['se_3_pours_deg']:.1f} deg cohesive (20 mm)",
     "grain roughness of the silhouette and heap-to-heap scatter, not pixel size"],
    ["2 Bulk/tapped density", "rho_b, rho_tap, Hausner", "400-1400 kg/m3; HR 1.07-1.38",
     "0.05 mm on 26-60 mm columns (0.1-0.2 %)",
     f"rho_b {min(rb_sig):.1f}-{max(rb_sig):.1f} %, HR {min(hr_sig):.1f}-{max(hr_sig):.1f} % (with the cone integrated)",
     f"poured cone on top: reading the apex biases rho_b by {min(cone_bias):.0f}-{max(cone_bias):.0f} %"],
    ["3 Tilting plate", "slip angle -> mu_w, a_w", f"mu_w 0.3-0.7 at sigma_n {lo3:.0f}-{hi3:.0f} Pa",
     "IMU about 0.1 deg after a flip calibration",
     f"mu_w +-{mu_sig:.3f}, a_w +-{loci[pt.SALT_DRY.name]['sigma_adhesion_Pa']:.1f} Pa from 3 lids at 0.5 deg per slip",
     "stick-slip scatter; plate jolts (0.01 g shifts the angle 0.2-0.3 deg); grains under a 0.5 mm shim; a lid-less ring resting on the plate"],
    ["4 PSD images", "d10/d50/d90 (number, volume)", "25-425 um", "0.9-13 um/px (zoom); 10 px/grain sizes to 0.8 %",
     f"number d50 +-2 % needs {nn['0.3']['number_d50_2pct']:.0f} / {nn['0.5']['number_d50_2pct']:.0f} / {nn['0.7']['number_d50_2pct']:.0f} grains "
     f"(s 0.3 / 0.5 / 0.7); volume d50 needs {nn['0.3']['volume_d50_2pct']:.0f} / {nn['0.5']['volume_d50_2pct']:.0f} / {nn['0.7']['volume_d50_2pct']:.0f}",
     "counting statistics of the coarse tail (volume weighting)"],
    ["5 Orifice cup", "W(D), D_c -> sigma_c", "W 0.04-7 g/s; D_c 1-6 mm; sigma_c 4-30 Pa",
     "disc steps: +-8 to +-20 % in D",
     "sigma_c +-18-26 % (disc step and H(theta) 2.0-2.75); k 1.5 vs 2.9 moves W by 5 % (fine) to 50-75 % (coarse, D <= 3 mm)",
     "H(theta), disc set; 26-63 % of a 5 g fill stays as a heel, under 1 s of steady flow at 6 mm"],
    ["6 Humidity", "uptake (mg/g) vs RH and time", "0.005-340 mg/g (inert powders to hydrocolloids)",
     "0.1 mg on 2-5 g (0.02-0.05 mg/g)",
     "slurry RH +-0.1-0.3 %RH; SHT45 +-1 %RH; sample 1 K warmer = -1.9 to -4.9 %RH",
     "temperature differences in the box; chamber-limited uptake above the DRH (18 mg/h still air)"],
    ["7 Drum", "dynamic angle, avalanche scatter", "30-60 deg; Fr 2e-5 to 9e-3 (1-20 rpm)",
     "about 0.2 deg per frame", "end-wall bias +0.9 (fine) to +3.7 deg (coarse) at 15 mm depth",
     "end-wall friction; few cohesive avalanches in 90 s (SE 3.2 deg at 1 rpm); 10 fps under-samples dry avalanches below 5 rpm"],
    ["8 UCS", "sigma_c vs sigma_1 -> ff_c", "sigma_c 20-1000 Pa", "0.06 Pa (2 mg)",
     f"PLA wall: foot of the column gets {100*t8['janssen'][pt.COHESIVE.name+' | PLA mu 0.4']['s0_2000']['bottom_over_top']:.0f} % of a 2 kPa top stress; "
     f"columns stand only if ff_c < {st['H40 | mu 0.4 | s0 2000']:.1f} (PLA) / {st['H40 | mu 0.15 | s0 2000']:.1f} (PTFE)",
     "Janssen wall friction and self-weight (390-490 Pa at H 40 mm)"],
    ["9 Spreading", "areal mass, phi_layer, coverage", "0.15-4 g per coupon layer", "0.1 mg",
     "phi_layer +-5 % at 0.10 mm gap, +-2.5 % at 0.20 mm (5 um gap setting)",
     f"gap setting and coupon flatness; a 0.20 mm gap is at least 2.5 d50 for only {n_ok_gap} of 12 battery powders"],
    ["10 Faraday cup", "q/m (C/kg)", "1e-6 to 1e-4 C/kg -> 0.5-100 nC per 0.5-1 g",
     "1.25 pC (10 nF), 12.5 pC (100 nF)",
     "0.3-1 % at 0.5 nC (LSB, 20 fA over 200 s, R_leak 1e13 ohm, film C_f); 5 % false charge after a full-scale reading with C0G",
     "leakage and dielectric absorption of C_f; airborne grains at read time (sim/fea)"],
]
R["summary_table"] = summary
R["runtime_s"] = time.time() - T0
with open(os.path.join(HERE, "results.json"), "w") as f:
    json.dump(R, f, indent=1, default=lambda o: o if not isinstance(o, np.generic) else o.item())

# ============================== Figures ==========================================================
# Fig 1: AoR fit uncertainty
fig, ax = plt.subplots(figsize=(5.2, 3.4))
peds = [12, 20, 30]
for i, p in enumerate(REFS):
    an = [t1["pedestals"][f"{d}mm"][p.name]["sigma_flank_analytic_deg"] for d in peds]
    mcs = [mc[f"{p.name} | {d}mm | subpixel"]["sigma_deg"] for d in peds]
    mcw = [mc[f"{p.name} | {d}mm | whole-pixel"]["sigma_deg"] for d in peds]
    ax.plot(peds, an, "-", color=PAL[i], label=f"{p.name}: line-fit formula")
    ax.plot(peds, mcs, "o", color=PAL[i], label=f"{p.name}: Monte Carlo, sub-pixel edge")
    ax.plot(peds, mcw, "s", mfc="white", color=PAL[i], label=f"{p.name}: Monte Carlo, whole-pixel edge")
ax.set_xlabel("pedestal diameter (mm)")
ax.set_ylabel("SD of one flank angle from the fit (deg)")
ax.set_title("Test 1: flank-fit error at 35 um/px (computed)", loc="left", fontsize=9)
ax.set_xticks(peds)
ax.set_ylim(bottom=0)
ax.legend(fontsize=6.5, loc="upper right")
fig.tight_layout()
fig.savefig(os.path.join(HERE, "fig_aor_fit.png"))
plt.close(fig)

# Fig 2: PSD counting statistics
fig, axs = plt.subplots(1, 2, figsize=(7.6, 3.3), sharey=True)
for ax, s in zip(axs, (0.3, 0.5)):
    for j, (key, lbl) in enumerate((("n_d50", "number d50"), ("n_d90", "number d90"),
                                    ("v_d50", "volume d50"), ("v_d90", "volume d90"))):
        hw = [100 * boot[s][N][key] for N in N_LIST]
        ax.loglog(N_LIST, hw, "-o", color=PAL[j], label=lbl, ms=4)
    ax.axhline(2, color=TXT2, lw=1, ls="--")
    ax.axhline(5, color=TXT2, lw=1, ls=":")
    ax.text(1.6e4, 2.15, "+-2 %", color=TXT2, fontsize=7)
    ax.text(1.6e4, 5.4, "+-5 %", color=TXT2, fontsize=7)
    ax.set_title(f"lognormal, s = {s}", loc="left", fontsize=9)
    ax.set_xlabel("grains counted")
axs[0].set_ylabel("95 % half-width (% of the true value)")
axs[1].legend(fontsize=7)
fig.suptitle("Test 4: counting statistics by bootstrap (computed)", x=0.02, ha="left", fontsize=9)
fig.tight_layout()
fig.savefig(os.path.join(HERE, "fig_psd_counting.png"))
plt.close(fig)

# Fig 3: Greenspan and temperature offsets
fig, axs = plt.subplots(1, 2, figsize=(7.6, 3.2))
Tg = np.linspace(15, 35, 41)
for i, salt in enumerate(pt.GREENSPAN):
    axs[0].plot(Tg, [pt.greenspan_rh(salt, t) for t in Tg], color=PAL[i], label=salt)
    axs[0].plot(pt.GREENSPAN_T, pt.GREENSPAN[salt]["rh"], "o", color=PAL[i], ms=4)
    dTs = np.linspace(-1, 1, 41)
    rh25 = pt.greenspan_rh(salt, 25)
    axs[1].plot(dTs, [pt.rh_at_offset(rh25, 25, d) for d in dTs], color=PAL[i], label=salt)
axs[0].set_xlabel("temperature (C)")
axs[0].set_ylabel("RH over the slurry (%)")
axs[0].set_title("Greenspan 1977 (points) and cubic fit", loc="left", fontsize=9)
axs[1].set_xlabel("sample warmer than the slurry by (K)")
axs[1].set_ylabel("RH at the sample (%)")
axs[1].set_title("Same vapour pressure, 25 C", loc="left", fontsize=9)
axs[1].legend(fontsize=7, loc="center right")
fig.suptitle("Test 6: salt RH and its temperature sensitivity (computed)", x=0.02, ha="left", fontsize=9)
fig.tight_layout()
fig.savefig(os.path.join(HERE, "fig_humidity.png"))
plt.close(fig)

# Fig 4: Beverloo
fig, ax = plt.subplots(figsize=(5.4, 3.5))
Dg = np.linspace(0.8, 6.2, 200)
show = [pt.SALT_DRY, pt.COHESIVE] + [p for p in pt.BATTERY if p.name in ("white-rice-flour", "alsi10mg", "barium-chloride")]
for i, p in enumerate(show):
    W = [pt.beverloo(D * 1e-3, p.d50, p.rho_bulk) * 1e3 for D in Dg]
    Wm = np.array(W)
    Dj = pt.jamming_diameter(p.d50) * 1e3
    ax.plot(Dg[Dg >= Dj], Wm[Dg >= Dj], color=PAL[i], label=f"{p.name}")
    ax.plot(Dg[Dg < Dj], Wm[Dg < Dj], color=PAL[i], ls=":", lw=1)
for D in pt.ORIFICES_MM:
    ax.axvline(D, color=GRID, lw=0.8, zorder=0)
ax.set_yscale("log")
ax.set_ylim(1e-2, 20)
ax.set_xlabel("orifice diameter (mm); grey lines = SPEC discs")
ax.set_ylabel("Beverloo flow rate (g/s), C 0.58, k 1.5")
ax.set_title("Test 5: expected flow (dotted below D = 4.94 d50, clogs)", loc="left", fontsize=9)
ax.legend(fontsize=7, loc="lower right")
fig.tight_layout()
fig.savefig(os.path.join(HERE, "fig_orifice.png"))
plt.close(fig)

# Fig 5: Janssen profiles and Mohr circles
fig, axs = plt.subplots(1, 2, figsize=(7.8, 3.4))
p = pt.COHESIVE
K = pt.janssen_K(p.phi_i_deg)
for i, s0 in enumerate((200, 500, 1000, 2000)):
    axs[0].plot(pt.janssen_sigma_v(z, pt.MOULD_D, 0.4, K, p.rho_bulk, s0), z * 1e3, color=PAL[i], label=f"{s0} Pa")
    axs[0].plot(pt.janssen_sigma_v(z, pt.MOULD_D, 0.15, K, p.rho_bulk, s0), z * 1e3, color=PAL[i], ls="--", lw=1.2)
axs[0].invert_yaxis()
axs[0].set_xlim(0, 2700)
axs[0].set_xlabel("vertical stress (Pa); solid PLA wall (mu 0.4), dashed PTFE (0.15)")
axs[0].set_ylabel("depth below the piston (mm)")
axs[0].set_title("Janssen in the 20 mm mould, cohesive ref", loc="left", fontsize=9)
axs[0].legend(fontsize=6.5, loc="lower right", title="top stress", title_fontsize=6.5, frameon=True, facecolor="white", edgecolor="white", framealpha=0.9)
sig = np.linspace(-30, 650, 300)
axs[1].plot(sig, p.c_pa + sig * math.tan(math.radians(p.phi_i_deg)), color=TXT, lw=1.2, label="yield locus c 11.9 Pa, phi 32.3 deg")
th = np.linspace(0, math.pi, 200)
uc = pt.ucs_mohr_coulomb(p.c_pa, p.phi_i_deg)
axs[1].plot(uc / 2 + uc / 2 * np.cos(th), uc / 2 * np.sin(th), color=PAL[1], label=f"unconfined test, sigma_c {uc:.0f} Pa")
cc, rr = pt.consolidation_circle(uc * 13.8, p.c_pa, p.phi_i_deg)
axs[1].plot(cc + rr * np.cos(th), rr * np.sin(th), color=PAL[0], label=f"consolidation, sigma_1 {uc*13.8:.0f} Pa")
axs[1].set_xlim(-30, 650)
axs[1].set_ylim(0, 330)
axs[1].set_aspect("equal")
axs[1].set_xlabel("normal stress (Pa)")
axs[1].set_ylabel("shear stress (Pa)")
axs[1].set_title("Mohr circles, ff_c 13.8 (DEM run 6)", loc="left", fontsize=9)
axs[1].legend(fontsize=6.5, loc="upper left")
fig.suptitle("Test 8: consolidation profile and UCS stress state (computed)", x=0.02, ha="left", fontsize=9)
fig.tight_layout()
fig.savefig(os.path.join(HERE, "fig_mould.png"))
plt.close(fig)

# Fig 6: Faraday signal levels
fig, ax = plt.subplots(figsize=(6.8, 3.4))
dose = np.logspace(-1, 0.3, 50)
for i, qm in enumerate((1e-6, 1e-5, 2.8e-5, 1e-4)):
    ax.loglog(dose, qm * dose * 1e-3 * 1e9, color=PAL[i], label=f"q/m {qm:.1e} C/kg")
for Cf, ls in ((10e-9, "--"), (100e-9, ":")):
    ax.axhline(2.4 * Cf * 1e9, color=TXT2, ls=ls, lw=1)
    ax.axhline(pt.adc_charge_lsb(Cf) * 1e9, color=TXT2, ls=ls, lw=1)
ax.text(0.105, 26, "full scale 10 nF (24 nC)", fontsize=7, color=TXT2)
ax.text(0.105, 260, "full scale 100 nF (240 nC)", fontsize=7, color=TXT2)
ax.text(0.105, 1.4e-3, "1 LSB, 10 nF (1.25 pC)", fontsize=7, color=TXT2)
ax.text(0.105, 1.4e-2, "1 LSB, 100 nF (12.5 pC)", fontsize=7, color=TXT2)
ax.set_xlabel("dose (g)")
ax.set_ylabel("charge (nC)")
ax.set_ylim(5e-4, 1e3)
ax.set_title("Test 10: signal vs range and resolution (computed)", loc="left", fontsize=9)
ax.legend(fontsize=7, loc="center left", bbox_to_anchor=(1.01, 0.5))
fig.tight_layout()
fig.savefig(os.path.join(HERE, "fig_faraday.png"))
plt.close(fig)

# Fig 7: drum Froude
fig, ax = plt.subplots(figsize=(5.4, 3.2))
rpm = np.logspace(0, math.log10(109), 100)
ax.loglog(rpm, [pt.froude(r, DRUM_D) for r in rpm], color=PAL[0], label="this drum, 40 mm")
ax.loglog(rpm, [pt.froude(r, 84e-3) for r in rpm], color=PAL[1], label="GranuDrum size, 84 mm")
for lo, hi, name, col in ((1e-5, 1e-4, "slumping", "#f3f3f3"), (1e-4, 1e-3, "slumping/rolling", "#e8f1fb"),
                          (1e-3, 1e-2, "rolling/cascading", "#f3f3f3"), (1e-2, 0.1, "cascading", "#e8f1fb"),
                          (0.1, 1.0, "cataracting", "#f3f3f3")):
    ax.axhspan(lo, hi, color=col, zorder=0)
    ax.text(1.05, lo * 1.3, name, fontsize=7, color=TXT2)
for r in (1, 2, 5, 10, 20):
    ax.plot(r, pt.froude(r, DRUM_D), "o", color=PAL[0], ms=5)
ax.set_xlabel("drum speed (rpm); dots = SPEC SOP speeds")
ax.set_ylabel("Froude number omega^2 R / g")
ax.set_title("Test 7: Froude number and regimes (Mellmann 2001)", loc="left", fontsize=9)
ax.legend(fontsize=7, loc="lower right")
fig.tight_layout()
fig.savefig(os.path.join(HERE, "fig_drum.png"))
plt.close(fig)

print(f"done in {time.time()-T0:.1f} s")
