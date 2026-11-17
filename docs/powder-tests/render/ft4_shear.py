"""FT4 Powder Rheometer shear cell (ASTM D7891-24): yield locus and flow function ffc.

The bed in a 25 mm borosilicate split vessel is conditioned with a helical blade,
consolidated with a vented piston to the pre-consolidation stress (9 kPa), split to
leave a level bed of known volume, then sheared by a bladed head: pre-shear at 9 kPa to
a steady state, then shear to failure at lower stresses (here 7, 6, 5, 4 and 3 kPa),
pre-shearing before each.
The failure points give the yield locus; its Mohr circles give the unconfined yield
strength sigma_c and the major principal stress sigma_1, and ffc = sigma_1 / sigma_c.
Values are illustrative (an AlSi10Mg-like powder), not measurements.
"""
from common import *  # noqa: F401,F403
from shear_analysis import ffc_class, fit_locus, locus_chart, mohr

NAME = "ft4_shear"
POWDER = "#aeb3b9"
COH, PHI = 0.90, 30.0                 # kPa, deg: illustrative linear yield locus
SIG_PRE = 9.0
SIG_SH = [7.0, 6.0, 5.0, 4.0, 3.0]
TAU_PRE = COH + math.tan(math.radians(PHI)) * SIG_PRE + 0.18
NOISE = [0.06, -0.05, 0.04, -0.03, 0.05]
TAU_F = [COH + math.tan(math.radians(PHI)) * s + e for s, e in zip(SIG_SH, NOISE)]

# geometry (mm)
Z_PLAT = 55.0            # top of the instrument base
Z_SEAT = 64.0            # top of the load-cell puck the vessel sits on
Z_FLOOR = 70.0           # vessel floor
R_IN, R_GL = 12.5, 15.0  # bore and glass outer radius
Z_SPLIT = 90.4           # top of the lower vessel: 10 mL below this line
Z_EXT0, Z_EXT1 = 93.0, 128.0
R_BED = 12.35
SHAFT = 62.0             # spindle length below the carriage
Z_FILL = 123.5           # poured height (mound apex a little higher)
Z_COND = 121.0           # level after conditioning
Z_CONS = 113.0           # after consolidation at 9 kPa
CUT = (-40.0, 220.0)     # section through the powder bed, facing the camera
T_SH0, T_SH1 = 16.6, 26.6
SEGS = [("pre", SIG_PRE)]
for s_ in SIG_SH:
    SEGS += [("sh", s_), ("pre", SIG_PRE)]
SEGS = SEGS[:-1]          # ends on the last shear step
SEG_T = (T_SH1 - T_SH0) / len(SEGS)

TL = Timeline([
    Step(0.0, 4.6, "Assemble: base with load-cell seat, drive tower, split glass vessel"),
    Step(4.6, 7.0, "Fill the 25 mm split vessel with powder"),
    Step(7.0, 10.2, "Condition: blade spirals down and up for a uniform, loose packing"),
    Step(10.2, 13.2, "Vented piston consolidates the bed to 9 kPa; air escapes"),
    Step(13.2, 15.2, "Split the vessel: excess powder leaves a level 10 mL bed"),
    Step(15.2, 16.6, "Bladed shear head moves down; its blades enter the bed"),
    Step(16.6, 26.6, "Pre-shear at 9 kPa; shear to failure at e.g. 7, 6, 5, 4, 3 kPa"),
    Step(26.6, 31.0, "Yield locus + Mohr circles give σc and σ1; ffc = σ1 / σc"),
])


# --------------------------------------------------------------------------- Mohr analysis
C_FIT, MU_FIT = fit_locus(SIG_SH, TAU_F)
SIG_C, X0, R1, SIG_1 = mohr(C_FIT, MU_FIT, SIG_PRE, TAU_PRE)
FFC = SIG_1 / SIG_C


# --------------------------------------------------------------------------- shear-test signals
def seg_at(t):
    """(segment index, kind, sigma, fraction within segment) during the shear test."""
    u = (t - T_SH0) / SEG_T
    i = int(np.clip(math.floor(u), 0, len(SEGS) - 1))
    return i, SEGS[i][0], SEGS[i][1], float(np.clip(u - i, 0, 1))


