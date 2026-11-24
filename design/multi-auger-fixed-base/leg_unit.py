"""One telescoping leg unit for the tri-star's L4 layout, and what the base needs to take it (issue #204, 24 Nov).

Ethan picked the "lever + lean" actuator layout (L4 in leg_room.py: a P16-200 leaning 25 deg outward,
its rod-end clevis pin 120 mm behind the hinge) on S2-style telescoping legs, for the lab's A&D HR-250AZ.
The HR-250AZ has the same body as the HR-100A that scale_room.py traced from A&D's drawing
(198 x 294 x 315 mm; one manual covers both series), so that model is used here.

One leg unit, the same at each of the three lobes:

  * a printed head: an arm bolted under the lobe end (4 x M4 countersunk from the top, nuts in traps
    underneath), a window in the arm for the clevis block and the P16's rod, a sleeve 302 mm from the
    beaker axis for the tube, and a tab that carries the P16-200's own U-bracket at its rear pin.  The
    tab is on the head, so the rear pin stays put relative to the hinge whatever the stand's height;
  * a 20 x 20 x 1.5 mm aluminium square tube, 280 mm long, that slides in the sleeve, pinned with an M5
    through one of ten holes 10 mm apart: the shelf's underside 310-400 mm above the bench;
  * a printed foot on the tube's lower end.

The script builds the unit, checks it against every moving part (its own module and both neighbours, 0-90
deg in 5 deg steps), builds the base with L4's slot and the new holes and checks that too, fits the HR-100A
under the station at every orientation (lid on and off), checks a reach-in corridor beside each side door
and the lid's swing, exports STEP/STL files and draws the figures.

    pip install cadquery trimesh python-fcl rtree vtk pillow numpy matplotlib scipy
    xvfb-run -a python leg_unit.py                  # about 7 min; leg_unit.json, leg-unit/, renders/leg_*.png
    xvfb-run -a python leg_unit.py --figures-only   # redraws the figures from leg_unit.json

Frames.  The leg frame: origin on the beaker axis at the shelf's underside, x across the module (along its
hinge axis), y outward along the module's centre line (distance from the beaker axis), z up.  For the back
module this is the frame of base/base.step (whose z = 0 is the base's underside), so a part in this frame
drops straight onto the base there.  The unit frame of doserlib.py (hinge on x, +y behind the hinge, z up,
hinge at z = 0) is the leg frame shifted by (0, -32, -43.25).  Station frame as in doserlib.py.
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
import leg_room as LR

HERE = Path(__file__).resolve().parent
OUT = HERE / "renders"
CAD = HERE / "leg-unit"
SP = B.SP                                   # 32: hinge axis to beaker axis
BOT = B.BOT                                 # -43.25: shelf underside, unit frame
GAP = 2.0
TILTS = tuple(range(0, 91, 5))
S_SHOW = 340.0                              # the height the checks and renders use (HR-100A, lid on)
L2U = D.Tt(0.0, -SP, BOT)                   # leg frame -> unit frame

# --------------------------------------------------------------------------- #
# the actuator (L4) and the clevis block variant it needs
# --------------------------------------------------------------------------- #
MT.P16.setdefault("P16-200", dict(closed=247.0, stroke=200.0))
PIN = (0.0, 258.5, -230.0)                  # the P16-200's rear pin, leg frame: L4's (258.50, -230.14) rounded
_BP = np.array([PIN[1] - SP, PIN[2] + BOT])  # the same, unit frame: (226.5, -273.25)
ACT = dict(a=120.0, act="P16-200", lean=25.0, pin_u=(float(_BP[0]), float(_BP[1])))
_base_pin0 = MT.base_pin


def _base_pin(o):
    """mounts.base_pin, but a rear pin given outright (``pin_u``, unit frame) wins."""
    return np.array(o["pin_u"], float) if "pin_u" in o else _base_pin0(o)


MT.base_pin = _base_pin

# --------------------------------------------------------------------------- #
# the leg unit (leg frame, mm)
# --------------------------------------------------------------------------- #
HEAD = dict(
    half=32.0,                              # every printed section is 64 wide (x), so it prints flat on its side
    arm_y0=92.0, arm_depth=15.0,            # the arm: from 92 mm out, 15 deep under the shelf
    holes_x=25.0, holes_y=(100.0, 126.0), hole_d=4.5, nut_af=7.2, nut_h=3.4,   # 4 x M4: base -> arm
    window=[(0.0, 127.0), (17.0, 144.0), (17.0, 161.0), (9.0, 169.0), (9.0, 198.0), (0.0, 207.0)],  # +x half
    sleeve_y=285.5, wall=6.0, bore=20.6, sleeve_bot=-281.75, bore_top=-20.0,
    arm_gusset=50.0,                        # 45 deg web, arm underside to the sleeve's inner face
    tab_y0=250.5, tab_t=8.0, tab_gusset=15.5,
    pocket=(15.1, 8.1, 1.0),                # keys the U-bracket's base (14.5 x 7.5)
    m3_d=3.4, m3_nut_af=5.7, m3_nut_h=2.6,  # M3 x 12 button head from inside the U, nut underneath
    pin_z=-130.0, pin_d=5.3,                # M5 height pin, along y through the sleeve
)
HEAD["post_y"] = HEAD["sleeve_y"] + HEAD["wall"] + HEAD["bore"] / 2            # 301.8: tube centre
HEAD["sleeve_out"] = HEAD["sleeve_y"] + 2 * HEAD["wall"] + HEAD["bore"]        # 318.1
HEAD["tab_top"] = PIN[2] - K.UB["h"] + HEAD["pocket"][2]                       # -238.1
TUBE = dict(size=20.0, wall=1.5, length=280.0, pitch=10.0, hole_d=5.2, foot_hole_d=4.5, foot_hole_h=10.0)
FOOT = dict(pad=60.0, pad_t=6.0, socket=28.0, socket_h=20.0, bore=20.4, hole_d=4.5)
S_RANGE = (310.0, 400.0)                    # shelf underside above the bench, in 10 mm steps


def tube_bottom(S):
    return -S + FOOT["pad_t"]


def tube_holes():
    """Heights of the tube's M5 holes above its lower end: one per setting in S_RANGE."""
    return [round(S - FOOT["pad_t"] + HEAD["pin_z"], 1) for S in np.arange(S_RANGE[0], S_RANGE[1] + 0.1, 10.0)]


