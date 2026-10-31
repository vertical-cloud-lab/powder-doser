"""GP emulator on a Sobol design + emcee posterior for (mu_s, mu_r, Bo) of the doser
STAND-IN model (doser_standin.py, not DEM). Case A: measured salt mg/rev vs tilt only.
Case B: same plus a synthetic angle-of-repose observation (second observable).

Usage: OMP_NUM_THREADS=1 python run.py [outdir]
"""
import json
import os
import sys
import time
import warnings

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import emcee
import sklearn
from scipy.stats import qmc
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import ConstantKernel, Matern, WhiteKernel

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import doser_standin as ds  # noqa: E402

OUT = sys.argv[1] if len(sys.argv) > 1 else HERE
warnings.filterwarnings("ignore")
rng = np.random.default_rng(1)
t0 = time.time()

NAMES = [r"$\mu_s$", r"$\mu_r$", "Bo"]
LO = np.array([0.1, 0.02, 0.0])
HI = np.array([1.0, 0.6, 1.5])
N_DESIGN = 48
TRUTH_AOR = (0.5, 0.3, 0.0)      # synthetic AoR "measurement" generated at the DEM twin's nominal set
AOR_SD = 1.5                     # deg, assumed measurement error of a heap test
MUW_OBS, MUW_SD = 0.4, 0.04      # synthetic wall-friction test (PLA, ASTM D6128-type), model mu_w = 0.8 mu_s


def forward(x):
    """x: (n,3) physical -> (n,5): mg/rev at 4 tilts, AoR (deg)."""
    x = np.atleast_2d(x)
    mg = np.array([ds.mg_per_rev(ds.TILTS_DEG, *xi) for xi in x])
    aor = ds.angle_of_repose(x[:, 0], x[:, 1], x[:, 2])[:, None]
    return np.hstack([mg, aor])


# ---------- Sobol design and GP emulators ----------
sob = qmc.Sobol(d=3, scramble=True, seed=7)
u_train = sob.random(N_DESIGN)
x_train = LO + u_train * (HI - LO)
y_train = forward(x_train)
u_test = rng.random((400, 3))
y_test = forward(LO + u_test * (HI - LO))

gps, val = [], []
for j in range(y_train.shape[1]):
    k = ConstantKernel(1.0, (1e-3, 1e3)) * Matern(length_scale=[0.5] * 3, length_scale_bounds=(0.03, 20.0), nu=2.5) \
        + WhiteKernel(1e-4, (1e-8, 1e-1))
    gp = GaussianProcessRegressor(kernel=k, normalize_y=True, n_restarts_optimizer=4, random_state=j)
    gp.fit(u_train, y_train[:, j])
    pred = gp.predict(u_test)
    rmse = float(np.sqrt(np.mean((pred - y_test[:, j]) ** 2)))
    r2 = float(1 - np.sum((pred - y_test[:, j]) ** 2) / np.sum((y_test[:, j] - y_test[:, j].mean()) ** 2))
    gps.append(gp)
    val.append({"output": (["mg@%g" % t for t in ds.TILTS_DEG] + ["AoR"])[j], "rmse": rmse, "r2": r2,
                "kernel": str(gp.kernel_)})
    print(val[-1]["output"], "RMSE %.2f R2 %.3f" % (rmse, r2), flush=True)

obs_dose = ds.OBS_MG
sd_dose = ds.OBS_SD
aor_obs = float(ds.angle_of_repose(*TRUTH_AOR))


def emulate(u):
    mus, sds = [], []
    for gp in gps:
        m, s = gp.predict(np.atleast_2d(u), return_std=True)
        mus.append(m); sds.append(s)
    return np.array(mus).T, np.array(sds).T


def log_prob(u, use_aor, use_wall=False):
    if np.any(u < 0) or np.any(u > 1):
        return -np.inf
    m, s = emulate(u)
    m, s = m[0], s[0]
    var = sd_dose ** 2 + s[:4] ** 2
    lp = -0.5 * np.sum((m[:4] - obs_dose) ** 2 / var + np.log(var))
    if use_aor:
        va = AOR_SD ** 2 + s[4] ** 2
        lp += -0.5 * ((m[4] - aor_obs) ** 2 / va + np.log(va))
    if use_wall:
        mu_s = LO[0] + u[0] * (HI[0] - LO[0])
        lp += -0.5 * ((0.8 * mu_s - MUW_OBS) / MUW_SD) ** 2
    return lp