def tau_in_seg(i, s):
    kind, sig = SEGS[i]
    if kind == "pre":
        v = TAU_PRE * (1 - math.exp(-s / 0.14))
    else:
        pk = TAU_F[SIG_SH.index(sig)]
        v = pk * (1 - math.exp(-s / 0.12)) / (1 - math.exp(-0.55 / 0.12)) if s < 0.55 else \
            pk * (1 - 0.16 * smooth((s - 0.55) / 0.35))
    return v * (1 - smooth((s - 0.9) / 0.1)) if s > 0.9 else v


def sigma_in_seg(i, s):
    kind, sig = SEGS[i]
    prev = SEGS[i - 1][1] if i > 0 else 0.0
    return prev + (sig - prev) * smooth(s / 0.08)


def head_turn(t):
    """Cumulative shear-head rotation (deg, exaggerated for the eye)."""
    if t <= T_SH0:
        return 0.0
    i, kind, _, s = seg_at(min(t, T_SH1 - 1e-6))
    done = sum(16.0 if k == "pre" else 10.0 for k, _ in SEGS[:i])
    return done + (16.0 if kind == "pre" else 10.0) * smooth(min(s, 0.9) / 0.9)


def dilation(t):
    if not (T_SH0 <= t < T_SH1):
        return 0.0
    i, kind, _, s = seg_at(t)
    return 0.45 * math.sin(math.pi * min(s / 0.9, 1)) if kind == "sh" else 0.0


# --------------------------------------------------------------------------- stage
st = Stage(bench=(-260, 260, -150, 200))
# instrument: base, vessel seat over the load cell, tower with the vertical/rotary drive
st.add("base", box(-110, 110, -70, 95, 0, Z_PLAT), "light")
st.add("panel", box(-100, 100, -70.6, -70, 8, 46), "dark")
st.add("led", box(60, 88, -71.2, -70.5, 30, 38), "lcd", color="#38c172")
st.add("plate", disc(36, Z_PLAT, Z_PLAT + 4), "steel_dark")
st.add("loadcell", disc(24, Z_PLAT + 4, Z_SEAT), "dark")
st.add("tower", box(-55, 55, 62, 125, Z_PLAT, 440), "light")
st.add("rail", box(-11, 11, 58, 62, 80, 420), "dark")
st.add("topcap", box(-58, 58, 58, 128, 440, 452), "mid")
st.add("carriage", box(-24, 24, -6, 58, 0, 34).merge(disc(13, -10, 0)), "mid")
st.add("shaft", rod((0, 0, -SHAFT), (0, 0, -10), 3.0), "steel")
# split vessel: base clamp, lower glass, splitting ring, upper glass extension
st.add("vbase", lathe([(0, Z_SEAT), (19, Z_SEAT), (19, Z_SEAT + 9), (R_GL + 0.3, Z_SEAT + 9),
                       (R_GL + 0.3, Z_FLOOR), (0, Z_FLOOR)]), "steel")
st.add("glass_lo", lathe([(R_IN, Z_FLOOR), (R_GL, Z_FLOOR), (R_GL, Z_SPLIT), (R_IN, Z_SPLIT)]), "glass")
st.add("splitring", lathe([(R_IN, Z_SPLIT), (18, Z_SPLIT), (18, Z_EXT0), (R_IN, Z_EXT0)]), "steel_dark")
st.add("glass_hi", lathe([(R_IN, Z_EXT0), (R_GL, Z_EXT0), (R_GL, Z_EXT1), (R_IN, Z_EXT1)]), "glass")
st.add("tab", box(17, 30, -3, 3, Z_SPLIT, Z_EXT0), "steel_dark")   # handle used to turn the split ring
st.shadow("sh_base", (0, 15), 150, 110, 0.35)


# tools, built with the coupling at z = 0 (they hang below the spindle tip)
def blade_tool():
    m = disc(3.2, -9, 0)
    for sgn in (1, -1):
        b = box(0, 11.75, -3.0, 3.0, -0.45, 0.45).transform(matrix(rot_deg=sgn * 28, axis=(1, 0, 0)),
                                                            inplace=False)
        if sgn < 0:
            b = b.transform(matrix(rot_deg=180), inplace=False)
        m = m.merge(b.translate((0, 0, -8), inplace=False))
    return m


def piston_tool():
    body = disc(3.2, -10, 0).merge(disc(12.25, -16, -10))
    vent = disc(0.9, -10.05, -9.9)
    for a in np.radians(np.arange(0, 360, 30)):
        vent = vent.merge(disc(0.9, -10.05, -9.9).translate((6.2 * math.cos(a), 6.2 * math.sin(a), 0),
                                                            inplace=False))
    return body, vent, disc(12.2, -16.12, -15.98)


