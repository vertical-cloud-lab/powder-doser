"""Angle of repose, fixed-funnel method (ISO 4324; USP <1174> fixed-base cone).

Powder runs through a funnel clamped at a fixed height over a flat base of fixed diameter.
The cone grows until it covers the base; after that its height stops rising and the excess
rolls off the edge. The angle of repose is arctan(h / r) for cone height h on base radius r.
A cohesive powder builds a steeper, rougher cone. Values are illustrative.
"""
from common import *  # noqa: F401,F403

NAME = "angle_of_repose"
R = 40.0                         # base radius (80 mm base)
TRAY_R, TRAY_FLOOR = 78.0, 1.5
Z_B = 25.0                       # top of the base (pedestal)
Z_O = Z_B + 60.0                 # funnel outlet, fixed height above the base
PROF, FG = funnel_geom(Z_O, 4.0, r_top=36.0, l_orifice=22.0, wall=2.0, lip_h=4.0, lip_w=3.0)
ROD = np.array([0.0, 92.0])      # ring-stand rod (x, y)
CLAMP_Z = FG["z_ct"] - 6.0

RUNS = [  # (label, colour, angle deg, excess fraction, pour window)
    dict(name="316L (free-flowing)", col="#7c838b", ang=32.0, excess=0.35, t0=3.8, t1=9.4, rough=0.0),
    dict(name="AlSi10Mg (cohesive)", col="#aeb3b9", ang=47.0, excess=0.25, t0=15.9, t1=20.3, rough=1.0),
]
for r_ in RUNS:
    r_["tan"] = math.tan(math.radians(r_["ang"]))
    r_["vmax"] = math.pi / 3 * R ** 3 * r_["tan"]
    r_["vtot"] = r_["vmax"] * (1 + r_["excess"])
    r_["hmax"] = R * r_["tan"]

USP = [(25, 30, "excellent", "#2e9e5b"), (31, 35, "good", "#7cc36a"), (36, 40, "fair", "#d8d65a"),
       (41, 45, "passable", "#f0b44c"), (46, 55, "poor", "#e98a3c"), (56, 65, "very poor", "#d9573a"),
       (66, 75, "very, very poor", "#a8322d")]

TL = Timeline([
    Step(0.0, 3.4, "Assemble: fixed-diameter base, funnel clamped at a fixed height"),
    Step(3.4, 7.4, "Pour powder through the funnel; a cone builds on the base"),
    Step(7.4, 10.0, "Once the cone covers the base, the excess rolls off the edge"),
    Step(10.0, 14.2, "Measure the cone height h: angle of repose = arctan(h / r)"),
    Step(14.2, 15.8, "Clear the base; repeat with a cohesive powder (e.g. AlSi10Mg)"),
    Step(15.8, 20.6, "A cohesive powder builds a steeper, rougher cone"),
    Step(20.6, 24.4, "Steeper cone, larger angle: 47° ('poor') vs 32° ('good')"),
    Step(24.4, 27.5, "Rank on the USP <1174> flow scale: lower angle, freer flow"),
])

st = Stage()
st.add("tray", lathe([(0, 0), (TRAY_R + 2, 0), (TRAY_R + 2, 9), (TRAY_R, 9), (TRAY_R, TRAY_FLOOR), (0, TRAY_FLOOR)]), "steel")
st.add("pedestal", lathe([(0, TRAY_FLOOR), (R, TRAY_FLOOR), (R, Z_B), (0, Z_B)]), "light")
st.add("stand_base", box(-50, 50, ROD[1] - 30, ROD[1] + 30, 0, 10), "dark")
st.add("rod", rod((ROD[0], ROD[1], 10), (ROD[0], ROD[1], FG["lip_top"] + 45), 6), "steel")
st.add("boss", cbox((ROD[0], ROD[1], CLAMP_Z + 2), (22, 22, 20)), "steel_dark")
arm_y0 = FG["r_lip"] + 7
st.add("clamp_arm", rod((0, ROD[1], CLAMP_Z + 2), (0, arm_y0, CLAMP_Z + 2), 4.5), "steel_dark")
st.add("clamp_ring", tube(FG["r_lip"] - 1.5, FG["r_lip"] + 7, CLAMP_Z - 2, CLAMP_Z + 6), "steel_dark")
st.add("funnel", lathe(PROF), "glass", opacity=0.35)
st.add("beaker", lathe([(0, 0), (24, 0), (24, 46), (27, 50), (25.6, 50), (22.6, 46.5), (22.6, 1.6), (0, 1.6)]), "glass",
       opacity=0.4)
