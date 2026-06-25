#!/usr/bin/env python3
"""Generate a labelled schematic panel of the carousel indexing/holding
mechanisms and commercial/open-source reference systems surveyed in
BILL-OF-MATERIALS.md §5.2.

These are *original schematic line drawings* (not product photos) so the
panel can be committed without copyright concerns; each tile illustrates the
operating principle of the named mechanism so a reader can quickly tell what
"Geneva drive", "barrel-cam indexer", "paternoster", etc. refer to.

Run:  python3 make_panel.py
Out:  carousel-mechanism-panel.png  (+ .svg)
"""
import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import (
    Circle,
    Rectangle,
    FancyArrow,
    Wedge,
    RegularPolygon,
    FancyArrowPatch,
    Polygon,
)

ACCENT = "#1f6feb"   # chosen / highlight
INK = "#222222"
GREY = "#888888"
FILL = "#dce6f7"
WARN = "#c2410c"     # rejected / caveat


def _frame(ax, title, subtitle=None, accent=False):
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10)
    ax.set_aspect("equal")
    ax.set_xticks([])
    ax.set_yticks([])
    for s in ax.spines.values():
        s.set_edgecolor(ACCENT if accent else "#cccccc")
        s.set_linewidth(2.0 if accent else 1.0)
    ax.set_title(title, fontsize=10.5, fontweight="bold",
                 color=ACCENT if accent else INK, pad=4)
    if subtitle:
        ax.text(5, 0.4, subtitle, ha="center", va="bottom",
                fontsize=7.2, color=GREY, wrap=True)


def _auger(ax, x, y, w=0.5, h=2.0, color=ACCENT, angle=0):
    """Draw a small auger glyph (body + tip)."""
    r = Rectangle((x - w / 2, y), w, h, facecolor=FILL, edgecolor=color,
                  linewidth=1.0)
    t = matplotlib.transforms.Affine2D().rotate_deg_around(x, y, angle) + ax.transData
    r.set_transform(t)
    ax.add_patch(r)
    tip = Polygon([[x - w / 2, y], [x + w / 2, y], [x, y - 0.35]],
                  facecolor=color, edgecolor=color)
    tip.set_transform(t)
    ax.add_patch(tip)


# --- individual tiles -------------------------------------------------------

def tile_vertical(ax):
    """Chosen: vertical (paternoster) carousel — augers hang, small footprint."""
    _frame(ax, "Vertical carousel (CHOSEN)",
           "axis horizontal · augers stay vertical · compact footprint",
           accent=True)
    # oblong chain loop (paternoster)
    cx, top, bot = 5, 8.0, 3.0
    rad = 1.6
    th = np.linspace(-90, 90, 40)
    ax.plot(cx + rad * np.cos(np.radians(th)) + 0, top + 0 * th, lw=0)  # noop
    # left/right straight runs
    ax.plot([cx - rad, cx - rad], [bot, top], color=INK, lw=1.5)
    ax.plot([cx + rad, cx + rad], [bot, top], color=INK, lw=1.5)
    # top/bottom sprockets
    for cy in (top, bot):
        ax.add_patch(Circle((cx, cy), rad, fill=False, edgecolor=INK, lw=1.5))
        ax.add_patch(Circle((cx, cy), 0.18, facecolor=INK))
    # hanging augers on the loop
    for cy in (top + rad, top, bot, bot - rad):
        pass
    ys = [9.0, 7.6, 6.2, 4.8, 3.6, 2.2]
    xs = [cx - rad, cx - rad, cx - rad, cx + rad, cx + rad, cx + rad]
    for x, y in zip(xs, ys):
        _auger(ax, x, y - 0.1, h=1.1)
    # dispense station at bottom
    ax.add_patch(Rectangle((cx + rad - 0.45, 1.0), 0.9, 0.55,
                           facecolor="#fde68a", edgecolor=WARN))
    ax.text(cx + rad + 0.7, 1.25, "dispense\n(servo+solenoid\npulls auger down)",
            fontsize=6.0, va="center", color=WARN)
    ax.annotate("", xy=(cx + rad, 1.0), xytext=(cx + rad, 2.0),
                arrowprops=dict(arrowstyle="->", color=WARN, lw=1.4))


