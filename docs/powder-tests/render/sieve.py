"""Dry sieve analysis of metal powders (ASTM B214, sieves to ASTM E11).

About 100 g (90-110 g; 40-60 g if the apparent density is below 1.50 g/cm3) goes on the top
of a nest of 200 mm (8 in.) test sieves, coarsest on top, with a pan underneath. A
rotating-and-tapping shaker runs for 15 min; then the powder retained on each sieve and in
the pan is weighed and reported as mass % per size band. Below about 45 um dry sieving
stops working, which is why fine AM powders go to laser diffraction (ASTM B822).

Each dot is an equal-mass parcel of powder; dot sizes are exaggerated by size band.
Values are illustrative (a 45-150 um cut of the kind used for DED or EBM).
"""
from common import *  # noqa: F401,F403

NAME = "sieve"
CUT = (-48.0, 228.0)            # cutaway wedge (84 degrees) faces the camera
Z_P = 158.0                     # top of the shaker's sieve plate; the stack sits here
APERTURES = [150, 106, 75, 63, 45]           # um, top to bottom
MESH_NO = [100, 140, 200, 230, 325]          # US standard sieve numbers (ASTM E11)
BANDS = [">150", "106–150", "75–106", "63–75", "45–63", "<45"]       # retained on deck d
GRAMS = [1.82, 21.36, 37.95, 17.12, 15.88, 5.79]                     # illustrative
SAMPLE = 100.04
TOTAL = sum(GRAMS)
PCT = [100 * g / TOTAL for g in GRAMS]
DOT_PX = [6.2, 5.4, 4.6, 4.0, 3.5, 3.0]

T_POUR0, T_POUR1 = 4.4, 6.3
T_SHAKE0, T_SHAKE1 = 8.0, 17.0
T_EXP0, T_EXP1 = 18.0, 19.2     # the nest is spread apart so each deck shows
EXPLODE = 27.0                  # extra gap between decks (mm)
T_W0, T_WSTEP = 19.4, 1.0       # weighing: one fraction per second, top sieve first

TL = Timeline([
    Step(0.0, 4.2, "Nest 200 mm test sieves, coarsest on top, pan at the bottom"),
    Step(4.2, 6.6, "Pour about 100 g (90–110 g) onto the top sieve"),
    Step(6.6, 8.0, "Fit the lid, clamp the stack and lower the tapping hammer"),
    Step(8.0, 17.0, "Shake 15 min: gyratory motion plus a tap on the lid"),
    Step(17.0, 19.4, "Stop, unclamp and unstack the sieves"),
    Step(19.4, 25.6, "Weigh the powder retained on each sieve and in the pan"),
    Step(25.6, 28.4, "Report mass % per size band and cumulative % passing"),
    Step(28.4, 31.4, "Below about 45 µm dry sieving fails: use laser diffraction"),
])


# --------------------------------------------------------------------------- geometry
def deck_z(d):
    """Height (stack frame, relative to Z_P) of the surface grains rest on, deck d (0 = top)."""
    return 2.0 if d == 5 else 26.5 + 19.0 * (4 - d)


def sieve_bottom(d):
    return 0.0 if d == 5 else 19.0 + 19.0 * (4 - d)


SIEVE_PROF = [(97.6, 0.0), (99.3, 0.0), (99.3, 6.0), (101.8, 7.5), (101.8, 23.0), (103.0, 25.0),
              (100.0, 25.0), (100.0, 8.5), (97.6, 7.0)]
PAN_PROF = [(0.0, 0.0), (101.8, 0.0), (101.8, 23.0), (103.0, 25.0), (100.0, 25.0), (100.0, 2.0), (0.0, 2.0)]
LID_PROF = [(0.0, 7.0), (97.6, 7.0), (97.6, 0.0), (99.3, 0.0), (99.3, 6.0), (103.0, 6.0), (103.0, 10.0),
            (0.0, 10.0)]


def mesh_texture(cells=4, n=256, wire=3):
    img = np.zeros((n, n, 4), np.uint8)
    step = n // cells
    for k in range(cells):
        a = k * step
        img[a:a + wire, :, :3] = (88, 94, 102)
        img[:, a:a + wire, :3] = (88, 94, 102)
        img[a:a + wire, :, 3] = 235
        img[:, a:a + wire, 3] = 235
    tex = pv.Texture(img)
    tex.repeat = True
    return tex


