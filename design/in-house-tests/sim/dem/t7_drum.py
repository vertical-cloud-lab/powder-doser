"""Test 7, rotating drum (SPEC.md section 7), LIGGGHTS-PUBLIC 3.8.

As designed: 40 mm inner diameter, 24 axial ribs 0.8 mm tall (1.0 mm wide) on the wall, 40 % fill by
volume, turned at 20, then 5, then 2 rpm (one continuous run, speeds stepped down so each speed starts
from a bed already at its dynamic angle). The drum is a 2.13 mm (5 d50) slice, periodic along its axis,
so there are no end walls. The ribbed wall is a rotating STL mesh (PLA, mu_wall 0.4).

usage: python t7_drum.py run|analyze CASE     CASE = dry | coh
"""
import math
import os
import shutil
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import demlib as L  # noqa: E402

TEST = "t7_drum"
R = 20e-3
LY = 2.13e-3
NRIB, HRIB, WRIB = 24, 0.8e-3, 1.0e-3
FILL = 0.40
PHI = {"dry": 0.58, "coh": 0.50}          # loose packing used to turn 40 % by volume into a grain count
CED = {"dry": 0.0, "coh": L.CED_COH}
T_FILL = 0.25
# rpm, duration (s), averaging window (s after the drum starts). The dry run's deck also holds a 2 rpm stage,
# but the run was stopped at the end of its 5 rpm stage for time (the runner was shared); 2 rpm was not run.
SCHEDULES = {"dry": [(20.0, 1.6, (0.6, 1.6)), (5.0, 2.0, (2.1, 3.6)), (2.0, 3.0, (4.1, 6.6))],
             "coh": [(20.0, 1.6, (0.6, 1.6)), (5.0, 2.5, (2.1, 4.1))]}
SCHEDULE = SCHEDULES["dry"]
DUMP_DT = 0.02


def drum_profile():
    pts = []
    nseg = 8
    for k in range(NRIB):
        a0 = 2 * math.pi * k / NRIB
        a1 = a0 + 2 * math.pi / NRIB
        dw = WRIB / 2 / R
        di = WRIB / 2 / (R - HRIB)
        pts += [(R * math.cos(a0 - dw), R * math.sin(a0 - dw)),
                ((R - HRIB) * math.cos(a0 - di), (R - HRIB) * math.sin(a0 - di)),
                ((R - HRIB) * math.cos(a0 + di), (R - HRIB) * math.sin(a0 + di)),
                (R * math.cos(a0 + dw), R * math.sin(a0 + dw))]
        for j in range(1, nseg):
            a = a0 + dw + (a1 - a0 - 2 * dw) * j / nseg
            pts.append((R * math.cos(a), R * math.sin(a)))
    return pts


def fill_level(frac):
    """Height z_f (axis at 0) of a flat surface with frac of the circle below it."""
    lo, hi = -R, R
    for _ in range(60):
        zf = 0.5 * (lo + hi)
        a = math.acos(-zf / R)          # half angle of the segment below zf, measured from the bottom
        area = R * R * (a - math.sin(a) * math.cos(a))
        if area / (math.pi * R * R) < frac:
            lo = zf
        else:
            hi = zf
    return zf


