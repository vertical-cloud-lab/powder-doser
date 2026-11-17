#!/usr/bin/env python3
"""Run 34: how much powder information do a BO campaign's own doses carry?

Reads the 60 spooled trial documents of the salt campaign (`salt-20260929T014732Z`, #166), each with its
balance telemetry, and pulls out the fingerprint-like numbers every three-stage dose contains:

* bulk phase: mg per auger revolution at the dose's bulk tilt and rpm (settled bulk mass / bulk revolutions);
* PI trickle: mg per revolution at the trim tilt and the low rpm the PI chose;
* tap endgame: mg released per tap at the tap tilt, and how often a tap released nothing;
* stops: afterflow mass and its time constant (afterflow / rate at the stop).

It then fits one small rate model to the bulk points, log10(mg/rev) = a + b (tilt - 27.5) + c log10(rpm / 30)
+ d [cadence taps on], and compares what it predicts at the battery's protocol C and D settings with Sam's
salt fingerprint (#116, August). Writes campaign_phases.csv, result.json and campaign_as_data.png.

Usage (from this folder): python extract.py        (about 2 s)
"""
from __future__ import annotations

import csv
import glob
import json
import math
import os
import time
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
TRIALS = HERE / "data" / "salt_trials"
RATE_SUMMARY = HERE.parent / "heldout-powders" / "data" / "rate_summary.csv"
BATTERY = HERE.parent / "heldout-powders" / "data" / "battery_responses.csv"
NUDGE_DEG = 5.0          # campaign's frozen tap_nudge_deg
REF_TILT, REF_RPM = 27.5, 30.0


def parse_rows(doc):
    tel = doc.get("telemetry") or {}
    if not tel.get("header") or not tel.get("rows"):
        return None                      # telemetry was not pulled for this dose
    hdr = tel["header"].split(",")
    out = []
    for line in doc["telemetry"]["rows"]:
        parts = line.split(",")
        row = {}
        for k, v in zip(hdr, parts):
            if k == "phase":
                row[k] = v
            else:
                try:
                    row[k] = float(v) if v != "" else None
                except ValueError:
                    row[k] = None
        out.append(row)
    return out


def stop_event(doc, phase):
    for ev in doc.get("stop_events") or []:
        if ev.get("phase") == phase:
            return ev
    return None


