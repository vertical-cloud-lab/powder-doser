"""DEM doser emulator along a one-dimensional flowability path (the PR #180 twin at protocol C conditions).

Every case is the #180 rig twin: CAD cone exit, core tip inside the 3 mm hole, 1.5 flight turns meshed,
about 29 k salt-sized grains (0.361/0.425/0.489 mm) at salt's particle density, 30 rpm (battery protocol C),
0.12 s settle with the exit plugged, then 0.75 revolution. Only the contact parameters move along the path:

    P0     "smooth"  mu_pp 0.3, mu_roll 0.1, k = 0       (spherical, low-friction grains)
    P1     "salt"    mu_pp 0.5, mu_roll 0.3, k = 0       (the #180 twin, validated on salt)
    kNNNN  salt friction plus SJKR cohesion energy density k = NNNN J/m3 (grain-grain and grain-auger)

The grains are the same size for every point, so a powder enters only through where its angle of repose puts
it on the path (see aor_path.py and predict.py). The time step is 0.3 of the Rayleigh time of the smallest
grain (#180 used 0.2), to fit eight cases into the session.

usage:
    python doser_path.py list
    python doser_path.py run CASE [CASE ...]      # serially; launch several processes for parallel cases
    python doser_path.py summarize                 # -> doser_path.json
"""
from __future__ import annotations

import json
import math
import os
import subprocess
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
SCRATCH = os.environ.get("SCRATCH", "/tmp/sims-scratch/heldout-powders")
PY = sys.executable

GEOMETRY = {  # identical to rig_t27p5_r60 in PR #180 (and ../dem-liggghts-auger-short)
    "bore_r": 10.45, "core_r": 3.98, "shaft_r": 3.98, "pitch": 10.4, "flight_t": 0.5, "n_turns": 1.5,
    "funnel_h": 12.0, "exit_r": 1.5, "funnel_top_r": 10.45, "tip_r": 0.43, "flight_into_funnel": True,
    "throat_h": 0.0, "feed_h": 5.0,
}
BASE = {
    "geometry": GEOMETRY, "d_mean_mm": 0.425, "d_spread": 0.15, "density": 2165.0, "youngs": 2.0e5,
    "poisson": 0.3, "restitution": 0.5, "mu_pp": 0.5, "mu_pw": 0.4, "mu_roll": 0.3, "ced": 0.0,
    "rpm": 30, "revs": 0.75, "settle_s": 0.12, "stop_s": 0.0, "log_every_s": 0.005,
    "dump_every_s": 0.05, "dump_start_s": 0.0, "np": 1, "fill_frac": 1.0, "fill_x_max_mm": -4.0,
    "feed": True, "seed": 12345, "mesh_format": "stl",
}
PATH = {  # path point -> contact parameters
    "P0": {"mu_pp": 0.3, "mu_roll": 0.1, "ced": 0.0},
    "P1": {"mu_pp": 0.5, "mu_roll": 0.3, "ced": 0.0},
    "k750": {"ced": 750.0},
    "k1500": {"ced": 1500.0},
    "k2250": {"ced": 2250.0},
    "k3000": {"ced": 3000.0},
    "k4500": {"ced": 4500.0},
    "k6000": {"ced": 6000.0},
}
CASES = {
    "d45_P0": ("P0", 45.0), "d45_P1": ("P1", 45.0), "d45_k3000": ("k3000", 45.0),
    "d45_k4500": ("k4500", 45.0), "d45_k6000": ("k6000", 45.0),
    "d22_P1": ("P1", 22.5), "d22_k3000": ("k3000", 22.5), "d22_k4500": ("k4500", 22.5),
    # added after the first batch showed the 45 deg twin stalling already at k = 3000 J/m3
    "d45_k750": ("k750", 45.0), "d45_k1500": ("k1500", 45.0), "d45_k2250": ("k2250", 45.0),
    "d22_k750": ("k750", 22.5), "d22_k1500": ("k1500", 22.5),
    # speed check against protocol D (22.5 deg, 15/45/90 rpm): the same points at 90 rpm
    "d22_P1_r90": ("P1", 22.5, 90), "d22_k750_r90": ("k750", 22.5, 90),
}


def rayleigh_dt(d, rho, E, nu):
    G = E / (2 * (1 + nu))
    return math.pi * (d / 2) * math.sqrt(rho / G) / (0.1631 * nu + 0.8766)


