"""Physics-informed neural networks (Raissi, Perdikaris & Karniadakis 2019) for the Janssen
equation of the powder column above the auger inlet.

  d sigma / dz = rho_b g - (4 K mu_w / D) sigma,  sigma(0) = 0
  nondimensional: s = sigma / (rho_b g D), zeta = z / D, lambda = K mu_w:
  ds/dzeta = 1 - 4 lambda s,  s(0) = 0,  exact s = (1 - exp(-4 lambda zeta)) / (4 lambda)

(1) forward, parametric PINN s(zeta, lambda) trained on the ODE residual only (no data):
    a surrogate over lambda in [0.05, 0.5];
(2) inverse PINN: infer lambda from 8 noisy synthetic stress readings (lambda_true = 0.2,
    i.e. K = 0.5 (Jaky, phi ~ 30 deg) x mu_w = 0.4 (salt-PLA, LIGGGHTS twin)), 5 noise seeds.

Usage: OMP_NUM_THREADS=1 python run.py [outdir]
"""
import json
import os
import sys
import time

import numpy as np
import torch
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(os.path.abspath(__file__))
torch.set_num_threads(1)
RHO_B, G, D = 1256.0, 9.81, 20.9e-3          # kg/m3, m/s2, m (auger bore)
SIG0 = RHO_B * G * D                         # Pa per unit s
ZMAX = 3.0                                   # column height 3 D = 63 mm
LAM_TRUE = 0.2
t0 = time.time()


def exact(zeta, lam):
    return (1 - np.exp(-4 * lam * zeta)) / (4 * lam)


def mlp(nin, width=32, depth=3):
    layers, d = [], nin
    for _ in range(depth):
        layers += [torch.nn.Linear(d, width), torch.nn.Tanh()]
        d = width
    layers.append(torch.nn.Linear(d, 1))
    return torch.nn.Sequential(*layers)


# ---------- (1) forward parametric PINN ----------
torch.manual_seed(0)
net = mlp(2)
opt = torch.optim.Adam(net.parameters(), lr=3e-3)
sched = torch.optim.lr_scheduler.StepLR(opt, 1500, 0.3)
fwd_log = []
for it in range(4500):
    z = (torch.rand(512, 1) * ZMAX).requires_grad_(True)
    lam = 0.05 + 0.45 * torch.rand(512, 1)
    s = z * net(torch.cat([z / ZMAX, (lam - 0.275) / 0.225], 1))          # hard BC s(0) = 0
    ds = torch.autograd.grad(s.sum(), z, create_graph=True)[0]
    loss = ((ds - 1 + 4 * lam * s) ** 2).mean()
    opt.zero_grad(); loss.backward(); opt.step(); sched.step()
    if it % 100 == 0:
        fwd_log.append((it, float(loss)))
fwd_s = time.time() - t0
zg = np.linspace(0, ZMAX, 121)
lg = np.linspace(0.05, 0.5, 46)
Zg, Lg = np.meshgrid(zg, lg)
with torch.no_grad():
    zt = torch.tensor(Zg.reshape(-1, 1), dtype=torch.float32)
    lt = torch.tensor(Lg.reshape(-1, 1), dtype=torch.float32)
    sp = (zt * net(torch.cat([zt / ZMAX, (lt - 0.275) / 0.225], 1))).numpy().reshape(Zg.shape)
se = exact(Zg, Lg)
rel_err = np.abs(sp - se).max() / np.abs(se).max()
rel_err_l2 = np.sqrt(((sp - se) ** 2).mean() / (se ** 2).mean())

# ---------- (2) inverse PINN ----------
zeta_obs = np.linspace(0.3, ZMAX, 8)
inv = []
for seed in range(5):
    rng = np.random.default_rng(seed)
    s_obs = exact(zeta_obs, LAM_TRUE) * (1 + 0.03 * rng.standard_normal(zeta_obs.size))
    torch.manual_seed(100 + seed)
    m = mlp(1, 24, 3)
    raw = torch.nn.Parameter(torch.tensor(-2.0))                          # lambda = softplus(raw), starts ~0.13
    o = torch.optim.Adam(list(m.parameters()) + [raw], lr=3e-3)
    zo = torch.tensor(zeta_obs[:, None], dtype=torch.float32)
    so = torch.tensor(s_obs[:, None], dtype=torch.float32)
    lam_hist = []
    for it in range(3000):
        lam = torch.nn.functional.softplus(raw)
        z = (torch.rand(256, 1) * ZMAX).requires_grad_(True)
        s = z * m(z / ZMAX)
        ds = torch.autograd.grad(s.sum(), z, create_graph=True)[0]
        l_pde = ((ds - 1 + 4 * lam * s) ** 2).mean()
        l_dat = ((zo * m(zo / ZMAX) - so) ** 2).mean() / (so ** 2).mean()
        loss = l_pde + 10 * l_dat
        o.zero_grad(); loss.backward(); o.step()
        if it % 50 == 0:
            lam_hist.append(float(lam))
    with torch.no_grad():
        s_fit = (torch.tensor(zg[:, None], dtype=torch.float32) * m(torch.tensor(zg[:, None] / ZMAX, dtype=torch.float32))).numpy()[:, 0]
    # least-squares fit of the exact solution to the same data, for reference
    lam_grid = np.linspace(0.02, 0.8, 4000)
    lam_ls = lam_grid[np.argmin([((exact(zeta_obs, l) - s_obs) ** 2).sum() for l in lam_grid])]
    inv.append({"seed": seed, "lambda_pinn": float(torch.nn.functional.softplus(raw)), "lambda_lsq_exact": float(lam_ls),
                "lam_hist": lam_hist, "s_obs": s_obs.tolist(), "s_fit": s_fit.tolist()})
