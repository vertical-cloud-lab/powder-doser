"""Figures for leg_unit.py (issue #204, 24 Nov): the leg unit's drawing, the station on three legs over the
HR-100A, the base's lobe end before and after, one module's side view at 0/45/90 deg and Onshape's own views.

    xvfb-run -a python leg_unit.py --figures-only
"""
from __future__ import annotations

import math
from pathlib import Path

import numpy as np

import doserlib as D
import components as K
import base as B
import stands as ST
import scale_room as SR
import leg_unit as LU

HERE = Path(__file__).resolve().parent
OUT = HERE / "renders"
INK, GREY, TEAL, RED, ORANGE = "#1f1f1f", "#8a8a8a", "#16a085", "#c0392b", "#e67e22"
PRINT_C, ALU_C = "#7fc8bb", "#c7ccd3"


def _plt():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    return plt


def _poly(ax, pts, fc, ec=INK, lw=1.0, z=2, ls="-", alpha=1.0, hatch=None):
    from matplotlib.patches import Polygon
    ax.add_patch(Polygon(np.asarray(pts), closed=True, fc=fc, ec=ec, lw=lw, zorder=z, ls=ls, alpha=alpha, hatch=hatch))


def _rect(ax, x0, y0, x1, y1, **kw):
    _poly(ax, [(x0, y0), (x1, y0), (x1, y1), (x0, y1)], **kw)


def _hidden(ax, xs, ys, col=INK, lw=0.7):
    ax.plot(xs, ys, color=col, lw=lw, ls=(0, (4, 2.5)), zorder=4)


