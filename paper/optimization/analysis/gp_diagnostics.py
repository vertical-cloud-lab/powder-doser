#!/usr/bin/env python3
"""Model diagnostics for the salt campaign (Elsevier's ML rubric, items 5-8).

Refits the campaign's surrogate (a fully Bayesian SAAS Gaussian process per objective,
BoTorch) to the 42 campaign doses, with the outcomes encoded as the campaign encoded them
for Ax (a jammed dose reported at the 180 s / 20 mg limits or its true value if worse;
overshoots at their measured values), and compares it by leave-one-out cross-validation
with three simpler models:

  constant     the mean of the other 41 doses (no model at all)
  linear       ordinary least squares on the eight settings (main effects only)
  gp-map       a standard GP (Matern-5/2, one length scale per setting, MAP fit)
  saas         the campaign's model class (SAAS prior, NUTS), Standardize outcome
  saas-log     the same on log(time), as a sensitivity check (time only)

Inputs are the eight settings scaled to [0, 1] (the two tap settings as 0/1), as Ax's
default transforms do.  The campaign itself used Ax 0.4.3; this refit uses BoTorch
directly, so hyperparameter draws differ in detail, but the model class, inputs and
outcome encoding are the same.

Writes analysis/results/gp_cv.json, gp_cv_predictions.csv and figures/figS_gp_cv.{pdf,png}.
Usage (from paper/optimization/):  python3 analysis/gp_diagnostics.py [--fast]
"""
from __future__ import annotations

import json
import math
import sys
import time
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

warnings.filterwarnings("ignore")
HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
OUT = HERE / "results"
SALT = ROOT / "data" / "salt-20260929T014732Z"
FAST = "--fast" in sys.argv
T_LIM, E_LIM = 180.0, 20.0
PARAMS = ["bulk_tap", "trim_tap", "bulk_tilt_deg", "trickle_tilt_deg", "tap_tilt_deg", "bulk_rpm",
          "trickle_start_remaining_g", "tolerance_g"]


def load():
    camp = json.load(open(SALT / "campaign.json"))
    bounds = {p["name"]: p.get("bounds") for p in camp["search_space"]}
    rows = []
    for line in open(SALT / "campaign_records.jsonl"):
        r = json.loads(line)
        if r["mode"] == "validation":
            continue
        s, p = r["summary"], r["params"]
        jam = s["status"] not in ("ok", "overshoot")
        t, e = s["t_total_s"], s["abs_error_mg"]
        if jam:
            t, e = max(t, T_LIM), max(e, E_LIM)
        x = []
        for k in PARAMS:
            if k in ("bulk_tap", "trim_tap"):
                x.append(1.0 if p[k] == "2hz" else 0.0)
            else:
                lo, hi = bounds[k]
                x.append((p[k] - lo) / (hi - lo))
        rows.append(dict(label=r["label"], status=s["status"], t=t, e=e, **{f"x{i}": v for i, v in enumerate(x)}))
    df = pd.DataFrame(rows)
    X = df[[f"x{i}" for i in range(len(PARAMS))]].values
    return df, X, bounds


def x_of(params, bounds):
    x = []
    for k in PARAMS:
        if k in ("bulk_tap", "trim_tap"):
            x.append(1.0 if params[k] == "2hz" else 0.0)
        else:
            lo, hi = bounds[k]
            x.append((params[k] - lo) / (hi - lo))
    return np.array(x)


# ------------------------------------------------------------------ models
def fit_predict_constant(Xtr, ytr, Xte):
    mu = ytr.mean()
    sd = ytr.std(ddof=1) * math.sqrt(1 + 1 / len(ytr))
    return np.full(len(Xte), mu), np.full(len(Xte), sd)


def fit_predict_linear(Xtr, ytr, Xte):
    A = np.c_[np.ones(len(Xtr)), Xtr]
    beta, *_ = np.linalg.lstsq(A, ytr, rcond=None)
    res = ytr - A @ beta
    dof = max(len(ytr) - A.shape[1], 1)
    s2 = res @ res / dof
    At = np.c_[np.ones(len(Xte)), Xte]
    cov = s2 * np.linalg.pinv(A.T @ A)
    var = s2 + np.einsum("ij,jk,ik->i", At, cov, At)
    return At @ beta, np.sqrt(var)


