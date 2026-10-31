"""Assemble result.json for the GNS run. Usage: python make_result.py SCRATCH_OUT DATA_DIR REPO_OUT GNS_COMMIT"""
import json
import os
import sys

SCR, DATA, OUT, COMMIT = sys.argv[1:5]
s = json.load(open(os.path.join(SCR, "train_summary.json")))
c = json.load(open(os.path.join(DATA, "cases.json")))
cases = {k: {kk: (round(vv, 4) if isinstance(vv, float) else vv) for kk, vv in v.items() if not isinstance(vv, list)}
         for k, v in s["cases"].items()}
res = {
    "id": "gns-gnn-simulator",
    "method": "Learned graph-network simulator (GNS, Sanchez-Gonzalez et al. 2020; Kumar & Vantassel 2023) trained "
              "on a self-generated 2D numba-DEM granular column-collapse dataset; rollout vs DEM on held-out columns",
    "code": "geoelements/gns LearnedSimulator (own training loop with the gns loss/noise) + self-written numba DEM",
    "version": f"gns commit {COMMIT}, torch 2.5.1+cpu, torch_geometric 2.6.1, torch_cluster 1.6.3",
    "status": "partial",
    "wall_s": round(c["wall_s"] + s["train_s"] + s["rollout_s"], 1),
    "cores": 1,
    "key_results": {
        "route": "self-generated dataset (no small pretrained 2D sand GNS model available; gns-sample has only "
                 "WaterDropSample data, no checkpoint)",
        "dataset": {"train": 40, "valid": 2, "test": 3, "frames": c["nframes"], "N_train_range": [36, 264],
                    "train_aspect_H_over_W_requested": [0.73, 2.39], "datagen_wall_s": round(c["wall_s"], 1)},
        "model": {"latent": s["latent"], "mlp_hidden": s["hidden"], "message_passing_steps": s["nmp"],
                  "connectivity_radius": s["R_conn"], "params": s["nparams"], "noise_std": s["noise_std"]},
        "training": {"steps": s["steps"], "train_s": round(s["train_s"], 1), "batch": "2 windows",
                     "lr": "1e-3 -> 1e-4 exponential"},
        "rollout_s_3_cases": round(s["rollout_s"], 1),
        "test_cases": cases,
    },
    "notes": "Reduced GNS (5 message-passing steps, latent 64) trained ~5000 steps on 1 CPU thread, versus ~1e6+ "
             "steps in the papers. Rollouts track the DEM for the two in-range columns (runout within -6 % and +20 % "
             "of the DEM runout distance) and blow up for the taller, out-of-range column (test_1, H/W 2.6).",
}
with open(os.path.join(OUT, "result.json"), "w") as f:
    json.dump(res, f, indent=1)
print(json.dumps(res["key_results"]["test_cases"], indent=1))
