"""MuJoCo collision geometry of the lab's rotating auger cartridge.

All numbers below were measured from ``reference/auger-threaded-storage.step``
by ``measure_auger.py`` (cadquery/OCP tessellation + trimesh ray casts; raw
output in ``out/auger/auger_geometry_raw.json``).  Auger frame: axis +z, outlet
plane at z = 0, cap end at z = 250 mm.  Units in this module are millimetres;
the model builder converts to metres.

Measured (STEP):
  bore (tube ID)            21.0 mm  (r = 10.50) from z = 12 to 250
  tube OD                   25.0 mm  (r = 12.50); 44T gear OD 46 mm at z ~ 78-88
  solid core                r = 4.00 from z = 12.0 to 83.33 (8 pitches); nothing above
  core tip (cone)           r = 0.40 + 0.30 z   (0.40 at the exit plane -> 4.00 at z = 12)
  funnel (cone)             r = 1.50 + 0.75 z   (exit hole r = 1.50 -> bore 10.50 at z = 12;
                                                 36.9 deg half-angle)
  exit                      annulus r 0.40 .. 1.50 mm (6.6 mm^2), 1.1 mm wide
  flight                    single start, right-handed, pitch 10.417 mm (= 250/24),
                            0.50 mm thick (axial), from core/tip to wall/funnel,
                            lower face z = p * theta / 2pi (mod p), runs from the
                            exit plane up to z = 83.33 (8 turns)
  storage                   open bore r = 10.5 from z = 83.33 to the cap (z = 250)
"""
from __future__ import annotations

import numpy as np

BORE_R = 10.50
CORE_R = 4.00
CORE_TOP = 83.33
FUNNEL_H = 12.0
PITCH = 10.417
FLIGHT_T = 0.50
TUBE_LEN = 250.0


def r_wall(z):
    """Inner wall radius (funnel cone below z = 12, bore above)."""
    return np.minimum(1.50 + 0.75 * np.asarray(z, float), BORE_R)


def r_tip(z):
    """Core radius (core-tip cone below z = 12)."""
    return np.minimum(0.40 + 0.30 * np.asarray(z, float), CORE_R)


def z_cut_for_annulus(width):
    """Height where the funnel/tip annulus is ``width`` mm wide (w = 1.1 + 0.45 z)."""
    return max(0.0, (width - 1.10) / 0.45)


def _rotmat_to_quat(R):
    """Rotation matrix (columns = box axes) -> MuJoCo quaternion (w, x, y, z)."""
    m = R
    tr = m[0, 0] + m[1, 1] + m[2, 2]
    if tr > 0:
        s = np.sqrt(tr + 1.0) * 2
        w = 0.25 * s
        x = (m[2, 1] - m[1, 2]) / s
        y = (m[0, 2] - m[2, 0]) / s
        z = (m[1, 0] - m[0, 1]) / s
    elif m[0, 0] > m[1, 1] and m[0, 0] > m[2, 2]:
        s = np.sqrt(1.0 + m[0, 0] - m[1, 1] - m[2, 2]) * 2
        w = (m[2, 1] - m[1, 2]) / s
        x = 0.25 * s
        y = (m[0, 1] + m[1, 0]) / s
        z = (m[0, 2] + m[2, 0]) / s
    elif m[1, 1] > m[2, 2]:
        s = np.sqrt(1.0 + m[1, 1] - m[0, 0] - m[2, 2]) * 2
        w = (m[0, 2] - m[2, 0]) / s
        x = (m[0, 1] + m[1, 0]) / s
        y = 0.25 * s
        z = (m[1, 2] + m[2, 1]) / s
    else:
        s = np.sqrt(1.0 + m[2, 2] - m[0, 0] - m[1, 1]) * 2
        w = (m[1, 0] - m[0, 1]) / s
        x = (m[0, 2] + m[2, 0]) / s
        y = (m[1, 2] + m[2, 1]) / s
        z = 0.25 * s
    q = np.array([w, x, y, z])
    return q / np.linalg.norm(q)