def deck_cloth(z, repeats):
    m = polar_surface(lambda r, t: z + 0 * r, 99.6, nr=12, nth=72, a0=CUT[0], a1=CUT[1])
    m = m.texture_map_to_plane(origin=(-100, -100, z), point_u=(100, -100, z), point_v=(-100, 100, z))
    m.active_texture_coordinates = m.active_texture_coordinates * repeats
    return m


st = Stage(bench=(-420, 330, -230, 230))
TEX = mesh_texture()
# shaker body (Ro-Tap style) with sieve plate, side posts and the hammer column at the back
st.add("body", box(-175, 175, -150, 150, 0, 150), "mid")
st.add("panel", box(-120, 120, -151.5, -149.5, 40, 120), "light")
st.add("display", box(-60, 20, -153, -151.4, 85, 108), "lcd")
st.add("knob", rod((50, -151, 96), (50, -162, 96), 9), "dark")
st.add("plate", disc(112, Z_P - 8, Z_P), "steel_dark")
for s in (-1, 1):
    st.add(f"post{s}", rod((150 * s, 0, 150), (150 * s, 0, Z_P + 150), 7), "steel")
st.add("hcol", box(-16, 16, 112, 140, 150, Z_P + 196), "mid")
# hammer arm: pivot at the top of the column, head over the cork
PIV = np.array([0.0, 126.0, Z_P + 186.0])
CORK_TOP = Z_P + 142.0
arm = box(-9, 9, -2, 128, Z_P + 180, Z_P + 192).merge(rod((0, 0, CORK_TOP), (0, 0, Z_P + 182), 15))
st.add("hammer", arm, "dark")
st.add("crossbar", box(-160, 160, -15, 15, Z_P + 124, Z_P + 134).merge(disc(19, Z_P + 124, Z_P + 134)), "steel")
st.add("cork", disc(13, Z_P + 134, CORK_TOP), "orange", color="#b58a5a", specular=0.1)
st.add("cover", disc(106, Z_P + 124, Z_P + 128), "steel_dark")
# nest: pan, five sieves, lid (all in the stack frame, at Z_P)
st.add("pan", lathe(PAN_PROF, a0=CUT[0], a1=CUT[1]).translate((0, 0, Z_P), inplace=False), "steel")
for d in range(5):
    zb = Z_P + sieve_bottom(d)
    st.add(f"sieve{d}", lathe(SIEVE_PROF, a0=CUT[0], a1=CUT[1]).translate((0, 0, zb), inplace=False), "steel")
    st.add(f"cloth{d}", deck_cloth(Z_P + deck_z(d) - 0.6, 3 + d), "white", texture=TEX, color="#ffffff",
           ambient=0.35, diffuse=0.7, specular=0.2)
st.add("lid", lathe(LID_PROF, a0=CUT[0], a1=CUT[1]).translate((0, 0, Z_P + 114), inplace=False), "steel")
st.add("beaker", lathe([(0, 0), (30, 0), (30, 62), (33, 66), (31.5, 66), (28.4, 62.5), (28.4, 1.6), (0, 1.6)]), "glass")
st.add("hl", lathe([(103.5, 0), (106.5, 0), (106.5, 3), (103.5, 3)], res=120), "orange", ambient=0.5)
st.shadow("sh_body", (0, 0), 230, 195, 0.35)

# ---- parcels of powder: class d ends up on deck d
rng = np.random.default_rng(11)
N_TOTAL = 2600
counts = np.maximum(8, np.round(np.array(PCT) / 100 * N_TOTAL).astype(int))
DEST = np.concatenate([np.full(c, d) for d, c in enumerate(counts)])
N = len(DEST)
rng.shuffle(DEST)
ph_lo, ph_hi = math.radians(CUT[0] + 5), math.radians(CUT[1] - 5)
HOME_R = np.sqrt(rng.uniform(0.01, 1, N)) * 93.0
HOME_PH = rng.uniform(ph_lo, ph_hi, N)
HEAP_R = np.sqrt(rng.uniform(0, 1, N)) * 30.0
HEAP_PH = rng.uniform(ph_lo, ph_hi, N)
POUR_T = rng.uniform(T_POUR0 + 0.2, T_POUR1, N)
SPREAD_T = rng.uniform(0.4, 1.8, N)
JIT = rng.normal(0, 1, (N, 2))
PASS = np.full((N, 5), np.inf)        # time (s after T_SHAKE0) the parcel drops through deck j
for i in range(N):
    p = SPREAD_T[i] * 0.6
    for j in range(DEST[i]):
        p += 0.15 + rng.exponential(0.75)
        PASS[i, j] = min(p, (T_SHAKE1 - T_SHAKE0) - 0.6)
