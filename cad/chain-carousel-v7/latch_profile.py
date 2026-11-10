"""Profile view of the plate latch (Sam, PR #185, 2026-11-10: "the mounting plate is usually locked in on both sides, but the
side that lets it swing to dose gets released when it comes into the base station. However, there's another pin on the
bottom that can be removed by hand ... Is that right? Show a profile view of how it works.").

A true section through the latch plane (Sam y = LATCH_Y6, the follower's plane) looking along the hinge axis, drawn in 2-D
with matplotlib from OCC sections of the real CAD solids (BRepAlgoAPI_Common of each solid with the plane). Cut faces are
filled and hatched, one colour per part; the auger, its cap and the plate's centre plane are drawn behind as light
silhouettes (their section at Sam y = 0). The section plane moves with the carriage, so the station's fixed cam is cut in
the carriage's latch plane wherever the carriage is: its face in the drawing is the cam profile the follower meets.
Every position comes from the model: the chain path (layout.carriage_frame), the cam's schedule (layout.latch_open) and the
hinge rotation (layout.sam_frame) for the swings.

    python latch_profile.py [--src ../chain-carousel-v6] [--preview]
    -> renders/v7/latch_profile_v7.{gif,mp4} and latch_profile_v7_{closed,station,by_hand}.png

--src picks the design directory whose builders and layout are drawn (default v6's, whose latch v7 keeps unchanged).
"""
from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ap = argparse.ArgumentParser()
ap.add_argument("--src", default=str(HERE.parent / "chain-carousel-v6"))
ap.add_argument("--preview", action="store_true", help="three stills only")
ap.add_argument("--fps", type=float, default=10.0)
ap.add_argument("--frames", default="", help="comma-separated frame indices to write to /tmp/latch_profile_<i>.png, then stop")
ARGS = ap.parse_args()
SRC = Path(ARGS.src).resolve()
sys.path[0:1] = [str(SRC)]                    # import the --src design's modules, not this directory's (v7 is being edited)

import cadquery as cq                         # noqa: E402
import matplotlib                             # noqa: E402
matplotlib.use("Agg")
import matplotlib.pyplot as plt               # noqa: E402
from matplotlib.patches import FancyArrowPatch, PathPatch, Rectangle   # noqa: E402
from matplotlib.path import Path as MPath     # noqa: E402
import numpy as np                            # noqa: E402
from OCP.gp import gp_Trsf                    # noqa: E402
from OCP.TopLoc import TopLoc_Location        # noqa: E402

import layout as L                            # noqa: E402
import parts3 as P3                           # noqa: E402
import parts6 as P6                           # noqa: E402
from params import (AUGER_LEN, P, CHAIN_L, HINGE_W, HINGE_X, KC4_A, KC4_B, KC4_C,  # noqa: E402
                    KEEPER6_X, LATCH6_ENGAGE, LATCH6_FOLLOW_X, LATCH6_HOUSING_X, LATCH6_MANUAL, LATCH6_PIN, LATCH_SPRING,
                    LATCH_TRAVEL, LATCH_Y6, LOOP_B, LOOP_Y, LUG_T, LUG_U4, N_LINKS, PIN_CBORE, R, RUN_DIRECTION, SHELF6,
                    SIDE_GAP, Z_BOT, Z_TOP)

OUT = HERE / "renders" / "v7"
OUT.mkdir(parents=True, exist_ok=True)
Y0 = LATCH_Y6                                  # the section plane, Sam y
K0 = 0                                         # carriage 1
LINK0 = L.carriage_links()[K0]

# ---------------------------------------------------------------- geometry helpers
def xform(shape: cq.Shape, M: np.ndarray) -> cq.Shape:
    tr = gp_Trsf()
    tr.SetValues(*[float(v) for v in M[:3, :].ravel()])
    return cq.Shape.cast(shape.wrapped.Moved(TopLoc_Location(tr)))


def solid_of(w) -> cq.Shape:
    vals = w.vals() if hasattr(w, "vals") else [w]
    return vals[0] if len(vals) == 1 else cq.Compound.makeCompound(vals)


def _loop(wire: cq.Wire) -> np.ndarray:
    n = int(max(24, min(900, wire.Length() / 0.15)))
    pts = wire.positions(np.linspace(0.0, 1.0, n))
    return np.array([(p.x, p.z) for p in pts])


def _area(a: np.ndarray) -> float:
    x, y = a[:, 0], a[:, 1]
    return 0.5 * float(np.dot(x, np.roll(y, -1)) - np.dot(y, np.roll(x, -1)))


def section(shape: cq.Shape, y0: float = Y0) -> list:
    """Faces of `shape` cut by the plane y = y0 (its own frame): [(outer (n, 2) in (x, z), [holes])]."""
    face = cq.Face.makePlane(4000.0, 4000.0, basePnt=(0.0, y0, 0.0), dir=(0.0, 1.0, 0.0))
    try:
        res = shape.intersect(face)
    except Exception:                          # noqa: BLE001
        return []
    out = []
    for f in res.Faces():
        o = _loop(f.outerWire())
        if abs(_area(o)) < 1e-4:
            continue
        if _area(o) < 0:
            o = o[::-1]
        holes = []
        for w in f.innerWires():
            h = _loop(w)
            holes.append(h[::-1] if _area(h) > 0 else h)
        out.append((o, holes))
    return out


