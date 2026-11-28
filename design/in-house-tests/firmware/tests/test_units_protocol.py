import math

import pytest

import protocol
import sim_hw
import tic
import units


# -- servos and ramps ---------------------------------------------------------

def test_servo_duty_end_points():
    assert units.servo_pulse_us(0, 0, 180, 500, 2500) == 500
    assert units.servo_pulse_us(180, 0, 180, 500, 2500) == 2500
    assert units.servo_pulse_us(90, 0, 180, 500, 2500) == 1500
    assert units.servo_duty_u16(90, 0, 180, 500, 2500) == round(1500 / 20000 * 65535)
    assert units.servo_pulse_us(500, 0, 180, 500, 2500) == 2500     # clamped


def test_table_gear_is_one_to_two():
    assert units.table_to_servo(45.0) == 90.0
    assert units.servo_to_table(180.0) == 90.0
    assert units.servo_to_table(units.table_to_servo(17.3, 2.0, 4.0), 2.0, 4.0) == pytest.approx(17.3)


def test_ramps():
    assert units.ramp_duration_s(0, 10, 0.5) == pytest.approx(20.0)
    assert units.ramp_duration_s(0, 10, 0.5, eased=True) == pytest.approx(20.0 * math.pi / 2)
    xs = [units.ramp_position(10, 30, 4, t / 10, eased=True) for t in range(0, 90)]
    assert xs[0] == 10 and xs[-1] == 30
    assert all(b >= a for a, b in zip(xs, xs[1:]))
    assert xs[1] - xs[0] < 0.1                     # eased start
    lin = units.ramp_position(0, 10, 0.5, 4.0)
    assert lin == pytest.approx(2.0)               # constant 0.5 deg/s


# -- stepper ----------------------------------------------------------------------

def test_tic_t500_current_codes_round_down():
    assert units.tic_t500_current_code(670) == 5          # 634 mA for the 0.67 A NEMA 11
    assert units.TIC_T500_CURRENTS_MA[5] == 634
    assert units.tic_t500_current_code(1000) == 8         # 990 mA for the stage
    assert units.tic_t500_current_code(0) == 0
    assert units.tic_t500_current_code(99999) == 32


def test_stage_resolution_and_speeds():
    spr = units.usteps_per_rev(200, 8)
    assert units.mm_per_ustep(8.0, spr) == pytest.approx(0.005)
    assert units.mm_s_to_usteps_s(0.05, 8.0, spr) == pytest.approx(10.0)
    assert units.mm_s_to_usteps_s(0.2, 8.0, spr) == pytest.approx(40.0)
    assert units.mm_s_to_usteps_s(100.0, 8.0, spr) == pytest.approx(20000.0)
    assert units.usteps_s_to_tic(10.0) == 100000
    assert units.mm_to_usteps(50.0, 8.0, spr) == 10000


def test_move_time():
    assert units.move_time_s(1000, 100, 0) == pytest.approx(10.0)
    # trapezoid: 1000 at vmax 100, accel 100 -> 10 + 1 s
    assert units.move_time_s(1000, 100, 100) == pytest.approx(11.0)
    # triangle: too short to reach vmax
    assert units.move_time_s(25, 100, 100) == pytest.approx(1.0)


def test_cam_timing_at_250_taps_per_min():
    assert units.cam_rpm(250) == 125
    assert units.cam_turns(1250) == 625
    t = units.cam_timing(250, drop_mm=3.0, lobes=2, step_deg=4.0, dwell_deg=60.0)
    assert t["period_ms"] == pytest.approx(240.0)
    assert t["fall_ms"] == pytest.approx(24.7, abs=0.1)     # sqrt(2 h / g) for 3 mm
    assert t["free_fall"] and t["settled"]
    # a slow cam lets the carriage ride down the step instead of dropping
    assert not units.cam_timing(30, step_deg=4.0)["free_fall"]
    times = units.cam_tap_times_s(5, 250)
    assert times[-1] == pytest.approx(1.2)


def test_tap_duty_limit():
    assert units.tap_period_ms(60, 30) == pytest.approx(1000)
    with pytest.raises(ValueError):
        units.tap_period_ms(600, 60, 0.25)          # 60 % on-time


# -- sensors ------------------------------------------------------------------------