T_FALL = math.sqrt(2 * 19.0 / G_VIS)
ZD = np.array([deck_z(d) for d in range(6)])
COLS = grain_colors(N, "#7c838b", 0.13, seed=4)

chart = Chart()

# camera keyframes: (t, focal x, focal z, distance, elevation, azimuth, window-centre x)
CAM = [(0.0, -20, 190, 1120, 23, -30, 0.30), (3.4, -20, 190, 1120, 23, -22, 0.30),
       (5.4, 0, 235, 900, 27, -19, 0.28), (7.3, 0, 235, 900, 27, -17, 0.28),
       (8.8, 0, Z_P + 62, 600, 11, -15, 0.20), (16.9, 0, Z_P + 62, 600, 12, -7, 0.20),
       (19.2, 0, 300, 1010, 17, -6, 0.26), (25.6, 0, 300, 1010, 17, -1, 0.26),
       (31.4, 0, 300, 960, 16, 4, 0.26)]


def keys(t, table):
    """Smoothstep between keyframe rows (t, v1, v2, ...); holds the ends."""
    if t <= table[0][0]:
        return table[0][1:]
    for a, b in zip(table, table[1:]):
        if t <= b[0]:
            u = ramp(t, a[0], b[0])
            return tuple(x + (y - x) * u for x, y in zip(a[1:], b[1:]))
    return table[-1][1:]


def taps(t):
    """Current hammer lift (0..1) and the time of the last tap, during shaking."""
    if not (T_SHAKE0 <= t < T_SHAKE1):
        return 0.0, None
    period = 0.42
    ph = ((t - T_SHAKE0) % period) / period
    lift = math.sin(math.pi * min(1.0, ph / 0.85)) if ph < 0.85 else 0.0
    return lift, T_SHAKE0 + math.floor((t - T_SHAKE0) / period) * period


def gyration(t):
    """Horizontal circular (gyratory) offset of the nest; amplitude exaggerated."""
    if not (T_SHAKE0 <= t < T_SHAKE1):
        return np.zeros(3)
    a = 3.2 * ramp(t, T_SHAKE0, T_SHAKE0 + 0.4) * (1 - ramp(t, T_SHAKE1 - 0.4, T_SHAKE1))
    w = 2 * math.pi * 1.6
    return np.array([a * math.cos(w * t), a * math.sin(w * t), 0.0])


def explode_z(d, t):
    return 0.0 if d == 5 else EXPLODE * (5 - d) * ramp(t, T_EXP0, T_EXP1)


