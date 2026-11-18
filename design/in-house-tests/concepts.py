"""Concept sketches of the in-house powder tests built on the doser.

Draws one schematic side view per test (not to scale) and writes concepts.png next to
this file. Grey parts are on the doser already, teal parts are new printed parts and
purple parts are new bought parts.

    python concepts.py
"""
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib import patches  # noqa: E402
from matplotlib.path import Path as MPath  # noqa: E402

HERE = Path(__file__).resolve().parent

EXIST, EXIST_DARK, EXIST_LIGHT = "#9aa1ab", "#5b616b", "#c9ced5"
PRINT, PRINT_DARK = "#2a9d8f", "#1d6f65"
BUY, BUY_DARK, BUY_LIGHT = "#8a6fbf", "#5a4386", "#d9cdef"
POWDER, POWDER_DOT = "#dcb56f", "#9c7433"
GLASS = "#e3f1f7"
LIGHT, LIGHT_EDGE = "#fff2a8", "#d9b93a"
WATER = "#bcd7e6"
TEXT = "#222222"
FS = 7.2


def poly(ax, pts, fc, ec=None, lw=0.9, z=2, ls="-", alpha=1.0):
    p = patches.Polygon(np.asarray(pts, float), closed=True, facecolor=fc,
                        edgecolor=ec if ec else fc, lw=lw, zorder=z, ls=ls, alpha=alpha)
    ax.add_patch(p)
    return p


def rect(ax, x, y, w, h, fc, ec=None, lw=0.9, z=2, ls="-"):
    return poly(ax, [(x, y), (x + w, y), (x + w, y + h), (x, y + h)], fc, ec, lw, z, ls)


def powder(ax, pts, seed=0, z=3, dots=0.09):
    """Fill a polygon with powder colour and stipple it."""
    pts = np.asarray(pts, float)
    poly(ax, pts, POWDER, POWDER_DOT, 0.5, z)
    rng = np.random.default_rng(seed)
    lo, hi = pts.min(0), pts.max(0)
    n = int(dots * (hi - lo).prod()) + 3
    cand = rng.uniform(lo, hi, size=(n, 2))
    inside = MPath(pts).contains_points(cand)
    c = cand[inside]
    ax.scatter(c[:, 0], c[:, 1], s=0.7, color=POWDER_DOT, zorder=z + 0.1, lw=0)


def stream(ax, x0, y0, x1, y1, n=9, seed=1, z=3):
    """A thin stream of falling grains."""
    rng = np.random.default_rng(seed)
    t = np.linspace(0, 1, n)
    xs = x0 + (x1 - x0) * t + rng.normal(0, 0.35, n)
    ys = y0 + (y1 - y0) * t
    ax.scatter(xs, ys, s=3.5, color=POWDER_DOT, zorder=z, lw=0)


def note(ax, xy, xytext, text, ha="left", fs=FS, color=TEXT):
    ax.annotate(text, xy=xy, xytext=xytext, fontsize=fs, ha=ha, va="center", color=color,
                arrowprops=dict(arrowstyle="-", lw=0.55, color="#666666",
                                shrinkA=1, shrinkB=1), zorder=10)


def text(ax, x, y, s, ha="center", fs=FS, color=TEXT, **kw):
    ax.text(x, y, s, ha=ha, va="center", fontsize=fs, color=color, zorder=10, **kw)


def arrow(ax, p0, p1, color=TEXT, lw=0.9, style="-|>", z=9):
    ax.annotate("", xy=p1, xytext=p0, zorder=z,
                arrowprops=dict(arrowstyle=style, lw=lw, color=color,
                                shrinkA=0, shrinkB=0, mutation_scale=7))


def balance(ax, x0=15.0, y0=3.0, w=70.0, label=True):
    """HR-100A balance: body, stem and pan. Returns (pan centre x, pan top y)."""
    rect(ax, x0, y0, w, 9, EXIST, EXIST_DARK)
    rect(ax, x0 + 3, y0 + 2.5, 9, 4, "#e6eaee", EXIST_DARK, lw=0.6)
    cx = x0 + w / 2
    rect(ax, cx - 1.2, y0 + 9, 2.4, 3, EXIST_DARK, EXIST_DARK)
    rect(ax, cx - 12, y0 + 12, 24, 1.6, EXIST_LIGHT, EXIST_DARK)
    if label:
        text(ax, x0 + w - 2, y0 + 4.5, "balance", ha="right", color="white", fs=6.5)
    return cx, y0 + 13.6


