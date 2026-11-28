"""Small I2C drivers for the accessory Pico's STEMMA QT chain.

Each class takes a machine.I2C-like bus (readfrom_mem / writeto_mem /
writeto / readfrom) and a Clock (compat.Clock or a fake), so the same code
runs against sim_hw's register-level fakes under CPython.

  NAU7802   0x2A  24-bit load-cell ADC (TAL221 100 g bar)
  LSM6DSOX  0x6A  accelerometer + gyro (tilt-table angle)
  SHT45     0x44  temperature + RH
  ADS1115   0x48  16-bit ADC, charge amplifier output (AIN0-AIN1)
"""

import units


class SensorError(Exception):
    pass


class _Dev:
    def __init__(self, i2c, addr, clock):
        self.i2c = i2c
        self.addr = addr
        self.clock = clock

    def _r8(self, reg):
        return self.i2c.readfrom_mem(self.addr, reg, 1)[0]

    def _w8(self, reg, val):
        self.i2c.writeto_mem(self.addr, reg, bytes([val & 0xFF]))

    def _set(self, reg, mask):
        self._w8(reg, self._r8(reg) | mask)

    def _clr(self, reg, mask):
        self._w8(reg, self._r8(reg) & ~mask)


# ---------------------------------------------------------------------------
# NAU7802 (Nuvoton datasheet rev 1.7; power-on sequence of section 9.1)
# ---------------------------------------------------------------------------

class NAU7802(_Dev):
    PU_CTRL, CTRL1, CTRL2, ADCO_B2, ADC, PGA, PGA_PWR = 0x00, 0x01, 0x02, 0x12, 0x15, 0x1B, 0x1C
    RR, PUD, PUA, PUR, CS, CR, AVDDS = 0x01, 0x02, 0x04, 0x08, 0x10, 0x20, 0x80
    CALS, CAL_ERR = 0x04, 0x08
    GAINS = {1: 0, 2: 1, 4: 2, 8: 3, 16: 4, 32: 5, 64: 6, 128: 7}
    RATES = {10: 0, 20: 1, 40: 2, 80: 3, 320: 7}

    def __init__(self, i2c, clock, addr=0x2A, gain=128, sps=80):
        _Dev.__init__(self, i2c, addr, clock)
        self.gain = gain
        self.sps = sps
        self.begin()

    def begin(self):
        self._w8(self.PU_CTRL, self.RR)          # register reset
        self.clock.sleep_ms(1)
        self._w8(self.PU_CTRL, self.PUD)         # leave reset, power up digital
        self._set(self.PU_CTRL, self.PUA)        # power up analog
        for _ in range(100):
            if self._r8(self.PU_CTRL) & self.PUR:
                break
            self.clock.sleep_ms(1)
        else:
            raise SensorError("NAU7802 did not power up")
        # Internal LDO at 3.3 V (VLDO = 0b100), AVDD from the LDO.
        self._w8(self.CTRL1, (self._r8(self.CTRL1) & 0xC0) | (0b100 << 3) | self.GAINS[self.gain])
        self._set(self.PU_CTRL, self.AVDDS)
        self.set_rate(self.sps, calibrate=False)
        self._set(self.ADC, 0x30)                # chopper clock off (datasheet 9.1)
        self._set(self.PGA_PWR, 0x80)            # 330 pF decoupling cap on channel 2
        self._clr(self.PGA, 0x40)                # LDOMODE = improved accuracy
        self._set(self.PU_CTRL, self.CS)         # start conversions
        self.clock.sleep_ms(250)                 # LDO settles
        self.calibrate()

    def set_rate(self, sps, calibrate=True):
        if sps not in self.RATES:
            raise SensorError("NAU7802 rate must be one of {}".format(sorted(self.RATES)))
        self._w8(self.CTRL2, (self._r8(self.CTRL2) & 0x8F) | (self.RATES[sps] << 4))
        self.sps = sps
        if calibrate:
            self.calibrate()

    def calibrate(self):
        """Internal offset calibration (CALMOD = 00)."""
        self._w8(self.CTRL2, self._r8(self.CTRL2) & 0xFC)
        self._set(self.CTRL2, self.CALS)
        for _ in range(1000):
            if not self._r8(self.CTRL2) & self.CALS:
                break
            self.clock.sleep_ms(1)
        if self._r8(self.CTRL2) & self.CAL_ERR:
            raise SensorError("NAU7802 calibration error")

    def ready(self):
        return bool(self._r8(self.PU_CTRL) & self.CR)

    def raw(self):
        b = self.i2c.readfrom_mem(self.addr, self.ADCO_B2, 3)
        return units.s24(b[0], b[1], b[2])

    def read_raw(self, n=1, timeout_ms=1000):
        """Mean of n fresh conversions (blocks about n / sps seconds)."""
        vals = []
        start = self.clock.ticks_ms()
        while len(vals) < n:
            if self.ready():
                vals.append(self.raw())
            elif self.clock.diff(self.clock.ticks_ms(), start) > timeout_ms * max(1, n):
                raise SensorError("NAU7802 timeout")
            else:
                self.clock.sleep_ms(1)
        return vals


