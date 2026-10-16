"""2D dimensioned schematic of the bayonet-plug cap (front section + bottom view).

Mirrors the constants from cad_model.py.
"""
from __future__ import annotations

from pathlib import Path
import math

import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Rectangle, Arc, Wedge

OUT = Path(__file__).parent / "renders"
OUT.mkdir(exist_ok=True)

AUGER_OD = 25.0
EXIT_HOLE_D = 3.0
RECV_OD = 32.0
RECV_H = 10.0
RECV_BORE_D = 18.0
GROOVE_W = 4.0
GROOVE_DEPTH = 2.5
GROOVE_Z = 4.0
EAR_RUN = 80.0
EAR_ANGLE = 16.0
PLUG_OD = 17.6
PLUG_H = 8.0
KNOB_OD = 22.0
KNOB_T = 4.0
ORING_OD = 14.0
ORING_CS = 1.5


def annotate(ax, x1, y1, x2, y2, label, side="right", off=2.0):
    ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle="<->", color="0.2", lw=0.8))
    mx, my = (x1 + x2) / 2, (y1 + y2) / 2
    if side == "right":
        mx += off
    elif side == "bottom":
        my -= off
    elif side == "top":
        my += off
    ax.text(mx, my, label, ha="center", va="center", fontsize=8)


fig, (ax_sect, ax_bot) = plt.subplots(1, 2, figsize=(11, 5))

# ---- Section view ----
ax_sect.set_title("Front section — plug installed (locked)")
ax_sect.set_aspect("equal")
ax_sect.set_xlim(-RECV_OD / 2 - 12, RECV_OD / 2 + 12)
ax_sect.set_ylim(-KNOB_T - 2, RECV_H + 8 + 22)

# Receiver walls (left + right slabs)
ax_sect.add_patch(Rectangle((-RECV_OD / 2, 0),
                             (RECV_OD - RECV_BORE_D) / 2, RECV_H,
                             facecolor="#c9beed", edgecolor="0.2"))
ax_sect.add_patch(Rectangle((RECV_BORE_D / 2, 0),
                             (RECV_OD - RECV_BORE_D) / 2, RECV_H,
                             facecolor="#c9beed", edgecolor="0.2"))
# Snap collar
ax_sect.add_patch(Rectangle((-AUGER_OD / 2 - 1.6, RECV_H), 1.6, 8.0,
                             facecolor="#b3a7e8", edgecolor="0.2"))
ax_sect.add_patch(Rectangle((AUGER_OD / 2, RECV_H), 1.6, 8.0,
                             facecolor="#b3a7e8", edgecolor="0.2"))
# Auger stub
ax_sect.add_patch(Rectangle((-AUGER_OD / 2, RECV_H + 8.0), 2.0, 18,
                             facecolor="0.85", edgecolor="0.5"))
ax_sect.add_patch(Rectangle((AUGER_OD / 2 - 2.0, RECV_H + 8.0), 2.0, 18,
                             facecolor="0.85", edgecolor="0.5"))
# Plug body
plug_z0 = GROOVE_Z - GROOVE_W / 2
ax_sect.add_patch(Rectangle((-PLUG_OD / 2, plug_z0),
                             PLUG_OD, PLUG_H,
                             facecolor="#8ed68e", edgecolor="0.2"))
# Knob
ax_sect.add_patch(Rectangle((-KNOB_OD / 2, plug_z0 - KNOB_T),
                             KNOB_OD, KNOB_T,
                             facecolor="#6abf6a", edgecolor="0.2"))
# Ears (cross-section blobs at GROOVE_Z)
ax_sect.add_patch(Rectangle((-PLUG_OD / 2 - GROOVE_DEPTH + 0.4,
                              GROOVE_Z - GROOVE_W / 2 + 0.4),
                             GROOVE_DEPTH - 0.4, GROOVE_W - 0.8,
                             facecolor="#6abf6a", edgecolor="0.2"))