def tile_horizontal(ax):
    """Rejected: horizontal turntable — huge diameter for 50 augers + radial pull."""
    _frame(ax, "Horizontal carousel (rejected)",
           "axis vertical · radial pull needs a very large \u00d8")
    cx, cy = 5, 5.6
    ax.add_patch(Circle((cx, cy), 3.4, fill=False, edgecolor=WARN, lw=1.6,
                        linestyle="--"))
    ax.add_patch(Circle((cx, cy), 0.2, facecolor=INK))
    # augers as dots around big rim
    for a in np.linspace(0, 360, 26, endpoint=False):
        x = cx + 3.4 * np.cos(np.radians(a))
        y = cy + 3.4 * np.sin(np.radians(a))
        ax.add_patch(Circle((x, y), 0.16, facecolor=FILL, edgecolor=ACCENT))
    # radial pull arrow at one station
    ax.annotate("", xy=(cx + 4.5, cy), xytext=(cx + 3.2, cy),
                arrowprops=dict(arrowstyle="->", color=WARN, lw=1.6))
    ax.text(cx, cy, "huge \u00d8", ha="center", va="center",
            fontsize=8, color=WARN, fontweight="bold")


def tile_geneva(ax):
    _frame(ax, "Geneva (Maltese) drive",
           "intermittent index + positive geometric lock")
    # driven wheel (slotted cross)
    cx, cy = 4.0, 5.5
    R = 2.4
    ax.add_patch(Circle((cx, cy), R, fill=False, edgecolor=INK, lw=1.5))
    for a in range(0, 360, 60):
        x = cx + R * np.cos(np.radians(a))
        y = cy + R * np.sin(np.radians(a))
        ax.plot([cx, x], [cy, y], color=GREY, lw=1.0)
        ax.add_patch(Circle((x, y), 0.22, facecolor=FILL, edgecolor=INK))
    ax.add_patch(Circle((cx, cy), 0.15, facecolor=INK))
    # driver crank + pin
    dx, dy = 8.3, 5.5
    ax.add_patch(Circle((dx, dy), 1.2, fill=False, edgecolor=ACCENT, lw=1.5))
    ax.add_patch(Circle((dx, dy), 0.13, facecolor=ACCENT))
    px = dx - 1.2
    ax.plot([dx, px], [dy, dy], color=ACCENT, lw=1.4)
    ax.add_patch(Circle((px, dy), 0.18, facecolor=ACCENT, edgecolor=ACCENT))
    ax.annotate("", xy=(dx + 0.2, dy + 1.5), xytext=(dx - 0.7, dy + 1.4),
                arrowprops=dict(arrowstyle="->", color=ACCENT, lw=1.2,
                                connectionstyle="arc3,rad=0.4"))


def tile_barrelcam(ax):
    _frame(ax, "Barrel / roller-gear cam indexer",
           "globoidal cam · backlash-free · built-in dwell")
    # barrel cam (horizontal cylinder w/ helical rib)
    ax.add_patch(Rectangle((1.5, 4.2), 5.0, 2.2, fill=False, edgecolor=INK,
                           lw=1.5))
    ax.add_patch(matplotlib.patches.Ellipse((1.5, 5.3), 0.9, 2.2, fill=False,
                                            edgecolor=INK, lw=1.5))
    ax.add_patch(matplotlib.patches.Ellipse((6.5, 5.3), 0.9, 2.2, fill=False,
                                            edgecolor=INK, lw=1.5))
    xs = np.linspace(1.7, 6.3, 60)
    ax.plot(xs, 5.3 + 0.9 * np.sin((xs - 1.7) * 1.2), color=ACCENT, lw=1.6)
    # output turret w/ rollers
    ax.add_patch(Circle((8.0, 5.3), 1.4, fill=False, edgecolor=INK, lw=1.5))
    for a in range(0, 360, 45):
        x = 8.0 + 1.4 * np.cos(np.radians(a))
        y = 5.3 + 1.4 * np.sin(np.radians(a))
        ax.add_patch(Circle((x, y), 0.16, facecolor=FILL, edgecolor=INK))
    ax.add_patch(Circle((8.0, 5.3), 0.13, facecolor=INK))


