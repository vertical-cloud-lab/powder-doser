"""One-piece base for the three-auger tri-star (B2 with #203's tap bracket), issue #204, 13 Nov.

Ethan asked for detailed dimensions of the base, with the hinge towers merged into
it. He has also cut the gears and their arms off the mounting plate, so the plate is
now widest at the stepper mount.  This script:

* models the plate that way: PR #170's plate body without the gears, the webs and the
  floor's front wings (|x| > 34 mm), plus the clevis block's two holes;
* builds the base as one part: a 6 mm shelf (three tapered lobes round a 78 mm window,
  a slot per module for the clevis block and actuator rod, now ending 112 mm behind the
  hinge instead of 120, and four hanger holes per lobe), small enough for one H2D nozzle
  and six hinge towers.  The towers are copied from today's baseplate (PR #170's
  baseplate.step): same profile, 12.3 mm wide, 5.3 mm bore;
* checks every moving part against the base over 0-90 deg (2 mm target) at the
  tri-star's spacing (hinges 32 mm from the beaker axis);
* writes base/base.step and base/base.stl, base.json, renders/base_drawing.png (the
  dimensioned drawing) and renders/base_iso.png.

    pip install cadquery trimesh python-fcl rtree vtk pillow numpy matplotlib
    xvfb-run -a python base.py        # about 20 s; --no-checks reuses the checks in base.json

Frames: the unit frame of doserlib.py (hinge axis = X, +Y = behind the hinge, Z up,
hinge at z = 0, shelf top at z = -37.25).  The drawing and the STEP file use the
beaker axis as the origin, with z = 0 on the base's underside.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
import cadquery as cq

import doserlib as D
import concepts as C
import components as K

HERE = Path(__file__).resolve().parent
OUT = HERE / "renders"
CAD = HERE / "base"
SP = K.SP                         # 32 mm: hinge axis to beaker axis
T = 6.0                           # shelf thickness, as today's baseplate
TOP, BOT = D.BASE_TOP_U, D.BASE_BOT_U       # shelf top / underside in the unit frame (-37.25 / -43.25)
GAP = 2.0
LOBE = dict(half_w=50.0, y_wide=50.0, half_w_end=24.0, y_end=142.0, root=15.0, r=10.0)
WIN_D = 78.0                      # 250 mL beaker (70 mm) + 4 mm a side, as before
SLOT = dict(K.SLOT, y1=112.0)     # |x| < 17, 33..112 mm behind the hinge (clevis block + rod; was ..120)
PAD = dict(x=14.5, y=(119.0, 133.0), d=4.5)  # hanger (or leg) holes, M4
BED = (325.0, 320.0)              # Bambu H2D, one nozzle (a single-filament print)
TOWER_X = (28.9, 41.2)            # today's towers, |x| from the module centreline
WING_CUT_X, WING_CUT_Y = 34.0, 70.0          # trim the plate's floor to |x| <= 34 up to 70 mm behind the hinge
BEARINGS = (90.0, 210.0, 330.0)


# --------------------------------------------------------------------------- #
# geometry
# --------------------------------------------------------------------------- #
_S: dict = {}


def tower_today():
    """Today's +X hinge tower, cut out of PR #170's baseplate above its top face, in the unit frame."""
    if "tower" not in _S:
        bp = D.step_shape("fusion-step/baseplate.step")
        H = D.HINGE
        tw = bp.intersect(cq.Solid.makeBox(20.0, 70.0, 60.0, cq.Vector(25.0, H[1] - 25.0, 6.0)))
        _S["tower"] = tw.moved(C._loc(D.W2U)).clean()
    return _S["tower"]


def tower_profile():
    """The tower's side profile (y behind the hinge, z above it) from a section at mid-width."""
    tw = tower_today()
    xm = sum(TOWER_X) / 2
    sec = tw.intersect(cq.Solid.makeBox(0.01, 200, 200, cq.Vector(xm, -100, -100)))
    face = next(f for f in sec.Faces() if abs(f.normalAt().x) > 0.9 and f.Center().x < xm + 0.005)
    out = []
    for e in face.Edges():
        a, b = e.startPoint(), e.endPoint()
        row = dict(kind=e.geomType().lower(), start=[round(a.y, 2), round(a.z, 2)], end=[round(b.y, 2), round(b.z, 2)])
        if e.geomType() == "CIRCLE":
            c = e.arcCenter()
            row.update(radius=round(e.radius(), 2), centre=[round(c.y, 2), round(c.z, 2)])
        out.append(row)
    return out


def plate_trimmed():
    """PR #170's plate without gears, webs and the floor's front wings (Ethan, 13 Nov), plus the
    clevis block's two holes, in the plate's STEP frame (as components.plate_with_holes)."""
    if "plate" not in _S:
        Mown = D.W2U @ D.L.placements(0.0)["Mounting plate"][1]
        inv = C._loc(np.linalg.inv(Mown))
        pl = K.plate_with_holes()
        for sx in (1, -1):
            x0 = WING_CUT_X if sx > 0 else -WING_CUT_X - 40.0
            pl = pl.cut(D.box(x0, x0 + 40.0, -30.0, WING_CUT_Y, -60.0, 40.0).moved(inv))
        _S["plate"] = pl.clean()
    return _S["plate"]


