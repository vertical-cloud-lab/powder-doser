"""Environment-artifact rejection for the bench balance (issue #116).

The 2026-08-20 bare-pan survey separated three effects that a single
peak-to-peak number had been conflating:

* **draft noise** -- sample-to-sample jitter, ~0.1 mg, at the balance's
  own display resolution.  Solved by the enclosure; nothing to do.
* **zero creep** -- a smooth ramp of order 5 mg/min.  It is *smooth*,
  so it is predictable over the seconds a trial takes.
* **mechanical shocks** -- a door, a machine starting, someone at the
  bench.  These are steps: the zero moves ~100 mg and *stays* moved,
  rather than an oscillation that rings down.

Environmental error therefore scales with how long a measurement takes:
0.70 mg median over 5 s, 33.3 mg over 180 s.  This module attacks the
last two so that error stops growing with duration.

The key idea is an **actuator gate**.  A trial is bracketed by two
windows during which *no actuator is commanded*.  During such a window
mass physically cannot arrive: the fastest powder measured conveys
~116 mg/s while rotating and nothing at all while stopped.  So any
change observed inside a bracket is, by construction, not powder --
it is the environment, and it can be measured and removed:

* the **slope** of the bracket is the creep rate, extrapolated across
  the action so the trial delta is drift-corrected;
* a **single-poll jump** larger than ``SHOCK_STEP_G`` is provably a
  mechanical shock, so it is subtracted as a zero step *and counted*,
  which puts the artifact rate into the data instead of into the
  measurement;
* the **residual scatter** around the fitted line becomes a real
  per-trial uncertainty, which is what the manuscript review asked for.

Nothing here talks to hardware: ``collect()`` takes any object with the
``scale.AndScale`` surface, so the simulation tests drive the identical
code path the Pico runs.  Import-safe under CPython and MicroPython.
"""

import math
import time

# A single-poll jump at least this large, inside a window where no
# actuator was commanded, is a mechanical shock rather than powder.
# The survey's step events were ~100 mg; the quietest 30 s window was
# 0.9 mg peak to peak.  10 mg sits an order of magnitude clear of both.
SHOCK_STEP_G = 0.010

# Residual RMS about the fitted line above which the balance is judged
# not settled enough to trust for this trial.
MAX_RESID_G = 0.0015

# Bracket shape.  6 samples over ~2.4 s: long enough to fit a slope,
# short enough that 96 % of windows in the survey were quiet.
BRACKET_N = 6
BRACKET_INTERVAL_MS = 400

# Give up extrapolating the pre-action drift across a gap longer than
# this -- prediction variance grows with the square of the lever arm.
MAX_EXTRAP_S = 60.0

# How many consecutive brackets to try while waiting for a quiet one.
QUIET_TRIES = 8

# How long after an action powder may still be landing.  Inside this
# window a *gain* is trusted as late-arriving powder; after it, the
# column is assumed drained and a jump is an artifact again.  Kept
# short deliberately: material in flight lands in well under a second,
# so a wide window would hand a positive bench knock a free pass.
ARRIVAL_WINDOW_MS = 1200


class BalanceSilent(Exception):
    """The balance returned no usable frame at all (not merely noisy)."""


try:
    _ticks_ms = time.ticks_ms                 # MicroPython
    _ticks_diff = time.ticks_diff
except AttributeError:                        # CPython (sim tests)
    def _ticks_ms():
        return int(time.monotonic() * 1000)

    def _ticks_diff(a, b):
        return a - b


def _default_sleep_ms(ms):
    time.sleep(ms / 1000.0)