def head_profile():
    """The head's side profile, (y, z) in the leg frame: arm, web, sleeve, tab and its web."""
    h = HEAD
    yi, yo, zb = h["sleeve_y"], h["sleeve_out"], h["sleeve_bot"]
    za, g = -h["arm_depth"], h["arm_gusset"]
    tt, tb = h["tab_top"], h["tab_top"] - h["tab_t"]
    tg = h["tab_gusset"]
    return [(h["arm_y0"], 0.0), (yo, 0.0), (yo, zb), (yi, zb), (yi, tb - tg), (yi - tg, tb), (h["tab_y0"], tb),
            (h["tab_y0"], tt), (yi, tt), (yi, za - g), (yi - g, za), (h["arm_y0"], za)]


def window_pts():
    w = HEAD["window"]
    return w + [(-x, y) for x, y in reversed(w[1:-1])]


def hexagon(cx, cy, af, rot=0.0):
    r = af / math.sqrt(3.0)
    return [(cx + r * math.cos(math.radians(rot + 30 + 60 * i)), cy + r * math.sin(math.radians(rot + 30 + 60 * i)))
            for i in range(6)]


def prism_xy(pts, z0, z1):
    return cq.Workplane("XY", origin=(0, 0, z0)).polyline(pts).close().extrude(z1 - z0).val()


def head():
    """The printed head, one part."""
    h = HEAD
    prof = cq.Workplane("YZ", origin=(-h["half"], 0, 0)).polyline(head_profile()).close().extrude(2 * h["half"]).val()
    za = -h["arm_depth"]
    out = prof.cut(prism_xy(window_pts(), za - 1, 1))
    for sx in (1, -1):
        for y in h["holes_y"]:
            out = out.cut(D.cyl(h["hole_d"] / 2, h["arm_depth"] + 2, sx * h["holes_x"], y, za - 1))
            out = out.cut(prism_xy(hexagon(sx * h["holes_x"], y, h["nut_af"]), za - 1, za + h["nut_h"]))
    b, pc = h["bore"] / 2, h["post_y"]
    out = out.cut(D.box(-b, b, pc - b, pc + b, h["sleeve_bot"] - 1, h["bore_top"]))
    out = out.cut(D.cyl(h["pin_d"] / 2, 60.0, 0.0, h["sleeve_y"] - 10, h["pin_z"], d=(0, 1, 0)))
    px, py, pd = h["pocket"]
    tt, tb = h["tab_top"], h["tab_top"] - h["tab_t"]
    out = out.cut(D.box(-px / 2, px / 2, PIN[1] - py / 2, PIN[1] + py / 2, tt - pd, tt + 0.01))
    out = out.cut(D.cyl(h["m3_d"] / 2, h["tab_t"] + 2, 0.0, PIN[1], tb - 1))
    out = out.cut(prism_xy(hexagon(0.0, PIN[1], h["m3_nut_af"]), tb - 1, tb + h["m3_nut_h"]))
    return out.clean()