def to_draw(polys: list, S: np.ndarray, y0: float, H: np.ndarray) -> list:
    """Section polygons in a Sam frame (x, z at y = y0) -> the drawing: world (x, z) relative to the hinge H, seen from -y."""
    out = []
    for o, holes in polys:
        def m(a):
            P4 = np.c_[a[:, 0], np.full(len(a), y0), a[:, 1], np.ones(len(a))]
            w = (S @ P4.T).T
            return np.c_[w[:, 0] - H[0], w[:, 2] - H[2]]
        out.append((m(o), [m(h) for h in holes]))
    return out


def patch(polys: list, **kw):
    verts, codes = [], []
    for o, holes in polys:
        for ring in [o] + holes:
            verts += ring.tolist() + [ring[0].tolist()]
            codes += [MPath.MOVETO] + [MPath.LINETO] * (len(ring) - 1) + [MPath.CLOSEPOLY]
    if not verts:
        return None
    return PathPatch(MPath(verts, codes), **kw)


def Ty(M, t):
    return L.T(None, t) @ M


# ---------------------------------------------------------------- the solids, each in its own frame
print("building solids ...", flush=True)
REF = L.reference_parts()
SAM_C = np.linalg.inv(L.SAM_IN_CARRIAGE)       # carriage frame -> Sam frame (on the same carriage)
MOD = {                                        # move with the module (tilt about the hinge)
    "plate": solid_of(REF["sam_mounting_plate"]),
    "magnet": [xform(solid_of(P6.kc6_magnet()), L.T(None, (x, y, -18.0))) for (x, y) in (KC4_A, KC4_B, KC4_C)],
}
AUGER = xform(solid_of(REF["auger"]), L.AUGER_IN_SAM)
CAP = xform(solid_of(REF["auger_cap"]), L.AUGER_IN_SAM @ L.T(None, (0, 0, AUGER_LEN)))
CARRIAGE = xform(solid_of(P6.carriage_v6()), SAM_C)
PINS = []
for su in (-1, 1):
    u_head = su * (LUG_U4 + LUG_T - PIN_CBORE[1])
    PINS.append(xform(solid_of(L.shape("clevis_pin")), SAM_C @ L.T(L.Ry(su * math.pi / 2), (u_head, HINGE_W, HINGE_X))))
BOLT = solid_of(P6.latch_bolt_v6())
k0, k1 = KEEPER6_X
d_pin, l_pin, z_pin = LATCH6_PIN
PIN = solid_of(P6._cyl_x(d_pin / 2, k1 - LATCH6_ENGAGE, k1 - LATCH6_ENGAGE + l_pin, LATCH_Y6, z_pin).edges("<X").chamfer(0.5))
FOLLOWER = solid_of(P6.latch_follower_v6())
CAM_STATION = solid_of(L.shape("latch_rail"))  # in the station's Sam frame (layout places it at sam_frame(station, 0))
C1 = P6.LATCH6_CARRIER[1]                      # carrier's back face, closed
SPRING_SEAT = LATCH6_HOUSING_X[1] - 3.0        # the housing channel's back wall (latch_housing_v6: x1 - 3)
SPRING_SOLID = 6 * 0.3                         # the stand-in spring (P3.spring(.., 0.3, 5)): 6 rings of 0.3 mm wire
SPRING_FREE, SPRING_RATE = LATCH_SPRING[1], LATCH_SPRING[2]


def spring_len(lo: float) -> float:
    return SPRING_SEAT - (C1 + lo)


_spring_cache: dict = {}


def spring_polys(lo: float) -> list:
    """The latch spring compressed between the carrier and the housing's back wall (the CAD's stand-in moves it rigidly)."""
    key = round(lo, 1)
    if key not in _spring_cache:
        Ls = max(spring_len(key), SPRING_SOLID)
        s = P3.spring(LATCH_SPRING[0], Ls, 0.3, 5).rotate((0, 0, 0), (0, 1, 0), 90).translate((C1 + key, LATCH_Y6, LATCH6_PIN[2] + 1.0))
        _spring_cache[key] = section(solid_of(s))
    return _spring_cache[key]


# fixed parts in the world (the back and front side plates)
_pl0 = L.placements(L.State(enclosure=False, scale=False, carriages=(), modules=()))
FIXED_WORLD = []
for p in _pl0:
    if p.key in ("side_plate_back", "side_plate_front"):
        FIXED_WORLD.append((p.key, L.moved(p.key, p.M)))
S_STATION = L.sam_frame(L.station_frame(), 0.0)

