"""Candidate trim-dispensing methods (issue #153).

A ladder of six methods, ordered so each one isolates a single design decision.
All of them start from the same handover state -- the bang-bang bulk phase has
halted with ``start_deficit_g`` still to go -- and all of them are scored on the
same one-sided metrics.

===================  ======================================================
method               the question it answers
===================  ======================================================
``margin_only``      What does bang-bang alone give?  No trim at all: this is
                     the "guard band and hope" control.
``rate_pi``          The deployed trickle (PR #124 ``bangbang.trickle_tap``):
                     PI on estimated rate, predictive cutoff, tap finish.
``rate_pid``         The same with a derivative term, which is what issue #153
                     asks about directly.
``fixed_increment``  Increment-and-measure with a fixed 45 deg step -- the
                     step size the bench actually characterised, which the
                     Edison review says is "much too coarse for a 5 mg
                     endpoint".  Included to show that discrete dosing is not
                     automatically safe; the *step size* is the whole game.
``chance_increment`` The proposal.  Each command is the largest one whose
                     UPPER QUANTILE delivery still fits the remaining one-sided
                     budget, measured at rest between commands.
``chance_tap``       ``chance_increment`` plus a chance-constrained tap, used
                     only for stall recovery and only when the tap's own upper
                     quantile fits the budget.
===================  ======================================================

The one structural point worth stating up front: ``chance_increment`` needs no
handover constant.  Early on, when the remaining budget is large, the quantile
rule returns a big command and the method runs the auger continuously for most
of a revolution -- the continuum regime.  As the budget shrinks the same rule
returns smaller and smaller commands until it is nudging.  The coarse-to-fine
handover the Edison review asks for ("handover when the upper quantile of mass
delivered over the stop horizon exceeds the remaining one-sided error budget")
falls out of the rule rather than being tuned into it.
"""
from __future__ import annotations

import numpy as np

from estimators import MassRateLagKF, TapYieldModel, YieldModel
from trim_sim import TOL_G, TrimRig

__all__ = ["METHODS", "run_method"]

# Deployed-controller constants, from optimization/benchmarks/bangbang.py.
CUTOFF_MARGIN_G = 0.035      # the fixed 35 mg margin
TAU_PRIOR_S = 0.30           # rate lookahead
TRICKLE_RPM_CAP = 45.0
FF_PRIOR = 0.35

# Hard safety interlock: never actuate when the settled reading is already
# within EPS_HARD of target.  This is deliberately outside every control law --
# the Edison MPC follow-up asks for a "formal no-overshoot guarantee independent
# of the PI/cutoff logic".
EPS_HARD_G = 1e-3

# Metered mass that can go in with nothing coming out before the auger is
# declared blocked rather than merely recharging the lip.  Sized above a
# plausible lip capacity (~55-90 mg across the bench powders).
STALL_METERED_G = 0.15


# ---------------------------------------------------------------------------
# 1. No trim at all
# ---------------------------------------------------------------------------

def margin_only(rig: TrimRig, target_g: float, **_) -> str:
    """Bang-bang guard band only: stop, settle, declare done.

    The bulk phase already halted below target, so this method's error is
    exactly the guard band minus the afterflow.  It is the control condition:
    everything a trim method achieves has to be measured against it.
    """
    rig.settled_read()
    return "ok"


# ---------------------------------------------------------------------------
# 2/3. Rate-feedback trims (the PI / PID family)
# ---------------------------------------------------------------------------