def tube(S=S_SHOW):
    t = TUBE
    z0 = tube_bottom(S)
    a, pc = t["size"] / 2, HEAD["post_y"]
    out = D.box(-a, a, pc - a, pc + a, z0, z0 + t["length"])
    out = out.cut(D.box(-a + t["wall"], a - t["wall"], pc - a + t["wall"], pc + a - t["wall"], z0 - 1, z0 + t["length"] + 1))
    for hh in tube_holes():
        out = out.cut(D.cyl(t["hole_d"] / 2, 30.0, 0.0, pc - 15.0, z0 + hh, d=(0, 1, 0)))
    out = out.cut(D.cyl(t["foot_hole_d"] / 2, 30.0, -15.0, pc, z0 + t["foot_hole_h"], d=(1, 0, 0)))
    return out.clean()


def foot(S=S_SHOW):
    f = FOOT
    zb, pc = -S, HEAD["post_y"]
    p, s, b = f["pad"] / 2, f["socket"] / 2, f["bore"] / 2
    out = D.box(-p, p, pc - p, pc + p, zb, zb + f["pad_t"])
    out = out.fuse(D.box(-s, s, pc - s, pc + s, zb + f["pad_t"], zb + f["pad_t"] + f["socket_h"]))
    out = out.cut(D.box(-b, b, pc - b, pc + b, zb + f["pad_t"], zb + f["pad_t"] + f["socket_h"] + 1))
    out = out.cut(D.cyl(f["hole_d"] / 2, 40.0, -20.0, pc, zb + f["pad_t"] + TUBE["foot_hole_h"], d=(1, 0, 0)))
    return out.clean()


def m5_pin():
    """M5 x 40 socket head along y, head on the sleeve's outer face, a wing nut (as a 9 mm disc) inside."""
    y1 = HEAD["sleeve_out"]
    z = HEAD["pin_z"]
    shank = D.cyl(2.5, 40.0, 0.0, y1 - 40.0, z, d=(0, 1, 0))
    hd = D.cyl(4.25, 5.0, 0.0, y1, z, d=(0, 1, 0))
    nut = D.cyl(4.5, 4.0, 0.0, HEAD["sleeve_y"] - 4.0, z, d=(0, 1, 0))
    return shank.fuse(hd).fuse(nut).clean()


def foot_screw(S=S_SHOW):
    z = tube_bottom(S) + TUBE["foot_hole_h"]
    pc = HEAD["post_y"]
    return D.cyl(2.0, 36.0, -18.0, pc, z, d=(1, 0, 0)).fuse(D.cyl(3.5, 4.0, 14.0, pc, z, d=(1, 0, 0))).fuse(
        D.cyl(3.9, 4.0, -18.0, pc, z, d=(1, 0, 0))).clean()


def m4_screws():
    """4 x M4 x 25 countersunk (ISO 10642) from the shelf's top, nuts in the arm's traps (leg frame)."""
    out = None
    za = -HEAD["arm_depth"]
    for sx in (1, -1):
        for y in HEAD["holes_y"]:
            x = sx * HEAD["holes_x"]
            hd = cq.Solid.makeCone(2.0, 4.48, 2.48, cq.Vector(x, y, B.T - 0.2 - 2.48), cq.Vector(0, 0, 1))
            s = D.cyl(2.0, 25.0 - 2.48, x, y, B.T - 0.2 - 25.0).fuse(hd)
            n = prism_xy(hexagon(x, y, 7.0), za, za + 3.2)
            s = s.fuse(n)
            out = s if out is None else out.fuse(s)
    return out.clean()


def m3_screw():
    """M3 x 12 button head (ISO 7380, 1.65 mm head) through the U-bracket's base into the tab's nut."""
    z_top = PIN[2] - K.UB["h"] + K.UB["t"]               # top of the bracket's base sheet
    hd = D.cyl(2.85, 1.65, 0.0, PIN[1], z_top)
    sh = D.cyl(1.5, 12.0, 0.0, PIN[1], z_top - 12.0)
    tb = HEAD["tab_top"] - HEAD["tab_t"]
    nut = prism_xy(hexagon(0.0, PIN[1], 5.5), tb, tb + 2.4)
    return hd.fuse(sh).fuse(nut).clean()


