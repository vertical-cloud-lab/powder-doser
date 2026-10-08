"""Shared parametric dimensions for the Powder Doser assembly.

Every value is transcribed from ``SPEC.md`` (the standalone assembly prompt,
issue #106).  All lengths are millimetres, all angles degrees unless noted.

The module is intentionally free of any CAD-library import so it can be read,
diffed and unit-tested on its own.
"""

# --------------------------------------------------------------------------
# 0. Global tolerances & fastener sizes (SPEC §7, §5.10)
# --------------------------------------------------------------------------
M3_CLEAR = 3.4        # M3 clearance hole
M3_PILOT = 2.7        # M3 self-tap pilot
M3_SET_PILOT = 2.5    # M3 setscrew (grub) pilot
M5_CLEAR = 5.4        # M5 clearance hole

PINION_SLIP = 0.20    # +0.2 mm radial slip fit (pinion bore on Ø5 shaft)
RUN_FIT = 0.50        # +0.5 mm diametral running fit (collar/bracket bore)
THREAD_FIT = 0.35     # +0.35 mm hand-fit clearance for printed threads
GEAR_BACKLASH = 0.15  # ~0.15 mm backlash at pitch line for printed teeth

EPS = 0.4             # union overlap to stay manifold (0.2-0.4 mm, §7)

# --------------------------------------------------------------------------
# 1. Global layout (SPEC §1)
# --------------------------------------------------------------------------
AUGER_AXIS_Z = 29.25  # auger bore centreline above the mounting-plate top
HINGE_Z = 29.25       # hinge axis height (same as auger axis)

# --------------------------------------------------------------------------
# 2. Auger shared tube geometry (SPEC §3)
# --------------------------------------------------------------------------
AUGER_OD = 25.0
AUGER_WALL = 2.0
AUGER_BORE_ID = AUGER_OD - 2 * AUGER_WALL          # 21.0
AUGER_OR = AUGER_OD / 2.0                           # 12.5
AUGER_IR = AUGER_BORE_ID / 2.0                      # 10.5

AUGER_LEN_FULL = 250.0
AUGER_LEN_180 = 180.0
AUGER_LEN_SHORT = 90.0

TOP_CAP_H = 6.0
SLOT_W = 4.0          # loading slot width
SLOT_L = 7.0          # loading slot length
SLOT_BC_R = 6.5       # slot bolt-circle radius
N_SLOTS = 4

FUNNEL_H = 12.0       # bottom funnel / cap height
EXIT_HOLE_D = 3.0     # exit hole diameter
EXIT_HOLE_R = EXIT_HOLE_D / 2.0

# Internal Archimedean screw
SHAFT_D = 8.0
SHAFT_R = SHAFT_D / 2.0                              # 4.0
HELIX_PITCH = 10.0    # mm / turn
FIN_THICK = 2.0
FIN_INNER_OVERLAP = 0.4   # fin overlaps shaft
FIN_OUTER_OVERLAP = 0.2   # fin overlaps inner wall

# v4 nozzle tip
V4_TIP_BOTTOM_R = 0.4     # cone tip radius at the bottom

# External 48T drive gear band (SPEC §3 / §4)
BAND_MODULE = 1.0
BAND_TEETH = 48
BAND_PA = 20.0
BAND_FACE = 10.0
BAND_CENTRE_FROM_TIP = AUGER_LEN_FULL / 3.0         # 83.33 from dispense end

# Threaded sealable variant + cap (SPEC §3)
THREAD_LEN = 25.4         # 1 inch
THREAD_PITCH = 4.0
THREAD_DEPTH = 1.0
THREAD_CREST_R = 12.5     # major radius flush with OD
THREAD_ROOT_R = 11.5      # minor radius
THREAD_HALF_ANGLE = 58.0  # tooth half-angle (deg)

CAP_WALL = 3.0
CAP_TOP = 3.0
CAP_CLEAR_ABOVE = 3.0     # clearance above engaged threads
CAP_CHAMFER = 1.5         # 1.5 x 45 chamfer on top outer edge

# --------------------------------------------------------------------------
# 3. Stepper pinion (SPEC §4.1)
# --------------------------------------------------------------------------
PINION_MODULE = 1.0
PINION_TEETH = 16
PINION_PA = 20.0
PINION_FACE = 10.0
PINION_BORE_D = 5.0 + 2 * PINION_SLIP   # Ø5 + 0.2 radial -> 5.4 diametral
PINION_HUB_D = 9.0
PINION_HUB_RISE = 6.0                   # hub rises 6 above gear face
PINION_SET_Z = 3.0                      # setscrew axis above gear face
CENTRE_DIST_DRIVE = 32.0                # pinion<->auger band centre distance

# --------------------------------------------------------------------------
# 4. Mounting plate "the table" (SPEC §4.2)
# --------------------------------------------------------------------------
PLATE_THICK = 6.0
PLATE_X = 54.1                          # half-width (+/-)
PLATE_Y_MIN = -15.0
PLATE_Y_MAX = 115.0
PLATE_UNOTCH_W = 32.0                   # U-notch width in +Y edge
PLATE_UNOTCH_DEPTH = 35.0               # notch starts 35 mm back from front
BRACKET_LIFT = 14.0                     # bracket thickness that lifts the axis

# Hinge gear bands on the plate (SPEC §4.2)
HINGE_GEAR_MODULE = 0.9083
HINGE_GEAR_TEETH = 40
HINGE_GEAR_PA = 20.0
HINGE_LOBE_OD = 18.0                    # hinge eye OD

