"""Refill-tap endgame: running-average tap yield + auger refills.

The stock endgame taps until within tolerance and turns the auger only
when the tip is bone dry (``max_stall_cycles`` taps under 0.2 mg, then a
5 deg nudge).  The rig logs from the PR #166 campaigns say that is the
slow part of a dose: tap yield decays as the tip drains (2.8 mg on the
first tap after the auger stops, 1.2 mg by taps 6-10, 0.5 mg after 40),
it rarely falls under the 0.2 mg stall line, so the nudge seldom fires
(26 times in 2695 taps), and doses ran 100+ taps (5+ minutes) or hit
the 120-cycle budget 40-80 mg short.

``RefillTapDoser`` keeps everything else and changes only the tap stage:

1. tap, settle, read; the cycle's gain is that tap's yield;
2. ``avg`` = mean of the last REFILL_AVG_TAPS yields since the last
   refill; ``need`` = goal - tolerance - mass (to reach the band);
3. if ``avg * REFILL_TAPS_TO_GO < need`` -- at this yield the dose would
   take more than REFILL_TAPS_TO_GO more taps -- rotate the auger
   REFILL_DEG to refill the tip, settle, read (what the refill itself
   delivered is measured, not guessed), and restart the average;
4. otherwise keep tapping.

So the auger turns between taps until the tap yield is high enough,
and stops turning once it is.  A refill is held back when:

* fewer than REFILL_MIN_TAPS taps have been seen since the last refill
  (one empty tap is not evidence; never two refills back to back);
* less than REFILL_MIN_TO_GO_G is still needed -- a rotation can drop a
  slug, so refills are a mid-endgame tool, and the last stretch is the
  stock endgame (single taps + 5 deg dry-lip nudges), unchanged;
* the room left to the band's upper edge is no more than the largest
  refill delivery seen this dose (the worst one, repeated, would
  overshoot);
* the REFILL_MAX budget is spent.

``REFILL_ENABLED = 0`` (or ``REFILL_DEG = 0``) hands the tap stage back
to the stock ``_run_phase``, step for step: the A/B baseline is one
``set`` away on the same build.

Works on top of either trickle_tap build (this PR's, or PR #166's with
the RESULT line, which then carries a ``refill`` section and a ``fw``
tagged ``+refill-tap``).  Knobs: ``refill_params.py``.
"""

import json

import main_three_phase as m3
import refill_params
import trickle_controller as tc
from trickle_controller import TrickleTapDoser, params_dict

REFILL_ID = "refill-tap/2026-10-06"
# PR #154's build predates FIRMWARE_ID; PR #166's executor only ever
# boots main_trickle.py, so a runner answering with this id is refused
# by it unless --takeover (no accidental campaign doses on this endgame).
FIRMWARE_ID = getattr(tc, "FIRMWARE_ID", "trickle_tap/pr154") + "+" + REFILL_ID

REFILL_PARAM_KEYS = (
    "refill_enabled", "refill_deg", "refill_rpm", "refill_avg_taps",
    "refill_min_taps", "refill_taps_to_go", "refill_min_to_go_g",
    "refill_settle_ms", "refill_max",
)


def refill_params_dict():
    return params_dict(refill_params)


