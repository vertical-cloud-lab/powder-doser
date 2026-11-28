"""CPython-only fakes of the accessory hardware (not uploaded to the Pico).

The fakes work at the register / byte level, so the real drivers
(sensors.py, actuators.py, tic.py) and the real Accessory run against
them unchanged. The bench simulator passes ``hooks`` to tie them to its
physical models (table angle -> IMU, platen force -> load cell, ...).
"""

import math
import random

import actuators
import sensors
import tic
import units


class FakeClock:
    """Millisecond clock that only moves when told to (or on sleep_ms)."""

    def __init__(self, t0=1000.0):
        self.t = float(t0)
        self.listeners = []

    def ticks_ms(self):
        return int(self.t)

    def diff(self, a, b):
        return a - b

    def add(self, a, b):
        return a + b

    def sleep_ms(self, ms):
        self.advance(ms)

    def advance(self, ms):
        dt = float(ms)
        self.t += dt
        for fn in self.listeners:
            fn(dt)


class FakePin:
    def __init__(self, value=0, source=None):
        self._v = value
        self.source = source
        self.history = []

    def value(self, v=None):
        if v is None:
            return self.source() if self.source else self._v
        self._v = int(v)
        self.history.append(self._v)
        return None


class FakePWM:
    def __init__(self, freq=50):
        self._duty = 0
        self._freq = freq
        self.history = []

    def duty_u16(self, v=None):
        if v is None:
            return self._duty
        self._duty = int(v)
        self.history.append(self._duty)
        return None

    def freq(self, f=None):
        if f is None:
            return self._freq
        self._freq = f
        return None


def servo_deg_from_duty(duty, min_deg, max_deg, min_us, max_us, period_us=20000):
    us = duty / 65535.0 * period_us
    return min_deg + (us - min_us) / float(max_us - min_us) * (max_deg - min_deg)


# ---------------------------------------------------------------------------
# I2C bus and chips
# ---------------------------------------------------------------------------

class FakeI2C:
    def __init__(self):
        self.devices = {}

    def scan(self):
        return sorted(self.devices)

    def _dev(self, addr):
        if addr not in self.devices:
            raise OSError(19, "ENODEV")
        return self.devices[addr]

    def readfrom_mem(self, addr, reg, n):
        return self._dev(addr).read_mem(reg, n)

    def writeto_mem(self, addr, reg, data):
        self._dev(addr).write_mem(reg, bytes(data))

    def writeto(self, addr, data):
        self._dev(addr).write(bytes(data))

    def readfrom(self, addr, n):
        return self._dev(addr).read(n)


class FakeNAU7802:
    def __init__(self, grams=lambda: 0.0, counts_per_g=21500.0, offset=12345.0,
                 noise_counts=40.0, rng=None):
        self.regs = bytearray(0x20)
        self.grams = grams
        self.counts_per_g = counts_per_g
        self.offset = offset
        self.noise = noise_counts
        self.rng = rng or random.Random(1)

    def read_mem(self, reg, n):
        if reg == 0x12:
            c = int(round(self.offset + self.grams() * self.counts_per_g
                          + self.rng.gauss(0, self.noise)))
            c &= 0xFFFFFF
            return bytes([(c >> 16) & 0xFF, (c >> 8) & 0xFF, c & 0xFF])
        if reg == 0x00:
            v = self.regs[0]
            if v & 0x02 and v & 0x04:
                v |= 0x08                       # PUR once powered
            v |= 0x20                           # CR: a conversion is always ready
            return bytes([v])
        return bytes(self.regs[reg:reg + n])

    def write_mem(self, reg, data):
        v = data[0]
        if reg == 0x00 and v & 0x01:
            self.regs = bytearray(0x20)
            return
        if reg == 0x02:
            v &= ~0x04                          # calibration finishes at once
        self.regs[reg] = v


