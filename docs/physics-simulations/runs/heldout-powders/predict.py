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
        doser = [r for r in doser if r.get("tilt_deg") is not None and r.get("rpm", 30) == 30]
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


def lopo(powders, key, chain):
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
    for i in range(len(powders)):
        tr = np.array([j for j in range(len(powders)) if j != i])
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
    for key in TILTS:
        print(f"--- tilt {key}")
        for m, s in out["tilts"][key]["scores"].items():
            print(f"  {m:16s} rmse {s['rmse_log10']:.3f}  mae {s['mae_log10']:.3f}  fold {s['median_fold_error']:6.2f}  rho {s['spearman_rho']:+.2f}  class {s['flow_class_correct']}/{s['n']}")
    if "inverse_aor" in out:
        print("--- inverse (AoR from fingerprint)", out["inverse_aor"])
    return out, powders, chain


if __name__ == "__main__":
    main()
