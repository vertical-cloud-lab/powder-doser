"""v3 station: the seat magnets, the dock's holding against tilt, the outlet door and the plate latch.

    python sim/dock_statics.py          # writes sim/results/statics.json and the plots (a few minutes: the magnet integrals)

Runs (see sim/README.md):
  2. seat magnet pull on a 1/4 in ball against gap (cone and vee), and the curve the MuJoCo model uses;
  1. the separating force at the mesh that opens the Kelvin dock, tilt 0-90 deg, magnets on/off;
  4. the outlet door: opening against the EC's rise, forces, holding shut upside down and on the loop;
  5. the plate latch: holding upside down, and the station rail's drag on the chain.
Geometry from ../params.py and ../layout.py (Sam's frame: x along the auger from the hinge axis, z away from the plate).
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))
import kelvin as K  # noqa: E402
import layout as L  # noqa: E402
from params import *  # noqa: E402,F401,F403

OUT = HERE / "results"
G = 9.81
DR = DOCK_RISE_V3

# ------------------------------------------------------------------------------------------------ masses (kg, Sam mm)
# module v3: v2's parts (station_sim.py) with the armature v3, the dock balls, the door and the keeper
MOD_PARTS = [  # (name, kg, (x, y, z))
    ("plate (Sam's, PETG)", 0.0345, (52.4, 0, -11.3)),
    ("armature v3, 2 mm steel 31.5 x 22", 31.5 * 22 * 2 * 7.85e-6, (105.25, 0, -19.0)),
    ("hinge pins, e-clips, screws", 0.0035, (40.0, 0, 0.0)),
    ("auger", 0.0662, (103.4, 0, 0.0)),
    ("cap", 0.0054, (241.4, 0, 0.0)),
    ("dock balls A and B (2 x 1.05 g)", 0.0021, (30.0, 0, -18.6)),
    ("door housing, shutter, spring", 0.0030, (-1.5, 0, 4.0)),
    ("latch keeper, inserts", 0.0015, (100.0, 0, -13.0)),
]
POWDER = (0.050, (125.0, 0, -4.0))
# EC v3: v2's 0.285 kg (Sam's carriage, NEMA 11, solenoid, electromagnet and bracket, wiring, pinion) at v2's centre, plus
# v3's additions (printed PETG at 1.27 g/cm^3 from the CAD's dimensions, and the bought parts); EC's as-drawn frame
EC_PARTS = [
    ("v2 EC (station_sim.py)", 0.285, (52.0, 0, -33.6)),
    ("ears (cone, vee), 1.2 cm^3", 0.0015, (30.0, 0, -25.0)),
    ("ball C boss, 1.8 cm^3", 0.0023, (113.0, 0, -30.0)),
    ("base, legs, clevis cheeks, 8.6 cm^3", 0.0109, (40.0, 0, -63.0)),
    ("door finger", 0.0002, (-1.0, 7.5, -20.0)),
    ("ball C", 0.00105, (114.5, 0, -24.1)),
    ("3 base balls", 0.00314, (59.3, 0, -64.4)),
    ("2 vee dowels 1/8 x 8 mm", 0.0010, (30.0, -18.5, -22.9)),
    ("2 D44-N52", 0.00302, (30.0, 0, -27.0)),
    ("shoulder screw 4 x 20, nut", 0.0030, (58.0, 0, -76.0)),
]


def mass_com(parts):
    m = sum(p[1] for p in parts)
    c = sum(p[1] * np.array(p[2], float) for p in parts) / m
    return m, c


M_MOD, C_MOD = mass_com(MOD_PARTS)
M_EC, C_EC_DRAWN = mass_com(EC_PARTS)
C_EC = C_EC_DRAWN + np.array([0, 0, DR])          # docked, Sam frame

# ------------------------------------------------------------------------------------------------ dock geometry (Sam, docked)
ZB = KC_BALL_Z                                      # plate balls' centres
H_VEE = math.sqrt((KC_BALL_D / 2 + VEE_DOWEL_D / 2) ** 2 - (VEE_SPACING / 2) ** 2)
C_BALL_Z = -18.0 - 2.0 - KC_BALL_D / 2              # ball C centre, docked (its top on the armature's underside)
GEOM = dict(
    A=(KC_A[0], KC_A[1], ZB), B=(KC_B[0], KC_B[1], ZB), C=(KC_C[0], KC_C[1], -20.0),
    axis=np.array([0, 0, 1.0]),
    vee=[np.array([s * VEE_SPACING / 2, 0, -H_VEE]) / math.hypot(VEE_SPACING / 2, H_VEE) for s in (-1, 1)],
    c_dir=np.array([0, 0, -1.0]),
)
MAG_A = (KC_A[0], KC_A[1], ZB - KC_BALL_D / 2 - KC_MAG_GAP)                    # cone magnet's face (Sam, docked)
GAP_A = KC_MAG_GAP                                                              # 0.6 mm
MAG_B_FACE = ZB - H_VEE - VEE_DOWEL_D / 2 - 0.4 - 0.2 + 0.0                     # vee magnet's face (parts3.kc_magnet_tops + DR)
GAP_B = (ZB - KC_BALL_D / 2) - MAG_B_FACE                                        # 2.38 mm, the dowels between
EM_PT = (DOCK_MAG_XY3[0], 0.0, -20.15)                                          # electromagnet face, 0.15 under the armature
MESH_PT = (GEAR_X + 5.0, 0.0, -22.0)                                            # 44T pitch point (v2's station_sim)
PIN_PT = (EC_PIN[0], 0.0, EC_PIN[1] + DR)                                       # clevis pin, docked
FINGER_PT = (-2.1, DOOR_ROD_Y, DOOR_ROD_BOTTOM + DOOR_TRAVEL)                   # finger on the push strip, open
SEP_RATIO = SEP_RATIO_STEEL                                                     # separating / tangential (v2: 0.55)
F_STALL_SEP = 0.067 / 0.010 * SEP_RATIO                                         # NEMA 11 at 450 mA: 0.067 N*m at R 10 -> 3.7 N
F_DOOR_OPEN = DOOR_SPRING[2] * (DOOR_SPRING[1] - (DOOR_SPRING_SHUT - DOOR_TRAVEL))   # 0.63 N
B_PIN = L.actuator_pins(0.0, 0.0)[0] - L.HINGE_STATION                           # P16 base pin (world-aligned Sam frame)


def frames(tilt):
    th = math.radians(tilt)
    R = np.array([[math.cos(th), 0, -math.sin(th)], [0, 1, 0], [math.sin(th), 0, math.cos(th)]])   # Ry(-tilt), layout.sam_frame
    return R, np.zeros(3)


def dock_loads(tilt, F_sep, sign_t, *, seat=True, coil=True, powder=0.0, pin="push", fa=None, fb=None, f_em=None, extra=(), geom=None):
    """Loads on the EC [(point Sam, force frame)] at this tilt with F_sep at the mesh (tangential F_sep / SEP_RATIO, sign_t)."""
    R, t = frames(tilt)
    gvec = np.array([0, 0, -G])
    loads = [(C_EC, M_EC * gvec)]
    a = R @ np.array([0, 0, 1.0])
    fa = SEAT_PULL["A"] if fa is None else fa
    fb = SEAT_PULL["B"] if fb is None else fb
    if seat:
        if geom is None:
            loads += [(MAG_A, fa * a), ((KC_B[0], KC_B[1], MAG_B_FACE), fb * a)]
        else:     # fix: a D44 under the vee (dowels between, as B now) and one behind the EC's ball on the flat (assumed the same)
            loads += [((KC_A[0], KC_A[1], MAG_B_FACE), fb * a), ((KC_B[0], KC_B[1], MAG_B_FACE), fb * a)]
    if coil:
        loads.append((EM_PT, (K.em_pull(0.15) if f_em is None else f_em) * a))
    loads.append((FINGER_PT, -F_DOOR_OPEN * a))
    loads.append((MESH_PT, -F_sep * a + sign_t * F_sep / SEP_RATIO * (R @ np.array([0, 1.0, 0]))))
    for p, fz in extra:
        loads.append((p, fz * a))
    F_act = 0.0
    if pin == "push":
        # module + EC moment about the hinge (y axis through the origin) carried by the P16 along its rod
        m_mod = M_MOD + (POWDER[0] if powder else 0.0)
        c_mod = (C_MOD * M_MOD + np.array(POWDER[1]) * POWDER[0] * (1 if powder else 0)) / m_mod
        P = R @ np.array(PIN_PT)
        u = (P - B_PIN) / np.linalg.norm(P - B_PIN)
        Mg = np.cross(R @ c_mod, m_mod * gvec)[1] + np.cross(R @ C_EC, M_EC * gvec)[1]
        F_act = -Mg / np.cross(P, u)[1]
        loads.append((PIN_PT, F_act * u))
    return R, t, loads, F_act


def dock_case(tilt, F_sep, sign_t, **kw):
    R, t, loads, F_act = dock_loads(tilt, F_sep, sign_t, **kw)
    x = K.kelvin_solve(R, t, GEOM, loads, pivot=np.zeros(3))
    return x, K.kelvin_check(x, R, GEOM), F_act


MU = dict(liftoff=(50.0, 50.0), friction=(0.25, 0.15), frictionless=(0.0, 0.0))   # (steel ball on printed cone, steel on steel)


def opening_force(tilt, mode="friction", **kw):
    """Largest separating force at the mesh (N) the dock carries, worst tangential sign (bisection on the friction LP).
    liftoff: only a ball lifting off its seat counts (sideways slip ignored, as v2's criterion); friction: mu 0.25 on the
    cone, 0.15 steel on steel; frictionless: the exact Kelvin clamp (most conservative)."""
    mc, ms = MU[mode]
    worst, Fa = 40.0, 0.0
    for sgn in (-1, 1):
        def ok(F):
            R, t, loads, fa_ = dock_loads(tilt, F, sgn, **kw)
            return K.lp_holds(R, t, kw.get("geom") or GEOM, loads, np.zeros(3), mc, ms), fa_
        h0, Fa = ok(0.0)
        if not h0:
            return 0.0, Fa
        lo, hi = 0.0, 40.0
        if ok(hi)[0]:
            continue
        for _ in range(14):
            mid = 0.5 * (lo + hi)
            if ok(mid)[0]:
                lo = mid
            else:
                hi = mid
        worst = min(worst, lo)
    return round(worst, 2), Fa


SEAT_PULL = {}


def run_magnets():
    """Run 2: pull on the ball against gap; the shims of T6a add to each seat's design gap."""
    out = dict(model=("D44-N52 as two charged discs (Br 1.45 T); ball cells magnetised M = 3 H (high-permeability sphere), "
                      "capped at Js 1.7 T; pull = d(co-energy)/dz"),
               case1_ideal_N=round(K.case1_pull(0.0), 2), case1_kj_N=round(K.KJ_CASE1_N, 2))
    out["kj_over_model"] = round(K.KJ_CASE1_N / out["case1_ideal_N"], 3)
    cache = OUT / "magnet_curve_cache.json"
    if cache.exists():
        curve = json.loads(cache.read_text())
    else:
        curve = []
    for g in ([] if curve else [0.0, 0.25, 0.5, 0.6, 0.85, 1.1, 1.5, 2.0, 2.38, 2.63, 2.88, 3.5, 4.5, 6.0]):
        F = K.ball_pull(g * 1e-3)
        curve.append(dict(gap_mm=g, pull_N=round(F, 3), pull_kj_scaled_N=round(F * out["kj_over_model"], 3)))
        print("ball pull", curve[-1], flush=True)
    cache.write_text(json.dumps(curve))
    out["curve"] = curve
    fz = {c["gap_mm"]: c["pull_N"] for c in curve}
    sc = out["kj_over_model"]
    out["cone_A"] = [dict(shim_mm=s, gap_mm=round(GAP_A + s, 2), pull_N=round(fz[round(GAP_A + s, 2)], 2),
                          pull_central_N=round(fz[round(GAP_A + s, 2)] * sc, 2)) for s in (0.0, 0.25, 0.5)]
    out["vee_B_bare"] = [dict(shim_mm=s, gap_mm=round(GAP_B + s, 2), pull_N=round(fz[round(GAP_B + s, 2)], 2),
                              pull_central_N=round(fz[round(GAP_B + s, 2)] * sc, 2)) for s in (0.0, 0.25, 0.5)]
    # dipole (point) approximation at the ball's centre as the low bound, on-axis analytic field
    def bz(z):
        a, h = K.A_MAG, K.H_MAG
        return K.BR / 2 * ((z + h) / math.hypot(z + h, a) - z / math.hypot(z, a))
    def dip(gap):
        z = gap + K.R_BALL
        dbdz = (bz(z + 1e-6) - bz(z - 1e-6)) / 2e-6
        return -4 * math.pi * K.R_BALL ** 3 * bz(z) * dbdz / K.MU0
    out["cone_A_dipole_low_N"] = [round(dip((GAP_A + s) * 1e-3), 2) for s in (0.0, 0.25, 0.5)]
    out["vee_B_dipole_low_N"] = [round(dip((GAP_B + s) * 1e-3), 2) for s in (0.0, 0.25, 0.5)]
    SEAT_PULL["A"] = out["cone_A"][0]["pull_central_N"]
    SEAT_PULL["B"] = out["vee_B_bare"][0]["pull_central_N"]
    # hold the EC seated at tilt 0 with the coil off and the pin floating?
    need = {}
    R, _ = frames(0.0)
    # moment of the EC's weight about the A-B ball line (x = KC_A[0]) against what a pull at C would give
    need["ec_weight_N"] = round(M_EC * G, 2)
    need["ec_com_x_mm"] = round(float(C_EC[0]), 1)
    need["moment_about_AB_Nmm"] = round(M_EC * G * (C_EC[0] - KC_A[0]), 1)
    need["pull_needed_at_C_N"] = round(M_EC * G * (C_EC[0] - KC_A[0]) / (KC_C[0] - KC_A[0]), 2)
    need["seat_magnets_sum_N"] = round(SEAT_PULL["A"] + SEAT_PULL["B"], 2)
    x, c, _ = dock_case(0.0, 0.0, 1, seat=True, coil=False, pin="float")
    need["coil_off_pin_floating_flat_C_N"] = round(float(c["flat"]), 2)
    need["holds"] = bool(min(c.values()) >= 0)
    out["hold_at_tilt0_coil_off"] = need
    return out


def run_dock():
    """Run 1: the separating force at the mesh that opens the dock, tilt 0-90 deg."""
    tilts = [0.0, 0.5, 15.0, 30.0, 45.0, 60.0, 75.0, 86.5, 90.0]
    rows = []
    for name, kw in CASES.items():
        for tl in tilts:
            pin = "float" if tl == 0.0 else "push"
            r = dict(case=name, tilt_deg=tl, pin=("floating in its slot" if pin == "float" else "pushing"))
            for mode in ("liftoff", "friction", "frictionless"):
                F, Fa = opening_force(tl, mode=mode, pin=pin, **kw)
                r[f"F_open_{mode}_N"] = F
            r["F_act_N"] = round(float(Fa), 2)
            r["motor_stalls_first_liftoff"] = bool(r["F_open_liftoff_N"] > F_STALL_SEP)
            r["motor_stalls_first_friction"] = bool(r["F_open_friction_N"] > F_STALL_SEP)
            rows.append(r)
            print(r, flush=True)
    ft = 0.03 / 0.022
    x, c, Fa = dock_case(30.0, ft * SEP_RATIO, 1, pin="push")
    detail = dict(tilt_deg=30.0, F_sep_N=round(ft * SEP_RATIO, 3), contact_forces_frictionless_N=dict(
        cone_A=round(float(np.linalg.norm(x[:3])), 2), vee_B=[round(float(x[3]), 2), round(float(x[4]), 2)], flat_C=round(float(x[5]), 2)),
        F_act_N=round(float(Fa), 2))
    return rows, detail


CASES = {
    "seat magnets + coil": dict(seat=True, coil=True),
    "seat magnets only (coil off)": dict(seat=True, coil=False),
    "coil only (no seat magnets)": dict(seat=False, coil=True),
    "fix: seat magnets 8 N per ball + coil": dict(seat=True, coil=True, fa=8.0, fb=8.0),
}


def run_door():
    """Run 4: the outlet door against the EC's rise; holding shut."""
    k, L0 = DOOR_SPRING[2], DOOR_SPRING[1]
    shut = k * (L0 - DOOR_SPRING_SHUT)
    opn = k * (L0 - (DOOR_SPRING_SHUT - DOOR_TRAVEL))
    rise = np.linspace(0, PARK_DROP, 201)
    door = np.clip(DOOR_TRAVEL - (PARK_DROP - rise), 0, DOOR_TRAVEL)
    # shutter mass: 1.5 mm PETG, the plate 14 x 11.5, the strip 3 x 18.5, a boss
    DOOR_Y = (-5.0, DOOR_ROD_Y + DOOR_ROD_D / 2)          # parts3.DOOR_Y
    v = DOOR_T * ((DOOR_Y[1] - DOOR_Y[0]) * (DOOR_CLOSED_Z[1] - DOOR_CLOSED_Z[0]) + DOOR_ROD_D * (DOOR_CLOSED_Z[0] - DOOR_ROD_BOTTOM)) + 3 * 3.3 * 2
    m = v * 1.27e-6
    # loop accelerations (v2 loop_sim): 100 mm/s, 500 mm/s^2 index; centripetal on a 32T corner; a hard stop 100 -> 0 in 0.146 s
    r_corner = 0.0486 + 0.035
    acc = dict(index=0.5, corner_centripetal=0.1 ** 2 / r_corner, hard_stop=0.1 / 0.146)
    a_max = max(acc.values())
    out = dict(spring_shut_N=round(shut, 3), spring_open_N=round(opn, 3), shutter_mass_g=round(m * 1e3, 2),
               shutter_weight_N=round(m * G, 4),
               finger_meets_strip_at_rise_mm=PARK_DROP - DOOR_TRAVEL, open_from_mm_before_dock=DOOR_TRAVEL,
               shut_after_descent_mm=DOOR_TRAVEL, loop_accel_m_s2={k2: round(v2, 3) for k2, v2 in acc.items()},
               shut_margin_upside_down=round(shut / (m * (G + a_max)), 1),
               accel_to_open_g=round(shut / m / G, 1),
               finger_force_max_N=round(opn, 3),
               finger_force_with_groove_friction_N=round(opn * 1.3, 3))
    return out, rise, door


def run_latch():
    """Run 5: the plate latch upside down; the rail's drag on the chain while it draws the bolt back."""
    m = M_MOD + POWDER[0]
    c = (C_MOD * M_MOD + np.array(POWDER[1]) * POWDER[0]) / m
    arm = 0.5 * (LATCH_KEEPER_X[0] + LATCH_KEEPER_X[1])
    M_static = m * G * c[0]
    F_static = M_static / arm
    F_dyn = F_static * 5.62 / 4.44                    # v2 loop_sim: 4.44 N static -> 5.62 N peak at 100 mm/s
    k, L0 = LATCH_SPRING[2], LATCH_SPRING[1]
    f_closed = 0.9
    ramp = math.radians(25.0)
    mu = 0.3
    ys = np.linspace(0, LATCH_TRAVEL / math.tan(ramp), 200)
    stroke = ys * math.tan(ramp)
    Fs = f_closed + k * stroke
    # follower on a 25 deg ramp, sliding (mu on the ramp) in its slot (mu on the slot's side wall):
    # drag along the run D = Fs (sin a + mu cos a) / (cos a - mu sin a - mu (sin a + mu cos a))
    sa, ca = math.sin(ramp), math.cos(ramp)
    D_noslot = Fs * (sa + mu * ca) / (ca - mu * sa)
    D = Fs * (sa + mu * ca) / (ca - mu * sa - mu * (sa + mu * ca))
    r_sprocket = 0.0486
    work = float(np.sum(0.5 * (D[1:] + D[:-1]) * np.diff(ys))) * 1e-3
    out = dict(module_kg=round(m, 4), module_com_x_mm=round(float(c[0]), 1), latch_arm_mm=arm,
               latch_load_static_N=round(F_static, 2), latch_load_peak_100mm_s_N=round(F_dyn, 2),
               bolt_axial_load_N=0.0,
               bolt_back_off=("none: the keeper presses the bolt square to its travel (along z, the bolt slides along x); "
                              "x is across the loop, so neither gravity nor the chain's accelerations push along the bolt"),
               spring_N=dict(closed=f_closed, open=round(f_closed + k * LATCH_TRAVEL, 3)),
               ramp_deg=25.0, ramp_length_mm=round(float(ys[-1]), 2), mu=mu,
               drag_peak_N=round(float(D.max()), 2), drag_peak_no_slot_friction_N=round(float(D_noslot.max()), 2),
               drive_torque_peak_Nm=round(float(D.max()) * r_sprocket, 3), work_per_opening_mJ=round(work * 1e3, 2),
               drive_torque_vs_motor=f"{float(D.max()) * r_sprocket:.3f} of the NEMA 34's 12 N*m; v2's index peaked at 0.52-1.37 N*m")
    return out, ys, stroke, D


FIX_C_PULL = 3.0      # proposed: a D42-N52 (1/4 x 1/8 in) behind ball C pulling the armature through the ball, about 3 N


def plots(dock_rows, mag, door, latch):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    OUT.mkdir(parents=True, exist_ok=True)
    # 1. dock opening against tilt
    fig, ax = plt.subplots(figsize=(8.5, 5))
    sty = {"seat magnets + coil": "#1f5fbf", "seat magnets only (coil off)": "#d0661a", "coil only (no seat magnets)": "#6b6b6b"}
    sty.update({k: c for k, c in zip([k for k in CASES if k not in sty], ("#2a9d5c", "#8e44ad", "#c0392b"))})
    sty.pop("coil only (no seat magnets)", None)
    for name, col in sty.items():
        r = [x for x in dock_rows if x["case"] == name and x["tilt_deg"] > 0]
        if not r:
            continue
        ax.plot([x["tilt_deg"] for x in r], [x["F_open_liftoff_N"] for x in r], "-", marker="o", ms=4, color=col, label=f"v3 {name}: a ball lifts off")
        ax.plot([x["tilt_deg"] for x in r], [x["F_open_friction_N"] for x in r], "--", marker="s", ms=3, color=col, label=f"v3 {name}: slides (mu 0.25/0.15)")
    v2t, v2f = [0, 15, 30, 45, 60, 75, 90], [13.3, 13.3, 13.3, 11.9, 9.6, 7.8, 7.0]
    ax.plot(v2t, v2f, "-", color="#999999", lw=1.2, marker=".", label="v2 (station_sim.py): dock magnet")
    ax.axhline(F_STALL_SEP, color="#b00020", lw=1.2)
    ax.text(30, F_STALL_SEP - 0.75, f"NEMA 11 stall at 450 mA: {F_STALL_SEP:.1f} N separating", color="#b00020", fontsize=9)
    ax.set_xlabel("tilt (deg, frame)")
    ax.set_ylabel("separating force at the mesh that opens the dock (N)")
    ax.set_title("v3 Kelvin dock: holding against tilt (empty module, P16 pushing)", fontsize=11)
    ax.set_xlim(0, 92)
    ax.set_ylim(0, 18)
    ax.grid(alpha=0.3)
    ax.legend(fontsize=8, loc="center left", bbox_to_anchor=(0.01, 0.42), framealpha=0.95)
    fig.tight_layout()
    fig.savefig(OUT / "dock_opening_vs_tilt.png", dpi=110)
    plt.close(fig)
    # 2. magnet pull
    fig, ax = plt.subplots(figsize=(7.5, 4.6))
    c = mag["curve"]
    g = [x["gap_mm"] for x in c]
    ax.plot(g, [x["pull_N"] for x in c], "-", color="#1f5fbf", label="model (local-sphere magnetisation, saturating)")
    ax.plot(g, [x["pull_kj_scaled_N"] for x in c], "--", color="#1f5fbf", label=f"x {mag['kj_over_model']} (K&J case 1 / model case 1)")
    for s, F in zip((0.0, 0.25, 0.5), mag["cone_A"]):
        ax.plot(F["gap_mm"], F["pull_central_N"], "o", color="#d0661a")
    for s, F in zip((0.0, 0.25, 0.5), mag["vee_B_bare"]):
        ax.plot(F["gap_mm"], F["pull_central_N"], "s", color="#6b6b6b")
    ax.axhline(M_EC * G / 2, color="#b00020", lw=1)
    ax.text(3.2, M_EC * G / 2 + 0.15, "half the EC's weight", color="#b00020", fontsize=9)
    ax.annotate("cone A: 0.6 mm + shims 0, 0.25, 0.5", (GAP_A, mag["cone_A"][0]["pull_central_N"]), (1.3, 4.2), fontsize=8,
                arrowprops=dict(arrowstyle="->", lw=0.6))
    ax.annotate("vee B (bare magnet; dowels not modelled)", (GAP_B, mag["vee_B_bare"][0]["pull_central_N"]), (2.7, 2.2), fontsize=8,
                arrowprops=dict(arrowstyle="->", lw=0.6))
    ax.set_xlabel("gap, magnet face to the ball's nearest point (mm)")
    ax.set_ylabel("pull on a 1/4 in steel ball (N)")
    ax.set_title("D44-N52 on a 1/4 in chrome-steel ball (estimate)", fontsize=11)
    ax.grid(alpha=0.3)
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(OUT / "seat_magnet_pull.png", dpi=110)
    plt.close(fig)
    # 3. door and latch
    dd, rise, door_mm = door
    lt, ys, stroke, D = latch
    fig, ax = plt.subplots(1, 2, figsize=(11, 4.2))
    ax[0].plot(rise, door_mm, color="#1f5fbf", label="door opening (mm)")
    ax[0].plot(rise, np.where(door_mm > 0, DOOR_SPRING[2] * (DOOR_SPRING[1] - (DOOR_SPRING_SHUT - door_mm)), 0) * 10, color="#d0661a",
               label="finger force x 10 (N)")
    ax[0].axvline(PARK_DROP, color="k", lw=0.8)
    ax[0].text(PARK_DROP - 5.5, 6.3, "docked", fontsize=8)
    ax[0].set_xlabel("EC rise from its park (mm)")
    ax[0].set_ylim(0, 7.2)
    ax[0].set_title("Outlet door against the EC's rise (undock: the same in reverse)", fontsize=10)
    ax[0].grid(alpha=0.3)
    ax[0].legend(fontsize=8)
    ax[1].plot(ys, D, color="#1f5fbf", label="rail drag on the chain (N)")
    ax[1].plot(ys, stroke, color="#6b6b6b", label="bolt drawn back (mm)")
    ax[1].set_xlabel("follower along the ramp (mm of travel)")
    ax[1].set_title(f"Latch rail, 25 deg ramp, mu {lt['mu']}: peak {lt['drag_peak_N']} N, {lt['drive_torque_peak_Nm']} N*m", fontsize=10)
    ax[1].grid(alpha=0.3)
    ax[1].legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(OUT / "door_and_latch.png", dpi=110)
    plt.close(fig)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    res = dict(masses=dict(module_v3_dry_kg=round(M_MOD, 4), module_v3_com_mm=[round(float(v), 1) for v in C_MOD],
                           ec_v3_kg=round(M_EC, 4), ec_v3_com_docked_mm=[round(float(v), 1) for v in C_EC],
                           module_parts=MOD_PARTS, ec_parts=EC_PARTS))
    print(res["masses"], flush=True)
    res["magnets"] = run_magnets()
    rows, detail = run_dock()
    res["dock"] = dict(rows=rows, detail_30deg_dosing=detail, F_stall_sep_N=round(F_STALL_SEP, 2), sep_ratio=SEP_RATIO,
                       seat_pulls_used_N=SEAT_PULL, coil_N=round(K.em_pull(0.15), 2), door_finger_N=round(F_DOOR_OPEN, 3),
                       fix_c_pull_N=FIX_C_PULL)
    door = run_door()
    res["door"] = door[0]
    latch = run_latch()
    res["latch"] = latch[0]
    (OUT / "statics.json").write_text(json.dumps(res, indent=1, default=lambda o: o.tolist() if hasattr(o, "tolist") else str(o)) + "\n")
    plots(rows, res["magnets"], door, latch)
    print(json.dumps(res["door"]), json.dumps(res["latch"]), sep="\n")


if __name__ == "__main__":
    main()
