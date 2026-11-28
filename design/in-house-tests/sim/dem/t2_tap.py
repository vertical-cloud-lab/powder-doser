"""Test 2, doser fill and cam-drop taps in the 10 mL cylinder (SPEC.md section 2), LIGGGHTS-PUBLIC 3.8.

As designed: 13 mm bore (glass, wall friction taken as the reference 0.4), filled through the funnel
collar's 8 mm throat by the doser, then tapped with a 3.0 mm drop. Reduced: the column is about 6 mm
tall (10 000 grains, 0.9 g) instead of 36 mm (6 g); the stream enters 14-18 mm above the floor at
1.2 m/s, the speed of a 75 mm fall from the collar; the fill rate is 10 000 grains/s (0.9 g/s), about
10x the doser's. Each tap lifts the bed rigidly by 3 mm and lets it fall onto the floor (as #196 run 5),
then 0.030 s of settling (60 taps).

usage: python t2_tap.py run|analyze CASE     CASE = dry | coh
"""
import math
import os
import shutil
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import demlib as L  # noqa: E402

TEST = "t2_tap"
RC = 6.5e-3
N_FILL = 10000
RATE = 10000.0
V_IN = 1.2
Z_INS = (14e-3, 18e-3)
T_SETTLE = 0.3
NTAPS = 60
DROP = 3.0e-3
T_REST = 0.030
CED = {"dry": 0.0, "coh": L.CED_COH}



def build(case, wd):
    os.makedirs(os.path.join(wd, "dump"), exist_ok=True)
    box = (-RC - 0.3e-3, RC + 0.3e-3, -RC - 0.3e-3, RC + 0.3e-3, -0.5e-3, 22e-3)
    head, wm, dt = L.header(box, ced=CED[case])
    st = lambda s: max(1, int(round(s / dt)))  # noqa: E731
    t_fall = math.sqrt(2 * DROP / 9.81)
    deck = head + f"""
fix floor all wall/gran {wm} primitive type 2 zplane 0.0
fix cyl all wall/gran {wm} primitive type 2 zcylinder {RC:.5e} 0. 0.
region pour cylinder z 0. 0. 3.8e-3 {Z_INS[0]:.4e} {Z_INS[1]:.4e} units box
fix ins all insert/rate/region seed 86028157 distributiontemplate pdd nparticles {N_FILL} particlerate {RATE} insert_every {st(0.004)} overlapcheck yes all_in yes vel constant 0. 0. -{V_IN} region pour ntry_mc 5000
fix integr all nve/sphere
variable t equal time
variable n equal atoms
variable ke equal ke
thermo_style custom step time atoms ke
thermo {st(0.1)}
thermo_modify lost ignore norm no flush yes
fix logk all print {st(0.005)} "${{t}} ${{n}} ${{ke}}" file ke.txt screen no title "t n ke"
dump dmp all custom {st(0.04)} dump/fill.*.txt id radius x y z vx vy vz
run {st(N_FILL / RATE)}
unfix ins
run {st(T_SETTLE)}
undump dmp
write_dump all custom dump/tap_0.txt id radius x y z vx vy vz
label tap
variable i loop {NTAPS}
  displace_atoms all move 0.0 0.0 {DROP:.4e} units box
  run {st(t_fall + T_REST)}
  write_dump all custom dump/tap_${{i}}.txt id radius x y z vx vy vz
next i
jump SELF tap
"""
    with open(os.path.join(wd, "in.tap"), "w") as f:
        f.write(deck)
    return dict(dt=dt)


