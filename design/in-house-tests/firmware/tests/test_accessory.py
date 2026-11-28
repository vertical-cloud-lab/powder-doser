"""End-to-end: the real Accessory firmware on register-level fakes."""

import pytest

import config
import sim_hw


def make(**kw):
    return sim_hw.SimAccessory(config, **kw)


def test_ping_help_status_and_ids():
    a = make()
    r = a.call("ping #7")
    assert r["ok"] and r["id"] == 7 and r["pong"]
    assert any(c["cmd"] == "table" for c in a.call("help")["commands"])
    st = a.call("status")
    assert st["devices"]["imu"] and st["devices"]["lc"] and st["motor"] == "cam"
    assert st["relay"] == "closed"                 # idle: integrator shorted
    bad = a.call("frobnicate")
    assert not bad["ok"] and "unknown" in bad["err"]
    assert not a.call("table 120")["ok"]           # above the software limit


def test_gate_ramp_is_eased_and_ends_at_open():
    a = make()
    r = a.call("gate open")
    assert r["ok"] and r["target"] == config.GATE_OPEN_DEG
    done = a.wait_done("gate", 5000)
    assert done["servo_deg"] == config.GATE_OPEN_DEG
    hist = a.hw.pwm_a.history
    steps = [b - a_ for a_, b in zip(hist, hist[1:])]
    assert steps[0] < max(steps) / 3               # slow start
    a.call("gate close")
    assert a.wait_done("gate", 5000)["servo_deg"] == config.GATE_CLOSED_DEG


def test_table_ramp_streams_imu_angle():
    a = make()
    r = a.call("table 30 rate=5 stream=10")
    assert r["ok"] and r["eta_s"] == pytest.approx(6.0)
    done = a.wait_done("table", 10000)
    imu = a.take_events("imu")
    assert len(imu) >= 55
    degs = [e["deg"] for e in imu]
    # the 8-sample average lags about 40 ms: 0.2 deg at 5 deg/s
    assert all(abs(e["deg"] - e["cmd_deg"]) < 0.35 for e in imu[3:])
    assert all(b > a_ - 0.2 for a_, b in zip(degs, degs[1:]))
    assert done["cmd_deg"] == pytest.approx(30.0)
    # servo B sits at twice the table angle
    assert a.hw.servo_b.angle == pytest.approx(60.0)
    one = a.call("imu n=16")
    assert one["deg"] == pytest.approx(30.0, abs=0.05)


def test_slow_ramp_rate_is_half_a_degree_per_second():
    a = make()
    a.call("table 10 rate=10")
    a.wait_done("table", 5000)
    a.call("table 20 rate=0.5 stream=5")
    a.wait_done("table", 25000)
    imu = a.take_events("imu")
    t = [e["t"] for e in imu]
    d = [e["cmd_deg"] for e in imu]
    rate = (d[-5] - d[5]) / ((t[-5] - t[5]) / 1000.0)
    assert rate == pytest.approx(0.5, rel=0.02)


def test_table_halts_on_jolt():
    state = {"t": 0}
    a = None

    def jolt():
        return 0.3 if a is not None and a.clock.t > state["t"] else 0.0
    a = make(hooks={"jolt_g": jolt})
    state["t"] = a.clock.t + 2000
    a.call("table 40 rate=5 stream=10 halt=0.1")
    done = a.wait_done("table", 15000)
    assert done["reason"] == "jolt"
    assert 5.0 < done["cmd_deg"] < 15.0
    assert a.take_events("jolt")


def test_imu_zero_removes_mount_offset():
    offset = 1.7
    a = make(hooks={"table_deg": lambda: a.hw.table_from_pwm() + offset})
    a.call("table 0 rate=10")
    a.wait_done("table", 1000)
    z = a.call("imu zero")
    assert z["offset_deg"] == pytest.approx(offset, abs=0.05)
    a.call("table 25 rate=10")
    a.wait_done("table", 5000)
    assert a.call("imu n=16")["deg"] == pytest.approx(25.0, abs=0.05)
    a.call("imu stream 10")
    assert not a.call("imu zero")["ok"]              # refuses while streaming
    a.call("stop")


def test_tap_train_count_timing_and_duty_limit():
    a = make()
    t0 = a.clock.t
    r = a.call("tap 5 rate=120 on=30")
    assert r["ok"] and r["eta_s"] == pytest.approx(2.5)
    done = a.wait_done("tap", 5000)
    assert done["taps"] == 5 and a.hw.tapper.count == 5
    assert 2.0 <= (a.clock.t - t0) / 1000.0 <= 2.6
    assert not a.hw.tapper.is_on
    assert not a.call("tap 3 rate=600 on=60")["ok"]