def tile_slewing(ax):
    _frame(ax, "Slewing-ring turntable + closed-loop stepper",
           "software-defined index · encoder corrects jams (\u00a75.1 baseline)",
           accent=False)
    cx, cy = 5, 6.2
    ax.add_patch(Circle((cx, cy), 2.4, fill=False, edgecolor=INK, lw=1.6))
    ax.add_patch(Circle((cx, cy), 2.0, fill=False, edgecolor=GREY, lw=1.0))
    # ball bearings ring
    for a in range(0, 360, 24):
        x = cx + 2.2 * np.cos(np.radians(a))
        y = cy + 2.2 * np.sin(np.radians(a))
        ax.add_patch(Circle((x, y), 0.1, facecolor=GREY, edgecolor=GREY))
    ax.add_patch(Circle((cx, cy), 0.15, facecolor=INK))
    # motor below
    ax.add_patch(Rectangle((cx - 0.7, 1.4), 1.4, 1.6, facecolor=FILL,
                           edgecolor=ACCENT, lw=1.4))
    ax.text(cx, 2.2, "CL\nstepper", ha="center", va="center", fontsize=6,
            color=ACCENT)
    ax.plot([cx, cx], [3.0, cy - 2.4], color=ACCENT, lw=1.4)


def tile_ratchet(ax):
    _frame(ax, "Ratchet-and-pawl",
           "single-direction index · cheap positive stop")
    cx, cy = 4.6, 5.4
    R = 2.6
    n = 12
    pts = []
    for i in range(n):
        a0 = np.radians(360 * i / n)
        a1 = np.radians(360 * (i + 0.5) / n)
        pts.append((cx + R * np.cos(a0), cy + R * np.sin(a0)))
        pts.append((cx + (R - 0.6) * np.cos(a1), cy + (R - 0.6) * np.sin(a1)))
    ax.add_patch(Polygon(pts, closed=True, fill=False, edgecolor=INK, lw=1.5))
    ax.add_patch(Circle((cx, cy), 0.15, facecolor=INK))
    # pawl
    ax.add_patch(Polygon([[8.6, 7.2], [7.0, 6.0], [8.0, 5.4], [8.9, 6.6]],
                         facecolor=FILL, edgecolor=ACCENT, lw=1.4))
    ax.annotate("", xy=(7.0, 6.0), xytext=(8.6, 7.2),
                arrowprops=dict(arrowstyle="-", color=ACCENT, lw=0))


def tile_detent(ax):
    _frame(ax, "Detent plunger + index plate",
           "spring plunger drops into an N-hole plate")
    cx, cy = 5, 5.2
    R = 2.6
    ax.add_patch(Circle((cx, cy), R, fill=False, edgecolor=INK, lw=1.5))
    for a in range(0, 360, 30):
        x = cx + R * np.cos(np.radians(a))
        y = cy + R * np.sin(np.radians(a))
        ax.add_patch(Circle((x, y), 0.22, facecolor="white", edgecolor=INK))
    ax.add_patch(Circle((cx, cy), 0.15, facecolor=INK))
    # plunger at top hole
    ax.add_patch(Rectangle((cx - 0.18, cy + R - 0.1), 0.36, 1.6,
                           facecolor=FILL, edgecolor=ACCENT, lw=1.3))
    # spring squiggle
    sx = np.linspace(cy + R + 1.5, cy + R + 2.6, 30)
    ax.plot(cx + 0.18 * np.sin(np.linspace(0, 18, 30)), sx, color=ACCENT, lw=1.1)


def tile_worm(ax):
    _frame(ax, "Self-locking worm reducer",
           "multiplies torque · resists back-drive (fail-safe hold)")
    # worm screw
    ax.add_patch(Rectangle((1.4, 5.6), 4.6, 1.0, facecolor=FILL,
                           edgecolor=INK, lw=1.3))
    for x in np.linspace(1.6, 5.8, 9):
        ax.plot([x, x + 0.35], [5.6, 6.6], color=ACCENT, lw=1.0)
    # worm gear
    ax.add_patch(Circle((6.9, 4.2), 2.0, fill=False, edgecolor=INK, lw=1.5))
    for a in range(0, 360, 18):
        x = 6.9 + 2.0 * np.cos(np.radians(a))
        y = 4.2 + 2.0 * np.sin(np.radians(a))
        ax.plot([6.9 + 1.8 * np.cos(np.radians(a)), x],
                [4.2 + 1.8 * np.sin(np.radians(a)), y], color=INK, lw=0.8)
    ax.add_patch(Circle((6.9, 4.2), 0.15, facecolor=INK))


