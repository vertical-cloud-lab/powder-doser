"""Plane shear cell (an unrolled Schulze ring-shear cell) with LIGGGHTS-PUBLIC 3.8.

Laterally periodic box (6.8 x 3.4 mm). Bottom: a frozen layer of grains (rough wall).
Lid: a layer of grains whose x,y motion is prescribed (fix move linear vx 0 NULL) and whose
z motion is free under a constant applied normal force (fix aveforce) -> constant normal stress.
Gravity is switched off after filling, so the normal stress is uniform (as in a kPa-loaded cell).
Shear stress and normal stress are read from the contact forces on the frozen bottom layer.

Schulze/Jenike procedure: pre-shear at SIG_PRE to steady state, stop, unload to SIG_I < SIG_PRE,
shear to failure (peak) -> one yield-locus point; repeat for each SIG_I.

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

SCRATCH = os.environ.get("SCRATCH", "/tmp/sims-scratch/dem-liggghts-shear")
A_LAT = 0.425e-3                 # wall-grain lattice spacing = wall grain diameter
NX, NY = 16, 8
LX, LY = NX * A_LAT, NY * A_LAT
AREA = LX * LY
N_BULK = 1800
SIG_PRE = 200.0                  # Pa, pre-shear normal stress
SIG_I = [50.0, 100.0, 150.0]     # Pa, shear-to-failure normal stresses
V_SHEAR = 0.01                   # m/s
T_SETTLE, T_CONS, T_PRE, T_RELAX, T_SHEAR = 0.15, 0.20, 0.25, 0.04, 0.20
K_LID = 24                       # lid layer index (z = (K+0.5)*a)


def build(variant, wd):
    os.makedirs(os.path.join(wd, "dump"), exist_ok=True)
    ced = L.CED_COHESIVE if variant == "coh" else 0.0
    box = (0.0, LX, 0.0, LY, 0.0, 12e-3)
    head, wall_model, dt = L.header(box, periodic="p p f", ced=ced, gravity=False)
    steps = lambda s: int(round(s / dt))  # noqa: E731
    n_lid = NX * NY
    f_pre = SIG_PRE * AREA / n_lid
    gam = 1.2e-3   # lid dashpot (N s/m per grain): terminal approach speed ~ F/gamma
    zl0, zl1 = K_LID * A_LAT, (K_LID + 1) * A_LAT
    sched = []
    t = 0.0

    def ph(name, dur, sig=None, v=0.0):
        nonlocal t
        sched.append(dict(name=name, t0=t, t1=t + dur, sigma=sig, v=v))
        t += dur
    deck = head + f"""
