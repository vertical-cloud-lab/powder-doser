"""Tests for the dose-run capture parser and document builder (issue #126).

The device side of the contract is
``hardware/test-module/firmware/pid_dose.py`` (``M,``/``D,``/``E,``/
``SUMMARY,`` lines); these tests pin the host side, including the
wrapper-stripping that makes a logged REPL session parse identically
to a raw stream -- a format drift on either side fails here.

Run from the repo root (stdlib only)::

    python scripts/tests/test_dose_run_capture.py

or via pytest.
"""

import io
import json
import os
import sys

_ROOT = os.path.join(os.path.dirname(__file__), "..", "..")
sys.path.insert(0, os.path.join(_ROOT, "scripts"))

import dose_run_capture as drc


# A miniature but complete run: metadata, pre-roll, a tare event, dosing
# with an unstable frame and a dropped poll, and the summary line.
STREAM = """\
M,controller,pid-v2
M,powder_id,salt
M,target_g,1.0
M,kp,150.0
M,ki,8.0
M,tol_g,0.002
E,20,preroll start (pre-zeroing absolute mass)
D,140,1.9243,S,0.0,0.00,0,preroll
D,235,1.9243,S,0.0,0.00,0,preroll
E,10079,tare (Z) sent
D,10787,0.0000,S,25.0,45.00,0,dose
D,10883,0.1240,U,25.0,45.00,0,dose
D,10979,nan,X,25.0,45.00,0,dose
D,11075,0.9990,U,25.0,12.00,1,dose
D,35045,1.0012,S,0.1,0.00,1,home
E,35143,final stable weigh: 1.0012 g
SUMMARY,status=ok,final_g=1.0012,target_g=1.0000,taps=1
"""


def _parsed(text=STREAM):
    return drc.parse_stream(io.StringIO(text))


def test_strip_wrapper_handles_repl_capture():
    assert drc.strip_wrapper("D,140,1.9243,S,0.0,0.00,0,preroll") == \
        "D,140,1.9243,S,0.0,0.00,0,preroll"
    assert drc.strip_wrapper("[   10.9s]   | D,140,1.9243,S,0.0,0.00,0,preroll") == \
        "D,140,1.9243,S,0.0,0.00,0,preroll"
    assert drc.strip_wrapper("[    3.9s]   | >>> M,controller,pid-v2") == \
        "M,controller,pid-v2"
    assert drc.strip_wrapper("   \n") == ""


def test_parse_line_kinds():
    kind, row = drc.parse_line("D,140,1.9243,S,1.5,45.00,3,dose")
    assert kind == "sample"
    assert row == {"t_ms": 140, "mass_g": 1.9243, "frame": "S",
                   "tilt_deg": 1.5, "rpm_cmd": 45.0, "taps_cum": 3,
                   "phase": "dose"}

    kind, payload = drc.parse_line("E,10079,tare (Z) sent")
    assert kind == "event" and payload == (10079, "tare (Z) sent")

    kind, payload = drc.parse_line("M,controller,pid-v2")
    assert kind == "meta" and payload == ("controller", "pid-v2")

    kind, payload = drc.parse_line(
        "SUMMARY,status=ok,final_g=1.0012,target_g=1.0000,taps=1")
    assert kind == "summary"
    assert payload == {"status": "ok", "final_g": 1.0012,
                       "target_g": 1.0, "taps": 1}

    assert drc.parse_line("[rig] ready -- type 'h' for help") is None
    # Wrong field count must not half-parse into a corrupt sample.
    assert drc.parse_line("D,140,1.9243,S,0.0") is None


def test_dropped_poll_becomes_null_not_nan():
    _, row = drc.parse_line("D,10979,nan,X,25.0,45.00,0,dose")
    assert row["mass_g"] is None and row["frame"] == "X"
    # The document must stay JSON-encodable (JSON has no NaN literal).
    doc = drc.build_run_document(_parsed())
    assert "NaN" not in json.dumps(doc)


def test_parse_stream_partitions_and_counts_noise():
    parsed = _parsed(STREAM + "[rig] ready\nTraceback (most recent call last)\n")
    assert len(parsed["samples"]) == 7
    assert len(parsed["events"]) == 3
    assert parsed["meta"]["controller"] == "pid-v2"
    assert parsed["summary"]["status"] == "ok"
    assert parsed["unparsed"] == 2


