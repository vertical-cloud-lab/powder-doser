"""Phase-resolved afterflow characterization -- PR #131 request (2026-08-13).

Runs ON the Pico via ``mpremote run`` (RAM only -- nothing is written to
the Pico filesystem).  Re-uses ``main_three_phase``'s hardware driver
classes (Stepper / Servo / Scale); no dose-controller logic.

Why this exists
---------------
The earlier afterflow battery halted the auger the instant the scale
first read a fixed target mass, and inferred afterflow ~= flow x tau.
The open question (williamulbz): *is each powder "slug" tied to an exact
full rotation of the auger, and does the afterflow depend on WHERE in the
auger rotation we stop?*  This script answers both by tracking the
commanded stepper position -- i.e. the true auger angle -- rather than
stopping on a mass threshold.

Gear ratio -- the whole point
-----------------------------
``main_three_phase`` folds the physical 44:20 motor->auger reduction into
``Stepper.steps_per_rev``:

    steps_per_rev = FULL_STEPS_REV(200) x MICROSTEPS(8) x GEAR(44/20)
                  = 3520 microsteps per AUGER revolution

so every degree/RPM at this API is TRUE auger motion, and the auger phase
of any commanded position is::

    auger_rev = _position / steps_per_rev
    phase_deg = (_position mod steps_per_rev) / steps_per_rev * 360

Position mode (``set_target_position``) advances the shadow ``_position``
by an exact microstep delta and the Tic lands exactly on it, so the halt
phase is known to the microstep (<0.11 deg auger).  Velocity mode does NOT
update the shadow and the Tic position TX is unwired, so it cannot be used
for phase-resolved work -- everything here is position mode.

Measurement design (v2 -- robust to the A&D balance quirks)
-----------------------------------------------------------
* Tare the balance ONCE at the start.  Per-trial ``Z`` is silently
  rejected by the HR-A while it is still settling from the previous dose,
  which made masses accumulate; instead we keep a continuous absolute
  reading and take DIFFERENCES (yield, afterflow), so the standing offset
  cancels.  The cup is never emptied mid-session; the running absolute
  mass is the cup cap guard.
* The balance updates its datum at only ~5-10 Hz, so ``read()`` returns
  None when polled faster.  Streaming polls at POLL_MS(120 ms ~ 8 Hz) and
  a ``settled()`` helper polls read() and returns a stable ST datum if one
  arrives, else the last valid (unstable) datum -- never a bare None while
  frames exist.
* The auger is DE-ENERGISED before every settle/weigh so the stepper
  driver cannot inject noise into the scale UART (this was the cause of
  the null frames during fast-move settles in v1).  De-energising does not
  disturb the shadow ``_position``, so the session-wide phase reference is
  preserved (this is exactly how ``rotate_degrees`` idles between moves).

Tests
-----
  A  Slug periodicity.  From the single tare, advance the auger in fixed
     INCR_DEG steps across N_SCAN_REVS revolutions x N_SCANS scans, weighing
     (settled) after every step.  Per-step yield vs exact auger angle,
     binned by phase over all revolutions -> is delivery periodic at 360
     deg of auger?  (Also the empirical check on the folded 2.2 gear ratio.)

  B  Afterflow vs halt phase.  Cruise CRUISE_REVS revolutions at feed RPM,
     decelerate to a hard stop at a COMMANDED auger phase phi (0..315 deg),
     de-energise, then weigh the settling tail.  afterflow = settled -
     m_halt.  phi swept, interleaved across reps and two tilts.

Telemetry (CSV over USB stdout)
-------------------------------
    M,<key>,<value>
    E,<t_ms>,<text>
    D,<t_ms>,<trial>,<phase>,<mass>,<S|U|X>,<rpm>,<auger_rev>,<phase_deg>
    P,<t_ms>,<trial>,<kind>,<mass>,<stab>,<auger_rev>,<phase_deg>
    A,<trial>,<scan>,<incr>,<tilt>,<rpm>,<incr_deg>,<cum_deg>,<phase_deg>,
      <auger_rev>,<m_before>,<m_after>,<yield>
    B,<trial>,<tilt>,<rep>,<rpm>,<cruise_revs>,<phase_cmd_deg>,
      <auger_rev_total>,<m_base>,<m_halt>,<t_move_s>,<m_settled>,
      <afterflow>,<dispensed>,<abs_mass>,<verdict>
``D.phase``: noise, preroll, scanmove, move, settle.
"""

