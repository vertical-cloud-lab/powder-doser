"""Dimensions for the paternoster multi-doser carousel (issue #128), in mm.

A second, independent design next to the chain carousel v2. Two #35 chains
run in vertical planes at the front and back of the modules, each round four
32T corner sprockets. Every 10th pitch an SA-1 attachment link carries a
shoulder-screw pivot, and a printed gondola hangs between the front and back
pivots. Gravity keeps each gondola, and the doser module in it, upright all
the way round: on the straights, over the top and round the corners. Nothing
on a module is ever sideways or upside down.

* The bottom corner shafts go right through from the front chain to the back
  chain: they keep the two chains in step, and one of them is the drive.
* The top corners turn on stub shafts that end flush with the sprocket's inner
  face. A through shaft at the top would sit in the path of every gondola
  going over the top.
* The station is mid-way along the bottom run. The module tilts up into the
  empty middle of the loop, so nothing above it is in the way.

World frame: x along the augers (front chain's centre plane at x = 0, back
chain's at x = CHAIN_L), y across the loop (the bottom run moves toward +y),
z up, bench top at z = 0. Purchased-part numbers are from the vendor tables
cited in BOM.md; printed-part numbers are design choices.
"""
from __future__ import annotations

import math

# --- ANSI #35 roller chain (ASME B29.1; rollerless) ---
P = 9.525            # pitch, 3/8 in
BUSH_D = 5.08        # bushing (0.200 in), what the teeth seat on
PIN_D = 3.58         # 0.141 in
W_IN = 4.78          # between inner plates, 0.188 in
PLATE_T = 1.27       # 0.050 in
PLATE_H = 9.0        # 0.354 in
PIN_HEAD = 0.45
INNER_W = W_IN + 2 * PLATE_T                 # 7.32
OUTER_GAP = INNER_W + 0.05                   # outer plates' inside faces
OUTER_W = OUTER_GAP + 2 * PLATE_T            # 9.91
PIN_LEN = OUTER_W + 2 * PIN_HEAD

# SA-1 attachment connecting link (straight tab in the plane of one outer
# plate, one hole). Tsubaki RS35 SA-1: C1 = 0.375 in (pitch line -> hole),
# N = 0.311 in (tab width), O = 0.102 in (hole), Xs = 0.573 in (pitch line ->
# tab end). The tab points out of the loop and sits on the outer plate on the
# gondola's side, so the hole's axis runs along x, parallel to the chain pins.
SA1_C = 9.525
SA1_N = 7.9
SA1_HOLE = 2.6       # opened to 3.4 mm (No. 29 drill) for an M3 shoulder screw thread
SA1_HOLE_DRILLED = 3.4
SA1_XS = 14.55
TAB_X0 = OUTER_GAP / 2                       # tab's inner face (toward the chain)
TAB_X1 = OUTER_GAP / 2 + PLATE_T             # tab's outer face (toward the gondola)

# --- 32T ANSI 35 sprockets (35BS32-5/8, type B, hub one side) ---
N_TEETH = 32
PD = P / math.sin(math.pi / N_TEETH)         # 97.13
R = PD / 2                                   # 48.57
OD = P * (0.6 + 1 / math.tan(math.pi / N_TEETH))   # 102.42
TOOTH_W = 4.27
SEAT_D = 1.005 * BUSH_D + 0.076
HUB_D = 50.8
LTB = 22.225
SPROCKET_BORE = 15.875
KEYWAY = (4.76, 2.38)

# --- loop: four 32T corners on a rectangle, 120 links per chain ---
LOOP_M = 20          # links on the bottom and top runs (B = 190.5)
LOOP_N = 24          # links on each side (A = 228.6)
N_LINKS = 2 * (LOOP_M + LOOP_N) + N_TEETH   # 120: each 90 deg wrap is exactly 8 links
LOOP_B = LOOP_M * P
LOOP_A = LOOP_N * P
CORNER_Y = LOOP_B / 2                        # corner shafts at y = +-95.25
Z_BOT = 420.0        # bottom corner shafts above the bench: room for the station under the bottom run
Z_TOP = Z_BOT + LOOP_A
CHAIN_L = 325.0      # front chain -> back chain, centre plane to centre plane

# --- modules ---
MODULE_LINKS = 10    # an SA-1 link every 10 pitches (even, so always an outer link)
N_MODULES = N_LINKS // MODULE_LINKS          # 12
MODULE_PITCH = MODULE_LINKS * P              # 95.25
STATION_U = LOOP_M / 2                       # station: link position along the loop (links from the bottom-left corner)
LOAD_U = STATION_U + 3 * MODULE_LINKS        # loading position: right side, mid-height (module k+3)