def _rate_trim(rig: TrimRig, target_g: float, kd: float = 0.0,
               dt: float = 0.2, kp: float = 250.0, ki: float = 120.0,
               k_sigma: float = 1.0, max_rate: float = 0.05,
               do_tap_finish: bool = True, **_) -> str:
    """Shared body for ``rate_pi`` and ``rate_pid``.

    This is ``bangbang.trickle_tap`` reimplemented against the trim rig, with
    the dead ff-adaptive margin term removed (the Edison review confirmed it
    fires in 0 of 360 doses) and an optional derivative term on the rate error.

    The rate estimate feeds two channels that the review asked to be kept
    separate, so they are named separately here even though both currently take
    the same signal: ``r`` drives the PI/PID feedback, ``r_stop`` drives the
    cutoff.  Splitting them is what makes an unconfounded ablation possible.
    """
    m0 = rig.settled_read()
    kf = MassRateLagKF(dt, tau_bal_s=rig.tau_bal_belief_s)
    kf.seed(m0)
    integ = 0.0
    rpm = 0.0
    ff = FF_PRIOR
    revs = 0.0
    prev_err = None
    last_tick = -1
    last_m, last_gain_t = m0, rig.t

    while True:
        if rig.timed_out():
            rig.set_rpm(0.0)
            return "timeout"
        rig.wait(dt)
        revs += (rpm / 60.0) * dt
        z, _, tick = rig.read_frame()
        m, r = kf.update(z, rig.actuating(), u_rev_s=rpm / 60.0, ff=ff,
                         fresh=tick != last_tick)
        last_tick = tick
        if revs > 0.3 and m - m0 > 1e-3:
            ff = 0.9 * ff + 0.1 * ((m - m0) / revs)

        r_stop = r
        if m + r_stop * TAU_PRIOR_S + k_sigma * kf.pred_sigma(TAU_PRIOR_S) \
                >= target_g - CUTOFF_MARGIN_G:
            break
        if m - last_m > 2e-3:
            last_m, last_gain_t = m, rig.t
        elif rig.t - last_gain_t > 8.0:
            break                                # stalled: hand to the finish

        remaining = target_g - m
        r_sp = float(np.clip((remaining - CUTOFF_MARGIN_G) / (2.0 * TAU_PRIOR_S),
                             0.003, max_rate))
        err = r_sp - r
        integ = float(np.clip(integ + err * dt, -0.5, 0.5))
        deriv = 0.0 if (prev_err is None or kd == 0.0) else (err - prev_err) / dt
        prev_err = err
        rpm = float(np.clip(kp * err + ki * integ + kd * deriv,
                            0.0, TRICKLE_RPM_CAP))
        rig.set_rpm(rpm)

    rig.set_rpm(0.0)
    rig.wait(1.2)
    if do_tap_finish:
        return _tap_finish(rig, target_g)
    rig.settled_read()
    return "ok"


def _tap_finish(rig: TrimRig, target_g: float, max_taps: int = 40) -> str:
    """The deployed tap endgame: tap until the reading reaches tolerance.

    Note this is *not* a protective action.  It cannot remove mass, and in the
    PR #124 diagnostic taps caused roughly half of all strict overshoots.  It is
    reproduced faithfully here so the study can price that.
    """
    for _ in range(max_taps):
        if rig.timed_out():
            return "timeout"
        m = rig.settled_read(settle_s=0.8, n_avg=4)
        if m >= target_g - TOL_G:
            return "ok"
        rig.tap(1)
    rig.settled_read()
    return "ok"


def rate_pi(rig: TrimRig, target_g: float, **kw) -> str:
    """Deployed trickle: PI on estimated dose rate + predictive cutoff + taps."""
    return _rate_trim(rig, target_g, kd=0.0, **kw)


def rate_pid(rig: TrimRig, target_g: float, **kw) -> str:
    """As ``rate_pi`` with a derivative term on the rate error.

    The D term differentiates a quantity that is itself the derivative of a
    lagged, quantized, vibration-corrupted balance signal, so it is effectively
    a second derivative of the measurement.  ``kd`` is set to the value that
    would give a conventional 1:4 D:P ratio.
    """
    return _rate_trim(rig, target_g, kd=kw.pop("kd", 60.0), **kw)


# ---------------------------------------------------------------------------
# 4/5/6. Increment-and-measure trims
# ---------------------------------------------------------------------------

