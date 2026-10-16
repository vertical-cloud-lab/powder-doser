"""MuJoCo model of the paternoster carousel: kinematic pivot table, motion
profiles and the MJCF builder. SI units inside MuJoCo (m, kg, s, N).

Every dimension comes from ../params.py and every pivot position from
../kinematics.py; nothing here re-derives the chain geometry.
"""
from __future__ import annotations

import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import kinematics as KN  # noqa: E402
import params as PR  # noqa: E402

OUT = os.path.join(HERE, "out")
os.makedirs(OUT, exist_ok=True)

MM = 1e-3
G = 9.81
DT = 5e-4                       # integrator step, s
NK = PR.N_MODULES
L_X = PR.CHAIN_L * MM
DELTA = KN.DELTA                # sprocket rotation per link, rad
KP_PIV = 2.0e5                  # chain "servo" stiffness per pivot axis, N/m (rigid chain)
KV_PIV = 550.0                  # its damping, N*s/m

# --- masses (kg), see README for the breakdown ---
M_END = 0.035                   # each printed end plate
M_FLOOR = 0.050                 # printed floor/rails
M_PLATE = 0.070                 # Sam's mounting plate
M_BRKT = 0.030                  # brackets, knuckles, fasteners
M_AUG_NOM = 0.16                # auger + powder (0.12-0.20)
M_CARR = 0.25                   # Sam's electronics carriage (NEMA 11 + solenoid + print)
J_DRIVE = 5.2e-3                # chain (2 x 1.14 m x 0.33 kg/m at R) + 8 sprockets + NEMA 34 rotor, kg*m^2

# ------------------------------------------------------------------ pivot table
DS = 0.002                      # table step, links
NG = int(round(PR.N_LINKS / DS))
_P0 = None


def pivot_table() -> np.ndarray:
    """Module 0's pivot (y, z) in mm for shift = i*DS, i = 0..NG (from kinematics.pivots).

    Module k at shift s sits where module 0 sits at s + 10k (its link is 10k pins
    ahead and the polygonal phase frac(s) is the same), so one call of
    kinematics.pivots(s) for s in [0, 10) fills twelve table entries.
    """
    global _P0
    if _P0 is not None:
        return _P0
    import hashlib
    key = hashlib.md5(b"".join(open(os.path.join(os.path.dirname(HERE), f), "rb").read()
                               for f in ("kinematics.py", "params.py"))).hexdigest()
    fn = os.path.join(OUT, "pivot_table.npz")
    if os.path.exists(fn):
        z = np.load(fn)
        if str(z.get("key", "")) == key:
            _P0 = z["P0"]
            return _P0
    nsub = int(round(PR.MODULE_LINKS / DS))
    P0 = np.zeros((NG + 1, 2))
    for i in range(nsub):
        pv = KN.pivots(i * DS)
        for k in range(NK):
            P0[i + k * nsub] = pv[k]
    P0[NG] = P0[0]
    np.savez_compressed(fn, P0=P0, key=key)
    _P0 = P0
    return P0


def module_u(shift, k):
    """Loop coordinate (links) of module k's SA-1 link midpoint."""
    return (np.asarray(shift)[..., None] + PR.MODULE_LINKS * np.asarray(k) + 0.5) % PR.N_LINKS


def pivots_mm(shift) -> np.ndarray:
    """(..., NK, 2) pivot positions in mm for an array of shifts (linear interpolation of the table)."""
    P0 = pivot_table()
    s = np.asarray(shift, dtype=float)
    u = (s[..., None] + PR.MODULE_LINKS * np.arange(NK)) % PR.N_LINKS
    x = u / DS
    i0 = np.floor(x).astype(int)
    w = (x - i0)[..., None]
    i0 = np.clip(i0, 0, NG - 1)
    return (1 - w) * P0[i0] + w * P0[i0 + 1]


