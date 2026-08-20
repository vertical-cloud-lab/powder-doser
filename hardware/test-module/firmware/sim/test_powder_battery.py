"""CPython simulation tests for the uniform powder test battery.

Drives ``powder_battery.Battery`` -- the exact loop the Pico executes
-- against fake hardware with a virtual clock, so a whole battery runs
in milliseconds, and round-trips the emitted serial stream through the
host parser in ``scripts/powder_battery_capture.py``.

No hardware, no firmware driver stack (``config.py`` etc.) needed:
``Battery`` is hardware-agnostic and only ``powder_battery.run()``
touches the Pico modules.

Run:  python3 hardware/test-module/firmware/sim/test_powder_battery.py
"""

import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))                       # powder_battery
sys.path.insert(0, str(_HERE.parents[3] / "scripts"))       # capture module

import powder_battery as pb
import powder_battery_capture as cap


# ---------------------------------------------------------------------------
# Fakes
# ---------------------------------------------------------------------------

class VirtualClock:
    def __init__(self):
        self.t = 0.0

    def sleep_ms(self, ms):
        self.t += ms / 1000.0

    def time(self):
        return self.t


class Reading:
    def __init__(self, grams, stable=True):
        self.grams = grams
        self.stable = stable
        self.overload = False
        self.unit = "g"


class FakeScale:
    def __init__(self, column):
        self.column = column
        self.tare = 0.0

    def zero(self):
        self.tare = self.column.pan_g

    def read(self):
        return Reading(self.column.pan_g - self.tare, stable=False)

    def read_stable(self, timeout_ms=0):
        return Reading(self.column.pan_g - self.tare, stable=True)


class Column:
    """Deterministic powder model.

    Per-revolution yield scales with tilt (plate angle x 2); the
    ``cohesive`` variant moves nothing at tilt 0 and never avalanches.
    """

    def __init__(self, g_per_rev=0.03, tap_g=0.003, vib_g=0.001,
                 cohesive=False):
        self.pan_g = 0.0
        self.g_per_rev = g_per_rev
        self.tap_g = tap_g
        self.vib_g = vib_g
        self.cohesive = cohesive
        self.plate_deg = 0.0

    def tilt_factor(self):
        tilt = self.plate_deg * 2.0
        if self.cohesive and tilt <= 0:
            return 0.0
        return 0.2 + 0.8 * tilt / 90.0

    def rotate(self, degrees):
        self.pan_g += degrees / 360.0 * self.g_per_rev * self.tilt_factor()


class FakeStepper:
    def __init__(self, column, clock):
        self.column = column
        self.clock = clock
        self.rpm = 30.0
        self.run_rpm = 0.0
        self._run_t0 = 0.0
        self.total_deg = 0.0
        self.rpm_history = []

    def set_speed(self, rpm):
        self.rpm = rpm

    def rotate_degrees(self, degrees):
        self.total_deg += degrees
        self.column.rotate(degrees)
        self.clock.sleep_ms(int(degrees / 360.0 / self.rpm * 60000))

    def run_at_rpm(self, rpm):
        self.rpm_history.append(rpm)
        self.run_rpm = rpm
        self._run_t0 = self.clock.time()

    def keep_alive(self):
        self._advance()

    def stop(self):
        self._advance()
        self.run_rpm = 0.0

    def _advance(self):
        if self.run_rpm <= 0:
            return
        now = self.clock.time()
        degrees = self.run_rpm / 60.0 * 360.0 * (now - self._run_t0)
        self._run_t0 = now
        self.total_deg += degrees
        self.column.rotate(degrees)


class FakeTap:
    def __init__(self, column):
        self.column = column
        self.taps = 0

    def tap(self, count=1, on_ms=None, off_ms=None):
        self.taps += count
        if not (self.column.cohesive and self.column.plate_deg <= 0):
            self.column.pan_g += count * self.column.tap_g


class FakeServo:
    def __init__(self, column):
        self.column = column
        self.history = []

    def move_to(self, plate_deg):
        self.column.plate_deg = plate_deg
        self.history.append(plate_deg)


class FakeVib:
    def __init__(self, column):
        self.column = column
        self.buzzes = 0

    def buzz(self):
        self.buzzes += 1
        self.column.pan_g += self.column.vib_g


class FakeDoseResult:
    def __init__(self, target_g, dispensed_g, elapsed_s):
        self.status = "ok"
        self.target_g = target_g
        self.dispensed_g = dispensed_g
        self.elapsed_s = elapsed_s
        self.phase_cycles = [("bulk", 17), ("fine", 10), ("tap", 43)]
        self.taps = 63
        self.auger_deg = 2765.0


