"""Paternoster carousel dynamics in MuJoCo: indexing, full laps, a fast lap, and the
station dock/tilt/tap/auger sequence. Writes plots + results.json to sim/out/.

    python carousel_sim.py            # everything (about 3-4 min)
    python carousel_sim.py --quick    # fewer runs

Pivots are driven by the exact chain kinematics (kinematics.pivots via model.pivot_table)
through stiff servos on two slide joints per gondola (the chain); each gondola swings
freely about the pivot axis (hinge on x) under gravity, contacts on.
"""
from __future__ import annotations

import json
import math
import os
import sys
import time

import mujoco
import numpy as np

import model as M
from model import DT, G, MM, NK, PR, KN, OUT

KP, KV = M.KP_PIV, M.KV_PIV
RAD = 180 / math.pi


# ------------------------------------------------------------------ helpers
def ids(model, prefix, n=NK, kind="joint"):
    obj = getattr(model, kind)
    return np.array([obj(f"{prefix}{k}").id for k in range(n)])


def pendulum(aug_mass=M.M_AUG_NOM):
    """Small-angle compound-pendulum frequency of one loaded gondola about its pivot axis."""
    xml, _ = M.build_xml(M.KN.HOME_SHIFT, aug_mass=aug_mass)
    m = mujoco.MjModel.from_xml_string(xml)
    d = mujoco.MjData(m)
    mujoco.mj_forward(m, d)
    g = m.body("g0").id
    full = np.zeros((m.nv, m.nv))
    mujoco.mj_fullM(m, d, full)
    j = m.joint("gs0").dofadr[0]
    I = full[j, j]
    mass = m.body_subtreemass[g]
    com = d.subtree_com[g] - d.xpos[g]
    dist = -com[2]
    f = math.sqrt(mass * G * dist / I) / (2 * math.pi)
    return dict(mass_kg=float(mass), com_below_pivot_mm=float(dist / MM), com_x_mm=float(com[0] / MM),
                I_pivot_kgmm2=float(I * 1e6), f_Hz=f, period_s=1 / f)


# ------------------------------------------------------------------ rectangle clearance (2D, vectorised)
_RECT = np.array([[-PR.GON_W / 2, PR.GON_Z0], [PR.GON_W / 2, PR.GON_Z0],
                  [PR.GON_W / 2, PR.GON_Z1], [-PR.GON_W / 2, PR.GON_Z1]])   # mm, gondola frame (y, z)


def rect_corners(c, th):
    """c (N,2) pivot mm, th (N,) swing rad -> (N,4,2) corners of the swung envelope."""
    ct, st = np.cos(th)[:, None], np.sin(th)[:, None]
    y = _RECT[None, :, 0] * ct - _RECT[None, :, 1] * st
    z = _RECT[None, :, 0] * st + _RECT[None, :, 1] * ct
    return np.stack([y + c[:, None, 0], z + c[:, None, 1]], axis=-1)


def _pt_seg(p, a, b):
    ab = b - a
    t = np.clip(np.sum((p - a) * ab, -1) / np.maximum(np.sum(ab * ab, -1), 1e-12), 0, 1)
    q = a + t[..., None] * ab
    return np.linalg.norm(p - q, axis=-1)


def poly_dist(A, B):
    """Signed distance between convex quads A, B (N,4,2): >0 gap, <0 penetration depth (SAT)."""
    dmin = np.full(A.shape[0], np.inf)
    for P, Q in ((A, B), (B, A)):
        for i in range(4):
            for j in range(4):
                dmin = np.minimum(dmin, _pt_seg(P[:, i], Q[:, j], Q[:, (j + 1) % 4]))
    pen = np.full(A.shape[0], np.inf)
    sep = np.zeros(A.shape[0], bool)
    for P in (A, B):
        for j in range(2):
            e = P[:, j + 1] - P[:, j]
            n = np.stack([-e[:, 1], e[:, 0]], -1)
            n /= np.linalg.norm(n, axis=-1, keepdims=True)
            pa, pb = np.einsum("nkd,nd->nk", A, n), np.einsum("nkd,nd->nk", B, n)
            ov = np.minimum(pa.max(1), pb.max(1)) - np.maximum(pa.min(1), pb.min(1))
            sep |= ov < 0
            pen = np.minimum(pen, ov)
    return np.where(sep, dmin, -pen)


def shaft_dist(A):
    """Distance from swung envelopes A (N,4,2) to the nearer bottom through-shaft surface (mm)."""
    out = np.full(A.shape[0], np.inf)
    r = PR.SHAFT_D / 2
    for sy in (-PR.CORNER_Y, PR.CORNER_Y):
        p = np.array([sy, PR.Z_BOT])
        d = np.full(A.shape[0], np.inf)
        for j in range(4):
            d = np.minimum(d, _pt_seg(p[None], A[:, j], A[:, (j + 1) % 4]))
        # inside test (centre inside polygon) -> negative
        inside = np.ones(A.shape[0], bool)
        for j in range(4):
            e = A[:, (j + 1) % 4] - A[:, j]
            w = p[None] - A[:, j]
            inside &= (e[:, 0] * w[:, 1] - e[:, 1] * w[:, 0]) > 0
        out = np.minimum(out, np.where(inside, -d, d) - r)
    return out