# --------------------------------------------------------------------------- #
# 1. drawing of the leg unit
# --------------------------------------------------------------------------- #
def drawing(res, fn):
    plt = _plt()
    h = res["head"]
    sl, tab, pin = h["sleeve"], h["tab"], h["m5_pin"]
    PIN = res["actuator"]["rear_pin_leg_frame"]
    S = 340.0
    fig = plt.figure(figsize=(19.0, 11.4), dpi=110)
    gs = fig.add_gridspec(2, 3, width_ratios=[1.45, 1.0, 0.55], height_ratios=[1.0, 0.55], wspace=0.05, hspace=0.10)
    # ---- side profile -----------------------------------------------------
    ax = fig.add_subplot(gs[:, 0])
    ax.set_aspect("equal")
    prof = np.array(h["profile"])
    _poly(ax, prof, PRINT_C, lw=1.3, z=3)
    zt = -S + res["foot"]["pad_t"]
    a = res["tube"]["size"] / 2
    pc = sl["bore_centre"]
    _rect(ax, pc - a, zt, pc + a, zt + res["tube"]["length"], fc=ALU_C, ec="#666", lw=0.8, z=2)
    f = res["foot"]
    _rect(ax, pc - f["pad"] / 2, -S, pc + f["pad"] / 2, -S + f["pad_t"], fc=PRINT_C, ec=INK, lw=1.0, z=3)
    _rect(ax, pc - f["socket"] / 2, -S + f["pad_t"], pc + f["socket"] / 2, -S + f["pad_t"] + f["socket_h"], fc=PRINT_C, ec=INK, lw=1.0, z=3)
    ax.plot([60, 360], [-S, -S], color="#9a8f7a", lw=2.0, zorder=1)
    ax.text(62, -S - 7, f"bench (shelf underside {S:.0f} mm up; {res['stand_range'][0]:.0f}-{res['stand_range'][1]:.0f} in 10 mm steps)",
            fontsize=9, color="#6b604c", va="top")
    # hidden: bore, window, holes, pin hole, pocket, nut traps
    b = sl["bore"] / 2
    _hidden(ax, [pc - b, pc - b], [sl["bottom"], sl["bore_top"]])
    _hidden(ax, [pc + b, pc + b], [sl["bottom"], sl["bore_top"]])
    _hidden(ax, [pc - b, pc + b], [sl["bore_top"], sl["bore_top"]])
    for y in (127.0, 207.0):
        _hidden(ax, [y, y], [0, -h["arm_depth"]])
    for y in sorted({p[1] for p in h["holes"]}):
        _hidden(ax, [y - 2.25, y - 2.25], [0, -h["arm_depth"]], col=GREY)
        _hidden(ax, [y + 2.25, y + 2.25], [0, -h["arm_depth"]], col=GREY)
    _hidden(ax, [sl["inner_face"], sl["outer_face"]], [pin["z"] + 2.65, pin["z"] + 2.65], col=GREY)
    _hidden(ax, [sl["inner_face"], sl["outer_face"]], [pin["z"] - 2.65, pin["z"] - 2.65], col=GREY)
    px, py, pd = tab["pocket"]
    _hidden(ax, [PIN[1] - py / 2, PIN[1] - py / 2, PIN[1] + py / 2, PIN[1] + py / 2], [tab["top"], tab["top"] - pd, tab["top"] - pd, tab["top"]])
    # the U-bracket and the P16-200's lower end (at 0 deg tilt, leaning 25 deg), for context
    ub_b = PIN[2] - K.UB["h"]
    _rect(ax, PIN[1] - 3.75, ub_b, PIN[1] + 3.75, PIN[2], fc="#55585e", ec="#33363b", lw=0.6, z=5)
    ax.add_patch(plt.Circle((PIN[1], PIN[2]), 4.75, fc="#4a4d52", ec="#222", lw=0.6, zorder=6))
    lean = math.radians(25.0)
    ax_ = np.array([-math.sin(lean), math.cos(lean)])
    nrm = np.array([math.cos(lean), math.sin(lean)])
    P0 = np.array(PIN[1:])
    hous = [P0 + 5 * ax_ - 10.5 * nrm, P0 + 5 * ax_ + 25.5 * nrm, P0 + 75 * ax_ + 25.5 * nrm, P0 + 75 * ax_ - 10.5 * nrm]
    _poly(ax, hous, "#6d7178", ec="#33363b", lw=0.6, z=4, alpha=0.55)
    tube_end = 247.0 - 15.5
    _poly(ax, [P0 + 75 * ax_ - 6 * nrm, P0 + 75 * ax_ + 6 * nrm, P0 + tube_end * ax_ + 6 * nrm, P0 + tube_end * ax_ - 6 * nrm],
          "#9ea2a8", ec="#55585e", lw=0.5, z=4, alpha=0.5)
    ax.text(P0[0] - 60, P0[1] + 120, "P16-200 at 0° tilt\n(leans 18.5-25°\nover 0-90°)", fontsize=8.5, color="#44474c", ha="center")
    ax.plot([P0[0]], [P0[1]], marker="+", color="w", ms=6, zorder=7)
    # shelf (context)
    _rect(ax, 30, 0, 174, 6, fc="#fbe3c8", ec="#c46a1c", lw=0.8, z=1)
    ax.text(40, 9, "base (shelf, 6 thick), ends at 174", fontsize=8.5, color="#a65a17")
    # dimensions
    D_ = B._dim
    D_(ax, (h["arm_from_axis"][0], 0), (sl["outer_face"], 0), 26, f"{sl['outer_face'] - h['arm_from_axis'][0]:.1f}")
    D_(ax, (0, 0), (h["arm_from_axis"][0], 0), 26, f"{h['arm_from_axis'][0]:.0f} from the beaker axis", tpos=0.62)
    ax.plot([0, 0], [-6, 36], color=GREY, lw=0.7, ls="-.")
    ax.text(2, 38, "beaker axis", fontsize=8.5, color=GREY)
    D_(ax, (sl["outer_face"], 0), (sl["outer_face"], sl["bottom"]), 34, f"{-sl['bottom']:.2f}")
    D_(ax, (sl["inner_face"], sl["bottom"]), (sl["outer_face"], sl["bottom"]), -12, f"{sl['outer_face'] - sl['inner_face']:.1f}")
    D_(ax, (h["arm_from_axis"][0], -h["arm_depth"]), (h["arm_from_axis"][0], 0), 10, f"{h['arm_depth']:.0f}")
    D_(ax, (0, sl["bottom"] - 4), (sl["inner_face"], sl["bottom"] - 4), -26, f"sleeve's inner face {sl['inner_face']:.1f}", tpos=0.75)
    ax.text(pc, -185, f"bore {sl['bore']}\nsquare,\ncentre\n{pc:.1f}\nfrom the\naxis;\nstops {-sl['bore_top']:.0f}\nunder the\narm's top", fontsize=8,
            ha="center", va="center", color=INK, bbox=dict(fc="white", ec="none", pad=0.4), zorder=8)
    D_(ax, (sl["outer_face"], 0), (sl["outer_face"], pin["z"]), 14, f"M5 pin hole {-pin['z']:.0f} down (Ø{pin['d']})", tpos=0.5)
    D_(ax, (sl["inner_face"], -h["arm_depth"]), (sl["inner_face"] - h["arm_web"], -h["arm_depth"]), 8, f"web {h['arm_web']:.0f} x 45°")
    D_(ax, (tab["from_y"], tab["top"]), (sl["inner_face"], tab["top"]), 16, f"tab {sl['inner_face'] - tab['from_y']:.0f}")
    D_(ax, (tab["from_y"], tab["top"] - tab["thickness"]), (tab["from_y"], tab["top"]), 8, f"{tab['thickness']:.0f}")
    D_(ax, (60, 0), (60, tab["top"]), 0, f"tab top {-tab['top']:.1f} under the shelf", tpos=0.5)
    ax.plot([60, tab["from_y"]], [tab["top"], tab["top"]], color=GREY, lw=0.5, ls=":")
    B._note(ax, (PIN[1], PIN[2]), f"P16's rear pin (#8-32), {PIN[1]} from the axis,\n{-PIN[2]:.1f} under the shelf, in its own U-bracket",
            (95, PIN[2] + 55), fs=8.5)
    B._note(ax, (PIN[1], tab["top"] - 0.5), f"pocket {px} x {py} x {pd} deep keys the bracket;\nM3 x 12 button head inside the U,\nnut trap {5.7} AF underneath",
            (95, tab["top"] - 40), fs=8.5)
    ax.set_xlim(-12, 372)
    ax.set_ylim(-S - 22, 52)
    ax.axis("off")
    ax.set_title("Side view (leg frame: y from the beaker axis, z from the shelf's underside); mm",
                 loc="left", fontsize=11.5, fontweight="bold")
    # ---- plan of the arm ---------------------------------------------------
    ax = fig.add_subplot(gs[0, 1])
    ax.set_aspect("equal")
    w = h["width_x"] / 2
    y0, y1 = h["arm_from_axis"]
    _rect(ax, -w, y0, w, y1, fc=PRINT_C, ec=INK, lw=1.2, z=2)
    _poly(ax, h["window"], "white", ec=INK, lw=1.0, z=3)
    for x, y in h["holes"]:
        ax.add_patch(plt.Circle((x, y), h["hole_d"] / 2, fc="white", ec=INK, lw=0.9, zorder=4))
        hx = np.array(LU.hexagon(x, y, h["nut_trap_af"]))
        _hidden(ax, np.r_[hx[:, 0], hx[0, 0]], np.r_[hx[:, 1], hx[0, 1]], col=GREY, lw=0.6)
    _hidden(ax, [-b, b, b, -b, -b], [pc - b, pc - b, pc + b, pc + b, pc - b])
    _hidden(ax, [-px / 2, px / 2, px / 2, -px / 2, -px / 2], [PIN[1] - py / 2, PIN[1] - py / 2, PIN[1] + py / 2, PIN[1] + py / 2, PIN[1] - py / 2], col=GREY)
    # the lobe end above it
    lo = np.array(B.lobe_pts()) + [0, SP_]
    _poly(ax, lo, "none", ec="#c46a1c", lw=1.0, z=5, ls="--")
    ax.text(-128, 170, "dashed: the lobe end\nabove (ends at 174)", fontsize=8.5, color="#a65a17", va="center")
    D_(ax, (-w, y0), (w, y0), -10, f"{2 * w:.0f}")
    D_(ax, (h["holes"][2][0], 113), (h["holes"][0][0], 113), 0, f"{h['holes'][0][0] - h['holes'][2][0]:.0f}")
    for y in sorted({p[1] for p in h["holes"]}):
        ax.plot([-w - 14, -w], [y, y], color=GREY, lw=0.4, ls=":")
        ax.text(-w - 15, y, f"{y:.0f}", fontsize=8.5, va="center", ha="right")
    for (x, y) in h["window"]:
        if x >= 0:
            ax.plot([x, w + 14], [y, y], color=GREY, lw=0.3, ls=":")
            ax.text(w + 15, y, f"{y:.0f}", fontsize=8.5, va="center", color="#555")
    ax.text(0, 152.5, "±17", fontsize=8.5, ha="center")
    ax.text(0, 183, "±9", fontsize=8.5, ha="center")
    ax.text(w + 15, 225, "y from the\nbeaker axis", fontsize=8.5, color="#555")
    B._note(ax, (h["holes"][2][0], h["holes"][2][1]), f"4 x Ø{h['hole_d']} for M4 x 25\ncountersunk (from the shelf's top);\n"
            f"nut traps {h['nut_trap_af']} AF x {h['nut_trap_depth']}\ndeep underneath", (-128, 75), fs=8.5, ha="left")
    B._note(ax, (-9, 186), "window: the clevis block's\nlugs and M4 pin (at 0°)\nand the P16's rod pass", (-128, 215), fs=8.5)
    ax.set_xlim(-130, 78)
    ax.set_ylim(58, 330)
    ax.axis("off")
    ax.set_title("Arm from below/above (plan), mm", loc="left", fontsize=11.5, fontweight="bold")
    # ---- tube and foot ------------------------------------------------------
    ax = fig.add_subplot(gs[0, 2])
    ax.set_aspect("equal")
    L = res["tube"]["length"]
    _rect(ax, -10, 0, 10, L, fc=ALU_C, ec=INK, lw=1.0)
    for hh in res["tube"]["holes_from_lower_end"]:
        ax.add_patch(plt.Circle((0, hh), res["tube"]["hole_d"] / 2, fc="white", ec=INK, lw=0.6, zorder=4))
    ax.plot([-10, 10], [res["tube"]["foot_hole_h"]] * 2, color=INK, lw=0.6, ls="--")
    D_(ax, (10, 0), (10, L), -10, f"{L:.0f}")
    hs = res["tube"]["holes_from_lower_end"]
    D_(ax, (-10, 0), (-10, hs[0]), 12, f"{hs[0]:.0f}")
    D_(ax, (-10, hs[0]), (-10, hs[-1]), 12, f"9 x {res['tube']['pitch']:.0f}")
    ax.text(0, L + 12, "20 x 20 x 1.5\naluminium tube", fontsize=8.5, ha="center")
    ax.text(14, hs[3], f"Ø{res['tube']['hole_d']} through\n(along y), one per\nheight setting", fontsize=8, va="center")
    ax.text(14, res["tube"]["foot_hole_h"] + 4, f"Ø{res['tube']['foot_hole_d']} across (x):\nfoot screw", fontsize=8, va="bottom")
    ax.set_xlim(-55, 75)
    ax.set_ylim(-60, L + 40)
    ax.axis("off")
    ax.set_title("Tube", loc="left", fontsize=11.5, fontweight="bold")
    ax = fig.add_subplot(gs[1, 2])
    ax.set_aspect("equal")
    _rect(ax, -f["pad"] / 2, 0, f["pad"] / 2, f["pad_t"], fc=PRINT_C, ec=INK)
    _rect(ax, -f["socket"] / 2, f["pad_t"], f["socket"] / 2, f["pad_t"] + f["socket_h"], fc=PRINT_C, ec=INK)
    _hidden(ax, [-f["bore"] / 2, -f["bore"] / 2, f["bore"] / 2, f["bore"] / 2], [f["pad_t"] + f["socket_h"], f["pad_t"], f["pad_t"], f["pad_t"] + f["socket_h"]])
    ax.add_patch(plt.Circle((0, f["pad_t"] + res["tube"]["foot_hole_h"]), f["hole_d"] / 2, fc="white", ec=INK, lw=0.6, zorder=4))
    D_(ax, (-f["pad"] / 2, 0), (f["pad"] / 2, 0), -8, f"{f['pad']:.0f} square, {f['pad_t']:.0f} thick")
    D_(ax, (f["socket"] / 2, f["pad_t"]), (f["socket"] / 2, f["pad_t"] + f["socket_h"]), -6, f"{f['socket_h']:.0f}")
    ax.text(0, f["pad_t"] + f["socket_h"] + 6, f"socket {f['socket']:.0f} square,\nbore {f['bore']} square", fontsize=8.5, ha="center")
    ax.set_xlim(-40, 40)
    ax.set_ylim(-22, 60)
    ax.axis("off")
    ax.set_title("Foot", loc="left", fontsize=11.5, fontweight="bold")
    # ---- notes ---------------------------------------------------------------
    ax = fig.add_subplot(gs[1, 1])
    ax.axis("off")
    m = res["masses"]
    lines = [
        "One leg unit (make three):",
        f"  head: printed, {m['head_cm3']:.0f} cm³; prints flat on its side (x up), {res['print']['footprint_mm'][0]:.0f} x "
        f"{res['print']['footprint_mm'][1]:.0f} x {res['print']['height_mm']:.0f} mm, one H2D nozzle, no supports",
        f"  tube: 20 x 20 x 1.5 aluminium, {res['tube']['length']:.0f} long, {len(res['tube']['holes_from_lower_end'])} + 1 holes",
        f"  foot: printed, {m['foot_cm3']:.0f} cm³; a rubber pad under it",
        "Hardware per leg:",
        "  4 x M4 x 25 countersunk (ISO 10642) + nuts: base to arm",
        "  1 x M5 x 40 + wing nut (or a Ø5 ball-lock pin): height",
        "  1 x M4 x 35 + nyloc: foot to tube",
        "  1 x M3 x 12 button head (ISO 7380) + nut: U-bracket to tab",
        "  the P16-200's own U-bracket and #8-32 screw: rear pin",
        "Every printed section is 64 wide (x = ±32).",
    ]
    ax.text(0.0, 1.0, "\n".join(lines), fontsize=10, va="top", ha="left", family="DejaVu Sans", transform=ax.transAxes)
    fig.suptitle("Tri-star leg unit for L4 (P16-200 leaning 25°): head, tube and foot (the tube and foot drawn at 340 mm)",
                 x=0.01, ha="left", fontsize=14, fontweight="bold")
    fig.savefig(fn, bbox_inches="tight")
    plt.close(fig)
    return fn