def test_stdin_is_teed_verbatim():
    sink = io.StringIO()
    drc.parse_stream(io.StringIO(STREAM), tee=sink)
    assert sink.getvalue() == STREAM


def test_rle_round_trip():
    values = ["preroll"] * 3 + ["dose"] * 4 + ["home"]
    encoded = drc.encode_rle(values)
    assert encoded == [["preroll", 3], ["dose", 4], ["home", 1]]
    assert drc.decode_rle(encoded) == values
    assert drc.encode_rle([]) == []


def test_build_run_document_shape():
    doc = drc.build_run_document(_parsed(), powder_id="salt",
                                 operator="wm",
                                 started_utc="2026-07-29T20:52:00Z")
    assert doc["schema_version"] == drc.SCHEMA_VERSION
    assert doc["doc_type"] == "dose_run"
    assert doc["powder_id"] == "salt"
    assert doc["controller"] == "pid-v2"
    assert doc["gains"] == {"target_g": 1.0, "kp": 150.0, "ki": 8.0,
                            "tol_g": 0.002}
    assert doc["n_samples"] == 7
    assert doc["duration_s"] == (35045 - 140) / 1000.0
    assert doc["events"][0] == {"t_ms": 20,
                                "text": "preroll start "
                                        "(pre-zeroing absolute mass)"}
    # powder_id is promoted out of the raw meta bag, gains are typed.
    assert "powder_id" not in doc["meta"] and "kp" not in doc["meta"]


def test_summary_gets_derived_error_and_tolerance():
    doc = drc.build_run_document(_parsed())
    assert doc["summary"]["error_mg"] == 1.2   # 1.2 mg, tol_g is 2 mg
    assert doc["summary"]["within_tolerance"] is True

    off = STREAM.replace("final_g=1.0012", "final_g=1.0300")
    doc = drc.build_run_document(_parsed(off))
    assert doc["summary"]["error_mg"] == 30.0
    assert doc["summary"]["within_tolerance"] is False


def test_series_round_trips_to_rows():
    parsed = _parsed()
    doc = drc.build_run_document(parsed)
    # t_ms stays a plain column; every value column is RLE'd.
    assert sorted(doc["series"]) == [
        "frame_rle", "mass_g_rle", "phase_rle", "rpm_cmd_rle", "t_ms",
        "taps_cum_rle", "tilt_deg_rle"]
    assert drc.samples_from_document(doc) == parsed["samples"]


def test_run_uid_is_stable_and_content_addressed():
    raw = drc.build_run_document(_parsed())["run_uid"]
    # Same run seen through a logged REPL session -> same uid.
    wrapped = "".join("[   {:5.1f}s]   | {}\n".format(i * 0.1, line)
                      for i, line in enumerate(STREAM.splitlines()))
    assert drc.build_run_document(_parsed(wrapped))["run_uid"] == raw
    # Host-side annotations must not change the identity of the run.
    annotated = drc.build_run_document(_parsed(), operator="wm",
                                       notes="auger 4")
    assert annotated["run_uid"] == raw
    # A different run does.
    other = STREAM.replace("final_g=1.0012", "final_g=0.9406")
    assert drc.build_run_document(_parsed(other))["run_uid"] != raw


def test_columnar_layout_beats_row_documents():
    """The layout choice should pay for itself on a realistic run.

    A 10 Hz HR-100A stream repeats each reading until it changes, so a
    4,450-sample run holds ~100 distinct mass values; the RLE columns
    have to exploit that, not just reshape it.
    """
    long_stream = "M,controller,pid-v2\nM,powder_id,salt\n"
    long_stream += "".join(
        "D,{},{:.4f},S,25.0,45.00,0,dose\n".format(i * 96, 0.5 + (i // 40) * 1e-3)
        for i in range(4450))
    parsed = _parsed(long_stream)
    columnar = len(json.dumps(drc.build_run_document(parsed)))
    rowwise = len(json.dumps(parsed["samples"]))
    assert columnar < 0.35 * rowwise


def main():
    tests = [(name, fn) for name, fn in sorted(globals().items())
             if name.startswith("test_") and callable(fn)]
    for name, fn in tests:
        fn()
        print("PASS {}".format(name))
    print("{} tests passed".format(len(tests)))


if __name__ == "__main__":
    main()
