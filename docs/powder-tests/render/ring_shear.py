"""Schulze ring shear tester (ASTM D6773-22): yield locus and flow function ffc.

The annular bottom ring is filled, scraped level and covered with an annular lid; bars on
the ring floor and under the lid grip the powder. A loading rod presses the lid (normal
stress sigma = N / A) while a counterweight cancels the lid's own weight. The ring turns
slowly and two tie rods hold the lid through load cells F1 and F2, so a shear zone forms
just under the lid; the torque (F1 + F2) * lever arm gives the shear stress. Pre-shear
at sigma_pre to a steady state, then shear at a lower sigma_sh to failure, repeated for
several sigma_sh. Values are illustrative (a cohesive fine powder), not measurements.
"""
from common import *  # noqa: F401,F403
from shear_analysis import ffc_class, fit_locus, locus_chart, mohr

NAME = "ring_shear"
POWDER = "#c9c3b8"
COH, PHI = 1.40, 28.0                 # kPa, deg: illustrative linear yield locus (cohesive powder)
SIG_PRE = 6.0
SIG_SH = [4.5, 3.0, 1.5]
MU = math.tan(math.radians(PHI))
TAU_PRE = COH + MU * SIG_PRE + 0.12
TAU_F = [COH + MU * s + e for s, e in zip(SIG_SH, (0.05, -0.06, 0.04))]
C_FIT, MU_FIT = fit_locus(SIG_SH, TAU_F)
SIG_C, X0, R1, SIG_1 = mohr(C_FIT, MU_FIT, SIG_PRE, TAU_PRE)
FFC = SIG_1 / SIG_C

# geometry (mm)
Z_TAB = 70.0                 # top of the drive base
Z_FL = 82.0                  # ring floor (inside)
Z_RIM = 102.0                # ring rim = level of the scraped bed
R_I, R_O = 30.0, 55.0        # annulus of the bed
R_BEAM = 80.0                # lever arm of the tie rods
AREA = math.pi * (R_O ** 2 - R_I ** 2)                      # mm^2
TORQUE_K = 2 * math.pi / 3 * (R_O ** 3 - R_I ** 3)           # mm^3: torque = tau * TORQUE_K
CUT = (-40.0, 220.0)
DISC_KPA = 1.5               # each slotted weight adds 1.5 kPa on the lid (schematic)

T_SH0, T_SH1 = 11.0, 20.0
SEGS = []
for s_ in SIG_SH:
    SEGS += [("pre", SIG_PRE), ("sh", s_)]
SEG_T = (T_SH1 - T_SH0) / len(SEGS)

TL = Timeline([
    Step(0.0, 4.0, "Assemble: drive base, turntable, annular shear cell with floor bars"),
    Step(4.0, 6.6, "Fill the ring, then scrape the powder level with the rim"),
    Step(6.6, 8.6, "Lay the annular lid, bars down, on the powder"),
    Step(8.6, 11.0, "Tie rods hold the lid; weights add the normal load"),
    Step(11.0, 20.0, "Ring turns, lid is held: pre-shear at 6 kPa, shear at 4.5, 3, 1.5 kPa"),
    Step(20.0, 24.6, "Yield locus + Mohr circles give σc and σ1; ffc = σ1 / σc"),
])


# --------------------------------------------------------------------------- shear-test signals
def seg_at(t):
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
            pk * (1 - 0.14 * smooth((s - 0.55) / 0.35))
    return v * (1 - smooth((s - 0.9) / 0.1)) if s > 0.9 else v


def sigma_in_seg(i, s):
    kind, sig = SEGS[i]
    prev = SEGS[i - 1][1] if i > 0 else 0.0
    return prev + (sig - prev) * smooth(s / 0.1)


def ring_turn(t):
    """Cumulative ring rotation in degrees, clockwise seen from above (exaggerated)."""
    if t <= T_SH0:
        return 0.0
    i, kind, _, s = seg_at(min(t, T_SH1 - 1e-6))
    done = sum(14.0 if k == "pre" else 9.0 for k, _ in SEGS[:i])
    return -(done + (14.0 if kind == "pre" else 9.0) * smooth(min(s, 0.9) / 0.9))