def dose_record(doc):
    p = doc["parameters"]
    pe = doc.get("parameters_executed") or {}
    o = doc.get("outcomes") or {}
    fl = doc.get("flags") or {}
    cov = doc.get("covariates") or {}
    rows = parse_rows(doc)
    have_tel = rows is not None
    rows = rows or []
    ev_b, ev_t = stop_event(doc, "bulk"), stop_event(doc, "trickle")

    # trickle revolutions: each telemetry row's rpm_cmd is the rpm the auger ran at since the previous poll
    trk = [r for r in rows if r["phase"] == "trickle"]
    trickle_rev, trickle_s = 0.0, 0.0
    for a, b in zip(trk[:-1], trk[1:]):
        dt = (b["t_s"] or 0) - (a["t_s"] or 0)
        if 0 < dt < 3 and b.get("rpm_cmd") is not None:
            trickle_rev += b["rpm_cmd"] / 60.0 * dt
            trickle_s += dt
    nudges = o.get("nudges") or 0
    auger_rev = o.get("auger_rev")
    # The firmware's bulk count is rpm x (whole seconds of spin): MicroPython's time.time() has 1 s resolution
    # (main_three_phase.py, _run_phase_continuous), so auger_rev is quantized in steps of rpm/60 rev. The
    # telemetry clock is ticks_ms, so the spin time is taken from it instead: the auger starts one poll before
    # the first bulk row and halts on the poll before the settle gap.
    bulk_rev_fw = None if (auger_rev is None or not have_tel) else auger_rev - trickle_rev - nudges * NUDGE_DEG / 360.0
    bulk_rows = [r for r in rows if r["phase"] == "bulk" and r.get("t_s") is not None]
    bulk_rev, spin_s = None, None
    if len(bulk_rows) >= 2:
        ts = [r["t_s"] for r in bulk_rows]
        gaps = np.diff(ts)
        halt = len(ts) - 1
        for i, g in enumerate(gaps):
            if g > 1.0:                       # settle gap: the halt poll is row i
                halt = i
                break
        poll = float(np.median(gaps[gaps < 1.0])) if np.any(gaps < 1.0) else 0.29
        spin_s = ts[halt] - ts[0] + poll
        bulk_rev = p.get("bulk_rpm") / 60.0 * spin_s

    rec = {
        "label": doc.get("label") or "",
        "trial_uuid": doc["trial_uuid"],
        "telemetry": have_tel,
        "started_utc": doc["started_utc"],
        "mode": doc.get("mode"),
        "status": fl.get("status"),
        "jam": bool(fl.get("jam")),
        "bulk_tap": p.get("bulk_tap"), "trim_tap": p.get("trim_tap"),
        "bulk_tilt_deg": p.get("bulk_tilt_deg"), "bulk_rpm": p.get("bulk_rpm"),
        "trickle_tilt_deg": p.get("trickle_tilt_deg"), "tap_tilt_deg": p.get("tap_tilt_deg"),
        "trickle_start_remaining_g": p.get("trickle_start_remaining_g"), "tolerance_g": p.get("tolerance_g"),
        "tau_afterflow_s": pe.get("tau_afterflow_s"),
        "t_total_s": o.get("t_total_s"), "abs_error_mg": o.get("abs_error_mg"), "taps": o.get("taps"),
        "nudges": nudges, "auger_rev": auger_rev, "bulk_rev_firmware": bulk_rev_fw, "bulk_spin_s": spin_s,
        "doses_since_cup_empty": cov.get("doses_since_cup_empty"), "recycle_count": cov.get("recycle_count"),
        "hopper_refills": cov.get("hopper_refills"), "cup_load_g": cov.get("cup_load_g"),
        "bulk_mass_mg": None, "bulk_rev": None, "bulk_mg_rev": None, "bulk_stalled": None,
        "bulk_afterflow_mg": None, "bulk_rate_stop_mg_s": None, "bulk_tau_s": None, "bulk_run_s_telemetry": None,
        "trickle_mass_mg": None, "trickle_rev": None, "trickle_mg_rev": None, "trickle_mean_rpm": None,
        "trickle_stalled": None, "trickle_afterflow_mg": None,
        "tap_n": 0, "tap_mass_mg": None, "tap_mg_per_tap": None, "tap_median_mg": None, "tap_zero_frac": None,
    }
    if ev_b is not None and bulk_rev is not None and bulk_rev > 0:
        rec["bulk_mass_mg"] = 1000.0 * ev_b["settled_g"]
        rec["bulk_rev"] = bulk_rev
        rec["bulk_mg_rev"] = rec["bulk_mass_mg"] / bulk_rev
        rec["bulk_stalled"] = ev_b.get("stalled")
        rec["bulk_afterflow_mg"] = 1000.0 * (ev_b.get("afterflow_g") or 0.0)
        rs = ev_b.get("rate_slope_gps")
        rec["bulk_rate_stop_mg_s"] = None if rs is None else 1000.0 * rs
        if rs and rs > 1e-3:
            rec["bulk_tau_s"] = (ev_b.get("afterflow_g") or 0.0) / rs
        rec["bulk_run_s_telemetry"] = spin_s
    m_after_trickle = None
    if ev_t is not None and ev_b is not None and have_tel:
        rec["trickle_mass_mg"] = 1000.0 * (ev_t["settled_g"] - ev_b["settled_g"])
        rec["trickle_rev"] = trickle_rev
        rec["trickle_stalled"] = ev_t.get("stalled")
        rec["trickle_afterflow_mg"] = 1000.0 * (ev_t.get("afterflow_g") or 0.0)
        if trickle_rev > 0.05:
            rec["trickle_mg_rev"] = rec["trickle_mass_mg"] / trickle_rev
            rec["trickle_mean_rpm"] = 60.0 * trickle_rev / trickle_s if trickle_s > 0 else None
        m_after_trickle = ev_t["settled_g"]
    elif ev_b is not None:
        m_after_trickle = ev_b["settled_g"]
    # tap endgame: one settled reading per tap cycle (taps_per_cycle = 1)
    taps = [r for r in rows if r["phase"] == "tap" and r.get("z_g") is not None]
    if taps and m_after_trickle is not None:
        z = np.array([m_after_trickle] + [r["z_g"] for r in taps])
        inc = 1000.0 * np.diff(z)
        rec["tap_n"] = len(inc)
        rec["tap_mass_mg"] = float(inc.sum())
        rec["tap_mg_per_tap"] = float(inc.mean())
        rec["tap_median_mg"] = float(np.median(inc))
        rec["tap_zero_frac"] = float(np.mean(inc < 0.2))
    return rec


