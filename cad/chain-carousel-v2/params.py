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
N_LINKS = 104        # per chain, cut from a 10 ft roll (two loops use 208 of its 320 links)
INNER_W = W_IN + 2 * PLATE_T              # 7.32, inner link across the plates
OUTER_GAP = INNER_W + 0.05                 # outer plates' inside faces
OUTER_W = OUTER_GAP + 2 * PLATE_T          # 9.91
PIN_LEN = OUTER_W + 2 * PIN_HEAD

# A-1 attachment connecting link (bent tab, one hole): Nitro CL35-A1, which
# matches Tsubaki's RS35 A-1 table: S = 0.250 in pitch line -> tab face,
# C = 0.375 in chain centre plane -> hole, X = 0.562 in -> tab end, N = 0.312
# in tab width, hole 0.133 in (M3; Red Boar's is 0.10 in). With the chain in a vertical plane
# the tab lies along the pins, on the outside of the loop, and its hole is
# radial: vertical at the station, square to the augers and to the travel.
A1_C = 6.35          # S: pitch line -> tab mounting face (radially outward)
A1_HOLE_D = 3.38
A1_TAB_L = 7.9       # N
A1_HOLE_C = 9.525    # C, from the chain centre plane toward the modules
A1_X = 14.3          # X, tab end from the chain centre plane

# --- 32T ANSI 35 sprockets, type B (hub one side): 35BS32-5/8, Surplus Center 601139 ---
# 32 teeth: four 90-degree wraps of exactly 8 links each, and a pitch radius
# big enough that the auger's 44T gear clears the corner shafts (see SHAFT_CLEAR).
N_TEETH = 32
PD = P / math.sin(math.pi / N_TEETH)                 # 97.13 pitch diameter
R = PD / 2                                           # 48.57
OD = P * (0.6 + 1 / math.tan(math.pi / N_TEETH))     # 102.42 outside diameter
TOOTH_W = 4.27       # 0.168" single-strand #35 tooth
SEAT_D = 1.005 * BUSH_D + 0.076                      # ANSI seating-curve diameter
HUB_D = 50.8         # 2 in hub
LTB = 22.225         # length through bore, 7/8 in
SPROCKET_BORE = 15.875  # 5/8 in finished bore, 3/16 x 3/32 in keyway, 2 set screws
KEYWAY = (4.76, 2.38)

# --- loop: four sprockets on a rectangle, 104 links ---
LOOP_M, LOOP_N = 12, 24  # links on the bottom/top runs and on each side
LOOP_B = LOOP_M * P  # 114.3 horizontal centre distance: 32T tips (102.4 OD) clear by 11.9 mm
LOOP_A = LOOP_N * P  # 228.6 vertical centre distance: room to tilt module 1 to 90 deg
assert 2 * (LOOP_M + LOOP_N) + N_TEETH == N_LINKS   # closes exactly: 24 + 48 + 32
LOOP_Y = LOOP_B / 2  # corner shafts at y = +-57.15
Z_RUN = 210.0        # bottom run's pitch line above the bench: room for the station under it
Z_BOT = Z_RUN + R    # bottom corner shafts
Z_TOP = Z_BOT + LOOP_A                               # top corner shafts (as built, before tensioning)
CHAIN_L = 305.0      # front chain -> back chain, centre plane to centre plane

# --- modules ---
MODULE_LINKS = 8                                      # 8 pitches = 76.2 mm
N_MODULES = N_LINKS // MODULE_LINKS                   # 13

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
CAR_W = 60.0         # along the travel: 16.2 mm between neighbours on the straights
CAR_T = 5.0          # Sam's base plates are 5 mm
CAR_W0 = -A1_C                                       # plate's inner face (on the tabs)
CAR_X0, CAR_X1 = -23.0, CHAIN_L + 23.0               # tongue ends, beyond both chains
TONGUE_W = 40.0      # along the travel
TONGUE_L = 16.0      # beyond the chain's outer plates
RIB = (4.0, 7.0)     # edge ribs on the inside: width, height
HINGE_W = SAM_DROP + CAR_W0                          # 11.65: hinge axis inside the pitch line
LUG_U = 25.5         # hinge lug inner faces, 0.5 mm outside Sam's 50 mm knuckle
LUG_T = 4.0          # lugs end at u = +-29.5, inside the carriage's +-30
# On a corner two neighbours are 90 deg apart about the sprocket axis, so a
# point (u, w) on one meets the other unless |u| + w < R (48.6). The lugs are
# chamfered to |u| + w <= INNER_CORNER and the hinge screws are flush.
INNER_CORNER = 45.0
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
POST_Y = 112.0       # post centres: clear of the bearings and the motor standoffs; the frame encloses the carriages
SIDE_GAP = 30.0      # chain centre plane -> side plate's inner face
PLATE_T_SIDE = 6.35  # 1/4 in 6061 side plates
SIDE_W = 2 * POST_Y + EXT                             # 244
SIDE_Z = (180.0, 555.0)                               # front side plate bottom, top
SIDE_Z_BACK = (70.0, 555.0)                           # the back plate runs down to carry the motor
FOOT_H = 15.0        # leveling foot: bench -> underside of the base rails
Z_BASE = FOOT_H      # base rails' underside
Z_TOP_RAIL = 576.0   # top rails' underside, above the side plates and the post-head brackets
TENSION_TRAVEL = (-6.0, 8.0)  # top shafts' slot travel about nominal: down to fit the chain, up to tension it
DRIVE_TRAVEL = 4.0   # motor slides +-4 mm in its slots to tension the drive chain

# --- shafts and bearings (all four corners alike) ---
SHAFT_D = 15.875     # 5/8 in keyed shafting (the sprockets' bore)
# SBSFL202-10 2-bolt stamped-steel flange unit (Surplus Center 600174): 3.189 x
# 2.3125 x 0.875 in, 2-1/2 in bolt centres, 1/4 in bolts, 7/8 in through the
# insert. Its rear dome sits in a 49 mm hole in the plate (FYH catalogue).
BRG = dict(L=81.0, W=58.7, J=63.5, T=3.0, OUT=12.6, IN=9.6, DOME_D=47.0, RING_D=24.0, BOLT_D=6.35, HOLE=49.0)
SHAFT_CLEAR = R - HINGE_W - GEAR_R - SHAFT_D / 2     # 6.0: gear past a corner shaft

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

# --- drive: NEMA 34 inside the frame on the back plate, #35 drive chain up to the B+ shaft ---
# Two 35BS15H sprockets (Surplus Center: 5/8 in keyed on the shaft, 1/2 in
# re-bored to 14 mm + 5 mm keyway on the motor): 1.99 in OD, 1-11/32 in hub,
# 3/4 in through the bore. 44 links from the roll's spare, 1:1.
N15 = 15
PD15 = P / math.sin(math.pi / N15)                   # 45.81
HUB15_D, LTB15 = 34.1, 19.05
DRIVE_LINKS = 44
C_DRIVE = (DRIVE_LINKS - N15) / 2 * P                # 138.11: closes exactly with 14-link spans (as v1's loop)
Z_MOTOR = Z_BOT - C_DRIVE                            # 120.46: motor axis, under the B+ shaft

# --- station test fixtures ---
HOLD_DOWN_GAP = 0.5
MAGNET_D, MAGNET_H = 6.35, 3.18                       # K&J D42-N52, 1/4 x 1/8 in
