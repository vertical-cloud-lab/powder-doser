"""Test 3, tilting plate (SPEC.md section 3), LIGGGHTS-PUBLIC 3.8.

Mode A (wall friction): a 3 mm powder layer under a rigid lid, periodic in x and y (the interior of the
Ø25 ring; the ring wall, its 0.5 mm gap and the edges are not modelled). The plate is a flat wall with
mu_wall 0.4 (PLA). The lid is a square layer of 0.425 mm spheres that translates as one body (fix nve +
fix aveforce, no rotation); its density is set so that powder + lid give sigma_n = 100 or 400 Pa on the
plate. Variants: dry; cohesive grains on a non-adhesive plate; cohesive grains with grain-plate SJKR
adhesion (k_w = 6 kJ/m3).
Mode B (layer start angle): a struck-off layer 1, 2 or 3 mm thick on a rough base (frozen random
monolayer of grains, 50 % cover, as the powder-roughened coupon), periodic in x and y.
Tilting: gravity is turned in 0.25 deg steps held 0.02 s (12.5 deg/s); the real table turns at 0.5 deg/s.
Slip / start: mean grain speed down the slope > 20 mm/s.

usage: python t3_tilt.py run|analyze CASE    CASE = A_{dry,coh,cohw}_{100,400} | B_{dry,coh}_{1,2,3}
"""
import math
import os
import shutil
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import demlib as L  # noqa: E402

TEST = "t3_tilt"
DTH, HOLD = 0.25, 0.02
V_SLIP = 0.02


def rsa_periodic(Lx, Ly, rng, coverage=0.5, max_try=300000):
    pts = np.zeros((0, 2))
    rad = np.zeros(0)
    area = 0.0
    for _ in range(max_try):
        r = 0.5 * L.sample_psd(1, rng)[0]
        x, y = rng.uniform(0, Lx), rng.uniform(0, Ly)
        if len(rad):
            dx = x - pts[:, 0]
            dy = y - pts[:, 1]
            dx -= Lx * np.round(dx / Lx)
            dy -= Ly * np.round(dy / Ly)
            if np.any(dx * dx + dy * dy < 4 * r * rad * 1.0001):
                continue
        pts = np.vstack([pts, [x, y]])
        rad = np.append(rad, r)
        area += math.pi * r * r
        if area / (Lx * Ly) >= coverage:
            break
    return np.c_[pts, rad], 2 * rad


def parse(case):
    mode, var, val = case.split("_")
    return mode, var, float(val)


