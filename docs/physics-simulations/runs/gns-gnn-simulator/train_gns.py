"""Train a reduced-size GNS (geoelements/gns LearnedSimulator, Sanchez-Gonzalez et al. 2020)
on the tiny numba-DEM column-collapse dataset, then roll out on held-out columns.

Usage: OMP_NUM_THREADS=1 python train_gns.py GNS_REPO DATA_DIR SCRATCH_OUT REPO_OUT TRAIN_SECONDS
"""
import json
import os
import sys
import time

import numpy as np
import torch

GNS_REPO, DATA, SCR, OUT, TBUDGET = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], float(sys.argv[5])
sys.path.insert(0, GNS_REPO)
from gns import learned_simulator, noise_utils  # noqa: E402

torch.set_num_threads(1)
torch.manual_seed(0)
rng = np.random.default_rng(0)
os.makedirs(SCR, exist_ok=True)
INPUT_LEN = 6
R_CONN = 0.035
LATENT, HIDDEN, NMP = 64, 64, 5
D_MEAN = 0.016


def load(split):
    z = np.load(os.path.join(DATA, f"{split}.npz"), allow_pickle=True)
    return {k: (z[k][0].astype(np.float32), z[k][1].astype(np.int64), z[k][2].astype(np.float32)) for k in z.files}


train, valid, test = load("train"), load("valid"), load("test")
vel = np.concatenate([np.diff(p, axis=0).reshape(-1, 2) for p, _, _ in train.values()])
acc = np.concatenate([np.diff(p, n=2, axis=0).reshape(-1, 2) for p, _, _ in train.values()])
vel_mean, vel_std = vel.mean(0), vel.std(0)
acc_mean, acc_std = acc.mean(0), acc.std(0)
NOISE = float(min(0.5 * vel_std.mean(), 5.0 * acc_std.mean()))
print("vel_std", vel_std, "acc_std", acc_std, "noise_std", NOISE, flush=True)
stats = {"acceleration": {"mean": torch.tensor(acc_mean), "std": torch.sqrt(torch.tensor(acc_std) ** 2 + NOISE ** 2)},
         "velocity": {"mean": torch.tensor(vel_mean), "std": torch.sqrt(torch.tensor(vel_std) ** 2 + NOISE ** 2)}}

sim = learned_simulator.LearnedSimulator(
    particle_dimensions=2, nnode_in=30, nedge_in=3, latent_dim=LATENT, nmessage_passing_steps=NMP,
    nmlp_layers=2, mlp_hidden_dim=HIDDEN, connectivity_radius=R_CONN,
    boundaries=np.array([[0.0, 1.0], [0.0, 1.0]]), normalization_stats=stats,
    nparticle_types=9, particle_type_embedding_size=16, device="cpu")
nparams = sum(p.numel() for p in sim.parameters())
opt = torch.optim.Adam(sim.parameters(), lr=1e-3)
keys = list(train.keys())


def sample_window():
    k = keys[rng.integers(len(keys))]
    pos, typ, _ = train[k]
    t = rng.integers(INPUT_LEN - 1, pos.shape[0] - 1)
    seq = torch.from_numpy(np.ascontiguousarray(pos[t - INPUT_LEN + 1:t + 1].transpose(1, 0, 2)))
    lab = torch.from_numpy(pos[t + 1])
    return seq, lab, torch.from_numpy(typ)


def rollout(pos, typ, nsteps=None):
    nsteps = nsteps or pos.shape[0] - INPUT_LEN
    cur = torch.from_numpy(np.ascontiguousarray(pos[:INPUT_LEN].transpose(1, 0, 2)))
    typ_t = torch.from_numpy(typ)
    n = torch.tensor([pos.shape[1]])
    preds = []
    with torch.no_grad():
        for _ in range(nsteps):
            nxt = sim.predict_positions(cur, nparticles_per_example=n, particle_types=typ_t)
            nxt = torch.clamp(nxt, 0.0, 1.0)
            preds.append(nxt.numpy())
            cur = torch.cat([cur[:, 1:], nxt[:, None, :]], dim=1)
    return np.concatenate([pos[:INPUT_LEN], np.array(preds)], axis=0)


