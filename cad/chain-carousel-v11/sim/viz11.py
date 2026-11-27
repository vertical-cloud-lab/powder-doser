"""Clips and plots for the v11 gear-engagement study (mesh11.py, run11.py), drawn from the simulation's own states.

    python viz11.py entry        # renders/v11/mesh_entry_v11.{gif,mp4}: the gear sliding into mesh, seen from the front, three cases
    python viz11.py tilt         # renders/v11/mesh_hold_v11.{gif,mp4}: side view of a cycle, what holds the centre distance
    python viz11.py plots        # sim/out/*.png: outcomes vs tolerance, the centre-distance window, stall ramps
    python viz11.py spring       # renders/v11/spring_pinion_v12.png: the spring-loaded pinion (a v12 candidate), schematic

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
from matplotlib.patches import Polygon, Rectangle, Circle, FancyArrowPatch  # noqa: E402

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import mesh11 as M  # noqa: E402
import mujoco  # noqa: E402

V11 = HERE.parent
REN = V11 / "renders" / "v11"
OUT = M.OUT
GREY, ORANGE, GREEN, BLUE, DARK = "#9a9a96", "#f07a14", "#2f9e5a", "#2244cc", "#333333"
plt.rcParams.update({"font.size": 11, "font.family": "DejaVu Sans"})


# ---------------------------------------------------------------- geometry helpers
def gear_outline(poly, z, ang, cy, cz, root):
    """Teeth (convex prisms' sections) + root disc of a gear whose body is turned `ang` about x, centred at (cy, cz) in Sam (y, z)."""
    out = []
    for k in range(z):
        a = ang + 2 * math.pi * k / z
        c, s = math.cos(a), math.sin(a)
        P = np.c_[poly[:, 0] * c - poly[:, 1] * s + cy, poly[:, 0] * s + poly[:, 1] * c + cz]
        out.append(P)
    return out


def body_angle_x(R):
    """Rotation of a body about x from its xmat (the y axis's image in the y-z plane)."""
    return math.atan2(R[2, 1], R[1, 1])


def show(ax, y, z, **kw):
    """Sam (y, z) -> drawing (y, -z): world up is drawn up."""
    return ax.plot(y, -np.asarray(z), **kw)


class Scene:
    """Replays recorded qpos on a Station to read body poses."""

    def __init__(self, cfg):
        self.S = M.Station(cfg)
        self.gp, self.pp = M.tooth_polys()

    def set(self, q):
        self.S.d.qpos[:] = q
        mujoco.mj_forward(self.S.m, self.S.d)

    def gear(self):
        S = self.S
        c = S.pos("auger")
        Rm = S.R("auger")
        # the gear's mid-plane centre: the auger axis at x = 83.4
        gc = c + Rm[:, 0] * 83.4
        return gc, body_angle_x(Rm)

    def pinion(self):
        S = self.S
        return S.pos("pinion"), body_angle_x(S.R("pinion"))


def draw_front(ax, sc: Scene, title, note, y_lim=(-26, 22), z_lim=(-52, 4)):
    S = sc.S
    ax.clear()
    ax.set_aspect("equal")
    ax.set_xlim(*y_lim)
    ax.set_ylim(-z_lim[1], -z_lim[0])
    ax.axis("off")
    gc, ga = sc.gear()
    pc, pa = sc.pinion()
    # the carriage plates' inner face and the module's plate (z -18), drawn under the station
    my = S.pos("carriage")[1]
    ax.add_patch(Rectangle((my - 27, 18.0 - 12.0), 54, 12.0 - 0.0, color=BLUE, alpha=0.18, lw=0))
    ax.text(my - 25.5, 14.5, "mounting plate", color=BLUE, fontsize=8)
    # gear: teeth + root disc
    for P in gear_outline(sc.gp, M.Z2, ga, gc[1], gc[2], 20.84):
        ax.add_patch(Polygon(np.c_[P[:, 0], -P[:, 1]], closed=True, color=GREY, lw=0))
    ax.add_patch(Circle((gc[1], -gc[2]), 20.9, color=GREY, lw=0))
    ax.add_patch(Circle((gc[1], -gc[2]), 1.2, color="white", lw=0))
    # pinion
    for P in gear_outline(sc.pp, M.Z1, pa + math.pi + math.pi / M.Z1, pc[1], pc[2], 10.75):
        ax.add_patch(Polygon(np.c_[P[:, 0], -P[:, 1]], closed=True, color=ORANGE, lw=0))
    ax.add_patch(Circle((pc[1], -pc[2]), 10.8, color=ORANGE, lw=0))
    ax.add_patch(Circle((pc[1], -pc[2]), 2.5, color="white", lw=0))
    # the EC round the pinion (its cheeks and motor plate, sectioned), translucent
    ec = S.pos("ec")
    Re = S.R("ec")
    px, py, pz = M.GEO["p16_pin"]
    for (y0, y1, z0, z1) in ((-19.5, -15.5, -20.5, -50.5), (15.5, 19.5, -20.5, -50.5), (-15.5, 15.5, -48.5, -50.5)):
        corners = np.array([[83.3 - px, y0 - py, z0 - pz], [83.3 - px, y1 - py, z0 - pz], [83.3 - px, y1 - py, z1 - pz], [83.3 - px, y0 - py, z1 - pz]])
        W = (ec + (Re @ corners.T).T)
        ax.add_patch(Polygon(np.c_[W[:, 1], -W[:, 2]], closed=True, color=GREEN, alpha=0.25, lw=0))
    cd = S.centre_distance()
    ax.plot([gc[1], pc[1]], [-gc[2], -pc[2]], color=DARK, lw=0.8, ls=":")
    ax.text(y_lim[0] + 0.5, -z_lim[0] - 2.0, title, fontsize=11, weight="bold", va="top")
    ax.text(y_lim[0] + 0.5, -z_lim[0] - 5.5, note, fontsize=8.5, va="top", color=DARK)
    ax.text(y_lim[0] + 0.5, -z_lim[1] + 1.0, f"centre distance {cd:5.2f} mm\nchain at {S.d.qpos[S.qa['chain']] * 1e3:+6.1f} mm", fontsize=9,
            family="DejaVu Sans Mono", va="bottom")


def entry_clip():
    """Three entries side by side: as drawn (meshes), as drawn (stubs and jams), spring-loaded (stubs, the seek drops it in)."""
    import imageio.v2 as imageio
    cases = [("As drawn: the free pinion turns as the gear slides in", M.Cfg(), 0.5,
              "NEMA 11 free; the gear's teeth roll the pinion round"),
             ("As drawn: tip lands on tip, the index jams", M.Cfg(), 0.25,
              "nothing can give: the chain drives the tips together"),
             ("Spring-loaded pinion (v12 candidate): lifts, then drops in", M.Cfg(spring=True), 0.0,
              "tip on tip lifts the pinion 1.8 mm on its 6 N spring;\nthen the seek (a slow turn, reversing once) drops it in")]
    runs = []
    for title, cfg, ph, note in cases:
        r, A, frames, S = M.entry(cfg, ph, record=True, seek_reverse=True)
        runs.append((title, cfg, frames, note, r))
        print(title, r["outcome"], flush=True)
    n = max(len(f[2]) for f in runs)
    fig, axs = plt.subplots(1, 3, figsize=(15.36, 6.6), dpi=100)
    fig.subplots_adjust(left=0.01, right=0.99, top=0.86, bottom=0.02, wspace=0.03)
    scenes = [Scene(c[1]) for c in runs]
    writer = imageio.get_writer(str(REN / "mesh_entry_v11.mp4"), fps=30, quality=8, macro_block_size=8)
    gif = []
    step = 1
    for i in range(0, n, step):
        for ax, sc, (title, cfg, frames, note, r) in zip(axs, scenes, runs):
            t, q = frames[min(i, len(frames) - 1)]
            sc.set(q)
            draw_front(ax, sc, title, note)
        fig.suptitle("v11: one index into the station, then a slow turn of the pinion (the seek); seen from the front, world up is up; slowed 10x; MuJoCo, real tooth contact",
                     fontsize=12)
        fig.canvas.draw()
        img = np.asarray(fig.canvas.buffer_rgba())[..., :3].copy()
        writer.append_data(img)
        if i % 4 == 0:
            gif.append(img[::2, ::2])
    for _ in range(30):
        writer.append_data(img)
    writer.close()
    imageio.mimsave(str(REN / "mesh_entry_v11.gif"), gif + [gif[-1]] * 10, duration=0.1, loop=0)
    plt.close(fig)
    (OUT / "entry_clip_cases.json").write_text(json.dumps([dict(title=c[0], result=c[4]) for c in runs], indent=1, default=str))


# ---------------------------------------------------------------- side view of the cycle
def _tf(S, body, pts_sam_rest):
    """Points given in the body's frame as it sits at rest (Sam mm) -> current Sam mm."""
    b = S.pos(body)
    R = S.R(body)
    if body == "ec":
        o = np.array(M.GEO["p16_pin"])
    else:
        o = np.zeros(3)
    P = np.asarray(pts_sam_rest, float) - o
    return b + (R @ P.T).T


def draw_side(ax, S, txt_lines, title):
    ax.clear()
    ax.set_aspect("equal")
    ax.set_xlim(-150, 280)
    ax.set_ylim(-60, 290)
    ax.axis("off")
    # module: plate, tube, gear, T
    plate = _tf(S, "module", [[-5, 0, -18], [252, 0, -18], [252, 0, -10], [-5, 0, -10]])
    tube = _tf(S, "module", [[0.4, 0, -12.5], [250, 0, -12.5], [250, 0, 12.5], [0.4, 0, 12.5]])
    gear = _tf(S, "module", [[78.4, 0, -23], [88.4, 0, -23], [88.4, 0, 23], [78.4, 0, 23]])
    T = _tf(S, "module", [[52, 0, -27], [68, 0, -27], [68, 0, -24], [63, 0, -24], [63, 0, -20], [57, 0, -20], [57, 0, -24], [52, 0, -24]])
    for P, c, a in ((tube, "#d8d8d0", 1.0), (plate, BLUE, 0.55), (gear, GREY, 1.0), (T, ORANGE, 1.0)):
        ax.add_patch(Polygon(np.c_[P[:, 0], -P[:, 2]], closed=True, color=c, alpha=a, lw=0))
    # EC: spine, rail block (lips), motor, arm
    spine = _tf(S, "ec", [[-8.6, 0, -33], [93.5, 0, -33], [93.5, 0, -37.5], [-8.6, 0, -37.5]])
    lips = _tf(S, "ec", [[51.7, 0, -21], [68.3, 0, -21], [68.3, 0, -23.8], [51.7, 0, -23.8]])
    rail = _tf(S, "ec", [[45, 0, -27.5], [75, 0, -27.5], [75, 0, -31], [45, 0, -31]])
    motor = _tf(S, "ec", [[93.5, 0, -20.3], [137, 0, -20.3], [137, 0, -48.2], [93.5, 0, -48.2]])
    pin = _tf(S, "pinion", [[78.3 - 83.3, 0, -13], [88.3 - 83.3, 0, -13], [88.3 - 83.3, 0, 13], [78.3 - 83.3, 0, 13]])
    sol = _tf(S, "ec", [[25, 0, -27.2], [39, 0, -27.2], [39, 0, -57], [25, 0, -57]])
    arm = _tf(S, "ec", [[90, 0, -20], [126, 0, -20], [126, 0, -30], [90, 0, -30]])
    for P, c, a in ((spine, GREEN, 0.55), (rail, GREEN, 0.75), (lips, GREEN, 0.9), (motor, DARK, 0.85), (sol, DARK, 0.6), (arm, GREEN, 0.35),
                    (pin, ORANGE, 1.0)):
        ax.add_patch(Polygon(np.c_[P[:, 0], -P[:, 2]], closed=True, color=c, alpha=a, lw=0))
    # P16: base to the rod-end pin
    bx, _, bz = M.GEO["p16_base"]
    pp = _tf(S, "ec", [M.GEO["p16_pin"]])[0]
    ax.plot([bx, pp[0]], [-bz, -pp[2]], color="#444", lw=5, solid_capstyle="round", alpha=0.8)
    ax.plot([bx], [-bz], "o", color="#444", ms=7)
    ax.add_patch(Circle((pp[0], -pp[2]), 2.2, color="white", ec="#222", lw=1))
    # hinge and the carriage (bottom run) line
    ax.add_patch(Circle((0, 0), 2.5, color="#222"))
    ax.plot([-40, 300], [18, 18], color="#777", lw=2)
    ax.text(285, 18, "carriage\n(chain)", fontsize=8, va="center", color="#555")
    # shoe and seat
    shoe = _tf(S, "ec", [M.GEO["shoe_tip"]])[0]
    tx, _, tz = M.GEO["shoe_tip"]
    ax.plot([tx - 7, tx, tx + 7], [-(tz + 0.5) + 7, -(tz + 0.5), -(tz + 0.5) + 7], color=ORANGE, lw=2)
    ax.plot([shoe[0]], [-shoe[2]], "v", color=GREEN, ms=8)
    ax.text(-145, 285, title, fontsize=12, weight="bold", va="top")
    ax.text(118, 262, "\n".join(txt_lines), fontsize=9.5, va="top", family="DejaVu Sans Mono",
            bbox=dict(boxstyle="round,pad=0.4", fc="white", ec="#bbb"))
    # labels on the parts (text placed off to the side, arrows to the parts' current positions)
    lab = dict(fontsize=8.5, color="#222", arrowprops=dict(arrowstyle="-", color="#888", lw=0.8))
    tip = _tf(S, "module", [[230.0, 0.0, 0.0]])[0]
    ax.annotate("module: plate + auger\n(hangs on its hinge pins)", (tip[0], -tip[2]), (215, -45), **lab)
    g = _tf(S, "module", [[83.4, 0.0, 15.0]])[0]
    ax.annotate("44T gear", (g[0], -g[2]), (150, -45), **lab)
    pn = _tf(S, "pinion", [[0.0, 0.0, -11.0]])[0]
    ax.annotate("24T pinion on the NEMA 11", (pn[0], -pn[2]), (-140, 140), **lab)
    t_ = _tf(S, "module", [[60.0, 0.0, -25.5]])[0]
    ax.annotate("T's head on the EC's lips", (t_[0], -t_[2]), (-140, 112), **lab)
    ec_ = _tf(S, "ec", [[10.0, 0.0, -35.0]])[0]
    ax.annotate("electronics carriage (EC)", (ec_[0], -ec_[2]), (-140, 84), **lab)
    ax.annotate("guide seat", (tx, -(tz + 0.5) + 3), (150, 5), **lab)
    ax.annotate("hinge", (0, 0), (-60, -30), **lab)
    ax.annotate("P16-150, to its base\non the front bar", (bx + 0.35 * (pp[0] - bx), -(bz + 0.35 * (pp[2] - bz))), (-60, 210), **lab)


def tilt_clip():
    import imageio.v2 as imageio
    cfg = M.Cfg()
    out, A, frames, S = M.cycle(cfg, record=True)
    t_A = A[:, 0]
    fig, ax = plt.subplots(figsize=(12.8, 7.2), dpi=100)
    fig.subplots_adjust(left=0, right=1, top=1, bottom=0)
    writer = imageio.get_writer(str(REN / "mesh_hold_v11.mp4"), fps=30, quality=8, macro_block_size=8)
    gif = []
    ev = out["events"]
    for i, (t, q) in enumerate(frames):
        S.d.qpos[:] = q
        mujoco.mj_forward(S.m, S.d)
        k = int(np.searchsorted(t_A, t))
        k = min(k, len(A) - 1)
        lo = max(0, k - 20)
        phase = next((e for e in ev if e[2] <= t <= e[3]), None)
        ph = {"tilt": "P16 pulls: the lips pick up the T", "dose": "dosing: auger turning, solenoid tapping", "back": "P16 extends: back onto the shelf and the seat",
              "reverse": "one reverse turn at rest"}.get(phase[0] if phase else "", "at rest, in mesh")
        lines = [f"{ph}",
                 f"tilt          {A[k, 1]:6.1f} deg",
                 f"centre dist.  {A[k, 4]:6.2f} mm   (34.00 tight, 34.72 contact ratio 1)",
                 f"P16 force     {A[k, 3]:6.1f} N    (50 N limit)",
                 f"T on lips     {np.mean(A[lo:k + 1, 7]):6.1f} N",
                 f"EC on seat    {np.mean(A[lo:k + 1, 6]):6.1f} N",
                 f"teeth         {np.mean(A[lo:k + 1, 5]):6.1f} N"]
        draw_side(ax, S, lines, "v11 station, side view: what keeps the gear in mesh (MuJoCo, as drawn; real time)")
        fig.canvas.draw()
        img = np.asarray(fig.canvas.buffer_rgba())[..., :3].copy()
        writer.append_data(img)
        if i % 3 == 0:
            gif.append(img[::2, ::2])
    writer.close()
    imageio.mimsave(str(REN / "mesh_hold_v11.gif"), gif, duration=0.1, loop=0)
    plt.close(fig)


# ---------------------------------------------------------------- plots
def contact_window_plot():
    import common as GC  # noqa: F401
    a = np.linspace(33.9, 34.9, 400)
    rb1, rb2 = 12 * math.cos(math.radians(20)), 22 * math.cos(math.radians(20))
    ra1, ra2 = 13.0, 23.0
    pa = np.arccos(34.0 * math.cos(math.radians(20)) / a)
    L = np.sqrt(ra1 ** 2 - rb1 ** 2) + np.sqrt(ra2 ** 2 - rb2 ** 2) - a * np.sin(pa)
    cr = L / (math.pi * math.cos(math.radians(20)))
    bl = 2 * (a - 34.0) * np.tan(pa)
    fig, ax = plt.subplots(figsize=(9, 4.6), dpi=120)
    ax.plot(a, cr, color=DARK, lw=2, label="contact ratio")
    ax.axhline(1.0, color="#c33", lw=1, ls="--")
    ax.axvspan(33.9, 34.0, color="#c33", alpha=0.15)
    ax.text(33.905, 1.75, "binds\n(no backlash)", color="#a22", fontsize=9, va="top")
    a1 = float(np.interp(1.0, cr[::-1], a[::-1]))
    ax.axvspan(a1, 34.9, color="#c33", alpha=0.15)
    ax.text(a1 + 0.01, 1.75, f"teeth can jump\n(contact ratio < 1\nfrom {a1:.2f} mm)", color="#a22", fontsize=9, va="top")
    marks = [(34.25, "v11 as drawn\n(34.25)"), (34.08, "at rest, EC leaning\non the gear (sim)"), (34.45, "tilted: T on the lips\n(+0.2 gap)")]
    for x, lab in marks:
        ax.axvline(x, color=BLUE, lw=1)
        ax.text(x + 0.005, 0.62, lab, color=BLUE, fontsize=8.5, rotation=90, va="bottom")
    ax.set_xlabel("centre distance, pinion to gear (mm)")
    ax.set_ylabel("contact ratio")
    ax.set_ylim(0.6, 1.8)
    ax2 = ax.twinx()
    ax2.plot(a, bl, color=ORANGE, lw=1.5)
    ax2.set_ylabel("backlash (mm)", color=ORANGE)
    ax.set_title("24T on 44T, module 1: the window the centre distance has to stay in")
    fig.tight_layout()
    fig.savefig(OUT / "centre_distance_window.png")
    plt.close(fig)
    return a1


def outcome_plots():
    """Per tolerance offset, pooled over the three clevis stiffnesses (36 indexes each): as drawn, the share that jams; spring-loaded,
    the share that jams (none) and the share left on the tips until the seek."""
    E = json.loads((OUT / "entry.json").read_text())["runs"]
    E = [r for r in E if r["mode"] == "free" and abs(r["drag_mNm"] - 5.0) < 1e-6 and r.get("k_roll") in (3.0, 10.0, 100.0)]
    errs = sorted({r["a_err"] for r in E})
    fig, ax = plt.subplots(figsize=(10, 4.6), dpi=120)
    w = 0.38
    for i, e in enumerate(errs):
        a = [r for r in E if not r["spring"] and r["a_err"] == e]
        b = [r for r in E if r["spring"] and r["a_err"] == e and r.get("f_spring", 6.0) == 6.0]
        if a:
            ja = 100 * sum(r["jam"] for r in a) / len(a)
            ax.bar(i - w / 2, ja, w * 0.95, color="#c33", label="as drawn: jams" if i == 1 else None)
            ax.text(i - w / 2, ja + 1, f"{sum(r['jam'] for r in a)}/{len(a)}", ha="center", fontsize=8, color="#a22")
        if b:
            jb = 100 * sum(r["jam"] for r in b) / len(b)
            sb = 100 * sum(r["outcome"].startswith("stub") for r in b) / len(b)
            ax.bar(i + w / 2, sb, w * 0.95, bottom=jb, color="#bbb", hatch="//", label="spring-loaded: left on the tips, cleared by the seek" if i == 0 else None)
            ax.text(i + w / 2, sb + 1, f"0 jams\n{sum(r['outcome'].startswith('stub') for r in b)}/{len(b)} stubs", ha="center", fontsize=7.5, color="#555")
    ax.set_xticks(range(len(errs)))
    ax.set_xticklabels([f"{e:+.2f}" for e in errs])
    ax.set_ylim(0, 60)
    ax.set_xlabel("pinion this far from its drawn place, away from the gear (mm): the tolerance stack")
    ax.set_ylabel("% of indexes")
    ax.set_title("One index into the station (MuJoCo, real teeth): jams as drawn, none with a 6 N spring-loaded pinion", fontsize=11)
    ax.text(0.99, 0.97, "as drawn: 12 phases x 3 clevis stiffnesses per offset\nspring 6 N: 12 phases x 2 clevis stiffnesses", transform=ax.transAxes,
            ha="right", va="top", fontsize=8, color="#555")
    ax.legend(fontsize=8.5, loc="upper left")
    fig.tight_layout()
    fig.savefig(OUT / "entry_outcomes.png")
    plt.close(fig)


if __name__ == "__main__":
    what = sys.argv[1] if len(sys.argv) > 1 else "plots"
    REN.mkdir(parents=True, exist_ok=True)
    if what == "entry":
        entry_clip()
    elif what == "tilt":
        tilt_clip()
    elif what == "plots":
        print("CR = 1 at", contact_window_plot())
        if (OUT / "entry.json").exists():
            outcome_plots()


# ---------------------------------------------------------------- the spring-loaded pinion (v12 candidate), schematic
def spring_schematic():
    """Front view (Sam y-z, world up drawn up) of the proposed change: the NEMA 11 and pinion on a printed cradle that pivots on a
    3 mm pin level with the pinion's axis, 24 mm to one side; a 1 N/mm spring at 42 mm presses it toward the gear with about 6 N;
    an M3 set screw is the stop 0.4 mm past tight mesh. Drawn to scale over the true tooth outlines."""
    gp, pp = M.tooth_polys()
    fig, ax = plt.subplots(figsize=(11, 6.6), dpi=120)
    ax.set_aspect("equal")
    ax.axis("off")
    a = 34.03
    for P in gear_outline(gp, M.Z2, 0.0, 0.0, 0.0, 20.84):
        ax.add_patch(Polygon(np.c_[P[:, 0], -P[:, 1]], closed=True, color=GREY, lw=0))
    ax.add_patch(Circle((0, 0), 20.9, color=GREY, lw=0))
    for P in gear_outline(pp, M.Z1, math.pi + math.pi / M.Z1, 0.0, -a, 10.75):
        ax.add_patch(Polygon(np.c_[P[:, 0], -P[:, 1]], closed=True, color=ORANGE, lw=0))
    ax.add_patch(Circle((0, a), 10.8, color=ORANGE, lw=0))
    # NEMA 11 face (28 square) behind the pinion, the cradle round it
    ax.add_patch(Rectangle((-14, a - 14), 28, 28, fill=False, ec=DARK, lw=1.2, ls="--"))
    cradle = np.array([[-27, a - 5], [-27, a + 5], [-16, a + 17], [24, a + 17], [24, a + 9], [16, a + 9], [16, a - 15], [-16, a - 15], [-22, a - 5]])
    ax.add_patch(Polygon(cradle, closed=True, fc=GREEN, alpha=0.25, ec=GREEN, lw=1.5))
    ax.add_patch(Circle((-24, a), 1.5, color=DARK))
    ax.annotate("pivot: 3 mm steel pin\nparallel to the auger,\nlevel with the pinion's axis", (-24, a), (-62, a + 22), fontsize=9,
                arrowprops=dict(arrowstyle="->", color=DARK))
    # spring (zigzag) between the EC's cheek (above) and the cradle's arm at y = +18
    zs = np.linspace(a + 17, a + 33, 11)
    ys = 18 + np.r_[0, np.tile([2.5, -2.5], 4), 2.5, 0][:len(zs)]
    ax.plot(ys, zs, color="#a0522d", lw=2)
    ax.add_patch(Rectangle((8, a + 33), 22, 4, color=GREEN, alpha=0.6))
    ax.text(31, a + 35, "EC cheek", fontsize=9, va="center")
    ax.annotate("spring 1 N/mm,\nabout 6 N preload\n(presses the pinion\ninto the gear)", (20.5, a + 25), (36, a + 12), fontsize=9,
                arrowprops=dict(arrowstyle="->", color=DARK))
    # stop screw
    ax.plot([22, 22], [a + 9, a + 3.5], color=DARK, lw=3)
    ax.add_patch(Rectangle((19, a + 1.5), 6, 2, color=GREEN, alpha=0.6))
    ax.annotate("M3 set screw: the stop,\n0.4 mm past tight mesh", (22, a + 3), (36, a - 6), fontsize=9, arrowprops=dict(arrowstyle="->", color=DARK))
    ax.text(0, -27.5, "auger gear, 44T (the module below)", ha="center", fontsize=9)
    ax.text(0, a + 1.5, "24T", ha="center", fontsize=8, color="white")
    ax.add_patch(FancyArrowPatch((-24 + 3, a - 3), (-2, a - 12), connectionstyle="arc3,rad=0.25", arrowstyle="->", mutation_scale=12, color=BLUE))
    ax.text(29, 6, "What it changes\n"
                     "- the pinion always sits in tight mesh (34.0 mm),\n  whatever the tolerance stack\n"
                     "- a tooth landing tip on tip lifts it instead of jamming;\n  a short turn of the motor drops it into the gap\n"
                     "- the preload (6 N) is above the mesh's separating\n  force at the motor's stall (about 3 N), so it stays in",
            fontsize=9, va="top", family="DejaVu Sans")
    ax.set_xlim(-66, 95)
    ax.set_ylim(-31, a + 42)
    ax.set_title("A spring-loaded pinion for the next version (proposed, not in v11's CAD); front view, to scale", fontsize=12)
    fig.tight_layout()
    REN.mkdir(parents=True, exist_ok=True)
    fig.savefig(REN / "spring_pinion_v12.png")
    plt.close(fig)


if __name__ == "__main__" and len(sys.argv) > 1 and sys.argv[1] == "spring":
    spring_schematic()
