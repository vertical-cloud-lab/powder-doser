"""Build the real accessory hardware on the Pico 2 W (MicroPython only).

A missing I2C sensor is reported in the boot event (`missing`) and its
commands answer with an error, so the accessory still runs the parts that
are connected.
"""

from machine import I2C, PWM, Pin, UART

import actuators
import sensors
import tic


class Hardware:
    pass


def _pwm(pin, freq, duty=0):
    p = PWM(Pin(pin))
    p.freq(freq)
    p.duty_u16(duty)
    return p


def build(cfg, clock):
    hw = Hardware()
    hw.missing = []
    hw.i2c = I2C(cfg.I2C_ID, sda=Pin(cfg.PIN_I2C_SDA), scl=Pin(cfg.PIN_I2C_SCL),
                 freq=cfg.I2C_FREQ)
    found = hw.i2c.scan()

    def opt(name, addr, ctor):
        if addr not in found:
            hw.missing.append(name)
            return None
        try:
            return ctor()
        except Exception as exc:  # noqa: BLE001 - keep booting without it
            hw.missing.append("{} ({})".format(name, exc))
            return None

    hw.lc = opt("NAU7802", cfg.ADDR_NAU7802, lambda: sensors.NAU7802(
        hw.i2c, clock, cfg.ADDR_NAU7802, cfg.NAU_GAIN, cfg.NAU_RATE_SPS))
    hw.imu = opt("LSM6DSOX", cfg.ADDR_LSM6DSOX, lambda: sensors.LSM6DSOX(
        hw.i2c, clock, cfg.ADDR_LSM6DSOX, cfg.IMU_ODR_HZ, cfg.IMU_ACCEL_FS_G, cfg.IMU_GYRO_FS_DPS))
    hw.env = opt("SHT45", cfg.ADDR_SHT45, lambda: sensors.SHT45(hw.i2c, clock, cfg.ADDR_SHT45))
    hw.adc = opt("ADS1115", cfg.ADDR_ADS1115, lambda: sensors.ADS1115(
        hw.i2c, clock, cfg.ADDR_ADS1115, cfg.ADS_FSR_V, cfg.ADS_RATE_SPS))

    # Servos get no pulses until their first command (duty 0).
    hw.servo_a = actuators.Servo(_pwm(cfg.PIN_SERVO_A, 50), cfg.SERVO_A_MIN_US, cfg.SERVO_A_MAX_US,
                                 cfg.SERVO_A_MIN_DEG, cfg.SERVO_A_MAX_DEG, cfg.SERVO_A_REST_DEG,
                                 cfg.SERVO_PERIOD_US)
    hw.servo_b = actuators.Servo(_pwm(cfg.PIN_SERVO_B, 50), cfg.SERVO_B_MIN_US, cfg.SERVO_B_MAX_US,
                                 cfg.SERVO_B_MIN_DEG, cfg.SERVO_B_MAX_DEG, cfg.SERVO_B_REST_DEG,
                                 cfg.SERVO_PERIOD_US)
    hw.tapper = actuators.Tapper(_pwm(cfg.PIN_TAP_IN1, cfg.TAP_PWM_HZ),
                                 Pin(cfg.PIN_TAP_IN2, Pin.OUT, value=0), cfg.TAP_DUTY)
    hw.relay = Pin(cfg.PIN_Q_RESET, Pin.OUT, value=cfg.Q_RESET_ACTIVE)
    hw.aux = Pin(cfg.PIN_AUX_IN, Pin.IN, Pin.PULL_UP)
    hw.light = actuators.Light(_pwm(cfg.PIN_LIGHT, cfg.LIGHT_PWM_HZ))
    try:
        uart = UART(cfg.TIC_UART_ID, baudrate=cfg.TIC_BAUD, tx=Pin(cfg.PIN_TIC_TX),
                    rx=Pin(cfg.PIN_TIC_RX), timeout=cfg.TIC_READ_TIMEOUT_MS)
        hw.motor = actuators.TicMotor(tic.TicSerial(uart), clock, cfg.MOTOR_PROFILE,
                                      cfg.MOTOR_PROFILES[cfg.MOTOR_PROFILE], cfg.TIC_SET_CURRENT)
    except Exception as exc:  # noqa: BLE001
        hw.missing.append("Tic ({})".format(exc))
        hw.motor = None
    return hw