# --- pivot: M3 shoulder screw (4 mm shoulder) through the SA-1 tab ---
PIV_R = R * math.cos(math.pi / N_TEETH) + SA1_C    # pivot radius round a corner (link midpoint + C1)
SHOULDER_D = 4.0
SHOULDER_L = 8.0
SHOULDER_HEAD_D, SHOULDER_HEAD_H = 7.0, 3.0
WASHER_T = 0.8       # PTFE thrust washer between the tab and the gondola
BUSHING_FLANGE = (6.0, 0.8)   # flanged sleeve bearing in the gondola: (flange OD rim, flange thickness) -- see BOM
END_X0 = TAB_X1 + WASHER_T + 0.1             # gondola end plate's outer face
END_T = 6.0
END_X1 = END_X0 + END_T

# --- gondola (printed PETG), profile about its pivot ---
# Upright box that every gondola stays inside: y in +-GON_W/2, z in [GON_Z0, GON_Z1].
# The loop study (sim/clearance_study.py) checks two neighbours never overlap.
GON_W = 62.0
GON_Z0, GON_Z1 = -48.0, 9.0
GON_X0, GON_X1 = END_X0, CHAIN_L - END_X0
FLOOR_T = 5.0

# --- the module in a gondola (Sam's mounting plate + the lab auger) ---
# Sam's studio frame: hinge axis = his y at x = z = 0, auger along his +x from
# the outlet end, the plate's underside at his z = -18. In a gondola his x is
# world x, his y world y, his z world z (the module is never turned).
HINGE_X = 45.0       # hinge axis from the front chain's centre plane
HINGE_Z = -16.0      # hinge axis below the pivot
SAM_DROP = 18.0      # hinge axis above the plate's underside
AUGER_Z0_XS = 0.4    # auger STEP z = 0 (outlet end) in Sam's x
AUGER_LEN = 250.0
GEAR_R = 23.0
KNUCKLE_HALF = 25.0  # Sam's hinge knuckle spans his y = +-25
LUG_IN = 25.5        # gondola hinge lugs' inner faces
LUG_T = 5.5          # |y| 25.5-31: holds a short M5 heat-set insert
HINGE_PIN_D = 5.0    # M5 thumb screw tips are the hinge pins (Sam's knuckle holes are 5.3, at |y| 15-25)
KNUCKLE_IN = 15.0    # Sam's knuckles' inner faces
THUMB_L = 16.0       # M5 x 16 knurled thumb screw: from the lug's outer face (|y| = 31) to the knuckle's inner face
THUMB_HEAD = (11.0, 4.5)   # knurled head dia, height
INSERT_D = 6.4       # M5 heat-set insert hole in the lug

# Station reach-through for Sam's electronics carriage (his x 2.3-73.3, y +-18).
WIN_X = (HINGE_X + 0.5, HINGE_X + 100.0)   # to the 44T gear's far side and the carriage's tilt sweep
WIN_Y = 21.0

# --- frame: 2020 extrusion, built vertically, with 1/4 in 6061 side plates ---
EXT = 20.0
PLATE_T_SIDE = 6.35
SIDE_IN = -33.0      # front side plate's inner face (x); the back one mirrors at CHAIN_L - SIDE_IN
FOOT_H = 15.0

# --- shafts and bearings ---
SHAFT_D = 15.875     # 5/8 in
# SBSFL202-10 2-bolt stamped-steel flange unit (3.189 x 2.3125 x 0.875 in, 2-1/2 in bolt centres)
BRG = dict(L=81.0, W=58.7, J=63.5, T=3.0, OUT=12.6, IN=9.6, DOME_D=47.0, RING_D=24.0, BOLT_D=6.35, HOLE=49.0)
TENSION_TRAVEL = (-6.0, 8.0)  # top stub shafts slide in slots: down to fit the chain, up to tension it

# --- StepperOnline 34HS59-6004D-E1000 (NEMA 34, 12 N*m, 1000-line encoder) ---
M34_FLANGE = 86.0
M34_BOLT_SQ = 69.58
M34_HOLE_D = 5.5
M34_PILOT_D = 73.0
M34_SHAFT_D = 14.0
M34_SHAFT_L = 37.0
M34_BODY_L = 150.0
M34_ENC_L = 19.0
STEPS_PER_REV = 4000
STEPS_PER_MODULE = STEPS_PER_REV * MODULE_LINKS // N_TEETH   # 1250: direct drive, 10/32 of a turn

# --- station: Actuonix P16-P feedback actuator tilts the module ---
ACT_STROKE = 150.0
ACT_RETRACTED = 197.0        # hole to hole, retracted (P16-P, 150 mm stroke)
ACT_BODY = (37.0, 26.0)      # body cross-section (envelope)
ACT_CLEVIS_D = 4.1
TILT_MAX = 90.0

MAGNET_D, MAGNET_H = 6.35, 3.18