import time
import main_three_phase as m3

POWDER_ID = "salt"

# ---- safety budget (absolute cup mass, g -- tared once at start) ----
# Operator reset the system; cup EMPTY at start.  Keep absolute cup mass
# well under both the ~50 g cup and the balance ~102 g range.
CAP_G = 40.0        # stop before a trial if absolute mass exceeds this
HARD_G = 45.0       # emergency mid-move halt on absolute mass

# ---- timing ----
NOISE_S = 15.0
PREROLL_S = 1.0
SETTLE_STREAM_S = 7.0
SETTLED_MAX_S = 3.0    # robust settled() poll budget
POLL_MS = 120          # ~8 Hz, matched to the balance datum rate

# ---- Test A: slug periodicity ----
TILT_A = 55.0
RPM_A = 30.0
INCR_DEG = 45.0
N_SCAN_REVS = 4
N_SCANS = 2

# ---- Test B: afterflow vs halt phase ----
RPM_B = 90.0
CRUISE_REVS = 4
PHASES = [0.0, 45.0, 90.0, 135.0, 180.0, 225.0, 270.0, 315.0]
TILTS_B = [55.0, 70.0]
REPS_B = {55.0: 3, 70.0: 2}

_t0 = time.ticks_ms()


def t_ms():
    return time.ticks_diff(time.ticks_ms(), _t0)


def ev(msg):
    print("E,{},{}".format(t_ms(), msg))


def meta(k, v):
    print("M,{},{}".format(k, v))


