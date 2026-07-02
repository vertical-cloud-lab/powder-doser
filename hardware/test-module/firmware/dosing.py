"""Closed-loop powder dosing: coarse auger fill, fine solenoid-tap trim.

The control strategy (issue #99):

1. **Coarse phase** -- rotate the auger in ``DOSE_COARSE_STEP_DEG``
   increments, reading the scale between increments, until the pan
   holds ``DOSE_COARSE_FRACTION`` of the target mass (default 90 %).
   Stopping *below* the target is deliberate: auger dispensing
   over-shoots (powder keeps streaming for a moment after the auger
   stops), so the coarse phase must leave headroom for the fine phase.
2. **Fine phase** -- fire the tap solenoid in small bursts; each tap
   knocks a few particles off the auger tube's lip.  Between bursts,
   wait for a stable scale reading and stop as soon as the measured
   mass is within ``DOSE_TOLERANCE_G`` of the target (or above it).

The class is deliberately hardware-agnostic: it talks to *duck-typed*
``stepper`` (``rotate_degrees(deg)``), ``tap`` (``tap(count)``) and
``scale`` (``read()`` / ``read_stable()`` / ``zero()``) objects, so the
exact same control loop runs

* on the Pico W against the real Tic T500 / DRV8871 / HR-100A, and
* under CPython against the simulated rig in ``sim/`` for testing.

Tunables live in ``config.py`` and can be overridden per-instance.
"""

import time


class DoseResult:
    OK = "ok"
    TIMEOUT = "timeout"
    OVERSHOOT = "overshoot"
    SCALE_ERROR = "scale-error"
    EMPTY = "no-flow"

    def __init__(self, status, target_g, dispensed_g, coarse_revs, taps,
                 elapsed_s):
        self.status = status
        self.target_g = target_g
        self.dispensed_g = dispensed_g
        self.coarse_revs = coarse_revs
        self.taps = taps
        self.elapsed_s = elapsed_s

    @property
    def ok(self):
        return self.status == self.OK

    def __repr__(self):
        return ("DoseResult({s}: {d:.4f}/{t:.4f} g in {e:.1f}s, "
                "{r:.2f} auger rev, {n} taps)").format(
                    s=self.status, d=self.dispensed_g, t=self.target_g,
                    e=self.elapsed_s, r=self.coarse_revs, n=self.taps)


