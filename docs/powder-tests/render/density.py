"""Apparent density (ASTM B212) and tap density (ASTM B527): the Hausner ratio.

B212: a Hall funnel held concentric with a 25 cm3 brass density cup, orifice about 25 mm
above the cup rim, fills the cup until it overflows; the funnel is moved aside, the heap is
struck off level with the rim without jarring the cup, and the powder is weighed:
apparent density = mass / cup volume.
B527: a weighed sample in a graduated cylinder is tapped (a cam lifts the cylinder a few
millimetres and drops it onto an anvil) until the volume stops falling:
tap density = mass / tapped volume. Hausner ratio = tap / apparent density.
Values are illustrative for a free-flowing gas-atomized 316L powder.
"""
from common import *  # noqa: F401,F403

NAME = "density"
AD = 4.42e-3                  # g/mm^3, apparent density (illustrative)
TD = 5.02e-3                  # g/mm^3, tap density (illustrative)
TAN_T = math.tan(math.radians(31))
CUT = (-55.0, 235.0)          # cutaway wedge faces the camera (camera on -y)
POWDER = "#7c838b"

# ---- B212 geometry: stand, tray, 25 cm3 cup, Hall funnel 25 mm above the rim
Z_BASE = 14.0
TRAY_R, TRAY_FLOOR, TRAY_H = 52.0, Z_BASE + 1.5, 10.0
CUP_RI, CUP_RO = 14.0, 17.0
CUP_V = 25000.0
CUP_DEPTH = CUP_V / (math.pi * CUP_RI ** 2)          # 40.6 mm
Z_CUP0 = TRAY_FLOOR                                  # cup outer base
Z_CUPF = Z_CUP0 + 4.0                                # inner floor
Z_RIM = Z_CUPF + CUP_DEPTH
Z_O = Z_RIM + 25.0
PROF, FG = funnel_geom(Z_O, 1.27)
COL = np.array([-80.0, 45.0])                        # column axis (x, y)
RING_Z = FG["z_ct"] - 7.0
V_MOUND = math.pi / 3 * CUP_RI ** 2 * (CUP_RI * TAN_T)
V_POUR = 140.0 / AD                                  # 140 g loaded into the funnel
T_FLOW = 140.0 / 50.0 * 15.8                         # s, illustrative Hall rate
T_REL, T_EMPTY = 5.0, 9.4                            # release and last grain (animation time)
FLOW_SPEED = T_FLOW / (T_EMPTY - T_REL)

# ---- balance (to the right of the stand)
BAL = np.array([150.0, -32.0])
BAL_PAN_Z = 36.0

# ---- B527 geometry: tap-density tester and 25 mL graduated cylinder
TB_TOP = 55.0                                        # top of the tester base
ANVIL_TOP = TB_TOP + 5.0
CYL_FOOT0 = ANVIL_TOP + 6.0                          # cylinder foot bottom (resting)
CYL_RI, CYL_RO = 8.5, 10.0
CYL_FLOOR = CYL_FOOT0 + 8.0
ML_MM = 1000.0 / (math.pi * CYL_RI ** 2)             # mm of column per mL
CYL_TOP = CYL_FLOOR + 25 * ML_MM + 18.0
MASS_B = 100.0                                       # g in the cylinder
V0 = MASS_B / AD / 1000.0                            # 22.6 mL loose
VT = MASS_B / TD / 1000.0                            # 19.9 mL tapped
KAW_A, KAW_B = 1.0 - VT / V0, 0.05
DROP = 3.0                                           # mm
T_TAP0, T_TAP1 = 17.8, 24.2
N_MAX = 3000

TL = Timeline([
    Step(0.0, 3.2, "Assemble: levelled stand, Hall funnel 25 mm above a 25 cm³ cup"),
    Step(3.2, 5.0, "Block the orifice and load the funnel with powder"),
    Step(5.0, 9.6, "Release: powder fills the cup and overflows into the tray"),
    Step(9.6, 10.8, "Swing the funnel aside without jarring the cup"),
    Step(10.8, 12.7, "Strike off the heap: one pass of a spatula, blade upright"),
    Step(12.7, 15.0, "Weigh the powder: apparent density = mass ÷ 25 cm³"),
    Step(15.0, 17.8, "Tap density: weighed sample into a 25 mL graduated cylinder"),
    Step(17.8, 24.4, "A cam lifts the cylinder and drops it on the anvil, over and over"),
    Step(24.4, 28.5, "Hausner = TD/AD = 1.14 (above ~1.25 suggests a cohesive powder)"),
])