# --------------------------------------------------------------------------- #
# the base with L4's slot and the leg's holes (leg frame per lobe; built in the station frame)
# --------------------------------------------------------------------------- #
BASE = dict(slot_x=17.0, slot_y=(134.0, 182.0), holes=[(sx * HEAD["holes_x"], y) for sx in (1, -1) for y in HEAD["holes_y"]],
            hole_d=4.5, csk_d=9.4)
OLD = dict(slot_y=(B.SLOT["y0"] + SP, B.SLOT["y1"] + SP), holes=[(sx * B.PAD["x"], y + SP) for sx in (1, -1) for y in B.PAD["y"]])


def base_l4(old_slot=False):
    """The one-piece base (base.py) with, per lobe: the slot from 134 mm out through the lobe end (174), the
    old hanger holes gone, four countersunk M4 holes for the leg.  ``old_slot`` keeps base.py's slot too."""
    sk = B.shelf_outline_sketch()
    shelf = cq.Workplane("XY", origin=(0, 0, BOT)).placeSketch(sk).extrude(B.T).val()
    shelf = shelf.cut(D.cyl(B.WIN_D / 2, B.T + 2, 0, 0, BOT - 1))
    for th in B.BEARINGS:
        loc = LR.C_loc(D.place(th, SP, 0.0) @ L2U)
        cut = D.box(-BASE["slot_x"], BASE["slot_x"], BASE["slot_y"][0], BASE["slot_y"][1], -1, B.T + 1)
        if old_slot:
            cut = cut.fuse(D.box(-B.SLOT["x"], B.SLOT["x"], OLD["slot_y"][0], OLD["slot_y"][1], -1, B.T + 1))
        for x, y in BASE["holes"]:
            cut = cut.fuse(D.cyl(BASE["hole_d"] / 2, B.T + 2, x, y, -1))
            r1 = BASE["csk_d"] / 2
            dz = r1 - BASE["hole_d"] / 2                     # 90 deg countersink
            cut = cut.fuse(cq.Solid.makeCone(BASE["hole_d"] / 2, r1 + 0.5, dz + 0.5, cq.Vector(x, y, B.T - dz), cq.Vector(0, 0, 1)))
        shelf = shelf.cut(cut.moved(loc))
    tw = B.tower_today()
    tw_neg = tw.mirror("YZ", (0, 0, 0))
    for th in B.BEARINGS:
        loc = LR.C_loc(D.place(th, SP, 0.0))
        shelf = shelf.fuse(tw.moved(loc)).fuse(tw_neg.moved(loc))
    return shelf.clean()


# --------------------------------------------------------------------------- #
# assembly
# --------------------------------------------------------------------------- #
PRINT = (0.16, 0.62, 0.56)
ALU = (0.78, 0.80, 0.83)
HW = (0.55, 0.56, 0.58)
_S: dict = {}


def cached(k, fn):
    if k not in _S:
        _S[k] = fn()
    return _S[k]


def leg_parts(th, u, S=S_SHOW, hardware=True):
    """One leg unit at the lobe of the module at bearing th (station frame)."""
    M = D.place(th, SP, 0.0) @ L2U
    ps = [(f"{u}:leg head", cached("head", head), PRINT, "print"),
          (f"{u}:leg tube", cached(("tube", S), lambda: tube(S)), ALU, "alu"),
          (f"{u}:leg foot", cached(("foot", S), lambda: foot(S)), PRINT, "print")]
    if hardware:
        ps += [(f"{u}:M5 height pin", cached("m5", m5_pin), HW, "hw"),
               (f"{u}:M4 base screws", cached("m4", m4_screws), HW, "hw"),
               (f"{u}:M3 bracket screw", cached("m3", m3_screw), HW, "hw"),
               (f"{u}:foot screw", cached(("fs", S), lambda: foot_screw(S)), HW, "hw")]
    out = []
    for name, shp, col, kind in ps:
        p = D.Part(name, shp, M, col, "leg-" + u, False)
        p.kind = kind
        out.append(p)
    return out