ax_sect.add_patch(Rectangle((PLUG_OD / 2,
                              GROOVE_Z - GROOVE_W / 2 + 0.4),
                             GROOVE_DEPTH - 0.4, GROOVE_W - 0.8,
                             facecolor="#6abf6a", edgecolor="0.2"))
# O-ring on plug face
ax_sect.add_patch(Circle((-ORING_OD / 2, plug_z0 + PLUG_H), ORING_CS / 2,
                          facecolor="#cc4040", edgecolor="0.2"))
ax_sect.add_patch(Circle((ORING_OD / 2, plug_z0 + PLUG_H), ORING_CS / 2,
                          facecolor="#cc4040", edgecolor="0.2"))
ax_sect.text(0, plug_z0 + PLUG_H + 1.5, f"O-ring Ø{ORING_OD}×{ORING_CS}",
             ha="center", fontsize=7, color="#882020")

annotate(ax_sect, -RECV_OD / 2, -1.5, RECV_OD / 2, -1.5,
         f"RECV_OD = {RECV_OD:.0f}", side="bottom", off=0.8)
annotate(ax_sect, RECV_OD / 2 + 4, 0, RECV_OD / 2 + 4, RECV_H,
         f"RECV_H = {RECV_H}", side="right", off=3.0)
annotate(ax_sect, -RECV_BORE_D / 2, RECV_H + 6, RECV_BORE_D / 2, RECV_H + 6,
         f"BORE = {RECV_BORE_D}", side="top", off=1.2)

ax_sect.set_xlabel("X [mm]")
ax_sect.set_ylabel("Z [mm]")
ax_sect.grid(True, ls=":", lw=0.4, alpha=0.5)

# ---- Bottom view (the bayonet J-slots, looking up at the receiver) ----
ax_bot.set_title("Bottom view — bayonet J-slot (one of two, mirrored)")
ax_bot.set_aspect("equal")
lim = RECV_OD / 2 + 4
ax_bot.set_xlim(-lim, lim)
ax_bot.set_ylim(-lim, lim)

ax_bot.add_patch(Circle((0, 0), RECV_OD / 2,
                         facecolor="#e8e1ff", edgecolor="0.2"))
ax_bot.add_patch(Circle((0, 0), RECV_BORE_D / 2,
                         facecolor="white", edgecolor="0.2"))
# Two locking arcs (the circumferential run of the J)
for theta0 in (0.0, 180.0):
    ax_bot.add_patch(Wedge((0, 0), RECV_BORE_D / 2 + GROOVE_DEPTH,
                            theta0, theta0 + EAR_RUN,
                            width=GROOVE_DEPTH,
                            facecolor="0.4", edgecolor="0.2"))
    # Axial entry slot indicator (radial dash)
    a = math.radians(theta0)
    x0 = (RECV_BORE_D / 2) * math.cos(a)
    y0 = (RECV_BORE_D / 2) * math.sin(a)
    x1 = (RECV_BORE_D / 2 + GROOVE_DEPTH) * math.cos(a)
    y1 = (RECV_BORE_D / 2 + GROOVE_DEPTH) * math.sin(a)
    ax_bot.plot([x0, x1], [y0, y1], color="#cc4040", lw=2)

ax_bot.text(0, RECV_OD / 2 + 1.5,
            f"EAR_RUN = {EAR_RUN}°  (quarter-turn lock ≈ 80°)",
            ha="center", fontsize=8)
ax_bot.text(RECV_BORE_D / 2 + GROOVE_DEPTH + 1, 0,
            "axial entry\n(red)", ha="left", fontsize=7, color="#882020")
ax_bot.set_xlabel("X [mm]")
ax_bot.set_ylabel("Y [mm]")
ax_bot.grid(True, ls=":", lw=0.4, alpha=0.5)

fig.suptitle("Bayonet-plug sealing cap — dimensioned schematic (mm)")
fig.tight_layout()
out = OUT / "sealing_cap_bayonet_plug_sketch.png"
fig.savefig(out, dpi=150)
print(f"wrote {out}")
