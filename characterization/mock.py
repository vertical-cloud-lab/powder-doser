"""Offline rig + balance simulator.

Two jobs:

1. **Dry runs.** ``--mock`` exercises the whole sweep -- design, serial
   protocol shape, logging, analysis, calibration emit -- with no
   hardware attached, so the night's run plan can be debugged before
   anyone walks to the bench.
2. **Testing the analysis against known truth.** The simulator injects a
   *known* bias, noise floor, resonance band and reseat step; the tests
   then assert that :mod:`characterization.analyze` recovers them.  An
   analysis pipeline that has never been shown to recover a planted
   effect is not evidence of anything.

The physics is deliberately crude -- white noise, linear drift, a damped
sinusoid per excitation, an occasional persistent step -- but it has the
qualitative features that matter for the harness: ringing that takes time
to decay, a stability detector that can be fooled, load-dependent settle
time, and RPM bands that are worse than their neighbours.

The mock and hardware code paths are identical -- same threads, same
blocking, same file output.  ``speedup`` compresses only the *blocking*:
a 3 s settle window costs 30 ms of wall clock at ``speedup=100`` but is
still recorded as 3 s, so a mock trace is numerically comparable to a
hardware trace rather than a scaled copy of one.  The runner takes its
clock and sleep from :func:`make_mock` for exactly this reason.
"""

from __future__ import annotations

import math
import random
import time
from dataclasses import dataclass
from typing import Iterator, List, Optional

from . import firmware_params
from .balance import Balance, Reading
from .rig import Ack, Rig, RigError


@dataclass
class Excitation:
    """A damped-sinusoid disturbance starting at host time ``t0``."""

    t0: float
    amplitude_g: float
    freq_hz: float
    tau_s: float
    #: Duration the source is actively driving; ringdown starts after.
    drive_s: float = 0.0

    def value(self, t_sim: float) -> float:
        dt = t_sim - self.t0
        if dt < 0:
            return 0.0
        if dt < self.drive_s:
            envelope = self.amplitude_g
        else:
            envelope = self.amplitude_g * math.exp(-(dt - self.drive_s)
                                                   / max(self.tau_s, 1e-6))
        return envelope * math.sin(2 * math.pi * self.freq_hz * dt)


@dataclass
class SimConfig:
    """Ground truth the tests assert against."""

    noise_g: float = 2e-5           # 0.02 mg white noise
    drift_g_per_s: float = 1e-6     # slow thermal drift
    tare_load_g: float = 0.0        # mass sitting on the pan
    #: Load-cell resonance ~ sqrt(k/m): heavier pan rings slower and longer.
    base_freq_hz: float = 18.0
    base_tau_s: float = 0.35
    #: Stepper step frequencies within +/-``band_width_hz`` of these excite
    #: a structural resonance and ring far harder.
    resonant_step_hz: tuple = (400.0,)
    band_width_hz: float = 40.0
    resonance_gain: float = 12.0
    #: Each solenoid tap has this chance of reseating the cup, leaving a
    #: persistent apparent-mass step -- the artefact that most looks like
    #: real powder.
    tap_reseat_prob: float = 0.25
    tap_reseat_g: float = 3e-4
    #: 0 = reseat direction is random (scatter, no bias); +/-1 = always the
    #: same direction, which is the systematic-coupling case a powder run
    #: would absorb into "how much came out".
    tap_reseat_sign: int = 0
    #: Servo hunting while holding a setpoint.
    servo_hold_noise_g: float = 5e-5
    seed: int = 0


