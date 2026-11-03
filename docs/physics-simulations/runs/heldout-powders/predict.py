"""Can the physics simulations predict held-out powders in Sam's 13-powder battery (#116)?

Every model is scored leave-one-powder-out (LOPO): it is fitted on 11 powders and predicts the 12th
(the 12 powders that have literature properties; fumed silica has none). Targets are log10 mg/rev at
45 and 22.5 deg tilt from battery protocol C (30 rpm, 6 single revolutions per tilt), taken from Sam's
paper. Values below 0.1 mg/rev are floored at 0.1 (about one grain of salt, and the balance step).

Forward models (literature properties -> mg/rev):
  mean        training mean (no information)
  aor_ols     log10 mg/rev = a + b * AoR (2 parameters)
  aor_rho_ols log10 mg/rev = a + b * AoR + c * log10(rho_p) (3 parameters)
  aor_iso     isotonic (monotone non-increasing) fit on AoR
  bond_ols    log10 mg/rev = a + b * log10 Bo, Bo = van der Waals pull-off / grain weight from d50, rho_p
  bev0        Beverloo through the core-tip annulus with g sin(tilt), per-powder d50 and bulk density,
              no fitted parameter (run 24 extended to every powder)
  dem0        DEM chain, no fitted parameter: literature AoR -> position on the DEM angle-of-repose path ->
              DEM doser mg/rev at that position (twin at 30 rpm) x rho_p / rho_salt
  dem_shift   the same with one fitted offset between literature and DEM repose angles
  dem_shift_scale  plus a fitted log10 scale (2 parameters)
Inverse model (dosing fingerprint -> AoR), mirroring the paper's claim:
  inv_ols     AoR = a + b * log10 mg/rev(45 deg) (2 parameters)
  inv_dem     measured mg/rev at both tilts -> DEM path position -> DEM repose angle + fitted offset

usage: python predict.py          # reads data/, doser_path.json, aor_path.json; writes predictions.json,
                                  # result.json and the figures
"""
from __future__ import annotations

import csv
import json
import math
import os
import sys

import numpy as np
from scipy import stats

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
FLOOR = 0.1               # mg/rev
RHO_SALT = 2165.0         # kg/m3, DEM particle density
TILTS = {"45": 45.0, "22p5": 22.5}
FLOW_THRESHOLD = 50.0     # mg/rev at 45 deg: "conveys" vs "does not convey"

# ----------------------------------------------------------------------------------------- data


def read_csv(name):
    with open(os.path.join(DATA, name), newline="") as f:
        return list(csv.DictReader(f))


