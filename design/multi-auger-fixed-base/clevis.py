"""The clevis block on its own, with every dimension (issue #204, 17 Nov).

Ethan asked for the clevis block's dimensions.  This is the block components.py (12 Nov)
hangs under the mounting plate's floor and holes.py (17 Nov) places: a 30 x 24 x 4 mm pad
that screws to the floor with 2 x M3, and two 4 mm lugs that hold the Actuonix P16's rod
end on an M4 pin.  It builds the block as a part on its own, from the same numbers, and
changes one thing: the M3 nut pockets are hexagonal (5.8 mm across flats, 2.6 mm deep)
instead of round, so a nut can't turn while its screw is tightened from above.  It checks
the block against components.py's, re-runs the rod end's swing in the clevis over 0..90 deg
and the block, pin and screws against the one-piece base (base.py), exports the block, and
draws a dimensioned sheet.  Renders only: nothing touches Onshape.

    pip install cadquery trimesh python-fcl rtree vtk pillow numpy matplotlib
    xvfb-run -a python clevis.py      # about 1 min; writes clevis.json, clevis/ and renders/clevis_block*.png

Block frame: origin at the centre of the pad's top face (the face that sits against the
floor's underside), x along the pin (+x = the plate's plain side, away from the stepper),
y along the plate (+y = toward the rear, away from the hinge), z up; the block hangs below
z = 0.  In doserlib's unit frame (tilt 0) the origin is at (0, 95, -35.25).
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
import holes as H

HERE = Path(__file__).resolve().parent
OUT = HERE / "renders"
CAD = HERE / "clevis"

PX, PY, PT = K.BLOCK["pad"]                       # 30 x 24 x 4 pad
GAP, LUG_T, LUG_R = K.BLOCK["gap"], K.BLOCK["cheek"], K.BLOCK["lug_r"]     # 6.5 between the lugs, 4 thick, R7 ends
SX = K.BLOCK["screw_x"]                           # 11: screw axes either side of the centre line
PIN_Z = -K.CC - K.FLOOR_U                         # -9.75: pin axis below the pad's top face (= the floor's underside)
PIN_D = K.HOLE                                    # 4.25, the same as the P16's own rod-end hole (M4)
SCREW_D = 3.4                                     # M3 clearance, the same as the plate's holes
NUT_AF, NUT_H = 5.8, 2.6                          # hex pocket for an ISO 4032 M3 nut (5.5 across flats, 2.4 thick)
BOT = PIN_Z - LUG_R                               # -16.75: the lugs' lowest point
XO = GAP / 2 + LUG_T                              # 7.25: the lugs' outer faces
ORIGIN_U = (0.0, K.A, K.FLOOR_U)                  # block origin in the unit frame
FLOOR_T = K.FLOOR_TOP - K.FLOOR_U                 # 6: the plate's floor
TAB_T, BOSS, SHAFT = K.P16R["tab_t"], K.P16R["boss"], K.P16R["shaft"]   # P16 rod end: 6 mm tab, 9 mm hub, 8 mm rod
PLA = 1.24                                        # g/cm3
INK, GREY, ORANGE = "#1f1f1f", "#8a8a8a", "#f2a65a"
HW_C, FLOOR_C, ROD_C = "#9a9da3", "#c9d0da", "#c3c6cc"


# --------------------------------------------------------------------------- #
# geometry, block frame
# --------------------------------------------------------------------------- #
def hexagon(cx, cy, af):
    """Hexagon with its flats facing +-x (corners on +-y)."""
    r = af / math.sqrt(3.0)
    return [(cx + r * math.cos(math.radians(30 + 60 * i)), cy + r * math.sin(math.radians(30 + 60 * i))) for i in range(6)]


def hex_prism(cx, cy, af, z0, h):
    return cq.Workplane("XY", origin=(0, 0, z0)).polyline(hexagon(cx, cy, af)).close().extrude(h).val()


def block(pocket="hex"):
    """The clevis block: pad, two lugs rounded R7 about the pin, pin hole, two M3 holes and their nut pockets."""
    b = D.box(-PX / 2, PX / 2, -PY / 2, PY / 2, -PT, 0.0)
    for x0 in (GAP / 2, -GAP / 2 - LUG_T):
        lug = D.box(x0, x0 + LUG_T, -LUG_R, LUG_R, PIN_Z, -PT + 0.5).fuse(D.cyl(LUG_R, LUG_T, x0, 0.0, PIN_Z, d=(1, 0, 0)))
        b = b.fuse(lug)
    b = b.cut(D.cyl(PIN_D / 2, 40.0, -20.0, 0.0, PIN_Z, d=(1, 0, 0)))
    for sx in (1, -1):
        b = b.cut(D.cyl(SCREW_D / 2, 20.0, sx * SX, 0.0, -10.0))
        if pocket == "hex":
            b = b.cut(hex_prism(sx * SX, 0.0, NUT_AF, -PT - 0.01, NUT_H + 0.01))
        else:                                     # components.py's placeholder: a round pocket
            b = b.cut(D.cyl(3.2, 2.6, sx * SX, 0.0, -PT - 0.01))
    return b.clean()


def floor_patch():
    f = D.box(-22.0, 22.0, -18.0, 18.0, 0.0, FLOOR_T)
    for sx in (1, -1):
        f = f.cut(D.cyl(SCREW_D / 2, 10.0, sx * SX, 0.0, -2.0))
    return f


def m3_screws(length=10.0):
    """Socket heads (5.5 x 3) on the floor's top."""
    out = None
    for sx in (1, -1):
        s = D.cyl(2.75, 3.0, sx * SX, 0.0, FLOOR_T).fuse(D.cyl(1.5, length, sx * SX, 0.0, FLOOR_T - length))
        out = s if out is None else out.fuse(s)
    return out


