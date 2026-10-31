#!/usr/bin/env python3
"""Overview figure: cheap doser measurements related to standard powder tests.

Drawn from the whiteboard sketch made by Sterling and Will on 2026-10-28 and
the corrected transcript of that meeting
(``meetings/2026-10-28-sterling-will.md``, 38:27-48:52 and main point 8):

* top row, cheap and on the doser: feed factor at several tilts; the
  "ghost dose" (a transparent doser, outlet closed, tapped, giving bulk and
  tapped density); angle of repose of the pile the doser pours;
* bottom row, the standard tests people measure and care about: Hall/Carney
  flow, PSD (SEM images in BSE mode, or laser diffraction), shear cell,
  bulk/tapped density, moisture;
* between them, the relational matrix: physics-based ML (surrogate models
  and DEM simulations) learns which doser measurements predict which standard
  property, with the state and history of the powder as extra inputs.

The figure is a schematic; it shows no data.

Usage (from paper/optimization/):
    python3 figures/make_overview_relations.py           # every link (default)
    python3 figures/make_overview_relations.py --board   # only the links drawn on the board
Writes figures/fig_overview_relations.{pdf,png}
(or figures/fig_overview_relations_board.{pdf,png} with --board).
"""
from __future__ import annotations

import sys

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Circle, Ellipse, FancyArrowPatch, FancyBboxPatch, Polygon, Rectangle

from make_figures import AQUA, BLUE, DOUBLE, INK, INK2, MUTED, ORANGE, save

# ------------------------------------------------------------------ colours
SAND, SAND_D = "#d9c49a", "#9c8456"           # powder and its grains
GLASS = "#f3f8fe"                              # transparent wall
TOP_FC, BOT_FC, ML_FC = "#eef4fd", "#fdf1ea", "#e6f6ef"
AQUA_D = "#11815a"                             # text on the green boxes (contrast)
BLUE_D, ORANGE_D = "#1d5fae", "#b8481c"        # row headers

# -------------------------------------------------------------------- nodes
# (key, title, subtitle)
DOSER = [
    ("ff", "Feed factor", "mg per auger revolution at several\ntilts, and before/after humid air",
     "measured now (13 powders)"),
    ("gd", "“Ghost dose”", "transparent doser, outlet closed,\ntapped: bulk and tapped density",
     "proposed: thin-walled SLA vessel"),
    ("aor", "Angle of repose", "camera on the pile\nthe doser pours",
     "proposed: camera at the outlet"),
]
STANDARD = [
    ("hall", "Hall/Carney flow", "50 g through a standard\nfunnel (ASTM B213, B964)",
     "in-house: funnel set"),
    ("psd", "Particle size (PSD)", "SEM images (BSE mode)\nor laser diffraction",
     "in-house SEM, or outside lab"),
    ("shear", "Shear cell, $ff_c$", "cohesion under load\n(ASTM D6773, D7891)",
     "outside lab"),
    ("tap", "Tapped density", "graduated cylinder, loose\nthen tapped (ASTM B527)",
     "in-house: cylinder"),
    ("moist", "Moisture", "loss on drying\n(weigh, dry, reweigh)",
     "in-house: oven, balance"),
]
# Links drawn on the 28 Oct board (green lines), read from the photo.
BOARD_LINKS = {("ff", "hall"), ("ff", "psd"), ("gd", "hall"), ("gd", "shear"),
               ("aor", "hall"), ("aor", "psd"), ("aor", "shear"), ("aor", "tap")}
ALL_LINKS = {(d[0], s[0]) for d in DOSER for s in STANDARD}

# ------------------------------------------------------------------ layout
W, Y0, Y1 = 100.0, -4.0, 66.6
TOP_X = {"ff": 27.5, "gd": 50.0, "aor": 72.5}
TOP_W, TOP_Y, TOP_H = 20.4, 38.6, 23.6
ICON_DY = 2.8  # top-row icons are drawn for y 46-58, then lifted by this much
SIDE_W = 15.4
BOT_X = {k: 10.0 + 20.0 * i for i, (k, *_) in enumerate(STANDARD)}
BOT_W, BOT_Y, BOT_H = 17.8, 0.4, 22.0