def module_parts(th, u, tilt):
    """The module (L4: P16-200 leaning 25 deg, clevis pin 120 mm behind the hinge) at ``tilt``, with the
    U-bracket on the head's tab (vertical, under the rear pin) and the #8-32 pin."""
    ps = LR.module_parts("L4", tilt, D.place(th, SP, 0.0), u)
    out = []
    for p in ps:
        if p.name.endswith("P16 bracket"):
            p.M = D.place(th, SP, 0.0) @ D.Tt(0.0, float(_BP[0]), float(_BP[1]))
        if p.name.endswith("tail"):
            continue                                   # not needed: the L4 block ends at the floor's rear edge
        if p.name.endswith("clevis block"):
            p.shape = cached("l4block", l4_block)
        out.append(p)
    pin = D.Part(f"{u}:#8-32 pin", cached("bpin", K.base_pin), D.place(th, SP, 0.0) @ D.Tt(0.0, float(_BP[0]), float(_BP[1])),
                 HW, u, False)
    pin.kind = "module"
    out.append(pin)
    return out


L4_BLOCK = dict(pad_y=(-14.0, 10.0), screw_y=-10.0)     # block frame: y from the pin, + toward the rear


def l4_block():
    """The clevis block for L4 (block frame of clevis.py: x along the pin, y from the pin axis, z = 0 on the
    pad's top face).  clevis.py's block with its pad shifted 2 mm forward, so it ends at the floor's rear edge
    (130 mm behind the hinge) instead of 2 mm past it, and its two M3 holes 10 mm ahead of the pin, clear of
    the rear Flexible Bracket that covers the floor's top from 118 to 130 mm behind the hinge."""
    import clevis as CL
    y0, y1 = L4_BLOCK["pad_y"]
    ys = L4_BLOCK["screw_y"]
    b = D.box(-CL.PX / 2, CL.PX / 2, y0, y1, -CL.PT, 0.0)
    for x0 in (CL.GAP / 2, -CL.GAP / 2 - CL.LUG_T):
        lug = D.box(x0, x0 + CL.LUG_T, -CL.LUG_R, CL.LUG_R, CL.PIN_Z, -CL.PT + 0.5).fuse(
            D.cyl(CL.LUG_R, CL.LUG_T, x0, 0.0, CL.PIN_Z, d=(1, 0, 0)))
        b = b.fuse(lug)
    b = b.cut(D.cyl(CL.PIN_D / 2, 40.0, -20.0, 0.0, CL.PIN_Z, d=(1, 0, 0)))
    for sx in (1, -1):
        b = b.cut(D.cyl(CL.SCREW_D / 2, 20.0, sx * CL.SX, ys, -10.0))
        b = b.cut(CL.hex_prism(sx * CL.SX, ys, CL.NUT_AF, -CL.PT - 0.01, CL.NUT_H + 0.01))
    return b.clean()


# --------------------------------------------------------------------------- #
# checks
# --------------------------------------------------------------------------- #
CONTACT = ("P16 bracket", "#8-32 pin")          # sit on the tab by design


def prepare():
    """leg_room's options, with L4's rear pin set to PIN (rounded) instead of computed."""
    LR.prepare()
    LR.OPTIONS["L4"]["act_fit"] = dict(ACT)


def checks():
    """Every part of the leg units (and the L4 base) against every moving part, 0-90 deg in 5 deg steps,
    one module at a time (so every tilt mix): own module, both neighbours."""
    legs = []
    for i, th in enumerate(B.BEARINGS):
        legs += leg_parts(th, "ABC"[i])
    lo = ST._objs(legs)
    base = D.Part("base", cached("base_l4", base_l4), np.eye(4), (0.6, 0.6, 0.6), "fixed", False)
    bo = ST._objs([base])
    worst = {"own module": (1e9,), "neighbours": (1e9,), "base": (1e9,)}
    per_part = {}
    for i, th in enumerate(B.BEARINGS):
        u = "ABC"[i]
        for t in TILTS:
            for p, op in ST._objs(module_parts(th, u, t)):
                for q, oq in lo:
                    own = q.name.startswith(u + ":")
                    if own and p.name.endswith(CONTACT) and q.name.endswith(("leg head", "M3 bracket screw")):
                        continue
                    d = ST._dist(op, oq)
                    k = "own module" if own else "neighbours"
                    if d < worst[k][0]:
                        worst[k] = (d, p.name, q.name, t)
                    pk = q.name.split(":")[1]
                    if own and d < per_part.get(pk, (1e9,))[0]:
                        per_part[pk] = (d, p.name, t)
                if p.name.endswith(("Mounting plate",)):
                    continue                       # the knuckles run 0.3 mm inside the towers, as today
                if p.name.endswith(CONTACT):
                    continue
                d = ST._dist(op, bo[0][1])
                if d < worst["base"][0]:
                    worst["base"] = (d, p.name, "base", t)
        print(f"  checks: module {u} done", flush=True)
    out = {k: dict(mm=round(v[0], 2), between=f"{v[1]} / {v[2]}", at_tilt=v[3]) for k, v in worst.items()}
    out["per_leg_part_own_module"] = {k: dict(mm=round(v[0], 2), closest=v[1], at_tilt=v[2]) for k, v in per_part.items()}
    return out