def ring_speed(t):
    if not (T_SH0 <= t < T_SH1):
        return 0.0
    _, _, _, s = seg_at(t)
    x = min(s, 0.9) / 0.9
    return 6 * x * (1 - x) if s < 0.9 else 0.0     # derivative of smoothstep


def n_weights(t):
    """Slotted weights on the carrier (float while one is being added or removed)."""
    if t < 10.0:
        return 0.0
    if t < T_SH0:
        return 4 * lin(t, 10.0, 10.8)
    i, _, sig, s = seg_at(min(t, T_SH1 - 1e-6))
    prev = SEGS[i - 1][1] if i > 0 else SIG_PRE
    a, b = prev / DISC_KPA, sig / DISC_KPA
    return a + (b - a) * smooth(s / 0.1)


def in_section(th):
    d = (np.degrees(th) - CUT[0]) % 360.0
    return d <= (CUT[1] - CUT[0]) + 1e-6


# --------------------------------------------------------------------------- stage
st = Stage(bench=(-300, 300, -190, 230))
st.add("base", box(-150, 150, -115, 115, 0, Z_TAB), "light")
st.add("panel", box(-135, 135, -115.6, -115, 10, 58), "dark")
st.add("led", box(70, 112, -116.2, -115.4, 34, 46), "lcd", color="#38c172")
st.add("table", disc(72, Z_TAB, 77), "steel_dark")
bolts = None
for a in np.radians(np.arange(0, 360, 45)):
    b = disc(3.0, 77, 80).translate((66 * math.cos(a), 66 * math.sin(a), 0), inplace=False)
    bolts = b if bolts is None else bolts.merge(b)
st.add("bolts", bolts, "steel")
ring_prof = [(25, 77), (60, 77), (60, Z_RIM), (R_O, Z_RIM), (R_O, Z_FL), (R_I, Z_FL), (R_I, Z_RIM), (25, Z_RIM)]
st.add("ring", lathe(ring_prof, a0=CUT[0], a1=CUT[1]), "steel")
# lid: annular plate with bars underneath, cut like the ring
st.add("lid", lathe([(R_I + 0.8, Z_RIM), (R_O - 0.8, Z_RIM), (R_O - 0.8, Z_RIM + 4), (R_I + 0.8, Z_RIM + 4)],
                    a0=CUT[0], a1=CUT[1]), "alu")
lid_bars = None
for a in np.arange(0, 360, 22.5):
    if not in_section(np.radians([a]))[0]:
        continue
    b = box(R_I + 1.5, R_O - 1.5, -0.8, 0.8, Z_RIM - 2.0, Z_RIM).transform(matrix(rot_deg=a), inplace=False)
    lid_bars = b if lid_bars is None else lid_bars.merge(b)
st.add("lidbars", lid_bars, "alu")
lid_top = None
for x in (-42.5, 42.5):
    p = disc(4, Z_RIM + 4, Z_RIM + 12).translate((x, 0, 0), inplace=False)
    lid_top = p if lid_top is None else lid_top.merge(p)
lid_top = lid_top.merge(box(-R_BEAM - 2, R_BEAM + 2, -4.5, 4.5, Z_RIM + 12, Z_RIM + 18)).merge(
    disc(7, Z_RIM + 18, Z_RIM + 22))
st.add("crossbeam", lid_top, "alu")
Z_TIE = Z_RIM + 15
st.add("tie1", rod((R_BEAM, 0, Z_TIE), (R_BEAM, 96, Z_TIE), 1.6), "steel")
st.add("tie2", rod((-R_BEAM, 0, Z_TIE), (-R_BEAM, -96, Z_TIE), 1.6), "steel")
st.add("post1", rod((R_BEAM, 104, Z_TAB), (R_BEAM, 104, Z_TIE - 10), 4), "steel_dark")
st.add("post2", rod((-R_BEAM, -104, Z_TAB), (-R_BEAM, -104, Z_TIE - 10), 4), "steel_dark")
st.add("cell1", cbox((R_BEAM, 104, Z_TIE), (13, 11, 16)), "blue")
st.add("cell2", cbox((-R_BEAM, -104, Z_TIE), (13, 11, 16)), "blue")
Z_LEV = 232.0
st.add("lrod", rod((0, 0, Z_RIM + 22), (0, 0, Z_LEV), 3.0), "steel")
st.add("carrier", disc(15, 168, 171), "steel_dark")
st.add("pivot", rod((0, 100, Z_TAB), (0, 100, Z_LEV - 3), 5), "steel_dark")
st.add("lever", box(-4, 4, -8, 182, Z_LEV - 3, Z_LEV + 3), "mid")
st.add("cweight", cbox((0, 168, Z_LEV - 20), (34, 26, 30)), "dark")
for k in range(4):
    st.add(f"w{k}", lathe([(3.6, 0), (14, 0), (14, 5.2), (3.6, 5.2)]), "brass")
