"""Populated POWDER_DOSER_V2 PCB standing on its printed holder, with the
holder's three #10 wood screws.  This is the drop-in for the full assemblies.

Frame: z = 0 is the wooden board's top surface (the holder stands on it),
x = 0 the holder's centre line, y = 0 the holder's front face; everything
lies at y >= 0 (footprint x = -60..60, y = 0..70; height 88.2 mm + the
regulator's 3.8 mm overhang).  The PCB faces -Y (towards the doser): its
component side is at y = 24.4 and the tallest parts reach y = 5.8.

PCB placement inside this frame: rotate the board frame +90 deg about X
(board +Y -> up, board +Z -> -Y), then translate by (-50.8, 26.0, 12.0).
"""
from __future__ import annotations

from pathlib import Path

from cadgen import build123d as bd
from cadgen import read_step, step

import pcb_parts as P
from pcb_assembly import pcb_assembly
from pcb_layout import BOARD_W, STANDOFF_L
from pcb_mount import (BASE_T, PCB_Z0, UPRIGHT_T, UPRIGHT_Y, WOOD_SCREWS,
                       pcb_mount, standoff_points)

_HERE = Path(__file__).resolve().parent
_PARTS = _HERE.parents[1] / "STEP" / "imported" / "step-parts"


def build() -> bd.Shape:
    kids = []
    holder = pcb_mount()
    holder.label = "pcb_holder"
    kids.append(holder)

    # board frame -> holder frame: Rx(+90): (x, y, z) -> (x, -z, y)
    board_loc = bd.Location((-BOARD_W / 2, UPRIGHT_Y - STANDOFF_L, PCB_Z0), (90, 0, 0))
    pcb = board_loc * pcb_assembly()
    pcb.label = "pcb_assembly"
    kids.append(pcb)

    # M3 x 8 button heads from behind the upright into the F-F standoffs
    screw = read_step(_PARTS / "button_head_screw_m3_l0008_simple.step")
    for name, (x, z) in standoff_points().items():
        s = bd.Location((x, UPRIGHT_Y + UPRIGHT_T, z), (-90, 0, 0)) * screw   # shank -> -Y
        s.label = f"screw_m3x8_button_rear:{name}"
        kids.append(s)

    # #10 x 1 in flat-head wood screws, heads flush in the countersinks
    wood = P.wood_screw_10()
    for i, (x, y) in enumerate(WOOD_SCREWS):
        s = bd.Location((x, y, BASE_T)) * wood
        s.label = f"wood_screw_10x1in:{i + 1}"
        kids.append(s)

    return bd.Compound(children=kids, label="pcb_holder_assembly")


@step(out="../../STEP/electronics/pcb_holder_assembly.step")
def pcb_holder_assembly():
    return build()


if __name__ == "__main__":
    pcb_holder_assembly()