def doser(ax, tip, angle, length=38.0, width=6.5, label=None, label_at=None):
    """The auger module: a tube whose exit is at `tip`, tilted `angle` degrees from
    horizontal and rising to the left, with the stepper at its upper end."""
    a = np.radians(angle)
    d = np.array([-np.cos(a), np.sin(a)])
    n = np.array([np.sin(a), np.cos(a)])
    tip = np.asarray(tip, float)
    p0, p1 = tip + n * width / 2, tip - n * width / 2
    poly(ax, [p0, p1, p1 + d * length, p0 + d * length], EXIST, EXIST_DARK)
    top = tip + d * length
    m = [top + n * (width / 2 + 1.4), top - n * (width / 2 + 1.4),
         top - n * (width / 2 + 1.4) + d * 8, top + n * (width / 2 + 1.4) + d * 8]
    poly(ax, m, EXIST_DARK, "#363a40")
    poly(ax, [tip + n * 1.4, tip - n * 1.4, tip - n * 0.9 - d * 1.6, tip + n * 0.9 - d * 1.6],
         EXIST_DARK, EXIST_DARK)
    if label:
        mid = tip + d * length * 0.55
        note(ax, tuple(mid + n * width * 0.5), label_at, label)
    return tip - d * 1.6


def camera(ax, x, y, facing="right", label="camera", label_at=None, ha="left"):
    """Camera body and lens; (x, y) is the front of the lens."""
    if facing == "right":
        rect(ax, x - 11, y - 3.5, 8, 7, BUY, BUY_DARK)
        poly(ax, [(x - 3, y - 2), (x, y - 3), (x, y + 3), (x - 3, y + 2)], BUY_DARK, BUY_DARK)
    elif facing == "left":
        rect(ax, x + 3, y - 3.5, 8, 7, BUY, BUY_DARK)
        poly(ax, [(x + 3, y - 2), (x, y - 3), (x, y + 3), (x + 3, y + 2)], BUY_DARK, BUY_DARK)
    else:  # down
        rect(ax, x - 3.5, y + 3, 7, 8, BUY, BUY_DARK)
        poly(ax, [(x - 2, y + 3), (x - 3, y), (x + 3, y), (x + 2, y + 3)], BUY_DARK, BUY_DARK)
    if label and label_at:
        note(ax, (x - 7 if facing == "right" else x + 7 if facing == "left" else x, y + 3.5
                  if facing != "down" else y + 8), label_at, label, ha=ha)


def backlight(ax, x, y, w, h, label="LED backlight", label_at=None, ha="left"):
    rect(ax, x, y, w, h, LIGHT, LIGHT_EDGE)
    if label_at:
        note(ax, (x + w / 2, y + h * 0.85), label_at, label, ha=ha)


def angle_arc(ax, centre, r, a0, a1, label, label_r=None, fs=FS + 0.5):
    arc = patches.Arc(centre, 2 * r, 2 * r, theta1=a0, theta2=a1, lw=0.9, color=TEXT, zorder=9)
    ax.add_patch(arc)
    am = np.radians((a0 + a1) / 2)
    lr = label_r if label_r else r + 3
    text(ax, centre[0] + lr * np.cos(am), centre[1] + lr * np.sin(am), label, fs=fs,
         style="italic")


def setup(ax, title):
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.text(0, 101, title, ha="left", va="bottom", fontsize=9.5, fontweight="bold", color=TEXT)


# --- the ten panels -------------------------------------------------------------------