st = Stage()


def lines_mesh(segs):
    """Polyline segments [(p0, p1, ...), ...] -> PolyData of lines."""
    pts, cells = [], []
    for s in segs:
        s = np.asarray(s, float)
        cells.append(np.r_[len(s), np.arange(len(pts), len(pts) + len(s))])
        pts.extend(s.tolist())
    return pv.PolyData(np.asarray(pts), lines=np.concatenate(cells))


# ---------------------------------------------------------------- B212 parts
st.add("base", disc(98, 4, Z_BASE).translate((-22, 14, 0), inplace=False), "dark")
for k, a in enumerate((60, 180, 300)):
    x, y = -22 + 84 * math.cos(math.radians(a)), 14 + 84 * math.sin(math.radians(a))
    st.add(f"foot{k}", disc(7, 0, 4).translate((x, y, 0), inplace=False), "rubber")
st.add("level", disc(6, Z_BASE, Z_BASE + 3).translate((-62, -40, 0), inplace=False), "glass", opacity=0.6,
       color="#9be39b")
st.add("column", rod((COL[0], COL[1], Z_BASE), (COL[0], COL[1], RING_Z + 40), 7), "steel")
d_arm = -COL / np.linalg.norm(COL)
arm_end = -d_arm * (FG["r_lip"] + 6.0)
st.add("collar", tube(7.0, 12.0, RING_Z - 2, RING_Z + 10).translate((COL[0], COL[1], 0), inplace=False), "steel_dark")
st.add("arm", rod((COL[0], COL[1], RING_Z + 3), (arm_end[0], arm_end[1], RING_Z + 3), 4.5), "steel_dark")
st.add("ring", tube(FG["r_lip"] - 2.0, FG["r_lip"] + 6.0, RING_Z, FG["z_ct"] - 1.0), "steel_dark")
st.add("funnel", lathe(PROF, a0=CUT[0], a1=CUT[1]), "steel")
st.add("tray", lathe([(0, Z_BASE), (TRAY_R + 2, Z_BASE), (TRAY_R + 2, Z_BASE + TRAY_H), (TRAY_R, Z_BASE + TRAY_H),
                      (TRAY_R, TRAY_FLOOR), (0, TRAY_FLOOR)], a0=CUT[0], a1=CUT[1]), "steel")
st.add("cup", lathe([(0, Z_CUP0), (CUP_RO, Z_CUP0), (CUP_RO, Z_RIM), (CUP_RI, Z_RIM), (CUP_RI, Z_CUPF), (0, Z_CUPF)],
                    a0=CUT[0], a1=CUT[1]), "brass")
st.add("finger", rod((-58, -12, Z_O - 13), (0, 0, Z_O - 7.5), 7.5).merge(pv.Sphere(radius=7.5, center=(0, 0, Z_O - 7.5))),
       "blue", color="#5b8fd6")
st.add("pan", lathe([(0, 0), (26, 0), (30, 8), (28.6, 8), (24.8, 1.4), (0, 1.4)]), "alu")
blade = box(-0.6, 0.6, -24, 24, 0, 20).merge(box(-2.5, 2.5, -10, 10, 20, 70))
st.add("spatula", blade, "steel")
# balance
st.add("bal_body", box(BAL[0] - 55, BAL[0] + 55, BAL[1] - 62, BAL[1] + 62, 0, 30), "light")
st.add("bal_lcd", box(BAL[0] - 40, BAL[0] + 40, BAL[1] - 63, BAL[1] - 61.5, 8, 24), "lcd")
st.add("bal_post", rod((BAL[0], BAL[1] + 4, 30), (BAL[0], BAL[1] + 4, BAL_PAN_Z - 2), 5), "steel_dark")
st.add("bal_pan", disc(40, BAL_PAN_Z - 2, BAL_PAN_Z).translate((BAL[0], BAL[1] + 4, 0), inplace=False), "steel")
st.shadow("sh_base", (-22, 14), 125, 115, 0.30)
st.shadow("sh_bal", (BAL[0], BAL[1]), 78, 82, 0.28)

