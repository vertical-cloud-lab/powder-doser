"""More room for the scale under the tri-star: options that spread out what hangs round it (issue #204, 21 Nov).

Ethan asked: whatever the legs turn out to be, they have to fit easily round the scale (a new one, whose
dimensions are to come).  What are some options that make the space between them bigger?

Two things hang round the scale under the shelf: the stand's legs and the three P16 actuators.  In
scale_room.py (S2, 21 Nov) the actuators were the tighter of the two: Ø187 mm between them at any tilt
and Ø233 mm parked, while S2's posts are Ø336 mm apart.  So the options here move the legs, the
actuators, or both, or take the actuators out from under the shelf altogether:

  L0  today: S2's posts at the lobe ends; each P16-150 straight under its clevis pin, 95 mm behind the hinge.
  L1  legs splayed outward: the actuators as today, on their own hangers; three legs splayed 15 deg.
  L2  actuators leaning 25 deg outward: the same P16-150 and clevis block (the pin 3 mm nearer the hinge,
      so the stroke still covers 0-90 deg); each foot on a post further out, on an outrigger arm.
  L3  a longer lever: the clevis pin 135 mm behind the hinge, on a tail under the plate's rear end, and a
      P16-200; the actuators stay vertical, 40 mm further out; posts behind them.
  L4  both: the pin 120 mm behind the hinge, a P16-200, leaning 25 deg outward; posts further out.
  L5  nothing under the shelf: a gearmotor on each module's hinge axis, beside its +X hinge tower, in the
      gap to the next module.  The P16s, clevis blocks and slots go.  Only the legs (S2's posts) remain.

For each it measures, in 10 mm bands below the shelf's underside: the free radius about the beaker axis
(the actuators at any tilt 0-90 deg, at 0-60 deg, and parked; and the legs), and the front opening (the
widest thing, centred on the beaker axis, that fits between everything in front of the axis).  It checks
each layout's new parts against every moving part over 0-90 deg (2 mm target), the actuator stroke, and
fits the HR-100A (scale_room.py's model) at every orientation as an example of a real balance.

    pip install cadquery trimesh python-fcl rtree vtk pillow numpy matplotlib scipy
    xvfb-run -a python leg_room.py            # about 4 min; writes leg_room.json and renders/legroom_*.png
    xvfb-run -a python leg_room.py --figures-only   # redraws the charts from leg_room.json (no renders)

Frames as in doserlib.py: the unit frame has the hinge axis on x, +y behind the hinge, z up, hinge at
z = 0; the station frame has the beaker axis on z, modules at bearings 90 (back), 210 and 330 deg, the
front gap facing -y.  Every new part (legs, arms, tails, motors, cradles) is a placeholder.
"""
from __future__ import annotations

import json
import math
import sys
import time
from pathlib import Path

import numpy as np
import cadquery as cq

import doserlib as D
import components as K
import base as B
import mounts as MT
import stands as ST
import scale_room as SR

HERE = Path(__file__).resolve().parent
OUT = HERE / "renders"
SP = B.SP                                   # 32 mm, hinge axis to beaker axis
BOT, TOP = B.BOT, B.TOP                     # shelf underside / top (-43.25 / -37.25)
S = 340.0                                   # shelf underside above the bench, for the legs and the HR-100A
ZB = BOT - S                                # bench, station z
GAP = 2.0
TILTS = tuple(range(0, 91, 5))
BAND = 10.0
DEPTHS = np.arange(0.0, S, BAND)            # bands below the shelf's underside
BEARINGS = B.BEARINGS
MT.P16.setdefault("P16-200", dict(closed=247.0, stroke=200.0))   # closed = stroke + 47 mm, as the P16-100/150

# colours
LEG = (0.16, 0.62, 0.56)                    # printed leg parts (teal)
ALU = (0.78, 0.80, 0.83)
NEWC = K.STATUS["new"][2]
MOTOR = (0.22, 0.24, 0.27)
STEEL = (0.55, 0.56, 0.58)

OPTIONS = {
    "L0": dict(title="Today", short="today (S2)", act=dict(a=95.0, act="P16-150", lean=0.0), legs="s2",
               change="nothing"),
    "L1": dict(title="Legs splayed out", short="legs splayed", act=dict(a=95.0, act="P16-150", lean=0.0),
               legs="splay", splay=15.0, hangers=True, change="three splayed legs; the P16s on their own hangers"),
    "L2": dict(title="Actuators leaning out 25°", short="P16s leaning 25°", act=dict(a=95.0, act="P16-150", lean=25.0),
               legs="post", fit_a=True, change="the P16 feet move out; posts on outrigger arms"),
    "L3": dict(title="Longer lever, P16-200", short="longer lever", act=dict(a=135.0, act="P16-200", lean=0.0),
               legs="post", change="P16-200s; a tail under each plate's rear end; longer slots; posts behind the P16s"),
    "L4": dict(title="Longer lever + leaning 25°", short="lever + lean", act=dict(a=120.0, act="P16-200", lean=25.0),
               legs="post", change="P16-200s leaning 25°; posts on longer outrigger arms"),
    "L5": dict(title="Drive on the hinge axis", short="hinge-axis drive", act=None, legs="post0",
               change="a gearmotor on each hinge axis instead of a P16; no slots"),
}
ORDER = list(OPTIONS)

# hinge-axis drive (L5): placeholders, unit frame of the module whose hinge it drives (+X side)
# (the coupler starts 53 mm out: nearer than that it would pass within 2 mm of the next module's tower nose)
HD = dict(shaft_d=8.0, shaft_x=(20.0, 76.0), coupler=(10.0, 53.0, 73.0), motor_r=18.5, motor_x=(75.0, 160.0),
          cradle_x=(82.0, 154.0), cradle_w=22.0, pad_x=(44.0, 164.0), pad_w=24.0)
