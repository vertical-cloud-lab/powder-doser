#!/usr/bin/env python3
"""Overview figure: cheap doser measurements related to standard powder tests.

Drawn from the whiteboard sketch made by Sterling and Will on 2026-10-28 and
the corrected transcript of that meeting
(``meetings/2026-10-28-sterling-will.md``, 38:27-48:52 and main point 8).
Three tiers, read top to bottom:

* (a) cheap, on the doser: feed factor at several tilts; the "ghost dose" (a
  transparent doser, outlet closed, tapped, giving bulk and tapped density);
  angle of repose of the pile the doser pours. A solid border means measured,
  a dashed border proposed (the convention of Fig. 1b).
* (b) the relational matrix that physics-based ML (surrogate models and DEM
  simulations) learns between the two rows, with the state and history of the
  powder as extra inputs. Filled dots are the links drawn on the board; open dots
  are the other pairs, which the model tests as well (Sterling at 47:17 asked for
  a matrix, and the questions on the board were all-to-one). The two arrows are
  the two uses Sterling described at 09:41.
* (c) the standard tests people measure and care about: Hall/Carney flow, PSD
  (SEM images in BSE mode, or laser diffraction), shear cell, tapped density,
  moisture, each with the route to a number (in-house or an outside lab).

Each card carries a 3D still (``figures/stills/``, made by
``figures/render3d/render_stills.py``): the standard tests are stills from the
animated walkthroughs of PR #190, and the three doser measurements are new scenes
built with the same toolkit around the doser's CAD from PR #170. The DEM icon is
drawn here: shaded spheres from a seeded random deposition, not a simulation.

The figure is a schematic; it shows no data.

Usage (from paper/optimization/):
    python3 figures/make_overview_relations.py
Writes figures/fig_overview_relations.{pdf,png}.
"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Circle, FancyArrowPatch, FancyBboxPatch, Polygon, Rectangle

from make_figures import AQUA, BLUE, DOUBLE, INK, INK2, ORANGE, save

STILLS = Path(__file__).resolve().parent / "stills"

# ------------------------------------------------------------------ colours
SAND = "#d9c49a"                                # powder (as in the stills)
TOP_FC, BOT_FC, ML_FC = "#eef4fd", "#fdf1ea", "#eaf7f1"  # card fills; the stills are rendered on the first two
AQUA_D = "#11815a"                              # text and marks on the green band (contrast)
BLUE_D, ORANGE_D = "#1d5fae", "#b8481c"         # tier headers, row/column labels

# Type sizes (pt at 190 mm).  Elsevier asks for 7 pt normal text at the printed size
# and for lettering that does not vary much, so three sizes: 9 (panel letters),
# 8 (titles) and 7 (everything else).
F_PANEL, F_TITLE, F_BODY = 9.0, 8.0, 7.0

# -------------------------------------------------------------------- nodes
# Doser measurements: (key, title, subtitle, measured?, short name for the matrix)
DOSER = [
    ("ff", "Feed factor", "mg per auger revolution at three\ntilts; before and after humid air", True,
     "Feed factor"),
    ("gd", "“Ghost dose”", "transparent doser, outlet closed,\ntapped: bulk and tapped density", False,
     "Ghost dose"),
    ("aor", "Angle of repose", "a camera on the pile\nthe doser pours", False, "Angle of repose"),
]
# Standard tests: (key, title, subtitle, route to a number, short name for the matrix)
STANDARD = [
    ("hall", "Hall/Carney flow", "50 g through a funnel\nASTM B213, B964", "in-house", "Hall"),
    ("psd", "Particle size (PSD)", "SEM (BSE) images or\nlaser diffraction", "in-house or outside lab",
     "PSD"),
    ("shear", "Shear cell, $ff_c$", "flowability under load\nASTM D6773, D7891", "outside lab", "Shear"),
    ("tap", "Tapped density", "graduated cylinder\nASTM B527", "in-house", "Tap"),
    ("moist", "Moisture", "loss on drying:\nweigh, dry, reweigh", "in-house", "Moisture"),
]
# Links drawn on the 28 Oct board (green lines), read from the photo: filled dots.
BOARD_LINKS = {("ff", "hall"), ("ff", "psd"), ("gd", "hall"), ("gd", "shear"),
               ("aor", "hall"), ("aor", "psd"), ("aor", "shear"), ("aor", "tap")}
# The ghost dose measures tapped density itself ("tap density" is written under the
# transparent doser on the board), so that cell is the same quantity, not a learned link.
SAME = {("gd", "tap")}

# ------------------------------------------------------------------ layout
# Data units: the figure is W = 100 wide (190 mm, so 1 unit = 1.9 mm); y runs up.
W = 100.0
BOT_W, BOT_H, BOT_PITCH = 18.6, 26.0, 20.0     # (c) five standard-test cards
BOT_X = {k: 10.0 + BOT_PITCH * i for i, (k, *_) in enumerate(STANDARD)}
BOT_Y = 0.0
BOT_TEXT = 10.4                                 # height of a bottom card's text block
HEAD_GAP = 4.4                                  # room for the (c) header above the bottom row
BAND_X0, BAND_X1 = 5.4, 94.6                    # (b) the green band
BAND_Y = BOT_Y + BOT_H + HEAD_GAP
BAND_H = 19.0
TOP_W, TOP_H = 25.0, 27.0                       # (a) three doser cards
TOP_X = {"ff": 22.5, "gd": 50.0, "aor": 77.5}
TOP_Y = BAND_Y + BAND_H + 2.4
TOP_TEXT = 8.6
Y1 = TOP_Y + TOP_H + 4.2                        # top of the figure
Y0 = -0.4
USE_X = (2.2, 97.8)                             # the two side arrows (the two uses)
STILL_DPI = 450   # the stills are resampled to this, so the PDF stays small


def card(ax, cx, y, w, h, fc, ec, dashed=False):
    ax.add_patch(FancyBboxPatch((cx - w / 2, y), w, h, boxstyle="round,pad=0,rounding_size=1.0",
                                fc=fc, ec=ec, lw=0.9, ls=(0, (3.2, 1.8)) if dashed else "-", zorder=1))


def header(ax, x, y, letter, text, color):
    """Panel letter and tier title, left-aligned on one baseline."""
    t = ax.text(x, y, f"({letter})", fontsize=F_PANEL, fontweight="bold", color=INK, ha="left", va="baseline")
    ax.text(x + 4.2, y, text, fontsize=F_TITLE, fontweight="bold", color=color, ha="left", va="baseline")
    return t


# -------------------------------------------------------------- 3D stills
def place_still(ax, key, x0, y0, w, h):
    """Draw stills/<key>.png fitted (aspect kept) and centred in the box; return its extent."""
    from PIL import Image
    im = Image.open(STILLS / f"{key}.png").convert("RGB")
    aspect = im.width / im.height
    ew, eh = (h * aspect, h) if w / h > aspect else (w, w / aspect)
    ex0, ey0 = x0 + (w - ew) / 2, y0 + (h - eh) / 2
    px_h = int(round(eh / W * DOUBLE * STILL_DPI))
    if px_h < im.height:
        im = im.resize((max(1, int(round(px_h * aspect))), px_h), Image.LANCZOS)
    ax.imshow(np.asarray(im), extent=(ex0, ex0 + ew, ey0, ey0 + eh), zorder=2, interpolation="antialiased")
    return ex0, ey0, ew, eh


def anchor(ext, info, name):
    """Where a labelled feature of a still lands, in data units."""
    ex0, ey0, ew, eh = ext
    u, v = info["anchors"][name]
    return np.array([ex0 + u * ew, ey0 + (1 - v) * eh])


def label_ghost_dose(ax, ext, info):
    for name, ls in (("bulk", (0, (2, 1.4))), ("tapped", "-")):
        x, y = anchor(ext, info, name)
        ax.plot([x - 2.2, x - 0.1], [y, y], color=BLUE_D, lw=0.8, ls=ls, zorder=7)
        ax.text(x - 2.4, y, name, fontsize=F_BODY, color=BLUE_D, ha="right", va="center", zorder=7)
    x, y = anchor(ext, info, "tap")
    ax.text(x - 0.2, y + 1.1, "tap", fontsize=F_BODY, color=INK2, ha="center", va="bottom", zorder=7)
    x, y = anchor(ext, info, "closed")
    ax.plot([x + 0.1, x + 1.6], [y, y], color=INK2, lw=0.5, zorder=7)
    ax.text(x + 1.8, y, "closed", fontsize=F_BODY, color=INK2, ha="left", va="center", zorder=7)


def label_angle(ax, ext, info):
    """The angle of repose, drawn at the right foot of the pile's outline."""
    foot, along, apex = (anchor(ext, info, k) for k in ("foot", "along", "apex"))
    a0 = np.degrees(np.arctan2(*(along - foot)[::-1]))
    a1 = np.degrees(np.arctan2(*(apex - foot)[::-1]))
    a1 = a0 + (a1 - a0 + 180.0) % 360.0 - 180.0  # the short way round, from the base up to the slope
    r = 3.4
    th = np.radians(np.linspace(a0, a1, 24))
    ax.plot(foot[0] + r * np.cos(th), foot[1] + r * np.sin(th), color=BLUE_D, lw=0.9, zorder=7)
    ax.plot(*np.c_[foot, foot + 3.0 * (along - foot) / np.linalg.norm(along - foot)], color=BLUE_D, lw=0.6,
            ls=(0, (1.6, 1.0)), zorder=7)
    ax.text(foot[0] + 0.8, foot[1] + 1.0, "θ", fontsize=F_BODY, color=BLUE_D, ha="left", va="center", zorder=7)