# ---------------------------------------------------------------- B527 parts (tap-density tester)
tb = []
tb.append(box(-75, 75, -60, 60, 0, 6))                          # bottom
tb.append(box(-75, 75, -60, 60, TB_TOP - 6, TB_TOP))            # top deck
tb.append(box(-75, 75, 54, 60, 6, TB_TOP - 6))                  # back
tb.append(box(-75, -69, -60, 54, 6, TB_TOP - 6))                # left
tb.append(box(69, 75, -60, 54, 6, TB_TOP - 6))                  # right
tb.append(box(-69, -26, -60, -54, 6, TB_TOP - 6))               # front, left of window
tb.append(box(26, 69, -60, -54, 6, TB_TOP - 6))                 # front, right of window
tb.append(box(-26, 26, -60, -54, 6, 12))                        # under window
tb.append(box(-26, 26, -60, -54, TB_TOP - 12, TB_TOP - 6))      # over window
tester = tb[0]
for m in tb[1:]:
    tester = tester.merge(m)
st.add("tester", tester, "mid")
st.add("tester_win", box(-26, 26, -58.5, -57.5, 12, TB_TOP - 12), "glass", opacity=0.18)
st.add("tester_lcd", box(36, 64, -60.8, -59.8, 26, 42), "lcd")
st.add("anvil", disc(30, TB_TOP, ANVIL_TOP), "steel")
st.add("guide", rod((0, 46, ANVIL_TOP), (0, 46, CYL_TOP + 8), 6), "steel")
st.add("clampA", rod((0, 46, CYL_FLOOR + 30), (0, CYL_RO + 3.5, CYL_FLOOR + 30), 3.2).merge(
    tube(CYL_RO + 1.5, CYL_RO + 5, CYL_FLOOR + 26, CYL_FLOOR + 34)), "steel_dark")
st.add("clampB", rod((0, 46, CYL_TOP - 30), (0, CYL_RO + 3.5, CYL_TOP - 30), 3.2).merge(
    tube(CYL_RO + 1.5, CYL_RO + 5, CYL_TOP - 34, CYL_TOP - 26)), "steel_dark")
# cam (inside the window), follower and platform move each frame
cam_disc = pv.Cylinder(center=(0, 0, 0), direction=(0, 1, 0), radius=9, height=8, resolution=48).triangulate()
st.add("cam", cam_disc.compute_normals(split_vertices=True, feature_angle=40), "orange")
st.add("cam_axle", rod((0, -51, 24), (0, 40, 24), 2.2), "steel_dark")
st.add("follower", rod((0, -44, 0), (0, -44, 1), 3.0), "steel")
st.add("platform", disc(24, ANVIL_TOP, CYL_FOOT0), "steel_dark")
# graduated cylinder (glass), foot and graduation marks, in the cylinder frame
st.add("cyl_foot", disc(19, CYL_FOOT0, CYL_FOOT0 + 6), "glass", opacity=0.55, color="#d7ebfb")
st.add("cyl_glass", lathe([(0, CYL_FOOT0 + 6), (CYL_RO, CYL_FOOT0 + 6), (CYL_RO, CYL_TOP), (CYL_RO + 1.6, CYL_TOP + 1.5),
                           (CYL_RI, CYL_TOP + 1.5), (CYL_RI, CYL_FLOOR), (0, CYL_FLOOR)]), "glass")
segs = []
for k in range(0, 26):
    z = CYL_FLOOR + k * ML_MM
    half = 34 if k % 5 == 0 else 16
    th = np.radians(np.linspace(-90 - half, -90 + half, 9))
    segs.append(np.c_[(CYL_RO + 0.08) * np.cos(th), (CYL_RO + 0.08) * np.sin(th), np.full(9, z)])
grad = lines_mesh(segs)
st.pl.add_mesh(grad, name="cyl_grad", color="#1f2a44", line_width=1.6, lighting=False)
st.names.add("cyl_grad")
st.shadow("sh_tester", (0, 0), 95, 80, 0.30)

B212_PARTS = ["base", "foot0", "foot1", "foot2", "level", "column", "collar", "arm", "ring", "funnel", "tray", "cup",
              "bal_body", "bal_lcd", "bal_post", "bal_pan", "sh_base", "sh_bal"]
TAP_PARTS = ["tester", "tester_win", "tester_lcd", "anvil", "guide", "clampA", "clampB", "cam", "cam_axle", "follower",
             "platform", "cyl_foot", "cyl_glass", "cyl_grad", "sh_tester"]
SWING = ["collar", "arm", "ring", "funnel"]

COLS = grain_colors(8000, POWDER, 0.12, seed=11)
rng = np.random.default_rng(5)
SIDE_U = rng.random(700)                               # grains seen through the cylinder wall
SIDE_TH = np.radians(rng.uniform(-150, -30, 700))
chart = Chart()


