"""Figures for l4_details.py (issue #204, 24 Nov): the L4 clevis block, the plate's holes from its back edge,
and the P16-200's joint at the leg.

    xvfb-run -a python l4_details.py        # draws these at the end
"""
from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import cadquery as cq

import doserlib as D
import concepts as C
import components as K
import base as B
import holes as H
import clevis as CL
import leg_unit as LU
import l4_details as L4

HERE = Path(__file__).resolve().parent
OUT = HERE / "renders"
INK, GREY, BLUE = "#1f1f1f", "#8a8a8a", "#3060c0"
NEW_C, PAD_C, LUG_C, FLOOR_C, HW_C = "#e8731e", "#fbe3c8", "#f6c99a", "#c9d0da", "#9a9da3"
TEAL, STEEL = "#7fc8bb", "#8d9097"


def _plt():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    return plt


def _poly(ax, pts, fc, ec=INK, lw=1.0, z=2, ls="-", hatch=None, alpha=1.0):
    from matplotlib.patches import Polygon
    ax.add_patch(Polygon(np.asarray(pts, float), closed=True, fc=fc, ec=ec, lw=lw, zorder=z, ls=ls, hatch=hatch, alpha=alpha))


def _rect(ax, x0, y0, x1, y1, **kw):
    _poly(ax, [(x0, y0), (x1, y0), (x1, y1), (x0, y1)], **kw)


def _hid(ax, xs, ys, col="#4d4d4d"):
    ax.plot(xs, ys, color=col, lw=0.75, ls=(0, (3, 2)), zorder=6)


def _cen(ax, xs, ys, col=GREY):
    ax.plot(xs, ys, color=col, lw=0.55, ls=(0, (9, 3, 2, 3)), zorder=7)


def _dim(ax, p1, p2, off, text, fs=10, ext=True, tpos=0.5, col=INK):
    B._dim(ax, p1, p2, off, text, fs=fs, ext=ext, tpos=tpos, col=col)


def _note(ax, xy, text, xytext, fs=9.5, col=INK, ha="center"):
    ax.annotate(text, xy=xy, xytext=xytext, fontsize=fs, color=col, ha=ha, va="center",
                arrowprops=dict(arrowstyle="-|>", lw=0.6, color=col, mutation_scale=7, shrinkA=2, shrinkB=0),
                bbox=dict(boxstyle="square,pad=0.15", fc="white", ec="none"), zorder=20)


def _ext(ax, xs, ys):
    ax.plot(xs, ys, color=INK, lw=0.45, zorder=7)


def _frame(fig, rect, cx, cy, k):
    """Axes at a common scale: k inches per mm, centred on (cx, cy)."""
    ax = fig.add_axes(rect)
    ax.set_aspect("equal")
    ax.axis("off")
    w_in, h_in = rect[2] * fig.get_figwidth(), rect[3] * fig.get_figheight()
    ax.set_xlim(cx - w_in / k / 2, cx + w_in / k / 2)
    ax.set_ylim(cy - h_in / k / 2, cy + h_in / k / 2)
    return ax


def _title(ax, x, y, text, fs=11.5):
    ax.text(x, y, text, fontsize=fs, fontweight="bold", ha="left", va="bottom", zorder=30)


def _sections(shape, axis, at, ij):
    out = []
    for f in H._section(shape, axis, at):
        out.append((H._wire_pts(f.outerWire(), ij), [H._wire_pts(w, ij) for w in f.innerWires()]))
    return out


def _draw_sections(ax, shape, axis, at, ij, fc, z=2, lw=0.7, hatch=None, flip=None):
    for ow, inner in _sections(shape, axis, at, ij):
        if flip is not None:
            ow = flip(ow)
            inner = [flip(w) for w in inner]
        _poly(ax, ow, fc, lw=lw, z=z, hatch=hatch)
        for iw in inner:
            _poly(ax, iw, "white", lw=0.5, z=z)


def _text_block(ax, lines, y0=0.99, dy=0.06, fs=10):
    y = y0
    for t, b in lines:
        ax.text(0.0, y, t, fontsize=fs + (0.5 if b else 0), fontweight="bold" if b else "normal", va="top", transform=ax.transAxes)
        y -= dy


# --------------------------------------------------------------------------- #
# 1. the clevis block for L4
# --------------------------------------------------------------------------- #
def block_tiles(blk):
    I = np.eye(4)
    oc = tuple(int(NEW_C[i:i + 2], 16) / 255 for i in (1, 3, 5))
    hw = (0.62, 0.63, 0.66)
    K.tile([D.Part("block", blk, I, oc, "b")], OUT / "l4_clevis_block_iso.png", size=(700, 560), az=-62.0, el=-32.0, zoom=0.95)
    floor = D.box(-24.0, 24.0, -20.0, L4.PAD_Y[1], 0.0, CL.FLOOR_T)
    for sx in (1, -1):
        floor = floor.cut(D.cyl(CL.SCREW_D / 2, 10.0, sx * L4.SX, L4.SCREW_Y, -2.0))
    hwp = L4.block_hw()
    asm = [D.Part("block", blk, I, oc, "b"), D.Part("floor", floor, I, (0.79, 0.82, 0.86), "f", opacity=0.55)]
    asm += [D.Part(k, v, I, hw, "h") for k, v in hwp.items()]
    asm.append(D.Part("rod", CL.rod_end(0.0), I, (0.80, 0.81, 0.84), "r"))
    K.tile(asm, OUT / "l4_clevis_block_asm.png", size=(700, 560), az=-58.0, el=-22.0, zoom=1.0)