LABELS = {"gd": label_ghost_dose, "aor": label_angle}


# ------------------------------------------------------------- band icons
def dem_heap(rng, w_px=400, h_px=232, r0=10.0, bg=ML_FC):
    """A DEM-style picture: a heap of shaded spheres on a jittered close packing.

    Two layers (the back one offset and darker) clipped to a 34 degree heap, with a
    stream pouring onto its apex, shaded per pixel (Lambert plus a Phong highlight) so it
    reads like the 3D stills. Illustrative only: the packing is drawn, not simulated.
    """
    slope = np.tan(np.radians(34.0))
    discs = []
    for layer, (ox, oy, dark) in enumerate(((r0 * 0.9, r0 * 0.55, 0.80), (0.0, 0.0, 1.0))):
        row, y = 0, r0 + oy
        while y < h_px - r0:
            x = r0 + (r0 if row % 2 else 0.0) + ox
            while x < w_px - r0:
                if y - r0 * 0.4 <= (w_px * 0.47 - abs(x - w_px / 2)) * slope:
                    discs.append((x + rng.uniform(-1.2, 1.2), y + rng.uniform(-1.0, 1.0),
                                  r0 * rng.uniform(0.80, 0.97), dark))
                x += 2 * r0
            y += np.sqrt(3.0) * r0
            row += 1
    apex = w_px * 0.47 * slope
    for y in np.arange(apex + 2.6 * r0, h_px - r0, 2.3 * r0):  # the falling stream
        discs.append((w_px / 2 + rng.uniform(-0.5, 0.5) * r0, y, r0 * rng.uniform(0.80, 0.95), 1.0))
    img = np.empty((h_px, w_px, 3))
    img[:] = np.array([int(bg[i:i + 2], 16) for i in (1, 3, 5)]) / 255.0
    yy, xx = np.mgrid[0:h_px, 0:w_px] + 0.5
    light = np.array([-0.45, 0.55, 0.70])
    light /= np.linalg.norm(light)
    half = (light + np.array([0, 0, 1.0])) / np.linalg.norm(light + np.array([0, 0, 1.0]))
    tones = [np.array([0.85, 0.77, 0.60]), np.array([0.79, 0.69, 0.51]), np.array([0.89, 0.82, 0.67])]
    for i, (cx, cy, r, dark) in enumerate(discs):
        sx = slice(max(0, int(cx - r) - 1), min(w_px, int(cx + r) + 2))
        sy = slice(max(0, int(cy - r) - 1), min(h_px, int(cy + r) + 2))
        dx, dy = (xx[sy, sx] - cx) / r, (yy[sy, sx] - cy) / r
        d2 = dx ** 2 + dy ** 2
        m = d2 < 1.0
        nrm = np.stack([dx, dy, np.sqrt(np.clip(1.0 - d2, 0, 1))], -1)
        diff = np.clip(nrm @ light, 0, 1)
        spec = np.clip(nrm @ half, 0, 1) ** 40
        col = tones[int(rng.integers(3))] * dark
        shade = col * (0.38 + 0.62 * diff[..., None]) + 0.40 * dark * spec[..., None]
        rim = np.clip((1.0 - d2) * r / 1.5, 0, 1)[..., None]  # a soft dark rim
        img[sy, sx][m] = np.clip((shade * (0.6 + 0.4 * rim))[m], 0, 1)
    return img[::-1]  # row 0 at the top for imshow