SP_ = LU.SP


# --------------------------------------------------------------------------- #
# 2. the base's lobe end: what changes
# --------------------------------------------------------------------------- #
def base_changes(res, fn):
    plt = _plt()
    bc = res["base_changes"]
    fig, axs = plt.subplots(1, 2, figsize=(16.5, 9.4), dpi=110, gridspec_kw=dict(width_ratios=[1, 1]))
    lo = np.array(B.lobe_pts()) + [0, SP_]
    for ax, which in zip(axs, ("today", "L4")):
        ax.set_aspect("equal")
        _poly(ax, lo, "#fbe3c8", ec="#c46a1c", lw=1.2, z=1)
        for sx in (1, -1):
            x0, x1 = sorted((sx * B.TOWER_X[0], sx * B.TOWER_X[1]))
            _rect(ax, x0, 10 + SP_, x1, 35 + SP_, fc="#e2b27f", ec="#a65a17", lw=0.8, z=2)
        ax.text(0, 26 + SP_, "hinge towers' feet", fontsize=8.5, ha="center", color="#a65a17")
        ax.plot([-60, 60], [SP_, SP_], color=GREY, lw=0.7, ls="-.")
        ax.text(62, SP_, "hinge axis (32)", fontsize=8.5, va="center", color=GREY)
        if which == "today":
            _rect(ax, -bc["old_slot"]["half_width"], bc["old_slot"]["from_axis"][0], bc["old_slot"]["half_width"],
                  bc["old_slot"]["from_axis"][1], fc="white", ec=INK, lw=1.0, z=3)
            for x, y in bc["old_holes"]:
                ax.add_patch(plt.Circle((x, y), 2.25, fc="white", ec=INK, lw=0.9, zorder=4))
            ax.set_title("Today (base.py, 13 Nov): slot 65-144, hanger holes at 151 and 165", loc="left", fontsize=11.5, fontweight="bold")
            B._dim(ax, (-17, 65), (17, 65), 8, "34")
            B._dim(ax, (-48, 0), (-48, 65), 0, "65", tpos=0.85)
            B._dim(ax, (-48, 65), (-48, 144), 0, "79")
            B._note(ax, (14.5, 151), "4 x Ø4.5 at x ±14.5,\n151 and 165: inside L4's slot", (35, 172), fs=9)
        else:
            # what L4 fills, removes and adds
            _rect(ax, -17, 65, 17, 134, fc="#d9f0e9", ec=TEAL, lw=0.8, z=2, ls="--", hatch="///")
            ax.text(0, 100, "fill\n(no longer\nneeded)", fontsize=9, ha="center", va="center", color=TEAL, zorder=6,
                    bbox=dict(fc="white", ec="none", pad=0.3))
            _rect(ax, -bc["slot"]["half_width"], bc["slot"]["from_axis"], bc["slot"]["half_width"], 186, fc="white", ec=INK, lw=1.0, z=3)
            for x, y in bc["old_holes"]:
                ax.plot([x - 2.6, x + 2.6], [y - 2.6, y + 2.6], color=RED, lw=1.2, zorder=6)
                ax.plot([x - 2.6, x + 2.6], [y + 2.6, y - 2.6], color=RED, lw=1.2, zorder=6)
            for x, y in bc["new_holes"]:
                ax.add_patch(plt.Circle((x, y), bc["countersink_d"] / 2, fc="white", ec=INK, lw=0.7, zorder=4))
                ax.add_patch(plt.Circle((x, y), bc["hole_d"] / 2, fc="white", ec=INK, lw=0.9, zorder=5))
            # the arm underneath
            h = res["head"]
            w = h["width_x"] / 2
            _rect(ax, -w, h["arm_from_axis"][0], w, 200, fc="none", ec=TEAL, lw=1.0, z=5, ls=(0, (5, 3)))
            ax.text(-w + 1, 196, "leg's arm, under the shelf", fontsize=8.5, color=TEAL, va="top")
            ax.set_title("For L4's legs: slot 134 to past the lobe end; 4 new countersunk M4 holes", loc="left",
                         fontsize=11.5, fontweight="bold")
            B._dim(ax, (-17, 186), (17, 186), -6, "34 (unchanged)")
            B._dim(ax, (-48, 0), (-48, 134), 0, "134", tpos=0.85)
            B._note(ax, (0, 180), "open through the lobe end\n(the P16's rod passes\nout to 153 at mid tilts)", (40, 196), fs=9)
            B._dim(ax, (bc["new_holes"][0][0], 0), (bc["new_holes"][0][0], bc["new_holes"][0][1]), -26, f"{bc['new_holes'][0][1]:.0f}", tpos=0.88)
            B._dim(ax, (bc["new_holes"][1][0], 0), (bc["new_holes"][1][0], bc["new_holes"][1][1]), -42, f"{bc['new_holes'][1][1]:.0f}", tpos=0.92)
            B._dim(ax, (-25, 84), (25, 84), 0, "50")
            B._note(ax, (-25, 126), f"4 x Ø{bc['hole_d']} through,\ncountersunk 90° to Ø{bc['countersink_d']}\non the top (M4 flat heads\nsit 0.2 below the surface)",
                    (-118, 150), fs=9)
            B._note(ax, (14.5, 151), "old holes: delete", (40, 160), fs=9, col=RED)
        ax.plot([0, 0], [0, 12], color=GREY, lw=0.7)
        ax.text(2, 2, "beaker axis", fontsize=8.5, color=GREY)
        ax.set_xlim(-120, 120)
        ax.set_ylim(-5, 205)
        ax.axis("off")
    fig.suptitle("One lobe of the base, from above (the same at all three; mm from the beaker axis along the module's centre line)",
                 x=0.01, ha="left", fontsize=13.5, fontweight="bold")
    fig.text(0.01, 0.01, "Nothing else changes: outline, Ø78 window, towers and the other two lobes' features stay as drawn on 13 Nov. "
             "If you keep the old slot open, the new holes still clear it by 5.75 mm, but the lobe end becomes a 110 mm fork until the leg is bolted on.",
             fontsize=10, color="#333")
    fig.tight_layout(rect=(0, 0.03, 1, 0.95))
    fig.savefig(fn)
    plt.close(fig)
    return fn