@pytest.mark.parametrize("deg", [0.0, 0.5, 12.0, 33.3, 60.0, 89.0])
def test_tilt_from_gravity(deg):
    th = math.radians(deg)
    assert units.tilt_deg(math.sin(th), 0.0, math.cos(th)) == pytest.approx(deg, abs=1e-9)
    # a 3 deg roll of the mount does not change the pitch reading
    r = math.radians(3.0)
    assert units.tilt_deg(math.sin(th), math.cos(th) * math.sin(r), math.cos(th) * math.cos(r)) == \
        pytest.approx(deg, abs=1e-9)
    assert units.tilt_deg(math.sin(th), 0.0, math.cos(th), offset_deg=1.0) == pytest.approx(deg - 1.0)


def test_sensirion_crc_and_conversion():
    assert units.crc8_sensirion(b"\xbe\xef") == 0x92               # datasheet example
    t, rh = units.sht45_convert(*units.sht45_raw(23.45, 51.2))
    assert t == pytest.approx(23.45, abs=0.01)
    assert rh == pytest.approx(51.2, abs=0.01)


def test_ads1115_config_and_charge():
    assert units.ads_config(2.048, 128, single_shot=True, start=True) == 0x8583   # power-on default
    assert units.ads_config(4.096, 128) == 0x0283
    assert units.ads_volts(16384, 4.096) == pytest.approx(2.048)
    assert units.charge_nc(1.0, 10.0) == pytest.approx(-10.0)
    assert units.charge_full_scale_nc(10.0) == pytest.approx(24.0)            # SPEC: +-24 nC
    assert units.charge_full_scale_nc(100.0) == pytest.approx(240.0)


def test_signed_words():
    assert units.s24(0xFF, 0xFF, 0xFF) == -1
    assert units.s24(0x7F, 0xFF, 0xFF) == 0x7FFFFF
    assert units.s16(0x00, 0x80) == -32768


def test_loadcell_conversion():
    cpg = units.lc_counts_per_g(1000 + 20 * 21500, 1000, 20.0)
    assert cpg == pytest.approx(21500)
    assert units.lc_grams(1000 + 5 * 21500, 1000, cpg) == pytest.approx(5.0)


# -- protocol -----------------------------------------------------------------------

def test_parse_line():
    assert protocol.parse_line("table 30 rate=0.5 stream=20 #17") == \
        ("table", ["30"], {"rate": "0.5", "stream": "20"}, 17)
    assert protocol.parse_line("  GATE Open ")[:2] == ("gate", ["open"])
    assert protocol.parse_line("!")[0] == "estop"
    assert protocol.parse_line("")[0] is None
    with pytest.raises(protocol.ProtocolError):
        protocol.parse_line("tap 3 rate=")
    with pytest.raises(protocol.ProtocolError):
        protocol.parse_line("tap 3 #x")


def test_numbers_and_replies():
    assert protocol.num("2.5", "x", 0, 3) == 2.5
    assert protocol.num(None, "x", default=4.0) == 4.0
    for bad in ("abc", "nan", "9"):
        with pytest.raises(protocol.ProtocolError):
            protocol.num(bad, "x", 0, 3)
    with pytest.raises(protocol.ProtocolError):
        protocol.integer("2.5", "n")
    r = protocol.reply("imu", 123, True, 4, deg=1.234567891)
    assert r == {"ok": True, "cmd": "imu", "t": 123, "id": 4, "deg": 1.23457}
    assert protocol.loads(protocol.dumps(r)) == r
    names = [c["cmd"] for c in protocol.help_list()]
    for need in ("gate", "table", "imu", "cam", "stage", "tap", "lc", "env", "q", "light", "estop", "status"):
        assert need in names


# -- Tic framing ------------------------------------------------------------------------

@pytest.mark.parametrize("value", [0, 1, 127, 128, 1234567890, -1, -987654, 2**31 - 1, -(2**31)])
def test_tic_32bit_round_trip(value):
    fake = sim_hw.FakeTic()
    t = tic.TicSerial(fake)
    t.set_target_position(value)
    assert fake.log[-1] == (0xE0, value)


def test_tic_get_variable_has_length_byte():
    fake = sim_hw.FakeTic()
    t = tic.TicSerial(fake)
    t.halt_and_set_position(-4242)
    assert t.current_position() == -4242
    assert len(fake.buf) == 0          # the 3-byte request was consumed whole
