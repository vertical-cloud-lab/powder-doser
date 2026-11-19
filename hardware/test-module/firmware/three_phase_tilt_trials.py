"""30 x 1 g salt trials: three-phase dose with a stepped bulk tilt (PR #131).

Requested by XZaitzeff on 2026-11-18 (PR #131): 30 trials of 1 g of salt.
Bulk stage at 55 auger rpm with the plate stepping through five angles,
fine stage at 30 deg and 25 rpm, then the usual tap stage, with the
balance logged as often as it answers.  The two readings XZaitzeff picked
("1a, 2a"):

* 1a -- ONE tilt schedule inside every trial: the bulk starts at the first
  angle and steps down one angle at a time as the cup fills, in equal mass
  bands across the bulk span (0 .. target - t1 = 0.75 g, so 0.15 g each).
* 2a -- the fine stage turns the auger STEADILY at 25 rpm (velocity mode)
  until the fine -> tap hand-off, instead of the default 180 deg steps.

Bulk angles by version:

* 2026-11-18a/b: 60 -> 55 -> 50 -> 45 -> 40 deg.  With the tube filled to
  the brim the full column plugs at these angles; both launches stopped
  after two stalled trials in a row.
* 2026-11-18c: 50 -> 45 -> 40 -> 35 -> 30 deg (XZaitzeff, 2026-11-18
  15:56 UTC: "do 50, 45, 40, 35, and 30 during the bulk stage.  Keep all
  the other settings the same.  Run the 30 trials").  Nothing else changed
  from 2026-11-18b.
* 2026-11-19a: back to 60 -> 55 -> 50 -> 45 -> 40 deg on a NEW auger tube
  (XZaitzeff, 2026-11-19 19:31 UTC: "we replaced the auger with a new
  one.  So run the 30 experiments with the 60, 55, 50, 45, and 40 degree
  bulk regime from the first attempt and the same for everything else").
  Functionally identical to 2026-11-18b (the first attempt's launch 2,
  with the no-flow step); only the version string differs.
* 2026-11-19b: the same 60 -> 40 deg bulk on the new tube, now WITH taps
  during the bulk (XZaitzeff, 2026-11-19 20:32 UTC: "Add taps into the
  bulk session to shake up the salt like what was done in the summer.
  Still try to do different angles.  Run the 30 experiments").  The
  summer tap-while-rotating runs (2026-08-07 stop response, 2026-08-12/13
  C6/C8) fired one 60 ms solenoid pulse every third poll loop while the
  auger spun at 55 rpm: 3.2-3.5 taps/s measured, one every ~300 ms.  Here
  the controller's own cadence taps do the same (taps_per_cycle > 0 in
  velocity mode, the issue #164 code): one BULK_TAP_ON_MS pulse per
  BULK_TAP_PERIOD_MS while the bulk auger spins, and only in the bulk.
  Nothing else changed from 2026-11-19a.
* 2026-11-19c: launch 1 of 19b (20:41 UTC) showed the bulk taps work --
  both trials reached the bulk exit (0.755 and 0.759 g) where the
  tap-free November bulk never got past 0.57 g -- but the tap-free fine
  stage then stalled (30 deg, 25 rpm: +0.4 and +5.4 mg before the 7.5 s
  stall rule), and two such trials ended the launch.  Two changes:
  (1) the fine stage gets the same cadence taps as the bulk (one 60 ms
  pulse per 300 ms while the auger spins; still 30 deg, 25 rpm);
  (2) the two-failed-in-a-row stop now only counts a failed trial
  (stalled / timeout / scale error / cycle budget) that delivered less
  than LOW_DELIVERY_G -- its job is to catch an empty or blocked tube,
  and a trial that got most of the way there shows the tube is feeding.
  The session budget is set so the last trial ends inside the Actions
  job's time limit.  Bulk, tap stage, thresholds and stall rules are
  unchanged.
* 2026-11-19d: the OLD auger tube is back on (the one used on 11-18), and
  the bulk auger runs at 80 rpm instead of 55 (XZaitzeff, 2026-11-19
  21:36 UTC: "I put the auger from before back on the doser.  Do the 30
  experiments with the tapping during the bulk session.  Increase the
  rotate speed of the bulk session to 80 rpm").  Everything else is
  2026-11-19c: the same bulk taps (one 60 ms pulse per 300 ms, so fewer
  taps per auger revolution than at 55 rpm), the same 60 -> 40 deg
  stepped bulk, the fine stage at 30 deg and 25 rpm with the same taps,
  the stock tap stage, thresholds and stall rules, and the 19c
  failed-in-a-row rule.

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
3. the bulk tilt schedule (1a): when a bulk poll crosses a band edge
   the plate steps to the next angle while the auger keeps spinning.
   Fallback added after the first launch (2026-11-18 06:45 UTC): with
   the tube freshly filled to the brim, 60 deg holds the tube vertical
   and the full column plugs -- trials 1 and 2 got 0 mg in 18 auger revs
   there and stalled, and after priming a 60 deg probe gave one 112 mg
   slug then nothing.  So if an angle shows no flow (< SCHED_FLOW_G) for
   SCHED_DWELL_S while spinning, the plate also steps on to the next
   angle; every step is logged with its reason (band or no-flow);
4. the dose timeout, the thresholds and every stall rule stay stock.

Parameters that differ from the stock phase dicts (all per the request):

    bulk  angle 60 -> 40 deg stepped (50 -> 30 in c), 55 rpm (80 rpm
          from 2026-11-19d), continuous; no taps up to 2026-11-19a, from 2026-11-19b one
          60 ms tap per 300 ms while the auger spins (summer cadence)
    fine  angle 30 deg, 25 rpm, continuous (2a), no taps up to
          2026-11-19b, from 2026-11-19c the bulk's cadence taps, anticipation
          FINE_ANTICIPATION_G = 20 mg (the 25 rpm afterflow, ~10-45 mg, so it
          lands at the hand-off rather than past 1 g)
    tap   stock (0 deg, 1 tap + 15 deg per cycle, 1.5 s settle, 5 deg
          nudge after 3 dry cycles, up to 10), except its 15 deg turns
          run at 25 rpm in every trial (stock leaves the speed at
          whatever the previous stage set)
    poll  continuous stages poll every POLL_MS (stock 250 ms), which is
          what "as frequently as possible" needs

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

SCRIPT_VERSION = "2026-11-19d"
POWDER_ID = "salt"

N_TRIALS = 30
TARGET_G = 1.0

# --- the request (XZaitzeff, PR #131, 2026-11-18 "1a, 2a, yes"; 2026-11-19 a-d)
BULK_RPM = 80.0               # 2026-11-19d (55 up to 2026-11-19c)
BULK_TILTS = (60.0, 55.0, 50.0, 45.0, 40.0)   # plate deg, stepped as it fills
SCHED_FLOW_G = 0.002           # a bulk angle "flows" once it gains this ...
SCHED_DWELL_S = 3.0            # ... and is left after this long without it
# 2026-11-19b: taps during the bulk, at the summer tap-while-rotating
# cadence (08-07 and 08-12/13: one 60 ms pulse per ~300 ms at 55 rpm)
BULK_TAP_ON_MS = 60
BULK_TAP_PERIOD_MS = 300       # pulse start to pulse start
FINE_TAPS = True               # 2026-11-19c: same cadence in the fine stage
FINE_TILT = 30.0
FINE_RPM = 25.0
FINE_ANTICIPATION_G = 0.020
TAP_STAGE_RPM = FINE_RPM       # speed of the tap stage's 15 deg turns

POLL_MS = 80                   # continuous-stage poll sleep (stock 250)
FILL_PERIOD_MS = 95            # extra reads while waiting: ~10 Hz
FILL_MIN_REM_MS = 40           # only start a fill read with this much left
FILL_TIMEOUT_MS = 150          # and give up on it quickly

PREROLL_S = 5.0                # logged before each trial's baseline
POSTROLL_S = 8.0               # logged after the controller finishes

# --- safety ----------------------------------------------------------------
CUP_CAP_G = 45.0               # total into the cup this session
CUP_NEXT_MARGIN_G = 1.6        # don't start a trial that could pass the cap
CUP_HARD_G = 46.5              # any frame above this mid-trial -> abort
BAL_MAX_G = 95.0               # displayed ceiling (balance range 102 g)
MAX_FAILED_IN_A_ROW = 2        # stalled / scale-error / timeout ... in a row
LOW_DELIVERY_G = 0.5           # 19c: ... counted only if it delivered < this
SESSION_BUDGET_S = 110 * 60    # don't start a trial after this (19c: 110,
                               # so the last trial ends inside the job limit)


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
    p3.update({"rotation_rpm": TAP_STAGE_RPM})
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
    meta("script", "three_phase_tilt_trials.py " + SCRIPT_VERSION)
    meta("powder_id", POWDER_ID)
    meta("main_three_phase_sha16", file_sha("main_three_phase.py"))
    meta("config_sha16", file_sha("config.py"))
    meta("scale_sha16", file_sha("scale.py"))
    meta("balance_filter_sha16", file_sha("balance_filter.py"))
    meta("n_trials", N_TRIALS)
    meta("target_g", TARGET_G)
    meta("bulk", "rpm {} tilts {} continuous cadence-taps {} ms per {} ms "
         "anticipation 0".format(
             BULK_RPM, "/".join("{:.0f}".format(a) for a in BULK_TILTS),
             BULK_TAP_ON_MS, BULK_TAP_PERIOD_MS))
    meta("fine", "tilt {} rpm {} continuous {} anticipation {}".format(
        FINE_TILT, FINE_RPM,
        ("cadence-taps {} ms per {} ms".format(BULK_TAP_ON_MS,
                                               BULK_TAP_PERIOD_MS)
         if FINE_TAPS else "no-taps"),
        FINE_ANTICIPATION_G))
    meta("tap", "stock PHASE3_TAP, turns at {} rpm".format(TAP_STAGE_RPM))
    meta("thresholds", "/".join("{}".format(v) for v in m3.THRESHOLDS))
    meta("dose_timeout_s", m3.DOSE_TIMEOUT_S)
    meta("poll_ms", POLL_MS)
    meta("fill_period_ms", FILL_PERIOD_MS)
    meta("preroll_s", PREROLL_S)
    meta("postroll_s", POSTROLL_S)
    meta("cup_cap_g", CUP_CAP_G)
    meta("session_budget_s", SESSION_BUDGET_S)
    meta("failed_in_a_row", "{} trials that end failed with < {} g".format(
        MAX_FAILED_IN_A_ROW, LOW_DELIVERY_G))
    meta("tare", "none (baseline bracket per trial)")

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
    thresholds = list(m3.THRESHOLDS)
    C.sched_band_g = (TARGET_G - thresholds[0]) / len(BULK_TILTS)
    meta("bulk_band_g", "{:.4f}".format(C.sched_band_g))
    meta("bulk_no_flow_step", "{} g within {} s".format(SCHED_FLOW_G,
                                                         SCHED_DWELL_S))
    for i, p in enumerate(phases):
        meta("phase{}".format(i + 1), json.dumps(p))
    doser = Doser(C.stepper, tap_w, servo_w, C.scale, config,
                  phases=phases, thresholds=thresholds, log=clog,
                  sleep_ms=lsleep)

    results = []
    failed_in_row = 0
    stop_reason = "all trials done"
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
        for trial in range(1, N_TRIALS + 1):
            elapsed = time.ticks_diff(time.ticks_ms(), session_t0) / 1000.0
            if elapsed > SESSION_BUDGET_S:
                stop_reason = "session time budget ({:.0f} min)".format(
                    SESSION_BUDGET_S / 60.0)
                break
            cup = (C.last_abs - C.abs0) if C.last_abs is not None else 0.0
            if cup > CUP_CAP_G - CUP_NEXT_MARGIN_G:
                stop_reason = "cup cap: {:.3f} g in the cup".format(cup)
                break
            if failed_in_row >= MAX_FAILED_IN_A_ROW:
                stop_reason = "{} failed trials in a row".format(
                    failed_in_row)
                break
            gc.collect()
            C.trial = trial
            C.taps = 0
            C.base = None
            C.stage = "pre"
            doser.halts = []
            print("TRIAL_START,{},{},cup_before_g={:.4f}".format(
                trial, t_ms(), cup))
            t_start = t_ms()
            stream(PREROLL_S)
            t_dose = t_ms()
            res = doser.dose(TARGET_G)
            t_done = t_ms()
            C.stage = "post"
            stream(POSTROLL_S)
            final_abs = mean_reads()
            t_end = t_ms()
            final_rel = None
            if final_abs is not None and C.base is not None:
                final_rel = final_abs - C.base
            if abs(servo_w.angle) > 0.05:
                servo_w.move_to(0.0)
            rec = {
                "trial": trial, "status": res.status,
                "target_g": TARGET_G,
                "dose_reported_g": round(res.dispensed_g, 4),
                "final_g": None if final_rel is None else round(final_rel, 4),
                "error_mg": (None if final_rel is None
                             else round(1000.0 * (final_rel - TARGET_G), 1)),
                "baseline_abs_g": (None if C.base is None
                                   else round(C.base, 4)),
                "final_abs_g": (None if final_abs is None
                                else round(final_abs, 4)),
                "dose_s": round(res.elapsed_s, 1),
                "t_start_ms": t_start, "t_dose_ms": t_dose,
                "t_done_ms": t_done, "t_end_ms": t_end,
                "phase_cycles": res.phase_cycles,
                "taps": res.taps, "auger_rev": round(res.auger_deg / 360.0, 3),
                "halts": doser.halts, "read_retries": doser.read_retries,
            }
            results.append(rec)
            print("T," + json.dumps(rec))
            if (res.status in ("ok", "overshoot")
                    or res.dispensed_g >= LOW_DELIVERY_G):
                failed_in_row = 0
            else:
                failed_in_row += 1
            if C.abort:
                stop_reason = C.abort
                break
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
