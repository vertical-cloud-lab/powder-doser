"""mc-packing: Monte Carlo / geometric packing of polydisperse sphere PSDs.

Usage:  python run.py [sim|plot|anim|all]   (default: all)
Bulky outputs go to /tmp/sims-scratch/mc-packing; the PNG, GIF, MP4 and
result.json are written next to this script.
"""
import json
import math
import os
import sys
import time

os.environ.setdefault("NUMBA_NUM_THREADS", "1")
os.environ.setdefault("OMP_NUM_THREADS", "1")
import numpy as np  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import packing_kernels as pk  # noqa: E402

SCR = "/tmp/sims-scratch/mc-packing"
os.makedirs(SCR, exist_ok=True)

# ------------------------------------------------------------------ PSDs
# lengths are in units of d_ref (salt: d50 = 0.425 mm; AlSi10Mg: volume d50 = 35 um)
SIG_AM = math.asinh(0.5) / 1.2815516   # log-normal sigma giving span (d90-d10)/d50 = 1
PSD = {
    "mono": dict(kind=0, p=(0.5, 0, 0, 0), dmax=1.0, d_ref_um=None,
                 rho_s=None, label="monodisperse (validation)"),
    "salt": dict(kind=1, p=(0.36 / 0.425, 0.49 / 0.425, 0, 0), dmax=0.49 / 0.425,
                 d_ref_um=425.0, rho_s=2165.0,
                 label="NaCl: uniform 0.36-0.49 mm (number), d50 0.425 mm"),
    "alsi10mg": dict(kind=2, p=(math.exp(-3 * SIG_AM ** 2), SIG_AM,
                                math.exp(-2.5 * SIG_AM), math.exp(2.5 * SIG_AM)),
                     dmax=math.exp(2.5 * SIG_AM), d_ref_um=35.0, rho_s=2670.0,
                     label="AlSi10Mg: log-normal, volume d50 35 um, span 1"),
}


def sample_diam(name, n, seed):
    rng = np.random.default_rng(seed)
    P = PSD[name]
    k, (p1, p2, p3, p4) = P["kind"], P["p"]
    if k == 0:
        return np.full(n, 2 * p1)
    if k == 1:
        return rng.uniform(p1, p2, n)
    out = np.empty(0)
    while out.size < n:
        d = p1 * np.exp(p2 * rng.standard_normal(2 * n))
        out = np.concatenate([out, d[(d >= p3) & (d <= p4)]])
    return out[:n]


def vol_percentiles(d):
    s = np.sort(d)
    w = np.cumsum(s ** 3)
    w /= w[-1]
    return [float(np.interp(q, w, s)) for q in (0.1, 0.5, 0.9)]


# ----------------------------------------------------------- simulations
def measure_bed(pos, rad, L, dmax):
    H = pk.surface_map(pos, rad, L, 48)
    zlo = 3.0 * dmax
    zhi = float(np.percentile(H, 10)) - 2.0 * dmax
    phi = pk.slab_fraction(pos, rad, L, zlo, zhi) if zhi > zlo + dmax else float("nan")
    zb = np.arange(0.0, float(H.max()) + 0.5, 0.25)
    prof = np.array([pk.slab_fraction(pos, rad, L, a, a + 0.25) for a in zb])
    return phi, zlo, zhi, float(H.mean()), float(H.std()), zb, prof


