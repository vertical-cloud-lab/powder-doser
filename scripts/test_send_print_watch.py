#!/usr/bin/env python3
"""Self-test for the gcode_state watch in all four send scripts - no
printer required.

The regression this exists for: a Bambu printer's status is STICKY. It
keeps reporting the previous job's `gcode_state` and `print_error` until
a new job overwrites them, and re-delivers them to every fresh
subscriber in the pushall snapshot. A watch loop that reads FAILED on
its first poll - about a second after publishing - is reading history,
not a verdict, and quitting there abandons a print that is actually
starting. Reported on Thumbelina 2026-08-05, where one failed AMS job
poisoned every later run in the session.

Each script is driven against a scripted status sequence: the raw-MQTT
ones through a fake paho client that replays reports, the bambulabs_api
one through a fake Printer whose last state sticks the way the real
status dict does.

    python test_send_print_watch.py
"""

import contextlib
import importlib.util
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

RAW_SCRIPTS = ("a1_mini_send_print.py",
               "h2d_step3_send_print.py",
               "a1_mini_slice_and_send.py")
LIB_SCRIPT = "h2d_step4_bambulabs_api.py"

PASSES, FAILURES = [], []


def check(name, cond, out=""):
    (PASSES if cond else FAILURES).append(name)
    print(f"{'ok  ' if cond else 'FAIL'}  {name}")
    if not cond and out:
        print("\n".join("      " + ln for ln in out.splitlines()))


def load(filename):
    """Import a send script by path, with sleeps stubbed out so a
    scripted sequence replays instantly."""
    path = os.path.join(HERE, filename)
    name = "_uut_" + filename.replace(".py", "")
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    mod.time.sleep = lambda *_a, **_k: None
    return mod


# --- raw-MQTT scripts ---------------------------------------------------------
def S(state):
    return {"gcode_state": state}


class _Msg:
    def __init__(self, doc):
        self.payload = json.dumps(doc).encode()


def run_raw(mod, pre, post, watch_seconds=1):
    """pre  = reports answering the pre-publish pushall,
    post = reports the printer sends after print.project_file."""
    class FakeClient:
        def __init__(self):
            self.on_connect = self.on_message = None

        def username_pw_set(self, *a, **k):
            pass

        tls_set = tls_insecure_set = subscribe = username_pw_set
        loop_start = loop_stop = disconnect = username_pw_set

        def connect(self, *a, **k):
            self.on_connect(self, None, None, 0, None)

        def publish(self, topic, payload):
            for report in (pre if "pushall" in payload else post):
                self.on_message(self, None, _Msg({"print": report}))

    mod.make_mqtt_client = lambda: FakeClient()
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = mod.start_and_watch("1.2.3.4", "code", "SER", "p.gcode.3mf",
                                 "", False, "", watch_seconds,
                                 wait_done=True)
    return rc, buf.getvalue()


def test_raw(filename):
    mod = load(filename)
    tag = filename

    # THE REPORTED BUG: latched at FAILED, our job then runs to completion.
    rc, out = run_raw(mod, [S("FAILED")],
                      [S("FAILED"), S("PREPARE"), S("RUNNING"), S("FINISH")])
    check(f"{tag}: latched FAILED ignored, print completes",
          rc == 0 and "PRINT COMPLETE" in out, out)

    # Same, but the pushall answer carried no gcode_state, so the latched
    # FAILED is the very first state seen and there is no baseline yet.
    rc, out = run_raw(mod, [{"mc_percent": 0}],
                      [S("FAILED"), S("PREPARE"), S("RUNNING"), S("FINISH")])
    check(f"{tag}: latched FAILED with no pre-publish baseline",
          rc == 0 and "PRINT COMPLETE" in out and "LATCHED" in out, out)

    rc, out = run_raw(mod, [{"mc_percent": 0}],
                      [S("IDLE"), S("PREPARE"), S("FAILED")])
    check(f"{tag}: no baseline, a real failure is still caught", rc == 2, out)

    # A real failure of OUR job, from the same latched baseline.
    rc, out = run_raw(mod, [S("FAILED")], [S("PREPARE"), S("FAILED")])
    check(f"{tag}: FAILED -> PREPARE -> FAILED still fails", rc == 2, out)

    rc, out = run_raw(mod, [S("IDLE")], [S("PREPARE"), S("FAILED")])
    check(f"{tag}: IDLE -> PREPARE -> FAILED still fails", rc == 2, out)

    # Command ignored outright: blame the command, not the job.
    rc, out = run_raw(mod, [S("FAILED")], [S("FAILED")])
    check(f"{tag}: stuck at the latch times out with the right message",
          rc == 3 and "never moved off" in out and "was ignored" in out, out)

    # A genuine rejection announces itself as a NEW print_error, which is
    # what keeps the conservative state guard from hiding real failures.
    rc, out = run_raw(mod, [S("FAILED")],
                      [{"gcode_state": "FAILED", "print_error": 83902467}])
    check(f"{tag}: a new print_error while latched still fails fast",
          rc == 2 and "0500-4003" in out, out)

    rc, out = run_raw(mod, [S("IDLE")],
                      [S("PREPARE"), S("RUNNING"), S("FINISH")])
    check(f"{tag}: clean IDLE -> FINISH unchanged",
          rc == 0 and "PRINT COMPLETE" in out, out)

    rc, out = run_raw(mod, [S("FINISH")], [S("FINISH")])
    check(f"{tag}: stale FINISH does not fire PRINT COMPLETE",
          rc == 3 and "PRINT COMPLETE" not in out, out)

    rc, out = run_raw(mod, [S("RUNNING")], [])
    check(f"{tag}: a busy printer is still refused before publishing",
          rc == 4 and "ABORT" in out, out)