# static sections in the carriage's own Sam frame
SEC = {
    "plate": section(MOD["plate"]),
    "plate_c": section(MOD["plate"], 0.0),
    "magnet": sum((section(m) for m in MOD["magnet"]), []),
    "auger": section(AUGER, 0.0),
    "cap": section(CAP, 0.0),
    "carriage": section(CARRIAGE),
    "carriage_g": section(CARRIAGE, -29.0),
    "pins": sum((section(p) for p in PINS), []),
    "bolt": section(BOLT),
    "pin": section(PIN),
    "follower": section(xform(FOLLOWER, L.T(None, (LATCH6_FOLLOW_X, LATCH_Y6, 0.0))), Y0),
}
print("static sections done", flush=True)


def chain_world(shift: float, back: bool) -> list:
    """The chain links within about 5 links of carriage 1's link, as world solids."""
    out = []
    for di in range(-6, 7):
        i = (LINK0 + di) % N_LINKS
        key = "chain_a1" if i in L.carriage_links() else ("chain_outer" if i % 2 == 0 else "chain_inner")
        out.append(L.moved(key, L.link_frame(i, back, shift)))
    return out


_fixed_cache: dict = {}


def fixed_polys(shift: float, station: bool) -> dict:
    """Sections of the frame's parts and the chain in carriage 1's latch plane at this chain travel (and the station's cam,
    only near the station)."""
    key = (round(shift, 3), station)
    if key in _fixed_cache:
        return _fixed_cache[key]
    C = L.carriage_frame(LINK0, shift)
    S = L.sam_frame(C, 0.0)
    Sinv = np.linalg.inv(S)
    out = {"side": [], "chain": [], "cam": []}
    for _, w in FIXED_WORLD:
        out["side"] += section(xform(w, Sinv))
    for back in (False, True):
        for w in chain_world(shift, back):
            out["chain"] += section(xform(w, Sinv))
    if station:
        out["cam"] = section(xform(CAM_STATION, Sinv @ S_STATION))
    _fixed_cache[key] = out
    return out


# ---------------------------------------------------------------- drawing
COL = dict(plate=(0.12, 0.33, 0.86), carriage=(0.60, 0.66, 0.74), bolt=(0.96, 0.56, 0.12), pin=(0.58, 0.60, 0.64),
           follower=(0.45, 0.47, 0.50), spring=(0.25, 0.26, 0.28), cam=(0.15, 0.62, 0.32), side=(0.80, 0.82, 0.85),
           chain=(0.30, 0.31, 0.33), magnet=(0.78, 0.16, 0.12), ghost=(0.90, 0.90, 0.91), hinge=(0.40, 0.42, 0.45))
EDGE = lambda c: tuple(0.55 * v for v in c)          # noqa: E731
plt.rcParams.update({"hatch.linewidth": 0.35, "font.family": "DejaVu Sans"})


def draw_cut(ax, polys, col, hatch="////", z=3, lw=0.6, alpha=1.0):
    pp = patch(polys, facecolor=col, edgecolor=EDGE(col), linewidth=lw, hatch=hatch, zorder=z, alpha=alpha)
    if pp is not None:
        ax.add_patch(pp)


def draw_ghost(ax, polys, z=1, col=COL["ghost"], ec=(0.62, 0.63, 0.66)):
    pp = patch(polys, facecolor=col, edgecolor=ec, linewidth=0.6, zorder=z)
    if pp is not None:
        ax.add_patch(pp)


def rot_tilt(theta_deg: float) -> np.ndarray:
    return L.T(L.Ry(math.radians(theta_deg)))


class Frame:
    def __init__(self, title, text, shift=0.0, lo=0.0, tilt=0.0, run="bottom", arrows=None, dims=(), note=None, flag=None):
        self.title, self.text, self.shift, self.lo, self.tilt = title, text, shift, lo, tilt
        self.run, self.arrows, self.dims, self.note, self.flag = run, arrows, dims, note, flag


