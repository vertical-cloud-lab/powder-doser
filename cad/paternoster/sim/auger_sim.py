"""MuJoCo granular-proxy simulation of the lab's rotating auger cartridge dosing into a vial.

Subcommands
  run   one dosing run (settle with the outlet plugged, open, rotate, stop), logs the
        balance reading / grain counts and 30 fps grain snapshots for the video
  heap  angle-of-repose check of the grain contact model (cylinder-collapse heap)

Examples (from cad/paternoster/sim):
  python auger_sim.py run --tilt 30 --tag t30
  python auger_sim.py run --tilt 30 --tap-hz 2 --tap-n 4 --tag t30_tap
  python auger_sim.py heap
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time

import numpy as np
import mujoco

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import auger_geom as G  # noqa: E402
import auger_model as AM  # noqa: E402

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out", "auger")
MM = 1.0          # model units are mm, g, s
GRAV = 9810.0     # mm/s^2


def run(a):
    os.makedirs(OUT, exist_ok=True)
    z_cut = G.z_cut_for_annulus(a.annulus_d * 2 * a.rp) if a.exit == "scaled" else 0.0
    xml, meta = AM.build_xml(tilt_deg=a.tilt, n_grains=a.n, rp_mm=a.rp, z_cut=z_cut, dt=a.dt,
                             solver="CG", iterations=a.iters, cone="elliptic",
                             solref=f"{max(0.004, 2 * a.dt):g} 1", mu=a.mu, mu_roll=a.mu_roll,
                             impratio=a.impratio, noslip=a.noslip)
    m = mujoco.MjModel.from_xml_string(xml)
    d = mujoco.MjData(m)
    n = a.n
    g0 = m.nbody - n                       # first grain body
    aid, mid = m.body("auger").id, m.body("mount").id
    plug = m.geom("plug").id
    spin_q = m.jnt_qposadr[m.joint("spin").id]
    bal_q = m.jnt_qposadr[m.joint("balance").id]
    mount_q = m.jnt_qposadr[m.joint("mount").id]
    O = np.array([0, 0, meta["H"]])
    Rf = AM.frame_R(a.tilt)
    tap_dir = Rf @ np.array([1.0, 0, 0])   # perpendicular to the auger axis, in the vertical plane
    vial_c = np.array([0, 0])
    vial_bot, vial_top = meta["vial_bottom"], meta["vial_bottom"] + meta["vial_h_mm"] * MM
    mg = meta["m_grain_g"]
    k_bal = meta["balance_k"] * 1000.0     # N/m -> g/s^2

    def counts():
        p = d.xpos[g0:]
        loc = (Rf.T @ (p - O).T).T / MM                 # auger-frame-ish (tilt only, ignoring spin)
        rr = np.hypot(p[:, 0] - vial_c[0], p[:, 1] - vial_c[1])
        in_vial = (rr < meta["vial_r_mm"] * MM) & (p[:, 2] > vial_bot - 2.0) & (p[:, 2] < vial_top)
        exited = loc[:, 2] < z_cut - 1.0
        floor = p[:, 2] < vial_bot - 3.0
        return int(in_vial.sum()), int(exited.sum()), int(floor.sum())

    # ---- settle with the outlet plugged, motor off
    t0 = time.time()
    d.ctrl[0] = 0.0
    n_settle = int(a.settle / a.dt)
    for _ in range(n_settle):
        mujoco.mj_step(m, d)
    v = np.linalg.norm(d.cvel[g0:, 3:], axis=1)
    print(f"[{a.tag}] settled {a.settle}s in {time.time() - t0:.0f}s wall, vmax {v.max():.3f} m/s, ncon {d.ncon}", flush=True)
    loc0 = (Rf.T @ (d.xpos[g0:] - O).T).T / MM
    fill = dict(z_min=float(loc0[:, 2].min()), z_max=float(np.percentile(loc0[:, 2], 99)), n_out=int((np.hypot(loc0[:, 0], loc0[:, 1]) > G.BORE_R + 1).sum()))
    # balance zero (tare) with the empty vial after settling
    q_tare = d.qpos[bal_q]
    # ---- open the outlet and dose
    m.geom_contype[plug] = 0
    m.geom_conaffinity[plug] = 0
    m.geom_rgba[plug, 3] = 0.0
    m.geom_group[plug] = 5
    omega = a.rpm * 2 * np.pi / 60
    t_rot = a.revs / (a.rpm / 60)
    t_rev = a.reverse_revs / (a.rpm / 60) if a.reverse_revs > 0 else 0.0
    T = t_rot + t_rev + a.stop
    nsteps = int(T / a.dt)
    log_every = max(1, int(0.01 / a.dt))
    frame_every = max(1, int(round((1 / 30) / a.dt)))
    logs, frames, fq = [], [], []
    tap_period = 1.0 / a.tap_hz if a.tap_hz > 0 else None
    t_start = d.time
    wall0 = time.time()
    for k in range(nsteps + 1):
        t = d.time - t_start
        if t < t_rot:
            d.ctrl[0] = omega
        elif t < t_rot + t_rev:
            d.ctrl[0] = -omega
        else:
            d.ctrl[0] = 0.0
        taps_on = tap_period is not None and (a.tap_when == "always" or (a.tap_when == "stop" and t >= t_rot + t_rev)
                                               or (a.tap_when == "rotate" and t < t_rot))
        if taps_on and (t % tap_period) < a.tap_ms * 1e-3:
            d.xfrc_applied[mid, :3] = a.tap_n * 1e6 * tap_dir    # N -> g mm/s^2
        else:
            d.xfrc_applied[mid, :3] = 0.0
        if k % log_every == 0:
            nv_, ne_, nf_ = counts()
            reading = -k_bal * (d.qpos[bal_q] - q_tare) / GRAV      # g, spring force
            logs.append((t, d.qpos[spin_q], nv_, ne_, nf_, reading, d.qpos[mount_q], d.ncon))
        if a.record and k % frame_every == 0:
            frames.append(d.xpos[g0:].astype(np.float32).copy())
            fq.append((t, d.qpos[spin_q], d.qpos[mount_q], d.qpos[bal_q], counts()[0], counts()[1]))
        if k % int(0.5 / a.dt) == 0:
            print(f"[{a.tag}] t={t:.2f}s rev={d.qpos[spin_q] / (2 * np.pi):+.2f} vial={logs[-1][2]} exited={logs[-1][3]} "
                  f"floor={logs[-1][4]} ncon={d.ncon} wall {time.time() - wall0:.0f}s", flush=True)
        mujoco.mj_step(m, d)
    L = np.array(logs)
    res = dict(meta, tag=a.tag, rpm=a.rpm, revs=a.revs, reverse_revs=a.reverse_revs, stop_s=a.stop, settle_s=a.settle,
               tap_hz=a.tap_hz, tap_n=a.tap_n, tap_ms=a.tap_ms, tap_when=a.tap_when, exit=a.exit,
               annulus_over_d=a.annulus_d, fill=fill, wall_s=time.time() - t0)
    # summary numbers
    t, ang, nvial, nex, nfl = L[:, 0], L[:, 1], L[:, 2], L[:, 3], L[:, 4]
    i_rot = np.searchsorted(t, t_rot)
    i_rev = np.searchsorted(t, t_rot + t_rev)
    res["n_exited_end_rotation"] = int(nex[min(i_rot, len(t) - 1)])
    res["n_exited_end_reverse"] = int(nex[min(i_rev, len(t) - 1)])
    res["n_exited_final"] = int(nex[-1])
    res["n_in_vial_final"] = int(nvial[-1])
    res["n_floor_final"] = int(nfl[-1])
    res["mass_exited_rotation_mg"] = res["n_exited_end_rotation"] * mg * 1e3
    res["mass_vial_final_mg"] = res["n_in_vial_final"] * mg * 1e3
    res["afterflow_mg"] = (res["n_exited_final"] - res["n_exited_end_reverse"]) * mg * 1e3
    # dose per revolution: whole rotation phase, and after the first revolution (steady)
    t1 = min(1.0 / (a.rpm / 60), t_rot)
    i1 = np.searchsorted(t, t1)
    res["dose_per_rev_mg"] = res["mass_exited_rotation_mg"] / a.revs if a.revs > 0 else 0.0
    if a.revs > 1:
        res["dose_per_rev_after_first_mg"] = (nex[i_rot] - nex[i1]) * mg * 1e3 / (a.revs - t1 * a.rpm / 60)
    res["flow_rate_mg_s"] = res["mass_exited_rotation_mg"] / t_rot if t_rot > 0 else 0.0
    per_rev = []
    for r in range(int(a.revs)):
        ia, ib = np.searchsorted(t, r * 60 / a.rpm), np.searchsorted(t, (r + 1) * 60 / a.rpm)
        per_rev.append(float((nex[min(ib, len(t) - 1)] - nex[ia]) * mg * 1e3))
    res["dose_each_rev_mg"] = per_rev
    res["balance_reading_final_mg"] = float(np.mean(L[-20:, 5]) * 1e3)
    np.savez_compressed(os.path.join(OUT, f"run_{a.tag}.npz"), log=L,
                        cols=np.array(["t", "spin", "n_vial", "n_exited", "n_floor", "balance_g", "mount_q_mm", "ncon"]),
                        frames=np.array(frames) if frames else np.zeros(0), fq=np.array(fq) if fq else np.zeros(0))
    with open(os.path.join(OUT, f"run_{a.tag}.json"), "w") as f:
        json.dump(res, f, indent=1)
    print(f"[{a.tag}] done: exited {res['n_exited_final']} ({res['mass_exited_rotation_mg']:.0f} mg in rotation), "
          f"{res['dose_per_rev_mg']:.0f} mg/rev, wall {res['wall_s']:.0f}s", flush=True)


def heap(a):
    """Cylinder-collapse heap: grains in a 10 mm radius column released onto a rough plate."""
    os.makedirs(OUT, exist_ok=True)
    rp = a.rp * MM
    mg = 2160e-6 * 4 / 3 * np.pi * rp ** 3     # g
    s = 2.08 * rp
    pts = []
    zs = np.arange(rp + 0.5, 200.0, s)
    for z in zs:
        for x in np.arange(-10.0, 10.0, s):
            for y in np.arange(-10.0, 10.0, s):
                if x * x + y * y < (10.0 - rp) ** 2:
                    pts.append((x, y, z))
        if len(pts) >= a.n:
            break
    pts = pts[:a.n]
    # rough plate: a layer of fixed grains so the base cannot slide
    base = [(x, y, -rp * 0.2) for x in np.arange(-40.0, 40.0, 2 * rp) for y in np.arange(-40.0, 40.0, 2 * rp)
            if x * x + y * y < 35.0 ** 2]
    bx = "\n".join(f'<geom type="sphere" size="{rp}" pos="{x} {y} {z}" class="solid"/>' for x, y, z in base)
    gx = "\n".join(f'<body pos="{x} {y} {z}"><freejoint/><geom class="grain"/></body>' for x, y, z in pts)
    xml = f"""<mujoco><option timestep="{a.dt}" gravity="0 0 -9810" solver="CG" iterations="{a.iters}" cone="elliptic" integrator="implicitfast" impratio="{a.impratio}" noslip_iterations="{a.noslip}"/>