# ---------------------------------------------------------------- helpers
def tray_heap(V):
    """Annular overflow heap around the cup in the tray: (L, h_wall) for volume V (mm^3)."""
    if V <= 1.0:
        return 0.0, 0.0
    lo, hi = 0.0, TRAY_R - CUP_RO
    for _ in range(40):
        L = 0.5 * (lo + hi)
        v = 2 * math.pi * TAN_T * (CUP_RO * L ** 2 / 2 + L ** 3 / 6)
        lo, hi = (L, hi) if v < V else (lo, L)
    return L, L * TAN_T


def kawakita(n):
    return V0 * (1 - KAW_A * KAW_B * n / (1 + KAW_B * n))


def taps_at(t):
    s = lin(t, T_TAP0, T_TAP1)
    return 0 if s <= 0 else int(round(10 ** (s * math.log10(N_MAX + 1)) - 1))


def cup_matrix(t):
    """Cup carried from the stand to the balance between 12.9 s and 14.1 s."""
    s1, s2, s3 = ramp(t, 12.8, 13.25), ramp(t, 13.2, 13.8), ramp(t, 13.75, 14.15)
    dz = 70 * s1 - 70 * s3
    xy = np.array([BAL[0], BAL[1] + 4]) * s2
    z_rest = (BAL_PAN_Z - Z_CUP0) * s3
    return matrix(translate=(xy[0], xy[1], dz + z_rest))


