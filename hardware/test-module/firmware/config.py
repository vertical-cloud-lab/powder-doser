"""Easily-adjustable configuration for the powder-doser test rig.

Edit any of these values and re-upload via the MicroPico extension's
"Upload project to Pico" (or right-click → "Upload file to Pico" on
just `config.py`); a soft-reset (Ctrl+D in the terminal) picks up the
new values.

The default values match the hardware in `hardware/test-module/README.md`:
NEMA-11 11HS18-0674S stepper + Pololu Tic T500, JF-0530B 5 V solenoid +
DRV8871, 10 mm ERM coin + DRV2605L, and an HD-1810MG servo on the
dispensing axis, all driven from a single Raspberry Pi Pico W.
"""

# -----------------------------------------------------------------------
# Pin assignments (Pi Pico W GPIO numbers; must match the KiCad schematic).
#
# These all live on the Pico W's left-column header (GP0..GP15), which
# has the same pinout as the standard Pico.  The Pico W reuses
# GP23/GP24/GP25/GP29 for its on-board CYW43439 wireless module, so we
# intentionally stay below GP16 and the rig is firmware-compatible with
# both Pico and Pico W.
# -----------------------------------------------------------------------
PIN_I2C_SDA   = 0          # DRV2605L SDA (I2C0)
PIN_I2C_SCL   = 1          # DRV2605L SCL (I2C0)

# Pololu Tic T500 stepper controller over UART1 (TTL serial).
PIN_TIC_TX    = 4          # Pico UART1 TX -> Tic RX
PIN_TIC_RX    = 5          # Pico UART1 RX <- Tic TX
TIC_UART_ID   = 1          # RP2040 UART1 (TX=GP4, RX=GP5)
TIC_BAUD      = 9600       # match the Tic's "Serial / I2C / USB" baud
TIC_READ_TIMEOUT_MS = 50   # how long to wait for a get-variable reply

PIN_SOL_IN1   = 10         # DRV8871 IN1
PIN_SOL_IN2   = 11         # DRV8871 IN2

# A&D HR-100A balance via MAX3232 RS-232 transceiver on UART0.
# (UART0's second pin-mux site; GP0/GP1 are taken by I2C0.)
PIN_SCALE_TX  = 12         # Pico UART0 TX -> MAX3232 T1IN -> scale RXD
PIN_SCALE_RX  = 13         # Pico UART0 RX <- MAX3232 R1OUT <- scale TXD
SCALE_UART_ID = 0          # RP2040 UART0 (TX=GP12, RX=GP13)

PIN_HAPT_EN   = 14         # DRV2605L EN / IN_TRIG (tie high to enable)
PIN_SERVO_SIG = 15         # Servo PWM signal


# -----------------------------------------------------------------------
# Auger (stepper) configuration.
#
# The Tic T500 runs the step generation and motion planner internally; the
# Pico W just sends target positions over serial.  Set the Tic's *current
# limit* and "Control mode = Serial / I2C / USB" once with the Tic Control
# Center over USB (recommend the motor's rated 670 mA, never above the
# Tic T500's 1500 mA continuous limit); the firmware pushes the step mode,
# max speed, and acceleration below over serial on boot.  Disabling the
# Tic's "Command timeout" in the Control Center avoids the motor stopping
# mid-move during a long rotation.
# -----------------------------------------------------------------------
# Microstep resolution -- the Tic T500 (MP6500) supports 1, 2, 4, 8 only.
STEPPER_MICROSTEPS    = 8             # 1, 2, 4, 8
STEPPER_FULL_STEPS_REV = 200          # 1.8 deg/step NEMA-11
STEPPER_SPEED_RPM     = 60            # 5 .. 240 RPM is a safe range
STEPPER_ACCEL_REV_PER_S2 = 4.0        # auger accel/decel ramp (rev/s^2)
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
# Smooth-motion parameters.  Every angle command (a / p / SERVO_DEFAULT
# on boot) is interpolated from the current position to the target at
# SERVO_SPEED_DEG_PER_S deg/s with a 50 Hz update rate.  Lower speed =
# gentler motion and less powder spillage; higher = snappier response.
# Set SERVO_SPEED_DEG_PER_S to 0 to fall back to instantaneous "snap"
# moves (the pre-smoothing behaviour).
SERVO_SPEED_DEG_PER_S = 60            # 30..120 is a comfortable range
SERVO_UPDATE_HZ       = 50            # matches the servo's PWM frame
# Pre-canned positions exposed as CLI shortcuts:
SERVO_PRESETS = {
    "horizontal": 0,
    "tilt":       45,
    "vertical":   90,
    "tip":        135,
}