def clevis_sheet(res, blk):
    plt = _plt()
    from matplotlib.patches import Circle
    b = res["block"]
    y0, y1 = L4.PAD_Y
    ys = L4.SCREW_Y
    PZ, BOT, XO, GAP, LT, LR = CL.PIN_Z, CL.BOT, CL.XO, CL.GAP, CL.LUG_T, CL.LUG_R
    PT, PX, SX = L4.PT, L4.PX, L4.SX
    pc = L4.NUT_AC / 2
    pk = L4.NUT_AF / 2
    k = 0.094
    fig = plt.figure(figsize=(18.0, 12.4))

    # ---- side view: along the pin, hinge to the left, the back edge to the right; x axis = y (block), up = z ------
    ax = _frame(fig, [0.005, 0.47, 0.36, 0.48], 0.0, -8.5, k)
    # ghost floor and the back edge
    _rect(ax, y0 - 6.0, 0.0, y1, CL.FLOOR_T, fc=FLOOR_C, ec="#6b7480", lw=0.8, z=1, alpha=0.6)
    ax.text(y0 - 5.0, CL.FLOOR_T / 2, "plate floor (6)", fontsize=8.5, color="#4b5460", va="center", zorder=3)
    ax.plot([y1, y1], [BOT - 6.0, CL.FLOOR_T + 9.0], color=BLUE, lw=1.0, ls=(0, (8, 3)), zorder=8)
    ax.text(y1 + 0.6, CL.FLOOR_T + 8.0, "plate's back edge =\npad's rear end", fontsize=9, color=BLUE, ha="left", va="top")
    arc = [(LR * math.cos(a), PZ + LR * math.sin(a)) for a in np.linspace(0.0, -math.pi, 61)]
    prof = [(y0, 0), (y1, 0), (y1, -PT), (LR, -PT)] + arc + [(-LR, -PT), (y0, -PT)]
    _poly(ax, prof, PAD_C, z=3)
    ax.add_patch(Circle((0, PZ), CL.PIN_D / 2, fc="white", ec=INK, lw=1.0, zorder=4))
    for yy in (ys - pc, ys + pc):
        _hid(ax, [yy, yy], [-PT, -PT + L4.NUT_H])
    _hid(ax, [ys - pc, ys + pc], [-PT + L4.NUT_H] * 2)
    for yy in (ys - CL.SCREW_D / 2, ys + CL.SCREW_D / 2):
        _hid(ax, [yy, yy], [-PT + L4.NUT_H, 0])
    _cen(ax, [-LR - 2.5, LR + 2.5], [PZ, PZ])
    _cen(ax, [0, 0], [BOT - 2.5, CL.FLOOR_T + 2.0])
    _cen(ax, [ys, ys], [-PT - 2.5, CL.FLOOR_T + 2.0])
    # horizontal dimensions from the rear end
    zd = BOT - 4.0
    _ext(ax, [y1, y1], [-PT - 1, zd - 1.5])
    _ext(ax, [0, 0], [BOT - 1, zd - 1.5])
    _dim(ax, (0, zd), (y1, zd), 0.0, f"{y1 - 0:g}", ext=False, fs=10.5)
    _ext(ax, [ys, ys], [-PT - 1, zd - 7.5])
    _dim(ax, (ys, zd - 6.0), (y1, zd - 6.0), 0.0, f"{y1 - ys:g}", ext=False, fs=10.5)
    _ext(ax, [y0, y0], [-PT - 1, zd - 13.5])
    _ext(ax, [y1, y1], [zd - 1.5, zd - 13.5])
    _dim(ax, (y0, zd - 12.0), (y1, zd - 12.0), 0.0, f"{y1 - y0:g}", ext=False, fs=10.5)
    _dim(ax, (y0, 0.0), (ys, 0.0), 3.0 + CL.FLOOR_T, f"{ys - y0:g}", fs=9.5)
    # vertical
    xr = y1 + 4.0
    _ext(ax, [y1 + 0.5, xr + 9.0], [-PT, -PT])
    _ext(ax, [LR + 0.5, xr + 9.0], [PZ, PZ])
    _ext(ax, [0.5, xr + 13.0], [BOT, BOT])
    _dim(ax, (xr, -PT), (xr, 0), 0.0, f"{PT:g}", fs=9.5, ext=False)
    _dim(ax, (xr, PZ), (xr, -PT), 0.0, f"{-PZ - PT:g}", fs=9.5, ext=False)
    _dim(ax, (xr, BOT), (xr, PZ), 0.0, f"{LR:g}", fs=9.5, ext=False)
    _dim(ax, (xr + 7.0, PZ), (xr + 7.0, 0), 0.0, f"{-PZ:g}", fs=9.5, ext=False)
    _dim(ax, (xr + 11.5, BOT), (xr + 11.5, 0), 0.0, f"{-BOT:g}", fs=9.5, ext=False)
    _note(ax, (LR * math.cos(math.radians(-140)), PZ + LR * math.sin(math.radians(-140))), f"R{LR:g} about the pin", (-15.0, -19.5), fs=9.5)
    _note(ax, (-CL.PIN_D / 2 * 0.7, PZ + CL.PIN_D / 2 * 0.7), f"Ø{CL.PIN_D:g} thru (M4 pin)", (-17.0, -8.0), fs=9.5)
    _note(ax, (ys - 1.0, -PT + L4.NUT_H / 2), f"hex pocket {L4.NUT_AF:g} A/F, {L4.NUT_H:g} deep (hidden)", (-14.0, CL.FLOOR_T + 12.5), fs=9)
    _title(ax, y0 - 6.0, CL.FLOOR_T + 16.0, "SIDE  (along the pin; hinge to the left, back edge to the right)")

    # ---- bottom view: from below, hinge to the left, back edge to the right; up = +x (plain side) ------------------
    ax = _frame(fig, [0.365, 0.47, 0.32, 0.48], 1.5, -2.5, k)
    _rect(ax, y0, -PX / 2, y1, PX / 2, fc=PAD_C, z=2)
    for s in (1, -1):
        x0, x1 = sorted((s * GAP / 2, s * XO))
        _rect(ax, -LR, x0, LR, x1, fc=LUG_C, z=3)
        _hid(ax, [-CL.PIN_D / 2] * 2, [x0, x1])
        _hid(ax, [CL.PIN_D / 2] * 2, [x0, x1])
        hx = [(yy, xx) for xx, yy in CL.hexagon(s * SX, ys, L4.NUT_AF)]
        _poly(ax, hx, "white", lw=1.0, z=4)
        ax.add_patch(Circle((ys, s * SX), CL.SCREW_D / 2, fc="#dddddd", ec=INK, lw=0.8, zorder=5))
        _cen(ax, [ys - pc - 2.0, ys + pc + 2.0], [s * SX, s * SX])
    _cen(ax, [y0 - 2, y1 + 2], [0, 0])
    _cen(ax, [0, 0], [-PX / 2 - 2, PX / 2 + 2])
    _cen(ax, [ys, ys], [-PX / 2 - 2, PX / 2 + 2])
    ax.plot([y1, y1], [-PX / 2 - 12, PX / 2 + 3], color=BLUE, lw=1.0, ls=(0, (8, 3)), zorder=8)
    # along, from the rear end (bottom of the view)
    xb = -PX / 2 - 4.0
    _ext(ax, [0, 0], [-XO - 0.5, xb - 1.5])
    _ext(ax, [ys, ys], [-SX - pc, xb - 7.5])
    _ext(ax, [y0, y0], [-PX / 2 - 0.5, xb - 13.5])
    _dim(ax, (0, xb), (y1, xb), 0.0, f"{y1:g}", ext=False, fs=10.5)
    _dim(ax, (ys, xb - 6.0), (y1, xb - 6.0), 0.0, f"{y1 - ys:g}", ext=False, fs=10.5)
    _dim(ax, (y0, xb - 12.0), (y1, xb - 12.0), 0.0, f"{y1 - y0:g}", ext=False, fs=10.5)
    # across, to the right of the pad
    yr = y1 + 3.0
    for v in (-PX / 2, -SX, SX, PX / 2):
        _ext(ax, [ys + 1.5 if abs(v) == SX else y1 + 0.5, yr + 7.5], [v, v])
    _dim(ax, (yr + 6.0, -SX), (yr + 6.0, SX), 0.0, f"{2 * SX:g}", ext=False, fs=10.5)
    _dim(ax, (yr + 6.0, SX), (yr + 6.0, PX / 2), 0.0, f"{PX / 2 - SX:g}", ext=False, fs=9.5)
    _dim(ax, (yr + 6.0, -PX / 2), (yr + 6.0, -SX), 0.0, f"{PX / 2 - SX:g}", ext=False, fs=9.5)
    _ext(ax, [y1 + 0.5, yr + 12.5], [PX / 2, PX / 2])
    _ext(ax, [y1 + 0.5, yr + 12.5], [-PX / 2, -PX / 2])
    _dim(ax, (yr + 11.0, -PX / 2), (yr + 11.0, PX / 2), 0.0, f"{PX:g}", ext=False, fs=10.5)
    # lugs, across, on the left
    yl = y0 - 3.0
    for v in (-XO, -GAP / 2, GAP / 2, XO):
        _ext(ax, [-LR - 0.5, yl - 2.0], [v, v])
    _dim(ax, (yl, -XO), (yl, -GAP / 2), 0.0, f"{LT:g}", ext=False, fs=8.5)
    _dim(ax, (yl, -GAP / 2), (yl, GAP / 2), 0.0, f"{GAP:g}", ext=False, fs=8.5)
    _dim(ax, (yl, GAP / 2), (yl, XO), 0.0, f"{LT:g}", ext=False, fs=8.5)
    _dim(ax, (-LR, XO), (LR, XO), 2.5, f"{2 * LR:g}", fs=8.5)
    _dim(ax, (y0, SX), (ys - pc, SX), 0.0, f"{b['nut_pockets']['wall_to_pad_front']:g}", fs=8, ext=False)
    _note(ax, (ys + 1.2, -SX - 1.2), f"2 × Ø{CL.SCREW_D:g} thru (M3)", (ys + 4.0, -PX / 2 - 3.0), fs=9)
    _note(ax, (ys - pc * 0.6, SX + 1.5), f"2 × hex pocket {L4.NUT_AF:g} A/F × {L4.NUT_H:g} deep", (ys - 1.0, PX / 2 + 5.0), fs=9)
    ax.text(y1 + 0.6, -PX / 2 - 11.0, "back edge", fontsize=8.5, color=BLUE, ha="left", va="center")
    ax.text(y0 + 0.5, PX / 2 + 0.6, "stepper side is -x (down here)", fontsize=8, color=GREY, ha="left", va="bottom")
    _title(ax, y0 - 8.0, PX / 2 + 8.0, "BOTTOM  (from below: lugs, nut pockets)")

    # ---- front view: from the hinge -------------------------------------------------------------------------
    ax = _frame(fig, [0.69, 0.47, 0.31, 0.48], 0.0, -5.0, k)
    out = [(-PX / 2, 0), (PX / 2, 0), (PX / 2, -PT), (XO, -PT), (XO, BOT), (GAP / 2, BOT), (GAP / 2, -PT),
           (-GAP / 2, -PT), (-GAP / 2, BOT), (-XO, BOT), (-XO, -PT), (-PX / 2, -PT)]
    _poly(ax, out, PAD_C)
    for s in (1, -1):
        _hid(ax, [s * GAP / 2, s * XO], [PZ + CL.PIN_D / 2] * 2)
        _hid(ax, [s * GAP / 2, s * XO], [PZ - CL.PIN_D / 2] * 2)
        for x in (s * SX - pk, s * SX + pk):
            _hid(ax, [x, x], [-PT, -PT + L4.NUT_H])
        _hid(ax, [s * SX - pk, s * SX + pk], [-PT + L4.NUT_H] * 2)
        _cen(ax, [s * SX, s * SX], [-PT - 2.5, 2.0])
    _cen(ax, [-XO - 2.5, XO + 2.5], [PZ, PZ])
    _cen(ax, [0, 0], [BOT - 1.5, 2.0])
    _dim(ax, (-SX, 0), (SX, 0), 4.0, f"{2 * SX:g}")
    _dim(ax, (-PX / 2, 0), (PX / 2, 0), 8.5, f"{PX:g}")
    _dim(ax, (-XO, BOT), (-GAP / 2, BOT), -3.5, f"{LT:g}", fs=9.5)
    _dim(ax, (-GAP / 2, BOT), (GAP / 2, BOT), -3.5, f"{GAP:g}", fs=9.5)
    _dim(ax, (GAP / 2, BOT), (XO, BOT), -3.5, f"{LT:g}", fs=9.5)
    _dim(ax, (-XO, BOT), (XO, BOT), -7.5, f"{2 * XO:g}")
    _title(ax, -PX / 2 - 2.0, 14.5, "FRONT  (from the hinge; unchanged)")
    ax.text(0.0, -PT / 2, "pad", fontsize=9, color=GREY, ha="center", va="center", zorder=8)

    # ---- iso renders ------------------------------------------------------------------------------------------
    from PIL import Image
    for rect, fn, cap in (([0.005, 0.02, 0.24, 0.27], "l4_clevis_block_iso.png", "from below"),
                          ([0.235, 0.02, 0.24, 0.27], "l4_clevis_block_asm.png", "with its screws, nuts, M4 pin and the rod end")):
        a2 = fig.add_axes(rect)
        a2.imshow(Image.open(OUT / fn))
        a2.axis("off")
        a2.text(0.02, 0.97, cap, transform=a2.transAxes, fontsize=10, color="#444444", va="top")

    # ---- changes and the Onshape edit ------------------------------------------------------------------------
    ax = fig.add_axes([0.49, 0.02, 0.50, 0.42])
    ax.axis("off")
    nb = b["nut_pockets"]
    sw = res.get("checks", {}).get("rod_swing")
    bl = res.get("checks", {}).get("base_and_leg")
    lines = [
        ("What changes from the 17 Nov block (your Onshape clevis block)", True),
        (f"1. Pad: 30 × {y1 - y0:g} (was 30 × 24). The pin is {y1:g} from its rear end and {-y0:g} from its front end (was 12 / 12).", False),
        (f"2. Screw holes and hex pockets: {y1 - ys:g} from the rear end, {ys - y0:g} from the front end (were on the pin's line).", False),
        ("3. Nothing else: lugs, R7 ends, Ø4.25 pin hole, Ø3.4 holes, 22 apart, 5.8 A/F × 2.6 pockets.", False),
        (f"Why 26, not 24: with 24 the pockets' corners come {nb['wall_to_pad_front_24nov']:g} mm from the front end;"
         f" 26 leaves {nb['wall_to_pad_front']:g}.", False),
        ("In Onshape (origin above the pin, +y toward the back edge)", True),
        (f"Pad sketch: rectangle x ±15, y from {y0:g} to +{y1:g}.  Screw holes sketch and Nut pockets sketch:", False),
        (f"move both centres from y = 0 to y = {ys:g} (x = ±11 stays).  Lug profile, Pin hole: no change.", False),
        ("Checks, 0-90° (L4: P16-200 leaning, pin 120 behind the hinge)", True),
    ]
    if sw:
        lines += [(f"The rod end turns from {-sw['rod_from_plate_down_deg']['at_0']:g}° toward the back edge (0°) to "
                   f"{sw['rod_from_plate_down_deg']['at_90']:g}° toward the hinge (90°).", False),
                  (f"Hub to the lugs ≥ {sw['hub_and_rod_to_block_min']['mm']:g} mm; tab to the pad ≥ {sw['tab_to_pad_min']['mm']:g} mm"
                   " (as on 17 Nov).", False)]
    if bl:
        lines += [(f"Block to the base's slot ≥ {bl['clevis block']['to_base']['mm']:g} mm (0°: pad front {bl['pad_front_from_beaker_axis_at_0']:g}"
                   f" from the beaker axis, slot from {bl['slot_start_from_beaker_axis']:g});", False),
                  (f"to the leg head's arm ≥ {bl['clevis block']['to_leg_head']['mm']:g} mm; screws, nuts, M4 pin and nyloc ≥ "
                   f"{min(v['to_base']['mm'] for k_, v in bl.items() if isinstance(v, dict) and k_ != 'clevis block'):g} mm.", False)]
    lines += [("Hardware and printing (unchanged)", True),
              ("2 × M3 × 10 socket head + nut; M4 × 20 socket head + nyloc (snug). Print pad-down, no supports;"
               f" {b['volume_cm3']:.1f} cm³.", False)]
    _text_block(ax, lines, dy=0.072, fs=10.5)
    fig.text(0.005, 0.993, f"Clevis block for L4 (issue #204): mm, measured from the pad's rear end, which sits flush with the plate's back edge",
             fontsize=16.5, fontweight="bold", va="top")
    fig.text(0.995, 0.968, "1 per module (3); printed; views at one scale", fontsize=10.5, color="#555555", va="top", ha="right")
    fig.savefig(OUT / "l4_clevis_block.png", dpi=110)
    plt.close(fig)
    print("  -> renders/l4_clevis_block.png", flush=True)