class FakeLSM6DSOX:
    def __init__(self, tilt_deg=lambda: 0.0, jolt_g=lambda: 0.0, axis="x",
                 noise_g=0.0005, roll_deg=0.0, rng=None):
        self.regs = bytearray(0x80)
        self.regs[0x0F] = 0x6C
        self.tilt_deg = tilt_deg
        self.jolt_g = jolt_g
        self.axis = axis
        self.noise = noise_g
        self.roll = math.radians(roll_deg)
        self.rng = rng or random.Random(2)

    def _accel_fs(self):
        code = (self.regs[0x10] >> 2) & 3
        return {0: 2, 1: 16, 2: 4, 3: 8}[code]

    def read_mem(self, reg, n):
        if reg == 0x20 and n == 14:
            th = math.radians(self.tilt_deg())
            # gravity in the plate frame, tilt about the hinge (y), small mount roll about x
            along, across, normal = math.sin(th), math.cos(th) * math.sin(self.roll), math.cos(th) * math.cos(self.roll)
            j = self.jolt_g()
            ax, ay = (along, across) if self.axis == "x" else (across, along)
            a = [ax + j, ay, normal]
            lsb = units.ACC_LSB_G[self._accel_fs()]
            out = [0, 0]                       # temperature 25 C
            out += [0, 0, 0, 0, 0, 0]          # gyro
            for v in a:
                c = int(round((v + self.rng.gauss(0, self.noise)) / lsb))
                c = max(-32768, min(32767, c)) & 0xFFFF
                out += [c & 0xFF, c >> 8]
            return bytes(out)
        return bytes(self.regs[reg:reg + n])

    def write_mem(self, reg, data):
        if reg == 0x12 and data[0] & 0x01:
            self.regs[0x12] = 0
            return
        self.regs[reg] = data[0]


class FakeSHT45:
    def __init__(self, env=lambda: (22.0, 40.0)):
        self.env = env
        self.pending = False

    def write(self, data):
        self.pending = data[0] == 0xFD

    def read(self, n):
        t, rh = self.env()
        tr, hr = units.sht45_raw(t, rh)
        tb = bytes([tr >> 8, tr & 0xFF])
        hb = bytes([hr >> 8, hr & 0xFF])
        return tb + bytes([units.crc8_sensirion(tb)]) + hb + bytes([units.crc8_sensirion(hb)])


class FakeADS1115:
    PGA = {0: 6.144, 1: 4.096, 2: 2.048, 3: 1.024, 4: 0.512, 5: 0.256, 6: 0.256, 7: 0.256}

    def __init__(self, volts=lambda: 0.0, noise_v=0.0002, rng=None):
        self.config = 0x8583
        self.volts = volts
        self.noise = noise_v
        self.rng = rng or random.Random(3)

    def write_mem(self, reg, data):
        if reg == 0x01:
            self.config = (data[0] << 8) | data[1]

    def read_mem(self, reg, n):
        if reg == 0x00:
            fsr = self.PGA[(self.config >> 9) & 7]
            c = units.ads_counts(self.volts() + self.rng.gauss(0, self.noise), fsr) & 0xFFFF
            return bytes([c >> 8, c & 0xFF])
        return bytes([self.config >> 8, self.config & 0xFF])


# ---------------------------------------------------------------------------
# Tic T500 on a UART: decodes the compact protocol and moves a virtual axis
# ---------------------------------------------------------------------------

class FakeTic:
    LENGTHS = {0xE0: 5, 0xE3: 5, 0xEC: 5, 0xE6: 5, 0xE5: 5, 0xEA: 5, 0xE9: 5,
               0x94: 1, 0x91: 1, 0xA1: 2}   # get variable: offset, length

    def __init__(self, phys0=0.0, tx_wired=True):
        self.buf = bytearray()
        self.out = bytearray()
        self.pos = 0.0              # what the Tic reports
        self.phys = float(phys0)    # where the axis really is (usteps from the switch / cam zero)
        self.target = 0.0
        self.velocity = None        # usteps/s in velocity mode
        self.max_speed = 2000.0     # usteps/s
        self.energized = False
        self.tx_wired = tx_wired
        self.log = []
        self.current_code = None
        self.step_mode = None

    @staticmethod
    def _decode32(b):
        v = (b[1] | ((b[0] & 1) << 7)) | ((b[2] | ((b[0] & 2) << 6)) << 8) \
            | ((b[3] | ((b[0] & 4) << 5)) << 16) | ((b[4] | ((b[0] & 8) << 4)) << 24)
        return v - (1 << 32) if v & 0x80000000 else v

    # UART surface
    def write(self, data):
        self.buf.extend(data)
        while self.buf:
            cmd = self.buf[0]
            need = self.LENGTHS.get(cmd, 0)
            if len(self.buf) < 1 + need:
                break
            body = bytes(self.buf[1:1 + need])
            del self.buf[:1 + need]
            self._exec(cmd, body)
        return len(data)

    def read(self, n=None):
        if not self.out:
            return None
        n = len(self.out) if n is None else n
        b = bytes(self.out[:n])
        del self.out[:n]
        return b

    def any(self):
        return len(self.out)

    def _exec(self, cmd, body):
        if len(body) == 5:
            val = self._decode32(body)
        elif len(body) >= 1:
            val = body[0]
        else:
            val = None
        self.log.append((cmd, val))
        if cmd == 0xE0:
            self.target = float(val)
            self.velocity = None
        elif cmd == 0xE3:
            self.velocity = val / 10000.0
        elif cmd == 0xEC:
            self.pos = float(val)
            self.target = float(val)
            self.velocity = None
        elif cmd == 0x89:
            self.target = self.pos
            self.velocity = None
        elif cmd == 0xE6:
            self.max_speed = val / 10000.0
        elif cmd == 0x85:
            self.energized = True
        elif cmd == 0x86:
            self.energized = False
            self.velocity = None
            self.target = self.pos
        elif cmd == 0x91:
            self.current_code = val
        elif cmd == 0x94:
            self.step_mode = val
        elif cmd == 0xA1 and self.tx_wired:
            offset, length = body[0], body[1]
            p = int(round(self.pos)) & 0xFFFFFFFF
            block = bytearray(0x40)
            block[0x22:0x26] = bytes([p & 0xFF, (p >> 8) & 0xFF, (p >> 16) & 0xFF, (p >> 24) & 0xFF])
            self.out.extend(block[offset:offset + length])

    def advance(self, dt_ms):
        if not self.energized:
            return
        dt = dt_ms / 1000.0
        if self.velocity is not None:
            v = max(-self.max_speed, min(self.max_speed, self.velocity))
            d = v * dt
        else:
            err = self.target - self.pos
            step = self.max_speed * dt
            d = err if abs(err) <= step else math.copysign(step, err)
        self.pos += d
        self.phys += d


