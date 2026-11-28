"""Test 1, heap angle of repose on the printed pedestal (SPEC.md section 1), LIGGGHTS-PUBLIC 3.8.

As designed: pedestal top (12, 20 or 30 mm) with a 0.4 mm land and a 45 deg chamfer underneath, its top
roughened with a glued layer of the test powder (here a frozen random monolayer, 50 % area coverage).
Feed: a 3 mm wide stream 11-14 mm above the pedestal top (doser outlet 12 mm above it), 8000 grains/s
(0.73 g/s, as #196 run 2). Grains that fall off the rim leave the box (the overflow tray is not weighed).

usage: python t1_heap.py run|analyze CASE      CASE = d20_dry | d20_coh | d12_dry | d12_coh | d30_dry
"""
import math
import os
import shutil
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import demlib as L  # noqa: E402

TEST = "t1_heap"
CASES = {
    "d20_dry": dict(D=20e-3, ced=0.0, N=20000),
    "d20_coh": dict(D=20e-3, ced=L.CED_COH, N=32000),
    "d12_dry": dict(D=12e-3, ced=0.0, N=5000),
    "d12_coh": dict(D=12e-3, ced=L.CED_COH, N=8000),
    "d30_dry": dict(D=30e-3, ced=0.0, N=60000, stages=[(40000, 16000.0), (20000, 8000.0)]),
}
RATE = 8000.0
T_SETTLE = 0.4
Z_INS = (11e-3, 14e-3)
DUMP_DT = 0.02


def build(case, wd):
    c = CASES[case]
    R = 0.5 * c["D"]
    os.makedirs(os.path.join(wd, "dump"), exist_ok=True)
    prof = [(0.0, 0.0), (R, 0.0), (R, -0.4e-3), (R - 3e-3, -3.4e-3)]
    L.write_stl(os.path.join(wd, "pedestal.stl"), L.revolve(prof, n=128), "pedestal")
    rng = np.random.default_rng(7)
    xyz, diam = L.rsa_monolayer(lambda x, y, r: x * x + y * y <= (R - r) ** 2, (-R, R, -R, R), rng,
                                coverage=0.5)
    glued, xyz, diam = L.frozen_atoms_block(xyz, diam, group="glued")
    ng = len(diam)
    half = R + 5e-3
    box = (-half, half, -half, half, -6e-3, 16e-3)
    head, wall_model, dt = L.header(box, ced=c["ced"])
    st = lambda s: max(1, int(round(s / dt)))  # noqa: E731
    stages = c.get("stages", [(c["N"], RATE)])
    t_pour = sum(n / rt for n, rt in stages)
    deck = head + glued + f"""
region farreg block 1 2 1 2 1 2 units box
group grains region farreg
fix ped all mesh/surface file pedestal.stl type 2 curvature_tolerant yes
fix walls all wall/gran {wall_model} mesh n_meshes 1 meshes ped
region pour cylinder z 0. 0. 1.5e-3 {Z_INS[0]:.4e} {Z_INS[1]:.4e} units box
fix integr grains nve/sphere
region heapreg cylinder z 0. 0. {R + 0.5e-3:.4e} -0.6e-3 10.5e-3 units box
variable t equal time
variable n equal count(grains)
variable nh equal count(grains,heapreg)
variable mh equal mass(grains,heapreg)
thermo_style custom step time atoms ke
thermo {st(0.1)}
thermo_modify lost ignore norm no flush yes
fix logm all print {st(0.005)} "${{t}} ${{n}} ${{nh}} ${{mh}}" file heapmass.txt screen no title "t n nh mh"
dump dmp all custom {st(DUMP_DT)} dump/p.*.txt id type radius x y z vx vy vz
"""
    for i, (n, rt) in enumerate(stages):
        deck += (f"fix ins{i} grains insert/rate/region seed {86028157 + 2 * i} distributiontemplate pdd nparticles {n} "
                 f"particlerate {rt} insert_every {st(0.005)} overlapcheck yes all_in yes vel constant 0. 0. -0.1 "
                 f"region pour ntry_mc 5000\nrun {st(n / rt)}\nunfix ins{i}\n")
    deck += f"run {st(T_SETTLE)}\n"
    with open(os.path.join(wd, "in.heap"), "w") as f:
        f.write(deck)
    return dict(dt=dt, n_glued=ng, t_pour=t_pour, R=R)


