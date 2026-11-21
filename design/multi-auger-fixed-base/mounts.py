"""Ways to mount the tri-star's three linear actuators (issue #204, 20 Nov).

Ethan asked for more options for mounting the actuators, for example a second deck
that all three mount to.  Today's placeholder (components.py, 12 Nov) hangs each
Actuonix P16 from the shelf on its own strap.  This script compares:

  M0  today's placeholder: one hanger strap per actuator, from the shelf.
  M1  a lower deck: one printed ring under the shelf that carries all three P16
      U-brackets, held by three posts at the lobe ends (where the hangers hang now).
      It can stand on the bench or on legs.
  M2  M1 with a shorter actuator on a shorter lever: a P16-100 and the clevis block
      48 mm behind the hinge instead of 95.  The deck moves 50 mm up.
  M3  the P16-150 leaning 40 deg outward, each on its own foot.  Kinematics and the
      side-view panel only.

For each it works out the stroke, the effective lever and force, the height under
the shelf and the footprint.  For M1 and M2 it builds the deck and posts, checks
every moving part against them over 0..90 deg, checks a stir plate between the
actuators, and renders the station.  It writes mounts.json, mount-deck/deck_M1.step
(the deck with its posts) and renders/mount_*.png.

    pip install cadquery trimesh python-fcl rtree vtk pillow numpy matplotlib
    xvfb-run -a python mounts.py       # about 3 min

Frames as in doserlib: the unit frame has the hinge axis on x, +y behind the hinge
(away from the beaker), z up, hinge at z = 0; the station frame has the beaker
axis on z.  All new parts are placeholders.
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
import base as B
import clevis as CL

HERE = Path(__file__).resolve().parent
OUT = HERE / "renders"
CAD = HERE / "mount-deck"
SP = K.SP                                   # 32 mm, hinge to beaker axis
CC = K.CC                                   # 45: clevis pin below the hinge (9.75 under the floor)
FLOOR_U = K.FLOOR_U                         # -35.25
SHELF_BOT = D.BASE_BOT_U                    # -43.25
TORQUE = 650.0                              # N mm, the README's upper estimate (module + powder)
PRELOAD = 5.0                               # rod out at 0 deg
UB = K.UB                                   # the P16's U-bracket: pin 9.1 above its base
BED = B.BED                                 # one H2D nozzle, 325 x 320
P16 = {"P16-150": dict(closed=197.0, stroke=150.0), "P16-100": dict(closed=147.0, stroke=100.0)}

OPTIONS = {
    "M0": dict(title="Today: a hanger per actuator", a=95.0, act="P16-150", lean=0.0),
    "M1": dict(title="Lower deck on three posts", a=95.0, act="P16-150", lean=0.0, post_gap=5.5),
    "M2": dict(title="Shorter actuator, shorter lever", a=48.0, act="P16-100", lean=0.0, post_gap=10.0, slot_end=70.0),
    "M3": dict(title="Actuators leaning outward", a=95.0, act="P16-150", lean=40.0),
}

DECK_T = 6.0
POST = dict(w=20.0, d=16.0)                 # post 20 (across) x 16 (radial), o["post_gap"] behind the P16's housing
LOBE_HALF, FILLET = 24.0, 10.0              # lobe ends 48 wide, R10 corners (as the shelf's)
STIR = dict(w=150.0, h=100.0)               # placeholder stir plate (clearance.py)
BEAKER = dict(d=70.0, h=95.0, rim=-11.6 - 15.0)   # 250 mL, rim 15 mm under the 90 deg outlets


# --------------------------------------------------------------------------- #
# kinematics (module plane: y behind the hinge, z up)
# --------------------------------------------------------------------------- #
def rod_pin(tilt, a):
    t = math.radians(tilt)
    return np.array([a * math.cos(t) + CC * math.sin(t), a * math.sin(t) - CC * math.cos(t)])


def base_pin(o):
    """(y, z) of the P16's rear pin: (closed + 5 mm) from the rod pin at 0 deg, leaning o['lean'] deg outward."""
    L0 = P16[o["act"]]["closed"] + PRELOAD
    b = math.radians(o["lean"])
    return rod_pin(0.0, o["a"]) + L0 * np.array([math.sin(b), -math.cos(b)])


def kinematics(o, tilts=np.arange(0.0, 90.001, 0.5)):
    a, Bp, act = o["a"], base_pin(o), P16[o["act"]]
    L = np.array([np.linalg.norm(rod_pin(t, a) - Bp) for t in tilts])
    lever = np.gradient(L, np.radians(tilts))                    # mm of stroke per radian of tilt
    lean = [math.degrees(math.atan2(*(rod_pin(t, a) - Bp))) for t in tilts]   # + = top leaning outward
    i = int(np.argmin(lever))
    return dict(
        rod_pin_mm=[a, -CC], base_pin_mm=[round(float(Bp[0]), 1), round(float(Bp[1]), 1)],
        actuator=o["act"], closed=act["closed"], stroke=act["stroke"],
        rod_out={f"{t:g}": round(float(L[int(t * 2)] - act["closed"]), 1) for t in (0, 30, 45, 60, 90)},
        spare_at_90=round(float(act["closed"] + act["stroke"] - L[-1]), 1),
        monotonic=bool(np.all(np.diff(L) > 0)),
        lever_mm_per_rad=[round(float(lever.min()), 1), round(float(lever.max()), 1)],
        mm_per_deg=[round(float(lever.min()) * math.pi / 180, 2), round(float(lever.max()) * math.pi / 180, 2)],
        max_force_N=round(TORQUE / float(lever.min()), 1), max_force_at_tilt=float(tilts[i]),
        actuator_lean_deg=[round(min(lean), 1), round(max(lean), 1)],
        base_pin_from_beaker_axis=round(SP + float(Bp[0]), 1),
        below_shelf_underside=round(SHELF_BOT - (float(Bp[1]) - UB["h"] - (DECK_T if "post_gap" in o else 4.0)), 1),
    )