def icon_ml(ax, x0, y0, rng):
    """DEM heap (left) and a surrogate model with its uncertainty band (right)."""
    w, h = 9.2, 6.0
    ax.add_patch(Rectangle((x0, y0), w, h, fc=ML_FC, ec=AQUA, lw=0.6, zorder=3))
    iw = w - 0.4
    ax.imshow(dem_heap(rng), extent=(x0 + 0.2, x0 + 0.2 + iw, y0 + 0.25, y0 + 0.25 + iw * 232 / 400), zorder=3,
              interpolation="antialiased")
    ax.plot([x0 + 0.2, x0 + w - 0.2], [y0 + 0.25] * 2, color=INK2, lw=0.8, zorder=4)
    g0 = x0 + w + 0.8
    ax.add_patch(Rectangle((g0, y0), w, h, fc="white", ec=AQUA, lw=0.6, zorder=3))
    x = np.linspace(g0 + 0.5, g0 + w - 0.5, 80)
    s = (x - g0) / w
    mu = y0 + h * (0.48 + 0.26 * np.sin(2 * np.pi * (s * 0.9 + 0.05)))
    sd = h * (0.05 + 0.13 * np.abs(np.sin(np.pi * (s - 0.32) * 1.4)))
    ax.fill_between(x, mu - sd, mu + sd, color=AQUA, alpha=0.25, lw=0, zorder=4)
    ax.plot(x, mu, color=AQUA_D, lw=1.0, zorder=5)
    pts = np.array([0.12, 0.33, 0.62, 0.86])
    xs = g0 + 0.5 + pts * (w - 1.0)
    ss = (xs - g0) / w
    ax.scatter(xs, y0 + h * (0.48 + 0.26 * np.sin(2 * np.pi * (ss * 0.9 + 0.05))), s=6, c=INK, zorder=6,
               edgecolors="none")


