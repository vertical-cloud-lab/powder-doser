"""v9 parts (Sam, PR #185, 2026-11-17). parts.py is v2's, parts3-7 v3-v7's, all unchanged; v9 is a variation on v7.

Sam's note, and the part each piece became:
1. "remove the draft cage on the scale" -> balance_v9: v7's weighing base, display and pan, with no cage, no doors, no lid.
2. "you can put the scale on a block instead of lowering the whole multidoser" -> block_v9: a granite block on the bench under
   the balance (the lab's isolating paver idea, #146), touching nothing of the doser; the carousel stays at v7's height.
3. "how close can we get the auger while not sacrificing the good aspects of the electronics carriage designs?" -> ec_mods_v9:
   v7's EC (Sam's Oct 13 carriage turned over, the dock on the plate's posts, the tail with the P16's pin and the guide shoes)
   with only what hangs over the beaker taken off: its front 18 mm (a new front wall in front of the NEMA 11), the solenoid
   moved behind the gear onto the tail, and the door finger made a slim arm. The beaker sits on the pan 32 mm under the exit.
4. "close-able plexiglas surrounding the doser ... replace the draft cage ... internal panels ... a bay window" ->
   bay_v9_* (a bay window round the balance with a door for the beaker) and chamber_v9_* (a weighing chamber inside the frame:
   two side baffles, a back baffle with a slot for the P16, and a deck under the bottom run with an opening at the station).
Frames: the EC "as drawn" (Sam's Oct 13 carriage mirrored z -> -z, as parts7); world for the balance, the block and the panels.
"""
from __future__ import annotations

import cadquery as cq

from params import *  # noqa: F401,F403
import parts7 as P7
from parts3 import _box, _cyl

DR4 = DOCK_RISE_V4


# ---------------------------------------------------------------- 1. EC v9: v7's EC without what hangs over the beaker
def finger9_top() -> float:
    """As drawn z of the finger's top face: docked it holds the push strip DOOR_TRAVEL up (v7's f_top)."""
    return -(DOOR_ROD_BOTTOM + DOOR_TRAVEL) - DR4


def ec_mods_v9() -> tuple[cq.Workplane, cq.Workplane, cq.Workplane]:
    """(trim, add, cut) applied to EC v7 as drawn: cut `trim` first (everything in front of EC9_FRONT: Sam's carriage's front
    18 mm with the solenoid's pocket, and v7's finger), then union `add` (a new front wall in front of the NEMA 11, the slim
    finger, the solenoid's cradle under the tail's web), then cut `cut` (the solenoid's pocket through the web)."""
    trim = _box(-20.0, EC9_FRONT, -40.0, 40.0, -10.0, 90.0)
    x0 = EC9_FRONT
    wall = _box(x0, x0 + EC9_WALL, -18.0, 18.0, 18.9, 59.2).edges("|X and >Z").fillet(1.5)
    ft = finger9_top()
    fy = DOOR_ROD_Y
    finger = _box(-3.6, x0 + 0.5, fy - 2.0, fy + 2.0, ft, ft + FINGER9_T).edges("|Y and <X").fillet(0.8)
    gus = _box(x0 - 6.0, x0 + 0.5, fy - 2.0, fy + 2.0, ft, ft + FINGER9_T + 6.0)          # gusset under the finger's root
    gus = gus.cut(cq.Workplane("XZ").polyline([(x0 - 6.0, ft + FINGER9_T), (x0 - 6.0, ft + FINGER9_T + 6.1), (x0 + 0.1, ft + FINGER9_T + 6.1)])
                  .close().extrude(-10.0).translate((0, fy - 5.0, 0)))
    c0, c1, hw, t = SOL9_CRADLE
    z_web = EC7_TAIL_Z[1]
    z_frame = 53.75                                         # the solenoid's frame's underside as drawn (v7: 53.7)
    cradle = _box(c0, c1, -hw, hw, z_web - 0.01, z_frame + t)
    add = wall.union(finger).union(gus).union(cradle)
    cut = _box(SOL9_X - 8.7, SOL9_X + 8.7, -7.3, 7.3, 23.0, z_frame)
    return trim, add, cut


def ec_v9_from_v7(ec7: cq.Workplane) -> cq.Workplane:
    trim, add, cut = ec_mods_v9()
    return ec7.cut(trim).union(add).cut(cut)


# ---------------------------------------------------------------- 2. the balance without its cage, and the block
def balance_v9() -> dict[str, cq.Workplane]:
    """v7's balance model without the draft cage: the weighing base (with the ring round the pan), the display and the pan.
    Frame as parts7.balance_v7: origin under the pan's centre at the feet, x from the display (front, -x) back, z up."""
    b = P7.balance_v7()
    return {"bal9_base": b["bal7_base"], "bal9_display": b["bal7_display"], "bal9_pan": b["bal7_pan"]}