TOWER_OUT = B.TOWER_X[1]                    # 41.2: the +X tower's outer face


# --------------------------------------------------------------------------- #
# small helpers
# --------------------------------------------------------------------------- #
_S: dict = {}


def cached(k, fn):
    if k not in _S:
        _S[k] = fn()
    return _S[k]


def part(name, shape, M, colour, unit="fixed", moving=False, kind="new"):
    p = D.Part(name, shape, M, colour, unit, moving)
    p.kind = kind
    return p


def strut_yz(y0, z0, y1, z1, w=20.0, d=20.0):
    """A straight w (x) by d (perpendicular, in the y-z plane) bar from (y0, z0) to (y1, z1), unit frame."""
    L_ = math.hypot(y1 - y0, z1 - z0)
    ang = math.degrees(math.atan2(y1 - y0, z1 - z0))          # from +z towards +y
    b = D.box(-w / 2, w / 2, -d / 2, d / 2, 0.0, L_)
    return b.rotate(cq.Vector(0, 0, 0), cq.Vector(1, 0, 0), -ang).translate(cq.Vector(0, y0, z0))


def samples(shape, M, spacing=2.0):
    import trimesh
    m = D.mesh_of(shape)
    n = max(200, int(m.area / spacing ** 2))
    p, _ = trimesh.sample.sample_surface_even(m, n, seed=1)
    p = np.vstack([p, np.asarray(m.vertices)])
    return (M[:3, :3] @ p.T).T + M[:3, 3]


def in_unit(P, th):
    """Station points -> the unit frame of the module at bearing th (x along its hinge, y behind)."""
    Mi = np.linalg.inv(D.place(th, SP, 0.0))
    return (Mi[:3, :3] @ P.T).T + Mi[:3, 3]


# --------------------------------------------------------------------------- #
# actuator kinematics
# --------------------------------------------------------------------------- #
def fit_a(o, spare_min=1.0):
    """Largest clevis distance (0.5 mm steps, from o['a'] down) whose stroke still covers 0-90 deg."""
    o = dict(o)
    while MT.kinematics(o)["spare_at_90"] < spare_min:
        o["a"] -= 0.5
    return o


def lean_at(o, tilt):
    """The actuator's lean from vertical (deg, + = its foot further out) at ``tilt``."""
    P = MT.rod_pin(tilt, o["a"])
    Bp = MT.base_pin(o)
    return math.degrees(math.atan2(Bp[0] - P[0], P[1] - Bp[1]))


# --------------------------------------------------------------------------- #
# one module, per option
# --------------------------------------------------------------------------- #
def tail(o):
    """A tail under the plate's rear end that carries the clevis block when the pin sits behind the floor
    (the floor ends 130 mm behind the hinge): 30 wide, 6 thick, from 112 mm to 14 mm past the pin."""
    return D.box(-17.0, 17.0, 112.0, o["a"] + 14.0, K.FLOOR_U, K.FLOOR_U + 6.0)


def ubracket_frame(Mst, o):
    """The P16's own U-bracket at its rear pin, square to the actuator at mid-tilt (45 deg)."""
    Bp = MT.base_pin(o)
    return Mst @ D.Tt(0.0, Bp[0], Bp[1]) @ D.Rx(-lean_at(o, 45.0))


def module_parts(key, tilt, Mst, tag):
    """Every part of one module at ``tilt`` for option ``key`` (towers are in the base)."""
    opt = OPTIONS[key]
    o = opt["act_fit"] if opt["act"] else None
    if o is None:                                           # L5: no actuator, no clevis block
        ps = [p for p in MT.module(float(tilt), Mst, tag, dict(a=95.0, act="P16-150", lean=0.0))
              if not p.name.endswith(("clevis block", "M4 pin", "P16 body", "P16 rod", "P16 bracket"))]
    else:
        ps = MT.module(float(tilt), Mst, tag, o)
        for p in ps:
            if p.name.endswith("P16 bracket"):
                p.M = ubracket_frame(Mst, o)
        if o["a"] + 12.0 > 130.0:
            ps.append(D.Part(f"{tag}:tail", cached(("tail", o["a"]), lambda: tail(o)), Mst @ D.Rx(float(tilt)),
                             NEWC, tag, True))
    for p in ps:
        p.kind = "module"
    return ps


HANGING = ("clevis block", "M4 pin", "P16 body", "P16 rod", "P16 bracket", "tail")


# --------------------------------------------------------------------------- #
# legs and the other fixed parts, per option (unit frame of each module, placed 3x)
# --------------------------------------------------------------------------- #
def flange(y0, y1, half=20.0, t=6.0):
    return ST.bolt_holes(D.box(-half, half, y0, y1, BOT - t, BOT), BOT - t, BOT)


