"""Test 5, orifice cup (SPEC.md section 5), LIGGGHTS-PUBLIC 3.8.

As designed: 25 mm bore, flat bottom; orifice disc with a 0.5 mm land and a 45 deg relief underneath.
Reduced: the cup is filled to about 7 mm (48 000 grains dry, 41 000 cohesive) instead of 5 g / 20 mm.
One fill per powder is saved as a restart; each orifice run swaps the closed gate (a plane at z = 0) for a
disc with a D mm hole. Grains leave the box 8 mm below the disc; the discharged mass is logged every 2 ms.
A run stops early when no grain has left the cup for 0.05 s (jammed).

usage: python t5_orifice.py fill CASE | run CASE D_mm | analyze CASE     CASE = dry | coh
"""
import glob
import math
import os
import shutil
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import demlib as L  # noqa: E402

TEST = "t5_orifice"
RCUP = 12.5e-3
H_BED = 7.0e-3
PHI = {"dry": 0.58, "coh": 0.50}
CED = {"dry": 0.0, "coh": L.CED_COH}
T_SETTLE = 0.3
T_RUN = {2.0: 0.25, 3.0: 0.22, 4.0: 0.18, 5.08: 0.15, 6.0: 0.15}
ANIM_D = 4.0
BOX = (-RCUP - 0.5e-3, RCUP + 0.5e-3, -RCUP - 0.5e-3, RCUP + 0.5e-3, -8e-3, 18.5e-3)


def n_grains(case):
    return int(round(math.pi * RCUP ** 2 * H_BED * PHI[case] / L.mean_grain_volume()))


def fill(case, wd):
    os.makedirs(wd, exist_ok=True)
    head, wm, dt = L.header(BOX, ced=CED[case])
    st = lambda s: max(1, int(round(s / dt)))  # noqa: E731
    deck = head + f"""
fix gate all wall/gran {wm} primitive type 2 zplane 0.0
fix cup all wall/gran {wm} primitive type 2 zcylinder {RCUP:.5e} 0. 0.
region fill cylinder z 0. 0. {RCUP - 0.3e-3:.5e} 0.3e-3 18.0e-3 units box
fix ins all insert/pack seed 86028157 distributiontemplate pdd insert_every once overlapcheck yes all_in yes particles_in_region {n_grains(case)} region fill ntry_mc 100000
fix integr all nve/sphere
thermo_style custom step time atoms ke
thermo {st(0.05)}
thermo_modify lost ignore norm no flush yes
run {st(T_SETTLE)}
write_restart fill.restart
write_dump all custom fill_end.txt id radius x y z vx vy vz
"""
    with open(os.path.join(wd, "in.fill"), "w") as f:
        f.write(deck)
    shutil.copy(os.path.join(wd, "in.fill"), os.path.join(L.HERE, "decks", f"in.{TEST}_{case}_fill"))
    rc, wall, tail = L.run_liggghts(wd, "in.fill", log="log.fill", screen="screen.fill")
    L.write_json(os.path.join(wd, "fill.json"), dict(rc=rc, wall_s=wall, dt=dt, n=n_grains(case)))
    if rc != 0:
        print(tail)
        sys.exit(rc)


