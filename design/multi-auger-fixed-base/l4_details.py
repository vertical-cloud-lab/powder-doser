"""L4 details (issue #204, 24 Nov): the clevis block as changed for L4, the plate's two holes measured from
its back edge, and how each P16-200 attaches to its leg.

Ethan asked for specific dimensions and drawings for (1) the changes to the clevis block and (2) where the
two new holes go in the mounting plate, measured from the plate's back edge (not the hinge), and (3) more
detail on how the actuators attach to the legs.  leg_unit.py (24 Nov) put L4's clevis pin 120 mm behind the
hinge and said, in words, to shift the block's pad and screws.  This script builds that block, measures it
and the plate from the back edge, checks both over 0-90 deg, details the joint at the leg, and draws three
dimensioned sheets.  Renders only: nothing touches Onshape.

Two corrections come out of it:

  * The block's pad grows from 24 to 26 mm (16 ahead of the pin instead of 14).  With the screws 10 mm ahead
    of the pin, the hexagonal nut pockets' corners came within 0.65 mm of the pad's front end; 26 mm leaves
    2.65 mm.  The plate's holes don't move: 20 mm from the back edge.
  * The P16's U-bracket is 11.5 mm *outside* (Actuonix's P16 drawing, Rev B; the sheet scales to about
    1.2 mm, so about 9.1 mm inside), not 11.5 mm inside as components.py (12 Nov) and every run since took
    it.  The tab's pocket for it should be 12.1 x 8.1 mm, not 15.1 x 8.1.  The P16's rear lug (8 mm thick,
    10 wide, its end 4.5 mm from the hole) then has about 0.55 mm each side in the U, and the housing's end
    (about 4.6 mm from the hole) clears the bracket's rounded ends by about 0.85 mm.

    pip install cadquery trimesh python-fcl rtree vtk pillow numpy matplotlib
    xvfb-run -a python l4_details.py      # about 2 min; l4_details.json, clevis-l4/, renders/l4_*.png

Frames as in leg_unit.py: the unit frame (hinge axis = x through the origin, +y behind the hinge, z up,
tilt 0; the stepper on -x), the block frame of clevis.py (origin above the pin on the pad's top face, x
along the pin, +y toward the plate's rear, z up) and the leg frame (origin on the beaker axis at the shelf's
underside, y out along the module's centre line).
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np
import cadquery as cq

import doserlib as D
import concepts as C
import components as K
import base as B
import holes as H
import clevis as CL
import stands as ST
import mounts as MT
import leg_unit as LU                      # also sets L4's rear pin (mounts.base_pin)

HERE = Path(__file__).resolve().parent
OUT = HERE / "renders"
CAD = HERE / "clevis-l4"
INK, GREY = "#1f1f1f", "#8a8a8a"

# --------------------------------------------------------------------------- #
# the numbers
# --------------------------------------------------------------------------- #
A4 = LU.ACT["a"]                           # 120: clevis pin behind the hinge axis (L4)
FLOOR_U, FLOOR_TOP = K.FLOOR_U, K.FLOOR_TOP  # -35.25 / -29.25: the floor's underside and top (unit frame)
PX, PT = CL.PX, CL.PT                      # pad 30 wide (x), 4 thick
PAD_Y = (-16.0, 10.0)                      # block frame: the pad from 16 ahead of the pin to 10 behind it (26 long)
PAD_Y_24NOV = LU.L4_BLOCK["pad_y"]         # (-14, 10): what leg_unit.py drew on 24 Nov
SCREW_Y = LU.L4_BLOCK["screw_y"]           # -10: the two M3 screws, 10 ahead of the pin
SX = CL.SX                                 # 11: screws either side of the centre line
NUT_AF, NUT_H = CL.NUT_AF, CL.NUT_H        # 5.8 across flats, 2.6 deep
NUT_AC = NUT_AF * 2 / math.sqrt(3.0)       # 6.70 across corners (corners on +-y)

# the P16's U-bracket and rear lug, from Actuonix's P16 drawing (Rev B)
UB = dict(outside=11.5, width=7.5, pin_above_base=9.1, hole=4.25,
          sheet=1.2,                       # not dimensioned: scales to 1.15-1.27 mm on the drawing
          base_hole=4.25)                  # not dimensioned either; the drawing's iso view shows a round hole
UB["inside"] = round(UB["outside"] - 2 * UB["sheet"], 2)   # about 9.1
LUG = dict(t=8.0, w=10.0, end=4.5, corner_r=3.0, housing_from_pin=4.6)   # corner_r and housing: scaled
TAB = dict(top=LU.HEAD["tab_top"], t=LU.HEAD["tab_t"], y0=LU.HEAD["tab_y0"], y1=LU.HEAD["sleeve_y"],
           pocket_depth=LU.HEAD["pocket"][2], pocket_24nov=LU.HEAD["pocket"][:2],
           pocket=(round(UB["outside"] + 0.6, 2), round(UB["width"] + 0.6, 2)),
           m3_d=LU.HEAD["m3_d"], m3_nut_af=LU.HEAD["m3_nut_af"], m3_nut_h=LU.HEAD["m3_nut_h"], half=LU.HEAD["half"])
PIN = LU.PIN                               # (0, 258.5, -230): the rear pin, leg frame
LEAN = LU.rear_pin_swing()                 # 18.5..25 deg


# --------------------------------------------------------------------------- #
# geometry
# --------------------------------------------------------------------------- #
def block(pad_y=PAD_Y, screw_y=SCREW_Y):
    """The clevis block for L4, block frame: clevis.py's block with its pad from pad_y[0] to pad_y[1] (y from the
    pin, + toward the rear) and its two M3 holes and hex nut pockets at y = screw_y."""
    y0, y1 = pad_y
    b = D.box(-PX / 2, PX / 2, y0, y1, -PT, 0.0)
    for x0 in (CL.GAP / 2, -CL.GAP / 2 - CL.LUG_T):
        lug = D.box(x0, x0 + CL.LUG_T, -CL.LUG_R, CL.LUG_R, CL.PIN_Z, -PT + 0.5).fuse(
            D.cyl(CL.LUG_R, CL.LUG_T, x0, 0.0, CL.PIN_Z, d=(1, 0, 0)))
        b = b.fuse(lug)
    b = b.cut(D.cyl(CL.PIN_D / 2, 40.0, -20.0, 0.0, CL.PIN_Z, d=(1, 0, 0)))
    for sx in (1, -1):
        b = b.cut(D.cyl(CL.SCREW_D / 2, 20.0, sx * SX, screw_y, -10.0))
        b = b.cut(CL.hex_prism(sx * SX, screw_y, NUT_AF, -PT - 0.01, NUT_H + 0.01))
    return b.clean()


def m3_screws(screw_y=SCREW_Y, length=10.0):
    """2 x M3 x 10 socket head, heads (5.5 x 3) on the floor's top (block frame: the floor is z = 0..6)."""
    out = None
    for sx in (1, -1):
        s = D.cyl(2.75, 3.0, sx * SX, screw_y, CL.FLOOR_T).fuse(D.cyl(1.5, length, sx * SX, screw_y, CL.FLOOR_T - length))
        out = s if out is None else out.fuse(s)
    return out