# ---------------------------------------------------------------------------
# Assemble a simulated accessory
# ---------------------------------------------------------------------------

class Hardware:
    pass


def build_sim(cfg, clock, hooks=None, tic_tx_wired=True, stage_start_mm=37.0, seed=0):
    """Fake hardware for the Accessory. hooks (all optional):
      table_deg()  plate angle seen by the IMU (default: from servo B's PWM)
      jolt_g()     extra acceleration on the IMU axis
      lc_grams()   load on the load cell
      env()        (T C, RH %)
      q_volts()    charge-amplifier output (V)
    """
    hooks = dict(hooks or {})
    rng = random.Random(seed)
    hw = Hardware()
    hw.missing = []
    hw.i2c = FakeI2C()
    hw.pwm_a = FakePWM()
    hw.pwm_b = FakePWM()
    hw.servo_a = actuators.Servo(hw.pwm_a, cfg.SERVO_A_MIN_US, cfg.SERVO_A_MAX_US, cfg.SERVO_A_MIN_DEG,
                                 cfg.SERVO_A_MAX_DEG, cfg.SERVO_A_REST_DEG, cfg.SERVO_PERIOD_US)
    hw.servo_b = actuators.Servo(hw.pwm_b, cfg.SERVO_B_MIN_US, cfg.SERVO_B_MAX_US, cfg.SERVO_B_MIN_DEG,
                                 cfg.SERVO_B_MAX_DEG, cfg.SERVO_B_REST_DEG, cfg.SERVO_PERIOD_US)

    def table_from_pwm():
        d = hw.pwm_b.duty_u16()
        if d == 0:
            return units.servo_to_table(cfg.SERVO_B_REST_DEG, cfg.TABLE_GEAR, cfg.TABLE_ZERO_SERVO_DEG)
        s = servo_deg_from_duty(d, cfg.SERVO_B_MIN_DEG, cfg.SERVO_B_MAX_DEG, cfg.SERVO_B_MIN_US,
                                cfg.SERVO_B_MAX_US, cfg.SERVO_PERIOD_US)
        return units.servo_to_table(s, cfg.TABLE_GEAR, cfg.TABLE_ZERO_SERVO_DEG)

    hw.table_from_pwm = table_from_pwm
    hw.chip_lc = FakeNAU7802(hooks.get("lc_grams", lambda: 0.0), rng=random.Random(rng.random()))
    hw.chip_imu = FakeLSM6DSOX(hooks.get("table_deg", table_from_pwm), hooks.get("jolt_g", lambda: 0.0),
                               axis=cfg.IMU_TILT_AXIS, rng=random.Random(rng.random()))
    hw.chip_env = FakeSHT45(hooks.get("env", lambda: (22.0, 40.0)))
    hw.chip_adc = FakeADS1115(hooks.get("q_volts", lambda: 0.0), rng=random.Random(rng.random()))
    hw.i2c.devices = {cfg.ADDR_NAU7802: hw.chip_lc, cfg.ADDR_LSM6DSOX: hw.chip_imu,
                      cfg.ADDR_SHT45: hw.chip_env, cfg.ADDR_ADS1115: hw.chip_adc}
    hw.lc = sensors.NAU7802(hw.i2c, clock, cfg.ADDR_NAU7802, cfg.NAU_GAIN, cfg.NAU_RATE_SPS)
    hw.imu = sensors.LSM6DSOX(hw.i2c, clock, cfg.ADDR_LSM6DSOX, cfg.IMU_ODR_HZ, cfg.IMU_ACCEL_FS_G,
                              cfg.IMU_GYRO_FS_DPS)
    hw.env = sensors.SHT45(hw.i2c, clock, cfg.ADDR_SHT45)
    hw.adc = sensors.ADS1115(hw.i2c, clock, cfg.ADDR_ADS1115, cfg.ADS_FSR_V, cfg.ADS_RATE_SPS)
    hw.tap_pwm = FakePWM(cfg.TAP_PWM_HZ)
    hw.tapper = actuators.Tapper(hw.tap_pwm, FakePin(0), cfg.TAP_DUTY)
    hw.relay = FakePin(cfg.Q_RESET_ACTIVE)
    hw.light = actuators.Light(FakePWM(cfg.LIGHT_PWM_HZ))

    prof = cfg.MOTOR_PROFILES[cfg.MOTOR_PROFILE]
    usteps_rev = units.usteps_per_rev(prof["full_steps"], prof["microsteps"])
    stage = cfg.MOTOR_PROFILES["stage"]
    phys0 = units.mm_to_usteps(stage_start_mm, stage["lead_mm"], usteps_rev) \
        if cfg.MOTOR_PROFILE == "stage" else 0.3 * usteps_rev
    hw.tic = FakeTic(phys0=phys0, tx_wired=tic_tx_wired)
    clock.listeners.append(hw.tic.advance)

    def aux_level():
        # Stage: NO switch to GND, pressed (0) at or below the switch.
        # Cam: TCRT5000 output low while the flag (first 5 % of a turn) passes.
        name = hw.motor.name if getattr(hw, "motor", None) else cfg.MOTOR_PROFILE
        if name == "stage":
            return 0 if hw.tic.phys <= 0 else 1
        frac = (hw.tic.phys / usteps_rev) % 1.0
        return 0 if frac < 0.05 else 1

    hw.aux = FakePin(1, source=aux_level)
    hw.motor = actuators.TicMotor(tic.TicSerial(hw.tic), clock, cfg.MOTOR_PROFILE, prof,
                                  cfg.TIC_SET_CURRENT)

    def stage_mm():
        return units.usteps_to_mm(hw.tic.phys, stage["lead_mm"], usteps_rev)

    hw.stage_mm = stage_mm
    return hw


