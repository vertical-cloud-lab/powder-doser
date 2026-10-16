"""PID closed-loop dose with full telemetry streaming (PR #131 request).

Runs ON the Pico via ``mpremote run`` (RAM only -- nothing is saved to
the Pico's filesystem).  Uses main_three_phase's hardware driver classes
(Stepper velocity mode / Servo plate degrees / Tap / Scale) but NOT its
three-phase controller: the control law here is a single continuous PID
loop on auger speed with flow anticipation, plus a tilt gain-schedule
and a tap-based stall fallback.

Control law (each scale sample, ~5 Hz):
    e_raw  = target - m_filt
    e_pred = e_raw - T_ANT * flow      # anticipate in-flight powder
    u_rpm  = clamp(KP * e_pred + KI * I, 0, MAX_RPM)
Tilt: 25 plate deg while e_raw > 50 mg, ramped down to 15 deg for the
tail (measured 07-28: salt trims controllably at 15-18 deg).
Taps: only as stall recovery (lip empty), every burst logged.

Telemetry (CSV over USB stdout):
    D,<t_ms>,<mass_g>,<S|U|X>,<tilt_deg>,<rpm_cmd>,<taps_cum>,<phase>
    E,<t_ms>,<event text>
    M,<key>,<value>                    # metadata
Phases: preroll (10 s, includes pre-zeroing state), tare, dose,
postroll (10 s), home.
"""

import sys
import time
import main_three_phase as m3

# ---- targets & gains -------------------------------------------------
TARGET_G = 1.0000
TOL_G = 0.002          # +/- 2 mg finish window
KP = 150.0             # rpm per g of predicted error
KI = 8.0               # rpm per (g * s) of integrated raw error
I_MAX_RPM = 6.0        # integral contribution clamp
T_ANT_S = 1.1          # flow anticipation (in-flight lag), seconds
MAX_RPM = 45.0
BULK_TILT = 25.0       # plate deg while far from target
FINE_TILT = 15.0       # plate deg for the tail
FINE_ERR_G = 0.050     # switch tilt schedule below this error
TILT_RATE = 12.0       # plate deg/s ramp between schedule points
PRE_S = 10.0
POST_S = 10.0
DOSE_TIMEOUT_S = 240.0
NOFLOW_ABORT_S = 45.0  # abort if nothing lands for this long mid-dose
STALL_TAP_S = 10.0     # tap burst if no gain for this long
FLOW_WIN_S = 1.5       # flow-estimate window

_t0 = time.ticks_ms()


def t_ms():
    return time.ticks_diff(time.ticks_ms(), _t0)


def ev(msg):
    print("E,{},{}".format(t_ms(), msg))


def meta(k, v):
    print("M,{},{}".format(k, v))


class Telemetry:
    def __init__(self, scale):
        self.scale = scale
        self.tilt = 0.0
        self.rpm = 0.0
        self.taps = 0
        self.phase = "init"
        self.last_mass = None
        self.misses = 0

    def sample(self):
        """One Q-poll; logs a D row; returns (mass, fresh)."""
        r = self.scale.read()
        ts = t_ms()
        if r is None or r.grams is None:
            self.misses += 1
            print("D,{},nan,X,{:.1f},{:.2f},{},{}".format(
                ts, self.tilt, self.rpm, self.taps, self.phase))
            return None
        self.misses = 0
        self.last_mass = r.grams
        print("D,{},{:.4f},{},{:.1f},{:.2f},{},{}".format(
            ts, r.grams, "S" if r.stable else "U",
            self.tilt, self.rpm, self.taps, self.phase))
        return r.grams