lattice sc {A_LAT:.6e} origin 0.5 0.5 0.5
region botlayer block 0. {LX:.6e} 0. {LY:.6e} 0. {A_LAT:.6e} units box
create_atoms 1 region botlayer
group bot region botlayer
region lidlayer block 0. {LX:.6e} 0. {LY:.6e} {zl0:.6e} {zl1:.6e} units box
create_atoms 1 region lidlayer
group lid region lidlayer
set group bot diameter {A_LAT:.6e}
set group bot density {L.SALT['density']}
set group lid diameter {A_LAT:.6e}
set group lid density {L.SALT['density']}
region insreg block 0. {LX:.6e} 0. {LY:.6e} 0.7e-3 {zl0 - 0.5e-3:.6e} units box
group bulk region insreg
fix ins bulk insert/pack seed 86028157 distributiontemplate pdd insert_every once overlapcheck yes all_in yes particles_in_region {N_BULK} region insreg ntry_mc 20000
fix integr bulk nve/sphere
fix gravi bulk gravity 9.81 vector 0.0 0.0 -1.0
fix lidmove lid move linear 0.0 0.0 0.0
compute fbot bot reduce sum fx fy fz
compute zlid lid reduce ave z
variable t equal time
variable tau equal c_fbot[1]/{AREA:.6e}
variable sig equal -c_fbot[3]/{AREA:.6e}
variable zl equal c_zlid
thermo_style custom step time atoms c_fbot[1] c_fbot[3] c_zlid
thermo {steps(0.05)}
thermo_modify lost ignore norm no flush yes
run 1
fix logs all print {steps(0.001)} "${{t}} ${{tau}} ${{sig}} ${{zl}}" file stress.txt screen no title "t tau sig zlid"
dump dmp all custom {steps(0.01)} dump/p.*.txt id type radius x y z vx vy vz
"""
    ph("settle", T_SETTLE)
    deck += f"run {steps(T_SETTLE)}\nunfix gravi\nunfix lidmove\n"
    deck += f"fix lidmove lid move linear 0.0 0.0 NULL\nfix lidvisc lid viscous {gam}\nfix lidload lid aveforce NULL NULL {-f_pre:.6e}\n"
    ph("consolidate", T_CONS, SIG_PRE)
    deck += f"run {steps(T_CONS)}\n"
    for i, s in enumerate(SIG_I):
        deck += f"unfix lidmove\nfix lidmove lid move linear {V_SHEAR} 0.0 NULL\n"
        ph(f"preshear{i}", T_PRE, SIG_PRE, V_SHEAR)
        deck += f"run {steps(T_PRE)}\n"
        fi = s * AREA / n_lid
        deck += f"unfix lidmove\nfix lidmove lid move linear 0.0 0.0 NULL\nunfix lidload\nfix lidload lid aveforce NULL NULL {-fi:.6e}\n"
        ph(f"relax{i}", T_RELAX, s)
        deck += f"run {steps(T_RELAX)}\n"
        deck += f"unfix lidmove\nfix lidmove lid move linear {V_SHEAR} 0.0 NULL\n"
        ph(f"shear{i}", T_SHEAR, s, V_SHEAR)
        deck += f"run {steps(T_SHEAR)}\n"
        deck += f"unfix lidload\nfix lidload lid aveforce NULL NULL {-f_pre:.6e}\n"
    # final pre-shear so that every shear point has a pre-shear before it and one after
    deck += f"unfix lidmove\nfix lidmove lid move linear {V_SHEAR} 0.0 NULL\n"
    ph("preshear3", T_PRE, SIG_PRE, V_SHEAR)
    deck += f"run {steps(T_PRE)}\n"
    with open(os.path.join(wd, "in.shear"), "w") as f:
        f.write(deck)
    L.write_json(os.path.join(wd, "schedule.json"), sched)
    return dt, sched


def smooth(y, n):
    if n <= 1:
        return y
    k = np.ones(n) / n
    return np.convolve(y, k, mode="same")


def analyze(wd, sched):
    A = np.loadtxt(os.path.join(wd, "stress.txt"), skiprows=1)
    t, tau, sig = A[:, 0], A[:, 1], A[:, 2]
    taus = smooth(tau, 9)
    out = {"pre": [], "points": []}
    for p in sched:
        m = (t >= p["t0"]) & (t < p["t1"])
        if p["name"].startswith("preshear"):
            mm = m & (t > p["t1"] - 0.08)
            out["pre"].append(dict(sigma_set=p["sigma"], sigma_meas=float(np.mean(sig[mm])), tau_ss=float(np.mean(tau[mm])),
                                   tau_ss_std=float(np.std(taus[mm]))))
        if p["name"].startswith("shear"):
            i = np.argmax(np.where(m, taus, -np.inf))
            mm = m & (t > p["t1"] - 0.06)
            out["points"].append(dict(sigma_set=p["sigma"], sigma_meas_at_peak=float(np.mean(sig[max(0, i - 15):i + 15])),
                                      tau_peak=float(taus[i]), t_peak_after_start=float(t[i] - p["t0"]),
                                      tau_end=float(np.mean(tau[mm]))))
    s = np.array([q["sigma_meas_at_peak"] for q in out["points"]])
    tp = np.array([q["tau_peak"] for q in out["points"]])
    slope, c = np.polyfit(s, tp, 1)
    phi = math.degrees(math.atan(slope))
    out["yield_locus"] = dict(cohesion_Pa=float(c), tan_phi=float(slope), phi_i_deg=float(phi))
    sp = np.mean([q["sigma_meas"] for q in out["pre"]])
    tpre = np.mean([q["tau_ss"] for q in out["pre"]])
    out["preshear_point"] = dict(sigma_Pa=float(sp), tau_Pa=float(tpre))
    # Mohr circles for a linear yield locus tau = c + sigma*tan(phi):
    # unconfined yield strength: circle through the origin tangent to the locus
    sphi = math.sin(math.radians(phi))
    cphi = math.cos(math.radians(phi))
    sig_c = 2 * c * cphi / (1 - sphi) if c > 0 else 0.0
    # major consolidation stress: circle through the pre-shear point, tangent to the locus.
    # centre p, radius R = (p + c/tan(phi))*sin(phi); require (sp-p)^2 + tpre^2 = R^2 -> solve for p
    a_ = c / slope
    # (sp - p)^2 + tpre^2 = (p + a_)^2 sphi^2
    qa = 1 - sphi ** 2
    qb = -2 * sp - 2 * a_ * sphi ** 2
    qc = sp ** 2 + tpre ** 2 - a_ ** 2 * sphi ** 2
    disc = qb ** 2 - 4 * qa * qc
    if disc >= 0:
        pc = (-qb + math.sqrt(disc)) / (2 * qa)   # larger root: circle on the consolidated side
        Rr = (pc + a_) * sphi
        sig1 = pc + Rr
    else:
        pc, Rr, sig1 = float("nan"), float("nan"), float("nan")
    ffc = sig1 / sig_c if sig_c > 0 else float("inf")
    out["mohr"] = dict(sigma_c_Pa=float(sig_c), sigma_1_Pa=float(sig1), centre_Pa=float(pc), radius_Pa=float(Rr),
                       ffc=(None if not math.isfinite(ffc) else float(ffc)))
    return out, (t, tau, sig)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("variant")
    ap.add_argument("--analyze-only", action="store_true")
    a = ap.parse_args()
    wd = os.path.join(SCRATCH, a.variant)
    os.makedirs(wd, exist_ok=True)
    dt, sched = build(a.variant, wd)
    res = {"variant": a.variant, "dt": dt}
    runjson = os.path.join(wd, "run.json")
    if not a.analyze_only:
        rc, wall, tail = L.run_liggghts(wd, "in.shear")
        res.update(rc=rc, wall_s=wall)
        if rc != 0:
            res["error_tail"] = tail[-2500:]
            L.write_json(runjson, res)
            print(tail[-2500:])
            sys.exit(rc)
    elif os.path.exists(runjson):
        res.update({k: v for k, v in json.load(open(runjson)).items() if k in ("rc", "wall_s")})
    out, _ = analyze(wd, sched)
    res.update(out)
    L.write_json(runjson, res)
    print(json.dumps({k: res[k] for k in ("yield_locus", "preshear_point", "mohr")}, indent=1))


if __name__ == "__main__":
    main()
