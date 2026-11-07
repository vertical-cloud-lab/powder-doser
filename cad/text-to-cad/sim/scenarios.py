"""DEM scenarios for the powder-doser auger (issue #172).  Run ONE per process:

    /tmp/simenv/bin/python sim/scenarios.py repose      # angle-of-repose check
    /tmp/simenv/bin/python sim/scenarios.py settle      # seed + settle the auger bed (needed first)
    /tmp/simenv/bin/python sim/scenarios.py dose 22.5   # tilt, then rotate: dose per revolution
    /tmp/simenv/bin/python sim/scenarios.py leaktap     # 45 deg, no rotation: leakage, then taps
    /tmp/simenv/bin/python sim/scenarios.py sequence    # tilt -> rotate -> taps -> tilt back (GIF)

Results go to sim/results/*.json; frames for the GIF and the settled bed go to
/tmp/simframes (large, regenerable, not committed).
"""
from __future__ import annotations

import json
import math
import os
import sys
import time

import numpy as np

import dem
from dem import G, MM

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "results")
FRAMES = os.environ.get("SIM_FRAMES", "/tmp/simframes")
os.makedirs(RES, exist_ok=True)
os.makedirs(FRAMES, exist_ok=True)

# ---- coarse-grained powder + contact parameters ----------------------------
D_MEAN = 0.9 * MM            # sphere diameter, uniform +-11 % (0.8 .. 1.0 mm)
D_SPREAD = 0.1 * MM
RHO = 1500.0                 # solid density, kg/m^3 (organic / salt-like lab powder)
KN = 25.0                    # normal stiffness, N/m (softened; overlaps checked in logs)
E_REST = 0.3                 # restitution
MU_PP = float(os.environ.get("SIM_MUPP", 0.5))   # sliding friction particle-particle
MU_PW = 0.35                 # sliding friction particle-PLA wall
MUR_PP = MUR_PW = float(os.environ.get("SIM_MUR", 0.3))   # EPSD rolling coefficient (calibrated)
ETA_R = 0.3                  # rolling damping ratio (EPSD)
BOND = float(os.environ.get("SIM_BOND", 0.0))   # cohesion: F_coh = BOND * m_mean * g
COH_GAP_D = 0.05             # cohesion acts up to a gap of 0.05 d
SUFFIX = f"_bo{BOND:g}" if BOND > 0 else ""
DT = 1.5e-5                  # time step, s (~ t_c/20 for the lightest pair)
# ---- simulated section and operating point --------------------------------
Z_CAP = 6.0 * MM             # capture plane: annular gap there 3.8 mm ~ 4.2 d
Z_TOP = dem.Z_FUN + 2.5 * dem.PITCH   # artificial (frictionless) top of the section
Y_FILL = -2.0 * MM           # initial fill: powder below y = -2 mm (about 41 % of the annulus)
RPM_TUBE = 60.0              # tube speed (stepper 132 rpm through 20T:44T)
TAP_A, TAP_T = 0.30 * MM, 4e-3   # tap = tube displacement u = -A sin^2(pi t/T) along y
TAP_PEAK = TAP_A * 2 * math.pi ** 2 / TAP_T ** 2   # peak acceleration, m/s^2

BLOCK = 0.005                # logging interval, s


def params(mode=0, rcyl=0.0, zcap=Z_CAP):
    p = np.zeros(dem.NPRM)
    p[dem.P_KN], p[dem.P_KT] = KN, KN * 2.0 / 7.0
    p[dem.P_MUPP], p[dem.P_MUPW] = MU_PP, MU_PW
    p[dem.P_MURPP], p[dem.P_MURPW] = MUR_PP, MUR_PW
    p[dem.P_ZETA] = dem.zeta_from_e(E_REST)
    p[dem.P_ZTOP], p[dem.P_ZCAP], p[dem.P_RCYL] = Z_TOP, zcap, rcyl
    p[dem.P_ETAR] = ETA_R
    if BOND > 0:
        p[dem.P_FCOH] = BOND * RHO * math.pi / 6 * D_MEAN ** 3 * G
        p[dem.P_GAP] = COH_GAP_D * D_MEAN
    return p


