"""One 3 g dose of carboxymethyl cellulose with the plate held at 60 deg
and the solenoid tapping (PR #131, 2026-11-24).

Requested by XZaitzeff on 2026-11-24 (PR #131): "carboxymethyl cellulose
is in the auger.  Dose 3 g at 60 degrees with tapping".

This is three_phase_tilt_trials.py (version 2026-11-20e, the November
stepped-tilt protocol) cut down to ONE dose at ONE fixed angle:

* the plate is held at FIXED_TILT = 60 deg in all three stages (bulk,
  fine and tap stage), instead of stepping the bulk 60 -> 40 deg and
  running the fine stage at 30 deg and the tap stage at 0 deg;
* "with tapping": the bulk and fine stages fire the November cadence
  taps (one 60 ms pulse per 300 ms while the auger spins), and the tap
  stage is the stock one (one tap and a 15 deg auger turn per cycle,
  +/-1 mg tolerance), at 60 deg;
* bulk 80 rpm continuous, fine 25 rpm continuous with 20 mg anticipation,
  tap-stage turns at 25 rpm, thresholds 0.25 / 0.025 / 0.001 g: all the
  November values;
* the dose timeout is DOSE_TIMEOUT_S = 900 s (stock 600 s), because CMC
  is a slow, cohesive powder (2026-08-05 battery: 26 mg/rev at 22.5 deg,
  about 2 mg/rev at 45 deg once it arches) and 3 g is 1.5x the November
  2 g target;
* after the dose the cup is read at 60 deg (as November did, at the last
  stage's angle) and again after the plate is back at 0 deg, the angle
  the baseline was taken at, so the tilt's own offset on the balance
  drops out of the second reading;
* if the dose ends failed early (stalled / scale error / cycle budget)
  the script may run ONE top-up dose for what is still missing from 3 g
  (measured at 0 deg against the session start), if it can start within
  SESSION_BUDGET_S; its timeout ends it by SESSION_HARD_S.  An ok or
  overshoot dose is never topped up, and nor is a timeout (the powder
  feeds, only too slowly, so a top-up would hit the same wall).

Runs ON the Pico via ``mpremote run`` (RAM only -- nothing is written to
the Pico filesystem).  The controller is the Pico's own
``main_three_phase.ThreePhaseDoser`` (the issue #164 build), unmodified
apart from four hooks that change nothing about its decisions:

1. ``_tare_and_baseline`` takes a bracket of the current reading as the
   baseline and does NOT send the A&D tare -- on this bench the tare
   stops the balance answering ``Q`` while the pan is loaded, so masses
   are tracked absolutely and every dose is a difference (as in the
   2026-08-17 batteries).
2. the doser's sleeps, and the stepper's wait during position moves,
   read the balance while they wait, so the mass is logged at ~10 Hz for
   the whole trial, settle waits included (each read is logged, never
   used by the controller);
3. the bulk tilt schedule hook is kept from the November script but has
   a single angle (FIXED_TILT), so it never steps the plate;
4. the thresholds and every stall rule stay stock; the dose timeout is
   DOSE_TIMEOUT_S (above).

Parameters that differ from the stock phase dicts (all per the request
or the November protocol):

    bulk  angle 60 deg, 80 rpm, continuous, one 60 ms tap per 300 ms
          while the auger spins, no anticipation
    fine  angle 60 deg, 25 rpm, continuous, the same cadence taps,
          anticipation FINE_ANTICIPATION_G = 20 mg
    tap   stock (1 tap + 15 deg per cycle, 1.5 s settle, 5 deg nudge
          after 3 dry cycles, up to 10, +/-1 mg) but at 60 deg, with its
          15 deg turns at 25 rpm
    poll  continuous stages poll every POLL_MS (stock 250 ms)

Each dose (attempt) is logged as a "trial" in the November format, so
scripts/analyze_tilt_trials.py reads the session log unchanged.

Telemetry (CSV over USB stdout; the Pi stamps each line with its UTC
receipt time, which anchors the Pico clock):

    M,<key>,<value>                                    metadata
    S,<trial>,<t_ms>,<src>,<stat>,<grams>,<stage>,<tilt>,<rpm>,<taps>,<dur>
        one balance frame; grams is the ABSOLUTE display (blank if none),
        stat ST/US/OL/NA, src poll|bracket|fill, tilt = plate deg, rpm =
        commanded auger rpm, taps = cumulative this trial, dur = how long
        the Q poll took (ms); t_ms is when the reply arrived
    E,<trial>,<t_ms>,<event text>                      actuator/stage event
    L,<trial>,<t_ms>,<controller log line>             ThreePhaseDoser log
    T,<json>                                           one trial summary
    SUMMARY,<json>                                     end of session
"""

