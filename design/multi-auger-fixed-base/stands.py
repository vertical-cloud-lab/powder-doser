"""Stand options for the three-auger tri-star (B2 with #203's tap bracket), issue #204, 20 Nov.

Ethan asked for options for a stand for the tri-star.  The stand holds the one-piece base
(base.py) off the bench.  Every concept here keeps the actuators hanging from the shelf, as
components.py has them, so the stand only has to hold the shelf; the P16s move with it.

Four concepts, each with the doser at a working height and a vessel set-up:

* S1  printed tripod, fixed 217 mm: three printed A-frame legs.  Each one bolts to a lobe
      end's four hanger holes and also carries its actuator's U-bracket (it replaces the hanger);
* S2  telescoping tripod, 217-359 mm: a printed sleeve under each lobe end (it carries the
      U-bracket too) and a 20 x 20 mm aluminium square tube sliding in it, pinned every 10 mm;
* S3  fixed table on a board, 372 mm, plus a lab jack: three 2020 posts on a 12 mm board.  The
      doser stays put; a lab jack on the board brings each vessel up to it;
* S4  retort stand: a printed arm under two lobes clamps a standard 12.7 mm lab rod in the
      back-left gap between modules (or a fume hood's lattice rod).

For each one the script checks the stand against every moving part over 0-90 deg (2 mm
target), measures the front gap a stir plate or vessel can slide through, estimates the
centre of mass against the feet (how hard a sideways push at the shelf has to be to tip it),
and checks S2 set to 320 mm over the A&D HR-100A, for weighing while dosing.

    pip install cadquery trimesh python-fcl rtree vtk pillow numpy matplotlib scipy
    xvfb-run -a python stands.py        # about 3 min; writes stands.json and renders/stand_*.png

Frames: the station frame of doserlib.py (beaker axis = Z, hinge axes at z = 0, modules at
bearings 90 (back), 210 and 330 deg, so the front gap faces -Y, towards the user).  Every
stand part and the glassware, stir plate, lab jack and retort stand are placeholders.
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
import clearance as CL

HERE = Path(__file__).resolve().parent
OUT = HERE / "renders"
SP = B.SP                                  # 32 mm, hinge axis to beaker axis
BOT = D.BASE_BOT_U                         # shelf underside, -43.25
A = K.A                                    # rod-end pin 95 mm behind the hinge
UB_BASE = K.BASE_PIN_Z - K.UB["h"]         # U-bracket base, -256.1 (the base pin is at -247)
TAB = (UB_BASE - 4.0, UB_BASE)             # 4 mm tab under the U-bracket
S_MIN = 217.0                              # clearance.json: the shortest stand
BEARINGS = B.BEARINGS                      # 90, 210, 330
GAP = 2.0
HOLES = [(sx * B.PAD["x"], y) for sx in (1, -1) for y in B.PAD["y"]]   # the lobe ends' 4 hanger holes (M4)
OUTLET_90 = -D.OUTLET_AHEAD                # outlets at 90 deg, 11.6 below the hinge

# colours
PRINT = (0.16, 0.62, 0.56)                 # printed stand parts (teal)
ALU = (0.78, 0.80, 0.83)                   # aluminium tube / extrusion
STEEL = (0.36, 0.37, 0.40)                 # steel rod, cast iron base
BOARD = (0.93, 0.92, 0.86)                 # HDPE or plywood board
BENCH = (0.82, 0.80, 0.76)

# masses (estimates): printed parts at 60% of solid PLA; bought parts from their size
RHO_PRINT = 1.24 * 0.6e-3                  # g/mm^3
M_P16 = 95.0                               # g, Actuonix P16-150 (estimate)
M_NEMA = 110.0                             # g, NEMA 11 x 31 mm (estimate)
M_SOL = 40.0                               # g, Adafruit 412 (estimate)
M_POWDER = 50.0                            # g per auger, at its middle
M_STIR, M_JACK = 2000.0, 1500.0            # g, placeholder stir plate and 150 mm lab jack
ALU_TUBE = 0.30                            # g/mm, 20 x 20 x 1.5 mm square tube
ALU_2020 = 0.50                            # g/mm, 2020 extrusion
RHO_HDPE, RHO_IRON, RHO_STEEL = 0.95e-3, 7.2e-3, 7.85e-3


# --------------------------------------------------------------------------- #
# helpers
# --------------------------------------------------------------------------- #
def prism_yz(pts, x0, x1):
    """A polygon in the (y, z) plane, extruded from x = x0 to x1 (unit frame)."""
    return cq.Workplane("YZ", origin=(x0, 0, 0)).polyline(pts).close().extrude(x1 - x0).val()


def prism_xy(pts, z0, z1):
    return cq.Workplane("XY", origin=(0, 0, z0)).polyline(pts).close().extrude(z1 - z0).val()


def hull_pts(circles, n=24):
    """Convex hull (anticlockwise) of a few circles [(x, y, r)] in a plane."""
    from scipy.spatial import ConvexHull
    p = np.array([(x + r * math.cos(t), y + r * math.sin(t)) for x, y, r in circles
                  for t in np.linspace(0, 2 * math.pi, n, endpoint=False)])
    h = ConvexHull(p)
    return [tuple(p[i]) for i in h.vertices]


def bolt_holes(shape, z0, z1, d=4.5):
    for x, y in HOLES:
        shape = shape.cut(D.cyl(d / 2, z1 - z0 + 2, x, y, z0 - 1))
    return shape


def flange(y0=112.0, y1=140.0, half=20.0, t=6.0):
    """Flange under a lobe end, bolted through the 4 hanger holes (unit frame)."""
    return bolt_holes(D.box(-half, half, y0, y1, BOT - t, BOT), BOT - t, BOT)


def place_all(shape_fn, name, colour, kind="print"):
    out = []
    for i, th in enumerate(BEARINGS):
        p = D.Part(f"{name} {'ABC'[i]}", shape_fn(), D.place(th, SP, 0.0), colour, "stand", False)
        p.kind = kind
        out.append(p)
    return out


_S: dict = {}


def cached(k, fn):
    if k not in _S:
        _S[k] = fn()
    return _S[k]


# --------------------------------------------------------------------------- #
# the doser (modules on the one-piece base), with the U-brackets and their pins
# --------------------------------------------------------------------------- #
def doser(tilts, hangers=False):
    parts = []
    plate = B.plate_trimmed()
    for i, th in enumerate(BEARINGS):
        M = D.place(th, SP, 0.0)
        for p in K.module(float(tilts[i]), M, "ABC"[i], with_hanger=hangers):
            if p.kind == "tower":
                continue
            if p.name.endswith("Mounting plate"):
                p.shape = plate
            parts.append(p)
    b = D.Part("base", B.base_station(), np.eye(4), K.STATUS["new"][2], "fixed", False)
    b.kind, b.status = "base", "new"
    parts.append(b)
    for p in parts:
        if p.kind != "base":
            p.colour = K.STATUS[p.status][2]
    return parts


# --------------------------------------------------------------------------- #
# S1: printed tripod, fixed 217 mm
# --------------------------------------------------------------------------- #
S1 = dict(height=S_MIN, half=12.0, inner=(128.0, 140.0), splay_deg=15.0, strut=14.0, tie=10.0)


def s1_leg():
    """One printed A-frame leg (unit frame): a flange under the lobe end, an inner upright
    (the hanger, 7.5 mm behind the P16's housing, as today), a strut splayed 15 deg outward and a
    tie along the bench.  Its front end is the tab the P16's U-bracket screws to."""
    S = S1["height"]
    zb = BOT - S
    h = S1["half"]
    y0, y1 = S1["inner"]
    zt = BOT - 6.0
    run = (zt - zb) * math.tan(math.radians(S1["splay_deg"]))
    yo_top = y1 + 8.0
    yo_bot = yo_top + run
    pts = [(y0, zt), (yo_top, zt), (yo_bot, zb), (A - 8.0, zb), (A - 8.0, TAB[1]), (y0, TAB[1])]
    leg = prism_yz(pts, -h, h)
    # lightening window: inside the upright, the strut and the tie
    ins = S1["strut"]
    yi_top, yi_bot = yo_top - ins, yo_bot - ins
    ztie = zb + S1["tie"]

    def strut_y(z):                       # y of the strut's inner edge at height z
        return yi_top + (yi_bot - yi_top) * (zt - z) / (zt - zb)
    za = zt - 14.0
    hole = [(y1, za), (y1, ztie), (strut_y(ztie), ztie), (strut_y(za), za)]
    leg = leg.cut(prism_yz(hole, -h - 1, h + 1))
    leg = leg.fuse(flange(112.0, 140.0, 20.0)).clean()
    return bolt_holes(leg, zt - 1, BOT)


def s1_parts():
    return place_all(lambda: cached("s1", s1_leg), "S1 leg", PRINT)


# --------------------------------------------------------------------------- #
# S2: telescoping tripod, 217-358 mm
# --------------------------------------------------------------------------- #
S2 = dict(sleeve=(34.0, (128.0, 164.0)), bore=20.6, post=20.0, post_y=(136.0, 156.0), foot_h=6.0,
          foot=dict(half=15.0, y=(136.0, 215.0)), pitch=10.0, min_overlap=60.0)
S2["sleeve_bot"] = BOT - S_MIN + S2["foot_h"] + 2.0      # -252.25: 2 mm over the foot at the lowest setting
S2["post_len"] = (BOT - 7.0) - (BOT - S_MIN + S2["foot_h"])   # 204: 1 mm under the flange at 217 mm
S2["range"] = (S_MIN, S_MIN + S2["post_len"] - 2.0 - S2["min_overlap"])   # 217..359: 60 mm of post stays in


def s2_sleeve():
    """Printed sleeve + flange + U-bracket tab, one part (unit frame)."""
    w, (y0, y1) = S2["sleeve"]
    zt = BOT - 6.0
    sl = D.box(-w / 2, w / 2, y0, y1, S2["sleeve_bot"], zt)
    b = S2["bore"] / 2
    pc = sum(S2["post_y"]) / 2
    sl = sl.cut(D.box(-b, b, pc - b, pc + b, S2["sleeve_bot"] - 1, zt - 0.01))
    fl = flange(112.0, y1, 20.0)
    web = D.box(-12.0, 12.0, y0, y0 + 6.0, TAB[0], S2["sleeve_bot"] + 20.0)
    tab = D.box(-12.0, 12.0, A - 8.0, y0 + 6.0, TAB[0], TAB[1])
    part = sl.fuse(fl).fuse(web).fuse(tab).clean()
    # the pin hole (M5) through the sleeve, 20 mm above its bottom
    part = part.cut(D.cyl(2.7, 60, -30, pc, S2["sleeve_bot"] + 20.0, d=(1, 0, 0)))
    return bolt_holes(part, zt - 1, BOT)


def s2_post(S):
    """20 x 20 mm aluminium square tube on a printed long-toed foot, for stand height S."""
    zb = BOT - S
    p0, p1 = S2["post_y"]
    h = S2["post"] / 2
    post = D.box(-h, h, p0, p1, zb + S2["foot_h"], zb + S2["foot_h"] + S2["post_len"])
    post = post.cut(D.box(-h + 1.5, h - 1.5, p0 + 1.5, p1 - 1.5, zb, zb + 400))
    return post


def s2_foot(S):
    """Printed long-toed foot: a 6 mm pad reaching out under the post (an M5 screw holds the post)."""
    zb = BOT - S
    f = S2["foot"]
    return D.box(-f["half"], f["half"], f["y"][0], f["y"][1], zb, zb + S2["foot_h"])


def s2_pin(S):
    """M5 bolt through the sleeve and the post at the hole nearest the sleeve's bottom."""
    pc = sum(S2["post_y"]) / 2
    z = S2["sleeve_bot"] + 20.0
    return D.cyl(2.5, 44, -22, pc, z, d=(1, 0, 0)).fuse(D.cyl(4.5, 4, 18, pc, z, d=(1, 0, 0)))


def s2_parts(S):
    out = place_all(lambda: cached("s2", s2_sleeve), "S2 sleeve", PRINT)
    out += place_all(lambda: cached(f"s2p{S}", lambda: s2_post(S)), "S2 post", ALU, "alu")
    out += place_all(lambda: cached(f"s2f{S}", lambda: s2_foot(S)), "S2 foot", PRINT)
    out += place_all(lambda: cached("s2pin", lambda: s2_pin(S)), "S2 pin", STEEL, "hw")
    return out


# --------------------------------------------------------------------------- #
# S3: fixed table on a board (2020 posts) + lab jack
# --------------------------------------------------------------------------- #
S3 = dict(height=372.0, board=dict(x=(-195.0, 195.0), y=(-160.0, 210.0), t=12.0), post_y=(128.0, 148.0),
          jack=dict(w=150.0, plate=6.0))


def s3_cap():
    """Printed cap on each post's top: the flange through the 4 hanger holes and a socket for the 2020."""
    y0, y1 = S3["post_y"]
    cap = flange(112.0, y1 + 6.0, 20.0).fuse(D.box(-14.0, 14.0, y0 - 4.0, y1 + 4.0, BOT - 26.0, BOT - 6.0))
    cap = cap.cut(D.box(-10.2, 10.2, y0 - 0.2, y1 + 0.2, BOT - 27.0, BOT - 6.0))
    return bolt_holes(cap, BOT - 7.0, BOT)


def s3_post():
    zb = BOT - S3["height"]
    y0, y1 = S3["post_y"]
    return D.box(-10.0, 10.0, y0, y1, zb + S3["board"]["t"], BOT - 6.0)


def s3_collar():
    """Printed collar clamped round the post (T-nuts) at the U-bracket's height, with the tab."""
    y0, y1 = S3["post_y"]
    col = D.box(-14.0, 14.0, y0 - 4.0, y1 + 4.0, TAB[0] - 12.0, TAB[1])
    col = col.cut(D.box(-10.2, 10.2, y0 - 0.2, y1 + 0.2, TAB[0] - 20.0, TAB[1] + 5.0))
    return col.fuse(D.box(-12.0, 12.0, A - 8.0, y0 - 4.0, TAB[0], TAB[1])).clean()


def s3_gusset():
    """Printed corner gusset at each post's foot, on its outer side."""
    zb = BOT - S3["height"] + S3["board"]["t"]
    y1 = S3["post_y"][1]
    return prism_yz([(y1, zb), (y1 + 45.0, zb), (y1, zb + 45.0)], -10.0, 10.0).fuse(
        D.box(-10.0, 10.0, y1, y1 + 45.0, zb, zb + 4.0))


def s3_board():
    zb = BOT - S3["height"]
    b = S3["board"]
    pts = [(b["x"][0], b["y"][0]), (b["x"][1], b["y"][0]), (b["x"][1], b["y"][1]), (b["x"][0], b["y"][1])]
    sk = cq.Sketch().polygon(pts + [pts[0]]).vertices().fillet(15.0)
    return cq.Workplane("XY", origin=(0, 0, zb)).placeSketch(sk).extrude(b["t"]).val()


def lab_jack(z0, z1, w=150.0, t=6.0):
    """A 150 x 150 mm scissor lab jack between z0 (its base) and z1 (its top) (placeholder)."""
    base = D.box(-w / 2, w / 2, -w / 2, w / 2, z0, z0 + t)
    top = D.box(-w / 2, w / 2, -w / 2, w / 2, z1 - t, z1)
    out = base.fuse(top)
    h = (z1 - t) - (z0 + t)
    ln = math.hypot(w - 30, h)
    ang = math.degrees(math.atan2(h, w - 30))
    for sx in (1, -1):
        for sgn in (1, -1):
            bar = D.box(-4.0, 4.0, -ln / 2, ln / 2, -3.0, 3.0)
            bar = bar.rotate((0, 0, 0), (1, 0, 0), sgn * ang)
            bar = bar.translate((sx * (w / 2 - 12), 0, (z0 + z1) / 2))
            out = out.fuse(bar)
        out = out.fuse(D.cyl(4.0, w - 10, -(w - 10) / 2, 0, (z0 + z1) / 2, d=(1, 0, 0)))
    return out


def s3_parts():
    out = place_all(lambda: cached("s3cap", s3_cap), "S3 post cap", PRINT)
    out += place_all(lambda: cached("s3post", s3_post), "S3 post", ALU, "alu")
    out += place_all(lambda: cached("s3col", s3_collar), "S3 collar", PRINT)
    out += place_all(lambda: cached("s3gus", s3_gusset), "S3 gusset", PRINT)
    bd = D.Part("S3 board", cached("s3board", s3_board), np.eye(4), BOARD, "stand", False)
    bd.kind = "board"
    return out + [bd]


# --------------------------------------------------------------------------- #
# S4: retort stand (or hood lattice) clamp
# --------------------------------------------------------------------------- #
S4 = dict(rod_r=12.7 / 2, rod_at=(150.0, 140.0), rod_len=650.0, base=(280.0, 180.0, 15.0), base_behind=35.0,
          arm_t=10.0, sleeve=(15.0, 70.0), lobe_pts=((-30.0, 70.0), (30.0, 70.0)), strut_r=9.0, base_mass=3000.0)


def s4_rod_xy():
    th, r = S4["rod_at"]
    return r * math.cos(math.radians(th)), r * math.sin(math.radians(th))


def s4_arm_points():
    """The arm's two bolt points: one on each lobe either side of the back-left gap (station xy)."""
    (xa, ya), (xb, yb) = S4["lobe_pts"]
    pa = D.place(90.0, SP, 0.0) @ np.array([xa, ya, 0.0, 1.0])
    pb = D.place(210.0, SP, 0.0) @ np.array([xb, yb, 0.0, 1.0])
    return (pa[0], pa[1]), (pb[0], pb[1])


def s4_arm():
    rx, ry = s4_rod_xy()
    pa, pb = s4_arm_points()
    r_s, h_s = S4["sleeve"]
    rs = S4["strut_r"]
    arm = None
    for p in (pa, pb):          # two struts (a V), so the arm stays outside the clear column under the shelf
        st = prism_xy(hull_pts([(p[0], p[1], rs), (rx, ry, r_s)]), BOT - S4["arm_t"], BOT)
        arm = st if arm is None else arm.fuse(st)
    arm = arm.fuse(D.cyl(r_s, h_s, rx, ry, BOT - h_s))
    arm = arm.cut(D.cyl(S4["rod_r"] + 0.2, h_s + 2, rx, ry, BOT - h_s - 1))
    for p in (pa, pb):
        arm = arm.cut(D.cyl(2.25, 20, p[0], p[1], BOT - 15))
    # two M5 pinch screws across a slit
    return arm.clean()


def s4_stand(S):
    zb = BOT - S
    rx, ry = s4_rod_xy()
    L, W, t = S4["base"]
    # base plate: from 35 mm behind the rod, along the line through the beaker axis
    u = np.array([-rx, -ry]) / math.hypot(rx, ry)          # towards the axis
    v = np.array([-u[1], u[0]])
    c = np.array([rx, ry]) + u * (L / 2 - S4["base_behind"])
    pts = [tuple(c + u * a * L / 2 + v * b * W / 2) for a, b in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
    base = prism_xy(pts, zb, zb + t)
    rod = D.cyl(S4["rod_r"], S4["rod_len"], rx, ry, zb + t)
    return base, rod


def s4_hanger():
    """Hanger under each lobe end for S4 (its arm doesn't hold the P16s): the flange through the 4 hanger
    holes, an upright 7.5 mm behind the P16's housing and the tab under its U-bracket (S1's leg without
    its strut and tie)."""
    h = D.box(-12.0, 12.0, 128.0, 140.0, TAB[0], BOT - 6.0).fuse(D.box(-12.0, 12.0, A - 8.0, 128.0, TAB[0], TAB[1]))
    return bolt_holes(h.fuse(flange(112.0, 140.0, 20.0)).clean(), BOT - 7.0, BOT)


def s4_parts(S):
    base, rod = s4_stand(S)
    arm = D.Part("S4 arm", cached("s4arm", s4_arm), np.eye(4), PRINT, "stand", False)
    arm.kind = "print"
    b = D.Part("S4 retort base", base, np.eye(4), STEEL, "stand", False)
    b.kind = "iron"
    r = D.Part("S4 rod", rod, np.eye(4), STEEL, "stand", False)
    r.kind = "rod"
    return [arm, b, r] + place_all(lambda: cached("s4hang", s4_hanger), "S4 hanger", PRINT)


# --------------------------------------------------------------------------- #
# vessels and the HR-100A
# --------------------------------------------------------------------------- #
def bench(zb, half=420.0):
    p = D.Part("bench", D.box(-half, half, -half, half, zb - 12.0, zb), np.eye(4), BENCH, "bench", False)
    p.kind = "bench"
    return p


def stir_plate(z_top, rot=0.0):
    w, h = CL.STIR["w"], CL.STIR["h"]
    body = D.box(-w / 2, w / 2, -w / 2, w / 2, z_top - h, z_top - 3)
    top = D.cyl(CL.STIR["top"] / 2, 3.0, 0, 0, z_top - 3)
    out = [D.Part("stir plate", body, D.Rz(rot), (0.30, 0.31, 0.34), "vessel"),
           D.Part("stir plate top", top, np.eye(4), (0.92, 0.92, 0.92), "vessel")]
    for p in out:
        p.kind = "vessel"
    return out


def vessel_parts(kind, z_floor, rim_or_mouth=None, riser=0.0, stir=True, jack_top=None, riser_r=45.0):
    """Stir plate (+ riser) + glassware standing on z_floor (or on a lab jack whose top is at jack_top)."""
    out = []
    z = z_floor
    if jack_top is not None:
        jk = D.Part("lab jack", lab_jack(z_floor, jack_top), np.eye(4), (0.70, 0.71, 0.74), "vessel")
        jk.kind = "vessel"
        out.append(jk)
        z = jack_top
    if stir:
        out += stir_plate(z + CL.STIR["h"], rot=0.0)
        z += CL.STIR["h"]
    if riser > 0.05:
        rs = D.Part("riser", D.cyl(riser_r, riser, 0, 0, z), np.eye(4), (0.70, 0.72, 0.76), "vessel")
        rs.kind = "vessel"
        out.append(rs)
        z += riser
    if kind in C.BEAKERS:
        d, h = C.BEAKERS[kind]
        bk = D.Part(f"beaker {kind}", D.beaker(d, h), D.Tt(0, 0, z), D.COL["glass"], "vessel", False, 0.45)
        bk.kind = "vessel"
        out.append(bk)
    else:
        db, hb, dn = CL.ERLENMEYER[kind]
        fl = D.Part("flask", CL.erlenmeyer(db, hb, dn), D.Tt(0, 0, z), D.COL["glass"], "vessel", False, 0.45)
        seat = CL.FUNNEL["stem_len"] + (dn / 2 - CL.NECK_WALL - CL.FUNNEL["stem"] / 2) / math.tan(math.radians(30.0))
        fu = D.Part("funnel", CL.funnel(), D.Tt(0, 0, z + hb - seat), (0.55, 0.75, 0.90), "vessel", False, 0.75)
        fl.kind = fu.kind = "vessel"
        out += [fl, fu]
    return out


def balance_parts(zb):
    body, glass = D.hr100a()
    b = D.Part("HR-100A", body, D.Tt(0, 0, zb), D.COL["balance"], "balance")
    g = D.Part("HR-100A glass", glass, D.Tt(0, 0, zb), D.COL["glass"], "balance", False, 0.35)
    b.kind = g.kind = "balance"
    return [b, g]


# --------------------------------------------------------------------------- #
# checks
# --------------------------------------------------------------------------- #
CASES = B.CASES


def _objs(parts):
    import fcl
    return [(p, fcl.CollisionObject(D._bvh(p.shape), fcl.Transform(p.M[:3, :3], p.M[:3, 3]))) for p in parts]


def _dist(oa, ob):
    import fcl
    return fcl.distance(oa, ob, fcl.DistanceRequest(enable_nearest_points=False), fcl.DistanceResult())


MOUNTED_ON = ("P16 bracket", "#8-32 pin")       # screwed to the stand's tab: contact by design


def stand_vs_doser(stand, units="A", tilts=range(0, 91, 5), extra=()):
    """Closest approach of the stand (and ``extra`` fixed things, e.g. the balance) to every part of
    the doser that moves, and to the actuators, over 0..90 deg, one module at a time (the stand is
    fixed, so this covers every tilt mix).  The U-bracket and its pin sit on the stand's tab."""
    so = _objs(list(stand) + list(extra))
    worst = (1e9, None, None, None)
    for u in units:
        i = "ABC".index(u)
        for t in tilts:
            tl = [0, 0, 0]
            tl[i] = t
            ps = [p for p in doser(tl) if p.name.startswith(u + ":")]
            for p, op in _objs(ps):
                if p.name.endswith(MOUNTED_ON):
                    continue
                for q, oq in so:
                    d = _dist(op, oq)
                    if d < worst[0]:
                        worst = (d, p.name, q.name, t)
    return dict(mm=round(worst[0], 2), between=f"{worst[1]} / {worst[2]}", at_tilt=worst[3])


def obstacle_points(stand, tilts=range(0, 91, 10)):
    """Surface samples of the stand and of everything that hangs under the shelf (the P16s, rods,
    U-brackets), at ``tilts`` (all three modules together): what a vessel sliding in from the front
    has to miss.  Returns (points, part name per point)."""
    pts, names = [], []

    def add(p):
        v = CL._samples(p.shape)
        pts.append((p.M[:3, :3] @ v.T).T + p.M[:3, 3])
        nm = p.name.split(":", 1)[-1]
        names.extend([nm.rsplit(" ", 1)[0] if nm[-2:] in (" A", " B", " C") else nm] * len(v))
    for p in stand:
        add(p)
    for t in tilts:
        for p in doser((t, t, t)):
            if p.kind in ("p16", "ubracket") or p.name.endswith(("#8-32 pin", "clevis block", "M4 pin")):
                add(p)
    return np.vstack(pts), np.array(names)


def front_gate(ob, z_floor, z_top):
    """Widest square object (W x W) that slides in from the front (-Y) to the beaker axis between
    z_floor and z_top: W/2 = min over obstacle points of max(|x|, y).  Returns (W, what limits it)."""
    pts, names = ob
    sel = (pts[:, 2] > z_floor + 0.5) & (pts[:, 2] < z_top)
    if not sel.any():
        return None, None
    q = np.maximum(np.abs(pts[sel, 0]), pts[sel, 1])
    i = int(np.argmin(q))
    return round(2.0 * float(q[i]), 1), str(names[sel][i])


def column_r(ob, z_floor, z_top):
    pts, names = ob
    sel = (pts[:, 2] > z_floor + 0.5) & (pts[:, 2] < z_top)
    r = np.hypot(pts[sel, 0], pts[sel, 1])
    i = int(np.argmin(r))
    return round(float(r[i]), 1), str(names[sel][i])


def vessel_check(stand, ves, units="ABC", tilts=range(0, 91, 10), extra=(), rests_on=()):
    """The vessel set-up shown in a figure against the stand and against every module over 0..90 deg
    (one module at a time).  ``rests_on``: (vessel part, stand part) pairs that touch by design."""
    vo = _objs([v for v in ves])
    so = _objs(list(stand) + list(extra))
    best = (1e9, None, None, None)
    for p, op in vo:
        for q, oq in so:
            if (p.name, q.name) in rests_on:
                continue
            d = _dist(op, oq)
            if d < best[0]:
                best = (d, p.name, q.name, None)
    for u in units:
        i = "ABC".index(u)
        for t in tilts:
            tl = [0, 0, 0]
            tl[i] = t
            for q, oq in _objs([x for x in doser(tl) if x.name.startswith(u + ":")]):
                for p, op in vo:
                    d = _dist(op, oq)
                    if d < best[0]:
                        best = (d, p.name, q.name, t)
    return dict(mm=round(best[0], 2), between=f"{best[1]} / {best[2]}", at_tilt=best[3])


def _mass_part(p, rho=None, mass=None):
    sh = p.shape
    c = sh.Center()
    c = (p.M @ np.array([c.x, c.y, c.z, 1.0]))[:3]
    if mass is None:
        mass = sh.Volume() * rho
    return mass, c


def masses(parts):
    """Mass and centre of each part (grams, station mm).  Printed parts at 60% of solid PLA; the
    P16, NEMA 11 and solenoid from estimates; aluminium by length; powder at each auger's middle."""
    out = []
    for p in parts:
        k = getattr(p, "kind", "")
        n = p.name
        if k in ("bench", "vessel", "balance"):
            continue
        if n.endswith("P16 body"):
            out.append(_mass_part(p, mass=M_P16 * 0.85))
        elif n.endswith("P16 rod"):
            out.append(_mass_part(p, mass=M_P16 * 0.15))
        elif n.endswith("Stepper (NEMA 11)"):
            out.append(_mass_part(p, mass=M_NEMA))
        elif n.endswith("Solenoid coil"):
            out.append(_mass_part(p, mass=M_SOL))
        elif "Solenoid" in n or n.endswith(("M3 screws", "M4 pin", "#8-32 pin", "P16 bracket")) or k == "hw":
            continue
        elif k == "alu":
            bb = p.shape.BoundingBox()
            out.append(_mass_part(p, mass=max(bb.xlen, bb.ylen, bb.zlen) * (ALU_TUBE if "S2" in n else ALU_2020)))
        elif k == "board":
            out.append(_mass_part(p, rho=RHO_HDPE))
        elif k == "iron":
            out.append(_mass_part(p, mass=S4["base_mass"]))
        elif k == "rod":
            out.append(_mass_part(p, rho=RHO_STEEL))
        else:
            out.append(_mass_part(p, rho=RHO_PRINT))
            if n.endswith(":Auger"):
                out.append(_mass_part(p, mass=M_POWDER))
    return out


def support_polygon(stand, zb):
    """Convex hull (xy) of every stand surface within 1 mm of the bench."""
    from scipy.spatial import ConvexHull
    pts = []
    for p in stand:
        m = D.mesh_of(p.shape)
        v = (p.M[:3, :3] @ np.asarray(m.vertices).T).T + p.M[:3, 3]
        pts.append(v[v[:, 2] < zb + 1.0][:, :2])
    pts = np.vstack(pts)
    h = ConvexHull(pts)
    return pts[h.vertices]


def edge_margin(poly, c):
    """Smallest distance from point c (inside) to the polygon's edges."""
    best = 1e9
    n = len(poly)
    for i in range(n):
        a, b = poly[i], poly[(i + 1) % n]
        ab = b - a
        t = np.clip(np.dot(c - a, ab) / np.dot(ab, ab), 0, 1)
        best = min(best, float(np.linalg.norm(c - (a + t * ab))))
    from matplotlib.path import Path as MPath
    return best if MPath(poly).contains_point(c) else -best


def stability(stand, zb, extra_on_base=()):
    """Centre of mass of doser + stand (+ things standing on the stand's own base) against the feet,
    over the B2T tilt cases.  Returns the worst margin and the sideways push at the shelf's top that
    would tip it there."""
    poly = support_polygon(stand, zb)
    sm = masses(stand)
    worst = None
    for c in CASES:
        ms = masses(doser(c)) + sm + list(extra_on_base)
        m = sum(x[0] for x in ms)
        cg = sum(x[0] * x[1] for x in ms) / m
        mg = edge_margin(poly, cg[:2])
        if worst is None or mg < worst["margin_mm"]:
            h_cg = cg[2] - zb
            h_push = (D.BASE_TOP_U - zb)
            worst = dict(case=",".join(map(str, c)), mass_kg=round(m / 1000, 2), cg_height_mm=round(h_cg, 1),
                         cg_offset_mm=[round(float(cg[0]), 1), round(float(cg[1]), 1)], margin_mm=round(mg, 1),
                         tip_angle_deg=round(math.degrees(math.atan2(mg, h_cg)), 1),
                         push_at_shelf_N=round(m / 1000 * 9.81 * mg / h_push, 1))
    worst["feet_polygon"] = [[round(float(x), 1), round(float(y), 1)] for x, y in poly]
    return worst


def footprint(stand, zb):
    poly = support_polygon(stand, zb)
    return [round(float(np.ptp(poly[:, 0])), 0), round(float(np.ptp(poly[:, 1])), 0)]


def printed(stand):
    """Printed parts: count, size, solid volume."""
    rows = {}
    for p in stand:
        if getattr(p, "kind", "") != "print":
            continue
        key = p.name.rsplit(" ", 1)[0] if p.name[-2:] in (" A", " B", " C") else p.name
        bb = p.shape.BoundingBox()
        r = rows.setdefault(key, dict(qty=0, size_mm=sorted([round(bb.xlen), round(bb.ylen), round(bb.zlen)], reverse=True),
                                      volume_cm3=round(p.shape.Volume() / 1000, 1)))
        r["qty"] += 1
    for r in rows.values():
        r["grams_each_est"] = round(r["volume_cm3"] * 1000 * RHO_PRINT)
        a, b, c = r["size_mm"]
        r["fits_h2d"] = bool(a <= 325 and b <= 320 and c <= 325)
    return rows


# --------------------------------------------------------------------------- #
# figures
# --------------------------------------------------------------------------- #
def iso(parts, fn, size=(1300, 1150), az=-62.0, el=20.0, dist=1.3, focal=None):
    pts = []
    for p in parts:
        if getattr(p, "kind", "") == "bench":
            continue
        m = D.mesh_of(p.shape)
        pts.append((p.M[:3, :3] @ np.asarray(m.vertices).T).T + p.M[:3, 3])
    v = np.vstack(pts)
    c = (v.max(0) + v.min(0)) / 2 if focal is None else np.asarray(focal)
    a_, e_ = math.radians(az), math.radians(el)
    d = np.array([math.cos(e_) * math.cos(a_), math.cos(e_) * math.sin(a_), math.sin(e_)])
    up = np.array([0, 0, 1.0]) - d * d[2]
    up /= np.linalg.norm(up)
    rt = np.cross(up, d)
    w = (v - c) @ rt
    h = (v - c) @ up
    scale = max((h.max() - h.min()) / 2, (w.max() - w.min()) / 2 * size[1] / size[0]) * dist
    foc = c + up * (h.max() + h.min()) / 2 + rt * (w.max() + w.min()) / 2
    return D.render(parts, fn, az=az, el=el, size=size, parallel=True, dist=scale, focal=tuple(foc), fixed=True)


def label(img, lines, x=24, y=20, sz=30):
    from PIL import ImageDraw
    d = ImageDraw.Draw(img)
    for i, (t, bold) in enumerate(lines):
        f = K.font(sz if i == 0 else sz - 6, bold)
        d.text((x, y), t, font=f, fill=(25, 25, 25) if i == 0 else (60, 60, 60))
        y += (sz + 12) if i == 0 else (sz + 2)
    return img


def legend_row(img, items, x=24, y=None, sz=24):
    from PIL import ImageDraw
    d = ImageDraw.Draw(img)
    y = img.height - sz - 24 if y is None else y
    f = K.font(sz)
    for name, col in items:
        d.rectangle([x, y, x + sz, y + sz], fill=tuple(int(255 * c) for c in col), outline=(40, 40, 40))
        d.text((x + sz + 8, y - 2), name, font=f, fill=(40, 40, 40))
        x += sz + 8 + d.textlength(name, font=f) + 30
    return img


LEGEND = [("stand, printed", PRINT), ("aluminium", ALU), ("steel / iron", STEEL), ("board", BOARD),
          ("base", K.STATUS["new"][2]), ("P16", K.STATUS["buy"][2])]


def render_concept(key, parts, title, sub, fn, az=-62.0, el=20.0, dist=1.08):
    from PIL import Image
    tmp = OUT / f"_{key}.png"
    iso(parts, tmp, az=az, el=el, dist=dist)
    im = Image.open(tmp).convert("RGB")
    tmp.unlink()
    band = 46 + 32 * len(sub) + 10
    out = Image.new("RGB", (im.width, im.height + band), "white")
    out.paste(im, (0, band))
    label(out, [(title, True)] + [(s, False) for s in sub])
    out.save(fn)
    return fn


def sheet(paths, out, title, lines, cols=2):
    from PIL import Image, ImageDraw
    ims = [Image.open(p).convert("RGB") for p in paths]
    w, h = ims[0].size
    rows = math.ceil(len(ims) / cols)
    cap = 40 + 36 * len(lines) + 50
    S = Image.new("RGB", (cols * w + (cols - 1) * 16, 80 + rows * h + (rows - 1) * 16 + cap), "white")
    for i, im in enumerate(ims):
        S.paste(im.resize((w, h)), ((i % cols) * (w + 16), 80 + (i // cols) * (h + 16)))
    d = ImageDraw.Draw(S)
    d.text((24, 18), title, font=K.font(40, True), fill=(20, 20, 20))
    y = 80 + rows * h + (rows - 1) * 16 + 20
    for ln in lines:
        d.text((24, y), ln, font=K.font(26), fill=(60, 60, 60))
        y += 36
    legend_row(S, LEGEND, y=y + 10, sz=26)
    S.save(out)


def plan_figure(res, fn):
    """Plan of the four stands' feet (and S3's board) under the doser's outline at 0 deg."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Polygon as MPoly, Circle
    fig, axs = plt.subplots(1, 4, figsize=(24, 7.2), dpi=110)
    face = B.shelf_outline_sketch()._faces.Faces()[0]
    ol = B._wire_xy(face.outerWire())
    reach = res["doser_reach_mm"]
    for ax, key in zip(axs, ("S1", "S2", "S3", "S4")):
        r = res[key]
        ax.set_aspect("equal")
        ax.add_patch(Circle((0, 0), reach, fill=False, ls="--", lw=0.8, color="#888"))
        ax.fill(ol[:, 0], ol[:, 1], color="#fbe3c8", zorder=1)
        ax.plot(ol[:, 0], ol[:, 1], color="#c46a1c", lw=1.0, zorder=2)
        poly = np.array(r["stability"]["feet_polygon"])
        ax.add_patch(MPoly(poly, closed=True, fill=True, fc=(0.16, 0.62, 0.56, 0.18), ec=PRINT, lw=1.6, zorder=3))
        cg = r["stability"]["cg_offset_mm"]
        ax.plot(*cg, "x", color="k", ms=9, mew=2, zorder=5)
        ax.add_patch(Circle((0, 0), r["front_gate_mm"]["any_tilt"]["column_dia"] / 2, fill=False, color="#3060c0", lw=1.0,
                            zorder=4))
        g = r["front_gate_mm"]["parked_0deg"]["up_to_shelf"]
        ax.plot([-g / 2, -g / 2], [-330, 0], color="#3060c0", lw=0.8, ls=":")
        ax.plot([g / 2, g / 2], [-330, 0], color="#3060c0", lw=0.8, ls=":")
        ax.annotate("", xy=(0, -40), xytext=(0, -300), arrowprops=dict(arrowstyle="-|>", color="#3060c0", lw=1.2))
        ax.text(0, -318, f"front gap {g:.0f} mm (modules at 0°)", ha="center", fontsize=10, color="#3060c0")
        ax.set_title(f"{key}: {res[key]['name']}", fontsize=12, loc="left", fontweight="bold")
        st = r["stability"]
        ax.text(-300, 300, f"feet {r['footprint_mm'][0]:.0f} x {r['footprint_mm'][1]:.0f} mm\n"
                f"CG {st['margin_mm']:.0f} mm inside the feet\n(worst tilt mix {st['case']})", fontsize=9.5, va="top")
        ax.set_xlim(-310, 310)
        ax.set_ylim(-340, 330)
        ax.axis("off")
    fig.suptitle("Where each stand meets the bench (teal: the feet's outline; x: centre of mass at the worst tilt mix; "
                 "blue circle: the clear column under the shelf; dashed: the modules' reach at 0°; front is down)",
                 fontsize=12, x=0.01, ha="left")
    fig.tight_layout(rect=(0, 0, 1, 0.95))
    fig.savefig(fn)
    plt.close(fig)


# --------------------------------------------------------------------------- #
# main
# --------------------------------------------------------------------------- #
NAMES = {"S1": "printed tripod, fixed 217 mm", "S2": "telescoping tripod, 217-359 mm",
         "S3": "table on a board + lab jack, 372 mm", "S4": "retort stand or hood lattice"}


def concept(key):
    """(stand parts, stand height, bench z, vessel set-up, extra masses on the stand's base)."""
    if key == "S1":
        S = S1["height"]
        zb = BOT - S
        st = s1_parts()
        row = "250 mL"
        # the 250 mL beaker between the towers on the stir plate + riser (clearance.json's table)
        rim = OUTLET_90 - CL.RIM_BELOW_90
        riser = rim - C.BEAKERS[row][1] - (zb + CL.STIR["h"])
        ves = vessel_parts(row, zb, riser=riser)
        return st, S, zb, ves, (), dict(vessel=f"250 mL beaker on a 100 mm stir plate + {riser:.0f} mm riser")
    if key == "S2":
        S = 326.0
        zb = BOT - S
        st = s2_parts(S)
        ves = vessel_parts("500 mL", zb)
        return st, S, zb, ves, (), dict(vessel="500 mL Erlenmeyer + 80 mm funnel on a 100 mm stir plate")
    if key == "S3":
        S = S3["height"]
        zb = BOT - S
        st = s3_parts()
        zf = zb + S3["board"]["t"]
        rim = OUTLET_90 - CL.RIM_BELOW_90
        jack_top = rim - C.BEAKERS["250 mL"][1] - CL.STIR["h"]
        ves = vessel_parts("250 mL", zf, jack_top=jack_top)
        extra = [(M_STIR, np.array([0, 0, jack_top + 50.0])), (M_JACK, np.array([0, 0, (zf + jack_top) / 2]))]
        return st, S, zb, ves, extra, dict(vessel=f"250 mL beaker on a 100 mm stir plate on a lab jack set to "
                                                  f"{jack_top - zf:.0f} mm", jack_height=round(jack_top - zf, 1))
    if key == "S4":
        S = 250.0
        zb = BOT - S
        st = s4_parts(S)
        zf = zb + S4["base"][2]
        rim = OUTLET_90 - CL.RIM_BELOW_90
        riser = rim - C.BEAKERS["250 mL"][1] - (zf + CL.STIR["h"])
        ves = vessel_parts("250 mL", zf, riser=riser)
        extra = [(M_STIR, np.array([0, 0, zf + 50.0]))]
        return st, S, zb, ves, extra, dict(vessel=f"250 mL beaker on a stir plate + {riser:.0f} mm riser, on the "
                                                  "retort stand's base")
    raise KeyError(key)


def main():
    import sys
    OUT.mkdir(exist_ok=True)
    res = dict(spacing=SP, s_min=S_MIN, S1=dict(S1), S2={k: v for k, v in S2.items()}, S3=dict(S3), S4=dict(S4))
    # the doser's reach in plan (0 deg) and height above the hinge (90 deg)
    ext = []
    for t in (0, 90):
        for p in doser((t, t, t)):
            m = D.mesh_of(p.shape)
            ext.append((p.M[:3, :3] @ np.asarray(m.vertices).T).T + p.M[:3, 3])
    ev = np.vstack(ext)
    res["doser_reach_mm"] = round(float(np.hypot(ev[:, 0], ev[:, 1]).max()), 1)
    res["doser_top_above_hinge_mm"] = round(float(ev[:, 2].max()), 1)
    print("reach", res["doser_reach_mm"], "top", res["doser_top_above_hinge_mm"], flush=True)
    quick = "--no-checks" in sys.argv
    paths = {}
    for key in ("S1", "S2", "S3", "S4"):
        st, S, zb, ves, extra, info = concept(key)
        r = res[key] = dict(name=NAMES[key], height_mm=S, **info, **{k: v for k, v in res[key].items()})
        units = "ABC" if key == "S4" else "A"
        if not quick:
            r["clearance_to_moving_parts"] = stand_vs_doser(st, units=units)
            print(key, "clearance", r["clearance_to_moving_parts"], flush=True)
        z_floor = zb + (S3["board"]["t"] if key == "S3" else S4["base"][2] if key == "S4" else 0.0)
        r["floor_above_bench_mm"] = round(z_floor - zb, 1)
        gate = {}
        for tag, tl in (("parked_0deg", (0,)), ("any_tilt", range(0, 91, 10))):
            ob = obstacle_points(st, tilts=tl)
            w1, l1 = front_gate(ob, z_floor, z_floor + 100.0)
            w2, l2 = front_gate(ob, z_floor, BOT)
            cr, cl = column_r(ob, z_floor + 1.0, BOT)
            gate[tag] = dict(lowest_100mm=w1, lowest_100mm_set_by=l1, up_to_shelf=w2, up_to_shelf_set_by=l2,
                             column_dia=round(2 * cr, 1), column_set_by=cl)
        r["front_gate_mm"] = gate
        r["column_r_mm"] = gate["any_tilt"]["column_dia"] / 2
        r["stability"] = stability(st, zb, extra)
        r["footprint_mm"] = footprint(st, zb)
        r["overall_height_mm"] = dict(at_0=round(S - BOT + 23.7), at_90=round(S - BOT + res["doser_top_above_hinge_mm"]))
        r["printed"] = printed(st)
        print(key, json.dumps({k: r[k] for k in ("front_gate_mm", "footprint_mm", "overall_height_mm")}),
              r["stability"]["margin_mm"], r["stability"]["push_at_shelf_N"], flush=True)
        if not quick:
            rests = {"S3": (("lab jack", "S3 board"),), "S4": (("stir plate", "S4 retort base"),)}.get(key, ())
            r["vessel_clearance"] = vessel_check(st, ves, rests_on=rests)
            print(key, "vessel", r["vessel_clearance"], flush=True)
        tilts = (30, 60, 0)
        ps = doser(tilts) + st + ves + [bench(zb)]
        paths[key] = (ps, S, zb)
    # S2 over the HR-100A, at 320 mm
    S = 320.0
    zb = BOT - S
    st = s2_parts(S)
    bal = balance_parts(zb)
    pan = zb + 86.5
    rim = OUTLET_90 - CL.RIM_BELOW_90
    riser = rim - C.BEAKERS["100 mL"][1] - pan
    ves = vessel_parts("100 mL", pan, riser=riser, stir=False, riser_r=30.0)
    bal_res = dict(height_mm=S, riser_mm=round(riser, 1),
                   gap_shelf_to_balance_top_mm=round(BOT - (zb + 315.0), 1),
                   overlap_post_in_sleeve_mm=round((BOT - S + S2["foot_h"] + S2["post_len"]) - S2["sleeve_bot"], 1))
    if not quick:
        hr = [p for p in bal if p.name == "HR-100A"]
        bal_res["stand_to_balance"] = round(min(_dist(o1, o2) for (_, o1) in _objs(st) for (_, o2) in _objs(hr)), 2)
        bal_res["moving_parts_to_balance"] = stand_vs_doser(hr, units="ABC", tilts=range(0, 91, 10))
        bal_res["moving_parts_to_stand"] = stand_vs_doser(st, units="A")
        hang = [p for p in doser((0, 0, 0)) if p.kind in ("p16", "ubracket")]
        bal_res["actuators_to_balance_0deg"] = round(min(_dist(o1, o2) for (_, o1) in _objs(hang) for (_, o2) in _objs(hr)), 2)
        bal_res["beaker_and_riser"] = vessel_check(st + hr, ves, rests_on=(("riser", "HR-100A"),))
        print("balance", bal_res, flush=True)
    res["S2_over_HR100A"] = bal_res
    paths["S2bal"] = (doser((30, 60, 0)) + st + bal + ves + [bench(zb)], S, zb)
    res["S2"]["range_mm"] = list(S2["range"])
    # S3: the doser stays at one height, so each vessel needs its own lab-jack height (clearance.json's stacks,
    # which stand each vessel on a 100 mm stir plate)
    stacks = json.loads((HERE / "clearance.json").read_text())["stacks"]
    res["S3"]["jack_for_each_vessel_mm"] = {r_["vessel"]: round(S3["height"] - S3["board"]["t"] - r_["stand_needed"], 1)
                                            for r_ in stacks}
    (HERE / "stands.json").write_text(json.dumps(res, indent=1, default=float) + "\n")
    figures(res, paths)


def figures(res, paths):
    files = []
    sub = {
        "S1": ["Three printed A-frame legs, one under each lobe end; each also holds its P16.",
               f"Shelf {res['S1']['height_mm']:.0f} mm up (the lowest it can go). {res['S1']['vessel']}."],
        "S2": ["Printed sleeves (each holds its P16) on 20 x 20 aluminium posts, pinned every 10 mm.",
               f"Shown at {res['S2']['height_mm']:.0f} mm: {res['S2']['vessel']}."],
        "S3": [f"2020 posts on a 12 mm board; the shelf stays {res['S3']['height_mm']:.0f} mm up and a lab jack lifts the vessel.",
               f"{res['S3']['vessel']}."],
        "S4": ["A printed arm under two lobes clamps a 12.7 mm lab rod in the back-left gap.",
               f"Shown at {res['S4']['height_mm']:.0f} mm: {res['S4']['vessel']}."],
        "S2bal": [f"S2 set to {res['S2_over_HR100A']['height_mm']:.0f} mm over the A&D HR-100A, touching nothing on it.",
                  f"100 mL beaker on a {res['S2_over_HR100A']['riser_mm']:.0f} mm riser on the pan, up through the top door."],
    }
    titles = {"S1": "S1  Printed tripod, fixed", "S2": "S2  Telescoping tripod", "S3": "S3  Table on a board + lab jack",
              "S4": "S4  Retort stand clamp", "S2bal": "S2 over the balance (weighing while dosing)"}
    for key in ("S1", "S2", "S3", "S4", "S2bal"):
        ps, S, zb = paths[key]
        fn = OUT / f"stand_{key.lower()}.png"
        render_concept(key, ps, titles[key], sub[key], fn, az=-58.0 if key != "S4" else -150.0, el=18.0)
        files.append(fn)
        print("  ->", fn.name, flush=True)
    sheet(files[:4], OUT / "stands_overview.png", "Stand options for the tri-star (issue #204)",
          ["Modules at 30, 60 and 0 deg. Doser colours as before (blue reused, yellow plate, magenta #203 bracket, orange base,"
           " dark grey P16). Stand parts are placeholders.",
           "Every stand leaves the actuators hanging from the shelf, so it only has to hold the shelf. Nothing rises above the"
           " shelf where the modules sweep (S4's rod stands in the gap between two modules)."])
    print("  -> stands_overview.png", flush=True)
    plan_figure(res, OUT / "stands_plan.png")
    print("  -> stands_plan.png", flush=True)


if __name__ == "__main__":
    main()