# -----------------------------------------------------------------------
# Scale (A&D HR-100A over RS-232C) configuration.
#
# The HR-A series factory default is 2400 baud / 7 data bits / even
# parity / 1 stop bit, A&D standard data format, terminator CR LF.
# If the balance's function settings (bASFnc) have been changed, mirror
# them here.  Parity: 0 = none, 1 = odd, 2 = even (config encoding; the
# UART constructors translate this to machine.UART's parity argument).
# -----------------------------------------------------------------------
SCALE_BAUD            = 2400
SCALE_BITS            = 7
SCALE_PARITY          = 2             # even
SCALE_STOP            = 1
SCALE_RESPONSE_TIMEOUT_MS = 1000      # max wait for one reply frame
SCALE_STABLE_TIMEOUT_MS   = 10000     # max wait for an ST (stable) frame


# -----------------------------------------------------------------------
# Closed-loop dosing (issue #99): coarse auger fill, fine tap trim.
# -----------------------------------------------------------------------
# Stop the auger at this fraction of the target mass and switch to
# solenoid taps.  0.90 leaves a 10 % band for the fine phase; lower it
# for free-flowing powders that keep streaming after the auger stops.
DOSE_COARSE_FRACTION  = 0.90
# ...but on multi-gram doses never leave more than this much (g) for
# the (slow) tap phase; whichever coarse stop is closer to the target
# wins.
DOSE_COARSE_HEADROOM_G = 0.05
# Largest single auger increment between scale readings (deg).
DOSE_COARSE_STEP_DEG  = 360.0
# Initial guess for auger throughput (grams per auger revolution).
# The dose loop measures the actual throughput from the scale after
# every increment and refines this online, so it only needs to be
# order-of-magnitude right; 0 disables the estimator (fixed steps).
DOSE_GRAMS_PER_REV    = 0.5
# Derating applied to DOSE_GRAMS_PER_REV for the *first* increment of a
# dose (before any scale feedback exists), in case the real powder runs
# denser than the configured guess.
DOSE_GPR_SAFETY       = 3.0
# Stop when |measured - target| <= tolerance (g).  The HR-100A resolves
# 0.1 mg, so the loop -- not the scale -- limits repeatability.
DOSE_TOLERANCE_G      = 0.005
# Solenoid taps fired per fine-phase burst (re-uses TAP_ON_MS/TAP_OFF_MS).
DOSE_TAPS_PER_BURST   = 2
# Give up if the fine phase needs more than this many taps in total.
DOSE_MAX_TAPS         = 200
# Wait after each actuation before trusting the scale (powder settles,
# draft shield stops swinging).  The HR-A needs ~1.5 s to stabilise.
DOSE_SETTLE_MS        = 1500
# If a coarse increment adds less than this (g), count it as a stall
# (empty hopper / jam); abort after DOSE_MAX_STALLS in a row.
DOSE_MIN_FLOW_G       = 0.001
DOSE_MAX_STALLS       = 5
# Hard wall-clock limit for one dose (s).
DOSE_TIMEOUT_S        = 600
# Fine-phase stall recovery: if this many tap bursts in a row each add
# less than DOSE_FINE_MIN_GAIN_G, the tube lip is empty -- nudge the
# auger DOSE_FINE_NUDGE_DEG to re-feed it, then resume tapping.
DOSE_FINE_STALL_BURSTS = 3
DOSE_FINE_MIN_GAIN_G   = 0.0002
DOSE_FINE_NUDGE_DEG    = 15.0
