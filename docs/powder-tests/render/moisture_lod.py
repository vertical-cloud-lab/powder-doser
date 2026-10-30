"""Moisture by loss on drying (LOD), gravimetric oven method as in USP <731>.

Weigh a dried, empty weighing bottle; add about 10 g of powder from the jar that is being
dosed and weigh again; dry with the lid off at 105 °C; close, cool in a desiccator and
reweigh; repeat an extra hour of drying until two weighings agree (USP: within 0.50 mg per
g of sample). LOD = mass lost / moist sample mass. Log room T/RH with the result, since
hygroscopic powders pick up water between sampling and weighing. Values illustrative.
"""
from common import *  # noqa: F401,F403

NAME = "moisture_lod"
M_BOT = 24.8316            # g, dried empty bottle + lid
M_WET = 34.8457            # g, bottle + lid + moist sample
M_2H = 34.8189             # after 2 h at 105 °C
M_3H = 34.8186             # after one more hour: change 0.3 mg < 0.50 mg/g x 10 g
SAMPLE = M_WET - M_BOT
LOD = (M_WET - M_3H) / SAMPLE * 100

TL = Timeline([
    Step(0.0, 3.6, "Lay out: analytical balance, oven at 105 °C, desiccator, T/RH logger"),
    Step(3.6, 6.6, "Weigh the dried, empty weighing bottle with its lid"),
    Step(6.6, 9.6, "Add about 10 g from the jar being dosed, spread thin, weigh"),
    Step(9.6, 11.2, "Into the oven with the lid off"),
    Step(11.2, 15.6, "Dry at 105 °C: water and other volatiles leave the powder"),
    Step(15.6, 18.2, "Lid on, cool to room temperature in the desiccator"),
    Step(18.2, 20.6, "Reweigh"),
    Step(20.6, 24.0, "Dry 1 h more, cool, reweigh: repeat until two weighings agree"),
    Step(24.0, 28.5, "LOD = mass lost ÷ moist sample mass; record T/RH with it"),
])

st = Stage(bench=(-420, 400, -300, 280))

# ---- analytical balance with a glass draft shield whose top slides open
BAL = np.array([-250.0, 70.0])
st.add("bal_body", box(BAL[0] - 105, BAL[0] + 105, BAL[1] - 150, BAL[1] + 140, 0, 82), "white")
st.add("bal_disp", box(BAL[0] - 70, BAL[0] + 70, BAL[1] - 152, BAL[1] - 148, 18, 62), "lcd")
st.add("bal_pan", disc(46, 84, 88).translate((BAL[0], BAL[1] + 20, 0), inplace=False), "steel")
SH = dict(x0=BAL[0] - 100, x1=BAL[0] + 100, y0=BAL[1] - 85, y1=BAL[1] + 135, z0=82, z1=290)
for nm, b in (("sh_l", (SH["x0"], SH["x0"] + 4, SH["y0"], SH["y1"], SH["z0"], SH["z1"])),
              ("sh_r", (SH["x1"] - 4, SH["x1"], SH["y0"], SH["y1"], SH["z0"], SH["z1"])),
              ("sh_f", (SH["x0"], SH["x1"], SH["y0"], SH["y0"] + 4, SH["z0"], SH["z1"])),
              ("sh_b", (SH["x0"], SH["x1"], SH["y1"] - 4, SH["y1"], SH["z0"], SH["z1"]))):
    st.add(nm, box(*b), "glass", opacity=0.18)
st.add("sh_top", box(SH["x0"], SH["x1"], SH["y0"], SH["y1"], SH["z1"], SH["z1"] + 4), "glass", opacity=0.22)
st.add("sh_frame", box(SH["x0"] - 4, SH["x1"] + 4, SH["y1"] - 6, SH["y1"] + 2, SH["z0"], SH["z1"] + 8), "white")
P_BAL = np.array([BAL[0], BAL[1] + 20, 88.5])

