"""Angle of repose (ISO 4324 style, reduced scale) with LIGGGHTS-PUBLIC 3.8.

Salt grains rain from a 3 mm wide insertion stream onto a fixed 12 mm diameter base disk;
grains that roll off the edge leave the box. The repose angle is read off the final heap.

usage: python run.py VARIANT [--analyze-only]   VARIANT = dry | coh | cap_low | cap_high
"""
import argparse
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import ligcommon as L  # noqa: E402

SCRATCH = os.environ.get("SCRATCH", "/tmp/sims-scratch/dem-liggghts-aor")
R_BASE = 6.0e-3          # base radius (m): 12 mm disk, about 28 mean grain diameters
N_POUR = 4000            # grains poured
RATE = 8000              # grains/s
T_SETTLE = 0.35          # s after pouring ends

# liquid-bridge (capillary) settings for the moisture variants (easo/capillary/viscous)
CAP = {
    "cap_low": 0.5,    # initial surface liquid content, % of particle volume
    "cap_high": 2.0,
}


def disk_stl(path, R, z, n=96):
    with open(path, "w") as f:
        f.write("solid base\n")
        for i in range(n):
            a0, a1 = 2 * math.pi * i / n, 2 * math.pi * (i + 1) / n
            p = [(0, 0, z), (R * math.cos(a0), R * math.sin(a0), z), (R * math.cos(a1), R * math.sin(a1), z)]
            f.write("facet normal 0 0 1\nouter loop\n")
            for q in p:
                f.write(f"vertex {q[0]:.6e} {q[1]:.6e} {q[2]:.6e}\n")
            f.write("endloop\nendfacet\n")
        f.write("endsolid base\n")


def build(variant, wd):
    os.makedirs(os.path.join(wd, "dump"), exist_ok=True)
    disk_stl(os.path.join(wd, "base.stl"), R_BASE, 0.0)
    ced = L.CED_COHESIVE if variant == "coh" else 0.0
    extra = ""
    pair_coh = None
    if variant in CAP:
        pair_coh = "easo/capillary/viscous"
        extra = (
            "fix m7 all property/global surfaceTension scalar 0.072\n"
            "fix m8 all property/global fluidViscosity scalar 0.001\n"
            "fix m9 all property/global contactAngle peratomtype 20.0 20.0\n"  # degrees (LIGGGHTS checks 0 <= contactAngle <= 180)
            "fix m10 all property/global maxSeparationDistanceRatio scalar 1.1\n"
            "fix m11 all property/global minSeparationDistanceRatio scalar 1.01\n"
            f"fix m12 all property/global surfaceLiquidContentInitial scalar {CAP[variant]}\n"
        )
    box = (-9e-3, 9e-3, -9e-3, 9e-3, -3e-3, 16e-3)
    head, wall_model, dt = L.header(box, ced=ced, extra_pp_props=extra, pair_cohesion=pair_coh)
    steps = lambda s: int(round(s / dt))  # noqa: E731
    t_pour = N_POUR / RATE
    ins_every = steps(0.01)
    liq = ""
    deck = head + f"""
fix base all mesh/surface file base.stl type 2
fix walls all wall/gran {wall_model} mesh n_meshes 1 meshes base
region pour cylinder z 0. 0. 1.5e-3 1.0e-2 1.4e-2 units box
fix ins all insert/rate/region seed 86028157 distributiontemplate pdd nparticles {N_POUR} particlerate {RATE} insert_every {ins_every} overlapcheck yes all_in yes vel constant 0. 0. -0.1 region pour ntry_mc 5000
fix integr all nve/sphere
variable t equal time
variable n equal atoms
thermo_style custom step time atoms ke
thermo {steps(0.05)}
thermo_modify lost ignore norm no flush yes
fix logn all print {steps(0.01)} "${{t}} ${{n}}" file natoms.txt screen no
dump dmp all custom {steps(0.025)} dump/p.*.txt id type radius x y z vx vy vz
run {steps(t_pour + T_SETTLE)}
"""
    deck = deck.replace("fix integr all nve/sphere", liq + "fix integr all nve/sphere") if liq else deck
    with open(os.path.join(wd, "in.aor"), "w") as f:
        f.write(deck)
    return dt


def heap_profile(d, nbins=15, nsect=8):
    x, y, z, r = d["x"], d["y"], d["z"], d["radius"]
    rr = np.hypot(x, y)
    keep = (z > -0.5e-3) & (rr < R_BASE + 0.5e-3)
    x, y, z, r, rr = x[keep], y[keep], z[keep], r[keep], rr[keep]
    top = z + r
    edges = np.linspace(0, R_BASE, nbins + 1)
    th = np.arctan2(y, x)
    sect = ((th + math.pi) / (2 * math.pi) * nsect).astype(int) % nsect
    prof = np.full((nsect, nbins), np.nan)
    for s in range(nsect):
        for b in range(nbins):
            m = (sect == s) & (rr >= edges[b]) & (rr < edges[b + 1])
            if m.any():
                prof[s, b] = top[m].max()
    rc = 0.5 * (edges[1:] + edges[:-1])
    h = np.nanmean(prof, axis=0)
    hs = np.nanstd(prof, axis=0)
    fit = (rc > 1.0e-3) & (rc < 5.2e-3) & np.isfinite(h)
    p = np.polyfit(rc[fit], h[fit], 1)
    angle_fit = math.degrees(math.atan(-p[0]))
    # per-sector fits for a scatter estimate
    angs = []
    for s in range(nsect):
        ok = fit & np.isfinite(prof[s])
        if ok.sum() > 4:
            angs.append(math.degrees(math.atan(-np.polyfit(rc[ok], prof[s, ok], 1)[0])))
    H = top[rr < 1.0e-3].max() if (rr < 1.0e-3).any() else float("nan")
    angle_iso = math.degrees(math.atan(H / R_BASE))
    return dict(r_mm=(rc * 1e3).tolist(), h_mm=(h * 1e3).tolist(), h_std_mm=(hs * 1e3).tolist(),
                fit=[float(p[0]), float(p[1])], angle_fit_deg=angle_fit,
                angle_fit_sector_std_deg=float(np.std(angs)) if angs else None,
                apex_height_mm=float(H * 1e3), angle_iso_deg=angle_iso, n_on_base=int(keep.sum()))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("variant")
    ap.add_argument("--analyze-only", action="store_true")
    a = ap.parse_args()
    wd = os.path.join(SCRATCH, a.variant)
    os.makedirs(wd, exist_ok=True)
    dt = build(a.variant, wd)
    res = {"variant": a.variant, "dt": dt}
    if not a.analyze_only:
        rc, wall, tail = L.run_liggghts(wd, "in.aor")
        res.update(rc=rc, wall_s=wall)
        if rc != 0:
            res["error_tail"] = tail[-2500:]
            L.write_json(os.path.join(wd, "run.json"), res)
            print(tail[-2500:])
            sys.exit(rc)
    else:
        old = os.path.join(wd, "run.json")
        if os.path.exists(old):
            import json
            res.update({k: v for k, v in json.load(open(old)).items() if k in ("rc", "wall_s")})
    files = L.dump_series(os.path.join(wd, "dump", "p.*.txt"))
    step, d = L.read_dump(files[-1])
    res.update(heap_profile(d))
    res["n_poured"] = N_POUR
    res["n_dumps"] = len(files)
    L.write_json(os.path.join(wd, "run.json"), res)
    print({k: res[k] for k in ("variant", "angle_fit_deg", "angle_iso_deg", "apex_height_mm", "n_on_base")})


if __name__ == "__main__":
    main()