# --------------------------------------------------------------------------- #
# 3. renders: the station on three legs over the HR-100A; one module at 0/45/90
# --------------------------------------------------------------------------- #
def station_parts(tilts, S=340.0, phi=90.0, lid=True, balance=True):
    parts = []
    for i, th in enumerate(B.BEARINGS):
        u = "ABC"[i]
        for p in LU.module_parts(th, u, tilts[i]):
            parts.append(p)
        parts += LU.leg_parts(th, u, S)
    b = D.Part("base", LU.cached("base_l4", LU.base_l4), np.eye(4), K.STATUS["new"][2], "fixed", False)
    parts.append(b)
    zb = LU.BOT - S
    if balance:
        hb = D.Part("HR-100A", SR.hr_solid(lid), SR.M_balance(phi, zb), (0.80, 0.81, 0.83), "bal", False)
        parts.append(hb)
    parts.append(ST.bench(zb, half=380.0))
    return parts


def render_station(res, fn):
    from PIL import Image
    t1, t2 = OUT / "_lu_a.png", OUT / "_lu_b.png"
    fit = res["hr100a"]["340"]
    ST.render_concept("lu1", station_parts((30, 60, 0)), "The tri-star on three leg units, 340 mm up, over the HR-100A / HR-250AZ",
                      ["modules at 30°, 60° and 0°; balance display facing you",
                       f"clearance to the balance at every orientation: {fit['worst_lid_on']:.0f} mm lid on, {fit['worst_lid_off']:.0f} lid off"],
                      t1, az=-62.0, el=16.0, dist=1.05)
    ST.render_concept("lu2", station_parts((90, 0, 45)), "The same from the front-right, modules at 90°, 0° and 45°",
                      ["teal: printed leg parts; light grey: aluminium tubes", "orange: the base; dark: the P16-200s"],
                      t2, az=-20.0, el=10.0, dist=1.05)
    ims = [Image.open(p).convert("RGB") for p in (t1, t2)]
    w = sum(im.width for im in ims) + 16
    hgt = max(im.height for im in ims)
    out = Image.new("RGB", (w, hgt), "white")
    x = 0
    for im in ims:
        out.paste(im, (x, 0))
        x += im.width + 16
    out.save(fn)
    for p in (t1, t2):
        p.unlink()
    return fn