chains = {}
for case, use_aor, use_wall in (("dosing_only", False, False), ("dosing_plus_AoR", True, False),
                                ("dosing_plus_wall_friction", False, True)):
    nw, nsteps, burn = 24, 1500, 500
    p0 = rng.random((nw, 3))
    sampler = emcee.EnsembleSampler(nw, 3, log_prob, args=(use_aor, use_wall))
    sampler.run_mcmc(p0, nsteps, progress=False)
    flat = sampler.get_chain(discard=burn, thin=5, flat=True)
    chains[case] = {"u": flat, "x": LO + flat * (HI - LO),
                    "acc": float(np.mean(sampler.acceptance_fraction))}
    try:
        chains[case]["tau"] = sampler.get_autocorr_time(discard=burn, quiet=True).tolist()
    except Exception as e:  # noqa: BLE001
        chains[case]["tau"] = str(e)
    print(case, "done", "acc %.2f" % chains[case]["acc"], flush=True)

summ = {}
for case, c in chains.items():
    x = c["x"]
    corr = np.corrcoef(x.T)
    summ[case] = {
        "mean": dict(zip(["mu_s", "mu_r", "Bo"], np.round(x.mean(0), 4).tolist())),
        "sd": dict(zip(["mu_s", "mu_r", "Bo"], np.round(x.std(0), 4).tolist())),
        "p05_p95": {n: [round(float(np.percentile(x[:, i], 5)), 4), round(float(np.percentile(x[:, i], 95)), 4)]
                    for i, n in enumerate(["mu_s", "mu_r", "Bo"])},
        "corr_mu_s_mu_r": round(float(corr[0, 1]), 3),
        "corr_mu_s_Bo": round(float(corr[0, 2]), 3),
        "corr_mu_r_Bo": round(float(corr[1, 2]), 3),
        "acceptance": round(c["acc"], 3),
        "autocorr_time": c["tau"],
        "n_samples": int(len(x)),
    }
    # posterior predictive at posterior mean, using the TRUE stand-in (checks emulator too)
    summ[case]["standin_at_posterior_mean_mg_per_rev"] = np.round(forward(x.mean(0))[0, :4], 1).tolist()
    summ[case]["standin_AoR_at_posterior_mean_deg"] = round(float(forward(x.mean(0))[0, 4]), 2)

wall = time.time() - t0

# ---------- figure ----------
fig, ax = plt.subplots(2, 3, figsize=(15, 9))
pairs = [(0, 1), (0, 2), (1, 2)]
cols = {"dosing_only": "C0", "dosing_plus_AoR": "C3", "dosing_plus_wall_friction": "C2"}
labs = {"dosing_only": "mg/rev vs tilt only", "dosing_plus_AoR": "+ angle of repose (synthetic)",
        "dosing_plus_wall_friction": "+ wall-friction test (synthetic)"}
for a, (i, j) in zip(ax[0], pairs):
    for case, c in chains.items():
        x = c["x"]
        a.scatter(x[::4, i], x[::4, j], s=2, alpha=0.2, color=cols[case], label=labs[case]
                  + "  (r = %.2f)" % np.corrcoef(x[:, i], x[:, j])[0, 1])
    a.scatter(x_train[:, i], x_train[:, j], marker="x", s=14, color="k", lw=0.8, label="Sobol design (48)")
    a.plot(*[TRUTH_AOR[q] for q in (i, j)], "k*", ms=12, label="nominal DEM set (synthetic truth)")
    a.set_xlim(LO[i], HI[i]); a.set_ylim(LO[j], HI[j])
    a.set_xlabel(NAMES[i] + " (-)"); a.set_ylabel(NAMES[j] + " (-)")
    leg = a.legend(fontsize=7, loc="upper right", markerscale=4)
ax[0, 0].set_title("posterior samples (emcee on GP emulator)")

# emulator parity on held-out points
pred_test = np.column_stack([gp.predict(u_test) for gp in gps])
for j, lab in enumerate(["0", "22.5", "27.5", "45"]):
    ax[1, 0].scatter(y_test[:, j], pred_test[:, j], s=4, alpha=0.5, label=f"{lab} deg (R$^2$={val[j]['r2']:.3f})")
lim = [0, max(y_test[:, :4].max(), pred_test[:, :4].max()) * 1.05]
ax[1, 0].plot(lim, lim, "k-", lw=0.8)
ax[1, 0].set_xlabel("stand-in model (mg/rev)"); ax[1, 0].set_ylabel("GP emulator (mg/rev)")
ax[1, 0].set_title("emulator check, 400 held-out points"); ax[1, 0].legend(fontsize=7)

