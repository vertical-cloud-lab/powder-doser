"""v4 station (augers outside the loop): the auger-side Kelvin dock against tilt 0-50 deg, and the lift off the tube rest.

    python sim/dock_v4.py        # writes sim/results/dock_v4.json and dock_v4.png (seconds)

Same model as ../../chain-carousel-v3/sim/dock_statics.py (it loads its kelvin.py and the seat-magnet curve):
* EC v4 on the plate's auger-side face through a cone (A), a vee (B, two 1/8 in dowels) and ball C on a steel washer.
* Three D44-N52 seat magnets (behind the cone, beyond the vee's dowels, behind ball C); no electromagnet in v4.
* The P16 pushes along its rod (pinned both ends) and carries the module + EC about the hinge; module empty (worst case).
* Gear mesh on the auger's far side: separating force pushes the EC away from the plate, tangential = separating / 0.55.
* Three thresholds per tilt: a ball lifts off (sideways slip ignored, v2's criterion); slip with friction (0.25 cone,
  0.15 steel on steel, best case); frictionless (exact Kelvin clamp, worst case).
"""
from __future__ import annotations

import importlib.util
import json
import math
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
V3SIM = HERE.parent.parent / "chain-carousel-v3" / "sim"
sys.path.insert(0, str(HERE.parent))
_spec = importlib.util.spec_from_file_location("kelvin_v3sim", V3SIM / "kelvin.py")
K = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(K)
import layout as L  # noqa: E402
from params import *  # noqa: E402,F401,F403

OUT = HERE / "results"
G = 9.81
CURVE = json.loads((V3SIM / "results" / "magnet_curve_cache.json").read_text())
_CG = np.array([c["gap_mm"] for c in CURVE])
_CF = np.array([c["pull_kj_scaled_N"] for c in CURVE])
pull = lambda g: float(np.interp(g, _CG, _CF))

# module: v3's module (dock_statics.py) in Sam's frame; EC v4 = EC v3 mirrored z -> -z, no coil, the two arms, a third magnet
M_MOD, C_MOD = 0.1271, np.array([90.1, 0.0, -5.1])
EC_PARTS = [
    ("EC v3 (dock_statics.py), mirrored", 0.3111, (51.9, -0.1, 34.2)),
    ("minus the coil and its bracket (v2's 27 g)", -0.027, (100.0, 0.0, 28.0)),
    ("minus v3's ears and ball C boss", -0.0038, (60.0, 0.0, 27.0)),
    ("two arms past the auger, 13.2 cm^3 PETG", 0.0168, (47.0, 8.0, 10.0)),
    ("third D44-N52 (behind ball C)", 0.0015, (64.0, 19.5, -2.0)),
]
M_EC = sum(p[1] for p in EC_PARTS)
C_EC = sum(p[1] * np.array(p[2]) for p in EC_PARTS) / M_EC + np.array([0, 0, DOCK_RISE_V4])

R_B = KC_BALL_D / 2
ZB = KC4_BALL_Z
H_VEE = math.sqrt((R_B + VEE_DOWEL_D / 2) ** 2 - (VEE_SPACING / 2) ** 2)
GEOM = dict(
    A=(KC4_A[0], KC4_A[1], ZB), B=(KC4_B[0], KC4_B[1], ZB), C=(KC4_C[0], KC4_C[1], -13.0 + KC4_PAD[1]),
    axis=np.array([0, 0, -1.0]),                       # from the EC toward the plate
    vee=[np.array([s * VEE_SPACING / 2, 0, H_VEE]) / math.hypot(VEE_SPACING / 2, H_VEE) for s in (-1, 1)],
    c_dir=np.array([0, 0, 1.0]),
)
GAPS = dict(A=KC_MAG_GAP, B=H_VEE + VEE_DOWEL_D / 2 + 0.4 + 0.1 - R_B, C=KC_MAG_GAP)
MAGS = dict(A=(KC4_A[0], KC4_A[1], ZB + R_B + KC_MAG_GAP), B=(KC4_B[0], KC4_B[1], ZB + H_VEE + VEE_DOWEL_D / 2 + 0.5),
            C=(KC4_C[0], KC4_C[1], -12.0 + KC_BALL_D + 0.5))
MESH_PT = (GEAR_X + 5.0, 0.0, 22.0)
PIN = np.array([EC_PIN[0], 0.0, -EC_PIN[1] + DOCK_RISE_V4])
F_STALL_SEP = 0.067 / 0.010 * SEP_RATIO_STEEL
MU = dict(liftoff=(50.0, 50.0), friction=(0.25, 0.15), frictionless=(0.0, 0.0))


def frames(tilt):
    M = L.sam_frame(L.station_frame(), tilt)
    return M[:3, :3], M[:3, 3]


B_PIN = L.actuator_pins(0.0, 0.0)[0]