def p1_heap(ax):
    setup(ax, "1  Heap angle of repose")
    cx, top = balance(ax)
    # pedestal on the pan
    rect(ax, cx - 2.5, top, 5, 10, PRINT, PRINT_DARK)
    poly(ax, [(cx - 11, top + 10), (cx + 11, top + 10), (cx + 10, top + 13), (cx - 10, top + 13)],
         PRINT, PRINT_DARK)
    base_y = top + 13
    h = 10 * np.tan(np.radians(35))
    powder(ax, [(cx - 10, base_y), (cx + 10, base_y), (cx, base_y + h)], seed=3)
    # catch ring on the chamber floor, clear of the pan
    for x in (cx - 27, cx + 15):
        poly(ax, [(x, 12), (x + 1.2, 12), (x + 1.2, 18.5), (x + 10.8, 18.5), (x + 10.8, 12),
                  (x + 12, 12), (x + 12, 20), (x, 20)], PRINT, PRINT_DARK)
    powder(ax, [(cx - 25.8, 18.5), (cx - 16.2, 18.5), (cx - 16.2, 19.6), (cx - 25.8, 19.6)], seed=4)
    stream(ax, cx + 11, base_y - 0.5, cx + 18, 20.5, n=5, seed=5)
    exit_pt = doser(ax, (cx + 0.2, base_y + h + 9), 45, length=34,
                    label="doser at a fixed tilt", label_at=(2, 92))
    stream(ax, exit_pt[0], exit_pt[1] - 1, cx, base_y + h + 0.8, n=6, seed=6)
    angle_arc(ax, (cx + 10, base_y), 6.5, 145, 180, "θ", label_r=9.5)
    camera(ax, 12, base_y + 6, "right", label="camera", label_at=(1, 52))
    backlight(ax, 94, 26, 3.5, 32, label_at=(99, 68), ha="right")
    note(ax, (cx + 10.5, base_y - 1.5), (63, 44), "20 mm pedestal\non the pan")
    note(ax, (cx - 26.4, 16), (1, 24), "catch ring\n(chamber floor)")
    text(ax, 50, -2.5, "flank fit → AoR · mass drops → avalanches", fs=FS)


def p2_density(ax):
    setup(ax, "2  Bulk and tapped density")
    # fill on the balance
    cx, top = balance(ax, x0=2, w=44, label=False)
    text(ax, 24, 1.0, "1  doser fills it on the balance", fs=FS)
    rect(ax, cx - 7, top, 14, 2.5, PRINT, PRINT_DARK)
    rect(ax, cx - 5, top + 2.5, 10, 30, GLASS, BUY_DARK, lw=1.0)
    powder(ax, [(cx - 4.4, top + 3), (cx + 4.4, top + 3), (cx + 4.4, top + 20),
                (cx - 4.4, top + 20)], seed=7)
    poly(ax, [(cx - 7, top + 33), (cx + 7, top + 33), (cx + 4, top + 30), (cx - 4, top + 30)],
         PRINT, PRINT_DARK)
    tip = doser(ax, (cx + 0.3, top + 41), 50, length=24)
    stream(ax, tip[0], tip[1] - 1, cx, top + 21, n=9, seed=8)
    # tap in the tap collar
    tx = 77
    text(ax, 75, 1.0, "2  doser's solenoid taps it", fs=FS)
    rect(ax, tx - 5, 18, 10, 46, GLASS, BUY_DARK, lw=1.0)
    powder(ax, [(tx - 4.4, 18.6), (tx + 4.4, 18.6), (tx + 4.4, 44), (tx - 4.4, 44)], seed=9)
    ax.plot([tx - 6.5, tx + 6.5], [48, 48], ls="--", lw=0.7, color=POWDER_DOT, zorder=6)
    for yy in np.arange(22, 62, 4):
        ax.plot([tx + 5, tx + 6.6], [yy, yy], lw=0.5, color=BUY_DARK, zorder=6)
    rect(ax, tx - 7, 52, 14, 5, PRINT, PRINT_DARK)
    rect(ax, tx - 7, 24, 14, 5, PRINT, PRINT_DARK)
    rect(ax, tx - 26, 50, 19, 9, EXIST, EXIST_DARK)
    text(ax, tx - 16.5, 54.5, "tap collar", fs=6.3, color="white")
    rect(ax, tx - 26, 24, 12, 7, EXIST_DARK, "#363a40")
    rect(ax, tx - 14, 26.6, 6.8, 1.8, EXIST, EXIST_DARK)
    arrow(ax, (tx - 13, 32.5), (tx - 8, 32.5), lw=0.8)
    text(ax, tx - 20, 36.5, "solenoid", fs=6.5)
    note(ax, (tx + 6.6, 46), (88, 72), "height after\nN taps", ha="left")
    note(ax, (cx + 5, top + 28), (31, 72), "glass tube,\n10–12 mm bore")
    camera(ax, 87, 40, "left", label=None)
    text(ax, 94, 33, "camera", fs=6.5, ha="center")