def draw_scene(ax, fr: Frame, detail: bool):
    C = L.carriage_frame(LINK0, fr.shift)
    S = L.sam_frame(C, 0.0)
    St = L.sam_frame(C, fr.tilt)
    H = L.to_world(S, (0.0, 0.0, 0.0))
    station = fr.run == "bottom" and abs(fr.shift) < 3.0
    fx = fixed_polys(fr.shift, station)
    # behind the cut: the auger and its cap, the plate's centre plane
    draw_ghost(ax, to_draw(SEC["plate_c"], St, 0.0, H), z=1, col=(0.86, 0.89, 0.97), ec=(0.62, 0.68, 0.86))
    draw_ghost(ax, to_draw(SEC["auger"], St, 0.0, H), z=1.2)
    draw_ghost(ax, to_draw(SEC["cap"], St, 0.0, H), z=1.2)
    draw_ghost(ax, to_draw(SEC["carriage_g"], S, -29.0, H), z=0.8, col=(0.93, 0.94, 0.96), ec=(0.72, 0.74, 0.78))
    # the frame and the chain
    draw_cut(ax, to_draw(fx["side"], S, Y0, H), COL["side"], hatch="\\\\\\\\", z=2)
    draw_cut(ax, to_draw(fx["chain"], S, Y0, H), COL["chain"], hatch=None, z=2.5, lw=0.3)
    if fx["cam"]:
        draw_cut(ax, to_draw(fx["cam"], S, Y0, H), COL["cam"], z=3.4)
    # the carriage and the latch
    draw_cut(ax, to_draw(SEC["carriage"], S, Y0, H), COL["carriage"], z=3)
    Mb = S @ L.T(None, (fr.lo, 0.0, 0.0))
    draw_cut(ax, to_draw(SEC["bolt"], Mb, Y0, H), COL["bolt"], z=3.6)
    draw_cut(ax, to_draw(SEC["pin"], Mb, Y0, H), COL["pin"], hatch="....", z=3.7)
    draw_cut(ax, to_draw(SEC["follower"], Mb, Y0, H), COL["follower"], hatch=None, z=3.8)
    draw_cut(ax, to_draw(spring_polys(fr.lo), S, Y0, H), COL["spring"], hatch=None, z=3.5, lw=0.3)
    # the module
    draw_cut(ax, to_draw(SEC["plate"], St, Y0, H), COL["plate"], z=3.2)
    draw_cut(ax, to_draw(SEC["magnet"], St, Y0, H), COL["magnet"], hatch=None, z=3.3)
    draw_cut(ax, to_draw(SEC["pins"], S, Y0, H), COL["hinge"], hatch=None, z=3.9)
    over = spring_len(fr.lo) - SPRING_SOLID
    if over < 0:                                  # the carrier runs into the spring's solid height / the housing's back wall
        x0 = SPRING_SEAT - SPRING_SOLID
        a = to_draw([(np.array([[x0, LATCH6_PIN[2] - 2.6], [C1 + fr.lo, LATCH6_PIN[2] - 2.6], [C1 + fr.lo, LATCH6_PIN[2] + 4.6],
                                [x0, LATCH6_PIN[2] + 4.6]]), [])], S, Y0, H)
        pp = patch(a, facecolor=(1.0, 0.1, 0.1, 0.45), edgecolor=(0.85, 0.0, 0.0), linewidth=1.2, zorder=5)
        ax.add_patch(pp)
    return S, St, H


def W(S, H, x, z, y=Y0):
    p = L.to_world(S, (x, y, z))
    return np.array([p[0] - H[0], p[2] - H[2]])


def setup(ax, xl, yl):
    fig = ax.figure
    bb = ax.get_position()
    wpx, hpx = bb.width * fig.get_figwidth(), bb.height * fig.get_figheight()
    dx, dy = xl[1] - xl[0], yl[1] - yl[0]
    if dx / dy < wpx / hpx:                       # widen x about its centre
        c, dx = (xl[0] + xl[1]) / 2, dy * wpx / hpx
        xl = (c - dx / 2, c + dx / 2)
    else:
        c, dy = (yl[0] + yl[1]) / 2, dx * hpx / wpx
        yl = (c - dy / 2, c + dy / 2)
    ax.set_xlim(*xl)
    ax.set_ylim(*yl)
    ax.set_aspect("equal", adjustable="box")
    ax.set_xticks([])
    ax.set_yticks([])
    for s in ax.spines.values():
        s.set_color((0.8, 0.8, 0.8))


def lab(ax, text, xy, xytext, color=(0.15, 0.15, 0.15), fs=9, ha="left"):
    ax.annotate(text, xy=xy, xytext=xytext, fontsize=fs, color=color, ha=ha, va="center", zorder=10,
                arrowprops=dict(arrowstyle="-", color=(0.35, 0.35, 0.35), lw=0.7, shrinkA=0, shrinkB=1),
                bbox=dict(boxstyle="round,pad=0.2", fc=(1, 1, 1, 0.85), ec="none"))


def swing_arrows(ax, S, St, H, state):
    """At the cap end: IN (into the loop, the dose direction) and OUT, each marked free or blocked."""
    if state is None:
        return
    base = W(St, H, 196.0, -15.5)
    up = W(S, H, 196.0, -60.0) - W(S, H, 196.0, -10.0)
    up = up / np.linalg.norm(up)
    for sgn, name, ok in ((1, "IN (dose)", state[0]), (-1, "OUT", state[1])):
        tip = base + sgn * up * 42.0
        col = (0.05, 0.55, 0.15) if ok else (0.85, 0.08, 0.05)
        ax.add_patch(FancyArrowPatch(tuple(base + sgn * up * 14), tuple(tip), arrowstyle="-|>", mutation_scale=16, lw=2.2, color=col, zorder=9))
        ax.text(*(tip + np.array([-5.0, 0.0])), f"{name}: {'free' if ok else 'blocked'}", color=col, fontsize=10.5,
                fontweight="bold", va="center", ha="right", zorder=10, bbox=dict(boxstyle="round,pad=0.15", fc=(1, 1, 1, 0.85), ec="none"))


