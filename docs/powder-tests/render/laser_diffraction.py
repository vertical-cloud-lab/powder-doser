"""Particle-size distribution by laser diffraction (ASTM B822; technique per ISO 13320).

A wet recirculating set-up is shown: the powder is dispersed in water with a little
surfactant, stirred and pumped in a loop through a flow cell that sits in an expanded laser
beam. Particles scatter light: large ones strongly at small angles, small ones weakly at wide
angles. A Fourier lens maps each scattering angle onto a ring of a focal-plane detector
array (wide-angle and back-scatter detectors catch the rest); a central detector measures
the transmitted beam, i.e. the obscuration. A Mie model (needs the refractive indices) or the
Fraunhofer approximation inverts the angular pattern into a volume-weighted PSD.
B822 also allows dispersion in a gas for powders that react with liquids.

Angles and particle sizes are exaggerated; the PSD is an illustrative 15-45 um L-PBF cut.
"""
import matplotlib as mpl
from scipy.special import j1

from common import *  # noqa: F401,F403

NAME = "laser_diffraction"
ZB = 120.0                       # beam height above the bench
X_LASER0, X_LASER1 = -262.0, -182.0
X_EXP0, X_EXP1 = -160.0, -112.0
X_CELL = -60.0
X_LENS = 15.0
X_DET = 125.0
TANK = np.array([-175.0, 168.0])  # dispersion unit tank centre (x, y)
Z_TANK0, Z_TANK1 = 64.0, 172.0

# illustrative 316L L-PBF cut: lognormal volume distribution
D50, SIG = 31.4, 0.355
D10, D90 = D50 * math.exp(-1.2816 * SIG), D50 * math.exp(1.2816 * SIG)
OBSC = 10.8                      # % obscuration reached

TL = Timeline([
    Step(0.0, 4.8, "Assemble: laser, beam expander, flow cell, Fourier lens, detectors"),
    Step(4.8, 7.2, "Fill the dispersion unit with water + surfactant; pump and stir"),
    Step(7.2, 9.8, "Laser on: record the background with clean liquid"),
    Step(9.8, 12.8, "Add powder until obscuration is in range (about 5–15 %)"),
    Step(12.8, 18.2, "Particles scatter light: large ones at small angles, small at wide"),
    Step(18.2, 23.0, "A Mie (or Fraunhofer) model inverts the pattern into sizes"),
    Step(23.0, 27.6, "Report volume-weighted D10, D50, D90; compare like with like"),
])


# --------------------------------------------------------------------------- optics model
def fraunhofer_ring_energy(theta_deg, d50=D50, sig=SIG, lam=0.633):
    """Relative light energy per log-spaced detector ring for a lognormal volume PSD."""
    d = np.exp(np.linspace(math.log(d50) - 4 * sig, math.log(d50) + 4 * sig, 400))
    q3 = np.exp(-0.5 * ((np.log(d) - math.log(d50)) / sig) ** 2)
    th = np.radians(np.asarray(theta_deg))[:, None]
    u = np.pi * d[None, :] * np.sin(th) / lam
    airy = (2 * j1(u) / u) ** 2
    intensity = (q3[None, :] * d[None, :] * airy).sum(axis=1)
    e = intensity * th[:, 0] ** 2           # ring area grows with angle on a log-spaced array
    return e / e.max()


N_RING = 18
RING_THETA = np.logspace(math.log10(0.03), math.log10(12.0), N_RING)        # real angles (deg)
RING_R = np.logspace(math.log10(2.6), math.log10(44.0), N_RING + 1)          # drawn radii (mm)
E_RING = fraunhofer_ring_energy(RING_THETA)
WIDE_THETA = np.array([25.0, 35.0, 48.0, 62.0])
BACK_THETA = np.array([125.0, 145.0])
E_WIDE = np.array([0.020, 0.012, 0.008, 0.005])
E_BACK = np.array([0.003, 0.002])
CMAP = mpl.colormaps["inferno"]


def to_x(mesh, x, y=0.0, z=ZB):
    """Turn a z-axis lathe so its axis runs along +x, centred at (x, y, z)."""
    return mesh.rotate_y(90, inplace=False).translate((x, y, z), inplace=False)


def frustum_x(x0, r0, x1, r1, res=72):
    return to_x(lathe([(r0, 0.0), (r1, x1 - x0)], res=res, closed=False), x0)