def dpivot_ds_mm(shift) -> np.ndarray:
    """(..., NK, 2) d(pivot)/d(shift) in mm per link (centred difference on the table)."""
    h = 0.01
    return (pivots_mm(np.asarray(shift) + h) - pivots_mm(np.asarray(shift) - h)) / (2 * h)


REGIONS = [("bottom run", 0, 20), ("BR corner", 20, 28), ("right side", 28, 52), ("TR corner", 52, 60),
           ("top run", 60, 80), ("TL corner", 80, 88), ("left side", 88, 112), ("BL corner", 112, 120)]


def region_of(u):
    u = np.asarray(u)
    out = np.zeros(u.shape, dtype=int)
    for i, (_, a, b) in enumerate(REGIONS):
        out[(u >= a) & (u < b)] = i
    return out


# ------------------------------------------------------------------ motion profiles
def _shape(n, fa=1 / 3, r=0.0):
    """Normalised acceleration on tau in (0,1): +1 on [0,fa], 0, -1 on [1-fa,1]; linear jerk ramps of width r."""
    tau = (np.arange(n) + 0.5) / n
    a = np.zeros(n)
    acc = tau <= fa
    dec = tau >= 1 - fa
    if r > 0:
        a[acc] = np.clip(np.minimum(tau[acc], fa - tau[acc]) / r, 0, 1)
        a[dec] = -np.clip(np.minimum(tau[dec] - (1 - fa), 1 - tau[dec]) / r, 0, 1)
    else:
        a[acc] = 1.0
        a[dec] = -1.0
    return a


def move(D, T, kind="trap", fa=1 / 3, f_shaper=None, zeta=0.0, base_kind="scurve"):
    """Shift samples (links, step DT) for one move of D links lasting T s (shaped moves keep the total T)."""
    if kind == "zv":
        Td = 1.0 / f_shaper / math.sqrt(1 - zeta ** 2)
        K = math.exp(-zeta * math.pi / math.sqrt(1 - zeta ** 2))
        A1, A2 = 1 / (1 + K), K / (1 + K)
        base = move(D, T - Td / 2, base_kind, fa)
        lag = int(round(Td / 2 / DT))
        s1 = np.concatenate([base, np.full(lag, base[-1])])
        s2 = np.concatenate([np.zeros(lag), base])
        return A1 * s1 + A2 * s2
    n = int(round(T / DT))
    if kind == "zvd":                         # ZVD: impulses 1/4, 1/2, 1/4 at 0, Td/2, Td
        Td = 1.0 / f_shaper
        base = move(D, T - Td, base_kind, fa)
        lag = int(round(Td / 2 / DT))
        pad = lambda a, pre, post: np.concatenate([np.zeros(pre), a, np.full(post, a[-1])])
        return 0.25 * pad(base, 0, 2 * lag) + 0.5 * pad(base, lag, lag) + 0.25 * pad(base, 2 * lag, 0)
    r = 0.0 if kind == "trap" else fa / 3
    a = _shape(n, fa, r)
    v = np.cumsum(a)
    v -= np.linspace(0, v[-1], n)            # remove the O(1/n) residual so v(T) = 0 exactly
    s = np.cumsum(v)
    return D * s / s[-1]


def sequence(s0, moves, dwell0=0.3):
    """Concatenate (D, T, kind, dwell, kw) moves from shift s0; returns (shift samples, list of stop times)."""
    out = [np.full(int(round(dwell0 / DT)), s0)]
    cur = s0
    stops = []
    for D, T, kind, dwell, kw in moves:
        m = cur + move(D, T, kind, **kw)
        out.append(m)
        cur = m[-1]
        stops.append(sum(len(o) for o in out) * DT)
        out.append(np.full(int(round(dwell / DT)), cur))
    return np.concatenate(out), stops