# --------------------------------------------------------------------------- #
# 2. the plate's holes, from its back edge
# --------------------------------------------------------------------------- #
def plate_sheet(res, blk, pl, outline, parts):
    plt = _plt()
    from matplotlib.collections import PolyCollection
    from matplotlib.patches import Circle, Rectangle
    fl = res["plate"]
    rear = fl["back_edge_behind_hinge"]
    yh = L4.A4 + L4.SCREW_Y
    SX = L4.SX
    se = fl["side_edges_at_the_holes"][1]
    fig = plt.figure(figsize=(18.0, 11.6))

    # ---- plan from above: u = distance from the back edge (to the left), v = x (plain side down) ------------------
    ax = fig.add_axes([0.005, 0.30, 0.55, 0.64])
    ax.set_aspect("equal")
    ax.axis("off")
    P = lambda x, y: (y - rear, -x)                                             # noqa: E731  back edge at u = 0
    tri = H.silhouette(pl)
    ax.add_collection(PolyCollection([[P(*p) for p in t] for t in tri], facecolor="#e4e7ec", edgecolor="#e4e7ec", lw=0.3, zorder=0))
    o = np.array([P(x, y) for x, y in outline])
    ax.fill(o[:, 0], o[:, 1], color=FLOOR_C, zorder=1)
    ax.plot(o[:, 0], o[:, 1], color=INK, lw=1.2, zorder=3)
    wall = H.wall_box(pl)
    wx, wy = wall["x"], wall["y"]
    ax.add_patch(Rectangle(P(wx[1], wy[0]), wy[1] - wy[0], wx[1] - wx[0], fc="#9aa6b8", ec=INK, lw=0.9, hatch="////", zorder=4))
    # rear bracket footprint on the floor's top (0-12 from the back edge, x +-30)
    ax.add_patch(Rectangle(P(30.0, rear - 12.0), 12.0, 60.0, fc="none", ec="#5a6b85", lw=1.0, hatch="\\\\\\", zorder=4))
    _note(ax, P(-26.0, rear - 4.0), "rear Flexible Bracket's foot\n(0-12 from the back edge)", (8.0, 44.0), fs=9, ha="left")
    # the block's pad (under the floor) and the pin line
    y0, y1 = L4.A4 + L4.PAD_Y[0], L4.A4 + L4.PAD_Y[1]
    ax.add_patch(Rectangle(P(L4.PX / 2, y0), y1 - y0, L4.PX, fill=False, ec=NEW_C, lw=1.1, ls=(0, (4, 2)), zorder=5))
    ax.plot(*zip(P(-20.0, L4.A4), P(20.0, L4.A4)), color=NEW_C, lw=0.8, ls=(0, (10, 3, 2, 3)), zorder=5)
    # holes
    for h in fl["holes"]:
        if isinstance(h["x"], str):
            for sx in (1, -1):
                c = P(sx * SX, h["y_behind_hinge"])
                ax.add_patch(Circle(c, 1.7, fill=False, ec=GREY, lw=0.9, ls=(0, (2, 1.5)), zorder=6))
            continue
        c = P(h["x"], h["y_behind_hinge"])
        new = h["used_by"].startswith("new")
        ax.add_patch(Circle(c, h["dia"] / 2, fc="white", ec=NEW_C if new else INK, lw=2.0 if new else 0.8, zorder=7))
        if new:
            ax.add_patch(Circle(c, 3.6, fill=False, ec=NEW_C, lw=1.0, zorder=7))
        ax.plot([c[0] - 2.6, c[0] + 2.6], [c[1], c[1]], color=GREY, lw=0.4, zorder=8)
        ax.plot([c[0], c[0]], [c[1] - 2.6, c[1] + 2.6], color=GREY, lw=0.4, zorder=8)
    ax.plot([-136, 4], [0, 0], color=GREY, lw=0.6, ls=(0, (10, 3, 2, 3)), zorder=2)
    ax.plot(*zip(P(0, 0), P(0, 0)), color=BLUE)
    ax.plot([-rear, -rear], [-46, 58], color=BLUE, lw=0.9, ls=(0, (10, 3, 2, 3)), zorder=8)
    ax.text(-rear, 60, "hinge axis", ha="center", va="bottom", fontsize=9.5, color=BLUE)
    ax.plot([0, 0], [-64, 62], color=BLUE, lw=1.3, zorder=8)
    ax.text(0.8, 62, "BACK EDGE\n(datum)", ha="left", va="top", fontsize=10, color=BLUE, fontweight="bold")
    # dimensions along, from the back edge (below the plate, plain side)
    ub = -se - 7.0
    for u, lab, col, lvl in ((yh, f"{rear - yh:g}", NEW_C, 0), (L4.A4, f"{rear - L4.A4:g}", NEW_C, 1), (y0, f"{rear - y0:g}", NEW_C, 2),
                             (95.0, f"({rear - 95.0:g})", GREY, 3)):
        uu = u - rear
        zl = ub - 7.0 * lvl
        ax.plot([uu, uu], [-(SX if u in (yh, 95.0) else (L4.PX / 2 if u == y0 else 0.0)) - 2.0, zl - 1.5], color=INK if col != GREY else GREY, lw=0.45)
        ax.plot([0, 0], [-se - 1.0, zl - 1.5], color=INK, lw=0.45)
        B._dim(ax, (uu, zl), (0.0, zl), 0.0, lab, fs=11 if lvl == 0 else 10, ext=False, col=col if col == GREY else INK)
    for lvl, (u, lab, col) in enumerate(((yh, "new holes", NEW_C), (L4.A4, "clevis pin (under the floor)", NEW_C),
                                         (y0, "front end of the block's pad", NEW_C), (95.0, "17 Nov holes: not used by L4", GREY))):
        ax.text(u - rear - 2.0, ub - 7.0 * lvl, lab, fontsize=9 if lvl == 0 else 8.5, color=col, ha="right", va="center",
                fontweight="bold" if lvl == 0 else "normal")
    # across: to the left of the back edge... use the right side of the drawing
    ur = 8.0
    for v in (-SX, SX):
        ax.plot([yh - rear + 2.5, ur + 9], [v, v], color=INK, lw=0.45)
    ax.plot([1, ur + 20], [-se, -se], color=INK, lw=0.45)
    ax.plot([1, ur + 20], [se, se], color=INK, lw=0.45)
    B._dim(ax, (ur, -SX), (ur, SX), 0.0, f"{2 * SX:g}", fs=11, ext=False)
    B._dim(ax, (ur + 16, -se), (ur + 16, -SX), 0.0, f"{se - SX:g}", fs=11, ext=False)
    B._dim(ax, (ur + 16, -SX), (ur + 16, 0.0), 0.0, f"{SX:g}", fs=10, ext=False)
    B._dim(ax, (ur + 16, SX), (ur + 16, se), 0.0, f"{se - SX:g}", fs=10, ext=False)
    ax.annotate(f"2 × Ø{CL.SCREW_D:g} THRU (M3)\n{rear - yh:g} from the back edge", xy=P(-SX - 1.5, yh + 1.0), xytext=(-100, 50),
                fontsize=11.5, fontweight="bold", color=NEW_C, ha="center", va="center",
                arrowprops=dict(arrowstyle="-|>", lw=0.9, color=NEW_C, mutation_scale=9, shrinkA=2, shrinkB=0),
                bbox=dict(boxstyle="square,pad=0.2", fc="white", ec="none"), zorder=20)
    ax.text(-rear + 14, 41, "STEPPER SIDE (-x)", fontsize=9, color=GREY, ha="left", va="center")
    ax.text(-rear + 14, -41, "PLAIN SIDE (+x)", fontsize=9, color=GREY, ha="left", va="center")
    ax.text(*P(0.0, 74.0), "floor, 6 thick", fontsize=9, color=INK, ha="center", va="center")
    ax.text(*P(17.0, y0 - 1.0), "block's pad (dashed, under the floor)", fontsize=8, color=NEW_C, ha="right", va="center", rotation=0,
            bbox=dict(boxstyle="square,pad=0.08", fc=FLOOR_C, ec="none"), zorder=6)
    ax.set_xlim(-rear - 12, 50)
    ax.set_ylim(-se - 36, 72)
    ax.text(-rear - 10, 70, "FLOOR FROM ABOVE: mm from the back edge (your plate: no gears, arms or front wings)",
            fontsize=11.5, fontweight="bold", ha="left", va="top")

    # ---- section along the plate at x = +11 (through the plain-side screw), back edge to the right -------------
    k = 0.075
    ax = _frame(fig, [0.56, 0.40, 0.44, 0.55], -36.0, -23.0, k)
    flipu = lambda w: np.column_stack([w[:, 0] - rear, w[:, 1]])                # noqa: E731  u from the back edge, z
    cols = {"Mounting plate": FLOOR_C, "Bracket (rear)": "#9fb1c9"}
    for name, sh in parts.items():
        if name not in cols:
            continue
        _draw_sections(ax, sh, 0, SX, (1, 2), cols[name], z=2, flip=flipu)
    Mb = D.Tt(0.0, L4.A4, L4.FLOOR_U)
    blk_u = blk.moved(C._loc(Mb))
    _draw_sections(ax, blk_u, 0, SX, (1, 2), PAD_C, z=3, hatch="////", flip=flipu)
    hw = L4.block_hw()
    for nm in ("M3 x 10 screws", "M3 nuts", "M4 x 20 pin"):
        _draw_sections(ax, hw[nm].moved(C._loc(Mb)), 0, SX, (1, 2), HW_C, z=5, flip=flipu)
    # the lugs and the pin, beyond (projected, dashed)
    arc = [(L4.A4 - rear + CL.LUG_R * math.cos(a), L4.FLOOR_U + CL.PIN_Z + CL.LUG_R * math.sin(a)) for a in np.linspace(0, -math.pi, 40)]
    ax.plot([p[0] for p in arc], [p[1] for p in arc], color="#4d4d4d", lw=0.8, ls=(0, (3, 2)), zorder=6)
    for s in (1, -1):
        ax.plot([L4.A4 - rear + s * CL.LUG_R] * 2, [L4.FLOOR_U - L4.PT, L4.FLOOR_U + CL.PIN_Z], color="#4d4d4d", lw=0.8, ls=(0, (3, 2)), zorder=6)
    _cen(ax, [L4.A4 - rear - 10, L4.A4 - rear + 10], [L4.FLOOR_U + CL.PIN_Z] * 2)
    _cen(ax, [L4.A4 - rear] * 2, [L4.FLOOR_U + CL.PIN_Z - 9, L4.FLOOR_TOP + 4])
    _cen(ax, [yh - rear] * 2, [L4.FLOOR_U - L4.PT - 6, L4.FLOOR_TOP + 30])
    ax.plot([0, 0], [L4.FLOOR_U - 36, L4.FLOOR_TOP + 30], color=BLUE, lw=1.2, zorder=8)
    ax.text(0.8, L4.FLOOR_TOP + 29, "back edge", fontsize=9.5, color=BLUE, ha="left", va="top", fontweight="bold")
    zl = L4.FLOOR_U - 19.5
    ax.plot([yh - rear] * 2, [L4.FLOOR_U - L4.PT - 1, zl - 1.5], color=INK, lw=0.45)
    ax.plot([L4.A4 - rear] * 2, [L4.FLOOR_U + CL.PIN_Z - 7.5, zl - 6.0], color=INK, lw=0.45)
    ax.plot([y0 - rear] * 2, [L4.FLOOR_U - L4.PT - 1, zl - 10.5], color=INK, lw=0.45)
    B._dim(ax, (yh - rear, zl), (0, zl), 0.0, f"{rear - yh:g}", fs=10.5, ext=False)
    B._dim(ax, (L4.A4 - rear, zl - 4.5), (0, zl - 4.5), 0.0, f"{rear - L4.A4:g}", fs=10.5, ext=False)
    B._dim(ax, (y0 - rear, zl - 9), (0, zl - 9), 0.0, f"{rear - y0:g}", fs=10.5, ext=False)
    ax.plot([0, 0], [L4.FLOOR_U, zl - 10.5], color=BLUE, lw=0.45)
    B._dim(ax, (4.0, L4.FLOOR_U), (4.0, L4.FLOOR_TOP), 0.0, "6", fs=9.5, ext=False)
    B._dim(ax, (4.0, L4.FLOOR_U + CL.PIN_Z), (4.0, L4.FLOOR_U), 0.0, f"{-CL.PIN_Z:g}", fs=9.5, ext=False)
    ax.plot([L4.A4 - rear + 3, 6.0], [L4.FLOOR_U + CL.PIN_Z] * 2, color=INK, lw=0.45)
    oh = fl["over_the_holes"]
    zt = L4.FLOOR_TOP + oh["auger_tube_above_floor_top_over_a_5_5mm_head"]
    B._dim(ax, (yh - rear - 7.0, L4.FLOOR_TOP), (yh - rear - 7.0, zt), 0.0, f"{oh['auger_tube_above_floor_top_over_a_5_5mm_head']:.1f}",
           fs=9, ext=False)
    ax.plot([-78.0, -2.0], [zt, zt], color="#3a7fc0", lw=1.0, ls=(0, (6, 3)), zorder=6)
    notes = [((yh - rear - 1.0, L4.FLOOR_TOP + 2.5), "M3 × 10, head on the floor", (-52.0, L4.FLOOR_TOP + 10.0)),
             ((yh - rear + 1.5, L4.FLOOR_U - 3.0), "nut in a hex pocket", (-50.0, L4.FLOOR_U - 12.0)),
             ((L4.A4 - rear + 3.5, L4.FLOOR_U + CL.PIN_Z + 1.5), "M4 pin (cut through its head)", (-46.0, L4.FLOOR_U - 22.0)),
             ((-5.0, L4.FLOOR_TOP + 9.0), "rear Flexible Bracket (cut)", (-36.0, L4.FLOOR_TOP + 33.0)),
             ((-60.0, zt), "underside of the auger tube (beyond)", (-58.0, zt + 7.0))]
    for xy, t, xt in notes:
        _note(ax, xy, t, xt, fs=9)
    ax.text(0.0, 1.0, f"SECTION at x = +{SX:g}, through a screw (back edge to the right)", transform=ax.transAxes, fontsize=11.5,
            fontweight="bold", ha="left", va="top")

    # ---- table and notes ---------------------------------------------------------------------------------------
    ax = fig.add_axes([0.565, 0.02, 0.43, 0.36])
    ax.axis("off")
    nh = fl["new_holes"]
    lines = [("In an Onshape sketch on the floor's top face", True),
             (f"Two Ø{nh['dia']:g} circles, {nh['centre_to_centre']:g} apart, {nh['from_centre_line']:g} either side of the centre line,", False),
             (f"centres {nh['from_back_edge']:g} from the back edge. Extrude, remove, through all (6 thick).", False),
             ("Cross-checks (mm)", True),
             (f"{nh['from_side_edges']:g} from each side edge (the floor is {2 * se:g} wide there); {nh['from_rear_bracket_holes']['along']:g} in front of"
              f" and {nh['from_rear_bracket_holes']['across']:g} inboard of", False),
             ("the rear bracket's holes (6 from the back edge); 110 behind the hinge axis.", False),
             (f"Screw heads: {oh['screws_to_nearest_parts_mm']['Bracket (rear)']:g} from the rear bracket, "
              f"{oh['screws_to_nearest_parts_mm']['Stepper (NEMA 11)']:g} from the stepper, "
              f"{oh['screws_to_nearest_parts_mm']['Auger']:g} from the auger.", False),
             (f"The auger tube is {oh['auger_tube_above_floor_top_over_a_5_5mm_head']:.1f} over the floor there:"
              " fit the block before the auger goes in.", False),
             ("The block: its pad's rear end flush with the back edge; pin 10 from it, 9.75 under the floor.", False),
             ("Already drilled the 17 Nov holes (35 from the back edge)? They can stay: nothing uses them.", False)]
    _text_block(ax, lines, dy=0.092, fs=10.5)
    # holes table (left bottom)
    ax = fig.add_axes([0.02, 0.02, 0.52, 0.22])
    ax.axis("off")
    rows = [["Hole", "From back edge", "Behind hinge", "Used by"]]
    for h in sorted(fl["holes"], key=lambda h: h["from_back_edge"]):
        xs = h["x"] if isinstance(h["x"], str) else f"{h['x']:+g}"
        rows.append([f"Ø{h['dia']:g} at x = {xs}", f"{h['from_back_edge']:g}", f"{h['y_behind_hinge']:g}", h["used_by"]])
    tb = ax.table(cellText=rows[1:], colLabels=rows[0], loc="upper left", cellLoc="left", colLoc="left",
                  colWidths=[0.20, 0.15, 0.13, 0.52])
    tb.auto_set_font_size(False)
    tb.set_fontsize(9.5)
    tb.scale(1.0, 1.32)
    for (r, c), cell in tb.get_celld().items():
        cell.set_edgecolor("#bbbbbb")
        if r == 0:
            cell.set_text_props(fontweight="bold")
        elif rows[r][3].startswith("new"):
            cell.set_text_props(color=NEW_C, fontweight="bold")
    fig.text(0.005, 0.993, "Mounting plate: the two holes for the L4 clevis block, measured from the plate's back edge (issue #204)",
             fontsize=16.5, fontweight="bold", va="top")
    fig.savefig(OUT / "l4_plate_holes.png", dpi=110)
    plt.close(fig)
    print("  -> renders/l4_plate_holes.png", flush=True)