# --------------------------------------------------------------------------
# 5. Baseplate (SPEC §4.3)
# --------------------------------------------------------------------------
BASE_THICK = 6.0
BASE_X = 100.0                          # +/- (200 wide)
BASE_Y_MIN = 55.0
BASE_Y_MAX = 115.0
BASE_BOTTOM_Z = -14.0
BASE_CHAMFER = 25.0                     # rear-corner 25 x 45 chamfer
BASE_HOLE_X = 80.0                      # M5 mount holes +/-X
BASE_HOLE_Y = (68.0, 105.0)

# Hinge (SPEC §4.4)
HINGE_AXIS_FWD = 10.0                   # forward of baseplate front edge
HINGE_LAYER_GAP = 0.4
HINGE_ARM_DEPTH = 35.0
HINGE_Y = BASE_Y_MAX + HINGE_AXIS_FWD   # 125: tilt axis 10 mm forward of front edge

# --------------------------------------------------------------------------
# 6. Servo pinion + servos (SPEC §4.5)
# --------------------------------------------------------------------------
SERVO_PINION_MODULE = 0.9083
SERVO_PINION_TEETH = 20
SERVO_PINION_PA = 20.0
SERVO_CENTRE_DIST = 27.25               # servo pinion <-> hinge gear (2:1)
SERVO_PINION_BORE_D = 6.0               # +chordal flat (MG996R 25T spline)
SERVO_SPLINE_Z = 10.0                   # spline axis above baseplate top

# MG996R envelope (SPEC §4.5 / §5.3)
MG_BODY_Y = 40.0
MG_BODY_Z = 20.0
MG_BODY_X = 36.8                        # inward from flange face
MG_FLANGE_TIP = 54.5
MG_EAR_THICK = 2.0
MG_HOLE_Y = 49.5
MG_HOLE_Z = 10.0
MG_SPLINE_OFFSET = 10.1                 # from near body end
SERVO_POST_X_IN = 59.0                  # +X post inboard faces at X=+/-59
SERVO_BODY_X_OUT = 95.8
SERVO_OVERHANG = 5.0                    # head overhangs porch front by 5

# Underside flange / gusset (SPEC §4.5)
FLANGE_X = 79.0
FLANGE_THICK = 6.0
FLANGE_DROP = 40.0                      # below baseplate bottom
GUSSET_THICK = 10.0
GUSSET_RUN = 20.0
FLANGE_BOLT_Z_BELOW = 15.0              # M5 hole 15 below baseplate bottom

# NEMA 11 motor block (SPEC §4.6 / §5.1)
MOTOR_BLOCK_X = 32.0                    # boss centred at X=+32 (gear centre)
MOTOR_BLOCK_FOOT = 36.2
MOTOR_BLOCK_THICK = 6.0
NEMA11_BODY = 28.0
NEMA11_LEN = 32.0
NEMA11_SHAFT_D = 5.0
NEMA11_SHAFT_LEN = 18.0
NEMA11_PILOT_D = 22.0
NEMA11_PILOT_H = 2.0
NEMA11_HOLE_PITCH = 23.0                # M2.5 face holes square pattern

# --------------------------------------------------------------------------
# 7. Auger brackets (SPEC §4.7)
# --------------------------------------------------------------------------
BRK_FLANGE_X = 60.0
BRK_FLANGE_Y = 12.0
BRK_FLANGE_Z = 14.0
BRK_HOLE_X = 24.0                       # 2 x M3 at X=+/-24
BRK_COLLAR_OD = 33.5
BRK_BORE_D = AUGER_OD + RUN_FIT         # 25.5 running fit
BRK_SLOT_W = 2.0                        # clamp slot width
PACK_GAP = 1.0                          # 1 mm air-gap pack between Y parts

# --------------------------------------------------------------------------
# 8. Tap collar (SPEC §4.7 / §8) + mount plate
# --------------------------------------------------------------------------
COLLAR_OD = 33.5
COLLAR_BORE_D = AUGER_OD + RUN_FIT      # 25.5
COLLAR_DEPTH = 17.0                     # along auger axis (Y)
COLLAR_SLOT_W = 2.0                     # clamp slot
COIN_PAD_D = 10.0                       # coin motor pad on -X
COIN_RECESS_DEPTH = 1.0                 # adhesive pocket
SOL_BUSHING_D = 6.9
SOL_PLUNGER_BORE_D = 7.5                # plunger clearance bore
SOL_HOLE_PITCH_X = 18.2                 # solenoid M3 pattern across body
SOL_HOLE_PITCH_Y = 16.0                 # solenoid M3 pattern along body
SOL_BODY_X = 30.0                       # solenoid body along plunger (X)
SOL_BODY_Y = 15.5
SOL_BODY_Z = 16.0
SOL_TIP_INTO_OD = 3.0                   # deliberate interference (tip into OD)
HARDSTOP_EAR_W = 8.0
HARDSTOP_EAR_H = 8.0

# Tap-collar mount plate
TC_MOUNT_THICK = 6.0
TC_MOUNT_LIFT = BRACKET_LIFT            # lift collar bore to AUGER_AXIS_Z

# --------------------------------------------------------------------------
# 9. Hinge pin (SPEC §4.4)
# --------------------------------------------------------------------------
HINGE_PIN_D = 5.0                       # M5
HINGE_PIN_LEN = 40.0