st.shadow("sh_base", (0, 0), 200, 150, 0.33)

ticks = []
for a in np.arange(0, 360, 10):
    ticks.append((a, box(60.0, 60.7, -0.9, 0.9, 93, 100)))
floor_bars = [(a, box(R_I + 0.6, R_O - 0.6, -0.8, 0.8, Z_FL, Z_FL + 2.4)) for a in np.arange(0, 360, 22.5)]

rng = np.random.default_rng(31)
N_FACE = 900
F_R = rng.uniform(R_I + 0.3, R_O - 0.3, N_FACE)
F_U = rng.uniform(0, 1, N_FACE)
F_A = np.radians(np.where(rng.random(N_FACE) < 0.5, CUT[0], CUT[1]))
F_COL = grain_colors(N_FACE, POWDER, 0.12, seed=32)
N_TOP = 1400
T_R = np.sqrt(rng.uniform((R_I + 0.4) ** 2, (R_O - 0.4) ** 2, N_TOP))
T_TH = np.radians(rng.uniform(CUT[0], CUT[1], N_TOP))
T_COL = grain_colors(N_TOP, POWDER, 0.12, seed=33)
chart = Chart()
_LF = font(15, bold=True)


# --------------------------------------------------------------------------- powder level
def bed_top(t):
    if t < 4.15:
        return Z_FL
    return Z_FL + (Z_RIM - Z_FL) * lin(t, 4.15, 5.6)


def excess(r, th, t):
    """Heaped powder above the rim before scraping; zero where the scraper has passed."""
    h = 1.6 * ramp(t, 4.9, 5.6) * (1 + 0.45 * np.sin(5 * th + 1.3) * np.sin(math.pi * (r - R_I) / (R_O - R_I)))
    ang = scraper_angle(t)
    if ang is None:
        return h
    passed = ((CUT[1] - np.degrees(th)) % 360.0) <= -ang + 1e-9   # scraper sweeps clockwise from CUT[1]
    return np.where(passed, -0.05, h)


def scraper_angle(t):
    if t < 5.75:
        return None
    return -(CUT[1] - CUT[0]) * ramp(t, 5.8, 6.55)


