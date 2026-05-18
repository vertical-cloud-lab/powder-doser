"""Easily-adjustable configuration for the powder-doser test rig.

Edit any of these values, save the file, and the Pico will reload the
firmware automatically.  All values are documented in the header next
to each block — typical / safe ranges are in the comments.

The default values match the hardware in `hardware/test-module/README.md`:
NEMA-11 11HS18-0674S stepper + DRV8825, JF-0530B 5 V solenoid + DRV8871,
10 mm ERM coin + DRV2605L, and an HD-1810MG servo on the dispensing
axis.
"""

# -----------------------------------------------------------------------
# Pin assignments (Pi Pico GPIO numbers; must match the KiCad schematic).
# -----------------------------------------------------------------------
PIN_I2C_SDA   = 0          # DRV2605L SDA (I2C0)
PIN_I2C_SCL   = 1          # DRV2605L SCL (I2C0)

PIN_STEP      = 2          # DRV8825 STEP
PIN_DIR       = 3          # DRV8825 DIR
PIN_STEPPER_EN = 4         # DRV8825 ~ENABLE (active low)
PIN_M0        = 5          # DRV8825 microstep select
PIN_M1        = 6
PIN_M2        = 7

PIN_SOL_IN1   = 10         # DRV8871 IN1
PIN_SOL_IN2   = 11         # DRV8871 IN2

PIN_HAPT_EN   = 14         # DRV2605L EN / IN_TRIG (tie high to enable)
PIN_SERVO_SIG = 15         # Servo PWM signal


# -----------------------------------------------------------------------
# Auger (stepper) configuration.
# -----------------------------------------------------------------------
# Microstep resolution -- DRV8825 M2/M1/M0 truth table:
#   (0,0,0)=full, (0,0,1)=1/2, (0,1,0)=1/4, (0,1,1)=1/8,
#   (1,0,0)=1/16, (1,0,1)..(1,1,1)=1/32.
STEPPER_MICROSTEPS    = 16            # 1, 2, 4, 8, 16, 32
STEPPER_FULL_STEPS_REV = 200          # 1.8 deg/step NEMA-11
STEPPER_SPEED_RPM     = 60            # 5 .. 240 RPM is a safe range
STEPPER_DIRECTION     = 1             # +1 = CW from motor face, -1 = CCW
# Per-shot dispense in degrees of auger rotation; the test CLI will run
# this on the "dispense" command.  Keep small for incremental dosing.
STEPPER_DISPENSE_DEG  = 360.0


# -----------------------------------------------------------------------
# Vibration (DRV2605L + ERM/LRA) configuration.
# -----------------------------------------------------------------------
# Effect ID from the DRV2605L's built-in ROM library (1..123).  See
# Adafruit's "Haptic Motor Driver" guide for the catalog.  Useful picks:
#   1   = strong click 100%
#   14  = strong buzz 100%
#   47  = long buzz no.1 5s
#   84  = long sharp buzz no.2 (continuous)
VIBRATION_EFFECT_ID   = 14
VIBRATION_LIBRARY     = 1             # 1 = ERM A, 6 = LRA
VIBRATION_DURATION_S  = 0.6           # how long to hold the buzz


# -----------------------------------------------------------------------
# Tap (solenoid) configuration.
# -----------------------------------------------------------------------
TAP_COUNT             = 3             # number of taps per "tap" command
TAP_ON_MS             = 60            # coil energised, must be << 100 % duty
TAP_OFF_MS            = 150           # quiet gap between taps
TAP_PWM_DUTY          = 1.0           # 0.0 .. 1.0 -- holding force (PWM)


# -----------------------------------------------------------------------
# Dispensing-angle (servo) configuration.
# -----------------------------------------------------------------------
SERVO_MIN_PULSE_US    = 500           # HD-1810MG: 500..2400 us
SERVO_MAX_PULSE_US    = 2400
SERVO_MIN_ANGLE_DEG   = 0             # mechanical min
SERVO_MAX_ANGLE_DEG   = 180
SERVO_DEFAULT_DEG     = 90            # home position on boot
# Pre-canned positions exposed as CLI shortcuts:
SERVO_PRESETS = {
    "horizontal": 0,
    "tilt":       45,
    "vertical":   90,
    "tip":        135,
}
