"""Accessory Pico 2 W firmware for the in-house powder tests (MicroPython).

Runs the new actuators and sensors (SPEC 0.2) for tests 2, 3, 5, 6, 8, 9
and 10: two hobby servos (orifice gate A, tilt table B), a Tic T500 stepper
(cam tapper or linear stage), a DRV8871 tapper, the charge-amplifier reset
relay, a limit/index input, the backlight PWM and an I2C chain (NAU7802,
LSM6DSOX, SHT45, ADS1115).

Protocol (see protocol.py): one command per line on USB serial, one JSON
object per line back. Every command answers at once; long actions run as
cooperative tasks and end with a {"ev": "done", "task": ...} event, so
`estop` and `stop` act immediately even mid-move (unlike the doser's
blocking REPL).

Upload to the Pico: accessory_main.py (as main.py), config.py, compat.py,
units.py, protocol.py, sensors.py, actuators.py, tic.py, hw.py.
Under CPython the module imports without `machine`; the tests and the bench
simulator build an Accessory on sim_hw's fakes.
"""

import sys

import compat
import protocol
import units
from protocol import ProtocolError, error, event, reply

try:
    import ujson as json
except ImportError:
    import json


# ---------------------------------------------------------------------------
# Calibration store (cal.json on the Pico's flash)
# ---------------------------------------------------------------------------

class Store:
    def __init__(self, path):
        self.path = path

    def load(self):
        if self.path is None:
            return {}
        try:
            with open(self.path) as f:
                return json.load(f)
        except (OSError, ValueError):
            return {}

    def save(self, data):
        if self.path is None:
            return
        with open(self.path, "w") as f:
            json.dump(data, f)


# ---------------------------------------------------------------------------
# Tasks: step(now) returns True to keep running, False when finished.
# ---------------------------------------------------------------------------

class Task:
    name = "task"

    def __init__(self, acc):
        self.acc = acc
        self.t0 = acc.now()
        self.reason = "done"
        self.info = {}

    def elapsed(self, now):
        return self.acc.clock.diff(now, self.t0)

    def step(self, now):
        return False

    def cancel(self):
        pass


class RampTask(Task):
    """Servo ramp: eased (gate) or constant-rate (table)."""

    def __init__(self, acc, name, servo, target, speed, eased):
        Task.__init__(self, acc)
        self.name = name
        self.servo = servo
        self.start = servo.angle
        self.target = servo.clamp(target)
        self.speed = speed
        self.eased = eased
        self.dur_ms = 1000.0 * units.ramp_duration_s(self.start, self.target, speed, eased)
        self.next_ms = self.t0

    def step(self, now):
        el = self.elapsed(now)
        if el >= self.dur_ms:
            self.servo.write(self.target)
            self.info["servo_deg"] = self.servo.angle
            return False
        if self.acc.clock.diff(now, self.next_ms) >= 0:
            self.servo.write(units.ramp_position(self.start, self.target, self.speed,
                                                 el / 1000.0, self.eased))
            self.next_ms = self.acc.clock.add(now, self.acc.cfg.SERVO_UPDATE_MS)
        return True

    def cancel(self):
        self.info["servo_deg"] = self.servo.angle   # holds where it is


class TableTask(RampTask):
    """Tilt-table ramp with an optional IMU stream and halt-on-jolt."""

    def __init__(self, acc, target_deg, rate, stream_hz, halt_g):
        cfg = acc.cfg
        servo_target = units.table_to_servo(target_deg, cfg.TABLE_GEAR, cfg.TABLE_ZERO_SERVO_DEG)
        RampTask.__init__(self, acc, "table", acc.hw.servo_b, servo_target,
                          rate * cfg.TABLE_GEAR, False)
        self.period = int(1000 / stream_hz) if stream_hz else 0
        self.next_emit = self.t0
        self.halt_g = halt_g
        self.max_jolt = 0.0
        acc.imu_users += 1

    def table_deg(self):
        cfg = self.acc.cfg
        return units.servo_to_table(self.servo.angle, cfg.TABLE_GEAR, cfg.TABLE_ZERO_SERVO_DEG)

    def step(self, now):
        acc = self.acc
        s = acc.imu_state
        if s is not None:
            self.max_jolt = max(self.max_jolt, s["jolt"])
            if self.halt_g and s["jolt"] > self.halt_g and self.elapsed(now) > 300:
                self.reason = "jolt"
                acc.emit(event("jolt", now, deg=s["deg"], cmd_deg=self.table_deg(), jolt=s["jolt"]))
                self.finish_info(now)
                return False
        if self.period and acc.clock.diff(now, self.next_emit) >= 0:
            self.next_emit = acc.clock.add(now, self.period)
            if s is not None:
                acc.emit(event("imu", now, deg=s["deg"], cmd_deg=self.table_deg(),
                               jolt=self.max_jolt))
            else:
                acc.emit(event("imu", now, deg=None, cmd_deg=self.table_deg()))
            self.max_jolt = 0.0
        going = RampTask.step(self, now)
        if not going:
            self.finish_info(now)
        return going

    def finish_info(self, now):
        s = self.acc.imu_state
        self.info["cmd_deg"] = self.table_deg()
        self.info["deg"] = s["deg"] if s else None

    def cancel(self):
        self.finish_info(self.acc.now())

    def close(self):
        self.acc.imu_users -= 1