def icon_history(ax, x0, x1, y):
    """What happened to the powder, as a timeline."""
    steps = ("made", "sieved", "dried", "stored", "reused")
    ax.add_patch(FancyArrowPatch((x0, y), (x1 + 1.3, y), arrowstyle="-|>", mutation_scale=7, color=AQUA_D,
                                 lw=0.9, zorder=4, shrinkA=0, shrinkB=0))
    for i, t in enumerate(steps):
        xx = x0 + (x1 - x0) * i / (len(steps) - 1)
        ax.add_patch(Circle((xx, y), 0.42, fc=AQUA_D, ec=ML_FC, lw=0.5, zorder=5))
        above = i % 2 == 0  # alternate labels above and below the line so they fit
        ax.text(xx, y + 1.0 if above else y - 1.0, t, fontsize=F_BODY, color=AQUA_D, ha="center",
                va="bottom" if above else "top", zorder=5)


def relational_matrix(ax, x0, y_top, cw=6.3, ch=2.9):
    """Rows: doser measurements; columns: standard tests. Returns the grid's right and bottom edges."""
    n_r, n_c = len(DOSER), len(STANDARD)
    for j, s in enumerate(STANDARD):
        ax.text(x0 + (j + 0.5) * cw, y_top + 0.7, s[4], fontsize=F_BODY, color=ORANGE_D, ha="center",
                va="bottom")
    for i, d in enumerate(DOSER):
        ax.text(x0 - 0.9, y_top - (i + 0.5) * ch, d[4], fontsize=F_BODY, color=BLUE_D, ha="right", va="center")
    ax.add_patch(Rectangle((x0, y_top - n_r * ch), n_c * cw, n_r * ch, fc="white", ec=AQUA, lw=0.7, zorder=3))
    for j in range(1, n_c):
        ax.plot([x0 + j * cw] * 2, [y_top, y_top - n_r * ch], color=AQUA, lw=0.35, alpha=0.6, zorder=3)
    for i in range(1, n_r):
        ax.plot([x0, x0 + n_c * cw], [y_top - i * ch] * 2, color=AQUA, lw=0.35, alpha=0.6, zorder=3)
    for i, d in enumerate(DOSER):
        for j, s in enumerate(STANDARD):
            mark(ax, (x0 + (j + 0.5) * cw, y_top - (i + 0.5) * ch),
                 "same" if (d[0], s[0]) in SAME else "board" if (d[0], s[0]) in BOARD_LINKS else "open")
    return x0 + n_c * cw, y_top - n_r * ch


