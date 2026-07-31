"""Tests for scripts/scale_stream_capture.py (stdlib only).

Run with:  python scripts/tests/test_scale_stream_capture.py
"""

import os
import sys
import unittest
from datetime import datetime, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import scale_stream_capture as ssc  # noqa: E402


ANCHOR = datetime(2026, 7, 31, 6, 30, 0)


def sample(t_ms, grams, flag="S"):
    return ssc.Sample(t_ms, grams, flag)


class TestParsing(unittest.TestCase):
    def test_sample_row(self):
        kind, s = ssc.parse_line("S,1234,1.0361,S")
        self.assertEqual(kind, "S")
        self.assertEqual((s.t_ms, s.grams, s.flag), (1234, 1.0361, "S"))

    def test_unstable_and_missed(self):
        _, u = ssc.parse_line("S,10,0.9998,U")
        self.assertEqual(u.flag, "U")
        _, x = ssc.parse_line("S,20,nan,X")
        self.assertEqual(x.flag, "X")
        self.assertIsNone(x.grams)

    def test_overload_has_no_mass(self):
        _, o = ssc.parse_line("S,30,nan,O")
        self.assertEqual(o.flag, "O")
        self.assertIsNone(o.grams)

    def test_metadata_and_events(self):
        self.assertEqual(ssc.parse_line("M,poll_hz,5.0"), ("M", ("poll_hz", "5.0")))
        self.assertEqual(ssc.parse_line("E,8,stream start"), ("E", (8, "stream start")))

    def test_garbage_is_ignored(self):
        for line in ("", "\n", "Traceback (most recent call last):",
                     "S,abc,1.0,S", "S,1,1.0", "S,1,1.0,Z", "Q,1,2,3"):
            self.assertIsNone(ssc.parse_line(line), line)

    def test_repl_wrapper_is_stripped(self):
        # mpremote's raw REPL can glue OK/\x04 onto the first payload line;
        # without stripping, the first sample of every run is lost.
        kind, s = ssc.parse_line("OK\x04S,78,1.0361,S\r")
        self.assertEqual(kind, "S")
        self.assertEqual(s.t_ms, 78)

    def test_meta_values_stay_numeric(self):
        self.assertEqual(ssc.coerce_meta("19200"), 19200)
        self.assertEqual(ssc.coerce_meta("5.0"), 5.0)
        self.assertEqual(ssc.coerce_meta("scale-idle-v1"), "scale-idle-v1")


class TestDeadBand(unittest.TestCase):
    def test_first_sample_always_kept(self):
        band = ssc.DeadBand(heartbeat_s=60.0)
        self.assertTrue(band.keep(sample(0, 1.0)))

    def test_repeat_suppressed_change_kept(self):
        band = ssc.DeadBand(heartbeat_s=60.0)
        band.keep(sample(0, 1.0))
        self.assertFalse(band.keep(sample(200, 1.0)))
        self.assertTrue(band.keep(sample(400, 1.0001)))

    def test_heartbeat_fires(self):
        band = ssc.DeadBand(heartbeat_s=60.0)
        band.keep(sample(0, 1.0))
        self.assertFalse(band.keep(sample(59_000, 1.0)))
        self.assertTrue(band.keep(sample(60_000, 1.0)))
        # ...and the heartbeat clock restarts from the kept sample.
        self.assertFalse(band.keep(sample(90_000, 1.0)))

    def test_flag_transition_is_information(self):
        band = ssc.DeadBand(heartbeat_s=60.0)
        band.keep(sample(0, 1.0, "S"))
        self.assertTrue(band.keep(sample(200, 1.0, "U")))

    def test_epsilon_widens_the_band(self):
        band = ssc.DeadBand(heartbeat_s=600.0, epsilon=0.001)
        band.keep(sample(0, 1.0))
        self.assertFalse(band.keep(sample(200, 1.0005)))
        self.assertTrue(band.keep(sample(400, 1.002)))

    def test_deadband_is_lossless_at_zero_epsilon(self):
        """Every distinct value the scale reports survives the filter."""
        band = ssc.DeadBand(heartbeat_s=60.0)
        values = [1.0, 1.0, 1.0, 1.0001, 1.0001, 0.9999, 0.9999, 0.9999]
        kept = [v for i, v in enumerate(values)
                if band.keep(sample(i * 200, v))]
        self.assertEqual(kept, [1.0, 1.0001, 0.9999])


