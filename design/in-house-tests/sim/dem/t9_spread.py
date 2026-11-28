"""Test 9, blade spreading over the 100 x 30 mm coupon (SPEC.md section 9), LIGGGHTS-PUBLIC 3.8.

As designed: the doser lays a 0.5 g line across the coupon's start (here 0.167 g on a 10 mm wide strip,
periodic across the width, the same mass per width); a 1.5 mm thick blade (STL mesh) sweeps it at 50 mm/s
with its edge 0.2 mm above the coupon (flat wall, mu_wall 0.4). A second gap of 1.0 mm (2 x d90) shows
what a gap sized for the reference powder gives. Cohesive variant: SJKR between grains and between grains
and coupon / blade (6 kJ/m3).

usage: python t9_spread.py run|analyze CASE     CASE = g0.2_dry | g0.2_coh | g1.0_dry | g1.0_coh
"""
import math
import os
import shutil
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import demlib as L  # noqa: E402

TEST = "t9_spread"
LY = 10e-3
COUPON = (0.0, 100e-3)
FEED_G_PER_30MM = 0.5
V_BLADE = 0.05
X0_BLADE, X1_BLADE = -3e-3, 108e-3
T_BLADE = 1.5e-3


def parse(case):
    g, v = case.split("_")
    return float(g[1:]) * 1e-3, v


def build(case, wd):
    gap, var = parse(case)
    os.makedirs(os.path.join(wd, "dump"), exist_ok=True)
    ced = 0.0 if var == "dry" else L.CED_COH
    n = int(round(FEED_G_PER_30MM * 1e-3 * LY / 30e-3 / L.grain_mass_mean()))
    zt = 9e-3
    tris = []
    x0 = X0_BLADE
    for (a, b, c, d) in [((x0, 0, gap), (x0, LY, gap), (x0, LY, zt), (x0, 0, zt)),
                         ((x0, 0, gap), (x0 + T_BLADE, 0, gap), (x0 + T_BLADE, LY, gap), (x0, LY, gap))]:
        tris += [(a, b, c), (a, c, d)]
    L.write_stl(os.path.join(wd, "blade.stl"), tris, "blade")
    box = (-6e-3, 112e-3, 0.0, LY, -0.5e-3, 10e-3)
    head, wm, dt = L.header(box, periodic="f p f", ced=ced, cohesion_walls=(var == "coh"), ced_wall=ced)
    st = lambda s: max(1, int(round(s / dt)))  # noqa: E731
    t_move = (X1_BLADE - X0_BLADE) / V_BLADE
    deck = head + f"""
fix coupon all wall/gran {wm} primitive type 2 zplane 0.0
fix blade all mesh/surface file blade.stl type 2 curvature_tolerant yes
fix walls all wall/gran {wm} mesh n_meshes 1 meshes blade
region feed block 0.5e-3 7.5e-3 0. {LY:.5e} 0.3e-3 7.0e-3 units box
fix ins all insert/pack seed 86028157 distributiontemplate pdd insert_every once overlapcheck yes all_in yes particles_in_region {n} region feed ntry_mc 50000
fix integr all nve/sphere
thermo_style custom step time atoms ke
thermo {st(0.1)}
thermo_modify lost ignore norm no flush yes
run {st(0.25)}
dump dmp all custom {st(0.04)} dump/p.*.txt id radius x y z vx vy vz
fix mv all move/mesh mesh blade linear {V_BLADE} 0. 0.
run {st(t_move)}
unfix mv
run {st(0.05)}
write_dump all custom final.txt id radius x y z vx vy vz
"""
    with open(os.path.join(wd, "in.spread"), "w") as f:
        f.write(deck)
    return dict(dt=dt, n=n, gap=gap, t_move=t_move)


def layer_metrics(d, gap, x_lo, x_hi, binw=5e-3, px=20e-6):
    x, y, z, r = d["x"], d["y"], d["z"], d["radius"]
    out = []
    for a in np.arange(x_lo, x_hi - 1e-9, binw):
        b = a + binw
        m = (x >= a) & (x < b) & (z < 3e-3)
        vol = (4 / 3 * math.pi * r[m] ** 3).sum()
        # coverage: rasterised projected discs
        nx, ny = int(binw / px), int(LY / px)
        img = np.zeros((nx, ny), bool)
        for xi, yi, ri in zip(x[m], y[m], r[m]):
            i0, i1 = int((xi - ri - a) / px), int((xi + ri - a) / px) + 1
            j0, j1 = int((yi - ri) / px), int((yi + ri) / px) + 1
            ii = np.arange(max(i0, 0), min(i1, nx))
            jj = np.arange(j0, j1)
            if len(ii) == 0:
                continue
            X, Y = np.meshgrid(a + (ii + 0.5) * px, (jj + 0.5) * px, indexing="ij")
            inside = (X - xi) ** 2 + (Y - yi) ** 2 <= ri * ri
            img[np.ix_(ii, jj % ny)] |= inside
        out.append(dict(x_mm=(a + 0.5 * binw) * 1e3, n=int(m.sum()), areal_mass_g_m2=float(vol * L.SALT["density"] / (binw * LY) * 1e3),
                        phi_layer=float(vol / (binw * LY * max(gap, 1e-9))), coverage=float(img.mean())))
    return out