# ------------------------------------------------------------------ carousel run
def run_carousel(shift, cfg=None, log_every=10, frame_cb=None, fps=30):
    cfg = dict(cfg or {})
    xml, info = M.build_xml(shift[0], damping=cfg.get("damping", 1e-4), fric=cfg.get("fric", 0.0),
                            aug_mass=cfg.get("aug_mass", M.M_AUG_NOM), channel=cfg.get("channel", False))
    m = mujoco.MjModel.from_xml_string(xml)
    d = mujoco.MjData(m)
    y0, z0 = np.array(info["y0"]), np.array(info["z0"])
    P = M.pivots_mm(shift) * MM                        # (n, NK, 2)
    V = np.gradient(P, DT, axis=0)
    iy = ids(m, "ay", kind="actuator")
    iz = ids(m, "az", kind="actuator")
    qs = np.array([m.jnt_qposadr[j] for j in ids(m, "gs")])
    qy = np.array([m.jnt_qposadr[j] for j in ids(m, "gy")])
    qz = np.array([m.jnt_qposadr[j] for j in ids(m, "gz")])
    gbody = ids(m, "g", kind="body")
    gmass = m.body_subtreemass[gbody]
    gid2k = {}
    for k in range(NK):
        for nm in ("gef", "geb", "gfl"):
            gid2k[m.geom(f"{nm}{k}").id] = k
    n = len(shift)
    nl = (n + log_every - 1) // log_every
    L = dict(t=np.zeros(nl), s=np.zeros(nl), th=np.zeros((nl, NK)), py=np.zeros((nl, NK)), pz=np.zeros((nl, NK)),
             fy=np.zeros((nl, NK)), fz=np.zeros((nl, NK)), ncontact=np.zeros(nl, int), pen=np.zeros(nl))
    contacts = []
    next_frame = 0.0
    li = 0
    for i in range(n):
        d.ctrl[iy] = KP * (P[i, :, 0] - y0) + KV * V[i, :, 0]
        d.ctrl[iz] = KP * (P[i, :, 1] - z0) + KV * V[i, :, 1] + gmass * G
        mujoco.mj_step(m, d)
        if i % log_every == 0:
            L["t"][li] = d.time
            L["s"][li] = shift[i]
            L["th"][li] = d.qpos[qs]
            L["py"][li] = (d.qpos[qy] + y0) / MM
            L["pz"][li] = (d.qpos[qz] + z0) / MM
            L["fy"][li] = d.actuator_force[iy]
            L["fz"][li] = d.actuator_force[iz]
            nc, pen = 0, 0.0
            for c in d.contact[:d.ncon]:
                if c.dist < 0 and (c.geom1 in gid2k or c.geom2 in gid2k):
                    nc += 1
                    pen = min(pen, c.dist)
                    if len(contacts) < 50:
                        contacts.append(dict(t=float(d.time), g1=mujoco.mj_id2name(m, mujoco.mjtObj.mjOBJ_GEOM, c.geom1),
                                             g2=mujoco.mj_id2name(m, mujoco.mjtObj.mjOBJ_GEOM, c.geom2), dist_mm=float(c.dist / MM)))
            L["ncontact"][li] = nc
            L["pen"][li] = pen / MM
            li += 1
        if frame_cb is not None and d.time >= next_frame - 1e-9:
            frame_cb(m, d, dict(shift=shift[i], t=d.time, th=d.qpos[qs].copy()))
            next_frame += 1.0 / fps
    L["contacts"] = contacts
    return L