def tile_shotpin(ax):
    _frame(ax, "Shot-pin station lock",
           "spring pin into a precision hole at the dosing station")
    cx, cy = 4.4, 4.8
    R = 2.6
    ax.add_patch(Wedge((cx, cy), R, 20, 160, width=0.6, facecolor=FILL,
                       edgecolor=INK, lw=1.2))
    ax.add_patch(Circle((cx, cy), R, fill=False, edgecolor=INK, lw=1.4))
    # precision hole at top-right
    hx = cx + R * np.cos(np.radians(60))
    hy = cy + R * np.sin(np.radians(60))
    ax.add_patch(Circle((hx, hy), 0.22, facecolor="white", edgecolor=ACCENT,
                        lw=1.4))
    # pin
    ax.add_patch(Rectangle((hx - 0.13, hy + 0.2), 0.26, 1.8, facecolor=ACCENT,
                           edgecolor=ACCENT))
    ax.annotate("", xy=(hx, hy + 0.2), xytext=(hx, hy + 1.2),
                arrowprops=dict(arrowstyle="->", color=ACCENT, lw=1.4))


def tile_clip(ax):
    _frame(ax, "Spring-clip auger retention",
           "leaf/wire clip holds each auger through the sweep")
    _auger(ax, 5, 3.2, w=1.0, h=4.0, color=ACCENT)
    # two leaf springs
    for sgn in (-1, 1):
        xs = np.linspace(0, 1.4, 30)
        ax.plot(5 + sgn * (0.55 + 0.5 * np.sin(xs * 2)), 4.0 + xs * 1.5,
                color=WARN, lw=1.6)
    ax.text(5, 8.0, "clip", ha="center", fontsize=7, color=WARN)


def tile_atc(ax):
    _frame(ax, "CNC ATC drum magazine",
           "horizontal-axis drum holds many elongated tools (Edison ref)")
    cx, cy = 5, 5.4
    R = 2.8
    ax.add_patch(Circle((cx, cy), R, fill=False, edgecolor=INK, lw=1.5))
    ax.add_patch(Circle((cx, cy), R - 0.5, fill=False, edgecolor=GREY, lw=1.0))
    for a in range(0, 360, 30):
        x = cx + (R - 0.25) * np.cos(np.radians(a))
        y = cy + (R - 0.25) * np.sin(np.radians(a))
        ax.add_patch(RegularPolygon((x, y), numVertices=4, radius=0.28,
                                    orientation=np.radians(a),
                                    facecolor=FILL, edgecolor=INK))
    ax.add_patch(Circle((cx, cy), 0.15, facecolor=INK))


def tile_autosampler(ax):
    _frame(ax, "Lab autosampler vial carousel",
           "Gilson/Agilent/ISCO · home sensor + stepper index")
    cx, cy = 5, 5.4
    for ring, n in ((2.7, 18), (1.7, 12)):
        ax.add_patch(Circle((cx, cy), ring, fill=False, edgecolor=GREY, lw=0.8))
        for a in np.linspace(0, 360, n, endpoint=False):
            x = cx + ring * np.cos(np.radians(a))
            y = cy + ring * np.sin(np.radians(a))
            ax.add_patch(Circle((x, y), 0.2, facecolor=FILL, edgecolor=INK))
    ax.add_patch(Circle((cx, cy), 0.15, facecolor=INK))


def tile_pharmacy(ax):
    _frame(ax, "Pharmacy canister carousel",
           "ScriptPro / Parata / Omnicell · index canister to chute")
    cx, cy = 5, 5.8
    R = 2.7
    ax.add_patch(Circle((cx, cy), R, fill=False, edgecolor=INK, lw=1.5))
    for a in np.linspace(0, 360, 16, endpoint=False):
        x = cx + R * np.cos(np.radians(a))
        y = cy + R * np.sin(np.radians(a))
        ax.add_patch(Rectangle((x - 0.22, y - 0.3), 0.44, 0.6,
                               facecolor=FILL, edgecolor=INK,
                               transform=matplotlib.transforms.Affine2D()
                               .rotate_deg_around(x, y, a + 90) + ax.transData))
    ax.add_patch(Circle((cx, cy), 0.15, facecolor=INK))
    # chute
    ax.add_patch(Polygon([[cx - 0.5, 1.2], [cx + 0.5, 1.2], [cx + 0.2, 0.4],
                          [cx - 0.2, 0.4]], facecolor="#fde68a", edgecolor=WARN))
    ax.text(cx, 0.0, "chute", ha="center", fontsize=6, color=WARN)