def m3_nuts():
    """ISO 4032 M3 (5.5 across flats, 2.4 thick), pulled up against the pockets' roofs."""
    out = None
    for sx in (1, -1):
        n = hex_prism(sx * SX, 0.0, 5.5, -PT + NUT_H - 2.4, 2.4).cut(D.cyl(1.5, 6.0, sx * SX, 0.0, -6.0))
        out = n if out is None else out.fuse(n)
    return out


def m4_pin(length=20.0):
    """M4 socket head cap screw as the pin: head (7 x 4) on the +x lug, shank through both lugs."""
    return D.cyl(3.5, 4.0, XO, 0.0, PIN_Z, d=(1, 0, 0)).fuse(D.cyl(2.0, length, XO - length, 0.0, PIN_Z, d=(1, 0, 0)))


def nyloc():
    """DIN 985 M4 (7 across flats, 5 thick) on the -x lug."""
    pts = [(y, z + PIN_Z) for y, z in hexagon(0.0, 0.0, 7.0)]
    return cq.Workplane("YZ", origin=(-XO - 5.0, 0, 0)).polyline(pts).close().extrude(5.0).val() \
        .cut(D.cyl(2.0, 10.0, -XO - 7.0, 0.0, PIN_Z, d=(1, 0, 0)))


def rod_end(phi=0.0, shaft=26.0):
    """The P16's rod end on the pin, pointing straight down at phi = 0, turned phi deg toward -y
    (the hinge side, the way it turns as the module tilts): 6 mm tab rounded R4.5 about the pin,
    9 mm hub 8.5..14.5 mm from the pin, then the 8 mm rod."""
    tab = D.box(-TAB_T / 2, TAB_T / 2, -BOSS / 2, BOSS / 2, PIN_Z - 8.5, PIN_Z).fuse(
        D.cyl(BOSS / 2, TAB_T, -TAB_T / 2, 0.0, PIN_Z, d=(1, 0, 0)))
    tab = tab.cut(D.cyl(PIN_D / 2, 20.0, -10.0, 0.0, PIN_Z, d=(1, 0, 0)))
    r = tab.fuse(D.cyl(BOSS / 2, 6.0, 0.0, 0.0, PIN_Z - 14.5)).fuse(D.cyl(SHAFT / 2, shaft, 0.0, 0.0, PIN_Z - 14.5 - shaft))
    return r.rotate(cq.Vector(0, 0, PIN_Z), cq.Vector(1, 0, PIN_Z), -phi) if phi else r


# --------------------------------------------------------------------------- #
# checks
# --------------------------------------------------------------------------- #
def model_check(blk):
    """Is the block (with components.py's round pockets) the same solid components.py places?"""
    mine = block("round").moved(cq.Location(cq.Vector(*ORIGIN_U)))
    theirs = K.clevis_block()
    diff = mine.cut(theirs).Volume() + theirs.cut(mine).Volume()
    bb = blk.BoundingBox()
    return dict(same_as_components_py_with_round_pockets=diff < 0.01, volume_difference_mm3=round(diff, 4),
                bounding_box=dict(x=[round(bb.xmin, 2), round(bb.xmax, 2)], y=[round(bb.ymin, 2), round(bb.ymax, 2)],
                                  z=[round(bb.zmin, 2), round(bb.zmax, 2)]),
                volume_cm3=round(blk.Volume() / 1000.0, 2), mass_g_pla_solid=round(blk.Volume() / 1000.0 * PLA, 1))