def lifted(ax, dy, draw, *args):
    """Run draw(ax, *args), then shift everything it added up by dy (data units)."""
    from matplotlib.transforms import Affine2D
    before = {k: len(getattr(ax, k)) for k in ("patches", "lines", "texts", "collections")}
    draw(ax, *args)
    shift = Affine2D().translate(0, dy) + ax.transData
    for k, n in before.items():
        for art in getattr(ax, k)[n:]:
            art.set_transform(shift)


def card(ax, cx, y, w, h, fc, ec):
    ax.add_patch(FancyBboxPatch((cx - w / 2, y), w, h, boxstyle="round,pad=0,rounding_size=1.2",
                                fc=fc, ec=ec, lw=0.8, zorder=1))


def grains(ax, poly_xy, n, rng, r=(0.10, 0.22), col=SAND_D):
    """Scatter n grains inside a polygon (rejection sampling)."""
    from matplotlib.path import Path
    path = Path(poly_xy)
    xs, ys = np.asarray(poly_xy)[:, 0], np.asarray(poly_xy)[:, 1]
    got = 0
    while got < n:
        p = (rng.uniform(xs.min(), xs.max()), rng.uniform(ys.min(), ys.max()))
        if path.contains_point(p, radius=-0.25):
            ax.add_patch(Circle(p, rng.uniform(*r), fc=col, ec="none", zorder=5))
            got += 1


def tube(ax, p0, angle_deg, length, width, fc="white", ec=INK2, lw=0.9, alpha=1.0, z=4):
    """Auger barrel: a rotated rectangle from outlet p0 along angle, with a motor block at the far end."""
    t = np.radians(angle_deg)
    u, n = np.array([np.cos(t), np.sin(t)]), np.array([-np.sin(t), np.cos(t)])
    p0 = np.asarray(p0, float)
    body = [p0 + n * width / 2, p0 + n * width / 2 + u * length,
            p0 - n * width / 2 + u * length, p0 - n * width / 2]
    ax.add_patch(Polygon(body, closed=True, fc=fc, ec=ec, lw=lw, alpha=alpha, zorder=z))
    m0 = p0 + u * length
    motor = [m0 + n * width * 0.75, m0 + n * width * 0.75 + u * 1.6,
             m0 - n * width * 0.75 + u * 1.6, m0 - n * width * 0.75]
    ax.add_patch(Polygon(motor, closed=True, fc="#d6d4ce" if alpha == 1 else fc, ec=ec, lw=lw,
                         alpha=alpha, zorder=z))
    # auger flight hint
    if alpha == 1:
        for s in np.linspace(0.18, 0.88, 6):
            a, b = p0 + u * length * s + n * width / 2, p0 + u * length * (s + 0.07) - n * width / 2
            ax.plot([a[0], b[0]], [a[1], b[1]], color=MUTED, lw=0.5, zorder=z + 0.1)
    return p0, u, n


def collar(ax, c, angle_deg, width, z=4.5):
    t = np.radians(angle_deg)
    ax.add_patch(Ellipse(c, 1.0, width * 2.1, angle=angle_deg, fc="none", ec=INK2, lw=0.9, zorder=z))
    return t


def falling(ax, x0, y0, y1, rng, n=7, spread=0.35):
    for y in np.linspace(y0, y1, n):
        ax.add_patch(Circle((x0 + rng.uniform(-spread, spread), y), 0.17, fc=SAND_D, ec="none", zorder=5))


def camera(ax, x, y, facing=1, s=1.0):
    ax.add_patch(FancyBboxPatch((x - 1.3 * s, y - 0.8 * s), 2.2 * s, 1.6 * s,
                                boxstyle="round,pad=0,rounding_size=0.25", fc="#4a4946", ec="none", zorder=6))
    lens = [(x + facing * 0.9 * s, y - 0.45 * s), (x + facing * 1.7 * s, y - 0.8 * s),
            (x + facing * 1.7 * s, y + 0.8 * s), (x + facing * 0.9 * s, y + 0.45 * s)]
    ax.add_patch(Polygon(lens, closed=True, fc="#4a4946", ec="none", zorder=6))
    ax.add_patch(Circle((x - 0.2 * s, y), 0.38 * s, fc="#9fb8d6", ec="none", zorder=7))