def plate_split():
    """The trimmed plate in two pieces: inboard of the towers' inner faces (|x| < 28.75: the knuckles and
    the arms under them, which run 0.3 mm from the towers' inner faces, as today) and the rest, which
    must clear the base by 2 mm."""
    if "split" not in _S:
        Mown = D.W2U @ D.L.placements(0.0)["Mounting plate"][1]
        inv = C._loc(np.linalg.inv(Mown))
        pl = plate_trimmed()
        mid = D.box(-28.75, 28.75, -40.0, 140.0, -60.0, 40.0).moved(inv)
        _S["split"] = (pl.intersect(mid).clean(), pl.cut(mid).clean())
    return _S["split"]


def lobe_pts():
    """One lobe of the shelf, unit frame (the beaker axis is at y = -SP)."""
    w, yw, we, ye, rt = (LOBE[k] for k in ("half_w", "y_wide", "half_w_end", "y_end", "root"))
    y0 = -SP - rt
    return [(-w, y0), (w, y0), (w, yw), (we, ye), (-we, ye), (-w, yw)]


def station_xy(M, pts):
    return [tuple((M @ np.array([x, y, 0.0, 1.0]))[:2]) for x, y in pts]


def shelf_outline_sketch():
    sk = cq.Sketch()
    for i, th in enumerate(BEARINGS):
        pts = station_xy(D.place(th, SP, 0.0), lobe_pts())
        sk = sk.polygon(pts + [pts[0]], mode="a")
    return sk.clean().reset().vertices().fillet(LOBE["r"]).reset()


def base_station():
    """The base as one solid, station frame (beaker axis = Z, hinge axes at z = 0)."""
    if "base" in _S:
        return _S["base"]
    sk = shelf_outline_sketch()
    shelf = cq.Workplane("XY", origin=(0, 0, BOT)).placeSketch(sk).extrude(T).val()
    shelf = shelf.cut(D.cyl(WIN_D / 2, T + 2, 0, 0, BOT - 1))
    for th in BEARINGS:
        loc = C._loc(D.place(th, SP, 0.0))
        cut = D.box(-SLOT["x"], SLOT["x"], SLOT["y0"], SLOT["y1"], BOT - 1, TOP + 1)
        for x in (-PAD["x"], PAD["x"]):
            for y in PAD["y"]:
                cut = cut.fuse(D.cyl(PAD["d"] / 2, T + 2, x, y, BOT - 1))
        shelf = shelf.cut(cut.moved(loc))
    base = shelf
    tw = tower_today()
    tw_neg = tw.mirror("YZ", (0, 0, 0))          # a true mirror (a det = -1 matrix would turn the solid inside out)
    for th in BEARINGS:
        loc = C._loc(D.place(th, SP, 0.0))
        base = base.fuse(tw.moved(loc)).fuse(tw_neg.moved(loc))
    _S["base"] = base.clean()
    return _S["base"]


# --------------------------------------------------------------------------- #
# checks
# --------------------------------------------------------------------------- #
def shelf_only():
    if "shelf" not in _S:
        sk = shelf_outline_sketch()
        sh = cq.Workplane("XY", origin=(0, 0, BOT)).placeSketch(sk).extrude(T).val()
        _S["shelf"] = sh.cut(D.cyl(WIN_D / 2, T + 2, 0, 0, BOT - 1))
    return _S["shelf"]


def station_parts(tilts, units="ABC"):
    """The modules' parts at ``tilts`` (no placeholder towers, hangers, U-brackets or their pins), the
    trimmed plate split in two (plate_split), the base as one fixed part, and its shelf alone."""
    parts = []
    inner, outer = plate_split()
    for i, th in enumerate(BEARINGS):
        if "ABC"[i] not in units:
            continue
        M = D.place(th, SP, 0.0)
        for p in K.module(float(tilts[i]), M, "ABC"[i], with_hanger=False):
            if p.kind == "tower" or p.name.endswith(("P16 bracket", "#8-32 pin")):
                continue
            if p.name.endswith("Mounting plate"):
                parts.append(D.Part(p.name + " (inboard)", inner, p.M, p.colour, p.unit, True))
                p.shape = outer
            parts.append(p)
    parts.append(D.Part("base", base_station(), np.eye(4), (0.95, 0.47, 0.18), "fixed", False))
    parts.append(D.Part("shelf", shelf_only(), np.eye(4), (0.95, 0.47, 0.18), "fixed", False))
    return parts


