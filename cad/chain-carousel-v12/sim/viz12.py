"""Clips and plots for the v12 gear-engagement study (mesh12.py, run12.py), drawn from the simulation's own states.

    python viz12.py entry        # renders/v12/mesh_entry_v12.{gif,mp4}: one index, seen from the front: v11 as drawn jams; v12's cradle lifts,
                                 #   its switch reads lifted and the seek drops the pinion in; v12, most arrivals
    python viz12.py hold         # renders/v12/mesh_hold_v12.{gif,mp4}: side view of a v12 station cycle, the cradle and the spring
    python viz12.py plots        # sim/out/*.png: outcomes vs the tolerance stack, stall torque vs what the auger needs

Views: "from the front" is Sam's y-z plane looking along +x (the machine's front toward its back), world up drawn up; the side view
is Sam's x-z plane seen from the machine's -y side (Sam +y), world up drawn up. Teeth are the simulation's own convex tooth prisms.
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.patches import Polygon, Rectangle, Circle  # noqa: E402

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import mesh12 as M  # noqa: E402
import mujoco  # noqa: E402

V12 = HERE.parent
REN = V12 / "renders" / "v12"
REN.mkdir(parents=True, exist_ok=True)
OUT = M.OUT
V11_OUT = V12.parent / "chain-carousel-v11" / "sim" / "out"
GREY, ORANGE, GREEN, BLUE, DARK, RED, GOLD = "#9a9a96", "#f07a14", "#2f9e5a", "#2244cc", "#333333", "#c8322a", "#d9a21b"
plt.rcParams.update({"font.size": 11, "font.family": "DejaVu Sans"})


def gear_outline(poly, z, ang, cy, cz):
    out = []
    for k in range(z):
        a = ang + 2 * math.pi * k / z
        c, s = math.cos(a), math.sin(a)
        out.append(np.c_[poly[:, 0] * c - poly[:, 1] * s + cy, poly[:, 0] * s + poly[:, 1] * c + cz])
    return out


def body_angle_x(R):
    return math.atan2(R[2, 1], R[1, 1])


class Scene:
    def __init__(self, cfg):
        self.S = M.Station(cfg)
        self.gp, self.pp = M.tooth_polys()

    def set(self, q):
        self.S.d.qpos[:] = q
        mujoco.mj_forward(self.S.m, self.S.d)


def _tf(S, body, pts):
    """Points in a body's frame as drawn at rest (Sam mm) -> current Sam mm."""
    b = S.pos(body)
    R = S.R(body)
    if body == "ec":
        o = np.array(M.GEO["p16_pin"])
    elif body == "cradle":
        cf = S.cfg
        o = np.array([83.3, cf.piv_dy, M.GEO["pivot"][1] + cf.piv_dz])
    else:
        o = np.zeros(3)
    P = np.asarray(pts, float) - o
    return b + (R @ P.T).T


def _poly(ax, P, c, a, axes=(1, 2), lw=0, ec=None):
    ax.add_patch(Polygon(np.c_[P[:, axes[0]], -P[:, axes[1]]], closed=True, color=c, alpha=a, lw=lw, ec=ec))


def _spring(ax, p0, p1, n=7, w=3.0, axes=(1, 2), color="#8b4a1c"):
    """Zigzag between two points (drawn coordinates are (a, -b))."""
    a0, b0 = p0[axes[0]], -p0[axes[1]]
    a1, b1 = p1[axes[0]], -p1[axes[1]]
    t = np.linspace(0, 1, 2 * n + 1)
    xs = a0 + (a1 - a0) * t
    ys = b0 + (b1 - b0) * t
    off = np.r_[0, [(w if k % 2 else -w) for k in range(1, 2 * n)], 0]
    nx, ny = -(b1 - b0), (a1 - a0)
    nn = math.hypot(nx, ny) or 1.0
    ax.plot(xs + off * nx / nn, ys + off * ny / nn, color=color, lw=1.6)