def fnum(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return float("nan")


def load_powders():
    rate = {r["powder_id"]: r for r in read_csv("rate_summary.csv")}
    lit = {r["powder_id"]: r for r in read_csv("literature_powder_properties.csv")}
    rng = {}
    for r in read_csv("literature_powder_properties_long.csv"):
        if r["property"] == "angle_of_repose":
            rng[r["powder_id"]] = (fnum(r["range_low"]), fnum(r["range_high"]), r["specificity"])
    dose = {}
    for r in read_csv("dose_summary_by_powder_target.csv"):
        if r["target_mg"] == "1000.0":
            dose[r["powder_id"]] = r
    out = []
    for pid, L in lit.items():
        R = rate[pid]
        p = {
            "powder_id": pid, "display": R["display"], "track": R["track"],
            "aor": fnum(L["angle_repose_deg"]), "aor_lo": rng.get(pid, (np.nan,) * 3)[0],
            "aor_hi": rng.get(pid, (np.nan,) * 3)[1], "aor_specificity": rng.get(pid, (None,) * 3)[2],
            "rho_p": fnum(L["true_density_g_cm3"]) * 1000.0, "rho_b": fnum(L["bulk_density_g_ml"]) * 1000.0,
            "hausner": fnum(L["hausner_ratio"]), "d50_um": fnum(L["d50_um"]), "moisture_pct": fnum(L["moisture_pct"]),
            "shape": L["shape"],
            "mg_rev": {"0": fnum(R["mg_rev_tilt0deg"]), "22p5": fnum(R["mg_rev_tilt22p5deg"]),
                       "45": fnum(R["mg_rev_tilt45deg"])},
            "speed_alpha": fnum(R["speed_exponent_alpha"]), "qc_valid": R["qc_valid"] == "True",
        }
        d = dose.get(pid)
        if d:
            n_pass, n = (int(v) for v in d["pass_5pct"].split("/"))
            p["dose1g"] = {"n": n, "pass_5pct": n_pass, "mean_time_s": fnum(d["mean_time_s"])}
        out.append(p)
    return out


def logy(v):
    return math.log10(max(v, FLOOR))

# ------------------------------------------------------------------------------- physics features


def bond_number(d50_um, rho_p, A=1.0e-19, z0=0.4e-9, r_asp=0.1e-6, g=9.81):
    """van der Waals pull-off at one asperity of radius r_asp (Rumpf) over the grain weight."""
    F = A * r_asp / (12 * z0 ** 2)
    d = d50_um * 1e-6
    return F / (rho_p * g * math.pi / 6 * d ** 3)


def beverloo_annulus_mg_rev(d50_um, rho_b, tilt_deg, rpm=30.0, k=1.5, C=1.03, ri=0.43e-3, ro=1.5e-3):
    """Run 24's outlet-limited model: the core-tip annulus unrolled into a closed slot,
    W = C rho_b sqrt(g sin tilt) L (b - k d)^1.5, converted to mg per auger revolution."""
    g_eff = 9.81 * math.sin(math.radians(tilt_deg))
    b = ro - ri
    be = max(b - k * d50_um * 1e-6, 0.0)
    W = C * rho_b * math.sqrt(g_eff) * math.pi * (ri + ro) * be ** 1.5      # kg/s
    return W * 1e6 * 60.0 / rpm

# ------------------------------------------------------------------------------------ DEM chain


def u_of(point):
    """Path coordinate: P0 = -1 (smooth grains), P1 = 0 (salt), kNNNN = NNNN / 1000 (SJKR, kJ/m3)."""
    return {"P0": -1.0, "P1": 0.0}.get(point, None) if point in ("P0", "P1") else float(point[1:]) / 1000.0


def dem_rate(r):
    """mg/rev of a twin case: after the first quarter revolution, or, for stalled cases stopped early
    (0.2-0.5 rev simulated), after the opening burst."""
    if r.get("mg_per_rev_after_quarter") is not None:
        return r["mg_per_rev_after_quarter"]
    return r.get("mg_per_rev_after_burst")


class DemChain:
    def __init__(self, doser, aor):
        doser = [r for r in doser if r.get("tilt_deg") is not None and r.get("rpm", 30) == 30
                 and r.get("d_mean_mm", 0.425) == 0.425]
        self.aor_u = np.array([u_of(r["point"]) for r in aor])
        self.aor_deg = np.array([r["angle_iso_deg"] for r in aor])
        o = np.argsort(self.aor_u)
        self.aor_u, self.aor_deg = self.aor_u[o], self.aor_deg[o]
        # enforce a monotone (non-decreasing) AoR along the path for the inversion
        self.aor_mono = np.maximum.accumulate(self.aor_deg)
        self.doser = {}
        for key, tilt in TILTS.items():
            pts = sorted((u_of(r["path_point"]), dem_rate(r)) for r in doser
                         if abs(r["tilt_deg"] - tilt) < 1e-6 and dem_rate(r) is not None)
            if pts:
                self.doser[key] = (np.array([p[0] for p in pts]), np.array([logy(p[1]) for p in pts]))

    def u_from_aor(self, aor_deg):
        """Position on the path whose DEM (ISO apex) repose angle equals aor_deg (clamped at the ends)."""
        a, u = self.aor_mono, self.aor_u
        if aor_deg <= a[0]:
            return float(u[0])
        if aor_deg >= a[-1]:
            return float(u[-1])
        # first segment where the monotone curve crosses aor_deg
        i = int(np.searchsorted(a, aor_deg, side="left"))
        a0, a1, u0, u1 = a[i - 1], a[i], u[i - 1], u[i]
        return float(u0 + (aor_deg - a0) / (a1 - a0) * (u1 - u0)) if a1 > a0 else float(u1)

    def aor_from_u(self, u):
        return float(np.interp(u, self.aor_u, self.aor_mono))

    def logmg(self, u, key):
        """log10 mg/rev of the salt-density twin at path position u; outside the simulated points the
        last segment's slope is continued (floored at 0.1 mg/rev); below u = 0 at 22.5 deg, the 45 deg
        P0/P1 difference is added."""
        us, ys = self.doser[key]
        if u <= us[0]:
            if us[0] > -1.0 and "45" in self.doser and key != "45":
                u45, y45 = self.doser["45"]
                d = np.interp(u, u45, y45) - np.interp(us[0], u45, y45)
                return float(ys[0] + d)
            if len(us) > 1 and u < us[0]:
                return float(ys[0] + (u - us[0]) * (ys[1] - ys[0]) / (us[1] - us[0]))
            return float(ys[0])
        if u >= us[-1]:
            slope = (ys[-1] - ys[-2]) / (us[-1] - us[-2]) if len(us) > 1 else 0.0
            return float(max(ys[-1] + (u - us[-1]) * min(slope, 0.0), math.log10(FLOOR)))
        return float(np.interp(u, us, ys))

    def predict(self, p, key, shift=0.0, scale=0.0, density="particle"):
        u = self.u_from_aor(p["aor"] - shift)
        y = self.logmg(u, key)
        if density == "particle":
            y += math.log10(p["rho_p"] / RHO_SALT)
        else:   # bulk: literature bulk density over the DEM salt bed's 1249 kg/m3 (run 5, poured)
            y += math.log10(p["rho_b"] / 1249.0)
        return max(y + scale, math.log10(FLOOR)), u

# ------------------------------------------------------------------------------------- LOPO


def ols(X, y):
    X1 = np.column_stack([np.ones(len(X)), X])
    beta, *_ = np.linalg.lstsq(X1, y, rcond=None)
    return beta


def isotonic_decreasing(x, y):
    """Pool-adjacent-violators for a non-increasing fit; returns a predictor (step interpolation)."""
    o = np.argsort(x)
    xs, ys = np.asarray(x)[o], np.asarray(y)[o]
    blocks = [[v, 1.0, [xx]] for v, xx in zip(ys, xs)]
    i = 0
    while i < len(blocks) - 1:
        if blocks[i][0] < blocks[i + 1][0]:      # violation of non-increasing
            v = (blocks[i][0] * blocks[i][1] + blocks[i + 1][0] * blocks[i + 1][1]) / (blocks[i][1] + blocks[i + 1][1])
            blocks[i] = [v, blocks[i][1] + blocks[i + 1][1], blocks[i][2] + blocks[i + 1][2]]
            del blocks[i + 1]
            i = max(i - 1, 0)
        else:
            i += 1
    knots_x = np.array([np.mean(b[2]) for b in blocks])
    knots_y = np.array([b[0] for b in blocks])
    return lambda xq: float(np.interp(xq, knots_x, knots_y))


def lopo(powders, key, chain, models=None):
    y = np.array([logy(p["mg_rev"][key]) for p in powders])
    aor = np.array([p["aor"] for p in powders])
    lrho = np.log10([p["rho_p"] for p in powders])
    lbo = np.log10([bond_number(p["d50_um"], p["rho_p"]) for p in powders])
    tilt = TILTS[key]
    bev = np.array([logy(beverloo_annulus_mg_rev(p["d50_um"], p["rho_b"], tilt)) for p in powders])
    preds = {m: np.full(len(powders), np.nan) for m in
             ("mean", "aor_ols", "aor_rho_ols", "aor_iso", "bond_ols", "bev0", "bev_scale")}
    fitted = {"dem_shift": [], "dem_shift_scale": []}
    if chain is not None and key in chain.doser:
        for m in ("dem0", "dem0_bulk", "dem_shift", "dem_shift_scale"):
            preds[m] = np.full(len(powders), np.nan)
    shifts = np.arange(-10.0, 15.01, 0.25)
    if models is not None:
        preds = {m: v for m, v in preds.items() if m in models}
    for i in range(len(powders)):
        tr = np.array([j for j in range(len(powders)) if j != i])
        if models is not None:
            if "aor_ols" in preds:
                b = ols(aor[tr], y[tr]); preds["aor_ols"][i] = b[0] + b[1] * aor[i]
            if "dem_shift" in preds:
                sse = [np.sum((np.array([chain.predict(powders[j], key, shift=s)[0] for j in tr]) - y[tr]) ** 2) for s in shifts]
                preds["dem_shift"][i] = chain.predict(powders[i], key, shift=float(shifts[int(np.argmin(sse))]))[0]
            continue
        preds["mean"][i] = y[tr].mean()
        b = ols(aor[tr], y[tr]); preds["aor_ols"][i] = b[0] + b[1] * aor[i]
        b = ols(np.column_stack([aor[tr], lrho[tr]]), y[tr]); preds["aor_rho_ols"][i] = b[0] + b[1] * aor[i] + b[2] * lrho[i]
        preds["aor_iso"][i] = isotonic_decreasing(aor[tr], y[tr])(aor[i])
        b = ols(lbo[tr], y[tr]); preds["bond_ols"][i] = b[0] + b[1] * lbo[i]
        preds["bev0"][i] = bev[i]
        preds["bev_scale"][i] = bev[i] + np.mean(y[tr] - bev[tr])
        if "dem0" in preds:
            preds["dem0"][i] = chain.predict(powders[i], key)[0]
            preds["dem0_bulk"][i] = chain.predict(powders[i], key, density="bulk")[0]
            # one fitted parameter: the AoR offset, by grid search on the training powders
            sse = [np.sum((np.array([chain.predict(powders[j], key, shift=s)[0] for j in tr]) - y[tr]) ** 2) for s in shifts]
            s_best = float(shifts[int(np.argmin(sse))])
            preds["dem_shift"][i] = chain.predict(powders[i], key, shift=s_best)[0]
            fitted["dem_shift"].append(s_best)
            # two: offset plus a log10 scale (the scale is the mean residual at that offset)
            best = None
            for s in shifts:
                yt = np.array([chain.predict(powders[j], key, shift=s)[0] for j in tr])
                c = float(np.mean(y[tr] - yt))
                e = float(np.sum((yt + c - y[tr]) ** 2))
                if best is None or e < best[0]:
                    best = (e, s, c)
            preds["dem_shift_scale"][i] = chain.predict(powders[i], key, shift=best[1], scale=best[2])[0]
            fitted["dem_shift_scale"].append([float(best[1]), round(best[2], 3)])
    return y, preds, fitted


def score(y, yhat):
    ok = np.isfinite(yhat)
    e = yhat[ok] - y[ok]
    flows = y[ok] >= math.log10(FLOW_THRESHOLD)
    pf = yhat[ok] >= math.log10(FLOW_THRESHOLD)
    rho, pval = stats.spearmanr(yhat[ok], y[ok]) if np.ptp(yhat[ok]) > 0 else (float("nan"), float("nan"))
    return {"n": int(ok.sum()), "rmse_log10": round(float(np.sqrt(np.mean(e ** 2))), 3),
            "mae_log10": round(float(np.mean(np.abs(e))), 3),
            "median_fold_error": round(float(10 ** np.median(np.abs(e))), 2),
            "spearman_rho": round(float(rho), 3), "spearman_p": round(float(pval), 4),
            "flow_class_correct": int(np.sum(flows == pf))}

# ------------------------------------------------------------------------------ inverse (AoR)


def inverse(powders, chain):
    """Predict each held-out powder's literature AoR from its measured mg/rev at 45 and 22.5 deg."""
    aor = np.array([p["aor"] for p in powders])
    y45 = np.array([logy(p["mg_rev"]["45"]) for p in powders])
    out = {"inv_ols": np.full(len(powders), np.nan), "inv_dem": np.full(len(powders), np.nan),
           "inv_dem_noshift": np.full(len(powders), np.nan)}
    ugrid = np.linspace(chain.aor_u[0], chain.aor_u[-1], 401)

    def u_hat(p):
        err = np.zeros_like(ugrid)
        for key in chain.doser:
            ym = logy(p["mg_rev"][key]) - math.log10(p["rho_p"] / RHO_SALT)
            err += np.array([(chain.logmg(u, key) - ym) ** 2 for u in ugrid])
        # flat stretches (fully flowing or fully stalled): take the middle of the minimising set
        m = np.isclose(err, err.min(), atol=1e-3)
        return float(np.median(ugrid[m]))

    uh = np.array([u_hat(p) for p in powders])
    a_dem = np.array([chain.aor_from_u(u) for u in uh])
    for i in range(len(powders)):
        tr = np.array([j for j in range(len(powders)) if j != i])
        b = ols(y45[tr], aor[tr]); out["inv_ols"][i] = b[0] + b[1] * y45[i]
        out["inv_dem"][i] = a_dem[i] + np.mean(aor[tr] - a_dem[tr])
        out["inv_dem_noshift"][i] = a_dem[i]
    res = {}
    for m, v in out.items():
        e = v - aor
        rho, pval = stats.spearmanr(v, aor)
        res[m] = {"rmse_deg": round(float(np.sqrt(np.mean(e ** 2))), 2), "mae_deg": round(float(np.mean(np.abs(e))), 2),
                  "spearman_rho": round(float(rho), 3), "spearman_p": round(float(pval), 4)}
    base = np.array([np.mean(np.delete(aor, i)) for i in range(len(aor))])
    res["mean"] = {"rmse_deg": round(float(np.sqrt(np.mean((base - aor) ** 2))), 2),
                   "mae_deg": round(float(np.mean(np.abs(base - aor))), 2)}
    return res, out, uh

# ----------------------------------------------------------------------- robustness and few-shot


def paired_test(y, a, b):
    """Wilcoxon signed-rank test on per-powder absolute LOPO errors of models a and b."""
    ea, eb = np.abs(a - y), np.abs(b - y)
    d = ea - eb
    if np.allclose(d, 0):
        return {"median_abs_err_diff_log10": 0.0, "wilcoxon_p": 1.0, "a_better": 0, "b_better": 0}
    res = stats.wilcoxon(ea, eb)
    return {"median_abs_err_diff_log10": round(float(np.median(d)), 3), "wilcoxon_p": round(float(res.pvalue), 3),
            "a_better": int(np.sum(d < 0)), "b_better": int(np.sum(d > 0))}


def aor_range_sensitivity(powders, key, chain, n_rep=200, seed=0):
    """Redraw every literature repose angle uniformly within its published range and redo the LOPO comparison
    of the AoR regression and the one-parameter DEM chain."""
    rng = np.random.default_rng(seed)
    out = {"aor_ols": [], "dem_shift": [], "aor_ols_class": [], "dem_shift_class": []}
    for _ in range(n_rep):
        pw = [{**p, "aor": float(rng.uniform(p["aor_lo"], p["aor_hi"]))} for p in powders]
        y, preds, _ = lopo(pw, key, chain, models=("aor_ols", "dem_shift"))
        for m in ("aor_ols", "dem_shift"):
            s = score(y, preds[m])
            out[m].append(s["rmse_log10"])
            out[m + "_class"].append(s["flow_class_correct"])
    res = {m: {"rmse_median": round(float(np.median(out[m])), 3),
               "rmse_p10_p90": [round(float(np.percentile(out[m], 10)), 3), round(float(np.percentile(out[m], 90)), 3)],
               "class_correct_median": float(np.median(out[m + "_class"]))} for m in ("aor_ols", "dem_shift")}
    res["dem_shift_rmse_lower_fraction"] = round(float(np.mean(np.array(out["dem_shift"]) < np.array(out["aor_ols"]))), 3)
    res["n_rep"] = n_rep
    return res


def few_shot_tilt(powders, chain):
    """Given a held-out powder's measured mg/rev at 22.5 deg, predict 45 deg.
    DEM: path position matching the (density-corrected) 22.5 deg value -> twin's 45 deg value.
    Baseline: the training powders' median log ratio 45/22.5."""
    if not ("45" in chain.doser and "22p5" in chain.doser):
        return None
    ugrid = np.linspace(chain.aor_u[0], chain.aor_u[-1], 801)
    y22 = np.array([logy(p["mg_rev"]["22p5"]) for p in powders])
    y45 = np.array([logy(p["mg_rev"]["45"]) for p in powders])
    pred_dem, pred_ratio = np.zeros(len(powders)), np.zeros(len(powders))
    for i, p in enumerate(powders):
        lr = math.log10(p["rho_p"] / RHO_SALT)
        err = np.array([(chain.logmg(u, "22p5") - (y22[i] - lr)) ** 2 for u in ugrid])
        m = np.isclose(err, err.min(), atol=1e-4)
        u = float(np.median(ugrid[m]))
        pred_dem[i] = chain.logmg(u, "45") + lr
        tr = [j for j in range(len(powders)) if j != i]
        pred_ratio[i] = y22[i] + float(np.median(y45[tr] - y22[tr]))
    return {"dem": score(y45, pred_dem), "median_ratio": score(y45, pred_ratio),
            "paired_dem_vs_ratio": paired_test(y45, pred_dem, pred_ratio),
            "per_powder": {p["powder_id"]: {"measured_45": p["mg_rev"]["45"], "dem": round(10 ** pd_, 2),
                                            "median_ratio": round(10 ** pr, 2)}
                           for p, pd_, pr in zip(powders, pred_dem, pred_ratio)}}

# --------------------------------------------------------------------------- correlation table


def correlations(powders, chain):
    """Spearman correlations of every feature with every response (raw, not cross-validated)."""
    feats = {
        "AoR (literature)": [p["aor"] for p in powders],
        "Hausner ratio (literature)": [p["hausner"] for p in powders],
        "bulk density (literature)": [p["rho_b"] for p in powders],
        "particle density (literature)": [p["rho_p"] for p in powders],
        "d50 (literature)": [p["d50_um"] for p in powders],
        "moisture (literature)": [p["moisture_pct"] for p in powders],
        "log Bond number, van der Waals (closed form)": [math.log10(bond_number(p["d50_um"], p["rho_p"])) for p in powders],
        "Beverloo, core-tip annulus, 45 deg (closed form)": [beverloo_annulus_mg_rev(p["d50_um"], p["rho_b"], 45.0) for p in powders],
    }
    if chain is not None and "45" in chain.doser:
        feats["DEM chain, 45 deg, no fit"] = [chain.predict(p, "45")[0] for p in powders]
    if chain is not None and "22p5" in chain.doser:
        feats["DEM chain, 22.5 deg, no fit"] = [chain.predict(p, "22p5")[0] for p in powders]
    resp = {
        "log mg/rev, 0 deg": [logy(p["mg_rev"]["0"]) for p in powders],
        "log mg/rev, 22.5 deg": [logy(p["mg_rev"]["22p5"]) for p in powders],
        "log mg/rev, 45 deg": [logy(p["mg_rev"]["45"]) for p in powders],
        "speed exponent (mg/s ~ rpm^a)": [p["speed_alpha"] for p in powders],
        "1 g dose time (s), powders that convey": [p["dose1g"]["mean_time_s"] if ("dose1g" in p and p["mg_rev"]["45"] >= FLOW_THRESHOLD / 10) else float("nan") for p in powders],
        "1 g doses within 5 %": [p["dose1g"]["pass_5pct"] / p["dose1g"]["n"] if "dose1g" in p else float("nan") for p in powders],
    }
    table = {}
    for f, x in feats.items():
        table[f] = {}
        for r, y in resp.items():
            x_, y_ = np.array(x, float), np.array(y, float)
            ok = np.isfinite(x_) & np.isfinite(y_)
            if ok.sum() < 5 or np.ptp(x_[ok]) == 0 or np.ptp(y_[ok]) == 0:
                table[f][r] = {"n": int(ok.sum()), "rho": None, "p": None}
                continue
            rho, pv = stats.spearmanr(x_[ok], y_[ok])
            table[f][r] = {"n": int(ok.sum()), "rho": round(float(rho), 2), "p": round(float(pv), 4)}
    n_tests = sum(1 for f in table for r in table[f] if table[f][r]["rho"] is not None)
    lines = ["# Spearman correlations: features vs. battery responses (12 powders with literature properties)", "",
             f"Raw correlations, not cross-validated. **Bold**: p < 0.05 uncorrected; † also below the Bonferroni "
             f"threshold 0.05/{n_tests} = {0.05 / n_tests:.4f} for the {n_tests} tests in this table.", "",
             "| feature | " + " | ".join(resp) + " |", "|---|" + "---|" * len(resp)]
    for f in table:
        cells = []
        for r in resp:
            c = table[f][r]
            if c["rho"] is None:
                cells.append("–")
                continue
            s = f"{c['rho']:+.2f} (n {c['n']}, p {c['p']:.3f})"
            if c["p"] < 0.05:
                s = f"**{s}**" + (" †" if c["p"] < 0.05 / n_tests else "")
            cells.append(s)
        lines.append(f"| {f} | " + " | ".join(cells) + " |")
    with open(os.path.join(HERE, "correlations.md"), "w") as fh:
        fh.write("\n".join(lines) + "\n")
    return table, n_tests

# ------------------------------------------------------------------------------- speed check


def speed_check(doser, powders):
    """Effective speed exponent a (mg/s ~ rpm^a) of the twin at 22.5 deg from 30 and 90 rpm, against protocol D."""
    rows = {}
    for r in doser:
        if r.get("tilt_deg") == 22.5 and dem_rate(r) is not None:
            rows[(r["path_point"], r.get("rpm", 30))] = dem_rate(r)
    out = {}
    for pt in ("P1", "k750", "k1500"):
        if (pt, 30) in rows and (pt, 90) in rows and rows[(pt, 30)] > 0 and rows[(pt, 90)] > 0:
            a = 1 + math.log(rows[(pt, 90)] / rows[(pt, 30)]) / math.log(3)
            out[pt] = {"mg_rev_30rpm": rows[(pt, 30)], "mg_rev_90rpm": rows[(pt, 90)], "speed_exponent": round(a, 3)}
    meas = {p["powder_id"]: p["speed_alpha"] for p in powders if np.isfinite(p["speed_alpha"])}
    flow = [v for k, v in meas.items() if next(p for p in powders if p["powder_id"] == k)["mg_rev"]["45"] >= FLOW_THRESHOLD]
    noflow = [v for k, v in meas.items() if next(p for p in powders if p["powder_id"] == k)["mg_rev"]["45"] < FLOW_THRESHOLD]
    out["measured_speed_exponent"] = {"conveying_powders_median": round(float(np.median(flow)), 3) if flow else None,
                                      "conveying_range": [round(min(flow), 3), round(max(flow), 3)] if flow else None,
                                      "poor_powders_median": round(float(np.median(noflow)), 3) if noflow else None,
                                      "poor_range": [round(min(noflow), 3), round(max(noflow), 3)] if noflow else None,
                                      "per_powder": meas}
    return out

# ----------------------------------------------------------------------------- markdown tables

MODEL_LABEL = {
    "mean": "training mean (no information)",
    "aor_ols": "log mg/rev linear in literature AoR (2 fitted)",
    "aor_rho_ols": "… plus log particle density (3 fitted)",
    "aor_iso": "monotone (isotonic) fit on AoR",
    "bond_ols": "linear in log Bond number from d50 (2 fitted)",
    "bev0": "Beverloo through the core-tip annulus, no fit",
    "bev_scale": "Beverloo, fitted log offset (1 fitted)",
    "dem0": "**DEM chain, no fitted parameter**",
    "dem0_bulk": "DEM chain, no fit, bulk-density scaling",
    "dem_shift": "**DEM chain, fitted AoR offset (1 fitted)**",
    "dem_shift_scale": "DEM chain, fitted offset and log scale (2 fitted)",
}


def write_tables(out, per_powder):
    L = []
    L.append("### Leave-one-powder-out scores (12 powders)\n")
    L.append("RMSE and median error are in log<sub>10</sub>(mg/rev) and as a factor; ρ is the Spearman rank correlation of "
             "the held-out predictions with the measurements; the last column counts powders put on the right side of "
             f"{FLOW_THRESHOLD:g} mg/rev at 45° (7 convey, 5 do not).\n")
    L.append("| model | 45°: RMSE | median error | ρ | flow class | 22.5°: RMSE | median error | ρ | flow class |")
    L.append("|---|---|---|---|---|---|---|---|---|")
    for m, lab in MODEL_LABEL.items():
        a, b = out["tilts"]["45"]["scores"].get(m), out["tilts"]["22p5"]["scores"].get(m)
        if a is None:
            continue
        cell = lambda s: (f"{s['rmse_log10']:.2f} | {s['median_fold_error']:.1f}× | {s['spearman_rho']:+.2f} | {s['flow_class_correct']}/{s['n']}"
                          if s else "– | – | – | –")
        L.append(f"| {lab} | {cell(a)} | {cell(b)} |")
    L.append("")
    fits = out["tilts"]["45"]["fitted"].get("dem_shift")
    if fits:
        f22 = out["tilts"]["22p5"]["fitted"].get("dem_shift") or []
        L.append(f"Fitted AoR offset Δ across the 12 folds: median {np.median(fits):g}° (range {min(fits):g}–{max(fits):g}°) at 45°"
                 + (f", median {np.median(f22):g}° (range {min(f22):g}–{max(f22):g}°) at 22.5°." if f22 else ".") + "\n")
    pt = out.get("paired_tests", {})
    if pt:
        L.append("Paired comparison of per-powder absolute errors (Wilcoxon signed-rank, 12 powders):\n")
        L.append("| tilt | comparison | powders where the first is better / worse | median difference (log<sub>10</sub>) | p |")
        L.append("|---|---|---|---|---|")
        for key, d in pt.items():
            for comp, v in d.items():
                L.append(f"| {'45°' if key == '45' else '22.5°'} | {comp.replace('_vs_', ' vs ')} | {v['a_better']} / {v['b_better']} | "
                         f"{v['median_abs_err_diff_log10']:+.2f} | {v['wilcoxon_p']:.2f} |")
        L.append("")
    sens = out.get("aor_range_sensitivity", {})
    if sens:
        L.append("Literature AoR redrawn uniformly within each published range (200 draws), LOPO repeated:\n")
        L.append("| tilt | model | median RMSE | 10–90 % | median flow class | DEM chain better in |")
        L.append("|---|---|---|---|---|---|")
        for key, d in sens.items():
            for m in ("aor_ols", "dem_shift"):
                L.append(f"| {'45°' if key == '45' else '22.5°'} | {m} | {d[m]['rmse_median']:.2f} | {d[m]['rmse_p10_p90'][0]:.2f}–{d[m]['rmse_p10_p90'][1]:.2f} | "
                         f"{d[m]['class_correct_median']:g}/12 | {'' if m == 'aor_ols' else f'{100 * d['dem_shift_rmse_lower_fraction']:.0f} % of draws'} |")
        L.append("")
    L.append("### Per powder at 45° (mg/rev; held-out predictions)\n")
    L.append("| powder | literature AoR (range) | measured | DEM chain, no fit | DEM chain, fitted offset | AoR regression | DEM no-fit over the AoR range |")
    L.append("|---|---|---|---|---|---|---|")
    rows = sorted(per_powder.items(), key=lambda kv: -kv[1]["measured"]["45"])
    for pid, r in rows:
        lp = r["lopo_log10_pred"]["45"]
        f = lambda v: "–" if v is None else (f"{10 ** v:.3g}")
        rng = r.get("dem0_mg_rev_range_over_aor_range", {}).get("45")
        L.append(f"| {r['display']} | {r['aor_lit']:g}° | {r['measured']['45']:.3g} | {f(lp.get('dem0'))} | {f(lp.get('dem_shift'))} | "
                 f"{f(lp.get('aor_ols'))} | {'' if not rng else f'{rng[0]:.3g}–{rng[1]:.3g}'} |")
    L.append("")
    inv = out.get("inverse_aor")
    if inv:
        L.append("### Inverse: each held-out powder's literature AoR from its measured mg/rev\n")
        L.append("| model | RMSE (deg) | MAE (deg) | ρ |")
        L.append("|---|---|---|---|")
        names = {"mean": "training mean", "inv_ols": "linear in log mg/rev at 45°", "inv_dem": "DEM path, both tilts, mean offset",
                 "inv_dem_noshift": "DEM path, no offset"}
        for m in ("mean", "inv_ols", "inv_dem", "inv_dem_noshift"):
            v = inv[m]
            rho_s = "–" if "spearman_rho" not in v else f"{v['spearman_rho']:+.2f}"
            L.append(f"| {names[m]} | {v['rmse_deg']:.1f} | {v['mae_deg']:.1f} | {rho_s} |")
        L.append("")
    fs = out.get("few_shot_45_from_22p5")
    if fs:
        L.append("### Few-shot: 45° from the same powder's measured 22.5° value\n")
        L.append("| model | RMSE | median error | ρ |")
        L.append("|---|---|---|---|")
        for m, lab in (("median_ratio", "training powders' median 45/22.5 ratio"), ("dem", "DEM path (22.5° → position → 45°)")):
            v = fs[m]
            L.append(f"| {lab} | {v['rmse_log10']:.2f} | {v['median_fold_error']:.2f}× | {v['spearman_rho']:+.2f} |")
        L.append("")
    sp = out.get("speed_check")
    if sp:
        L.append("### Speed: effective exponent a (mg/s ∝ rpm<sup>a</sup>) at 22.5°\n")
        L.append("| | 30 rpm (mg/rev) | 90 rpm (mg/rev) | a |")
        L.append("|---|---|---|---|")
        for k in ("P1", "k750", "k1500"):
            if k in sp:
                L.append(f"| DEM {k} | {sp[k]['mg_rev_30rpm']:.1f} | {sp[k]['mg_rev_90rpm']:.1f} | {sp[k]['speed_exponent']:.2f} |")
        m = sp["measured_speed_exponent"]
        L.append(f"| measured, the 7 powders that convey (protocol D, 15–90 rpm) | | | {m['conveying_powders_median']:.2f} (range {m['conveying_range'][0]:.2f}–{m['conveying_range'][1]:.2f}) |")
        L.append(f"| measured, the 4 poor powders with an exponent | | | {m['poor_powders_median']:.2f} (range {m['poor_range'][0]:.2f}–{m['poor_range'][1]:.2f}) |")
        L.append("")
    with open(os.path.join(HERE, "tables.md"), "w") as fh:
        fh.write("\n".join(L) + "\n")

# ------------------------------------------------------------------------------- result.json


def write_result_json(out, doser, aor):
    sc = {k: v["scores"] for k, v in out["tilts"].items()}
    pick = ("mean", "aor_ols", "aor_iso", "bev0", "bond_ols", "dem0", "dem_shift")
    walls = [r.get("wall_s") for r in doser if r.get("wall_s")] + [r.get("wall_s") for r in aor if r.get("wall_s")]
    complete = [r for r in doser if r.get("mg_per_rev_after_quarter") is not None]
    res = {
        "id": "heldout-powders",
        "method": "Leave-one-powder-out prediction of Sam's #116 battery (12 powders) from literature properties: "
                  "DEM repose-angle path + #180 auger twin along the same path (protocol C, 30 rpm) vs. "
                  "no-simulation baselines; correlations; inverse (AoR from the dosing fingerprint)",
        "code": "LIGGGHTS-PUBLIC + numpy/scipy",
        "version": "3.8.0 (Debian package liggghts)",
        "status": "ran" if len(complete) >= 6 else "partial",
        "wall_s": round(float(sum(walls)), 1) if walls else None,
        "cores": 4,
        "key_results": {
            "twin_salt_mg_rev": {r["case"]: r.get("mg_per_rev_after_quarter") for r in doser
                                 if r.get("path_point") == "P1" and r.get("rpm", 30) == 30},
            "lopo_45deg": {m: {k: sc["45"][m][k] for k in ("rmse_log10", "median_fold_error", "spearman_rho", "flow_class_correct")}
                           for m in pick if m in sc["45"]},
            "lopo_22p5deg": {m: {k: sc["22p5"][m][k] for k in ("rmse_log10", "median_fold_error", "spearman_rho", "flow_class_correct")}
                             for m in pick if m in sc["22p5"]},
            "spearman_aor_vs_log_mg_rev_45": out["spearman_raw"]["45"]["aor_lit"],
            "inverse_aor": out.get("inverse_aor"),
            "fitted_aor_offset_deg_45": out["tilts"]["45"]["fitted"].get("dem_shift"),
            "speed_check": {k: v for k, v in (out.get("speed_check") or {}).items() if k != "measured_speed_exponent"},
            "few_shot_45_from_22p5": out.get("few_shot_45_from_22p5"),
        },
    }
    with open(os.path.join(HERE, "result.json"), "w") as f:
        json.dump(res, f, indent=1)

# ------------------------------------------------------------------------------------- main


def main():
    powders = load_powders()
    doser = json.load(open(os.path.join(HERE, "doser_path.json"))) if os.path.exists(os.path.join(HERE, "doser_path.json")) else []
    aor = json.load(open(os.path.join(HERE, "aor_path.json"))) if os.path.exists(os.path.join(HERE, "aor_path.json")) else []
    aor = [r for r in aor if r.get("rc") == 0 and "angle_iso_deg" in r]
    chain = DemChain(doser, aor) if (doser and len(aor) >= 3) else None
    out = {"n_powders": len(powders), "floor_mg_rev": FLOOR, "flow_threshold_mg_rev_45": FLOW_THRESHOLD,
           "powders": [p["powder_id"] for p in powders], "tilts": {}, "spearman_raw": {}}
    pred_rows = {p["powder_id"]: {"display": p["display"], "aor_lit": p["aor"], "rho_p": p["rho_p"],
                                  "d50_um": p["d50_um"], "measured": p["mg_rev"]} for p in powders}
    for key in TILTS:
        y, preds, fitted = lopo(powders, key, chain)
        out["tilts"][key] = {"scores": {m: score(y, v) for m, v in preds.items()}, "fitted": fitted}
        for m, v in preds.items():
            for p, yy in zip(powders, v):
                pred_rows[p["powder_id"]].setdefault("lopo_log10_pred", {}).setdefault(key, {})[m] = None if not np.isfinite(yy) else round(float(yy), 3)
        # raw (not cross-validated) Spearman correlations of single features with the response
        feats = {"aor_lit": [p["aor"] for p in powders], "hausner_lit": [p["hausner"] for p in powders],
                 "log_bond_vdw": [math.log10(bond_number(p["d50_um"], p["rho_p"])) for p in powders],
                 "beverloo_annulus": [beverloo_annulus_mg_rev(p["d50_um"], p["rho_b"], TILTS[key]) for p in powders],
                 "rho_p": [p["rho_p"] for p in powders], "rho_b": [p["rho_b"] for p in powders],
                 "d50": [p["d50_um"] for p in powders], "moisture": [p["moisture_pct"] for p in powders]}
        if chain is not None and key in chain.doser:
            feats["dem0_prediction"] = [chain.predict(p, key)[0] for p in powders]
            for p in powders:
                pred_rows[p["powder_id"]].setdefault("dem_u", chain.u_from_aor(p["aor"]))
        out["spearman_raw"][key] = {}
        for f, v in feats.items():
            r, pv = stats.spearmanr(v, y)
            out["spearman_raw"][key][f] = {"rho": round(float(r), 3), "p": round(float(pv), 4)}
    out["correlations"], out["n_correlation_tests"] = correlations(powders, chain)
    if chain is not None:
        out["paired_tests"], out["aor_range_sensitivity"] = {}, {}
        for key in TILTS:
            if key not in chain.doser:
                continue
            y, preds, _ = lopo(powders, key, chain)
            out["paired_tests"][key] = {"dem_shift_vs_aor_ols": paired_test(y, preds["dem_shift"], preds["aor_ols"]),
                                        "dem_shift_vs_aor_iso": paired_test(y, preds["dem_shift"], preds["aor_iso"]),
                                        "dem0_vs_aor_ols": paired_test(y, preds["dem0"], preds["aor_ols"])}
            if "--quick" not in sys.argv:
                out["aor_range_sensitivity"][key] = aor_range_sensitivity(powders, key, chain)
        out["speed_check"] = speed_check(doser, powders)
        fs = few_shot_tilt(powders, chain)
        if fs is not None:
            out["few_shot_45_from_22p5"] = {k: v for k, v in fs.items() if k != "per_powder"}
            for pid, v in fs["per_powder"].items():
                pred_rows[pid]["few_shot_45_from_22p5"] = v
    if chain is not None:
        # literature AoR ranges pushed through the no-fit chain: how much the handbook spread moves each prediction
        for p in powders:
            rr = {}
            for key in chain.doser:
                ys = [chain.predict({**p, "aor": a}, key)[0] for a in (p["aor_lo"], p["aor"], p["aor_hi"]) if np.isfinite(a)]
                rr[key] = [round(10 ** min(ys), 2), round(10 ** max(ys), 2)]
            pred_rows[p["powder_id"]]["dem0_mg_rev_range_over_aor_range"] = rr
        inv_scores, inv_pred, uh = inverse(powders, chain)
        out["inverse_aor"] = inv_scores
        for p, a, b, u in zip(powders, inv_pred["inv_ols"], inv_pred["inv_dem"], uh):
            pred_rows[p["powder_id"]]["inverse"] = {"aor_ols": round(float(a), 2), "aor_dem": round(float(b), 2),
                                                    "u_from_fingerprint": round(float(u), 3)}
        out["dem_path"] = {"aor_u": chain.aor_u.tolist(), "aor_iso_deg": [round(a, 2) for a in chain.aor_deg],
                           "doser": {k: {"u": v[0].tolist(), "log10_mg_rev": [round(x, 3) for x in v[1]]}
                                     for k, v in chain.doser.items()}}
    with open(os.path.join(HERE, "predictions.json"), "w") as f:
        json.dump({"summary": out, "per_powder": pred_rows}, f, indent=1)
    write_result_json(out, doser, aor)
    write_tables(out, pred_rows)
    for key in TILTS:
        print(f"--- tilt {key}")
        for m, s in out["tilts"][key]["scores"].items():
            print(f"  {m:16s} rmse {s['rmse_log10']:.3f}  mae {s['mae_log10']:.3f}  fold {s['median_fold_error']:6.2f}  rho {s['spearman_rho']:+.2f}  class {s['flow_class_correct']}/{s['n']}")
    if "inverse_aor" in out:
        print("--- inverse (AoR from fingerprint)", out["inverse_aor"])
    return out, powders, chain


if __name__ == "__main__":
    main()