def shear_head():
    body = disc(3.2, -10, 0).merge(disc(12.0, -16, -10))
    blades = None
    for a in np.arange(0, 360, 20):
        b = box(1.6, 11.8, -0.32, 0.32, -18.2, -16).transform(matrix(rot_deg=a), inplace=False)
        blades = b if blades is None else blades.merge(b)
    return body, blades, box(7, 11, -1.0, 1.0, -9.95, -9.6)


st.add("t_blade", blade_tool(), "steel")
p_body, p_vent, p_mesh = piston_tool()
st.add("t_piston", p_body, "steel")
st.add("t_vent", p_vent, "dark")
st.add("t_mesh", p_mesh, "dark")
h_body, h_blades, h_mark = shear_head()
st.add("t_head", h_body, "steel")
st.add("t_hblades", h_blades, "steel_dark")
st.add("t_hmark", h_mark, "orange")
AIR = None
for a in np.radians(np.arange(0, 360, 60)):
    arw = pv.Arrow(start=(6.2 * math.cos(a), 6.2 * math.sin(a), 0), direction=(0, 0, 1), scale=6.0,
                   tip_length=0.35, tip_radius=0.16, shaft_radius=0.06)
    AIR = arw if AIR is None else AIR.merge(arw)
st.add("air", AIR, "blue", color="#6fb6ff", opacity=0.85)

rng = np.random.default_rng(11)
N_WALL = 1400
W_TH = rng.uniform(0, 2 * np.pi, N_WALL)
W_U = rng.uniform(0, 1, N_WALL)          # height fraction in the poured column
W_COL = grain_colors(N_WALL, POWDER, 0.13, seed=12)
N_TOP = 450
T_R = np.sqrt(rng.uniform(0, 1, N_TOP)) * (R_BED - 0.3)
T_TH = rng.uniform(0, 2 * np.pi, N_TOP)
T_COL = grain_colors(N_TOP, POWDER, 0.13, seed=13)
N_FACE = 700                              # grains on the two section faces
F_R = rng.uniform(0.3, R_BED - 0.2, N_FACE)
F_U = rng.uniform(0, 1, N_FACE)
F_A = np.radians(np.where(rng.random(N_FACE) < 0.5, CUT[0], CUT[1]))
F_COL = grain_colors(N_FACE, POWDER, 0.13, seed=14)
ORANGE = hex_rgb(C["orange"])
chart = Chart()
_LF = font(15, bold=True)


def in_section(th):
    """True where the bed is kept (outside the removed wedge)."""
    d = (np.degrees(th) - CUT[0]) % 360.0
    return d <= (CUT[1] - CUT[0]) + 1e-6


# --------------------------------------------------------------------------- timeline helpers
def bed_top(t):
    """Level of the bed surface (before splitting: the column in the whole split vessel)."""
    if t < 4.9:
        return Z_FLOOR
    if t < 6.6:
        return Z_FLOOR + (Z_FILL - Z_FLOOR) * lin(t, 4.9, 6.6)
    if t < 7.2:
        return Z_FILL
    if t < 10.0:
        return Z_FILL + (Z_COND - Z_FILL) * ramp(t, 7.2, 9.8)
    if t < 13.2:
        return Z_COND + (Z_CONS - Z_COND) * ramp(t, 11.0, 12.4)
    return Z_CONS if t < 13.9 else Z_SPLIT


def mound(t):
    """Height of the central mound left by pouring, flattened by conditioning."""
    return 3.0 * ramp(t, 5.4, 6.6) * (1 - ramp(t, 7.4, 9.6))


def grain_z(u, t, top):
    """Grains keep their place in the bed: laid down as it fills, squeezed with it."""
    z_fill = Z_FLOOR + 0.4 + u * (Z_FILL - Z_FLOOR - 0.8)
    if t < 6.6:
        return z_fill
    h = (min(top, Z_FILL) if t < 13.3 else Z_CONS) - Z_FLOOR
    return Z_FLOOR + (z_fill - Z_FLOOR) * h / (Z_FILL - Z_FLOOR)