def contact_time():
    m = RHO * math.pi / 6 * (D_MEAN - D_SPREAD) ** 3
    z = dem.zeta_from_e(E_REST)
    return math.pi / (math.sqrt(KN / (m / 2)) * math.sqrt(1 - z * z))


def lattice(lo, hi, a, rng):
    g = [np.arange(l + a / 2, h - a / 2 + 1e-12, a) for l, h in zip(lo, hi)]
    pts = np.stack(np.meshgrid(*g, indexing="ij"), -1).reshape(-1, 3)
    return pts + rng.uniform(-0.02 * a, 0.02 * a, pts.shape)


def smooth_kf(t, kf):
    """Piecewise cosine-smoothed interpolation through keyframes [(t, v), ...]."""
    ts = np.array([k[0] for k in kf])
    vs = np.array([k[1] for k in kf], dtype=float)
    out = np.full_like(t, vs[-1], dtype=float)
    out[t <= ts[0]] = vs[0]
    for a in range(len(kf) - 1):
        m = (t > ts[a]) & (t <= ts[a + 1])
        f = (t[m] - ts[a]) / (ts[a + 1] - ts[a])
        out[m] = vs[a] + (vs[a + 1] - vs[a]) * (0.5 - 0.5 * np.cos(np.pi * f))
    return out


def tap_accel(t, taps):
    """Pseudo-acceleration (+y) in the tube frame from solenoid taps at times taps."""
    a = np.zeros_like(t)
    for t0 in taps:
        m = (t >= t0) & (t < t0 + TAP_T)
        a[m] += TAP_PEAK * np.cos(2 * np.pi * (t[m] - t0) / TAP_T)
    return a


def make_auger(seed=1):
    rng = np.random.default_rng(seed)
    prm = params()
    a = (D_MEAN + D_SPREAD) * 1.02
    pts = lattice((-dem.R_BORE, -dem.R_BORE, dem.Z_FUN + 0.5 * MM),
                  (dem.R_BORE, Y_FILL, Z_TOP), a, rng)
    rad = 0.5 * rng.uniform(D_MEAN - D_SPREAD, D_MEAN + D_SPREAD, len(pts))
    ok = dem.free_space_ok(pts, rad, prm, margin=0.03 * MM)
    pts, rad = pts[ok], rad[ok]
    lo = (-dem.R_BORE - 1 * MM, -dem.R_BORE - 1 * MM, Z_CAP - 2 * MM)
    hi = (dem.R_BORE + 1 * MM, dem.R_BORE + 1 * MM, Z_TOP + 1 * MM)
    return dem.DEM(pts, rad, RHO, 0, prm, DT, lo, hi)