def _torch():
    import torch
    torch.set_default_dtype(torch.float64)
    return torch


def fit_predict_gp_map(Xtr, ytr, Xte):
    torch = _torch()
    from botorch.fit import fit_gpytorch_mll
    from botorch.models import SingleTaskGP
    from botorch.models.transforms import Standardize
    from gpytorch.mlls import ExactMarginalLogLikelihood
    m = SingleTaskGP(torch.tensor(Xtr), torch.tensor(ytr).unsqueeze(-1), outcome_transform=Standardize(m=1))
    fit_gpytorch_mll(ExactMarginalLogLikelihood(m.likelihood, m))
    with torch.no_grad():
        post = m.posterior(torch.tensor(Xte), observation_noise=True)
    return post.mean.squeeze(-1).detach().numpy(), post.variance.squeeze(-1).sqrt().detach().numpy()


def fit_saas(Xtr, ytr, seed=0):
    torch = _torch()
    from botorch.fit import fit_fully_bayesian_model_nuts
    from botorch.models.fully_bayesian import SaasFullyBayesianSingleTaskGP
    from botorch.models.transforms import Standardize
    torch.manual_seed(seed)
    m = SaasFullyBayesianSingleTaskGP(torch.tensor(Xtr), torch.tensor(ytr).unsqueeze(-1),
                                      outcome_transform=Standardize(m=1))
    w, n, th = (64, 64, 8) if FAST else (256, 128, 16)
    fit_fully_bayesian_model_nuts(m, warmup_steps=w, num_samples=n, thinning=th, disable_progbar=True)
    return m


def saas_predict(m, Xte):
    """Mixture over the NUTS draws: mean and total variance (incl. observation noise)."""
    torch = _torch()
    with torch.no_grad():
        post = m.posterior(torch.tensor(Xte), observation_noise=True)
        mu = post.mixture_mean.squeeze(-1).detach().numpy()
        var = post.mixture_variance.squeeze(-1).detach().numpy()
    return mu, np.sqrt(var)


def fit_predict_saas(Xtr, ytr, Xte, seed=0):
    return saas_predict(fit_saas(Xtr, ytr, seed), Xte)


# ------------------------------------------------------------- evaluation
def loo(model_fn, X, y, name, log=False):
    mu, sd = np.zeros(len(y)), np.zeros(len(y))
    t0 = time.time()
    for i in range(len(y)):
        tr = np.arange(len(y)) != i
        ytr = np.log(y[tr]) if log else y[tr]
        m_, s_ = model_fn(X[tr], ytr, X[i:i + 1])
        mu[i], sd[i] = m_[0], s_[0]
    print(f"  {name}: {time.time() - t0:.0f} s", flush=True)
    return mu, sd


def metrics(y, mu, sd, log=False):
    """Scores on the scale the model was fitted on (log time for saas-log)."""
    yy = np.log(y) if log else y
    z = (yy - mu) / sd
    nlpd = float(np.mean(0.5 * np.log(2 * np.pi * sd ** 2) + 0.5 * z ** 2))
    out = {"rmse": float(np.sqrt(np.mean((yy - mu) ** 2))), "mae": float(np.mean(np.abs(yy - mu))),
           "spearman_rho": float(stats.spearmanr(yy, mu).statistic),
           "spearman_p": float(stats.spearmanr(yy, mu).pvalue),
           "coverage95": float(np.mean(np.abs(z) <= 1.96)), "nlpd": nlpd,
           "z_mean": float(z.mean()), "z_sd": float(z.std(ddof=1)),
           "shapiro_p": float(stats.shapiro(z).pvalue)}
    return out