def packing(d):
    """Whole-column packing from the column height (as the camera reads it) and a slab value (#196 method)."""
    x, y, z, r = d["x"], d["y"], d["z"], d["radius"]
    vol = 4.0 / 3.0 * math.pi * r ** 3
    A = math.pi * RC ** 2
    # surface height: mean over 1 mm columns (inside r < RC - 0.5 mm) of the highest grain top
    top = z + r
    g = 1.0e-3
    ix, iy = np.floor(x / g).astype(int), np.floor(y / g).astype(int)
    keys = (ix + 500) * 1000 + (iy + 500)
    hs = []
    for k in np.unique(keys):
        m = keys == k
        cx, cy = (k // 1000 - 500 + 0.5) * g, (k % 1000 - 500 + 0.5) * g
        if math.hypot(cx, cy) < RC - 0.5e-3:
            hs.append(top[m].max())
    h = float(np.mean(hs)) if hs else float("nan")
    phi_col = vol.sum() / (A * h)
    # slab 1 mm above the floor to 1 mm below the surface, exact volume of spheres cut by planes
    lo, hi = 1.0e-3, h - 1.0e-3
    def cap(rr, hh):
        hh = np.clip(hh, 0, 2 * rr)
        return math.pi * hh ** 2 * (3 * rr - hh) / 3
    v = cap(r, hi - (z - r)) - cap(r, lo - (z - r))
    phi_slab = v.sum() / (A * (hi - lo)) if hi > lo else float("nan")
    return h, phi_col, phi_slab, vol.sum()


def kawakita(N, h):
    """C = (h0 - hN)/h0 = a b N / (1 + b N); linear fit of N/C against N (N >= 1)."""
    N = np.asarray(N, float)
    C = (h[0] - np.asarray(h)) / h[0]
    m = (N >= 1) & (C > 0)
    if m.sum() < 3:
        return None
    p = np.polyfit(N[m], N[m] / C[m], 1)
    a = 1 / p[0]
    b = 1 / (p[1] * a) if p[1] > 0 else float("inf")
    pred = a * b * N[m] / (1 + b * N[m])
    r2 = 1 - np.sum((C[m] - pred) ** 2) / np.sum((C[m] - C[m].mean()) ** 2)
    return dict(a=float(a), b=float(b), one_over_b_taps=float(1 / b), r2=float(r2))


def analyze(case, wd, meta):
    taps, hs, phc, phs, frames, ts = [], [], [], [], [], []
    fills = L.dump_series(os.path.join(wd, "dump", "fill.*.txt"))
    dt = meta["dt"]
    for fp in fills:
        step, d = L.read_dump(fp)
        frames.append({k: d[k] for k in ("id", "x", "y", "z", "radius")})
        ts.append(step * dt)
    t_end_fill = N_FILL / RATE + T_SETTLE
    for i in range(0, NTAPS + 1):
        fp = os.path.join(wd, "dump", f"tap_{i}.txt")
        if not os.path.exists(fp):
            break
        step, d = L.read_dump(fp)
        h, pc, ps, vs = packing(d)
        taps.append(i)
        hs.append(h)
        phc.append(pc)
        phs.append(ps)
        frames.append({k: d[k] for k in ("id", "x", "y", "z", "radius")})
        ts.append(step * dt)
    taps, hs, phc, phs = map(np.array, (taps, hs, phc, phs))
    rho = L.SALT["density"]
    last = taps >= max(taps.max() - 9, 1)
    out = dict(case=case, ced=CED[case], n_grains=N_FILL, bore_mm=2 * RC * 1e3, taps_done=int(taps.max()),
               column_h0_mm=float(hs[0] * 1e3), column_h_final_mm=float(hs[last].mean() * 1e3),
               phi_bulk_column=float(phc[0]), phi_tapped_column=float(phc[last].mean()),
               phi_tapped_column_sd=float(phc[last].std()),
               phi_bulk_slab=float(phs[0]), phi_tapped_slab=float(phs[last].mean()),
               rho_bulk_kg_m3=float(phc[0] * rho), rho_tapped_kg_m3=float(phc[last].mean() * rho),
               hausner_column=float(phc[last].mean() / phc[0]), hausner_slab=float(phs[last].mean() / phs[0]),
               carr_index_pct=float(100 * (1 - phc[0] / phc[last].mean())),
               kawakita=kawakita(taps, hs), series=dict(taps=taps.tolist(), h_mm=(hs * 1e3).tolist(),
                                                         phi_column=phc.tolist(), phi_slab=phs.tolist()),
               t_fill_end_s=t_end_fill)
    size = L.save_frames(os.path.join(L.HERE, "frames", f"{TEST}_{case}.npz"), ts, frames, max_frames=150,
                         extra=dict(tap_index=np.array([-1] * len(fills) + list(taps), dtype=np.int32),
                                    bore_R_mm=np.float32(RC * 1e3),
                                    note=np.array("frames before the taps are the fill (tap_index -1); then one "
                                                  "frame after each tap, at rest on the floor")))
    out["frames_npz_bytes"] = size
    return out


def main():
    mode, case = sys.argv[1], sys.argv[2]
    wd = os.path.join(L.SCRATCH, TEST, case)
    os.makedirs(wd, exist_ok=True)
    meta = build(case, wd)
    shutil.copy(os.path.join(wd, "in.tap"), os.path.join(L.HERE, "decks", f"in.{TEST}_{case}"))
    runinfo = L.read_json(os.path.join(wd, "run.json"), {})
    if mode == "run":
        rc, wall, tail = L.run_liggghts(wd, "in.tap")
        runinfo = dict(rc=rc, wall_s=wall)
        L.write_json(os.path.join(wd, "run.json"), runinfo)
        if rc != 0:
            print(tail)
    res = analyze(case, wd, meta)
    res.update(wall_s=runinfo.get("wall_s"), dt_s=meta["dt"])
    L.write_json(os.path.join(L.HERE, "results", f"{TEST}_{case}.json"), res)
    print({k: res[k] for k in ("case", "phi_bulk_column", "phi_tapped_column", "hausner_column", "hausner_slab",
                               "carr_index_pct", "kawakita", "taps_done", "wall_s")})


if __name__ == "__main__":
    main()