def minimap(ax, fr: Frame):
    ax.clear()
    ax.set_aspect("equal")
    ax.axis("off")
    t = np.linspace(0, 2 * np.pi, 400)
    # the pitch-line loop: a rectangle of centres with R rounds
    pts = []
    yc, z0, z1 = LOOP_Y, Z_BOT, Z_TOP
    for (cy, cz, a0) in ((yc, z0, -90), (yc, z1, 0), (-yc, z1, 90), (-yc, z0, 180)):
        for a in np.linspace(a0, a0 + 90, 30):
            pts.append((cy + R * math.cos(math.radians(a)), cz + R * math.sin(math.radians(a))))
    pts.append(pts[0])
    pts = np.array(pts)
    ax.plot(pts[:, 0], pts[:, 1], color=(0.4, 0.4, 0.42), lw=2)
    Hs = L.HINGE_STATION
    ax.plot([Hs[1]], [Z_BOT - R], marker="s", ms=9, color=COL["cam"])
    ax.text(Hs[1], Z_BOT - R - 12, "station", ha="center", fontsize=8, color=COL["cam"], va="top")
    C = L.carriage_frame(LINK0, fr.shift)
    ax.plot([C[1, 3]], [C[2, 3]], marker="o", ms=10, color=COL["bolt"], mec="k")
    ax.text(C[1, 3], C[2, 3] + (18 if fr.run == "top" else 20), "carriage 1", ha="center", fontsize=8)
    d = RUN_DIRECTION
    ax.annotate("", xy=(d * 40, Z_BOT - R - 34), xytext=(-d * 40, Z_BOT - R - 34), arrowprops=dict(arrowstyle="-|>", color=(0.4, 0.4, 0.42)))
    ax.text(0, Z_BOT - R - 44, "the run's direction", ha="center", fontsize=7, color=(0.4, 0.4, 0.42), va="top")
    ax.set_xlim(-LOOP_Y - R - 30, LOOP_Y + R + 30)
    ax.set_ylim(Z_BOT - R - 62, Z_TOP + R + 20)
    ax.set_title("Where the carriage is (seen from the front)", fontsize=9)


