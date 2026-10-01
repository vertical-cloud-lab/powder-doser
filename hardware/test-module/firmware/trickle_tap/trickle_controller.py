"""KF + rate-PI trickle-tap dose controller for the Pico (MicroPython).

This is the hardware port of the twin's deployed ``trickle_tap``
controller (``optimization/benchmarks/bangbang.py``, PR #124), with the
parameters and structure of the trim study's re-derivation
(``optimization/trim/trim_methods.py::_rate_trim``): the dead
ff-adaptive margin term is dropped (it fired in 0 of 360 sim doses) and
the cutoff margin is the fixed ``CUTOFF_MARGIN_G``.

Dose structure (each stage skipped when already inside its threshold):

1. **bulk**   -- velocity mode borrowed unchanged from
   ``main_three_phase._run_phase_continuous``: spin fast, halt at
   ``TRICKLE_START_REMAINING_G`` (+ anticipation), settle, read.
2. **trickle** -- the part this folder exists to let you watch: a
   3-state Kalman filter (mass, rate, lagged balance) fed instantaneous
   balance polls, a PI loop steering the *estimated delivery rate* to a
   set-point that tapers as the target approaches, and the predictive
   cutoff  ``m + r*tau + k*sigma >= goal - margin``  that halts the
   auger.  Every poll appends a telemetry row (see TELEMETRY_HEADER).
3. **tap**    -- the firmware's phase-3 endgame, single taps with
   settled reads and dry-lip nudges, until within tolerance.

``TRICKLE_ENABLED = 0`` drops stage 2: the bulk then tapers its rpm and
halts on a predicted final mass ``BULK_STOP_MARGIN_G`` short of the
goal, and the tap endgame finishes from there (the bulk -> tap dose).
``BULK_ONLY = 1`` drops stages 2 and 3.

Reads between stages go through the ThreePhaseDoser bracket machinery
(``balance_filter``), i.e. the verified-tare and silent-balance-retry
fixes from the 2026-09-03 Block H session are inherited, not copied.

Hardware-agnostic like the base class: ``stepper`` needs the base
surface plus ``set_velocity_rpm(rpm)`` (see ``main_trickle.py`` /
``sim/test_trickle_tap.py``), so the identical control path runs on the
Pico and under CPython.
"""

import gc
import json
import time

import main_three_phase as m3
from trickle_kf import TrickleKF

try:
    import trickle_params as _tp
except ImportError:          # pragma: no cover - params file always ships
    _tp = None

try:
    _ticks_ms = time.ticks_ms                 # MicroPython
    _ticks_diff = time.ticks_diff
    _ticks_add = time.ticks_add
except AttributeError:                        # CPython (sim tests)
    def _ticks_ms():
        return int(time.monotonic() * 1000)

    def _ticks_diff(a, b):
        return a - b

    def _ticks_add(t, delta):
        return t + delta


# gc.mem_free is MicroPython-only; under CPython the reserve check is off.
_mem_free = getattr(gc, "mem_free", None)


def params_dict(module=None):
    """All UPPERCASE names in trickle_params as a lowercase-keyed dict."""
    module = module or _tp
    out = {}
    for name in dir(module):
        if name.isupper() and not name.startswith("_"):
            out[name.lower()] = getattr(module, name)
    return out


TELEMETRY_HEADER = ("t_s,phase,z_g,fresh,m_g,r_gps,sigma_g,ff_gpr,"
                    "r_sp_gps,err_gps,integ,rpm_cmd,pred_g,cutoff_g,"
                    "clamp_hits")

# Identity of this build, printed by 's' and carried in every RESULT
# line.  The Pico is shared with other sessions' firmware, so the
# campaign executor refuses to dose unless this matches
# scripts/opt_common.FIRMWARE_ID -- bump both together.
FIRMWARE_ID = "trickle_tap/2026-10-01"

# The searched + campaign-relevant knobs echoed back in every RESULT
# line (issue #164 section 2.6: parameters *as executed*, not just as
# commanded).
RESULT_PARAM_KEYS = (
    "bulk_tap", "trickle_tap", "bulk_tilt_deg", "trickle_tilt_deg",
    "tap_tilt_deg", "bulk_rpm", "trickle_start_remaining_g",
    "tolerance_g", "tau_afterflow_s", "goal_mass_g",
    "tap_cadence_on_ms", "tap_cadence_off_ms", "overshoot_abort_g",
    "final_settle_ms", "taps_per_cycle", "tap_burst_taps",
    "tap_burst_above_g", "bulk_only", "bulk_taper_start_g",
    "bulk_min_rpm", "bulk_boost_s", "bulk_max_passes",
    "trickle_enabled", "bulk_stop_margin_g", "bulk_halt_kf",
)


class TelemetryBuffer:
    """Fixed-capacity row store that can never take a dose down.

    2026-09-30 (Al 4047, PR #166): a plain list grew one row per poll and
    MicroPython doubles a list's storage when it fills; at row 257 that
    asked the fragmented Pico W heap for one contiguous 2048-byte block,
    got ``MemoryError``, and the exception escaped the dose mid-bulk.
    The slot array is allocated ONCE, up front (boot, when the heap is
    clean), so appending never needs a large block; a row that still
    cannot be allocated (the heap is simply full) ends logging for this
    dose with ``truncated`` set -- the dose itself carries on.
    """

    def __init__(self, cap):
        self.cap = max(0, int(cap))
        self._slots = [None] * self.cap
        self.n = 0
        self.truncated = False

    def clear(self):
        for i in range(self.n):
            self._slots[i] = None
        self.n = 0
        self.truncated = False

    def append(self, row):
        if self.truncated:
            return False
        if self.n >= self.cap:
            self.truncated = True
            return False
        self._slots[self.n] = row
        self.n += 1
        return True

    def drop(self):
        """Free every row (the out-of-memory path) and stop logging."""
        self.clear()
        self.truncated = True

    def __len__(self):
        return self.n

    def __iter__(self):
        for i in range(self.n):
            yield self._slots[i]


def _round(value, digits):
    if value is None:
        return None
    try:
        return round(value, digits)
    except (TypeError, ValueError):
        return value