class Bracket:
    """A window of scale samples taken with no actuator commanded.

    ``samples`` is a list of ``(t_ms, grams, stable)``.  Construction
    detects and removes step artifacts, then least-squares fits the
    cleaned series so the caller gets a drift rate, a predicted value
    at any time, and an honest uncertainty.
    """

    def __init__(self, samples, shock_g=SHOCK_STEP_G,
                 max_resid_g=MAX_RESID_G, fit_from=0,
                 arrivals_until=0):
        self.samples = list(samples)
        self.fit_from = fit_from
        # Index up to which a *positive* jump may be real powder still
        # arriving rather than a shock.  The actuator gate says mass
        # cannot arrive while the auger is stopped, but that is only
        # true once everything already in flight has landed: a fast
        # powder can drop a 200 mg slug a beat after the screw stops.
        # Inside this prefix, gains are therefore trusted and only
        # *losses* are treated as artifacts -- powder cannot leave the
        # vessel on its own.  Without this a fast powder's own slug
        # would be subtracted as a bench knock.
        self.arrivals_until = arrivals_until
        self.shock_g = shock_g
        self.max_resid_g = max_resid_g
        if not self.samples:
            raise BalanceSilent("no usable scale frames in bracket")

        self.t = [s[0] for s in self.samples]
        self.raw_g = [s[1] for s in self.samples]
        self.n_stable = sum(1 for s in self.samples if s[2])

        # -- step detection: actuator-gated, so a jump is not powder --
        self.steps = []           # (index, jump_g) -- removed as artifacts
        self.arrivals = []        # (index, jump_g) -- kept as late powder
        cleaned = [self.raw_g[0]]
        offset = 0.0
        for i in range(1, len(self.raw_g)):
            jump = self.raw_g[i] - self.raw_g[i - 1]
            if abs(jump) >= self.shock_g:
                if jump > 0 and i <= self.arrivals_until:
                    self.arrivals.append((i, jump))
                else:
                    self.steps.append((i, jump))
                    offset += jump
            cleaned.append(self.raw_g[i] - offset)
        self.clean_g = cleaned
        self.step_total_g = offset

        # Samples ahead of ``fit_from`` are watched for steps but kept
        # out of the fit.  That is how the post-action settle window is
        # covered: the auger has stopped, so it is actuator-gated and a
        # shock landing in it is still provably not powder, but the
        # balance is still ringing down so its values must not bias the
        # fitted level.
        self._fit()

    # -- fitting -------------------------------------------------------

    def _fit(self):
        t = self.t[self.fit_from:] or self.t
        g = self.clean_g[self.fit_from:] or self.clean_g
        self._fit_t = t
        self._fit_g = g
        n = len(t)
        self.t_mean = sum(t) / n
        g_mean = sum(g) / n
        sxx = sum((v - self.t_mean) ** 2 for v in t)
        if n < 2 or sxx == 0:
            self.slope_g_per_ms = 0.0
            self.intercept_g = g_mean
            self.resid_rms_g = 0.0
            self._sxx = 0.0
            self._n = n
            return
        sxy = sum((t[i] - self.t_mean) * (g[i] - g_mean)
                  for i in range(n))
        slope = sxy / sxx
        self.slope_g_per_ms = slope
        self.intercept_g = g_mean
        resid_sq = 0.0
        for i in range(n):
            pred = g_mean + slope * (t[i] - self.t_mean)
            resid_sq += (g[i] - pred) ** 2
        dof = n - 2
        self.resid_rms_g = math.sqrt(resid_sq / dof) if dof > 0 else 0.0
        self._sxx = sxx
        self._n = n

    # -- accessors -----------------------------------------------------

    @property
    def slope_g_per_s(self):
        return self.slope_g_per_ms * 1000.0

    @property
    def mid_t_ms(self):
        return self.t_mean

    @property
    def shocked(self):
        return bool(self.steps)

    @property
    def unsettled(self):
        return self.resid_rms_g > self.max_resid_g

    @property
    def disturbed(self):
        return self.shocked or self.unsettled

    def value_at(self, t_ms):
        """Fitted value at ``t_ms`` (extrapolating the drift)."""
        return self.intercept_g + self.slope_g_per_ms * (t_ms - self.t_mean)

    def prediction_sigma_g(self, t_ms):
        """Standard error of ``value_at(t_ms)``.

        Ordinary linear-prediction variance: it grows with the square of
        the distance from the window's centre, which is exactly why the
        caller must not extrapolate a short bracket across a long gap.
        """
        if self._n < 2 or self._sxx == 0:
            return self.resid_rms_g
        lever = (t_ms - self.t_mean) ** 2 / self._sxx
        return self.resid_rms_g * math.sqrt(1.0 / self._n + lever)

    def quality(self):
        if self.shocked:
            return "shock"
        if self.unsettled:
            return "unsettled"
        return "ok"

    def __repr__(self):                        # pragma: no cover
        return ("Bracket(n={}, mean={:.4f}, slope={:.4f} mg/s, "
                "resid={:.4f} mg, steps={})".format(
                    len(self.samples), self.intercept_g,
                    1000.0 * self.slope_g_per_s, 1000.0 * self.resid_rms_g,
                    len(self.steps)))