def main():
    df, X, bounds = load()
    res, preds = {"n": int(len(df)), "inputs": PARAMS, "fast": FAST,
                  "outcome_encoding": "jams at max(true, 180 s / 20 mg); overshoots at measured values"}, {}
    models = {"constant": fit_predict_constant, "linear": fit_predict_linear, "gp-map": fit_predict_gp_map,
              "saas": fit_predict_saas}
    for obj in ("t", "e"):
        y = df[obj].values.astype(float)
        res[obj] = {}
        for name, fn in models.items():
            mu, sd = loo(fn, X, y, f"{obj}/{name}")
            res[obj][name] = metrics(y, mu, sd)
            preds[f"{obj}_{name}_mu"], preds[f"{obj}_{name}_sd"] = mu, sd
        if obj == "t":
            mu, sd = loo(fit_predict_saas, X, y, "t/saas-log", log=True)
            res[obj]["saas-log"] = metrics(y, mu, sd, log=True)
            preds["t_saas-log_mu"], preds["t_saas-log_sd"] = mu, sd
    pr = pd.concat([df[["label", "status", "t", "e"]], pd.DataFrame(preds)], axis=1)
    pr.to_csv(OUT / "gp_cv_predictions.csv", index=False)

    # full-data SAAS fits: relevance of each setting, and the prediction at bo-005
    camp_bo = [json.loads(l) for l in open(SALT / "campaign_records.jsonl")]
    bo5 = next(r for r in camp_bo if r["label"] == "bo-005")
    x5 = x_of(bo5["params"], bounds)[None, :]
    val = [r["summary"] for r in camp_bo if r["mode"] == "validation" and "bo-005" in r["label"]
           and r["trial_index"] not in (42, 43)]
    res["full_fit"] = {}
    for obj in ("t", "e"):
        y = df[obj].values.astype(float)
        m = fit_saas(X, y, seed=1)
        ls = m.covar_module.base_kernel.lengthscale.detach().numpy().reshape(-1, X.shape[1])
        inv = np.median(1.0 / ls, axis=0)
        mu, sd = saas_predict(m, x5)
        obs = np.array([v["t_total_s"] if obj == "t" else v["abs_error_mg"] for v in val])
        res["full_fit"][obj] = {
            "median_inverse_lengthscale": dict(zip(PARAMS, map(float, inv))),
            "bo005_pred_mean": float(mu[0]), "bo005_pred_sd_incl_noise": float(sd[0]),
            "bo005_validation_mean": float(obs.mean()),
            "bo005_validation_inside_95pi": int(np.sum(np.abs(obs - mu[0]) <= 1.96 * sd[0])),
            "bo005_validation_n": int(len(obs))}
    json.dump(res, open(OUT / "gp_cv.json", "w"), indent=1)
    print(json.dumps({k: v for k, v in res.items() if k in ("t", "e")}, indent=1))
    print(json.dumps(res["full_fit"], indent=1))
    plot(pr, res)


def plot(pr, res):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update({"font.size": 7, "axes.spines.top": False, "axes.spines.right": False,
                         "font.family": "sans-serif", "font.sans-serif": ["DejaVu Sans"], "pdf.fonttype": 42})
    names = [("linear", "linear (OLS)"), ("gp-map", "GP, MAP"), ("saas", "SAAS GP (campaign model)")]
    fig, axs = plt.subplots(2, 3, figsize=(7.48, 4.6))
    for r, (obj, lab, lim) in enumerate((("t", "time per dose (s)", (0, 420)), ("e", "|error| (mg)", (0, 90)))):
        for c, (name, title) in enumerate(names):
            ax = axs[r, c]
            mu, sd = pr[f"{obj}_{name}_mu"], pr[f"{obj}_{name}_sd"]
            ax.errorbar(pr[obj], mu, yerr=1.96 * sd, fmt="o", ms=3, lw=0.5, color="#2a78d6", ecolor="#9cc3f0",
                        mec="white", mew=0.4)
            ax.plot(lim, lim, color="#8a8983", lw=0.6, ls=(0, (3, 2)))
            ax.set_xlim(lim)
            ax.set_ylim(lim[0] - 0.4 * lim[1], 1.4 * lim[1])
            m = res[obj][name]
            ax.set_title(f"{title}\nρ = {m['spearman_rho']:.2f}, 95% coverage {100 * m['coverage95']:.0f}%",
                         fontsize=7)
            ax.set_xlabel(f"observed {lab}")
            if c == 0:
                ax.set_ylabel(f"leave-one-out prediction")
    fig.tight_layout()
    for ext in ("pdf", "png"):
        fig.savefig(ROOT / "figures" / f"figS_gp_cv.{ext}", dpi=300, bbox_inches="tight")
    print("wrote figures/figS_gp_cv")


if __name__ == "__main__":
    main()
