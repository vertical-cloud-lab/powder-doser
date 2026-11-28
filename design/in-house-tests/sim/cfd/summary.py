"""Collect the key numbers of every CFD study into cfd_summary.json (and print them)."""
import json
import os

import numpy as np


def load(fn):
    return json.load(open(fn)) if os.path.exists(fn) else None


def at(series_t, y, t):
    return float(np.interp(t, series_t, y))


def main():
    S = {"note": "All values computed, not measured."}
    cav = load("cavity_validation.json")
    if cav:
        runs = cav["runs"]
        ext = {}
        for key in ("u_min", "v_min", "v_max"):
            a, b = runs[-2][key], runs[-1][key]
            ext[key] = b + (b - a) / 3.0          # Richardson, 2nd order
        order = float(np.log2((runs[0]["u_min"] - runs[1]["u_min"]) / (runs[1]["u_min"] - runs[2]["u_min"])))
        S["validation_cavity"] = dict(
            grids=[r["N"] for r in runs], max_err_u_vs_ghia=[round(r["max_err_u"], 4) for r in runs],
            max_err_v_vs_ghia=[round(r["max_err_v"], 4) for r in runs],
            richardson_extrapolated=ext, observed_order_u_min=order,
            reference_high_accuracy=dict(u_min=-0.21404, v_min=-0.25380, v_max=0.17957,
                                         source="Marchi, Suero and Araki (2009), 1024x1024, quoted from memory"),
            ghia=dict(u_min=-0.21090, v_min=-0.24533, v_max=0.17527))
    pipe = load("pipe_validation.json")
    if pipe:
        S["validation_pipe"] = [dict(nr=r["nr"], profile_err=round(r["max_err_profile"], 4),
                                     dpdz_err=round(r["dpdz_rel_err"], 4)) for r in pipe["runs"]]
    dif = load("diffusion_validation.json")
    if dif:
        S["validation_diffusion"] = dict(t95_exact=dif["t95_exact"], t99_exact=dif["t99_exact"],
                                         runs=[dict(h_mm=r["h_mm"], dt=r["dt_s"], max_err=round(r["max_abs_err"], 4),
                                                    t95=round(r["t95_top"], 1), t99=round(r["t99_top"], 1))
                                               for r in dif["runs"]])
    hum = {}
    for h in ("5.0", "2.5"):
        r = load(f"humidity_3d_h{h}mm.json")
        if not r:
            continue
        if "case_b" not in r:
            # the 2.5 mm case b ran once (log_h3d_2.5_first.txt); its JSON was lost when that run was
            # stopped during case c (memory), so only the printed numbers are kept
            hum[f"3d_still_h{h}"] = dict(
                a_sample=r["case_a"]["sample"], a_sensor=r["case_a"]["sensor"],
                c_deliquescent_uptake_mg_h=r["case_c"]["uptake_rate_mg_per_h"] if "case_c" in r else None,
                c_sensor_RH=r["case_c"]["sensor_RH"] if "case_c" in r else None,
                b_from_log=dict(sample_surface_t95_setpoint_h=13334.3 / 3600, sensor_t95_setpoint_h=6649.8 / 3600,
                                sensor_t99_setpoint_h=18512.7 / 3600, uptake_t50_h=4451.4 / 3600))
            continue
        a, b, c = r["case_a"], r["case_b"], r["case_c"]
        sb = b["series"]
        hum[f"3d_still_h{h}"] = dict(
            a_sample=a["sample"], a_sensor=a["sensor"],
            b_sample_surface_t95_setpoint_h=(b["sample_surface"]["t_95pct_of_setpoint_s"] or float("nan")) / 3600,
            b_sensor_t95_setpoint_h=(b["sensor"]["t_95pct_of_setpoint_s"] or float("nan")) / 3600,
            b_uptake_t50_h=(b["uptake_t50_s"] or float("nan")) / 3600,
            b_uptake_t95_h=(b["uptake_t95_s"] or float("nan")) / 3600 if b["uptake_t95_s"] else None,
            b_uptake_at_6h_mg_g=sb["uptake"][-1], b_equilibrium_mg_g=b["equilibrium_uptake_mg_per_g"],
            b_ideal_t50_min=b["ideal_uptake_t50_s"] / 60, b_ideal_t95_min=b["ideal_uptake_t95_s"] / 60,
            b_sensor_minus_sample_at_1h=at(sb["t"], np.array(sb["sensor"]) - np.array(sb["sample_surface"]), 3600),
            b_sensor_minus_sample_at_3h=at(sb["t"], np.array(sb["sensor"]) - np.array(sb["sample_surface"]), 3 * 3600),
            b_water_needed_mg=b["water_needed_mg"], box_vapour_mg=b["box_vapour_at_setpoint_mg"],
            c_deliquescent_uptake_mg_h=c["uptake_rate_mg_per_h"], c_sensor_RH=c["sensor_RH"],
            c_air_above_sample_RH=c["air_above_sample_RH"])
    f2 = load("humidity_fan2d.json")
    if f2:
        for key, r in f2.items():
            a, c = r["case_a"], r["case_c"]
            b = r.get("case_b")
            k_s = a.get("k_slurry")
            V, A = 0.180 * 0.120 * 0.090 - 0.150 * 0.090 * 0.010, 0.146 * 0.086
            lumped = None
            if k_s and key != "still_2d":
                tau = V / (k_s * A)
                lumped = dict(k_slurry_m_s=k_s, tau_s=tau, t95_setpoint_s=tau * np.log(0.353 / (0.753 - 0.95 * 0.753)),
                              t99_setpoint_s=tau * np.log(0.353 / (0.753 - 0.99 * 0.753)))
            hum[key] = dict(
                lumped_well_mixed_check=lumped,
                a_sample=a["sample"], a_sensor=a["sensor"],
                c_deliquescent_uptake_mg_h=c["uptake_rate_mg_per_h"], c_sensor_RH=c["sensor_RH"],
                flow=r.get("flow"))
            if b:
                sb = b["series"]
                hum[key].update(
                    b_sample_surface_t95_setpoint_h=(b["sample_surface"]["t_95pct_of_setpoint_s"] or float("nan")) / 3600,
                    b_sample_surface_t99_setpoint_h=(b["sample_surface"]["t_99pct_of_setpoint_s"] or float("nan")) / 3600,
                    b_uptake_t50_h=(b["uptake_t50_s"] or float("nan")) / 3600,
                    b_uptake_t95_h=(b["uptake_t95_s"] / 3600) if b["uptake_t95_s"] else None,
                    b_uptake_at_6h_mg_g=sb["uptake"][-1],
                    b_sensor_minus_sample_at_1h=at(sb["t"], np.array(sb["sensor"]) - np.array(sb["sample_surface"]), 3600))
    S["humidity"] = hum
    st = load("stream.json")
    if st:
        S["stream"] = {n: {k: dict(single_over_vacuum=round(v["single_over_vacuum"], 3),
                                   stream_over_vacuum=round(v["stream_over_vacuum"], 3),
                                   entrained_mL_s=round(v["entrained_Q_mL_s"], 1))
                           for k, v in p["1.0_g_s"]["drops"].items()}
                       for n, p in st["powders"].items()}
    fa = {}
    for c in ("fine1", "fine01", "salt1", "fine1_tall", "fine1_h0.50"):
        r = load(f"faraday_flow_{c}.json")
        t = load(f"faraday_track_{c}.json")
        if not r and not t:
            continue
        fa[c] = {}
        if r:
            fa[c] = dict(Q_inlet_down_mL_s=r["Q_inlet_down_mLs"], Q_cup_mouth_up_mL_s=r["Q_cupmouth_up_mLs"],
                         v_up_max_in_cup=r["v_up_max_in_cup"], v_up_inlet_annulus_max=r["v_up_inlet_annulus_max"],
                         stream_v_floor=r["stream_v_at_floor"])
        if t:
            fa[c]["captured"] = {k: {s: round(v["captured"], 3) for s, v in res.items()}
                                 for k, res in t["results"].items()}
            fa[c]["out_of_lid"] = {k: {s: round(v["out_of_lid"], 3) for s, v in res.items()}
                                   for k, res in t["results"].items()}
    S["faraday"] = fa
    orf = load("orifice_air.json")
    if orf:
        S["orifice"] = {k: dict(critical_size=v["critical_size"],
                                W_over_WB={n: {D: round(x["W_over_WB"], 3) for D, x in row.items()}
                                           for n, row in v["powders"].items()})
                        for k, v in orf["cases"].items() if k in ("cup_H20mm_deps0.04", "deep_deps0.04")}
    json.dump(S, open("cfd_summary.json", "w"), indent=1, default=lambda o: None)
    print(json.dumps({k: v for k, v in S.items() if k in ("validation_cavity", "validation_pipe")}, indent=0)[:1500])
    for k, v in hum.items():
        print(k, {kk: (round(vv, 3) if isinstance(vv, float) else vv) for kk, vv in v.items()
                  if kk not in ("a_sample", "a_sensor", "flow")})
        print("   a_sample", v["a_sample"])


if __name__ == "__main__":
    main()
