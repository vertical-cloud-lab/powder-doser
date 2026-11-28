"""Accessory Pico 2 W configuration (in-house powder tests).

Pins follow SPEC.md section 0.2. Edit values here, re-upload, soft-reset.
Every number that is a design choice rather than a datasheet value says so.
"""

FIRMWARE = "accessory 0.1.0 (2026-11-28)"

# ---------------------------------------------------------------------------
# Pins (Pico 2 W GPIO numbers; SPEC 0.2)
# ---------------------------------------------------------------------------
PIN_I2C_SDA = 0          # I2C0 SDA, STEMMA QT chain
PIN_I2C_SCL = 1          # I2C0 SCL
I2C_ID = 0
I2C_FREQ = 400_000

PIN_TIC_TX = 4           # UART1 TX -> Tic RX
PIN_TIC_RX = 5           # UART1 RX <- Tic TX (wire it: position read-back)
TIC_UART_ID = 1
TIC_BAUD = 9600          # must match the Tic's serial baud (Tic Control Center)
TIC_READ_TIMEOUT_MS = 20

PIN_SERVO_A = 6          # orifice gate (9 g metal-gear micro servo)
PIN_SERVO_B = 7          # tilt table (20 kg.cm servo, 1:2 gear to the table)
PIN_TAP_IN1 = 8          # DRV8871 #2 IN1 (PWM)
PIN_TAP_IN2 = 9          # DRV8871 #2 IN2 (held low)
PIN_Q_RESET = 10         # reed relay driver for the charge amplifier (high = closed = C_f shorted)
PIN_AUX_IN = 11          # stage profile: home limit switch; cam profile: TCRT5000 index
PIN_LIGHT = 12           # backlight MOSFET gate (PWM)
PIN_SPARE_ADC = 26       # ADC0, spare

# ---------------------------------------------------------------------------
# Hobby servos (50 Hz PWM). The 1:2 spur pair halves the table angle:
# table deg = servo deg / 2 (SPEC 3).
# ---------------------------------------------------------------------------
SERVO_PERIOD_US = 20_000
SERVO_UPDATE_MS = 20                 # ramp update interval (50 Hz)

SERVO_A_MIN_US, SERVO_A_MAX_US = 500, 2500   # 9 g MG90S-class: check yours
SERVO_A_MIN_DEG, SERVO_A_MAX_DEG = 0, 180
GATE_CLOSED_DEG = 20                 # servo deg with the slide covering the orifice (set on the bench)
GATE_OPEN_DEG = 110                  # servo deg with the slide 10 mm clear (set on the bench)
GATE_SPEED_DEG_S = 180               # eased ramp; about 0.5 s for the full stroke

SERVO_B_MIN_US, SERVO_B_MAX_US = 500, 2500   # DS3218-class 20 kg.cm: check yours
SERVO_B_MIN_DEG, SERVO_B_MAX_DEG = 0, 180
TABLE_GEAR = 2.0                     # servo deg per table deg
TABLE_ZERO_SERVO_DEG = 0.0           # servo deg at which the table sits level (set on the bench)
TABLE_MAX_DEG = 85.0                 # software limit, table deg
TABLE_DEFAULT_RATE = 5.0             # table deg/s for moves without rate=
TABLE_MAX_RATE = 30.0

# Servos are not driven at boot. The first command ramps from these
# assumed rest positions (gate shut, table on its level stop).
SERVO_A_REST_DEG = GATE_CLOSED_DEG
SERVO_B_REST_DEG = TABLE_ZERO_SERVO_DEG

# ---------------------------------------------------------------------------
# Accessory stepper on a Pololu Tic T500 (one motor connected at a time).
# MOTOR_PROFILE picks the default; `motor cam|stage` switches when idle.
# ---------------------------------------------------------------------------
MOTOR_PROFILE = "cam"
TIC_SET_CURRENT = True        # push current_ma (as a T500 code, rounded down) on profile select
TIC_KEEPALIVE_MS = 500        # reset the Tic's command timeout while moving

