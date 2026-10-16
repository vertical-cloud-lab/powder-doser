"""Knobs for the refill-tap endgame (``main_trickle_refill.py``).

Same workflow as ``trickle_params.py`` (which still holds every other
knob, goal mass and tilts included): edit + re-upload this file, or
change values live at the REPL -- ``set refill_deg 15``,
``set refill_taps_to_go 30`` -- and ``s`` prints them.

The rule, after every tap (see ``refill_tap.py``):

    avg  = mean yield of the last REFILL_AVG_TAPS taps (since the last refill)
    need = goal - TOLERANCE_G - mass        # still to go to reach the band
    if avg * REFILL_TAPS_TO_GO < need:      # tap yield far below the need
        rotate the auger REFILL_DEG, settle, read, restart the average

so the auger turns between taps until the taps are yielding enough to
finish in about REFILL_TAPS_TO_GO more.  It never refills closer than
REFILL_MIN_TO_GO_G to the band, nor when the largest refill delivery
seen this dose would overshoot; there the tuned endgame (single taps,
5 deg dry-lip nudges) finishes the dose unchanged.

Angles/RPM are TRUE AUGER degrees/RPM, as everywhere in this folder.
"""

# 0/False = the stock tap endgame, step for step (the A/B baseline: the
# same build, one knob).
REFILL_ENABLED = True

# The refill rotation, auger degrees, and its speed (auger RPM).  The 5 deg
# dry-lip nudge barely refills the tip (rig logs, PR #166: 0.4 mg/tap in
# the three taps after a nudge vs 2.8 mg on the first tap after the
# trickle halts), hence the bigger default.  On the rig a rotation also
# waits ~2 s after the move (Stepper._wait_estimated_time).
REFILL_DEG = 10.0
REFILL_RPM = 20.0

# The running average: window length, in taps.  The window restarts after
# every refill, so it only ever describes the tip as it is now.
REFILL_AVG_TAPS = 4

# Taps of evidence needed after the tap stage starts or after a refill
# before the next refill decision.  2 = never two refills back to back,
# and one empty tap (P ~ 10 % on salt) cannot trigger a refill alone.
REFILL_MIN_TAPS = 2

# "Far below": refill when the average tap yield would need MORE than
# this many taps to cover what is still needed.  Lower = refill sooner and
# more often (faster, riskier); higher = closer to the stock endgame.
# Rig logs: taps 2-3 s apart, 0.5-1 mg each once the tip has drained.
REFILL_TAPS_TO_GO = 20

# Never refill with less than this still to go to the band, grams.  A
# rotation can drop a slug (45 deg steps at 22.5 deg tilt delivered
# 6-76 mg in Block H), so the refill zone stops well short of the goal.
REFILL_MIN_TO_GO_G = 0.025

# Wait after the refill rotation before the settled read that measures
# what the refill itself delivered, ms (on top of the stepper's ~2 s).
REFILL_SETTLE_MS = 800

# Refill budget per dose (on top of TAP_MAX_CYCLES / TAP_MAX_NUDGES).
REFILL_MAX = 20
