#!/usr/bin/env python3
"""Run 33 (ml-property-dose): machine-learning models in both directions between powder properties and the
dosing fingerprint, trained on the 12 powders of Sam's #116 battery that have #163 handbook properties.

  inverse  dosing fingerprint -> property  (angle of repose, bulk/tapped/particle density, Hausner ratio, d50,
                                            moisture)
  forward  properties -> dosing outcome     (log10 mg/rev at 45, 22.5 and 0 deg, speed exponent, conveys or not)
  joint    one Gaussian latent-factor model of both blocks, conditioned on whichever block is known, so the
           inverse and forward predictions come from the same fitted model

Every score is leave-one-powder-out (LOPO): fit on 11 powders, predict the 12th, repeat for all 12. Feature
selection, imputation, scaling and hyperparameters are chosen inside each fold, so no score sees the held-out
powder. Nothing new is simulated; the DEM-chain predictions are read from run 32 (../heldout-powders).

Inputs
  ../heldout-powders/data/rate_summary.csv                Sam's per-powder battery summary (protocol C, D, E, B)
  ../heldout-powders/data/literature_powder_properties*.csv  #163 handbook values and their published ranges
  ../heldout-powders/predictions.json                     run 32's LOPO predictions (DEM chain)
  data/trials.csv, data/runs.csv                          Sam's per-revolution battery data (replicate noise)
Outputs
  result.json, tables.md, ml_inverse.png, ml_forward.png, ml_data_needs.png

usage: python ml_property_dose.py      (about 1-2 min on one core; numpy, scipy, scikit-learn, matplotlib)
"""
from __future__ import annotations

import csv
import json
import math
import time
import warnings
from pathlib import Path

import numpy as np
from scipy import stats

warnings.filterwarnings("ignore")

from sklearn.cross_decomposition import PLSRegression  # noqa: E402
from sklearn.decomposition import FactorAnalysis  # noqa: E402
from sklearn.ensemble import RandomForestRegressor  # noqa: E402
from sklearn.gaussian_process import GaussianProcessRegressor  # noqa: E402
from sklearn.gaussian_process.kernels import ConstantKernel, Matern, WhiteKernel  # noqa: E402
from sklearn.linear_model import LogisticRegression, RidgeCV  # noqa: E402
from sklearn.neighbors import KNeighborsRegressor  # noqa: E402

HERE = Path(__file__).resolve().parent
H32 = HERE.parent / "heldout-powders"
D32 = H32 / "data"
FLOOR = 0.1     # mg/rev (and mg/tap, mg/hold): about one salt grain and the balance step
FLOW = 50.0     # mg/rev at 45 deg: "conveys" vs "does not convey" (as in run 32)
SEED = 0

FP_FULL = ["lmg0", "lmg22", "lmg45", "alpha", "ltap22", "lhold45"]
FP_CORE = ["lmg0", "lmg22", "lmg45", "alpha"]
PROPS = ["aor", "bulk", "tapped", "hausner", "ld50", "rho_p", "lmoist"]
FWD_TARGETS = ["lmg45", "lmg22", "lmg0", "alpha"]

NAMES = {
    "lmg0": "log10 mg/rev, 0 deg", "lmg22": "log10 mg/rev, 22.5 deg", "lmg45": "log10 mg/rev, 45 deg",
    "alpha": "speed exponent", "ltap22": "log10 mg/tap, 22.5 deg", "lhold45": "log10 mg in 15 s hold, 45 deg",
    "aor": "angle of repose (deg)", "bulk": "bulk density (g/mL)", "tapped": "tapped density (g/mL)",
    "hausner": "Hausner ratio", "ld50": "log10 d50 (um)", "rho_p": "particle density (g/cm3)",
    "lmoist": "log10 moisture (wt%)",
}
LONG_PROP = {"aor": "angle_of_repose", "bulk": "bulk_density", "tapped": "tapped_density",
             "hausner": "hausner_ratio", "ld50": "d50", "rho_p": "true_density", "lmoist": "equilibrium_moisture"}
LOG_PROPS = {"ld50", "lmoist"}


# ----------------------------------------------------------------------------------------------------- data

def rcsv(path):
    with open(path, newline="") as f:
        return list(csv.DictReader(f))