def p3_tilt(ax):
    setup(ax, "3  Tilting plate: wall friction")
    piv = np.array([16.0, 30.0])
    rect(ax, 8, 4, 16, 22, EXIST, EXIST_DARK)
    text(ax, 16, 13, "tilt\nservo", fs=6.5, color="white")
    ax.add_patch(patches.Circle(piv, 3.2, facecolor=EXIST_DARK, edgecolor="#363a40", zorder=4))
    th = np.radians(24)
    u = np.array([np.cos(th), np.sin(th)])
    v = np.array([-np.sin(th), np.cos(th)])

    def P(s, t):
        return piv + u * s + v * t

    poly(ax, [P(0, -1.5), P(78, -1.5), P(78, 1.5), P(0, 1.5)], PRINT, PRINT_DARK, z=3)
    # ring of powder with a lid, just clear of the plate
    s0 = 38
    poly(ax, [P(s0, 2.1), P(s0 + 1.6, 2.1), P(s0 + 1.6, 12), P(s0, 12)], PRINT, PRINT_DARK, z=4)
    poly(ax, [P(s0 + 18.4, 2.1), P(s0 + 20, 2.1), P(s0 + 20, 12), P(s0 + 18.4, 12)], PRINT,
         PRINT_DARK, z=4)
    powder(ax, [P(s0 + 1.6, 1.5), P(s0 + 18.4, 1.5), P(s0 + 18.4, 10.2), P(s0 + 1.6, 10.2)], seed=10,
           z=3.5)
    poly(ax, [P(s0 + 1.8, 10.3), P(s0 + 18.2, 10.3), P(s0 + 18.2, 13.6), P(s0 + 1.8, 13.6)],
         BUY, BUY_DARK, z=4)
    rect_c = P(70, 1.5)
    poly(ax, [rect_c, rect_c + u * 5, rect_c + u * 5 + v * 2.2, rect_c + v * 2.2], BUY, BUY_DARK,
         z=4)
    arrow(ax, tuple(P(s0 - 1, 16)), tuple(P(s0 - 13, 16)), lw=1.0)
    ax.plot([piv[0], piv[0] + 40], [piv[1], piv[1]], ls="--", lw=0.6, color="#777777", zorder=2)
    angle_arc(ax, tuple(piv), 24, 0, 24, "θ", label_r=27)
    note(ax, tuple(P(s0 + 10, 13.6)), (36, 80), "ring of powder, lid sets\n50–400 Pa")
    note(ax, tuple(P(72.5, 3.7)), (82, 88), "IMU", ha="left")
    note(ax, tuple(P(20, -1.5)), (40, 16), "plate: PLA, steel or glass")
    text(ax, 3, 66, "slides at θ\n→ wall friction", ha="left", fs=FS)
    text(ax, 50, -2.5, "mode B: a layer of set thickness starts to flow", fs=FS)


