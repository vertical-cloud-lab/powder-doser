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
GOAL_MASS_G = 0.200

# Dispensing angle during the PI trickle, plate degrees.  Steeper (bigger)
# feeds faster but holds more powder on the tube lip; the twin's deployed
# controller trickles at 20.  The fine phase of the three-phase firmware
# uses 22.5, the tap endgame 0 (horizontal, most precise).
TRICKLE_TILT_DEG = 20.0

# =========================================================================
# Dose structure
# =========================================================================

# Finish tolerance, grams: dose is "ok" when |mass - goal| <= this.
TOLERANCE_G = 0.005

# Remaining-mass threshold at which the bulk phase hands over to the PI
# trickle, grams.  A goal below (this + BULK_ANTICIPATION_G) skips bulk
# entirely and the whole dose is trickle + taps -- handy for watching the
# PI behaviour on its own at small targets.
TRICKLE_START_REMAINING_G = 0.300

# Bulk phase (velocity mode, borrowed from main_three_phase's phase 1):
# spin at BULK_RPM / BULK_TILT_DEG until remaining <= TRICKLE_START_
# REMAINING_G + BULK_ANTICIPATION_G, then settle and hand to the trickle.
BULK_ENABLED = True          # 0/False = always start in the trickle
BULK_TILT_DEG = 25.0
BULK_RPM = 55.0              # auger RPM (ceiling ~109)
BULK_ANTICIPATION_G = 0.050  # halt this much EARLY (in-flight margin)
BULK_POLL_MS = 250
BULK_SETTLE_MS = 1500

# Tap endgame tilt, plate degrees (0 = horizontal, the precise end).
TAP_TILT_DEG = 0.0
TAPS_PER_CYCLE = 1           # single taps: a 2-burst can dump a slug past
                             # target off a charged lip (twin finding)
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
# Safety
# =========================================================================

DOSE_TIMEOUT_S = 600         # hard wall-clock abort for one dose
MAX_POLL_MISSES = 10         # consecutive silent polls before scale-error

# =========================================================================
# Telemetry
# =========================================================================

LOG_TO_FLASH = True          # write /trickle_log_<n>.csv on the Pico after
                             # each dose (download with MicroPico, or print
                             # with the ``log`` command)
LOG_MAX_ROWS = 2400          # RAM guard: ~10 min of 4 Hz rows
PRINT_EVERY_N_POLLS = 2      # console cadence during the trickle (1 = all)