def mark(ax, c, kind, s=1.0):
    """● a link drawn on the board, ○ a pair the model tests too, ◆ the same quantity."""
    if kind == "board":
        ax.add_patch(Circle(c, 0.80 * s, fc=AQUA_D, ec="none", zorder=4))
    elif kind == "open":
        ax.add_patch(Circle(c, 0.66 * s, fc="white", ec=AQUA_D, lw=0.9, zorder=4))
    else:
        d = 0.95 * s
        ax.add_patch(Polygon([(c[0], c[1] + d), (c[0] + d, c[1]), (c[0], c[1] - d), (c[0] - d, c[1])],
                             closed=True, fc=BLUE_D, ec="none", zorder=4))


def key_row(ax, items, xc, y, gap=2.6, pad=1.9):
    """One centred row of (mark kind, label) pairs."""
    widths = []
    for _, txt in items:  # measure first, then draw centred
        t = ax.text(0, y, txt, fontsize=F_BODY)
        widths.append(_bbox(ax, t).width)
        t.remove()
    x = xc - (sum(widths) + len(items) * pad + (len(items) - 1) * gap) / 2
    for (kind, txt), w in zip(items, widths):
        mark(ax, (x + 0.6, y), kind, s=0.85)
        ax.text(x + pad, y, txt, fontsize=F_BODY, color=INK2, ha="left", va="center")
        x += pad + w + gap


def _bbox(ax, t):
    return t.get_window_extent(ax.figure.canvas.get_renderer()).transformed(ax.transData.inverted())


def text_right(ax, t):
    """Right edge of a drawn text, in data units."""
    return _bbox(ax, t).x1


def text_left(ax, t):
    """Left edge of a drawn text, in data units."""
    return _bbox(ax, t).x0