def draw_front(ax, sc: Scene, title, note, y_lim=(-30, 30), z_lim=(-70, 4)):
    S = sc.S
    ax.clear()
    ax.set_aspect("equal")
    ax.set_xlim(*y_lim)
    ax.set_ylim(-z_lim[1], -z_lim[0])
    ax.axis("off")
    my = S.pos("carriage")[1]
    ax.add_patch(Rectangle((my - 27, 18.0 - 12.0), 54, 12.0, color=BLUE, alpha=0.18, lw=0))
    ax.text(my - 25.5, 14.5, "mounting plate", color=BLUE, fontsize=8)
    Rg = S.R("auger")
    gc = S.pos("auger") + Rg[:, 0] * 83.4
    for P in gear_outline(sc.gp, M.Z2, body_angle_x(Rg), gc[1], gc[2]):
        ax.add_patch(Polygon(np.c_[P[:, 0], -P[:, 1]], closed=True, color=GREY, lw=0))
    ax.add_patch(Circle((gc[1], -gc[2]), 20.9, color=GREY, lw=0))
    pc = S.pos("pinion")
    pa = body_angle_x(S.R("pinion"))
    cf = S.cfg
    if cf.cradle:
        # the cradle (its plate's outline, the pivot tube, the lug), the motor's square, the spring to the EC's roof, the stop
        cr = [[83.3, -16.0, -49.0], [83.3, 14.0, -49.0], [83.3, 14.0, -40.0], [83.3, 26.0, -40.0], [83.3, 26.0, -32.0], [83.3, 14.0, -32.0],
              [83.3, 14.0, -20.25], [83.3, -16.0, -20.25], [83.3, -16.0, -30.5], [83.3, -22.0, -30.5], [83.3, -22.0, -37.5], [83.3, -16.0, -37.5]]
        cr = [[x, y, z + 0.0] for x, y, z in cr]
        _poly(ax, _tf(S, "cradle", cr), GOLD, 0.30)
        mot = [[83.3, -14.0, -48.0], [83.3, 14.0, -48.0], [83.3, 14.0, -20.0], [83.3, -14.0, -20.0]]
        _poly(ax, _tf(S, "cradle", mot), DARK, 0.18)
        piv = _tf(S, "cradle", [[83.3, cf.piv_dy, M.GEO["pivot"][1] + cf.piv_dz]])[0]
        ax.add_patch(Circle((piv[1], -piv[2]), 1.6, color=DARK))
        top = _tf(S, "cradle", [[83.3, 0.0, -51.5]])[0]
        roof = _tf(S, "ec", [[83.3, 0.0, -64.1]])[0]
        _spring(ax, top, roof)
        rf = _tf(S, "ec", [[83.3, -9.0, -64.1], [83.3, 9.0, -64.1], [83.3, 9.0, -68.1], [83.3, -9.0, -68.1]])
        _poly(ax, rf, GREEN, 0.45)
        arm = _tf(S, "ec", [[83.3, 17.5, -30.0], [83.3, 30.0, -30.0], [83.3, 30.0, -20.0], [83.3, 17.5, -20.0]])
        _poly(ax, arm, GREEN, 0.30)
        sst = _tf(S, "cradle", [[83.3, 21.0, -30.85 - 0.0], [83.3, 21.0, -40.0]])
        ax.plot(sst[:, 1], -sst[:, 2], color=DARK, lw=2.5)
        lifted = S.lifted()
        ax.text(y_lim[1] - 0.5, -z_lim[0] - 2.0, f"switch: {'LIFTED' if lifted else 'seated'}", ha="right", va="top", fontsize=10,
                color="white", weight="bold", bbox=dict(boxstyle="round,pad=0.3", fc=RED if lifted else GREEN, ec="none"))
        ax.text(y_lim[1] - 0.5, -z_lim[0] - 6.5, f"pinion {S.lift():+5.2f} mm\nover the pivot's level", ha="right", va="top", fontsize=8.5,
                family="DejaVu Sans Mono")
    else:
        for (y0, y1, z0, z1) in ((-19.5, -15.5, -20.5, -50.5), (15.5, 19.5, -20.5, -50.5), (-15.5, 15.5, -48.5, -50.5)):
            P = _tf(S, "ec", [[83.3, y0, z0], [83.3, y1, z0], [83.3, y1, z1], [83.3, y0, z1]])
            _poly(ax, P, GREEN, 0.25)
    for P in gear_outline(sc.pp, M.Z1, pa + math.pi + math.pi / M.Z1, pc[1], pc[2]):
        ax.add_patch(Polygon(np.c_[P[:, 0], -P[:, 1]], closed=True, color=ORANGE, lw=0))
    ax.add_patch(Circle((pc[1], -pc[2]), 10.8, color=ORANGE, lw=0))
    ax.add_patch(Circle((pc[1], -pc[2]), 2.5, color="white", lw=0))
    cd = S.centre_distance()
    ax.plot([gc[1], pc[1]], [-gc[2], -pc[2]], color=DARK, lw=0.8, ls=":")
    ax.text(y_lim[0] + 0.5, -z_lim[0] - 2.0, title, fontsize=11, weight="bold", va="top")
    ax.text(y_lim[0] + 0.5, -z_lim[0] - 6.0, note, fontsize=8.5, va="top", color=DARK)
    ax.text(y_lim[0] + 0.5, -z_lim[1] + 1.0, f"centre distance {cd:5.2f} mm\nchain at {S.d.qpos[S.qa['chain']] * 1e3:+6.1f} mm", fontsize=9,
            family="DejaVu Sans Mono", va="bottom")