import gc
import json
import time

import config
import main_three_phase as m3

SCRIPT_VERSION = "2026-11-24b"
POWDER_ID = "carboxymethyl-cellulose"   # the #116 battery's id

FIRST_TRIAL = 2                # 24b: the top-up is dose 2 (24a: 1)
N_TRIALS = 1                   # 24b: the top-up only (24a: 2, a dose and a
                               # possible top-up after an early failure)
TARGET_G = 3.0                 # total into the cup, both doses together
# 24b: the cup's reading at 0 deg before dose 1 (24a's baseline, 19:52:44
# UTC).  The top-up doses TARGET_G minus what the cup has gained since.
TOPUP_OF_ABS0_G = 0.0429       # None in 24a
# 24b thresholds: the bulk halts 8 mg short and the fine stage is skipped
# (0.4 mg/s at 25 rpm in 24a); the tap stage finishes to +/-1 mg.
THRESHOLDS = (0.008, 0.008, 0.001)   # None in 24a (stock 0.25/0.025/0.001)
TAP_ROT_DEG = 45.0             # 24b: tap-stage turn (stock 15 deg = ~0.1 mg
                               # of CMC at 60 deg in 24a)

FIXED_TILT = 60.0              # plate deg, every stage (the request)
BULK_RPM = 80.0                # November bulk speed
BULK_TILTS = (FIXED_TILT,)     # one angle: the schedule never steps
SCHED_FLOW_G = 0.002
SCHED_DWELL_S = 3.0
BULK_TAP_ON_MS = 60            # "with tapping": November cadence taps,
BULK_TAP_PERIOD_MS = 300       # one 60 ms pulse per 300 ms while spinning
FINE_TAPS = True
FINE_TILT = FIXED_TILT
FINE_RPM = 25.0
FINE_ANTICIPATION_G = 0.020
TAP_TILT = FIXED_TILT
TAP_STAGE_RPM = FINE_RPM       # speed of the tap stage's 15 deg turns
DOSE_TIMEOUT_S = 420           # 24b (900 in 24a; stock 600 s)

POLL_MS = 80                   # continuous-stage poll sleep (stock 250)
FILL_PERIOD_MS = 95            # extra reads while waiting: ~10 Hz
FILL_MIN_REM_MS = 40           # only start a fill read with this much left
FILL_TIMEOUT_MS = 150          # and give up on it quickly

PREROLL_S = 20.0               # 24b: 20 s, long enough for a drift fit (5 in 24a)
POSTROLL_S = 8.0               # logged after the controller finishes
HOME_SETTLE_S = 6.0            # logged after the plate is back at 0 deg

# --- safety ----------------------------------------------------------------
CUP_HARD_G = 6.0               # any frame this far over the session start
                               # -> abort (twice the target)
BAL_MAX_G = 41.0               # displayed ceiling (the beaker goes OL at
                               # about 43.1 g displayed)
TOPUP_MIN_G = 0.002            # don't top up for less than this
SESSION_BUDGET_S = 16 * 60     # no top-up dose starts after this ...
SESSION_HARD_S = 20 * 60       # ... and a top-up's timeout ends it by this


