"""Single source of truth for every dimension in the Powder Doser assembly.

All values are millimetres unless noted.  Section numbers (e.g. ``§3``) refer
to ``SPEC.md`` / the engineering-spec prompt that drives this package.  Keeping
the numbers here (and importing them everywhere else) means the parts and the
assembly can never disagree about a shared dimension.
"""

from types import SimpleNamespace

# --------------------------------------------------------------------------- #
# §1 Global layout / datums
# --------------------------------------------------------------------------- #
AUGER_AXIS_Z = 29.25          # auger bore centreline above the mounting-plate top
PLATE_TOP_Z = 0.0             # datum: top surface of the mounting plate at Z=0

# --------------------------------------------------------------------------- #
# §3 Auger (shared tube geometry)
# --------------------------------------------------------------------------- #
AUGER_OD = 25.0
AUGER_WALL = 2.0
AUGER_ID = AUGER_OD - 2 * AUGER_WALL          # = 21.0 bore
AUGER_R_OUT = AUGER_OD / 2.0                  # 12.5
AUGER_R_IN = AUGER_ID / 2.0                   # 10.5

AUGER_LEN_FULL = 250.0
AUGER_LEN_180 = 180.0
AUGER_LEN_SHORT = 90.0        # bench-test length (no gear band)

TOP_CAP_H = 6.0               # top loading cover height
TOP_SLOT_W = 4.0
TOP_SLOT_L = 7.0
TOP_SLOT_BC_R = 6.5           # bolt-circle radius for the 4 loading slots
TOP_SLOT_N = 4
TOP_PILOT = SimpleNamespace(d=2.7)   # central M3 pilot boss (self-tap pilot)

FUNNEL_H = 12.0               # bottom funnel / cap height
EXIT_HOLE_D = 3.0            # single axial exit hole

# Internal Archimedean screw
SHAFT_D = 8.0
SHAFT_R = SHAFT_D / 2.0       # 4.0
FIN_PITCH = 10.0             # mm per turn, single-start
FIN_THK = 2.0
FIN_SHAFT_OVERLAP = 0.4      # inner edge overlaps the shaft
FIN_WALL_OVERLAP = 0.2       # outer edge overlaps the inner tube wall
FIN_R_INNER = SHAFT_R - FIN_SHAFT_OVERLAP
FIN_R_OUTER = AUGER_R_IN + FIN_WALL_OVERLAP

# Storage variant: screw occupies only the bottom 1/3 of the length
STORAGE_SCREW_FRACTION = 1.0 / 3.0

# v4 nozzle tip
V4_TIP_R_BOTTOM = 0.4        # shaft radius at the very bottom of the tip
V4_TIP_CLEAR = 0.5           # helix stops ~0.5 mm above the exit plane

# --------------------------------------------------------------------------- #
# §3 / §4.1 Gears (module 1.0 drive train, 20deg pressure angle)
# --------------------------------------------------------------------------- #
PRESSURE_ANGLE = 20.0
BACKLASH = 0.15               # ~0.15 mm backlash at pitch for printed teeth

# 48T auger drive band
AUGER_GEAR = SimpleNamespace(teeth=48, module=1.0, face=10.0)
AUGER_GEAR_TIP_D = 50.0
AUGER_GEAR_ROOT_D = 45.5
AUGER_GEAR_PITCH_D = 48.0
# band centre = length / 3 from the dispense (+Y) end
AUGER_GEAR_CENTRE_FROM_TIP = AUGER_LEN_FULL / 3.0   # 83.33

# 16T stepper pinion (NEMA 11)
STEPPER_PINION = SimpleNamespace(teeth=16, module=1.0, face=10.0)
STEPPER_PINION_TIP_D = 18.0
STEPPER_PINION_ROOT_D = 13.5
STEPPER_PINION_PITCH_D = 16.0
STEPPER_CENTRE_DIST = 32.0    # C between pinion and auger band, 3:1
STEPPER_BORE_D = 5.0
STEPPER_BORE_SLIP = 0.2       # radial slip-fit -> +0.4 diametral
STEPPER_HUB_D = 9.0
STEPPER_HUB_H = 6.0           # hub rises above the gear face
STEPPER_SETSCREW_PILOT = 2.5  # M3 setscrew pilot
STEPPER_SETSCREW_Z = 3.0      # axis above the gear face

# 20T servo pinion (MG996R), module ~0.9083, 2:1 onto the 40T hinge gear
HINGE_MODULE = 0.9083
SERVO_PINION = SimpleNamespace(teeth=20, module=HINGE_MODULE, face=8.0)
SERVO_PINION_TIP_D = 20.2
SERVO_PINION_PITCH_D = 18.2
SERVO_PINION_BORE_D = 6.0     # MG996R 25T spline + chordal flat
SERVO_SPLINE_FLAT = 5.5       # chordal flat depth across the bore (approx)
SERVO_HORN_SCREW = SimpleNamespace(d=3.4, cs_d=6.0)   # M3 countersink
SERVO_CENTRE_DIST = 27.25     # C between servo pinion and hinge gear

# 40T hinge gear band (one per side, on the outer mounting-plate lobe)
HINGE_GEAR = SimpleNamespace(teeth=40, module=HINGE_MODULE)
HINGE_GEAR_PITCH_D = 36.33
HINGE_GEAR_TIP_D = 38.15

# --------------------------------------------------------------------------- #
# §4.2 Mounting plate ("the table")
# --------------------------------------------------------------------------- #
PLATE_THK = 6.0
PLATE_X = 54.1                # half-width (+/-)
PLATE_Y_MIN = -15.0
PLATE_Y_MAX = 115.0
PLATE_NOTCH_W = 32.0          # open U-notch in the +Y edge
PLATE_NOTCH_FROM_FRONT = 35.0  # notch starts 35 mm back from the front edge
BRACKET_LIFT = 14.0          # bracket flange thickness that lifts the bore axis