def leg_post(y_post, tab=None, slot=None):
    """A vertical 20 x 20 post at y_post (unit frame) on a printed arm bolted through the lobe end's four
    hanger holes (an outrigger when the post is past the lobe end), a long-toed foot, and, if ``tab``
    is given (o), a printed tab from the post under the P16's U-bracket."""
    zt = BOT - 8.0
    arm = flange(112.0, max(140.0, y_post + 16.0), 20.0 if slot is None or slot < 112.5 else 26.0, 8.0)
    if slot is not None and slot > 112.5:                  # a fork either side of the lengthened slot
        arm = arm.cut(D.box(-B.SLOT["x"], B.SLOT["x"], 100.0, slot, BOT - 20.0, BOT + 1.0))
    post = D.box(-10.0, 10.0, y_post - 10.0, y_post + 10.0, ZB + 6.0, zt)
    post = post.cut(D.box(-8.5, 8.5, y_post - 8.5, y_post + 8.5, ZB, zt + 1))
    foot = D.box(-15.0, 15.0, y_post - 14.0, y_post + 60.0, ZB, ZB + 6.0)
    out = arm.fuse(post).fuse(foot)
    if tab is not None:
        Mu = ubracket_frame(np.eye(4), tab)                 # bracket frame -> unit frame
        h = K.UB["h"]
        # the tab in the bracket's frame: under its base, from 12 mm inboard of the pin out to the post
        far = 80.0
        tb = D.box(-12.0, 12.0, -12.0, far, -h - 5.0, -h)
        tb = tb.moved(C_loc(Mu))
        tb = tb.intersect(D.box(-12.0, 12.0, -400.0, y_post - 9.5, ZB, BOT))   # stop at the post's inner face
        out = out.fuse(tb)
    return out.clean()


def leg_splay(y_top, splay):
    """A 20 x 20 leg from under the lobe end, splayed ``splay`` deg outward, on a foot; with a flange."""
    zt = BOT - 6.0
    y_bot = y_top + (zt - (ZB + 6.0)) * math.tan(math.radians(splay))
    leg = strut_yz(y_top, zt, y_bot, ZB + 6.0)
    leg = leg.intersect(D.box(-50, 50, -400, 800, ZB + 6.0, zt))
    fl = flange(112.0, y_top + 12.0, 20.0)
    foot = D.box(-15.0, 15.0, y_bot - 25.0, y_bot + 25.0, ZB, ZB + 6.0)
    return fl.fuse(leg).fuse(foot).clean(), y_bot


def C_loc(M):
    import concepts as C
    return C._loc(M)


def hinge_drive():
    """L5: the drive on the module's +X hinge axis (unit frame): an 8 mm shaft through the +X knuckle and
    tower, a coupler, a Ø37 gearmotor with encoder (85 mm, placeholder) and its cradle on a pad."""
    r = HD["motor_r"]
    shaft = D.cyl(HD["shaft_d"] / 2, HD["shaft_x"][1] - HD["shaft_x"][0], HD["shaft_x"][0], 0, 0, d=(1, 0, 0))
    cr, c0, c1 = HD["coupler"]
    coupler = D.cyl(cr, c1 - c0, c0, 0, 0, d=(1, 0, 0))
    motor = D.cyl(r, HD["motor_x"][1] - HD["motor_x"][0], HD["motor_x"][0], 0, 0, d=(1, 0, 0))
    w = HD["cradle_w"]
    cradle = D.box(HD["cradle_x"][0], HD["cradle_x"][1], -w, w, TOP, -r + 6.0).cut(
        D.cyl(r + 0.3, 200, HD["cradle_x"][0] - 1, 0, 0, d=(1, 0, 0)))
    for x in (HD["cradle_x"][0], HD["cradle_x"][1] - 8.0):               # two clamp rings
        cradle = cradle.fuse(D.cyl(r + 4.0, 8.0, x, 0, 0, d=(1, 0, 0)).cut(D.cyl(r + 0.3, 10, x - 1, 0, 0, d=(1, 0, 0))))
    pw = HD["pad_w"]
    pad = D.box(HD["pad_x"][0], HD["pad_x"][1], -pw, pw, BOT, TOP)
    return dict(shaft=shaft.clean(), coupler=coupler.clean(), motor=motor.clean(), cradle=cradle.clean(),
                pad=pad.clean())


def fixed_parts(key):
    """Legs (and hangers, motors, cradles) for option ``key``, station frame, 3x; plus the base."""
    opt = OPTIONS[key]
    o = opt.get("act_fit")
    out = []
    kind = opt["legs"]
    for i, th in enumerate(BEARINGS):
        u = "ABC"[i]
        M = D.place(th, SP, 0.0)
        if kind == "s2":
            continue
        if kind == "splay":
            sh, _ = cached(("splay", opt["splay"]), lambda: leg_splay(146.0, opt["splay"]))
            out.append(part(f"{u}:leg", sh, M, LEG))
        elif kind == "post":
            yp = opt["post_y"]
            sh = cached(("post", key), lambda: leg_post(yp, tab=o, slot=slot_end(key)))
            out.append(part(f"{u}:leg", sh, M, LEG))
        elif kind == "post0":
            sh = cached("post0", lambda: leg_post(146.0, tab=None))
            out.append(part(f"{u}:leg", sh, M, LEG))
        if opt.get("hangers"):
            out.append(part(f"{u}:hanger", cached("hanger", K.hanger), M, LEG))
        if key == "L5":
            hd = cached("hd", hinge_drive)
            out.append(part(f"{u}:drive shaft", hd["shaft"], M, STEEL, kind="drive"))
            out.append(part(f"{u}:coupler", hd["coupler"], M, STEEL, kind="drive"))
            out.append(part(f"{u}:gearmotor", hd["motor"], M, MOTOR, kind="drive"))
            out.append(part(f"{u}:motor cradle", hd["cradle"], M, NEWC, kind="drive"))
            out.append(part(f"{u}:motor pad", hd["pad"], M, NEWC, kind="drive"))
    if kind == "s2":
        for p in ST.s2_parts(S):
            p.kind = "new"
            p.name = f"{p.name[-1]}:{p.name[:-2]}"
            out.append(p)
    return out


