"""Dimensions for the chain-carousel test rig (issue #128), in mm.

One place for every number the model uses. Purchased-part dimensions come
from the vendor's own tables (sources in BOM.md); printed-part numbers are
design choices. World frame: x along the long axis of the loop (drive end at
+x), y across it, z up, deck top surface at z = 0.
"""
from __future__ import annotations

import math

# --- ANSI #35 roller chain (ASME B29.1; the Aobbmok listing on the ME order) ---
P = 9.525            # pitch (3/8")
BUSH_D = 5.08        # #35 is rollerless: the bushing (0.200") is what the teeth seat on
PIN_D = 3.58         # 0.141"
W_IN = 4.78          # width between inner plates (0.188")
PLATE_T = 1.27       # 0.050"
PLATE_H = 9.0        # plate height, 0.354"
PIN_HEAD = 0.45      # riveted pin end beyond the outer plate
N_LINKS = 96         # 3 ft box, closed with one of its two connecting links
INNER_W = W_IN + 2 * PLATE_T              # 7.32, inner link across the plates
OUTER_GAP = INNER_W + 0.05                 # outer plates' inside faces
OUTER_W = OUTER_GAP + 2 * PLATE_T          # 9.91
PIN_LEN = OUTER_W + 2 * PIN_HEAD

# The chain lies flat on the deck (pins vertical), resting on its pin heads.
CHAIN_Z = PIN_LEN / 2                       # chain centre plane above the deck

# A-1 attachment connecting link (bent tab, one hole, on the top plate).
# Tsubaki/US Tsubaki RS35 A-1 envelope; see BOM.md for the vendor table.
A1_C = 7.9           # chain centre line -> tab mounting face (radial here)
A1_H = 9.5           # tab height above the top outer plate
A1_HOLE_D = 3.4      # M3 clearance
A1_HOLE_Z = 5.6      # hole centre above the top outer plate
A1_TAB_L = 15.9      # tab length along the chain

# --- 19T ANSI 35 sprockets (USA Roller Chain 35B19 / 35BB19H tables) ---
N_TEETH = 19
PD = P / math.sin(math.pi / N_TEETH)                 # 57.87 pitch diameter
OD = P * (0.6 + 1 / math.tan(math.pi / N_TEETH))     # 62.88 outside diameter
TOOTH_W = 4.27       # 0.168" single-strand #35 tooth
SEAT_D = 1.005 * BUSH_D + 0.076                      # ANSI seating-curve diameter
HUB_D = 42.1         # 35B19 hub (1-21/32")
LTB = 22.2           # length through bore (7/8")
DRIVE_BORE = 14.0    # bored to the NEMA 34 shaft, 5 mm key
IDLER_BORE = 9.525   # 3/8" ball-bearing idler
IDLER_HUB_D = 28.6
IDLER_W = 12.7

# Centre distance for 96 links on two 19T sprockets (ANSI formula, equal
# sprockets: L = 2C/P + N). layout.py refines it so the loop closes exactly.
C_NOMINAL = (N_LINKS - N_TEETH) * P / 2              # 366.71
TENSION_TRAVEL = 12.0                                 # idler slot length

# --- modules ---
MODULE_LINKS = 8                                      # 8 pitches = 76.2 mm
N_MODULES = N_LINKS // MODULE_LINKS                   # 12

# --- StepperOnline 34HS59-6004D-E1000 (NEMA 34, 12 N*m, 1000-line encoder) ---
M34_FLANGE = 86.0
M34_BOLT_SQ = 69.58
M34_HOLE_D = 5.5
M34_PILOT_D = 73.0
M34_PILOT_H = 1.6
M34_SHAFT_D = 14.0
M34_SHAFT_L = 32.0
M34_KEY_W = 5.0
M34_BODY_L = 156.0                                    # motor body
M34_ENC_L = 20.0                                      # encoder housing behind it

# --- deck and frame ---
DECK_T = 12.7        # 1/2" HDPE
DECK_L = 1050.0      # cut from a 48" x 48" sheet; set by the 250 mm auger (README)
DECK_W = 740.0
EXT = 20.0           # 2020 extrusion
RAIL_Y = DECK_W / 2 - EXT / 2 - 5                     # long rails, centre y
CROSS_X = (-505.0, -280.0, None, None, 505.0)         # None: the two either side of the motor
LEG_L = 230.0
MOTOR_PLATE_T = 6.35  # 1/4" 6061
MOTOR_PLATE = 140.0

# --- printed carriage (base plate the mounting plate hinges on) ---
# Carriage frame: X along the chain, Y radially outward from the chain pitch
# line, Z up from the deck. Its inner face bolts to the A-1 tab. The lab
# auger is 250 mm long and Sam's Oct 8 mounting plate holds it outlet-end at
# the hinge, so the tube runs 150 mm past the plate back toward the chain:
# the hinge has to sit ~270 mm out for the cap end to stay outside the chain.
CAR_W = 70.0         # along the chain: 6.2 mm between neighbours on the straights
CAR_Y0 = A1_C + PLATE_T                               # inner face on the tab
CAR_L = 290.0        # radial; one piece on the H2D (350 x 320 bed)
CAR_T = 5.0          # Sam's base plates are 5 mm
CAR_SKID = 1.5       # PETG skids under the plate ride on the HDPE
RIB = (6.0, 6.0)     # edge ribs: width, height above the plate
TONGUE = (8.0, 3.0, 60.0)                             # radial, thick, wide
HINGE_Y = CAR_Y0 + 270.0                              # hinge axis, radial
HINGE_Z = 28.0       # gear (46 OD) clears the deck by 5 mm
LUG_X = 30.5         # lug centre planes, outside Sam's 54 mm plate
LUG_T = 5.0
HINGE_D = 5.3        # M5 pin, as in Sam's parts
# Station reach-through: clears Sam's Oct 8 electronics carriage (71 x 36)
# and the auger's 44T gear when the mounting plate rests on the carriage.
CUT_Y = (CAR_Y0 + 186.0, CAR_Y0 + 272.0)
CUT_X = 21.0
SAM_GEAR_XS = 73.75  # gear centre in Sam's part studio (x along the auger)
AUGER_Z0_XS = -4.6   # auger STEP z = 0 (outlet end) in Sam's x

# --- station test fixtures ---
HOLD_DOWN_GAP = 0.5
HALL_R_INDEX = 70.0  # radial position of the index magnet on every carriage
HALL_R_HOME = 105.0  # only carriage 1 has a magnet here
MAGNET_D, MAGNET_H = 6.0, 3.0