def analyse(L, stops=None, dwell=None):
    t, s, th = L["t"], L["s"], L["th"]
    nl = len(t)
    u = M.module_u(s, np.arange(NK))                   # (nl, NK)
    reg = M.region_of(u)
    absd = np.abs(th) * RAD
    res = {"max_swing_deg": float(absd.max())}
    per = {}
    for i, (nm, _, _) in enumerate(M.REGIONS):
        sel = reg == i
        per[nm] = float(absd[sel].max()) if sel.any() else None
    res["max_swing_by_region_deg"] = per
    # neighbour clearance with the actual swung orientations
    C = np.stack([L["py"], L["pz"]], -1)                # (nl, NK, 2)
    clr = np.zeros((nl, NK))
    shf = np.zeros((nl, NK))
    for k in range(NK):
        A = rect_corners(C[:, k], th[:, k])
        B = rect_corners(C[:, (k + 1) % NK], th[:, (k + 1) % NK])
        clr[:, k] = poly_dist(A, B)
        shf[:, k] = shaft_dist(A)
    # same geometry with every gondola upright (kinematic reference)
    clr0 = np.zeros((nl, NK))
    z = np.zeros(nl)
    for k in range(NK):
        clr0[:, k] = poly_dist(rect_corners(C[:, k], z), rect_corners(C[:, (k + 1) % NK], z))
    i, k = np.unravel_index(np.argmin(clr), clr.shape)
    res["min_neighbour_clearance_mm"] = float(clr.min())
    res["min_neighbour_clearance_upright_mm"] = float(clr0.min())
    res["min_clearance_where"] = dict(t=float(t[i]), pair=[int(k), int((k + 1) % NK)],
                                      region_k=M.REGIONS[reg[i, k]][0], u_k=float(u[i, k]),
                                      swing_deg=[float(th[i, k] * RAD), float(th[i, (k + 1) % NK] * RAD)])
    res["min_shaft_clearance_mm"] = float(shf.min())
    res["gondola_contacts"] = int((L["ncontact"] > 0).sum())
    res["max_penetration_mm"] = float(-L["pen"].min())
    # drive torque: virtual work of the pivot forces + chain/sprocket/rotor inertia
    dP = M.dpivot_ds_mm(s) * MM                         # (nl, NK, 2) m per link
    F = np.stack([L["fy"], L["fz"]], -1)
    tq_load = np.einsum("nkd,nkd->n", F, dP) / M.DELTA
    sd = np.gradient(s, t)
    sdd = np.gradient(sd, t)
    tq = tq_load + M.J_DRIVE * sdd * M.DELTA
    res["motor_torque_peak_Nm"] = float(np.abs(tq).max())
    # the rigid-chain servo turns each chordal (polygonal) kink into a short force spike; a 25 ms
    # moving average gives the torque a real, slightly compliant chain would pass to the motor
    from scipy.ndimage import uniform_filter1d
    res["motor_torque_peak_filtered_Nm"] = float(np.abs(uniform_filter1d(tq, size=5)).max())
    res["motor_torque_rms_Nm"] = float(np.sqrt(np.mean(tq ** 2)))
    res["motor_speed_peak_rpm"] = float(np.abs(sd).max() * M.DELTA * 60 / (2 * math.pi))
    res["chain_speed_peak_mm_s"] = float(np.abs(sd).max() * PR.P)
    res["drive_tension_step_per_chain_N_peak"] = float(np.abs(tq).max() / (2 * PR.R * MM))
    # strand tension above the slack (bottom-run, leaving the driver) per chain, front share
    tang = dP / np.maximum(np.linalg.norm(dP, axis=-1, keepdims=True), 1e-12)
    Ft = np.einsum("nkd,nkd->nk", F, tang) * (dP.__abs__().sum(-1) > 0)
    front = 1 - 143.5 / PR.CHAIN_L
    order = np.argsort(u, axis=1)
    Ft_sorted = np.take_along_axis(Ft, order, 1) * front
    cum = np.cumsum(Ft_sorted, axis=1)
    res["strand_tension_rise_front_chain_N_max"] = float(cum.max())
    L["torque"] = tq
    L["clr"] = clr
    L["shf"] = shf
    L["u"] = u
    if stops:
        st = []
        for ts in stops:
            w = (t >= ts) & (t < ts + (dwell or 2.0) - 1e-6)
            # module at the station after this stop: the one whose u is nearest 10
            kst = int(np.argmin(np.abs(((u[np.argmax(w)] - 10.0 + 60) % 120) - 60)))
            a = absd[w, kst]
            tw = t[w] - ts
            above = np.where(a > 0.5)[0]
            settle = float(tw[above[-1]] + (tw[1] - tw[0])) if len(above) else 0.0
            if len(above) and above[-1] == len(a) - 1:
                settle = float("nan")          # not settled within the dwell
            st.append(dict(stop_t=float(ts), module=kst, residual_deg=float(a.max()),
                           residual_after_0p5s_deg=float(a[tw >= 0.5].max()) if (tw >= 0.5).any() else None,
                           settle_to_0p5deg_s=settle))
        res["stops"] = st
        res["station_residual_deg_max"] = max(x["residual_deg"] for x in st)
        sts = [x["settle_to_0p5deg_s"] for x in st]
        res["station_settle_s_max"] = float("nan") if any(math.isnan(x) for x in sts) else max(sts)
    return res


def free_decay(cfg, theta0_deg=3.0, T=6.0):
    """Release the station gondola from theta0 with the chain stopped; measure period and decay."""
    shift = np.full(int(T / DT), KN.HOME_SHIFT)
    xml, info = M.build_xml(shift[0], damping=cfg.get("damping", 1e-4), fric=cfg.get("fric", 0.0),
                            aug_mass=cfg.get("aug_mass", M.M_AUG_NOM))
    m = mujoco.MjModel.from_xml_string(xml)
    d = mujoco.MjData(m)
    j = m.joint("gs0").qposadr[0]
    d.qpos[j] = math.radians(theta0_deg)
    y0, z0 = np.array(info["y0"]), np.array(info["z0"])
    iy, iz = ids(m, "ay", kind="actuator"), ids(m, "az", kind="actuator")
    gm = m.body_subtreemass[ids(m, "g", kind="body")]
    th = []
    for i in range(len(shift)):
        d.ctrl[iy] = 0.0
        d.ctrl[iz] = gm * G
        mujoco.mj_step(m, d)
        th.append(d.qpos[j])
    th = np.array(th) * RAD
    t = (np.arange(len(th)) + 1) * DT
    zc = np.where((th[:-1] > 0) & (th[1:] <= 0))[0]
    period = float(np.mean(np.diff(t[zc]))) if len(zc) > 2 else float("nan")
    above = np.where(np.abs(th) > 0.5)[0]
    return dict(period_s=period, f_Hz=1 / period if period == period else None,
                settle_to_0p5deg_s=float(t[above[-1]]) if len(above) else 0.0, t=t, th=th)


