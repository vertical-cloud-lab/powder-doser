"""Auger leakage on the multi-doser carousels: MuJoCo granular proxy with a moving module.

Builds on the paternoster's auger model (``cad/paternoster/sim/auger_*.py``): the same
1100-grain proxy, the same measured tube, flight, core and widened exit, the same vial on
a spring balance. The one change is that the auger's frame is no longer fixed. It sits on
a free joint whose pose and velocity are prescribed every step (heavy body with gravity
compensation), so the module can tilt back after a dose, roll round a v2 corner, or swing
in a paternoster gondola. Translation of the module through the loop enters as an
inertial body force (gravity minus the outlet point's acceleration), which is exact for
a rigid module.

Frames. World z up. The machine is pitched about world y by ``alpha`` (outlet end up),
so a module at rest has its outlet->cap axis at world (cos a, 0, -sin a): nozzle up by
alpha. Module orientation = R_y(alpha) . R_x(roll) . frame_R(tilt_m), with tilt_m the
station tilt relative to the machine (cap end up) and roll the carriage's angle on the
loop (v2) or the gondola's swing (paternoster), both about the machine x axis, which is
parallel to the auger.

Subcommands
  prefix   settle at the dose tilt (30 deg world by default) with the outlet plugged, open,
           dose 2 rev at 60 rpm, optional motor-off wait; saves the state the post-dose
           branches start from
  branch   from a prefix state: optional hold, optional reverse at the dose tilt, return to
           rest (nozzle up by alpha), optional reverse at rest, dwell, then transit (one
           paternoster index with its swing, a still dwell, solenoid taps, or a vertical or
           axial vibration ramp)
  v2lap    settle at rest (nozzle up by alpha), open, then one v2 lap: four 90 deg
           corner rolls at the chain's index speed, in either direction
  store    settle at rest, open, then taps (motor off) [storage check]

Model units are mm, g, s (as in the paternoster model).
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time

import numpy as np
import mujoco
from scipy.spatial.transform import Rotation as Rot

HERE = os.path.dirname(os.path.abspath(__file__))
PSIM = os.path.normpath(os.path.join(HERE, "..", "paternoster", "sim"))
sys.path.insert(0, PSIM)
import auger_geom as G  # noqa: E402
import auger_model as AM  # noqa: E402

OUT = os.path.join(HERE, "out")
GRAV = 9810.0                      # mm/s^2
DT = 1e-3
N_GRAINS = 1100
RP = 1.0
Z_CUT = G.z_cut_for_annulus(2.5 * 2 * RP)     # 8.67 mm: exit widened so the 2 mm proxy grains fit (see AUGER-SIM.md)
H = 150.0
O = np.array([0.0, 0.0, H])
RPM = 60.0
OMEGA = RPM * 2 * np.pi / 60.0
DOSE_TILT = 30.0                   # world tilt during the dose (cap end up), deg
DOSE_REVS = 2.0
TILT_RATE = 20.0                   # deg/s, the P16-P's tilt speed at the station (about 30 mm/s on the linkage)
NEAR_EXIT_MM = 15.0                # grains within this of the outlet plane count as "at the exit"

PHASES = {0: "settle", 1: "dose", 2: "stop", 3: "reverse at dose tilt", 4: "return to rest", 5: "reverse at rest",
          6: "dwell", 7: "transit", 8: "still (open)", 9: "corner 1", 10: "corner 2", 11: "corner 3", 12: "corner 4",
          13: "final dwell", 14: "taps", 15: "vertical vibration ramp", 16: "axial vibration ramp"}

# v2 geometry (cad/chain-carousel-v2/params.py): auger axis 11.65 mm inside the pitch line, 32T corners
V2_R_SPROCKET = 48.57
V2_HINGE_W = 11.65
V2_R_AUGER = V2_R_SPROCKET - V2_HINGE_W        # 36.9 mm: the auger axis' radius round a corner
V2_SPEED = 50.0                                 # mm/s (test/chain_rig.py default)
V2_ACCEL = 250.0                                # mm/s^2
V2_OMEGA = V2_SPEED / V2_R_SPROCKET             # 1.03 rad/s on a sprocket
V2_T_ACC = V2_SPEED / V2_ACCEL                  # 0.2 s


# ------------------------------------------------------------------ model
def build(tilt0_world, alpha=0.0, seed=0):
    """Paternoster auger model with the frame on a prescribed free joint. seed > 0 jitters the initial
    grain lattice by up to 0.05 mm (the lattice clears the walls by 0.15 mm), giving an independent run."""
    pos = None
    if seed:
        loc = AM.particle_lattice(N_GRAINS, RP, Z_CUT)
        loc = loc + np.random.default_rng(seed).uniform(-0.05, 0.05, loc.shape)
        pos = O[None, :] + (AM.frame_R(tilt0_world) @ loc.T).T
    xml, meta = AM.build_xml(tilt_deg=tilt0_world, n_grains=N_GRAINS, rp_mm=RP, z_cut=Z_CUT, dt=DT, solver="CG",
                             iterations=20, cone="elliptic", solref="0.004 1", mu=0.5, mu_roll=0.2, impratio=1.0,
                             noslip=0, grain_positions_world=pos)
    pat = re.compile(r'<body name="frame" pos="([^"]*)" quat="([^"]*)">')
    xml2, n = pat.subn(r'<body name="frame" pos="\1" quat="\2" gravcomp="1">\n      <freejoint name="frame_free"/>\n'
                       r'      <inertial pos="0 0 0" mass="1e6" diaginertia="1e9 1e9 1e9"/>', xml)
    assert n == 1, "frame body not found"
    m = mujoco.MjModel.from_xml_string(xml2)
    return m, meta


def R_y(a):
    c, s = np.cos(a), np.sin(a)
    return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])


def R_x(a):
    c, s = np.cos(a), np.sin(a)
    return np.array([[1, 0, 0], [0, c, -s], [0, s, c]])


def module_R(alpha_deg, roll_rad, tilt_m_deg):
    return R_y(np.radians(alpha_deg)) @ R_x(roll_rad) @ AM.frame_R(tilt_m_deg)


class Sched:
    """Per-step arrays: machine tilt (deg), roll (rad), spin command (rad/s), base acceleration
    in the machine frame (mm/s^2), tap flag, phase code."""

    def __init__(self):
        self.tilt, self.roll, self.spin, self.acc, self.tap, self.phase = [], [], [], [], [], []

    def add(self, n, tilt, roll=0.0, spin=0.0, acc=None, tap=None, phase=0):
        n = int(n)
        bc = lambda v: np.broadcast_to(np.asarray(v, float), (n,)).copy()
        self.tilt.append(bc(tilt))
        self.roll.append(bc(roll))
        self.spin.append(bc(spin))
        self.acc.append(np.zeros((n, 3)) if acc is None else np.asarray(acc, float).reshape(n, 3))
        self.tap.append(np.zeros(n, bool) if tap is None else np.asarray(tap, bool))
        self.phase.append(np.full(n, phase, int))

    def done(self):
        for k in ("tilt", "roll", "spin", "tap", "phase"):
            setattr(self, k, np.concatenate(getattr(self, k)))
        self.acc = np.concatenate(self.acc)
        self.n = len(self.tilt)
        return self


def cos_ramp(n, a, b):
    s = (np.arange(n) + 1) / n
    return a + (b - a) * (1 - np.cos(np.pi * s)) / 2


def taps(n, hz=2.0, ms=10.0):
    t = np.arange(n) * DT
    return (t % (1.0 / hz)) < ms * 1e-3


def vib(n, g_peak, hz, alpha, axial=False):
    """Sinusoidal base acceleration whose amplitude ramps linearly from 0 to g_peak, in the machine frame
    (the runner maps machine -> world with R_y(alpha)): vertical in the world, or along the auger axis
    (machine x, the axis of a module at rest) if axial."""
    t = np.arange(n) * DT
    a_w = (g_peak * GRAV) * (t / t[-1]) * np.sin(2 * np.pi * hz * t)
    e = np.array([1.0, 0.0, 0.0]) if axial else R_y(np.radians(alpha)).T @ np.array([0.0, 0.0, 1.0])
    return a_w[:, None] * e[None, :]


def v2_corner(direction):
    """One 90 deg corner at the chain's index speed: (roll increments rad, base accel in the machine frame)
    as functions of the roll angle at the start; trapezoid in angular speed (ramps of V2_T_ACC)."""
    wp = V2_OMEGA
    T = (np.pi / 2) / wp + V2_T_ACC
    n = int(round(T / DT))
    t = (np.arange(n) + 1) * DT
    w = np.minimum(1.0, np.minimum(t / V2_T_ACC, (T - t) / V2_T_ACC).clip(0)) * wp
    w *= (np.pi / 2) / (w.sum() * DT)            # exact 90 deg
    wd = np.gradient(w, DT)
    return direction * np.cumsum(w) * DT, direction * w, direction * wd


def pat_transit(n_s=2.0):
    """One paternoster index (and its dwell) as seen by the auger outlet: roll (gondola swing) and base
    acceleration (machine frame), from the MuJoCo carousel model (pat_transit.py)."""
    z = np.load(os.path.join(OUT, "pat_transit.npz"))
    t, roll, ay, az = z["t"], z["roll"], z["ay"], z["az"]
    t0 = float(z["t_move0"])
    tt = t0 + np.arange(int(round(n_s / DT))) * DT
    r = np.interp(tt, t, roll) - np.interp(t0, t, roll)   # swing relative to the station pose
    acc = np.stack([np.zeros_like(tt), np.interp(tt, t, ay), np.interp(tt, t, az)], 1)
    return r, acc


# ------------------------------------------------------------------ runner
class Runner:
    def __init__(self, m, meta, alpha, tag, record=True):
        self.m, self.meta, self.alpha, self.tag, self.record = m, meta, alpha, tag, record
        self.d = mujoco.MjData(m)
        self.g0 = m.nbody - N_GRAINS
        self.fid = m.body("frame").id
        self.mid = m.body("mount").id
        j = m.joint("frame_free").id
        self.qa, self.da = m.jnt_qposadr[j], m.jnt_dofadr[j]
        self.spin_q = m.jnt_qposadr[m.joint("spin").id]
        self.bal_q = m.jnt_qposadr[m.joint("balance").id]
        self.plug = m.geom("plug").id
        self.exit_t = np.full(N_GRAINS, np.nan)
        self.exit_ph = np.full(N_GRAINS, -1, int)
        self.logs, self.frames, self.fq = [], [], []
        self.vial = (meta["vial_bottom"], meta["vial_bottom"] + meta["vial_h_mm"], meta["vial_r_mm"])

    def open_plug(self):
        m = self.m
        m.geom_contype[self.plug] = 0
        m.geom_conaffinity[self.plug] = 0
        m.geom_rgba[self.plug, 3] = 0.0
        m.geom_group[self.plug] = 5

    def set_frame(self, R, w_world):
        d = self.d
        q = Rot.from_matrix(R).as_quat()
        d.qpos[self.qa:self.qa + 3] = O
        d.qpos[self.qa + 3:self.qa + 7] = (q[3], q[0], q[1], q[2])
        d.qvel[self.da:self.da + 3] = 0.0
        d.qvel[self.da + 3:self.da + 6] = R.T @ w_world

    def local(self):
        Rf = self.d.xmat[self.fid].reshape(3, 3)
        return (Rf.T @ (self.d.xpos[self.g0:] - O).T).T

    def classify(self, t, ph):
        loc = self.local()
        r = np.hypot(loc[:, 0], loc[:, 1])
        out = (loc[:, 2] < Z_CUT - 1.0) | (r > G.BORE_R + 2.5)
        new = out & np.isnan(self.exit_t)
        self.exit_t[new] = t
        self.exit_ph[new] = ph
        near = (~out) & (loc[:, 2] < Z_CUT + NEAR_EXIT_MM)
        p = self.d.xpos[self.g0:]
        vb, vt, vr = self.vial
        inv = (np.hypot(p[:, 0], p[:, 1]) < vr) & (p[:, 2] > vb - 2.0) & (p[:, 2] < vt)
        return int((~np.isnan(self.exit_t)).sum()), int(near.sum()), int(inv.sum()), loc

    def run(self, S, t_offset=0.0, tilt_prev=None, roll_prev=None):
        m, d = self.m, self.d
        Rprev = module_R(self.alpha, S.roll[0] if roll_prev is None else roll_prev,
                         S.tilt[0] if tilt_prev is None else tilt_prev)
        g = np.array([0, 0, -GRAV])
        Ra = R_y(np.radians(self.alpha))
        log_every = int(round(0.01 / DT))
        frame_every = int(round((1 / 30) / DT))
        wall0 = time.time()
        for k in range(S.n):
            R = module_R(self.alpha, S.roll[k], S.tilt[k])
            w = Rot.from_matrix(R @ Rprev.T).as_rotvec() / DT
            Rprev = R
            self.set_frame(R, w)
            m.opt.gravity[:] = g - Ra @ S.acc[k]
            d.ctrl[0] = S.spin[k]
            if S.tap[k]:
                d.xfrc_applied[self.mid, :3] = 4.0 * 1e6 * (R @ np.array([1.0, 0, 0]))   # 4 N, as the paternoster runs
            else:
                d.xfrc_applied[self.mid, :3] = 0.0
            mujoco.mj_step(m, d)
            t = t_offset + (k + 1) * DT
            if k % log_every == 0 or k == S.n - 1:
                nex, near, nvial, loc = self.classify(t, S.phase[k])
                self.logs.append((t, S.phase[k], S.tilt[k] - self.alpha, S.roll[k], d.qpos[self.spin_q], nex, near, nvial, d.ncon))
            if self.record and k % frame_every == 0:
                q = Rot.from_matrix(R).as_quat()
                self.frames.append(d.xpos[self.g0:].astype(np.float32).copy())
                self.fq.append((t, S.phase[k], d.qpos[self.spin_q], d.qpos[self.bal_q], q[3], q[0], q[1], q[2],
                                self.logs[-1][5], self.logs[-1][7]))
            if k % 500 == 0:
                print(f"[{self.tag}] t={t:.2f} {PHASES[S.phase[k]]:22s} tilt_w={S.tilt[k] - self.alpha:+6.1f} roll={np.degrees(S.roll[k]):+7.1f} "
                      f"out={self.logs[-1][5]} near={self.logs[-1][6]} ncon={d.ncon} wall {time.time() - wall0:.0f}s", flush=True)
        m.opt.gravity[:] = g
        return t_offset + S.n * DT

    def save(self, extra, state=False):
        os.makedirs(OUT, exist_ok=True)
        L = np.array(self.logs)
        mg = self.meta["m_grain_g"] * 1e3
        ph = self.exit_ph
        by_phase = {PHASES[p]: int((ph == p).sum()) for p in sorted(set(ph.tolist())) if p >= 0}
        res = dict(extra, tag=self.tag, alpha_deg=self.alpha, n_grains=N_GRAINS, rp_mm=RP, z_cut_mm=Z_CUT,
                   m_grain_mg=mg, exits_by_phase=by_phase,
                   exits_by_phase_mg={k: v * mg for k, v in by_phase.items()},
                   n_out_total=int((ph >= 0).sum()), near_exit_final=int(L[-1, 6]))
        arrs = dict(log=L, cols=np.array(["t", "phase", "tilt_world", "roll", "spin", "n_out", "n_near_exit", "n_vial", "ncon"]),
                    exit_t=self.exit_t, exit_ph=self.exit_ph,
                    frames=np.array(self.frames) if self.frames else np.zeros(0),
                    fq=np.array(self.fq) if self.fq else np.zeros(0))
        if state:
            arrs.update(qpos=self.d.qpos.copy(), qvel=self.d.qvel.copy(), qacc_ws=self.d.qacc_warmstart.copy(),
                        time=np.array(self.d.time))
        np.savez_compressed(os.path.join(OUT, f"{self.tag}.npz"), **arrs)
        with open(os.path.join(OUT, f"{self.tag}.json"), "w") as f:
            json.dump(res, f, indent=1)
        return res


# ------------------------------------------------------------------ subcommands
def cmd_prefix(a):
    tilt = a.dose_tilt
    m, meta = build(tilt, seed=a.seed)
    tag = a.name or ("prefix" if a.seed == 0 else f"prefix_s{a.seed}")
    R = Runner(m, meta, 0.0, tag, record=a.record)
    S = Sched()
    S.add(0.5 / DT, tilt, phase=0)
    S.done()
    t = R.run(S)
    R.open_plug()
    S = Sched()
    S.add(DOSE_REVS / (RPM / 60) / DT, tilt, spin=OMEGA, phase=1)
    if a.stop > 0:
        S.add(a.stop / DT, tilt, phase=2)
    S.done()
    t = R.run(S, t_offset=t)
    res = R.save(dict(kind="prefix", seed=a.seed, dose_tilt_world=tilt, stop_s=a.stop, rpm=RPM, dose_revs=DOSE_REVS), state=True)
    print(json.dumps(res, indent=1))


def cmd_branch(a):
    pname = a.prefix or ("prefix" if a.seed == 0 else f"prefix_s{a.seed}")
    st = np.load(os.path.join(OUT, pname + ".npz"))
    dose_tilt = json.load(open(os.path.join(OUT, pname + ".json")))["dose_tilt_world"]
    alpha = a.alpha
    m, meta = build(dose_tilt)
    R = Runner(m, meta, alpha, a.tag, record=a.record)
    R.open_plug()
    d = R.d
    d.qpos[:] = st["qpos"]
    d.qvel[:] = st["qvel"]
    d.qacc_warmstart[:] = st["qacc_ws"]
    d.time = float(st["time"])
    R.exit_t[:] = st["exit_t"]
    R.exit_ph[:] = st["exit_ph"]
    t0 = float(st["time"])
    tilt_dose_m = dose_tilt + alpha              # machine tilt that gives the dose tilt in the world
    S = Sched()
    if a.hold > 0:
        S.add(a.hold / DT, tilt_dose_m, phase=2)
    if a.protocol == "revdose" and a.R > 0:
        S.add(a.R / (RPM / 60) / DT, tilt_dose_m, spin=-OMEGA, phase=3)
    n_ret = int(round(tilt_dose_m / TILT_RATE / DT))
    S.add(n_ret, cos_ramp(n_ret, tilt_dose_m, 0.0), phase=4)
    if a.protocol == "returnrev" and a.R > 0:
        S.add(a.R / (RPM / 60) / DT, 0.0, spin=-OMEGA, phase=5)
    S.add(0.5 / DT, 0.0, phase=6)
    nt = int(round(a.transit_s / DT))
    if a.transit == "pat":
        roll, acc = pat_transit(a.transit_s)
        S.add(nt, 0.0, roll=roll, acc=acc, phase=7)
    elif a.transit == "taps":
        S.add(nt, 0.0, tap=taps(nt), phase=14)
    elif a.transit == "vib":
        S.add(nt, 0.0, acc=vib(nt, a.vib_g, a.vib_hz, alpha), phase=15)
    elif a.transit == "avib":
        S.add(nt, 0.0, acc=vib(nt, a.vib_g, a.vib_hz, alpha, axial=True), phase=16)
    else:
        S.add(nt, 0.0, phase=7)
    S.done()
    R.run(S, t_offset=t0, tilt_prev=tilt_dose_m, roll_prev=0.0)
    res = R.save(dict(kind="branch", seed=a.seed, prefix=pname, hold_s=a.hold, protocol=a.protocol, R_rev=a.R, transit=a.transit, transit_s=a.transit_s,
                      vib_g=a.vib_g if a.transit in ("vib", "avib") else None,
                      vib_hz=a.vib_hz if a.transit in ("vib", "avib") else None,
                      tilt_rate_deg_s=TILT_RATE, dose_tilt_world=dose_tilt))
    print(json.dumps(res, indent=1))


def cmd_v2lap(a):
    alpha, direction = a.alpha, (1.0 if a.dir == "fwd" else -1.0)
    m, meta = build(-alpha, alpha, seed=a.seed)
    R = Runner(m, meta, alpha, a.tag, record=a.record)
    S = Sched()
    S.add(0.5 / DT, 0.0, phase=0)
    S.done()
    t = R.run(S)
    R.open_plug()
    S = Sched()
    S.add(0.3 / DT, 0.0, phase=8)
    roll0 = 0.0
    for c in range(a.corners):
        dpsi, w, wd = v2_corner(direction)
        psi = roll0 + dpsi
        # outlet point accel on the corner (machine frame): r (psi'' u + psi'^2 w), u = travel, w = inward
        u = np.stack([np.zeros_like(psi), np.cos(psi), np.sin(psi)], 1)
        win = np.stack([np.zeros_like(psi), -np.sin(psi), np.cos(psi)], 1)
        acc = V2_R_AUGER * (wd[:, None] * u + (w ** 2)[:, None] * win)
        S.add(len(psi), 0.0, roll=psi, acc=acc, phase=9 + min(c, 3))
        roll0 = float(psi[-1])
        S.add(0.4 / DT, 0.0, roll=roll0, phase=9 + min(c, 3))
    S.add(0.3 / DT, 0.0, roll=roll0, phase=13)
    S.done()
    R.run(S, t_offset=t, tilt_prev=0.0, roll_prev=0.0)
    res = R.save(dict(kind="v2lap", seed=a.seed, direction=a.dir, corners=a.corners, v2_speed_mm_s=V2_SPEED, v2_accel_mm_s2=V2_ACCEL,
                      auger_corner_radius_mm=V2_R_AUGER,
                      note="straights between corners compressed to 0.4 s dwells; the tube turns with the module (clamp friction)"))
    print(json.dumps(res, indent=1))


def cmd_store(a):
    alpha = a.alpha
    m, meta = build(-alpha, alpha, seed=a.seed)
    R = Runner(m, meta, alpha, a.tag, record=a.record)
    S = Sched()
    S.add(0.5 / DT, 0.0, phase=0)
    S.done()
    t = R.run(S)
    R.open_plug()
    n = int(round(a.seconds / DT))
    S = Sched()
    S.add(n, 0.0, tap=taps(n), phase=14)
    S.done()
    R.run(S, t_offset=t, tilt_prev=0.0)
    res = R.save(dict(kind="store", seed=a.seed, seconds=a.seconds, taps="4 N x 10 ms at 2 Hz"))
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd")
    p = sub.add_parser("prefix")
    p.add_argument("--seed", type=int, default=0)
    p.add_argument("--dose-tilt", type=float, default=DOSE_TILT)
    p.add_argument("--stop", type=float, default=0.3, help="motor-off time at the dose tilt before the state is saved")
    p.add_argument("--name", default="")
    p.add_argument("--record", action="store_true")
    b = sub.add_parser("branch")
    b.add_argument("--seed", type=int, default=0)
    b.add_argument("--prefix", default="", help="prefix state to start from (default prefix / prefix_s<seed>)")
    b.add_argument("--hold", type=float, default=0.0, help="stay at the dose tilt, motor off, before anything else (s)")
    b.add_argument("--alpha", type=float, default=0.0)
    b.add_argument("--protocol", choices=["return", "revdose", "returnrev"], default="return")
    b.add_argument("--R", type=float, default=0.0, help="reverse revolutions")
    b.add_argument("--transit", choices=["pat", "still", "taps", "vib", "avib"], default="pat")
    b.add_argument("--vib-g", type=float, default=1.5, help="vib: peak vertical acceleration at the end of the ramp, in g")
    b.add_argument("--vib-hz", type=float, default=25.0)
    b.add_argument("--transit-s", type=float, default=2.0)
    b.add_argument("--record", action="store_true")
    b.add_argument("--tag", required=True)
    v = sub.add_parser("v2lap")
    v.add_argument("--seed", type=int, default=0)
    v.add_argument("--alpha", type=float, default=0.0)
    v.add_argument("--dir", choices=["fwd", "rev"], default="fwd")
    v.add_argument("--corners", type=int, default=4)
    v.add_argument("--record", action="store_true")
    v.add_argument("--tag", required=True)
    s = sub.add_parser("store")
    s.add_argument("--seed", type=int, default=0)
    s.add_argument("--alpha", type=float, default=0.0)
    s.add_argument("--seconds", type=float, default=2.0)
    s.add_argument("--record", action="store_true")
    s.add_argument("--tag", required=True)
    a = ap.parse_args()
    {"prefix": cmd_prefix, "branch": cmd_branch, "v2lap": cmd_v2lap, "store": cmd_store}[a.cmd](a)