def balance(ax, cx, y, w=8.0):
    ax.add_patch(FancyBboxPatch((cx - w / 2, y), w, 1.5, boxstyle="round,pad=0,rounding_size=0.3",
                                fc="#e4e2dc", ec=INK2, lw=0.8, zorder=4))
    ax.add_patch(Rectangle((cx + w / 2 - 2.8, y + 0.35), 2.0, 0.8, fc="#cfe0c8", ec=INK2, lw=0.4, zorder=5))


# ------------------------------------------------------------- doser icons
def icon_feed_factor(ax, cx, rng):
    base = 47.0
    balance(ax, cx - 3.5, base, w=8.5)
    cup = [(cx - 5.4, base + 1.5), (cx - 1.6, base + 1.5), (cx - 1.2, base + 3.6), (cx - 5.8, base + 3.6)]
    ax.add_patch(Polygon(cup, closed=True, fc="white", ec=INK2, lw=0.8, zorder=5))
    ax.add_patch(Polygon([(cx - 5.2, base + 1.7), (cx - 1.8, base + 1.7), (cx - 1.65, base + 2.4),
                          (cx - 5.35, base + 2.4)], closed=True, fc=SAND, ec="none", zorder=5.5))
    pivot = np.array([cx + 2.2, base + 6.4])
    # stand
    ax.plot([pivot[0], cx + 0.6], [pivot[1], base], color=INK2, lw=1.0, zorder=3)
    ax.plot([pivot[0], cx + 5.0], [pivot[1], base], color=INK2, lw=1.0, zorder=3)
    ax.plot([cx - 0.1, cx + 5.8], [base, base], color=INK2, lw=1.2, zorder=3)
    # three tilts about the collar: two ghosts and the drawn one
    L, wid, back = 8.8, 1.5, 4.9
    for ang, alpha in ((15, 0.45), (43, 0.45), (29, 1.0)):
        t = np.radians(ang)
        u = np.array([np.cos(t), np.sin(t)])
        outlet = pivot - u * back
        if alpha < 1:
            tube(ax, outlet, ang, L, wid, fc="white", ec=MUTED, lw=0.6, alpha=alpha, z=2)
        else:
            tube(ax, outlet, ang, L, wid)
            collar(ax, pivot, ang, wid)
            out_main = outlet
    falling(ax, out_main[0] - 0.2, out_main[1] - 1.1, base + 2.9, rng, n=5)
    # tilt arc
    arc_r = 6.1
    th = np.radians(np.linspace(18, 40, 30))
    ax.plot(pivot[0] + arc_r * np.cos(th), pivot[1] + arc_r * np.sin(th), color=BLUE, lw=0.8, zorder=6)
    ax.add_patch(FancyArrowPatch((pivot[0] + arc_r * np.cos(th[-3]), pivot[1] + arc_r * np.sin(th[-3])),
                                 (pivot[0] + arc_r * np.cos(th[-1]), pivot[1] + arc_r * np.sin(th[-1])),
                                 arrowstyle="-|>", mutation_scale=6, color=BLUE, lw=0.8, zorder=6))
    ax.add_patch(FancyArrowPatch((pivot[0] + arc_r * np.cos(th[2]), pivot[1] + arc_r * np.sin(th[2])),
                                 (pivot[0] + arc_r * np.cos(th[0]), pivot[1] + arc_r * np.sin(th[0])),
                                 arrowstyle="-|>", mutation_scale=6, color=BLUE, lw=0.8, zorder=6))