def pair_ok(a, b):
    """Which pairs to measure: different units; the plate's inboard piece against the shelf only (it runs
    0.3 mm from its own towers by design); everything else against the whole base."""
    if a.unit == b.unit:
        return False
    for x, y in ((a, b), (b, a)):
        if y.name == "shelf":
            return x.name.endswith("(inboard)")
        if y.name == "base" and x.name.endswith("(inboard)"):
            return False
    return True


def clear(parts, only=None):
    import fcl
    objs = [(p, fcl.CollisionObject(D._bvh(p.shape), fcl.Transform(p.M[:3, :3], p.M[:3, 3]))) for p in parts]
    best = (1e9, None, None)
    req = fcl.DistanceRequest(enable_nearest_points=False)
    for i in range(len(objs)):
        for j in range(i + 1, len(objs)):
            pa, oa = objs[i]
            pb, ob = objs[j]
            if not pair_ok(pa, pb) or (only and not only(pa, pb)):
                continue
            d = fcl.distance(oa, ob, req, fcl.DistanceResult())
            if d < best[0]:
                best = (d, pa.name, pb.name)
    return best


CASES = [(0, 0, 0), (30, 30, 30), (45, 45, 45), (60, 60, 60), (90, 90, 90), (90, 0, 0),
         (60, 0, 0), (90, 90, 0), (60, 60, 0), (30, 60, 0)]


def checks():
    """(1) one module's parts against the base, 0..90 deg in 5 deg steps; (2) the three modules against
    each other and the base at the B2T tilt cases; (3) the hinge's running gap (knuckle to tower)."""
    out = {}
    worst, per_tilt = (1e9, None, None, None), {}
    for t in range(0, 91, 5):
        d, a, b = clear(station_parts((t, 0, 0), units="A"))
        per_tilt[str(t)] = round(d, 2)
        if d < worst[0]:
            worst = (d, a, b, t)
    out["one_module_to_base"] = dict(mm=round(worst[0], 2), between=f"{worst[1]} / {worst[2]}", at_tilt=worst[3],
                                     by_tilt=per_tilt)
    print("  one module:", out["one_module_to_base"], flush=True)
    cases = {}
    for c in CASES:
        ps = station_parts(c)
        d, a, b = clear(ps)
        dm, am, bm = clear(ps, only=lambda x, y: "fixed" not in (x.unit, y.unit))
        cases[",".join(map(str, c))] = dict(mm=round(d, 2), between=f"{a} / {b}", modules_only_mm=round(dm, 2),
                                            modules_only_between=f"{am} / {bm}")
        print(f"  tilts {c}: {d:.2f} mm ({a} / {b}); between modules {dm:.2f} ({am} / {bm})", flush=True)
    out["station_cases"] = cases
    pl = plate_trimmed()
    Mown = D.W2U @ D.L.placements(0.0)["Mounting plate"][1]
    m = D.mesh_of(pl)
    v = (Mown[:3, :3] @ np.asarray(m.vertices).T).T + Mown[:3, 3]
    near = v[np.hypot(v[:, 1], v[:, 2]) < 7.6]
    kx = float(np.abs(near[:, 0]).max())
    out["knuckle_outer_face_x"] = round(kx, 2)
    out["knuckle_to_tower_gap"] = round(TOWER_X[0] - kx, 2)
    return out


def plate_extent():
    pl = plate_trimmed()
    Mown = D.W2U @ D.L.placements(0.0)["Mounting plate"][1]
    m = D.mesh_of(pl)
    v = (Mown[:3, :3] @ np.asarray(m.vertices).T).T + Mown[:3, 3]
    lo, hi = v.min(0), v.max(0)
    floor = v[(v[:, 2] < TOP + 2.0 + 6.5) & (v[:, 2] > TOP + 1.5)]
    widest_y = float(floor[np.argmin(floor[:, 0]), 1])
    return dict(x=[round(lo[0], 2), round(hi[0], 2)], y=[round(lo[1], 2), round(hi[1], 2)], z=[round(lo[2], 2), round(hi[2], 2)],
                width=round(hi[0] - lo[0], 2), widest_at_y_behind_hinge=round(widest_y, 1),
                volume_cm3=round(pl.Volume() / 1000.0, 1))


# --------------------------------------------------------------------------- #
# export
# --------------------------------------------------------------------------- #
def base_export_shape():
    """Base with the beaker axis at the origin and z = 0 on its underside."""
    return base_station().moved(cq.Location(cq.Vector(0, 0, -BOT)))


def export():
    CAD.mkdir(parents=True, exist_ok=True)
    sh = base_export_shape()
    cq.exporters.export(cq.Workplane().add(sh), str(CAD / "base.step"))
    cq.exporters.export(cq.Workplane().add(sh), str(CAD / "base.stl"), tolerance=0.05, angularTolerance=0.1)
    bb = sh.BoundingBox()
    return dict(x=[round(bb.xmin, 2), round(bb.xmax, 2)], y=[round(bb.ymin, 2), round(bb.ymax, 2)],
                z=[round(bb.zmin, 2), round(bb.zmax, 2)], volume_cm3=round(sh.Volume() / 1000.0, 1))