class FakeDoser:
    def __init__(self, column, error_g=-0.0007):
        self.column = column
        self.error_g = error_g
        self.doses = []

    def dose(self, target_g):
        self.column.pan_g += target_g + self.error_g
        self.doses.append(target_g)
        return FakeDoseResult(target_g, target_g + self.error_g, 280.0)


def make_battery(column=None, vib=True, doser=True, attended_input=None,
                 **kwargs):
    clock = VirtualClock()
    column = column or Column()
    stepper = FakeStepper(column, clock)
    tap = FakeTap(column)
    servo = FakeServo(column)
    scale = FakeScale(column)
    lines = []
    battery = pb.Battery(
        stepper, tap, servo, scale,
        vib=FakeVib(column) if vib else None,
        doser=FakeDoser(column) if doser else None,
        log=lines.append, sleep_ms=clock.sleep_ms,
        input_line=attended_input,
        attended=attended_input is not None,
        powder_id="sim-powder", **kwargs)
    return battery, lines, column, stepper, tap, servo


def parsed(lines):
    out = []
    for line in lines:
        result = cap.parse_line(line)
        if result is not None:
            out.append(result)
    return out


def rows_of(events, kind):
    return [payload for k, payload in events if k == kind]


FAILURES = []


def check(name, cond, detail=""):
    status = "PASS" if cond else "FAIL"
    print("{:4} {} {}".format(status, name, detail if not cond else ""))
    if not cond:
        FAILURES.append(name)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_full_run_protocol():
    battery, lines, column, stepper, tap, servo = make_battery()
    status = battery.run_all()
    events = parsed(lines)
    trials = rows_of(events, "trial")
    check("full-run status ok", status == "ok", status)
    markers = rows_of(events, "run")
    check("RUN BEGIN/END", markers[0][0] == "BEGIN"
          and markers[-1][0] == "END" and markers[-1][1] == "ok")
    meta = dict(rows_of(events, "meta"))
    check("META powder_id", meta.get("powder_id") == "sim-powder")
    check("META battery_version", meta.get("battery_version") == "2")

    def block(phase, letter=None):
        return [t for t in trials if t["phase"] == phase
                and (letter is None or t["block"] == letter)]

    check("baseline rows", len(block("baseline")) == pb.BASELINE_READS,
          len(block("baseline")))
    check("hold rows", len(block("hold")) == len(pb.TILTS_DEG))
    check("rotation rows",
          len(block("rotation")) == pb.ROTATION_TRIALS * len(pb.TILTS_DEG),
          len(block("rotation")))
    check("speed rows", len(block("speed")) == len(pb.SPEED_RPMS))
    check("speed polls", len(rows_of(events, "poll")) > 0)
    check("tap rows", len(block("tap")) == pb.TAP_TRIALS * len(pb.TAP_TILTS))
    check("tap refeed rows",
          len(block("refeed", "E")) == pb.TAP_TRIALS * len(pb.TAP_TILTS))
    check("vib rows", len(block("vib")) == pb.TAP_TRIALS * len(pb.TAP_TILTS))
    doses = rows_of(events, "dose")
    check("dose rows", len(doses) == pb.DOSE_REPEATS, len(doses))
    check("dose error round-trip",
          all(abs(d["error_g"] + 0.0007) < 1e-9 for d in doses))
    check("dose phase cycles",
          doses[0]["phase_cycles"] == "bulk:17;fine:10;tap:43")
    sums = rows_of(events, "device_summary")
    check("summary rows present", len(sums) >= 10, len(sums))

    # Tilt -> plate conversion: tilts 0/45/90 arrive as plate 0/22.5/45.
    check("plate angles", {0.0, 22.5, 45.0}.issuperset(set(servo.history)),
          sorted(set(servo.history)))

    # Rotation yield rises with tilt in the model; the summaries must
    # reflect that ordering (sanity that tilt actually took effect).
    rot = {t["tilt_deg"]: t for t in sums
           if t["phase"] == "rotation"}
    check("rotation yield ordered by tilt",
          rot[0.0]["mean_g"] < rot[45.0]["mean_g"] < rot[90.0]["mean_g"])