def tile_quantos(ax):
    _frame(ax, "Mettler-Toledo Quantos dosing-head carousel",
           "index 1 of N replaceable dosing heads under a balance")
    cx, cy = 5, 6.2
    R = 2.3
    ax.add_patch(Circle((cx, cy), R, fill=False, edgecolor=INK, lw=1.5))
    for a in np.linspace(0, 360, 6, endpoint=False):
        x = cx + R * np.cos(np.radians(a))
        y = cy + R * np.sin(np.radians(a))
        ax.add_patch(Rectangle((x - 0.3, y - 0.3), 0.6, 0.6, facecolor=FILL,
                               edgecolor=INK))
    ax.add_patch(Circle((cx, cy), 0.15, facecolor=INK))
    # balance pan below dosing station
    ax.add_patch(Rectangle((cx - 1.0, 1.4), 2.0, 0.3, facecolor="#e5e7eb",
                           edgecolor=INK))
    ax.plot([cx, cx], [1.7, 2.6], color=INK, lw=1.0)
    ax.text(cx, 1.0, "balance", ha="center", fontsize=6, color=GREY)


def tile_counterweight(ax):
    _frame(ax, "Counterweight / paternoster balance",
           "balance the wheel so the motor fights only inertia + friction")
    cx, cy = 5, 5.4
    R = 2.6
    ax.add_patch(Circle((cx, cy), R, fill=False, edgecolor=INK, lw=1.5))
    ax.add_patch(Circle((cx, cy), 0.15, facecolor=INK))
    # heavy augers top, counterweight bottom
    for a in (60, 90, 120):
        x = cx + R * np.cos(np.radians(a))
        y = cy + R * np.sin(np.radians(a))
        ax.add_patch(Circle((x, y), 0.3, facecolor=FILL, edgecolor=ACCENT))
    ax.add_patch(Rectangle((cx - 0.5, cy - R - 0.2), 1.0, 0.7,
                           facecolor=WARN, edgecolor=WARN))
    ax.text(cx, cy - R - 0.5, "counterweight", ha="center", va="top",
            fontsize=6, color=WARN)
    ax.annotate("", xy=(cx, cy + R + 0.6), xytext=(cx, cy + R - 0.2),
                arrowprops=dict(arrowstyle="->", color=ACCENT, lw=1.2))


def tile_homing(ax):
    _frame(ax, "Home sensor + index control",
           "photo/inductive home flag · step-count to any pocket")
    cx, cy = 4.6, 5.4
    R = 2.5
    ax.add_patch(Circle((cx, cy), R, fill=False, edgecolor=INK, lw=1.5))
    ax.add_patch(Circle((cx, cy), 0.15, facecolor=INK))
    # home flag
    fx = cx + R * np.cos(np.radians(20))
    fy = cy + R * np.sin(np.radians(20))
    ax.add_patch(Rectangle((fx, fy - 0.15), 0.7, 0.3, facecolor=ACCENT,
                           edgecolor=ACCENT))
    # sensor
    ax.add_patch(Rectangle((fx + 1.0, fy - 0.35), 0.5, 0.7, facecolor=FILL,
                           edgecolor=INK))
    ax.text(fx + 1.25, fy + 0.7, "home\nsensor", ha="center", fontsize=6,
            color=GREY)
    # controller box
    ax.add_patch(Rectangle((1.0, 1.2), 2.4, 1.2, facecolor="#e5e7eb",
                           edgecolor=INK))
    ax.text(2.2, 1.8, "Pico\u2192driver", ha="center", va="center",
            fontsize=6.5)


TILES = [
    tile_vertical, tile_horizontal, tile_geneva, tile_barrelcam,
    tile_slewing, tile_ratchet, tile_detent, tile_worm,
    tile_shotpin, tile_clip, tile_atc, tile_autosampler,
    tile_pharmacy, tile_quantos, tile_counterweight, tile_homing,
]


def main():
    nrows, ncols = 4, 4
    fig, axes = plt.subplots(nrows, ncols, figsize=(16, 16))
    for ax, tile in zip(axes.ravel(), TILES):
        tile(ax)
    fig.suptitle(
        "Powder-doser 50-auger carousel \u2014 indexing/holding mechanisms "
        "& reference systems (BOM \u00a75.2)",
        fontsize=15, fontweight="bold", y=0.995)
    fig.text(0.5, 0.005,
             "Original schematic line drawings (operating principle only, "
             "not to scale, not product photographs). "
             "Blue = chosen/baseline, orange = caveat/rejected.",
             ha="center", fontsize=9, color=GREY)
    fig.tight_layout(rect=[0, 0.012, 1, 0.985])
    fig.savefig("carousel-mechanism-panel.png", dpi=130)
    fig.savefig("carousel-mechanism-panel.svg")
    print("wrote carousel-mechanism-panel.png / .svg")


if __name__ == "__main__":
    main()