def slot_end(key):
    """Where each module's slot has to end (unit y): 4 mm past the farthest point at which the clevis
    block, rod or actuator passes through the shelf or comes within 6 mm under the 8 mm arm, over
    0..90 deg; never shorter than today's 112 mm."""
    opt = OPTIONS[key]
    if opt["act"] is None:
        return None
    if "slot_y1" not in opt:
        ymax = -1e9
        for t in TILTS:
            for p in module_parts(key, t, np.eye(4), "A"):
                if not p.name.endswith(HANGING):
                    continue
                v = samples(p.shape, p.M, 1.0)
                v = v[(v[:, 2] > BOT - 14.0) & (v[:, 2] < TOP + 1.0) & (np.abs(v[:, 0]) < 30.0)]
                if len(v):
                    ymax = max(ymax, float(v[:, 1].max()))
        opt["slot_y1"] = round(max(B.SLOT["y1"], ymax + 4.0), 1)
    return opt["slot_y1"]


def base_for(key):
    """The one-piece base (base.py), each slot lengthened as far as slot_end() needs (open-ended past
    the lobe end), or closed when there is no actuator (L5)."""
    y1 = slot_end(key)
    if y1 is not None and abs(y1 - B.SLOT["y1"]) < 0.1:
        return B.base_station()
    return cached(("base", y1), lambda: base_with_slot(y1))


def base_with_slot(y1):
    sk = B.shelf_outline_sketch()
    shelf = cq.Workplane("XY", origin=(0, 0, BOT)).placeSketch(sk).extrude(B.T).val()
    shelf = shelf.cut(D.cyl(B.WIN_D / 2, B.T + 2, 0, 0, BOT - 1))
    for th in BEARINGS:
        loc = C_loc(D.place(th, SP, 0.0))
        cut = None
        if y1 is not None:
            cut = D.box(-B.SLOT["x"], B.SLOT["x"], B.SLOT["y0"], y1, BOT - 1, TOP + 1)
        for x in (-B.PAD["x"], B.PAD["x"]):
            for y in B.PAD["y"]:
                h = D.cyl(B.PAD["d"] / 2, B.T + 2, x, y, BOT - 1)
                cut = h if cut is None else cut.fuse(h)
        shelf = shelf.cut(cut.moved(loc))
    tw = B.tower_today()
    tw_neg = tw.mirror("YZ", (0, 0, 0))
    for th in BEARINGS:
        loc = C_loc(D.place(th, SP, 0.0))
        shelf = shelf.fuse(tw.moved(loc)).fuse(tw_neg.moved(loc))
    return shelf.clean()


# --------------------------------------------------------------------------- #
# the room: samples of everything under the shelf
# --------------------------------------------------------------------------- #
def hanging_samples(key):
    """(points, tilt) of everything that hangs below the shelf's underside from module A, tilts 0..90."""
    if OPTIONS[key]["act"] is None:
        return np.zeros((0, 3)), np.zeros(0)
    M = D.place(90.0, SP, 0.0)
    P, T = [], []
    for t in TILTS:
        for p in module_parts(key, t, M, "A"):
            if not p.name.endswith(HANGING):
                continue
            q = samples(p.shape, p.M, 1.5)
            q = q[q[:, 2] < BOT]
            P.append(q)
            T.append(np.full(len(q), t))
    return np.vstack(P), np.concatenate(T)


def rot3(P):
    """Module A's points copied to the other two modules (station frame)."""
    out = [P]
    for d in (120.0, 240.0):
        R = D.Rz(d)[:3, :3]
        out.append((R @ P.T).T)
    return np.vstack(out)


def leg_samples(key):
    P = [samples(p.shape, p.M, 2.0) for p in fixed_parts(key) if p.kind == "new"]
    P = np.vstack(P)
    return P[P[:, 2] < BOT]


def room(key, hang, legs):
    """Per depth band: free radius (actuators at any tilt, <= 60 deg, parked; legs; both) and the
    front opening (twice the smallest |x| of anything in front of the beaker axis)."""
    P, T = hang
    allP = rot3(P) if len(P) else np.zeros((0, 3))
    allT = np.tile(T, 3) if len(T) else np.zeros(0)
    rows = []
    for d0 in DEPTHS:
        z1, z0 = BOT - d0, BOT - d0 - BAND
        row = dict(depth=[round(float(d0)), round(float(d0 + BAND))])
        sel = (P[:, 2] < z1) & (P[:, 2] >= z0) if len(P) else np.zeros(0, bool)
        r = np.hypot(P[:, 0], P[:, 1]) if len(P) else np.zeros(0)
        for lab, lim in (("act_any", 90), ("act_60", 60), ("act_parked", 0)):
            s = sel & (T <= lim) if len(P) else sel
            row[lab] = round(float(r[s].min()), 1) if s.any() else None
        sl = (legs[:, 2] < z1) & (legs[:, 2] >= z0)
        row["legs"] = round(float(np.hypot(legs[sl, 0], legs[sl, 1]).min()), 1) if sl.any() else None
        vals = [v for v in (row["act_any"], row["legs"]) if v is not None]
        row["free_r"] = min(vals) if vals else None
        # front opening, any tilt / parked
        for lab, lim in (("front_any", 90), ("front_parked", 0)):
            pts = []
            if len(allP):
                s = (allP[:, 2] < z1) & (allP[:, 2] >= z0) & (allT <= lim) & (allP[:, 1] < 0)
                pts.append(allP[s])
            s = sl & (legs[:, 1] < 0)
            pts.append(legs[s])
            pts = np.vstack(pts) if pts else np.zeros((0, 3))
            row[lab] = round(float(2 * np.abs(pts[:, 0]).min()), 1) if len(pts) else None
        rows.append(row)
    return rows


