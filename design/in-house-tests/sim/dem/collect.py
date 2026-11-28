"""Combine results/*.json into results.json (compact, per test). All values are simulated, not measured."""
import glob
import json
import os

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))


def load(name):
    p = os.path.join(HERE, "results", name + ".json")
    return json.load(open(p)) if os.path.exists(p) else None


def slim(r, drop=("series", "flank_angle_time_series", "silhouette_view0", "bins", "platen_series",
                  "final_vx_profile", "radius_profile_after_release_mm", "z_bins_mm")):
    return {k: v for k, v in r.items() if k not in drop} if r else None


def r3(x):
    if isinstance(x, float):
        return round(x, 4)
    if isinstance(x, dict):
        return {k: r3(v) for k, v in x.items()}
    if isinstance(x, list):
        return [r3(v) for v in x]
    return x


def heap_balance_stats(case, r):
    p = os.path.join(HERE, "results", f"t1_heap_{case}_heapmass.csv")
    if not os.path.exists(p):
        return {}
    A = np.loadtxt(p, delimiter=",", skiprows=1)
    t, m = A[:, 0], A[:, 3] * 1e3
    tp = r["t_pour_s"]
    tb = np.arange(0.1, t[-1], 0.1)
    inc = np.diff(np.interp(tb, t, m)) * 1e3
    sat = (tb[1:] > tp - 0.6) & (tb[1:] <= tp)
    post = tb[1:] > tp + 0.1
    return dict(balance_10Hz_increment_sd_mg_last_0p6s_of_feed=float(inc[sat].std()),
                balance_10Hz_largest_drop_mg_last_0p6s_of_feed=float(-inc[sat].min()),
                mass_change_after_feed_stops_mg=float((m[-1] - np.interp(tp, t, m)) * 1e3))


def main():
    out = {"note": "All numbers are DEM predictions (LIGGGHTS-PUBLIC 3.8.0), not measurements. Reference powders: "
                   "#196's real-size salt-like spheres, dry and SJKR-cohesive (k = 6 kJ/m3, Bo about 5).",
           "tests": {}}
    t1 = {}
    for c in ("d12_dry", "d12_coh", "d20_dry", "d20_coh", "d30_dry"):
        r = load(f"t1_heap_{c}")
        if r:
            s = slim(r)
            s.update(heap_balance_stats(c, r))
            t1[c] = s
    out["tests"]["1_heap"] = t1
    out["tests"]["7_drum"] = {c: slim(load(f"t7_drum_{c}")) for c in ("dry", "coh") if load(f"t7_drum_{c}")}
    out["tests"]["2_tap"] = {c: slim(load(f"t2_tap_{c}")) for c in ("dry", "coh") if load(f"t2_tap_{c}")}
    out["tests"]["5_orifice"] = {c: slim(load(f"t5_orifice_{c}")) for c in ("dry", "coh") if load(f"t5_orifice_{c}")}
    t3 = {}
    for p in sorted(glob.glob(os.path.join(HERE, "results", "t3_tilt_*.json"))):
        c = os.path.basename(p)[len("t3_tilt_"):-5]
        t3[c] = slim(load(f"t3_tilt_{c}"))
    out["tests"]["3_tilt"] = t3
    out["tests"]["8_ucs"] = {c: slim(load(f"t8_ucs_{c}")) for c in ("coh", "dry") if load(f"t8_ucs_{c}")}
    t9 = {}
    for p in sorted(glob.glob(os.path.join(HERE, "results", "t9_spread_*.json"))):
        c = os.path.basename(p)[len("t9_spread_"):-5]
        t9[c] = slim(load(f"t9_spread_{c}"))
    out["tests"]["9_spread"] = t9
    frames = sorted(os.path.basename(p) for p in glob.glob(os.path.join(HERE, "frames", "*.npz")))
    out["frames"] = {f: os.path.getsize(os.path.join(HERE, "frames", f)) for f in frames}
    with open(os.path.join(HERE, "results.json"), "w") as f:
        json.dump(r3(out), f, indent=1)
    # one result.json per test (all its variants), next to the per-run files
    for k, v in out["tests"].items():
        with open(os.path.join(HERE, "results", f"test{k}_result.json"), "w") as f:
            json.dump(r3(dict(test=k, note=out["note"], variants=v)), f, indent=1)
    print("tests:", {k: list(v.keys()) for k, v in out["tests"].items()})


if __name__ == "__main__":
    main()