def icon_ghost_dose(ax, cx, rng):
    base, top = 46.6, 57.4
    x0, x1 = cx - 1.7, cx + 1.7
    tapped, bulk = 51.4, 53.3
    ax.add_patch(Rectangle((x0, base), x1 - x0, top - base, fc=GLASS, ec="none", zorder=3))
    pw = [(x0, base + 0.5), (x1, base + 0.5), (x1, tapped), (x0, tapped)]
    ax.add_patch(Polygon(pw, closed=True, fc=SAND, ec="none", zorder=4))
    grains(ax, pw, 26, rng)
    ax.plot([x0, x0], [base, top], color=INK2, lw=0.9, zorder=6)
    ax.plot([x1, x1], [base, top], color=INK2, lw=0.9, zorder=6)
    # closed outlet
    ax.add_patch(Rectangle((cx - 2.5, base - 0.4), 5.0, 0.9, fc="#4a4946", ec="none", zorder=6))
    ax.text(cx + 2.9, base, "closed", fontsize=5.6, color=INK2, va="center", ha="left", zorder=6)
    # collar holding the tube
    ax.add_patch(Rectangle((cx - 3.0, 55.0), 6.0, 0.9, fc="#d6d4ce", ec=INK2, lw=0.6, zorder=6))
    # fill levels
    ax.plot([x0 - 1.4, x1], [bulk, bulk], color=BLUE, lw=0.8, ls=(0, (2, 1.4)), zorder=7)
    ax.plot([x0 - 1.4, x1], [tapped, tapped], color=BLUE, lw=0.8, zorder=7)
    ax.text(x0 - 1.6, bulk, "bulk", fontsize=5.6, color=BLUE, ha="right", va="center", zorder=7)
    ax.text(x0 - 1.6, tapped, "tapped", fontsize=5.6, color=BLUE, ha="right", va="center", zorder=7)
    # tap solenoid hitting the wall
    ax.add_patch(FancyBboxPatch((x1 + 1.7, 48.6), 3.0, 1.7, boxstyle="round,pad=0,rounding_size=0.25",
                                fc="#d6d4ce", ec=INK2, lw=0.6, zorder=6))
    ax.plot([x1 + 0.05, x1 + 1.7], [49.45, 49.45], color=INK2, lw=1.4, zorder=6)
    ax.text(x1 + 3.2, 51.0, "tap", fontsize=5.6, color=INK2, ha="center", va="bottom", zorder=6)


def icon_angle_of_repose(ax, cx, rng):
    base = 47.0
    ax.add_patch(Rectangle((cx - 6.5, base - 0.5), 12.0, 0.5, fc="#d6d4ce", ec=INK2, lw=0.6, zorder=4))
    half, ang = 4.2, 34.0
    apex = (cx - 0.5, base + half * np.tan(np.radians(ang)))
    pile = [(cx - 0.5 - half, base), (cx - 0.5 + half, base), apex]
    ax.add_patch(Polygon(pile, closed=True, fc=SAND, ec=SAND_D, lw=0.5, zorder=5))
    grains(ax, pile, 18, rng)
    # angle
    th = np.linspace(0, ang, 20)
    r = 2.3
    ax.plot(cx - 0.5 - half + r * np.cos(np.radians(th)), base + r * np.sin(np.radians(th)),
            color=BLUE, lw=0.8, zorder=7)
    ax.text(cx - 0.5 - half + r + 0.5, base + 0.55, "θ", fontsize=6.5, color=BLUE, zorder=7,
            va="center", ha="left")
    # doser above, pouring on the apex
    ang_t = 24
    outlet = np.array([apex[0] + 0.4, apex[1] + 3.6])
    tube(ax, outlet, ang_t, 7.4, 1.5)
    collar(ax, outlet + 4.4 * np.array([np.cos(np.radians(ang_t)), np.sin(np.radians(ang_t))]), ang_t, 1.5)
    falling(ax, outlet[0] - 0.1, outlet[1] - 1.0, apex[1] + 0.5, rng, n=4, spread=0.25)
    camera(ax, cx - 8.0, base + 2.6, facing=1, s=0.95)
    ax.plot([cx - 6.3, cx - 4.4], [base + 2.6, base + 2.0], color=MUTED, lw=0.5, ls=(0, (1.5, 1.2)), zorder=6)


