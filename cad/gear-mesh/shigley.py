"""Hand calculations for the station's 20T:44T mesh (Shigley's Mechanical Engineering
Design, Ch. 13-14), for both carousel designs. Writes out/shigley.json and three figures.

The question (PR #185, 2026-10-18): is the weight of the module (gondola) enough to keep the
auger's 44T gear in mesh with the NEMA 11's 20T pinion, at higher speeds and at every tilt?

1. Geometry: contact ratio and operating pressure angle against centre distance (Ch. 13).
2. Forces (Sec. 13-14): W_t = T/r_1; the radial (separating) force is W_t tan(phi) without
   friction. With tooth friction mu it peaks at W_t (tan(phi) + mu) during part of every
   mesh cycle (the friction force flips at the pitch point).
3. Motor: available torque against speed for a 2-phase hybrid stepper on a chopper driver
   (phasor model with the datasheet R, L and holding torque).
4. Dynamic factor (Eq. 14-4a Barth "cast profile", for printed teeth; Eq. 14-27 AGMA, Q_v 6).
5. Tooth bending (Lewis, Eq. 14-8 with Table 14-2) and surface stress (Eq. 14-14, Cp Eq. 14-13).
6. Preload: moments about the hinge. Weight (and magnet) against the separating force at
   the gear, at each tilt. Gives the largest pinion torque before the plate lifts.
7. Separation runaway: as the gear lifts, phi' grows and the contact ratio drops.
8. Engagement at docking: tip-on-tip odds and the flank wedge.

    python shigley.py
"""
from __future__ import annotations

import json
import math

import numpy as np

import common as C
import vizstyle as V

LEWIS = [(12, .245), (13, .261), (14, .277), (15, .290), (16, .296), (17, .303), (18, .309), (19, .314), (20, .322),
         (21, .328), (22, .331), (24, .337), (26, .346), (28, .353), (30, .359), (34, .371), (38, .384), (43, .397),
         (50, .409), (60, .422), (75, .435), (100, .447), (150, .460), (300, .472), (400, .480)]


def lewis_Y(n: int) -> float:
    xs, ys = zip(*LEWIS)
    return float(np.interp(n, xs, ys))


KT = C.T_HOLD / (math.sqrt(2) * C.I_RATED)      # N*m/A: holding torque is with both phases at the rated current


def motor_torque(rev_s, v_supply: float, i_set: float) -> np.ndarray:
    """Largest torque (N*m) the NEMA 11 can make at a speed: current amplitude limited by the
    driver setting and by what the supply can push through R + jwL against the back-EMF."""
    w = 2 * np.pi * np.asarray(rev_s, float)
    x = C.N_ROTOR * w * C.L_PH
    e = KT * w
    a = C.R_PH ** 2 + x ** 2
    b = 2 * C.R_PH * e
    c = e ** 2 - v_supply ** 2
    i_max = np.where(c < 0, (-b + np.sqrt(np.maximum(b ** 2 - 4 * a * c, 0))) / (2 * a), 0.0)
    return KT * np.minimum(i_set, i_max)


def kv_barth_cast(v):           # Eq. 14-4a: cast profile, the roughest of Barth's forms (printed teeth)
    return (3.05 + v) / 3.05


def kv_agma(v, qv=6):           # Eq. 14-27, SI (v in m/s)
    B = 0.25 * (12 - qv) ** (2 / 3)
    A = 50 + 56 * (1 - B)
    return ((A + np.sqrt(200 * np.asarray(v))) / A) ** B


def cp(m1: dict, m2: dict) -> float:     # Eq. 14-13, sqrt(MPa)
    return math.sqrt(1 / (math.pi * ((1 - m1["nu"] ** 2) / m1["E"] + (1 - m2["nu"] ** 2) / m2["E"])))


def stresses(t_pinion: float, rev_s: float, pinion_mat: str, gear_mat: str = "PETG (printed)") -> dict:
    v = math.pi * 2 * C.R1 * 1e-3 * rev_s                 # pitch-line velocity, m/s
    kv = float(kv_barth_cast(v))
    wt = t_pinion / (C.R1 * 1e-3)                         # N
    s_b1 = kv * wt / (C.FACE * C.M * lewis_Y(C.Z1))       # MPa
    s_b2 = kv * wt / (C.FACE * C.M * lewis_Y(C.Z2))
    r1, r2 = C.R1 * math.sin(C.PHI), C.R2 * math.sin(C.PHI)
    p1, p2 = C.MAT[pinion_mat], C.MAT[gear_mat]
    s_c = cp(p1, p2) * math.sqrt(kv * wt / (C.FACE * math.cos(C.PHI)) * (1 / r1 + 1 / r2))
    return dict(v_mps=round(v, 4), Kv=round(kv, 3), Wt_N=round(wt, 3),
                bending_pinion_MPa=round(s_b1, 2), bending_gear_MPa=round(s_b2, 2), contact_MPa=round(s_c, 2),
                SF_bending_pinion=round(p1["Sb"] / s_b1, 2), SF_bending_gear=round(p2["Sb"] / s_b2, 2),
                SF_contact=round(min(p1["Sc"], p2["Sc"]) / s_c, 2))


