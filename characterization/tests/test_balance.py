"""Tests for balance line-format parsing.

Getting the stability flag backwards would be a silent disaster: every
reading would be labelled settled, the analysis would report a beautiful
noise floor, and none of it would be true.  Each preset is therefore
pinned to a stable and an unstable example.
"""

from __future__ import annotations

import unittest

from characterization.balance import FORMATS


class FormatTests(unittest.TestCase):
    def parse(self, name, line):
        return FORMATS[name].parse(line, t=1.0)

    def test_mtsics_stable_and_dynamic(self) -> None:
        stable = self.parse("mtsics", "S S      1.23456 g")
        self.assertIsNotNone(stable)
        self.assertAlmostEqual(stable.grams, 1.23456)
        self.assertTrue(stable.stable)
        dynamic = self.parse("mtsics", "S D      1.23400 g")
        self.assertFalse(dynamic.stable)

    def test_mtsics_negative(self) -> None:
        reading = self.parse("mtsics", "S S     -0.00123 g")
        self.assertAlmostEqual(reading.grams, -0.00123)

    def test_and_stable_and_unstable(self) -> None:
        stable = self.parse("and", "ST,+00012.345 g")
        self.assertAlmostEqual(stable.grams, 12.345)
        self.assertTrue(stable.stable)
        unstable = self.parse("and", "US,+00012.300 g")
        self.assertFalse(unstable.stable)
        # Overload is not stability, whatever the comma format suggests.
        self.assertFalse(self.parse("and", "OL,+99999.9 g").stable)

    def test_sbi_trailing_question_mark_means_unstable(self) -> None:
        stable = self.parse("sbi", "+   123.456 g")
        self.assertAlmostEqual(stable.grams, 123.456)
        self.assertTrue(stable.stable)
        unstable = self.parse("sbi", "+   123.456 g ?")
        self.assertIsNotNone(unstable)
        self.assertFalse(unstable.stable)

    def test_unit_conversion_to_grams(self) -> None:
        self.assertAlmostEqual(self.parse("mtsics", "S S 5.0 mg").grams, 0.005)
        self.assertAlmostEqual(self.parse("mtsics", "S S 1.5 kg").grams, 1500.0)

    def test_garbage_returns_none_rather_than_guessing(self) -> None:
        for line in ("", "\x00\x11", "hello world", "S"):
            self.assertIsNone(self.parse("mtsics", line),
                              "parsed garbage: {!r}".format(line))

    def test_raw_line_is_preserved(self) -> None:
        reading = self.parse("mtsics", "S S      1.23456 g\r\n")
        self.assertEqual(reading.raw, "S S      1.23456 g")


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