# ---------------------------------------------------------- standard icons
def icon_hall(ax, cx, rng):
    top, neck, spout = 20.6, 15.6, 14.3
    cone = [(cx - 4.2, top), (cx + 2.2, top), (cx - 0.5, neck), (cx - 1.5, neck)]
    ax.add_patch(Polygon(cone, closed=True, fc="white", ec=INK2, lw=0.9, zorder=4))
    fill = [(cx - 3.55, top - 0.8), (cx + 1.55, top - 0.8), (cx - 0.55, neck + 0.3), (cx - 1.45, neck + 0.3)]
    ax.add_patch(Polygon(fill, closed=True, fc=SAND, ec="none", zorder=5))
    grains(ax, fill, 14, rng)
    ax.add_patch(Rectangle((cx - 1.5, spout), 1.0, neck - spout, fc="white", ec=INK2, lw=0.8, zorder=4))
    falling(ax, cx - 1.0, spout - 0.6, 12.4, rng, n=3, spread=0.15)
    cup = [(cx - 3.0, 10.4), (cx + 1.0, 10.4), (cx + 1.3, 12.2), (cx - 3.3, 12.2)]
    ax.add_patch(Polygon(cup, closed=True, fc="white", ec=INK2, lw=0.8, zorder=4))
    ax.text(cx - 6.6, 18.7, "50 g", fontsize=6.0, color=INK2, ha="left", va="center", zorder=6)
    # stopwatch
    sw = (cx + 5.0, 15.0)
    ax.add_patch(Circle(sw, 1.7, fc="white", ec=INK2, lw=0.9, zorder=5))
    ax.add_patch(Rectangle((sw[0] - 0.35, sw[1] + 1.65), 0.7, 0.55, fc=INK2, ec="none", zorder=5))
    ax.plot([sw[0], sw[0] + 0.9], [sw[1], sw[1] + 0.9], color=ORANGE, lw=0.9, zorder=6)
    ax.plot([sw[0], sw[0]], [sw[1], sw[1] + 1.2], color=INK2, lw=0.6, zorder=6)


def icon_psd(ax, cx, rng):
    x0, y0, s = cx - 4.6, 10.6, 9.6
    ax.add_patch(Rectangle((x0, y0), s, s, fc="#3b3a37", ec=INK2, lw=0.8, zorder=4))
    pts = []
    while len(pts) < 24:
        r = float(np.clip(rng.lognormal(np.log(0.55), 0.45), 0.2, 1.4))
        p = np.array([rng.uniform(x0 + r + 0.2, x0 + s - r - 0.2), rng.uniform(y0 + r + 1.2, y0 + s - r - 0.2)])
        if all(np.hypot(*(p - q)) > r + rq + 0.12 for q, rq in pts):
            pts.append((p, r))
    for p, r in pts:
        ax.add_patch(Circle(p, r, fc="#d8d6cf", ec="#f4f3ef", lw=0.3, zorder=5))
    ax.plot([x0 + s - 3.0, x0 + s - 0.7], [y0 + 0.6, y0 + 0.6], color="white", lw=1.2, zorder=6)
    ax.text(x0 + 0.5, y0 + 0.6, "BSE", fontsize=5.0, color="white", va="center", zorder=6)


def icon_shear(ax, cx, rng):
    lo, h, w = 11.0, 2.7, 7.6
    shift = 1.0
    low = [(cx - w / 2 - 0.4, lo), (cx + w / 2 - 0.4, lo), (cx + w / 2 - 0.4, lo + h), (cx - w / 2 - 0.4, lo + h)]
    up = [(cx - w / 2 - 0.4 + shift, lo + h), (cx + w / 2 - 0.4 + shift, lo + h),
          (cx + w / 2 - 0.4 + shift, lo + 2 * h), (cx - w / 2 - 0.4 + shift, lo + 2 * h)]
    for poly in (low, up):
        ax.add_patch(Polygon(poly, closed=True, fc=SAND, ec="none", zorder=4))
        grains(ax, poly, 12, rng)
        ax.add_patch(Polygon(poly, closed=True, fc="none", ec=INK2, lw=1.0, zorder=6))
    # lid and normal load
    ax.add_patch(Rectangle((up[0][0] + 0.2, lo + 2 * h), w - 0.4, 0.7, fc="#d6d4ce", ec=INK2, lw=0.7, zorder=6))
    xm = (up[0][0] + up[1][0]) / 2
    ax.add_patch(FancyArrowPatch((xm, 21.2), (xm, lo + 2 * h + 0.75), arrowstyle="-|>", mutation_scale=8,
                                 color=INK, lw=1.0, zorder=7))
    ax.text(xm + 0.5, 20.2, "σ", fontsize=6.8, color=INK, ha="left", va="center", zorder=7)
    # shear force on the upper ring
    ax.add_patch(FancyArrowPatch((up[0][0] - 3.1, lo + 1.5 * h), (up[0][0] - 0.1, lo + 1.5 * h),
                                 arrowstyle="-|>", mutation_scale=8, color=ORANGE, lw=1.1, zorder=7))
    ax.text(up[0][0] - 2.0, lo + 1.5 * h + 0.9, "τ", fontsize=6.8, color=ORANGE, ha="center",
            va="bottom", zorder=7)
    ax.plot([cx - w / 2 - 1.2, cx + w / 2 + 1.4], [lo + h, lo + h], color=ORANGE, lw=0.6,
            ls=(0, (2, 1.2)), zorder=7)