# --------------------------------------------------------------------------- #
# geometry
# --------------------------------------------------------------------------- #
_S: dict = {}


def p16(L_, closed):
    """K.p16_shapes for any closed length (the P16-100's housing is the same, its tube 50 mm shorter)."""
    w, h, ln = K.P16R["housing"]
    e, z0 = K.P16R["axis_from_edge"], K.P16R["housing_from_hole"]
    key = ("body", closed)
    if key not in _S:
        lug = D.cyl(4.75, K.P16R["lug_t"], -K.P16R["lug_t"] / 2, 0, 0, d=(1, 0, 0)).fuse(
            D.box(-K.P16R["lug_t"] / 2, K.P16R["lug_t"] / 2, -4.75, 4.75, 0, z0 + 1))
        lug = lug.cut(D.cyl(K.HOLE / 2, 20, -10, 0, 0, d=(1, 0, 0)))
        housing = D.box(-w / 2, w / 2, -e, h - e, z0, z0 + ln)
        tube = D.box(-6.0, 6.0, -6.0, 6.0, z0 + ln - 1, closed - 15.5)
        _S[key] = housing.fuse(lug).fuse(tube)
    tube_end = closed - 15.5
    rk = ("rod", closed, round(L_, 2))
    if rk not in _S:
        shaft = D.cyl(K.P16R["shaft"] / 2, L_ - 14.5 - (tube_end - 2), 0, 0, tube_end - 2)
        hub = D.cyl(K.P16R["boss"] / 2, 6.0, 0, 0, L_ - 14.5)
        tab = D.box(-3.0, 3.0, -4.5, 4.5, L_ - 8.5, L_).fuse(D.cyl(4.5, 6.0, -3.0, 0, L_, d=(1, 0, 0)))
        _S[rk] = shaft.fuse(hub).fuse(tab.cut(D.cyl(K.HOLE / 2, 20, -10, 0, L_, d=(1, 0, 0))))
    return _S[key], _S[rk]


def act_frame(Mst, tilt, o):
    a, Bp = o["a"], base_pin(o)
    Pp = (Mst @ D.Rx(tilt) @ np.array([0.0, a, -CC, 1.0]))[:3]
    Bw = (Mst @ np.array([0.0, Bp[0], Bp[1], 1.0]))[:3]
    L_ = float(np.linalg.norm(Pp - Bw))
    wv = (Pp - Bw) / L_
    ax = Mst[:3, 0] - wv * (Mst[:3, 0] @ wv)
    ax /= np.linalg.norm(ax)
    M = np.eye(4)
    M[:3, 0], M[:3, 1], M[:3, 2], M[:3, 3] = ax, np.cross(wv, ax), wv, Bw
    return M, L_


def module(tilt, Mst, tag, o):
    """One module at ``tilt`` with the option's clevis position and actuator (no hanger)."""
    parts = [p for p in D.unit_parts(K.SPEC, tilt, Mst, tag)]
    for p in parts:
        if p.name.endswith("Mounting plate"):
            if "plate" not in _S:
                _S["plate"] = B.plate_trimmed()
            p.shape = _S["plate"]
            p.colour = K.STATUS["modify"][2]
        elif "Tap bracket" in p.name:
            p.colour = K.STATUS["t203"][2]
        else:
            p.colour = K.STATUS["reuse"][2]
    Mb = Mst @ D.Rx(tilt) @ D.Tt(0.0, o["a"], FLOOR_U)
    if "block" not in _S:
        _S["block"], _S["pin"] = CL.block(), CL.m4_pin(20.0)
    parts.append(D.Part(f"{tag}:clevis block", _S["block"], Mb, K.STATUS["new"][2], tag, True))
    parts.append(D.Part(f"{tag}:M4 pin", _S["pin"], Mb, K.STATUS["hw"][2], tag, True))
    Ma, L_ = act_frame(Mst, tilt, o)
    body, rod = p16(L_, P16[o["act"]]["closed"])
    parts.append(D.Part(f"{tag}:P16 body", body, Ma, K.STATUS["buy"][2], tag, False))
    parts.append(D.Part(f"{tag}:P16 rod", rod, Ma, (0.80, 0.81, 0.84), tag, True))
    Bp = base_pin(o)
    Mu = Mst @ D.Tt(0.0, Bp[0], Bp[1]) @ D.Rx(-o["lean"])
    if "ub" not in _S:
        _S["ub"] = K.u_bracket()
    parts.append(D.Part(f"{tag}:P16 bracket", _S["ub"], Mu, K.STATUS["buy"][2], tag, False))
    return parts


