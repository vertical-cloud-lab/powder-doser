"""Hall flowmeter (ASTM B213) and Carney funnel (ASTM B964): time for 50 g to flow.

Static method: block the orifice with a dry finger, pour in 50.0 g, release and time until
the last powder leaves the orifice. A powder that will not flow unaided through the
2.54 mm Hall orifice is retested in the Carney funnel (5.08 mm). Values are illustrative.
"""
from common import *  # noqa: F401,F403

NAME = "hall_flow"
RHO_316L = 4.4e-3      # g/mm^3 apparent density (illustrative)
RHO_ALSI = 1.4e-3
MASS = 50.0
T_HALL = 15.8          # s/50 g, illustrative free-flowing 316L
T_CARNEY = 7.6         # s/50 g, illustrative AlSi10Mg in the Carney funnel
SPEED = 2.0            # flow shown at 2x real time
TAN_HEAP = math.tan(math.radians(31))

Z_BASE = 14.0          # top of the stand's base plate
CUP_R, CUP_H = 22.0, 42.0
Z_O = Z_BASE + CUP_H + 25.0   # orifice exit, 25 mm above the receiver rim
CUT = (-55.0, 235.0)          # cutaway wedge faces the camera

HALL_PROF, HG = funnel_geom(Z_O, 1.27)
CARN_PROF, CG = funnel_geom(Z_O, 2.54)

TL = Timeline([
    Step(0.0, 4.0, "Assemble: levelled stand, Hall funnel in its holder, receiver underneath"),
    Step(4.0, 6.6, "Block the orifice with a dry finger and pour in 50.0 g of powder"),
    Step(6.6, 7.2, "Remove the finger and start the timer"),
    Step(7.2, 15.1, "Powder runs out through the 2.54 mm orifice"),
    Step(15.1, 16.8, "Stop when the last powder leaves the orifice: report s/50 g"),
    Step(16.8, 19.6, "A cohesive powder (e.g. AlSi10Mg) arches over the orifice: no flow"),
    Step(19.6, 21.4, "Swap in the Carney funnel (5.08 mm orifice, ASTM B964)"),
    Step(21.4, 25.6, "Release and time 50 g through the larger orifice"),
    Step(25.6, 29.0, "Report both: 'no flow' in Hall is a result, not a missing value"),
])

st = Stage()
# stand: base with three feet, column, arm and funnel holder ring
st.add("base", disc(70, 4, Z_BASE), "dark")
for i, a in enumerate((90, 210, 330)):
    x, y = 58 * math.cos(math.radians(a)), 58 * math.sin(math.radians(a))
    st.add(f"foot{i}", disc(7, 0, 4).translate((x, y, 0), inplace=False), "rubber")
st.add("level", disc(7, Z_BASE, Z_BASE + 3).translate((-45, -40, 0), inplace=False), "glass", opacity=0.6, color="#9be39b")
COL_XY = np.array([-62.0, 48.0])
st.add("column", rod((COL_XY[0], COL_XY[1], Z_BASE), (COL_XY[0], COL_XY[1], HG["lip_top"] + 30), 7), "steel")
ring_z = HG["z_ct"] - 7.0
st.add("ring", tube(HG["r_lip"] - 2.0, HG["r_lip"] + 6.0, ring_z, HG["z_ct"] - 1.0), "steel_dark")
_u = COL_XY / np.linalg.norm(COL_XY)
st.add("arm", rod((*(_u * (HG["r_lip"] + 4)), ring_z + 3), (COL_XY[0], COL_XY[1], ring_z + 3), 4.5), "steel_dark")
st.add("clamp", disc(11, ring_z - 4, ring_z + 10).translate((COL_XY[0], COL_XY[1], 0), inplace=False), "steel_dark")
st.add("hall", lathe(HALL_PROF, a0=CUT[0], a1=CUT[1]), "steel")
st.add("carney", lathe(CARN_PROF, a0=CUT[0], a1=CUT[1]), "brass")
st.add("cup", lathe([(0, Z_BASE), (CUP_R, Z_BASE), (CUP_R, Z_BASE + CUP_H), (CUP_R - 1.6, Z_BASE + CUP_H),
                     (CUP_R - 1.6, Z_BASE + 2.0), (0, Z_BASE + 2.0)]), "glass")
