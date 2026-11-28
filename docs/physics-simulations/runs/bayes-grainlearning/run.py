"""GrainLearning iterative Bayesian filter: calibrate (mu_s, Bo) of the doser STAND-IN
model (doser_standin.py, not DEM) against measured salt mg/rev vs tilt.

Usage: OMP_NUM_THREADS=1 python run.py [outdir]
"""
import json
import os
import sys
import time

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import doser_standin as ds  # noqa: E402
import grainlearning  # noqa: E402
from grainlearning import BayesianCalibration  # noqa: E402
from grainlearning.dynamic_systems import DynamicSystem  # noqa: E402

OUT = sys.argv[1] if len(sys.argv) > 1 else HERE
MU_R_FIXED = 0.3
NUM_SAMPLES = 40
NUM_ITER = 8
t0 = time.time()


def run_sim(calib):
    """GrainLearning callback: evaluate the stand-in for every parameter sample."""
    sysm = calib.system
    data = []
    for mu_s, bo in sysm.param_data:
        y = ds.mg_per_rev(sysm.ctrl_data, mu_s, MU_R_FIXED, bo)
        data.append(np.array(y, ndmin=2))
    sysm.set_sim_data(data)


calibration = BayesianCalibration.from_dict({
    "num_iter": NUM_ITER,
    "callback": run_sim,
    "system": {
        "system_type": DynamicSystem,
        "param_names": ["mu_s", "Bo"],
        "param_min": [0.1, 0.0],
        "param_max": [1.0, 2.0],
        "num_samples": NUM_SAMPLES,
        "obs_data": [list(ds.OBS_MG)],
        "obs_names": ["mg_per_rev"],
        "ctrl_data": list(ds.TILTS_DEG),
        "ctrl_name": "tilt_deg",
        "sim_name": "doser_standin",
        "sigma_tol": 1.0e-3,  # GrainLearning default
    },
    "inference": {
        "Bayes_filter": {"ess_target": 0.3},
        "sampling": {"max_num_components": 2, "n_init": 1, "random_state": 0,
                     "slice_sampling": True, "covariance_type": "full"},
        "initial_sampling": "halton",
    },
    "save_fig": -1,
})

hist = []
for it in range(NUM_ITER):
    params = calibration.inference.param_data_list[-1].copy() if it > 0 else None
    stop = calibration.run_one_iteration()
    params = calibration.system.param_data.copy()
    w = calibration.inference.posterior.copy()
    mean = (w[:, None] * params).sum(0)
    sd = np.sqrt((w[:, None] * (params - mean) ** 2).sum(0))
    best = params[np.argmax(w)]
    ess = float(1.0 / np.sum(w ** 2) / len(w))
    hist.append({"iter": it, "params": params.tolist(), "weights": w.tolist(),
                 "mean": mean.tolist(), "sd": sd.tolist(), "best": best.tolist(),
                 "sigma": float(np.ravel(calibration.system.sigma_max)[0]), "ess": ess})
    print(f"iter {it}: mean mu_s={mean[0]:.3f}+/-{sd[0]:.3f}  Bo={mean[1]:.3f}+/-{sd[1]:.3f}"
          f"  best={best}  sigma={float(np.ravel(calibration.system.sigma_max)[0]):.4g}", flush=True)
    if stop:
        break

wall = time.time() - t0
last = hist[-1]
pm = np.array(last["mean"])
pb = np.array(last["best"])
fit_mean = ds.mg_per_rev(ds.TILTS_DEG, pm[0], MU_R_FIXED, pm[1])
fit_best = ds.mg_per_rev(ds.TILTS_DEG, pb[0], MU_R_FIXED, pb[1])
nominal = ds.mg_per_rev(ds.TILTS_DEG, 0.5, MU_R_FIXED, 0.0)

# ---------- figure ----------
fig, ax = plt.subplots(1, 3, figsize=(15, 4.6))
cmap = plt.get_cmap("viridis")
n = len(hist)
for h in hist:
    p = np.array(h["params"]); w = np.array(h["weights"])
    ax[0].scatter(p[:, 0], p[:, 1], s=8 + 300 * w, color=cmap(h["iter"] / max(n - 1, 1)),
                  alpha=0.7, label=f"iter {h['iter']}", edgecolors="none")
ax[0].plot(0.5, 0.0, "r*", ms=14, label="DEM twin nominal (0.5, 0)")
ax[0].set_xlabel(r"sliding friction $\mu_s$ (-)")
ax[0].set_ylabel("granular Bond number Bo (-)")
ax[0].set_title("GrainLearning samples per iteration\n(marker size = posterior weight)")
ax[0].legend(fontsize=7, ncol=2)

