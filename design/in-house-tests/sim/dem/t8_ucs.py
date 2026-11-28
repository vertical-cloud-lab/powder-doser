"""Test 8, unconfined compression of a column made in the split mould (SPEC.md section 8), LIGGGHTS 3.8.

As designed: 20 mm bore, column about 40 mm tall (H/D = 2), consolidated at sigma_1 = 1 kPa by a 19.6 mm
piston, piston lifted, mould removed, then a 30 mm platen lowered onto the column. Coarse-grained 2x
(grains 0.72/0.85/0.98 mm, 23.5 d50 across the bore) to afford the column on a shared runner: SJKR k is kept
at 6 kJ/m3, which keeps the pull-off force per unit contact area, so roughly the bulk cohesion, while the
grain Bond number drops from about 5 to about 2.5. The piston and the platen are layers of frozen spheres: the piston is force-controlled
(fix aveforce, as #196 run 6), the platen moves down at 20 mm/s (0.1 mm/s on the bench).

usage: python t8_ucs.py run|analyze CASE     CASE = coh | dry
"""
import math
import os
import shutil
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import demlib as L  # noqa: E402

TEST = "t8_ucs"
CG = 2.0
RM = 10.0e-3
H_COL = 40e-3
SIG1 = 1000.0
PHI = {"dry": 0.58, "coh": 0.50}
CED = {"dry": 0.0, "coh": L.CED_COH}
V_PLATEN = 0.02


def build(case, wd):
    os.makedirs(os.path.join(wd, "dump"), exist_ok=True)
    vg = L.mean_grain_volume(CG)
    n = int(round(math.pi * RM ** 2 * H_COL * PHI[case] / vg))
    box = (-16e-3, 16e-3, -16e-3, 16e-3, -1e-3, 95e-3)
    head, wm, dt = L.header(box, ced=CED[case], scale=CG)
    st = lambda s: max(1, int(round(s / dt)))  # noqa: E731
    dl = 0.85e-3                               # piston / platen sphere diameter
    m_sphere = L.SALT["density"] * math.pi / 6 * dl ** 3
    # piston spheres in r < 9.8 mm on a square lattice of pitch dl
    n_lid = sum(1 for i in range(-20, 21) for j in range(-20, 21)
                if math.hypot((i + 0.5) * dl, (j + 0.5) * dl) < 9.8e-3 - 0.5 * dl)
    F = SIG1 * math.pi * RM ** 2
    f_extra = (F - n_lid * m_sphere * 9.81) / n_lid
    deck = head + f"""
fix base all wall/gran {wm} primitive type 2 zplane 0.0
fix mould all wall/gran {wm} primitive type 2 zcylinder {RM:.5e} 0. 0.
region farreg block 1 2 1 2 1 2 units box
group grains region farreg
region fill cylinder z 0. 0. {RM - 0.4e-3:.5e} 0.5e-3 90e-3 units box
fix ins grains insert/pack seed 86028157 distributiontemplate pdd insert_every once overlapcheck yes all_in yes particles_in_region {n} region fill ntry_mc 100000
fix integr grains nve/sphere
variable t equal time
thermo_style custom step time atoms ke
thermo {st(0.05)}
thermo_modify lost ignore norm no flush yes
dump dmp all custom {st(0.02)} dump/p.*.txt id radius x y z vx vy vz
run {st(0.45)}
# ---- piston: square layer of frozen spheres just above the bed, force-controlled to sigma_1
variable ztop equal bound(grains,zmax)
run 0
variable zp0 equal ${{ztop}}+0.0009
variable zp1 equal ${{zp0}}+{dl:.6e}
lattice sc {dl:.6e} origin 0.5 0.5 0.5
region pist cylinder z 0. 0. {9.8e-3 - 0.5 * dl:.6e} ${{zp0}} ${{zp1}} units box
create_atoms 1 region pist
group lid region pist
set group lid diameter {dl:.6e}
set group lid density {L.SALT['density']}
fix lidmove lid move linear 0.0 0.0 NULL
fix lidvisc lid viscous 0.002
fix lidload lid aveforce NULL NULL {-f_extra:.6e}
compute zlid lid reduce ave z
compute fpl lid reduce sum fz
variable zl equal c_zlid
fix logp all print {st(0.005)} "${{t}} ${{zl}}" file piston.txt screen no title "t zlid"
run {st(0.4)}
# ---- lift the piston, relax
unfix logp
unfix lidload
unfix lidvisc
unfix lidmove
delete_atoms group lid
run {st(0.1)}
write_dump all custom consolidated.txt id radius x y z vx vy vz
# ---- open the mould
unfix mould
run {st(0.4)}
write_dump all custom released.txt id radius x y z vx vy vz
# ---- platen: 30 mm layer of spheres, lowered at {V_PLATEN * 1e3:.0f} mm/s from just above the column
run 0
variable zq0 equal ${{ztop}}+0.0005
variable zq1 equal ${{zq0}}+{dl:.6e}
region plat cylinder z 0. 0. 15.0e-3 ${{zq0}} ${{zq1}} units box
create_atoms 1 region plat
group platen region plat
set group platen diameter {dl:.6e}
set group platen density {L.SALT['density']}
fix platmove platen move linear 0.0 0.0 -{V_PLATEN}
compute fpt platen reduce sum fz
compute zpt platen reduce ave z
variable fp equal c_fpt
variable zp equal c_zpt
fix logf all print {st(0.002)} "${{t}} ${{zp}} ${{fp}}" file platen.txt screen no title "t zplaten fz"
run {st(0.2)}
"""
    with open(os.path.join(wd, "in.ucs"), "w") as f:
        f.write(deck)
    return dict(dt=dt, n=n, n_lid=n_lid, F_target_N=F)