def icon_tap(ax, cx, rng):
    x0, x1, base, top = cx - 1.5, cx + 1.5, 11.6, 20.8
    ax.add_patch(Rectangle((cx - 2.9, base - 0.6), 5.8, 0.6, fc="#d6d4ce", ec=INK2, lw=0.6, zorder=5))
    ax.add_patch(Rectangle((x0, base), x1 - x0, top - base, fc=GLASS, ec="none", zorder=3))
    pw = [(x0, base), (x1, base), (x1, 16.2), (x0, 16.2)]
    ax.add_patch(Polygon(pw, closed=True, fc=SAND, ec="none", zorder=4))
    grains(ax, pw, 18, rng)
    ax.plot([x0, x0, x1, x1], [top, base, base, top], color=INK2, lw=0.9, zorder=6)
    for y in np.arange(base + 1.0, top - 0.4, 1.0):
        ax.plot([x0, x0 + (0.9 if round((y - base)) % 2 == 0 else 0.5)], [y, y], color=INK2, lw=0.45, zorder=6)
    ax.plot([x0, x1], [17.6, 17.6], color=ORANGE, lw=0.8, ls=(0, (2, 1.4)), zorder=7)
    # tapping
    for dx in (-4.4, 4.4):
        ax.add_patch(FancyArrowPatch((cx + dx, base - 0.4), (cx + dx, base + 2.6), arrowstyle="<|-|>",
                                     mutation_scale=6, color=INK2, lw=0.8, zorder=6))
    ax.text(cx + 4.4, base + 3.2, "tap", fontsize=5.6, color=INK2, ha="center", va="bottom", zorder=6)


def icon_moisture(ax, cx, rng):
    balance(ax, cx, 10.4, w=8.5)
    dish = [(cx - 3.2, 11.9), (cx + 3.2, 11.9), (cx + 3.7, 12.9), (cx - 3.7, 12.9)]
    ax.add_patch(Polygon(dish, closed=True, fc="white", ec=INK2, lw=0.8, zorder=5))
    ax.add_patch(Polygon([(cx - 2.9, 12.25), (cx + 2.9, 12.25), (cx + 3.15, 12.75), (cx - 3.15, 12.75)],
                         closed=True, fc=SAND, ec="none", zorder=6))
    # drying lamp and vapour
    ax.add_patch(FancyBboxPatch((cx - 3.8, 19.3), 7.6, 1.1, boxstyle="round,pad=0,rounding_size=0.3",
                                fc="#d6d4ce", ec=INK2, lw=0.6, zorder=5))
    ax.add_patch(Rectangle((cx - 3.0, 19.0), 6.0, 0.35, fc=ORANGE, ec="none", zorder=5))
    yy = np.linspace(13.6, 18.2, 40)
    for x in (cx - 2.0, cx, cx + 2.0):
        ax.plot(x + 0.35 * np.sin((yy - 13.6) * 3.0), yy, color="#7fa7d6", lw=0.8, zorder=5)