def m3_nuts(screw_y=SCREW_Y):
    out = None
    for sx in (1, -1):
        n = CL.hex_prism(sx * SX, screw_y, 5.5, -PT + NUT_H - 2.4, 2.4).cut(D.cyl(1.5, 6.0, sx * SX, screw_y, -6.0))
        out = n if out is None else out.fuse(n)
    return out


def block_hw():
    return {"M3 x 10 screws": m3_screws(), "M3 nuts": m3_nuts(), "M4 x 20 pin": CL.m4_pin(20.0), "M4 nyloc": CL.nyloc()}


def plate_l4_u():
    """The plate as Ethan has it (PR #170's plate body without the gears, their arms and the floor's front
    wings) with the two holes at 110 behind the hinge instead of 95, in the unit frame."""
    Mown = D.W2U @ D.L.placements(0.0)["Mounting plate"][1]
    inv = C._loc(np.linalg.inv(Mown))
    pl = D.mp_bodies()["plate"]
    for sx in (1, -1):
        pl = pl.cut(D.cyl(CL.SCREW_D / 2, 12.0, sx * SX, A4 + SCREW_Y, FLOOR_U - 3.0).moved(inv))
        x0 = B.WING_CUT_X if sx > 0 else -B.WING_CUT_X - 40.0
        pl = pl.cut(D.box(x0, x0 + 40.0, -30.0, B.WING_CUT_Y, -60.0, 40.0).moved(inv))
    return pl.clean().moved(C._loc(Mown))