class Rig:
    def __init__(self):
        self.scale = m3.Scale()
        self.stepper = m3.Stepper()
        self.servo = m3.Servo()
        self.spr = int(round(self.stepper.steps_per_rev))   # 3520
        self.trial = 0
        self.rpm = 0.0
        self.absmass = 0.0     # last known absolute cup mass (post single tare)
        self.aborted = False

    # -- phase helpers -------------------------------------------------
    def auger_rev(self):
        return self.stepper._position / self.spr

    def phase_deg(self):
        return (self.stepper._position % self.spr) / self.spr * 360.0

    def _delta_to_phase(self, revs, phase_deg):
        cur = self.stepper._position % self.spr
        want = int(round(phase_deg / 360.0 * self.spr)) % self.spr
        extra = (want - cur) % self.spr
        return revs * self.spr + extra

    # -- measurement ---------------------------------------------------
    def sample(self, phase):
        r = self.scale.read()
        ts = t_ms()
        arev = self.auger_rev()
        aph = self.phase_deg()
        if r is None or r.grams is None:
            print("D,{},{},{},nan,X,{:.0f},{:.4f},{:.2f}".format(
                ts, self.trial, phase, self.rpm, arev, aph))
            return None
        print("D,{},{},{},{:.4f},{},{:.0f},{:.4f},{:.2f}".format(
            ts, self.trial, phase, r.grams, "S" if r.stable else "U",
            self.rpm, arev, aph))
        return r.grams

    def stream(self, seconds, phase):
        end = time.ticks_add(time.ticks_ms(), int(seconds * 1000))
        last = None
        while time.ticks_diff(end, time.ticks_ms()) > 0:
            m = self.sample(phase)
            if m is not None:
                last = m
                self.absmass = m
            time.sleep_ms(POLL_MS)
        return last

    def settled(self, kind, max_s=SETTLED_MAX_S):
        """Poll read() up to max_s; return (grams, stable_bool).  Returns a
        stable ST datum if one arrives, else the last valid (unstable)
        datum; only (None, False) if no frame at all was seen."""
        end = time.ticks_add(time.ticks_ms(), int(max_s * 1000))
        last = None
        laststab = False
        while time.ticks_diff(end, time.ticks_ms()) > 0:
            r = self.scale.read()
            if r is not None and r.grams is not None:
                last = r.grams
                laststab = r.stable
                if r.stable:
                    break
            time.sleep_ms(80)
        if last is not None:
            self.absmass = last
        print("P,{},{},{},{},{},{:.4f},{:.2f}".format(
            t_ms(), self.trial, kind,
            "nan" if last is None else "{:.4f}".format(last),
            "S" if laststab else "U", self.auger_rev(), self.phase_deg()))
        return last, laststab

    # -- position-mode move, streaming the balance throughout ----------
    def move_usteps(self, delta_u, rpm, phase_label):
        self.stepper.set_speed(rpm)
        if not self.stepper._enabled:
            self.stepper.enable(True)
        self.rpm = rpm
        self.stepper._position += delta_u
        target = self.stepper._position
        self.stepper.tic.set_target_position(target)

        a = m3.config.STEPPER_ACCEL_REV_PER_S2 * self.spr
        vmax = abs(rpm) / 60.0 * self.spr
        dd = abs(delta_u)
        if a <= 0 or vmax <= 0:
            t_move = 0.5
        else:
            d_acc = vmax * vmax / (2.0 * a)
            if 2.0 * d_acc <= dd:
                t_move = 2.0 * (vmax / a) + (dd - 2.0 * d_acc) / vmax
            else:
                t_move = 2.0 * (dd / a) ** 0.5
        t_move += 0.20

        t_start = time.ticks_ms()
        m_last = None
        while time.ticks_diff(time.ticks_ms(), t_start) / 1000.0 < t_move:
            m = self.sample(phase_label)
            if m is not None:
                m_last = m
                self.absmass = m
                if m >= HARD_G:
                    self.stepper.enable(False)
                    ev("HARD CAP mid-move: abs {:.2f} >= {:.1f}".format(
                        m, HARD_G))
                    self.aborted = True
                    break
            self.stepper.keep_alive()
            time.sleep_ms(POLL_MS)
        self.rpm = 0.0
        return m_last, t_move

    # -- Test A: slug periodicity -------------------------------------
    def slug_scan(self, scan, tilt, rpm, incr_deg, n_incr):
        self.trial += 1
        ev("=== A scan {} trial {} : tilt {:.0f} rpm {:.0f} incr {:.0f} "
           "x {} ===".format(scan, self.trial, tilt, rpm, incr_deg, n_incr))
        self.servo.move_to(tilt)
        time.sleep_ms(1000)
        m_prev, _ = self.settled("scan0")
        if m_prev is None:
            m_prev = self.absmass
        incr_u = int(round(incr_deg / 360.0 * self.spr))
        for i in range(n_incr):
            self.move_usteps(incr_u, rpm, "scanmove")
            self.stepper.enable(False)      # quiet the driver before weighing
            m_now, _ = self.settled("scan{}".format(i + 1))
            if m_now is None:
                m_now = m_prev
            yld = m_now - m_prev
            print("A,{},{},{},{:.0f},{:.0f},{:.0f},{:.1f},{:.2f},{:.4f},"
                  "{:.4f},{:.4f},{:.4f}".format(
                      self.trial, scan, i + 1, tilt, rpm, incr_deg,
                      (i + 1) * incr_deg, self.phase_deg(), self.auger_rev(),
                      m_prev, m_now, yld))
            m_prev = m_now
            if self.absmass >= CAP_G:
                ev("CAP during scan: abs {:.2f} g".format(self.absmass))
                self.aborted = True
                break

    # -- Test B: afterflow vs halt phase ------------------------------
    def afterflow_trial(self, tilt, rep, rpm, cruise_revs, phase_cmd):
        if self.absmass > CAP_G:
            ev("BUDGET: abs {:.2f} > cap {:.1f} -- stop".format(
                self.absmass, CAP_G))
            self.aborted = True
            return
        self.trial += 1
        ev("=== B trial {} : tilt {:.0f} rep {} rpm {:.0f} cruise {} rev "
           "-> phase {:.0f} deg (abs {:.2f}) ===".format(
               self.trial, tilt, rep, rpm, cruise_revs, phase_cmd,
               self.absmass))
        self.servo.move_to(tilt)
        time.sleep_ms(1000)
        m_base, _ = self.settled("base")
        if m_base is None:
            m_base = self.absmass
        self.stream(PREROLL_S, "preroll")

        delta_u = self._delta_to_phase(cruise_revs, phase_cmd)
        m_halt, t_move = self.move_usteps(delta_u, rpm, "move")
        self.stepper.enable(False)          # de-energise: quiet + hold phase
        if m_halt is None:
            m_halt = self.absmass
        self.stream(SETTLE_STREAM_S, "settle")
        m_set, _ = self.settled("settled")
        if m_set is None:
            m_set = self.absmass

        after = m_set - m_halt
        disp = m_set - m_base
        verdict = "capstop" if self.aborted else "ok"
        print("B,{},{:.0f},{},{:.0f},{},{:.1f},{:.4f},{:.4f},{:.4f},{:.2f},"
              "{:.4f},{:.4f},{:.4f},{:.4f},{}".format(
                  self.trial, tilt, rep, rpm, cruise_revs, phase_cmd,
                  self.auger_rev(), m_base, m_halt, t_move, m_set,
                  after, disp, self.absmass, verdict))