# -------------------------------------------------------- side-box icons
def icon_ml(ax, cx, y, rng):
    # DEM grains in a box (left) and a surrogate curve with its band (right)
    ax.add_patch(Rectangle((cx - 6.2, y), 5.0, 4.4, fc="white", ec=AQUA, lw=0.6, zorder=4))
    for i in range(4):
        for j in range(3):
            r = 0.55 + 0.12 * ((i * 3 + j) % 3)
            ax.add_patch(Circle((cx - 5.5 + 1.2 * i + 0.3 * (j % 2), y + 0.75 + 1.35 * j), r * 0.9,
                                fc=SAND, ec=SAND_D, lw=0.3, zorder=5))
    x = np.linspace(cx + 0.3, cx + 6.3, 60)
    mu = y + 2.2 + 1.1 * np.sin((x - cx) * 0.9)
    sd = 0.35 + 0.5 * np.abs(np.sin((x - cx) * 0.45))
    ax.add_patch(Rectangle((cx + 0.0, y), 6.6, 4.4, fc="white", ec=AQUA, lw=0.6, zorder=4))
    ax.fill_between(x, mu - sd, mu + sd, color=AQUA, alpha=0.25, lw=0, zorder=5)
    ax.plot(x, mu, color=AQUA_D, lw=0.9, zorder=6)
    xs = cx + np.array([1.0, 2.6, 4.9])
    ax.scatter(xs, y + 2.2 + 1.1 * np.sin((xs - cx) * 0.9), s=5, c=INK, zorder=7, edgecolors="none")


def icon_context(ax, cx, y):
    # a jar of powder with a label tag
    ax.add_patch(Rectangle((cx - 5.6, y), 3.6, 4.0, fc=GLASS, ec=INK2, lw=0.7, zorder=4))
    ax.add_patch(Rectangle((cx - 5.6, y), 3.6, 2.6, fc=SAND, ec="none", zorder=4.5))
    ax.add_patch(Rectangle((cx - 5.9, y + 4.0), 4.2, 0.8, fc="#4a4946", ec="none", zorder=5))
    ax.add_patch(Rectangle((cx - 5.0, y + 0.8), 2.4, 1.2, fc="white", ec=INK2, lw=0.4, zorder=5))
    # history: a short timeline of what happened to it
    ax.plot([cx - 1.0, cx + 5.4], [y + 2.0, y + 2.0], color=AQUA_D, lw=0.8, zorder=4)
    for i, t in enumerate(("made", "sieved", "dried", "reused")):
        xx = cx - 0.5 + 1.85 * i
        ax.add_patch(Circle((xx, y + 2.0), 0.32, fc=AQUA_D, ec="none", zorder=5))
        above = i % 2 == 0  # alternate labels above and below the line so they fit
        ax.text(xx, y + 2.9 if above else y + 1.1, t, fontsize=4.8, color=AQUA_D, ha="center",
                va="bottom" if above else "top", zorder=5)


# ------------------------------------------------------------------- links
def draw_links(ax, links):
    tops = {k: TOP_X[k] for k, *_ in DOSER}
    bots = BOT_X
    out = {k: sorted([b for (a, b) in links if a == k], key=lambda b: bots[b]) for k in tops}
    inn = {k: sorted([a for (a, b) in links if b == k], key=lambda a: tops[a]) for k in bots}
    y_top, y_bot = TOP_Y - 0.25, BOT_Y + BOT_H + 0.25

    def spread(n, half):
        return [0.0] if n == 1 else list(np.linspace(-half, half, n))

    for a in tops:
        for b in out[a]:
            xa = tops[a] + spread(len(out[a]), 6.5)[out[a].index(b)]
            xb = bots[b] + spread(len(inn[b]), 4.0)[inn[b].index(a)]
            ax.plot([xa, xb], [y_top, y_bot], color=AQUA, lw=1.0, alpha=0.75, solid_capstyle="round", zorder=2)
            ax.add_patch(Circle((xa, y_top), 0.32, fc=AQUA, ec="white", lw=0.4, zorder=3))
            ax.add_patch(Circle((xb, y_bot), 0.32, fc=AQUA, ec="white", lw=0.4, zorder=3))