# ---- drying oven: hollow body, hinged door with a window, warm interior when heating
OV = dict(x0=60, x1=340, y0=-20, y1=240, z0=0, z1=250, t=14)
o = OV
for nm, b in (("ov_l", (o["x0"], o["x0"] + o["t"], o["y0"], o["y1"], o["z0"], o["z1"])),
              ("ov_r", (o["x1"] - o["t"], o["x1"], o["y0"], o["y1"], o["z0"], o["z1"])),
              ("ov_t", (o["x0"], o["x1"], o["y0"], o["y1"], o["z1"] - o["t"], o["z1"])),
              ("ov_bt", (o["x0"], o["x1"], o["y0"], o["y1"], o["z0"], o["z0"] + o["t"]))):
    st.add(nm, box(*b), "light")
st.add("ov_back", box(o["x0"], o["x1"], o["y1"] - o["t"], o["y1"], o["z0"], o["z1"]), "light")
st.add("ov_inner", box(o["x0"] + o["t"], o["x1"] - o["t"], o["y1"] - o["t"] - 1, o["y1"] - o["t"],
                       o["z0"] + o["t"], o["z1"] - o["t"]), "steel", color="#c9ccd0")
st.add("ov_panel", box(o["x0"], o["x1"], o["y0"] - 4, o["y1"], o["z1"], o["z1"] + 42), "mid")
st.add("ov_disp", box(o["x1"] - 110, o["x1"] - 20, o["y0"] - 6, o["y0"] - 4, o["z1"] + 10, o["z1"] + 32), "lcd")
SHELF_Z = 96.0
shelf = box(o["x0"] + o["t"], o["x1"] - o["t"], o["y0"] + 10, o["y1"] - o["t"], SHELF_Z - 3, SHELF_Z)
st.add("ov_shelf", shelf, "steel")
WIN = (o["x0"] + 60, o["x1"] - 60, 70, 200)
door = box(o["x0"], o["x1"], o["y0"] - 16, o["y0"], o["z0"], WIN[2]).merge(
    box(o["x0"], o["x1"], o["y0"] - 16, o["y0"], WIN[3], o["z1"])).merge(
    box(o["x0"], WIN[0], o["y0"] - 16, o["y0"], WIN[2], WIN[3])).merge(
    box(WIN[1], o["x1"], o["y0"] - 16, o["y0"], WIN[2], WIN[3]))
st.add("ov_door", door, "light")
st.add("ov_win", box(WIN[0], WIN[1], o["y0"] - 10, o["y0"] - 6, WIN[2], WIN[3]), "glass", opacity=0.22)
st.add("ov_handle", rod((o["x1"] - 22, o["y0"] - 30, 90), (o["x1"] - 22, o["y0"] - 30, 170), 5), "steel_dark")
HINGE = (o["x0"], o["y0"] - 8, 0)
P_OVEN = np.array([180.0, 110.0, SHELF_Z])

# ---- glass desiccator with a sliding lid, perforated plate and desiccant
DES = np.array([-30.0, -150.0])
bowl = lathe([(0, 0), (88, 0), (98, 40), (104, 112), (112, 118), (112, 124), (96, 124), (90, 46), (80, 6), (0, 6)])
st.add("des_bowl", bowl.translate((DES[0], DES[1], 0), inplace=False), "glass", opacity=0.30)
st.add("des_dry", lathe([(0, 6), (80, 6), (86, 30), (0, 30)]).translate((DES[0], DES[1], 0), inplace=False),
       "blue", color="#4b78c6")
st.add("des_plate", disc(92, 44, 49).translate((DES[0], DES[1], 0), inplace=False), "white")
lid = lathe([(0, 186), (30, 182), (80, 160), (110, 130), (112, 124), (104, 124), (102, 130), (74, 156), (26, 176), (0, 180)])
lid = lid.merge(disc(16, 184, 202))
st.add("des_lid", lid.translate((DES[0], DES[1], 0), inplace=False), "glass", opacity=0.30)
P_DES = np.array([DES[0], DES[1], 49.0])

# ---- T/RH logger and the powder jar
st.add("logger", box(-380, -300, -260, -230, 0, 120), "white")
st.add("logger_disp", box(-372, -308, -262, -260, 50, 100), "lcd")
st.add("jar", lathe([(0, 0), (38, 0), (38, 90), (30, 96), (30, 104), (0, 104)]).translate((-110, -250, 0), inplace=False),
       "glass", opacity=0.35)