# ---------------------------------------------------------------------------
# clock + context
# ---------------------------------------------------------------------------

_T0 = time.ticks_ms()


def t_ms():
    return time.ticks_diff(time.ticks_ms(), _T0)


class Ctx:
    trial = 0
    stage = "init"
    src = "poll"
    tilt = 0.0
    rpm = 0.0
    move_until = None          # ticks when a position move should be done
    spinning = False
    taps = 0
    base = None                # this trial's baseline (absolute g)
    abs0 = None                # session baseline (absolute g)
    last_abs = None
    last_read_t = None         # ticks of the start of the last read
    abort = None               # reason string once a hard cap trips
    sched_on = False
    sched_band_g = 0.15
    sched_idx = 0
    sched_ref = None           # bulk mass at the last flow / step
    sched_t = None             # ticks of the last flow / step
    servo = None
    stepper = None
    scale = None
    scale_inner = None


C = Ctx()


class HardCap(Exception):
    pass


def ev(msg):
    print("E,{},{},{}".format(C.trial, t_ms(), msg))


def meta(key, value):
    print("M,{},{}".format(key, value))


def clog(msg):
    print("L,{},{},{}".format(C.trial, t_ms(), msg))


def rpm_now():
    if C.move_until is not None:
        if time.ticks_diff(time.ticks_ms(), C.move_until) >= 0:
            C.move_until = None
            C.rpm = 0.0
    return C.rpm


# ---------------------------------------------------------------------------
# logged hardware wrappers (duck-typed for ThreePhaseDoser)
# ---------------------------------------------------------------------------

class LoggedScale:
    """Logs every frame; trips the hard cap; drives the bulk tilt schedule."""

    def __init__(self, inner):
        self.inner = inner

    def read(self):
        t_a = time.ticks_ms()
        C.last_read_t = t_a
        r = self.inner.read()
        stat = "NA"
        grams = ""
        if r is not None:
            stat = r.status
            if r.grams is not None:
                grams = "{:.4f}".format(r.grams)
        print("S,{},{},{},{},{},{},{:.1f},{:.1f},{},{}".format(
            C.trial, t_ms(), C.src, stat, grams, C.stage, C.tilt,
            rpm_now(), C.taps, time.ticks_diff(time.ticks_ms(), t_a)))
        if r is None:
            return r
        if r.overload:
            C.abort = "balance overload (OL)"
            raise HardCap(C.abort)
        if r.grams is None:
            return r
        C.last_abs = r.grams
        if r.grams > BAL_MAX_G:
            C.abort = "display {:.3f} g over the {:.0f} g ceiling".format(
                r.grams, BAL_MAX_G)
            raise HardCap(C.abort)
        if C.abs0 is not None and r.grams - C.abs0 > CUP_HARD_G:
            C.abort = "cup holds {:.3f} g, hard cap {:.1f} g".format(
                r.grams - C.abs0, CUP_HARD_G)
            raise HardCap(C.abort)
        if C.sched_on and C.spinning and C.base is not None:
            _schedule_tilt(r.grams - C.base)
        return r

    def read_stable(self, timeout_ms=10000):
        # Not used (the doser reads brackets); kept for the duck type.
        waited = 0
        last = None
        while waited <= timeout_ms:
            r = self.read()
            if r is not None:
                last = r
                if r.stable:
                    return r
            time.sleep_ms(100)
            waited += 200
        return last

    def zero(self):
        raise RuntimeError("no hardware tare in this battery")