st.shadow("sh_tray", (0, 0), 110, 110, 0.32)
st.shadow("sh_stand", (0, ROD[1]), 75, 45, 0.3)
chart = Chart()
rng = np.random.default_rng(7)
N_SURF = 2600
SURF_R = np.sqrt(rng.uniform(0, 1, N_SURF)) * R
SURF_PH = rng.uniform(0, 2 * np.pi, N_SURF)
CLUMP = rng.random(N_SURF) < 0.06


def noise(r, ph, k):
    """Rough-surface perturbation for the cohesive cone (zero at the apex)."""
    f = np.clip(r / R, 0, 1)
    return k * f * (1.7 * np.sin(3 * ph + 0.15 * r) + 1.2 * np.sin(7 * ph - 0.22 * r + 1.3)
                    + 0.8 * np.sin(11 * ph + 0.4 * r + 0.4))


def pile_state(run, t):
    Vp = run["vtot"] * lin(t, run["t0"], run["t1"])
    Vpile = min(Vp, run["vmax"])
    a = (3 * Vpile * run["tan"] ** 2 / math.pi) ** (1 / 3) if Vpile > 0 else 0.0
    return Vp, Vpile, a, max(0.0, Vp - run["vmax"])


def ring_heap(V, tan_t):
    if V <= 1.0:
        return 0.0, 0.0
    lo, hi = 0.0, TRAY_R - R
    for _ in range(40):
        L = 0.5 * (lo + hi)
        v = 2 * math.pi * tan_t * (R * L ** 2 / 2 + L ** 3 / 6)
        lo, hi = (L, hi) if v < V else (lo, L)
    return L, L * tan_t


def rollers(t, run, a, rate=70, seed=0):
    """Grains running down the cone flank; past the rim they fly off and drop into the tray."""
    t0, t1 = run["t0"] + 0.4, run["t1"]
    if t <= t0:
        return np.empty((0, 3))
    i_last = int((min(t, t1) - t0) * rate)
    i_first = max(0, int((t - t0 - 1.6) * rate))
    if i_last <= i_first:
        return np.empty((0, 3))
    u = np.random.default_rng(seed).random((i_last + 1, 2))
    idx = np.arange(i_first, i_last)
    tau = t - (t0 + idx / rate)
    ph = 2 * np.pi * u[idx, 0]
    acc = 60.0 + 40 * u[idx, 1]
    s = 0.5 * acc * tau ** 2 + 8 * tau                     # distance travelled along the slope
    cosb = 1 / math.sqrt(1 + run["tan"] ** 2)
    r = s * cosb
    rp = a / run["tan"] if a > 0 else 0.0
    z = Z_B + np.maximum(0.0, a - r * run["tan"]) + 0.6
    on = r < min(rp, R)
    pts = [np.c_[r[on] * np.cos(ph[on]), r[on] * np.sin(ph[on]), z[on]]]
    if rp >= R - 0.5:                                      # off the rim: ballistic
        off = r >= R
        if off.any():
            t_rim = (-8 + np.sqrt(64 + 2 * acc[off] * R / cosb)) / acc[off]
            dt = tau[off] - t_rim
            v_rim = (8 + acc[off] * t_rim)
            rr = R + v_rim * cosb * dt
            zz = Z_B - v_rim * math.sin(math.atan(run["tan"])) * dt - 0.5 * G_VIS * dt ** 2
            keep = zz > TRAY_FLOOR + 2
            pts.append(np.c_[rr[keep] * np.cos(ph[off][keep]), rr[keep] * np.sin(ph[off][keep]), zz[keep]])
    return np.vstack(pts)