def fnum(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return float("nan")


def lg(x):
    return math.log10(max(x, FLOOR)) if np.isfinite(x) else float("nan")


def load():
    rate = {r["powder_id"]: r for r in rcsv(D32 / "rate_summary.csv")}
    lit = {r["powder_id"]: r for r in rcsv(D32 / "literature_powder_properties.csv")}
    rng = {}
    for r in rcsv(D32 / "literature_powder_properties_long.csv"):
        rng[(r["powder_id"], r["property"])] = (fnum(r["range_low"]), fnum(r["range_high"]), r["specificity"])
    trials = rcsv(HERE / "data" / "trials.csv")
    ids = [pid for pid in rate if pid in lit]          # the 12 with handbook values (fumed silica has none)
    rows = []
    for pid in ids:
        R, L = rate[pid], lit[pid]
        row = {
            "powder_id": pid, "display": R["display"], "run_id": R["run_id"],
            "mg0": fnum(R["mg_rev_tilt0deg"]), "mg22": fnum(R["mg_rev_tilt22p5deg"]),
            "mg45": fnum(R["mg_rev_tilt45deg"]),
            "alpha": fnum(R["speed_exponent_alpha"]),
            "tap22": fnum(R["mg_per_tap_tilt22p5deg"]), "hold45": fnum(R["hold15s_tilt45deg_mg"]),
            "tap_resolvable": R["tap_resolvable"] == "True", "noise_floor_mg": fnum(R["noise_floor_mg"]),
            "aor": fnum(L["angle_repose_deg"]), "bulk": fnum(L["bulk_density_g_ml"]),
            "tapped": fnum(L["tapped_density_g_ml"]), "hausner": fnum(L["hausner_ratio"]),
            "d50": fnum(L["d50_um"]), "rho_p": fnum(L["true_density_g_cm3"]), "moist": fnum(L["moisture_pct"]),
        }
        row["lmg0"], row["lmg22"], row["lmg45"] = lg(row["mg0"]), lg(row["mg22"]), lg(row["mg45"])
        row["ltap22"], row["lhold45"] = lg(row["tap22"]), lg(row["hold45"])
        row["ld50"], row["lmoist"] = math.log10(row["d50"]), math.log10(row["moist"])
        row["conveys"] = int(row["mg45"] >= FLOW)
        row["hygroscopic"] = int(row["moist"] > 1.0)
        # handbook spread: SD of a value drawn uniformly inside the published range
        sd = {}
        for k, lp in LONG_PROP.items():
            lo, hi, _ = rng.get((pid, lp), (float("nan"),) * 3)
            if k in LOG_PROPS and lo > 0 and hi > 0:
                lo, hi = math.log10(lo), math.log10(hi)
            sd[k] = (hi - lo) / math.sqrt(12) if np.isfinite(lo) and np.isfinite(hi) and hi > lo else float("nan")
        row["label_sd"] = sd
        # replicate noise of the fingerprint: SE of log10 mg/rev at 45 deg from the six protocol C revolutions
        # (servo setting 90 = 45 deg tube tilt)
        revs = [fnum(t["delta_g"]) * 1000 for t in trials
                if t["run_id"] == R["run_id"] and t["block"] == "C" and fnum(t["tilt_deg"]) == 90.0]
        lrev = np.log10(np.maximum(np.array(revs), FLOOR)) if revs else np.array([])
        row["n_rev45"] = len(revs)
        row["se_lmg45"] = float(np.std(lrev, ddof=1) / math.sqrt(len(lrev))) if len(lrev) > 1 else float("nan")
        rows.append(row)
    dem = {}
    pj = H32 / "predictions.json"
    if pj.exists():
        P = json.loads(pj.read_text())["per_powder"]
        for pid, v in P.items():
            for tilt, key in (("45", "lmg45"), ("22p5", "lmg22")):
                for m in ("dem0", "dem_shift"):
                    dem.setdefault(m, {}).setdefault(key, {})[pid] = v["lopo_log10_pred"][tilt][m]
    return rows, dem


def matrix(rows, cols):
    return np.array([[r[c] for c in cols] for r in rows], dtype=float)


# --------------------------------------------------------------------------------------------- model zoo
# Every fit_predict(Xtr, ytr, Xte) returns (mean, sd, dof); sd is NaN when the model has no predictive
# distribution. Missing inputs are imputed with the training-fold median.

def impute(Xtr, Xte):
    med = np.nanmedian(Xtr, axis=0)
    med = np.where(np.isfinite(med), med, 0.0)
    A, B = Xtr.copy(), Xte.copy()
    for j in range(A.shape[1]):
        A[~np.isfinite(A[:, j]), j] = med[j]
        B[~np.isfinite(B[:, j]), j] = med[j]
    return A, B


def scale(Xtr, Xte):
    mu, sd = Xtr.mean(0), Xtr.std(0, ddof=0)
    sd = np.where(sd > 0, sd, 1.0)
    return (Xtr - mu) / sd, (Xte - mu) / sd


def m_mean(Xtr, ytr, Xte):
    n = len(ytr)
    return float(ytr.mean()), float(ytr.std(ddof=1) * math.sqrt(1 + 1 / n)), n - 1


def ols1(x, y, x0):
    """Simple linear regression with its t-based predictive SD."""
    n = len(y)
    xb, yb = x.mean(), y.mean()
    sxx = ((x - xb) ** 2).sum()
    b = ((x - xb) * (y - yb)).sum() / sxx
    a = yb - b * xb
    s = math.sqrt(((y - a - b * x) ** 2).sum() / (n - 2))
    return a + b * x0, s * math.sqrt(1 + 1 / n + (x0 - xb) ** 2 / sxx), n - 2


def loo_press_ols1(x, y):
    n = len(y)
    xb = x.mean()
    sxx = ((x - xb) ** 2).sum()
    if sxx <= 0:
        return float("inf")
    b = ((x - xb) * (y - y.mean())).sum() / sxx
    a = y.mean() - b * xb
    h = 1 / n + (x - xb) ** 2 / sxx
    return float((((y - a - b * x) / (1 - h)) ** 2).sum())


def make_line(j):
    def f(Xtr, ytr, Xte):
        A, B = impute(Xtr, Xte)
        m, s, d = ols1(A[:, j], ytr, B[0, j])
        return float(m), float(s), d
    return f


PICKS = {}


def make_best1(tag, cols):
    """Single feature chosen by inner leave-one-out PRESS on the training fold only."""
    def f(Xtr, ytr, Xte):
        A, B = impute(Xtr, Xte)
        press = [loo_press_ols1(A[:, j], ytr) for j in range(A.shape[1])]
        j = int(np.argmin(press))
        PICKS.setdefault(tag, []).append(cols[j])
        m, s, d = ols1(A[:, j], ytr, B[0, j])
        return float(m), float(s), d
    return f


def m_ridge(Xtr, ytr, Xte):
    A, B = scale(*impute(Xtr, Xte))
    r = RidgeCV(alphas=np.logspace(-3, 3, 25)).fit(A, ytr)
    return float(r.predict(B)[0]), float("nan"), 0


def m_pls1(Xtr, ytr, Xte):
    A, B = scale(*impute(Xtr, Xte))
    p = PLSRegression(n_components=1, scale=False).fit(A, ytr)
    return float(np.ravel(p.predict(B))[0]), float("nan"), 0


def m_gp(Xtr, ytr, Xte):
    A, B = scale(*impute(Xtr, Xte))
    d = A.shape[1]
    k = (ConstantKernel(1.0, (1e-2, 1e2)) * Matern(length_scale=np.ones(d), length_scale_bounds=(0.1, 100.0), nu=2.5)
         + WhiteKernel(0.1, (1e-4, 10.0)))
    g = GaussianProcessRegressor(kernel=k, normalize_y=True, n_restarts_optimizer=4, random_state=SEED).fit(A, ytr)
    m, s = g.predict(B, return_std=True)
    return float(m[0]), float(s[0]), 0


def m_rf(Xtr, ytr, Xte):
    A, B = impute(Xtr, Xte)
    r = RandomForestRegressor(n_estimators=300, min_samples_leaf=2, random_state=SEED).fit(A, ytr)
    return float(r.predict(B)[0]), float("nan"), 0


def m_knn(Xtr, ytr, Xte):
    A, B = scale(*impute(Xtr, Xte))
    r = KNeighborsRegressor(n_neighbors=2).fit(A, ytr)
    return float(r.predict(B)[0]), float("nan"), 0


def lopo(X, y, fp):
    n = len(y)
    mu, sd, dof = np.full(n, np.nan), np.full(n, np.nan), np.zeros(n)
    for i in range(n):
        if not np.isfinite(y[i]):
            continue
        tr = (np.arange(n) != i) & np.isfinite(y)
        mu[i], sd[i], dof[i] = fp(X[tr], y[tr], X[i:i + 1])
    return mu, sd, dof


# ---------------------------------------------------------------------------------- joint latent model

class Joint:
    """Gaussian factor model of [fingerprint, properties] in standardized units: Sigma = W W^T + Psi.

    Fitting needs complete rows, so missing entries are imputed with the training median before the fit;
    prediction conditions on whatever entries of the held-out powder are observed.
    """

    def __init__(self, Z, k):
        Zi, _ = impute(Z, Z[:1])
        self.mu, self.sd = Zi.mean(0), Zi.std(0, ddof=1)
        fa = FactorAnalysis(n_components=k, random_state=SEED, max_iter=5000).fit((Zi - self.mu) / self.sd)
        self.S = fa.get_covariance()
        self.W = fa.components_

    def predict(self, z, obs, tgt):
        obs = [j for j in obs if np.isfinite(z[j])]
        zo = (z[obs] - self.mu[obs]) / self.sd[obs]
        Soo, Sto, Stt = self.S[np.ix_(obs, obs)], self.S[np.ix_(tgt, obs)], self.S[np.ix_(tgt, tgt)]
        m = Sto @ np.linalg.solve(Soo, zo)
        C = Stt - Sto @ np.linalg.solve(Soo, Sto.T)
        return self.mu[tgt] + self.sd[tgt] * m, self.sd[tgt] * np.sqrt(np.clip(np.diag(C), 1e-12, None))


def lopo_joint(Z, obs, tgt, k):
    n = Z.shape[0]
    mu, sd = np.full((n, len(tgt)), np.nan), np.full((n, len(tgt)), np.nan)
    for i in range(n):
        J = Joint(Z[np.arange(n) != i], k)
        mu[i], sd[i] = J.predict(Z[i], obs, tgt)
    return mu, sd


# ------------------------------------------------------------------------------------------------ scores

def score(y, p, sd=None, dof=None):
    ok = np.isfinite(y) & np.isfinite(p)
    y, p = y[ok], p[ok]
    e = p - y
    out = {"n": int(ok.sum()), "rmse": float(np.sqrt(np.mean(e ** 2))),
           "q2": float(1 - np.sum(e ** 2) / np.sum((y - y.mean()) ** 2)),
           "spearman": float(stats.spearmanr(y, p)[0]) if np.ptp(p) > 0 else float("nan")}
    if sd is not None and np.all(np.isfinite(sd[ok])):
        s = sd[ok]
        if dof is not None and np.all(dof[ok] > 0):
            z = stats.t.ppf(0.95, dof[ok])
        else:
            z = np.full(len(s), stats.norm.ppf(0.95))
        out["cover90"] = int(np.sum(np.abs(e) <= z * s))
        out["width90_median"] = float(np.median(2 * z * s))
    return out


def ceiling(rows, key):
    """Best LOPO Q2 any model could reach if the handbook spread were the only error in the labels."""
    y = np.array([r[key] for r in rows])
    v = np.array([r["label_sd"][key] for r in rows])
    v = v[np.isfinite(v)]
    rms = float(np.sqrt(np.mean(v ** 2))) if len(v) else float("nan")
    return {"label_sd_rms": rms, "q2_max": float(1 - rms ** 2 / np.var(y, ddof=1)), "n_ranges": int(len(v))}


# ---------------------------------------------------------------------------------- analyses

def inverse(rows):
    X = matrix(rows, FP_FULL)
    models = {
        "mean": m_mean,
        "line45": make_line(FP_FULL.index("lmg45")),
        "best1": None,
        "ridge": m_ridge, "pls1": m_pls1, "gp": m_gp, "rf": m_rf, "knn2": m_knn,
    }
    out, preds = {}, {}
    for key in PROPS:
        y = np.array([r[key] for r in rows])
        res, pr = {"ceiling": ceiling(rows, key)}, {}
        for name, fp in models.items():
            if name == "best1":
                fp = make_best1(f"inv:{key}", FP_FULL)
            mu, sd, dof = lopo(X, y, fp)
            res[name] = score(y, mu, sd, dof)
            pr[name] = (mu, sd)
        Z = matrix(rows, FP_CORE + PROPS)
        obs = list(range(len(FP_CORE)))
        tgt = [len(FP_CORE) + PROPS.index(key)]
        for k in (1, 2):
            mu, sd = lopo_joint(Z, obs, tgt, k)
            res[f"joint{k}"] = score(y, mu[:, 0], sd[:, 0])
            pr[f"joint{k}"] = (mu[:, 0], sd[:, 0])
        mu, sd = lopo_joint(Z, [FP_CORE.index("lmg45")], tgt, 1)
        res["joint1_lmg45only"] = score(y, mu[:, 0], sd[:, 0])
        pr["joint1_lmg45only"] = (mu[:, 0], sd[:, 0])
        res["best1_picks"] = {c: PICKS.get(f"inv:{key}", []).count(c) for c in FP_FULL
                              if PICKS.get(f"inv:{key}", []).count(c)}
        out[key], preds[key] = res, pr
    return out, preds


def forward(rows, dem):
    X = matrix(rows, PROPS)
    models = {
        "mean": m_mean,
        "aor_line": make_line(PROPS.index("aor")),
        "best1": None,
        "ridge": m_ridge, "pls1": m_pls1, "gp": m_gp, "rf": m_rf, "knn2": m_knn,
    }
    out, preds = {}, {}
    for key in FWD_TARGETS:
        y = np.array([r[key] for r in rows])
        res, pr = {}, {}
        for name, fp in models.items():
            if name == "best1":
                fp = make_best1(f"fwd:{key}", PROPS)
            mu, sd, dof = lopo(X, y, fp)
            res[name] = score(y, mu, sd, dof)
            pr[name] = (mu, sd)
        Z = matrix(rows, FP_CORE + PROPS)
        obs = [len(FP_CORE) + j for j in range(len(PROPS))]
        tgt = [FP_CORE.index(key)]
        for k in (1, 2):
            mu, sd = lopo_joint(Z, obs, tgt, k)
            res[f"joint{k}"] = score(y, mu[:, 0], sd[:, 0])
            pr[f"joint{k}"] = (mu[:, 0], sd[:, 0])
        mu, sd = lopo_joint(Z, [len(FP_CORE) + PROPS.index("aor")], tgt, 1)
        res["joint1_aoronly"] = score(y, mu[:, 0], sd[:, 0])
        pr["joint1_aoronly"] = (mu[:, 0], sd[:, 0])
        for m in ("dem0", "dem_shift"):
            if key in dem.get(m, {}):
                p = np.array([dem[m][key].get(r["powder_id"], np.nan) for r in rows])
                res[m] = score(y, p)
                pr[m] = (p, np.full(len(p), np.nan))
        res["best1_picks"] = {c: PICKS.get(f"fwd:{key}", []).count(c) for c in PROPS
                              if PICKS.get(f"fwd:{key}", []).count(c)}
        out[key], preds[key] = res, pr
    return out, preds


def classify(rows):
    """Flow/no-flow from properties (forward) and hygroscopic class from the fingerprint (inverse)."""
    def lopo_logit(X, y, C=1.0):
        n = len(y)
        p = np.full(n, np.nan)
        for i in range(n):
            tr = np.arange(n) != i
            A, B = scale(*impute(X[tr], X[i:i + 1]))
            if len(set(y[tr])) < 2:
                p[i] = y[tr].mean()
                continue
            p[i] = LogisticRegression(C=C, max_iter=2000).fit(A, y[tr]).predict_proba(B)[0, 1]
        return p

    out = {}
    cases = {
        "conveys | AoR": (matrix(rows, ["aor"]), "conveys"),
        "conveys | all 7 properties": (matrix(rows, PROPS), "conveys"),
        "conveys | particle density + log d50": (matrix(rows, ["rho_p", "ld50"]), "conveys"),
        "hygroscopic | log10 mg/rev 45 deg": (matrix(rows, ["lmg45"]), "hygroscopic"),
        "hygroscopic | full fingerprint": (matrix(rows, FP_FULL), "hygroscopic"),
    }
    for name, (X, key) in cases.items():
        y = np.array([r[key] for r in rows])
        p = lopo_logit(X, y)
        base = np.array([np.mean(np.delete(y, i)) for i in range(len(y))])
        out[name] = {"n": len(y), "n_positive": int(y.sum()), "correct": int(np.sum((p >= 0.5) == (y == 1))),
                     "brier": float(np.mean((p - y) ** 2)), "brier_base_rate": float(np.mean((base - y) ** 2)),
                     "wrong": [r["display"] for r, pi, yi in zip(rows, p, y) if (pi >= 0.5) != (yi == 1)]}
    return out


def extras(rows):
    """Three checks for the write-up: a two-part (flow / no flow, then rate) model; what explains the rate among
    the powders that convey; and few-shot prediction of the fingerprint from one quick dosing measurement."""
    out = {}
    aor = np.array([r["aor"] for r in rows])
    conv = np.array([r["conveys"] for r in rows])
    n = len(rows)
    # (1) two-part model on AoR: P(conveys) from a logistic fit, then each class's training mean of log mg/rev
    for key in ("lmg45", "lmg22", "lmg0"):
        y = np.array([r[key] for r in rows])
        pred = np.full(n, np.nan)
        for i in range(n):
            tr = np.arange(n) != i
            A, B = scale(aor[tr, None], aor[i:i + 1, None])
            p = LogisticRegression(C=1.0, max_iter=2000).fit(A, conv[tr]).predict_proba(B)[0, 1]
            pred[i] = p * y[tr & (conv == 1)].mean() + (1 - p) * y[tr & (conv == 0)].mean()
        out[f"two_part_{key}"] = score(y, pred)
    # (2) among the 7 powders that convey: does any single handbook property explain log mg/rev at 45 deg?
    idx = np.flatnonzero(conv == 1)
    y = np.array([rows[i]["lmg45"] for i in idx])
    within = {"mean": score(y, lopo(np.zeros((len(idx), 1)), y, m_mean)[0])}
    for k in PROPS:
        x = np.array([[rows[i][k]] for i in idx])
        within[f"line on {k}"] = score(y, lopo(x, y, make_line(0))[0])
    # constant solid volume per revolution: log10 mg = log10 V + log10 rho_p, one fitted constant
    lr = np.log10([rows[i]["rho_p"] for i in idx])
    pv = np.array([np.mean(np.delete(y - lr, j)) + lr[j] for j in range(len(idx))])
    within["constant volume x particle density"] = score(y, pv)
    within["_powders"] = [rows[i]["display"] for i in idx]
    within["_spread_decades_sd"] = float(np.std(y, ddof=1))
    out["within_conveyors_lmg45"] = within
    # (3) few-shot: one quick dosing measurement on the new powder -> the rest of its fingerprint
    few = {}
    X = matrix(rows, FP_FULL)
    for tgt, src in (("lmg45", "lmg22"), ("lmg0", "lmg22"), ("alpha", "lmg22"), ("lmg45", "lmg0")):
        y = np.array([r[tgt] for r in rows])
        mu, sd, dof = lopo(X, y, make_line(FP_FULL.index(src)))
        few[f"{tgt} from {src}"] = score(y, mu, sd, dof)
    out["few_shot"] = few
    return out


def learning_curves(rows, reps=400):
    rng = np.random.default_rng(SEED)
    n = len(rows)
    sizes = list(range(4, n))
    cases = {
        "inverse AoR: line on log mg/rev 45 deg": (matrix(rows, FP_FULL), np.array([r["aor"] for r in rows]),
                                                  make_line(FP_FULL.index("lmg45"))),
        "inverse AoR: ridge on the full fingerprint": (matrix(rows, FP_FULL), np.array([r["aor"] for r in rows]),
                                                       m_ridge),
        "forward log mg/rev 45 deg: line on AoR": (matrix(rows, PROPS), np.array([r["lmg45"] for r in rows]),
                                                  make_line(PROPS.index("aor"))),
        "forward log mg/rev 45 deg: ridge on all 7 properties": (matrix(rows, PROPS),
                                                                 np.array([r["lmg45"] for r in rows]), m_ridge),
    }
    out = {}
    for name, (X, y, fp) in cases.items():
        curve = []
        for m in sizes:
            per_split, allsq = [], []
            for _ in range(reps):
                tr = rng.choice(n, m, replace=False)
                te = np.setdiff1d(np.arange(n), tr)
                sq = []
                for i in te:
                    mu, _, _ = fp(X[tr], y[tr], X[i:i + 1])
                    sq.append((mu - y[i]) ** 2)
                per_split.append(math.sqrt(np.mean(sq)))
                allsq += sq
            curve.append({"n_train": m, "rmse": float(math.sqrt(np.mean(allsq))),
                          "rmse_median": float(np.median(per_split)),
                          "rmse_p10": float(np.percentile(per_split, 10)),
                          "rmse_p90": float(np.percentile(per_split, 90))})
        out[name] = curve
    return out


def inflation_table(reps=4000):
    """Out-of-sample MSE of least squares with p inputs fitted on n powders, relative to the noise variance.

    Closed form for Gaussian inputs (with intercept): (1 + 1/n)(n - 2)/(n - p - 2); checked here by Monte Carlo.
    """
    rng = np.random.default_rng(SEED + 1)
    rows = []
    for n in (12, 20, 30, 50):
        for p in (1, 2, 4, 6):
            exact = (1 + 1 / n) * (n - 2) / (n - p - 2) if n - p - 2 > 0 else float("inf")
            mc = []
            for _ in range(reps if n <= 30 else reps // 2):
                X = rng.standard_normal((n + 1, p))
                y = X @ np.ones(p) * 0.5 + rng.standard_normal(n + 1)
                A = np.column_stack([np.ones(n), X[:n]])
                b, *_ = np.linalg.lstsq(A, y[:n], rcond=None)
                mc.append((np.r_[1.0, X[n]] @ b - y[n]) ** 2)
            rows.append({"n": n, "p": p, "inflation_exact": exact, "inflation_mc": float(np.mean(mc))})
    return rows


# ---------------------------------------------------------------------------------------------- figures

INK, INK2, MUTED, GRID, SURF = "#0b0b0b", "#52514e", "#8a8984", "#e4e3df", "#fcfcfb"
S1, S2, S3 = "#2a78d6", "#eb6834", "#1baf7a"            # categorical slots 1-3 (all-pairs safe)
RAMP = ["#86b6ef", "#3987e5", "#1c5cab", "#0d366b"]     # ordinal blue ramp (steps 250, 400, 550, 700)


def style(ax):
    ax.set_facecolor(SURF)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color(MUTED)
    ax.tick_params(colors=INK2, labelsize=8)
    ax.grid(True, color=GRID, lw=0.6)
    ax.set_axisbelow(True)


def short(name):
    return {"NaCl (control)": "salt", "Si (110/200 mesh)": "Si 75-150", "Si (-325 mesh)": "Si <44",
            "Sodium sulfate": "Na2SO4", "Calcium lactate": "Ca lactate", "Barium chloride": "BaCl2",
            "Xanthan gum": "xanthan", "White rice flour": "white rice", "Brown rice flour": "brown rice",
            "Sodium alginate": "alginate"}.get(name, name)


LABEL_OFFSETS = {  # (dx, dy) in points, to keep the crowded free-flowing cluster readable
    "AlSi10Mg": (5, -10), "Si (110/200 mesh)": (5, -12), "NaCl (control)": (-30, 6), "Sodium sulfate": (-44, -12),
    "Calcium lactate": (5, -10), "Barium chloride": (5, 4), "Xanthan gum": (5, 6), "White rice flour": (5, -10),
    "Sodium alginate": (5, -10), "Carboxymethyl cellulose": (-30, 6), "Brown rice flour": (-58, -4),
    "Si (-325 mesh)": (5, -10), "CMC": (-30, 6),
}


def fig_inverse(rows, inv, ipred, path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, axs = plt.subplots(1, 2, figsize=(12.5, 5.2), gridspec_kw={"width_ratios": [1.0, 1.0]}, facecolor=SURF)
    # (a) LOPO skill per property: three models and the ceiling set by the handbook spread
    ax = axs[0]
    style(ax)
    keys = PROPS[::-1]
    ys = np.arange(len(keys))
    for yi, k in zip(ys, keys):
        c = inv[k]["ceiling"]["q2_max"]
        ax.plot([c], [yi], marker="|", ms=18, mew=2.2, color=MUTED, zorder=2)
    series = [("line45", "line on log10 mg/rev at 45° (chosen in advance)", S1, "o"),
              ("ridge", "ridge on all 6 dosing features", S2, "s"),
              ("joint1", "joint 1-factor model (4 dosing features)", S3, "D")]
    for j, (m, lab, col, mk) in enumerate(series):
        q = [max(inv[k][m]["q2"], -1.0) for k in keys]
        ax.scatter(q, ys + (1 - j) * 0.2, s=48, color=col, marker=mk, edgecolor=SURF, lw=1.2, zorder=3, label=lab)
    ax.plot([], [], marker="|", ms=12, mew=2.2, color=MUTED, ls="", label="ceiling if the handbook spread were the only error")
    ax.axvline(0, color=INK2, lw=0.8)
    ax.set_yticks(ys)
    ax.set_yticklabels([NAMES[k] for k in keys], fontsize=8.5, color=INK)
    ax.set_xlim(-1.05, 1.02)
    ax.set_ylim(-0.6, len(keys) + 1.4)
    ax.set_xlabel("leave-one-powder-out skill Q² (1 perfect, 0 = predicting the mean; clipped at -1)", fontsize=8.5,
                  color=INK2)
    ax.legend(fontsize=7.5, loc="upper left", frameon=False, labelcolor=INK2, ncol=1)
    ax.set_title("(a) Inverse: which properties the dosing data predict", fontsize=10, color=INK, loc="left")
    # (b) AoR: held-out prediction against the handbook value, with the handbook range and the 90 % interval
    ax = axs[1]
    style(ax)
    y = np.array([r["aor"] for r in rows])
    half = np.array([r["label_sd"]["aor"] for r in rows]) * math.sqrt(3)
    for j, (m, lab, col, mk) in enumerate([("line45", "line on log10 mg/rev at 45°", S1, "o"),
                                           ("joint1", "joint 1-factor model", S3, "D")]):
        mu, sd = ipred["aor"][m]
        off = (j - 0.5) * 0.4
        if j == 0:
            ax.errorbar(y, mu, xerr=half, fmt="none", ecolor=MUTED, elinewidth=1.0, alpha=0.7, zorder=1)
        ax.errorbar(y + off, mu, yerr=1.645 * sd, fmt="none", ecolor=col, elinewidth=1.1, alpha=0.55, zorder=2)
        ax.scatter(y + off, mu, s=50, color=col, marker=mk, edgecolor=SURF, lw=1.2, zorder=3,
                   label=f"{lab}: RMSE {inv['aor'][m]['rmse']:.1f}°, 90 % interval holds {inv['aor'][m].get('cover90', '-')}/12")
    ax.plot([], [], color=MUTED, lw=1.0, label="published handbook range (horizontal)")
    ax.plot([22, 56], [22, 56], color=INK2, lw=0.8, ls="--", zorder=1)
    for r, yi, mi in zip(rows, y, ipred["aor"]["line45"][0]):
        dx, dy = LABEL_OFFSETS.get(r["display"], (5, -10))
        ax.annotate(short(r["display"]), (yi, mi), xytext=(dx, dy), textcoords="offset points", fontsize=6.8,
                    color=INK2)
    ax.set_xlim(23, 56)
    ax.set_ylim(25, 56)
    ax.set_xlabel("handbook angle of repose (°)", fontsize=9, color=INK2)
    ax.set_ylabel("held-out prediction from the dosing data (°)", fontsize=9, color=INK2)
    ax.legend(fontsize=7.5, loc="upper left", frameon=False, labelcolor=INK2)
    ax.set_title("(b) Angle of repose from the doser, each powder held out", fontsize=10, color=INK, loc="left")
    fig.tight_layout()
    fig.savefig(path, dpi=150, facecolor=SURF)
    plt.close(fig)


def fig_forward(rows, fwd, fpred, cls, path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, axs = plt.subplots(1, 2, figsize=(12.5, 5.2), facecolor=SURF)
    ax = axs[0]
    style(ax)
    y = np.array([r["lmg45"] for r in rows])
    for j, (m, lab, col, mk) in enumerate([("aor_line", "line on handbook AoR", S1, "o"),
                                           ("ridge", "ridge on all 7 handbook properties", S2, "s"),
                                           ("dem_shift", "DEM chain + fitted AoR offset (run 32)", S3, "D")]):
        mu, sd = fpred["lmg45"][m]
        off = (j - 1) * 0.05
        if np.all(np.isfinite(sd)):
            ax.errorbar(y + off, mu, yerr=1.645 * sd, fmt="none", ecolor=col, elinewidth=1.0, alpha=0.45, zorder=2)
        ax.scatter(y + off, mu, s=50, color=col, marker=mk, edgecolor=SURF, lw=1.2, zorder=3,
                   label=f"{lab}: RMSE {fwd['lmg45'][m]['rmse']:.2f} decades")
    t = math.log10(FLOW)
    ax.axvline(t, color=MUTED, lw=0.8, ls=":")
    ax.axhline(t, color=MUTED, lw=0.8, ls=":")
    ax.plot([-1.2, 3.4], [-1.2, 3.4], color=INK2, lw=0.8, ls="--", zorder=1)
    for r, yi, mi in zip(rows, y, fpred["lmg45"]["aor_line"][0]):
        dx, dy = LABEL_OFFSETS.get(r["display"], (5, -10))
        if r["display"] in ("NaCl (control)", "Sodium sulfate", "Barium chloride", "Si (110/200 mesh)"):
            continue        # the free-flowing cluster is named in the table instead
        ax.annotate(short(r["display"]), (yi, mi), xytext=(dx, dy), textcoords="offset points", fontsize=6.8,
                    color=INK2)
    ax.text(t + 0.04, -1.1, "50 mg/rev", fontsize=7, color=INK2)
    ax.set_xlim(-1.2, 3.2)
    ax.set_ylim(-1.2, 4.0)
    ax.set_xlabel("measured log10 mg/rev at 45° (protocol C)", fontsize=9, color=INK2)
    ax.set_ylabel("held-out prediction from properties", fontsize=9, color=INK2)
    ax.legend(fontsize=7.5, loc="upper left", frameon=False, labelcolor=INK2)
    ax.set_title("(a) Forward: dosing rate from handbook properties", fontsize=10, color=INK, loc="left")
    # (b) skill per dosing target
    ax = axs[1]
    style(ax)
    keys = FWD_TARGETS[::-1]
    ys = np.arange(len(keys))
    series = [("aor_line", "line on handbook AoR", S1, "o"), ("ridge", "ridge on all 7 properties", S2, "s"),
              ("joint1", "joint 1-factor model, given all 7 properties", S3, "D")]
    for j, (m, lab, col, mk) in enumerate(series):
        q = [max(fwd[k][m]["q2"], -1.0) for k in keys]
        ax.scatter(q, ys + (1 - j) * 0.2, s=48, color=col, marker=mk, edgecolor=SURF, lw=1.2, zorder=3, label=lab)
    ax.axvline(0, color=INK2, lw=0.8)
    ax.set_yticks(ys)
    ax.set_yticklabels([NAMES[k] for k in keys], fontsize=8.5, color=INK)
    ax.set_xlim(-1.05, 1.02)
    ax.set_ylim(-0.95, len(keys) + 0.9)
    ax.set_xlabel("leave-one-powder-out skill Q² (clipped at -1)", fontsize=8.5, color=INK2)
    c = cls["conveys | AoR"]
    ax.text(-1.0, -0.75, f"Flow / no flow at 45° from handbook AoR alone (logistic): {c['correct']}/{c['n']} right",
            fontsize=7.5, color=INK2)
    ax.legend(fontsize=7.5, loc="upper left", frameon=False, labelcolor=INK2)
    ax.set_title("(b) Which dosing outcomes the handbook properties predict", fontsize=10, color=INK, loc="left")
    fig.tight_layout()
    fig.savefig(path, dpi=150, facecolor=SURF)
    plt.close(fig)


def fig_data_needs(lc, infl, path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, axs = plt.subplots(1, 3, figsize=(14, 4.4), facecolor=SURF)
    pairs = [("inverse AoR: line on log mg/rev 45 deg", "inverse AoR: ridge on the full fingerprint",
              "(a) Inverse: angle of repose", "RMSE on held-out powders (°)"),
             ("forward log mg/rev 45 deg: line on AoR", "forward log mg/rev 45 deg: ridge on all 7 properties",
              "(b) Forward: log10 mg/rev at 45°", "RMSE on held-out powders (decades)")]
    for ax, (a, b, title, ylab) in zip(axs[:2], pairs):
        style(ax)
        for name, col, mk, lab in ((a, S1, "o", "one input"), (b, S2, "s", "all inputs, ridge")):
            c = lc[name]
            x = [p["n_train"] for p in c]
            ax.fill_between(x, [p["rmse_p10"] for p in c], [p["rmse_p90"] for p in c], color=col, alpha=0.12, lw=0)
            ax.plot(x, [p["rmse_median"] for p in c], color=col, lw=2, marker=mk, ms=6, mec=SURF, label=lab)
        ax.set_xlabel("powders in the training set", fontsize=9, color=INK2)
        ax.set_ylabel(ylab, fontsize=9, color=INK2)
        ax.set_title(title, fontsize=10, color=INK, loc="left")
        ax.legend(fontsize=7.5, frameon=False, labelcolor=INK2,
                  title="median over 400 random splits; band 10-90 %", title_fontsize=7)
    ax = axs[2]
    style(ax)
    ns = np.arange(8, 61)
    for p, col in zip((1, 2, 4, 6), RAMP):
        f = np.where(ns - p - 2 > 0, (1 + 1 / ns) * (ns - 2) / np.maximum(ns - p - 2, 1e-9), np.nan)
        f = np.where(f > 4, np.nan, f)
        ax.plot(ns, f, color=col, lw=2, label=f"{p} input{'s' if p > 1 else ''}")
        mc = [r for r in infl if r["p"] == p]
        ax.scatter([r["n"] for r in mc if r["inflation_mc"] < 4], [r["inflation_mc"] for r in mc if r["inflation_mc"] < 4],
                   s=26, color=col, edgecolor=SURF, zorder=3)
    ax.axvline(12, color=MUTED, lw=0.8, ls=":")
    ax.text(12.5, 3.75, "today: 12 powders", fontsize=7.5, color=INK2)
    ax.set_ylim(1, 4)
    ax.set_xlabel("powders with both measurements", fontsize=9, color=INK2)
    ax.set_ylabel("held-out error / noise (variance ratio)", fontsize=9, color=INK2)
    ax.set_title("(c) Cost of each extra input (least squares)", fontsize=10, color=INK, loc="left")
    ax.legend(fontsize=7.5, frameon=False, labelcolor=INK2, title="dots: Monte Carlo", title_fontsize=7)
    fig.tight_layout()
    fig.savefig(path, dpi=150, facecolor=SURF)
    plt.close(fig)


# ------------------------------------------------------------------------------------------------ report

MODEL_LABELS = {
    "mean": "training mean", "line45": "line on log10 mg/rev 45°", "aor_line": "line on AoR",
    "best1": "best single input (nested)", "ridge": "ridge, all inputs", "pls1": "PLS, 1 component",
    "gp": "GP (ARD Matérn), all inputs", "rf": "random forest", "knn2": "2 nearest powders",
    "joint1": "joint model, 1 factor", "joint2": "joint model, 2 factors",
    "joint1_lmg45only": "joint 1-factor, given mg/rev 45° only", "joint1_aoronly": "joint 1-factor, given AoR only",
    "dem0": "DEM chain, no fit (run 32)", "dem_shift": "DEM chain + AoR offset (run 32)",
}


def fmt_cell(s):
    return f"{s['q2']:+.2f} ({s['rmse']:.2g})"


def tables(rows, inv, fwd, cls, lc, infl, loadings, ex):
    L = []
    L.append("# Run 33 tables (generated by `ml_property_dose.py`)\n")
    L.append("Cells are **leave-one-powder-out Q² (RMSE)**. Q² = 1 − Σ(error²)/Σ(y − ȳ)²: 1 is perfect, 0 is no "
             "better than predicting the mean, negative is worse. RMSE is in the target's units. n = 12 powders "
             "(11 for the speed exponent).\n")
    L.append("## Inverse: dosing fingerprint → handbook property\n")
    L.append("Inputs: log10 mg/rev at 0, 22.5 and 45°, speed exponent, log10 mg per tap at 22.5° and log10 mg in "
             "the 15 s hold at 45° (6 features). *Ceiling*: the Q² a perfect model would score if the only error "
             "were the handbook spread (each value uniform within its published range).\n")
    cols = ["mean", "line45", "best1", "ridge", "pls1", "gp", "rf", "knn2", "joint1", "joint2"]
    L.append("| property | ceiling Q² (label SD) | " + " | ".join(MODEL_LABELS[c] for c in cols) + " | best single input picked |")
    L.append("|---" * (len(cols) + 3) + "|")
    for k in PROPS:
        c = inv[k]["ceiling"]
        picks = ", ".join(f"{NAMES[f]} ×{n}" for f, n in sorted(inv[k]["best1_picks"].items(), key=lambda t: -t[1]))
        L.append(f"| {NAMES[k]} | {c['q2_max']:+.2f} ({c['label_sd_rms']:.2g}) | "
                 + " | ".join(fmt_cell(inv[k][m]) for m in cols) + f" | {picks} |")
    L.append("")
    L.append("## Forward: handbook properties → dosing outcome\n")
    L.append("Inputs: angle of repose, bulk and tapped density, Hausner ratio, log10 d50, particle density and log10 "
             "moisture (7 features). The two DEM rows are run 32's leave-one-out predictions.\n")
    cols = ["mean", "aor_line", "best1", "ridge", "pls1", "gp", "rf", "knn2", "joint1", "joint2", "joint1_aoronly",
            "dem0", "dem_shift"]
    L.append("| dosing outcome | " + " | ".join(MODEL_LABELS[c] for c in cols) + " | best single input picked |")
    L.append("|---" * (len(cols) + 2) + "|")
    for k in FWD_TARGETS:
        picks = ", ".join(f"{NAMES[f]} ×{n}" for f, n in sorted(fwd[k]["best1_picks"].items(), key=lambda t: -t[1]))
        L.append(f"| {NAMES[k]} | " + " | ".join(fmt_cell(fwd[k][m]) if m in fwd[k] else "–" for m in cols)
                 + f" | {picks} |")
    L.append("")
    L.append("## Classification (logistic regression, leave one powder out)\n")
    L.append("| task | right | Brier score | Brier, base rate | misclassified |")
    L.append("|---|---|---|---|---|")
    for name, c in cls.items():
        L.append(f"| {name} | {c['correct']}/{c['n']} | {c['brier']:.3f} | {c['brier_base_rate']:.3f} | "
                 f"{', '.join(c['wrong']) or '–'} |")
    L.append("")
    L.append("## Two-part model, the powders that convey, and few-shot prediction\n")
    L.append("**Two-part model** (logistic P(conveys | AoR), then each class's training mean of log10 mg/rev):\n")
    L.append("| target | Q² (RMSE) |")
    L.append("|---|---|")
    for key in ("lmg45", "lmg22", "lmg0"):
        L.append(f"| {NAMES[key]} | {fmt_cell(ex['two_part_' + key])} |")
    w = ex["within_conveyors_lmg45"]
    L.append(f"\n**Among the {len(w['_powders'])} powders that convey** ({', '.join(w['_powders'])}; SD of log10 mg/rev "
             f"at 45° = {w['_spread_decades_sd']:.2f} decades), one handbook input at a time, leave one out:\n")
    L.append("| model | Q² (RMSE) |")
    L.append("|---|---|")
    for k, v in w.items():
        if not k.startswith("_"):
            label = f"line on {NAMES[k[8:]]}" if k.startswith("line on ") else k
            L.append(f"| {label} | {fmt_cell(v)} |")
    L.append("\n**Few-shot**: one quick dosing measurement on the held-out powder predicts the rest of its fingerprint "
             "(line fitted on the other 11):\n")
    L.append("| prediction | Q² (RMSE) | 90 % intervals covering |")
    L.append("|---|---|---|")
    for k, v in ex["few_shot"].items():
        a, b = k.split(" from ")
        L.append(f"| {NAMES[a]} from {NAMES[b]} | {fmt_cell(v)} | {v.get('cover90', '-')}/{v['n']} |")
    L.append("")
    L.append("## Are the uncertainties honest? 90 % prediction intervals, leave one powder out\n")
    L.append("| direction | target | model | intervals that contain the held-out value | median width |")
    L.append("|---|---|---|---|---|")
    for direction, res, keys, ms in (("inverse", inv, ["aor", "rho_p", "lmoist"], ["line45", "gp", "joint1"]),
                                     ("forward", fwd, ["lmg45", "lmg22", "alpha"], ["aor_line", "gp", "joint1"])):
        for k in keys:
            for m in ms:
                s = res[k][m]
                if "cover90" in s:
                    L.append(f"| {direction} | {NAMES[k]} | {MODEL_LABELS[m]} | {s['cover90']}/{s['n']} | "
                             f"{s['width90_median']:.2g} |")
    L.append("")
    L.append("## Learning curves (random training subsets, 400 per size, scored on the powders left out)\n")
    L.append("Median RMSE over the splits, with the pooled RMSE (all held-out errors together) in brackets; the "
             "pooled value is dominated by the few splits where a model extrapolates badly.\n")
    L.append("| model | " + " | ".join(f"{m} powders" for m in (4, 6, 8, 10, 11)) + " |")
    L.append("|---" * 6 + "|")
    for name, c in lc.items():
        d = {p["n_train"]: p for p in c}
        L.append(f"| {name} | " + " | ".join(f"{d[m]['rmse_median']:.2f} ({d[m]['rmse']:.2f})"
                                               for m in (4, 6, 8, 10, 11)) + " |")
    L.append("")
    L.append("## Error inflation from fitting p inputs on n powders (least squares, Gaussian inputs)\n")
    L.append("Held-out mean squared error divided by the noise variance: (1 + 1/n)(n − 2)/(n − p − 2), with a "
             "Monte Carlo check in brackets.\n")
    L.append("| powders | " + " | ".join(f"{p} input{'s' if p > 1 else ''}" for p in (1, 2, 4, 6)) + " |")
    L.append("|---" * 5 + "|")
    for n in (12, 20, 30, 50):
        cells = [r for r in infl if r["n"] == n]
        L.append(f"| {n} | " + " | ".join(f"{r['inflation_exact']:.2f} ({r['inflation_mc']:.2f})" for r in cells) + " |")
    L.append("")
    L.append("## Joint 2-factor model fitted on all 12 powders: loadings (standardized units)\n")
    L.append("| variable | factor 1 | factor 2 | uniqueness |")
    L.append("|---|---|---|---|")
    for v, a, b, u in loadings:
        L.append(f"| {NAMES[v]} | {a:+.2f} | {b:+.2f} | {u:.2f} |")
    L.append("")
    L.append("## Fingerprint replicate noise vs model error\n")
    se = [r["se_lmg45"] for r in rows if np.isfinite(r["se_lmg45"])]
    L.append(f"Standard error of log10 mg/rev at 45° from the six protocol C revolutions: median {np.median(se):.3f}, "
             f"max {np.max(se):.3f} decades (12 powders). The best forward model's held-out RMSE is "
             f"{min(fwd['lmg45'][m]['rmse'] for m in ('aor_line', 'dem_shift', 'joint1')):.2f} decades.\n")
    (HERE / "tables.md").write_text("\n".join(L) + "\n")


def main():
    t0 = time.time()
    rows, dem = load()
    print(f"{len(rows)} powders:", ", ".join(r["powder_id"] for r in rows))
    inv, ipred = inverse(rows)
    fwd, fpred = forward(rows, dem)
    cls = classify(rows)
    ex = extras(rows)
    lc = learning_curves(rows)
    infl = inflation_table()
    J = Joint(matrix(rows, FP_CORE + PROPS), 2)
    fa_vars = FP_CORE + PROPS
    unique = np.diag(J.S) - (J.W ** 2).sum(0)
    loadings = [(v, float(J.W[0, j]), float(J.W[1, j]), float(unique[j])) for j, v in enumerate(fa_vars)]
    tables(rows, inv, fwd, cls, lc, infl, loadings, ex)
    fig_inverse(rows, inv, ipred, HERE / "ml_inverse.png")
    fig_forward(rows, fwd, fpred, cls, HERE / "ml_forward.png")
    fig_data_needs(lc, infl, HERE / "ml_data_needs.png")

    per_powder = {}
    for i, r in enumerate(rows):
        per_powder[r["powder_id"]] = {
            "display": r["display"],
            "fingerprint": {k: r[k] for k in FP_FULL}, "handbook": {k: r[k] for k in PROPS},
            "se_lmg45": r["se_lmg45"],
            "inverse_lopo": {k: {m: [round(float(ipred[k][m][0][i]), 4), round(float(ipred[k][m][1][i]), 4)]
                                 for m in ("line45", "best1", "ridge", "gp", "joint1")} for k in PROPS},
            "forward_lopo": {k: {m: [round(float(fpred[k][m][0][i]), 4), round(float(fpred[k][m][1][i]), 4)]
                                 for m in ("aor_line", "best1", "ridge", "gp", "joint1", "joint1_aoronly")}
                             for k in FWD_TARGETS},
        }
    wall = time.time() - t0
    best_inv_aor = min(("line45", "best1", "ridge", "pls1", "gp", "rf", "knn2", "joint1", "joint2"),
                       key=lambda m: inv["aor"][m]["rmse"])
    result = {
        "run": "ml-property-dose", "family": "Data-driven (machine learning) models between properties and dosing",
        "code": "scikit-learn", "version": __import__("sklearn").__version__, "status": "ran", "wall_s": round(wall, 1),
        "n_powders": len(rows),
        "key_results": {
            "inverse AoR RMSE deg (line on mg/rev 45, joint 1-factor, mean)": [
                round(inv["aor"]["line45"]["rmse"], 2), round(inv["aor"]["joint1"]["rmse"], 2),
                round(inv["aor"]["mean"]["rmse"], 2)],
            "inverse AoR ceiling Q2 from handbook spread": round(inv["aor"]["ceiling"]["q2_max"], 2),
            "forward log10 mg/rev 45 RMSE (AoR line, ridge all, joint, DEM+offset)": [
                round(fwd["lmg45"]["aor_line"]["rmse"], 2), round(fwd["lmg45"]["ridge"]["rmse"], 2),
                round(fwd["lmg45"]["joint1"]["rmse"], 2), round(fwd["lmg45"]["dem_shift"]["rmse"], 2)],
            "flow/no-flow from AoR (right of 12)": cls["conveys | AoR"]["correct"],
            "best inverse AoR model": best_inv_aor,
        },
        "inverse": inv, "forward": fwd, "classification": cls, "extras": ex, "learning_curves": lc,
        "inflation": infl,
        "joint2_loadings": [{"variable": v, "f1": a, "f2": b, "uniqueness": u} for v, a, b, u in loadings],
        "per_powder": per_powder,
        "notes": "Handbook (#163) property values, not same-jar measurements; n = 12; leave-one-powder-out "
                 "throughout, with selection and tuning nested inside each fold.",
    }
    (HERE / "result.json").write_text(json.dumps(result, indent=1, default=float) + "\n")
    print(json.dumps(result["key_results"], indent=1))
    print(f"wall {wall:.0f} s")


if __name__ == "__main__":
    main()