def summary(rows, at=(15, 105, 205)):
    """Free diameter and front opening at a few depths (the band that holds each depth)."""
    out = {}
    for d in at:
        r = next(x for x in rows if x["depth"][0] <= d < x["depth"][1])
        dia = lambda v: None if v is None else round(2 * v)
        out[str(d)] = dict(free_dia_any=dia(r["free_r"]),
                           free_dia_60=dia(min([v for v in (r["act_60"], r["legs"]) if v is not None], default=None)),
                           free_dia_parked=dia(min([v for v in (r["act_parked"], r["legs"]) if v is not None], default=None)),
                           actuators_dia_any=dia(r["act_any"]), legs_dia=dia(r["legs"]),
                           front_any=None if r["front_any"] is None else round(r["front_any"]),
                           front_parked=None if r["front_parked"] is None else round(r["front_parked"]))
    return out


# --------------------------------------------------------------------------- #
# checks
# --------------------------------------------------------------------------- #
def checks(key):
    """New fixed parts (legs, arms, tabs, hangers, motors) and the base against every moving part of the
    modules over 0..90 deg, one module at a time (so every tilt mix); the drive (L5) also against the
    neighbouring module; the stand's own parts against the module at rest."""
    fx = fixed_parts(key)
    base = part("base", base_for(key), np.eye(4), (0.6, 0.6, 0.6))
    so = ST._objs(fx)
    bo = ST._objs([base])
    worst = dict(stand=(1e9, None, None, None), base=(1e9, None, None, None))
    mounted = ("P16 bracket",)
    for i, th in enumerate(BEARINGS):
        u = "ABC"[i]
        for t in TILTS:
            for p, op in ST._objs(module_parts(key, t, D.place(th, SP, 0.0), u)):
                for q, oq in so:
                    if p.name.endswith(mounted) and q.name.startswith(u + ":") and q.name.endswith(("leg", "hanger", "S2 sleeve")):
                        continue              # the U-bracket sits on its own leg's tab (or hanger's foot)
                    if p.name.endswith("Mounting plate") and q.name == f"{u}:drive shaft":
                        continue              # the shaft drives this module's knuckle
                    d = ST._dist(op, oq)
                    if d < worst["stand"][0]:
                        worst["stand"] = (d, p.name, q.name, t)
                if p.name.endswith(("Mounting plate",)):
                    continue                  # the plate's knuckles run 0.3 mm from the towers, as today
                for q, oq in bo:
                    d = ST._dist(op, oq)
                    if d < worst["base"][0]:
                        worst["base"] = (d, p.name, q.name, t)
    out = {k: dict(mm=round(v[0], 2), between=f"{v[1]} / {v[2]}", at_tilt=v[3]) for k, v in worst.items()}
    if key == "L5":
        out["drive"] = drive_checks()
    return out


def drive_checks():
    """L5 in more detail: each part of A's drive against A's own parts (except the plate it drives) and
    against its neighbour C's parts, over 0..90 deg; and against the base (towers)."""
    hd = cached("hd", hinge_drive)
    MA, MC = D.place(90.0, SP, 0.0), D.place(330.0, SP, 0.0)
    drive = [part(f"A:{k}", s, MA, MOTOR) for k, s in hd.items() if k != "pad"]
    do = ST._objs(drive)
    res = {}
    for who, M, u in (("own module (A)", MA, "A"), ("neighbour (C)", MC, "C")):
        w = (1e9, None, None, None)
        for t in TILTS:
            for p, op in ST._objs(module_parts("L5", t, M, u)):
                for q, oq in do:
                    if u == "A" and q.name == "A:shaft" and p.name.endswith("Mounting plate"):
                        continue              # the shaft is keyed into this plate's +X knuckle
                    d = ST._dist(op, oq)
                    if d < w[0]:
                        w = (d, p.name, q.name, t)
        res[who] = dict(mm=round(w[0], 2), between=f"{w[1]} / {w[2]}", at_tilt=w[3])
    base = part("base", base_for("L5"), np.eye(4), (0.6, 0.6, 0.6))
    bo = ST._objs([base])
    w = (1e9, None)
    for q, oq in do:
        if q.name in ("A:shaft", "A:cradle"):
            continue                          # the shaft runs in the +X tower's bore; the cradle sits on the shelf
        d = ST._dist(oq, bo[0][1])
        if d < w[0]:
            w = (d, q.name)
    res["base_towers_to_coupler_and_motor"] = dict(mm=round(w[0], 2), part=w[1])
    # plan position of A's gearmotor: bearing and radius of its two ends
    ends = []
    for x in HD["motor_x"]:
        p = MA @ np.array([x, 0.0, 0.0, 1.0])
        ends.append(dict(r=round(float(math.hypot(p[0], p[1])), 1), bearing=round(math.degrees(math.atan2(p[1], p[0])) % 360, 1)))
    res["motor_ends_station"] = ends
    return res


def base_fit(key):
    """Bounding box of the base (with L5's motor pads) against one H2D nozzle (325 x 320)."""
    shp = base_for(key)
    if key == "L5":
        hd = cached("hd", hinge_drive)
        for th in BEARINGS:
            shp = shp.fuse(hd["pad"].moved(C_loc(D.place(th, SP, 0.0))))
    bb = shp.BoundingBox()
    w, h = sorted((bb.xlen, bb.ylen), reverse=True)
    best = None
    for rot in range(0, 180, 2):          # the smallest box over rotations in the bed's plane
        s2 = shp.rotate(cq.Vector(0, 0, 0), cq.Vector(0, 0, 1), rot)
        b2 = s2.BoundingBox()
        a, c = sorted((b2.xlen, b2.ylen), reverse=True)
        if best is None or (a <= B.BED[0] and c <= B.BED[1] and not (best[0] <= B.BED[0] and best[1] <= B.BED[1])) \
                or (a * c < best[0] * best[1] and (a <= B.BED[0] and c <= B.BED[1]) == (best[0] <= B.BED[0] and best[1] <= B.BED[1])):
            best = (a, c, rot)
    return dict(xy=[round(w, 1), round(h, 1)], best_rotation=dict(box=[round(best[0], 1), round(best[1], 1)], deg=best[2]),
                fits_h2d=bool(best[0] <= B.BED[0] and best[1] <= B.BED[1]))