# --------------------------------------------------------------------------- #
# 3. the P16-200 at the leg
# --------------------------------------------------------------------------- #
def joint_parts(lean=25.0, explode=0.0):
    """The tab (cropped), the U-bracket, the M3 button head and nut, the P16's rear end, the #8-32 pin and lock
    nut, all in the leg frame; ``explode`` pulls them apart along their assembly directions."""
    PIN = np.array(L4.PIN)
    e = explode
    teal = (0.50, 0.78, 0.73)
    steel, dark, alu = (0.62, 0.63, 0.66), (0.30, 0.32, 0.36), (0.80, 0.81, 0.84)
    m3, nut = L4.m3_button()
    ps = [D.Part("tab", L4.tab_part(), np.eye(4), teal, "t"),
          D.Part("bracket", L4.u_bracket(), D.Tt(*(PIN + [0, 0, 1.2 * e])), dark, "b"),
          D.Part("m3", m3, D.Tt(0, 0, 3.2 * e), steel, "h"),
          D.Part("m3 nut", nut, D.Tt(0, 0, -1.2 * e), steel, "h")]
    Ma = D.Tt(*(PIN + [0, 0, 2.4 * e])) @ D.Rx(lean)          # top leans inward (-y), as in L4
    body = L4.lug_solid().fuse(L4.housing_end())
    ps.append(D.Part("P16-200 (rear end)", body, Ma, dark, "a"))
    hd, ln = L4.pin_832()
    ps.append(D.Part("#8-32 pin", hd, D.Tt(*(PIN + [1.6 * e, 0, 2.4 * e])), steel, "h"))
    ps.append(D.Part("lock nut", ln, D.Tt(*(PIN + [-1.6 * e, 0, 2.4 * e])), steel, "h"))
    return ps