def rear_pin_swing():
    """How far the P16-200 swings about its rear pin: its lean from vertical (deg, its top leaning in), which
    is also its angle in the upright U-bracket."""
    leans = [LR.lean_at(ACT, t) for t in np.arange(0.0, 90.01, 0.5)]
    return dict(lean_min_deg=round(min(leans), 2), lean_max_deg=round(max(leans), 2))


def bracket_check():
    """Inside the U-bracket, by design: the P16-200 (housing and lug) against the bracket, and the M3 button
    head against the P16, over 0-90 deg (5 deg steps)."""
    th, u = 90.0, "A"
    m3 = ST._objs([p for p in leg_parts(th, u) if p.name.endswith("M3 bracket screw")])[0][1]
    w = dict(bracket=(1e9, None), m3_head=(1e9, None))
    for t in TILTS:
        ps = {p.name.split(":", 1)[1]: p for p in module_parts(th, u, t)}
        (_, ob), (_, oy) = ST._objs([ps["P16 bracket"], ps["P16 body"]])
        d = ST._dist(ob, oy)
        if d < w["bracket"][0]:
            w["bracket"] = (d, t)
        d = ST._dist(m3, oy)
        if d < w["m3_head"][0]:
            w["m3_head"] = (d, t)
    return {"P16 housing/lug to its U-bracket": dict(mm=round(w["bracket"][0], 2), at_tilt=w["bracket"][1]),
            "M3 button head to the P16's lug": dict(mm=round(w["m3_head"][0], 2), at_tilt=w["m3_head"][1])}


# --------------------------------------------------------------------------- #
# the HR-100A (HR-250AZ) under the station: body, side doors, lid
# --------------------------------------------------------------------------- #
DOOR = dict(width=100.0, z=(SR.HR["base_top"], SR.HR["rim_top"]), r0=SR.HR["bb_r"], reach=150.0)


def obstacle_samples(S=S_SHOW):
    """Surface samples (station frame) of everything under the shelf: the modules' hanging parts at every
    tilt (module A's swept and copied to B and C), and the legs."""
    P = []
    for t in TILTS:
        for p in module_parts(90.0, "A", t):
            if not p.name.endswith(LR.HANGING + ("#8-32 pin",)):
                continue
            q = LR.samples(p.shape, p.M, 1.5)
            P.append(q[q[:, 2] < BOT + 0.5])
    A = np.vstack(P)
    legs = np.vstack([LR.samples(p.shape, p.M, 2.0) for th, u in zip(B.BEARINGS, "ABC")
                      for p in leg_parts(th, u, S, hardware=False)])
    return LR.rot3(A), legs


def door_corridor(Pb, side):
    """Clear reach-in depth beside a side door: the corridor runs from the breeze break (r 93) outward along
    the balance's y (side = +1 left, -1 right), DOOR['width'] wide in x, over the doors' height range.
    Returns how far out (mm past the breeze break) the first obstacle sits, capped at DOOR['reach']."""
    w = DOOR["width"] / 2
    s = (np.abs(Pb[:, 0]) < w) & (Pb[:, 2] > DOOR["z"][0]) & (Pb[:, 2] < DOOR["z"][1]) & (side * Pb[:, 1] > DOOR["r0"])
    if not s.any():
        return DOOR["reach"]
    return round(float(min(DOOR["reach"], (side * Pb[s, 1]).min() - DOOR["r0"])), 1)


def lid_swing(Pb):
    """The lid swings out to the user's left (+y), to 270 mm from the pan centre: the band |x| < 93 from the
    pan centre out to y = 270, between the rim and the lid's top (290-315).  Closest obstacle (mm, + = clear)."""
    s = (Pb[:, 2] > SR.HR["rim_top"] - 5.0) & (Pb[:, 2] < SR.HR["H"] + 5.0) & (Pb[:, 1] > 0.0) & (Pb[:, 1] < SR.HR["lid_open_reach"])
    if not s.any():
        return 99.0
    return round(float((np.abs(Pb[s, 0]) - SR.HR["bb_r"]).min()), 1)