def footprint(key):
    """Feet: the radius of the outermost foot point from the beaker axis, and the feet's bounding box."""
    pts = [samples(p.shape, p.M, 4.0) for p in fixed_parts(key) if p.kind == "new"]
    P = np.vstack(pts)
    P = P[P[:, 2] < ZB + 7.0]
    return dict(r_max=round(float(np.hypot(P[:, 0], P[:, 1]).max()), 1),
                box=[round(float(np.ptp(P[:, 0])), 1), round(float(np.ptp(P[:, 1])), 1)])


def hr100a_fit(hang, legs):
    """The HR-100A (scale_room.py's model) on the bench, pan centre on the beaker axis, at every
    orientation: the closest approach to everything under the shelf (actuators at any tilt, legs)."""
    P, T = hang
    allP = np.vstack([rot3(P), legs]) if len(P) else legs
    res = {}
    for lid in (False, True):
        prims = SR.hr_prims(lid)
        rows = []
        for phi in range(0, 360, 5):
            d = SR.sdf(SR.to_balance(allP, phi, ZB), prims)
            rows.append((phi, float(d.min())))
        best = max(rows, key=lambda r: r[1])
        ok = [phi for phi, d in rows if d >= GAP]
        res["lid_on" if lid else "lid_off"] = dict(best_phi=best[0], best_mm=round(best[1], 1),
                                                   worst_mm=round(min(d for _, d in rows), 1),
                                                   phis_ok=ok, n_ok=len(ok),
                                                   shelf_gap=round(S - SR.hr_top(lid), 1))
    return res


def l5_wide():
    """L5 with its three posts moved out to L2's radius on the same outrigger arms (no tabs): the free
    diameter (the posts alone) and the HR-100A at every orientation."""
    yp = OPTIONS["L2"]["post_y"]
    sh = leg_post(yp, tab=None)
    legs = np.vstack([samples(sh, D.place(th, SP, 0.0), 2.0) for th in BEARINGS])
    legs = legs[legs[:, 2] < BOT]
    rows = room("L5", (np.zeros((0, 3)), np.zeros(0)), legs)
    sm = summary(rows)
    fp = legs[legs[:, 2] < ZB + 7.0]
    return dict(post_centre_from_beaker_axis=round(SP + yp, 1), summary=sm,
                feet_r_max=round(float(np.hypot(fp[:, 0], fp[:, 1]).max()), 1),
                hr100a=hr100a_fit((np.zeros((0, 3)), np.zeros(0)), legs))


# --------------------------------------------------------------------------- #
# figures
# --------------------------------------------------------------------------- #
COLS = {"L0": "#7f7f7f", "L1": "#9b59b6", "L2": "#e67e22", "L3": "#2e86c1", "L4": "#c0392b", "L5": "#16a085"}


def figure_profiles(res, fn):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, axs = plt.subplots(1, 2, figsize=(17.5, 8.2), dpi=110, gridspec_kw=dict(width_ratios=[1.25, 1]))
    ax = axs[0]
    draw = ["L1", "L2", "L3", "L4", "L5", "L0"]              # today last, so it stays on top
    for key in draw:
        rows = res["options"][key]["room"]
        d = np.array([(r["depth"][0] + r["depth"][1]) / 2 for r in rows])
        f = np.array([np.nan if r["free_r"] is None else 2 * r["free_r"] for r in rows])
        ax.step(f, d, where="mid", color=COLS[key], lw=2.0 if key == "L0" else 2.4, ls="-." if key == "L1" else "-",
                label=f"{key} {OPTIONS[key]['short']}", zorder=5 if key == "L0" else 3)
        if OPTIONS[key]["act"] is not None and key in ("L0", "L3"):
            f6 = np.array([np.nan if r["act_60"] is None else 2 * min(r["act_60"], r["legs"] or 1e9) for r in rows])
            ax.step(f6, d, where="mid", color=COLS[key], lw=1.4, ls="--", label=f"{key} with tilts kept to 60°")
    ax.axvline(186, color="#555", lw=0.9, ls=":")
    ax.text(189, 8, "HR-100A breeze break Ø186", fontsize=9, color="#333", rotation=90, va="top")
    ax.set_ylim(S, 0)
    ax.set_xlim(150, 520)
    ax.set_xlabel("free diameter about the beaker axis (mm): actuators at any tilt 0-90°, and the legs")
    ax.set_ylabel("depth below the shelf's underside (mm)")
    ax.set_title("Room under the shelf, by depth", loc="left", fontsize=13, fontweight="bold")
    ax.grid(alpha=0.3)
    h, l = ax.get_legend_handles_labels()
    order = sorted(range(len(l)), key=lambda i: l[i])
    ax.legend([h[i] for i in order], [l[i] for i in order], fontsize=9.5, loc="upper right")
    ax = axs[1]
    for key in draw:
        rows = res["options"][key]["room"]
        d = np.array([(r["depth"][0] + r["depth"][1]) / 2 for r in rows])
        f = np.array([np.nan if r["front_any"] is None else r["front_any"] for r in rows])
        ax.step(f, d, where="mid", color=COLS[key], lw=2.0 if key == "L0" else 2.4, ls="-." if key == "L1" else "-",
                label=f"{key} {OPTIONS[key]['short']}", zorder=5 if key == "L0" else 3)
    ax.axvline(198, color="#555", lw=0.9, ls=":")
    ax.text(201, 8, "HR-100A width 198", fontsize=9, color="#333", rotation=90, va="top")
    ax.set_ylim(S, 0)
    ax.set_xlim(150, 650)
    ax.set_xlabel("front opening (mm): widest thing, centred on the beaker axis,\nthat clears everything in front of the axis (any tilt)")
    ax.set_title("Width that slides in from the front", loc="left", fontsize=13, fontweight="bold")
    ax.grid(alpha=0.3)
    fig.suptitle(f"Shelf {S:.0f} mm above the bench; actuators checked at every tilt 0-90° in 5° steps", x=0.01, ha="left",
                 fontsize=10.5, color="#444")
    fig.tight_layout(rect=(0, 0, 1, 0.97))
    fig.savefig(fn)
    plt.close(fig)