def run(sim, t_end, tilt_kf, omega_kf, taps=(), frame_dt=None, phase=None, verbose=True):
    """Advance to t_end following the tilt (deg) and tube-speed (rad/s) keyframes.
    Returns the log (dict of lists) and frames (list of dicts) if frame_dt."""
    log = {k: [] for k in ("t", "m_disp_mg", "tilt_deg", "theta_deg", "omega_rpm",
                           "n_active", "ke_uJ", "max_overlap_pct", "tap_g")}
    frames = []
    nb = int(round(BLOCK / sim.dt))
    nb += nb % 2
    next_frame = sim.t
    w0 = time.time()
    while sim.t < t_end - 1e-9:
        if frame_dt is not None and sim.t >= next_frame - 1e-9:
            frames.append(dict(t=sim.t, pos=sim.pos.astype(np.float32).copy(),
                               active=sim.active.copy(), theta=sim.theta,
                               tilt=float(smooth_kf(np.array([sim.t]), tilt_kf)[0]),
                               m_disp=sim.m_disp, phase=phase(sim.t) if phase else ""))
            next_frame += frame_dt
        ts = sim.t + (np.arange(nb) + 0.5) * sim.dt
        beta = np.radians(smooth_kf(ts, tilt_kf))
        om = np.interp(ts, [k[0] for k in omega_kf], [k[1] for k in omega_kf])
        at = tap_accel(ts, taps)
        g = np.stack([np.zeros_like(ts), -G * np.cos(beta) + at, -G * np.sin(beta)], 1)
        omax = sim.advance(nb, np.ascontiguousarray(om), np.ascontiguousarray(g))
        log["t"].append(round(sim.t, 6))
        log["m_disp_mg"].append(sim.m_disp * 1e6)
        log["tilt_deg"].append(float(np.degrees(beta[-1])))
        log["theta_deg"].append(float(np.degrees(sim.theta)))
        log["omega_rpm"].append(float(om[-1] * 60 / (2 * np.pi)))
        log["n_active"].append(int(sim.active.sum()))
        log["ke_uJ"].append(sim.kinetic_energy() * 1e6)
        log["max_overlap_pct"].append(100 * omax)
        log["tap_g"].append(float(np.abs(at).max() / G))
        if verbose and len(log["t"]) % 20 == 0:
            print(f"t={sim.t:.3f}s disp={sim.m_disp*1e6:.1f}mg tilt={np.degrees(beta[-1]):.1f} "
                  f"theta={np.degrees(sim.theta):.0f} act={sim.active.sum()} lost={sim.n_lost} "
                  f"ovl={100*omax:.2f}% KE={sim.kinetic_energy()*1e6:.3f}uJ wall={time.time()-w0:.0f}s",
                  flush=True)
    return log, frames


def save_frames(name, frames, sim, extra=None):
    np.savez_compressed(
        os.path.join(FRAMES, f"{name}_frames.npz"),
        t=np.array([f["t"] for f in frames]), pos=np.stack([f["pos"] for f in frames]),
        active=np.stack([f["active"] for f in frames]), theta=np.array([f["theta"] for f in frames]),
        tilt=np.array([f["tilt"] for f in frames]), m_disp=np.array([f["m_disp"] for f in frames]),
        phase=np.array([f["phase"] for f in frames]), rad=sim.rad, **(extra or {}))


def common_meta(sim, wall):
    return dict(n_particles=int(sim.N), d_mean_mm=D_MEAN / MM, d_range_mm=[(D_MEAN - D_SPREAD) / MM,
                (D_MEAN + D_SPREAD) / MM], rho_solid=RHO, k_n=KN, k_t=KN * 2 / 7, e=E_REST,
                mu_pp=MU_PP, mu_pw=MU_PW, mur_pp=MUR_PP, mur_pw=MUR_PW, eta_r=ETA_R,
                rolling_model="EPSD (Ai et al. 2011 type C)", bond=BOND, coh_gap_d=COH_GAP_D, dt=DT,
                t_contact=contact_time(), z_capture_mm=Z_CAP / MM, z_top_mm=Z_TOP / MM,
                rpm_tube=RPM_TUBE, froude=(RPM_TUBE * 2 * math.pi / 60) ** 2 * dem.R_BORE / G,
                tap_amplitude_mm=TAP_A / MM, tap_duration_ms=TAP_T * 1e3,
                tap_peak_g=TAP_PEAK / G, wall_time_s=round(wall, 1), n_lost=int(sim.n_lost))


def dump(name, obj):
    with open(os.path.join(RES, f"{name}.json"), "w") as f:
        json.dump(obj, f, indent=1)
    print("wrote", os.path.join(RES, f"{name}.json"))