# ------------------------------------------------------------------ station run
# current CAD (params.py): rod-end pin at Sam's (YOKE_X, YOKE_Z) = (40, -72) mm from the hinge, base clevis
# at hinge + (40, -289.4) mm (DOCK_EXT = 20 mm above the 197.4 mm retracted length), P16-150-22-12-P
STATION_BASE = dict(a=PR.YOKE_X * MM, b=PR.YOKE_Z * MM, base_rel=(PR.YOKE_X * MM, (PR.YOKE_Z - PR.ACT_RETRACTED - PR.DOCK_EXT) * MM),
                    v_act=0.040, fmax=50.0)
K_TAB = 2000.0            # SA-1 tab + pivot compliance per pivot, N/m (coordinator's 2 N/mm)
T_CHAIN = 40.0                                  # assumed static tension per chain on the bottom run, N
KZ_CHAIN = 2 * 4 * T_CHAIN / (PR.LOOP_B * MM)   # two chains, point load mid-span: k = 4T/L each -> 1680 N/m


def station_geometry(st, z_piv):
    """Stroke and static actuator force vs tilt for rod-pin (a, b) in the hinge frame and base (xb, zb)."""
    hx, hz = PR.HINGE_X * MM, z_piv + PR.HINGE_Z * MM
    base = np.array([hx + st["base_rel"][0], hz + st["base_rel"][1]]) if "base_rel" in st else np.array([st["xb"], st["zb"]])
    out = []
    for deg in range(0, 91, 5):
        q = math.radians(deg)
        rot = lambda a, b: np.array([a * math.cos(q) - b * math.sin(q), a * math.sin(q) + b * math.cos(q)])
        pin = np.array([hx, hz]) + rot(st["a"], st["b"])
        dvec = pin - base
        Lact = np.linalg.norm(dvec)
        dvec /= Lact
        r = pin - np.array([hx, hz])
        arm = abs(r[0] * dvec[1] - r[1] * dvec[0])
        mod_x = 0.0897 * math.cos(q) - (-0.0051) * math.sin(q)
        car_x = rot(0.0378, -0.0355)[0]
        tq = (M.M_PLATE + M.M_BRKT + M.M_AUG_NOM) * G * mod_x + M.M_CARR * G * car_x
        out.append(dict(tilt_deg=deg, length_mm=Lact / MM, stroke_mm=(Lact - PR.ACT_RETRACTED * MM) / MM,
                        arm_mm=arm / MM, force_N=tq / arm, line_angle_deg=math.degrees(math.atan2(dvec[0], dvec[1]))))
    return out