def p4_psd(ax):
    setup(ax, "4  PSD and shape from images")
    camera(ax, 40, 64, "down", label=None)
    rect(ax, 37.5, 56, 5, 8, BUY_DARK, BUY_DARK)
    note(ax, (43.5, 70), (47, 92), "camera + macro lens", ha="left")
    rect(ax, 14, 44, 52, 2.2, GLASS, BUY_DARK, lw=1.0)
    rect(ax, 14, 33, 6, 11, PRINT, PRINT_DARK)
    rect(ax, 60, 33, 6, 11, PRINT, PRINT_DARK)
    rng = np.random.default_rng(11)
    for x in np.linspace(19, 61, 11):
        r = rng.uniform(0.7, 1.7)
        k = rng.integers(5, 8)
        ang = np.sort(rng.uniform(0, 2 * np.pi, k))
        rr = r * rng.uniform(0.75, 1.15, k)
        poly(ax, np.c_[x + rr * np.cos(ang), 46.2 + r + rr * np.sin(ang)], POWDER, POWDER_DOT, 0.5, 4)
    backlight(ax, 22, 24, 36, 4, label=None)
    for x in np.linspace(26, 54, 6):
        arrow(ax, (x, 29), (x, 42), color=LIGHT_EDGE, lw=0.7)
    note(ax, (24, 28), (4, 14), "light from below")
    note(ax, (62, 46.2), (70, 30), "glass slide,\nscattered grains")
    # zoomed view
    zc = np.array([82.0, 64.0])
    ax.add_patch(patches.Circle(zc, 13, facecolor="#fffbe6", edgecolor=TEXT, lw=0.8, zorder=3))
    for (dx, dy, r, k) in [(-5, 4, 3.0, 7), (4, 5, 2.2, 6), (-1, -5, 3.6, 8), (6, -4, 1.6, 6),
                           (-7, -3, 1.4, 5)]:
        ang = np.sort(rng.uniform(0, 2 * np.pi, k))
        rr = r * rng.uniform(0.7, 1.15, k)
        poly(ax, np.c_[zc[0] + dx + rr * np.cos(ang), zc[1] + dy + rr * np.sin(ang)], "#3b3b3b",
             "#d9473b", 0.8, 4)
    text(ax, 82, 47.5, "outlines → size, shape", fs=FS)


def p5_orifice(ax):
    setup(ax, "5  Orifice cup")
    cx, top = balance(ax)
    # catch cup on the pan
    poly(ax, [(cx - 9, top), (cx + 9, top), (cx + 9, top + 9), (cx + 8, top + 9), (cx + 8, top + 1),
              (cx - 8, top + 1), (cx - 8, top + 9), (cx - 9, top + 9)], EXIST, EXIST_DARK)
    powder(ax, [(cx - 8, top + 1), (cx + 8, top + 1), (cx + 3, top + 4), (cx - 3, top + 4)], seed=12)
    # stand, standing beside the balance
    rect(ax, 4, 3, 3, 60, PRINT, PRINT_DARK)
    rect(ax, 4, 60, 34, 3, PRINT, PRINT_DARK)
    # cup with orifice disc
    y0 = 46
    poly(ax, [(cx - 11, y0), (cx - 9.5, y0), (cx - 9.5, y0 + 24), (cx - 11, y0 + 24)], PRINT,
         PRINT_DARK)
    poly(ax, [(cx + 9.5, y0), (cx + 11, y0), (cx + 11, y0 + 24), (cx + 9.5, y0 + 24)], PRINT,
         PRINT_DARK)
    rect(ax, cx - 11, y0 - 2, 9.6, 2, PRINT_DARK, PRINT_DARK)
    rect(ax, cx + 1.4, y0 - 2, 9.6, 2, PRINT_DARK, PRINT_DARK)
    powder(ax, [(cx - 9.5, y0), (cx + 9.5, y0), (cx + 9.5, y0 + 15), (cx - 9.5, y0 + 15)], seed=13)
    # gate pulled aside by a micro servo
    rect(ax, cx + 4, y0 - 4.2, 15, 1.8, PRINT, PRINT_DARK)
    rect(ax, cx + 19, y0 - 7, 8, 7, BUY, BUY_DARK)
    stream(ax, cx, y0 - 3, cx, top + 5, n=12, seed=14)
    # disc set
    for i, (x, r) in enumerate([(64, 0.6), (73, 1.0), (82, 1.5), (91, 2.2)]):
        ax.add_patch(patches.Ellipse((x, 84), 8, 4, facecolor=PRINT, edgecolor=PRINT_DARK,
                                     zorder=4))
        ax.add_patch(patches.Ellipse((x, 84), 2 * r, r, facecolor="white", edgecolor=PRINT_DARK,
                                     lw=0.6, zorder=5))
    text(ax, 77, 77.5, "discs, 1–6 mm", fs=FS)
    note(ax, (cx - 10, y0 + 20), (10, 80), "cup, filled by the doser")
    note(ax, (cx + 23, y0 - 3.5), (78, 52), "gate on a\nmicro servo")
    note(ax, (cx + 1, top + 14), (66, 28), "balance logs\nthe flow rate")
    text(ax, 50, -2.5, "smallest orifice that flows → strength at 10–50 Pa", fs=FS)