def u_bracket():
    """The P16's U-bracket per Actuonix's drawing, pin at the origin along x, base underneath (z < 0)."""
    o, t, w, h = UB["outside"] / 2, UB["sheet"], UB["width"], UB["pin_above_base"]
    base = D.box(-o, o, -w / 2, w / 2, -h, -h + t).cut(D.cyl(UB["base_hole"] / 2, 5, 0, 0, -h - 1))
    out = base
    for x0 in (o - t, -o):
        ch = D.box(x0, x0 + t, -w / 2, w / 2, -h, 0).fuse(D.cyl(w / 2, t, x0, 0, 0, d=(1, 0, 0)))
        out = out.fuse(ch)
    return out.cut(D.cyl(UB["hole"] / 2, 30, -15, 0, 0, d=(1, 0, 0))).clean()


def lug_profile(n=12):
    """The P16's rear lug, side view (y across, z along the actuator from the pin): 10 wide, its end 4.5 from
    the pin with R3 corners, up to the housing 4.6 the other side."""
    w, e, r, hz = LUG["w"] / 2, LUG["end"], LUG["corner_r"], LUG["housing_from_pin"]
    pts = [(w, hz)]
    for a in np.linspace(0.0, -math.pi / 2, n):
        pts.append((w - r + r * math.cos(a), -e + r + r * math.sin(a)))
    for a in np.linspace(-math.pi / 2, -math.pi, n):
        pts.append((-w + r + r * math.cos(a), -e + r + r * math.sin(a)))
    pts.append((-w, hz))
    return np.array(pts)


def lug_solid():
    p = lug_profile()
    return cq.Workplane("YZ", origin=(-LUG["t"] / 2, 0, 0)).polyline([tuple(q) for q in p]).close().extrude(LUG["t"]).val() \
        .cut(D.cyl(UB["hole"] / 2, 20, -10, 0, 0, d=(1, 0, 0)))


def housing_end():
    """The first 12 mm of the P16's housing (20 x 36, the axis 10.5 from its inner side), actuator frame."""
    w, h = K.P16R["housing"][:2]
    e = K.P16R["axis_from_edge"]
    return D.box(-w / 2, w / 2, -e, h - e, LUG["housing_from_pin"], LUG["housing_from_pin"] + 12.0)


def tab_part():
    """The leg head's tab around the pin (leg frame, cropped to the tab: x +-32, y 250.5..285.5), with the
    corrected 12.1 x 8.1 pocket, the M3 hole and its nut trap."""
    tt, tb = TAB["top"], TAB["top"] - TAB["t"]
    px, py = TAB["pocket"]
    out = D.box(-TAB["half"], TAB["half"], TAB["y0"], TAB["y1"], tb, tt)
    out = out.cut(D.box(-px / 2, px / 2, PIN[1] - py / 2, PIN[1] + py / 2, tt - TAB["pocket_depth"], tt + 0.01))
    out = out.cut(D.cyl(TAB["m3_d"] / 2, TAB["t"] + 2, 0.0, PIN[1], tb - 1))
    out = out.cut(LU.prism_xy(LU.hexagon(0.0, PIN[1], TAB["m3_nut_af"]), tb - 1, tb + TAB["m3_nut_h"]))
    return out.clean()


def m3_button():
    """M3 x 12 button head (ISO 7380: 5.7 x 1.65) from inside the U, leg frame; its nut (2.4) in the trap."""
    z_top = PIN[2] - UB["pin_above_base"] + UB["sheet"]
    hd = D.cyl(2.85, 1.65, 0.0, PIN[1], z_top)
    sh = D.cyl(1.5, 12.0, 0.0, PIN[1], z_top - 12.0)
    tb = TAB["top"] - TAB["t"]
    nut = LU.prism_xy(LU.hexagon(0.0, PIN[1], 5.5), tb + TAB["m3_nut_h"] - 2.4, tb + TAB["m3_nut_h"]) \
        .cut(D.cyl(1.5, 10, 0.0, PIN[1], tb - 2))
    return hd.fuse(sh), nut