# --- bambulabs_api script -----------------------------------------------------
class FakePrinter:
    """Replays a gcode_state sequence; the LAST value sticks, exactly as
    the real printer's status dict does."""

    def __init__(self, states, errors=None):
        self.states = list(states)
        self.errors = list(errors or [])
        self.i = 0

    def _tick(self):
        i = min(self.i, len(self.states) - 1)
        self.i += 1
        return i

    def get_state(self):
        return self.states[self._tick()]

    def print_error_code(self):
        if not self.errors:
            return 0
        return self.errors[min(self.i, len(self.errors) - 1)]

    def get_percentage(self):
        return None

    get_time = current_layer_num = total_layer_num = get_percentage


def run_lib(mod, states, baseline, errors=None, wait_done=True,
            watch_seconds=1, baseline_errors=()):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = mod.watch(FakePrinter(states, errors), watch_seconds, wait_done,
                       set(baseline_errors), baseline)
    return rc, buf.getvalue()


def test_lib():
    mod = load(LIB_SCRIPT)
    tag = LIB_SCRIPT

    # THE REPORTED BUG, verbatim: the log showed `gcode_state: FAILED` as
    # the first line after the start command, ~1 s in.
    rc, out = run_lib(mod, ["FAILED", "FAILED", "PREPARE", "RUNNING",
                            "FINISH"], "FAILED")
    check(f"{tag}: latched FAILED ignored, print completes",
          rc == 0 and "PRINT COMPLETE" in out, out)

    # The same trace with no baseline reproduces the old false verdict,
    # which is what makes the check above meaningful.
    rc, _ = run_lib(mod, ["FAILED", "PREPARE", "RUNNING", "FINISH"], None)
    check(f"{tag}: without a baseline the old false FAILED reproduces",
          rc == 2)

    # get_state() reads UNKNOWN until the first status lands.
    rc, out = run_lib(mod, ["UNKNOWN", "FAILED", "FAILED", "PREPARE",
                            "RUNNING", "FINISH"], "UNKNOWN")
    check(f"{tag}: UNKNOWN baseline adopts the first real state",
          rc == 0 and "PRINT COMPLETE" in out, out)

    rc, out = run_lib(mod, ["UNKNOWN", "IDLE", "PREPARE", "FAILED"], "UNKNOWN")
    check(f"{tag}: UNKNOWN baseline still catches a real failure",
          rc == 2, out)

    rc, out = run_lib(mod, ["IDLE", "PREPARE", "FAILED"], "IDLE")
    check(f"{tag}: IDLE -> PREPARE -> FAILED still fails",
          rc == 2 and "FAILED:" in out, out)

    rc, out = run_lib(mod, ["FAILED", "PREPARE", "FAILED"], "FAILED")
    check(f"{tag}: FAILED -> PREPARE -> FAILED still fails", rc == 2, out)

    rc, out = run_lib(mod, ["FAILED", "RUNNING", "RUNNING", "FAILED"],
                      "FAILED")
    check(f"{tag}: a mid-print failure after RUNNING still fails",
          rc == 2, out)

    rc, out = run_lib(mod, ["FAILED"], "FAILED")
    check(f"{tag}: stuck at the latch times out with the right message",
          rc == 3 and "never moved off" in out and "was ignored" in out, out)

    rc, out = run_lib(mod, ["FAILED"] * 4, "FAILED",
                      errors=[0, 83902467, 83902467, 83902467])
    check(f"{tag}: a new print_error while latched still fails fast",
          rc == 2 and "0500-4003" in out, out)

    rc, out = run_lib(mod, ["FAILED", "PREPARE", "RUNNING", "FINISH"],
                      "FAILED", errors=[83935248] * 4,
                      baseline_errors=[83935248])
    check(f"{tag}: a latched print_error is still ignored",
          rc == 0 and "PRINT COMPLETE" in out, out)

    rc, out = run_lib(mod, ["FINISH"], "FINISH")
    check(f"{tag}: stale FINISH does not fire PRINT COMPLETE",
          rc == 3 and "PRINT COMPLETE" not in out, out)

    rc, out = run_lib(mod, ["FAILED", "PREPARE", "RUNNING"], "FAILED",
                      wait_done=False)
    check(f"{tag}: --no-wait returns 0 at RUNNING",
          rc == 0 and "SUCCESS" in out, out)

    rc, out = run_lib(mod, ["FAILED", "RUNNING", "IDLE"], "FAILED")
    check(f"{tag}: RUNNING -> IDLE is reported as STOPPED",
          rc == 2 and "STOPPED" in out, out)

    # The post-publish status refresh must shrink the stale window
    # without ever being able to break a run.
    class FakeMQTT:
        def __init__(self):
            self.calls = 0
            self._last_update = 12345

        def pushall(self):
            self.calls += 1
            return True

    class FakeClient:
        def __init__(self):
            self.mqtt_client = FakeMQTT()

    printer = FakeClient()
    ok = mod.request_status_refresh(printer)
    check(f"{tag}: status refresh calls pushall and resets the throttle",
          ok and printer.mqtt_client.calls == 1
          and printer.mqtt_client._last_update == 0)
    check(f"{tag}: status refresh never raises on an unfamiliar library",
          mod.request_status_refresh(object()) is False)


def main():
    for name in RAW_SCRIPTS:
        print(f"--- {name}")
        test_raw(name)
    print(f"--- {LIB_SCRIPT}")
    test_lib()
    print(f"\n{len(PASSES)} passed, {len(FAILURES)} failed")
    for name in FAILURES:
        print(f"  FAILED: {name}")
    return 1 if FAILURES else 0


if __name__ == "__main__":
    sys.exit(main())