def _schedule_tilt(m_rel):
    """1a: step the plate down one band at a time as the cup fills.

    Plus the no-flow fallback: an angle that delivers nothing for
    SCHED_DWELL_S while the auger spins is left for the next one.
    """
    now = time.ticks_ms()
    if C.sched_ref is None or m_rel - C.sched_ref >= SCHED_FLOW_G:
        C.sched_ref = m_rel
        C.sched_t = now
    last = len(BULK_TILTS) - 1
    idx = int(m_rel / C.sched_band_g) if m_rel > 0 else 0
    if idx > last:
        idx = last
    why = "band"
    if idx <= C.sched_idx:           # monotonic: never tilts back up
        if (C.sched_idx < last and
                time.ticks_diff(now, C.sched_t) >= SCHED_DWELL_S * 1000):
            idx = C.sched_idx + 1
            why = "no flow for {:.1f} s".format(SCHED_DWELL_S)
        else:
            return
    ev("tilt schedule: {:.4f} g in the cup -> step {} ({:.1f} deg, {})"
       .format(m_rel, idx, BULK_TILTS[idx], why))
    C.sched_idx = idx
    C.servo.move_to(BULK_TILTS[idx])
    C.sched_ref = m_rel
    C.sched_t = time.ticks_ms()


def fill_read():
    """One extra logged read while the controller waits (never used by it)."""
    prev_src = C.src
    prev_to = C.scale_inner.response_timeout_ms
    C.src = "fill"
    C.scale_inner.response_timeout_ms = FILL_TIMEOUT_MS
    try:
        C.scale.read()
    finally:
        C.src = prev_src
        C.scale_inner.response_timeout_ms = prev_to


def lsleep(ms):
    """Sleep ``ms`` while reading the balance about every FILL_PERIOD_MS."""
    end = time.ticks_add(time.ticks_ms(), int(ms))
    while True:
        now = time.ticks_ms()
        rem = time.ticks_diff(end, now)
        if rem <= 0:
            return
        due = (C.last_read_t is None or
               time.ticks_diff(now, C.last_read_t) >= FILL_PERIOD_MS)
        if due and rem >= FILL_MIN_REM_MS:
            if C.stepper is not None:
                C.stepper.keep_alive()
            fill_read()
        else:
            time.sleep_ms(rem if rem < 10 else 10)


class LoggedServo:
    def __init__(self, inner):
        self.inner = inner

    @property
    def angle(self):
        return self.inner.angle

    def move_to(self, deg):
        a0 = self.inner.angle
        if abs(a0 - deg) < 0.05:
            return
        ev("servo start {:.1f} -> {:.1f} deg".format(a0, deg))
        self.inner.move_to(deg)
        C.tilt = self.inner.angle
        ev("servo at {:.1f} deg".format(C.tilt))


class LoggedTap:
    def __init__(self, inner):
        self.inner = inner

    def tap(self, count=None, on_ms=None, off_ms=None):
        n = config.TAP_COUNT if count is None else int(count)
        ev("tap x{} ({} on / {} off ms)".format(n, on_ms, off_ms))
        self.inner.tap(count, on_ms, off_ms)
        C.taps += n

    def _off(self):
        self.inner._off()


def wrap_stepper(st):
    """Log auger commands; read the balance during position-move waits."""
    orig_run = st.run_at_rpm
    orig_stop = st.stop
    orig_rot = st.rotate_degrees

    def run_at_rpm(rpm):
        orig_run(rpm)
        C.rpm = st._rpm
        C.move_until = None
        C.spinning = True
        ev("auger run {:.1f} rpm".format(st._rpm))

    def stop():
        ev("auger halt")
        C.spinning = False
        C.rpm = 0.0
        C.move_until = None
        orig_stop()

    def rotate_degrees(deg):
        rpm = st._rpm
        move_ms = int(abs(deg) / 360.0 * 60.0 / max(0.1, rpm) * 1000) + 150
        ev("auger rotate {:.1f} deg @ {:.1f} rpm".format(deg, rpm))
        C.rpm = rpm
        C.move_until = time.ticks_add(time.ticks_ms(), move_ms)
        try:
            orig_rot(deg)
        finally:
            C.rpm = 0.0
            C.move_until = None

    def wait_estimated_time(delta):
        # The stock wait (estimated move time + 2 s margin, keep-alive
        # every 50 ms), reading the balance while it waits.
        usteps_per_s = max(1.0, st._rpm / 60.0 * st.steps_per_rev)
        est_s = abs(delta) / usteps_per_s + 0.2
        deadline = time.ticks_add(time.ticks_ms(), int(est_s * 1000) + 2000)
        while time.ticks_diff(deadline, time.ticks_ms()) > 0:
            st.keep_alive()
            lsleep(50)

    st.run_at_rpm = run_at_rpm
    st.stop = stop
    st.rotate_degrees = rotate_degrees
    st._wait_estimated_time = wait_estimated_time
    return st