def pin_832():
    """#8-32 x 5/8 in pan head (head 6.9 x 2.6) through cheek, lug, cheek, and a #8-32 nylon-insert lock nut
    (11/32 in = 8.7 across flats, 4.0 thick): actuator frame, pin along x."""
    o = UB["outside"] / 2
    L = 15.9
    hd = D.cyl(3.45, 2.6, o, 0, 0, d=(1, 0, 0))
    sh = D.cyl(2.08, L, o - L, 0, 0, d=(1, 0, 0))
    pts = [(y, z) for y, z in LU.hexagon(0.0, 0.0, 8.7)]
    nut = cq.Workplane("YZ", origin=(-o - 4.0, 0, 0)).polyline(pts).close().extrude(4.0).val() \
        .cut(D.cyl(2.08, 10, -o - 6, 0, 0, d=(1, 0, 0)))
    return hd.fuse(sh), nut


# --------------------------------------------------------------------------- #
# checks
# --------------------------------------------------------------------------- #
def _d(a, Ma, b, Mb):
    (_, oa), (_, ob) = ST._objs([D.Part("a", a, Ma, (0, 0, 0), "a"), D.Part("b", b, Mb, (0, 0, 0), "b")])
    return float(ST._dist(oa, ob))


def block_frame(tilt, Mst=np.eye(4)):
    return Mst @ D.Rx(float(tilt)) @ D.Tt(0.0, A4, FLOOR_U)


def swing_check(blk, tilts=np.arange(0.0, 90.01, 2.5)):
    """The P16-200's rod end in the L4 clevis over 0-90 deg (L4's kinematics, leg_unit.ACT): how far it turns
    relative to the plate, its hub and rod against the block, its tab against the pad."""
    pad = D.box(-PX / 2, PX / 2, PAD_Y[0], PAD_Y[1], -PT, 0.0)
    rows, hub_w, tab_w = {}, (1e9, None), (1e9, None)
    for t in tilts:
        t = float(t)
        Mb = block_frame(t)
        Ma, L_ = MT.act_frame(np.eye(4), t, LU.ACT)
        rod_dir = Mb[:3, :3].T @ (-Ma[:3, 2])                 # pin -> rear pin, block frame
        phi = math.degrees(math.atan2(-rod_dir[1], -rod_dir[2]))   # + = toward the hinge
        hub = D.cyl(CL.BOSS / 2, 6.0 + 30.0, 0, 0, L_ - 14.5 - 30.0)
        tab = D.box(-CL.TAB_T / 2, CL.TAB_T / 2, -CL.BOSS / 2, CL.BOSS / 2, L_ - 8.5, L_).fuse(
            D.cyl(CL.BOSS / 2, CL.TAB_T, -CL.TAB_T / 2, 0, L_, d=(1, 0, 0)))
        d1 = _d(hub, Ma, blk, Mb)
        d2 = _d(tab, Ma, pad, Mb)
        rows[f"{t:g}"] = dict(rod_from_plate_down_deg=round(phi, 1), hub_to_block=round(d1, 2), tab_to_pad=round(d2, 2))
        if d1 < hub_w[0]:
            hub_w = (d1, t)
        if d2 < tab_w[0]:
            tab_w = (d2, t)
    ph = [r["rod_from_plate_down_deg"] for r in rows.values()]
    return dict(rod_from_plate_down_deg=dict(at_0=rows["0"]["rod_from_plate_down_deg"], at_90=rows["90"]["rod_from_plate_down_deg"],
                                             min=min(ph), max=max(ph), sign="+ = toward the hinge, - = toward the plate's back edge"),
                hub_and_rod_to_block_min=dict(mm=round(hub_w[0], 2), at_tilt=hub_w[1]),
                tab_to_pad_min=dict(mm=round(tab_w[0], 2), at_tilt=tab_w[1]), by_tilt=rows)


