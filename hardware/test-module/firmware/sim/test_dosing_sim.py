"""CPython unit tests for the scale driver + closed-loop dosing logic.

Run from ``hardware/test-module/firmware/``:

    python3 -m pytest sim/ -q          # or
    python3 sim/test_dosing_sim.py     # plain stdlib runner

These exercise the exact modules that ship to the Pico W (``scale.py``,
``dosing.py``) against the simulated rig in ``sim_rig.py``.
"""

import sys
import types
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tests"))

import config                                            # noqa: E402
import scale as scale_mod                                # noqa: E402
import test_scale_contact as contact                     # noqa: E402
from dosing import DoseResult                            # noqa: E402
from sim_rig import VirtualClock, make_rig               # noqa: E402


class ParseFrameTests(unittest.TestCase):
    def test_stable(self):
        r = scale_mod.parse_frame("ST,+00012.345  g\r\n")
        self.assertTrue(r.stable)
        self.assertAlmostEqual(r.grams, 12.345)
        self.assertEqual(r.unit, "g")

    def test_unstable_negative(self):
        r = scale_mod.parse_frame(b"US,-00001.2300  g\r\n")
        self.assertFalse(r.stable)
        self.assertAlmostEqual(r.grams, -1.23)

    def test_overload(self):
        r = scale_mod.parse_frame("OL,+99999.999  g")
        self.assertTrue(r.overload)
        self.assertIsNone(r.grams)

    def test_garbage_and_blank(self):
        for junk in ("", "\r\n", "?,123", "STX", None, b"\xff\xfe",
                     "WT,+1.0 g"):
            self.assertIsNone(scale_mod.parse_frame(junk), junk)


class AndScaleTests(unittest.TestCase):
    def _scale(self):
        clock = VirtualClock()
        _, column, _ = (None, None, None)
        from sim_rig import PowderColumn, SimScaleUart
        column = PowderColumn(clock)
        uart = SimScaleUart(column, clock)
        sc = scale_mod.AndScale(uart, response_timeout_ms=200,
                                sleep_ms=clock.sleep_ms)
        return sc, column, clock

    def test_read_round_trip(self):
        sc, column, _ = self._scale()
        column.pan_g = 1.2345
        r = sc.read()
        self.assertAlmostEqual(r.grams, 1.2345, places=4)

    def test_read_stable_waits_for_settling(self):
        sc, column, clock = self._scale()
        column.pan_g = 2.0
        column._disturb()           # scale is settling -> US frames first
        r = sc.read_stable(timeout_ms=20000)
        self.assertTrue(r.stable)
        self.assertGreaterEqual(clock.time(), column.settle_s)

    def test_zero_tares(self):
        sc, column, _ = self._scale()
        column.pan_g = 5.0
        sc.zero()
        self.assertAlmostEqual(sc.read().grams, 0.0, places=4)


class DoseLoopTests(unittest.TestCase):
    def test_dose_reaches_tolerance(self):
        doser, column, _ = make_rig()
        result = doser.dose(0.500)
        self.assertEqual(result.status, DoseResult.OK)
        self.assertAlmostEqual(result.dispensed_g, 0.500,
                               delta=config.DOSE_TOLERANCE_G)
        # The coarse phase must not have crossed the target by itself.
        self.assertGreater(result.taps, 0)

    def test_dose_various_targets(self):
        for target in (0.050, 0.250, 1.000, 2.500):
            doser, _, _ = make_rig()
            result = doser.dose(target)
            self.assertEqual(result.status, DoseResult.OK, target)
            self.assertAlmostEqual(result.dispensed_g, target,
                                   delta=config.DOSE_TOLERANCE_G)

    def test_coarse_phase_stops_short(self):
        events = []
        doser, column, _ = make_rig()
        original = doser.tap.tap

        def spy(count):
            events.append(column.reading_g())
            original(count)
        doser.tap.tap = spy
        result = doser.dose(1.000)
        self.assertEqual(result.status, DoseResult.OK)
        # When the first tap fires, the pan must be below the target:
        # the auger never finishes the job on its own.
        self.assertTrue(events)
        self.assertLess(events[0], 1.000)

    def test_empty_hopper_aborts(self):
        doser, _, _ = make_rig(hopper_g=0.010)
        result = doser.dose(1.000)
        self.assertEqual(result.status, DoseResult.EMPTY)
        self.assertLess(result.dispensed_g, 0.100)

    def test_dead_scale_reports_error(self):
        doser, _, _ = make_rig()
        doser.scale.uart.write = lambda data: None    # scale never answers
        result = doser.dose(1.000)
        self.assertEqual(result.status, DoseResult.SCALE_ERROR)

    def test_unstable_timeout_reports_scale_error(self):
        doser, _, _ = make_rig()
        doser.scale.read_stable = lambda timeout_ms: scale_mod.ScaleReading(
            scale_mod.UNSTABLE, 0.0, "g")
        result = doser.dose(1.000)
        self.assertEqual(result.status, DoseResult.SCALE_ERROR)

    def test_zero_target_is_noop(self):
        doser, column, _ = make_rig()
        result = doser.dose(0.0)
        self.assertEqual(result.status, DoseResult.OK)
        self.assertEqual(column.pan_g, 0.0)

    def test_sticky_powder_uses_more_taps_but_converges(self):
        doser, _, _ = make_rig(inflight_fraction=0.4, tap_grams=0.0004)
        result = doser.dose(0.300)
        self.assertEqual(result.status, DoseResult.OK)
        self.assertAlmostEqual(result.dispensed_g, 0.300,
                               delta=config.DOSE_TOLERANCE_G)