def deck_geometry(o):
    """Where the deck and posts go for option o (unit frame of each module)."""
    Bp = base_pin(o)
    top = float(Bp[1]) - UB["h"]                         # the U-bracket's base sits on the deck
    rb = SP + o["a"]                                     # U-bracket from the beaker axis
    housing_back = o["a"] + K.P16R["housing"][1] - K.P16R["axis_from_edge"]   # P16 housing's outer face (y)
    y0 = housing_back + o["post_gap"]
    y1 = y0 + POST["d"]
    return dict(top=round(top, 2), bottom=round(top - DECK_T, 2), ring=(rb - 15.0, rb + 13.0),
                post_y=(round(y0, 2), round(y1, 2)), post_x=POST["w"] / 2, post_len=round(SHELF_BOT - top, 2),
                lobe_end=round(y1, 2), lobe_from_axis=round(SP + y1, 2), bracket_from_axis=rb,
                bracket_hole=(0.0, o["a"]), post_screw=(0.0, round((y0 + y1) / 2, 2)))


def deck_outline_sketch(g):
    sk = cq.Sketch().circle(g["ring"][1])
    for th in B.BEARINGS:
        M = D.place(th, SP, 0.0)
        y_in = g["ring"][0] - SP
        pts = B.station_xy(M, [(-LOBE_HALF, y_in), (LOBE_HALF, y_in), (LOBE_HALF, g["lobe_end"]), (-LOBE_HALF, g["lobe_end"])])
        sk = sk.polygon(pts + [pts[0]], mode="a")
    return sk.clean().reset().vertices().fillet(FILLET).reset()


def deck(o, posts=True):
    """The lower deck (station frame): ring + three lobes, 6 thick, its top under the U-brackets, an
    M4 hole for each U-bracket and an M5 hole for each post; with ``posts``, the three posts printed on it."""
    key = ("deck", o["a"], o["act"], posts)
    if key in _S:
        return _S[key]
    g = deck_geometry(o)
    d = cq.Workplane("XY", origin=(0, 0, g["bottom"])).placeSketch(deck_outline_sketch(g)).extrude(DECK_T).val()
    d = d.cut(D.cyl(g["ring"][0], DECK_T + 2, 0, 0, g["bottom"] - 1))
    for th in B.BEARINGS:
        loc = C._loc(D.place(th, SP, 0.0))
        h = D.cyl(2.25, DECK_T + 2, *g["bracket_hole"], g["bottom"] - 1).fuse(
            D.box(-UB["gap"] / 2 - UB["t"] - 0.2, UB["gap"] / 2 + UB["t"] + 0.2, o["a"] - UB["w"] / 2 - 0.2,
                  o["a"] + UB["w"] / 2 + 0.2, g["top"] - 1.0, g["top"] + 1))        # 1 mm pocket keys the bracket square
        h = h.fuse(D.cyl(2.75, DECK_T + 2, *g["post_screw"], g["bottom"] - 1))
        d = d.cut(h.moved(loc))
        if posts:
            p = D.box(-g["post_x"], g["post_x"], g["post_y"][0], g["post_y"][1], g["top"] - 0.5, SHELF_BOT)
            d = d.fuse(p.moved(loc))
    _S[key] = d.clean()
    return _S[key]


def shelf_for(o):
    """The one-piece base (base.py); for M2 its slots end 66 mm behind the hinge so the posts land on it."""
    if o["a"] == 95.0:
        return B.base_station()
    key = ("shelf", o["a"])
    if key not in _S:
        g = deck_geometry(o)
        sk = B.shelf_outline_sketch()
        sh = cq.Workplane("XY", origin=(0, 0, B.BOT)).placeSketch(sk).extrude(B.T).val()
        sh = sh.cut(D.cyl(B.WIN_D / 2, B.T + 2, 0, 0, B.BOT - 1))
        for th in B.BEARINGS:
            loc = C._loc(D.place(th, SP, 0.0))
            sh = sh.cut(D.box(-B.SLOT["x"], B.SLOT["x"], B.SLOT["y0"], o["slot_end"], B.BOT - 1, B.TOP + 1).moved(loc))
            sh = sh.cut(D.cyl(2.75, B.T + 2, *g["post_screw"], B.BOT - 1).moved(loc))
        tw = B.tower_today()
        tw_neg = tw.mirror("YZ", (0, 0, 0))
        for th in B.BEARINGS:
            loc = C._loc(D.place(th, SP, 0.0))
            sh = sh.fuse(tw.moved(loc)).fuse(tw_neg.moved(loc))
        _S[key] = sh.clean()
    return _S[key]


def stir_plate(z_bench, rot):
    s = D.box(-STIR["w"] / 2, STIR["w"] / 2, -STIR["w"] / 2, STIR["w"] / 2, z_bench, z_bench + STIR["h"])
    return s.rotate(cq.Vector(0, 0, 0), cq.Vector(0, 0, 1), rot)


# --------------------------------------------------------------------------- #
# checks
# --------------------------------------------------------------------------- #
def fixed_parts(o):
    col = (0.95, 0.47, 0.18)
    return [D.Part("deck + posts", deck(o), np.eye(4), col, "fixed", False),
            D.Part("shelf", shelf_for(o), np.eye(4), (0.62, 0.66, 0.72), "fixed", False)]