def frame(t):
    i_step, step = TL.current(t)
    labels, readouts = [], []
    turn = ring_turn(t)
    R_turn = matrix(rot_deg=turn)

    # ---- assembly / hook-up arrivals
    arr = [("base", 0.1, (0, 0, -70)), ("panel", 0.1, (0, 0, -70)), ("led", 0.1, (0, 0, -70)),
           ("table", 0.6, (0, 0, 80)), ("bolts", 0.6, (0, 0, 80)),
           ("post1", 1.0, (0, 0, -60)), ("post2", 1.0, (0, 0, -60)), ("cell1", 1.0, (0, 0, -60)),
           ("cell2", 1.0, (0, 0, -60)), ("pivot", 1.0, (0, 0, -60)),
           ("ring", 1.6, (0, 0, 130)),
           ("lid", 6.8, (0, 0, 90)), ("lidbars", 6.8, (0, 0, 90)),
           ("crossbeam", 8.7, (0, 0, 90)), ("tie1", 9.1, (0, 60, 0)), ("tie2", 9.1, (0, -60, 0)),
           ("lrod", 9.5, (0, 0, 120)), ("carrier", 9.5, (0, 0, 120)),
           ("lever", 9.5, (0, 0, 80)), ("cweight", 9.5, (0, 0, 80))]
    for nm, t0, off in arr:
        M, vis, _ = arrive(t, t0, offset=off)
        if nm in ("bolts",):
            M = M @ R_turn
        st.pose(nm, M, vis)

    # slotted weights on the carrier
    nw = n_weights(t)
    for k in range(4):
        frac = float(np.clip(nw - k, 0, 1))
        z = 171 + 5.6 * k
        st.pose(f"w{k}", matrix(translate=(0, -40 * (1 - frac), z + 40 * (1 - frac))), frac > 0.02,
                opacity=min(1.0, 0.2 + frac))

    # rotating features of the ring: outer-wall ticks and floor bars (only outside the cut)
    ring_vis = t >= 1.6
    Mr = arrive(t, 1.6, offset=(0, 0, 130))[0]
    tk = None
    for a, m in ticks:
        a_now = a + turn
        if not in_section(np.radians([a_now]))[0]:
            continue
        mm = m.transform(matrix(rot_deg=a_now), inplace=False)
        tk = mm if tk is None else tk.merge(mm)
    st.add("ticks", tk, "dark")
    st.pose("ticks", Mr, ring_vis)
    fb = None
    for a, m in floor_bars:
        a_now = a + turn
        if not in_section(np.radians([a_now - 3, a_now + 3])).all():
            continue
        mm = m.transform(matrix(rot_deg=a_now), inplace=False)
        fb = mm if fb is None else fb.merge(mm)
    st.add("fbars", fb, "steel_dark")
    st.pose("fbars", Mr, ring_vis)

    # ---- powder bed, its excess before scraping, and the scraper
    top = bed_top(t)
    if top > Z_FL + 0.2:
        bed = lathe([(R_I + 0.05, Z_FL + 0.02), (R_O - 0.05, Z_FL + 0.02), (R_O - 0.05, top), (R_I + 0.05, top)],
                    a0=CUT[0], a1=CUT[1])
        st.add("bed", bed, "powder", color=POWDER)
        zf = Z_FL + 0.3 + F_U * (top - Z_FL - 0.6)
        nrm = np.c_[-np.sin(F_A), np.cos(F_A), 0 * F_A] * np.where(F_A == np.radians(CUT[0]), -1, 1)[:, None]
        Pf = np.c_[F_R * np.cos(F_A), F_R * np.sin(F_A), zf] + 0.15 * nrm
        st.grains("face", Pf, F_COL, size=3.0)
    else:
        st.remove("bed")
        st.remove("face")
    if 4.9 <= t < 6.6:
        surf = polar_surface(lambda r, th: Z_RIM + excess(r, th, t), R_O - 0.05, R_I + 0.05, nr=10, nth=90,
                             a0=CUT[0], a1=CUT[1])
        st.add("heap", surf, "powder", color=POWDER)
    else:
        st.remove("heap")
    if t < 6.9:   # grains on the open surface until the lid covers it
        zt = np.full(N_TOP, min(top, Z_RIM) + 0.15) + (np.maximum(excess(T_R, T_TH, t), 0) if t >= 4.9 else 0)
        keep = zt > Z_FL + 0.5
        st.grains("topg", np.c_[T_R * np.cos(T_TH), T_R * np.sin(T_TH), zt][keep], T_COL[keep], size=3.0)
    else:
        st.remove("topg")
    sa = scraper_angle(t)
    if sa is not None and t < 6.65:
        a = CUT[1] + sa
        scr = box(R_I - 6, R_O + 6, -0.8, 0.8, Z_RIM, Z_RIM + 14).transform(matrix(rot_deg=a), inplace=False)
        st.add("scraper", scr, "orange")
    else:
        st.remove("scraper")
    # filling stream from a spout circling the annulus
    if 4.1 <= t <= 5.75:
        ang = math.radians(CUT[1] - 300 * lin(t, 4.1, 5.6))
        o = (42.5 * math.cos(ang), 42.5 * math.sin(ang), 175)
        p, _ = stream(t, 4.1, 5.6, 1000, o, 3.0, v0=60, floor=lambda x, y: top + 0 * x, seed=41)
        st.grains("pour", p, T_COL[: len(p)] if len(p) <= N_TOP else None, size=3.0)
    else:
        st.remove("pour")

    # shear zone under the lid, and the velocity profile on the right-hand section face
    shearing = T_SH0 <= t < T_SH1
    if shearing or (T_SH1 <= t < T_SH1 + 1.0):
        i_, _, _, s_ = seg_at(min(t, T_SH1 - 1e-6))
        z0, z1 = Z_RIM - 6.0, Z_RIM - 2.0
        quads = None
        for a_deg, sgn in ((CUT[0], -1), (CUT[1], 1)):
            a = math.radians(a_deg)
            u = np.array([math.cos(a), math.sin(a), 0.0])
            n = sgn * np.array([-math.sin(a), math.cos(a), 0.0]) * 0.25
            q = pv.PolyData(np.array([n + R_I * u + (0, 0, z0), n + R_O * u + (0, 0, z0),
                                      n + R_O * u + (0, 0, z1), n + R_I * u + (0, 0, z1)]), [4, 0, 1, 2, 3])
            quads = q if quads is None else quads.merge(q)
        live = 0.35 + 0.35 * min(1.0, tau_in_seg(i_, s_) / TAU_PRE)
        st.add("band", quads, "orange", opacity=live * (1 - ramp(t, T_SH1, T_SH1 + 1.0)), lighting=False)
        v = ring_speed(t)
        if v > 0.05:
            a = math.radians(CUT[0])
            u = np.array([math.cos(a), math.sin(a), 0.0])
            d = np.array([math.sin(a), -math.cos(a), 0.0])        # clockwise = into the open wedge
            arrows = None
            for zq in (85.0, 88.5, 92.0, 95.0, 97.5, 99.5):
                frac = float(np.clip((Z_RIM - 2.0 - zq) / 4.5, 0, 1))
                L = 13.0 * v / 1.5 * frac
                if L < 0.8:
                    continue
                start = (R_I + R_O) / 2 * u + np.array([0, 0, zq]) + 0.3 * d
                arw = pv.Arrow(start=start, direction=d, scale=L, tip_length=min(0.45, 3.2 / L),
                               tip_radius=min(0.25, 1.4 / L), shaft_radius=min(0.09, 0.55 / L))
                arrows = arw if arrows is None else arrows.merge(arw)
            if arrows is not None:
                st.add("vel", arrows, "orange", color="#e85d0c")
            else:
                st.remove("vel")
        else:
            st.remove("vel")
    else:
        st.remove("band")
        st.remove("vel")

    # ---- camera: whole tester, closer during the test, back for the result
    near = ramp(t, 10.4, 12.0) * (1 - ramp(t, 20.0, 21.8))
    pre = ramp(t, 3.4, 4.6) * (1 - ramp(t, 7.6, 9.0))       # look into the ring while filling
    dist = 780 - 350 * near - 280 * pre
    focal = lerp((0, 10, 128), (0, -5, 98), max(near, pre))
    az = -28 + 18 * ramp(t, 0, 24)
    el = 24 + 10 * pre + 2 * near
    st.orbit(focal, dist, az, el)
    st.pl.camera.SetWindowCenter(0.30, 0.0)
    rgb = st.render()

    # ---- labels
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
    a_mid = math.radians(200)
    lab("Turntable (drive below)", (-60, -40, 77), 50, 0.8, 3.6)
    lab("Annular shear cell", (R_O * math.cos(a_mid) - 5, R_O * math.sin(a_mid), Z_RIM), -40, 2.0, 4.1, "left")
    lab("Bars on the floor", (42 * math.cos(math.radians(-40)), 42 * math.sin(math.radians(-40)), Z_FL + 2),
        60, 2.4, 4.1, "right")
    lab("Scraper levels the bed with the rim", (40 * math.cos(math.radians(150)), 40 * math.sin(math.radians(150)),
                                                 Z_RIM + 8), -55, 5.8, 6.9, "left")
    lab("Lid, bars underneath", (-R_O + 2, -3, Z_RIM + 4), -45, 7.0, 8.7, "left")
    lab("Tie rods → load cells F1, F2", (-R_BEAM, -104, Z_TIE + 10), -40, 9.3, 11.4, "left")
    lab("Weights set the normal load", (-14, 0, 182), -30, 10.0, 12.2, "left")
    lab("Counterweight balances the lid", (0, 168, Z_LEV - 22), 34, 10.0, 12.2, "right")
    lab("Ring turns; lid held still", (-60, -10, 90), 60, 11.4, 14.6, "left")
    lab("Shear zone just under the lid", (R_O * math.cos(math.radians(220)), R_O * math.sin(math.radians(220)),
                                          Z_RIM - 4), 45, 14.6, 19.6, "left")

    # ---- readouts
    if shearing:
        i, kind, _, s = seg_at(t)
        tau = tau_in_seg(i, s)
        f_sum = tau * TORQUE_K * 1e-3 / R_BEAM            # N  (kPa = 1e-3 N/mm^2)
        readouts.append(Readout("NORMAL STRESS σ", f"{sigma_in_seg(i, s):4.1f} kPa"))
        readouts.append(Readout("STEP", "pre-shear" if kind == "pre" else "shear", "#9ad0ff"))
        readouts.append(Readout("F1 / F2", f"{0.51 * f_sum:4.1f} / {0.49 * f_sum:4.1f} N", "#FFD166"))
        readouts.append(Readout("SHEAR STRESS τ", f"{tau:4.2f} kPa", "#FFD166"))
    if t >= 21.0:
        readouts.append(Readout("σc (UYS)", f"{SIG_C:4.2f} kPa"))
    if t >= 21.8:
        readouts.append(Readout("σ1 (MPS)", f"{SIG_1:4.1f} kPa"))
    if t >= 22.6:
        readouts.append(Readout("ffc = σ1/σc", f"{FFC:3.1f}  {ffc_class(FFC)}", "#FFD166"))

    # ---- chart
    def programme(fig):
        ax = fig.add_axes([0.03, 0.03, 0.94, 0.94])
        ax.axis("off")
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.text(0.03, 0.93, "Ring shear test (one flow function point)", fontsize=11, fontweight="bold",
                color="#222")
        rows = [("1", "Fill the ring, scrape level", 4.0),
                ("2", "Lid on; tie rods to load cells F1, F2", 6.6),
                ("3", "Normal load σ = N / A on the lid", 8.6),
                ("4", "Pre-shear at σpre = 6 kPa to steady flow", 11.0),
                ("5", "Shear to failure at σ = 4.5, 3, 1.5 kPa", 11.0),
                ("", "   (pre-shear again before each step)", 11.0),
                ("6", "τ = torque / (2π/3 · (ro³ − ri³))", 11.0),
                ("7", "Yield locus + Mohr circles → ffc", 20.0)]
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
        ax.set_ylim(0, 8)
        ax.set_xticks([1.5 + 2 * j for j in range(len(SIG_SH))])
        ax.set_xticklabels([f"{s:g}" for s in SIG_SH])
        ax.set_xlabel("shear steps at σ (kPa); pre-shear at 6 kPa before each")
        ax.set_ylabel("stress (kPa)")
        ax.legend(fontsize=8, loc="upper right", frameon=False, ncol=2)

    if t < T_SH0 - 0.3:
        img = chart.draw(programme)
    elif t < T_SH1 + 0.6:
        img = chart.draw(trace)
    else:
        img = chart.draw(lambda fig: locus_chart(fig, t - (T_SH1 + 0.6), SIG_SH, TAU_F, SIG_PRE, TAU_PRE))
    ov = Overlay("Schulze ring shear tester", "Shear strength of a consolidated bed → flow function ffc",
                 "ASTM D6773-22", labels=labels, readouts=readouts, chart=img,
                 step_idx=i_step, n_steps=len(TL.steps), step_text=step.text,
                 speed_note="test time compressed" if shearing else "",
                 footer="Schematic; dimensions approximate; values illustrative", readout_row_px=470)
    return compose(rgb, ov, st)


if __name__ == "__main__":
    run(frame, NAME, TL.duration)