# ---------------------------------------------------------------------------
def sc_repose():
    """Lifted-cylinder heap on a base of glued (fixed) spheres.  A column of radius
    7 mm and height 27 mm drains as the frictionless cylinder lifts at 50 mm/s; the
    flank slope is fitted between 25 % and 75 % of the heap height."""
    rng = np.random.default_rng(3)
    rc, hcol, rbase = 7.0 * MM, 27.0 * MM, 17.0 * MM
    gb = np.arange(-rbase, rbase + 1e-9, 0.9 * MM)
    X, Y = np.meshgrid(gb, gb)
    base = np.c_[X.ravel(), Y.ravel()]
    base = base[np.hypot(base[:, 0], base[:, 1]) < rbase] + rng.uniform(-0.1 * MM, 0.1 * MM, (1, 2))
    base += rng.uniform(-0.1 * MM, 0.1 * MM, base.shape)
    rbs = 0.5 * rng.uniform(D_MEAN - D_SPREAD, D_MEAN + D_SPREAD, len(base))
    a = (D_MEAN + D_SPREAD) * 1.02
    pts = lattice((-rc, -rc, 1.4 * MM), (rc, rc, hcol), a, rng)
    pts = pts[np.hypot(pts[:, 0], pts[:, 1]) < rc - 0.55 * MM]
    rad = 0.5 * rng.uniform(D_MEAN - D_SPREAD, D_MEAN + D_SPREAD, len(pts))
    allp = np.vstack([np.c_[base, rbs], pts])
    allr = np.r_[rbs, rad]
    fixed = np.r_[np.ones(len(base), bool), np.zeros(len(pts), bool)]
    prm = params(mode=1, rcyl=rc, zcap=0.0)
    prm[dem.P_MUPW], prm[dem.P_MURPW], prm[dem.P_RDISC] = 1.0, 0.5, rbase + 1 * MM
    sim = dem.DEM(allp, allr, RHO, 1, prm, DT, (-rbase - 2 * MM, -rbase - 2 * MM, -1 * MM),
                  (rbase + 2 * MM, rbase + 2 * MM, hcol + MM), fixed=fixed)
    w0 = time.time()
    nb = 2 * int(round(0.0005 / DT / 2))
    om = np.zeros(nb)
    g = np.tile([0.0, 0.0, -G], (nb, 1))
    while sim.t < 0.12:                      # settle inside the cylinder
        sim.advance(nb, om, g)
    v_lift = 0.05                            # m/s
    t_lift0 = sim.t
    while True:
        sim.prm[dem.P_ZCAP] = (sim.t - t_lift0) * v_lift   # lower edge height of the cylinder
        if sim.prm[dem.P_ZCAP] > hcol + 2 * MM:
            sim.prm[dem.P_RCYL] = 0.0
            if sim.kinetic_energy() < 1e-9 or sim.t > t_lift0 + 0.95:
                break
        sim.advance(nb, om, g)
    mob = sim.active & ~sim.fixed
    p = sim.pos[mob]
    r = np.hypot(p[:, 0], p[:, 1])
    ztop = p[:, 2] + sim.rad[mob]
    zb = 2 * np.median(rbs)                  # top of the glued layer
    edges = np.arange(0, rbase + 1e-9, 1.0 * MM)
    rb, hb = [], []
    for lo_, hi_ in zip(edges[:-1], edges[1:]):
        m = (r >= lo_) & (r < hi_)
        if m.sum() >= 3:
            rb.append(0.5 * (lo_ + hi_))
            hb.append(np.percentile(ztop[m], 90) - zb)
    rb, hb = np.array(rb), np.array(hb)
    H = hb.max()
    sel = (rb > rb[np.argmax(hb)]) & (hb > 0.25 * H) & (hb < 0.75 * H)
    slope = np.polyfit(rb[sel], hb[sel], 1)[0]
    ang = float(np.degrees(np.arctan(-slope)))
    res = dict(scenario="repose", angle_of_repose_deg=ang, heap_height_mm=float(H / MM),
               heap_height_d=float(H / D_MEAN), n_glued=int(len(base)), n_mobile=int(len(pts)),
               n_on_heap=int(mob.sum()), cylinder_r_mm=rc / MM, column_h_mm=hcol / MM,
               lift_speed_m_s=v_lift, profile_r_mm=(rb / MM).tolist(), profile_h_mm=(hb / MM).tolist(),
               fit_bins=int(sel.sum()), t_end_s=sim.t, ke_final_uJ=sim.kinetic_energy() * 1e6,
               **common_meta(sim, time.time() - w0))
    dump(f"repose_mur{MUR_PP:g}_mu{MU_PP:g}{SUFFIX}", res)
    print(f"mu_r={MUR_PP} mu={MU_PP} Bo={BOND}: angle of repose {ang:.1f} deg, H={H/MM:.1f} mm "
          f"({H/D_MEAN:.1f} d), fit bins {sel.sum()}, mobile {len(pts)}, glued {len(base)}, "
          f"wall {time.time()-w0:.0f}s", flush=True)


