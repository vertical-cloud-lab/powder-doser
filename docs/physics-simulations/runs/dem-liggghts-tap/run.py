"""Apparent (poured) and tapped density with LIGGGHTS-PUBLIC 3.8 (ASTM B212 / B527 style, reduced scale).

Salt grains rain into a laterally periodic 5.1 x 5.1 mm column (no side walls, so no wall
layering) onto a flat floor. After settling, the bed is "tapped" NTAP times: each tap lifts the
whole bed rigidly by 3 mm (displace_atoms, contacts kept) and lets it free-fall onto the fixed
floor (impact 0.24 m/s, as for a 3 mm drop of a tap-density cylinder), then settle.
Packing fraction is measured in a slab away from floor and free surface.

usage: python run.py VARIANT [--analyze-only]    VARIANT = dry | coh
"""
import argparse
import json
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import ligcommon as L  # noqa: E402

SCRATCH = os.environ.get("SCRATCH", "/tmp/sims-scratch/dem-liggghts-tap")
LX = LY = 5.1e-3          # periodic cell (12 mean diameters)
N = 2500                  # grains
NTAP = 30
FILL = os.environ.get("TAP_FILL", "cloud")   # "cloud" (default) or "rain"
DROP = 3.0e-3             # m
T_FALL = math.sqrt(2 * DROP / 9.81)


def build(variant, wd):
    os.makedirs(os.path.join(wd, "dump"), exist_ok=True)
    ced = L.CED_COHESIVE if variant == "coh" else 0.0
    box = (0.0, LX, 0.0, LY, -0.5e-3, 30e-3)
    head, wall_model, dt = L.header(box, periodic="p p f", ced=ced)
    steps = lambda s: int(round(s / dt))  # noqa: E731
    rate = 10000
    t_pour = N / rate
    fill = FILL
    tap_settle = 0.05
    t_tap = T_FALL + tap_settle
    if fill == "rain":   # grains rain in from 20-28 mm at 10000 grains/s (first run: very dense, see README)
        fill_block = (f"region pour block 0. {LX:.6e} 0. {LY:.6e} 2.0e-2 2.8e-2 units box\n"
                      f"fix ins all insert/rate/region seed 86028157 distributiontemplate pdd nparticles {N} particlerate {rate} "
                      f"insert_every {steps(0.005)} overlapcheck yes all_in yes vel constant 0. 0. -0.3 region pour ntry_mc 5000")
    else:                # 'cloud': all grains placed at random (solid fraction 0.25) in 0.3-16.3 mm, then settle together
        fill_block = (f"region pour block 0. {LX:.6e} 0. {LY:.6e} 0.3e-3 16.3e-3 units box\n"
                      f"fix ins all insert/pack seed 86028157 distributiontemplate pdd insert_every once overlapcheck yes "
                      f"all_in yes particles_in_region {N} region pour ntry_mc 20000")
        t_pour = 0.15
    deck = head + f"""
fix floor all wall/gran {wall_model} primitive type 2 zplane 0.0
{fill_block}
fix integr all nve/sphere
variable t equal time
variable n equal atoms
variable zt equal bound(all,zmax)
variable ke equal ke
thermo_style custom step time atoms ke
thermo {steps(0.05)}
thermo_modify lost ignore norm no flush yes
fix logz all print {steps(0.002)} "${{t}} ${{n}} ${{zt}} ${{ke}}" file ztop.txt screen no
# --- pour (apparent density)
run {steps(t_pour + 0.12)}
unfix ins
run {steps(0.08)}
write_dump all custom dump/poured.txt id type radius x y z vx vy vz
dump dmp all custom {steps(0.01)} dump/p.*.txt id type radius x y z vx vy vz
dump_modify dmp first yes
# --- taps
label tap
variable i loop {NTAP}
  displace_atoms all move 0.0 0.0 {DROP:.4e} units box
  run {steps(t_tap)}
  write_dump all custom dump/tap_${{i}}.txt id type radius x y z vx vy vz
next i
jump SELF tap
"""
    with open(os.path.join(wd, "in.tap"), "w") as f:
        f.write(deck)
    return dt, t_tap


def slab_volume(z, r, z0, z1):
    """Exact volume of spheres (centre z, radius r) inside the slab z0<z<z1."""
    def below(h, r):  # volume of sphere below plane at height h relative to centre
        h = np.clip(h, -r, r)
        return math.pi * (r + h) ** 2 * (2 * r - h) / 3.0
    return np.sum(below(z1 - z, r) - below(z0 - z, r))


def packing(d):
    z, r = d["z"], d["radius"]
    keep = z < 25e-3
    z, r = z[keep], r[keep]
    # free-surface height: mean of the top grains in 1 mm columns
    x, y = d["x"][keep] % LX, d["y"][keep] % LY
    nb = 5
    ix = np.minimum((x / LX * nb).astype(int), nb - 1)
    iy = np.minimum((y / LY * nb).astype(int), nb - 1)
    tops = [np.max((z + r)[(ix == i) & (iy == j)]) for i in range(nb) for j in range(nb) if np.any((ix == i) & (iy == j))]
    H = float(np.mean(tops))
    z0, z1 = 1.0e-3, H - 1.0e-3
    phi_slab = slab_volume(z, r, z0, z1) / (LX * LY * (z1 - z0))
    vol = np.sum(4 / 3 * math.pi * r ** 3)
    phi_total = vol / (LX * LY * H)
    rho_b = phi_slab * L.SALT["density"]
    return dict(H_mm=H * 1e3, phi_slab=float(phi_slab), phi_overall=float(phi_total), rho_bulk=float(rho_b), n=int(len(z)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("variant")
    ap.add_argument("--analyze-only", action="store_true")
    a = ap.parse_args()
    wd = os.path.join(SCRATCH, a.variant if FILL == "cloud" else a.variant + "_rain")
    os.makedirs(wd, exist_ok=True)
    dt, t_tap = build(a.variant, wd)
    res = {"variant": a.variant, "dt": dt, "t_tap_s": t_tap}
    runjson = os.path.join(wd, "run.json")
    if not a.analyze_only:
        rc, wall, tail = L.run_liggghts(wd, "in.tap")
        res.update(rc=rc, wall_s=wall)
        if rc != 0:
            res["error_tail"] = tail[-2500:]
            L.write_json(runjson, res)
            print(tail[-2500:])
            sys.exit(rc)
    elif os.path.exists(runjson):
        res.update({k: v for k, v in json.load(open(runjson)).items() if k in ("rc", "wall_s")})
    _, d0 = L.read_dump(os.path.join(wd, "dump", "poured.txt"))
    p0 = packing(d0)
    taps = []
    for i in range(1, NTAP + 1):
        f = os.path.join(wd, "dump", f"tap_{i}.txt")
        if os.path.exists(f):
            taps.append(packing(L.read_dump(f)[1]))
    res["poured"] = p0
    res["taps"] = taps
    if taps:
        pt = np.mean([t["phi_slab"] for t in taps[-5:]])
        res["phi_bulk"] = p0["phi_slab"]
        res["phi_tapped_last5"] = float(pt)
        res["hausner"] = float(pt / p0["phi_slab"])
        res["carr_index_pct"] = float(100 * (1 - p0["phi_slab"] / pt))
        res["hausner_overall"] = float(np.mean([t["phi_overall"] for t in taps[-5:]]) / p0["phi_overall"])
    L.write_json(runjson, res)
    print({k: res.get(k) for k in ("variant", "phi_bulk", "phi_tapped_last5", "hausner", "carr_index_pct", "hausner_overall")})


if __name__ == "__main__":
    main()