def build_plan_B():
    plan = []
    for tilt in TILTS_B:
        reps = REPS_B.get(tilt, 2)
        for rep in range(1, reps + 1):
            k = (rep - 1) % len(PHASES)
            order = PHASES[k:] + PHASES[:k]
            if rep % 2 == 0:
                order = list(reversed(order))
            for ph in order:
                plan.append((tilt, rep, ph))
    return plan


def main():
    meta("experiment", "afterflow-phase-A-slug-B-halt-phase")
    meta("powder_id", POWDER_ID)
    meta("gear_ratio_stepper_per_auger", "44/20=2.2")
    meta("steps_per_auger_rev", 3520)
    meta("full_steps_rev", m3.config.STEPPER_FULL_STEPS_REV)
    meta("microsteps", m3.config.STEPPER_MICROSTEPS)
    meta("stepper_direction", m3.config.STEPPER_DIRECTION)
    meta("accel_rev_per_s2", m3.config.STEPPER_ACCEL_REV_PER_S2)
    meta("cap_g", CAP_G)
    meta("hard_g", HARD_G)
    meta("tare_mode", "no-hardware-tare-absolute-differences")
    meta("auger_tare_g", 56.716)
    meta("total_loaded_g", 127.98)
    meta("salt_onboard_est_g", 71.26)
    meta("tilt_A", TILT_A)
    meta("rpm_A", RPM_A)
    meta("incr_deg_A", INCR_DEG)
    meta("scan_revs_A", N_SCAN_REVS)
    meta("n_scans_A", N_SCANS)
    meta("rpm_B", RPM_B)
    meta("cruise_revs_B", CRUISE_REVS)
    meta("phases_B", "|".join("{:.0f}".format(p) for p in PHASES))
    meta("tilts_B", "|".join("{:.0f}".format(t) for t in TILTS_B))

    rig = Rig()
    plan_b = build_plan_B()
    meta("planned_B_trials", len(plan_b))
    try:
        # NO hardware tare: the A&D `Z` command halts Q-responses when the
        # pan is loaded (the cup cannot be emptied remotely mid-session), so
        # we track ABSOLUTE mass and take differences.  Establish the
        # baseline and a static noise stream instead.
        rig.servo.move_to(0.0)
        time.sleep_ms(1000)
        ev("baseline (no tare) + {:.0f} s static noise stream".format(NOISE_S))
        rig.settled("baseline0", max_s=4.0)
        rig.stream(NOISE_S, "noise")
        rig.settled("noise_end", max_s=4.0)
        ev("noise baseline done")

        # ---- Test A: slug periodicity ----
        n_incr = int(N_SCAN_REVS * 360 / INCR_DEG)
        for scan in range(1, N_SCANS + 1):
            rig.slug_scan(scan, TILT_A, RPM_A, INCR_DEG, n_incr)
            if rig.aborted:
                break

        if not rig.aborted:
            # ---- Test B: afterflow vs halt phase ----
            for (tilt, rep, ph) in plan_b:
                rig.afterflow_trial(tilt, rep, RPM_B, CRUISE_REVS, ph)
                if rig.aborted:
                    ev("battery stopped early (budget/cap)")
                    break
        ev("battery complete")
    except KeyboardInterrupt:
        ev("KeyboardInterrupt -- stopping")
    finally:
        try:
            rig.stepper.tic.set_target_velocity(0)
        except Exception:
            pass
        try:
            rig.stepper.stop()
        except Exception:
            pass
        try:
            rig.servo.move_to(0.0)
        except Exception:
            pass
    print("SUMMARY,trials={},abs_g={:.3f}".format(rig.trial, rig.absmass))


main()