def sc_settle():
    sim = make_auger()
    print("N =", sim.N, "t_c =", contact_time(), "dt ratio =", contact_time() / DT, flush=True)
    w0 = time.time()
    log, _ = run(sim, 0.30, [(0, 0.0), (1, 0.0)], [(0, 0.0), (1, 0.0)])
    sim.save(os.path.join(FRAMES, f"settled{SUFFIX}.npz"))
    res = dict(scenario="settle", m_total_mg=float(sim.mass.sum() * 1e6),
               m_disp_during_settle_mg=sim.m_disp * 1e6, log=log,
               **common_meta(sim, time.time() - w0))
    dump("settle" + SUFFIX, res)
    print(f"settled N={sim.N} in {time.time()-w0:.0f}s wall; KE={sim.kinetic_energy()*1e6:.4f} uJ")


def load_settled():
    sim = make_auger()
    sim.load(os.path.join(FRAMES, f"settled{SUFFIX}.npz"))
    sim.m_disp = 0.0
    sim.t = 0.0
    return sim


def sc_dose(tilt_deg, revs=1.5):
    sim = load_settled()
    w = RPM_TUBE * 2 * math.pi / 60
    t_tilt, t_hold, ramp = 0.25, 0.10, 0.05
    t_rot0 = t_tilt + t_hold
    t_rot1 = t_rot0 + ramp + revs * 2 * math.pi / w
    t_end = t_rot1 + ramp + 0.15
    tilt_kf = [(0, 0.0), (t_tilt, tilt_deg), (t_end + 1, tilt_deg)]
    om_kf = [(0, 0.0), (t_rot0, 0.0), (t_rot0 + ramp, w), (t_rot1, w), (t_rot1 + ramp, 0.0),
             (t_end + 1, 0.0)]
    w0 = time.time()
    log, frames = run(sim, t_end, tilt_kf, om_kf, frame_dt=0.025)
    t = np.array(log["t"])
    m = np.array(log["m_disp_mg"])
    th = np.array(log["theta_deg"])
    m_at = lambda deg: float(np.interp(deg, th, m))  # noqa: E731 (theta is monotone here)
    m_pre = float(np.interp(t_rot0, t, m))
    per_rev = []
    for k in range(int(revs * 4)):                 # dose in each quarter turn
        per_rev.append(m_at(90 * (k + 1)) - m_at(90 * k))
    last_rev = m_at(360 * revs) - m_at(360 * (revs - 1))
    m_cap = sim.mass[sim.captured]
    res = dict(scenario="dose", tilt_deg=tilt_deg, revs=revs, m_before_rotation_mg=m_pre,
               dose_quarter_turns_mg=per_rev, dose_last_rev_mg=last_rev,
               dose_first_rev_mg=m_at(360) - m_at(0), m_total_disp_mg=float(m[-1]),
               n_disp=int(sim.captured.sum()),
               bulk_vol_last_rev_mm3=last_rev * 1e-6 / (RHO * 0.6) * 1e9,
               m_total_mg=float(sim.mass.sum() * 1e6), log=log,
               **common_meta(sim, time.time() - w0))
    name = f"dose_tilt{tilt_deg:g}{SUFFIX}"
    dump(name, res)
    save_frames(name, frames, sim)