class StreamTask(Task):
    def __init__(self, acc, name, hz, seconds, read_fn, uses_imu=False):
        Task.__init__(self, acc)
        self.name = name + "_stream"
        self.ev = name
        self.period = max(1, int(1000 / hz))
        self.end_ms = int(seconds * 1000) if seconds else 0
        self.read_fn = read_fn
        self.next_ms = self.t0
        self.n = 0
        self.uses_imu = uses_imu
        if uses_imu:
            acc.imu_users += 1

    def step(self, now):
        if self.end_ms and self.elapsed(now) >= self.end_ms:
            self.info["samples"] = self.n
            return False
        if self.acc.clock.diff(now, self.next_ms) >= 0:
            self.next_ms = self.acc.clock.add(self.next_ms, self.period)
            if self.acc.clock.diff(now, self.next_ms) > 0:      # fell behind: resync
                self.next_ms = self.acc.clock.add(now, self.period)
            try:
                vals = self.read_fn()
            except Exception as exc:  # noqa: BLE001 - report and end the stream
                self.reason = "error"
                self.info["err"] = repr(exc)
                return False
            self.n += 1
            self.acc.emit(event(self.ev, now, **vals))
        return True

    def cancel(self):
        self.info["samples"] = self.n

    def close(self):
        if self.uses_imu:
            self.acc.imu_users -= 1


class TapTask(Task):
    name = "tap"

    def __init__(self, acc, n, period_ms, on_ms):
        Task.__init__(self, acc)
        self.n = n
        self.period = period_ms
        self.on_ms = on_ms
        self.done = 0
        self.tapper = acc.hw.tapper
        self.tapper.on()
        self.on_since = self.t0

    def step(self, now):
        el = self.elapsed(now)
        if self.tapper.is_on:
            if self.acc.clock.diff(now, self.on_since) >= self.on_ms:
                self.tapper.off()
                self.done += 1
                if self.done >= self.n:
                    self.info["taps"] = self.done
                    return False
        elif el >= self.done * self.period:
            self.tapper.on()
            self.on_since = now
        return True

    def cancel(self):
        self.tapper.off()
        self.info["taps"] = self.done


class RelayPulseTask(Task):
    name = "q_zero"

    def __init__(self, acc, ms):
        Task.__init__(self, acc)
        self.ms = ms
        acc.set_relay(True)

    def step(self, now):
        if self.elapsed(now) >= self.ms:
            self.acc.set_relay(False)
            self.info["relay"] = "open"
            return False
        return True


class MotorMoveTask(Task):
    """Position move on the Tic; done on read-back, else on the ETA."""

    def __init__(self, acc, name, target, eta_s, report=None):
        Task.__init__(self, acc)
        self.name = name
        self.m = acc.hw.motor
        self.target = target
        self.eta_ms = int(eta_s * 1000)
        self.report = report
        self.next_keep = self.t0
        self.next_read = self.t0
        self.towards_home = (acc.motor_profile == "stage" and target < self.m.pos)

    def step(self, now):
        acc = self.acc
        if acc.clock.diff(now, self.next_keep) >= 0:
            self.m.keepalive()
            self.next_keep = acc.clock.add(now, acc.cfg.TIC_KEEPALIVE_MS)
        if self.towards_home and acc.aux_active():
            self.m.halt_hold()
            self.reason = "limit"
            acc.emit(event("limit", now, task=self.name))
            self.fill()
            return False
        el = self.elapsed(now)
        if self.m.readback is not False and acc.clock.diff(now, self.next_read) >= 0:
            self.next_read = acc.clock.add(now, 50)
            p = self.m.read_position()
            if p is not None and p == self.target:
                self.fill()
                return False
        if self.m.readback is False and el >= self.eta_ms + 300:
            self.m.pos = self.target
            self.info["estimated"] = True
            self.fill()
            return False
        if el > 2 * self.eta_ms + 3000:
            self.reason = "timeout"
            self.m.halt_hold()
            self.fill()
            return False
        return True

    def fill(self):
        if self.report:
            self.info.update(self.report(self))

    def cancel(self):
        self.m.halt_hold()
        self.fill()


