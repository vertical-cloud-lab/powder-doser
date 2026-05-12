"""
2D freeform schematic of the §2.2 "inward-pointing single collection point"
dispense geometry.

Two views are drawn (top and side), with realistic dimensions taken from
design/brainstorming.md §2.2:

  * N ~= 12 dispense tubes, ~30 mm OD
  * arranged on a ~150 mm pitch-circle radius
  * aimed inward and downward at a single shared collection cup
  * cup ~80 mm OD (~40 mm radius), seated on a load cell directly below
  * tube outlets sit ~80 mm above the cup rim, tilted ~30 deg from vertical

Output: sketch_top_side.png (saved next to this script).
"""

from pathlib import Path

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np

# --- design constants (mm) -------------------------------------------------
N_CHANNELS = 12
TUBE_OD = 30.0
TUBE_ID = 12.0           # auger bore
PITCH_RADIUS = 75.0      # circle that the tube *outlets* lie on (top view); 150 mm dia per §2.2
CUP_OD = 80.0
CUP_ID = 70.0
CUP_HEIGHT = 35.0
LOAD_CELL_W = 110.0
LOAD_CELL_H = 18.0
TUBE_TILT_DEG = 30.0     # angle from vertical
TUBE_LEN = 110.0         # visible auger-tube length
RESERVOIR_OD = 55.0
RESERVOIR_H = 80.0
OUTLET_HEIGHT_ABOVE_CUP = 80.0  # vertical distance, outlet -> cup rim


# --- figure ---------------------------------------------------------------
fig, (ax_top, ax_side) = plt.subplots(
    1, 2, figsize=(13, 6.5), gridspec_kw={"width_ratios": [1, 1.05]}
)


# --- top view -------------------------------------------------------------
ax_top.set_aspect("equal")
ax_top.set_title(
    f"Top view — {N_CHANNELS} dispense tubes on a "
    f"{2 * PITCH_RADIUS:.0f} mm-dia pitch circle, aimed inward",
    fontsize=10,
)

# pitch circle (construction)
pc = plt.Circle((0, 0), PITCH_RADIUS, fill=False, ls="--", lw=0.8, color="gray")
ax_top.add_patch(pc)
ax_top.annotate(
    f"pitch circle  Ø{2 * PITCH_RADIUS:.0f} mm",
    xy=(PITCH_RADIUS * np.cos(np.radians(35)),
        PITCH_RADIUS * np.sin(np.radians(35))),
    xytext=(180, 130), fontsize=8, color="gray",
    arrowprops=dict(arrowstyle="-", color="gray", lw=0.6),
)

# collection cup
cup = plt.Circle((0, 0), CUP_OD / 2, fc="#fff2cc", ec="black", lw=1.2)
ax_top.add_patch(cup)
cup_id = plt.Circle((0, 0), CUP_ID / 2, fc="white", ec="black", lw=0.8)
ax_top.add_patch(cup_id)
ax_top.annotate(
    f"shared collection cup\nØ{CUP_OD:.0f} mm",
    xy=(0, -CUP_OD / 2), xytext=(0, -55),
    fontsize=8, ha="center",
    arrowprops=dict(arrowstyle="->", color="black", lw=0.6),
)

# dispense tubes (circles at outlet positions, with reservoir circle behind)
for i in range(N_CHANNELS):
    theta = 2 * np.pi * i / N_CHANNELS + np.pi / N_CHANNELS
    x_out = PITCH_RADIUS * np.cos(theta)
    y_out = PITCH_RADIUS * np.sin(theta)
    # auger tube (outlet projection)
    tube = plt.Circle((x_out, y_out), TUBE_OD / 2,
                      fc="#d9e7ff", ec="#1f4e8a", lw=1.0)
    ax_top.add_patch(tube)
    bore = plt.Circle((x_out, y_out), TUBE_ID / 2,
                      fc="white", ec="#1f4e8a", lw=0.6)
    ax_top.add_patch(bore)
    # reservoir centroid sits radially outboard of the outlet
    r_res = PITCH_RADIUS + TUBE_OD / 2 + RESERVOIR_OD / 2 + 5
    x_res = r_res * np.cos(theta)
    y_res = r_res * np.sin(theta)
    res = plt.Circle((x_res, y_res), RESERVOIR_OD / 2,
                     fc="#eaeaea", ec="#555555", lw=0.8, alpha=0.85)
    ax_top.add_patch(res)
    # arrow showing dispense direction (toward cup)
    ax_top.annotate(
        "", xy=(0.4 * x_out, 0.4 * y_out), xytext=(0.95 * x_out, 0.95 * y_out),
        arrowprops=dict(arrowstyle="->", color="#1f4e8a", lw=0.8),
    )