def test_tilt_parked_at_zero_after_run():
    """The rig is left horizontal so the next auger swap is predictable."""
    battery, lines, _, _, _, servo = make_battery()
    battery.run_all()
    events = parsed(lines)
    meta = dict(rows_of(events, "meta"))
    check("park META emitted",
          meta.get("park_tilt_deg") == "0.0", meta.get("park_tilt_deg"))
    check("last servo move is plate 0", servo.history[-1] == 0.0,
          servo.history[-3:])
    # Park happens before RUN,END so the capture log records it in order.
    markers = rows_of(events, "run")
    check("park precedes RUN END", markers[-1][0] == "END")

    # Block G leaves the servo with the doser; the park must still move.
    battery2, lines2, _, _, _, servo2 = make_battery(blocks="G")
    battery2.run_all()
    check("park after block G", servo2.history[-1] == 0.0,
          servo2.history[-3:])
    check("park META after block G",
          dict(rows_of(parsed(lines2), "meta")).get("park_tilt_deg") == "0.0")


def test_tilt_parked_after_abort():
    """An aborted run still leaves the tube horizontal."""
    battery, lines, _, _, _, servo = make_battery(
        attended_input=lambda: "abort")
    status = battery.run_all()
    check("abort still parks", servo.history[-1] == 0.0, servo.history[-3:])
    check("abort park META",
          dict(rows_of(parsed(lines), "meta")).get("park_tilt_deg") == "0.0")
    check("abort status preserved", status == "aborted", status)


def test_cohesive_lowflow_unattended():
    battery, lines, _, _, _, _ = make_battery(column=Column(cohesive=True))
    status = battery.run_all()
    events = parsed(lines)
    trials = rows_of(events, "trial")
    lowflow = [t for t in trials if t["flag"] == "lowflow"]
    check("cohesive run completes", status == "ok", status)
    check("lowflow rows flagged", len(lowflow) > 0)
    check("lowflow only at tilt 0",
          all(t["tilt_deg"] == 0.0 for t in lowflow),
          sorted({t["tilt_deg"] for t in lowflow}))
    # Unattended stall prompts auto-answer 'keep': all trials recorded.
    rotation0 = [t for t in trials
                 if t["phase"] == "rotation" and t["tilt_deg"] == 0.0]
    check("all tilt-0 rotations recorded",
          len(rotation0) == pb.ROTATION_TRIALS, len(rotation0))


def test_missing_hardware_skips():
    battery, lines, _, _, _, _ = make_battery(vib=False, doser=False)
    status = battery.run_all()
    meta = dict(rows_of(parsed(lines), "meta"))
    check("no-vib run ok", status == "ok", status)
    check("vib skip META", meta.get("vib") == "unavailable")
    check("dose skip META", meta.get("dose") == "unavailable")
    trials = rows_of(parsed(lines), "trial")
    check("no vib trials",
          not [t for t in trials if t["phase"] == "vib"])


def test_block_selection():
    battery, lines, _, _, _, _ = make_battery(blocks="CG")
    battery.run_all()
    events = parsed(lines)
    blocks = {t["block"] for t in rows_of(events, "trial")}
    check("only block C trials", blocks == {"C"}, blocks)
    check("block G doses ran",
          len(rows_of(events, "dose")) == pb.DOSE_REPEATS)


def test_operator_abort():
    battery, lines, _, _, _, _ = make_battery(
        attended_input=lambda: "abort")
    status = battery.run_all()
    check("abort status", status == "aborted", status)
    markers = rows_of(parsed(lines), "run")
    check("abort RUN END", markers[-1] == ["END", "aborted"])


def test_host_summary_round_trip():
    battery, lines, _, _, _, _ = make_battery()
    battery.run_all()
    events = parsed(lines)
    trials = rows_of(events, "trial")
    summary = cap.summarize(trials)
    keys = {(row["block"], row["tilt_deg"], row["phase"])
            for row in summary}
    check("host summary groups", ("C", 45.0, "rotation") in keys
          and ("E", 0.0, "tap") in keys and ("D", 45.0, "speed") in keys)
    doses = rows_of(events, "dose")
    agg = cap.dose_summary(doses)
    check("dose summary", agg["n"] == pb.DOSE_REPEATS
          and agg["ok"] == pb.DOSE_REPEATS
          and abs(agg["mean_error_g"] + 0.0007) < 1e-9, agg)


def main():
    for test in (test_full_run_protocol, test_tilt_parked_at_zero_after_run,
                 test_tilt_parked_after_abort,
                 test_cohesive_lowflow_unattended,
                 test_missing_hardware_skips, test_block_selection,
                 test_operator_abort, test_host_summary_round_trip):
        print("--- {}".format(test.__name__))
        test()
    print()
    if FAILURES:
        print("FAILED: {}".format(", ".join(FAILURES)))
        return 1
    print("all sim tests passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