def spline_tube(pts, r=3.2, n=80):
    return pv.Spline(np.asarray(pts, float), n).tube(radius=r, n_sides=20).triangulate()


# --------------------------------------------------------------------------- build
st = Stage(bench=(-360, 300, -200, 280))
st.add("rail", box(-275, 150, -38, 38, 0, 16), "dark")
for nm, x in (("post_l1", -245), ("post_l2", -200), ("post_e", -136), ("post_c", X_CELL), ("post_n", X_LENS),
              ("post_d", X_DET)):
    st.add(nm, rod((x, 0, 16), (x, 0, ZB - 18), 5.5), "steel")
# laser head (He-Ne style tube) and beam expander
st.add("laser", to_x(lathe([(0, 0), (24, 0), (24, X_LASER1 - X_LASER0), (8, X_LASER1 - X_LASER0 + 6),
                            (0, X_LASER1 - X_LASER0 + 6)]), X_LASER0), "dark", color="#24324a")
st.add("laser_band", to_x(tube(24.2, 25.5, 30, 42), X_LASER0), "orange")
st.add("expander", to_x(lathe([(0, 0), (9, 0), (9, 20), (19, 34), (19, X_EXP1 - X_EXP0), (0, X_EXP1 - X_EXP0)]),
                        X_EXP0), "steel_dark")
# flow cell: glass cuvette in a clamp frame, ports top and bottom
st.add("cell_glass", box(X_CELL - 7, X_CELL + 7, -20, 20, ZB - 36, ZB + 36), "glass", opacity=0.22)
st.add("cell_frame", box(X_CELL - 9, X_CELL + 9, -27, -20, ZB - 42, ZB + 42).merge(
    box(X_CELL - 9, X_CELL + 9, 20, 27, ZB - 42, ZB + 42)).merge(
    box(X_CELL - 9, X_CELL + 9, -27, 27, ZB - 46, ZB - 36)).merge(
    box(X_CELL - 9, X_CELL + 9, -27, 27, ZB + 36, ZB + 46)), "steel")
st.add("port_in", rod((X_CELL, 0, ZB - 46), (X_CELL, 0, ZB - 58), 4.2), "steel_dark")
st.add("port_out", rod((X_CELL, 0, ZB + 46), (X_CELL, 0, ZB + 58), 4.2), "steel_dark")
# Fourier lens in its ring mount
a, tc, te = 34.0, 11.0, 3.0
rr = np.linspace(0, a, 16)
lens_prof = [(r, -(te / 2 + (tc - te) / 2 * (1 - (r / a) ** 2))) for r in rr] + \
            [(r, te / 2 + (tc - te) / 2 * (1 - (r / a) ** 2)) for r in rr[::-1]]
st.add("lens", to_x(lathe(lens_prof), X_LENS), "glass", opacity=0.42, color="#b9dcff")
st.add("lens_mount", to_x(tube(34.2, 41, -7, 7), X_LENS), "dark")
# detector: PCB with concentric rings and a central (obscuration) detector
st.add("pcb", box(X_DET + 1, X_DET + 5, -58, 58, ZB - 58, ZB + 58), "green", color="#1f5a3a", specular=0.2)
for k in range(N_RING):
    r0, r1 = RING_R[k] + 0.35, RING_R[k + 1] - 0.35
    st.add(f"ring{k}", to_x(tube(r0, r1, -0.6, 0.0, res=96), X_DET + 1), "dark", color="#262a30",
           ambient=0.6, diffuse=0.4, specular=0.5)
st.add("centre", to_x(disc(1.9, -0.8, 0.0), X_DET + 1), "dark", color="#262a30", ambient=0.7)
# wide-angle chips on an arc behind the beam (+y side), back-scatter chips on the laser side
WIDE_P, BACK_P = [], []
for th in WIDE_THETA:
    R = 70.0
    p = np.array([X_CELL + R * math.cos(math.radians(th)), R * math.sin(math.radians(th)), ZB])
    WIDE_P.append(p)
for th in BACK_THETA:
    R = 55.0
    p = np.array([X_CELL + R * math.cos(math.radians(th)), R * math.sin(math.radians(th)), ZB])
    BACK_P.append(p)
for k, p in enumerate(WIDE_P + BACK_P):
    st.add(f"chip{k}", cbox(p, (7, 7, 7)), "dark", color="#2a3346", ambient=0.6)
    st.add(f"chipost{k}", rod((p[0], p[1], 16), (p[0], p[1], ZB - 4), 2.2), "steel")