def p6_humidity(ax):
    setup(ax, "6  Humidity chambers")
    rect(ax, 6, 14, 54, 52, "#f7fbfd", BUY_DARK, lw=1.1)
    rect(ax, 4, 66, 58, 3.5, BUY, BUY_DARK)
    rect(ax, 7, 15, 52, 9, WATER, WATER)
    rng = np.random.default_rng(15)
    for _ in range(26):
        x, y = rng.uniform(9, 57), rng.uniform(16, 22.5)
        rect(ax, x, y, 1.3, 1.3, "white", "#8fb3c7", lw=0.4, z=3)
    rect(ax, 20, 24, 2.5, 12, PRINT, PRINT_DARK)
    rect(ax, 43.5, 24, 2.5, 12, PRINT, PRINT_DARK)
    poly(ax, [(15, 36), (51, 36), (51, 40), (49, 40), (49, 38), (17, 38), (17, 40), (15, 40)], PRINT,
         PRINT_DARK)
    powder(ax, [(17, 38), (49, 38), (49, 39.6), (17, 39.6)], seed=16)
    rect(ax, 50, 53, 9, 6, BUY, BUY_DARK)
    note(ax, (50, 56), (30, 78), "RH and T sensor", ha="center")
    note(ax, (30, 21), (18, 6), "saturated salt solution: NaCl holds 75 % RH", ha="left")
    note(ax, (25, 39.6), (14, 50), "thin layer of powder")
    for i, s in enumerate(["weigh before\nand after", "dose before\nand after", "AoR before\nand after"]):
        y = 58 - i * 17
        ax.add_patch(patches.FancyBboxPatch((70, y - 5.5), 27, 11, boxstyle="round,pad=0.6",
                                            facecolor="#f2f2f2", edgecolor="#777777", lw=0.7,
                                            zorder=3))
        text(ax, 83.5, y, s, fs=FS)
        arrow(ax, (61.5, 40), (69, y), lw=0.7)


def p7_drum(ax):
    setup(ax, "7  Rotating drum")
    c = np.array([50.0, 60.0])
    R = 21.0
    ax.add_patch(patches.Circle(c, R + 1.6, facecolor=PRINT, edgecolor=PRINT_DARK, zorder=2))
    ax.add_patch(patches.Circle(c, R, facecolor=GLASS, edgecolor=PRINT_DARK, zorder=2.5))
    for a in np.linspace(0, 2 * np.pi, 24, endpoint=False):
        ax.plot([c[0] + R * np.cos(a), c[0] + (R - 1.4) * np.cos(a)],
                [c[1] + R * np.sin(a), c[1] + (R - 1.4) * np.sin(a)], color=PRINT_DARK, lw=0.7,
                zorder=3)
    th = np.radians(36)
    nrm = np.array([np.sin(th), -np.cos(th)])  # points into the powder
    off = 3.0
    t = np.linspace(0, 2 * np.pi, 400)
    circ = c + (R - 1.4) * np.c_[np.cos(t), np.sin(t)]
    keep = (circ - c) @ nrm > -off
    pts = circ[keep]
    ang = np.arctan2(pts[:, 1] - c[1], pts[:, 0] - c[0])
    order = np.argsort(np.unwrap(ang - ang[0]))
    powder(ax, pts[order], seed=17)
    ax.plot([c[0] - 24, c[0] + 4], [c[1] - 24 * np.tan(th) * 0 + 0, c[1]], lw=0)
    # free-surface angle against the horizontal
    p_low = c + np.array([np.cos(th), np.sin(th)]) * (R - 4) - nrm * off
    ax.plot([p_low[0], p_low[0] - 16], [p_low[1], p_low[1]], ls="--", lw=0.6, color="#555555",
            zorder=6)
    angle_arc(ax, tuple(p_low), 10, 180, 180 + 36, "θ", label_r=13)
    ax.add_patch(patches.FancyArrowPatch((c[0] - 18, c[1] + 18), (c[0] + 18, c[1] + 18),
                                         connectionstyle="arc3,rad=-0.45", arrowstyle="-|>",
                                         mutation_scale=8, lw=0.9, color=TEXT, zorder=7))
    text(ax, 50, 91, "1–20 rpm", fs=FS)
    # side view: stepper, drum, window, camera
    rect(ax, 12, 10, 14, 13, EXIST_DARK, "#363a40")
    text(ax, 19, 16.5, "stepper", fs=6.3, color="white")
    rect(ax, 26, 15.4, 8, 2.2, EXIST, EXIST_DARK)
    rect(ax, 34, 8, 12, 17, PRINT, PRINT_DARK)
    rect(ax, 46, 8, 1.6, 17, GLASS, BUY_DARK)
    camera(ax, 63, 16.5, "left", label=None)
    text(ax, 79, 16.5, "camera looks\nalong the axis", fs=6.5, ha="left")
    text(ax, 30, 29, "side view: drum in place of the auger, module level", fs=6.5)
    note(ax, (c[0] + 7, c[1] - 12), (82, 44), "surface angle,\navalanches")