def build(case, wd):
    mode, var, val = parse(case)
    os.makedirs(os.path.join(wd, "dump"), exist_ok=True)
    ced = 0.0 if var == "dry" else L.CED_COH
    rho = L.SALT["density"]
    if mode == "A":
        Lx = Ly = 14 * 0.425e-3
        h_layer = 3.0e-3
        n = int(round(Lx * Ly * h_layer * (0.58 if var == "dry" else 0.50) / L.mean_grain_volume()))
        box = (0, Lx, 0, Ly, -0.2e-3, 8e-3)
        head, wm, dt = L.header(box, periodic="p p f", ced=ced, cohesion_walls=(var == "cohw"), ced_wall=ced)
        m_powder = n * L.grain_mass_mean()
        sig = val
        m_lid = max(sig * Lx * Ly / 9.81 - m_powder, 0.0)
        v_lid_sphere = math.pi / 6 * 0.425e-3 ** 3
        rho_lid = m_lid / (196 * v_lid_sphere)
        th0, th1 = 12.0, 34.0
        st = lambda s: max(1, int(round(s / dt)))  # noqa: E731
        z_lid = 6.2e-3
        setup = f"""
lattice sc 4.250000e-04 origin 0.5 0.5 0.5
region lidlayer block 0. {Lx:.6e} 0. {Ly:.6e} {z_lid:.6e} {z_lid + 0.425e-3:.6e} units box
create_atoms 1 region lidlayer
group lid region lidlayer
set group lid diameter 4.250000e-04
set group lid density {rho_lid:.6e}
region farreg block 1 2 1 2 1 2 units box
group grains region farreg
fix plate all wall/gran {wm} primitive type 2 zplane 0.0
region insreg block 0. {Lx:.6e} 0. {Ly:.6e} 0.3e-3 {z_lid - 0.4e-3:.6e} units box
fix ins grains insert/pack seed 86028157 distributiontemplate pdd insert_every once overlapcheck yes all_in yes particles_in_region {n} region insreg ntry_mc 50000
fix integr grains nve/sphere
fix lidint lid nve
fix lidave lid aveforce 0.0 0.0 0.0
compute vg grains reduce ave vx
compute vl lid reduce ave vx
compute zl lid reduce ave z
"""
        info = dict(n=n, m_lid_g=m_lid * 1e3, rho_lid=rho_lid, sigma_n_Pa=sig, sigma_powder_Pa=m_powder * 9.81 / (Lx * Ly),
                    Lx_mm=Lx * 1e3, layer_mm=h_layer * 1e3)
    else:
        Lx, Ly = 8.0e-3, 4.0e-3
        h = val * 1e-3
        rng = np.random.default_rng(11)
        xyzr, diam = rsa_periodic(Lx, Ly, rng)
        xyz = np.c_[xyzr[:, 0], xyzr[:, 1], 0.5 * diam]
        base, _, _ = L.frozen_atoms_block(xyz, diam, group="base")
        nb = len(diam)
        n = int(round(Lx * Ly * (h + 1.5e-3) * 0.58 / L.mean_grain_volume()))
        box = (0, Lx, 0, Ly, -0.2e-3, h + 8e-3)
        head, wm, dt = L.header(box, periodic="p p f", ced=ced)
        th0, th1 = 15.0, 60.0
        st = lambda s: max(1, int(round(s / dt)))  # noqa: E731
        setup = base + f"""
region farreg block 1 2 1 2 1 2 units box
group grains region farreg
fix plate all wall/gran {wm} primitive type 2 zplane 0.0
region insreg block 0. {Lx:.6e} 0. {Ly:.6e} 0.6e-3 {h + 7.5e-3:.6e} units box
fix ins grains insert/pack seed 86028157 distributiontemplate pdd insert_every once overlapcheck yes all_in yes particles_in_region {n} region insreg ntry_mc 50000
fix integr grains nve/sphere
compute vg grains reduce ave vx
compute zl grains reduce max z
"""
        info = dict(n_inserted=n, n_base=nb, layer_mm=val, Lx_mm=Lx * 1e3, Ly_mm=Ly * 1e3)
    nsteps = int(round((th1 - th0) / DTH))
    deck = head + setup + f"""
variable t equal time
thermo_style custom step time atoms ke c_vg c_zl
thermo {st(0.1)}
thermo_modify lost ignore norm no flush yes
run {st(0.35)}
"""
    if mode == "B":
        deck += f"""region strike block INF INF INF INF {val * 1e-3 - 0.2e-3:.6e} INF units box
group above region strike
group struck intersect above grains
delete_atoms group struck
run {st(0.1)}
"""
    deck += f"""variable th equal {th0}
variable gx equal sin(v_th*PI/180.0)
variable gz equal -cos(v_th*PI/180.0)
unfix gravi
fix gravi all gravity 9.81 vector ${{gx}} 0.0 ${{gz}}
run {st(0.15)}
variable vgx equal c_vg
fix logt all print {st(0.002)} "${{t}} ${{th}} ${{vgx}} {'${vlx} ${zlz}' if mode == 'A' else '${zlz}'}" file tilt.txt screen no title "t theta vgrains {'vlid zlid' if mode == 'A' else 'zmax'}"
dump dmp all custom {st(0.04)} dump/p.*.txt id radius x y z vx vy vz
variable j loop {nsteps}
label tilt
  variable th equal {th0}+{DTH}*${{j}}
  unfix gravi
  fix gravi all gravity 9.81 vector ${{gx}} 0.0 ${{gz}}
  run {st(HOLD)}
  variable vnow equal ${{vgx}}
  if "${{vnow}} > {V_SLIP}" then "jump SELF done"
  next j
jump SELF tilt
label done
run {st(0.06)}
write_dump all custom final.txt id radius x y z vx vy vz
"""
    pre = "variable vlx equal c_vl\nvariable zlz equal c_zl\n" if mode == "A" else "variable zlz equal c_zl\n"
    deck = deck.replace("variable th equal", pre + "variable th equal", 1)
    with open(os.path.join(wd, "in.tilt"), "w") as f:
        f.write(deck)
    info.update(dt=dt, th0=th0, th1=th1)
    return info