# --------------------------------------------------------------------------- #
# figures
# --------------------------------------------------------------------------- #
INK, GREY, ORANGE, TOWER_C = "#1f1f1f", "#8a8a8a", "#f2a65a", "#c46a1c"


def _dim(ax, p1, p2, off, text, fs=8.5, ext=True, tpos=0.5, tshift=0.0, col=INK):
    """Linear dimension between p1 and p2, drawn ``off`` mm to the left of p1 -> p2."""
    p1, p2 = np.asarray(p1, float), np.asarray(p2, float)
    u = (p2 - p1) / np.linalg.norm(p2 - p1)
    n = np.array([-u[1], u[0]])
    a, b = p1 + n * off, p2 + n * off
    if ext:
        sgn = 1.0 if off >= 0 else -1.0
        for p, q in ((p1, a), (p2, b)):
            ax.plot([p[0] + n[0] * sgn * 1.0, q[0] + n[0] * sgn * 2.0], [p[1] + n[1] * sgn * 1.0, q[1] + n[1] * sgn * 2.0],
                    lw=0.45, color=col)
    ax.annotate("", xy=b, xytext=a, arrowprops=dict(arrowstyle="<|-|>", lw=0.7, color=col, shrinkA=0, shrinkB=0,
                                                    mutation_scale=7))
    ang = math.degrees(math.atan2(u[1], u[0]))
    if ang > 90.5 or ang < -89.5:
        ang -= 180.0
    m = a + (b - a) * tpos + u * tshift
    ax.text(m[0], m[1], text, rotation=ang, ha="center", va="center", fontsize=fs, color=col,
            bbox=dict(boxstyle="square,pad=0.12", fc="white", ec="none"))


def _note(ax, xy, text, xytext, fs=8.5, col=INK, ha="left"):
    ax.annotate(text, xy=xy, xytext=xytext, fontsize=fs, color=col, ha=ha, va="center",
                arrowprops=dict(arrowstyle="-|>", lw=0.6, color=col, mutation_scale=7, shrinkA=2, shrinkB=0),
                bbox=dict(boxstyle="square,pad=0.15", fc="white", ec="none"))


def _wire_xy(w, n=24):
    pts = []
    for e in w.Edges():
        k = n if e.geomType() != "LINE" else 2
        pts += [(e.positionAt(t).x, e.positionAt(t).y) for t in np.linspace(0, 1, k)]
    return np.array(pts)


def _rot(th):
    """Station -> drawing frame of one lobe: the module at bearing ``th`` points up (+y), x to its +X."""
    r = math.radians(90.0 - th)
    return np.array([[math.cos(r), -math.sin(r)], [math.sin(r), math.cos(r)]])


def _plan_geometry(ax, R2=np.eye(2), lw=0.9, towers=True, centre_lines=True):
    face = shelf_outline_sketch()._faces.Faces()[0]
    out = _wire_xy(face.outerWire()) @ R2.T
    ax.fill(out[:, 0], out[:, 1], color="#fbe3c8", zorder=0)
    ax.plot(out[:, 0], out[:, 1], color=INK, lw=lw)
    t = np.linspace(0, 2 * math.pi, 200)
    ax.fill(WIN_D / 2 * np.cos(t), WIN_D / 2 * np.sin(t), color="white", zorder=1)
    ax.plot(WIN_D / 2 * np.cos(t), WIN_D / 2 * np.sin(t), color=INK, lw=lw, zorder=2)
    for th in BEARINGS:
        M = D.place(th, SP, 0.0)
        def tr(pts):
            return np.array(station_xy(M, pts)) @ R2.T
        sl = tr([(-SLOT["x"], SLOT["y0"]), (SLOT["x"], SLOT["y0"]), (SLOT["x"], SLOT["y1"]), (-SLOT["x"], SLOT["y1"]),
                 (-SLOT["x"], SLOT["y0"])])
        ax.fill(sl[:, 0], sl[:, 1], color="white", zorder=1)
        ax.plot(sl[:, 0], sl[:, 1], color=INK, lw=lw, zorder=2)
        for x in (-PAD["x"], PAD["x"]):
            for y in PAD["y"]:
                c = tr([(x, y)])[0]
                ax.fill(c[0] + PAD["d"] / 2 * np.cos(t), c[1] + PAD["d"] / 2 * np.sin(t), color="white", zorder=2)
                ax.plot(c[0] + PAD["d"] / 2 * np.cos(t), c[1] + PAD["d"] / 2 * np.sin(t), color=INK, lw=0.6, zorder=3)
        if towers:
            for sx in (1, -1):
                xa, xb = sorted((sx * TOWER_X[0], sx * TOWER_X[1]))
                tw = tr([(xa, -9.0), (xb, -9.0), (xb, 35.0), (xa, 35.0), (xa, -9.0)])
                ax.fill(tw[:, 0], tw[:, 1], color=TOWER_C, alpha=0.85, zorder=4)
                ax.plot(tw[:, 0], tw[:, 1], color=INK, lw=0.6, zorder=5)
        if centre_lines:
            h = tr([(-62.0, 0.0), (62.0, 0.0)])
            ax.plot(h[:, 0], h[:, 1], color="#3060c0", lw=0.7, ls=(0, (8, 3, 2, 3)), zorder=6)
            cl = tr([(0.0, -SP), (0.0, LOBE["y_end"] + 12.0)])
            ax.plot(cl[:, 0], cl[:, 1], color=GREY, lw=0.5, ls=(0, (8, 3, 2, 3)), zorder=6)