def checks(o, tilts=range(0, 91, 5)):
    """One module swept 0..90 deg against the deck + posts; the P16 against its post; the block and rod
    against the shelf; the P16s' closest approach to the beaker axis under the shelf."""
    g = deck_geometry(o)
    dk = D.Part("deck + posts", deck(o), np.eye(4), (0, 0, 0), "fixed")
    sh = D.Part("shelf", shelf_for(o), np.eye(4), (0, 0, 0), "fixed")
    M = D.place(90.0, SP, 0.0)
    worst = dict(deck=(1e9, None, None, None), shelf=(1e9, None, None, None))
    rmin, zlow = 1e9, 1e9
    for t in tilts:
        ps = [p for p in module(float(t), M, "A", o) if not p.name.endswith("P16 bracket")]
        d = D.clearance(ps + [dk])
        if d[0] < worst["deck"][0]:
            worst["deck"] = (d[0], d[1], d[2], t)
        mv = [p for p in ps if p.name.endswith(("clevis block", "M4 pin", "P16 rod", "P16 body"))]
        d = D.clearance(mv + [sh])
        if d[0] < worst["shelf"][0]:
            worst["shelf"] = (d[0], d[1], d[2], t)
        body = next(p for p in ps if p.name.endswith("P16 body"))
        m = D.mesh_of(body.shape)
        v = (body.M[:3, :3] @ np.asarray(m.vertices).T).T + body.M[:3, 3]
        sel = v[:, 2] < SHELF_BOT
        rmin = min(rmin, float(np.hypot(v[sel, 0], v[sel, 1]).min()))
        zlow = min(zlow, float(v[:, 2].min()))
    out = dict(
        module_to_deck_and_posts=dict(mm=round(worst["deck"][0], 2), between=f"{worst['deck'][1]} / {worst['deck'][2]}",
                                      at_tilt=worst["deck"][3]),
        moving_parts_to_shelf=dict(mm=round(worst["shelf"][0], 2), between=f"{worst['shelf'][1]} / {worst['shelf'][2]}",
                                   at_tilt=worst["shelf"][3]),
        p16_closest_to_beaker_axis_under_shelf=round(rmin, 1),
        column_dia_under_shelf=round(2 * rmin, 1),
        p16_lowest_point=round(zlow, 2),
    )
    # a stir plate standing on the bench inside the deck (deck on the bench), best of a few rotations
    z_bench = g["bottom"]
    best = (-1e9, None)
    for rot in range(0, 90, 5):
        sp_ = D.Part("stir plate", stir_plate(z_bench, rot), np.eye(4), (0, 0, 0), "stir")
        dm = 1e9
        for t in (0, 30, 60, 75, 90):
            ps = []
            for i, th in enumerate(B.BEARINGS):
                ps += [p for p in module(float(t), D.place(th, SP, 0.0), "ABC"[i], o) if "P16" in p.name]
            dm = min(dm, D.clearance(ps + [sp_])[0], D.clearance([dk, sp_])[0])
        if dm > best[0]:
            best = (dm, rot)
    out["stir_plate_150_on_bench_inside_deck"] = dict(mm=round(best[0], 2), rotation_deg=best[1],
                                                      fits=bool(best[0] >= 2.0))
    return out


def own_parts_check(o):
    """The clevis block and its M3 screw heads against the module's own parts at 0 deg (matters for M2,
    where the block sits under #203's tap bracket)."""
    M = np.eye(4)
    ps = module(0.0, M, "A", o)
    blk = next(p for p in ps if p.name.endswith("clevis block"))
    heads = None
    for sx in (1, -1):
        h = D.cyl(2.75, 3.0, sx * K.BLOCK["screw_x"], o["a"], K.FLOOR_TOP)
        heads = h if heads is None else heads.fuse(h)
    hd = D.Part("M3 heads", heads, np.eye(4), (0, 0, 0), "h")
    out = {}
    for p in ps:
        k = p.name.split(":", 1)[1]
        if k in ("clevis block", "M4 pin", "P16 body", "P16 rod", "P16 bracket", "Mounting plate"):
            continue
        q = D.Part(k, p.shape, p.M, (0, 0, 0), "o")
        out[k] = dict(block=round(D.clearance([D.Part("b", blk.shape, blk.M, (0, 0, 0), "b"), q])[0], 2),
                      screw_heads=round(D.clearance([hd, q])[0], 2))
    worst = min(out.items(), key=lambda kv: min(kv[1].values()))
    return dict(closest=worst[0], **worst[1])


