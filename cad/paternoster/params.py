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
PIN_HEAD = 0.95       # pin heads stand 0.95 mm proud of the tab plate (McMaster 7321K31 STEP)
INNER_W = W_IN + 2 * PLATE_T                 # 7.32
OUTER_GAP = INNER_W + 0.05                   # outer plates' inside faces
OUTER_W = OUTER_GAP + 2 * PLATE_T            # 9.91
PIN_LEN = OUTER_W + 2 * PIN_HEAD

# SA-1 attachment connecting link (straight tab in the plane of one outer
# plate, one hole): McMaster 7321K31, measured from McMaster's STEP and drawing:
# C1 = 0.375 in (pitch line -> hole), tab 0.312 in wide, hole 0.134 in, tab end
# 0.578 in from the pitch line. The tab is on the pressed plate; the clip goes on
# the other side, away from the gondola. The tab points out of the loop and sits on the outer plate on the
# gondola's side, so the hole's axis runs along x, parallel to the chain pins.
SA1_C = 9.525
SA1_N = 7.9
SA1_HOLE = 3.4       # McMaster 7321K31 / Nitro CL35-SA1: 0.134 in, M3 passes (Tsubaki's 0.102 in would need a No. 29 drill)
SA1_HOLE_DRILLED = 3.4
SA1_XS = 14.68
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
Z_BOT = 432.0        # bottom corner shafts above the bench: room for the station under the bottom run (+12 mm for the
                     # U-yoke's 60 mm reach below the carriage's stub pins, so the P16's base clevis still sits on its rail)
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
SHOULDER_L = 10.0    # McMaster 90265A121: 18-8, 4 x 10 mm shoulder, M3 x 5 thread (reaches the nylock's ring)
SHOULDER_HEAD_D, SHOULDER_HEAD_H = 6.0, 3.0
WASHER_T = 0.8       # PTFE thrust washers (95630A630, 4.3 x 9 x 0.8): one on the tab, one under the head
BUSHING_FLANGE = (10.0, 1.5)  # McMaster 6659K65 bronze: 4 ID x 7.02 OD x 6, flange 10 x 1.5
END_X0 = TAB_X1 + WASHER_T + 0.6             # gondola end plate's outer face: 0.75 mm clear of the pin heads
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
THUMB_HEAD = (11.0, 5.0)   # McMaster 92545A179 low-profile knurled head
INSERT_D = 6.4       # M5 heat-set insert hole in the lug

# Station reach-through for Sam's electronics carriage (his x 2.3-73.3, y +-18).
WIN_X = (HINGE_X + 0.5, HINGE_X + 116.0)   # to the dock magnet's bracket (Sam's x 111) and the carriage's tilt sweep
WIN_Y = 23.5         # the U-yoke's steel arms (|y| 19.5-21.5) rise through the window as the module tilts

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
ACT_RETRACTED = 197.4        # hole to hole, retracted: P16-150-22-12-P (Actuonix STEP), stroke + 47
ACT_BODY = (36.0, 20.0)      # motor/gear block, 79 long; rod axis 10.5 mm from one 20 mm face
ACT_CLEVIS_D = 4.25          # both clevis holes, for M4 or #8-32 pins
TILT_MAX = 90.0

MAGNET_D, MAGNET_H = 6.35, 3.18

# --- top idlers: 35BS32 re-bored to 35 mm H7 for two 6202-2RS, on a fixed 15 mm axle stud ---
IDLER_BORE = 35.0
IDLER_AXLE_L = 31.0          # bearing seat from the shoulder (on the plate's inner face) to flush with the sprocket face
SPROCKET_FACE = TOOTH_W / 2  # tooth ring's inner face, x = +2.13 at the front chain: nothing on the axis goes further in

# --- jaw coupling, NEMA 34 (14 mm) to the 5/8 in drive shaft: Lovejoy L-075 class ---
CPL_OD, CPL_L = 53.6, 54.8   # L090 (two 6408K14 hubs + 6408K75 spider): the L075's spider is rated 10.2 N*m, under the motor's 12

# --- gondola details ---
BUSHING_OD = 7.0             # 6659K65 pressed into a 7.0 mm printed bore
HINGE_HOLE = 5.3
HINGE_PIN_GRIP = 62.0
SADDLE_XS = 190.0            # saddle under the auger tube, in Sam's x from the hinge
AUGER_R_TUBE = 12.5          # the auger's tube is 25 mm across (44T gear 46 mm)