def drawing(res):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Arc
    fig = plt.figure(figsize=(22, 15.5), dpi=110)
    fig.patch.set_facecolor("white")
    # ---- 1: the whole base, plan ------------------------------------------------
    ax = fig.add_axes([0.01, 0.30, 0.47, 0.64])
    ax.set_aspect("equal"); ax.axis("off")
    _plan_geometry(ax)
    bb = res["export"]
    x0, x1, y0, y1 = bb["x"][0], bb["x"][1], bb["y"][0], bb["y"][1]
    face = shelf_outline_sketch()._faces.Faces()[0]
    ol = _wire_xy(face.outerWire())
    px0, px1 = ol[np.argmin(ol[:, 0])], ol[np.argmax(ol[:, 0])]
    py0, py1 = ol[np.argmin(ol[:, 1])], ol[np.argmax(ol[:, 1])]
    yb = y0 - 16
    for p_ in (px0, px1):
        ax.plot([p_[0], p_[0]], [p_[1] - 2, yb - 3], lw=0.45, color=INK)
    _dim(ax, (x0, yb), (x1, yb), 0, f"{x1 - x0:.1f}", fs=10, ext=False)
    xr = x1 + 16
    for p_ in (py0, py1):
        ax.plot([p_[0] + 2, xr + 3], [p_[1], p_[1]], lw=0.45, color=INK)
    _dim(ax, (xr, y0), (xr, y1), 0, f"{y1 - y0:.1f}", fs=10, ext=False)
    _note(ax, (WIN_D / 2 * math.cos(math.radians(265)), WIN_D / 2 * math.sin(math.radians(265))),
          f"window Ø{WIN_D:.0f}, centred on the beaker axis", (0, y0 - 34), fs=9.5, ha="center")
    _dim(ax, (0, 0), (0, SP), 9, f"{SP:.0f}", fs=9.5)
    _note(ax, (-40, SP), "hinge axis (blue)", (-120, 95), fs=9, ha="center", col="#3060c0")
    ax.add_patch(Arc((0, 0), 300, 300, theta1=90, theta2=210, lw=0.7, color=INK))
    ax.text(150 * math.cos(math.radians(150)) - 6, 150 * math.sin(math.radians(150)) + 6, "120°", fontsize=10,
            ha="right", va="bottom", bbox=dict(boxstyle="square,pad=0.1", fc="white", ec="none"))
    _note(ax, (69.28 * math.cos(math.radians(30)) - 10 * math.cos(math.radians(30)),
               69.28 * math.sin(math.radians(30)) - 10 * math.sin(math.radians(30))), "R10, all 15 outline corners",
          (110, 30), fs=9)
    _note(ax, (36, 26), "neighbouring towers\nmeet here: one block", (95, 75), fs=9)
    ax.set_xlim(x0 - 25, x1 + 34); ax.set_ylim(y0 - 42, y1 + 14)
    ax.set_title("Plan, the whole base (one part).  Hinge axes blue, module centre lines grey, towers brown",
                 fontsize=12, loc="left", fontweight="bold")
    # ---- 2: one lobe, every dimension ----------------------------------------------
    ax = fig.add_axes([0.50, 0.30, 0.49, 0.64])
    ax.set_aspect("equal"); ax.axis("off")
    _plan_geometry(ax, R2=np.eye(2))
    yc = SP                                       # hinge axis, from the beaker axis
    w, yw, we, ye = LOBE["half_w"], LOBE["y_wide"], LOBE["half_w_end"], LOBE["y_end"]
    # lobe outline
    _dim(ax, (-w, yc + yw), (w, yc + yw), 7, f"{2 * w:.0f}", fs=9.5, tshift=-30)
    _dim(ax, (-we, yc + ye), (we, yc + ye), 12, f"{2 * we:.0f}", fs=9.5)
    _dim(ax, (-we - 40, 0), (-we - 40, yc + ye), 0, f"{SP + ye:.0f}", fs=9.5, ext=False)
    ax.plot([-we - 46, -we + 2], [yc + ye, yc + ye], lw=0.45, color=INK)
    ax.plot([-we - 46, -2], [0, 0], lw=0.45, color=INK)
    _dim(ax, (-w - 18, 0), (-w - 18, yc + yw), 0, f"{SP + yw:.0f}", fs=9.5, ext=False)
    ax.plot([-w - 24, -w + 2], [yc + yw, yc + yw], lw=0.45, color=INK)
    # towers
    _dim(ax, (-TOWER_X[0], yc - 9), (TOWER_X[0], yc - 9), -9, f"{2 * TOWER_X[0]:.1f}", fs=9)
    _dim(ax, (-TOWER_X[1], yc - 9), (TOWER_X[1], yc - 9), -19, f"{2 * TOWER_X[1]:.1f}", fs=9)
    _dim(ax, (TOWER_X[1], yc - 9), (TOWER_X[1], yc), -6, "9", fs=8.5)
    _dim(ax, (TOWER_X[1], yc + 10), (TOWER_X[1], yc + 35), -6, "25", fs=8.5)
    _dim(ax, (TOWER_X[1], yc), (TOWER_X[1], yc + 10), -6, "10", fs=8.5)
    _dim(ax, (TOWER_X[0], yc + 36), (TOWER_X[1], yc + 36), -4, "12.3", fs=8.5)
    _note(ax, (TOWER_X[1] - 3, yc + 4), "tower foot: 10 to 35\nbehind the hinge axis;\nnose 9 in front (R9)",
          (62, yc + 6), fs=8.5)
    # slot
    _dim(ax, (-SLOT["x"], yc + SLOT["y0"] + 12), (SLOT["x"], yc + SLOT["y0"] + 12), 0, f"{2 * SLOT['x']:.0f}", fs=9, ext=False)
    _dim(ax, (SLOT["x"], yc + SLOT["y0"]), (SLOT["x"], yc + SLOT["y1"]), -8, f"{SLOT['y1'] - SLOT['y0']:.0f}", fs=9)
    _dim(ax, (60, 0), (60, yc + SLOT["y0"]), 0, f"{SP + SLOT['y0']:.0f}", fs=9, ext=False)
    ax.plot([2, 63], [0, 0], lw=0.45, color=INK)
    ax.plot([SLOT["x"] + 2, 63], [yc + SLOT["y0"], yc + SLOT["y0"]], lw=0.45, color=INK)
    # hanger holes
    hx, (hy0, hy1) = PAD["x"], PAD["y"]
    _dim(ax, (-hx, yc + hy1), (hx, yc + hy1), 8, f"{2 * hx:.0f}", fs=9)
    _dim(ax, (hx, yc + hy0), (hx, yc + hy1), -14, f"{hy1 - hy0:.0f}", fs=9)
    _dim(ax, (75, 0), (75, yc + hy0), 0, f"{SP + hy0:.0f}", fs=9, ext=False)
    ax.plot([hx + 3, 78], [yc + hy0, yc + hy0], lw=0.45, color=INK)
    ax.plot([63, 78], [0, 0], lw=0.45, color=INK)
    _note(ax, (hx + 1.6, yc + hy1 + 1.6), f"4 × Ø{PAD['d']} through (M4):\nthe actuator hanger", (52, yc + hy1 + 22), fs=9)
    _note(ax, (w - 1, yc + yw + 6), "R10 (all corners)", (70, yc + yw + 40), fs=9)
    _note(ax, (-SLOT["x"] + 2, yc + SLOT["y0"] + 60), "slot, through:\nclevis block and\nactuator rod", (-88, yc + SLOT["y0"] + 95), fs=9, ha="center")
    ax.set_xlim(-130, 118); ax.set_ylim(-44, yc + ye + 30)
    ax.set_title("One lobe (the other two are the same at ±120°).  mm from the beaker axis (0) along the centre line",
                 fontsize=12, loc="left", fontweight="bold")
    # ---- 3: tower profile -----------------------------------------------------------
    ax = fig.add_axes([0.02, 0.02, 0.36, 0.27])
    ax.set_aspect("equal"); ax.axis("off")
    prof = res["tower_profile"]
    for e in prof:
        if e["kind"] == "line":
            ax.plot([e["start"][0], e["end"][0]], [e["start"][1], e["end"][1]], color=INK, lw=1.1)
        elif e["kind"] == "circle":
            c, r = e["centre"], e["radius"]
            if r < 3:
                ax.add_patch(plt.Circle(c, r, fill=False, color=INK, lw=1.0))
                continue
            a0 = math.degrees(math.atan2(e["start"][1] - c[1], e["start"][0] - c[0]))
            a1 = math.degrees(math.atan2(e["end"][1] - c[1], e["end"][0] - c[0]))
            lo, hi = sorted((a0, a1))
            if r > 8.5 and abs(c[0]) < 0.1:            # the nose: the front half circle
                lo, hi = 90.0, 270.0
            ax.add_patch(Arc(c, 2 * r, 2 * r, theta1=lo, theta2=hi, color=INK, lw=1.1))
    ax.fill_between([-20, 60], TOP - T, TOP, color="#fbe3c8")
    ax.plot([-20, 60, 60, -20, -20], [TOP, TOP, TOP - T, TOP - T, TOP], color=INK, lw=0.9)
    ax.plot([-14, 40], [0, 0], color="#3060c0", lw=0.7, ls=(0, (8, 3, 2, 3)))
    ax.plot([0, 0], [-14, 14], color="#3060c0", lw=0.7, ls=(0, (8, 3, 2, 3)))
    _dim(ax, (-14, TOP), (-14, 0), 0, "37.25", fs=8.5, ext=False)
    _dim(ax, (-24, TOP - T), (-24, 9), 0, "52.25", fs=8.5, ext=False)
    _dim(ax, (63, TOP - T), (63, TOP), 0, "6", fs=8.5, ext=False)
    for yy in (TOP - T, TOP, 0.0, 9.0):
        ax.plot([-27, 0 if yy == 0 else (12 if yy == 9 else -20)], [yy, yy], lw=0.4, color=INK)
    _dim(ax, (10, TOP), (35, TOP), -9, "25", fs=8.5)
    _dim(ax, (0, TOP), (10, TOP), -9, "10", fs=8.5)
    _dim(ax, (0, 9), (12.93, 9), 4, "12.93", fs=8)
    _note(ax, (-6.36, 6.36), "R9 about the hinge axis", (-48, 20), fs=8.5)
    _note(ax, (19.0, 6.6), "R10", (34, 18), fs=8.5)
    _note(ax, (1.8, -1.8), "Ø5.3 hinge bore (M5)", (40, 2), fs=8.5)
    _note(ax, (28.7, -15.5), "rear face: (22.36, 2.34)\nto (35, -33.38), then\nstraight down to the shelf", (44, -16), fs=8)
    _note(ax, (5.0, -23.1), "front face: (10, -37.25)\nto (0, -9), the nose's bottom", (-44, -28), fs=8, ha="center")
    ax.set_xlim(-58, 92); ax.set_ylim(TOP - T - 8, 28)
    ax.set_title("Tower side profile (today's baseplate tower), y behind the hinge axis",
                 fontsize=11, loc="left", fontweight="bold")
    # ---- 4: tower pair from the front -----------------------------------------------
    ax = fig.add_axes([0.40, 0.02, 0.30, 0.27])
    ax.set_aspect("equal"); ax.axis("off")
    ax.fill_between([-58, 58], TOP - T, TOP, color="#fbe3c8")
    ax.plot([-58, 58, 58, -58, -58], [TOP, TOP, TOP - T, TOP - T, TOP], color=INK, lw=0.9)
    for sx in (1, -1):
        xa, xb = sorted((sx * TOWER_X[0], sx * TOWER_X[1]))
        ax.fill([xa, xb, xb, xa], [TOP, TOP, 9, 9], color=TOWER_C, alpha=0.85)
        ax.plot([xa, xb, xb, xa, xa], [TOP, TOP, 9, 9, TOP], color=INK, lw=0.9)
        ka, kb = sorted((sx * 16.08, sx * 28.6))
        ax.plot([ka, kb, kb, ka, ka], [-7.5, -7.5, 7.5, 7.5, -7.5], color=GREY, lw=0.9, ls="--")
        ax.add_patch(plt.Circle((sx * (TOWER_X[0] + TOWER_X[1]) / 2, 0), 2.65, fill=False, color=INK, lw=0.6))
    ax.plot([-62, 62], [0, 0], color="#3060c0", lw=0.7, ls=(0, (8, 3, 2, 3)))
    _dim(ax, (-TOWER_X[0], 9), (TOWER_X[0], 9), 6, f"{2 * TOWER_X[0]:.1f}", fs=8.5)
    _dim(ax, (-TOWER_X[1], 9), (TOWER_X[1], 9), 14, f"{2 * TOWER_X[1]:.1f}", fs=8.5)
    _dim(ax, (TOWER_X[0], TOP), (TOWER_X[1], TOP), -5, "12.3", fs=8.5)
    _note(ax, (-22, 7.5), "plate knuckles (dashed), 0.3 mm\ninside the towers, as today", (-40, 30), fs=8, ha="center")
    ax.set_xlim(-70, 70); ax.set_ylim(TOP - T - 14, 40)
    ax.set_title("Tower pair, looking along the module's centre line", fontsize=11, loc="left", fontweight="bold")
    # ---- notes --------------------------------------------------------------------
    ax = fig.add_axes([0.72, 0.02, 0.27, 0.27]); ax.axis("off")
    ck = res.get("checks", {})
    fp = res["export"]
    lines = [
        ("One printed part: a 6 mm shelf and six hinge towers.", True),
        (f"Overall {fp['x'][1] - fp['x'][0]:.1f} × {fp['y'][1] - fp['y'][0]:.1f} × {fp['z'][1]:.2f} mm,"
         f" {fp['volume_cm3']:.0f} cm³ solid.", False),
        ("Towers: today's baseplate towers, unchanged (copied from", False),
        ("PR #170's baseplate.step). Hinge axes 37.25 above the shelf.", False),
        ("Neighbouring towers meet near their noses, so they", False),
        ("print as one block between modules. The M5 hinge screw", False),
        ("still goes in from outside (2.9 mm past the next tower).", False),
        ("Plate modelled as Ethan's: no gears, arms or front", False),
        (f"wings, {res['plate_trimmed']['width']:.1f} mm wide at the stepper mount.", False),
    ]
    if ck:
        lines += [
            (f"Closest approaches, 0-90°:", True),
            (f"modules to each other {min(v['modules_only_mm'] for v in ck['station_cases'].values()):.1f} mm (tap brackets at 90/90);", False),
            (f"plate floor to its tower's foot {ck['one_module_to_base']['mm']:.2f} mm at 0°, as today;", False),
            (f"4+ mm from 5°. Knuckle to tower {ck['knuckle_to_tower_gap']:.1f} mm (the hinge).", False),
        ]
    y = 0.98
    for t_, b_ in lines:
        ax.text(0.0, y, t_, fontsize=10, fontweight="bold" if b_ else "normal", va="top", transform=ax.transAxes)
        y -= 0.075
    fig.text(0.01, 0.985, "Tri-star base with the hinge towers merged in (issue #204): dimensions in mm",
             fontsize=17, fontweight="bold", va="top")
    OUT.mkdir(exist_ok=True)
    fig.savefig(OUT / "base_drawing.png", dpi=110)
    plt.close(fig)
    print("  -> base_drawing.png", flush=True)