def discharge(case, D_mm, wd):
    D = D_mm * 1e-3
    rd = os.path.join(wd, f"D{D_mm:g}")
    os.makedirs(os.path.join(rd, "dump"), exist_ok=True)
    prof = [(RCUP + 0.3e-3, 0.0), (0.5 * D, 0.0), (0.5 * D, -0.5e-3), (0.5 * D + 1.5e-3, -2.0e-3)]
    L.write_stl(os.path.join(rd, "disc.stl"), L.revolve(prof, n=96), "disc")
    head, wm, dt = L.header(BOX, ced=CED[case])
    keep = [ln for ln in head.split("\n") if not ln.startswith((
        "atom_style", "atom_modify", "boundary", "newton", "units", "region          domain", "create_box",
        "communicate", "soft_particles"))]
    st = lambda s: max(1, int(round(s / dt)))  # noqa: E731
    anim = abs(D_mm - ANIM_D) < 1e-6
    chunk = st(0.025)
    nchunks = int(math.ceil(T_RUN[D_mm] / 0.025))
    deck = ("atom_style granular\natom_modify map array\nnewton off\ncommunicate single vel yes\n"
            "soft_particles yes\nread_restart ../fill.restart\n" + "\n".join(keep) + f"""
fix cup all wall/gran {wm} primitive type 2 zcylinder {RCUP:.5e} 0. 0.
fix disc all mesh/surface file disc.stl type 2 curvature_tolerant yes
fix walls all wall/gran {wm} mesh n_meshes 1 meshes disc
fix integr all nve/sphere
region cupreg cylinder z 0. 0. {RCUP + 0.5e-3:.5e} -0.6e-3 18.5e-3 units box
variable t equal time
variable m equal mass(all)
variable nc equal count(all,cupreg)
thermo_style custom step time atoms ke
thermo {st(0.05)}
thermo_modify lost ignore norm no flush yes
fix logm all print {st(0.002)} "${{t}} ${{m}} ${{nc}}" file mass.txt screen no title "t m ncup"
""")
    if anim:
        deck += f"dump dmp all custom {st(0.005)} dump/p.*.txt id radius x y z vx vy vz\n"
    deck += f"""variable nprev equal {10 ** 9}
variable k loop {nchunks}
label chunk
  run {chunk}
  variable nnow equal ${{nc}}
  if "${{t}} > 0.075 && ${{nnow}} == ${{nprev}}" then "jump SELF done"
  variable nprev equal ${{nnow}}
  next k
jump SELF chunk
label done
write_dump all custom final.txt id radius x y z vx vy vz
"""
    # the jam test compares ncup over 0.025 s chunks; two equal successive counts = no grain left for 0.025 s
    with open(os.path.join(rd, "in.dis"), "w") as f:
        f.write(deck)
    shutil.copy(os.path.join(rd, "in.dis"), os.path.join(L.HERE, "decks", f"in.{TEST}_{case}_D{D_mm:g}"))
    rc, wall, tail = L.run_liggghts(rd, "in.dis")
    L.write_json(os.path.join(rd, "run.json"), dict(rc=rc, wall_s=wall, dt=dt))
    if rc != 0:
        print(tail)