def block_v9(h: float) -> cq.Workplane:
    """The block under the balance: granite (or a stack of pavers), h tall, its top at z = 0 under the balance's feet. Same frame
    as balance_v9 (origin under the pan's centre)."""
    x0, x1 = BLOCK9_X
    hy = BLOCK9[1] / 2
    return _box(x0, x1, -hy, hy, -h, 0.0).edges("|Z").fillet(3.0).edges(">Z").chamfer(1.0)


# ---------------------------------------------------------------- 3. the bay window and the weighing chamber (world)
def _panel_x(x0: float, y0: float, y1: float, z0: float, z1: float, cut=None) -> cq.Workplane:
    """A 3 mm acrylic sheet in a y-z plane, x0..x0+t (world)."""
    p = _box(x0, x0 + ACRYLIC_T, y0, y1, z0, z1)
    if cut:
        ya, za, yb, zb = cut
        p = p.cut(_box(x0 - 1, x0 + ACRYLIC_T + 1, ya, yb, za, zb).edges("|X").fillet(3.0))
    return p


def _panel_y(y0: float, x0: float, x1: float, z0: float, z1: float) -> cq.Workplane:
    """A 3 mm acrylic sheet in an x-z plane, y0..y0+t (world)."""
    return _box(x0, x1, y0, y0 + ACRYLIC_T, z0, z1)


def bay_v9(xf_out: float, sy: float) -> dict[str, cq.Workplane]:
    """The bay window, world: a clear acrylic box BAY9_DEPTH proud of the front panel's outer face (xf_out), BAY9_HW either side
    of the station (sy), from the bench to BAY9_TOP: a front with a door opening, two sides and a top. Its back is the front
    panel's opening, so the bay and the weighing chamber inside the frame are one space."""
    t = ACRYLIC_T
    xb = xf_out - BAY9_DEPTH                                 # the bay front's outer face
    dw, dh = BAY9_DOOR
    z1 = BAY9_TOP
    dz1 = z1 - 6.0
    out = {"bay9_front": _panel_x(xb, sy - BAY9_HW, sy + BAY9_HW, 0.0, z1 - t, cut=(sy - dw / 2, dz1 - dh, sy + dw / 2, dz1)),
           "bay9_top": _box(xb, xf_out, sy - BAY9_HW, sy + BAY9_HW, z1 - t, z1)}
    for s in (-1, 1):
        y0 = sy + s * BAY9_HW - (t if s > 0 else 0.0)
        out[f"bay9_side_{'p' if s > 0 else 'm'}"] = _panel_y(y0, xb + t, xf_out, 0.0, z1 - t)
    return out


def bay9_door_opening(xf_out: float, sy: float) -> tuple:
    """(x of the bay front's outer face, y0, z0, y1, z1) of the door's opening."""
    dw, dh = BAY9_DOOR
    dz1 = BAY9_TOP - 6.0
    return (xf_out - BAY9_DEPTH, sy - dw / 2, dz1 - dh, sy + dw / 2, dz1)


def chamber_v9(xf_in: float, sy: float, guide_bar: tuple) -> dict[str, cq.Workplane]:
    """The weighing chamber inside the frame, world: two side baffles (in line with the bay's sides) from the front panel's inner
    face (xf_in) back to the back baffle, the back baffle (with a slot for the P16 from P16SLOT9[1] up), and the deck over them
    under the bottom run (top at BAY9_TOP, 4.6 mm under the lowest point of any passing module) with an opening at the station
    for the EC, the stream and the P16, open to the deck's back edge (the EC's tail swings through there as it tilts).
    guide_bar: (x0, x1, z0, z1) of the guide cross bar, which runs through both side baffles (notched round it)."""
    t = ACRYLIC_T
    z1 = BAY9_TOP
    xb = DECK9_X1                                            # the back baffle's front face
    gx0, gx1, gz0, gz1 = guide_bar
    n = GUIDEBAR9_NOTCH
    out = {}
    for s in (-1, 1):
        y0 = sy + s * BAY9_HW - (t if s > 0 else 0.0)
        p = _panel_y(y0, xf_in, xb, 0.0, z1 - t)
        p = p.cut(_box(gx0 - n, gx1 + n, y0 - 1, y0 + t + 1, gz0 - n, gz1 + n))
        out[f"baffle9_side_{'p' if s > 0 else 'm'}"] = p
    hw, zs = P16SLOT9
    out["baffle9_back"] = _panel_x(xb, sy - BAY9_HW, sy + BAY9_HW, 0.0, z1 - t, cut=(sy - hw, zs, sy + hw, z1 + 1.0))
    cx0, cx1, cy0, cy1 = DECK9_CUT
    deck = _box(xf_in, xb + t, sy - BAY9_HW, sy + BAY9_HW, z1 - t, z1)
    deck = deck.cut(_box(cx0, xb + t + 1.0, sy + cy0, sy + cy1, z1 - t - 1, z1 + 1).edges("|Z and <X").fillet(4.0))
    out["deck9"] = deck
    return out