wall = time.time() - t0
lp = np.array([d["lambda_pinn"] for d in inv]); ll = np.array([d["lambda_lsq_exact"] for d in inv])

# ---------- figure ----------
fig, ax = plt.subplots(1, 3, figsize=(15, 4.6))
for lam, c in zip([0.05, 0.2, 0.5], ["C0", "C1", "C2"]):
    i = np.argmin(np.abs(lg - lam))
    ax[0].plot(zg * D * 1e3, se[i] * SIG0, "-", color=c, lw=2.5, alpha=0.5, label=f"exact, K$\\mu_w$ = {lg[i]:.2f}")
    ax[0].plot(zg * D * 1e3, sp[i] * SIG0, "--", color=c, lw=1.2, label=f"PINN surrogate, K$\\mu_w$ = {lg[i]:.2f}")
ax[0].set_xlabel("depth below powder surface z (mm)"); ax[0].set_ylabel("vertical stress $\\sigma_v$ (Pa)")
ax[0].set_title(f"(1) parametric PINN, no data: max error {100 * rel_err:.2f} % of max stress")
ax[0].legend(fontsize=7)
ax[1].semilogy(*zip(*fwd_log), label="forward PINN residual loss")
for d in inv[:1]:
    ax[1].plot(np.arange(len(d["lam_hist"])) * 50, np.abs(np.array(d["lam_hist"]) - LAM_TRUE) / LAM_TRUE, label="inverse: |$\\lambda$ - true| / true (seed 0)")
ax[1].set_xlabel("Adam iteration"); ax[1].set_ylabel("loss (-) / relative error (-)")
ax[1].set_title("training"); ax[1].legend(fontsize=8)
for d in inv:
    ax[2].plot(zeta_obs * D * 1e3, np.array(d["s_obs"]) * SIG0, "o", ms=4, alpha=0.6)
    ax[2].plot(zg * D * 1e3, np.array(d["s_fit"]) * SIG0, "-", lw=0.8, alpha=0.7)
ax[2].plot(zg * D * 1e3, exact(zg, LAM_TRUE) * SIG0, "k--", lw=1.5, label=f"truth, K$\\mu_w$ = {LAM_TRUE}")
ax[2].set_xlabel("depth below powder surface z (mm)"); ax[2].set_ylabel("vertical stress $\\sigma_v$ (Pa)")
ax[2].set_title(f"(2) inverse PINN, 8 readings, 3 % noise, 5 seeds:\nK$\\mu_w$ = {lp.mean():.3f} $\\pm$ {lp.std():.3f} (truth {LAM_TRUE})")
ax[2].legend(fontsize=8)
fig.suptitle("surrogate-pinn: PyTorch %s PINNs for the Janssen stress in the powder column above the auger "
             "(D = 20.9 mm, $\\rho_b$ = 1256 kg/m$^3$)" % torch.__version__, fontsize=11)
fig.tight_layout()
fig.savefig(os.path.join(OUT, "pinn_janssen.png"), dpi=100)

res = {"id": "surrogate-pinn",
       "method": "Physics-informed neural networks for the Janssen powder-column stress: parametric forward "
                 "surrogate over K*mu_w and inverse inference of K*mu_w from noisy stress readings",
       "code": "self-written PyTorch PINN (run.py)", "version": f"torch {torch.__version__}",
       "status": "ran", "wall_s": round(wall, 1), "cores": 1,
       "key_results": {"forward_max_abs_err_over_max_stress": round(float(rel_err), 5),
                       "forward_rel_L2_err": round(float(rel_err_l2), 5),
                       "forward_train_s": round(fwd_s, 1), "forward_iterations": 4500,
                       "lambda_true": LAM_TRUE,
                       "inverse_lambda_pinn_per_seed": np.round(lp, 4).tolist(),
                       "inverse_lambda_pinn_mean_sd": [round(float(lp.mean()), 4), round(float(lp.std()), 4)],
                       "inverse_lambda_exact_lsq_per_seed": np.round(ll, 4).tolist(),
                       "noise": "3 % multiplicative, 8 readings at z = 6-63 mm",
                       "stress_scale_Pa_per_unit_s": round(SIG0, 2),
                       "sigma_v_at_63mm_true_Pa": round(float(exact(ZMAX, LAM_TRUE) * SIG0), 2)},
       "notes": "Janssen ODE is a 1D continuum stand-in for the hopper/inlet stress, not a doser model; the PINN is "
                "compared with the closed-form solution and with a least-squares fit of that solution to the same data."}
with open(os.path.join(OUT, "result.json"), "w") as f:
    json.dump(res, f, indent=1)
print(json.dumps(res["key_results"], indent=1)); print("wall", wall)