def base_and_leg_check(blk):
    """The block and its hardware against the L4 base (leg_unit.base_l4) and the leg head, module A (bearing 90),
    0-90 deg: 1 deg steps to 20, then 5."""
    base = LU.base_l4()
    head = LU.head()
    Mst = D.place(90.0, LU.SP, 0.0)
    Mh = Mst @ LU.L2U
    shapes = {"clevis block": blk, **block_hw()}
    out = {}
    for name, sh in shapes.items():
        wb, wh = (1e9, None), (1e9, None)
        for t in list(range(0, 20)) + list(range(20, 91, 5)):
            M = block_frame(t, Mst)
            d = _d(sh, M, base, np.eye(4))
            if d < wb[0]:
                wb = (d, t)
            d = _d(sh, M, head, Mh)
            if d < wh[0]:
                wh = (d, t)
        out[name] = dict(to_base=dict(mm=round(wb[0], 2), at_tilt=wb[1]), to_leg_head=dict(mm=round(wh[0], 2), at_tilt=wh[1]))
        print(f"  {name}: base {out[name]['to_base']}, leg head {out[name]['to_leg_head']}", flush=True)
    # the pad's front end against the slot's start at 0 deg, along y (leg frame)
    out["pad_front_from_beaker_axis_at_0"] = round(LU.SP + A4 + PAD_Y[0], 2)
    out["slot_start_from_beaker_axis"] = LU.BASE["slot_y"][0]
    return out


def module_u():
    """The module at tilt 0 in the unit frame (the parts over the holes): name -> shape (placed)."""
    out = {}
    for p in K.module(0.0, with_hanger=False):
        name = p.name.split(":", 1)[1]
        if name in ("clevis block", "M3 screws", "M4 pin", "P16 rod", "P16 body", "P16 bracket", "#8-32 pin"):
            continue
        sh = plate_l4_u() if name == "Mounting plate" else p.shape.moved(C._loc(p.M))
        out[name] = sh
    return out


def over_the_holes(parts):
    """What sits over the two holes on the floor's top: the auger tube's height over a 5.5 mm head, and the
    gaps from the screw heads to the nearest parts."""
    y = A4 + SCREW_Y
    tube = parts["Auger"]
    heads = []
    for x in (-SX, SX):
        col = cq.Solid.makeCylinder(2.75, 80.0, cq.Vector(x, y, FLOOR_TOP + 0.01))
        heads.append(tube.intersect(col).BoundingBox().zmin - FLOOR_TOP)
    scr = m3_screws().moved(C._loc(D.Tt(0.0, A4, FLOOR_U)))
    near = {k: round(H.dist(scr, v), 2) for k, v in parts.items() if k not in ("Mounting plate",)}
    near = dict(sorted(near.items(), key=lambda kv: kv[1])[:5])
    return dict(auger_tube_above_floor_top_over_a_5_5mm_head=round(min(heads), 2), screws_to_nearest_parts_mm=near)


