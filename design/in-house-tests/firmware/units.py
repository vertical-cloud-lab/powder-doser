"""Pure conversions shared by the accessory firmware and its CPython tests.

Nothing here touches hardware, so every function runs unchanged on the
Pico (MicroPython) and on the runner (CPython + pytest).
"""

import math

G = 9.80665  # m/s^2

# ---------------------------------------------------------------------------
# Hobby servos
# ---------------------------------------------------------------------------


def clamp(x, lo, hi):
    return lo if x < lo else hi if x > hi else x


def servo_pulse_us(deg, min_deg, max_deg, min_us, max_us):
    """Pulse width for a servo angle (linear between the end points)."""
    span = max_deg - min_deg
    frac = (clamp(deg, min_deg, max_deg) - min_deg) / span if span else 0.0
    return min_us + frac * (max_us - min_us)


def servo_duty_u16(deg, min_deg, max_deg, min_us, max_us, period_us=20000):
    us = servo_pulse_us(deg, min_deg, max_deg, min_us, max_us)
    return int(round(us / period_us * 65535))


def table_to_servo(table_deg, gear=2.0, zero_servo_deg=0.0):
    """Tilt table angle -> servo angle through the 1:2 spur pair."""
    return zero_servo_deg + gear * table_deg


def servo_to_table(servo_deg, gear=2.0, zero_servo_deg=0.0):
    return (servo_deg - zero_servo_deg) / gear


def ease_cos(frac):
    """Cosine ease-in/ease-out: zero velocity at both ends."""
    frac = clamp(frac, 0.0, 1.0)
    return 0.5 - 0.5 * math.cos(math.pi * frac)


def ramp_duration_s(start, end, rate, eased=False):
    """Time for a ramp; an eased ramp has the same peak rate, so it takes
    pi/2 times longer than a constant-rate one."""
    if rate <= 0:
        return 0.0
    t = abs(end - start) / rate
    return t * math.pi / 2.0 if eased else t


def ramp_position(start, end, rate, t_s, eased=False):
    """Set point t_s seconds into a ramp from start to end."""
    dur = ramp_duration_s(start, end, rate, eased)
    if dur <= 0 or t_s >= dur:
        return end
    if t_s <= 0:
        return start
    frac = t_s / dur
    if eased:
        frac = ease_cos(frac)
    return start + (end - start) * frac


# ---------------------------------------------------------------------------
# Stepper on a Pololu Tic (speed unit 1e-4 microstep/s, accel unit
# 1e-2 microstep/s^2; Tic user's guide section 9)
# ---------------------------------------------------------------------------

# Tic T500 "current limit" codes -> mA (Tic user's guide section 6).
TIC_T500_CURRENTS_MA = (0, 1, 174, 343, 495, 634, 762, 880, 990, 1092, 1189,
                        1281, 1368, 1452, 1532, 1611, 1687, 1762, 1835, 1909,
                        1982, 2056, 2131, 2207, 2285, 2366, 2451, 2540, 2634,
                        2734, 2843, 2962, 3093)


def tic_t500_current_code(ma):
    """Largest T500 code whose current does not exceed ``ma`` (round down,
    so a profile never drives a motor above its rating)."""
    code = 0
    for i, cur in enumerate(TIC_T500_CURRENTS_MA):
        if cur <= ma:
            code = i
    return code


def usteps_per_rev(full_steps=200, microsteps=8, gear=1.0):
    return full_steps * microsteps * gear


def rpm_to_usteps_s(rpm, usteps_rev):
    return rpm / 60.0 * usteps_rev


def usteps_s_to_tic(usteps_s):
    return int(round(usteps_s * 10000))


def usteps_s2_to_tic(usteps_s2):
    return max(1, int(round(usteps_s2 * 100)))


def mm_per_ustep(lead_mm, usteps_rev):
    return lead_mm / usteps_rev


def mm_to_usteps(mm, lead_mm, usteps_rev):
    return int(round(mm / lead_mm * usteps_rev))


def usteps_to_mm(usteps, lead_mm, usteps_rev):
    return usteps * lead_mm / usteps_rev