st.add("jar_salt", lathe([(0, 2), (35, 2), (35, 60), (0, 64)]).translate((-110, -250, 0), inplace=False), "salt")

# ---- weighing bottle (local frame: base at origin), lid, sample layer
bottle = lathe([(0, 0), (25, 0), (25, 34), (23.4, 34), (23.4, 1.6), (0, 1.6)])
st.add("bottle", bottle, "glass", opacity=0.38)
st.add("blid", lathe([(0, 0), (27, 0), (27, 6), (8, 7), (8, 13), (0, 13)]), "glass", opacity=0.42)
for nm, (cx, cy, rx) in {"sh_bal": (BAL[0], BAL[1] - 5, 140), "sh_ov": (200, 110, 190), "sh_des": (DES[0], DES[1], 125),
                         "sh_log": (-340, -245, 60), "sh_jar": (-110, -250, 55)}.items():
    st.shadow(nm, (cx, cy), rx, rx * 0.8, 0.30)

SALT_COLS = grain_colors(4000, C["salt"], 0.06, seed=4)
VAPOR = np.random.default_rng(11).random((500, 4))
chart = Chart()


def path(t, keys):
    """Piecewise motion through (time, xyz) keys with smoothstep easing per segment."""
    for (t0, p0), (t1, p1) in zip(keys[:-1], keys[1:]):
        if t <= t1:
            return lerp(p0, p1, ramp(t, t0, t1))
    return np.asarray(keys[-1][1], float)


UP = np.array([0, 0, 260.0])
DOOR_FRONT = np.array([P_OVEN[0], -150.0, SHELF_Z + 40])
BOTTLE_KEYS = [
    (0.0, P_DES), (3.8, P_DES), (4.3, P_DES + [0, 0, 150]), (4.9, P_BAL + UP), (5.4, P_BAL),
    (9.7, P_BAL), (10.0, P_BAL + UP), (10.5, DOOR_FRONT), (11.0, P_OVEN),
    (15.7, P_OVEN), (16.1, DOOR_FRONT), (16.6, P_DES + [0, 0, 150]), (17.0, P_DES),
    (18.3, P_DES), (18.6, P_DES + [0, 0, 150]), (19.1, P_BAL + UP), (19.5, P_BAL),
    (20.7, P_BAL), (21.0, P_BAL + UP), (21.4, DOOR_FRONT), (21.7, P_OVEN),
    (22.3, P_OVEN), (22.6, DOOR_FRONT), (22.9, P_DES + [0, 0, 150]), (23.1, P_DES),
    (23.2, P_DES), (23.4, P_DES + [0, 0, 150]), (23.7, P_BAL + UP), (24.0, P_BAL),
]
DRY = [(11.0, 15.6), (21.7, 22.3)]       # lid off, in the oven
COOL = [(17.0, 18.3), (23.1, 23.2)]      # lid on, in the desiccator


def in_any(t, spans):
    return any(a <= t <= b for a, b in spans)


CAM = [  # (t, focal, dist, azimuth, elevation)
    (0.0, (-20, 0, 100), 2100, -30, 30), (3.4, (-20, 0, 100), 1950, -18, 30),
    (3.8, (P_BAL[0], P_BAL[1], 150), 1050, -14, 24), (9.6, (P_BAL[0], P_BAL[1], 150), 1000, -8, 24),
    (10.2, (40, 0, 120), 1700, -10, 26), (11.2, (200, 80, 130), 1050, -10, 16),
    (15.6, (200, 80, 130), 1020, -4, 16), (16.4, (DES[0], DES[1] + 40, 100), 1050, -8, 30),
    (18.0, (DES[0], DES[1] + 40, 100), 1030, -2, 30), (18.6, (P_BAL[0], P_BAL[1], 150), 1050, -10, 24),
    (20.6, (P_BAL[0], P_BAL[1], 150), 1020, -6, 24), (21.2, (-20, 0, 100), 1900, -12, 30),
    (28.5, (-20, 0, 100), 1850, 2, 30),
]