def analyze(case, wd):
    fj = L.read_json(os.path.join(wd, "fill.json"), {})
    _, d0 = L.read_dump(os.path.join(wd, "fill_end.txt"))
    vol = 4 / 3 * math.pi * d0["radius"] ** 3
    # bed packing from the bed height (mean top in 1 mm columns away from the wall)
    top = d0["z"] + d0["radius"]
    g = 1e-3
    keys = (np.floor(d0["x"] / g).astype(int) + 500) * 1000 + np.floor(d0["y"] / g).astype(int) + 500
    hs = [top[keys == k].max() for k in np.unique(keys)
          if math.hypot((k // 1000 - 500 + 0.5) * g, (k % 1000 - 500 + 0.5) * g) < RCUP - 1e-3]
    hbed = float(np.mean(hs))
    phi_b = float(vol.sum() / (math.pi * RCUP ** 2 * hbed))
    rho_b = phi_b * L.SALT["density"]
    out = dict(case=case, ced=CED[case], n_grains=fj.get("n"), fill_wall_s=fj.get("wall_s"), bed_height_mm=hbed * 1e3,
               phi_bed=phi_b, rho_bulk_kg_m3=rho_b, orifices=[])
    for rd in sorted(glob.glob(os.path.join(wd, "D*")), key=lambda p: float(os.path.basename(p)[1:])):
        D_mm = float(os.path.basename(rd)[1:])
        mp = os.path.join(rd, "mass.txt")
        if not os.path.exists(mp):
            continue
        A = np.loadtxt(mp, skiprows=1, ndmin=2)
        if len(A) < 5:
            continue
        t, m, nc = A[:, 0], A[:, 1], A[:, 2]
        out_m = m[0] - m
        rj = L.read_json(os.path.join(rd, "run.json"), {})
        n_out = int(nc[0] - nc[-1])
        win = (t > 0.05) & (t <= t[-1])
        rate = float(np.polyfit(t[win], out_m[win], 1)[0]) if win.sum() > 10 else 0.0
        # steadiness: rates in 25 ms windows after 0.05 s
        wr = []
        for a in np.arange(0.05, t[-1] - 0.025 + 1e-9, 0.025):
            mm = (t >= a) & (t < a + 0.025)
            if mm.sum() > 3:
                wr.append(float(np.polyfit(t[mm], out_m[mm], 1)[0]))
        last = (t > t[-1] - 0.05)
        jammed = bool(t[-1] < T_RUN.get(D_mm, 0.3) - 0.03 or (np.ptp(nc[last]) == 0 and t[-1] > 0.1))
        out["orifices"].append(dict(D_mm=D_mm, D_over_d50=D_mm / 0.425, t_end_s=float(t[-1]),
                                    grains_out=n_out, mass_out_g=float(out_m[-1] * 1e3),
                                    flow_rate_g_s=rate * 1e3 if not jammed else 0.0,
                                    flow_rate_before_jam_g_s=rate * 1e3,
                                    window_rates_g_s=[w * 1e3 for w in wr], jammed=jammed,
                                    wall_s=rj.get("wall_s")))
    # Beverloo fit on flowing orifices: W^0.4 = A (D - k d), W = C rho_b sqrt(g) (D - k d)^2.5
    fl = [o for o in out["orifices"] if not o["jammed"] and o["flow_rate_g_s"] > 0]
    if len(fl) >= 2:
        Dm = np.array([o["D_mm"] * 1e-3 for o in fl])
        W = np.array([o["flow_rate_g_s"] * 1e-3 for o in fl])
        p = np.polyfit(Dm, W ** 0.4, 1)
        k = -p[1] / p[0] / L.D50
        C = p[0] ** 2.5 / (rho_b * math.sqrt(9.81))
        out["beverloo"] = dict(C=float(C), k=float(k), d_m=L.D50, rho_b=rho_b, n_points=len(fl))
    jam = [o["D_mm"] for o in out["orifices"] if o["jammed"]]
    flow = [o["D_mm"] for o in out["orifices"] if not o["jammed"]]
    if jam:
        Dj = max(jam)
        bigger = [x for x in flow if x > Dj]
        out["D_c_bracket_mm"] = [Dj, min(bigger) if bigger else None]
        Dc = 0.5 * (Dj + min(bigger)) if bigger else Dj
        out["sigma_c_jenike_Pa"] = rho_b * 9.81 * Dc * 1e-3 / 2.2
    # animation frames
    ad = os.path.join(wd, f"D{ANIM_D:g}")
    files = L.dump_series(os.path.join(ad, "dump", "p.*.txt"))
    if files:
        frames, ts = [], []
        _, f0 = L.read_dump(files[0])
        slab_ids = set(f0["id"][np.abs(f0["y"]) < 2.0e-3].astype(int).tolist())
        dtj = L.read_json(os.path.join(ad, "run.json"), {}).get("dt", L.default_dt())
        step0 = None
        for fp in files:
            step, d = L.read_dump(fp)
            step0 = step if step0 is None else step0
            m = np.isin(d["id"].astype(int), list(slab_ids))
            frames.append({k: d[k][m] for k in ("id", "x", "y", "z", "radius")})
            ts.append((step - step0) * dtj)
        out["frames_npz_bytes"] = L.save_frames(
            os.path.join(L.HERE, "frames", f"{TEST}_{case}.npz"), ts, frames, max_frames=80,
            extra=dict(orifice_D_mm=np.float32(ANIM_D), cup_R_mm=np.float32(RCUP * 1e3),
                       note=np.array("grains in the slab |y| < 2 mm at the gate opening only; t = 0 at opening")))
    return out


def main():
    mode, case = sys.argv[1], sys.argv[2]
    wd = os.path.join(L.SCRATCH, TEST, case)
    if mode == "fill":
        fill(case, wd)
    elif mode == "run":
        for D in [float(x) for x in sys.argv[3:]]:
            discharge(case, D, wd)
    res = analyze(case, wd)
    L.write_json(os.path.join(L.HERE, "results", f"{TEST}_{case}.json"), res)
    print({k: res.get(k) for k in ("case", "phi_bed", "beverloo", "D_c_bracket_mm")},
          [(o["D_mm"], round(o["flow_rate_g_s"], 3), o["jammed"]) for o in res["orifices"]])


if __name__ == "__main__":
    main()