# ------------------------------------------------------------------ figure
def fig_overview_relations(links=ALL_LINKS, name="fig_overview_relations"):
    rng = np.random.default_rng(7)
    fig = plt.figure(figsize=(DOUBLE, DOUBLE * (Y1 - Y0) / W))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, W)
    ax.set_ylim(Y0, Y1)
    ax.set_aspect("equal")
    ax.axis("off")

    # row headers
    ax.text(50, Y1 - 1.6, "Cheap: measured on the doser itself", fontsize=8.2, fontweight="bold",
            color=BLUE_D, ha="center", va="center")
    ax.text(50, Y0 + 1.5, "Standard tests: a separate instrument for each, some only in outside labs",
            fontsize=8.2, fontweight="bold", color=ORANGE_D, ha="center", va="center")

    # links first, so the cards sit on top of their ends
    draw_links(ax, links)

    for key, title, sub, status in DOSER:
        cx = TOP_X[key]
        card(ax, cx, TOP_Y, TOP_W, TOP_H, TOP_FC, BLUE)
        lifted(ax, ICON_DY, {"ff": icon_feed_factor, "gd": icon_ghost_dose,
                             "aor": icon_angle_of_repose}[key], cx, rng)
        ax.text(cx, TOP_Y + 7.9, title, fontsize=7.6, fontweight="bold", color=INK, ha="center", va="center")
        ax.text(cx, TOP_Y + 4.9, sub, fontsize=5.9, color=INK2, ha="center", va="center", linespacing=1.15)
        ax.text(cx, TOP_Y + 1.6, status, fontsize=5.7, color=BLUE_D, ha="center", va="center", style="italic")

    for key, title, sub, route in STANDARD:
        cx = BOT_X[key]
        card(ax, cx, BOT_Y, BOT_W, BOT_H, BOT_FC, ORANGE)
        {"hall": icon_hall, "psd": icon_psd, "shear": icon_shear, "tap": icon_tap,
         "moist": icon_moisture}[key](ax, cx, rng)
        ax.text(cx, BOT_Y + 8.0, title, fontsize=7.4, fontweight="bold", color=INK, ha="center", va="center")
        ax.text(cx, BOT_Y + 5.0, sub, fontsize=5.9, color=INK2, ha="center", va="center", linespacing=1.15)
        ax.text(cx, BOT_Y + 1.6, route, fontsize=5.7, color=ORANGE_D, ha="center", va="center",
                style="italic")

    # side boxes: what finds the links, and what else goes in
    for cx, title, body, draw in (
        (8.2, "Physics-based ML", "surrogate models and\nDEM simulations\nfind the links",
         lambda c: icon_ml(ax, c, 55.6, rng)),
        (91.8, "State and history\nof the powder", "composition; how it was\nmade, sieved, dried,\n"
         "stored or reused", lambda c: icon_context(ax, c, 55.4)),
    ):
        card(ax, cx, TOP_Y, SIDE_W, TOP_H, ML_FC, AQUA)
        draw(cx)
        ax.text(cx, TOP_Y + 11.2, title, fontsize=7.4, fontweight="bold", color=AQUA_D, ha="center",
                va="center", linespacing=1.1)
        ax.text(cx, TOP_Y + 4.6, body, fontsize=5.9, color=INK2, ha="center", va="center", linespacing=1.15)

    # the two directions (transcript 09:41)
    ax.add_patch(FancyArrowPatch((2.6, 36.6), (2.6, 23.6), arrowstyle="-|>", mutation_scale=9,
                                 color=AQUA_D, lw=1.2, zorder=6))
    ax.text(3.6, 34.6, "infer the\nproperties of\na new powder", fontsize=5.8, color=AQUA_D, ha="left",
            va="top", linespacing=1.1, zorder=6)
    ax.add_patch(FancyArrowPatch((97.4, 23.6), (97.4, 36.6), arrowstyle="-|>", mutation_scale=9,
                                 color=AQUA_D, lw=1.2, zorder=6))
    ax.text(96.4, 25.6, "known\nproperties\nspeed up\ncalibration", fontsize=5.8, color=AQUA_D, ha="right",
            va="bottom", linespacing=1.1, zorder=6)

    save(fig, name)


if __name__ == "__main__":
    if "--board" in sys.argv[1:]:
        fig_overview_relations(BOARD_LINKS, "fig_overview_relations_board")
    else:
        fig_overview_relations()