def swing_check(blk, tilts=np.arange(0.0, 90.01, 2.5)):
    """The P16's rod end in the clevis, 0..90 deg tilt (components.py's actuator geometry): how far it
    turns in the clevis, its hub and rod against the block, and its tab against the pad."""
    pad = D.box(-PX / 2, PX / 2, -PY / 2, PY / 2, -PT, 0.0)
    rows, hub_w, tab_w = {}, (1e9, None), (1e9, None)
    for t in tilts:
        t = float(t)
        Mb = D.Rx(t) @ D.Tt(*ORIGIN_U)                       # block frame -> unit frame
        Ma, L_ = K.actuator_frame(np.eye(4), t)
        rod_dir = Mb[:3, :3].T @ (-Ma[:3, 2])                # the rod, pin -> base pin, in the block frame
        phi = math.degrees(math.atan2(-rod_dir[1], -rod_dir[2]))
        hub = D.cyl(BOSS / 2, 6.0 + 30.0, 0, 0, L_ - 14.5 - 30.0)        # hub and the rod below it, as components.checks
        tab = D.box(-TAB_T / 2, TAB_T / 2, -BOSS / 2, BOSS / 2, L_ - 8.5, L_).fuse(
            D.cyl(BOSS / 2, TAB_T, -TAB_T / 2, 0, L_, d=(1, 0, 0)))
        d1 = D.clearance([D.Part("hub", hub, Ma, (0, 0, 0), "r"), D.Part("blk", blk, Mb, (0, 0, 0), "b")])[0]
        d2 = D.clearance([D.Part("tab", tab, Ma, (0, 0, 0), "r"), D.Part("pad", pad, Mb, (0, 0, 0), "b")])[0]
        rows[f"{t:g}"] = dict(rod_turned_in_clevis_deg=round(phi, 1), hub_to_block=round(d1, 2), tab_to_pad=round(d2, 2))
        if d1 < hub_w[0]:
            hub_w = (d1, t)
        if d2 < tab_w[0]:
            tab_w = (d2, t)
    return dict(rod_turned_in_clevis_deg=dict(at_0=rows["0"]["rod_turned_in_clevis_deg"],
                                              at_90=rows["90"]["rod_turned_in_clevis_deg"],
                                              toward="-y, the hinge side"),
                hub_and_rod_to_block_min=dict(mm=round(hub_w[0], 2), at_tilt=hub_w[1]),
                tab_to_pad_min=dict(mm=round(tab_w[0], 2), at_tilt=tab_w[1]),
                tab_side_gap_each_side=round((GAP - TAB_T) / 2, 2),
                by_tilt=rows)


def base_check():
    """The block, its screws and nuts and the pin (two lengths) against the one-piece base (base.py's slot),
    module A (bearing 90), 0..90 deg: 1 deg steps up to 20, then 5."""
    base = B.base_station()
    Mst = D.place(90, K.SP, 0.0)
    hw = {"block": block(), "M3 x 10 screws": m3_screws(10.0), "M3 x 12 screws": m3_screws(12.0), "M3 nuts": m3_nuts(),
          "M4 x 20 pin": m4_pin(20.0), "M4 x 25 pin": m4_pin(25.0), "M4 nyloc": nyloc()}
    tilts = list(range(0, 20)) + list(range(20, 91, 5))
    out = {}
    for name, sh in hw.items():
        worst = (1e9, None)
        for t in tilts:
            M = Mst @ D.Rx(float(t)) @ D.Tt(*ORIGIN_U)
            d = D.clearance([D.Part(name, sh, M, (0, 0, 0), "m"), D.Part("base", base, np.eye(4), (0, 0, 0), "fixed")])[0]
            if d < worst[0]:
                worst = (d, t)
        row = dict(mm=round(max(worst[0], 0.0), 2), at_tilt=worst[1])
        if worst[0] <= 0.0:                       # overlap: measure it exactly
            M = Mst @ D.Rx(float(worst[1])) @ D.Tt(*ORIGIN_U)
            vol = sh.moved(C._loc(M)).intersect(base).Volume()
            row.update(overlaps=True, overlap_mm3=round(vol, 3))
        out[name] = row
        print(f"  {name} to base: {row}", flush=True)
    # the pin's free end against the slot's side wall, at 0 deg
    out["slot_half_width"] = B.SLOT["x"]
    out["pin_free_end_x"] = {"M4 x 20": -(20.0 - XO), "M4 x 25": -(25.0 - XO)}
    out["pin_top_above_shelf_underside_at_0"] = round((K.FLOOR_U + PIN_Z + 2.0) - D.BASE_BOT_U, 2)
    return out


# --------------------------------------------------------------------------- #
# files
# --------------------------------------------------------------------------- #
def export(blk):
    CAD.mkdir(parents=True, exist_ok=True)
    cq.exporters.export(cq.Workplane().add(blk), str(CAD / "clevis_block.step"))
    flipped = blk.rotate(cq.Vector(0, 0, 0), cq.Vector(1, 0, 0), 180.0)     # pad's top face on the bed, lugs up
    cq.exporters.export(cq.Workplane().add(flipped), str(CAD / "clevis_block_print.stl"), tolerance=0.02,
                        angularTolerance=0.1)
    asm = {"clevis block": blk, "M3 x 10 screws": m3_screws(), "M3 nuts": m3_nuts(), "M4 x 20 pin": m4_pin(),
           "M4 nyloc": nyloc(), "P16 rod end (0 deg)": rod_end(0.0)}
    a = cq.Assembly()
    for k, v in asm.items():
        a.add(v, name=k.replace(" ", "_").replace("(", "").replace(")", ""))
    (a.export if hasattr(a, "export") else a.save)(str(CAD / "clevis_block_with_hardware.step"))
    return ["clevis/clevis_block.step", "clevis/clevis_block_print.stl", "clevis/clevis_block_with_hardware.step"]