def render_module(res, fn):
    """Module A (the back one) and its leg, from the side, at 0, 45 and 90 deg."""
    from PIL import Image, ImageDraw
    tiles = []
    for t in (0, 45, 90):
        parts = [p for p in LU.module_parts(90.0, "A", t)] + LU.leg_parts(90.0, "A", 340.0)
        sh = D.Part("shelf", LU.cached("base_l4", LU.base_l4), np.eye(4), K.STATUS["new"][2], "fixed", False)
        parts.append(sh)
        tmp = OUT / f"_lum{t}.png"
        D.render(parts, tmp, az=0.0, el=0.0, size=(760, 1000), parallel=True, dist=292.0, focal=(0.0, 130.0, -118.0), fixed=True)
        im = Image.open(tmp).convert("RGB")
        tmp.unlink()
        d = ImageDraw.Draw(im)
        d.text((18, 14), f"{t}° tilt", font=K.font(34, True), fill=(20, 20, 20))
        tiles.append(im)
    w = sum(im.width for im in tiles) + 2 * 12
    out = Image.new("RGB", (w, tiles[0].height + 120), "white")
    x = 0
    for im in tiles:
        out.paste(im, (x, 120))
        x += im.width + 12
    d = ImageDraw.Draw(out)
    d.text((18, 12), "One module and its leg from the side: the P16-200 swings 18.5-25° about the rear pin on the leg's tab",
           font=K.font(32, True), fill=(20, 20, 20))
    c = res["checks"]
    d.text((18, 62), f"closest over 0-90°: leg head to the P16 {c['per_leg_part_own_module']['leg head']['mm']} mm; "
                     f"tube {c['per_leg_part_own_module']['leg tube']['mm']} mm; base to the clevis block {c['base']['mm']} mm",
           font=K.font(26), fill=(60, 60, 60))
    out.save(fn)
    return fn