def mm_s_to_usteps_s(mm_s, lead_mm, usteps_rev):
    return mm_s / lead_mm * usteps_rev


def move_time_s(distance, vmax, accel):
    """Time for a trapezoidal (or triangular) move of ``distance`` at peak
    speed ``vmax`` and acceleration ``accel`` (any consistent units)."""
    d = abs(distance)
    if d == 0:
        return 0.0
    if accel <= 0:
        return d / vmax
    d_acc = vmax * vmax / accel          # distance to reach vmax and stop again
    if d >= d_acc:
        return d / vmax + vmax / accel
    return 2.0 * math.sqrt(d / accel)


# ---------------------------------------------------------------------------
# Cam-drop tapper (SPEC 2): a 2-lobe snail cam, 1 turn = 2 taps
# ---------------------------------------------------------------------------


def cam_rpm(taps_per_min, lobes=2):
    return taps_per_min / float(lobes)


def cam_turns(taps, lobes=2):
    return taps / float(lobes)


def free_fall_ms(drop_mm):
    """Free-fall time of the carriage over the drop height."""
    return 1000.0 * math.sqrt(2.0 * drop_mm / 1000.0 / G)


def cam_timing(taps_per_min, drop_mm=3.0, lobes=2, step_deg=4.0,
               dwell_deg=60.0, settle_ms=40.0):
    """Check that a cam speed gives a true free fall and a settled landing.

    step_deg: cam angle over which the snail's step passes the follower.
    dwell_deg: cam angle after the step at base radius (carriage on the anvil).
    The drop is a free fall if the step clears the follower faster than the
    carriage falls; the landing settles if the dwell outlasts settle_ms.
    """
    rpm = cam_rpm(taps_per_min, lobes)
    deg_per_ms = rpm * 360.0 / 60000.0
    period_ms = 60000.0 / taps_per_min
    step_ms = step_deg / deg_per_ms if deg_per_ms else float("inf")
    fall_ms = free_fall_ms(drop_mm)
    dwell_ms = dwell_deg / deg_per_ms if deg_per_ms else float("inf")
    return {
        "rpm": rpm,
        "period_ms": period_ms,
        "step_ms": step_ms,
        "fall_ms": fall_ms,
        "free_fall": step_ms < fall_ms,
        "dwell_ms": dwell_ms,
        "settled": dwell_ms - fall_ms >= settle_ms,
    }


def cam_tap_times_s(taps, taps_per_min, t0=0.0):
    """Nominal drop times for a constant-speed cam."""
    period = 60.0 / taps_per_min
    return [t0 + period * (i + 1) for i in range(int(taps))]


def tap_period_ms(taps_per_min, on_ms, max_ontime=0.25):
    """Period for a solenoid tap train; raises ValueError if the coil
    on-time fraction would exceed max_ontime."""
    if taps_per_min <= 0:
        raise ValueError("rate must be > 0")
    period = 60000.0 / taps_per_min
    if on_ms / period > max_ontime:
        raise ValueError("on-time {:.0f}% exceeds {:.0f}%".format(
            100.0 * on_ms / period, 100.0 * max_ontime))
    return period


# ---------------------------------------------------------------------------
# IMU tilt from gravity
# ---------------------------------------------------------------------------

ACC_LSB_G = {2: 0.061e-3, 4: 0.122e-3, 8: 0.244e-3, 16: 0.488e-3}
GYRO_LSB_DPS = {125: 4.375e-3, 250: 8.75e-3, 500: 17.5e-3, 1000: 35e-3,
                2000: 70e-3}


def s16(lo, hi):
    v = lo | (hi << 8)
    return v - 0x10000 if v & 0x8000 else v


def tilt_deg(ax, ay, az, axis="x", sign=1, offset_deg=0.0,
             bias=(0.0, 0.0, 0.0)):
    """Plate tilt about the hinge from the gravity vector (any units).

    ``axis`` is the sensor axis that points down the slope. The pitch form
    atan2(a_axis, sqrt(other^2 + az^2)) is insensitive to a small roll of
    the mount, and is valid from -90 to +90 deg.
    """
    ax -= bias[0]
    ay -= bias[1]
    az -= bias[2]
    if axis == "x":
        num, other = ax, ay
    else:
        num, other = ay, ax
    ang = math.degrees(math.atan2(sign * num, math.sqrt(other * other + az * az)))
    return ang - offset_deg


