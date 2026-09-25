"""Tests for the issue #164 per-dose executor -- no hardware needed.

Replays a canned Pico conversation through a fake ``serial.Serial`` so
the whole executor path runs: runner probe, parameter push with echo
verification, dose -> RESULT parse, telemetry pull, spool, summary
line, and the never-dose-twice idempotency rule.

Run:  python3 scripts/tests/test_opt_dose_capture.py
"""

import io
import json
import os
import re
import sys
import tempfile
import time
import types
import contextlib

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(_HERE))            # scripts/

import opt_common as oc                                # noqa: E402


RESULT_DOC = {
    "v": 1, "status": "ok", "target_g": 0.5, "final_g": 0.5042,
    "settled_final": 1, "error_mg": 4.2, "t_total_s": 74.3,
    "t_bulk_s": 8.1, "t_trickle_s": 51.0, "t_tap_s": 9.0,
    "t_settle_s": 2.6, "phase_cycles": {"bulk": 30, "trickle": 200,
                                        "tap": 4},
    "taps": 4, "nudges": 1, "auger_rev": 4.4, "ff_g_per_rev": 0.1131,
    "baseline_g": 0.0003, "read_retries": 0,
    "stop_events": [
        {"phase": "bulk", "m_stop_g": 0.203, "settled_g": 0.291,
         "afterflow_g": 0.088, "rate_slope_gps": 0.102,
         "rate_kf_gps": None, "tau_s": 0.3, "stalled": 0},
        {"phase": "trickle", "m_stop_g": 0.462, "settled_g": 0.489,
         "afterflow_g": 0.027, "rate_slope_gps": 0.031,
         "rate_kf_gps": 0.028, "tau_s": 0.3, "stalled": 0},
    ],
    "params": {"bulk_tap": False, "trickle_tap": True,
               "bulk_tilt_deg": 27.5, "trickle_tilt_deg": 14.0,
               "tap_tilt_deg": 9.0, "bulk_rpm": 62.0,
               "trickle_start_remaining_g": 0.22, "tolerance_g": 0.006,
               "tau_afterflow_s": 0.83, "goal_mass_g": 0.75},
    "telemetry_rows": 2, "log_path": "/trickle_log_004.csv",
    "dose_n": 5, "fw": oc.FIRMWARE_ID,
}