# --------------------------------------------------------------------------- #
# §4.3 Baseplate (fixed forward tab)
# --------------------------------------------------------------------------- #
BASE_THK = 6.0
BASE_X = 100.0               # half-width (+/-) -> 200 wide
BASE_Y_MIN = 55.0
BASE_Y_MAX = 115.0
BASE_BOTTOM_Z = -14.0        # baseplate bottom
BASE_CHAMFER = 25.0          # rear corner chamfer (x45deg)
BASE_HOLE_D = 5.4            # M5 clearance
BASE_HOLE_X = 80.0
BASE_HOLE_Y = (68.0, 105.0)

# --------------------------------------------------------------------------- #
# §4.4 Hinge
# --------------------------------------------------------------------------- #
HINGE_AXIS_Z = 29.25
HINGE_AXIS_FWD = 10.0        # 10 mm forward of the baseplate front edge
HINGE_AXIS_Y = BASE_Y_MAX + HINGE_AXIS_FWD   # 125
HINGE_EYE_OD = 18.0
HINGE_PIN_D = 5.0            # M5 pin nominal
HINGE_BORE_D = 5.4          # M5 clearance
HINGE_LAYER_GAP = 0.4
HINGE_ARM_DEPTH = 35.0       # reduced so it clears the front bracket
HINGE_LOBE_W = 6.0           # nominal hinge-lobe / layer width (each of 3 layers)
HINGE_ARM_X = 48.0           # X centre of each hinge sandwich (one per side)

# --------------------------------------------------------------------------- #
# §4.5 Servos (dual MG996R)
# --------------------------------------------------------------------------- #
MG996R = SimpleNamespace(
    body_y=40.0, body_z=20.0, body_x=36.8,
    flange_tip=54.5, ear_thk=2.0,
    hole_d=5.0, hole_span_y=49.5, hole_span_z=10.0,
    spline_offset=10.1, spline_z_above_base=10.0,
)
SERVO_POST = SimpleNamespace(size=10.0)       # square post side
SERVO_POST_INBOARD_X = 63.0
SERVO_BODY_X_OUTER = 95.8
SERVO_FLANGE_X = 79.0
SERVO_FLANGE_LEN = 40.0     # rib length along X (inboard edge stays clear of plate)
SERVO_FLANGE_DROP = 40.0      # below baseplate bottom
SERVO_FLANGE_THK = 6.0
SERVO_GUSSET = SimpleNamespace(thk=10.0, run=20.0)
SERVO_FLANGE_HOLE_D = 5.4     # M5 side-bolt through the gusset
SERVO_FLANGE_HOLE_DROP = 15.0  # below baseplate bottom

# --------------------------------------------------------------------------- #
# §4.6 NEMA 11 motor block
# --------------------------------------------------------------------------- #
MOTOR_BLOCK = SimpleNamespace(x=32.0, size=36.2, thk=6.0)
NEMA11 = SimpleNamespace(
    body=28.0, length=32.0,
    shaft_d=5.0, shaft_len=18.0,
    pilot_d=22.0, pilot_h=2.0,
    hole_pat=23.0, hole_d=3.4,   # we clear the M2.5 pattern with M3
)

# --------------------------------------------------------------------------- #
# §4.7 Auger brackets (split shaft-collar style)
# --------------------------------------------------------------------------- #
BRACKET = SimpleNamespace(
    flange_x=60.0, flange_y=12.0, flange_z=14.0,
    hole_x=24.0, hole_d=3.4,
    collar_od=33.5, slot_w=2.0,
)
BRACKET_BORE_D = AUGER_OD + 0.5      # running fit on the auger OD
BRACKET_PACK_GAP = 1.0               # air gap packed along Y

# --------------------------------------------------------------------------- #
# §4.7 / §8 Tap collar + mount plate
# --------------------------------------------------------------------------- #
COLLAR = SimpleNamespace(
    od=33.5, depth=17.0, slot_w=2.0,
    bore_d=AUGER_OD + 0.5,           # 25.5 running fit
    coin_pad_d=10.0, coin_recess=1.0,
    solenoid_bushing_d=6.9, solenoid_bore_d=7.5,
    solenoid_hole_pitch_x=18.2, solenoid_hole_pitch_y=16.0,
    m3_hole_d=3.4,
)

# §5.4 tap solenoid (Adafruit 412 / TAU0730TM)
SOLENOID = SimpleNamespace(
    body_x=30.0, body_y=15.5, body_z=16.0,
    bushing_d=6.9, plunger_bore_d=7.5,
    interference=3.0,            # plunger tip reaches 3 mm inside the auger OD
)

# --------------------------------------------------------------------------- #
# §7 Tolerances / fastener pilots
# --------------------------------------------------------------------------- #
M3_CLEAR = 3.4
M3_PILOT = 2.7
M3_SETSCREW_PILOT = 2.5
M5_CLEAR = 5.4
THREAD_CLEAR = 0.35           # printed thread hand fit

# --------------------------------------------------------------------------- #
# §3 Threaded sealable variant + cap
# --------------------------------------------------------------------------- #
THREAD = SimpleNamespace(
    length=25.4,              # 1 inch on the top of the tube
    pitch=4.0,
    depth=1.0,
    major_r=12.5,             # crest flush with the tube OD
    minor_r=11.5,
    half_angle=58.0,
)
CAP = SimpleNamespace(
    wall=3.0, top=3.0, clearance_above=3.0,
    chamfer=1.5,
    clear=THREAD_CLEAR,
)