def analyze(case, wd, info):
    mode, var, val = parse(case)
    A = np.loadtxt(os.path.join(wd, "tilt.txt"), skiprows=1, ndmin=2)
    t, th, vg = A[:, 0], A[:, 1], A[:, 2]
    out = dict(case=case, mode=mode, variant=var, **{k: v for k, v in info.items() if k != "dt"})
    # slip / start angle: first tilt step where the mean grain speed exceeds V_SLIP
    over = np.where(vg > V_SLIP)[0]
    th_slip = float(th[over[0]]) if len(over) else None
    # 0.5 mm displacement criterion (camera), from integrating the mean grain velocity
    disp = np.concatenate([[0], np.cumsum(0.5 * (vg[1:] + vg[:-1]) * np.diff(t))])
    m = np.where(disp > 0.5e-3)[0]
    th_disp = float(th[m[0]]) if len(m) else None
    # creep before slip: velocity at 1 deg below the slip angle
    out.update(slip_angle_deg=th_slip, angle_at_0p5mm_deg=th_disp, resolution_deg=DTH,
               tan_slip=math.tan(math.radians(th_slip)) if th_slip else None,
               atan_mu_wall_deg=math.degrees(math.atan(L.SALT["mu_pw"])),
               series=dict(theta=th[::5].tolist(), v_grains=vg[::5].tolist()))
    if mode == "A" and th_slip:
        out["lid_moved_with_powder"] = bool(A[over[0], 3] > 0.5 * V_SLIP)
    # where does it fail? velocity profile vs height in the last dump before stop
    fp = os.path.join(wd, "final.txt")
    if os.path.exists(fp):
        _, d = L.read_dump(fp)
        z, vx = d["z"], d["vx"]
        bins = np.linspace(0, z.max(), 9)
        prof = [float(vx[(z >= a) & (z < b)].mean()) if ((z >= a) & (z < b)).any() else None
                for a, b in zip(bins[:-1], bins[1:])]
        out["final_vx_profile"] = dict(z_mm=(0.5 * (bins[1:] + bins[:-1]) * 1e3).tolist(), vx=prof)
    files = L.dump_series(os.path.join(wd, "dump", "p.*.txt"))
    if files and case in ("A_dry_100", "A_cohw_100", "B_dry_2", "B_coh_2"):
        frames, ts = [], []
        for fp in files:
            step, d = L.read_dump(fp)
            frames.append({k: d[k] for k in ("id", "x", "y", "z", "radius")})
            ts.append(step * info["dt"])
        th_f = np.interp(ts, t, th, left=th[0])
        out["frames_npz_bytes"] = L.save_frames(
            os.path.join(L.HERE, "frames", f"{TEST}_{case}.npz"), ts, frames, max_frames=120,
            extra=dict(tilt_deg=np.array(th_f, dtype=np.float32),
                       note=np.array("plate frame: x down the slope, z normal to the plate; periodic in x and y; "
                                     "tilt_deg is the gravity angle from the plate normal")))
    return out


def main():
    mode, case = sys.argv[1], sys.argv[2]
    wd = os.path.join(L.SCRATCH, TEST, case)
    os.makedirs(wd, exist_ok=True)
    info = build(case, wd)
    shutil.copy(os.path.join(wd, "in.tilt"), os.path.join(L.HERE, "decks", f"in.{TEST}_{case}"))
    runinfo = L.read_json(os.path.join(wd, "run.json"), {})
    if mode == "run":
        rc, wall, tail = L.run_liggghts(wd, "in.tilt")
        runinfo = dict(rc=rc, wall_s=wall)
        L.write_json(os.path.join(wd, "run.json"), runinfo)
        if rc != 0:
            print(tail)
            sys.exit(rc)
    res = analyze(case, wd, info)
    res.update(wall_s=runinfo.get("wall_s"))
    L.write_json(os.path.join(L.HERE, "results", f"{TEST}_{case}.json"), res)
    print({k: res.get(k) for k in ("case", "slip_angle_deg", "angle_at_0p5mm_deg", "tan_slip", "lid_moved_with_powder",
                                   "wall_s")})


if __name__ == "__main__":
    main()