MOTOR_PROFILES = {
    # NEMA 11 (11HS18-0674S class, 0.67 A) turning the 2-lobe snail cam of
    # the tap-density tapper: 1 turn = 2 drops of 3.0 mm; 250 taps/min = 125 rpm.
    "cam": {
        "full_steps": 200,
        "microsteps": 8,
        "current_ma": 670,
        "lobes": 2,
        "max_rpm": 240,
        "accel_rev_s2": 20.0,
        "dir": 1,
        "default_tap_rate": 250.0,    # taps/min (USP <616> method 2 / ASTM B527)
        "home_rpm": 20.0,
        "index_active": 0,            # TCRT5000 module output is low over the flag
    },
    # NEMA 17 on the universal 100 mm stage (T8 lead screw, 8 mm lead):
    # 1/8 microstep = 8 / 1600 = 0.005 mm per microstep (SPEC 0.3).
    "stage": {
        "full_steps": 200,
        "microsteps": 8,
        "current_ma": 1000,
        "lead_mm": 8.0,
        "stroke_mm": 100.0,
        "min_mm_s": 0.01,
        "max_mm_s": 100.0,
        "default_mm_s": 5.0,
        "accel_mm_s2": 200.0,
        "dir": 1,
        "home_dir": -1,               # toward the switch
        "home_mm_s": 5.0,
        "home_slow_mm_s": 0.5,
        "home_backoff_mm": 2.0,
        "home_park_mm": 1.0,
        "home_max_mm": 110.0,         # give up if no switch within this travel
        "limit_active": 0,            # NO switch to GND with pull-up: pressed = 0
    },
}

# ---------------------------------------------------------------------------
# DRV8871 #2 tapper (JF-0530B solenoid on the orifice-cup holder)
# ---------------------------------------------------------------------------
TAP_PWM_HZ = 20_000
TAP_DUTY = 1.0
TAP_ON_MS = 30
TAP_DEFAULT_RATE = 60.0       # taps/min
TAP_MAX_ONTIME = 0.25         # coil on-time fraction limit; faster rates are refused

# ---------------------------------------------------------------------------
# Charge amplifier (test 10): reed relay across C_f, ADS1115 differential
# AIN0-AIN1. Inverting integrator: Q = -C_f * V_out.
# ---------------------------------------------------------------------------
Q_RESET_ACTIVE = 1            # GPIO level that closes the relay
Q_ZERO_MS = 500               # default relay closure for `q zero`
Q_CF_NF = 10.0                # 10 or 100 nF, set to match the fitted C_f
Q_SIGN = -1                   # charge = Q_SIGN * C_f * V_out
ADS_FSR_V = 4.096             # +-24 nC on 10 nF is +-2.4 V
ADS_RATE_SPS = 128

# ---------------------------------------------------------------------------
# I2C sensors (SPEC 0.2): no address clashes
# ---------------------------------------------------------------------------
ADDR_NAU7802 = 0x2A
ADDR_LSM6DSOX = 0x6A
ADDR_SHT45 = 0x44
ADDR_ADS1115 = 0x48

NAU_GAIN = 128
NAU_RATE_SPS = 80
LC_COUNTS_PER_G = 21500.0     # starting guess for a 100 g TAL221 at 1 mV/V; run `lc cal`

IMU_ODR_HZ = 104
IMU_ACCEL_FS_G = 2
IMU_GYRO_FS_DPS = 250
IMU_TILT_AXIS = "x"           # sensor axis that points down the slope of the plate
IMU_TILT_SIGN = 1
IMU_AVG = 8                   # samples averaged per reported angle
IMU_SAMPLE_MS = 10            # internal sampling while a stream or ramp runs
IMU_BIAS_G = (0.0, 0.0, 0.0)  # accelerometer zero-g offsets (6-position calibration)
JOLT_ALPHA = 0.05             # EMA factor for the jolt (high-pass) metric

# ---------------------------------------------------------------------------
# Backlight
# ---------------------------------------------------------------------------
LIGHT_PWM_HZ = 20_000         # above any rolling-shutter banding
LIGHT_DEFAULT = 100           # percent for `light on`

# ---------------------------------------------------------------------------
# Streams and housekeeping
# ---------------------------------------------------------------------------
STREAM_MAX_HZ = 100
CAL_FILE = "cal.json"