def measure_overlay(img, run, alpha):
    """Dimension lines, angle arc and the arctan(h/r) result over the side view."""
    if alpha <= 0:
        return img
    d = ImageDraw.Draw(img, "RGBA")
    a8 = int(255 * alpha)
    h = run["hmax"]
    apex = st.project((0, 0, Z_B + h))
    foot = st.project((0, 0, Z_B))
    right = st.project((R, 0, Z_B))
    left = st.project((-R, 0, Z_B))
    col = (224, 122, 31, a8)
    dark = (25, 28, 33, a8)
    d.line([left, right], fill=dark, width=2)
    d.line([foot, apex], fill=col, width=3)
    d.line([right, apex], fill=(47, 109, 181, a8), width=3)
    rad = 70
    ang = math.degrees(math.atan2(apex[1] - right[1], apex[0] - right[0]))
    d.arc((right[0] - rad, right[1] - rad, right[0] + rad, right[1] + rad), start=180, end=ang % 360, fill=col, width=3)
    f1, f2 = font(18, bold=True), font(17, bold=True)

    def tag(xy, text, fnt, fg):
        w_ = d.textlength(text, font=fnt)
        d.rounded_rectangle((xy[0] - 6, xy[1] - 3, xy[0] + w_ + 6, xy[1] + 23), radius=6,
                            fill=(255, 255, 255, int(0.9 * a8)))
        d.text(xy, text, font=fnt, fill=fg)
    tag((foot[0] + 10, (foot[1] + apex[1]) / 2 - 12), f"h = {h:.1f} mm", f1, col)
    tag(((foot[0] + right[0]) / 2 - 30, foot[1] + 10), f"r = {R:.0f} mm", f1, dark)
    tag((right[0] + 14, right[1] - 34), f"{run['ang']:.0f}°", f2, col)
    txt = f"θ = arctan(h / r) = arctan({h:.1f} / {R:.0f}) = {run['ang']:.0f}°"
    tw = d.textlength(txt, font=f1)
    x0, y0 = left[0] - 10, apex[1] - 70
    d.rounded_rectangle((x0, y0, x0 + tw + 24, y0 + 36), radius=9, fill=(255, 255, 255, int(0.92 * a8)),
                        outline=(30, 34, 40, int(0.4 * a8)))
    d.text((x0 + 12, y0 + 7), txt, font=f1, fill=dark)
    return img