# --------------------------------------------------------------------------- #
# figures
# --------------------------------------------------------------------------- #
def options_panel(res):
    """Side views in one module's plane, to scale: each option at 0 and 90 deg."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Polygon, Rectangle, Circle

    INK, GREY, OR, DK = "#1f1f1f", "#8a8a8a", "#f2a65a", "#4a4d55"
    fig, axs = plt.subplots(1, 4, figsize=(19, 7.4), sharey=True)
    for ax, (key, o) in zip(axs, OPTIONS.items()):
        kin = res["kinematics"][key]
        Bp = base_pin(o)
        bench = Bp[1] - UB["h"] - (DECK_T if key in ("M1", "M2") else 4.0)
        y = lambda v: v + SP                             # x axis: distance from the beaker axis
        ax.axvspan(0, res["column_r"].get(key) or 0, color="#dff0d8", alpha=0.6, lw=0)
        ax.axhline(bench, color=GREY, lw=1.0)
        ax.text(2, bench - 9, "bench", fontsize=9, color=GREY, va="top")
        ax.add_patch(Rectangle((y(-SP), SHELF_BOT), 174.0, 6.0, fc="#c9d0da", ec=INK, lw=0.8))   # shelf lobe
        slot_end = o.get("slot_end", 142.0 if key == "M3" else B.SLOT["y1"])
        ax.add_patch(Rectangle((y(B.SLOT["y0"]), SHELF_BOT - 0.2), slot_end - B.SLOT["y0"],
                               6.4, fc="white", ec="none"))
        for tl, al in ((0.0, 1.0), (90.0, 0.45)):
            R = np.array([[1, 0], [0, 1]])
            t = math.radians(tl)
            rot = lambda p: np.array([p[0] * math.cos(t) - p[1] * math.sin(t), p[0] * math.sin(t) + p[1] * math.cos(t)])
            plate = [rot(p) for p in ((-7.5, -35.25), (130.0, -35.25), (130.0, -29.25), (-7.5, -29.25))]
            ax.add_patch(Polygon([(y(p[0]), p[1]) for p in plate], closed=True, fc="#f7c35a", ec=INK, lw=0.6, alpha=al))
            tube = [rot(p) for p in ((-11.6, -6.5), (110.0, -6.5), (110.0, 6.5), (-11.6, 6.5))]
            ax.add_patch(Polygon([(y(p[0]), p[1] - 4) for p in tube], closed=True, fc="#e3c48a", ec=INK, lw=0.5, alpha=al))
            P = rod_pin(tl, o["a"])
            ax.plot([y(Bp[0]), y(P[0])], [Bp[1], P[1]], color=DK, lw=9 if tl == 0 else 6, alpha=al, solid_capstyle="butt")
            Lc = P16[o["act"]]["closed"] - 15.5
            u = (P - Bp) / np.linalg.norm(P - Bp)
            ax.plot([y(Bp[0]), y(Bp[0] + u[0] * Lc)], [Bp[1], Bp[1] + u[1] * Lc], color="#2b2d33", lw=14 if tl == 0 else 10,
                    alpha=al, solid_capstyle="butt")
            ax.add_patch(Circle((y(P[0]), P[1]), 3.0, fc="white", ec=INK, lw=1.0, alpha=al, zorder=5))
        ax.add_patch(Circle((y(0), 0), 3.0, fc=INK, zorder=6))
        ax.add_patch(Circle((y(Bp[0]), Bp[1]), 3.0, fc="white", ec=INK, lw=1.0, zorder=6))
        if key == "M0":
            ax.add_patch(Rectangle((y(128.0), Bp[1] - UB["h"] - 4.0), 6.0, SHELF_BOT - (Bp[1] - UB["h"] - 4.0), fc=OR, ec=INK, lw=0.6))
            ax.add_patch(Rectangle((y(o["a"] - 8.0), Bp[1] - UB["h"] - 4.0), 128 - o["a"] + 14, 4.0, fc=OR, ec=INK, lw=0.6))
        elif key in ("M1", "M2"):
            g = res["deck"][key]["geometry"]
            ax.add_patch(Rectangle((g["ring"][0], g["bottom"]), g["lobe_from_axis"] - g["ring"][0], DECK_T, fc=OR, ec=INK, lw=0.6))
            ax.add_patch(Rectangle((y(g["post_y"][0]), g["top"]), POST["d"], SHELF_BOT - g["top"], fc=OR, ec=INK, lw=0.6))
        else:
            ax.add_patch(Rectangle((y(Bp[0]) - 18, bench), 36, Bp[1] - UB["h"] - bench, fc=OR, ec=INK, lw=0.6))
            ax.text(y(Bp[0]), bench - 9, "a foot (or leg)\nper actuator", fontsize=8.5, ha="center", va="top", color=INK)
            ax.text(y(120.0), SHELF_BOT + 10, "slot open to\nthe lobe end", fontsize=8.5, ha="center", va="bottom", color=INK)
        ax.set_title(f"{key}  {o['title']}", fontsize=12.5, fontweight="bold", loc="left")
        txt = (f"{o['act']}, clevis {o['a']:.0f} mm behind the hinge" + (f"\nleaning {o['lean']:.0f}° outward" if o["lean"] else "") +
               f"\nshelf underside to bench: {SHELF_BOT - bench:.0f} mm"
               f"\nactuator foot {kin['base_pin_from_beaker_axis']:.0f} mm from the beaker axis"
               f"\nstroke used {kin['rod_out']['0']:.0f}–{kin['rod_out']['90']:.0f} mm of {kin['stroke']:.0f}"
               f"\nmax force {kin['max_force_N']:.0f} N (at {kin['max_force_at_tilt']:.0f}°)")
        if res["column_r"].get(key):
            txt += f"\nfree column under the shelf Ø{2 * res['column_r'][key]:.0f} mm"
        bx = (0.98, 0.985, "top", "right")
        ax.text(bx[0], bx[1], txt, transform=ax.transAxes, fontsize=9.4, va=bx[2], ha=bx[3],
                bbox=dict(fc="white", ec=GREY, lw=0.6, boxstyle="round,pad=0.4"))
        ax.set_xlim(-5, 300)
        ax.set_ylim(-285, 150)
        ax.set_aspect("equal")
        ax.grid(alpha=0.25)
        ax.set_xlabel("distance from the beaker axis (mm)")
    axs[0].set_ylabel("height above the hinge axis (mm)")
    fig.suptitle("Ways to hold the three P16s, one module in side view, to scale: dark at 0°, faded at 90°. "
                 "Orange: the new support. Green: the free column under the shelf.", fontsize=12.5, x=0.01, ha="left")
    fig.tight_layout(rect=(0, 0, 1, 0.965))
    fig.savefig(OUT / "mount_options.png", dpi=110, bbox_inches="tight")
    plt.close(fig)
    print("  -> mount_options.png", flush=True)


def station_render(key, o, res, tilts=(0, 45, 90), out_name=None):
    from PIL import Image, ImageDraw
    g = deck_geometry(o)
    parts = []
    for i, th in enumerate(B.BEARINGS):
        parts += module(float(tilts[i]), D.place(th, SP, 0.0), "ABC"[i], o)
    parts += [D.Part("deck + posts", deck(o), np.eye(4), (0.95, 0.47, 0.18), "fixed", False),
              D.Part("shelf", shelf_for(o), np.eye(4), (0.62, 0.66, 0.72), "fixed", False)]
    sp_ = res["deck"][key]["checks"]["stir_plate_150_on_bench_inside_deck"]
    floor = g["bottom"]                                  # the bench, with the deck standing on it
    if sp_["fits"]:
        parts.append(D.Part("stir plate", stir_plate(g["bottom"], sp_["rotation_deg"]), np.eye(4), (0.86, 0.86, 0.84),
                            "fixed", False))
        floor += STIR["h"]
    riser_top = BEAKER["rim"] - BEAKER["h"]
    if riser_top > floor + 1:
        parts.append(D.Part("riser", D.cyl(40.0, riser_top - floor, 0, 0, floor), np.eye(4), (0.75, 0.75, 0.72), "fixed", False))
    bk = D.cyl(BEAKER["d"] / 2, BEAKER["h"], 0, 0, riser_top).cut(D.cyl(BEAKER["d"] / 2 - 2, BEAKER["h"], 0, 0, riser_top + 2))
    parts.append(D.Part("beaker", bk, np.eye(4), D.COL["glass"], "fixed", False, 0.55))
    a = OUT / f"_{key}_a.png"
    D.render(parts, a, az=-62, el=14, size=(1150, 1150), dist=1.12, focal=(0, 0, -105))
    b = OUT / f"_{key}_b.png"
    D.render([p for p in parts if p.name not in ("beaker", "riser", "stir plate")], b, az=-100, el=-38, size=(1000, 1150),
             dist=1.12, focal=(0, 0, -140))
    ims = [Image.open(a), Image.open(b)]
    W = sum(i.width for i in ims)
    img = Image.new("RGB", (W, ims[0].height + 185), "white")
    x = 0
    for i in ims:
        img.paste(i, (x, 105))
        x += i.width
    d = ImageDraw.Draw(img)
    kin = res["kinematics"][key]
    d.text((22, 14), f"{key}: {o['title']}  ({o['act']}, clevis {o['a']:.0f} mm behind the hinge)", font=K.font(34, True),
           fill=(20, 20, 20))
    d.text((22, 60), f"Tilts {tilts[0]}, {tilts[1]} and {tilts[2]}°. Orange: the lower deck and its three posts, one print. "
           f"Grey: the one-piece base. Dark: the P16s on their U-brackets.", font=K.font(23), fill=(60, 60, 60))
    c = res["deck"][key]["checks"]
    sp_ = c["stir_plate_150_on_bench_inside_deck"]
    d.text((22, img.height - 72),
           "Left: from the front, with a 150 x 150 mm stir plate on the bench and a 250 mL beaker. Right: from below, without them."
           if sp_["fits"] else
           "Left: from the front, a 250 mL beaker on a riser; a 150 x 150 mm stir plate does NOT fit between these actuators"
           " (stand the station over it on legs). Right: from below.", font=K.font(21), fill=(40, 40, 40))
    d.text((22, img.height - 38),
           f"Shelf underside to bench {SHELF_BOT - g['bottom']:.0f} mm; deck {res['deck'][key]['size_mm'][0]:.0f} x "
           f"{res['deck'][key]['size_mm'][1]:.0f} mm; the closest a moving part comes to the deck or posts is "
           f"{c['module_to_deck_and_posts']['mm']:.1f} mm.", font=K.font(21), fill=(40, 40, 40))
    img.save(OUT / (out_name or f"mount_{key}.png"))
    a.unlink()
    b.unlink()
    print(f"  -> {out_name or f'mount_{key}.png'}", flush=True)


def wire_xy(w, step=1.5):
    """Points along a wire in order (edges taken in connection order, reversed ones flipped)."""
    from OCP.BRepTools import BRepTools_WireExplorer
    from OCP.TopAbs import TopAbs_REVERSED
    ex = BRepTools_WireExplorer(w.wrapped)
    pts = []
    while ex.More():
        e = cq.Edge(ex.Current())
        ts = np.linspace(0.0, 1.0, max(2, int(e.Length() / step)))
        if ex.Current().Orientation() == TopAbs_REVERSED:
            ts = ts[::-1]
        pts += [(e.positionAt(t).x, e.positionAt(t).y) for t in ts]
        ex.Next()
    return pts


def deck_drawing(res, key="M1"):
    """Dimensioned plan of the deck, and a side view of one post."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Circle, Polygon, Rectangle

    o = OPTIONS[key]
    g = deck_geometry(o)
    INK, GREY = "#1f1f1f", "#8a8a8a"
    fig = plt.figure(figsize=(17, 9.4))
    ax = fig.add_axes((0.02, 0.06, 0.56, 0.86))
    sk = deck(o, posts=False)
    sec = sk.intersect(cq.Solid.makeBox(1000, 1000, 0.01, cq.Vector(-500, -500, g["bottom"] + DECK_T / 2)))
    for f_ in sec.Faces():
        ax.add_patch(Polygon(wire_xy(f_.outerWire()), closed=True, fc="#fbe3cc", ec=INK, lw=1.0))
        for w in f_.innerWires():
            ax.add_patch(Polygon(wire_xy(w), closed=True, fc="white", ec=INK, lw=1.0))
    for th in B.BEARINGS:
        M = D.place(th, SP, 0.0)
        for (px, py_), lab in ((g["bracket_hole"], "b"), (g["post_screw"], "p")):
            q = M @ np.array([px, py_, 0, 1.0])
            ax.add_patch(Circle(q[:2], 2.25 if lab == "b" else 2.75, fc="white", ec=INK, lw=0.9))
        pts = B.station_xy(M, [(-g["post_x"], g["post_y"][0]), (g["post_x"], g["post_y"][0]), (g["post_x"], g["post_y"][1]),
                               (-g["post_x"], g["post_y"][1])])
        ax.add_patch(Polygon(pts, closed=True, fc="none", ec="#c0392b", lw=1.2, ls="--"))
        ub = B.station_xy(M, [(-7.45, o["a"] - 3.95), (7.45, o["a"] - 3.95), (7.45, o["a"] + 3.95), (-7.45, o["a"] + 3.95)])
        ax.add_patch(Polygon(ub, closed=True, fc="none", ec="#2f5d9b", lw=1.0))
        c = M @ np.array([0, 0, 0, 1.0])
        e = M @ np.array([0, g["lobe_end"] + 12, 0, 1.0])
        ax.plot([0, e[0]], [0, e[1]], color=GREY, lw=0.6, ls=(0, (8, 3, 2, 3)))
    ax.add_patch(Circle((0, 0), g["ring"][0], fc="none", ec=GREY, lw=0.5, ls=":"))
    ax.plot([0], [0], "+", color=INK, ms=14)
    # dimensions (module at bearing 90: its centre line runs up the page)
    def dim(p1, p2, off, text, ang=0):
        p1, p2 = np.array(p1, float), np.array(p2, float)
        n = np.array([-(p2 - p1)[1], (p2 - p1)[0]])
        n = n / np.linalg.norm(n) * off
        a_, b_ = p1 + n, p2 + n
        ax.annotate("", xy=b_, xytext=a_, arrowprops=dict(arrowstyle="<->", lw=0.9, color=INK, shrinkA=0, shrinkB=0))
        for p, q in ((p1, a_), (p2, b_)):
            ax.plot([p[0], q[0]], [p[1], q[1]], color=GREY, lw=0.5)
        m = (a_ + b_) / 2
        ax.text(m[0], m[1], text, fontsize=9.5, ha="center", va="center", rotation=ang,
                bbox=dict(fc="white", ec="none", pad=0.6))
    r_in, r_out = g["ring"]
    dim((-r_in, 0), (r_in, 0), 0, f"Ø{2 * r_in:.0f} opening")
    dim((-r_out, -150), (r_out, -150), 0, f"Ø{2 * r_out:.0f} ring")
    yb, yp, ye = SP + o["a"], SP + g["post_screw"][1], SP + g["lobe_end"]
    dim((0, 0), (0, yb), -60, f"{yb:.0f}", 90)
    dim((0, 0), (0, yp), -85, f"{yp:.0f}", 90)
    dim((0, 0), (0, ye), -110, f"{ye:.0f}", 90)
    dim((-LOBE_HALF, ye), (LOBE_HALF, ye), 18, f"{2 * LOBE_HALF:.0f}")
    ax.annotate("Ø4.5 hole (the P16's #8-32 or M4)\nin a 1 mm pocket that keys\nthe U-bracket square (blue)", xy=(7.5, yb),
                xytext=(-182, yb + 22), fontsize=9.5, arrowprops=dict(arrowstyle="-", lw=0.6, color=GREY))
    ax.annotate(f"post {POST['w']:.0f} x {POST['d']:.0f} (red dashes),\nprinted on the deck; Ø5.5 hole\nfor an M5 into its top and foot",
                xy=(-g["post_x"], yp), xytext=(-182, yp + 8), fontsize=9.5, arrowprops=dict(arrowstyle="-", lw=0.6, color=GREY))
    ax.text(0, 4, "beaker axis", fontsize=9, ha="center", va="bottom", color=GREY)
    ex = res["deck"][key]["size_mm"]
    ax.text(-160, -175, f"Deck {ex[0]:.1f} x {ex[1]:.1f} mm, {DECK_T:.0f} thick; corners R{FILLET:.0f}.\n"
            f"Fits one H2D nozzle ({BED[0]:.0f} x {BED[1]:.0f}) like the base.\n"
            f"Every module's lobe is the same: sketch one, pattern 3x at 120°.", fontsize=10, va="top")
    ax.set_xlim(-185, 185)
    ax.set_ylim(-185, 205)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_title(f"{key} lower deck, plan (mm, from the beaker axis)", fontsize=13, fontweight="bold", loc="left")
    # side view: one module's post, deck and actuator at 0 deg
    ax2 = fig.add_axes((0.62, 0.06, 0.36, 0.86))
    Bp = base_pin(o)
    yy = lambda v: v + SP
    ax2.add_patch(Rectangle((yy(-SP), SHELF_BOT), 174, 6, fc="#c9d0da", ec=INK, lw=0.8))
    ax2.add_patch(Rectangle((g["ring"][0], g["bottom"]), g["lobe_from_axis"] - g["ring"][0], DECK_T, fc="#fbe3cc", ec=INK, lw=0.8))
    ax2.add_patch(Rectangle((yy(g["post_y"][0]), g["top"]), POST["d"], SHELF_BOT - g["top"], fc="#fbe3cc", ec=INK, lw=0.8))
    P = rod_pin(0.0, o["a"])
    w, h, ln = K.P16R["housing"]
    e = K.P16R["axis_from_edge"]
    ax2.add_patch(Rectangle((yy(o["a"] - e), Bp[1] + 5), h, ln, fc="#4a4d55", ec=INK, lw=0.6))
    ax2.add_patch(Rectangle((yy(o["a"] - 6), Bp[1] + 75), 12, P16[o["act"]]["closed"] - 15.5 - 75, fc="#6b6e75", ec=INK, lw=0.6))
    ax2.plot([yy(o["a"])] * 2, [Bp[1] + P16[o["act"]]["closed"] - 17, P[1]], color="#9a9da3", lw=4)
    ax2.add_patch(Rectangle((yy(o["a"] - 3.75), g["top"]), 7.5, UB["h"] + 3, fc="#30333a", ec=INK, lw=0.5))
    for q in (P, Bp):
        ax2.add_patch(Circle((yy(q[0]), q[1]), 2.6, fc="white", ec=INK, lw=0.9, zorder=5))
    ax2.add_patch(Circle((yy(0), 0), 2.6, fc=INK))
    ax2.plot([yy(-7.5), yy(130)], [-35.25, -35.25], color="#b8860b", lw=1.2)
    def vdim(x, z1, z2, text):
        ax2.annotate("", xy=(x, z2), xytext=(x, z1), arrowprops=dict(arrowstyle="<->", lw=0.9, color=INK))
        ax2.text(x + 3, (z1 + z2) / 2, text, fontsize=9.5, va="center", rotation=90, bbox=dict(fc="white", ec="none", pad=0.5))
    vdim(yy(g["post_y"][1]) + 14, g["top"], SHELF_BOT, f"post {g['post_len']:.2f}")
    vdim(yy(g["post_y"][1]) + 34, g["bottom"], SHELF_BOT, f"{SHELF_BOT - g['bottom']:.2f} shelf underside to deck underside")
    vdim(yy(o["a"]) - 22, Bp[1], P[1], f"pin to pin {P[1] - Bp[1]:.0f} at 0°")
    ax2.text(62, g["top"] + 4, f"U-bracket: pin\n{UB['h']} above the deck", fontsize=9)
    ax2.text(62, SHELF_BOT + 9, "shelf (base.py)", fontsize=9.5)
    ax2.text(g["ring"][0], g["bottom"] - 12, "deck, 6", fontsize=9.5)
    ax2.set_xlim(60, 230)
    ax2.set_ylim(g["bottom"] - 25, 25)
    ax2.set_aspect("equal")
    ax2.grid(alpha=0.25)
    ax2.set_xlabel("distance from the beaker axis (mm)")
    ax2.set_ylabel("height above the hinge axis (mm)")
    ax2.set_title("Side view on one module's centre line, 0°", fontsize=13, fontweight="bold", loc="left")
    fig.savefig(OUT / f"mount_deck_drawing.png", dpi=110)
    plt.close(fig)
    print("  -> mount_deck_drawing.png", flush=True)