def config(case):
    point, tilt, *rest = CASES[case]
    cfg = {**BASE, **PATH[point], "name": case, "incline_deg": tilt, "rpm": rest[0] if rest else BASE["rpm"]}
    dmin = cfg["d_mean_mm"] * (1 - cfg["d_spread"]) * 1e-3
    cfg["dt"] = 0.3 * rayleigh_dt(dmin, cfg["density"], cfg["youngs"], cfg["poisson"])
    return cfg


def run(case):
    wd = os.path.join(SCRATCH, case)
    os.makedirs(wd, exist_ok=True)
    cfg = config(case)
    path = os.path.join(wd, "config.json")
    with open(path, "w") as f:
        json.dump(cfg, f, indent=1)
    env = dict(os.environ, OMP_NUM_THREADS="1")
    p = subprocess.run([PY, os.path.join(HERE, "run_case.py"), path, "--workdir", wd], env=env,
                       capture_output=True, text=True)
    with open(os.path.join(wd, "driver.log"), "w") as f:
        f.write(p.stdout + "\n" + p.stderr)
    return p.returncode


def summarize_case(case):
    wd = os.path.join(SCRATCH, case)
    meta = json.load(open(os.path.join(wd, "case.json")))
    A = np.loadtxt(os.path.join(wd, "outflow.txt"), ndmin=2)
    t, m, n = A[:, 0], A[:, 1] * 1e6, A[:, 2]
    T, t0 = meta["period_s"], meta["settle_s"]
    revs_done = max(0.0, (t[-1] - t0) / T)
    point, tilt, *_ = CASES[case]
    out = {"case": case, "path_point": point, "tilt_deg": tilt, "rpm": meta["cfg"]["rpm"],
           "params": {k: meta["cfg"][k] for k in ("mu_pp", "mu_pw", "mu_roll", "ced")},
           "dt_s": meta["dt"], "n_init": meta["n_init"], "wall_s": meta.get("wall_s"),
           "revs_simulated": round(revs_done, 3), "mg_leaked_settle": round(float(np.interp(t0, t, m)), 3)}
    # mass in eighth-revolution sectors after the exit opens
    k_max = int(math.floor(revs_done * 8 + 1e-6))
    edges = t0 + T * np.arange(k_max + 1) / 8
    sect = np.diff(np.interp(edges, t, m))
    out["sector_mg"] = [round(float(s), 3) for s in sect]
    m_open = float(np.interp(t0, t, m))
    out["mg_total_after_open"] = round(float(m[-1] - m_open), 3)
    out["grains_total_after_open"] = int(n[-1] - np.interp(t0, t, n))
    if revs_done > 0.05:
        out["mg_per_rev_whole"] = round(out["mg_total_after_open"] / revs_done, 2)
    # steady window: drop the first quarter revolution (start-up transient, as in #180)
    if revs_done >= 0.5:
        a = t0 + 0.25 * T
        out["mg_per_rev_after_quarter"] = round(float(m[-1] - np.interp(a, t, m)) / (revs_done - 0.25), 2)
    elif revs_done >= 0.2:
        # stalled cases stopped early to free a core: rate after the opening burst (first 0.1 rev)
        a = t0 + 0.1 * T
        out["mg_per_rev_after_burst"] = round(float(m[-1] - np.interp(a, t, m)) / (revs_done - 0.1), 2)
        out["stopped_early"] = True
    else:
        out["stopped_early"] = True
    return out


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "list"
    if cmd == "list":
        print("\n".join(CASES))
    elif cmd == "run":
        rc = 0
        for c in sys.argv[2:]:
            rc |= run(c)
        sys.exit(rc)
    elif cmd == "summarize":
        res = []
        for c in CASES:
            if os.path.exists(os.path.join(SCRATCH, c, "outflow.txt")) and \
                    os.path.exists(os.path.join(SCRATCH, c, "case.json")):
                try:
                    res.append(summarize_case(c))
                except Exception as e:  # noqa: BLE001
                    res.append({"case": c, "error": repr(e)})
        with open(os.path.join(HERE, "doser_path.json"), "w") as f:
            json.dump(res, f, indent=1)
        for r in res:
            print({k: r.get(k) for k in ("case", "revs_simulated", "mg_per_rev_whole", "mg_per_rev_after_quarter")})


if __name__ == "__main__":
    main()