# ---------------------------------------------------------------------------
# controller hooks
# ---------------------------------------------------------------------------

class Doser(m3.ThreePhaseDoser):
    halts = None

    def _collect_retry(self, retries=m3.DOSE_READ_RETRIES):
        prev = C.src
        C.src = "bracket"
        try:
            return m3.ThreePhaseDoser._collect_retry(self, retries)
        finally:
            C.src = prev

    def _tare_and_baseline(self, target_g):
        # No A&D tare (see the module docstring): the baseline is a
        # bracket of the current reading, subtracted from every read.
        self._baseline_g = 0.0
        bracket = self._collect_retry()
        if bracket is None:
            return False, 0.0
        baseline = bracket.value_at(bracket.mid_t_ms)
        self.baseline_drift_g_per_s = bracket.slope_g_per_s
        self.read_sigma_g = bracket.resid_rms_g
        self.last_baseline_g = baseline
        if baseline > BAL_MAX_G:
            self.log("[dose] pan reads {:.4f} g, over the {:.0f} g ceiling"
                     .format(baseline, BAL_MAX_G))
            return False, baseline
        self._baseline_g = baseline
        C.base = baseline
        self.log("[dose] baseline {:.4f} g absolute (no tare), drift "
                 "{:+.1f} mg/min, read noise {:.2f} mg".format(
                     baseline, 60000.0 * self.baseline_drift_g_per_s,
                     1000.0 * self.read_sigma_g))
        return True, 0.0

    def _run_phase(self, num, p, exit_g, target_g, grams, t0, state):
        C.stage = p["name"]
        ev("stage {} start ({:.4f} g in, exit at {:.4f} g to go)".format(
            p["name"], grams, exit_g))
        C.sched_on = (num == 1)
        C.sched_idx = 0
        C.sched_ref = None
        C.sched_t = None
        try:
            return m3.ThreePhaseDoser._run_phase(
                self, num, p, exit_g, target_g, grams, t0, state)
        finally:
            C.sched_on = False
            ev("stage {} end".format(p["name"]))

    def _run_phase_continuous(self, num, p, exit_g, target_g, grams, t0,
                              state):
        self.last_halt = None
        out = m3.ThreePhaseDoser._run_phase_continuous(
            self, num, p, exit_g, target_g, grams, t0, state)
        if self.last_halt is not None and self.halts is not None:
            self.halts.append(dict(self.last_halt))
        return out


def build_phases():
    p1 = dict(m3.PHASE1_BULK)
    p1.update({"angle_deg": BULK_TILTS[0], "rotation_rpm": BULK_RPM,
               "continuous": 1, "poll_ms": POLL_MS, "anticipation_g": 0.0,
               # cadence taps (velocity mode): one tap_on_ms pulse per
               # tap_on_ms + tap_off_ms while the auger spins
               "taps_per_cycle": 1, "tap_on_ms": BULK_TAP_ON_MS,
               "tap_off_ms": BULK_TAP_PERIOD_MS - BULK_TAP_ON_MS})
    p2 = dict(m3.PHASE2_FINE)
    p2.update({"angle_deg": FINE_TILT, "rotation_rpm": FINE_RPM,
               "continuous": 1, "poll_ms": POLL_MS,
               "anticipation_g": FINE_ANTICIPATION_G,
               "taps_per_cycle": 1 if FINE_TAPS else 0,
               "tap_on_ms": BULK_TAP_ON_MS,
               "tap_off_ms": BULK_TAP_PERIOD_MS - BULK_TAP_ON_MS})
    p3 = dict(m3.PHASE3_TAP)
    p3.update({"angle_deg": TAP_TILT, "rotation_rpm": TAP_STAGE_RPM})
    if TAP_ROT_DEG is not None:
        p3.update({"rotation_deg": TAP_ROT_DEG})
    return [p1, p2, p3]