def _pick(runs, **kw):
    for r in runs:
        if all(r.get(k) == v for k, v in kw.items()):
            return r
    return None


def entry_clip():
    """Three indexes side by side: v11 as drawn (tip on tip, jams); v12 at the same arrival or a stub (the cradle lifts, the switch reads
    lifted, the seek drops it in); v12, an arrival that meshes on its own."""
    import imageio.v2 as imageio
    E = json.loads((OUT / "entry.json").read_text())["runs"]
    v12 = [r for r in E if r.get("label") == "v12" and r["a_err"] == 0.0 and r["k_roll"] == 10.0]
    stub = next((r for r in v12 if r["outcome"].startswith("stub")), None)
    mesh = next((r for r in v12 if r["outcome"] == "meshed"), v12[0])
    ph_stub = stub["phase"] if stub else 0.25
    cases = [("v11 as drawn: tip lands on tip, the index jams", M.Cfg(cradle=False), 0.25, "the pinion is bolted to the EC: nothing can give,\nso the chain drives the tips together"),
             ("v12: the gear lands on the pinion's tips", M.Cfg(), ph_stub, "the cradle lifts on its spring, the switch reads LIFTED;\nthen the seek (forward, back) drops it into the gap"),
             ("v12: most arrivals mesh on their own", M.Cfg(), mesh["phase"], "the free pinion turns out of the way as the gear\nslides in; the spring holds it in tight mesh")]
    runs = []
    for title, cfg, ph, note in cases:
        r, A, frames, S = M.entry(cfg, ph, record=True)
        runs.append((title, cfg, frames, note, r))
        print(title, r["outcome"], r.get("hall"), flush=True)
    n = max(len(f[2]) for f in runs)
    fig, axs = plt.subplots(1, 3, figsize=(15.36, 7.4), dpi=100)
    fig.subplots_adjust(left=0.01, right=0.99, top=0.88, bottom=0.02, wspace=0.03)
    scenes = [Scene(c[1]) for c in runs]
    writer = imageio.get_writer(str(REN / "mesh_entry_v12.mp4"), fps=30, quality=8, macro_block_size=8)
    gif = []
    img = None
    for i in range(0, n):
        for ax, sc, (title, cfg, frames, note, r) in zip(axs, scenes, runs):
            t, q = frames[min(i, len(frames) - 1)]
            sc.set(q)
            draw_front(ax, sc, title, note)
        fig.suptitle("One index into the station, then v12's seek; seen from the front, world up is up; slowed 10x (MuJoCo, real tooth contact)",
                     fontsize=12)
        fig.canvas.draw()
        img = np.asarray(fig.canvas.buffer_rgba())[..., :3].copy()
        writer.append_data(img)
        if i % 4 == 0:
            gif.append(img[::2, ::2])
    for _ in range(30):
        writer.append_data(img)
    writer.close()
    imageio.mimsave(str(REN / "mesh_entry_v12.gif"), gif + [gif[-1]] * 10, duration=0.1, loop=0)
    plt.close(fig)
    (OUT / "entry_clip_cases.json").write_text(json.dumps([dict(title=c[0], result=c[4]) for c in runs], indent=1, default=str))