class RefillTapDoser(TrickleTapDoser):
    """TrickleTapDoser whose tap stage refills the tip on low yield."""

    def __init__(self, stepper, tap, servo, scale, cfg, p=None, **kw):
        merged = dict(p) if p is not None else params_dict()
        for key, value in refill_params_dict().items():
            merged.setdefault(key, value)
        super().__init__(stepper, tap, servo, scale, cfg, p=merged, **kw)
        self.refill_events = []      # one dict per refill, last dose
        self.tap_yields = []         # every tap-cycle yield (g), last dose

    def dose(self, target_g=None):
        self.refill_events = []
        self.tap_yields = []
        return super().dose(target_g)

    # -- the tap stage ---------------------------------------------------

    def _refill_on(self):
        return bool(self.p["refill_enabled"]) and self.p["refill_deg"] > 0

    def _run_phase(self, num, p, exit_g, target_g, grams, t0, state):
        if (int(p["continuous"]) or not p["name"].startswith("tap")
                or int(p["taps_per_cycle"]) <= 0 or not self._refill_on()):
            return TrickleTapDoser._run_phase(self, num, p, exit_g,
                                              target_g, grams, t0, state)
        return self._run_refill_taps(num, p, exit_g, target_g, grams, t0,
                                     state)

    def _refill_hold(self, window, avg, need, room, state):
        """None = refill now, else the reason it is held back."""
        q = self.p
        if state["refills"] >= int(q["refill_max"]):
            return "budget spent"
        if len(window) < max(1, int(q["refill_min_taps"])):
            return "gathering taps"
        if avg * q["refill_taps_to_go"] >= need:
            return "yield ok"
        if need < q["refill_min_to_go_g"]:
            return "too close"
        if room <= state["refill_worst_g"]:
            return "worst refill {:.1f} mg would overshoot".format(
                1000.0 * state["refill_worst_g"])
        return None

    def _run_refill_taps(self, num, p, exit_g, target_g, grams, t0, state):
        """The stock tap loop (main_three_phase._run_phase) + refills.

        Returns (grams, abort_status_or_None, tap_cycles); refills are
        counted in ``state["refills"]``, not in the cycles.
        """
        q = self.p
        self.servo.move_to(p["angle_deg"])
        taps_n = int(p["taps_per_cycle"])
        tol = self.tolerance_g
        guard = getattr(self, "overshoot_abort_g", 0.0)
        tag = "[phase {} {}]".format(num, p["name"])
        for key, zero in (("refills", 0), ("refill_deg", 0.0),
                          ("refill_g", 0.0), ("refill_worst_g", 0.0)):
            state.setdefault(key, zero)
        self.log("{} refill rule: tap yield avg (last {}) x {} < still "
                 "needed -> auger {:.1f} deg; none within {:.1f} mg of the "
                 "band; budget {}".format(
                     tag, int(q["refill_avg_taps"]), q["refill_taps_to_go"],
                     q["refill_deg"], 1000.0 * q["refill_min_to_go_g"],
                     int(q["refill_max"]) - state["refills"]))
        cycles = 0
        stalls = 0
        nudges = 0
        window = []                  # tap yields since the last refill
        while target_g - grams > exit_g:
            if self._now() - t0 > self.timeout_s:
                self.log(tag + " dose timeout ({} s)".format(self.timeout_s))
                return grams, m3.DoseResult.TIMEOUT, cycles
            if cycles >= p["max_cycles"]:
                self.log(tag + " cycle budget ({}) exhausted".format(
                    p["max_cycles"]))
                return grams, m3.DoseResult.BUDGET, cycles
            before = grams
            self.tap.tap(taps_n, p["tap_on_ms"], p["tap_off_ms"])
            state["taps"] += taps_n
            self._sleep_ms(int(p["settle_ms"]))
            grams = self._read_grams()
            if grams is None:
                return before, m3.DoseResult.SCALE_ERROR, cycles
            cycles += 1
            gain = grams - before
            self.tap_yields.append(gain)
            window.append(gain)
            if len(window) > max(1, int(q["refill_avg_taps"])):
                window.pop(0)
            avg = sum(window) / len(window)
            need = target_g - tol - grams
            self._objectives(tag + " cycle {}:".format(cycles),
                             grams, target_g, gain, t0)
            if guard > 0.0 and grams > target_g + guard:
                self.log(tag + " overshoot guard: {:+.1f} mg past the "
                         "target -- aborting".format(
                             1000.0 * (grams - target_g)))
                return grams, m3.DoseResult.OVERSHOOT, cycles
            if target_g - grams <= exit_g:
                break
            hold = self._refill_hold(window, avg, need,
                                     target_g + tol - grams, state)
            self.log("{}   yield avg {:.2f} mg over {} tap(s); {:.1f} mg "
                     "needed -> {}".format(
                         tag, 1000.0 * avg, len(window), 1000.0 * need,
                         "REFILL" if hold is None else hold))
            if hold is None:
                grams, status = self._refill(tag, target_g, grams, t0,
                                             state, avg, need)
                if status is not None:
                    return grams, status, cycles
                window = []
                stalls = 0
                continue
            # Outside the refill zone: the stock dry-lip nudge, unchanged.
            if gain < p["min_gain_g"]:
                stalls += 1
                if stalls >= p["max_stall_cycles"]:
                    if p["stall_nudge_deg"] > 0 and nudges < p["max_nudges"]:
                        nudges += 1
                        state["nudges"] = state.get("nudges", 0) + 1
                        self.log(tag + " lip empty; nudging auger {:.1f} deg"
                                 " (nudge {}/{})".format(
                                     p["stall_nudge_deg"], nudges,
                                     p["max_nudges"]))
                        self.stepper.rotate_degrees(p["stall_nudge_deg"])
                        state["deg"] += p["stall_nudge_deg"]
                        stalls = 0
                    else:
                        self.log(tag + " no powder flow -- hopper empty, "
                                 "jam, or nudge budget spent")
                        return grams, m3.DoseResult.STALLED, cycles
            else:
                stalls = 0
        return grams, None, cycles

    def _refill(self, tag, target_g, grams, t0, state, avg, need):
        """One refill rotation + settled read.  Returns (grams, status)."""
        q = self.p
        deg = float(q["refill_deg"])
        state["refills"] += 1
        n = state["refills"]
        self.log("{} refill {}/{}: tap yield {:.2f} mg is far below the "
                 "{:.1f} mg needed; auger {:.1f} deg @ {:.0f} rpm".format(
                     tag, n, int(q["refill_max"]), 1000.0 * avg,
                     1000.0 * need, deg, q["refill_rpm"]))
        t_s = self._t_s()
        self.stepper.set_speed(q["refill_rpm"])
        try:
            self.stepper.rotate_degrees(deg)
        finally:
            self.stepper.set_speed(self.cfg.STEPPER_SPEED_RPM)
        state["deg"] += deg
        state["refill_deg"] += deg
        self._sleep_ms(int(q["refill_settle_ms"]))
        after = self._read_grams()
        if after is None:
            return grams, m3.DoseResult.SCALE_ERROR
        delivered = after - grams
        state["refill_g"] += delivered
        if delivered > state["refill_worst_g"]:
            state["refill_worst_g"] = delivered
        label = self._phase_label
        if label is not None:
            self._phase_label = "refill"      # its own telemetry row
        self._objectives(tag + " refill {}:".format(n), after, target_g,
                         delivered, t0, gain_label="from the refill")
        self._phase_label = label
        self.refill_events.append({
            "n": n, "t_s": round(t_s, 2), "deg": deg,
            "after_tap": len(self.tap_yields),
            "mass_before_g": round(grams, 5),
            "delivered_g": round(delivered, 5),
            "avg_yield_g": round(avg, 5), "need_g": round(need, 5),
        })
        guard = getattr(self, "overshoot_abort_g", 0.0)
        if guard > 0.0 and after > target_g + guard:
            self.log(tag + " overshoot guard: {:+.1f} mg past the target "
                     "-- aborting".format(1000.0 * (after - target_g)))
            return after, m3.DoseResult.OVERSHOOT
        return after, None

    # -- reporting -------------------------------------------------------

    def refill_summary(self):
        ys = self.tap_yields
        ev = self.refill_events
        return {
            "id": REFILL_ID,
            "refills": len(ev),
            "refill_deg": round(sum(e["deg"] for e in ev), 1),
            "refill_g": round(sum(e["delivered_g"] for e in ev), 5),
            "refill_max_g": (round(max(e["delivered_g"] for e in ev), 5)
                             if ev else None),
            "tap_cycles": len(ys),
            "tap_mean_g": round(sum(ys) / len(ys), 5) if ys else None,
            "events": ev,
            "params": dict((k, self.p.get(k)) for k in REFILL_PARAM_KEYS),
        }

    def _emit_result(self, res, state, t_marks, settled, error=None):
        """PR #166 builds: the RESULT line plus a ``refill`` section.

        The base method builds and logs the document; its line is held
        back, the refill summary and the tagged ``fw`` are added, and the
        line goes out once.  (PR #154's build has no RESULT line and
        never calls this.)
        """
        log, held = self.log, []
        self.log = held.append
        try:
            TrickleTapDoser._emit_result(self, res, state, t_marks,
                                         settled, error)
        finally:
            self.log = log
        doc = self.last_result
        if doc is None:
            for line in held:
                log(line)
            return
        doc["fw"] = FIRMWARE_ID
        doc["refill"] = self.refill_summary()
        log("RESULT " + json.dumps(doc))

    def print_refills(self):
        """The ``refills`` REPL command: last dose's taps and refills."""
        s = self.refill_summary()
        if not s["tap_cycles"] and not s["refills"]:
            print("[refills] no tap stage in the last dose")
            return
        print("[refills] {} tap cycles (mean {} mg), {} refills ({:.1f} "
              "auger deg, {:.1f} mg delivered by the refills)".format(
                  s["tap_cycles"],
                  "-" if s["tap_mean_g"] is None
                  else "{:.2f}".format(1000.0 * s["tap_mean_g"]),
                  s["refills"], s["refill_deg"], 1000.0 * s["refill_g"]))
        for e in s["events"]:
            print("  refill {n}: t {t_s:.1f} s, {deg:.1f} deg, avg yield "
                  "{a:.2f} mg vs {need:.1f} mg needed -> delivered "
                  "{d:+.2f} mg".format(
                      a=1000.0 * e["avg_yield_g"],
                      need=1000.0 * e["need_g"],
                      d=1000.0 * e["delivered_g"], **e))
        print("  tap yields (mg): " + " ".join(
            "{:.1f}".format(1000.0 * y) for y in self.tap_yields))