def column_shape(d):
    z, r = d["z"], d["radius"]
    rr = np.hypot(d["x"], d["y"])
    H = float(np.percentile(z + r, 99.5))
    zs = np.linspace(0, H, 9)
    prof = []
    for a, b in zip(zs[:-1], zs[1:]):
        m = (z >= a) & (z < b)
        prof.append(float(np.percentile(rr[m] + r[m], 98)) if m.sum() > 20 else 0.0)
    return H, zs, prof


def analyze(case, wd, info):
    out = dict(case=case, ced=CED[case], coarse_grain=CG, n_grains=info["n"], sigma1_Pa=SIG1)
    if os.path.exists(os.path.join(wd, "consolidated.txt")):
        _, dc = L.read_dump(os.path.join(wd, "consolidated.txt"))
        Hc, _, _ = column_shape(dc)
        vol = (4 / 3 * math.pi * dc["radius"] ** 3).sum()
        out.update(H_consolidated_mm=Hc * 1e3, phi_consolidated=float(vol / (math.pi * RM ** 2 * Hc)),
                   self_weight_stress_base_Pa=float(vol * L.SALT["density"] * 9.81 / (math.pi * RM ** 2)))
    if os.path.exists(os.path.join(wd, "released.txt")):
        _, dr = L.read_dump(os.path.join(wd, "released.txt"))
        Hr, zs, prof = column_shape(dr)
        out.update(H_after_release_mm=Hr * 1e3, radius_profile_after_release_mm=[p * 1e3 for p in prof],
                   z_bins_mm=(zs * 1e3).tolist(),
                   stood=bool(Hr > 0.9 * out.get("H_consolidated_mm", 0) / 1e3 and max(prof) < RM + 2e-3))
    pp = os.path.join(wd, "platen.txt")
    if os.path.exists(pp):
        A = np.loadtxt(pp, skiprows=1, ndmin=2)
        t, zp, fz = A[:, 0], A[:, 1], A[:, 2]
        fz = fz - fz[0]                    # remove the platen spheres' own weight (no contact at the start)
        # running mean over 5 samples, peak force while the platen moved down
        fs = np.convolve(fz, np.ones(5) / 5, mode="same")
        k = int(np.argmax(fs))
        area = math.pi * RM ** 2
        out.update(platen_peak_force_N=float(fs[k]), sigma_c_Pa=float(fs[k] / area),
                   platen_travel_at_peak_mm=float((zp[0] - zp[k]) * 1e3),
                   platen_series=dict(travel_mm=((zp[0] - zp) * 1e3)[::3].tolist(), stress_Pa=(fs / area)[::3].tolist()))
        if out.get("stood") is False:
            out["note"] = "column did not stand after the mould opened; the platen force is that of a slumped heap"
    files = L.dump_series(os.path.join(wd, "dump", "p.*.txt"))
    if files:
        frames, ts = [], []
        for fp in files:
            step, d = L.read_dump(fp)
            m = np.abs(d["y"]) < 2.0e-3
            frames.append({k: d[k][m] for k in ("id", "x", "y", "z", "radius")})
            ts.append(step * info["dt"])
        out["frames_npz_bytes"] = L.save_frames(
            os.path.join(L.HERE, "frames", f"{TEST}_{case}.npz"), ts, frames, max_frames=90,
            extra=dict(mould_R_mm=np.float32(RM * 1e3),
                       note=np.array("slab |y| < 2 mm (grains entering/leaving the slab appear/disappear); "
                                     "fill 0-0.45 s, piston 0.45-0.85 s, relax, mould removed at 0.95 s, "
                                     "platen from 1.35 s; coarse-grained 2x")))
    return out


def main():
    mode, case = sys.argv[1], sys.argv[2]
    wd = os.path.join(L.SCRATCH, TEST, case)
    os.makedirs(wd, exist_ok=True)
    info = build(case, wd)
    shutil.copy(os.path.join(wd, "in.ucs"), os.path.join(L.HERE, "decks", f"in.{TEST}_{case}"))
    runinfo = L.read_json(os.path.join(wd, "run.json"), {})
    if mode == "run":
        rc, wall, tail = L.run_liggghts(wd, "in.ucs")
        runinfo = dict(rc=rc, wall_s=wall)
        L.write_json(os.path.join(wd, "run.json"), runinfo)
        if rc != 0:
            print(tail)
    res = analyze(case, wd, info)
    res.update(wall_s=runinfo.get("wall_s"), dt_s=info["dt"])
    L.write_json(os.path.join(L.HERE, "results", f"{TEST}_{case}.json"), res)
    print({k: res.get(k) for k in ("case", "H_consolidated_mm", "phi_consolidated", "H_after_release_mm", "stood",
                                   "sigma_c_Pa", "self_weight_stress_base_Pa", "wall_s")})


if __name__ == "__main__":
    main()