def draw_side(ax, S, txt_lines, title):
    ax.clear()
    ax.set_aspect("equal")
    ax.set_xlim(-150, 280)
    ax.set_ylim(-60, 290)
    ax.axis("off")
    ax2 = (0, 2)
    plate = _tf(S, "module", [[-5, 0, -18], [252, 0, -18], [252, 0, -10], [-5, 0, -10]])
    tube = _tf(S, "module", [[0.4, 0, -12.5], [250, 0, -12.5], [250, 0, 12.5], [0.4, 0, 12.5]])
    gear = _tf(S, "module", [[78.4, 0, -23], [88.4, 0, -23], [88.4, 0, 23], [78.4, 0, 23]])
    T = _tf(S, "module", [[52, 0, -27], [68, 0, -27], [68, 0, -24], [63, 0, -24], [63, 0, -20], [57, 0, -20], [57, 0, -24], [52, 0, -24]])
    for P, c, a in ((tube, "#d8d8d0", 1.0), (plate, BLUE, 0.55), (gear, GREY, 1.0), (T, ORANGE, 1.0)):
        _poly(ax, P, c, a, ax2)
    spine = _tf(S, "ec", [[-8.6, 0, -33], [89.4, 0, -33], [89.4, 0, -37.5], [-8.6, 0, -37.5]])
    lips = _tf(S, "ec", [[51.7, 0, -21], [68.3, 0, -21], [68.3, 0, -23.8], [51.7, 0, -23.8]])
    rail = _tf(S, "ec", [[45, 0, -27.5], [75, 0, -27.5], [75, 0, -31], [45, 0, -31]])
    sol = _tf(S, "ec", [[25, 0, -27.2], [39, 0, -27.2], [39, 0, -57], [25, 0, -57]])
    arm = _tf(S, "ec", [[90, 0, -20], [126, 0, -20], [126, 0, -30], [90, 0, -30]])
    roof = _tf(S, "ec", [[104, 0, -64.1], [128, 0, -64.1], [128, 0, -68.1], [104, 0, -68.1]])
    cross = _tf(S, "ec", [[139.5, 0, -30.5], [143.5, 0, -30.5], [143.5, 0, -37.5], [139.5, 0, -37.5]])
    for P, c, a in ((spine, GREEN, 0.55), (rail, GREEN, 0.75), (lips, GREEN, 0.9), (sol, DARK, 0.6), (arm, GREEN, 0.35), (roof, GREEN, 0.5),
                    (cross, GREEN, 0.5)):
        _poly(ax, P, c, a, ax2)
    if S.cfg.cradle:
        cpl = _tf(S, "cradle", [[89.9, 0, -49.0], [93.5, 0, -49.0], [93.5, 0, -20.25], [89.9, 0, -20.25]])
        top = _tf(S, "cradle", [[93.5, 0, -48.3], [128, 0, -48.3], [128, 0, -51.5], [93.5, 0, -51.5]])
        motor = _tf(S, "cradle", [[93.5, 0, -20.0], [138.5, 0, -20.0], [138.5, 0, -48.0], [93.5, 0, -48.0]])
        for P, c, a in ((motor, DARK, 0.85), (cpl, GOLD, 0.9), (top, GOLD, 0.9)):
            _poly(ax, P, c, a, ax2)
        s0 = _tf(S, "cradle", [[116.0, 0, -51.5]])[0]
        s1 = _tf(S, "ec", [[116.0, 0, -64.1]])[0]
        _spring(ax, s0, s1, axes=ax2, w=2.5)
    pin = _tf(S, "pinion", [[78.3 - 83.3, 0, -13], [88.3 - 83.3, 0, -13], [88.3 - 83.3, 0, 13], [78.3 - 83.3, 0, 13]])
    _poly(ax, pin, ORANGE, 1.0, ax2)
    bx, _, bz = M.GEO["p16_base"]
    pp = _tf(S, "ec", [M.GEO["p16_pin"]])[0]
    ax.plot([bx, pp[0]], [-bz, -pp[2]], color="#444", lw=5, solid_capstyle="round", alpha=0.8)
    ax.plot([bx], [-bz], "o", color="#444", ms=7)
    ax.add_patch(Circle((pp[0], -pp[2]), 2.2, color="white", ec="#222", lw=1))
    ax.add_patch(Circle((0, 0), 2.5, color="#222"))
    ax.plot([-40, 300], [18, 18], color="#777", lw=2)
    ax.text(285, 18, "carriage\n(chain)", fontsize=8, va="center", color="#555")
    tx, _, tz = M.GEO["shoe_tip"]
    ax.plot([tx - 7, tx, tx + 7], [-(tz + 0.5) + 7, -(tz + 0.5), -(tz + 0.5) + 7], color=ORANGE, lw=2)
    shoe = _tf(S, "ec", [M.GEO["shoe_tip"]])[0]
    ax.plot([shoe[0]], [-shoe[2]], "v", color=GREEN, ms=8)
    ax.text(-145, 285, title, fontsize=12, weight="bold", va="top")
    ax.text(118, 262, "\n".join(txt_lines), fontsize=9.5, va="top", family="DejaVu Sans Mono", bbox=dict(boxstyle="round,pad=0.4", fc="white", ec="#bbb"))
    lab = dict(fontsize=8.5, color="#222", arrowprops=dict(arrowstyle="-", color="#888", lw=0.8))
    tip = _tf(S, "module", [[230.0, 0.0, 0.0]])[0]
    ax.annotate("module: plate + auger", (tip[0], -tip[2]), (215, -45), **lab)
    g = _tf(S, "module", [[83.4, 0.0, 15.0]])[0]
    ax.annotate("44T gear", (g[0], -g[2]), (150, -45), **lab)
    pn = _tf(S, "pinion", [[0.0, 0.0, -11.0]])[0]
    ax.annotate("24T pinion on the cradle", (pn[0], -pn[2]), (-140, 150), **lab)
    if S.cfg.cradle:
        sp = _tf(S, "ec", [[116.0, 0.0, -60.0]])[0]
        ax.annotate("spring 1 N/mm (6 N at the stop)", (sp[0], -sp[2]), (-140, 178), **lab)
    t_ = _tf(S, "module", [[60.0, 0.0, -25.5]])[0]
    ax.annotate("T's head on the EC's lips", (t_[0], -t_[2]), (-140, 122), **lab)
    ec_ = _tf(S, "ec", [[10.0, 0.0, -35.0]])[0]
    ax.annotate("electronics carriage (EC)", (ec_[0], -ec_[2]), (-140, 94), **lab)
    ax.annotate("guide seats (2)", (tx, -(tz + 0.5) + 3), (150, 5), **lab)
    ax.annotate("P16-150", (bx + 0.35 * (pp[0] - bx), -(bz + 0.35 * (pp[2] - bz))), (-60, 220), **lab)