def joint_tiles():
    for ex, fn in ((0.0, "l4_joint_iso.png"), (14.0, "l4_joint_exploded.png")):
        ps = joint_parts(25.0, ex)
        K.tile(ps, OUT / fn, size=(760, 760), az=-40.0, el=24.0, zoom=1.0)


def joint_sheet(res):
    plt = _plt()
    from matplotlib.patches import Circle, Arc
    from PIL import Image
    ub, lug, tab, ck = L4.UB, L4.LUG, L4.TAB, res["bracket"]["checks"]
    PIN = L4.PIN
    pz = PIN[2]
    tt, tb = tab["top"], tab["top"] - tab["t"]
    o, t, w, h = ub["outside"] / 2, ub["sheet"], ub["width"], ub["pin_above_base"]
    zb = pz - h                                          # bracket base underside (= pocket floor)
    k = 0.105
    fig = plt.figure(figsize=(19.0, 12.6))

    # ---- iso: exploded and assembled ---------------------------------------------------------------------------
    for rect, fn, cap in (([0.0, 0.50, 0.215, 0.44], "l4_joint_exploded.png", "exploded"),
                          ([0.20, 0.50, 0.215, 0.44], "l4_joint_iso.png", "assembled (the P16 at 25°)")):
        a2 = fig.add_axes(rect)
        a2.imshow(Image.open(OUT / fn))
        a2.axis("off")
        a2.text(0.03, 0.98, cap, transform=a2.transAxes, fontsize=10.5, color="#333333", va="top")

    # ---- section A-A through the pin, looking out along +y (x to the right, z up) -------------------------------
    ax = _frame(fig, [0.42, 0.47, 0.30, 0.47], 0.0, pz - 3.5, k)
    _rect(ax, -18.0, tb, 18.0, tt - tab["pocket_depth"], fc=TEAL, lw=0.9, z=2, hatch="////")
    px = tab["pocket"][0] / 2
    _rect(ax, -18.0, tt - tab["pocket_depth"], -px, tt, fc=TEAL, lw=0.9, z=2, hatch="////")
    _rect(ax, px, tt - tab["pocket_depth"], 18.0, tt, fc=TEAL, lw=0.9, z=2, hatch="////")
    ax.plot([-18.0, -18.0], [tb - 1, tt + 1], color=INK, lw=0.6, ls=(0, (6, 2)), zorder=3)
    ax.plot([18.0, 18.0], [tb - 1, tt + 1], color=INK, lw=0.6, ls=(0, (6, 2)), zorder=3)
    # M3 hole and the nut trap (cut), screw and nut
    nh = tab["m3_nut_af"] / 2
    _rect(ax, -tab["m3_d"] / 2, tb + tab["m3_nut_h"], tab["m3_d"] / 2, tt - tab["pocket_depth"], fc="white", lw=0.6, z=3)
    _rect(ax, -nh, tb, nh, tb + tab["m3_nut_h"], fc="white", lw=0.6, z=3)
    _rect(ax, -2.75, tb + tab["m3_nut_h"] - 2.4, 2.75, tb + tab["m3_nut_h"], fc=STEEL, lw=0.7, z=5)
    _rect(ax, -1.5, zb + t - 12.0, 1.5, zb + t, fc=STEEL, lw=0.7, z=5)
    hz = zb + t
    head = [(-2.85, hz)] + [(2.85 * math.cos(a), hz + 1.65 * math.sin(a)) for a in np.linspace(math.pi, 0, 30)] + [(2.85, hz)]
    _poly(ax, head, STEEL, lw=0.7, z=6)
    # bracket (U), cut
    _rect(ax, -o, zb, o, zb + t, fc="#4b4f57", lw=0.7, z=4)
    _rect(ax, -o, zb, -o + t, pz + w / 2, fc="#4b4f57", lw=0.7, z=4)
    _rect(ax, o - t, zb, o, pz + w / 2, fc="#4b4f57", lw=0.7, z=4)
    # lug (cut through the pin plane: 8 thick), the housing above
    lz0 = pz - lug["end"]
    _rect(ax, -lug["t"] / 2, lz0, lug["t"] / 2, pz + lug["housing_from_pin"], fc="#6b7079", lw=0.7, z=4)
    hw_, hz0 = K.P16R["housing"][0] / 2, pz + lug["housing_from_pin"]
    _rect(ax, -hw_, hz0, hw_, hz0 + 9.0, fc="none", ec="#55595f", lw=0.9, z=4, ls=(0, (5, 2)))
    ax.text(0.0, hz0 + 4.5, "P16-200 housing, 20 thick (dashed)", fontsize=8.5, color="#444444", ha="center", va="center", zorder=6)
    # #8-32 pin along x, head + lock nut
    _rect(ax, -o - 4.0, pz - 2.08, o + 2.6, pz + 2.08, fc=STEEL, lw=0.7, z=7)
    _rect(ax, o, pz - 3.45, o + 2.6, pz + 3.45, fc=STEEL, lw=0.7, z=7)
    _rect(ax, -o - 4.0, pz - 4.35, -o, pz + 4.35, fc=STEEL, lw=0.7, z=7)
    _cen(ax, [-o - 6, o + 5], [pz, pz])
    _cen(ax, [0, 0], [tb - 2.5, hz0 + 11])
    # dimensions
    xl = -o - 8.0
    _ext(ax, [-o - 0.5, xl - 1.5], [zb, zb])
    _ext(ax, [-o - 4.5, xl - 6.5], [pz, pz])
    _ext(ax, [-18.5, xl - 6.5], [tt, tt])
    _ext(ax, [-18.5, xl - 1.5], [tb, tb])
    _dim(ax, (xl, zb), (xl, pz), 0.0, f"{h:g}", fs=9.5, ext=False)
    _dim(ax, (xl - 5.0, tt), (xl - 5.0, pz), 0.0, f"{ck['pin_above_tab_top']:g}", fs=9.5, ext=False)
    _dim(ax, (-o, pz + w / 2), (o, pz + w / 2), 11.5, f"bracket {ub['outside']:g} outside", fs=9)
    _ext(ax, [-px, -px], [tt - 1.2, tb - 8.0])
    _ext(ax, [px, px], [tt - 1.2, tb - 8.0])
    _dim(ax, (-px, tb - 6.5), (px, tb - 6.5), 0.0, f"pocket {tab['pocket'][0]:g}", fs=9, ext=False)
    _dim(ax, (o + 0.0, tt - tab["pocket_depth"]), (o + 0.0, tt), -2.5, f"{tab['pocket_depth']:g}", fs=8.5)
    _dim(ax, (-lug["t"] / 2, lz0), (lug["t"] / 2, lz0), -2.4, f"lug {lug['t']:g}", fs=8.5)
    _note(ax, (lug["t"] / 2 + 0.3, pz - 3.0), f"≈{ck['lug_side_gap_each_side']:g} each side\n(about {ub['inside']:g} inside)", (13.5, pz - 9.0), fs=8.5)
    _note(ax, (1.8, hz + 1.7), f"M3 × 12 button head, {ck['m3_head_to_lug_min']:g} under the lug", (12.5, zb - 3.5), fs=8.5)
    _note(ax, (2.2, tb + 1.0), f"M3 nut in a {tab['m3_nut_af']:g} A/F × {tab['m3_nut_h']:g} trap", (13.5, tb - 10.0), fs=8.5)
    _note(ax, (o + 1.3, pz + 3.0), "#8-32 × 5/8 in\n(ships with the P16)", (16.0, pz + 11.0), fs=8.5)
    _note(ax, (-o - 2.0, pz + 3.5), "#8-32 lock nut", (-15.0, pz + 9.5), fs=8.5)
    _note(ax, (o - t / 2, pz + w / 2 - 0.5), f"{t:g} sheet (scaled)", (16.0, pz + 4.5), fs=8)
    ax.text(-17.5, tb + 1.0, "tab (8)", fontsize=8.5, color=INK, ha="left", va="bottom", zorder=8,
            bbox=dict(boxstyle="square,pad=0.05", fc="white", ec="none"))
    _title(ax, -24.0, hz0 + 15.5, "SECTION A-A through the pin, looking outward")

    # ---- side view along x (y = from the beaker axis to the right; z up) ---------------------------------------
    k2 = 0.068
    ax = _frame(fig, [0.715, 0.47, 0.28, 0.47], 262.0, pz - 4.0, k2)
    # tab and its web, the sleeve's inner face
    yi = tab["y1"]
    _poly(ax, [(tab["y0"], tt), (yi, tt), (yi, tb - 15.5), (yi - 15.5, tb), (tab["y0"], tb)], TEAL, lw=1.0, z=2)
    _rect(ax, yi, tb - 22.0, yi + 6.0, tt + 34.0, fc=TEAL, lw=1.0, z=2)
    ax.text(yi + 3.0, tt + 20.0, "sleeve wall", rotation=90, fontsize=8, ha="center", va="center", zorder=8)
    py = tab["pocket"][1] / 2
    _rect(ax, PIN[1] - py, tt - tab["pocket_depth"], PIN[1] + py, tt, fc="white", lw=0.6, z=3)
    _hid(ax, [PIN[1] - 1.7] * 2, [tb, tt - 1])
    _hid(ax, [PIN[1] + 1.7] * 2, [tb, tt - 1])
    # bracket cheek outline (7.5 wide, R3.75 end) and base
    ch = [(PIN[1] - w / 2, zb)] + [(PIN[1] + w / 2 * math.cos(a), pz + w / 2 * math.sin(a)) for a in np.linspace(math.pi, 0, 30)] + [(PIN[1] + w / 2, zb)]
    _poly(ax, ch, "#4b4f57", lw=0.8, z=4)
    ax.add_patch(Circle((PIN[1], pz), 2.08, fc=STEEL, ec=INK, lw=0.6, zorder=8))
    # the P16 lug + housing at the two extremes of its lean
    for lean, ls, col in ((L4.LEAN["lean_min_deg"], (0, (5, 2)), "#7a7f88"), (L4.LEAN["lean_max_deg"], "-", INK)):
        a = math.radians(lean)
        R = np.array([[math.cos(a), -math.sin(a)], [math.sin(a), math.cos(a)]])   # top leans inward (-y), wide side out
        lp = L4.lug_profile(16)
        housing = np.array([(-K.P16R["axis_from_edge"], lug["housing_from_pin"]), (K.P16R["housing"][1] - K.P16R["axis_from_edge"], lug["housing_from_pin"]),
                            (K.P16R["housing"][1] - K.P16R["axis_from_edge"], 22.0), (-K.P16R["axis_from_edge"], 22.0)])
        for shp in (lp, housing):
            q = shp @ R.T
            # the actuator's local +y (housing's wide side) faces outward (+y), its axis leans in
            q = np.column_stack([PIN[1] + q[:, 0], pz + q[:, 1]])
            _poly(ax, q, "none", ec=col, lw=1.0, z=6, ls=ls)
    ax.text(PIN[1] - 26.0, pz + 30.0, f"P16-200 at {L4.LEAN['lean_max_deg']:.0f}° (solid)\nand {L4.LEAN['lean_min_deg']:.1f}° (dashed)",
            fontsize=8.5, ha="left", va="center", zorder=9, bbox=dict(boxstyle="square,pad=0.1", fc="white", ec="none"))
    _cen(ax, [PIN[1]] * 2, [tb - 3, pz + 8])
    _cen(ax, [PIN[1] - 7, PIN[1] + 7], [pz, pz])
    # dims along y
    zd = tb - 24.0
    for yy in (tab["y0"], PIN[1], yi):
        _ext(ax, [yy, yy], [tb - 1 if yy != yi else tb - 23, zd - 1.5])
    _dim(ax, (tab["y0"], zd), (PIN[1], zd), 0.0, f"{PIN[1] - tab['y0']:g}", fs=9.5, ext=False)
    _dim(ax, (PIN[1], zd), (yi, zd), 0.0, f"{yi - PIN[1]:g}", fs=9.5, ext=False)
    a_ = math.radians(L4.LEAN["lean_max_deg"])
    ax.plot([PIN[1], PIN[1] - 33.0 * math.sin(a_)], [pz, pz + 33.0 * math.cos(a_)], color="#6b6b6b", lw=0.8, ls=(0, (9, 3, 2, 3)), zorder=7)
    ax.text(PIN[1] - 33.0 * math.sin(a_) - 1.0, pz + 33.0 * math.cos(a_), "P16 axis, up to\nthe rod end", fontsize=8, color="#555555", ha="right", va="center")
    ax.text(PIN[1], zd - 4.5, f"pin {PIN[1]:g} from the beaker axis, {-pz:g} under the shelf's underside", fontsize=9, ha="center", va="top")
    _ext(ax, [tab["y0"] - 0.5, tab["y0"] - 8.0], [tt, tt])
    _ext(ax, [tab["y0"] - 0.5, tab["y0"] - 8.0], [tb, tb])
    _ext(ax, [PIN[1] - 2.5, tab["y0"] - 13.0], [pz, pz])
    _dim(ax, (tab["y0"] - 6.0, tb), (tab["y0"] - 6.0, tt), 0.0, f"{tab['t']:g}", fs=9, ext=False)
    _dim(ax, (tab["y0"] - 11.0, tt), (tab["y0"] - 11.0, pz), 0.0, f"{ck['pin_above_tab_top']:g}", fs=9, ext=False)
    ax.text(tab["y0"] - 12.5, tt - 4.0, f"tab top {-tt:g}\nunder the shelf", fontsize=8.5, ha="right", va="center")
    _note(ax, (PIN[1] + w / 2 + 0.2, pz + 1.5), f"housing {ck['housing_to_bracket_ends']:g} over the\nbracket's R{w / 2:g} ends", (PIN[1] + 17.0, pz + 13.0), fs=8.5)
    ax.text(tab["y0"] - 20.0, tt + 44.0, "← beaker axis", fontsize=8.5, color=GREY, ha="left")
    _title(ax, tab["y0"] - 22.0, tt + 49.0, "SIDE  (along the pin)")

    # ---- plan of the tab's top ---------------------------------------------------------------------------------
    k3 = 0.050
    ax = _frame(fig, [0.0, 0.02, 0.30, 0.43], 2.0, 280.0, k3)
    _rect(ax, -tab["half"], tab["y0"], tab["half"], yi, fc=TEAL, lw=1.0, z=2)
    _rect(ax, -tab["half"], yi, tab["half"], yi + 6.0 + 20.6 + 6.0, fc="#a6d8cf", lw=0.8, z=2)
    _rect(ax, -10.3, yi + 6.0, 10.3, yi + 26.6, fc="white", lw=0.8, z=3)
    ax.text(0.0, yi + 16.3, "sleeve bore\n20.6 sq.", fontsize=8, ha="center", va="center", color=GREY, zorder=4)
    pxh, pyh = tab["pocket"][0] / 2, tab["pocket"][1] / 2
    _rect(ax, -pxh, PIN[1] - pyh, pxh, PIN[1] + pyh, fc="white", lw=1.0, z=4)
    ax.add_patch(Circle((0.0, PIN[1]), tab["m3_d"] / 2, fc="#dddddd", ec=INK, lw=0.8, zorder=5))
    hx = LU.hexagon(0.0, PIN[1], tab["m3_nut_af"])
    _poly(ax, hx, "none", ec="#4d4d4d", lw=0.7, z=5, ls=(0, (3, 2)))
    _cen(ax, [-pxh - 3, pxh + 3], [PIN[1], PIN[1]])
    _cen(ax, [0, 0], [tab["y0"] - 3, yi + 3])
    _dim(ax, (-pxh, PIN[1] + pyh), (pxh, PIN[1] + pyh), 4.0, f"{tab['pocket'][0]:g}", fs=9.5)
    _dim(ax, (pxh, PIN[1] - pyh), (pxh, PIN[1] + pyh), -4.0, f"{tab['pocket'][1]:g}", fs=9.5)
    _ext(ax, [-tab["half"] - 0.5, -tab["half"] - 10], [tab["y0"], tab["y0"]])
    _ext(ax, [-pxh - 3.5, -tab["half"] - 10], [PIN[1], PIN[1]])
    _ext(ax, [-tab["half"] - 0.5, -tab["half"] - 10], [yi, yi])
    _dim(ax, (-tab["half"] - 8.0, tab["y0"]), (-tab["half"] - 8.0, PIN[1]), 0.0, f"{PIN[1] - tab['y0']:g}", fs=9.5, ext=False)
    _dim(ax, (-tab["half"] - 8.0, PIN[1]), (-tab["half"] - 8.0, yi), 0.0, f"{yi - PIN[1]:g}", fs=9.5, ext=False)
    _dim(ax, (-tab["half"], tab["y0"]), (tab["half"], tab["y0"]), -4.0, f"{2 * tab['half']:g}", fs=9.5)
    _note(ax, (0.9, PIN[1] - 0.9), f"Ø{tab['m3_d']:g} thru; M3 nut trap\n{tab['m3_nut_af']:g} A/F × {tab['m3_nut_h']:g} underneath",
          (19.0, PIN[1] - 18.0), fs=8.5)
    _note(ax, (pxh - 1.0, PIN[1] + pyh - 0.5), f"pocket {tab['pocket'][0]:g} × {tab['pocket'][1]:g} × {tab['pocket_depth']:g} deep\n"
          f"(Onshape leg has {tab['pocket_24nov'][0]:g} × {tab['pocket_24nov'][1]:g}: change to {tab['pocket'][0]:g})", (14.0, PIN[1] + 22.0), fs=8.5,
          col=NEW_C)
    ax.text(-tab["half"], tab["y0"] - 9.0, "beaker axis ↓ (y from it)", fontsize=8.5, color=GREY, ha="left", va="top")
    _title(ax, -tab["half"] - 16.0, yi + 36.0, "TAB, from above (leg frame)")

    # ---- the bracket as Actuonix draws it ------------------------------------------------------------------------
    k4 = 0.088
    ax = _frame(fig, [0.30, 0.02, 0.19, 0.43], 1.0, -6.0, k4)
    # front (U) and side, side by side
    xo = -9.5
    _poly(ax, [(xo - o, -h), (xo + o, -h), (xo + o, 4), (xo + o - t, 4), (xo + o - t, -h + t), (xo - o + t, -h + t), (xo - o + t, 4), (xo - o, 4)],
          "#4b4f57", lw=0.8, z=3)
    _dim(ax, (xo - o, 4.0), (xo + o, 4.0), 2.5, f"{ub['outside']:g} outside", fs=8.5)
    _dim(ax, (xo - o + t, -h + t), (xo + o - t, -h + t), 2.0, f"≈{ub['inside']:g}", fs=8)
    xs = 8.0
    ch = [(xs - w / 2, -h)] + [(xs + w / 2 * math.cos(a), w / 2 * math.sin(a)) for a in np.linspace(math.pi, 0, 30)] + [(xs + w / 2, -h)]
    _poly(ax, ch, "#4b4f57", lw=0.8, z=3)
    ax.add_patch(Circle((xs, 0.0), ub["hole"] / 2, fc="white", ec=INK, lw=0.7, zorder=4))
    _dim(ax, (xs - w / 2, -h), (xs + w / 2, -h), -2.5, f"{w:g}", fs=8.5)
    _ext(ax, [xs + w / 2 + 0.5, xs + w / 2 + 5.0], [0, 0])
    _ext(ax, [xs + w / 2 + 0.5, xs + w / 2 + 5.0], [-h, -h])
    _dim(ax, (xs + w / 2 + 3.5, -h), (xs + w / 2 + 3.5, 0), 0.0, f"{h:g}", fs=8.5, ext=False)
    _note(ax, (xs - 1.0, 1.0), f"Ø{ub['hole']:g}", (xs - 3.0, 9.0), fs=8.5)
    ax.text(-17.0, -h - 8.5, "P16 U-bracket, from Actuonix's P16\ndrawing (Rev B); 2 ship with each P16.\n"
            "Sheet ≈1.2 and the base hole are not\ndimensioned there: measure yours.", fontsize=8.5, ha="left", va="top")
    _title(ax, -17.0, 11.0, "U-BRACKET (bought)")

    # ---- notes ---------------------------------------------------------------------------------------------------
    ax = fig.add_axes([0.50, 0.02, 0.49, 0.43])
    ax.axis("off")
    lines = [
        ("How it goes together (one per leg)", True),
        (f"1. Drop an M3 nut into the trap under the tab. Set the U-bracket in the {tab['pocket'][0]:g} × {tab['pocket'][1]:g} pocket,", False),
        ("    its holes along x (parallel to the hinge), so the P16 swings in the module's plane.", False),
        ("2. From inside the U, screw an M3 × 12 button head down through the bracket's base and the tab into the nut.", False),
        ("3. Slip the P16-200's rear lug between the cheeks and push the #8-32 × 5/8 in screw through cheek, lug, cheek.", False),
        ("4. Lock nut on: snug the cheeks onto the lug, then back off about 1/4 turn so the P16 pivots freely.", False),
        ("5. Pin the rod end in the clevis block (M4 × 20 + nyloc) with the module tilted up a little.", False),
        ("What carries the load", True),
        ("The P16 pushes (about 5-10 N here): the pin takes it, the bracket's base bears on the pocket floor,", False),
        (f"and the pocket's walls take the sideways part (the P16 leans {L4.LEAN['lean_min_deg']:.1f}-{L4.LEAN['lean_max_deg']:.0f}°). The M3 only holds it down.", False),
        ("Clearances (2D, from Actuonix's outlines)", True),
        (f"Lug in the U: ≈{ck['lug_side_gap_each_side']:g} each side. Housing over the bracket's ends: ≈{ck['housing_to_bracket_ends']:g}"
         f" (as in Actuonix's own bracket).", False),
        (f"M3 head under the lug: {ck['m3_head_to_lug_min']:g} at {L4.LEAN['lean_max_deg']:.0f}° lean. Pin {ck['pin_above_tab_top']:g} above the tab's top.", False),
        ("Correction to the 24 Nov leg", True),
        (f"Actuonix's 11.5 is the bracket's OUTSIDE width (earlier runs read it as inside). In the Onshape leg,", False),
        (f"change the tab's pocket from {tab['pocket_24nov'][0]:g} × {tab['pocket_24nov'][1]:g} to {tab['pocket'][0]:g} × {tab['pocket'][1]:g}"
         f" (1 deep; 0.3 play a side). Nothing else moves.", False),
    ]
    _text_block(ax, lines, dy=0.0605, fs=10.3)
    fig.text(0.005, 0.993, "How each P16-200 attaches to its leg: its own U-bracket, keyed into the leg head's tab (issue #204, L4)",
             fontsize=16.5, fontweight="bold", va="top")
    fig.savefig(OUT / "l4_actuator_mount.png", dpi=110)
    plt.close(fig)
    print("  -> renders/l4_actuator_mount.png", flush=True)


def all_figures(res, blk, pl, outline, parts):
    block_tiles(blk)
    clevis_sheet(res, blk)
    plate_sheet(res, blk, pl, outline, parts)
    joint_tiles()
    joint_sheet(res)