class ScaleContactTests(unittest.TestCase):
    def _scale(self):
        clock = VirtualClock()
        from sim_rig import PowderColumn, SimScaleUart
        column = PowderColumn(clock)
        uart = SimScaleUart(column, clock)
        sc = scale_mod.AndScale(uart, response_timeout_ms=200,
                                sleep_ms=clock.sleep_ms)
        return sc, column, clock

    def test_contact_detects_live_balance(self):
        sc, column, _ = self._scale()
        column.pan_g = 3.21
        result = contact.probe_contact(sc, listen_ms=200,
                                       sleep_ms=sc._sleep_ms)
        self.assertTrue(result["saw_bytes"])
        self.assertIsNotNone(result["reading"])
        self.assertAlmostEqual(result["reading"].grams, 3.21, places=2)

    def test_contact_reports_silent_link(self):
        sc, _, _ = self._scale()
        sent = []
        sc.uart.write = lambda data: sent.append(data)   # bytes leave, nothing echoes back
        result = contact.probe_contact(sc, listen_ms=200,
                                       sleep_ms=sc._sleep_ms)
        self.assertFalse(result["saw_bytes"])
        self.assertIsNone(result["reading"])
        self.assertEqual(result["frames"], [])
        # the active-poll path must have actually tried to send "Q"
        self.assertTrue(any(b"Q" in bytes(d) for d in sent))


class ReadlineNonblockingTests(unittest.TestCase):
    """Regression tests for main._readline_nonblocking.

    Bench failure (PR #100): MicroPython function objects reject
    attribute assignment, so caching the ``uselect.poll()`` object on
    the function itself crashed the REPL loop on the Pico with
    ``AttributeError: 'function' object has no attribute '_poll'``.
    These tests import ``main`` with stub ``machine``/``uselect``
    modules and pin down the MicroPython-safe behaviour.
    """

    def setUp(self):
        self._saved = {name: sys.modules.get(name)
                       for name in ("machine", "uselect", "main")}

        machine = types.ModuleType("machine")
        for name in ("I2C", "Pin", "PWM", "UART"):
            setattr(machine, name, type(name, (), {}))

        self.polls = []
        created = self.polls

        class _FakePoll:
            def __init__(self):
                self.registered = []
                created.append(self)

            def register(self, stream, mask):
                self.registered.append((stream, mask))

            def poll(self, timeout_ms):
                return []          # no pending input

        uselect = types.ModuleType("uselect")
        uselect.POLLIN = 1
        uselect.poll = _FakePoll

        sys.modules["machine"] = machine
        sys.modules["uselect"] = uselect
        sys.modules.pop("main", None)
        import main
        self.main = main

    def tearDown(self):
        for name, module in self._saved.items():
            if module is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = module

    def test_no_state_stashed_on_the_function_object(self):
        # Two idle polls: no input pending -> both return None, ...
        self.assertIsNone(self.main._readline_nonblocking())
        self.assertIsNone(self.main._readline_nonblocking())
        # ... the poller is built once and registered on stdin once, ...
        self.assertEqual(len(self.polls), 1)
        self.assertEqual(len(self.polls[0].registered), 1)
        # ... and nothing was assigned onto the function object itself
        # (MicroPython raises AttributeError for that).
        self.assertEqual(self.main._readline_nonblocking.__dict__, {})


if __name__ == "__main__":
    unittest.main(verbosity=2)