def run_sims():
    res = {"rsa": {}, "deposit": {}, "compress": {}}
    t_all = time.time()
    # warm-up compile on tiny problems
    pk.deposit(np.full(50, 0.5), 6.0, 0.0, 1, 64, 300)
    pk.rsa_run(0, 0.5, 0, 0, 0, 0.5, 6.0, 1000, np.array([1000], np.int64), 1, 64)
    pk.compress(np.full(200, 0.5), 0.3, 1, 0.02, 1e-2, 50, 1e-3, 64, 2)
    pk.max_overlap(np.zeros((2, 3)), np.ones(2), 5.0, False)

    # ---------------- RSA (fully periodic cube, sizes drawn per attempt)
    n_att = int(float(os.environ.get("RSA_ATT", "1e7")))
    ck = np.unique(np.logspace(3, math.log10(n_att), 40).astype(np.int64))
    for name in ("mono", "salt", "alsi10mg"):
        P = PSD[name]
        L = 12.0
        t0 = time.time()
        pos, rad, hist, ovf = pk.rsa_run(P["kind"], *P["p"], P["dmax"] / 2, L, n_att, ck, 11, 512)
        dt = time.time() - t0
        mo = pk.max_overlap(pos, rad, L, True)
        # Feder-type extrapolation phi(n) = phi_inf - A n^(-1/3) over the last decade
        sel = ck >= ck[-1] / 10
        X = np.vstack([np.ones(sel.sum()), ck[sel] ** (-1.0 / 3.0)]).T
        coef = np.linalg.lstsq(X, hist[sel], rcond=None)[0]
        res["rsa"][name] = dict(phi=float(hist[-1]), phi_extrap=float(coef[0]), n_att=n_att,
                                N_accepted=int(rad.size), mean_d_accepted=float(2 * rad.mean()),
                                L=L, wall_s=dt, max_rel_overlap=float(mo), cap_overflow=int(ovf))
        np.savez_compressed(f"{SCR}/rsa_{name}.npz", pos=pos, rad=rad, hist=hist, ck=ck)
        print("RSA", name, res["rsa"][name], flush=True)

    # ---------------- deposition with stickiness knob
    cfg = {"mono": (4000, 12.0, [0.0, 1.0]),
           "salt": (4000, 12.0, [0.0, 0.1, 0.25, 0.5, 0.75, 1.0]),
           "alsi10mg": (8000, 12.0, [0.0, 0.1, 0.25, 0.5, 0.75, 1.0])}
    for name, (N, L, plist) in cfg.items():
        P = PSD[name]
        d = sample_diam(name, N, 7)
        rad = 0.5 * d
        res["deposit"][name] = {"N": N, "L": L, "d_vol_10_50_90": vol_percentiles(d), "runs": {}}
        for ps in plist:
            t0 = time.time()
            pos, ncon, stuck, ovf = pk.deposit(rad, L, ps, 3, 512, 400)
            dt = time.time() - t0
            mo = pk.max_overlap(pos, rad, L, False)
            phi, zlo, zhi, Hm, Hs, zb, prof = measure_bed(pos, rad, L, P["dmax"])
            ok = ncon[ncon > 0]
            r = dict(p_stick=ps, phi=float(phi), z_window=[zlo, zhi], H_mean=Hm, H_std=Hs,
                     wall_s=dt, stuck=int(stuck), cap_overflow=int(ovf),
                     max_rel_overlap=float(mo),
                     mean_support_contacts=float(ok.mean()) if ok.size else float("nan"))
            res["deposit"][name]["runs"][str(ps)] = r
            np.savez_compressed(f"{SCR}/dep_{name}_p{ps}.npz", pos=pos, rad=rad, ncon=ncon, zb=zb,
                                prof=prof, L=L)
            print("DEP", name, r, flush=True)

    # ---------------- force-biased compression (fully periodic cube)
    for name in ("mono", "salt", "alsi10mg"):
        d = sample_diam(name, 2000, 5)
        t0 = time.time()
        pos, a, L, phiJ, phis, its, snaps, snap_s = pk.compress(0.5 * d, 0.45, 9, 0.01, 1e-4,
                                                                4000, 2e-4, 512, 40)
        dt = time.time() - t0
        mo = pk.max_overlap(pos, a, L, True)
        res["compress"][name] = dict(phi=float(phiJ), N=2000, L=float(L), growth_steps=int(phis.size),
                                     wall_s=dt, max_rel_overlap=float(mo),
                                     d_vol_10_50_90=vol_percentiles(d))
        np.savez_compressed(f"{SCR}/cmp_{name}.npz", pos=pos, a=a, L=L, phis=phis, its=its)
        print("CMP", name, res["compress"][name], flush=True)
    res["wall_s_total"] = time.time() - t_all
    with open(f"{SCR}/raw_results.json", "w") as f:
        json.dump(res, f, indent=1)
    return res


if __name__ == "__main__":
    stage = sys.argv[1] if len(sys.argv) > 1 else "all"
    if stage in ("sim", "all"):
        run_sims()
    t0 = time.time()
    if stage in ("plot", "all"):
        import plots
        plots.main()
    if stage in ("anim", "all"):
        import plots
        plots.animate()
    if stage in ("plot", "anim", "all", "result"):
        import plots
        plots.write_result(extra_wall=time.time() - t0)
