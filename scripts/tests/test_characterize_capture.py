"""Tests for the host capture parser/statistics (issue #130).

The device side of the contract is the ``Characterizer`` in
``hardware/test-module/firmware/characterize.py``; these tests run it
against the simulated rig from ``sim/test_characterize.py`` and feed
its emitted lines through the host parser, so a format drift on either
side fails here.

Run from the repo root (stdlib only)::

    python scripts/tests/test_characterize_capture.py

or via pytest.
"""

import argparse
import csv
import json
import math
import os
import sys
import tempfile

_ROOT = os.path.join(os.path.dirname(__file__), "..", "..")
sys.path.insert(0, os.path.join(_ROOT, "scripts"))
sys.path.insert(0, os.path.join(_ROOT, "hardware", "test-module",
                                "firmware", "sim"))

import characterize_capture as cap
import test_characterize as sim


def _captured(angles=(0, 45, 90), points=4, **overrides):
    _, lines, status = sim._run_sweep(angles, points, **overrides)
    trials, summaries, meta, markers = [], [], {}, []
    for line in lines:
        parsed = cap.parse_line(line)
        if parsed is None:
            continue
        kind, payload = parsed
        if kind == "trial":
            trials.append(payload)
        elif kind == "device_summary":
            summaries.append(payload)
        elif kind == "meta":
            meta[payload[0]] = payload[1]
        elif kind == "run":
            markers.append(payload)
    return trials, summaries, meta, markers, status


def test_parse_roundtrip():
    trials, summaries, meta, markers, status = _captured()
    assert status == "ok"
    assert markers[0][0] == "BEGIN" and markers[-1] == ["END", "ok"]
    assert meta["points_per_angle"] == "4"
    assert meta["angles_deg"] == "0;45;90"
    # 3 angles x (2 baseline + 4 rotation + 4 refeed + 4 tap)
    assert len(trials) == 3 * 14
    assert len(summaries) == 3 * 4
    row = trials[0]
    assert set(row) == set(cap.TRIAL_FIELDS)
    assert isinstance(row["delta_g"], float)


def test_host_summary_pools_refeed_with_rotation():
    trials, _, _, _, _ = _captured(angles=(45,), points=4)
    summary = {(r["angle_deg"], r["phase"]): r
               for r in cap.summarize(trials)}
    rot = summary[(45.0, "rotation")]
    pooled = summary[(45.0, "rotation+refeed")]
    assert rot["n"] == 4
    assert pooled["n"] == 8          # refeed rows double the sample size
    expected = sim.GPR_BASE + sim.GPR_PER_DEG * 45
    assert abs(pooled["mean_g"] - expected) < 2e-4
    tap = summary[(45.0, "tap")]
    assert abs(tap["mean_g"] - sim.LIP_LOAD_G / 2.0) < 2e-4
    # SEM shrinks with the pooled sample (or at worst equals: the ideal
    # sim has ~zero spread; guard the relation rather than exact values)
    if rot["sem_g"] and pooled["sem_g"]:
        assert pooled["sem_g"] <= rot["sem_g"] + 1e-12


def test_host_summary_matches_device_summary():
    trials, device, _, _, _ = _captured(angles=(30,), points=6)
    host = {(r["angle_deg"], r["phase"]): r
            for r in cap.summarize(trials)}
    for row in device:
        key = (row["angle_deg"], row["phase"])
        assert key in host
        assert host[key]["n"] == row["n"]
        for field in ("mean_g", "std_g", "sem_g", "min_g", "max_g"):
            a, b = host[key][field], row[field]
            if a is None or b is None:
                assert a == b
            else:
                # device rows are rounded to 4 decimals on emission
                assert abs(a - b) < 1e-4, (key, field, a, b)


def test_lowflow_rows_excluded_from_stats():
    trials = [
        {"angle_deg": 10.0, "phase": "rotation", "trial": i,
         "action": "360.0", "before_g": 0.0, "after_g": d, "delta_g": d,
         "flag": flag, "t_ms": i}
        for i, (d, flag) in enumerate(
            [(0.05, ""), (0.0, "lowflow"), (0.05, ""), (0.0, "lowflow")])
    ]
    summary = {r["phase"]: r for r in cap.summarize(trials)
               if r["angle_deg"] == 10.0}
    assert summary["rotation"]["n"] == 2
    assert abs(summary["rotation"]["mean_g"] - 0.05) < 1e-12
    assert summary["rotation+refeed"]["n"] == 2


def test_sample_stats():
    n, mean, std, sem, lo, hi = cap.sample_stats([1.0, 2.0, 3.0, 4.0])
    assert n == 4 and mean == 2.5 and lo == 1.0 and hi == 4.0
    assert abs(std - math.sqrt(5.0 / 3.0)) < 1e-12
    assert abs(sem - std / 2.0) < 1e-12
    assert cap.sample_stats([7.0])[2] is None      # std undefined at n=1
    assert cap.sample_stats([])[0] == 0


def test_normalize_powder_id():
    assert cap.normalize_powder_id("Salt") == "salt"
    assert cap.normalize_powder_id("xanthan gum") == "xanthan-gum"
    assert cap.normalize_powder_id(" flour_00 ") == "flour_00"
    for bad in ("", "   ", "a/b", "-lead", "salt!", None):
        try:
            cap.normalize_powder_id(bad)
        except ValueError:
            pass
        else:
            raise AssertionError("accepted {!r}".format(bad))


def test_powder_id_on_document_and_files():
    """The powder ID lands in the run doc, the file names, and every
    CSV row -- the data stays attributable out of context."""
    trials, device, meta, _, _ = _captured(angles=(45,), points=2)
    host = cap.summarize(trials)
    args = argparse.Namespace(powder_id="salt", powder="table salt",
                              operator="wm", notes=None)
    doc = cap.build_run_document(meta, trials, device, host, "ok", args,
                                 "2026-07-21T00:00:00", "2026-07-21T00:20:00")
    assert doc["powder_id"] == "salt"
    with tempfile.TemporaryDirectory() as tmp:
        cap.write_outputs(tmp, "salt", trials, host, doc)
        with open(os.path.join(tmp, "trials_salt.csv")) as fh:
            rows = list(csv.DictReader(fh))
        assert rows and all(r["powder_id"] == "salt" for r in rows)
        assert set(rows[0]) == set(cap.OUT_TRIAL_FIELDS)
        with open(os.path.join(tmp, "summary_salt.csv")) as fh:
            srows = list(csv.DictReader(fh))
        assert srows and all(r["powder_id"] == "salt" for r in srows)
        with open(os.path.join(tmp, "run_salt.json")) as fh:
            assert json.load(fh)["powder_id"] == "salt"


def test_parse_line_rejects_garbage():
    assert cap.parse_line("") is None
    assert cap.parse_line("[rig] ready -- type 'h' for help") is None
    assert cap.parse_line("CSV,not,enough,fields") is None
    kind, payload = cap.parse_line("PROMPT,refill the hopper")
    assert kind == "prompt" and payload == "refill the hopper"


def main():
    tests = [(name, fn) for name, fn in sorted(globals().items())
             if name.startswith("test_") and callable(fn)]
    for name, fn in tests:
        fn()
        print("PASS {}".format(name))
    print("{} tests passed".format(len(tests)))


if __name__ == "__main__":
    main()