def p8_ucs(ax):
    setup(ax, "8  Unconfined strength")
    rect(ax, 14, 3, 4, 86, PRINT, PRINT_DARK)
    rect(ax, 82, 3, 4, 86, PRINT, PRINT_DARK)
    rect(ax, 14, 86, 72, 4, PRINT, PRINT_DARK)
    rect(ax, 26, 6, 48, 6, BUY, BUY_DARK)
    text(ax, 50, 9, "500 g load cell", fs=6.5, color="white")
    rect(ax, 35, 12, 30, 3, PRINT, PRINT_DARK)
    powder(ax, [(41, 15), (59, 15), (59, 47), (41, 47)], seed=18)
    for x0, dx in ((30.5, -1), (61.5, 1)):
        rect(ax, x0, 15, 8, 34, "none", PRINT_DARK, lw=0.9, ls="--")
        arrow(ax, (x0 + 4, 32), (x0 + 4 + 7 * dx, 32), lw=0.8)
    text(ax, 50, 53.5, "", fs=6)
    rect(ax, 37, 51, 26, 3.2, EXIST_LIGHT, EXIST_DARK)
    ax.plot([50, 50], [54.2, 76], color=EXIST_DARK, lw=2.2, zorder=3)
    for yy in np.arange(56, 76, 2):
        ax.plot([48.6, 51.4], [yy, yy + 1], color=EXIST_DARK, lw=0.6, zorder=3)
    rect(ax, 43, 76, 14, 10, EXIST_DARK, "#363a40")
    text(ax, 50, 81, "NEMA 11", fs=6.2, color="white")
    arrow(ax, (66, 64), (66, 55), lw=1.0)
    text(ax, 68, 60, "0.1 mm/s", fs=FS, ha="left")
    note(ax, (36, 38), (2, 60), "split mould,\nopened", ha="left")
    text(ax, 50, -2.5, "peak force ÷ area = σc  →  ffc at 0.2–2 kPa", fs=FS)