# label one tube + one reservoir
theta0 = 2 * np.pi * 0 / N_CHANNELS + np.pi / N_CHANNELS
x0 = PITCH_RADIUS * np.cos(theta0)
y0 = PITCH_RADIUS * np.sin(theta0)
ax_top.annotate(
    f"auger tube\nØ{TUBE_OD:.0f} mm OD\nØ{TUBE_ID:.0f} mm bore",
    xy=(x0, y0), xytext=(x0 + 70, y0 + 35), fontsize=8,
    arrowprops=dict(arrowstyle="->", color="black", lw=0.6),
)
r_res0 = PITCH_RADIUS + TUBE_OD / 2 + RESERVOIR_OD / 2 + 5
x_res0 = r_res0 * np.cos(theta0)
y_res0 = r_res0 * np.sin(theta0)
ax_top.annotate(
    f"hopper / cartridge\nØ{RESERVOIR_OD:.0f} mm",
    xy=(x_res0, y_res0), xytext=(x_res0 + 30, y_res0 - 30), fontsize=8,
    arrowprops=dict(arrowstyle="->", color="black", lw=0.6),
)

lim = PITCH_RADIUS + RESERVOIR_OD + 70
ax_top.set_xlim(-lim, lim)
ax_top.set_ylim(-lim, lim)
ax_top.set_xlabel("x (mm)")
ax_top.set_ylabel("y (mm)")
ax_top.grid(alpha=0.25)


# --- side view ------------------------------------------------------------
ax_side.set_aspect("equal")
ax_side.set_title(
    f"Side view — tubes tilted {TUBE_TILT_DEG:.0f}° inward, "
    f"outlets ~{OUTLET_HEIGHT_ABOVE_CUP:.0f} mm above cup",
    fontsize=10,
)

# load cell at the bottom
y_lc_bot = 0
y_lc_top = LOAD_CELL_H
lc = mpatches.Rectangle(
    (-LOAD_CELL_W / 2, y_lc_bot), LOAD_CELL_W, LOAD_CELL_H,
    fc="#e0e0e0", ec="black", lw=1.0,
)
ax_side.add_patch(lc)
ax_side.text(0, y_lc_bot + LOAD_CELL_H / 2, "load cell",
             ha="center", va="center", fontsize=8)

# cup sitting on load cell
y_cup_bot = y_lc_top
y_cup_top = y_cup_bot + CUP_HEIGHT
cup_outer = mpatches.Rectangle(
    (-CUP_OD / 2, y_cup_bot), CUP_OD, CUP_HEIGHT,
    fc="#fff2cc", ec="black", lw=1.0,
)
ax_side.add_patch(cup_outer)
# show the inner cavity of the cup as a notched rectangle
wall = (CUP_OD - CUP_ID) / 2
cup_inner = mpatches.Rectangle(
    (-CUP_ID / 2, y_cup_bot + 4), CUP_ID, CUP_HEIGHT - 4,
    fc="white", ec="black", lw=0.6,
)
ax_side.add_patch(cup_inner)
ax_side.annotate(
    f"collection cup\nØ{CUP_OD:.0f} OD / Ø{CUP_ID:.0f} ID × {CUP_HEIGHT:.0f} mm",
    xy=(-CUP_OD / 2, y_cup_top), xytext=(-180, y_cup_top + 30),
    fontsize=8, arrowprops=dict(arrowstyle="->", color="black", lw=0.6),
)

# outlet plane height above cup rim
y_outlet = y_cup_top + OUTLET_HEIGHT_ABOVE_CUP