it_ax = np.array([h["iter"] for h in hist])
means = np.array([h["mean"] for h in hist]); sds = np.array([h["sd"] for h in hist])
ax[1].errorbar(it_ax - 0.05, means[:, 0], sds[:, 0], fmt="o-", capsize=3, label=r"$\mu_s$")
ax[1].errorbar(it_ax + 0.05, means[:, 1], sds[:, 1], fmt="s-", capsize=3, label="Bo")
ax[1].set_xlabel("iteration")
ax[1].set_ylabel("posterior mean $\\pm$ 1 sd (-)")
ax[1].set_title("posterior evolution")
ax[1].legend()

tt = np.linspace(0, 45, 91)
p = np.array(last["params"]); w = np.array(last["weights"])
ens = np.array([ds.mg_per_rev(tt, a, MU_R_FIXED, b) for a, b in p])
order = np.argsort(-w)[:20]
for k in order:
    ax[2].plot(tt, ens[k], color="0.75", lw=0.8, zorder=1)
ax[2].plot(tt, ds.mg_per_rev(tt, pm[0], MU_R_FIXED, pm[1]), "C0-", lw=2,
           label=f"stand-in, posterior mean ($\\mu_s$={pm[0]:.2f}, Bo={pm[1]:.2f})")
ax[2].plot(tt, ds.mg_per_rev(tt, 0.5, MU_R_FIXED, 0.0), "r--", lw=1.2, label="stand-in, nominal (0.5, 0)")
ax[2].errorbar(ds.TILTS_DEG, ds.OBS_MG, ds.OBS_SD, fmt="ko", capsize=3, label="measured salt (60 rpm)")
ax[2].plot(ds.TILTS_DEG, ds.DEM_TWIN_MG, "^", color="C1", ms=8, label="LIGGGHTS twin (no fit)")
ax[2].set_xlabel("auger tilt (deg)")
ax[2].set_ylabel("delivery (mg per auger rev)")
ax[2].set_title("fingerprint: data vs calibrated stand-in\n(grey: 20 highest-weight samples)")
ax[2].legend(fontsize=7, loc="upper left")
fig.suptitle("bayes-grainlearning: GrainLearning %s iterative Bayesian filter on a STAND-IN doser model "
             "(not DEM); $\\mu_r$ fixed at 0.3" % grainlearning.__version__ if hasattr(grainlearning, "__version__")
             else "bayes-grainlearning: GrainLearning on a STAND-IN doser model (not DEM)", fontsize=10)
fig.tight_layout()
fig.savefig(os.path.join(OUT, "grainlearning_posterior.png"), dpi=110)

res = {
    "id": "bayes-grainlearning",
    "method": "Iterative Bayesian filtering (sequential Monte Carlo + GMM resampling) calibrating "
              "(mu_s, Bo) of a stand-in doser model against measured salt mg/rev vs tilt",
    "code": "GrainLearning (pip grainlearning)",
    "version": getattr(grainlearning, "__version__", "2.0.5"),
    "status": "ran",
    "wall_s": round(wall, 1),
    "cores": 1,
    "key_results": {
        "iterations_run": n,
        "samples_per_iteration": NUM_SAMPLES,
        "model_evaluations": n * NUM_SAMPLES,
        "posterior_mean": {"mu_s": round(pm[0], 4), "Bo": round(pm[1], 4)},
        "posterior_sd": {"mu_s": round(last["sd"][0], 4), "Bo": round(last["sd"][1], 4)},
        "most_probable_sample": {"mu_s": round(pb[0], 4), "Bo": round(pb[1], 4)},
        "final_sigma_normalized": last["sigma"],
        "fit_at_posterior_mean_mg_per_rev": dict(zip([str(t) for t in ds.TILTS_DEG], np.round(fit_mean, 1).tolist())),
        "fit_at_most_probable_mg_per_rev": dict(zip([str(t) for t in ds.TILTS_DEG], np.round(fit_best, 1).tolist())),
        "standin_at_nominal_dem_params_mg_per_rev": dict(zip([str(t) for t in ds.TILTS_DEG], np.round(nominal, 1).tolist())),
        "measured_mg_per_rev": dict(zip([str(t) for t in ds.TILTS_DEG], ds.OBS_MG.tolist())),
        "per_iteration": [{k: h[k] for k in ("iter", "mean", "sd", "best", "sigma", "ess")} for h in hist],
    },
    "notes": "Forward model is a stand-in (screw push + Beverloo annulus + tilt threshold), not DEM. "
             "GrainLearning's likelihood uses a relative (obs-scaled) Gaussian whose width sigma is tuned "
             "each iteration to an effective sample size of 0.3, so the posterior width reflects that "
             "annealing scheme rather than the measurement error bars.",
}
with open(os.path.join(OUT, "result.json"), "w") as f:
    json.dump(res, f, indent=1)
print(json.dumps({k: res["key_results"][k] for k in ("posterior_mean", "posterior_sd", "most_probable_sample",
                                                      "fit_at_posterior_mean_mg_per_rev")}, indent=1))
print("wall_s", round(wall, 1))