# --------------------------------------------------------------------------- #
# 4. plan: the balance, its doors and lid, at two orientations
# --------------------------------------------------------------------------- #
def plan_doors(res, fn):
    plt = _plt()
    from matplotlib.patches import Polygon as MPoly
    fit = res["hr100a"]["340"]
    rows = {r["phi"]: r for r in fit["rows"]}
    act, legs = LU.obstacle_samples(340.0)
    face = B.shelf_outline_sketch()._faces.Faces()[0]
    ol = B._wire_xy(face.outerWire())
    fig, axs = plt.subplots(1, 2, figsize=(17.5, 8.9), dpi=105)
    for ax, phi, title in ((axs[0], 90, "Display facing you"), (axs[1], 70, "Turned 20° clockwise")):
        r = rows[phi]
        ax.set_aspect("equal")
        ax.fill(ol[:, 0], ol[:, 1], color="#fbe3c8", zorder=1)
        ax.plot(ol[:, 0], ol[:, 1], color="#c46a1c", lw=0.9, zorder=2)
        ax.scatter(act[:, 0], act[:, 1], s=0.15, color="#555b63", zorder=3)
        ax.scatter(legs[:, 0], legs[:, 1], s=0.15, color=TEAL, zorder=3)
        for poly in SR.plan_outline_station(phi, lid=True):
            ax.add_patch(MPoly(poly, closed=True, fc=(0.55, 0.55, 0.6, 0.25), ec="#444", lw=0.8, zorder=5))
        c, s = math.cos(math.radians(phi)), math.sin(math.radians(phi))
        R = np.array([[c, -s], [s, c]])
        w = LU.DOOR["width"] / 2
        for side, key in ((1, "door_left"), (-1, "door_right")):
            d = r[key]
            box = np.array([(-w, side * LU.DOOR["r0"]), (w, side * LU.DOOR["r0"]), (w, side * (LU.DOOR["r0"] + d)), (-w, side * (LU.DOOR["r0"] + d))])
            ok = d >= LU.DOOR["reach"]
            ax.add_patch(MPoly(box @ R.T, closed=True, fc=(0.1, 0.6, 0.3, 0.18) if ok else (0.85, 0.3, 0.2, 0.18),
                               ec="#1e8449" if ok else RED, lw=1.0, zorder=6))
            ctr = (np.array([0, side * (LU.DOOR["r0"] + d / 2 + 10)]) @ R.T)
            ax.text(ctr[0], ctr[1], f"{'left' if side > 0 else 'right'} door\n{d:.0f}{'+' if ok else ''} mm",
                    fontsize=8.5, ha="center", va="center", zorder=8, color="#1e8449" if ok else RED)
        bb = SR.HR["bb_r"]
        band = np.array([(-bb, 0), (bb, 0), (bb, SR.HR["lid_open_reach"]), (-bb, SR.HR["lid_open_reach"])])
        okl = r["lid_swing"] >= LU.GAP
        ax.add_patch(MPoly(band @ R.T, closed=True, fc="none", ec="#2471a3" if okl else RED, lw=1.1, ls="--", zorder=7))
        tip = np.array([0, SR.HR["lid_open_reach"] + 14]) @ R.T
        ax.text(tip[0], tip[1], f"lid swings out here:\n{'clear by ' if okl else 'hits an actuator, '}{abs(r['lid_swing']):.0f} mm",
                fontsize=8.5, ha="center", color="#2471a3" if okl else RED, zorder=8)
        front = np.array([-170, 0]) @ R.T
        ax.annotate("display", xy=(np.array([-125, 0]) @ R.T), xytext=front, fontsize=9, ha="center",
                    arrowprops=dict(arrowstyle="-|>", lw=0.8, color="#444"))
        ax.text(0, -335, "you", fontsize=10, ha="center", color="#555")
        ax.set_xlim(-360, 360)
        ax.set_ylim(-350, 370)
        ax.axis("off")
        ax.set_title(f"{title}: balance clear by {r['lid_on']:.0f} mm (lid on), {r['lid_off']:.0f} (lid off)", loc="left",
                     fontsize=11.5, fontweight="bold")
    fig.suptitle("HR-100A / HR-250AZ under the station at 340 mm: reach-in beside each side door (100 mm wide, door height) "
                 "and the lid's swing", x=0.01, ha="left", fontsize=13, fontweight="bold")
    fig.text(0.01, 0.01, "grey dots: the P16-200s, clevis blocks and pins at every tilt 0-90°; teal: the legs; orange: the base. "
             "Green: clear for 150 mm or more. Balance outline traced from A&D's drawing (scale_room.py).", fontsize=10, color="#333")
    fig.tight_layout(rect=(0, 0.03, 1, 0.95))
    fig.savefig(fn)
    plt.close(fig)
    return fn