def _increment_loop(rig: TrimRig, target_g: float, sizer, use_tap: bool,
                    alpha: float, max_steps: int = 30,
                    inc_rpm: float = 40.0) -> str:
    """Shared driver: size an action, run it, settle, measure, repeat.

    ``sizer(budget_g, alpha_step, model)`` returns the commanded revolutions.
    The loop itself contributes the three properties that matter:

    * every measurement is taken **at rest**, so it needs no lag correction and
      therefore no assumption about ``tau_bal``, and it sees the 0.5 mg quiet
      noise floor instead of the 8 mg actuating one;
    * every command is followed by a full settle, so what the yield model
      identifies is *total settled mass per commanded revolution* -- conveying,
      lip drain, free fall and estimator error all folded into one identified
      quantity, which is what the Edison review asks for in place of a
      mechanistic afterflow decomposition;
    * ``alpha`` is the risk accepted by a **single decision**.  Overshoot is
      terminal, so K decisions at risk ``alpha`` give a dose-level risk of at
      most ``1 - (1 - alpha)^K``; in practice it is far lower, because the rule
      only spends risk on the last few decisions -- while the budget is large
      every command is comfortably safe.  Rather than bound the dose-level rate
      by a slack union bound, the study measures it, and ``run_study.py alpha``
      reports the realised mapping from per-decision alpha to dose-level
      P(E>0).

    When neither an auger command nor a tap is safe, the loop returns ``short``.
    That is a distinct outcome from ``stalled``, and deliberately so: stopping
    because no action's quantum fits the remaining budget is the *correct*
    behaviour under a one-sided constraint, whereas stalling means the auger is
    blocked and the taps could not clear it.  Collapsing the two would score a
    controller that correctly declined to gamble as if it had failed.
    """
    model = YieldModel()
    tap_model = TapYieldModel()
    m = rig.settled_read()
    # A run of zero-yield steps is normal, not a blockage: small commands
    # recharge a lip that an earlier avalanche stripped below its retained
    # capacity, and nothing comes out until the charge is rebuilt.  A real stall
    # is metering a lot of mass with nothing arriving, so the test is on
    # commanded mass since the last delivery, not on a step count.
    dry_rev = 0.0

    for _step in range(max_steps):
        if rig.timed_out():
            return "timeout"
        budget = target_g - m
        if budget <= TOL_G or budget <= EPS_HARD_G:   # interlock + tolerance
            return "ok"

        n_rev = sizer(budget, alpha, model)

        if n_rev > 1e-4:
            before = m
            rig.rotate_deg(n_rev * 360.0, rpm=inc_rpm)
            m = rig.settled_read()
            delivered = m - before
            model.observe(n_rev, delivered)
            dry_rev = dry_rev + n_rev if delivered < 2e-4 else 0.0
            if model.g * dry_rev < STALL_METERED_G:
                continue
            if not use_tap:
                return "stalled"

        # No auger command is safe (or the auger is blocked).  The tap is the
        # finer-quantum terminal actuator: it fires only when its own
        # exceedance against the remaining budget is inside the risk budget.
        if use_tap and tap_model.exceedance(budget) <= alpha:
            before = m
            rig.tap(1)
            m = rig.settled_read()
            tap_model.observe(m - before)
            dry_rev = 0.0
            continue
        return "stalled" if model.g * dry_rev >= STALL_METERED_G else "short"

    return "ok"


def fixed_increment(rig: TrimRig, target_g: float, step_deg: float = 45.0,
                    **_) -> str:
    """Increment-and-measure with the fixed 45 deg step the bench characterised.

    Discrete dosing with the wrong quantum.  Salt yields 6.4 +/- 15.9 mg per
    45 deg step, so a single step can blow a 5 mg budget on its own -- measuring
    at rest between steps does not help if the step itself is too coarse.
    """
    n_rev = step_deg / 360.0
    return _increment_loop(rig, target_g,
                           sizer=lambda budget, a, model: n_rev,
                           use_tap=False, alpha=0.01)


def chance_increment(rig: TrimRig, target_g: float, alpha: float = 0.05,
                     n_max_rev: float = 4.0, **_) -> str:
    """The proposal: every command sized by a one-sided chance constraint.

    At each step choose the largest command ``n`` satisfying

        P( delivered(n) > remaining budget ) <= alpha

    using a Gamma predictive distribution matched to the identified mean and
    compound-Poisson variance of the settled yield.  The budget shrinks each
    step, so the command shrinks with it and the exceedance risk stays pinned at
    ``alpha`` throughout rather than growing as the target is approached.

    No handover constant appears anywhere: the first command is typically most
    of a revolution (continuum regime, many slug events, low relative
    dispersion) and the last is a few degrees.
    """
    return _increment_loop(
        rig, target_g,
        sizer=lambda budget, a, model: model.largest_safe_rev(
            budget, a, n_max=n_max_rev),
        use_tap=False, alpha=alpha)


def chance_tap(rig: TrimRig, target_g: float, alpha: float = 0.05,
               n_max_rev: float = 4.0, **_) -> str:
    """``chance_increment`` plus a chance-constrained tap for stall recovery.

    The tap is treated exactly like an auger command -- it fires only when its
    own identified upper quantile fits the remaining budget -- which is the
    difference between a tap that rescues a blocked cohesive powder and the
    deployed ``tap_finish``, where taps caused about half the strict overshoots.
    """
    return _increment_loop(
        rig, target_g,
        sizer=lambda budget, a, model: model.largest_safe_rev(
            budget, a, n_max=n_max_rev),
        use_tap=True, alpha=alpha)


METHODS = {
    "margin_only": margin_only,
    "rate_pi": rate_pi,
    "rate_pid": rate_pid,
    "fixed_increment": fixed_increment,
    "chance_increment": chance_increment,
    "chance_tap": chance_tap,
}


def run_method(name: str, rig: TrimRig, target_g: float, **kw) -> str:
    return METHODS[name](rig, target_g, **kw)