# --- top idlers: 35BS32 re-bored to 35 mm H7 for two 6202-2RS, on a fixed 15 mm axle stud ---
IDLER_BORE = 35.0
IDLER_AXLE_L = 31.0          # bearing seat from the shoulder (on the plate's inner face) to flush with the sprocket face
SPROCKET_FACE = TOOTH_W / 2  # tooth ring's inner face, x = +2.13 at the front chain: nothing on the axis goes further in

# --- jaw coupling, NEMA 34 (14 mm) to the 5/8 in drive shaft: Lovejoy L-075 class ---
CPL_OD, CPL_L = 44.5, 52.3

# --- gondola details ---
BUSHING_OD = 6.0             # flanged sleeve bearing 4 x 6 x 6 pressed into the end plates
HINGE_HOLE = 5.3
HINGE_PIN_GRIP = 62.0
SADDLE_XS = 190.0            # saddle under the auger tube, in Sam's x from the hinge
AUGER_R_TUBE = 12.5          # the auger's tube is 25 mm across (44T gear 46 mm)

# --- station geometry (Sam's studio frame at the station; actuator rod end pinned under his carriage) ---
YOKE_X, YOKE_Z = 40.0, -72.0 # clevis pin under the electronics carriage, Sam's x, z
TONGUE_X = YOKE_X + 25.0     # guide tongue (rides the approach fork), Sam's x
DOCK_EXT = 30.0              # actuator extension when the carriage meets the plate (approach = DOCK_EXT)
ACT_REAR = 8.0               # rear clevis hole -> body start
ACT_BODY_L = 175.0
ACT_ROD_D = 10.0
CLEVIS_H = 12.0
FORK_H = 36.0
VIAL_H = 61.0
LC_L = 80.0
VIAL_X = HINGE_X - 3.0       # vial under the outlet

# --- frame layout ---
SIDE_HALF_W = 160.0
SIDE_Z = (355.0, 700.0)
POST_Y = 140.0             # post centres: clear of the bottom flange bearings
BASE_Z = FOOT_H              # base rails' underside
TOP_Z = 745.0                # top of the posts (top x-rails sit on them)
MOTOR_PLATE = 120.0
MOTOR_SO = (28.0, 52.0)      # standoff offsets (y, z) from the motor axis: inside the posts, outside the flange bearing
MOTOR_STANDOFF = BRG["OUT"] + 6.0 + CPL_L - 25.0 + M34_SHAFT_L - PLATE_T_SIDE   # 76.55: back plate -> motor plate


def pivot_on_straight_z() -> float:
    """Pivot height on the bottom run (link midpoint on the pitch line, then C1 down)."""
    return Z_BOT - R - SA1_C


if __name__ == "__main__":
    print(f"links {N_LINKS}, modules {N_MODULES} every {MODULE_PITCH:.2f} mm, corners R {R:.2f}, pivot R {PIV_R:.2f}")
    print(f"loop {LOOP_B:.1f} x {LOOP_A:.1f} between corner centres; station pivot z {pivot_on_straight_z():.1f}")
    print(f"steps per module {STEPS_PER_MODULE}")

# --- placement details (layout.py) ---
DRIVE_EXT = 28.0             # drive shaft runs on past the back bearing into the coupling
MODULE_LIFT = 16.0           # swap: lift the module clear of the lugs and rails...
MODULE_SLIDE = 70.0          # ...then slide it out sideways (+y) from the loading position
NEMA11_X, NEMA11_Z = 73.3, -32.0   # NEMA 11 face on the carriage's back face, 32 mm under the auger axis (20T:44T, m1)
SOL_X, SOL_Z = 12.0, -24.0   # solenoid under the auger tube near the outlet, plunger up
STATION_RAIL_X = (VIAL_X, HINGE_X + YOKE_X)   # base cross rails under the vial post and the actuator
FORK_POST_Y = -45.0
VIAL_POST_Y = -120.0
VIAL_GAP = 32.0              # vial mouth below the gondolas' lowest point: clear of the docked electronics carriage
HALL_X = (130.0, 160.0)      # INDEX magnet (every gondola) and HOME magnet (gondola 1), under the -y rail
HALL_GAP = 3.0
_PIV0 = Z_BOT - R * math.cos(math.pi / N_TEETH) - SA1_C            # station pivot height (polygonal: f = 0.5)
_HINGE_W = _PIV0 + HINGE_Z
FORK_Z = _HINGE_W - 60.75 - 25.0 - 1.0 - FORK_H                     # fork bottom; its top is 1 mm under the docked tongue
STATION_POST_H = FORK_Z + 12.0 - (BASE_Z + EXT)
VIAL_Z = _PIV0 + GON_Z0 - VIAL_GAP - VIAL_H                         # vial base
VIAL_POST_H = VIAL_Z - 3.0 - 12.7 - (BASE_Z + EXT)
