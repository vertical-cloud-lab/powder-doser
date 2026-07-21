"""Unit tests for the parametric CAD model and the DFM feedback loop.

Run from the repo root::

    python -m unittest discover cad/tests

These tests are deliberately fast (no STL/STEP export, no slicing). They
exercise three things:

1. The parametric model builds without errors at default parameters.
2. The DFM check passes (no errors) at default parameters.
3. Deliberate parameter regressions -- making the trough wall thinner than
   the FDM minimum, and routing the slot path off the board -- are correctly
   caught by the DFM checks.
"""

from __future__ import annotations

import unittest
from dataclasses import replace

from cad.dfm import run_all
from cad.excavator import (
    ExcavatorParams,
    build_arm,
    build_assembly,
    build_cam_ramp,
    build_pin,
    build_slot_board,
    build_strike_off_bar,
    build_trough,
)


class BuildTests(unittest.TestCase):
    def test_parts_build_at_defaults(self) -> None:
        p = ExcavatorParams()
        for part_fn in (
            build_trough, build_arm, build_pin,
            build_strike_off_bar, build_cam_ramp, build_slot_board,
        ):
            with self.subTest(part=part_fn.__name__):
                obj = part_fn(p)
                vol = obj.val().Volume()
                self.assertGreater(vol, 0.0, f"{part_fn.__name__} has zero volume")

    def test_assembly_builds(self) -> None:
        asm = build_assembly()
        names = {c.name for c in asm.children}
        self.assertIn("trough", names)
        self.assertIn("arm_left", names)
        self.assertIn("arm_right", names)
        self.assertIn("pin", names)


class DFMTests(unittest.TestCase):
    def test_defaults_pass(self) -> None:
        results = run_all(ExcavatorParams())
        failures = [r for r in results if not r.ok and r.severity == "error"]
        self.assertFalse(
            failures,
            f"DFM should pass at default parameters; failures: "
            f"{[r.name for r in failures]}",
        )

    def test_thin_wall_fails(self) -> None:
        bad = replace(ExcavatorParams(), trough_wall=0.4)
        results = run_all(bad)
        names = [r.name for r in results if not r.ok and r.severity == "error"]
        self.assertIn("fdm.min_wall.trough", names)

    def test_slot_off_board_fails(self) -> None:
        bad = replace(
            ExcavatorParams(),
            slot_path=((10.0, 30.0), (5000.0, 30.0)),
        )
        results = run_all(bad)
        names = [r.name for r in results if not r.ok and r.severity == "error"]
        self.assertIn("kinematics.slot.waypoints_inside_board", names)

    def test_inverted_pendulum_fails(self) -> None:
        # Old defaults (pivot at -trough_radius/2 = -6.5 mm with the
        # heavy 6x6 lips) put the loaded CG above the pivot. This is
        # the Edison-v3 inverted-pendulum failure mode.
        bad = replace(
            ExcavatorParams(),
            pivot_offset_y=-6.5,
            bumper_height=6.0,
            bumper_chamfer=2.0,
            bumper_width=6.0,
        )
        results = run_all(bad)
        names = [r.name for r in results if not r.ok and r.severity == "error"]
        self.assertIn("physics.pendulum.cg_below_pivot", names)

    def test_cam_sensitivity_singularity_fails(self) -> None:
        # A short lever arm + a tilt target near the singularity must
        # blow the d(theta)/d(X) ceiling.
        bad = replace(
            ExcavatorParams(),
            cam_target_tilt_deg=80.0,
            cam_sensitivity_ceiling_deg_per_mm=15.0,
        )
        results = run_all(bad)
        names = [r.name for r in results if not r.ok and r.severity == "error"]
        self.assertIn("physics.cam.sensitivity", names)

    def test_sharp_slot_corner_fails(self) -> None:
        bad = replace(
            ExcavatorParams(),
            slot_path=((20.0, 30.0), (100.0, 30.0), (100.0, 10.0), (180.0, 10.0)),
        )
        results = run_all(bad)
        names = [r.name for r in results if not r.ok and r.severity == "error"]
        self.assertIn("kinematics.slot.peg_friction.corner_angle", names)

    def test_slot_x_reversal_warns(self) -> None:
        # Path that goes +X then -X requires a gantry-X reversal; this
        # should be flagged (not-ok at warning severity) by
        # kinematics.slot.gantry_x_only.
        bad = replace(
            ExcavatorParams(),
            slot_path=((20.0, 30.0), (180.0, 30.0), (50.0, 30.0)),
        )
        results = run_all(bad)
        match = next(r for r in results if r.name == "kinematics.slot.gantry_x_only")
        self.assertFalse(match.ok)
        self.assertEqual(match.severity, "warning")


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