def main():
    meta("controller", "pid-v2")
    meta("powder_id", "salt")
    meta("target_g", TARGET_G)
    meta("kp", KP)
    meta("ki", KI)
    meta("t_ant_s", T_ANT_S)
    meta("max_rpm", MAX_RPM)
    meta("tol_g", TOL_G)

    scale = m3.Scale()
    stepper = m3.Stepper()
    servo = m3.Servo()
    tap = m3.Tap()
    tel = Telemetry(scale)

    sign = 1 if m3.config.STEPPER_DIRECTION >= 0 else -1
    usteps_rev = stepper.steps_per_rev

    def set_rpm(rpm):
        rpm = max(0.0, min(MAX_RPM, rpm))
        if rpm <= 0.0:
            stepper.tic.set_target_velocity(0)
        else:
            v = sign * max(1, int(rpm / 60.0 * usteps_rev * 10000))
            stepper.tic.set_target_velocity(v)
        tel.rpm = rpm

    def tilt_step(target, dt):
        """Ramp tilt toward target at TILT_RATE, one telemetry tick."""
        d = target - tel.tilt
        if abs(d) < 1e-6:
            return
        step = TILT_RATE * dt
        if abs(d) <= step:
            tel.tilt = target
        else:
            tel.tilt += step if d > 0 else -step
        servo._write_angle(tel.tilt)
        servo.angle = tel.tilt

    status = "aborted"
    final_g = None
    try:
        # ---- pre-roll: 10 s incl. pre-zeroing state ------------------
        tel.phase = "preroll"
        ev("preroll start (pre-zeroing absolute mass)")
        end = time.ticks_add(time.ticks_ms(), int(PRE_S * 1000))
        while time.ticks_diff(end, time.ticks_ms()) > 0:
            tel.sample()
            time.sleep_ms(60)

        # ---- tare ----------------------------------------------------
        tel.phase = "tare"
        ev("tare (Z) sent")
        scale.zero()
        r = scale.read_stable(timeout_ms=8000)
        if r is None or not r.stable:
            ev("tare did not settle -- continuing anyway")
        else:
            ev("tare settled at {:.4f} g".format(r.grams))
        tel.sample()

        # ---- dose: PID loop -----------------------------------------
        tel.phase = "dose"
        ev("dose start: PID to {:.4f} g".format(TARGET_G))
        stepper.set_speed(MAX_RPM)   # Tic max-speed ceiling, set once
        stepper.enable(True)

        hist = []                    # (t_s, m_filt) for flow estimate
        m_filt = None
        integ = 0.0
        last_t = time.ticks_ms()
        last_gain_t = time.ticks_ms()
        last_gain_m = 0.0
        tap_rounds = 0
        dose_t0 = time.ticks_ms()
        settle_pending = False

        while True:
            el = time.ticks_diff(time.ticks_ms(), dose_t0) / 1000.0
            if el > DOSE_TIMEOUT_S:
                status = "timeout"
                ev("dose timeout after {:.0f} s".format(el))
                break
            m = tel.sample()
            now = time.ticks_ms()
            dt = time.ticks_diff(now, last_t) / 1000.0
            last_t = now
            stepper.keep_alive()
            if m is None:
                if tel.misses >= 8:
                    status = "scale-error"
                    ev("scale unresponsive -- aborting")
                    break
                time.sleep_ms(60)
                continue
            m_filt = m if m_filt is None else 0.6 * m_filt + 0.4 * m
            t_s = time.ticks_diff(now, dose_t0) / 1000.0
            hist.append((t_s, m_filt))
            while hist and t_s - hist[0][0] > FLOW_WIN_S:
                hist.pop(0)
            flow = 0.0
            if len(hist) >= 2 and t_s - hist[0][0] > 0.3:
                flow = (m_filt - hist[0][1]) / (t_s - hist[0][0])

            e_raw = TARGET_G - m_filt
            e_pred = e_raw - T_ANT_S * flow

            # gain tracking for stall / no-flow detection
            if m_filt - last_gain_m > 0.0005:
                last_gain_m = m_filt
                last_gain_t = now
            quiet_s = time.ticks_diff(now, last_gain_t) / 1000.0

            # finish check: close enough and flow died down
            if e_raw <= TOL_G and abs(flow) < 0.0004:
                set_rpm(0.0)
                settle_pending = True
                ev("target window reached at {:.4f} g; settling".format(
                    m_filt))
                break
            if m > TARGET_G + TOL_G:
                set_rpm(0.0)
                settle_pending = True
                ev("overshoot guard tripped at {:.4f} g".format(m))
                break

            # no-flow / stall handling
            if quiet_s > NOFLOW_ABORT_S and m_filt < 0.005:
                status = "no-flow"
                ev("no powder after {:.0f} s -- hopper empty?".format(
                    quiet_s))
                break
            if quiet_s > STALL_TAP_S and e_raw > TOL_G:
                set_rpm(0.0)
                ev("stall {:.0f} s; tap burst".format(quiet_s))
                tap.tap(2, on_ms=60, off_ms=150)
                tel.taps += 2
                tap_rounds += 1
                last_gain_t = now
                if tap_rounds >= 4 and m_filt < 0.02:
                    status = "no-flow"
                    ev("taps not helping and nothing landed -- abort")
                    break
                if tap_rounds >= 8:
                    status = "exhausted"
                    ev("8 stall rounds with no yield -- hopper exhausted")
                    break
                continue

            # PID
            u_p = KP * e_pred
            if 0.0 < u_p < MAX_RPM and e_pred > 0:
                integ += e_raw * dt
            i_rpm = max(0.0, min(I_MAX_RPM, KI * integ))
            u = u_p + i_rpm
            if e_pred <= 0:
                u = 0.0
            set_rpm(u)

            # tilt schedule
            tilt_step(BULK_TILT if e_raw > FINE_ERR_G else FINE_TILT, dt)

        set_rpm(0.0)
        stepper.stop()

        # settle + verdict
        if settle_pending:
            end = time.ticks_add(time.ticks_ms(), 2500)
            while time.ticks_diff(end, time.ticks_ms()) > 0:
                tel.sample()
                time.sleep_ms(60)
            r = scale.read_stable(timeout_ms=8000)
            if r is not None and r.grams is not None:
                final_g = r.grams
                err = final_g - TARGET_G
                if abs(err) <= TOL_G:
                    status = "ok"
                elif err > 0:
                    status = "overshoot"
                else:
                    # short: single gentle top-up round, then accept
                    ev("short by {:.4f} g after settle; top-up".format(
                        -err))
                    stepper.set_speed(3.0)
                    stepper.enable(True)
                    t_end = time.ticks_add(time.ticks_ms(), 60000)
                    while time.ticks_diff(t_end, time.ticks_ms()) > 0:
                        m = tel.sample()
                        stepper.keep_alive()
                        if m is not None and m >= TARGET_G - TOL_G * 0.5:
                            break
                        set_rpm(2.0)
                        time.sleep_ms(60)
                    set_rpm(0.0)
                    stepper.stop()
                    r = scale.read_stable(timeout_ms=8000)
                    if r is not None and r.grams is not None:
                        final_g = r.grams
                        status = ("ok" if abs(final_g - TARGET_G) <= TOL_G
                                  else ("overshoot"
                                        if final_g > TARGET_G else "short"))

        # ---- post-roll: 10 s ----------------------------------------
        tel.phase = "postroll"
        ev("postroll start")
        end = time.ticks_add(time.ticks_ms(), int(POST_S * 1000))
        while time.ticks_diff(end, time.ticks_ms()) > 0:
            tel.sample()
            time.sleep_ms(60)

        # ---- home the tilt, final weigh -----------------------------
        tel.phase = "home"
        while tel.tilt > 0.0:
            tel.sample()
            tilt_step(0.0, 0.25)
            time.sleep_ms(60)
        r = scale.read_stable(timeout_ms=10000)
        if r is not None and r.grams is not None:
            final_g = r.grams
        ev("final stable weigh: {} g".format(
            "{:.4f}".format(final_g) if final_g is not None else "?"))

    except KeyboardInterrupt:
        status = "interrupted"
        ev("KeyboardInterrupt -- stopping")
    finally:
        try:
            stepper.tic.set_target_velocity(0)
            stepper.stop()
        except Exception:
            pass
        try:
            tap._off()
        except Exception:
            pass
        try:
            servo._write_angle(0.0)
        except Exception:
            pass
    print("SUMMARY,status={},final_g={},target_g={:.4f},taps={}".format(
        status, "{:.4f}".format(final_g) if final_g is not None else "nan",
        TARGET_G, tel.taps))


main()