def tool_pose(t):
    """(tool name, coupling z, spin deg) — the carriage follows the coupling."""
    hi = 230.0
    if t < 7.0:
        return None, 300.0, 0.0
    if t < 10.2:  # conditioning blade: down along a helix, then back up
        lo = Z_FLOOR + 3.0
        z_tip = hi - (hi - lo) * ramp(t, 7.0, 8.7) + (hi - lo) * ramp(t, 8.8, 10.15)
        return "blade", z_tip + 8.0, 900.0 * (t - 7.0)
    if t < 13.2:  # vented piston
        z_face = hi - (hi - Z_COND) * ramp(t, 10.2, 11.0)
        if t >= 11.0:
            z_face = bed_top(t)
        z_face += (hi - Z_CONS) * ramp(t, 12.6, 13.2)
        return "piston", z_face + 16.0, 0.0
    if t < 15.2:
        return None, 300.0, 0.0
    z_tips = hi - (hi - (Z_SPLIT - 2.0)) * ramp(t, 15.2, 16.4) + dilation(t)
    if t >= T_SH1:
        z_tips = Z_SPLIT - 2.0 + (hi - Z_SPLIT) * ramp(t, 26.8, 28.0)
    return "head", z_tips + 18.2, head_turn(t)


def split_motion(t):
    s_rot = ramp(t, 13.3, 14.0)
    s_up = ramp(t, 14.0, 14.9)
    return matrix(translate=(70 * s_up, 0, 80 * s_up)) @ matrix(rot_deg=70 * s_rot), s_up