def build(case, wd):
    os.makedirs(os.path.join(wd, "dump"), exist_ok=True)
    pts = drum_profile()
    tris = []
    n = len(pts)
    for i in range(n):
        (x0, z0), (x1, z1) = pts[i], pts[(i + 1) % n]
        # the mesh overhangs the periodic slice by 0.1 mm at each end: a mesh that ends exactly on the
        # periodic boundary tripped an insertion assertion in LIGGGHTS 3.8 for this slice width
        ya, yb = -0.1e-3, LY + 0.1e-3
        p00, p01, p10, p11 = (x0, ya, z0), (x1, ya, z1), (x0, yb, z0), (x1, yb, z1)
        tris += [(p00, p01, p11), (p00, p11, p10)]
    L.write_stl(os.path.join(wd, "drum.stl"), tris, "drum")
    zf = fill_level(FILL)
    ngr = int(round(FILL * math.pi * R * R * LY * PHI[case] / L.mean_grain_volume()))
    box = (-R - 0.5e-3, R + 0.5e-3, 0.0, LY, -R - 0.5e-3, R + 0.5e-3)
    head, wm, dt = L.header(box, periodic="f p f", ced=CED[case])
    st = lambda s: max(1, int(round(s / dt)))  # noqa: E731
    deck = head + f"""
fix drum all mesh/surface file drum.stl type 2 curvature_tolerant yes
fix walls all wall/gran {wm} mesh n_meshes 1 meshes drum
region fillreg cylinder y 0. 0. {R - HRIB - 0.3e-3:.5e} 0. {LY:.5e} units box
region fillcut block INF INF INF INF INF {R - 2.0e-3:.5e} units box
region fill intersect 2 fillreg fillcut
fix ins all insert/pack seed 86028157 distributiontemplate pdd insert_every once overlapcheck yes all_in yes particles_in_region {ngr} region fill ntry_mc 50000
fix integr all nve/sphere
variable t equal time
thermo_style custom step time atoms ke
thermo {st(0.1)}
thermo_modify lost ignore norm no flush yes
dump dmp all custom {st(DUMP_DT)} dump/p.*.txt id radius x y z vx vy vz
dump dmesh all mesh/stl {st(0.5)} dump/drum*.stl drum
run {st(T_FILL)}
"""
    for rpm, dur, _ in SCHEDULES[case]:
        deck += f"""fix rot all move/mesh mesh drum rotate origin 0. 0. 0. axis 0. -1. 0. period {60.0 / rpm:.6f}
run {st(dur)}
unfix rot
"""
    with open(os.path.join(wd, "in.drum"), "w") as f:
        f.write(deck)
    return dict(dt=dt, n_grains=ngr, z_fill=zf)


def surface_angle(d):
    """Free-surface angle (deg) and the surface heights, from a line fit across the central 60 % of the chord."""
    x, z, r = d["x"], d["z"], d["radius"]
    top = z + r
    # rough surface: highest grain per 0.5 mm column
    edges = np.arange(-R, R + 0.5e-3, 0.5e-3)
    idx = np.digitize(x, edges) - 1
    h = np.full(len(edges) - 1, np.nan)
    for b in np.unique(idx):
        if 0 <= b < len(h):
            h[b] = top[idx == b].max()
    xc = 0.5 * (edges[1:] + edges[:-1])
    ok = np.isfinite(h)
    # chord ends: where the surface meets the wall; use the bins that hold grains
    xs = xc[ok]
    x0, x1 = xs.min(), xs.max()
    w = x1 - x0
    m = ok & (xc > x0 + 0.2 * w) & (xc < x1 - 0.2 * w)
    p = np.polyfit(xc[m], h[m], 1)
    resid = h[m] - np.polyval(p, xc[m])
    return math.degrees(math.atan(p[0])), float(np.sqrt(np.mean(resid ** 2))), xc, h, p


