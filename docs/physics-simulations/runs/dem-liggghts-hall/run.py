"""Hall (ASTM B213) and Carney (ASTM B964) funnel discharge with LIGGGHTS-PUBLIC 3.8, reduced scale.

60 deg included-angle cone with a 3.2 mm long cylindrical orifice (2.54 mm Hall, 5.08 mm Carney),
truncated at a reduced top radius and topped by a short cylinder. Grains rain in with the
orifice plugged, settle, then the plug is removed. A counting disk 1.8 mm below the orifice
(fix massflow/mesh, count once, delete atoms) gives the discharged mass vs time.

usage: python run.py CASE [--analyze-only]    CASE = hall | carney | hall_coh
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

SCRATCH = os.environ.get("SCRATCH", "/tmp/sims-scratch/dem-liggghts-hall")
CASES = {
    #           orifice D, top radius, cylinder height, grains, discharge time
    "hall":     dict(D0=2.54e-3, Rtop=7.0e-3, Hcyl=6.0e-3, N=5000, t_dis=0.6, ced=0.0),
    "carney":   dict(D0=5.08e-3, Rtop=9.0e-3, Hcyl=8.5e-3, N=12000, t_dis=0.3, ced=0.0),
    "hall_coh": dict(D0=2.54e-3, Rtop=7.0e-3, Hcyl=6.0e-3, N=5000, t_dis=0.6, ced=L.CED_COHESIVE),
}
STEM = 3.2e-3
HALF_ANGLE = math.radians(30.0)
T_FILL = 0.25


def funnel_stl(path, r0, Rtop, Hcyl, n=72):
    Hc = (Rtop - r0) / math.tan(HALF_ANGLE)
    rings = [(r0, -STEM), (r0, 0.0), (Rtop, Hc), (Rtop, Hc + Hcyl)]
    tris = []
    for (ra, za), (rb, zb) in zip(rings[:-1], rings[1:]):
        for i in range(n):
            a0, a1 = 2 * math.pi * i / n, 2 * math.pi * (i + 1) / n
            p00 = (ra * math.cos(a0), ra * math.sin(a0), za)
            p01 = (ra * math.cos(a1), ra * math.sin(a1), za)
            p10 = (rb * math.cos(a0), rb * math.sin(a0), zb)
            p11 = (rb * math.cos(a1), rb * math.sin(a1), zb)
            tris += [(p00, p01, p11), (p00, p11, p10)]
    with open(path, "w") as f:
        f.write("solid funnel\n")
        for t in tris:
            f.write("facet normal 0 0 0\nouter loop\n")
            for q in t:
                f.write(f"vertex {q[0]:.6e} {q[1]:.6e} {q[2]:.6e}\n")
            f.write("endloop\nendfacet\n")
        f.write("endsolid funnel\n")
    return Hc


def disk_stl(path, R, z, n=48):
    with open(path, "w") as f:
        f.write("solid disk\n")
        for i in range(n):
            a0, a1 = 2 * math.pi * i / n, 2 * math.pi * (i + 1) / n
            p = [(0, 0, z), (R * math.cos(a0), R * math.sin(a0), z), (R * math.cos(a1), R * math.sin(a1), z)]
            f.write("facet normal 0 0 1\nouter loop\n")
            for q in p:
                f.write(f"vertex {q[0]:.6e} {q[1]:.6e} {q[2]:.6e}\n")
            f.write("endloop\nendfacet\n")
        f.write("endsolid disk\n")


def build(case, wd):
    c = CASES[case]
    os.makedirs(os.path.join(wd, "dump"), exist_ok=True)
    r0 = 0.5 * c["D0"]
    Hc = funnel_stl(os.path.join(wd, "funnel.stl"), r0, c["Rtop"], c["Hcyl"])
    z_out = -STEM - 1.8e-3
    disk_stl(os.path.join(wd, "outlet.stl"), c["Rtop"], z_out)
    R = c["Rtop"] + 1e-3
    box = (-R, R, -R, R, z_out - 1.5e-3, Hc + c["Hcyl"] + 1e-3)
    head, wall_model, dt = L.header(box, ced=c["ced"])
    steps = lambda s: int(round(s / dt))  # noqa: E731
    deck = head + f"""
