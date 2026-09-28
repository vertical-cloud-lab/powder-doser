"""2D dimensioned schematic of the spring-hatch cap (front + side elevations).

Mirrors the constants from cad_model.py exactly.
"""
from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Rectangle

OUT = Path(__file__).parent / "renders"
OUT.mkdir(exist_ok=True)

AUGER_OD = 25.0
EXIT_HOLE_D = 3.0
BASE_OD = 32.0
BASE_T = 5.0
COLLAR_H = 8.0
FLAP_OD = 22.0
FLAP_T = 2.5
HINGE_FLEXURE_T = 0.6
CAM_TAB_W = 5.0
CAM_TAB_H = 4.0
CAM_TAB_L = 6.0


def annotate(ax, x1, y1, x2, y2, label, side="bottom", off=2.0):
    ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle="<->", color="0.2", lw=0.8))
    mx, my = (x1 + x2) / 2, (y1 + y2) / 2
    if side == "bottom":
        my -= off
    elif side == "top":
        my += off
    elif side == "right":
        mx += off
    ax.text(mx, my, label, ha="center", va="center", fontsize=8)


fig, (ax_closed, ax_open) = plt.subplots(1, 2, figsize=(11, 5))

for ax, title, flap_angle in [(ax_closed, "Closed", 0.0),
                               (ax_open, "Open (cam pin pushes tab)", 70.0)]:
    ax.set_title(title)
    ax.set_aspect("equal")
    ax.set_xlim(-BASE_OD / 2 - 14, BASE_OD / 2 + 10)
    ax.set_ylim(-CAM_TAB_H - 2, BASE_T + COLLAR_H + 22)

    # Cap base
    ax.add_patch(Rectangle((-BASE_OD / 2, 0), BASE_OD, BASE_T,
                            facecolor="#c9beed", edgecolor="0.2"))
    # Snap collar (left wall + right wall)
    ax.add_patch(Rectangle((-AUGER_OD / 2 - 1.6, BASE_T),
                            1.6, COLLAR_H,
                            facecolor="#b3a7e8", edgecolor="0.2"))
    ax.add_patch(Rectangle((AUGER_OD / 2, BASE_T), 1.6, COLLAR_H,
                            facecolor="#b3a7e8", edgecolor="0.2"))
    # Auger stub
    ax.add_patch(Rectangle((-AUGER_OD / 2, BASE_T + COLLAR_H),
                            2.0, 18, facecolor="0.85", edgecolor="0.5"))
    ax.add_patch(Rectangle((AUGER_OD / 2 - 2.0, BASE_T + COLLAR_H),
                            2.0, 18, facecolor="0.85", edgecolor="0.5"))
    # Exit-hole centreline
    ax.plot([-EXIT_HOLE_D / 2, -EXIT_HOLE_D / 2],
            [BASE_T, BASE_T + COLLAR_H + 18], "--", color="0.4", lw=0.8)
    ax.plot([EXIT_HOLE_D / 2, EXIT_HOLE_D / 2],
            [BASE_T, BASE_T + COLLAR_H + 18], "--", color="0.4", lw=0.8)
    # Flap (closed = horizontal under base, open = pivoted out)
    import numpy as np
    a = np.radians(flap_angle)
    pivot_x = FLAP_OD / 2 + 1.0
    pivot_y = BASE_T - FLAP_T - 0.2
    # flap body as a rectangle from pivot extending in -X
    L = FLAP_OD
    corners = np.array([[0, 0], [-L, 0], [-L, FLAP_T], [0, FLAP_T]])
    R = np.array([[np.cos(a), -np.sin(a)], [np.sin(a), np.cos(a)]])
    rotated = corners @ R.T + np.array([pivot_x, pivot_y])
    ax.add_patch(plt.Polygon(rotated, closed=True,
                              facecolor="#8ed68e", edgecolor="0.2"))
    # Cam tab (small rectangle at the far end of the flap, points down)
    tab_corners = np.array([[-L, 0], [-L - CAM_TAB_L, 0],
                             [-L - CAM_TAB_L, -CAM_TAB_H], [-L, -CAM_TAB_H]])
    tab_rotated = tab_corners @ R.T + np.array([pivot_x, pivot_y])
    ax.add_patch(plt.Polygon(tab_rotated, closed=True,
                              facecolor="#6abf6a", edgecolor="0.2"))
    # Cam pin marker (mechanism-side) — only show in 'open'
    if flap_angle > 0:
        ax.plot([-BASE_OD / 2 - 6], [-CAM_TAB_H / 2 - 1], marker=">",
                markersize=12, color="#cc4040")
        ax.text(-BASE_OD / 2 - 7, -CAM_TAB_H / 2 - 4,
                "cam pin\n(stationary, on dispense head)",
                ha="left", va="top", fontsize=7, color="#882020")

    annotate(ax, -BASE_OD / 2, -CAM_TAB_H - 1.5, BASE_OD / 2,
             -CAM_TAB_H - 1.5, f"BASE_OD = {BASE_OD:.0f}",
             side="bottom", off=0.8)
    annotate(ax, BASE_OD / 2 + 4, 0, BASE_OD / 2 + 4, BASE_T,
             f"BASE_T = {BASE_T}", side="right", off=2.5)
    annotate(ax, BASE_OD / 2 + 4, BASE_T, BASE_OD / 2 + 4, BASE_T + COLLAR_H,
             f"COLLAR_H = {COLLAR_H}", side="right", off=2.5)

    ax.set_xlabel("X [mm]")
    ax.set_ylabel("Z [mm]")
    ax.grid(True, ls=":", lw=0.4, alpha=0.5)

fig.suptitle("Spring-hatch sealing cap — dimensioned schematic (mm)")
fig.tight_layout()
out = OUT / "sealing_cap_spring_hatch_sketch.png"
fig.savefig(out, dpi=150)
print(f"wrote {out}")