class TestMinuteAggregator(unittest.TestCase):
    def test_bucket_boundary_and_stats(self):
        agg = ssc.MinuteAggregator(ANCHOR)
        emitted = []
        for i in range(5):
            doc = agg.add(sample(i * 1000, 1.0 + i / 10000.0))
            if doc:
                emitted.append(doc)
        self.assertEqual(emitted, [])          # still inside minute 1
        doc = agg.add(sample(61_000, 2.0))     # crosses into minute 2
        self.assertIsNotNone(doc)
        self.assertEqual(doc["t"], ANCHOR.replace(second=0, microsecond=0))
        self.assertEqual(doc["n"], 5)
        self.assertAlmostEqual(doc["min_g"], 1.0)
        self.assertAlmostEqual(doc["max_g"], 1.0004)
        self.assertAlmostEqual(doc["ptp_mg"], 0.4, places=6)
        self.assertGreater(doc["std_mg"], 0.0)

    def test_counts_unstable_and_missed(self):
        agg = ssc.MinuteAggregator(ANCHOR)
        agg.add(sample(0, 1.0, "S"))
        agg.add(sample(200, 1.0, "U"))
        agg.add(sample(400, None, "X"))
        doc = agg.flush()
        self.assertEqual((doc["n"], doc["n_unstable"], doc["n_missed"]),
                         (3, 1, 1))
        # A minute of nothing but misses still records the gap, without
        # inventing a mass for it.
        agg2 = ssc.MinuteAggregator(ANCHOR)
        agg2.add(sample(0, None, "X"))
        doc2 = agg2.flush()
        self.assertEqual(doc2["n_missed"], 1)
        self.assertNotIn("mean_g", doc2)

    def test_flush_of_empty_aggregator_is_none(self):
        self.assertIsNone(ssc.MinuteAggregator(ANCHOR).flush())


class TestDocuments(unittest.TestCase):
    def test_raw_doc_uses_device_time_not_host_time(self):
        meta = {"device": "pi"}
        doc = ssc.raw_doc(sample(1500, 1.0361), ANCHOR, meta, 7)
        self.assertEqual(doc["t"], ANCHOR + timedelta(milliseconds=1500))
        self.assertEqual(doc["g"], 1.0361)
        self.assertEqual(doc["seq"], 7)

    def test_capture_feeds_both_tiers(self):
        meta = {"device": "pi"}
        cap = ssc.Capture(meta, ANCHOR, heartbeat_s=60.0)
        for line in ["M,poll_hz,5.0", "E,0,stream start",
                     "S,0,1.0,S", "S,200,1.0,S", "S,400,1.0001,S",
                     "S,61000,1.0001,S"]:
            cap.feed_line(line)
        cap.finish()
        self.assertEqual(cap.n_samples, 4)
        self.assertEqual(cap.n_kept, 3)        # the repeat is dropped
        self.assertEqual(len(cap.minute_docs), 2)
        self.assertEqual(cap.stream_meta["poll_hz"], 5.0)
        self.assertEqual(cap.events[0]["text"], "stream start")


class TestLayouts(unittest.TestCase):
    def _samples(self, n=300):
        # A realistically boring idle stream: one step partway through.
        return [sample(i * 200, 1.0361 if i < n // 2 else 1.0362)
                for i in range(n)]

    def test_compact_beats_verbose_and_deadband_beats_both(self):
        meta = {"device": "pi", "scale": "AND HR-100A", "src": "s"}
        layouts = ssc.build_layouts(self._samples(), ANCHOR, meta, 60.0, 0.0)
        by_letter = {label[0]: docs for label, docs, _ in layouts}
        self.assertEqual(len(by_letter["A"]), 300)
        self.assertEqual(len(by_letter["B"]), 300)
        self.assertLess(len(by_letter["C"]), 20)   # 2 values + heartbeats
        self.assertLessEqual(len(by_letter["D"]), 2)

    def test_layouts_cover_the_same_span(self):
        meta = {"device": "pi", "scale": "AND HR-100A", "src": "s"}
        samples = self._samples()
        layouts = dict((label[0], docs)
                       for label, docs, _ in ssc.build_layouts(
                           samples, ANCHOR, meta, 60.0, 0.0))
        self.assertEqual(layouts["A"][0]["timestamp"], layouts["B"][0]["t"])
        self.assertEqual(layouts["B"][0]["t"], layouts["C"][0]["t"])


if __name__ == "__main__":
    unittest.main()