class FakeSerial:
    """Just enough of pyserial -- and of a shared Pico -- for PicoSession.

    ``mode`` is what the Pico is doing when the executor connects:
    "runner" (main_trickle answering, firmware ``fw``), "repl" (idle
    >>>), "busy" (someone's program, silent), "streaming" (someone's
    program printing with nobody connected).
    """

    doses = 0
    instances = 0
    mode = "runner"
    fw = oc.FIRMWARE_ID
    lock_error = False
    last = None

    def __init__(self, port, baud, timeout=0.25, exclusive=False):
        if FakeSerial.lock_error:
            raise OSError(11, "Could not exclusively lock port {}: [Errno "
                              "11] Resource temporarily unavailable"
                          .format(port))
        FakeSerial.instances += 1
        FakeSerial.last = self
        self.exclusive = exclusive
        self.mode = FakeSerial.mode
        self.raw_mode = False
        self.queue = []
        self.set_seen = []
        self.writes = []
        self.closed = False

    def _listing(self):
        return ((["firmware: {}".format(FakeSerial.fw)]
                 if FakeSerial.fw else [])
                + ["stepper: 55 auger rpm",
                   "trickle parameters ('set <key> <value>'):",
                   "  bulk_rpm = 55.0"])

    def write(self, data):
        self.writes.append(data)
        if b"\x03" in data and self.mode in ("busy", "runner",
                                             "streaming"):
            self.mode = "repl"
            self.queue += ["KeyboardInterrupt:", ">>> "]
        if b"\x01" in data and self.mode == "repl":
            self.raw_mode = True
            self.queue += ["raw REPL; CTRL-B to exit", ">"]
            return
        if data == b"\x04" and self.raw_mode:
            self.queue += ["MPY: soft reboot", "raw REPL; CTRL-B to exit",
                           ">"]
            return
        if b"\x02" in data and self.mode == "repl":
            self.raw_mode = False
            self.queue += ["MicroPython v1.24.1; Raspberry Pi Pico", ">>> "]
            return
        line = data.decode(errors="replace").strip()
        if self.mode == "repl":
            if "import main_trickle" in line:
                self.boot_line = line
                self.mode = "runner"
                self.queue += ["[rig] bringing up powder-doser test module"]
                self.queue += self._listing()
            elif line == "":
                self.queue.append(">>> ")
            elif line and line[0] >= " ":
                self.queue += ["NameError: name {!r} isn't defined"
                               .format(line), ">>> "]
            return
        if self.mode != "runner":
            return
        if line == "s":
            self.queue += self._listing()
        elif line.startswith("set "):
            _, key, value = line.split(" ", 2)
            self.set_seen.append((key, value))
            self.queue.append("[set] {} = {} (was x)".format(key, value))
        elif line.startswith("g "):
            FakeSerial.doses += 1
            self.queue += ["[dose] trickle-tap dose to 0.5000 g",
                           "=== stage 1 'bulk': ...",
                           "RESULT " + json.dumps(RESULT_DOC)]
        elif line == "log":
            self.queue += ["--- BEGIN trickle telemetry CSV ---",
                           "t_s,phase,z_g",
                           "0.25,bulk,0.001",
                           "0.50,bulk,0.002",
                           "--- END trickle telemetry CSV ---"]
        elif line == "res":
            self.queue.append("RESULT " + json.dumps(RESULT_DOC))

    def flush(self):
        pass

    def readline(self):
        if self.mode == "streaming":
            time.sleep(0.05)
            return b"PRE,rev,3,0.25,0.0312\r\n"
        if self.queue:
            item = self.queue.pop(0)
            # a prompt carries no newline: readline returns it on timeout
            return (item if item in (">>> ", ">")
                    else item + "\r\n").encode()
        time.sleep(0.01)
        return b""

    def close(self):
        self.closed = True


def _fake_pico(mode="runner", fw=oc.FIRMWARE_ID, lock_error=False):
    FakeSerial.mode, FakeSerial.fw = mode, fw
    FakeSerial.lock_error = lock_error
    FakeSerial.last = None
    sys.modules["serial"] = types.SimpleNamespace(Serial=FakeSerial)


_FAILURES = []


def check(what, ok):
    print("  {} {}".format("PASS" if ok else "FAIL", what))
    if not ok:
        _FAILURES.append(what)


PARAMS = {"bulk_tap": "off", "trim_tap": "2hz", "bulk_tilt_deg": 27.5,
          "trickle_tilt_deg": 14.0, "tap_tilt_deg": 9.0,
          "bulk_rpm": 62.0, "trickle_start_remaining_g": 0.22,
          "tolerance_g": 0.006, "tau_afterflow_s": 0.83}


def test_firmware_set_lines():
    lines = oc.firmware_set_lines(oc.validate_params(PARAMS))
    check("categoricals map to boolean knobs",
          "set bulk_tap 0" in lines and "set trickle_tap 1" in lines)
    check("tau_afterflow_s rides along", "set tau_afterflow_s 0.83" in lines)
    check("all 8 searched knobs + tau pushed", len(lines) == 9)


def test_penalization():
    ok = oc.ax_raw_data({"t_total_s": 74.3, "abs_error_mg": 4.2})
    jam = oc.ax_raw_data({"t_total_s": 74.3, "abs_error_mg": 4.2}, jam=True)
    worse = oc.ax_raw_data({"t_total_s": 240.0, "abs_error_mg": 35.0},
                           spill=True)
    check("clean dose passes through", ok == {"t_total_s": 74.3,
                                              "abs_error_mg": 4.2})
    check("jam is pushed to the ceilings", jam == {"t_total_s": 180.0,
                                                   "abs_error_mg": 20.0})
    check("true value kept when worse than the cap",
          worse == {"t_total_s": 240.0, "abs_error_mg": 35.0})