class Simulator:
    """Shared state between :class:`MockBalance` and :class:`MockRig`."""

    def __init__(self, cfg: Optional[SimConfig] = None, speedup: float = 1.0):
        self.cfg = cfg or SimConfig()
        self.speedup = float(speedup)
        self.rng = random.Random(self.cfg.seed)
        self.t_origin = time.monotonic()
        self.excitations: List[Excitation] = []
        self.offset_g = 0.0          # persistent steps (reseat) + tare state
        self.servo_holding = False
        self.stepper_energized = False
        self.events: List[tuple] = []  # (t_sim, label) for debugging

    # -- clock -----------------------------------------------------------
    # Simulated seconds are the unit everything outside this module sees:
    # traces, run rows and analysis are all in sim time, and only the
    # actual blocking is compressed. That keeps a mock trace numerically
    # comparable to a hardware trace instead of being a scaled copy of one.
    def now(self) -> float:
        """Current simulated time, in seconds since the run began."""
        return (time.monotonic() - self.t_origin) * self.speedup

    def sim_time(self, t_sim: Optional[float] = None) -> float:
        return self.now() if t_sim is None else t_sim

    def sleep(self, seconds: float) -> None:
        """Block for ``seconds`` of *simulated* time."""
        if seconds > 0:
            time.sleep(seconds / self.speedup)

    # -- excitation ------------------------------------------------------
    def _resonance_gain(self, step_hz: float) -> float:
        gain = 1.0
        for centre in self.cfg.resonant_step_hz:
            if abs(step_hz - centre) <= self.cfg.band_width_hz:
                # Triangular weighting, peaking at the band centre.
                closeness = 1.0 - abs(step_hz - centre) / self.cfg.band_width_hz
                gain = max(gain, 1.0 + (self.cfg.resonance_gain - 1.0) * closeness)
        return gain

    def _load_scaling(self):
        """Heavier pan -> lower resonant frequency, longer ringdown."""
        m = 1.0 + self.cfg.tare_load_g / 10.0
        return self.cfg.base_freq_hz / math.sqrt(m), self.cfg.base_tau_s * math.sqrt(m)

    def excite_stepper(self, step_hz: float, duration_s: float,
                       amplitude_g: float = 1.5e-4) -> None:
        freq, tau = self._load_scaling()
        gain = self._resonance_gain(step_hz)
        self.excitations.append(Excitation(
            t0=self.sim_time(), amplitude_g=amplitude_g * gain,
            freq_hz=freq, tau_s=tau * (1.0 + 0.5 * (gain - 1.0)),
            drive_s=duration_s))
        self.events.append((self.sim_time(),
                            "stepper step_hz={:.0f} gain={:.1f}".format(
                                step_hz, gain)))

    def excite_vibration(self, duration_s: float, effect: int) -> None:
        freq, tau = self._load_scaling()
        self.excitations.append(Excitation(
            t0=self.sim_time(), amplitude_g=4e-4 * (0.5 + effect / 60.0),
            freq_hz=freq * 1.7, tau_s=tau, drive_s=duration_s))
        self.events.append((self.sim_time(), "vibration"))

    def excite_tap(self, count: int, energy: float) -> None:
        freq, tau = self._load_scaling()
        for i in range(count):
            self.excitations.append(Excitation(
                t0=self.sim_time() + i * 0.25,
                amplitude_g=8e-4 * energy, freq_hz=freq, tau_s=tau))
            if self.rng.random() < self.cfg.tap_reseat_prob:
                # A reseat is indistinguishable from real mass in a
                # single stable reading -- that is the whole point.
                sign = (float(self.cfg.tap_reseat_sign)
                        if self.cfg.tap_reseat_sign
                        else self.rng.choice((-1.0, 1.0)))
                self.offset_g += (sign * self.cfg.tap_reseat_g
                                  * self.rng.uniform(0.5, 1.5))
        self.events.append((self.sim_time(), "tap x{}".format(count)))

    def excite_servo(self, travel_deg: float, duration_s: float) -> None:
        freq, tau = self._load_scaling()
        self.excitations.append(Excitation(
            t0=self.sim_time(), amplitude_g=1e-4 * min(1.0, travel_deg / 90.0),
            freq_hz=freq * 0.8, tau_s=tau, drive_s=duration_s))
        self.events.append((self.sim_time(), "servo"))

    # -- readout ---------------------------------------------------------
    def value(self, t_sim: Optional[float] = None) -> float:
        t_sim = self.sim_time(t_sim)
        value = self.offset_g + self.cfg.drift_g_per_s * t_sim
        value += self.rng.gauss(0.0, self.cfg.noise_g)
        if self.servo_holding:
            value += self.rng.gauss(0.0, self.cfg.servo_hold_noise_g)
        if self.stepper_energized:
            value += self.rng.gauss(0.0, self.cfg.noise_g * 0.5)
        for exc in self.excitations:
            value += exc.value(t_sim)
        # Drop excitations that have rung down to nothing, so a long
        # sweep doesn't accumulate thousands of dead terms.
        if len(self.excitations) > 32:
            cutoff = t_sim - 30.0
            self.excitations = [e for e in self.excitations if e.t0 > cutoff]
        return value

    def tare(self) -> None:
        self.offset_g = 0.0
        self.excitations = []


class MockBalance(Balance):
    """Continuous-output balance backed by a :class:`Simulator`."""

    def __init__(self, sim: Simulator, sample_hz: float = 10.0,
                 stability_window: int = 5, stability_tol_g: float = 5e-5,
                 never_stable: bool = False):
        self.sim = sim
        self.sample_hz = sample_hz
        self.stability_window = stability_window
        self.stability_tol_g = stability_tol_g
        #: Glovebox mode: the balance's own detector never fires, which
        #: stalls any controller that waits on it.
        self.never_stable = never_stable
        self._recent: List[float] = []
        self._closed = False

    def close(self) -> None:
        self._closed = True

    def tare(self) -> None:
        self.sim.tare()
        self._recent = []

    zero = tare

    def _stable(self, value: float) -> bool:
        self._recent.append(value)
        if len(self._recent) > self.stability_window:
            self._recent.pop(0)
        if self.never_stable or len(self._recent) < self.stability_window:
            return False
        return (max(self._recent) - min(self._recent)) <= self.stability_tol_g

    def readings(self) -> Iterator[Reading]:
        period = 1.0 / (self.sample_hz * self.sim.speedup)
        while not self._closed:
            time.sleep(period)
            t = self.sim.now()
            grams = self.sim.value(t)
            yield Reading(t=t, grams=grams, stable=self._stable(grams),
                          raw="MOCK {:+.6f} g".format(grams))