class CamTapsTask(MotorMoveTask):
    def __init__(self, acc, taps, rate):
        m = acc.hw.motor
        p = m.p
        turns = units.cam_turns(taps, p["lobes"])
        m.set_speed(units.rpm_to_usteps_s(units.cam_rpm(rate, p["lobes"]), m.usteps_rev))
        target = m.target + int(round(turns * m.usteps_rev))
        eta = m.move_to(target)
        self.edges0 = acc.aux_edges
        self.taps = taps
        self.turns = turns
        MotorMoveTask.__init__(self, acc, "cam", target, eta, report=self._report)

    def _report(self, task):
        edges = self.acc.aux_edges - self.edges0
        return {"taps": self.taps, "turns": self.turns, "index_turns": edges,
                "index_ok": abs(edges - self.turns) <= 1}


class CamHomeTask(Task):
    name = "cam_home"

    def __init__(self, acc):
        Task.__init__(self, acc)
        m = acc.hw.motor
        self.m = m
        self.edges0 = acc.aux_edges
        rpm = m.p["home_rpm"]
        m.run_velocity(units.rpm_to_usteps_s(rpm, m.usteps_rev))
        self.timeout = int(2.2 * 60000 / rpm) + 1000
        self.next_keep = self.t0

    def step(self, now):
        acc = self.acc
        if acc.clock.diff(now, self.next_keep) >= 0:
            self.m.keepalive()
            self.next_keep = acc.clock.add(now, acc.cfg.TIC_KEEPALIVE_MS)
        if acc.aux_edges != self.edges0:
            self.m.halt_set(0)
            acc.cam_homed = True
            return False
        if self.elapsed(now) > self.timeout:
            self.m.halt_set(0)
            self.reason = "no_index"
            return False
        return True

    def cancel(self):
        self.m.halt_set(0)


class StageHomeTask(Task):
    """Fast approach, back off, slow approach, zero at the switch, park."""
    name = "stage_home"

    def __init__(self, acc, speed_mm_s):
        Task.__init__(self, acc)
        self.m = acc.hw.motor
        self.p = self.m.p
        self.fast = speed_mm_s
        self.phase = None
        self.next_keep = self.t0
        self.sub = None
        acc.stage_homed = False
        self._approach(self.fast, "fast")

    def _approach(self, v_mm_s, phase):
        self.phase = phase
        self.phase_t0 = self.acc.now()
        self.limit_ms = int(1000 * self.p["home_max_mm"] / v_mm_s) + 2000
        self.m.run_velocity(self.p["home_dir"] * self.m.mm_s(v_mm_s))

    def _move(self, mm, phase):
        self.phase = phase
        self.phase_t0 = self.acc.now()
        self.m.set_speed(self.m.mm_s(self.fast))
        eta = self.m.move_to(self.m.usteps(mm))
        self.limit_ms = int(eta * 1000) + 300

    def step(self, now):
        acc = self.acc
        if acc.clock.diff(now, self.next_keep) >= 0:
            self.m.keepalive()
            self.next_keep = acc.clock.add(now, acc.cfg.TIC_KEEPALIVE_MS)
        el = acc.clock.diff(now, self.phase_t0)
        if self.phase in ("fast", "slow"):
            if acc.aux_active():
                self.m.halt_set(0)
                if self.phase == "fast":
                    self._move(self.p["home_backoff_mm"], "backoff")
                else:
                    self._move(self.p["home_park_mm"], "park")
                return True
            if el > self.limit_ms:
                self.m.halt_hold()
                self.reason = "no_switch"
                return False
            return True
        # backoff / park: position moves
        p = self.m.read_position()
        reached = (p == self.m.target) if p is not None else el >= self.limit_ms
        if reached:
            self.m.pos = self.m.target
            if self.phase == "backoff":
                if acc.aux_active():
                    self.m.halt_hold()
                    self.reason = "switch_stuck"
                    return False
                self._approach(self.p["home_slow_mm_s"], "slow")
                return True
            acc.stage_homed = True
            self.m.set_speed(self.m.mm_s(acc.stage_speed))
            self.info["pos_mm"] = self.m.mm(self.m.pos)
            return False
        return True

    def cancel(self):
        self.m.halt_hold()


# ---------------------------------------------------------------------------
# The accessory
# ---------------------------------------------------------------------------

