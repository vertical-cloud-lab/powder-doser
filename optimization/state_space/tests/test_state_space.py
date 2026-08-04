"""Behaviour tests for the powder-doser state-space model (issue #140).

Run from the repo root::

    python -m unittest discover optimization/state_space/tests

Each test asserts a *qualitative behaviour that the salt data actually shows*,
so a future re-parameterization (another powder, more data) is checked against
the phenomena rather than against frozen numbers.  The one exception is the
feed-factor peak location, which is a headline finding of the 0-70 deg sweep.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from state_space import (  # noqa: E402
    IDX, N_STATES, PowderDoserModel, Params, SALT, feed_factor, initial_state,
    lip_capacity, pulsation, reduced_bulk_model, tap_floor,
)

INVENTORY = ("m_hop", "m_scr1", "m_scr2", "m_scr3", "x_lip", "m_air", "m_cup")


def total_powder(x: np.ndarray) -> float:
    return float(sum(x[IDX[k]] for k in INVENTORY))


class TestConstitutiveMaps(unittest.TestCase):
    def test_feed_factor_peaks_near_40_deg(self):
        """The 0-70 deg sweep found delivery peaking at ~40 deg and falling by 70."""
        grid = np.arange(0.0, 90.0, 0.5)
        ff = np.array([feed_factor(a, 53.3, SALT) for a in grid])
        peak = grid[int(np.argmax(ff))]
        self.assertGreater(peak, 30.0)
        self.assertLess(peak, 55.0)
        self.assertLess(feed_factor(70.0, 53.3, SALT), feed_factor(peak, 53.3, SALT))
        self.assertGreater(feed_factor(25.0, 53.3, SALT), feed_factor(0.0, 53.3, SALT))

    def test_tap_gain_and_lip_capacity_grow_with_tilt(self):
        for a, b in ((0.0, 25.0), (25.0, 50.0), (50.0, 70.0)):
            self.assertGreater(tap_floor(b, SALT), tap_floor(a, SALT))
            self.assertGreater(lip_capacity(b, 0.0, SALT), lip_capacity(a, 0.0, SALT))

    def test_consolidation_collapses_the_tappable_shelf(self):
        """The refilled/re-packed tube gave 10-20x weaker taps at matched tilt."""
        loose = lip_capacity(25.0, 0.0, SALT)
        packed = lip_capacity(25.0, 0.9, SALT)
        self.assertLess(packed, loose / 5.0)

    def test_pulsation_is_nonnegative_and_averages_to_one(self):
        theta = np.linspace(0.0, 1.0, 2001)
        p = np.array([pulsation(t, SALT) for t in theta])
        self.assertTrue(np.all(p >= 0.0))
        self.assertAlmostEqual(float(p.mean()), 1.0, delta=0.15)
        self.assertGreater(p.max() / max(p.mean(), 1e-9), 1.5)  # strong modulation


class TestDynamics(unittest.TestCase):
    def setUp(self):
        self.model = PowderDoserModel(SALT)

    def test_mass_is_conserved(self):
        x = initial_state(53.3, alpha_deg=25.0, params=SALT)
        m0 = total_powder(x)
        u = np.array([45.0, 25.0, 0.0])
        for _ in range(200):
            x = self.model.step(x, u, 0.05)
        self.assertAlmostEqual(total_powder(x), m0, delta=1e-6)
        # and a tap only moves mass between compartments
        x, released = self.model.tap(x, 3)
        self.assertGreater(released, 0.0)

    def test_no_spontaneous_flow_at_steep_tilt(self):
        """Safety probe (2026-07-31): 0.0 mg at every tilt up to 72 deg with
        nothing actuating."""
        x = initial_state(53.3, alpha_deg=70.0, params=SALT)
        u = np.array([0.0, 70.0, 0.0])
        for _ in range(200):  # 10 s parked
            x = self.model.step(x, u, 0.05)
        self.assertLess(x[IDX["m_cup"]], 1e-4)

    def test_one_revolution_delivers_the_feed_factor(self):
        for alpha in (0.0, 25.0, 40.0):
            x = initial_state(53.3, alpha_deg=alpha, params=SALT)
            u = np.array([30.0, alpha, 0.0])
            # prime the screw chain first, then measure two clean revolutions
            for _ in range(int(8.0 / 0.02)):
                x = self.model.step(x, u, 0.02)
            m0 = x[IDX["m_cup"]] + x[IDX["m_air"]]
            for _ in range(int(4.0 / 0.02)):  # 2 rev at 30 rpm
                x = self.model.step(x, u, 0.02)
            per_rev = (x[IDX["m_cup"]] + x[IDX["m_air"]] - m0) / 2.0
            self.assertAlmostEqual(per_rev, feed_factor(alpha, 53.3, SALT),
                                   delta=0.15 * feed_factor(alpha, 53.3, SALT))

    def test_in_flight_inventory_delays_delivery_after_halt(self):
        x = initial_state(53.3, alpha_deg=25.0, params=SALT)
        u = np.array([45.0, 25.0, 0.0])
        for _ in range(int(10.0 / 0.02)):
            x = self.model.step(x, u, 0.02)
        m_air_at_halt = x[IDX["m_air"]]
        m_halt = x[IDX["m_cup"]]
        u_halt = np.array([0.0, 25.0, 0.0])
        for _ in range(int(3.0 / 0.02)):
            x = self.model.step(x, u_halt, 0.02)
        landed = x[IDX["m_cup"]] - m_halt
        # everything that was airborne (plus whatever the lip was already
        # shedding) lands after the halt -- the anticipation mass
        self.assertGreater(landed, 5e-3)                      # measurable
        self.assertGreaterEqual(landed, m_air_at_halt - 1e-9)
        # the excess is the lip finishing its spill plus the stepper's spin-down
        self.assertLess(landed, m_air_at_halt + 0.5 * feed_factor(25.0, 53.3, SALT))
        self.assertLess(x[IDX["m_air"]], 0.01 * m_air_at_halt)  # column emptied

    def test_successive_taps_deplete_toward_a_floor(self):
        """Single-tap battery: 19.2 -> 10.0 -> ... -> 1.3 mg at 25 deg."""
        params = Params.from_json(fill="half")  # the depletable-lip session
        model = PowderDoserModel(params)
        x = initial_state(53.3, alpha_deg=25.0, params=params)
        yields = []
        for _ in range(10):
            x, dm = model.tap(x)
            yields.append(dm)
        self.assertGreater(yields[0], yields[1])
        self.assertGreater(yields[1], yields[4])
        self.assertGreater(yields[0] / yields[-1], 2.0)
        self.assertGreater(yields[-1], 0.0)          # the non-depleting floor
        self.assertLess(sum(yields), feed_factor(25.0, 53.3, params))  # < 1 rev

    def test_rotation_refills_the_lip_between_tap_trains(self):
        x = initial_state(53.3, alpha_deg=25.0, params=SALT)
        model = self.model
        for _ in range(6):
            x, _ = model.tap(x)
        drained = x[IDX["x_lip"]]
        u = np.array([30.0, 25.0, 0.0])
        for _ in range(int(3.0 / 0.02)):  # ~1.5 rev
            x = model.step(x, u, 0.02)
        self.assertGreater(x[IDX["x_lip"]], drained)

    def test_bridged_mode_delivers_only_the_residual_hold_up(self):
        """Run 1 (2026-07-29) kept delivering for a few seconds after the hopper
        bridged, then flat-lined for 400 s: the screw's own hold-up drains, but
        nothing new leaves the hopper."""
        bridged = PowderDoserModel(SALT, mode="bridged")
        x = initial_state(53.3, alpha_deg=25.0, params=SALT)
        hold_up = sum(x[IDX[k]] for k in ("m_scr1", "m_scr2", "m_scr3", "x_lip"))
        u = np.array([45.0, 25.0, 0.0])
        for _ in range(int(5.0 / 0.05)):
            x = bridged.step(x, u, 0.05)
        drained = x[IDX["m_cup"]]
        self.assertLessEqual(drained, hold_up + 1e-9)
        self.assertAlmostEqual(x[IDX["m_hop"]], 53.3, places=9)  # hopper untouched
        for _ in range(int(60.0 / 0.05)):                        # a further minute
            x = bridged.step(x, u, 0.05)
        self.assertLess(x[IDX["m_cup"]] - drained, 1e-3)         # flat-lined
        x, released = bridged.tap(x)   # taps still shake the floor term loose
        self.assertGreater(released, 0.0)


class TestLinearDesignModels(unittest.TestCase):
    def setUp(self):
        self.model = PowderDoserModel(SALT)
        self.x = initial_state(53.3, alpha_deg=25.0, params=SALT)
        self.u = np.array([45.0, 25.0, 0.0])
        for _ in range(int(5.0 / 0.02)):
            self.x = self.model.step(self.x, self.u, 0.02)

    def test_linearization_shapes_and_integrator(self):
        A, B, C, D = self.model.linearize(self.x, self.u)
        self.assertEqual(A.shape, (N_STATES, N_STATES))
        self.assertEqual(B.shape, (N_STATES, 3))
        self.assertEqual(C.shape, (1, N_STATES))
        self.assertEqual(D.shape, (1, 3))
        # cup mass is a pure integrator of the in-flight state
        self.assertAlmostEqual(A[IDX["m_cup"], IDX["m_air"]],
                               1.0 / SALT.tau_flight_s, places=6)
        self.assertAlmostEqual(A[IDX["m_cup"], IDX["m_cup"]], 0.0, places=9)

    def test_discretization_matches_euler_for_small_dt(self):
        A, B, _, _ = self.model.linearize(self.x, self.u)
        dt = 1e-4
        Ad, Bd = self.model.discretize(self.x, self.u, dt)
        self.assertTrue(np.allclose(Ad, np.eye(N_STATES) + A * dt, atol=1e-5))
        self.assertTrue(np.allclose(Bd, B * dt, atol=1e-5))

    def test_feed_factor_state_is_unobservable_when_the_auger_is_stopped(self):
        """phi only shows up in the output through rotation: a dose that never
        turns the screw cannot identify it (the persistent-excitation limit)."""
        running = self.model.observability_report(self.x, self.u)
        halted_x = self.x.copy()
        halted_x[IDX["omega"]] = 0.0
        halted = self.model.observability_report(halted_x,
                                                 np.array([0.0, 25.0, 0.0]))
        self.assertIn("phi", halted["states_with_no_path_to_balance"])
        self.assertNotIn("phi", running["states_with_no_path_to_balance"])
        self.assertGreater(running["rank"], halted["rank"])

    def test_reduced_bulk_model_structure(self):
        red = reduced_bulk_model(25.0, 45.0)
        A, B, C = red["A"], red["B"], red["C"]
        self.assertEqual(A.shape, (4, 4))
        self.assertEqual(B.shape, (4, 2))
        self.assertEqual(C.shape, (1, 4))
        # integrating output, no direct feedthrough from omega to the cup
        self.assertAlmostEqual(A[0, 0], 0.0)
        self.assertAlmostEqual(B[0, 0], 0.0)
        # rotation drives the lip, taps drain it
        self.assertGreater(B[2, 0], 0.0)
        self.assertLess(B[2, 1], 0.0)
        self.assertGreater(B[1, 1], 0.0)


if __name__ == "__main__":
    unittest.main()