st.add("finger", rod((-44, -26, Z_O - 17), (0, 0, Z_O - 7.5), 7.5).merge(pv.Sphere(radius=7.5, center=(0, 0, Z_O - 7.5))),
       "blue", color="#5b8fd6")
pan = lathe([(0, 0), (26, 0), (30, 8), (28.6, 8), (24.8, 1.4), (0, 1.4)])
st.add("pan", pan, "alu")
st.shadow("sh_base", (0, 6), 98, 92, 0.38)
PAN_XY = (-48.0, 6.0)
POUR_O = (PAN_XY[0] + 29.5, PAN_XY[1], HG["lip_top"] + 14.0)   # pan lip when tilted

COLS_316 = grain_colors(6000, "#7c838b", 0.12, seed=1)
COLS_ALSI = grain_colors(6000, "#b2b7bd", 0.10, seed=2)
chart = Chart()


def flow_state(t):
    """Mass in funnel/receiver for each run at animation time t."""
    pour = lin(t, 4.6, 6.4)
    run1 = lin(t, 7.0, 7.0 + T_HALL / SPEED)
    carney = lin(t, 21.6, 21.6 + T_CARNEY / SPEED)
    return pour, run1, carney


def frame(t):
    i, step = TL.current(t)
    pour, run1, run2 = flow_state(t)
    labels, readouts = [], []

    # ---- assembly
    for nm, t0, off in (("base", 0.1, (0, 0, 60)), ("column", 0.5, (0, 0, 120)), ("ring", 0.9, (0, 0, 80)),
                        ("arm", 0.9, (0, 0, 80)), ("hall", 1.4, (0, 0, 110)), ("cup", 2.0, (-140, 0, 0))):
        M, vis, op = arrive(t, t0, offset=off)
        st.pose(nm, M, vis)
    for k in range(3):
        st.pose(f"foot{k}", arrive(t, 0.1, offset=(0, 0, 60))[0], t >= 0.1)
    st.pose("level", arrive(t, 0.1, offset=(0, 0, 60))[0], t >= 0.1)

    # ---- funnel swap (Hall out, Carney in)
    out = ramp(t, 19.7, 20.6)
    inn = ramp(t, 20.4, 21.3)
    if t >= 19.7:
        st.pose("hall", matrix(translate=(170 * out, 0, 140 * out)), out < 0.98)
    st.pose("carney", matrix(translate=(-170 * (1 - inn), 0, 140 * (1 - inn))), t >= 20.4)

    # ---- finger: in for the pour, out at release; again for the cohesive and Carney runs
    f_in = ramp(t, 3.9, 4.5) * (1 - ramp(t, 6.6, 7.0)) + ramp(t, 16.9, 17.3) * (1 - ramp(t, 17.6, 18.0)) \
        + ramp(t, 20.9, 21.2) * (1 - ramp(t, 21.3, 21.6))
    st.pose("finger", matrix(translate=(-90 * (1 - f_in), -50 * (1 - f_in), -20 * (1 - f_in))), f_in > 0.01)

    # ---- pan pours the sample (twice)
    def pan_pose(t0, t1):
        s_in, s_out, tilt = ramp(t, t0 - 0.5, t0), ramp(t, t1, t1 + 0.5), ramp(t, t0, t0 + 0.4) * (1 - ramp(t, t1 - 0.2, t1))
        M = matrix(translate=(PAN_XY[0], PAN_XY[1], HG["lip_top"] + 26)) @ matrix(rot_deg=-40 * tilt, axis=(0, 1, 0), origin=(26, 0, 6))
        M = matrix(translate=(-140 * (1 - s_in) - 140 * s_out, 0, 30 * (1 - s_in) + 30 * s_out)) @ M
        return M, (t0 - 0.5) <= t <= (t1 + 0.5)
    if t < 12:
        M, vis = pan_pose(4.6, 6.4)
    else:
        M, vis = pan_pose(17.0, 17.5)
    st.pose("pan", M, vis)

    # ---- powder in funnel / receiver and the falling stream
    hall_present = t < 19.7
    g_act = HG if t < 20.4 else CG
    a0, a1 = CUT
    if t < 16.8:
        V_f = MASS / RHO_316L * (pour - run1)
        V_r = MASS / RHO_316L * run1
        cols = COLS_316
        flowing = 7.0 <= t <= 7.0 + T_HALL / SPEED
    elif t < 21.6:
        V_f = MASS / RHO_ALSI * ramp(t, 17.0, 17.6)
        V_r = 0.0
        cols = COLS_ALSI
        flowing = False
    else:
        V_f = MASS / RHO_ALSI * (1 - run2)
        V_r = MASS / RHO_ALSI * run2
        cols = COLS_ALSI
        flowing = t <= 21.6 + T_CARNEY / SPEED
    # emptied receiver between runs
    if 16.3 <= t < 16.8:
        V_r *= 1 - ramp(t, 16.3, 16.8)
    dip = 4.0 * (run1 if t < 16.8 else run2)
    M_f = st.pl.actors["hall"].user_matrix if (hall_present and t >= 19.7) else np.eye(4)
    fill = funnel_fill(V_f, g_act, dip=dip, a0=a0, a1=a1) if t >= 4.6 else None
    if fill is not None:
        st.add("fill", fill, "powder", color="#7c838b" if t < 16.8 else "#aeb3b9")
        st.pose("fill", np.asarray(M_f) if t < 20.4 else matrix(translate=(-170 * (1 - inn), 0, 140 * (1 - inn))))
    else:
        st.remove("fill")
    apex = heap_apex(V_r, CUP_R - 1.6, TAN_HEAP)
    hs = heap_solid(CUP_R - 1.6, apex, TAN_HEAP, Z_BASE + 2.0)
    if hs is not None and t >= 7.0:
        st.add("heap", hs, "powder", color="#7c838b" if t < 16.8 else "#aeb3b9", opacity=1.0)
    else:
        st.remove("heap")

    # streams: the pour into the funnel, the run-out below the orifice
    floor_r = lambda x, y: Z_BASE + 2.0 + np.maximum(0.05, apex - np.hypot(x, y) * TAN_HEAP)  # noqa: E731
    pts = []
    if 4.7 <= t <= 6.6:
        p, _ = stream(t, 4.7, 6.3, 700, POUR_O, 2.0, v0=40, floor=lambda x, y: funnel_level(V_f, g_act) + 0 * x, seed=5)
        pts.append(p)
    if 17.0 <= t <= 17.9:
        p, _ = stream(t, 17.05, 17.55, 700, POUR_O, 2.0, v0=40, floor=lambda x, y: funnel_level(V_f, g_act) + 0 * x, seed=6)
        pts.append(p)
    if t >= 7.0 and t < 16.0:
        p, _ = stream(t, 7.0, 7.0 + T_HALL / SPEED, 900, (0, 0, Z_O), HG["r_o"] * 0.8, v0=90, floor=floor_r,
                      max_fall=Z_O - Z_BASE, seed=7)
        pts.append(p)
    if 18.0 <= t <= 18.9:   # a few grains, then the arch holds
        p, _ = stream(t, 18.0, 18.25, 250, (0, 0, Z_O), HG["r_o"] * 0.8, v0=90, floor=floor_r, max_fall=Z_O - Z_BASE, seed=8)
        pts.append(p)
    if t >= 21.6:
        p, _ = stream(t, 21.6, 21.6 + T_CARNEY / SPEED, 1500, (0, 0, Z_O), CG["r_o"] * 0.8, v0=110, floor=floor_r,
                      max_fall=Z_O - Z_BASE, seed=9)
        pts.append(p)
    P = np.vstack(pts) if pts else np.empty((0, 3))
    st.grains("stream", P, cols[: len(P)] if len(P) <= len(cols) else None, size=3.2)

    # ---- camera: slow orbit
    az = -34 + 24 * ramp(t, 0, 6) + 18 * ramp(t, 15, 29)
    dist = 600 - 110 * ramp(t, 2.5, 6.5) + 40 * ramp(t, 19, 21) - 40 * ramp(t, 21.5, 23)
    st.orbit((0, 10, 88), dist, az, 20 - 4 * ramp(t, 4, 8))
    st.pl.camera.SetWindowCenter(0.28, -0.06)
    rgb = st.render()

    # ---- labels
    def lab(text, xyz, off, t0, t1):
        a = ramp(t, t0, t0 + 0.4) * (1 - ramp(t, t1 - 0.4, t1))
        if a > 0:
            labels.append(Label(text, xyz, off, a))
    lab("Hall funnel, 2.54 mm orifice", (-HG["r_lip"], 0, HG["lip_top"] - 2), (-30, -62), 1.6, 6.0)
    lab("Stand with spirit level", (-45, -40, Z_BASE + 3), (-70, 45), 0.4, 4.2)
    lab("Receiver", (CUP_R, -6, Z_BASE + 30), (80, 30), 2.4, 6.2)
    lab("Dry finger seals the orifice", (0, -8, Z_O - 9), (-70, 70), 4.4, 6.8)
    lab("Timer runs from release to last grain", (0, 0, Z_O - 6), (70, 70), 7.2, 11.0)
    lab("Arch over the orifice: no flow", (0, 0, Z_O + 4), (80, 70), 18.3, 19.7)
    lab("Carney funnel, 5.08 mm orifice", (-CG["r_lip"], 0, CG["lip_top"] - 2), (-30, -62), 20.9, 24.0)

    # ---- readouts
    if t < 16.8:
        tim = min(max(0.0, (t - 7.0) * SPEED), T_HALL)
        col = "#7CFC9A" if t < 7.0 + T_HALL / SPEED else "#FFD166"
    elif t < 21.6:
        tim = min(max(0.0, (t - 18.0) * SPEED), 3.0) if t >= 18.0 else 0.0
        col = "#FF6B6B"
    else:
        tim = min(max(0.0, (t - 21.6) * SPEED), T_CARNEY)
        col = "#7CFC9A" if t < 21.6 + T_CARNEY / SPEED else "#FFD166"
    no_flow = 18.9 <= t < 21.6
    readouts.append(Readout("TIMER", "  ---" if no_flow else f"{tim:5.1f} s", col))
    readouts.append(Readout("SAMPLE", "50.00 g"))
    if t >= 15.1:
        readouts.append(Readout("HALL, 316L", f"{T_HALL:.1f} s/50 g", "#FFD166"))
    if t >= 19.0:
        readouts.append(Readout("HALL, AlSi10Mg", "no flow", "#FF6B6B"))
    if t >= 25.3:
        readouts.append(Readout("CARNEY, AlSi10Mg", f"{T_CARNEY:.1f} s/50 g", "#FFD166"))

    # ---- chart: mass collected vs real time
    def plot(fig):
        ax = fig.add_axes([0.14, 0.17, 0.82, 0.70])
        style_axes(ax, "Mass collected in the receiver")
        tt = np.linspace(0, 20, 200)
        if t >= 7.0:
            tr = min((t - 7.0) * SPEED, T_HALL) if t < 16.8 else T_HALL
            x = tt[tt <= tr]
            ax.plot(x, MASS * x / T_HALL, color=C["blue"], lw=2.4, label="316L · Hall")
        if t >= 18.0:
            x = tt[tt <= min((t - 18.0) * SPEED, 6.0)]
            ax.plot(x, np.minimum(0.4, 0.4 * x / 0.5), color=C["red"], lw=2.4, ls="--", label="AlSi10Mg · Hall (no flow)")
        if t >= 21.6:
            x = tt[tt <= min((t - 21.6) * SPEED, T_CARNEY)]
            ax.plot(x, MASS * x / T_CARNEY, color=C["orange"], lw=2.4, label="AlSi10Mg · Carney")
        ax.set_xlim(0, 20)
        ax.set_ylim(0, 55)
        ax.set_xlabel("time since release (s)")
        ax.set_ylabel("mass (g)")
        if t >= 7.0:
            ax.legend(fontsize=8, loc="upper left", frameon=False)
    img = chart.draw(plot)
    ov = Overlay("Hall flowmeter & Carney funnel", "Flow rate of metal powders: seconds for 50 g to run out",
                 "ASTM B213", "ASTM B964", labels=labels, readouts=readouts, chart=img,
                 step_idx=i, n_steps=len(TL.steps), step_text=step.text,
                 speed_note="flow shown at 2× speed" if 7.0 <= t <= 25.6 else "",
                 footer="Schematic; dimensions approximate; values illustrative")
    return compose(rgb, ov, st)


if __name__ == "__main__":
    run(frame, NAME, TL.duration)