def iso(res):
    """The base alone, and with the three modules at 30 / 60 / 0 deg (status colours as before)."""
    from PIL import Image, ImageDraw
    col = (0.95, 0.55, 0.25)
    b = D.Part("base", base_station(), np.eye(4), col, "fixed")
    a = OUT / "_base_a.png"
    D.render([b], a, az=-62, el=32, size=(1100, 850), dist=1.25)
    ps = station_parts((30, 60, 0))
    ps = [p for p in ps if p.name != "shelf"]
    for p in ps:
        if p.name.endswith("(inboard)") or p.name.endswith("Mounting plate"):
            p.colour = K.STATUS["modify"][2]
        elif p.name != "base":
            p.colour = K.STATUS[getattr(p, "status", "reuse")][2]
    c = OUT / "_base_b.png"
    D.render(ps, c, az=-62, el=24, size=(1100, 850), dist=1.45, focal=(0, 0, -20))
    ims = [Image.open(a), Image.open(c)]
    W = sum(i.width for i in ims)
    out = Image.new("RGB", (W, ims[0].height + 90), "white")
    x = 0
    for i in ims:
        out.paste(i, (x, 0)); x += i.width
    d = ImageDraw.Draw(out)
    from components import font
    d.text((20, ims[0].height + 10), "Left: the base, one part (shelf + six towers).  Right: with the three modules at 30, 60 and 0°;"
           " the plates (yellow) without gears or front wings. Hangers not shown.", font=font(22), fill=(30, 30, 30))
    d.text((20, ims[0].height + 45), "Towers are today's baseplate towers; neighbouring ones meet near their noses and print as one block.",
           font=font(22), fill=(30, 30, 30))
    out.save(OUT / "base_iso.png")
    a.unlink(); c.unlink()
    print("  -> base_iso.png", flush=True)


