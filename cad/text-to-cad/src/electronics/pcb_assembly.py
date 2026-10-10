"""POWDER_DOSER_V2 PCB, populated.

Frame = the bare board's frame (see pcb.py / pcb_layout.py): origin at the
lower-left outline corner, X along the 101.6 mm edge, Z up, board top at
z = 1.6.  Standoffs hang below the board (z -10..0); screw heads sit on top.

Every placement below is derived from FlyingProbeTesting.json (component
centroids, pin coordinates and nets) and registered pin-for-pin against the
module hole patterns; the Gerber coordinates are kept in the source so they
can be checked against the zip.  Module seating: male 0.1" header plastic
(2.54 mm) under every module; the Pico W sits in 8.5 mm female sockets on
its own male headers; the Waveshare RS-232 module carries its own female
headers and plugs onto male headers.
"""
from __future__ import annotations

from pathlib import Path

from cadgen import build123d as bd
from cadgen import glb, read_step, step

import pcb_parts as P
from pcb import pcb
from pcb_layout import (BOARD_T, GERBER_TO_BOARD, MODULE_Z, MOUNT_HOLES,
                        STACK_Z, STANDOFF_L)

_HERE = Path(__file__).resolve().parent
_PARTS = _HERE.parents[1] / "STEP" / "imported" / "step-parts"


def gb(x: float, y: float, z: float = 0.0) -> tuple[float, float, float]:
    """Gerber (EasyEDA) coordinates -> board frame."""
    return (x + GERBER_TO_BOARD[0], y + GERBER_TO_BOARD[1], z)


def place(shape, label: str, xyz, rot_z: float = 0.0, rot_y: float = 0.0):
    s = bd.Location(xyz, (0, rot_y, rot_z)) * shape
    s.label = label
    return s


def build_assembly() -> bd.Shape:
    kids = [pcb()]

    # ---- modules (gerber coordinate of the module-frame origin, rotation) --
    kids.append(place(P.pico_w(), "U2_pico_w", gb(-1.61, -25.5, STACK_Z)))
    kids.append(place(P.waveshare_pico_2ch_rs232(), "U6_pico_2ch_rs232",
                      gb(-27.011, -26.0, STACK_Z)))
    kids.append(place(P.tic_t500(), "U5_tic_t500", gb(-39.37, -45.72, MODULE_Z), 90))
    kids.append(place(P.drv8871(), "U4_drv8871_solenoid", gb(-44.45, -6.985, MODULE_Z), 90))
    kids.append(place(P.drv2605l_stemma(), "U3_drv2605l_haptic",
                      gb(-9.525, -29.845, MODULE_Z), 180))
    kids.append(place(P.d24v22f5(), "U1_d24v22f5_5v", gb(-61.595, 14.605, MODULE_Z)))
    kids.append(place(P.shunt_regulator_9w(), "SR1_shunt_33v",
                      gb(22.61, -27.305, MODULE_Z), 180))

    # ---- 0.1" headers / sockets (pin-1 gerber coordinate, rotation) --------
    h20, s20 = P.pin_header(20), P.pin_socket(20)
    for lab, x in (("pico_l", 0.0), ("pico_r", 17.78)):
        kids.append(place(s20, f"J_{lab}_socket", gb(x, 24.13, BOARD_T)))
        kids.append(place(h20, f"J_{lab}_pins", gb(x, 24.13, STACK_Z), rot_y=180))
    for lab, x in (("waveshareleft", -25.401), ("waveshareright", -7.621)):
        kids.append(place(h20, f"J_{lab}_pins", gb(x, 24.13, BOARD_T)))
    headers = [  # label, n, pin-1 gerber xy, rotation (0: along -Y, 90: along +X)
        ("J_ticpower", 2, (-57.15, -8.89), 90),
        ("J_stepperpins", 4, (-49.53, -8.89), 90),
        ("J_tic_serial", 3, (-54.61, -44.45), 90),
        ("J_solenoiddriver", 4, (-46.99, 6.985), 0),
        ("J_hapticdriver", 5, (-27.305, -32.385), 90),
        ("J_5v_reg", 5, (-60.325, 15.875), 90),
        ("J_shunt", 4, (17.78, -33.655), 0),
        ("J_stepperpins_OUT", 4, (-74.295, 1.905), 0),
        ("J_servo_l", 3, (-74.295, -9.525), 0),
        ("J_servo_r", 3, (-74.295, -19.05), 0),
    ]
    cache: dict[int, bd.Shape] = {}
    for lab, n, (x, y), rot in headers:
        cache.setdefault(n, P.pin_header(n))
        kids.append(place(cache[n], lab, gb(x, y, BOARD_T), rot))

    # ---- step.parts catalogue parts -----------------------------------------
    cap = read_step(_PARTS / "cp_radial_d10_0mm_p5_00mm.step")
    for lab, y in (("C_12v", 19.05), ("C_tic", 6.985), ("C_5v", -5.715), ("C_3v3", -17.145)):
        kids.append(place(cap, lab, gb(-35.52, y, BOARD_T)))   # pin 1 (+) at x = -35.52
    jack = read_step(_PARTS / "barreljack_horizontal.step")
    kids.append(place(jack, "J1_12v_barrel_jack", gb(-69.39, 24.55, BOARD_T)))

    standoff = read_step(_PARTS / "standoff_hex_female_female_m3_l0010_simple.step")
    screw = read_step(_PARTS / "button_head_screw_m3_l0006_simple.step")
    for name, (x, y) in MOUNT_HOLES.items():
        kids.append(place(standoff, f"standoff_m3x10:{name}", (x, y, -STANDOFF_L)))
        kids.append(place(screw, f"screw_m3x6_button:{name}", (x, y, BOARD_T)))

    return bd.Compound(children=kids, label="powder_doser_v2_pcb_assembly")


@glb(out="../../GLB/electronics/pcb_assembly.glb")
@step(out="../../STEP/electronics/pcb_assembly.step")
def pcb_assembly():
    return build_assembly()


if __name__ == "__main__":
    pcb_assembly()