# --------------------------------------------------------------------------- #
# renders
# --------------------------------------------------------------------------- #
def iso_tiles():
    I = np.eye(4)
    oc = tuple(int(ORANGE[i:i + 2], 16) / 255 for i in (1, 3, 5))
    hw = (0.62, 0.63, 0.66)
    blk = [D.Part("block", block(), I, oc, "b")]
    K.tile(blk, OUT / "clevis_block_iso.png", size=(700, 560), az=-62.0, el=-32.0, zoom=0.95)
    asm = blk + [D.Part("floor", floor_patch(), I, (0.79, 0.82, 0.86), "f", opacity=0.55),
                 D.Part("m3", m3_screws(), I, hw, "h"), D.Part("nuts", m3_nuts(), I, hw, "h"),
                 D.Part("pin", m4_pin(), I, hw, "h"), D.Part("nyl", nyloc(), I, hw, "h"),
                 D.Part("rod", rod_end(0.0), I, (0.80, 0.81, 0.84), "r")]
    K.tile(asm, OUT / "clevis_block_asm.png", size=(700, 560), az=-58.0, el=-22.0, zoom=1.0)


def _poly(ax, pts, fc, ec=INK, lw=1.1, z=2, hatch=None, ls="-"):
    from matplotlib.patches import Polygon
    ax.add_patch(Polygon(np.asarray(pts), closed=True, fc=fc, ec=ec, lw=lw, zorder=z, hatch=hatch, ls=ls))


def _hid(ax, xs, ys):
    ax.plot(xs, ys, color="#4d4d4d", lw=0.75, ls=(0, (3, 2)), zorder=6)


def _cen(ax, xs, ys, col=GREY):
    ax.plot(xs, ys, color=col, lw=0.55, ls=(0, (9, 3, 2, 3)), zorder=7)


def _dim(ax, p1, p2, off, text, fs=10, ext=True, tpos=0.5, col=INK):
    B._dim(ax, p1, p2, off, text, fs=fs, ext=ext, tpos=tpos, col=col)


def _note(ax, xy, text, xytext, fs=9.5, col=INK, ha="center"):
    ax.annotate(text, xy=xy, xytext=xytext, fontsize=fs, color=col, ha=ha, va="center",
                arrowprops=dict(arrowstyle="-|>", lw=0.6, color=col, mutation_scale=7, shrinkA=2, shrinkB=0),
                bbox=dict(boxstyle="square,pad=0.15", fc="white", ec="none"), zorder=20)


def _frame(fig, rect, cx, cy, k=0.115):
    """Axes at a common scale: k inches per mm."""
    ax = fig.add_axes(rect)
    ax.set_aspect("equal")
    ax.axis("off")
    w_in, h_in = rect[2] * fig.get_figwidth(), rect[3] * fig.get_figheight()
    ax.set_xlim(cx - w_in / k / 2, cx + w_in / k / 2)
    ax.set_ylim(cy - h_in / k / 2, cy + h_in / k / 2)
    return ax


def _section_faces(shape):
    out = []
    for f in H._section(shape, 1, 0.0):
        out.append((H._wire_pts(f.outerWire(), (0, 2)), [H._wire_pts(w, (0, 2)) for w in f.innerWires()]))
    return out


