"""Tests for the firmware's runtime-parameter overlay.

Run from the repo root::

    python -m unittest discover characterization/tests

These load ``hardware/test-module/firmware/params.py`` directly, so the
firmware module is covered by the host test suite even though nothing
else in CI runs MicroPython.
"""

from __future__ import annotations

import json
import unittest

from characterization import firmware_params


class ParamsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.mod = firmware_params.load_params_module()
        self.params = firmware_params.make_params()

    def test_defaults_come_from_config(self) -> None:
        self.assertEqual(self.params["stepper_rpm"],
                         firmware_params.StubConfig.STEPPER_SPEED_RPM)
        self.assertEqual(self.params["tap_count"],
                         firmware_params.StubConfig.TAP_COUNT)

    def test_firmware_only_knobs_have_defaults(self) -> None:
        # deenergize_after and move_pad_ms have no config counterpart;
        # their defaults must reproduce the pre-#139 firmware behaviour.
        self.assertIs(self.params["deenergize_after"], False)
        self.assertEqual(self.params["move_pad_ms"], 2000)

    def test_set_coerces_strings(self) -> None:
        self.assertEqual(self.params.set("stepper_rpm", "45"), 45.0)
        self.assertIsInstance(self.params["stepper_rpm"], float)
        self.assertEqual(self.params.set("tap_count", "3"), 3)
        self.assertIsInstance(self.params["tap_count"], int)

    def test_bool_spellings(self) -> None:
        for text in ("1", "true", "on", "YES"):
            self.assertIs(self.params.set("deenergize_after", text), True)
        for text in ("0", "false", "off", "no"):
            self.assertIs(self.params.set("deenergize_after", text), False)

    def test_range_and_choice_enforcement(self) -> None:
        with self.assertRaises(self.mod.ParamError):
            self.params.set("stepper_rpm", 10_000)
        with self.assertRaises(self.mod.ParamError):
            self.params.set("stepper_rpm", 0)
        with self.assertRaises(self.mod.ParamError):
            self.params.set("tap_duty", 1.5)
        # The Tic only supports these step modes; 64 would be silently
        # clamped by the controller and desync the position shadow.
        with self.assertRaises(self.mod.ParamError):
            self.params.set("stepper_microsteps", 64)
        self.assertEqual(self.params.set("stepper_microsteps", 32), 32)

    def test_unknown_name_rejected(self) -> None:
        with self.assertRaises(self.mod.ParamError):
            self.params.set("stepper_rpmm", 30)
        with self.assertRaises(self.mod.ParamError):
            self.params.get("nope")

    def test_non_numeric_rejected(self) -> None:
        with self.assertRaises(self.mod.ParamError):
            self.params.set("stepper_rpm", "fast")

    def test_reset(self) -> None:
        self.params.set("stepper_rpm", 99)
        self.params.set("tap_count", 7)
        self.params.reset("stepper_rpm")
        self.assertEqual(self.params["stepper_rpm"],
                         firmware_params.StubConfig.STEPPER_SPEED_RPM)
        self.assertEqual(self.params["tap_count"], 7)
        self.params.reset()
        self.assertEqual(self.params["tap_count"],
                         firmware_params.StubConfig.TAP_COUNT)
        self.assertFalse(self.params.is_overridden("tap_count"))

    def test_snapshot_is_json_and_complete(self) -> None:
        self.params.set("stepper_rpm", 45)
        snapshot = json.loads(self.params.snapshot())
        self.assertEqual(snapshot["stepper_rpm"], 45.0)
        # Every knob must appear: a partial snapshot would mean a run log
        # that silently omits whatever was actually in force.
        self.assertEqual(sorted(snapshot), self.params.names())

    def test_missing_config_attr_falls_back_to_default(self) -> None:
        class Bare:
            pass

        params = self.mod.Params(Bare())
        # No config at all -> every knob still resolves (to None where the
        # spec has no default), rather than raising on attribute access.
        self.assertEqual(len(params.as_dict()), len(params.names()))
        self.assertEqual(params["move_pad_ms"], 2000)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