# --------------------------------------------------------------------------- #
# 5. Onshape's own views
# --------------------------------------------------------------------------- #
def onshape_sheet(fn):
    from PIL import Image, ImageDraw
    src = [HERE / "leg-unit" / "onshape_iso.png", HERE / "leg-unit" / "onshape_side.png"]
    if not all(p.exists() for p in src):
        return None
    ims = []
    for p in src:
        im = Image.open(p).convert("RGBA")
        bg = Image.new("RGBA", im.size, "white")
        ims.append(Image.alpha_composite(bg, im).convert("RGB"))
    w = sum(im.width for im in ims) + 20
    out = Image.new("RGB", (w, ims[0].height + 90), "white")
    x = 0
    for im in ims:
        out.paste(im, (x, 90))
        x += im.width + 20
    d = ImageDraw.Draw(out)
    d.text((16, 10), "The leg unit in Onshape (rendered by Onshape): Leg head, Leg tube, Leg foot", font=K.font(30, True), fill=(20, 20, 20))
    d.text((16, 52), "isometric, and from the side (the module's centre line runs left to right; the beaker axis is off to the left)",
           font=K.font(22), fill=(70, 70, 70))
    out.save(fn)
    return fn


def all_figures(res):
    OUT.mkdir(exist_ok=True)
    out = [drawing(res, OUT / "leg_unit_drawing.png"), base_changes(res, OUT / "leg_base_changes.png")]
    if "hr100a" in res:
        out.append(plan_doors(res, OUT / "leg_doors.png"))
    if "checks" in res:
        out.append(render_module(res, OUT / "leg_unit_module.png"))
    out.append(render_station(res, OUT / "leg_unit_station.png") if "hr100a" in res else None)
    out.append(onshape_sheet(OUT / "leg_unit_onshape.png"))
    return out