def auger_boxes(z_cut=0.0, z_top=100.0, n_wall=36, n_funnel=36, n_tip=24,
                dtheta_deg=10.0, wall_t=1.0):
    """Return a list of geoms (dict(kind, type, size, pos, quat)) in mm, auger frame.

    z_cut: the outlet plane (0 = the real CAD exit; > 0 truncates funnel + tip there,
    i.e. a wider exit hole for coarse proxy grains).  z_top: storage closed here
    (powder never reaches it in these runs).
    """
    geoms = []
    # --- tube wall: ring of thin boxes, inner faces tangent to r = BORE_R
    half_w = BORE_R * np.tan(np.pi / n_wall) * 1.15 + 0.3
    zc, hz = 0.5 * (FUNNEL_H - 0.3 + z_top), 0.5 * (z_top - FUNNEL_H + 0.3)
    for i in range(n_wall):
        th = 2 * np.pi * i / n_wall
        er = np.array([np.cos(th), np.sin(th), 0.0])
        et = np.array([-np.sin(th), np.cos(th), 0.0])
        R = np.stack([er, et, [0, 0, 1.0]], 1)
        pos = er * (BORE_R + wall_t / 2) + np.array([0, 0, zc])
        geoms.append(dict(kind="wall", type="box", size=[wall_t / 2, half_w, hz],
                          pos=pos, quat=_rotmat_to_quat(R), theta=th))
    # --- funnel cone planks (inner face tangent to r_wall(z), z_cut..12)
    if z_cut < FUNNEL_H:
        L = np.hypot(FUNNEL_H - z_cut, r_wall(FUNNEL_H) - r_wall(z_cut))
        gen = np.array([0.75, 1.0]) / np.hypot(0.75, 1.0)  # (dr, dz) along generatrix
        nrm = np.array([1.0, -0.75]) / np.hypot(0.75, 1.0)  # outward normal (r, z)
        zm = 0.5 * (z_cut + FUNNEL_H)
        rm = float(r_wall(zm))
        half_w = BORE_R * np.tan(np.pi / n_funnel) * 1.2 + 0.2
        for i in range(n_funnel):
            th = 2 * np.pi * i / n_funnel
            er = np.array([np.cos(th), np.sin(th), 0.0])
            et = np.array([-np.sin(th), np.cos(th), 0.0])
            eg = gen[0] * er + np.array([0, 0, gen[1]])
            en = nrm[0] * er + np.array([0, 0, nrm[1]])
            R = np.stack([en, et, eg], 1)
            pos = er * rm + np.array([0, 0, zm]) + en * (wall_t / 2)
            geoms.append(dict(kind="funnel", type="box", size=[wall_t / 2, half_w, L / 2 + 0.25],
                              pos=pos, quat=_rotmat_to_quat(R), theta=th))
    # --- solid core cylinder + core-tip cone planks (outer face tangent to r_tip)
    geoms.append(dict(kind="core", type="cylinder", size=[CORE_R, 0.5 * (CORE_TOP - FUNNEL_H)],
                      pos=np.array([0, 0, 0.5 * (CORE_TOP + FUNNEL_H)]), quat=np.array([1, 0, 0, 0.0]), theta=0))
    if z_cut < FUNNEL_H:
        L = np.hypot(FUNNEL_H - z_cut, r_tip(FUNNEL_H) - r_tip(z_cut))
        gen = np.array([0.30, 1.0]) / np.hypot(0.30, 1.0)
        nrm = np.array([1.0, -0.30]) / np.hypot(0.30, 1.0)
        zm = 0.5 * (z_cut + FUNNEL_H)
        rm = float(r_tip(zm))
        half_w = CORE_R * np.tan(np.pi / n_tip) * 1.2
        t = 0.8
        for i in range(n_tip):
            th = 2 * np.pi * i / n_tip
            er = np.array([np.cos(th), np.sin(th), 0.0])
            et = np.array([-np.sin(th), np.cos(th), 0.0])
            eg = gen[0] * er + np.array([0, 0, gen[1]])
            en = nrm[0] * er + np.array([0, 0, nrm[1]])
            R = np.stack([en, et, eg], 1)
            pos = er * rm + np.array([0, 0, zm]) - en * (t / 2)
            geoms.append(dict(kind="tip", type="box", size=[t / 2, half_w, L / 2],
                              pos=pos, quat=_rotmat_to_quat(R), theta=th))
    # --- helical flight: one flat box per 10 deg, tilted to the local helix angle
    dth = np.radians(dtheta_deg)
    th = 0.0
    while True:
        thc = th + dth / 2
        zc = PITCH * thc / (2 * np.pi) + FLIGHT_T / 2
        if zc > CORE_TOP - FLIGHT_T / 2:
            break
        th += dth
        if zc < z_cut + FLIGHT_T / 2:
            continue
        ri, ro = float(r_tip(zc)), float(r_wall(zc))
        rc = 0.5 * (ri + ro)
        alpha = np.arctan(PITCH / (2 * np.pi * rc))
        er = np.array([np.cos(thc), np.sin(thc), 0.0])
        tan = np.array([-np.sin(thc), np.cos(thc), 0.0]) * np.cos(alpha) + np.array([0, 0, np.sin(alpha)])
        n = np.cross(er, tan)
        R = np.stack([er, tan, n], 1)
        half_len = 0.5 * ro * dth / np.cos(alpha) * 1.25
        pos = er * rc + np.array([0, 0, zc])
        geoms.append(dict(kind="flight", type="box",
                          size=[0.5 * (ro - ri) + 0.15, half_len, 0.5 * FLIGHT_T * np.cos(alpha)],
                          pos=pos, quat=_rotmat_to_quat(R), theta=thc))
    # --- closed storage end (stands in for the cap; powder never reaches it)
    geoms.append(dict(kind="cap", type="cylinder", size=[BORE_R + 1.0, 1.0],
                      pos=np.array([0, 0, z_top + 1.0]), quat=np.array([1, 0, 0, 0.0]), theta=0))
    return geoms


def free_slot(r, th, z, rp, z_cut=0.0):
    """True if a sphere of radius rp centred at (r, th, z) (auger frame, mm) clears all walls."""
    if z < max(z_cut, FUNNEL_H) + rp + 0.2:
        return False
    if r > BORE_R - rp - 0.15:
        return False
    if z < CORE_TOP + rp + 0.2:
        if r < CORE_R + rp + 0.15:
            return False
        zl = (z - PITCH * (th % (2 * np.pi)) / (2 * np.pi)) % PITCH
        if zl < FLIGHT_T + rp + 0.15 or zl > PITCH - rp - 0.15:
            return False
    return True