def jolt_g(a, ema):
    """Magnitude of the high-passed acceleration (a minus its running mean)."""
    return math.sqrt((a[0] - ema[0]) ** 2 + (a[1] - ema[1]) ** 2
                     + (a[2] - ema[2]) ** 2)


def ema_update(ema, a, alpha):
    if ema is None:
        return [a[0], a[1], a[2]]
    return [ema[i] + alpha * (a[i] - ema[i]) for i in range(3)]


# ---------------------------------------------------------------------------
# NAU7802 load cell
# ---------------------------------------------------------------------------


def s24(b2, b1, b0):
    v = (b2 << 16) | (b1 << 8) | b0
    return v - 0x1000000 if v & 0x800000 else v


def lc_grams(raw, offset, counts_per_g):
    return (raw - offset) / counts_per_g


def lc_counts_per_g(raw_loaded, offset, grams):
    if grams == 0:
        raise ValueError("calibration mass must be > 0")
    return (raw_loaded - offset) / grams


def mean(xs):
    return sum(xs) / len(xs) if xs else 0.0


def stdev(xs):
    n = len(xs)
    if n < 2:
        return 0.0
    m = mean(xs)
    return math.sqrt(sum((x - m) ** 2 for x in xs) / (n - 1))


# ---------------------------------------------------------------------------
# SHT45 humidity / temperature
# ---------------------------------------------------------------------------


def crc8_sensirion(data):
    crc = 0xFF
    for b in data:
        crc ^= b
        for _ in range(8):
            crc = ((crc << 1) ^ 0x31) & 0xFF if crc & 0x80 else (crc << 1) & 0xFF
    return crc


def sht45_convert(t_raw, rh_raw):
    t_c = -45.0 + 175.0 * t_raw / 65535.0
    rh = -6.0 + 125.0 * rh_raw / 65535.0
    return t_c, clamp(rh, 0.0, 100.0)


def sht45_raw(t_c, rh):
    """Inverse of sht45_convert (for fakes and tests)."""
    t_raw = int(round((t_c + 45.0) / 175.0 * 65535.0))
    rh_raw = int(round((rh + 6.0) / 125.0 * 65535.0))
    return clamp(t_raw, 0, 65535), clamp(rh_raw, 0, 65535)


# ---------------------------------------------------------------------------
# ADS1115 and the charge amplifier
# ---------------------------------------------------------------------------

ADS_PGA = {6.144: 0, 4.096: 1, 2.048: 2, 1.024: 3, 0.512: 4, 0.256: 5}
ADS_DR = {8: 0, 16: 1, 32: 2, 64: 3, 128: 4, 250: 5, 475: 6, 860: 7}


def ads_config(fsr=4.096, sps=128, single_shot=False, start=False, mux=0):
    """Config word: MUX=mux (0 = AIN0-AIN1 differential), comparator off."""
    if fsr not in ADS_PGA:
        raise ValueError("fsr must be one of {}".format(sorted(ADS_PGA)))
    if sps not in ADS_DR:
        raise ValueError("sps must be one of {}".format(sorted(ADS_DR)))
    word = 0
    if start:
        word |= 0x8000
    word |= (mux & 7) << 12
    word |= ADS_PGA[fsr] << 9
    if single_shot:
        word |= 0x0100
    word |= ADS_DR[sps] << 5
    word |= 0x0003              # comparator disabled
    return word


def ads_volts(raw, fsr):
    return raw * fsr / 32768.0


def ads_counts(volts, fsr):
    return int(clamp(round(volts / fsr * 32768.0), -32768, 32767))


def charge_nc(volts, cf_nf, sign=-1):
    """Charge (nC) on the integrator: Q = sign * C_f * V (nF x V = nC)."""
    return sign * cf_nf * volts


def charge_full_scale_nc(cf_nf, fsr=4.096, swing_v=2.4):
    """Usable range: the smaller of the ADC range and the op-amp swing."""
    return cf_nf * min(fsr, swing_v)