# dispersion unit (pump base, glass tank, stirrer) and the silicone tubing loop
tx, ty = TANK
st.add("disp_base", box(tx - 75, tx + 75, ty - 58, ty + 58, 0, Z_TANK0), "light")
st.add("disp_panel", box(tx - 50, tx + 30, ty - 59.5, ty - 58, 18, 46), "lcd")
st.add("tank", lathe([(0, 0), (46, 0), (46, Z_TANK1 - Z_TANK0), (43.8, Z_TANK1 - Z_TANK0), (43.8, 2), (0, 2)])
       .translate((tx, ty, Z_TANK0), inplace=False), "glass", opacity=0.24)
st.add("motor", disc(17, Z_TANK1 + 24, Z_TANK1 + 62).translate((tx, ty, 0), inplace=False), "dark")
st.add("motor_arm", box(tx - 6, tx + 6, ty + 10, ty + 70, Z_TANK1 + 40, Z_TANK1 + 52).merge(
    box(tx - 6, tx + 6, ty + 58, ty + 70, Z_TANK0, Z_TANK1 + 52)), "mid")
st.add("shaft", rod((tx, ty, Z_TANK0 + 14), (tx, ty, Z_TANK1 + 24), 2.2), "steel")
imp = box(-15, 15, -3, 3, -1.5, 1.5).merge(box(-3, 3, -15, 15, -1.5, 1.5))
st.add("impeller", imp, "steel")
TUBE1 = [(tx + 40, ty - 58, 30), (tx + 70, ty - 100, 34), (X_CELL - 22, 34, 40), (X_CELL, 10, 50),
         (X_CELL, 0, ZB - 58)]
TUBE2 = [(X_CELL, 0, ZB + 58), (X_CELL, 10, ZB + 92), (X_CELL - 50, 90, ZB + 106), (tx + 14, ty - 28, Z_TANK1 + 22),
         (tx + 20, ty - 16, Z_TANK1 - 22)]
st.add("tube1", spline_tube(TUBE1), "glass", opacity=0.5, color="#dfe9f2")
st.add("tube2", spline_tube(TUBE2), "glass", opacity=0.5, color="#dfe9f2")
st.add("water", disc(43.6, 0, 1).translate((tx, ty, Z_TANK0 + 2), inplace=False), "glass", opacity=0.35,
       color="#8fc4ff")
st.add("spatula", box(-70, 0, -5, 5, -1, 1).merge(box(0, 26, -8, 8, -1.2, 1.2)), "steel")
# light: beams and scattered-light shells (glowing, unlit)
GLOW = dict(color=C["laser"], ambient=1.0, diffuse=0.0, specular=0.0)
st.add("beam_thin", to_x(disc(1.2, 0, X_EXP0 - X_LASER1), X_LASER1), GLOW, opacity=0.95)
st.add("beam_wide", to_x(disc(6.5, 0, X_LENS - 5 - X_EXP1), X_EXP1), GLOW, opacity=0.38)
st.add("beam_focus", frustum_x(X_LENS + 5, 6.5, X_DET, 0.7), GLOW, opacity=0.45)
SHELLS = [(3.2, 6.5, 0.20), (7.5, 18.0, 0.12), (12.5, 33.0, 0.07)]   # (visual angle, ring radius, opacity)
for k, (ang, R, op) in enumerate(SHELLS):
    r_l = (X_LENS - X_CELL) * math.tan(math.radians(ang))
    st.add(f"shellA{k}", frustum_x(X_CELL, 0.5, X_LENS - 5, r_l), GLOW, opacity=op)
    st.add(f"shellB{k}", frustum_x(X_LENS + 5, r_l, X_DET, R), GLOW, opacity=op)
for k, p in enumerate(WIDE_P + BACK_P):
    st.add(f"ray{k}", rod((X_CELL, 0, ZB), p, 0.9, res=12), GLOW, opacity=0.18 if k < 4 else 0.10)
st.shadow("sh_rail", (-62, 0), 255, 70, 0.30)
st.shadow("sh_disp", (tx, ty), 110, 85, 0.30)

# ---- particles: a recirculating loop (tube 1 -> cell -> tube 2) and a stirred tank
rng = np.random.default_rng(7)