def camera(t):
    for (t0, f0, d0, a0, e0), (t1, f1, d1, a1, e1) in zip(CAM[:-1], CAM[1:]):
        if t <= t1:
            s = ramp(t, t0, min(t1, t0 + 0.9)) if (t1 - t0) < 2 else lin(t, t0, t1)
            return lerp(f0, f1, s), d0 + (d1 - d0) * s, a0 + (a1 - a0) * s, e0 + (e1 - e0) * s
    t0, f0, d0, a0, e0 = CAM[-1]
    return np.asarray(f0, float), d0, a0, e0


def balance_reading(t):
    on = np.linalg.norm(path(t, BOTTLE_KEYS) - P_BAL) < 0.5
    if not on:
        return "0.0000 g"
    if t < 6.8:
        return f"{M_BOT:.4f} g"
    if t < 9.7:
        return f"{M_BOT + (M_WET - M_BOT) * ramp(t, 7.0, 8.6):.4f} g"
    if t < 20.7:
        return f"{M_2H:.4f} g"
    return f"{M_3H:.4f} g"


def frame(t):
    i, step = TL.current(t)
    labels, readouts = [], []
    # assembly: everything eases in during step 1
    groups = [(("bal_body", "bal_disp", "bal_pan", "sh_l", "sh_r", "sh_f", "sh_b", "sh_top", "sh_frame"), 0.2, (0, 0, 120)),
              (("ov_l", "ov_r", "ov_t", "ov_bt", "ov_back", "ov_inner", "ov_panel", "ov_disp", "ov_shelf", "ov_door",
                "ov_win", "ov_handle"), 0.8, (0, 0, 140)),
              (("des_bowl", "des_dry", "des_plate", "des_lid"), 1.4, (0, 0, 120)),
              (("logger", "logger_disp", "jar", "jar_salt"), 2.0, (0, 0, 100))]
    for names, t0, off in groups:
        M, vis, _ = arrive(t, t0, offset=off)
        for nm in names:
            st.pose(nm, M, vis)

    # sliding draft-shield top: open when the bottle passes through
    near_bal = any(a - 0.4 <= t <= b + 0.4 for a, b in ((4.3, 5.4), (9.7, 10.0), (18.6, 19.5), (20.7, 21.0), (23.4, 24.0)))
    sh_open = ramp(t, 3.9, 4.3) * (1 - ramp(t, 5.5, 5.9)) + ramp(t, 9.5, 9.75) * (1 - ramp(t, 10.05, 10.3)) \
        + ramp(t, 18.3, 18.6) * (1 - ramp(t, 19.6, 19.9)) + ramp(t, 20.55, 20.75) * (1 - ramp(t, 21.05, 21.3)) \
        + ramp(t, 23.2, 23.45) * (1 - ramp(t, 24.1, 24.4))
    if t >= 0.2 + 0.9:
        st.pose("sh_top", matrix(translate=(0, 200 * min(1.0, sh_open), 0)), True)
    _ = near_bal
    # oven door: hinge swing when loading/unloading
    door = ramp(t, 10.0, 10.5) * (1 - ramp(t, 11.1, 11.6)) + ramp(t, 15.3, 15.7) * (1 - ramp(t, 16.2, 16.7)) \
        + ramp(t, 21.0, 21.3) * (1 - ramp(t, 21.75, 22.0)) + ramp(t, 22.15, 22.35) * (1 - ramp(t, 22.65, 22.9))
    if t >= 0.8 + 0.9:
        Md = matrix(rot_deg=-105 * door, axis=(0, 0, 1), origin=HINGE)
        st.pose("ov_door", Md, True)
        st.pose("ov_win", Md, True)
        st.pose("ov_handle", Md, True)
    heating = in_any(t, DRY)
    st.pose("ov_inner", None, t >= 0.8)
    st.pl.actors["ov_inner"].prop.color = "#ffcf8a" if heating else "#c9ccd0"
    # desiccator lid slides aside when the bottle goes in or out
    dl = ramp(t, 3.4, 3.8) * (1 - ramp(t, 4.4, 4.8)) + ramp(t, 16.2, 16.6) * (1 - ramp(t, 17.05, 17.45)) \
        + ramp(t, 18.0, 18.3) * (1 - ramp(t, 18.65, 19.0)) + ramp(t, 22.5, 22.8) * (1 - ramp(t, 23.45, 23.7))
    if t >= 1.4 + 0.9:
        st.pose("des_lid", matrix(translate=(150 * min(1.0, dl), 40 * min(1.0, dl), 0)), True)

    # weighing bottle, lid and sample
    p = path(t, BOTTLE_KEYS)
    vis_b = t >= 2.4
    Mb = matrix(translate=p)
    st.pose("bottle", Mb, vis_b)
    lid_off = in_any(t, [(10.7, 15.65), (21.5, 22.35)]) or (6.7 <= t <= 8.8)
    if lid_off and 10.0 < t:
        lp = p + [58, 0, 0] if np.linalg.norm(p - P_OVEN) < 1 else p + [0, 0, 34]
    elif lid_off:
        lp = P_BAL + [72, -10, 0] if np.linalg.norm(p - P_BAL) < 1 else p + [0, 0, 34]
    else:
        lp = p + [0, 0, 34]
    st.pose("blid", matrix(translate=lp), vis_b)
    fill = ramp(t, 7.0, 8.6) if t < 9.0 else 1.0
    if vis_b and fill > 0.01:
        layer = disc(23.2, 1.7, 1.7 + 7.0 * fill)
        st.add("sample", layer.translate(p, inplace=False), "salt")
        gp = surface_grains(1500, 23.0, lambda r, th: 1.7 + 7.0 * fill + 0 * r, seed=5, lift=0.1)()
        st.grains("sample_g", gp + p, SALT_COLS[:1500], size=3.0, mat="salt")
    else:
        st.remove("sample")
        st.remove("sample_g")
    # scoop pouring from the jar into the bottle on the pan
    pts = []
    if 6.8 <= t <= 8.8:
        st.add("scoop", lathe([(0, 0), (16, 0), (18, 7), (16.6, 7), (14.8, 1.2), (0, 1.2)]).merge(
            rod((18, 0, 4), (90, 0, 30), 2.5)), "steel")
        s_in = ramp(t, 6.8, 7.1) * (1 - ramp(t, 8.6, 8.8))
        Ms = matrix(translate=P_BAL + [-14 - 80 * (1 - s_in), 0, 70]) @ matrix(rot_deg=55 * ramp(t, 7.0, 7.3), axis=(0, 1, 0), origin=(0, 0, 3))
        st.pose("scoop", Ms, True)
        q, _ = stream(t, 7.1, 8.5, 500, P_BAL + [-2, 0, 66], 4.0, v0=30, floor=lambda x, y: P_BAL[2] + 9 + 0 * x, seed=3)
        pts.append(q)
    else:
        st.remove("scoop")
    # water vapour leaving the sample while it dries
    if heating:
        tt = (t - (11.2 if t < 20 else 21.7)) * 0.8
        ph = (VAPOR[:, 0] + tt) % 1.0
        vx = p[0] + (VAPOR[:, 1] - 0.5) * 36 + 8 * np.sin(6 * ph + VAPOR[:, 2] * 6)
        vy = p[1] + (VAPOR[:, 2] - 0.5) * 36
        vz = p[2] + 10 + ph * 120
        pts_v = np.c_[vx, vy, vz][VAPOR[:, 3] < 0.6]
        st.grains("vapor", pts_v, None, size=3.0, mat="white")
        st.pl.actors["vapor"].prop.opacity = 0.35
    else:
        st.remove("vapor")
    P = np.vstack(pts) if pts else np.empty((0, 3))
    st.grains("stream", P, SALT_COLS[: len(P)], size=3.0, mat="salt")

    f, dist, az, el = camera(t)
    st.orbit(f, dist, az, el)
    st.pl.camera.SetWindowCenter(0.28, -0.04)
    rgb = st.render()

    def lab(text, xyz, off, t0, t1):
        a = ramp(t, t0, t0 + 0.4) * (1 - ramp(t, t1 - 0.4, t1))
        if a > 0:
            labels.append(Label(text, xyz, off, a))
    lab("Analytical balance, 0.1 mg", (BAL[0], BAL[1] - 85, 290), (40, -50), 0.6, 3.6)
    lab("Drying oven, 105 °C", (o["x0"] + 60, o["y0"], o["z1"] + 40), (-40, -48), 1.2, 3.6)
    lab("Desiccator", (DES[0] - 100, DES[1], 90), (-60, 50), 1.8, 3.6)
    lab("T/RH logger", (-340, -260, 120), (-30, -60), 2.4, 3.6)
    lab("Weighing bottle + lid", (P_BAL[0] - 25, P_BAL[1], P_BAL[2] + 40), (-90, -50), 4.6, 6.6)
    lab("Lid off while drying", (P_OVEN[0] + 58, P_OVEN[1], P_OVEN[2] + 8), (60, -70), 11.6, 14.4)
    lab("Desiccant keeps the cooling sample dry", (DES[0] + 40, DES[1], 20), (60, 50), 16.8, 18.2)

    readouts.append(Readout("BALANCE", balance_reading(t)))
    oven_T = 105.0
    readouts.append(Readout("OVEN", f"{oven_T:.0f} °C", "#FFB347"))
    if 11.2 <= t <= 15.6:
        hrs = 2.0 * lin(t, 11.2, 15.6)
    elif t > 15.6:
        hrs = 2.0 + (1.0 * lin(t, 21.7, 22.3) if t >= 21.7 else 0.0)
    else:
        hrs = 0.0
    readouts.append(Readout("DRYING TIME", f"{int(hrs)} h {int(round((hrs % 1) * 60)) % 60:02d} min"))
    readouts.append(Readout("ROOM", "22.4 °C · 31 %RH", "#9AD0FF"))
    if t >= 24.3:
        readouts.append(Readout("LOSS ON DRYING", f"{LOD:.2f} %", "#FFD166"))

    def plot(fig):
        ax = fig.add_axes([0.15, 0.17, 0.80, 0.70])
        style_axes(ax, "Mass lost by the sample")
        tt = np.linspace(0, 3.2, 200)
        loss_model = (M_WET - M_3H) * 1000 * (1 - np.exp(-tt / 0.45))
        ax.plot(tt, loss_model, color="#9aa3ad", lw=1.4, ls="--", label="typical drying curve")
        pts_t, pts_m = [0.0], [0.0]
        if t >= 19.6:
            pts_t.append(2.0)
            pts_m.append((M_WET - M_2H) * 1000)
        if t >= 24.1:
            pts_t.append(3.0)
            pts_m.append((M_WET - M_3H) * 1000)
        if t >= 8.8:
            ax.plot(pts_t, pts_m, "o", color=C["blue"], ms=7, label="weighings", zorder=5)
        if t >= 24.1:
            ax.annotate("constant mass:\n0.3 mg change < 0.50 mg/g", xy=(3.0, (M_WET - M_3H) * 1000), xytext=(1.05, 9),
                        fontsize=8.5, arrowprops=dict(arrowstyle="->", color="#444"))
        ax.set_xlim(0, 3.3)
        ax.set_ylim(0, 34)
        ax.set_xlabel("time at 105 °C (h)")
        ax.set_ylabel("mass lost (mg)")
        ax.legend(fontsize=8, loc="lower right", frameon=False)
    img = chart.draw(plot)
    ov = Overlay("Moisture by loss on drying", "Mass lost on drying at 105 °C, as % of the moist sample",
                 "USP <731>", "gravimetric", labels=labels, readouts=readouts, chart=img,
                 step_idx=i, n_steps=len(TL.steps), step_text=step.text,
                 speed_note="time-lapse" if 11.2 <= t <= 24.0 else "",
                 footer="Schematic; dimensions approximate; values illustrative (table salt)")
    return compose(rgb, ov, st)


if __name__ == "__main__":
    run(frame, NAME, TL.duration, gif_fps=10)