def render(fr: Frame, path=None):
    fig = plt.figure(figsize=(16, 9), dpi=100)
    fig.patch.set_facecolor("white")
    fig.text(0.012, 0.965, fr.title, fontsize=17, fontweight="bold", va="center")
    fig.text(0.988, 0.965, "chain carousel v7 latch (unchanged from v6) · PR #185 · section on the latch plane", fontsize=9,
             color=(0.45, 0.45, 0.45), ha="right", va="center")
    ax_o = fig.add_axes([0.01, 0.50, 0.60, 0.43])
    ax_c = fig.add_axes([0.01, 0.02, 0.60, 0.46])
    ax_m = fig.add_axes([0.64, 0.56, 0.15, 0.36])
    ax_t = fig.add_axes([0.63, 0.02, 0.36, 0.52])
    ax_t.axis("off")
    top = fr.run == "top"
    # overview: the whole module in profile
    S, St, H = draw_scene(ax_o, fr, False)
    f = 1 if not top else -1                      # drawing y of "into the loop"
    yl = (-62, 128) if not top else (-60, 70)
    setup(ax_o, (-80, 318), yl)
    ax_o.plot([0], [0], marker="+", ms=14, mew=2, color="k", zorder=11)

    def L2(ax, text, anchor, off, **kw):
        a_ = np.asarray(anchor, float)
        lab(ax, text, tuple(a_), (a_[0] + off[0], a_[1] + f * off[1]), **kw)
    def LA(ax, text, anchor, at, **kw):          # a label at an absolute drawing position (y mirrored on the top run)
        lab(ax, text, tuple(np.asarray(anchor, float)), (at[0], f * at[1]), **kw)
    LA(ax_o, "hinge axis (5 mm pins in the carriage's lugs)", (0.0, 0.0), (-76, -30), fs=9)
    LA(ax_o, "auger and cap (behind the cut)", W(St, H, 60.0, 12.0, 0.0), (-76, -52), fs=9)
    LA(ax_o, "mounting plate (cut on the latch plane)", W(St, H, 90.0, -15.5), (-60, 46), fs=9)
    LA(ax_o, "carriage (behind the cut)", W(S, H, 222.0, -20.6), (214, 50), fs=9)
    LA(ax_o, "back side plate", W(S, H, 305.0, -75.0 if not top else -40.0), (296, 104 if not top else 52), fs=9, ha="right")
    by = -28 if not top else -40
    ax_o.add_patch(Rectangle((228, by), 84, 68, fill=False, ec=(0.2, 0.2, 0.2), lw=0.8, ls="--", zorder=11))
    ax_o.text(310, by - 2 if not top else by + 70, "close-up below", fontsize=8, color=(0.2, 0.2, 0.2), zorder=11, ha="right",
              va="top" if not top else "bottom")
    ax_o.text(-78, yl[1] - 6, "into the loop " + ("↑" if not top else "↓ (top run: the loop is below)"), fontsize=9,
              color=(0.3, 0.3, 0.3), va="top")
    swing_arrows(ax_o, S, St, H, fr.arrows)
    # close-up: the latch
    draw_scene(ax_c, fr, True)
    setup(ax_c, (226, 314), (-27, 41) if not top else (-41, 27))
    lo = fr.lo
    xr, xl_ = 311.5, 241.0                         # label columns right of the side plate and left of the keeper
    LA(ax_c, "chain", W(S, H, 277.0, -31.0), (xr, 34), fs=9.5)
    LA(ax_c, "carriage", W(S, H, 279.0, -20.6), (xr, 26), fs=9.5)
    LA(ax_c, "latch housing (on the carriage)", W(S, H, 278.0, -10.0), (xr, 18), fs=9.5)
    LA(ax_c, "spring", W(S, H, C1 + lo + max(spring_len(lo), 1.0) / 2, LATCH6_PIN[2] + 2.0), (xr, 10), fs=9.5)
    LA(ax_c, "bolt carrier", W(S, H, 268.5 + lo, -6.0), (xr, 2), fs=9.5)
    LA(ax_c, "follower (3 mm dowel)", W(S, H, LATCH6_FOLLOW_X + lo + 1.5, 4.0), (xr, -6), fs=9.5)
    LA(ax_c, "keeper (on the plate's back end)", W(St, H, 247.0, -16.0), (xl_, 31), fs=9.5, ha="right")
    LA(ax_c, "4 mm pin", W(S, H, k1 - LATCH6_ENGAGE + 1.5 + lo, LATCH6_PIN[2]), (xl_, 21), fs=9.5, ha="right")
    LA(ax_c, "rest shelf (same bolt)", W(S, H, 247.0 + lo, -6.8), (xl_, -3), fs=9.5, ha="right")
    if fr.run == "bottom" and abs(fr.shift) < 3.0:
        LA(ax_c, "cam (fixed, at the station)", W(S, H, 257.5, 5.0), (xl_, -14), fs=9.5, ha="right", color=(0.05, 0.45, 0.2))
    s_ = -1 if not top else 1
    for (x0, x1, z, txt) in fr.dims:
        a_, b_ = W(S, H, x0, z), W(S, H, x1, z)
        ax_c.annotate("", xy=tuple(a_), xytext=tuple(b_), arrowprops=dict(arrowstyle="<->", color=(0.05, 0.05, 0.05), lw=1.1), zorder=12)
        ax_c.text((a_[0] + b_[0]) / 2, a_[1] - f * 3.6, txt, ha="center", fontsize=10.5, fontweight="bold", zorder=12, va="center",
                  bbox=dict(boxstyle="round,pad=0.15", fc=(1, 1, 0.75), ec="none"))
    minimap(ax_m, fr)
    # readouts and caption
    pin_in = max(0.0, LATCH6_ENGAGE - fr.lo)
    shelf_in = max(0.0, SHELF6[0] - fr.lo)
    rd = [("bolt drawn back", f"{fr.lo:4.1f} mm"), ("pin in the keeper's hole", f"{pin_in:4.1f} mm"),
          ("shelf under the keeper", f"{shelf_in:4.1f} mm"), ("plate swung about the hinge", f"{fr.tilt:+5.1f}°")]
    for i, (a, b) in enumerate(rd):
        fig.text(0.81, 0.89 - i * 0.045, a, fontsize=10, color=(0.3, 0.3, 0.3))
        fig.text(0.985, 0.89 - i * 0.045, b, fontsize=11, fontweight="bold", ha="right", family="DejaVu Sans Mono")
    ax_t.text(0.0, 1.0, fr.text, fontsize=12.5, va="top", ha="left", wrap=True, transform=ax_t.transAxes, linespacing=1.45)
    if fr.flag:
        ax_t.text(0.0, 0.30, fr.flag, fontsize=10, va="bottom", ha="left", color=(0.8, 0.0, 0.0), transform=ax_t.transAxes,
                  linespacing=1.35, bbox=dict(boxstyle="round,pad=0.35", fc=(1, 0.93, 0.93), ec=(0.8, 0.0, 0.0)))
    if fr.note:
        ax_t.text(0.0, 0.0, fr.note, fontsize=10, va="bottom", ha="left", color=(0.35, 0.35, 0.35), transform=ax_t.transAxes, linespacing=1.4)
    fig.canvas.draw()
    img = np.asarray(fig.canvas.buffer_rgba())[:, :, :3].copy()
    if path:
        fig.savefig(path, dpi=100)
    plt.close(fig)
    return img


def wrap(s: str, n: int = 58) -> str:
    import textwrap
    return "\n".join(textwrap.fill(p, n) for p in s.split("\n"))


# ---------------------------------------------------------------- the story
def lo_at(shift: float) -> float:
    return L.latch_open(K0, L.State(shift=shift))


