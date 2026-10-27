"""Every load the FEA cases use, in one place (N, mm, kg), with where each number comes from.

Masses are in kg here; multiply by G_MS2 for newtons. Cases import this module rather than restating numbers.
"""
from __future__ import annotations

G_MS2 = 9.81

# --- motors -------------------------------------------------------------------------------------------------
# StepperOnline lists the open-loop 34HS59-6004S (same 86 mm frame, 150 mm body, 12 N*m) at 5.4 kg; the E1000
# encoder and its cover add about 0.2 kg. No published mass for the closed-loop part was found.
M_NEMA34 = 5.6
NEMA34_HOLD_NM = 12.0          # holding torque: what a jam can load the drive with (closed-loop driver, full current)
NEMA34_BODY_L = 150.0 + 19.0   # mm, mounting face to the encoder's end (params.M34_BODY_L + M34_ENC_L)
M_NEMA11 = 0.18                # 11HS18-0674S class (station carriage)

# --- drive torque in normal running (the design's own simulations) --------------------------------------------
V2_DRIVE_NM = 1.7              # chain-carousel-v2/sim/README.md: MuJoCo loop, every run under 1.7 N*m
PAT_DRIVE_NM = 1.6             # paternoster/sim/README.md: raw peak 1.6 N*m (0.3 N*m averaged)

# --- chains -------------------------------------------------------------------------------------------------
CHAIN_KG_M = 0.33              # ANSI 35 (paternoster sim; Tsubaki RS35 about 0.33 kg/m)
V2_TENSION_N = 80.0            # params.CHAIN_TENSION_N, per chain
PAT_TENSION_N = 40.0           # paternoster sim and TEST-PLAN T1 (3-4 mm sag under 10 N)
V2_R15_MM = 45.81 / 2          # 15T drive sprockets' pitch radius (v2's 1:1 drive chain)

# --- v2 module and carriage (chain-carousel-v2/sim/README.md) -------------------------------------------------
V2_MODULE_KG = 0.219           # plate 34.5 g, steel tab 9.2 g, pins 3.5 g, auger 66.2 g, cap 5.4 g, powder 100 g
V2_MODULE_COM_SAM = (107.5, 0.0, -4.4)   # Sam's frame, mm (hinge axis at x = z = 0)
V2_CARRIAGE_KG = 0.098
V2_HOOK_STATIC_N = 4.4         # both snap hooks together, module upside down on the top run (MuJoCo)
V2_HOOK_MAX_N = 5.6            # ... worst case in the loop runs (100 mm/s)
V2_HOOK_RELEASE_N = 8.0        # station sim: force to pull the plate past both hooks
V2_N_MODULES = 13

# --- paternoster gondola and module (paternoster/sim/README.md) -----------------------------------------------
PAT_GONDOLA_KG = 0.12          # two end plates 0.035 kg + floor/rails 0.05 kg
PAT_MODULE_KG = 0.26           # plate 0.07 + brackets 0.03 + auger with powder 0.16 (0.12-0.20 tested)
PAT_LOADED_KG = 0.38           # gondola + module; COM 24 mm under the pivot, 143.5 mm from the front chain
PAT_FRONT_SHARE = 0.56         # the front chain carries 56 % (COM is nearer the front)
PAT_HOLD_STRIP_N = 10.9        # UHMW hold-down strip, worst case in the station run
PAT_PIVOT_LIFT_N = 2.7         # tilting pulls the station gondola's front pivot up (quasi-static)
PAT_N_MODULES = 12

# --- station (same design in both) ----------------------------------------------------------------------------
ECAR_KG = 0.285 + 0.020        # Sam's electronics carriage with NEMA 11, solenoid, magnet + bracket, wiring, steel pinion
ECAR_COM_SAM = (52.0, 0.0, -33.6)
P16_MAX_N = 50.0               # Actuonix P16-150-22-12-P: 50 N lift (what a stall against an obstacle can push)
P16_BACKDRIVE_N = 75.0         # its back-drive force
P16_RUN_PEAK_N = 19.3          # paternoster station sim with the U-yoke
MAGNET_HOLD_N = 24.5           # Adafruit 3872 P20/15 at zero gap
MAGNET_DESIGN_N = 10.6         # at the 0.15 mm design gap: 20 N / (1 + g / 0.4 mm)^2
GEAR_SEP_STALL_N = 3.7         # NEMA 11 at 450 mA stalls with 3.7 N separating force at the mesh (v2 station sim)
GEAR_SEP_DRY_N = 6.6           # printed-on-printed dry teeth at holding torque (gear-mesh study)
SOLENOID_TAP_N = 3.0           # 10 ms taps in the sims

# --- people ---------------------------------------------------------------------------------------------------
HAND_N = 20.0                  # a hand loading or unloading a module, pressing a carriage onto the tabs
LEAN_N = 100.0                 # someone leaning on or bumping the frame's top rail

# --- motion ---------------------------------------------------------------------------------------------------
ESTOP_DECEL = 0.68             # m/s^2: v2 power cut at 100 mm/s coasts 7.3 mm (v^2 / 2d)
V_MAX_MM_S = 130.0             # paternoster's continuous-move cap; v2 runs up to 100 mm/s
SPROCKET_CIRC_MM = 9.525 * 32  # one 32T revolution moves the chain 304.8 mm
FULL_STEPS_PER_REV = 200


def full_step_hz(v_mm_s: float) -> float:
    """Full-step rate of the NEMA 34 at a chain speed (both designs turn a 32T sprocket once per motor turn:
    v2 through its 1:1 drive chain, the paternoster directly)."""
    return v_mm_s / SPROCKET_CIRC_MM * FULL_STEPS_PER_REV


def kgf(kg: float) -> float:
    return kg * G_MS2