def hr_fit(S=S_SHOW):
    act, legs = obstacle_samples(S)
    allP = np.vstack([act, legs])
    zb = BOT - S
    rows = []
    for phi in range(0, 360, 5):
        Pb = SR.to_balance(allP, phi, zb)
        row = dict(phi=phi)
        for lid in (True, False):
            row["lid_on" if lid else "lid_off"] = round(float(SR.sdf(Pb, SR.hr_prims(lid)).min()), 1)
        row["door_left"] = door_corridor(Pb, +1)
        row["door_right"] = door_corridor(Pb, -1)
        row["lid_swing"] = lid_swing(Pb)
        rows.append(row)
    # the display faces the user (bearing 270) when the rear column points to bearing 90
    face = next(r for r in rows if r["phi"] == 90)
    best_door = max(rows, key=lambda r: (min(DOOR["reach"], max(r["door_left"], r["door_right"])), r["lid_swing"], r["lid_on"]))
    both = [r["phi"] for r in rows if r["door_left"] >= DOOR["reach"] and r["door_right"] >= DOOR["reach"]]
    one = [r["phi"] for r in rows if max(r["door_left"], r["door_right"]) >= DOOR["reach"]]
    lid_ok = [r["phi"] for r in rows if r["lid_swing"] >= GAP]
    return dict(S=S, rows=rows, display_facing_user=face,
                worst_lid_on=min(r["lid_on"] for r in rows), worst_lid_off=min(r["lid_off"] for r in rows),
                phis_both_doors=both, phis_one_door=one, phis_lid_swings=lid_ok,
                phis_lid_and_a_door=[p for p in lid_ok if p in one], best=best_door,
                arm_bottom_above_bench=round(S - HEAD["arm_depth"], 1), hr_top_lid_on=SR.HR["H"], hr_rim=SR.HR["rim_top"])


# --------------------------------------------------------------------------- #
# numbers for the README
# --------------------------------------------------------------------------- #
def masses():
    hd, tb, ft = cached("head", head), tube(), foot()
    return dict(head_cm3=round(hd.Volume() / 1000, 1), foot_cm3=round(ft.Volume() / 1000, 1), tube_cm3=round(tb.Volume() / 1000, 1),
                head_g_at_60pct=round(hd.Volume() * 1.24e-3 * 0.6), foot_g_at_60pct=round(ft.Volume() * 1.24e-3 * 0.6),
                tube_g=round(tb.Volume() * 2.70e-3))


def bed_fit():
    """The head printed on its side (x up): its y-z box against one H2D nozzle (325 x 320)."""
    bb = cached("head", head).BoundingBox()
    a, b = sorted((bb.ylen, bb.zlen), reverse=True)
    return dict(footprint_mm=[round(a, 1), round(b, 1)], height_mm=round(bb.xlen, 1), fits_h2d=bool(a <= 325 and b <= 320))


def summary():
    h = HEAD
    k = MT.kinematics(ACT)
    return dict(
        frame="leg frame: origin on the beaker axis at the shelf's underside; x across, y out along the module's centre line, z up "
              "(for the back module, the frame of base/base.step)",
        actuator=dict(model="Actuonix P16-200-22-12-P", closed_hole_to_hole=247.0, stroke=200.0, clevis_pin_behind_hinge=ACT["a"],
                      rear_pin_leg_frame=list(PIN), rear_pin_from_beaker_axis=PIN[1], rod_out=k["rod_out"], spare_at_90=k["spare_at_90"],
                      **rear_pin_swing()),
        head=dict(width_x=2 * h["half"], arm_from_axis=[h["arm_y0"], h["sleeve_out"]], arm_depth=h["arm_depth"],
                  window=window_pts(), holes=[[x, y] for x, y in BASE["holes"]], hole_d=h["hole_d"], nut_trap_af=h["nut_af"],
                  nut_trap_depth=h["nut_h"], sleeve=dict(inner_face=h["sleeve_y"], outer_face=h["sleeve_out"], wall=h["wall"],
                                                         bore=h["bore"], bore_centre=h["post_y"], bottom=h["sleeve_bot"], bore_top=h["bore_top"]),
                  arm_web=h["arm_gusset"], tab=dict(top=h["tab_top"], thickness=h["tab_t"], from_y=h["tab_y0"], web=h["tab_gusset"],
                                                    pocket=list(h["pocket"]), pocket_centre=[0.0, PIN[1]]),
                  m5_pin=dict(z=h["pin_z"], d=h["pin_d"]), profile=head_profile()),
        tube=dict(TUBE, holes_from_lower_end=tube_holes()), foot=FOOT, stand_range=S_RANGE,
        base_changes=dict(slot=dict(half_width=BASE["slot_x"], from_axis=BASE["slot_y"][0], to="through the lobe end (174)"),
                          old_slot=dict(half_width=B.SLOT["x"], from_axis=list(OLD["slot_y"])), old_holes=OLD["holes"],
                          new_holes=BASE["holes"], hole_d=BASE["hole_d"], countersink_d=BASE["csk_d"]),
    )