<size memory="800M"/>
<default><geom solref="{max(0.004, 2 * a.dt):g} 1" solimp="0.9 0.95 0.5"/>
<default class="solid"><geom contype="1" conaffinity="0" condim="3" friction="{a.mu} 0.2 {a.mu_roll}"/></default>
<default class="grain"><geom type="sphere" size="{rp}" mass="{mg}" contype="2" conaffinity="3" condim="6" friction="{a.mu} 0.2 {a.mu_roll}"/></default></default>
<worldbody>{bx}
{gx}</worldbody></mujoco>"""
    m = mujoco.MjModel.from_xml_string(xml)
    d = mujoco.MjData(m)
    t0 = time.time()
    for _ in range(int(a.settle / a.dt)):
        mujoco.mj_step(m, d)
    p = d.xpos[1:]
    r = np.hypot(p[:, 0], p[:, 1])
    z = p[:, 2]
    # heap surface: max height in radial bins, fit slope over the flank
    bins = np.arange(0, r.max() + 1.5, 1.5)
    rc, hz = [], []
    for b0, b1 in zip(bins[:-1], bins[1:]):
        sel = (r >= b0) & (r < b1)
        if sel.sum() > 3:
            rc.append(0.5 * (b0 + b1))
            hz.append(np.percentile(z[sel], 95))
    rc, hz = np.array(rc), np.array(hz)
    hmax = hz.max()
    flank = (hz < 0.85 * hmax) & (hz > 0.15 * hmax)
    slope = np.polyfit(rc[flank], hz[flank], 1)[0] if flank.sum() >= 2 else np.nan
    ang = float(np.degrees(np.arctan(-slope)))
    res = dict(n=len(pts), rp_mm=a.rp, mu=a.mu, mu_roll=a.mu_roll, impratio=a.impratio, noslip=a.noslip, angle_of_repose_deg=ang, heap_h_mm=float(hmax),
               heap_r_mm=float(rc[hz > 1.5 * a.rp].max()) if (hz > 1.5 * a.rp).any() else None,
               profile_r_mm=rc.tolist(), profile_h_mm=hz.tolist(), wall_s=time.time() - t0)
    with open(os.path.join(OUT, f"heap_mu{a.mu}_roll{a.mu_roll}_imp{a.impratio:g}_ns{a.noslip}.json"), "w") as f:
        json.dump(res, f, indent=1)
    print(f"heap mu={a.mu} roll={a.mu_roll}: angle of repose {ang:.1f} deg, h {hmax:.1f} mm, wall {time.time() - t0:.0f}s")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd")
    r = sub.add_parser("run")
    r.add_argument("--tilt", type=float, default=30.0)
    r.add_argument("--rpm", type=float, default=60.0)
    r.add_argument("--revs", type=float, default=3.0)
    r.add_argument("--reverse-revs", type=float, default=0.0)
    r.add_argument("--stop", type=float, default=0.8)
    r.add_argument("--settle", type=float, default=0.5)
    r.add_argument("--n", type=int, default=1100)
    r.add_argument("--rp", type=float, default=1.0)
    r.add_argument("--exit", choices=["scaled", "cad"], default="scaled")
    r.add_argument("--annulus-d", type=float, default=2.5, help="exit annulus width / grain diameter (salt in the CAD exit: 2.5)")
    r.add_argument("--dt", type=float, default=1e-3)
    r.add_argument("--iters", type=int, default=20)
    r.add_argument("--mu", type=float, default=0.5)
    r.add_argument("--mu-roll", type=float, default=0.2, help="rolling friction length, mm")
    r.add_argument("--tap-hz", type=float, default=0.0)
    r.add_argument("--tap-n", type=float, default=4.0)
    r.add_argument("--tap-ms", type=float, default=10.0)
    r.add_argument("--tap-when", choices=["always", "rotate", "stop"], default="always")
    r.add_argument("--record", action="store_true")
    r.add_argument("--impratio", type=float, default=1.0)
    r.add_argument("--noslip", type=int, default=0)
    r.add_argument("--tag", default="run")
    h = sub.add_parser("heap")
    h.add_argument("--n", type=int, default=1200)
    h.add_argument("--rp", type=float, default=1.0)
    h.add_argument("--mu", type=float, default=0.5)
    h.add_argument("--mu-roll", type=float, default=0.2)
    h.add_argument("--dt", type=float, default=1e-3)
    h.add_argument("--iters", type=int, default=30)
    h.add_argument("--settle", type=float, default=1.5)
    h.add_argument("--impratio", type=float, default=1.0)
    h.add_argument("--noslip", type=int, default=0)
    a = ap.parse_args()
    {"run": run, "heap": heap}[a.cmd](a)