def silhouette_flanks(x, y, z, r, R, nview=8, binw=0.25e-3):
    """Camera silhouettes from nview azimuths; flank lines fitted between 15 and 85 % of height."""
    top = z + r
    out = []
    sil0 = None
    for k in range(nview):
        a = math.pi * k / nview
        u = x * math.cos(a) + y * math.sin(a)
        edges = np.arange(-R - 1e-3, R + 1e-3 + binw, binw)
        idx = np.digitize(u, edges) - 1
        hmax = np.full(len(edges) - 1, np.nan)
        for b in np.unique(idx):
            if 0 <= b < len(hmax):
                m = idx == b
                hmax[b] = top[m].max()
        uc = 0.5 * (edges[1:] + edges[:-1])
        h = np.nanmax(hmax)
        if k == 0:
            sil0 = (uc, hmax)
        for side in (-1, 1):
            m = np.isfinite(hmax) & (hmax > 0.15 * h) & (hmax < 0.85 * h) & (np.sign(uc) == side)
            if m.sum() >= 4:
                p = np.polyfit(uc[m], hmax[m], 1)
                out.append(math.degrees(math.atan(abs(p[0]))))
    return np.array(out), sil0


def radial_profile_fit(x, y, z, r, R, nbins=None, nsect=8):
    """#196 run 2 method: top of the heap in radial bins x 8 sectors; line fit 1/6 to 0.87 R."""
    rr = np.hypot(x, y)
    top = z + r
    nb = nbins or int(round(R / 0.4e-3))
    edges = np.linspace(0, R, nb + 1)
    sect = ((np.arctan2(y, x) + math.pi) / (2 * math.pi) * nsect).astype(int) % nsect
    prof = np.full((nsect, nb), np.nan)
    for s in range(nsect):
        for b in range(nb):
            m = (sect == s) & (rr >= edges[b]) & (rr < edges[b + 1])
            if m.any():
                prof[s, b] = top[m].max()
    rc = 0.5 * (edges[1:] + edges[:-1])
    h = np.nanmean(prof, axis=0)
    fit = (rc > R / 6) & (rc < 0.87 * R) & np.isfinite(h)
    p = np.polyfit(rc[fit], h[fit], 1)
    angs = []
    for s in range(nsect):
        ok = fit & np.isfinite(prof[s])
        if ok.sum() > 4:
            angs.append(math.degrees(math.atan(-np.polyfit(rc[ok], prof[s, ok], 1)[0])))
    return math.degrees(math.atan(-p[0])), float(np.std(angs))


def heap_state(d, R, ng):
    keep = (d["id"] > ng) & (d["z"] > -0.6e-3) & (np.hypot(d["x"], d["y"]) < R + 0.5e-3)
    rest = keep & (d["vz"] > -0.15)          # drop the falling feed stream, keep the flowing surface layer
    x, y, z, r = d["x"][rest], d["y"][rest], d["z"][rest], d["radius"][rest]
    m = L.SALT["density"] * 4 / 3 * math.pi * r ** 3
    return x, y, z, r, m