# --------------------------------------------------------------------------- #
# exports
# --------------------------------------------------------------------------- #
def export():
    CAD.mkdir(exist_ok=True)
    hd, tb, ft = cached("head", head), tube(), foot()
    for nm, shp in (("leg_head", hd), ("leg_tube", tb), ("leg_foot", ft)):
        cq.exporters.export(cq.Workplane().add(shp), str(CAD / f"{nm}.step"))
    # the head as printed: on its side (+x up), on the bed
    pr = hd.rotate(cq.Vector(0, 0, 0), cq.Vector(0, 1, 0), -90)
    bb = pr.BoundingBox()
    pr = pr.translate(cq.Vector(-bb.xmin, -bb.ymin, -bb.zmin))
    cq.exporters.export(cq.Workplane().add(pr), str(CAD / "leg_head_print.stl"), tolerance=0.05, angularTolerance=0.1)
    asm = cq.Assembly(name="leg_unit_S340")
    asm.add(hd, name="leg head", color=cq.Color(*PRINT))
    asm.add(tb, name="leg tube", color=cq.Color(*ALU))
    asm.add(ft, name="leg foot", color=cq.Color(*PRINT))
    for nm, shp in (("M5 height pin", m5_pin()), ("M4 base screws", m4_screws()), ("M3 bracket screw", m3_screw()),
                    ("foot screw", foot_screw())):
        asm.add(shp, name=nm, color=cq.Color(*HW))
    asm.add(K.u_bracket().moved(cq.Location(cq.Vector(*PIN))), name="P16 U-bracket (ships with the P16)", color=cq.Color(0.3, 0.32, 0.36))
    asm.save(str(CAD / "leg_unit_S340.step"))
    return [str(p.relative_to(HERE)) for p in sorted(CAD.glob("*"))]


# --------------------------------------------------------------------------- #
# main
# --------------------------------------------------------------------------- #
def main():
    t0 = time.time()
    prepare()
    if "--figures-only" in sys.argv:
        import leg_unit_figs as F
        F.all_figures(json.loads((HERE / "leg_unit.json").read_text()))
        return
    old = json.loads((HERE / "leg_unit.json").read_text()) if (HERE / "leg_unit.json").exists() else {}
    res = summary()
    res["masses"] = masses()
    res["print"] = bed_fit()
    print("summary done", round(time.time() - t0), "s", flush=True)
    if "--summary-only" in sys.argv:                 # the numbers onshape_leg.py builds from; keep earlier checks
        for k in ("files", "checks", "hr100a"):
            if k in old:
                res[k] = old[k]
        (HERE / "leg_unit.json").write_text(json.dumps(res, indent=1, default=float) + "\n")
        return
    res["files"] = export()
    print("export done", res["files"], round(time.time() - t0), "s", flush=True)
    if "--no-checks" not in sys.argv:
        res["checks"] = checks()
        res["checks"]["inside_the_u_bracket"] = bracket_check()
        print("checks", {k: v for k, v in res["checks"].items() if k != "per_leg_part_own_module"}, round(time.time() - t0), "s", flush=True)
    res["hr100a"] = {}
    for S in (330.0, 340.0, 350.0):
        r = hr_fit(S)
        res["hr100a"][str(int(S))] = r
        print("HR", S, {k: v for k, v in r.items() if k not in ("rows",)}, round(time.time() - t0), "s", flush=True)
    (HERE / "leg_unit.json").write_text(json.dumps(res, indent=1, default=float) + "\n")
    import leg_unit_figs as F
    F.all_figures(res)
    print("figures", round(time.time() - t0), "s", flush=True)


if __name__ == "__main__":
    main()