class TrickleTapDoser(m3.ThreePhaseDoser):
    """Bulk -> KF/PI trickle -> tap endgame, with per-poll telemetry."""

    def __init__(self, stepper, tap, servo, scale, cfg, p=None, **kw):
        super().__init__(stepper, tap, servo, scale, cfg, **kw)
        self.p = dict(p) if p is not None else params_dict()
        # CSV rows (strings) of the last dose, in a slot array sized
        # once here while the heap is still clean (TelemetryBuffer).
        self.telemetry = TelemetryBuffer(self.p["log_max_rows"])
        self.dose_count = 0
        self.log_dir = ""            # "" = filesystem root on the Pico
        self.last_log_path = None
        self._phase_label = None
        self._t0_ms = 0
        # Issue #164 campaign additions: per-halt stop events (the
        # tau_afterflow dataset), the learned feed factor at cutoff, and
        # the last machine-parseable RESULT document ('res' reprints it).
        self.stop_events = []
        self.last_ff = None
        self.last_result = None
        self._last_grams = 0.0       # last mass seen (fw-error reports it)
        self._dose_ctx = None

    # -- clocks --------------------------------------------------------

    def _tms(self):
        return (self._ticks_ms or _ticks_ms)()

    def _tdiff(self, a, b):
        if self._ticks_ms is not None:        # injected virtual clock
            return a - b
        return _ticks_diff(a, b)

    # -- telemetry -----------------------------------------------------

    def _t_s(self):
        return self._tdiff(self._tms(), self._t0_ms) / 1000.0

    def _tel(self, row):
        """Log one row; telemetry is best-effort and never raises."""
        tel = self.telemetry
        if tel.truncated:
            return
        # Leave the controller its working heap: every row is a fresh
        # string, so stop logging while there is still room to format
        # the rest of the dose's print lines and its RESULT.  mem_free()
        # does not count garbage the collector has not reclaimed yet
        # (2026-09-30: 1248 bytes "free" at row 80 of a 128 kB heap), so
        # only a shortfall that survives a collection counts.
        floor = int(self.p.get("log_min_free_bytes", 0))
        if (_mem_free is not None and tel.n % 16 == 0
                and _mem_free() < floor):
            gc.collect()
        if (_mem_free is not None and tel.n % 16 == 0
                and _mem_free() < floor):
            tel.truncated = True
            self.log("[dose] heap low ({} bytes free) -- telemetry stops at"
                     " {} rows; the dose carries on".format(_mem_free(),
                                                            tel.n))
            return
        try:
            if not tel.append(row):
                self.log("[dose] telemetry full at {} rows (log_max_rows);"
                         " not logging the rest of this dose".format(
                             tel.cap))
        except MemoryError:
            tel.truncated = True

    def _reset_telemetry(self):
        """Empty the row store before a dose, re-sizing it only when
        ``log_max_rows`` was changed with ``set``."""
        cap = int(self.p["log_max_rows"])
        self.telemetry.clear()
        gc.collect()
        if cap != self.telemetry.cap:
            self.telemetry = None
            gc.collect()
            try:
                self.telemetry = TelemetryBuffer(cap)
            except MemoryError:
                self.log("[dose] no room for {} telemetry rows; logging "
                         "off for this dose".format(cap))
                self.telemetry = TelemetryBuffer(0)
                self.telemetry.truncated = True

    def _objectives(self, tag, grams, target_g, gain, t0, gain_label="this cycle"):
        # Base-class hook: every bulk poll / tap cycle / phase summary
        # lands here, so the mass staircase outside the trickle gets into
        # the CSV too (PI columns empty).
        m3.ThreePhaseDoser._objectives(self, tag, grams, target_g, gain,
                                       t0, gain_label)
        self._last_grams = grams
        if self._phase_label is not None:
            self._tel("%.2f,%s,%.5f,1,%.5f,,,,,,,,,," % (
                self._t_s(), self._phase_label, grams, grams))

    def _flush_log(self):
        self.last_log_path = None
        if not self.p["log_to_flash"] or len(self.telemetry) == 0:
            return
        for i in range(1000):
            path = "%s/trickle_log_%03d.csv" % (self.log_dir, i)
            try:
                f = open(path)                # exists?
                f.close()
            except OSError:
                break
        else:                                 # pragma: no cover
            return
        try:
            with open(path, "w") as f:
                f.write(TELEMETRY_HEADER + "\n")
                for row in self.telemetry:
                    f.write(row + "\n")
            self.last_log_path = path
            self.log("[dose] telemetry: {} rows -> {} (download it, or "
                     "type 'log' to print)".format(len(self.telemetry), path))
        except Exception as exc:              # full flash must not kill a dose
            self.log("[dose] telemetry write failed ({}); rows kept in "
                     "RAM -- 'log' still prints them".format(exc))

    def _emit_result(self, res, state, t_marks, settled, error=None):
        """One machine-parseable ``RESULT {json}`` line per dose.

        The opt_dose_capture.py executor on the Pi Zero parses this
        instead of scraping the human-oriented log text (issue #164
        section 3).  Emitted on EVERY dose exit, aborts included; the
        'res' REPL command reprints the last one.
        """
        p = self.p
        events = []
        for ev in self.stop_events:
            out = {}
            for k, v in ev.items():
                out[k] = _round(v, 5) if isinstance(v, float) else v
            events.append(out)
        doc = {
            "v": 1,
            "status": res.status,
            "target_g": _round(res.target_g, 5),
            "final_g": _round(res.dispensed_g, 5),
            "settled_final": 1 if settled else 0,
            "error_mg": _round(
                1000.0 * (res.dispensed_g - res.target_g), 2),
            "t_total_s": _round(self._t_s(), 2),
            "t_bulk_s": _round(t_marks.get("bulk", 0.0), 2),
            "t_trickle_s": _round(t_marks.get("trickle", 0.0), 2),
            "t_tap_s": _round(t_marks.get("tap", 0.0), 2),
            "t_settle_s": _round(t_marks.get("settle", 0.0), 2),
            "phase_cycles": dict(res.phase_cycles),
            "taps": res.taps,
            "nudges": state.get("nudges", 0),
            "auger_rev": _round(res.auger_deg / 360.0, 3),
            "ff_g_per_rev": _round(self.last_ff, 4),
            "baseline_g": _round(self.last_baseline_g, 5),
            "read_retries": self.read_retries,
            "stop_events": events,
            "params": dict((k, p.get(k)) for k in RESULT_PARAM_KEYS),
            "telemetry_rows": len(self.telemetry),
            "telemetry_truncated": 1 if self.telemetry.truncated else 0,
            "log_path": self.last_log_path,
            "dose_n": self.dose_count,
            "fw": FIRMWARE_ID,
        }
        if error is not None:
            doc["error"] = error
        self.last_result = doc
        self.log("RESULT " + json.dumps(doc))

    # -- stage parameter dicts (built fresh so live `set` applies) -----

    def _bulk_phase(self):
        p, cfg = self.p, self.cfg
        # bulk_tap on -> cadence tapping while the auger spins: one
        # tap_cadence_on_ms pulse per (on + off) period (issue #164;
        # the velocity-mode runner honors taps_per_cycle > 0 as cadence).
        return {"name": "bulk", "angle_deg": p["bulk_tilt_deg"],
                "rotation_deg": 0.0, "rotation_rpm": p["bulk_rpm"],
                "continuous": 1, "poll_ms": int(p["bulk_poll_ms"]),
                "anticipation_g": p["bulk_anticipation_g"],
                "taps_per_cycle": 1 if p.get("bulk_tap") else 0,
                "tap_on_ms": int(p.get("tap_cadence_on_ms",
                                       cfg.TAP_ON_MS)),
                "tap_off_ms": int(p.get("tap_cadence_off_ms",
                                        cfg.TAP_OFF_MS)),
                "settle_ms": int(p["bulk_settle_ms"]),
                "min_gain_g": 0.002, "max_stall_cycles": 10,
                "stall_nudge_deg": 0.0, "max_nudges": 0, "max_cycles": 100}

    def _tap_phase(self):
        p, cfg = self.p, self.cfg
        return {"name": "tap", "angle_deg": p["tap_tilt_deg"],
                "rotation_deg": 0.0, "rotation_rpm": 0.0, "continuous": 0,
                "poll_ms": 250, "anticipation_g": 0.0,
                "taps_per_cycle": int(p["taps_per_cycle"]),
                "tap_on_ms": cfg.TAP_ON_MS, "tap_off_ms": cfg.TAP_OFF_MS,
                "settle_ms": int(p["tap_settle_ms"]), "min_gain_g": 0.0002,
                "max_stall_cycles": 3,
                "stall_nudge_deg": p["tap_nudge_deg"],
                "max_nudges": int(p["tap_max_nudges"]),
                "max_cycles": int(p["tap_max_cycles"])}

    def _tap_burst_phase(self, tap, tol):
        """The tap stage's opening stretch: ``tap_burst_taps`` per cycle
        while more than ``tap_burst_above_g`` is to go.  None = off."""
        p = self.p
        above = float(p.get("tap_burst_above_g", 0.0))
        taps_n = int(p.get("tap_burst_taps", 0))
        if above <= tol or taps_n <= tap["taps_per_cycle"]:
            return None
        burst = dict(tap)
        burst["name"] = "tap-burst"
        burst["taps_per_cycle"] = taps_n
        burst["exit_g"] = above
        return burst

    # -- the dose ------------------------------------------------------

    def dose(self, target_g=None):
        """One dose; ALWAYS ends in a RESULT line.

        Any exception inside the dose (2026-09-30: a telemetry
        ``MemoryError`` mid-bulk) used to escape to the REPL loop with
        no RESULT, so the Zero's executor sat out its whole timeout.
        Now the rig is made safe and the dose is reported as
        ``fw-error`` (an infrastructure fault, never modeled) with the
        last mass seen.
        """
        if target_g is None:
            target_g = self.p["goal_mass_g"]
        target_g = float(target_g)
        self._last_grams = 0.0
        self._dose_ctx = None
        try:
            return self._dose(target_g)
        except Exception as exc:
            if isinstance(exc, MemoryError):
                self.telemetry.drop()         # make room to report
                gc.collect()
            return self._fail_dose(target_g, exc)

    def _fail_dose(self, target_g, exc):
        for halt in (self.stepper.stop, self._restore_rig):
            try:
                halt()
            except Exception:
                pass
        self._phase_label = None
        ctx = self._dose_ctx or {}
        t0 = ctx.get("t0", self._now())
        state = ctx.get("state", {"taps": 0, "deg": 0.0, "nudges": 0})
        res = m3.DoseResult(self.FW_ERROR, target_g, self._last_grams,
                            self._now() - t0, ctx.get("stage_cycles", []),
                            state["taps"], state["deg"])
        self.log("[dose] firmware error {!r}; rig stopped, {:.4f} g "
                 "delivered so far".format(exc, self._last_grams))
        self.log("[dose] done: {!r}".format(res))
        self._emit_result(res, state, ctx.get("t_marks", {}), False,
                          error=repr(exc))
        return res

    FW_ERROR = "fw-error"

    def _dose(self, target_g):
        p = self.p
        self.timeout_s = p["dose_timeout_s"]
        self.thresholds = [p["trickle_start_remaining_g"], p["tolerance_g"]]
        tol = p["tolerance_g"]

        t0 = self._now()
        self._t0_ms = self._tms()
        state = {"taps": 0, "deg": 0.0, "nudges": 0}
        stage_cycles = []
        t_marks = {}                 # stage name -> seconds spent in it
        self._dose_ctx = {"t0": t0, "state": state,
                          "stage_cycles": stage_cycles, "t_marks": t_marks}
        self._reset_telemetry()
        self.read_retries = 0
        self.dose_count += 1
        self.stop_events = []
        self.last_ff = None
        self.last_halt = None
        self.overshoot_abort_g = float(p.get("overshoot_abort_g", 0.0))

        def result(status, grams, settled=False):
            self._phase_label = None
            self._flush_log()
            res = m3.DoseResult(status, target_g, grams, self._now() - t0,
                                stage_cycles, state["taps"], state["deg"])
            self.log("[dose] done: {!r}".format(res))
            self._emit_result(res, state, t_marks, settled)
            return res

        if target_g <= 0:
            return result(m3.DoseResult.OK, 0.0)
        self.log("[dose] trickle-tap dose to {:.4f} g (tol {:.1f} mg, "
                 "trickle tilt {:.1f} plate deg); taring scale".format(
                     target_g, 1000.0 * tol, p["trickle_tilt_deg"]))
        tared, baseline = self._tare_and_baseline(target_g)
        if not tared:
            status = (m3.DoseResult.NOT_TARED if baseline
                      else m3.DoseResult.SCALE_ERROR)
            return result(status, 0.0)
        grams = self._read_grams()
        if grams is None:
            return result(m3.DoseResult.SCALE_ERROR, 0.0)

        def finish(grams):
            # --- final settle: the reading that scores the dose ---------
            # t_total and |error| are defined against the balance AT REST
            # (issue #164 section 2.2), so wait out the afterflow + balance
            # lag before the reading, and only then restore the rig (servo
            # motion shakes the pan).
            settle_ms = int(p.get("final_settle_ms", 0))
            t_stage = self._t_s()
            if settle_ms > 0:
                self._phase_label = None
                self.log("[dose] final settle {} ms before the scoring "
                         "reading".format(settle_ms))
                self._sleep_ms(settle_ms)
                settled = self._read_grams()
                if settled is None:
                    t_marks["settle"] = self._t_s() - t_stage
                    self._restore_rig()
                    return result(m3.DoseResult.SCALE_ERROR, grams)
                grams = settled
            t_marks["settle"] = self._t_s() - t_stage
            self._restore_rig()
            status = m3.DoseResult.OK
            if grams > target_g + tol:
                status = m3.DoseResult.OVERSHOOT
            return result(status, grams, settled=settle_ms > 0)

        def endgame(grams):
            # --- stage 3: tap endgame (inherited phase machinery) ------
            if target_g - grams > tol:
                self._phase_label = "tap"
                tap = self._tap_phase()
                burst = self._tap_burst_phase(tap, tol)
                t_stage = self._t_s()
                cycles, status = 0, None
                if burst is not None and target_g - grams > burst["exit_g"]:
                    self.log("=== stage 3 'tap': {:.4f} g to go, {} taps per "
                             "cycle until {:.4f} g to go, then {} at {:.1f} "
                             "plate deg".format(target_g - grams,
                                                burst["taps_per_cycle"],
                                                burst["exit_g"],
                                                tap["taps_per_cycle"],
                                                tap["angle_deg"]))
                    nudges0 = state["nudges"]
                    grams, status, cycles = self._run_phase(
                        3, burst, burst["exit_g"], target_g, grams, t0, state)
                    stage_cycles.append(("tap_burst", cycles))
                    # the closing stretch gets what is left of both budgets
                    tap["max_cycles"] -= cycles
                    tap["max_nudges"] -= state["nudges"] - nudges0
                else:
                    self.log("=== stage 3 'tap': {:.4f} g to go, single taps "
                             "at {:.1f} plate deg".format(target_g - grams,
                                                          tap["angle_deg"]))
                if status is None and target_g - grams > tol:
                    grams, status, more = self._run_phase(
                        3, tap, tol, target_g, grams, t0, state)
                    cycles += more
                t_marks["tap"] = self._t_s() - t_stage
                stage_cycles.append(("tap", cycles))
                if status is not None:
                    self._restore_rig()
                    return result(status, grams)
            else:
                stage_cycles.append(("tap", 0))
                self.log("=== stage 3 'tap' skipped ({:.4f} g to go is inside "
                         "tolerance)".format(target_g - grams))
            return finish(grams)

        # --- bulk-only dose: stage 1 is the whole dose -----------------
        if p.get("bulk_only"):
            if target_g - grams > tol:
                self._phase_label = "bulk"
                t_stage = self._t_s()
                grams, status, polls = self._run_bulk_predictive(
                    target_g, grams, t0, state)
                t_marks["bulk"] = self._t_s() - t_stage
                stage_cycles.append(("bulk", polls))
                if status is not None:
                    self._restore_rig()
                    return result(status, grams)
            else:
                stage_cycles.append(("bulk", 0))
            stage_cycles.append(("trickle", 0))
            stage_cycles.append(("tap", 0))
            self.log("=== stages 2-3 skipped (bulk_only: the dose never "
                     "leaves the bulk tilt)")
            return finish(grams)

        # --- bulk -> tap dose: a predictive bulk replaces stages 1-2 ---
        if not p.get("trickle_enabled", True):
            margin = max(0.0, float(p["bulk_stop_margin_g"]))
            if p["bulk_enabled"] and target_g - grams > margin + tol:
                self._phase_label = "bulk"
                t_stage = self._t_s()
                grams, status, polls = self._run_bulk_predictive(
                    target_g, grams, t0, state, to_taps=True)
                t_marks["bulk"] = self._t_s() - t_stage
                stage_cycles.append(("bulk", polls))
                if status is not None:
                    self._restore_rig()
                    return result(status, grams)
            else:
                stage_cycles.append(("bulk", 0))
                self.log("=== stage 1 'bulk' skipped ({:.4f} g to go is "
                         "inside the stop margin)".format(target_g - grams))
            stage_cycles.append(("trickle", 0))
            self.log("=== stage 2 'trickle' off (trickle_enabled 0): the "
                     "tap endgame takes over at {:.4f} g to go".format(
                         target_g - grams))
            return endgame(grams)

        # --- stage 1: bulk (velocity mode, inherited) ------------------
        bulk = self._bulk_phase()
        need_bulk = (p["bulk_enabled"] and
                     target_g - grams > p["trickle_start_remaining_g"]
                     + p["bulk_anticipation_g"])
        if need_bulk:
            self._phase_label = "bulk"
            self.log("=== stage 1 'bulk': {:.4f} g to go, velocity mode "
                     "@ {:.0f} rpm until {:.4f} g to go".format(
                         target_g - grams, bulk["rotation_rpm"],
                         p["trickle_start_remaining_g"]
                         + p["bulk_anticipation_g"]))
            t_stage = self._t_s()
            grams, status, cycles = self._run_phase(
                1, bulk, p["trickle_start_remaining_g"], target_g, grams,
                t0, state)
            t_marks["bulk"] = self._t_s() - t_stage
            stage_cycles.append(("bulk", cycles))
            if self.last_halt is not None:
                ev = self.last_halt
                ev["t_stop_s"] = _round(self._t_s(), 2)
                ev["rate_kf_gps"] = None
                ev["tau_s"] = p["tau_afterflow_s"]
                ev["stalled"] = 0
                self.stop_events.append(ev)
                self.last_halt = None
            if status is not None:
                self._restore_rig()
                return result(status, grams)
        else:
            stage_cycles.append(("bulk", 0))
            self.log("=== stage 1 'bulk' skipped ({:.4f} g to go)".format(
                target_g - grams))

        # --- stage 2: KF + rate-PI trickle -----------------------------
        if target_g - grams > tol:
            self._phase_label = "trickle"
            t_stage = self._t_s()
            grams, status, polls = self._run_trickle(target_g, grams, t0,
                                                     state)
            t_marks["trickle"] = self._t_s() - t_stage
            stage_cycles.append(("trickle", polls))
            if status is not None:
                self._restore_rig()
                return result(status, grams)
        else:
            stage_cycles.append(("trickle", 0))
            self.log("=== stage 2 'trickle' skipped ({:.4f} g to go is "
                     "inside tolerance)".format(target_g - grams))

        return endgame(grams)

    # -- predictive bulk internals (BULK_ONLY, TRICKLE_ENABLED = 0) -----

    def _bulk_taper_rpm(self, remaining_g, end_g):
        """BULK_RPM until BULK_TAPER_START_G to go, then linear down to
        BULK_MIN_RPM at ``end_g`` to go (the tolerance band for a
        bulk-only dose, the stop margin for a bulk -> tap one)."""
        p = self.p
        top = float(p["bulk_rpm"])
        floor = min(top, max(1.0, float(p["bulk_min_rpm"])))
        start = float(p["bulk_taper_start_g"])
        if start <= end_g or remaining_g >= start:
            return top
        frac = max(0.0, (remaining_g - end_g) / (start - end_g))
        return floor + (top - floor) * frac

    def _run_bulk_predictive(self, target_g, grams, t0, state,
                             to_taps=False):
        """Stage 1 that halts on a predicted final mass, at BULK_TILT_DEG.

        Velocity mode like the bulk phase -- instantaneous polls every
        BULK_POLL_MS, cadence taps when BULK_TAP -- with three additions:

        * taper: the rpm follows ``_bulk_taper_rpm`` (slower near the
          goal, so less powder is in flight when the auger halts);
        * boost: every BULK_BOOST_S the trailing slope over that window
          is checked; under 2 mg per window is "no flow" and multiplies
          the rpm by 1.5 (capped at BULK_RPM), flow relaxes it a step.
          No flow at BULK_RPM for the bulk stall window (10 x
          BULK_SETTLE_MS) ends the dose as stalled;
        * predictive halt at the aim, then BULK_SETTLE_MS and a settled
          read.  The prediction is mass + trailing-2 s slope *
          TAU_AFTERFLOW_S, or with BULK_HALT_KF the trickle's Kalman
          filter: m_hat + r_hat * TAU_AFTERFLOW_S + K_SIGMA * sigma.

        BULK_ONLY (``to_taps`` False) aims at goal - TOLERANCE_G/2 and
        runs another pass while more than the tolerance is to go, up to
        BULK_MAX_PASSES.  A bulk -> tap dose (``to_taps``) aims
        BULK_STOP_MARGIN_G short of the goal and makes ONE pass: a
        top-up pass spins 1.5 s before its prediction is trusted, which
        can overshoot a free-flowing powder, so whatever is left goes to
        the tap endgame instead.

        Every halt is a stop event.  Returns (grams, status|None, polls).
        """
        p = self.p
        tol = p["tolerance_g"]
        tau = p["tau_afterflow_s"]
        top = float(p["bulk_rpm"])
        if to_taps:
            margin = max(0.0, float(p["bulk_stop_margin_g"]))
            aim = target_g - margin
            end_g = max(tol, margin)
            max_passes = 1
            tag = "[phase 1 bulk->tap]"
        else:
            aim = target_g - 0.5 * tol
            end_g = tol
            max_passes = max(1, int(p["bulk_max_passes"]))
            tag = "[phase 1 bulk-only]"
        boost_s = max(0.5, float(p["bulk_boost_s"]))
        stall_s = 10 * int(p["bulk_settle_ms"]) / 1000.0
        poll_ms = max(50, int(p["bulk_poll_ms"]))
        min_gain = 0.002
        use_kf = bool(p.get("bulk_halt_kf"))
        k_sigma = float(p["k_sigma"])
        ff = float(p["ff_prior_g_per_rev"])
        cad_on_ms = int(p.get("tap_cadence_on_ms", 60))
        cad_period_ms = 0
        if p.get("bulk_tap"):
            cad_period_ms = max(100, cad_on_ms
                                + int(p.get("tap_cadence_off_ms", 440)))
        self.servo.move_to(p["bulk_tilt_deg"])
        self.log("=== stage 1 'bulk' ({}): {:.4f} g to go at {:.1f} plate "
                 "deg; {:.0f} rpm tapering to {:.0f} over the last {:.0f} mg"
                 ", x1.5 after {:.1f} s without flow; halt when {} >= "
                 "{:.4f} g; cadence taps {}".format(
                     "bulk -> tap, no PI trickle" if to_taps else "bulk_only",
                     target_g - grams, p["bulk_tilt_deg"], top,
                     min(top, float(p["bulk_min_rpm"])),
                     1000.0 * float(p["bulk_taper_start_g"]), boost_s,
                     ("KF m + r*{:.2f}s + {:.1f}*sigma".format(tau, k_sigma)
                      if use_kf else "m + slope*{:.2f}s".format(tau)),
                     aim, "on" if cad_period_ms else "off"))
        polls, passes = 0, 0
        boost = 1.0
        while True:
            passes += 1
            status = None
            hist = []                 # (ticks_ms, grams) this pass
            misses = 0
            rpm = min(top, self._bulk_taper_rpm(target_g - grams, end_g)
                      * boost)
            revs = 0.0
            slope = None
            window_t = self._t_s()    # the current boost window (ms clock)
            dry_since = None          # no flow at full rpm since
            prev_ms = self._tms()
            next_tap = _ticks_add(prev_ms, cad_period_ms)
            kf = None                 # BULK_HALT_KF: built once armed
            m_hat, r_hat, sigma = grams, 0.0, 0.0
            self.stepper.run_at_rpm(rpm)
            try:
                while True:
                    if self._now() - t0 > self.timeout_s:
                        self.log(tag + " dose timeout ({} s)".format(
                            self.timeout_s))
                        status = m3.DoseResult.TIMEOUT
                        break
                    self._sleep_ms(poll_ms)
                    self.stepper.keep_alive()
                    if (cad_period_ms
                            and self._tdiff(self._tms(), next_tap) >= 0):
                        self.tap.tap(1, cad_on_ms, 0)
                        state["taps"] += 1
                        next_tap = _ticks_add(next_tap, cad_period_ms)
                        if self._tdiff(self._tms(), next_tap) > 0:
                            next_tap = _ticks_add(self._tms(), cad_period_ms)
                    reading = self.scale.read()
                    now_ms = self._tms()
                    revs += rpm / 60.0 * self._tdiff(now_ms, prev_ms) / 1000.0
                    prev_ms = now_ms
                    polls += 1
                    if (reading is None or reading.overload
                            or reading.grams is None):
                        misses += 1
                        if misses >= int(p["max_poll_misses"]):
                            self.log(tag + " scale went quiet mid-rotation")
                            status = m3.DoseResult.SCALE_ERROR
                            break
                        continue
                    misses = 0
                    grams = reading.grams - self._baseline_g
                    self._last_grams = grams
                    hist.append((now_ms, grams))
                    if len(hist) > 40:
                        hist.pop(0)
                    slope = m3._recent_slope(hist, 2.0, self._tdiff)
                    # a pass's first polls give a noise-dominated slope
                    # (and an unlearned KF rate) that would halt a top-up
                    # before powder arrives
                    armed = self._tdiff(now_ms, hist[0][0]) >= 1500
                    flowing = armed and slope is not None and slope > 0.0
                    if use_kf and kf is None and flowing and rpm > 1.0:
                        # Started from the poll fit rather than from rest
                        # with the trickle's ff prior: that prior is 3x
                        # salt's, and m_hat ran 140 mg ahead at the halt
                        # of a 0.5 g sim dose.
                        kf = TrickleKF(p["trickle_dt_s"],
                                       tau_bal_s=p["tau_bal_s"],
                                       rate_tau_s=p["rate_tau_s"],
                                       q_var=p["kf_q_var"],
                                       quiet_sd_g=p["quiet_sd_g"],
                                       noisy_sd_g=p["noisy_sd_g"])
                        kf.seed(grams, sigma_g=max(1e-3, self.read_sigma_g),
                                rate_gps=slope)
                        ff = slope / (rpm / 60.0)
                        kf_ms = now_ms
                        m_hat, r_hat = kf.x[0], kf.x[1]
                    elif kf is not None:
                        dt = self._tdiff(now_ms, kf_ms) / 1000.0
                        kf_ms = now_ms
                        m_hat, r_hat = kf.update(
                            grams, True, u_rev_s=rpm / 60.0, ff=ff,
                            fresh=True, dt=min(2.0, max(0.02, dt)))
                        # the slope measures the delivery rate directly
                        # at bulk rpm; ff (g/rev) drifts with the rpm
                        if flowing:
                            ff = 0.9 * ff + 0.1 * (slope / (rpm / 60.0))
                    if kf is not None:
                        sigma = kf.pred_sigma(tau)
                        r = r_hat
                        pred = m_hat + r_hat * tau + k_sigma * sigma
                        self._tel("%.2f,bulk,%.5f,1,%.5f,%.5f,%.5f,%.4f,,,,"
                                  "%.2f,%.5f,%.5f,%d" % (
                                      self._t_s(), grams, m_hat, r_hat,
                                      sigma, ff, rpm, pred, aim,
                                      kf.clamp_hits))
                    else:
                        r = slope if flowing and not use_kf else 0.0
                        pred = grams + r * tau
                        self._tel("%.2f,bulk,%.5f,1,%.5f,%.5f,,,,,,%.2f,"
                                  "%.5f,%.5f,0" % (self._t_s(), grams,
                                                   grams, r, rpm, pred,
                                                   aim))
                    self.log(tag + " poll {}: mass {:.4f} / {:.4f} g ({:.4f}"
                             " g to go), {:.0f} rpm, {:.1f} mg/s, elapsed "
                             "{:.1f} s".format(polls, grams, target_g,
                                               target_g - grams, rpm,
                                               1000.0 * r, self._t_s()))
                    if (self.overshoot_abort_g > 0.0
                            and grams > target_g + self.overshoot_abort_g):
                        self.log(tag + " overshoot guard: {:+.1f} mg past "
                                 "the target -- aborting".format(
                                     1000.0 * (grams - target_g)))
                        status = m3.DoseResult.OVERSHOOT
                        break
                    if pred >= aim:
                        break
                    now = self._t_s()
                    if now - window_t >= boost_s:
                        flow = m3._recent_slope(hist, boost_s, self._tdiff)
                        window_t = now
                        if flow is None or flow * boost_s < min_gain:
                            if rpm < top - 1e-6:
                                boost *= 1.5
                                self.log(tag + " no flow for {:.1f} s -- "
                                         "rpm up".format(boost_s))
                            elif dry_since is None:
                                dry_since = now - boost_s
                            elif now - dry_since > stall_s:
                                self.log(tag + " no powder flow for {:.1f} s"
                                         " at {:.0f} rpm -- hopper empty or "
                                         "jam".format(now - dry_since, rpm))
                                status = m3.DoseResult.STALLED
                                break
                        else:
                            dry_since = None
                            boost = max(1.0, boost / 1.5)
                    want = min(top, self._bulk_taper_rpm(target_g - grams,
                                                         end_g) * boost)
                    if abs(want - rpm) >= 1.0:
                        rpm = want
                        self.stepper.run_at_rpm(rpm)
            finally:
                self.stepper.stop()
            state["deg"] += revs * 360.0
            if kf is not None:
                self.last_ff = ff
            if status is not None:
                return grams, status, polls
            # the stop event pairs the halt estimate with its own rate,
            # so the tau fit stays consistent with the predictor in use
            m_stop = m_hat if kf is not None else grams
            t_stop_s = self._t_s()
            self.log(tag + " auger halted (pass {}) at {:.0f} rpm with "
                     "{:.4f} g to go; settling {} ms".format(
                         passes, rpm, max(0.0, target_g - grams),
                         int(p["bulk_settle_ms"])))
            self._sleep_ms(int(p["bulk_settle_ms"]))
            settled = self._read_grams()
            if settled is None:
                return grams, m3.DoseResult.SCALE_ERROR, polls
            self.stop_events.append({
                "phase": "bulk", "pass": passes, "stalled": 0,
                "t_stop_s": _round(t_stop_s, 2),
                "m_stop_g": m_stop, "settled_g": settled,
                "afterflow_g": settled - m_stop,
                "rate_slope_gps": slope,
                "rate_kf_gps": r_hat if kf is not None else None,
                "predictor": "kf" if kf is not None else "slope",
                "rpm": _round(rpm, 1), "tau_s": tau,
            })
            self._tel("%.2f,bulk_end,%.5f,1,%.5f,,,,,,,,,,0" % (
                self._t_s(), settled, settled))
            grams = settled
            self._last_grams = grams
            self.log(tag + " settled: mass {:.4f} / {:.4f} g ({:+.1f} mg "
                     "after the halt, {:+.1f} mg vs target)".format(
                         grams, target_g, 1000.0 * (grams - m_stop),
                         1000.0 * (grams - target_g)))
            if to_taps or target_g - grams <= tol:
                return grams, None, polls
            if passes >= max_passes:
                self.log(tag + " pass budget ({}) spent {:.1f} mg short"
                         .format(max_passes, 1000.0 * (target_g - grams)))
                return grams, m3.DoseResult.BUDGET, polls
            self.log(tag + " {:.1f} mg short -- pass {}".format(
                1000.0 * (target_g - grams), passes + 1))

    # -- stage 2 internals ---------------------------------------------

    def _run_trickle(self, target_g, grams, t0, state):
        """The ported controller loop.  Returns (grams, status|None, polls)."""
        p = self.p
        set_rpm = getattr(self.stepper, "set_velocity_rpm", None)
        if set_rpm is None:
            self.log("[trickle] stepper has no set_velocity_rpm() -- run "
                     "main_trickle.py (its TrickleStepper), not main.py")
            return grams, m3.DoseResult.SCALE_ERROR, 0

        self.servo.move_to(p["trickle_tilt_deg"])
        self._sleep_ms(800)
        m0 = self._read_grams()               # settled, bracketed seed
        if m0 is None:
            return grams, m3.DoseResult.SCALE_ERROR, 0
        kf = TrickleKF(p["trickle_dt_s"], tau_bal_s=p["tau_bal_s"],
                       rate_tau_s=p["rate_tau_s"], q_var=p["kf_q_var"],
                       quiet_sd_g=p["quiet_sd_g"],
                       noisy_sd_g=p["noisy_sd_g"])
        # Seed covariance from the bracket's measured noise (>= 1 mg floor)
        # rather than the twin's diag(0.05) -- see TrickleKF.seed.
        kf.seed(m0, sigma_g=max(1e-3, self.read_sigma_g))
        tau = p["tau_afterflow_s"]
        margin = p["cutoff_margin_g"]
        cutoff_g = target_g - margin
        integ, rpm, revs = 0.0, 0.0, 0.0
        ff = p["ff_prior_g_per_rev"]
        m, r, sigma = m0, 0.0, kf.pred_sigma(tau)
        last_m, last_gain_t = m0, self._now()
        dt_ms = max(50, int(p["trickle_dt_s"] * 1000))
        prev_ms = self._tms()
        polls, misses = 0, 0
        stalled = False
        status = None
        # Cadence tapping during the trickle (issue #164): one
        # tap_cadence_on_ms pulse per (on + off) period.  The solenoid
        # shakes the pan, so every poll counts as "noisy" to the KF
        # while the knob is on.
        cad_on_ms = int(p.get("tap_cadence_on_ms", 60))
        cad_period_ms = 0
        if p.get("trickle_tap"):
            cad_period_ms = max(100, cad_on_ms
                                + int(p.get("tap_cadence_off_ms", 440)))
            self.log("[trickle] cadence taps on: one {} ms pulse per "
                     "{} ms".format(cad_on_ms, cad_period_ms))
        next_tap = prev_ms + cad_period_ms
        hist = []                     # (ticks_ms, z) fresh polls for the
                                      # stop-event trailing slope
        print_every = max(1, int(p["print_every_n_polls"]))
        self.log("[trickle] seeded at {:.4f} g; cutoff when m+r*{:.2f}s"
                 "+{:.1f}*sigma >= {:.4f} g".format(m0, tau, p["k_sigma"],
                                                    cutoff_g))
        try:
            while True:
                if self._now() - t0 > self.timeout_s:
                    self.log("[trickle] dose timeout ({} s)".format(
                        self.timeout_s))
                    status = m3.DoseResult.TIMEOUT
                    break
                self._sleep_ms(dt_ms)
                self.stepper.keep_alive()
                if (cad_period_ms
                        and self._tdiff(self._tms(), next_tap) >= 0):
                    self.tap.tap(1, cad_on_ms, 0)
                    state["taps"] += 1
                    next_tap = _ticks_add(next_tap, cad_period_ms)
                    if self._tdiff(self._tms(), next_tap) > 0:
                        next_tap = _ticks_add(self._tms(), cad_period_ms)
                reading = self.scale.read()
                now_ms = self._tms()
                dt = self._tdiff(now_ms, prev_ms) / 1000.0
                dt = min(2.0, max(0.02, dt))
                prev_ms = now_ms
                polls += 1
                revs += (rpm / 60.0) * dt
                fresh = (reading is not None and reading.grams is not None
                         and not reading.overload)
                if fresh:
                    misses = 0
                    z = reading.grams - self._baseline_g
                    hist.append((now_ms, z))
                    if len(hist) > 40:
                        hist.pop(0)
                else:
                    misses += 1
                    if misses >= int(p["max_poll_misses"]):
                        self.log("[trickle] scale went quiet mid-trickle")
                        status = m3.DoseResult.SCALE_ERROR
                        break
                    z = 0.0                   # unused when fresh is False
                m, r = kf.update(z, rpm > 1e-6 or cad_period_ms > 0,
                                 u_rev_s=rpm / 60.0, ff=ff,
                                 fresh=fresh, dt=dt)
                self._last_grams = m
                if revs > 0.3 and m - m0 > 1e-3:
                    ff = 0.9 * ff + 0.1 * ((m - m0) / revs)
                sigma = kf.pred_sigma(tau)
                pred = m + r * tau + p["k_sigma"] * sigma

                remaining = target_g - m
                r_sp = (remaining - margin) / (2.0 * tau)
                if r_sp < p["trickle_min_rate_gps"]:
                    r_sp = p["trickle_min_rate_gps"]
                elif r_sp > p["trickle_max_rate_gps"]:
                    r_sp = p["trickle_max_rate_gps"]
                err = r_sp - r

                self._tel("%.2f,trickle,%s,%d,%.5f,%.5f,%.5f,%.4f,%.5f,"
                          "%.5f,%.4f,%.2f,%.5f,%.5f,%d" % (
                              self._t_s(), ("%.5f" % z) if fresh else "",
                              1 if fresh else 0, m, r, sigma, ff, r_sp,
                              err, integ, rpm, pred, cutoff_g,
                              kf.clamp_hits))
                if polls % print_every == 0:
                    self.log("[trickle] {:5.1f}s m {:.4f} r {:5.1f} mg/s "
                             "(sp {:5.1f}) rpm {:5.1f} pred {:.4f}/{:.4f} "
                             "sigma {:.1f} mg".format(
                                 self._t_s(), m, 1000.0 * r, 1000.0 * r_sp,
                                 rpm, pred, cutoff_g, 1000.0 * sigma))

                if pred >= cutoff_g:
                    self.log("[trickle] predictive cutoff: m {:.4f} + "
                             "r*tau {:.4f} + k*sigma {:.4f} >= {:.4f} g"
                             .format(m, r * tau, p["k_sigma"] * sigma,
                                     cutoff_g))
                    break
                if m - last_m > 2e-3:
                    last_m, last_gain_t = m, self._now()
                elif self._now() - last_gain_t > p["stall_bail_s"]:
                    self.log("[trickle] no gain for {:.0f} s -- stalled; "
                             "handing to the tap endgame".format(
                                 p["stall_bail_s"]))
                    stalled = True
                    break

                integ += err * dt
                if integ > p["trickle_integ_clamp"]:
                    integ = p["trickle_integ_clamp"]
                elif integ < -p["trickle_integ_clamp"]:
                    integ = -p["trickle_integ_clamp"]
                rpm = p["trickle_kp"] * err + p["trickle_ki"] * integ
                if rpm < 0.0:
                    rpm = 0.0
                elif rpm > p["trickle_rpm_cap"]:
                    rpm = p["trickle_rpm_cap"]
                set_rpm(rpm)
        finally:
            self.stepper.stop()               # halt + re-zero shadow position
            # set_velocity_rpm left the max-speed register at the last PI
            # command (possibly ~0); restore it or the tap-phase nudges crawl
            self.stepper.set_speed(self.cfg.STEPPER_SPEED_RPM)
        state["deg"] += revs * 360.0
        self.last_ff = ff
        if status is not None:
            return grams, status, polls
        m_stop, r_stop = m, r         # KF estimates at the halt
        t_stop_s = self._t_s()
        self._sleep_ms(int(p["post_trickle_settle_ms"]))
        settled = self._read_grams()
        if settled is None:
            return m, m3.DoseResult.SCALE_ERROR, polls
        # Stop event (issue #164 section 2.8): rate at stop from the KF
        # r_hat AND the trailing-2 s poll slope (both #131 definitions),
        # at-stop mass estimate, settled mass, and the afterflow delta.
        self.stop_events.append({
            "phase": "trickle",
            "stalled": 1 if stalled else 0,
            "t_stop_s": _round(t_stop_s, 2),
            "m_stop_g": _round(m_stop, 5),
            "settled_g": _round(settled, 5),
            "afterflow_g": _round(settled - m_stop, 5),
            "rate_kf_gps": _round(r_stop, 5),
            "rate_slope_gps": _round(
                m3._recent_slope(hist, 2.0, self._tdiff), 5),
            "tau_s": tau,
        })
        self._tel("%.2f,trickle_end,%.5f,1,%.5f,,,,,,,,,,%d" % (
            self._t_s(), settled, settled, kf.clamp_hits))
        self.log("[trickle] halted{}; settled at {:.4f} g ({:+.1f} mg vs "
                 "KF m_hat, {:.4f} g to go), {} polls, {} KF clamps, "
                 "ff {:.3f} g/rev".format(
                     " (stalled)" if stalled else "", settled,
                     1000.0 * (settled - m), max(0.0, target_g - settled),
                     polls, kf.clamp_hits, ff))
        return settled, None, polls