# ------------------------------------------------------------------ figure
def fig_overview_relations(name="fig_overview_relations"):
    rng = np.random.default_rng(7)
    info = json.loads((STILLS / "anchors.json").read_text())
    fig = plt.figure(figsize=(DOUBLE, DOUBLE * (Y1 - Y0) / W))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, W)
    ax.set_ylim(Y0, Y1)
    ax.set_aspect("equal")
    ax.set_autoscale_on(False)
    ax.axis("off")

    # ---------------------------------------------------------- (a) doser
    hy = Y1 - 2.4
    header(ax, 0.6, hy, "a", "Cheap: measured on the doser itself", BLUE_D)
    kx = W - 0.6                                   # key, laid out right to left
    for dashed, txt in ((True, "proposed"), (False, "measured (13 powders)")):
        t = ax.text(kx, hy, txt, fontsize=F_BODY, color=INK2, ha="right", va="baseline")
        x_left = text_left(ax, t)
        ax.add_patch(FancyBboxPatch((x_left - 3.8, hy - 0.35), 3.0, 1.9, boxstyle="round,pad=0,rounding_size=0.45",
                                    fc=TOP_FC, ec=BLUE, lw=0.8, ls=(0, (2.4, 1.4)) if dashed else "-"))
        kx = x_left - 3.8 - 2.4
    for key, title, sub, measured, _ in DOSER:
        cx = TOP_X[key]
        card(ax, cx, TOP_Y, TOP_W, TOP_H, TOP_FC, BLUE, dashed=not measured)
        ext = place_still(ax, key, cx - TOP_W / 2 + 0.8, TOP_Y + TOP_TEXT, TOP_W - 1.6, TOP_H - TOP_TEXT - 0.7)
        if key in LABELS:
            LABELS[key](ax, ext, info[key])
        ax.text(cx, TOP_Y + 6.6, title, fontsize=F_TITLE, fontweight="bold", color=INK, ha="center",
                va="center")
        ax.text(cx, TOP_Y + 2.9, sub, fontsize=F_BODY, color=INK2, ha="center", va="center", linespacing=1.2)

    # ----------------------------------------------- (b) the green band
    ax.add_patch(FancyBboxPatch((BAND_X0, BAND_Y), BAND_X1 - BAND_X0, BAND_H,
                                boxstyle="round,pad=0,rounding_size=1.0", fc=ML_FC, ec=AQUA, lw=0.9, zorder=1))
    yb = BAND_Y + BAND_H
    ty = yb - 2.6                                   # one baseline for the band's three titles
    ax.text(BAND_X0 + 1.0, ty, "(b)", fontsize=F_PANEL, fontweight="bold", color=INK, ha="left",
            va="baseline")
    # left: what finds the links
    lx = BAND_X0 + 5.2
    ax.text(lx, ty, "Physics-based ML", fontsize=F_TITLE, fontweight="bold", color=AQUA_D, ha="left",
            va="baseline")
    ax.text(lx, ty - 1.6, "surrogate models and\nDEM simulations", fontsize=F_BODY, color=INK2,
            ha="left", va="top", linespacing=1.2)
    icon_ml(ax, lx, BAND_Y + 1.6, rng)
    # centre: the relational matrix
    cw, ch = 6.2, 2.7
    mx0 = lx + 2 * 9.2 + 0.8 + 13.0                 # clear of the ML icons and the row labels
    ax.text(mx0 + 2.5 * cw, ty, "Relational matrix", fontsize=F_TITLE, fontweight="bold",
            color=AQUA_D, ha="center", va="baseline")
    m_right, m_bot = relational_matrix(ax, mx0, ty - 4.3, cw=cw, ch=ch)
    key_row(ax, (("board", "expected"), ("open", "to be tested"), ("same", "same quantity")),
            (mx0 - 11.5 + m_right) / 2, m_bot - 1.9)
    # right: what else goes in, as a dashed input box with an arrow into the matrix
    rx = BAND_X1 - 1.4
    sx0 = m_right + 2.8
    ax.add_patch(FancyBboxPatch((sx0, BAND_Y + 0.9), rx + 0.5 - sx0, BAND_H - 1.8,
                                boxstyle="round,pad=0,rounding_size=0.8", fc="white", ec=AQUA_D, lw=0.7,
                                ls=(0, (2.4, 1.4)), zorder=1.5))
    ym = (ty - 4.3) - 1.5 * ch
    ax.add_patch(FancyArrowPatch((sx0, ym), (m_right + 0.15, ym), arrowstyle="-|>", mutation_scale=8,
                                 color=AQUA_D, lw=1.0, zorder=5, shrinkA=0, shrinkB=0))
    sc = (sx0 + rx + 0.5) / 2                       # centre of the input box
    for k, line in enumerate(("Powder state", "and history")):
        ax.text(sc, ty - 1.9 * k, line, fontsize=F_TITLE, fontweight="bold", color=AQUA_D, ha="center",
                va="baseline")
    ax.text(sc, ty - 3.5, "composition, and\nhow it was handled", fontsize=F_BODY, color=INK2, ha="center",
            va="top", linespacing=1.2)
    icon_history(ax, sx0 + 2.2, rx - 2.6, BAND_Y + 3.4)

    # ---------------------------------------------------------- (c) standard
    header(ax, 0.6, BOT_Y + BOT_H + 1.3, "c",
           "Standard tests: a separate instrument for each, some only in outside labs", ORANGE_D)
    for key, title, sub, route, _ in STANDARD:
        cx = BOT_X[key]
        card(ax, cx, BOT_Y, BOT_W, BOT_H, BOT_FC, ORANGE)
        place_still(ax, key, cx - BOT_W / 2 + 0.7, BOT_Y + BOT_TEXT, BOT_W - 1.4, BOT_H - BOT_TEXT - 0.7)
        ax.text(cx, BOT_Y + 8.4, title, fontsize=F_TITLE, fontweight="bold", color=INK, ha="center",
                va="center")
        ax.text(cx, BOT_Y + 4.9, sub, fontsize=F_BODY, color=INK2, ha="center", va="center", linespacing=1.2)
        ax.text(cx, BOT_Y + 1.5, route, fontsize=F_BODY, color=INK2, ha="center", va="center",
                style="italic")

    # ------------------------------- the two uses (transcript 09:41), full height
    top, bot = TOP_Y + TOP_H - 0.6, BAND_Y - 0.9
    for x, (y0, y1), txt, rot, dx in ((USE_X[0], (top, bot), "infer the properties of a new powder", -90, 1.3),
                                      (USE_X[1], (bot, top), "known properties speed up calibration", 90, -1.3)):
        ax.add_patch(FancyArrowPatch((x, y0), (x, y1), arrowstyle="-|>", mutation_scale=10, color=AQUA_D,
                                     lw=1.4, zorder=5, shrinkA=0, shrinkB=0))
        ax.text(x + dx, TOP_Y + TOP_H / 2, txt, fontsize=F_BODY, color=AQUA_D, ha="center", va="center",
                rotation=rot, rotation_mode="anchor")

    save(fig, name)


if __name__ == "__main__":
    fig_overview_relations()