def run_station(st=None, cfg=None, log_every=10, frame_cb=None, fps=30, tap_N=3.0):
    st = dict(STATION_BASE, **(st or {}))
    cfg = dict(cfg or {})
    s0 = KN.HOME_SHIFT
    hold = cfg.get("chain")            # dict(k_tab, k_span, gap) -> compliant chain (+ hold-down strip) at the station
    xml, info = M.build_xml(s0, damping=cfg.get("damping", 1e-4), fric=cfg.get("fric", 0.0),
                            station=st, channel=cfg.get("channel", False), kz0=0.0 if hold else cfg.get("kz0"),
                            pitch0=bool(hold))
    m = mujoco.MjModel.from_xml_string(xml)
    d = mujoco.MjData(m)
    sinfo = info["station"]
    y0, z0 = np.array(info["y0"]), np.array(info["z0"])
    iy, iz = ids(m, "ay", kind="actuator"), ids(m, "az", kind="actuator")
    gb = ids(m, "g", kind="body")
    gm = m.body_subtreemass[gb]
    ia, iaug = m.actuator("act_drive").id, m.actuator("aug_drive").id
    kpa, kva = st.get("kp_act", 3e4), st.get("kv_act", 250)
    jslide = m.joint("act_slide").qposadr[0]
    jtilt = m.joint("mt0").qposadr[0]
    jsw = m.joint("gs0").qposadr[0]
    jz0 = m.joint("gz0").qposadr[0]
    jaug = m.joint("ar0").dofadr[0]
    jhold = [m.joint("act_pitch").id, m.joint("car_pitch").id]
    kh = m.jnt_stiffness[jhold].copy()
    eq = m.equality("dock").id
    bm0, bcar, bg0 = m.body("m0").id, m.body("car").id, m.body("g0").id
    L0 = sinfo["L0"] - sinfo["ret"]
    geo = station_geometry(st, z0[0])
    L90 = geo[-1]["stroke_mm"] * MM
    v_act = st.get("v_act", 0.018)
    if hold:
        mujoco.mj_forward(m, d)
        Wg = m.body_subtreemass[bg0] * G
        xc = d.subtree_com[bg0][0]
        Fnom = np.array([Wg * (1 - xc / M.L_X), Wg * xc / M.L_X])          # static front/back pivot loads
        zn = np.array([d.xpos[bg0][2], d.xpos[bg0][2]])
        kt, ks, gap = hold["k_tab"], hold["k_span"], hold.get("gap")
        c_t = 2 * 0.3 * math.sqrt(kt * m.body_subtreemass[bg0] / 2)
        jacp = np.zeros((3, m.nv))
        hz_state = np.zeros(8)
    # timeline
    T = dict(dock0=0.3)
    T["dock1"] = T["dock0"] + L0 / v_act
    T["tilt0"] = T["dock1"] + 0.3
    T["tilt1"] = T["tilt0"] + (L90 - L0) / v_act
    T["work0"] = T["tilt1"] + 0.5
    T["work1"] = T["work0"] + 2.4
    T["back0"] = T["work1"] + 0.3
    T["back1"] = T["back0"] + (L90 - L0) / v_act
    T["undock"] = T["back1"] + 0.3
    T["ret1"] = T["undock"] + L0 / v_act
    T["end"] = T["ret1"] + 0.5
    taps = [T["work0"] + 0.3 + 0.25 * i for i in range(8)]

    def ref(t):
        if t < T["dock0"]:
            return 0.0, 0.0
        if t < T["dock1"]:
            return (t - T["dock0"]) * v_act, v_act
        if t < T["tilt0"]:
            return L0, 0.0
        if t < T["tilt1"]:
            return L0 + (t - T["tilt0"]) * v_act, v_act
        if t < T["back0"]:
            return L90, 0.0
        if t < T["back1"]:
            return L90 - (t - T["back0"]) * v_act, -v_act
        if t < T["undock"]:
            return L0, 0.0
        if t < T["ret1"]:
            return L0 - (t - T["undock"]) * v_act, -v_act
        return 0.0, 0.0

    n = int(T["end"] / DT)
    nl = n // log_every + 1
    keys = ["t", "tilt", "slide", "Fact", "swing", "Ffz", "Fbz", "Ffy", "Fby", "dz0", "aug_w", "tap", "docked", "Frail",
            "rise_f", "rise_b", "chain_f", "chain_b", "strip_f", "strip_b"]
    Lg = {k_: np.zeros(nl) for k_ in keys}
    docked = False
    next_frame = 0.0
    li = 0
    tap_pt = np.zeros(3)
    rail_ids = [i for i in range(m.ngeom) if (mujoco.mj_id2name(m, mujoco.mjtObj.mjOBJ_GEOM, i) or "").startswith("rail")]
    for i in range(n):
        t = d.time
        q_ref, v_ref = ref(t)
        d.ctrl[ia] = kpa * q_ref + kva * v_ref
        d.ctrl[iy] = KP * 0.0
        kz = cfg.get("kz0")
        d.ctrl[iz] = KP * 0.0 + gm * G
        if kz is not None or hold:
            d.ctrl[iz[0]] = 0.0 if hold else gm[0] * G
        d.ctrl[iaug] = 5.7 if T["work0"] <= t < T["work1"] else 0.0       # auger 54 rpm (NEMA 11 at 2 rev/s, 20:44)
        # dock: carriage frame reaches the hinge frame
        if not docked and T["dock0"] < t < T["tilt0"]:
            if np.linalg.norm(d.xpos[bcar] - d.xpos[bm0]) < 0.0005:         # cones seated
                d.eq_active[eq] = 1
                m.eq_solref[eq] = [0.05, 1.0]                                # cones pull in gently ...
                T["stiffen"] = t + 0.25
                m.jnt_stiffness[jhold] = 0.0
                docked = True
                T["docked_at"] = t
                T["dock_offset_mm"] = float(np.linalg.norm(d.xpos[bcar] - d.xpos[bm0]) / MM)
        if docked and t >= T.get("stiffen", 1e9):
            m.eq_solref[eq] = [0.003, 1.0]                                   # ... then the dock is rigid
            T["stiffen"] = 1e9
        if docked and t >= T["undock"]:
            d.eq_active[eq] = 0
            m.jnt_stiffness[jhold] = kh
            docked = False
        d.qfrc_applied[:] = 0.0
        tap = 0.0
        for k_, tt in enumerate(taps):
            if tt <= t < tt + 0.010:
                R = d.xmat[bm0].reshape(3, 3)
                dirl = np.array([0, 1.0, 0]) if k_ < 4 else np.array([0, 0, 1.0])
                Fw = R @ (tap_N * dirl)
                pt = d.xpos[bm0] + R @ np.array([0.020, 0.0, 0.0])
                mujoco.mj_applyFT(m, d, Fw, np.zeros(3), pt, bm0, d.qfrc_applied)
                tap = tap_N if k_ < 4 else -tap_N
        if hold:
            R0 = d.xmat[bg0].reshape(3, 3)
            for ip, px in enumerate((0.0, M.L_X)):
                pw = d.xpos[bg0] + R0 @ np.array([px, 0.0, 0.0])
                rise = pw[2] - zn[ip]
                mujoco.mj_jac(m, d, jacp, None, pw, bg0)
                vz = jacp[2] @ d.qvel
                dc = kt * rise / (kt + ks)                 # massless chain span in series with the tab
                N = 0.0
                if gap is not None and dc > gap:           # chain meets the hold-down strip (rigid one-sided stop)
                    dc = gap
                    N = kt * (rise - gap) - ks * gap
                Fup = Fnom[ip] - kt * (rise - dc) - c_t * vz
                mujoco.mj_applyFT(m, d, np.array([0.0, 0.0, Fup]), np.zeros(3), pw, bg0, d.qfrc_applied)
                hz_state[ip * 4:(ip + 1) * 4] = (rise, dc, N, Fup)
        mujoco.mj_step(m, d)
        if i % log_every == 0:
            mujoco.mj_rnePostConstraint(m, d)
            if hold:
                Lg["rise_f"][li], Lg["chain_f"][li], Lg["strip_f"][li] = hz_state[0] / MM, hz_state[1] / MM, hz_state[2]
                Lg["rise_b"][li], Lg["chain_b"][li], Lg["strip_b"][li] = hz_state[4] / MM, hz_state[5] / MM, hz_state[6]
            c = d.subtree_com[bg0]
            tq_c, f = d.cfrc_int[bg0, :3], d.cfrc_int[bg0, 3:]
            pf = np.array([0.0, d.xpos[bg0][1], d.xpos[bg0][2]])
            tq_f = tq_c + np.cross(c - pf, f)
            Lx = M.L_X
            Fbz, Fby = -tq_f[1] / Lx, tq_f[2] / Lx
            Lg["t"][li] = t
            Lg["tilt"][li] = d.qpos[jtilt] * RAD
            Lg["slide"][li] = d.qpos[jslide] / MM
            Lg["Fact"][li] = d.actuator_force[ia]
            Lg["swing"][li] = d.qpos[jsw] * RAD
            Lg["Ffz"][li], Lg["Fbz"][li] = (hz_state[3], hz_state[7]) if hold else (f[2] - Fbz, Fbz)
            Lg["Ffy"][li], Lg["Fby"][li] = f[1] - Fby, Fby
            Lg["dz0"][li] = d.qpos[jz0] / MM
            Lg["aug_w"][li] = d.qvel[jaug]
            Lg["tap"][li] = tap
            Lg["docked"][li] = float(docked)
            fr = 0.0
            for ci in range(d.ncon):
                cc = d.contact[ci]
                if cc.geom1 in rail_ids or cc.geom2 in rail_ids:
                    f6 = np.zeros(6)
                    mujoco.mj_contactForce(m, d, ci, f6)
                    fr += f6[0]
            Lg["Frail"][li] = fr
            li += 1
        if frame_cb is not None and d.time >= next_frame - 1e-9:
            frame_cb(m, d, dict(t=d.time, shift=s0, tilt=d.qpos[jtilt] * RAD, Fact=d.actuator_force[ia],
                                swing=d.qpos[jsw] * RAD, docked=docked, tap=tap, phase=phase_name(T, d.time),
                                rise_f=(hz_state[0] / MM) if hold else 0.0, strip_f=hz_state[2] if hold else 0.0))
            next_frame += 1.0 / fps
    for k_ in keys:
        Lg[k_] = Lg[k_][:li]
    return Lg, T, geo, sinfo