# ---------------------------------------------------------------------------
# session
# ---------------------------------------------------------------------------

def stream(seconds):
    end = time.ticks_add(time.ticks_ms(), int(seconds * 1000))
    while time.ticks_diff(end, time.ticks_ms()) > 0:
        C.scale.read()
        rem = time.ticks_diff(end, time.ticks_ms())
        if rem <= 0:
            break
        lsleep(min(rem, FILL_PERIOD_MS))


def mean_reads(n=8, gap_ms=95):
    vals = []
    for _ in range(n):
        r = C.scale.read()
        if r is not None and r.grams is not None and not r.overload:
            vals.append(r.grams)
        lsleep(gap_ms)
    if not vals:
        return None
    vals.sort()
    return vals[len(vals) // 2]          # median


def safe_state(servo, stepper, tap):
    try:
        stepper.stop()
    except Exception:
        pass
    try:
        stepper.enable(False)
    except Exception:
        pass
    try:
        tap._off()
    except Exception:
        pass
    try:
        servo.move_to(0.0)
    except Exception:
        pass


def file_sha(name):
    try:
        import hashlib
        import binascii
        h = hashlib.sha256()
        with open(name, "rb") as fh:
            while True:
                b = fh.read(512)
                if not b:
                    break
                h.update(b)
        return binascii.hexlify(h.digest()).decode()[:16]
    except Exception as exc:
        return "n/a ({})".format(exc)


def main(hw=None):
    """``hw`` = (stepper, tap, servo, scale) for the CPython sim."""
    meta("script", "fixed_tilt_dose.py " + SCRIPT_VERSION)
    meta("powder_id", POWDER_ID)
    meta("main_three_phase_sha16", file_sha("main_three_phase.py"))
    meta("config_sha16", file_sha("config.py"))
    meta("scale_sha16", file_sha("scale.py"))
    meta("balance_filter_sha16", file_sha("balance_filter.py"))
    meta("n_trials", N_TRIALS)
    meta("first_trial", FIRST_TRIAL)
    meta("target_g", TARGET_G)
    meta("fixed_tilt_deg", FIXED_TILT)
    meta("bulk", "rpm {} tilt {:.0f} continuous cadence-taps {} ms per {} ms "
         "anticipation 0".format(BULK_RPM, FIXED_TILT, BULK_TAP_ON_MS,
                                 BULK_TAP_PERIOD_MS))
    meta("fine", "tilt {} rpm {} continuous {} anticipation {}".format(
        FINE_TILT, FINE_RPM,
        ("cadence-taps {} ms per {} ms".format(BULK_TAP_ON_MS,
                                               BULK_TAP_PERIOD_MS)
         if FINE_TAPS else "no-taps"),
        FINE_ANTICIPATION_G))
    meta("tap", "stock PHASE3_TAP at {} deg, turns at {} rpm".format(
        TAP_TILT, TAP_STAGE_RPM))
    meta("thresholds", "/".join("{}".format(v) for v in
                                (THRESHOLDS if THRESHOLDS else m3.THRESHOLDS)))
    meta("topup_of_abs0_g", TOPUP_OF_ABS0_G)
    meta("dose_timeout_s", DOSE_TIMEOUT_S)
    meta("poll_ms", POLL_MS)
    meta("fill_period_ms", FILL_PERIOD_MS)
    meta("preroll_s", PREROLL_S)
    meta("postroll_s", POSTROLL_S)
    meta("home_settle_s", HOME_SETTLE_S)
    meta("cup_hard_g", CUP_HARD_G)
    meta("session_budget_s", SESSION_BUDGET_S)
    meta("topup", "one top-up dose for the rest of {} g if the dose ends "
         "failed".format(TARGET_G))
    meta("tare", "none (baseline bracket per dose)")

    C.stepper = None
    if hw is None:
        stepper = m3.Stepper()
        tap = m3.Tap()
        servo = m3.Servo()
        scale = m3.Scale()
    else:
        stepper, tap, servo, scale = hw
    C.scale_inner = scale
    C.scale = LoggedScale(scale)
    C.stepper = wrap_stepper(stepper)
    servo_w = LoggedServo(servo)
    C.servo = servo_w
    tap_w = LoggedTap(tap)
    C.tilt = servo.angle

    phases = build_phases()
    thresholds = list(THRESHOLDS if THRESHOLDS else m3.THRESHOLDS)
    C.sched_band_g = TARGET_G        # one angle: never steps
    for i, p in enumerate(phases):
        meta("phase{}".format(i + 1), json.dumps(p))
    doser = Doser(C.stepper, tap_w, servo_w, C.scale, config,
                  phases=phases, thresholds=thresholds,
                  timeout_s=DOSE_TIMEOUT_S, log=clog, sleep_ms=lsleep)

    results = []
    stop_reason = "dose done"
    session_t0 = time.ticks_ms()
    try:
        servo_w.move_to(0.0)
        C.stage = "session"
        stream(2.0)
        C.abs0 = mean_reads()
        if C.abs0 is None:
            stop_reason = "balance silent at session start"
            raise HardCap(stop_reason)
        meta("abs0_g", "{:.4f}".format(C.abs0))
        cup_total = 0.0                  # at 0 deg, against the session start
        if TOPUP_OF_ABS0_G is not None:  # 24b: what dose 1 already put in
            cup_total = C.abs0 - TOPUP_OF_ABS0_G
            ev("cup holds {:.4f} g since dose 1's baseline ({:.4f} g)".format(
                cup_total, TOPUP_OF_ABS0_G))
            if TARGET_G - cup_total < TOPUP_MIN_G:
                stop_reason = "{:.4f} g in the cup: nothing to top up".format(
                    cup_total)
                raise HardCap(stop_reason)
        trial = FIRST_TRIAL - 1
        while trial < FIRST_TRIAL + N_TRIALS - 1:
            trial += 1
            want = TARGET_G - cup_total
            elapsed = time.ticks_diff(time.ticks_ms(), session_t0) / 1000.0
            doser.timeout_s = DOSE_TIMEOUT_S
            if trial > FIRST_TRIAL:
                if want < TOPUP_MIN_G:
                    stop_reason = "{:.4f} g in the cup: nothing to top up".format(
                        cup_total)
                    break
                if elapsed > SESSION_BUDGET_S:
                    stop_reason = "session time budget ({:.0f} min)".format(
                        SESSION_BUDGET_S / 60.0)
                    break
                doser.timeout_s = int(min(DOSE_TIMEOUT_S,
                                          max(60, SESSION_HARD_S - elapsed)))
                C.trial = trial
                ev("top-up dose: {:.4f} g in the cup, {:.4f} g to go, "
                   "timeout {} s".format(cup_total, want, doser.timeout_s))
            gc.collect()
            C.trial = trial
            C.taps = 0
            C.base = None
            C.stage = "pre"
            doser.halts = []
            print("TRIAL_START,{},{},cup_before_g={:.4f}".format(
                trial, t_ms(), cup_total))
            t_start = t_ms()
            stream(PREROLL_S)
            t_dose = t_ms()
            res = doser.dose(want)
            t_done = t_ms()
            C.stage = "post"
            dose_tilt = servo_w.angle
            stream(POSTROLL_S)
            final_abs = mean_reads()          # at the last stage's angle
            if abs(servo_w.angle) > 0.05:
                servo_w.move_to(0.0)
            stream(HOME_SETTLE_S)
            final0_abs = mean_reads()         # plate home, as the baseline
            t_end = t_ms()
            final_rel = final0_rel = None
            if final_abs is not None and C.base is not None:
                final_rel = final_abs - C.base
            if final0_abs is not None and C.base is not None:
                final0_rel = final0_abs - C.base
            ref0 = C.abs0 if TOPUP_OF_ABS0_G is None else TOPUP_OF_ABS0_G
            if final0_abs is not None:
                cup_total = final0_abs - ref0
            elif final_abs is not None:
                cup_total = final_abs - ref0
            rec = {
                "trial": trial, "status": res.status,
                "target_g": round(want, 4),
                "session_target_g": TARGET_G,
                "dose_reported_g": round(res.dispensed_g, 4),
                "final_g": None if final_rel is None else round(final_rel, 4),
                "error_mg": (None if final_rel is None
                             else round(1000.0 * (final_rel - want), 1)),
                "final_tilt_deg": round(dose_tilt, 1),
                "final_g_at_0deg": (None if final0_rel is None
                                    else round(final0_rel, 4)),
                "error_mg_at_0deg": (None if final0_rel is None
                                     else round(1000.0 * (final0_rel - want),
                                                1)),
                "cup_total_g_at_0deg": round(cup_total, 4),
                "baseline_abs_g": (None if C.base is None
                                   else round(C.base, 4)),
                "final_abs_g": (None if final_abs is None
                                else round(final_abs, 4)),
                "final_abs_g_at_0deg": (None if final0_abs is None
                                        else round(final0_abs, 4)),
                "dose_s": round(res.elapsed_s, 1),
                "t_start_ms": t_start, "t_dose_ms": t_dose,
                "t_done_ms": t_done, "t_end_ms": t_end,
                "phase_cycles": res.phase_cycles,
                "taps": res.taps, "auger_rev": round(res.auger_deg / 360.0, 3),
                "halts": doser.halts, "read_retries": doser.read_retries,
            }
            results.append(rec)
            print("T," + json.dumps(rec))
            if C.abort:
                stop_reason = C.abort
                break
            if res.status in ("ok", "overshoot"):
                stop_reason = "dose {}".format(res.status)
                break
            if res.status == "timeout":
                # the powder is feeding, only slowly: a top-up would just
                # run into the same wall again
                stop_reason = "dose timeout; no top-up after a timeout"
                break
            stop_reason = "dose {}; no top-up left".format(res.status)
    except HardCap as exc:
        stop_reason = "hard cap: {}".format(exc)
        ev("HARD CAP -- stopping: {}".format(exc))
    except KeyboardInterrupt:
        stop_reason = "interrupted (Ctrl-C)"
        ev("interrupted")
    except Exception as exc:
        stop_reason = "error: {!r}".format(exc)
        ev("ERROR {!r}".format(exc))
    finally:
        C.stage = "end"
        safe_state(servo_w, C.stepper, tap)
        cup = None
        if C.last_abs is not None and C.abs0 is not None:
            cup = round(C.last_abs - C.abs0, 4)
        print("SUMMARY," + json.dumps({
            "trials_run": len(results), "stop_reason": stop_reason,
            "cup_g": cup,
            "statuses": [r["status"] for r in results],
            "elapsed_s": round(time.ticks_diff(time.ticks_ms(),
                                               session_t0) / 1000.0, 1)}))
    return results


if m3._ON_HARDWARE:     # on the Pico: run.  Under CPython (sim): import only.
    main()