def hold_clip():
    import imageio.v2 as imageio
    cfg = M.Cfg()
    out, A, frames, S = M.cycle(cfg, record=True)
    t_A = A[:, 0]
    fig, ax = plt.subplots(figsize=(12.8, 7.2), dpi=100)
    fig.subplots_adjust(left=0, right=1, top=1, bottom=0)
    writer = imageio.get_writer(str(REN / "mesh_hold_v12.mp4"), fps=30, quality=8, macro_block_size=8)
    gif = []
    ev = out["events"]
    for i, (t, q) in enumerate(frames):
        S.d.qpos[:] = q
        mujoco.mj_forward(S.m, S.d)
        k = min(int(np.searchsorted(t_A, t)), len(A) - 1)
        lo = max(0, k - 20)
        phase = next((e for e in ev if e[2] <= t <= e[3]), None)
        ph = {"tilt": "P16 pulls: the lips pick up the T", "dose": "dosing: auger turning, solenoid tapping", "back": "P16 extends: back down",
              "reverse": "one reverse turn at rest"}.get(phase[0] if phase else "", "at rest, in mesh")
        lift = S.lift()
        lines = [ph,
                 f"tilt          {A[k, 1]:6.1f} deg",
                 f"centre dist.  {A[k, 4]:6.2f} mm   (34.00 tight; 34.72 contact ratio 1)",
                 f"pinion        {lift:+6.2f} mm over the pivot ({'LIFTED' if S.lifted() else 'seated'})",
                 f"P16 force     {A[k, 3]:6.1f} N    (50 N limit)",
                 f"T on lips     {np.mean(A[lo:k + 1, 7]):6.1f} N",
                 f"EC on seats   {np.mean(A[lo:k + 1, 6]):6.1f} N",
                 f"teeth         {np.mean(A[lo:k + 1, 5]):6.1f} N"]
        draw_side(ax, S, lines, "v12 station, side view: the spring-loaded pinion through a dose cycle (MuJoCo; real time)")
        fig.canvas.draw()
        img = np.asarray(fig.canvas.buffer_rgba())[..., :3].copy()
        writer.append_data(img)
        if i % 3 == 0:
            gif.append(img[::2, ::2])
    writer.close()
    imageio.mimsave(str(REN / "mesh_hold_v12.gif"), gif, duration=0.1, loop=0)
    plt.close(fig)