class Accessory:
    def __init__(self, hw, cfg, clock=None, emit=None, store=None):
        self.hw = hw
        self.cfg = cfg
        self.clock = clock or compat.Clock()
        self.emit_line = emit or print
        self.store = store if store is not None else Store(getattr(cfg, "CAL_FILE", None))
        self.tasks = {}
        self.boot_ms = self.now()
        self.cal = {"imu_offset_deg": 0.0, "lc_offset": 0.0,
                    "lc_counts_per_g": cfg.LC_COUNTS_PER_G}
        self.cal.update(self.store.load())
        self.motor_profile = hw.motor.name if hw.motor else None
        self.stage_homed = False
        self.cam_homed = False
        self.stage_speed = cfg.MOTOR_PROFILES["stage"]["default_mm_s"]
        self.relay_closed = False
        self.q_cf_nf = cfg.Q_CF_NF
        self.imu_users = 0
        self.imu_state = None
        self.imu_buf = []
        self.imu_ema = None
        self.imu_next = self.now()
        self.aux_edges = 0
        self._aux_prev = None
        self.errors = 0
        if hw.relay is not None:
            self.set_relay(True)          # idle: integrator shorted

    # -- plumbing ------------------------------------------------------------
    def now(self):
        return self.clock.ticks_ms()

    def emit(self, obj):
        self.emit_line(protocol.dumps(obj))

    def set_relay(self, closed):
        level = self.cfg.Q_RESET_ACTIVE if closed else 1 - self.cfg.Q_RESET_ACTIVE
        self.hw.relay.value(level)
        self.relay_closed = closed

    def aux_level(self):
        return self.hw.aux.value() if self.hw.aux is not None else 1

    def aux_active(self):
        prof = self.cfg.MOTOR_PROFILES.get(self.motor_profile, {})
        active = prof.get("limit_active", prof.get("index_active", 0))
        return self.aux_level() == active

    def _service_aux(self):
        """Count index edges (cam profile) by polling; the main loop runs
        every 1-2 ms and the cam flag passes in tens of ms."""
        lvl = self.aux_active()
        if self._aux_prev is not None and lvl and not self._aux_prev:
            self.aux_edges += 1
        self._aux_prev = lvl

    def _need(self, attr, what):
        dev = getattr(self.hw, attr, None)
        if dev is None:
            raise ProtocolError("no {} (check wiring / i2c)".format(what))
        return dev

    def start(self, task):
        old = self.tasks.get(task.name)
        if old is not None:
            self._finish(old, "replaced", cancel=True)
        self.tasks[task.name] = task
        return task

    def _finish(self, task, reason=None, cancel=False):
        if cancel:
            task.cancel()
        if reason:
            task.reason = reason
        close = getattr(task, "close", None)
        if close:
            close()
        self.tasks.pop(task.name, None)
        self.emit(event("done", self.now(), task=task.name, reason=task.reason, **task.info))

    def _motor_busy(self):
        for name in ("cam", "cam_home", "stage", "stage_home"):
            if name in self.tasks:
                return True
        return False

    # -- IMU sampling shared by the table ramp and imu streams ----------------
    def _imu_sample(self):
        cfg = self.cfg
        a, g, temp = self.hw.imu.read()
        self.imu_ema = units.ema_update(self.imu_ema, a, cfg.JOLT_ALPHA)
        jolt = units.jolt_g(a, self.imu_ema)
        bias = self.cal.get("imu_bias_g", cfg.IMU_BIAS_G)
        ang = units.tilt_deg(a[0], a[1], a[2], cfg.IMU_TILT_AXIS, cfg.IMU_TILT_SIGN,
                             self.cal["imu_offset_deg"], bias)
        self.imu_buf.append(ang)
        if len(self.imu_buf) > cfg.IMU_AVG:
            self.imu_buf.pop(0)
        self.imu_state = {"deg": units.mean(self.imu_buf), "raw_deg": ang, "jolt": jolt,
                          "a": a, "g": g, "temp": temp}
        return self.imu_state

    def _service_imu(self, now):
        if self.imu_users <= 0 or self.hw.imu is None:
            return
        if self.clock.diff(now, self.imu_next) >= 0:
            self.imu_next = self.clock.add(now, self.cfg.IMU_SAMPLE_MS)
            try:
                self._imu_sample()
            except Exception:  # noqa: BLE001 - a failed read is retried next tick
                self.errors += 1

    def imu_read(self, n):
        """Blocking average of n samples (only when no stream is running)."""
        if self.imu_users > 0 and self.imu_state is not None:
            s = dict(self.imu_state)
            s["n"] = len(self.imu_buf)
            s["sd"] = units.stdev(self.imu_buf)
            return s
        angs = []
        s = None
        for i in range(n):
            s = self._imu_sample()
            angs.append(s["raw_deg"])
            if i < n - 1:
                self.clock.sleep_ms(self.cfg.IMU_SAMPLE_MS)
        s = dict(s)
        s["deg"] = units.mean(angs)
        s["sd"] = units.stdev(angs)
        s["n"] = n
        return s

    # -- main entry points -------------------------------------------------------
    def poll(self):
        now = self.now()
        self._service_aux()
        self._service_imu(now)
        for task in list(self.tasks.values()):
            try:
                going = task.step(now)
            except Exception as exc:  # noqa: BLE001 - never let a task kill the loop
                task.reason = "error"
                task.info["err"] = repr(exc)
                going = False
            if not going and self.tasks.get(task.name) is task:
                self._finish(task)

    def handle(self, line):
        now = self.now()
        try:
            cmd, args, kw, rid = protocol.parse_line(line)
        except ProtocolError as exc:
            self.emit(error("?", now, exc))
            return
        if cmd is None:
            return
        fn = getattr(self, "cmd_" + cmd, None)
        if fn is None or cmd not in protocol.COMMAND_NAMES:
            self.emit(error(cmd, now, "unknown command; try help", rid))
            return
        try:
            vals = fn(args, kw) or {}
            self.emit(reply(cmd, now, True, rid, **vals))
        except ProtocolError as exc:
            self.emit(error(cmd, now, exc, rid))
        except Exception as exc:  # noqa: BLE001 - report device errors as replies
            self.errors += 1
            self.emit(error(cmd, now, repr(exc), rid))

    # -- commands ------------------------------------------------------------------
    def cmd_ping(self, args, kw):
        return {"pong": True, "fw": self.cfg.FIRMWARE}

    def cmd_help(self, args, kw):
        return {"commands": protocol.help_list()}

    def cmd_status(self, args, kw):
        hw = self.hw
        m = hw.motor
        st = {
            "fw": self.cfg.FIRMWARE,
            "uptime_s": self.clock.diff(self.now(), self.boot_ms) / 1000.0,
            "devices": {k: getattr(hw, k) is not None
                        for k in ("imu", "lc", "env", "adc", "motor", "servo_a", "servo_b", "tapper")},
            "tasks": sorted(self.tasks),
            "gate_deg": hw.servo_a.angle if hw.servo_a else None,
            "table_deg": units.servo_to_table(hw.servo_b.angle, self.cfg.TABLE_GEAR,
                                              self.cfg.TABLE_ZERO_SERVO_DEG) if hw.servo_b else None,
            "motor": self.motor_profile,
            "relay": "closed" if self.relay_closed else "open",
            "q_cf_nf": self.q_cf_nf,
            "light": hw.light.level if hw.light else None,
            "aux": self.aux_level(),
            "cal": self.cal,
            "errors": self.errors,
        }
        if m is not None:
            st["motor_readback"] = m.readback
            st["current_code"] = m.current_code
            if self.motor_profile == "stage":
                st["stage_mm"] = m.mm(m.pos)
                st["stage_homed"] = self.stage_homed
            else:
                st["cam_turns"] = m.pos / m.usteps_rev
                st["cam_homed"] = self.cam_homed
                st["index_edges"] = self.aux_edges
        return st

    def cmd_estop(self, args, kw):
        hw = self.hw
        for task in list(self.tasks.values()):
            self._finish(task, "estop", cancel=True)
        if hw.motor is not None:
            try:
                hw.motor.halt_hold()
            finally:
                hw.motor.deenergize()
        if hw.tapper is not None:
            hw.tapper.off()
        if hw.relay is not None:
            self.set_relay(True)
        return {"stopped": True}

    def cmd_stop(self, args, kw):
        which = protocol.arg(args, 0, default="all")
        names = list(self.tasks) if which == "all" else [n for n in self.tasks if n.startswith(which)]
        for n in names:
            self._finish(self.tasks[n], "stopped", cancel=True)
        return {"stopped": names}

    # servos
    def _servo_move(self, name, servo, target, speed, eased=True):
        task = self.start(RampTask(self, name, servo, target, speed, eased))
        return {"from": task.start, "target": task.target, "eta_s": task.dur_ms / 1000.0}

    def cmd_gate(self, args, kw):
        s = self._need("servo_a", "servo A")
        which = protocol.arg(args, 0, "open|close|<deg>")
        if which == "open":
            target = self.cfg.GATE_OPEN_DEG
        elif which in ("close", "closed", "shut"):
            target = self.cfg.GATE_CLOSED_DEG
        else:
            target = protocol.num(which, "angle", s.min_deg, s.max_deg)
        speed = protocol.num(kw.get("speed"), "speed", 1, 1000, self.cfg.GATE_SPEED_DEG_S)
        return self._servo_move("gate", s, target, speed)

    def cmd_servo(self, args, kw):
        which = protocol.arg(args, 0, "a|b")
        if which not in ("a", "b"):
            raise ProtocolError("servo must be a or b")
        s = self._need("servo_" + which, "servo " + which)
        target = protocol.num(protocol.arg(args, 1, "angle"), "angle", s.min_deg, s.max_deg)
        speed = protocol.num(kw.get("speed"), "speed", 1, 1000, 60.0)
        name = "gate" if which == "a" else "table"
        return self._servo_move(name, s, target, speed)

    def cmd_table(self, args, kw):
        cfg = self.cfg
        self._need("servo_b", "servo B")
        first = protocol.arg(args, 0, "angle|stop")
        if first == "stop":
            t = self.tasks.get("table")
            if t is None:
                return {"running": False}
            self._finish(t, "stopped", cancel=True)
            return {"running": False, "deg": t.info.get("deg"), "cmd_deg": t.info.get("cmd_deg")}
        target = protocol.num(first, "table angle", 0, cfg.TABLE_MAX_DEG)
        rate = protocol.num(kw.get("rate"), "rate", 0.01, cfg.TABLE_MAX_RATE, cfg.TABLE_DEFAULT_RATE)
        hz = protocol.num(kw.get("stream"), "stream", 0, 50, 0.0)
        halt = protocol.num(kw.get("halt"), "halt", 0, 4, 0.0)
        if hz and self.hw.imu is None:
            raise ProtocolError("stream needs the IMU")
        task = self.start(TableTask(self, target, rate, hz, halt))
        return {"from": task.table_deg(), "target": target, "rate": rate,
                "eta_s": task.dur_ms / 1000.0}

    # IMU
    def cmd_imu(self, args, kw):
        self._need("imu", "LSM6DSOX")
        sub = protocol.arg(args, 0, default="read")
        if sub == "zero":
            if self.imu_users > 0:
                raise ProtocolError("stop the table ramp / imu stream before zeroing")
            self.cal["imu_offset_deg"] = 0.0
            s = self.imu_read(protocol.integer(kw.get("n"), "n", 1, 200, 32))
            self.cal["imu_offset_deg"] = s["deg"]
            self.store.save(self.cal)
            return {"offset_deg": s["deg"], "sd": s["sd"]}
        if sub == "stream":
            hz = protocol.num(protocol.arg(args, 1, "Hz"), "Hz", 0.1, 50)
            secs = protocol.num(kw.get("s"), "s", 0, 86400, 0.0)

            def read():
                st = self.imu_state
                if st is None:
                    st = self._imu_sample()
                return {"deg": st["deg"], "jolt": st["jolt"]}
            self.start(StreamTask(self, "imu", hz, secs, read, uses_imu=True))
            return {"streaming": "imu", "hz": hz, "s": secs}
        if sub != "read":
            raise ProtocolError("imu [read] | imu zero | imu stream <Hz>")
        s = self.imu_read(protocol.integer(kw.get("n"), "n", 1, 200, self.cfg.IMU_AVG))
        return {"deg": s["deg"], "sd": s["sd"], "n": s["n"], "a_g": s["a"], "g_dps": s["g"],
                "temp_c": s["temp"]}

    # stepper
    def cmd_motor(self, args, kw):
        m = self._need("motor", "Tic T500")
        if not args:
            return {"profile": self.motor_profile, "profiles": sorted(self.cfg.MOTOR_PROFILES)}
        name = args[0]
        if name not in self.cfg.MOTOR_PROFILES:
            raise ProtocolError("profile must be one of {}".format(sorted(self.cfg.MOTOR_PROFILES)))
        if self._motor_busy():
            raise ProtocolError("motor busy; stop it first")
        m.select(name, self.cfg.MOTOR_PROFILES[name], self.cfg.TIC_SET_CURRENT)
        self.motor_profile = name
        self.stage_homed = False
        self.cam_homed = False
        return {"profile": name, "current_ma": self.cfg.MOTOR_PROFILES[name]["current_ma"],
                "current_code": m.current_code}

    def _require_profile(self, name):
        m = self._need("motor", "Tic T500")
        if self.motor_profile != name:
            raise ProtocolError("motor profile is {}; send 'motor {}' first".format(
                self.motor_profile, name))
        return m

    def cmd_cam(self, args, kw):
        m = self._require_profile("cam")
        sub = protocol.arg(args, 0, "home|taps")
        if self._motor_busy():
            raise ProtocolError("cam busy")
        if sub == "home":
            self.start(CamHomeTask(self))
            return {"homing": True}
        if sub == "taps":
            n = protocol.integer(protocol.arg(args, 1, "n"), "n", 1, 100000)
            p = m.p
            max_rate = p["max_rpm"] * p["lobes"]
            rate = protocol.num(kw.get("rate"), "rate", 1, max_rate, p["default_tap_rate"])
            task = self.start(CamTapsTask(self, n, rate))
            return {"taps": n, "rate": rate, "rpm": units.cam_rpm(rate, p["lobes"]),
                    "turns": task.turns, "eta_s": task.eta_ms / 1000.0}
        raise ProtocolError("cam home | cam taps <n> [rate=]")

    def cmd_stage(self, args, kw):
        m = self._require_profile("stage")
        p = m.p
        sub = protocol.arg(args, 0, "home|move|rel|speed|pos|off|stop")
        if sub == "pos":
            rb = m.read_position()
            return {"mm": m.mm(m.pos), "homed": self.stage_homed, "readback": rb is not None}
        if sub == "stop":
            t = self.tasks.get("stage") or self.tasks.get("stage_home")
            if t is not None:
                self._finish(t, "stopped", cancel=True)
            else:
                m.halt_hold()
            return {"mm": m.mm(m.pos)}
        if sub == "off":
            if self._motor_busy():
                raise ProtocolError("stage moving; stop it first")
            m.deenergize()
            self.stage_homed = False
            return {"energized": False}
        if sub == "speed":
            v = protocol.num(protocol.arg(args, 1, "mm/s"), "speed", p["min_mm_s"], p["max_mm_s"])
            self.stage_speed = v
            return {"speed": v}
        if self._motor_busy():
            raise ProtocolError("stage busy")
        if sub == "home":
            v = protocol.num(kw.get("speed"), "speed", 0.1, 20, p["home_mm_s"])
            self.start(StageHomeTask(self, v))
            return {"homing": True}
        if sub in ("move", "rel"):
            x = protocol.num(protocol.arg(args, 1, "mm"), "mm")
            if not self.stage_homed and kw.get("force") != "1":
                raise ProtocolError("stage not homed; 'stage home' first (or force=1)")
            target_mm = x if sub == "move" else m.mm(m.target) + x
            if not 0.0 <= target_mm <= p["stroke_mm"]:
                raise ProtocolError("target {:.3f} mm outside 0..{} mm".format(target_mm, p["stroke_mm"]))
            v = protocol.num(kw.get("speed"), "speed", p["min_mm_s"], p["max_mm_s"], self.stage_speed)
            m.set_speed(m.mm_s(v))
            eta = m.move_to(m.usteps(target_mm))
            t0_mm = m.mm(m.pos)

            def report(task):
                return {"mm": m.mm(m.pos), "from_mm": t0_mm, "speed": v}
            self.start(MotorMoveTask(self, "stage", m.target, eta, report))
            return {"from": t0_mm, "target": target_mm, "speed": v, "eta_s": eta}
        raise ProtocolError("stage home|move|rel|speed|pos|off|stop")

    # solenoid tapper
    def cmd_tap(self, args, kw):
        self._need("tapper", "DRV8871 tapper")
        n = protocol.integer(protocol.arg(args, 0, "n"), "n", 1, 10000)
        rate = protocol.num(kw.get("rate"), "rate", 1, 600, self.cfg.TAP_DEFAULT_RATE)
        on = protocol.num(kw.get("on"), "on", 5, 200, self.cfg.TAP_ON_MS)
        try:
            period = units.tap_period_ms(rate, on, self.cfg.TAP_MAX_ONTIME)
        except ValueError as exc:
            raise ProtocolError(str(exc))
        self.start(TapTask(self, n, period, on))
        return {"n": n, "rate": rate, "on_ms": on, "eta_s": n * period / 1000.0}

    # load cell
    def _lc_grams(self, raw):
        return units.lc_grams(raw, self.cal["lc_offset"], self.cal["lc_counts_per_g"])

    def cmd_lc(self, args, kw):
        lc = self._need("lc", "NAU7802")
        sub = protocol.arg(args, 0, default="read")
        n = protocol.integer(kw.get("n"), "n", 1, 400, 8)
        if sub == "read":
            vals = lc.read_raw(n)
            raw = units.mean(vals)
            return {"g": self._lc_grams(raw), "sd_g": units.stdev(vals) / self.cal["lc_counts_per_g"],
                    "raw": raw, "n": n}
        if sub == "tare":
            vals = lc.read_raw(protocol.integer(kw.get("n"), "n", 1, 400, 32))
            self.cal["lc_offset"] = units.mean(vals)
            return {"offset": self.cal["lc_offset"], "sd_counts": units.stdev(vals)}
        if sub == "cal":
            grams = protocol.num(protocol.arg(args, 1, "grams"), "grams", 0.001, 1000)
            vals = lc.read_raw(protocol.integer(kw.get("n"), "n", 1, 400, 32))
            cpg = units.lc_counts_per_g(units.mean(vals), self.cal["lc_offset"], grams)
            self.cal["lc_counts_per_g"] = cpg
            self.store.save(self.cal)
            return {"counts_per_g": cpg}
        if sub == "rate":
            sps = protocol.integer(protocol.arg(args, 1, "sps"), "sps")
            try:
                lc.set_rate(sps)
            except Exception as exc:  # noqa: BLE001
                raise ProtocolError(str(exc))
            return {"sps": sps}
        if sub == "stream":
            hz = protocol.num(protocol.arg(args, 1, "Hz"), "Hz", 0.1, self.cfg.STREAM_MAX_HZ)
            secs = protocol.num(kw.get("s"), "s", 0, 86400, 0.0)

            def read():
                raw = lc.raw()
                return {"g": self._lc_grams(raw), "raw": raw}
            self.start(StreamTask(self, "lc", hz, secs, read))
            return {"streaming": "lc", "hz": hz, "s": secs}
        raise ProtocolError("lc read|tare|cal|rate|stream")

    # environment
    def cmd_env(self, args, kw):
        env = self._need("env", "SHT45")
        sub = protocol.arg(args, 0, default="read")
        if sub == "stream":
            hz = protocol.num(protocol.arg(args, 1, "Hz"), "Hz", 0.01, 5)
            secs = protocol.num(kw.get("s"), "s", 0, 864000, 0.0)

            def read():
                t, rh = env.read()
                return {"t_c": t, "rh": rh}
            self.start(StreamTask(self, "env", hz, secs, read))
            return {"streaming": "env", "hz": hz, "s": secs}
        t, rh = env.read()
        return {"t_c": t, "rh": rh}

    # charge amplifier
    def _q_vals(self, volts):
        return {"v": volts, "nc": units.charge_nc(volts, self.q_cf_nf, self.cfg.Q_SIGN)}

    def cmd_q(self, args, kw):
        sub = protocol.arg(args, 0, default="read")
        if sub == "zero":
            self._need("relay", "reset relay")
            ms = protocol.num(kw.get("ms"), "ms", 10, 10000, self.cfg.Q_ZERO_MS)
            self.start(RelayPulseTask(self, ms))
            return {"relay": "closed", "open_in_ms": ms}
        if sub == "short":
            self._need("relay", "reset relay")
            t = self.tasks.get("q_zero")
            if t is not None:
                self._finish(t, "stopped", cancel=True)
            self.set_relay(True)
            return {"relay": "closed"}
        if sub == "cf":
            cf = protocol.num(protocol.arg(args, 1, "nF"), "C_f", 0.1, 10000)
            self.q_cf_nf = cf
            return {"cf_nf": cf, "full_scale_nc": units.charge_full_scale_nc(cf, self.hw.adc.fsr if self.hw.adc else 4.096)}
        adc = self._need("adc", "ADS1115")
        if sub == "gain":
            fsr = protocol.num(protocol.arg(args, 1, "fsr"), "fsr")
            if fsr not in units.ADS_PGA:
                raise ProtocolError("fsr must be one of {}".format(sorted(units.ADS_PGA)))
            adc.configure(fsr, adc.sps)
            return {"fsr": fsr, "full_scale_nc": units.charge_full_scale_nc(self.q_cf_nf, fsr)}
        if sub == "read":
            n = protocol.integer(kw.get("n"), "n", 1, 64, 4)
            vs = []
            for i in range(n):
                vs.append(adc.volts())
                if i < n - 1:
                    self.clock.sleep_ms(int(1000 / adc.sps) + 1)
            out = self._q_vals(units.mean(vs))
            out["sd_v"] = units.stdev(vs)
            out["relay"] = "closed" if self.relay_closed else "open"
            out["fsr"] = adc.fsr
            out["cf_nf"] = self.q_cf_nf
            return out
        if sub == "stream":
            hz = protocol.num(protocol.arg(args, 1, "Hz"), "Hz", 0.1, min(self.cfg.STREAM_MAX_HZ, adc.sps / 2))
            secs = protocol.num(kw.get("s"), "s", 0, 86400, 0.0)
            self.start(StreamTask(self, "q", hz, secs, lambda: self._q_vals(adc.volts())))
            return {"streaming": "q", "hz": hz, "s": secs}
        raise ProtocolError("q zero|short|read|gain|cf|stream")

    # light
    def cmd_light(self, args, kw):
        light = self._need("light", "backlight PWM")
        which = protocol.arg(args, 0, "on|off|<0-100>")
        if which == "on":
            light.set(self.cfg.LIGHT_DEFAULT)
        elif which == "off":
            light.set(0)
        else:
            light.set(protocol.num(which, "level", 0, 100))
        return {"level": light.level}

    def cmd_i2c(self, args, kw):
        i2c = self._need("i2c", "I2C bus")
        return {"found": ["0x{:02X}".format(a) for a in i2c.scan()]}

    def cmd_cal(self, args, kw):
        sub = protocol.arg(args, 0, default="show")
        if sub == "save":
            self.store.save(self.cal)
        elif sub == "clear":
            self.cal = {"imu_offset_deg": 0.0, "lc_offset": 0.0,
                        "lc_counts_per_g": self.cfg.LC_COUNTS_PER_G}
            self.store.save(self.cal)
        elif sub != "show":
            raise ProtocolError("cal show|save|clear")
        return {"cal": self.cal}


# ---------------------------------------------------------------------------
# Pico main loop
# ---------------------------------------------------------------------------

_poll = None
_buf = []


def _read_lines():
    """Non-blocking: drain stdin into a buffer, return complete lines."""
    global _poll
    import uselect
    if _poll is None:
        _poll = uselect.poll()
        _poll.register(sys.stdin, uselect.POLLIN)
    lines = []
    for _ in range(128):
        if not _poll.poll(0):
            break
        ch = sys.stdin.read(1)
        if ch in ("\r", "\n"):
            if _buf:
                lines.append("".join(_buf))
                del _buf[:]
        elif len(_buf) < 200:
            _buf.append(ch)
    return lines


def main():
    import config
    import hw as hwmod
    clock = compat.Clock()
    hardware = hwmod.build(config, clock)
    acc = Accessory(hardware, config, clock=clock)
    acc.emit(event("boot", acc.now(), fw=config.FIRMWARE, missing=hardware.missing))
    while True:
        for line in _read_lines():
            acc.handle(line)
        acc.poll()
        clock.sleep_ms(1)


if __name__ == "__main__" and sys.implementation.name == "micropython":
    main()