def collect(scale, n=BRACKET_N, interval_ms=BRACKET_INTERVAL_MS,
            sleep_ms=None, ticks_ms=None, shock_g=SHOCK_STEP_G,
            max_resid_g=MAX_RESID_G, settle_n=0, arrivals_until=None):
    """Take ``n`` instantaneous readings and return a :class:`Bracket`.

    Uses ``scale.read()`` (the A&D ``Q`` datum) rather than
    ``read_stable()`` on purpose.  A balance in a working lab may never
    assert ``ST`` -- that is what made ``battery_preflight`` abort with
    ``scale-unreadable`` on 2026-08-20 -- but its ``US`` frames still
    carry a perfectly good number, and a bracket of them is a *better*
    estimator than one stable frame because it also yields a slope and
    an uncertainty.  Frames that are overloaded, unparsed or in the
    wrong unit are dropped; if none survive the balance is genuinely
    silent and :class:`BalanceSilent` is raised.
    """
    sleep_ms = sleep_ms or _default_sleep_ms
    ticks_ms = ticks_ms or _ticks_ms
    samples = []
    overloads = 0
    n = n + settle_n
    for i in range(n):
        if i:
            sleep_ms(interval_ms)
        reading = scale.read()
        if reading is None or reading.grams is None:
            continue
        if getattr(reading, "overload", False):
            overloads += 1
            continue
        unit = getattr(reading, "unit", "g")
        if unit and unit != "g":
            continue
        samples.append((ticks_ms(), reading.grams,
                        bool(getattr(reading, "stable", False))))
    if not samples:
        raise BalanceSilent(
            "no usable frames in {} reads ({} overloaded)".format(
                n, overloads))
    # ``settle_n`` counts samples that were *attempted*; unusable frames
    # are dropped, so clamp the fit window to what actually arrived.
    fit_from = min(settle_n, max(0, len(samples) - 2))
    if arrivals_until is None:
        arrivals_until = min(fit_from,
                             int(ARRIVAL_WINDOW_MS // max(1, interval_ms)))
    return Bracket(samples, shock_g=shock_g, max_resid_g=max_resid_g,
                   fit_from=fit_from, arrivals_until=arrivals_until)


def quiet_bracket(scale, tries=QUIET_TRIES, **kwargs):
    """Keep taking brackets until one is free of *shocks*.

    Returns ``(bracket, attempts, quiet)``.

    Note what this does and does not wait for.  A shock is a transient:
    waiting genuinely fixes it, because the next window will not contain
    one.  Stationary jitter is not a transient -- waiting for a quiet
    window when the whole room is buzzing never terminates, and it is
    the wrong tool anyway, since jitter is beaten by *averaging*, which
    the bracket already does (its uncertainty falls as the residual over
    the square root of the sample count).  So a high-residual bracket is
    kept and flagged ``unsettled``, and only a shocked one is retried.
    That distinction is why a battery can run in a busy lab instead of
    stalling in one.
    """
    best = None
    for attempt in range(1, tries + 1):
        bracket = collect(scale, **kwargs)
        if not bracket.shocked:
            return bracket, attempt, True
        if best is None or _worse(best, bracket):
            best = bracket
    return best, tries, False


def _worse(current_best, candidate):
    """True when ``candidate`` is the better bracket to keep."""
    if current_best.shocked and not candidate.shocked:
        return True
    if candidate.shocked and not current_best.shocked:
        return False
    return candidate.resid_rms_g < current_best.resid_rms_g


class Delta:
    """A drift-corrected mass change between two brackets."""

    def __init__(self, before, after, drift_correct=True,
                 max_extrap_s=MAX_EXTRAP_S):
        self.before = before
        self.after = after
        self.gap_s = (after.mid_t_ms - before.mid_t_ms) / 1000.0
        self.drift_corrected = bool(
            drift_correct and 0 < self.gap_s <= max_extrap_s)

        self.after_g = after.value_at(after.mid_t_ms)
        if self.drift_corrected:
            # Carry the pre-action creep forward across the action: what
            # the balance *would* read now had nothing been dispensed.
            self.baseline_g = before.value_at(after.mid_t_ms)
            sigma_before = before.prediction_sigma_g(after.mid_t_ms)
        else:
            self.baseline_g = before.value_at(before.mid_t_ms)
            sigma_before = before.prediction_sigma_g(before.mid_t_ms)
        self.delta_g = self.after_g - self.baseline_g
        sigma_after = after.prediction_sigma_g(after.mid_t_ms)
        self.sigma_g = math.sqrt(sigma_before ** 2 + sigma_after ** 2)

        self.drift_g = self.baseline_g - before.value_at(before.mid_t_ms)
        self.shock_g = before.step_total_g + after.step_total_g
        self.n_shocks = len(before.steps) + len(after.steps)

    @property
    def disturbed(self):
        return self.before.disturbed or self.after.disturbed

    def quality(self):
        for bracket in (self.after, self.before):
            q = bracket.quality()
            if q != "ok":
                return q
        if not self.drift_corrected and self.gap_s > MAX_EXTRAP_S:
            return "drift"
        return "ok"

    def __repr__(self):                        # pragma: no cover
        return ("Delta({:.4f} g +/- {:.4f}, drift {:+.4f}, shock {:+.4f}, "
                "{})".format(self.delta_g, self.sigma_g, self.drift_g,
                             self.shock_g, self.quality()))


def error_vs_duration(samples, durations_s, shock_g=SHOCK_STEP_G):
    """Median/p90 apparent mass error for a measurement of each length.

    Given a passive record of ``(t_ms, grams, stable)`` with nothing on
    the pan, this is what the environment alone would have contributed
    to a trial of each duration -- the table that decides which blocks
    are viable in a given room.  Used by the survey tool; kept here so
    it is covered by the same tests as the rejection logic.
    """
    if len(samples) < 2:
        return {}
    out = {}
    for duration in durations_s:
        window_ms = duration * 1000.0
        errors = []
        j = 0
        for i in range(len(samples)):
            target = samples[i][0] + window_ms
            if j < i:
                j = i
            while j + 1 < len(samples) and samples[j + 1][0] <= target:
                j += 1
            if samples[j][0] < target * 0.999 and j == len(samples) - 1:
                break
            errors.append(abs(samples[j][1] - samples[i][1]))
        if not errors:
            continue
        errors.sort()
        out[duration] = {
            "n": len(errors),
            "median_g": errors[len(errors) // 2],
            "p90_g": errors[min(len(errors) - 1, int(0.9 * len(errors)))],
            "max_g": errors[-1],
        }
    return out
