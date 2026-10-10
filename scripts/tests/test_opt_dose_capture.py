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
# What PR #154's refill runner adds to its RESULT line.
REFILL_SECTION = {
    "id": "refill-tap/2026-10-06", "refills": 2, "refill_deg": 20.0,
    "refill_g": 0.0071, "refill_max_g": 0.0042, "tap_cycles": 9,
    "tap_mean_g": 0.0011,
    "events": [{"n": 1, "t_s": 61.2, "deg": 10.0, "after_tap": 2,
                "mass_before_g": 0.4551, "delivered_g": 0.0042,
                "avg_yield_g": 0.0005, "need_g": 0.0399}],
    "params": dict(oc.REFILL_DEFAULTS),
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
    # what a fresh boot of each runner module reports
    BOOT_FW = {"main_trickle": oc.FIRMWARE_ID,
               "main_trickle_refill": oc.REFILL_FIRMWARE_ID}

    def __init__(self, port, baud, timeout=0.25, exclusive=False):
        if FakeSerial.lock_error:
            raise OSError(11, "Could not exclusively lock port {}: [Errno "
                              "11] Resource temporarily unavailable"
                          .format(port))
        FakeSerial.instances += 1
        FakeSerial.last = self
        self.exclusive = exclusive
        self.mode = FakeSerial.mode
        self.fw = FakeSerial.fw
        self.boot_line = None
        self.raw_mode = False
        self.queue = []
        self.set_seen = []
        self.writes = []
        self.closed = False

    def _listing(self):
        return ((["firmware: {}".format(self.fw)]
                 if self.fw else [])
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
                module = ("main_trickle_refill"
                          if "import main_trickle_refill" in line
                          else "main_trickle")
                self.fw = FakeSerial.BOOT_FW[module]
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
            doc = dict(RESULT_DOC, fw=self.fw)
            if self.fw == oc.REFILL_FIRMWARE_ID:
                doc["refill"] = REFILL_SECTION
            self.queue += ["[dose] trickle-tap dose to 0.5000 g",
                           "=== stage 1 'bulk': ...",
                           "RESULT " + json.dumps(doc)]
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


BULK_TAP_PARAMS = {"bulk_tap": "2hz", "bulk_tilt_deg": 40.0,
                   "bulk_rpm": 100.0, "bulk_min_rpm": 10.0,
                   "bulk_taper_start_g": 0.2, "bulk_stop_margin_g": 0.02,
                   "tap_tilt_deg": 15.0, "tolerance_g": 0.003,
                   "tau_afterflow_s": 0.83}


def test_firmware_set_lines():
    lines = oc.firmware_set_lines(oc.validate_params(PARAMS))
    check("categoricals map to boolean knobs",
          "set bulk_tap 0" in lines and "set trickle_tap 1" in lines)
    check("tau_afterflow_s rides along, last",
          lines[-1] == "set tau_afterflow_s 0.83")
    check("all 8 searched knobs + the PI-trickle switch + tau pushed",
          len(lines) == 10 and "set trickle_enabled 1" in lines)


def test_bulk_tap_variant():
    check("each parameter set names its variant",
          oc.variant_of(PARAMS) == oc.VARIANT_THREE_STAGE
          and oc.variant_of(BULK_TAP_PARAMS) == oc.VARIANT_BULK_TAP)
    clean = oc.validate_params(BULK_TAP_PARAMS)
    lines = oc.firmware_set_lines(clean)
    check("bulk-tap push: 8 knobs, trickle_enabled 0, tau last",
          len(lines) == 10 and "set trickle_enabled 0" in lines
          and "set bulk_stop_margin_g 0.02" in lines
          and "set bulk_min_rpm 10" in lines
          and lines[-1] == "set tau_afterflow_s 0.83"
          and not any("trickle_tilt" in l or "trickle_start" in l
                      for l in lines))
    for bad, why in (
            (dict(BULK_TAP_PARAMS, trickle_tilt_deg=15.0), "a trim knob"),
            ({k: v for k, v in BULK_TAP_PARAMS.items()
              if k != "bulk_stop_margin_g"}, "a missing margin")):
        try:
            oc.validate_params(bad)
            ok = False
        except ValueError:
            ok = True
        check("bulk-tap params with {} are rejected".format(why), ok)
    check("the bulk-tap box contains the shipped trickle_params values",
          all(b["bounds"][0] <= {"bulk_tilt_deg": 30.0, "bulk_rpm": 55.0,
                                 "bulk_min_rpm": 20.0,
                                 "bulk_taper_start_g": 0.1,
                                 "bulk_stop_margin_g": 0.01,
                                 "tap_tilt_deg": 10.0,
                                 "tolerance_g": 0.005}[b["name"]]
              <= b["bounds"][1]
              for b in oc.BULK_TAP_SEARCH_SPACE_AX if "bounds" in b))


FROZEN = {"trickle_kp": 250.0, "k_sigma": 1.0, "log_to_flash": True,
          "bulk_poll_ms": 250, "goal_mass_g": 0.75, "tau_afterflow_s": 0.3,
          "bulk_rpm": 55.0, "trickle_tap": False, "note": "text"}


def test_frozen_snapshot_helpers():
    lines = oc.frozen_set_lines(FROZEN, skip=oc.SEARCHED_FIRMWARE_KEYS)
    check("frozen push: bools as 0/1, ints and floats as numbers",
          "set log_to_flash 1" in lines and "set bulk_poll_ms 250" in lines
          and "set trickle_kp 250" in lines)
    check("frozen push leaves out the target, searched knobs, and text",
          not any(l.split()[1] in ("goal_mass_g", "bulk_rpm", "trickle_tap",
                                   "note") for l in lines))
    check("frozen push carries the tuned tau (screening runs on it)",
          "set tau_afterflow_s 0.3" in lines)
    import opt_campaign as ocamp
    base = oc.baseline_params(ocamp.frozen_snapshot())
    check("baseline = trickle_params.py's hand-tuned values",
          base == {"bulk_tap": "off", "trim_tap": "off",
                   "bulk_tilt_deg": 30.0, "trickle_tilt_deg": 15.0,
                   "tap_tilt_deg": 10.0, "bulk_rpm": 55.0,
                   "trickle_start_remaining_g": 0.25,
                   "tolerance_g": 0.005}
          if os.path.isdir(ocamp.FIRMWARE_DIR) else True)


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

    # A dose whose executor died after opening the Pico session: the raw
    # serial log exists, the trial document does not.
    with open(os.path.join(tmp, "salt-test", "serial_dead-1.log"), "w") as f:
        f.write("--- session ---\n")
    code5, lines5 = _run_capture(["--fetch", "dead-1", "--campaign-id",
                                  "salt-test", "--out", tmp])
    check("--fetch: executor died mid-dose -> interrupted, exit 3",
          code5 == 3 and json.loads(lines5[0])["status"] == "interrupted")

    import opt_dose_capture as odc
    real_pid = odc.live_dose_pid
    odc.live_dose_pid = lambda uuid: 4242 if uuid == "live-1" else None
    try:
        code6, lines6 = _run_capture(["--fetch", "live-1", "--campaign-id",
                                      "salt-test", "--out", tmp])
        before = FakeSerial.doses
        code7, lines7 = _run_capture(_dose_argv(tmp, "live-1"))
    finally:
        odc.live_dose_pid = real_pid
    check("--fetch: dose still running -> in-progress, exit 5",
          code6 == 5 and json.loads(lines6[0])["status"] == "in-progress")
    check("same uuid while it is still dosing: not started twice",
          code7 == 5 and FakeSerial.doses == before
          and json.loads(lines7[0])["status"] == "in-progress")
    check("live_dose_pid scans this host without raising",
          real_pid("no-such-uuid") is None)


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

    code, summ, port, dosed = run("runner", "t-frozen", "--frozen",
                                  json.dumps(FROZEN))
    keys = [k for k, _v in port.set_seen]
    check("--frozen: snapshot pushed first, searched knobs + tau on top",
          summ["status"] == "ok" and keys[0] == "bulk_poll_ms"
          and keys.index("trickle_kp") < keys.index("bulk_tap")
          and keys[-1] == "tau_afterflow_s"
          and ("tau_afterflow_s", "0.3") in port.set_seen
          and ("tau_afterflow_s", "0.83") == port.set_seen[-1])
    check("--frozen: the target and the searched knobs are not pushed "
          "from the snapshot", keys.count("bulk_rpm") == 1
          and "goal_mass_g" not in keys and "note" not in keys)

    stale = dict(FROZEN, trickle_enabled=True, bulk_stop_margin_g=0.01)
    _fake_pico("runner")
    code, lines = _run_capture(
        ["--powder-id", "salt", "--target-g", "0.5", "--campaign-id",
         "salt-bulktap-test", "--trial", "t-bulktap", "--params",
         json.dumps(BULK_TAP_PARAMS), "--frozen", json.dumps(stale),
         "--out", tmp, "--no-upload"])
    port = FakeSerial.last
    keys = [k for k, _v in port.set_seen]
    check("bulk-tap trial: the snapshot's trickle_enabled/margin are not "
          "pushed, the variant's are, after the snapshot",
          json.loads(lines[0])["status"] == "ok"
          and keys.count("trickle_enabled") == 1
          and ("trickle_enabled", "0") in port.set_seen
          and ("bulk_stop_margin_g", "0.02") in port.set_seen
          and keys.count("bulk_stop_margin_g") == 1
          and keys.index("trickle_kp") < keys.index("trickle_enabled"))

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


MARGIN_PARAMS = dict(PARAMS, cutoff_margin_g=0.012)


def test_margin_variant():
    """Section 7: the three-stage dose with the trickle's cutoff margin
    searched -- a 9th knob, pushed per trial like the other 8."""
    check("8 three-stage knobs + cutoff_margin_g name the margin variant; "
          "8 alone stay three-stage",
          oc.variant_of(MARGIN_PARAMS) == oc.VARIANT_THREE_STAGE_MARGIN
          and oc.variant_of(PARAMS) == oc.VARIANT_THREE_STAGE)
    lines = oc.firmware_set_lines(oc.validate_params(MARGIN_PARAMS))
    check("margin push: 9 knobs + the PI-trickle switch + tau last",
          len(lines) == 11 and "set cutoff_margin_g 0.012" in lines
          and "set trickle_enabled 1" in lines
          and lines[-1] == "set tau_afterflow_s 0.83")
    try:
        oc.validate_params(MARGIN_PARAMS, oc.VARIANT_THREE_STAGE)
        ok = False
    except ValueError:
        ok = True
    check("a three-stage campaign refuses a margin value", ok)
    box = {b["name"]: b["bounds"] for b in oc.MARGIN_SEARCH_SPACE_AX
           if "bounds" in b}
    check("margin box 0-35 mg: the hand-tuned 35 mg is its top edge",
          box["cutoff_margin_g"] == [0.0, 0.035]
          and [b for b in oc.MARGIN_SEARCH_SPACE_AX
               if b["name"] != "cutoff_margin_g"] == oc.SEARCH_SPACE_AX)

    _fake_pico("runner")
    tmp = tempfile.mkdtemp(prefix="optdose-margin-")
    code, lines = _run_capture(
        ["--powder-id", "salt", "--target-g", "0.5", "--campaign-id",
         "salt-margin-test", "--trial", "t-margin", "--params",
         json.dumps(MARGIN_PARAMS), "--frozen",
         json.dumps(dict(FROZEN, cutoff_margin_g=0.035)), "--out", tmp,
         "--no-upload"])
    port = FakeSerial.last
    keys = [k for k, _v in port.set_seen]
    check("executor: the trial's margin pushed once, after the snapshot "
          "(whose 35 mg is left out)",
          json.loads(lines[0])["status"] == "ok"
          and keys.count("cutoff_margin_g") == 1
          and ("cutoff_margin_g", "0.012") in port.set_seen
          and keys.index("trickle_kp") < keys.index("cutoff_margin_g"))


def _firmware_source(name):
    path = os.path.join(os.path.dirname(os.path.dirname(_HERE)),
                        "hardware", "test-module", "firmware",
                        "trickle_tap", name)
    if not os.path.exists(path):
        return None
    with open(path) as f:
        return f.read()


def test_refill_endgame():
    """PR #154's refill-tap endgame as an opt-in production option: its
    own runner, swapped in and out without --takeover, never in a
    campaign dose."""
    params_src = _firmware_source("refill_params.py")
    tap_src = _firmware_source("refill_tap.py")
    if params_src is None or tap_src is None:
        print("  SKIP firmware source not checked out here")
    else:
        ns = {}
        exec(params_src, ns)
        knobs = {k.lower(): v for k, v in ns.items()
                 if k.isupper() and not k.startswith("_")}
        check("opt_common.REFILL_DEFAULTS == refill_params.py",
              knobs == oc.REFILL_DEFAULTS)
        m = re.search(r'^REFILL_ID = "([^"]+)"', tap_src, re.M)
        check("opt_common.REFILL_FIRMWARE_ID == this build + refill_tap's "
              "REFILL_ID", m is not None and oc.REFILL_FIRMWARE_ID
              == oc.FIRMWARE_ID + "+" + m.group(1))
    check("--refill-set parsing: typed like the defaults, unknown keys "
          "refused",
          oc.refill_override("refill_deg=15") == ("refill_deg", 15.0)
          and oc.refill_override("refill_max=8") == ("refill_max", 8)
          and oc.refill_override("refill_enabled=0")
          == ("refill_enabled", False))
    try:
        oc.refill_override("tap_tilt_deg=5")
        ok = False
    except ValueError:
        ok = True
    check("--refill-set refuses a non-refill knob", ok)

    tmp = tempfile.mkdtemp(prefix="optdose-refill-")
    _fake_pico("runner")                  # the stock runner is up
    code, lines = _run_capture(_dose_argv(
        tmp, "t-refill", "--mode", "production", "--endgame", "refill",
        "--refill-set", "refill_deg=15"))
    port = FakeSerial.last
    summ = json.loads(lines[0])
    keys = [k for k, _v in port.set_seen]
    check("--endgame refill: this build's idle stock runner is swapped "
          "for main_trickle_refill without --takeover",
          summ["status"] == "ok" and any(b"\x03" in w for w in port.writes)
          and "import main_trickle_refill" in (port.boot_line or ""))
    check("--endgame refill: every refill knob pushed after the trial's "
          "values, --refill-set applied",
          [k for k in keys if k.startswith("refill_")]
          == sorted(oc.REFILL_DEFAULTS)
          and ("refill_enabled", "1") in port.set_seen
          and ("refill_deg", "15") in port.set_seen
          and keys.index("tau_afterflow_s") < keys.index("refill_avg_taps"))
    with open(os.path.join(tmp, "salt-test",
                           "trial_t-refill.json")) as f:
        doc = json.load(f)
    check("trial doc: the RESULT's refill section and the endgame "
          "covariates", doc["refill"]["refills"] == 2
          and doc["covariates"]["endgame"] == "refill"
          and doc["covariates"]["refill_params"]["refill_deg"] == 15.0
          and doc["device"]["firmware"] == oc.REFILL_FIRMWARE_ID)

    _fake_pico("runner", fw=oc.REFILL_FIRMWARE_ID)   # refill runner up
    code, lines = _run_capture(_dose_argv(tmp, "t-after-refill"))
    port = FakeSerial.last
    check("a campaign dose finding the refill runner swaps the stock one "
          "back, no --takeover, no refill knobs",
          json.loads(lines[0])["status"] == "ok"
          and "import main_trickle;" in (port.boot_line or "")
          and not any(k.startswith("refill_") for k, _v in port.set_seen))

    refused = 0
    for extra in (("--endgame", "refill"),                  # mode bo
                  ("--mode", "production", "--refill-set",
                   "refill_deg=15"),                        # no endgame
                  ("--mode", "production", "--endgame", "refill",
                   "--refill-set", "tap_tilt_deg=5")):
        _fake_pico("runner")
        try:
            with contextlib.redirect_stderr(io.StringIO()):
                _run_capture(_dose_argv(tmp, "t-refused", *extra))
        except SystemExit:
            refused += FakeSerial.last is None
    check("--endgame refill outside production, --refill-set without it, "
          "and an unknown refill knob are refused before the port opens",
          refused == 3)

    import dose
    cache = tempfile.mkdtemp(prefix="optdose-profiles-")
    profile = {"profile_id": "salt-test-bo-005", "powder_id": "salt",
               "target_g": 0.5, "validated": True,
               "parameters": {k: v for k, v in PARAMS.items()
                              if k != "tau_afterflow_s"},
               "tau_afterflow_s": 0.8338, "frozen_params": FROZEN}
    with open(os.path.join(cache, "salt.json"), "w") as f:
        json.dump(profile, f)
    real_cache, real_env = dose.PROFILE_CACHE, oc.MONGODB_ENV_FILE
    dose.PROFILE_CACHE = cache
    oc.MONGODB_ENV_FILE = os.path.join(cache, "no-such-env")
    try:
        with _mongo_env():
            _fake_pico("runner")
            out, err = io.StringIO(), io.StringIO()
            with contextlib.redirect_stdout(out), \
                    contextlib.redirect_stderr(err):
                code = dose.main(["--powder-id", "salt", "--target-g", "0.5",
                                  "--endgame", "refill", "--refill-set",
                                  "refill_min_to_go_g=0.015", "--out", tmp,
                                  "--no-upload"])
    finally:
        dose.PROFILE_CACHE, oc.MONGODB_ENV_FILE = real_cache, real_env
    port = FakeSerial.last
    summ = json.loads(out.getvalue().strip().splitlines()[-1])
    with open(os.path.join(tmp, "production-salt", "trial_{}.json".format(
            summ["trial_uuid"]))) as f:
        doc = json.load(f)
    check("dose.py --endgame refill: the profile's values + tau, then the "
          "refill knobs, on the refill runner",
          code == 0 and summ["status"] == "ok"
          and "import main_trickle_refill" in (port.boot_line or "")
          and ("tau_afterflow_s", "0.8338") in port.set_seen
          and ("refill_min_to_go_g", "0.015") in port.set_seen
          and ("refill_enabled", "1") in port.set_seen
          and doc["covariates"]["endgame"] == "refill"
          and doc["covariates"]["profile_id"] == "salt-test-bo-005"
          and doc["refill"]["refills"] == 2
          and "2 refill(s)" in err.getvalue())


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

    # An older executor on the Zero answers --fetch with a short dict.
    real_run = ocamp.subprocess.run
    ocamp.subprocess.run = lambda *a, **k: types.SimpleNamespace(
        stdout='{"kind": "opt_trial_summary", "trial_uuid": "u1", '
               '"status": "not-found", "infra_error": true}\n',
        stderr="", returncode=3)
    try:
        short = ex.fetch("u1", "salt-test")
    finally:
        ocamp.subprocess.run = real_run
    check("a short status answer is filled out to the summary shape",
          short["status"] == "not-found" and short["t_total_s"] is None
          and short["stop_events"] == [] and short["jam"] is False)


def main():
    for fn in (test_firmware_set_lines, test_bulk_tap_variant,
               test_frozen_snapshot_helpers,
               test_penalization,
               test_jam_classification, test_mongo_uri_resolution,
               test_ssh_remote_cmd, test_executor_end_to_end,
               test_shared_pico_guards, test_firmware_id_in_sync,
               test_margin_variant, test_refill_endgame):
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