for case, c in chains.items():
    for i, ls in zip(range(3), ["-", "--", ":"]):
        h, e = np.histogram(c["u"][:, i], bins=40, range=(0, 1), density=True)
        ax[1, 1].step(0.5 * (e[1:] + e[:-1]), h, ls=ls, color=cols[case],
                      label=f"{NAMES[i]}, {labs[case]}")
ax[1, 1].set_xlabel("parameter scaled to prior box (0 = low bound, 1 = high bound)")
ax[1, 1].set_ylabel("posterior density (-)")
ax[1, 1].set_title("marginals (prior = flat at 1)")
ax[1, 1].legend(fontsize=6)

tt = np.linspace(0, 45, 91)
for case, c in chains.items():
    sel = c["x"][rng.choice(len(c["x"]), 150, replace=False)]
    curves = np.array([ds.mg_per_rev(tt, *s) for s in sel])
    lo, hi = np.percentile(curves, [5, 95], axis=0)
    ax[1, 2].fill_between(tt, lo, hi, color=cols[case], alpha=0.25, label=labs[case] + " (5-95 %)")
ax[1, 2].errorbar(ds.TILTS_DEG, ds.OBS_MG, ds.OBS_SD, fmt="ko", capsize=3, label="measured salt (60 rpm)")
ax[1, 2].plot(ds.TILTS_DEG, ds.DEM_TWIN_MG, "^", color="C1", ms=8, label="LIGGGHTS twin (no fit)")
ax[1, 2].set_xlabel("auger tilt (deg)"); ax[1, 2].set_ylabel("delivery (mg per auger rev)")
ax[1, 2].set_title("posterior predictive (true stand-in)"); ax[1, 2].legend(fontsize=7, loc="upper left")
fig.suptitle("bayes-gp-emulator-mcmc: scikit-learn %s GP emulator (48-pt Sobol) + emcee %s, on a STAND-IN doser model "
             "(not DEM)" % (sklearn.__version__, emcee.__version__), fontsize=11)
fig.tight_layout()
fig.savefig(os.path.join(OUT, "gp_emcee_posterior.png"), dpi=100)

res = {
    "id": "bayes-gp-emulator-mcmc",
    "method": "Gaussian-process emulator on a 48-point Sobol design over (mu_s, mu_r, Bo) of a stand-in "
              "doser model + emcee posterior; identifiability with and without an angle-of-repose observable",
    "code": "scikit-learn GaussianProcessRegressor + emcee + scipy.stats.qmc.Sobol",
    "version": f"scikit-learn {sklearn.__version__}, emcee {emcee.__version__}",
    "status": "ran",
    "wall_s": round(wall, 1),
    "cores": 1,
    "key_results": {
        "design_points": N_DESIGN,
        "prior_box": {"mu_s": [0.1, 1.0], "mu_r": [0.02, 0.6], "Bo": [0.0, 1.5]},
        "emulator_validation_400_heldout": val,
        "synthetic_AoR_obs_deg": round(aor_obs, 2), "AoR_sd_deg": AOR_SD,
        "synthetic_wall_friction_obs": MUW_OBS, "wall_friction_sd": MUW_SD,
        "posterior": summ,
        "equivalent_DEM_cost": {
            "runs": N_DESIGN * 4,
            "note": "48 parameter sets x 4 tilts, one 30-CPU-min revolution each",
            "cpu_hours": N_DESIGN * 4 * 0.5,
            "wall_hours_on_4_cores": N_DESIGN * 4 * 0.5 / 4,
        },
    },
    "notes": "Forward model is a stand-in (screw push + Beverloo annulus + tilt threshold; Zhou-form AoR), "
             "not DEM. The AoR observation is synthetic (stand-in evaluated at the DEM twin's nominal set "
             "mu_s=0.5, mu_r=0.3, Bo=0, sd 1.5 deg); the wall-friction observation is also synthetic (mu_w = 0.4 +/- 0.04, "
             "model mu_w = 0.8 mu_s). GP predictive variance is added to the likelihood variance.",
}
with open(os.path.join(OUT, "result.json"), "w") as f:
    json.dump(res, f, indent=1)
print(json.dumps(summ, indent=1))
print("wall_s", round(wall, 1))