class Doser:
    def __init__(self, stepper, tap, scale, cfg, log=print,
                 monotonic=None, sleep_ms=None):
        self.stepper = stepper
        self.tap = tap
        self.scale = scale
        self.cfg = cfg
        self.log = log
        if monotonic is None:
            monotonic = time.time
        if sleep_ms is None:
            try:
                sleep_ms = time.sleep_ms       # MicroPython
            except AttributeError:
                sleep_ms = lambda ms: time.sleep(ms / 1000.0)
        self._now = monotonic
        self._sleep_ms = sleep_ms

    # ------------------------------------------------------------------

    def _stable_grams(self):
        """Stable reading relative to the tare, or None on scale trouble."""
        reading = self.scale.read_stable(
            timeout_ms=self.cfg.SCALE_STABLE_TIMEOUT_MS)
        if (reading is None or not reading.stable or reading.overload or
                reading.grams is None):
            return None
        if reading.unit and reading.unit != "g":
            # A balance set up for another system may not be reporting
            # grams -- the AutoTrickler preset makes it boot in grains
            # ("GN"), and silently treating grains as grams would
            # mis-dose by 15.4x.  Refuse instead.
            self.log("[dose] scale reports {!r}, not grams -- press MODE "
                     "on the balance to select g".format(reading.unit))
            return None
        return reading.grams

    def dose(self, target_g):
        """Dispense ``target_g`` grams onto the (already tared) pan."""
        cfg = self.cfg
        t0 = self._now()
        coarse_deg = 0.0
        taps = 0

        if target_g <= 0:
            return DoseResult(DoseResult.OK, target_g, 0.0, 0.0, 0, 0.0)

        self.log("[dose] target {:.4f} g; taring scale".format(target_g))
        self.scale.zero()
        grams = self._stable_grams()
        if grams is None:
            return DoseResult(DoseResult.SCALE_ERROR, target_g, 0.0,
                              0.0, 0, self._now() - t0)

        # Coarse stop: a fraction of the target for small doses, but
        # never more than DOSE_COARSE_HEADROOM_G short on big doses
        # (iteration 5 fix: percentage-only headroom made multi-gram
        # doses spend hundreds of taps covering the last ~10 %).
        coarse_stop = max(target_g * cfg.DOSE_COARSE_FRACTION,
                          target_g - cfg.DOSE_COARSE_HEADROOM_G)
        self.log("[dose] coarse phase to {:.4f} g".format(coarse_stop))

        # ---- coarse: auger increments -------------------------------
        # Auger throughput (g/rev) is *learned online*: config provides
        # only the initial guess, and every increment refines it from
        # the scale's response (iteration 5 fix: trusting the config
        # value blindly overshot whenever the real powder ran denser).
        gpr_est = cfg.DOSE_GRAMS_PER_REV
        gpr_seen = False
        stalls = 0
        while grams < coarse_stop:
            if self._now() - t0 > cfg.DOSE_TIMEOUT_S:
                return DoseResult(DoseResult.TIMEOUT, target_g, grams,
                                  coarse_deg / 360.0, taps,
                                  self._now() - t0)
            if gpr_est > 0:
                # Until the first scale-verified increment, derate the
                # configured throughput by DOSE_GPR_SAFETY in case the
                # real powder runs denser; afterwards keep a 2x margin
                # (some committed powder lags in the tube, so the pan
                # under-reports the true g/rev).
                margin = 2.0 if gpr_seen else cfg.DOSE_GPR_SAFETY
                mass_budget = min(coarse_stop - grams,
                                  (target_g - grams) * 0.9)
                step_deg = mass_budget / (gpr_est * margin) * 360.0
                if step_deg < 1.8:  # under one full motor step
                    self.log("[dose] coarse step would overshoot; "
                             "switching to fine phase early")
                    break
                step_deg = min(step_deg, cfg.DOSE_COARSE_STEP_DEG)
            else:
                step_deg = cfg.DOSE_COARSE_STEP_DEG
            before = grams
            self.stepper.rotate_degrees(step_deg)
            coarse_deg += step_deg
            self._sleep_ms(cfg.DOSE_SETTLE_MS)
            grams = self._stable_grams()
            if grams is None:
                return DoseResult(DoseResult.SCALE_ERROR, target_g, before,
                                  coarse_deg / 360.0, taps,
                                  self._now() - t0)
            gain = grams - before
            if gain > 0 and step_deg > 0:
                observed = gain / (step_deg / 360.0)
                gpr_est = (observed if not gpr_seen
                           else 0.5 * gpr_est + 0.5 * observed)
                gpr_seen = True
            if gain < cfg.DOSE_MIN_FLOW_G:
                stalls += 1
                if stalls >= cfg.DOSE_MAX_STALLS:
                    self.log("[dose] no powder flow -- hopper empty or "
                             "auger jammed?")
                    return DoseResult(DoseResult.EMPTY, target_g, grams,
                                      coarse_deg / 360.0, taps,
                                      self._now() - t0)
            else:
                stalls = 0
            self.log("[dose]   coarse {:.4f} / {:.4f} g".format(
                grams, target_g))

        # ---- fine: solenoid taps ------------------------------------
        self.log("[dose] fine phase ({} g left)".format(target_g - grams))
        stall_bursts = 0
        while grams < target_g - cfg.DOSE_TOLERANCE_G:
            if self._now() - t0 > cfg.DOSE_TIMEOUT_S:
                return DoseResult(DoseResult.TIMEOUT, target_g, grams,
                                  coarse_deg / 360.0, taps,
                                  self._now() - t0)
            if taps >= cfg.DOSE_MAX_TAPS:
                self.log("[dose] tap budget exhausted")
                return DoseResult(DoseResult.TIMEOUT, target_g, grams,
                                  coarse_deg / 360.0, taps,
                                  self._now() - t0)
            self.tap.tap(cfg.DOSE_TAPS_PER_BURST)
            taps += cfg.DOSE_TAPS_PER_BURST
            self._sleep_ms(cfg.DOSE_SETTLE_MS)
            before = grams
            grams = self._stable_grams()
            if grams is None:
                return DoseResult(DoseResult.SCALE_ERROR, target_g, before,
                                  coarse_deg / 360.0, taps,
                                  self._now() - t0)
            # Stall recovery (iteration 3 fix): taps only deliver powder
            # that's already sitting at the auger tube's lip.  If a few
            # bursts in a row move (almost) nothing, the lip is empty --
            # nudge the auger a little to re-feed it rather than tapping
            # uselessly until the budget runs out.
            if grams - before < cfg.DOSE_FINE_MIN_GAIN_G:
                stall_bursts += 1
                if stall_bursts >= cfg.DOSE_FINE_STALL_BURSTS:
                    # Size the nudge from the remaining mass (iteration 4
                    # fix: a fixed nudge overshot small remainders).  At
                    # least one full step of the motor, at most the
                    # configured nudge, and never more powder than half
                    # of what is still missing.
                    nudge = cfg.DOSE_FINE_NUDGE_DEG
                    if gpr_est > 0:
                        missing = max(0.0, target_g - grams)
                        nudge = min(nudge,
                                    missing / gpr_est
                                    * 360.0 * 0.5)
                        nudge = max(nudge, 360.0 / 200.0)  # >= 1 full step
                    self.log("[dose]   lip empty; nudging auger {:.1f} deg"
                             .format(nudge))
                    self.stepper.rotate_degrees(nudge)
                    coarse_deg += nudge
                    self._sleep_ms(cfg.DOSE_SETTLE_MS)
                    stall_bursts = 0
            else:
                stall_bursts = 0
            self.log("[dose]   fine {:.4f} / {:.4f} g ({} taps)".format(
                grams, target_g, taps))

        status = DoseResult.OK
        if grams > target_g + cfg.DOSE_TOLERANCE_G:
            status = DoseResult.OVERSHOOT
        result = DoseResult(status, target_g, grams,
                            coarse_deg / 360.0, taps, self._now() - t0)
        self.log("[dose] done: {!r}".format(result))
        return result