def _run_capture(argv):
    import opt_dose_capture as odc
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        code = odc.main(argv)
    lines = [l for l in out.getvalue().splitlines() if l.strip()]
    return code, lines


def test_executor_end_to_end():
    _fake_pico()
    tmp = tempfile.mkdtemp(prefix="optdose-")
    argv = ["--powder-id", "salt", "--target-g", "0.5",
            "--campaign-id", "salt-test", "--trial", "aaaa-bbbb",
            "--trial-index", "3", "--mode", "bo",
            "--params", json.dumps(PARAMS),
            "--covariates", json.dumps({"doses_since_cup_empty": 4}),
            "--out", tmp, "--no-upload"]
    code, lines = _run_capture(argv)
    check("exit 0 on a clean dose", code == 0)
    check("exactly one stdout line", len(lines) == 1)
    summary = json.loads(lines[0])
    check("summary carries the outcomes",
          summary["t_total_s"] == 74.3
          and summary["abs_error_mg"] == 4.2
          and summary["status"] == "ok" and summary["jam"] is False)
    check("summary carries both stop events",
          len(summary["stop_events"]) == 2)
    doc_path = os.path.join(tmp, "salt-test", "trial_aaaa-bbbb.json")
    check("full trial doc spooled", os.path.exists(doc_path))
    with open(doc_path) as f:
        doc = json.load(f)
    check("executed params echoed from the firmware",
          doc["parameters_executed"]["trickle_tap"] in (True, 1))
    check("telemetry rows captured",
          doc["telemetry"]["rows"] == ["0.25,bulk,0.001",
                                       "0.50,bulk,0.002"])
    check("covariates stored",
          doc["covariates"] == {"doses_since_cup_empty": 4})
    check("port opened with the exclusive (mpremote-compatible) lock",
          FakeSerial.last.exclusive is True)
    check("firmware id recorded with the trial",
          doc["device"]["firmware"] == oc.FIRMWARE_ID)

    doses_before = FakeSerial.doses
    code2, lines2 = _run_capture(argv)
    summary2 = json.loads(lines2[0])
    check("re-invoking the same uuid never doses twice",
          FakeSerial.doses == doses_before and code2 == 0
          and summary2["t_total_s"] == 74.3)

    code3, lines3 = _run_capture(["--fetch", "aaaa-bbbb", "--out", tmp])
    check("--fetch returns the stored summary",
          code3 == 0 and json.loads(lines3[0])["status"] == "ok")
    code4, lines4 = _run_capture(["--fetch", "nope", "--out", tmp])
    check("--fetch on an unknown uuid exits 3",
          code4 == 3 and json.loads(lines4[0])["status"] == "not-found")


def _dose_argv(tmp, trial, *extra):
    return (["--powder-id", "salt", "--target-g", "0.5",
             "--campaign-id", "salt-test", "--trial", trial,
             "--params", json.dumps(PARAMS), "--out", tmp, "--no-upload"]
            + list(extra))