def frame(t):
    i, step = TL.current(t)
    labels, readouts = [], []
    a0, a1 = CUT

    # ---- part A assembly, then everything slides out for part B
    gone = ramp(t, 14.9, 15.6)
    for nm, t0, off in (("base", 0.1, (0, 0, 70)), ("column", 0.4, (0, 0, 120)), ("collar", 0.7, (0, 0, 90)),
                        ("arm", 0.7, (0, 0, 90)), ("ring", 0.7, (0, 0, 90)), ("funnel", 1.2, (0, 0, 120)),
                        ("tray", 1.7, (-150, 0, 0)), ("cup", 2.2, (0, -130, 45)), ("bal_body", 2.0, (160, 0, 0)),
                        ("bal_lcd", 2.0, (160, 0, 0)), ("bal_post", 2.0, (160, 0, 0)), ("bal_pan", 2.0, (160, 0, 0))):
        M, vis, _ = arrive(t, t0, offset=off)
        st.pose(nm, matrix(translate=(-420 * gone, 0, 0)) @ M, vis and gone < 0.99)
    for nm in ("foot0", "foot1", "foot2", "level"):
        st.pose(nm, matrix(translate=(-420 * gone, 0, 0)) @ arrive(t, 0.1, offset=(0, 0, 70))[0], t >= 0.1 and gone < 0.99)
    st.pose("sh_base", matrix(translate=(-420 * gone, 0, 0)), t >= 0.3 and gone < 0.99)
    st.pose("sh_bal", matrix(translate=(-420 * gone, 0, 0)), t >= 2.3 and gone < 0.99)

    # swing arm: rotate about the column after the funnel empties
    phi = 80.0 * ramp(t, 9.7, 10.6)
    M_sw = matrix(rot_deg=phi, origin=(COL[0], COL[1], 0))
    for nm in SWING:
        base_M = arrive(t, {"funnel": 1.2}.get(nm, 0.7), offset=(0, 0, 120 if nm == "funnel" else 90))[0]
        st.pose(nm, matrix(translate=(-420 * gone, 0, 0)) @ M_sw @ base_M,
                t >= (1.2 if nm == "funnel" else 0.7) and gone < 0.99)

    # cup carried to the balance
    M_cup = matrix(translate=(-420 * gone, 0, 0)) @ cup_matrix(t) @ arrive(t, 2.2, offset=(0, -130, 45))[0]
    st.pose("cup", M_cup, t >= 2.2 and gone < 0.99)

    # finger and pan (load the funnel)
    f_in = ramp(t, 3.0, 3.5) * (1 - ramp(t, 4.8, 5.1))
    st.pose("finger", matrix(translate=(-90 * (1 - f_in), -20 * (1 - f_in), 0)), f_in > 0.01)
    s_in, s_out = ramp(t, 3.1, 3.6), ramp(t, 4.7, 5.2)
    tilt = ramp(t, 3.6, 3.9) * (1 - ramp(t, 4.5, 4.75))
    M_pan = matrix(translate=(-40, -6, FG["lip_top"] + 26)) @ matrix(rot_deg=40 * tilt, axis=(0, 1, 0), origin=(26, 0, 6))
    st.pose("pan", matrix(translate=(-170 * (1 - s_in) - 170 * s_out, 0, 0)) @ M_pan, 3.1 <= t <= 5.2)

    # ---- B212 powder: funnel, cup, overflow, strike-off
    loaded = lin(t, 3.65, 4.6)
    released = lin(t, T_REL, T_EMPTY)
    V_f = V_POUR * (loaded - released)
    fill = funnel_fill(V_f, FG, dip=5.0 * released, a0=a0, a1=a1) if t >= 3.65 and gone < 0.99 else None
    if fill is not None:
        st.add("fill", fill, "powder", color=POWDER)
        st.pose("fill", matrix(translate=(-420 * gone, 0, 0)) @ M_sw)
    else:
        st.remove("fill")
    V_rel = V_POUR * released
    V_cup = min(V_rel, CUP_V + V_MOUND)
    V_over = max(0.0, V_rel - CUP_V - V_MOUND)
    apex = heap_apex(V_cup, CUP_RI, TAN_T)            # above the inner floor
    xb = -40 + 80 * lin(t, 11.0, 12.3)                # spatula position along x
    struck = t >= 11.0
    if gone < 0.99 and V_cup > 0:
        if not struck:
            st.add("cup_pow", heap_solid(CUP_RI - 0.05, apex, TAN_T, Z_CUPF, a0=a0, a1=a1), "powder", color=POWDER)
            st.remove("cup_mound")
        else:
            st.add("cup_pow", lathe([(0, Z_CUPF), (CUP_RI - 0.05, Z_CUPF), (CUP_RI - 0.05, Z_RIM - 0.05), (0, Z_RIM - 0.05)],
                                    a0=a0, a1=a1), "powder", color=POWDER)
            mound_h = apex - CUP_DEPTH

            def zf(r, th):
                x = r * np.cos(th)
                return Z_RIM + np.where(x > xb, np.maximum(0.0, mound_h - r * TAN_T), 0.0)
            st.add("cup_mound", polar_surface(zf, CUP_RI - 0.05, nr=24, nth=72, a0=a0, a1=a1), "powder", color=POWDER)
        st.pose("cup_pow", M_cup)
        st.pose("cup_mound", M_cup)
    else:
        st.remove("cup_pow")
        st.remove("cup_mound")
    L, hw = tray_heap(V_over + (V_MOUND * lin(t, 11.0, 12.3) if struck else 0.0))
    if L > 0.2 and gone < 0.99:
        rr = np.linspace(CUP_RO + L, CUP_RO, 16)
        prof = [(CUP_RO, TRAY_FLOOR), (CUP_RO + L, TRAY_FLOOR)] + [(r, TRAY_FLOOR + max(0.05, hw - (r - CUP_RO) * TAN_T))
                                                                    for r in rr]
        st.add("tray_heap", lathe(prof, a0=a0, a1=a1), "powder", color=POWDER)
        st.pose("tray_heap", matrix(translate=(-420 * gone, 0, 0)))
    else:
        st.remove("tray_heap")

    # spatula: one pass across the rim, blade upright
    sp_in = ramp(t, 10.6, 11.0) * (1 - ramp(t, 12.3, 12.7))
    st.pose("spatula", matrix(translate=(xb, 0, Z_RIM + 0.2 + 60 * (1 - sp_in))), 10.6 <= t <= 12.7)

    # ---- grains: load stream, run-out stream, overflow spill, strike-off spill
    pts = []
    if 3.7 <= t <= 4.9:
        lvl = funnel_level(max(V_f, 1.0), FG)
        p, _ = stream(t, 3.7, 4.55, 800, (-12, -6, FG["lip_top"] + 30), 2.2, v0=40,
                      floor=lambda x, y: lvl + 0 * x, seed=21)
        pts.append(p)
    if T_REL <= t <= T_EMPTY + 0.5:
        def floor_cup(x, y):
            r = np.hypot(x, y)
            return np.where(r < CUP_RI, Z_CUPF + np.maximum(0.05, apex - r * TAN_T), Z_RIM)
        p, _ = stream(t, T_REL, T_EMPTY, 1100, (0, 0, Z_O), FG["r_o"] * 0.8, v0=90, floor=floor_cup,
                      max_fall=Z_O - Z_CUPF, seed=22)
        pts.append(p)
    t_over = T_REL + (CUP_V + V_MOUND) / V_POUR * (T_EMPTY - T_REL)
    if t_over <= t <= T_EMPTY + 0.4:
        pts.append(spill(t, t_over, T_EMPTY, 260, Z_RIM + 0.5, 15.5, L, hw, seed=23))
    if 11.0 <= t <= 12.6:
        pts.append(spill(t, 11.0, 12.3, 120, Z_RIM + 0.5, 15.5, L, hw, seed=24, arc=(-30, 30)))
    P = np.vstack(pts) if pts else np.empty((0, 3))
    st.grains("stream", P, COLS[: len(P)] if len(P) <= len(COLS) else None, size=3.2)

    # ---- part B: tap-density tester
    arr = ramp(t, 15.2, 16.3)
    M_in = matrix(translate=(0, 0, 160 * (1 - arr)))
    cam_ang = 0.0
    lift = 0.0
    n = taps_at(t)
    if T_TAP0 <= t <= T_TAP1 + 0.2:
        f_tap = 4.2                                  # taps/s shown (about 250 per minute)
        ph = ((t - T_TAP0) * f_tap) % 1.0
        cam_ang = 360.0 * (t - T_TAP0) * f_tap
        lift = DROP * min(1.0, ph / 0.85) if ph < 0.85 else DROP * (1 - (ph - 0.85) / 0.05) if ph < 0.9 else 0.0
    for nm in TAP_PARTS:
        st.pose(nm, M_in, t >= 15.2)
    st.pose("sh_tester", np.eye(4), arr > 0.5)
    st.pose("cam", M_in @ matrix(translate=(0, -46, 24)) @ matrix(rot_deg=cam_ang, axis=(0, 1, 0))
            @ matrix(translate=(0, 0, 3)), t >= 15.2)
    st.add("follower", rod((0, -46, 24 + 12 + lift), (0, -46, TB_TOP - 6), 2.6), "steel")
    st.pose("follower", M_in, t >= 15.2)
    M_cyl = M_in @ matrix(translate=(0, 0, lift))
    for nm in ("platform", "cyl_foot", "cyl_glass", "cyl_grad"):
        st.pose(nm, M_cyl, t >= 15.2)

    # powder column in the cylinder
    poured = lin(t, 16.4, 17.4)
    if t < T_TAP0:
        V_ml = V0 * poured
    else:
        V_ml = kawakita(n)
    h = V_ml * ML_MM
    if h > 0.3 and t >= 15.2:
        st.add("col_pow", lathe([(0, CYL_FLOOR), (CYL_RI - 0.15, CYL_FLOOR), (CYL_RI - 0.15, CYL_FLOOR + h), (0, CYL_FLOOR + h)]),
               "powder", color=POWDER)
        st.pose("col_pow", M_cyl)
        k_side = int(len(SIDE_U) * min(1.0, poured if t < T_TAP0 else 1.0))
        z_side = CYL_FLOOR + SIDE_U[:k_side] * (h - 0.4)
        side = np.c_[(CYL_RI - 0.1) * np.cos(SIDE_TH[:k_side]), (CYL_RI - 0.1) * np.sin(SIDE_TH[:k_side]), z_side]
        side = side + np.array([0, 0, lift])
        st.grains("col_side", side, COLS[:k_side], size=3.0)
    else:
        st.remove("col_pow")
        st.remove("col_side")
    pan2_in, pan2_out = ramp(t, 15.9, 16.3), ramp(t, 17.3, 17.7)
    if 15.9 <= t <= 17.7:
        tilt2 = ramp(t, 16.2, 16.45) * (1 - ramp(t, 17.1, 17.35))
        M_p2 = matrix(translate=(-28, -4, CYL_TOP + 24)) @ matrix(rot_deg=42 * tilt2, axis=(0, 1, 0), origin=(26, 0, 6))
        st.pose("pan", matrix(translate=(-160 * (1 - pan2_in) - 160 * pan2_out, 0, 0)) @ M_p2, True)
    if 16.4 <= t <= 17.6:
        p, _ = stream(t, 16.45, 17.35, 700, (0, -4, CYL_TOP + 28), 2.0, v0=40,
                      floor=lambda x, y: CYL_FLOOR + h + 0 * x, seed=25)
        st.grains("stream2", p, COLS[: len(p)], size=3.0)
    else:
        st.remove("stream2")

    # ---- camera
    if t < 15.0:
        foc = lerp((-12, 10, 84), (8, 2, Z_RIM - 6), ramp(t, 10.2, 11.0))
        foc = lerp(foc, (70, -14, 50), ramp(t, 12.7, 13.6))
        dist = 580 - 50 * ramp(t, 3.0, 5.5) - 170 * ramp(t, 10.2, 11.0) + 140 * ramp(t, 12.6, 13.6)
        az = -26 + 16 * ramp(t, 0, 10) + 10 * ramp(t, 12.6, 14.5)
        el = 20 + 8 * ramp(t, 10.2, 11.0) - 8 * ramp(t, 12.4, 13.4)
    else:
        foc = lerp((0, 6, 108), (0, 0, CYL_FLOOR + 72), ramp(t, 17.6, 18.8))
        foc = lerp(foc, (0, 6, 108), ramp(t, 24.2, 25.4))
        dist = 590 - 230 * ramp(t, 17.6, 18.8) + 230 * ramp(t, 24.2, 25.4)
        az = -24 + 30 * ramp(t, 15.0, 28.5)
        el = 14 + 4 * ramp(t, 24.2, 25.4)
    st.orbit(foc, dist, az, el)
    st.pl.camera.SetWindowCenter(0.30, -0.04)
    rgb = st.render()

    # ---- labels
    def lab(text, xyz, off, t0, t1):
        al = ramp(t, t0, t0 + 0.35) * (1 - ramp(t, t1 - 0.35, t1))
        if al > 0:
            labels.append(Label(text, xyz, off, al))
    lab("Hall funnel, 2.54 mm orifice", (-FG["r_lip"] * 0.7, -FG["r_lip"] * 0.7, FG["lip_top"] - 4), (-70, -40), 1.4, 5.0)
    lab("orifice ~25 mm above the rim", (0, -2, Z_RIM + 12), (-150, 6), 2.5, 5.0)
    lab("25 cm³ brass density cup", (-CUP_RO * 0.7, -CUP_RO * 0.7, Z_RIM - 15), (-120, 40), 2.6, 5.5)
    lab("Catch tray", (-(TRAY_R + 2) * 0.7, -(TRAY_R + 2) * 0.7, Z_BASE + TRAY_H), (-80, 50), 2.9, 5.5)
    lab("Overflow is part of the method", (-(CUP_RO + 10) * 0.7, -(CUP_RO + 10) * 0.7, TRAY_FLOOR + 3), (-100, 60), 8.0, 9.8)
    sw_pt = (M_sw @ np.array([FG["r_lip"], 0.0, FG["lip_top"], 1.0]))[:3]
    lab("Funnel swings clear", sw_pt, (80, 30), 9.9, 10.9)
    lab("Spatula blade held upright", (xb, -20, Z_RIM + 20), (70, -70), 11.0, 12.6)
    lab("Tared balance", (BAL[0] - 40, BAL[1] - 62, 24), (-90, 50), 13.6, 15.0)
    lab("25 mL graduated cylinder", (-CYL_RO, 0, CYL_TOP - 70), (-130, 10), 15.7, 18.6)
    lab("Anvil", (-28, -10, ANVIL_TOP), (-110, 30), 15.9, 18.6)
    lab("Cam: ~3 mm lift, then a sudden drop", (0, -58, 30), (-150, 55), 18.2, 21.5)
    lab("Powder column settles", (-CYL_RO, 0, CYL_FLOOR + V_ml * ML_MM), (-120, -20), 19.0, 23.5)

    # ---- readouts
    on_bal = t >= 14.15
    readouts.append(Readout("BALANCE", f"{110.5 if on_bal else 0.0:6.2f} g", "#7CFC9A"))
    if t >= 14.3:
        readouts.append(Readout("APPARENT DENSITY", f"{AD * 1000:.2f} g/cm³", "#FFD166"))
    if t >= 15.2:
        readouts = [r for r in readouts if r.title != "BALANCE"]
        readouts.append(Readout("TAPS", f"{n:5d}"))
        vol_show = V0 * poured if t < T_TAP0 else V_ml
        readouts.append(Readout("VOLUME", f"{vol_show:5.1f} mL"))
    if t >= 24.4:
        readouts.append(Readout("TAP DENSITY", f"{TD * 1000:.2f} g/cm³", "#FFD166"))
        readouts.append(Readout("HAUSNER", f"{TD / AD:.2f}", "#FFD166"))
        readouts.append(Readout("CARR INDEX", f"{100 * (1 - AD / TD):.0f} %", "#FFD166"))

    # ---- chart
    def plot(fig):
        ax = fig.add_axes([0.15, 0.17, 0.80, 0.70])
        if t < 15.0:
            style_axes(ax, "Powder in the density cup")
            tt = np.linspace(0, T_FLOW, 300)
            vv = np.minimum(V_POUR * tt / T_FLOW, CUP_V + V_MOUND) / 1000.0
            tr = min(max(0.0, (t - T_REL) * FLOW_SPEED), T_FLOW)
            if t >= T_REL:
                ax.plot(tt[tt <= tr], vv[tt <= tr], color=C["blue"], lw=2.4)
            if t >= 11.0:
                s = lin(t, 11.0, 12.3)
                ax.plot([T_FLOW, T_FLOW + 4], [(CUP_V + V_MOUND * (1 - s)) / 1000] * 2, color=C["orange"], lw=2.4)
                ax.annotate("struck off: 25.0 cm³", (T_FLOW + 2, 25.0), (T_FLOW - 22, 21.0), fontsize=8.5,
                            arrowprops=dict(arrowstyle="->", lw=0.8))
            ax.axhline(25.0, color="#888", lw=1, ls="--")
            ax.text(1, 25.4, "cup volume", fontsize=8, color="#555")
            ax.set_xlim(0, T_FLOW + 5)
            ax.set_ylim(0, 30)
            ax.set_xlabel("time since release (s)")
            ax.set_ylabel("volume (cm³)")
        else:
            style_axes(ax, "Tap curve: volume vs taps")
            nn = np.unique(np.round(np.logspace(0, math.log10(N_MAX), 200)))
            vv = kawakita(nn)
            if t >= T_TAP0:
                sel = nn <= max(n, 1)
                ax.plot(nn[sel], vv[sel], color=C["blue"], lw=2.4)
            ax.axhline(V0, color="#888", lw=1, ls="--")
            ax.text(1.1, V0 + 0.12, f"loose  V₀ = {V0:.1f} mL", fontsize=8, color="#555")
            if t >= 24.0:
                ax.axhline(VT, color=C["orange"], lw=1.2, ls="--")
                ax.text(1.1, VT - 0.38, f"tapped  V = {VT:.1f} mL", fontsize=8, color=C["orange"])
            ax.set_xscale("log")
            ax.set_xlim(1, N_MAX * 1.2)
            ax.set_ylim(19.0, 23.2)
            ax.set_xlabel("number of taps")
            ax.set_ylabel("volume (mL)")
    img = chart.draw(plot)
    speed = ""
    if T_REL <= t <= T_EMPTY:
        speed = f"flow shown at {FLOW_SPEED:.0f}× speed"
    elif T_TAP0 <= t <= T_TAP1:
        speed = "tap count accelerated"
    ov = Overlay("Apparent & tap density → Hausner ratio", "How loosely the powder packs, and how much tapping compacts it",
                 "ASTM B212", "ASTM B527", labels=labels, readouts=readouts, chart=img,
                 step_idx=i, n_steps=len(TL.steps), step_text=step.text, speed_note=speed,
                 footer="Schematic; dimensions approximate; values illustrative")
    return compose(rgb, ov, st)


def spill(t, t0, t1, rate, z0, r0, L, hw, seed=0, arc=(-180, 180)):
    """Grains tipping over the cup rim and falling onto the overflow heap in the tray."""
    if t <= t0:
        return np.empty((0, 3))
    i_last = int((min(t, t1) - t0) * rate)
    t_fall = math.sqrt(2 * (z0 - TRAY_FLOOR) / G_VIS) + 0.3
    i_first = max(0, int((t - t0 - t_fall) * rate))
    if i_last <= i_first:
        return np.empty((0, 3))
    r_ = np.random.default_rng(seed).random((i_last + 1, 3))
    idx = np.arange(i_first, i_last)
    tau = t - (t0 + idx / rate)
    th = np.radians(arc[0] + (arc[1] - arc[0]) * r_[idx, 0])
    vr = 25 + 25 * r_[idx, 1]
    r = r0 + vr * tau
    z = z0 - 0.5 * G_VIS * tau ** 2
    heap = TRAY_FLOOR + np.maximum(0.0, hw - (r - CUP_RO) * TAN_T)
    keep = z > heap
    pts = np.c_[r * np.cos(th), r * np.sin(th), z]
    return pts[keep]


if __name__ == "__main__":
    run(frame, NAME, TL.duration)