def polyline(pts, n=200):
    sp = pv.Spline(np.asarray(pts, float), n).points
    seg = np.linalg.norm(np.diff(sp, axis=0), axis=1)
    return sp, np.r_[0, np.cumsum(seg)]


cell_path = [(X_CELL, 0, ZB - 58), (X_CELL, 0, ZB - 20), (X_CELL, 0, ZB + 20), (X_CELL, 0, ZB + 58)]
LOOP = np.vstack([pv.Spline(np.asarray(TUBE1, float), 120).points, pv.Spline(np.asarray(cell_path, float), 60).points,
                  pv.Spline(np.asarray(TUBE2, float), 120).points])
SEG = np.linalg.norm(np.diff(LOOP, axis=0), axis=1)
CUM = np.r_[0, np.cumsum(SEG)]
N_LOOP, N_TANK = 520, 700
LOOP_S0 = rng.uniform(0, CUM[-1], N_LOOP)
LOOP_OFF = rng.normal(0, 1, (N_LOOP, 2))
TANK_R = np.sqrt(rng.uniform(0.02, 1, N_TANK)) * 40.0
TANK_PH = rng.uniform(0, 2 * np.pi, N_TANK)
TANK_Z = rng.uniform(Z_TANK0 + 6, Z_TANK1 - 14, N_TANK)
TANK_W = rng.uniform(1.2, 2.6, N_TANK)
SIZE_RANK = rng.uniform(0, 1, N_LOOP + N_TANK)
COLS = grain_colors(N_LOOP + N_TANK, "#7c838b", 0.14, seed=9)
SHOW_T = rng.uniform(10.2, 12.4, N_LOOP + N_TANK)    # time each particle has been added/dispersed


def loop_points(t):
    s = (LOOP_S0 + 95.0 * t) % CUM[-1]
    idx = np.clip(np.searchsorted(CUM, s) - 1, 0, len(SEG) - 1)
    f = (s - CUM[idx]) / np.maximum(SEG[idx], 1e-9)
    p = LOOP[idx] + (LOOP[idx + 1] - LOOP[idx]) * f[:, None]
    in_cell = (np.abs(p[:, 0] - X_CELL) < 1.0) & (np.abs(p[:, 2] - ZB) < 36)
    p[:, 1] += np.where(in_cell, 17.0, 2.0) * np.tanh(LOOP_OFF[:, 0] / 1.5)
    p[:, 0] += np.where(in_cell, 4.5, 1.6) * np.tanh(LOOP_OFF[:, 1] / 1.5)
    return p


def tank_points(t, level):
    ph = TANK_PH + TANK_W * t
    z = np.minimum(TANK_Z + 4 * np.sin(1.7 * t + TANK_PH), level - 2)
    return np.c_[TANK[0] + TANK_R * np.cos(ph), TANK[1] + TANK_R * np.sin(ph), z]


chart_a, chart_b = Chart(), Chart()
CAM = [(0.0, -70, 50, 110, 930, 26, -22, 0.40), (4.6, -70, 50, 110, 930, 26, -15, 0.40),
       (6.6, -110, 80, 120, 860, 25, -14, 0.40), (7.6, -60, 20, 120, 780, 21, -22, 0.40),
       (9.6, -60, 20, 120, 780, 21, -20, 0.40), (11.0, -70, 60, 125, 840, 25, -16, 0.46),
       (12.8, -70, 60, 125, 840, 25, -16, 0.46), (14.2, 10, 0, 120, 470, 14, -55, 0.29),
       (18.2, 10, 0, 120, 470, 15, -47, 0.29), (19.6, -70, 40, 112, 900, 25, -20, 0.40),
       (27.6, -70, 40, 112, 920, 25, -10, 0.40)]


def keys(t, table):
    """Smoothstep between keyframe rows (t, v1, v2, ...); holds the ends."""
    if t <= table[0][0]:
        return table[0][1:]
    for a_, b_ in zip(table, table[1:]):
        if t <= b_[0]:
            u = ramp(t, a_[0], b_[0])
            return tuple(x + (y - x) * u for x, y in zip(a_[1:], b_[1:]))
    return table[-1][1:]


def rgb_of(v):
    c = CMAP(0.10 + 0.88 * float(np.clip(v, 0, 1)))
    return (c[0], c[1], c[2])