def phase_name(T, t):
    if t < T["dock0"]:
        return "at station"
    if t < T.get("docked_at", T["dock1"]) + 0.05:
        return "carriage rising to dock"
    if t < T["tilt0"]:
        return "docked"
    if t < T["tilt1"]:
        return "tilting up"
    if t < T["work0"]:
        return "tilted, hold"
    if t < T["work1"]:
        return "auger turning + solenoid taps"
    if t < T["back0"]:
        return "hold"
    if t < T["back1"]:
        return "tilting back"
    if t < T["ret1"]:
        return "undocked, retracting"
    return "retracted"


def station_summary(Lg, T, geo):
    t = Lg["t"]
    up = (t >= T["tilt0"]) & (t < T["tilt1"])
    work = (t >= T["work0"]) & (t < T["work1"] + 0.2)
    dock = (t >= T["dock0"]) & (t < T["undock"])
    static = (t < T["dock0"])
    # actuator force vs tilt (binned)
    bins = []
    for deg in range(0, 91, 10):
        w = up & (np.abs(Lg["tilt"] - deg) < 2.5)
        if w.any():
            bins.append(dict(tilt_deg=deg, force_sim_N=float(np.median(Lg["Fact"][w]))))
    lift = Lg["Ffz"][dock].min(), Lg["Fbz"][dock].min()
    tilt_ph = (t >= T["tilt0"]) & (t < T["back1"])
    return dict(
        static_pivot_Fz_N=dict(front=float(Lg["Ffz"][static].mean()), back=float(Lg["Fbz"][static].mean())),
        min_pivot_Fz_N=dict(front=float(lift[0]), back=float(lift[1])),
        chain_lifted=bool(min(lift) < 0),
        min_pivot_Fz_tilting_N=dict(front=float(Lg["Ffz"][tilt_ph].min()), back=float(Lg["Fbz"][tilt_ph].min())),
        actuator_force_peak_tilting_N=float(np.abs(Lg["Fact"][up]).max()),
        max_pivot_uplift_disp_mm=float(Lg["dz0"][dock].max() - Lg["dz0"][static].mean()),
        max_swing_docked_deg=float(np.abs(Lg["swing"][dock]).max()),
        max_swing_during_taps_auger_deg=float(np.abs(Lg["swing"][work] - Lg["swing"][work][0]).max() + abs(Lg["swing"][work][0])),
        tilt_reached_deg=float(Lg["tilt"].max()),
        actuator_force_peak_N=float(np.abs(Lg["Fact"][dock]).max()),
        actuator_force_vs_tilt_sim=bins,
        actuator_force_vs_tilt_static=[dict(tilt_deg=g["tilt_deg"], force_N=round(g["force_N"], 2), stroke_mm=round(g["stroke_mm"], 1),
                                            arm_mm=round(g["arm_mm"], 1)) for g in geo if g["tilt_deg"] % 10 == 0],
        stroke_used_mm=dict(dock=float(geo[0]["stroke_mm"]), tilt90=float(geo[-1]["stroke_mm"])),
        rail_force_max_N=float(Lg["Frail"].max()),
        pivot_rise_max_mm=dict(front=float(Lg["rise_f"][dock].max()), back=float(Lg["rise_b"][dock].max())),
        chain_rise_max_mm=dict(front=float(Lg["chain_f"][dock].max()), back=float(Lg["chain_b"][dock].max())),
        strip_force_max_N=dict(front=float(Lg["strip_f"].max()), back=float(Lg["strip_b"].max())),
        pivot_Fz_at_tilt=[dict(tilt_deg=dg, front=float(np.median(Lg["Ffz"][up & (np.abs(Lg["tilt"] - dg) < 2.5)])),
                               back=float(np.median(Lg["Fbz"][up & (np.abs(Lg["tilt"] - dg) < 2.5)])),
                               rise_front_mm=float(np.median(Lg["rise_f"][up & (np.abs(Lg["tilt"] - dg) < 2.5)])),
                               strip_front_N=float(np.median(Lg["strip_f"][up & (np.abs(Lg["tilt"] - dg) < 2.5)])))
                          for dg in (0, 15, 30, 45, 60, 75, 90) if (up & (np.abs(Lg["tilt"] - dg) < 2.5)).any()],
        pivot_Fz_range_during_taps_N=dict(front=[float(Lg["Ffz"][work].min()), float(Lg["Ffz"][work].max())],
                                         back=[float(Lg["Fbz"][work].min()), float(Lg["Fbz"][work].max())]),
        timeline_s={k: round(v, 3) for k, v in T.items()})


