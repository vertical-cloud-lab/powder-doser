"""POWDER_DOSER_V2 board constants (plain module, literals only).

Board frame (used by pcb.py / pcb_assembly.py): origin at the lower-left
outline corner, X along the 101.6 mm edge, Y along the 76.2 mm edge, Z up,
FR-4 from z = 0 to z = 1.6 (top copper side up).

Gerber coordinates (EasyEDA Pro export, mm) map to the board frame by
adding GERBER_TO_BOARD.  Every number below was read from
hardware/PCBs/POWDER_DOSER_V2.zip (GKO outline, DRL drills,
FlyingProbeTesting.json centroids/pins); see README.md for the evidence.
"""

BOARD_W = 101.6          # mm, 4.000 in (GKO: x -78.105 .. 23.495)
BOARD_H = 76.2           # mm, 3.000 in (GKO: y -47.625 .. 28.575)
BOARD_T = 1.6            # mm FR-4 (standard; not encoded in the Gerbers)
GERBER_TO_BOARD = (78.105, 47.625)

# NPTH mounting holes, 4.064 mm (0.160 in), in the board frame.
MOUNT_HOLE_D = 4.064
MOUNT_HOLES = {
    "lower_left": (6.35, 6.985),      # Gerber (-71.755, -40.640)
    "lower_right": (86.995, 7.62),    # Gerber (  8.890, -40.005), under the shunt regulator
    "upper_mid": (63.5, 61.595),      # Gerber (-14.605,  13.970), under the RS-232 module
}

# Header / module seating heights above the board (z of the module's PCB
# underside).  Male 0.1" header plastic = 2.54 mm; KiCad 1x20 socket = 8.5 mm.
HEADER_PLASTIC = 2.54
SOCKET_H = 8.5
MODULE_Z = BOARD_T + HEADER_PLASTIC                # 4.14: Tic, DRV8871, DRV2605L, D24V22F5, shunt
STACK_Z = BOARD_T + SOCKET_H + HEADER_PLASTIC      # 12.64: Pico W (in sockets), RS-232 module (own sockets)

# Standoffs below the board (M3 F-F hex, 10 mm) and screws from the top.
STANDOFF_L = 10.0