def frame(t):
    i, step = TL.current(t)
    labels, readouts = [], []

    # ---- assembly
    for nm, t0, off in (("tray", 0.1, (0, 0, 60)), ("pedestal", 0.5, (0, 0, 90)), ("stand_base", 0.9, (0, 0, 60)),
                        ("rod", 1.1, (0, 0, 140)), ("boss", 1.5, (0, 0, 80)), ("clamp_arm", 1.5, (0, 0, 80)),
                        ("clamp_ring", 1.5, (0, 0, 80)), ("funnel", 2.0, (0, 0, 110))):
        M, vis, _ = arrive(t, t0, offset=off)
        st.pose(nm, M, vis)
    st.pose("sh_tray", None, t >= 0.3)
    st.pose("sh_stand", None, t >= 1.0)

    run = RUNS[0] if t < 14.2 else RUNS[1]
    Vp, Vpile, a, Vspill = pile_state(run, t)
    clear = ramp(t, 14.25, 15.0) if t < 15.6 else 0.0
    if 14.2 <= t < 15.6:                     # first pile being cleared
        run_c = RUNS[0]
        Vp, Vpile, a, Vspill = pile_state(run_c, t)
        a *= (1 - clear)
        Vspill *= (1 - clear)
        run = run_c

    # ---- beaker pours into the funnel
    pour_on = [(r_["t0"] - 0.3, r_["t1"]) for r_ in RUNS]
    b_vis = False
    for (p0, p1) in pour_on:
        if p0 - 0.6 <= t <= p1 + 0.6:
            s_in, s_out = ramp(t, p0 - 0.6, p0), ramp(t, p1, p1 + 0.6)
            tilt = ramp(t, p0, p0 + 0.35) * (1 - ramp(t, p1 - 0.3, p1))
            M_b = matrix(translate=(-39, -8, FG["lip_top"] + 5)) @ matrix(rot_deg=62 * tilt, axis=(0, 1, 0),
                                                                         origin=(25, 0, 50))
            M_b = matrix(translate=(-170 * (1 - s_in) - 170 * s_out, 0, 30 * (1 - s_in) + 30 * s_out)) @ M_b
            st.pose("beaker", M_b, True)
            b_vis = True
    if not b_vis:
        st.pose("beaker", None, False)

    # funnel buffer of powder
    buf = 0.0
    for r_ in RUNS:
        buf = max(buf, ramp(t, r_["t0"] - 0.1, r_["t0"] + 0.4) * (1 - ramp(t, r_["t1"] - 0.2, r_["t1"] + 0.5)))
    if buf > 0.02:
        st.add("fill", funnel_fill(9000 * buf, FG, dip=3.0), "powder", color=run["col"])
    else:
        st.remove("fill")

    # ---- pile on the base
    k = run["rough"]
    if a > 0.2:
        rp = min(a / run["tan"], R)

        def zf(r, ph):
            return Z_B + np.maximum(0.0, a - r * run["tan"] + (noise(r, ph, 1.0) if k else 0.0) * min(1, a / 8))
        surf = polar_surface(zf, rp, nr=44, nth=120)
        st.add("pile", surf, "powder", color=run["col"])
        sel = SURF_R < rp * 0.98
        rr, pp = SURF_R[sel], SURF_PH[sel]
        zz = zf(rr, pp) + 0.35
        cols = grain_colors(len(rr), run["col"], 0.13, seed=3)
        st.grains("pile_grains", np.c_[rr * np.cos(pp), rr * np.sin(pp), zz], cols, size=3.0)
        if k and CLUMP[sel].any():
            c = CLUMP[sel]
            st.grains("clumps", np.c_[rr[c] * np.cos(pp[c]), rr[c] * np.sin(pp[c]), zz[c] + 0.6],
                      grain_colors(int(c.sum()), run["col"], 0.08, seed=4), size=7.0)
        else:
            st.remove("clumps")
    else:
        for nm in ("pile", "pile_grains", "clumps"):
            st.remove(nm)
    L, hw = ring_heap(Vspill, run["tan"])
    if L > 0.3:
        rr_ = np.linspace(R + L, R, 14)
        prof = [(R, TRAY_FLOOR), (R + L, TRAY_FLOOR)] + [(r, TRAY_FLOOR + max(0.05, hw - (r - R) * run["tan"])) for r in rr_]
        st.add("spill", lathe(prof), "powder", color=run["col"])
    else:
        st.remove("spill")

    # ---- grains: beaker -> funnel, funnel -> pile, rolling down the flank
    pts = []
    colsrc = grain_colors(4000, run["col"], 0.13, seed=9)
    for j, r_ in enumerate(RUNS):
        if r_["t0"] - 0.1 <= t <= r_["t1"] + 0.3:
            lvl = funnel_level(9000 * max(buf, 0.05), FG)
            p, _ = stream(t, r_["t0"] - 0.1, r_["t1"] - 0.3, 500, (-14, -8, FG["lip_top"] + 55), 2.5, v0=40,
                          floor=lambda x, y: lvl + 0 * x, seed=31 + j)
            pts.append(p)

            def floor_pile(x, y, a_=a, r__=r_):
                return Z_B + np.maximum(0.0, a_ - np.hypot(x, y) * r__["tan"])
            if j == 0:
                p, _ = stream(t, r_["t0"], r_["t1"], 900, (0, 0, Z_O), FG["r_o"] * 0.8, v0=80, floor=floor_pile,
                              max_fall=Z_O - Z_B, seed=41)
                pts.append(p)
            else:  # cohesive: flows in spurts
                span = r_["t1"] - r_["t0"]
                for q in range(5):
                    s0 = r_["t0"] + q * span / 5
                    p, _ = stream(t, s0, s0 + 0.55 * span / 5, 900, (0, 0, Z_O), FG["r_o"] * 0.8, v0=60,
                                  floor=floor_pile, max_fall=Z_O - Z_B, seed=50 + q)
                    pts.append(p)
            pts.append(rollers(t, r_, a, rate=80 if j == 0 else 35, seed=61 + j))
    P = np.vstack(pts) if pts else np.empty((0, 3))
    st.grains("stream", P, colsrc[: len(P)] if len(P) <= len(colsrc) else None, size=3.2)

    # ---- camera: orbit, then square side views for the two measurements
    side = max(ramp(t, 9.8, 10.8) * (1 - ramp(t, 13.8, 14.6)), ramp(t, 20.4, 21.4) * (1 - ramp(t, 24.2, 25.0)))
    az = (-30 + 22 * ramp(t, 0, 9.8) + 26 * ramp(t, 14.5, 20.4) + 14 * ramp(t, 24.4, 27.5))
    az = az * (1 - side)
    el = 22 - 4 * ramp(t, 3, 8)
    el = el * (1 - side) + 0.5 * side
    foc = lerp((0, 24, 84), (0, 0, Z_B + 24), side)
    dist = lerp(740 - 80 * ramp(t, 3.0, 6.0), 430, side)
    st.orbit(foc, dist, az, el)
    st.pl.camera.SetWindowCenter(0.30, -0.05 * (1 - side) + 0.06 * side)
    rgb = st.render()

    # ---- labels
    def lab(text, xyz, off, t0, t1):
        al = ramp(t, t0, t0 + 0.35) * (1 - ramp(t, t1 - 0.35, t1))
        if al > 0:
            labels.append(Label(text, xyz, off, al))
    lab("Fixed-diameter base (80 mm)", (-R * 0.8, -R * 0.6, Z_B), (-150, -14), 0.8, 4.5)
    lab("Funnel at a fixed height", (-FG["r_lip"] * 0.7, -FG["r_lip"] * 0.7, FG["lip_top"] - 4), (-110, -36), 2.3, 5.5)
    lab("Catch tray", (-(TRAY_R + 2) * 0.7, -(TRAY_R + 2) * 0.7, 9), (-40, 46), 0.6, 4.2)
    lab("Cone grows at a constant slope", (-a / run["tan"] * 0.5 if a > 0 else 0, -2, Z_B + a * 0.5), (-60, -80), 5.0, 7.4)
    lab("Height stops rising: excess rolls off", (-R * 0.75, -R * 0.66, Z_B + 2), (-30, 72), 7.8, 9.9)
    lab("Steeper, rougher cone", (-a / run["tan"] * 0.5 if a > 0 else 0, -2, Z_B + a * 0.5), (-70, -80), 17.5, 20.4)

    # ---- readouts
    if t >= 3.4:
        readouts.append(Readout("CONE HEIGHT", f"{a:5.1f} mm"))
    if t >= 12.0:
        readouts.append(Readout("316L", f"{RUNS[0]['ang']:.0f}° good", "#FFD166"))
    if t >= 22.4:
        readouts.append(Readout("AlSi10Mg", f"{RUNS[1]['ang']:.0f}° poor", "#FF9F6B"))

    # ---- chart: cone height vs volume poured, and the USP <1174> scale
    def plot(fig):
        ax = fig.add_axes([0.13, 0.50, 0.83, 0.38])
        style_axes(ax, "Cone height vs powder poured")
        for j, r_ in enumerate(RUNS):
            if t < r_["t0"]:
                continue
            vv = np.linspace(0, r_["vtot"], 200)
            hh = np.minimum((3 * vv * r_["tan"] ** 2 / math.pi) ** (1 / 3), r_["hmax"])
            cur = r_["vtot"] * lin(t, r_["t0"], r_["t1"])
            sel = vv <= cur
            colr = C["blue"] if j == 0 else C["orange"]
            ax.plot(vv[sel] / 1000, hh[sel], color=colr, lw=2.3, label=r_["name"])
            if t >= r_["t1"] + 1.5:
                ax.axhline(r_["hmax"], color=colr, lw=0.9, ls="--")
        ax.set_xlim(0, RUNS[1]["vtot"] / 1000 * 1.02)
        ax.set_ylim(0, 50)
        ax.set_xlabel("volume poured (cm³)", labelpad=1)
        ax.set_ylabel("height (mm)")
        if t >= RUNS[0]["t0"]:
            ax.legend(fontsize=7.5, loc="lower right", frameon=False)
        bx = fig.add_axes([0.13, 0.07, 0.83, 0.15])
        for lo, hi, nm, cc in USP:
            bx.barh(0, hi + 0.5 - (lo - 0.5), left=lo - 0.5, color=cc, height=1.0)
            bx.text((lo + hi) / 2, 0, nm, ha="center", va="center", fontsize=6.6 if len(nm) < 10 else 5.6,
                    color="#111", rotation=0)
        for j, r_ in enumerate(RUNS):
            if t >= (12.0 if j == 0 else 22.4):
                bx.plot([r_["ang"]], [0.78], marker="v", ms=9, color=C["blue"] if j == 0 else C["orange"],
                        markeredgecolor="#222", clip_on=False)
        bx.set_xlim(24.5, 75.5)
        bx.set_ylim(-0.5, 0.5)
        bx.set_yticks([])
        bx.tick_params(labelsize=7.5)
        for s_ in ("top", "right", "left"):
            bx.spines[s_].set_visible(False)
        bx.set_title("USP <1174> flow character (angle of repose, °)", fontsize=8.5, loc="left", pad=19)
    img = chart.draw(plot)
    speed = "pouring shown sped up" if (RUNS[0]["t0"] <= t <= RUNS[0]["t1"] or RUNS[1]["t0"] <= t <= RUNS[1]["t1"]) else ""
    ov = Overlay("Angle of repose (fixed funnel)", "Slope of a poured cone of powder on a fixed-diameter base",
                 "ISO 4324", "USP <1174>", labels=labels, readouts=readouts, chart=img,
                 step_idx=i, n_steps=len(TL.steps), step_text=step.text, speed_note=speed,
                 footer="Schematic; dimensions approximate; values illustrative")
    out = compose(rgb, ov, st)
    m_al = ramp(t, 10.6, 11.2) * (1 - ramp(t, 13.6, 14.1))
    if m_al > 0:
        out = measure_overlay(out, RUNS[0], m_al)
    m_al2 = ramp(t, 21.2, 21.8) * (1 - ramp(t, 24.0, 24.5))
    if m_al2 > 0:
        out = measure_overlay(out, RUNS[1], m_al2)
    return out


if __name__ == "__main__":
    run(frame, NAME, TL.duration)