# ------------------------------------------------------------------ MJCF builder
def lookat(pos, target, up=(0, 0, 1)):
    pos, target, up = (np.asarray(v, float) for v in (pos, target, up))
    f = target - pos
    f /= np.linalg.norm(f)
    r = np.cross(f, up)
    r /= np.linalg.norm(r)
    u = np.cross(r, f)
    return " ".join(f"{v:.4f}" for v in (*r, *u))


def _f(*v):
    return " ".join(f"{x:.6f}" for x in v)


def module_geoms(k, off=(0.0, 0.0, 0.0), aug_mass=M_AUG_NOM, with_auger=True):
    """Mounting plate + brackets (+ auger) in Sam's frame (hinge axis at origin), shifted by off."""
    ox, oy, oz = off
    m = "modhi" if k == 0 else "mod"
    s = [f'<geom name="mp{k}" type="box" pos="{_f(ox + 0.040, oy, oz - 0.0155)}" size="0.040 0.025 0.0025" '
         f'mass="{M_PLATE}" material="alu" contype="0" conaffinity="0"/>',
         f'<geom name="mb{k}" type="box" pos="{_f(ox + 0.015, oy, oz - 0.008)}" size="0.010 0.022 0.006" '
         f'mass="{M_BRKT}" material="alu" contype="0" conaffinity="0"/>']
    if with_auger:
        s += auger_geoms(k, off, aug_mass)
    return s


def auger_geoms(k, off=(0.0, 0.0, 0.0), aug_mass=M_AUG_NOM):
    ox, oy, oz = off
    x0 = PR.AUGER_Z0_XS * MM
    m = "auger0" if k == 0 else "auger"
    return [f'<geom name="ag{k}" type="cylinder" fromto="{_f(ox + x0, oy, oz, ox + x0 + PR.AUGER_LEN * MM, oy, oz)}" '
            f'size="0.014" mass="{aug_mass}" material="{m}" contype="0" conaffinity="0"/>',
            f'<geom name="agc{k}" type="cylinder" fromto="{_f(ox + x0 + 0.215, oy, oz, ox + x0 + 0.25, oy, oz)}" '
            f'size="0.0165" density="0" material="cap" contype="0" conaffinity="0"/>',
            f'<geom name="agg{k}" type="cylinder" fromto="{_f(ox + 0.004, oy, oz, ox + 0.010, oy, oz)}" '
            f'size="{PR.GEAR_R * MM:.4f}" density="0" material="gear" contype="0" conaffinity="0"/>',
            f'<geom name="agm{k}" type="box" pos="{_f(ox + 0.007, oy + 0.016, oz)}" size="0.0035 0.004 0.004" '
            f'density="0" material="cap" contype="0" conaffinity="0"/>']


GUIDE_PIN_X = (0.016, 0.309)
GUIDE_PIN_Z = -0.040
GUIDE_PIN_R = 0.0025
GUIDE_GAP = 0.0005


