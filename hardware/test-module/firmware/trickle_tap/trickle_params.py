"""Every user-facing knob for the manual trickle-tap runner.

EDIT THIS FILE, nothing else.  Workflow: change a value, save, re-upload
just this file to the Pico (MicroPico: right-click -> "Upload file to
Pico"), then re-run ``main_trickle.py``.  Or change values live at the
REPL without re-uploading:  ``set goal_mass_g 0.5``,
``set trickle_tilt_deg 15`` -- every UPPERCASE name below is settable as
its lowercase form, and ``s`` prints the current values.

Angle convention: TRUE MOUNTING-PLATE degrees (0 = horizontal cup-side,
45 = "vertical" preset), same as ``main_three_phase.py`` -- the 2:1
servo gearing is folded in at the driver.  Rotations are TRUE AUGER
degrees / RPM (44:20 gearing folded in likewise).
"""

# =========================================================================
# THE TWO KNOBS MOST SESSIONS TOUCH
# =========================================================================

# Goal (target) mass for a bare ``g`` command, grams.
GOAL_MASS_G = 0.7500

# Dispensing angle during the PI trickle, plate degrees.  Steeper (bigger)
# feeds faster but holds more powder on the tube lip; the twin's deployed
# controller trickles at 20.  The fine phase of the three-phase firmware
# uses 22.5, the tap endgame 0 (horizontal, most precise).
TRICKLE_TILT_DEG = 15.0

# =========================================================================
# Dose structure
# =========================================================================

# Finish tolerance, grams: dose is "ok" when |mass - goal| <= this.
TOLERANCE_G = 0.005

# Remaining-mass threshold at which the bulk phase hands over to the PI
# trickle, grams.  A goal below (this + BULK_ANTICIPATION_G) skips bulk
# entirely and the whole dose is trickle + taps -- handy for watching the
# PI behaviour on its own at small targets.
TRICKLE_START_REMAINING_G = 0.250

# Bulk phase (velocity mode, borrowed from main_three_phase's phase 1):
# spin at BULK_RPM / BULK_TILT_DEG until remaining <= TRICKLE_START_
# REMAINING_G + BULK_ANTICIPATION_G, then settle and hand to the trickle.
BULK_ENABLED = True          # 0/False = always start in the trickle
BULK_TILT_DEG = 30.0
BULK_RPM = 55.0              # auger RPM (ceiling ~109)
BULK_ANTICIPATION_G = 0.050  # halt this much EARLY (in-flight margin)
BULK_POLL_MS = 250
BULK_SETTLE_MS = 1500

# Bulk-only dose (added 2026-09-30 for a clogged Al 4047 load, PR #166):
# 1 = the WHOLE dose runs at BULK_TILT_DEG with the bulk cadence taps --
# no trickle, no tap endgame, the tube never tips shallower (chunks in
# the tube fed at 40 deg and stopped dead at the 10/15 deg trim tilts).
# The auger rpm then tapers from BULK_RPM to BULK_MIN_RPM over the last
# BULK_TAPER_START_G, and steps back up x1.5 (to at most BULK_RPM) after
# every BULK_BOOST_S without flow.  It halts when mass + trailing-2 s
# slope * TAU_AFTERFLOW_S reaches goal - TOLERANCE_G/2; a dose that
# settles short by more than the tolerance gets another pass, up to
# BULK_MAX_PASSES.  0 = the tuned bulk -> trickle -> tap dose.
BULK_ONLY = False
BULK_TAPER_START_G = 0.100
BULK_MIN_RPM = 20.0
BULK_BOOST_S = 3.0
BULK_MAX_PASSES = 8

# Bulk -> tap dose (added 2026-10-01, PR #166): 0 = no PI trickle.  The
# bulk then runs like BULK_ONLY's (taper, no-flow boost, predictive
# halt) but aims BULK_STOP_MARGIN_G short of the goal, in ONE pass, and
# the tap endgame below finishes the dose.  The taper ends at the larger
# of the margin and TOLERANCE_G; start it before the predicted afterflow
# (flow x TAU_AFTERFLOW_S, about 0.1 g for salt at 100 rpm) or the halt
# fires at full speed.  TRICKLE_START_REMAINING_G and
# BULK_ANTICIPATION_G are unused in this mode, and BULK_ONLY wins when
# both are set.  1 = the tuned bulk -> trickle -> tap dose.
TRICKLE_ENABLED = True
BULK_STOP_MARGIN_G = 0.010

# The predictive halt of BULK_ONLY and TRICKLE_ENABLED = 0 doses.
# 0 = mass + trailing-2 s poll slope * TAU_AFTERFLOW_S, the rule the
# 2026-09-30 Al 4047 top-up landed +0.95 mg with (the TAU fit pairs the
# same raw reading with the same slope).  1 = the Kalman filter below:
# halt when m_hat + r_hat * TAU_AFTERFLOW_S + K_SIGMA * sigma reaches
# the aim, the PI trickle's cutoff rule with the auger at bulk rpm.
BULK_HALT_KF = False

# Tap endgame tilt, plate degrees (0 = horizontal, the precise end).
TAP_TILT_DEG = 10.0
TAPS_PER_CYCLE = 1           # single taps: a 2-burst can dump a slug past
                             # target off a charged lip (twin finding)