def test_shared_pico_guards():
    """The Pico is shared with other sessions' firmware (section 5.1):
    never interrupt their programs, never dose on foreign firmware."""
    import opt_dose_capture as odc
    tmp = tempfile.mkdtemp(prefix="optdose-shared-")

    def run(mode, trial, *extra, **fake):
        _fake_pico(mode, **fake)
        before = FakeSerial.doses
        code, lines = _run_capture(_dose_argv(tmp, trial, *extra))
        return (code, json.loads(lines[0]), FakeSerial.last,
                FakeSerial.doses - before)

    code, summ, port, dosed = run("repl", "t-repl")
    wrote = b"".join(port.writes)
    check("idle >>> REPL: clean raw-mode soft reset, then boot",
          wrote.index(b"\x01") < wrote.index(b"\x04")
          < wrote.index(b"\x02"))
    check("idle >>> REPL: runner imported from /trickle_tap",
          "sys.path.insert(0, '/trickle_tap')" in port.boot_line)
    check("idle >>> REPL: dose then runs", summ["status"] == "ok"
          and dosed == 1 and code == 0)

    code, summ, port, dosed = run("busy", "t-busy")
    check("unknown program: rig-busy, exit 4, nothing dosed",
          summ["status"] == "rig-busy" and summ["infra_error"]
          and code == 4 and dosed == 0)
    check("unknown program: never ctrl-C'd",
          not any(b"\x03" in w for w in port.writes))

    code, summ, port, dosed = run("streaming", "t-stream")
    check("output streaming with nobody connected: rig-busy, not a "
          "single byte typed into it",
          summ["status"] == "rig-busy" and port.writes == [] and dosed == 0)

    for i, fw in enumerate(("trickle_tap/2026-01-01", None)):
        code, summ, port, dosed = run("runner", "t-fw-{}".format(i), fw=fw)
        check("foreign runner firmware {!r}: rig-busy, no set/g "
              "sent".format(fw),
              summ["status"] == "rig-busy" and port.set_seen == []
              and dosed == 0)

    code, summ, port, dosed = run("busy", "t-take", "--takeover")
    check("--takeover: ctrl-C, clean boot, dose",
          any(b"\x03" in w for w in port.writes)
          and summ["status"] == "ok" and dosed == 1)

    code, summ, port, dosed = run("runner", "t-lock", lock_error=True)
    check("port locked by mpremote/portguard: rig-busy",
          summ["status"] == "rig-busy" and port is None and dosed == 0)

    real_holders = odc.port_holders
    odc.port_holders = lambda path: [(4242, "python3 scripts/"
                                            "powder_battery_capture.py")]
    try:
        code, summ, port, dosed = run("runner", "t-held")
    finally:
        odc.port_holders = real_holders
    check("port open in an unlocked bench script: rig-busy, port closed",
          summ["status"] == "rig-busy" and port.closed and dosed == 0
          and port.writes == [])
    check("port_holders runs on this host without raising",
          isinstance(odc.port_holders("/dev/null"), list))


def test_firmware_id_in_sync():
    path = os.path.join(os.path.dirname(os.path.dirname(_HERE)),
                        "hardware", "test-module", "firmware",
                        "trickle_tap", "trickle_controller.py")
    if not os.path.exists(path):          # e.g. the Zero's sparse checkout
        print("  SKIP firmware source not checked out here")
        return
    with open(path) as f:
        m = re.search(r'^FIRMWARE_ID = "([^"]+)"', f.read(), re.M)
    check("opt_common.FIRMWARE_ID matches trickle_controller.FIRMWARE_ID",
          m is not None and m.group(1) == oc.FIRMWARE_ID)


def test_jam_classification():
    check("stall / budget / timeout are jams with reasons",
          oc.classify_status("stalled") == (True, "stall", False)
          and oc.classify_status("cycle-budget") == (True, "tap-budget",
                                                     False)
          and oc.classify_status("timeout") == (True, "timeout", False))
    check("scale trouble is infra, not jam",
          oc.classify_status("scale-error") == (False, None, True))
    check("ok / overshoot are neither",
          oc.classify_status("ok") == (False, None, False)
          and oc.classify_status("overshoot") == (False, None, False))


@contextlib.contextmanager
def _mongo_env(**values):
    """os.environ with the Mongo vars forced to ``values`` (or absent)."""
    names = (oc.MONGODB_URI_ENV,) + oc.MONGODB_URI_ENV_FALLBACKS
    saved = {n: os.environ.pop(n, None) for n in names}
    os.environ.update(values)
    try:
        yield
    finally:
        for n in names:
            os.environ.pop(n, None)
            if saved[n] is not None:
                os.environ[n] = saved[n]