def one_step_val():
    errs = []
    with torch.no_grad():
        for pos, typ, _ in valid.values():
            for t in range(INPUT_LEN - 1, pos.shape[0] - 1, 7):
                seq = torch.from_numpy(np.ascontiguousarray(pos[t - INPUT_LEN + 1:t + 1].transpose(1, 0, 2)))
                pred = sim.predict_positions(seq, torch.tensor([pos.shape[1]]), torch.from_numpy(typ))
                errs.append(float(((pred.numpy() - pos[t + 1]) ** 2).sum(-1).mean()))
    return float(np.mean(errs))


t0 = time.time()
step, log = 0, []
lr0, lr1 = 1e-3, 1e-4
while time.time() - t0 < TBUDGET:
    frac = (time.time() - t0) / TBUDGET
    for g in opt.param_groups:
        g["lr"] = lr0 * (lr1 / lr0) ** frac
    seqs, labs, typs, ns = [], [], [], []
    for _ in range(2):
        s, l, ty = sample_window()
        seqs.append(s); labs.append(l); typs.append(ty); ns.append(s.shape[0])
    seq = torch.cat(seqs); lab = torch.cat(labs); typ = torch.cat(typs); n = torch.tensor(ns)
    noise = noise_utils.get_random_walk_noise_for_position_sequence(seq, noise_std_last_step=NOISE)
    pred_acc, tgt_acc = sim.predict_accelerations(next_positions=lab, position_sequence_noise=noise,
                                                  position_sequence=seq, nparticles_per_example=n,
                                                  particle_types=typ)
    loss = ((pred_acc - tgt_acc) ** 2).sum(-1).mean()
    opt.zero_grad(); loss.backward(); opt.step()
    step += 1
    if step % 250 == 0:
        entry = {"step": step, "t": round(time.time() - t0, 1), "loss": float(loss)}
        if step % 1000 == 0:
            entry["val_onestep_mse"] = one_step_val()
        log.append(entry)
        print(entry, flush=True)
train_s = time.time() - t0
torch.save(sim.state_dict(), os.path.join(SCR, "gns_collapse.pt"))

# ---------- rollouts on held-out cases ----------
t1 = time.time()
res_cases = {}
for k, (pos, typ, r) in test.items():
    pr = rollout(pos, typ)
    err = np.sqrt(((pr - pos) ** 2).sum(-1).mean(-1))           # RMS position error per step
    run_true = np.percentile(pos[:, :, 0], 99.5, axis=1)
    run_pred = np.percentile(pr[:, :, 0], 99.5, axis=1)
    hgt_true = np.percentile(pos[:, :, 1], 99.5, axis=1)
    hgt_pred = np.percentile(pr[:, :, 1], 99.5, axis=1)
    np.savez_compressed(os.path.join(SCR, f"rollout_{k}.npz"), pred=pr, true=pos, r=r)
    res_cases[k] = {"N": int(pos.shape[1]), "W": float(pos[0, :, 0].max()), "H0": float(hgt_true[0]),
                    "rms_err_final_over_d": float(err[-1] / D_MEAN),
                    "rms_err_mid_over_d": float(err[len(err) // 2] / D_MEAN),
                    "runout_true_final": float(run_true[-1]), "runout_gns_final": float(run_pred[-1]),
                    "runout_rel_err": float((run_pred[-1] - run_true[-1]) / (run_true[-1] - run_true[0])),
                    "height_true_final": float(hgt_true[-1]), "height_gns_final": float(hgt_pred[-1]),
                    "err_curve_over_d": (err / D_MEAN).round(3).tolist(),
                    "runout_true": run_true.round(4).tolist(), "runout_gns": run_pred.round(4).tolist()}
    print(k, {kk: v for kk, v in res_cases[k].items() if not isinstance(v, list)}, flush=True)
roll_s = time.time() - t1
with open(os.path.join(SCR, "train_summary.json"), "w") as f:
    json.dump({"train_s": train_s, "rollout_s": roll_s, "steps": step, "nparams": nparams, "noise_std": NOISE,
               "log": log, "cases": res_cases, "R_conn": R_CONN, "latent": LATENT, "hidden": HIDDEN, "nmp": NMP,
               "vel_std": vel_std.tolist(), "acc_std": acc_std.tolist()}, f, indent=1)
print("train_s", train_s, "steps", step, "rollout_s", roll_s, "nparams", nparams)