def hold_moment(world_tilt, m_powder=0.0, f_mag=0.0, x_mag=99.5, x_powder=None):
    """N*mm holding the plate on the carriage: weight (+ magnet pull at x_mag)."""
    return C.weight_moment(m_powder, world_tilt, x_powder) + f_mag * x_mag


def torque_capacity(world_tilt, mu, m_powder=0.0, f_mag=0.0, kv=1.0, x_powder=None):
    """Largest pinion torque (N*m) before the separating moment beats the holding moment."""
    m = hold_moment(world_tilt, m_powder, f_mag, x_powder=x_powder)
    wt = m / (C.separating_ratio(mu, math.radians(20.48)) * C.GEAR_X)       # at the docked 32.1 mm (phi' 20.48)
    return max(wt, 0.0) * C.R1 * 1e-3 / kv


def main():
    V.setup()
    import matplotlib.pyplot as plt
    out = {}

    # 1. geometry
    geo = {}
    for a in (32.0, C.A_DOCK, 32.3, 32.5, 32.7, 33.0, 33.5):
        geo[f"{a:.2f}"] = dict(phi_op_deg=round(math.degrees(C.operating_pressure_angle(a)), 2), contact_ratio=round(C.contact_ratio(a), 3))
    backlash = 2 * (C.A_DOCK - C.A0) * math.tan(math.radians(20.48))
    out["geometry"] = dict(m=C.M, z=[C.Z1, C.Z2], phi_deg=20.0, face_mm=C.FACE, a0_mm=C.A0, a_dock_mm=C.A_DOCK,
                           gear_x_from_hinge_mm=round(C.GEAR_X, 2), backlash_at_dock_mm=round(backlash, 3),
                           base_pitch_mm=round(C.PB, 3), by_centre_distance=geo)

    # 2-3. forces and motor
    speeds = np.linspace(0.05, 16, 320)                                   # pinion rev/s
    mt = {f"{v} V, {i} A": motor_torque(speeds, v, i) for v, i in ((12, 0.67), (12, 0.95), (24, 0.95))}
    out["motor"] = dict(kt_NmA=round(KT, 4), holding_Nm=C.T_HOLD,
                        max_torque_Nm_at_0p67A=round(KT * 0.67, 4), max_torque_Nm_at_0p95A=round(KT * 0.95, 4),
                        corner_speed_rev_s={k: float(speeds[np.argmax(t < 0.98 * t[0])]) for k, t in mt.items()},
                        note="DRV8825/TIC current limit is the sine amplitude: 0.67 A gives 0.071 N*m; 0.95 A puts 0.67 A rms in each coil and gives the 0.10 N*m holding torque")
    loads = {}
    for name, t in (("running, light (auger 0.005 N*m)", 0.005 / 2.2), ("running, heavy (auger 0.03 N*m)", 0.03 / 2.2),
                    ("stall at 0.67 A", KT * 0.67), ("holding torque (0.95 A)", C.T_HOLD)):
        wt = t / (C.R1 * 1e-3)
        loads[name] = dict(pinion_Nm=round(t, 4), Wt_N=round(wt, 3), Wr_frictionless_N=round(wt * math.tan(C.PHI), 3),
                           **{f"Wr_max_mu{mu}": round(wt * C.separating_ratio(mu), 3) for mu in (0.1, 0.2, 0.3)})
    out["loads"] = loads

    # 4-5. dynamic factor and stresses
    st = {}
    for rev in (1.0, 5.0, 10.0, 15.0):
        for pm in ("PETG (printed)", "steel"):
            st[f"{rev:g} rev/s, {pm} pinion, 0.10 N*m"] = stresses(C.T_HOLD, rev, pm)
    out["stresses"] = st

    # 6. preload against tilt
    tilts = np.linspace(0, 90, 181)
    cases = {
        "weight only, empty": dict(m_powder=0.0, f_mag=0.0),
        "weight only, 60 g of powder": dict(m_powder=0.060, f_mag=0.0),
        "with the magnet (12 N), empty": dict(m_powder=0.0, f_mag=12.0),
    }
    cap = {}
    for k, kw in cases.items():
        for mu in (0.1, 0.3):
            cap[f"{k}, mu {mu}"] = [torque_capacity(t, mu, **kw) for t in tilts]
    out["preload"] = dict(
        weight_moment_Nmm={f"{t:g} deg": round(C.weight_moment(0.0, t), 1) for t in (0, 15, 30, 45, 60, 75, 90)},
        weight_at_gear_N={f"{t:g} deg": round(C.weight_moment(0.0, t) / C.GEAR_X, 3) for t in (0, 15, 30, 45, 60, 75, 90)},
        torque_capacity_Nm={k: {f"{t:g} deg": round(v[int(t * 2)], 5) for t in (0, 30, 45, 60, 90)} for k, v in cap.items()},
        required_magnet_N=None)
    # magnet force needed at x = 99.5 mm for SF 1.5 against the holding torque, PETG friction, at 90 deg (no weight help)
    need = {}
    for mu in (0.1, 0.2, 0.3):
        for t_name, t in (("holding 0.10 N*m", C.T_HOLD), ("stall at 0.67 A", KT * 0.67)):
            m_sep = t / (C.R1 * 1e-3) * C.separating_ratio(mu, math.radians(20.48)) * C.GEAR_X
            need[f"mu {mu}, {t_name}"] = round((1.5 * m_sep - C.weight_moment(0.0, 90.0)) / 99.5, 2)
    out["preload"]["required_magnet_N"] = need

    # critical tilt for gravity only, running heavy (auger 0.03 N*m), mu 0.3
    def crit_tilt(t_pinion, mu, m_powder=0.0):
        for t in tilts:
            if torque_capacity(t, mu, m_powder) < t_pinion:
                return float(t)
        return None
    out["preload"]["lift_off_tilt_deg_weight_only"] = {
        f"{name}, mu {mu}, {fill}": crit_tilt(d["pinion_Nm"], mu, mp)
        for name, d in loads.items() for mu in (0.1, 0.3) for fill, mp in (("empty", 0.0), ("60 g", 0.06))}

    # 7. runaway
    lifts = np.linspace(0, 1.6, 161)
    run = {}
    for mu in (0.0, 0.1, 0.3):
        run[f"mu {mu}"] = [C.separating_ratio(mu, C.operating_pressure_angle(C.A_DOCK + d)) for d in lifts]
    eps = [C.contact_ratio(C.A_DOCK + d) for d in lifts]
    d_eps1 = float(lifts[np.argmax(np.array(eps) < 1.0)])
    out["runaway"] = dict(lift_where_contact_ratio_hits_1_mm=d_eps1,
                          sep_ratio_at={f"{d:g} mm": {k: round(v[int(round(d * 100))], 3) for k, v in run.items()} for d in (0, 0.3, 0.6, 1.0, 1.5)})

    # 8. engagement at docking
    def tip_thickness(r_p, r_a, z):
        a_a = math.acos(r_p * math.cos(C.PHI) / r_a)
        inv = lambda x: math.tan(x) - x
        return 2 * r_a * (math.pi * C.M / 2 / (2 * r_p) + inv(C.PHI) - inv(a_a))
    sa1, sa2 = tip_thickness(C.R1, C.RA1, C.Z1), tip_thickness(C.R2, C.RA2, C.Z2)
    pitch = math.pi * C.M
    a_tip2 = math.acos(C.RB2 / C.RA2)
    wedge = {}
    for mu in (0.1, 0.3):
        wedge[f"mu {mu}"] = round((math.cos(a_tip2) - mu * math.sin(a_tip2)) / (math.sin(a_tip2) + mu * math.cos(a_tip2)), 3)
    out["engagement"] = dict(tip_land_pinion_mm=round(sa1, 3), tip_land_gear_mm=round(sa2, 3), circular_pitch_mm=round(pitch, 3),
                             tip_on_tip_fraction=round((sa1 + sa2) / pitch, 3),
                             flank_wedge_tangential_per_radial=wedge,
                             note="the fraction of random pinion phases where a gear tip lands on a pinion tip land; "
                                  "elsewhere the flanks meet and the weight must rotate the auger or the pinion to slide in")

    (C.OUT / "shigley.json").write_text(json.dumps(out, indent=1))

    # ---------------------------------------------------------------- figures
    # A: torque capacity vs tilt
    fig, ax = plt.subplots(figsize=(7.6, 4.6))
    ax.axhspan(0.005 / 2.2, 0.03 / 2.2, color="#ecebe7", lw=0, zorder=0)
    ax.text(1.5, 0.0062, "normal running (auger 0.005-0.03 N·m)", fontsize=8, color=V.INK2, va="center")
    for y, txt in ((C.T_HOLD, "holding torque 0.10 N·m"), (KT * 0.67, "stall at 0.67 A, 0.071 N·m")):
        ax.axhline(y, color=V.CRITICAL, lw=0.9)
        ax.text(89, y * 1.08, txt, fontsize=8, color=V.INK2, ha="right")
    sel = [("weight only, empty, mu 0.3", V.SERIES[0], "weight only, empty"),
           ("weight only, 60 g of powder, mu 0.3", V.SERIES[2], "weight only, 60 g powder"),
           ("with the magnet (12 N), empty, mu 0.3", V.SERIES[1], "with a 12 N magnet, empty")]
    for key, col, lab in sel:
        y = np.maximum(np.array(cap[key]), 1e-5)
        ax.plot(tilts, y, color=col, label=lab)
        V.label_end(ax, tilts[-1], y[-1], lab.split(",")[0] if "magnet" in lab else "", dx=3)
    ax.set_yscale("log")
    ax.set_ylim(3e-4, 0.6)
    ax.set_xlim(0, 90)
    ax.set_xticks(range(0, 91, 15))
    ax.set_xlabel("module tilt at the station, cap end up (deg, from horizontal)")
    ax.set_ylabel("largest pinion torque before the plate lifts (N·m)")
    ax.set_title("Gravity alone holds the mesh only at light torque and low tilt")
    ax.legend(loc="lower left")
    fig.text(0.01, 0.005, "PETG teeth (worst-case separating force W_t(tan 20.5° + 0.3)), 32.1 mm centre distance, gear 83.7 mm and magnet 99.5 mm from the hinge",
             fontsize=7, color=V.INK2)
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    fig.savefig(C.OUT / "torque_capacity_vs_tilt.png", dpi=150)
    plt.close(fig)

    # B: runaway
    fig, axs = plt.subplots(1, 2, figsize=(8.6, 3.5))
    for (k, v), col in zip(run.items(), V.SERIES):
        axs[0].plot(lifts, v, color=col, label=k.replace("mu", "μ"))
    axs[0].set_xlabel("gear lifted off the pinion (mm)")
    axs[0].set_ylabel("separating force / tangential load")
    axs[0].set_title("Separating force rises as the gear lifts")
    axs[0].legend(loc="upper left")
    axs[1].plot(lifts, eps, color=V.SERIES[0])
    axs[1].axhline(1.0, color=V.CRITICAL, lw=0.9)
    axs[1].text(1.55, 1.04, "contact ratio 1", ha="right", fontsize=8, color=V.INK2)
    axs[1].set_xlabel("gear lifted off the pinion (mm)")
    axs[1].set_ylabel("contact ratio")
    axs[1].set_title("…and the overlap runs out")
    for a in axs:
        a.set_xlim(0, 1.6)
    fig.tight_layout()
    fig.savefig(C.OUT / "separation_runaway.png", dpi=150)
    plt.close(fig)

    # C: motor torque and dynamic factor vs speed (two panels, one axis each)
    fig, axs = plt.subplots(1, 2, figsize=(8.6, 3.5))
    for (k, t), col in zip(mt.items(), V.SERIES):
        axs[0].plot(speeds, t, color=col, label=k)
    axs[0].set_xlabel("pinion speed (rev/s)   [auger rpm = 27.3 × rev/s]")
    axs[0].set_ylabel("largest motor torque (N·m)")
    axs[0].set_title("NEMA 11 torque falls with speed")
    axs[0].legend(loc="upper right")
    vv = np.pi * 0.020 * speeds
    axs[1].plot(speeds, kv_barth_cast(vv), color=V.SERIES[0], label="Barth, cast profile (printed)")
    axs[1].plot(speeds, kv_agma(vv, 6), color=V.SERIES[1], label="AGMA, Q_v 6")
    axs[1].set_xlabel("pinion speed (rev/s)")
    axs[1].set_ylabel("dynamic factor K_v")
    axs[1].set_title("Dynamic factor stays small")
    axs[1].legend(loc="upper left")
    for a in axs:
        a.set_xlim(0, 16)
    fig.tight_layout()
    fig.savefig(C.OUT / "motor_and_kv_vs_speed.png", dpi=150)
    plt.close(fig)

    print(json.dumps({k: out[k] for k in ("motor", "loads", "preload", "runaway", "engagement")}, indent=1))


if __name__ == "__main__":
    main()