SHIFT_IN = 2.5                                  # links before the station (the machine runs -shift: it arrives from +y)
NOTE = wrap("Section on the latch plane (Sam y 21), looking along the hinge axis. Cut faces hatched; the auger, cap and the "
            "plate's centre plane are drawn behind, light. Every position is the CAD's: the chain path, the cam's schedule and "
            "the hinge rotation.", 70)
issue = spring_len(LATCH_TRAVEL) < SPRING_SOLID or spring_len(LATCH6_MANUAL) < SPRING_SOLID
FLAG_CAM = None
FLAG_HAND = None
if spring_len(LATCH_TRAVEL) < SPRING_SOLID:
    FLAG_CAM = wrap(f"CAD issue: the spring pocket is {spring_len(0):.1f} mm long closed, so at the cam's {LATCH_TRAVEL} mm the spring "
                    f"would be {spring_len(LATCH_TRAVEL):.1f} mm (solid). Its spec (12.7 mm free, 0.25 N/mm) wants "
                    f"{SPRING_FREE - 0.9 / SPRING_RATE:.1f} mm closed.", 62)
if spring_len(LATCH6_MANUAL) < SPRING_SOLID:
    FLAG_HAND = wrap(f"CAD issue: the housing's channel ends {spring_len(0):.1f} mm behind the closed carrier, so the bolt can't go "
                     f"back {LATCH6_MANUAL:.0f} mm (red: {-(spring_len(LATCH6_MANUAL)):.1f} mm into the back wall, spring solid). "
                     f"The channel and spring need about {LATCH6_MANUAL + 4.0 - spring_len(0):.0f} mm more length.", 62)


def story() -> list:
    fps = ARGS.fps
    fr: list = []

    def hold(f: Frame, sec: float):
        fr.extend([f] * max(1, int(round(sec * fps))))

    def ease(t):
        return 0.5 - 0.5 * math.cos(math.pi * t)

    T1 = "1. Away from the station: locked both ways"
    t1 = wrap("One spring bolt on the carriage does all the locking. Its 4 mm pin sits 4 mm deep in the hole in the keeper on "
              "the plate's back end, so the plate can swing neither in nor out. Its rest shelf sits under the keeper.\n\nOn the "
              "top run the module rides on top of the loop, upside down from how it hangs at the station; the pin holds it the "
              "same way.")
    hold(Frame(T1 + " (top run)", t1, shift=52.0, run="top", arrows=(False, False)), 4.0)
    t1b = wrap("On the bottom run the module hangs under its carriage. The pin still holds it both ways. "
               "There is no second pin: the pin and the shelf are on the same bolt.")
    hold(Frame(T1 + " (bottom run)", t1b, shift=SHIFT_IN + 3.0, arrows=(False, False)), 3.0)
    T2 = "2. Indexing into the station: the cam opens the latch"
    t2 = wrap("As the carriage indexes in, the follower meets the station's fixed cam (25° ramps) and the bolt is drawn back "
              "4.5 mm, with no human input. The pin leaves the keeper, but the shelf is still 3.5 mm under it: the module now "
              "rests on its own carriage.")
    n = int(4.0 * fps)
    for i in range(n + 1):
        s = (SHIFT_IN + 3.0) * (1 - ease(i / n))
        hold(Frame(T2, t2, shift=s, lo=lo_at(s), arrows=None), 1 / fps)
    k1_ = KEEPER6_X[1]
    dims = [(k1_ - SHELF6[0] + LATCH_TRAVEL, k1_, -7.0, f"{SHELF6[0] - LATCH_TRAVEL:.1f} mm")]
    hold(Frame(T2, t2, shift=0.0, lo=lo_at(0.0), arrows=(True, False), dims=dims, flag=FLAG_CAM), 3.5)
    T3 = "3. Dosing: the plate swings IN, never out"
    t3 = wrap("With the pin out, the docked electronics carriage can swing the module IN about the hinge (into the loop, the "
              "dose direction; shown to 25° here). The keeper simply lifts off the shelf. The shelf still stops it swinging "
              "OUT.\n\nBack at 0°, the keeper settles onto the shelf again.")
    n = int(5.0 * fps)
    for i in range(n + 1):
        th = 25.0 * math.sin(math.pi * i / n)
        hold(Frame(T3, t3, shift=0.0, lo=lo_at(0.0), tilt=th, arrows=(True, False)), 1 / fps)
    T4 = "4. Leaving: the spring shuts the latch"
    t4 = wrap("The next index takes the follower down the cam's far ramp. The spring pushes the bolt forward and the pin goes "
              "back into the keeper: locked both ways again for the rest of the lap.")
    n = int(3.5 * fps)
    for i in range(n + 1):
        s = -(SHIFT_IN + 1.0) * ease(i / n)
        hold(Frame(T4, t4, shift=s, lo=lo_at(s), arrows=None), 1 / fps)
    hold(Frame(T4, t4, shift=-(SHIFT_IN + 1.0), lo=0.0, arrows=(False, False)), 1.5)
    T5 = "5. By hand only (maintenance): the shelf clears, the plate can swing OUT"
    t5 = wrap("The only way the outward direction opens: push the bolt back 10 mm by hand (with the follower) and the shelf "
              "clears the keeper too, so the plate can swing out, away from the carriage, to come off. It is the same bolt "
              "pushed further, not a second pin.\n\nNothing in normal running needs the outward swing, so a fixed stop in "
              "place of this position would be the more robust choice Sam mentions.")
    n = int(2.0 * fps)
    s5 = -(SHIFT_IN + 1.0)
    for i in range(n + 1):
        lo = LATCH6_MANUAL * ease(i / n)
        hold(Frame(T5, t5, shift=s5, lo=lo, arrows=None, flag=FLAG_HAND if lo > 5.5 else None), 1 / fps)
    n = int(3.0 * fps)
    for i in range(n + 1):
        th = -8.0 * math.sin(math.pi * i / n)
        hold(Frame(T5, t5, shift=s5, lo=LATCH6_MANUAL, tilt=th, arrows=(True, True), flag=FLAG_HAND), 1 / fps)
    n = int(1.5 * fps)
    for i in range(n + 1):
        lo = LATCH6_MANUAL * (1 - ease(i / n))
        hold(Frame(T5, t5, shift=s5, lo=lo, arrows=None, flag=FLAG_HAND if lo > 5.5 else None), 1 / fps)
    hold(Frame(T5, t5, shift=s5, lo=0.0, arrows=(False, False)), 1.5)
    for f in fr:
        f.note = NOTE
    return fr