def frame(t):
    i, step = TL.current(t)
    labels, readouts = [], []
    g = gyration(t)
    lift, t_tap = taps(t)
    since_tap = (t - t_tap) if t_tap is not None else 1.0
    jolt = -0.8 * math.exp(-(since_tap - 0.36) / 0.05) if (t_tap is not None and since_tap > 0.36) else 0.0

    # ---- assembly
    for nm in ("body", "panel", "display", "knob", "plate", "post-1", "post1", "hcol"):
        st.pose(nm, arrive(t, 0.1, offset=(0, 0, -40))[0], t >= 0.1)
    order = ["pan", "sieve4", "sieve3", "sieve2", "sieve1", "sieve0"]
    for k, nm in enumerate(order):
        d = 5 if nm == "pan" else int(nm[-1])
        M, vis, _ = arrive(t, 0.8 + 0.5 * k, offset=(0, 0, 110))
        M = matrix(translate=g + np.array([0, 0, jolt + explode_z(d, t)])) @ M
        st.pose(nm, M, vis)
        if d < 5:
            st.pose(f"cloth{d}", M, vis)
    # lid, clamp (cover plate, crossbar, cork) and hammer
    lid_in, lid_out = ramp(t, 6.65, 7.2), ramp(t, 17.6, 18.2)
    st.pose("lid", matrix(translate=g + np.array([0, -260 * lid_out, jolt + 160 * (1 - lid_in) + 100 * lid_out])),
            6.65 <= t < 18.2, opacity=1 - lid_out)
    cl_in, cl_out = ramp(t, 7.0, 7.5), ramp(t, 17.3, 17.9)
    Mc = matrix(translate=g + np.array([0, 0, jolt + 120 * (1 - cl_in) + 150 * cl_out]))
    for nm in ("crossbar", "cork", "cover"):
        st.pose(nm, Mc, 7.0 <= t < 17.9, opacity=1 - cl_out)
    ang = 32 * (1 - ramp(t, 7.4, 7.9)) + 100 * ramp(t, 17.0, 17.8) + 11 * lift
    st.pose("hammer", matrix(rot_deg=-ang, axis=(1, 0, 0), origin=PIV), True)

    # ---- beaker pours the sample
    b_in, b_out = ramp(t, 3.9, 4.4), ramp(t, 6.3, 6.8)
    tilt = ramp(t, 4.3, 4.7) * (1 - ramp(t, 6.1, 6.4))
    Mb = matrix(translate=(40 - 180 * (1 - b_in) - 180 * b_out, -10, Z_P + 150)) @ \
        matrix(rot_deg=105 * tilt, axis=(0, 1, 0), origin=(30, 0, 64))
    st.pose("beaker", Mb, 3.9 <= t < 6.8)

    # ---- parcels
    s = t - T_SHAKE0
    pos = np.zeros((N, 3))
    vis = np.zeros(N, bool)
    lip = np.array([40 + 30 + 4, -10, Z_P + 150 + 62])
    if t >= T_POUR0:
        landed = t >= POUR_T
        falling = (t >= POUR_T - 0.45) & ~landed
        hx, hy = HEAP_R * np.cos(HEAP_PH), HEAP_R * np.sin(HEAP_PH)
        frac_landed = np.clip((t - T_POUR0) / (T_POUR1 - T_POUR0), 0, 1)
        hz = Z_P + ZD[0] + 1.0 + 11.0 * frac_landed * np.clip(1 - HEAP_R / 30.0, 0, 1)
        tau = np.clip(t - (POUR_T - 0.45), 0, 0.45) / 0.45
        fx = lip[0] + (hx - lip[0]) * tau
        fy = lip[1] + (hy - lip[1]) * tau
        fz = lip[2] + (hz - lip[2]) * tau ** 2
        pos[falling] = np.c_[fx, fy, fz][falling]
        vis |= falling
        if t < T_SHAKE0:
            pos[landed] = np.c_[hx, hy, hz][landed]
        else:
            sp = smooth(np.clip(s / SPREAD_T, 0, 1))
            x = hx + (HOME_R * np.cos(HOME_PH) - hx) * sp
            y = hy + (HOME_R * np.sin(HOME_PH) - hy) * sp
            z_top = Z_P + ZD[0] + 1.0 + (hz - Z_P - ZD[0] - 1.0) * (1 - sp)
            deck_now = (s >= PASS).sum(axis=1)
            fall_t = np.zeros(N)
            for j in range(5):
                cur = (deck_now == j + 1) & (s < PASS[:, j] + T_FALL)
                fall_t[cur] = s - PASS[cur, j]
            z_rest = Z_P + ZD[deck_now] + 1.0
            z_from = Z_P + ZD[np.maximum(deck_now - 1, 0)] + 1.0
            zf = np.maximum(z_rest, z_from - 0.5 * G_VIS * fall_t ** 2)
            z = np.where(deck_now == 0, z_top, np.where(fall_t > 0, zf, z_rest))
            shaking = 1.0 if T_SHAKE0 <= t < T_SHAKE1 else 0.0
            jit = 1.2 * JIT * shaking * math.sin(7.3 * t)
            bounce = 1.3 * math.exp(-(since_tap - 0.36) / 0.07) if (t_tap is not None and since_tap > 0.36) else 0.0
            z = z + bounce * np.abs(JIT[:, 0]) * 0.6 + np.array([explode_z(d, t) for d in range(6)])[deck_now]
            pos[landed] = np.c_[x + jit[:, 0], y + jit[:, 1], z][landed]
        vis |= landed
        pos += g + np.array([0, 0, jolt])
    for d in range(6):
        sel = vis & (DEST == d)
        st.grains(f"g{d}", pos[sel], COLS[sel], size=DOT_PX[d])

    # ---- weighing: highlight ring on the deck being weighed
    cur_w = None
    for d in range(6):
        if T_W0 + T_WSTEP * d <= t < T_W0 + T_WSTEP * (d + 1):
            cur_w = d
    if cur_w is not None:
        z_rim = Z_P + (sieve_bottom(cur_w) + 23.0 if cur_w < 5 else 23.0) + explode_z(cur_w, t)
        st.pose("hl", matrix(translate=(0, 0, z_rim)), True)
    else:
        st.pose("hl", None, False)

    # ---- camera
    fx, fz, dist, el, az, wc = keys(t, CAM)
    st.orbit((fx, 0, fz), dist, az, el)
    st.pl.camera.SetWindowCenter(wc, -0.06)
    rgb = st.render()

    # ---- labels: aperture per deck, then the weighed mass
    def lab(text, xyz, off, a):
        if a > 0:
            labels.append(Label(text, xyz, off, a))
    weighed = [d for d in range(6) if t >= T_W0 + T_WSTEP * d + 0.55]
    for d in range(6):
        t0 = 0.8 + 0.5 * (5 - d) + 0.3
        a = ramp(t, t0, t0 + 0.35)
        z = Z_P + (ZD[d] if d < 5 else 10.0) + jolt + explode_z(d, t)
        name = f"{APERTURES[d]} µm (No. {MESH_NO[d]})" if d < 5 else "Pan"
        if d in weighed:
            name = f"{name} · {GRAMS[d]:.2f} g"
        lab(name, (-101 + g[0], g[1], z), (-34, 0), a)
    a = ramp(t, 0.3, 0.6) * (1 - ramp(t, 3.6, 4.0))
    lab("Rotating-and-tapping sieve shaker", (175, -150, 120), (40, 40), a)
    a = ramp(t, 7.6, 7.9) * (1 - ramp(t, 10.2, 10.5))
    lab("Tapping hammer on the lid", (0, 0, CORK_TOP + 30), (60, -30), a)

    # ---- readouts
    if t >= 4.2:
        readouts.append(Readout("SAMPLE", f"{SAMPLE:.2f} g"))
    if t >= T_SHAKE0 - 0.3:
        el_s = np.clip((t - T_SHAKE0) / (T_SHAKE1 - T_SHAKE0), 0, 1) * 15 * 60
        readouts.append(Readout("SHAKER", f"{int(el_s // 60):2d}:{int(el_s % 60):02d}",
                                "#FFD166" if t >= T_SHAKE1 else "#7CFC9A"))
    if cur_w is not None:
        f = min(1.0, (t - (T_W0 + T_WSTEP * cur_w)) / 0.5)
        readouts.append(Readout(f"BALANCE: {BANDS[cur_w]} µm", f"{GRAMS[cur_w] * f:6.2f} g"))
    if t >= T_W0 + T_WSTEP * 6:
        readouts.append(Readout("TOTAL RECOVERED", f"{TOTAL:.2f} g", "#FFD166"))

    # ---- chart: % retained per band (bars) and cumulative % passing (line)
    def plot(fig):
        ax = fig.add_axes([0.12, 0.27, 0.76, 0.60])
        style_axes(ax, "Mass retained per size band")
        order_f = [5, 4, 3, 2, 1, 0]     # fine to coarse
        h = [PCT[d] if d in weighed else 0 for d in order_f]
        ax.bar(range(6), h, color=["#9aa5b1" if d == 5 else C["blue"] for d in order_f], width=0.68, zorder=2)
        for k, d in enumerate(order_f):
            if d in weighed:
                ax.text(k, PCT[d] + 1.5, f"{PCT[d]:.1f}", ha="center", fontsize=8, color="#222")
        a2 = ax.twinx()
        if len(weighed) == 6:
            cum = np.cumsum([PCT[d] for d in order_f])
            a2.plot(range(6), cum, color=C["orange"], marker="o", ms=4, lw=2, zorder=3)
        a2.set_ylim(0, 105)
        a2.set_ylabel("cumulative % passing", fontsize=9, color=C["orange"])
        a2.tick_params(labelsize=8, colors=C["orange"])
        a2.spines["top"].set_visible(False)
        a2.spines["right"].set_color(C["orange"])
        ax.set_xticks(range(6))
        ax.set_xticklabels([BANDS[d] for d in order_f], fontsize=8)
        ax.set_ylim(0, 50)
        ax.set_ylabel("mass % retained")
        ax.set_xlabel("size band (µm)")
    img = chart.draw(plot)
    speed = "15 min shown in 9 s" if T_SHAKE0 <= t < T_SHAKE1 else ""
    ov = Overlay("Sieve analysis", "Size distribution of metal powders above about 45 µm, by mass",
                 "ASTM B214", "ASTM E11 sieves", labels=labels, readouts=readouts, chart=img,
                 step_idx=i, n_steps=len(TL.steps), step_text=step.text, speed_note=speed,
                 footer="Schematic; dimensions approximate; values illustrative; dots = equal-mass parcels")
    return compose(rgb, ov, st)


if __name__ == "__main__":
    run(frame, NAME, TL.duration, gif_fps=8, gif_width=560, gif_colors=112)