def test_mongo_uri_resolution():
    with tempfile.TemporaryDirectory(prefix="optenv-") as tmp:
        env_file = os.path.join(tmp, "env")
        with open(env_file, "w") as f:
            f.write("# comment\n"
                    "export MONGODB_URI='mongodb+srv://file-user@x/'\n"
                    "OTHER=ignored\n")
        with _mongo_env():
            uri, src = oc.resolve_mongo_uri(env_file=env_file)
            check("env file is parsed (export + quotes) when no env var",
                  uri == "mongodb+srv://file-user@x/" and src == env_file)
            check("no URI anywhere -> (None, None)",
                  oc.resolve_mongo_uri(env_file=os.path.join(tmp, "nope"))
                  == (None, None))
        with _mongo_env(PI_MONGODB_URI="mongodb+srv://pi@x/"):
            uri, src = oc.resolve_mongo_uri(env_file=env_file)
            check("$PI_MONGODB_URI beats the env file",
                  uri == "mongodb+srv://pi@x/" and src == "$PI_MONGODB_URI")
        with _mongo_env(MONGODB_URI="mongodb+srv://main@x/",
                        PI_MONGODB_URI="mongodb+srv://pi@x/"):
            uri, src = oc.resolve_mongo_uri(env_file=env_file)
            check("$MONGODB_URI wins over every fallback",
                  uri == "mongodb+srv://main@x/" and src == "$MONGODB_URI")
            check("explicit argument wins over $MONGODB_URI",
                  oc.resolve_mongo_uri("mongodb://arg/")[0]
                  == "mongodb://arg/")
        with open(env_file, "w") as f:
            f.write('PI_MONGODB_URI="mongodb+srv://pi-file@x/"\n')
        with _mongo_env():
            check("bare PI_MONGODB_URI= line in the file also resolves",
                  oc.resolve_mongo_uri(env_file=env_file)[0]
                  == "mongodb+srv://pi-file@x/")


def test_ssh_remote_cmd():
    import opt_campaign as ocamp
    ex = ocamp.SSHExecutor("pi@zero", "~/powder-doser", None, None)
    cmd = ex._remote_cmd(["--fetch", "aaaa-bbbb",
                          "--params", '{"a": 1}'])
    check("~ stays expandable in cd (not swallowed by quoting)",
          "cd ~/powder-doser " in cmd and "'~" not in cmd)
    check("credential file sourced for non-interactive SSH",
          ". ~/.config/powder-doser/env; " in cmd)
    check("venv python preferred with python3 fallback",
          'PY=~/powder-doser-venv/bin/python; [ -x "$PY" ] || '
          "PY=python3" in cmd)
    check("script args are shell-quoted",
          "'{\"a\": 1}'" in cmd and "scripts/opt_dose_capture.py" in cmd)
    spaced = ocamp.SSHExecutor("pi@zero", "~/my repo", None, None,
                               remote_python="/opt/py 3/bin/python")
    cmd2 = spaced._remote_cmd([])
    check("paths with spaces still quote safely",
          "cd ~/'my repo' " in cmd2 and "PY='/opt/py 3/bin/python';" in cmd2)


def main():
    for fn in (test_firmware_set_lines, test_penalization,
               test_jam_classification, test_mongo_uri_resolution,
               test_ssh_remote_cmd, test_executor_end_to_end,
               test_shared_pico_guards, test_firmware_id_in_sync):
        print(fn.__name__)
        fn()
    if _FAILURES:
        print("\n{} check(s) FAILED: {}".format(len(_FAILURES),
                                                "; ".join(_FAILURES)))
        return 1
    print("\nall opt_dose_capture checks pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
