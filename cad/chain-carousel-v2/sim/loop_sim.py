"""Loop dynamics of the v2 carousel (MuJoCo, kinematic chain): what the snap hooks, the carriages and the drive see.

    python sim/loop_sim.py           # index moves, a lap, a hard stop and a coast-down; plots + results/loop/results.json

The chain is inextensible and its motion is exact (kinematics.pins_at): every carriage follows its A-1 link's pose
through a stiff weld to a mocap target, so the weld forces are what the chain has to apply to it. Each module (Sam's
plate, steel tab, auger, cap, 100 g of powder) sits on its hinge on the carriage and is held shut by the snap hooks,
modelled as a stiff detent: the detent torque is the hook demand, reported as the force at the hooks (52 mm from the
hinge). Gravity, the index accelerations and the corners all load it; upside down on the top run is the worst case.

Drive torque: the power the welds put into the carriages and modules, divided by the shaft speed, plus the chain's and
sprockets' inertia and a measured friction torque (PyBullet index run: 0.23 N*m at 50 mm/s).

The closed-chain PyBullet model (carousel_sim.py) ran one index cleanly but its soft loop closure drifted after about
80 mm in both directions, so the lap, hook and stop numbers come from this model.
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import mujoco
import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import kinematics as K  # noqa: E402
import layout as L  # noqa: E402
from params import *  # noqa: E402,F401,F403

OUT = HERE / "results" / "loop"
MM = 1e-3
G = 9.81
DT = 5e-4
M_CAR = 0.098
POWDER = 0.100
M_MOD = 0.0345 + 0.0092 + 0.0035 + 0.0662 + 0.0054 + POWDER
COM_MOD = np.array([(0.0345 * 52.4 + 0.0092 * 100.0 + 0.0035 * 40.0 + 0.0662 * 103.4 + 0.0054 * 241.4 + POWDER * 125.0) / M_MOD, 0.0,
                    (0.0345 * -11.3 + 0.0092 * -19.0 + POWDER * -4.0) / M_MOD])
HOOK_ARM = (SNAP_X - HINGE_X) * MM
K_DETENT = 200.0                  # N*m/rad: holds the module within a few hundredths of a degree
FRICTION_NM = 0.23                # drive friction torque at 50 mm/s (PyBullet index run)
J_CHAIN = 2 * N_LINKS * 0.0042 * (R * MM) ** 2      # both chains moving at the pitch line
J_SPROCKETS = 8 * 0.5 * 0.49 * (0.045) ** 2 + 4 * 0.5 * 0.62 * (SHAFT_D / 2 * MM) ** 2 + 2 * 0.5 * 0.13 * 0.02 ** 2
J_MOTOR = 4.0e-4                  # 34HS59 rotor (StepperOnline: 4000 g*cm^2), 1:1 drive chain


def _f(*v):
    return " ".join(f"{x:.6f}" for x in v)


def quat(Rm: np.ndarray) -> np.ndarray:
    q = np.zeros(4)
    mujoco.mju_mat2Quat(q, np.asarray(Rm, float).ravel())
    return q


def build() -> str:
    links = L.carriage_links()
    xml = [f"""<mujoco model="v2 loop">
  <option timestep="{DT}" integrator="implicitfast" gravity="0 0 -{G}"/>
  <worldbody>"""]
    for k, li in enumerate(links):
        C = L.carriage_frame(li)
        p, q = C[:3, 3] * MM, quat(C[:3, :3])
        sam = L.SAM_IN_CARRIAGE
        xml.append(f'    <body name="tgt{k}" mocap="true" pos="{_f(*p)}" quat="{_f(*q)}"/>')
        xml.append(f'    <body name="car{k}" pos="{_f(*p)}" quat="{_f(*q)}">')
        xml.append('      <freejoint/>')
        xml.append(f'      <inertial pos="0 -0.008 {CHAIN_L / 2 * MM:.4f}" mass="{M_CAR}" diaginertia="0.0009 0.0009 0.00004"/>')
        xml.append(f'      <body name="mod{k}" pos="{_f(*(sam[:3, 3] * MM))}" quat="{_f(*quat(sam[:3, :3]))}">')
        xml.append(f'        <joint name="hinge{k}" type="hinge" axis="0 -1 0" range="0 100" limited="true" damping="0.002"/>')
        xml.append(f'        <inertial pos="{_f(*(COM_MOD * MM))}" mass="{M_MOD}" diaginertia="{_f(2e-5, M_MOD * 0.25 ** 2 / 12 + 4e-5, M_MOD * 0.25 ** 2 / 12 + 4e-5)}"/>')
        xml.append('      </body>')
        xml.append('    </body>')
    xml.append("  </worldbody>\n  <equality>")
    for k in range(len(links)):
        xml.append(f'    <weld body1="tgt{k}" body2="car{k}" solref="0.002 1" torquescale="1"/>')
    xml.append("  </equality>\n</mujoco>")
    return "\n".join(xml)


def profile_index(links: float, v: float, a: float, dwell: float = 0.3):
    """Shift (links) vs time for a trapezoidal move of `links` links at v (mm/s) and a (mm/s^2)."""
    D = links * P
    ta = v / a
    if a * ta * ta > D:
        ta = math.sqrt(D / a)
        v = a * ta
    tc = (D - a * ta * ta) / v
    T = 2 * ta + tc

    def s(t):
        t = t - dwell
        if t <= 0:
            return 0.0
        if t < ta:
            return 0.5 * a * t * t / P
        if t < ta + tc:
            return (0.5 * a * ta * ta + v * (t - ta)) / P
        if t < T:
            u = T - t
            return (D - 0.5 * a * u * u) / P
        return links
    return s, T + 2 * dwell


class Loop:
    def __init__(self):
        self.m = mujoco.MjModel.from_xml_string(build())
        self.d = mujoco.MjData(self.m)
        self.links = L.carriage_links()
        self.jh = [self.m.joint(f"hinge{k}").qposadr[0] for k in range(N_MODULES)]
        self.dh = [self.m.joint(f"hinge{k}").dofadr[0] for k in range(N_MODULES)]
        self.bc = [self.m.body(f"car{k}").id for k in range(N_MODULES)]
        self.bm = [self.m.body(f"mod{k}").id for k in range(N_MODULES)]
        self.mocap = [self.m.body(f"tgt{k}").mocapid[0] for k in range(N_MODULES)]
        mujoco.mj_forward(self.m, self.d)

    def set_shift(self, s: float):
        pins = K.pins_at(s)
        for k, li in enumerate(self.links):
            C = L._frame_from_pins(pins[li % N_LINKS], pins[(li + 1) % N_LINKS])
            self.d.mocap_pos[self.mocap[k]] = C[:3, 3] * MM
            self.d.mocap_quat[self.mocap[k]] = quat(C[:3, :3])

    def step(self):
        th = self.d.qpos[self.jh]
        self.d.qfrc_applied[:] = 0.0
        tau = -K_DETENT * np.maximum(th, 0.0)          # snap hooks: hold the plate shut
        self.d.qfrc_applied[self.dh] = tau
        self.hook_tau = -tau
        mujoco.mj_step(self.m, self.d)

    def power(self) -> float:
        """Power the chain puts into carriages + modules: sum over bodies of d/dt (kinetic + potential energy)."""
        mujoco.mj_energyPos(self.m, self.d)
        mujoco.mj_energyVel(self.m, self.d)
        return float(self.d.energy[0] + self.d.energy[1])


def run(kind: str, v: float = 50.0, a: float = 250.0):
    lp = Loop()
    dirn = RUN_DIRECTION
    if kind == "index":
        sfun, T = profile_index(MODULE_LINKS, v, a)
    elif kind == "lap":
        sfun, T = profile_index(N_LINKS, v, a)
    elif kind == "hardstop":                        # full speed, then the driver stops the motor at its torque limit
        sfun0, _ = profile_index(N_LINKS, v, a, dwell=0.2)
        t_stop = 0.2 + v / a + 0.6
        Jtot = 0.02                                 # kg m^2 at the shaft, checked below
        alpha = 12.0 / Jtot                         # rad/s^2 at 12 N*m
        dec = alpha * R                             # mm/s^2

        def sfun(t):
            if t < t_stop:
                return sfun0(t)
            s0 = sfun0(t_stop) * P
            u = min(t - t_stop, v / dec)
            return (s0 + v * u - 0.5 * dec * u * u) / P
        T = t_stop + 0.4
    else:
        raise ValueError(kind)
    rows = []
    E_prev = None
    n = int(T / DT)
    for i in range(n):
        t = i * DT
        s = dirn * sfun(t)
        lp.set_shift(s)
        lp.step()
        if i % 10 == 0:
            E = lp.power()
            pw = 0.0 if E_prev is None else (E - E_prev) / (10 * DT)
            E_prev = E
            ds = dirn * (sfun(t + DT) - sfun(t - DT)) / (2 * DT) * P * MM    # m/s
            omega = ds / (R * MM)
            hook_N = lp.hook_tau / HOOK_ARM
            rows.append(dict(t=t, shift=s, v=ds * 1000, P=pw, T_load=(pw / omega if abs(omega) > 1e-3 else 0.0),
                             hook_max=float(hook_N.max()), hook_k=int(hook_N.argmax()), tilt_max=float(np.degrees(lp.d.qpos[lp.jh]).max())))
    return rows


def coastdown(v: float = 100.0):
    """Power cut at speed: the loop coasts on its own inertia against the friction torque (the loop is balanced)."""
    lp = Loop()
    m_eff = 0.0
    lp.set_shift(0.0)
    mujoco.mj_forward(lp.m, lp.d)
    # effective mass of carriages + modules along the chain: kinetic energy at 1 mm/s chain speed, by finite difference
    s0 = 0.0
    h = 0.01
    p0 = {}
    for k, li in enumerate(lp.links):
        p0[k] = (L.carriage_frame(li, s0)[:3, 3], L.carriage_frame(li, s0 + h)[:3, 3])
    for k in range(N_MODULES):
        dp = (p0[k][1] - p0[k][0]) / (h * P)        # per mm of chain
        m_eff += (M_CAR + M_MOD) * float(dp @ dp)
    J_tot = m_eff * (R * MM) ** 2 + J_CHAIN + J_SPROCKETS + J_MOTOR
    omega0 = v / R
    t_stop = J_tot * omega0 / FRICTION_NM
    dist = 0.5 * v * t_stop
    return dict(v_mm_s=v, J_total_kgm2=round(J_tot, 5), J_carriages_modules=round(m_eff * (R * MM) ** 2, 5), J_chain=round(J_CHAIN, 5),
                J_sprockets_shafts=round(J_SPROCKETS, 5), J_motor=J_MOTOR, friction_Nm=FRICTION_NM, coast_time_s=round(t_stop, 3),
                coast_distance_mm=round(dist, 2))


def summarize(rows, J_tot):
    rows = [r for r in rows if r["t"] > 0.25]            # skip the detents settling from the as-built pose
    t = np.array([r["t"] for r in rows])
    T_load = np.array([r["T_load"] for r in rows])
    v = np.array([r["v"] for r in rows])
    acc = np.gradient(v, t) if len(t) > 2 else np.zeros_like(v)
    T_inertia = J_tot * acc / R * np.sign(RUN_DIRECTION) * 0 + (J_CHAIN + J_SPROCKETS + J_MOTOR) * np.abs(acc) / R   # chain, sprockets, rotor
    T_total = np.abs(T_load) + T_inertia + FRICTION_NM * (np.abs(v) > 0.5)
    return dict(hook_force_max_N=round(max(r["hook_max"] for r in rows), 2),
                hook_module=int(rows[int(np.argmax([r["hook_max"] for r in rows]))]["hook_k"]) + 1,
                module_opening_max_deg=round(max(r["tilt_max"] for r in rows), 3),
                drive_torque_peak_Nm=round(float(T_total.max()), 3),
                drive_torque_load_peak_Nm=round(float(np.abs(T_load).max()), 3),
                speed_peak_mm_s=round(float(np.abs(v).max()), 1))


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    cd = coastdown(100.0)
    res = {"coastdown_100": cd, "coastdown_50": coastdown(50.0)}
    J_tot = cd["J_total_kgm2"]
    series = {}
    for name, kind, v, a in (("index_50", "index", 50.0, 250.0), ("index_100", "index", 100.0, 500.0), ("lap_50", "lap", 50.0, 250.0),
                             ("lap_100", "lap", 100.0, 500.0), ("hardstop_100", "hardstop", 100.0, 500.0)):
        rows = run(kind, v, a)
        res[name] = summarize(rows, J_tot)
        series[name] = rows
        print(name, json.dumps(res[name]), flush=True)
    print("coast", json.dumps(cd))
    # static hook demand upside down on the top run: weight moment about the hinge
    res["hook_static_top_run_N"] = round(M_MOD * G * COM_MOD[0] * MM / HOOK_ARM, 2)
    res["module_mass_kg"] = round(M_MOD, 4)
    res["module_com_sam_mm"] = [round(float(c), 1) for c in COM_MOD]
    (OUT / "results.json").write_text(json.dumps(res, indent=1) + "\n")
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(2, 1, figsize=(10, 7), sharex=False)
    for name in ("lap_50", "lap_100"):
        rows = [r for r in series[name] if r["t"] > 0.25]
        u = [((r["shift"]) % N_LINKS) for r in rows]
        ax[0].plot([r["t"] for r in rows], [r["hook_max"] for r in rows], label=f"{name}: largest hook demand among the 13 modules")
    ax[0].axhline(res["hook_static_top_run_N"], color="k", lw=0.8, ls="--", label="static, upside down on the top run")
    ax[0].set_ylabel("N at the snap hooks")
    ax[0].set_xlabel("s")
    ax[0].legend(fontsize=8)
    ax[0].grid(alpha=0.3)
    for name in ("index_50", "index_100", "hardstop_100"):
        rows = [r for r in series[name] if r["t"] > 0.25]
        ax[1].plot([r["t"] for r in rows], [abs(r["T_load"]) for r in rows], label=f"{name}: load torque from carriages + modules")
    ax[1].set_ylabel("N*m at the drive shaft")
    ax[1].set_xlabel("s")
    ax[1].legend(fontsize=8)
    ax[1].grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(OUT / "loop.png", dpi=110)


if __name__ == "__main__":
    main()