# ---------------------------------------------------------------------------
# LSM6DSOX (ST datasheet DocID 033155)
# ---------------------------------------------------------------------------

class LSM6DSOX(_Dev):
    WHO_AM_I, CTRL1_XL, CTRL2_G, CTRL3_C, OUT_TEMP_L = 0x0F, 0x10, 0x11, 0x12, 0x20
    ODR = {12: 1, 26: 2, 52: 3, 104: 4, 208: 5, 416: 6, 833: 7}
    XL_FS = {2: 0, 16: 1, 4: 2, 8: 3}
    G_FS = {250: 0, 500: 1, 1000: 2, 2000: 3}

    def __init__(self, i2c, clock, addr=0x6A, odr=104, accel_fs=2, gyro_fs=250):
        _Dev.__init__(self, i2c, addr, clock)
        who = self._r8(self.WHO_AM_I)
        if who != 0x6C:
            raise SensorError("LSM6DSOX WHO_AM_I = 0x{:02X}, expected 0x6C".format(who))
        self._w8(self.CTRL3_C, 0x01)             # software reset
        self.clock.sleep_ms(10)
        self._w8(self.CTRL3_C, 0x44)             # BDU + register auto-increment
        self._w8(self.CTRL1_XL, (self.ODR[odr] << 4) | (self.XL_FS[accel_fs] << 2))
        self._w8(self.CTRL2_G, (self.ODR[odr] << 4) | (self.G_FS[gyro_fs] << 2))
        self.acc_lsb = units.ACC_LSB_G[accel_fs]
        self.gyro_lsb = units.GYRO_LSB_DPS[gyro_fs]

    def read(self):
        """(ax, ay, az) in g, (gx, gy, gz) in deg/s, temperature in C."""
        b = self.i2c.readfrom_mem(self.addr, self.OUT_TEMP_L, 14)
        temp = 25.0 + units.s16(b[0], b[1]) / 256.0
        g = [units.s16(b[2 + 2 * i], b[3 + 2 * i]) * self.gyro_lsb for i in range(3)]
        a = [units.s16(b[8 + 2 * i], b[9 + 2 * i]) * self.acc_lsb for i in range(3)]
        return a, g, temp


# ---------------------------------------------------------------------------
# SHT45 (Sensirion datasheet v1)
# ---------------------------------------------------------------------------

class SHT45:
    MEASURE_HIGH = 0xFD

    def __init__(self, i2c, clock, addr=0x44):
        self.i2c = i2c
        self.addr = addr
        self.clock = clock

    def read(self):
        """(temperature C, RH %) from one high-precision measurement (10 ms)."""
        self.i2c.writeto(self.addr, bytes([self.MEASURE_HIGH]))
        self.clock.sleep_ms(10)
        b = self.i2c.readfrom(self.addr, 6)
        if units.crc8_sensirion(b[0:2]) != b[2] or units.crc8_sensirion(b[3:5]) != b[5]:
            raise SensorError("SHT45 CRC error")
        return units.sht45_convert((b[0] << 8) | b[1], (b[3] << 8) | b[4])


# ---------------------------------------------------------------------------
# ADS1115 (TI SBAS444), continuous conversion of AIN0-AIN1
# ---------------------------------------------------------------------------

class ADS1115:
    CONV, CONFIG = 0x00, 0x01

    def __init__(self, i2c, clock, addr=0x48, fsr=4.096, sps=128):
        self.i2c = i2c
        self.addr = addr
        self.clock = clock
        self.configure(fsr, sps)

    def configure(self, fsr, sps):
        word = units.ads_config(fsr=fsr, sps=sps, single_shot=False)
        self.i2c.writeto_mem(self.addr, self.CONFIG, bytes([word >> 8, word & 0xFF]))
        self.fsr = fsr
        self.sps = sps
        self.clock.sleep_ms(int(2000 / sps) + 1)   # two conversions at the new setting

    def raw(self):
        b = self.i2c.readfrom_mem(self.addr, self.CONV, 2)
        v = (b[0] << 8) | b[1]
        return v - 0x10000 if v & 0x8000 else v

    def volts(self):
        return units.ads_volts(self.raw(), self.fsr)