fix funnel all mesh/surface file funnel.stl type 2 curvature_tolerant yes
fix outlet all mesh/surface/planar file outlet.stl type 2
fix walls all wall/gran {wall_model} mesh n_meshes 1 meshes funnel
fix plug all wall/gran {wall_model} primitive type 2 zplane {-STEM:.6e}
region fillreg cylinder z 0. 0. {c['Rtop'] - 0.4e-3:.6e} {Hc + 0.3e-3:.6e} {Hc + c['Hcyl'] - 0.3e-3:.6e} units box
fix ins all insert/pack seed 86028157 distributiontemplate pdd insert_every once overlapcheck yes all_in yes particles_in_region {c['N']} region fillreg ntry_mc 20000
fix integr all nve/sphere
fix mf all massflow/mesh mesh outlet vec_side 0. 0. -1. count once delete_atoms yes
variable t equal time
variable mout equal f_mf[1]
variable nout equal f_mf[2]
variable n equal atoms
thermo_style custom step time atoms f_mf[1] ke
thermo {steps(0.05)}
thermo_modify lost ignore norm no flush yes
fix logmf all print {steps(0.002)} "${{t}} ${{mout}} ${{nout}} ${{n}}" file outflow.txt screen no
dump dmp all custom {steps(0.02)} dump/p.*.txt id type radius x y z vx vy vz
run {steps(T_FILL)}
unfix plug
print "PHASE open t=${{t}}"
run {steps(c['t_dis'])}
"""
    with open(os.path.join(wd, "in.funnel"), "w") as f:
        f.write(deck)
    return dt, Hc


def beverloo(D0, d, rho_b, C=0.58, k=1.5, g=9.81):
    return C * rho_b * math.sqrt(g) * max(D0 - k * d, 0.0) ** 2.5


def analyze(case, wd, rho_b):
    c = CASES[case]
    A = np.loadtxt(os.path.join(wd, "outflow.txt"))
    t, m, nout, n = A[:, 0], A[:, 1], A[:, 2], A[:, 3]
    t_open = T_FILL
    tt = t - t_open
    win = (tt > 0.05) & (tt <= c["t_dis"] - 0.02)
    out = dict(m_out_total_g=float(m[-1] * 1e3), n_out_total=int(nout[-1]), n_left=int(n[-1]))
    if win.sum() > 5 and m[win][-1] > m[win][0]:
        p = np.polyfit(tt[win], m[win], 1)
        W = float(p[0])
        # windowed rates (25 ms) for unsteadiness / jamming
        edges = np.arange(0.05, c["t_dis"] - 0.02 + 1e-9, 0.025)
        rates = [float((np.interp(b, tt, m) - np.interp(a, tt, m)) / (b - a)) for a, b in zip(edges[:-1], edges[1:])]
        out.update(W_g_s=W * 1e3, t50_s=50e-3 / W if W > 0 else None, rates_25ms_g_s=[r * 1e3 for r in rates],
                   n_windows_zero=int(sum(1 for r in rates if r <= 0)))
    else:
        out.update(W_g_s=0.0, t50_s=None, rates_25ms_g_s=[], n_windows_zero=None)
    # jam: no grain crossed the counter in the last 0.1 s while grains remain
    last = tt > c["t_dis"] - 0.1
    out["jammed"] = bool(m[last][-1] - m[last][0] <= 0 and n[-1] > 0)
    d_mean = 0.425e-3
    out["beverloo"] = {f"k={k}": beverloo(c["D0"], d_mean, rho_b, k=k) * 1e3 for k in (1.5, 2.0, 2.9)}
    out["beverloo_rho_b"] = rho_b
    out["D0_over_d"] = c["D0"] / d_mean
    return out, (tt, m)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("case")
    ap.add_argument("--analyze-only", action="store_true")
    ap.add_argument("--rho-b", type=float, default=0.58 * L.SALT["density"])
    a = ap.parse_args()
    wd = os.path.join(SCRATCH, a.case)
    os.makedirs(wd, exist_ok=True)
    dt, Hc = build(a.case, wd)
    res = {"case": a.case, "dt": dt, "cone_height_mm": Hc * 1e3, **{k: v for k, v in CASES[a.case].items()}}
    runjson = os.path.join(wd, "run.json")
    if not a.analyze_only:
        rc, wall, tail = L.run_liggghts(wd, "in.funnel")
        res.update(rc=rc, wall_s=wall)
        if rc != 0:
            res["error_tail"] = tail[-2500:]
            L.write_json(runjson, res)
            print(tail[-2500:])
            sys.exit(rc)
    elif os.path.exists(runjson):
        res.update({k: v for k, v in json.load(open(runjson)).items() if k in ("rc", "wall_s")})
    out, _ = analyze(a.case, wd, a.rho_b)
    res.update(out)
    L.write_json(runjson, res)
    print({k: res.get(k) for k in ("case", "W_g_s", "t50_s", "jammed", "beverloo", "n_windows_zero", "m_out_total_g")})


if __name__ == "__main__":
    main()
