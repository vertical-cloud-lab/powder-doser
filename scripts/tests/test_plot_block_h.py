"""Checks for the Block H dose-accuracy figure.

The failure this file mostly exists to prevent is a *derived* title that
stops being derived.  Three separate panel titles in this repo have
asserted something the data contradicted (2026-08-05 twice, 2026-08-20),
so the scaling headline is pinned against synthetic data with a known
answer, in both directions.

Run:  python3 scripts/tests/test_plot_block_h.py
"""

import json
import sys
import tempfile
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))

import plot_block_h as ph                                       # noqa: E402

_FAILURES = []


def check(name, cond, detail=""):
    if cond:
        print("  ok   {}".format(name))
    else:
        print("  FAIL {} {}".format(name, detail))
        _FAILURES.append(name)


def doc(doses, read_path="bracket", powder="salt", started="2026-09-03T00"):
    return {
        "powder_id": powder,
        "started_utc": started + ":00:00+00:00",
        "parameters": {"config.dose_read_path": read_path},
        "doses": doses,
    }


def dose(target, delivered, status="ok", block="H", elapsed=20.0, taps=0):
    return {"target_g": target, "dispensed_g": delivered, "status": status,
            "block": block, "elapsed_s": elapsed, "taps": taps}


def write(tmp, name, payload):
    path = Path(tmp) / name
    path.write_text(json.dumps(payload))
    return str(path)


def test_unfinished_doses_are_excluded():
    """A dose that never dosed is not a dose-accuracy measurement."""
    with tempfile.TemporaryDirectory() as tmp:
        p = write(tmp, "r.json", doc([
            dose(0.050, 0.0494),
            dose(0.050, 0.0000, status="scale-error"),
            dose(0.050, 1.5410, status="not-tared"),
        ]))
        doses = ph.load_doses([p])
    check("scale-error and not-tared doses are dropped", len(doses) == 1,
          "kept {}".format(len(doses)))
    check("the phantom 1.5410 g overshoot never reaches the figure",
          all(d["delivered_g"] < 0.1 for d in doses))


def test_fixed_mass_error_is_described_as_such():
    groups = ph.by_target([
        {"target_g": 0.050, "error_g": 0.004, "status": "ok"},
        {"target_g": 1.000, "error_g": -0.004, "status": "ok"},
    ])
    head = ph.scaling_headline(groups)
    check("constant absolute error reads as constant", "constant" in head,
          head)
    check("and says relative error falls", "falls" in head, head)


def test_proportional_error_is_described_as_such():
    groups = ph.by_target([
        {"target_g": 0.050, "error_g": 0.004, "status": "ok"},
        {"target_g": 1.000, "error_g": 0.080, "status": "ok"},   # 20x
    ])
    head = ph.scaling_headline(groups)
    check("proportional error is not called constant",
          "constant" not in head, head)
    check("proportional error reads as proportional",
          "proportion" in head, head)


def test_single_target_makes_no_scaling_claim():
    groups = ph.by_target([{"target_g": 0.050, "error_g": 0.004,
                            "status": "ok"}])
    head = ph.scaling_headline(groups)
    check("one target claims no scaling law",
          "no scaling statement" in head, head)


def test_missing_block_field_is_not_a_question_mark():
    """Older Block G documents have no per-dose block letter."""
    with tempfile.TemporaryDirectory() as tmp:
        d = dose(1.000, 0.9953)
        d.pop("block")
        p = write(tmp, "g.json", doc([d], read_path=None))
        doses = ph.load_doses([p])
    check("a dose with no block letter is labelled G, not '?'",
          doses[0]["block"] == "G", doses[0]["block"])


def test_read_path_defaults_to_the_old_one():
    """A document predating the flag was collected with read_stable."""
    with tempfile.TemporaryDirectory() as tmp:
        payload = doc([dose(1.000, 0.9953)])
        payload["parameters"] = {}
        p = write(tmp, "old.json", payload)
        doses = ph.load_doses([p])
    check("a run without the flag is read_stable, not silently 'bracket'",
          doses[0]["read_path"] == "read_stable", doses[0]["read_path"])


def test_figure_builds_and_mixed_read_paths_are_disclosed():
    with tempfile.TemporaryDirectory() as tmp:
        new = write(tmp, "new.json", doc(
            [dose(0.050, 0.0494), dose(0.200, 0.1987)],
            read_path="bracket"))
        old = write(tmp, "old.json", doc(
            [dose(1.000, 0.9953, block="G")], read_path="read_stable",
            started="2026-08-12T00"))
        out = str(Path(tmp) / "fig.png")
        groups = ph.build(out, [new, old])
        check("figure is written", Path(out).exists() and
              Path(out).stat().st_size > 10000)
        check("three targets are grouped", len(groups) == 3,
              "{} groups".format(len(groups)))
        paths = {d["read_path"] for _, ds in groups for d in ds}
        check("both read paths survive into the figure data",
              paths == {"bracket", "read_stable"}, str(paths))


def main():
    for fn in (test_unfinished_doses_are_excluded,
               test_fixed_mass_error_is_described_as_such,
               test_proportional_error_is_described_as_such,
               test_single_target_makes_no_scaling_claim,
               test_missing_block_field_is_not_a_question_mark,
               test_read_path_defaults_to_the_old_one,
               test_figure_builds_and_mixed_read_paths_are_disclosed):
        print(fn.__name__)
        fn()
    if _FAILURES:
        print("\n{} check(s) FAILED: {}".format(len(_FAILURES),
                                                ", ".join(_FAILURES)))
        return 1
    print("\nall Block H figure checks pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