def ols(X, y):
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    res = y - X @ beta
    dof = max(1, len(y) - X.shape[1])
    s2 = float(res @ res) / dof
    cov = s2 * np.linalg.inv(X.T @ X)
    return beta, cov, math.sqrt(s2), res


def design(tilt, rpm, tap):
    tilt, rpm, tap = map(np.asarray, (tilt, rpm, tap))
    return np.column_stack([np.ones_like(tilt, dtype=float), tilt - REF_TILT, np.log10(rpm / REF_RPM), tap])


def predict(beta, cov, s, tilt, rpm, tap=0.0):
    x = design([tilt], [rpm], [tap])[0]
    mu = float(x @ beta)
    se_mean = math.sqrt(float(x @ cov @ x))
    se_pred = math.sqrt(se_mean ** 2 + s ** 2)
    return {"mg_rev": 10 ** mu, "mean_90": [10 ** (mu - 1.645 * se_mean), 10 ** (mu + 1.645 * se_mean)],
            "single_90": [10 ** (mu - 1.645 * se_pred), 10 ** (mu + 1.645 * se_pred)]}


def read_sam():
    with open(RATE_SUMMARY) as f:
        row = next(r for r in csv.DictReader(f) if r["powder_id"] == "salt")
    with open(BATTERY) as f:
        pooled = next(r for r in csv.DictReader(f) if r["powder_id"] == "salt")
    g = lambda k: float(row[k])
    return {
        "run_id": row["run_id"],
        "mg_rev_0": g("mg_rev_tilt0deg"), "mg_rev_22p5": g("mg_rev_tilt22p5deg"), "mg_rev_45": g("mg_rev_tilt45deg"),
        "rsd_pct_22p5": g("rsd_pct_tilt22p5deg"),
        "mg_rev_15rpm": g("mg_rev_15rpm"), "mg_rev_45rpm": g("mg_rev_45rpm"), "mg_rev_90rpm": g("mg_rev_90rpm"),
        "speed_exponent": g("speed_exponent_alpha"),
        "mg_per_tap_0": g("mg_per_tap_tilt0deg"),
        "pooled_mg_rev_0_22p5_45": [float(pooled["ff0_mg_per_rev"]), float(pooled["ff45_mg_per_rev"]),
                                   float(pooled["ff90_mg_per_rev"])],
        "pooled_mg_per_tap_22p5": float(pooled["tap45_mg_per_tap"]),
    }