def main():
    frames = story()
    print(len(frames), "frames;", f"{len(frames) / ARGS.fps:.1f} s", flush=True)
    if ARGS.frames:
        for i in [int(v) for v in ARGS.frames.split(",")]:
            render(frames[i], f"/tmp/latch_profile_{i}.png")
            print("frame", i, frames[i].title, flush=True)
        return
    stills = {"closed": next(f for f in frames if f.title.startswith("1.") and f.run == "bottom"),
              "station": next(f for f in frames if f.title.startswith("2.") and f.dims),
              "by_hand": [f for f in frames if f.title.startswith("5.") and f.tilt < -7.9][0]}
    for name, f in stills.items():
        render(f, OUT / f"latch_profile_v7_{name}.png")
        print("still", name, flush=True)
    if ARGS.preview:
        return
    import imageio.v2 as imageio
    from PIL import Image
    imgs, keys = [], []
    last_key, last_img = None, None
    for i, f in enumerate(frames):
        key = (f.title, round(f.shift, 4), round(f.lo, 3), round(f.tilt, 3), f.flag, f.arrows, tuple(f.dims))
        img = last_img if key == last_key else render(f)
        imgs.append(img)
        keys.append(key)
        last_key, last_img = key, img
        if i % 25 == 0:
            print(f"frame {i}/{len(frames)}", flush=True)
    mp4 = OUT / "latch_profile_v7.mp4"
    with imageio.get_writer(mp4, fps=ARGS.fps, codec="libx264", quality=8, macro_block_size=8, pixelformat="yuv420p") as w:
        for im in imgs:
            w.append_data(im)
    # GIF: 2x smaller, one shared palette, identical consecutive frames merged into one longer frame
    small = [Image.fromarray(im).resize((im.shape[1] // 2, im.shape[0] // 2), Image.LANCZOS) for im in imgs]
    picks = [small[int(i)] for i in np.linspace(0, len(small) - 1, 10)]       # one palette from frames of every stage
    mosaic = Image.new("RGB", (picks[0].width, picks[0].height * len(picks)))
    for j, im in enumerate(picks):
        mosaic.paste(im, (0, j * im.height))
    base = mosaic.quantize(colors=200, method=Image.Quantize.MEDIANCUT).getpalette()[: 200 * 3]
    exact = [COL[k] for k in COL] + [EDGE(COL[k]) for k in COL] + [(0.05, 0.55, 0.15), (0.85, 0.08, 0.05), (0.8, 0.0, 0.0),
                                                                  (1.0, 0.93, 0.93), (1.0, 1.0, 0.75), (1.0, 0.55, 0.55)]
    extra = [int(round(255 * v)) for c in exact for v in c]
    pal = Image.new("P", (1, 1))
    pal.putpalette((extra + base)[: 256 * 3])
    gif_frames, durs = [], []
    for j, (im, k) in enumerate(zip(small, keys)):
        if j and k == keys[j - 1]:
            durs[-1] += 1000.0 / ARGS.fps
            continue
        gif_frames.append(im.quantize(palette=pal, dither=Image.Dither.NONE))
        durs.append(1000.0 / ARGS.fps)
    gif = OUT / "latch_profile_v7.gif"
    gif_frames[0].save(gif, save_all=True, append_images=gif_frames[1:], duration=[int(d) for d in durs], loop=0, optimize=True)
    print("wrote", mp4, gif, f"{gif.stat().st_size / 1e6:.1f} MB", flush=True)


if __name__ == "__main__":
    main()