def floor_measure(pl):
    outline, holes = H.floor_outline(pl)
    rear = float(outline[:, 1].max())
    y = A4 + SCREW_Y
    band = outline[(outline[:, 1] > y - 8.0) & (outline[:, 1] < y + 8.0)]
    side = float(band[:, 0].max())
    side_neg = float(band[:, 0].min())
    rb = [h for h in holes if abs(h[1] - 124.0) < 0.5]
    use = {124.0: "rear Flexible Bracket", 58.33: "#203's tap bracket", 42.33: "#203's tap bracket (-x); +x not used",
           110.0: "new: L4 clevis block"}
    hl = []
    for x, yy, dd in holes:
        u = next((v for k, v in use.items() if abs(yy - k) < 0.5), "?")
        hl.append(dict(x=x, y_behind_hinge=yy, dia=dd, from_back_edge=round(rear - yy, 2), used_by=u))
    hl.append(dict(x="+-11", y_behind_hinge=95.0, dia=3.4, from_back_edge=round(rear - 95.0, 2),
                   used_by="17 Nov position: not used by L4 (harmless if already drilled)"))
    return dict(
        back_edge_behind_hinge=round(rear, 2),
        back_edge_straight_across=[round(float(outline[np.abs(outline[:, 1] - rear) < 0.01, 0].min()), 2),
                                   round(float(outline[np.abs(outline[:, 1] - rear) < 0.01, 0].max()), 2)],
        side_edges_at_the_holes=[round(side_neg, 2), round(side, 2)],
        new_holes=dict(dia=CL.SCREW_D, x=[-SX, SX], from_back_edge=round(rear - y, 2), behind_hinge=y,
                       centre_to_centre=2 * SX, from_centre_line=SX, from_side_edges=round(side - SX, 2),
                       from_rear_bracket_holes=dict(along=round(rb[0][1] - y, 2), across=round(abs(rb[0][0]) - SX, 2))),
        pin=dict(from_back_edge=round(rear - A4, 2), below_floor_underside=round(-CL.PIN_Z, 2), behind_hinge=A4),
        pad=dict(from_back_edge=[0.0, round(PAD_Y[1] - PAD_Y[0], 2)], flush_with_back_edge=abs(rear - (A4 + PAD_Y[1])) < 0.01),
        rear_bracket_footprint_from_back_edge=[0.0, 12.0],
        holes=hl,
    ), outline


def bracket_checks():
    """Inside the U-bracket at the leg (2D, exact for these outlines): the lug's side gaps, the M3 button head
    under the lug over the lean range, the housing over the bracket's rounded ends."""
    base_in = UB["pin_above_base"] - UB["sheet"]           # 7.9: the base's inside face below the pin
    head_top = base_in - 1.65                              # the button head's top below the pin
    worst = 1e9
    for lean in np.linspace(LEAN["lean_min_deg"], LEAN["lean_max_deg"], 27):
        a = math.radians(lean)
        p = lug_profile(40)
        # rotate the lug by the lean (its far end leans away from vertical), world z down = -z
        zz = p[:, 0] * math.sin(a) + p[:, 1] * math.cos(a)
        lowest = -float(zz.min())
        worst = min(worst, head_top - lowest)
    return dict(lug_side_gap_each_side=round((UB["inside"] - LUG["t"]) / 2, 2),
                m3_head_to_lug_min=round(worst, 2),
                housing_to_bracket_ends=round(LUG["housing_from_pin"] - UB["width"] / 2, 2),
                base_inside_below_pin=round(base_in, 2), pin_above_tab_top=round(UB["pin_above_base"] - TAB["pocket_depth"], 2),
                pocket_play_each_side=dict(x=round((TAB["pocket"][0] - UB["outside"]) / 2, 2),
                                           y=round((TAB["pocket"][1] - UB["width"]) / 2, 2)),
                pocket_24nov_play_x=round((TAB["pocket_24nov"][0] - UB["outside"]) / 2, 2),
                pin_screw_grip=UB["outside"], pin_thread_past_bracket=round(15.9 - UB["outside"], 2))