def figure_plans(res, fn, mv, legs_all):
    """Plan of each option: what hangs under the shelf (actuators at 0 and 90 deg, legs), the free circle
    just under the shelf and 150 mm down, and the HR-100A at its best orientation (lid off)."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Circle, Polygon as MPoly
    face = B.shelf_outline_sketch()._faces.Faces()[0]
    ol = B._wire_xy(face.outerWire())
    fig, axs = plt.subplots(2, 3, figsize=(19.5, 13.6), dpi=100)
    for ax, key in zip(axs.ravel(), ORDER):
        ax.set_aspect("equal")
        ax.fill(ol[:, 0], ol[:, 1], color="#fbe3c8", zorder=1)
        ax.plot(ol[:, 0], ol[:, 1], color="#c46a1c", lw=1.0, zorder=2)
        P, T = mv[key]
        if len(P):
            A3 = rot3(P)
            T3 = np.tile(T, 3)
            for t, col in ((0, "#5b8bd9"), (90, "#c0392b")):
                m = T3 == t
                ax.scatter(A3[m, 0], A3[m, 1], s=0.3, color=col, zorder=5)
        L_ = legs_all[key]
        ax.scatter(L_[:, 0], L_[:, 1], s=0.3, color="#16a085", zorder=4)
        if key == "L5":                                       # the gearmotors sit above the shelf, in the gaps
            for p in fixed_parts(key):
                if p.kind == "drive" and not p.name.endswith("pad"):
                    q = samples(p.shape, p.M, 2.5)
                    ax.scatter(q[:, 0], q[:, 1], s=0.3, color="#333333", zorder=8)
        fit = res["options"][key]["hr100a"]["lid_off"]
        for poly in SR.plan_outline_station(fit["best_phi"], lid=False):
            ax.add_patch(MPoly(poly, closed=True, fc=(0.55, 0.55, 0.55, 0.22), ec="#444", lw=0.8, zorder=6))
        sm = res["options"][key]["summary"]
        for d, ls in (("15", "-"), ("105", "--")):
            v = sm[d]["free_dia_any"]
            if v:
                ax.add_patch(Circle((0, 0), v / 2, fill=False, ls=ls, color="k", lw=1.2, zorder=7))
        ax.annotate("front", xy=(0, -330), ha="center", fontsize=10, color="#555")
        ax.set_xlim(-345, 345)
        ax.set_ylim(-345, 345)
        ax.axis("off")
        ax.set_title(f"{key}  {OPTIONS[key]['title']}\nfree Ø{sm['15']['free_dia_any']} just under the shelf (solid), "
                     f"Ø{sm['105']['free_dia_any']} 100 mm down (dashed);\nHR-100A best {fit['best_mm']:+.0f} mm (lid off, "
                     f"{fit['n_ok']} of 72 orientations clear)", fontsize=10.5, loc="left")
    fig.text(0.01, 0.005, "blue: actuators parked (0°); red: at 90°; teal: legs, hangers, arms; dark grey (L5): the gearmotors, above the shelf; "
             "orange: the base; grey: the HR-100A "
             "(scale_room.py's model) turned for the most room, lid off.  Circles: free diameter at any tilt.",
             fontsize=10.5, color="#333")
    fig.tight_layout(rect=(0, 0.02, 1, 1))
    fig.savefig(fn)
    plt.close(fig)


def render_option(key, tilts, fn, title, sub):
    parts = []
    for i, th in enumerate(BEARINGS):
        parts += module_parts(key, tilts[i], D.place(th, SP, 0.0), "ABC"[i])
    for p in parts:
        if not hasattr(p, "colour") or p.colour is None:
            p.colour = K.STATUS["reuse"][2]
    b = part("base", base_for(key), np.eye(4), K.STATUS["new"][2])
    parts += [b] + fixed_parts(key) + [ST.bench(ZB, half=380.0)]
    ST.render_concept(f"lr{key}", parts, title, sub, fn, az=-62.0, el=18.0)
    return fn


def render_sheet(res, fn):
    from PIL import Image
    tiles = []
    for key in ORDER:
        f = OUT / f"_lr_{key}.png"
        o = res["options"][key]
        sm = o["summary"]
        render_option(key, (30, 60, 0), f, f"{key}  {OPTIONS[key]['title']}",
                      [f"free Ø{sm['15']['free_dia_any']} under the shelf, Ø{sm['105']['free_dia_any']} 100 mm down; "
                       f"feet within r {o['footprint']['r_max']:.0f}"])
        tiles.append(f)
    ims = [Image.open(p).convert("RGB") for p in tiles]
    w, h = ims[0].size
    w2, h2 = int(w * 0.62), int(h * 0.62)
    sheet = Image.new("RGB", (3 * w2 + 2 * 12, 2 * h2 + 12 + 70), "white")
    for i, im in enumerate(ims):
        sheet.paste(im.resize((w2, h2)), ((i % 3) * (w2 + 12), 70 + (i // 3) * (h2 + 12)))
    from PIL import ImageDraw
    d = ImageDraw.Draw(sheet)
    d.text((20, 16), f"Six ways to make room for the scale (shelf {S:.0f} mm up; modules at 30, 60 and 0°)",
           font=K.font(36, True), fill=(20, 20, 20))
    sheet.save(fn)
    for p in tiles:
        p.unlink()
    return fn


# --------------------------------------------------------------------------- #
# main
# --------------------------------------------------------------------------- #
def prepare():
    for key, opt in OPTIONS.items():
        if opt["act"] is None:
            continue
        o = fit_a(opt["act"]) if opt.get("fit_a") or MT.kinematics(opt["act"])["spare_at_90"] < 1.0 else dict(opt["act"])
        opt["act_fit"] = o
    # posts behind the actuators: 5 mm behind the farthest point of the P16, its bracket and the tail
    for key, opt in OPTIONS.items():
        if opt["legs"] != "post":
            continue
        ymax = -1e9
        for t in TILTS:
            for p in module_parts(key, t, np.eye(4), "A"):
                if not p.name.endswith(HANGING):
                    continue
                v = samples(p.shape, p.M, 3.0)
                v = v[v[:, 2] < BOT - 8.0]
                if len(v):
                    ymax = max(ymax, float(v[:, 1].max()))
        opt["post_y"] = round(ymax + 5.0 + 10.0, 1)


def main():
    OUT.mkdir(exist_ok=True)
    t0 = time.time()
    prepare()
    cache = Path("/tmp/leg_room_samples.npz")
    if "--figures-only" in sys.argv:
        res = json.loads((HERE / "leg_room.json").read_text())
        if cache.exists():
            z = np.load(cache)
            mv = {k: (z[f"{k}_P"], z[f"{k}_T"]) for k in ORDER}
            legs_all = {k: z[f"{k}_L"] for k in ORDER}
        else:
            mv = {k: hanging_samples(k) for k in ORDER}
            legs_all = {k: leg_samples(k) for k in ORDER}
        figure_profiles(res, OUT / "legroom_profiles.png")
        figure_plans(res, OUT / "legroom_plans.png", mv, legs_all)
        return
    res = dict(shelf_underside_above_bench=S, tilts=list(TILTS), band_mm=BAND, options={})
    mv, legs_all = {}, {}
    for key in ORDER:
        opt = OPTIONS[key]
        r = dict(title=opt["title"], change=opt["change"])
        if opt["act"] is not None:
            o = opt["act_fit"]
            k = MT.kinematics(o)
            r["actuator"] = dict(clevis_pin_behind_hinge=o["a"], actuator=o["act"], lean_deg=o["lean"], **{
                kk: k[kk] for kk in ("rod_out", "spare_at_90", "monotonic", "mm_per_deg", "max_force_N", "actuator_lean_deg",
                                     "base_pin_from_beaker_axis")},
                lean_at_0_45_90=[round(lean_at(o, t), 1) for t in (0, 45, 90)])
        if opt["legs"] == "post":
            r["post_centre_from_beaker_axis"] = round(SP + opt["post_y"], 1)
        if opt["act"] is not None:
            r["slot_ends_behind_hinge"] = slot_end(key)
        mv[key] = hanging_samples(key)
        legs_all[key] = leg_samples(key)
        r["room"] = room(key, mv[key], legs_all[key])
        r["summary"] = summary(r["room"])
        P = mv[key][0]
        r["hangs_below_shelf_mm"] = round(float(BOT - P[:, 2].min()), 1) if len(P) else 0.0
        r["footprint"] = footprint(key)
        r["hr100a"] = hr100a_fit(mv[key], legs_all[key])
        print(key, "room", r["summary"], "hangs", r["hangs_below_shelf_mm"], "feet", r["footprint"], flush=True)
        print("   HR-100A", {k: (v["best_phi"], v["best_mm"], v["n_ok"]) for k, v in r["hr100a"].items()},
              round(time.time() - t0), "s", flush=True)
        if "--no-checks" not in sys.argv:
            r["checks"] = checks(key)
            if key == "L5":
                r["base_bed"] = base_fit(key)
            print("   checks", r["checks"], r.get("base_bed"), round(time.time() - t0), "s", flush=True)
        res["options"][key] = r
    res["L5_posts_at_L2_radius"] = l5_wide()
    print("L5 wide", res["L5_posts_at_L2_radius"], flush=True)
    (HERE / "leg_room.json").write_text(json.dumps(res, indent=1, default=float) + "\n")
    np.savez_compressed(cache, **{f"{k}_P": mv[k][0] for k in ORDER}, **{f"{k}_T": mv[k][1] for k in ORDER},
                        **{f"{k}_L": legs_all[k] for k in ORDER})
    figure_profiles(res, OUT / "legroom_profiles.png")
    figure_plans(res, OUT / "legroom_plans.png", mv, legs_all)
    print("figures", round(time.time() - t0), "s", flush=True)
    if "--no-renders" not in sys.argv:
        render_sheet(res, OUT / "legroom_options.png")
        print("renders", round(time.time() - t0), "s", flush=True)


if __name__ == "__main__":
    main()