def sc_leaktap():
    sim = load_settled()
    t_tilt, t_hold = 0.25, 0.45
    taps = [t_tilt + t_hold + 0.15 * k for k in range(4)]
    t_end = taps[-1] + 0.20
    w0 = time.time()
    log, frames = run(sim, t_end, [(0, 0.0), (t_tilt, 45.0), (t_end + 1, 45.0)],
                      [(0, 0.0), (t_end + 1, 0.0)], taps=taps, frame_dt=0.02)
    t = np.array(log["t"])
    m = np.array(log["m_disp_mg"])
    leak_tilt = float(np.interp(t_tilt, t, m))
    leak_hold = float(np.interp(taps[0], t, m) - np.interp(t_tilt + 0.05, t, m))
    edges = taps + [t_end]
    per_tap = [float(np.interp(b - 1e-4, t, m) - np.interp(a - 1e-4, t, m)) for a, b in zip(edges[:-1], edges[1:])]
    res = dict(scenario="leaktap", tilt_deg=45.0, m_during_tilt_mg=leak_tilt,
               leak_during_hold_mg=leak_hold, hold_s=t_hold - 0.05, tap_times_s=taps,
               mass_per_tap_mg=per_tap, log=log, **common_meta(sim, time.time() - w0))
    dump("leaktap" + SUFFIX, res)
    save_frames("leaktap" + SUFFIX, frames, sim)


def sc_sequence(tilt=35.0):
    sim = load_settled()
    w = RPM_TUBE * 2 * math.pi / 60
    T = dict(tilt0=0.05, tilt1=0.40, rot0=0.45, ramp=0.05)
    T["rot1"] = T["rot0"] + T["ramp"] + 2 * math.pi / w
    T["rot2"] = T["rot1"] + T["ramp"]
    taps = [T["rot2"] + 0.10 + 0.15 * k for k in range(4)]
    T["back0"] = taps[-1] + 0.15
    T["back1"] = T["back0"] + 0.35
    t_end = T["back1"] + 0.10
    tilt_kf = [(0, 0.0), (T["tilt0"], 0.0), (T["tilt1"], tilt), (T["back0"], tilt),
               (T["back1"], 0.0), (t_end + 1, 0.0)]
    om_kf = [(0, 0.0), (T["rot0"], 0.0), (T["rot0"] + T["ramp"], w), (T["rot1"], w),
             (T["rot2"], 0.0), (t_end + 1, 0.0)]

    def phase(t):
        if t < T["tilt0"]:
            return "horizontal"
        if t < T["tilt1"]:
            return "tilting down"
        if t < T["rot0"]:
            return "hold"
        if t < T["rot2"]:
            return "rotating (1 rev)"
        if t < taps[0]:
            return "hold"
        for k, tk in enumerate(taps):
            if tk <= t < tk + 0.15:
                return f"tap {k + 1}/{len(taps)}"
        if t < T["back1"]:
            return "tilting back"
        return "horizontal"

    w0 = time.time()
    log, frames = run(sim, t_end, tilt_kf, om_kf, taps=taps, frame_dt=1 / 30, phase=phase)
    t = np.array(log["t"])
    m = np.array(log["m_disp_mg"])
    mi = lambda x: float(np.interp(x, t, m))  # noqa: E731
    res = dict(scenario="sequence", tilt_deg=tilt, times=T, tap_times_s=taps,
               m_after_tilt_mg=mi(T["rot0"]), m_rotation_mg=mi(T["rot2"] + 0.1) - mi(T["rot0"]),
               m_per_tap_mg=[mi(tk + 0.15) - mi(tk) for tk in taps],
               m_tilt_back_mg=mi(t_end) - mi(T["back0"]), m_total_mg=mi(t_end), log=log,
               **common_meta(sim, time.time() - w0))
    dump("sequence" + SUFFIX, res)
    pos0 = np.load(os.path.join(FRAMES, f"settled{SUFFIX}.npz"))["pos"]
    save_frames("sequence" + SUFFIX, frames, sim, extra=dict(chamber0=dem.flight_chamber(pos0, 0.0)))


if __name__ == "__main__":
    what = sys.argv[1]
    if what == "repose":
        sc_repose()
    elif what == "settle":
        sc_settle()
    elif what == "dose":
        sc_dose(float(sys.argv[2]), float(sys.argv[3]) if len(sys.argv) > 3 else 1.5)
    elif what == "leaktap":
        sc_leaktap()
    elif what == "sequence":
        sc_sequence(float(sys.argv[2]) if len(sys.argv) > 2 else 35.0)
    else:
        raise SystemExit(__doc__)