def drawing(res, blk):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Circle

    fig = plt.figure(figsize=(17.0, 12.0))
    pk = NUT_AF / 2                                       # pocket half-width across the flats (x)
    pc = NUT_AF / math.sqrt(3.0)                          # pocket half-width across the corners (y)

    # ---- front view: from the hinge, x to the right, z up -------------------------------------------------------
    ax = _frame(fig, [0.005, 0.50, 0.32, 0.43], 4.0, -6.0)
    out = [(-PX / 2, 0), (PX / 2, 0), (PX / 2, -PT), (XO, -PT), (XO, BOT), (GAP / 2, BOT), (GAP / 2, -PT),
           (-GAP / 2, -PT), (-GAP / 2, BOT), (-XO, BOT), (-XO, -PT), (-PX / 2, -PT)]
    _poly(ax, out, "#fbe3c8")
    for s in (1, -1):
        _hid(ax, [s * GAP / 2, s * XO], [PIN_Z + PIN_D / 2] * 2)
        _hid(ax, [s * GAP / 2, s * XO], [PIN_Z - PIN_D / 2] * 2)
        for x in (s * SX - pk, s * SX + pk):
            _hid(ax, [x, x], [-PT, -PT + NUT_H])
        _hid(ax, [s * SX - pk, s * SX + pk], [-PT + NUT_H] * 2)
        for x in (s * SX - SCREW_D / 2, s * SX + SCREW_D / 2):
            _hid(ax, [x, x], [-PT + NUT_H, 0])
        _cen(ax, [s * SX, s * SX], [-PT - 2.5, 2.0])
    _cen(ax, [-XO - 2.5, XO + 2.5], [PIN_Z, PIN_Z])
    _cen(ax, [0, 0], [BOT - 1.5, 2.0])
    _dim(ax, (-SX, 0), (SX, 0), 4.0, f"{2 * SX:g}")
    _dim(ax, (-PX / 2, 0), (PX / 2, 0), 8.5, f"{PX:g}")
    _dim(ax, (-XO, BOT), (-GAP / 2, BOT), -3.5, f"{LUG_T:g}", fs=9.5)
    _dim(ax, (-GAP / 2, BOT), (GAP / 2, BOT), -3.5, f"{GAP:g}", fs=9.5)
    _dim(ax, (GAP / 2, BOT), (XO, BOT), -3.5, f"{LUG_T:g}", fs=9.5)
    _dim(ax, (-XO, BOT), (XO, BOT), -7.5, f"{2 * XO:g}")
    _dim(ax, (PX / 2, -PT), (PX / 2, 0), -3.5, f"{PT:g}", fs=9.5)
    ax.plot([XO + 1, PX / 2 + 9.5], [PIN_Z, PIN_Z], color=INK, lw=0.45)
    ax.plot([XO + 1, PX / 2 + 13.5], [BOT, BOT], color=INK, lw=0.45)
    _dim(ax, (PX / 2 + 8.0, PIN_Z), (PX / 2 + 8.0, 0), 0.0, f"{-PIN_Z:g}", fs=9.5, ext=False)
    ax.plot([PX / 2 + 1, PX / 2 + 13.5], [0, 0], color=INK, lw=0.45)
    _dim(ax, (PX / 2 + 12.0, BOT), (PX / 2 + 12.0, 0), 0.0, f"{-BOT:g}", fs=9.5, ext=False)
    ax.text(-PX / 2, 14.5, "FRONT  (from the hinge; plain side to the right)", fontsize=11.5, fontweight="bold",
            ha="left", va="bottom")
    ax.text(0.0, -PT / 2, "pad", fontsize=9, color=GREY, ha="center", va="center", zorder=8)
    for s in (1, -1):
        ax.text(s * (GAP / 2 + LUG_T / 2), (BOT - PT) / 2 - 2.5, "lug", fontsize=9, color=GREY, ha="center", va="center",
                rotation=90, zorder=8)

    # ---- side view: along the pin, rear (+y) to the right, z up ---------------------------------------------------
    ax = _frame(fig, [0.335, 0.50, 0.32, 0.43], 0.0, -6.0)
    arc = [(LUG_R * math.cos(a), PIN_Z + LUG_R * math.sin(a)) for a in np.linspace(0.0, -math.pi, 61)]
    prof = [(-PY / 2, 0), (PY / 2, 0), (PY / 2, -PT), (LUG_R, -PT)] + arc + [(-LUG_R, -PT), (-PY / 2, -PT)]
    _poly(ax, prof, "#fbe3c8", z=3)
    ax.add_patch(Circle((0, PIN_Z), PIN_D / 2, fc="white", ec=INK, lw=1.0, zorder=4))
    _hid(ax, [-pc, -pc], [-PT, -PT + NUT_H])
    _hid(ax, [pc, pc], [-PT, -PT + NUT_H])
    _hid(ax, [-pc, pc], [-PT + NUT_H] * 2)
    _hid(ax, [-SCREW_D / 2] * 2, [-PT + NUT_H, 0])
    _hid(ax, [SCREW_D / 2] * 2, [-PT + NUT_H, 0])
    _cen(ax, [-LUG_R - 2.5, LUG_R + 2.5], [PIN_Z, PIN_Z])
    _cen(ax, [0, 0], [BOT - 1.5, 2.0])

    def rod_outline(phi):
        top = [(4.5 * math.cos(a), 4.5 * math.sin(a)) for a in np.linspace(0, math.pi, 25)]
        pts = top + [(-4.5, -14.5), (-SHAFT / 2, -14.5), (-SHAFT / 2, -21.0), (SHAFT / 2, -21.0), (SHAFT / 2, -14.5),
                     (4.5, -14.5)]
        c, s = math.cos(math.radians(-phi)), math.sin(math.radians(-phi))
        return [(c * y - s * z, PIN_Z + s * y + c * z) for y, z in pts]

    phi90 = res["checks"]["rod_swing"]["rod_turned_in_clevis_deg"]["at_90"]
    for phi, lab, xy in ((0.0, "rod end,\n0 deg tilt", (11.5, -26.0)),
                         (phi90, f"rod end at 90 deg tilt\n(turned {phi90:.0f} deg in the clevis)", (-12.0, -24.5))):
        _poly(ax, rod_outline(phi), "none", ec="#7a7f88", lw=0.9, z=2, ls=(0, (5, 2)))
        ax.text(*xy, lab, fontsize=8.5, color="#5a5f68", ha="center", va="center")
    _dim(ax, (-PY / 2, 0), (PY / 2, 0), 5.0, f"{PY:g}")
    _dim(ax, (-LUG_R, PIN_Z), (LUG_R, PIN_Z), -(LUG_R + 3.0), f"{2 * LUG_R:g}", fs=9.5)
    ax.plot([PY / 2 + 1, PY / 2 + 11.5], [0, 0], color=INK, lw=0.45)
    ax.plot([PY / 2 + 1, PY / 2 + 11.5], [-PT, -PT], color=INK, lw=0.45)
    ax.plot([LUG_R + 1, PY / 2 + 11.5], [PIN_Z, PIN_Z], color=INK, lw=0.45)
    ax.plot([1, PY / 2 + 11.5], [BOT, BOT], color=INK, lw=0.45)
    _dim(ax, (PY / 2 + 5.0, -PT), (PY / 2 + 5.0, 0), 0.0, f"{PT:g}", fs=9.5, ext=False)
    _dim(ax, (PY / 2 + 5.0, PIN_Z), (PY / 2 + 5.0, -PT), 0.0, f"{-PIN_Z - PT:g}", fs=9.5, ext=False)
    _dim(ax, (PY / 2 + 5.0, BOT), (PY / 2 + 5.0, PIN_Z), 0.0, f"{LUG_R:g}", fs=9.5, ext=False)
    _dim(ax, (PY / 2 + 10.0, BOT), (PY / 2 + 10.0, 0), 0.0, f"{-BOT:g}", fs=9.5, ext=False)
    _note(ax, (LUG_R * math.cos(math.radians(-35)), PIN_Z + LUG_R * math.sin(math.radians(-35))), f"R{LUG_R:g}",
          (11.5, -19.5), fs=10)
    _note(ax, (-PIN_D / 2 * 0.7, PIN_Z + PIN_D / 2 * 0.7), f"Ø{PIN_D:g} thru", (-17.5, -0.5), fs=9.5)
    ax.text(-PY / 2, 14.5, "SIDE  (along the pin; hinge to the left)", fontsize=11.5, fontweight="bold", ha="left",
            va="bottom")

    # ---- iso renders --------------------------------------------------------------------------------------------
    from PIL import Image
    for rect, fn, cap in (([0.665, 0.715, 0.33, 0.25], "clevis_block_iso.png", "from below"),
                          ([0.665, 0.475, 0.33, 0.25], "clevis_block_asm.png",
                           "with its screws, nuts, M4 pin and the P16's rod end")):
        a2 = fig.add_axes(rect)
        a2.imshow(Image.open(OUT / fn))
        a2.axis("off")
        a2.text(0.02, 0.97, cap, transform=a2.transAxes, fontsize=10, color="#444444", va="top")

    # ---- bottom view: from below, x to the right, y up ----------------------------------------------------------
    ax = _frame(fig, [0.005, 0.02, 0.32, 0.43], 1.5, 1.5)
    _poly(ax, [(-PX / 2, -PY / 2), (PX / 2, -PY / 2), (PX / 2, PY / 2), (-PX / 2, PY / 2)], "#fbe3c8", z=2)
    for s in (1, -1):
        x0, x1 = sorted((s * GAP / 2, s * XO))
        _poly(ax, [(x0, -LUG_R), (x1, -LUG_R), (x1, LUG_R), (x0, LUG_R)], "#f6c99a", z=3)
        _hid(ax, [x0, x1], [PIN_D / 2] * 2)
        _hid(ax, [x0, x1], [-PIN_D / 2] * 2)
        _poly(ax, hexagon(s * SX, 0.0, NUT_AF), "white", lw=1.0, z=4)
        ax.add_patch(Circle((s * SX, 0.0), SCREW_D / 2, fc="#dddddd", ec=INK, lw=0.8, zorder=5))
        _cen(ax, [s * SX, s * SX], [-pc - 2.0, PY / 2 + 2.0])
    _cen(ax, [-PX / 2 - 2, PX / 2 + 2], [0, 0])
    _cen(ax, [0, 0], [-PY / 2 - 2, PY / 2 + 2])
    _dim(ax, (-PX / 2, PY / 2), (-SX, PY / 2), 3.5, f"{PX / 2 - SX:g}", fs=9.5)
    _dim(ax, (-SX, PY / 2), (SX, PY / 2), 3.5, f"{2 * SX:g}")
    _dim(ax, (SX, PY / 2), (PX / 2, PY / 2), 3.5, f"{PX / 2 - SX:g}", fs=9.5)
    _dim(ax, (-PX / 2, PY / 2), (PX / 2, PY / 2), 8.0, f"{PX:g}")
    _dim(ax, (-PX / 2, -PY / 2), (-PX / 2, PY / 2), 3.5, f"{PY:g}")
    _dim(ax, (PX / 2, 0), (PX / 2, PY / 2), -3.5, f"{PY / 2:g}", fs=9.5)
    _dim(ax, (SX - pk, -pc / 2), (SX + pk, -pc / 2), -4.5, f"{NUT_AF:g}", fs=9.5)
    _dim(ax, (-XO, -LUG_R), (-GAP / 2, -LUG_R), -5.5, f"{LUG_T:g}", fs=9)
    _dim(ax, (-GAP / 2, -LUG_R), (GAP / 2, -LUG_R), -5.5, f"{GAP:g}", fs=9)
    _dim(ax, (GAP / 2, -LUG_R), (XO, -LUG_R), -5.5, f"{LUG_T:g}", fs=9)
    _note(ax, (-SX - 0.9, -0.9), f"2 × Ø{SCREW_D:g} thru (M3)", (-12.5, -18.5), fs=9.5)
    _note(ax, (SX + pk * 0.4, -pc * 0.75), f"2 × hex pocket {NUT_AF:g} A/F,\n{NUT_H:g} deep (M3 nut)", (15.0, -18.5),
          fs=9.5)
    ax.text(-PX / 2 - 5.0, 22.0, "BOTTOM  (from below: the lugs and the nut pockets)", fontsize=11.5, fontweight="bold",
            ha="left", va="bottom")

    # ---- section A-A at y = 0, from the hinge, with the hardware -----------------------------------------------------
    ax = _frame(fig, [0.335, 0.02, 0.32, 0.43], 0.0, -6.0)
    layers = [(floor_patch(), FLOOR_C, None, 1), (blk, "#fbe3c8", "////", 3), (rod_end(0.0), ROD_C, None, 2),
              (m3_nuts(), HW_C, None, 4), (m3_screws(), HW_C, None, 5), (nyloc(), HW_C, None, 4), (m4_pin(), HW_C, None, 5)]
    for sh, fc, hatch, z in layers:
        for ow, inner in _section_faces(sh):
            _poly(ax, ow, fc, lw=0.8, z=z, hatch=hatch)
            for iw in inner:
                _poly(ax, iw, "white", lw=0.6, z=z)
    for s in (1, -1):
        _cen(ax, [s * SX, s * SX], [-PT - 3.0, FLOOR_T + 5.0])
    _cen(ax, [-XO - 8.0, XO + 8.0], [PIN_Z, PIN_Z])
    ax.plot([-PX / 2 - 1, -PX / 2 - 6.5], [-PT + NUT_H] * 2, color=INK, lw=0.45)
    ax.plot([-PX / 2 - 1, -PX / 2 - 6.5], [-PT] * 2, color=INK, lw=0.45)
    ax.plot([-PX / 2 - 1, -PX / 2 - 6.5], [0, 0], color=INK, lw=0.45)
    _dim(ax, (-PX / 2 - 5.0, -PT), (-PX / 2 - 5.0, -PT + NUT_H), 0.0, "", fs=9, ext=False)
    _dim(ax, (-PX / 2 - 5.0, -PT + NUT_H), (-PX / 2 - 5.0, 0), 0.0, "", fs=9, ext=False)
    ax.text(-PX / 2 - 6.0, -PT + NUT_H / 2, f"pocket {NUT_H:g}", fontsize=9, ha="right", va="center")
    ax.text(-PX / 2 - 6.0, -(PT - NUT_H) / 2 + 0.5, f"{PT - NUT_H:g}", fontsize=9, ha="right", va="center")
    _note(ax, (-20.0, FLOOR_T - 1.5), f"plate floor ({FLOOR_T:g})", (-16.0, FLOOR_T + 5.0), fs=9)
    _note(ax, (SX + 1.0, FLOOR_T + 2.6), "M3 × 10, head\non the floor", (18.5, FLOOR_T + 6.0), fs=9)
    _note(ax, (SX + 2.2, -PT + 1.0), "M3 nut", (20.0, -4.0), fs=9)
    _note(ax, (XO + 3.0, PIN_Z + 2.8), "M4 × 20 pin", (17.0, -21.5 + 6.0), fs=9)
    _note(ax, (-XO - 2.5, PIN_Z - 3.0), "M4 nyloc", (-17.5, -19.0), fs=9)
    _note(ax, (0.0, PIN_Z - 11.0), f"P16 rod end, {TAB_T:g} thick:\n{(GAP - TAB_T) / 2:g} each side in the {GAP:g} gap",
          (12.0, -25.0), fs=9)
    ax.text(-PX / 2 - 7.0, 13.5, "SECTION A-A  (through the screws and the pin)", fontsize=11.5,
            fontweight="bold", ha="left", va="bottom")

    # ---- notes ----------------------------------------------------------------------------------------------------
    ax = fig.add_axes([0.672, 0.02, 0.325, 0.44])
    ax.axis("off")
    mc, sw, bc = res["checks"]["model"], res["checks"]["rod_swing"], res["checks"]["base"]
    lines = [
        ("Where it goes", True),
        (f"On the floor's underside, on the centre line, its holes on the two new Ø{SCREW_D:g}", False),
        (f"holes ({2 * SX:g} apart, {K.A:g} behind the hinge axis). Pin {-PIN_Z:g} under the floor.", False),
        ("Hardware", True),
        ("2 × M3 × 10 socket head + 2 × M3 nut (in the hex pockets)", False),
        ("1 × M4 × 20 socket head (the pin) + 1 × M4 nyloc: snug, not tight,", False),
        ("so the lugs don't pinch the rod end", False),
        ("Printing", True),
        ("Lugs up, the pad's top face on the bed; no supports.", False),
        (f"{mc['volume_cm3']:.1f} cm³, about {mc['mass_g_pla_solid']:.0f} g of PLA if solid", False),
        ("Checks, 0-90 deg", True),
        (f"Rod end turns {sw['rod_turned_in_clevis_deg']['at_90']:.0f} deg in the clevis; its hub stays "
         f"{sw['hub_and_rod_to_block_min']['mm']:.1f} from the lugs,", False),
        (f"its tab {sw['tab_to_pad_min']['mm']:g} from the pad. Block to the base's slot: {bc['block']['mm']:g};"
         f" pin: {bc['M4 x 20 pin']['mm']:g}", False),
        (f"An M4 × 25 pin would stick {-bc['pin_free_end_x']['M4 x 25'] - B.SLOT['x']:g} past the slot's"
         " side at 0 deg: keep M4 × 20", False),
        ("Changed from the 12 Nov placeholder", True),
        ("Nut pockets are hex (5.8 A/F) instead of round (Ø6.4), so the nuts can't spin.", False),
        ("Nothing else: same outline, holes and pin position.", False),
    ]
    y = 0.99
    for t_, b_ in lines:
        ax.text(0.0, y, t_, fontsize=10.5 if b_ else 10, fontweight="bold" if b_ else "normal", va="top",
                transform=ax.transAxes)
        y -= 0.0585
    fig.text(0.005, 0.993, "Clevis block (issue #204): dimensions in mm", fontsize=18, fontweight="bold", va="top")
    fig.text(0.995, 0.993, "printed, 1 per module (3 in the tri-star); views at the same scale",
             fontsize=10.5, color="#555555", va="top", ha="right")
    fig.savefig(OUT / "clevis_block.png", dpi=110)
    plt.close(fig)
    print("  -> renders/clevis_block.png", flush=True)