if __name__ == "__main__":
    import sys
    res = dict(spacing_hinge_to_beaker_axis=SP, shelf_thickness=T, lobe=LOBE, window_dia=WIN_D, slot=SLOT, pad=PAD,
               tower_x=TOWER_X, wing_cut=dict(x=WING_CUT_X, y_up_to=WING_CUT_Y))
    res["plate_trimmed"] = plate_extent()
    print("plate", res["plate_trimmed"], flush=True)
    res["tower_profile"] = tower_profile()
    res["export"] = export()
    ex = res["export"]
    w_, h_ = ex["x"][1] - ex["x"][0], ex["y"][1] - ex["y"][0]
    res["fits_h2d_one_nozzle"] = dict(bed=BED, size=[round(w_, 1), round(h_, 1)], fits=bool(w_ <= BED[0] and h_ <= BED[1]))
    print("export", res["export"], res["fits_h2d_one_nozzle"], flush=True)
    if "--no-checks" not in sys.argv:
        res["checks"] = checks()
        print(json.dumps(res["checks"], indent=1), flush=True)
    elif (HERE / "base.json").exists():
        res["checks"] = json.loads((HERE / "base.json").read_text()).get("checks", {})
    (HERE / "base.json").write_text(json.dumps(res, indent=1, default=float) + "\n")
    drawing(res)
    iso(res)