class SimAccessory:
    """The real Accessory on fake hardware with a fake clock.

    call() sends one line and returns the parsed reply; run_until() advances
    time in small steps, polling the firmware and collecting events.
    """

    def __init__(self, cfg, hooks=None, seed=0, store=None, tic_tx_wired=True,
                 stage_start_mm=37.0, clock=None, profile=None):
        import accessory_main
        if profile is not None and profile != cfg.MOTOR_PROFILE:
            cfg = _with(cfg, MOTOR_PROFILE=profile)
        self.cfg = cfg
        self.clock = clock or FakeClock()
        self.lines = []
        self.hw = build_sim(cfg, self.clock, hooks, tic_tx_wired, stage_start_mm, seed)
        self.acc = accessory_main.Accessory(self.hw, cfg, clock=self.clock,
                                            emit=self.lines.append,
                                            store=store or accessory_main.Store(None))
        self.events = []

    def _drain(self):
        import json
        out = [json.loads(s) for s in self.lines]
        del self.lines[:]
        return out

    def call(self, line):
        self.acc.handle(line)
        msgs = self._drain()
        replies = [m for m in msgs if "ok" in m]
        self.events.extend(m for m in msgs if "ev" in m)
        return replies[-1] if replies else None

    def step(self, ms=2):
        self.clock.advance(ms)
        self.acc.poll()
        evs = [m for m in self._drain() if "ev" in m]
        self.events.extend(evs)
        return evs

    def run_until(self, pred, timeout_ms=60000, step_ms=2):
        """Advance until pred(event) is true for a new event; return it."""
        waited = 0
        while waited < timeout_ms:
            for ev in self.step(step_ms):
                if pred(ev):
                    return ev
            waited += step_ms
        return None

    def wait_done(self, task, timeout_ms=60000, step_ms=2):
        return self.run_until(lambda e: e.get("ev") == "done" and e.get("task") == task,
                              timeout_ms, step_ms)

    def take_events(self, ev=None):
        out = [e for e in self.events if ev is None or e.get("ev") == ev]
        self.events = [e for e in self.events if not (ev is None or e.get("ev") == ev)]
        return out


def _with(cfg, **changes):
    """Shallow copy of a config module as a simple namespace with changes."""
    class C:
        pass
    c = C()
    for k in dir(cfg):
        if k.isupper():
            setattr(c, k, getattr(cfg, k))
    for k, v in changes.items():
        setattr(c, k, v)
    return c