def frame(t):
    i, step = TL.current(t)
    labels, readouts = [], []

    # ---- assembly
    seq = [("rail", 0.1, (0, 0, -60)), ("laser", 0.5, (0, 0, 90)), ("laser_band", 0.5, (0, 0, 90)),
           ("post_l1", 0.5, (0, 0, 90)), ("post_l2", 0.5, (0, 0, 90)), ("expander", 0.9, (0, 0, 90)),
           ("post_e", 0.9, (0, 0, 90)), ("cell_glass", 1.3, (0, 0, 90)), ("cell_frame", 1.3, (0, 0, 90)),
           ("port_in", 1.3, (0, 0, 90)), ("port_out", 1.3, (0, 0, 90)), ("post_c", 1.3, (0, 0, 90)),
           ("lens", 1.7, (0, 0, 90)), ("lens_mount", 1.7, (0, 0, 90)), ("post_n", 1.7, (0, 0, 90)),
           ("pcb", 2.1, (0, 0, 90)), ("centre", 2.1, (0, 0, 90)), ("post_d", 2.1, (0, 0, 90)),
           ("disp_base", 2.9, (0, 140, 0)), ("disp_panel", 2.9, (0, 140, 0)), ("tank", 2.9, (0, 140, 0)),
           ("motor", 2.9, (0, 140, 0)), ("motor_arm", 2.9, (0, 140, 0)), ("shaft", 2.9, (0, 140, 0)),
           ("tube1", 3.4, (0, 0, 60)), ("tube2", 3.4, (0, 0, 60))]
    for nm, t0, off in seq:
        M, vis, _ = arrive(t, t0, offset=off)
        st.pose(nm, M, vis)
    for k in range(N_RING):
        st.pose(f"ring{k}", arrive(t, 2.1, offset=(0, 0, 90))[0], t >= 2.1)
    for k in range(len(WIDE_P) + len(BACK_P)):
        M, vis, _ = arrive(t, 2.5, offset=(0, 0, 90))
        st.pose(f"chip{k}", M, vis)
        st.pose(f"chipost{k}", M, vis)
    imp_M = matrix(translate=(TANK[0], TANK[1], Z_TANK0 + 16), rot_deg=(t * 720.0 if t >= 5.2 else 0.0))
    st.pose("impeller", matrix(translate=(0, 140 * (1 - ramp(t, 2.9, 3.8)), 0)) @ imp_M, t >= 2.9)

    # ---- liquid
    level = Z_TANK0 + 2 + (Z_TANK1 - Z_TANK0 - 22) * ramp(t, 5.0, 6.6)
    if t >= 5.0:
        st.add("water", lathe([(0, 0), (43.6, 0), (43.6, level - Z_TANK0 - 2), (0, level - Z_TANK0 - 2)])
               .translate((TANK[0], TANK[1], Z_TANK0 + 2), inplace=False), "glass", opacity=0.30, color="#8fc4ff")
        wet = ramp(t, 6.0, 7.0)
        for nm in ("tube1", "tube2"):
            st.pl.actors[nm].prop.color = tuple(np.array([0.875, 0.914, 0.949]) * (1 - wet)
                                                + np.array([0.56, 0.77, 1.0]) * wet)
        st.pl.actors["cell_glass"].prop.color = tuple(np.array([0.81, 0.90, 0.98]) * (1 - wet)
                                                     + np.array([0.56, 0.77, 1.0]) * wet)
    else:
        st.pose("water", None, False)

    # ---- light
    laser_on = t >= 7.3
    beam_a = ramp(t, 7.3, 7.6)
    for nm, op in (("beam_thin", 0.95), ("beam_wide", 0.38), ("beam_focus", 0.45)):
        st.pose(nm, None, laser_on, opacity=op * beam_a)
    sample = ramp(t, 10.2, 12.4)                 # how much powder is dispersed
    scat = sample * (1.0 if laser_on else 0.0)
    flick = 1.0 + 0.10 * math.sin(23.0 * t) + 0.06 * math.sin(41.0 * t + 1.0)
    for k, (_, _, op) in enumerate(SHELLS):
        st.pose(f"shellA{k}", None, scat > 0.02, opacity=op * scat * flick)
        st.pose(f"shellB{k}", None, scat > 0.02, opacity=op * scat * flick)
    for k in range(len(WIDE_P) + len(BACK_P)):
        st.pose(f"ray{k}", None, scat > 0.02, opacity=(0.18 if k < 4 else 0.10) * scat)
    # detector rings light up with the measured pattern
    for k in range(N_RING):
        v = E_RING[k] * scat * (1.0 + 0.12 * math.sin(17.0 * t + 1.3 * k))
        st.pl.actors[f"ring{k}"].prop.color = rgb_of(v) if v > 0.01 else (0.15, 0.16, 0.19)
    st.pl.actors["centre"].prop.color = rgb_of(1.0 - 0.6 * scat) if laser_on else (0.15, 0.16, 0.19)
    for k in range(len(WIDE_P) + len(BACK_P)):
        e = (E_WIDE[k] if k < 4 else E_BACK[k - 4]) * 25 * scat
        st.pl.actors[f"chip{k}"].prop.color = rgb_of(e) if e > 0.02 else (0.16, 0.2, 0.27)

    # ---- spatula adds the powder; particles in the tank and the loop
    sp_in, sp_out = ramp(t, 9.6, 10.1), ramp(t, 11.4, 11.9)
    tilt = ramp(t, 10.1, 10.5) * (1 - ramp(t, 11.2, 11.5))
    Ms = matrix(translate=(TANK[0] - 10 - 200 * (1 - sp_in) - 200 * sp_out, TANK[1] - 20, Z_TANK1 + 30)) @ \
        matrix(rot_deg=-35 * tilt, axis=(1, 0, 0), origin=(13, 0, 0))
    st.pose("spatula", Ms, 9.6 <= t < 11.9)
    pts, cols = [], []
    if 10.2 <= t < 11.5:
        p, _ = stream(t, 10.2, 11.3, 260, (TANK[0] + 3, TANK[1] - 20, Z_TANK1 + 28), 4.0, v0=30,
                      floor=lambda x, y: level + 0 * x, seed=21)
        pts.append(p)
        cols.append(COLS[: len(p)])
    shown = t >= SHOW_T
    tp = tank_points(t, level)
    sel = shown[N_LOOP:]
    pts.append(tp[sel])
    cols.append(COLS[N_LOOP:][sel])
    lp = loop_points(t)
    # loop particles enter from the tank a little after dispersion
    sel = t >= SHOW_T[:N_LOOP] + 0.6
    pts.append(lp[sel])
    cols.append(COLS[:N_LOOP][sel])
    P = np.vstack(pts) if pts else np.empty((0, 3))
    st.grains("particles", P, np.vstack(cols) if len(P) else None, size=3.4)

    # ---- camera
    fx, fy, fz, dist, el, az, wc = keys(t, CAM)
    st.orbit((fx, fy, fz), dist, az, el)
    st.pl.camera.SetWindowCenter(wc, -0.04)
    rgb = st.render()

    # ---- labels
    def lab(text, xyz, off, t0, t1):
        a_ = ramp(t, t0, t0 + 0.35) * (1 - ramp(t, t1 - 0.35, t1))
        if a_ > 0:
            labels.append(Label(text, xyz, off, a_))
    lab("Laser (red, 633 nm)", (X_LASER0 + 30, -24, ZB - 10), (10, 110), 0.7, 2.6)
    lab("Beam expander", (X_EXP0 + 30, -19, ZB - 8), (40, 150), 1.1, 3.0)
    lab("Flow cell", (X_CELL, -27, ZB - 30), (60, 100), 1.5, 3.4)
    lab("Fourier lens", (X_LENS, -41, ZB - 10), (40, 95), 1.9, 3.8)
    lab("Ring detector array", (X_DET, -58, ZB - 40), (20, 150), 2.3, 4.4)
    lab("Wide-angle and back-scatter detectors", (WIDE_P[2][0], WIDE_P[2][1], ZB + 5), (-30, -80), 2.7, 4.6)
    lab("Dispersion unit: tank, stirrer, pump", (TANK[0] + 40, TANK[1] - 20, Z_TANK1 - 5), (60, -40), 3.1, 6.8)
    lab("Transmitted beam → central detector (obscuration)", (X_DET, 0, ZB), (-40, 150), 7.8, 10.6)
    lab("Large particles: strong light at small angles", (X_LENS + 40, 0, ZB + 12), (-60, -150), 14.4, 18.2)
    lab("Small particles: weak light at wide angles", WIDE_P[1], (40, 210), 15.0, 18.2)
    lab("Each ring sees one band of angles", (X_DET, -30, ZB - 25), (-20, 120), 15.6, 18.2)

    # ---- readouts
    if laser_on:
        ob = OBSC * sample * (1 + 0.02 * math.sin(9 * t)) if sample > 0 else 0.0
        col = "#7CFC9A" if 5.0 <= ob <= 15.0 else "#FFD166"
        readouts.append(Readout("OBSCURATION", f"{ob:4.1f} %", col))
    if t >= 19.4:
        readouts.append(Readout("D10", f"{D10:4.1f} µm", "#FFD166"))
    if t >= 20.0:
        readouts.append(Readout("D50", f"{D50:4.1f} µm", "#FFD166"))
    if t >= 20.6:
        readouts.append(Readout("D90", f"{D90:4.1f} µm", "#FFD166"))
    if t >= 21.4:
        readouts.append(Readout("SPAN", f"{(D90 - D10) / D50:4.2f}", "#FFD166"))

    # ---- charts: scattered light per detector, then the PSD
    def plot_a(fig):
        ax = fig.add_axes([0.14, 0.19, 0.82, 0.68])
        style_axes(ax, "Light on each detector")
        th = np.r_[RING_THETA, WIDE_THETA, BACK_THETA]
        e = np.r_[E_RING, E_WIDE, E_BACK]
        bg = 2e-4 * (1 + 0.3 * np.sin(np.arange(len(th)) * 1.7))
        if laser_on:
            ax.plot(th, bg, color="#888", lw=1.2, ls="--", marker="o", ms=2.5, label="background (clean liquid)")
        avg = ramp(t, 12.8, 16.5)
        if scat > 0.02:
            noise = 1 + 0.25 * (1 - avg) * np.sin(np.arange(len(th)) * 2.3 + 11 * t)
            ax.plot(th, np.maximum(bg, e * scat * noise), color=C["red"], lw=2.0, marker="o", ms=3,
                    label="with sample")
        ax.set_xscale("log")
        ax.set_yscale("log")
        ax.set_xlim(0.02, 200)
        ax.set_ylim(1e-4, 2)
        ax.set_xlabel("scattering angle (degrees)")
        ax.set_ylabel("relative light energy")
        if laser_on:
            ax.legend(fontsize=7.5, loc="upper right", frameon=False)

    def plot_b(fig):
        ax = fig.add_axes([0.14, 0.19, 0.82, 0.68])
        style_axes(ax, "Particle-size distribution (by volume)")
        d = np.logspace(math.log10(3), math.log10(150), 300)
        q = np.exp(-0.5 * ((np.log(d) - math.log(D50)) / SIG) ** 2)
        q = 100 * q / q.sum() * (300 / (math.log10(50) * 20))    # % per 1/20 decade, for display
        grow = ramp(t, 18.6, 19.3)
        ax.fill_between(d, 0, q * grow, color=C["blue"], alpha=0.25)
        ax.plot(d, q * grow, color=C["blue"], lw=2.2)
        for v, nm, t0, hy in ((D10, "D10", 19.4, 1.06), (D50, "D50", 20.0, 1.15), (D90, "D90", 20.6, 1.06)):
            if t >= t0:
                ax.axvline(v, color=C["orange"], lw=1.4, ls="--")
                ax.text(v, q.max() * hy, nm, ha="center", fontsize=8.5, color=C["orange"], fontweight="bold")
        ax.set_xscale("log")
        ax.set_xlim(3, 150)
        ax.set_ylim(0, q.max() * 1.28)
        ax.set_xlabel("particle size (µm)")
        ax.set_ylabel("volume density (%)")

    xf = ramp(t, 18.2, 18.7)
    if xf <= 0:
        img = chart_a.draw(plot_a)
    elif xf >= 1:
        img = chart_b.draw(plot_b)
    else:
        img = Image.blend(chart_a.draw(plot_a), chart_b.draw(plot_b), xf)
    ov = Overlay("Laser diffraction", "Particle-size distribution from the angles of scattered light",
                 "ASTM B822", "ISO 13320", labels=labels, readouts=readouts, chart=img,
                 step_idx=i, n_steps=len(TL.steps), step_text=step.text,
                 footer="Schematic; angles and particles exaggerated; values illustrative")
    return compose(rgb, ov, st)


if __name__ == "__main__":
    run(frame, NAME, TL.duration, gif_fps=10, gif_width=600, gif_colors=112)