# ---------------------------------------------------------------- plots
def outcome_plot():
    """Per tolerance offset: v11 as drawn (its jams, from v11's own study) against v12 (pooled over three clevis stiffnesses: 36 indexes
    per offset): meshed on arrival, stubbed and cleared by the first seek, by the second try, left, jammed."""
    E = json.loads((OUT / "entry.json").read_text())["runs"]
    E11 = json.loads((V11_OUT / "entry.json").read_text())["runs"]
    offs = sorted({r["a_err"] for r in E if r.get("label") == "v12"})
    fig, ax = plt.subplots(figsize=(10.5, 6.0), dpi=120)
    w = 0.38
    cats = [("meshed", "meshed on arrival", "#7fbf7f"), ("stub, cleared by the seek", "on the tips, cleared by the seek", "#f3c46b"),
            ("stub, cleared by the second try", "cleared by the second try", "#e08a2e"), ("stub left", "left on the tips (switch: lifted)", "#9b59b6"),
            ("jam", "jammed", RED)]
    for i, e in enumerate(offs):
        g = [r for r in E if r.get("label") == "v12" and r["a_err"] == e]
        bottom = 0.0
        for key, lab, col in cats:
            k = sum(1 for r in g if r["outcome"].startswith(key)) / max(1, len(g))
            ax.bar(i + w / 2, k, w * 0.95, bottom=bottom, color=col, label=lab if i == 0 else None)
            bottom += k
        g11 = [r for r in E11 if not r.get("spring") and abs(r["a_err"] - e) < 1e-9 and r.get("mode", "free") == "free" and r.get("drag_mNm", 5.0) == 5.0]
        if g11:
            j = sum(r["jam"] for r in g11) / len(g11)
            ax.bar(i - w / 2, 1.0, w * 0.95, color="#dddddd")
            ax.bar(i - w / 2, j, w * 0.95, color=RED, alpha=0.75)
            ax.text(i - w / 2, j + 0.02, f"{j:.0%}", ha="center", fontsize=9, color=RED)
        else:
            ax.text(i - w / 2, 0.45, "not run\nin v11", ha="center", fontsize=8, color="#777")
    ax.set_xticks(range(len(offs)))
    ax.set_xticklabels([f"{e:+.2f} mm" for e in offs])
    ax.set_ylabel("share of indexes")
    ax.set_ylim(0, 1.12)
    ax.legend(loc="lower center", ncol=3, fontsize=8.5, frameon=False, bbox_to_anchor=(0.5, 1.0))
    ax.set_xlabel("tolerance stack: the EC (its pivot and stop) this far farther from the gear than drawn\n"
                  "left bar: v11 as drawn (its jams in red); right bar: v12 (36 indexes per offset: 12 arrival phases x 3 clevis stiffnesses)", fontsize=9.5)
    fig.suptitle("One index into the station (MuJoCo, real teeth): v11 jams about 1 in 4; v12's cradle and seek, none", fontsize=11.5)
    fig.tight_layout(rect=(0, 0, 1, 0.97))
    fig.savefig(OUT / "entry_outcomes.png")
    plt.close(fig)