# draw two representative dispense tubes (left and right), tilted inward
def draw_tube(ax, sign):
    theta = np.radians(TUBE_TILT_DEG) * sign  # +x side tilts left (toward 0)
    # outlet point: on the pitch circle (in side projection that's just |x|=PR)
    x_out = sign * PITCH_RADIUS
    y_out = y_outlet
    # tube axis points from outlet up-and-out (away from cup)
    dx = -sign * np.sin(np.radians(TUBE_TILT_DEG))
    dy = np.cos(np.radians(TUBE_TILT_DEG))
    # tube body as a polygon (rectangle along the tube axis)
    half = TUBE_OD / 2
    perp_x, perp_y = -dy, dx  # perpendicular to axis
    # NOTE: sign of perp doesn't matter for symmetric thickness
    p1 = (x_out + perp_x * half, y_out + perp_y * half)
    p2 = (x_out - perp_x * half, y_out - perp_y * half)
    p3 = (p2[0] + dx * TUBE_LEN, p2[1] + dy * TUBE_LEN)
    p4 = (p1[0] + dx * TUBE_LEN, p1[1] + dy * TUBE_LEN)
    poly = mpatches.Polygon([p1, p2, p3, p4], closed=True,
                            fc="#d9e7ff", ec="#1f4e8a", lw=1.0)
    ax.add_patch(poly)
    # bore as a thinner polygon
    half_b = TUBE_ID / 2
    b1 = (x_out + perp_x * half_b, y_out + perp_y * half_b)
    b2 = (x_out - perp_x * half_b, y_out - perp_y * half_b)
    b3 = (b2[0] + dx * TUBE_LEN, b2[1] + dy * TUBE_LEN)
    b4 = (b1[0] + dx * TUBE_LEN, b1[1] + dy * TUBE_LEN)
    bore = mpatches.Polygon([b1, b2, b3, b4], closed=True,
                            fc="white", ec="#1f4e8a", lw=0.4)
    ax.add_patch(bore)
    # reservoir cylinder at the top of the tube
    cx = x_out + dx * (TUBE_LEN + RESERVOIR_H / 2)
    cy = y_out + dy * (TUBE_LEN + RESERVOIR_H / 2)
    res_w = RESERVOIR_OD
    res_h = RESERVOIR_H
    # axis-aligned ellipse-topped rectangle for clarity (not tilted, OK for schematic)
    res = mpatches.FancyBboxPatch(
        (cx - res_w / 2, cy - res_h / 2),
        res_w, res_h, boxstyle="round,pad=2,rounding_size=8",
        fc="#eaeaea", ec="#555555", lw=0.8,
    )
    ax.add_patch(res)
    # powder stream (dashed) from outlet down into cup
    stream_x = [x_out, 0]
    stream_y = [y_out, y_cup_top - 2]
    ax.plot(stream_x, stream_y, ls=(0, (3, 3)), color="#a06000", lw=0.9)


draw_tube(ax_side, +1)
draw_tube(ax_side, -1)

# show several "background" tubes faded to imply N=12 around the ring
for i in range(N_CHANNELS):
    theta = 2 * np.pi * i / N_CHANNELS + np.pi / N_CHANNELS
    # project the outlet x onto the side view
    x_proj = PITCH_RADIUS * np.cos(theta)
    if abs(abs(x_proj) - PITCH_RADIUS) < 1e-3:
        continue  # already drawn
    if abs(x_proj) < 5:
        continue  # would overlap cup centerline
    sign = 1 if x_proj > 0 else -1
    dx = -sign * np.sin(np.radians(TUBE_TILT_DEG))
    dy = np.cos(np.radians(TUBE_TILT_DEG))
    x_out = x_proj
    y_out = y_outlet
    # short faded line up-and-out
    ax_side.plot(
        [x_out, x_out + dx * (TUBE_LEN * 0.85)],
        [y_out, y_out + dy * (TUBE_LEN * 0.85)],
        color="#1f4e8a", alpha=0.18, lw=4,
    )

# annotate outlet height above cup
ax_side.annotate(
    "", xy=(0.62 * PITCH_RADIUS, y_cup_top),
    xytext=(0.62 * PITCH_RADIUS, y_outlet),
    arrowprops=dict(arrowstyle="<->", color="black", lw=0.6),
)
ax_side.text(
    0.62 * PITCH_RADIUS + 6, (y_cup_top + y_outlet) / 2,
    f"{OUTLET_HEIGHT_ABOVE_CUP:.0f} mm\noutlet → cup rim",
    fontsize=8, va="center",
)

# annotate tilt angle on the right tube
ax_side.annotate(
    f"{TUBE_TILT_DEG:.0f}° tilt\n(from vertical)",
    xy=(PITCH_RADIUS, y_outlet + 35),
    xytext=(PITCH_RADIUS + 25, y_outlet + 90),
    fontsize=8, arrowprops=dict(arrowstyle="->", color="black", lw=0.6),
)

# floor / structural reference line
ax_side.axhline(y_lc_bot, color="black", lw=0.4, alpha=0.4)
ax_side.text(-LOAD_CELL_W / 2 - 5, y_lc_bot - 8, "frame / base", fontsize=7)

ax_side.set_xlim(-260, 260)
ax_side.set_ylim(-25, y_outlet + TUBE_LEN + RESERVOIR_H + 25)
ax_side.set_xlabel("x (mm)")
ax_side.set_ylabel("z (mm)")
ax_side.grid(alpha=0.25)


fig.suptitle(
    "Powder doser §2.2 — N parallel channels aimed inward at a single "
    "shared collection cup",
    fontsize=12, y=0.995,
)
fig.tight_layout(rect=(0, 0, 1, 0.97))

out = Path(__file__).with_name("sketch_top_side.png")
fig.savefig(out, dpi=150, bbox_inches="tight")
print(f"wrote {out}")