def loads_at(tilt, F_sep, sgn, seat_scale=1.0, c_pull=None, powder=0.0):
    R, t = frames(tilt)
    g = np.array([0, 0, -G])
    a = R @ GEOM["axis"]
    loads = [(C_EC, M_EC * g)]
    for k in ("A", "B", "C"):
        f = pull(GAPS[k]) * seat_scale
        if k == "C" and c_pull is not None:
            f = c_pull
        loads.append((MAGS[k], f * a))
    loads.append((MESH_PT, -F_sep * a + sgn * F_sep / SEP_RATIO_STEEL * (R @ np.array([0, 1.0, 0]))))
    # the P16 carries the module and the EC about the hinge axis
    m_mod = M_MOD + powder
    c_mod = (C_MOD * M_MOD + np.array([125.0, 0, -4.0]) * powder) / m_mod
    ax = R @ np.array([0, 1.0, 0])
    P = R @ PIN + t
    u = (P - B_PIN) / np.linalg.norm(P - B_PIN)
    Mg = np.cross(R @ c_mod, m_mod * g) @ ax + np.cross(R @ C_EC, M_EC * g) @ ax
    F_act = -Mg / (np.cross(P - t, u) @ ax)
    loads.append((tuple(PIN), F_act * u))
    return R, t, loads, F_act


def threshold(tilt, mode, **kw):
    mc, ms = MU[mode]
    worst, Fa = 40.0, 0.0
    for sgn in (-1, 1):
        def ok(F):
            R, t, loads, fa = loads_at(tilt, F, sgn, **kw)
            return K.lp_holds(R, t, GEOM, loads, t, mc, ms), fa
        h0, Fa = ok(0.0)
        if not h0:
            return 0.0, Fa
        lo, hi = 0.0, 40.0
        if ok(hi)[0]:
            continue
        for _ in range(14):
            mid = 0.5 * (lo + hi)
            lo, hi = (mid, hi) if ok(mid)[0] else (lo, mid)
        worst = min(worst, lo)
    return round(worst, 2), Fa


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    res = dict(ec_v4_kg=round(M_EC, 4), ec_v4_com_mm=[round(float(v), 1) for v in C_EC], ec_parts=EC_PARTS,
               module_kg=M_MOD, seat_gaps_mm={k: round(v, 2) for k, v in GAPS.items()},
               seat_pulls_N={k: round(pull(v), 2) for k, v in GAPS.items()}, F_stall_sep_N=round(F_STALL_SEP, 2))
    # lift off the tube rest at tilt 0: the P16 force that carries the module and the EC (latch open, rest 0.5 mm below)
    R, t, loads, Fa = loads_at(0.0, 0.0, 1)
    res["lift_off_rest"] = dict(F_act_N=round(float(Fa), 2), module_weight_N=round(M_MOD * G, 2),
                                note="the P16 lifts the EC and the module 0.5 mm off the tube rest; the module's weight presses the plate onto the EC's seats")
    rows = []
    for name, kw in {"seat magnets (A, B, C)": {}, "no seat magnets (weight only)": dict(seat_scale=0.0),
                     "ball C's magnet doubtful (C 0 N)": dict(c_pull=0.0)}.items():
        for tl in (0.0, 10.0, 20.0, 30.0, 40.0, 50.0):
            r = dict(case=name, tilt_deg=tl)
            for mode in ("liftoff", "friction", "frictionless"):
                F, Fa = threshold(tl, mode, **kw)
                r[f"F_open_{mode}_N"] = F
            r["F_act_N"] = round(float(Fa), 2)
            r["motor_stalls_first_liftoff"] = bool(r["F_open_liftoff_N"] > F_STALL_SEP)
            r["motor_stalls_first_friction"] = bool(r["F_open_friction_N"] > F_STALL_SEP)
            rows.append(r)
            print(r, flush=True)
    res["rows"] = rows
    (OUT / "dock_v4.json").write_text(json.dumps(res, indent=1) + "\n")
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(8, 4.8))
    for name, col in (("seat magnets (A, B, C)", "#1f5fbf"), ("no seat magnets (weight only)", "#6b6b6b"), ("ball C's magnet doubtful (C 0 N)", "#d0661a")):
        r = [x for x in rows if x["case"] == name]
        ax.plot([x["tilt_deg"] for x in r], [x["F_open_liftoff_N"] for x in r], "-o", ms=4, color=col, label=f"{name}: a ball lifts off")
        ax.plot([x["tilt_deg"] for x in r], [x["F_open_friction_N"] for x in r], "--s", ms=3, color=col, label=f"{name}: slides (mu 0.25/0.15)")
    ax.axhline(F_STALL_SEP, color="#b00020", lw=1.2)
    ax.text(1, F_STALL_SEP + 0.3, f"NEMA 11 stall at 450 mA: {F_STALL_SEP:.1f} N", color="#b00020", fontsize=9)
    ax.set_xlabel("tilt (deg)")
    ax.set_ylabel("separating force at the mesh that opens the dock (N)")
    ax.set_title("v4 auger-side dock: holding against tilt (empty module, P16 pushing)", fontsize=10)
    ax.grid(alpha=0.3)
    ax.set_ylim(0, None)
    ax.legend(fontsize=7)
    fig.tight_layout()
    fig.savefig(OUT / "dock_v4.png", dpi=110)


if __name__ == "__main__":
    main()
