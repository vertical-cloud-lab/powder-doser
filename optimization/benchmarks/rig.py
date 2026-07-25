"""Fair actuator/sensor interface between controllers and the digital twin.

Controllers may ONLY act through this class: they see the noisy, quantized,
lag-filtered balance (plus their own commanded actuator state) and never the
simulator's hidden truth (lip mass, in-flight powder, true dispensed grams,
feed factor).  Ground truth is read by the benchmark harness *after* the
controller declares the dose finished, for scoring only.
"""
from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "simulation"))

from powder_sim import Context, PowderDoserSim, POWDERS  # noqa: E402

__all__ = ["Rig", "DoseOutcome", "Context", "PowderDoserSim", "POWDERS"]


@dataclass
class DoseOutcome:
    method: str
    powder: str
    context_name: str
    target_g: float
    dispensed_g: float
    error_mg: float          # |dispensed - target| in mg, after full settle
    signed_error_mg: float
    overshoot: bool          # dispensed > target (strict asymmetric constraint)
    within_tol: bool         # |error| <= tolerance
    time_s: float            # controller start -> controller "done"
    taps: int
    auger_rev: float
    status: str              # ok | stalled | timeout | overshoot_abort
    seed: int


class Rig:
    """Sensor/actuator surface mirroring the firmware's capabilities."""

    TAP_PERIOD_S = 0.12          # solenoid on+off, matches firmware tap timing
    GLOBAL_TIMEOUT_S = 300.0

    def __init__(self, sim: PowderDoserSim):
        self._sim = sim
        self.t0 = sim.t_s
        self._last_actuation_end = -10.0

    # ---- time ----
    @property
    def t(self) -> float:
        return self._sim.t_s - self.t0

    def timed_out(self) -> bool:
        return self.t > self.GLOBAL_TIMEOUT_S

    def wait(self, dt: float) -> None:
        self._sim.step(dt)

    # ---- actuators (controller knows what it commanded) ----
    def set_rpm(self, rpm: float) -> None:
        self._sim.set_auger_rpm(rpm)
        if rpm > 0.0:
            self._last_actuation_end = float("inf")
        else:
            self._last_actuation_end = self._sim.t_s

    def set_tilt(self, deg: float) -> None:
        self._sim.set_tilt_deg(deg)
        # servo motion shakes the frame; be conservative about the window
        self._last_actuation_end = max(
            self._last_actuation_end if self._last_actuation_end != float("inf")
            else self._sim.t_s, self._sim.t_s + 0.6)

    def rotate_deg(self, auger_deg: float, rpm: float) -> None:
        self._sim.rotate_auger_deg(auger_deg, rpm)
        self._last_actuation_end = self._sim.t_s

    def tap(self, n: int = 1) -> None:
        for _ in range(n):
            self._sim.tap()
            self._sim.step(self.TAP_PERIOD_S)
        self._last_actuation_end = self._sim.t_s

    def tare(self) -> None:
        self._sim.tare()

    # ---- sensing ----
    def read(self) -> tuple[float, bool]:
        """One balance frame (grams, stable) - what RS-232 would deliver."""
        return self._sim.read_balance()

    def actuating(self) -> bool:
        """Whether the controller's own actuators are (or were very recently)
        moving - the controller legitimately knows this about itself."""
        if self._last_actuation_end == float("inf"):
            return True
        return self._sim.t_s < self._last_actuation_end + 0.8

    def stable_read(self, timeout_s: float = 6.0, poll_s: float = 0.2) -> float:
        """Block until the balance reports a stable frame (firmware's
        _stable_grams); falls back to the last frame on timeout."""
        t_end = self._sim.t_s + timeout_s
        grams, stable = self.read()
        while not stable and self._sim.t_s < t_end:
            self.wait(poll_s)
            grams, stable = self.read()
        return grams

    # ---- scoring only (used by the harness AFTER the dose ends) ----
    def true_dispensed_g(self) -> float:
        self._sim.step(1.0)  # let in-flight powder land
        return self._sim.dispensed_g

    @property
    def taps_used(self) -> int:
        return self._sim.total_taps

    @property
    def auger_rev_used(self) -> float:
        return self._sim.total_auger_rev