def main():
    t0 = time.time()
    docs = [json.load(open(f)) for f in sorted(glob.glob(str(TRIALS / "trial_*.json")))]
    docs.sort(key=lambda d: d["started_utc"])
    recs = [dose_record(d) for d in docs]
    for i, r in enumerate(recs):
        r["dose_order"] = i
    # labels come from the campaign records; the trial docs carry only the uuid
    rec_path = HERE.parent / "ml-property-dose" / "data" / "salt_campaign_records.jsonl"
    labels = {}
    for line in open(rec_path):
        j = json.loads(line)
        labels[j["trial_uuid"]] = (j.get("label"), j.get("mode"))
    for r in recs:
        lab, mode = labels.get(r["trial_uuid"], ("", r["mode"]))
        r["label"], r["mode"] = lab, mode

    keys = list(recs[0].keys())
    with open(HERE / "campaign_phases.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader()
        for r in recs:
            w.writerow({k: (round(v, 4) if isinstance(v, float) else v) for k, v in r.items()})

    sam = read_sam()

    # ---- bulk rate model -------------------------------------------------------------------------------------
    # "jam" in this campaign means the tap endgame ran out of cycles (cycle-budget); the bulk phase before it is
    # still a clean measurement, so only stalled bulks and doses without telemetry are left out
    use = [r for r in recs if r["bulk_mg_rev"] and r["bulk_rev"] >= 0.5 and not r["bulk_stalled"]]
    tilt = np.array([r["bulk_tilt_deg"] for r in use])
    rpm = np.array([r["bulk_rpm"] for r in use])
    tap = np.array([1.0 if r["bulk_tap"] == "2hz" else 0.0 for r in use])
    y = np.log10([r["bulk_mg_rev"] for r in use])
    X = design(tilt, rpm, tap)
    beta, cov, s, res = ols(X, y)
    se = np.sqrt(np.diag(cov))
    alpha = 1.0 + beta[2]
    pred = {
        "tilt22p5_30rpm": predict(beta, cov, s, 22.5, 30.0),
        "tilt45_30rpm_extrapolated": predict(beta, cov, s, 45.0, 30.0),
        "tilt0_30rpm_extrapolated": predict(beta, cov, s, 0.0, 30.0),
        "tilt22p5_15rpm": predict(beta, cov, s, 22.5, 15.0),
        "tilt22p5_90rpm": predict(beta, cov, s, 22.5, 90.0),
    }
    # leave-one-dose-out residuals and a time split: first half of the campaign predicts the second
    loo = []
    for i in range(len(y)):
        m = np.ones(len(y), bool); m[i] = False
        b_i, *_ = np.linalg.lstsq(X[m], y[m], rcond=None)
        loo.append(y[i] - X[i] @ b_i)
    loo = np.array(loo)
    order = np.array([r["dose_order"] for r in use])
    half = order < np.median(order)
    b_h, *_ = np.linalg.lstsq(X[half], y[half], rcond=None)
    split_res = y[~half] - X[~half] @ b_h
    # drift: residual against dose order and recycle count
    rec_cnt = np.array([r["recycle_count"] or 0 for r in use], float)
    drift_slope = float(np.polyfit(order, res, 1)[0]) if len(order) > 2 else None

    # interaction sensitivity: does the tilt effect shrink at high rpm?
    Xi = np.column_stack([X, X[:, 1] * X[:, 2]])
    b_i, cov_i, s_i, _ = ols(Xi, y)
    # hopper emptying: the cup on the balance holds what has left the hopper this session
    cup = np.array([r["cup_load_g"] or 0.0 for r in use])
    cup_slope = float(np.polyfit(cup, res, 1)[0]) * 10.0
    cup_corr = float(np.corrcoef(cup, res)[0, 1])
    # the same settings on two days, and how well one dose repeats (validation blocks, 6 Oct)
    same = {}
    for key, name in (((40.0, 20.0, "2hz"), "corner-09 settings (40 deg, 20 rpm, bulk taps)"),
                      ((40.0, 100.0, "2hz"), "bo-005 settings (40 deg, 100 rpm, bulk taps)")):
        by_day = {}
        for r in use:
            if (r["bulk_tilt_deg"], r["bulk_rpm"], r["bulk_tap"]) == key:
                by_day.setdefault(r["started_utc"][:10], []).append(r["bulk_mg_rev"])
        same[name] = {d: {"n": len(v), "mean_mg_rev": float(np.mean(v)),
                          "cv_pct": float(100 * np.std(v, ddof=1) / np.mean(v)) if len(v) > 1 else None}
                      for d, v in sorted(by_day.items())}
    fw = np.array([r["bulk_rev_firmware"] for r in use if r["bulk_rev_firmware"] is not None])
    tl = np.array([r["bulk_rev"] for r in use if r["bulk_rev_firmware"] is not None])
    fw_err_pct = 100 * np.abs(fw - tl) / tl

    # ---- trickle points: does the same model carry to low rpm and low tilt? ------------------------------------
    trk = [r for r in recs if r["trickle_mg_rev"] and r["trickle_rev"] >= 0.2 and r["trickle_mean_rpm"]]
    t_tilt = np.array([r["trickle_tilt_deg"] for r in trk])
    t_rpm = np.array([r["trickle_mean_rpm"] for r in trk])
    t_tap = np.array([1.0 if r["trim_tap"] == "2hz" else 0.0 for r in trk])
    t_y = np.log10(np.clip([r["trickle_mg_rev"] for r in trk], 1e-3, None))
    t_pred = design(t_tilt, t_rpm, t_tap) @ beta
    t_res = t_y - t_pred

    # ---- stops and taps ---------------------------------------------------------------------------------------
    taus = np.array([r["bulk_tau_s"] for r in recs if r["bulk_tau_s"] is not None and r["bulk_rate_stop_mg_s"] > 20])
    tp = [r for r in recs if r["tap_n"] >= 3]
    tap_tilt = np.array([r["tap_tilt_deg"] for r in tp])
    tap_mean = np.array([r["tap_mg_per_tap"] for r in tp])
    tap_zero = np.array([r["tap_zero_frac"] for r in tp])
    tap_total = int(sum(r["tap_n"] for r in recs))

    # ---- coverage of the box and campaign cost -----------------------------------------------------------------
    allb = [r for r in recs if r["bulk_tilt_deg"] is not None]
    bt = np.array([r["bulk_tilt_deg"] for r in allb]); br = np.array([r["bulk_rpm"] for r in allb])
    modes = {}
    for r in recs:
        modes[r["mode"]] = modes.get(r["mode"], 0) + 1
    bo = [r for r in allb if r["mode"] == "bo"]
    bo_t = np.array([r["bulk_tilt_deg"] for r in bo]); bo_r = np.array([r["bulk_rpm"] for r in bo])
    t_start = min(d["started_utc"] for d in docs); t_end = max(d["ended_utc"] for d in docs)
    dose_s = float(sum((r["t_total_s"] or 0) for r in recs))
    revs_total = float(sum((r["auger_rev"] or 0) for r in recs))
    mass_total = float(sum(1000 * (d["outcomes"].get("settled_final_g") or 0) for d in docs))

    result = {
        "run": "campaign-as-data",
        "code": "own numpy",
        "version": np.__version__,
        "status": "ran",
        "wall_s": round(time.time() - t0, 1),
        "inputs": {"campaign": "salt-20260929T014732Z", "doses": len(recs), "modes": modes,
                   "sam_fingerprint_run": sam["run_id"]},
        "campaign_cost": {"first_dose_utc": t_start, "last_dose_utc": t_end,
                          "sum_dose_time_min": round(dose_s / 60, 1),
                          "auger_rev_total": round(revs_total, 1), "dosed_mass_total_g": round(mass_total / 1000, 2),
                          "taps_total": tap_total},
        "bulk_model": {
            "n_doses": int(len(y)),
            "formula": "log10(mg/rev) = a + b (tilt - 27.5) + c log10(rpm/30) + d [bulk cadence taps]",
            "coef": {"a": float(beta[0]), "b_per_deg": float(beta[1]), "c": float(beta[2]), "d_tap": float(beta[3])},
            "se": {"a": float(se[0]), "b_per_deg": float(se[1]), "c": float(se[2]), "d_tap": float(se[3])},
            "resid_sd_log10": s, "resid_sd_pct": 100 * (10 ** s - 1),
            "loo_rmse_log10": float(np.sqrt(np.mean(loo ** 2))),
            "first_half_predicts_second_rmse_log10": float(np.sqrt(np.mean(split_res ** 2))),
            "first_half_predicts_second_bias_log10": float(np.mean(split_res)),
            "resid_slope_per_dose_log10": drift_slope,
            "speed_exponent_alpha": alpha, "speed_exponent_90": [alpha - 1.645 * se[2], alpha + 1.645 * se[2]],
            "predictions": pred,
        },
        "sam_salt_fingerprint": sam,
        "comparison": {
            "mg_rev_22p5_30rpm": {"campaign": pred["tilt22p5_30rpm"]["mg_rev"], "sam": sam["mg_rev_22p5"],
                                  "sam_pooled_two_runs": sam["pooled_mg_rev_0_22p5_45"][1]},
            "mg_rev_45_30rpm": {"campaign_extrapolated": pred["tilt45_30rpm_extrapolated"]["mg_rev"],
                                "sam": sam["mg_rev_45"], "sam_pooled_two_runs": sam["pooled_mg_rev_0_22p5_45"][2]},
            "mg_rev_0_30rpm": {"campaign_extrapolated": pred["tilt0_30rpm_extrapolated"]["mg_rev"],
                               "sam": sam["mg_rev_0"]},
            "speed_exponent": {"campaign": alpha, "sam": sam["speed_exponent"]},
        },
        "interaction_model": {"tilt_x_log10rpm": float(b_i[4]), "se": float(np.sqrt(cov_i[4, 4])),
                              "resid_sd_log10": s_i,
                              "mg_rev_22p5_30rpm": float(10 ** (np.array([1, -5.0, 0, 0, 0]) @ b_i)),
                              "speed_exponent_at_15deg": float(1 + b_i[2] + b_i[4] * (15 - REF_TILT)),
                              "speed_exponent_at_40deg": float(1 + b_i[2] + b_i[4] * (40 - REF_TILT))},
        "fill_level": {"resid_change_log10_per_10g_dosed": cup_slope, "corr": cup_corr,
                       "cup_load_max_g": float(cup.max())},
        "same_settings_by_day": same,
        "firmware_rev_count": {"note": "rpm x whole seconds of spin (1 s clock)",
                               "median_abs_err_pct": float(np.median(fw_err_pct)),
                               "max_abs_err_pct": float(np.max(fw_err_pct))},
        "trickle_check": {"n": int(len(t_y)), "tilt_range": [float(t_tilt.min()), float(t_tilt.max())],
                          "rpm_range": [float(t_rpm.min()), float(t_rpm.max())],
                          "median_resid_log10": float(np.median(t_res)),
                          "rmse_log10": float(np.sqrt(np.mean(t_res ** 2)))},
        "afterflow": {"n_bulk_stops": int(len(taus)), "tau_median_s": float(np.median(taus)) if len(taus) else None,
                      "tau_iqr_s": [float(np.percentile(taus, 25)), float(np.percentile(taus, 75))] if len(taus) else None,
                      "campaign_refit_tau_s": 0.834},
        "taps": {"doses_with_tap_phase": int(len(tp)), "taps_total": tap_total,
                 "mg_per_tap_median_over_doses": float(np.median(tap_mean)),
                 "mg_per_tap_range": [float(tap_mean.min()), float(tap_mean.max())],
                 "zero_release_fraction_median": float(np.median(tap_zero)),
                 "spearman_mg_per_tap_vs_tap_tilt": float(spearman(tap_tilt, tap_mean))},
        "coverage": {"bulk_tilt_range": [float(bt.min()), float(bt.max())],
                     "bulk_rpm_range": [float(br.min()), float(br.max())],
                     "bo_doses": int(len(bo)),
                     "bo_frac_tilt_ge_38": float(np.mean(bo_t >= 38)) if len(bo) else None,
                     "bo_frac_rpm_ge_90": float(np.mean(bo_r >= 90)) if len(bo) else None},
    }
    result["key_results"] = {
        "campaign mg/rev at 22.5 deg, 30 rpm (Sam: %.0f)" % sam["mg_rev_22p5"]: round(pred["tilt22p5_30rpm"]["mg_rev"], 1),
        "speed exponent (Sam: %.2f)" % sam["speed_exponent"]: round(alpha, 2),
        "bulk points": int(len(y)),
    }
    figure(recs, use, X, y, beta, cov, s, sam, trk, t_res, tp, tap_tilt, tap_mean, order, res, bo_t, bo_r, bt, br)
    result["wall_s"] = round(time.time() - t0, 1)
    (HERE / "result.json").write_text(json.dumps(result, indent=1) + "\n")
    print(json.dumps({k: result[k] for k in ("campaign_cost", "comparison", "interaction_model", "fill_level",
                                             "same_settings_by_day", "firmware_rev_count", "trickle_check",
                                             "afterflow", "taps", "coverage")}, indent=1))
    print("bulk model", json.dumps(result["bulk_model"]["coef"]), "se", json.dumps(result["bulk_model"]["se"]),
          "sd %.3f loo %.3f split %.3f bias %.3f" % (s, result["bulk_model"]["loo_rmse_log10"],
                                                     result["bulk_model"]["first_half_predicts_second_rmse_log10"],
                                                     result["bulk_model"]["first_half_predicts_second_bias_log10"]))


def spearman(a, b):
    ra = np.argsort(np.argsort(a)); rb = np.argsort(np.argsort(b))
    return np.corrcoef(ra, rb)[0, 1]


def figure(recs, use, X, y, beta, cov, s, sam, trk, t_res, tp, tap_tilt, tap_mean, order, res, bo_t, bo_r, bt, br):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    INK, INK2, GRID = "#1f2328", "#59636e", "#d0d7de"
    C1, C2, C3 = "#0969da", "#bc4c00", "#1a7f37"
    plt.rcParams.update({"font.size": 8, "axes.edgecolor": INK2, "axes.labelcolor": INK, "xtick.color": INK2,
                         "ytick.color": INK2, "axes.spines.top": False, "axes.spines.right": False})
    fig, ax = plt.subplots(1, 4, figsize=(13.2, 3.4), constrained_layout=True)

    # (a) where the campaign put its bulk doses, coloured by mode
    a = ax[0]
    mode_c = {"screen": C2, "recenter": "#8250df", "bo": C1, "validation": C3}
    rng = np.random.default_rng(0)
    counts = {}
    for mode in ("screen", "recenter", "bo", "validation"):
        m = [r for r in recs if r["mode"] == mode and r["bulk_tilt_deg"] is not None]
        if not m:
            continue
        for r in m:
            k = (r["bulk_tilt_deg"], r["bulk_rpm"])
            counts[k] = counts.get(k, 0) + 1
        a.scatter([r["bulk_tilt_deg"] + rng.uniform(-0.9, 0.9) for r in m],
                  [r["bulk_rpm"] + rng.uniform(-2.5, 2.5) for r in m], s=12,
                  c=mode_c[mode], label=f"{mode} ({len(m)})", alpha=0.7, edgecolors="none")
    for (tx, ry), n in counts.items():
        if n >= 4:
            a.annotate(f"{n}", (tx, ry), xytext=(6 if tx < 30 else -12, 5), textcoords="offset points",
                       fontsize=7, color=INK)
    a.scatter([22.5, 45, 0], [30, 30, 30], marker="s", s=28, facecolors="none", edgecolors=INK,
              label="Sam's protocol C")
    a.scatter([22.5] * 3, [15, 45, 90], marker="^", s=24, facecolors="none", edgecolors=INK,
              label="protocol D")
    a.axvspan(15, 40, color=GRID, alpha=0.35, lw=0)
    a.set_xlabel("bulk tilt (deg)"); a.set_ylabel("bulk rpm")
    a.set_xlim(-3, 48); a.set_ylim(0, 108)
    a.set_title("(a) bulk settings of the 60 doses", loc="left", fontsize=8.5)
    a.legend(fontsize=6.5, frameon=False, loc="lower left")

    # (b) bulk mg/rev vs tilt with the fitted model at three rpm, plus Sam's fingerprint
    b = ax[1]
    tilt = X[:, 1] + REF_TILT
    rpm = REF_RPM * 10 ** X[:, 2]
    sc = b.scatter(tilt, 10 ** y, c=np.log10(rpm), cmap="viridis", s=16, edgecolors="none")
    for rr, ls in ((30, "-"), (90, "--")):
        for lo, hi, lw, lab in ((15, 40, 1.2, f"fit, {rr} rpm"), (0, 15, 0.6, None), (40, 45, 0.6, None)):
            tt = np.linspace(lo, hi, 40)
            yy = design(tt, np.full_like(tt, rr), np.zeros_like(tt)) @ beta
            b.plot(tt, 10 ** yy, color=INK2, ls=ls, lw=lw, label=lab)
    b.errorbar([0, 22.5, 45], [sam["mg_rev_0"], sam["mg_rev_22p5"], sam["mg_rev_45"]],
               yerr=[0, sam["mg_rev_22p5"] * sam["rsd_pct_22p5"] / 100 / math.sqrt(6), 0], fmt="s", ms=5,
               mfc="white", mec=INK, ecolor=INK, capsize=2, label="Sam, protocol C (30 rpm)")
    b.scatter([0, 22.5, 45], sam["pooled_mg_rev_0_22p5_45"], marker="x", s=22, c=INK, label="#163 pooled, 2 runs")
    b.axvspan(15, 40, color=GRID, alpha=0.35, lw=0)
    b.set_yscale("log"); b.set_xlabel("tilt (deg)"); b.set_ylabel("mg per revolution")
    b.set_title("(b) mg/rev from each dose's bulk phase", loc="left", fontsize=8.5)
    b.legend(fontsize=6.5, frameon=False, loc="lower right")
    cb = fig.colorbar(sc, ax=b, shrink=0.8, pad=0.01)
    cb.set_label("log10 rpm", fontsize=7)

    # (c) residuals against dose order: does the powder drift over the campaign?
    c = ax[2]
    c.axhline(0, color=GRID, lw=1)
    c.scatter(order, 100 * (10 ** res - 1), s=14, c=C1, edgecolors="none", label="bulk")
    tr_order = np.array([r["dose_order"] for r in trk])
    c.scatter(tr_order, 100 * (10 ** t_res - 1), s=14, c=C2, marker="D", edgecolors="none",
              label="trim (PI trickle), same model")
    c.set_xlabel("dose number in the campaign"); c.set_ylabel("measured / model − 1 (%)")
    c.set_ylim(-100, 200)
    c.set_title("(c) misfit along the campaign", loc="left", fontsize=8.5)
    c.legend(fontsize=6.5, frameon=False, loc="upper left")

    # (d) taps: mean release per tap against tap tilt
    d = ax[3]
    d.scatter(tap_tilt, tap_mean, s=16, c=C3, edgecolors="none", label="campaign tap phase (mean per dose)")
    d.errorbar([0.0], [sam["mg_per_tap_0"]], fmt="s", ms=5, mfc="white", mec=INK, label="Sam, protocol E (0 deg)")
    d.scatter([22.5], [sam["pooled_mg_per_tap_22p5"]], marker="x", s=22, c=INK, label="#163 pooled (22.5 deg)")
    d.set_yscale("log"); d.set_xlabel("tilt during taps (deg)"); d.set_ylabel("mg per tap")
    d.set_title("(d) tap endgame", loc="left", fontsize=8.5)
    d.legend(fontsize=6.5, frameon=False, loc="lower right")
    fig.savefig(HERE / "campaign_as_data.png", dpi=170)


if __name__ == "__main__":
    main()