def p9_spread(ax):
    setup(ax, "9  Blade spreading")
    rect(ax, 6, 28, 88, 4, BUY_LIGHT, BUY_DARK)
    powder(ax, [(8, 32), (51.5, 32), (51.5, 33.1), (8, 33.1)], seed=20, dots=0.25)
    powder(ax, [(53.6, 32), (66, 32), (60, 38), (55.4, 38.5)], seed=19)
    poly(ax, [(51.6, 32.6), (53.6, 32.6), (51.5, 54), (49.5, 54)], EXIST_LIGHT, EXIST_DARK)
    rect(ax, 42, 54, 16, 8, PRINT, PRINT_DARK)
    ax.plot([6, 94], [62.8, 62.8], color=EXIST_DARK, lw=1.2, zorder=1)
    arrow(ax, (62, 67), (80, 67), lw=1.1)
    text(ax, 71, 71, "10–100 mm/s", fs=FS)
    camera(ax, 26, 72, "down", label=None)
    text(ax, 31, 78, "camera", fs=6.5, ha="left")
    rect(ax, 0.5, 35, 4, 4, LIGHT, LIGHT_EDGE)
    for dy in (0.0, 1.5):
        ax.plot([4.5, 30], [36.5 + dy, 33.4 + dy * 0.3], color=LIGHT_EDGE, lw=0.6, zorder=2)
    note(ax, (20, 28), (8, 14), "coupon; blade gap 100–200 µm set by shims")
    note(ax, (36, 33.1), (22, 48), "spread layer")
    note(ax, (62, 36), (70, 46), "pile pushed by\nthe blade, laid\nby the doser")
    text(ax, 50, -2.5, "coverage · layer mass (weigh the coupon) · streaks", fs=FS)


def p10_faraday(ax):
    setup(ax, "10  Faraday cup")
    poly(ax, [(26, 14), (74, 14), (74, 58), (71, 58), (71, 17), (29, 17), (29, 58), (26, 58)],
         BUY, BUY_DARK)
    poly(ax, [(36, 23), (64, 23), (64, 54), (62, 54), (62, 25), (38, 25), (38, 54), (36, 54)],
         BUY_LIGHT, BUY_DARK)
    for x in (37, 59):
        rect(ax, x, 17, 4, 6, PRINT, PRINT_DARK)
    powder(ax, [(38, 25), (62, 25), (58, 30), (42, 30)], seed=22)
    tip = doser(ax, (50, 76), 60, length=17)
    stream(ax, tip[0], tip[1] - 1, 50, 31, n=12, seed=23)
    ax.plot([64, 80], [40, 40], color=TEXT, lw=0.8, zorder=1)
    rect(ax, 80, 33, 17, 14, BUY, BUY_DARK)
    text(ax, 88.5, 40, "nC", fs=8, color="white")
    text(ax, 88.5, 27.5, "charge\nmeter", fs=6.8)
    ax.plot([26, 16, 16], [30, 30, 24], color=TEXT, lw=0.8)
    for i, w in enumerate((6, 4, 2)):
        ax.plot([16 - w / 2, 16 + w / 2], [24 - 1.6 * i, 24 - 1.6 * i], color=TEXT, lw=0.8)
    text(ax, 16, 16, "ground", fs=6.5)
    note(ax, (62, 50), (78, 64), "inner cup,\ninsulated")
    note(ax, (72.5, 56), (80, 78), "grounded can")
    note(ax, (39, 20), (8, 6), "insulating spacers")
    text(ax, 50, -2.5, "charge ÷ dosed mass → q/m (C/kg)", fs=FS)


def main():
    fig, axes = plt.subplots(2, 5, figsize=(19, 8.6))
    panels = [p1_heap, p2_density, p3_tilt, p4_psd, p5_orifice,
              p6_humidity, p7_drum, p8_ucs, p9_spread, p10_faraday]
    for ax, f in zip(axes.ravel(), panels):
        f(ax)
    handles = [patches.Patch(facecolor=EXIST, edgecolor=EXIST_DARK, label="on the doser now"),
               patches.Patch(facecolor=PRINT, edgecolor=PRINT_DARK, label="new printed part"),
               patches.Patch(facecolor=BUY, edgecolor=BUY_DARK, label="new bought part"),
               patches.Patch(facecolor=POWDER, edgecolor=POWDER_DOT, label="powder")]
    fig.legend(handles=handles, loc="lower center", ncol=4, frameon=False, fontsize=9.5,
               bbox_to_anchor=(0.5, -0.005))
    fig.suptitle("In-house powder tests built on the doser: concept sketches, not to scale",
                 fontsize=12.5, y=0.995)
    fig.subplots_adjust(left=0.01, right=0.99, top=0.93, bottom=0.07, wspace=0.08, hspace=0.22)
    out = HERE / "concepts.png"
    fig.savefig(out, dpi=130, facecolor="white")
    print("wrote", out)


if __name__ == "__main__":
    main()