def main():
    OUT.mkdir(exist_ok=True)
    CAD.mkdir(exist_ok=True)
    res = dict(torque_Nmm=TORQUE, options={k: dict(o) for k, o in OPTIONS.items()},
               kinematics={k: kinematics(o) for k, o in OPTIONS.items()}, deck={}, column_r={})
    for k, v in res["kinematics"].items():
        print(k, v, flush=True)
    res["column_r"]["M0"] = None                      # filled from M1 (same actuator placement)
    for key in ("M1", "M2"):
        o = OPTIONS[key]
        g = deck_geometry(o)
        dk = deck(o)
        bb = deck(o, posts=False).BoundingBox()
        res["deck"][key] = dict(geometry=g, size_mm=[round(bb.xlen, 1), round(bb.ylen, 1)],
                                fits_h2d=bool(bb.xlen <= BED[0] and bb.ylen <= BED[1]),
                                volume_cm3=round(dk.Volume() / 1000, 1), shelf_underside_to_bench=round(SHELF_BOT - g["bottom"], 2))
        print(key, "deck", res["deck"][key], flush=True)
        res["deck"][key]["checks"] = checks(o)
        res["column_r"][key] = res["deck"][key]["checks"]["p16_closest_to_beaker_axis_under_shelf"]
        if key == "M1":
            res["column_r"]["M0"] = res["column_r"]["M1"]
        res["deck"][key]["checks"]["block_on_plate"] = own_parts_check(o)
        print(key, "checks", res["deck"][key]["checks"], flush=True)
        cq.exporters.export(cq.Workplane().add(dk), str(CAD / f"deck_{key}.step"))
    (HERE / "mounts.json").write_text(json.dumps(res, indent=1, default=float) + "\n")
    options_panel(res)
    deck_drawing(res, "M1")
    station_render("M1", OPTIONS["M1"], res)
    station_render("M2", OPTIONS["M2"], res)


if __name__ == "__main__":
    main()