def test_stage_home_move_limits_and_estop():
    a = make(profile="stage", stage_start_mm=37.0)
    assert not a.call("stage move 10")["ok"]            # not homed
    assert a.call("stage home")["ok"]
    done = a.wait_done("stage_home", 60000)
    assert done["reason"] == "done"
    assert a.hw.stage_mm() == pytest.approx(config.MOTOR_PROFILES["stage"]["home_park_mm"], abs=0.02)
    r = a.call("stage move 50 speed=10")
    assert r["ok"] and r["eta_s"] == pytest.approx(4.9 + 0.05, abs=0.1)
    done = a.wait_done("stage", 20000)
    assert done["reason"] == "done"
    assert a.hw.stage_mm() == pytest.approx(50.0, abs=0.01)
    assert not a.call("stage move 150")["ok"]           # soft limit
    a.call("stage move 0.5 speed=0.1")
    a.step(1000)
    r = a.call("estop")
    assert r["ok"] and not a.hw.tic.energized
    ev = [e for e in a.take_events("done") if e["task"] == "stage"]
    assert ev and ev[-1]["reason"] == "estop"
    assert a.call("stage pos")["mm"] == pytest.approx(49.9, abs=0.01)   # 1 s at 0.1 mm/s


def test_stage_without_tic_readback_uses_eta():
    a = make(profile="stage", tic_tx_wired=False)
    a.call("stage home")
    assert a.wait_done("stage_home", 60000)["reason"] == "done"
    a.call("stage move 20 speed=20")
    done = a.wait_done("stage", 20000)
    assert done["estimated"] is True
    assert a.hw.stage_mm() == pytest.approx(20.0, abs=0.01)


def test_cam_home_and_taps_count_index_turns():
    a = make()
    assert a.call("cam home")["ok"]
    assert a.wait_done("cam_home", 10000)["reason"] == "done"
    r = a.call("cam taps 20 rate=250")
    assert r["rpm"] == pytest.approx(125.0) and r["turns"] == 10
    done = a.wait_done("cam", 20000)
    assert done["reason"] == "done" and done["index_ok"]
    assert done["index_turns"] in (9, 10, 11)
    assert a.call("motor stage")["current_code"] == 8   # 990 mA, round down from 1.0 A
    assert not a.call("cam taps 2")["ok"]               # wrong profile now


def test_loadcell_tare_cal_read_and_stream():
    load = {"g": 0.0}
    a = make(hooks={"lc_grams": lambda: load["g"]})
    a.call("lc tare")
    load["g"] = 20.0
    cpg = a.call("lc cal 20")["counts_per_g"]
    assert cpg == pytest.approx(21500, rel=0.002)
    load["g"] = 7.5
    assert a.call("lc read n=32")["g"] == pytest.approx(7.5, abs=0.005)
    a.call("lc stream 50 s=1")
    done = a.wait_done("lc_stream", 3000)
    assert done["samples"] == pytest.approx(50, abs=2)


def test_env_charge_and_light():
    v = {"v": 0.0}
    a = make(hooks={"env": lambda: (24.2, 55.5), "q_volts": lambda: v["v"]})
    e = a.call("env")
    assert e["t_c"] == pytest.approx(24.2, abs=0.01) and e["rh"] == pytest.approx(55.5, abs=0.01)
    assert a.call("q zero ms=200")["ok"]
    assert a.wait_done("q_zero", 1000)["relay"] == "open"
    v["v"] = 0.5
    q = a.call("q read n=8")
    assert q["nc"] == pytest.approx(-5.0, abs=0.01) and q["relay"] == "open"
    a.call("q cf 100")
    assert a.call("q read")["nc"] == pytest.approx(-50.0, abs=0.1)
    assert not a.call("q gain 3.3")["ok"]
    assert a.call("q gain 2.048")["full_scale_nc"] == pytest.approx(204.8)
    assert a.call("light 40")["level"] == 40
    assert a.call("light off")["level"] == 0
    a.call("q short")
    assert a.call("status")["relay"] == "closed"


def test_stop_and_stream_lifecycle():
    a = make()
    a.call("imu stream 20")
    a.call("env stream 1")
    a.step(500)
    assert sorted(a.call("status")["tasks"]) == ["env_stream", "imu_stream"]
    r = a.call("stop imu")
    assert r["stopped"] == ["imu_stream"]
    assert a.call("status")["tasks"] == ["env_stream"]
    a.call("stop")
    assert a.call("status")["tasks"] == []
    assert a.acc.imu_users == 0