class MockRig(Rig):
    """Rig REPL backed by a :class:`Simulator`.

    Parameter handling goes through the *firmware's own* ``Params`` class,
    so the mock rejects exactly what the hardware would reject.
    """

    def __init__(self, sim: Simulator, config=None):
        self.sim = sim
        # Named ``_params`` so it does not shadow ``Rig.params()``,
        # the protocol call that reads the snapshot back.
        self._params = firmware_params.make_params(config)
        self._params_mod = firmware_params.load_params_module()
        self.config = config or firmware_params.StubConfig()
        self.history: List[str] = []
        self.servo_angle = float(self.config.SERVO_DEFAULT_DEG)

    # -- helpers ---------------------------------------------------------
    def _step_hz(self) -> float:
        steps_per_rev = (self.config.STEPPER_FULL_STEPS_REV
                         * self._params["stepper_microsteps"])
        return self._params["stepper_rpm"] / 60.0 * steps_per_rev

    def _move_seconds(self, degrees: float) -> float:
        rpm = max(self._params["stepper_rpm"], 1e-6)
        return abs(degrees) / 360.0 / rpm * 60.0

    def _rotate(self, degrees: float) -> float:
        duration = self._move_seconds(degrees)
        self.sim.stepper_energized = True
        self.sim.excite_stepper(self._step_hz(), duration)
        self.sim.sleep(duration + self._params["move_pad_ms"] / 1000.0)
        if self._params["deenergize_after"]:
            self.sim.stepper_energized = False
        return duration

    # -- protocol --------------------------------------------------------
    def command(self, line: str, timeout: float = 30.0) -> Ack:
        line = line.strip()
        self.history.append(line)
        host_start = self.sim.now()
        cmd, _, arg = line.partition(" ")
        cmd = cmd.lower()
        arg = arg.strip()
        lines: List[str] = []
        est_ms = 0
        try:
            if cmd == "set":
                name, _, raw = arg.partition(" ")
                self._params.set(name, raw.strip())
            elif cmd == "get":
                lines.append("[get] {}={}".format(arg, self._params.get(arg)))
            elif cmd == "params":
                lines.append(self._params.snapshot())
            elif cmd == "reset":
                self._params.reset(arg or None)
            elif cmd == "d":
                est_ms = int(self._rotate(self._params["dispense_deg"]) * 1000)
            elif cmd == "r":
                est_ms = int(self._rotate(float(arg)) * 1000)
            elif cmd == "v":
                duration = self._params["vib_duration_s"]
                self.sim.excite_vibration(duration, self._params["vib_effect"])
                self.sim.sleep(duration)
            elif cmd == "t":
                count = self._params["tap_count"]
                on_ms = self._params["tap_on_ms"]
                energy = self._params["tap_duty"] * on_ms / 40.0
                self.sim.excite_tap(count, energy)
                self.sim.sleep(count * (on_ms
                                            + self._params["tap_off_ms"]) / 1000.0)
            elif cmd == "a":
                target = float(arg)
                travel = abs(target - self.servo_angle)
                speed = max(self._params["servo_speed_dps"], 1e-6)
                duration = travel / speed
                self.sim.excite_servo(travel, duration)
                self.sim.sleep(duration)
                self.servo_angle = target
                self.sim.servo_holding = bool(self._params["servo_hold"])
            elif cmd == "e":
                self.sim.stepper_energized = arg not in ("0", "off", "false")
            elif cmd in ("!", "stop"):
                self.sim.stepper_energized = False
                self.sim.servo_holding = False
            elif cmd in ("s", "h", "?", "help"):
                lines.append("[mock] rig state")
            else:
                raise ValueError("unknown command {!r}".format(cmd))
        except self._params_mod.ParamError as exc:
            raise RigError("{}: {}".format(line, exc)) from exc
        except ValueError as exc:
            raise RigError("{}: {}".format(line, exc)) from exc
        host_end = self.sim.now()
        return Ack(cmd=cmd, ok=True,
                   t0_ms=int(host_start * 1000) % (1 << 30),
                   t1_ms=int(host_end * 1000) % (1 << 30),
                   est_ms=est_ms, lines=lines,
                   host_start=host_start, host_end=host_end)


def make_mock(speedup: float = 50.0, cfg: Optional[SimConfig] = None,
              sample_hz: float = 10.0, never_stable: bool = False):
    """Convenience factory returning ``(rig, balance, simulator)``.

    Pass ``clock=sim.now, sleep=sim.sleep`` to
    :class:`~characterization.sweep.SweepRunner` so its pre/post windows
    are compressed too; otherwise the runner waits in real seconds while
    the simulated world races ahead of it.
    """
    sim = Simulator(cfg, speedup=speedup)
    return (MockRig(sim), MockBalance(sim, sample_hz=sample_hz,
                                      never_stable=never_stable), sim)