# --------------------------------------------------------------------------- #
def numbers():
    blk = block()
    old = block(PAD_Y_24NOV)
    res = dict(
        frame_block="block frame: origin on the pad's top face straight above the pin; x along the pin (+x = the plate's plain "
                    "side, away from the stepper), y along the plate (+y toward the back edge), z up",
        block=dict(
            overall=dict(x=PX, y=round(PAD_Y[1] - PAD_Y[0], 2), z=round(-CL.BOT, 2)),
            pad=dict(x=PX, y=round(PAD_Y[1] - PAD_Y[0], 2), thickness=PT, from_pin=list(PAD_Y)),
            measured_from_pad_rear_end=dict(pin=PAD_Y[1], screws=round(PAD_Y[1] - SCREW_Y, 2), pad_front_end=round(PAD_Y[1] - PAD_Y[0], 2),
                                            lugs=[round(PAD_Y[1] - CL.LUG_R, 2), round(PAD_Y[1] + CL.LUG_R, 2)]),
            screws_from_pad_front_end=round(SCREW_Y - PAD_Y[0], 2),
            pin_hole=dict(dia=CL.PIN_D, below_pad_top=-CL.PIN_Z, below_pad_underside=round(-CL.PIN_Z - PT, 2)),
            lugs=dict(t=CL.LUG_T, gap=CL.GAP, over_both=2 * CL.XO, width=2 * CL.LUG_R, end_radius=CL.LUG_R, hang_below_pad=round(-CL.BOT - PT, 2)),
            screw_holes=dict(dia=CL.SCREW_D, x=[-SX, SX], apart=2 * SX, from_pad_sides=round(PX / 2 - SX, 2)),
            nut_pockets=dict(af=NUT_AF, ac=round(NUT_AC, 2), depth=NUT_H, corners="on +-y (flats face the pad's sides)",
                             wall_to_pad_front=round(SCREW_Y - NUT_AC / 2 - PAD_Y[0], 2),
                             wall_to_pad_front_24nov=round(SCREW_Y - NUT_AC / 2 - PAD_Y_24NOV[0], 2),
                             wall_to_pad_side=round(PX / 2 - SX - NUT_AF / 2, 2)),
            volume_cm3=round(blk.Volume() / 1000, 2), mass_g_pla=round(blk.Volume() / 1000 * CL.PLA, 1),
            changes=[
                "pad 26 long instead of 24: from 16 ahead of the pin to 10 behind it (17 Nov: +-12; 24 Nov text: 14 ahead)",
                "screw holes and nut pockets 10 ahead of the pin (17 Nov: on the pin's line)",
                "nothing else: lugs, pin hole, hole and pocket sizes as on 17 Nov"],
        ),
        block_24nov_volume_cm3=round(old.Volume() / 1000, 2),
    )
    return res, blk


def main():
    OUT.mkdir(exist_ok=True)
    CAD.mkdir(exist_ok=True)
    res, blk = numbers()
    print(json.dumps(res["block"], indent=1), flush=True)
    pl = plate_l4_u()
    fl, outline = floor_measure(pl)
    res["plate"] = fl
    print(json.dumps({k: v for k, v in fl.items() if k != "holes"}, indent=1), flush=True)
    parts = module_u()
    res["plate"]["over_the_holes"] = over_the_holes(parts)
    print(res["plate"]["over_the_holes"], flush=True)
    res["bracket"] = dict(u_bracket=UB, lug=LUG, tab=TAB, lean=LEAN, checks=bracket_checks())
    print(res["bracket"]["checks"], flush=True)
    if "--no-checks" not in sys.argv:
        res["checks"] = dict(rod_swing=swing_check(blk))
        print({k: v for k, v in res["checks"]["rod_swing"].items() if k != "by_tilt"}, flush=True)
        res["checks"]["base_and_leg"] = base_and_leg_check(blk)
    res["files"] = export(blk)
    (HERE / "l4_details.json").write_text(json.dumps(res, indent=1, default=float) + "\n")
    if "--no-figures" not in sys.argv:
        import l4_details_figs as F
        F.all_figures(res, blk, pl, outline, parts)


def export(blk):
    cq.exporters.export(cq.Workplane().add(blk), str(CAD / "clevis_block_l4.step"))
    flipped = blk.rotate(cq.Vector(0, 0, 0), cq.Vector(1, 0, 0), 180.0)
    cq.exporters.export(cq.Workplane().add(flipped), str(CAD / "clevis_block_l4_print.stl"), tolerance=0.02, angularTolerance=0.1)
    asm = cq.Assembly(name="leg_tab_joint")
    asm.add(tab_part(), name="leg head tab (cropped)", color=cq.Color(0.16, 0.62, 0.56))
    m3, nut = m3_button()
    asm.add(m3, name="M3 x 12 button head", color=cq.Color(0.55, 0.56, 0.58))
    asm.add(nut, name="M3 nut", color=cq.Color(0.55, 0.56, 0.58))
    asm.add(u_bracket().moved(cq.Location(cq.Vector(*PIN))), name="P16 U-bracket (Actuonix drawing)", color=cq.Color(0.3, 0.32, 0.36))
    asm.save(str(CAD / "leg_tab_joint.step"))
    return ["clevis-l4/clevis_block_l4.step", "clevis-l4/clevis_block_l4_print.stl", "clevis-l4/leg_tab_joint.step"]


if __name__ == "__main__":
    main()