def stall_plot():
    C = json.loads((OUT / "cycle.json").read_text())["runs"]
    groups = [("v11 as drawn (rigid)", dict(cradle=False)), ("v12 as drawn\n(trailing pivot, 6 N)", dict()),
              ("pivot 10 mm\nnearer the gear", dict(piv_dz=10.0)), ("leading pivot", dict(piv_dy=18.5)), ("4 N spring", dict(f_spring=4.0))]
    angles = (0.0, 30.0, 60.0, 90.0)
    fig, ax = plt.subplots(figsize=(10.5, 5.6), dpi=120)
    w = 0.16
    cols = ["#888888", BLUE, "#5aa0d8", "#9ec9ee", "#d0e6f7"]
    for gi, (lab, cfg) in enumerate(groups):
        for ai, a in enumerate(angles):
            r = next((r for r in C if r["stall_at"] == a and r["cfg"] == cfg), None)
            if r is None:
                continue
            st = r["steps"][0]["stall"]
            v = st["load_Nm"] if st and st.get("load_Nm") else float("nan")
            ax.bar(ai + (gi - 2) * w, v * 1e3, w * 0.95, color=cols[gi], label=lab if ai == (1 if cfg.get("cradle") is False else 0) or (ai == 0) else None)
            if not math.isnan(v):
                ax.text(ai + (gi - 2) * w, v * 1e3 + 1.0, f"{v * 1e3:.0f}", ha="center", fontsize=7.5)
    ax.axhspan(5, 30, color="#c33", alpha=0.10)
    ax.text(1.62, 31, "what the auger is estimated to need: 5-30 mN m", fontsize=8.5, color="#a22", va="bottom", ha="center")
    ax.set_xticks(range(len(angles)))
    ax.set_xticklabels([f"{a:.0f} deg" for a in angles])
    ax.set_ylabel("auger load when the NEMA 11 stalls (mN m)")
    h, l = ax.get_legend_handles_labels()
    seen = {}
    for hh, ll in zip(h, l):
        seen.setdefault(ll, hh)
    ax.legend(seen.values(), seen.keys(), fontsize=8.5, ncol=5, loc="lower center", bbox_to_anchor=(0.5, 1.0), frameon=False)
    fig.suptitle("Stall ramps at 30 rpm, 450 mA: the motor stalls before any tooth jumps, in every case", fontsize=11.5)
    fig.tight_layout(rect=(0, 0, 1, 0.97))
    fig.savefig(OUT / "stall_vs_tilt.png")
    plt.close(fig)


if __name__ == "__main__":
    what = sys.argv[1] if len(sys.argv) > 1 else "plots"
    if what == "entry":
        entry_clip()
    elif what == "hold":
        hold_clip()
    elif what == "plots":
        outcome_plot()
        stall_plot()