# Tap burst: TAP_BURST_TAPS taps per cycle while MORE than
# TAP_BURST_ABOVE_G is still to go, then TAPS_PER_CYCLE for the last
# stretch, where the slug risk above matters.  Both stretches share
# TAP_MAX_CYCLES and TAP_MAX_NUDGES.  0 = off (the tuned salt runs).
TAP_BURST_ABOVE_G = 0.0
TAP_BURST_TAPS = 2
TAP_SETTLE_MS = 1500
TAP_NUDGE_DEG = 5.0          # auger nudge when the lip runs dry
TAP_MAX_NUDGES = 20          # the twin's tap_finish budget; the trickle can
TAP_MAX_CYCLES = 120         # hand over 35-65 mg short, deeper than the
                             # three-phase fine->tap threshold (25 mg)

# =========================================================================
# The PI trickle itself (the part under inspection)
# Values are the deployed twin controller's: optimization/benchmarks/
# bangbang.py trickle_tap() as re-derived in optimization/trim/
# trim_methods.py _rate_trim().
# =========================================================================

TRICKLE_DT_S = 0.25          # control period: sleep this, then poll+update.
                             # The KF rebuilds its model from the MEASURED
                             # interval each cycle, so serial latency on top
                             # of this does not bias the estimate.
TRICKLE_KP = 250.0           # PI proportional gain, rpm per (g/s) of rate error
TRICKLE_KI = 120.0           # PI integral gain
TRICKLE_INTEG_CLAMP = 0.5    # anti-windup bound on the integrator state
TRICKLE_MAX_RATE_GPS = 0.05  # rate set-point ceiling, g/s
TRICKLE_RPM_CAP = 45.0       # commanded-rpm ceiling (slug-dump protection)
TRICKLE_MIN_RATE_GPS = 0.003 # rate set-point floor, g/s

# Predictive cutoff:  halt when  m_hat + r_hat*TAU + K_SIGMA*sigma
#                                >= goal - CUTOFF_MARGIN_G.
CUTOFF_MARGIN_G = 0.035      # the fixed 35 mg undershoot margin
TAU_AFTERFLOW_S = 0.30       # afterflow lookahead (lip drain + free fall)
K_SIGMA = 1.0                # extra margin in units of KF prediction sd

# Stall bail: no 2 mg of estimated gain for this long while trickling ->
# stop and hand to the tap endgame (cohesive powder blocked the lip).
STALL_BAIL_S = 8.0

# Wait after the trickle halts before the settled hand-over reading, ms.
POST_TRICKLE_SETTLE_MS = 1200

# =========================================================================
# Kalman filter (3-state: true mass m, rate r, lagged balance reading b)
# =========================================================================

TAU_BAL_S = 0.7              # believed balance lag.  Datasheet ~0.7 s; the
                             # pre-move drop tests said ~0.16 s; bench-plan
                             # test A1 decides.  This is THE sensitive one:
                             # the sim puts 22.7 mg on getting it wrong.
RATE_TAU_S = 0.5             # how fast delivery rate tracks ff * rpm
KF_Q_VAR = 2e-4              # process-noise scale on (m, r)
QUIET_SD_G = 5e-4            # assumed balance sd at rest (0.5 mg)
NOISY_SD_G = 8e-3            # assumed sd while actuating (8 mg)
FF_PRIOR_G_PER_REV = 0.35    # feed-factor prior, g per auger rev.  Learned
                             # online after ~0.3 rev; bench salt runs at
                             # ~0.113 g/rev, so the prior only shapes the
                             # first seconds.

# =========================================================================
# Optimization-campaign knobs (issue #164) -- cadence taps + result line
# =========================================================================

# Cadence tapping: a flow aid for powders that will not feed from
# rotation alone.  Each is an on/off categorical in the issue #164
# search space; "on" fires ONE solenoid pulse per cadence period while
# the phase runs.  Salt baseline: both off.
BULK_TAP = False             # cadence taps during the bulk phase
TRICKLE_TAP = False          # cadence taps during the PI trickle

# The fixed "on" cadence (locked 2026-09-22: 2 Hz).  60 ms energize
# pulse (the proven TAP_ON_MS) + 440 ms gap = one tap per 500 ms.
TAP_CADENCE_ON_MS = 60
TAP_CADENCE_OFF_MS = 440

# Wait after the last actuation before the settled FINAL reading that
# scores the dose (|error| and t_total are measured against it), ms.
FINAL_SETTLE_MS = 2000

# =========================================================================
# Safety
# =========================================================================

DOSE_TIMEOUT_S = 600         # hard wall-clock abort for one dose
MAX_POLL_MISSES = 10         # consecutive silent polls before scale-error

# Overshoot guard (issue #164): abort the dose the moment the measured
# mass exceeds goal + this, instead of letting later phases discover it.
# 0 disables.  Distinct from TOLERANCE_G: that scores the dose, this
# stops the rig from feeding a runaway one.
OVERSHOOT_ABORT_G = 0.100

# =========================================================================
# Telemetry
# =========================================================================

LOG_TO_FLASH = True          # write /trickle_log_<n>.csv on the Pico after
                             # each dose (download with MicroPico, or print
                             # with the ``log`` command)
LOG_MAX_ROWS = 1200          # RAM guard: ~5 min of 4 Hz rows.  The slot
                             # array is allocated once at boot; 2400 rows
                             # of strings never fit the Pico W heap
                             # (2026-09-30 MemoryError at row 257, PR #166)
LOG_MIN_FREE_BYTES = 24000   # stop logging (not dosing) below this much
                             # free heap, so the controller keeps room
PRINT_EVERY_N_POLLS = 2      # console cadence during the trickle (1 = all)