# --- station geometry (Sam's studio frame at the station; actuator rod end pinned under his carriage) ---
# Carriage pivot at the carriage's centre-of-mass height (cad/gear-mesh/README.md). The P16 is pinned at both ends,
# so only the dock holds the carriage's attitude on the plate. With the old pin under the carriage at (40, -72) the
# carriage was an inverted pendulum (COM 39 mm above the pin) and fell off the plate once tilted, even unloaded.
# Now two 4 mm steel stub pins go through the carriage's solid side posts (x 29-37), and a U-yoke on the P16's rod
# end carries them, its 2 mm steel arms outside the carriage's |y| 18. The same station is used in chain carousel v2.
YOKE_X, YOKE_Z = 32.0, -34.0 # stub-pin axis, Sam's frame, carriage as drawn (docked it rises DOCK_RISE)
UFORK_L = 60.0               # stub-pin axis -> the P16's rod-end hole: the crossbar clears the carriage's front-bottom corner
UFORK_Y = (19.5, 21.5)       # the yoke's steel arms, |y|; printed boss on the post at |y| 18-19.5; e-clip outside
TONGUE_X, TONGUE_Y = YOKE_X, 15.0   # guide tongue under the yoke's crossbar, rides the approach fork
YOKE_STOP_Z = -11.0 - 0.3 - 4.0     # stop blocks on the arms (yoke frame z of the block's bottom): 0.3 mm under the pin plate's tail
DOCK_RISE = 0.9              # Sam's Part Studio leaves the carriage 0.9 mm under the plate; docked, they touch
ECLIP = (9.0, 0.6)           # DIN 6799 e-clip on each stub pin, outside the arm
LOCPIN_D, LOCPIN_PROUD = 4.0, 3.0    # steel dowels on the carriage rim into a hole and a slot in the plate
LOCPIN_XY = ((30.0, 16.0), (70.0, -16.0))
LOCPIN_HOLE, LOCPIN_SLOT = 4.2, 6.0
SEP_RATIO_STEEL = 0.55       # separating / tangential mesh force, steel pinion on the printed gear, dry PTFE lube
# Dock electromagnet behind the pinion pulls a steel tab on each plate (cad/gear-mesh): Adafruit 3872 P20/15
DOCK_MAG_D, DOCK_MAG_H = 20.0, 15.0
DOCK_MAG_XY = (99.5, 0.0)
DOCK_MAG_FACE_Z = -18.0 - 2.0 - 0.15 - DOCK_RISE  # -21.05 as drawn: 0.15 mm under the tab when docked
ARMATURE_X = (89.0, 111.0)   # 2 mm low-carbon steel tab under each plate's back strip, |y| <= 14
ARMATURE_HW, ARMATURE_T = 14.0, 2.0
ARMATURE_SCREWS = ((94.0, -10.0), (94.0, 10.0))   # M3 x 6 flat heads into M3 heat-set inserts in the plate
DOCK_EXT = 20.0              # actuator extension when the carriage meets the plate (approach = DOCK_EXT)
ACT_REAR = 8.0               # rear clevis hole -> body start
ACT_BODY_L = 175.0
ACT_ROD_D = 10.0
FORK_H = 36.0
VIAL_H = 61.0
LC_L = 80.0
VIAL_X = 30.0                # vial ahead of the docked carriage's front face (x 47.3); a D-funnel catches the stream

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
MODULE_LIFT = 22.0           # swap: lift the module so the auger clears the +y lug and the gear the rail...
MODULE_SLIDE = 70.0          # ...then slide it out sideways (+y) from the loading position
NEMA11_X, NEMA11_Z = 68.3, -33.15  # NEMA 11 face on the inner face of the carriage's 5 mm back wall (boss in Sam's pilot
                                   # recess, screws from outside), as drawn; docked its axis is 32.25 mm under
                                   # the auger's (20T:44T, m1): 0.18 mm backlash for printed-gear runout and the plate's
                                   # bending under the magnet (cad/gear-mesh); Sam's pilot sits at -33.0, so -0.15 mm
SOL_X, SOL_Z = 12.0, -24.0   # solenoid under the auger tube near the outlet, plunger up
STATION_RAIL_X = (VIAL_X, HINGE_X + YOKE_X)   # base cross rails under the vial post and the actuator
FORK_POST_Y = 45.0
VIAL_POST_Y = -120.0
VIAL_GAP = 32.0              # vial mouth below the gondolas' lowest point: clear of the docked electronics carriage
HALL_X = (130.0, 160.0)      # INDEX magnet (every gondola) and HOME magnet (gondola 1), under the -y rail
HALL_GAP = 3.0
_PIV0 = Z_BOT - R * math.cos(math.pi / N_TEETH) - SA1_C            # station pivot height (polygonal: f = 0.5)
_HINGE_W = _PIV0 + HINGE_Z
_TONGUE_BOT = YOKE_Z + DOCK_RISE - UFORK_L - 6.0 - 25.0            # docked tongue's bottom (Sam's z): under the crossbar
FORK_Z = _HINGE_W + _TONGUE_BOT - 1.0 - FORK_H                     # fork bottom; its top is 1 mm under the docked tongue
_BASE_PIN_Z = _HINGE_W + YOKE_Z + DOCK_RISE - (ACT_RETRACTED + DOCK_EXT + UFORK_L)   # P16 base pin (world z)
CLEVIS_H = _BASE_PIN_Z - (BASE_Z + EXT)                            # pin above the bracket's foot (foot on the station rail)
STATION_POST_H = FORK_Z + 12.0 - (BASE_Z + EXT)
VIAL_Z = _PIV0 + GON_Z0 - VIAL_GAP - VIAL_H                         # vial base
VIAL_POST_H = VIAL_Z - 3.0 - 12.7 - (BASE_Z + EXT)

# --- station chain hold-down strips (added after the MuJoCo station run: tilting lifts the chain) ---
# UHMW-PE bar over each chain's bottom run at the station, 0.5 mm above the link plates' top edge;
# the chain only touches it if the module's tilt tries to lift the pivot.
HOLD_STRIP = (10.0, 100.0, 12.0)    # x (across the chain), y (along the run), z: ends clear the 32T tooth tips by 2 mm
HOLD_GAP = 0.5
HOLD_Z0 = Z_BOT - R * math.cos(math.pi / N_TEETH) + PLATE_H / 2 + HOLD_GAP   # underside (span at its highest)
HOLD_BRACKET_Y = 38.0
FUNNEL = dict(top_d=36.0, spout_d=18.0, x_max=46.0, h=22.0)   # printed D-funnel on the vial: mouth cut flat at x = 46