def analyze(case, wd, info):
    gap = info["gap"]
    fp = os.path.join(wd, "final.txt")
    _, d = L.read_dump(fp)
    bins = layer_metrics(d, gap, COUPON[0] + 10e-3, COUPON[1], binw=5e-3)
    cov = np.array([b["coverage"] for b in bins])
    phi = np.array([b["phi_layer"] for b in bins])
    am = np.array([b["areal_mass_g_m2"] for b in bins])
    covered = [b["x_mm"] for b in bins if b["coverage"] > 0.5]
    n_tot = info["n"]
    on_coupon = int(((d["x"] > COUPON[0] + 8e-3) & (d["x"] < COUPON[1]) & (d["z"] < 3e-3)).sum())
    pushed = int((d["x"] >= COUPON[1]).sum())
    under_gap_max = float((2 * d["radius"][(d["x"] > 10e-3) & (d["x"] < COUPON[1])]).max()) if on_coupon else None
    out = dict(case=case, gap_mm=gap * 1e3, n_grains=n_tot, feed_g_per_30mm=FEED_G_PER_30MM, strip_width_mm=LY * 1e3,
               grains_left_on_coupon=on_coupon, grains_pushed_off_end=pushed,
               coverage_mean=float(cov.mean()), coverage_first_20mm=float(cov[:4].mean()),
               phi_layer_mean_where_covered=float(phi[cov > 0.3].mean()) if (cov > 0.3).any() else 0.0,
               areal_mass_g_m2_mean=float(am.mean()), areal_mass_cv=float(am.std() / am.mean()) if am.mean() > 0 else None,
               covered_length_mm=float(max(covered) - min(covered) + 5) if covered else 0.0,
               largest_grain_left_mm=under_gap_max * 1e3 if under_gap_max else None, bins=bins)
    files = L.dump_series(os.path.join(wd, "dump", "p.*.txt"))
    if files:
        frames, ts = [], []
        for fpp in files:
            step, dd = L.read_dump(fpp)
            frames.append({k: dd[k] for k in ("id", "x", "y", "z", "radius")})
            ts.append(step * info["dt"])
        t0 = ts[0]
        bx = X0_BLADE + V_BLADE * np.clip(np.array(ts) - t0, 0, info["t_move"])
        out["frames_npz_bytes"] = L.save_frames(
            os.path.join(L.HERE, "frames", f"{TEST}_{case}.npz"), np.array(ts) - t0, frames, max_frames=70,
            extra=dict(blade_x_mm=(bx * 1e3).astype(np.float32), blade_gap_mm=np.float32(gap * 1e3),
                       blade_thickness_mm=np.float32(T_BLADE * 1e3), strip_width_mm=np.float32(LY * 1e3),
                       note=np.array("blade_x_mm is the blade's front face per frame (before decimation, 1 per "
                                     "0.04 s); periodic in y")))
    return out


def main():
    mode, case = sys.argv[1], sys.argv[2]
    wd = os.path.join(L.SCRATCH, TEST, case)
    os.makedirs(wd, exist_ok=True)
    info = build(case, wd)
    shutil.copy(os.path.join(wd, "in.spread"), os.path.join(L.HERE, "decks", f"in.{TEST}_{case}"))
    runinfo = L.read_json(os.path.join(wd, "run.json"), {})
    if mode == "run":
        rc, wall, tail = L.run_liggghts(wd, "in.spread")
        runinfo = dict(rc=rc, wall_s=wall)
        L.write_json(os.path.join(wd, "run.json"), runinfo)
        if rc != 0:
            print(tail)
            sys.exit(rc)
    res = analyze(case, wd, info)
    res.update(wall_s=runinfo.get("wall_s"), dt_s=info["dt"])
    L.write_json(os.path.join(L.HERE, "results", f"{TEST}_{case}.json"), res)
    print({k: res.get(k) for k in ("case", "coverage_mean", "phi_layer_mean_where_covered", "covered_length_mm",
                                   "grains_left_on_coupon", "largest_grain_left_mm", "wall_s")})


if __name__ == "__main__":
    main()