# ------------------------------------------------------------------ main
def main(quick=False):
    t_start = time.time()
    R = {"model": {}, "runs": {}, "iterations": []}
    pend = pendulum()
    R["model"]["pendulum_nominal"] = pend
    R["model"]["pendulum_light_aug0.12"] = pendulum(0.12)
    R["model"]["pendulum_heavy_aug0.20"] = pendulum(0.20)
    fz = pend["f_Hz"]
    print("pendulum", pend)
    # free decay with damping / friction sensitivity
    fric_nom = 0.1 * pend["mass_kg"] * G * 0.002             # mu N r, both pivots together
    dec = {}
    DEC = {}
    for c in (0.0, 1e-4, 1e-3):
        for mu in (0.0, 0.1):
            fd = free_decay(dict(damping=c, fric=mu / 0.1 * fric_nom), 5.0, 8.0)
            key = f"c={c:g}, mu={mu:g}"
            dec[key] = dict(period_s=fd["period_s"], settle_from_5deg_s=fd["settle_to_0p5deg_s"])
            DEC[key] = fd
    R["model"]["free_decay_from_5deg"] = dec
    R["model"]["pivot_friction_torque_Nm_mu0.1"] = fric_nom
    print("decay", dec)
    base_cfg = dict(damping=1e-4, fric=0.0)
    LOGS = {}

    def index_run(name, kind, T, cfg=base_cfg, n_idx=3, dwell=2.0, kw=None):
        kw = dict(kw or {})
        if kind == "zv":
            kw.setdefault("f_shaper", fz)
        sh, stops = M.sequence(KN.HOME_SHIFT, [(-0.0 + PR.MODULE_LINKS, T, kind, dwell, kw)] * n_idx)
        L = run_carousel(sh, cfg)
        res = analyse(L, stops, dwell)
        res.update(profile=kind, move_time_s=T, cfg={k: v for k, v in cfg.items()})
        R["runs"][name] = res
        LOGS[name] = (L, stops)
        print(f"{name:28s} swing max {res['max_swing_deg']:.2f} resid {res['station_residual_deg_max']:.2f} settle {res['station_settle_s_max']:.2f} "
              f"clr {res['min_neighbour_clearance_mm']:.1f} tq {res['motor_torque_peak_Nm']:.3f}  ({time.time() - t_start:.0f}s)")
        return res

    for T in (1.0, 1.5):
        for kind in ("trap", "scurve", "zv"):
            index_run(f"index_{kind}_{T:.1f}s", kind, T)
    # the four profiles again with the bronze pivot friction (mu = 0.1)
    for T in (1.0, 1.5):
        for kind, kw in (("trap", {}), ("scurve", {}), ("zv", {}), ("trapTn", dict(fa=1 / fz / T))):
            index_run(f"index_{kind}_{T:.1f}s_mu0.1", "trap" if kind == "trapTn" else kind, T,
                      dict(damping=1e-4, fric=fric_nom), kw=kw)
    index_run("index_trap_1.0s_c1e-3", "trap", 1.0, dict(damping=1e-3, fric=0.0))
    index_run("index_trap_1.0s_c0", "trap", 1.0, dict(damping=0.0, fric=0.0))
    # ZV robustness to auger/powder mass (shaper tuned for the nominal module)
    index_run("index_zv_1.0s_aug0.12", "zv", 1.0, dict(base_cfg, aug_mass=0.12))
    index_run("index_zv_1.0s_aug0.20", "zv", 1.0, dict(base_cfg, aug_mass=0.20))
    index_run("index_zv_0.8s", "zv", 0.8)
    index_run("index_trap_1.0s_channel", "trap", 1.0, dict(base_cfg, channel=True), n_idx=1)
    # iteration 3: trapezoid whose acceleration time equals the pendulum period (its accel pulse has a
    # spectral zero at f_n), with and without the bronze pivot friction
    for T in (1.0, 1.2, 1.5):
        index_run(f"index_trapTn_{T:.1f}s", "trap", T, kw=dict(fa=1 / fz / T))
    index_run("index_trapTn_1.2s_mu0.1", "trap", 1.2, dict(damping=1e-4, fric=fric_nom), kw=dict(fa=1 / fz / 1.2))
    index_run("index_zv_trapbase_1.5s", "zv", 1.5, kw=dict(base_kind="trap"))
    index_run("index_trapTn_1.5s_aug0.12", "trap", 1.5, dict(base_cfg, aug_mass=0.12), kw=dict(fa=1 / fz / 1.5))
    index_run("index_trapTn_1.5s_aug0.20", "trap", 1.5, dict(base_cfg, aug_mass=0.20), kw=dict(fa=1 / fz / 1.5))

    # full laps of indexing
    for name, T, kw in (("lap12_trap_1.0s", 1.0, {}), ("lap12_trapTn_1.5s", 1.5, dict(fa=1 / fz / 1.5))):
        kind = "trap"
        sh, stops = M.sequence(KN.HOME_SHIFT, [(PR.MODULE_LINKS, T, "trap", 0.5, kw)] * 12)
        L = run_carousel(sh, base_cfg)
        res = analyse(L, stops, 0.5)
        R["runs"][name] = res
        LOGS[name] = (L, stops)
        print(f"lap12 {kind}: swing {res['max_swing_deg']:.2f} clr {res['min_neighbour_clearance_mm']:.1f} tq {res['motor_torque_peak_Nm']:.3f}")
    # continuous laps: 10 s (task), then faster what-ifs
    for Tlap, fa in ((10.0, 0.1), (6.0, 0.15), (4.0, 0.2)):
        sh, stops = M.sequence(KN.HOME_SHIFT, [(PR.N_LINKS, Tlap, "scurve", 2.0, dict(fa=fa))])
        L = run_carousel(sh, base_cfg)
        res = analyse(L, stops, 2.0)
        R["runs"][f"fastlap_{Tlap:g}s"] = res
        LOGS[f"fastlap_{Tlap:g}s"] = (L, stops)
        print(f"fastlap {Tlap}: swing {res['max_swing_deg']:.2f} {res['max_swing_by_region_deg']} clr {res['min_neighbour_clearance_mm']:.1f} shaft {res['min_shaft_clearance_mm']:.1f} tq {res['motor_torque_peak_Nm']:.3f}")

    # station
    ST = {}
    KS = 4 * T_CHAIN / (PR.LOOP_B * MM)             # one chain's bottom-run span stiffness at mid-span, N/m
    for nm, st, cfg in (("station_cad_rigidchain", {}, dict(base_cfg)),
                        ("station_cad_chain_nostrip", {}, dict(base_cfg, chain=dict(k_tab=K_TAB, k_span=KS, gap=None))),
                        ("station_cad_strip", {}, dict(base_cfg, chain=dict(k_tab=K_TAB, k_span=KS, gap=0.5 * MM))),
                        ("station_cad_strip_tab50", {}, dict(base_cfg, chain=dict(k_tab=50e3, k_span=KS, gap=0.5 * MM)))):
        Lg, T, geo, sinfo = run_station(st, cfg)
        ssum = station_summary(Lg, T, geo)
        ssum["rig"] = dict(STATION_BASE, **st)
        ssum["cfg"] = cfg
        R["runs"][nm] = ssum
        ST[nm] = (Lg, T, geo)
        print(nm, json.dumps({k: ssum[k] for k in ("min_pivot_Fz_N", "min_pivot_Fz_tilting_N", "chain_lifted", "max_swing_docked_deg", "actuator_force_peak_tilting_N", "pivot_rise_max_mm", "chain_rise_max_mm", "strip_force_max_N", "tilt_reached_deg")}))
    R["elapsed_s"] = time.time() - t_start
    def clean(o):                                   # strict JSON: NaN (not settled within the dwell) -> null
        if isinstance(o, dict):
            return {k: clean(v) for k, v in o.items()}
        if isinstance(o, (list, tuple)):
            return [clean(v) for v in o]
        if isinstance(o, (float, np.floating)):
            return None if math.isnan(float(o)) else float(o)
        if isinstance(o, np.integer):
            return int(o)
        return o
    with open(os.path.join(OUT, "results.json"), "w") as fh:
        json.dump(clean(R), fh, indent=1)
    import plots
    plots.make_all(R, LOGS, ST, DEC, fz)
    print("done in", time.time() - t_start)
    return R


if __name__ == "__main__":
    main(quick="--quick" in sys.argv)
