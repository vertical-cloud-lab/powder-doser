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
import sys
import tempfile
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
    "dose_n": 5,
}


class FakeSerial:
    """Just enough of pyserial to satisfy PicoSession."""

    doses = 0
    instances = 0

    def __init__(self, port, baud, timeout=0.25):
        FakeSerial.instances += 1
        self.queue = []
        self.set_seen = []

    def write(self, data):
        line = data.decode(errors="replace").strip()
        if line == "s" or line == "":
            self.queue += ["stepper: 55 auger rpm",
                           "trickle parameters ('set <key> <value>'):",
                           "  bulk_rpm = 55.0"]
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
        if self.queue:
            return (self.queue.pop(0) + "\r\n").encode()
        return b""

    def close(self):
        pass


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
    sys.modules["serial"] = types.SimpleNamespace(Serial=FakeSerial)
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


def main():
    for fn in (test_firmware_set_lines, test_penalization,
               test_jam_classification, test_executor_end_to_end):
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