def frame(t):
    i_step, step = TL.current(t)
    labels, readouts = [], []

    # ---- assembly
    for nm, t0, off in (("base", 0.1, (0, 0, -60)), ("panel", 0.1, (0, 0, -60)), ("led", 0.1, (0, 0, -60)),
                        ("plate", 0.5, (0, 0, 60)), ("loadcell", 0.5, (0, 0, 60)),
                        ("tower", 0.9, (0, 160, 0)), ("rail", 0.9, (0, 160, 0)), ("topcap", 0.9, (0, 160, 0)),
                        ("vbase", 1.8, (0, 0, 120)), ("glass_lo", 2.3, (0, 0, 140)),
                        ("splitring", 2.8, (0, 0, 150)), ("tab", 2.8, (0, 0, 150)), ("glass_hi", 3.2, (0, 0, 160))):
        M, vis, _ = arrive(t, t0, offset=off)
        st.pose(nm, M, vis)
    Ms, s_up = split_motion(t)
    if t >= 13.3:
        for nm in ("splitring", "tab"):
            st.pose(nm, Ms, s_up < 0.999)
        st.pose("glass_hi", Ms, s_up < 0.999, opacity=0.28 * (1 - 0.8 * s_up))

    # ---- tools and carriage
    tool, z_c, spin = tool_pose(t)
    carr_in = arrive(t, 1.3, offset=(0, 0, 200))
    z_carr = z_c + SHAFT if t >= 4.6 else 300.0 + SHAFT
    st.pose("carriage", matrix(translate=(0, 0, z_carr)) @ carr_in[0], carr_in[1])
    st.pose("shaft", matrix(translate=(0, 0, z_carr)) @ carr_in[0], carr_in[1])
    for nm in ("t_blade", "t_piston", "t_vent", "t_mesh", "t_head", "t_hblades", "t_hmark", "air"):
        st.pose(nm, None, False)
    if tool == "blade":
        st.pose("t_blade", matrix(translate=(0, 0, z_c)) @ matrix(rot_deg=spin), True)
    elif tool == "piston":
        for nm in ("t_piston", "t_vent", "t_mesh"):
            st.pose(nm, matrix(translate=(0, 0, z_c)), True)
        if 11.0 <= t <= 12.5:
            rise = ((t - 11.0) * 14.0) % 5.0
            st.pose("air", matrix(translate=(0, 0, z_c - 10 + 0.5 + rise)), True,
                    opacity=0.85 * (1 - rise / 5.0))
    elif tool == "head":
        for nm in ("t_head", "t_hblades", "t_hmark"):
            st.pose(nm, matrix(translate=(0, 0, z_c)) @ matrix(rot_deg=spin), True)

    # ---- powder bed: sectioned so the tools inside it show
    top = bed_top(t)
    md = mound(t)
    head_in = tool == "head" and t >= 16.0
    shearing = T_SH0 <= t < T_SH1
    if top > Z_FLOOR + 0.2:
        if 13.3 <= t < 13.9 or t >= 13.9:
            prof = [(0, Z_FLOOR + 0.05), (R_BED, Z_FLOOR + 0.05), (R_BED, Z_SPLIT), (0, Z_SPLIT)]
        else:
            rr = np.linspace(R_BED, 0, 15)
            prof = [(0, Z_FLOOR + 0.05), (R_BED, Z_FLOOR + 0.05)] + [(r, top + md * (1 - r / R_BED)) for r in rr]
        conditioning = 7.0 <= t <= 10.15
        st.add("bed", lathe(prof, a0=CUT[0], a1=CUT[1]), "powder", color=POWDER,
               opacity=0.55 if conditioning else 1.0)
        if 13.3 <= t < 15.0:   # the excess above the split line travels with the upper section
            ex = lathe([(0, Z_SPLIT), (R_BED, Z_SPLIT), (R_BED, Z_CONS), (0, Z_CONS)], a0=CUT[0], a1=CUT[1])
            st.add("excess", ex, "powder", color=POWDER, opacity=1 - 0.85 * s_up)
            st.pose("excess", Ms)
        else:
            st.remove("excess")
    else:
        st.remove("bed")
        st.remove("excess")

    if top > Z_FLOOR + 0.5:
        zcap = Z_SPLIT - 0.25 if t >= 13.3 else top - 0.2
        # wall grains (seen through the glass); the top layer turns with the shear head
        z = grain_z(W_U, t, top)
        th = W_TH.copy()
        if head_in:
            dz = Z_SPLIT - z
            th = th + np.radians(head_turn(t)) * np.clip(1 - dz / 2.6, 0, 1) ** 1.5
            z = z + dilation(t) * np.clip(1 - dz / 4.0, 0, 1)
        keep = (z <= zcap) & in_section(th)
        r = np.full(N_WALL, R_BED + 0.12)
        st.grains("wall", np.c_[r * np.cos(th), r * np.sin(th), z][keep], W_COL[keep], size=3.0)
        # grains on the section faces; the shear band under the blades lights up while shearing
        zf = grain_z(F_U, t, top)
        keepf = zf <= zcap
        Pf = np.c_[F_R * np.cos(F_A), F_R * np.sin(F_A), zf]
        nrm = np.c_[-np.sin(F_A), np.cos(F_A), 0 * F_A] * np.where(F_A == np.radians(CUT[0]), -1, 1)[:, None]
        Pf = Pf + 0.12 * nrm
        cols = F_COL.astype(float)
        if shearing or (T_SH1 <= t < T_SH1 + 1.0):
            band = np.clip(1 - np.abs(zf - (Z_SPLIT - 3.0)) / 1.3, 0, 1) * (1 - ramp(t, T_SH1, T_SH1 + 1.0))
            cols = cols * (1 - 0.8 * band[:, None]) + ORANGE[None, :] * 0.8 * band[:, None]
        st.grains("face", Pf[keepf], cols.astype(np.uint8)[keepf], size=3.0)
        if tool is None or tool == "blade" or (tool == "piston" and t < 10.9):
            zt = top + md * (1 - T_R / R_BED) + 0.12
            kt = in_section(T_TH)
            st.grains("topg", np.c_[T_R * np.cos(T_TH), T_R * np.sin(T_TH), zt][kt], T_COL[kt], size=3.0)
        else:
            st.remove("topg")
    else:
        for nm in ("wall", "face", "topg"):
            st.remove(nm)

    # helical path of the blade tip while conditioning
    if tool == "blade":
        tt = np.linspace(max(7.0, t - 0.6), t, 60)
        pts = []
        for tq in tt:
            _, zc_q, sp_q = tool_pose(tq)
            a = math.radians(sp_q)
            pts.append((11.6 * math.cos(a), 11.6 * math.sin(a), zc_q - 8.0))
        pts = np.asarray(pts)
        pts = pts[pts[:, 2] < Z_EXT1 - 1.0]
        if len(pts) > 2:
            st.add("trail", pv.lines_from_points(pts), "orange", line_width=3, render_lines_as_tubes=True,
                   opacity=0.9)
        else:
            st.remove("trail")
    else:
        st.remove("trail")

    # shear zone: a band just under the blade tips, drawn on both section faces
    if shearing or (T_SH1 <= t < T_SH1 + 1.0):
        i_, kind_, _, s_ = seg_at(min(t, T_SH1 - 1e-6))
        z0, z1 = Z_SPLIT - 4.3, Z_SPLIT - 2.0
        quads = None
        for a_deg, sgn in ((CUT[0], -1), (CUT[1], 1)):
            a = math.radians(a_deg)
            u = np.array([math.cos(a), math.sin(a), 0.0])
            n = sgn * np.array([-math.sin(a), math.cos(a), 0.0]) * 0.18
            q = pv.PolyData(np.array([n + 0.3 * u + (0, 0, z0), n + R_BED * u + (0, 0, z0),
                                      n + R_BED * u + (0, 0, z1), n + 0.3 * u + (0, 0, z1)]), [4, 0, 1, 2, 3])
            quads = q if quads is None else quads.merge(q)
        live = 0.35 + 0.35 * min(1.0, tau_in_seg(i_, s_) / TAU_PRE)
        st.add("band", quads, "orange", opacity=live * (1 - ramp(t, T_SH1, T_SH1 + 1.0)), lighting=False)
    else:
        st.remove("band")

    if 4.85 <= t <= 6.8:   # pour stream
        p, _ = stream(t, 4.9, 6.55, 900, (0, -2, 175), 1.6, v0=60, floor=lambda x, y: top + md + 0 * x, seed=21)
        st.grains("pour", p, W_COL[: len(p)] if len(p) <= N_WALL else None, size=3.0)
    else:
        st.remove("pour")

    # ---- camera: wide for the assembly, close on the vessel for the test, back out for the result
    zoom = ramp(t, 4.0, 6.4)
    dist = 1000 - (1000 - 240) * zoom - 45 * ramp(t, 14.6, 16.4) + 90 * ramp(t, 26.8, 28.6)
    focal = lerp((0, 30, 210), (0, 0, 100), zoom) + np.array([0, 0, -12]) * ramp(t, 14.6, 16.4)
    az = -34 + 14 * ramp(t, 0, 5) + 22 * ramp(t, 7, 28)
    el = 18 + 7 * zoom - 13 * ramp(t, 15.2, 16.8) + 11 * ramp(t, 26.8, 28.6)
    st.orbit(focal, dist, az, el)
    st.pl.camera.SetWindowCenter(0.30, 0.0)
    rgb = st.render()

    # ---- labels: placed on whichever side keeps the box clear of the chart and frame edge
    def lab(text, xyz, dy, t0, t1, side=None):
        a = ramp(t, t0, t0 + 0.4) * (1 - ramp(t, t1 - 0.4, t1))
        if a <= 0:
            return
        ax_, _ = st.project(xyz)
        w = _LF.getlength(text) + 16
        left_ok = ax_ - 50 - w > 12
        right_ok = ax_ + 50 + w < W - 515
        go_left = left_ok if side is None else (side == "left")
        if not go_left and not right_ok and left_ok:
            go_left = True
        labels.append(Label(text, xyz, (-50 if go_left else 50, dy), a))
    lab("Vessel seat on a load cell", (-24, -10, Z_SEAT), 60, 0.8, 4.4)
    lab("Drive tower: vertical + rotation", (-55, 62, 330), -30, 1.3, 4.4)
    lab("Split vessel, 25 mm bore", (-R_GL, -2, 110), -40, 3.4, 6.6, "left")
    lab("Conditioning blade, 23.5 mm", (-11, -4, 128), -50, 7.4, 9.9, "left")
    lab("Vented piston: air escapes", (-12, -4, Z_COND + 3), -50, 10.4, 13.0, "left")
    lab("Upper section turns and lifts off", (18, 0, Z_EXT0 + 2), -60, 13.4, 15.1, "right")
    lab("Level 10 mL bed", (-R_GL, -2, Z_SPLIT), 40, 14.4, 16.4, "left")
    lab("Bladed shear head, 24 mm", (-12, -3, Z_SPLIT + 4), -55, 15.4, 18.6, "left")
    lab("Shear zone under the blades", (-R_BED * 0.6, -R_BED * 0.8, Z_SPLIT - 3.0), 55, 18.6, 25.0, "left")

    # ---- readouts
    if 10.2 <= t < 13.2:
        sig_now = SIG_PRE * ramp(t, 11.0, 12.4) * (1 - ramp(t, 12.5, 12.8))
        readouts.append(Readout("NORMAL STRESS σ", f"{sig_now:4.1f} kPa"))
    if shearing:
        i, kind, _, s = seg_at(t)
        readouts.append(Readout("NORMAL STRESS σ", f"{sigma_in_seg(i, s):4.1f} kPa"))
        readouts.append(Readout("SHEAR STRESS τ", f"{tau_in_seg(i, s):4.2f} kPa", "#FFD166"))
        readouts.append(Readout("STEP", "pre-shear" if kind == "pre" else "shear", "#9ad0ff"))
    if t >= 27.6:
        readouts.append(Readout("σc (UYS)", f"{SIG_C:4.2f} kPa"))
    if t >= 28.4:
        readouts.append(Readout("σ1 (MPS)", f"{SIG_1:4.1f} kPa"))
    if t >= 29.2:
        readouts.append(Readout("ffc = σ1/σc", f"{FFC:3.1f}  {ffc_class(FFC)}", "#FFD166"))

    # ---- chart: test programme, then the live trace, then the yield locus
    def programme(fig):
        ax = fig.add_axes([0.03, 0.03, 0.94, 0.94])
        ax.axis("off")
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.text(0.03, 0.93, "Shear test (example: 9 kPa pre-shear)", fontsize=11, fontweight="bold", color="#222")
        rows = [("1", "Condition: blade, helical path", 7.0),
                ("2", "Consolidate: vented piston to 9 kPa", 10.2),
                ("3", "Split: level 10 mL bed", 13.2),
                ("4", "Shear head into the bed", 15.2),
                ("5", "Pre-shear at 9 kPa to steady state", 16.6),
                ("6", "Shear to failure at e.g. 7, 6, 5, 4, 3 kPa", 16.6),
                ("", "   (pre-shear again before each step)", 16.6),
                ("7", "Fit yield locus, Mohr circles → ffc", 26.6)]
        cur = max([r[2] for r in rows if r[2] <= t], default=-1)
        for k, (n_, txt, t_on) in enumerate(rows):
            y = 0.80 - k * 0.105
            col = "#e07a1f" if t_on == cur else ("#333" if t_on < cur else "#9aa1a9")
            ax.text(0.05, y, n_, fontsize=10, fontweight="bold", color=col)
            ax.text(0.12, y, txt, fontsize=10, color=col)

    def trace(fig):
        ax = fig.add_axes([0.12, 0.2, 0.84, 0.66])
        style_axes(ax, "Shear stress τ and normal stress σ")
        u_now = (min(t, T_SH1) - T_SH0) / SEG_T
        xs, ts, ss = [], [], []
        for i in range(len(SEGS)):
            if i > u_now:
                break
            for s in np.linspace(0, min(1.0, u_now - i), 40):
                xs.append(i + s)
                ts.append(tau_in_seg(i, s))
                ss.append(sigma_in_seg(i, s))
        ax.plot(xs, ss, color="#8a929b", lw=1.6, ls="--", label="σ (set)")
        ax.plot(xs, ts, color=C["blue"], lw=2.2, label="τ (measured)")
        for j in range(len(SIG_SH)):
            if u_now >= 1 + 2 * j + 0.55:
                ax.plot([1 + 2 * j + 0.55], [TAU_F[j]], "o", color=C["orange"], ms=5)
        ax.set_xlim(0, len(SEGS))
        ax.set_ylim(0, 10)
        ax.set_xticks([1.5 + 2 * j for j in range(len(SIG_SH))])
        ax.set_xticklabels([f"{s:g}" for s in SIG_SH])
        ax.set_xlabel("shear steps at σ (kPa); pre-shear at 9 kPa between them")
        ax.set_ylabel("stress (kPa)")
        ax.legend(fontsize=8, loc="upper right", frameon=False, ncol=2)

    if t < T_SH0 - 0.4:
        img = chart.draw(programme)
    elif t < T_SH1 + 0.6:
        img = chart.draw(trace)
    else:
        img = chart.draw(lambda fig: locus_chart(fig, t - (T_SH1 + 0.6), SIG_SH, TAU_F, SIG_PRE, TAU_PRE))
    ov = Overlay("FT4 shear cell", "Shear strength of a consolidated bed → flow function ffc",
                 "ASTM D7891-24", labels=labels, readouts=readouts, chart=img,
                 step_idx=i_step, n_steps=len(TL.steps), step_text=step.text,
                 speed_note="test time compressed" if shearing else "",
                 footer="Schematic; dimensions approximate; values illustrative", readout_row_px=560)
    return compose(rgb, ov, st)


if __name__ == "__main__":
    run(frame, NAME, TL.duration)
