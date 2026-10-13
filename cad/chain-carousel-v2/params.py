"""Dimensions for the chain-carousel test rig v2 (issue #128), in mm.

v2 is a vertical twin-chain loop: two #35 chains in vertical planes, one at
the front of the carriages (the auger's outlet/hinge end) and one at the
back (cap end). Each chain runs round four 32T sprockets on the corners of a
rectangle; the front and back sprockets at each corner share one shaft, so
the two chains can't drift out of step. The carriages bolt to an A-1 lug on
each chain from the outside of the loop and the modules ride on the inside,
between the chains. The station is on the bottom straight.

One place for every number the model uses. Purchased-part dimensions come
from the vendor's own tables (sources in BOM.md); printed-part numbers are
design choices. World frame: x along the augers (front chain's centre plane
at x = 0, back chain's at x = CHAIN_L), y across the loop (the bottom run
travels toward +y), z up, bench top at z = 0.
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
N_LINKS = 96         # per chain: one 3 ft box each, closed with one of its two connecting links
INNER_W = W_IN + 2 * PLATE_T              # 7.32, inner link across the plates
OUTER_GAP = INNER_W + 0.05                 # outer plates' inside faces
OUTER_W = OUTER_GAP + 2 * PLATE_T          # 9.91
PIN_LEN = OUTER_W + 2 * PIN_HEAD

# A-1 attachment connecting link (bent tab, one hole), from Tsubaki's RS35
# A-1 table: S = 0.250 in pitch line -> tab face, C = 0.375 in chain centre
# plane -> hole, X = 0.563 in -> tab end, N = 0.311 in tab width, hole
# 0.102 in (Red Boar's is 0.10 in: M2.5). With the chain in a vertical plane
# the tab lies along the pins, on the outside of the loop, and its hole is
# radial: vertical at the station, square to the augers and to the travel.
A1_C = 6.35          # S: pitch line -> tab mounting face (radially outward)
A1_HOLE_D = 2.6
A1_TAB_L = 7.9       # N
A1_HOLE_C = 9.525    # C, from the chain centre plane toward the modules
A1_X = 14.3          # X, tab end from the chain centre plane

# --- 32T ANSI 35 sprockets, type B (hub one side) ---
# 32 teeth: four 90-degree wraps of exactly 8 links each, and a pitch radius
# big enough that the auger's 44T gear clears the corner shafts (see SHAFT_CLEAR).
N_TEETH = 32
PD = P / math.sin(math.pi / N_TEETH)                 # 97.13 pitch diameter
R = PD / 2                                           # 48.57
OD = P * (0.6 + 1 / math.tan(math.pi / N_TEETH))     # 102.42 outside diameter
TOOTH_W = 4.27       # 0.168" single-strand #35 tooth
SEAT_D = 1.005 * BUSH_D + 0.076                      # ANSI seating-curve diameter
HUB_D = 63.5         # 35B32 hub, 2-1/2 in
LTB = 25.4           # length through bore, 1 in
SPROCKET_BORE = 12.7  # 1/2 in finished bore, set screws over a flat

# --- loop: four sprockets on a rectangle, 96 links ---
LOOP_B = 8 * P       # 76.2  horizontal centre distance (bottom and top runs: 8 links)
LOOP_A = 24 * P      # 228.6 vertical centre distance (the two sides: 24 links)
assert 2 * (8 + 24) + N_TEETH == N_LINKS            # closes exactly: 16 + 48 + 32
LOOP_Y = LOOP_B / 2  # corner shafts at y = +-38.1
Z_RUN = 210.0        # bottom run's pitch line above the bench: room for the station under it
Z_BOT = Z_RUN + R    # bottom corner shafts
Z_TOP = Z_BOT + LOOP_A                               # top corner shafts (as built, before tensioning)
CHAIN_L = 305.0      # front chain -> back chain, centre plane to centre plane

# --- modules ---
MODULE_LINKS = 8                                      # 8 pitches = 76.2 mm
N_MODULES = N_LINKS // MODULE_LINKS                   # 12

# --- the module on a carriage (Sam's Oct 8 mounting plate + the lab auger) ---
# Sam's studio frame: hinge axis = his y, auger axis = his x at z = 0, the
# plate's underside at z = -18. On a carriage his x points front -> back,
# his y along the travel and his z into the loop.
HINGE_X = 33.0       # hinge axis, from the front chain's centre plane
SAM_DROP = 18.0      # hinge axis above the plate's underside
GEAR_R = 23.0        # the auger's 44T gear (46 OD), its widest part
AUGER_Z0_XS = 0.4    # auger STEP z = 0 (outlet end) in Sam's x
AUGER_LEN = 250.0

# --- printed carriage ---
# Carriage frame: u along the travel, w radially inward (into the loop), x
# front -> back. Origin on the front chain's pitch line, mid-way between the
# A-1 link's pins. The plate sits on the two A-1 tabs, outside the chains.
CAR_W = 66.0         # along the travel: 10.2 mm between neighbours on the straights
CAR_T = 5.0          # Sam's base plates are 5 mm
CAR_W0 = -A1_C                                       # plate's inner face (on the tabs)
CAR_X0, CAR_X1 = -23.0, CHAIN_L + 23.0               # tongue ends, beyond both chains
TONGUE_W = 40.0      # along the travel
TONGUE_L = 16.0      # beyond the chain's outer plates
RIB = (4.0, 7.0)     # edge ribs on the inside: width, height
HINGE_W = SAM_DROP + CAR_W0                          # 11.65: hinge axis inside the pitch line
LUG_U = 25.5         # hinge lug inner faces, 0.5 mm outside Sam's 50 mm knuckle
LUG_T = 4.0
HINGE_D = 5.3        # M5 pin, as in Sam's parts
# Station reach-through: Sam's electronics carriage (his x 2.3-73.3, y +-18),
# the gear (his x 78.3-88.3) and the outlet's powder path when tilted.
WIN_X = (HINGE_X - 14.0, HINGE_X + 92.0)
WIN_U = 21.0
# Snap hooks that keep Sam's plate shut upside down (top of the loop): they
# overhang the plate's edge where it is 50 mm wide (his x 40-65).
SNAP_X = HINGE_X + 52.0
SNAP_LAP = 0.8       # overhang onto the plate's top edge

# --- 2020 frame, built vertically ---
EXT = 20.0
POST_Y = 95.0        # post centres; clears the motor flange and the bearings
SIDE_GAP = 30.0      # chain centre plane -> side plate's inner face
PLATE_T_SIDE = 6.35  # 1/4 in 6061 side plates
SIDE_W = 2 * POST_Y + EXT                             # 210
SIDE_Z = (180.0, 555.0)                               # side plate bottom, top
FOOT_H = 15.0        # leveling foot: bench -> underside of the base rails
Z_BASE = FOOT_H      # base rails' underside
Z_TOP_RAIL = 576.0   # top rails' underside, above the side plates and the post-head brackets
TENSION_TRAVEL = (-6.0, 8.0)  # top shafts' slot travel about nominal: down to fit the chain, up to tension it

# --- shafts and bearings (all four corners alike) ---
SHAFT_D = 12.7       # 1/2 in
BRG = dict(L=113.0, J=90.0, W=60.0, T=11.0, H=33.3, BOSS_D=52.0, BOLT_D=10.0)   # UCFL201-8 envelope
SHAFT_CLEAR = R - HINGE_W - GEAR_R - SHAFT_D / 2     # 7.6: gear past a corner shaft

# --- StepperOnline 34HS59-6004D-E1000 (NEMA 34, 12 N*m, 1000-line encoder) ---
M34_FLANGE = 86.0
M34_BOLT_SQ = 69.58
M34_HOLE_D = 5.5
M34_PILOT_D = 73.0
M34_PILOT_H = 1.6
M34_SHAFT_D = 14.0
M34_SHAFT_L = 37.0   # 25 mm of it keyed
M34_KEY_W = 5.0
M34_BODY_L = 150.0
M34_ENC_L = 19.0
COUPLING = dict(D=30.0, L=40.0)                      # jaw coupling 14 mm <-> 1/2 in
MOTOR_SHAFT_IN = 17.0  # motor shaft's engagement in the coupling
STANDOFF_L = BRG["H"] + 1.0 + COUPLING["L"] + M34_SHAFT_L - MOTOR_SHAFT_IN   # 94.3: side plate -> motor flange

# --- station test fixtures ---
HOLD_DOWN_GAP = 0.5
MAGNET_D, MAGNET_H = 6.35, 3.18                       # K&J D42-N52, 1/4 x 1/8 in