def analyze(case, wd, meta):
    R = meta["R"]
    ng = meta["n_glued"]
    files = L.dump_series(os.path.join(wd, "dump", "p.*.txt"))
    dt = meta["dt"]
    ts, flank_t, h_t, mass_t, frames = [], [], [], [], []
    for fp in files:
        step, d = L.read_dump(fp)
        t = step * dt
        frames.append(d)
        ts.append(t)
        x, y, z, r, m = heap_state(d, R, ng)
        mass_t.append(m.sum())
        if len(z) > 50:
            h = (z + r).max()
            h_t.append(h)
            fl, _ = silhouette_flanks(x, y, z, r, R, nview=4) if h > 1.0e-3 else (np.array([]), None)
            flank_t.append(float(np.mean(fl)) if len(fl) else float("nan"))
        else:
            h_t.append(0.0)
            flank_t.append(float("nan"))
    # final heap
    _, d = L.read_dump(files[-1])
    x, y, z, r, m = heap_state(d, R, ng)
    fl, sil0 = silhouette_flanks(x, y, z, r, R, nview=8)
    H = float((z + r).max())
    prof_ang, prof_sd = radial_profile_fit(x, y, z, r, R)
    # volume of revolution of the silhouette: average the 8 views' half-widths at each height
    zs = np.linspace(0, H, 60)
    radii = []
    for k in range(8):
        a = math.pi * k / 8
        u = x * math.cos(a) + y * math.sin(a)
        for side in (-1, 1):
            uu = u * side
            rad = []
            for zz in zs:
                mm = (z + r > zz)
                rad.append(min(R, uu[mm].max() + 0.0) if mm.any() else 0.0)
            radii.append(rad)
    rad_mean = np.clip(np.mean(radii, axis=0), 0, R)
    V = float(np.trapezoid(math.pi * rad_mean ** 2, zs))
    M = float(m.sum())
    # balance signal
    hm = np.loadtxt(os.path.join(wd, "heapmass.txt"), skiprows=1)
    tt, mh = hm[:, 0], hm[:, 3]
    dm = np.diff(mh)
    t_pour = meta["t_pour"]
    drops = dm[(tt[1:] > 0.3) & (dm < 0)]
    gm = L.grain_mass_mean()
    big = np.sort(-drops)[::-1][:10]
    # growth over the last 0.25 s of pouring, per 0.25 s (about one doser rev at 30 rpm and 0.2 g/rev
    # delivers the same mass as 0.25 s here)
    def m_at(tq):
        return float(np.interp(tq, tt, mh))
    growth = (m_at(t_pour) - m_at(t_pour - 0.25)) / max(m_at(t_pour), 1e-12)
    res = dict(
        case=case, D_mm=2 * R * 1e3, ced=CASES[case]["ced"], n_poured=CASES[case]["N"], n_glued=ng,
        flank_angle_deg=float(np.mean(fl)), flank_angle_sd_deg=float(np.std(fl)), n_flank_fits=len(fl),
        iso_apex_angle_deg=math.degrees(math.atan(2 * H / (2 * R))), apex_height_mm=H * 1e3,
        profile_fit_angle_deg=prof_ang, profile_fit_sector_sd_deg=prof_sd,
        heap_mass_g=M * 1e3, heap_grains=int(len(z)), heap_volume_mm3=V * 1e9,
        heap_density_kg_m3=M / V if V > 0 else None, heap_packing_fraction=(M / V / L.SALT["density"]) if V > 0 else None,
        growth_last_0p25s_frac=growth,
        mass_drops_n=int((drops < -3 * gm).sum()), mass_drops_largest_mg=(big * 1e6).tolist(),
        t_pour_s=t_pour, t_end_s=float(ts[-1]),
        flank_angle_time_series=dict(t=ts, angle=flank_t, apex_mm=(np.array(h_t) * 1e3).tolist(),
                                     mass_g=(np.array(mass_t) * 1e3).tolist()),
        silhouette_view0=dict(u_mm=(sil0[0] * 1e3).tolist(), h_mm=(sil0[1] * 1e3).tolist()),
    )
    # trajectory for animation
    fr = []
    for d in frames:
        mm = (d["z"] > -6e-3)
        fr.append({k: d[k][mm] for k in ("id", "x", "y", "z", "radius")})
    size = L.save_frames(os.path.join(L.HERE, "frames", f"{TEST}_{case}.npz"), ts, fr,
                         extra=dict(pedestal_R_mm=np.float32(R * 1e3), glued_ids_max=np.int32(ng),
                                    feed_z_mm=np.array(Z_INS, dtype=np.float32) * 1e3))
    res["frames_npz_bytes"] = size
    np.savetxt(os.path.join(L.HERE, "results", f"{TEST}_{case}_heapmass.csv"), hm[::2], delimiter=",",
               header="t_s,n_in_box,n_on_pedestal,mass_on_pedestal_kg", fmt="%.5g", comments="")
    return res


def main():
    mode, case = sys.argv[1], sys.argv[2]
    wd = os.path.join(L.SCRATCH, TEST, case)
    os.makedirs(wd, exist_ok=True)
    if mode == "run" or not os.path.exists(os.path.join(wd, "in.heap")):
        meta = build(case, wd)
    else:   # analyze only: keep the deck that ran, rebuild elsewhere just for the metadata
        meta = build(case, wd + "_meta")
        meta["n_glued"] = sum(1 for ln in open(os.path.join(wd, "in.heap")) if ln.startswith("create_atoms"))
    shutil.copy(os.path.join(wd, "in.heap"), os.path.join(L.HERE, "decks", f"in.{TEST}_{case}"))
    runinfo = L.read_json(os.path.join(wd, "run.json"), {})
    if mode == "run":
        rc, wall, tail = L.run_liggghts(wd, "in.heap")
        runinfo = dict(rc=rc, wall_s=wall)
        L.write_json(os.path.join(wd, "run.json"), runinfo)
        if rc != 0:
            print(tail)
            sys.exit(rc)
    res = analyze(case, wd, meta)
    res.update(wall_s=runinfo.get("wall_s"), dt_s=meta["dt"])
    L.write_json(os.path.join(L.HERE, "results", f"{TEST}_{case}.json"), res)
    print({k: res[k] for k in ("case", "flank_angle_deg", "flank_angle_sd_deg", "iso_apex_angle_deg",
                               "profile_fit_angle_deg", "heap_mass_g", "growth_last_0p25s_frac", "wall_s")})


if __name__ == "__main__":
    main()