# --------------------------------------------------------------------------- #
def main():
    blk = block()
    checks = dict(model=model_check(blk))
    print("model:", checks["model"], flush=True)
    checks["rod_swing"] = swing_check(blk)
    print("swing:", {k: v for k, v in checks["rod_swing"].items() if k != "by_tilt"}, flush=True)
    checks["base"] = base_check()
    files = export(blk)
    res = dict(
        what="Rod-end clevis block for the tri-star (B2) module: printed, screwed under the gearless mounting plate's"
             " floor, holds the Actuonix P16's rod end on an M4 pin",
        frame="block frame: origin at the centre of the pad's top face (against the floor's underside); x along the pin"
              " (+x = the plate's plain side), y along the plate (+y = toward the rear), z up; the block hangs below z = 0",
        origin_in_unit_frame=list(ORIGIN_U),
        overall=dict(x=PX, y=PY, z=round(-BOT, 2)),
        pad=dict(x=PX, y=PY, thickness=PT),
        lugs=dict(count=2, thickness=LUG_T, width=2 * LUG_R, gap_between=GAP, inner_faces_x=[-GAP / 2, GAP / 2],
                  outer_faces_x=[-XO, XO], over_both=2 * XO, end_radius=LUG_R, end_round_about="the pin axis",
                  hang_below_pad=round(-BOT - PT, 2)),
        pin_hole=dict(dia=PIN_D, through="both lugs", axis_below_top_face=-PIN_Z, axis_below_pad_underside=round(-PIN_Z - PT, 2),
                      axis_y=0.0),
        screw_holes=dict(dia=SCREW_D, through="the pad", x=[-SX, SX], centre_to_centre=2 * SX, from_pad_ends=PX / 2 - SX,
                         from_pad_sides=PY / 2, y=0.0),
        nut_pockets=dict(shape="hexagon", across_flats=NUT_AF, across_corners=round(2 * NUT_AF / math.sqrt(3.0), 2),
                         depth=NUT_H, opens_on="the pad's underside", flats_face="the pad's ends (x)",
                         wall_to_pad_end=round(PX / 2 - SX - NUT_AF / 2, 2), roof_under_floor=round(PT - NUT_H, 2),
                         was="round, 6.4 dia, 2.6 deep (components.py placeholder)"),
        hardware=[dict(item="M3 x 10 socket head cap screw (ISO 4762)", qty=2, note="head on the floor's top"),
                  dict(item="M3 hex nut (ISO 4032)", qty=2, note="in the hex pockets"),
                  dict(item="M4 x 20 socket head cap screw (ISO 4762)", qty=1, note="the pin; head on the +x lug"),
                  dict(item="M4 nyloc nut (DIN 985)", qty=1, note="on the -x lug; snug, not tight")],
        p16_rod_end=dict(tab=TAB_T, hole=PIN_D, hub_dia=BOSS, hub_from_pin=[8.5, 14.5], source="Actuonix P16 drawing, as components.py"),
        print=dict(orientation="lugs up, the pad's top face on the bed", supports="none"),
        files=files,
        checks=checks,
    )
    (HERE / "clevis.json").write_text(json.dumps(res, indent=1) + "\n")
    OUT.mkdir(exist_ok=True)
    iso_tiles()
    drawing(res, blk)


if __name__ == "__main__":
    main()