def build_xml(shift0, damping=1e-4, fric=0.0, aug_mass=M_AUG_NOM, station=None, channel=False,
              kz0=None, pitch0=False):
    """Return (xml, info). station: dict with actuator geometry for module 0's dock/tilt rig."""
    pv = pivots_mm(np.array([shift0]))[0] * MM
    hy = PR.GON_W / 2 * MM
    gz0, gz1 = PR.GON_Z0 * MM, PR.GON_Z1 * MM
    zc, hz = (gz0 + gz1) / 2, (gz1 - gz0) / 2
    ex0, ex1 = PR.END_X0 * MM, PR.END_X1 * MM
    xc, hx = (ex0 + ex1) / 2, (ex1 - ex0) / 2
    ft = PR.FLOOR_T * MM
    hingx, hingz = PR.HINGE_X * MM, PR.HINGE_Z * MM
    zb, ytop = PR.Z_BOT * MM, PR.Z_TOP * MM
    cy = PR.CORNER_Y * MM
    xml = []
    xml.append(f"""<mujoco model="paternoster">
  <compiler angle="degree"/>
  <option timestep="{DT}" integrator="implicitfast" gravity="0 0 -{G}" cone="elliptic"/>
  <size memory="64M"/>
  <visual>
    <global offwidth="1920" offheight="1080" fovy="40"/>
    <quality shadowsize="4096" offsamples="8"/>
    <headlight ambient="0.35 0.35 0.35" diffuse="0.55 0.55 0.55" specular="0.1 0.1 0.1"/>
    <map znear="0.01" zfar="20"/>
  </visual>
  <asset>
    <texture name="grid" type="2d" builtin="checker" rgb1="0.86 0.84 0.80" rgb2="0.80 0.78 0.74" width="512" height="512"/>
    <material name="bench" texture="grid" texrepeat="8 8" reflectance="0.05"/>
    <material name="petg" rgba="0.95 0.55 0.20 1"/>
    <material name="petghi" rgba="0.16 0.47 0.84 1"/>
    <material name="alu" rgba="0.72 0.74 0.78 1"/>
    <material name="auger" rgba="0.92 0.92 0.88 1"/>
    <material name="auger0" rgba="0.95 0.95 0.90 1"/>
    <material name="cap" rgba="0.25 0.25 0.28 1"/>
    <material name="gear" rgba="0.55 0.35 0.75 1"/>
    <material name="steel" rgba="0.55 0.57 0.60 1" specular="0.5" shininess="0.6"/>
    <material name="sprocket" rgba="0.35 0.36 0.38 1" specular="0.4"/>
    <material name="act" rgba="0.15 0.15 0.17 1"/>
    <material name="carr" rgba="0.10 0.65 0.45 1"/>
    <material name="rail" rgba="0.80 0.20 0.20 1"/>
    <material name="frame" rgba="0.75 0.77 0.80 0.25"/>
  </asset>
  <default>
    <geom contype="1" conaffinity="1" condim="3" friction="0.3 0.005 0.0001" solref="0.002 1" solimp="0.95 0.99 0.0005"/>
  </default>
  <worldbody>
    <light name="sun" pos="{_f(-0.6, -1.0, 2.0)}" dir="{_f(0.3, 0.5, -1)}" diffuse="0.6 0.6 0.6" castshadow="true"/>
    <geom name="bench" type="plane" pos="{_f(L_X / 2, 0, 0)}" size="0.9 0.6 0.01" material="bench" contype="0" conaffinity="0"/>
    <camera name="side" pos="{_f(L_X + 1.05, 0, 0.53)}" xyaxes="0 1 0 0 0 1" fovy="38"/>
    <camera name="iso" pos="{_f(-0.42, -0.78, 0.92)}" xyaxes="{lookat((-0.42, -0.78, 0.92), (0.17, 0.0, 0.50))}" fovy="42"/>
    <camera name="st_side" pos="{_f(0.17, -0.95, 0.40)}" xyaxes="1 0 0 0 0 1" fovy="40"/>
    <camera name="st_iso" pos="{_f(-0.36, -0.44, 0.27)}" xyaxes="{lookat((-0.36, -0.44, 0.27), (0.13, 0.0, 0.40))}" fovy="50"/>
""")
    # corner shafts: bottom ones go right through (collide), top ones are stubs outside the gondola span
    sr = PR.SHAFT_D / 2 * MM
    for sgn in (-1, 1):
        xml.append(f'    <geom name="shaft_b{"LR"[sgn > 0]}" type="cylinder" fromto="{_f(-0.040, sgn * cy, zb, L_X + 0.040, sgn * cy, zb)}" size="{sr:.5f}" material="steel"/>')
        for x0, x1 in ((-0.040, -0.0021), (L_X + 0.0021, L_X + 0.040)):
            xml.append(f'    <geom type="cylinder" fromto="{_f(x0, sgn * cy, ytop, x1, sgn * cy, ytop)}" size="{sr:.5f}" material="steel" contype="0" conaffinity="0"/>')
        for zz in (zb, ytop):
            for xs in (0.0, L_X):
                xml.append(f'    <geom type="cylinder" fromto="{_f(xs - 0.00213, sgn * cy, zz, xs + 0.00213, sgn * cy, zz)}" size="{PR.OD / 2 * MM:.5f}" material="sprocket" contype="0" conaffinity="0"/>')
                xml.append(f'    <geom type="cylinder" fromto="{_f(xs - 0.0222 if xs == 0 else xs, sgn * cy, zz, xs if xs == 0 else xs + 0.0222, sgn * cy, zz)}" size="{PR.HUB_D / 2 * MM:.5f}" material="sprocket" contype="0" conaffinity="0"/>')
    # frame posts (2020) and side plates, see-through, visual only
    for xs in (PR.SIDE_IN * MM - 0.010, L_X - PR.SIDE_IN * MM + 0.010):
        for ys in (-0.235, 0.235):
            xml.append(f'    <geom type="box" pos="{_f(xs, ys, 0.39)}" size="0.010 0.010 0.39" material="frame" contype="0" conaffinity="0"/>')
    if channel:
        zr = pv[0, 1] + GUIDE_PIN_Z
        off = GUIDE_PIN_R + GUIDE_GAP + 0.003
        for px in GUIDE_PIN_X:
            for sgn in (-1, 1):
                xml.append(f'    <geom name="rail{px:.3f}{"lu"[sgn > 0]}" type="box" pos="{_f(px, 0.0, zr + sgn * off)}" size="0.004 0.070 0.003" material="rail" contype="2" conaffinity="2" friction="0.15 0.005 0.0001"/>')

    info = {"y0": [], "z0": [], "station": None}
    for k in range(NK):
        y0, z0 = pv[k]
        info["y0"].append(y0)
        info["z0"].append(z0)
        mat = "petghi" if k == 0 else "petg"
        xml.append(f'    <body name="g{k}" pos="{_f(0, y0, z0)}">')
        xml.append(f'      <joint name="gy{k}" type="slide" axis="0 1 0"/>')
        xml.append(f'      <joint name="gz{k}" type="slide" axis="0 0 1"/>')
        if k == 0 and pitch0:      # station gondola: front and back pivots can rise separately (chain hold-down study)
            xml.append(f'      <joint name="gp0" type="hinge" axis="0 1 0" pos="{_f(L_X / 2, 0, 0)}"/>')
        xml.append(f'      <joint name="gs{k}" type="hinge" axis="1 0 0" damping="{damping}" frictionloss="{fric}"/>')
        xml.append(f'      <geom name="gef{k}" type="box" pos="{_f(xc, 0, zc)}" size="{_f(hx, hy, hz)}" mass="{M_END}" material="{mat}"/>')
        xml.append(f'      <geom name="geb{k}" type="box" pos="{_f(L_X - xc, 0, zc)}" size="{_f(hx, hy, hz)}" mass="{M_END}" material="{mat}"/>')
        xml.append(f'      <geom name="gfl{k}" type="box" pos="{_f(L_X / 2, 0, gz0 + ft / 2)}" size="{_f(L_X / 2 - ex1, hy, ft / 2)}" mass="{M_FLOOR}" material="{mat}"/>')
        xml.append(f'      <geom name="gsr{k}" type="box" pos="{_f(L_X / 2, -hy + 0.002, gz0 + 0.012)}" size="{_f(L_X / 2 - ex1, 0.002, 0.007)}" density="0" material="{mat}" contype="0" conaffinity="0"/>')
        xml.append(f'      <geom name="gsl{k}" type="box" pos="{_f(L_X / 2, hy - 0.002, gz0 + 0.012)}" size="{_f(L_X / 2 - ex1, 0.002, 0.007)}" density="0" material="{mat}" contype="0" conaffinity="0"/>')
        xml.append(f'      <geom name="gpv{k}" type="cylinder" fromto="{_f(-0.004, 0, 0, L_X + 0.004, 0, 0)}" size="0.0008" density="0" material="steel" contype="0" conaffinity="0" group="3"/>')
        for px in GUIDE_PIN_X if channel else ():
            xml.append(f'      <geom name="gp{k}_{px:.3f}" type="cylinder" fromto="{_f(px - 0.004, 0, GUIDE_PIN_Z, px + 0.004, 0, GUIDE_PIN_Z)}" size="{GUIDE_PIN_R}" mass="0.001" material="steel" contype="2" conaffinity="2" friction="0.15 0.005 0.0001"/>')
        if station is not None and k == 0:
            xml.append(f'      <body name="m0" pos="{_f(hingx, 0, hingz)}">')
            xml.append('        <joint name="mt0" type="hinge" axis="0 -1 0" range="0 95" limited="true" damping="0.002" solreflimit="0.004 1"/>')
            xml += ["        " + g for g in module_geoms(0, with_auger=False)]
            xml.append('        <body name="a0" pos="0 0 0">')
            xml.append('          <joint name="ar0" type="hinge" axis="1 0 0" frictionloss="0.03" armature="2e-5"/>')
            xml += ["          " + g for g in auger_geoms(0, aug_mass=aug_mass)]
            xml.append('        </body>')
            xml.append('      </body>')
        else:
            xml += ["      " + g for g in module_geoms(k, off=(hingx, 0, hingz), aug_mass=aug_mass)]
        xml.append('    </body>')

    if station is not None:
        a, b = station["a"], station["b"]
        hxw, hzw = hingx, pv[0, 1] + hingz
        if "base_rel" in station:
            xb, zbse = hxw + station["base_rel"][0], hzw + station["base_rel"][1]
        else:
            xb, zbse = station["xb"], station["zb"]
        pin_dock = np.array([hxw + a, hzw + b])
        base = np.array([xb, zbse])
        d0 = pin_dock - base
        L0 = float(np.linalg.norm(d0))
        d0 /= L0
        ret = PR.ACT_RETRACTED * MM
        pin_ret = base + ret * d0
        car_org = pin_ret - np.array([a, b])          # carriage frame (= hinge frame when docked), world-aligned
        info["station"] = dict(L0=L0, d0=d0.tolist(), base=base.tolist(), hinge=[hxw, hzw], ret=ret)
        # chain hold-down strips (UHMW-PE) over each chain's bottom run at the station: underside 0.5 mm above
        # the link plates (pitch line + 4.5 mm), y -60..60; visual here, the stop itself is in run_station
        z_pl = pv[0, 1] + PR.SA1_C * MM
        for xs in (0.0, L_X):
            xml.append(f'    <geom name="strip{xs:.3f}" type="box" pos="{_f(xs, 0, z_pl + 0.0050 + 0.003)}" size="0.006 0.060 0.003" rgba="0.95 0.95 0.95 1" contype="0" conaffinity="0"/>')
        kh = station.get("k_hold", 400.0)
        xml.append(f'    <body name="act" pos="{_f(xb, 0, zbse)}">')
        xml.append(f'      <joint name="act_pitch" type="hinge" axis="0 1 0" stiffness="{kh}" damping="0.05"/>')
        xml.append(f'      <joint name="act_roll" type="hinge" axis="1 0 0" stiffness="{station.get("k_roll", 150.0)}" damping="0.3"/>')
        xml.append(f'      <geom name="act_clevis" type="cylinder" fromto="{_f(0, -0.012, 0, 0, 0.012, 0)}" size="0.005" density="0" material="steel" contype="0" conaffinity="0"/>')
        xml.append(f'      <geom name="act_body" type="box" pos="{_f(*(0.09 * np.array([d0[0], 0, d0[1]])))}" size="0.0185 0.013 0.085" '
                   f'euler="0 {math.degrees(math.atan2(d0[0], d0[1])):.4f} 0" mass="0.10" material="act" contype="0" conaffinity="0"/>')
        xml.append('      <body name="rod" pos="0 0 0">')
        xml.append(f'        <joint name="act_slide" type="slide" axis="{_f(d0[0], 0, d0[1])}" range="0 {PR.ACT_STROKE * MM}" limited="true"/>')
        xml.append(f'        <geom name="rod_g" type="capsule" fromto="{_f(0.14 * d0[0], 0, 0.14 * d0[1], ret * d0[0], 0, ret * d0[1])}" size="0.004" mass="0.02" material="steel" contype="0" conaffinity="0"/>')
        xml.append(f'        <geom name="rod_v" type="capsule" fromto="{_f(0.02 * d0[0], 0, 0.02 * d0[1], 0.14 * d0[0], 0, 0.14 * d0[1])}" size="0.004" density="0" material="steel" contype="0" conaffinity="0"/>')
        cx, cz = car_org - base
        xml.append(f'        <body name="car" pos="{_f(cx, 0, cz)}">')
        xml.append(f'          <joint name="car_pitch" type="hinge" axis="0 1 0" pos="{_f(a, 0, b)}" stiffness="{kh}" damping="0.02"/>')
        xml.append(f'          <geom name="car_box" type="box" pos="{_f(0.0378, 0, -0.0355)}" size="0.0355 0.018 0.0175" mass="{M_CARR}" material="carr" contype="0" conaffinity="0"/>')
        xml.append(f'          <geom name="car_lug" type="box" pos="{_f(a, 0, (b - 0.053) / 2 if b < -0.053 else b)}" size="{_f(0.006, 0.006, max(0.004, abs(b + 0.053) / 2 + 0.004))}" density="0" material="carr" contype="0" conaffinity="0"/>')
        for cxx in (0.012, 0.064):
            xml.append(f'          <geom type="cylinder" fromto="{_f(cxx, 0.0, -0.018, cxx, 0.0, -0.0185)}" size="0.004" density="0" material="steel" contype="0" conaffinity="0"/>')
        xml.append(f'          <geom name="car_motor" type="box" pos="{_f(0.020, 0, -0.033)}" size="0.014 0.014 0.014" density="0" material="act" contype="0" conaffinity="0"/>')
        xml.append(f'          <geom name="car_sol" type="cylinder" fromto="{_f(0.045, 0.0, -0.040, 0.060, 0.0, -0.040)}" size="0.007" density="0" material="steel" contype="0" conaffinity="0"/>')
        xml.append('        </body>')
        xml.append('      </body>')
        xml.append('    </body>')
    xml.append('  </worldbody>')
    xml.append('  <actuator>')
    for k in range(NK):
        kp = KP_PIV
        kv = KV_PIV
        xml.append(f'    <general name="ay{k}" joint="gy{k}" gainprm="1" biastype="affine" biasprm="0 -{kp} -{kv}"/>')
        if k == 0 and kz0 is not None:
            kp, kv = kz0, 2 * 0.3 * math.sqrt(kz0 * 0.4)
        xml.append(f'    <general name="az{k}" joint="gz{k}" gainprm="1" biastype="affine" biasprm="0 -{kp} -{kv}"/>')
    if station is not None:
        xml.append(f'    <general name="act_drive" joint="act_slide" gainprm="1" biastype="affine" biasprm="0 -{station.get("kp_act", 3e4)} -{station.get("kv_act", 250)}" forcelimited="true" forcerange="-{station.get("fmax", 90)} {station.get("fmax", 90)}"/>')
        xml.append('    <velocity name="aug_drive" joint="ar0" kv="0.01" forcelimited="true" forcerange="-0.18 0.18"/>')
    xml.append('  </actuator>')
    if station is not None:
        xml.append('  <equality>')
        xml.append('    <weld name="dock" body1="m0" body2="car" relpose="0 0 0 1 0 0 0" active="false" solref="0.003 1"/>')
        xml.append('  </equality>')
    xml.append('</mujoco>')
    return "\n".join(xml), info