def analyze(case, wd, meta):
    dt = meta["dt"]
    files = L.dump_series(os.path.join(wd, "dump", "p.*.txt"))
    ts, ang, rough, frames, cm = [], [], [], [], []
    for fp in files:
        step, d = L.read_dump(fp)
        if len(d["x"]) < 100:          # the dump at step 0 is written before the grains are inserted
            continue
        t = step * dt - T_FILL
        ts.append(t)
        a, rr, *_ = surface_angle(d)
        ang.append(abs(a))
        rough.append(rr)
        frames.append({k: d[k] for k in ("id", "x", "y", "z", "radius")})
        cm.append(float(np.mean(np.sqrt(d["vx"] ** 2 + d["vz"] ** 2))))
    ts, ang, rough = np.array(ts), np.array(ang), np.array(rough)
    out = dict(case=case, n_grains=meta["n_grains"], drum_D_mm=2 * R * 1e3, slice_mm=LY * 1e3,
               fill_frac=FILL, ced=CED[case], t_end_s=float(ts[-1]), speeds=[])
    t0 = 0.0
    for rpm, dur, (wa, wb) in SCHEDULES[case]:
        m = (ts >= wa) & (ts <= wb)
        w = 2 * math.pi * rpm / 60
        rec = dict(rpm=rpm, froude=w * w * R / 9.81, window_s=[wa, wb], n_samples=int(m.sum()))
        if m.sum() >= 10 and ts[-1] >= wb - 0.05:
            a = ang[m]
            # avalanche extrema: local maxima / minima of the angle series
            mx = [a[i] for i in range(1, len(a) - 1) if a[i] >= a[i - 1] and a[i] > a[i + 1]]
            mn = [a[i] for i in range(1, len(a) - 1) if a[i] <= a[i - 1] and a[i] < a[i + 1]]
            rec.update(dynamic_angle_deg=float(a.mean()), angle_sd_deg=float(a.std()),
                       angle_sem_deg=float(a.std() / math.sqrt(max(1, m.sum() / 5))),
                       angle_max_deg=float(a.max()), angle_min_deg=float(a.min()),
                       upper_angle_deg=float(np.mean(sorted(mx)[-3:])) if mx else None,
                       lower_angle_deg=float(np.mean(sorted(mn)[:3])) if mn else None,
                       surface_roughness_mm=float(rough[m].mean() * 1e3),
                       drum_turn_in_window_deg=float(rpm * 6 * (min(wb, ts[-1]) - wa)),
                       complete=bool(ts[-1] >= wb - 0.05))
        out["speeds"].append(rec)
        t0 += dur
    out["series"] = dict(t=ts.tolist(), angle_deg=ang.tolist(), roughness_mm=(rough * 1e3).tolist(),
                         mean_speed_m_s=cm)
    # drum angle (deg, about -y) vs time for the animation
    tt = np.array(ts)
    phi = np.zeros_like(tt)
    tcur, phicur = 0.0, 0.0
    for rpm, dur, _ in SCHEDULES[case]:
        m = (tt > tcur) & (tt <= tcur + dur)
        phi[m] = phicur + rpm * 6 * (tt[m] - tcur)
        phicur += rpm * 6 * dur
        tcur += dur
    size = L.save_frames(os.path.join(L.HERE, "frames", f"{TEST}_{case}.npz"), ts, frames, max_frames=90,
                         extra=dict(drum_angle_deg=np.interp(np.linspace(tt[0], tt[-1], 90), tt, phi).astype(np.float32),
                                    drum_R_mm=np.float32(R * 1e3), n_ribs=np.int32(NRIB),
                                    rib_height_mm=np.float32(HRIB * 1e3), slice_mm=np.float32(LY * 1e3),
                                    note=np.array("drum_angle_deg is sampled at np.linspace(t[0], t[-1], 90) "
                                                  "before frame decimation; rotation about -y (right side rises)")))
    out["frames_npz_bytes"] = size
    return out


def main():
    mode, case = sys.argv[1], sys.argv[2]
    wd = os.path.join(L.SCRATCH, TEST, case)
    os.makedirs(wd, exist_ok=True)
    meta = build(case, wd)
    shutil.copy(os.path.join(wd, "in.drum"), os.path.join(L.HERE, "decks", f"in.{TEST}_{case}"))
    runinfo = L.read_json(os.path.join(wd, "run.json"), {})
    if mode == "run":
        rc, wall, tail = L.run_liggghts(wd, "in.drum")
        runinfo = dict(rc=rc, wall_s=wall)
        L.write_json(os.path.join(wd, "run.json"), runinfo)
        if rc != 0:
            print(tail)
    res = analyze(case, wd, meta)
    res.update(wall_s=runinfo.get("wall_s"), dt_s=meta["dt"])
    L.write_json(os.path.join(L.HERE, "results", f"{TEST}_{case}.json"), res)
    for s in res["speeds"]:
        print(case, {k: s.get(k) for k in ("rpm", "froude", "dynamic_angle_deg", "angle_sd_deg", "upper_angle_deg",
                                          "lower_angle_deg", "n_samples")})


if __name__ == "__main__":
    main()
